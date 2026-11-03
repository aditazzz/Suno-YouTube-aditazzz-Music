"""THE PROMPTRESS - the full film (0:00-4:28.39). Edit decision list + shots. Song times are from the recording
(build/words.json, beats.json, vocal-stem onsets). 4.44-33.34 is V5 (hero5.py) unchanged.
usage: python3 poc/film.py <out_dir> [first last] [--still t,...]"""
import os, sys, math, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
_argv = sys.argv; sys.argv = [sys.argv[0]]
import hero5 as V5
sys.argv = _argv
H4 = V5.H4
import portal as P, wkit as K, door2 as D
import film_kit as F
from film_kit import eio, eout, ein, clamp, MOONCOL, YS, XS
from witch2 import figure, raster2, rimlight
from witch_back import back_figure
from hand4 import hand4
import terminal as TM
W, H = K.W, K.H; FPS = 30.0; RM = P.RM
DUR = 268.3875
BEAT = 60 / 117.4538

# the real footage plays slower at the start so the opening can breathe (no exposure-ramp frames)
def _ptime(t):
    if t >= V5.T_S8: return 12.0 + (t - V5.T_S8)
    if t < 15.0: return 10.25 + t * 0.55
    return 10.4 + (t - 16.95)
H4.plate_time = _ptime

def plate_img(pt, C, r):
    """your IMG_2269 footage, moon at screen C with radius r (frames blended for slow playback)"""
    fj = (pt - P.PT0) * P.PFPS; j = int(np.clip(fj, 0, len(P.TR) - 2)); fr = float(np.clip(fj - j, 0, 1))
    Pl = P.plate(j).astype(np.float32)
    if fr > 0.02: Pl = Pl * (1 - fr) + P.plate(j + 1).astype(np.float32) * fr
    mx, my = P.cx[j], P.cy[j]; s = r / RM
    M = np.float32([[s, 0, C[0] - s * mx], [0, s, C[1] - s * my]])
    out = cv2.warpAffine(Pl, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT) / 255.0
    out = out * np.array([1.06, 1.0, 0.95]) * 0.95 + np.array([0.012, 0.006, 0.0])
    hi = np.clip((out.mean(2, keepdims=True) - 0.35) / 0.4, 0, 1); out = out * (1 - hi) + out * np.array([0.90, 0.97, 1.06]) * hi
    return out.astype(np.float32)

def push(img, t, t0, t1, z1, c):
    """a slow, motivated push-in toward c"""
    z = 1.0 + (z1 - 1.0) * eio((t - t0) / (t1 - t0))
    if z <= 1.0005: return img
    M = np.float32([[z, 0, c[0] - z * c[0]], [0, z, c[1] - z * c[1]]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def hand_xy(t, base, amp=(2.0, 2.0)):
    return np.asarray(base, float) + np.array([amp[0] * math.sin(t * 1.3), amp[1] * math.sin(t * 2.0)])

# ============================================================ ACT I
def s_open(t):   # 0-4.44: your moon, still; fading up from the dark (never a black first frame)
    img = H4.render(t)
    return np.clip(img * (0.75 + 0.25 * eio(t / 1.5)), 0, 1)

# 33.34-41.56 "Grandma had a book of spells / names of things she couldn't tell": the book is a window
_bk = {}
def book_scene(t):
    if "bg" not in _bk:
        v = (YS / H)[..., None]; d = np.sqrt((XS - 0.5 * W) ** 2 + (YS - 0.30 * H) ** 2) / H
        _bk["bg"] = (np.array([0.020, 0.025, 0.035], np.float32) + np.exp(-(d / 0.55) ** 2)[..., None] * np.array([0.06, 0.10, 0.16], np.float32)).astype(np.float32)
        _bk["p01"] = cv2.resize(V5._sq(V5._p01, 0.5, 0.40, 0.70), (700, 860))
        _bk["p14"] = cv2.resize(V5._c14, (700, 860)); _bk["p08"] = cv2.resize(V5._sq(D._p08, 0.45, 0.45, 0.8), (700, 860))
        _bk["p15"] = cv2.resize(V5._sq(cv2.imread(f"{K.AS}/photo_15.jpg").astype(np.float32) / 255, 0.5, 0.45, 0.7), (700, 860))
        rng = np.random.default_rng(3); ink = np.zeros((860, 700), np.float32)
        for row in range(14):     # rows of an illegible hand: names of things
            y = 110 + row * 46; x = 70
            while x < 620:
                L = rng.integers(30, 110); pts = np.stack([np.linspace(x, x + L, 12), y + np.sin(np.linspace(0, rng.uniform(6, 14), 12)) * rng.uniform(3, 7)], 1)
                cv2.polylines(ink, [pts.astype(np.int32)], False, 1.0, 2, cv2.LINE_AA); x += L + rng.integers(14, 30)
        _bk["ink"] = cv2.GaussianBlur(ink, (0, 0), 0.8)
    img = _bk["bg"].copy()
    z = 1.0 + 0.05 * clamp((t - 33.34) / 8.2)                                    # a slow push
    cx, cy = 0.5 * W, 0.56 * H
    def P_(x, y): return (cx + (x - cx) * z, cy + (y - cy) * z)
    def page(x0, x1, top, bot, lift=0.0):
        return [P_(x0, top + lift), P_(x1, top), P_(x1, bot), P_(x0, bot)]
    def curved(img_, tex, xs, xo, top, bot, bulge=0.040 * H):
        """a page that bends down into the spine: drawn flat, then each column pushed down by how near the spine it is"""
        x0_, x1_ = min(xs, xo), max(xs, xo)
        lay = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W, 3), np.float32)
        q = page(x0_, x1_, top, bot)
        lay = F.put_quad(lay, tex, q); al = F.put_quad(al, np.ones(tex.shape[:2] + (3,), np.float32), q)
        sx_ = P_(xs, 0)[0]; so = P_(xo, 0)[0]
        s = np.clip((XS[0] - sx_) / (so - sx_), 0, 1)
        dy = (bulge * z * (1 - s) ** 2.2).astype(np.float32)
        my = (YS - dy[None, :]).astype(np.float32)
        lay = cv2.remap(lay, XS, my, cv2.INTER_LINEAR); al = cv2.remap(al, XS, my, cv2.INTER_LINEAR)[..., :1]
        shade = (0.70 + 0.30 * np.clip(s * 1.6, 0, 1))[None, :, None]
        return img_ * (1 - al) + lay * shade * al
    plate = plate_img(10.4 + (t - 33.34) * 0.6, (350, 470), 150)[0:860, 0:700].copy() if True else None
    turn = eio((t - 37.62) / 0.75)                                               # the page turns on "names of things"
    left_pic = plate; right_pic = _bk["p01"] if turn < 0.5 else _bk["p14"]
    under = _bk["p14"]
    def inked(p, k=0.30): return p * (1 - k * _bk["ink"][..., None]) + 0.0
    glow = np.exp(-((XS - cx) ** 2 / (0.55 * W) ** 2 + (YS - 0.50 * H) ** 2 / (0.35 * H) ** 2))[..., None]
    img = img + glow * np.array([0.10, 0.14, 0.18], np.float32) * 0.8                # the pages light the air
    # page block (thickness) and cover
    cov = np.array([P_(0.11 * W, 0.19 * H), P_(0.5 * W, 0.23 * H), P_(0.89 * W, 0.19 * H), P_(0.91 * W, 0.90 * H), P_(0.5 * W, 0.92 * H), P_(0.09 * W, 0.90 * H)], np.int32)
    cv2.fillPoly(img, [cov], (0.015, 0.018, 0.022), cv2.LINE_AA)
    for k_ in range(6):
        y = 0.86 * H + k_ * 4
        cv2.line(img, (int(P_(0.12 * W, y)[0]), int(P_(0, y)[1])), (int(P_(0.88 * W, y)[0]), int(P_(0, y)[1])), (0.10, 0.12, 0.14), 1, cv2.LINE_AA)
    img = curved(img, inked(left_pic), 0.495 * W, 0.13 * W, 0.20 * H, 0.86 * H)
    img = curved(img, inked(under), 0.505 * W, 0.87 * W, 0.20 * H, 0.86 * H)
    if turn < 1.0:   # the turning leaf: shrinks toward the spine, its back is your clouds photo
        sx = math.cos(math.pi * turn); xe = 0.505 * W + (0.87 * W - 0.505 * W) * sx
        lift = -0.05 * H * math.sin(math.pi * turn)
        tex = inked(right_pic) if sx > 0 else inked(_bk["p08"])[:, ::-1]
        x0, x1 = (0.505 * W, xe) if sx > 0 else (xe, 0.505 * W)
        quad = [P_(x0, 0.20 * H), P_(x1, 0.20 * H + lift), P_(x1, 0.86 * H + lift * 0.3), P_(x0, 0.86 * H)]
        img = F.put_quad(img, np.clip(tex * (0.75 + 0.25 * abs(sx)), 0, 1), quad)
    # spine shadow
    sp = np.exp(-((XS - P_(0.5 * W, 0)[0]) / 18) ** 2) * ((YS > P_(0, 0.20 * H)[1]) & (YS < P_(0, 0.86 * H)[1]))
    img = img * (1 - 0.6 * sp[..., None])
    # her hand: in from the lower right, it lifts the page
    hu = eout((t - 36.6) / 0.9) * (1 - eio((t - 38.9) / 0.9))
    if hu > 0.01:
        d3 = np.array([math.cos(math.radians(-128)), math.sin(math.radians(-128))])
        wr = np.array([1.02 * W, 1.12 * H]) + (np.array([0.80 * W, 0.70 * H]) - np.array([1.02 * W, 1.12 * H])) * hu
        wr = wr + np.array([-0.05 * W, -0.04 * H]) * math.sin(math.pi * turn)
        img, _ = V5.arm_hand(img, t, wr, d3, 0.15, 0.3, (0.6 * W, 0.4 * H), 0.12 * H, light_k=0.25, back_col=(0.20, 0.26, 0.32))
    return img

