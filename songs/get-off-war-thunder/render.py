#!/usr/bin/env python3
"""Get Off War Thunder — 'Little Brother Simulator' music video renderer.
Usage:
  python3 render.py frame <t> out.png        # render one frame
  python3 render.py segment <f0> <f1> out.mp4  # render frames [f0,f1) to mp4 (no audio)
  python3 render.py thumb out.png
"""
import sys, math, json, random, subprocess
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
FPS = 30
DUR = 120.56
FONT_DIR = "fonts/"
F_STENCIL = FONT_DIR + "BlackOpsOne-Regular.ttf"
F_SHOUT = FONT_DIR + "Bangers-Regular.ttf"
F_HUD = FONT_DIR + "RussoOne-Regular.ttf"
F_MONO = FONT_DIR + "ShareTechMono-Regular.ttf"
F_DIGI = FONT_DIR + "Orbitron[wght].ttf"

feats = json.load(open("audio_feats.json"))
BPM, PHASE, RMS = feats["bpm"], feats["phase"], feats["rms"]
PERIOD = 60.0 / BPM

# ---------------- palette ----------------
BG = (13, 17, 14)
WALL = (38, 44, 52)
FLOOR = (28, 31, 36)
HUD = (120, 255, 150)
HUD_DIM = (60, 130, 80)
AMBER = (255, 196, 64)
RED = (255, 72, 60)
WHITE = (246, 246, 236)
INK = (10, 10, 12)
SKY_DAY = ((96, 178, 255), (178, 224, 255))
SKY_SUNSET = ((255, 120, 70), (255, 206, 120))
SKY_NIGHT = ((16, 18, 48), (40, 44, 96))
GRASS = (72, 162, 64)
GRASS_D = (54, 128, 50)
DOOR_C = (128, 86, 54)
DOOR_D = (92, 60, 38)
JERSEY = (40, 200, 110)
JERSEY2 = (70, 120, 240)
SKIN = (240, 200, 170)


@lru_cache(maxsize=None)
def font(path, size):
    f = ImageFont.truetype(path, int(size))
    if "Orbitron" in path:
        try:
            f.set_variation_by_name("Black")
        except Exception:
            pass
    return f


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_c(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def beat(t):
    """0..1 phase within beat and an exponential pulse."""
    ph = ((t - PHASE) / PERIOD) % 1.0
    return ph, math.exp(-5 * ph)


def rms_at(t):
    i = int(t * FPS)
    return RMS[min(max(i, 0), len(RMS) - 1)]


def shake(t, amp, speed=37.0):
    return (amp * math.sin(t * speed * 1.3 + 1.0), amp * math.cos(t * speed + 0.4))


# ---------------- lyric timeline ----------------
# rows: list of rows; each row = list of (word, time)
def L(kind, *rows, hold=None):
    rws = []
    for r in rows:
        toks = []
        for item in r:
            toks.append(item)
        rws.append(toks)
    return {"kind": kind, "rows": rws, "hold": hold}


LINES = [
    L("spoken", [("Owen?", 2.80)], hold=1.4),
    L("spoken", [("OWEN!", 4.32)], hold=2.0),
    L("spoken", [("He's", 6.64), ("got", 6.96), ("the", 7.12), ("headset", 7.28), ("on", 8.00), ("again.", 8.32)], hold=2.6),
    # verse 1
    L("verse", [("Every", 9.60), ("single", 9.92), ("day", 10.40)], [("it's", 10.72), ("the", 10.96), ("same", 11.12), ("old", 11.36), ("thing", 11.68)]),
    L("verse", [("Big", 12.16), ("brother's", 12.48), ("in", 13.20), ("his", 13.36), ("room", 13.52)], [("with", 13.84), ("a", 14.00), ("tank", 14.16), ("and", 14.56), ("a", 14.72), ("plane", 14.80)]),
    L("verse", [("I", 15.44), ("knock", 15.60), ("on", 16.08), ("the", 16.32), ("door,", 16.40), ("I", 16.88), ("say", 16.96)], [("\"Come", 17.20), ("on,", 17.36), ("let's", 17.68), ("play!\"", 17.92)]),
    L("verse", [("He", 18.40), ("says", 18.56), ("\"One", 18.88), ("more", 19.12), ("match\"", 19.36)], [("—", 19.80), ("he", 19.92), ("said", 20.08), ("that", 20.24), ("yesterday!", 20.48)]),
    L("verse", [("I", 21.52), ("got", 21.68), ("my", 21.84), ("soccer", 22.24), ("ball,", 22.72)], [("I", 23.20), ("got", 23.36), ("on", 23.52), ("my", 23.84), ("cleats", 24.00)]),
    L("verse", [("I", 24.64), ("got", 24.80), ("a", 24.96), ("whole", 25.12), ("backyard", 25.44)], [("and", 26.24), ("nobody", 26.48), ("to", 26.96), ("beat", 27.20)], hold=3.4),
]


def chorus_lines(o, final=False):
    """o = time of 'Get' in 'Get off'. Chorus 1 'Get' is 29.56."""
    d = o - 29.56
    big = "chorus_final" if final else "chorus"
    ls = [
        L(big, [("OWEN!", 28.12 + d), ("(Owen!)", 28.76 + d)], [("Get", 29.56 + d), ("off", 29.80 + d), ("War", 30.12 + d), ("Thunder!", 30.52 + d)]),
        L(big, [("OWEN!", 31.24 + d), ("(Owen!)", 31.88 + d)], [("You've", 32.68 + d), ("got", 32.84 + d), ("a", 33.00 + d), ("little", 33.16 + d), ("brother!", 33.48 + d)]),
        L(big, [("Your", 34.16 + d), ("plane", 34.32 + d), ("went", 34.72 + d), ("down,", 35.12 + d)], [("your", 35.68 + d), ("tank", 35.84 + d), ("blew", 36.24 + d), ("up!", 36.64 + d)]),
        L(big, [("Come", 37.28 + d), ("outside", 37.60 + d), ("and", 38.00 + d), ("play", 38.16 + d), ("with", 38.32 + d), ("me", 38.56 + d)]),
    ]
    return ls


LINES += chorus_lines(29.56)
LINES += [
    L("chorus", [("Owen,", 39.04), ("get", 40.08), ("up!", 40.40)], hold=3.4),
    L("chorus", [("Owen,", 42.72), ("get", 43.28), ("up!", 43.60)], hold=2.2),
    # verse 2
    L("verse", [("He", 46.08), ("says", 46.24), ("\"Hold", 46.64), ("on,", 46.96), ("bro,", 47.20)], [("I'm", 47.60), ("unlocking", 47.84), ("a", 48.56), ("new", 48.72), ("tank\"", 48.88)]),
    L("verse", [("I", 49.28), ("say", 49.44), ("\"You", 49.84), ("said", 50.00), ("that", 50.24), ("Monday!\"", 50.48)], [("He", 51.20), ("says", 51.36), ("\"Yeah...", 51.68), ("and?\"", 52.00)]),
    L("verse", [("I", 52.72), ("know", 52.88), ("all", 53.04), ("his", 53.20), ("tanks,", 53.44)], [("I", 54.24), ("know", 54.40), ("all", 54.56), ("his", 54.72), ("planes", 54.96)]),
    L("verse", [("I", 55.84), ("know", 55.92), ("when", 56.08), ("he's", 56.32), ("losing", 56.56)], [("'cause", 57.04), ("he", 57.28), ("yells", 57.36), ("at", 57.76), ("the", 57.84), ("game", 58.00)]),
    L("verse", [("I'll", 58.48), ("let", 58.72), ("him", 58.88), ("be", 59.12), ("the", 59.28), ("captain,", 59.44)], [("I'll", 60.40), ("let", 60.64), ("him", 60.80), ("be", 60.96), ("the", 61.04), ("coach", 61.20)]),
    L("verse", [("I'll", 61.60), ("even", 61.84), ("let", 62.08), ("him", 62.24), ("make", 62.48), ("the", 62.64), ("rules", 62.72)]),
    L("spoken", [("...okay,", 63.44), ("SOME", 63.76), ("of", 64.00), ("the", 64.08), ("rules", 64.24)], hold=1.6),
]
LINES += chorus_lines(66.56)
LINES += [
    L("chorus", [("Owen,", 76.00), ("get", 76.96), ("up!", 77.20)], hold=1.5),
    # bridge
    L("bridge", [("One", 77.60), ("more", 77.92), ("match!", 78.08)], [("(that's", 78.88), ("what", 79.20), ("you", 79.44), ("said)", 79.68)]),
    L("bridge", [("One", 80.48), ("more", 80.80), ("match!", 81.12)], [("(it's", 81.84), ("almost", 82.08), ("bed)", 82.64)]),
    L("bridge", [("One", 83.60), ("more", 83.92), ("match!", 84.16)], [("(the", 84.88), ("sun", 85.04), ("went", 85.36), ("down)", 85.84)]),
    L("bridge", [("One", 86.72), ("more", 87.04), ("match!", 87.28)], [("MOM'S", 87.84), ("COMING", 88.32), ("AROUND!", 88.72)]),
    L("spoken", [("Owen.", 89.76), ("Owen.", 90.32), ("She's", 90.80), ("got", 91.04), ("the", 91.12), ("face.", 91.28)], hold=2.6),
]
LINES += chorus_lines(94.24, final=True)
LINES += [
    L("chorus_final", [("OWEN!", 103.68), ("(OWEN!)", 104.56)], [("GET", 106.24), ("UP!", 106.56)], hold=3.6),
    # outro
    L("spoken", [("He", 108.00), ("paused", 108.16), ("it!", 108.80)], hold=1.8),
    L("spoken", [("He", 109.84), ("actually", 110.00), ("paused", 110.56), ("it!", 111.12)], hold=2.3),
    L("spoken", [("Okay", 112.24), ("—", 112.80), ("I'm", 112.96), ("the", 113.28), ("captain.", 113.44)], [("You're", 114.48), ("the", 114.64), ("goalie.", 114.80)], hold=3.1),
    L("spoken", [("Don't", 115.44), ("argue.", 115.68)], hold=1.4),
    L("spoken", [("Hey", 116.32), ("Owen?", 116.56)], [("Can", 117.28), ("I", 117.52), ("play", 117.60), ("War", 117.84), ("Thunder", 118.16), ("after?", 118.72)], hold=3.4),
]

for i, ln in enumerate(LINES):
    ln["start"] = ln["rows"][0][0][1]
    nxt = LINES[i + 1]["rows"][0][0][1] if i + 1 < len(LINES) else DUR
    ln["end"] = min(nxt - 0.05, ln["start"] + ln["hold"]) if ln["hold"] else nxt - 0.05
    ln["end"] = max(ln["end"], ln["rows"][-1][-1][1] + 0.6)


def current_line(t):
    for ln in LINES:
        if ln["start"] - 0.35 <= t < ln["end"]:
            return ln
    return None


# ---------------- scenes ----------------
SCENES = [
    (0.0, 2.6, "title"),
    (2.6, 9.6, "door"),
    (9.6, 21.4, "hallway"),
    (21.4, 28.0, "backyard"),
    (28.0, 45.8, "chorus"),
    (45.8, 52.6, "chat"),
    (52.6, 58.4, "spotter"),
    (58.4, 65.0, "offers"),
    (65.0, 77.5, "chorus2"),
    (77.5, 92.6, "bridge"),
    (92.6, 107.8, "chorus3"),
    (107.8, 112.1, "paused"),
    (112.1, 119.4, "backyard2"),
    (119.4, DUR + 1, "end"),
]


def scene_at(t):
    for a, b, n in SCENES:
        if a <= t < b:
            return n, a, b
    return "end", 119.4, DUR


# ---------------- drawing helpers ----------------
def text(d, xy, s, fnt, fill, anchor="mm", stroke=0, stroke_fill=INK):
    d.text(xy, s, font=fnt, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def fit_font(path, s, max_w, size, min_size=40):
    while size > min_size and font(path, size).getlength(s) > max_w:
        size -= 4
    return font(path, size)


def stamp(img, s, fnt, center, fill, rot=0.0, scale=1.0, stroke=10, stroke_fill=INK, alpha=255):
    """Rotated/scaled text pasted onto img."""
    w = int(fnt.getlength(s) * scale) + stroke * 4 + 40
    h = int(fnt.size * 1.35 * scale) + stroke * 4 + 40
    if scale != 1.0:
        fnt = font(fnt.path, fnt.size * scale)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((w / 2, h / 2), s, font=fnt, fill=fill + (alpha,), anchor="mm", stroke_width=int(stroke * scale), stroke_fill=stroke_fill + (alpha,))
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    img.paste(layer, (int(center[0] - layer.width / 2), int(center[1] - layer.height / 2)), layer)


def draw_check(d, cx, cy, r, col):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK, outline=col, width=5)
    d.line((cx - r * 0.5, cy, cx - r * 0.1, cy + r * 0.42), fill=col, width=int(r * 0.22))
    d.line((cx - r * 0.1, cy + r * 0.42, cx + r * 0.55, cy - r * 0.4), fill=col, width=int(r * 0.22))


def draw_warn(d, cx, cy, r):
    d.polygon([(cx, cy - r), (cx + r * 1.05, cy + r * 0.75), (cx - r * 1.05, cy + r * 0.75)], fill=AMBER, outline=INK)
    d.polygon([(cx, cy - r * 0.7), (cx + r * 0.78, cy + r * 0.62), (cx - r * 0.78, cy + r * 0.62)], outline=INK, width=4)
    d.rectangle((cx - r * 0.1, cy - r * 0.35, cx + r * 0.1, cy + r * 0.2), fill=INK)
    d.ellipse((cx - r * 0.11, cy + r * 0.3, cx + r * 0.11, cy + r * 0.52), fill=INK)


def img_of(d):
    return d._image


def dark_panel(img, box, alpha=140, r=12):
    x0, y0, x1, y1 = [int(v) for v in box]
    if x1 <= x0 or y1 <= y0:
        return
    ov = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), radius=r, fill=(0, 0, 0, alpha))
    img.paste(ov, (x0, y0), ov)


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def hazard_band(d, y0, y1, c1=AMBER, c2=INK, step=60, offset=0):
    d.rectangle((0, y0, W, y1), fill=c2)
    h = y1 - y0
    x = -h - step * 2 + (offset % (step * 2))
    while x < W + h:
        d.polygon([(x, y1), (x + step, y1), (x + step + h, y0), (x + h, y0)], fill=c1)
        x += step * 2


