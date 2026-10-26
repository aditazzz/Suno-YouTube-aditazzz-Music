import numpy as np, cv2, json, math, re, os
from studio import core as CORE
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageDraw, ImageFont

FPS = 30
DUR = json.load(open(os.path.join(HERE, 'build', 'beats.json')))['duration']
F_INTER, F_INTER_L, F_DISP, F_DISPB, F_MONO, F_MONOB = CORE.F_INTER, CORE.F_INTER_L, CORE.F_DISP, CORE.F_DISPB, CORE.F_MONO, CORE.F_MONOB

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sstep(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else float(x >= a)
    return t * t * (3 - 2 * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_io(t): t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10)
def win(t, a, b, fi=0.3, fo=0.3): return sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t))
def lerp(a, b, t): return a + (b - a) * t
def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

ICE = hexc('5fd8ff'); ICE2 = hexc('a8f0ff'); WHITE = np.array([1, 1, 1], np.float32)
RED = hexc('ff2a3d'); MAG = hexc('ff3fbf'); VIO = hexc('8b5cff'); GOLD = hexc('ffc35a')
TEAL = hexc('2bffc6'); NAVY = hexc('050a1c'); IVORY = hexc('f3ead8'); AMBER = hexc('ff8a3d')

# ---------------------------------------------------------------- timing data
LINES = json.load(open(os.path.join(HERE, 'build', 'timed.json')))
_bt = json.load(open(os.path.join(HERE, 'build', 'beats.json')))
BEATS = np.array(_bt['beats'])
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

def line_t(sub, nth=0):
    hits = [L for L in LINES if sub.lower() in L['text'].lower()]
    return hits[nth]['s']
def word_t(sub, word, nth=0):
    hits = [L for L in LINES if sub.lower() in L['text'].lower()]
    L = hits[nth]
    for w, t in zip(L['words'], L['wt']):
        if norm(word) == norm(w): return t
    raise KeyError(word)
def snap(t, tol=0.32):
    i = np.argmin(abs(BEATS - t))
    return float(BEATS[i]) if abs(BEATS[i] - t) < tol else t

def beat_pulse(t, k=7.0):
    i = np.searchsorted(BEATS, t) - 1
    if i < 0: return 0.0
    return math.exp(-(t - BEATS[i]) * k)
def beat_index(t): return int(np.searchsorted(BEATS, t))

# key moments
T_TYPE = word_t("Ran DROP", "DROP") - 0.15
T_DROP = word_t("seal my fate", "seal")
T_REMEMBER = line_t("Then I remembered")
T_PRE = line_t("just sat there")
T_RET = line_t("Check retention")
T_RUN = line_t("Run one command")
T_CH1 = snap(line_t("UNDROP", 0) - 0.15)
T_EVERY1 = line_t("Everything I swore", 0)
T_GAVE_END1 = LINES[[i for i, L in enumerate(LINES) if L['sec'] == 'CH1'][-1]]['s']
T_V2 = line_t("Now I clone")
T_WRECK = line_t("wreck the clone")
T_PROD = line_t("Prod's not")
T_WARE = line_t("warehouse isn't")
T_SUSP = line_t("you suspend")
T_QUERY = line_t("send a query")
T_CALL = line_t("call again")
T_SORRY = line_t("sorry, just")
T_BIZ = line_t("three-business")
T_OFF = line_t("take this offline")
T_ROWS = word_t("rows rolled back", "rows")
T_PRE2 = line_t("Auto-suspend")
T_BILL = line_t("bill me")
T_CH2 = snap(line_t("UNDROP", 3) - 0.15)
T_BRIDGE = line_t("read the docs")
T_HIGH = line_t("highlighted")
T_ONEDAY = line_t("One day by default")
T_NINETY = line_t("up to ninety")
T_TT = line_t("Time Travel lets")
T_BUILT = line_t("somebody built")
T_TRUST = line_t("what trust is")
T_ONLYU = line_t("only you")
T_PRICING = line_t("consumption pricing")
T_BUILD = line_t("You remembered what")
T_BACKUP = line_t("backup I can trust")
T_FINAL = snap(line_t("UNDROP", 5) - 0.15)
T_OUTRO = line_t("Snowflake", -1) if False else [L for L in LINES if L['sec'] == 'OUTRO'][0]['s']
T_HEALTHY = line_t("healthiest")
T_THERAPIST = line_t("therapist")

