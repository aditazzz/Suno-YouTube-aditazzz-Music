#!/usr/bin/env python3
"""LGTM - 'The Church of LGTM' music video renderer. Every frame is drawn by this program."""
import os, sys, math, json, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import uniform_filter1d
import doc as docmod

V = os.environ.get("LGTM_V") == "1"
W, H, FPS = (1080, 1920, 30) if V else (1920, 1080, 30)
CX = W // 2
DUR = 179.92
HERE = os.path.dirname(os.path.abspath(__file__))
FD = HERE + "/fonts/"
INTER = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
INTERB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
MONO, MONOB = "jetbrains-mono-400", "jetbrains-mono-700"
CINZ, CINZB = "cinzel-700", "cinzel-900"
CORM, CORMI = "cormorant-garamond-600", "cormorant-garamond-500-italic"

BG = (10, 10, 11)
IVORY = (236, 230, 216)
DIM = (140, 136, 128)
FAINT = (58, 57, 54)
GREEN = (102, 214, 146)
GREEN_BG = (16, 42, 28)
RED = (232, 106, 110)
RED_BG = (50, 20, 24)

_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc:
        p = name if name.startswith("/") else FD + name + ".ttf"
        _fc[k] = ImageFont.truetype(p, int(size))
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def seg(t, a, b): return clamp((t - a) / (b - a))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def window(t, a, b, fi=0.25, fo=0.35):
    return min(seg(t, a - fi, a), 1 - seg(t, b, b + fo))