def draw_tank(d, x, y, s, fill, outline=INK, wobble=0.0):
    """Tank silhouette, (x,y) = bottom center, s = scale (1 ~ 200px wide)."""
    def P(px, py):
        return (x + px * s, y + py * s)
    # tracks
    d.rounded_rectangle([P(-100, -34), P(100, 0)], radius=int(17 * s), fill=INK)
    for i in range(-3, 4):
        d.ellipse([P(i * 28 - 11, -28), P(i * 28 + 11, -6)], fill=fill, outline=outline, width=max(1, int(3 * s)))
    # hull
    d.polygon([P(-96, -34), P(96, -34), P(80, -66), P(-80, -66)], fill=fill, outline=outline)
    # turret
    d.rounded_rectangle([P(-46, -100), P(40, -62)], radius=int(12 * s), fill=fill, outline=outline, width=max(1, int(3 * s)))
    # barrel
    d.polygon([P(36, -92 + wobble), P(140, -88 + wobble), P(140, -78 + wobble), P(36, -80 + wobble)], fill=fill, outline=outline)
    d.rectangle([P(120, -94 + wobble), P(142, -76 + wobble)], fill=fill, outline=outline)
    d.ellipse([P(-14, -118), P(8, -98)], fill=fill, outline=outline)  # hatch


def draw_plane(d, x, y, s, fill, outline=INK, rot=0.0):
    """Plane silhouette centered at (x,y), nose pointing right (rot in degrees ccw)."""
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(px, py):
        return (x + (px * cr + py * sr) * s, y + (-px * sr + py * cr) * s)
    # wings
    d.polygon([P(-10, -6), P(30, -6), P(10, -70), P(-30, -70)], fill=fill, outline=outline)
    d.polygon([P(-10, 6), P(30, 6), P(10, 70), P(-30, 70)], fill=fill, outline=outline)
    # tail
    d.polygon([P(-80, -4), P(-60, -4), P(-70, -40), P(-92, -40)], fill=fill, outline=outline)
    d.polygon([P(-80, 4), P(-60, 4), P(-70, 40), P(-92, 40)], fill=fill, outline=outline)
    d.polygon([P(-88, -10), P(-60, -10), P(-70, -46), P(-96, -46)], fill=fill, outline=outline)
    # fuselage
    d.polygon([P(-96, -10), P(40, -14), P(90, -6), P(100, 0), P(90, 6), P(40, 14), P(-96, 10)], fill=fill, outline=outline)
    # canopy (rotated ellipse as polygon)
    d.polygon([P(28 + 18 * math.cos(a), -8 + 6 * math.sin(a)) for a in [k * math.pi / 8 for k in range(16)]], fill=INK)
    hx, hy = P(100, 0)
    d.ellipse((hx - 14 * s, hy - 14 * s, hx + 14 * s, hy + 14 * s), fill=INK)  # prop hub


def draw_ball(d, cx, cy, r, rot=0.0):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=INK, width=max(2, r // 10))
    for k in range(5):
        a = math.radians(rot + k * 72)
        px, py = cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55
        rr = r * 0.26
        d.regular_polygon((px, py, rr), 5, rotation=-rot - k * 72, fill=INK)
    d.regular_polygon((cx, cy, r * 0.22), 5, rotation=-rot, fill=INK)


def draw_kid(d, x, y, h, jersey, number, flip=False, bob=0.0, arm_up=False, headset=False, sit=False):
    """Kid figure: (x,y) bottom-center, h = total height."""
    s = h / 100.0
    f = -1 if flip else 1

    def P(px, py):
        return (x + px * s * f, y + py * s)

    def NB(pts):
        (x0, y0), (x1, y1) = pts
        return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

    def NR(pts, **kw):
        d.rectangle(NB(pts), **kw)

    def NRR(pts, **kw):
        d.rounded_rectangle(NB(pts), **kw)
    y -= bob
    hr = 15 * s
    if sit:
        # chair
        NRR([P(-26, -62), P(26, -40)], radius=int(6 * s), fill=(40, 40, 46), outline=INK, width=2)
        NR([P(-6, -40), P(6, 0)], fill=(40, 40, 46))
        NRR([P(18, -110), P(30, -46)], radius=int(5 * s), fill=(40, 40, 46), outline=INK, width=2)
        # legs forward
        NRR([P(-30, -58), P(10, -44)], radius=int(6 * s), fill=(40, 60, 120), outline=INK, width=2)
        NR([P(-34, -46), P(-22, -4)], fill=(40, 60, 120), outline=INK, width=2)
        NRR([P(-40, -6), P(-16, 2)], radius=int(4 * s), fill=INK)
        body_top, body_bot = -104, -56
    else:
        # legs
        NR([P(-16, -34), P(-4, -2)], fill=(50, 50, 60), outline=INK, width=2)
        NR([P(4, -34), P(16, -2)], fill=(50, 50, 60), outline=INK, width=2)
        NRR([P(-22, -6), P(-2, 2)], radius=int(4 * s), fill=INK)
        NRR([P(2, -6), P(22, 2)], radius=int(4 * s), fill=INK)
        body_top, body_bot = -78, -32
    # body
    NRR([P(-22, body_top), P(22, body_bot)], radius=int(8 * s), fill=jersey, outline=INK, width=max(2, int(2 * s)))
    if number:
        text(d, P(0, (body_top + body_bot) / 2), str(number), font(F_HUD, int(22 * s)), WHITE, stroke=max(1, int(1.5 * s)))
    # arms
    if arm_up:
        NRR([P(22, body_top + 2), P(32, body_top - 36)], radius=int(5 * s), fill=SKIN, outline=INK, width=2)
    else:
        NRR([P(22, body_top + 4), P(32, body_bot - 6)], radius=int(5 * s), fill=SKIN, outline=INK, width=2)
    NRR([P(-32, body_top + 4), P(-22, body_bot - 6)], radius=int(5 * s), fill=SKIN, outline=INK, width=2)
    # head
    hx, hy = P(0, body_top - 17)
    d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=SKIN, outline=INK, width=max(2, int(2 * s)))
    # hair
    d.chord((hx - hr, hy - hr, hx + hr, hy + hr), 180, 360, fill=(70, 45, 30))
    # eyes
    ex = 5 * s * f
    d.ellipse((hx + ex - 2 * s, hy - 2 * s, hx + ex + 2 * s, hy + 2 * s), fill=INK)
    d.ellipse((hx - ex - 2 * s, hy - 2 * s, hx - ex + 2 * s, hy + 2 * s), fill=INK)
    d.arc((hx - 6 * s, hy + 1 * s, hx + 6 * s, hy + 9 * s), 10, 170, fill=INK, width=max(1, int(2 * s)))
    if headset:
        d.arc((hx - hr - 4 * s, hy - hr - 6 * s, hx + hr + 4 * s, hy + hr), 190, 350, fill=(30, 30, 34), width=max(3, int(5 * s)))
        d.rounded_rectangle((hx - hr - 8 * s, hy - 8 * s, hx - hr + 2 * s, hy + 8 * s), radius=int(3 * s), fill=(30, 30, 34), outline=HUD, width=2)
        d.rounded_rectangle((hx + hr - 2 * s, hy - 8 * s, hx + hr + 8 * s, hy + 8 * s), radius=int(3 * s), fill=(30, 30, 34), outline=HUD, width=2)


