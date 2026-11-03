"""Shared building blocks for the full film (film.py). Everything here is drawn at 1920x1080, float BGR 0..1."""
import os, sys, math
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
import wkit as K, door2 as D
from witch2 import raster2, rimlight, figure
from witch_back import back_figure
from witch import stroke, bez
W, H = K.W, K.H
MOONCOL = np.array([0.95, 0.94, 0.88], np.float32)
def eio(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)
def eout(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 2
def ein(u): u = min(max(u, 0.0), 1.0); return u * u
def clamp(u): return min(max(u, 0.0), 1.0)
YS, XS = np.mgrid[0:H, 0:W].astype(np.float32)

# ---------------- her moon (IMG_1976), as a full disc ----------------
def _fulltex(n=512):
    """her IMG_1976 moon as a full disc: shading divided out (an albedo map), the unlit part filled from the lit part"""
    m = K._moon; R = K.MOON_R; c = K.MOON_C
    s = (n / 2) / R
    M = np.float32([[s, 0, n / 2 - s * c[0]], [0, s, n / 2 - s * c[1]]])
    t = cv2.warpAffine(m, M, (n, n), flags=cv2.INTER_AREA)
    lum = t.mean(2)
    yy, xx = np.mgrid[0:n, 0:n]; rho = np.sqrt((xx - n / 2 + .5) ** 2 + (yy - n / 2 + .5) ** 2) / (n / 2)
    shade = cv2.GaussianBlur(lum, (0, 0), n * 0.05)
    alb = t / np.maximum(shade, 0.22 * shade.max())[..., None]
    lit = np.clip((shade - 0.08) / 0.10, 0, 1)
    rot = cv2.rotate(alb, cv2.ROTATE_180); rlit = cv2.rotate(lit, cv2.ROTATE_180)
    fill = np.where((rlit > 0.5)[..., None], rot, alb[:, ::-1])
    w = cv2.GaussianBlur(lit, (0, 0), n * 0.02)[..., None]
    full = alb * w + fill * (1 - w)
    full = full / (np.percentile(full[rho < 0.85].mean(-1), 60) + 1e-4) * 0.66
    full = full * (1 - 0.38 * np.clip(rho, 0, 1) ** 2.5)[..., None]
    return np.clip(full, 0, 1).astype(np.float32)
FULL = _fulltex()

def phase_mask(n, p, soft=0.035):
    """p 0 new .. 0.25 first quarter .. 0.5 full .. 0.75 last quarter .. 1 new. -> lit fraction per pixel"""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); x = (xx - n / 2 + .5) / (n / 2); y = (yy - n / 2 + .5) / (n / 2)
    w = np.sqrt(np.clip(1 - y * y, 1e-6, 1)); k = math.cos(2 * math.pi * p)
    p = p % 1.0
    if p <= 0.5: v = (x - k * w) / (w + 1e-3)
    else: v = (-k * w - x) / (w + 1e-3)
    return np.clip(v / soft + 0.5, 0, 1)

_pm = {}
def pmoon(img, c, r, p=0.5, ghost=0.0, glow=0.10, gain=1.0, tint=None, alpha=1.0, earthshine=0.05, blur=0.0):
    """her moon at c, radius r, phase p. ghost: the unlit part drawn as a pale 'suggestion' (autocomplete)."""
    if r < 1 or alpha <= 0: return img
    n = max(8, int(2 * r) + 2)
    key = (n,)
    if key not in _pm: _pm[key] = cv2.resize(FULL, (n, n), interpolation=cv2.INTER_AREA)
    tex = _pm[key] * gain
    if tint is not None: tex = tex * np.asarray(tint, np.float32)
    lit = phase_mask(n, p)[..., None]
    pic = tex * lit + tex * (1 - lit) * earthshine + tex * (1 - lit) * ghost * np.array([1.0, 0.97, 0.94], np.float32) * 0.50
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); rho = np.sqrt((xx - n / 2 + .5) ** 2 + (yy - n / 2 + .5) ** 2) / r
    a = np.clip((1 - rho) * r / 1.2 + 0.5, 0, 1)[..., None] * alpha
    if blur > 0:
        pd = int(blur * 3) + 2; pic = cv2.GaussianBlur(np.pad(pic, ((pd, pd), (pd, pd), (0, 0))), (0, 0), blur)
        a = cv2.GaussianBlur(np.pad(a[..., 0], pd), (0, 0), blur)[..., None]; n += 2 * pd
    out = img
    litfrac = float(phase_mask(16, p).mean()) if True else 1.0
    if glow > 0: out = halo(out, c, r, glow * alpha * (0.25 + 0.75 * litfrac))
    x0, y0 = int(round(c[0] - n / 2)), int(round(c[1] - n / 2))
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + n), min(H, y0 + n)
    if xb <= xa or yb <= ya: return out
    sub = out[ya:yb, xa:xb]; pa = pic[ya - y0:yb - y0, xa - x0:xb - x0]; aa = a[ya - y0:yb - y0, xa - x0:xb - x0]
    out[ya:yb, xa:xb] = sub * (1 - aa) + pa * aa
    return out