SECTIONS = [("INTRO", 0, 2.2), ("V1", 2.2, T_PRE), ("PRE", T_PRE, T_CH1), ("CH1", T_CH1, T_V2 - 1.8),
            ("V2", T_V2 - 1.8, T_PRE2 - 0.5), ("PRE2", T_PRE2 - 0.5, T_CH2), ("CH2", T_CH2, T_BRIDGE - 0.6),
            ("BRIDGE", T_BRIDGE - 0.6, T_BUILD), ("BUILD", T_BUILD, T_FINAL), ("FINAL", T_FINAL, T_OUTRO - 0.3),
            ("OUTRO", T_OUTRO - 0.3, DUR + 1)]
def section(t):
    for n, a, b in SECTIONS:
        if a <= t < b: return n
    return "OUTRO"

# UNDROP stamp times (any word 'undrop')
STAMPS = []
for L in LINES:
    for w, tt in zip(L['words'], L['wt']):
        if norm(w) == 'undrop': STAMPS.append(snap(tt - 0.12, 0.25))
STAMPS = sorted(STAMPS)
_fix = []
for s in STAMPS:
    if _fix and s - _fix[-1] < 0.3:
        nb = BEATS[BEATS > _fix[-1] + 0.3]; s = float(nb[0])
    _fix.append(s)
STAMPS = _fix
def last_stamp(t):
    i = np.searchsorted(STAMPS, t) - 1
    return (STAMPS[i], i) if i >= 0 else (None, -1)

# ---------------------------------------------------------------- geometry: the table / shards
rng = np.random.default_rng(7)
R, C = 26, 12
CW, CH = 0.36, 0.17
N = R * C
ri, ci = np.divmod(np.arange(N), C)
G = np.stack([(ci - (C - 1) / 2) * CW, ((R - 1) / 2 - ri) * CH, np.zeros(N)], 1).astype(np.float32)
LOC = np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]], np.float32) * np.array([CW * 0.44, CH * 0.38, 1], np.float32)
# header row is brighter
IS_HDR = (ri == 0)

# explosion velocities (impact slightly above center, toward camera)
d = G - np.array([0.3, 0.6, -0.4], np.float32)
dn = d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-6)
mag = rng.uniform(1.8, 6.5, N)[:, None]
V = (dn * mag + rng.normal(0, 1.0, (N, 3)) + np.array([0, 0.6, -1.2])).astype(np.float32)
AX = rng.normal(0, 1, (N, 3)); AX /= np.linalg.norm(AX, axis=1, keepdims=True)
OM = rng.uniform(1.5, 6.0, N) * rng.choice([-1, 1], N)

def rodrigues(axis, ang):
    # axis (N,3), ang (N,) -> (N,3,3)
    k = axis; c = np.cos(ang)[:, None, None]; s = np.sin(ang)[:, None, None]
    K = np.zeros((len(k), 3, 3), np.float32)
    K[:, 0, 1] = -k[:, 2]; K[:, 0, 2] = k[:, 1]; K[:, 1, 0] = k[:, 2]
    K[:, 1, 2] = -k[:, 0]; K[:, 2, 0] = -k[:, 1]; K[:, 2, 1] = k[:, 0]
    I = np.eye(3, dtype=np.float32)[None]
    return I + s * K + (1 - c) * (K @ K)

