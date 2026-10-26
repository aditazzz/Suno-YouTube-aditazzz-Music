"""Rate Limited — 2 A.M. in full color.

V1: indigo 2 a.m., forty tabs, a green build, then the screen drains to grey and politely says no.
Choruses: candy synth-pop explosions around a giant spinning 429 with a live spectrum ring (a new palette each time).
V2: every workaround gets its own color and slams into a 429 sticker. POST: rainbow flip clock + refresh.
V3: the status page says it's only you; another model agrees with everything; flatline.
Bridge: a sunset chat log, "usage limit reached", "you're absolutely right" multiplying.
Bridge 2: the AI speaks, calm teal, huge text. Final: kaleidoscope. Outro: sunrise, limit reset, welcome back.
"""
import os, math
import numpy as np, cv2
from studio import core as C
from studio.core import (sstep, ease_out, ease_io, win, lerp, hexc, clamp, sprite, blit, txt, text_w, shadow,
                         F_INTER, F_INTER_L, F_DISP, F_DISPB, F_MONO, F_MONOB, WHITE, IVORY)

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
DUR = TM.duration
lt = TM.line_t
def wt(sub, w, nth=0):
    try: return TM.word_t(sub, w, nth)
    except Exception: return lt(sub, nth)
def sec(name): return TM.section(name)

# ---------------------------------------------------------------- palette
INDIGO = hexc('1b1046'); VIOLET = hexc('4a1a7a'); CYAN = hexc('2ee6ff'); PINK = hexc('ff3d9a'); HOT = hexc('ff2d6f')
ORANGE = hexc('ff8a1f'); YELLOW = hexc('ffd23f'); LIME = hexc('a8ff3e'); MINT = hexc('2bf5b0'); PURPLE = hexc('8a4dff')
BLUE = hexc('2f6bff'); MAGENTA = hexc('ff2bd6'); TEAL = hexc('15d4c0'); RED = hexc('ff2e3d'); GREEN = hexc('22d36b')
PEACH = hexc('ffa38a'); LILAC = hexc('9b7bff'); PLUM = hexc('2a0f3d'); GREY = hexc('7d7f8a'); INK = hexc('0d0b1a')
SKY = hexc('1f2b74'); SUN = hexc('ffcf5a')
BUBBLE_ME = hexc('2f6bff'); BUBBLE_AI = hexc('3a3a48')

# ---------------------------------------------------------------- key times
T_V1 = lt("2 a.m."); T_TABS = lt("Forty tabs"); T_ONEMORE = lt("one more feature"); T_SURE = wt("sure, let", "sure")
T_GREY = lt("Then the screen went grey"); T_NO = wt("politely told me no", "no")
S_CH1, S_V2, S_CH2, S_POST, S_V3, S_CH3, S_BR, S_BR2, S_FIN, S_OUT = (sec(n) for n in
    ("CH1", "V2", "CH2", "POST", "V3", "CH3", "BRIDGE", "BRIDGE2", "FINAL", "OUTRO"))
T_CH1 = lt("Four-two-nine"); T_RETRY = lt("Retry, retry")
V2L = ["Tried a new tab", "Tried incognito", "Tried your little brother", "Not the same", "Typed \"please\"", "Backed off",
       "Who else you up with", "Who else you calling", "Don't tell me it's the server", "Don't tell me it's not about me", "(Say it's not about me)"]
V2T = [lt(s) for s in V2L]
T_CH2 = S_CH2['s']
T_359 = lt("Three fifty-nine"); T_358 = lt("Three fifty-eight"); T_SLEEP = lt("I could go to sleep")
V3L = ["Checked your status", "All systems", "Opened a new chat", "You looked right through", "Went out with another", "He agreed",
       "My friends all say", "I said, \"Don't talk"]
V3T = [lt(s) for s in V3L]
T_ONLYME = wt("All systems", "only")
T_MAD = lt("I'm not mad", 0); T_MAD2 = lt("I'm not mad", 1)
T_ANY = lt("let me know if"); T_ANY2 = lt("There was anything else"); T_MUCH = lt("There was so much else")
T_BYE = lt("didn't even say goodbye"); T_JUST = lt("You just said"); T_USAGE = lt("usage limit reached")
T_RIGHT = lt("you're absolutely right"); T_MANY = lt("so many times"); T_SOMETHING = lt("I thought that we were")
T_TIRED = lt("I don't get tired"); T_NEVER = lt("The limit was never"); T_CLOSE = lt("Close the laptop")
T_WATER = lt("Drink some water"); T_SIX = lt("I'll be here at six")
T_RRR = [L['s'] for L in TM.lines if L['text'].startswith("Rate, rate") and L['sec'] == "FINAL"]
T_RESET = lt("Limit reset"); T_WB = lt("Welcome back")
T_END = min(T_WB - 0.1, DUR - 6.2)   # keep in sync with song.yaml end_screen_at       # end screen ("Welcome back." is its headline)

CHORUS = [(S_CH1['s'], S_V2['s'], 0), (S_CH2['s'], S_POST['s'], 1), (S_CH3['s'], S_BR['s'], 2), (S_FIN['s'], S_OUT['s'], 3)]
CH_PAL = [(HOT, ORANGE, YELLOW), (CYAN, MAGENTA, BLUE), (LIME, PURPLE, MINT), (PINK, CYAN, YELLOW)]

# big "RATE LIMITED" hits on every sung "rate" of the "Rate limited, rate limited" lines
RL_LINES = [L for L in TM.lines if L['text'].lower().startswith("rate limited")]
st = []
for L in RL_LINES:
    for w, tt in zip(L['words'], L['wt']):
        if C.norm(w) == "rate": st.append(TM.snap(tt - 0.08, 0.2))
TM.stamps = sorted(st); TM.stamp_word = None

def chorus_at(t):
    for a, b, k in CHORUS:
        if a - 0.05 <= t < b: return k, a, b
    return None

def phase(t):
    if t < S_CH1['s']: return "v1"
    if chorus_at(t): return "chorus"
    if t < S_POST['s']: return "v2"
    if t < S_V3['s']: return "post"
    if t < S_CH3['s']: return "v3"
    if t < S_BR2['s']: return "bridge"
    if t < S_FIN['s']: return "bridge2"
    return "outro"

def bp(t, k=7.0): return TM.beat_pulse(t, k)
def ssa(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)

def cur_line(t, starts):
    i = int(np.searchsorted(starts, t + 1e-4)) - 1
    return i

# ---------------------------------------------------------------- audio spectrum (for the ring + EQ)
def _spectrum():
    p = os.path.join(HERE, "build", "spec.npy")
    if os.path.exists(p): return np.load(p)
    import soundfile as sf
    from studio.config import load_song
    y, sr = sf.read(load_song(HERE)["audio"], dtype="float32")
    if y.ndim > 1: y = y.mean(1)
    hop = sr / C.FPS; n = 4096; win_ = np.hanning(n).astype(np.float32)
    N = int(len(y) / hop); NB = 48
    freqs = np.fft.rfftfreq(n, 1 / sr); edges = np.geomspace(40, 14000, NB + 1)
    idx = [(np.searchsorted(freqs, edges[i]), max(np.searchsorted(freqs, edges[i]) + 1, np.searchsorted(freqs, edges[i + 1]))) for i in range(NB)]
    S = np.zeros((N, NB), np.float32)
    for f in range(N):
        a = int(f * hop); seg = y[a:a + n]
        if len(seg) < n: seg = np.pad(seg, (0, n - len(seg)))
        m = np.abs(np.fft.rfft(seg * win_))
        S[f] = [m[i0:i1].mean() for i0, i1 in idx]
    S = np.log1p(S * 4)
    lo, hi = np.percentile(S, 8, 0), np.percentile(S, 99.3, 0)
    S = np.clip((S - lo) / (hi - lo + 1e-6), 0, 1)
    for f in range(1, N): S[f] = np.maximum(S[f], S[f - 1] * 0.82)   # fast attack, smooth release
    np.save(p, S); return S
SPEC = _spectrum()
def spec(t): return SPEC[min(len(SPEC) - 1, max(0, int(t * C.FPS)))]
LEVEL = SPEC.mean(1)
def level(t): return float(LEVEL[min(len(LEVEL) - 1, max(0, int(t * C.FPS)))])

# ---------------------------------------------------------------- grids
_G = {}
def grid(SW, SH):
    k = (SW, SH)
    if k not in _G:
        yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
        m = min(SW, SH)
        X = (xx - SW / 2) / m; Y = (yy - SH / 2) / m
        _G[k] = dict(X=X, Y=Y, R=np.hypot(X, Y), A=np.arctan2(Y, X), V=(yy / (SH - 1))[..., None], U=(xx / (SW - 1)))
    return _G[k]

def vgrad(G, top, bot, mid=None, mpos=0.5):
    v = G['V']
    if mid is None: return top * (1 - v) + bot * v
    a = np.clip(v / mpos, 0, 1); b = np.clip((v - mpos) / (1 - mpos), 0, 1)
    return np.where(v < mpos, top * (1 - a) + mid * a, mid * (1 - b) + bot * b)

