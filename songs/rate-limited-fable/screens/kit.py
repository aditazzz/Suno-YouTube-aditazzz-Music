"""Rate Limited: the 2D screen layers' shared kit (rl_screens, Nov 15 2026).

Every frame is a pure function of time t (seconds, audio time). Shapes are drawn through 4x masks so curved edges are clean;
text is PIL's own antialiased text, recorded with studio.textfit so tools/text_fit_check.py can measure it.
Screens are never brighter than WHITE_MAX (her note Nov 15: no blown highlights), so a screen can be lit and graded without clipping.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SONG = os.path.join(ROOT, 'songs', 'rate-limited')
OUT = os.path.join(SONG, 'build', 'screens')
sys.path.insert(0, ROOT)
from studio import textfit  # noqa: E402

FPS = 30
WHITE_MAX = 236                      # brightest screen pixel (no blown highlights)
FD = os.path.join(ROOT, 'assets', 'fonts')
_FONTS = {}


def font(name, size):
    files = {'reg': 'Inter-Regular.otf', 'med': 'Inter-Medium.otf', 'semi': 'Inter-SemiBold.otf', 'bold': 'InterDisplay-Bold.otf',
             'black': 'InterDisplay-Black.otf', 'light': 'InterDisplay-Light.otf', 'mono': 'JBMono-400.ttf', 'monob': 'JBMono-700.ttf',
             'hand': 'Caveat-Medium.ttf', 'disp': 'InterDisplay-Bold.otf'}
    k = (name, int(size))
    if k not in _FONTS:
        _FONTS[k] = ImageFont.truetype(os.path.join(FD, files[name]), int(size))
    return _FONTS[k]


# ------------------------------------------------------------------ colour
BLUE = (34, 122, 246)                # her sent bubbles (as in the approved close frame)
RED = (214, 52, 52)                  # the 429, and only the 429
GREEN = (52, 178, 110)               # it went through
INK = (20, 22, 28)


def W(a=255, v=WHITE_MAX):
    return (v, v, v, a)


# ------------------------------------------------------------------ timing
def _load_shots():
    p = os.path.join(SONG, 'build', 'shots', 'shots.json')
    if os.path.exists(p):
        d = json.load(open(p))
        rows = d['shots'] if isinstance(d, dict) and 'shots' in d else d
        out = {}
        for r in rows:
            sid = r.get('id') or r.get('shot')
            s = r.get('start_s', r.get('start')); e = r.get('end_s', r.get('end'))
            out[sid] = dict(start=float(s), end=float(e), onsets=r.get('cues') or r.get('onsets') or {}, src='shots.json')
        return out
    rows = json.load(open(os.path.join(SONG, 'build', 'shots', 'boards_parsed.json')))
    return {r['id']: dict(start=float(r['start_b']), end=float(r['end_b']), onsets={}, src='boards_parsed.json') for r in rows}


SHOTS = _load_shots()
BEATS = [b + 0.23 for b in json.load(open(os.path.join(SONG, 'bts_reel', 'work', 'beats_midi.json')))]


def shot(sid):
    return SHOTS[sid]


def beats_in(sid):
    s = SHOTS[sid]
    return [b for b in BEATS if s['start'] - .02 <= b < s['end'] - .02]       # a beat 2 ms before the cut is this shot's beat 1


def onset(sid, word, fallback):
    """measured on-word onset from shots.json when it has one, else the fallback time (a beat of the grid)"""
    o = SHOTS[sid].get('onsets') or {}
    if isinstance(o, dict):
        for k, v in o.items():
            if word.lower() in k.lower():
                return float(v if not isinstance(v, dict) else v.get('t', fallback))
    if isinstance(o, list):
        for r in o:
            if word.lower() in (str(r.get('cue', '')) + ' | ' + str(r.get('word', r.get('label', '')))).lower():
                return float(r.get('t', r.get('onset', fallback)))
    return fallback


# ------------------------------------------------------------------ motion (pure functions of time)
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lin(t, t0, t1):
    return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_io(x):
    return x * x * (3 - 2 * x)


def spring(t, t0, freq=3.2, damp=0.42):
    """0 before t0; a damped spring that overshoots once and settles at 1"""
    if t <= t0:
        return 0.0
    x = t - t0; w = 2 * math.pi * freq
    wd = w * math.sqrt(1 - damp * damp)
    return 1 - math.exp(-damp * w * x) * (math.cos(wd * x) + damp / math.sqrt(1 - damp * damp) * math.sin(wd * x))


def fade(t, t0, dur=0.12):
    return ease_io(lin(t, t0, t0 + dur))


# ------------------------------------------------------------------ drawing (antialiased through 4x masks)
SS = 4


def _mask_shape(w, h, fn):
    m = Image.new('L', (w * SS, h * SS), 0); fn(ImageDraw.Draw(m), SS)
    return m.resize((w, h), Image.LANCZOS)


def rrect_mask(w, h, r):
    w, h = max(1, int(round(w))), max(1, int(round(h)))
    return _mask_shape(w, h, lambda d, s: d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), radius=r * s, fill=255))


def paste_mask(img, mask, xy, fill, alpha=1.0):
    """composite a solid colour through mask at integer xy"""
    if alpha <= 0:
        return
    col = Image.new('RGBA', mask.size, fill[:3] + (255,))
    a = mask if (alpha >= 1 and (len(fill) < 4 or fill[3] == 255)) else mask.point(lambda v: int(v * alpha * (fill[3] if len(fill) > 3 else 255) / 255))
    col.putalpha(a)
    img.alpha_composite(col, (int(round(xy[0])), int(round(xy[1]))))


def rrect(img, box, r, fill, alpha=1.0):
    x0, y0, x1, y1 = box
    paste_mask(img, rrect_mask(x1 - x0, y1 - y0, r), (x0, y0), fill, alpha)


def circle(img, cx, cy, r, fill, alpha=1.0):
    d = int(math.ceil(2 * r)) + 2
    m = _mask_shape(d, d, lambda dr, s: dr.ellipse(((d / 2 - r) * s, (d / 2 - r) * s, (d / 2 + r) * s, (d / 2 + r) * s), fill=255))
    paste_mask(img, m, (cx - d / 2, cy - d / 2), fill, alpha)


def ring(img, cx, cy, r, width, fill, start=-90, end=270, alpha=1.0):
    d = int(math.ceil(2 * r + width)) + 4
    def fn(dr, s):
        c = d / 2
        dr.arc(((c - r) * s, (c - r) * s, (c + r) * s, (c + r) * s), start, end, fill=255, width=int(width * s))
    paste_mask(img, _mask_shape(d, d, fn), (cx - d / 2, cy - d / 2), fill, alpha)


def poly(img, pts, fill, alpha=1.0):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; x0, y0 = int(min(xs)) - 2, int(min(ys)) - 2
    w, h = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
    m = _mask_shape(w, h, lambda dr, s: dr.polygon([((x - x0) * s, (y - y0) * s) for x, y in pts], fill=255))
    paste_mask(img, m, (x0, y0), fill, alpha)


def shadow(img, box, r, blur, offset=(0, 0), alpha=0.35, spread=0):
    x0, y0, x1, y1 = box; pad = int(blur * 3)
    m = Image.new('L', (int(x1 - x0) + 2 * pad, int(y1 - y0) + 2 * pad), 0)
    ImageDraw.Draw(m).rounded_rectangle((pad - spread, pad - spread, pad + x1 - x0 + spread, pad + y1 - y0 + spread), radius=r, fill=int(255 * alpha))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    col = Image.new('RGBA', m.size, (0, 0, 0, 255)); col.putalpha(m)
    img.alpha_composite(col, (int(x0 - pad + offset[0]), int(y0 - pad + offset[1])))


def sprite_scaled(img, spr, anchor_xy, pivot, scale, alpha=1.0):
    """place sprite spr so that its pivot (fraction of its size) lands on anchor_xy, scaled about that pivot"""
    if scale <= 0.01 or alpha <= 0.003:
        return
    w, h = spr.size
    if abs(scale - 1) > 1e-3:
        sw, sh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
        s2 = spr.resize((sw, sh), Image.BICUBIC)
    else:
        s2, sw, sh = spr, w, h
    if alpha < 1:
        s2 = s2.copy(); s2.putalpha(s2.getchannel('A').point(lambda v: int(v * alpha)))
    x = anchor_xy[0] - pivot[0] * sw; y = anchor_xy[1] - pivot[1] * sh
    _paste_sub(img, s2, x, y)


def _paste_sub(img, spr, x, y):
    """sub-pixel placement (so slow moves don't step): shift by the fraction with an affine resample"""
    ix, iy = math.floor(x), math.floor(y); fx, fy = x - ix, y - iy
    if fx > 1e-3 or fy > 1e-3:
        spr = spr.transform((spr.width + 1, spr.height + 1), Image.AFFINE, (1, 0, -fx, 0, 1, -fy), resample=Image.BILINEAR)
    img.alpha_composite(spr, (int(ix), int(iy))) if ix >= 0 and iy >= 0 and ix + spr.width <= img.width and iy + spr.height <= img.height else _paste_clip(img, spr, ix, iy)


def _paste_clip(img, spr, ix, iy):
    l, t = max(0, -ix), max(0, -iy); r, b = min(spr.width, img.width - ix), min(spr.height, img.height - iy)
    if r > l and b > t:
        img.alpha_composite(spr.crop((l, t, r, b)), (ix + l, iy + t))


def text_w(txt, f):
    return ImageDraw.Draw(Image.new('L', (4, 4))).textlength(txt, font=f)


def clamp_white(img):
    """no screen pixel above WHITE_MAX (her note: no blown highlights)"""
    a = np.asarray(img).copy(); a[..., :3] = np.minimum(a[..., :3], WHITE_MAX)
    return Image.fromarray(a, img.mode)


# ------------------------------------------------------------------ output
def frames_for(sid, handle=6):
    s = SHOTS[sid]
    f0 = int(round(s['start'] * FPS)) - handle; f1 = int(round(s['end'] * FPS)) + handle
    return list(range(max(0, f0), f1))


def save_seq(folder, frame, img):
    os.makedirs(folder, exist_ok=True)
    img.save(os.path.join(folder, f'f_{frame:05d}.png'), compress_level=3)


def write_meta(folder, **kw):
    os.makedirs(folder, exist_ok=True)
    json.dump(kw, open(os.path.join(folder, 'layer.json'), 'w'), indent=1)
