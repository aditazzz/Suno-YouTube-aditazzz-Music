#!/usr/bin/env python3
"""The hero image at the very top of the README (docs/img/hero.jpg): one line about the repo and a 4 x 3 grid of
favorite thumbnails, sized to read well as a screenshot or a social preview. The count comes from site/videos.json,
so run it alongside tools/wall.py after adding a video. Change PICKS to change the grid.

  python3 tools/hero.py          # needs Inter-SemiBold.otf, Inter-Regular.otf and Inter-Medium.otf in assets/fonts
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICKS = ["look-what-i-can-do", "asking-for-a-friend", "great-idea-ted", "please-hold",
         "you-said-you-needed-space", "i-have-a-blocker", "ted-talk-charts", "rate-limited",
         "omg-agents-swarm", "graceful-shutdown-opus", "next-token", "run-it"]
W, COLS, GAP, PAD, HEAD = 1600, 4, 10, 40, 250
BG, IVORY, AMBER, GREY, DIM = (13, 14, 18), (245, 245, 245), (255, 196, 84), (175, 178, 186), (140, 144, 152)
LINE = "Songs I write, and films I build in code with Claude Code and Codex. The source for each is here."


def font(name, size):
    return ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", name), size)


def main():
    count = len(json.load(open(os.path.join(ROOT, "site", "videos.json"))))
    tw = (W - 2 * PAD - (COLS - 1) * GAP) // COLS; th = tw * 9 // 16
    rows = -(-len(PICKS) // COLS)
    im = Image.new("RGB", (W, HEAD + rows * th + (rows - 1) * GAP + PAD + 70), BG); d = ImageDraw.Draw(im)
    big = font("Inter-SemiBold.otf", 78)
    a = f"{count} music videos. "
    d.text((PAD, 52), a, font=big, fill=IVORY)
    d.text((PAD + d.textlength(a, font=big), 52), "Every frame is code.", font=big, fill=AMBER)
    d.text((PAD, 160), LINE, font=font("Inter-Regular.otf", 30), fill=GREY)
    for i, slug in enumerate(PICKS):
        t = Image.open(os.path.join(ROOT, "songs", slug, "thumbnail.jpg")).convert("RGB")
        w, h = t.size; keep = w * 9 // 16
        if h > keep: t = t.crop((0, (h - keep) // 2, w, (h - keep) // 2 + keep))
        r, c = divmod(i, COLS)
        im.paste(t.resize((tw, th), Image.LANCZOS), (PAD + c * (tw + GAP), HEAD + r * (th + GAP)))
    d.text((PAD, HEAD + rows * th + (rows - 1) * GAP + 24), "youtube.com/@adita_zzz   ·   aditazzz.github.io",
           font=font("Inter-Medium.otf", 26), fill=DIM)
    out = os.path.join(ROOT, "docs", "img", "hero.jpg")
    im.save(out, quality=88, optimize=True)
    print(f"{out}: {count} videos, {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()
