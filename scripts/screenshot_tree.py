"""生成项目目录树截图。
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots" / "tree.png"
OUT.parent.mkdir(parents=True, exist_ok=True)


def find_font(candidates, size=14):
    for fp in candidates:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


# 中文目录/文件名需要中文字体，但 Cascadia Mono 不带中文，所以用微软雅黑为主，
# 字符宽度差异用统一 pad 解决
FONT_CN = find_font([r"C:\Windows\Fonts\msyh.ttc",
                     r"C:\Windows\Fonts\simhei.ttf"], 14)
FONT_CN_BOLD = find_font([r"C:\Windows\Fonts\msyh.ttc",
                          r"C:\Windows\Fonts\simhei.ttf"], 16)


def build_tree_lines(root: Path, prefix: str = "") -> list[tuple[str, bool]]:
    """返回 [(text, is_dir), ...]"""
    entries = sorted([p for p in root.iterdir() if p.name not in {
        ".git", "__pycache__", "data", "output", "scripts",
        ".gitignore"
    } and not p.name.startswith(".")])
    out = []
    for i, p in enumerate(entries):
        last = i == len(entries) - 1
        connector = "└── " if last else "├── "
        out.append((prefix + connector + p.name, p.is_dir()))
        if p.is_dir():
            extension = "    " if last else "│   "
            out.extend(build_tree_lines(p, prefix + extension))
    return out


def main():
    tree_lines = [(ROOT.name + "/", True)] + build_tree_lines(ROOT)
    extra = [
        ("", False),
        ("  # data/ output/ 已在 .gitignore 忽略", False),
        ("  # __pycache__/ 也是", False),
    ]
    tree_lines.extend(extra)

    line_h = FONT_CN.size + 8
    pad = 20
    tmp = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(tmp)
    max_w = max(d.textbbox((0, 0), ln, font=FONT_CN)[2] for ln, _ in tree_lines)
    img_w = max_w + pad * 2 + 20
    img_h = line_h * len(tree_lines) + pad * 2 + 60

    img = Image.new("RGB", (img_w, img_h), (252, 252, 252))
    d = ImageDraw.Draw(img)
    title = "📁 " + ROOT.name + "/"
    d.text((pad, pad), title, fill=(40, 60, 120), font=FONT_CN_BOLD)
    y = pad + FONT_CN_BOLD.size + 12
    for ln, is_dir in tree_lines[1:]:
        if not ln:
            y += line_h // 2
            continue
        color = (32, 90, 170) if is_dir else (60, 60, 60)
        d.text((pad + 16, y), ln, fill=color, font=FONT_CN)
        y += line_h

    img.save(OUT, "PNG", optimize=True)
    print(f"[OK] {OUT}  size={img.size}")


if __name__ == "__main__":
    main()
