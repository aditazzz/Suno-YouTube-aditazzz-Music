"""Round 2 proof of concept: the same song window and camera spine as round 1 (portal.py), with what changed:
- inside the moon is world C (moon-doors on the A crater plain), rendered by its own perspective camera, so the move
  in has real parallax: the tiny figure on the moon's face becomes life-size faster than the moon grows
- we pass through the surface through HER clouds (IMG_2269 frames), not generated mist
- the gesture: she calls the moon out of the door's picture (the real moon, photo_08) into her fingers, on the drop
- witch v2 (strand hair, chiffon, rim light), film grain/halation from the kit
usage: python3 poc/portal2.py <out_dir> [first last] [--still t,t,...] [--timeline poc|t2]"""
import os, sys, math, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
import portal as P                         # plate, track, easing, keys (round 1)
import wkit as K, scenes as S
from witch2 import figure, raster2, rimlight
W, H = K.W, K.H; HD = 0.5 * math.hypot(W, H); FPS = 30.0
RM = P.RM; eio, ein2, eout2, eout4, lin, keys = P.eio, P.ein2, P.eout2, P.eout4, P.lin, P.keys
ARGS = sys.argv[1:]
TLN = ARGS[ARGS.index("--timeline") + 1] if "--timeline" in ARGS else "poc"

class PocTimeline:
    """song 4.44-19.02: hold, push, through, gesture, snap out on the 16.95 drop"""
    T0, T1 = 4.44, 19.02
    T_PUSH, T_PASS, T_DROP, T_LAND = 8.64, 13.92, 16.95, 18.15
    R_HOLD = RM * 2.0
    R_KEYS = [(4.44, R_HOLD, lin), (8.64, R_HOLD * 1.07, lin), (12.4, HD * 0.55, ein2), (13.92, HD * 1.04, eout2), (16.95, HD * 1.04, lin),
              (18.15, 250.0, eout4), (19.02, 228.0, eio)]
    G_KEYS = [(4.44, (0.5 * W, 0.44 * H), lin), (8.64, (0.5 * W, 0.44 * H), lin), (13.92, (0.5 * W, 0.5 * H), eio),
              (16.95, (0.5 * W, 0.5 * H), lin), (18.15, (0.56 * W, 0.40 * H), eout4), (19.02, (0.555 * W, 0.405 * H), eio)]
    # inner camera: dollies 16 m forward from far behind as we come in (parallax), then holds; drifts back on the snap
    Z_KEYS = [(4.44, -16.0, lin), (9.0, -16.0, lin), (13.92, -4.0, ein2), (16.95, 4.0, eout2), (18.15, -16.0, eout4), (19.02, -16.0, lin)]
    X_KEYS = [(4.44, 0.0, lin), (13.92, 0.0, lin), (16.95, -1.2, eio), (18.15, 0.0, eout4), (19.02, 0.0, lin)]
    def plate_time(self, t): return 10.3 + (t - 4.44) * 0.82 if t < 15.0 else 10.4 + (t - 16.95)
    def pose(self, t):
        return dict(raise_u=eio((t - 14.25) / 1.45), look_u=eio((t - 14.0) / 1.3), pinch=eio((t - 16.55) / 0.4))
    def walk(self, t):     # she walks in across the moon's face (world metres of x offset)
        return -7.0 * (1 - eio((t - 6.3) / 3.3)), (1.0 if 6.3 < t < 9.6 else 0.0)
    def moon_flight(self, t): return eio((t - 15.55) / (16.95 - 15.55))
    def m_of(self, t, r):
        m = eio((r - RM * 2.25) / (RM * 3.6)); return m if t < self.T_DROP else max(m, 0.78)
    def fly(self, t, r):  # how much of her clouds we fly through
        x = math.log(r / (HD * 0.75)); w = math.exp(-(x / 0.40) ** 2)
        w *= min(1.0, max(0.0, (14.5 - t) / 0.6)) if t < 16.95 else min(1.0, max(0.0, (17.7 - t) / 0.4))
        return w
