---
name: cross-window-photo-diptych-v2
description: Quickly create a vertical two-photo cross-window diptych by exchanging complete or visually distinctive photographic regions at their exact original locations. Use when a user supplies two photos for a fast surreal position-swap collage that should preserve source fidelity, keep recognizable subjects intact when possible, tolerate ridge or branch crossings, adapt to difficult proportions, and always produce an artwork for valid image inputs.
---

# Cross-Window Photo Diptych V2

Create the effect through deterministic compositing. Preserve the two source photographs, stack them at a common width without changing their aspect ratios, and exchange two crisp photographic windows. Never redraw, blend, generatively edit, add text, or globally grade the images.

## Single-pass workflow

1. Inspect both current inputs once with `view_image`.
2. Choose one visible anchor box per image using this preference order:
   - a complete independent person, animal, object, light, shadow, reflection, or compact group;
   - a complete subject that touches a ridge, branch, ground line, waterline, or other continuous background;
   - a compact distinctive detail belonging to a larger subject;
   - when no obvious subject exists, the most recognizable local color, texture, silhouette, or shape event.
3. Keep each box tight enough to preserve the parent photograph. Include inseparable evidence such as a person's long shadow or all members of a compact group. A window may cross a ridge, branch, horizon, hull, or canopy when that is necessary to keep the selected subject.
4. Run exactly one command:

   ```bash
   python scripts/diptych_v2.py quick \
     --top /absolute/photo-a.jpg \
     --bottom /absolute/photo-b.jpg \
     --top-box 0.10,0.20,0.28,0.46 \
     --bottom-box 0.42,0.36,0.61,0.62 \
     --top-label "visible anchor A" \
     --bottom-label "visible anchor B" \
     --output /absolute/work/final-diptych.png
   ```

5. Return the PNG after `DELIVERY PASS`. Use only this one-command path.

If ordinary Python lacks Pillow, call `load_workspace_dependencies` and use its bundled Python. Do not install a package for one run.

## Composition behavior

- Paste B at A's original normalized center and A at B's original normalized center.
- Cover the outgoing region completely so no orphaned body part, shadow, or object fragment remains.
- Prefer restrained square windows around 18% of the common width.
- Automatically enlarge or reshape each destination window when required by its outgoing anchor. The two windows may use different adaptive rectangles rather than fail.
- Reduce context, shift the source crop within its image bounds, or use a complete-box resize when an anchor sits near an edge or has an extreme aspect ratio.
- Preserve source colors and exposure differences; the visible contrast between the two windows is part of the style.
- Reuse neither a previous composite nor a screenshot. Always start from the two current source paths.
- If the requested output name already exists, automatically create a numbered filename and continue.

## Completion rule

For valid, decodable image inputs and valid normalized boxes, always produce the best available composition. Do not reject a pair for aesthetic uncertainty, repeated subjects, structural crossings, large scene subjects, scale mismatch, shape mismatch, edge proximity, or imperfect visual balance. Only missing, unreadable, or malformed inputs may stop execution.
