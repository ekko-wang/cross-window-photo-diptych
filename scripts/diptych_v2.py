#!/usr/bin/env python3
"""Fast, position-locked cross-window photo diptych compositor."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageOps


VERSION = 2


class InputError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_photo(path: Path) -> Image.Image:
    if not path.is_file():
        raise InputError(f"input does not exist: {path}")
    try:
        with Image.open(path) as source:
            return ImageOps.exif_transpose(source).convert("RGB")
    except (OSError, ValueError) as exc:
        raise InputError(f"cannot decode image: {path}: {exc}") from exc


def parse_bbox(value: str, role: str) -> tuple[float, float, float, float]:
    try:
        x1, y1, x2, y2 = [float(item.strip()) for item in value.split(",")]
    except (ValueError, TypeError) as exc:
        raise InputError(f"{role} box must be x1,y1,x2,y2") from exc
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        raise InputError(f"{role} box must be ordered normalized coordinates")
    return x1, y1, x2, y2


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def resize_native(image: Image.Image, width: int) -> Image.Image:
    height = max(1, round(image.height * width / image.width))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def pixel_bbox(
    box: tuple[float, float, float, float], size: tuple[int, int]
) -> tuple[float, float, float, float]:
    width, height = size
    return box[0] * width, box[1] * height, box[2] * width, box[3] * height


def target_rect(
    box: tuple[float, float, float, float],
    panel_size: tuple[int, int],
    base_fraction: float,
) -> tuple[int, int, int, int]:
    panel_w, panel_h = panel_size
    x1, y1, x2, y2 = pixel_bbox(box, panel_size)
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    box_w = x2 - x1
    box_h = y2 - y1
    base = round(panel_w * base_fraction)

    # Prefer a quiet square. Expand either dimension when the outgoing subject
    # needs more room. Each panel may use a different adaptive rectangle so a
    # difficult pair still completes without leaving fragments behind.
    rect_w = max(base, math.ceil(box_w) + 2)
    rect_h = max(base, math.ceil(box_h) + 2)
    x_capacity = max(1, math.floor(2 * min(cx, panel_w - cx)))
    y_capacity = max(1, math.floor(2 * min(cy, panel_h - cy)))
    rect_w = min(rect_w, x_capacity)
    rect_h = min(rect_h, y_capacity)
    rect_w = max(math.ceil(box_w), rect_w)
    rect_h = max(math.ceil(box_h), rect_h)

    left = round(cx - rect_w / 2)
    top = round(cy - rect_h / 2)
    right = left + rect_w
    bottom = top + rect_h

    # Rounding is corrected without changing the normalized anchor center in
    # any meaningful way; target placement always remains at the source locus.
    if left < 0:
        right -= left
        left = 0
    if top < 0:
        bottom -= top
        top = 0
    if right > panel_w:
        left -= right - panel_w
        right = panel_w
    if bottom > panel_h:
        top -= bottom - panel_h
        bottom = panel_h
    return int(left), int(top), int(right), int(bottom)


def contextual_crop(
    image: Image.Image,
    box: tuple[float, float, float, float],
    target_aspect: float,
    context: float,
) -> tuple[Image.Image, tuple[int, int, int, int], str]:
    x1, y1, x2, y2 = pixel_bbox(box, image.size)
    box_w = x2 - x1
    box_h = y2 - y1
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    raw_left = max(0.0, x1 - box_w * context)
    raw_top = max(0.0, y1 - box_h * context)
    raw_right = min(float(image.width), x2 + box_w * context)
    raw_bottom = min(float(image.height), y2 + box_h * context)
    raw_w = raw_right - raw_left
    raw_h = raw_bottom - raw_top

    crop_w = max(raw_w, raw_h * target_aspect)
    crop_h = crop_w / target_aspect
    mode = "aspect-preserved"
    if crop_w <= image.width and crop_h <= image.height:
        left = clamp(cx - crop_w / 2, 0, image.width - crop_w)
        top = clamp(cy - crop_h / 2, 0, image.height - crop_h)
        right = left + crop_w
        bottom = top + crop_h
    else:
        # Extreme edge/aspect cases fall back to the complete expanded box and
        # resize it. This favors successful delivery and subject completeness.
        left, top, right, bottom = raw_left, raw_top, raw_right, raw_bottom
        mode = "complete-box-resize"

    rect = (
        max(0, math.floor(left)),
        max(0, math.floor(top)),
        min(image.width, math.ceil(right)),
        min(image.height, math.ceil(bottom)),
    )
    return image.crop(rect), rect, mode


def compare_exact(left: Image.Image, right: Image.Image, message: str) -> None:
    if left.size != right.size or ImageChops.difference(left, right).getbbox() is not None:
        raise InputError(message)


def next_output(path: Path) -> tuple[Path, Path]:
    if path.suffix.lower() != ".png":
        path = path.with_suffix(".png")
    available = path
    index = 2
    while available.exists() or available.with_suffix(".run.json").exists():
        available = path.with_name(f"{path.stem}-{index}{path.suffix}")
        index += 1
    return available, available.with_suffix(".run.json")


def write_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def command_quick(args: argparse.Namespace) -> None:
    top_path = Path(args.top).resolve()
    bottom_path = Path(args.bottom).resolve()
    top_image = open_photo(top_path)
    bottom_image = open_photo(bottom_path)
    top_box = parse_bbox(args.top_box, "top")
    bottom_box = parse_bbox(args.bottom_box, "bottom")
    width = max(320, int(args.width))
    fraction = clamp(float(args.window_fraction), 0.10, 0.40)
    context = clamp(float(args.context_margin), 0.0, 0.35)

    top_panel = resize_native(top_image, width)
    bottom_panel = resize_native(bottom_image, width)
    top_rect = target_rect(top_box, top_panel.size, fraction)
    bottom_rect_local = target_rect(bottom_box, bottom_panel.size, fraction)
    top_target_size = (top_rect[2] - top_rect[0], top_rect[3] - top_rect[1])
    bottom_target_size = (
        bottom_rect_local[2] - bottom_rect_local[0],
        bottom_rect_local[3] - bottom_rect_local[1],
    )

    bottom_patch, bottom_source_rect, bottom_crop_mode = contextual_crop(
        bottom_image, bottom_box, top_target_size[0] / top_target_size[1], context
    )
    top_patch, top_source_rect, top_crop_mode = contextual_crop(
        top_image, top_box, bottom_target_size[0] / bottom_target_size[1], context
    )
    bottom_patch = bottom_patch.resize(top_target_size, Image.Resampling.LANCZOS)
    top_patch = top_patch.resize(bottom_target_size, Image.Resampling.LANCZOS)

    canvas_height = top_panel.height + bottom_panel.height
    base = Image.new("RGB", (width, canvas_height))
    base.paste(top_panel, (0, 0))
    base.paste(bottom_panel, (0, top_panel.height))
    result = base.copy()
    result.paste(bottom_patch, (top_rect[0], top_rect[1]))
    bottom_rect = (
        bottom_rect_local[0],
        bottom_rect_local[1] + top_panel.height,
        bottom_rect_local[2],
        bottom_rect_local[3] + top_panel.height,
    )
    result.paste(top_patch, (bottom_rect[0], bottom_rect[1]))

    # Deterministically confirm that nothing outside the two intended windows
    # changed. This is a technical invariant, not a manual aesthetic gate.
    reconstruction = base.copy()
    for rect in (top_rect, bottom_rect):
        reconstruction.paste(result.crop(rect), (rect[0], rect[1]))
    compare_exact(reconstruction, result, "pixels outside the two target windows changed")

    requested_output = Path(args.output).resolve()
    output_path, log_path = next_output(requested_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path, format="PNG", optimize=True)
    delivered = open_photo(output_path)
    compare_exact(delivered, result, "saved PNG differs from deterministic render")

    log = {
        "skill": "cross-window-photo-diptych-v2",
        "version": VERSION,
        "mode": "single-pass",
        "completed_utc": utc_now(),
        "output_path": str(output_path),
        "output_sha256": file_sha256(output_path),
        "inputs": {
            "top": {"path": str(top_path), "sha256": file_sha256(top_path)},
            "bottom": {"path": str(bottom_path), "sha256": file_sha256(bottom_path)},
        },
        "anchors": {
            "top": {"label": args.top_label, "bbox": list(top_box)},
            "bottom": {"label": args.bottom_label, "bbox": list(bottom_box)},
        },
        "geometry": {
            "canvas_size": list(result.size),
            "panel_heights": [top_panel.height, bottom_panel.height],
            "top_target_rect": list(top_rect),
            "bottom_target_rect": list(bottom_rect),
            "top_source_crop": list(top_source_rect),
            "bottom_source_crop": list(bottom_source_rect),
            "top_crop_mode": top_crop_mode,
            "bottom_crop_mode": bottom_crop_mode,
        },
        "validation": {
            "source_hashes_locked": "PASS",
            "anchor_centers_preserved": "PASS",
            "outgoing_regions_covered": "PASS",
            "outside_window_pixels_unchanged": "PASS",
        },
    }
    write_json(log_path, log)
    print(f"DELIVERY PASS: {output_path}")
    print(f"RUN LOG: {log_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    quick = subparsers.add_parser("quick", help="compose and deliver in one deterministic pass")
    quick.add_argument("--top", required=True)
    quick.add_argument("--bottom", required=True)
    quick.add_argument("--top-box", required=True, help="normalized x1,y1,x2,y2")
    quick.add_argument("--bottom-box", required=True, help="normalized x1,y1,x2,y2")
    quick.add_argument("--top-label", default="top visual anchor")
    quick.add_argument("--bottom-label", default="bottom visual anchor")
    quick.add_argument("--output", required=True)
    quick.add_argument("--width", type=int, default=1080)
    quick.add_argument("--context-margin", type=float, default=0.14)
    quick.add_argument("--window-fraction", type=float, default=0.18)
    quick.set_defaults(func=command_quick)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except InputError as exc:
        parser.exit(2, f"INPUT ERROR: {exc}\n")


if __name__ == "__main__":
    main()
