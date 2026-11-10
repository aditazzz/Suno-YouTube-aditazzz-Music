"""Ground v2 composite (CPU, linear light): Poly Haven rogland_clear_night sky (CC0) through the canopy gap + the Blender
passes from ground2.py (beauty on alpha, emitters only, depth, soft foreground layer) + mist sheets placed by DEPTH (each
sheet only veils what is behind it, and carries the light of the emitters near it) + motes with depth-of-field bokeh
(3D points, hidden behind nearer leaves) + bloom from the emitters-only pass + grade.
comp2.py <passes.npz> <out.png> [t_seconds]      (import comp2; comp2.frame(d, t) for the motion test)"""
import sys, os, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, minimum_filter, zoom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sky2
LENS, SENSOR, PITCH, CAMH, FOCUS = 24.0, 36.0, 9.0, 0.24, 1.12
PUSH = 0.0      # camera push-in, metres per second (set by motion2.py)
GRAIN = 0.010
_sky = {}
HAZE = np.array([0.006, 0.030, 0.055], np.float32)


def blur(img, s):
    """gaussian, done small when the radius is large"""
    if s < 6: return gaussian_filter(img, (s, s, 0) if img.ndim == 3 else s)
    k = int(min(8, max(2, s // 3))); h, w = img.shape[:2]
    sm = img[:h - h % k, :w - w % k]
    sm = sm.reshape(h // k, k, w // k, k, -1).mean((1, 3)) if img.ndim == 3 else sm.reshape(h // k, k, w // k, k).mean((1, 3))
    sm = gaussian_filter(sm, (s / k, s / k, 0) if img.ndim == 3 else s / k)
    im = Image.fromarray
    if img.ndim == 3:
        return np.stack([np.asarray(im(sm[..., c]).resize((w, h), Image.BICUBIC)) for c in range(sm.shape[-1])], -1)
    return np.asarray(im(sm).resize((w, h), Image.BICUBIC))


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


_cache = {}
def noise_tile(H, W, seed, sy, sx):
    key = (H, W, seed, sy, sx)
    if key not in _cache:
        r = np.random.default_rng(seed); acc = np.zeros((H, W * 2), np.float32)
        for o, amp in ((1, 1.0), (2, 0.5), (4, 0.25)):
            n = r.random((H // 4, W // 2)).astype(np.float32)
            n = gaussian_filter(n, (sy / o / 4, sx / o / 4), mode='wrap')
            acc += np.asarray(Image.fromarray(n).resize((W * 2, H), Image.BICUBIC)) * amp / n.std() * 0.1
        acc = (acc - acc.mean()) / acc.std()
        _cache[key] = np.clip(0.5 + acc * 0.28, 0, 1)
    return _cache[key]


def slide(tile, W, px):
    px = px % (tile.shape[1]); i = int(px); f = px - i
    a = np.roll(tile, -i, 1)[:, :W]; b = np.roll(tile, -i - 1, 1)[:, :W]
    return a * (1 - f) + b * f


def sky_plate(H, W, s, clear, t):
    if (H, W) in _sky:
        col0, stars, xs, ys, X, Y, mx0, my0 = _sky[(H, W)]
        return _sky_t(col0, stars, xs, ys, X, Y, mx0, my0, s, t)
    sk, el = sky2.view('rogland_clear_night', W, H, yaw_deg=14, pitch_deg=PITCH + 14, lens_mm=LENS)   # tipped up: the Milky Way band fills the gap
    lin = np.clip(sk, 0, 1) ** 2.0
    den = gaussian_filter(lin, (0.7 * s, 0.7 * s, 0))
    loc = gaussian_filter(lin, (5 * s, 5 * s, 0))
    stars = np.clip(den - loc * 1.45 - 0.045, 0, None) ** 1.2       # relative to the local sky: the plate's bright clouds are jpeg-noisy
    # the plate's few very bright stars carry a halo of jpeg speckle (reads as puff-balls): thin out any dense knot of "stars"
    dens = gaussian_filter((stars.mean(-1) > 0.02).astype(np.float32), 9 * s)
    stars = np.minimum(stars, 0.20) * (1 - sstep(dens, 0.10, 0.22))[..., None]
    g = gaussian_filter(lin, (3 * s, 3 * s, 0)).mean(-1, keepdims=True)
    g = np.minimum(g, gaussian_filter(g, (30 * s, 30 * s, 0)) * 1.25 + 0.01)
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; xs = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    col = g * (np.array([0.09, 0.30, 0.95], np.float32) * (1 - ys) + np.array([0.04, 0.55, 0.75], np.float32) * ys) * 1.5
    col += g ** 1.5 * np.array([0.50, 0.18, 0.95], np.float32) * 1.1 * np.clip(1.2 - xs * 1.4, 0, 1)
    col += np.array([0.004, 0.010, 0.028], np.float32)
    # him: ONE tiny hard warm-white star, where the gap is clearest (it drifts a few pixels; stars do not)
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    want = clear * np.exp(-(((X / W - 0.27) / 0.10) ** 2 + ((Y / H - 0.15) / 0.10) ** 2))
    my, mx = np.unravel_index(np.argmax(want), want.shape)
    _sky[(H, W)] = (col, stars, xs, ys, X, Y, float(mx), float(my))
    return _sky_t(col, stars, xs, ys, X, Y, float(mx), float(my), s, t)


def _sky_t(col0, stars, xs, ys, X, Y, mx, my, s, t):
    tw = 1.0 + 0.10 * np.sin(t * 5.0 + xs * 900 + ys * 700)
    col = col0 + stars * np.array([0.85, 0.95, 1.0], np.float32) * 5.5 * tw
    mx = mx + t * 5.0 * s; my = my - t * 1.4 * s
    col += (np.exp(-((X - mx) ** 2 + (Y - my) ** 2) / (2 * (1.5 * s) ** 2)) * 9.0)[..., None] * np.array([1.0, 0.92, 0.78], np.float32)
    return col, (mx, my)


def frame(d, t=0.0, pulse=True, stats=False):
    main = d['rgba_main'].astype(np.float32); emit = d['emit_main'].astype(np.float32); z = d['z_main'].astype(np.float32)
    fg = d['rgba_fg'].astype(np.float32) if 'rgba_fg' in d else None
    H, W = z.shape; s = W / 1920; fpx = W * LENS / SENSOR
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    hz = H / 2 + np.tan(np.radians(PITCH)) * fpx
    a = main[..., 3:4]; rgb = main[..., :3].copy()
    zs = np.where(z > 1e3, 60.0, z)
    # the veins breathe: a slow wave of light travelling away from the camera through the emitters
    if pulse:
        wave = 0.5 + 0.5 * np.sin(2 * np.pi * (t / 3.2 - zs / 5.0))
        gainp = (0.16 * wave - 0.04)[..., None]
        rgb += emit * gainp; emit = emit * (1 + gainp)
    # --- sky through the gap, and a far glow where the jungle would close the horizon
    clear = minimum_filter((1 - a[..., 0]) * (1 - (fg[..., 3] if fg is not None else 0)), int(30 * s))
    sky, him = sky_plate(H, W, s, clear, t)
    eb1 = blur(emit, 28 * s); eb2 = blur(emit, 110 * s)
    low = sstep(Y, hz - 330 * s, hz - 40 * s)[..., None]
    far_glow = HAZE * 1.6 + eb2 * 1.6 + np.array([0.0, 0.085, 0.11], np.float32) * np.exp(-((X - W * 0.40) / (W * 0.20)) ** 2)[..., None]
    bg = sky * (1 - low) + far_glow * low
    img = bg * (1 - a) + rgb
    # --- aerial haze by depth, then mist sheets at set depths; each veils only what lies behind it
    hf = (1 - np.exp(-np.clip(zs - 1.6, 0, None) * 0.075))[..., None] * a
    img = img * (1 - hf * 0.75) + (HAZE * 1.2 + eb2 * 1.2) * hf * 0.75
    for i, (D, amt, hs) in enumerate(((21.0, 0.85, 3.2), (13.0, 0.80, 1.9), (10.0, 0.50, 1.6), (8.0, 0.68, 1.3), (5.0, 0.56, 0.9), (3.2, 0.38, 0.6), (2.0, 0.24, 0.36))):
        h = CAMH - (Y - hz) * D / fpx                                   # world height of this row on the sheet
        dens = np.exp(-np.clip(h, 0, None) / hs) * (h > -0.05)
        n = slide(noise_tile(H, W, 40 + i, 6 * s * 6 / D + 3, 44 * s * 6 / D + 10), W, t * (9 + 3 * i) * s * 6 / D + i * 300)
        vis = sstep(zs, D * 0.9, D * 1.25)
        al = (amt * dens * np.clip(0.05 + 1.5 * n ** 1.5, 0, 1.4) * vis)[..., None]
        al = np.clip(al, 0, 0.92)
        img = img * (1 - al) + (HAZE * (1.9 - 0.14 * i) + eb1 * 0.9 + eb2 * 1.5) * al
    # --- motes: 3D points with bokeh by distance from the focus plane, hidden behind nearer leaves
    r = np.random.default_rng(7); NM = 300
    mz = 0.55 + 9.0 * r.random(NM) ** 1.7
    mxw = (r.random(NM) - 0.5) * 2 * (0.78 * mz); mh = 0.03 + 1.6 * r.random(NM) ** 1.3 * (0.4 + mz / 4)
    ph = r.random(NM) * 6.283; spd = 0.5 + r.random(NM); hue = r.random(NM); amp = r.uniform(0.35, 1.0, NM)
    mxw = mxw + 0.05 * np.sin(t * 0.9 * spd + ph) + 0.022 * t * (spd - 0.9); mh = mh + 0.028 * t * spd + 0.03 * np.sin(t * 1.3 * spd + ph * 2)
    mz = mz - PUSH * t                                                   # the push-in
    motes = np.zeros((H, W, 3), np.float32)
    for j in range(NM):
        px = W / 2 + mxw[j] / mz[j] * fpx; py = hz - (mh[j] - CAMH) / mz[j] * fpx
        if not (4 < px < W - 4 and 4 < py < H - 4): continue
        if zs[int(py), int(px)] < mz[j] - 0.05: continue
        rad = max(1.15 * s, 12.7 * s * abs(mz[j] - FOCUS) / mz[j])
        c = np.array([0.10, 0.85, 1.0]) if hue[j] < 0.5 else (np.array([0.05, 0.95, 0.70]) if hue[j] < 0.78 else np.array([0.62, 0.32, 1.0]))
        tw = 0.75 + 0.25 * np.sin(t * 2.2 * spd[j] + ph[j])
        e = amp[j] * tw * (5.0 * s * s / (rad * rad) + 0.11) * min(1.0, 2.2 / mz[j] + 0.35)
        R = int(rad + 3); x0, x1 = max(0, int(px) - R), min(W, int(px) + R + 1); y0, y1 = max(0, int(py) - R), min(H, int(py) + R + 1)
        dd = np.hypot(X[y0:y1, x0:x1] - px, Y[y0:y1, x0:x1] - py)
        disc = np.clip((rad - dd) / max(1.0, rad * 0.18), 0, 1) * (0.72 + 0.28 * np.clip(dd / rad, 0, 1) ** 2) if rad > 2.5 * s else np.exp(-(dd / rad) ** 2)
        motes[y0:y1, x0:x1] += disc[..., None] * c * e
    if fg is not None:
        fa = fg[..., 3:4]
        img = (img + motes * 0.8) * (1 - fa) + fg[..., :3] + motes * 0.2
    else:
        img = img + motes
    # --- bloom: only from things that emit (the emitters pass, the motes, the stars)
    src = emit * 0.55 + motes * 0.5 + np.clip(bg * (1 - a) - 0.5, 0, None)
    img = img + blur(src, 4 * s) * 0.30 + blur(src, 16 * s) * 0.22 + blur(src, 60 * s) * 0.16
    # --- grade: filmic shoulder (nothing clips), blue floor (a place, not a void), vignette, grain
    x = np.clip(img * 0.90, 0, None) + np.array([0.0030, 0.0055, 0.0120], np.float32)
    out = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14) * 0.955
    out = np.clip(out, 0, 1) ** (1 / 2.2)
    out = out ** 1.26
    r2 = ((X / W - 0.5) ** 2 + (Y / H - 0.5) ** 2) * 2
    out = out * (1 - 0.34 * r2)[..., None]
    out = out + (np.random.default_rng(int(t * 24) + 3).random((H, W, 1)).astype(np.float32) - 0.5) * GRAIN
    out8 = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    if stats:
        mx = out8.max(-1); print('blown(>=250) %.3f%%  black(<=4 all ch) %.2f%%  mean %.1f  him at %s' % ((mx >= 250).mean() * 100, (mx <= 4).mean() * 100, out8.mean(), (int(him[0]), int(him[1]))))
    return out8


if __name__ == '__main__':
    d = dict(np.load(sys.argv[1])); t = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    o = frame(d, t, stats=True)
    Image.fromarray(o).save(sys.argv[2])
    im = Image.fromarray(o); im.thumbnail((960, 540), Image.LANCZOS); im.save(sys.argv[2].rsplit('.', 1)[0] + '_960.jpg', quality=88)
    print('wrote', sys.argv[2], o.shape)
