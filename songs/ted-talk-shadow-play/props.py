"""Cut-paper props for the shadow theatre. Everything returns polygons in world units (or stamps glyphs into masks).
Floor at y = 880."""
import math, os
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from puppets import smooth, ellipse_pts, limb, rot
import stage as ST
from studio import core as C

F32 = np.float32
FONT = lambda n: os.path.join(C.FONTS, n)
F_SC = FONT("PlayfairDisplaySC-Regular.ttf"); F_SERIF = FONT("CormorantGaramond-Bold.ttf"); F_ITAL = FONT("CormorantGaramond-MediumItalic.ttf")
FLOOR = ST.FLOOR

# ---------------------------------------------------------------- glyphs (letters, question marks, words) as stamps
@lru_cache(256)
def glyph(text, font, px):
    f = ImageFont.truetype(font, px)
    l, t_, r, b = f.getbbox(text)
    w, h = r - l + 8, b - t_ + 8
    im = Image.new("L", (w, h), 0); ImageDraw.Draw(im).text((4 - l, 4 - t_), text, font=f, fill=255)
    return np.asarray(im, np.uint8)

@lru_cache(512)
def em_glyph(ch, font, px=200):
    """a glyph on a shared em box: (image, (advance-centre x, baseline y) in px, advance, ink top y, cap height px)"""
    f = ImageFont.truetype(font, px)
    asc, desc = f.getmetrics(); adv = f.getlength(ch)
    l, t_, r, b = f.getbbox(ch) if ch.strip() else (0, asc, 0, asc)
    x0 = 4 - min(l, 0)
    W = int(math.ceil(max(r, adv) - min(l, 0))) + 8; H = asc + desc + 8
    im = Image.new("L", (W, H), 0); ImageDraw.Draw(im).text((x0, 4), ch, font=f, fill=255)
    cl, ct, cr, cb = f.getbbox("I")
    return np.asarray(im, np.uint8), (x0 + adv / 2, 4 + asc), adv, 4 + t_, cb - ct

def stamp(mask, cam, g, c, size_world, ang=0.0, anchor=(0.5, 0.5), val=255, holes=None):
    """put glyph mask g (uint8) into mask, centred (by anchor) at world point c, height size_world, turned by ang"""
    h, w = g.shape; s = cam.L(size_world) / h
    if s * h < 2: return
    cx, cy = cam.P(np.asarray(c, float))
    M = cv2.getRotationMatrix2D((anchor[0] * w, anchor[1] * h), -math.degrees(ang), s)
    M[0, 2] += cx - anchor[0] * w; M[1, 2] += cy - anchor[1] * h
    out = cv2.warpAffine(g, M, (mask.shape[1], mask.shape[0]), flags=cv2.INTER_LINEAR)
    if val == 255: np.maximum(mask, out, out=mask)
    else: mask[:] = np.minimum(mask, 255 - out)

# ---------------------------------------------------------------- strings, circles
def string_to(mask, cam, top, bottom, w=1.6):
    ST.line(mask, cam, top, bottom, w)

def circle(mask, cam, c, r, val=255, thick=-1):
    p = cam.P(np.asarray(c, float)); rr = cam.L(r)
    cv2.circle(mask, (int(round(p[0] * 8)), int(round(p[1] * 8))), max(1, int(round(rr * 8))), val, -1 if thick < 0 else max(1, int(round(cam.L(thick)))), cv2.LINE_AA, 3)

