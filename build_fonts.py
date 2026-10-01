#!/usr/bin/env python3
"""Self-hosted fonts for the redesign (spec §4.2, §7.3).

- Noto Serif TC (display only): instanced at 600 and 900 from the variable source, then
  subset to the CJK characters inside `.cjk-display` elements across the partials, the EN
  pages and the generated /zh/ pages. Chinese body text uses the reader's system font.
- Overpass: instanced at 400/600/800/900, subset to Latin.

Sources live in tools/font-src/ (git-ignored; see PROJECT_HANDOFF.md).
Run last, after build_zh.py (see build_all.sh).
Requires fontTools + brotli for system Python.
"""
import glob
import os

import lxml.html
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "tools", "font-src")
OUT = os.path.join(ROOT, "vendor", "fonts")
# punctuation used in display settings, kept even when no page uses it yet
ALWAYS = "「」『』、。，：；！？（）《》・"
LATIN = "U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2010-2027,U+2030,U+2039-203A,U+20AC,U+2122"


def _is_cjk(ch):
    o = ord(ch)
    return 0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or 0x3000 <= o <= 0x303F


def collect():
    """Sorted unique CJK characters used inside .cjk-display, plus ALWAYS."""
    paths = (glob.glob(os.path.join(ROOT, "partials", "*.html"))
             + glob.glob(os.path.join(ROOT, "*.html"))
             + glob.glob(os.path.join(ROOT, "blog", "*.html"))
             + glob.glob(os.path.join(ROOT, "zh", "*.html"))
             + glob.glob(os.path.join(ROOT, "zh", "blog", "*.html")))
    chars = set(ALWAYS)
    for p in paths:
        with open(p, encoding="utf-8") as f:
            src = f.read()
        if "cjk-display" not in src:
            continue
        root = lxml.html.fromstring(src)
        for el in root.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," cjk-display ")]'):
            chars.update(c for c in el.text_content() if _is_cjk(c))
    return "".join(sorted(chars))


def _write(font, out_path, text=None, unicodes=None):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]   # keep vert/vrt2 for vertical writing, kern, etc.
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    if text is not None:
        sub.populate(text=text)
    else:
        sub.populate(unicodes=subset.parse_unicodes(unicodes))
    sub.subset(font)
    font.flavor = "woff2"
    # deterministic output: a rebuild with the same glyphs must not change the file
    font["head"].modified = font["head"].created
    font.recalcTimestamp = False
    font.save(out_path)


def main():
    os.makedirs(OUT, exist_ok=True)
    chars = collect()
    serif_src = os.path.join(SRC, "NotoSerifTC[wght].ttf")
    for w in (600, 900):
        f = instancer.instantiateVariableFont(TTFont(serif_src), {"wght": w})
        _write(f, os.path.join(OUT, f"noto-serif-tc-{w}-subset.woff2"), text=chars)
    sans_src = os.path.join(SRC, "Overpass[wght].ttf")
    for w in (400, 600, 800, 900):
        f = instancer.instantiateVariableFont(TTFont(sans_src), {"wght": w})
        _write(f, os.path.join(OUT, f"overpass-{w}-latin.woff2"), unicodes=LATIN)
    sizes = {os.path.basename(p): os.path.getsize(p) // 1024 for p in glob.glob(os.path.join(OUT, "*-subset.woff2"))}
    print(f"build_fonts: {len(chars)} CJK display glyphs; subsets (KB): {sizes}")


if __name__ == "__main__":
    main()
