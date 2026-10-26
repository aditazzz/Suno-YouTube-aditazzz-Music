"""TED Talk, in charts: "The Daily Standup".

The whole song is one issue of a newspaper called The Daily Standup. Every line becomes a news graphic: black ink on
cream paper, one red for Ted, and blue ballpoint notes in the margins (the narrator's voice). When somebody dims the
lights the paper sits under a spotlight like a stage; at the hard stop the office lights snap back on and the paper
prints a CORRECTION. In the outro Ted's dot unplugs from the team network and drifts off the page into a footnote.
"""
import os, math
import numpy as np, cv2
from studio import core as C
from studio.core import sstep, ease_out, ease_io, clamp, lerp, hexc

HERE = os.path.dirname(os.path.abspath(__file__))
TM = C.Timing(HERE)
TAIL = 3.0
DUR = TM.duration + TAIL
F32 = np.float32
lt = TM.line_t
def wt(sub, w, nth=0):
    try: return TM.word_t(sub, w, nth)
    except Exception: return lt(sub, nth)

FONT = lambda n: os.path.join(C.FONTS, n)
F_MAST = FONT("PlayfairDisplaySC-Regular.ttf")
F_HEAD = FONT("EBGaramond-SemiBold.ttf")
F_ITAL = FONT("EBGaramond-MediumItalic.ttf")
F_SANS = FONT("Inter-SemiBold.otf")
F_SANSM = FONT("Inter-Medium.otf")
F_NUM = FONT("InterDisplay-Black.otf")
F_NUMB = FONT("InterDisplay-Bold.otf")
F_MONO = FONT("JBMono-700.ttf")
F_PEN = FONT("Caveat-Medium.ttf")
F_TAB = FONT("Anton-Regular.ttf")

# ---------------------------------------------------------------- palette (linear-ish display floats)
PAPER = hexc('f2ece1'); CARD = hexc('fbf7ef'); INK = hexc('171513'); INK2 = hexc('3d3832'); MUTE = hexc('8a8378')
RULE = hexc('cbc2b2'); GRID = hexc('ddd5c7'); BAR = hexc('b4ab9c'); RED = hexc('d93a2b'); REDL = hexc('f2a093')
PEN = hexc('2448a8'); PENL = hexc('9fb3e6'); GHOST = hexc('a9bccf'); CREAM = hexc('fbf4e6')