class T2Timeline(PocTimeline):
    """transition concept T2 (4.5 s, no song): the moon becomes a window; inside, the camera dollies so the tiny
    figure becomes enormous; we pass through her real clouds into world B"""
    T0, T1 = 10.3, 14.8
    T_PUSH, T_PASS, T_DROP, T_LAND = 10.9, 13.2, 99, 99
    R_HOLD = RM * 2.0
    R_KEYS = [(10.3, R_HOLD, lin), (10.9, R_HOLD * 1.05, lin), (12.3, HD * 0.5, ein2), (13.2, HD * 1.04, eout2), (14.8, HD * 1.04, lin)]
    G_KEYS = [(10.3, (0.5 * W, 0.44 * H), lin), (13.2, (0.5 * W, 0.5 * H), eio), (14.8, (0.5 * W, 0.5 * H), lin)]
    Z_KEYS = [(10.3, -22.0, lin), (11.0, -22.0, lin), (13.2, -6.0, ein2), (14.8, 5.5, eout2)]
    X_KEYS = [(10.3, 0.0, lin), (13.2, 0.0, lin), (14.8, -1.0, eio)]
    def plate_time(self, t): return t
    def pose(self, t): return dict(raise_u=0.0, look_u=0.35 + 0.4 * eio((t - 13.4) / 1.2), pinch=0.0)
    def walk(self, t): return 0.0, 0.0
    def moon_flight(self, t): return 0.0
    def m_of(self, t, r): return eio((r - RM * 2.25) / (RM * 3.6))
    def fly(self, t, r):
        x = math.log(r / (HD * 0.75)); w = math.exp(-(x / 0.40) ** 2)
        return w * min(1.0, max(0.0, (13.8 - t) / 0.6))
TL = T2Timeline() if TLN == "t2" else PocTimeline()

_p08 = cv2.imread(f"{K.AS}/photo_08.png").astype(np.float32) / 255
MOON08 = (451.3, 497.5, 59.0)
def door_picture(cx, cy, r, moon_left):
    """the big door's picture: her photo_08 (moon in lit clouds), cropped square; the moon itself is lifted out
    (moon_left: 1 = still in the picture, 0 = gone, a faint ghost of its glow remains)"""
    h, w = _p08.shape[:2]; sz = int(2 * r) + 4; s = sz / w
    pic = cv2.resize(_p08, (sz, int(h * s) + 1), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    yo = (pic.shape[0] - sz) // 2; pic = pic[yo:yo + sz]
    mx, my, mr = MOON08[0] * s, MOON08[1] * s - yo, MOON08[2] * s
    pic = np.clip(pic * 1.15 + 0.02, 0, 1) ** 0.9
    pic = pic * 0.55 + pic.mean(2, keepdims=True) * np.array([0.92, 0.98, 1.04], np.float32) * 0.45
    if moon_left < 1:
        yy, xx = np.ogrid[0:sz, 0:sz]; d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2) / mr
        hole = np.clip((1.25 - d) / 0.25, 0, 1)[..., None]
        # what was behind the moon: the cloud around it, smoothed in
        fill = cv2.GaussianBlur(pic, (0, 0), max(mr * 0.6, 1.0))
        ring = cv2.GaussianBlur(pic * (1 - hole), (0, 0), max(mr * 0.9, 1)) / np.maximum(cv2.GaussianBlur(np.ascontiguousarray(1 - hole[..., 0]), (0, 0), max(mr * 0.9, 1)), 1e-3)[..., None]
        bg = ring * 0.9 + np.array([0.04, 0.045, 0.05], np.float32) * 0.0
        k = (1 - moon_left)
        pic = pic * (1 - hole * k) + (bg * 0.92 + 0.08 * np.exp(-d ** 2 / 2)[..., None] * 0.6) * hole * k
    full = np.zeros((H, W, 3), np.float32); y0, x0 = int(cy - sz / 2), int(cx - sz / 2)
    ya, xa = max(0, y0), max(0, x0); yb, xb = min(H, y0 + sz), min(W, x0 + sz)
    if yb > ya and xb > xa: full[ya:yb, xa:xb] = pic[ya - y0:yb - y0, xa - x0:xb - x0]
    door_picture.moon = (x0 + mx, y0 + my, mr)
    return full

