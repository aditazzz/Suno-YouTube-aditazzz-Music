"""Thumbnails + Short cover for TED Talk (Stepping Back).

usage: MUSIC_DIR=... python3 songs/ted-talk-stepping-back/thumb.py
  - YouTube thumbnail.jpg            a zoom tunnel: the standup inside the city inside the Earth inside the Milky Way,
                                     the question pinned in the middle, "SO — STEPPING BACK."
  - YouTube thumbnail option 2.jpg   the Earth from space with the question pinned on it
  - YouTube thumbnail option 3.jpg   the edge of the observable universe with the question in the middle
  - YouTube thumbnail (no text).jpg  the zoom tunnel without words
  - Short cover (9x16).jpg / (9x16, no text).jpg
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from studio.config import load_song
from studio.render import load_scene
from studio import core as C

sc = load_scene(HERE)
song = load_song(HERE)
OUT = song["out_dir"]; T = song["title"]
os.makedirs(OUT, exist_ok=True)
F_COND = os.path.join(C.FONTS, "Anton-Regular.ttf")
F_SANS = os.path.join(C.FONTS, "Inter-SemiBold.otf"); F_SANSM = os.path.join(C.FONTS, "Inter-Medium.otf")

def frame(t, W=1920, H=1080):
    C.STATE["bare"] = True
    im = sc.render_frame(t, W, H, int(t * 30))
    C.STATE["bare"] = False
    return Image.fromarray(im)

def bubble(img, x, y, s=1.0):
    """the question as it appears in the video: white card, tail pointing at (x, y), a blue pin"""
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(F_SANS, int(46 * s)); f2 = ImageFont.truetype(F_SANSM, int(34 * s))
    txt = "Is the file ready?"; tw = d.textlength(txt, font=f1)
    bw, bh = tw + 56 * s, 128 * s; bx, by = x - bw / 2, y - 26 * s - bh
    sh = Image.new("L", img.size, 0); ImageDraw.Draw(sh).rounded_rectangle((bx, by + 6 * s, bx + bw, by + bh + 6 * s), int(22 * s), fill=120)
    img.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(12 * s)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((bx, by, bx + bw, by + bh), int(22 * s), fill=(255, 255, 255))
    d.polygon([(x - 15 * s, by + bh - 2), (x + 15 * s, by + bh - 2), (x, by + bh + 20 * s)], fill=(255, 255, 255))
    d.text((bx + 28 * s, by + 16 * s), txt, font=f1, fill=(29, 28, 26))
    d.text((bx + bw - 26 * s, by + bh - 18 * s), "Delivered", font=f2, fill=(139, 135, 127), anchor="rb")
    r = 10 * s; d.ellipse((x - r - 4 * s, y + 4 * s - r - 4 * s, x + r + 4 * s, y + 4 * s + r + 4 * s), fill=(255, 255, 255))
    d.ellipse((x - r, y + 4 * s - r, x + r, y + 4 * s + r), fill=(47, 111, 224))

_FR = {}
def tunnel(W=1920, H=1080, cx=None, cy=None, ks=(0.60, 0.37, 0.21)):
    """nested frames, each a power of ten (or more) further out, all centred on the question"""
    cx = W / 2 if cx is None else cx; cy = H / 2 if cy is None else cy
    def fr_(t):
        if (t, W, H) not in _FR: _FR[(t, W, H)] = frame(t, W, H)
        return _FR[(t, W, H)]
    img = fr_(141.25).convert("RGB")                   # the Milky Way, filling the frame
    for t, k in [(76.0, ks[0]), (37.0, ks[1]), (12.0, ks[2])]:   # the Earth, the city, the standup
        fr = fr_(t)
        w, h = int(W * k), int(H * k)
        fr = fr.resize((w, h), Image.LANCZOS)
        x, y = int(cx - w / 2), int(cy - h / 2)
        sh = Image.new("L", img.size, 0); ImageDraw.Draw(sh).rectangle((x - 2, y + 10, x + w + 2, y + h + 14), fill=170)
        img.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
        ImageDraw.Draw(img).rectangle((x - 5, y - 5, x + w + 4, y + h + 4), fill=(255, 255, 255))
        img.paste(fr, (x, y))
    return img

def words(img, lines, x, y, size, side="left"):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(F_COND, size); sw = max(5, size // 14)
    sh = Image.new("L", img.size, 0); ds = ImageDraw.Draw(sh); yy = y
    for txt, col in lines:
        ds.text((x + sw, yy + sw * 1.5), txt, font=f, fill=210, stroke_width=sw, stroke_fill=210); yy += int(size * 1.02)
    img.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(sw * 1.3)))
    d = ImageDraw.Draw(img); yy = y
    for txt, col in lines:
        d.text((x, yy), txt, font=f, fill=col, stroke_width=sw, stroke_fill="#0b0b0f"); yy += int(size * 1.02)

def badge(img, x, y, h=58, txt="CLAUDE ANIMATED THIS"):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(F_COND, int(h * 0.6)); w = d.textlength(txt, font=f) + h * 0.9
    d.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=(217, 58, 43)); d.text((x + h * 0.45, y + h / 2 + 1), txt, font=f, fill=(255, 255, 255), anchor="lm")

if __name__ == "__main__":
    W, H = 1920, 1080
    tun = tunnel(W, H)
    tun_nt = tun.copy(); bubble(tun_nt, W / 2, H / 2 + 8, 0.9); tun_nt.save(os.path.join(OUT, f"{T} - YouTube thumbnail (no text).jpg"), quality=93)
    main = tunnel(W, H, cx=1235, cy=560, ks=(0.55, 0.34, 0.20)); bubble(main, 1235, 568, 0.85)
    badge(main, 52, 48)
    words(main, [("SO —", "#ff5b49"), ("STEPPING", "#ffffff"), ("BACK.", "#ffffff")], 52, 140, 168)
    main.save(os.path.join(OUT, f"{T} - YouTube thumbnail.jpg"), quality=93)
    # option 2: the Earth with the question pinned on it (slid right, words on the left)
    e0 = frame(76.0, W, H); e = Image.new("RGB", (W, H), (0, 0, 0)); e.paste(e0, (300, 0))
    bubble(e, W / 2 + 300, H / 2, 1.0); badge(e, 52, 48)
    words(e, [("HE SAID", "#ffffff"), ("“SO —", "#ffffff"), ("STEPPING", "#ffffff"), ("BACK.”", "#ff5b49")], 52, 130, 150)
    e.save(os.path.join(OUT, f"{T} - YouTube thumbnail option 2.jpg"), quality=93)
    # option 3: the edge of the observable universe
    u = frame(158.0, W, H); C.STATE["clean"] = False
    bubble(u, W / 2, H / 2, 1.0); badge(u, 52, 48)
    words(u, [("STILL WAITING", "#ffffff"), ("FOR AN ANSWER", "#ff5b49")], 52, 130, 120)
    u.save(os.path.join(OUT, f"{T} - YouTube thumbnail option 3.jpg"), quality=93)
    # Short cover: the zoom tunnel, vertical
    tv = tunnel(1080, 1920); bubble(tv, 540, 960 + 8, 0.9)
    tv.save(os.path.join(OUT, f"{T} - Short cover (9x16, no text).jpg"), quality=93)
    badge(tv, 48, 230, 56); words(tv, [("SO —", "#ff5b49"), ("STEPPING BACK.", "#ffffff")], 48, 310, 118)
    tv.save(os.path.join(OUT, f"{T} - Short cover (9x16).jpg"), quality=93)
    print("thumbnails written to", OUT)
