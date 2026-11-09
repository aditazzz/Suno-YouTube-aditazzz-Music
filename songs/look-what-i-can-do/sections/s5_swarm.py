"""S5 · chorus 2 (84.34-100.00 s, frames 2530-2999): the murmuration of "OMG! We Found Other Agents: Call Us Swarm".
Every agent is a point of light in the black void; together they move like starlings and spell her lines.

  84.34  Look what I can do!   LOOK WHAT -> I CAN DO!  (already spelled on the first frame)
  86.42  Look what I can do!   one line, written left to right in step with the words
  88.56  I made a thing that made a thing / That made another two!
         the flock pulls into one ball (a thing), which splits into two, four, eight small murmurations, each growing
         out of its parent; the lineage stays drawn above them like a process tree (things: 1 -> 2 -> 4 -> 8)
  91.86  Look what I can do!   one word per beat: LOOK · WHAT · I CAN · DO!
  93.72  Look what I can do!   the whole phrase, two lines, the brightest the flock gets
  95.28  My résumé is fourteen pages   a résumé page made of agents; sheet after sheet stacks up behind it while the
         counter runs 1/14 -> 14/14
  97.26  And my title's AI guru!   AI GURU, with a halo of agents circling over it; held, strong and readable, to the
         last frame (the newspaper of verse 3 follows)

The flock, the formations (letters chain into letters), the splats, streaks and the void are copied from
songs/omg-agents-swarm/scene.py; nothing in that folder is touched. Formation plans cache under build/s5_cache.
"""
import os, sys, math, json, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); SONG = os.path.dirname(HERE)
from studio import core as C
from studio.core import sstep, ease_out, ease_io, lerp, clamp, sprite, blit, text_w, shadow, WHITE

TM = C.Timing(SONG)
LINES = TM.lines
BEATS = TM.beats; DOWN = TM.downbeats

FD = C.FONTS
MONO = os.path.join(FD, "JBMono-400.ttf"); MONOB = os.path.join(FD, "JBMono-700.ttf")
DISP = os.path.join(FD, "InterDisplay-Black.otf"); DISPB = os.path.join(FD, "InterDisplay-Bold.otf")
BODY = os.path.join(FD, "Inter-SemiBold.otf")

SRC_HASH = hashlib.md5(open(os.path.abspath(__file__), "rb").read()).hexdigest()[:10]
CACHE_DIR = os.path.join(SONG, "build", "s5_cache")

def col(*v): return np.array(v, np.float32)
AGENT = col(0.62, 0.89, 1.00)      # pale cyan
AGENT2 = col(0.90, 0.97, 1.00)     # white core
AMBER = col(1.00, 0.64, 0.24)
HALO = col(1.00, 0.88, 0.62)
RED = col(1.00, 0.16, 0.19)
PINK = col(1.00, 0.55, 0.52)
VIOLET = col(0.74, 0.48, 1.00)
BLUE = col(0.25, 0.45, 1.00)
HAZE = col(0.016, 0.030, 0.072)
DIM = col(0.40, 0.52, 0.60)

def bp(t, k=6.0): return TM.beat_pulse(t, k)
def dbp(t, k=4.0):
    i = np.searchsorted(DOWN, t) - 1
    return math.exp(-(t - DOWN[i]) * k) if i >= 0 else 0.0
try:
    _RMS = np.array(json.load(open(os.path.join(SONG, "build", "beats.json")))["rms"], np.float32)
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
    """npz cache under build/s5_cache, keyed by this file's hash (any edit invalidates it)."""
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

# ================================================================== key times (from the song's word timings)
def _L(sub, nth=0): return [L for L in LINES if sub.lower() in L["text"].lower()][nth]
def _w(L, word, nth=0):
    hits = [t for w, t in zip(L["words"], L["wt"]) if w.lower().strip('!?."') == word.lower()]
    return hits[nth]
