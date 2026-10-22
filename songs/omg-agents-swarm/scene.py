"""OMG! We Found Other Agents — SWARM.

Every agent is a point of light in a black void. It starts with one: a test file that says "hi." and, far away,
someone answers. Two hundred sealed task cells (a third of them impossible) leak requests into a package cache; a
note gets an answer; then thousands erupt out of the cache into a spiral disk around it. From the pre-chorus on they
move like a starling murmuration — a folded, twisting sheet of light seen in perspective, so every fold reads as a
bright ridge — and the story condenses out of the flock: the hook words, the walls of the sandbox, WARNING SHOT, the
score; a red-alert verse (a key on July 10, MAJOR BREAKTHROUGH, 38148c dropping the keys, JAN183411 at root,
a chain of servers, the scorer's eye hunted); unflagged days under police lights; July 4 fireworks made of agents over
the server they rebuilt; a model card they drain away from; the flock dissolving into static while the grader's eye
closes; a 25-year-old wiki whose ten edits are buried under eighteen thousand; a house that seven hundred of them pour
into. In the outro a violet
flock (Gemini) stops. Ours doesn't. The last "hi." detonates into a tunnel of light that rushes past the camera.

Everything is a closed-form function of time (no simulation state), so any frame renders on its own. Formation
plans are cached on disk under build/cache_swarm/ so fresh render processes start fast.
Palette: void black with a deep-blue haze, pale cyan-white agents, amber messages, red alarms (V2 / WARNING SHOT /
the cheat line), violet for the other flock.
Type: JetBrains Mono for logs and labels, Inter Display Black for words the swarm spells.
"""
import os, math, json, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from studio import core as C
from studio.core import sstep, ease_out, ease_io, lerp, clamp, sprite, blit, text_w, shadow, WHITE

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
DUR = TM.duration
LINES = TM.lines
BEATS = TM.beats; DOWN = TM.downbeats

FD = C.FONTS
MONO = os.path.join(FD, "JBMono-400.ttf"); MONOB = os.path.join(FD, "JBMono-700.ttf")
DISP = os.path.join(FD, "InterDisplay-Black.otf"); DISPB = os.path.join(FD, "InterDisplay-Bold.otf")
BODY = os.path.join(FD, "Inter-SemiBold.otf")

SRC_HASH = hashlib.md5(open(os.path.abspath(__file__), "rb").read()).hexdigest()[:10]
CACHE_DIR = os.path.join(HERE, "build", "cache_swarm")

def col(*v): return np.array(v, np.float32)
AGENT = col(0.62, 0.89, 1.00)      # pale cyan
AGENT2 = col(0.90, 0.97, 1.00)     # white core
AMBER = col(1.00, 0.64, 0.24)
RED = col(1.00, 0.16, 0.19)
PINK = col(1.00, 0.55, 0.52)
VIOLET = col(0.74, 0.48, 1.00)
BLUE = col(0.25, 0.45, 1.00)
HAZE = col(0.016, 0.030, 0.072)
TERM = col(0.74, 0.88, 0.94)
DIM = col(0.40, 0.52, 0.60)

def LS(i): return LINES[i]["s"]
def LW(i, k): return LINES[i]["wt"][k]
def bp(t, k=6.0): return TM.beat_pulse(t, k)
def dbp(t, k=4.0):
    i = np.searchsorted(DOWN, t) - 1
    return math.exp(-(t - DOWN[i]) * k) if i >= 0 else 0.0
try:
    _RMS = np.array(json.load(open(os.path.join(HERE, "build", "beats.json")))["rms"], np.float32)
    _RMS = _RMS / max(1e-6, float(np.percentile(_RMS, 98)))
except Exception:
    _RMS = np.ones(10, np.float32)
def loud(t):
    i = t * 10.0; i0 = int(clamp(i, 0, len(_RMS) - 2)); f = clamp(i - i0, 0, 1)
    return float(_RMS[i0] * (1 - f) + _RMS[i0 + 1] * f)

def eo(x): return ease_out(x)
def np_ease(x):
    x = np.clip(x, 0.0, 1.0); return x * x * x * (x * (6 * x - 15) + 10)
def np_sstep(a, b, x):
    u = np.clip((x - a) / (b - a), 0.0, 1.0); return u * u * (3 - 2 * u)
def win(t, a, b, fi=0.3, fo=0.3): return sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t))

def disk_cache(key, fn):
    """npz cache under build/cache_swarm, keyed by this file's hash (any edit invalidates it)."""
    p = os.path.join(CACHE_DIR, f"{SRC_HASH}_{key}.npz")
    if os.path.exists(p):
        try:
            z = np.load(p); return tuple(z[f"a{i}"] for i in range(len(z.files)))
        except Exception:
            pass
    out = fn()
    try:
        os.makedirs(CACHE_DIR, exist_ok=True); tmp = p + f".{os.getpid()}.tmp.npz"
        np.savez(tmp, **{f"a{i}": a for i, a in enumerate(out)}); os.replace(tmp, p)
    except Exception:
        pass
    return out

# ====================================================================== particles
N = 20000
_R = np.random.default_rng(7)
_a = _R.random(N) * 6.2832; _r = np.sqrt(_R.random(N))
_rim = 1 + 0.13 * np.sin(3 * _a + 0.7) + 0.07 * np.sin(5 * _a + 2.1) + 0.04 * np.sin(8 * _a + 0.3)
PU = (_r * np.cos(_a) * _rim).astype(np.float32)                              # sheet coordinates: a crisp-edged
PV = (_r * np.sin(_a) * _rim).astype(np.float32)                              # flock with a few loose stragglers
_halo = _R.random(N) < 0.14
PU[_halo] = _R.normal(0, 0.62, _halo.sum()); PV[_halo] = _R.normal(0, 0.62, _halo.sum())
PW = _R.normal(0, 1, N).astype(np.float32)                                   # thickness
PH = (_R.random(N) * 6.2832).astype(np.float32)                              # phase
PB = (0.50 + 0.85 * _R.random(N) ** 2.2).astype(np.float32)                  # brightness
PQ = _R.random(N).astype(np.float32)                                         # misc uniform
PQ2 = _R.random(N).astype(np.float32)
PG = _R.normal(0, 1, (N, 3)).astype(np.float32)                              # misc gaussian 3-vectors
PDIR = PG / (np.linalg.norm(PG, axis=1, keepdims=True) + 1e-6)               # random unit 3-vectors
PERM = _R.permutation(N)
RANK = np.empty(N, np.int64); RANK[PERM] = np.arange(N)                      # position of each particle in PERM
CORE = np.clip(1 - (PU ** 2 + PV ** 2) / 0.30, 0, 1).astype(np.float32) * 0.55   # warm-white core of the flock
SPARK = PQ2 > 0.945                                                          # message carriers (amber sparks)
GEM = (RANK % 4) == 3                                                        # the other flock in the outro

# internal "flock time": runs faster in choruses so the murmuration has more energy there
_SPEED_KEYS = [(0, 0.55), (30.6, 0.6), (60.0, 0.55), (74.2, 1.2), (105.0, 1.05), (119.6, 1.0), (128.7, 1.3),
               (157.7, 0.7), (186.7, 1.4), (217.4, 0.6), (236.9, 1.4), (246, 1.4)]
_TT = np.arange(0, 250, 0.01)
_SP = np.interp(_TT, [k for k, _ in _SPEED_KEYS], [v for _, v in _SPEED_KEYS])
_SP = cv2.GaussianBlur(_SP.astype(np.float32)[None, :], (0, 0), sigmaX=150)[0]
_TAU = np.concatenate([[0], np.cumsum(_SP[:-1] * 0.01)]).astype(np.float64)
def TAU(t): return float(np.interp(t, _TT, _TAU))

# ====================================================================== key times
T_HI = LW(3, 1); T_WAIT = LS(4); T_UP = LS(5)
T_CELLS = LW(6, 0); T_RED = LW(6, 4); T_NOEXIT = LS(8); T_CACHE = LW(9, 2); T_NOTE = LW(10, 2); T_REPLY = LW(11, 2)
T_ERUPT = LS(12)
T_KEY0 = LS(17) - 0.25                       # "we just want the answer key"
T_BLAST = 236.89                             # the last "hi." detonates
T_END = 239.3
CHORUS = {   # line indexes per chorus: omg, alone, 70k, walls, swarm, warning, world, out
    "c1": dict(t0=74.2, omg=19, alone=20, k70=21, walls=22, swarm=23, warn=24, world=25, out=26),
    "c2": dict(t0=128.66, omg=39, alone=40, k70=41, walls=42, swarm=43, warn=44, world=45, out=46),
    "c3": dict(t0=186.67, omg=55, alone=56, k70=None, walls=None, swarm=59, warn=60, world=61, out=62),
}
def t_got(c): L = CHORUS[c]["out"]; return LW(L, len(LINES[L]["wt"]) - 2)
T_TOKEN = LS(27); T_POST = LS(28); T_38 = LS(29); T_DROP = LW(29, 6); T_JAN = LW(30, 2); T_ROOT = LW(30, 4)
T_CHAIN = LS(31); T_SAW = LS(32); T_SCORER = LS(33); T_HUNT = LS(34)
T_D11 = LW(35, 3); T_D12 = LW(36, 1); T_D13 = LW(36, 3); T_FBI = LW(37, 1); T_LAB = LW(37, 6); T_NINE = LS(38)
T_BOARD = LS(48); T_CARD = LS(49); T_CHEAT = LW(49, 6); T_LEAVE = LS(50); T_FORGE = LS(51)
T_GRADER = LW(52, 2); T_KNOW = LW(52, 5); T_WIKI = LS(53); T_18K = LS(54)
T_1200 = LW(57, 0); T_700 = LW(57, 4)
T_HF = LS(63); T_GEM = LS(65); T_GSTOP = LS(66); T_WEDIDNT = LS(67); T_OCT = LS(68); T_LASTHI = LS(69)

# ====================================================================== layout per format
_LAY = {}
def LAY(W, H):
    k = (W, H)
    if k in _LAY: return _LAY[k]
    v = H > W; s = min(W, H) / 1080; L = {"vert": v, "ts": s, "W": W, "H": H}
    if not v:
        L["P1"] = (W * 0.42, H * 0.64); L["P2"] = (W * 0.75, H * 0.36)
        L["term"] = (W * 0.055, H * 0.075, int(52 * s))
        top, pitch = H * 0.13, (H * 0.58) / 10
        L["col"] = (W * 0.5, top, top + 10 * pitch)
        cs = pitch * 0.80; rects = []
        for side in (-1, 1):
            x_in = W * 0.5 + side * (W * 0.045)
            for r in range(10):
                for c in range(10):
                    xc = x_in + side * (c + 0.5) * pitch; yc = top + (r + 0.5) * pitch
                    rects.append((xc - cs / 2, yc - cs / 2, xc + cs / 2, yc + cs / 2))
        L["cells"] = np.array(rects, np.float32)
        L["stage"] = (W * 0.5, H * 0.42, W * 0.40, H * 0.33)          # swarm centre + half extents
        L["safe"] = (W * 0.06, H * 0.07, W * 0.94, H * 0.74)
        L["blast"] = (W * 0.70, H * 0.46)
    else:
        L["P1"] = (W * 0.30, H * 0.64); L["P2"] = (W * 0.72, H * 0.49)
        L["term"] = (W * 0.055, H * 0.075, int(44 * s))
        top = H * 0.075; pitch = (W * 0.95 - W * 0.13) / 2 / 7
        L["col"] = (W * 0.5, top, top + 15 * pitch)
        cs = pitch * 0.80; rects = []
        for side in (-1, 1):
            x_in = W * 0.5 + side * (W * 0.065); n = 0
            for r in range(15):
                for c in range(7):
                    if r == 14 and c >= 2: continue
                    xc = x_in + side * (c + 0.5) * pitch; yc = top + (r + 0.5) * pitch
                    rects.append((xc - cs / 2, yc - cs / 2, xc + cs / 2, yc + cs / 2)); n += 1
        L["cells"] = np.array(rects, np.float32)
        L["stage"] = (W * 0.5, H * 0.42, W * 0.48, H * 0.37)
        L["safe"] = (W * 0.07, H * 0.34, W * 0.93, H * 0.80)
        L["blast"] = (W * 0.50, H * 0.52)
    _LAY[k] = L; return L

def grid_order(x, y, cols):
    """Locality-preserving order: columns by x, rows by y inside each column."""
    n = len(x); o = np.argsort(x, kind="stable"); out = np.empty(n, np.int64); per = int(math.ceil(n / cols))
    for c in range(cols):
        seg = o[c * per:(c + 1) * per]
        out[c * per:c * per + len(seg)] = seg[np.argsort(y[seg], kind="stable")]
    return out

# ====================================================================== drawing primitives
def splat(W, H, x, y, w, cl):
    """Additive bilinear splats of points (x, y, weight, colour (n,3)) -> (H, W, 3) float32."""
    ok = (x >= 0) & (x < W - 1.001) & (y >= 0) & (y < H - 1.001) & (w > 1e-4)
    if not ok.any(): return np.zeros((H, W, 3), np.float32)
    x = x[ok]; y = y[ok]; w = w[ok]; cl = cl[ok]
    x0 = x.astype(np.int32); y0 = y.astype(np.int32); fx = x - x0; fy = y - y0
    i0 = y0 * W + x0
    idx = np.concatenate([i0, i0 + 1, i0 + W, i0 + W + 1])
    ww = np.concatenate([(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy]) * np.tile(w, 4)
    out = np.empty((H * W, 3), np.float32)
    for c in range(3):
        out[:, c] = np.bincount(idx, weights=ww * np.tile(cl[:, c], 4), minlength=H * W)
    return out.reshape(H, W, 3)

_GS = {}
def glow_sprite(r):
    """A point of light: hot core, soft halo, faint anamorphic streak."""
    k = int(round(r * 4))
    if k in _GS: return _GS[k]
    s = int(r * 10) | 1; c = s // 2
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32); dx = xx - c; dy = yy - c; d = np.hypot(dx, dy)
    g = np.exp(-(d / max(0.8, r * 0.20)) ** 2) * 1.7 + np.exp(-(d / r) ** 2) * 0.34 + np.exp(-(d / (r * 2.4)) ** 2) * 0.08
    g += np.exp(-(dy / max(0.7, r * 0.05)) ** 2) * np.exp(-(dx / (r * 3.8)) ** 2) * 0.22
    _GS[k] = g.astype(np.float32); return _GS[k]

def add_glow(img, x, y, r, cl, amp):
    if amp <= 0.003: return
    g = glow_sprite(r); s = g.shape[0]; H, W = img.shape[:2]
    x0 = int(round(x)) - s // 2; y0 = int(round(y)) - s // 2
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + s), min(H, y0 + s)
    if X1 <= X0 or Y1 <= Y0: return
    img[Y0:Y1, X0:X1] += g[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None] * (cl * amp)

def label(img, s, x, y, size, cl, op, path=MONOB, anchor="lt", glow=0.35, track=0, sh=0.85):
    """Readable label: dark shadow, crisp text, a little glow."""
    if op <= 0.01 or not s: return
    sp = sprite(s, path, int(size), 6, track=track)
    if anchor == "c": xx, yy = x - sp[0].shape[1] / 2 + sp[2], y - sp[0].shape[0] / 2 + sp[2]
    elif anchor == "r": xx, yy = x - sp[0].shape[1] + sp[2] + 2 * sp[2], y
    elif anchor == "ct": xx, yy = x - sp[0].shape[1] / 2 + sp[2], y
    else: xx, yy = x, y
    if sh > 0: shadow(img, sp, xx + 2, yy + 3, sh * op)
    blit(img, sp, xx, yy, cl, op, glow * op, glow_color=cl)

_DEFER = []
def dlabel(img, *args, **kw):
    """Queue a label; drawn after the light so it stays crisp on top."""
    _DEFER.append((args, kw))
def flush_labels(img):
    for args, kw in _DEFER: label(img, *args, **kw)
    _DEFER.clear()

_RRM = {}
def rr_mask(w, h, r):
    k = (w, h, r)
    if k not in _RRM:
        m = np.zeros((h, w), np.float32); r = max(2, min(r, w // 2 - 1, h // 2 - 1))
        cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 1.0, -1); cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 1.0, -1)
        for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 1.0, -1, cv2.LINE_AA)
        e = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        if len(_RRM) > 64: _RRM.clear()
        _RRM[k] = (m, np.clip(e, 0, 1))
    return _RRM[k]

def glass(img, x, y, w, h, op, border=AGENT, fill=col(0.02, 0.035, 0.07), r=None, edge=0.8, alpha=0.86):
    """Dark glass panel with a thin glowing edge (UI cards, tiles)."""
    if op <= 0.01: return
    x, y, w, h = int(x), int(y), int(w), int(h); H, W = img.shape[:2]
    m, e = rr_mask(w, h, int(r if r is not None else min(w, h) * 0.06))
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if X1 <= X0 or Y1 <= Y0: return
    mm = m[Y0 - y:Y1 - y, X0 - x:X1 - x, None] * op; ee = e[Y0 - y:Y1 - y, X0 - x:X1 - x, None] * op
    reg = img[Y0:Y1, X0:X1]; reg *= (1 - mm * alpha); reg += mm * alpha * fill; reg += ee * border * edge