def kf(t, pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return float(np.interp(t, xs, ys))

# ------------------------------------------------------------------ sprites
_tc = {}
def text_sprite(txt, font, color, tracking=0):
    key = (txt, font.path, font.size, color, tracking)
    if key in _tc: return _tc[key]
    asc, desc = font.getmetrics()
    if tracking == 0:
        w = int(font.getlength(txt)) + 8
        img = Image.new("RGBA", (max(w, 2), asc + desc + 4), color + (0,))
        ImageDraw.Draw(img).text((4, 0), txt, font=font, fill=color + (255,))
    else:
        w = int(sum(font.getlength(c) + tracking for c in txt)) + 8
        img = Image.new("RGBA", (max(w, 2), asc + desc + 4), color + (0,))
        d = ImageDraw.Draw(img); x = 4
        for c in txt:
            d.text((x, 0), c, font=font, fill=color + (255,)); x += font.getlength(c) + tracking
    _tc[key] = img
    return img

def paste(frame, spr, x, y, alpha=1.0):
    if alpha <= 0.004: return
    if alpha < 0.996:
        a = spr.getchannel("A").point(lambda v: int(v * alpha))
        frame.paste(spr, (int(round(x)), int(round(y))), a)
    else:
        frame.paste(spr, (int(round(x)), int(round(y))), spr)

def paste_c(frame, spr, cx, cy, alpha=1.0):
    paste(frame, spr, cx - spr.width / 2, cy - spr.height / 2, alpha)

def txt(frame, s, font, color, x, y, alpha=1.0, anchor="l", tracking=0):
    sp = text_sprite(s, font, color, tracking)
    if anchor == "c": x -= sp.width / 2
    elif anchor == "r": x -= sp.width
    paste(frame, sp, x, y, alpha)
    return sp.width

def ss(w, h, fn, scale=3):
    img = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    fn(ImageDraw.Draw(img), scale)
    return img.resize((w, h), Image.LANCZOS)

def add_light(frame, glow, x, y, k):
    """additive blend of RGB sprite `glow` at (x,y) scaled by k"""
    if k <= 0.01: return
    x, y = int(x), int(y)
    box = (max(0, x), max(0, y), min(W, x + glow.width), min(H, y + glow.height))
    if box[2] <= box[0] or box[3] <= box[1]: return
    g = glow.crop((box[0] - x, box[1] - y, box[2] - x, box[3] - y))
    if k < 0.99 or k > 1.01:
        g = g.point(lambda v: min(255, int(v * k)))
    frame.paste(ImageChops.add(frame.crop(box), g), box)

# ------------------------------------------------------------------ timing
B = json.load(open(HERE + "/beats.json"))
BEATS = np.array(B["beats"]); ENV = np.array(B["env"]); ONS = np.array(B["onset"])
def env(t): return float(ENV[min(len(ENV) - 1, max(0, int(t * 30)))])
def beat_info(t):
    i = int(np.searchsorted(BEATS, t, side="right")) - 1
    if i < 0: return 0, 0.0
    return i, math.exp(-7.0 * (t - BEATS[i]))
def snap(t, tol=0.28):
    j = int(np.argmin(np.abs(BEATS - t)))
    return float(BEATS[j]) if abs(BEATS[j] - t) < tol else t

# chorus: (L onset, "looks" onset, "I did" onset)
CH = [(0.74, 5.3, 10.1), (18.9, 23.1, 28.1), (56.7, 60.9, 65.6), (74.45, 78.6, 83.4), (134.4, 138.6, 143.6), (152.15, 156.2, 161.1)]
STAMPS = [snap(c[2] + 2.95) for c in CH]
OUTRO_L = [169.6, 174.35]
LYR = []
for i, (l, lk, idd) in enumerate(CH):
    LYR.append((lk, lk + 3.3, "looks good to me", "ci"))
    LYR.append((idd, STAMPS[i] + 1.3, "I did not read a single line", "cb"))
LYR += [
    (35.3, 36.9, "There's a change in the auth", "v"), (37.0, 39.5, "and a change in the schema", "v"),
    (39.8, 43.9, "There's a comment that says “temporary, remove later”", "v"),
    (44.3, 47.7, "and later was fourteen months ago", "v"),
    (48.6, 50.2, "But the tests are green", "v"), (50.3, 53.6, "so away we do go", "v"),
    (90.8, 92.4, "He'll review mine on Thursday", "v"), (92.5, 94.9, "same as I did his", "v"),
    (95.6, 99.3, "and neither of us knows what the other one is", "v"),
    (100.0, 103.9, "It's a covenant, a promise, a sacred trade", "v"),
    (104.4, 108.4, "Two engineers and the mess we made", "v"),
    (114.2, 115.3, "One nit", "v"), (115.4, 117.7, "I left one nit", "v"),
    (117.9, 121.7, "a variable name on line four hundred", "v"),
    (122.0, 125.7, "so he knows that I was there", "v"), (126.5, 131.3, "so he knows that I care", "v"),
]
# window in which the words of a line get sung (fraction of the line's span)
SUNG = {"ci": 0.45, "cb": 0.66, "v": 0.78}

# ------------------------------------------------------------------ diff document
DOC, AN = docmod.build()
LH, DW, DX0, DY0 = (41, 1080, 0, 370) if V else (34, 1520, 200, 150)
FS = 24 if V else 20
X_OLD, X_NEW, X_SIGN, X_CODE, X_FILE = (None, 76, 96, 125, 22) if V else (70, 142, 162, 190, 18)
CW = 14.4 if V else 12.0
ANCH = 500 if V else 330
HX0, HX1 = (44, 1036) if V else (200, 1720)
VH = H - DY0
_auth, _schema, _temp, _tests, _mess, _l400, _end = AN["auth"], AN["schema"], AN["temp"], AN["tests"], AN["mess"], AN["l400"], AN["end"]
KF = [(0, 0), (13.0, 2.0), (14.5, 10), (17, 70), (19.5, 170), (34.7, _auth - 14), (35.5, _auth + 2), (36.7, _auth + 4.5),
      (37.4, _schema + 2), (39.3, _schema + 4.5), (40.2, _temp - 0.5), (47.3, _temp + 2.0), (48.7, _tests + 2), (50.3, _tests + 4.5),
      (52.5, _tests + 50), (56.5, _tests + 190), (88.0, _tests + 1324), (104.3, _mess - 24), (105.3, _mess + 3), (108.2, _mess + 11),
      (110.6, _l400 - 45), (113.6, _l400), (131.2, _l400), (133.2, _l400 + 14), (136, _l400 + 110), (163.5, _end - 70), (166.3, _end - 6),
      (181, _end - 6)]
assert all(KF[i][1] <= KF[i + 1][1] for i in range(len(KF) - 1)), [(KF[i], KF[i + 1]) for i in range(len(KF) - 1) if KF[i][1] > KF[i + 1][1]]
_P = PchipInterpolator([k[0] for k in KF], [k[1] for k in KF])
def warp(t):
    if t < 13.4 or t > 166.3: return t
    i = int(np.searchsorted(BEATS, t, side="right")) - 1
    if i < 0 or i >= len(BEATS) - 1: return t
    b0, b1 = BEATS[i], BEATS[i + 1]
    u = (t - b0) / (b1 - b0)
    return b0 + (b1 - b0) * ease(min(1.0, u / 0.42))
def scroll(t):
    A = 20 + (ANCH - 20) * ease(seg(t, 13, 19))
    return float(_P(clamp(warp(t), 0, 180))) * LH - A
def line_y(idx, t): return DY0 + idx * LH - scroll(t)

_strips = {}
def strip(idx, z=1.0):
    key = (idx, z)
    if key in _strips: return _strips[key]
    lh, dw = int(round(LH * z)), int(round(DW * z))
    L = DOC[idx] if 0 <= idx < len(DOC) else {"k": "gap", "t": ""}
    k = L["k"]
    band = {"add": GREEN_BG, "del": RED_BG, "file": (24, 24, 26), "hunk": (15, 17, 21)}.get(k, BG)
    img = Image.new("RGB", (dw, lh), band)
    d = ImageDraw.Draw(img)
    fm, fb = F(MONO, FS * z), F(MONOB, (FS + 1) * z)
    ty = int((5 if V else 4) * z)
    if k == "file":
        d.line([(0, 0), (dw, 0)], fill=FAINT, width=1)
        d.text((int(X_FILE * z), ty), L["t"], font=fb, fill=IVORY)
    elif k == "hunk":
        d.text((int(X_CODE * z), ty), L["t"], font=fm, fill=(104, 116, 138))
    elif k == "end":
        w = fm.getlength("—  " + L["t"] + "  —")
        d.text(((dw - w) / 2, ty), "—  " + L["t"] + "  —", font=fm, fill=DIM)
    elif k in ("add", "del", "ctx"):
        numc = (92, 90, 85)
        if X_OLD is None:
            nn = L["n"] if L["n"] is not None else L["o"]
            s = str(nn); d.text((int(X_NEW * z) - fm.getlength(s), ty), s, font=fm, fill=numc)
        else:
            if L["o"] is not None:
                s = str(L["o"]); d.text((int(X_OLD * z) - fm.getlength(s), ty), s, font=fm, fill=numc)
            if L["n"] is not None:
                s = str(L["n"]); d.text((int(X_NEW * z) - fm.getlength(s), ty), s, font=fm, fill=numc)
        col = {"add": (188, 236, 206), "del": (240, 176, 180), "ctx": (150, 146, 138)}[k]
        sign = {"add": "+", "del": "−", "ctx": " "}[k]
        d.text((int(X_SIGN * z), ty), sign, font=fm, fill={"add": GREEN, "del": RED, "ctx": DIM}[k])
        d.text((int(X_CODE * z), ty), L["t"], font=fm, fill=col)
    arr = np.asarray(img).copy()
    if len(_strips) > 900: _strips.clear()
    _strips[key] = arr
    return arr

def diff_layer(t, dim=1.0, z=1.0, x0=None, y_anchor=None):
    """returns RGB array (VH x DW) of the diff at time t. z>1 renders natively zoomed around line 400."""
    s = scroll(t)
    v = abs(scroll(t + 1 / FPS) - s)
    blur = int(v * 0.55)
    pad = blur + 2 if blur > 2 else 0
    if z == 1.0:
        lh, dw, top = LH, DW, s - pad
        vh = VH + 2 * pad
    else:
        lh = int(round(LH * z)); dw = int(round(DW * z)); vh = H; pad = 0
        # keep line 400's top at y_anchor (absolute screen y) -> layer starts at screen y=0
        top = _l400 * lh - y_anchor
    out = np.empty((vh, dw, 3), np.uint8); out[:] = BG
    i0 = int(math.floor(top / lh)); i1 = int(math.floor((top + vh) / lh)) + 1
    for i in range(max(0, i0), min(len(DOC), i1)):
        y = int(round(i * lh - top))
        st = strip(i, z)
        a = max(0, -y); b = min(lh, vh - y)
        if b > a: out[y + a:y + b] = st[a:b]
    if z == 1.0 and blur > 2:
        out = uniform_filter1d(out, size=blur, axis=0, mode="nearest")[pad:pad + VH]
    if dim < 0.995:
        bg = np.array(BG, np.float32)
        out = (bg + (out.astype(np.float32) - bg) * dim).astype(np.uint8)
    return out

DIMK = [(0, 0.0), (0.6, 1.0), (15.5, 1.0), (18.5, 0.42), (33.3, 0.42), (34.6, 1.0), (54.2, 1.0), (56.6, 0.26), (88.2, 0.26),
        (89.4, 0.14), (104.0, 0.14), (105.0, 0.95), (131.6, 1.0), (133.6, 0.24), (166.2, 0.24), (167.3, 0.0), (181, 0.0)]

# ------------------------------------------------------------------ static art
def make_scrim():
    a = np.zeros((H, W), np.float32)
    ys = np.arange(H)
    g = np.clip((ys - (1230 if V else 770)) / 130.0, 0, 1) ** 1.4 * 0.9
    a[:] = g[:, None]
    top = np.clip((150 - ys) / 150.0, 0, 1) * 0.0
    img = Image.new("RGBA", (W, H), BG + (0,))
    img.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return img
SCRIM = make_scrim()

def make_spot():
    """dark veil with a clear band around the nit line"""
    a = np.zeros((H, W), np.float32)
    ys = np.arange(H)
    d = np.abs(ys - ((DY0 + ANCH + LH // 2) if V else 497))
    g = np.clip((d - 60) / 240.0, 0, 1) * 0.72
    a[:] = g[:, None]
    img = Image.new("RGBA", (W, H), BG + (0,))
    img.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return img
SPOT = make_spot()

# ---- stained glass window
WW, WHT = 500, 690
WX, WY = CX - WW // 2, (420 if V else 150)
def arch_poly(w, ys, R, bottom, n=40, inset=0.0):
    pts = []
    apex_ang = math.acos((R - w / 2) / R)
    for i in range(n + 1):  # left arc, centre (R, ys)
        a = math.pi - apex_ang * i / n
        pts.append((R + (R - inset) * math.cos(a), ys - (R - inset) * math.sin(a)))
    for i in range(n + 1):  # right arc, centre (w-R, ys)
        a = apex_ang * (1 - i / n)
        pts.append((w - R + (R - inset) * math.cos(a), ys - (R - inset) * math.sin(a)))
    pts.append((w - inset, bottom - inset)); pts.append((inset, bottom - inset))
    return pts

def build_window():
    S = 3
    ys, R = 352, 372
    outer = arch_poly(WW, ys, R, WHT)
    cx, cy, rr = WW / 2, 212, 118
    def draw_lead(d, s):
        P = lambda pts: [(x * s, y * s) for x, y in pts]
        col = IVORY + (255,)
        d.line(P(outer + [outer[0]]), fill=col, width=int(2.4 * s), joint="curve")
        inner = arch_poly(WW, ys, R, WHT, inset=13)
        d.line(P(inner + [inner[0]]), fill=IVORY + (150,), width=int(1 * s), joint="curve")
        for r, wd, al in [(rr, 2.0, 255), (rr - 11, 1.0, 150), (36, 1.6, 255)]:
            d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], outline=IVORY + (al,), width=max(1, int(wd * s)))
        for k in range(8):
            a = math.pi / 8 + k * math.pi / 4
            d.line(P([(cx + 36 * math.cos(a), cy + 36 * math.sin(a)), (cx + (rr - 11) * math.cos(a), cy + (rr - 11) * math.sin(a))]), fill=col, width=int(1.4 * s))
        # two lancets
        for lx in (26, WW / 2 + 6):
            lw, ly, lr = WW / 2 - 32, 470, 172
            lp = arch_poly(lw, ly, lr, WHT - 26)
            d.line(P([(x + lx, y) for x, y in lp] + [(lp[0][0] + lx, lp[0][1])]), fill=col, width=int(1.6 * s), joint="curve")
            for yy in (540, 606):
                d.line(P([(lx, yy), (lx + lw, yy)]), fill=IVORY + (170,), width=int(1 * s))
        # check mark in the hub
        d.line(P([(cx - 14, cy + 1), (cx - 4, cy + 11), (cx + 15, cy - 11)]), fill=GREEN + (255,), width=int(3.2 * s), joint="curve")
    lead = ss(WW, WHT, draw_lead, S)
    mask = ss(WW, WHT, lambda d, s: d.polygon([(x * s, y * s) for x, y in arch_poly(WW, ys, R, WHT, inset=3)], fill=(255, 255, 255, 255)), S).getchannel("A")
    rng = random.Random(54)
    Gs = [(72, 190, 125), (46, 140, 92), (120, 226, 160)]
    Rs = [(214, 92, 98), (160, 60, 68), (236, 128, 132)]
    Is = [(206, 200, 186), (124, 120, 112), (236, 230, 216)]
    def region(x, y):
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        if r < 36: return "i"
        if r < rr:
            return "g" if int(((math.atan2(dy, dx) + math.pi / 8) % (2 * math.pi)) / (math.pi / 4)) % 2 == 0 else "r"
        if y > 400: return "g" if x < WW / 2 else "r"
        return "i"
    rows = []
    y = WHT - 16
    while y > 6:
        x = 8 + rng.choice([0, 0, 10, 20])
        bars = []
        while x < WW - 10:
            ln = rng.randint(12, 58)
            reg = region(x + ln / 2, y)
            pal = {"g": Gs, "r": Rs, "i": Is}[reg]
            if rng.random() < 0.16: pal = rng.choice([Gs, Rs, Is])
            bars.append((x, min(WW - 6, x + ln), rng.choice(pal)))
            x += ln + rng.randint(5, 9)
        rows.append((y, bars))
        y -= 10
    full = Image.new("RGB", (WW, WHT), (9, 9, 11))
    d = ImageDraw.Draw(full)
    for y, bars in rows:
        for x0, x1, c in bars: d.rectangle([x0, y, x1, y + 5], fill=c)
    M = 240
    gl = Image.new("RGB", (WW + 2 * M, WHT + 2 * M), (0, 0, 0))
    gl.paste(full, (M, M), mask)
    glow = gl.filter(ImageFilter.GaussianBlur(46)).point(lambda v: min(255, int(v * 1.25)))
    return lead, mask, rows, full, glow, M
LEAD, WMASK, WROWS, WFULL, WGLOW, WGM = build_window()

def build_rays():
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    ox, oy = CX, WY + 212
    rng = random.Random(7)
    for k in range(9):
        a = math.radians(38 + k * 13 + rng.uniform(-3, 3))
        wd = math.radians(rng.uniform(2.2, 4.5))
        L = 2200
        c = rng.choice([(34, 46, 38), (44, 42, 36), (40, 30, 30)])
        d.polygon([(ox, oy), (ox + L * math.cos(a - wd), oy + L * math.sin(a - wd)), (ox + L * math.cos(a + wd), oy + L * math.sin(a + wd))], fill=c)
    return img.filter(ImageFilter.GaussianBlur(22))
RAYS = build_rays()

def window_layer(frame, t, alpha, p, lead_wipe=1.0, glow=0.0):
    if alpha <= 0.004: return
    if glow > 0.01: add_light(frame, WGLOW, WX - WGM, WY - WGM, glow)
    if p >= 0.999:
        glass = WFULL
    else:
        glass = Image.new("RGB", (WW, WHT), (9, 9, 11))
        d = ImageDraw.Draw(glass)
        n = p * len(WROWS)
        for i, (y, bars) in enumerate(WROWS):
            if i > n: break
            fresh = clamp((n - i) / 5.0)
            fr = n - i
            for x0, x1, c in bars:
                if fr < 1.0 and (x0 / WW) > fr: break
                if fresh < 1:
                    c = tuple(int(c[j] + (245 - c[j]) * (1 - fresh)) for j in range(3))
                d.rectangle([x0, y, x1, y + 5], fill=c)
    m = WMASK if alpha > 0.996 else WMASK.point(lambda v: int(v * alpha * 0.96))
    frame.paste(glass, (WX, WY), m)
    if lead_wipe >= 0.999:
        paste(frame, LEAD, WX, WY, alpha)
    else:
        yc = int(WHT * (1 - lead_wipe))
        paste(frame, LEAD.crop((0, yc, WW, WHT)), WX, WY + yc, alpha)

# ---- choir
def build_singer():
    def fn(d, s):
        d.ellipse([17 * s, 6 * s, 47 * s, 36 * s], outline=IVORY + (255,), width=int(1.6 * s))
        d.line([(24 * s, 21 * s), (30 * s, 27 * s), (40 * s, 15 * s)], fill=GREEN + (255,), width=int(2.4 * s), joint="curve")
        d.line([(22 * s, 44 * s), (42 * s, 44 * s), (56 * s, 118 * s), (8 * s, 118 * s), (22 * s, 44 * s)], fill=IVORY + (230,), width=int(1.4 * s), joint="curve")
        d.line([(32 * s, 44 * s), (32 * s, 118 * s)], fill=IVORY + (90,), width=int(1 * s))
    sp = ss(64, 124, fn, 3)
    back = Image.new("RGBA", (64, 124), BG + (0,))
    ImageDraw.Draw(back).polygon([(22, 44), (42, 44), (56, 118), (8, 118)], fill=BG + (235,))
    ImageDraw.Draw(back).ellipse([17, 6, 47, 36], fill=BG + (235,))
    back.alpha_composite(sp)
    return back
SINGER = build_singer()
CHOIR = []
for r in range(3):
    for side in (-1, 1):
        for k in range(6 - r):
            CHOIR.append((r, CX + side * ((35 if V else 338) + k * 70 + r * 35), (1190 if V else 668) + r * 44, (k + r) % 2, k))
CHOIR.sort(key=lambda c: c[0])

def choir_layer(frame, t, vis):
    if vis <= 0.004: return
    bi, bp = beat_info(t)
    for r, x, y, par, k in CHOIR:
        ent = eout(clamp(vis * 1.6 - (k * 0.07 + r * 0.12)))
        if ent <= 0.01: continue
        bob = -11 * bp * (1.0 if (bi % 2) == par else 0.25)
        paste(frame, SINGER, x - 32, y - 60 + bob + (1 - ent) * 70, ent)

# ---- stamp
def build_stamp(text_top="REVIEWED  ·  APPROVED", text_bot="0  LINES  READ", color=GREEN, w=640, h=320):
    S = 2
    def fn(d, s):
        c = color + (255,)
        d.rounded_rectangle([8 * s, 8 * s, (w - 8) * s, (h - 8) * s], radius=26 * s, outline=c, width=9 * s)
        d.rounded_rectangle([26 * s, 26 * s, (w - 26) * s, (h - 26) * s], radius=14 * s, outline=c, width=2 * s)
        f = F(CINZB, 150 * s); tw = f.getlength("LGTM")
        d.text(((w * s - tw) / 2, 74 * s), "LGTM", font=f, fill=c)
        f2 = F(MONOB, 22 * s)
        for txt_, yy in ((text_top, 44), (text_bot, 248)):
            tw = sum(f2.getlength(ch) + 3 * s for ch in txt_); x = (w * s - tw) / 2
            for ch in txt_:
                d.text((x, yy * s), ch, font=f2, fill=c); x += f2.getlength(ch) + 3 * s
    img = ss(w, h, fn, S)
    rng = np.random.default_rng(3)
    n = rng.random((h // 4, w // 4)).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    wear = np.clip((n - 0.22) * 4.0, 0.35, 1.0)
    a = np.asarray(img.getchannel("A"), np.float32) * wear
    img.putalpha(Image.fromarray(a.astype(np.uint8)))
    return img
STAMP0 = build_stamp()
STAMP = {ang: STAMP0.rotate(ang, expand=True, resample=Image.BICUBIC) for ang in (-9, -5, 6, 10, -13, 4)}
MINI = {ang: STAMP0.resize((208, 104), Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC) for ang in (-14, -8, -3, 5, 9, 15)}
STAMP_ANG = [-9, -5, 6, -9, 10, -9]

def stamp_layer(frame, tau, cx, cy, ang, hold=1.7, base=1.0):
    if tau < 0 or tau > hold + 0.4: return
    sp = STAMP[ang]
    sc = base * (1 + 1.9 * math.exp(-tau * 24))
    a = clamp(tau * 18) * (1 - seg(tau, hold, hold + 0.4))
    if abs(sc - 1) > 0.01:
        sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
    paste_c(frame, sp, cx, cy, a)

# mini stamp rain in the last choruses
_rr = random.Random(11)
RAIN = []
_rb = [b for b in BEATS if 134.3 < b < 165.2]
for i, b in enumerate(_rb[::2]):
    side = -1 if i % 2 == 0 else 1
    RAIN.append((float(b), CX + side * (_rr.randint(330, 440) if V else _rr.randint(350, 700)), (_rr.randint(440, 1090) if V else _rr.randint(250, 570)), _rr.choice(list(MINI.keys()))))
def approvals(t):
    n = sum(1 for s in STAMPS[:4] if t >= s)
    n += (t >= 92.3) + (t >= 93.9)
    if t >= 134.4:
        n += min(104, int(104 * (t - 134.4) / (STAMPS[5] - 134.4)))
    if t >= STAMPS[5]: n = 111
    return n
N_FINAL = approvals(170)

# ---- big letters
LET_F = F(CINZB, 250 if V else 300)
LETX = [140, 390, 640, 905] if V else [462, 792, 1128, 1462]
LETY = 700 if V else 470
def build_letter(ch):
    sp = text_sprite(ch, LET_F, IVORY)
    pad = 60
    base = Image.new("RGBA", (sp.width + 2 * pad, sp.height + 2 * pad), BG + (0,))
    sh = Image.new("RGBA", base.size, BG + (0,))
    sh.paste(BG + (255,), (pad, pad), sp.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    sh.putalpha(sh.getchannel("A").point(lambda v: min(255, int(v * 1.7))))
    base.alpha_composite(sh); base.alpha_composite(sp, (pad, pad))
    return base
LETTERS = [build_letter(c) for c in "LGTM"]

def letters_layer(frame, t):
    for ci, (l, lk, idd) in enumerate(CH):
        if ci == 0: continue
        if t < l - 0.05 or t > STAMPS[ci] + 0.5: continue
        hold = 1 - seg(t, lk - 0.55, lk - 0.05)
        out = 1 - seg(t, STAMPS[ci] - 0.15, STAMPS[ci] + 0.25)
        for i in range(4):
            tau = t - (l + i * 0.28)
            if tau < 0: continue
            sc = 1 + 1.5 * math.exp(-tau * 20)
            a = clamp(tau * 14) * hold * out
            sp = LETTERS[i]
            if sc > 1.01: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
            paste_c(frame, sp, LETX[i], LETY, a)

# ---- captions
def caption(frame, t):
    for a, b, s, kind in LYR:
        if t < a - 0.15 or t > b + 0.4: continue
        al = min(seg(t, a - 0.12, a + 0.05), 1 - seg(t, b, b + 0.35))
        if V:
            if kind == "v": font, y = F(CORM, 54), 1392
            elif kind == "ci": font, y = F(CORMI, 68), 1384
            else: font, y = F(CORM, 66), 1386
        else:
            if kind == "v": font, y = F(CORM, 66), 912
            elif kind == "ci": font, y = F(CORMI, 82), 900
            else: font, y = F(CORM, 86), 898
        words = s.split(" ")
        sw = font.getlength(" ")
        widths = [font.getlength(w) for w in words]
        total = sum(widths) + sw * (len(words) - 1)
        maxw = 860 if V else 1500
        rows = [list(range(len(words)))]
        if total > maxw:
            best, bi_ = 1e9, 1
            for cut in range(1, len(words)):
                w1 = sum(widths[:cut]) + sw * (cut - 1); w2 = sum(widths[cut:]) + sw * (len(words) - cut - 1)
                if max(w1, w2) < best: best, bi_ = max(w1, w2), cut
            rows = [list(range(bi_)), list(range(bi_, len(words)))]
            y -= int(font.size * 0.56)
        span = (b - a) * SUNG[kind]
        for ri, row in enumerate(rows):
            rw = sum(widths[i] for i in row) + sw * (len(row) - 1)
            x = (W - rw) / 2
            for i in row:
                wt = a + span * i / max(1, len(words))
                wa = seg(t, wt - 0.04, wt + 0.12)
                if wa > 0:
                    paste(frame, text_sprite(words[i], font, IVORY), x - 4, y + ri * int(font.size * 1.12) + (1 - eout(wa)) * 10, al * wa)
                x += widths[i] + sw

# ---- header chrome
def header(frame, t, a=1.0):
    if a <= 0.004: return
    y1 = 262 if V else 52
    x = HX0
    x += txt(frame, "#1111", F(MONO, 26), DIM, x, y1 + 3, a) + 14
    x += txt(frame, "misc cleanup (small)", F(INTERB, 32), IVORY, x, y1 - 4, a) + 22
    merged = t >= 167.6
    pill = PILL_MERGED if merged else PILL_OPEN
    paste(frame, pill, x, y1 + 1, a)
    xr = HX1
    y2 = 318 if V else 102
    if not V:
        xr -= txt(frame, "187 files changed", F(MONO, 22), DIM, xr, y1 + 5, a, "r") + 22
        xr -= txt(frame, "−3,907", F(MONOB, 22), RED, xr, y1 + 5, a, "r") + 14
        txt(frame, "+4,812", F(MONOB, 22), GREEN, xr, y1 + 5, a, "r")
        txt(frame, "aditazzz wants to merge 111 commits into main from thursday", F(INTER, 21), DIM, HX0, y2, a)
    xr = HX1
    ncom = 1 if t >= 118.9 else 0
    nap = approvals(t)
    viewed = "0"
    for label, val, hot in (("comments", str(ncom), t - 118.9), ("approvals", f"{nap:,}", 9), ("files viewed", viewed + " / 187", 9)):
        col = IVORY
        xr -= txt(frame, val, F(MONOB, 21), col, xr, y2, a, "r") + 10
        xr -= txt(frame, label, F(MONO, 21), DIM, xr, y2, a, "r") + (26 if V else 34)
    ImageDraw.Draw(frame).line([(HX0, 362 if V else 142), (HX1, 362 if V else 142)], fill=tuple(int(BG[i] + (FAINT[i] - BG[i]) * a) for i in range(3)), width=1)

def make_pill(text, col, w):
    def fn(d, s):
        d.rounded_rectangle([1 * s, 1 * s, (w - 1) * s, 33 * s], radius=17 * s, outline=col + (255,), width=int(1.4 * s))
        f = F(INTERB, 19 * s); tw = f.getlength(text)
        d.text(((w * s - tw) / 2, 5 * s), text, font=f, fill=col + (255,))
    return ss(w, 36, fn, 3)
PILL_OPEN = make_pill("Open", GREEN, 78)
PILL_MERGED = make_pill("Merged", IVORY, 98)

# ---- cursor
def build_cursor():
    def fn(d, s):
        pts = [(2, 2), (2, 30), (9, 23), (14, 34), (19, 32), (14, 21), (24, 21)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=IVORY + (255,), outline=BG + (255,))
        d.line([(x * s, y * s) for x, y in pts + [pts[0]]], fill=BG + (255,), width=int(1.6 * s))
    return ss(28, 38, fn, 3)
CURSOR = build_cursor()

# ---- chorus 1: the review dialog
DLG_W, DLG_H = 860, 430
DLG_X, DLG_Y = (W - DLG_W) // 2, (640 if V else 300)
def build_dialog():
    def fn(d, s):
        d.rounded_rectangle([1 * s, 1 * s, (DLG_W - 1) * s, (DLG_H - 1) * s], radius=18 * s, fill=(12, 12, 13, 246), outline=IVORY + (190,), width=int(1.3 * s))
        d.text((36 * s, 26 * s), "Finish your review", font=F(INTERB, 28 * s), fill=IVORY + (255,))
        d.rounded_rectangle([36 * s, 80 * s, (DLG_W - 36) * s, 250 * s], radius=10 * s, outline=FAINT + (255,), width=int(1.2 * s))
        x = 44
        for lab in ("Comment", "Approve", "Request changes"):
            d.ellipse([x * s, 286 * s, (x + 22) * s, 308 * s], outline=DIM + (255,), width=int(1.4 * s))
            d.text(((x + 34) * s, 282 * s), lab, font=F(INTER, 24 * s), fill=IVORY + (255,))
            x += 34 + int(F(INTER, 24).getlength(lab)) + 54
        d.rounded_rectangle([(DLG_W - 256) * s, 346 * s, (DLG_W - 36) * s, 398 * s], radius=26 * s, outline=IVORY + (255,), width=int(1.4 * s))
        f = F(INTERB, 23 * s); tw = f.getlength("Submit review")
        d.text(((DLG_W - 146) * s - tw / 2, 358 * s), "Submit review", font=f, fill=IVORY + (255,))
        d.text((36 * s, 362 * s), "0 of 187 files viewed", font=F(MONO, 20 * s), fill=DIM + (255,))
    return ss(DLG_W, DLG_H, fn, 2)
DIALOG = build_dialog()
APPROVE_XY = (DLG_X + 44 + 34 + int(F(INTER, 24).getlength("Comment")) + 54 + 11, DLG_Y + 297)
SUBMIT_XY = (DLG_X + DLG_W - 146, DLG_Y + 372)
def build_submit_hot():
    def fn(d, s):
        d.rounded_rectangle([0, 0, 220 * s, 52 * s], radius=26 * s, fill=IVORY + (255,))
        f = F(INTERB, 23 * s); tw = f.getlength("Submit review")
        d.text((110 * s - tw / 2, 12 * s), "Submit review", font=f, fill=BG + (255,))
    return ss(220, 52, fn, 2)
SUBMIT_HOT = build_submit_hot()

def dialog_layer(frame, t):
    s1 = STAMPS[0]
    a = seg(t, 0.15, 0.7) * (1 - seg(t, s1 + 0.05, s1 + 0.3))
    if a <= 0.004: return
    paste(frame, DIALOG, DLG_X, DLG_Y, a)
    L0 = CH[0][0]
    f = F(MONOB, 96)
    x = DLG_X + 70
    for i, c in enumerate("LGTM"):
        tau = t - (L0 + i * 0.28)
        if tau >= 0:
            sp = text_sprite(c, f, IVORY)
            paste(frame, sp, x, DLG_Y + 102 - 12 * math.exp(-tau * 16), a * clamp(tau * 16))
            x += f.getlength(c) + 14
    if (t * 1.7) % 1 < 0.55 and t > 0.5:
        ImageDraw.Draw(frame).rectangle([x + 6, DLG_Y + 112, x + 10, DLG_Y + 212], fill=IVORY)
    d = ImageDraw.Draw(frame)
    tap = CH[0][2] + 0.25
    if t >= tap:
        ax, ay = APPROVE_XY
        d.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], fill=GREEN)
    if t >= s1 - 0.12:
        paste(frame, SUBMIT_HOT, SUBMIT_XY[0] - 110, SUBMIT_XY[1] - 26, a)
    # pointer
    p0 = (820, 1340) if V else (1480, 860)
    if t < tap:
        u = ease(seg(t, 7.2, tap)); cxp = p0[0] + (APPROVE_XY[0] - p0[0]) * u; cyp = p0[1] + (APPROVE_XY[1] - p0[1]) * u
    else:
        u = ease(seg(t, tap + 0.5, s1 - 0.25)); cxp = APPROVE_XY[0] + (SUBMIT_XY[0] - APPROVE_XY[0]) * u; cyp = APPROVE_XY[1] + (SUBMIT_XY[1] - APPROVE_XY[1]) * u
    for tc in (tap, s1 - 0.12):
        tau = t - tc
        if 0 <= tau < 0.4:
            r = 8 + 60 * tau
            c = tuple(int(BG[i] + (IVORY[i] - BG[i]) * (1 - tau / 0.4) * 0.8) for i in range(3))
            d.ellipse([cxp - r, cyp - r, cxp + r, cyp + r], outline=c, width=2)
    paste(frame, CURSOR, cxp, cyp, a * seg(t, 6.6, 7.2))

# ---- verse 1 overlays
def chip(text, col=IVORY, font=None, padx=16, h=36, fill=True):
    font = font or F(MONO, 20)
    w = int(font.getlength(text)) + 2 * padx
    def fn(d, s):
        f = F(font.path, font.size * s)
        d.rounded_rectangle([1 * s, 1 * s, (w - 1) * s, (h - 1) * s], radius=(h // 2) * s, fill=(BG + (245,)) if fill else None, outline=col + (255,), width=int(1.4 * s))
        d.text((padx * s, (h * s - (f.getmetrics()[0] + f.getmetrics()[1])) / 2), text, font=f, fill=col + (255,))
    return ss(w, h, fn, 3)
CHIP_BLAME = chip("blame: last touched 14 months ago", IVORY)
CHECKS = ["lint", "build", "unit tests (0 ran)", "integration (skipped)", "vibes"]
def build_ci():
    w, h = 400, 60 + len(CHECKS) * 40
    def fn(d, s):
        d.rounded_rectangle([1 * s, 1 * s, (w - 1) * s, (h - 1) * s], radius=14 * s, fill=(12, 12, 13, 246), outline=IVORY + (170,), width=int(1.3 * s))
        d.text((24 * s, 16 * s), "Checks", font=F(INTERB, 22 * s), fill=IVORY + (255,))
        for i, c in enumerate(CHECKS):
            d.text((62 * s, (56 + i * 40) * s), c, font=F(MONO, 21 * s), fill=IVORY + (255,))
    return ss(w, h, fn, 2), w, h
CI, CI_W, CI_H = build_ci()
def build_tick():
    def fn(d, s):
        d.ellipse([2 * s, 2 * s, 24 * s, 24 * s], outline=GREEN + (255,), width=int(1.6 * s))
        d.line([(7 * s, 13 * s), (11 * s, 17 * s), (19 * s, 8 * s)], fill=GREEN + (255,), width=int(2.2 * s), joint="curve")
    return ss(26, 26, fn, 3)
TICK = build_tick()

def verse1_layer(frame, t):
    # blame chip rides the TEMPORARY line
    a = window(t, 45.0, 47.4, 0.2, 0.3)
    if a > 0:
        y = line_y(_temp, t)
        pop = 1 + 0.0
        paste(frame, CHIP_BLAME, DX0 + X_CODE + CW * 31, y + (LH - 36) // 2 - (1 - eout(seg(t, 44.8, 45.1))) * 8, a)
    a = window(t, 48.5, 52.2, 0.25, 0.4)
    if a > 0:
        x, y = (W - CI_W - 40, 410) if V else (DX0 + DW - CI_W - 20, 176)
        paste(frame, CI, x, y, a)
        for i in range(len(CHECKS)):
            tk = 48.75 + i * 0.3
            if t >= tk:
                paste(frame, TICK, x + 24, y + 56 + i * 40 + 2 - 6 * math.exp(-(t - tk) * 18), a)

# ---- verse 2: the sacred trade
CARD_W, CARD_H = 600, 370
def build_card(num, title, who, stats):
    def fn(d, s):
        d.rounded_rectangle([1 * s, 1 * s, (CARD_W - 1) * s, (CARD_H - 1) * s], radius=18 * s, fill=(12, 12, 13, 250), outline=IVORY + (200,), width=int(1.3 * s))
        d.text((30 * s, 24 * s), num, font=F(MONO, 22 * s), fill=DIM + (255,))
        d.text((30 * s, 54 * s), title, font=F(INTERB, 30 * s), fill=IVORY + (255,))
        d.text((30 * s, 100 * s), who, font=F(INTER, 20 * s), fill=DIM + (255,))
        f = F(MONO, 20 * s); tw = f.getlength(stats)
        d.text(((CARD_W - 30) * s - tw, 26 * s), stats, font=f, fill=DIM + (255,))
        d.line([(30 * s, 140 * s), ((CARD_W - 30) * s, 140 * s)], fill=FAINT + (255,), width=int(1 * s))
    return ss(CARD_W, CARD_H, fn, 2)
CARD_A = build_card("#1111", "misc cleanup (small)", "by you  ·  reviewer: him", "187 files")
CARD_B = build_card("#1112", "quick fix (large)", "by him  ·  reviewer: you", "211 files")
CARDS = [(240, 400), (240, 860)] if V else [(250, 230), (1070, 230)]
CAX, CBX, CY = CARDS[0][0], CARDS[1][0], CARDS[0][1]
MINI_ST = {a: STAMP0.resize((300, 150), Image.LANCZOS).rotate(a, expand=True, resample=Image.BICUBIC) for a in (-8, 7)}
def build_arc(flip):
    w, h = 300, 150
    def fn(d, s):
        pts = []
        for i in range(41):
            u = i / 40; x = 20 + 260 * u; y = 120 - 96 * math.sin(math.pi * u)
            pts.append((x * s, y * s))
        if flip: pts = [((w * s - x), (h * s - y)) for x, y in pts]
        d.line(pts, fill=IVORY + (255,), width=int(1.8 * s), joint="curve")
        (x1, y1), (x0, y0) = pts[-1], pts[-4]
        ang = math.atan2(y1 - y0, x1 - x0)
        for da in (2.6, -2.6):
            d.line([(x1, y1), (x1 + 20 * s * math.cos(ang + da), y1 + 20 * s * math.sin(ang + da))], fill=IVORY + (255,), width=int(1.8 * s))
    return ss(w, h, fn, 3)
ARC_TOP, ARC_BOT = build_arc(True), build_arc(False)
if V: ARC_TOP, ARC_BOT = ARC_TOP.rotate(-90, expand=True), ARC_BOT.rotate(-90, expand=True)   # top: right->left (he reviews mine); bottom: left->right
THU = chip("Thursday", IVORY, F(MONOB, 22), 20, 42)
_cr = random.Random(5)
CARD_BARS = [[(_cr.choice([0, 0, 24, 48]), _cr.randint(120, 480), _cr.choice("gri" + "i")) for _ in range(7)] for _ in range(2)]

def verse2_layer(frame, t):
    a = seg(t, 88.9, 89.9) * (1 - seg(t, 104.2, 105.0))
    if a <= 0.004: return
    d = ImageDraw.Draw(frame)
    unknown = seg(t, 95.4, 96.4)
    for ci, card in enumerate((CARD_A, CARD_B)):
        x, CY = CARDS[ci]
        slide = (1 - eout(seg(t, 88.9 + ci * 0.15, 90.0 + ci * 0.15))) * 60
        paste(frame, card, x, CY + slide, a)
        if a > 0.5:
            jr = random.Random(int(t * 8) * 7 + ci) if unknown > 0 and t < 99.6 else None
            for j, (ind, ln, c) in enumerate(CARD_BARS[ci]):
                if jr: ln = jr.randint(60, 500); ind = jr.choice([0, 24, 48])
                col = {"g": (40, 96, 64), "r": (104, 44, 48), "i": (62, 60, 56)}[c]
                if unknown > 0: col = tuple(int(col[k] + ((52, 51, 48)[k] - col[k]) * unknown) for k in range(3))
                yy = CY + slide + 164 + j * 26
                d.rounded_rectangle([x + 30 + ind, yy, x + 30 + ind + ln, yy + 12], radius=6, fill=col)
    # the trade
    mx = W / 2
    CY = CARDS[0][1]
    gy = (CARDS[0][1] + CARD_H + CARDS[1][1]) / 2
    if t >= 90.9:
        paste(frame, THU, mx - THU.width / 2, (gy - 21) if V else (CY - 62), a * seg(t, 90.9, 91.2))
    u = seg(t, 91.2, 92.1)
    if u > 0:
        if V:
            hh = ARC_TOP.height
            sp = ARC_TOP.crop((0, int(hh * (1 - u)), ARC_TOP.width, hh))
            paste(frame, sp, 70, gy - hh / 2 + int(hh * (1 - u)), a)
        else:
            sp = ARC_TOP.crop((int(ARC_TOP.width * (1 - u)), 0, ARC_TOP.width, ARC_TOP.height))
            paste(frame, sp, mx - 150 + int(ARC_TOP.width * (1 - u)), CY + 30, a)
    u = seg(t, 92.7, 93.6)
    if u > 0:
        if V:
            hh = ARC_BOT.height
            paste(frame, ARC_BOT.crop((0, 0, ARC_BOT.width, int(hh * u))), 860, gy - hh / 2, a)
        else:
            sp = ARC_BOT.crop((0, 0, int(ARC_BOT.width * u), ARC_BOT.height))
            paste(frame, sp, mx - 150, CY + 190, a)
    for ts, cidx, ang in ((92.3, 0, -8), (93.9, 1, 7)):
        tau = t - ts
        if tau >= 0:
            sp = MINI_ST[ang]; sc = 1 + 1.6 * math.exp(-tau * 22)
            if sc > 1.01: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
            paste_c(frame, sp, CARDS[cidx][0] + CARD_W / 2, CARDS[cidx][1] + 250, a * clamp(tau * 16))
    # covenant / promise / sacred trade
    WORDS = (("COVENANT", 100.0, 470, 101.0), ("PROMISE", 101.0, 960, 102.0), ("SACRED TRADE", 102.0, 1450, 104.0))
    for word, tw, x, tend in WORDS:
        wa = seg(t, tw, tw + 0.25) * (1 - seg(t, 104.0, 104.6))
        wy = 690
        if V:
            x, wy = CX, 1248
            wa = seg(t, tw, tw + 0.2) * (1 - seg(t, tend - 0.12, tend + (0.5 if tend > 103 else 0.0) + 0.02))
        if wa > 0:
            f = F(CINZ, 52)
            sp = text_sprite(word, f, IVORY, 8)
            paste(frame, sp, x - sp.width / 2, wy + (1 - eout(wa)) * 14, a * wa)
            d.line([(x - 120, wy + 74), (x + 120, wy + 74)], fill=tuple(int(BG[i] + (DIM[i] - BG[i]) * wa * a) for i in range(3)), width=1)

# ---- verse 3: one nit
ZN = 1.0 if V else 1.5
NIT_T0, NIT_T1 = 112.4, 114.6        # zoom in
NIT_OUT0, NIT_OUT1 = 131.2, 132.6    # zoom out
ZCX, ZCY = 360.0, 497.0
NIT_LY = (DY0 + ANCH) if V else 472
def nit_zoom(t):
    return 1 + (ZN - 1) * (ease(seg(t, NIT_T0, NIT_T1)) - ease(seg(t, NIT_OUT0, NIT_OUT1)))
def nit_spot(t):
    return ease(seg(t, NIT_T0, NIT_T1)) - ease(seg(t, NIT_OUT0, NIT_OUT1))
CM_W, CM_H = 900, 150
def build_comment():
    def fn(d, s):
        d.rounded_rectangle([1 * s, 1 * s, (CM_W - 1) * s, (CM_H - 1) * s], radius=16 * s, fill=(12, 12, 13, 250), outline=IVORY + (220,), width=int(1.4 * s))
        d.ellipse([26 * s, 24 * s, 70 * s, 68 * s], outline=IVORY + (255,), width=int(1.4 * s))
        f = F(INTERB, 24 * s); d.text((48 * s - f.getlength("a") / 2, 30 * s), "a", font=f, fill=IVORY + (255,))
        d.text((88 * s, 22 * s), "aditazzz", font=F(INTERB, 24 * s), fill=IVORY + (255,))
        d.text((88 * s + F(INTERB, 24 * s).getlength("aditazzz") + 14 * s, 26 * s), "commented on line 400", font=F(INTER, 21 * s), fill=DIM + (255,))
    return ss(CM_W, CM_H, fn, 2)
COMMENT = build_comment()
NIT_TEXT = "nit: rename tmp2 -> tmp_2 ?"
def build_heart():
    def fn(d, s):
        pts = []
        for i in range(81):
            a = 2 * math.pi * i / 80
            x = 16 * math.sin(a) ** 3; y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
            pts.append(((30 + x * 1.5) * s, (28 + y * 1.5) * s))
        d.line(pts, fill=RED + (255,), width=int(2.2 * s), joint="curve")
    return ss(60, 60, fn, 3)
HEART = build_heart()
CHIP_THERE = chip("   reviewed", GREEN, F(MONOB, 22), 18, 42)

def nit_layer(frame, t):
    a = seg(t, 114.3, 114.9) * (1 - seg(t, 131.0, 131.5))
    if a <= 0.004: return
    d = ImageDraw.Draw(frame)
    ly = NIT_LY
    lh = int(LH * ZN)
    # ring around the line number 400
    pul = seg(t, 119.4, 119.7) * (1 - seg(t, 121.6, 122.2))
    nx0, nx1 = (30, 82) if V else (120 + int(96 * ZN), 120 + int(150 * ZN))
    col = tuple(int(BG[i] + (IVORY[i] - BG[i]) * a * (0.55 + 0.45 * pul)) for i in range(3))
    d.rounded_rectangle([nx0 - 4 - 5 * pul, ly - 3 - 5 * pul, nx1 + 4 + 5 * pul, ly + lh + 1 + 5 * pul], radius=10, outline=col, width=2)
    cx, cy = (90 if V else 400), ly + lh * 5 + 14
    ca = seg(t, 115.2, 115.7)
    paste(frame, COMMENT, cx, cy + (1 - eout(ca)) * 16, a * ca)
    n = int(len(NIT_TEXT) * seg(t, 116.5, 118.9))
    if n > 0:
        f = F(MONO, 34)
        txt(frame, NIT_TEXT[:n], f, IVORY, cx + 84, cy + 78, a)
        if n < len(NIT_TEXT):
            xx = cx + 88 + f.getlength(NIT_TEXT[:n])
            d.rectangle([xx + 4, cy + 82, xx + 7, cy + 122], fill=IVORY)
    ta = seg(t, 123.2, 123.5)
    if ta > 0:
        yy = cy + 22 - (1 - eout(ta)) * 8
        paste(frame, CHIP_THERE, cx + CM_W - CHIP_THERE.width - 24, yy, a * ta)
        paste(frame, TICK, cx + CM_W - CHIP_THERE.width - 24 + 14, yy + 8, a * ta)
    ha = seg(t, 128.6, 129.0)
    if ha > 0:
        sc = 1 + 0.5 * math.exp(-(t - 128.6) * 9)
        sp = HEART if sc < 1.02 else HEART.resize((int(60 * sc), int(60 * sc)), Image.BILINEAR)
        paste_c(frame, sp, (cx + CM_W - 70) if V else (cx + CM_W + 62), (cy + CM_H + 56) if V else (cy + CM_H / 2), a * ha)

# ---- outro
def build_merge_btn(hot):
    w, h = 420, 76
    def fn(d, s):
        d.rounded_rectangle([1 * s, 1 * s, (w - 1) * s, (h - 1) * s], radius=38 * s, fill=(IVORY + (255,)) if hot else (12, 12, 13, 250), outline=IVORY + (255,), width=int(1.5 * s))
        f = F(INTERB, 30 * s); tw = f.getlength("Merge pull request")
        d.text(((w * s - tw) / 2, 18 * s), "Merge pull request", font=f, fill=(BG if hot else IVORY) + (255,))
    return ss(w, h, fn, 2)
MERGE, MERGE_HOT = build_merge_btn(False), build_merge_btn(True)
T_MERGE = snap(167.6)
ALERTS = [(170.6, "FIRING", "auth-service: everyone is logged in as admin"), (171.7, "FIRING", "db-primary: table “users” does not exist"),
          (172.8, "FIRING", "billing: refunds issued to all customers, twice"), (173.9, "PAGE", "on-call is you. It is Friday.")]
def build_alert(kind, msg):
    w, h = 760, 64
    def fn(d, s):
        d.rounded_rectangle([1 * s, 1 * s, (w - 1) * s, (h - 1) * s], radius=12 * s, fill=(14, 10, 11, 250), outline=RED + (255,), width=int(1.4 * s))
        d.ellipse([22 * s, 24 * s, 38 * s, 40 * s], fill=RED + (255,))
        d.text((54 * s, 18 * s), kind, font=F(MONOB, 21 * s), fill=RED + (255,))
        d.text((54 * s + F(MONOB, 21 * s).getlength(kind) + 16 * s, 17 * s), msg, font=F(INTER, 22 * s), fill=IVORY + (255,))
    return ss(w, h, fn, 2)
ALERT_SP = [build_alert(k, m) for _, k, m in ALERTS]
REVERT = build_card("#1112", "Revert “misc cleanup (small)”", "by aditazzz  ·  reviewer: him", "187 files")
T_REV, T_REVST = 174.4, snap(175.6)
REV_ST = STAMP0.resize((340, 170), Image.LANCZOS).rotate(-8, expand=True, resample=Image.BICUBIC)

def outro_layer(frame, t):
    if t < 166.4: return
    out = 1 - seg(t, 177.0, 177.9)
    # merge button -> Merged.
    ba = seg(t, 166.6, 167.2) * (1 - seg(t, T_MERGE + 0.25, T_MERGE + 0.5))
    if ba > 0:
        paste_c(frame, MERGE_HOT if t >= T_MERGE - 0.05 else MERGE, *((CX, 760) if V else (620, 430)), ba)
        u = ease(seg(t, 166.7, T_MERGE - 0.1))
        c0, c1 = ((820, 1300), (570, 770)) if V else ((1200, 760), (650, 440))
        paste(frame, CURSOR, c0[0] + (c1[0] - c0[0]) * u, c0[1] + (c1[1] - c0[1]) * u, ba)
    ma = seg(t, T_MERGE + 0.3, T_MERGE + 0.7) * out
    if ma > 0:
        mxy = (70, 420) if V else (200, 330)
        txt(frame, "Merged.", F(CORM, 150), IVORY, mxy[0], mxy[1], ma)
        txt(frame, f"187 files  ·  0 viewed  ·  {N_FINAL} approvals", F(MONO, 24), DIM, mxy[0] + 8, mxy[1] + 190, ma)
    for i, (ta, _, _) in enumerate(ALERTS):
        tau = t - ta
        if tau >= 0:
            paste(frame, ALERT_SP[i], (160 if V else 960) + (1 - eout(seg(tau, 0, 0.3))) * 120, (720 if V else 196) + i * 78, clamp(tau * 6) * out)
    ra = seg(t, T_REV, T_REV + 0.4) * out
    if ra > 0:
        rx, ry = (240, 1070) if V else (200, 610)
        paste(frame, REVERT, rx, ry + (1 - eout(ra)) * 30, ra * 0.999)
        d = ImageDraw.Draw(frame)
        for j, (ind, ln, c) in enumerate(CARD_BARS[0][:6]):
            col = {"g": (104, 44, 48), "r": (40, 96, 64), "i": (62, 60, 56)}[c]
            col = tuple(int(BG[k] + (col[k] - BG[k]) * ra) for k in range(3))
            yy = ry + 164 + j * 26 + (1 - eout(ra)) * 30
            d.rounded_rectangle([rx + 30 + ind, yy, rx + 30 + ind + ln, yy + 12], radius=6, fill=col)
        tau = t - T_REVST
        if tau >= 0:
            sp = REV_ST; sc = 1 + 1.6 * math.exp(-tau * 22)
            if sc > 1.01: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
            paste_c(frame, sp, rx + CARD_W / 2 + 40, ry + 240, out * clamp(tau * 16))
    ea = seg(t, 177.7, 178.5)
    if ea > 0:
        f = F(CINZB, 190)
        sp = text_sprite("LGTM", f, IVORY, 26)
        ey = 740 if V else 370
        paste(frame, sp, (W - sp.width) / 2 + 13, ey, ea)
        txt(frame, "aditazzz", F(MONO, 30), DIM, W / 2, ey + 240, ea, "c", 8)
        txt(frame, "no lines were read in the making of this video", F(CORMI, 34), DIM, W / 2, ey + 310, ea * seg(t, 178.3, 179.0), "c")

# ------------------------------------------------------------------ frame
def shake_of(t):
    dx = dy = 0.0; fl = 0.0
    for i, s in enumerate(STAMPS):
        tau = t - s
        if 0 <= tau < 0.45:
            amp = (10 + 4 * (i >= 4)) * math.exp(-tau * 9)
            dx += amp * math.sin(tau * 71 + i); dy += amp * math.cos(tau * 83 + 2 * i)
            fl = max(fl, 0.16 * math.exp(-tau * 16))
    for ci, (l, lk, idd) in enumerate(CH):
        if ci == 0: continue
        for i in range(4):
            tau = t - (l + i * 0.28)
            if 0 <= tau < 0.25:
                amp = 5 * math.exp(-tau * 14); dx += amp * math.sin(tau * 90 + i); dy += amp * math.cos(tau * 77 + i)
    return dx, dy, fl

WINK = [(0, 0), (16.4, 0), (17.0, 1), (33.4, 1), (34.4, 0), (55.4, 0), (56.6, 1), (88.3, 1), (89.2, 0), (132.0, 0), (133.6, 1), (166.2, 1), (167.0, 0), (181, 0)]
WINP = [(0, 0), (19.0, 0.0), (33.0, 0.30), (56.7, 0.30), (72.0, 0.66), (74.4, 0.66), (86.4, 1.0), (181, 1.0)]
LEADW = [(0, 0), (16.6, 0), (19.2, 1), (181, 1)]
CHOIRK = [(0, 0), (56.2, 0), (58.6, 1), (88.2, 1), (89.0, 0), (132.6, 0), (134.6, 1), (166.0, 1), (166.8, 0), (181, 0)]
HEADK = [(0, 0), (0.2, 0), (0.9, 1), (176.9, 1), (177.7, 0), (181, 0)]

def render(t):
    frame = Image.new("RGB", (W, H), BG)
    dim = kf(t, DIMK)
    z = nit_zoom(t)
    if dim > 0.004:
        if (not V) and z >= ZN - 1e-4:
            arr = diff_layer(t, dim, z=ZN, y_anchor=NIT_LY)
            frame.paste(Image.fromarray(arr[:, :W - 120]), (120, 0))
        else:
            frame.paste(Image.fromarray(diff_layer(t, dim)), (DX0, DY0))
            if z > 1.001:
                bw, bh = W / z, H / z
                x0, y0 = ZCX - ZCX / z, ZCY - ZCY / z
                frame = frame.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + bw, y0 + bh))
    sa = nit_spot(t)
    if sa > 0.004:
        paste(frame, SPOT, 0, 0, sa)
    # chorus world
    wa = kf(t, WINK)
    if wa > 0.004:
        p = kf(t, WINP)
        bi, bp = beat_info(t)
        late = t > 132
        glow = wa * (p ** 1.5) * (0.30 + 0.5 * env(t) + 0.35 * bp) * (1.25 if late else 0.9)
        if late:
            add_light(frame, RAYS, 0, 0, wa * (0.55 + 0.6 * env(t) + 0.3 * bp))
        window_layer(frame, t, wa, p, kf(t, LEADW), glow)
    choir_layer(frame, t, kf(t, CHOIRK))
    # mini stamp rain
    if 134 < t < 167.2:
        ra = 1 - seg(t, 166.2, 167.0)
        for tb, x, y, ang in RAIN:
            tau = t - tb
            if tau < 0: break
            sp = MINI[ang]; sc = 1 + 1.4 * math.exp(-tau * 22)
            if sc > 1.02: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
            paste_c(frame, sp, x, y, ra * clamp(tau * 16) * (0.34 + 0.66 * math.exp(-tau * 1.6)))
    letters_layer(frame, t)
    verse1_layer(frame, t)
    verse2_layer(frame, t)
    nit_layer(frame, t)
    paste(frame, SCRIM, 0, 0, 1.0 if t < 166.3 else 1 - seg(t, 166.3, 167.2))
    if z < 1.2: header(frame, t, kf(t, HEADK) * (1 - seg(z, 1.0, 1.2)))
    if t < STAMPS[0] + 0.4: dialog_layer(frame, t)
    for i, s in enumerate(STAMPS):
        stamp_layer(frame, t - s, CX, ((760 if i else 850) if V else (500 if i else 520)), STAMP_ANG[i], hold=1.6 if i < 5 else 2.0)
    caption(frame, t)
    outro_layer(frame, t)
    dx, dy, fl = shake_of(t)
    if abs(dx) > 0.5 or abs(dy) > 0.5:
        f2 = Image.new("RGB", (W, H), BG); f2.paste(frame, (int(dx), int(dy))); frame = f2
    if fl > 0.004:
        frame = Image.blend(frame, Image.new("RGB", (W, H), IVORY), fl)
    if t > 179.3:
        frame = Image.blend(frame, Image.new("RGB", (W, H), BG), seg(t, 179.3, 179.9))
    return frame

def main():
    if sys.argv[1] == "still":
        for ts in sys.argv[2:]:
            t = float(ts); render(t).save(f"{HERE}/stills/{'v' if V else 's'}_{t:07.2f}.png")
        return
    if sys.argv[1] == "seg":
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-g", "30", out], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            p.stdin.write(render(f / FPS).tobytes())
            if f % 150 == 0: print(f, flush=True)
        p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