# ---------------------------------------------------------------- curtains
def curtain(side, open_k, t, h=1080.0):
    """an ornate stage curtain (left or right), gathered toward its side as it opens; returns polygons"""
    sgn = -1 if side == "left" else 1
    x_edge0 = 960.0                                   # closed: the inner edge at the centre
    x_edge1 = 960.0 + sgn * 820.0                     # open: gathered at the side
    xe = x_edge0 + (x_edge1 - x_edge0) * open_k
    xo = 0.0 if side == "left" else 1920.0
    ys = np.linspace(-20, FLOOR + 30, 60)
    # the inner edge: a wavy fold, pulled into a tie-back when open
    tie_y = 560.0
    pts = []
    for y in ys:
        pull = math.exp(-((y - tie_y) / 160.0) ** 2) * 70 * open_k
        wav = 10 * math.sin(y * 0.045 + t * 0.8) * (1 - 0.5 * open_k)
        pts.append((xe - sgn * pull + wav, y))
    poly = [(xo, -20)] + pts + [(xo, FLOOR + 30)]
    out = [np.array(poly)]
    # fold lines are cut as thin holes (the light leaks through the folds)
    holes = []
    for k in range(1, 5):
        fx = xo + (xe - xo) * k / 5.0
        P = [(fx + 6 * math.sin(y * 0.03 + k), y) for y in np.linspace(30, FLOOR - 30, 24)]
        holes.append(limb(P, [1.6] * len(P)))
    # tassel at the tie-back
    if open_k > 0.3:
        tx = xe - sgn * 60 * open_k
        out.append(ellipse_pts((tx, tie_y + 40), 16, 26, n=16))
        out.append(np.array([(tx - 12, tie_y + 60), (tx + 12, tie_y + 60), (tx + 18, tie_y + 120), (tx - 18, tie_y + 120)]))
    return out, holes

def valance(t):
    """the scalloped top border of the stage"""
    pts = [(-10, -10), (1930, -10)]
    for x in np.linspace(1930, -10, 25):
        k = (x / 80.0) % 1.0
        pts.append((x, 62 + 26 * math.sin(math.pi * k)))
    return [np.array(pts)]

# ---------------------------------------------------------------- the office
def wall_clock(mask, cam, c, r, minutes, val=255):
    """a round clock: a ring, ticks and two hands"""
    circle(mask, cam, c, r, val, thick=r * 0.16)
    for i in range(12):
        a = i * math.pi / 6; p0 = np.array(c) + np.array([math.sin(a), -math.cos(a)]) * r * 0.78; p1 = np.array(c) + np.array([math.sin(a), -math.cos(a)]) * r * 0.64
        ST.line(mask, cam, p0, p1, r * (0.07 if i % 3 == 0 else 0.04), val)
    am = minutes / 60 * 2 * math.pi; ah = (9.25 + minutes / 60) / 12 * 2 * math.pi
    ST.line(mask, cam, c, np.array(c) + np.array([math.sin(am), -math.cos(am)]) * r * 0.70, r * 0.07, val)
    ST.line(mask, cam, c, np.array(c) + np.array([math.sin(ah), -math.cos(ah)]) * r * 0.48, r * 0.09, val)
    circle(mask, cam, c, r * 0.08, val)

def chair(x, facing=1, s=1.0):
    f = facing
    seat_y = FLOOR - 250 * s
    out = [np.array([(x - f * 70 * s, seat_y), (x + f * 80 * s, seat_y), (x + f * 80 * s, seat_y + 22 * s), (x - f * 70 * s, seat_y + 22 * s)])]
    out.append(limb([(x - f * 66 * s, seat_y + 10), (x - f * 80 * s, seat_y - 165 * s)], [9 * s, 8 * s]))     # back
    out.append(limb([(x - f * 80 * s, seat_y - 165 * s), (x - f * 30 * s, seat_y - 158 * s)], [10 * s, 9 * s]))
    for lx in (-60, 70):
        out.append(limb([(x + f * lx * s, seat_y + 15), (x + f * (lx + (6 if lx > 0 else -6)) * s, FLOOR)], [7 * s, 6 * s]))
    return out

def plant(x, s=1.0, t=0.0):
    out = [np.array([(x - 45 * s, FLOOR), (x + 45 * s, FLOOR), (x + 55 * s, FLOOR - 90 * s), (x - 55 * s, FLOOR - 90 * s)])]
    for i in range(9):
        a = -math.pi / 2 + (i - 4) * 0.28 + 0.03 * math.sin(t * 1.3 + i)
        L = (150 + 60 * math.cos(i * 1.7)) * s
        base = np.array([x, FLOOR - 90 * s]); tip = base + np.array([math.cos(a), math.sin(a)]) * L
        mid = (base + tip) / 2 + np.array([-math.sin(a), math.cos(a)]) * 14 * s
        out.append(smooth([base, mid + np.array([-math.sin(a), math.cos(a)]) * 18 * s, tip, mid - np.array([-math.sin(a), math.cos(a)]) * 6 * s], 4))
    return out