_moonspr = None
def moon_sprite(img, c, r, glow=0.0):
    """the moon lifted from photo_08, drawn at screen c, radius r"""
    global _moonspr
    if _moonspr is None:
        mx, my, mr = MOON08; R = int(mr * 1.3)
        _moonspr = _p08[int(my) - R:int(my) + R, int(mx) - R:int(mx) + R].copy()
    R0 = _moonspr.shape[0] / 2; s = r / MOON08[2]
    M = np.float32([[s, 0, c[0] - s * R0], [0, s, c[1] - s * R0]])
    spr = cv2.warpAffine(_moonspr, M, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    yy, xx = np.ogrid[0:H, 0:W]; d = np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2) / max(r, 1e-3)
    a = np.clip((1.0 - d) * max(r, 1) / 1.2 + 0.5, 0, 1)[..., None]
    out = img * (1 - a) + np.clip(spr * 1.15, 0, 1) * a
    out = out + (glow * np.exp(-np.clip(d - 1, 0, None) / 0.5) * (d > 1))[..., None] * np.array([0.85, 0.92, 1.0], np.float32)
    return out

def world(t):
    """her world for the inner camera at time t -> linear float image (C for the proof of concept, B for T2)"""
    if TLN == "t2":
        c = K.cam(z=float(keys(t, TL.Z_KEYS)), x=float(keys(t, TL.X_KEYS)))
        fig = figure(t=t, wind=1.8, **TL.pose(t))
        img = S.scene_B(c, t, TL.pose(t), witch_on=True, fig=fig)
        world.fig = (fig, None, None)
        return img
    z = float(keys(t, TL.Z_KEYS)); dx, walking = TL.walk(t)
    c = K.cam(z=z, x=float(keys(t, TL.X_KEYS)))
    pose = TL.pose(t); u = TL.moon_flight(t)
    fig = figure(t=t, wind=0.6, walk=walking, **pose)
    img = S.scene_C(c, t, pose, witch_on=False, big_door_img=lambda cx, cy, r: door_picture(cx, cy, r, 1 - (u > 0) * 1.0))
    # her (placed by hand so she can walk in, and so the moon can land in her fingers)
    feet, k = K.project(c, K.X_WITCH + dx, K.Z_WITCH)
    hgt = 1.7 * k
    img, a = K.witch(img, fig, light_dir=(1, -0.2), light_col=(0.65, 0.75, 0.85), rim=1.1, shadow_dir=(1.8, -0.14), shadow_k=0.55,
                     feet=tuple(feet), height=hgt, hz_row=c["hz"])
    # the moon leaves the door's picture and arcs into her fingers
    if u > 0 and hasattr(door_picture, "moon"):
        m0 = np.array(door_picture.moon[:2]); r0 = door_picture.moon[2]
        hand = feet + fig["A"]["moon_c"] * hgt; r1 = fig["A"]["moon_r"] * hgt * 0.95
        p = m0 + (hand - m0) * u + np.array([0, -0.07 * H]) * math.sin(math.pi * u)
        rr = r0 + (r1 - r0) * u
        glow = 0.10 + 0.5 * math.exp(-((t - 16.95) / 0.12) ** 2)
        img = moon_sprite(img, p, rr, glow=glow)
        if u > 0.9:   # fingers back over the moon's edge
            hand_fig = dict(solid=fig["hand"], sheer=[], hair=[])
            ah, _ = raster2(hand_fig, np.array(feet, float), hgt, (H, W))
            img = img * (1 - ah[..., None]) + K.INK * ah[..., None] + rimlight(ah, (1, -0.2), max(hgt / 260, 0.8))[..., None] * np.array([0.65, 0.75, 0.85], np.float32)
    world.fig = (fig, feet, hgt)
    return img

