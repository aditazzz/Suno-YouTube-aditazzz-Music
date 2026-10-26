"""Shared scene pieces: loading plates, candle flames, keyed cut-outs, lyric typography."""
import math, os
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw
from .fx import F32, to_lin, rgb, blur, fast_blur, n1, paste_add, font, luma, sstep, clamp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@lru_cache(16)
def _read(i):
    return cv2.cvtColor(cv2.imread(os.path.join(ROOT, 'plates', f'{i}.png')), cv2.COLOR_BGR2RGB)


_UP = {}


def _read_up(i):
    """The Real-ESRGAN version from tools/upscale.py (plates/up/<i>.png), if it exists (re-checked until found)."""
    if i in _UP: return _UP[i]
    p = os.path.join(ROOT, 'plates', 'up', f'{i}.png')
    if not os.path.exists(p): return None
    _UP.clear()                                   # keep at most one big plate in memory
    _UP[i] = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)
    return _UP[i]


def plate_pixels(i, w2, h2):
    """Plate i at (w2, h2): from the upscaled master when there is one (area-downsampled), else a Lanczos resize."""
    up = _read_up(i)
    if up is not None:
        return cv2.resize(up, (w2, h2), interpolation=cv2.INTER_AREA if up.shape[1] >= w2 else cv2.INTER_LANCZOS4)
    return cv2.resize(_read(i), (w2, h2), interpolation=cv2.INTER_LANCZOS4)


# where to centre a vertical (9:16) crop of each plate, as a fraction of its width
FOCUS_V = {2: 0.56, 4: 0.55, 5: 0.55, 6: 0.30, 11: 0.72, 12: 0.58, 13: 0.62, 14: 0.66, 16: 0.64, 17: 0.47, 3: 0.62, 10: 0.42}


def load_plate(i, W, H):
    """Plate i scaled to cover W x H (centre crop). Returns (linear float, scale, (ox, oy)) where
    output = plate * scale - (ox, oy), in the ORIGINAL plate's pixel coordinates."""
    src = _read(i); ph, pw = src.shape[:2]
    s = max(W / pw, H / ph)
    w2, h2 = int(round(pw * s)), int(round(ph * s))
    up = plate_pixels(i, w2, h2)
    ox, oy = (w2 - W) // 2, (h2 - H) // 2
    if H > W and i in FOCUS_V:
        ox = int(min(max(0, FOCUS_V[i] * w2 - W / 2), w2 - W))
    return to_lin(up[oy:oy + H, ox:ox + W]), s, (ox, oy), up[oy:oy + H, ox:ox + W]


def grid(H, W):
    yy, xx = np.mgrid[0:H, 0:W].astype(F32); return yy, xx


def flame(H, W, t, bx, by, fw, fh, s, strength=1.0, lean=0.0, gutter=0.0, seed=0, halo=1.0):
    """Candle flame + halo as additive linear RGB. (bx, by) wick base in output px; fw half-width, fh height (output px)."""
    if strength <= 0.001: return np.zeros((H, W, 3), F32)
    flick = 1.0 + 0.10 * n1(t, 3 + seed, 7.0) + 0.05 * n1(t, 5 + seed, 19.0)
    hgt = fh * (0.92 + 0.12 * n1(t, 8 + seed, 3.0)) * (0.55 + 0.45 * strength) * (1 - 0.45 * gutter)
    wid = fw * (1.0 + 0.08 * n1(t, 9 + seed, 5.0))
    sway = (0.10 * n1(t, 11 + seed, 1.3) + 0.06 * n1(t, 12 + seed, 4.0) + 0.55 * lean) * hgt
    pad = int(hgt * 1.4) + 4
    x0, y0 = int(bx - pad), int(by - hgt - pad)
    x1, y1 = int(bx + pad), int(by + pad * 0.4)
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(F32)
    v = np.clip((by - ys) / hgt, -0.3, 1.4)
    bend = sway * np.clip(v, 0, 1) ** 1.7
    u = (xs - bx - bend) / wid
    prof = np.where(v < 0.25, np.sqrt(np.clip(v / 0.25, 0, 1)) * (0.75 + 0.25 * v / 0.25),
                    np.clip(1 - (v - 0.25) / 0.75, 0, 1) ** 0.85)
    r = np.abs(u) / np.maximum(prof, 1e-3)
    body = np.clip(1 - r, 0, 1) ** 0.6 * (v > -0.05) * (v < 1.0)
    body = blur(body.astype(F32), max(0.5, 0.004 * fh * 6))
    core = np.clip(1 - r * 1.6, 0, 1) * np.clip(1 - np.abs(v - 0.35) * 2.2, 0, 1)
    blue_base = np.exp(-((v + 0.02) / 0.09) ** 2) * np.clip(1 - r, 0, 1)
    col = (body[..., None] * rgb(1.0, 0.62, 0.22) * 3.2 + core[..., None] * rgb(1.0, 0.92, 0.75) * 5.5
           - blue_base[..., None] * rgb(0.6, 0.4, 0.1) * 1.5 + blue_base[..., None] * rgb(0.05, 0.12, 0.45) * 1.2)
    col = np.clip(col, 0, None) * flick * strength
    out = np.zeros((H, W, 3), F32)
    paste_add(out, col.astype(F32), x0, y0)
    if halo > 0:
        hx, hy = bx + sway * 0.5, by - hgt * 0.5
        R = fh * 0.55
        bx0, by0 = int(max(0, hx - R * 12)), int(max(0, hy - R * 12)); bx1, by1 = int(min(W, hx + R * 12)), int(min(H, hy + R * 12))
        yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(F32)
        d2 = ((xx - hx) ** 2 + ((yy - hy) * 0.8) ** 2) / R ** 2
        hal = (np.exp(-d2) * 0.35 + 0.12 / (1 + d2 * 0.4)) * strength * flick * halo
        out[by0:by1, bx0:bx1] += hal[..., None] * rgb(1.0, 0.55, 0.2)
    return out


