"""Shared building blocks for Allow (Fangs for Asking).

Everything works in linear-light float32 RGB. Plates come in as sRGB 8-bit, are linearised once, and the film finish
(fx.finish) converts back at the very end. All randomness is seeded, so any frame renders identically every time.
"""
import math, os
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

F32 = np.float32
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(ROOT, "fonts")
if not os.path.isdir(FONTS):                                # inside deadletter-studio: the shared fonts
    FONTS = os.path.join(ROOT, "..", "..", "assets", "fonts")


# ------------------------------------------------------------------ colour
def to_lin(u8):
    x = u8.astype(F32) / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(F32)


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(F32)


def luma(img): return (img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722).astype(F32)


def rgb(*c): return np.array(c, F32)


def hexlin(h):
    h = h.lstrip('#'); c = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)[None, None]
    return to_lin(c)[0, 0]


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sstep(a, b, x):
    if b == a: return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def ease_io(t): t = clamp(t); return t * t * t * (t * (6 * t - 15) + 10)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def lerp(a, b, t): return a + (b - a) * t
def win(t, a, b, fi=0.3, fo=0.3): return sstep(a - fi, a, t) * (1 - sstep(b, b + fo, t))


# ------------------------------------------------------------------ noise
def n1(t, seed=0, freq=1.0, octaves=3):
    """Smooth deterministic 1-D noise in [-1, 1]."""
    v = 0.0; amp = 1.0; tot = 0.0
    for o in range(octaves):
        x = t * freq * (2 ** o) + seed * 17.13 + o * 3.7
        i = math.floor(x); f = x - i
        def h(k):
            s = math.sin((k + seed * 101 + o * 57) * 12.9898) * 43758.5453
            return (s - math.floor(s)) * 2 - 1
        u = f * f * (3 - 2 * f)
        v += amp * (h(i) * (1 - u) + h(i + 1) * u); tot += amp; amp *= 0.5
    return v / tot


def fbm2(h, w, cell, seed=0, octaves=4, gain=0.5):
    """Smooth 2-D fractal noise in roughly [0, 1], size (h, w). `cell` = size in px of the coarsest octave."""
    rng = np.random.RandomState(seed)
    out = np.zeros((h, w), F32); amp = 1.0; tot = 0.0; c = float(cell)
    for o in range(octaves):
        gh, gw = max(2, int(h / c) + 3), max(2, int(w / c) + 3)
        g = rng.rand(gh, gw).astype(F32)
        up = cv2.resize(g, (int(gw * c), int(gh * c)), interpolation=cv2.INTER_CUBIC)
        oy, ox = rng.randint(0, max(1, up.shape[0] - h)), rng.randint(0, max(1, up.shape[1] - w))
        out += amp * up[oy:oy + h, ox:ox + w]; tot += amp; amp *= gain; c = max(2.0, c / 2)
    return np.clip(out / tot, 0, 1)


def blur(img, s):
    if s <= 0.3: return img
    return cv2.GaussianBlur(img, (0, 0), s)


