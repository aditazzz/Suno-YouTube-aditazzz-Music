"""The Promptress, proof of concept (song 4.44-19.02 s): the real moon -> push in -> through its surface into her
world -> she calls the moon to her fingers -> on the drop, snap back out: the whole scene is inside the real moon.

One continuous camera: the disc (the plate's moon) has radius r px at screen C; her world lives in disc units (R=1),
so it stays glued to the real moon while it is a moon, and fills the frame once we're through.
usage: python3 poc/portal.py <out_dir> [first last] [--w 1920 --h 1080] [--still t1,t2,...]"""
import os, sys, json, math, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from witch import pose, raster, overlaps, ease

ARGS = sys.argv[1:]
def opt(k, d):
    return type(d)(ARGS[ARGS.index(k) + 1]) if k in ARGS else d
W, H = opt("--w", 1920), opt("--h", 1080)
FPS = 30.0; T0, T1 = 4.44, 19.02
B = "build/poc"; NF = int(round((T1 - T0) * FPS))
HD = 0.5 * math.hypot(W, H)                     # half-diagonal: the disc covers the frame when r > HD
RM = 72.0                                       # the plate moon's radius in plate px (fitEllipse, 7.5-18.5 s)
PFPS = 29.97; PT0 = 7.5

# ---------------- plate + moon track ----------------
TR = json.load(open(f"{B}/track.json"))
cx = np.array([t["cx"] for t in TR]); cy = np.array([t["cy"] for t in TR])
good = np.arange(len(TR)) >= int((10.2 - PT0) * PFPS)      # before 10.2 s the phone was still exposing
cx[~good] = cx[good][0]; cy[~good] = cy[good][0]
def gsmooth(x, s):
    k = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); k /= k.sum()
    return np.convolve(np.pad(x, 3 * s, mode="edge"), k, mode="valid")
sx, sy = gsmooth(cx, 24), gsmooth(cy, 24)
cx, cy = gsmooth(cx, 2), gsmooth(cy, 2)       # the fit is a few px noisy frame to frame
_pc = {}
def plate(i):
    i = int(np.clip(i, 0, len(TR) - 1))
    if i not in _pc:
        if len(_pc) > 6: _pc.pop(next(iter(_pc)))
        _pc[i] = cv2.imread(f"{B}/plate/{TR[i]['f']}").astype(np.float32)
    return _pc[i]
def plate_time(t):
    """song time -> plate time: the push plays 10.3-18.0 (slowed to 0.82 so it covers the hold and push); the
    pull-back lands on 10.4 s onwards (it's unseen in between)"""
    return 10.3 + (t - T0) * 0.82 if t < 15.0 else 10.4 + (t - 16.95)
# the moon's own colour, so her sky glows like the real moon
_m = plate(int((12 - PT0) * PFPS)); _c = (int(sy[135]), int(sx[135]))
MOONCOL = np.median(_m[_c[0] - 30:_c[0] + 30, _c[1] - 25:_c[1] + 25].reshape(-1, 3), 0)

