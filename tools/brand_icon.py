"""Prepare the selected puzzle logo from tools/brand/enterprise-agent-puzzle.png.
Drop near-invisible specks, normalize nearly opaque pixels, then crop, center and resize.
python3 tools/brand_icon.py <site dir>
Writes assets/brand/icon.png (transparent, 256 px), and assets/favicon.png (64 px) and assets/apple-touch-icon.png (180 px)
with the figure on a white tile, since the dark green figure does not show on a dark tab bar.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

SITE = Path(sys.argv[1])
SRC = Path(__file__).parent / 'brand/enterprise-agent-puzzle.png'
im = Image.open(SRC).convert('RGBA')
alpha = im.getchannel('A').point(lambda v: 0 if v < 16 else (255 if v >= 250 else v))
im.putalpha(alpha)
fig = im.crop(alpha.getbbox())
w, h = fig.size
side = max(w, h)
square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
square.paste(fig, ((side - w) // 2, (side - h) // 2))


def scaled(img, n):
    """Resize with premultiplied alpha, so the edge does not pick up the black of the transparent pixels."""
    return img.convert('RGBa').resize((n, n), Image.LANCZOS).convert('RGBA')


def tile(n, fill=0.8, radius=0.24):
    big = n * 4
    t = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(t).rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * radius), fill=(255, 255, 255, 255))
    f = scaled(square, int(big * fill))
    t.alpha_composite(f, ((big - f.width) // 2, (big - f.height) // 2))
    return scaled(t, n)


(SITE / 'assets/brand').mkdir(parents=True, exist_ok=True)
scaled(square, 256).save(SITE / 'assets/brand/icon.png', optimize=True)
tile(64).save(SITE / 'assets/favicon.png', optimize=True)
apple = Image.new('RGB', (180, 180), (255, 255, 255))      # iOS wants an opaque square and rounds the corners itself
f = scaled(square, 140)
apple.paste(f, (20, 20), f)
apple.save(SITE / 'assets/apple-touch-icon.png', optimize=True)
print('figure', w, 'x', h, 'from', SRC.name)