_cloud = None
def her_clouds(C, r):
    """a layer of her real clouds (IMG_2269) at the moon's surface, scaled with the camera"""
    global _cloud
    if _cloud is None:
        im = cv2.imread(f"{K.AS}/cloudframe_46.png").astype(np.float32) / 255
        _cloud = im[0:900]
    th, tw = _cloud.shape[:2]; s = r * 2.4 / tw
    M = np.float32([[s, 0, C[0] - s * tw / 2], [0, s, C[1] - s * th * 0.45]])
    cl = cv2.warpAffine(_cloud, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    g = cl.mean(2); dens = np.clip((g - cv2.GaussianBlur(g, (0, 0), 40)) * 4 + 0.55, 0, 1)
    return cl, dens

def render(t, check=None):
    r = float(keys(t, TL.R_KEYS, log=True)); G = keys(t, TL.G_KEYS); C = G
    pt = TL.plate_time(t); j = int(np.clip((pt - P.PT0) * P.PFPS, 0, len(P.TR) - 1))
    lock = eio((t - 7.5) / 2.5); follow = 0.45 + 0.55 * lock
    mx = P.sx[j] + follow * (P.cx[j] - P.sx[j]); my = P.sy[j] + follow * (P.cy[j] - P.sy[j])
    S_ = r / RM; Cm = C + S_ * np.array([P.cx[j] - mx, P.cy[j] - my])
    out = np.zeros((H, W, 3), np.float32)
    if r < HD * 2.6:
        dl = abs(math.log(float(keys(t + 1 / FPS, TL.R_KEYS, log=True))) - math.log(r)); n = 1 if dl < 0.004 else 7
        Pl = P.plate(j); acc = np.zeros_like(out)
        for k in range(n):
            s = S_ * math.exp(-dl * 0.9 * k / max(n - 1, 1)) if n > 1 else S_
            M = np.float32([[s, 0, C[0] - s * mx], [0, s, C[1] - s * my]])
            acc += cv2.warpAffine(Pl, M, (W, H), flags=cv2.INTER_CUBIC if s < 6 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        out = acc / n / 255.0
        out = out * np.array([1.06, 1.0, 0.95]) * 0.95 + np.array([0.012, 0.006, 0.0])
        hi = np.clip((out.mean(2, keepdims=True) - 0.35) / 0.4, 0, 1); out = out * (1 - hi) + out * np.array([0.90, 0.97, 1.06]) * hi
        out = out.astype(np.float32)
    m = TL.m_of(t, r)
    ys, xs = np.ogrid[0:H, 0:W]; rho = np.sqrt((xs - Cm[0]) ** 2 + (ys - Cm[1]) ** 2) / r
    dm = np.clip((1 - rho) * r / (1.2 + 2.0 * (r < 400)) + 0.5, 0, 1).astype(np.float32)
    # the plate moon's face never peeks out around the window once we're close
    lim = 1.0 - 0.80 * eio((r - RM * 3.2) / (RM * 3.5))
    if lim < 0.999:
        ring = np.clip((rho - 0.97) / 0.05, 0, 1)[..., None]
        out = out - ring * np.clip(out - lim * 0.22 - 0.02, 0, None) * (1 - lim) / 0.8
    if m > 0.001:
        wimg = world(t)
        k = r / HD
        # the round window reaches past the world image: extend it (sky and ground repeat vertically, sides mirror)
        px_, py_ = int(W * 0.35), int(H * 0.62)
        big = np.pad(wimg, ((0, 0), (px_, px_), (0, 0)), mode="reflect")
        big = np.pad(big, ((py_, py_), (0, 0), (0, 0)), mode="edge")
        if k < 1:
            small = cv2.resize(big, (max(1, int(big.shape[1] * k)), max(1, int(big.shape[0] * k))), interpolation=cv2.INTER_AREA)
            M2 = np.float32([[1, 0, Cm[0] - small.shape[1] / 2], [0, 1, Cm[1] - small.shape[0] / 2]])
            wv = cv2.warpAffine(small, M2, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            wv = wv * (1 - 0.55 * np.clip((rho - 0.80) / 0.20, 0, 1))[..., None]      # the window's edge falls into shadow
        else:
            M = np.float32([[k, 0, Cm[0] - k * big.shape[1] / 2], [0, k, Cm[1] - k * big.shape[0] / 2]])
            wv = cv2.warpAffine(big, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        # seen from outside, the moon's own light and mottling stay over the window and fade as we near
        far = 1 - eio((r - RM * 3) / (RM * 11))
        if far > 0.01:
            mot = cv2.GaussianBlur(out.mean(2), (0, 0), max(1.0, r * 0.03))
            sel = rho < 0.7
            mot = mot / (np.percentile(mot[sel], 80) + 1e-4) if sel.any() else mot
            lift = (0.38 * far) * np.clip(mot, 0, 1.2)[..., None] * np.array([0.80, 0.90, 0.95], np.float32)
            wv = wv + lift * (1 - wv)
            wv = wv * (1 - 0.25 * far * (rho ** 3)[..., None])
        a = (dm * m)[..., None]
        out = out * (1 - a) + wv * a
        # a thin moonlit limb: the rim is a physical edge (a door) we pass through, not a dissolve
        limb = np.exp(-((rho - 1) * r / 2.2) ** 2) * m * (0.25 + 0.75 * eio((r - RM * 4) / (RM * 6)))
        out = out + limb[..., None] * np.array([0.70, 0.80, 0.90], np.float32) * 0.55
    elif hasattr(TL, "hold_shadow"):
        out = TL.hold_shadow(out, t, Cm, r, dm)
    else:
        # the hold: she is a shadow walking on the moon's face (the same figure, at the size the world puts her)
        z = float(keys(t, TL.Z_KEYS)); dx, walking = TL.walk(t); c = K.cam(z=z)
        feet, kk = K.project(c, K.X_WITCH + dx, K.Z_WITCH); k = r / HD
        if TLN == "t2": walking = 0.0
        sp = Cm + (feet - np.array([W / 2, H / 2])) * k
        fig = figure(t=t, wind=0.6, walk=walking, strands=120, **TL.pose(t))
        a, _ = raster2(fig, sp, 1.7 * kk * k, (H, W))
        out = out * (1 - 0.8 * (a * dm)[..., None])
    halo = np.exp(-np.clip(rho - 1, 0, None) / 0.10) * (rho > 1) * (0.14 + 0.10 * (t > TL.T_DROP)) * eio((r - RM * 2) / (RM * 6))
    out = out + halo[..., None] * np.array([0.75, 0.85, 0.92], np.float32) * 0.8
    # passing through the surface: her real clouds (the plate, zoomed with us) drift across the window's edge
    fa = TL.fly(t, r)
    if fa > 0.01 and r < HD * 2.6:
        Pl = P.plate(j).astype(np.float32) / 255; s_ = S_ * 1.08
        M = np.float32([[s_, 0, C[0] - s_ * mx], [0, s_, C[1] - s_ * my]])
        cl = cv2.warpAffine(Pl, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        g = cv2.GaussianBlur(cl.mean(2), (0, 0), 3)
        dens = np.clip((g - cv2.GaussianBlur(g, (0, 0), 25)) * 14 - 0.10, 0, 1) ** 1.5
        edge = np.clip((rho - 0.62) / 0.38, 0, 1) * np.clip((1.25 - rho) / 0.25, 0, 1)
        a = np.clip(dens * edge * fa * 0.9, 0, 0.38)[..., None]
        out = out * (1 - a) + (0.18 + 1.1 * cl) * np.array([0.92, 0.97, 1.03], np.float32) * a
    fl = 0.08 * math.exp(-max(t - TL.T_DROP, 0) / 0.08) * (t >= TL.T_DROP - 1 / FPS)
    out = out * (1 + fl)
    if check is not None and hasattr(world, "fig") and m > 0.001 and TLN != "t2":
        from witch import overlaps
        fig = world.fig[0]; A = fig["A"]
        ov = overlaps([p for p in fig["hand"]], [A["brim"], A["hat"]])
        if ov > 2e-5: check.append(f"CHECK t={t:.2f} hand cuts hat {ov:.2e}")
    return K.finish(out, grain=0.026, vign=0.26, hal=0.20, seed=int(t * 1000) % 100000)

if __name__ == "__main__":
    out_dir = ARGS[0]; os.makedirs(out_dir, exist_ok=True)
    if "--still" in ARGS:
        for ts in ARGS[ARGS.index("--still") + 1].split(","):
            t = float(ts); t0 = time.time(); chk = []
            K.save(render(t, chk), f"{out_dir}/still_{t:06.2f}.jpg"); print(f"t={t:.2f} {time.time() - t0:.1f}s", *chk)
        sys.exit()
    NF = int(round((TL.T1 - TL.T0) * FPS))
    a = int(ARGS[1]) if len(ARGS) > 1 and ARGS[1].isdigit() else 0; b = int(ARGS[2]) if len(ARGS) > 2 and ARGS[2].isdigit() else NF
    log = open(f"{out_dir}/render.log", "a")
    for f in range(a, min(b, NF)):
        p = f"{out_dir}/{f:04d}.jpg"
        if os.path.exists(p): continue
        chk = []; img = render(TL.T0 + f / FPS, chk)
        K.save(img, p + ".tmp.jpg", q=95); os.replace(p + ".tmp.jpg", p)
        for c_ in chk: log.write(f"{f} {c_}\n")
    log.close()
