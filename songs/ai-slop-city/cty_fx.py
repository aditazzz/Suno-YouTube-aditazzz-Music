"""In-world effects: assistant chat bubbles rising from her phone like lanterns, notebook pages, ghost pedestrians,
the LED band text, slop pictures inside close windows."""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from cty_eng import F32, AA, hexc, mix, clamp, sstep, to_8
import cty_city as CC

import os
from studio.core import FONTS
FONT_DIR = os.path.join(FONTS, '')
_BUB = {}


def bubble_sprite(text, px_h, style='ai'):
    """RGBA sprite of a chat bubble: rounded, soft, with a little tail. px_h = text cap height in pixels."""
    key = (text, int(px_h), style)
    if key in _BUB: return _BUB[key]
    s = max(8, int(px_h))
    f = ImageFont.truetype(FONT_DIR + 'Inter-Medium.otf', s)
    tw = f.getlength(text)
    padx, pady = s * 0.9, s * 0.62
    w = int(tw + padx * 2); h = int(s * 1.25 + pady * 2)
    tail = int(s * 0.6)
    W, H = w + 8, h + tail + 8
    im = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fill = (244, 244, 248, 255) if style == 'ai' else (58, 108, 255, 255)
    d.rounded_rectangle([8, 8, w * 2, h * 2], radius=int(h), fill=fill)
    if style == 'ai':
        d.polygon([(int(w * 0.18 * 2), h * 2 - 4), (int(w * 0.12 * 2), (h + tail) * 2), (int(w * 0.3 * 2), h * 2 - 4)], fill=fill)
    else:
        d.polygon([(int(w * 0.82 * 2), h * 2 - 4), (int(w * 0.88 * 2), (h + tail) * 2), (int(w * 0.7 * 2), h * 2 - 4)], fill=fill)
    im = im.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.text((4 + padx, 4 + pady - s * 0.05), text, font=f, fill=(22, 22, 28, 255) if style == 'ai' else (255, 255, 255, 255))
    a = np.asarray(im, F32) / 255
    _BUB[key] = a
    return a


def composite_rgba(img, spr, x, y, alpha=1.0, glow_layer=None, glow_k=0.0):
    """Premultiply-free RGBA over float RGB at top-left (x, y)."""
    H, W = img.shape[:2]
    h, w = spr.shape[:2]
    x, y = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if X1 <= X0 or Y1 <= Y0: return
    s = spr[Y0 - y:Y1 - y, X0 - x:X1 - x]
    a = s[..., 3:4] * alpha
    img[Y0:Y1, X0:X1] = img[Y0:Y1, X0:X1] * (1 - a) + s[..., :3] * a
    if glow_layer is not None and glow_k > 0:
        glow_layer[Y0:Y1, X0:X1] = np.maximum(glow_layer[Y0:Y1, X0:X1], s[..., :3] * a * glow_k)