def paint_out(up_u8, mask_u8, radius=6, k=2):
    """Inpaint a region of an sRGB uint8 image at a working size; returns linear float of the patched image."""
    H, W = mask_u8.shape
    small = cv2.resize(up_u8, (W // k, H // k), interpolation=cv2.INTER_AREA)
    ms = cv2.resize(mask_u8, (W // k, H // k), interpolation=cv2.INTER_NEAREST)
    inp = cv2.inpaint(small, ms, radius, cv2.INPAINT_TELEA)
    return to_lin(cv2.resize(inp, (W, H), interpolation=cv2.INTER_CUBIC))


@lru_cache(4)
def silhouette():
    """Plate 7: the man in the coat, keyed off flat grey. Returns float alpha (h, w)."""
    g = cv2.cvtColor(_read(7), cv2.COLOR_RGB2GRAY).astype(F32) / 255
    bg = np.median(g[:40, :40])
    a = np.clip((bg - g) / (bg - 0.06), 0, 1)
    return a


# ------------------------------------------------------------------ lyrics
LYR_FONT = 'CormorantGaramond-SemiBold.ttf'
LYR_FONT_I = 'CormorantGaramond-MediumItalic.ttf'


def lyric(img, text, W, H, op=1.0, italic=False, size=0.054, y_frac=None, color=(0.86, 0.80, 0.70), track=0.02):
    """Quiet cinematic lyric line: ivory serif, soft shadow, centred low in the picture (above the letterbox).
    Vertical frames: smaller, wrapped to two lines if needed, and kept above the Shorts/Reels UI."""
    if op <= 0.002 or not text: return img
    portrait = H > W
    fs = (W * 0.050 * size / 0.054) if portrait else H * size
    f = font(LYR_FONT_I if italic else LYR_FONT, fs)
    def measure(s_): return sum(f.getlength(ch) for ch in s_) + track * fs * (len(s_) - 1)
    lines = [text]
    if measure(text) > W * 0.86 and ' ' in text:
        words = text.split(' '); best = None
        for k in range(1, len(words)):
            a_, b_ = ' '.join(words[:k]), ' '.join(words[k:])
            sc = max(measure(a_), measure(b_))
            if best is None or sc < best[0]: best = (sc, [a_, b_])
        lines = best[1]
    asc, desc = f.getmetrics(); pad = int(fs * 0.6); lh = int(fs * 1.18)
    tw = int(max(measure(l) for l in lines))
    m = Image.new('L', (tw + 2 * pad, asc + desc + 2 * pad + lh * (len(lines) - 1)), 0); d = ImageDraw.Draw(m)
    for li, line in enumerate(lines):
        x = pad + (tw - measure(line)) / 2
        for ch in line:
            d.text((x, pad + li * lh), ch, font=f, fill=255); x += f.getlength(ch) + track * fs
    m = np.asarray(m, F32) / 255
    if y_frac is not None: yb = H * y_frac
    elif portrait: yb = H * 0.70
    else:
        vis = int(round(W / 2.0)); bar = (H - vis) // 2
        yb = H - bar - fs * 0.55
    px = W / 2 - m.shape[1] / 2
    py = yb - (asc + pad) + fs * 0.12 - lh * (len(lines) - 1)
    sh = blur(m, fs * 0.10)
    A = np.zeros((H, W), F32); S = np.zeros((H, W), F32)
    paste_add(A, m, px, py); paste_add(S, sh, px + fs * 0.03, py + fs * 0.05)
    img = img * (1 - (S * 0.65 * op)[..., None])
    col = np.array([c ** 2.2 for c in color], F32)
    return img * (1 - (A * op)[..., None]) + (A * op)[..., None] * col