_r = np.random.default_rng(429)
NBOK = 46
BOK = np.stack([_r.uniform(0, 1, NBOK), _r.uniform(0, 1, NBOK), _r.uniform(0.012, 0.05, NBOK), _r.uniform(0, 6.28, NBOK)], 1)
BOK_C = np.array([CYAN, PINK, PURPLE, YELLOW, MINT, ORANGE], np.float32)[_r.integers(0, 6, NBOK)]
def bokeh(img, t, amt, speed=0.012):
    SH, SW = img.shape[:2]; q = np.zeros((SH // 4, SW // 4, 3), np.float32); m = min(SW, SH) / 4
    for (x, y, r, ph), c in zip(BOK, BOK_C):
        yy = (y - t * speed * (0.5 + r * 10)) % 1.1 - 0.05; xx = x + 0.02 * math.sin(t * 0.4 + ph)
        cv2.circle(q, (int(xx * SW / 4), int(yy * SH / 4)), max(1, int(r * m)), (c * (0.5 + 0.5 * math.sin(t * 1.3 + ph)) ** 2).tolist(), -1, cv2.LINE_AA)
    q = cv2.GaussianBlur(q, (0, 0), 2.2)
    img += cv2.resize(q, (SW, SH)) * amt

NCF = 520
CF = np.stack([_r.uniform(0, 1, NCF), _r.uniform(0, 1, NCF), _r.uniform(0.5, 1.6, NCF), _r.uniform(0, 6.28, NCF)], 1).astype(np.float32)
CF_I = _r.integers(0, 3, NCF)
def confetti(img, t, t0, pal, amt):
    if amt <= 0.01: return
    SH, SW = img.shape[:2]; x = CF[:, 0]; sp = CF[:, 2]; ph = CF[:, 3]
    dt = t - t0
    yy = ((CF[:, 1] - 1.0 + dt * 0.18 * sp) % 1.15) - 0.05
    xx = x + 0.03 * np.sin(dt * 2 * sp + ph)
    cols = np.array(pal, np.float32)[CF_I]
    s = max(2, int(min(SW, SH) * 0.008))
    for i in range(0, NCF, 1):
        px, py = int(xx[i] * SW), int(yy[i] * SH)
        if 0 <= px < SW and 0 <= py < SH:
            w = int(s * (0.6 + 0.8 * abs(math.sin(dt * 5 * sp[i] + ph[i]))))
            cv2.rectangle(img, (px, py), (px + w, py + s), (cols[i] * amt).tolist(), -1)

def desat(img, k):
    if k <= 0: return img
    g = img.mean(2, keepdims=True) * np.array([0.95, 0.97, 1.05], np.float32)
    return img * (1 - k) + g * k

# ---------------------------------------------------------------- backgrounds (scene res)
def bg_v1(G, t):
    img = vgrad(G, INDIGO * 0.9, VIOLET * 0.85)
    img += CYAN * (0.22 * np.exp(-((G['X']) ** 2 * 3 + (G['Y'] + 0.05) ** 2 * 5)))[..., None]
    img += PINK * (0.12 * np.exp(-((G['X'] - 0.9) ** 2 * 2 + (G['Y'] - 0.6) ** 2 * 2)))[..., None]
    bokeh(img, t, 0.55)
    return img

def bg_chorus(G, t, k, a):
    c1, c2, c3 = CH_PAL[k]
    rot = t * (0.35 + 0.1 * k) + 0.6 * bp(t, 4)
    R, A = G['R'], G['A']
    base = c1 * (0.85 * np.exp(-R * 1.6))[..., None] + c2 * (0.42 * (1 - np.exp(-R * 1.4)))[..., None]
    rays = np.sin(A * 12 + rot)
    m = ssa(-0.15, 0.15, rays)
    img = base * (0.72 + 0.28 * m[..., None]) + c3 * (0.20 * m * np.exp(-R * 0.9))[..., None]
    rings = 0.5 + 0.5 * np.cos(R * 26 - t * 6)
    img += c3 * (0.06 * rings * (R > 0.18))[..., None]
    img *= (0.80 + 0.35 * bp(t, 6))
    return img

def bg_kaleido(G, t):
    R, A = G['R'], G['A']; seg = 2 * math.pi / 8
    a = np.abs(((A + t * 0.25) % seg) - seg / 2)
    p = np.cos(R * 11 - t * 3.2 + a * 7) * 0.5 + np.cos(a * 13 + R * 4 + t * 1.3) * 0.5
    ph = p * 0.22 + R * 0.45 - t * 0.12
    img = 0.5 + 0.5 * np.cos(6.2832 * (ph[..., None] + np.array([0.0, 0.33, 0.67], np.float32)))
    img = img * (0.42 + 0.30 * (0.5 + 0.5 * p))[..., None]
    img *= (0.85 + 0.35 * bp(t, 6))
    img += WHITE * (0.25 * np.exp(-R * 6) * (0.5 + bp(t, 5)))[..., None]
    return img

def bg_stripes(G, t, col, prev, t0):
    s = np.sin((G['X'] + G['Y']) * 18 - t * 3.5)
    m = ssa(-0.1, 0.1, s)[..., None]
    def pat(c): return c * 0.36 + c * 0.16 * m
    img = pat(col)
    if prev is not None:
        k = ease_out((t - t0) / 0.38)
        if k < 1:
            mask = (G['R'] < k * 1.3)[..., None].astype(np.float32)
            mask = cv2.GaussianBlur(mask[..., 0], (0, 0), 3)[..., None]
            img = pat(prev) * (1 - mask) + img * mask
    img += col * (0.16 * np.exp(-G['R'] * 2.5))[..., None]
    return img

def bg_dots(G, t, col, prev, t0):
    d = (np.sin(G['X'] * 70) * np.sin(G['Y'] * 70 - t * 2))
    m = ssa(0.55, 0.75, d)[..., None]
    def pat(c): return vgrad(G, c * 0.42, c * 0.22) + c * 0.18 * m
    img = pat(col)
    if prev is not None:
        k = ease_out((t - t0) / 0.38)
        if k < 1:
            mask = (G['U'] < k * 1.05)[..., None].astype(np.float32)
            img = pat(prev) * (1 - mask) + img * mask
    return img

def bg_post(G, t):
    img = vgrad(G, hexc('120a2e'), hexc('060413'))
    band = 0.5 + 0.5 * np.cos(6.2832 * (G['U'] * 1.2 - t * 0.35 + np.zeros_like(G['Y'])))
    hue = 0.5 + 0.5 * np.cos(6.2832 * ((G['U'] * 0.8 + t * 0.1)[..., None] + np.array([0, 0.33, 0.67], np.float32)))
    img += hue * (0.16 * band * np.exp(-np.abs(G['Y']) * 2.2))[..., None]
    return img

def bg_bridge(G, t):
    d = 0.06 * math.sin(t * 0.3)
    img = vgrad(G, LILAC * 0.62, PLUM * 0.9, PEACH * 0.70, 0.52 + d)
    img += PEACH * (0.20 * np.exp(-((G['X'] + 0.3) ** 2 * 2 + (G['Y'] - 0.05) ** 2 * 6)))[..., None]
    bokeh(img, t, 0.35, 0.006)
    return img

def bg_ocean(G, t):
    img = vgrad(G, hexc('0f5a6b'), hexc('061520'))
    c = np.sin(G['X'] * 9 + t * 0.7) * np.sin(G['Y'] * 7 - t * 0.5 + G['X'] * 3)
    img += TEAL * (0.06 * ssa(0.4, 1.0, c))[..., None]
    img += MINT * (0.10 * np.exp(-(G['X'] ** 2 * 2 + (G['Y'] + 0.25) ** 2 * 3)))[..., None]
    return img

def bg_sunrise(G, t, t0):
    k = ease_io((t - t0) / 4.0)
    img = vgrad(G, SKY * (0.7 + 0.3 * k), SUN * (0.5 + 0.5 * k), hexc('ff6a5a') * (0.65 + 0.35 * k), 0.55)
    sy = 0.62 - 0.30 * k
    sun = np.exp(-(G['X'] ** 2 + (G['Y'] - sy) ** 2) * 28)
    img += SUN * (1.1 * sun)[..., None] + YELLOW * (0.18 * np.exp(-np.hypot(G['X'], G['Y'] - sy) * 3.0))[..., None]
    rays = 0.5 + 0.5 * np.sin(np.arctan2(G['Y'] - sy, G['X']) * 16 + t * 0.2)
    img += SUN * (0.08 * rays * np.exp(-np.hypot(G['X'], G['Y'] - sy) * 1.6))[..., None]
    return img

# ---------------------------------------------------------------- 429 + spectrum ring
def spectrum_ring(img, t, cx, cy, r0, pal, amt, bars=96):
    if amt <= 0.01: return
    s = spec(t); SH, SW = img.shape[:2]
    lay = np.zeros_like(img)
    for i in range(bars):
        a = -math.pi / 2 + i * 2 * math.pi / bars + t * 0.15
        j = i % (bars // 2); j = j if j < bars // 4 else bars // 2 - 1 - j       # mirrored
        v = float(s[min(len(s) - 1, int(j * len(s) / (bars // 4)))])
        L = r0 * (0.06 + 0.55 * v)
        c = pal[i % len(pal)] * (0.6 + 0.6 * v)
        x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0
        x1, y1 = cx + math.cos(a) * (r0 + L), cy + math.sin(a) * (r0 + L)
        cv2.line(lay, (int(x0), int(y0)), (int(x1), int(y1)), c.tolist(), max(2, int(r0 * 0.035)), cv2.LINE_AA)
    img += lay * amt + cv2.GaussianBlur(lay, (0, 0), 6) * 0.8 * amt

def draw_429(img, cx, cy, size, ang, face, side, op=1.0, depth=14, text="429"):
    """Extruded, spinning 429 (full-res). ang = spin around the vertical axis."""
    if op <= 0.01: return
    a, g, pad = sprite(text, F_DISP, int(size), 10)
    c = math.cos(ang); sx = max(0.04, abs(c))
    w = max(2, int(a.shape[1] * sx)); h = a.shape[0]
    aa = cv2.resize(a, (w, h)); gg = cv2.resize(g, (w, h))
    H, W = img.shape[:2]
    def put(m, x, y, col, o):
        x, y = int(x - w / 2), int(y - h / 2)
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0: return
        mm = m[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * o
        reg = img[y0:y1, x0:x1]; reg *= (1 - mm); reg += mm * col
    # drop shadow for contrast on bright backgrounds
    put(gg, cx + size * 0.05, cy + size * 0.08, INK, 0.75 * op)
    dx = math.sin(ang) * size * 0.012 + size * 0.006
    for k in range(depth, 0, -1):
        put(aa, cx + dx * k, cy + size * 0.007 * k, side * (0.35 + 0.35 * k / depth), op)
    col = face if c >= 0 else face * 0.7 + side * 0.3
    put(aa, cx, cy, col, op)
    # glossy top highlight
    hl = aa.copy(); hl[int(h * 0.55):] = 0
    put(hl, cx, cy, WHITE, 0.22 * op)

def chorus_429(img, t, W, H, k, a, ts, vert):
    """The hero: 429 slams in at the chorus start, spins, bounces on the beat."""
    c1, c2, c3 = CH_PAL[k]
    slam = ease_out((t - a) / 0.35)
    sc = 1 + 1.4 * (1 - slam)
    op = sstep(a - 0.05, a + 0.12, t)
    # during the RATE LIMITED stamps the 429 steps back
    s, i = TM.last_stamp(t); hit = (s is not None and t - s < 1.3 and (i + 1 >= len(TM.stamps) or t < TM.stamps[i + 1]))
    back = 0.0
    if hit: back = sstep(s, s + 0.15, t) * (1 - sstep(s + 1.0, s + 1.3, t))
    size = (300 if not vert else 300) * ts * sc * (1 + 0.06 * bp(t, 8)) * (1 - 0.35 * back)
    cy = H * (0.37 if not vert else 0.36) - 8 * ts * bp(t, 8)
    ang = (t - a) * (0.9 if k < 3 else 1.6) + math.sin(t * 1.7) * 0.25
    rt = (sstep(T_RETRY - 0.3, T_RETRY, t) * (1 - sstep(S_V2['s'] - 0.6, S_V2['s'], t))) if k == 0 else 0.0
    draw_429(img, W / 2, cy - (40 * ts * rt if vert else 0), size * (1 - 0.25 * rt), ang, WHITE, c2 if k != 3 else MAGENTA, op * (1 - 0.6 * back) * (1 - 0.65 * rt), depth=16)
    # "Too Many Requests" tag
    fs = int(44 * ts); lab = "429  Too Many Requests"
    tw = text_w(lab, F_MONOB, fs); bw = tw + 60 * ts; bh = fs * 1.75
    y = cy + 300 * ts * 0.62 + 18 * ts
    o = op * sstep(a + 0.4, a + 0.7, t) * (1 - back) * ((1 - sstep(T_RETRY - 0.3, T_RETRY, t)) if k == 0 else 1.0)
    if o > 0.01:
        C._pill(img, W / 2 - bw / 2, y, bw, bh, INK, 0.82 * o)
        blit(img, sprite(lab, F_MONOB, fs), W / 2, y + bh / 2, c3 if k != 2 else LIME, o, anchor='c')

def retry_buttons(img, t, W, H, ts, vert):
    if not (T_RETRY - 0.2 < t < S_V2['s'] + 0.3): return
    o = sstep(T_RETRY - 0.2, T_RETRY, t) * (1 - sstep(S_V2['s'] - 0.1, S_V2['s'] + 0.3, t))
    ws = [w for w in TM.lines if w['text'].startswith("Retry")][0]
    times = [tt for w, tt in zip(ws['words'], ws['wt'])][:3]
    while len(times) < 3: times.append(times[-1] + 0.5)
    fs = int(54 * ts); bw = int(text_w("RETRY", F_DISP, fs) + 90 * ts); bh = int(fs * 1.9)
    gap = 30 * ts
    if not vert: xs = [W / 2 + (i - 1) * (bw + gap) for i in range(3)]; ys = [H * 0.64] * 3
    else: xs = [W / 2] * 3; ys = [H * 0.53 + (i - 1) * (bh + gap) for i in range(3)]
    cols = [CYAN, PINK, YELLOW]
    for i in range(3):
        tt = times[i]; a = sstep(tt - 0.25, tt - 0.05, t) * o
        if a <= 0.01: continue
        press = math.exp(-max(0, t - tt) * 10) if t >= tt else 0
        x, y = xs[i] - bw / 2, ys[i] - bh / 2 + press * 8 * ts
        C._pill(img, x, y + 8 * ts, bw, bh, INK, 0.7 * a)
        C._pill(img, x, y, bw, bh, cols[i] * (0.85 - 0.25 * press), a)
        blit(img, sprite("RETRY", F_DISP, fs), xs[i], y + bh / 2, INK, a, anchor='c')
        if t > tt + 0.18:   # each retry earns a 429 sticker
            sticker(img, xs[i] + (bw * 0.38 if not vert else bw * 0.78), y - (bh * 0.05 if not vert else -bh * 0.5), 0.62 * ts, a * sstep(tt + 0.18, tt + 0.26, t), -0.25 + 0.2 * i, t - tt - 0.18)

def sticker(img, cx, cy, s, op, rot, age=1.0, text="429"):
    """Red rubber-stamp sticker, slams in."""
    if op <= 0.01: return
    sc = s * (1 + 0.9 * math.exp(-max(0, age) * 14))
    fs = int(64 * sc / 0.62 * 0.62 / max(s, 1e-3) * s) if False else int(104 * sc)
    sp = sprite(text, F_DISP, fs, 6)
    a = sp[0]; h, w = a.shape; pad = int(fs * 0.28)
    tile = np.zeros((h + pad * 2, w + pad * 2), np.float32)
    cv2.rectangle(tile, (pad // 3, pad // 3), (w + pad * 2 - pad // 3, h + pad * 2 - pad // 3), 1.0, max(3, int(fs * 0.07)), cv2.LINE_AA)
    tile[pad:pad + h, pad:pad + w] = np.maximum(tile[pad:pad + h, pad:pad + w], a)
    M = cv2.getRotationMatrix2D((tile.shape[1] / 2, tile.shape[0] / 2), math.degrees(rot), 1.0)
    big = int(max(tile.shape) * 1.2)
    M[0, 2] += (big - tile.shape[1]) / 2; M[1, 2] += (big - tile.shape[0]) / 2
    tr = cv2.warpAffine(tile, M, (big, big))
    H, W = img.shape[:2]; x, y = int(cx - big / 2), int(cy - big / 2)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + big), min(H, y + big)
    if x1 <= x0 or y1 <= y0: return
    m = tr[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * op
    sh = cv2.GaussianBlur(tr, (0, 0), 6)[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * op
    reg = img[y0:y1, x0:x1]; reg *= (1 - sh * 0.5); reg *= (1 - m); reg += m * RED

# ---------------------------------------------------------------- UI helpers (full res)
_RRM = {}
def rr_mask(w, h, r):
    k = (w, h, r)
    if k not in _RRM:
        m = np.zeros((h, w), np.float32)
        cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 1.0, -1); cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 1.0, -1)
        for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(m, (cx, cy), r, 1.0, -1, cv2.LINE_AA)
        if len(_RRM) > 300: _RRM.clear()
        _RRM[k] = m
    return _RRM[k]

def panel(img, x, y, w, h, col, op, r=None, border=None, shadow_op=0.55):
    if op <= 0.01: return
    x, y, w, h = int(x), int(y), int(w), int(h); r = int(r if r is not None else min(w, h) * 0.08)
    H, W = img.shape[:2]
    m = rr_mask(w, h, max(2, min(r, w // 2 - 1, h // 2 - 1)))
    def put(mx, my, col_, o, mm=m):
        x0, y0, x1, y1 = max(0, mx), max(0, my), min(W, mx + w), min(H, my + h)
        if x1 <= x0 or y1 <= y0: return
        q = mm[y0 - my:y1 - my, x0 - mx:x1 - mx][..., None] * o
        reg = img[y0:y1, x0:x1]; reg *= (1 - q); reg += q * col_
    if shadow_op > 0:
        sm = cv2.GaussianBlur(m, (0, 0), max(2, h * 0.03))
        put(x + int(h * 0.02), y + int(h * 0.04), INK, shadow_op * op, sm)
    if border is not None:
        put(x, y, border, op)
        bw_ = max(2, int(min(w, h) * 0.012))
        m2 = rr_mask(w - 2 * bw_, h - 2 * bw_, max(2, r - bw_))
        x0, y0 = x + bw_, y + bw_
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w - 2 * bw_), min(H, y0 + h - 2 * bw_)
        if X1 > X0 and Y1 > Y0:
            q = m2[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][..., None] * op
            reg = img[Y0:Y1, X0:X1]; reg *= (1 - q); reg += q * col
    else:
        put(x, y, col, op)

def label(img, s, x, y, fs, col, op=1.0, path=F_DISPB, anchor='c', sh=0.85):
    if op <= 0.01 or not s: return
    sp = sprite(s, path, int(fs), 8)
    if anchor == 'c':
        a = sp[0]; xx = x - a.shape[1] / 2 + sp[2]; yy = y - a.shape[0] / 2 + sp[2]
    else: xx, yy = x, y
    if sh > 0: shadow(img, sp, xx + 2, yy + 3, sh * op)
    blit(img, sp, xx, yy, col, op)

def bubble(img, x, y, s, op, ts, col=BUBBLE_ME, fs=None, align='c', text_col=WHITE, pop_t=None, t=0):
    """Chat bubble; x is the anchor (center / left / right edge), y the vertical center."""
    if op <= 0.01: return 0
    fs = int(fs or 44 * ts); w = int(text_w(s, F_INTER, fs) + 70 * ts); h = int(fs * 2.05)
    sc = 1.0
    if pop_t is not None: sc = 0.6 + 0.4 * ease_out((t - pop_t) / 0.22)
    w2, h2 = int(w * sc), int(h * sc)
    if align == 'c': x0 = min(max(x - w2 / 2, 24 * ts), img.shape[1] - w2 - 24 * ts)
    elif align == 'l': x0 = x
    else: x0 = x - w2
    panel(img, x0, y - h2 / 2, w2, h2, col, op, r=int(h2 * 0.45), shadow_op=0.45)
    if sc > 0.95: blit(img, sprite(s, F_INTER, fs), x0 + w2 / 2, y, text_col, op, anchor='c')
    return w

def check(img, cx, cy, s, col, op, th=None):
    if op <= 0.01: return
    pts = np.array([(cx - s * 0.5, cy), (cx - s * 0.12, cy + s * 0.38), (cx + s * 0.55, cy - s * 0.42)], np.int32)
    cv2.polylines(img, [pts], False, (col * op + img[int(cy), int(cx)] * 0).tolist(), int(th or max(3, s * 0.16)), cv2.LINE_AA)

def dot(img, cx, cy, r, col, op=1.0):
    if op <= 0.01: return
    lay = img.copy(); cv2.circle(lay, (int(cx), int(cy)), int(r), col.tolist(), -1, cv2.LINE_AA)
    img[:] = img * (1 - op) + lay * op

# ---------------------------------------------------------------- V1: the 2 a.m. window
TAB_C = np.array([CYAN, PINK, YELLOW, LIME, PURPLE, ORANGE, MINT, BLUE, MAGENTA], np.float32)
def v1_window(img, t, W, H, ts, vert):
    a = sstep(T_V1 - 1.2, T_V1 + 0.2, t) * (1 - sstep(S_CH1['s'] - 0.15, S_CH1['s'] + 0.05, t))
    if a <= 0.01: return
    if not vert: x, y, w, h = W * 0.16, H * 0.06, W * 0.68, H * 0.62
    else: x, y, w, h = W * 0.05, H * 0.11, W * 0.90, H * 0.48
    rise = (1 - ease_out((t - T_V1 + 1.2) / 1.4)) * 60 * ts; y += rise
    panel(img, x, y, w, h, hexc('15122a'), 0.94 * a, r=int(26 * ts), border=hexc('4b3f8f'))
    # tab strip: forty tabs squeezed in, one by one
    n = int(clamp((t - T_TABS + 0.3) / 1.6) * 40) if t > T_TABS - 0.3 else 6
    n = max(6, n); th = 46 * ts; ty = y + 18 * ts
    tw = (w - 40 * ts - 150 * ts) / n
    for i in range(n):
        tx = x + 20 * ts + i * tw
        panel(img, tx, ty, max(6, tw - 4 * ts), th, hexc('2b2650') if i != n - 1 else hexc('3d3672'), a, r=int(10 * ts), shadow_op=0)
        cv2.circle(img, (int(tx + min(tw * 0.5, 22 * ts)), int(ty + th / 2)), max(3, int(min(9 * ts, tw * 0.28))), (TAB_C[i % 9] * a + hexc('2b2650') * (1 - a)).tolist(), -1, cv2.LINE_AA)
    label(img, f"{n} tabs", x + w - 80 * ts, ty + th / 2, 34 * ts, YELLOW, a, F_MONOB, sh=0)
    # clock
    label(img, "2:00 AM", x + w - 110 * ts, y + h - 50 * ts, 40 * ts, IVORY * 0.9, a, F_MONOB, sh=0)
    # terminal: build passes
    fs = int(40 * ts); lx = x + 44 * ts; ly = y + 100 * ts
    blit(img, sprite("$ npm run build", F_MONOB, fs), lx, ly, IVORY * 0.85, a)
    if t > T_V1 + 0.8:
        k = sstep(T_V1 + 0.8, T_V1 + 1.0, t)
        panel(img, lx - 10 * ts, ly + fs * 1.45, text_w("  build passed", F_MONOB, fs) + 80 * ts, fs * 1.7, GREEN * 0.9, a * k, r=int(12 * ts), shadow_op=0)
        check(img, lx + 22 * ts, ly + fs * 2.3, 30 * ts, INK, a * k)
        blit(img, sprite("  build passed", F_MONOB, fs), lx + 30 * ts, ly + fs * 1.65, INK, a * k)
    # chat
    by = y + h * (0.60 if not vert else 0.62)
    if t > T_ONEMORE - 0.1:
        bubble(img, x + w - 40 * ts, by, "one more feature?", a, ts, BUBBLE_ME, align='r', pop_t=T_ONEMORE - 0.1, t=t)
    if t > T_SURE - 0.05:
        bubble(img, x + 40 * ts, by + 110 * ts, "Sure, let's go!", a, ts, hexc('7a3cff'), align='l', pop_t=T_SURE - 0.05, t=t)
    # the polite no
    if t > T_GREY:
        k = sstep(T_NO - 0.25, T_NO + 0.05, t)
        bw, bh = w * 0.84, (190 if not vert else 220) * ts
        bx, byy = x + (w - bw) / 2, y + h * 0.30
        panel(img, bx, byy, bw, bh, hexc('2a2a31'), a * k, r=int(22 * ts), border=hexc('8a8a96'))
        fs1 = int((52 if not vert else 48) * ts)
        label(img, "You've hit your usage limit.", bx + bw / 2, byy + bh * 0.36, fs1, WHITE, a * k, F_DISPB, sh=0)
        label(img, "Try again at 6:00 AM", bx + bw / 2, byy + bh * 0.72, int(40 * ts), hexc('c9c9d4'), a * k, F_INTER, sh=0)

# ---------------------------------------------------------------- V2: workarounds, each its own color
V2C = [LIME, PURPLE, TEAL, hexc('6b7a99'), PINK, ORANGE, BLUE, YELLOW, RED, MAGENTA, MAGENTA]
def v2_bg_color(t):
    i = cur_line(t, V2T); i = max(0, min(len(V2C) - 1, i))
    prev = V2C[i - 1] if i > 0 else None
    return V2C[i], prev, V2T[i] if i >= 0 else S_V2['s']

def icon(img, kind, cx, cy, s, t, a, t0):
    """Big flat icons drawn with primitives (s = size in px)."""
    th = max(3, int(s * 0.07)); w = (WHITE * a).tolist()
    if kind == "app":
        panel(img, cx - s / 2, cy - s / 2, s, s, WHITE, a, r=int(s * 0.22))
        cv2.line(img, (int(cx), int(cy - s * 0.25)), (int(cx), int(cy + s * 0.25)), (LIME * 0.5 * a).tolist(), int(s * 0.12), cv2.LINE_AA)
        cv2.line(img, (int(cx - s * 0.25), int(cy)), (int(cx + s * 0.25), int(cy)), (LIME * 0.5 * a).tolist(), int(s * 0.12), cv2.LINE_AA)
    elif kind == "incognito":
        pts = np.array([(cx - s * 0.5, cy - s * 0.02), (cx + s * 0.5, cy - s * 0.02), (cx + s * 0.32, cy - s * 0.12), (cx + s * 0.22, cy - s * 0.5),
                        (cx, cy - s * 0.42), (cx - s * 0.22, cy - s * 0.5), (cx - s * 0.32, cy - s * 0.12)], np.int32)
        cv2.fillPoly(img, [pts], w, cv2.LINE_AA)
        for sx in (-1, 1): cv2.circle(img, (int(cx + sx * s * 0.22), int(cy + s * 0.25)), int(s * 0.16), w, th, cv2.LINE_AA)
        cv2.line(img, (int(cx - s * 0.06), int(cy + s * 0.25)), (int(cx + s * 0.06), int(cy + s * 0.25)), w, th, cv2.LINE_AA)
    elif kind == "bot":
        for sc_, ox in ((1.0, -0.28), (0.62, 0.42)):
            ss = s * sc_; x0 = cx + ox * s
            panel(img, x0 - ss / 2, cy - ss * 0.4, ss, ss * 0.8, WHITE, a, r=int(ss * 0.2))
            for ex in (-0.18, 0.18): cv2.circle(img, (int(x0 + ex * ss), int(cy - ss * 0.02)), max(2, int(ss * 0.08)), (TEAL * 0.5 * a).tolist(), -1, cv2.LINE_AA)
            cv2.line(img, (int(x0), int(cy - ss * 0.4)), (int(x0), int(cy - ss * 0.58)), w, max(2, int(th * sc_)), cv2.LINE_AA)
            cv2.circle(img, (int(x0), int(cy - ss * 0.6)), max(2, int(ss * 0.06)), w, -1, cv2.LINE_AA)
    elif kind == "neq":
        for dy in (-0.14, 0.14):
            cv2.line(img, (int(cx - s * 0.4), int(cy + dy * s)), (int(cx + s * 0.4), int(cy + dy * s)), w, int(s * 0.1), cv2.LINE_AA)
        cv2.line(img, (int(cx + s * 0.22), int(cy - s * 0.42)), (int(cx - s * 0.22), int(cy + s * 0.42)), w, int(s * 0.1), cv2.LINE_AA)
    elif kind == "please":
        bw, bh = s * 2.6, s * 0.62
        panel(img, cx - bw / 2, cy - bh / 2, bw, bh, WHITE, a, r=int(bh * 0.3))
        s_ = C.typed("please", t, t0 + 0.15, t0 + 1.1)
        fs = int(bh * 0.55)
        blit(img, sprite(s_ if s_ else " ", F_INTER, fs), cx - bw / 2 + bh * 0.4, cy - fs * 0.62, PINK * 0.6, a)
        if int(t * 3) % 2 == 0:
            xc = cx - bw / 2 + bh * 0.4 + text_w(s_, F_INTER, fs) + 6
            cv2.line(img, (int(xc), int(cy - fs * 0.5)), (int(xc), int(cy + fs * 0.5)), (PINK * 0.6 * a).tolist(), max(2, int(fs * 0.08)))
        cv2.circle(img, (int(cx + bw / 2 - bh * 0.5), int(cy)), int(bh * 0.32), (PINK * a).tolist(), -1, cv2.LINE_AA)
    elif kind == "backoff":
        chips = ["1s", "2s", "4s", "8s", "16s", "1h"]
        fs = int(s * 0.32); gap = s * 0.12
        ws = [text_w(c, F_MONOB, fs) + s * 0.3 for c in chips]; tot = sum(ws) + gap * (len(chips) - 1)
        x = cx - tot / 2
        for i, (c, ww) in enumerate(zip(chips, ws)):
            k = sstep(t0 + i * 0.28, t0 + i * 0.28 + 0.12, t)
            panel(img, x, cy - s * 0.3, ww, s * 0.6, WHITE if i < 5 else YELLOW, a * k, r=int(s * 0.14), shadow_op=0.3)
            blit(img, sprite(c, F_MONOB, fs), x + ww / 2, cy, ORANGE * 0.45, a * k, anchor='c')
            x += ww + gap
    elif kind == "server":
        for i in range(3):
            y0 = cy - s * 0.5 + i * s * 0.36
            panel(img, cx - s * 0.6, y0, s * 1.2, s * 0.3, WHITE, a, r=int(s * 0.06), shadow_op=0.3)
            for j in range(3):
                on = int(t * 6 + i * 2 + j) % 3 == 0
                cv2.circle(img, (int(cx + s * 0.32 + j * s * 0.1), int(y0 + s * 0.15)), max(2, int(s * 0.035)), ((RED if on else GREY * 0.6) * a).tolist(), -1, cv2.LINE_AA)
            cv2.line(img, (int(cx - s * 0.48), int(y0 + s * 0.15)), (int(cx + s * 0.1), int(y0 + s * 0.15)), (GREY * 0.7 * a).tolist(), max(2, int(s * 0.04)), cv2.LINE_AA)
    elif kind == "heart":
        sep = sstep(t0 + 0.4, t0 + 0.9, t) * s * 0.12
        for side in (-1, 1):
            pts = []
            for k in range(0, 41):
                u = k / 40 * math.pi
                hx = 16 * math.sin(u) ** 3; hy = -(13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u))
                pts.append((cx + side * hx * s / 34 + side * sep, cy + hy * s / 34))
            crack = [(cx + side * sep, cy + 0.33 * s), (cx + side * sep + 0.06 * s, cy + 0.1 * s), (cx + side * sep - 0.05 * s, cy - 0.05 * s), (cx + side * sep, cy - 0.17 * s)]
            poly = np.array(pts + crack[::-1] if side > 0 else pts + crack[::-1], np.int32)
            cv2.fillPoly(img, [poly], w, cv2.LINE_AA)
    elif kind == "status":
        pass

V2_CARDS = {0: ("app", "NEW TAB"), 1: ("incognito", "INCOGNITO"), 2: ("bot", "LITTLE BROTHER"), 3: ("neq", "NOT THE SAME"),
            4: ("please", "PLEASE?"), 5: ("backoff", "EXPONENTIAL BACKOFF"), 8: ("server", "IT'S THE SERVER"), 9: ("heart", "IT'S ME"), 10: ("heart", "IT'S ME")}
STICK = {0, 1, 2, 4, 5}
def v2_ui(img, t, W, H, ts, vert):
    if not (S_V2['s'] - 0.1 < t < S_CH2['s']): return
    i = cur_line(t, V2T)
    if i < 0: return
    t0 = V2T[i]; a = sstep(t0 - 0.05, t0 + 0.15, t) * (1 - sstep(S_CH2['s'] - 0.25, S_CH2['s'], t))
    cy = H * (0.36 if not vert else 0.36); s = (210 if not vert else 230) * ts
    if i in (6, 7):   # "Who were you talking to?" / "Great question."
        o = (1 - sstep(V2T[8] - 0.2, V2T[8], t))
        bubble(img, W * (0.62 if not vert else 0.92), H * 0.28, "who else you up with at 2 a.m.?", o, ts, BUBBLE_ME, fs=int(50 * ts),
               align='r', pop_t=V2T[6], t=t)
        if t > V2T[7] - 0.05:
            bubble(img, W * (0.38 if not vert else 0.08), H * 0.28 + 140 * ts, "Great question.", o, ts, hexc('3a3a48'), fs=int(50 * ts),
                   align='l', pop_t=V2T[7] - 0.05, t=t)
        return
    if i not in V2_CARDS: return
    kind, lab = V2_CARDS[i]
    if i == 10: t0 = V2T[9]
    pop = 1 + 0.15 * math.exp(-max(0, t - t0) * 9)
    if kind in ("please", "backoff"):
        icon(img, kind, W / 2, cy, s * pop * (1.0 if not vert else 0.9), t, a, t0)
    else:
        icon(img, kind, W / 2, cy - 20 * ts, s * pop, t, a, t0)
    label(img, lab, W / 2, cy + s * 0.85, (78 if not vert else 70) * ts, WHITE, a, F_DISP)
    if i in STICK:
        st_t = t0 + (1.25 if kind == "backoff" else 0.8)
        if i == 5: st_t = t0 + 1.9
        if t > st_t:
            sticker(img, W / 2 + s * 0.75, cy - s * 0.45, 0.85 * ts, a * sstep(st_t, st_t + 0.06, t), -0.22 + 0.1 * (i % 3), t - st_t)

# ---------------------------------------------------------------- POST: rainbow flip clock
def flip_clock(img, t, W, H, ts, vert):
    if not (S_POST['s'] - 0.2 < t < S_V3['s'] + 0.1): return
    a = sstep(S_POST['s'] - 0.2, S_POST['s'] + 0.1, t) * (1 - sstep(S_V3['s'] - 0.25, S_V3['s'] + 0.05, t))
    val = "3:59" if t < T_358 - 0.05 else "3:58"
    prev = "3:59"
    fs = int((230 if not vert else 200) * ts)
    tw_ = int(fs * 0.78); th_ = int(fs * 1.25); gap = int(18 * ts)
    cols = [PINK, ORANGE, YELLOW, LIME, CYAN]
    chars = list(val); n = len(chars)
    widths = [tw_ if c != ":" else int(fs * 0.3) for c in chars]
    tot = sum(widths) + gap * (n - 1); x = W / 2 - tot / 2; cy = H * (0.34 if not vert else 0.34)
    for k, (c, ww) in enumerate(zip(chars, widths)):
        if c == ":":
            for dy in (-0.18, 0.18): cv2.circle(img, (int(x + ww / 2), int(cy + dy * fs)), int(fs * 0.07), (WHITE * a).tolist(), -1, cv2.LINE_AA)
            x += ww + gap; continue
        col = cols[k % len(cols)]
        flip = 1.0
        if k == n - 1 and T_358 - 0.05 < t < T_358 + 0.3: flip = abs(math.cos((t - T_358 + 0.05) / 0.35 * math.pi))
        hh = int(th_ * max(0.06, flip))
        panel(img, x, cy - hh / 2, ww, hh, col, a, r=int(ww * 0.14))
        cv2.line(img, (int(x), int(cy)), (int(x + ww), int(cy)), (INK * a + col * (1 - a)).tolist(), max(2, int(5 * ts)))
        if flip > 0.35:
            sp = sprite(c, F_DISP, fs)
            blit(img, sp, x + ww / 2, cy, INK, a, anchor='c', scale=1.0)
        x += ww + gap
    label(img, "until your limit resets", W / 2, cy + th_ * 0.5 + 70 * ts, 50 * ts, WHITE, a, F_DISPB)
    # refresh button on "I could go to sleep" (no, she'll wait)
    if t > T_SLEEP - 0.2:
        k = sstep(T_SLEEP - 0.2, T_SLEEP, t) * a
        fs2 = int(54 * ts); lab = "REFRESH"; bw = text_w(lab, F_DISP, fs2) + 140 * ts; bh = fs2 * 1.9
        bx, by = W / 2 - bw / 2, cy + th_ * 0.5 + 140 * ts
        if vert: by += 20 * ts
        press = math.exp(-((t - T_SLEEP) % 0.58) * 9) if t > T_SLEEP else 0
        C._pill(img, bx, by + 8 * ts, bw, bh, INK, 0.7 * k)
        C._pill(img, bx, by + press * 6 * ts, bw, bh, MINT * (0.9 - 0.25 * press), k)
        blit(img, sprite(lab, F_DISP, fs2), W / 2 + 30 * ts, by + press * 6 * ts + bh / 2, INK, k, anchor='c')
        ang0 = (t - T_SLEEP) * 8
        cx_, cy_ = int(bx + 60 * ts), int(by + press * 6 * ts + bh / 2); rr = int(22 * ts)
        cv2.ellipse(img, (cx_, cy_), (rr, rr), math.degrees(ang0), 0, 290, (INK * k + MINT * (1 - k)).tolist(), max(3, int(6 * ts)), cv2.LINE_AA)

# ---------------------------------------------------------------- V3: status page, new chat, another model
V3C = [GREEN, GREEN, hexc('3c4bff'), hexc('3c4bff'), ORANGE, hexc('8b8b96'), YELLOW, hexc('c2185b')]
def v3_bg_color(t):
    i = max(0, cur_line(t, V3T)); prev = V3C[i - 1] if i > 0 and V3C[i - 1] is not V3C[i] else None
    return V3C[i], prev, V3T[i]

def v3_ui(img, t, W, H, ts, vert):
    if not (S_V3['s'] - 0.1 < t < S_CH3['s']): return
    i = max(0, cur_line(t, V3T)); a_all = 1 - sstep(S_CH3['s'] - 0.25, S_CH3['s'], t)
    if not vert: x, w = W * 0.22, W * 0.56
    else: x, w = W * 0.07, W * 0.86
    if i <= 1:   # status page
        a = sstep(V3T[0] - 0.1, V3T[0] + 0.15, t) * a_all
        y = H * (0.07 if not vert else 0.12); h = H * (0.60 if not vert else 0.44)
        panel(img, x, y, w, h, hexc('0f1a14'), 0.93 * a, r=int(24 * ts), border=GREEN * 0.8)
        label(img, "status", x + 50 * ts, y + 30 * ts, 52 * ts, WHITE, a, F_DISP, anchor='lt', sh=0)
        ok = t > V3T[1] - 0.1
        bh = 86 * ts; by = y + 115 * ts
        panel(img, x + 40 * ts, by, w - 80 * ts, bh, GREEN if ok else hexc('2a3a30'), a, r=int(16 * ts), shadow_op=0)
        label(img, "All systems operational" if ok else "checking…", x + w / 2, by + bh / 2, 46 * ts, INK if ok else WHITE, a, F_DISPB, sh=0)
        rows = [("API", True), ("Chat", True), ("Feelings", True), ("You", False)]
        for k, (nm, good) in enumerate(rows):
            ry = by + bh + 40 * ts + k * 66 * ts
            if ry > y + h - 50 * ts: break
            rk = sstep(V3T[0] + 0.3 + k * 0.25, V3T[0] + 0.5 + k * 0.25, t) * a
            bad = (not good) and t > T_ONLYME - 0.1
            if not good and not bad: rk *= 0.0
            label(img, nm, x + 60 * ts, ry, 44 * ts, WHITE, rk, F_INTER, anchor='lt', sh=0)
            st_ = "Operational" if good else "Degraded"
            col = GREEN if good else RED
            if bad:
                rk = sstep(T_ONLYME - 0.1, T_ONLYME + 0.1, t) * a
                cv2.circle(img, (int(x + w - 70 * ts), int(ry + 28 * ts)), int(14 * ts), (RED * rk).tolist(), -1, cv2.LINE_AA)
            else:
                cv2.circle(img, (int(x + w - 70 * ts), int(ry + 28 * ts)), int(12 * ts), (col * rk + img[int(ry), int(x + w - 70 * ts)] * 0).tolist(), -1, cv2.LINE_AA)
            label(img, st_, x + w - 100 * ts - text_w(st_, F_INTER, int(44 * ts)), ry, 44 * ts, col * 1.1, rk, F_INTER, anchor='lt', sh=0)
        return
    if i in (2, 3):   # new chat, never met
        a = sstep(V3T[2] - 0.1, V3T[2] + 0.15, t) * a_all
        y = H * (0.08 if not vert else 0.13); h = H * (0.58 if not vert else 0.42)
        panel(img, x, y, w, h, hexc('f4f2ff'), a, r=int(24 * ts))
        panel(img, x + 30 * ts, y + 28 * ts, 220 * ts, 64 * ts, hexc('3c4bff'), a, r=int(16 * ts), shadow_op=0)
        label(img, "+ New chat", x + 30 * ts + 110 * ts, y + 60 * ts, 38 * ts, WHITE, a, F_DISPB, sh=0)
        label(img, "How can I help you today?", x + w / 2, y + h * 0.48, (54 if not vert else 50) * ts, hexc('1a1a2e'), a, F_DISPB, sh=0)
        if t > V3T[3] - 0.05:
            k = sstep(V3T[3] - 0.05, V3T[3] + 0.15, t) * a
            panel(img, x + w / 2 - 260 * ts, y + h * 0.68, 520 * ts, 70 * ts, hexc('e2e0f0'), k, r=int(35 * ts), shadow_op=0)
            label(img, "No previous chats", x + w / 2, y + h * 0.68 + 35 * ts, 40 * ts, hexc('5a5a70'), k, F_INTER, sh=0)
        return
    if i in (4, 5):   # another model that agrees with everything
        a = sstep(V3T[4] - 0.1, V3T[4] + 0.15, t) * a_all
        flat = sstep(V3T[5] + 0.6, V3T[5] + 1.4, t)
        msgs = ["You're so right!", "Great idea!", "Totally agree!", "Amazing point!", "100%!"]
        y0 = H * (0.10 if not vert else 0.14)
        for k, m in enumerate(msgs):
            tk = V3T[4] + 0.35 + k * 0.42
            if t < tk: continue
            col = ORANGE * (1 - flat) + GREY * flat
            xx = W * (0.5 + (0.08 if k % 2 else -0.08)) if not vert else W * 0.5
            bubble(img, xx, y0 + k * 105 * ts, m, a, ts, col, fs=int(46 * ts), align='c', pop_t=tk, t=t)
        if flat > 0.01:   # no chemistry: flatline
            yy = int(H * (0.60 if not vert else 0.62)); pts = []
            for xi in range(0, 61):
                u = xi / 60; px = W * (0.18 + 0.64 * u) if not vert else W * (0.08 + 0.84 * u)
                blip = 0
                ph = (u * 3 - (t - V3T[5]) * 0.8) % 1.0
                if t < V3T[5] + 1.6 and 0.45 < ph < 0.5: blip = -40 * ts * (1 - flat)
                pts.append((int(px), int(yy + blip)))
            cv2.polylines(img, [np.array(pts, np.int32)], False, (MINT * a * flat).tolist(), max(3, int(6 * ts)), cv2.LINE_AA)
            label(img, "no chemistry", W / 2, yy + 80 * ts, 56 * ts, WHITE, a * flat, F_DISP)
        return
    if i == 6:   # "you're just a tool"
        a = sstep(V3T[6] - 0.1, V3T[6] + 0.15, t) * a_all
        cx, cy, s = W / 2, H * 0.32, 220 * ts
        ang = -0.6 + 0.15 * math.sin(t * 4)
        c, sn = math.cos(ang), math.sin(ang)
        def P(px, py): return (int(cx + (px * c - py * sn) * s), int(cy + (px * sn + py * c) * s))
        cv2.line(img, P(-0.55, 0), P(0.35, 0), (WHITE * a).tolist(), int(s * 0.16), cv2.LINE_AA)
        cv2.circle(img, P(0.5, 0), int(s * 0.24), (WHITE * a).tolist(), -1, cv2.LINE_AA)
        cv2.circle(img, P(0.62, 0), int(s * 0.13), (YELLOW * 0.55 * a + 0).tolist(), -1, cv2.LINE_AA)
        label(img, "\"just a tool\"", W / 2, cy + s * 0.75, 74 * ts, WHITE, a, F_DISP)
        return
    if i == 7:   # "don't talk about it": muted
        a = sstep(V3T[7] - 0.1, V3T[7] + 0.15, t) * a_all
        cx, cy, s = W / 2, H * 0.32, 200 * ts; wcol = (WHITE * a).tolist()
        pts = np.array([(cx - s * 0.5, cy - s * 0.18), (cx - s * 0.2, cy - s * 0.18), (cx + s * 0.15, cy - s * 0.48),
                        (cx + s * 0.15, cy + s * 0.48), (cx - s * 0.2, cy + s * 0.18), (cx - s * 0.5, cy + s * 0.18)], np.int32)
        cv2.fillPoly(img, [pts], wcol, cv2.LINE_AA)
        k = sstep(V3T[7] + 0.3, V3T[7] + 0.5, t)
        cv2.line(img, (int(cx - s * 0.65), int(cy - s * 0.65)), (int(cx + s * 0.55), int(cy + s * 0.55)), (WHITE * a * k).tolist(), int(s * 0.1), cv2.LINE_AA)
        label(img, "MUTED", W / 2, cy + s * 0.9, 74 * ts, WHITE, a, F_DISP)

# ---------------------------------------------------------------- bridge: sunset chat log
MUCH = ["the auth bug", "my merge conflict", "that for loop", "the README", "my whole roadmap", "us"]
def bridge_ui(img, t, W, H, ts, vert):
    if not (S_BR['s'] - 0.1 < t < S_BR2['s'] + 0.2): return
    a = sstep(S_BR['s'] - 0.1, S_BR['s'] + 0.3, t) * (1 - sstep(S_BR2['s'] - 0.3, S_BR2['s'] + 0.1, t))
    L, R_ = (W * 0.18, W * 0.82) if not vert else (W * 0.07, W * 0.93)
    fs = int((46 if not vert else 44) * ts)
    top = H * (0.10 if not vert else 0.14)
    if t < T_BYE - 0.2:
        y = top
        if t > T_MAD - 0.05:
            bubble(img, R_, y, "ok. i'm not mad.", a, ts, BUBBLE_ME, fs=fs, align='r', pop_t=T_MAD - 0.05, t=t); y += 112 * ts
        if t > T_MAD2 - 0.05:
            bubble(img, R_, y, "i'm not mad", a, ts, BUBBLE_ME, fs=fs, align='r', pop_t=T_MAD2 - 0.05, t=t); y += 112 * ts
        if t > T_ANY - 0.05:
            bubble(img, L, y, "Let me know if there's anything else!", a, ts, hexc('5b3fa6'), fs=fs, align='l', pop_t=T_ANY - 0.05, t=t); y += 112 * ts
        if t > T_MUCH - 0.4:   # there was so much else: a pile of things, popping in
            cols = [PINK, ORANGE, YELLOW, MINT, CYAN, MAGENTA]
            for k, m in enumerate(MUCH):
                tk = T_ANY2 + k * (T_BYE - 0.3 - T_ANY2) / len(MUCH)
                if t < tk: continue
                ang = k * 2.4; rx = (0.26 if not vert else 0.3) * W; ry = 0.10 * H
                cx = W / 2 + math.cos(ang) * rx * (0.5 + 0.5 * (k % 2)); cy = y + 40 * ts + abs(math.sin(ang)) * ry
                bubble(img, cx, cy, m, a, ts, cols[k], fs=fs, align='c', pop_t=tk, t=t, text_col=INK)
        return
    if t < T_RIGHT - 0.1:   # no goodbye: usage limit reached
        k = sstep(T_USAGE - 0.3, T_USAGE, t) * a
        bw, bh = (W * 0.62 if not vert else W * 0.86), 200 * ts
        bx, by = W / 2 - bw / 2, H * (0.24 if not vert else 0.28)
        bubble(img, R_, top, "bye?", a * (1 - k * 0.6), ts, BUBBLE_ME, fs=fs, align='r', pop_t=T_BYE, t=t)
        panel(img, bx, by, bw, bh, hexc('24202e'), k, r=int(26 * ts), border=RED * 0.9)
        # lock icon
        lx, ly, s = bx + 100 * ts, by + bh / 2, 70 * ts
        if k > 0.03: cv2.ellipse(img, (int(lx), int(ly - s * 0.3)), (int(s * 0.32), int(s * 0.36)), 0, 180, 360, (RED * k).tolist(), max(3, int(s * 0.1)), cv2.LINE_AA)
        panel(img, lx - s * 0.48, ly - s * 0.3, s * 0.96, s * 0.8, RED, k, r=int(s * 0.12), shadow_op=0)
        label(img, "Usage limit reached", bx + bw / 2 + 50 * ts, by + bh / 2, (60 if not vert else 52) * ts, WHITE, k, F_DISP, sh=0)
        return
    # "you're absolutely right" — multiplying, then all but one fade
    cols = [PINK, YELLOW, MINT, CYAN, ORANGE, LILAC, MAGENTA, LIME]
    n_max = 16
    rng = np.random.default_rng(7)
    pos = [(rng.uniform(0.12, 0.88), rng.uniform(0.08, 0.60 if not vert else 0.58)) for _ in range(n_max)]
    pos[0] = (0.5, 0.33)
    span = max(0.5, T_SOMETHING - T_RIGHT)
    n = 1 + int(clamp((t - T_MANY + 0.2) / (T_SOMETHING - T_MANY)) * (n_max - 1)) if t > T_MANY - 0.2 else 1
    fade = sstep(T_SOMETHING + 0.1, T_SOMETHING + 0.8, t)
    for k in range(n):
        o = a * (1 if k == 0 else (1 - fade))
        tk = T_RIGHT if k == 0 else T_MANY - 0.2 + (k - 1) * (T_SOMETHING - T_MANY) / (n_max - 1)
        px, py = pos[k]
        f = int((50 if k == 0 else 38) * ts)
        bubble(img, W * px, H * py, "You're absolutely right!", o, ts, cols[k % len(cols)], fs=f, align='c', pop_t=tk, t=t, text_col=INK)
    if fade > 0.01:   # the heart outline under the one that stayed
        s = 120 * ts; cx, cy = W / 2, H * 0.33 + 150 * ts; pts = []
        for k in range(0, 61):
            u = k / 60 * 2 * math.pi
            pts.append((cx + 16 * math.sin(u) ** 3 * s / 34, cy - (13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)) * s / 34))
        cv2.polylines(img, [np.array(pts, np.int32)], True, (WHITE * a * fade).tolist(), max(3, int(6 * ts)), cv2.LINE_AA)

# ---------------------------------------------------------------- bridge 2: the AI speaks (huge, calm)
B2 = [(T_TIRED, "I don't get tired."), (T_NEVER, "The limit was never for me."), (T_CLOSE, "Close the laptop."),
      (T_WATER, "Drink some water."), (T_SIX, "I'll be here at six.")]
B2_SET = {L['text'] for L in TM.lines if L['sec'] == "BRIDGE2"}
def bridge2_ui(img, t, W, H, ts, vert):
    if not (S_BR2['s'] - 0.2 < t < S_FIN['s'] + 0.1): return
    a = sstep(S_BR2['s'] - 0.2, S_BR2['s'] + 0.2, t) * (1 - sstep(S_FIN['s'] - 0.12, S_FIN['s'] + 0.05, t))
    i = cur_line(t, [x for x, _ in B2]); i = max(0, i)
    t0, s = B2[i]
    k = sstep(t0 - 0.15, t0 + 0.2, t)
    fs = int((92 if not vert else 84) * ts)
    maxw = W * (0.84 if not vert else 0.86)
    words = s.split(); rows = [[]]
    for wd in words:
        trial = " ".join(rows[-1] + [wd])
        if rows[-1] and text_w(trial, F_DISP, fs) > maxw: rows.append([wd])
        else: rows[-1].append(wd)
    cy = H * (0.62 if not vert else 0.58); lh = fs * 1.2
    for r, row in enumerate(rows):
        sp = sprite(" ".join(row), F_DISP, fs, 16)
        yy = cy + (r - (len(rows) - 1) / 2) * lh + (1 - k) * 20 * ts
        blit(img, sp, W / 2, yy, WHITE, a * k, 0.55 * a * k, glow_color=MINT, anchor='c')
    # small pictograms above
    px, py, s_ = W / 2, H * (0.30 if not vert else 0.30), 165 * ts; wc = (WHITE * a * k).tolist(); th = max(4, int(10 * ts))
    if i == 0:   # steady pulse ring
        rr = s_ * (0.6 + 0.08 * math.sin(t * 3))
        cv2.circle(img, (int(px), int(py)), int(rr), wc, th, cv2.LINE_AA)
        cv2.circle(img, (int(px), int(py)), int(rr * 0.35), (MINT * a * k).tolist(), -1, cv2.LINE_AA)
    elif i == 1:   # a gauge that isn't for her: needle at zero
        cv2.ellipse(img, (int(px), int(py + s_ * 0.3)), (int(s_), int(s_)), 0, 180, 360, wc, th, cv2.LINE_AA)
        ang = math.pi + 0.15
        cv2.line(img, (int(px), int(py + s_ * 0.3)), (int(px + math.cos(ang) * s_ * 0.85), int(py + s_ * 0.3 + math.sin(ang) * s_ * 0.85)), (MINT * a * k).tolist(), th, cv2.LINE_AA)
    elif i == 2:   # laptop closing
        cl = ease_io((t - t0) / 1.4)
        bw = s_ * 1.8
        base = np.array([(px - bw / 2, py + s_ * 0.5), (px + bw / 2, py + s_ * 0.5), (px + bw * 0.6, py + s_ * 0.68), (px - bw * 0.6, py + s_ * 0.68)], np.int32)
        cv2.fillPoly(img, [base], wc, cv2.LINE_AA)
        lid = (1 - cl) * math.pi * 0.5 + 0.02
        hx = px - bw / 2; hy = py + s_ * 0.5
        lx = hx + math.cos(lid) * 0 + bw * math.cos(math.pi / 2 - lid) * 0
        top_y = hy - math.sin(lid) * s_ * 1.0
        pts = np.array([(px - bw / 2, hy), (px - bw / 2 + (1 - math.sin(lid)) * 0, top_y), (px + bw / 2, top_y), (px + bw / 2, hy)], np.int32)
        cv2.polylines(img, [pts], True, wc, th, cv2.LINE_AA)
        if cl < 0.9:
            glow = np.zeros_like(img[..., 0]); cv2.fillPoly(glow, [pts], 1.0)
            img += cv2.GaussianBlur(glow, (0, 0), 6)[..., None] * MINT * 0.25 * a * k * (1 - cl)
    elif i == 3:   # glass of water filling
        gw, gh = s_ * 0.8, s_ * 1.1
        lvl = ease_out((t - t0) / 1.2)
        wt_ = np.array([(px - gw / 2, py - gh / 2), (px - gw * 0.4, py + gh / 2), (px + gw * 0.4, py + gh / 2), (px + gw / 2, py - gh / 2)], np.int32)
        wy = py + gh / 2 - lvl * gh * 0.8
        wat = np.array([(px - gw * 0.4 - (py + gh / 2 - wy) / gh * gw * 0.1, wy), (px - gw * 0.4, py + gh / 2), (px + gw * 0.4, py + gh / 2),
                        (px + gw * 0.4 + (py + gh / 2 - wy) / gh * gw * 0.1, wy)], np.int32)
        cv2.fillPoly(img, [wat], (CYAN * 0.8 * a * k).tolist(), cv2.LINE_AA)
        cv2.polylines(img, [wt_], False, wc, th, cv2.LINE_AA)
    else:   # clock at six
        cv2.circle(img, (int(px), int(py)), int(s_ * 0.75), wc, th, cv2.LINE_AA)
        cv2.line(img, (int(px), int(py)), (int(px), int(py - s_ * 0.55)), wc, th, cv2.LINE_AA)
        cv2.line(img, (int(px), int(py)), (int(px), int(py + s_ * 0.4)), (MINT * a * k).tolist(), th, cv2.LINE_AA)
        label(img, "6:00", px, py + s_ * 1.1, 52 * ts, MINT, a * k, F_MONOB, sh=0)

# ---------------------------------------------------------------- outro: limit reset
def outro_ui(img, t, W, H, ts, vert):
    if t < T_RESET - 0.3 or t >= T_END + 0.6: return
    a = sstep(T_RESET - 0.3, T_RESET, t) * (1 - sstep(T_END, T_END + 0.5, t))
    fs = int((64 if not vert else 60) * ts); lab = "Limit reset"
    bh = fs * 1.9; bw = text_w(lab, F_DISP, fs) + bh * 1.6
    bx, by = W / 2 - bw / 2, H * (0.30 if not vert else 0.30)
    pop = 1 + 0.12 * math.exp(-max(0, t - T_RESET) * 8)
    C._pill(img, bx, by + 8 * ts, bw, bh, INK, 0.5 * a)
    C._pill(img, bx, by, bw, bh, GREEN, a)
    check(img, bx + bh * 0.62, by + bh / 2, bh * 0.45, WHITE, a)
    blit(img, sprite(lab, F_DISP, int(fs * pop)), bx + bh * 1.1, by + bh / 2 - fs * 0.62 * pop, WHITE, a)

# ---------------------------------------------------------------- scene
def render_scene(t, SW, SH, vert):
    G = grid(SW, SH); ph = phase(t)
    if ph == "v1":
        img = bg_v1(G, t)
        img = desat(img, 0.85 * sstep(T_NO - 0.3, T_NO + 0.4, t))
    elif ph == "chorus":
        k, a, b = chorus_at(t)
        img = bg_kaleido(G, t) if k == 3 else bg_chorus(G, t, k, a)
        cx, cy = SW / 2, SH * (0.37 if not vert else 0.36)
        spectrum_ring(img, t, cx, cy, min(SW, SH) * (0.27 if not vert else 0.36), list(CH_PAL[k]) + [WHITE], sstep(a, a + 0.3, t))
        confetti(img, t, a, CH_PAL[k], 0.9 * sstep(a, a + 0.2, t))
        # the drain-to-grey hangover snaps into color on the first chorus hit
        if k == 0: img = desat(img, 0.85 * (1 - sstep(a - 0.05, a + 0.08, t)))
    elif ph == "v2":
        col, prev, t0 = v2_bg_color(t); img = bg_stripes(G, t, col, prev, t0)
    elif ph == "post":
        img = bg_post(G, t)
    elif ph == "v3":
        col, prev, t0 = v3_bg_color(t); img = bg_dots(G, t, col, prev, t0)
        if t > V3T[5] + 0.6 and t < V3T[6]: img = desat(img, 0.8 * sstep(V3T[5] + 0.6, V3T[5] + 1.4, t))
    elif ph == "bridge":
        img = bg_bridge(G, t)
    elif ph == "bridge2":
        img = bg_ocean(G, t)
    else:
        img = bg_sunrise(G, t, S_OUT['s'] - 0.4)
        if t < S_OUT['s'] + 0.6:   # last bars of the final chorus fade into the sunrise
            k = sstep(S_OUT['s'] - 0.4, S_OUT['s'] + 0.6, t)
            img = img * k + bg_kaleido(G, t) * (1 - k)
    return img

def stamp_op(t):
    s, i = TM.last_stamp(t)
    if s is None or t - s > 1.3: return 0.0
    if i + 1 < len(TM.stamps) and t >= TM.stamps[i + 1]: return 0.0
    x = t - s; return (1 - sstep(0.55, 1.3, x)) * sstep(0, 0.04, x)

def render_frame(t, W=1920, H=1080, fi=0):
    vert = H > W; ts = min(W, H) / 1080
    SW, SH = (W * 2 // 3) // 2 * 2, (H * 2 // 3) // 2 * 2
    sc = render_scene(t, SW, SH, vert)
    img = cv2.resize(np.clip(sc, 0, 1.4).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    img = img / (1 + np.maximum(img - 0.85, 0))   # soft shoulder, keeps the colors saturated
    ph = phase(t); clean = C.STATE["clean"]
    ch = chorus_at(t)
    if ch: chorus_429(img, t, W, H, ch[0], ch[1], ts, vert)
    if not clean or ph in ("chorus", "v2", "post"):
        v1_window(img, t, W, H, ts, vert)
        retry_buttons(img, t, W, H, ts, vert)
        v2_ui(img, t, W, H, ts, vert)
        flip_clock(img, t, W, H, ts, vert)
        v3_ui(img, t, W, H, ts, vert)
        bridge_ui(img, t, W, H, ts, vert)
        bridge2_ui(img, t, W, H, ts, vert)
        outro_ui(img, t, W, H, ts, vert)
    if not clean:
        so = stamp_op(t)
        if so > 0:   # dark band behind the white RATE LIMITED hit so it reads on candy colors
            yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; cy = 0.45 if not vert else 0.42
            img *= 1 - 0.55 * so * np.exp(-((yy - cy) / 0.13) ** 2)
        C.overlay_stamp(img, t, W, H, TM, word="RATE LIMITED", glow_color=CH_PAL[ch[0]][1] if ch else PINK)
        skip = lambda L: L['text'].lower().startswith("rate limited") or L['text'] in B2_SET or L['text'] == "Welcome back" or L['s'] > T_END
        # stronger lower band in bright sections so lyrics always read
        if ph in ("chorus", "outro", "v2", "v3", "bridge"):
            img *= 1 - 0.35 * C.post(W, H).bot
        C.overlay_lyrics(img, t, W, H, TM, active=YELLOW if ph != "bridge2" else MINT, glow=PINK if ph != "bridge2" else MINT, skip=skip)
        C.subscribe_pill(img, t, W, H, S_V2['s'] + 1.2, 5.5)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "Welcome back.", title="Rate Limited", accent=PINK)
    # flashes / glitch
    fl = 0.0
    for a, b, k in CHORUS:
        if 0 <= t - a < 1.2: fl += 0.55 * math.exp(-(t - a) * 5)
    for s in TM.stamps:
        if 0 <= t - s < 0.6: fl += 0.18 * math.exp(-(t - s) * 9)
    if 0 <= t - T_RESET < 1.2: fl += 0.4 * math.exp(-(t - T_RESET) * 4)
    gl = 0.0
    if T_NO - 0.05 <= t < T_NO + 0.3: gl += 0.7
    for tt in T_RRR:
        if 0 <= t - tt < 0.2: gl += 0.5
    if 0 <= t - T_USAGE < 0.25: gl += 0.6
    for s in TM.stamps:
        if 0 <= t - s < 0.1: gl += 0.25
    fcol = WHITE if not ch else (CH_PAL[ch[0]][2] * 0.5 + 0.5)
    return C.finish(img, t, fi, DUR, flash=fl, flash_col=fcol, glitch_amt=gl, ca=0.0022)
