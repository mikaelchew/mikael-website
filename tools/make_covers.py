#!/usr/bin/env python3
"""Generate "map covers" for blog posts tied to the book.

For every content/posts/<slug>.json that has a "cover_zh" keyword (two or three characters),
writes images/blog/<slug>.webp (1200x675) and <slug>-600.webp: the site's contour map
(images/map/terrain.svg, each post looking through its own window onto it), the keyword set
vertically in red Noto Serif TC Black, and the post's English title in Overpass Black.
Fonts come from tools/font-src/ (see build_fonts.py). Provenance: images/blog/README.md.

Usage: /usr/bin/python3 tools/make_covers.py
"""
import glob
import hashlib
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 675
NAVY, ACETATE, RED, CONTOUR = (34, 48, 58), (242, 242, 238), (240, 112, 95), (182, 196, 190)


def contour_paths():
    svg = open(os.path.join(ROOT, "images", "map", "terrain.svg"), encoding="utf-8").read()
    out = []
    for d in re.findall(r'd="([^"]+)"', svg):
        for sub in d.split("M")[1:]:
            nums = list(map(int, sub.split()))
            out.append(list(zip(nums[0::2], nums[1::2])))
    return out


def font(name, size, weight):
    f = ImageFont.truetype(os.path.join(ROOT, "tools", "font-src", name), size)
    f.set_variation_by_axes([weight])
    return f


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if line and draw.textlength(t, font=fnt) > width:
            lines.append(line)
            line = w
        else:
            line = t
    return lines + [line]


def cover(post, paths):
    seed = int(hashlib.md5(post["slug"].encode()).hexdigest(), 16)
    ox, oy = seed % 1200, (seed // 1200) % 825  # each post gets its own window onto the map
    im = Image.new("RGB", (W, H), NAVY)
    dr = ImageDraw.Draw(im, "RGBA")
    for pts in paths:
        p = [(x - ox, y - oy) for x, y in pts]
        if any(-50 < x < W + 50 and -50 < y < H + 50 for x, y in p):
            dr.line(p, fill=CONTOUR + (60,), width=2)
    zh = post["cover_zh"]
    size = 170 if len(zh) <= 2 else 140
    zf = font("NotoSerifTC[wght].ttf", size, 900)
    y = (H - (size + 5) * len(zh)) // 2
    for ch in zh:
        dr.text((W - 70 - size, y), ch, font=zf, fill=RED)
        y += size + 5
    dr.text((70, 80), post["category_en"], font=font("Overpass[wght].ttf", 26, 800), fill=CONTOUR)
    ef = font("Overpass[wght].ttf", 64, 900)
    lines = wrap(dr, post["short_en"], ef, W - 140 - size - 120)
    y = H - 70 - 72 * len(lines)
    for line in lines:
        dr.text((70, y), line, font=ef, fill=ACETATE)
        y += 72
    out = os.path.join(ROOT, "images", "blog", post["slug"])
    im.save(out + ".webp", "WEBP", quality=82, method=6)
    im.resize((600, 338), Image.LANCZOS).save(out + "-600.webp", "WEBP", quality=82, method=6)
    return out + ".webp"


def main():
    paths = contour_paths()
    n = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "content", "posts", "*.json"))):
        post = json.load(open(p, encoding="utf-8"))
        if post.get("cover_zh"):
            print("cover", os.path.relpath(cover(post, paths), ROOT))
            n += 1
    print("make_covers: %d covers" % n)


if __name__ == "__main__":
    main()
