#!/usr/bin/env python3
"""Vertical (1080x1920) Shorts renderer built on render.py.
Usage: python3 vertical.py <short_id> out.mp4      (video only, no audio)
       python3 vertical.py frame <short_id> <t> out.png
"""
import sys, math, subprocess
from PIL import Image, ImageDraw
argv = sys.argv[:]
sys.argv = ["x"]
import render as R
from render import *

VW, VH = 1080, 1920

SHORTS = {
    "1": {"a": 9.6, "b": 45.8, "hook": ["A 6-YEAR-OLD", "vs WAR THUNDER"], "name": "owen-get-off-war-thunder"},
    "2": {"a": 45.8, "b": 77.5, "hook": ["HE KNOWS", "ALL HIS TANKS"], "name": "alexs-spotter-guide"},
    "3": {"a": 77.5, "b": DUR, "hook": ["MOM'S", "COMING AROUND"], "name": "moms-coming-around"},
}

# silence the 16:9 HUD / lyric band / kill feed — the vertical layout draws its own
R.draw_hud = lambda *a, **k: None
R.draw_lyrics = lambda *a, **k: None
R.draw_feed = lambda *a, **k: None

VID_Y0 = 400
VID_H = 748
SAFE_W = 820  # keep lyric rows clear of the Shorts right-side buttons


def wrap_words(words, fnt, max_w):
    rows, cur = [], []
    for w, wt in words:
        trial = " ".join(x for x, _ in cur + [(w, wt)])
        if cur and fnt.getlength(trial) > max_w:
            rows.append(cur)
            cur = [(w, wt)]
        else:
            cur.append((w, wt))
    if cur:
        rows.append(cur)
    return rows


def draw_lyrics_vert(img, d, t):
    ln = R.current_line(t)
    if ln is None:
        return
    kind = ln["kind"]
    big = kind in ("chorus", "chorus_final")
    words = [w for row in ln["rows"] for w in row]
    size = 100 if big else 92
    if kind == "spoken":
        size = 84
    fnt = font(F_SHOUT, size)
    rows = wrap_words(words, fnt, SAFE_W)
    if len(rows) > 3:
        fnt = font(F_SHOUT, size - 16)
        rows = wrap_words(words, fnt, SAFE_W)
    gap = int(fnt.size * 1.08)
    y = 1300
    for row in rows:
        s_full = " ".join(w for w, _ in row)
        total = fnt.getlength(s_full)
        x = 540 - total / 2
        space = fnt.getlength(" ")
        for (w, wt) in row:
            ww = fnt.getlength(w)
            cx = x + ww / 2
            age = t - wt
            if t < wt:
                col = (120, 120, 118) if kind == "spoken" else (140, 140, 135)
                text(d, (cx, y), w, fnt, col, stroke=6)
            elif age < 0.18:
                sc = 1 + 0.3 * (1 - age / 0.18)
                stamp(img, w, fnt, (cx, y), AMBER, scale=sc, stroke=7)
            else:
                hot = w.strip("(),.!?\"").upper() in ("OWEN", "MATCH!", "UP!") or (w.isupper() and len(w) > 2)
                col = AMBER if (hot and big) else WHITE
                if kind == "spoken":
                    col = (235, 235, 225)
                text(d, (cx, y), w, fnt, col, stroke=7)
            x += ww + space
        y += gap


def vframe(short, t):
    base = R.render_frame(t).crop((180, 0, 1740, 1080)).resize((VW, VID_H), Image.LANCZOS)
    img = Image.new("RGB", (VW, VH), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, VW, 80):
        d.line((x, 0, x, VH), fill=(22, 30, 24), width=1)
    for y in range(0, VH, 80):
        d.line((0, y, VW, y), fill=(22, 30, 24), width=1)
    hazard_band(d, 40, 80, offset=int(t * 120))
    hazard_band(d, 1840, 1880, offset=-int(t * 120))
    # title block
    stamp(img, "GET OFF", font(F_STENCIL, 108), (540, 150), WHITE, stroke=10)
    stamp(img, "WAR THUNDER", fit_font(F_STENCIL, "WAR THUNDER", 940, 108), (540, 262), AMBER, stroke=10)
    text(d, (540, 352), "a song by a 6-year-old about his big brother", fit_font(F_HUD, "a song by a 6-year-old about his big brother", 1000, 42, 30), HUD, stroke=3)
    # video
    img.paste(base, (0, VID_Y0))
    d.rectangle((0, VID_Y0 - 4, VW - 1, VID_Y0 + VID_H + 4), outline=AMBER, width=4)
    # hook overlay (first 1.3 s)
    a, b = short["a"], short["b"]
    age = t - a
    if age < 1.3:
        fade = 1.0 if age < 1.0 else clamp(1 - (age - 1.0) / 0.3)
        ov = Image.new("RGBA", (VW, VID_H), (0, 0, 0, int(150 * fade)))
        img.paste(ov, (0, VID_Y0), ov)
        if fade > 0.05:
            cy = VID_Y0 + VID_H / 2
            stamp(img, short["hook"][0], fit_font(F_STENCIL, short["hook"][0], 980, 120), (540, cy - 70), WHITE, rot=-3, stroke=12, alpha=int(255 * fade))
            stamp(img, short["hook"][1], fit_font(F_STENCIL, short["hook"][1], 980, 120), (540, cy + 70), RED, rot=-3, stroke=12, alpha=int(255 * fade))
    # badge
    s2 = "ANIMATED BY CLAUDE FABLE 5.1"
    bf = fit_font(F_STENCIL, s2, 720, 50)
    w2 = bf.getlength(s2) + 60
    bx, by = 60, 1206
    rrect(d, (bx, by - 40, bx + w2, by + 40), 14, fill=RED, outline=WHITE, width=5)
    text(d, (bx + w2 / 2, by), s2, bf, WHITE)
    # lyrics
    draw_lyrics_vert(img, d, t)
    # artist line
    text(d, (540, 1780), "ADITAZZZ  feat.  ALEX (age 6)", font(F_HUD, 44), HUD, stroke=3)
    # end fade for last 0.5 s
    rem = b - t
    if rem < 0.5:
        ov = Image.new("RGBA", (VW, VH), (0, 0, 0, int(255 * (1 - rem / 0.5))))
        img.paste(ov, (0, 0), ov)
    return img


def main():
    if argv[1] == "frame":
        short = SHORTS[argv[2]]
        vframe(short, float(argv[3])).save(argv[4])
        return
    short = SHORTS[argv[1]]
    out = argv[2]
    f0, f1 = int(round(short["a"] * FPS)), int(round(short["b"] * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        img = vframe(short, min(f / FPS, DUR - 0.001))
        p.stdin.write(img.tobytes())
        if (f - f0) % 150 == 0:
            print(f"{out}: {f - f0}/{f1 - f0}", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main()