# snowflake target positions
def make_snowflake(n, scale=1.0, seed=3):
    r = np.random.default_rng(seed)
    pts = []; angs = []
    per = n // 6
    for k in range(6):
        th = k * math.pi / 3 + math.pi / 2
        u = np.array([math.cos(th), math.sin(th)]); v = np.array([-u[1], u[0]])
        arm = []
        # spine
        for s in np.linspace(0.45, 3.6, 22): arm.append((u * s, th))
        # branches
        for (b0, bl, nb) in [(1.15, 1.25, 7), (2.0, 1.0, 6), (2.75, 0.7, 4), (3.25, 0.38, 2)]:
            for sgn in (-1, 1):
                bd = u * math.cos(math.pi / 3) + sgn * v * math.sin(math.pi / 3)
                bth = math.atan2(bd[1], bd[0])
                for s in np.linspace(0.18, bl, nb): arm.append((u * b0 + bd * s, bth))
        arm = arm[:per]
        while len(arm) < per: arm.append((u * r.uniform(0.3, 0.6), th))
        for p, a in arm: pts.append(p); angs.append(a)
    while len(pts) < n:
        th = r.uniform(0, 2 * math.pi); rr = 0.25
        pts.append(np.array([math.cos(th), math.sin(th)]) * rr); angs.append(th)
    P = np.array(pts) * scale
    S = np.concatenate([P, r.normal(0, 0.05, (n, 1))], 1).astype(np.float32)
    return S, np.array(angs, np.float32)
S_POS, S_ANG = make_snowflake(N, 1.15)
# random permutation so cells fly across (more dramatic)
PERM = np.random.default_rng(11).permutation(N)
S_POS = S_POS[PERM]; S_ANG = S_ANG[PERM]

# frost points along the snowflake (dense dust for crystal look)
def frost_points(n=9000, scale=1.15, seed=5):
    r = np.random.default_rng(seed)
    segs = []
    for k in range(6):
        th = k * math.pi / 3 + math.pi / 2
        u = np.array([math.cos(th), math.sin(th)]); v = np.array([-u[1], u[0]])
        segs.append((u * 0.3, u * 3.75))
        for (b0, bl) in [(1.15, 1.35), (2.0, 1.1), (2.75, 0.8), (3.25, 0.45)]:
            for sgn in (-1, 1):
                bd = u * 0.5 + sgn * v * math.sin(math.pi / 3)
                segs.append((u * b0, u * b0 + bd * bl))
    # hexagon core
    for k in range(6):
        a1 = k * math.pi / 3; a2 = (k + 1) * math.pi / 3
        segs.append((np.array([math.cos(a1), math.sin(a1)]) * 0.62, np.array([math.cos(a2), math.sin(a2)]) * 0.62))
        segs.append((np.array([math.cos(a1), math.sin(a1)]) * 0.3, np.array([math.cos(a2), math.sin(a2)]) * 0.3))
    L = np.array([np.linalg.norm(b - a) for a, b in segs]); p = L / L.sum()
    idx = r.choice(len(segs), n, p=p); s = r.random(n)
    A = np.array([segs[i][0] for i in idx]); B = np.array([segs[i][1] for i in idx])
    P = A + (B - A) * s[:, None]
    tang = (B - A); tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    P += np.stack([-tang[:, 1], tang[:, 0]], 1) * r.normal(0, 0.035, (n, 1))
    out = np.concatenate([P, r.normal(0, 0.03, (n, 1))], 1) * scale
    return out.astype(np.float32), r.random(n).astype(np.float32)
FROST, FROST_R = frost_points()

# ---------------------------------------------------------------- physics time warp
_dt = 1 / 240
_tg = np.arange(0, DUR + 2, _dt)
def _speed(t):
    if t < T_DROP: return 0.0
    if t < T_REMEMBER: return 1.0
    if t < T_PRE: return lerp(1.0, 0.1, sstep(T_REMEMBER, T_PRE, t))
    return 0.05
