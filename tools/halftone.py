"""Render a newspaper AM halftone (ink dots on transparent) from a photo.
Origin: Mikael Chew's own stage photographs in images/. Output is derived, not generated."""
import sys, math
from PIL import Image, ImageOps, ImageDraw, ImageEnhance, ImageFilter
src, out, width, cell = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
ink = (242, 242, 238, 255) if len(sys.argv) > 5 and sys.argv[5] == "light" else (20, 20, 20, 255)
im = Image.open(src).convert("L")
h = round(im.height * width / im.width)
im = im.resize((width, h), Image.LANCZOS)
im = ImageOps.autocontrast(im, cutoff=1)
im = ImageEnhance.Contrast(im).enhance(1.25)
im = im.filter(ImageFilter.GaussianBlur(cell / 4))
S = 3  # supersample for smooth dots
canvas = Image.new("RGBA", (width * S, h * S), (0, 0, 0, 0))
d = ImageDraw.Draw(canvas)
ang = math.radians(45)
ca, sa = math.cos(ang), math.sin(ang)
diag = int(math.hypot(width, h)) + 2
px = im.load()
r = -diag
while r < diag:
    c = -diag
    while c < diag:
        x = c * ca - r * sa + width / 2
        y = c * sa + r * ca + h / 2
        if 0 <= x < width and 0 <= y < h:
            dark = (px[int(x), int(y)] / 255) if ink[0] > 128 else (1 - px[int(x), int(y)] / 255)
            rad = cell * 0.5 * math.sqrt(dark) * 1.42
            if rad > 0.25:
                d.ellipse([(x - rad) * S, (y - rad) * S, (x + rad) * S, (y + rad) * S], fill=ink)
        c += cell
    r += cell
canvas = canvas.resize((width, h), Image.LANCZOS)
canvas.save(out, "WEBP", lossless=True, quality=100, method=6)
print(out, canvas.size)