# ---------------------------------------------------------------- key times
TT = [L['s'] for L in TM.lines if L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always")]
T_V1 = lt("He doesn't answer"); T_RESP = lt("He responds"); T_DIFF = lt("difference"); T_FOUR = lt("four minutes")
T_ASK = lt("I asked him"); T_SO = lt("He said, so"); T_SOW = wt("He said, so", "so"); T_DIM = lt("Somebody dim"); T_SIT = lt("everybody sit")
T_18 = lt("Eighteen minutes", 0); T_SLIDES = wt("Eighteen minutes", "slides", 0); T_POINT = wt("Eighteen minutes", "point", 0)
T_FATHER = lt("story about his father", 0); T_PAUSE = lt("pause he thinks", 0); T_CIRCLE = lt("circle back", 0)
T_RAFTER = lt("right after the part", 0); T_YOUNG = lt("where he was young", 0); T_BELIEVE = lt("nobody believed", 0)
T_V2 = lt("He starts every"); T_ENDS = lt("He ends every"); T_REALQ = lt("the real question"); T_ABOUTQ = lt("about the question")
T_JOURNEY = wt("He said journey", "journey"); T_UNLOCK = wt("He said journey", "unlock"); T_STORY = lt("let me tell you")
T_STORYW = wt("let me tell you", "story"); T_CAL = lt("watched my calendar"); T_GIVEUP = lt("give up")
T_18b = lt("Eighteen minutes", 1); T_FATHERb = lt("story about his father", 1); T_PAUSEb = lt("pause he thinks", 1)
T_CIRCLEb = lt("circle back", 1); T_RAFTERb = lt("right after the part", 1); T_BELIEVEb = lt("nobody believed", 1)
T_STOP = TM.section("BRIDGE")["s"]
T_TED = lt("Ted."); T_STANDUP = lt("This is a standup"); T_FIFTEEN = lt("fifteen minutes"); T_EIGHT = lt("eight people")
T_SIX = lt("You have used six"); T_HARD = lt("Dana had a hard stop"); T_HAS = lt("Dana has had"); T_TWO = lt("two years")
T_GHOST = lt("Dana is a ghost"); T_DIDTHAT = lt("You did that")
T_NOSCHED = lt("Nobody scheduled"); T_NOEND = lt("Nobody can end"); T_NOQA = lt("no Q and A")
T_NOA = lt("because there's no A"); T_NEVERQ = lt("never a Q"); T_ALWAYS = lt("always a Ted talk")
T_ANYWAY = lt("Anyway"); T_HESAYS = lt("He says."); T_HAVING = lt("Having taken"); T_PLACE = lt("Into a place"); T_REACH = lt("none of us")
T_END = 157.2
T_PILL = TM.section("V2")["s"] + 0.3
STAMPS = [TM.snap(t - 0.04, 0.2) for t in TT]

NAMES = ["Ted", "Me", "Dana", "Priya", "Marcus", "Sam", "Lee", "Jo"]

# ---------------------------------------------------------------- canvas: design units -> pixels
SHB = 4; SCL = 1 << SHB
class Cv:
    def __init__(s, img, W, H):
        s.img = img; s.W = W; s.H = H; s.vert = H > W
        s.DW, s.DH = (1080, 1920) if s.vert else (1920, 1080)
        s.k = W / s.DW
        s.cx, s.cy, s.z = s.DW / 2, s.DH / 2, 1.0
        s.dx = 0.0; s.dy = 0.0; s.op = 1.0
        s.box = (80, 370, 920, 850) if s.vert else (170, 196, 1580, 624)
    def X(s, x): return s.W / 2 + (x + s.dx - s.cx) * s.z * s.k
    def Y(s, y): return s.H / 2 + (y + s.dy - s.cy) * s.z * s.k
    def L(s, v): return v * s.z * s.k

def _paint(cv, P, draw, pad, col, op):
    op *= cv.op
    if op <= 0.003: return
    x0 = int(math.floor(P[:, 0].min() - pad)); y0 = int(math.floor(P[:, 1].min() - pad))
    x1 = int(math.ceil(P[:, 0].max() + pad)) + 1; y1 = int(math.ceil(P[:, 1].max() + pad)) + 1
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(cv.W, x1), min(cv.H, y1)
    if X1 <= X0 or Y1 <= Y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    Q = np.round((P - [x0, y0]) * SCL).astype(np.int32)
    draw(m, Q)
    a = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(F32) * (op / 255.0)
    reg = cv.img[Y0:Y1, X0:X1]
    reg *= (1 - a[..., None]); reg += a[..., None] * col

def _px(cv, pts): return np.array([[cv.X(x), cv.Y(y)] for x, y in pts], np.float64)

def fill(cv, pts, col, op=1.0):
    P = _px(cv, pts)
    _paint(cv, P, lambda m, Q: cv2.fillPoly(m, [Q], 255, cv2.LINE_AA, shift=SHB), 3, col, op)

def stroke(cv, pts, col, wd=2.0, op=1.0, closed=False):
    P = _px(cv, pts); w = cv.L(wd)
    if w < 1.0: op *= max(0.25, w); w = 1.0
    t = max(1, int(round(w)))
    _paint(cv, P, lambda m, Q: cv2.polylines(m, [Q], closed, 255, t, cv2.LINE_AA, shift=SHB), t + 3, col, op)

def dashed(cv, pts, col, wd=2.0, op=1.0, dash=14, gap=10, prog=1.0):
    pts = np.asarray(pts, np.float64); seg = np.hypot(*np.diff(pts, axis=0).T); tot = seg.sum() * prog
    cum = np.concatenate([[0], np.cumsum(seg)])
    def at(d):
        i = min(len(seg) - 1, np.searchsorted(cum, d, side='right') - 1); u = (d - cum[i]) / max(seg[i], 1e-9)
        return pts[i] + (pts[i + 1] - pts[i]) * u
    d = 0.0
    while d < tot:
        e = min(tot, d + dash); stroke(cv, [at(d), at((d + e) / 2), at(e)], col, wd, op); d = e + gap

def circ_pts(cx, cy, r, n=72, a0=0.0, a1=2 * math.pi, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

def circle(cv, cx, cy, r, col, op=1.0, wd=None):
    if wd is None: fill(cv, circ_pts(cx, cy, r, 64)[:-1], col, op)
    else: stroke(cv, circ_pts(cx, cy, r, 72), col, wd, op, closed=True)

def rrect_pts(x, y, w, h, r):
    r = min(r, w / 2, h / 2); P = []
    for cx, cy, a0 in ((x + w - r, y + r, -math.pi / 2), (x + w - r, y + h - r, 0), (x + r, y + h - r, math.pi / 2), (x + r, y + r, math.pi)):
        for i in range(7): a = a0 + i * (math.pi / 2) / 6; P.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return P

def rect(cv, x, y, w, h, col, op=1.0, r=0, wd=None):
    pts = rrect_pts(x, y, w, h, r) if r > 0 else [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    if wd is None: fill(cv, pts, col, op)
    else: stroke(cv, pts, col, wd, op, closed=True)

def wedge(cv, cx, cy, r0, r1, a0, a1, col, op=1.0):
    n = max(3, int(abs(a1 - a0) / 0.04))
    outer = [(cx + r1 * math.cos(a0 + (a1 - a0) * i / n), cy + r1 * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    inner = [(cx + r0 * math.cos(a1 - (a1 - a0) * i / n), cy + r0 * math.sin(a1 - (a1 - a0) * i / n)) for i in range(n + 1)]
    fill(cv, outer + inner, col, op)

def arrow(cv, pts, col, wd=3.0, op=1.0, head=16, prog=1.0, dash=False):
    pts = np.asarray(pts, np.float64)
    if prog < 1.0:
        seg = np.hypot(*np.diff(pts, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)]); d = cum[-1] * clamp(prog)
        i = min(len(seg) - 1, np.searchsorted(cum, d, side='right') - 1); u = (d - cum[i]) / max(seg[i], 1e-9)
        pts = np.vstack([pts[:i + 1], pts[i] + (pts[i + 1] - pts[i]) * u])
    if len(pts) < 2 or np.hypot(*(pts[-1] - pts[0])) < 1: return
    if dash: dashed(cv, pts, col, wd, op)
    else: stroke(cv, pts, col, wd, op)
    if prog >= 0.98:
        p1, p0 = pts[-1], pts[-2]; d = p1 - p0; n = np.hypot(*d)
        if n > 1e-6:
            d /= n; q = np.array([-d[1], d[0]])
            fill(cv, [p1 + d * 2, p1 - d * head + q * head * 0.55, p1 - d * head - q * head * 0.55], col, op)

# ---------------------------------------------------------------- text
def text(cv, s, x, y, font, size, col, op=1.0, ax='l', ay='m', track=0):
    op *= cv.op
    if op <= 0.004 or not s: return 0.0
    px = max(6, int(round(size * cv.z * cv.k)))
    if px > 900: return 0.0
    spr = C.sprite(s, font, px, 0, track=int(round(track * cv.z * cv.k)) if track else 0)
    h, w = spr[0].shape
    asc, desc = C.font(font, px).getmetrics()
    X = cv.X(x); Y = cv.Y(y)
    if ax == 'c': X -= w / 2
    elif ax == 'r': X -= w
    if ay == 'm': Y -= asc - 0.36 * px
    elif ay == 'b': Y -= asc
    elif ay == 't': Y -= asc - 0.74 * px
    C.blit(cv.img, spr, X, Y, col, op)
    return w / (cv.z * cv.k)

def tw(s, font, size): return C.text_w(s, font, max(6, int(size))) if s else 0.0

def wrap(s, font, size, maxw):
    words = s.split(); rows = [""]
    for w in words:
        cand = (rows[-1] + " " + w).strip()
        if rows[-1] and tw(cand, font, size) > maxw: rows.append(w)
        else: rows[-1] = cand
    return rows

# ---------------------------------------------------------------- the blue pen (narrator) and the red marker
def _smooth_noise(seed, n, amp):
    r = np.random.default_rng(seed); v = r.normal(0, 1, n + 8)
    v = np.convolve(v, np.ones(7) / 7, mode='same')[4:4 + n]
    return v * amp

def _resample(pts, step=6.0):
    pts = np.asarray(pts, np.float64); out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        d = np.hypot(*(b - a)); k = max(1, int(d / step))
        for i in range(1, k + 1): out.append(a + (b - a) * i / k)
    return np.array(out)

def pen(cv, pts, prog, seed=0, wd=4.6, col=PEN, op=0.92, jit=2.0):
    if prog <= 0: return
    P = _resample(pts)
    if len(P) < 2: return
    d = np.diff(P, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.maximum(np.hypot(nrm[:, 0], nrm[:, 1])[:, None], 1e-9)
    nrm = np.vstack([nrm, nrm[-1:]])
    P = P + nrm * _smooth_noise(seed, len(P), jit)[:, None]
    n = max(2, int(len(P) * clamp(prog)))
    stroke(cv, P[:n], col, wd, op)

def pen_ellipse(cv, cx, cy, rx, ry, prog, seed=0, wd=4.6, col=PEN, op=0.92):
    a0 = -2.4 + 0.3 * math.sin(seed); n = 90
    pts = [(cx + rx * (1 + 0.05 * math.sin(i * 0.21 + seed)) * math.cos(a0 + 2 * math.pi * 1.1 * i / n),
            cy + ry * (1 + 0.06 * math.cos(i * 0.17 + seed)) * math.sin(a0 + 2 * math.pi * 1.1 * i / n)) for i in range(n + 1)]
    pen(cv, pts, prog, seed, wd, col, op, jit=1.2)

def pen_arrow(cv, p0, p1, prog, seed=0, bend=0.25, wd=4.6, col=PEN, op=0.92):
    p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; q = np.array([-d[1], d[0]]) * bend
    mid = (p0 + p1) / 2 + q
    pts = [(1 - u) ** 2 * p0 + 2 * (1 - u) * u * mid + u * u * p1 for u in np.linspace(0, 1, 40)]
    pen(cv, pts, min(1, prog / 0.8), seed, wd, col, op, jit=1.0)
    if prog > 0.8:
        k = clamp((prog - 0.8) / 0.2); e = pts[-1]; dd = pts[-1] - pts[-4]; dd /= max(np.hypot(*dd), 1e-9); nq = np.array([-dd[1], dd[0]])
        L = 26
        pen(cv, [e, e - dd * L + nq * L * 0.6], k, seed + 1, wd, col, op, jit=0.6)
        pen(cv, [e, e - dd * L - nq * L * 0.6], k, seed + 2, wd, col, op, jit=0.6)

def pen_text(cv, s, x, y, size, prog, ax='l', ay='m', col=PEN, op=0.95):
    if prog <= 0: return 0.0
    k = max(1, int(round(len(s) * clamp(prog * 1.0))))
    full = tw(s, F_PEN, size)
    if ax == 'c': x -= full / 2
    elif ax == 'r': x -= full
    return text(cv, s[:k], x, y, F_PEN, size, col, op, 'l', ay)

def marker(cv, x, y, w, h, prog, col=REDL, op=0.62, seed=0):
    """highlighter swipe behind a word (x,y = left, middle)."""
    if prog <= 0: return
    w2 = w * clamp(prog); sk = _smooth_noise(seed, 4, 3)
    fill(cv, [(x - 6, y - h / 2 + sk[0]), (x + w2 + 6, y - h / 2 + sk[1]), (x + w2 + 8, y + h / 2 + sk[2]), (x - 4, y + h / 2 + sk[3])], col, op)

# ---------------------------------------------------------------- paper, lights, finish
_PAPER = {}
def paper(W, H):
    k = (W, H)
    if k not in _PAPER:
        r = np.random.default_rng(11)
        low = cv2.resize(cv2.GaussianBlur(r.normal(0, 1, (H // 8, W // 8)).astype(F32), (0, 0), 5), (W, H), interpolation=cv2.INTER_CUBIC)
        low /= max(1e-6, np.abs(low).max())
        fib = cv2.GaussianBlur(r.normal(0, 1, (H, W)).astype(F32), (0, 0), 0.8)
        fib2 = cv2.GaussianBlur(r.normal(0, 1, (H, W)).astype(F32), (0, 0), sigmaX=6, sigmaY=0.6)
        img = PAPER[None, None, :] * (1 + 0.022 * low[..., None] + 0.010 * fib[..., None] + 0.008 * fib2[..., None])
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        img *= (1 - 0.10 * np.clip(d - 0.55, 0, None) ** 1.6)[..., None]
        # the fold of the newspaper (a soft crease across the middle of the sheet)
        fy = H * 0.5 if W > H else H * 0.5
        crease = np.exp(-((yy[:, :1] - fy) / (2.2 * W / 1920)) ** 2) * 0.035 - np.exp(-((yy[:, :1] - fy + 5 * W / 1920) / (5 * W / 1920)) ** 2) * 0.012
        img *= (1 - crease)[..., None]
        _PAPER[k] = img.astype(F32)
    return _PAPER[k].copy()

def amb(t):
    """overall light: 1 = office lights on, ~0.2 = lights dimmed for the keynote"""
    a = 1.0
    a = lerp(a, 0.16, ease_io((t - T_DIM) / 2.3))
    on = sstep(T_STOP + 0.55, T_STOP + 0.7, t)                       # hard stop: lights snap on (with a flicker)
    fl = 0.0
    if T_STOP + 0.55 <= t < T_STOP + 1.15: fl = 0.35 * (math.sin((t - T_STOP) * 70) > 0.3)
    a = lerp(a, 1.0, on) - fl * on
    a = lerp(a, 0.17, ease_io((t - (T_NOSCHED - 1.9)) / 1.4))
    a = lerp(a, 1.0, ease_io((t - (T_ANYWAY - 0.3)) / 1.8))
    return clamp(a, 0.0, 1.0)

_SPOT = {}
def spot(W, H):
    """a soft-edged rounded-rectangle pool of light that covers the whole figure area"""
    k = (W, H)
    if k not in _SPOT:
        cv = Cv(None, W, H); x, y, w, h = cv.box
        cx, cy = cv.X(x + w / 2), cv.Y(y + h / 2 + (40 if cv.vert else 6))
        rx, ry = cv.L(w * 0.60), cv.L(h * (0.64 if not cv.vert else 0.60))
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        d = ((np.abs(xx - cx) / rx) ** 4 + (np.abs(yy - cy) / ry) ** 4) ** 0.25
        _SPOT[k] = (1 / (1 + d ** 14)).astype(F32)
    return _SPOT[k]

def light(img, t, W, H):
    a = amb(t)
    if a > 0.995: return
    s = spot(W, H)[..., None]
    red = sstep(T_NOSCHED - 1.9, T_NOSCHED - 0.5, t) * (1 - sstep(T_ANYWAY - 0.3, T_ANYWAY + 1, t))
    warm = np.array([1.0, 0.965 - 0.05 * red, 0.90 - 0.07 * red], F32); cool = np.array([0.86, 0.85, 0.94], F32)
    tint = 1 + (1 - a) * ((s * warm + (1 - s) * cool) - 1)
    img *= (a + (1 - a) * s) * tint

def finish(img, t, fi):
    H, W = img.shape[:2]; p = C.post(W, H)
    img += cv2.resize(p.grain[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 0.011
    img *= (1 - sstep(DUR - 1.0, DUR - 0.05, t))
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

# ---------------------------------------------------------------- the newspaper furniture
def clock_label(t):
    if t >= T_ANYWAY - 0.2: return "THURSDAY", "9:15 A.M."
    day = "WEDNESDAY"
    for tt, lab in ((T_NOSCHED - 2.0, "11:48 A.M."), (T_STOP + 0.6, "10:12 A.M."), (TT[2], "10:02 A.M."), (T_V2, "9:41 A.M."),
                    (TT[0], "9:24 A.M."), (T_ASK, "9:19 A.M.")):
        if t >= tt: return day, lab
    return day, "9:15 A.M."

def masthead(cv, t):
    v = cv.vert; day, clk = clock_label(t); ink = INK
    if not v:
        text(cv, "THE DAILY STANDUP", 960, 66, F_MAST, 74, ink, 1.0, 'c', 'm', track=3)
        stroke(cv, [(120, 112), (1800, 112)], ink, 2.2); stroke(cv, [(120, 119), (1800, 119)], ink, 1.0)
        text(cv, f"{day}, OCT. 21", 120, 146, F_SANSM, 30, INK2, 1.0, 'l', 'm', track=2)
        text(cv, clk, 960, 146, F_MONO, 32, RED if t > T_ASK - 0.2 else INK2, 1.0, 'c', 'm')
        text(cv, "PRICE: 15 MINUTES", 1800, 146, F_SANSM, 30, INK2, 1.0, 'r', 'm', track=2)
        stroke(cv, [(120, 172), (1800, 172)], ink, 1.4)
    else:
        text(cv, "THE DAILY STANDUP", 540, 240, F_MAST, 62, ink, 1.0, 'c', 'm', track=2)
        stroke(cv, [(70, 300), (1010, 300)], ink, 2.2); stroke(cv, [(70, 307), (1010, 307)], ink, 1.0)
        text(cv, day, 70, 336, F_SANSM, 30, INK2, 1.0, 'l', 'm', track=2)
        text(cv, clk, 1010, 336, F_MONO, 34, RED if t > T_ASK - 0.2 else INK2, 1.0, 'r', 'm')
        stroke(cv, [(70, 360), (1010, 360)], ink, 1.4)

def frame(cv, kicker, title, source=None):
    """figure furniture: red kicker, serif headline, hairline; returns the chart area (x, y, w, h)"""
    x, y, w, h = cv.box; v = cv.vert
    text(cv, kicker, x, y + 22, F_SANS, 32, RED, 1.0, 'l', 'm', track=3)
    ts = 60 if not v else 58
    rows = wrap(title, F_HEAD, ts, w) if v else [title]
    if not v:
        while tw(title, F_HEAD, ts) > w and ts > 40: ts -= 2
    for i, r in enumerate(rows): text(cv, r, x, y + 80 + i * ts * 1.08, F_HEAD, ts, INK, 1.0, 'l', 'm')
    yr = y + 80 + (len(rows) - 1) * ts * 1.08 + ts * 0.7
    stroke(cv, [(x, yr), (x + w, yr)], RULE, 1.6)
    if source: text(cv, source, x, y + h - 14, F_SANSM, 30, MUTE, 1.0, 'l', 'm')
    top = yr + 28; bot = y + h - (54 if source else 20)
    return (x, top, w, bot - top)

def fakelines(cv, x, y, w, n, lh=34, op=0.55, seed=0):
    r = np.random.default_rng(seed)
    for i in range(n):
        ww = w * (0.55 if i == n - 1 else r.uniform(0.86, 1.0))
        rect(cv, x, y + i * lh, ww, 9, BAR, op * 0.55, r=4)

# ================================================================ the figures
def fig_front(cv, t, u):
    x, y, w, h = cv.box; v = cv.vert
    hs = 78 if not v else 76
    rows = wrap("Standup to last 15 minutes, sources say", F_HEAD, hs, w if not v else w)
    for i, r in enumerate(rows): text(cv, r, x, y + 50 + i * hs * 1.06, F_HEAD, hs, INK, 1.0, 'l', 'm')
    yb = y + 50 + len(rows) * hs * 1.06
    text(cv, "Eight attendees. One question on the agenda.", x, yb + 4, F_ITAL, 44 if not v else 42, INK2, 1.0, 'l', 'm')
    stroke(cv, [(x, yb + 46), (x + w, yb + 46)], RULE, 1.6)
    # left column: body text (texture); right: the attendee ring
    if not v:
        fakelines(cv, x, yb + 92, 640, 9, 38, seed=2); fakelines(cv, x + 680, yb + 92, 300, 9, 38, seed=5)
        cx, cy, R = 1430, yb + 240, 165
    else:
        cx, cy, R = 540, yb + 320, 190
        fakelines(cv, x, cy + R + 130, w, 3, 38, seed=2)
    stroke(cv, circ_pts(cx, cy, R, 90), RULE, 1.6, closed=True)
    for i, n in enumerate(NAMES):
        a = -math.pi / 2 + i * 2 * math.pi / 8; px, py = cx + R * math.cos(a), cy + R * math.sin(a)
        bob = 5 * TM.beat_pulse(t + i * 0.05, 9) if t > 0.6 else 0
        col = RED if i == 0 else PEN if i == 1 else INK2
        circle(cv, px, py - bob, 20 if i else 25, col)
        lx = px + (40 if math.cos(a) > 0.2 else -40 if math.cos(a) < -0.2 else 0)
        ly = py + (46 if math.sin(a) > 0.7 else -46 if math.sin(a) < -0.7 else 0)
        text(cv, n, lx, ly, F_SANS, 36, col if i < 2 else INK, 1.0, 'l' if math.cos(a) > 0.2 else 'r' if math.cos(a) < -0.2 else 'c', 'm')
    if not v: pen_text(cv, "1 question. easy.", cx - 120, cy + R + 96, 50, (t - 3.2) / 0.9)
    else: pen_text(cv, "1 question. easy.", cx - 150, cy + R + 84, 50, (t - 3.2) / 0.9)

def box_label(cv, x, y, w, h, lab, col_fill, col_txt, op=1.0, dash=False, size=38):
    if dash:
        pts = rrect_pts(x, y, w, h, 14); dashed(cv, pts + [pts[0]], MUTE, 2.4, op)
    else:
        rect(cv, x, y, w, h, col_fill, op, r=14)
    text(cv, lab, x + w / 2, y + h / 2, F_SANS, size, col_txt, op, 'c', 'm', track=2)

def fig_flow(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 1", "How Ted handles a question", "Source: every standup since March")
    v = cv.vert
    names = ["QUESTION", "RESPOND", "ANECDOTE", "REFRAME"]
    if not v:
        bw, bh = 300, 104; ys = cy_ + ch * 0.26
        xs = [cx_ + i * (cw - bw) / 3 for i in range(4)]
        pos = [(xx, ys) for xx in xs]; ans = (xs[0] + 40, cy_ + ch * 0.66)
    else:
        bw, bh = 470, 104; xs = cx_ + 20
        pos = [(xs, cy_ + 40 + i * (ch - 160) / 3) for i in range(4)]; ans = (cx_ + cw - 300, pos[0][1])
    # dashed route toward ANSWER (never taken)
    k_ans = sstep(T_V1 + 0.5, T_V1 + 1.0, t)
    aw = 300 if not v else 290
    if not v:
        p0 = (pos[0][0] + bw / 2, pos[0][1] + bh + 6); p1 = (ans[0] + aw / 2 - 40, ans[1] - 6)
        p1 = (p0[0], ans[1] - 6)
        arrow(cv, [p0, p1], MUTE, 2.4, k_ans, dash=True, prog=k_ans)
        bx, by = p0[0], (p0[1] + p1[1]) / 2
    else:
        p0 = (pos[0][0] + bw + 6, pos[0][1] + bh / 2); p1 = (ans[0] - 8, ans[1] + bh / 2)
        arrow(cv, [p0, p1], MUTE, 2.4, k_ans, dash=True, prog=k_ans)
        bx, by = (p0[0] + p1[0]) / 2, p0[1]
    box_label(cv, ans[0], ans[1], aw, bh, "ANSWER", None, MUTE, k_ans, dash=True)
    s = 16 * sstep(T_V1 + 0.9, T_V1 + 1.1, t)
    if s > 0: stroke(cv, [(bx - s, by - s), (bx + s, by + s)], RED, 4); stroke(cv, [(bx - s, by + s), (bx + s, by - s)], RED, 4)
    pen_ellipse(cv, ans[0] + aw / 2, ans[1] + bh / 2, aw * 0.62, bh * 0.85, (t - (T_V1 + 1.6)) / 0.7, seed=3)
    if not v: pen_text(cv, "never reached", ans[0] + aw * 1.2, ans[1] + bh / 2, 54, (t - (T_V1 + 2.2)) / 0.6, 'l')
    else: pen_text(cv, "never reached", ans[0] + aw / 2, ans[1] + bh + 84, 52, (t - (T_V1 + 2.2)) / 0.6, 'c')
    # the real route
    tq = T_V1 + 0.1; starts = [tq, T_RESP + 0.05, T_RESP + 0.75, T_RESP + 1.45]
    for i, (nm, (bx, by)) in enumerate(zip(names, pos)):
        k = sstep(starts[i], starts[i] + 0.25, t)
        if k <= 0: continue
        if i > 0:
            pa = pos[i - 1]
            if not v: arrow(cv, [(pa[0] + bw + 8, by + bh / 2), (bx - 10, by + bh / 2)], INK, 3.2, 1.0, prog=sstep(starts[i] - 0.3, starts[i], t))
            else: arrow(cv, [(bx + bw / 2, pa[1] + bh + 6), (bx + bw / 2, by - 8)], INK, 3.2, 1.0, prog=sstep(starts[i] - 0.3, starts[i], t))
        red = i > 0
        box_label(cv, bx, by, bw, bh, nm, RED if red else INK, CREAM, k)
    # loop back from REFRAME to RESPOND
    kl = sstep(T_RESP + 1.9, T_RESP + 2.8, t)
    if kl > 0:
        if not v:
            a, b = pos[3], pos[1]; yy = a[1] - 70
            arrow(cv, [(a[0] + bw / 2, a[1] - 6), (a[0] + bw / 2, yy), (b[0] + bw / 2, yy), (b[0] + bw / 2, b[1] - 8)], RED, 3.2, 1.0, prog=kl)
            if kl > 0.6: text(cv, "repeat", (a[0] + b[0]) / 2 + bw / 2, yy - 26, F_SANS, 32, RED, sstep(0.6, 0.9, kl), 'c', 'm', track=2)
        else:
            a, b = pos[3], pos[1]; xx = a[0] + bw + 70
            arrow(cv, [(a[0] + bw + 6, a[1] + bh / 2), (xx, a[1] + bh / 2), (xx, b[1] + bh / 2), (b[0] + bw + 8, b[1] + bh / 2)], RED, 3.2, 1.0, prog=kl)
            if kl > 0.6: text(cv, "repeat", xx + 18, (a[1] + b[1]) / 2 + bh / 2, F_SANS, 32, RED, sstep(0.6, 0.9, kl), 'l', 'm', track=2)

def axes(cv, x, y, w, h, xt, yt, ylab=None, xlab=None, grid=True):
    for f, lab in yt:
        yy = y + h - f * h
        if grid and f > 0: stroke(cv, [(x, yy), (x + w, yy)], GRID, 1.4)
        text(cv, lab, x - 16, yy, F_SANSM, 34, MUTE, 1.0, 'r', 'm')
    stroke(cv, [(x, y + h), (x + w, y + h)], INK, 2.2)
    for f, lab in xt:
        xx = x + f * w; stroke(cv, [(xx, y + h), (xx, y + h + 10)], INK, 2.0)
        text(cv, lab, xx, y + h + 36, F_SANSM, 34, MUTE, 1.0, 'c', 'm')
    if ylab: text(cv, ylab, x, y - 28, F_SANS, 34, INK2, 1.0, 'l', 'm')
    if xlab: text(cv, xlab, x + w, y + h + 78, F_SANSM, 32, MUTE, 1.0, 'r', 'm')

def fig_line(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 2", "Will to live during standup, by minute", "Source: me, sitting there")
    v = cv.vert
    x = cx_ + (110 if not v else 100); y = cy_ + 40; w = cw - (150 if not v else 130); h = ch - (110 if not v else 130)
    axes(cv, x, y, w, h, [(i / 15, f"{i}" if i else "0 min") for i in (0, 4, 8, 12, 15)], [(0, "0%"), (0.5, "50"), (1, "100%")],
         ylab="will to live", xlab="minutes into standup")
    def val(m):
        if m < 4: return 0.97 - 0.01 * math.sin(m * 3)
        if m < 4.5: return lerp(0.97, 0.07, ease_io((m - 4) / 0.5))
        return 0.06 + 0.012 * math.sin(m * 5.3) + 0.008 * math.sin(m * 11.1)
    # draw-on: 0..4 min before "four minutes in", the cliff on it, then the rest
    if t < T_FOUR: mx = 4.0 * clamp((t - T_DIFF + 0.2) / (T_FOUR - T_DIFF + 0.2))
    else: mx = 4.0 + 11.0 * ease_out((t - T_FOUR) / 2.6)
    ms = np.linspace(0, max(0.01, mx), max(2, int(mx * 24)))
    pts = [(x + m / 15 * w, y + h - val(m) * h) for m in ms]
    pre = [p for p, m in zip(pts, ms) if m <= 4.02]; post = [p for p, m in zip(pts, ms) if m >= 3.98]
    if len(pre) > 1: stroke(cv, pre, INK, 5)
    if len(post) > 1: stroke(cv, post, RED, 5)
    if t > T_FOUR - 0.05:
        k = sstep(T_FOUR - 0.05, T_FOUR + 0.15, t); px, py = x + 4 / 15 * w, y + h - val(3.99) * h
        circle(cv, px, py, 13 * k, RED); circle(cv, px, py, 24 * k, RED, 0.6 * k, wd=2.5)
        pen_text(cv, "you'll feel it here", px + 90, py + 150, 54 if not v else 50, (t - T_FOUR - 0.4) / 0.6)
        pen_arrow(cv, (px + 100, py + 118), (px + 22, py + 22), (t - T_FOUR - 0.9) / 0.5, seed=4, bend=0.3)

def fig_question(cv, t, u):
    x, y, w, h = cv.box; v = cv.vert
    cw_, chh = (1120, 470) if not v else (900, 560)
    bx = x + w / 2 - cw_ / 2; by = y + h / 2 - chh / 2 + (10 if not v else 0)
    rect(cv, bx + 10, by + 12, cw_, chh, INK, 0.10, r=18)
    rect(cv, bx, by, cw_, chh, CARD, 1.0, r=18); rect(cv, bx, by, cw_, chh, INK, 1.0, r=18, wd=2.2)
    text(cv, "QUESTION 1 OF 1", bx + 60, by + 70, F_SANS, 32, RED, 1.0, 'l', 'm', track=3)
    qs = 104 if not v else 92
    rows = ["Is the file ready?"] if not v else ["Is the file", "ready?"]
    for i, r in enumerate(rows): text(cv, r, bx + 60, by + 170 + i * qs * 1.02, F_HEAD, qs, INK, 1.0, 'l', 'm')
    yy = by + chh - 90
    for j, lab in enumerate(("Yes", "No")):
        xx = bx + 60 + j * 260
        rect(cv, xx, yy - 26, 52, 52, INK, 1.0, r=6, wd=3)
        text(cv, lab, xx + 74, yy, F_SANS, 44, INK, 1.0, 'l', 'm')
    pen_text(cv, "(yes/no question)", bx + cw_ - (40 if not v else 30), yy, 50, (t - (T_ASK + 0.6)) / 0.6, 'r')

def zoom_out(cv, t):
    """'so — stepping back': the camera steps back from the question card; the page turns out to be enormous."""
    k = ease_io((t - (T_SOW - 0.15)) / 1.5)
    return 1.0 / (1 + 4.6 * k)

def page_beyond(cv, t, z):
    """when zoomed out: a whole broadsheet of other (tiny, irrelevant) items around the card."""
    if z > 0.95: return
    op = sstep(0.95, 0.6, z)
    x, y, w, h = cv.box; cx, cy = x + w / 2, y + h / 2
    for gy in range(-3, 4):
        for gx in range(-3, 4):
            if gx == 0 and gy == 0: continue
            bx = cx + gx * (w + 120) - w / 2; by = cy + gy * (h + 160) - h / 2
            stroke(cv, [(bx, by - 30), (bx + w, by - 30)], INK, 3, op)
            rect(cv, bx, by, w * 0.6, 44, INK2, op * 0.45, r=6)
            fakelines(cv, bx, by + 90, w * 0.46, 7, 46, op, seed=(gx + 3) * 7 + gy + 3)
            rect(cv, bx + w * 0.52, by + 90, w * 0.48, h * 0.6, BAR, op * 0.35, r=6)

def fig_so(cv, t):
    """the giant red 'so —' that arrives with the word"""
    k = sstep(T_SOW - 0.02, T_SOW + 0.12, t) * (1 - sstep(T_DIM + 0.1, T_DIM + 0.5, t))
    if k <= 0: return
    v = cv.vert; sz = (300 if not v else 250) * (1 + 0.15 * (1 - ease_out((t - T_SOW) / 0.25)))
    z0, cx0, cy0, op0 = cv.z, cv.cx, cv.cy, cv.op; cv.z = 1.0; cv.cx, cv.cy = cv.DW / 2, cv.DH / 2; cv.op = 1.0
    # the card ends up small in the middle of the screen: "so —" sits above it, STEPPING BACK below it
    yy, ys = (330, 652) if not v else (770, 1085)
    halo(cv, "so —", cv.DW / 2, yy, F_ITAL, sz, k)
    text(cv, "so —", cv.DW / 2, yy, F_ITAL, sz, RED, k, 'c', 'm')
    k2 = k * sstep(T_SOW + 0.35, T_SOW + 0.6, t)
    halo(cv, "STEPPING BACK", cv.DW / 2, ys, F_SANS, 48, k2, track=6)
    text(cv, "STEPPING BACK", cv.DW / 2, ys, F_SANS, 48, INK, k2, 'c', 'm', track=6)
    cv.z, cv.cx, cv.cy, cv.op = z0, cx0, cy0, op0

def halo(cv, s, x, y, font, size, op, track=0):
    """paint paper behind a piece of text so it reads over anything (a knockout)"""
    if op <= 0.01: return
    px = max(6, int(round(size * cv.z * cv.k))); gl = max(4, int(px * 0.10))
    spr = C.sprite(s, font, px, gl, track=int(round(track * cv.z * cv.k)) if track else 0)
    a, g, pad = spr; h, w = a.shape
    asc, _ = C.font(font, px).getmetrics()
    X = int(round(cv.X(x) - (w - 2 * pad) / 2 - pad)); Y = int(round(cv.Y(y) - (asc - 0.36 * px) - pad))
    H, W = cv.img.shape[:2]; X0, Y0, X1, Y1 = max(0, X), max(0, Y), min(W, X + w), min(H, Y + h)
    if X1 <= X0 or Y1 <= Y0: return
    m = np.clip(g[Y0 - Y:Y1 - Y, X0 - X:X1 - X] * 3.0, 0, 1)[..., None] * op * 0.92
    reg = cv.img[Y0:Y1, X0:X1]; reg *= (1 - m); reg += m * PAPER

def seat_positions(cv, cx_, cy_, cw, ch):
    v = cv.vert
    stage = (cx_ + cw / 2, cy_ + 70)
    rows = [[1, 2, 3, 4], [5, 6, 7]]
    P = {}
    for ri, row in enumerate(rows):
        n = len(row); sp = (cw * (0.16 if not v else 0.2))
        for j, i in enumerate(row):
            P[i] = (cx_ + cw / 2 + (j - (n - 1) / 2) * sp, cy_ + ch * (0.55 if not v else 0.52) + ri * (ch * 0.22))
    return stage, P

def fig_seating(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 3", "Seating chart, standup (revised)")
    v = cv.vert
    stage, P = seat_positions(cv, cx_, cy_, cw, ch)
    # stage line, spotlight cone, Ted
    stroke(cv, [(stage[0] - cw * 0.28, stage[1] + 40), (stage[0] + cw * 0.28, stage[1] + 40)], INK, 3)
    text(cv, "STAGE", stage[0] + cw * 0.28 + 20, stage[1] + 40, F_SANS, 30, MUTE, 1.0, 'l', 'm', track=3)
    kc = sstep(T_DIM + 0.2, T_DIM + 1.2, t)
    fill(cv, [(stage[0] - 18, cy_ - 30), (stage[0] + 18, cy_ - 30), (stage[0] + 110, stage[1] + 40), (stage[0] - 110, stage[1] + 40)], hexc('fff3c8'), 0.55 * kc)
    circle(cv, stage[0], stage[1] + 8, 24, RED)
    text(cv, "Ted", stage[0], stage[1] - 40, F_SANS, 36, RED, 1.0, 'c', 'm')
    # the ring of attendees files into rows
    R = 150 if not v else 170; rc = (cx_ + cw / 2, cy_ + ch * 0.5)
    for i in range(1, 8):
        a = -math.pi / 2 + i * 2 * math.pi / 8
        p0 = (rc[0] + R * math.cos(a), rc[1] + R * math.sin(a))
        k = ease_io((t - (T_SIT - 0.2) - i * 0.07) / 1.0)
        px, py = lerp(p0[0], P[i][0], k), lerp(p0[1], P[i][1], k)
        col = PEN if i == 1 else INK2
        circle(cv, px, py, 21, col)
        text(cv, NAMES[i], px, py + 48, F_SANS, 34, col if i == 1 else INK, 1.0, 'c', 'm')
        if k > 0.9:   # little chair backs
            stroke(cv, [(px - 30, py + 20), (px - 30, py - 10)], MUTE, 2.4, (k - 0.9) * 10)
            stroke(cv, [(px + 30, py + 20), (px + 30, py - 10)], MUTE, 2.4, (k - 0.9) * 10)
    if not v: pen_text(cv, "we were standing", cx_ + cw * 0.74, cy_ + ch * 0.62, 54, (t - (T_SIT + 0.7)) / 0.6)
    else: pen_text(cv, "we were standing", cx_ + cw / 2, cy_ + ch - 30, 52, (t - (T_SIT + 0.7)) / 0.6, 'c')

def fig_kpi(cv, t, u, second=False):
    cx_, cy_, cw, ch = frame(cv, "KEY METRICS", "The talk, by the numbers")
    v = cv.vert
    items = [("MINUTES", T_18 - 0.05, None), ("SLIDES", T_SLIDES - 0.05, 0), ("POINTS", T_POINT - 0.05, 0)]
    for i, (lab, t0, val) in enumerate(items):
        k = ease_out((t - t0) / 0.25)
        if k <= 0: continue
        if not v: bw, bh = (cw - 2 * 40) / 3, ch - 10; bx = cx_ + i * (bw + 40); by = cy_ + 6 + (1 - k) * 30
        else: bw, bh = cw, (ch - 2 * 28) / 3; bx = cx_; by = cy_ + i * (bh + 28) + (1 - k) * 30
        rect(cv, bx, by, bw, bh, CARD, k, r=14); rect(cv, bx, by, bw, bh, INK, k, r=14, wd=2)
        num = val if val is not None else int(round(18 * ease_out((t - t0) / 1.6)))
        col = RED if lab == "POINTS" else INK
        if not v:
            text(cv, lab, bx + 34, by + 54, F_SANS, 34, MUTE, k, 'l', 'm', track=3)
            text(cv, str(num), bx + 34, by + bh * 0.62, F_NUM, 230, col, k, 'l', 'm')
        else:
            text(cv, lab, bx + 34, by + bh / 2, F_SANS, 38, MUTE, k, 'l', 'm', track=3)
            text(cv, str(num), bx + bw - 40, by + bh / 2, F_NUM, 170, col, k, 'r', 'm')
    if not v:
        bx3 = cx_ + 2 * ((cw - 80) / 3 + 40)
        pen_text(cv, "checks out", bx3 + 230, cy_ + ch * 0.62, 52, (t - (T_POINT + 0.5)) / 0.5)
    else:
        pen_text(cv, "checks out", cx_ + 300, cy_ + ch - 100, 52, (t - (T_POINT + 0.5)) / 0.5)

TREE = [("Ted", None), ("his father", 0), ("a garage", 1), ("a dream", 1), ("a lesson", 2), ("a handshake", 3),
        ("his father's father", 1), ("the farm", 6), ("a tractor", 7), ("1952", 8), ("a different tractor", 8)]
def fig_tree(cv, t, u, deep=False):
    t0 = T_FATHERb if deep else T_FATHER
    cx_, cy_, cw, ch = frame(cv, "FIG. 4" if not deep else "FIG. 4, CONTINUED",
                            "The story, by generation" if not deep else "The story, continued (generation 5)")
    v = cv.vert
    # layout: generations stacked upward from Ted at the bottom
    gen = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 2, 7: 3, 8: 4, 9: 5, 10: 5}
    order = [0, 1, 2, 3, 4, 5] if not deep else list(range(len(TREE)))
    col_x = {0: 0.5, 1: 0.5, 2: 0.22, 3: 0.5, 4: 0.22, 5: 0.5, 6: 0.80, 7: 0.80, 8: 0.80, 9: 0.62, 10: 0.92}
    if v: col_x.update({2: 0.18, 4: 0.18, 6: 0.82, 7: 0.82, 8: 0.82, 9: 0.6, 10: 0.86})
    gh = (ch - 40) / (3.6 if not deep else 5.4) if not v else (ch - 40) / (4.0 if not deep else 6.0)
    pan = 0.0
    if deep: pan = gh * 2.0 * ease_io((t - t0 - 0.3) / 1.4)
    base_y = cy_ + ch - 40 + pan
    def P(i): return (cx_ + col_x[i] * cw, base_y - gen[i] * gh)
    for j, i in enumerate(order):
        ti = t0 + (j * 0.32 if not deep else max(0, j - 5) * 0.22 - 0.1)
        if deep and j <= 5: ti = t0 - 1
        k = ease_out((t - ti) / 0.3)
        if k <= 0: continue
        name, par = TREE[i]; px, py = P(i)
        if py < cy_ - 10 or py > cy_ + ch + 30: continue
        if par is not None:
            qx, qy = P(par); my = (py + qy) / 2
            stroke(cv, [(qx, qy - 26), (qx, my), (px, my), (px, py + 26)], INK2 if i != 0 else RED, 2.4, k)
        fsz = 50 if not v else 46
        lab_w = tw(name, F_HEAD, fsz) + 44
        rect(cv, px - lab_w / 2, py - 34, lab_w, 68, RED if i == 0 else CARD, k, r=34)
        rect(cv, px - lab_w / 2, py - 34, lab_w, 68, RED if i == 0 else INK, k, r=34, wd=2)
        text(cv, name, px, py, F_HEAD, fsz, CREAM if i == 0 else INK, k, 'c', 'm')
    if deep: pen_text(cv, "we're in 1952", cx_ + cw * (0.06 if not v else 0.02), cy_ + 40, 52, (t - (t0 + 1.4)) / 0.5)
    else: pen_text(cv, "here we go", cx_ + cw * (0.66 if not v else 0.55), cy_ + ch - 30, 52, (t - (t0 + 2.2)) / 0.5)

_WAVE = np.abs(np.random.default_rng(5).normal(0, 1, 4000)).astype(F32)
_WAVE = np.convolve(_WAVE, np.ones(3) / 3, mode='same') * (0.55 + 0.45 * np.sin(np.arange(4000) * 0.07) ** 2)
def fig_wave(cv, t, u, long=False):
    t0 = T_PAUSEb if long else T_PAUSE
    cx_, cy_, cw, ch = frame(cv, "FIG. 5" if not long else "FIG. 5, AGAIN", "Ted's voice, last ten seconds",
                            "Applause during pause: 0" if not long else "Applause during pause: still 0")
    v = cv.vert
    x = cx_; w = cw * (0.82 if not v else 1.0); mid = cy_ + ch * (0.42 if not v else 0.38); amp = ch * (0.30 if not v else 0.22)
    stroke(cv, [(x, mid), (x + w, mid)], GRID, 1.4)
    n = 140; scroll = (t - t0 + 3) * 22
    ps = t0 + 0.6                                         # the pause starts
    for i in range(n):
        xi = x + i * w / n
        st = t - (n - i) / 22                            # time this column was "spoken"
        idx = int(scroll + i) % 3990
        a = _WAVE[idx]
        if st > ps: a = 0.0                               # silence: the pause he thinks is powerful
        if st < t0 - 6: a *= 0.8
        hh = max(1.5, a * amp * 0.85)
        if a > 0: rect(cv, xi, mid - hh, w / n * 0.62, hh * 2, RED, 0.95)
        else: rect(cv, xi, mid - 1.5, w / n * 0.62, 3, INK2, 0.9)
    # bracket over the pause
    bx0 = x + w - (t - ps) * 22 * w / n
    if t > ps + 0.3:
        bx0 = max(x, bx0); bx1 = x + w; by = mid - amp - 30
        k = sstep(ps + 0.3, ps + 0.6, t)
        stroke(cv, [(bx0, by + 14), (bx0, by), (bx1, by), (bx1, by + 14)], INK, 2.4, k)
        secs = "9.8 sec" if long else "4.2 sec"
        text(cv, secs, (bx0 + bx1) / 2, by - 34, F_NUMB, 46, INK, k, 'c', 'm')
        text(cv, "the pause he thinks is powerful", (bx0 + bx1) / 2 if v else bx1, mid + amp + 44, F_ITAL, 40 if not v else 38, INK2, k, 'c' if v else 'r', 'm')
    # applause meter
    if not v:
        mx = cx_ + cw * 0.9; my0 = cy_ + 10; mh = ch * 0.84
        rect(cv, mx, my0, 46, mh, INK, 1.0, r=6, wd=2); text(cv, "APPLAUSE", mx + 23, my0 + mh + 30, F_SANS, 30, MUTE, 1.0, 'c', 'm', track=2)
        text(cv, "0", mx + 23, my0 + mh - 26, F_NUMB, 36, RED, 1.0, 'c', 'm')
    pen_text(cv, "(it wasn't)", cx_ + (40 if not v else 20), cy_ + ch - (40 if not v else 70), 52, (t - (ps + 1.4)) / 0.5)

DONUT = [("His father", 38, INK), ("His journey", 24, INK2), ("Lessons learned", 18, hexc('6e675d')), ("Gratitude", 12, BAR),
         ("Unlocking", 8, hexc('d5ccbd')), ("Your question", 0, PEN)]
def fig_donut(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 6", "Topics covered, share of talk")
    v = cv.vert
    if not v: R = ch * 0.46; dcx = cx_ + R + 40; dcy = cy_ + ch / 2
    else: R = cw * 0.23; dcx = cx_ + cw / 2; dcy = cy_ + R + 10
    rot = (t - T_CIRCLE) * 0.9 - math.pi / 2
    k = ease_out((t - (T_CIRCLE - 0.1)) / 0.9)
    a = rot
    for i, (lab, pct, col) in enumerate(DONUT):
        span = 2 * math.pi * pct / 100 * k
        if pct == 0:
            wedge(cv, dcx, dcy, R * 0.58, R, a, a + 0.012, PEN, 1.0)
        elif span > 0.002:
            wedge(cv, dcx, dcy, R * 0.58, R, a, a + span, RED if i == 0 else col, 1.0)
        a += span
    text(cv, "100%", dcx, dcy - 8, F_NUM, 64, INK, 1.0, 'c', 'm'); text(cv, "of 18 min", dcx, dcy + 44, F_SANSM, 30, MUTE, 1.0, 'c', 'm')
    # legend
    if not v:
        lx, ly, lh = dcx + R + 110, cy_ + 20, (ch - 30) / 6
        L = [(lx, ly + i * lh + lh / 2, 560) for i in range(6)]
    else:
        lx, ly, lh = cx_, dcy + R + 50, 58
        L = [(lx + (i % 2) * cw / 2, ly + (i // 2) * lh + lh / 2, cw / 2 - 30) for i in range(6)]
    for i, (lab, pct, col) in enumerate(DONUT):
        kk = sstep(T_CIRCLE + 0.15 * i, T_CIRCLE + 0.15 * i + 0.3, t)
        x0, yy, wcol = L[i]
        fs = 36 if not v else 34
        rect(cv, x0, yy - 15, 30, 30, RED if i == 0 else col, kk, r=4)
        text(cv, lab, x0 + 46, yy, F_SANS, fs, PEN if pct == 0 else INK, kk, 'l', 'm')
        text(cv, f"{pct}%", x0 + wcol, yy, F_NUMB, fs + 2, PEN if pct == 0 else INK, kk, 'r', 'm')
    xq, yq, wq = L[5]
    if not v:
        pen_arrow(cv, (xq + wq + 80, yq + 60), (xq + wq + 30, yq + 4), (t - (T_CIRCLE + 1.6)) / 0.5, seed=6, bend=0.3)
        pen_text(cv, "mine", xq + wq + 90, yq + 80, 56, (t - (T_CIRCLE + 2.0)) / 0.4)
    else:
        pen_arrow(cv, (xq + wq - 30, yq + 90), (xq + wq - 20, yq + 26), (t - (T_CIRCLE + 1.6)) / 0.5, seed=6, bend=0.3)
        pen_text(cv, "mine", xq + wq - 150, yq + 100, 56, (t - (T_CIRCLE + 2.0)) / 0.4)

def fig_believers(cv, t, u, second=False):
    if second:
        return fig_picto(cv, t, u)
    cx_, cy_, cw, ch = frame(cv, "FIG. 7", "People who believed in him, by year")
    v = cv.vert
    x = cx_ + (90 if not v else 80); y = cy_ + 50; w = cw - (430 if not v else 120); h = ch - (140 if not v else 360)
    years = list(range(1996, 2005)) if not v else list(range(1997, 2003))
    axes(cv, x, y, w, h, [((i + 0.5) / len(years), str(yy)) for i, yy in enumerate(years)], [(0, "0"), (0.5, "5"), (1, "10")],
         ylab="believers", grid=True)
    for i, yy in enumerate(years):
        k = sstep(T_YOUNG + i * 0.08, T_YOUNG + i * 0.08 + 0.2, t)
        xx = x + (i + 0.5) / len(years) * w
        bump = 0.0
        if T_BELIEVE - 0.6 < t < T_BELIEVE + 0.4: bump = 0.0
        text(cv, "0", xx, y + h - 30, F_NUMB, 40, RED, k, 'c', 'm')
    # total tile
    if not v: tx, ty = cx_ + cw - 300, cy_ + 40
    else: tx, ty = cx_ + 20, cy_ + ch - 210
    kt = sstep(T_BELIEVE, T_BELIEVE + 0.3, t)
    rect(cv, tx, ty, 300, 200, CARD, kt, r=14); rect(cv, tx, ty, 300, 200, INK, kt, r=14, wd=2)
    text(cv, "TOTAL", tx + 30, ty + 44, F_SANS, 34, MUTE, kt, 'l', 'm', track=3)
    text(cv, "0", tx + 30, ty + 130, F_NUM, 120, RED, kt, 'l', 'm')
    if not v: pen_text(cv, "nobody. checked twice", tx - 20, ty + 270, 52, (t - (T_BELIEVE + 0.8)) / 0.6, 'l')
    else: pen_text(cv, "nobody. checked twice", tx + 340, ty + 100, 50, (t - (T_BELIEVE + 0.8)) / 0.6, 'l')

WORDS = [("so", 214, RED), ("right?", 96, RED), ("journey", 31, INK2), ("unlock", 27, INK2), ("honestly", 22, INK2), ("the file", 0, PEN)]
def fig_words(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 8", "Ted's most-used words this morning", "Source: I counted")
    v = cv.vert
    lab_w = 230 if not v else 190
    x = cx_ + lab_w; w = cw - lab_w - (150 if not v else 120); n = len(WORDS); rh = ch / n
    starts = [T_V2 + 0.2, T_ENDS + 0.1, T_ENDS + 1.4, T_ENDS + 1.6, T_ENDS + 1.8, T_ENDS + 2.0]
    for i, (word, val, col) in enumerate(WORDS):
        yy = cy_ + i * rh + rh / 2
        k0 = sstep(starts[i] - 0.3, starts[i], t)
        text(cv, word, x - 24, yy, F_SANS, 40, PEN if val == 0 else INK, k0, 'r', 'm')
        if i == 0: g = ease_out((t - starts[0]) / 2.6)
        elif i == 1: g = ease_out((t - starts[1]) / 1.8)
        else: g = ease_out((t - starts[i]) / 0.6)
        if g <= 0: continue
        frac = val / 100.0 * g
        bw = min(frac, (cw - lab_w + 120) / w) * w
        if val > 0: rect(cv, x, yy - rh * 0.3, bw, rh * 0.6, col, 1.0)
        else: stroke(cv, [(x, yy - rh * 0.3), (x, yy + rh * 0.3)], PEN, 3)
        num = int(round(val * g))
        if val >= 100: text(cv, str(num), min(x + bw - 20, cx_ + cw + 60), yy, F_NUMB, 44, CREAM, 1.0, 'r', 'm')
        else: text(cv, str(num), x + bw + 18, yy, F_NUMB, 40, PEN if val == 0 else INK, 1.0, 'l', 'm')
    # axis
    stroke(cv, [(x, cy_ - 6), (x, cy_ + ch)], INK, 2.2)
    yq = cy_ + 5 * rh + rh / 2
    pen_ellipse(cv, x + 26, yq, 54, rh * 0.42, (t - (T_REALQ - 0.9)) / 0.5, seed=9)
    if t > starts[0] + 2.0:
        nx, ny = x + w * (0.56 if not v else 0.42), cy_ + rh * 3.0
        pen_text(cv, "off the chart", nx, ny, 54, (t - (starts[0] + 2.0)) / 0.5)
        pen_arrow(cv, (nx + 160, ny - 40), (min(x + w * 0.92, cx_ + cw - 40), cy_ + rh * 0.86), (t - (starts[0] + 2.5)) / 0.5, seed=10, bend=-0.2)

def fig_nested(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 9", "The real question is…")
    v = cv.vert
    # boxes nested around an anchor near the lower right; continuous zoom in until "about the question I just asked"
    ax_, ay_ = cx_ + cw * (0.70 if not v else 0.62), cy_ + ch * (0.66 if not v else 0.70)
    r = 0.6
    zt = clamp((t - T_REALQ) / (T_ABOUTQ - T_REALQ))
    zz = r ** (-3.0 * ease_io(zt))                      # zoom factor
    bw0, bh0 = cw, ch
    stop = t > T_ABOUTQ - 0.05
    rect(cv, cx_, cy_, cw, ch, INK, 1.0, wd=2.6)                     # the outer frame stays put; the zoom happens inside it
    text(cv, "the real question is", cx_ + 24, cy_ + 40, F_ITAL, 46, INK2, 1.0 - sstep(T_ABOUTQ - 0.3, T_ABOUTQ, t), 'l', 'm')
    for lev in range(1, 9):
        s = (r ** lev) * zz
        if s > 1.0: continue
        fo = 1 - sstep(0.80, 1.0, s)                    # boxes fade as they grow past the figure (never spill onto the page)
        bw, bh = bw0 * s, bh0 * s
        bx = ax_ - (ax_ - cx_) * s; by = ay_ - (ay_ - cy_) * s
        if bw < 26: break
        inner = lev == 3
        if inner and stop:
            k = sstep(T_ABOUTQ - 0.05, T_ABOUTQ + 0.3, t)
            rect(cv, bx, by, bw, bh, CARD, k); rect(cv, bx, by, bw, bh, PEN, k, wd=3)
            fs = min(104, bw / 8.2)
            text(cv, "Is the file ready?", bx + bw / 2, by + bh / 2, F_HEAD, fs, PEN, k, 'c', 'm')
            break
        rect(cv, bx, by, bw, bh, INK, fo, wd=max(1.2, 2.6 * min(1, s)))
        fs = 46 * min(1.4, s * 1.4)
        if fs > 9: text(cv, "the real question is", bx + 24 * s, by + 40 * s, F_ITAL, fs, INK2, fo, 'l', 'm')
    if stop:
        pen_text(cv, "that was my question", cx_ + (30 if not v else 10), cy_ + ch * (0.30 if not v else 0.22), 54, (t - (T_ABOUTQ + 0.8)) / 0.6)

BINGO = [["NORTH STAR", "DOUBLE-CLICK", "SYNERGY", "LEAN IN"],
         ["BANDWIDTH", "JOURNEY", "ALIGNMENT", "UNLOCK"],
         ["DEEP DIVE", "LEVERAGE", "PIVOT", "LEARNINGS"],
         ["MOVE THE NEEDLE", "FREE SPACE", "TAKE IT OFFLINE", "CIRCLE BACK"]]
PRE = {(0, 0), (1, 0), (1, 2), (2, 0), (3, 1), (3, 3), (0, 2)}
def fig_bingo(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 10", "Buzzword bingo, 9:41 a.m.")
    v = cv.vert
    top = 70 if not v else 96                     # room above the card for the pen's BINGO!
    gw = min(cw, 1300) if not v else cw; gh = ch - top
    gx = cx_ + (cw - gw) / 2; gy = cy_ + top
    cwid, chei = gw / 4, gh / 4
    for r in range(4):
        for c in range(4):
            x = gx + c * cwid; y = gy + r * chei
            rect(cv, x, y, cwid, chei, INK, 1.0, wd=1.8)
            word = BINGO[r][c]; fs = 34 if not v else 32
            rows = wrap(word, F_SANS, fs, cwid - 24)
            for i, rr in enumerate(rows): text(cv, rr, x + cwid / 2, y + chei / 2 + (i - (len(rows) - 1) / 2) * fs * 1.15, F_SANS, fs, INK, 1.0, 'c', 'm')
            ts_ = None
            if (r, c) in PRE: ts_ = -10
            if word == "JOURNEY": ts_ = T_JOURNEY - 0.05
            if word == "UNLOCK": ts_ = T_UNLOCK - 0.05
            if ts_ is not None and t > ts_:
                k = ease_out((t - ts_) / 0.12); rad = min(cwid, chei) * 0.36 * (1 + 0.3 * (1 - k))
                circle(cv, x + cwid / 2, y + chei / 2, rad, RED, 0.42 * k)
    if t > T_UNLOCK + 0.15:
        k = clamp((t - (T_UNLOCK + 0.15)) / 0.45); yy = gy + 1.5 * chei
        pen(cv, [(gx - 20, yy + 6), (gx + gw + 20, yy - 6)], k, seed=12, wd=6)
        pen_text(cv, "BINGO!", gx + gw / 2, cy_ + (20 if not v else 34), 66 if not v else 76, (t - (T_UNLOCK + 0.6)) / 0.4, 'c', 'm')

GANTT = [("Standup", 9.25, 9.5), ("Ship the file", 9.5, 11.0), ("1:1 with Priya", 11.0, 11.5), ("Lunch", 12.0, 13.0), ("Deep work", 13.0, 16.0)]
def fig_gantt(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 11", "Today's schedule (revised)")
    v = cv.vert
    lw = 300 if not v else 250
    x = cx_ + lw; w = cw - lw - 20; t0h, t1h = 9.0, 17.0
    n = len(GANTT) + 1; rh = (ch - 60) / n
    def X(hh): return x + (hh - t0h) / (t1h - t0h) * w
    for hh in range(9, 18, 2 if v else 1):
        xx = X(hh); stroke(cv, [(xx, cy_), (xx, cy_ + ch - 50)], GRID, 1.2)
        lab = f"{hh if hh <= 12 else hh - 12}{'a' if hh < 12 else 'p'}"
        text(cv, lab, xx, cy_ + ch - 20, F_SANSM, 30, MUTE, 1.0, 'c', 'm')
    ks = ease_io((t - (T_STORYW - 0.1)) / 1.6)
    for i, (lab, a, b) in enumerate(GANTT):
        yy = cy_ + i * rh + rh / 2
        text(cv, lab, x - 20, yy, F_SANS, 36, INK, 1.0, 'r', 'm')
        dead = ks > 0.2 and i > 0
        rect(cv, X(a), yy - rh * 0.3, X(b) - X(a), rh * 0.6, BAR if dead else (PEN if i == 1 else INK2), 1.0, r=6)
        if dead: stroke(cv, [(x - 20 - tw(lab, F_SANS, 36), yy), (x - 14, yy)], RED, 3.0, sstep(0.2, 0.5, ks))
    yy = cy_ + (n - 1) * rh + rh / 2
    text(cv, "Ted's story", x - 20, yy, F_SANS, 36, RED, sstep(T_STORY, T_STORY + 0.3, t), 'r', 'm')
    if ks > 0: rect(cv, X(9.33), yy - rh * 0.36, (X(17.0) - X(9.33)) * ks, rh * 0.72, RED, 1.0, r=6)
    if ks > 0.98: text(cv, "→ 5:00 p.m.", X(17.0) - 20, yy, F_SANS, 34, CREAM, 1.0, 'r', 'm')
    pen_text(cv, "cool. cool cool.", cx_ + (20 if not v else 0), cy_ - 6, 50, (t - (T_STORYW + 1.3)) / 0.6) if False else None

CAL = [(0, 9.5, 11.5, "Deep work"), (1, 13, 14, "Gym"), (2, 9.5, 11, "Ship the file"), (2, 12, 13, "Lunch"), (3, 10, 12.5, "Deep work"),
       (4, 14, 15.5, "1:1 Priya"), (1, 9.5, 10.5, "Ship the file")]
def fig_calendar(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 12", "My calendar, this week", "Source: the shared calendar")
    v = cv.vert
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    lw = 100 if not v else 92
    x = cx_ + lw; w = cw - lw; top = cy_ + 46; h = ch - 46; h0, h1 = 9, 16
    dw = w / 5
    for i, d in enumerate(days): text(cv, d, x + (i + 0.5) * dw, cy_ + 14, F_SANS, 32, INK2, 1.0, 'c', 'm', track=2)
    for hh in range(h0, h1 + 1):
        yy = top + (hh - h0) / (h1 - h0) * h
        stroke(cv, [(x, yy), (x + w, yy)], GRID, 1.2)
        if hh < h1 and hh % (1 if not v else 2) == 0: text(cv, f"{hh if hh <= 12 else hh - 12}", x - 18, yy + 16, F_SANSM, 30, MUTE, 1.0, 'r', 'm')
    g = clamp((t - (T_GIVEUP - 0.05)) / 1.0)
    for j, (d, a, b, lab) in enumerate(CAL):
        bx = x + d * dw + 6; by = top + (a - h0) / (h1 - h0) * h + 3; bh = (b - a) / (h1 - h0) * h - 6
        gj = clamp(g * 1.4 - j * 0.06)
        fall = (gj ** 2) * 900; rot_col = lerp(1.0, 0.0, gj)
        col = PEN * rot_col + BAR * (1 - rot_col)
        rect(cv, bx, by + fall, dw - 12, bh, col, 1.0 - 0.7 * gj, r=8)
        fs = 32 if not v else 30
        for i, rr in enumerate(wrap(lab, F_SANS, fs, dw - 28)[:2]):
            text(cv, rr, bx + 12, by + fall + 26 + i * fs * 1.1, F_SANS, fs, CREAM, 1.0 - 0.7 * gj, 'l', 'm')
    pen_text(cv, "RIP", x + w * 0.5, top + h * 0.5, 120, (t - (T_GIVEUP + 0.5)) / 0.4, 'c', 'm')

def fig_scatter(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 13", "Minutes talked vs. points made")
    v = cv.vert
    x = cx_ + 100; y = cy_ + 40; w = cw - 140; h = ch - 120
    axes(cv, x, y, w, h, [(i / 36, f"{i}") for i in (0, 12, 24, 36)], [(0, "0"), (0.5, "5"), (1, "10")], ylab="points made", xlab="minutes talked")
    m = 36 * ease_out((t - T_18b) / 4.0) if t > T_18b else 0
    for i in range(int(m * 2)):
        mm = i / 2; xx = x + mm / 36 * w
        circle(cv, xx, y + h - 4, 9, RED, 0.9)
    if m > 18:
        dashed(cv, [(x, y + h - 26), (x + w, y + h - 26)], INK2, 2, sstep(18, 22, m))
        text(cv, "r = 0.00", x + w - 10, y + h - 60, F_MONO, 36, INK, sstep(18, 22, m), 'r', 'm')
    pen_text(cv, "very consistent", x + w * 0.25, y + h * 0.42, 54, (t - (T_18b + 2.5)) / 0.6)

def fig_spiral(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 14", "Distance from your question, over time")
    v = cv.vert
    R = ch * 0.50 if not v else cw * 0.40; ccx = cx_ + (cw * 0.38 if not v else cw / 2); ccy = cy_ + ch / 2 + (8 if not v else -20)
    for i, lab in enumerate(("close", "far", "farther")):
        rr = R * (i + 1) / 3; stroke(cv, circ_pts(ccx, ccy, rr, 90), GRID, 1.4, closed=True)
        text(cv, lab, ccx + 10, ccy - rr + 24, F_SANSM, 34, MUTE, 1.0, 'l', 'm')     # inside each ring, under its line
    circle(cv, ccx, ccy, 12, PEN)
    text(cv, "Is the file ready?", ccx + (0 if v else 0), ccy + 46, F_HEAD, 42, PEN, 1.0, 'c', 'm')
    T0 = T_CIRCLEb - 1.4; s = max(0.0, t - T0)
    ang = -math.pi / 2 + s * 2.6
    rr = R * (0.95 - 0.55 * (1 - math.exp(-s / 2.2))) + R * 0.05 * math.sin(s * 3)
    trail = [(ccx + R * (0.95 - 0.55 * (1 - math.exp(-q / 2.2)) + 0.05 * math.sin(q * 3)) * math.cos(-math.pi / 2 + q * 2.6),
              ccy + R * (0.95 - 0.55 * (1 - math.exp(-q / 2.2)) + 0.05 * math.sin(q * 3)) * math.sin(-math.pi / 2 + q * 2.6)) for q in np.linspace(max(0, s - 2.5), s, 80)]
    if len(trail) > 2: stroke(cv, trail, RED, 3.0, 0.6)
    px, py = ccx + rr * math.cos(ang), ccy + rr * math.sin(ang)
    circle(cv, px, py, 18, RED); text(cv, "Ted", px + 28, py, F_SANS, 34, RED, 1.0, 'l', 'm')
    if not v: pen_text(cv, "so close", cx_ + cw * 0.78, cy_ + ch * 0.5, 56, (t - (T_CIRCLEb + 2.4)) / 0.5, 'c')
    else: pen_text(cv, "so close", cx_ + cw * 0.5, cy_ + ch - 10, 56, (t - (T_CIRCLEb + 2.4)) / 0.5, 'c')

def person(cv, x, y, s, col, op=1.0, asleep=0.0):
    circle(cv, x, y - 46 * s, 22 * s, col, op)
    rect(cv, x - 28 * s, y - 18 * s, 56 * s, 64 * s, col, op, r=22 * s)
    if asleep > 0:
        text(cv, "z", x + 26 * s, y - 80 * s, F_PEN, 46 * s, PEN, asleep * op, 'l', 'm')

def fig_picto(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 15", "Believers in the room")
    v = cv.vert
    n = 7
    if not v: xs = [cx_ + 90 + i * (cw * 0.62 - 90) / (n - 1) for i in range(n)]; ys = [cy_ + ch * 0.58] * n; s = 1.7
    else: xs = [cx_ + 120 + (i % 4) * (cw - 240) / 3 for i in range(n)]; ys = [cy_ + 170 + (i // 4) * 240 for i in range(n)]; s = 1.45
    for i in range(n):
        az = sstep(T_BELIEVEb - 1.4 + i * 0.25, T_BELIEVEb - 1.1 + i * 0.25, t)
        person(cv, xs[i], ys[i], s, BAR, 1.0, az)
    if not v: tx, ty = cx_ + cw * 0.74, cy_ + ch * 0.18
    else: tx, ty = cx_ + cw / 2 - 160, cy_ + ch - 260
    k = sstep(T_BELIEVEb, T_BELIEVEb + 0.3, t)
    text(cv, "0", tx, ty + 110, F_NUM, 220, RED, k, 'l', 'm'); text(cv, "of 7", tx + 150, ty + 140, F_NUMB, 64, INK, k, 'l', 'm')

def fig_ted(cv, t, u):
    text(cv, "Ted.", cv.DW / 2, cv.DH * (0.48 if not cv.vert else 0.47), F_HEAD, 300 if not cv.vert else 260, INK, 1.0, 'c', 'm')

def fig_bridge(cv, t, u):
    x, y, w, h = cv.box; v = cv.vert
    # the paper prints a CORRECTION
    text(cv, "CORRECTION", x, y + 22, F_SANS, 34, RED, 1.0, 'l', 'm', track=4)
    text(cv, "This is a standup.", x, y + 92, F_HEAD, 74 if not v else 70, INK, 1.0, 'l', 'm')
    k15 = sstep(T_FIFTEEN - 0.1, T_FIFTEEN + 0.3, t)
    k8 = sstep(T_EIGHT - 0.05, T_EIGHT + 0.4, t)
    k6 = ease_io((t - (T_SIX - 0.05)) / 1.0)
    shares = np.array([1 / 8] * 8, float)
    shares[0] = lerp(1 / 8, 0.4, k6); shares[1:] = (1 - shares[0]) / 7
    ghost = sstep(T_GHOST - 0.1, T_GHOST + 1.2, t)
    kh = sstep(T_HARD - 0.05, T_HARD + 0.25, t)
    ka = sstep(T_HAS - 0.05, T_HAS + 0.4, t)
    dl = ease_out((t - T_TWO) / 1.0)
    def seg_col(i): return RED if i == 0 else (GHOST if i == 2 and ghost > 0 else BAR)
    def seg_op(i): return k8 * (1 - 0.72 * ghost if i == 2 else 1.0)
    def name_col(i): return RED if i == 0 else (GHOST if i == 2 and ghost > 0.5 else INK)
    def attendance(ax_, ay_, aw_, ah_, years):
        if ka <= 0: return
        text(cv, "Dana's attendance", ax_, ay_ - 34, F_SANS, 34, INK, ka, 'l', 'm')
        stroke(cv, [(ax_, ay_ + ah_), (ax_ + aw_, ay_ + ah_)], INK, 2, ka)
        for i, yy in enumerate(years):
            text(cv, yy, ax_ + i * aw_ / (len(years) - 1), ay_ + ah_ + 36, F_SANSM, 34, MUTE, ka, 'c', 'm')
        pts = [(ax_, ay_ + 10), (ax_ + 30, ay_ + ah_ - 4)] + ([(ax_ + 30 + (aw_ - 30) * dl, ay_ + ah_ - 4)] if dl > 0 else [])
        if ghost > 0: dashed(cv, pts, GHOST, 4, ka)
        else: stroke(cv, pts, INK, 4, ka)
        if dl > 0.9: text(cv, "0 since 2024", ax_ + aw_, ay_ + ah_ - 34, F_SANS, 34, RED, sstep(0.9, 1.0, dl), 'r', 'm')
    if not v:
        bx, by, bw, bh = x + 10, y + 200, w - 20, 104
        text(cv, "15:00", bx + bw, by - 34, F_MONO, 36, INK, k15, 'r', 'm')
        text(cv, "8 people", bx, by - 34, F_SANS, 34, INK2, k8, 'l', 'm')
        rect(cv, bx, by, bw * ease_out((t - T_FIFTEEN) / 0.6), bh, BAR, k15 * 0.5)
        xx = bx
        for i in range(8):
            sw = bw * shares[i]
            if k8 > 0:
                if i == 2 and ghost > 0:
                    P = rrect_pts(xx + 3, by + 3, sw - 6, bh - 6, 4); dashed(cv, P + [P[0]], GHOST, 2.4, k8)
                rect(cv, xx + 3, by + 3, sw - 6, bh - 6, seg_col(i), seg_op(i), r=4)
                text(cv, NAMES[i], xx + sw / 2, by + bh + 36, F_SANS, 34 if i else 38, name_col(i), k8, 'c', 'm')
                if i == 2 and ghost > 0.5: text(cv, "(ghost)", xx + sw / 2, by + bh + 76, F_SANS, 32, GHOST, sstep(0.5, 0.8, ghost), 'c', 'm')
            xx += sw
        if k6 > 0.6: text(cv, "Ted: 6:00", bx + bw * shares[0] / 2, by + bh / 2, F_NUMB, 46, CREAM, sstep(0.6, 0.9, k6), 'c', 'm')
        dx_ = bx + bw * (shares[0] + shares[1] + shares[2])
        if kh > 0:
            stroke(cv, [(dx_, by - 20), (dx_, by + bh + 8)], RED, 4, kh)
            text(cv, "hard stop", dx_ + 10, by - 40, F_SANS, 34, RED, kh, 'l', 'm')
        attendance(x + 870, by + bh + 170, 680, 110, ("2024", "2025", "2026"))
        tx, ty = x + 40, by + bh + 250
        pen_arrow(cv, (tx + 70, ty - 52), (bx + bw * shares[0] * 0.2, by + bh + 12), (t - (T_DIDTHAT - 0.1)) / 0.6, seed=21, bend=0.18, wd=6)
        pen_text(cv, "you did that.", tx, ty, 70, (t - (T_DIDTHAT + 0.3)) / 0.5)
    else:
        bx, by, bw, bh = x + 30, y + 190, 150, h - 260
        text(cv, "15:00", bx, by - 30, F_MONO, 34, INK, k15, 'l', 'm')
        rect(cv, bx, by, bw, bh * ease_out((t - T_FIFTEEN) / 0.6), BAR, k15 * 0.5)
        yy = by
        for i in range(8):
            sh_ = bh * shares[i]
            if k8 > 0:
                rect(cv, bx + 3, yy + 3, bw - 6, sh_ - 6, seg_col(i), seg_op(i), r=4)
                nm = NAMES[i] + (" (ghost)" if i == 2 and ghost > 0.5 else "")
                text(cv, nm, bx + bw + 24, yy + sh_ / 2, F_SANS, 34 if i else 38, name_col(i), k8, 'l', 'm')
            yy += sh_
        if k6 > 0.6: text(cv, "6:00", bx + bw / 2, by + bh * shares[0] / 2, F_NUMB, 42, CREAM, sstep(0.6, 0.9, k6), 'c', 'm')
        dy_ = by + bh * (shares[0] + shares[1] + shares[2])
        if kh > 0:
            stroke(cv, [(bx - 20, dy_), (bx + bw + 10, dy_)], RED, 4, kh)
            text(cv, "hard stop", x + w, dy_, F_SANS, 34, RED, kh, 'r', 'm')
        attendance(x + 500, y + 300, 400, 100, ("2024", "2026"))
        tx, ty = x + 480, y + 200
        pen_arrow(cv, (tx - 14, ty + 20), (bx + bw + 10, by + 46), (t - (T_DIDTHAT - 0.1)) / 0.6, seed=21, bend=0.2, wd=6)
        pen_text(cv, "you did that.", tx, ty, 66, (t - (T_DIDTHAT + 0.3)) / 0.5)

def fig_event(cv, t, u):
    x, y, w, h = cv.box; v = cv.vert
    cw_, chh = (1000, 470) if not v else (900, 560)
    bx = x + w / 2 - cw_ / 2; by = y + h / 2 - chh / 2
    rect(cv, bx, by, cw_, chh, CARD, 1.0, r=18); rect(cv, bx, by, cw_, chh, INK, 1.0, r=18, wd=2)
    rect(cv, bx, by, 18, chh, RED, 1.0)
    text(cv, "Ted Talk", bx + 60, by + 90, F_HEAD, 84, INK, 1.0, 'l', 'm')
    rows = [("Organizer", "—"), ("Invited", "everyone"), ("Ends", "—")]
    for i, (a, b) in enumerate(rows):
        yy = by + 200 + i * (78 if not v else 100)
        text(cv, a, bx + 60, yy, F_SANS, 38, MUTE, 1.0, 'l', 'm')
        text(cv, b, bx + (360 if not v else 330), yy, F_SANS, 42, RED if b == "—" else INK, 1.0, 'l', 'm')
    pen_text(cv, "who sent this??", bx + cw_ - 40, by + chh + (50 if not v else 60), 54, (t - (T_NOSCHED + 0.5)) / 0.5, 'r')

def fig_projection(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 16", "Meeting length, projected")
    v = cv.vert
    x = cx_ + 110; y = cy_ + 40; w = cw - (420 if not v else 150); h = ch - (120 if not v else 300)
    axes(cv, x, y, w, h, [(0, "9:15"), (0.5, "10:30"), (1, "noon")], [(0, "0"), (0.5, "1 hr"), (1, "∞")], ylab="length")
    k = ease_out((t - (T_NOEND - 0.6)) / 0.9)
    act = [(x + f * w * 0.62, y + h - (f ** 1.4) * h * 0.38) for f in np.linspace(0, k, 30)]
    if len(act) > 1: stroke(cv, act, INK, 5)
    kp = ease_in = clamp((t - (T_NOEND + 0.2)) / 1.0)
    if kp > 0:
        xs = np.linspace(0, kp, 40); pts = []
        for f in xs:
            xx = x + w * 0.62 + f * w * 0.36; yy = y + h - h * 0.38 - (f ** 3) * h * 1.6
            if yy < y - 20: break
            pts.append((xx, yy))
        if len(pts) > 1: dashed(cv, pts, RED, 5)
    if kp > 0.8: text(cv, "∞", x + w * 0.99, y - 40, F_NUM, 80, RED, sstep(0.8, 1.0, kp), 'c', 'm')
    # the End meeting button that does nothing
    if not v: bx, by = cx_ + cw - 300, cy_ + ch * 0.5
    else: bx, by = cx_ + cw / 2 - 150, cy_ + ch - 190
    kb = sstep(T_NOEND, T_NOEND + 0.3, t)
    rect(cv, bx, by, 300, 84, BAR, kb, r=42)
    text(cv, "End meeting", bx + 150, by + 42, F_SANS, 36, CREAM, kb, 'c', 'm')
    pen_text(cv, "tried. x14", bx + 150, by + 130, 52, (t - (T_NOEND + 1.2)) / 0.5, 'c')

def fig_venn(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 17", "Q and A")
    v = cv.vert
    R = min(ch * 0.42, cw * 0.27) if not v else cw * 0.27
    mcx, mcy = cx_ + cw / 2, cy_ + ch * (0.5 if not v else 0.44)
    qx, ax = mcx - R * 0.62, mcx + R * 0.62
    kA = 1 - sstep(T_NOA + 0.1, T_NOA + 0.9, t); kQ = 1 - sstep(T_NEVERQ + 0.3, T_NEVERQ + 1.1, t)
    for (cx2, lab, k, col) in ((qx, "Q", kQ, PEN), (ax, "A", kA, RED)):
        if k > 0.02:
            circle(cv, cx2, mcy, R, col, 0.10 * k)
            circle(cv, cx2, mcy, R, col, k, wd=3.5)
        else:
            dashed(cv, circ_pts(cx2, mcy, R, 90), MUTE, 2.4, 0.6)
        text(cv, lab, cx2 + (-R * 0.45 if lab == "Q" else R * 0.45), mcy, F_NUM, 120, col if k > 0.02 else MUTE, max(0.35, k), 'c', 'm')
    text(cv, "0", mcx, mcy, F_NUMB, 64, INK, sstep(T_NOQA, T_NOQA + 0.3, t) * (1 - sstep(T_NEVERQ + 1.1, T_NEVERQ + 1.5, t)), 'c', 'm')
    if t > T_NEVERQ + 1.2:
        text(cv, "∅", mcx, mcy, F_NUM, 200, INK, sstep(T_NEVERQ + 1.2, T_NEVERQ + 1.6, t), 'c', 'm')
    pen_text(cv, "no A", ax + R * 0.2, mcy + R + 50, 54, (t - (T_NOA + 0.4)) / 0.4, 'c')
    pen_text(cv, "never a Q", qx - R * 0.2, mcy + R + 50, 54, (t - (T_NEVERQ + 0.6)) / 0.4, 'c')

def fig_pie100(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 18", "Share of standup spoken, today")
    v = cv.vert
    R = ch * 0.44 if not v else cw * 0.34
    pcx, pcy = cx_ + (cw * 0.32 if not v else cw / 2), cy_ + (ch / 2 if not v else R + 30)
    k = ease_out((t - (T_ALWAYS - 2.3)) / 2.0)
    wedge(cv, pcx, pcy, 0, R, -math.pi / 2, -math.pi / 2 + 2 * math.pi * (0.9 + 0.1 * k), RED, 1.0)
    if k < 0.999: wedge(cv, pcx, pcy, 0, R, -math.pi / 2 + 2 * math.pi * (0.9 + 0.1 * k), 1.5 * math.pi, BAR, 1.0)
    if not v: lx, ly = cx_ + cw * 0.62, cy_ + ch * 0.3
    else: lx, ly = cx_ + 40, pcy + R + 80
    text(cv, f"Ted  {int(round(90 + 10 * k))}%", lx, ly, F_NUMB, 64, RED, 1.0, 'l', 'm')
    text(cv, f"Everyone else  {int(round(10 - 10 * k))}%", lx, ly + 90, F_SANS, 44, INK2, 1.0, 'l', 'm')

def net_pos(cv, cx_, cy_, cw, ch):
    if not cv.vert: Ry = ch * 0.42; Rx = Ry * 1.8; ncx, ncy = cx_ + cw / 2, cy_ + ch / 2 + 50
    else: Rx = Ry = min(cw, ch) * 0.38; ncx, ncy = cx_ + cw / 2, cy_ + ch / 2 + 70
    return [(ncx + Rx * math.cos(-math.pi / 2 + i * 2 * math.pi / 8), ncy + Ry * math.sin(-math.pi / 2 + i * 2 * math.pi / 8)) for i in range(8)]

def ted_drift(t):
    return ease_io((t - (T_PLACE - 0.2)) / 4.2)

def fig_network(cv, t, u):
    cx_, cy_, cw, ch = frame(cv, "FIG. 19", "Team network")
    P = net_pos(cv, cx_, cy_, cw, ch)
    cut = [sstep(T_HESAYS - 0.5 + i * 0.16, T_HESAYS - 0.4 + i * 0.16, t) for i in range(8)]
    for i in range(8):
        for j in range(i + 1, 8):
            if i == 0:
                k = 1 - cut[j]
                if k > 0.01: stroke(cv, [P[0], (lerp(P[0][0], P[j][0], k), lerp(P[0][1], P[j][1], k))], RED, 2.2, 0.85)
            else: stroke(cv, [P[i], P[j]], GRID, 1.6, 0.9)
    off = sstep(T_HAVING - 0.1, T_HAVING + 0.3, t)
    dr = ted_drift(t)
    for i in range(1, 8):
        circle(cv, P[i][0], P[i][1], 26, PEN if i == 1 else INK2)
        dy = 50 if P[i][1] > cy_ + ch / 2 else -50
        text(cv, NAMES[i], P[i][0], P[i][1] + dy, F_SANS, 34, PEN if i == 1 else INK, 1.0, 'c', 'm')
    if dr < 0.02:
        circle(cv, P[0][0], P[0][1], 30, RED * (1 - off) + BAR * off)
        circle(cv, P[0][0], P[0][1], 44, RED * (1 - off) + BAR * off, 0.6, wd=2.5)
        # the label sits above Ted's node (clear of Jo and Me)
        text(cv, "Ted" + (" · offline" if off > 0.5 else ""), P[0][0], P[0][1] - 66, F_SANS, 38, RED if off < 0.5 else MUTE, 1.0, 'c', 'm')
    if T_ANYWAY - 0.2 < t < T_HESAYS + 1.0:
        k = sstep(T_ANYWAY - 0.2, T_ANYWAY + 0.2, t) * (1 - sstep(T_HESAYS + 0.5, T_HESAYS + 0.9, t))
        q = "“happy to take this offline”"
        if not cv.vert: text(cv, q, P[0][0] + 80, P[0][1] - 66, F_ITAL, 46, INK, k, 'l', 'm')
        else: text(cv, q, P[0][0], P[0][1] - 124, F_ITAL, 44, INK, k, 'c', 'm')

def footnote_y(cv): return cv.DH + (260 if not cv.vert else 380)

def fig_drift(cv, t, u):
    """Ted's dot leaves the network, the page and the frame; the camera follows it down to the footnotes."""
    x, y, w, h = cv.box
    cx_, cy_, cw, ch = frame(cv, "FIG. 19", "Team network")
    P = net_pos(cv, cx_, cy_, cw, ch)
    for i in range(1, 8):
        for j in range(i + 1, 8): stroke(cv, [P[i], P[j]], GRID, 1.6, 0.9)
    for i in range(1, 8):
        circle(cv, P[i][0], P[i][1], 26, PEN if i == 1 else INK2)
        dy = 50 if P[i][1] > cy_ + ch / 2 else -50
        text(cv, NAMES[i], P[i][0], P[i][1] + dy, F_SANS, 34, PEN if i == 1 else INK, 1.0, 'c', 'm')
    dr = ted_drift(t)
    fy = footnote_y(cv)
    kf = sstep(T_REACH - 0.3, T_REACH + 0.2, t)
    tx = lerp(P[0][0], x + 14, dr) + 160 * math.sin(dr * 3.1) * (1 - dr)
    ty = lerp(P[0][1], fy - 40, dr)
    rr = lerp(30, 8, dr)
    circle(cv, tx, ty, rr, BAR, 1 - kf)
    # the footnotes at the bottom of the (now taller) page; in 9:16 they step aside for the end card, which sits right here
    kn = kf * (1 - sstep(T_END - 0.3, T_END + 0.3, t)) if cv.vert else kf
    stroke(cv, [(x, fy - 100), (x + 360, fy - 100)], INK, 2.0, kn)
    text(cv, "NOTES", x, fy - 136, F_SANS, 34, MUTE, kn, 'l', 'm', track=4)
    fs1, fs2 = (72, 52) if not cv.vert else (62, 46)
    text(cv, "¹", x, fy - 26, F_HEAD, fs1 * 0.72, RED, kn, 'l', 'm')
    text(cv, C.typed("Ted. Location unknown.", t, T_REACH, T_REACH + 1.1), x + 44, fy, F_ITAL, fs1, INK, kn, 'l', 'm')
    text(cv, C.typed("Last seen taking it offline.", t, T_REACH + 1.2, T_REACH + 2.4), x + 44, fy + fs1 * 1.15, F_ITAL, fs2, INK2, kn, 'l', 'm')

def drift_cam(cv, t):
    """camera pans down the page to the footnotes"""
    k = ease_io((t - (T_PLACE + 0.6)) / 3.2)
    return k * (footnote_y(cv) - cv.DH * (0.62 if not cv.vert else 0.58))

# ---------------------------------------------------------------- schedule
FIGS = [
    (-1.0, T_V1 - 0.1, fig_front, {}),
    (T_V1 - 0.1, T_DIFF - 0.06, fig_flow, {}),
    (T_DIFF - 0.06, T_ASK - 0.06, fig_line, {}),
    (T_ASK - 0.06, T_DIM + 0.15, fig_question, {}),
    (T_DIM + 0.05, STAMPS[0] + 0.05, fig_seating, {}),
    (STAMPS[0] + 1.2, T_FATHER - 0.05, fig_kpi, {}),
    (T_FATHER - 0.05, T_PAUSE - 0.05, fig_tree, {}),
    (T_PAUSE - 0.05, STAMPS[1] + 0.05, fig_wave, {}),
    (STAMPS[1] + 1.15, T_RAFTER - 0.05, fig_donut, {}),
    (T_RAFTER - 0.05, T_V2 - 0.6, fig_believers, {}),
    (T_V2 - 0.6, T_REALQ - 0.06, fig_words, {}),
    (T_REALQ - 0.06, T_JOURNEY - 0.4, fig_nested, {}),
    (T_JOURNEY - 0.4, T_STORY - 0.06, fig_bingo, {}),
    (T_STORY - 0.06, T_CAL - 0.06, fig_gantt, {}),
    (T_CAL - 0.06, STAMPS[2] + 0.05, fig_calendar, {}),
    (STAMPS[2] + 1.2, T_FATHERb - 0.05, fig_scatter, {}),
    (T_FATHERb - 0.05, T_PAUSEb - 0.05, fig_tree, {"deep": True}),
    (T_PAUSEb - 0.05, STAMPS[3] + 0.05, fig_wave, {"long": True}),
    (STAMPS[3] + 1.15, T_RAFTERb - 0.05, fig_spiral, {}),
    (T_RAFTERb - 0.05, T_STOP + 0.6, fig_picto, {}),
    (T_STOP + 0.6, T_STANDUP - 0.08, fig_ted, {}),
    (T_STANDUP - 0.08, STAMPS[4] + 0.05, fig_bridge, {}),
    (STAMPS[4] + 1.2, T_NOEND - 0.06, fig_event, {}),
    (T_NOEND - 0.06, T_NOQA - 0.06, fig_projection, {}),
    (T_NOQA - 0.06, STAMPS[5] + 0.05, fig_venn, {}),
    (STAMPS[5] + 0.05, T_ANYWAY - 0.3, fig_pie100, {}),
    (T_ANYWAY - 0.3, T_PLACE - 0.2, fig_network, {}),
    (T_PLACE - 0.2, DUR + 5, fig_drift, {}),
]

def draw_figs(cv, t):
    for a, b, fn, kw in FIGS:
        if not (a - 0.3 <= t <= b + 0.3): continue
        ein = ease_out((t - (a - 0.04)) / 0.24) if a > 0 else 1.0
        eout = ease_io((t - (b - 0.1)) / 0.2)
        op = ein * (1 - eout)
        if op <= 0.004: continue
        cv.op = op; cv.dy = (1 - ein) * 46 - eout * 46
        if fn is fig_question:
            z = zoom_out(cv, t); cv.z = z
            x, y, w, h = cv.box; cv.cx, cv.cy = x + w / 2, y + h / 2 + 10
            page_beyond(cv, t, z)
        if fn is fig_drift:
            cv.dy -= drift_cam(cv, t)
        fn(cv, t, t - a, **kw)
        cv.z = 1.0; cv.cx, cv.cy = cv.DW / 2, cv.DH / 2; cv.dy = 0.0; cv.op = 1.0

# ---------------------------------------------------------------- lyrics (newsprint captions, red marker on the sung word)
def lyrics(img, t, W, H):
    if C.STATE["clean"]: return
    vert = H > W; k = W / (1080 if vert else 1920)
    fs = int((64 if not vert else 58) * k); maxw = W * (0.80 if not vert else 0.80)
    ybase = H * (0.855 if not vert else 0.705)
    flt = C.STATE["lyric_filter"]
    skip = lambda L: L['text'].startswith("It's a Ted talk") or L['text'].startswith("It's always") or L['text'].strip() == "Ted."
    vis = [L for L in TM.lines if (flt is None or flt(L)) and not skip(L)]
    a = amb(t); dark = 1 - a
    col = INK * (1 - dark) + CREAM * dark
    for li, L in enumerate(vis):
        nxt = vis[li + 1]['s'] if li + 1 < len(vis) else 1e9
        prv = (vis[li - 1]['e'] + 0.45) if li > 0 else -1e9
        if prv > L['s'] - 0.3: a0, a1 = L['s'] - 0.07, L['s'] + 0.05
        else: a0, a1 = L['s'] - 0.3, L['s']
        if L['e'] + 0.45 > nxt - 0.3: b0, b1 = nxt - 0.17, nxt - 0.07
        else: b0, b1 = L['e'] + 0.05, L['e'] + 0.45
        if not (a0 <= t <= b1): continue
        opl = sstep(a0, a1, t) * (1 - sstep(b0, b1, t))
        if opl <= 0.003: continue
        items = list(zip(L['words'], L['wt']))
        nexts = [items[j + 1][1] for j in range(len(items) - 1)] + [L['e'] + 0.3]
        sp = C.text_w(" ", F_SANS, fs); rows = [[]]; cw = 0
        for j, (w_, tt) in enumerate(items):
            ww = C.text_w(w_, F_SANS, fs)
            if rows[-1] and cw + sp + ww > maxw: rows.append([]); cw = 0
            rows[-1].append((w_, tt, ww, nexts[j])); cw += ww + (sp if rows[-1] else 0)
        lh = fs * 1.32; y0 = ybase - (len(rows) - 1) * lh / 2 - lh * 0.25 * (1 - opl)
        for ri, row in enumerate(rows):
            x = (W - (sum(r[2] for r in row) + sp * (len(row) - 1))) / 2
            for w_, tt, ww, nt in row:
                kw = sstep(tt - 0.12, tt + 0.05, t)
                act = sstep(tt - 0.06, tt + 0.02, t) * (1 - sstep(nt - 0.06, nt + 0.04, t))   # only the word being sung
                yy = y0 + ri * lh
                if act > 0.02:   # red marker swipe behind the word being sung
                    swipe = clamp((t - tt + 0.04) / 0.14)
                    m = np.zeros((int(fs * 1.25), int(ww + fs * 0.5)), np.float32)
                    cv2.rectangle(m, (0, int(fs * 0.12)), (int((ww + fs * 0.5) * swipe), int(fs * 1.13)), 1.0, -1)
                    m = cv2.GaussianBlur(m, (0, 0), 1.2) * (0.62 if dark < 0.5 else 0.9) * act * opl
                    X0 = int(x - fs * 0.25); Y0 = int(yy - fs * 0.05)
                    hh, ww2 = m.shape; X1, Y1 = min(W, X0 + ww2), min(H, Y0 + hh)
                    if X1 > max(0, X0) and Y1 > max(0, Y0):
                        mm = m[max(0, -Y0):Y1 - Y0, max(0, -X0):X1 - X0][..., None]
                        reg = img[max(0, Y0):Y1, max(0, X0):X1]; mc = REDL if dark < 0.5 else RED
                        reg *= (1 - mm); reg += mm * mc
                op = opl * (0.35 + 0.65 * kw)
                spr = C.sprite(w_, F_SANS, fs, 9)
                if dark > 0.05: C.shadow(img, spr, x, yy + 2 * k, 0.9 * op * dark)
                C.blit(img, C.sprite(w_, F_SANS, fs, 0), x, yy, col, op)
                x += ww + sp

# ---------------------------------------------------------------- tabloid stamp: IT'S A TED TALK.
def tabloid(img, t, W, H):
    if C.STATE["clean"]: return
    vert = H > W; k = W / (1080 if vert else 1920)
    for i, s in enumerate(STAMPS):
        x = t - s; always = i == len(STAMPS) - 1
        dur = (T_ANYWAY - 0.4 - s) if always else 1.12
        if not (0 <= x < dur + 0.12): continue
        op = sstep(0, 0.03, x) * (1 - sstep(dur - 0.05, dur + 0.12, x))
        word = "IT'S ALWAYS A TED TALK." if always else "IT'S A TED TALK."
        fs = int((210 if not vert else 150) * k)
        if vert and always: fs = int(124 * k)
        spr = C.sprite(word, F_TAB, fs, 0)
        if spr[0].shape[1] > W * 0.9:
            fs = int(fs * W * 0.9 / spr[0].shape[1]); spr = C.sprite(word, F_TAB, fs, 0)
        a = spr[0]; th, tw_ = a.shape
        pad = int(46 * k); bh, bw = th + pad, tw_ + pad * 2
        ban = np.zeros((bh + int(90 * k), bw, 4), F32)
        ban[int(90 * k):, :, :3] = RED; ban[int(90 * k):, :, 3] = 1.0
        y0 = int(90 * k) + pad // 2 - int(fs * 0.04)
        reg = ban[y0:y0 + th, pad:pad + tw_]; aa = a[:reg.shape[0], :reg.shape[1]][..., None]
        reg[..., :3] = reg[..., :3] * (1 - aa) + CREAM * aa
        kick = C.sprite("BREAKING", F_SANS, int(40 * k), 0, track=int(6 * k))[0]
        kh, kw_ = kick.shape; kx = 0; ky = int(90 * k) - kh - int(10 * k)
        ban[ky:ky + kh + int(14 * k), kx:kx + kw_ + int(28 * k), :3] = INK; ban[ky:ky + kh + int(14 * k), kx:kx + kw_ + int(28 * k), 3] = 1.0
        rk = ban[ky + int(7 * k):ky + int(7 * k) + kh, kx + int(14 * k):kx + int(14 * k) + kw_]
        rk[..., :3] = rk[..., :3] * (1 - kick[..., None]) + CREAM * kick[..., None]
        sc = 1.0 + 0.22 * (1 - ease_out(x / 0.16))
        ang = -2.2 + 1.2 * (1 - ease_out(x / 0.2))
        cx, cy = W / 2, H * (0.47 if not vert else 0.46)
        M = cv2.getRotationMatrix2D((bw / 2, (bh + 90 * k) / 2), ang, sc)
        M[0, 2] += cx - bw / 2; M[1, 2] += cy - (bh + 90 * k) / 2
        warped = cv2.warpAffine(ban, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        al = warped[..., 3:4] * op
        sh = cv2.GaussianBlur(warped[..., 3], (0, 0), 14 * k)[..., None] * 0.35 * op
        img *= (1 - sh); img *= (1 - al); img += warped[..., :3] * al

# ---------------------------------------------------------------- frame
def render_frame(t, W=1920, H=1080, fi=0):
    img = paper(W, H)
    cv = Cv(img, W, H)
    tp = T_PILL
    if not cv.vert and not C.STATE["clean"]:   # the masthead steps aside while the subscribe pill is up (16:9)
        cv.op = 1 - sstep(tp - 0.1, tp + 0.3, t) * (1 - sstep(tp + 4.6, tp + 5.0, t))
    if not (T_PLACE + 0.6 < t):
        masthead(cv, t)
    else:
        cv.dy = -drift_cam(cv, t); masthead(cv, t); cv.dy = 0.0
    cv.op = 1.0
    draw_figs(cv, t)
    if T_SOW - 0.3 < t < T_DIM + 0.6:      # the zoomed-out page slides under a fixed masthead
        yb = int(round((186 if not cv.vert else 372) * cv.k)); fe = max(2, int(14 * cv.k))
        a = np.clip((yb - np.arange(yb + fe, dtype=F32)) / fe + 1.0, 0, 1)[:, None, None]
        img[:yb + fe] = img[:yb + fe] * (1 - a) + paper(W, H)[:yb + fe] * a
        masthead(cv, t)
    fig_so(cv, t)
    light(img, t, W, H)
    lyrics(img, t, W, H)
    tabloid(img, t, W, H)
    if not C.STATE["clean"]:
        C.subscribe_pill(img, t, W, H, T_PILL, 5.0)
        C.end_screen(img, t, W, H, T_END, DUR - T_END, "It's always a Ted talk.", sub_line="Subscribe for a new song every week",
                     title="TED Talk, in charts", accent=RED)
    return finish(img, t, fi)
