"""DEADLETTER fine-line rendering helpers (skia)."""
import os, math, random
import numpy as np
import skia

W, H = 1920, 1080
FPS = 30

# palette
BG = skia.Color(10, 10, 11)
IVORY = (237, 229, 211)
SILVER = (201, 206, 214)
COOL = (168, 186, 206)      # faint blue undertone (the honest one)
DIM = (120, 118, 112)

FONT_DIR = os.environ.get('EARLY_FONTS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'studio-early', 'fonts')) + '/'  # repo layout (the chat used an absolute path)
TF_SERIF_I = skia.Typeface.MakeFromFile(FONT_DIR + 'cormorant-garamond-latin-300-italic.ttf')
TF_SERIF_IB = skia.Typeface.MakeFromFile(FONT_DIR + 'cormorant-garamond-latin-500-italic.ttf')
TF_SERIF = skia.Typeface.MakeFromFile(FONT_DIR + 'cormorant-garamond-latin-300-normal.ttf')
TF_MONO = skia.Typeface.MakeFromFile(FONT_DIR + 'jetbrains-mono-latin-300-normal.ttf')
TF_MONO4 = skia.Typeface.MakeFromFile(FONT_DIR + 'jetbrains-mono-latin-400-normal.ttf')


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

def ease_out(t):
    t = clamp(t); return 1 - (1 - t) ** 3

def ease_in(t):
    t = clamp(t); return t ** 3

def ease_io(t):
    t = clamp(t); return 3 * t * t - 2 * t * t * t

def ease_io5(t):
    t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10)

def ramp(t, a, b):
    """0 before a, 1 after b, linear between"""
    if b <= a:
        return 1.0 if t >= a else 0.0
    return clamp((t - a) / (b - a))

def window(t, a, b, fin=0.3, fout=0.3):
    """fade-in at a, fade-out ending at b"""
    return min(ease_io(ramp(t, a, a + fin)), 1 - ease_io(ramp(t, b - fout, b)))


def col(c, a=1.0):
    return skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, clamp(a))


def mix(c1, c2, t):
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))


# ---------------------------------------------------------------- paint
def stroke_paint(c, a=1.0, w=2.0, blur=0.0, dash=None, cap=skia.Paint.kRound_Cap):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                   StrokeCap=cap, StrokeJoin=skia.Paint.kRound_Join)
    p.setColor4f(col(c, a))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(dash[0], dash[1] if len(dash) > 1 else 0))
    return p


def fill_paint(c, a=1.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kFill_Style)
    p.setColor4f(col(c, a))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def glow_stroke(canvas, path, c=IVORY, a=1.0, w=2.0, glow=1.0, dash=None):
    """fine line with soft halo"""
    if a <= 0.003:
        return
    if glow > 0:
        canvas.drawPath(path, stroke_paint(COOL if c == IVORY else c, a * 0.22 * glow, w * 4, blur=7, dash=dash))
        canvas.drawPath(path, stroke_paint(c, a * 0.35 * glow, w * 1.8, blur=2.2, dash=dash))
    canvas.drawPath(path, stroke_paint(c, a, w, dash=dash))


# ---------------------------------------------------------------- paths
def P():
    return skia.Path()


def path_length(path):
    pm = skia.PathMeasure(path, False)
    total = 0.0
    while True:
        total += pm.getLength()
        if not pm.nextContour():
            break
    return total


def trim(path, a, b):
    """portion of path between fractions a..b of total length (all contours)"""
    a, b = clamp(a), clamp(b)
    if b <= a:
        return skia.Path()
    if a <= 0 and b >= 1:
        return path
    total = path_length(path)
    sa, sb = a * total, b * total
    out = skia.Path()
    pm = skia.PathMeasure(path, False)
    acc = 0.0
    while True:
        L = pm.getLength()
        lo, hi = max(sa - acc, 0), min(sb - acc, L)
        if hi > lo:
            pm.getSegment(lo, hi, out, True)
        acc += L
        if acc >= sb or not pm.nextContour():
            break
    return out


def sample_path(path, step=4.0):
    """list of contours, each an array of points"""
    pm = skia.PathMeasure(path, False)
    contours = []
    while True:
        L = pm.getLength()
        if L > 0:
            n = max(2, int(L / step))
            pts = []
            for i in range(n + 1):
                r = pm.getPosTan(L * i / n)
                pos = r[0] if isinstance(r, tuple) else r
                pts.append((pos.x(), pos.y()))
            contours.append(np.array(pts))
        if not pm.nextContour():
            break
    return contours