def window_blinds(x, y, w, h):
    """a window on the back wall with blinds: the slats are holes"""
    frame = [np.array([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])]
    holes = []
    n = 9
    for i in range(n):
        yy = y + 14 + i * (h - 28) / n
        holes.append(np.array([(x + 14, yy), (x + w - 14, yy), (x + w - 14, yy + (h - 28) / n * 0.55), (x + 14, yy + (h - 28) / n * 0.55)]))
    return frame, holes

# ---------------------------------------------------------------- a calendar that gives up
def calendar(mask, cam, x, y, day, flying, t, flag=0.0):
    """a wall calendar: a board, a big date cut out of it; `flying` = list of (phase 0..1) for pages tearing off"""
    board = np.array([(x - 70, y - 10), (x + 70, y - 10), (x + 70, y + 160), (x - 70, y + 160)])
    ST.fill(mask, cam, [board])
    ST.fill(mask, cam, [np.array([(x - 60, y + 30), (x + 60, y + 30), (x + 60, y + 34), (x - 60, y + 34)])], 0)
    g = glyph(str(day), F_SERIF, 160)
    stamp(mask, cam, g, (x, y + 95), 100, val=0)
    ST.fill(mask, cam, [ellipse_pts((x, y - 26), 8, 8, n=10)])
    ST.line(mask, cam, (x, y - 26), (x, y - 10), 3)
    for item in flying:
        ph, spread = (item, 0.0) if not isinstance(item, tuple) else item
        if spread == 0.0:
            px = x + 260 * ph + 30 * math.sin(ph * 9); py = y + 60 - 320 * ph + 200 * ph * ph; sz = 1 - 0.3 * ph
        else:   # a flurry: pages fan out in every direction, smaller
            a = -math.pi / 2 + spread
            px = x + math.cos(a) * 520 * ph; py = y + 60 + math.sin(a) * 420 * ph + 260 * ph * ph; sz = 0.55 * (1 - 0.3 * ph)
        ang = ph * 9.0 + spread * 3
        P = np.array([(-60, -70), (60, -70), (60, 70), (-60, 70)], float) * sz
        P = np.array([rot(p, ang) for p in P]) + np.array([px, py])
        ST.fill(mask, cam, [P])
        slit = np.array([(-48, -42), (48, -42), (48, -36), (-48, -36)], float) * sz      # the header line of a calendar page
        ST.fill(mask, cam, [np.array([rot(p, ang) for p in slit]) + np.array([px, py])], 0)
    if flag > 0:   # the little white flag of surrender, poked out from behind the calendar
        base = np.array([x + 50, y + 70]); pole_top = base + np.array([120, -105]) * flag
        ST.line(mask, cam, base, pole_top, 4.5)
        w1, w2 = 6 * math.sin(t * 9), 6 * math.sin(t * 9 + 1)
        wv = [pole_top + np.array([0, 2]), pole_top + np.array([40 * flag, 4 + w1]), pole_top + np.array([78 * flag, 6 + w2]),
              pole_top + np.array([74 * flag, 46 + w2]), pole_top + np.array([38 * flag, 44 + w1]), pole_top + np.array([0, 42])]
        ST.polyline(mask, cam, wv, 3.0, closed=True)
        return np.array(wv)
    return None

