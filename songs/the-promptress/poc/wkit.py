"""World kit (round 2): photographic 2.5D layers for the worlds inside the moon.
- terrain(): a procedural crater field (heights, raking moonlight, cast shadows), seen in true perspective with mips
- clouds from my own footage (IMG_2269 frames) as fog banks and sky at different depths
- her moon (IMG_1976 stack) as celestial objects; her photos as worlds seen through moon-doors
- the witch (witch2) with rim light, a cast shadow on the ground, film grain and halation
Units: metres; camera at height CAM_H looking at the horizon; screen y down."""
import os, math, numpy as np, cv2
from witch2 import figure, raster2, rimlight

B = "build/poc"; AS = "assets/r2"; os.makedirs(f"{B}/kit", exist_ok=True)
W, H = 1920, 1080
HZ = int(0.64 * H)          # horizon row
F = 1.0 * W                 # focal length, px
FEET = (int(0.34 * W), int(0.82 * H)); WH = 0.26 * H          # her feet and height on screen (shared composition)
CAM_H = 1.7 * (FEET[1] - HZ) / WH                              # camera height so a 1.7 m figure stands there
KEY = (int(0.68 * W), int(0.36 * H))                           # the key celestial/portal object
Z_WITCH = F * CAM_H / (FEET[1] - HZ); X_WITCH = (FEET[0] - W / 2) * Z_WITCH / F     # her place in the world (m)
CAM0 = dict(F=F, hz=HZ, cx=W / 2, x=0.0, z=0.0, ch=CAM_H)

def cam(**kw):
    c = dict(CAM0); c.update(kw); return c

def project(c, X, Z, Y=0.0):
    """world point (X right, Z forward, Y up from the ground) -> screen (x, y), px per metre at that depth"""
    d = max(Z - c["z"], 1e-3); k = c["F"] / d
    return np.array([c["cx"] + (X - c["x"]) * k, c["hz"] + (c["ch"] - Y) * k]), k

def sky_pos(c, sx, sy, sr):
    """an object at infinity, placed by where it sits in the reference framing (sx, sy, radius sr)"""
    az = (sx - W / 2) / F; el = (HZ - sy) / F
    return np.array([c["cx"] + az * c["F"], c["hz"] - el * c["F"]]), sr * c["F"] / F