def draw_boom(d, cx, cy, r, phase, txt="BOOM!"):
    """Cartoon explosion burst. phase 0..1"""
    if phase <= 0 or phase >= 1:
        return
    rr = r * (0.4 + 0.6 * ease_out(phase * 1.6))
    pts = []
    n = 16
    for k in range(n):
        a = k * 2 * math.pi / n + phase * 0.8
        rad = rr if k % 2 == 0 else rr * 0.62
        pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    d.polygon(pts, fill=(255, 120, 40), outline=INK)
    pts2 = [(cx + (px - cx) * 0.62, cy + (py - cy) * 0.62) for px, py in pts]
    d.polygon(pts2, fill=AMBER, outline=INK)
    if phase < 0.85:
        text(d, (cx, cy), txt, font(F_SHOUT, int(rr * 0.6)), WHITE, stroke=int(rr * 0.05) + 2)


def draw_door(d, x0, y0, x1, y1, alpha_layer=None, sign=True, shake_x=0):
    x0 += shake_x
    x1 += shake_x
    d.rectangle((x0 - 18, y0 - 18, x1 + 18, y1), fill=(60, 44, 34))
    d.rectangle((x0, y0, x1, y1), fill=DOOR_C, outline=INK, width=4)
    m = 26
    d.rectangle((x0 + m, y0 + m, x1 - m, y0 + (y1 - y0) * 0.42), fill=DOOR_D, outline=INK, width=3)
    d.rectangle((x0 + m, y0 + (y1 - y0) * 0.5, x1 - m, y1 - m), fill=DOOR_D, outline=INK, width=3)
    kx, ky = x1 - 48, (y0 + y1) / 2 + 20
    d.ellipse((kx - 14, ky - 14, kx + 14, ky + 14), fill=AMBER, outline=INK, width=3)
    if sign:
        sw, sh = (x1 - x0) + 60, 150
        sx, sy = (x0 + x1) / 2, y0 + 64 + sh / 2
        rrect(d, (sx - sw / 2, sy - sh / 2, sx + sw / 2, sy + sh / 2), 10, fill=WHITE, outline=INK, width=4)
        text(d, (sx, sy - 44), "OWEN'S ROOM", fit_font(F_STENCIL, "OWEN'S ROOM", sw - 24, 34, 16), INK)
        text(d, (sx, sy), "KEEP OUT", fit_font(F_STENCIL, "KEEP OUT", sw - 24, 44, 16), RED)
        text(d, (sx, sy + 44), "(that means you, Alex)", fit_font(F_HUD, "(that means you, Alex)", sw - 24, 24, 14), INK)


def sky_image(kind):
    return _sky(kind)


@lru_cache(maxsize=None)
def _sky(kind):
    c_top, c_bot = {"day": SKY_DAY, "sunset": SKY_SUNSET, "night": SKY_NIGHT}[kind]
    img = Image.new("RGB", (1, 760))
    for y in range(760):
        img.putpixel((0, y), lerp_c(c_top, c_bot, y / 759))
    return img.resize((W, 760))