# ---------------- timing (song seconds) ----------------
def eio(u): u = min(max(u, 0), 1); return u * u * (3 - 2 * u)
def ein2(u): u = min(max(u, 0), 1); return u * u
def eout2(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 2
def eout4(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 4
def lin(u): return min(max(u, 0), 1)
def keys(t, ks, log=False):
    """ks: [(t, value, ease_into_this_key)]"""
    if t <= ks[0][0]: return np.asarray(ks[0][1], float)
    for (ta, va, _), (tb, vb, e) in zip(ks, ks[1:]):
        if t <= tb:
            u = e((t - ta) / (tb - ta)); va, vb = np.asarray(va, float), np.asarray(vb, float)
            return np.exp(np.log(va) + (np.log(vb) - np.log(va)) * u) if log else va + (vb - va) * u
    return np.asarray(ks[-1][1], float)

T_PUSH, T_PASS, T_DROP, T_LAND = 8.64, 13.92, 16.95, 18.15
R_HOLD = RM * 2.0
# log-zoom with matched velocity at the pass-through (ease-in quad into it, ease-out quad after)
R_KEYS = [(T0, R_HOLD, lin), (T_PUSH, R_HOLD * 1.07, lin), (T_PASS, HD * 1.1, ein2), (T_DROP, 4600.0, eout2),
          (T_LAND, 250.0, eout4), (T1, 228.0, eio)]
# F: the point of her world held at screen point G
WX0, HY = -0.06, 0.12                      # her spot, and the horizon (R units)
F_IN = np.array([-0.035, 0.03])
F_KEYS = [(T0, (0, 0), lin), (10.6, (0, 0), lin), (T_DROP, F_IN, eio), (T_LAND, (0.0, 0.0), eout4)]
G_KEYS = [(T0, (0.5 * W, 0.44 * H), lin), (T_PUSH, (0.5 * W, 0.44 * H), lin), (T_PASS, (0.5 * W, 0.5 * H), eio),
          (T_DROP, (0.5 * W, 0.5 * H), lin), (T_LAND, (0.56 * W, 0.40 * H), eout4), (T1, (0.555 * W, 0.405 * H), eio)]

def camera(t):
    r = float(keys(t, R_KEYS, log=True)); F = keys(t, F_KEYS); G = keys(t, G_KEYS)
    # the inside of the moon gets a slow, breathing handheld drift (never seen from outside)
    inside = ease((r - 600) / 1500)
    G = G + inside * np.array([7 * math.sin(t * 0.7) + 3 * math.sin(t * 1.9), 5 * math.sin(t * 0.9 + 1)])
    C = G - r * F
    return r, C

def witch_state(t):
    """where she is and what she's doing"""
    walk_u = eio((t - 6.3) / 3.3)            # walks in across the moon's face on "Once upon a midnight query"
    x = -0.55 + (WX0 + 0.55) * walk_u
    walking = 1.0 if 6.3 < t < 9.6 else 0.0
    raise_u = eio((t - 14.25) / 1.45)        # "I asked the dark..." she lifts her hand
    look_u = eio((t - 14.0) / 1.3)
    pinch = eio((t - 16.55) / 0.4)
    bob = 0.006 * abs(math.sin(t * 7.0)) * walking
    return dict(x=x, y=HY - bob, raise_u=raise_u, look_u=look_u, walk=walking, pinch=pinch)

H_W = 0.16                                     # her height in R
MOON0 = np.array([0.105, -0.018]); MOON0_R = 0.019
def inner_moon(t, A, wx, wy):
    """the half-lit moon of her world: rises to her fingers (16.0 -> 16.95), lands on the drop"""
    hand = np.array([wx, wy]) + A["moon_c"] * H_W; hr = A["moon_r"] * H_W * 0.92
    u = eio((t - 15.55) / (T_DROP - 15.55))
    # an arc, not a straight line: up and over, like it's being reeled in
    p = MOON0 + (hand - MOON0) * u + np.array([0, -0.035]) * math.sin(math.pi * u)
    rad = MOON0_R + (hr - MOON0_R) * u
    return p, rad, u

# ---------------- textures ----------------
def fbm(n, beta, seed):
    rng = np.random.default_rng(seed); f = np.fft.rfftfreq(n)[None, :]; g = np.fft.fftfreq(n)[:, None]
    k = np.sqrt(f * f + g * g); k[0, 0] = 1
    spec = (rng.normal(size=(n, n // 2 + 1)) + 1j * rng.normal(size=(n, n // 2 + 1))) / k ** beta
    spec[0, 0] = 0; x = np.fft.irfft2(spec, s=(n, n)).astype(np.float32)
    return (x - x.mean()) / x.std()
NT = 1024
TEX = {}
def tex(name):
    if name not in TEX:
        p = f"{B}/tex_{name}.npy"
        if os.path.exists(p): TEX[name] = np.load(p)
        else:
            TEX[name] = {"wisp": lambda: fbm(NT, 1.6, 3), "ripple": lambda: fbm(NT, 1.2, 7), "mist": lambda: fbm(NT, 1.9, 11)}[name]()
            np.save(p, TEX[name])
    return TEX[name]
def sample(name, u, v):
    """sample a periodic texture at (u, v) in texture periods (any real numbers), bilinear"""
    T = tex(name); return cv2.remap(T, (u % 1 * NT).astype(np.float32), (v % 1 * NT).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

# her moon: the stacked IMG_1976 moon, cut out on its own disc
_ms = cv2.imread(f"{B}/moon_1976_stack.png", -1).astype(np.float32) / 65535
_g = cv2.GaussianBlur(_ms.mean(2), (0, 0), 3); _yy, _xx = np.nonzero(_g > 0.25)
MC = np.array([_xx.mean(), _yy.mean()]); MR = 0.5 * max(_xx.max() - _xx.min(), _yy.max() - _yy.min())
MOONTEX = _ms

# ---------------- the world inside the moon ----------------
HORIZ = np.array([0.60, 0.76, 0.88])                          # antique ivory, warm at the horizon
UPPER = np.array([0.255, 0.235, 0.235])                       # smoky grey with a breath of midnight blue, high up
def hills(x):
    return np.clip(0.0016 + 0.0016 * np.sin(5 * x + 1) + 0.0011 * np.sin(13 * x + 2) + 0.0006 * np.sin(37 * x + 0.3) + 0.0012 * np.sin(2.3 * x), 0.0003, None)
def sky(wx, wy, t, inside=1.0):
    d = np.clip(HY - wy, 0, None)
    k = np.clip(d / 0.55, 0, 1) ** 0.65
    up = HORIZ * 0.92 * (1 - inside) + UPPER * inside      # seen from outside, the whole disc glows like the moon
    c = HORIZ[None, None, :] * (1 - k[..., None]) + up[None, None, :] * k[..., None]
    c = c + np.array([0.035, 0.05, 0.07]) * np.exp(-d / 0.035)[..., None]           # warm band right on the horizon
    w = sample("wisp", wx * 0.45 + t * 0.004, wy * 3.2 + 0.31)
    band = np.exp(-((d - 0.09) / 0.07) ** 2)
    c = c * (1 - 0.13 * np.clip(w, -1.5, 2.5)[..., None] * band[..., None])
    return c
def world(wx, wy, t, ws, A, mp, mrad, inside=1.0):
    """colour of her world (0..1 BGR) at world coords. ws: witch state; mp/mrad: her moon"""
    below = wy > HY
    yy = np.where(below, 2 * HY - wy, wy)
    c = sky(wx, yy, t, inside)
    # far hills on the horizon, hazy
    hh = hills(wx); hill = (yy > HY - hh)
    c = np.where(hill[..., None], c * 0.80 + UPPER * 0.10, c)
    # the ground is a still, mirror-flat plain: the sky reflected, a little darker, with long slow ripples
    rip = sample("ripple", wx * 0.25 + t * 0.002, wy * 22.0)
    refl = c * (0.66 + 0.045 * rip[..., None] * np.clip((wy - HY) / 0.02, 0, 1)[..., None])
    c = np.where(below[..., None], refl, c)
    return c

def disc_mask(rho, r):
    soft = 1.2 + 2.0 * (r < 400)          # a softer limb while it's still a moon in the sky
    return np.clip((1 - rho) * r / soft + 0.5, 0, 1)

# ---------------- frame ----------------
DARK = np.array([0.055, 0.052, 0.058])
def render(t, check=None):
    r, C = camera(t)
    pt = plate_time(t); pi = (pt - PT0) * PFPS; i0 = int(pi)
    # plate: lock the moon to C (partly stabilised during the hold, fully once we push)
    lock = eio((t - 7.5) / 2.5)
    j = int(np.clip(i0, 0, len(TR) - 1))
    follow = 0.45 + 0.55 * lock          # how much of the hand-shake the camera follows (all of it once we push)
    mx = sx[j] + follow * (cx[j] - sx[j]); my = sy[j] + follow * (cy[j] - sy[j])
    # the moon's real (jittering) position on screen, so her world stays glued to it
    S = r / RM
    Cm = C + S * np.array([cx[j] - mx, cy[j] - my])
    out = np.zeros((H, W, 3), np.float32)
    if r < HD * 2.4:
        # zoom blur from the camera's speed (log r per frame)
        dl = abs(math.log(float(keys(t + 1 / FPS, R_KEYS, log=True))) - math.log(r))
        n = 1 if dl < 0.004 else 7
        P = plate(j)
        acc = np.zeros_like(out)
        for k in range(n):
            s = S * math.exp(-dl * 0.9 * k / max(n - 1, 1)) if n > 1 else S
            M = np.float32([[s, 0, C[0] - s * mx], [0, s, C[1] - s * my]])
            acc += cv2.warpAffine(P, M, (W, H), flags=cv2.INTER_CUBIC if s < 6 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        out = acc / n / 255.0
        # grade: a touch deeper, midnight blue in the shadows
        out = out * np.array([1.06, 1.0, 0.95]) * 0.95 + np.array([0.012, 0.006, 0.0])
        hi = np.clip((out.mean(2, keepdims=True) - 0.35) / 0.4, 0, 1); out = out * (1 - hi) + out * np.array([0.90, 0.97, 1.06]) * hi
    # ---- the disc ----
    rb = r * 1.6 + 6       # room for the halo
    x0, y0 = int(max(0, Cm[0] - rb)), int(max(0, Cm[1] - rb)); x1, y1 = int(min(W, Cm[0] + rb)), int(min(H, Cm[1] + rb))
    ws = witch_state(t)
    L, A = pose(ws["raise_u"], ws["look_u"], t=t, walk=ws["walk"], pinch=ws["pinch"])
    mp, mrad, mu = inner_moon(t, A, ws["x"], ws["y"])
    # m: how much of the disc is her world (vs the real moon's face)
    m_push = eio((r - RM * 2.25) / (RM * 3.6))
    m = m_push if t < T_DROP else max(m_push, 0.82)
    if x1 > x0 and y1 > y0:
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        wx = (xs + 0.5 - Cm[0]) / r; wy = (ys + 0.5 - Cm[1]) / r
        rho = np.sqrt(wx * wx + wy * wy); dm = disc_mask(rho, r)
        base = out[y0:y1, x0:x1]
        # up close, the real moon's bright face must never peek out around the window (it flickers with the hand-shake)
        lim = 1.0 - 0.80 * eio((r - RM * 3.2) / (RM * 3.5))
        if lim < 0.999:
            ring = np.clip((rho - 0.97) / 0.05, 0, 1)[..., None]
            base = base - ring * np.clip(base - lim * 0.22 - 0.02, 0, None) * (1 - lim) / 0.8
        if m > 0.001:
            wc = world(wx, wy, t, ws, A, mp, mrad, inside=eio((r - RM * 4) / (RM * 14)))
            # limb darkening and the real moon's mottling, both fading as the disc becomes a window
            far = 1 - eio((r - RM * 3) / (RM * 30))
            wc = wc * (1 - 0.30 * far * rho[..., None] ** 3)
            if far > 0.01:
                mot = cv2.GaussianBlur(cv2.cvtColor(base.astype(np.float32), cv2.COLOR_BGR2GRAY), (0, 0), max(1.0, r * 0.03))
                mot = mot / (np.percentile(mot[rho < 0.7], 80) + 1e-4) if (rho < 0.7).any() else mot
                wc = wc * (1 - 0.35 * far * (1 - np.clip(mot, 0, 1.2))[..., None])
            a = (dm * m)[..., None]
            base = base * (1 - a) + wc * a
        # her moon (screen blend: a pale moon in a luminous sky)
        mpx = Cm + mp * r; mr = mrad * r
        if mr > 0.6 and m > 0.01:
            s = mr / MR; sz = int(math.ceil(MR * s * 1.3)) * 2 + 4
            M = np.float32([[s, 0, sz / 2 - s * MC[0]], [0, s, sz / 2 - s * MC[1]]])
            spr = cv2.warpAffine(MOONTEX, M, (sz, sz), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
            spr = np.clip(spr * np.array([0.93, 1.0, 1.04]) * 1.08, 0, 1)
            gx0, gy0 = int(mpx[0] - sz / 2), int(mpx[1] - sz / 2)
            yy, xx = np.mgrid[0:sz, 0:sz]; rr = np.hypot(xx - sz / 2, yy - sz / 2) / mr
            glow = 0.10 * np.exp(-np.clip(rr - 1, 0, None) / 0.25)[..., None] * (1 + 1.2 * eio((t - 16.8) / 0.15) * (1 - eio((t - 17.0) / 0.5)))
            sx0, sy0 = max(0, x0 - gx0), max(0, y0 - gy0); ex0, ey0 = max(gx0, x0), max(gy0, y0)
            ex1, ey1 = min(gx0 + sz, x1), min(gy0 + sz, y1)
            if ex1 > ex0 and ey1 > ey0:
                reg = base[ey0 - y0:ey1 - y0, ex0 - x0:ex1 - x0]
                sp = spr[ey0 - gy0:ey1 - gy0, ex0 - gx0:ex1 - gx0]; gl = glow[ey0 - gy0:ey1 - gy0, ex0 - gx0:ex1 - gx0]
                k = m * dm[ey0 - y0:ey1 - y0, ex0 - x0:ex1 - x0, None]
                reg[:] = reg + k * ((1 - (1 - reg) * (1 - sp)) - reg) + k * gl * np.array([0.8, 0.9, 1.0])
        # her, and her reflection on the mirror plain
        org = Cm + np.array([ws["x"], ws["y"]]) * r; sc = H_W * r
        if sc > 4:
            sil = raster(L, org, sc, (H, W))[y0:y1, x0:x1]
            fing = raster(A["fingers"], org, sc, (H, W))[y0:y1, x0:x1]
            refl = raster(L + A["fingers"], np.array([org[0], Cm[1] + (2 * HY - ws["y"]) * r]), sc, (H, W), flip_y=True)[y0:y1, x0:x1]
            if sc > 30:
                rip = 0.004 * sc * np.sin(np.arange(y1 - y0)[:, None] * (6.0 / max(sc * 0.02, 1)) + t * 2.0)
                mxp = (np.arange(x1 - x0)[None, :] + rip).astype(np.float32); myp = np.repeat(np.arange(y1 - y0, dtype=np.float32)[:, None], x1 - x0, 1)
                refl = cv2.remap(refl, mxp, myp.astype(np.float32), cv2.INTER_LINEAR)
            ink = DARK + 0.06 * HORIZ
            # on the real moon's face she is a shadow; in her world, a silhouette
            sh = 0.82 * (1 - m) + m
            a = (sil * dm * sh)[..., None]; base = base * (1 - a) + ink * a
            a = (refl * dm * m * 0.55 * (wy > HY))[..., None]; base = base * (1 - a) + ink * 1.4 * a
            # fingers in front of her moon
            a = (fing * dm * sh)[..., None]; base = base * (1 - a) + ink * a
        # a soft halo outside the rim (the real moon's glow, kept as the disc grows)
        halo = np.exp(-np.clip(rho - 1, 0, None) / 0.10) * (rho > 1) * (0.16 + 0.10 * (t > T_DROP)) * eio((r - RM * 2) / (RM * 6))
        base = base + halo[..., None] * MOONCOL / 255.0
        out[y0:y1, x0:x1] = base
        if check is not None:
            ov = overlaps(A["arm"], [A["brim"], A["hat"], A["face"]])
            if ov > 2e-5: check.append(f"CHECK t={t:.2f} arm cuts hat/face {ov:.2e}")
            hand_moon = np.linalg.norm(mp - (np.array([ws['x'], ws['y']]) + A["moon_c"] * H_W)) if mu > 0.99 else 0
            if mu > 0.99 and hand_moon > 0.002: check.append(f"CHECK t={t:.2f} moon off her fingers by {hand_moon:.4f}")
    # ---- passing through the surface: a breath of lunar mist ----
    xm = math.log(r / (HD * 0.95)); am = 0.24 * math.exp(-(xm / 0.28) ** 2)
    if am > 0.01:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        u = (xx - C[0]) / r; v = (yy - C[1]) / r
        mist = sample("mist", u * 1.3 + 0.2, v * 1.3 + 0.7)
        mist2 = sample("wisp", u * 3.0 + 0.5, v * 3.0)
        lift = np.clip(0.5 + 0.3 * mist + 0.12 * mist2, 0, 1)[..., None]      # light only: a veil, never dark smoke
        out = out + (HORIZ * 1.1 - out) * np.clip(am * lift * 1.6, 0, 0.6)
    # ---- the drop: a single exposure breath as the moon lands in her fingers ----
    fl = 0.10 * math.exp(-max(t - T_DROP, 0) / 0.08) * (t >= T_DROP - 1 / FPS)
    out = out * (1 + fl)
    # ---- finish: bloom, vignette, grain ----
    br = np.clip(out - 0.62, 0, None); out = out + 0.22 * cv2.GaussianBlur(br, (0, 0), H * 0.012)
    yy, xx = np.ogrid[0:H, 0:W]; vg = 1 - 0.16 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    out = out * vg[..., None].astype(np.float32)
    rng = np.random.default_rng(int(t * 1000))
    gr = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.7) * 0.020
    out = out + gr[..., None] * (0.6 + 0.6 * np.sqrt(np.clip(out, 0, 1)))
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    out_dir = ARGS[0]; os.makedirs(out_dir, exist_ok=True)
    if "--still" in ARGS:
        for ts in opt("--still", "").split(","):
            t = float(ts); chk = []; t0 = time.time()
            cv2.imwrite(f"{out_dir}/still_{t:06.2f}.jpg", render(t, chk), [cv2.IMWRITE_JPEG_QUALITY, 92])
            print(f"t={t:.2f} {time.time() - t0:.2f}s", *chk)
        sys.exit()
    a = int(ARGS[1]) if len(ARGS) > 1 and ARGS[1].isdigit() else 0; b = int(ARGS[2]) if len(ARGS) > 2 and ARGS[2].isdigit() else NF
    log = open(f"{out_dir}/render.log", "a")
    for f in range(a, b):
        p = f"{out_dir}/{f:04d}.png"
        if os.path.exists(p): continue
        chk = []; img = render(T0 + f / FPS, chk)
        cv2.imwrite(p + ".tmp.png", img, [cv2.IMWRITE_PNG_COMPRESSION, 1]); os.replace(p + ".tmp.png", p)
        for c in chk: log.write(f"{f} {c}\n")
    log.close()