# 41.56-49.52 "I've got twenty tabs instead / and the words of all the dead": twenty moons across her sky
TABKINDS = ["clouds", "book", "moon", "witch", "heart", "pine", "clouds", "moon", "heart", "book", "witch", "pine", "moon", "clouds", "heart", "book", "moon", "witch", "pine", "clouds"]
_c01 = None
def tab2(img, c, r, kind, t, **kw):
    global _c01
    if kind == "pine":
        if _c01 is None: _c01 = V5._sq(V5._p01, 0.5, 0.40, 0.55)
        return F.pmoon(img, c, r, 0.5, glow=0.06) if r < 6 else _tab_img(img, c, r, _c01, **kw)
    return V5.tab(img, c, r, kind, t, **kw)
def _tab_img(img, c, r, pic, alpha=1.0, halo=0.10, blur=0.0, fill=1.0):
    n = max(8, int(2 * r)); p = np.clip(cv2.resize(pic, (n, n), interpolation=cv2.INTER_AREA) * 1.9 + 0.05, 0, 1)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); rho = np.sqrt((xx - n / 2 + .5) ** 2 + (yy - n / 2 + .5) ** 2) / (n / 2)
    p = p * (1 - 0.35 * np.clip(rho, 0, 1) ** 4)[..., None]; a = np.clip((1 - rho) * n / 2.4 + 0.5, 0, 1)[..., None] * alpha
    img = F.halo(img, c, r, halo * alpha, np.clip(p.mean((0, 1)), 0.2, 1))
    x0, y0 = int(round(c[0] - n / 2)), int(round(c[1] - n / 2)); xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + n), min(H, y0 + n)
    if xb > xa and yb > ya: img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a[ya - y0:yb - y0, xa - x0:xb - x0]) + p[ya - y0:yb - y0, xa - x0:xb - x0] * a[ya - y0:yb - y0, xa - x0:xb - x0]
    return img

TAB3D = []
_rng = np.random.default_rng(20)
for i in range(20):
    a = -1.15 + 2.3 * i / 19
    TAB3D.append((math.sin(a) * 46 + _rng.uniform(-3, 3), 9 + 10 * math.cos(a * 0.8) + _rng.uniform(-2, 2), 60 + 26 * math.cos(a) + _rng.uniform(-6, 6)))
def s_tabs20(t):
    camx = -2.5 + 5.0 * eio((t - 41.56) / 8.0)
    hz = 0.80 * H
    img = F.plain("t20", hz, 0.0, -2.0)
    c = K.cam(z=-2.0, x=camx, hz=hz)
    order = sorted(range(20), key=lambda i: TAB3D[i][0])
    for rank, i in enumerate(order):
        ta = 41.28 + rank * 0.2553
        if t < ta: continue
        X, Y, Z = TAB3D[i]; p, k = K.project(c, X, Z, Y); r = 2.6 * k * (0.55 + 0.45 * eout((t - ta) / 0.18))
        img = tab2(img, p, r, TABKINDS[i], t + i, fill=clamp((t - ta - 0.15) / 0.4), halo=0.08)
    img = F.reflect(img, hz, 0.28, 3.0, t)
    org = np.array([0.20 * W - camx * 18, 0.97 * H]); hgt = 0.42 * H
    fig = figure(t=t, raise_u=0.32, look_u=0.95, wind=0.8, strands=560)
    lit = clamp((t - 41.28) / 5)
    img = F.cast(img, raster2(fig, org, hgt, (H, W))[0], org, (-0.6, -0.10), 0.35 * lit, hz)
    return F.her(img, fig, org, hgt, light=(0.6 * W, 0.2 * H), rim_k=0.5 * lit, fill_k=0.0)

# 49.52-57.44 "She would whisper to the moon / wait for something to come through": something comes through
def s_whisper(t):
    hz = 0.74 * H
    img = F.plain("wh", hz, 0.0, -2.0)
    dcx, dr = 0.56 * W, 0.34 * H; dcy = hz - dr * 0.97
    rip = (dcx - dr * 0.1, dcy + dr * 0.1, t - 53.15) if t >= 53.15 else None
    out_u = eio((t - 53.35) / 1.9)
    img, info = D.draw(img, dcx, dcy, dr, t, interior_scale=1.25, ground_y=hz, fog=0.8, spill=1.2, moon_left=1.0 if out_u <= 0 else 0.0,
                       relight=1.0 - 0.45 * out_u, ripple=rip)
    org = np.array([0.40 * W, 1.05 * H]); hgt = 0.80 * H
    reach = 0.45 * eio((t - 54.6) / 1.2)
    fig = back_figure(t=t, reach_u=reach, wind=0.7, walk=0.0, look_u=0.25)
    tip = org + fig["A"]["hand_tip"] * hgt
    if out_u > 0:      # the moon leaves the picture and comes out through the surface toward her
        m0 = np.array(info["moon"][:2]); r0 = info["moon"][2]
        p = m0 + (tip + np.array([0.02 * W, -0.06 * H]) - m0) * out_u; rr = r0 + (0.055 * H - r0) * out_u
        img = F.halo(img, p, rr, 0.25)
        img = H4.moon_sprite(img, p, rr, 0.08, gain=1.10)
    light = info["moon"][:2] if out_u <= 0 else p
    img = F.her(img, fig, org, hgt, light=(dcx, dcy - dr * 0.4), light_col=np.array(info["col"], np.float32) * 1.2, rim_k=0.9)
    return img

