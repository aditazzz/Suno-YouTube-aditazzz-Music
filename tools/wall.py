#!/usr/bin/env python3
"""The wall of thumbnails at the top of the README (docs/img/wall.jpg): every public video in site/videos.json, newest
first, in four rows, with the count in the last tile. Run it after adding a video, before tools/build_site.py.

  python3 tools/wall.py          # needs Inter-SemiBold.otf and Inter-Medium.otf in assets/fonts (see its README)
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW, TH, ROWS = 384, 216, 4                      # one tile is a thumbnail at 384x216
BG, IVORY, GREEN = (14, 14, 14), (245, 241, 232), (131, 223, 124)


def font(name, size):
    return ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", name), size)


def main():
    vids = json.load(open(os.path.join(ROOT, "site", "videos.json")))
    slugs = sorted(vids, key=lambda s: vids[s]["date"], reverse=True)
    cols = math.ceil((len(slugs) + 1) / ROWS)     # +1: the count tile, which also takes any spare tiles at the end
    wall = Image.new("RGB", (cols * TW, ROWS * TH), BG)
    for i, slug in enumerate(slugs):
        im = Image.open(os.path.join(ROOT, "songs", slug, "thumbnail.jpg")).convert("RGB")
        wall.paste(im.resize((TW, TH), Image.LANCZOS), ((i % cols) * TW, (i // cols) * TH))
    x, y = (len(slugs) % cols) * TW + 23, (len(slugs) // cols) * TH
    d = ImageDraw.Draw(wall)
    for text, name, size, color, top in ((f"{len(slugs)} music videos", "Inter-SemiBold.otf", 36, IVORY, 33),
                                         ("every frame is code", "Inter-Medium.otf", 22, GREEN, 79),
                                         ("@adita_zzz", "Inter-SemiBold.otf", 28, IVORY, 130),
                                         ("aditazzz.github.io", "Inter-Medium.otf", 22, GREEN, 167)):
        f = font(name, size)
        d.text((x, y + top - f.getbbox(text)[1]), text, font=f, fill=color)   # `top` is where the ink starts
    out = os.path.join(ROOT, "docs", "img", "wall.jpg")
    wall.save(out, quality=86, optimize=True, progressive=True)
    print(f"{out}: {len(slugs)} videos, {cols} x {ROWS} tiles, {wall.size[0]}x{wall.size[1]}")


if __name__ == "__main__":
    main()
