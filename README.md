# CrossWindow｜交错之窗

> 让两张照片，在彼此的位置上短暂相遇。  
> Let two photographs briefly meet in each other's place.

示例 ｜  Examples

<img width="270" height="280" alt="Codex 图像 2026年8月11日 14_20_23" src="https://github.com/user-attachments/assets/29d90bec-80a2-494f-807d-56a2230a63ee" /><img width="186.6" height="280" alt="v2-fuji-hikers-final" margin-left="10px" src="https://github.com/user-attachments/assets/54e99268-f6eb-4a4a-be1a-e7b4bf50848c" /><img width="182.4" height="280" alt="v2-gull-runner-final" margin-left="10px" src="https://github.com/user-attachments/assets/71fe67a2-86c4-4c9c-b869-96cf4b0bbdce" />



[中文](#中文) · [English](#english)

---

## 中文

### 关于

CrossWindow 是一个轻量的 Codex 摄影拼贴 Skill。

它将两张照片上下并置，从各自画面里取出一处有辨识度的局部，再把它们放进彼此原来的位置。人物遇见另一片风景，影子落入陌生的地面，日常物件也会获得一段意外的关系。

照片仍然是原来的照片，只多了一扇通往另一幅画面的窗口。

### 它能做什么

- 把两张照片组合成纵向摄影双联画
- 原位交换人物、动物、物件、灯光、影子或局部景色
- 尽量保留主体的完整轮廓和原图比例
- 自动适应横图、竖图与不同大小的交换区域
- 快速输出成片，不经过反复候选和人工复核

### 视觉气质

CrossWindow 偏爱清晰、克制的矩形窗口。它不抠图、不重绘，也不会抹平两张照片之间的色温与光线差异。

那些差异——冷与暖、远与近、城市与自然——正是画面产生诗意的地方。

### 安装

将仓库放入 Codex 的 Skills 目录：

```bash
git clone https://github.com/ekko-wang/cross-window-photo-diptych.git ~/.codex/skills/cross-window-photo-diptych-v2
```

需要 Python 3 与 Pillow：

```bash
python3 -m pip install Pillow
```

如果 Codex 工作区已经包含 Pillow，无需重复安装。

### 在 Codex 中使用

上传两张照片，然后说：

```text
用 $cross-window-photo-diptych-v2 处理这两张照片。
```

CrossWindow 会选择适合互换的局部，并输出一张纵向 PNG 成片。


### 小小的边界

CrossWindow 创作的是带有原始环境的摄影窗口，而不是透明背景抠图。窗口可能经过山脊、枝条、地平线或建筑线，但会优先让所选主体保持完整。

只要两张图片能够正常读取，它会尽可能完成作品。

---

## English

### About

CrossWindow is a lightweight photographic collage skill for Codex.

It places two photographs one above the other, finds a distinctive fragment in each, and lets the fragments trade their original positions. A person enters another landscape, a shadow falls on unfamiliar ground, and an everyday object begins a quiet conversation with a different scene.

The photographs remain themselves—each simply gains a small window into the other.

### What It Makes

- Vertical two-photo diptychs
- Position-locked exchanges of people, animals, objects, light, shadows, or local scenery
- Complete, recognizable subjects whenever possible
- Adaptive windows for mixed orientations and proportions
- Fast final artwork without repeated candidates or manual review rounds

### Visual Character

CrossWindow favors clear, restrained photographic rectangles. It does not cut subjects onto transparent backgrounds, redraw the image, or smooth away differences in light and color.

Those differences—warm and cool, near and far, city and nature—are where the poetry begins.

### Installation

Place the repository in your Codex Skills directory:

```bash
git clone https://github.com/ekko-wang/cross-window-photo-diptych.git ~/.codex/skills/cross-window-photo-diptych-v2
```

Python 3 and Pillow are required:

```bash
python3 -m pip install Pillow
```

No extra installation is needed when Pillow is already included in your Codex workspace runtime.

### Use in Codex

Provide two photographs and ask:

```text
Use $cross-window-photo-diptych-v2 to process these two photos.
```

CrossWindow selects two suitable visual fragments and returns a vertical PNG artwork.

### Run the Script Directly

```bash
python scripts/diptych_v2.py quick \
  --top /path/photo-a.jpg \
  --bottom /path/photo-b.jpg \
  --top-box 0.45,0.21,0.55,0.39 \
  --bottom-box 0.43,0.55,0.69,0.89 \
  --output /path/crosswindow.png
```

Bounding boxes use normalized `x1,y1,x2,y2` coordinates, from `(0,0)` at the top-left to `(1,1)` at the bottom-right.

### Output

Each creation leaves two files:

```text
crosswindow.png
crosswindow.run.json
```

The PNG is the finished artwork; the JSON is a lightweight record of the composition. Existing files are preserved automatically under a numbered name.

### A Gentle Boundary

CrossWindow creates photographic windows with their surroundings intact—it is not a transparent-background cutout tool. A window may cross a ridge, branch, horizon, or architectural line, while keeping the chosen subject as complete as possible.

As long as both photographs can be read, CrossWindow will do its best to make the encounter happen.