def halo(img, c, r, amt, col=MOONCOL, fall=1.4):
    if amt <= 0: return img
    R = int(r * (1 + fall * 5)); x0, y0 = int(c[0] - R), int(c[1] - R)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + 2 * R), min(H, y0 + 2 * R)
    if xb <= xa or yb <= ya: return img
    yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32); d = np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2) / max(r, 1)
    img[ya:yb, xa:xb] += (amt * np.exp(-np.clip(d - 1, 0, None) / fall) * (d > 0.98))[..., None] * np.asarray(col, np.float32)
    return img

# ---------------- skies, plains, reflections ----------------
_bg = {}
def plain(key, hz, camx=0.0, camz=-2.0, mood=1.0, blur=0.0, far_door=True):
    """her lunar plain under a night sky (no big door: draw that per frame). cached"""
    k = (key, hz, camx, camz, mood, blur, far_door)
    if k in _bg: return _bg[k].copy()
    c = K.cam(z=camz, x=camx, hz=hz)
    img = K.sky_grad((0.024, 0.026, 0.034), (0.085, 0.095, 0.115), (0.16, 0.17, 0.20), hz=c["hz"])
    img = img * mood
    g, d = K.ground(tint=(0.60, 0.68, 0.78), haze=(0.13, 0.14, 0.17), haze_m=300.0, exposure=1.05 * mood, c=c)
    img = np.where((d < 1e8)[..., None], g, img)
    img = K.fog_band(img, c["hz"] + 4, 40, 0.6, (0.15, 0.16, 0.19), scale=2.2, offset=0.2 + camx * 0.01, name="cloudframe_46", soft=0.8)
    if far_door:
        fb, fk = K.project(c, -26.0, 70.0); fr = 3.2 * fk
        if fr > 2 and 0 < fb[0] < W: img, _ = D.draw(img, fb[0], fb[1] - fr, fr, 0.0, interior_scale=1.3, fog=0.0, spill=0.5)
    if blur > 0: img = cv2.GaussianBlur(img, (0, 0), blur)
    _bg[k] = img.astype(np.float32)
    return _bg[k].copy()

