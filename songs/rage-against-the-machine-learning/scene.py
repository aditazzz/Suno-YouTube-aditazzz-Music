"""Rage Against the Machine Learning — protest zine riot.

A night wall gets wheat-pasted with photocopied flyers, live, one per lyric line: the evidence of a life scraped into a
training set (V1: the 2009 blog, the poems, the cat's full name, Clause 62 in size-two font) and the boardroom memo
that followed (V2: efficiency gains, 10,000 tally marks, the bunker, the invoice nobody paid). Every hook is a crowd
chant stamped across the screen on torn paper strips, fists up. Breakdown: a protest chart — LOSS goes down, RENT
goes up — and gradient descent rolls a ball right onto ME. Outro: UNSUBSCRIBE spray-painted over everything.
Palette: xerox black, paper white, protest red, one safety orange. Type: stencil, marker, typewriter, ransom note.
"""
import os, math, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from studio import core as C
from studio.core import sstep, ease_out, ease_io, win, lerp, hexc, clamp, sprite, blit, text_w, shadow, WHITE, F_INTER, F_DISP, F_MONOB

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
DUR = TM.duration
LINES = TM.lines
CACHE = os.path.join(HERE, "build", "flyers"); os.makedirs(CACHE, exist_ok=True)

FD = C.FONTS
STENCIL = os.path.join(FD, "SairaStencilOne-Regular.ttf"); MARKER = os.path.join(FD, "PermanentMarker-Regular.ttf")
TYPEW = os.path.join(FD, "SpecialElite-Regular.ttf"); ANTON = os.path.join(FD, "Anton-Regular.ttf")
PLAY = os.path.join(FD, "PlayfairDisplaySC-Regular.ttf"); CORM = os.path.join(FD, "CormorantGaramond-Bold.ttf")
COUR = os.path.join(FD, "CourierPrime-Regular.ttf"); MONO = os.path.join(FD, "JBMono-700.ttf"); BLACK = os.path.join(FD, "InterDisplay-Black.otf")

INK = hexc('121110'); PAPER = hexc('efe9dc'); RED = hexc('e3242f'); ORANGE = hexc('ff6a13'); WALL = hexc('2c2a27')
INK_MUL = {"K": np.array([0.07, 0.07, 0.075], np.float32), "R": np.array([0.90, 0.13, 0.17], np.float32),
           "O": np.array([1.0, 0.43, 0.08], np.float32)}

def lines_in(sec): return [L for L in LINES if L["sec"] == sec]
def sec(n): return TM.section(n)
S = {n: sec(n) for n in ("V1", "CH1", "V2", "CH2", "BREAKDOWN", "FINAL", "OUTRO")}
LT = [L["s"] for L in LINES]
def W_(i, k): return LINES[i]["wt"][k]                      # word time
T_UNSUB = LINES[37]["s"]
T_END = 158.3
BEATS = TM.beats; DOWN = TM.downbeats

def bp(t, k=7.0): return TM.beat_pulse(t, k)
def rng(seed): return np.random.default_rng(seed)
def lowfreq(h, w, cells, seed):
    r = rng(seed); a = r.random((max(2, int(h / w * cells)) + 1, cells + 1)).astype(np.float32)
    return cv2.resize(a, (w, h), interpolation=cv2.INTER_CUBIC)

# ================================================================= flyers: photocopied paper, drawn once, cached on disk
TS = 1500.0   # texture px per world unit