# ---------------------------------------------------------------- an hourglass
def hourglass(mask, cam, c, h, used, t):
    """15 minutes of sand; `used` 0..1 of it has fallen"""
    x, y = c; w = h * 0.42
    frame = [np.array([(x - w * 0.62, y - h / 2 - 16), (x + w * 0.62, y - h / 2 - 16), (x + w * 0.62, y - h / 2), (x - w * 0.62, y - h / 2)]),
             np.array([(x - w * 0.62, y + h / 2), (x + w * 0.62, y + h / 2), (x + w * 0.62, y + h / 2 + 16), (x - w * 0.62, y + h / 2 + 16)])]
    ST.fill(mask, cam, frame)
    glass = [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + 8, y), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2), (x - 8, y)]
    ST.polyline(mask, cam, glass, 5, closed=True)
    for sx in (-1, 1): ST.line(mask, cam, (x + sx * w * 0.56, y - h / 2), (x + sx * w * 0.56, y + h / 2), 7)
    top = 1 - used
    if top > 0.01:
        ty = y - h / 2 * top * 0.9
        hw = (w / 2 - 8) * (ty - y) / (-h / 2) + 8
        ST.fill(mask, cam, [np.array([(x - hw, ty), (x + hw, ty), (x + 8, y - 4), (x - 8, y - 4)])])
    if used > 0.01:
        bh = h / 2 * min(1, used) * 0.85
        ST.fill(mask, cam, [smooth([(x - w / 2 + 6, y + h / 2 - 2), (x + w / 2 - 6, y + h / 2 - 2), (x + 10, y + h / 2 - bh), (x - 10, y + h / 2 - bh)], 4)])
    if 0.01 < used < 0.99: ST.line(mask, cam, (x, y), (x, y + h / 2), 3)

# ---------------------------------------------------------------- creatures and small things
def cricket(x, t, s=1.0):
    y = FLOOR - 6
    body = smooth([(x - 30 * s, y - 14 * s), (x + 10 * s, y - 24 * s), (x + 34 * s, y - 16 * s), (x + 36 * s, y - 6 * s), (x - 26 * s, y - 2 * s)], 4)
    head = ellipse_pts((x + 38 * s, y - 16 * s), 10 * s, 9 * s, n=12)
    out = [body, head]
    out.append(limb([(x + 44 * s, y - 22 * s), (x + 70 * s, y - 60 * s + 6 * math.sin(t * 7)), (x + 100 * s, y - 64 * s)], [1.5 * s] * 3))
    out.append(limb([(x + 42 * s, y - 22 * s), (x + 60 * s, y - 70 * s), (x + 84 * s, y - 84 * s + 6 * math.sin(t * 5))], [1.5 * s] * 3))
    out.append(limb([(x - 6 * s, y - 14 * s), (x - 34 * s, y - 50 * s), (x - 52 * s, y)], [4 * s, 3 * s, 2 * s]))   # big hind leg
    out.append(limb([(x + 18 * s, y - 8 * s), (x + 26 * s, y)], [2 * s, 2 * s]))
    out.append(limb([(x + 6 * s, y - 8 * s), (x + 2 * s, y)], [2 * s, 2 * s]))
    return out

def chirp_lines(x, t, s=1.0):
    k = (t * 3.0) % 1.0
    out = []
    for i in range(3):
        r = (30 + i * 18) * s * (0.6 + 0.4 * k)
        a = np.linspace(-1.0, 0.2, 10)
        P = [(x + 30 * s + r * math.cos(q), FLOOR - 30 * s + r * math.sin(q)) for q in a]
        out.append(limb(P, [1.8 * s] * len(P), cap=True))
    return out

def zzz(x, y, t, s=1.0):
    out = []
    for i in range(3):
        ph = (t * 0.6 + i / 3) % 1.0
        out.append(((x + 30 * ph * s + 8 * math.sin(ph * 6), y - 120 * ph * s), 30 * s * (0.6 + 0.6 * ph), 1 - ph))
    return out

def ghost(x, y, t, s=1.0):
    """a sheet ghost (cut from thin paper: it casts a lighter shadow), with two cut-out eyes"""
    pts = [(x - 70 * s, y + 40 * s)]
    for i in range(7):
        pts.append((x - 70 * s + i * 23 * s, y + 70 * s + 14 * s * math.sin(t * 4 + i * 1.3) * (1 if i % 2 else -1)))
    pts += [(x + 72 * s, y + 40 * s), (x + 76 * s, y - 60 * s), (x + 40 * s, y - 140 * s), (x - 10 * s, y - 158 * s), (x - 56 * s, y - 120 * s), (x - 76 * s, y - 40 * s)]
    body = smooth(pts, 4)
    holes = [ellipse_pts((x - 10 * s, y - 80 * s), 11 * s, 17 * s, n=12), ellipse_pts((x + 24 * s, y - 80 * s), 11 * s, 17 * s, n=12),
             ellipse_pts((x + 8 * s, y - 40 * s), 9 * s, 12 * s, n=12)]
    return [body], holes

