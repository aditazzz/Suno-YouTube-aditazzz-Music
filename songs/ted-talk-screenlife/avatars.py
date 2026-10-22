"""The people in the video tiles: flat, front-facing illustrations in their home offices.

A person is drawn in "head units" (the head is 2 wide), placed in a tile measured in tile units (160 x 90, i.e. 16:9).
State per frame: blink, mouth (0 closed .. 1 wide open), smile, brows, gaze, head tilt and position, hands."""
import math
import numpy as np
import ui as U
from ui import smooth, ellipse

F32 = np.float32
def H(h): return U.hexc(h)
def mix(a, b, k): return np.asarray(a, F32) * (1 - k) + np.asarray(b, F32) * k
def dark(c, k=0.82): return np.asarray(c, F32) * k

HEAD = smooth([(0, -1.28), (0.62, -1.19), (0.95, -0.74), (1.02, -0.12), (0.96, 0.38), (0.80, 0.78), (0.45, 1.07), (0, 1.16),
               (-0.45, 1.07), (-0.80, 0.78), (-0.96, 0.38), (-1.02, -0.12), (-0.95, -0.74), (-0.62, -1.19)], 6)
SHADE = smooth([(0.30, -1.22), (0.75, -0.98), (1.0, -0.40), (0.99, 0.20), (0.86, 0.66), (0.50, 1.04), (0.10, 1.16), (0.42, 0.78),
                (0.66, 0.30), (0.74, -0.25), (0.62, -0.80)], 5)
TORSO = smooth([(-0.40, 1.42), (-1.25, 1.60), (-2.15, 1.92), (-2.62, 2.45), (-2.80, 3.5), (-2.86, 5.2), (-2.6, 6.6), (2.6, 6.6), (2.86, 5.2),
                (2.80, 3.5), (2.62, 2.45), (2.15, 1.92), (1.25, 1.60), (0.40, 1.42)], 5)

HAIR = {
    "swoop": ([], smooth([(-0.98, -0.18), (-1.04, -0.78), (-0.78, -1.22), (-0.22, -1.52), (0.45, -1.66), (0.98, -1.50), (1.15, -1.08),
                          (1.04, -0.48), (0.93, -0.14), (0.82, -0.62), (0.48, -0.95), (-0.02, -0.90), (-0.52, -0.84), (-0.84, -0.58)], 5)),
    "bob": (smooth([(-1.28, 0.98), (-1.37, 0.12), (-1.24, -0.86), (-0.74, -1.42), (0, -1.52), (0.74, -1.42), (1.24, -0.86), (1.37, 0.12),
                    (1.28, 0.98), (0.0, 1.02)], 5),
            smooth([(-0.99, -0.26), (-1.02, -0.86), (-0.64, -1.32), (0, -1.43), (0.64, -1.32), (1.02, -0.86), (0.99, -0.26), (0.66, -0.42),
                    (0.22, -0.39), (-0.22, -0.43), (-0.64, -0.40)], 5)),
    "pony": (smooth([(0.82, -0.95), (1.28, -0.72), (1.46, 0.0), (1.40, 0.92), (1.18, 1.55), (1.04, 0.92), (1.08, 0.12), (0.96, -0.50)], 5),
             smooth([(-0.97, -0.16), (-1.01, -0.80), (-0.62, -1.31), (0, -1.43), (0.62, -1.31), (1.01, -0.80), (0.97, -0.16), (0.80, -0.76),
                     (0.30, -0.97), (-0.30, -0.97), (-0.80, -0.76)], 5)),
    "long": (smooth([(-1.18, 2.45), (-1.38, 1.0), (-1.32, -0.2), (-1.16, -0.96), (-0.66, -1.41), (0, -1.50), (0.66, -1.41), (1.16, -0.96),
                     (1.32, -0.2), (1.38, 1.0), (1.18, 2.45), (0.0, 2.2)], 5),
             None),
    "short": ([], smooth([(-0.97, -0.24), (-1.01, -0.86), (-0.66, -1.33), (0, -1.46), (0.66, -1.33), (1.01, -0.86), (0.97, -0.24),
                          (0.84, -0.70), (0.42, -0.88), (-0.08, -0.84), (-0.56, -0.80), (-0.86, -0.64)], 5)),
    "buzz": ([], smooth([(-0.96, -0.40), (-0.99, -0.90), (-0.62, -1.30), (0, -1.38), (0.62, -1.30), (0.99, -0.90), (0.96, -0.40),
                         (0.70, -0.98), (0, -1.08), (-0.70, -0.98)], 5)),
    "bun": ([], smooth([(-0.97, -0.16), (-1.01, -0.80), (-0.62, -1.31), (0, -1.43), (0.62, -1.31), (1.01, -0.80), (0.97, -0.16), (0.80, -0.76),
                        (0.30, -0.97), (-0.30, -0.97), (-0.80, -0.76)], 5)),
    "curly": ([], None),
}

