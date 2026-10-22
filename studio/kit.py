"""Reusable 2D kit for colorful scenes: grids/gradients, rounded panels, chat bubbles, labels, stickers.
Text helpers keep the readability floor (see core.MIN_READ); pass sizes already multiplied by ts.
"""
import math
import numpy as np, cv2
from . import core as C
from .core import sstep, ease_out, sprite, blit, text_w, shadow, F_INTER, F_DISP, F_DISPB, WHITE, hexc

INK = hexc('0d0b1a'); RED = hexc('ff2e3d')
BUBBLE_ME = hexc('2f6bff')
def ssa(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)

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


def desat(img, k):
    if k <= 0: return img
    g = img.mean(2, keepdims=True) * np.array([0.95, 0.97, 1.05], np.float32)
    return img * (1 - k) + g * k


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



# ---------------------------------------------------------------- code editor / terminal widgets
def editor(img, x, y, w, h, lines, op, ts, *, fs=None, bg=None, fg=None, gutter=None, hl=None, hl_col=None,
           blame=None, blame_col=None, blame_w=0, title=None, scroll=0.0, cursor=None, t=0.0, line_no0=1):
    """Code panel. lines: list of str or (str, col). hl: set/list of highlighted row indexes. blame: per-row author str.
    cursor: (row, col_chars) to draw a blinking caret. Text >= 38 px for readability."""
    if op <= 0.01: return
    from .core import F_MONO, F_MONOB
    fs = int(fs or 40 * ts); bg = bg if bg is not None else hexc('15131f'); fg = fg if fg is not None else hexc('e9e4ff')
    panel(img, x, y, w, h, bg, op, r=int(22 * ts), shadow_op=0.55)
    top = y + 20 * ts
    if title:
        for i, c in enumerate((hexc('ff5f57'), hexc('febc2e'), hexc('28c840'))):
            cv2.circle(img, (int(x + (34 + i * 30) * ts), int(y + 32 * ts)), int(9 * ts), (c * op + img[int(y + 32 * ts), int(x + 34 * ts)] * 0).tolist(), -1, cv2.LINE_AA)
        blit(img, sprite(title, F_MONOB, int(30 * ts)), x + w / 2, y + 32 * ts, fg * 0.7, op, anchor='c')
        top = y + 70 * ts
    lh = fs * 1.42; n_vis = int((y + h - top - 10 * ts) / lh)
    gw = text_w("000", F_MONO, int(fs * 0.8)) + 30 * ts
    first = int(scroll); frac = scroll - first
    H, W = img.shape[:2]
    for k in range(n_vis + 1):
        i = first + k
        if i >= len(lines): break
        yy = top + (k - frac) * lh
        if yy < top - 2 or yy + lh > y + h - 4: continue
        s = lines[i]; col = fg
        if isinstance(s, tuple): s, col = s
        if hl is not None and i in hl:
            panel(img, x + 8 * ts, yy - 4 * ts, w - 16 * ts, lh, hl_col if hl_col is not None else hexc('ff4d6d') * 0.6, op * 0.85, r=int(10 * ts), shadow_op=0)
        blit(img, sprite(str(line_no0 + i), F_MONO, int(fs * 0.8)), x + gw - 10 * ts - text_w(str(line_no0 + i), F_MONO, int(fs * 0.8)), yy + fs * 0.12, fg * 0.45, op)
        xx = x + gw + 10 * ts
        if blame is not None and blame_w:
            b = blame[i] if i < len(blame) else ""
            if b:
                bc = blame_col[i] if isinstance(blame_col, (list, tuple)) else (blame_col if blame_col is not None else hexc('ff7a90'))
                blit(img, sprite(b, F_MONOB, int(fs * 0.85)), xx, yy + fs * 0.06, bc, op)
            xx += blame_w
        if s: blit(img, sprite(s, F_MONO if col is fg else F_MONOB, fs), xx, yy, col, op)
        if cursor is not None and cursor[0] == i and int(t * 2.2) % 2 == 0:
            cx = xx + text_w(s[:cursor[1]], F_MONO, fs) + 2
            cv2.rectangle(img, (int(cx), int(yy + fs * 0.1)), (int(cx + fs * 0.12), int(yy + fs * 1.15)), (fg * op).tolist(), -1)

def typed_line(s, t, t0, cps=18.0):
    if t < t0: return ""
    return s[:int((t - t0) * cps) + 1]

def heart_pts(cx, cy, s, n=48):
    pts = []
    for k in range(n):
        u = k / n * 2 * math.pi
        pts.append((cx + 16 * math.sin(u) ** 3 * s / 34, cy - (13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)) * s / 34))
    return np.array(pts, np.int32)

def fill_poly(img, pts, col, op):
    if op <= 0.01: return
    x0, y0 = np.maximum(pts.min(0) - 2, 0); x1, y1 = pts.max(0) + 3
    H, W = img.shape[:2]; x1 = min(W, x1); y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.float32); cv2.fillPoly(m, [pts - [x0, y0]], 1.0, cv2.LINE_AA)
    reg = img[y0:y1, x0:x1]; q = m[..., None] * op; reg *= (1 - q); reg += q * col

def chip(img, s, cx, cy, fs, bg, fg, op, pop_t=None, t=0.0):
    """Big rounded word chip (dark text on bright fill), pops in."""
    if op <= 0.01: return
    sc = 1.0
    if pop_t is not None: sc = 0.5 + 0.5 * ease_out((t - pop_t) / 0.2) + 0.12 * math.exp(-max(0, t - pop_t) * 7)
    fs2 = int(fs * sc); w = text_w(s, F_DISP, fs2) + fs2 * 1.1; h = fs2 * 1.75
    panel(img, cx - w / 2, cy - h / 2, w, h, bg, op, r=int(h * 0.45), shadow_op=0.5)
    blit(img, sprite(s, F_DISP, fs2), cx, cy, fg, op, anchor='c')

def kaleido(G, t, sat=1.0, seg=8, speed=0.25):
    R, A = G['R'], G['A']; s = 2 * math.pi / seg
    a = np.abs(((A + t * speed) % s) - s / 2)
    p = np.cos(R * 11 - t * 3.2 + a * 7) * 0.5 + np.cos(a * 13 + R * 4 + t * 1.3) * 0.5
    ph = p * 0.22 + R * 0.45 - t * 0.12
    img = 0.5 + 0.5 * np.cos(6.2832 * (ph[..., None] + np.array([0.0, 0.33, 0.67], np.float32)))
    g = img.mean(2, keepdims=True); img = g + (img - g) * sat
    return img * (0.42 + 0.30 * (0.5 + 0.5 * p))[..., None]

def rays(G, t, c1, c2, n=12, speed=0.4):
    m = ssa(-0.15, 0.15, np.sin(G['A'] * n + t * speed))[..., None]
    return c1 * (1 - m) + c2 * m