def door(x, w, h, open_k, val_holes=True):
    """a door in the back wall: frame, and the door leaf narrowing as it swings open; an open door is a lit rectangle"""
    y1 = FLOOR; y0 = FLOOR - h
    frame = [np.array([(x - w / 2 - 18, y0 - 18), (x + w / 2 + 18, y0 - 18), (x + w / 2 + 18, y1), (x - w / 2 - 18, y1)])]
    hole = [np.array([(x - w / 2, y0), (x + w / 2, y0), (x + w / 2, y1), (x - w / 2, y1)])]
    lw = w * (1 - open_k)
    leaf = [np.array([(x - w / 2, y0), (x - w / 2 + lw, y0 + 18 * open_k), (x - w / 2 + lw, y1 - 10 * open_k), (x - w / 2, y1)])]
    knob = [ellipse_pts((x - w / 2 + lw * 0.85, (y0 + y1) / 2), 8, 8, n=10)] if lw > 20 else []
    return frame, hole, leaf, knob

def cobweb(x, y, r, k):
    out = []
    if k <= 0: return out
    for i in range(6):
        a = math.pi / 2 + i * (math.pi / 2) / 5
        out.append(limb([(x, y), (x + math.cos(a) * r * k * -1, y + math.sin(a) * r * k)], [1.2, 1.0]))
    for j in range(1, 4):
        rr = r * k * j / 4
        P = [(x - math.cos(math.pi / 2 + i * (math.pi / 2) / 5) * rr * 1.0, y + math.sin(math.pi / 2 + i * (math.pi / 2) / 5) * rr) for i in range(6)]
        out.append(limb(P, [1.0] * len(P), cap=False))
    return out

def lamppost(x, s=1.0):
    out = [limb([(x, FLOOR), (x, FLOOR - 470 * s)], [7 * s, 5 * s]), limb([(x, FLOOR - 470 * s), (x + 40 * s, FLOOR - 500 * s), (x + 80 * s, FLOOR - 480 * s)], [5 * s] * 3)]
    out.append(np.array([(x + 62 * s, FLOOR - 482 * s), (x + 98 * s, FLOOR - 482 * s), (x + 90 * s, FLOOR - 452 * s), (x + 70 * s, FLOOR - 452 * s)]))
    return out

def boat(x, y, s=1.0):
    hull = smooth([(x - 150 * s, y - 30 * s), (x + 160 * s, y - 34 * s), (x + 120 * s, y + 20 * s), (x - 110 * s, y + 20 * s)], 4)
    return [hull]

def waves(x0, x1, y, t, amp=10.0):
    xs = np.linspace(x0, x1, 80)
    top = [(x, y + amp * math.sin(x * 0.04 + t * 2.0) + amp * 0.5 * math.sin(x * 0.09 - t * 1.3)) for x in xs]
    return [np.array(top + [(x1, y + 300), (x0, y + 300)])]

def road(t_k, horizon=420.0, cx=960.0):
    """a road winding off to the horizon: two edges and a dashed centre line, little trees along it (polygons + lines)"""
    n = 60; polys = []; lines_ = []
    L, R, M = [], [], []
    for i in range(n + 1):
        u = i / n * t_k
        y = FLOOR - (FLOOR - horizon) * (1 - (1 - u) ** 1.6)
        c = cx + 300 * math.sin(u * 5.5) * (1 - u) ** 1.2
        hw = 300 * (1 - u) ** 1.4 + 3
        L.append((c - hw, y)); R.append((c + hw, y)); M.append((c, y))
    if t_k > 0.02:
        lines_.append((L, 5.0)); lines_.append((R, 5.0))
        for i in range(0, len(M) - 1, 3): lines_.append(([M[i], M[i + 1]], 3.0))
        for i in range(4, len(L), 9):   # trees along the road, smaller further away
            for side, P in ((-1, L), (1, R)):
                x, y = P[i]; s_ = max(0.15, 1 - i / n) * 1.0
                x += side * 40 * s_
                polys.append(np.array([(x - 2 * s_, y), (x + 2 * s_, y), (x + 2 * s_, y - 40 * s_), (x - 2 * s_, y - 40 * s_)]))
                polys.append(ellipse_pts((x, y - 60 * s_), 22 * s_, 30 * s_, n=14))
    return polys, lines_