@lru_cache(maxsize=1)
def scanlines():
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(0, H, 4):
        d.line((0, y, W, y), fill=(0, 0, 0, 26))
    # vignette
    vig = Image.new("L", (W // 8, H // 8), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse((-W // 32, -H // 32, W // 8 + W // 32, H // 8 + H // 32), fill=255)
    vig = vig.resize((W, H)).filter(ImageFilter.GaussianBlur(60))
    inv = vig.point(lambda v: int((255 - v) * 0.55))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    black.putalpha(inv)
    ov = Image.alpha_composite(ov, black)
    return ov


def draw_backyard(img, d, t, sky="day", sun_y=None, kids=2, ball_x=None, labels=False, lonely=True, night_t=0.0):
    img.paste(sky_image(sky), (0, 0))
    if night_t > 0:
        # stars
        rnd = random.Random(7)
        for _ in range(90):
            sx, sy = rnd.randint(0, W), rnd.randint(0, 600)
            a = int(255 * night_t * (0.5 + 0.5 * math.sin(t * 3 + sx)))
            d.ellipse((sx - 2, sy - 2, sx + 2, sy + 2), fill=(255, 255, 230, a) if img.mode == "RGBA" else lerp_c(SKY_NIGHT[0], (255, 255, 230), a / 255))
    # sun / moon
    if sun_y is not None:
        sx = 440
        col = AMBER if sky != "night" else (235, 235, 220)
        d.ellipse((sx - 70, sun_y - 70, sx + 70, sun_y + 70), fill=col, outline=INK, width=4)
        if sky == "day":
            for k in range(12):
                a = k * math.pi / 6 + t * 0.4
                d.line((sx + math.cos(a) * 85, sun_y + math.sin(a) * 85, sx + math.cos(a) * 110, sun_y + math.sin(a) * 110), fill=col, width=8)
    # clouds
    for cx, cy, cs in [(300, 180, 1.0), (900, 120, 0.8), (1300, 230, 0.7)]:
        cx = (cx + t * 12) % (W + 400) - 200
        for ox, oy, r in [(0, 0, 60), (60, -20, 75), (130, 0, 60), (60, 20, 60)]:
            d.ellipse((cx + ox - r * cs, cy + oy - r * cs, cx + ox + r * cs, cy + oy + r * cs), fill=(255, 255, 255) if sky == "day" else lerp_c((255, 255, 255), (120, 110, 150), 0.6 if sky == "sunset" else 0.9))
    # fence
    d.rectangle((0, 560, W, 580), fill=(150, 110, 70), outline=INK, width=3)
    d.rectangle((0, 640, W, 660), fill=(150, 110, 70), outline=INK, width=3)
    for x in range(40, W, 90):
        d.polygon([(x, 540), (x + 50, 540), (x + 50, 700), (x, 700)], fill=(170, 125, 80), outline=INK)
        d.polygon([(x, 540), (x + 25, 515), (x + 50, 540)], fill=(170, 125, 80), outline=INK)
    # grass
    d.rectangle((0, 700, W, H), fill=GRASS)
    for k in range(0, W, 160):
        d.rectangle((k, 760, k + 80, H), fill=GRASS_D)
    # goal
    gx0, gy0, gx1, gy1 = 1180, 520, 1700, 800
    for gx in range(gx0 + 20, gx1, 40):
        d.line((gx, gy0 + 10, gx, gy1), fill=(230, 230, 230), width=2)
    for gy in range(gy0 + 20, gy1, 40):
        d.line((gx0, gy, gx1, gy), fill=(230, 230, 230), width=2)
    d.rectangle((gx0 - 10, gy0, gx0 + 10, gy1), fill=WHITE, outline=INK, width=2)
    d.rectangle((gx1 - 10, gy0, gx1 + 10, gy1), fill=WHITE, outline=INK, width=2)
    d.rectangle((gx0 - 10, gy0 - 10, gx1 + 10, gy0 + 10), fill=WHITE, outline=INK, width=2)
    # kids
    ph, pulse = beat(t)
    bob = 6 * pulse
    draw_kid(d, 560, 820, 300, JERSEY, 6, bob=bob, arm_up=True)
    if ball_x is None:
        ball_x = 700 + 60 * math.sin(t * 2.0)
    draw_ball(d, ball_x, 790, 36, rot=t * 240)
    if kids == 2:
        draw_kid(d, 1440, 830, 380, JERSEY2, 12, flip=True, bob=bob * 0.5, arm_up=True)
    if labels:
        for (lx, ly, s, c) in [(560, 400, "CAPTAIN: ALEX", HUD), (1440, 320, "GOALIE: OWEN", AMBER)]:
            fnt = font(F_HUD, 44)
            w = fnt.getlength(s) + 50
            rrect(d, (lx - w / 2, ly - 34, lx + w / 2, ly + 34), 10, fill=INK, outline=c, width=4)
            text(d, (lx, ly), s, fnt, c)
            d.polygon([(lx - 16, ly + 34), (lx + 16, ly + 34), (lx, ly + 56)], fill=c)


def hud_panel(d, box, title=None, color=HUD, fill=(8, 12, 9)):
    x0, y0, x1, y1 = box
    rrect(d, box, 8, fill=fill, outline=color, width=3)
    if title:
        tf = font(F_HUD, 26)
        tw = tf.getlength(title) + 28
        d.rectangle((x0 + 16, y0 - 16, x0 + 16 + tw, y0 + 16), fill=fill)
        text(d, (x0 + 16 + tw / 2, y0), title, tf, color)


def draw_hud(img, d, t, mode="normal", match_no=1, match_t0=0.0, mom=0.0, alert=0.0, show_cards=True, crosshair=True):
    col = HUD if mode != "alert" else RED
    # corner brackets
    L_ = 70
    for (cx, cy, sx, sy) in [(96, 54, 1, 1), (W - 96, 54, -1, 1), (96, H - 54, 1, -1), (W - 96, H - 54, -1, -1)]:
        d.line((cx, cy, cx + sx * L_, cy), fill=col, width=5)
        d.line((cx, cy, cx, cy + sy * L_), fill=col, width=5)
    # minimap radar
    mx, my, mr = 96 + 118, 54 + 24 + 118, 118
    d.ellipse((mx - mr, my - mr, mx + mr, my + mr), fill=(6, 12, 8), outline=col, width=4)
    for k in (0.33, 0.66):
        d.ellipse((mx - mr * k, my - mr * k, mx + mr * k, my + mr * k), outline=HUD_DIM if mode != "alert" else (120, 40, 40), width=2)
    d.line((mx - mr, my, mx + mr, my), fill=HUD_DIM, width=2)
    d.line((mx, my - mr, mx, my + mr), fill=HUD_DIM, width=2)
    a = (t * 2.4) % (2 * math.pi)
    for k in range(10):
        aa = a - k * 0.08
        d.line((mx, my, mx + math.cos(aa) * mr, my + math.sin(aa) * mr), fill=lerp_c((6, 12, 8), col, 1 - k / 10), width=4)
    # blips: alex (green) and owen (red)
    d.ellipse((mx - 60 - 7, my + 30 - 7, mx - 60 + 7, my + 30 + 7), fill=HUD)
    d.ellipse((mx + 55 - 8, my - 50 - 8, mx + 55 + 8, my - 50 + 8), fill=RED, outline=WHITE, width=2)
    if mom > 0:
        # big blip approaching from bottom-left
        bx = mx - 100 + 90 * mom
        by = my + 95 - 85 * mom
        pr = 12 + 6 * math.sin(t * 20)
        d.ellipse((bx - pr, by - pr, bx + pr, by + pr), fill=RED, outline=WHITE, width=3)
        text(d, (bx, by - 30), "MOM", font(F_HUD, 24), RED, stroke=3)
    text(d, (mx, my + mr + 26), "RADAR", font(F_HUD, 24), col, stroke=3)
    # match timer (top right)
    tx1 = W - 96
    hud_panel(d, (tx1 - 400, 54 + 24, tx1, 54 + 24 + 150), title=f"MATCH #{match_no}", color=col)
    el = max(0.0, t - match_t0) * 7.3  # 'game time' runs fast
    mm, ss = int(el // 60), int(el % 60)
    text(d, (tx1 - 200, 54 + 24 + 86), f"{mm:02d}:{ss:02d}", font(F_DIGI, 70), col)
    # crosshair center (subtle)
    if mode != "alert" and crosshair:
        cx, cy = W // 2, 470
        for (ax, ay, bx, by) in [(-60, 0, -20, 0), (20, 0, 60, 0), (0, -60, 0, -20), (0, 20, 0, 60)]:
            d.line((cx + ax, cy + ay, cx + bx, cy + by), fill=col, width=4)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), outline=col, width=3)
    # unit cards under the radar
    if show_cards:
        cx0, cy0 = 96, 54 + 24 + 236 + 70
        hud_panel(d, (cx0, cy0, cx0 + 440, cy0 + 112), title="UNIT", color=col)
        text(d, (cx0 + 20, cy0 + 36), "ALEX  •  AGE 6", font(F_HUD, 30), WHITE, anchor="lm")
        text(d, (cx0 + 20, cy0 + 78), "ROLE: CAPTAIN (self-appointed)", font(F_MONO, 28), col, anchor="lm")
        hud_panel(d, (cx0, cy0 + 136, cx0 + 440, cy0 + 248), title="TARGET", color=RED)
        text(d, (cx0 + 20, cy0 + 136 + 36), "OWEN  •  AGE 12", font(F_HUD, 30), WHITE, anchor="lm")
        status = "STATUS: AFK (headset on)" if mode != "paused" else "STATUS: PAUSED (!!)"
        text(d, (cx0 + 20, cy0 + 136 + 78), status, font(F_MONO, 28), RED if mode != "paused" else HUD, anchor="lm")
    if alert > 0:
        # red flashing border
        a = int(120 * alert * (0.6 + 0.4 * math.sin(t * 18)))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for k in range(1, 7):
            od.rectangle((k * 6, k * 6, W - k * 6, H - k * 6), outline=(255, 40, 30, max(0, a - k * 15)), width=6)
        img.paste(ov, (0, 0), ov)


# --------------- kill feed ----------------
FEED = [
    (9.9, "[ALEX] entered HALLWAY", HUD),
    (12.4, "[OWEN] is in a match", RED),
    (14.3, "[OWEN] spawned: TANK, PLANE", RED),
    (15.7, "[ALEX] knocked on DOOR", HUD),
    (19.0, "[OWEN] said \"one more match\"", RED),
    (20.6, "  ^ streak: 47 days", AMBER),
    (22.3, "[ALEX] equipped SOCCER BALL", HUD),
    (24.1, "[ALEX] equipped CLEATS", HUD),
    (26.5, "[SYSTEM] matchmaking... 0 found", AMBER),
]


def draw_feed(d, t, x1=W - 96, y0=54 + 24 + 150 + 40):
    fnt = font(F_MONO, 34)
    rows = [f for f in FEED if f[0] <= t < f[0] + 7.0]
    rows = rows[-5:]
    if rows:
        maxw = max(fnt.getlength(s) for _, s, _ in rows)
        dark_panel(img_of(d), (x1 - maxw - 40, y0 - 26, x1 + 14, y0 + 44 * len(rows) - 10), 150)
    y = y0
    for (ft, s, c) in rows:
        age = t - ft
        fade = 1.0 if age < 5.5 else clamp(1 - (age - 5.5) / 1.5)
        pop = ease_out(age / 0.25)
        cc = lerp_c((8, 12, 9), c, fade)
        text(d, (x1 - 12 + (1 - pop) * 60, y), s, fnt, cc, anchor="rm")
        y += 44


# ---------------- lyric band ----------------
def draw_lyrics(img, d, t):
    ln = current_line(t)
    if ln is None:
        return
    kind = ln["kind"]
    big = kind in ("chorus", "chorus_final")
    path = F_SHOUT
    size = 104 if big else 92
    if kind == "spoken":
        size = 84
    rows = ln["rows"]
    n = len(rows)
    base_y = 940 if n == 1 else 860
    gap = 96
    # band background
    y_top = base_y - gap / 2 - 24
    y_bot = base_y + gap * (n - 1) + gap / 2 + 20
    ov = Image.new("RGBA", (W, int(y_bot - y_top)), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle((300, 0, W - 300, ov.height - 1), radius=26, fill=(0, 0, 0, 120))
    img.paste(ov, (0, int(y_top)), ov)
    for ri, row in enumerate(rows):
        s_full = " ".join(w for w, _ in row)
        fnt = fit_font(path, s_full, 1680, size)
        total = fnt.getlength(s_full)
        x = W / 2 - total / 2
        y = base_y + ri * gap
        space = fnt.getlength(" ")
        for (w, wt) in row:
            ww = fnt.getlength(w)
            cx = x + ww / 2
            sung = t >= wt
            age = t - wt
            if not sung:
                col = (140, 140, 135)
                if kind == "spoken":
                    col = (120, 120, 118)
                text(d, (cx, y), w, fnt, col, stroke=6)
            else:
                if age < 0.18:
                    sc = 1 + 0.3 * (1 - age / 0.18)
                    col = AMBER
                    stamp(img, w, fnt, (cx, y), col, scale=sc, stroke=7)
                else:
                    hot = w.strip("(),.!?\"").upper() in ("OWEN", "MATCH!", "UP!") or w.isupper() and len(w) > 2
                    col = AMBER if (hot and big) else WHITE
                    if kind == "spoken":
                        col = (235, 235, 225)
                    text(d, (cx, y), w, fnt, col, stroke=7)
            x += ww + space


# ---------------- scene renderers ----------------
def scene_title(img, d, t, thumb=False):
    d.rectangle((0, 0, W, H), fill=BG)
    # grid
    for x in range(0, W, 80):
        d.line((x, 0, x, H), fill=(22, 30, 24), width=1)
    for y in range(0, H, 80):
        d.line((0, y, W, y), fill=(22, 30, 24), width=1)
    hazard_band(d, 300, 340, offset=int(t * 120))
    hazard_band(d, 740, 780, offset=-int(t * 120))
    # tank left, ball right rolling in
    draw_tank(d, 260 if thumb else 300, 960, 1.4, (90, 110, 80))
    bx = 1480 if thumb else 1520 - 160 * ease_out(t / 1.2)
    draw_ball(d, bx, 905, 56, rot=t * 300)
    draw_kid(d, 1640, 960, 200, JERSEY, 6, flip=True, arm_up=True)
    # title
    fnt = font(F_STENCIL, 150)
    stamp(img, "GET OFF", fnt, (W / 2, 450), WHITE, stroke=12)
    fnt2 = font(F_STENCIL, 190)
    stamp(img, "WAR THUNDER", fnt2, (W / 2, 610), AMBER, stroke=14)
    text(d, (W / 2, 220), "ADITAZZZ  feat.  ALEX (age 6)", font(F_HUD, 56), HUD, stroke=4)
    if thumb:
        rrect(d, (W / 2 - 470, 830, W / 2 + 470, 960), 20, fill=RED, outline=WHITE, width=6)
        text(d, (W / 2, 895), "CLAUDE CODED THIS VIDEO", font(F_STENCIL, 64), WHITE)
    else:
        text(d, (W / 2, 880), "a music video coded by Claude", font(F_HUD, 44), (200, 200, 190))


def hallway_bg(d):
    d.rectangle((0, 0, W, 660), fill=WALL)
    d.rectangle((0, 660, W, 700), fill=(70, 74, 84))
    d.rectangle((0, 700, W, H), fill=FLOOR)
    for x in range(0, W, 120):
        d.line((x, 700, x - 200, H), fill=(36, 40, 46), width=2)
    # picture frame on wall


def scene_door(img, d, t):
    hallway_bg(d)
    knock = 0.0
    for kt in (2.80, 2.95, 3.10, 4.32, 4.45, 4.58, 4.71):
        if 0 <= t - kt < 0.12:
            knock = 10 * math.sin((t - kt) / 0.12 * math.pi)
    reveal = ease_in_out((t - 6.6) / 0.6) if t > 6.6 else 0.0
    x0, y0, x1, y1 = 1000, 250, 1280, 700
    if reveal > 0:
        # room behind the door
        d.rectangle((x0, y0, x1, y1), fill=(18, 14, 28))
        glow = int(60 + 40 * math.sin(t * 9))
        d.rectangle((x0, y0, x1, y1), fill=(18 + glow // 6, 14 + glow // 5, 28 + glow // 3))
        draw_kid(d, (x0 + x1) / 2 - 20, y1 - 10, 230, JERSEY2, 12, sit=True, headset=True)
        d.rectangle((x0, y1 - 150, x1, y1 - 120), fill=(70, 50, 36), outline=INK, width=3)
        rrect(d, ((x0 + x1) / 2 - 110, y1 - 260, (x0 + x1) / 2 + 110, y1 - 170), 8, fill=(24, 26, 30), outline=(glow + 60, glow + 120, 255), width=5)
        d.rectangle(((x0 + x1) / 2 - 20, y1 - 170, (x0 + x1) / 2 + 20, y1 - 150), fill=(24, 26, 30))
        d.ellipse(((x0 + x1) / 2 - 6, y1 - 200, (x0 + x1) / 2 + 6, y1 - 188), fill=HUD)
    if reveal < 1:
        door_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(door_layer)
        draw_door(dd, x0, y0, x1, y1, shake_x=knock)
        if reveal > 0:
            alpha = door_layer.split()[3].point(lambda v: int(v * (1 - reveal)))
            door_layer.putalpha(alpha)
        img.paste(door_layer, (0, 0), door_layer)
    # alex
    ph, pulse = beat(t)
    draw_kid(d, 720, 770, 300, JERSEY, 6, bob=4 * pulse, arm_up=(knock != 0 or (2.7 < t < 5.0)))
    draw_ball(d, 850, 740, 36, rot=t * 60)
    if 2.8 <= t < 4.2:
        bubble(d, (760, 270), "Owen?", 70)
    elif 4.32 <= t < 6.4:
        sc = 1 + 0.25 * (1 - ease_out((t - 4.32) / 0.2))
        bubble(d, (760, 260), "OWEN!!", int(96 * sc), col=RED)
    if reveal > 0:
        tag_y = 150
        fnt = font(F_HUD, 36)
        s1, s2 = "TARGET: BIG BROTHER", "RESPONSE: NONE"
        rrect(d, (x0 - 60, tag_y - 30, x1 + 60, tag_y + 100), 10, fill=INK, outline=RED, width=4)
        text(d, ((x0 + x1) / 2, tag_y + 4), s1, fnt, WHITE)
        text(d, ((x0 + x1) / 2, tag_y + 62), s2, fnt, RED)


def bubble(d, pos, s, size, col=INK):
    fnt = font(F_SHOUT, size)
    w = fnt.getlength(s) + 60
    h = size * 1.3
    x, y = pos
    rrect(d, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), 24, fill=WHITE, outline=INK, width=5)
    d.polygon([(x - 30, y + h / 2 - 4), (x + 10, y + h / 2 - 4), (x - 20, y + h / 2 + 50)], fill=WHITE, outline=INK)
    d.line((x - 30, y + h / 2 - 4, x + 10, y + h / 2 - 4), fill=WHITE, width=6)
    text(d, (x, y), s, fnt, col)


def scene_hallway(img, d, t):
    hallway_bg(d)
    knock = 0.0
    for kt in (15.60, 15.78, 15.96):
        if 0 <= t - kt < 0.14:
            knock = 12 * math.sin((t - kt) / 0.14 * math.pi)
    x0, y0, x1, y1 = 1000, 250, 1280, 700
    draw_door(d, x0, y0, x1, y1, shake_x=knock)
    ph, pulse = beat(t)
    walk = 0
    draw_kid(d, 740, 770, 300, JERSEY, 6, bob=6 * pulse, arm_up=(15.4 < t < 16.6))
    draw_ball(d, 870 + 20 * math.sin(t * 3), 740, 36, rot=t * 90)
    # floating tank & plane over the door when mentioned
    if 14.16 <= t < 21.4:
        a = ease_out((t - 14.16) / 0.3)
        draw_tank(d, 1040, 200 - 30 * (1 - a), 0.5, (120, 130, 110))
    if 14.80 <= t < 21.4:
        a = ease_out((t - 14.80) / 0.3)
        draw_plane(d, 1290, 150 + 10 * math.sin(t * 2) - 30 * (1 - a), 0.5, (150, 160, 170), rot=10)
    # door speech "ONE MORE MATCH" from behind the door
    if 18.88 <= t < 21.3:
        sc = 1 + 0.2 * (1 - ease_out((t - 18.88) / 0.25))
        bubble(d, (800, 280), "one more match", int(50 * sc), col=RED)
    if 20.4 <= t < 21.4:
        stamp(img, "AGAIN?!", font(F_SHOUT, 110), (1140, 400), AMBER, rot=-8, stroke=9)
    draw_feed(d, t)


def scene_backyard(img, d, t):
    draw_backyard(img, d, t, sky="day", sun_y=160, kids=1)
    # lonely marker
    if t > 25.3:
        a = ease_out((t - 25.3) / 0.3)
        fnt = font(F_HUD, 48)
        s = "PLAYERS ONLINE: 1"
        w = fnt.getlength(s) + 60
        cx, cy = W / 2 - 100, 280 - 40 * (1 - a)
        rrect(d, (cx - w / 2, cy - 44, cx + w / 2, cy + 44), 14, fill=INK, outline=AMBER, width=5)
        text(d, (cx, cy), s, fnt, AMBER)
    if t > 26.4:
        a = ease_out((t - 26.4) / 0.3)
        fnt = font(F_HUD, 40)
        s = "OPPONENTS FOUND: 0"
        w = fnt.getlength(s) + 60
        cx, cy = W / 2 - 100, 380 - 30 * (1 - a)
        rrect(d, (cx - w / 2, cy - 38, cx + w / 2, cy + 38), 14, fill=INK, outline=RED, width=5)
        text(d, (cx, cy), s, fnt, RED)
    draw_feed(d, t)


def chorus_timeline(o):
    """Return dict of key event times for a chorus whose 'Get' is at o."""
    d = o - 29.56
    return {
        "owen1": 28.12 + d, "echo1": 28.76 + d, "getoff": 29.56 + d, "wt": 30.12 + d,
        "owen2": 31.24 + d, "echo2": 31.88 + d, "brother": 32.68 + d,
        "plane": 34.16 + d, "plane_down": 35.12 + d, "tank": 35.68 + d, "boom": 36.24 + d,
        "outside": 37.28 + d, "end_outside": 39.0 + d,
    }


def scene_chorus(img, d, t, o, variant=1, start=28.0, end=45.8):
    k = chorus_timeline(o)
    ph, pulse = beat(t)
    e = rms_at(t)
    # background: dark with pulsing hazard bands
    d.rectangle((0, 0, W, H), fill=(20, 12, 10) if variant < 3 else (24, 10, 20))
    for x in range(0, W, 80):
        d.line((x, 0, x, H), fill=(34, 24, 20), width=1)
    off = int(t * 160)
    # "come outside" washes the sky in
    if k["outside"] <= t < k["end_outside"] + 1.6:
        a = ease_in_out((t - k["outside"]) / 0.4)
        sky = sky_image("day")
        if a < 1:
            crop = sky.crop((0, 0, W, int(760 * a) + 1))
            img.paste(crop, (0, 0))
        else:
            img.paste(sky, (0, 0))
        d.rectangle((0, 700, W, H), fill=GRASS)
        sun_y = 170
        d.ellipse((440 - 80, sun_y - 80, 440 + 80, sun_y + 80), fill=AMBER, outline=INK, width=4)
        draw_kid(d, 560, 820, 300, JERSEY, 6, bob=8 * pulse, arm_up=True)
        draw_ball(d, 700 + 50 * math.sin(t * 4), 790, 36, rot=t * 300)
    else:
        hazard_band(d, 150, 200, c1=AMBER if variant != 3 else RED, offset=off)
        hazard_band(d, 760, 810, c1=AMBER if variant != 3 else RED, offset=-off)
    # OWEN stamps
    for key, echo, side, until in (("owen1", "echo1", -1, k["getoff"]), ("owen2", "echo2", 1, k["brother"])):
        t0 = k[key]
        if t0 <= t < until:
            a = ease_out((t - t0) / 0.14)
            sc = 1.45 - 0.45 * a
            sx, sy = shake(t, 10 * (1 - a) + 3 * e)
            stamp(img, "OWEN!", font(F_STENCIL, 230), (W / 2 - 120 * side + sx, 420 + sy), WHITE if variant != 3 else AMBER, rot=-5 * side, scale=sc, stroke=14)
        t1 = k[echo]
        if t1 <= t < until:
            a = ease_out((t - t1) / 0.14)
            sc = 1.3 - 0.3 * a
            stamp(img, "(Owen!)", font(F_SHOUT, 120), (W / 2 + 420 * side, 560 + 20 * side), AMBER if variant != 3 else WHITE, rot=6 * side, scale=sc, stroke=9)
    # GET OFF WAR THUNDER banner
    if k["getoff"] <= t < k["owen2"] - 0.1:
        a = ease_out((t - k["getoff"]) / 0.2)
        y = 470
        hazard_band(d, y - 120, y + 120, c1=RED, c2=INK, step=70, offset=off)
        b = ease_out((t - k["wt"]) / 0.2) if t >= k["wt"] else 0
        s = "GET OFF" if b == 0 else "GET OFF WAR THUNDER"
        fnt = font(F_STENCIL, 150) if b == 0 else fit_font(F_STENCIL, s, 1560, 128)
        stamp(img, s, fnt, (W / 2, y), WHITE, scale=1 + 0.35 * (1 - a) if b == 0 else 1 + 0.25 * (1 - b), stroke=14)
    if k["brother"] <= t < k["plane"] - 0.1:
        a = ease_out((t - k["brother"]) / 0.25)
        draw_kid(d, W / 2 + 60, 760, 330, JERSEY, 6, bob=10 * pulse, arm_up=True)
        draw_ball(d, W / 2 + 200, 730, 40, rot=t * 300)
        fnt = font(F_HUD, 60)
        s = "LITTLE BROTHER DETECTED"
        w = fnt.getlength(s) + 60
        rrect(d, (W / 2 - w / 2, 300 - 40 * (1 - a) - 50, W / 2 + w / 2, 300 - 40 * (1 - a) + 50), 16, fill=INK, outline=HUD, width=5)
        text(d, (W / 2, 300 - 40 * (1 - a)), s, fnt, HUD)
        d.polygon([(W / 2 - 24, 350 - 40 * (1 - a)), (W / 2 + 24, 350 - 40 * (1 - a)), (W / 2, 390 - 40 * (1 - a))], fill=HUD)
    # plane down
    if k["plane"] <= t < k["tank"]:
        p = clamp((t - k["plane"]) / (k["tank"] - k["plane"]))
        px = 300 + 1100 * p
        py = 250 + 430 * p * p
        # smoke trail
        for i in range(1, 14):
            q = p - i * 0.045
            if q < 0:
                break
            qx, qy = 300 + 1100 * q, 250 + 430 * q * q
            r = 14 + i * 3
            g = 70 + i * 8
            d.ellipse((qx - r, qy - r, qx + r, qy + r), fill=(g, g, g))
        draw_plane(d, px, py, 1.25, (160, 170, 180), rot=-35 - 40 * p)
        if p > 0.55:
            stamp(img, "MAYDAY!", font(F_SHOUT, 100), (W / 2 - 200, 560), AMBER, rot=-6, stroke=8)
        if p > 0.92:
            draw_boom(d, px, py, 160, (p - 0.92) / 0.08 * 0.6 + 0.2, txt="CRASH")
    # tank blew up
    if k["tank"] <= t < k["outside"]:
        p = clamp((t - k["tank"]) / (k["outside"] - k["tank"]))
        bt = k["boom"]
        if t < bt:
            wob = 6 * math.sin(t * 30)
            draw_tank(d, W / 2, 700, 1.3, (110, 125, 95), wobble=wob)
        else:
            bp = clamp((t - bt) / 0.9)
            if bp < 0.4:
                # pieces flying
                for i in range(7):
                    a = i * 0.9
                    r = 30 + 400 * bp
                    px, py = W / 2 + math.cos(a) * r, 650 + math.sin(a) * r * 0.6 - 300 * bp
                    d.rectangle((px - 18, py - 18, px + 18, py + 18), fill=(110, 125, 95), outline=INK)
            draw_boom(d, W / 2, 620, 330, bp if bp < 1 else 0, txt="BOOM!")
            if bp >= 0.6:
                text(d, (W / 2, 700), "TANK: DESTROYED", font(F_STENCIL, 70), RED, stroke=8)
    # Owen get up / AFK stamps
    if variant == 1:
        for gt, gend in ((39.04, 41.4), (42.72, 44.2)):
            if gt <= t < gt + 1.0:
                stamp(img, "AFK", font(F_STENCIL, 200), (W / 2, 320), RED, rot=-6, scale=1.4 - 0.4 * ease_out((t - gt) / 0.2), stroke=14)
            if gt + 1.04 <= t < gend:
                a = ease_out((t - gt - 1.04) / 0.15)
                stamp(img, "GET UP!", font(F_STENCIL, 210), (W / 2, 330), WHITE, rot=4, scale=1.5 - 0.5 * a, stroke=14)
        if 44.2 <= t < 45.8:
            text(d, (W / 2, 450), "RESPONSE: NONE", font(F_HUD, 80), RED, stroke=8)
            text(d, (W / 2, 560), "(he can't hear me, he's got the headset)", font(F_HUD, 44), (220, 220, 210), stroke=4)
    if variant == 2:
        gt = 76.0
        if gt <= t < gt + 0.96:
            stamp(img, "AFK", font(F_STENCIL, 200), (W / 2, 320), RED, rot=-6, scale=1.4 - 0.4 * ease_out((t - gt) / 0.2), stroke=14)
        if gt + 0.96 <= t < 77.5:
            a = ease_out((t - gt - 0.96) / 0.15)
            stamp(img, "GET UP!", font(F_STENCIL, 210), (W / 2, 330), WHITE, rot=4, scale=1.5 - 0.5 * a, stroke=14)
    if variant == 3:
        # confetti
        rnd = random.Random(42)
        for i in range(140):
            x0 = rnd.uniform(0, W)
            spd = rnd.uniform(120, 320)
            phs = rnd.uniform(0, 1000)
            col = rnd.choice([AMBER, RED, HUD, WHITE, (90, 170, 255)])
            sz = rnd.uniform(10, 22)
            y = ((t - 92.6) * spd + phs) % (H + 100) - 50
            x = x0 + 40 * math.sin(t * 2 + phs)
            ang = t * 4 + phs
            pts = [(x + math.cos(ang + k * math.pi / 2) * sz, y + math.sin(ang + k * math.pi / 2) * sz * 0.6) for k in range(4)]
            d.polygon(pts, fill=col)
        for (gt, s) in ((103.68, "OWEN!"), (104.56, "(OWEN!)")):
            if gt <= t < 106.2:
                a = ease_out((t - gt) / 0.14)
                side = -1 if s == "OWEN!" else 1
                stamp(img, s, font(F_STENCIL if side < 0 else F_SHOUT, 230 if side < 0 else 130), (W / 2 - 160 * side, 430 + 120 * (side > 0)), AMBER if side < 0 else WHITE, rot=-5 * side, scale=1.45 - 0.45 * a, stroke=14)
        if 106.24 <= t < 107.8:
            a = ease_out((t - 106.24) / 0.15)
            sx, sy = shake(t, 12 * (1 - a) + 4)
            stamp(img, "GET UP!!", font(F_STENCIL, 240), (W / 2 + sx, 440 + sy), WHITE, rot=3, scale=1.6 - 0.6 * a, stroke=16)
    draw_hud(img, d, t, mode="alert", match_no={1: 1, 2: 2, 3: 5}[variant], match_t0={1: 0.0, 2: 45.8, 3: 90.0}[variant], alert=0.5 + 0.5 * e, show_cards=False)


def scene_chat(img, d, t):
    d.rectangle((0, 0, W, H), fill=(14, 16, 22))
    for x in range(0, W, 80):
        d.line((x, 0, x, H), fill=(22, 26, 34), width=1)
    x0, y0, x1, y1 = 360, 260, 1460, 780
    rrect(d, (x0, y0, x1, y1), 18, fill=(10, 12, 16), outline=HUD, width=4)
    d.rectangle((x0, y0, x1, y0 + 70), fill=(16, 22, 18))
    text(d, (x0 + 30, y0 + 35), "SQUAD CHAT  —  #hallway", font(F_HUD, 36), HUD, anchor="lm")
    text(d, (x1 - 30, y0 + 35), "2 online", font(F_MONO, 32), HUD_DIM, anchor="rm")
    msgs = [
        (46.6, "OWEN", "hold on bro, I'm unlocking a new tank", JERSEY2),
        (49.8, "ALEX", "you said that MONDAY", JERSEY),
        (51.6, "OWEN", "yeah... and?", JERSEY2),
    ]
    y = y0 + 130
    fnt_n = font(F_HUD, 42)
    fnt_m = font(F_MONO, 46)
    for (mt, who, msg, col) in msgs:
        if t >= mt:
            a = ease_out((t - mt) / 0.25)
            yy = y + 20 * (1 - a)
            # avatar
            d.ellipse((x0 + 40, yy - 34, x0 + 108, yy + 34), fill=col, outline=INK, width=3)
            text(d, (x0 + 74, yy), who[0], font(F_HUD, 40), WHITE)
            text(d, (x0 + 140, yy - 36), who, fnt_n, col, anchor="lm")
            # typewriter
            n = int(clamp((t - mt) / 0.9) * len(msg))
            text(d, (x0 + 140, yy + 26), msg[:n] + ("▌" if n < len(msg) else ""), fnt_m, WHITE, anchor="lm")
            y += 150
    # typing indicator
    nxt = [m for m in msgs if m[0] > t]
    if nxt and t > nxt[0][0] - 1.6:
        who = nxt[0][1]
        dots = "." * (1 + int((t * 3) % 3))
        text(d, (x0 + 40, y + 10), f"{who} is typing{dots}", font(F_MONO, 36), HUD_DIM, anchor="lm")
    if 52.0 <= t < 52.6:
        stamp(img, "AND?!", font(F_SHOUT, 150), (1650, 560), RED, rot=8, scale=1.3 - 0.3 * ease_out((t - 52.0) / 0.15), stroke=10)
    draw_hud(img, d, t, mode="normal", match_no=2, match_t0=45.8, show_cards=False, crosshair=False)


def scene_spotter(img, d, t):
    d.rectangle((0, 0, W, H), fill=(12, 18, 14))
    for x in range(0, W, 80):
        d.line((x, 0, x, H), fill=(20, 30, 22), width=1)
    for y in range(0, H, 80):
        d.line((0, y, W, y), fill=(20, 30, 22), width=1)
    fnt = font(F_STENCIL, 56)
    if t < 55.6:
        text(d, (W / 2, 120), "ALEX'S SPOTTER GUIDE", fnt, HUD, stroke=6)
        text(d, (W / 2, 180), "(100% accurate, do not argue)", font(F_HUD, 34), (200, 200, 190))
    items = [
        ("tank", "THE BIG ONE", 53.44 - 0.6),
        ("tank", "THE ONE WITH TWO GUNS", 53.44 - 0.3),
        ("tank", "THE SNEAKY ONE", 53.44),
        ("plane", "THE LOUD ONE", 54.96 - 0.6),
        ("plane", "THE FAST ONE", 54.96 - 0.3),
        ("plane", "THE ONE THAT ALWAYS CRASHES", 54.96),
    ]
    cw, ch = 440, 250
    for i, (kind, label, ts) in enumerate(items):
        col_i, row_i = i % 3, i // 3
        cx = 560 + col_i * 480
        cy = 360 + row_i * 270
        if t < ts:
            continue
        a = ease_out((t - ts) / 0.3)
        sc = 0.7 + 0.3 * a
        box = (cx - cw / 2 * sc, cy - ch / 2 * sc, cx + cw / 2 * sc, cy + ch / 2 * sc)
        rrect(d, box, 16, fill=(8, 12, 9), outline=HUD if kind == "tank" else AMBER, width=4)
        if kind == "tank":
            draw_tank(d, cx, cy + 40, 0.75 * sc, (120, 135, 110))
        else:
            draw_plane(d, cx, cy - 10, 0.75 * sc, (160, 170, 180), rot=15)
        lf = fit_font(F_HUD, label, cw * sc - 36, 36, 22)
        text(d, (cx, cy + ch / 2 * sc - 32), label, lf, WHITE)
        # second-gun gag
        if label == "THE ONE WITH TWO GUNS":
            draw_tank(d, cx, cy + 40, 0.75 * sc, (120, 135, 110), wobble=-26)
        if label == "THE ONE THAT ALWAYS CRASHES":
            draw_boom(d, cx + 80 * sc, cy - 40, 60 * sc, 0.5 + 0.3 * math.sin(t * 6), txt="")
    # rage meter
    if t >= 55.6:
        a = ease_out((t - 55.6) / 0.3)
        mx0, my0, mx1, my1 = 560, 150, W - 560, 210
        text(d, (W / 2, 100 - 20 * (1 - a)), "OWEN RAGE METER", font(F_HUD, 40), RED)
        rrect(d, (mx0, my0, mx1, my1), 12, fill=(8, 12, 9), outline=RED, width=4)
        level = 0.25 + 0.1 * math.sin(t * 5)
        if t >= 56.56:  # losing
            level = 0.55 + 0.1 * math.sin(t * 9)
        if t >= 57.36:  # yells
            level = 0.97 + 0.03 * math.sin(t * 25)
        rrect(d, (mx0 + 6, my0 + 6, mx0 + 6 + (mx1 - mx0 - 12) * level, my1 - 6), 8, fill=lerp_c(AMBER, RED, level))
        if t >= 57.36:
            sx, sy = shake(t, 8)
            stamp(img, "RAGE DETECTED", font(F_STENCIL, 90), (W / 2 + sx, 500 + sy), RED, rot=-4, stroke=10)
    draw_hud(img, d, t, mode="normal", match_no=2, match_t0=45.8, show_cards=False, crosshair=False)


def scene_offers(img, d, t):
    d.rectangle((0, 0, W, H), fill=(12, 14, 20))
    for x in range(0, W, 80):
        d.line((x, 0, x, H), fill=(20, 24, 32), width=1)
    text(d, (W / 2, 130), "ALEX'S OFFER", font(F_STENCIL, 64), AMBER, stroke=6)
    text(d, (W / 2, 190), "(a very generous deal)", font(F_HUD, 34), (200, 200, 190))
    cards = [
        ("CAPTAIN", 59.44, "👑"),
        ("COACH", 61.20, "📋"),
        ("MAKE THE RULES", 62.72, "📜"),
    ]
    cw, ch = 440, 420
    for i, (label, ts, _) in enumerate(cards):
        cx = 560 + i * 480
        cy = 480
        if t < ts - 0.3:
            continue
        a = ease_out((t - (ts - 0.3)) / 0.35)
        yoff = (1 - a) * 500
        box = (cx - cw / 2, cy - ch / 2 + yoff, cx + cw / 2, cy + ch / 2 + yoff)
        rrect(d, box, 20, fill=(18, 22, 30), outline=AMBER, width=5)
        # icon area
        if label == "CAPTAIN":
            draw_kid(d, cx, cy + 60 + yoff, 220, JERSEY2, 12, arm_up=True)
            # crown
            hx, hy = cx, cy + 60 + yoff - 220 * 0.78 - 220 * 0.15 * 2 - 10
            d.polygon([(hx - 40, hy + 20), (hx + 40, hy + 20), (hx + 40, hy - 10), (hx + 20, hy + 5), (hx, hy - 25), (hx - 20, hy + 5), (hx - 40, hy - 10)], fill=AMBER, outline=INK)
        elif label == "COACH":
            rrect(d, (cx - 70, cy - 120 + yoff, cx + 70, cy + 60 + yoff), 10, fill=WHITE, outline=INK, width=4)
            for k in range(5):
                d.line((cx - 50, cy - 90 + k * 32 + yoff, cx + 50, cy - 90 + k * 32 + yoff), fill=(120, 120, 120), width=4)
            d.ellipse((cx - 30, cy + 10 + yoff, cx + 30, cy + 70 + yoff), fill=RED, outline=INK, width=3)
            draw_ball(d, cx + 90, cy + 40 + yoff, 36)
        else:
            rrect(d, (cx - 90, cy - 120 + yoff, cx + 90, cy + 70 + yoff), 10, fill=(240, 230, 200), outline=INK, width=4)
            for k in range(6):
                d.line((cx - 65, cy - 85 + k * 28 + yoff, cx + 65, cy - 85 + k * 28 + yoff), fill=(90, 80, 60), width=5)
        lf = fit_font(F_HUD, label, cw - 50, 44)
        text(d, (cx, cy + ch / 2 - 60 + yoff), label, lf, WHITE)
        # checkmark
        if t >= ts:
            b = ease_out((t - ts) / 0.2)
            draw_check(d, cx + cw / 2 - 60, cy - ch / 2 + 60 + yoff, 44 * (1.6 - 0.6 * b), HUD)
    # "SOME of the rules" edit
    if t >= 63.7:
        a = ease_out((t - 63.7) / 0.2)
        cx, cy = 560 + 2 * 480, 480
        # red strike + correction
        d.line((cx - 200, cy + ch / 2 - 60, cx + 200, cy + ch / 2 - 60), fill=RED, width=10)
        stamp(img, "SOME rules*", font(F_SHOUT, 84), (cx, cy + ch / 2 + 30), RED, rot=-7, scale=1.3 - 0.3 * a, stroke=8)
    if t >= 64.1:
        text(d, (W / 2, 790), "*subject to Alex's approval. Alex is the captain. See card 1.", font(F_HUD, 36), (220, 220, 210), stroke=3)
    draw_hud(img, d, t, mode="normal", match_no=2, match_t0=45.8, show_cards=False, crosshair=False)


def scene_bridge(img, d, t):
    # sun goes down over the backyard, then MOM alert
    omm = [77.60, 80.48, 83.60, 86.72]
    n = sum(1 for x in omm if t >= x)
    mom_t = 87.84
    if t < 84.88:
        sky, night_t = "day", 0.0
        sun_y = 160 + (t - 77.5) * 20
    elif t < 87.8:
        sky, night_t = "sunset", 0.0
        sun_y = 300 + (t - 84.88) * 110
    else:
        sky, night_t = "night", clamp((t - 87.8) / 1.0)
        sun_y = None
    img.paste(sky_image(sky), (0, 0))
    draw_backyard(img, d, t, sky=sky, sun_y=sun_y, kids=1, night_t=night_t)
    if sky == "night":
        # moon
        d.ellipse((1500 - 60, 150 - 60, 1500 + 60, 150 + 60), fill=(235, 235, 220), outline=INK, width=4)
        d.ellipse((1500 - 30, 150 - 75, 1500 + 70, 150 + 25), fill=SKY_NIGHT[0])
    # darken for night
    if night_t > 0:
        ov = Image.new("RGBA", (W, H), (0, 0, 20, int(110 * night_t)))
        img.paste(ov, (0, 0), ov)
    # match counter
    if t < mom_t:
        cx, cy = W / 2 + 160, 400
        rrect(d, (cx - 420, cy - 150, cx + 420, cy + 150), 24, fill=(8, 10, 12), outline=AMBER, width=6)
        text(d, (cx, cy - 90), "MATCHES REMAINING", font(F_HUD, 40), AMBER)
        last = max([x for x in omm if x <= t], default=None)
        sc = 1.0
        if last is not None and t - last < 0.25:
            sc = 1 + 0.6 * (1 - ease_out((t - last) / 0.25))
        if n == 0:
            s = "1"
        else:
            s = " + ".join(["1"] * n) if n <= 3 else "1 + 1 + 1 + 1"
        stamp(img, s, font(F_DIGI, 130), (cx, cy + 10), WHITE, scale=sc, stroke=8)
        note = ["", "(last one, promise)", "(for real this time)", "(okay LAST last one)", "(...)"][min(n, 4)]
        text(d, (cx, cy + 110), note, font(F_HUD, 34), (220, 220, 210))
        if 81.84 <= t < 83.5:
            # bed icon: clock
            stamp(img, "BEDTIME: SOON", font(F_HUD, 56), (W / 2, 640), RED, rot=-4, stroke=6)
    else:
        # MOM ALERT
        a = clamp((t - mom_t) / 0.3)
        e = rms_at(t)
        sx, sy = shake(t, 14 * a)
        hazard_band(d, 300 + sy, 360 + sy, c1=RED, offset=int(t * 300))
        hazard_band(d, 560 + sy, 620 + sy, c1=RED, offset=-int(t * 300))
        if t < 89.7:
            rrect(d, (W / 2 - 560 + sx, 360 + sy, W / 2 + 560 + sx, 560 + sy), 10, fill=INK, outline=RED, width=8)
            stamp(img, "INCOMING: MOM", font(F_STENCIL, 110), (W / 2 + 60 + sx, 430 + sy), RED, scale=1.5 - 0.5 * a, stroke=10)
            draw_warn(d, W / 2 - 470 + sx, 430 + sy, 70)
            text(d, (W / 2 + sx, 520 + sy), "THREAT LEVEL: MAXIMUM", font(F_HUD, 48), WHITE)
        if t >= 89.7:
            # the face
            b = ease_out((t - 89.7) / 0.3)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, int(140 * b)))
            img.paste(ov, (0, 0), ov)
            fx, fy = W / 2, 440
            r = 150
            d.ellipse((fx - r, fy - r, fx + r, fy + r), fill=SKIN, outline=INK, width=6)
            # hair
            d.chord((fx - r, fy - r, fx + r, fy + r), 190, 350, fill=(70, 45, 30))
            # angry brows
            d.line((fx - 95, fy - 45, fx - 30, fy - 20), fill=INK, width=14)
            d.line((fx + 95, fy - 45, fx + 30, fy - 20), fill=INK, width=14)
            d.ellipse((fx - 70, fy - 15, fx - 40, fy + 15), fill=INK)
            d.ellipse((fx + 40, fy - 15, fx + 70, fy + 15), fill=INK)
            d.line((fx - 50, fy + 80, fx + 50, fy + 80), fill=INK, width=12)
            rrect(d, (fx - 230, fy + 190, fx + 230, fy + 270), 14, fill=INK, outline=RED, width=5)
            text(d, (fx, fy + 230), "THE FACE", font(F_STENCIL, 54), RED)
    mom = 0.0
    if t >= mom_t - 1.2:
        mom = clamp((t - (mom_t - 1.2)) / 2.5)
    draw_hud(img, d, t, mode="alert" if t >= mom_t else "normal", match_no=2 + n, match_t0=omm[n - 1] if n else 77.5, mom=mom, alert=clamp((t - mom_t) / 0.3) if t >= mom_t else 0, show_cards=False, crosshair=False)


def scene_paused(img, d, t):
    # Owen's screen: a game view, then PAUSED
    d.rectangle((0, 0, W, H), fill=(40, 60, 40))
    img.paste(sky_image("day").resize((W, 500)), (0, 0))
    d.rectangle((0, 500, W, H), fill=(76, 110, 60))
    for k in range(0, W, 200):
        d.polygon([(k, 500), (k + 100, 380), (k + 200, 500)], fill=(60, 90, 70))
    draw_tank(d, 420, 780, 1.5, (110, 125, 95))
    draw_plane(d, 1560, 330, 0.9, (160, 170, 180), rot=5)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 150))
    img.paste(ov, (0, 0), ov)
    a = ease_out((t - 107.9) / 0.3)
    stamp(img, "PAUSED", font(F_STENCIL, 230), (W / 2, 400), WHITE, scale=1.5 - 0.5 * a, stroke=14)
    # pause bars
    d.rectangle((W / 2 + 60, 520, W / 2 + 110, 640), fill=WHITE, outline=INK, width=4)
    d.rectangle((W / 2 + 150, 520, W / 2 + 200, 640), fill=WHITE, outline=INK, width=4)
    if t >= 109.9:
        b = ease_out((t - 109.9) / 0.35)
        y = 760 - (1 - b) * 200
        rrect(d, (W / 2 - 620, y - 60, W / 2 + 620, y + 60), 18, fill=INK, outline=AMBER, width=6)
        text(d, (W / 2 - 560, y), "★", font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60), AMBER, anchor="lm")
        text(d, (W / 2 - 480, y - 24), "ACHIEVEMENT UNLOCKED", font(F_HUD, 34), AMBER, anchor="lm")
        text(d, (W / 2 - 480, y + 26), "He Actually Paused It  (first time ever)", font(F_HUD, 40), WHITE, anchor="lm")
    tagf = font(F_HUD, 44)
    rrect(d, (W / 2 - 500, 560 - 50, W / 2 - 60, 560 + 50), 12, fill=INK, outline=HUD, width=4)
    text(d, (W / 2 - 280, 560), "OWEN: PAUSED (!!)", font(F_HUD, 36), HUD)
    draw_hud(img, d, t, mode="paused", match_no=5, match_t0=90.0, show_cards=False, crosshair=False)