PEOPLE = {
    "Ted":    dict(skin="e9b896", hair="swoop", hair_c="3a2a20", shirt="1c1c1f", top="turtleneck", acc=("headset",), brow=1.2),
    "Me":     dict(skin="f0c8a8", hair="bob", hair_c="2a1d18", shirt="7c8b6a", top="cardigan", inner="efe6d6", acc=("clip",), brow=1.0),
    "Dana":   dict(skin="f3d3bd", hair="pony", hair_c="9a4a2a", shirt="d98c7a", top="vneck", acc=(), brow=0.9),
    "Priya":  dict(skin="b98262", hair="long", hair_c="1a1412", shirt="e7c75a", top="crew", acc=("earrings",), brow=1.1),
    "Marcus": dict(skin="7a4f36", hair="curly", hair_c="1d1714", shirt="4a5d78", top="hoodie", acc=("headphones",), brow=1.1),
    "Sam":    dict(skin="f1cdb0", hair="short", hair_c="8a6a4a", shirt="5e8f74", top="crew", acc=("glasses",), brow=1.0),
    "Lee":    dict(skin="d9a77f", hair="buzz", hair_c="2e2a28", shirt="3b4150", top="blazer", inner="f2f2ee", acc=(), brow=1.0),
    "Jo":     dict(skin="f6dcc6", hair="bun", hair_c="d8b26a", shirt="a8b8d8", top="cardigan", inner="f4f0e6", acc=(), brow=0.9),
}
for p in PEOPLE.values():
    for k in ("skin", "hair_c", "shirt", "inner"):
        if k in p: p[k] = H(p[k])

class St:
    """per-frame state of a person"""
    def __init__(self, **k):
        self.cx, self.cy, self.s = 80.0, 40.0, 10.0          # head centre and half-width, tile units
        self.tilt = 0.0; self.blink = 0.0; self.mouth = 0.0; self.smile = 0.25; self.brow = 0.0; self.gaze = (0.0, 0.0)
        self.body = False; self.hands = None              # hands: list of (side, shoulder angle, elbow angle) for raised arms
        self.eyes_closed = 0.0; self.lean = 0.0
        for a, b in k.items(): setattr(self, a, b)

def blink_at(t, seed):
    """a natural blink every few seconds"""
    period = 3.1 + (seed * 0.7) % 1.9
    ph = (t + seed * 1.37) % period
    return max(0.0, 1 - abs(ph - 0.08) / 0.08) if ph < 0.16 else 0.0