def keyhole(c, r, k_open):
    """a keyhole in the wall: when it opens, there's a smaller keyhole inside it (and another)"""
    polys, holes = [], []
    polys.append(ellipse_pts(c, r * 1.9, r * 2.3, n=40))                       # the escutcheon (dark plate)
    holes.append(ellipse_pts((c[0], c[1] - r * 0.4), r * 0.55 * (1 + 0.9 * k_open), r * 0.55 * (1 + 0.9 * k_open), n=24))
    holes.append(np.array([(c[0] - r * 0.3 * (1 + 0.9 * k_open), c[1] - r * 0.3), (c[0] + r * 0.3 * (1 + 0.9 * k_open), c[1] - r * 0.3),
                           (c[0] + r * 0.5 * (1 + 0.9 * k_open), c[1] + r * 1.2 * (1 + 0.5 * k_open)), (c[0] - r * 0.5 * (1 + 0.9 * k_open), c[1] + r * 1.2 * (1 + 0.5 * k_open))]))
    inner = []
    if k_open > 0.5:   # inside the opened keyhole: another keyhole
        q = (k_open - 0.5) * 2; r2 = r * 0.42
        inner.append(ellipse_pts((c[0], c[1] - r2 * 0.4 + r * 0.1), r2 * 0.55, r2 * 0.55, n=18))
        inner.append(np.array([(c[0] - r2 * 0.3, c[1] - r2 * 0.3 + r * 0.1), (c[0] + r2 * 0.3, c[1] - r2 * 0.3 + r * 0.1), (c[0] + r2 * 0.5, c[1] + r2 * 1.2 + r * 0.1), (c[0] - r2 * 0.5, c[1] + r2 * 1.2 + r * 0.1)]))
    return polys, holes, inner

def mountain_prop(x, y, s=1.0):
    """a cut-out mountain on a stick, a zig-zag path cut up to the summit, a flag on top. (x, y) = the hand"""
    stick = limb([(x, y + 6 * s), (x, y - 60 * s)], [4.5 * s, 4 * s])
    by = y - 56 * s
    mtn = np.array([(x - 150 * s, by), (x - 112 * s, by - 62 * s), (x - 92 * s, by - 52 * s), (x - 22 * s, by - 178 * s), (x + 8 * s, by - 150 * s),
                    (x + 36 * s, by - 160 * s), (x + 82 * s, by - 96 * s), (x + 150 * s, by)])
    snow = np.array([(x - 52 * s, by - 124 * s), (x - 22 * s, by - 178 * s), (x + 4 * s, by - 142 * s), (x - 6 * s, by - 134 * s), (x - 20 * s, by - 146 * s), (x - 36 * s, by - 126 * s)])
    path = limb([(x - 74 * s, by + 2 * s), (x + 34 * s, by - 34 * s), (x - 46 * s, by - 70 * s), (x + 14 * s, by - 104 * s), (x - 30 * s, by - 136 * s), (x - 22 * s, by - 172 * s)],
                [6 * s, 5.5 * s, 5 * s, 4.2 * s, 3.4 * s, 2.6 * s])
    pole = limb([(x - 22 * s, by - 174 * s), (x - 22 * s, by - 238 * s)], [2.6 * s, 2.2 * s])
    flag = np.array([(x - 20 * s, by - 238 * s), (x + 28 * s, by - 224 * s), (x - 20 * s, by - 208 * s)])
    return [stick, mtn, pole, flag], [path, snow]