def fast_blur(img, s):
    """Large Gaussian via downscale; fine for soft light maps."""
    if s < 6: return blur(img, s)
    k = int(max(1, s / 4)); h, w = img.shape[:2]
    small = cv2.resize(img, (max(1, w // k), max(1, h // k)), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), s / k)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


# ------------------------------------------------------------------ type
@lru_cache(64)
def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), int(round(size)))


def text_mask(s, name, size, pad=None, track=0.0):
    """White-on-black float mask of a string (tight box + padding). Returns (mask, (w, h))."""
    f = font(name, size)
    pad = int(size * 0.35) if pad is None else pad
    if track:
        widths = [f.getlength(ch) for ch in s]
        tw = int(sum(widths) + track * size * (len(s) - 1))
    else:
        tw = int(f.getlength(s))
    asc, desc = f.getmetrics()
    im = Image.new('L', (tw + 2 * pad, asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    if track:
        x = pad
        for ch, wch in zip(s, widths):
            d.text((x, pad), ch, font=f, fill=255); x += wch + track * size
    else:
        d.text((pad, pad), s, font=f, fill=255)
    return np.asarray(im, F32) / 255.0


def paste_add(dst, src, x, y, w=1.0):
    """dst[y:, x:] += src*w, clipped to bounds. src 2-D or 3-D."""
    H, W = dst.shape[:2]; h, ww = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + ww), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    sub = src[y0 - y:y1 - y, x0 - x:x1 - x]
    if dst.ndim == 3 and sub.ndim == 2: sub = sub[..., None]
    dst[y0:y1, x0:x1] += sub * w


def place(canvas_shape, src, x, y):
    """Return a canvas-sized array with src placed at (x, y)."""
    out = np.zeros(canvas_shape[:2] + src.shape[2:], F32)
    paste_add(out, src, x, y)
    return out


# ------------------------------------------------------------------ film finish
_CACHE = {}


def _vignette(W, H, strength):
    k = ('vig', W, H, strength)
    if k not in _CACHE:
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2 * 0.9)
        _CACHE[k] = (1 - strength * np.clip(r - 0.35, 0, None) ** 1.6).astype(F32)[..., None]
    return _CACHE[k]


def _grain_bank(W, H, n=6, pad=96):
    k = ('grain', W, H)
    if k not in _CACHE:
        rng = np.random.RandomState(1234); bank = []
        for _ in range(n):
            g = rng.standard_normal(((H + pad) // 2 + 1, (W + pad) // 2 + 1)).astype(F32)
            g = cv2.resize(g, (W + pad, H + pad), interpolation=cv2.INTER_LINEAR)
            g = g * 0.7 + rng.standard_normal((H + pad, W + pad)).astype(F32) * 0.3
            bank.append(g)
        _CACHE[k] = bank
    return _CACHE[k]


def _srgb_lut():
    if 'lut' not in _CACHE:
        q = (np.arange(4096, dtype=np.float64) / 4095.0) ** 2           # index = sqrt(linear) * 4095 (fine in the shadows)
        v = np.where(q <= 0.0031308, q * 12.92, 1.055 * np.power(q, 1 / 2.4) - 0.055)
        _CACHE['lut'] = v.astype(F32)
    return _CACHE['lut']


def to_srgb_fast(x):
    idx = (np.sqrt(np.clip(x, 0, 1)) * 4095 + 0.5).astype(np.uint16)
    return _srgb_lut()[idx]


def finish(img, t, seed=0, grain=0.035, halation=0.18, vignette=0.22, letterbox=2.0, lift=0.004, expo=1.0):
    """Linear in, sRGB uint8 out: exposure, highlight roll-off, halation, split-tone, vignette, grain, letterbox."""
    H, W = img.shape[:2]
    x = img * expo if expo != 1.0 else img
    if halation > 0:
        hi = np.clip(luma(x) - 0.55, 0, None)
        if hi.max() > 0:
            hal = fast_blur(hi, W * 0.006) * 0.6 + fast_blur(hi, W * 0.02) * 0.4
            x = x + hal[..., None] * (rgb(1.0, 0.32, 0.12) * halation)
    x = x / (1.0 + x * 0.32) * 1.18                       # filmic shoulder
    if vignette > 0: x = x * _vignette(W, H, vignette)
    x = x + lift * rgb(0.55, 0.85, 1.0)                    # charcoal-teal floor instead of dead black
    out = to_srgb_fast(x)
    if grain > 0:
        bank = _grain_bank(W, H)
        fi = int(round(t * 30)); rng = np.random.RandomState((seed * 7919 + fi) % (2 ** 31))
        g = bank[rng.randint(len(bank))]; ox, oy = rng.randint(0, 96), rng.randint(0, 96)
        g = g[oy:oy + H, ox:ox + W]
        m = luma(out); wgt = (0.35 + 1.3 * m * (1 - m)) * grain
        out = out + (g * wgt)[..., None]
    out = np.clip(out, 0, 1)
    if letterbox:
        vis = int(round(W / letterbox)); bar = max(0, (H - vis) // 2)
        if bar: out[:bar] = 0; out[H - bar:] = 0
    return (out * 255 + 0.5).astype(np.uint8)
