#!/usr/bin/env python3
"""Regenerate the light-on-dark halftone "recon prints" from Mikael's own photos.

  images/classroom-teaching.jpg  -> images/print/field.webp (+ field-600.webp)
  images/apac-stage.jpg          -> images/print/boardroom.webp (+ boardroom-600.webp)
  images/big-stage.jpg           -> images/print/stage.webp (+ stage-600.webp)

Each source is cropped and tone-adjusted, then rendered by tools/halftone.py
(AM dots, 45°, acetate-white ink on transparent). Provenance: images/print/README.md.
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageEnhance, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HALFTONE = os.path.join(ROOT, "tools", "halftone.py")

PRINTS = {
    # name: (source, crop box, prepare)
    "field": ("classroom-teaching.jpg", (0, 60, 1200, 800),
              lambda im: ImageOps.autocontrast(im.convert("L"), cutoff=2).point(lambda v: int(255 * ((v / 255) ** 1.9)))),
    "boardroom": ("apac-stage.jpg", (80, 170, 1200, 650),
                  lambda im: ImageEnhance.Brightness(im).enhance(1.35)),
    "stage": ("big-stage.jpg", (0, 210, 1200, 725),
              lambda im: ImageOps.autocontrast(im.convert("L"), cutoff=2).point(lambda v: int(255 * ((v / 255) ** 2.4)))),
}


def main():
    out_dir = os.path.join(ROOT, "images", "print")
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, (src, box, prepare) in PRINTS.items():
            staged = os.path.join(tmp, name + ".jpg")
            prepare(Image.open(os.path.join(ROOT, "images", src)).crop(box)).convert("RGB").save(staged, quality=95)
            for width, cell, suffix in ((900, 5.5, ""), (600, 4.5, "-600")):
                out = os.path.join(out_dir, f"{name}{suffix}.webp")
                subprocess.run([sys.executable, HALFTONE, staged, out, str(width), str(cell), "light"], check=True)
                im = Image.open(out)
                im.save(out, "WEBP", quality=80, method=6)
                print(out, im.size, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