def big_key(x, y, turn, s=1.0):
    """a big old key held up by its bow at (x, y), shaft pointing up; `turn` 0..1 flips the bits to the other side"""
    fx = math.cos(turn * math.pi)
    def X(P): return np.array([(x + (px - x) * fx, py) for px, py in P])
    bow = ellipse_pts((x, y - 34 * s), 40 * s, 46 * s, n=32)
    bow_hole = [ellipse_pts((x - 14 * s, y - 40 * s), 9 * s, 12 * s, n=14), ellipse_pts((x + 14 * s, y - 40 * s), 9 * s, 12 * s, n=14), ellipse_pts((x, y - 18 * s), 9 * s, 10 * s, n=14)]
    shaft = np.array([(x - 9 * s, y - 72 * s), (x + 9 * s, y - 72 * s), (x + 9 * s, y - 250 * s), (x - 9 * s, y - 250 * s)])
    collar = np.array([(x - 18 * s, y - 80 * s), (x + 18 * s, y - 80 * s), (x + 18 * s, y - 92 * s), (x - 18 * s, y - 92 * s)])
    bit = np.array([(x + 9 * s, y - 250 * s), (x + 9 * s, y - 196 * s), (x + 34 * s, y - 196 * s), (x + 34 * s, y - 208 * s), (x + 22 * s, y - 208 * s),
                    (x + 22 * s, y - 222 * s), (x + 40 * s, y - 222 * s), (x + 40 * s, y - 250 * s)])
    polys = [bow, shaft, collar, X(bit)]
    return polys, [X(h) for h in bow_hole]

def book(x, y, open_k, s=1.0):
    """a pop-up storybook held open: two page blocks with lines of text cut out, and a castle standing up out of the gutter"""
    out, holes = [], []
    k = max(0.0, min(1.0, open_k))
    L = 150 * s * (0.25 + 0.75 * k); th = 22 * s
    for sg in (-1, 1):
        top = [(x, y - 6 * s * k)] + [(x + sg * L * u, y - (6 + 26 * math.sin(u * math.pi * 0.9)) * s * k - 8 * s * u) for u in np.linspace(0.1, 1, 8)]
        bot = [(x + sg * L, y + th - 6 * s * k), (x, y + th + 8 * s)]
        P = np.array(top + bot)
        out.append(P)
        if k > 0.6:
            for i in range(4):   # lines of text, cut out
                u0, u1 = 0.18, 0.86 - 0.12 * (i == 3)
                yy = lambda u: y - (6 + 26 * math.sin(u * math.pi * 0.9)) * s * k - 8 * s * u + (9 + i * 3.4) * s
                pts = [(x + sg * L * u, yy(u)) for u in np.linspace(u0, u1, 6)]
                holes.append(limb(pts, [1.1 * s] * len(pts)))
    if k > 0.35:
        q = min(1, (k - 0.35) / 0.5); hh = 170 * s * q; x0 = x
        castle = [(x0 - 92 * s, y - 4 * s), (x0 - 92 * s, y - hh * 0.62), (x0 - 100 * s, y - hh * 0.62), (x0 - 100 * s, y - hh * 0.72), (x0 - 92 * s, y - hh * 0.72),
                  (x0 - 92 * s, y - hh * 0.80), (x0 - 80 * s, y - hh * 0.80), (x0 - 80 * s, y - hh * 0.72), (x0 - 70 * s, y - hh * 0.72), (x0 - 70 * s, y - hh * 0.80),
                  (x0 - 58 * s, y - hh * 0.80), (x0 - 58 * s, y - hh * 0.55), (x0 - 26 * s, y - hh * 0.55), (x0 - 26 * s, y - hh * 0.92), (x0 - 10 * s, y - hh * 1.12),
                  (x0 + 6 * s, y - hh * 0.92), (x0 + 6 * s, y - hh * 0.55), (x0 + 50 * s, y - hh * 0.55), (x0 + 50 * s, y - hh * 0.78), (x0 + 60 * s, y - hh * 0.78),
                  (x0 + 60 * s, y - hh * 0.70), (x0 + 70 * s, y - hh * 0.70), (x0 + 70 * s, y - hh * 0.78), (x0 + 80 * s, y - hh * 0.78), (x0 + 80 * s, y - hh * 0.55),
                  (x0 + 92 * s, y - hh * 0.55), (x0 + 92 * s, y - 4 * s)]
        out.append(np.array(castle))
        out.append(np.array([(x0 - 10 * s, y - hh * 1.12), (x0 - 10 * s, y - hh * 1.38), (x0 + 26 * s, y - hh * 1.31), (x0 - 7 * s, y - hh * 1.25)]))
        holes.append(np.array([(x0 - 22 * s, y - 4 * s), (x0 - 22 * s, y - hh * 0.30), (x0 - 10 * s, y - hh * 0.38), (x0 + 2 * s, y - hh * 0.30), (x0 + 2 * s, y - 4 * s)]))   # the gate
        for wx in (-75, 65): holes.append(np.array([(x0 + (wx - 5) * s, y - hh * 0.46), (x0 + (wx + 5) * s, y - hh * 0.46), (x0 + (wx + 5) * s, y - hh * 0.34), (x0 + (wx - 5) * s, y - hh * 0.34)]))
    return out, holes