def scene_backyard2(img, d, t):
    draw_backyard(img, d, t, sky="sunset", sun_y=250, kids=2, labels=(t >= 112.9), ball_x=1000 + 300 * math.sin(t * 2.2))
    if 115.44 <= t < 116.3:
        stamp(img, "DON'T ARGUE.", font(F_SHOUT, 110), (W / 2, 560), RED, rot=-5, scale=1.3 - 0.3 * ease_out((t - 115.44) / 0.15), stroke=9)
    if t >= 117.9:
        a = ease_out((t - 117.9) / 0.3)
        y = 200 - 60 * (1 - a)
        rrect(d, (W / 2 - 440, y - 70, W / 2 + 440, y + 70), 18, fill=INK, outline=HUD, width=5)
        text(d, (W / 2, y - 24), "QUEUE POSITION: #2", font(F_HUD, 44), HUD)
        text(d, (W / 2, y + 28), "estimated wait: \"one more match\"", font(F_MONO, 36), (220, 220, 210))
    draw_hud(img, d, t, mode="normal", match_no=6, match_t0=112.1, show_cards=False, crosshair=False)


def scene_end(img, d, t):
    scene_title(img, d, t)
    a = clamp((t - 119.4) / 0.5)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - a))))
    img.paste(ov, (0, 0), ov)