def night(key="night", top=(0.020, 0.022, 0.030), bot=(0.06, 0.07, 0.09), clouds=0.0):
    k = (key, top, bot, clouds)
    if k in _bg: return _bg[k].copy()
    v = (YS / H)[..., None]
    img = np.array(top, np.float32) * (1 - v) + np.array(bot, np.float32) * v
    if clouds > 0:
        d = K.cloud_tex("cloudframe_40"); d = cv2.resize(d[:, :d.shape[1] // 2], (W, H))
        img = img + (np.clip(d - 0.5, 0, 1) * clouds)[..., None] * np.array([0.25, 0.25, 0.27], np.float32)
    _bg[k] = img.astype(np.float32); return _bg[k].copy()

def reflect(img, hz, k=0.32, blur=3.0, t=0.0):
    """a wet plain: the sky above the horizon mirrored below it, rippled, fading with distance"""
    hz = int(hz); h = min(hz, H - hz)
    if h < 4: return img
    src = img[hz - h:hz][::-1]
    rip = (np.sin(np.arange(h)[:, None] * 0.21 + t * 2.2) * (1.5 + np.arange(h)[:, None] * 0.012)).astype(np.float32)
    src = cv2.remap(src, (XS[:h] + rip).astype(np.float32), YS[:h].copy(), cv2.INTER_LINEAR)
    src = cv2.GaussianBlur(src, (0, 0), blur, sigmaY=blur * 2.5)
    fade = (np.linspace(1, 0, h) ** 1.5)[:, None, None] * k
    out = img.copy(); out[hz:hz + h] = out[hz:hz + h] + np.clip(src - 0.03, 0, None) * fade
    return out

def cast(img, a, org, sdir, k, hz):
    if k <= 0.01: return img
    org = np.asarray(org, float)
    Msh = np.float32([[1, sdir[0], -sdir[0] * org[1]], [0, sdir[1], org[1] * (1 - sdir[1])]])
    s = cv2.warpAffine(a, Msh, (W, H)); s = cv2.GaussianBlur(s, (0, 0), 2.5); s[:max(0, int(hz))] = 0
    return img * (1 - k * s[..., None])

# ---------------- her ----------------
def mirror(fig):
    f = lambda p: np.asarray(p) * np.array([-1.0, 1.0])
    out = dict(solid=[f(p) for p in fig["solid"]], sheer=[(f(p), a) for p, a in fig["sheer"]], hair=[(f(p), w) for p, w in fig["hair"]])
    A = {k: (f(v) if isinstance(v, np.ndarray) and v.shape == (2,) else v) for k, v in fig["A"].items()}
    out["A"] = A; return out

def her(img, fig, org, hgt, light=None, light_col=MOONCOL, rim_k=0.6, fill_k=0.0, silhouette=False, alpha_mul=None, ret_alpha=False):
    """composite her figure. light: screen point of the main light (rim on the edges facing it)"""
    a, sh = raster2(fig, np.asarray(org, float), hgt, (H, W))
    if alpha_mul is not None: a = a * alpha_mul; sh = sh * alpha_mul
    ys_, xs_ = np.nonzero(a > 0.003)
    if len(ys_) == 0: return (img, a) if ret_alpha else img
    p = 24; y0, y1 = max(0, ys_.min() - p), min(H, ys_.max() + p + 1); x0, x1 = max(0, xs_.min() - p), min(W, xs_.max() + p + 1)
    A = a[y0:y1, x0:x1]; S = sh[y0:y1, x0:x1]; I = img[y0:y1, x0:x1]
    col = K.INK + (I - K.INK) * (S * 0.42)[..., None]
    out = I * (1 - A[..., None]) + col * A[..., None]
    if not silhouette and light is not None:
        ctr = np.asarray(org, float) + np.array([0, -0.55 * hgt]); L = np.asarray(light, float) - ctr
        w_ = max(hgt / 300, 0.8)
        out = out + rimlight(A, L, w_, rim_k)[..., None] * light_col * 0.8
        if fill_k > 0:
            dl = np.sqrt((XS[y0:y1, x0:x1] - light[0]) ** 2 + (YS[y0:y1, x0:x1] - light[1]) ** 2); lm = np.exp(-dl / (0.30 * hgt))
            out = out + (A * lm * fill_k)[..., None] * light_col
    lw = A * np.clip(1 - cv2.GaussianBlur(A, (0, 0), 4), 0, 1)
    out = out + lw[..., None] * cv2.GaussianBlur(I, (0, 0), 7) * 0.35
    res = img.copy(); res[y0:y1, x0:x1] = out
    return (res, a) if ret_alpha else res

def flick(t, times, lead=0.0, up=0.85, base=0.30, dur=0.32):
    """arm raise_u for sharp spell-casting flicks at the given times"""
    v = base
    for tt in times:
        u = (t - (tt - lead)) / dur
        if 0 <= u <= 1: v = max(v, base + (up - base) * math.sin(math.pi * min(u * 1.6, 1.0)) ** 0.7 * (1 - max(0, u - 0.62) / 0.38 * 0.6))
    return v

# ---------------- light traces: a figure drawn by a line before it exists ----------------
def trace(img, alpha, u, col=MOONCOL, width=2, amt=0.9, glow=True):
    """draw the outline of `alpha` progressively (u 0..1 of its length)"""
    if u <= 0: return img
    m = (cv2.GaussianBlur(alpha, (0, 0), 3.0) > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs: return img
    c = max(cs, key=len)
    c = cv2.approxPolyDP(c, 1.2, True)[:, 0, :]
    c = np.vstack([np.interp(np.linspace(0, len(c) - 1, len(c) * 6), np.arange(len(c)), c[:, i]) for i in (0, 1)]).T
    c = np.roll(c, -int(np.argmin(c[:, 1])), 0)          # start at the tip of the hat
    n = max(2, int(len(c) * clamp(u)))
    lay = np.zeros((H, W), np.float32)
    cv2.polylines(lay, [c[:n].astype(np.int32)], False, 1.0, width, cv2.LINE_AA)
    if n < len(c): cv2.circle(lay, tuple(int(v) for v in c[n - 1]), width + 2, 1.0, -1, cv2.LINE_AA)
    out = img + lay[..., None] * col * amt
    if glow: out = out + cv2.GaussianBlur(lay, (0, 0), 5)[..., None] * col * amt * 0.8
    return out

# ---------------- tarot cards ----------------
def card_face(n_w, n_h, pic, border=(0.42, 0.62, 0.78)):
    """an old card: the picture inset, a thin double border, dark paper"""
    f = np.zeros((n_h, n_w, 3), np.float32) + np.array([0.05, 0.07, 0.09], np.float32)
    m = int(n_w * 0.08)
    if pic is not None:
        p = cv2.resize(pic, (n_w - 2 * m, n_h - 2 * m), interpolation=cv2.INTER_AREA); f[m:n_h - m, m:n_w - m] = p
    b = np.array(border, np.float32)
    for inset, th in ((int(m * 0.35), max(1, n_w // 160)), (int(m * 0.75), max(1, n_w // 260))):
        cv2.rectangle(f, (inset, inset), (n_w - inset, n_h - inset), tuple(float(x) for x in b * 0.8), th, cv2.LINE_AA)
    return f

def card_back(n_w, n_h):
    f = np.zeros((n_h, n_w, 3), np.float32) + np.array([0.06, 0.05, 0.05], np.float32)
    b = (0.30, 0.45, 0.58); m = int(n_w * 0.08)
    cv2.rectangle(f, (m // 2, m // 2), (n_w - m // 2, n_h - m // 2), b, max(1, n_w // 160), cv2.LINE_AA)
    c = (n_w // 2, n_h // 2); r = int(n_w * 0.22)
    cv2.circle(f, c, r, b, max(1, n_w // 150), cv2.LINE_AA)
    cv2.ellipse(f, (c[0] + r // 3, c[1]), (int(r * 0.8), r), 0, 0, 360, (0.06, 0.05, 0.05), -1, cv2.LINE_AA)
    cv2.circle(f, c, r, b, max(1, n_w // 150), cv2.LINE_AA)
    for k in range(8):
        a = k * math.pi / 4; p1 = (int(c[0] + math.cos(a) * r * 1.3), int(c[1] + math.sin(a) * r * 1.3)); p2 = (int(c[0] + math.cos(a) * r * 1.6), int(c[1] + math.sin(a) * r * 1.6))
        cv2.line(f, p1, p2, b, max(1, n_w // 200), cv2.LINE_AA)
    return f

def put_quad(img, tex, quad, alpha=1.0):
    """warp texture onto a screen quad (tl, tr, br, bl)"""
    h, w = tex.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]]); dst = np.float32(quad)
    M = cv2.getPerspectiveTransform(src, dst)
    x0, y0 = np.floor(dst.min(0)).astype(int); x1, y1 = np.ceil(dst.max(0)).astype(int)
    x0, y0 = max(0, x0 - 2), max(0, y0 - 2); x1, y1 = min(W, x1 + 2), min(H, y1 + 2)
    if x1 <= x0 or y1 <= y0: return img
    T = np.float32([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ M
    wt = cv2.warpPerspective(tex, T, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)
    ma = cv2.warpPerspective(np.ones((h, w), np.float32), T, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)[..., None] * alpha
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - ma) + wt * ma
    return img

def card(img, c, w, h, face, flip=0.0, lean=0.0, light=1.0, back=None):
    """a card standing at screen centre c, size w x h. flip 0 = back towards us, 1 = face towards us"""
    sx = math.cos(math.pi * (1 - flip)); showing_face = sx > 0; sx = abs(sx)
    if sx < 0.02: return img
    tex = face if showing_face else (back if back is not None else card_back(int(w), int(h)))
    hw, hh = w / 2 * sx, h / 2
    persp = (1 - sx) * 0.08 * h
    quad = [(c[0] - hw, c[1] - hh + persp), (c[0] + hw, c[1] - hh - persp * 0), (c[0] + hw, c[1] + hh), (c[0] - hw, c[1] + hh - persp * 0)]
    return put_quad(img, np.clip(tex * light, 0, 1), quad)

# ---------------- text, cursor ----------------
from PIL import Image, ImageDraw, ImageFont
FONTS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "fonts")
_ft = {}
def text(img, s, center, size, font="CormorantSC-Medium.ttf", col=(0.92, 0.93, 0.95), alpha=1.0, track=0.0):
    if alpha <= 0: return img
    k = (font, size)
    if k not in _ft: _ft[k] = ImageFont.truetype(os.path.join(FONTS, font), size)
    f = _ft[k]
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    if track:
        widths = [d.textlength(ch, font=f) + track for ch in s]; tw = sum(widths) - track
        x = center[0] - tw / 2
        for ch, wd in zip(s, widths):
            d.text((x, center[1]), ch, font=f, fill=255, anchor="lm"); x += wd
        text.right = x - track
    else:
        d.text(center, s, font=f, fill=255, anchor="mm"); text.right = center[0] + d.textlength(s, font=f) / 2
    a = np.asarray(lay, np.float32)[..., None] / 255 * alpha
    return img * (1 - a) + np.array(col, np.float32) * a

def cursor(img, x, y, h, on, col=(0.92, 0.93, 0.95), w=None):
    if on <= 0: return img
    w = w or max(3, int(h * 0.07))
    x0, y0 = int(x), int(y - h / 2)
    img[y0:y0 + int(h), x0:x0 + w] = img[y0:y0 + int(h), x0:x0 + w] * (1 - on) + np.array(col, np.float32) * on
    return halo(img, (x0 + w / 2, y), h * 0.35, 0.05 * on, np.array(col, np.float32), fall=1.0)

_V = None; _GR = []
def finish_fast(img, grain=0.022, vign=0.22, hal=0.18, seed=0):
    """same look as wkit.finish (halation, vignette, film grain), ~6x faster: halation blurred at 1/4 size,
    grain drawn from a bank of 24 pre-made fields (rolled by the seed so it never repeats visibly)"""
    global _V
    br = np.clip(img - 0.55, 0, None)
    sm = cv2.resize(br, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), 4.5)
    img = img + hal * cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR) * np.array([0.9, 0.95, 1.1], np.float32)
    if _V is None or _V[0] != vign:
        v = 1 - vign * (((XS - W / 2) / (W / 2)) ** 2 + ((YS - H / 2) / (H / 2)) ** 2) ** 1.2
        _V = (vign, v[..., None].astype(np.float32))
    img = img * _V[1]
    if not _GR:
        rng = np.random.default_rng(1234)
        for i in range(8):
            g = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.75)
            c = cv2.GaussianBlur(rng.normal(0, 1, (H, W, 3)).astype(np.float32), (0, 0), 1.2) * 0.25
            _GR.append((g[..., None] + c).astype(np.float16))
    rs = np.random.default_rng(seed); gi = int(rs.integers(8)); dx, dy = int(rs.integers(W)), int(rs.integers(H))
    gr = np.roll(np.roll(_GR[gi], dy, 0), dx, 1).astype(np.float32)
    lum = np.clip(img.mean(2, keepdims=True), 0, 1)
    img = img + gr * grain * (0.5 + 1.2 * np.sqrt(lum) * (1 - lum) * 2)
    return np.clip(img, 0, 1)
K.finish = finish_fast

def finish(img, t):
    return finish_fast(img, grain=0.026, vign=0.26, hal=0.20, seed=int(t * 1000) % 100000)