def cobweb_corner(cx, cy, r, k, a0, a1, t=0.0):
    """a cobweb in a corner at (cx, cy), fanning between angles a0..a1; thin threads (polylines)"""
    if k <= 0: return []
    n = 6; angs = np.linspace(a0, a1, n); R = r * k
    out = [[(cx, cy), (cx + math.cos(a) * R, cy + math.sin(a) * R)] for a in angs]
    for j in range(1, 5):
        rr = R * j / 4.6
        P = []
        for i in range(n - 1):
            p0 = np.array([cx + math.cos(angs[i]) * rr, cy + math.sin(angs[i]) * rr]); p1 = np.array([cx + math.cos(angs[i + 1]) * rr, cy + math.sin(angs[i + 1]) * rr])
            m = (p0 + p1) / 2; d = m - np.array([cx, cy]); m = m - d / (np.hypot(*d) + 1e-6) * rr * 0.10   # threads sag inward
            P += [tuple(p0), tuple(m)]
        P.append((cx + math.cos(angs[-1]) * rr, cy + math.sin(angs[-1]) * rr))
        out.append(P)
    return out

def spider(x, y, s=1.0, t=0.0):
    body = [ellipse_pts((x, y), 7 * s, 9 * s, n=14), ellipse_pts((x, y - 11 * s), 5 * s, 5 * s, n=10)]
    legs = []
    for sg in (-1, 1):
        for i in range(4):
            a = (-0.5 + i * 0.35); wig = 0.15 * math.sin(t * 6 + i)
            p0 = (x + sg * 4 * s, y - 4 * s + i * 3 * s); p1 = (x + sg * (14 * s), y - 10 * s + i * 6 * s + wig * 6); p2 = (x + sg * 20 * s, y + (i * 7 - 2) * s)
            legs.append([p0, p1, p2])
    return body, legs

def number_tag(mask, cam, c, r, n, k):
    """a round cut-paper tag with a number cut out of it"""
    if k <= 0.01: return
    circle(mask, cam, c, r * k, 255)
    g = glyph(str(n), F_SERIF, 160)
    stamp(mask, cam, g, (c[0], c[1] + 2 * k), r * 1.25 * k, val=0)

def burn_edge(mask, prog, rng_seed=3):
    """burn a stamped region away from the bottom: returns (kept mask, glowing edge mask)"""
    ys, xs = np.nonzero(mask > 8)
    if len(ys) == 0: return mask, np.zeros_like(mask)
    y0, y1 = ys.min(), ys.max()
    H, W = mask.shape
    yy = np.arange(H, dtype=F32)[:, None]
    noise = cv2.resize(np.random.default_rng(rng_seed).random((max(2, H // 24), max(2, W // 24))).astype(F32), (W, H), interpolation=cv2.INTER_CUBIC)
    front = y1 - (y1 - y0 + 20) * prog + noise * 26
    keep = (yy < front).astype(F32)
    edge = np.exp(-((yy - front) / 4.0) ** 2) * (mask > 8)
    return (mask.astype(F32) * keep).astype(np.uint8), (np.clip(edge, 0, 1) * 255).astype(np.uint8)