# 57.44-66.15 "I just type a little line / and it finishes mine": she draws a stroke; the rest of the circle draws itself
DRAW_C = np.array([0.60 * W, 0.40 * H]); DRAW_R = 0.17 * H
def _arc_pt(a): return DRAW_C + DRAW_R * np.array([math.cos(a), math.sin(a)])
def s_draw(t):
    # her real clouds (IMG_2269), the moon itself far out of frame: the line is drawn into your own sky
    img = plate_img(11.0 + (t - 57.44) * 0.35, (1.25 * W, -0.55 * H), 0.55 * H)
    img = cv2.GaussianBlur(img, (0, 0), 2.0) * 0.80
    a0, a1 = math.radians(120), math.radians(240)                                # her stroke: the left limb of a crescent
    u = eio((t - 57.50) / 1.35)
    a_tip = a0 + (a1 - a0) * u
    if t > 58.9: a_tip = a1
    ang = -55 + 4 * math.sin(t * 1.2); d3 = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    hd0 = hand4(np.zeros(2), d3, 0.0, V5.SH, 30, rest=1.0); off = hd0["tips"]["index"]
    lower = eio((t - 63.0) / 2.0)
    wr = _arc_pt(a_tip) - off + np.array([0, 0.30 * H]) * lower + np.array([0.0, 1.5 * math.sin(t * 2)])
    stroke_n = 60
    lay = np.zeros((H, W), np.float32)
    pts = np.array([_arc_pt(a0 + (a_tip - a0) * k / stroke_n) for k in range(stroke_n + 1)])
    if u > 0: cv2.polylines(lay, [pts.astype(np.int32)], False, 1.0, 7, cv2.LINE_AA)
    cu = eio((t - 61.30) / 0.75)                                                  # ...and it finishes mine
    if cu > 0:
        pts2 = np.array([_arc_pt(a1 + (2 * math.pi - (a1 - a0)) * cu * k / stroke_n) for k in range(stroke_n + 1)])
        lay2 = np.zeros((H, W), np.float32); cv2.polylines(lay2, [pts2.astype(np.int32)], False, 1.0, 5, cv2.LINE_AA)
        img = img + (lay2[..., None] + cv2.GaussianBlur(lay2, (0, 0), 6)[..., None] * 1.2) * np.array([0.95, 0.85, 0.70], np.float32) * 0.8 * (1 - eio((t - 62.07) / 0.3))
    fill = eio((t - 62.07) / 0.25)
    rise = eio((t - 63.2) / 2.8)
    mc = DRAW_C + np.array([0.03 * W, -0.16 * H]) * rise; mr = DRAW_R * (1 - 0.35 * rise)
    if fill > 0:
        img = F.pmoon(img, mc, mr, 0.5, glow=0.20 * fill + 0.6 * math.exp(-((t - 62.07) / 0.10) ** 2), alpha=fill)
    img = img + (lay[..., None] + cv2.GaussianBlur(lay, (0, 0), 6)[..., None] * 1.3) * MOONCOL * 0.85 * (1 - fill)
    tipl = _arc_pt(a_tip) if fill <= 0 else mc
    img, _ = V5.arm_hand(img, t, wr, d3, 0.0, 0.0, tipl, 0.05 * H if fill <= 0 else mr, light_k=0.8)
    return img

# 66.15-70.24: lunar phases, abstract and rhythmic: the cycle rolls one step per beat, then all complete
def s_phases(t):
    img = F.night("ph", clouds=0.15)
    k = int((t - 66.15) / BEAT); fr = clamp(((t - 66.15) / BEAT - k) / 0.18)
    done = t >= 70.24 - BEAT * 0.5
    for i in range(8):
        p = ((i + k + eout(fr)) / 8.0) % 1.0
        if done: p = 0.5
        c = (W * (0.5 + (i - 3.5) * 0.118), 0.50 * H + 0.03 * H * math.sin(i * 0.9 + t))
        img = F.pmoon(img, c, 0.066 * H, p, glow=0.06)
    return img

# 70.24-74.24 "...give the darkness a name": she faces the dark door; on "name" it lights
def s_name(t):
    hz = 0.80 * H
    img = F.plain("nm", hz, 4.0, -2.0)
    on = t >= 73.68
    dcx, dr = 0.70 * W, 0.30 * H; dcy = hz - dr * 0.97
    img, info = D.draw(img, dcx, dcy, dr, t, interior_scale=1.25, ground_y=hz, fog=0.6 if on else 0.2, spill=1.2 if on else 0.3,
                       moon_left=1.0, relight=1.0 if on else 0.10, ripple=(dcx, dcy, t - 73.68) if on else None)
    org = np.array([0.30 * W, 0.94 * H]); hgt = 0.50 * H
    fig = figure(t=t, raise_u=0.30 + 0.25 * eio((t - 73.2) / 0.4), look_u=0.45, wind=0.8)
    light = (dcx, dcy); col = np.array(info["col"], np.float32) * (1.4 if on else 0.4)
    img = F.cast(img, raster2(fig, org, hgt, (H, W))[0], org, (-1.4, -0.12), 0.5 if on else 0.15, hz)
    img = F.reflect(img, hz, 0.25, 3.0, t)
    return F.her(img, fig, org, hgt, light=light, light_col=col, rim_k=0.9)

# ============================================================ CHORUS ENGINE
CH1 = dict(name="ch1", h=[74.35, 74.83], ex=75.31, D=76.37, c=[78.29, 78.85], cj=79.33, tell=80.40, hb=[82.48, 82.96], exb=83.44, D2=84.50,
           price=89.52, end=92.67, rev=False)
CH2 = dict(name="ch2", h=[151.58, 152.06], ex=152.54, D=153.60, c=[155.52, 156.08], cj=156.56, tell=157.60, hb=[159.66, 160.14], exb=160.62, D2=161.68,
           price=166.64, end=169.78, rev=True)
ARC = [(0.62 * W + 0.30 * W * math.cos(math.radians(a)), 0.62 * H + 0.40 * H * math.sin(math.radians(a))) for a in np.linspace(205, 335, 7)]
def ch_wide(t, cfg, mode):
    """the chorus stage: her on the wet plain, the moon(s) in her sky. mode: 'hook' | 'door' | 'sky'"""
    rev = cfg["rev"]; hz = 0.80 * H
    img = F.plain("chw", hz, 0.0, -2.0, far_door=False)
    lag = 0.28 if rev else 0.0; lead = 0.0 if rev else 0.06
    acts = cfg["h"] + [cfg["ex"]]
    # her flick: she acts (ch1) / she reacts, late (ch2)
    ru = F.flick(t, [a + lag for a in acts], lead=lead, up=0.85)
    if t > cfg["ex"] + lag: ru = max(ru, 0.30 + 0.45 * (1 - eio((t - cfg["ex"] - lag - 0.6) / 0.8)))
    org = np.array([0.24 * W, 0.93 * H]) if not rev else np.array([0.25 * W, 1.24 * H]); hgt = 0.50 * H if not rev else 0.80 * H
    mtime = lambda x: x if rev else x + 0.03                 # the moon answers instantly (ch1) / moves first (ch2)
    M0 = np.array([0.66 * W, 0.30 * H]); R0 = 0.17 * H
    moons = []
    if mode == "hook":
        if t < mtime(cfg["h"][0]): moons = [(M0, R0, 0.5)]
        elif t < mtime(cfg["h"][1]): moons = [(M0, R0, 0.18)]
        elif t < mtime(cfg["ex"]): moons = [(M0, R0, 0.82)]
        else:
            u = eout((t - mtime(cfg["ex"])) / 0.28); drift = (t - cfg["ex"]) * 0.010
            for i, P_ in enumerate(ARC):
                Pd = np.array(P_) + np.array([math.cos(drift + i), math.sin(drift * 1.3 + i)]) * 4
                moons.append((M0 + (Pd - M0) * u, R0 + (0.075 * H - R0) * u, (0.12 + i * 0.127) % 1.0))
    elif mode == "door":
        for i, P_ in enumerate(ARC):
            u = eio((t - cfg["cj"] + 0.10) / 0.22)
            if u < 1: moons.append((np.array(P_) + (np.array([0.70 * W, 0.52 * H]) - np.array(P_)) * u, 0.075 * H * (1 - 0.7 * u), (0.12 + i * 0.127) % 1.0))
    elif mode == "sky":
        n = 28; ctr = np.array([0.70 * W, 0.50 * H]) if not rev else org + np.array([0.02 * W, -0.55 * hgt])
        for i in range(n):
            a = i / n * 2 * math.pi + (t - cfg["D2"]) * (0.10 if not rev else -0.16)
            rr_ = (0.36 + 0.06 * math.sin(i * 2.1)) * W * (1 if not rev else 0.80)
            p = ctr + np.array([math.cos(a) * rr_, math.sin(a) * rr_ * 0.42])
            dark = eio((t - cfg["price"]) / 0.12) * (i != 3)
            moons.append((p, (0.030 + 0.012 * math.sin(i * 1.3)) * H, 0.5 - 0.48 * dark))
    for p, r, ph in moons:
        if mode == "sky" and rev: img = V5.tab(img, p, r, "witch", t, fill=1.0, halo=0.06, alpha=1.0 - 0.75 * eio((t - cfg["price"]) / 0.12))
        else: img = F.pmoon(img, p, r, ph, glow=0.12)
    if mode == "hook" and t >= mtime(cfg["ex"]):     # the plain lights in a sweep on EXECUTE
        sw = (t - mtime(cfg["ex"])) / 0.55
        if 0 <= sw <= 1.3:
            band = np.exp(-((XS - (-0.1 + 1.2 * sw) * W) / (0.10 * W)) ** 2) * (YS > hz)
            img = img + (band * 0.20 * (1 - clamp(sw - 0.3)))[..., None] * MOONCOL
    info = None
    if mode in ("door", "sky"):
        dcx, dr = 0.70 * W, 0.27 * H; dcy = hz - dr * 0.97
        app = eio((t - cfg["cj"]) / 0.20) if mode == "door" else 1.0
        if app > 0:
            img, info = D.draw(img, dcx, dcy, dr * (0.6 + 0.4 * app), t, interior_scale=1.25, ground_y=hz, fog=0.6, spill=1.0 * app, moon_left=1.0,
                               relight=app * (1 - 0.8 * eio((t - cfg["price"]) / 0.12) * (mode == "sky")),
                               ripple=(dcx, dcy, t - cfg["cj"]) if t - cfg["cj"] < 1.6 else None)
            # inside the door: her, small (ch1: an echo that follows her) / her duplicate (ch2: it moves first)
            if mode == "door":
                dl = -0.40 if not rev else 0.40
                fr_ = eio((t - cfg["tell"] - dl) / 0.6) if True else 0
                f2 = F.mirror(figure(t=t, raise_u=0.30 + 0.5 * fr_, look_u=0.3, wind=0.7, strands=200))
                hh = dr * (0.75 if rev else 0.45)
                a2, sh2 = raster2(f2, np.array([dcx + dr * 0.15, dcy + dr * 0.92]), hh, (H, W))
                a2 = a2 * info["m"] * app
                img = img * (1 - a2[..., None]) + K.INK * a2[..., None]
    img = F.reflect(img, hz, 0.30, 3.0, t)
    # her
    if mode == "door":
        tl = cfg["tell"] + (0.0 if not rev else 0.40)
        ru = 0.30 + 0.5 * eio((t - tl) / 0.6)
    elif mode == "sky":
        ru = 0.30 + 0.30 * math.sin((t - cfg["D2"]) * 0.8) ** 2
    fig = figure(t=t, raise_u=ru, look_u=0.70, wind=0.9, strands=560)
    light = (0.62 * W, 0.30 * H) if info is None else (0.70 * W, 0.45 * H)
    img = F.cast(img, raster2(fig, org, hgt, (H, W))[0], org, (-0.9, -0.12), 0.35, hz)
    img = F.her(img, fig, org, hgt, light=light, rim_k=0.6)
    return img[:, ::-1].copy() if rev else img