def bubbles(img, cam, t, items, origin, glow_k=0.35):
    """items: [(text, t0, t1, style, drift)]. Each bubble pops out of the phone at t0, floats up toward the tower,
    and fades by t1. origin: world position of her phone."""
    glow_layer = np.zeros_like(img)
    order = []
    for (text, t0, t1, style, drift) in items:
        if not (t0 - 0.05 <= t <= t1 + 0.6): continue
        u = t - t0
        rise = 0.25 + 1.15 * (1 - math.exp(-u * 0.9)) + 0.22 * u
        P = np.asarray(origin, float) + np.array([0, rise, 0]) + np.asarray(drift, float) * u
        z = cam.to_cam(P[None])[0, 2]
        if z <= cam.near: continue
        order.append((z, text, t0, t1, style, P, u))
    for z, text, t0, t1, style, P, u in sorted(order, key=lambda o: -o[0]):
        pop = 1 - math.exp(-max(0.0, u) * 9)
        a = sstep(t0 - 0.05, t0 + 0.12, t) * (1 - sstep(t1, t1 + 0.6, t))
        if a <= 0.01: continue
        ppm = cam.px_per_m(P)
        cap = max(0.034 * cam.H, 0.16 * ppm) * (0.6 + 0.4 * pop)
        spr = bubble_sprite(text, cap, style)
        sp = cam.proj(P[None])[0][0]
        x = sp[0] - spr.shape[1] * (0.2 if style == 'ai' else 0.8)
        x = min(max(x, cam.W * 0.04), cam.W * 0.96 - spr.shape[1])         # keep the whole bubble on screen
        y = max(sp[1] - spr.shape[0], cam.H * 0.06)
        composite_rgba(img, spr, x, y, a, glow_layer, glow_k)
    if glow_k > 0:
        g = cv2.GaussianBlur(cv2.resize(glow_layer, (img.shape[1] // 4, img.shape[0] // 4), interpolation=cv2.INTER_AREA), (0, 0), 6)
        img += cv2.resize(g, (img.shape[1], img.shape[0])) * 0.9
    return img


# ------------------------------------------------------------------ LED band text on the Feed Tower
_LED = {}


def led_text_strip(text, h_px, col):
    key = (text, int(h_px), tuple(np.round(col, 3)))
    if key in _LED: return _LED[key]
    f = ImageFont.truetype(FONT_DIR + 'InterDisplay-Bold.otf', max(6, int(h_px * 0.62)))
    w = int(f.getlength(text)) + int(h_px)
    im = Image.new('L', (w, int(h_px)), 0)
    ImageDraw.Draw(im).text((int(h_px * 0.4), int(h_px * 0.12)), text, font=f, fill=255)
    a = np.asarray(im, F32) / 255
    # LED dot matrix look
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    pitch = max(2, int(h_px / 14))
    dots = ((yy % pitch) < pitch * 0.75) & ((xx % pitch) < pitch * 0.75)
    a = a * (0.55 + 0.45 * dots)
    _LED[key] = a
    return a


def led_band(img, ctx, S, text, col, scroll_mps=6.0, t=0.0, k=1.0, glow_layer=None):
    """Scrolling text on the LED band wrapping the Feed Tower's two hero faces. The band is 54 m around; text runs
    from the south face (left) round the corner onto the east face."""
    if k <= 0.01 or '_led_band' not in S: return
    cam = ctx.cam
    res = 40.0                                  # px per metre of band
    band_h = 1.5
    hpx = int(band_h * res)
    strip = led_text_strip(text, hpx, col)
    total = 54.0
    tex = np.zeros((hpx, int(total * res)), F32)
    off = int((t * scroll_mps * res) % strip.shape[1])
    reps = int(math.ceil(tex.shape[1] / strip.shape[1])) + 2
    long = np.tile(strip, (1, reps))
    tex[:] = long[:, off:off + tex.shape[1]]
    for nm, a0 in (('W', 0.0), ('S', 27.0)):
        if nm not in S['_led_band']: continue
        band, sp = S['_led_band'][nm]
        part = tex[:, int(a0 * res):int((a0 + 27.0) * res)]
        hp, wp = part.shape
        src = np.float32([[0, hp], [wp, hp], [wp, 0], [0, 0]])
        Hm = cv2.getPerspectiveTransform(src, np.float32(sp))
        x0, y0 = max(0, int(sp[:, 0].min()) - 1), max(0, int(sp[:, 1].min()) - 1)
        x1, y1 = min(cam.W, int(sp[:, 0].max()) + 2), min(cam.H, int(sp[:, 1].max()) + 2)
        if x1 <= x0 or y1 <= y0: continue
        Hr = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ Hm
        w = cv2.warpPerspective(part, Hr, (x1 - x0, y1 - y0), flags=cv2.INTER_AREA)
        m = (ctx.idb[y0:y1, x0:x1] == CC.LEDB).astype(F32)
        a = (w * m * k)[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a * 0.85) + np.asarray(col, F32) * a
        if glow_layer is not None:
            glow_layer[y0:y1, x0:x1] += np.asarray(col, F32) * a * 0.6


# ------------------------------------------------------------------ slop pictures inside close windows
def window_pictures(img, ctx, S, pick, k=1.0, min_px=26):
    """Warp the actual slop pictures into the Feed Tower's screen windows when they are big enough on screen."""
    import cty_slop as SL
    scr = S.get('_t1_screens')
    if not scr: return
    for nm, (idx, Sq) in scr.items():
        for i in idx:
            q = Sq[i]
            w = np.linalg.norm(q[1] - q[0])
            if w < min_px: continue
            kind = pick(nm, i)
            im = SL.image(kind, 128 if w < 120 else 256)
            sub = CC.subquad(q, 0.06, 0.94, 0.1, 0.92)
            hh, ww = im.shape[:2]
            src = np.float32([[0, hh], [ww, hh], [ww, 0], [0, 0]])
            Hm = cv2.getPerspectiveTransform(src, np.float32(sub))
            x0, y0 = max(0, int(sub[:, 0].min()) - 1), max(0, int(sub[:, 1].min()) - 1)
            x1, y1 = min(ctx.cam.W, int(sub[:, 0].max()) + 2), min(ctx.cam.H, int(sub[:, 1].max()) + 2)
            if x1 <= x0 or y1 <= y0: continue
            Hr = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ Hm
            wimg = cv2.warpPerspective(im, Hr, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)
            m = cv2.warpPerspective(np.ones((hh, ww), F32), Hr, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)[..., None] * k
            img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + wimg * 1.1 * m


# ------------------------------------------------------------------ ghost pedestrians (time-lapse)
def ghosts(img, cam, t, n=10, seed=3, k=1.0, col=None):
    """Passers-by streak across the plaza during the time-lapse: translucent, motion-blurred, every one on a phone."""
    if k <= 0.01: return img
    rng = np.random.default_rng(seed)
    lay = np.zeros(img.shape[:2], F32)
    for i in range(n):
        speed = rng.uniform(0.6, 1.6); ph = rng.uniform(0, 1)
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(4, 18)
        along = ((t * speed * 0.35 + ph) % 1.0) * 2 - 1
        c = np.array([CC.fs(10 + rng.uniform(-6, 14), 0)[0], 0, CC.fs(10, 0)[1]])
        d = np.array([math.cos(a), 0, math.sin(a)])
        base = np.array([rng.uniform(-8, 28), 0.0, rng.uniform(-6, 26)])
        P0 = base + d * along * 18
        P1 = P0 + d * 2.2
        pts = []
        for P in (P0, P1):
            for y in (0.0, 1.7):
                pts.append(P + np.array([0, y, 0]))
        S, z = cam.proj(np.array(pts))
        if (z <= cam.near).any(): continue
        poly = np.array([S[0], S[2], S[3], S[1]])
        m = np.zeros(img.shape[:2], np.uint8)
        cv2.fillPoly(m, [np.round(cv2.convexHull(poly.astype(np.float32)).reshape(-1, 2) * 16).astype(np.int32)], 255, AA, shift=4)
        lay = np.maximum(lay, m.astype(F32) / 255 * rng.uniform(0.25, 0.45))
    lay = cv2.GaussianBlur(lay, (0, 0), 3)[..., None] * k
    tint = np.array([0.18, 0.16, 0.24], F32) if col is None else np.asarray(col, F32)
    return img * (1 - lay) + tint * lay


# ------------------------------------------------------------------ her notebook's pages, flying into the shadow
def page_paths(n, seed, origin, targets):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        T = targets[i % len(targets)]
        out.append(dict(delay=rng.uniform(0, 3.2), dur=rng.uniform(2.4, 3.6), spin=rng.uniform(2.0, 5.0) * rng.choice([-1, 1]),
                        tilt=rng.uniform(0, 6.28), wob=rng.uniform(0.5, 1.4), side=rng.uniform(-1, 1), target=np.asarray(T, float),
                        origin=np.asarray(origin, float) + np.array([rng.uniform(-0.05, 0.05), 0.02, rng.uniform(-0.05, 0.05)])))
    return out


def pages(img, cam, t, t0, paths, ink=(0.35, 0.33, 0.4)):
    """Cream pages lift off the notebook, tumble up and away into the Feed Tower. Returns indices of pages that arrived."""
    arrived = []
    items = []
    for i, P in enumerate(paths):
        u = (t - t0 - P['delay']) / P['dur']
        if u < 0: continue
        if u >= 1: arrived.append(i); continue
        k = u * u * (3 - 2 * u)
        o, T = P['origin'], P['target']
        mid = (o + T) / 2 + np.array([P['side'] * 9.0, 6.0, -P['side'] * 5.0])
        pos = (1 - k) ** 2 * o + 2 * (1 - k) * k * mid + k * k * T          # quadratic bezier
        pos = pos + np.array([math.sin(t * P['wob'] * 3) * 0.3, 0, math.cos(t * P['wob'] * 2.4) * 0.3]) * (1 - k) * min(1, u * 4)
        ang = P['tilt'] + (t - t0) * P['spin']
        sz = 1.0 + 1.6 * min(1.0, u * 3)
        a = np.array([math.cos(ang), 0.35 * math.sin(ang * 0.7), math.sin(ang)]) * 0.105 * sz
        b = np.array([-math.sin(ang) * 0.3, 0.95, math.cos(ang) * 0.3])
        b = b / np.linalg.norm(b) * 0.148 * sz
        q = np.array([pos - a - b, pos + a - b, pos + a + b, pos - a + b])
        S, z = cam.proj(q)
        if (z <= cam.near).any(): continue
        items.append((float(z.mean()), S, u))
    for z, S, u in sorted(items, key=lambda x: -x[0]):
        fade = 1 - max(0.0, (u - 0.85) / 0.15)
        H, W = img.shape[:2]
        x0, y0 = max(0, int(S[:, 0].min()) - 2), max(0, int(S[:, 1].min()) - 2)
        x1, y1 = min(W, int(S[:, 0].max()) + 3), min(H, int(S[:, 1].max()) + 3)
        if x1 <= x0 or y1 <= y0: continue
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(m, [np.round((S - [x0, y0]) * 16).astype(np.int32)], 255, AA, shift=4)
        mf = (m.astype(F32) / 255 * fade)[..., None]
        reg = img[y0:y1, x0:x1]
        reg[:] = reg * (1 - mf) + hexc('f6f0e2') * mf
        w = np.linalg.norm(S[1] - S[0])
        if w > 10:
            for k in range(4):
                l0 = CC._lerp4(S, 0.15, 0.25 + k * 0.17); l1 = CC._lerp4(S, 0.6 + 0.25 * ((k * 3) % 4) / 4, 0.25 + k * 0.17)
                cv2.line(reg, (int((l0[0] - x0) * 16), int((l0[1] - y0) * 16)), (int((l1[0] - x0) * 16), int((l1[1] - y0) * 16)),
                         tuple(float(c) * 0.9 for c in ink), 1, AA, shift=4)
        e = np.zeros_like(m)
        cv2.polylines(e, [np.round((S - [x0, y0]) * 16).astype(np.int32)], True, 255, 1, AA, shift=4)
        ef = (e.astype(F32) / 255 * fade * 0.8)[..., None]
        reg[:] = reg * (1 - ef) + hexc('2a2430') * ef
    return arrived


def gold_stream(img, cam, t, t0, src_px, targets, n=260, seed=8, k=1.0):
    """Golden motes pulled out of the sunset and into the shadow on the tower."""
    if k <= 0.01: return img
    rng = np.random.default_rng(seed)
    H, W = img.shape[:2]
    lay = np.zeros((H, W), F32)
    tg = cam.proj(np.asarray(targets, float))[0]
    for i in range(n):
        d = rng.uniform(0, 2.6); spd = rng.uniform(0.35, 0.6)
        u = (t - t0 - d) * spd
        if not 0 < u < 1: continue
        T = tg[i % len(tg)]
        s0 = np.array(src_px) + rng.normal(0, 60, 2)
        mid = (s0 + T) / 2 + np.array([rng.uniform(-200, 200), rng.uniform(-260, -60)])
        kk = u * u * (3 - 2 * u)
        p = (1 - kk) ** 2 * s0 + 2 * (1 - kk) * kk * mid + kk * kk * T
        p2 = (1 - (kk - 0.04)) ** 2 * s0 + 2 * (1 - (kk - 0.04)) * (kk - 0.04) * mid + (kk - 0.04) ** 2 * T
        if not (0 <= p[0] < W and 0 <= p[1] < H): continue
        a = math.sin(math.pi * u)
        cv2.line(lay, (int(p2[0]), int(p2[1])), (int(p[0]), int(p[1])), float(a * rng.uniform(0.5, 1.0)), 2, AA)
        cv2.circle(lay, (int(p[0]), int(p[1])), 2, float(a), -1, AA)
    g = cv2.GaussianBlur(lay, (0, 0), 1.2) + cv2.GaussianBlur(lay, (0, 0), 6) * 1.5
    return img + g[..., None] * hexc('ffc35a') * k
