"""Round 2 worlds as scenes with a camera (so transitions and the proof of concept can move through them).
scene_A: photographic dreamscape · scene_B: surreal editorial · scene_C: moon architecture.
Each takes a camera c (wkit.cam(...)), time t, her pose, and returns a linear-light float image (no grain yet)."""
import sys, math, numpy as np, cv2
sys.path.insert(0, "poc")
import wkit as K
from witch2 import figure
W, H, F0, HZ = K.W, K.H, K.F, K.HZ
MOON_REF = (K.KEY[0], K.KEY[1], int(0.27 * H))

def photo(name, size):
    im = cv2.imread(f"{K.AS}/{name}").astype(np.float32) / 255
    h, w = im.shape[:2]; s = max(size[0] / w, size[1] / h)
    im = cv2.resize(im, (int(w * s) + 1, int(h * s) + 1), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y0 = (im.shape[0] - size[1]) // 2; x0 = (im.shape[1] - size[0]) // 2
    return im[y0:y0 + size[1], x0:x0 + size[0]]

def place_witch(img, c, t, pose, wind, light_dir, light_col, rim, shadow_dir, shadow_k, translucency=0.42, X=None, Z=None, fig=None):
    X = K.X_WITCH if X is None else X; Z = K.Z_WITCH if Z is None else Z
    feet, k = K.project(c, X, Z)
    if Z - c["z"] < 0.3: return img, None, feet, k
    fig = fig or figure(t=t, wind=wind, **pose)
    img, a = K.witch(img, fig, light_dir=light_dir, light_col=light_col, rim=rim, shadow_dir=shadow_dir, shadow_k=shadow_k,
                     feet=tuple(feet), height=1.7 * k, translucency=translucency, hz_row=c["hz"])
    return img, fig, feet, k

def dof(img, c, near_row_frac=0.86, sigma=7.0):
    """photographic depth of field: the ground right in front of the lens falls out of focus"""
    y0 = int(c["hz"] + (H - c["hz"]) * 0.62)
    if y0 >= H: return img
    bl = cv2.GaussianBlur(img, (0, 0), sigma)
    w = np.clip((np.arange(H) - y0) / max(H - y0, 1), 0, 1)[:, None, None] ** 1.2
    return img * (1 - w) + bl * w

def scene_A(c=None, t=0.0, pose=dict(raise_u=1.0, look_u=1.0, pinch=0.0), moon_ref=MOON_REF, witch_on=True, fig=None):
    c = c or K.CAM0; hz = c["hz"]; sc = c["F"] / F0
    img = K.sky_grad((0.040, 0.042, 0.050), (0.20, 0.22, 0.25), (0.34, 0.37, 0.42), hz=hz)
    mpos, R = K.sky_pos(c, *moon_ref)
    ys, xs = np.ogrid[0:H, 0:W]
    glow = np.exp(-(((xs - mpos[0]) / (900.0 * sc)) ** 2 + ((ys - mpos[1] - 120 * sc) / (420.0 * sc)) ** 2)) * (ys <= hz)
    img += (glow * 0.22)[..., None] * np.array([0.85, 0.92, 1.0], np.float32)
    img = K.fog_band(img, hz - (HZ - 170) * sc, 300 * sc, 0.30, (0.30, 0.32, 0.36), scale=1.6 * sc, offset=0.13 + t * 0.002 + c["x"] * 0.004, name="cloudframe_1")
    if R > 1: img = K.moon(img, mpos, R, tint=(0.86, 0.95, 1.03), gain=1.18, glow=0.16)
    img = K.fog_band(img, mpos[1] + R * 0.45, 150 * sc, 0.40, (0.26, 0.28, 0.32), scale=1.3 * sc, offset=0.4 + t * 0.004 + c["x"] * 0.004, name="cloudframe_40", blur=6)
    g, d = K.ground(tint=(0.80, 0.88, 0.96), haze=(0.36, 0.39, 0.45), haze_m=380.0, exposure=1.7, c=c)
    gm = (d < 1e8)[..., None]; img = np.where(gm, g, img)
    img = K.fog_band(img, hz - 10 * sc, 120 * sc, 1.0, (0.48, 0.51, 0.56), scale=2.2 * sc, offset=0.2 + t * 0.003 + c["x"] * 0.01, name="cloudframe_46", soft=0.8, blur=2)
    img = K.fog_band(img, hz + 40 * sc, 110 * sc, 0.55, (0.36, 0.39, 0.44), scale=1.5 * sc, offset=0.55 + t * 0.006 + c["x"] * 0.02, name="cloudframe_40", soft=0.7)
    img = dof(img, c)
    if witch_on:
        img, fig, feet, k = place_witch(img, c, t, pose, 0.7, (1, -0.35), (0.62, 0.72, 0.82), 0.9, (1.9, -0.16), 0.6, fig=fig)
    return img

def scene_B(c=None, t=0.0, pose=dict(raise_u=1.0, look_u=1.0, pinch=0.0), witch_on=True, fig=None):
    c = c or K.CAM0; hz = c["hz"]; sc = c["F"] / F0
    img = K.sky_grad((0.20, 0.25, 0.33), (0.42, 0.55, 0.70), (0.55, 0.70, 0.86), hz=hz)
    mpos, R = K.sky_pos(c, K.KEY[0], K.KEY[1] + 30, int(0.30 * H))
    ys, xs = np.ogrid[0:H, 0:W]
    glow = np.exp(-(((xs - mpos[0]) / (700.0 * sc)) ** 2 + ((ys - mpos[1]) / (500.0 * sc)) ** 2)) * (ys <= hz)
    img += (glow * 0.20)[..., None] * np.array([0.55, 0.75, 0.95], np.float32)
    img = K.fog_band(img, hz - (HZ - 120) * sc, 260 * sc, 0.18, (0.36, 0.46, 0.58), scale=2.0 * sc, offset=0.3 + t * 0.002, name="cloudframe_30")
    if R > 1: img = K.moon(img, mpos, R, tint=(0.70, 0.86, 1.0), gain=1.12, glow=0.10)
    hzi = int(round(hz))
    if hzi < H - 1:
        y0 = max(hzi + 1, 0); yy = np.arange(y0, H)[:, None]; k = ((yy - hz) / max(H - hz, 1)) ** 0.6
        ground = np.array([0.30, 0.38, 0.48], np.float32) * (1 - k[..., None]) * 0.55 + np.array([0.05, 0.05, 0.06], np.float32) * k[..., None]
        sky = img.copy(); img[y0:] = np.broadcast_to(ground, (H - y0, W, 3))
        src = np.clip(2 * hzi - np.arange(y0, H), 0, H - 1)
        refl = cv2.GaussianBlur(sky[src], (0, 0), 6, sigmaY=14)
        img[y0:] = img[y0:] * 0.55 + refl * 0.38 * (1 - k[..., None] * 0.8)
    img = K.fog_band(img, hz + 4 * sc, 40 * sc, 0.5, (0.45, 0.58, 0.72), scale=2.5 * sc, offset=0.1 + t * 0.003, name="cloudframe_46", soft=0.9)
    if witch_on:
        img, fig, feet, k = place_witch(img, c, t, pose, 2.2, (1, -0.45), (0.62, 0.82, 1.0), 1.3, (0.55, -0.55), 0.45, translucency=0.55, fig=fig)
    return np.clip((img - 0.02) * 1.08, 0, None)

DOORS = [(-0.385, "photo_01.jpg", 0.075, 26), (0.43, "photo_14.jpg", 0.06, 18), (0.18, "photo_08.png", 0.30, 70)]
def scene_C(c=None, t=0.0, pose=dict(raise_u=1.0, look_u=1.0, pinch=0.0), witch_on=True, fig=None, big_door_img=None):
    """moon-doors stand on the plain at fixed world positions; each shows one of her photos (big_door_img overrides
    the big door's picture, e.g. her live footage)"""
    c = c or K.CAM0; hz = c["hz"]; sc = c["F"] / F0
    img = K.sky_grad((0.025, 0.027, 0.034), (0.10, 0.11, 0.13), (0.16, 0.17, 0.20), hz=hz)
    g, d = K.ground(tint=(0.62, 0.70, 0.80), haze=(0.15, 0.16, 0.19), haze_m=320.0, exposure=1.15, c=c)
    gm = (d < 1e8)[..., None]; img = np.where(gm, g, img)
    img = K.fog_band(img, hz + 4 * sc, 50 * sc, 0.6, (0.17, 0.18, 0.21), scale=2.2 * sc, offset=0.2 + c["x"] * 0.01, name="cloudframe_46", soft=0.8)
    ys, xs = np.ogrid[0:H, 0:W]
    out_doors = []
    # doors as world objects: (screen x fraction at CAM0, picture, radius as fraction of H at CAM0, bottom offset below horizon at CAM0)
    for fx, ph, rf, boff in DOORS:
        Zd = F0 * K.CAM_H / boff; Xd = fx * W * Zd / F0          # their place in the world, from the reference framing
        base, k = K.project(c, Xd, Zd); r = rf * H * Zd / F0 * k   # radius in metres * px/m
        if Zd - c["z"] < 0.2: continue
        cx, by = base; cy = by - r
        if r < 0.5 or cx + r < -W or cx - r > 2 * W: continue
        m = np.clip((r - np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)) / 1.2 + 0.5, 0, 1).astype(np.float32)
        rr = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / r
        if ph == "photo_08.png" and big_door_img is not None:
            full = big_door_img(cx, cy, r)
        else:
            sz = int(2 * r) + 4
            if sz > 6 * W: continue
            pic = photo(ph, (sz, sz)); gain = 2.4 if ph != "photo_08.png" else 1.15
            pic = np.clip(pic * gain + 0.02, 0, 1) ** 0.9
            pic = pic * 0.55 + pic.mean(2, keepdims=True) * np.array([0.92, 0.98, 1.04], np.float32) * 0.45
            full = np.zeros_like(img); y0, x0 = int(cy - sz / 2), int(cx - sz / 2)
            ya, xa = max(0, y0), max(0, x0); yb, xb = min(H, y0 + sz), min(W, x0 + sz)
            if yb > ya and xb > xa: full[ya:yb, xa:xb] = pic[ya - y0:yb - y0, xa - x0:xb - x0]
        col = full[m > 0.5].mean(0) if (m > 0.5).any() else np.zeros(3, np.float32)
        spill = np.exp(-(((xs - cx) / (r * 2.0)) ** 2 + ((ys - by - r * 0.30) / (r * 0.40)) ** 2)) * np.clip((ys - by + 2) / (r * 0.25), 0, 1) * 0.55
        img = img + spill[..., None] * col * 1.6
        cs = np.exp(-(((xs - cx) / (r * 0.55)) ** 2 + ((ys - by) / (r * 0.05 + 2)) ** 2)); img = img * (1 - 0.6 * cs[..., None])
        img = img * (1 - m[..., None]) + full * m[..., None]
        rim = np.exp(-((rr - 1) * r / 1.6) ** 2) * (0.5 + 0.5 * np.clip((xs - cx) / r, -1, 1))
        img = img + rim[..., None] * np.array([0.75, 0.85, 0.95], np.float32) * 0.8
        thick = np.exp(-((rr - 1.0) * r / 4.0) ** 2) * np.clip(-(xs - cx) / r, 0, 1) * (rr > 0.99); img = img * (1 - 0.7 * thick[..., None])
        out_doors.append((ph, cx, cy, r, by))
        if ph == "photo_08.png" and witch_on:
            f2 = figure(t=t + 3, raise_u=0, look_u=0, wind=0.4, strands=200)
            img, _ = K.witch(img, f2, light_dir=(1, -0.3), rim=0.9, feet=(cx - r * 0.18, by - r * 0.03 - 6 * sc), height=r * 0.34, shadow_k=0.0, hz_row=-1)
    img = K.fog_band(img, hz + 30 * sc, 90 * sc, 0.55, (0.20, 0.22, 0.26), scale=1.8 * sc, offset=0.5 + c["x"] * 0.02, name="cloudframe_40", soft=0.8, blur=2)
    img = dof(img, c)
    if witch_on:
        img, fig, feet, k = place_witch(img, c, t, pose, 0.6, (1, -0.2), (0.65, 0.75, 0.85), 1.1, (1.8, -0.14), 0.55, fig=fig)
        scene_C.witch = (fig, feet, k)
    scene_C.doors = out_doors
    return img

if __name__ == "__main__":
    import time
    for k in sys.argv[1:] or ["A", "B", "C"]:
        t0 = time.time()
        img = {"A": scene_A, "B": scene_B, "C": scene_C}[k](t=1.0)
        K.save(K.finish(img, grain=0.028, vign=0.28, hal=0.22, seed=1), f"build/poc/r2/style_{k}.jpg"); print(k, round(time.time() - t0, 1))