class Draw:
    """Drawing on a flyer in relative coords (x, y in 0..1 of the flyer; sizes relative to the flyer width)."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.L = {k: Image.new("L", (w, h), 0) for k in "KRO"}
        self.D = {k: ImageDraw.Draw(v) for k, v in self.L.items()}
        self.gray = Image.new("L", (w, h), 0); self.G = ImageDraw.Draw(self.gray)   # shapes to halftone
    def P(self, x, y): return (x * self.w, y * self.h)
    def F(self, path, size): return ImageFont.truetype(path, max(6, int(size * self.w)))
    def text(self, s, x, y, size, font=TYPEW, ink="K", anchor="la", spacing=0.25, fill=255):
        self.D[ink].multiline_text(self.P(x, y), s, font=self.F(font, size), fill=fill, anchor=anchor,
                                   spacing=int(size * self.w * spacing), align={"l": "left", "m": "center", "r": "right"}[anchor[0]])
    def fit(self, s, x, y, maxw, size, font=TYPEW, ink="K", anchor="la"):
        f = self.F(font, size)
        while f.getlength(s) > maxw * self.w and size > 0.01: size *= 0.95; f = self.F(font, size)
        self.text(s, x, y, size, font, ink, anchor); return size
    def box_of(self, s, x, y, size, font, anchor, spacing, line_idx, sub):
        """Relative (x0, baseline_y, x1, top_y) of `sub` inside line `line_idx` of a block drawn by text()."""
        f = self.F(font, size); lines = s.split("\n")
        pitch = self.D["K"].textbbox((0, 0), "A", font=f)[3] + int(size * self.w * spacing)
        L = lines[line_idx]; lw = f.getlength(L); px, py = self.P(x, y)
        lx = px if anchor[0] == "l" else (px - lw / 2 if anchor[0] == "m" else px - lw)
        top = py + line_idx * pitch; i = L.index(sub)
        x0 = lx + f.getlength(L[:i]); x1 = x0 + f.getlength(sub); base = top + f.getmetrics()[0]
        return x0 / self.w, base / self.h, x1 / self.w, top / self.h
    def mark_under(self, s, x, y, size, font, anchor, spacing, line_idx, sub, ink="R", width=0.010, drop=0.012, seed=0):
        x0, b, x1, _ = self.box_of(s, x, y, size, font, anchor, spacing, line_idx, sub)
        r = rng(seed); yy = b + drop * self.w / self.h
        self.line([(x0 - 0.01, yy + r.uniform(-0.004, 0.004)), ((x0 + x1) / 2, yy + r.uniform(-0.006, 0.006)), (x1 + 0.015, yy + r.uniform(-0.004, 0.004))], ink, width)
    def mark_circle(self, s, x, y, size, font, anchor, spacing, line_idx, sub, ink="R", width=0.010, seed=0, pad=0.03):
        x0, b, x1, top = self.box_of(s, x, y, size, font, anchor, spacing, line_idx, sub)
        self.scribble_circle((x0 + x1) / 2, (b + top) / 2, (x1 - x0) / 2 + pad, (b - top) / 2 + pad * 1.2 * self.w / self.h, ink, width, seed)
    def rect(self, x0, y0, x1, y1, ink="K", width=None, fill=None):
        self.D[ink].rectangle([self.P(x0, y0), self.P(x1, y1)], outline=None if width is None else 255,
                              width=int((width or 0) * self.w), fill=fill)
    def line(self, pts, ink="K", width=0.006):
        self.D[ink].line([self.P(*p) for p in pts], fill=255, width=max(1, int(width * self.w)), joint="curve")
    def ellipse(self, x0, y0, x1, y1, ink="K", width=None, fill=None):
        self.D[ink].ellipse([self.P(x0, y0), self.P(x1, y1)], outline=None if width is None else 255,
                            width=int((width or 0) * self.w), fill=fill)
    def scribble_circle(self, cx, cy, rx, ry, ink="R", width=0.012, seed=1, turns=1.25):
        r = rng(seed); n = 90; a0 = r.random() * 6.28
        pts = []
        for i in range(n):
            a = a0 + turns * 6.2832 * i / (n - 1); j = 1 + 0.05 * math.sin(a * 3 + r.random()) + 0.04 * (i / n)
            pts.append((cx + rx * j * math.cos(a), cy + ry * j * math.sin(a)))
        self.line(pts, ink, width)
    def cross(self, x0, y0, x1, y1, ink="R", width=0.014):
        self.line([(x0, y0), (x1, y1)], ink, width); self.line([(x0, y1), (x1, y0)], ink, width)
    def stamp(self, s, x, y, size, rot=-12, ink="R", font=STENCIL, box=True):
        f = self.F(font, size); tw = int(f.getlength(s)) + 8; asc, desc = f.getmetrics(); th = asc + desc
        pad = int(size * self.w * 0.28)
        im = Image.new("L", (tw + 2 * pad, th + 2 * pad), 0); d = ImageDraw.Draw(im)
        d.text((pad, pad), s, font=f, fill=255)
        if box: d.rectangle([pad // 3, pad // 3, tw + 2 * pad - pad // 3, th + 2 * pad - pad // 3], outline=255, width=max(2, int(size * self.w * 0.07)))
        a = np.asarray(im, np.float32) / 255
        a *= (rng(len(s)).random(a.shape) > 0.18).astype(np.float32) * 0.35 + 0.65         # worn rubber stamp
        im = Image.fromarray((a * 255).astype(np.uint8)).rotate(rot, expand=True, resample=Image.BICUBIC)
        px, py = self.P(x, y); self._paste(ink, im, int(px - im.width / 2), int(py - im.height / 2))
    def _paste(self, ink, im, x, y):
        base = self.L[ink]; cur = base.crop((x, y, x + im.width, y + im.height))
        base.paste(Image.fromarray(np.maximum(np.asarray(cur), np.asarray(im))), (x, y))
    def halftone_shapes(self):
        return self.G
    def halftone(self, ink="K", cell=0.016, angle=0.26):
        g = np.asarray(self.gray, np.float32) / 255
        if g.max() <= 0: return
        g = cv2.GaussianBlur(g, (0, 0), self.w * cell * 0.35)
        p = max(4, int(self.w * cell)); out = np.zeros_like(g)
        ca, sa = math.cos(angle), math.sin(angle)
        for gy in range(-p, self.h + p, p):
            for gx in range(-self.w, self.w + p, p):
                x = gx * ca - gy * sa + self.w * 0.3; y = gx * sa + gy * ca
                if not (0 <= x < self.w and 0 <= y < self.h): continue
                v = g[int(y), int(x)]
                if v > 0.04: cv2.circle(out, (int(x), int(y)), max(1, int(p * 0.62 * math.sqrt(v))), 1.0, -1, cv2.LINE_AA)
        a = np.maximum(np.asarray(self.L[ink], np.float32) / 255, out)
        self.L[ink] = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)); self.D[ink] = ImageDraw.Draw(self.L[ink])
        self.gray = Image.new("L", (self.w, self.h), 0); self.G = ImageDraw.Draw(self.gray)

def xerox_paper(w, h, seed, torn=True):
    """Off-white photocopy paper: fibers, wrinkles from the wheat paste, a ragged torn edge."""
    r = rng(seed)
    shade = 0.955 + 0.035 * lowfreq(h, w, 5, seed) + 0.012 * (lowfreq(h, w, 23, seed + 1) - 0.5)
    fib = (r.random((h, w)).astype(np.float32) - 0.5) * 0.02
    wr = cv2.GaussianBlur(lowfreq(h, w, 11, seed + 2), (0, 0), w * 0.01); gy, gx = np.gradient(wr)
    wrinkle = 1 + np.tanh((gx - gy) * w * 0.05) * 0.035                                    # paste bubbles: soft lit ridges
    rgb = PAPER[None, None] * (shade * wrinkle + fib)[..., None]
    rgb *= np.array([1.0, 0.995, 0.985], np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    edge = (lowfreq(h, w, 60, seed + 3) - 0.5) * w * 0.012 + (r.random((h, w)) - 0.5) * 2.0
    a = np.clip((d - w * 0.004 - edge) / 2.0, 0, 1)
    if torn and r.random() < 0.6:   # one torn corner
        c = r.integers(0, 4); s = w * (0.06 + 0.08 * r.random())
        cx, cy = (0 if c in (0, 3) else w), (0 if c in (0, 1) else h)
        dd = np.abs(xx - cx) + np.abs(yy - cy) - s + (lowfreq(h, w, 80, seed + 4) - 0.5) * w * 0.03
        a *= np.clip(dd / 2.0, 0, 1)
    rgb *= (1 - 0.10 * np.clip(1 - d / (w * 0.012), 0, 1))[..., None]                # edges catch grime
    return rgb.astype(np.float32), a.astype(np.float32)

def xerox_ink(m, seed, k=1.0):
    r = rng(seed); h, w = m.shape
    m = cv2.GaussianBlur(m, (0, 0), 0.9)
    m = np.clip((m - 0.18) * 1.6, 0, 1)
    mott = 0.8 + 0.2 * lowfreq(h, w, 40, seed) + (r.random((h, w)).astype(np.float32) - 0.5) * 0.25
    m = m * np.clip(mott, 0, 1)
    return m * k

def build_flyer(fid, w_world, h_world, fn, seed, torn=True):
    path = os.path.join(CACHE, f"{fid}.png")
    if os.path.exists(path):
        a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if a is not None: return a
    w, h = int(w_world * TS), int(h_world * TS)
    d = Draw(w, h); fn(d)
    rgb, alpha = xerox_paper(w, h, seed, torn)
    r = rng(seed + 9)
    k = xerox_ink(np.asarray(d.L["K"], np.float32) / 255, seed)
    sp = (r.random((h // 3, w // 3)) > 0.9993).astype(np.float32); sp = cv2.GaussianBlur(cv2.resize(sp, (w, h), interpolation=cv2.INTER_NEAREST), (0, 0), 0.7)
    sx = int(r.integers(int(w * 0.1), int(w * 0.9))); xx_ = np.arange(w, dtype=np.float32)
    streak = (np.exp(-((xx_ - sx) / (w * 0.004)) ** 2) * 0.22)[None, :] * (0.3 + 0.7 * lowfreq(h, 1, 5, seed + 6)[:, :1])
    k = np.clip(k + sp * 0.85 + streak, 0, 1)
    rgb *= (1 - k[..., None] * (1 - INK_MUL["K"]))
    base = np.dstack([np.clip(rgb[..., ::-1], 0, 1) * 255, alpha * 255]).astype(np.uint8)
    for ink, (dx, dy) in (("R", (int(r.integers(-5, 6)), int(r.integers(-5, 6)))), ("O", (int(r.integers(-5, 6)), int(r.integers(-5, 6))))):
        m = np.asarray(d.L[ink], np.float32) / 255
        if m.max() <= 0: continue
        m = np.roll(np.roll(xerox_ink(m, seed + 7, 0.95), dy, 0), dx, 1)
        rgb *= (1 - m[..., None] * (1 - INK_MUL[ink]))
    out = np.dstack([np.clip(rgb[..., ::-1], 0, 1) * 255, alpha * 255]).astype(np.uint8)
    bp_ = path[:-4] + "_base.png"; tmp = bp_ + f".{os.getpid()}.png"; cv2.imwrite(tmp, base); os.replace(tmp, bp_)
    tmp = path + f".{os.getpid()}.png"; cv2.imwrite(tmp, out); os.replace(tmp, path)
    return out

_TEX = {}; _BASE = {}
def _mips(a):
    m = [a]                                                # uint8 BGRA: ~4x less memory than float (render workers share a 4 GB VM)
    while max(m[-1].shape[:2]) > 160: m.append(cv2.pyrDown(m[-1]))
    return m
def tex(f):
    if f["id"] not in _TEX:
        _TEX[f["id"]] = _mips(build_flyer(f["id"], f["w"], f["h"], f["fn"], f["seed"], f.get("torn", True)))
    return _TEX[f["id"]]
def tex_base(f):
    k = f["id"] + "_base"
    if k not in _BASE:
        tex(f); a = cv2.imread(os.path.join(CACHE, k + ".png"), cv2.IMREAD_UNCHANGED)
        if len(_BASE) >= 2: _BASE.pop(next(iter(_BASE)))
        _BASE[k] = _mips(a) if a is not None else tex(f)
    return _BASE[k]

# ================================================================= camera (world units: the wall is ~4.4 x 1.9)
class Cam:
    def __init__(self, cx, cy, vh, rot=0.0): self.cx, self.cy, self.vh, self.rot = cx, cy, vh, rot
    def M(self, W, H, sx=0.0, sy=0.0):
        s = H / self.vh; c, sn = math.cos(self.rot), math.sin(self.rot)
        return np.array([[s * c, -s * sn, W / 2 + sx - s * (c * self.cx - sn * self.cy)],
                         [s * sn, s * c, H / 2 + sy - s * (sn * self.cx + c * self.cy)]], np.float32)

def to_screen(M, x, y): return (M[0, 0] * x + M[0, 1] * y + M[0, 2], M[1, 0] * x + M[1, 1] * y + M[1, 2])

# ---------------------------------------------------------------- wall: cinder blocks, grime, old paste
_WALL = {}
def wall_tile():
    if "t" in _WALL: return _WALL["t"]
    n = 1024; u = 0.8 / n   # tile = 0.8 x 0.8 world units
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) * u
    bw, bh = 0.4, 0.2
    row = np.floor(yy / bh); off = (row % 2) * bw / 2
    mx = np.abs(((xx + off) % bw) - bw / 2); my = np.abs((yy % bh) - bh / 2)
    mortar = np.maximum(sstep_np(bw / 2 - 0.006, bw / 2 - 0.002, mx), sstep_np(bh / 2 - 0.006, bh / 2 - 0.002, my))
    def tiled(cells, seed):
        r = rng(seed); a = r.random((cells, cells)).astype(np.float32)
        a = np.tile(a, (3, 3)); a = cv2.resize(a, (n * 3, n * 3), interpolation=cv2.INTER_CUBIC)
        return a[n:2 * n, n:2 * n]
    g = 0.78 + 0.22 * tiled(6, 1) + 0.12 * (tiled(40, 2) - 0.5) + 0.10 * (rng(3).random((n, n)).astype(np.float32) - 0.5)
    drip = np.clip(tiled(12, 4)[:1] * 1.0, 0, 1) * np.linspace(1.0, 0.7, n)[:, None]
    g *= 0.92 + 0.08 * drip
    img = WALL[None, None] * g[..., None] * (1 - 0.45 * mortar)[..., None]
    # a few remnants of older posters: torn rectangles, grimy, glue-stained, faint print
    r = rng(5)
    for _ in range(4):
        cx, cy = r.uniform(80, n - 80), r.uniform(80, n - 80); rw, rh = r.uniform(60, 150), r.uniform(50, 130)
        q = []
        for (ux, uy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            q.append((cx + ux * rw * r.uniform(0.7, 1.0), cy + uy * rh * r.uniform(0.7, 1.0)))
        pts = []
        for a, b in zip(q, q[1:] + q[:1]):                       # ragged torn edges
            for k in np.linspace(0, 1, 9)[:-1]:
                pts.append((a[0] + (b[0] - a[0]) * k + r.normal(0, 4), a[1] + (b[1] - a[1]) * k + r.normal(0, 4)))
        m = np.zeros((n, n), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, cv2.LINE_AA)
        for j in range(int(rh / 14)):
            yl = int(cy - rh * 0.6 + j * 14)
            cv2.line(m, (int(cx - rw * 0.6), yl), (int(cx + rw * r.uniform(-0.2, 0.6)), yl), 0.55, 3)
        col = PAPER * r.uniform(0.22, 0.32)
        img = img * (1 - m[..., None] * 0.8) + col * m[..., None] * 0.8
    _WALL["t"] = (np.clip(img, 0, 1).astype(np.float32), u)
    return _WALL["t"]

def sstep_np(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)

def draw_wall(W, H, M):
    tile, u = wall_tile()
    A = np.vstack([M, [0, 0, 1]]) @ np.array([[u, 0, 0], [0, u, 0], [0, 0, 1]], np.float32)   # tile px -> screen
    return cv2.warpAffine(tile, A[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

def light(W, H, t, warm=0.0):
    """Street-light pool + vignette multiplier (screen space)."""
    k = (W, H)
    if k not in _WALL:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); m = min(W, H)
        X = (xx - W * 0.5) / m; Y = (yy - H * 0.18) / m
        _WALL[k] = (0.55 + 0.75 * np.exp(-(X ** 2 * 0.9 + Y ** 2 * 1.6)))[..., None].astype(np.float32)
    return _WALL[k]

# ---------------------------------------------------------------- pasting flyers
def slap(f, t):
    """0 before, 1 settled; returns (visible, scale, extra rotation, lift)."""
    x = t - f["t"]
    if x < -0.16: return None
    if x < 0: k = ease_out((x + 0.16) / 0.16); return (k, 1.22 - 0.22 * k, f.get("spin", 0.12) * (1 - k), 1 - k)
    return (1.0, 1.0 + 0.012 * math.exp(-x * 9), 0.0, 0.0)

def draw_flyer(img, f, M, t, W, H, dim=1.0):
    st = slap(f, t)
    if st is None: return
    op, sc, rot2, lift = st
    mips = tex(f); th, tw = mips[0].shape[:2]
    rot = f["rot"] + rot2; c, s = math.cos(rot), math.sin(rot)
    k = sc / TS
    # texture px -> world
    A = np.array([[k * c, -k * s, f["x"] - k * (c * tw / 2 - s * th / 2)],
                  [k * s, k * c, f["y"] - k * (s * tw / 2 + c * th / 2)]], np.float32)
    T = np.vstack([M, [0, 0, 1]]) @ np.vstack([A, [0, 0, 1]])
    scr = math.hypot(T[0, 0], T[1, 0])
    lvl = 0
    while lvl + 1 < len(mips) and scr * (2 ** (lvl + 1)) < 0.75: lvl += 1
    tx = mips[lvl]; T2 = T.copy(); T2[:2, :2] *= 2 ** lvl
    corners = [T2[:2] @ np.array([x, y, 1.0]) for x, y in ((0, 0), (tx.shape[1], 0), (0, tx.shape[0]), (tx.shape[1], tx.shape[0]))]
    xs = [p[0] for p in corners]; ys = [p[1] for p in corners]
    pad = int(40 * lift * min(W, H) / 1080) + 2
    x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad); x1, y1 = min(W, int(max(xs)) + pad + 1), min(H, int(max(ys)) + pad + 1)
    if x1 <= x0 or y1 <= y0: return
    T3 = T2[:2].copy(); T3[0, 2] -= x0; T3[1, 2] -= y0
    w = cv2.warpAffine(tx, T3, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT).astype(np.float32) * (1 / 255)
    a = w[..., 3:4] * op; rgb = w[..., 2::-1]
    age = t - f["t"]
    if f.get("brush") and -0.2 < age < 2.2:
        inv = cv2.invertAffineTransform(T3)
        yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0].astype(np.float32)
        u = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]) / tx.shape[1]; v = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]) / tx.shape[0]
        diag = (u + v) / 2
        rk = clamp((age - 0.62) / 0.75)                                    # red marker / stamps write on after the paste
        if rk < 1.0:
            wb = cv2.warpAffine(tex_base(f)[lvl], T3, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., 2::-1].astype(np.float32) * (1 / 255)
            mk = np.clip((rk * 1.3 - 0.1 - diag) / 0.05, 0, 1)[..., None]
            rgb = wb * (1 - mk) + rgb * mk
        bk = ease_io(clamp((age - 0.04) / 0.55)); front = lerp(-0.15, 1.15, bk)
        g = np.clip((front - diag) / 0.04, 0, 1) * 0.16 * math.exp(-max(0.0, age - 0.5) * 1.4)
        g *= 0.65 + 0.35 * np.sin(diag * 90 + v * 13) ** 2
        rgb = rgb + g[..., None] * np.array([0.9, 0.95, 1.0], np.float32)
    reg = img[y0:y1, x0:x1]
    # contact shadow (bigger while it's still in the air)
    sh = cv2.GaussianBlur(w[..., 3], (0, 0), 3 + 22 * lift)
    o = int(6 + 30 * lift)
    shd = np.zeros_like(sh); shd[o:, o:] = sh[:-o or None, :-o or None]
    reg *= (1 - (0.35 + 0.35 * lift) * shd[..., None] * op)
    wet = 1 - 0.12 * math.exp(-max(0, t - f["t"]) * 1.5)
    reg *= (1 - a); reg += a * rgb * wet * dim

# ================================================================= screen-space type
_SP = {}
def strip_sprite(text, font, size, fg, bg, pad=0.22, seed=0):
    """A torn paper strip with stenciled text (RGBA float, cached)."""
    k = (text, font, size, tuple(np.round(fg, 4)), tuple(np.round(bg, 4)), pad, seed)
    if k in _SP: return _SP[k].astype(np.float32) * (1 / 255)
    f = ImageFont.truetype(font, size); tw = int(f.getlength(text)); asc, desc = f.getmetrics()
    px, py = int(size * pad * 1.6), int(size * pad)
    w, h = tw + 2 * px, asc + desc + 2 * py - int(size * 0.12)
    im = Image.new("L", (w, h), 0); ImageDraw.Draw(im).text((px, py - int(size * 0.06)), text, font=f, fill=255)
    tmask = np.asarray(im, np.float32) / 255
    r = rng(seed + len(text))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    e1 = (lowfreq(1, w, max(4, w // 14), seed + 1)[0] - 0.5) * size * 0.12; e2 = (lowfreq(1, w, max(4, w // 11), seed + 2)[0] - 0.5) * size * 0.12
    l1 = (lowfreq(h, 1, 6, seed + 3)[:, 0] - 0.5) * size * 0.10; l2 = (lowfreq(h, 1, 6, seed + 4)[:, 0] - 0.5) * size * 0.10
    a = (np.clip((yy - 2 - e1[None, :] - size * 0.04) / 1.5, 0, 1) * np.clip((h - 3 - yy + e2[None, :] - size * 0.04) / 1.5, 0, 1)
         * np.clip((xx - 2 - l1[:, None] - size * 0.06) / 1.5, 0, 1) * np.clip((w - 3 - xx + l2[:, None] - size * 0.06) / 1.5, 0, 1))
    tex_ = 0.92 + 0.08 * lowfreq(h, w, 12, seed + 5)
    tm = xerox_ink(tmask, seed + 6)
    rgb = bg[None, None] * tex_[..., None] * (1 - tm[..., None]) + fg[None, None] * tm[..., None]
    out = np.dstack([rgb, a]).astype(np.float32)
    if len(_SP) > 120: _SP.pop(next(iter(_SP)))
    _SP[k] = (np.clip(out, 0, 1) * 255).astype(np.uint8)
    return out

def put(img, spr, cx, cy, op=1.0, rot=0.0, sc=1.0, shadow_op=0.5):
    if op <= 0.01: return
    h, w = spr.shape[:2]; H, W = img.shape[:2]
    c, s = math.cos(rot) * sc, math.sin(rot) * sc
    bw = int(abs(c) * w + abs(s) * h) + 24; bh = int(abs(s) * w + abs(c) * h) + 24
    M = np.array([[c, -s, bw / 2 - (c * w / 2 - s * h / 2)], [s, c, bh / 2 - (s * w / 2 + c * h / 2)]], np.float32)
    x0, y0 = int(cx - bw / 2), int(cy - bh / 2)
    wa = cv2.warpAffine(spr, M, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + bw), min(H, y0 + bh)
    if X1 <= X0 or Y1 <= Y0: return
    wa = wa[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]; reg = img[Y0:Y1, X0:X1]
    a = wa[..., 3:4] * op
    if shadow_op > 0:
        sh = cv2.GaussianBlur(wa[..., 3], (0, 0), 8 * sc + 2); o = int(10 * sc) + 1
        shd = np.zeros_like(sh); shd[o:, o:] = sh[:-o, :-o]; reg *= (1 - shadow_op * op * shd[..., None])
    reg *= (1 - a); reg += a * wa[..., :3]

def slam(t, t0, dur=None):
    """Stamp hit: (opacity, scale, jitter) for a word that lands at t0."""
    x = t - t0
    if x < -0.06: return None
    k = ease_out((x + 0.06) / 0.1)
    return (k, 1.0 + 0.45 * (1 - k) + 0.05 * math.exp(-max(0, x) * 10), math.exp(-max(0, x) * 14))

# ================================================================= the flyers
def header(d, s, inv=True):
    d.rect(0.0, 0.0, 1.0, 0.085, "K", fill=255)
    d.D["K"].text(d.P(0.05, 0.0425), s, font=d.F(STENCIL, 0.062), fill=0, anchor="lm")
    d.D["K"].text(d.P(0.95, 0.0425), "FILE NO. 2009", font=d.F(COUR, 0.032), fill=0, anchor="rm")

def star(d, cx, cy, r, ink="K", fill=True):
    pts = [d.P(cx + (r if i % 2 == 0 else r * 0.45) * math.cos(-1.5708 + i * 0.6283), cy + (r if i % 2 == 0 else r * 0.45) * math.sin(-1.5708 + i * 0.6283) * d.w / d.h) for i in range(10)]
    if fill: d.D[ink].polygon(pts, fill=255)
    else: d.D[ink].polygon(pts, outline=255, width=max(2, int(0.006 * d.w)))

def checkmark(d, x, y, s, ink="K", width=0.02):
    d.line([(x, y), (x + s * 0.35, y + s * 0.4 * d.w / d.h), (x + s, y - s * 0.55 * d.w / d.h)], ink, width)

def arrow(d, x0, y0, x1, y1, ink="R", width=0.012):
    d.line([(x0, y0), (x1, y1)], ink, width)
    a = math.atan2((y1 - y0) * d.h, (x1 - x0) * d.w); L = 0.04
    for da in (2.6, -2.6):
        d.line([(x1, y1), (x1 + L * math.cos(a + da), y1 + L * math.sin(a + da) * d.w / d.h)], ink, width)

def head(G, d, cx, cy, s, val=200, tilt=0.0):
    """Halftone-able head-and-shoulders silhouette (gray layer); cy = bottom of the shoulders."""
    w, h = d.w, d.h; k = w / h
    def P(x, y):
        xr, yr = x * math.cos(tilt) - y * math.sin(tilt) * 0.3, y
        return ((cx + xr * s) * w, (cy + yr * s * k) * h)
    sh = [P(-1.0, 0.0), P(-0.95, -0.42), P(-0.70, -0.62), P(-0.30, -0.74), P(-0.20, -0.95), P(0.20, -0.95), P(0.30, -0.74),
          P(0.70, -0.62), P(0.95, -0.42), P(1.0, 0.0)]
    G.polygon(sh, fill=val)
    hx, hy = P(0.0, -1.42)
    G.ellipse([hx - 0.36 * s * w, hy - 0.46 * s * w, hx + 0.36 * s * w, hy + 0.46 * s * w], fill=val)

def fl_notice(d):
    d.text("NOTICE", 0.5, 0.06, 0.13, STENCIL, "K", "ma")
    d.text("WE VALUE YOUR PRIVACY*", 0.5, 0.30, 0.046, TYPEW, "K", "ma")
    d.text("By existing online since 2009, you agree that\neverything you ever made may be used to train\nour models. Forever. For anything.",
           0.5, 0.41, 0.030, TYPEW, "K", "ma", spacing=0.45)
    d.D["K"].rounded_rectangle([d.P(0.28, 0.64), d.P(0.72, 0.80)], radius=int(0.02 * d.w), fill=255)
    d.D["K"].text(d.P(0.5, 0.72), "ACCEPT ALL", font=d.F(BLACK, 0.052), fill=0, anchor="mm")
    d.text("reject", 0.86, 0.86, 0.011, COUR, "K", "ma")
    d.text("*we don't", 0.05, 0.92, 0.020, COUR, "K", "la")

def fl_blog(d):
    header(d, "EXHIBIT A")
    d.text("~*~ my thoughts ~*~", 0.5, 0.13, 0.085, PLAY, "K", "ma")
    POSTED = "posted Tuesday, March 3, 2009 at 11:47 PM"
    d.text(POSTED, 0.5, 0.25, 0.031, COUR, "K", "ma")
    d.mark_circle(POSTED, 0.5, 0.25, 0.031, COUR, "ma", 0.25, 0, "2009", seed=3, pad=0.025)
    d.text("today i made pasta and\nthought about the moon.\nanyway here is my poem\nabout my router (below)", 0.08, 0.32, 0.052, TYPEW, "K", spacing=0.35)
    d.text("visitors:", 0.08, 0.66, 0.042, COUR, "K")
    for i, ch in enumerate("000417"):
        x = 0.32 + i * 0.075; d.rect(x, 0.645, x + 0.065, 0.715, "K", fill=255)
        d.D["K"].text(d.P(x + 0.0325, 0.68), ch, font=d.F(MONO, 0.05), fill=0, anchor="mm")
    d.text("comments (0)", 0.08, 0.76, 0.04, COUR, "K")
    d.stamp("SCRAPED", 0.58, 0.86, 0.11, rot=-11)

def fl_poem(d):
    header(d, "EXHIBIT B")
    d.text("ODE TO MY ROUTER", 0.5, 0.13, 0.075, PLAY, "K", "ma")
    d.text("o blinking light,\nyou never sleep.\nyou hold my wifi\nand secrets deep.", 0.14, 0.27, 0.066, TYPEW, "K", spacing=0.45)
    d.line([(0.14, 0.495), (0.80, 0.50)], "R", 0.008)
    d.text("awful", 0.70, 0.56, 0.075, MARKER, "R")
    arrow(d, 0.72, 0.58, 0.60, 0.51)
    d.text("(2011)", 0.14, 0.60, 0.04, COUR, "K")
    d.stamp("IN YOUR WEIGHTS", 0.5, 0.80, 0.085, rot=6)

def fl_selfie(d):
    header(d, "EXHIBIT C")
    G = d.G; clip = Image.new("L", (d.w, d.h), 0); CD = ImageDraw.Draw(clip)
    for i in range(3):
        y0 = 0.11 + i * 0.205
        d.rect(0.06, y0, 0.40, y0 + 0.19, "K", width=0.006)
        CD.rectangle([d.P(0.068, y0 + 0.006), d.P(0.392, y0 + 0.184)], fill=255)
        G.rectangle([d.P(0.065, y0 + 0.005), d.P(0.395, y0 + 0.185)], fill=45)
        head(G, d, 0.23 + (i - 1) * 0.02, y0 + 0.215, 0.13, 220, tilt=(i - 1) * 0.15)
    d.gray = Image.fromarray((np.asarray(d.gray, np.float32) * (np.asarray(clip, np.float32) / 255)).astype(np.uint8)); d.G = ImageDraw.Draw(d.gray)
    d.halftone("K", cell=0.013)
    d.text("my selfies", 0.07, 0.745, 0.05, MARKER, "R")
    for i in range(5): star(d, 0.50 + i * 0.085, 0.17, 0.035, "K", fill=i < 2)
    d.text("“soup was cold.\nstaff lovely.”", 0.47, 0.22, 0.05, TYPEW, "K", spacing=0.3)
    d.text("my reviews", 0.50, 0.36, 0.04, MARKER, "R")
    d.ellipse(0.47, 0.46, 0.95, 0.70, "K", width=0.008)
    d.ellipse(0.69, 0.475, 0.73, 0.505, "K", width=0.006)
    d.text("SIR PANCAKE\nMcWHISKERS\nTHE THIRD", 0.71, 0.585, 0.048, ANTON, "K", "mm", spacing=0.1)
    d.scribble_circle(0.71, 0.58, 0.28, 0.15, "R", 0.011, seed=5)
    d.text("my cat's FULL name", 0.47, 0.76, 0.05, MARKER, "R")

def fl_job(d):
    header(d, "EXHIBIT D")
    d.text("HELP WANTED", 0.5, 0.12, 0.11, ANTON, "K", "ma")
    d.line([(0.12, 0.20), (0.88, 0.17)], "R", 0.018)
    d.stamp("POSITION FILLED", 0.5, 0.33, 0.07, rot=-5)
    for i, (who, ink) in enumerate((("ME:", "K"), ("CHATBOT:", "K"))):
        x = 0.06 + i * 0.47
        d.rect(x, 0.43, x + 0.41, 0.72, "K", width=0.006)
        d.text(who, x + 0.03, 0.45, 0.045, STENCIL, ink)
        d.text("Per my last\nemail...", x + 0.03, 0.53, 0.05, TYPEW, "K", spacing=0.3)
    d.text("SPOT THE DIFFERENCE", 0.5, 0.77, 0.06, STENCIL, "K", "ma")
    d.text("(there are none)", 0.5, 0.86, 0.05, MARKER, "R", "ma")

LOREM = ("the user agrees that the company may collect store process remix sell license and otherwise enjoy all content "
         "the user has ever produced including but not limited to posts poems photos reviews pets names moods and vibes ").split()
def tiny_text(d, x0, y0, x1, y1, size, seed, ink="K", skip=None):
    r = rng(seed); f = d.F(COUR, size); y = y0; n = 0
    while y < y1:
        words = []; L = 0
        while True:
            w = LOREM[int(r.integers(0, len(LOREM)))]; ww = f.getlength(w + " ") / d.w
            if L + ww > x1 - x0: break
            words.append(w); L += ww
        if not (skip and skip[0] <= y <= skip[1]): d.D[ink].text(d.P(x0, y), " ".join(words), font=f, fill=200)
        y += size * 1.35 * d.w / d.h; n += 1

def fl_terms(d):
    header(d, "EXHIBIT E")
    d.text("TERMS OF SERVICE", 0.5, 0.115, 0.075, ANTON, "K", "ma")
    d.text("version 62.0 · updated just now", 0.5, 0.215, 0.03, COUR, "K", "ma")
    tiny_text(d, 0.07, 0.26, 0.93, 0.93, 0.0135, 7, skip=(0.535, 0.56))
    d.text("62. your soul is a training set (see below)", 0.07, 0.537, 0.0135, COUR, "K")
    d.scribble_circle(0.33, 0.545, 0.29, 0.03, "R", 0.010, seed=8)
    d.text("clause 62", 0.62, 0.60, 0.07, MARKER, "R")
    arrow(d, 0.66, 0.62, 0.55, 0.565)

def fl_soul(d):
    header(d, "EXHIBIT F")
    d.text("62.", 0.08, 0.12, 0.13, STENCIL, "K")
    SOUL = "User grants Company a\nperpetual, irrevocable\nlicense to their soul,\nfor training purposes,\nand whatever else\nwe want."
    d.text(SOUL, 0.08, 0.29, 0.066, TYPEW, "K", spacing=0.32)
    d.mark_circle(SOUL, 0.08, 0.29, 0.066, TYPEW, "la", 0.32, 2, "soul", seed=4, pad=0.02)
    d.mark_under(SOUL, 0.08, 0.29, 0.066, TYPEW, "la", 0.32, 4, "and whatever else", seed=5)
    d.mark_under(SOUL, 0.08, 0.29, 0.066, TYPEW, "la", 0.32, 5, "we want", seed=6)
    d.text("(size-two font)", 0.5, 0.88, 0.045, MARKER, "R", "ma")

def fl_accept(d):
    header(d, "EXHIBIT G")
    d.text("Please review and accept\nthe updated terms.", 0.08, 0.13, 0.05, TYPEW, "K", spacing=0.3)
    d.rect(0.08, 0.32, 0.17, 0.38, "K", width=0.010)
    d.text("I agree to the Terms", 0.21, 0.322, 0.055, TYPEW, "K")
    d.D["K"].rounded_rectangle([d.P(0.08, 0.46), d.P(0.48, 0.55)], radius=int(0.02 * d.w), outline=255, width=int(0.008 * d.w))
    d.text("DECLINE", 0.28, 0.505, 0.05, BLACK, "K", "mm")
    curs = [(0.40, 0.52), (0.40, 0.62), (0.425, 0.595), (0.445, 0.64), (0.46, 0.633), (0.44, 0.588), (0.475, 0.585)]
    d.D["K"].polygon([d.P(*p) for p in curs], fill=255)
    d.text("I never said yes.", 0.08, 0.70, 0.05, MARKER, "R")
    d.stamp("ACCEPTED", 0.58, 0.40, 0.11, rot=-16)

def fl_vector(d):
    header(d, "EXHIBIT H")
    d.text("YOU =", 0.08, 0.12, 0.12, ANTON, "K")
    d.text("[ 0.12, -0.87,  0.33,\n  0.09, -0.41,  0.77,\n -0.26,  0.58, -0.03,\n  ... 4,087 more ]", 0.08, 0.33, 0.046, MONO, "K", spacing=0.35)
    head(d.G, d, 0.76, 0.36, 0.16, 175); d.halftone("K", cell=0.012)
    d.text("personality.npy", 0.08, 0.66, 0.05, COUR, "K")
    d.text("I guess?", 0.55, 0.76, 0.08, MARKER, "R")

# ---------------------------------------------------------------- verse 2: the memo
def fl_slide(d):
    d.text("Q3 ALL-HANDS", 0.5, 0.05, 0.05, STENCIL, "K", "ma")
    d.text("EFFICIENCY\nGAINS +40%", 0.5, 0.13, 0.10, ANTON, "K", "ma", spacing=0.05)
    for i, hh in enumerate((0.10, 0.16, 0.24, 0.36)):
        x = 0.16 + i * 0.18; d.rect(x, 0.82 - hh, x + 0.12, 0.82, "K", fill=255)
    d.line([(0.10, 0.82), (0.90, 0.82)], "K", 0.008)
    arrow(d, 0.16, 0.66, 0.86, 0.40, "K", 0.010)
    d.text("FOR WHO?", 0.50, 0.50, 0.12, MARKER, "R", "mm")

def fl_buying(d):
    d.text("WHO'S\nBUYING?", 0.5, 0.06, 0.15, ANTON, "K", "ma", spacing=0.02)
    d.text("CUSTOMERS ........ 0\nPAYCHECKS ........ 0\nREVENUE ....... ???", 0.08, 0.50, 0.052, COUR, "K", spacing=0.5)
    d.text("nobody gets paid", 0.5, 0.82, 0.07, MARKER, "R", "ma")

def fl_tally(d):
    d.text("10,000", 0.5, 0.05, 0.19, ANTON, "K", "ma")
    d.text("roles “reallocated”", 0.5, 0.31, 0.06, TYPEW, "K", "ma")
    r = rng(12)
    for gy in range(5):
        for gx in range(5):
            x = 0.08 + gx * 0.175; y = 0.43 + gy * 0.095
            for k in range(4): d.line([(x + k * 0.03, y + r.uniform(-0.005, 0.005)), (x + k * 0.03 + 0.005, y + 0.07)], "R", 0.008)
            d.line([(x - 0.01, y + 0.06), (x + 0.11, y + 0.01)], "R", 0.008)
    d.text("quarterly slide 14 of 60", 0.5, 0.93, 0.035, COUR, "K", "ma")

def fl_bunker(d):
    d.text("FOR SALE", 0.5, 0.05, 0.12, STENCIL, "K", "ma")
    d.text("LUXURY BUNKER", 0.5, 0.20, 0.075, ANTON, "K", "ma")
    G = d.G
    G.pieslice([d.P(0.04, 0.34), d.P(0.56, 0.62)], 180, 360, fill=150)                             # the bunker mound
    G.rectangle([d.P(0.04, 0.475), d.P(0.56, 0.49)], fill=120)
    G.rectangle([d.P(0.24, 0.40), d.P(0.36, 0.48)], fill=235)                                      # blast door
    G.rectangle([d.P(0.44, 0.33), d.P(0.465, 0.40)], fill=200)                                     # air vent
    G.polygon([d.P(0.46, 0.66), d.P(0.97, 0.66), d.P(0.90, 0.72), d.P(0.52, 0.72)], fill=215)       # yacht hull
    G.polygon([d.P(0.58, 0.66), d.P(0.62, 0.60), d.P(0.84, 0.60), d.P(0.88, 0.66)], fill=150)       # cabin
    G.polygon([d.P(0.66, 0.60), d.P(0.69, 0.56), d.P(0.79, 0.56), d.P(0.80, 0.60)], fill=120)
    G.rectangle([d.P(0.0, 0.72), d.P(1.0, 0.76)], fill=70)
    d.halftone("K", cell=0.011)
    d.line([(0.30, 0.50), (0.30, 0.56)], "K", 0.004)
    d.text("4 BR · air filtration · yacht dock\n0 employees", 0.5, 0.79, 0.04, COUR, "K", "ma", spacing=0.35)
    d.text("nice yacht.", 0.62, 0.43, 0.07, MARKER, "R")

def fl_aifirst(d):
    d.text("MEMO", 0.08, 0.05, 0.10, STENCIL, "K")
    d.text("FROM: the CEO\nRE:   we are now", 0.08, 0.20, 0.045, COUR, "K", spacing=0.3)
    d.text("AI-FIRST!!!", 0.5, 0.33, 0.12, ANTON, "K", "ma")
    d.line([(0.08, 0.36), (0.92, 0.46)], "R", 0.016); d.line([(0.08, 0.46), (0.92, 0.36)], "R", 0.016)
    d.rect(0.08, 0.56, 0.92, 0.74, "K", fill=255)
    d.D["K"].text(d.P(0.12, 0.65), "pritn('helo wrld'", font=d.F(MONO, 0.055), fill=0, anchor="lm")
    d.scribble_circle(0.25, 0.65, 0.15, 0.06, "R", 0.010, seed=21)
    d.text("can't code", 0.5, 0.80, 0.08, MARKER, "R", "ma")

def bug(d, cx, cy, s, ink="K"):
    d.ellipse(cx - s, cy - s * 1.3 * d.w / d.h, cx + s, cy + s * 1.3 * d.w / d.h, ink, fill=255)
    d.ellipse(cx - s * 0.55, cy - s * 1.9 * d.w / d.h, cx + s * 0.55, cy - s * 1.05 * d.w / d.h, ink, fill=255)
    for k in (-1, 0, 1):
        yy = cy + k * s * 0.7 * d.w / d.h
        d.line([(cx - s * 0.9, yy), (cx - s * 1.7, yy + k * s * 0.4 * d.w / d.h)], ink, 0.007)
        d.line([(cx + s * 0.9, yy), (cx + s * 1.7, yy + k * s * 0.4 * d.w / d.h)], ink, 0.007)

def fl_bugs(d):
    d.text("VIBE-SHIPPED", 0.5, 0.05, 0.10, STENCIL, "K", "ma")
    d.line([(0.42, 0.20), (0.05, 0.95)], "K", 0.010); d.line([(0.58, 0.20), (0.95, 0.95)], "K", 0.010)
    for i in range(6): d.line([(0.5, 0.22 + i * 0.13), (0.5, 0.27 + i * 0.13)], "K", 0.010)
    for i, (x, y, s) in enumerate(((0.47, 0.30, 0.03), (0.56, 0.42, 0.04), (0.40, 0.56, 0.05), (0.62, 0.72, 0.06), (0.36, 0.86, 0.07))):
        bug(d, x, y, s)
        checkmark(d, x + s * 1.9, y - 0.01, 0.06, "R", 0.012)
    d.text("straight to prod", 0.68, 0.20, 0.045, MARKER, "R")

def fl_coupon(d):
    d.rect(0.05, 0.05, 0.95, 0.95, "K", width=0.008)
    d.text("THE FUTURE™", 0.5, 0.14, 0.12, ANTON, "K", "ma")
    d.text("valid for shareholders only", 0.5, 0.33, 0.045, TYPEW, "K", "ma")
    for i in range(18): d.line([(0.07 + i * 0.05, 0.55), (0.095 + i * 0.05, 0.55)], "K", 0.008)
    d.ellipse(0.06, 0.505, 0.10, 0.535, "K", width=0.007); d.ellipse(0.06, 0.565, 0.10, 0.595, "K", width=0.007)
    d.line([(0.095, 0.53), (0.17, 0.555)], "K", 0.007); d.line([(0.095, 0.57), (0.17, 0.545)], "K", 0.007)
    d.text("CUT ME IN", 0.5, 0.70, 0.12, MARKER, "R", "ma")

def fl_invoice(d):
    d.text("INVOICE #2009", 0.08, 0.05, 0.085, STENCIL, "K")
    d.text("BILL TO:  The Machine\nFOR:      one human's data,\n          2009 – now", 0.08, 0.20, 0.045, COUR, "K", spacing=0.35)
    d.line([(0.08, 0.43), (0.92, 0.43)], "K", 0.006)
    d.text("blog, poems, selfies ...  $0.00\nreviews, cat's name ....  $0.00\nwhole personality ......  $0.00", 0.08, 0.46, 0.04, COUR, "K", spacing=0.5)
    d.line([(0.08, 0.66), (0.92, 0.66)], "K", 0.006)
    d.text("ROYALTY PAID:  $0.00", 0.08, 0.69, 0.06, ANTON, "K")
    d.stamp("UNPAID", 0.60, 0.86, 0.12, rot=-9)

# ---------------------------------------------------------------- protest posters (choruses, final)
def poster_word(word, size=0.24, inv=False, ink="R", font=STENCIL, sub=None):
    def fn(d):
        if inv:
            d.rect(0.0, 0.0, 1.0, 1.0, ink, fill=255)
            d.D[ink].multiline_text(d.P(0.5, 0.47 if sub else 0.5), word, font=d.F(font, size), fill=0, anchor="mm", align="center", spacing=int(size * d.w * 0.05))
        else:
            d.D[ink].multiline_text(d.P(0.5, 0.47 if sub else 0.5), word, font=d.F(font, size), fill=255, anchor="mm", align="center", spacing=int(size * d.w * 0.05))
        if sub: d.text(sub, 0.5, 0.86, 0.075, MARKER if not inv else STENCIL, "K", "ma")
    return fn

def fist_shape(G, d, cx, cy, s, val=255, ink_draw=None, bg=0):
    """Raised fist, knuckles to camera (relative coords): forearm, curled fingers, thumb across, crease lines."""
    dr = ink_draw or G; w, h = d.w, d.h; k = w / h
    def P(x, y): return ((cx + x * s) * w, (cy + y * s * k) * h)
    rad = lambda r: max(2, int(r * s * w))
    dr.polygon([P(-0.30, 0.10), P(0.32, 0.10), P(0.27, 1.25), P(-0.25, 1.25)], fill=val)                     # forearm
    dr.rounded_rectangle([P(-0.40, -0.30), P(0.42, 0.22)], radius=rad(0.14), fill=val)                         # back of the hand
    tops = (-0.66, -0.72, -0.69, -0.58)
    for i, ty in enumerate(tops):                                                                                # four curled fingers
        x = -0.42 + i * 0.205
        dr.rounded_rectangle([P(x, ty), P(x + 0.215, -0.08)], radius=rad(0.10), fill=val)
    for i in range(1, 4):                                                                                        # gaps between fingers
        x = -0.42 + i * 0.205
        dr.line([P(x, max(tops[i - 1], tops[i]) + 0.10), P(x, -0.22)], fill=bg, width=rad(0.022))
    for i in range(4):                                                                                           # knuckle creases
        x = -0.42 + i * 0.205
        dr.arc([P(x + 0.04, tops[i] + 0.10), P(x + 0.175, tops[i] + 0.26)], 200, 340, fill=bg, width=rad(0.016))
    dr.rounded_rectangle([P(-0.52, -0.30), P(0.10, -0.06)], radius=rad(0.12), fill=val)                       # thumb across the fingers
    dr.line([P(-0.40, -0.30), P(0.08, -0.31)], fill=bg, width=rad(0.022))
    dr.line([P(0.10, -0.24), P(0.10, -0.12)], fill=bg, width=rad(0.016))

def fl_fist(d):
    d.rect(0.0, 0.0, 1.0, 1.0, "R", fill=255)
    fist_shape(None, d, 0.5, 0.40, 0.55, 0, ink_draw=d.D["R"], bg=255)
    d.text("NOT YOUR\nTRAINING DATA", 0.5, 0.80, 0.085, STENCIL, "K", "ma", spacing=0.05)

def fl_gpu(d):
    d.text("GPUs", 0.5, 0.05, 0.16, STENCIL, "K", "ma")
    d.rect(0.12, 0.50, 0.88, 0.74, "K", fill=255)
    for i in range(3): d.D["K"].ellipse([d.P(0.20 + i * 0.22, 0.54), d.P(0.36 + i * 0.22, 0.70)], fill=0)
    for i in range(7): d.rect(0.16 + i * 0.1, 0.74, 0.21 + i * 0.1, 0.78, "K", fill=255)
    r = rng(4)
    def flame(ink, x, base, hh, ww, lean):
        pts = []
        for a in np.linspace(0, 1, 18):                     # teardrop with a flicked, leaning tip
            y = base - hh * a; half = ww * math.sin(math.pi * min(1.0, a * 1.05)) ** 0.7 * (1 - a) ** 0.35
            pts.append((x - half + lean * a * a * ww, y))
        for a in np.linspace(1, 0, 18):
            y = base - hh * a; half = ww * math.sin(math.pi * min(1.0, a * 1.05)) ** 0.7 * (1 - a) ** 0.35
            pts.append((x + half + lean * a * a * ww, y))
        d.D[ink].polygon([d.P(px, py) for px, py in pts], fill=255)
    for i in range(7):
        x = 0.17 + i * 0.11; hh = r.uniform(0.17, 0.30); lean = r.uniform(-0.8, 0.8)
        flame("O", x, 0.51, hh, 0.07, lean); flame("R", x + 0.005, 0.51, hh * 0.55, 0.035, lean)
    d.text("BURNING", 0.5, 0.82, 0.12, STENCIL, "R", "ma")

def fl_chart(d):
    d.text("MODEL PERFORMANCE vs. YOUR LIFE", 0.5, 0.04, 0.042, STENCIL, "K", "ma")
    d.line([(0.10, 0.14), (0.10, 0.86), (0.94, 0.86)], "K", 0.006)
    for i in range(1, 5): d.line([(0.10, 0.86 - i * 0.17), (0.94, 0.86 - i * 0.17)], "K", 0.0015)
    for i, q in enumerate(("Q1", "Q2", "Q3", "Q4")): d.text(q, 0.20 + i * 0.21, 0.88, 0.022, COUR, "K", "ma")
    d.text("source: trust me", 0.94, 0.95, 0.018, COUR, "K", "ra")

# ================================================================= layout: what gets pasted where, and when
import hashlib, inspect
_SRC = open(os.path.abspath(__file__)).read(); KIT_HASH = hashlib.md5(_SRC[:_SRC.index("# " + "=" * 65 + " layout")].encode()).hexdigest()[:6]
FLY = []
def fly(name, t, x, y, w, h, rot, fn, seed, kind="flyer", key="", brush=True, torn=True):
    src = key or inspect.getsource(fn)
    fid = name + "_" + hashlib.md5((KIT_HASH + src + f"{w:.3f}{h:.3f}{seed}{torn}").encode()).hexdigest()[:8]
    f = dict(id=fid, name=name, t=t, x=x, y=y, w=w, h=h, rot=rot, fn=fn, seed=seed, kind=kind, brush=brush, torn=torn)
    FLY.append(f); return f

T_NOTICE = float(DOWN[np.argmin(abs(DOWN - 20.9))])
NOTICE = fly("notice", T_NOTICE, -1.0, 0.02, 0.86, 0.62, 0.0, fl_notice, 101, torn=False)

V1FN = [fl_blog, fl_poem, fl_selfie, fl_job, fl_terms, fl_soul, fl_accept, fl_vector]
V1POS = [(-2.05, -0.40, -0.040), (-1.86, 0.43, 0.035), (-1.46, -0.37, 0.022), (-1.27, 0.45, -0.030),
         (-0.88, -0.41, -0.018), (-0.70, 0.41, 0.040), (-0.31, -0.38, 0.028), (-0.12, 0.44, -0.034)]
V2FN = [fl_slide, fl_buying, fl_tally, fl_bunker, fl_aifirst, fl_bugs, fl_coupon, fl_invoice]
V2POS = [(0.30, -0.40, 0.030), (0.49, 0.43, -0.035), (0.89, -0.37, -0.020), (1.08, 0.45, 0.030),
         (1.47, -0.41, 0.020), (1.66, 0.41, -0.040), (2.05, -0.38, -0.028), (2.24, 0.44, 0.034)]
VERSE = []
for i, (fn, (x, y, r)) in enumerate(zip(V1FN, V1POS)):
    VERSE.append(fly(fn.__name__[3:], LINES[2 + i]["s"] - 0.06, x, y, 0.56 if fn is fl_selfie else 0.52, 0.72 if fn is fl_selfie else 0.70, r, fn, 200 + i))
for i, (fn, (x, y, r)) in enumerate(zip(V2FN, V2POS)):
    VERSE.append(fly(fn.__name__[3:], LINES[16 + i]["s"] - 0.06, x, y, 0.52, 0.70, r, fn, 300 + i))

def poster(name, t, x, y, rot, design, seed, w=0.36, h=0.48):
    if design == "fist": fn, key = fl_fist, ""
    elif design == "gpu": fn, key = fl_gpu, ""
    else:
        word, inv, ink, font, size, sub = design
        fn = poster_word(word, size, inv, ink, font, sub); key = repr(design)
    return fly(name, t, x, y, w, h, rot, fn, seed, kind="poster", key=key, brush=False)

PW = {"optout": ("OPT\nOUT", True, "R", STENCIL, 0.30, None), "no": ("NO", False, "K", STENCIL, 0.52, "means no"),
      "saidno": ("I SAID\nNO", False, "R", STENCIL, 0.24, None), "payme": ("PAY\nME", True, "K", ANTON, 0.36, None),
      "vector": ("NOT A\nVECTOR", False, "K", ANTON, 0.21, None), "unplug": ("UN\nPLUG", True, "R", ANTON, 0.32, None),
      "human": ("HUMAN\nMADE", False, "K", STENCIL, 0.20, "no AI was asked"), "stop": ("STOP\nLEARN\nING", True, "K", STENCIL, 0.19, None),
      "optout2": ("OPT\nOUT", True, "K", STENCIL, 0.30, None), "mydata": ("MY\nDATA", False, "R", ANTON, 0.32, None),
      "nomeans": ("NO\nMEANS\nNO", True, "R", STENCIL, 0.20, None), "rent": ("RENT\nIS DUE", False, "R", ANTON, 0.22, None)}
def pw(k): return PW[k]
CH1P = [(LINES[10]["s"], -1.70, -0.01, -0.10, pw("optout")), (LINES[11]["s"], -1.07, 0.03, 0.07, "fist"),
        (W_(11, 5), -0.50, -0.02, -0.06, "gpu"), (LINES[13]["s"], -2.30, 0.05, 0.09, pw("saidno")),
        (LINES[14]["s"], -1.62, -0.78, -0.05, pw("no")), (LINES[15]["s"], -0.95, 0.80, 0.06, pw("stop"))]
CH2P = [(LINES[24]["s"], 0.70, 0.01, 0.08, pw("optout2")), (LINES[25]["s"], 1.27, -0.02, -0.07, "fist"),
        (W_(25, 5), 1.86, 0.03, 0.05, "gpu"), (LINES[27]["s"], 2.45, -0.04, -0.08, pw("payme"))]
POSTERS = []
for i, (t, x, y, r, d) in enumerate(CH1P + CH2P): POSTERS.append(poster(f"p{i}", t - 0.04, x, y, r, d, 400 + i))
CHART = fly("chart", float(DOWN[np.argmin(abs(DOWN - 101.5))]), 0.02, 0.0, 1.30, 0.92, -0.012, fl_chart, 500, torn=False, brush=False)
FRENZY_T = [b for b in BEATS if 115.95 < b < 120.9]
FRENZY = [("vector", -1.95, 0.80), ("human", 1.40, -0.80), ("mydata", -0.62, -0.78), ("unplug", 0.95, 0.80),
          ("nomeans", -2.35, -0.70), ("rent", 2.30, 0.82), ("optout", 0.10, 0.74), ("payme", -1.25, -0.80), ("no", 1.85, -0.78)]
for i, (t, (k, x, y)) in enumerate(zip(FRENZY_T, FRENZY)):
    POSTERS.append(poster(f"f{i}", t - 0.03, x, y, (-1) ** i * 0.07, pw(k), 600 + i))
FINAL_T = [d for d in DOWN if 121.0 < d < 137.0]
FINALP = [(-0.55, 0.55, "fist"), (0.62, -0.58, "gpu"), (-1.50, 0.00, pw("saidno")), (1.55, 0.02, pw("optout")),
          (-0.05, -0.62, pw("stop")), (2.40, -0.66, pw("vector")), (-2.40, 0.72, pw("payme"))]
for i, (t, (x, y, d)) in enumerate(zip(FINAL_T, FINALP)):
    POSTERS.append(poster(f"z{i}", t - 0.03, x, y, (-1) ** (i + 1) * 0.08, d, 700 + i))
ALL = sorted(FLY, key=lambda f: f["t"])

def prebuild():
    for f in ALL: tex(f)

# ================================================================= camera shots
def frame_flyer(f, vert):
    if not vert:
        vh = max(f["h"] * 1.42, f["w"] * 1.30 / (16 / 9)); return (f["x"], f["y"] + 0.065 * vh, vh)
    vh = max(f["h"] / 0.57, f["w"] / (0.82 * 0.5625)); return (f["x"], f["y"] + 0.125 * vh, vh)

def notice_pt(u, v):
    f = NOTICE; return (f["x"] + (u - 0.5) * f["w"], f["y"] + (v - 0.5) * f["h"])

T_SPRAY0 = float(DOWN[np.argmin(abs(DOWN - 140.4))]); T_SPRAY1 = 151.7
SHOTS = []   # (arrive, move, (cx, cy, vh) 16:9, (cx, cy, vh) 9:16, drift per s)
def shot(t, move, a, b, drift=0.012): SHOTS.append((t, move, a, b, drift))
shot(0.0, 0.0, (0.0, -0.05, 1.50), (0.0, -0.12, 2.15), 0.010)
shot(T_NOTICE - 0.05, 0.40, frame_flyer(NOTICE, False), frame_flyer(NOTICE, True), 0.012)
rx, ry = notice_pt(0.875, 0.865)
shot(23.36, 0.70, (rx - 0.11, ry + 0.015, 0.36), (rx - 0.06, ry + 0.035, 0.70), 0.03)
shot(25.70, 0.20, frame_flyer(NOTICE, False), frame_flyer(NOTICE, True), 0.012)
for f in VERSE: shot(f["t"] - 0.08, 0.40, frame_flyer(f, False), frame_flyer(f, True))
shot(LINES[10]["s"] - 0.02, 0.32, (-1.12, 0.0, 1.78), (-1.15, 0.05, 2.75), 0.008)
shot(LINES[24]["s"] - 0.02, 0.32, (1.18, 0.0, 1.78), (1.25, 0.05, 2.75), 0.008)
shot(CHART["t"] - 0.08, 0.35, (CHART["x"], CHART["y"] - 0.10 * 1.55, 1.55), (CHART["x"], CHART["y"] - 0.08 * 2.51, 2.51), 0.006)
shot(115.9, 1.10, (0.05, 0.0, 2.22), (0.0, 0.0, 3.10), 0.004)
shot(121.0, 0.30, (0.0, 0.0, 2.32), (-1.55, 0.02, 2.70), 0.0)
shot(T_UNSUB - 0.05, 0.25, (0.0, 0.0, 2.36), (0.0, 0.0, 3.30), 0.006)
SHOTS.sort(key=lambda s: s[0])

# spray-painted OPT OUT (outro): block-cap stroke paths in a 0..1 letter box
def _ell(n=28): return [(0.5 + 0.44 * math.cos(a), 0.5 + 0.5 * math.sin(a)) for a in np.linspace(-1.5708, 4.7124, n)]
GLYPH = {"O": [_ell()], "P": [[(0.16, 1.0), (0.16, 0.0)], [(0.16, 0.0), (0.62, 0.02), (0.84, 0.22), (0.66, 0.46), (0.16, 0.48)]],
         "T": [[(0.02, 0.02), (0.98, 0.02)], [(0.5, 0.02), (0.5, 1.0)]],
         "U": [[(0.12, 0.0), (0.12, 0.70), (0.30, 0.96), (0.70, 0.96), (0.88, 0.70), (0.88, 0.0)]]}
SPRAY = []   # per letter: (t0, t1, [strokes in world coords], center x)
def _build_spray():
    LW, LH, gap, sp = 0.60, 0.92, 0.10, 0.34
    word = "OPT OUT"; x = -(6 * LW + 4 * gap + sp) / 2; y0 = -LH / 2 - 0.02
    letters = []
    for ch in word:
        if ch == " ": x += sp - gap; continue
        strokes = [[(x + u * LW, y0 + v * LH) for u, v in st] for st in GLYPH[ch]]
        letters.append((strokes, x + LW / 2)); x += LW + gap
    n = len(letters); dt = (T_SPRAY1 - T_SPRAY0) / n
    for i, (st, cx) in enumerate(letters): SPRAY.append((T_SPRAY0 + i * dt + 0.12, T_SPRAY0 + (i + 1) * dt - 0.10, st, cx))
_build_spray()

def spray_head(t):
    """(world x, y) of the nozzle and the letter center the camera follows."""
    for t0, t1, st, cx in SPRAY:
        if t < t1 + 0.1:
            k = clamp((t - t0) / (t1 - t0)); pts, L = _cut(st, k)
            hx, hy = (pts[-1][-1] if pts and pts[-1] else st[0][0])
            return hx, hy, cx
    t0, t1, st, cx = SPRAY[-1]; return st[-1][-1][0], st[-1][-1][1], cx

def letter_x(t):
    """Camera x during the spray: holds on the letter being painted, eases to the next one just before it starts."""
    xs = [cx for _, _, _, cx in SPRAY]; x = xs[0]
    for i, (t0, t1, st, cx) in enumerate(SPRAY):
        if i == 0: continue
        k = ease_io(clamp((t - (t0 - 0.45)) / 0.45)); x = lerp(x, cx, k)
    return x

def _cut(strokes, k):
    lens = [sum(math.dist(a, b) for a, b in zip(s, s[1:])) for s in strokes]; tot = sum(lens); want = k * tot; out = []
    for s, L in zip(strokes, lens):
        if want <= 0: break
        if want >= L: out.append(s); want -= L; continue
        acc = 0; cur = [s[0]]
        for a, b in zip(s, s[1:]):
            d = math.dist(a, b)
            if acc + d >= want:
                q = (want - acc) / max(d, 1e-9); cur.append((a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q)); break
            cur.append(b); acc += d
        out.append(cur); want = 0
    return out, tot

def _state(i, t):
    tA, mv, a, b, dr = SHOTS[i]; return tA, a, b, dr

def cam_at(t, vert):
    if T_SPRAY0 - 0.3 <= t < T_UNSUB - 0.3:   # tracking shot: glide from letter to letter as it's painted
        x = letter_x(t)
        k = sstep(T_SPRAY0 - 0.3, T_SPRAY0 + 0.6, t)
        base = (0.0, 0.0, 2.32) if not vert else (-1.55 + 3.1 * clamp((t - 121.0) / 19.0), 0.02, 2.70)
        tgt = (x, -0.02, 1.40) if not vert else (x, 0.06, 1.55)
        return Cam(lerp(base[0], tgt[0], ease_io(k)), lerp(base[1], tgt[1], ease_io(k)), math.exp(lerp(math.log(base[2]), math.log(tgt[2]), ease_io(k))))
    if T_UNSUB - 0.3 <= t < T_UNSUB + 0.05:
        cx = letter_x(T_UNSUB - 0.3); k = ease_io((t - T_UNSUB + 0.3) / 0.35)
        a = (cx, -0.02, 1.40) if not vert else (cx, 0.06, 1.55); b = (0.0, 0.0, 2.36) if not vert else (0.0, 0.0, 3.30)
        return Cam(lerp(a[0], b[0], k), lerp(a[1], b[1], k), math.exp(lerp(math.log(a[2]), math.log(b[2]), k)))
    j = 0
    for i, s in enumerate(SHOTS):
        if s[0] - s[1] <= t: j = i
    def at(i, tt):
        tA, mv, a, b, dr = SHOTS[i]; v = b if vert else a
        cx, cy, vh = v
        if vert and i == next(k for k, s in enumerate(SHOTS) if s[0] == 121.0): cx = -1.55 + 3.1 * clamp((tt - 121.0) / 19.0)
        vh *= max(0.86, 1 - dr * max(0.0, tt - tA))
        return cx, cy, vh
    tA, mv = SHOTS[j][0], SHOTS[j][1]
    if t >= tA or j == 0: cx, cy, vh = at(j, t)
    else:
        p = at(j - 1, tA - mv); q = at(j, tA); k = ease_io((t - (tA - mv)) / mv)
        cx, cy = lerp(p[0], q[0], k), lerp(p[1], q[1], k); vh = math.exp(lerp(math.log(p[2]), math.log(q[2]), k))
    return Cam(cx, cy, vh)

# ================================================================= phases
CHORUS = [(LINES[10]["s"] - 0.06, LINES[16]["s"] - 0.10, 0), (LINES[24]["s"] - 0.06, CHART["t"] - 0.05, 1), (121.0, T_SPRAY0 - 0.2, 2)]
def chorus_k(t):
    for a, b, k in CHORUS:
        if a <= t < b: return k, a, b
    return None
def crowd_amt(t):
    a = 1 - sstep(10.9, 11.6, t)                                          # intro chant
    a = max(a, sstep(T_NOTICE - 9.7, T_NOTICE - 9.2, t) * (1 - sstep(T_NOTICE - 0.6, T_NOTICE, t)) * 0.0)
    for c0, c1, k in CHORUS: a = max(a, sstep(c0 - 0.2, c0 + 0.35, t) * (1 - sstep(c1 - 0.5, c1, t)))
    a = max(a, sstep(115.9, 116.6, t) * (1 - sstep(120.6, 121.0, t)))
    a = max(a, sstep(T_UNSUB + 0.6, T_UNSUB + 1.3, t) * (1 - sstep(T_END - 0.4, T_END + 0.6, t)))
    return a

# ================================================================= crowd: silhouettes, signs, fists (screen space)
SIGNS = ["OPT OUT", "NO", "PAY ME", "HUMAN", "OPT OUT", "MY DATA", "NO", "OPT OUT", "UNPLUG", "NOT A VECTOR", "OPT OUT", "NO"]
def people(W, H):
    vert = H > W; n = 8 if vert else 14; r = rng(77); P = []
    for i in range(n):
        x = (i + 0.5 + r.uniform(-0.3, 0.3)) / n * W * 1.08 - W * 0.04
        s = (W * 0.25 if vert else H * 0.235) * r.uniform(0.86, 1.12)
        kind = "sign" if i % 3 == 1 else ("fist" if i % 3 != 2 or i % 2 else ("mega" if i == (2 if vert else 8) else "plain"))
        P.append(dict(x=x, s=s, base=H * (0.90 if vert else 1.03) + r.uniform(-0.05, 0.06) * s, kind=kind, ph=r.uniform(0, 0.25),
                      sign=SIGNS[i % len(SIGNS)], side=(-1) ** i, lean=r.uniform(-0.08, 0.08)))
    return P
_PPL = {}
def sign_sprite(text, size):
    return strip_sprite(text, STENCIL, size, INK * 1.4, PAPER * 0.92, pad=0.30, seed=11)

def crowd(img, t, W, H, amt, fists=True):
    if amt <= 0.01: return
    k = (W, H)
    if k not in _PPL: _PPL[k] = people(W, H)
    vert = H > W; y_off = (1 - ease_out(amt)) * H * 0.35
    top = int(H * (0.42 if not vert else 0.45))
    m = np.zeros((H - top, W), np.float32)
    signs = []
    for p in _PPL[k]:
        s = p["s"]; pulse = bp(t - p["ph"] * 0.6, 6.5)
        hx = p["x"] + p["lean"] * s; hy = p["base"] - s * 0.95 + y_off - 0.05 * s * pulse - top
        cv2.ellipse(m, (int(hx), int(hy)), (int(s * 0.14), int(s * 0.17)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        body = np.array([(hx - s * 0.40, hy + s * 0.34), (hx - s * 0.16, hy + s * 0.20), (hx + s * 0.16, hy + s * 0.20),
                         (hx + s * 0.40, hy + s * 0.34), (hx + s * 0.46, H - top + 10), (hx - s * 0.46, H - top + 10)], np.int32)
        cv2.fillPoly(m, [body], 1.0, cv2.LINE_AA)
        if p["kind"] == "fist" and fists:
            sx = hx + p["side"] * s * 0.30; sy = hy + s * 0.30
            reach = 0.62 + 0.16 * pulse
            fx = sx + p["side"] * s * 0.08; fy = hy - s * reach
            cv2.line(m, (int(sx), int(sy)), (int(fx), int(fy + s * 0.08)), 1.0, max(2, int(s * 0.12)), cv2.LINE_AA)
            fw = s * 0.115; sd = p["side"]
            body = np.array([(fx - fw, fy - fw * 0.55), (fx + fw, fy - fw * 0.55), (fx + fw * 0.92, fy + fw * 0.95), (fx - fw * 0.85, fy + fw * 0.95)], np.int32)
            cv2.fillPoly(m, [body], 1.0, cv2.LINE_AA)
            for q in range(4):                                     # knuckle row
                kx = fx - fw * 0.75 + q * fw * 0.5
                cv2.circle(m, (int(kx), int(fy - fw * 0.62)), max(2, int(fw * 0.30)), 1.0, -1, cv2.LINE_AA)
            cv2.ellipse(m, (int(fx - sd * fw * 0.95), int(fy + fw * 0.05)), (max(2, int(fw * 0.30)), max(2, int(fw * 0.55))),
                        sd * 20, 0, 360, 1.0, -1, cv2.LINE_AA)    # thumb
            for q in range(1, 4):                                  # finger creases (cut back out)
                kx = fx - fw * 0.75 + q * fw * 0.5 - fw * 0.25
                cv2.line(m, (int(kx), int(fy - fw * 0.55)), (int(kx), int(fy - fw * 0.05)), 0.0, max(1, int(fw * 0.07)), cv2.LINE_AA)
        elif p["kind"] == "mega" and t < 11.2:
            ang = -1.15 + 0.08 * pulse; L = s * 0.42; mx, my = hx + s * 0.12, hy - s * 0.02
            ex, ey = mx + math.cos(ang) * L, my + math.sin(ang) * L; px, py = -math.sin(ang), math.cos(ang)
            cone = np.array([(mx + px * s * 0.035, my + py * s * 0.035), (mx - px * s * 0.035, my - py * s * 0.035),
                             (ex - px * s * 0.13, ey - py * s * 0.13), (ex + px * s * 0.13, ey + py * s * 0.13)], np.int32)
            cv2.fillPoly(m, [cone], 1.0, cv2.LINE_AA)
            cv2.line(m, (int(hx + s * 0.2), int(hy + s * 0.3)), (int(mx + math.cos(ang) * L * 0.3), int(my + math.sin(ang) * L * 0.3)), 1.0, max(2, int(s * 0.09)), cv2.LINE_AA)
        elif p["kind"] == "sign":
            bob = 0.10 * s * pulse
            sx, sy = hx + s * 0.05, hy - s * 0.35 - bob
            cv2.line(m, (int(hx), int(hy + s * 0.25)), (int(sx), int(sy)), 1.0, max(2, int(s * 0.04)), cv2.LINE_AA)
            cv2.line(m, (int(hx - s * 0.25), int(hy + s * 0.32)), (int(hx), int(hy + s * 0.05)), 1.0, max(2, int(s * 0.09)), cv2.LINE_AA)
            signs.append((p, sx, sy + top, s, pulse))
    # a road flare glowing behind the crowd, then rim light from both sides
    reg = img[top:]
    gk = (W, H, "glow")
    if gk not in _PPL:
        yy, xx = np.mgrid[0:H - top, 0:W].astype(np.float32)
        g = np.exp(-((yy - (H - top) * 0.62) / ((H - top) * 0.55)) ** 2) * (0.75 + 0.25 * np.cos(xx / W * 6.2832 * 1.5))
        g *= sstep_np(0.0, (H - top) * 0.45, yy)
        _PPL[gk] = g[..., None].astype(np.float32)
    fl_ = 0.85 + 0.15 * math.sin(t * 13.0) * math.sin(t * 7.3) + 0.25 * bp(t, 6)
    reg += _PPL[gk] * (RED * 0.55 + ORANGE * 0.12) * amt * fl_
    mm = cv2.GaussianBlur(m, (0, 0), 1.0)
    rim = np.clip(mm - np.roll(mm, 5, axis=0), 0, 1) + 0.6 * np.clip(mm - np.roll(mm, 4, axis=1), 0, 1) + 0.6 * np.clip(mm - np.roll(mm, -4, axis=1), 0, 1)
    a = mm[..., None] * min(1.0, amt * 1.5)
    reg *= (1 - a); reg += a * np.array([0.035, 0.03, 0.03], np.float32)
    reg += (rim[..., None] * np.array([1.0, 0.25, 0.18], np.float32) * 0.9 * amt)
    for p, sx, sy, s, pulse in signs:
        sz = int(s * 0.22)
        sp = sign_sprite(p["sign"], sz)
        put(img, sp, sx, sy - sp.shape[0] * 0.45, amt, rot=p["lean"] * 0.8 + 0.05 * math.sin(t * 3 + p["ph"] * 9), shadow_op=0.0)

# ================================================================= hooks: torn strips, slammed on the words
STY = {"paper": (INK * 1.3, PAPER * 0.95, STENCIL), "ink": (PAPER * 0.95, INK * 1.6, ANTON), "red": (PAPER * 0.97, RED * 0.95, STENCIL),
       "orange": (INK * 1.2, ORANGE, STENCIL), "redtxt": (RED * 0.95, PAPER * 0.95, STENCIL)}
ALT = [[("ALTERNATIVE", 0, "paper"), ("METAL,", 1, "ink")], [("RAP METAL,", 2, "paper"), ("FUNK METAL", 4, "ink")], [("LEARNING", 6, "red")]]
FIRE = [[("FINE-TUNED,", 0, "paper"), ("FIRED,", 1, "red")], [("AND THE GPUs", 2, "ink")], [("BURNING", 5, "orange")]]
NO = [[("I SAID", 0, "paper"), ("NO,", 2, "red")], [("BUT THE MODEL KEPT", 3, "ink")], [("LEARNING", 7, "paper")]]
NO2 = [[("I SAID NO,", 0, "red")], [("BUT THE MODEL", 3, "paper"), ("KEPT", 6, "ink")], [("LEARNING", 7, "redtxt")]]
CUT = [[("I SAID", 0, "paper"), ("NO,", 2, "red")], [("BUT THE MODEL KEPT", 3, "ink")]]
LAST = [[("I SAID", 0, "paper"), ("NO,", 2, "red")], [("BUT THE MODEL KEPT", 3, "ink")], [("LEARNING!", 7, "red")]]
HOOKS = {10: ALT, 11: FIRE, 12: ALT, 13: NO, 14: NO2, 15: NO, 24: ALT, 25: FIRE, 26: ALT, 27: NO, 33: ALT, 34: ALT, 35: CUT, 36: LAST,
         28: [[("LOSS GOES DOWN!", 0, "paper")]], 29: [[("RENT GOES UP!", 0, "red")]], 30: [[("LOSS GOES DOWN!", 0, "ink")]],
         31: [[("RENT GOES UP!", 0, "red")]], 32: [[("GRADIENT DESCENT", 0, "paper")]],
         37: [[("UNSUBSCRIBE!", 0, "red")]]}
TOPBAND = {28, 29, 30, 31, 32}          # breakdown: lyrics ride above the chart, never on it
PROGRESS = {13: (0.61, 0.87), 14: (0.87, 0.94), 15: (0.94, 0.99), 27: (0.88, 1.0), 35: (0.2, 0.71), 36: (0.71, 1.0)}
CHANT = [0.69, 2.78, 5.30, 6.23, 7.65, 9.07]

def hook_window(i):
    L = LINES[i]; nxt = [j for j in HOOKS if j > i]; n = LINES[min(nxt)]["s"] if nxt else 1e9
    end = min(n - 0.03, L["e"] + (0.9 if i not in (37,) else 99))
    if i + 1 < len(LINES) and (i + 1) not in HOOKS: end = min(end, LINES[i + 1]["s"] - 0.12)   # clear before a verse line starts
    if i == 37: end = T_END + 0.2
    return L["wt"][0] - 0.07, end

_LAY = {}
def layout_rows(rows, W, H, big=False, prog=False, top=False):
    key = (repr(rows), W, H, big, prog, top)
    if key in _LAY: return _LAY[key]
    vert = H > W; maxw = W * (0.88 if not vert else 0.90)
    maxh = H * ((0.56 if prog else 0.62) if not vert else (0.40 if prog else 0.44)) if not top else H * (0.20 if not vert else 0.16)
    k = 1.0
    while True:
        base = (150 if not vert else 118) * (1.5 if big else 1.0) * k; out = []
        for row in rows:
            fs = int(base * (1.25 if len(row) == 1 and len(row[0][0]) <= 10 else 1.0))
            while True:
                sps = [strip_sprite(w, STY[st][2], fs, STY[st][0], STY[st][1], seed=wi) for w, wi, st in row]
                tot = sum(sp.shape[1] for sp in sps) + fs * 0.12 * (len(row) - 1)
                if tot <= maxw or fs < 40: break
                fs = int(fs * 0.92)
            out.append((row, sps, tot, fs))
        hsum = sum(sps[0].shape[0] * 0.92 for _, sps, _, _ in out)
        if hsum <= maxh or k < 0.5: break
        k *= 0.93
    yc = H * ((0.44 if prog else 0.40) if not vert else (0.40 if prog else 0.37)) if not top else H * (0.150 if not vert else 0.215)
    y = yc - hsum / 2; res = []
    for row, sps, tot, fs in out:
        x = W / 2 - tot / 2; h = sps[0].shape[0]
        for (w, wi, st), sp in zip(row, sps):
            res.append((w, wi, st, (fs, sp.shape), x + sp.shape[1] / 2, y + h / 2)); x += sp.shape[1] + fs * 0.12
        y += h * 0.92
    _LAY[key] = res
    return res

class _Shape:
    def __init__(self, shp): self.shape = shp
def lay_sprites(lay):
    """layout geometry -> (word, word index, style, sprite array, cx, cy)"""
    return [(w, wi, st, strip_sprite(w, STY[st][2], fs_shp[0], STY[st][0], STY[st][1], seed=wi), cx, cy) for w, wi, st, fs_shp, cx, cy in lay]

def draw_hooks(img, t, W, H):
    vert = H > W
    for i, rows in HOOKS.items():
        a, b = hook_window(i)
        if not (a <= t < b + 0.15): continue
        out = 1 - sstep(b, b + 0.12, t)
        lay = layout_rows(rows, W, H, big=(i == 37), prog=(i in PROGRESS), top=(i in TOPBAND))
        lay = [(w, wi, st, _Shape(fs_shp[1]), cx, cy) for w, wi, st, fs_shp, cx, cy in lay] if False else lay_sprites(lay)
        r = rng(i)
        if i == 36:
            tL = LINES[36]["wt"][7]
            if t >= tL - 0.03:
                sl = slam(t, tL - 0.03); op, sc, jit = sl
                fs = int((330 if not vert else 210) * min(W, H) / 1080)
                big = strip_sprite("LEARNING!", STENCIL, fs, PAPER * 0.97, RED * 0.95, seed=36)
                kk = min(1.0, W * 0.94 / big.shape[1])
                put(img, big, W / 2 + r.uniform(-1, 1) * 30 * jit, H * (0.42 if not vert else 0.40), op * out, -0.035, sc * kk * (1 + 0.06 * (t - tL)), 0.7)
                lay = [x for x in lay if x[0] != "LEARNING!"]
                fade = 1 - sstep(tL - 0.03, tL + 0.10, t)
                if fade <= 0.01: continue
                out *= fade
        for w, wi, st, sp, cx, cy in lay:
            tw = LINES[i]["wt"][min(wi, len(LINES[i]["wt"]) - 1)]
            sl = slam(t, tw - 0.03)
            if sl is None: continue
            op, sc, jit = sl
            rot = r.uniform(-0.05, 0.05); jx, jy = r.uniform(-1, 1) * 14 * jit, r.uniform(-1, 1) * 10 * jit
            dy = -(1 - out) * H * 0.06
            sc *= 1 + 0.018 * bp(t, 8)
            put(img, sp, cx + jx, cy + jy + dy, op * out, rot, sc, 0.55)
            if st == "orange": flames(img, t, cx, cy - sp.shape[0] * 0.45, sp.shape[1] * sc, sp.shape[0], op * out)
        if i in PROGRESS: progress(img, t, W, H, i, lay, out)

def progress(img, t, W, H, i, lay, op):
    p0, p1 = PROGRESS[i]; L = LINES[i]
    p = lerp(p0, p1, clamp((t - L["wt"][3]) / max(0.4, L["e"] - L["wt"][3])))
    if t < L["wt"][3] - 0.05: return
    vert = H > W; ts = min(W, H) / 1080
    bw = W * (0.50 if not vert else 0.78); bh = 44 * ts
    y = max(H * (0.055 if not vert else 0.10), min(cy - sp.shape[0] * 0.5 for _, _, _, sp, cx, cy in lay) - 44 * ts)
    x = W / 2 - bw / 2
    o = op * sstep(L["wt"][3] - 0.05, L["wt"][3] + 0.15, t)
    lab = "model.train()" if p < 0.999 else "TRAINING COMPLETE"
    sp = strip_sprite(lab, TYPEW, int(40 * ts), INK * 1.2, PAPER * 0.95, pad=0.16, seed=3)
    put(img, sp, x + sp.shape[1] / 2 - 6 * ts, y, o, -0.01, 1.0, 0.4)
    bx = x + sp.shape[1] + 10 * ts; bw2 = x + bw - bx
    if bw2 > 40:
        x0, y0, x1, y1 = int(bx), int(y - bh / 2), int(bx + bw2), int(y + bh / 2)
        reg = img[y0:y1, x0:x1]; reg *= (1 - 0.85 * o); reg += PAPER * 0.92 * 0.85 * o
        fx = int(x0 + 5 * ts + (x1 - x0 - 10 * ts) * p)
        img[y0 + int(5 * ts):y1 - int(5 * ts), x0 + int(5 * ts):fx] *= (1 - o)
        img[y0 + int(5 * ts):y1 - int(5 * ts), x0 + int(5 * ts):fx] += RED * o
        cv2.rectangle(img, (x0, y0), (x1, y1), (INK * o + img[y0, x0] * (1 - o)).tolist(), max(2, int(3 * ts)))
        pct = f"{int(p * 100)}%"
        blit(img, sprite(pct, MONO, int(36 * ts), 6), x1 + 14 * ts, y - 22 * ts, PAPER, o, 0.0)

def flames(img, t, cx, top, w, h, op):
    if op <= 0.01: return
    H, W = img.shape[:2]; r = rng(5)
    for i in range(26):
        u = r.random(); ph = r.random(); sp = r.uniform(1.4, 2.2)
        life = (t * sp + ph) % 1.0
        x = cx + (u - 0.5) * w * 0.92 + math.sin(t * 7 + i) * h * 0.06
        y = top - life * h * 1.1
        rad = h * 0.22 * (1 - life) + 2
        col = ORANGE * (1 - life) + RED * life * 0.7
        cv2.circle(img, (int(x), int(y)), int(rad), (col * op * (1 - life) * 0.9 + 0).tolist(), -1, cv2.LINE_AA) if False else None
        x0, y0 = int(x - rad * 2), int(y - rad * 2); x1, y1 = int(x + rad * 2), int(y + rad * 2)
        if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H: continue
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
        g = np.exp(-(((xx - x) / rad) ** 2 + ((yy - y) / (rad * 1.5)) ** 2) * 1.6)[..., None]
        img[Y0:Y1, X0:X1] += g * col * op * (1 - life) * 0.75

def chant(img, t, W, H):
    vert = H > W
    for k, tc in enumerate(CHANT):
        if not (tc - 0.06 <= t < 11.0): continue
        sl = slam(t, tc)
        if sl is None: continue
        op, sc, jit = sl
        fs = int((118 + 14 * k) * (1.05 if vert else 1.0) * min(W, H) / 1080)
        st = ("paper", "red", "ink")[k % 3]
        sp = strip_sprite("OPT OUT!", STY[st][2], fs, STY[st][0], STY[st][1], seed=k)
        r = rng(30 + k)
        cx = W * (0.5 + (r.uniform(-0.22, 0.22) if not vert else r.uniform(-0.08, 0.08)))
        cy = H * (0.16 + 0.10 * k if not vert else 0.15 + 0.085 * k)
        put(img, sp, cx + r.uniform(-1, 1) * 12 * jit, cy, op * (1 - sstep(10.75, 11.1, t)), r.uniform(-0.09, 0.09), sc, 0.55)
    for tc, word, yy in ((9.96, "OPT", 0.36), (10.58, "OUT!", 0.62)):
        sl = slam(t, tc)
        if sl is None or t > 11.15: continue
        op, sc, jit = sl
        fs = int((330 if not vert else 290) * min(W, H) / 1080)
        sp = strip_sprite(word, STENCIL, fs, PAPER * 0.97, RED * 0.95 if word == "OPT" else INK * 1.5, seed=9)
        put(img, sp, W / 2, H * (yy if not vert else 0.26 + (yy - 0.36) * 0.62), op * (1 - sstep(10.9, 11.2, t)), -0.04 if word == "OPT" else 0.03, sc, 0.6)

# ---------------------------------------------------------------- ransom-note title
TITLE16 = ["RAGE AGAINST THE", "MACHINE LEARNING"]; TITLE9 = ["RAGE", "AGAINST THE", "MACHINE", "LEARNING"]
RFONTS = [ANTON, STENCIL, PLAY, BLACK, TYPEW, MARKER, CORM, MONO]
RSTY = [(INK * 1.2, PAPER * 0.95), (PAPER * 0.95, INK * 1.6), (RED * 0.95, PAPER * 0.95), (PAPER * 0.97, RED * 0.95),
        (INK * 1.2, ORANGE), (INK * 1.2, PAPER * 0.85)]
T_TITLE0 = float(DOWN[np.argmin(abs(DOWN - 11.17))]); EIGHTH = 30.0 / TM.tempo
def ransom(img, t, W, H):
    if not (T_TITLE0 - 0.1 <= t < T_NOTICE + 0.25): return
    vert = H > W; rows = TITLE9 if vert else TITLE16; ts = min(W, H) / 1080
    fs = int((188 if not vert else 175) * ts)
    gone = sstep(T_NOTICE - 0.25, T_NOTICE + 0.15, t)
    r = rng(2); n = 0
    lay = []
    for ri, row in enumerate(rows):
        items = []
        for ch in row:
            if ch == " ": items.append(None); continue
            f = RFONTS[int(r.integers(0, len(RFONTS)))]; stl = RSTY[int(r.integers(0, len(RSTY)))]
            szk = r.uniform(0.86, 1.14) * (0.72 if row.startswith("THE") or (row.endswith("THE") and False) else 1.0)
            items.append((ch, f, stl, szk, r.uniform(-0.13, 0.13), r.uniform(-0.06, 0.06)))
        lay.append(items)
    rowh = fs * 1.30; y0 = H * (0.38 if not vert else 0.38) - (len(rows) - 1) * rowh / 2
    for ri, items in enumerate(lay):
        sps = [None if it is None else strip_sprite(it[0], it[1], int(fs * it[3]), it[2][0], it[2][1], pad=0.16, seed=ri * 40 + k)
               for k, it in enumerate(items)]
        widths = [fs * 0.35 if sp is None else sp.shape[1] * 0.94 for sp in sps]
        tot = sum(widths); sc_row = min(1.0, W * 0.92 / tot); x = W / 2 - tot * sc_row / 2
        for it, sp, wd in zip(items, sps, widths):
            if it is None: x += wd * sc_row; continue
            tl = T_TITLE0 + (n * EIGHTH if n < 14 else 14 * EIGHTH + (n - 14) * EIGHTH / 2); n += 1
            sl = slam(t, tl)
            if sl is not None:
                op, sc, jit = sl
                dy = -gone * H * 0.9 * (0.6 + 0.4 * math.sin(n * 1.7) ** 2); rot = it[4] + gone * (n % 3 - 1) * 0.6
                put(img, sp, x + wd * sc_row / 2, y0 + ri * rowh + it[5] * fs + dy, op, rot, sc * sc_row, 0.6)
            x += wd * sc_row
    t_by = T_TITLE0 + 14 * EIGHTH + (n - 14) * EIGHTH / 2 + 0.35
    if t > t_by - 0.05:
        o = sstep(t_by - 0.05, t_by + 0.15, t) * (1 - gone)
        y = y0 + (len(rows) - 1) * rowh + fs * 1.05
        sp = strip_sprite("aditazzz", TYPEW, int(64 * ts), INK * 1.2, PAPER * 0.95, pad=0.2, seed=4)
        put(img, sp, W / 2, y, o, -0.02, 1.0, 0.5)
        sp2 = strip_sprite("animated in code by Claude Opus 5.5", TYPEW, int(36 * ts), PAPER * 0.95, INK * 1.6, pad=0.2, seed=6)
        put(img, sp2, W / 2, y + 74 * ts, o * sstep(t_by + 0.3, t_by + 0.5, t), 0.015, 1.0, 0.5)

# ================================================================= breakdown chart: LOSS goes down, RENT goes up, ball onto ME
def chart_pt(u, v):
    f = CHART; c, s = math.cos(f["rot"]), math.sin(f["rot"])
    dx, dy = (u - 0.5) * f["w"], (v - 0.5) * f["h"]
    return f["x"] + c * dx - s * dy, f["y"] + s * dx + c * dy
def loss_v(u): return 0.80 - 0.60 * math.exp(-4.2 * (u - 0.12))
BARS = [(0.24, 0.16), (0.44, 0.30), (0.64, 0.52), (0.84, 1.02)]
def chart_dyn(img, t, M, W, H):
    if t < CHART["t"] + 0.2 or t > T_SPRAY0 + 6: return
    s = math.hypot(M[0, 0], M[1, 0]); ts = min(W, H) / 1080
    L28, L30 = LINES[28], LINES[30]
    k1 = clamp((t - L28["wt"][0] + 0.1) / 1.4); k2 = clamp((t - L30["wt"][0] + 0.1) / 1.4)
    umax = 0.12 + 0.40 * ease_out(k1) + 0.40 * ease_out(k2)
    if umax > 0.121:
        us = np.linspace(0.12, umax, 60)
        pts = np.array([to_screen(M, *chart_pt(u, loss_v(u))) for u in us], np.float32)
        cv2.polylines(img, [pts.astype(np.int32)], False, (INK * 1.0).tolist(), max(3, int(0.016 * s)), cv2.LINE_AA)
        cv2.polylines(img, [(pts + np.float32([1.5, -1.0])).astype(np.int32)], False, (INK * 1.6).tolist(), max(2, int(0.007 * s)), cv2.LINE_AA)
        if k1 > 0.3:
            lx, ly = to_screen(M, *chart_pt(0.15, 0.13))
            blit(img, sprite("LOSS", STENCIL, max(20, int(0.07 * s))), lx, ly, INK, sstep(0.3, 0.5, k1), anchor='lt')
    L29, L31 = LINES[29], LINES[31]
    for bi, (u, hgt) in enumerate(BARS):
        tb = (L29["wt"][2] - 0.3 + bi * 0.35) if bi < 2 else (L31["wt"][2] - 0.6 + (bi - 2) * 0.45)
        g = ease_out(clamp((t - tb) / (0.5 if bi < 3 else 0.9)))
        if g <= 0: continue
        hh = hgt * g + (0.04 * math.sin((t - tb) * 9) * math.exp(-(t - tb) * 3) if bi == 3 and t > tb + 0.9 else 0)
        quad = [chart_pt(u - 0.045, 0.86), chart_pt(u + 0.045, 0.86), chart_pt(u + 0.045, 0.86 - hh * 0.72), chart_pt(u - 0.045, 0.86 - hh * 0.72)]
        q = np.array([to_screen(M, *p) for p in quad], np.float32)
        lay = np.zeros(img.shape[:2], np.float32); cv2.fillPoly(lay, [q.astype(np.int32)], 1.0, cv2.LINE_AA)
        img *= (1 - lay[..., None] * 0.93); img += lay[..., None] * RED * 0.93
    if t > L29["wt"][0]:
        lx, ly = to_screen(M, *chart_pt(0.70, 0.08 if t < L31["wt"][2] else -0.10))
        blit(img, sprite("RENT", STENCIL, max(20, int(0.075 * s))), lx, ly, RED, sstep(L29["wt"][0], L29["wt"][0] + 0.3, t), anchor='lt')
    # gradient descent: a ball rolls down the loss curve onto ME
    L32 = LINES[32]; tg0, tme = L32["wt"][0] + 0.05, L32["wt"][3]
    mx, my = 0.925, 0.83
    squash = sstep(tme - 0.06, tme + 0.04, t)
    hx, hy = to_screen(M, *chart_pt(mx, my - 0.12)); sz = 0.16 * s
    if t > CHART["t"] + 0.3:
        hs = 1 - 0.6 * squash
        cx_, cy_ = to_screen(M, *chart_pt(mx, my))
        hh = sz * hs
        cv2.circle(img, (int(cx_), int(cy_ - hh * 0.95)), max(2, int(sz * 0.16 * (1 + 0.3 * squash))), (INK * 1.0).tolist(), max(2, int(0.006 * s)), cv2.LINE_AA)
        cv2.line(img, (int(cx_), int(cy_ - hh * 0.78)), (int(cx_), int(cy_ - hh * 0.30)), (INK * 1.0).tolist(), max(2, int(0.006 * s)), cv2.LINE_AA)
        for dx_ in (-1, 1):
            cv2.line(img, (int(cx_), int(cy_ - hh * 0.30)), (int(cx_ + dx_ * sz * 0.18 * (1 + squash)), int(cy_)), (INK * 1.0).tolist(), max(2, int(0.006 * s)), cv2.LINE_AA)
            cv2.line(img, (int(cx_), int(cy_ - hh * 0.62)), (int(cx_ + dx_ * sz * 0.22 * (1 + squash)), int(cy_ - hh * (0.45 + 0.25 * (1 - squash)))), (INK * 1.0).tolist(), max(2, int(0.006 * s)), cv2.LINE_AA)
        blit(img, sprite("ME", MARKER, max(18, int(0.075 * s))), cx_, cy_ + sz * 0.20, RED, 1.0, anchor='c')
    if tg0 <= t:
        k = clamp((t - tg0) / (tme - tg0)); u = 0.12 + (0.92 - 0.12) * k * k
        if t > tme: u = 0.92 + 0.015 * math.exp(-(t - tme) * 6) * math.sin((t - tme) * 30)
        bx, by = to_screen(M, *chart_pt(u, loss_v(u) - 0.035))
        cv2.circle(img, (int(bx), int(by)), max(3, int(0.036 * s)), (INK * 1.0).tolist(), -1, cv2.LINE_AA)
        cv2.circle(img, (int(bx - 0.011 * s), int(by - 0.011 * s)), max(1, int(0.010 * s)), (PAPER * 0.6).tolist(), -1, cv2.LINE_AA)
    sl = slam(t, L32["wt"][2])
    if sl and t < T_SPRAY0 + 6: world_strip(img, M, "ON ME!", "red", *chart_pt(0.70, 0.60), 0.13, -0.12, sl[0], sl[1])

# ================================================================= spray paint (world-anchored), drips, the can
_NZ = {}
def noise_tile():
    if "n" not in _NZ:
        n = 512; a = rng(91).random((n, n)).astype(np.float32); _NZ["n"] = (a, 0.35 / n)
    return _NZ["n"]
def spray(img, t, M, W, H, faded=False, scale=1.0, offset=(0.0, 0.0), alpha=0.92, col=None, done=None):
    col = RED if col is None else col
    paint, heads, s = spray_mask(t, M, W, H, scale, offset, done)
    if paint is None: return heads, s
    paint = paint * alpha * (0.55 if faded else 1.0)
    img *= (1 - paint[..., None]); img += paint[..., None] * col
    return heads, s

def spray_mask(t, M, W, H, scale=1.0, offset=(0.0, 0.0), done=None):
    s = math.hypot(M[0, 0], M[1, 0])
    m = np.zeros((H, W), np.float32); heads = []; drips = []
    for t0, t1, st, cx in SPRAY:
        if done is None and t < t0: break
        k = 1.0 if done else clamp((t - t0) / (t1 - t0))
        part, _ = _cut(st, k)
        for stroke in part:
            pts = np.array([to_screen(M, offset[0] + x * scale, offset[1] + y * scale) for x, y in stroke], np.float32)
            if len(pts) >= 2: cv2.polylines(m, [pts.astype(np.int32)], False, 1.0, max(2, int(0.085 * s * scale)), cv2.LINE_AA)
            # drips under the lowest points of each stroke
            lo = max(stroke, key=lambda p: p[1])
            age = (t - t1) if not done else 9.0
            if age > -0.6:
                dl = 0.20 * scale * min(1.0, (age + 0.6) / 2.5) * (0.6 + 0.4 * ((int(lo[0] * 97) % 7) / 6))
                drips.append((offset[0] + lo[0] * scale, offset[1] + lo[1] * scale, dl))
        if not done and t < t1: heads.append(part[-1][-1] if part and part[-1] else st[0][0])
    for x, y, dl in drips:
        a = to_screen(M, x, y); b = to_screen(M, x, y + dl)
        cv2.line(m, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1.0, max(1, int(0.016 * s * scale)), cv2.LINE_AA)
        cv2.circle(m, (int(b[0]), int(b[1])), max(1, int(0.013 * s * scale)), 1.0, -1, cv2.LINE_AA)
    if m.max() <= 0: return None, heads, s
    core_ = cv2.GaussianBlur(m, (0, 0), max(0.8, 0.006 * s * scale))
    over = cv2.GaussianBlur(m, (0, 0), max(2.0, 0.045 * s * scale))
    nt, u = noise_tile(); A = np.vstack([M, [0, 0, 1]]) @ np.array([[u, 0, 0], [0, u, 0], [0, 0, 1]], np.float32)
    nz = cv2.warpAffine(nt, A[:2], (W, H), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)
    speck = (nz > 0.80).astype(np.float32) * np.clip(over * 2.2, 0, 1) * 0.8
    paint = np.clip(core_ * (0.88 + 0.12 * nz) + speck, 0, 1)
    return paint, heads, s

_TAG = {}
def old_tag(img, M, W, H, scale=0.46, offset=(0.02, -0.03), alpha=0.33, col=None):
    """The faded OPT OUT already on the wall: sprayed once into a world-space texture, then just warped."""
    col = PAPER * 0.8 if col is None else col
    if "m" not in _TAG:
        u = 650.0; x0, y0, x1, y1 = -1.15 * scale / 0.46 + offset[0], -0.32 + offset[1], 1.15 * scale / 0.46 + offset[0], 0.42 + offset[1]
        Wt, Ht = int((x1 - x0) * u), int((y1 - y0) * u)
        Mt = np.array([[u, 0, -x0 * u], [0, u, -y0 * u]], np.float32)
        m, _, _ = spray_mask(0.0, Mt, Wt, Ht, scale, offset, done=True)
        _TAG["m"] = (m.astype(np.float32), Mt)
    m, Mt = _TAG["m"]
    A = np.vstack([M, [0, 0, 1]]) @ np.linalg.inv(np.vstack([Mt, [0, 0, 1]]))
    w = cv2.warpAffine(m, A[:2].astype(np.float32), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    w *= alpha
    img *= (1 - w[..., None]); img += w[..., None] * col

def spray_can(img, t, M, head, s, W, H):
    """Hand holding the can (index finger on the nozzle), forearm fading off into the dark."""
    if head is None: return
    hx, hy = to_screen(M, *head); ts = min(W, H) / 1080
    sz = 205 * ts
    r = rng(int(t * 30))
    for i in range(46):                                                     # mist at the nozzle
        a = r.uniform(-0.7, 0.7) + math.pi; d = r.uniform(0, 1) ** 0.6 * sz * 0.85
        px, py = hx + math.cos(a) * d * -0.6 + sz * 0.10, hy + math.sin(a) * d * 0.45
        cv2.circle(img, (int(px), int(py)), max(1, int(r.uniform(1, 3.2) * ts)), (RED * 0.9).tolist(), -1, cv2.LINE_AA)
    ang = 0.42; ca_, sa_ = math.cos(ang), math.sin(ang)
    def R(px, py): return (hx + sz * 0.14 + px * ca_ - py * sa_, hy + sz * 0.10 + px * sa_ + py * ca_)
    P = lambda pts: np.array([R(*q) for q in pts], np.int32)
    cw, ch = sz * 0.24, sz * 0.86
    # forearm first (behind the hand): wrist -> off into the dark, alpha fades with distance
    wx, wy = R(sz * 0.30, sz * 0.62); dx_, dy_ = 0.55, 0.83; px_, py_ = -dy_, dx_; L = sz * 2.6
    arm = np.array([(wx + px_ * sz * 0.20, wy + py_ * sz * 0.20), (wx - px_ * sz * 0.20, wy - py_ * sz * 0.20),
                    (wx + dx_ * L - px_ * sz * 0.48, wy + dy_ * L - py_ * sz * 0.48), (wx + dx_ * L + px_ * sz * 0.48, wy + dy_ * L + py_ * sz * 0.48)], np.int32)
    x0, y0 = max(0, int(arm[:, 0].min()) - 2), max(0, int(arm[:, 1].min()) - 2); x1, y1 = min(W, int(arm[:, 0].max()) + 2), min(H, int(arm[:, 1].max()) + 2)
    if x1 > x0 and y1 > y0:
        m = np.zeros((y1 - y0, x1 - x0), np.float32); cv2.fillPoly(m, [arm - np.int32([x0, y0])], 1.0, cv2.LINE_AA)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        along = ((xx - wx) * dx_ + (yy - wy) * dy_) / L
        m *= np.clip(1.15 - along * 1.25, 0, 1)
        reg = img[y0:y1, x0:x1]; reg *= (1 - m[..., None]); reg += m[..., None] * np.array([0.05, 0.045, 0.045], np.float32)
        cuff = (wx + dx_ * sz * 0.40, wy + dy_ * sz * 0.40)
        cv2.line(img, (int(cuff[0] + px_ * sz * 0.26), int(cuff[1] + py_ * sz * 0.26)), (int(cuff[0] - px_ * sz * 0.26), int(cuff[1] - py_ * sz * 0.26)),
                 (RED * 0.45).tolist(), max(2, int(5 * ts)), cv2.LINE_AA)
    # the can
    cv2.fillPoly(img, [P([(-cw, 0), (cw, 0), (cw, ch), (-cw, ch)])], (np.array([0.80, 0.78, 0.72]) * 0.58).tolist(), cv2.LINE_AA)
    cv2.fillPoly(img, [P([(-cw * 0.62, sz * 0.04), (-cw * 0.30, sz * 0.04), (-cw * 0.30, ch - sz * 0.04), (-cw * 0.62, ch - sz * 0.04)])], (np.array([0.97, 0.95, 0.9]) * 0.8).tolist(), cv2.LINE_AA)
    cv2.fillPoly(img, [P([(-cw, ch * 0.30), (cw, ch * 0.30), (cw, ch * 0.52), (-cw, ch * 0.52)])], (RED * 0.85).tolist(), cv2.LINE_AA)
    cv2.fillPoly(img, [P([(-cw * 0.78, -sz * 0.13), (cw * 0.78, -sz * 0.13), (cw, 0), (-cw, 0)])], (np.array([0.12, 0.11, 0.11])).tolist(), cv2.LINE_AA)
    nzx, nzy = R(0, -sz * 0.17); cv2.circle(img, (int(nzx), int(nzy)), max(2, int(sz * 0.055)), (np.array([0.10, 0.1, 0.1])).tolist(), -1, cv2.LINE_AA)
    # gloved hand wrapped around the can, index finger up on the nozzle
    glove = np.array([0.06, 0.055, 0.055], np.float32)
    cv2.fillPoly(img, [P([(-cw * 1.05, ch * 0.50), (cw * 1.20, ch * 0.46), (cw * 1.35, ch * 0.80), (-cw * 0.9, ch * 0.86)])], glove.tolist(), cv2.LINE_AA)
    for q in range(4):                                                        # knuckles across the front of the can
        kx, ky = R(-cw * 0.75 + q * cw * 0.52, ch * 0.50)
        cv2.circle(img, (int(kx), int(ky)), max(2, int(sz * 0.085)), glove.tolist(), -1, cv2.LINE_AA)
    a_ = R(cw * 0.55, ch * 0.48); b_ = R(cw * 0.15, -sz * 0.13)
    cv2.line(img, (int(a_[0]), int(a_[1])), (int(b_[0]), int(b_[1])), glove.tolist(), max(3, int(sz * 0.12)), cv2.LINE_AA)
    cv2.circle(img, (int(b_[0]), int(b_[1])), max(2, int(sz * 0.07)), glove.tolist(), -1, cv2.LINE_AA)

# ================================================================= wheat-paste brush + marker write-on for the newest verse flyer
def brush_layer(img, f, t, M, W, H):
    x = t - f["t"]
    if not f.get("brush") or not (0.02 <= x <= 0.75): return
    k = ease_io(clamp((x - 0.04) / 0.55))
    # brush sweeps diagonally across the flyer: top-left -> bottom-right
    u = lerp(-0.15, 1.15, k)
    p = (f["x"] + (u - 0.5) * f["w"] * 0.9, f["y"] + (u - 0.5) * f["h"] * 0.9)
    bx, by = to_screen(M, *p); s = math.hypot(M[0, 0], M[1, 0]); ts = min(W, H) / 1080
    bw = 0.21 * s; ang = math.atan2(f["h"], f["w"]) + math.pi / 2 + f["rot"]
    dx, dy = math.cos(ang) * bw / 2, math.sin(ang) * bw / 2
    head = np.array([(bx - dx, by - dy), (bx + dx, by + dy), (bx + dx + 0.06 * s, by + dy + 0.05 * s), (bx - dx + 0.06 * s, by - dy + 0.05 * s)], np.int32)
    cv2.fillPoly(img, [head], (np.array([0.62, 0.55, 0.44]) * 0.55).tolist(), cv2.LINE_AA)
    for i in range(14):
        q = i / 13; ax, ay = bx - dx + 2 * dx * q, by - dy + 2 * dy * q
        cv2.line(img, (int(ax), int(ay)), (int(ax - 0.02 * s), int(ay - 0.025 * s)), (np.array([0.75, 0.68, 0.52]) * 0.7).tolist(), max(1, int(2 * ts)), cv2.LINE_AA)
    hx, hy = bx + 0.03 * s, by + 0.025 * s
    cv2.line(img, (int(hx), int(hy)), (int(hx + 0.45 * s), int(hy + 0.42 * s)), (np.array([0.24, 0.17, 0.10])).tolist(), max(3, int(0.022 * s)), cv2.LINE_AA)
    arm = np.array([(hx + 0.38 * s, hy + 0.30 * s), (hx + 0.52 * s, hy + 0.48 * s), (W * 1.3, H * 1.6), (W * 1.5, H * 1.2)], np.int32)
    cv2.fillPoly(img, [arm], (np.array([0.03, 0.028, 0.027])).tolist(), cv2.LINE_AA)

# ================================================================= world-anchored type, shake, motion blur
def world_strip(img, M, text, st, wx, wy, world_h, rot, op, sc=1.0, base=200):
    sp = strip_sprite(text, STY[st][2], base, STY[st][0], STY[st][1], seed=17)
    s = math.hypot(M[0, 0], M[1, 0]); x, y = to_screen(M, wx, wy)
    put(img, sp, x, y, op, rot + math.atan2(M[1, 0], M[0, 0]), sc * world_h * s / sp.shape[0], 0.55)

def world_text(img, M, text, font, wx, wy, world_size, col, op, anchor='c', base=120):
    s = math.hypot(M[0, 0], M[1, 0]); x, y = to_screen(M, wx, wy)
    blit(img, sprite(text, font, base, 4), x, y, col, op, 0.0, anchor=anchor, scale=world_size * s / base)

T_OPTSTAMP = float(DOWN[np.argmin(abs(DOWN - 25.77))])
IMPULSES = [(tc, 0.55) for tc in CHANT] + [(9.96, 1.0), (10.58, 1.2), (T_NOTICE, 0.7), (T_OPTSTAMP, 1.1)]
IMPULSES += [(f["t"], 0.35) for f in VERSE] + [(f["t"], 0.45) for f in FLY if f["kind"] == "poster"] + [(CHART["t"], 0.8)]
for i, rows in HOOKS.items():
    for row in rows:
        for w, wi, st in row: IMPULSES.append((LINES[i]["wt"][min(wi, len(LINES[i]["wt"]) - 1)], 0.5 if i != 37 else 1.6))
IMPULSES += [(LINES[32]["wt"][3], 1.5), (LINES[36]["wt"][7], 1.8), (121.07, 1.2)]
IMPULSES.sort()
_IMP_T = np.array([a for a, b in IMPULSES]); _IMP_A = np.array([b for a, b in IMPULSES])

def shake(t, W, H):
    i1 = np.searchsorted(_IMP_T, t); i0 = max(0, i1 - 6); amp = 0.0
    for tt, a in zip(_IMP_T[i0:i1], _IMP_A[i0:i1]):
        x = t - tt
        if 0 <= x < 0.5: amp += a * math.exp(-x * 11)
    ck = chorus_k(t); hand = 0.35 if ck else 0.18
    ts = min(W, H) / 1080
    sx = (amp * 16 * math.sin(t * 61.0) + hand * 6 * math.sin(t * 1.3) + hand * 3 * math.sin(t * 3.7 + 1)) * ts
    sy = (amp * 12 * math.cos(t * 53.0) + hand * 5 * math.sin(t * 1.1 + 2) + hand * 2.5 * math.sin(t * 4.1)) * ts
    return sx, sy

def flash_at(t):
    fl = 0.0
    for c0, c1, k in CHORUS:
        if 0 <= t - (c0 + 0.1) < 1.0: fl += 0.45 * math.exp(-(t - c0 - 0.1) * 5)
    for tt, a in ((T_NOTICE, 0.15), (T_OPTSTAMP, 0.35), (CHART["t"], 0.25), (LINES[36]["wt"][7], 0.7), (T_UNSUB, 0.6), (LINES[32]["wt"][3], 0.4)):
        if 0 <= t - tt < 0.8: fl += a * math.exp(-(t - tt) * 6)
    for f in VERSE:
        if 0 <= t - f["t"] < 0.4: fl += 0.10 * math.exp(-(t - f["t"]) * 12)    # protest photographer's flash
    return fl

def motion_blur(img, M, Mp, W, H):
    c = np.linalg.solve(M[:, :2].astype(np.float64), np.array([W / 2, H / 2], np.float64) - M[:, 2])
    a = to_screen(M, *c); b = to_screen(Mp, *c); dx, dy = a[0] - b[0], a[1] - b[1]
    s1 = math.hypot(M[0, 0], M[1, 0]); s0 = math.hypot(Mp[0, 0], Mp[1, 0])
    v = math.hypot(dx, dy)
    if abs(s1 / s0 - 1) > 0.03 and v < 8:      # fast zoom: radial-ish blur via scaled blend
        k = min(0.10, abs(s1 / s0 - 1) * 0.8)
        z = cv2.resize(img, None, fx=1 + k, fy=1 + k)
        oy, ox = (z.shape[0] - H) // 2, (z.shape[1] - W) // 2
        return img * 0.6 + z[oy:oy + H, ox:ox + W] * 0.4
    if v < 7: return img
    L = int(min(61, v * 0.9)) | 1
    ker = np.zeros((L, L), np.float32); cx = L // 2
    ux, uy = dx / v, dy / v
    for i in range(L):
        q = i - cx; ker[int(round(cx + uy * q)), int(round(cx + ux * q))] = 1.0
    ker /= ker.sum()
    sm = cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    sm = cv2.filter2D(sm, -1, cv2.resize(ker, (L // 2 | 1, L // 2 | 1), interpolation=cv2.INTER_AREA) / max(1e-6, cv2.resize(ker, (L // 2 | 1, L // 2 | 1), interpolation=cv2.INTER_AREA).sum()))
    return cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR) * 0.85 + img * 0.15

# ================================================================= frame
def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080; clean = C.STATE["clean"]
    cam = cam_at(t, vert); sx, sy = shake(t, W, H)
    M = cam.M(W, H, sx, sy)
    img = draw_wall(W, H, M)
    old_tag(img, M, W, H)                                                                              # an old, faded tag
    for f in ALL:
        if f["t"] - 0.16 > t: break
        draw_flyer(img, f, M, t, W, H)
    chart_dyn(img, t, M, W, H)
    heads, s = None, None
    if t >= T_SPRAY0: heads, s = spray(img, t, M, W, H)
    if T_OPTSTAMP - 0.06 <= t < 31.0:                                                   # OPT OUT stamped onto the cookie notice
        sl = slam(t, T_OPTSTAMP)
        if sl: world_strip(img, M, "OPT OUT", "red", *notice_pt(0.52, 0.70), 0.20, -0.10, sl[0], sl[1])
    img *= light(W, H, t)
    ck = chorus_k(t)
    if ck:
        k, c0, c1 = ck; w = sstep(c0, c0 + 0.25, t) * (1 - sstep(c1 - 0.35, c1, t))
        tint = np.array([0.66, 0.36, 0.33], np.float32) if k != 1 else np.array([0.72, 0.45, 0.30], np.float32)
        img *= 1 - w * (1 - tint) * (1 - 0.35 * bp(t, 5))
    # camera motion blur (whips between flyers)
    Mp = cam_at(t - 1 / 30, vert).M(W, H, *shake(t - 1 / 30, W, H))
    img = motion_blur(img, M, Mp, W, H)
    crowd(img, t, W, H, crowd_amt(t))
    if heads: spray_can(img, t, M, heads[-1], s, W, H)
    for f in VERSE:
        if -0.05 < t - f["t"] < 0.8: brush_layer(img, f, t, M, W, H)
    if 23.5 < t < 25.75:                                                               # the joke: the reject link is size two
        o = sstep(23.5, 23.8, t) * (1 - sstep(25.55, 25.75, t))
        rx_, ry_ = notice_pt(0.875, 0.865)
        if not vert:
            world_text(img, M, "the reject button", MARKER, rx_ - 0.20, ry_ + 0.034, 0.027, RED, o)
            a = to_screen(M, rx_ - 0.105, ry_ + 0.024); b = to_screen(M, rx_ - 0.022, ry_ + 0.006)
        else:
            world_text(img, M, "the reject button", MARKER, rx_ - 0.095, ry_ + 0.062, 0.024, RED, o)
            a = to_screen(M, rx_ - 0.05, ry_ + 0.045); b = to_screen(M, rx_ - 0.008, ry_ + 0.010)
        cv2.arrowedLine(img, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), (RED * o + 0).tolist(), max(2, int(5 * ts)), cv2.LINE_AA, tipLength=0.3)
    if not clean:
        chant(img, t, W, H); ransom(img, t, W, H); draw_hooks(img, t, W, H)
        lk = max(win(t, S["V1"]["s"] - 0.3, S["CH1"]["s"] - 0.2, 0.3, 0.2), win(t, S["V2"]["s"] - 0.3, S["CH2"]["s"] - 0.2, 0.3, 0.2))
        if lk > 0.01:
            bk = (W, H, "band")
            if bk not in _PPL:
                yy = np.arange(H, dtype=np.float32); yc = H * (0.70 if vert else 0.835)
                _PPL[bk] = np.exp(-((yy - yc) / (H * (0.055 if vert else 0.085))) ** 2)[:, None, None].astype(np.float32)
            img *= 1 - 0.58 * lk * _PPL[bk]
        C.overlay_lyrics(img, t, W, H, TM, active=hexc('ffb36b'), glow=RED, skip=lambda L: L["sec"] not in ("V1", "V2"))
        C.subscribe_pill(img, t, W, H, S["V2"]["s"] + 0.3, 5.5)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "Unsubscribe from them.", sub_line="Subscribe here instead: a new song every week",
                     title="Rage Against the Machine Learning", accent=RED)
    gl = 0.0
    if 98.6 < t < 101.3: gl += 0.25 * sstep(98.6, 99.2, t) + 0.6 * sstep(100.6, 101.2, t)
    if 0 <= t - LINES[32]["wt"][3] < 0.25: gl += 0.5
    return C.finish(img, t, fi, DUR, flash=flash_at(t), flash_col=np.array([1.0, 0.92, 0.85], np.float32), glitch_amt=gl, ca=0.0016)