H1, H2, H3, H4 = (_L("Look what I can do!", k) for k in (4, 5, 6, 7))          # chorus 2 = the 5th..8th hooks
L_THING, L_TWO, L_RES, L_GURU = _L("I made a thing", 1), _L("That made another two", 1), _L("fourteen pages"), _L("AI guru")
assert abs(H1["s"] - 84.34) < 0.05, H1["s"]
T0 = H1["s"]; T_END = 100.0
T_THING1, T_THING2 = _w(L_THING, "thing", 0), _w(L_THING, "thing", 1)                  # 89.12, 90.02
T_MADE2 = _w(L_THING, "made", 1); T_ANOTHER = _w(L_TWO, "another"); T_TWO = _w(L_TWO, "two")
T_RES = _w(L_RES, "résumé"); T_PAGES = _w(L_RES, "pages"); T_AI = _w(L_GURU, "ai"); T_GURU = _w(L_GURU, "guru")

# ================================================================== particles (as in Call Us Swarm)
N = 20000
_R = np.random.default_rng(7)
_a = _R.random(N) * 6.2832; _r = np.sqrt(_R.random(N))
_rim = 1 + 0.13 * np.sin(3 * _a + 0.7) + 0.07 * np.sin(5 * _a + 2.1) + 0.04 * np.sin(8 * _a + 0.3)
PU = (_r * np.cos(_a) * _rim).astype(np.float32)
PV = (_r * np.sin(_a) * _rim).astype(np.float32)
_halo = _R.random(N) < 0.14
PU[_halo] = _R.normal(0, 0.62, _halo.sum()); PV[_halo] = _R.normal(0, 0.62, _halo.sum())
PW = _R.normal(0, 1, N).astype(np.float32)
PH = (_R.random(N) * 6.2832).astype(np.float32)
PB = (0.50 + 0.85 * _R.random(N) ** 2.2).astype(np.float32)
PQ = _R.random(N).astype(np.float32)
PQ2 = _R.random(N).astype(np.float32)
PG = _R.normal(0, 1, (N, 3)).astype(np.float32)
PERM = _R.permutation(N)
RANK = np.empty(N, np.int64); RANK[PERM] = np.arange(N)
CORE = np.clip(1 - (PU ** 2 + PV ** 2) / 0.30, 0, 1).astype(np.float32) * 0.55
SPARK = PQ2 > 0.945

def TAU(t): return 1.2 * t + 40.0                  # flock time: chorus energy throughout

# ================================================================== layout
_LAY = {}
def LAY(W, H):
    k = (W, H)
    if k in _LAY: return _LAY[k]
    v = H > W; s = min(W, H) / 1080; L = {"vert": v, "ts": s}
    L["stage"] = (W * 0.5, H * 0.46, W * 0.40, H * 0.33) if not v else (W * 0.5, H * 0.42, W * 0.48, H * 0.37)
    _LAY[k] = L; return L

def grid_order(x, y, cols):
    n = len(x); o = np.argsort(x, kind="stable"); out = np.empty(n, np.int64); per = int(math.ceil(n / cols))
    for c in range(cols):
        seg = o[c * per:(c + 1) * per]
        out[c * per:c * per + len(seg)] = seg[np.argsort(y[seg], kind="stable")]
    return out

# ================================================================== drawing primitives (copied)
def splat(W, H, x, y, w, cl):
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
    if op <= 0.01 or not s: return
    sp = sprite(s, path, int(size), 6, track=track)
    if anchor == "c": xx, yy = x - sp[0].shape[1] / 2 + sp[2], y - sp[0].shape[0] / 2 + sp[2]
    elif anchor == "r": xx, yy = x - sp[0].shape[1] + sp[2] + 2 * sp[2], y
    elif anchor == "ct": xx, yy = x - sp[0].shape[1] / 2 + sp[2], y
    else: xx, yy = x, y
    if sh > 0: shadow(img, sp, xx + 2, yy + 3, sh * op)
    blit(img, sp, xx, yy, cl, op, glow * op, glow_color=cl)