def poly(pts, closed=False):
    p = skia.Path()
    if len(pts) == 0:
        return p
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def transformed(path, tx=0, ty=0, s=1.0, rot=0.0, sx=None, sy=None):
    m = skia.Matrix()
    m.setTranslate(tx, ty)
    if rot:
        m.preRotate(rot)
    m.preScale(sx if sx is not None else s, sy if sy is not None else s)
    out = skia.Path(path)
    out.transform(m)
    return out


# ---------------------------------------------------------------- text
_font_cache = {}

def font(tf, size):
    k = (id(tf), round(size, 1))
    if k not in _font_cache:
        f = skia.Font(tf, size)
        f.setSubpixel(True)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        _font_cache[k] = f
    return _font_cache[k]


def text_width(s, tf, size, tracking=0.0):
    f = font(tf, size)
    return f.measureText(s) + tracking * max(0, len(s) - 1)


def draw_text(canvas, s, x, y, tf, size, c=IVORY, a=1.0, align='center', tracking=0.0, glow=0.0, blur=0.0):
    if a <= 0.003 or not s:
        return
    f = font(tf, size)
    w = text_width(s, tf, size, tracking)
    if align == 'center':
        x0 = x - w / 2
    elif align == 'right':
        x0 = x - w
    else:
        x0 = x
    if glow > 0:
        gp = fill_paint(c, a * 0.35 * glow, blur=size * 0.18)
        _draw_tracked(canvas, s, x0, y, f, tracking, gp)
    _draw_tracked(canvas, s, x0, y, f, tracking, fill_paint(c, a, blur=blur))


def _draw_tracked(canvas, s, x0, y, f, tracking, paint):
    if tracking == 0:
        canvas.drawString(s, x0, y, f, paint)
        return
    x = x0
    for ch in s:
        canvas.drawString(ch, x, y, f, paint)
        x += f.measureText(ch) + tracking


def reveal_text(canvas, s, x, y, tf, size, t, t_in, t_out, c=IVORY, a=1.0, align='center',
                tracking=0.0, stagger=0.022, dur=0.45, rise=14, glow=0.6, out_dur=0.35, blur_in=True):
    """per-character reveal (fade + rise + unblur), whole-line fade out"""
    if t < t_in - 0.05 or t > t_out + out_dur:
        return
    f = font(tf, size)
    w = text_width(s, tf, size, tracking)
    x0 = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    fo = 1 - ease_io(ramp(t, t_out, t_out + out_dur))
    xx = x0
    n = len(s)
    for i, ch in enumerate(s):
        cw = f.measureText(ch)
        if ch != ' ':
            k = ease_out(ramp(t, t_in + i * stagger, t_in + i * stagger + dur))
            aa = a * k * fo
            if aa > 0.003:
                yy = y + (1 - k) * rise
                bl = (1 - k) * 6 if blur_in else 0
                if glow > 0:
                    canvas.drawString(ch, xx, yy, f, fill_paint(c, aa * 0.3 * glow, blur=size * 0.2))
                canvas.drawString(ch, xx, yy, f, fill_paint(c, aa, blur=bl))
        xx += cw + tracking


# ---------------------------------------------------------------- overlays
def make_grain(n=10, seed=1):
    rng = np.random.default_rng(seed)
    imgs = []
    for _ in range(n):
        g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        v = np.clip(128 + g * 40, 0, 255).astype(np.uint8)
        rgba = np.dstack([v, v, v, np.full_like(v, 255)])
        img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
        imgs.append(img)
    return imgs


def make_vignette():
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 0))
    shader = skia.GradientShader.MakeRadial(
        (W / 2, H / 2), W * 0.72,
        [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0.78)],
        [0.0, 0.45, 1.0])
    p = skia.Paint(Shader=shader)
    c.drawRect(skia.Rect(0, 0, W, H), p)
    return surf.makeImageSnapshot()


def make_bg():
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    shader = skia.GradientShader.MakeRadial(
        (W / 2, H * 0.46), W * 0.6,
        [skia.Color4f(19 / 255, 19 / 255, 21 / 255, 1), skia.Color4f(10 / 255, 10 / 255, 11 / 255, 1)],
        [0.0, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=shader))
    return surf.makeImageSnapshot()


def noise1(x, seed=0):
    """smooth 1D value noise in [-1,1]"""
    i = math.floor(x)
    f = x - i
    def h(n):
        n = (n * 374761393 + seed * 668265263) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return (n & 0xFFFF) / 32767.5 - 1.0
    u = f * f * (3 - 2 * f)
    return lerp(h(i), h(i + 1), u)