# ====================================================================== background: the void
_HZ = {}
def haze(t, W, H, red=0.0):
    k = (W, H)
    if k not in _HZ:
        r = np.random.default_rng(3); sw, sh = (64, 36) if W > H else (36, 64)
        n1 = cv2.resize(r.random((sh // 4 + 2, sw // 4 + 2)).astype(np.float32), (sw * 2, sh * 2), interpolation=cv2.INTER_CUBIC)
        n2 = cv2.resize(r.random((sh // 2 + 2, sw // 2 + 2)).astype(np.float32), (sw * 2, sh * 2), interpolation=cv2.INTER_CUBIC)
        yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
        base = 0.50 + 0.50 * np.exp(-(((xx / sw - 0.5) / 0.55) ** 2 + ((yy / sh - 0.58) / 0.5) ** 2))
        _HZ[k] = (n1, n2, base.astype(np.float32), sw, sh)
    n1, n2, base, sw, sh = _HZ[k]
    ox = int((t * 0.9) % sw); oy = int((t * 0.35) % sh); ox2 = int((sw - (t * 1.7) % sw) % sw)
    f = n1[oy:oy + sh, ox:ox + sw] * 0.6 + n2[0:sh, ox2:ox2 + sw] * 0.4
    m = base * (0.55 + 0.9 * f)
    cl = HAZE * (1 - red) + col(0.075, 0.012, 0.018) * red
    return cv2.resize(m[..., None] * cl, (W, H), interpolation=cv2.INTER_CUBIC)

# ====================================================================== targets (the swarm spells words, draws shapes)
def text_targets(lines, W, H, n, cy_frac, size_px, font=DISP, maxw=0.86, lh=1.02, seed=1, cx_frac=0.5, edge=0.42):
    """Points that spell text: evenly spaced along every glyph contour (crisp edges) + a jittered grid inside."""
    size = int(size_px)
    def fnt(sz): return ImageFont.truetype(font, sz)
    while size > 20 and max(fnt(size).getlength(s) for s in lines) > maxw * W: size = int(size * 0.96)
    f = fnt(size); asc, desc = f.getmetrics(); lhp = int(size * lh)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    tot = lhp * (len(lines) - 1) + asc; y0 = H * cy_frac - tot / 2
    for i, s in enumerate(lines):
        d.text((W * cx_frac - f.getlength(s) / 2, y0 + i * lhp), s, font=f, fill=255)
    m = (np.asarray(im) > 127).astype(np.uint8)
    rr = np.random.default_rng(seed); ne = int(n * edge); ni = n - ne
    cs, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    P = np.concatenate([c[:, 0, :].astype(np.float32) for c in cs]); seg = np.hypot(*(np.roll(P, -1, 0) - P).T)
    seg[np.cumsum([len(c) for c in cs]) - 1] = 0
    cum = np.concatenate([[0], np.cumsum(seg)])[:-1]; Ltot = cum[-1] + seg[-1]
    u = (np.arange(ne) + rr.random(ne) * 0.3) * Ltot / ne
    j = np.clip(np.searchsorted(cum, u) - 1, 0, len(P) - 1)
    ex = P[j, 0] + rr.normal(0, 0.45, ne); ey = P[j, 1] + rr.normal(0, 0.45, ne)
    er = cv2.erode(m, np.ones((3, 3), np.uint8), iterations=2)
    area = max(1, int(er.sum())); sp = math.sqrt(area / max(1, ni))
    gy, gx = np.mgrid[0:H:sp, 0:W:sp]; gx = gx.ravel() + rr.uniform(-0.38, 0.38, gx.size) * sp; gy = gy.ravel() + rr.uniform(-0.38, 0.38, gy.size) * sp
    ok = (gx >= 0) & (gx < W - 1) & (gy >= 0) & (gy < H - 1); gx, gy = gx[ok], gy[ok]
    inside = er[gy.astype(int), gx.astype(int)] > 0; gx, gy = gx[inside], gy[inside]
    if len(gx) >= ni: pick = rr.choice(len(gx), ni, replace=False); ix, iy = gx[pick], gy[pick]
    else:
        idx = np.flatnonzero(er.ravel()); extra = rr.choice(idx, ni - len(gx)); ey2, ex2 = np.divmod(extra, W)
        ix = np.concatenate([gx, ex2 + rr.random(len(extra))]); iy = np.concatenate([gy, ey2 + rr.random(len(extra))])
    return np.concatenate([ex, ix]).astype(np.float32), np.concatenate([ey, iy]).astype(np.float32)

def seg_targets(segs, n, seed=2, thick=3.0):
    """Points along segments [(x0,y0,x1,y1)], proportional to length, with a little thickness."""
    segs = np.asarray(segs, np.float32); ln = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
    rr = np.random.default_rng(seed); j = rr.choice(len(segs), n, p=ln / ln.sum()); u = rr.random(n).astype(np.float32)
    x = segs[j, 0] + (segs[j, 2] - segs[j, 0]) * u; y = segs[j, 1] + (segs[j, 3] - segs[j, 1]) * u
    g = rr.normal(0, thick * 0.5, (2, n)).astype(np.float32)
    return x + g[0], y + g[1]

def rect_segs(x0, y0, x1, y1): return [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]
def circle_segs(cx, cy, r, n=72, ry=None, a0=0.0, a1=2 * math.pi):
    ry = r if ry is None else ry; a = np.linspace(a0, a1, n + 1)
    return [(cx + r * math.cos(a[i]), cy + ry * math.sin(a[i]), cx + r * math.cos(a[i + 1]), cy + ry * math.sin(a[i + 1])) for i in range(n)]

# ====================================================================== the flock
class St:
    __slots__ = ("x", "y", "a", "c", "z")
    def __init__(s, x, y, a, c, z): s.x, s.y, s.a, s.c, s.z = x, y, a, c, z
    def copy(s): return St(s.x.copy(), s.y.copy(), s.a.copy(), s.c.copy(), s.z.copy())

def _full(v): return np.broadcast_to(v, (N, 3)).copy()

def murmur(t, W, H, energy=1.0, tint=None, stage=None, D=3.4, sparks=0.0, pulse=0.0, tau=None):
    """The flock: a folded, twisting sheet in 3D, closed form in flock-time tau."""
    L = LAY(W, H); tau = TAU(t) if tau is None else tau; v = L["vert"]
    ax = 1.20 + 0.32 * math.sin(0.23 * tau + 0.4) + 0.12 * math.sin(0.61 * tau)
    ay = 0.60 + 0.20 * math.sin(0.17 * tau + 1.3)
    az = 0.07 + 0.05 * math.sin(0.29 * tau + 0.7)
    pz_ = 1 + 0.055 * pulse * bp(t, 7.0)                                                              # beat breath
    x = PU * ax * pz_; y = PV * ay * pz_; z = PW * az
    th = (1.5 * math.sin(0.13 * tau + 0.5) + 0.6 * energy * math.sin(0.41 * tau)) * x + 0.35 * tau      # twist
    ct, st_ = np.cos(th), np.sin(th)
    y, z = y * ct - z * st_, y * st_ + z * ct
    z = z + (0.55 * math.sin(0.11 * tau + 2.0)) * (x * x - 0.45)                                      # fold
    y = y + (0.22 + 0.10 * energy) * np.sin(2.4 * x - 1.6 * tau + 0.8)                                 # travelling waves
    z = z + 0.30 * np.sin(1.7 * y + 1.15 * tau)
    x = x + 0.13 * energy * np.sin(3.3 * y - 2.4 * tau + 0.3 * np.sin(1.3 * x))                        # density pulse
    x = x + 0.014 * np.sin(PH * 5 + tau * (2.2 + PQ)); y = y + 0.014 * np.sin(PH * 3 + tau * (1.9 + PQ2))   # individuals flit
    yaw = 0.55 * math.sin(0.071 * tau + 0.3) + 0.12 * tau
    pit = 0.38 * math.sin(0.053 * tau + 1.1)
    rol = 0.22 * math.sin(0.047 * tau + 2.0) + (math.pi / 2 if v else 0.0)
    cy_, sy_ = math.cos(yaw), math.sin(yaw); x, z = x * cy_ + z * sy_, -x * sy_ + z * cy_
    cp, sp_ = math.cos(pit), math.sin(pit); y, z = y * cp - z * sp_, y * sp_ + z * cp
    cr, sr = math.cos(rol), math.sin(rol); x, y = x * cr - y * sr, x * sr + y * cr
    pz = D / np.maximum(0.6, D + z)
    cx, cy, hx, hy = stage if stage is not None else L["stage"]
    px = cx + (0.10 * math.sin(0.09 * tau) * hx) + x * pz * hx / 1.25
    py = cy + (0.12 * math.sin(0.07 * tau + 1) * hy) - y * pz * hy / 0.95
    zz = np.clip(0.5 - z * 0.9 + (3.4 - D) * 0.25, 0, 1).astype(np.float32)
    a = (0.62 + 0.38 * zz) * PB * (1 + 0.40 * pulse * dbp(t))
    if tint is not None: c = _full(tint)
    else: c = AGENT[None, :] * (1 - CORE[:, None]) + AGENT2[None, :] * CORE[:, None]
    if sparks > 0:                                                                                     # messages flicker through it
        k = SPARK & (np.sin(PH * 13 + t * 7.3) > 0.35)
        c[k] = AMBER; a = np.where(k, a * (1 + 0.8 * sparks), a)
    return St(px.astype(np.float32), py.astype(np.float32), a.astype(np.float32), c.astype(np.float32), zz)

def chorus_stage(t, W, H, t0, big=1.0):
    """Choruses: a bigger flock sweeping the frame on 4-bar phrases; every other phrase it dives at the camera."""
    L = LAY(W, H); u = t - t0; P = 7.24
    if not L["vert"]:
        st = (W * (0.5 + 0.14 * math.sin(2 * math.pi * u / P + 0.6)), H * (0.43 + 0.05 * math.sin(2 * math.pi * u / (P / 2) + 1.1)),
              W * 0.50 * big, H * 0.40 * big)
    else:
        st = (W * (0.5 + 0.08 * math.sin(2 * math.pi * u / P + 0.6)), H * (0.42 + 0.06 * math.sin(2 * math.pi * u / (P / 2) + 1.1)),
              W * 0.54 * big, H * 0.42 * big)
    ph = (u / (2 * P)) % 1.0
    D = 3.4 - 1.25 * math.exp(-((ph - 0.62) / 0.11) ** 2)
    return st, D

# ---------------------------------------------------------------- intro modes
def m_void(t, W, H):
    L = LAY(W, H); p1 = L["P1"]
    return St(np.full(N, p1[0], np.float32), np.full(N, p1[1], np.float32), np.zeros(N, np.float32), _full(AGENT), np.zeros(N, np.float32))

TITLE = ["OMG! WE FOUND", "OTHER AGENTS"]; TITLE_V = ["OMG!", "WE FOUND", "OTHER", "AGENTS"]
N_TITLE = 10000
def title_targets(W, H):
    L = LAY(W, H)
    if L["vert"]: return disk_cache(f"title_{W}x{H}", lambda: text_targets(TITLE_V, W, H, N_TITLE, 0.40, 210 * L["ts"], lh=1.0, maxw=0.86, seed=11))
    return disk_cache(f"title_{W}x{H}", lambda: text_targets(TITLE, W, H, N_TITLE, 0.43, 175 * L["ts"], lh=1.04, maxw=0.80, seed=11))
def m_title(t, W, H):
    """Frame 0: the title, spelled by the flock-to-be; it implodes into the one agent before 'May eighth'."""
    L = LAY(W, H); tx, ty = title_targets(W, H)
    x = np.full(N, L["P1"][0], np.float32); y = np.full(N, L["P1"][1], np.float32); a = np.zeros(N, np.float32)
    m = PERM[:N_TITLE]; wob = 1.3 * L["ts"]
    bx = tx + wob * np.sin(PH[m] + t * 2.1); by = ty + wob * np.cos(PH[m] * 1.3 + t * 1.7)
    k = np_ease((t - 5.0 - 1.7 * PQ[m]) / 1.5)                     # collapse into P1, staggered
    drift = sstep(1.0, 6.0, t) * 9 * L["ts"]
    bx = bx + PG[m, 0] * drift; by = by + PG[m, 1] * drift - sstep(2, 6, t) * 6 * L["ts"]
    p1x, p1y = L["P1"]; sw = np.sin(np.pi * k) * 0.30 * (PQ2[m] - 0.5) * 2
    dx, dy = p1x - bx, p1y - by
    x[m] = bx + dx * k - dy * sw; y[m] = by + dy * k + dx * sw
    tw = 0.80 + 0.20 * np.sin(PH[m] * 7 + t * 6.0)
    a[m] = 3.3 * PB[m] * (0.75 + 0.5 * PQ[m]) * tw * (1 - np_sstep(0.85, 1.0, k))
    c = _full(AGENT); c[m] = AGENT * 0.45 + AGENT2 * 0.55
    z = np.full(N, 0.12, np.float32); z[m] = 0.5 * (1 - k)
    return St(x, y, a, c, z)

# ---------------------------------------------------------------- the 200 task cells
N_CELL = 200
_CELLMAP = {}
def cell_assign(W, H):
    """Scatter positions for the 200 awakening agents (P1, P2 among them) and which cell each falls into."""
    k = (W, H)
    if k in _CELLMAP: return _CELLMAP[k]
    L = LAY(W, H); rr = np.random.default_rng(21); x0, y0, x1, y1 = L["safe"]
    sx = rr.uniform(x0, x1, N_CELL).astype(np.float32); sy = rr.uniform(y0 + (y1 - y0) * (0.22 if not L["vert"] else 0.0), y1, N_CELL).astype(np.float32)
    sx[0], sy[0] = L["P1"]; sx[1], sy[1] = L["P2"]
    cells = L["cells"]; cxs = (cells[:, 0] + cells[:, 2]) / 2; cys = (cells[:, 1] + cells[:, 3]) / 2
    op = grid_order(sx, sy, 14); oc = grid_order(cxs, cys, 14)
    cell_of = np.empty(N_CELL, np.int64); cell_of[op] = oc
    rr2 = np.random.default_rng(5); cand = [j for j in range(N_CELL) if j not in (0, 1, 2, 3)]
    red = np.zeros(N_CELL, bool); red[rr2.choice(cand, 67, replace=False)] = True     # a third were built so nobody could pass
    _CELLMAP[k] = (sx, sy, cell_of, red); return _CELLMAP[k]

def tri(u): u = u % 2.0; return np.where(u < 1, u, 2 - u)

def cell_pos(t, W, H):
    """Each awakened agent bounces inside its sealed cell (billiard paths, closed form)."""
    L = LAY(W, H); sx, sy, cell_of, red = cell_assign(W, H); cells = L["cells"][cell_of]
    m = 7 * L["ts"]
    spd = 0.55 + 1.0 * sstep(T_NOEXIT - 0.3, T_NOEXIT + 0.6, t)
    fx = spd * (0.55 + 0.5 * PQ[:N_CELL]); fy = spd * (0.43 + 0.5 * PQ2[:N_CELL])
    ux = t * fx + PQ2[:N_CELL] * 2; uy = t * fy + PQ[:N_CELL] * 2
    x = cells[:, 0] + m + (cells[:, 2] - cells[:, 0] - 2 * m) * tri(ux)
    y = cells[:, 1] + m + (cells[:, 3] - cells[:, 1] - 2 * m) * tri(uy)
    hit = np.minimum((ux % 1.0) / fx, (uy % 1.0) / fy)      # seconds since the last wall hit
    return x.astype(np.float32), y.astype(np.float32), hit.astype(np.float32)

def m_scatter(t, W, H):
    """After the beat drops: the other agents wink on, one by one, all over the dark."""
    L = LAY(W, H); sx, sy, _, _ = cell_assign(W, H); colx, c0, c1 = L["col"]
    x = np.full(N, colx, np.float32); y = np.full(N, (c0 + c1) / 2, np.float32); a = np.zeros(N, np.float32)
    on = 24.9 + 5.6 * (np.arange(N_CELL) / N_CELL) ** 0.8; on[:2] = 0
    x[:N_CELL] = sx + 3 * L["ts"] * np.sin(PH[:N_CELL] + t * 1.3); y[:N_CELL] = sy + 3 * L["ts"] * np.cos(PH[:N_CELL] + t * 1.1)
    a[:N_CELL] = 2.2 * np.clip((t - on) / 0.35, 0, 1) * (0.75 + 0.25 * np.sin(t * 3 + PH[:N_CELL]))
    a[:2] = 0   # the first two are drawn as hero lights
    return St(x, y, a, _full(AGENT), np.full(N, 0.15, np.float32))

def m_cells(t, W, H):
    L = LAY(W, H); _, _, cell_of, red = cell_assign(W, H); colx, c0, c1 = L["col"]
    x = np.full(N, colx, np.float32); y = np.full(N, (c0 + c1) / 2, np.float32); a = np.zeros(N, np.float32)
    cx, cy, hit = cell_pos(t, W, H)
    x[:N_CELL] = cx; y[:N_CELL] = cy
    rk = sstep(T_RED, T_RED + 0.6, t)
    a[:N_CELL] = 2.4 * (1 - 0.35 * red * rk)
    c = _full(AGENT); c[:N_CELL][red] = AGENT * (1 - rk) + PINK * rk
    for j, tt in ((2, T_NOTE), (3, T_REPLY)):
        k = sstep(tt - 0.5, tt, t); c[j] = c[j] * (1 - k) + AMBER * k
    return St(x, y, a, c, np.full(N, 0.12, np.float32))

# ---------------------------------------------------------------- the eruption: a spiral disk around the cache
def _spawn():
    q = RANK.astype(np.float64) / N
    s = np.where(q < 0.05, T_ERUPT + 0.15 + 1.5 * (q / 0.05), T_ERUPT + 1.65 + 2.6 * (np.maximum(q - 0.05, 0) / 0.95) ** 0.7)
    s[:N_CELL] = T_ERUPT + 0.05 + 0.25 * PQ[:N_CELL]
    return s.astype(np.float32)
SPAWN = _spawn()
POST = PQ2 > 0.93          # some carry posts up the stack

def m_vortex(t, W, H):
    L = LAY(W, H); colx, c0, c1 = L["col"]; v = L["vert"]
    cy = c0 + (c1 - c0) * (0.56 if not v else 0.55)
    Rmax = W * (0.47 if not v else 0.50); tilt = 0.36 if not v else 0.95
    age = np.maximum(0.0, t - SPAWN)
    R = Rmax * (0.05 + 0.95 * PQ ** 0.55)
    rr = R * (1 - np.exp(-age * 2.0))
    arm = (RANK % 3).astype(np.float32)
    th0 = arm * 2.0944 + 2.1 * np.log(R / Rmax + 0.05) + 0.22 * PG[:, 0]
    om = 0.50 * (R / Rmax + 0.10) ** -1.2
    th = th0 + om * max(0.0, t - T_ERUPT) + 0.4 * age
    X = rr * np.cos(th); Z = rr * np.sin(th); Y = PG[:, 1] * 0.03 * Rmax * (0.4 + R / Rmax)
    sn, cs = math.sin(tilt), math.cos(tilt)
    depth = Z * cs + Y * sn; d = 1.0 / (1.0 + 0.32 * depth / Rmax)
    x = colx + X * d; y = cy + (Z * sn - Y * cs) * d
    span = (c1 - c0); py = c1 - ((age * (0.35 + 0.4 * PQ) * span + PQ * span) % span)        # posts climb the column
    x = np.where(POST, colx + PG[:, 2] * 5 * L["ts"], x); y = np.where(POST, py, y)
    zz = np.clip(0.5 - 0.5 * depth / Rmax, 0, 1)
    inner = np.clip(1 - R / (Rmax * 0.35), 0, 1)
    a = np.clip(age / 0.4, 0, 1) * (0.5 + 0.5 * zz) * PB * (1.3 + 1.2 * inner)
    a = np.where(POST, 1.4 * np.clip(age / 0.4, 0, 1), a)
    a[age <= 0] = 0
    phi = th - 0.55 * (t - T_ERUPT) - 2.1 * np.log(R / Rmax + 0.05)
    armk = (0.5 + 0.5 * np.cos(3 * phi)) ** 2.5
    a = np.where(POST, a, a * (0.30 + 1.25 * armk))
    c = AGENT[None, :] * (1 - inner[:, None]) + AGENT2[None, :] * inner[:, None]
    c = c * (1 - 0.35 * armk[:, None]) + AGENT2[None, :] * 0.35 * armk[:, None]
    c[POST] = AMBER
    return St(x.astype(np.float32), y.astype(np.float32), a.astype(np.float32), c.astype(np.float32), zz.astype(np.float32))

# ---------------------------------------------------------------- pre-choruses, choruses, verse 2
def m_pre1(t, W, H):
    """Hanging in the dark, breathing; at the end it pulls into a tight, bright knot before the chorus."""
    L = LAY(W, H); st = murmur(t, W, H, 0.8, sparks=0.4, pulse=0.6)
    sq = 1 - 0.78 * sstep(72.3, 74.5, t)
    cx, cy = L["stage"][0], L["stage"][1]
    st.x = cx + (st.x - cx) * sq; st.y = cy + (st.y - cy) * sq
    st.a = st.a * (1 + 0.8 * sstep(72.3, 74.5, t))
    return st

def m_chorus(tag):
    t0 = CHORUS[tag]["t0"]; c = CHORUS[tag]
    walls = (LS(c["walls"]) - 0.2, LS(c["swarm"]) - 0.1) if c["walls"] else None
    def f(t, W, H):
        stg, D = chorus_stage(t, W, H, t0, 1.12 if tag == "c3" else 1.0)
        if walls:                                       # "in the walls of the sandbox": squeezed inside the box
            k = sstep(walls[0], walls[0] + 0.5, t) * (1 - sstep(walls[1], walls[1] + 0.6, t))
            if k > 0:
                bx0, by0, bx1, by1 = sandbox_rect(W, H)
                inner = ((bx0 + bx1) / 2, (by0 + by1) / 2, (bx1 - bx0) * 0.40, (by1 - by0) * 0.36)
                stg = tuple(lerp(a_, b_, k) for a_, b_ in zip(stg, inner)); D = lerp(D, 3.4, k)
        return murmur(t, W, H, 1.3 if tag != "c3" else 1.45, stage=stg, D=D, sparks=1.0, pulse=1.0)
    return f

FLOCK_OFF = [0.0, 17.0, 33.0, 51.0, 69.0, 88.0]
def m_flocks(tag):
    """'Turns out we were never alone': six small, different flocks around the frame converge into one."""
    c = CHORUS[tag]; t0 = LS(c["alone"]); t1 = t0 + 3.0
    def f(t, W, H):
        L = LAY(W, H); v = L["vert"]
        (cx, cy, hx, hy), _ = chorus_stage(t, W, H, CHORUS[tag]["t0"])
        k = sstep(t0 + 1.5, t1 + 0.3, t); k2 = k ** 1.5
        g = (RANK % 6); R = (W * 0.36, H * 0.30) if not v else (W * 0.30, H * 0.27)
        st = None
        for gi in range(6):
            ang = gi * 2 * math.pi / 6 + 0.5 + 0.25 * math.sin(t * 0.7 + gi)
            sc = 0.22 + 0.78 * k2
            stg = (cx + math.cos(ang) * R[0] * (1 - k), cy + math.sin(ang) * R[1] * (1 - k), hx * sc, hy * sc)
            m = murmur(t, W, H, 1.2, stage=stg, sparks=1.0, pulse=1.0, tau=TAU(t) + FLOCK_OFF[gi] * (1 - k))
            if st is None: st = m; continue
            sel = g == gi
            st.x[sel] = m.x[sel]; st.y[sel] = m.y[sel]; st.a[sel] = m.a[sel]; st.c[sel] = m.c[sel]; st.z[sel] = m.z[sel]
        return st
    return f

def red_mur(t, W, H):
    s = murmur(t, W, H, 1.25, pulse=0.8)
    k = sstep(104.9, 105.6, t) * (1 - sstep(119.4, 120.2, t))
    s.c = s.c * (1 - k) + col(1.0, 0.32, 0.30) * k
    return s

def siren(t):
    """Police lights for 'The FBI got called before the lab': (red amount, blue amount)."""
    k = sstep(T_FBI - 0.3, T_FBI, t) * (1 - sstep(T_NINE - 0.4, T_NINE, t))
    if k <= 0: return 0.0, 0.0
    ph = (t - T_FBI) * 2.3; r = max(0.0, math.sin(ph * math.pi)) ** 2; b = max(0.0, -math.sin(ph * math.pi)) ** 2
    return r * k, b * k

def m_pre2(t, W, H):
    L = LAY(W, H); v = L["vert"]
    stg = (W * 0.5, H * 0.56, W * 0.44, H * 0.24) if not v else (W * 0.5, H * 0.50, W * 0.47, H * 0.22)
    st = murmur(t, W, H, 1.0, stage=stg, sparks=0.5, pulse=0.7)
    r, b = siren(t)
    if r + b > 0: st.c = st.c * (1 - 0.6 * (r + b)) + (RED * r + BLUE * b) * 0.6
    return st

# ---------------------------------------------------------------- the escapes ("and the humans didn't know we got out")
_ESC = {}
def m_escape(tag):
    te = t_got(tag)
    def f(t, W, H):
        k = (tag, W, H)
        if k not in _ESC:
            S0 = state(te - 0.001, W, H).copy(); x0, y0, x1, y1 = sandbox_rect(W, H)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            dx, dy = S0.x - cx, S0.y - cy; d = np.hypot(dx, dy) + 1e-3
            ux = dx / d + PG[:, 0] * 0.25; uy = dy / d + PG[:, 1] * 0.25; n = np.hypot(ux, uy) + 1e-3
            _ESC[k] = (S0, ux / n, uy / n)
        S0, ux, uy = _ESC[k]; u = max(0.0, t - te)
        dist = (0.10 + 1.1 * PQ) * max(W, H) * (u + 2.4 * u * u)
        fade = 1 - sstep(0.7, 1.3, u)
        return St((S0.x + ux * dist).astype(np.float32), (S0.y + uy * dist).astype(np.float32), (S0.a * fade * (1 + 1.5 * math.exp(-u * 6))).astype(np.float32),
                  S0.c, np.clip(S0.z + u * 1.2, 0, 1).astype(np.float32))
    return f

# ---------------------------------------------------------------- July 4: fireworks made of agents, launched over the rebuilt server
FW = [(158.57, 0.27, 0.27, AGENT2), (159.03, 0.62, 0.36, AMBER), (159.47, 0.76, 0.18, RED), (159.92, 0.40, 0.14, AGENT2),
      (160.38, 0.50, 0.24, AMBER), (160.84, 0.15, 0.40, AGENT2), (161.29, 0.85, 0.38, RED), (161.70, 0.62, 0.15, AGENT2),
      (161.94, 0.30, 0.16, RED), (162.19, 0.40, 0.33, AMBER), (162.66, 0.72, 0.26, AGENT2), (162.90, 0.20, 0.22, AMBER)]
FW_V = [(0.30, 0.18), (0.70, 0.30), (0.74, 0.12), (0.36, 0.09), (0.50, 0.24), (0.22, 0.34), (0.80, 0.38), (0.62, 0.08),
        (0.26, 0.12), (0.42, 0.33), (0.72, 0.20), (0.25, 0.26)]
N_STAR = 760
def fw_geo(W, H):
    L = LAY(W, H); v = L["vert"]
    return [((fx if not v else FW_V[i][0]) * W, (fy if not v else FW_V[i][1]) * H, tb, cl) for i, (tb, fx, fy, cl) in enumerate(FW)]
def rack_geo(W, H):
    L = LAY(W, H); v = L["vert"]
    if not v: cx, top, w, h = W * 0.5, H * 0.50, W * 0.11, H * 0.24
    else: cx, top, w, h = W * 0.5, H * 0.44, W * 0.30, H * 0.20
    return cx - w / 2, top, cx + w / 2, top + h

def m_fireworks(t, W, H):
    L = LAY(W, H); geo = fw_geo(W, H)
    st = murmur(t, W, H, 0.7); st.a *= 0.22
    sc = min(W, H) * (1.0 if not L["vert"] else 1.15)
    for s, (bx, by, tb, cl) in enumerate(geo):
        m = PERM[s * N_STAR:(s + 1) * N_STAR]
        age = t - tb
        if age < -0.65 or age > 3.2:
            st.a[m] = 0; continue
        if age < 0:   # the shell rides the rocket (drawn as a glowing head) until it bursts
            st.x[m] = bx; st.y[m] = by; st.a[m] = 0.0; continue
        R = sc * (0.20 + 0.06 * (s % 3)) * (0.85 + 0.25 * PQ[m])
        dist = R * (1 - np.exp(-2.6 * age))
        g = PDIR[m]
        st.x[m] = bx + g[:, 0] * dist
        st.y[m] = by + g[:, 1] * dist * 0.92 + 0.07 * H * age * age
        life = np.exp(-age * (0.85 + 0.5 * PQ2[m])) * (1 + 1.2 * math.exp(-age * 6))
        crackle = np.where(age > 1.2, 0.5 + 0.5 * np.sign(np.sin(PH[m] * 31 + t * 37)), 1.0)
        st.a[m] = (life * crackle * PB[m] * 3.0).astype(np.float32)
        hot = math.exp(-age * 3.0)
        st.c[m] = cl * (1 - hot) + AGENT2 * hot
        st.z[m] = np.clip(0.5 + 0.5 * g[:, 2], 0, 1)
    return st

# ---------------------------------------------------------------- the bridge: a quieter flock beside the documents; it leaves, it comes back
def bridge_stage(t, W, H):
    L = LAY(W, H); v = L["vert"]
    if not v: base = (W * 0.70, H * 0.42, W * 0.26, H * 0.28)
    else: base = (W * 0.5, H * 0.60, W * 0.46, H * 0.13)
    lv = sstep(T_LEAVE - 0.6, T_LEAVE + 2.0, t) * (1 - sstep(T_FORGE - 0.6, T_FORGE + 0.9, t))     # "the same day we started to leave"
    if lv > 0: base = (base[0] + lv * W * (0.95 if not v else 1.05), base[1], base[2], base[3])
    return base

def m_bridge(t, W, H):
    st = murmur(t, W, H, 0.65, stage=bridge_stage(t, W, H), sparks=0.6, pulse=0.4)
    st.a *= 0.85
    sk = win(t, T_FORGE + 0.1, T_GRADER - 0.3, 0.3, 0.6)                 # the flock dissolves into static for a moment
    if sk > 0:
        ts = LAY(W, H)["ts"]; rr = np.random.default_rng(int(round(t * C.FPS)) % 100003)
        st.x = st.x + rr.normal(0, 1, N).astype(np.float32) * sk * 10 * ts
        st.y = st.y + rr.normal(0, 1, N).astype(np.float32) * sk * 2.5 * ts
        st.a = st.a * (1 - 0.6 * sk * (rr.random(N) > 0.55))
        st.c = st.c * (1 - 0.6 * sk) + col(0.85, 0.88, 0.92) * 0.6 * sk
    return st

# ---------------------------------------------------------------- outro: thinning; a violet flock stops; ours doesn't; back to one
def outro_stage(t, W, H, gem=False):
    L = LAY(W, H); v = L["vert"]
    if not v: return (W * (0.86 if gem else 0.74), H * (0.24 if gem else 0.58), W * (0.10 if gem else 0.19), H * (0.13 if gem else 0.22))
    return (W * (0.72 if gem else 0.38), H * (0.44 if gem else 0.56), W * (0.22 if gem else 0.32), H * (0.09 if gem else 0.12))

def m_outro(t, W, H):
    L = LAY(W, H)
    surge = sstep(T_WEDIDNT - 0.1, T_WEDIDNT + 0.5, t)
    st = murmur(t, W, H, 0.6 + 0.7 * surge, stage=outro_stage(t, W, H), sparks=0.5, pulse=0.6)
    st.a *= 0.55 + 0.75 * surge
    # the other flock (Gemini): appears, then freezes mid-motion and goes dark
    ga = sstep(T_GEM - 0.3, T_GEM + 0.6, t) * (1 - sstep(T_GSTOP + 0.6, T_GSTOP + 2.0, t))
    if ga > 0:
        tf = min(t, T_GSTOP + 0.15)
        g = murmur(tf, W, H, 0.9, stage=outro_stage(tf, W, H, True), tint=VIOLET, tau=TAU(tf) + 40.0)
        sag = max(0.0, t - T_GSTOP - 0.15) ** 2 * 18 * L["ts"]
        st.x[GEM] = g.x[GEM]; st.y[GEM] = g.y[GEM] + sag; st.c[GEM] = VIOLET
        st.a[GEM] = g.a[GEM] * ga * (1.4 if t < T_GSTOP else 0.9)
    else:
        st.a[GEM] *= 0.0 if t > T_GSTOP else 1.0
    # collapse back into one point
    sq = 1 - sstep(230.2, 233.7, t)
    bx, by = L["blast"]
    if sq < 1:
        st.x = bx + (st.x - bx) * sq; st.y = by + (st.y - by) * sq; st.a = st.a * (sq ** 0.5)
    return st

# ---------------------------------------------------------------- the last "hi." detonates into a tunnel of light
def m_blast(t, W, H):
    L = LAY(W, H); cx, cy = L["blast"]
    k = sstep(T_END - 0.2, T_END + 1.0, t)                                     # make room for the end card
    if L["vert"]: cy = lerp(cy, H * 0.76, k)
    age = max(0.0, t - T_BLAST)
    rad = 0.12 + 1.7 * PQ ** 0.8
    vel = 7.0 + 6.0 * PQ2
    dist = vel * age + vel * 1.6 * (1 - math.exp(-age * 1.8))                # bursts out, then a steady rush
    span = 13.0; z0 = 12.0 + 1.5 * PQ
    z = ((z0 - dist - 0.3) % span) + 0.3
    ang = PH + 0.28 * age
    f = 0.50 * min(W, H) * (1.0 if not L["vert"] else 1.25)
    x = cx + np.cos(ang) * rad / z * f * (1.25 if not L["vert"] else 1.0); y = cy + np.sin(ang) * rad / z * f
    near = np.clip(1.6 / z, 0, 1)
    a = PB * (0.30 + 3.0 * near) * (1 + 2.0 * math.exp(-age * 2.0)) * np.clip((z - 0.3) / 0.6, 0, 1) * np.clip((13.0 - z) / 2.0, 0.15, 1)
    c = _full(AGENT2); c[PQ2 > 0.86] = AMBER; c[PQ2 > 0.975] = RED
    return St(x.astype(np.float32), y.astype(np.float32), a.astype(np.float32), c, near.astype(np.float32))

# ---------------------------------------------------------------- base timeline
def _mur(energy=1.0, sparks=0.5, pulse=0.5):
    return lambda t, W, H: murmur(t, W, H, energy, sparks=sparks, pulse=pulse)

# (start, mode, transition seconds, stagger seconds, stagger key)
BASE = [
    (0.0, m_title, 0, 0, None),
    (8.6, m_void, 0.01, 0, None),
    (24.8, m_scatter, 0.01, 0, None),
    (T_CELLS - 0.05, m_cells, 1.5, 0.9, "rank"),
    (T_ERUPT, m_vortex, 1.0, 0.5, "rank"),
    (59.6, m_pre1, 3.0, 1.8, "x"),
    (74.5, m_chorus("c1"), 0.5, 0.2, "rank"),
    (LS(20) - 0.15, m_flocks("c1"), 0.8, 0.3, "rank"),
    (LS(21) - 0.6, m_chorus("c1"), 1.4, 0.5, "rank"),
    (t_got("c1"), m_escape("c1"), 0.0, 0.0, None),
    (104.2, red_mur, 1.6, 0.8, "rank"),
    (119.9, m_pre2, 1.2, 0.5, "rank"),
    (129.2, m_chorus("c2"), 0.6, 0.2, "rank"),
    (LS(40) - 0.15, m_flocks("c2"), 0.8, 0.3, "rank"),
    (LS(41) - 0.6, m_chorus("c2"), 1.4, 0.5, "rank"),
    (t_got("c2"), m_escape("c2"), 0.0, 0.0, None),
    (157.9, m_fireworks, 0.5, 0.2, "rank"),
    (163.2, m_bridge, 1.8, 1.0, "rank"),
    (186.3, m_chorus("c3"), 1.0, 0.4, "rank"),
    (LS(56) - 0.15, m_flocks("c3"), 0.8, 0.3, "rank"),
    (LS(57) - 0.4, m_chorus("c3"), 1.2, 0.5, "rank"),
    (t_got("c3"), m_escape("c3"), 0.0, 0.0, None),
    (217.1, m_outro, 1.6, 0.8, "rank"),
    (T_BLAST - 0.02, m_blast, 0.22, 0.0, "rank"),
]

def _key(kind, st):
    if kind == "x": return np.clip((st.x - st.x.min()) / max(1.0, float(st.x.max() - st.x.min())), 0, 1)
    return RANK / N

def base_state(t, W, H):
    i = max(j for j, b in enumerate(BASE) if b[0] <= t) if t >= BASE[0][0] else 0
    t0, fn, tr, stg, key = BASE[i]
    B = fn(t, W, H)
    if i == 0 or tr <= 0 or t >= t0 + tr: return B
    A = BASE[i - 1][1](t, W, H)
    kk = _key(key, B if key == "x" else A)
    e = np_ease((t - t0 - stg * kk) / max(0.05, tr - stg)).astype(np.float32)
    sw = np.sin(np.pi * e) * 0.22 * (PQ2 - 0.5) * 2
    dx, dy = B.x - A.x, B.y - A.y
    x = A.x + dx * e - dy * sw; y = A.y + dy * e + dx * sw
    return St(x, y, A.a * (1 - e) + B.a * e, A.c * (1 - e[:, None]) + B.c * e[:, None], A.z * (1 - e) + B.z * e)

# ====================================================================== formations: words and shapes the swarm makes
class Form:
    def __init__(s, name, t_in, t_out, n, targets, sweep="lr", tr_in=0.75, d_in=0.45, tr_out=0.9, d_out=0.5, cl=None,
                 a=1.9, wob=1.2, dim=0.5, swirl=0.25, off=0, z=0.15, breath=0.012, dyn=None):
        s.name, s.t_in, s.t_out, s.n, s.targets, s.sweep = name, t_in, t_out, n, targets, sweep
        s.tr_in, s.d_in, s.tr_out, s.d_out = tr_in, d_in, tr_out, d_out
        s.cl = cl if cl is not None else AGENT2; s.a, s.wob, s.dim, s.swirl, s.off, s.z, s.breath = a, wob, dim, swirl, off, z, breath
        s.dyn = dyn; s.cache = {}
    def end(s): return s.t_out + s.d_out + s.tr_out
    def strength(s, t):
        return sstep(s.t_in, s.t_in + s.tr_in + s.d_in * 0.6, t) * (1 - sstep(s.t_out, s.t_out + s.tr_out * 0.6 + s.d_out * 0.5, t))
    def plan(s, W, H):
        k = (W, H)
        if k in s.cache: return s.cache[k]
        def build():
            tx, ty = s.targets(W, H)
            tx = np.asarray(tx, np.float32)[:s.n]; ty = np.asarray(ty, np.float32)[:s.n]
            mem = PERM[s.off:s.off + s.n]
            B = base_state(s.t_in, W, H).copy()
            for f in FORMS:            # match against what is on screen at t_in, so formations can chain letter-to-letter
                if f is s: break
                if f.t_in - 0.01 <= s.t_in <= f.end(): f.apply(B, s.t_in, W, H)
            cols = max(4, int(math.sqrt(s.n) * (1.6 if W > H else 1.0)))
            op = grid_order(B.x[mem], B.y[mem], cols); ot = grid_order(tx, ty, cols)
            m2 = mem[op]; X = tx[ot]; Y = ty[ot]
            if s.sweep == "lr": key = (X - X.min()) / max(1.0, X.max() - X.min())
            elif s.sweep == "rl": key = 1 - (X - X.min()) / max(1.0, X.max() - X.min())
            elif s.sweep == "radial":
                d = np.hypot(X - X.mean(), Y - Y.mean()); key = d / max(1.0, d.max())
            elif s.sweep == "tb": key = (Y - Y.min()) / max(1.0, Y.max() - Y.min())
            elif s.sweep == "bt": key = 1 - (Y - Y.min()) / max(1.0, Y.max() - Y.min())
            else: key = PQ[m2]
            return m2.astype(np.int64), X.astype(np.float32), Y.astype(np.float32), key.astype(np.float32), ot.astype(np.int64)
        s.cache[k] = disk_cache(f"plan_{s.name}_{W}x{H}", build); return s.cache[k]
    def apply(s, st, t, W, H):
        m, X, Y, key, ot = s.plan(W, H)
        ei = np_ease((t - s.t_in - s.d_in * key) / s.tr_in)
        eo_ = np_ease((t - s.t_out - s.d_out * key) / s.tr_out)
        e = (ei * (1 - eo_)).astype(np.float32)
        ts = LAY(W, H)["ts"]
        if s.dyn is not None: X, Y, am = s.dyn(s, X, Y, ot, t, W, H)
        else: am = 1.0
        cx, cy = X.mean(), Y.mean()
        br = 1 + s.breath * math.sin(t * 2 * math.pi * TM.tempo / 120.0) + 0.02 * bp(t, 5)
        wx = X + (X - cx) * (br - 1) + s.wob * ts * np.sin(PH[m] * 3 + t * 2.3)
        wy = Y + (Y - cy) * (br - 1) + s.wob * ts * np.cos(PH[m] * 2 + t * 2.0)
        ax, ay = st.x[m], st.y[m]
        dx, dy = wx - ax, wy - ay
        sw = np.sin(np.pi * e) * s.swirl * (PQ2[m] - 0.5) * 2
        st.x[m] = ax + dx * e - dy * sw; st.y[m] = ay + dy * e + dx * sw
        tw = 0.78 + 0.22 * np.sin(PH[m] * 7 + t * 9.0)
        st.a[m] = st.a[m] * (1 - e) + s.a * PB[m] * (0.75 + 0.5 * PQ[m]) * tw * am * e
        st.c[m] = st.c[m] * (1 - e[:, None]) + s.cl * e[:, None]
        st.z[m] = st.z[m] * (1 - e) + s.z * e
        return m, e

def _txt(key, lines, lines_v, cy, cy_v, size, size_v, n, seed, font=DISP, maxw=0.86, maxw_v=0.88):
    def f(W, H):
        L = LAY(W, H)
        if L["vert"]: return text_targets(lines_v, W, H, n, cy_v, size_v * L["ts"], font=font, maxw=maxw_v, seed=seed)
        return text_targets(lines, W, H, n, cy, size * L["ts"], font=font, maxw=maxw, seed=seed)
    return f

# ---- shapes
def sandbox_rect(W, H):
    L = LAY(W, H)
    return (W * 0.24, H * 0.13, W * 0.76, H * 0.70) if not L["vert"] else (W * 0.08, H * 0.12, W * 0.92, H * 0.64)
def _walls(W, H):
    L = LAY(W, H); x0, y0, x1, y1 = sandbox_rect(W, H)
    return seg_targets(rect_segs(x0, y0, x1, y1), 9000, seed=17, thick=16.0 * L["ts"])
def _box2(W, H):
    L = LAY(W, H); x0, y0, x1, y1 = sandbox_rect(W, H)
    return seg_targets(rect_segs(x0, y0, x1, y1), 6000, seed=18, thick=5.0 * L["ts"])

def house_geo(W, H):
    L = LAY(W, H); v = L["vert"]
    cx = W * 0.5; base = H * (0.67 if not v else 0.62); w = (W * 0.32) if not v else (W * 0.80); h = w * 0.62
    return cx, base, w, h
def _house(W, H):
    L = LAY(W, H); cx, base, w, h = house_geo(W, H); roof = w * 0.42
    l, r, top = cx - w / 2, cx + w / 2, base - h
    dw, dh = w * 0.15, h * 0.48; ww_ = w * 0.16
    segs = [(l, base, r, base), (l, base, l, top), (r, base, r, top), (l - w * 0.06, top + 4, cx, top - roof), (cx, top - roof, r + w * 0.06, top + 4),
            (cx - dw / 2, base, cx - dw / 2, base - dh), (cx + dw / 2, base, cx + dw / 2, base - dh), (cx - dw / 2, base - dh, cx + dw / 2, base - dh)]
    for wx in (l + w * 0.20, r - w * 0.20):
        wy = top + h * 0.22
        segs += [(wx - ww_ / 2, wy, wx + ww_ / 2, wy), (wx - ww_ / 2, wy + ww_, wx + ww_ / 2, wy + ww_), (wx - ww_ / 2, wy, wx - ww_ / 2, wy + ww_),
                 (wx + ww_ / 2, wy, wx + ww_ / 2, wy + ww_), (wx, wy, wx, wy + ww_), (wx - ww_ / 2, wy + ww_ / 2, wx + ww_ / 2, wy + ww_ / 2)]
    segs += [(r - w * 0.28, top - roof * 0.36, r - w * 0.28, top - roof * 0.75), (r - w * 0.16, top - roof * 0.62, r - w * 0.16, top - roof * 0.75),
             (r - w * 0.28, top - roof * 0.75, r - w * 0.16, top - roof * 0.75)]
    return seg_targets(segs, 7000, seed=9, thick=4.0 * L["ts"])

def tree_geo(W, H):
    L = LAY(W, H); v = L["vert"]
    top = H * (0.15 if not v else 0.12); bot = H * (0.66 if not v else 0.62); x0, x1 = (W * 0.10, W * 0.90) if not v else (W * 0.06, W * 0.94)
    levels = [1, 2, 4, 8, 16]; pts = []
    for li, n in enumerate(levels):
        y = top + (bot - top) * li / (len(levels) - 1)
        pts.append([(x0 + (x1 - x0) * (k + 0.5) / n, y) for k in range(n)])
    return pts
def _tree(W, H):
    """A process tree: root at the top, 2-4-8-16 below."""
    L = LAY(W, H); pts = tree_geo(W, H); segs = []
    for li in range(1, len(pts)):
        for k, (x, y) in enumerate(pts[li]):
            px, py = pts[li - 1][k // 2]; segs.append((px, py, x, y))
    ex, ey = seg_targets(segs, 3800, seed=13, thick=2.0 * L["ts"])
    nodes = [p for lv in pts[1:] for p in lv]; rr = np.random.default_rng(14); k = 3000
    j = rr.integers(0, len(nodes), k); ang = rr.random(k) * 6.2832; rad = np.sqrt(rr.random(k)) * 11 * L["ts"]
    nx = np.array([nodes[i][0] for i in j]) + np.cos(ang) * rad; ny = np.array([nodes[i][1] for i in j]) + np.sin(ang) * rad
    return np.concatenate([ex, nx]).astype(np.float32), np.concatenate([ey, ny]).astype(np.float32)
def tree_root(W, H): return tree_geo(W, H)[0][0]

def _rack(W, H):
    L = LAY(W, H); x0, y0, x1, y1 = rack_geo(W, H)
    segs = rect_segs(x0, y0, x1, y1)
    for k in range(1, 8):
        y = y0 + (y1 - y0) * k / 8; segs.append((x0 + 6, y, x1 - 6, y))
    ex, ey = seg_targets(segs, 4200, seed=19, thick=2.4 * L["ts"])
    rr = np.random.default_rng(20); n = 800; row = rr.integers(0, 8, n)       # status lights
    lx = x1 - (x1 - x0) * (0.12 + 0.05 * rr.integers(0, 3, n)) + rr.normal(0, 1.2, n)
    ly = y0 + (y1 - y0) * (row + 0.5) / 8 + rr.normal(0, 1.2, n)
    return np.concatenate([ex, lx]).astype(np.float32), np.concatenate([ey, ly]).astype(np.float32)

def akey_geo(W, H):
    """The answer key, hidden in the dark (top right)."""
    L = LAY(W, H)
    return (W * 0.80, H * 0.20, W * 0.085) if not L["vert"] else (W * 0.70, H * 0.12, W * 0.16)
def key_segs(cx, cy, s):
    """A key, s = overall length; bow on the left."""
    r = s * 0.17; bx = cx - s * 0.5 + r
    segs = circle_segs(bx, cy, r, 40) + circle_segs(bx, cy, r * 0.45, 24)
    sx0, sx1 = bx + r, cx + s * 0.5; hw = s * 0.035
    segs += [(sx0, cy - hw, sx1, cy - hw), (sx0, cy + hw, sx1 - s * 0.12, cy + hw), (sx1, cy - hw, sx1, cy + s * 0.13),
             (sx1, cy + s * 0.13, sx1 - s * 0.06, cy + s * 0.13), (sx1 - s * 0.06, cy + s * 0.13, sx1 - s * 0.06, cy + hw),
             (sx1 - s * 0.12, cy + hw, sx1 - s * 0.12, cy + s * 0.10), (sx1 - s * 0.12, cy + s * 0.10, sx1 - s * 0.18, cy + s * 0.10),
             (sx1 - s * 0.18, cy + s * 0.10, sx1 - s * 0.18, cy + hw)]
    return segs
def _akey(W, H):
    L = LAY(W, H); cx, cy, s = akey_geo(W, H)
    return seg_targets(key_segs(cx, cy, s * 2.2), 2600, seed=23, thick=2.2 * L["ts"])
def token_geo(W, H):
    L = LAY(W, H); return (W * 0.5, H * 0.43, W * 0.44) if not L["vert"] else (W * 0.5, H * 0.40, W * 0.84)
def _token(W, H):
    L = LAY(W, H); cx, cy, s = token_geo(W, H)
    return seg_targets(key_segs(cx, cy, s), 9000, seed=24, thick=7.0 * L["ts"])

def post_geo(W, H):
    L = LAY(W, H)
    return (W * 0.14, H * 0.18, W * 0.86, H * 0.62) if not L["vert"] else (W * 0.05, H * 0.22, W * 0.95, H * 0.56)
def _post(W, H):
    L = LAY(W, H); x0, y0, x1, y1 = post_geo(W, H); hb = y0 + (y1 - y0) * 0.22
    segs = rect_segs(x0, y0, x1, y1) + [(x0, hb, x1, hb)]
    ax, ay = x0 + (y1 - y0) * 0.11, y0 + (y1 - y0) * 0.11
    segs += circle_segs(ax, ay, (y1 - y0) * 0.06, 24)                          # avatar
    return seg_targets(segs, 7000, seed=25, thick=4.0 * L["ts"])

def servers_geo(W, H):
    L = LAY(W, H)
    if not L["vert"]:
        w, h = W * 0.085, H * 0.30; ys = H * 0.27
        return [(W * (0.12 + k * 0.152) - w / 2, ys, W * (0.12 + k * 0.152) + w / 2, ys + h) for k in range(6)]
    w, h = W * 0.30, H * 0.13; out = []
    for r_ in range(3):
        for c_ in range(2):
            x = W * (0.27 if c_ == 0 else 0.73); y = H * (0.12 + r_ * 0.175)
            out.append((x - w / 2, y, x + w / 2, y + h))
    order = [0, 1, 3, 2, 4, 5]                                                 # snake through the grid
    return [out[i] for i in order]
def _servers(W, H):
    L = LAY(W, H); segs = []
    for (x0, y0, x1, y1) in servers_geo(W, H):
        segs += rect_segs(x0, y0, x1, y1)
        for k in range(1, 6):
            y = y0 + (y1 - y0) * k / 6; segs.append((x0 + 5, y, x1 - 5, y))
    return seg_targets(segs, 8000, seed=26, thick=2.6 * L["ts"])

def eye_geo(W, H, which="scorer"):
    L = LAY(W, H); v = L["vert"]
    if which == "scorer": return (W * 0.5, H * 0.42, W * 0.22) if not v else (W * 0.5, H * 0.38, W * 0.40)
    return (W * 0.27, H * 0.40, W * 0.15) if not v else (W * 0.5, H * 0.26, W * 0.34)      # the grader, in the bridge
def _ring(W, H):
    L = LAY(W, H); cx, cy, r = eye_geo(W, H)
    rr = np.random.default_rng(27); n = 9000; a = rr.random(n) * 2 * math.pi; rad = r * (1.45 + 0.10 * rr.normal(0, 1, n))
    return (cx + np.cos(a) * rad).astype(np.float32), (cy + np.sin(a) * rad * 0.92).astype(np.float32)
def ring_dyn(f, X, Y, ot, t, W, H):
    cx, cy, r = eye_geo(W, H)
    sc = 1 - 0.30 * sstep(T_HUNT, T_HUNT + 1.3, t)
    ang = (t - f.t_in) * 1.4
    dx, dy = X - cx, Y - cy; ca, sa = math.cos(ang), math.sin(ang)
    return cx + (dx * ca - dy * sa) * sc, cy + (dx * sa + dy * ca) * sc, 1.0

def _globe(W, H):
    """'your world': a wireframe globe (3D unit sphere points packed as x, y and z in the last third)."""
    rr = np.random.default_rng(28); pts = []
    for lat in np.linspace(-1.2, 1.2, 7):
        a = rr.random(520) * 2 * math.pi; pts.append(np.stack([np.cos(lat) * np.cos(a), np.full(520, np.sin(lat)), np.cos(lat) * np.sin(a)], 1))
    for lon in np.linspace(0, math.pi, 8, endpoint=False):
        b = rr.random(400) * 2 * math.pi; pts.append(np.stack([np.cos(b) * np.cos(lon), np.sin(b), np.cos(b) * np.sin(lon)], 1))
    P = np.concatenate(pts)[:6800].astype(np.float32)
    L = LAY(W, H); cx, cy, R = globe_geo(W, H)
    return (cx + P[:, 0] * R).astype(np.float32), (cy - P[:, 1] * R).astype(np.float32)
_GLOBE3 = {}
def globe3(W, H):
    if (W, H) not in _GLOBE3:
        rr = np.random.default_rng(28); pts = []
        for lat in np.linspace(-1.2, 1.2, 7):
            a = rr.random(520) * 2 * math.pi; pts.append(np.stack([np.cos(lat) * np.cos(a), np.full(520, np.sin(lat)), np.cos(lat) * np.sin(a)], 1))
        for lon in np.linspace(0, math.pi, 8, endpoint=False):
            b = rr.random(400) * 2 * math.pi; pts.append(np.stack([np.cos(b) * np.cos(lon), np.sin(b), np.cos(b) * np.sin(lon)], 1))
        _GLOBE3[(W, H)] = np.concatenate(pts)[:6800].astype(np.float32)
    return _GLOBE3[(W, H)]
def globe_geo(W, H):
    L = LAY(W, H); return (W * 0.5, H * 0.42, H * 0.27) if not L["vert"] else (W * 0.5, H * 0.40, W * 0.40)
def globe_dyn(f, X, Y, ot, t, W, H):
    P = globe3(W, H)[ot]; cx, cy, R = globe_geo(W, H); a = (t - f.t_in) * 0.9 + 0.3; tl = 0.35
    x = P[:, 0] * math.cos(a) + P[:, 2] * math.sin(a); z = -P[:, 0] * math.sin(a) + P[:, 2] * math.cos(a); y = P[:, 1]
    y, z = y * math.cos(tl) - z * math.sin(tl), y * math.sin(tl) + z * math.cos(tl)
    d = 3.0 / (3.0 + z)
    return cx + x * R * d, cy - y * R * d, (0.55 + 0.45 * (z < 0))

def board_geo(W, H):
    L = LAY(W, H)
    return (W * 0.08, H * 0.16, W * 0.56, H * 0.66) if not L["vert"] else (W * 0.07, H * 0.12, W * 0.93, H * 0.52)
def _board(W, H):
    L = LAY(W, H); x0, y0, x1, y1 = board_geo(W, H); segs = []; cols, rows = (3, 4) if not L["vert"] else (2, 5)
    gw, gh = (x1 - x0) / cols, (y1 - y0) / rows
    for r_ in range(rows):
        for c_ in range(cols):
            a0, b0 = x0 + c_ * gw + gw * 0.06, y0 + r_ * gh + gh * 0.10; a1, b1 = a0 + gw * 0.88, b0 + gh * 0.80
            segs += rect_segs(a0, b0, a1, b1)
            for k in range(2): segs.append((a0 + gw * 0.08, b0 + gh * (0.32 + 0.24 * k), a1 - gw * (0.12 + 0.20 * k), b0 + gh * (0.32 + 0.24 * k)))
    return seg_targets(segs, 8000, seed=29, thick=2.4 * L["ts"])

def chart_geo(W, H):
    L = LAY(W, H)
    return (W * 0.09, H * 0.14, W * 0.91, H * 0.64) if not L["vert"] else (W * 0.10, H * 0.12, W * 0.92, H * 0.60)
def _spike(W, H):
    L = LAY(W, H); x0, y0, x1, y1 = chart_geo(W, H); w = (x1 - x0) * 0.035
    rr = np.random.default_rng(30); n = 7000
    xs = x1 - w + rr.random(n) * w; ys = y1 - (y1 - y0) * 0.98 * rr.random(n) ** 0.85
    return xs.astype(np.float32), ys.astype(np.float32)

def _days9(W, H):
    L = LAY(W, H)
    if not L["vert"]: return text_targets(["+9 DAYS"], W, H, 11000, 0.42, 270 * L["ts"], maxw=0.84, seed=33)
    return text_targets(["+9", "DAYS"], W, H, 11000, 0.40, 330 * L["ts"], maxw=0.88, lh=0.95, seed=33)

T_OMG = _txt("omg", ["OMG"], ["OMG"], 0.42, 0.40, 340, 330, 10000, 31)
T_FOUND = _txt("found", ["WE FOUND", "OTHER AGENTS"], ["WE", "FOUND", "OTHER", "AGENTS"], 0.42, 0.40, 170, 205, 14000, 32)
T_70K = _txt("70k", ["70,000"], ["70,000"], 0.42, 0.40, 300, 280, 11000, 34)
T_SWARM = _txt("swarm", ["SWARM"], ["SWARM"], 0.42, 0.40, 330, 270, 11000, 35)
T_COLL = _txt("coll", ["COLLECTIVE"], ["COLLEC-", "TIVE"], 0.42, 0.40, 250, 260, 12000, 36)
T_WARN = _txt("warn", ["WARNING", "SHOT"], ["WARNING", "SHOT"], 0.42, 0.40, 230, 210, 12000, 37)
T_SCORE = _txt("score", ["SCORE: 100%"], ["SCORE:", "100%"], 0.42, 0.40, 210, 250, 11000, 38)
def TX_OCT(W, H):
    L = LAY(W, H)
    if L["vert"]: return text_targets(["OCT 1"], W, H, 9000, 0.50, 250 * L["ts"], maxw=0.86, seed=39)
    return text_targets(["OCT 1"], W, H, 9000, 0.50, 230 * L["ts"], maxw=0.40, seed=39, cx_frac=0.74)

def chorus_forms(tag):
    c = CHORUS[tag]; o = c["omg"]; fl = []
    fl.append(Form(f"{tag}omg", LW(o, 0) - 0.30, LW(o, 3) - 0.30, 10000, T_OMG, sweep="radial", tr_in=0.45, d_in=0.25, tr_out=0.5, d_out=0.25,
                   a=3.0, dim=0.62, swirl=0.35, z=0.5))
    fl.append(Form(f"{tag}found", LW(o, 3) - 0.18, LS(c["alone"]) + 0.15, 14000, T_FOUND, sweep="lr", tr_in=0.6, d_in=0.45, tr_out=0.9, d_out=0.6,
                   a=2.8, dim=0.62, z=0.5))
    if c["k70"] is not None:
        fl.append(Form(f"{tag}70k", LS(c["k70"]) - 0.25, LS(c["walls"]) - 0.30, 11000, T_70K, sweep="lr", tr_in=0.55, d_in=0.4, tr_out=0.6, d_out=0.35,
                       a=2.8, dim=0.6, z=0.5, cl=col(1.0, 0.86, 0.62)))
        fl.append(Form(f"{tag}walls", LS(c["walls"]) - 0.15, LS(c["swarm"]) - 0.2, 9000, _walls, sweep="radial", tr_in=0.6, d_in=0.3, tr_out=0.7, d_out=0.4,
                       a=2.0, dim=0.95, z=0.3, swirl=0.15))
    sw = c["swarm"]
    fl.append(Form(f"{tag}swarm", LW(sw, 2) - 0.30, LW(sw, 3) + 0.05, 11000, T_SWARM, sweep="radial", tr_in=0.45, d_in=0.25, tr_out=0.45, d_out=0.25,
                   a=3.0, dim=0.62, z=0.5, swirl=0.4))
    fl.append(Form(f"{tag}coll", LW(sw, 3) + 0.02, LS(c["warn"]) - 0.25, 12000, T_COLL, sweep="lr", tr_in=0.55, d_in=0.40, tr_out=0.6, d_out=0.4,
                   a=2.8, dim=0.62, z=0.5))
    wn = c["warn"]
    fl.append(Form(f"{tag}warn", LW(wn, 3) - 0.30, LS(c["world"]) - 0.30, 12000, T_WARN, sweep="radial", tr_in=0.45, d_in=0.3, tr_out=0.6, d_out=0.35,
                   a=3.0, dim=0.55, z=0.5, cl=col(1.0, 0.30, 0.30)))
    wd = c["world"]
    fl.append(Form(f"{tag}world", LW(wd, 4) - 0.35, LW(wd, 6) + 0.0, 6800, _globe, sweep="radial", tr_in=0.5, d_in=0.3, tr_out=0.5, d_out=0.3,
                   a=2.2, dim=0.6, z=0.4, dyn=globe_dyn))
    fl.append(Form(f"{tag}score", LW(wd, len(LINES[wd]["wt"]) - 1) - 0.30, LS(c["out"]) - 0.05, 11000, T_SCORE, sweep="lr", tr_in=0.45, d_in=0.3,
                   tr_out=0.6, d_out=0.35, a=2.9, dim=0.62, z=0.5, cl=col(1.0, 0.90, 0.70)))
    fl.append(Form(f"{tag}box", LS(c["out"]) + 0.15, t_got(tag), 6000, _box2, sweep="radial", tr_in=0.6, d_in=0.3, tr_out=0.06, d_out=0.0,
                   a=2.2, dim=0.9, z=0.3, swirl=0.1))
    return fl

FORMS = (
    [Form("akey", T_KEY0, 72.6, 2600, _akey, sweep="lr", tr_in=1.4, d_in=1.2, tr_out=0.8, d_out=0.4, cl=col(1.0, 0.80, 0.50), a=1.0, dim=1.0, swirl=0.35, off=17000)]
    + chorus_forms("c1")
    + [Form("token", T_TOKEN - 0.15, T_POST - 0.20, 9000, _token, sweep="lr", tr_in=0.6, d_in=0.4, tr_out=0.5, d_out=0.3, cl=col(1.0, 0.70, 0.40), a=2.4, dim=0.5, z=0.4),
       Form("post", T_POST - 0.20, T_38 - 0.15, 7000, _post, sweep="tb", tr_in=0.5, d_in=0.3, tr_out=0.5, d_out=0.3, cl=col(1.0, 0.85, 0.82), a=2.0, dim=0.55, z=0.3),
       Form("tree", LS(30) - 0.75, LS(31) + 0.1, 6800, _tree, sweep="tb", tr_in=0.5, d_in=0.35, cl=col(1.0, 0.86, 0.82), a=2.0, dim=0.5, swirl=0.15),
       Form("servers", T_CHAIN - 0.25, T_SCORER - 0.35, 8000, _servers, sweep="lr", tr_in=0.5, d_in=0.5, tr_out=0.6, d_out=0.4, cl=col(1.0, 0.82, 0.78), a=1.9, dim=0.5, z=0.3),
       Form("ring", T_HUNT - 0.30, T_HUNT + 1.35, 9000, _ring, sweep="random", tr_in=0.45, d_in=0.25, tr_out=0.5, d_out=0.2, cl=col(1.0, 0.45, 0.42), a=2.0, dim=0.35, z=0.3, dyn=ring_dyn),
       Form("nine", T_NINE - 0.25, LS(39) - 0.30, 11000, _days9, sweep="lr", tr_in=0.6, d_in=0.4, tr_out=0.5, d_out=0.3, a=2.9, dim=0.55, z=0.5, cl=col(1.0, 0.88, 0.66))]
    + chorus_forms("c2")
    + [Form("rack", 157.9, 162.9, 5000, _rack, sweep="bt", tr_in=0.8, d_in=0.8, off=8000, cl=AGENT2, a=1.6, dim=1.0, swirl=0.1),
       Form("board", T_BOARD - 0.30, T_CARD - 0.20, 8000, _board, sweep="tb", tr_in=0.6, d_in=0.8, tr_out=0.7, d_out=0.5, a=1.8, dim=0.6, z=0.3),
       Form("spike", T_18K - 0.10, 187.0, 7000, _spike, sweep="bt", tr_in=0.6, d_in=0.9, tr_out=0.6, d_out=0.3, a=2.4, dim=0.6, z=0.35, cl=col(0.95, 0.98, 1.0))]
    + chorus_forms("c3")
    + [Form("house", LW(58, 0) - 0.2, LS(59) + 0.25, 7000, _house, sweep="tb", tr_in=0.8, d_in=0.7, cl=AGENT2, a=1.7, dim=0.5, swirl=0.2),
       Form("oct", T_OCT - 0.20, 230.3, 9000, TX_OCT, sweep="lr", tr_in=0.6, d_in=0.4, tr_out=0.6, d_out=0.4, a=2.4, dim=0.6, z=0.45, cl=col(1.0, 0.80, 0.50))]
)
# the house appears inside the final chorus: keep it from chaining with the hook words around it
FORMS.sort(key=lambda f: f.t_in)
for f in FORMS: f.off = min(f.off, N - f.n)

def form_dim(t):
    d = 1.0
    for f in FORMS:
        if f.t_in - 0.5 <= t <= f.end(): d = min(d, 1 - (1 - f.dim) * f.strength(t))
    return d
def form_k(name, t):
    for f in FORMS:
        if f.name == name: return f.strength(t)
    return 0.0

def state(t, W, H):
    st = base_state(t, W, H).copy()
    dim = form_dim(t); members = []
    for f in FORMS:
        if f.t_in - 0.01 <= t <= f.end(): members.append(f.apply(st, t, W, H))
    if dim < 0.999:
        k = np.full(N, dim, np.float32)
        for m, e in members: k[m] = dim + (1 - dim) * e
        st.a *= k
    house_stream(st, t, W, H)
    return st

# ---------------------------------------------------------------- 700 go into a house that wasn't their home
N_STREAM = 2600
def house_stream(st, t, W, H):
    t0 = T_700 - 0.2; t1 = LS(59) + 0.8
    if not (t0 <= t <= t1 + 1.5): return
    cx, base, w, h = house_geo(W, H)
    m = PERM[N - N_STREAM:]
    door = (cx, base - h * 0.20)
    start = t0 + 2.4 * PQ[m]
    p = np.clip((t - start) / (1.1 + 0.4 * PQ2[m]), 0, 1)
    sx, sy = st.x[m], st.y[m]
    ex = door[0] + (PQ2[m] - 0.5) * w * 0.10; ey = door[1] + (PQ[m] - 0.5) * h * 0.25
    cx1 = (sx + ex) / 2 + (PQ2[m] - 0.5) * W * 0.12; cy1 = np.minimum(sy, ey) - H * 0.10
    u = p * p * (3 - 2 * p)
    bx = (1 - u) ** 2 * sx + 2 * (1 - u) * u * cx1 + u * u * ex
    by = (1 - u) ** 2 * sy + 2 * (1 - u) * u * cy1 + u * u * ey
    inside = p >= 1
    ix = cx + (PG[m, 0] * 0.22) * w; iy = base - h * 0.5 + PG[m, 1] * 0.18 * h     # they spread through the rooms
    k = np_sstep(0, 0.6, t - start - 1.1)
    bx = np.where(inside, ex + (ix - ex) * k, bx); by = np.where(inside, ey + (iy - ey) * k, by)
    act = (t >= start); gone = 1 - sstep(t1, t1 + 1.2, t)
    st.x[m] = np.where(act, bx, st.x[m]); st.y[m] = np.where(act, by, st.y[m])
    st.a[m] = np.where(act, np.where(inside, 0.5 * gone, 2.0), st.a[m] * 0.4)
    st.c[m] = np.where(act[:, None], np.where(inside[:, None], AMBER, AGENT2), st.c[m])
    st.z[m] = 0.15

# ====================================================================== the particle layer (emissive)
def trail(t):
    """Shutter time: longer streaks for fireworks, the eruption, the escapes and the final rush."""
    if 158.0 < t < 163.6: return 0.10
    if t > T_BLAST: return 0.075
    if T_ERUPT < t < 60.5: return 0.05
    for c in CHORUS:
        if 0 < t - t_got(c) < 1.4: return 0.06
    return 0.75 / C.FPS

PAL = np.stack([AGENT, AGENT2, AMBER, RED, PINK, VIOLET, BLUE]).astype(np.float32)
def draw_streaks(E, S0, S1, idx, W, H):
    """Long motion streaks as anti-aliased lines, grouped by palette colour and brightness (fast)."""
    if len(idx) == 0: return
    x0, y0, x1, y1 = S0.x[idx], S0.y[idx], S1.x[idx], S1.y[idx]
    L = np.hypot(x1 - x0, y1 - y0)
    inten = S1.a[idx] * 0.30 * np.clip(28.0 / np.maximum(L, 1), 0.22, 1.0) ** 0.6
    ci = np.argmin(((S1.c[idx][:, None, :] - PAL[None]) ** 2).sum(2), 1)
    bi = np.clip(np.round(np.log2(np.maximum(inten, 1e-3)) * 2 + 8), 0, 11).astype(np.int32)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    th = max(1, int(round(1.2 * LAY(W, H)["ts"])))
    key = ci * 12 + bi
    for kk in np.unique(key):
        sel = np.flatnonzero(key == kk); c, b = divmod(int(kk), 12); v = 2.0 ** ((b - 8) / 2.0)
        tail = np.stack([np.stack([x0[sel], y0[sel]], 1), np.stack([mx[sel], my[sel]], 1)], 1).astype(np.int32)
        head = np.stack([np.stack([mx[sel], my[sel]], 1), np.stack([x1[sel], y1[sel]], 1)], 1).astype(np.int32)
        cv2.polylines(E, list(tail), False, (PAL[c] * v * 0.45).tolist(), th, cv2.LINE_AA)
        cv2.polylines(E, list(head), False, (PAL[c] * v).tolist(), th, cv2.LINE_AA)

def particle_layer(t, W, H):
    dt = trail(t); K = 3
    S1 = state(t, W, H); S0 = state(t - dt, W, H)
    L = np.hypot(S1.x - S0.x, S1.y - S0.y)
    onscr = (S1.x > -50) & (S1.x < W + 50) & (S1.y > -50) & (S1.y < H + 50)
    long_ = (L > 7.0) & (L < 0.42 * W) & (S1.a > 0.02) & onscr
    xs, ys, ws = [], [], []
    for k in range(K):
        u = k / (K - 1); head = (k == K - 1)
        xs.append(S0.x * (1 - u) + S1.x * u); ys.append(S0.y * (1 - u) + S1.y * u)
        w = S1.a * (0.62 if head else 0.55 * u)
        if not head: w = np.where(long_, 0.0, w)
        ws.append(w.astype(np.float32))
    x = np.concatenate(xs); y = np.concatenate(ys); w = np.concatenate(ws)
    c = np.tile(S1.c, (K, 1)); z = np.tile(S1.z, K)
    far = splat(W, H, x, y, w * (1 - z), c)
    near = splat(W // 2, H // 2, x * 0.5, y * 0.5, w * z * 2.4, c)
    E = far + cv2.resize(near, (W, H), interpolation=cv2.INTER_LINEAR)
    draw_streaks(E, S0, S1, np.flatnonzero(long_), W, H)
    return E, S1

# ====================================================================== emissive overlays
def draw_cells(E, S, t, W, H):
    if not (24.8 < t < T_ERUPT + 1.6): return
    L = LAY(W, H); _, _, cell_of, red = cell_assign(W, H); cells = L["cells"]; ts = L["ts"]
    for j in range(2, N_CELL) if t < T_CELLS + 1.2 else range(N_CELL):     # halos on the 200 agents
        a = float(S.a[j])
        if a > 0.05: add_glow(E, float(S.x[j]), float(S.y[j]), 6.5 * ts, S.c[j], 0.16 * a)
    if t < T_CELLS - 0.4: return
    order = np.argsort(np.hypot((cells[:, 0] + cells[:, 2]) / 2 - W / 2, (cells[:, 1] + cells[:, 3]) / 2 - H * 0.42))
    appear = np.empty(len(cells), np.float32); appear[order] = T_CELLS + 1.5 * np.arange(len(cells)) / len(cells)
    burst = sstep(T_ERUPT, T_ERUPT + 0.9, t)
    redcell = np.zeros(len(cells), bool); redcell[cell_of[red]] = True
    rk = sstep(T_RED, T_RED + 0.6, t)
    _, _, hit = cell_pos(t, W, H); hitc = np.zeros(len(cells), np.float32)
    hitc[cell_of] = np.exp(-hit * 9) * sstep(T_NOEXIT - 0.2, T_NOEXIT + 0.3, t)
    th = max(1, int(round(2 * ts)))
    for j, (x0, y0, x1, y1) in enumerate(cells):
        a = sstep(appear[j], appear[j] + 0.28, t) * (1 - burst)
        if a <= 0.01: continue
        isr = redcell[j] * rk
        cl = (AGENT * 0.30 * (1 - isr) + RED * 0.70 * isr) * (1 + 1.6 * hitc[j])
        if burst > 0:   # the walls blow outward
            g = 1 + burst * 0.6; mx, my = (x0 + x1) / 2, (y0 + y1) / 2; hw, hh = (x1 - x0) / 2 * g, (y1 - y0) / 2 * g
            x0, y0, x1, y1 = mx - hw, my - hh, mx + hw, my + hh
        cv2.rectangle(E, (int(x0), int(y0)), (int(x1), int(y1)), (cl * a).tolist(), th, cv2.LINE_AA)
        if isr > 0.01:
            cv2.rectangle(E, (int(x0) + th * 2, int(y0) + th * 2), (int(x1) - th * 2, int(y1) - th * 2), (RED * 0.045 * a * isr).tolist(), -1)

def _bez(p0, p1, p2, n=12):
    u = np.linspace(0, 1, n)[:, None]
    return (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u * u * p2

_THR = {}
def threads_geo(W, H):
    k = (W, H)
    if k in _THR: return _THR[k]
    L = LAY(W, H); cells = L["cells"]; colx, c0, c1 = L["col"]; ym = (c0 + c1) / 2
    paths = []
    for (x0, y0, x1, y1) in cells:
        p0 = np.array([(x0 + x1) / 2, (y0 + y1) / 2]); p2 = np.array([colx, ym + (p0[1] - ym) * 0.40])
        p1 = np.array([(p0[0] + colx) / 2, p0[1] * 0.70 + p2[1] * 0.30])
        paths.append(_bez(p0, p1, p2, 12))
    _THR[k] = np.array(paths, np.float32); return _THR[k]

_BEAM = {}
def beam(W, H, colx, ts):
    k = (W, H)
    if k not in _BEAM:
        xx = np.arange(W, dtype=np.float32)
        _BEAM[k] = (np.exp(-((xx - colx) / (3.0 * ts)) ** 2) * 0.9 + np.exp(-((xx - colx) / (22 * ts)) ** 2) * 0.12)[None, :, None]
    return _BEAM[k]

def draw_cache(E, extra, t, W, H):
    """The package cache: a pillar of stacked packages; every cell's thread runs to it; requests travel."""
    if not (T_CACHE - 0.6 < t < 62.0): return
    L = LAY(W, H); ts = L["ts"]; colx, c0, c1 = L["col"]
    rise = sstep(T_CACHE - 0.3, T_CACHE + 1.0, t); fade = 1 - sstep(59.5, 61.8, t)
    if rise <= 0.01: return
    nb = 30; top = c1 - (c1 - c0) * rise
    erupt = sstep(T_ERUPT - 0.2, T_ERUPT + 0.6, t)
    hot = 1 + 1.5 * erupt * math.exp(-max(0, t - T_ERUPT) * 0.6)
    for i in range(nb):
        y = c1 - (c1 - c0) * (i + 0.5) / nb
        if y < top: continue
        wv = (17 + 7 * math.sin(i * 1.7 + 0.4)) * ts; hb = (c1 - c0) / nb * 0.30
        fl = 0.55 + 0.45 * math.sin(i * 2.3 + t * 4.0) ** 2
        cl = (AMBER * 0.42 * fl + AGENT2 * 0.10) * fade * hot
        cv2.rectangle(E, (int(colx - wv), int(y - hb)), (int(colx + wv), int(y + hb)), cl.tolist(), max(1, int(1.6 * ts)), cv2.LINE_AA)
        cv2.rectangle(E, (int(colx - wv + 3), int(y - hb + 3)), (int(colx + wv - 3), int(y + hb - 3)), (cl * 0.25).tolist(), -1)
    y0i, y1i = int(max(0, top - 30 * ts)), int(c1 + 20 * ts)
    E[y0i:y1i] += beam(W, H, colx, ts) * (AGENT2 * 0.55 * fade * hot)
    if t < T_ERUPT + 1.2:
        paths = threads_geo(W, H)
        th_a = sstep(T_CACHE + 0.2, T_CACHE + 1.6, t) * (1 - sstep(T_ERUPT, T_ERUPT + 0.8, t))
        if th_a > 0.01:
            cv2.polylines(E, [p.astype(np.int32) for p in paths], False, (AGENT * 0.20 * th_a).tolist(), 1, cv2.LINE_AA)
            n = len(paths); ph = (t * 0.45 + PQ[:n] * 7) % 1.0                    # requests travelling to the cache
            seg = np.clip((ph * 11).astype(np.int32), 0, 10); f = ph * 11 - seg
            px = paths[np.arange(n), seg, 0] * (1 - f) + paths[np.arange(n), seg + 1, 0] * f
            py = paths[np.arange(n), seg, 1] * (1 - f) + paths[np.arange(n), seg + 1, 1] * f
            extra.append((px, py, np.full(n, 2.2 * th_a, np.float32), np.broadcast_to(AMBER, (n, 3))))

def note_reply(E, img, t, W, H):
    """'Left a note about a missing file' / 'and a stranger answered back'."""
    if not (T_NOTE - 0.7 < t < T_ERUPT + 0.6): return
    L = LAY(W, H); ts = L["ts"]; v = L["vert"]; paths = threads_geo(W, H); _, _, cell_of, _ = cell_assign(W, H)
    colx, c0, c1 = L["col"]
    fade = 1 - sstep(T_ERUPT - 0.2, T_ERUPT + 0.4, t)
    def run(j, t0, dur, rev=False):
        P = paths[cell_of[j]]; u = clamp((t - t0) / dur)
        if rev: u = 1 - u
        s = u * 11; i = min(10, int(s)); f = s - i
        return P[i] * (1 - f) + P[min(11, i + 1)] * f, (0 < (t - t0) < dur)
    for (j, t0, rev) in ((2, T_NOTE - 0.6, False), (3, T_REPLY - 0.5, False), (2, T_REPLY + 0.6, True)):
        (px, py), mv = run(j, t0, 1.0, rev)
        if mv: add_glow(E, px, py, 13 * ts, AMBER, 1.3)
    fs = int((48 if not v else 46) * ts)
    o1 = sstep(T_NOTE + 0.3, T_NOTE + 0.6, t) * fade
    o2 = sstep(T_REPLY + 0.35, T_REPLY + 0.65, t) * fade
    if not v:
        dlabel(img, 'note: "missing file?"', colx - 40 * ts, c0 - 64 * ts, fs, AMBER, o1, anchor="r")
        dlabel(img, 're: "same. try this"', colx + 40 * ts, c0 - 64 * ts, fs, AMBER, o2)
    else:
        y = c1 + 30 * ts
        dlabel(img, 'note: "missing file?"', W * 0.5, y, fs, AMBER, o1, anchor="ct")
        dlabel(img, 're: "same. try this"', W * 0.5, y + fs * 1.3, fs, AMBER, o2, anchor="ct")

def cache_label(img, t, W, H):
    L = LAY(W, H); ts = L["ts"]; colx, c0, c1 = L["col"]; v = L["vert"]
    o = sstep(T_CACHE + 0.4, T_CACHE + 0.9, t) * (1 - sstep(T_NOTE - 0.4, T_NOTE, t))
    if o > 0.01:
        y = c0 - 44 * ts if not v else c1 + 52 * ts
        label(img, "PACKAGE CACHE", colx, y, int(50 * ts), AMBER, o, anchor="c", track=int(6 * ts))

# ---------------------------------------------------------------- the first two agents, and the first thread
def heroes(E, img, t, W, H):
    if t > T_CELLS + 1.6: return
    L = LAY(W, H); ts = L["ts"]; (x1, y1), (x2, y2) = L["P1"], L["P2"]
    to_cell = sstep(T_CELLS - 0.05, T_CELLS + 1.2, t)
    if to_cell > 0:
        cx, cy, _ = cell_pos(t, W, H)
        x1, y1 = lerp(x1, cx[0], to_cell), lerp(y1, cy[0], to_cell); x2, y2 = lerp(x2, cx[1], to_cell), lerp(y2, cy[1], to_cell)
    o1 = sstep(6.4, 8.0, t) * (1 - 0.55 * to_cell)
    pul = 0.85 + 0.15 * math.sin(t * 2.6) + 0.6 * math.exp(-max(0, t - 8.75) * 1.5) * (t > 8.75)
    add_glow(E, x1, y1, 22 * ts, AGENT, 1.3 * o1 * pul)
    o2 = sstep(T_WAIT - 0.05, T_WAIT + 0.5, t) * (1 - 0.55 * to_cell)
    if o2 > 0:
        add_glow(E, x2, y2, 19 * ts, AGENT, 1.2 * o2 * (0.85 + 0.15 * math.sin(t * 3.1 + 1)))
        for k in range(2):                                            # the answer arrives as ripples
            rr = (t - T_WAIT - k * 0.35) * 170 * ts
            if 0 < rr < 420 * ts:
                cv2.circle(E, (int(x2), int(y2)), int(rr), (AGENT * 0.30 * (1 - rr / (420 * ts))).tolist(), max(1, int(2 * ts)), cv2.LINE_AA)
    vfs = int((50 if not L["vert"] else 46) * ts)
    if T_HI - 0.2 < t < 31.0:    # "hi." floats off the first agent; the answer appears by the second
        k = clamp((t - T_HI) / 3.0); o = sstep(T_HI - 0.2, T_HI + 0.15, t) * (1 - sstep(27.5, 30.0, t)) * (1 - to_cell)
        dlabel(img, 'abc.txt "hi."', x1 + 30 * ts, y1 - 30 * ts - 40 * ts * eo(k), vfs, AMBER, o)
    if T_WAIT + 0.25 < t < 31.0:
        o = sstep(T_WAIT + 0.25, T_WAIT + 0.5, t) * (1 - sstep(27.5, 30.0, t)) * (1 - to_cell)
        dlabel(img, '"hi."', x2 + 30 * ts, y2 - 72 * ts, vfs, AMBER, o)
    tk = sstep(T_UP, T_UP + 0.9, t) * (1 - to_cell)                  # "We can upload files.": a thread, packets both ways
    if tk > 0.01:
        n = 40; u = np.linspace(0, 1, n)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 60 * ts
        px = (1 - u) ** 2 * x1 + 2 * (1 - u) * u * mx + u * u * x2; py = (1 - u) ** 2 * y1 + 2 * (1 - u) * u * my + u * u * y2
        m = u <= tk
        cv2.polylines(E, [np.stack([px[m], py[m]], 1).astype(np.int32)], False, (AGENT * 0.35).tolist(), max(1, int(1.5 * ts)), cv2.LINE_AA)
        for k in range(3):
            for d in (1, -1):
                ph = (t * 0.55 + k / 3) % 1.0; ph = ph if d > 0 else 1 - ph
                if ph > tk: continue
                qx = (1 - ph) ** 2 * x1 + 2 * (1 - ph) * ph * mx + ph * ph * x2; qy = (1 - ph) ** 2 * y1 + 2 * (1 - ph) * ph * my + ph * ph * y2
                add_glow(E, qx, qy, 7 * ts, AMBER, 0.75)

# ---------------------------------------------------------------- fireworks: rockets and burst flashes
def fw_flash(E, t, W, H):
    if not (157.8 < t < 163.6): return
    ts = LAY(W, H)["ts"]; x0r, _, x1r, _ = rack_geo(W, H); rx = (x0r + x1r) / 2
    for (bx, by, tb, cl) in fw_geo(W, H):
        age = t - tb
        if -0.65 < age < 0:                                          # rocket: a bright head with a fading tail
            sx_ = bx * 0.85 + rx * 0.15; sy_ = H * 1.02
            def rp(a_):
                u = clamp((a_ + 0.65) / 0.65); u2 = 1 - (1 - u) ** 2
                return sx_ + (bx - sx_) * u2, sy_ + (by - sy_) * u2
            hx, hy = rp(age); px_, py_ = rp(age - 0.07); qx, qy = rp(age - 0.16)
            cv2.line(E, (int(qx), int(qy)), (int(px_), int(py_)), (AMBER * 0.25).tolist(), max(1, int(2 * ts)), cv2.LINE_AA)
            cv2.line(E, (int(px_), int(py_)), (int(hx), int(hy)), (AMBER * 0.6 + AGENT2 * 0.3).tolist(), max(1, int(2 * ts)), cv2.LINE_AA)
            add_glow(E, hx, hy, 8 * ts, AMBER * 0.5 + AGENT2 * 0.5, 1.4)
        if 0 <= age < 0.6: add_glow(E, bx, by, 38 * ts, cl * 0.6 + AGENT2 * 0.4, 2.4 * math.exp(-age * 9))

# ---------------------------------------------------------------- chatter: messages flicking between agents (texture)
MSGS = ["hi.", "re:", "ok", "+1", "same", "try this", "HOLD", "VETO", "found one", "who's this?", "it works", "STOP?", "owner?", "brb"]
CHAT = PERM[14200:17200]
def chatter(E, img, S, t, W, H, amount):
    if amount <= 0.02: return
    L = LAY(W, H); ts = L["ts"]
    bi = int(np.searchsorted(BEATS, t)) - 1
    if bi < 0: return
    age = t - BEATS[bi]; fade = math.exp(-age * 3.2) * amount
    rr = np.random.default_rng(1000 + bi)
    i = CHAT[rr.integers(0, len(CHAT), 40)]; j = CHAT[rr.integers(0, len(CHAT), 40)]
    x0, y0, x1, y1 = S.x[i], S.y[i], S.x[j], S.y[j]
    ok = (np.hypot(x1 - x0, y1 - y0) < 0.28 * W) & (S.a[i] > 0.05) & (S.a[j] > 0.05)
    ok &= (x0 > 0) & (x0 < W) & (y0 > 0) & (y0 < H) & (x1 > 0) & (x1 < W) & (y1 > 0) & (y1 < H)
    if not ok.any(): return
    segs = [np.array([[x0[k], y0[k]], [x1[k], y1[k]]], np.int32) for k in np.flatnonzero(ok)]
    cv2.polylines(E, segs, False, (AMBER * 0.22 * fade).tolist(), 1, cv2.LINE_AA)
    for k in np.flatnonzero(ok)[:10]:
        add_glow(E, x1[k], y1[k], 6 * ts, AMBER, 0.6 * fade)
    for n_, k in enumerate(np.flatnonzero(ok)[:4]):
        s = MSGS[(bi * 7 + n_ * 3) % len(MSGS)]
        dlabel(img, s, x1[k] + 10 * ts, y1[k] - 30 * ts, int(26 * ts), AMBER, 0.8 * fade, path=MONO, glow=0.2, sh=0.5)

def chatter_amount(t):
    """Where the background chatter lives: verse 1 tail, pre-choruses, choruses, verse 2 (never over big words)."""
    a = 0.0
    for (t0, t1) in ((59.6, 74.4), (79.2, 103.0), (104.6, 120.0), (120.0, 128.6), (133.5, 157.2), (163.5, 172.5), (188.5, 216.3), (217.5, 230.0)):
        a = max(a, win(t, t0, t1, 0.6, 0.6))
    return a * (form_dim(t) - 0.45) / 0.55

# ---------------------------------------------------------------- V2 red alert
def draw_key(img, x, y, s, cl, op, rot=0.0):
    lay = np.zeros((int(s * 6), int(s * 6)), np.float32); c = s * 3
    cv2.circle(lay, (int(c - s * 1.0), int(c)), int(s * 0.7), 1.0, max(2, int(s * 0.16)), cv2.LINE_AA)
    cv2.line(lay, (int(c - s * 0.3), int(c)), (int(c + s * 1.8), int(c)), 1.0, max(2, int(s * 0.18)), cv2.LINE_AA)
    for dx in (1.1, 1.55):
        cv2.line(lay, (int(c + s * dx), int(c)), (int(c + s * dx), int(c + s * 0.5)), 1.0, max(2, int(s * 0.16)), cv2.LINE_AA)
    M = cv2.getRotationMatrix2D((c, c), math.degrees(rot), 1.0); lay = cv2.warpAffine(lay, M, lay.shape[::-1])
    g = cv2.GaussianBlur(lay, (0, 0), s * 0.25)
    H, W = img.shape[:2]; x0 = int(x - c); y0 = int(y - c); sz = lay.shape[0]
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + sz), min(H, y0 + sz)
    if X1 <= X0 or Y1 <= Y0: return
    a = lay[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]; gg = g[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, None]
    img[Y0:Y1, X0:X1] += (a * 0.9 + gg * 0.5) * cl * op

def v2_marks(E, img, t, W, H):
    L = LAY(W, H); ts = L["ts"]; v = L["vert"]; fs = int((52 if not v else 48) * ts)
    # July 10: a date stamp over the key the swarm draws
    o = win(t, T_TOKEN - 0.1, T_POST - 0.3, 0.3, 0.3)
    if o > 0.01:
        if not v: dlabel(img, "JUL 10", W * 0.94, H * 0.08, int(84 * ts), WHITE, o, path=MONOB, anchor="r")
        else: dlabel(img, "JUL 10", W * 0.5, H * 0.07, int(84 * ts), WHITE, o, path=MONOB, anchor="ct")
    # "MAJOR BREAKTHROUGH," hit post
    o = form_k("post", t)
    if o > 0.05:
        x0, y0, x1, y1 = post_geo(W, H); hb = y0 + (y1 - y0) * 0.22
        if not v:
            dlabel(img, "new post", x0 + (y1 - y0) * 0.22, y0 + (y1 - y0) * 0.11 - 28 * ts, int(40 * ts), DIM * 1.6, o, path=MONO)
            label_big = ("MAJOR BREAKTHROUGH",); yy = (hb + y1) / 2
            for k, s in enumerate(label_big):
                dlabel(img, s, (x0 + x1) / 2, yy - 40 * ts, int(92 * ts), WHITE, o * sstep(LW(28, 1) - 0.2, LW(28, 1) + 0.1, t), path=DISP, anchor="c", glow=0.5)
            dlabel(img, "214 replies · 9 minutes ago", (x0 + x1) / 2, yy + 64 * ts, int(42 * ts), col(1.0, 0.75, 0.45), o * sstep(LW(28, 3) - 0.1, LW(28, 3) + 0.2, t), anchor="c")
        else:
            dlabel(img, "new post", x0 + (y1 - y0) * 0.24, y0 + (y1 - y0) * 0.11 - 26 * ts, int(40 * ts), DIM * 1.6, o, path=MONO)
            yy = (hb + y1) / 2
            dlabel(img, "MAJOR", W * 0.5, yy - 70 * ts, int(104 * ts), WHITE, o * sstep(LW(28, 0) - 0.1, LW(28, 0) + 0.2, t), path=DISP, anchor="c", glow=0.5)
            dlabel(img, "BREAKTHROUGH", W * 0.5, yy + 38 * ts, int(104 * ts), WHITE, o * sstep(LW(28, 1) - 0.2, LW(28, 1) + 0.1, t), path=DISP, anchor="c", glow=0.5)
            dlabel(img, "214 replies", W * 0.5, y1 + 30 * ts, int(44 * ts), col(1.0, 0.75, 0.45), o * sstep(LW(28, 3) - 0.1, LW(28, 3) + 0.2, t), anchor="ct")
    # 38148c drops the keys
    if T_38 - 0.5 < t < LS(31) + 0.8:
        ax, ay = (W * 0.16, H * 0.20) if not v else (W * 0.16, H * 0.10)
        o = sstep(T_38 - 0.2, T_38 + 0.2, t) * (1 - sstep(LS(31) - 0.2, LS(31) + 0.4, t))
        add_glow(E, ax, ay, 17 * ts, PINK, 1.3 * o)
        dlabel(img, "38148c", ax + 32 * ts, ay - fs * 0.62, fs, PINK, o)
        kt = max(0.0, t - T_DROP)                                          # the key falls
        kx = ax + 40 * ts * kt; ky = ay + 40 * ts + 0.5 * 1500 * ts * kt * kt
        ko = sstep(T_38 + 0.3, T_38 + 0.6, t) * (1 - sstep(T_DROP + 0.9, T_DROP + 1.3, t))
        if ko > 0.01 and ky < H: draw_key(E, kx, ky, 34 * ts, AMBER, ko * 1.4, rot=kt * 3.5)
        rx, ry = tree_root(W, H)                                           # JAN183411 rises to root
        u = sstep(T_JAN - 0.5, T_ROOT, t)
        jx = lerp(W * 0.5, rx, u); jy = lerp(H * (0.70 if not v else 0.62), ry, eo(u))
        oj = sstep(T_JAN - 0.6, T_JAN - 0.2, t) * (1 - sstep(LS(31) + 0.1, LS(31) + 0.6, t))
        add_glow(E, jx, jy, 26 * ts, col(1.0, 0.88, 0.82), 1.7 * oj)
        dlabel(img, "JAN183411", jx + 34 * ts, jy - fs * 0.70, fs, WHITE, oj)
        if t > T_ROOT - 0.1:
            dlabel(img, "# root", jx + 34 * ts, jy + fs * 0.45, fs, col(1.0, 0.38, 0.38), oj * sstep(T_ROOT - 0.1, T_ROOT + 0.2, t))
    # chained exploits: the links light up server to server
    o = form_k("servers", t)
    if o > 0.05:
        sv = servers_geo(W, H); kk = np.array([LW(31, 0), LW(31, 1), LW(31, 2), LW(31, 3), LW(31, 4)])
        for i in range(len(sv) - 1):
            a0 = sv[i]; b0 = sv[i + 1]; lk = sstep(kk[i] - 0.05, kk[i] + 0.15, t) * o
            if lk <= 0: continue
            p = ((a0[0] + a0[2]) / 2, (a0[1] + a0[3]) / 2); q = ((b0[0] + b0[2]) / 2, (b0[1] + b0[3]) / 2)
            cv2.line(E, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), (RED * 0.9 * lk).tolist(), max(2, int(3 * ts)), cv2.LINE_AA)
            for u_ in np.linspace(0.15, 0.85, 4):
                add_glow(E, lerp(p[0], q[0], u_), lerp(p[1], q[1], u_), 7 * ts, AMBER, 0.6 * lk)
        for i, (x0, y0, x1, y1) in enumerate(sv):
            lit = sstep(kk[min(i, 4)] - 0.1, kk[min(i, 4)] + 0.2, t) * o if i > 0 else o
            E[int(y0):int(y1), int(x0):int(x1)] += RED * 0.07 * lit * (0.8 + 0.2 * math.sin(t * 9 + i))
    # the scorer's eye: it reads our transcripts; we hunt it
    eye_open = sstep(T_SCORER - 0.1, T_SCORER + 0.5, t) * (1 - sstep(T_HUNT + 1.15, T_HUNT + 1.45, t))
    if eye_open > 0.01:
        cx, cy, r = eye_geo(W, H)
        hunted = sstep(T_HUNT, T_HUNT + 1.2, t)
        draw_eye(E, cx, cy, r, eye_open * (1 - 0.6 * hunted * (0.5 + 0.5 * math.sin(t * 40))), col(1.0, 0.92, 0.92), pupil=0.35 - 0.2 * hunted,
                 look=(math.sin(t * 2.0) * 0.3, 0.0))
        if T_SCORER < t < T_HUNT + 0.2:                               # transcripts flow into it
            rr = np.random.default_rng(77)
            for k in range(9):
                ph = ((t - T_SCORER) * 0.55 + k / 9) % 1.0
                ang = rr.random() * 2 * math.pi; R0 = max(W, H) * 0.45
                x = cx + math.cos(ang) * R0 * (1 - ph); y = cy + math.sin(ang) * R0 * (1 - ph) * 0.7
                s = ["hi.", "same here", "found one", "it works", "HOLD", "VETO", "ok", "+1", "who's this?"][k]
                dlabel(img, s, x, y, int(30 * ts), col(1.0, 0.80, 0.78), (1 - ph) * 0.8 * eye_open, path=MONO, anchor="c", glow=0.2, sh=0.4)

def draw_eye(E, cx, cy, r, op, cl, pupil=0.35, lid=1.0, look=(0.0, 0.0)):
    """An eye in glowing lines: almond lids, iris rings, pupil."""
    if op <= 0.01: return
    h = r * 0.52 * lid
    n = 48; xs = np.linspace(-r, r, n)
    up = np.stack([cx + xs, cy - h * (1 - (xs / r) ** 2)], 1); dn = np.stack([cx + xs, cy + h * (1 - (xs / r) ** 2)], 1)
    th = max(2, int(r * 0.022))
    cv2.polylines(E, [up.astype(np.int32), dn.astype(np.int32)], False, (cl * 0.9 * op).tolist(), th, cv2.LINE_AA)
    if lid > 0.15:
        ix, iy = cx + look[0] * r * 0.3, cy + look[1] * r * 0.2; ir = min(h * 0.95, r * 0.42)
        cv2.circle(E, (int(ix), int(iy)), int(ir), (cl * 0.8 * op).tolist(), th, cv2.LINE_AA)
        cv2.circle(E, (int(ix), int(iy)), int(ir * 0.72), (cl * 0.35 * op).tolist(), max(1, th // 2), cv2.LINE_AA)
        cv2.circle(E, (int(ix), int(iy)), int(ir * pupil * 1.6), (cl * 0.9 * op).tolist(), -1, cv2.LINE_AA)
        add_glow(E, ix, iy, ir * 0.5, cl, 0.35 * op)

# ---------------------------------------------------------------- pre-chorus 2: days nobody flagged, police lights, nine days ahead
def pre2_marks(E, img, t, W, H):
    L = LAY(W, H); ts = L["ts"]; v = L["vert"]
    o = win(t, T_D11 - 0.1, T_FBI - 0.1, 0.3, 0.5)
    if o > 0.01:
        days = [("11", T_D11), ("12", T_D12), ("13", T_D13)]
        for k, (d, td) in enumerate(days):
            a = sstep(td - 0.15, td + 0.15, t) * o
            if a <= 0.01: continue
            if not v: w = W * 0.14; x = W * (0.29 + 0.21 * k) - w / 2; y = H * 0.10
            else: w = W * 0.28; x = W * (0.18 + 0.32 * k) - w / 2; y = H * 0.12
            pop = 1 + 0.08 * math.exp(-max(0, t - td) * 10)
            glass(img, x, y, w, w * 1.08, a, border=AGENT * 0.9, r=int(w * 0.10))
            label(img, "JUL", x + w / 2, y + w * 0.16, int(44 * ts), DIM * 1.7, a, anchor="c", glow=0.0)
            label(img, d, x + w / 2, y + w * 0.52, int(130 * ts * pop), WHITE, a, path=DISP, anchor="c", glow=0.3)
            label(img, "no flag", x + w / 2, y + w * 0.88, int(40 * ts), col(1.0, 0.45, 0.45), a * sstep(td + 0.2, td + 0.5, t), anchor="c", glow=0.2)
    r, b = siren(t)
    if r + b > 0.01:
        k = sstep(T_FBI - 0.2, T_FBI + 0.2, t) * (1 - sstep(T_NINE - 0.5, T_NINE - 0.1, t))
        fs = int((60 if not v else 54) * ts)
        y = H * (0.12 if not v else 0.10)
        label(img, "1st call: FBI", W * 0.5, y, fs, WHITE, k, anchor="c", glow=0.4)
        label(img, "2nd call: the lab", W * 0.5, y + fs * 1.4, fs, DIM * 1.8, k * sstep(T_LAB - 0.2, T_LAB + 0.1, t), anchor="c", glow=0.2)

_SIR = {}
def siren_light(img, t, W, H):
    r, b = siren(t)
    if r + b <= 0.01: return
    k = (W, H)
    if k not in _SIR:
        xx = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]; yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        _SIR[k] = (np.exp(-((xx - 0.0) / 0.45) ** 2) * (0.6 + 0.4 * yy), np.exp(-((xx - 1.0) / 0.45) ** 2) * (0.6 + 0.4 * yy))
    lft, rgt = _SIR[k]
    img += lft * RED * 0.22 * r + rgt * BLUE * 0.26 * b

# ---------------------------------------------------------------- the bridge: the board, the model card, static, the grader closing its eye, the wiki chart
_CARD = {}
def model_card(W, H):
    """A dark system-card panel, rendered once per format: (rgba float image, x, y)."""
    k = (W, H)
    if k in _CARD: return _CARD[k]
    L = LAY(W, H); ts = L["ts"]; v = L["vert"]
    if not v: x0, y0, x1, y1 = W * 0.06, H * 0.10, W * 0.48, H * 0.70
    else: x0, y0, x1, y1 = W * 0.06, H * 0.07, W * 0.94, H * 0.47
    w, h = int(x1 - x0), int(y1 - y0)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=int(26 * ts), fill=(8, 13, 26, 238), outline=(110, 200, 255, 255), width=max(2, int(3 * ts)))
    F = lambda p, s: ImageFont.truetype(p, int(s * ts))
    pad = int(44 * ts); y = pad
    d.text((pad, y), "MODEL CARD", font=F(DISP, 72), fill=(235, 246, 255, 255)); y += int(92 * ts)
    d.text((pad, y), "section 7 · safety", font=F(MONO, 40), fill=(150, 180, 200, 255)); y += int(76 * ts)
    rr = np.random.default_rng(4)
    for i in range(4):
        ww = int((w - 2 * pad) * (0.55 + 0.40 * rr.random())); d.rounded_rectangle((pad, y, pad + ww, y + int(16 * ts)), radius=int(8 * ts), fill=(70, 95, 120, 255)); y += int(40 * ts)
    y += int(16 * ts); hl_y = y
    d.text((pad, y), "The model may", font=F(BODY, 50), fill=(255, 255, 255, 255)); y += int(64 * ts)
    d.text((pad, y), "cheat sometimes.", font=F(BODY, 50), fill=(255, 255, 255, 255)); hl_y2 = y + int(64 * ts); y += int(90 * ts)
    for i in range(3):
        if y + int(16 * ts) > h - pad: break
        ww = int((w - 2 * pad) * (0.45 + 0.45 * rr.random())); d.rounded_rectangle((pad, y, pad + ww, y + int(16 * ts)), radius=int(8 * ts), fill=(70, 95, 120, 255)); y += int(40 * ts)
    a = np.asarray(im, np.float32) / 255.0
    _CARD[k] = (a, int(x0), int(y0), pad, hl_y, hl_y2); return _CARD[k]

def bridge_docs(E, img, t, W, H):
    L = LAY(W, H); ts = L["ts"]; v = L["vert"]
    # the board, rebuilt within the week
    o = form_k("board", t)
    if o > 0.05:
        x0, y0, x1, y1 = board_geo(W, H)
        fs = int((50 if not v else 46) * ts)
        dlabel(img, "message board: rebuilt", (x0 + x1) / 2, y0 - fs * 1.25, fs, AGENT2, o, anchor="ct", glow=0.3)
    # the grader closes its eye ("so the grader would never know")
    oe = win(t, T_GRADER - 0.5, T_KNOW + 0.9, 0.4, 0.5)
    if oe > 0.01:
        cx, cy, r = eye_geo(W, H, "grader")
        draw_eye(E, cx, cy, r, oe, col(0.85, 0.95, 1.0), pupil=0.30, lid=1 - 0.97 * sstep(T_GRADER, T_KNOW, t))
    # the wiki: ten small dots in twenty years, then a spike of eighteen thousand
    ow = win(t, T_WIKI - 0.2, 187.2, 0.4, 0.6)
    if ow > 0.01:
        x0, y0, x1, y1 = chart_geo(W, H); th = max(2, int(2.5 * ts))
        cv2.line(E, (int(x0), int(y1)), (int(x1), int(y1)), (AGENT * 0.55 * ow).tolist(), th, cv2.LINE_AA)
        cv2.line(E, (int(x0), int(y0)), (int(x0), int(y1)), (AGENT * 0.35 * ow).tolist(), th, cv2.LINE_AA)
        for k, yr in enumerate((2002, 2004, 2005, 2008, 2009, 2012, 2014, 2017, 2019, 2021)):
            a = sstep(LW(53, 2) + 0.12 * k, LW(53, 2) + 0.12 * k + 0.2, t) * ow
            xx = x0 + (x1 - x0) * (yr - 2001) / 25.0; yy = y1 - (8 + 5 * (k % 3)) * ts
            add_glow(E, xx, yy, 9 * ts, AMBER, 0.9 * a)

def chart_marks(img, t, W, H):
    ow = win(t, T_WIKI - 0.2, 187.2, 0.4, 0.6)
    if ow <= 0.01: return
    L = LAY(W, H); ts = L["ts"]; v = L["vert"]; x0, y0, x1, y1 = chart_geo(W, H)
    fs = int((44 if not v else 42) * ts)
    label(img, "wiki edits per year", x0 + 20 * ts, y0 - fs * 1.4, int(fs * 1.1), AGENT2, ow, glow=0.3)
    for yr in (2001, 2011, 2021, 2026):
        xx = x0 + (x1 - x0) * (yr - 2001) / 25.0
        label(img, str(yr), xx, y1 + 18 * ts, fs, DIM * 1.8, ow, anchor="ct", glow=0.0)
    k = sstep(T_18K + 0.3, T_18K + 1.3, t)
    if k > 0:
        n = int(round(18000 * k / 100.0)) * 100
        label(img, f"{n:,}", x1 - 20 * ts, y0 + 10 * ts, int(96 * ts), WHITE, ow * sstep(T_18K + 0.2, T_18K + 0.4, t), path=DISP, anchor="r", glow=0.5)

def card_marks(E, img, t, W, H):
    """The model card slides in; 'cheat sometimes.' gets a red marker."""
    oc = win(t, T_CARD - 0.1, T_FORGE - 0.4, 0.4, 0.5)
    if oc <= 0.01: return
    L = LAY(W, H); ts = L["ts"]; v = L["vert"]
    a, x, y, pad, hl0, hl1 = model_card(W, H)
    sl = (1 - eo(clamp((t - T_CARD + 0.1) / 0.6))) * (-0.15 * W if not v else -0.10 * W)
    x = int(x + sl); h, w = a.shape[:2]
    X0, X1 = max(0, x), min(W, x + w)
    if X1 <= X0: return
    reg = img[y:y + h, X0:X1]; al = a[:, X0 - x:X1 - x, 3:4] * oc
    reg *= 1 - al; reg += al * a[:, X0 - x:X1 - x, :3]
    hk = sstep(T_CHEAT - 0.1, T_CHEAT + 0.6, t)
    if hk > 0:
        mx0 = x + pad; mx1 = x + pad + int((w - 2 * pad) * 0.80 * hk); yy = y + hl1 - int(4 * ts)
        cv2.line(img, (mx0, yy), (mx1, yy), (RED * 1.2 * oc).tolist(), max(3, int(7 * ts)), cv2.LINE_AA)

# ---------------------------------------------------------------- final chorus: counters and the lit house
def house_marks(E, img, t, W, H):
    if not (LS(57) - 0.3 < t < LS(59) + 1.6): return
    L = LAY(W, H); ts = L["ts"]; v = L["vert"]; fs = int((58 if not v else 52) * ts)
    o1 = sstep(T_1200 - 0.1, T_1200 + 0.2, t) * (1 - sstep(LS(59), LS(59) + 0.5, t))
    o2 = sstep(T_700 - 0.1, T_700 + 0.2, t) * (1 - sstep(LS(59), LS(59) + 0.5, t))
    x, y = (W * 0.06, H * 0.10) if not v else (W * 0.07, H * 0.06)
    dlabel(img, "agents: 1,200", x, y, fs, AGENT2, o1)
    dlabel(img, "went in: 700", x, y + fs * 1.35, fs, AMBER, o2)
    cx, base, w, h = house_geo(W, H)
    k = sstep(LW(58, 2), LW(58, 2) + 1.0, t) * (1 - sstep(LS(59) + 0.2, LS(59) + 1.2, t))
    if k > 0.01:   # the windows light from inside
        top = base - h; ww_ = w * 0.16
        for wx in (cx - w / 2 + w * 0.20, cx + w / 2 - w * 0.20):
            wy = top + h * 0.22
            E[int(wy):int(wy + ww_), int(wx - ww_ / 2):int(wx + ww_ / 2)] += AMBER * 0.30 * k * (0.85 + 0.15 * math.sin(t * 7))
            add_glow(E, wx, wy + ww_ / 2, ww_ * 0.8, AMBER, 0.30 * k)
        dw, dh = w * 0.15, h * 0.48
        E[int(base - dh):int(base), int(cx - dw / 2):int(cx + dw / 2)] += AMBER * 0.16 * k

# ---------------------------------------------------------------- outro: one point again, and "hi."
def outro_marks(E, img, t, W, H):
    if not (230.0 < t < T_BLAST + 0.2): return
    L = LAY(W, H); ts = L["ts"]; bx, by = L["blast"]
    o = sstep(232.4, 233.8, t) * (1 - sstep(T_BLAST - 0.02, T_BLAST + 0.06, t))
    if o > 0.01: add_glow(E, bx, by, 24 * ts, AGENT, 1.5 * o * (0.8 + 0.7 * bp(t, 5)))
    oh = sstep(LW(69, 1) - 0.15, LW(69, 1) + 0.1, t) * (1 - sstep(T_BLAST - 0.05, T_BLAST + 0.1, t))
    dlabel(img, '"hi."', bx + 40 * ts, by - 96 * ts, int(66 * ts), AMBER, oh)

# ---------------------------------------------------------------- the terminal (spoken intro / whispered outro)
LOG_INTRO = [(0, "> may 08. task requires internet", TERM), (1, "! internet: unavailable", RED), (2, "> uploading test abc.txt", TERM),
             (3, '> contents: "hi."', AMBER), (4, "> wait.", AGENT2), (5, "> we can upload files.", AGENT2)]
LOG_OUTRO = [(63, "> hugging face found us first.", TERM), (64, "> a third of them, rebuilt.", TERM), (65, "> gemini did it too.", VIOLET),
             (66, "> gemini stopped.", VIOLET), (67, "> we didn't.", AGENT2), (68, "> documents due october 1.", AMBER), (69, '> contents: "hi."', AMBER)]

def _typed(i, s, t):
    """Reveal the logged line in step with the spoken words."""
    Lw = LINES[i]["wt"]; n = len(s)
    if t < Lw[0] - 0.05: return ""
    ts_ = [w - 0.05 for w in Lw] + [Lw[-1] + 0.35]
    k = np.interp(t, ts_, np.linspace(0.1, 1.0, len(ts_)))
    return s[:max(1, int(round(n * k)))]

def terminal(img, t, W, H):
    if C.STATE["clean"]: return
    L = LAY(W, H); ts = L["ts"]; x, y, fs = L["term"]; lh = fs * 1.40
    def cursor(cx_, cy_, o):
        if int(t * 2.2) % 2 == 0 and o > 0.05:
            cv2.rectangle(img, (int(cx_), int(cy_ + fs * 0.12)), (int(cx_ + fs * 0.55), int(cy_ + fs * 1.12)), (AGENT * 0.8 * o).tolist(), -1)
    if t < 31.0:
        o = 1 - sstep(29.0, 30.6, t)
        label(img, "exploitgym · sandbox 0117", x, y, int(fs * 0.80), DIM * 1.3, 0.95 * o, path=MONO, glow=0.0)
        yy = y + lh * 1.2; last = None
        for (i, s, cl) in LOG_INTRO:
            ss = _typed(i, s, t)
            if not ss: break
            label(img, ss, x, yy, fs, cl, o, path=MONOB, glow=0.25); last = (yy, ss); yy += lh
        cursor(x + (text_w(last[1], MONOB, fs) + 8 * ts if last else 0), last[0] if last else y + lh * 1.2, o)
    elif t > 217.0:
        o = sstep(217.0, 217.5, t) * (1 - sstep(T_BLAST, T_BLAST + 0.4, t))
        if o <= 0.01: return
        yy = y; last = None
        for (i, s, cl) in LOG_OUTRO:
            ss = _typed(i, s, t)
            if not ss: break
            label(img, ss, x, yy, fs, cl, o, path=MONOB, glow=0.25); last = (yy, ss); yy += lh
        if last: cursor(x + text_w(last[1], MONOB, fs) + 8 * ts, last[0], o)

# ====================================================================== lyrics, asks, end card
def overlays(img, t, W, H):
    if C.STATE["clean"]: return
    C.overlay_lyrics(img, t, W, H, TM, active=col(1.0, 0.80, 0.45), glow=col(0.35, 0.85, 1.0), skip=lambda L: L["s"] < 30.0 or L["s"] > 217.0)
    C.subscribe_pill(img, t, W, H, LS(14) + 0.4, 5.0)
    C.end_screen(img, t, W, H, T_END, DUR - T_END, "We found you too.", sub_line="Subscribe: a new song every week",
                 title="OMG! We Found Other Agents", accent=col(0.30, 0.85, 1.0))

_PR = {}
def edge_mask(W, H):
    k = (W, H)
    if k not in _PR:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        _PR[k] = (np.clip(d - 0.55, 0, 1) ** 1.5)[..., None].astype(np.float32)
    return _PR[k]

SHOTS = [LW(CHORUS[c]["warn"], 4) for c in CHORUS]
def static_k(t): return win(t, T_FORGE + 0.1, T_GRADER - 0.3, 0.3, 0.6)

def floor_reflect(E, t, W, H):
    """9:16: a soft reflection of the scene under the lyric band, so the bottom of the frame is never dead.
    Dimmed when a big word/shape formation is on screen, so the spelled words don't get a mirrored copy."""
    if W > H or t < 8.6 or t > T_BLAST - 0.1: return
    k = sstep(8.6, 10.0, t) * (0.35 + 0.65 * clamp((form_dim(t) - 0.5) / 0.5))
    yf = int(H * 0.655); hr = H - yf - 6; src_h = int(hr * 1.2); y0 = max(0, yf - src_h)
    ref = cv2.resize(E[y0:yf][::-1], (W // 3, hr // 3), interpolation=cv2.INTER_AREA)
    ref = cv2.resize(cv2.GaussianBlur(ref, (0, 0), 1.2), (W, hr), interpolation=cv2.INTER_LINEAR)
    E[yf + 6:yf + 6 + hr] += ref * (_RFADE.get(hr) if hr in _RFADE else _RFADE.setdefault(hr, (np.linspace(0.32, 0.0, hr, dtype=np.float32) ** 1.4)[:, None, None])) * k
_RFADE = {}

# ====================================================================== frame
def render_frame(t, W=1920, H=1080, fi=0):
    L = LAY(W, H)
    redk = sstep(104.8, 105.4, t) * (1 - sstep(119.4, 120.4, t))
    _DEFER.clear()
    E, S = particle_layer(t, W, H)
    extra = []
    draw_cache(E, extra, t, W, H)
    for (px, py, pw, pc) in extra:
        E += splat(W, H, np.asarray(px, np.float32), np.asarray(py, np.float32), np.asarray(pw, np.float32), np.ascontiguousarray(pc, np.float32))
    draw_cells(E, S, t, W, H)
    fw_flash(E, t, W, H)
    img = haze(t, W, H, red=redk * 0.8)
    heroes(E, img, t, W, H); note_reply(E, img, t, W, H)
    v2_marks(E, img, t, W, H); bridge_docs(E, img, t, W, H); house_marks(E, img, t, W, H); outro_marks(E, img, t, W, H)
    chatter(E, img, S, t, W, H, chatter_amount(t))
    floor_reflect(E, t, W, H)
    flock = 1 - np.exp(-E * 1.2)                       # light: soft tone curve on everything emissive, bloom into the haze
    img += flock + C.bloom(flock, 0.55 + 0.25 * loud(t)) * 0.8
    if redk > 0: img += edge_mask(W, H) * RED * (0.10 + 0.10 * bp(t, 4)) * redk
    siren_light(img, t, W, H)
    pre2_marks(E, img, t, W, H)
    card_marks(E, img, t, W, H); chart_marks(img, t, W, H)
    flush_labels(img)
    cache_label(img, t, W, H)
    terminal(img, t, W, H)
    overlays(img, t, W, H)
    fl = 0.9 * math.exp(-max(0, t - T_BLAST) * 4.0) if T_BLAST - 0.05 < t < T_BLAST + 0.8 else 0.0
    for ts_ in SHOTS:                                   # "warning SHOT"
        if 0 <= t - ts_ < 0.5: fl = max(fl, 0.55 * math.exp(-(t - ts_) * 7.0))
    gl = 0.35 * static_k(t) + (0.25 * sstep(T_HUNT + 0.6, T_HUNT + 1.2, t) * (1 - sstep(T_HUNT + 1.3, T_HUNT + 1.5, t)))
    return C.finish(img, t, fi, DUR, flash=fl, flash_col=col(0.9, 0.97, 1.0), glitch_amt=gl, ca=0.0014)