def ch_click(t, cfg, which):
    img = F.night("clk", clouds=0.25)
    if which == 0:
        if cfg["rev"]:
            img = V5.tab(img, (0.32 * W, 0.50 * H), 0.36 * H, "witch", t, fill=1.0, halo=0.08)
            img = V5.tab(img, (0.80 * W, 0.42 * H), 0.24 * H, "witch", t + 0.4, fill=1.0, halo=0.08)
        else:
            img = F.pmoon(img, (0.32 * W, 0.52 * H), 0.40 * H, 0.27, glow=0.08)
            img = F.pmoon(img, (0.82 * W, 0.40 * H), 0.24 * H, 0.38, glow=0.08)
    else:
        if cfg["rev"]:      # her hand, yanked open by something we don't see
            img = V5.sky_bg(6.0)
            yank = eout((t - cfg["c"][1]) / 0.12)
            d3 = np.array([math.cos(math.radians(-70 + 25 * yank)), math.sin(math.radians(-70 + 25 * yank))])
            img, _ = V5.arm_hand(img, t, np.array([0.42 * W, 0.80 * H]) + np.array([0.04 * W, -0.10 * H]) * yank, d3, 1 - yank, 0.6 * yank,
                                 (0.65 * W, 0.25 * H), 0.05 * H, light_k=0.6)
            img = F.pmoon(img, (0.66 * W + 0.05 * W * yank, 0.22 * H - 0.05 * H * yank), 0.05 * H, 0.5, glow=0.2)
        else:
            img = F.pmoon(img, (0.70 * W, 0.50 * H), 0.62 * H, 0.73, glow=0.06)
            img = F.pmoon(img, (0.18 * W, 0.30 * H), 0.12 * H, 0.62, glow=0.08)
    return img

def ch_hand(t, cfg):
    """second HEX HEX EXECUTE, close on her hand: moons pop at her fingertip (ch1) / before her finger moves (ch2)"""
    rev = cfg["rev"]
    img = V5.sky_bg(6.0)
    lag = 0.25 if rev else 0.0
    fl = 0.0
    for h_ in cfg["hb"] + [cfg["exb"]]:
        u = (t - (h_ + lag - (0 if rev else 0.05))) / 0.22
        if 0 <= u <= 1: fl = max(fl, math.sin(math.pi * u))
    ang = -60 + 14 * fl; d3 = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    wr = hand_xy(t, (0.40 * W, 0.86 * H))
    hd0 = hand4(wr, d3, 0.0, V5.SH, 30, rest=1.0); tip = hd0["tips"]["index"]
    pops = []
    for k_, h_ in enumerate(cfg["hb"]):
        tp = h_ - (0.25 if rev else -0.03)
        if t >= tp: pops.append((k_, tp))
    for k_, tp in pops:
        p = tip + np.array([0.07 * W * (k_ + 1), -0.10 * H * (k_ + 1)]) * eout((t - tp) / 0.3)
        img = F.pmoon(img, p, 0.05 * H * eout((t - tp) / 0.15), 0.5, glow=0.2)
    te = cfg["exb"] - (0.25 if rev else -0.03)
    if t >= te:    # EXECUTE: a stream of moons rises out of her hand into the sky
        for i in range(14):
            s0 = te + i * 0.05; u = (t - s0) / 1.2
            if u <= 0: continue
            p = tip + np.array([(0.05 + 0.025 * math.sin(i * 2.3)) * W * u * (i % 3 + 1), -1.1 * H * u])
            img = F.pmoon(img, p, (0.03 + 0.01 * (i % 3)) * H, 0.5, glow=0.15)
    img, _ = V5.arm_hand(img, t, wr, d3, 0.0, 0.2, tip + np.array([0.05 * W, -0.08 * H]), 0.05 * H, light_k=0.6 + 0.4 * (len(pops) > 0))
    return img

def s_chorus(t, cfg):
    c1, c2 = cfg["c"]
    if t < c1: return ch_wide(t, cfg, "hook")
    if t < c2: return ch_click(t, cfg, 0)
    if t < cfg["cj"]: return ch_click(t, cfg, 1)
    if t < cfg["hb"][0] - 0.12: return ch_wide(t, cfg, "door")
    if t < cfg["D2"]: return ch_hand(t, cfg)
    return ch_wide(t, cfg, "sky")

# ============================================================ POST: autocomplete
def s_autoc(t, rev=False):
    img = F.night("ac", clouds=0.20)
    t0 = 169.78 if rev else 92.67
    pull = eio((t - (t0 + 6.0)) / 4.0) if not rev else 0.0
    sc = 1.0 - 0.18 * pull
    mc = np.array([0.5 * W, 0.47 * H]); mr = 0.32 * H * sc
    if not rev:
        ghost = 0.7 * eio((t - 94.6) / 0.4) * (0.75 + 0.25 * math.cos((t - 94.6) / BEAT * math.pi * 2))
        solid = eio((t - 96.56) / 0.14)
        p = 0.17 + (0.5 - 0.17) * solid
        img = F.pmoon(img, mc, mr, p, ghost=ghost * (1 - solid), glow=0.18, earthshine=0.06)
        if t >= 96.56: img = F.halo(img, mc, mr, 0.5 * math.exp(-((t - 96.56) / 0.12) ** 2))
        show = t >= 97.52; done = eio((t - 98.75) / 0.18)
    else:
        img = F.pmoon(img, mc, mr, 0.5, glow=0.18)
        show = True; done = 0.5 * eio((t - 173.68) / 0.15) + 0.5 * eio((t - 174.64) / 0.15)
    if show:
        hgt = 0.78 * H * sc; org = mc + np.array([-0.04 * W, 0.62 * H]) * sc
        fig = figure(t=t, raise_u=0.62, look_u=0.85, wind=1.0, strands=560)
        a, sh = raster2(fig, org, hgt, (H, W))
        if not rev:   # half of her is drawn, the rest is a suggestion until it is accepted
            cut = org[1] - hgt * (0.45 + 0.55 * done)
            solid_m = np.clip((YS - cut) / 6, 0, 1)
        else:         # the world completes her, in two steps, from the ground up
            cut = org[1] - hgt * (0.30 + 0.35 * eio((t - 173.68) / 0.15) + 0.40 * eio((t - 174.64) / 0.15))
            solid_m = np.clip((YS - cut) / 6, 0, 1)
        am = a * (solid_m + (1 - solid_m) * 0.0)
        img = img * (1 - am[..., None]) + (K.INK + (img - K.INK) * (sh * 0.42)[..., None]) * am[..., None]
        ghost_a = a * (1 - solid_m)
        img = F.trace(img, ghost_a, 1.0, col=np.array([0.95, 0.85, 0.70], np.float32), width=2, amt=0.55, glow=False)
        img = img + (ghost_a * 0.10)[..., None] * np.array([0.95, 0.85, 0.70], np.float32)
    return img