# ---------------------------------------------------------------- drawing a person into a tile
def draw(img, cam, tile, name, st, t):
    """tile = (x, y, w, h) in desktop units"""
    p = PEOPLE[name]
    x, y, w, h = tile; k = w / 160.0
    S = st.s; ca, sa = math.cos(st.tilt), math.sin(st.tilt)
    def Hd(P):      # head units -> desktop (with the head tilt)
        P = np.asarray(P, float)
        X = P[:, 0] * ca - P[:, 1] * sa; Y = P[:, 0] * sa + P[:, 1] * ca
        return np.stack([x + (st.cx + X * S) * k, y + (st.cy + Y * S) * k], 1)
    def Bd(P):      # body units (no tilt) -> desktop
        P = np.asarray(P, float)
        return np.stack([x + (st.cx + (P[:, 0] + st.lean * (P[:, 1] - 6) * -0.0) * S) * k, y + (st.cy + P[:, 1] * S) * k], 1)
    skin = p["skin"]; hair_c = p["hair_c"]; shirt = p["shirt"]
    # ---------------- body
    if st.body:   # full figure (Ted, stepped back): legs, shoes
        legs = [smooth([(-1.45, 5.1), (-0.15, 5.1), (-0.25, 9.4), (-1.15, 9.4)], 3), smooth([(0.15, 5.1), (1.45, 5.1), (1.15, 9.4), (0.25, 9.4)], 3)]
        U.poly(img, cam, [Bd(l) for l in legs], H("2b2e36"))
        U.poly(img, cam, [Bd(ellipse(-0.75, 9.6, 0.75, 0.32, n=20)), Bd(ellipse(0.75, 9.6, 0.75, 0.32, n=20))], H("141416"))
        tor = smooth([(-0.40, 1.42), (-1.25, 1.60), (-2.10, 1.92), (-2.45, 2.45), (-2.30, 3.5), (-1.85, 4.6), (-1.55, 5.4), (1.55, 5.4), (1.85, 4.6),
                      (2.30, 3.5), (2.45, 2.45), (2.10, 1.92), (1.25, 1.60), (0.40, 1.42)], 5)
    else:
        tor = TORSO
    # arms behind the torso when they hang (full body) / out of frame when close
    arms = []
    if st.body:
        hs = st.hands or [(-1, 0.18, 0.25), (1, 0.18, 0.25)]
        for side, sh, el in hs:
            s0 = np.array([side * 2.05, 2.15]); a = -side * sh
            e = s0 + np.array([side * math.sin(abs(sh)) * 1.65 * (1 if sh >= 0 else 1), math.cos(sh) * 1.65])
            e = s0 + np.array([math.sin(-a) * 1.65 * -1 * side * side, math.cos(a) * 1.65]) if False else s0 + np.array([side * math.sin(sh) * 1.65, math.cos(sh) * 1.65])
            wv = e + np.array([side * math.sin(sh + el) * 1.55, math.cos(sh + el) * 1.55])
            arms.append((s0, e, wv))
            U.poly(img, cam, [Bd(U.smooth(np.vstack([_limb(s0, e, wv, 0.42, 0.34)]), 3))], dark(shirt, 0.92))
    U.poly(img, cam, [Bd(tor)], shirt)
    top = p.get("top")
    neck = Bd(smooth([(-0.36, 0.70), (0.36, 0.70), (0.38, 1.62), (-0.38, 1.62)], 2))
    U.poly(img, cam, [neck], dark(skin, 0.86))
    if top == "turtleneck":
        U.poly(img, cam, [Bd(U.rr_pts(-0.52, 1.10, 0.52, 1.80, 0.18))], mix(shirt, (1, 1, 1), 0.06))
        U.stroke(img, cam, Bd([(-0.48, 1.35), (0.48, 1.35)]), 0.03 * S * k, dark(shirt, 0.6))
        U.stroke(img, cam, Bd([(-0.48, 1.55), (0.48, 1.55)]), 0.03 * S * k, dark(shirt, 0.6))
    elif top == "vneck":
        U.poly(img, cam, [Bd([(-0.46, 1.44), (0, 2.25), (0.46, 1.44)])], dark(skin, 0.9))
    elif top == "crew":
        U.stroke(img, cam, Bd([(-0.62, 1.5), (0, 1.78), (0.62, 1.5)]), 0.10 * S * k, dark(shirt, 0.82))
    elif top == "hoodie":
        U.poly(img, cam, [Bd(smooth([(-1.25, 1.55), (-0.95, 1.20), (0, 1.32), (0.95, 1.20), (1.25, 1.55), (0.62, 1.80), (0, 1.86), (-0.62, 1.80)], 4))], dark(shirt, 0.82))
        for dx in (-0.32, 0.32): U.stroke(img, cam, Bd([(dx, 1.8), (dx * 1.1, 3.0)]), 0.06 * S * k, (0.92, 0.92, 0.9))
    elif top in ("blazer", "cardigan"):
        inner = p.get("inner", (0.95, 0.95, 0.95))
        U.poly(img, cam, [Bd([(-0.55, 1.46), (0.55, 1.46), (0.42, 6.6), (-0.42, 6.6)])], inner)
        lap = dark(shirt, 0.78) if top == "blazer" else dark(shirt, 0.9)
        U.poly(img, cam, [Bd([(-0.55, 1.46), (-0.95, 1.60), (-0.62, 3.2), (-0.30, 5.2), (-0.46, 6.6), (-0.10, 6.6)]),
                          Bd([(0.55, 1.46), (0.95, 1.60), (0.62, 3.2), (0.30, 5.2), (0.46, 6.6), (0.10, 6.6)])], lap)
        if top == "cardigan":
            for i in range(3): U.poly(img, cam, [Bd(ellipse(0.42, 3.0 + i * 0.85, 0.07, 0.07, n=10))], dark(shirt, 0.6))
    if "headphones" in p["acc"]:
        U.stroke(img, cam, Bd(smooth([(-1.05, 1.75), (-0.8, 2.25), (0, 2.42), (0.8, 2.25), (1.05, 1.75)], 4, closed=False)), 0.16 * S * k, H("1a1a1c"))
        for sx in (-1, 1): U.poly(img, cam, [Bd(ellipse(sx * 1.05, 1.75, 0.30, 0.38, n=18))], H("232326"))
    # ---------------- head
    back, front = HAIR.get(p["hair"], ([], None))
    if p["hair"] == "pony" and len(back): U.poly(img, cam, [Hd(back)], dark(hair_c, 0.85))
    elif len(back): U.poly(img, cam, [Hd(back)], dark(hair_c, 0.92))
    if p["hair"] == "bun": U.poly(img, cam, [Hd(ellipse(0.12, -1.62, 0.46, 0.40, n=24))], hair_c)
    for sx in (-1, 1): U.poly(img, cam, [Hd(ellipse(sx * 0.99, 0.08, 0.17, 0.27, n=16))], dark(skin, 0.93))
    U.poly(img, cam, [Hd(HEAD)], skin)
    U.poly(img, cam, [Hd(SHADE)], dark(skin, 0.94), 0.9)
    if "earrings" in p["acc"]:
        for sx in (-1, 1): U.poly(img, cam, [Hd(ellipse(sx * 1.0, 0.42, 0.07, 0.07, n=10))], H("e8c25a"))
    # cheeks
    for sx in (-1, 1): U.poly(img, cam, [Hd(ellipse(sx * 0.55, 0.42, 0.20, 0.12, n=16))], mix(skin, H("e48a7a"), 0.35), 0.45)
    # eyes
    gx, gy = st.gaze
    shut = max(st.blink, st.eyes_closed)
    for sx in (-1, 1):
        ex, ey = sx * 0.38 + gx * 0.06, 0.02 + gy * 0.05
        if shut > 0.6:
            U.stroke(img, cam, Hd([(ex - 0.13, ey + 0.02), (ex, ey + 0.06), (ex + 0.13, ey + 0.02)]), 0.055 * S * k, H("2a2220"))
        else:
            ry = 0.13 * (1 - shut)
            U.poly(img, cam, [Hd(ellipse(ex, ey, 0.105, max(0.02, ry), n=18))], H("2a2220"))
            U.poly(img, cam, [Hd(ellipse(ex + 0.035, ey - 0.045, 0.03, 0.03, n=8))], (1, 1, 1), 0.85)
    # brows
    b = st.brow; bt = 0.065 * p.get("brow", 1.0)
    for sx in (-1, 1):
        inner_y = -0.30 - 0.10 * b + (0.06 if b < 0 else 0) * -b
        P = [(sx * 0.18, inner_y + (0.04 * -b if b < 0 else 0)), (sx * 0.38, -0.34 - 0.10 * b), (sx * 0.58, -0.30 - 0.06 * b)]
        U.stroke(img, cam, Hd(P), bt * 2 * S * k, dark(hair_c, 0.9))
    # nose
    U.stroke(img, cam, Hd(smooth([(0.04, 0.10), (0.08, 0.32), (-0.02, 0.40)], 4, closed=False)), 0.05 * S * k, dark(skin, 0.80))
    # mouth
    mo = st.mouth
    if mo > 0.06:
        mw, mh = 0.22 + 0.04 * mo, 0.05 + 0.20 * mo
        U.poly(img, cam, [Hd(ellipse(0, 0.66 + mh * 0.25, mw, mh, n=24))], H("5c2b2b"))
        U.poly(img, cam, [Hd(ellipse(0, 0.66 + mh * 0.25 + mh * 0.45, mw * 0.6, mh * 0.35, n=16))], H("b85a5a"), 0.8)
    else:
        sm = st.smile
        U.stroke(img, cam, Hd(smooth([(-0.24, 0.63 - 0.05 * sm), (0, 0.66 + 0.07 * sm), (0.24, 0.63 - 0.05 * sm)], 4, closed=False)), 0.055 * S * k, H("8a4a44"))
    # hair in front
    if p["hair"] == "curly":
        for i, a in enumerate(np.linspace(math.pi * 0.95, math.pi * 2.05, 13)):
            r = 0.34 + 0.05 * math.sin(i * 2.3)
            U.poly(img, cam, [Hd(ellipse(math.cos(a) * 0.98, -0.45 + math.sin(a) * 0.95, r, r, n=14))], hair_c)
        U.poly(img, cam, [Hd(ellipse(0, -0.95, 0.85, 0.42, n=24))], hair_c)
    elif p["hair"] == "long":
        for sx in (-1, 1):
            P = [(0, -1.43), (sx * 0.55, -1.27), (sx * 0.96, -0.76), (sx * 1.04, 0.1), (sx * 0.98, 0.72), (sx * 0.82, 0.18), (sx * 0.64, -0.60), (sx * 0.2, -1.02)]
            U.poly(img, cam, [Hd(smooth(P, 4))], hair_c)
    elif front is not None:
        U.poly(img, cam, [Hd(front)], hair_c)
    if p["hair"] == "pony":
        U.poly(img, cam, [Hd(ellipse(1.06, -0.82, 0.12, 0.10, n=12))], H("d94a6a"))
    if "glasses" in p["acc"]:
        for sx in (-1, 1): U.stroke(img, cam, Hd(U.rr_pts(sx * 0.38 - 0.24, -0.16, sx * 0.38 + 0.24, 0.20, 0.08)), 0.055 * S * k, H("1f1f22"), closed=True)
        U.stroke(img, cam, Hd([(-0.14, -0.02), (0.14, -0.02)]), 0.05 * S * k, H("1f1f22"))
    if "clip" in p["acc"]:      # the red hair clip: a little bow
        c = (0.58, -0.86)
        U.poly(img, cam, [Hd(ellipse(c[0] - 0.13, c[1], 0.16, 0.10, 0.5, n=16)), Hd(ellipse(c[0] + 0.13, c[1], 0.16, 0.10, -0.5, n=16))], H("e0352b"))
        U.poly(img, cam, [Hd(ellipse(c[0], c[1], 0.06, 0.06, n=10))], H("a8201a"))
    if "headset" in p["acc"]:
        U.stroke(img, cam, Hd(smooth([(-1.08, 0.05), (-1.12, -0.9), (-0.6, -1.62), (0.35, -1.78), (1.0, -1.5), (1.14, -0.8), (1.10, 0.05)], 5, closed=False)),
                 0.07 * S * k, H("2c2c30"))
        U.poly(img, cam, [Hd(ellipse(1.08, 0.12, 0.13, 0.22, n=14))], H("2c2c30"))
        U.stroke(img, cam, Hd(smooth([(1.06, 0.30), (0.95, 0.75), (0.62, 0.82), (0.36, 0.74)], 4, closed=False)), 0.045 * S * k, H("2c2c30"))
        U.poly(img, cam, [Hd(ellipse(0.33, 0.73, 0.06, 0.05, n=10))], H("111113"))
    # arms raised into the frame (close framing): hands come up from below
    if not st.body and st.hands:
        for side, sh, el in st.hands:
            s0 = np.array([side * 2.1, 2.3])
            e = s0 + np.array([side * math.sin(sh) * 1.7, math.cos(sh) * 1.7])
            wv = e + np.array([side * math.sin(sh + el) * 1.6, math.cos(sh + el) * 1.6])
            U.poly(img, cam, [Bd(_limb(s0, e, wv, 0.44, 0.36))], dark(shirt, 0.95))
            U.poly(img, cam, [Bd(ellipse(wv[0], wv[1], 0.40, 0.44, n=18))], skin)
    elif st.body:
        for s0, e, wv in arms:
            U.poly(img, cam, [Bd(ellipse(wv[0], wv[1], 0.40, 0.44, n=18))], skin)