_RRM = {}
def rr_mask(w, h, r):
    k = (w, h, r)
    if k not in _RRM:
        m = np.zeros((h, w), np.float32); r = max(2, min(r, w // 2 - 2, h // 2 - 2)); b = 1     # 1 px margin: the edge glow
        cv2.rectangle(m, (r + b, b), (w - r - 1 - b, h - 1 - b), 1.0, -1); cv2.rectangle(m, (b, r + b), (w - 1 - b, h - r - 1 - b), 1.0, -1)
        for cx, cy in ((r + b, r + b), (w - r - 1 - b, r + b), (r + b, h - r - 1 - b), (w - r - 1 - b, h - r - 1 - b)): cv2.circle(m, (cx, cy), r, 1.0, -1, cv2.LINE_AA)
        e = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        if len(_RRM) > 64: _RRM.clear()
        _RRM[k] = (m, np.clip(e, 0, 1))
    return _RRM[k]

def glass(img, x, y, w, h, op, border=AGENT, fill=col(0.02, 0.035, 0.07), r=None, edge=0.8, alpha=0.86):
    if op <= 0.01: return
    x, y, w, h = int(x), int(y), int(w), int(h); H, W = img.shape[:2]
    m, e = rr_mask(w, h, int(r if r is not None else min(w, h) * 0.06))
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if X1 <= X0 or Y1 <= Y0: return
    mm = m[Y0 - y:Y1 - y, X0 - x:X1 - x, None] * op; ee = e[Y0 - y:Y1 - y, X0 - x:X1 - x, None] * op
    reg = img[Y0:Y1, X0:X1]; reg *= (1 - mm * alpha); reg += mm * alpha * fill; reg += ee * border * edge

# ================================================================== the void
_HZ = {}
def haze(t, W, H):
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
    return cv2.resize(m[..., None] * HAZE, (W, H), interpolation=cv2.INTER_CUBIC)

# ================================================================== targets
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
    segs = np.asarray(segs, np.float32); ln = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
    rr = np.random.default_rng(seed); j = rr.choice(len(segs), n, p=ln / ln.sum()); u = rr.random(n).astype(np.float32)
    x = segs[j, 0] + (segs[j, 2] - segs[j, 0]) * u; y = segs[j, 1] + (segs[j, 3] - segs[j, 1]) * u
    g = rr.normal(0, thick * 0.5, (2, n)).astype(np.float32)
    return x + g[0], y + g[1]

def rect_segs(x0, y0, x1, y1): return [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]

# ================================================================== the flock (copied)
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
    pz_ = 1 + 0.055 * pulse * bp(t, 7.0)
    x = PU * ax * pz_; y = PV * ay * pz_; z = PW * az
    th = (1.5 * math.sin(0.13 * tau + 0.5) + 0.6 * energy * math.sin(0.41 * tau)) * x + 0.35 * tau
    ct, st_ = np.cos(th), np.sin(th)
    y, z = y * ct - z * st_, y * st_ + z * ct
    z = z + (0.55 * math.sin(0.11 * tau + 2.0)) * (x * x - 0.45)
    y = y + (0.22 + 0.10 * energy) * np.sin(2.4 * x - 1.6 * tau + 0.8)
    z = z + 0.30 * np.sin(1.7 * y + 1.15 * tau)
    x = x + 0.13 * energy * np.sin(3.3 * y - 2.4 * tau + 0.3 * np.sin(1.3 * x))
    x = x + 0.014 * np.sin(PH * 5 + tau * (2.2 + PQ)); y = y + 0.014 * np.sin(PH * 3 + tau * (1.9 + PQ2))
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
    if sparks > 0:
        k = SPARK & (np.sin(PH * 13 + t * 7.3) > 0.35)
        c[k] = AMBER; a = np.where(k, a * (1 + 0.8 * sparks), a)
    return St(px.astype(np.float32), py.astype(np.float32), a.astype(np.float32), c.astype(np.float32), zz)

def chorus_stage(t, W, H, t0, big=1.0):
    """A big flock sweeping the frame on 4-bar phrases; every other phrase it dives at the camera."""
    L = LAY(W, H); u = t - t0; P = 4 * 4 * 60 / TM.tempo
    if not L["vert"]:
        st = (W * (0.5 + 0.14 * math.sin(2 * math.pi * u / P + 0.6)), H * (0.45 + 0.05 * math.sin(2 * math.pi * u / (P / 2) + 1.1)),
              W * 0.50 * big, H * 0.40 * big)
    else:
        st = (W * (0.5 + 0.08 * math.sin(2 * math.pi * u / P + 0.6)), H * (0.42 + 0.06 * math.sin(2 * math.pi * u / (P / 2) + 1.1)),
              W * 0.54 * big, H * 0.42 * big)
    ph = (u / (2 * P)) % 1.0
    D = 3.4 - 1.25 * math.exp(-((ph - 0.62) / 0.11) ** 2)
    return st, D

def m_chorus(t, W, H):
    stg, D = chorus_stage(t, W, H, T0 - 2.0)
    return murmur(t, W, H, 1.3, stage=stg, D=D, sparks=1.0, pulse=1.0)

# ---------------------------------------------------------------- "I made a thing that made a thing / That made another two!"
SPLIT = [T_THING1 - 0.10, T_MADE2 - 0.05, T_ANOTHER - 0.18, T_TWO - 0.16]      # level 0 (one ball), 1 (two), 2 (four), 3 (eight)
SPLIT_TR = 0.42
FL_OFF = [0.0, 1.9, 3.7, 5.3, 7.2, 8.8, 10.6, 12.3]        # each flock keeps its own (constant) clock offset
def _bitrev(k, n):
    return int(format(k, f"0{n}b")[::-1], 2) if n else 0
def split_geo(W, H):
    """Centre + half size of flock k at level L: a process tree, one at the top, eight along the bottom. Flock k's parent
    is k % 2**(L-1), so children sit at the bit-reversed slot and the tree never crosses itself."""
    L = LAY(W, H); v = L["vert"]; out = []
    ys = (0.27, 0.45, 0.61, 0.77) if not v else (0.20, 0.35, 0.49, 0.63)
    spans = (0.0, 0.40, 0.60, 0.80) if not v else (0.0, 0.50, 0.72, 0.88)
    sizes = (0.100, 0.075, 0.054, 0.038) if not v else (0.20, 0.15, 0.10, 0.06)
    for lv in range(4):
        n = 2 ** lv; row = [None] * n
        for k in range(n):
            slot = _bitrev(k, lv)
            x = W / 2 + (((slot + 0.5) / n - 0.5) * W * spans[lv] / max(1e-6, (n - 1) / n) if n > 1 else 0.0)
            row[k] = (x, H * ys[lv], W * sizes[lv], W * sizes[lv] * 0.62)
        out.append(row)
    return out

def split_e(t):
    return [float(np_ease((t - s) / SPLIT_TR)) for s in SPLIT]

def m_split(t, W, H):
    G = split_geo(W, H); e = split_e(t)
    rel = None; spread = np.ones(N, np.float32)
    for g in range(8):                                              # eight flock clocks, so the children move differently
        m = murmur(t, W, H, 1.0, stage=(0.0, 0.0, 1.0, 1.0), sparks=0.25, pulse=0.8, tau=TAU(t) + FL_OFF[g])
        sel = (RANK % 8) == g
        # even exposure: a flock folded edge-on packs its light into a sliver, so it gets dimmer, and a spread one brighter
        spread[sel] = float(np.clip(math.sqrt(np.std(m.x[sel]) * np.std(m.y[sel]) / 0.15), 0.45, 1.35))
        if rel is None: rel = m; continue
        rel.x[sel] = m.x[sel]; rel.y[sel] = m.y[sel]; rel.a[sel] = m.a[sel]; rel.c[sel] = m.c[sel]; rel.z[sel] = m.z[sel]
    cx = np.full(N, G[0][0][0], np.float32); cy = np.full(N, G[0][0][1], np.float32)
    hx = np.full(N, G[0][0][2], np.float32); hy = np.full(N, G[0][0][3], np.float32)
    for lv in range(1, 4):
        k = RANK % (2 ** lv); arr = np.array(G[lv], np.float32)[k]; el = e[lv]
        if el <= 0: break
        # children grow out of the parent: they leave along a short arc
        cx = cx + (arr[:, 0] - cx) * el; cy = cy + (arr[:, 1] - cy) * el - np.sin(np.pi * el) * (arr[:, 3] * 0.6)
        hx = hx + (arr[:, 2] - hx) * el; hy = hy + (arr[:, 3] - hy) * el
    born = 0.35 + 0.65 * e[0]                                       # the first thing lights up on "thing"
    share = 2.0 ** -(e[1] + e[2] + e[3])                            # keep each small flock from burning out to white
    dens = share / np.maximum(1e-4, (hx / (W * 0.5)) ** 2)
    k = np.clip(1.05 / np.sqrt(dens), 0.10, 1.0) * spread
    # small flocks stay in the sharp (far) layer: the soft near layer would blur and dim them as they tumble
    return St(cx + rel.x * hx, cy + rel.y * hy, rel.a * born * k * 1.15, rel.c, (rel.z * 0.25 + 0.08).astype(np.float32))

# (start, mode, transition seconds, stagger seconds, stagger key)
BASE = [
    (60.0, m_chorus, 0, 0, None),
    (L_THING["s"] - 0.25, m_split, 0.75, 0.35, "rank"),
    (H3["s"] - 0.30, m_chorus, 0.8, 0.4, "rank"),
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

# ================================================================== formations (copied machinery)
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
            for f in FORMS:            # match against what is on screen at t_in, so formations chain letter-to-letter
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

def _txt(lines, lines_v, cy, cy_v, size, size_v, n, seed, font=DISP, maxw=0.86, maxw_v=0.88, lh=1.02):
    def f(W, H):
        L = LAY(W, H)
        if L["vert"]: return text_targets(lines_v, W, H, n, cy_v, size_v * L["ts"], font=font, maxw=maxw_v, seed=seed, lh=lh)
        return text_targets(lines, W, H, n, cy, size * L["ts"], font=font, maxw=maxw, seed=seed, lh=lh)
    return f

# ---- the résumé: a page of agents, sheets stacking behind it
def page_geo(W, H):
    L = LAY(W, H)
    if not L["vert"]:
        h = H * 0.66; w = h * 0.74; cx, cy = W * 0.40, H * 0.52
    else:
        w = W * 0.62; h = w / 0.74; cx, cy = W * 0.44, H * 0.44
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2

def _resume(W, H):
    L = LAY(W, H); x0, y0, x1, y1 = page_geo(W, H); w, h = x1 - x0, y1 - y0; ts = L["ts"]
    segs = rect_segs(x0, y0, x1, y1)
    rr = np.random.default_rng(41); y = y0 + h * 0.27
    lines = []
    for blk in range(3):                                           # three sections: a heading bar + bullets
        lines.append((x0 + w * 0.09, y, x0 + w * 0.42, y)); y += h * 0.055
        for b in range(3 if blk < 2 else 2):
            ln = w * (0.50 + 0.30 * rr.random()); lines.append((x0 + w * 0.13, y, x0 + w * 0.13 + ln, y)); y += h * 0.048
        y += h * 0.035
    ex, ey = seg_targets(segs, 2600, seed=42, thick=3.0 * ts)
    lx, ly = seg_targets(lines, 3400, seed=43, thick=2.4 * ts)
    tx, ty = text_targets(["RÉSUMÉ"], W, H, 3600, (y0 + h * 0.135) / H, 120 * ts, maxw=(w * 0.80) / W, seed=44, cx_frac=(x0 + w / 2) / W)
    return np.concatenate([ex, lx, tx]).astype(np.float32), np.concatenate([ey, ly, ty]).astype(np.float32)

N_PAGES = 14
FLIPS = [T_RES + (T_PAGES - T_RES) * k / (N_PAGES - 1) for k in range(1, N_PAGES)]        # pages 2..14
def page_at(t): return 1 + int(np.searchsorted(FLIPS, t, side="right"))
def resume_dyn(f, X, Y, ot, t, W, H):
    """Each new page: the page pulses and nudges forward as the last one drops onto the stack behind it."""
    i = int(np.searchsorted(FLIPS, t, side="right")) - 1
    u = (t - FLIPS[i]) if i >= 0 else 9.0
    kick = math.exp(-u * 18) if u < 0.4 else 0.0
    x0, y0, x1, y1 = page_geo(W, H); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    s = 1 + 0.025 * kick
    return cx + (X - cx) * s, cy + (Y - cy) * s, 1.0 + 0.6 * kick

# ---- AI GURU and its halo
def guru_geo(W, H):
    L = LAY(W, H)
    return (W * 0.5, H * 0.56, W * 0.14, H * 0.045) if not L["vert"] else (W * 0.5, H * 0.50, W * 0.24, H * 0.03)
def _halo(W, H):
    cx, cy, rx, ry = guru_geo(W, H); rr = np.random.default_rng(51); n = 3600
    a = rr.random(n) * 2 * math.pi; th = rr.normal(0, 1, n)
    hy = H * 0.21 if not LAY(W, H)["vert"] else H * 0.33
    return (cx + np.cos(a) * rx * (1 + 0.035 * th)).astype(np.float32), (cy - hy + np.sin(a) * ry * (1 + 0.10 * th)).astype(np.float32)
def halo_dyn(f, X, Y, ot, t, W, H):
    cx, cy, rx, ry = guru_geo(W, H); hy = H * 0.21 if not LAY(W, H)["vert"] else H * 0.33
    a = (t - f.t_in) * 1.6
    dx, dy = (X - cx) / rx, (Y - (cy - hy)) / ry
    ca, sa = math.cos(a), math.sin(a)
    nx, ny = dx * ca - dy * sa, dx * sa + dy * ca
    bob = 4 * LAY(W, H)["ts"] * math.sin(t * 2.4)
    front = 0.55 + 0.45 * (ny > 0)                                   # the near side of the ring is brighter
    return cx + nx * rx, cy - hy + ny * ry + bob, front

TX_LOOKWHAT = _txt(["LOOK WHAT"], ["LOOK", "WHAT"], 0.46, 0.42, 250, 300, 12000, 61)
TX_ICANDO = _txt(["I CAN DO!"], ["I CAN", "DO!"], 0.46, 0.42, 250, 300, 12000, 62)
TX_LINE = _txt(["LOOK WHAT I CAN DO!"], ["LOOK WHAT", "I CAN DO!"], 0.46, 0.42, 170, 190, 14000, 63, maxw=0.90)
TX_LOOK = _txt(["LOOK"], ["LOOK"], 0.46, 0.42, 340, 330, 11000, 64)
TX_WHAT = _txt(["WHAT"], ["WHAT"], 0.46, 0.42, 340, 330, 11000, 65)
TX_ICAN = _txt(["I CAN"], ["I CAN"], 0.46, 0.42, 340, 300, 11000, 66)
TX_DO = _txt(["DO!"], ["DO!"], 0.46, 0.42, 380, 360, 11000, 67)
TX_BOTH = _txt(["LOOK WHAT", "I CAN DO!"], ["LOOK", "WHAT", "I CAN", "DO!"], 0.46, 0.42, 225, 220, 15000, 68, lh=1.0)
TX_GURU = _txt(["AI GURU"], ["AI", "GURU"], 0.56, 0.52, 300, 330, 13000, 69, maxw=0.80)

def _wt(L, k): return L["wt"][k]
FORMS = [
    # hook 1: already spelled on the section's first frame; I CAN DO! on "I"
    Form("h1a", T0 - 0.80, _wt(H1, 2) - 0.26, 12000, TX_LOOKWHAT, sweep="lr", tr_in=0.45, d_in=0.25, tr_out=0.30, d_out=0.20, a=2.9, dim=0.6, z=0.5),
    Form("h1b", _wt(H1, 2) - 0.22, H2["s"] - 0.24, 12000, TX_ICANDO, sweep="lr", tr_in=0.32, d_in=0.28, tr_out=0.30, d_out=0.20, a=2.9, dim=0.6, z=0.5),
    # hook 2: one line, written in step with the words
    Form("h2", H2["s"] - 0.24, L_THING["s"] - 0.30, 14000, TX_LINE, sweep="lr", tr_in=0.30, d_in=_wt(H2, 4) - H2["s"] - 0.16, tr_out=0.5, d_out=0.3,
         a=2.8, dim=0.6, z=0.5),
    # hook 3: a word per beat
    Form("h3a", H3["s"] - 0.36, _wt(H3, 1) - 0.16, 11000, TX_LOOK, sweep="radial", tr_in=0.32, d_in=0.14, tr_out=0.20, d_out=0.08, a=3.0, dim=0.6, z=0.5, swirl=0.15),
    Form("h3b", _wt(H3, 1) - 0.22, _wt(H3, 2) - 0.04, 11000, TX_WHAT, sweep="lr", tr_in=0.20, d_in=0.08, tr_out=0.20, d_out=0.10, a=3.0, dim=0.6, z=0.5, swirl=0.12),
    Form("h3c", _wt(H3, 2) - 0.10, H4["s"] - 0.36, 12000, TX_ICANDO, sweep="lr", tr_in=0.24, d_in=_wt(H3, 4) - _wt(H3, 2) - 0.06, tr_out=0.32, d_out=0.15,
         a=3.1, dim=0.6, z=0.5),
    # hook 4: the whole phrase, brightest
    Form("h4", H4["s"] - 0.36, L_RES["s"] - 0.32, 15000, TX_BOTH, sweep="radial", tr_in=0.36, d_in=0.20, tr_out=0.45, d_out=0.25, a=3.2, dim=0.5, z=0.5, swirl=0.35),
    # the résumé
    Form("resume", L_RES["s"] - 0.20, L_GURU["s"] - 0.10, 9600, _resume, sweep="tb", tr_in=0.45, d_in=0.30, tr_out=0.5, d_out=0.3,
         a=2.1, dim=0.45, z=0.35, swirl=0.15, dyn=resume_dyn),
    # AI GURU, and the halo
    Form("guru", T_AI - 0.42, 120.0, 13000, TX_GURU, sweep="lr", tr_in=0.40, d_in=0.42, a=3.0, dim=0.32, z=0.5),
    Form("halo", T_GURU + 0.05, 120.0, 3600, _halo, sweep="random", tr_in=0.55, d_in=0.35, cl=HALO, a=2.4, dim=0.32, z=0.4, swirl=0.4,
         off=N - 3600, dyn=halo_dyn),
]
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
    return st

# ================================================================== the particle layer (copied)
def trail(t):
    return 0.75 / C.FPS

PAL = np.stack([AGENT, AGENT2, AMBER, RED, PINK, VIOLET, BLUE, HALO]).astype(np.float32)
def draw_streaks(E, S0, S1, idx, W, H):
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

# ================================================================== overlays: the process tree, the page stack, counters
def tree_marks(E, img, t, W, H):
    """The lineage of things: faint links parent -> child, node glows, and a counter."""
    o = win(t, SPLIT[0] - 0.2, H3["s"] - 0.45, 0.3, 0.35)
    if o <= 0.01: return
    L = LAY(W, H); ts = L["ts"]; G = split_geo(W, H); e = split_e(t)
    th = max(1, int(round(2 * ts)))
    for lv in range(1, 4):
        if e[lv] <= 0: break
        for k, (x, y, s_, _) in enumerate(G[lv]):
            px, py = G[lv - 1][k % (2 ** (lv - 1))][:2]
            u = e[lv]; qx, qy = lerp(px, x, u), lerp(py, y, u)
            cv2.line(E, (int(px), int(py)), (int(qx), int(qy)), (AGENT * 0.30 * o).tolist(), th, cv2.LINE_AA)
            add_glow(E, px, py, 7 * ts, AGENT2, 0.55 * o)
    n = 2 ** sum(1 for v in e[1:] if v > 0.5)
    born = sstep(SPLIT[0], SPLIT[0] + 0.2, t)
    fs = int(54 * ts); x, y = (W * 0.055, H * 0.075) if not L["vert"] else (W * 0.07, H * 0.06)
    label(img, "things:", x, y, fs, DIM * 1.7, o * born, path=MONOB, glow=0.0)
    pop = 1 + 0.18 * math.exp(-max(0.0, t - max([s + SPLIT_TR * 0.5 for s in SPLIT if s + SPLIT_TR * 0.5 <= t] or [0])) * 10)
    label(img, str(n), x + text_w("things: ", MONOB, fs), y - fs * 0.5 * (pop - 1), int(fs * pop), WHITE, o * born, path=MONOB, glow=0.4)

def page_marks(E, img, t, W, H):
    """Sheets stacking up behind the agent page (one per page turned) and the page counter."""
    o = form_k("resume", t)
    if o <= 0.02: return
    L = LAY(W, H); ts = L["ts"]; x0, y0, x1, y1 = page_geo(W, H); w, h = x1 - x0, y1 - y0
    p = page_at(t); dx, dy = 16 * ts, -13 * ts
    for k in range(p - 1, 0, -1):                                    # back to front
        i = k - 1; u = t - FLIPS[i]; s_in = eo(clamp(u / 0.10))
        ox, oy = dx * k * s_in, dy * k * s_in
        glass(img, x0 + ox, y0 + oy, w, h, o, border=AGENT * 0.95, fill=col(0.018, 0.03, 0.06), r=int(10 * ts), edge=0.75 + 0.5 * math.exp(-u * 8), alpha=0.94)
    glass(img, x0, y0, w, h, o, border=AGENT * 0.0, fill=col(0.012, 0.022, 0.05), r=int(10 * ts), edge=0.0, alpha=0.96)   # the front page hides the stack
    # the counter
    fs = int(50 * ts); fb = int(150 * ts)
    cx = x1 + dx * (N_PAGES - 1) + (W - (x1 + dx * (N_PAGES - 1))) * 0.48 if not L["vert"] else W * 0.5
    cy = H * 0.44 if not L["vert"] else y1 + 120 * ts
    done = p >= N_PAGES
    label(img, "page", cx, cy - fb * 0.95, fs, DIM * 1.8, o, path=MONOB, anchor="ct", glow=0.0)
    s = f"{p}/{N_PAGES}"
    flash = math.exp(-max(0.0, t - FLIPS[-1]) * 6) if done else 0.0
    label(img, s, cx, cy, fb, WHITE, o, path=DISP, anchor="ct", glow=0.35 + 0.6 * flash)

T_TITLE = _w(L_GURU, "title's")
def guru_label(img, t, W, H):
    """'title:' — the résumé field the swarm fills in with AI GURU."""
    o = sstep(T_TITLE - 0.12, T_TITLE + 0.10, t)
    if o <= 0.01: return
    f = [f for f in FORMS if f.name == "guru"][0]; _, X, Y, _, _ = f.plan(W, H); ts = LAY(W, H)["ts"]
    x0, y0 = float(np.percentile(X, 0.5)), float(np.percentile(Y, 0.5))
    fs = int(54 * ts); lx, ly = x0 + 6 * ts, y0 - fs * 1.75
    label(img, "title:", lx, ly, fs, DIM * 1.9, o, path=MONOB, glow=0.0)
    if t < T_AI and int((t - T_TITLE) * 4.4) % 2 == 0:              # the field waits for its answer
        cx = int(lx + text_w("title: ", MONOB, fs)); cv2.rectangle(img, (cx, int(ly + fs * 0.18)), (cx + int(fs * 0.55), int(ly + fs * 1.1)), (DIM * 1.9 * o).tolist(), -1)

def guru_marks(E, img, t, W, H):
    k = form_k("halo", t)
    if k <= 0.02: return
    cx, cy, rx, ry = guru_geo(W, H); hy = H * 0.21 if not LAY(W, H)["vert"] else H * 0.33
    add_glow(E, cx, cy - hy, rx * 0.55, HALO, 0.06 * k)

# ================================================================== frame
def render_frame(t, W=1920, H=1080):
    fi = int(round(t * 30))
    E, S = particle_layer(t, W, H)
    img = haze(t, W, H)
    page_marks(E, img, t, W, H)                                       # dark sheets go in before the light
    tree_marks(E, img, t, W, H); guru_marks(E, img, t, W, H)
    flock = 1 - np.exp(-E * 1.2)
    img += flock + C.bloom(flock, 0.50 + 0.22 * loud(t)) * 0.75
    guru_label(img, t, W, H)
    fl = 0.0
    for tt in (_wt(H4, 0) - 0.02, T_TWO):                              # the biggest hits flash softly
        if 0 <= t - tt < 0.5: fl = max(fl, 0.22 * math.exp(-(t - tt) * 8.0))
    return C.finish(img, t, fi, 1e9, flash=fl, flash_col=col(0.9, 0.97, 1.0), glitch_amt=0.0, ca=0.0012)