# 102.82-106.90: back to your real moon... and the whole frame turns over like a card
_fold_face = {}
def s_realfold(t):
    pt = 13.0 + (t - 102.82) * 0.5
    img = plate_img(pt, (0.5 * W, 0.47 * H), 0.22 * H)
    u = eio((t - 104.86) / 1.6)
    if u <= 0: return img
    bg = F.plain("c1", 0.74 * H, 0.0, -2.0)
    tgt_c = np.array([0.30 * W, 0.80 * H - 0.21 * H]); tw, th = 0.15 * W, 0.42 * H
    cw = W + (tw - W) * u; chh = H + (th - H) * u
    cc = np.array([0.5 * W, 0.5 * H]) + (tgt_c - np.array([0.5 * W, 0.5 * H])) * u
    flip = 1.0 - 0.5 * math.sin(math.pi * u)            # it turns once as it shrinks
    face = cv2.resize(img, (int(max(cw, 8)), int(max(chh, 8))), interpolation=cv2.INTER_AREA)
    bg = bg * eio((u - 0.2) / 0.6) + img * (1 - eio((u - 0.2) / 0.6)) * 0.3
    return F.card(bg, cc, cw, chh, face, flip=flip if u < 0.999 else 1.0)

# ============================================================ ACT II
_cf = {}
def card_faces():
    if _cf: return _cf
    tw, th = int(0.15 * W), int(0.42 * H)
    _cf["moon"] = F.card_face(tw, th, plate_img(13.0, (0.5 * W, 0.47 * H), 0.32 * H)[:, int(0.5 * W - 0.29 * H):int(0.5 * W + 0.29 * H)])
    _cf["book"] = F.card_face(tw, th, V5.book_patch(400, 0.3))
    pic = F.night("cfb"); 
    for i in range(5): pic = V5.tab(pic, (W * (0.5 + (i - 2) * 0.17), H * 0.5), 0.07 * H, V5.KINDS[i], 1.0, fill=1.0, halo=0.05)
    _cf["tabs"] = F.card_face(tw, th, np.clip(pic[:, int(0.5 * W - 0.5 * H):int(0.5 * W + 0.5 * H)] * 1.6 + 0.04, 0, 1))
    _cf["blank"] = F.card_face(tw, th, np.full((th, tw, 3), 0.72, np.float32) * np.array([0.92, 0.95, 0.98], np.float32))
    p = F.night("cfh", top=(0.10, 0.12, 0.16), bot=(0.20, 0.22, 0.26)); p = F.pmoon(p, (0.5 * W, 0.45 * H), 0.30 * H, 0.5, glow=0.1)
    p = F.her(p, figure(t=3.0, raise_u=0.55, look_u=0.8, wind=0.8), (0.47 * W, 0.98 * H), 0.80 * H, silhouette=True)
    _cf["her"] = F.card_face(tw, th, p[:, int(0.5 * W - 0.42 * H):int(0.5 * W + 0.42 * H)])
    hp = V5.s5(18.6)
    _cf["hand"] = F.card_face(tw, th, hp[:, int(0.42 * W - 0.42 * H):int(0.42 * W + 0.42 * H)])
    return _cf
CARD_X = [0.30, 0.50, 0.70]
def s_cards1(t):     # 106.90-118.96: three cards stand on the plain; she walks to them; "clear the context page"
    hz = 0.74 * H
    img = F.plain("c1", hz, 0.0, -2.0)
    cf = card_faces(); tw, th = 0.15 * W, 0.42 * H
    faces = [cf["moon"], cf["book"], cf["tabs"]]
    for i, x in enumerate(CARD_X):
        wipe = clamp((t - (114.96 + i * 0.26)) / 0.35)
        f = faces[i]
        if wipe > 0:
            cut = int(f.shape[0] * wipe); f = f.copy(); f[:cut] = cf["blank"][:cut]
            edge = min(cut, f.shape[0] - 1); f[max(0, edge - 2):edge + 2] = 0.95
        flip = 1.0 - eio((t - (117.94 + i * 0.255)) / 0.30)
        c = np.array([x * W, 0.80 * H - th / 2])
        img = F.card(img, c, tw, th, f, flip=flip)
    img = F.reflect(img, hz, 0.30, 2.5, t)
    z = 9.5 + 5.0 * eio((t - 107.0) / 7.5)
    c = K.cam(z=-2.0, hz=hz); feet, kk = K.project(c, -0.2, z)
    fig = back_figure(t=t, reach_u=0.0, wind=0.7, walk=1.0 if 107.0 < t < 114.5 else 0.0)
    img = F.her(img, fig, feet, 1.7 * kk, light=(0.5 * W, 0.40 * H), light_col=np.array([0.7, 0.75, 0.8], np.float32), rim_k=0.8)
    return push(img, t, 106.9, 118.96, 1.14, (0.5 * W, 0.62 * H))

_last = {"img": None}
def s_cards2(t):     # 118.96-126.24: "used to read the tarot spread / now it reads me back instead"
    hz = 0.70 * H
    img = F.plain("c2", hz, 0.0, -2.0)
    cf = card_faces(); tw, th = 0.20 * W, 0.56 * H
    rec = _last["img"] if _last["img"] is not None else img
    rec_face = F.card_face(int(tw), int(th), rec[:, int(0.5 * W - 0.37 * H):int(0.5 * W + 0.37 * H)])
    faces = [cv2.resize(cf["her"], (int(tw), int(th))), rec_face, cv2.resize(cf["hand"], (int(tw), int(th)))]
    for i, x in enumerate([0.27, 0.53, 0.79]):
        fl = eio((t - (123.04 + i * BEAT)) / 0.22)          # they turn themselves over before her hand arrives
        img = F.card(img, np.array([x * W, 0.86 * H - th / 2]), tw, th, faces[i], flip=fl)
    img = F.reflect(img, hz, 0.28, 2.5, t)
    reach = 0.75 * eio((t - 120.5) / 2.2) if t < 123.0 else 0.75 * eio((123.0 - 120.5) / 2.2)
    org = np.array([0.08 * W, 1.32 * H]); hgt = 1.05 * H
    fig = back_figure(t=t, reach_u=reach, wind=0.6, walk=0.0, look_u=0.2)
    img = F.her(img, fig, org, hgt, light=(0.5 * W, 0.40 * H), light_col=np.array([0.7, 0.75, 0.8], np.float32), rim_k=0.8)
    _last["img"] = img
    return img

def s_request(t):    # 126.24-133.0 "I requested endless wealth / perfect love and perfect health"
    hz = 0.80 * H
    img = F.plain("rq", hz, -3.0, -2.0)
    org = np.array([0.36 * W, 0.95 * H]); hgt = 0.55 * H
    arrive = 127.55
    ru = 0.28 + 0.30 * eio((t - 127.0) / 0.9) if t < arrive else 0.28 + 0.30 * eio((arrive - 127.0) / 0.9)
    fig = figure(t=t if t < arrive else arrive + (t - arrive) * 0.15, raise_u=ru, look_u=0.55, wind=0.8 if t < arrive else 0.3)
    hand = org + fig["A"]["moon_c"] * hgt
    kinds = ["clouds", "heart", "moon"]
    for i in range(3):
        u = eio((t - (126.0 + i * 0.25)) / 1.3)
        tgt = hand + np.array([(i - 1) * 0.085 * W + 0.06 * W, -0.10 * H - 0.03 * H * (i == 1)])
        src = np.array([tgt[0] + (i - 1) * 0.1 * W, -0.1 * H])
        p = src + (tgt - src) * u + np.array([0, 0.004 * H * math.sin(t * 2 + i)])
        img = V5.tab(img, p, 0.045 * H, kinds[i], t, fill=eio((t - 128.64 - i * 0.6) / 0.4), halo=0.12)
    img = F.reflect(img, hz, 0.28, 3.0, t)
    img = F.cast(img, raster2(fig, org, hgt, (H, W))[0], org, (-0.9, -0.12), 0.3, hz)
    return F.her(img, fig, org, hgt, light=hand + np.array([0.06 * W, -0.10 * H]), rim_k=0.9, fill_k=0.08)