def _limb(a, b, c, w0, w1):
    """a two-segment arm as one polygon"""
    P = np.array([a, b, c], float)
    out_l, out_r = [], []
    for i in range(3):
        d = P[min(i + 1, 2)] - P[max(i - 1, 0)]; d = d / (np.hypot(*d) + 1e-9); n = np.array([-d[1], d[0]])
        ww = w0 if i == 0 else (w0 + w1) / 2 if i == 1 else w1
        out_l.append(P[i] + n * ww); out_r.append(P[i] - n * ww)
    return np.array(out_l + out_r[::-1])

# ---------------------------------------------------------------- the rooms behind them
def room(img, cam, tile, name, t, d=0.0):
    """the background of a tile; d = how far back the person stands (Ted)"""
    x, y, w, h = tile; k = w / 160.0
    def R(px, py, pw, ph, col, op=1.0, r=0.0): U.rrect(img, cam, x + px * k, y + py * k, pw * k, ph * k, r * k, col, op)
    def Pp(P): return np.asarray(P, float) * k + np.array([x, y])
    if name == "Ted":
        U.gradient_rect(img, cam, x, y, w, h, H("e9e6df"), H("d6d1c7"))
        R(0, 64, 160, 26, H("b49b7c"))                                       # the floor
        U.stroke(img, cam, Pp([(0, 64), (160, 64)]), 0.6 * k, H("9c8466"))
        R(104, 8, 46, 48, H("cfe1ee")); R(104, 8, 46, 48, None)               # the window: sky and a skyline
        U.poly(img, cam, [Pp([(104, 56), (104, 40), (110, 40), (110, 30), (118, 30), (118, 36), (124, 36), (124, 24), (132, 24), (132, 38),
                               (138, 38), (138, 32), (144, 32), (144, 44), (150, 44), (150, 56)])], H("a9bfd0"))
        U.rrect(img, cam, x + 104 * k, y + 8 * k, 46 * k, 48 * k, 0, None, 1.0, H("f7f5f0"), 1.6 * k)
        U.stroke(img, cam, Pp([(127, 8), (127, 56)]), 1.2 * k, H("f7f5f0"))
        R(10, 12, 50, 34, H("fbfbf8"), 1.0, 1.0)                               # the whiteboard
        U.rrect(img, cam, x + 10 * k, y + 12 * k, 50 * k, 34 * k, 1.0 * k, None, 1.0, H("b9b9b9"), 0.8 * k)
        U.text(img, cam, "VISION", x + 35 * k, y + 19 * k, 5.6 * k, H("2d5bd7"), "marker", 0.9, "cm")
        U.stroke(img, cam, Pp([(16, 40), (24, 37), (31, 39), (40, 31), (48, 33), (55, 24)]), 0.8 * k, H("d64545"), 0.9)
        U.poly(img, cam, [Pp([(55, 21.5), (57.5, 25.5), (53, 25.0)])], H("d64545"), 0.9)
        R(130, 50, 9, 14, H("c9c2b4"), 1.0, 1.5)                              # a plant
        for i in range(7):
            a = -math.pi / 2 + (i - 3) * 0.33
            U.poly(img, cam, [Pp(ellipse(134.5 + math.cos(a) * 9, 46 + math.sin(a) * 9, 2.6, 7.5, a + math.pi / 2, n=14))], H("4f7a4a"))
    elif name == "stage":     # his "keynote" virtual background
        U.gradient_rect(img, cam, x, y, w, h, H("0e0f14"), H("1d1a22"))
        U.poly(img, cam, [Pp([(62, -2), (98, -2), (124, 72), (36, 72)])], (1.0, 0.92, 0.78), 0.10)
        U.poly(img, cam, [Pp(ellipse(80, 72, 46, 7, n=40))], (1.0, 0.93, 0.80), 0.28)
        R(0, 72, 160, 18, H("15141a"))
        U.poly(img, cam, [Pp(ellipse(80, 72, 46, 7, n=40))], (1.0, 0.90, 0.75), 0.22)
        for i, cx in enumerate((20, 140)):
            U.poly(img, cam, [Pp(ellipse(cx, 10, 6, 6, n=16))], H("2a2a30"))
            U.glow(img, cam, x + cx * k, y + 10 * k, 10 * k, (0.9, 0.75, 0.5), 0.25)
    elif name == "Me":
        U.gradient_rect(img, cam, x, y, w, h, H("e8d2b4"), H("d9bf9c"))
        U.glow(img, cam, x + 18 * k, y + 22 * k, 40 * k, (0.35, 0.22, 0.08), 0.6)
        R(10, 30, 3, 60, H("3b2f28")); U.poly(img, cam, [Pp([(4, 30), (20, 30), (16, 18), (8, 18)])], H("f3e2c0"))   # floor lamp
        R(118, 10, 36, 62, H("8a6a4c"), 1.0, 1.0)                              # bookshelf
        cols = ["c8553d", "e2b04a", "3e6b8a", "6b8f5a", "d9c7a8", "8a4a6a", "2f3e4c", "e07a4a"]
        for row in range(3):
            xx = 121.0
            for j in range(8):
                bw = 2.6 + (j * 7 + row * 3) % 3 * 0.9; bh = 13 + (j * 5 + row) % 4
                R(xx, 12 + row * 20 + (17 - bh), bw, bh, H(cols[(j + row * 3) % 8]))
                xx += bw + 0.6
                if xx > 151: break
            R(118, 29 + row * 20, 36, 2, H("6e5440"))
        R(46, 14, 24, 18, H("f5efe2")); U.rrect(img, cam, x + 46 * k, y + 14 * k, 24 * k, 18 * k, 0, None, 1, H("6e5440"), 1.0 * k)
        U.poly(img, cam, [Pp(ellipse(58, 23, 6, 5, n=18))], H("e0a050"), 0.8)
    elif name == "Dana":
        U.gradient_rect(img, cam, x, y, w, h, H("cfdcc8"), H("b9c9b2"))
        for cx in (24, 136):
            U.stroke(img, cam, Pp([(cx, 0), (cx, 14)]), 0.5 * k, H("8a8a7a"))
            R(cx - 5, 14, 10, 7, H("d9c3a5"), 1.0, 1.0)
            for i in range(9):
                a = math.pi / 2 + (i - 4) * 0.3
                U.poly(img, cam, [Pp(ellipse(cx + math.cos(a) * 9, 22 + math.sin(a) * 9, 1.8, 5, a + math.pi / 2, n=12))], H("5d8a52"))
        R(60, 10, 16, 20, H("f4efe6")); U.poly(img, cam, [Pp(ellipse(68, 20, 5, 6, n=16))], H("d3a17a"), 0.8)
    elif name == "Priya":
        U.gradient_rect(img, cam, x, y, w, h, H("f1ede6"), H("e2ddd3"))
        cols = ["b5483d", "2f5d7c", "e2b04a", "5b7f54", "7a4a7e", "d9d0bf", "c46a3a", "34495e", "8fa3b8"]
        for row in range(4):
            R(0, 20 + row * 18, 160, 1.6, H("9c8466"))
            xx = 2.0
            for j in range(40):
                bw = 2.4 + (j * 7 + row * 5) % 4 * 0.8; bh = 11 + (j * 3 + row) % 5
                R(xx, 20 + row * 18 - bh, bw, bh, H(cols[(j * 5 + row) % 9]))
                xx += bw + 0.5
                if xx > 158: break
    elif name == "Marcus":
        U.gradient_rect(img, cam, x, y, w, h, H("2a2638"), H("1b1826"))
        U.stroke(img, cam, Pp([(0, 12), (160, 12)]), 1.2 * k, H("b06cff"), 0.9)
        U.glow(img, cam, x + 80 * k, y + 12 * k, 90 * k, (0.25, 0.12, 0.45), 0.5)
        R(16, 20, 26, 36, H("3a3450")); U.text(img, cam, "LO-FI", x + 29 * k, y + 38 * k, 6 * k, H("e7a4ff"), "k", 0.7, "cm")
    elif name == "Sam":
        U.gradient_rect(img, cam, x, y, w, h, H("f4efe7"), H("e6dfd2"))
        for i in range(4): R(4 + i * 39, 2, 36, 22, H("d8c2a0"), 1.0, 1.0); R(20 + i * 39, 12, 4, 1.2, H("8a7a64"))
        R(0, 58, 160, 4, H("c9b9a2")); R(128, 30, 30, 28, H("dfe6ea"), 1.0, 1.5)
    elif name == "Lee":
        U.gradient_rect(img, cam, x, y, w, h, H("c9d2db"), H("b8c2cc"))
        R(110, 14, 30, 22, H("f4f1e8")); U.rrect(img, cam, x + 110 * k, y + 14 * k, 30 * k, 22 * k, 0, None, 1, H("8a7a5a"), 1.4 * k)
        for i in range(3): R(115, 20 + i * 4.5, 20 - i * 4, 1.2, H("b0a890"))
    elif name == "Jo":
        U.gradient_rect(img, cam, x, y, w, h, H("efe9df"), H("e3dccf"))
        R(98, 6, 54, 52, H("dde9f2"))
        for i in range(12): R(98, 7 + i * 4.3, 54, 2.6, H("f4f2ec"))
        R(14, 44, 12, 20, H("c9a77a"), 1.0, 2.0)
        for i in range(6):
            a = -math.pi / 2 + (i - 2.5) * 0.35
            U.poly(img, cam, [Pp(ellipse(20 + math.cos(a) * 8, 40 + math.sin(a) * 8, 2.2, 6.5, a + math.pi / 2, n=12))], H("5d8a52"))

def camera_off(img, cam, tile, name, col):
    x, y, w, h = tile; k = w / 160.0
    U.rrect(img, cam, x, y, w, h, 0, H("26272b"))
    initials = name[0]
    U.circle(img, cam, x + w / 2, y + h / 2 - 2 * k, 15 * k, col)
    U.text(img, cam, initials, x + w / 2, y + h / 2 - 2 * k, 13 * k, (1, 1, 1), "s", 1.0, "cm")