def render_frame(t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    name, a, b = scene_at(t)
    if name == "title":
        scene_title(img, d, t)
    elif name == "door":
        scene_door(img, d, t)
        draw_hud(img, d, t, mode="normal", match_no=1, match_t0=0.0, show_cards=(t > 6.9))
    elif name == "hallway":
        scene_hallway(img, d, t)
        draw_hud(img, d, t, mode="normal", match_no=1, match_t0=0.0, show_cards=True)
    elif name == "backyard":
        scene_backyard(img, d, t)
        draw_hud(img, d, t, mode="normal", match_no=1, match_t0=0.0, show_cards=False)
    elif name == "chorus":
        scene_chorus(img, d, t, 29.56, variant=1)
    elif name == "chat":
        scene_chat(img, d, t)
    elif name == "spotter":
        scene_spotter(img, d, t)
    elif name == "offers":
        scene_offers(img, d, t)
    elif name == "chorus2":
        scene_chorus(img, d, t, 66.56, variant=2)
    elif name == "bridge":
        scene_bridge(img, d, t)
    elif name == "chorus3":
        scene_chorus(img, d, t, 94.24, variant=3)
    elif name == "paused":
        scene_paused(img, d, t)
    elif name == "backyard2":
        scene_backyard2(img, d, t)
    else:
        scene_end(img, d, t)
    # cut flash on scene starts (not title)
    if name not in ("title", "end") and t - a < 0.1:
        f = int(120 * (1 - (t - a) / 0.1))
        ov = Image.new("RGBA", (W, H), (255, 255, 255, f))
        img.paste(ov, (0, 0), ov)
    draw_lyrics(img, d, t)
    img.paste(scanlines(), (0, 0), scanlines())
    return img


def main():
    cmd = sys.argv[1]
    if cmd == "frame":
        t = float(sys.argv[2])
        render_frame(t).save(sys.argv[3])
    elif cmd == "thumb":
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        scene_title(img, d, 1.4, thumb=True)
        img.paste(scanlines(), (0, 0), scanlines())
        img.resize((1280, 720), Image.LANCZOS).save(sys.argv[2])
    elif cmd == "segment":
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        out = sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            img = render_frame(f / FPS)
            p.stdin.write(img.tobytes())
            if (f - f0) % 150 == 0:
                print(f"{out}: frame {f}/{f1}", flush=True)
        p.stdin.close()
        p.wait()


if __name__ == "__main__":
    main()