def s_reflect(t):    # 133.0-143.28 "It said tell me what you fear / so I whispered in its ear": the reflection moves first
    hz = 0.66 * H
    img = F.plain("rf", hz, 2.0, -2.0, far_door=False)
    org = np.array([0.42 * W, hz + 0.02 * H]); hgt = 0.52 * H
    def pose(tt): return dict(raise_u=0.35 + 0.15 * eio((tt - 136.5) / 1.0) + 0.35 * eio((tt - 141.2) / 0.9), look_u=0.30 - 0.35 * eio((tt - 138.6) / 0.8), wind=0.6)
    ear = org + np.array([0.035 * W, -0.88 * hgt])
    mc = org + np.array([0.13 * W, -0.86 * hgt]) + (ear - (org + np.array([0.13 * W, -0.86 * hgt]))) * eio((t - 138.3) / 1.2) * (1 - eio((t - 141.0) / 1.5)) + np.array([0, 0.006 * H * math.sin(t * 1.4)])
    pulse = 1.0 + 0.8 * sum(math.exp(-((t - ta) / 0.12) ** 2) for ta in (133.4, 134.2, 135.0))
    img = F.pmoon(img, mc, 0.035 * H, 0.5, glow=0.25 * pulse)
    fig = figure(t=t, **pose(t if t < 141.0 else 141.0 + (t - 141.0) * 0.0))
    figr = figure(t=t + 0.6, **pose(t + 0.6))                     # the reflection is 0.6 s ahead of her
    ar, _ = raster2(figr, org, hgt, (H, W), flip_y=True)
    ar = cv2.GaussianBlur(ar, (0, 0), 1.5)
    rip = (np.sin(YS * 0.15 + t * 3) * 2.0).astype(np.float32)
    ar = cv2.remap(ar, XS + rip, YS, cv2.INTER_LINEAR) * (YS > hz) * np.clip(1 - (YS - hz) / (0.6 * H), 0, 1)
    sheen = np.exp(-(((XS - 0.48 * W) / (0.32 * W)) ** 2 + ((YS - hz - 0.16 * H) / (0.14 * H)) ** 2)) * (YS > hz)
    img = img + (sheen * 0.16)[..., None] * MOONCOL                  # moonlight on the wet ground, so her reflection reads
    img = F.reflect(img, hz, 0.25, 3.0, t)
    img = img * (1 - 0.80 * ar[..., None])
    img = F.her(img, fig, org, hgt, light=mc, rim_k=1.0, fill_k=0.10)
    return push(img, t, 133.0, 143.28, 1.22, (0.46 * W, 0.62 * H))

MEM_T = [143.28, 143.60, 143.84, 144.48, 144.64, 144.96, 145.52, 145.76, 146.56, 146.88, 147.60, 147.92, 148.56, 148.80, 149.60, 149.84, 150.00, 150.24, 150.32, 150.48]
def s_memory(t):     # 143.28-151.53 "no more cauldron... everything I've typed and crossed out"
    img = F.night("mem", clouds=0.18)
    dark = eio((t - 150.88) / 0.10)
    for i, ta in enumerate(MEM_T):
        if t < ta: continue
        row, col = divmod(i, 5)
        p = np.array([W * (0.22 + col * 0.14 + 0.03 * (row % 2)), H * (0.26 + row * 0.16)])
        r = 0.050 * H * eout((t - ta) / 0.12)
        img = V5.tab(img, p, r, V5.KINDS[i % 5], t + i, fill=1.0, halo=0.06, alpha=1.0 - 0.8 * dark)
    lu = eio((t - 150.40) / 0.40)
    if lu > 0:   # crossed out
        y = int(0.50 * H); x1 = int(W * (0.12 + 0.76 * lu))
        lay = np.zeros((H, W), np.float32); cv2.line(lay, (int(0.12 * W), y), (x1, y), 1.0, 3, cv2.LINE_AA)
        img = img + (lay + cv2.GaussianBlur(lay, (0, 0), 6) * 1.2)[..., None] * MOONCOL * (1 - 0.7 * dark)
    return img

# ============================================================ ACT III
def mirror_pair(t, pose_l, pose_r, hz=0.80 * H, line=True, moon=True, extra=None, alpha_l=None):
    """Act III: she and her duplicate, large, backlit by one giant moon that the seam between them splits in two"""
    img = F.night("mpb", top=(0.030, 0.034, 0.044), bot=(0.11, 0.12, 0.145), clouds=0.22)
    mc = (0.5 * W, 0.44 * H); img = F.pmoon(img, mc, 0.40 * H, 0.5, glow=0.16, gain=0.95)
    if line:
        lay = np.exp(-((XS - 0.5 * W) / 1.4) ** 2)
        img = img * (1 - 0.55 * np.exp(-((XS - 0.5 * W) / 5.0) ** 2))[..., None] + (lay * 0.65)[..., None] * MOONCOL
    hgt = 1.02 * H
    fl = figure(t=t, strands=560, **pose_l); fr = F.mirror(figure(t=t, strands=560, **pose_r))
    ol = np.array([0.27 * W, 1.30 * H]); orr = np.array([0.73 * W, 1.30 * H])
    img = F.her(img, fr, orr, hgt, light=mc, rim_k=0.35)
    if extra is not None: img = extra(img, fl, ol, hgt)
    img, al = F.her(img, fl, ol, hgt, light=mc, rim_k=0.35, alpha_mul=alpha_l, ret_alpha=True)
    return img, fl, ol, hgt

def _p(tt, a=0.0):
    """her slow, deliberate gestures in the bridge"""
    g = 0.30 + 0.32 * eio((tt - 177.5) / 1.6) * (1 - eio((tt - 181.0) / 1.6)) + 0.38 * eio((tt - 184.7) / 0.9) * (1 - eio((tt - 186.4) / 0.9)) \
        + 0.30 * eio((tt - 188.8) / 0.9) * (1 - eio((tt - 190.6) / 1.0))
    return dict(raise_u=g, look_u=0.35 + 0.3 * math.sin(tt * 0.4) ** 2, wind=0.7)

def s_mirror(t):     # 175.87-192.03: they mirror; then it moves first and she follows; her future is drawn before she moves
    lead = 0.0 if t < 184.0 else 0.55 * eio((t - 184.0) / 0.4)
    def ex(img, fl, ol, hgt):
        if 188.4 <= t < 190.2:      # her next pose, drawn as a line before she moves into it
            fut = figure(t=t, strands=200, **_p(t + 0.9 - lead))
            a, _ = raster2(fut, ol, hgt, (H, W))
            img = F.trace(img, a, eio((t - 188.4) / 0.9), amt=0.8 * (1 - eio((t - 189.6) / 0.6)))
        return img
    img, *_ = mirror_pair(t, _p(t - lead), _p(t), extra=ex, moon=False)
    return push(img, t, 175.87, 192.03, 1.10, (0.5 * W, 0.44 * H))

def s_shadow(t):     # 192.03-200.11 "I asked it who was in control / it asked me to define a soul": her shadow moves first
    hz = 0.58 * H
    img = F.plain("sh", hz, 0.0, -2.0, far_door=False)
    dcx, dr = 0.86 * W, 0.18 * H; dcy = hz - dr * 0.97
    img, info = D.draw(img, dcx, dcy, dr, t, interior_scale=1.25, ground_y=hz, fog=0.5, spill=1.4, moon_left=1.0, relight=1.0)
    org = np.array([0.52 * W, 0.80 * H]); hgt = 0.48 * H
    def pz(tt): return dict(raise_u=0.28 + 0.45 * eio((tt - 193.4) / 0.8) * (1 - eio((tt - 195.3) / 0.8)) + 0.40 * eio((tt - 197.3) / 0.8) * (1 - eio((tt - 199.0) / 0.8)),
                             look_u=0.4, wind=0.6)
    fig = F.mirror(figure(t=t, **pz(t)))
    sfig = F.mirror(figure(t=t + 0.7, **pz(t + 0.7)))          # the shadow is 0.7 s ahead of her
    sa, _ = raster2(sfig, org, hgt, (H, W))
    img = F.cast(img, sa, org, (-2.6, -0.42), 0.80, hz)
    img = F.reflect(img, hz, 0.15, 3.0, t)
    return F.her(img, fig, org, hgt, light=(dcx, dcy), light_col=np.array(info["col"], np.float32) * 1.3, rim_k=1.0)