def fbm(n, beta, seed):
    rng = np.random.default_rng(seed); f = np.fft.rfftfreq(n)[None, :]; g = np.fft.fftfreq(n)[:, None]
    k = np.sqrt(f * f + g * g); k[0, 0] = 1
    spec = (rng.normal(size=(n, n // 2 + 1)) + 1j * rng.normal(size=(n, n // 2 + 1))) / k ** beta; spec[0, 0] = 0
    x = np.fft.irfft2(spec, s=(n, n)).astype(np.float32); return (x - x.mean()) / x.std()

# ---------------- crater terrain ----------------
TN, TSPAN = 2048, 48.0     # texels, metres per tile
def _terrain_tex(light_el=math.radians(12), seed=5):
    p = f"{B}/kit/terrain_{seed}.npy"
    if os.path.exists(p): return np.load(p)
    rng = np.random.default_rng(seed); px = TSPAN / TN
    h = fbm(TN, 2.1, seed) * 0.22 + fbm(TN, 1.5, seed + 1) * 0.10 + fbm(TN, 1.0, seed + 3) * 0.012
    # craters: a power law of sizes, bowls with raised rims (tile-periodic stamping)
    radii = np.clip(0.45 * (1 - rng.random(2600)) ** (-1 / 1.5), 0.45, 0.17 * TSPAN)
    for r in radii:
        rp = r / px; c = rng.random(2) * TN; R = int(rp * 2.2) + 2
        ys, xs = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32); rho = np.sqrt(xs * xs + ys * ys) / rp
        d = 0.22 * r * (0.7 + 0.6 * rng.random())
        prof = np.where(rho < 1, -d * (1 - rho ** 2) + 0.18 * d, 0.18 * d * np.exp(-((rho - 1) / 0.35) ** 2))
        prof += np.where(rho < 1, 0, 0.04 * d * np.exp(-(rho - 1) / 0.6))
        prof *= np.clip((2.15 - rho) / 0.7, 0, 1)        # fades to zero before the stamp's edge (no square seams)
        iy = (np.arange(-R, R + 1) + int(c[1])) % TN; ix = (np.arange(-R, R + 1) + int(c[0])) % TN
        h[np.ix_(iy, ix)] += prof
    # albedo: maria-like large patches from her own moon (the stacked IMG_1976), tiled big, plus fine grain
    mo = cv2.imread(f"{B}/moon_1976_stack.png", -1).astype(np.float32).mean(2) / 65535
    mc = mo[180:420, 260:500]; mc = (mc - mc.mean()) / (mc.std() + 1e-6)
    alb = 0.62 + 0.10 * cv2.resize(np.tile(mc, (2, 2)), (TN, TN), interpolation=cv2.INTER_CUBIC) + 0.04 * fbm(TN, 1.0, seed + 2)
    # shading: raking moonlight from screen-right (+u), cast shadows marched along u (tile-periodic: two passes)
    gy, gx = np.gradient(h, px)
    L = np.array([math.cos(light_el), 0.18, math.sin(light_el)]); L /= np.linalg.norm(L)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    lam = np.clip(n @ L, 0, None) / math.sin(light_el) * 0.33       # flats ~0.33, sunlit slopes brighter
    tanel = math.tan(light_el) * px; hor = np.full(TN, -1e9, np.float32); shadow = np.zeros_like(h)
    for p_ in range(2):
        for x in range(TN - 1, -1, -1):
            xn = (x + 1) % TN
            hor = np.maximum(hor - tanel, h[:, xn])
            if p_ == 1: shadow[:, x] = (h[:, x] < hor - 0.03)
    shadow = cv2.GaussianBlur(shadow, (0, 0), 0.7)
    tex = np.clip(alb * (0.05 + lam * (1 - 0.9 * shadow)), 0, 1.4)
    np.save(p, tex.astype(np.float32)); return tex.astype(np.float32)

_mips = {}
def ground(tex_key="crater", tint=(0.80, 0.86, 0.92), haze=(0.30, 0.34, 0.40), haze_m=420.0, cam_x=0.0, cam_z=0.0, exposure=1.0, c=None):
    """the ground plane below the horizon, in perspective -> (img HxWx3, depth HxW in m, mask)"""
    if tex_key not in _mips:
        t = _terrain_tex(); lv = [t]
        for _ in range(7): lv.append(cv2.pyrDown(lv[-1]))
        _mips[tex_key] = lv
    lv = _mips[tex_key]
    c = c or CAM0; hz = int(round(c["hz"]))
    img = np.zeros((H, W, 3), np.float32); depth = np.full((H, W), 1e9, np.float32)
    if hz >= H - 1: return img, depth
    y0 = max(hz + 1, 0)
    ys, xs = np.mgrid[y0:H, 0:W].astype(np.float32)
    z = c["F"] * c["ch"] / np.maximum(ys - c["hz"], 0.25); x = (xs - c["cx"]) * z / c["F"]
    u = (x + c["x"] + cam_x) / TSPAN; v = (z + c["z"] + cam_z) / TSPAN
    foot = z / c["F"] / (TSPAN / TN)                                    # texels per pixel
    L = np.clip(np.log2(np.maximum(foot, 1e-3)), 0, len(lv) - 1.001)
    out = np.zeros_like(xs)
    for i in range(int(L.max()) + 2):
        if i >= len(lv): break
        wgt = np.clip(1 - np.abs(L - i), 0, 1)
        if wgt.max() < 1e-4: continue
        n = lv[i].shape[0]
        s = cv2.remap(lv[i], (u % 1 * n).astype(np.float32), (v % 1 * n).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        out += s * wgt
    # near the camera the tile runs out of resolution: blend in the same craters at 6x smaller scale (detail),
    # and let the foreground fall into shadow the way a real night photo does
    near = np.clip(1 - z / 40.0, 0, 1)
    if near.max() > 0:
        u2, v2 = u * 6.0 + 0.37, v * 6.0 + 0.61; foot2 = foot * 6.0
        L2 = np.clip(np.log2(np.maximum(foot2, 1e-3)), 0, len(lv) - 1.001); det = np.zeros_like(xs)
        for i in range(int(L2.max()) + 2):
            if i >= len(lv): break
            wgt = np.clip(1 - np.abs(L2 - i), 0, 1)
            if wgt.max() < 1e-4: continue
            n = lv[i].shape[0]
            det += cv2.remap(lv[i], (u2 % 1 * n).astype(np.float32), (v2 % 1 * n).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP) * wgt
        out = out * (1 - 0.6 * near) + (cv2.GaussianBlur(out, (0, 0), 6) * 0.5 + det * 0.5) * 0.6 * near * 1.0 + 0.0
    fall = 0.42 + 0.58 * np.clip((H - ys) / max(H - c["hz"], 1) * 1.6, 0, 1) ** 0.8
    out = out * fall
    col = out[..., None] * np.array(tint, np.float32) * exposure
    k = 1 - np.exp(-z / haze_m)
    col = col * (1 - k[..., None]) + np.array(haze, np.float32) * k[..., None]
    img[y0:] = col; depth[y0:] = z
    return img, depth

# ---------------- clouds from her footage ----------------
_cl = {}
def cloud_tex(name="cloudframe_40"):
    if name not in _cl:
        im = cv2.imread(f"{AS}/{name}.png").astype(np.float32) / 255
        g = im.mean(2)[60:900]                       # the cloud band of the frame
        g = cv2.resize(g, (g.shape[1] * 2, g.shape[0]), interpolation=cv2.INTER_CUBIC)
        base = cv2.GaussianBlur(g, (0, 0), 90)
        d = np.clip((g - base) * 5 + 0.5, 0, 1)
        d = cv2.GaussianBlur(d, (0, 0), 1.2)
        d = np.hstack([d, d[:, ::-1]])               # mirror -> horizontally tileable
        _cl[name] = d
    return _cl[name]
def fog_band(img, y_center, height, opacity, color, scale=1.0, offset=0.0, name="cloudframe_40", soft=0.5, blur=0.0):
    """a bank of her real clouds laid across the scene at one depth (parallax = offset per depth)"""
    d = cloud_tex(name); th, tw = d.shape
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    v = (ys - (y_center - height / 2)) / height
    m = np.clip(1 - np.abs(v - 0.5) * 2, 0, 1) ** soft
    uu = ((xs / (W * scale)) + offset) % 1 * tw; vv = np.clip(v, 0, 1) * (th - 1)
    s = cv2.remap(d, uu.astype(np.float32), vv.astype(np.float32), cv2.INTER_LINEAR)
    if blur > 0: s = cv2.GaussianBlur(s, (0, 0), blur)
    a = np.clip(s * m * opacity, 0, 1)[..., None]
    return img * (1 - a) + np.array(color, np.float32) * a

# ---------------- her moon ----------------
_moon = cv2.imread(f"{B}/moon_1976_stack.png", -1).astype(np.float32) / 65535
_g = cv2.GaussianBlur(_moon.mean(2), (0, 0), 3); _yy, _xx = np.nonzero(_g > 0.25)
MOON_R = 0.5 * np.ptp(_yy); MOON_C = np.array([_xx.max() - MOON_R, 0.5 * (_yy.min() + _yy.max())])   # circle from the lit limb
def moon(img, c, r, tint=(0.92, 1.0, 1.04), gain=1.1, glow=0.12, mode="screen", full=0.0):
    """her IMG_1976 moon at screen c, radius r. full>0 fills in the dark limb (a full disc)"""
    s = r / MOON_R; M = np.float32([[s, 0, c[0] - s * MOON_C[0]], [0, s, c[1] - s * MOON_C[1]]])
    spr = cv2.warpAffine(_moon, M, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    spr = np.clip(spr * gain * np.array(tint, np.float32), 0, 1)
    ys, xs = np.ogrid[0:H, 0:W]; rr = np.sqrt((xs - c[0]) ** 2 + (ys - c[1]) ** 2) / r
    if full > 0:
        disc = np.clip((1 - rr) * r / 1.5 + 0.5, 0, 1)[..., None]
        spr = np.maximum(spr, disc * full * np.array(tint, np.float32) * 0.35)
    disc = np.clip((1 - rr) * r / 1.5 + 0.5, 0, 1)[..., None]
    img = img * (1 - 0.35 * disc)
    out = 1 - (1 - img) * (1 - spr) if mode == "screen" else img * (1 - np.clip(spr.max(2, keepdims=True) * 3, 0, 1)) + spr
    out = out + glow * np.exp(-np.clip(rr - 1, 0, None) / 0.35)[..., None] * np.array(tint, np.float32) * np.clip((rr - 1) * r / 3, 0, 1)[..., None]
    return out

# ---------------- the witch on the ground ----------------
INK = np.array([0.03, 0.028, 0.032], np.float32)
def witch(img, fig, light_dir=(1, -0.5), light_col=(0.8, 0.9, 1.0), rim=1.0, shadow_dir=(-1.6, 0.18), shadow_k=0.55,
          feet=FEET, height=WH, translucency=0.42, haze=0.0, haze_col=(0.5, 0.5, 0.5), hz_row=HZ):
    org = np.array(feet, float)
    a, sh = raster2(fig, org, height, (H, W))
    # cast shadow on the ground: flatten + shear the silhouette away from the light
    if shadow_k > 0:
        Msh = np.float32([[1, shadow_dir[0], -shadow_dir[0] * org[1]], [0, shadow_dir[1], org[1] * (1 - shadow_dir[1])]])
        s = cv2.warpAffine(a, Msh, (W, H)); s = cv2.GaussianBlur(s, (0, 0), 2.5); s[:max(0, int(hz_row))] = 0
        img = img * (1 - shadow_k * s[..., None])
    r = rimlight(a, light_dir, max(height / 260, 0.8), rim)
    ink = INK * (1 - haze) + np.array(haze_col, np.float32) * haze
    col = ink + (img - ink) * (sh * translucency)[..., None]
    img = img * (1 - a[..., None]) + col * a[..., None] + r[..., None] * np.array(light_col, np.float32)
    return img, a

# ---------------- finishing: halation, vignette, grain ----------------
def finish(img, grain=0.022, vign=0.22, hal=0.18, seed=0):
    br = np.clip(img - 0.55, 0, None); img = img + hal * cv2.GaussianBlur(br, (0, 0), 18) * np.array([0.9, 0.95, 1.1], np.float32)
    ys, xs = np.ogrid[0:H, 0:W]; v = 1 - vign * (((xs - W / 2) / (W / 2)) ** 2 + ((ys - H / 2) / (H / 2)) ** 2) ** 1.2
    img = img * v[..., None].astype(np.float32)
    rng = np.random.default_rng(seed)
    g = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.75)
    c = cv2.GaussianBlur(rng.normal(0, 1, (H, W, 3)).astype(np.float32), (0, 0), 1.2) * 0.25
    lum = np.clip(img.mean(2, keepdims=True), 0, 1)
    img = img + (g[..., None] + c) * grain * (0.5 + 1.2 * np.sqrt(lum) * (1 - lum) * 2)
    return np.clip(img, 0, 1)

def sky_grad(top, mid, horizon, glow=None, hz=None):
    hz = HZ if hz is None else int(round(hz))
    ys = (np.arange(H)[:, None, None] / max(hz, 1)).astype(np.float32); ys = np.clip(ys, 0, 1)
    k = ys ** 1.3
    s = np.array(top, np.float32) * (1 - k) + np.array(horizon, np.float32) * k
    s = s * (1 - np.exp(-((ys - 0.55) / 0.3) ** 2) * 0.0) + np.array(mid, np.float32) * np.exp(-((ys - 0.6) / 0.25) ** 2) * 0.3
    img = np.broadcast_to(s, (H, W, 3)).astype(np.float32).copy()
    return img

def save(img, path, q=93):
    cv2.imwrite(path, np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, q])
