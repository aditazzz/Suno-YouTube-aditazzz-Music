"""The Promptress: my terminal window (from my cover photo), typed on in the opening and the outro.
Dark translucent window, thin lime border, traffic lights, "aditazzz@witchbox: ~", JetBrains Mono in terminal green."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import film_kit as F

W, H = 1920, 1080
LIME = (168, 232, 96)
AMBER = (255, 168, 64)
PROMPT = "aditazzz@witchbox:~$ "
OFF = os.environ.get("NOTERM") == "1"          # NOTERM=1: render the film without the terminal (the vertical cut lays its own)
SIZE, LINE, BAR, PADX, PADT, PADB, RAD = 40, 56, 72, 50, 30, 26, 24
_f = {}
def font(name, size):
    k = (name, size)
    if k not in _f: _f[k] = ImageFont.truetype(os.path.join(F.FONTS, name), size)
    return _f[k]

def ease(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)

def window(img, x, y, w, lines, alpha=1.0, cursor=None, rise=0.0, bgr=True):
    """lines: [(text, rgb)], a leading "✓ " draws a check mark. cursor: (line index, on 0..1) after that line's text."""
    if alpha <= 0: return img
    n = len(lines); h = BAR + PADT + n * LINE + PADB
    y = int(y + rise)
    lay = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((0, 0, w - 1, h - 1), RAD, fill=(14, 15, 13, 222))
    d.rounded_rectangle((0, 0, w - 1, BAR + RAD), RAD, fill=(36, 37, 34, 235))
    d.rectangle((0, BAR, w - 1, BAR + RAD + 2), fill=(14, 15, 13, 222))
    d.line((2, BAR, w - 3, BAR), fill=(70, 72, 66, 255), width=2)
    d.rounded_rectangle((0, 0, w - 1, h - 1), RAD, outline=LIME + (150,), width=2)
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx, cy, r = 40 + i * 44, BAR // 2, 13
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c + (255,))
    ft = font("InterDisplay-Light.otf", 32)
    d.text((40 + 2 * 44 + 48, BAR // 2), "aditazzz@witchbox: ~", font=ft, fill=(200, 200, 192, 255), anchor="lm")
    fm = font("JBMono-400.ttf", SIZE); adv = fm.getlength("M")
    ends = []
    for i, (s, col) in enumerate(lines):
        ty = BAR + PADT + i * LINE + LINE // 2; tx = PADX
        if s.startswith("✓"):      # the font has no check mark: draw one
            u = SIZE * 0.5
            d.line([(tx + u * 0.08, ty + u * 0.02), (tx + u * 0.42, ty + u * 0.40), (tx + u * 1.02, ty - u * 0.52)], fill=col + (255,), width=4, joint="curve")
            tx += adv; s = s[1:]
        d.text((tx, ty), s, font=fm, fill=col + (255,), anchor="lm")
        ends.append((tx + fm.getlength(s), ty))
    if cursor is not None and cursor[1] > 0:
        ex, ey = ends[cursor[0]]
        d.rectangle((ex + 4, ey - SIZE * 0.55, ex + 4 + adv * 0.82, ey + SIZE * 0.52), fill=LIME + (int(255 * cursor[1]),))
    a = np.asarray(lay, np.float32) / 255
    rgb, al = (a[..., 2::-1] if bgr else a[..., :3]), a[..., 3:] * alpha          # the film's frames are BGR (OpenCV)
    HH, WW = img.shape[:2]
    y0, x0 = max(0, y), max(0, x); y1, x1 = min(HH, y + lay.height), min(WW, x + lay.width)
    sub = img[y0:y1, x0:x1]
    img[y0:y1, x0:x1] = sub * (1 - al[y0 - y:y1 - y, x0 - x:x1 - x]) + rgb[y0 - y:y1 - y, x0 - x:x1 - x] * al[y0 - y:y1 - y, x0 - x:x1 - x]
    return img

def typed(s, t, t0, cps):
    return s[:max(0, min(len(s), int((t - t0) * cps)))]

def blink(t, beat):
    return 1.0 if (t / beat) % 1.0 < 0.5 else 0.0

# ---------------------------------------------------------------- opening: moon --capture over her moon footage
OPEN_IN, OPEN_TYPE, OPEN_OUT = 4.90, 5.20, 9.55
def opening(img, t, beat, at=None, bgr=True):
    if OFF or t < OPEN_IN or t > OPEN_OUT + 0.5: return img
    al = ease((t - OPEN_IN) / 0.3) * (1 - ease((t - OPEN_OUT) / 0.40))
    cmd = "moon --capture"
    L = [(PROMPT + typed(cmd, t, OPEN_TYPE, 15), LIME)]
    busy = t < OPEN_TYPE + len(cmd) / 15
    for t0, word in ((6.40, "Capturing moon"), (7.30, "Aligning"), (8.20, "Acquiring")):
        if t >= t0: L.append((word + "." * min(3, int((t - t0) / 0.22) + 1), LIME))
    if t >= 9.05: L.append(("✓ Done.", LIME))
    cur = (len(L) - 1, 1.0 if busy else blink(t, beat))
    x, y, w = at or (int(0.040 * W), int(0.575 * H), 1010)
    return window(img, x, y, w, L, al, cur, rise=10 * (1 - ease((t - OPEN_IN) / 0.3)), bgr=bgr)

# ---------------------------------------------------------------- outro: the wish, granted, with terms
OUT_IN = 252.55
def outro(img, t, beat, dur, at=None, bgr=True):
    if OFF or t < OUT_IN: return img
    al = ease((t - OUT_IN) / 0.3)
    cmd = "wish --grant"
    L = [(PROMPT + typed(cmd, t, 252.95, 15), LIME)]
    busy = 252.95 <= t < 252.95 + len(cmd) / 15
    g = "✓ Your wish has been granted."
    if t >= 254.40:
        L.append((typed(g, t, 254.40, 40), LIME)); busy = busy or t < 254.40 + len(g) / 40
    tc = "Terms and conditions apply."
    if t >= 260.93:
        L.append((typed(tc, t, 260.93, 40), AMBER)); busy = busy or t < 260.93 + len(tc) / 40
    if t >= 261.95: L.append((PROMPT, LIME))
    on = 1.0 if (busy or t > dur - 0.6) else blink(t, beat)
    x, y, w = at or (int(0.5 * W - 480), int(0.635 * H), 960)
    return window(img, x, y, w, L, al, (len(L) - 1, on), rise=10 * (1 - al), bgr=bgr)