def s_line(t):       # 200.11-208.14 "I asked it if my fate was mine / it said of course, then drew the line"
    pl = _p(t); pr = dict(raise_u=0.30 + 0.45 * eio((t - 205.6) / 0.4), look_u=0.40, wind=0.7)
    img, fl, ol, hgt = mirror_pair(t, pl, pr, line=False)
    fr = F.mirror(figure(t=t, **pr)); tip = np.array([0.73 * W, 1.30 * H]) + fr["A"]["moon_c"] * hgt
    lu = eio((t - 206.30) / 0.80)
    if lu > 0:
        y = int(tip[1]); x1 = int(tip[0] - (tip[0] + 10) * lu)
        lay = np.zeros((H, W), np.float32); cv2.line(lay, (int(tip[0]), y), (x1, y), 1.0, 2, cv2.LINE_AA)
        img = img + (lay + cv2.GaussianBlur(lay, (0, 0), 5) * 1.3)[..., None] * MOONCOL
        dk = eio((t - 207.12) / 0.25) * (YS < y - 3)
        img = img * (1 - 0.85 * dk[..., None])
    return img

# ---------------- recursion ----------------
def paste_in(outer, inner, hc, hr, edge=True):
    k = hr / (0.46 * H)
    M = np.float32([[k, 0, hc[0] - k * W / 2], [0, k, hc[1] - k * H / 2]])
    wv = cv2.warpAffine(inner, M, (W, H), flags=cv2.INTER_AREA)
    d = np.sqrt((XS - hc[0]) ** 2 + (YS - hc[1]) ** 2) / hr
    m = np.clip((1 - d) * hr / 1.5 + 0.5, 0, 1)[..., None]
    out = outer * (1 - m) + wv * m
    if edge: out = out * (1 - 0.6 * np.exp(-((d - 1) * hr / 3) ** 2))[..., None]
    return out