_tau = np.cumsum([_speed(t) for t in _tg]) * _dt
def tau_explode(t):
    """physics time for the first explosion, includes reverse at UNDROP."""
    if t < T_DROP: return 0.0
    tf = float(np.interp(min(t, T_CH1), _tg, _tau))
    if t < T_CH1: return tf
    return tf * (1 - ease_io((t - T_CH1) / 1.25))

# ---------------------------------------------------------------- camera
class Cam:
    def __init__(s, pos, tgt, roll=0.0, fov=1.0):
        s.pos = np.array(pos, np.float32); s.tgt = np.array(tgt, np.float32); s.roll = roll; s.fov = fov
def orbit(yaw, pitch, dist, tgt=(0, 0, 0), roll=0.0, fov=1.0):
    tgt = np.array(tgt, np.float32)
    p = tgt + dist * np.array([math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)], np.float32)
    return Cam(p, tgt, roll, fov)

def project(P, cam, W, H):
    f = cam.pos; z = cam.tgt - f; z /= np.linalg.norm(z)
    up = np.array([math.sin(cam.roll), math.cos(cam.roll), 0], np.float32)
    x = np.cross(up, z); x /= np.linalg.norm(x); y = np.cross(z, x)
    Q = P - f
    cx = Q @ x; cy = Q @ y; cz = Q @ z
    foc = min(W, H) * 1.25 * cam.fov
    cz_s = np.maximum(cz, 1e-3)
    u = W / 2 + foc * cx / cz_s; v = H / 2 - foc * cy / cz_s
    return u, v, cz

# ---------------------------------------------------------------- text sprites
_FONTS = {}
def font(path, size):
    k = (path, size)
    if k not in _FONTS: _FONTS[k] = ImageFont.truetype(path, size)
    return _FONTS[k]
_SPR = {}
def sprite(text, path, size, glow=0, track=0):
    k = (text, path, size, glow, track)
    if k in _SPR: return _SPR[k]
    f = font(path, size)
    if track:
        ws = [f.getbbox(ch)[2] for ch in text]
        w = int(sum(ws) + track * (len(text) - 1)) + 4
    else:
        bb = f.getbbox(text); w = bb[2] + 4
    asc, desc = f.getmetrics(); h = asc + desc + 4
    pad = glow * 3
    im = Image.new('L', (w + pad * 2, h + pad * 2), 0); d = ImageDraw.Draw(im)
    if track:
        x = pad
        for ch, cw in zip(text, ws): d.text((x, pad), ch, font=f, fill=255); x += cw + track
    else: d.text((pad, pad), text, font=f, fill=255)
    a = np.asarray(im, np.float32) / 255
    g = cv2.GaussianBlur(a, (0, 0), glow) if glow else None
    _SPR[k] = (a, g, pad)
    if len(_SPR) > 4000: _SPR.clear()
    return _SPR[k]

def blit(img, spr, x, y, color, op=1.0, glow_op=0.0, glow_color=None, anchor='lt', scale=1.0):
    a, g, pad = spr
    if scale != 1.0:
        a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        if g is not None: g = cv2.resize(g, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        pad = pad * scale
    h, w = a.shape
    if anchor == 'c': x -= w / 2; y -= h / 2
    elif anchor == 'ct': x -= w / 2; y -= pad
    else: x -= pad; y -= pad
    x = int(round(x)); y = int(round(y))
    H, W = img.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    sa = a[y0 - y:y1 - y, x0 - x:x1 - x][..., None]
    reg = img[y0:y1, x0:x1]
    if g is not None and glow_op > 0:
        sg = g[y0 - y:y1 - y, x0 - x:x1 - x][..., None]
        reg += sg * glow_op * (glow_color if glow_color is not None else color)
    reg *= (1 - sa * op)
    reg += sa * op * color

def text_w(text, path, size):
    return font(path, size).getlength(text)
