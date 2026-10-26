"""Thumbnails + Short cover for TED Talk (Charts): a front page of The Daily Standup.

usage: MUSIC_DIR=... python3 songs/ted-talk-charts/thumb.py
Writes into the song's output folder:
  TED Talk (Charts) - YouTube thumbnail.jpg              front page: "Who talked at standup" pie + IT'S A TED TALK. banner
  TED Talk (Charts) - YouTube thumbnail option 2.jpg     the banner slamming onto the dimmed stage (a frame of the video)
  TED Talk (Charts) - YouTube thumbnail option 3.jpg     the CORRECTION frame (a frame of the video)
  TED Talk (Charts) - YouTube thumbnail (no text).jpg    the front page without the banner
  TED Talk (Charts) - Short cover (9x16).jpg / (9x16, no text).jpg
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

def to_u8(img): return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
def rgb(c): return tuple(int(round(float(v) * 255)) for v in c)

def banner(lines, fs, kicker="BREAKING"):
    """The tabloid banner as an RGBA image: red block, cream Anton lines, black BREAKING tab on top."""
    f = ImageFont.truetype(sc.F_TAB, fs)
    fk = ImageFont.truetype(sc.F_SANS, int(fs * 0.21))
    widths = [f.getbbox(l)[2] - f.getbbox(l)[0] for l in lines]
    cap = f.getbbox("H")[3] - f.getbbox("H")[1]                     # cap height
    pad_x, pad_y, gap = int(fs * 0.24), int(fs * 0.22), int(fs * 0.16)
    bw = max(widths) + 2 * pad_x; bh = len(lines) * cap + (len(lines) - 1) * gap + 2 * pad_y
    kh = int(fs * 0.36); kw = sum(fk.getbbox(ch)[2] for ch in kicker) + int(fs * 0.03) * (len(kicker) - 1) + int(fs * 0.30)
    im = Image.new("RGBA", (bw, bh + kh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, kh, bw, kh + bh), fill=rgb(sc.RED) + (255,))
    d.rectangle((0, 0, kw, kh + 2), fill=rgb(sc.INK) + (255,))
    # tracked kicker
    x = int(fs * 0.15)
    for ch in kicker:
        d.text((x, kh / 2), ch, font=fk, fill=rgb(sc.CREAM) + (255,), anchor="lm"); x += fk.getbbox(ch)[2] + int(fs * 0.03)
    y = kh + pad_y
    for l, w in zip(lines, widths):
        top = f.getbbox("H")[1]
        d.text(((bw - w) / 2 - f.getbbox(l)[0], y - top), l, font=f, fill=rgb(sc.CREAM) + (255,))
        y += cap + gap
    return im

def paste_banner(base, ban, cx, cy, ang):
    """rotate the banner, drop a soft shadow, composite it centred at (cx, cy)."""
    r = ban.rotate(ang, resample=Image.BICUBIC, expand=True)
    x, y = int(cx - r.width / 2), int(cy - r.height / 2)
    a = r.split()[3]
    sh = Image.new("L", base.size, 0); sh.paste(a, (x + 10, y + 16)); sh = sh.filter(ImageFilter.GaussianBlur(18))
    base = Image.composite(Image.new("RGB", base.size, (40, 30, 26)), base, sh.point(lambda v: int(v * 0.42)))
    base.paste(r, (x, y), r)
    return base

def badge(img, x, y, h, txt="CLAUDE ANIMATED THIS"):
    d = ImageDraw.Draw(img); f = ImageFont.truetype(sc.F_TAB, int(h * 0.62))
    w = f.getbbox(txt)[2] + int(h * 0.9)
    d.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=rgb(sc.INK))
    d.text((x + h * 0.45, y + h / 2 + 1), txt, font=f, fill=rgb(sc.CREAM), anchor="lm")
    return w

def masthead(cv, W, vert):
    if not vert:
        sc.text(cv, "THE DAILY STANDUP", 960, 92, sc.F_MAST, 132, sc.INK, 1.0, 'c', 'm', track=4)
        sc.stroke(cv, [(80, 172), (1840, 172)], sc.INK, 3.0); sc.stroke(cv, [(80, 181), (1840, 181)], sc.INK, 1.4)
        sc.text(cv, "9:15 A.M.", 960, 214, sc.F_MONO, 36, sc.RED, 1.0, 'c', 'm')
        sc.text(cv, "PRICE: 15 MINUTES", 1840, 214, sc.F_SANSM, 32, sc.INK2, 1.0, 'r', 'm', track=2)
        sc.stroke(cv, [(80, 246), (1840, 246)], sc.INK, 1.6)
    else:
        sc.text(cv, "THE DAILY STANDUP", 540, 150, sc.F_MAST, 84, sc.INK, 1.0, 'c', 'm', track=2)
        sc.stroke(cv, [(56, 206), (1024, 206)], sc.INK, 3.0); sc.stroke(cv, [(56, 215), (1024, 215)], sc.INK, 1.4)
        sc.text(cv, "9:15 A.M.", 1024, 252, sc.F_MONO, 36, sc.RED, 1.0, 'r', 'm')
        sc.stroke(cv, [(56, 290), (1024, 290)], sc.INK, 1.6)

def pie(cv, pcx, pcy, R, title_xy, title_size, label_side=1):
    tx, ty = title_xy
    sc.text(cv, "FIG. 18", tx, ty - 62, sc.F_SANS, 34, sc.RED, 1.0, 'l', 'm', track=3)
    sc.text(cv, "Who talked at standup", tx, ty, sc.F_HEAD, title_size, sc.INK, 1.0, 'l', 'm')
    a0 = -math.pi / 2; sl = 2 * math.pi * 0.04
    sc.wedge(cv, pcx, pcy, 0, R, a0 + sl, a0 + 2 * math.pi, sc.RED)
    sc.wedge(cv, pcx, pcy, 0, R, a0, a0 + sl, sc.BAR)
    sc.text(cv, "TED", pcx - R * 0.08, pcy - R * 0.17, sc.F_NUM, R * 0.42, sc.CREAM, 1.0, 'c', 'm')
    sc.text(cv, "96%", pcx - R * 0.08, pcy + R * 0.26, sc.F_NUM, R * 0.42, sc.CREAM, 1.0, 'c', 'm')
    # the sliver's label: a hairline leader and "everyone else"
    am = a0 + sl / 2; ex, ey = pcx + R * 1.0 * math.cos(am), pcy + R * 1.0 * math.sin(am)
    lx, ly = pcx + R * 0.42, pcy - R * 1.12
    sc.stroke(cv, [(ex, ey), (lx - 10, ly + 4)], sc.INK2, 2.0)
    sc.text(cv, "everyone else 4%", lx, ly, sc.F_SANS, 34, sc.INK2, 1.0, 'l', 'm')

def front(vert, with_banner=True):
    W, H = (1080, 1920) if vert else (1920, 1080)
    img = sc.paper(W, H); cv = sc.Cv(img, W, H)
    masthead(cv, W, vert)
    if not vert:
        pie(cv, 470, 740, 280, (96, 352), 66)
    else:
        pie(cv, 540, 1380, 290, (74, 990), 64)
    base = Image.fromarray(to_u8(img))
    if not vert: badge(base, 80, 194, 44)
    else: badge(base, 56, 230, 44)
    if with_banner:
        if not vert:
            ban = banner(["IT'S A", "TED TALK."], 228); base = paste_banner(base, ban, 1388, 636, -3.0)
        else:
            ban = banner(["IT'S A", "TED TALK."], 196); base = paste_banner(base, ban, 540, 560, -3.0)
    if with_banner:
        cv2_img = np.asarray(base).astype(np.float32) / 255; cv = sc.Cv(cv2_img, W, H)
        if not vert: sc.pen_text(cv, "(still going)", 1560, 1000, 66, 1.0, 'c')
        else: sc.pen_text(cv, "(still going)", 770, 884, 62, 1.0, 'c')
        base = Image.fromarray(to_u8(cv2_img))
    return base

def video_frame(t, W=1920, H=1080, lyrics=False, clean=False):
    C.STATE["clean"] = clean
    keep = C.STATE.get("lyric_filter")
    if not lyrics: C.STATE["lyric_filter"] = lambda L: False
    im = sc.render_frame(t, W, H, int(t * 30))
    C.STATE["lyric_filter"] = keep; C.STATE["clean"] = False
    return Image.fromarray(im)

if __name__ == "__main__":
    front(False).save(os.path.join(OUT, f"{T} - YouTube thumbnail.jpg"), quality=93)
    video_frame(58.9).save(os.path.join(OUT, f"{T} - YouTube thumbnail (no text).jpg"), quality=93)
    video_frame(27.62).save(os.path.join(OUT, f"{T} - YouTube thumbnail option 2.jpg"), quality=93)
    video_frame(121.3).save(os.path.join(OUT, f"{T} - YouTube thumbnail option 3.jpg"), quality=93)
    front(True).save(os.path.join(OUT, f"{T} - Short cover (9x16).jpg"), quality=93)
    front(True, with_banner=False).save(os.path.join(OUT, f"{T} - Short cover (9x16, no text).jpg"), quality=93)
    print("thumbnails written to", OUT)