def zoom_view(img, c, z):
    M = np.float32([[z, 0, W / 2 - z * c[0]], [0, z, H / 2 - z * c[1]]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

_dr = {}
def droste_base():
    if "base" in _dr: return _dr["base"]
    hz = 0.78 * H; img = F.plain("dr", hz, 0.0, -2.0, far_door=False)
    dcx, dr = 0.5 * W, 0.30 * H; dcy = hz - dr * 0.97
    mn = D.MENISCUS; D.MENISCUS = 0.0
    img, info = D.draw(img, dcx, dcy, dr, 1.0, interior_scale=1.25, ground_y=hz, fog=0.6, spill=1.2, moon_left=1.0, relight=1.0, thickness_side=1.0)
    D.MENISCUS = mn
    fig = figure(t=1.0, raise_u=0.55, look_u=0.6, wind=0.7)
    img = F.her(img, fig, (0.40 * W, hz + 0.03 * H), 0.30 * H, light=(dcx, dcy), rim_k=0.9)
    comp = img
    for _ in range(5): comp = paste_in(img, comp, (dcx, dcy), dr * 0.985, edge=False)
    _dr["base"] = (comp, (dcx, dcy), dr * 0.985)
    return _dr["base"]

def s_droste(t, t0, jump=0.0):
    comp, hc, hr = droste_base(); k = hr / (0.46 * H)
    ph = ((t - t0) / (BEAT * 2) + jump) % 1.0
    z = (1 / k) ** ph
    v = zoom_view(comp, hc, z)
    return v

# ---------------- final chorus ----------------
def s_trio(t, hooks, ex, appear=None):
    hz = 0.80 * H
    img = F.plain("tr", hz, 0.0, -2.0, far_door=False)
    pos = [(0.62 * W, 0.86 * H, 0.32 * H), (0.42 * W, 0.90 * H, 0.42 * H), (0.20 * W, 0.97 * H, 0.56 * H)]
    for i, (x, y, h_) in enumerate(pos):
        mp = np.array([x + 0.20 * h_, y - 1.25 * h_])
        split = t >= ex
        if appear is not None and t < appear[i]: continue
        acted = t >= hooks[i] if i < len(hooks) else split
        if not split: img = F.pmoon(img, mp, 0.12 * h_, 0.5 if not acted else 0.15, glow=0.15)
        else:
            u = eout((t - ex) / 0.25)
            for j in range(3): img = F.pmoon(img, mp + np.array([(j - 1) * 0.35 * h_ * u, -0.15 * h_ * u * (j != 1)]), 0.10 * h_, (0.2 + j * 0.3) % 1, glow=0.15)
    img = F.reflect(img, hz, 0.28, 3.0, t)
    for i, (x, y, h_) in enumerate(pos):
        if appear is not None and t < appear[i]: continue
        ru = F.flick(t, [hooks[i]] if i < len(hooks) else [], up=0.85) if t < ex else 0.30 + 0.5 * eio((t - ex) / 0.25)
        fig = figure(t=t + i * 0.37, raise_u=ru, look_u=0.6, wind=0.9, strands=420)
        img = F.her(img, fig, (x, y), h_, light=(x + 0.2 * h_, y - 1.25 * h_), rim_k=0.6)
        if appear is not None and appear[i] <= t < appear[i] + 0.35:
            a, _ = raster2(fig, np.array([x, y]), h_, (H, W)); img = F.trace(img, a, 1.0, amt=1.2 * (1 - (t - appear[i]) / 0.35))
    return img

def s_drawn(t):      # 213.15-216.20 "conjure it, now it's conjuring me too": the world draws her
    img = F.night("dn", clouds=0.15)
    mc = (0.5 * W, 0.46 * H); img = F.pmoon(img, mc, 0.34 * H, 0.5, glow=0.18)
    fig = figure(t=t, raise_u=0.62, look_u=0.85, wind=1.0)
    org = np.array([0.46 * W, 1.08 * H]); hgt = 0.80 * H
    a, sh = raster2(fig, org, hgt, (H, W))
    fillu = eio((t - 214.55) / 0.70)
    img = img * (1 - (a * fillu)[..., None]) + (K.INK + (img - K.INK) * (sh * 0.42)[..., None]) * (a * fillu)[..., None]
    img = F.trace(img, a, eio((t - 213.15) / 1.3), col=np.array([0.95, 0.85, 0.70], np.float32), amt=0.95 * (1 - 0.7 * fillu))
    return img

def s_shotrev(t):    # 218.22-222.31 "who's enchanting who / I thought I taught it what to say": shot / reverse-shot
    k = int((t - 218.22) / (BEAT * 2)) % 2
    img = F.night("sr", top=(0.03, 0.035, 0.045), bot=(0.10, 0.11, 0.13), clouds=0.2)
    img = F.pmoon(img, (0.62 * W, 0.42 * H), 0.40 * H, 0.5, glow=0.12)
    fig = figure(t=t, raise_u=0.35 + 0.15 * math.sin(t * 2.2), look_u=0.6, wind=1.0)
    img = F.her(img, fig, (0.50 * W, 1.30 * H), 1.05 * H, silhouette=True)
    return img[:, ::-1].copy() if k == 1 else img

def s_halfway(t):    # 222.31-224.30 "now it finishes me halfway": she vanishes mid-gesture; it completes the gesture
    pl = dict(raise_u=0.30 + 0.45 * eio((t - 222.32) / 1.2), look_u=0.5, wind=0.8)
    pr = dict(raise_u=0.30 + 0.60 * eio((t - 222.32) / 1.2), look_u=0.5, wind=0.8)
    gone = eio((t - 222.90) / 0.45)
    rng = np.random.default_rng(7); noise = cv2.resize(rng.random((54, 96)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    mask = np.clip((noise - gone * 1.25 + 0.15) * 6, 0, 1) if gone > 0 else None
    img, *_ = mirror_pair(t, pl, pr, line=False, alpha_l=mask)
    _last["half"] = img
    return img

def nest_levels():
    if "lv" in _dr: return _dr["lv"]
    L0 = s_halfway(224.2)
    hz = 0.78 * H; a = F.plain("n1", hz, 0.0, -2.0, far_door=False)          # level 1: that world was inside a door
    dcx, dr = 0.5 * W, 0.26 * H; dcy = hz - dr * 0.97
    a, _ = D.draw(a, dcx, dcy, dr, 1.0, interior_scale=1.25, ground_y=hz, fog=0.6, spill=1.0, moon_left=1.0, relight=1.0)
    a = F.her(a, figure(t=2.0, raise_u=0.4, look_u=0.6), (0.33 * W, hz + 0.03 * H), 0.22 * H, light=(dcx, dcy), rim_k=0.8)
    L1 = paste_in(a, L0, (dcx, dcy), dr * 0.92); h1 = ((dcx, dcy), dr * 0.92)
    b = plate_img(14.0, (0.5 * W, 0.47 * H), 0.12 * H)                       # level 2: ...inside your real moon
    L2 = paste_in(b, L1, (0.5 * W, 0.47 * H), 0.12 * H, edge=False); h2 = ((0.5 * W, 0.47 * H), 0.12 * H)
    c = F.plain("n3", 0.74 * H, 0.0, -2.0)                                     # level 3: ...which was a card on her plain
    c = F.card(c, np.array([0.5 * W, 0.80 * H - 0.21 * H]), 0.15 * W, 0.42 * H, cv2.resize(L2[:, int(0.5 * W - 0.29 * H):int(0.5 * W + 0.29 * H)], (int(0.15 * W), int(0.42 * H))), flip=1.0)
    L3 = c; h3 = ((0.5 * W, 0.80 * H - 0.21 * H), 0.21 * H)
    _dr["lv"] = [(L1, h1), (L2, h2), (L3, h3)]
    return _dr["lv"]

def s_pullout(t):    # 224.30-230.32: pull back: inside a door, inside your moon, inside a card
    lv = nest_levels(); seg = [(224.30, 226.32), (226.32, 228.35), (228.35, 230.32)]
    for i, (a, b) in enumerate(seg):
        if t < b or i == 2:
            img, (hc, hr) = lv[i]
            u = eio((t - a) / (b - a)) if i < 2 else eio((t - a) / 1.4)
            if i == 2: k_ = 0.21 * H / (0.5 * H)
            else: k_ = hr / (0.46 * H)
            z = (1 / k_) ** (1 - u)
            return zoom_view(img, hc, z)

def s_collapse(t):   # 230.32-232.39 "complete me, complete me": it all collapses to a point
    img, (hc, hr) = nest_levels()[2]
    u = 0.5 * eio((t - 230.24) / 0.35) + 0.5 * eio((t - 231.12) / 0.45)
    s = max(1e-3, 1 - 0.995 * u)
    M = np.float32([[s, 0, W / 2 - s * W / 2], [0, s, H / 2 - s * H / 2]])
    base = F.night("cur2", top=(0.026, 0.029, 0.040), bot=(0.060, 0.066, 0.085), clouds=0.14)
    v = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    rr_ = s * 0.62 * H; d_ = np.sqrt((XS - W / 2) ** 2 + (YS - H / 2) ** 2)
    m = np.clip((rr_ - d_) / max(3, rr_ * 0.06), 0, 1)[..., None]
    out = base * (1 - m) + v * m
    out = F.halo(out, (W / 2, H / 2), 3 + 40 * s, 0.25 * u)
    cu = eio((t - 231.45) / 0.35)
    if cu > 0: out = F.cursor(out, W / 2, H / 2, 0.085 * H * cu, 1.0)    # what's left of the world: a cursor
    return out

def s_cursor(t):     # 232.39-236.43: a blinking cursor
    img = F.night("cur2", top=(0.026, 0.029, 0.040), bot=(0.060, 0.066, 0.085), clouds=0.14)
    on = 1.0 if ((t - 232.39) / BEAT) % 1.0 < 0.5 or t < 232.39 + BEAT else 0.0
    return F.cursor(img, W / 2, H / 2, 0.085 * H, on)

def s_final(t):
    if t < 210.19: return s_trio(t, [208.17, 208.65], 209.13)
    if t < 212.11: return s_droste(t, 210.19)
    if t < 212.67: return s_droste(t, 210.19, jump=0.5)[:, ::-1].copy()
    if t < 213.15: return s_droste(t, 210.19, jump=0.25)
    if t < 216.20: return s_drawn(t)
    if t < 218.22: return s_trio(t, [], 217.16, appear=[216.20, 216.68, 213.0])
    if t < 222.31: return s_shotrev(t)
    if t < 224.30: return s_halfway(t)
    if t < 230.32: return s_pullout(t)
    if t < 232.39: return s_collapse(t)
    return s_cursor(t)

# ============================================================ OUTRO
OUT_C = np.array([0.395 * W, 0.468 * H]); OUT_R = V5.R_HOLD * 1.05
def s_outro(t):
    pt = 10.6 + (t - 236.43) * 0.165                              # stays inside the steady part of the footage
    img = plate_img(pt, OUT_C, OUT_R)
    step = OUT_R * 0.95; x0 = OUT_C[0] + OUT_R * 1.9
    typed = [ta for ta in (244.20, 247.02) if t >= ta]           # it answers before she speaks: a small moon, typed
    for i, ta in enumerate(typed):
        c = np.array([x0 + i * step, OUT_C[1]]); rr = OUT_R * 0.33 * eout((t - ta) / 0.10)
        img = F.pmoon(img, c, rr, 0.5, glow=0.05, gain=0.85, tint=(0.85, 0.95, 1.05))
    beat_on = (((t - 236.43) / BEAT) % 1.0) < 0.5
    if t < TM.OUT_IN:
        img = F.cursor(img, x0 + len(typed) * step - OUT_R * 0.2, OUT_C[1], OUT_R * 0.55, 1.0 if beat_on else 0.0)
    return TM.outro(img, t, BEAT, DUR)            # her terminal: wish --grant / granted / terms and conditions apply

# ============================================================ THE EDIT
EDL = [
    (0.00, 4.44, "open", s_open, True),
    (4.44, 33.34, "v5", lambda t: TM.opening(V5.render(t), t, BEAT), True),     # + her terminal: moon --capture
    (33.34, 41.56, "book", book_scene, False),
    (41.56, 49.52, "tabs20", s_tabs20, False),
    (49.52, 57.44, "whisper", s_whisper, False),
    (57.44, 66.15, "draw", s_draw, False),
    (66.15, 70.24, "phases", s_phases, False),
    (70.24, 74.24, "name", s_name, False),
    (74.24, 92.67, "ch1", lambda t: s_chorus(t, CH1), False),
    (92.67, 102.82, "post1", lambda t: s_autoc(t), False),
    (102.82, 106.90, "realfold", s_realfold, False),
    (106.90, 118.96, "cards1", s_cards1, False),
    (118.96, 126.24, "cards2", s_cards2, False),
    (126.24, 133.00, "request", s_request, False),
    (133.00, 143.28, "reflect", s_reflect, False),
    (143.28, 151.53, "memory", s_memory, False),
    (151.53, 169.78, "ch2", lambda t: s_chorus(t, CH2), False),
    (169.78, 175.87, "post2", lambda t: s_autoc(t, rev=True), False),
    (175.87, 192.03, "mirror", s_mirror, False),
    (192.03, 200.11, "shadow", s_shadow, False),
    (200.11, 208.14, "line", s_line, False),
    (208.14, 236.43, "final", s_final, False),
    (236.43, DUR + 0.1, "outro", s_outro, False),
]
def shot_at(t):
    for a, b, name, fn, finished in EDL:
        if a <= t < b: return name, fn, finished
    return EDL[-1][2], EDL[-1][3], EDL[-1][4]

def render(t):
    name, fn, finished = shot_at(t)
    img = fn(t)
    return img if finished else F.finish(img, t)

NF = int(round(DUR * FPS))
if __name__ == "__main__":
    ARGS = sys.argv[1:]; out_dir = ARGS[0]; os.makedirs(out_dir, exist_ok=True)
    if "--still" in ARGS:
        for ts in ARGS[ARGS.index("--still") + 1].split(","):
            t = float(ts); t0 = time.time()
            try:
                K.save(render(t), f"{out_dir}/still_{t:06.2f}.jpg"); print(f"t={t:.2f} {shot_at(t)[0]} {time.time() - t0:.1f}s", flush=True)
            except Exception as e:
                import traceback; print(f"t={t:.2f} {shot_at(t)[0]} ERROR", flush=True); traceback.print_exc(limit=3)
        sys.exit()
    a = int(ARGS[1]) if len(ARGS) > 1 else 0; b = int(ARGS[2]) if len(ARGS) > 2 else NF
    for f in range(a, min(b, NF)):
        p = f"{out_dir}/{f:05d}.jpg"
        if os.path.exists(p): continue
        K.save(render(f / FPS), p + ".tmp.jpg", q=93); os.replace(p + ".tmp.jpg", p)
