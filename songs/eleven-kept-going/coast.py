"""The view across the water toward the Cape: the cold open (a long lens on the floodlit rocket), the launch seen from
the shore, the long-exposure "two arcs", the booster standing on Landing Zone 1, and dawn.

One 3-D camera sits 3 m above the water ~7 km from the pads, so the rocket, its trajectory, the masts, the treeline and the
arcs all come from one projection (zooming is physically right); the water is a rippled mirror of everything above
the shoreline.
"""
import math
from functools import lru_cache
import numpy as np, cv2
import ekg as K
from ekg import F32, sstep, clamp, lerp, ease_io

PAD = np.array([-420.0, 0.0, -7200.0], F32)        # launch pad (rocket base)
LZ = np.array([1150.0, 0.0, -5600.0], F32)         # landing zone (closer, to the right)
EYE = np.array([0.0, 3.0, 0.0], F32)
SHORE_Z = -5100.0                                  # the far waterline (land beyond)

def cam_for(W, H, zoom=1.0, aim=None, pan=(0.0, 0.0)):
    """zoom 1 = 26 deg vertical fov. aim: world point to centre on (else the default framing). pan: deg (yaw, pitch)."""
    fov = 26.0 / zoom
    tgt = np.array([-70.0, 0.0, -1000.0], F32) if aim is None else np.asarray(aim, F32)
    d = tgt - EYE; yaw0 = math.atan2(d[0], -d[2]); pitch0 = math.atan2(d[1], math.hypot(d[0], d[2]))
    yaw, pitch = yaw0 + math.radians(pan[0]), pitch0 + math.radians(pan[1])
    t2 = EYE + np.array([math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)], F32) * 1000
    return K.Cam(EYE, t2, W, H, fov=fov)

# ---------------------------------------------------------------- the flight seen from the shore (world positions)
def ascent_pos(s):
    """seconds after liftoff -> world position. Pitch-over to the east (+x, away and right)."""
    if s <= 0: return PAD.copy()
    h = 0.5 * (2.6 + 0.16 * s) * s * s * 0.62
    turn = max(0.0, s - 10.0) ** 2.0 * 3.1
    return PAD + np.array([turn * 0.86, h, -turn * 0.36], F32)

def descent_path(u):
    """u 0..1 along the visible return: a steep fall from high in the east-north-east to LZ, curling in at the end."""
    p0 = LZ + np.array([3600.0, 2900.0, -2600.0], F32)
    p1 = LZ + np.array([1500.0, 1700.0, -900.0], F32)
    p2 = LZ + np.array([160.0, 420.0, 0.0], F32)
    a = (1 - u) ** 3; b = 3 * u * (1 - u) ** 2; c = 3 * u * u * (1 - u); d = u ** 3
    return (p0 * a + p1 * b + p2 * c + LZ * d).astype(F32)

# ---------------------------------------------------------------- scenery (world-space, cached)
@lru_cache(2)
def treeline(seed=7):
    """treeline heights along the far shore: x from -9 km to +9 km every 4 m."""
    r = np.random.default_rng(seed); xs = np.arange(-9000.0, 9000.0, 4.0, dtype=F32)
    h = 6.0 + 2.5 * np.sin(xs / 700.0) + 1.5 * np.sin(xs / 173.0 + 2)
    for _ in range(1400):
        c = r.uniform(-9000, 9000); w = r.uniform(8, 40); hh = r.uniform(3, 11)
        m = np.abs(xs - c) < w
        h[m] = np.maximum(h[m], 4 + hh * np.sqrt(np.clip(1 - ((xs[m] - c) / w) ** 2, 0, 1)))
    gaps = [(PAD[0], 380), (LZ[0], 260)]
    for gx, gw in gaps: h = np.where(np.abs(xs - gx) < gw, np.minimum(h, 2.0), h)
    return xs, h.astype(F32)

@lru_cache(2)
def shore_lights(seed=9):
    r = np.random.default_rng(seed); n = 520
    x = np.concatenate([r.uniform(-9000, 9000, 220), r.normal(3600, 700, 220), r.normal(-3500, 900, 80)]).astype(F32)
    z = (SHORE_Z - r.uniform(30, 2600, n)).astype(F32)
    y = r.uniform(1.5, 14, n).astype(F32)
    b = (r.power(0.3, n) * 0.85 + 0.15).astype(F32)
    warm = r.random(n) < 0.4
    return np.stack([x, y, z], 1), b, warm

# ---------------------------------------------------------------- palms (filled fronds)
def palm_layer(W, H, x, y, s, lean=0.2, seed=0, n_fronds=17):
    """alpha mask of a cabbage palm rooted at (x, y), height s px."""
    r = np.random.default_rng(seed); SS = 2
    m = np.zeros((H * SS, W * SS), np.uint8)
    pts = []
    for k in range(17):
        u = k / 16; pts.append((x + lean * s * u ** 1.8 + 3.0 * math.sin(u * 5 + seed), y - s * u))
    pts = np.array(pts)
    left, right = [], []
    for k in range(len(pts)):
        u = k / (len(pts) - 1); w = s * (0.034 - 0.012 * u)
        if k < len(pts) - 1: dx, dy = pts[k + 1] - pts[k]
        nx, ny = -dy, dx; ln = math.hypot(nx, ny) + 1e-6; nx, ny = nx / ln, ny / ln
        left.append(pts[k] + np.array([nx, ny]) * w / 2); right.append(pts[k] - np.array([nx, ny]) * w / 2)
    trunk = np.array(left + right[::-1])
    cv2.fillPoly(m, [np.round(trunk * SS * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    top = pts[-1]
    for k in range(n_fronds):
        ang = -math.pi / 2 + (k / (n_fronds - 1) - 0.5) * math.pi * 1.9 + r.normal(0, 0.1)
        L = s * r.uniform(0.26, 0.38); droop = r.uniform(0.35, 0.75)
        sp = []
        for j in range(22):
            u = j / 21
            px = top[0] + math.cos(ang) * L * u
            py = top[1] + math.sin(ang) * L * u * 0.8 + droop * L * u ** 2 * (0.4 + 0.6 * abs(math.cos(ang)))
            sp.append((px, py))
        sp = np.array(sp)
        # leaflet fan: width rises then tapers; jagged edge
        L1, L2 = [], []
        for j in range(len(sp)):
            u = j / (len(sp) - 1)
            w = s * 0.075 * math.sin(math.pi * min(1.0, u * 1.15)) ** 0.8 * (0.75 + 0.25 * ((j % 2) * 2 - 1) * (u > 0.15))
            if j < len(sp) - 1: dx, dy = sp[j + 1] - sp[j]
            nx, ny = -dy, dx; ln = math.hypot(nx, ny) + 1e-6; nx, ny = nx / ln, ny / ln
            L1.append(sp[j] + np.array([nx, ny]) * w * 0.5); L2.append(sp[j] - np.array([nx, ny]) * w * 0.5)
        fr = np.array(L1 + L2[::-1])
        cv2.fillPoly(m, [np.round(fr * SS * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
        # notches between leaflets: thin dark cuts across the fan
        for j in range(4, len(sp) - 2, 2):
            a0 = sp[j]; a1 = np.array(L1[j]) + (np.array(L1[j]) - a0) * 0.05; a2 = np.array(L2[j]) + (np.array(L2[j]) - a0) * 0.05
            for q in (a1, a2):
                cv2.line(m, tuple(np.round(a0 * SS * 16 + (q - a0) * SS * 16 * 0.35).astype(int)), tuple(np.round(q * SS * 16).astype(int)), 0, max(1, int(s * 0.004 * SS)), cv2.LINE_AA, shift=4)
    # old frond skirt under the crown
    for k in range(9):
        ang = math.pi / 2 + (k - 4) * 0.22
        L = s * 0.09
        a = top + np.array([0, s * 0.01]); b = a + np.array([math.cos(ang) * L * 0.6, math.sin(ang) * L])
        cv2.line(m, tuple(np.round(a * SS * 16).astype(int)), tuple(np.round(b * SS * 16).astype(int)), 255, max(1, int(s * 0.012 * SS)), cv2.LINE_AA, shift=4)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(F32) / 255

def palm(img, x, y, s, lean=0.2, seed=0, col=(0, 0, 0), backlight=None):
    a = palm_layer(img.shape[1], img.shape[0], x, y, s, lean, seed)
    img *= (1 - a)[..., None]; img += a[..., None] * np.asarray(col, F32)
    if backlight is not None:                                  # light wrapping around the edges when the sky is bright
        e = np.clip(cv2.GaussianBlur(a, (0, 0), 1.5) - a * 0.85, 0, 1)
        img += e[..., None] * np.asarray(backlight, F32)

# ---------------------------------------------------------------- water
def ripple_reflect(above, hy, W, H, t, strength=1.0, dark=0.42, blur=1.2, zoom=1.0):
    """mirror the picture above the shoreline into the water: ripples, darkening, vertical smear."""
    out = np.zeros((H, W, 3), F32); n = H - hy
    if n <= 0 or hy <= 2: return out
    ys = np.arange(n, dtype=F32)
    tex = K.noise_tex(256, 21, 4, 0.5)
    d = (ys / max(1, n))[:, None]
    persp = 1.0 / (0.05 + d * 3.0)                                       # far water: fine ripples; near: big
    amp = (0.4 + 7.0 * d) * strength * min(3.0, zoom ** 0.5)
    nx = K.tile_sample(tex, W, n, 0.5, 1.8, t * 25, t * 11) - 0.5
    ny = K.tile_sample(tex, W, n, 0.3, 2.8, 40 + t * 13, 7 + t * 37) - 0.5
    xx = np.arange(W, dtype=F32)[None, :] + nx * amp * 2.0
    sy = np.clip((hy - 1 - ys)[:, None] + ny * amp * 1.4 - 0.0 * persp, 0, hy - 1)
    ref = cv2.remap(above, xx.astype(F32), sy.astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    ref = cv2.GaussianBlur(ref, (0, 0), sigmaX=blur, sigmaY=blur * 4.0)
    out[hy:] = ref * (dark * (1 - 0.4 * d))[..., None]
    return out

def heat_shimmer(img, t, amt, y0, y1):
    """telephoto heat shimmer over 7 km of humid air: a gentle wobble of the band around the horizon."""
    if amt <= 0: return img
    H, W = img.shape[:2]; y0, y1 = int(max(0, y0)), int(min(H, y1))
    if y1 - y0 < 4: return img
    tex = K.noise_tex(256, 77, 4, 0.55); n = y1 - y0
    dx = (K.tile_sample(tex, W, n, 0.9, 0.5, t * 45, t * 20) - 0.5) * amt
    dy = (K.tile_sample(tex, W, n, 0.7, 0.4, 60 + t * 33, 9 + t * 28) - 0.5) * amt * 0.6
    gx, gy = np.meshgrid(np.arange(W, dtype=F32), np.arange(y0, y1, dtype=F32))
    img[y0:y1] = cv2.remap(img, gx + dx, gy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return img

# ---------------------------------------------------------------- the frame
def render(t, W, H, st):
    """st: zoom, aim, pan, dawn, launch_t, arcs=(up, down), arc_gain, lz_booster, lz_smoke, lz_floods, sats, vapor,
    floods, palms, shimmer, haze, cast (extra light on the scene), exposure tweak."""
    zoom = st.get("zoom", 1.0); cam = cam_for(W, H, zoom, st.get("aim"), st.get("pan", (0, 0)))
    dawn = st.get("dawn", 0.0)
    hy = int(round(cam.p1(np.array([cam.eye[0] + cam.f[0] * 1e6, 0, -1e6], F32))[1]))
    hy = int(round(cam.p1(np.array([PAD[0], 0.0, SHORE_Z], F32))[1]))
    hy = max(0, min(H, hy))
    S = cam.px_per_m(-PAD[2])                                           # px per metre at the pads
    # ---------------- sky
    top = lerp(K.SKY_TOP, np.array([0.012, 0.028, 0.075], F32), dawn)
    hor = lerp(np.array([0.010, 0.012, 0.020], F32), np.array([0.36, 0.20, 0.11], F32), dawn)
    img = K.vgrad(W, H, top, hor, y0=-0.2, y1=max(0.05, hy / H))
    yy = np.arange(H, dtype=F32)[:, None, None]
    img += np.exp(-((yy - hy) / (H * 0.05 * max(1, zoom ** 0.3))) ** 2) * np.array([0.022, 0.020, 0.024], F32) * (1 - dawn)
    if dawn > 0:
        xx = np.arange(W, dtype=F32)[None, :, None]
        sx, _, _ = cam.p1(np.array([9000.0, 0, -6000.0], F32))
        r = np.sqrt(((xx - sx) / (W * 0.6)) ** 2 + ((yy - hy) / (H * 0.4)) ** 2)
        img += np.exp(-r * 2.0) * np.array([0.55, 0.28, 0.11], F32) * dawn ** 1.6 * (yy < hy)
    ct = K.noise_tex(512, 4, 6, 0.58); ct = np.clip((ct - 0.5) * 2.4, 0, 1)
    if hy > 2:
        cl = K.tile_sample(ct, W, hy, 0.5 / zoom, 1.6 / zoom, 300 + t * 1.6 + cam.f[0] * 900, 90 - cam.f[1] * 900)
        prof = np.clip(np.linspace(0, 1, hy, dtype=F32) * 1.3 - 0.1, 0, 1)[:, None]
        a = cl * prof * 0.5
        ccol = lerp(np.array([0.020, 0.023, 0.034], F32), np.array([0.62, 0.36, 0.27], F32), dawn)
        img[:hy] = img[:hy] * (1 - a[..., None]) + a[..., None] * ccol
    sky_only = img.copy()
    # ---------------- far shore: treeline + lights + pads
    xs, th = treeline()
    sx_, sy_, sz_ = cam.project(np.stack([xs, np.zeros_like(xs), np.full_like(xs, SHORE_Z)], 1))
    tx, ty, tz = cam.project(np.stack([xs, th, np.full_like(xs, SHORE_Z)], 1))
    ok = (sx_ > -20) & (sx_ < W + 20)
    if ok.sum() > 2:
        poly = np.concatenate([np.stack([tx[ok], ty[ok]], 1), np.array([[tx[ok][-1], H + 5], [tx[ok][0], H + 5]])])
        land_a = K.poly_mask(W, H, poly, ss=2)
        land_col = lerp(np.array([0.0012, 0.0013, 0.0018], F32), np.array([0.012, 0.010, 0.013], F32), dawn)
        img = img * (1 - land_a[..., None]) + land_col * land_a[..., None]
    P, B, warm = shore_lights()
    lx, ly, lz = cam.project(P)
    vis = (lx > -5) & (lx < W + 5) & (ly > -5) & (ly < H + 5)
    for x, y, b, w, z in zip(lx[vis], ly[vis], B[vis], warm[vis], lz[vis]):
        col = np.array([1.0, 0.88, 0.70], F32) if w else np.array([0.88, 0.92, 1.0], F32)
        K.splat(img, x, y, 0.8 + 0.25 * min(6.0, zoom), col, b * 0.32 * (1 - 0.8 * dawn))
    floods = st.get("floods", 1.0)
    # launch complex
    pad_parts(img, cam, t, st, floods)
    light = np.zeros(3, F32)
    lt = st.get("launch_t", None)
    if lt is not None and lt >= -0.6:
        light = launch(img, cam, t, lt, st)
    arcs = st.get("arcs")
    if arcs: draw_arcs(img, cam, arcs, st.get("arc_gain", 1.0))
    lz_parts(img, cam, t, st)
    if st.get("descent_u") is not None: descent_dot(img, cam, t, st["descent_u"], st.get("descent_burn", 0.0))
    if st.get("sats", 0) > 0: sat_pass(img, t, st["sats"], hy)
    # ---------------- haze over distance (long lens), shimmer
    haze = st.get("haze", 0.0)
    if haze > 0:
        img += np.exp(-((yy - hy) / (H * 0.18)) ** 2) * np.array([0.01, 0.011, 0.014], F32) * haze
    if st.get("shimmer", 0) > 0: img = heat_shimmer(img, t, st["shimmer"] * min(6.0, zoom), hy - H * 0.35, hy + 4)
    # ---------------- stars after the shore (not reflected: the water is too rough for faint points)
    stars_layer = np.zeros_like(img)
    K.stars(stars_layer, t, gain=0.42 * (1 - dawn) ** 2 * (1 - 0.8 * clamp(float(light.max()) * 3)), n=2400, horizon=hy, scale=zoom ** 0.25, density=0.8)
    # ---------------- water
    above = img[:hy].copy()
    ref = ripple_reflect(above, hy, W, H, t, strength=st.get("ripple", 1.0) * (1.6 if zoom > 4 else 1.0), dark=0.26 + 0.25 * dawn, zoom=zoom)
    wcol = lerp(np.array([0.0010, 0.0013, 0.0024], F32), np.array([0.035, 0.028, 0.032], F32), dawn)
    img[hy:] = wcol + ref[hy:]
    img[:hy] += stars_layer[:hy]
    if light.max() > 0:
        lx_, ly_, _ = cam.p1(st.get("_flame_pos", PAD))
        img += K.glow_layer(W, H, [(lx_, (ly_ + hy) / 2, H * 0.55, light, 0.10), (lx_, hy, H * 0.25, light, 0.22)], 0.125)
        # 'darkness lost the sky': the whole sky and the water lit by it
        yy_ = np.arange(H, dtype=F32)[:, None, None]; xx_ = np.arange(W, dtype=F32)[None, :, None]
        d = np.sqrt(((xx_ - lx_) / W) ** 2 + ((yy_ - ly_) / H) ** 2)
        img += light[None, None] * (0.10 * np.exp(-d * 2.2) + 0.03) * st.get("sky_light", 1.0)
    # ---------------- palms
    if st.get("palms"):
        S2 = min(W, H); vert = H > W
        bl = light * 0.6 + K.MOON * 0.004
        for (fx, fy, fs, lean, seed) in st["palms"]:
            palm(img, W * fx, H * fy, S2 * fs, lean, seed, backlight=bl)
    return img, cam, hy

def pad_parts(img, cam, t, st, floods):
    """masts, strongback, the floodlit vehicle (until liftoff), floodlight beams, vapor."""
    H, W = img.shape[:2]
    lt = st.get("launch_t", None)
    on_pad = lt is None or lt < 0.15
    dark = np.array([0.006, 0.0062, 0.0068], F32)
    tops = []
    for (dx, dz) in [(-62, -50), (62, -50), (62, 58), (-62, 58)]:
        b = PAD + np.array([dx, 0, dz], F32)
        x0, y0, z0 = cam.p1(b); x1, y1, z1 = cam.p1(b + np.array([0, 96, 0], F32))
        w = max(1.0, 2.0 * cam.px_per_m(z0))
        m = np.zeros((H, W), np.uint8)
        cv2.line(m, (int(x0 * 8), int(y0 * 8)), (int(x1 * 8), int(y1 * 8)), 255, max(1, int(w)), cv2.LINE_AA, shift=3)
        a = m.astype(F32) / 255
        img *= (1 - a * 0.95)[..., None]; img += a[..., None] * (dark + K.FLOOD * 0.02 * floods)
        on = 0.5 + 0.5 * math.sin(t * math.pi + dx * 0.1)
        K.splat(img, x1, y1 - 1, 1.2 + 0.2 * cam.px_per_m(z1), (1.0, 0.05, 0.02), 0.25 * on ** 6 + 0.02)
        tops.append((x1, y1))
    # catenary wires between the masts (lightning protection)
    m = np.zeros((H, W), np.uint8)
    for a_, b_ in [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]:
        A, B = tops[a_], tops[b_]; pts = []
        for k in range(21):
            u = k / 20; pts.append((lerp(A[0], B[0], u), lerp(A[1], B[1], u) + math.sin(u * math.pi) * abs(B[0] - A[0]) * 0.06))
        cv2.polylines(m, [np.round(np.array(pts) * 8).astype(np.int32)], False, 255, 1, cv2.LINE_AA, shift=3)
    a = m.astype(F32) / 255 * 0.5
    img *= (1 - a)[..., None]
    if on_pad:
        lights = K.Lights(ambient=K.MOON * 0.015)
        for p, c in [((-34, 2, 48), 1.0), ((30, 2, 44), 0.7), ((0, 2, -60), 0.25)]:
            lights.point(PAD + np.array(p, F32), K.FLOOD * 2.6 * c * floods, 34)
        lights.dir((0.6, -0.5, -0.6), K.MOON * 0.05)
        rk = K.Mesh().extend(K.stage1_mesh(seg=40)).extend(K.transform(K.upper_mesh(40), None, (0, K.L_S1 + K.L_INT, 0)))
        K.draw_mesh(img, cam, K.transform(rk, None, PAD + np.array([0, 2.6, 0], F32)), lights, ss=4)
        # strongback (dark lattice tower beside the rocket)
        sb = K.box(PAD + np.array([-6.5, 36, 0], F32), (3.4, 72, 3.4), np.array([0.05, 0.05, 0.055], F32))
        K.draw_mesh(img, cam, sb, lights, ss=4)
        if st.get("vapor", 0) > 0: vapor(img, cam, t, st["vapor"], floods)
    # floodlight beams through the humid air + the lamps themselves
    beams = []
    for (dx, dz, ax) in [(-40, 55, 0.25), (38, 50, -0.2), (-70, 20, 0.5), (70, 25, -0.45)]:
        b = PAD + np.array([dx, 4, dz], F32)
        x0, y0, z0 = cam.p1(b); x1, y1, z1 = cam.p1(b + np.array([-dx * 1.4 + ax * 80, 260, -dz * 0.8], F32))
        K.splat(img, x0, y0, 1.6 + 0.35 * cam.px_per_m(z0), K.FLOOD, 2.2 * floods)
        beams.append((x0, y0, x1, y1, cam.px_per_m(z0)))
    if floods > 0:
        bl = np.zeros((H // 2, W // 2), F32)
        for x0, y0, x1, y1, s in beams:
            w0 = max(1.0, 0.8 * s / 2); w1 = max(3.0, 7 * s / 2)
            poly = np.array([[x0 / 2 - w0, y0 / 2], [x0 / 2 + w0, y0 / 2], [x1 / 2 + w1, y1 / 2], [x1 / 2 - w1, y1 / 2]])
            cv2.fillConvexPoly(bl, np.round(poly * 16).astype(np.int32), 1.0, cv2.LINE_AA, shift=4)
        bl = cv2.GaussianBlur(bl, (0, 0), 6)
        img += cv2.resize(bl, (W, H))[..., None] * K.FLOOD * 0.006 * floods * (1 if on_pad else 0.5)
        x, y, z = cam.p1(PAD + np.array([0, 30, 20], F32))
        img += K.glow_layer(W, H, [(x, y, 80 * cam.px_per_m(z), K.FLOOD, 0.012 * floods)], 0.25)

def vapor(img, cam, t, amt, floods):
    """LOX boil-off curling off the vehicle and drifting downwind (right), lit by the floodlights."""
    for i in range(22):
        per = 7.0; age = (t * 0.7 + i * per / 22) % per
        src = 28 + (i % 3) * 18                      # vents up the vehicle
        p = PAD + np.array([2.2 + age * 6.5, src + age * 1.4 - age ** 1.4 * 0.8, 1.5], F32)
        x, y, z = cam.p1(p); r = (2.5 + age * 3.2) * cam.px_per_m(z)
        a = 0.30 * amt * sstep(0, 0.6, age) * (1 - age / per) ** 1.5
        K.smoke_sprite(img, x, y, r, a, K.FLOOD * 0.10 * floods + K.MOON * 0.002, i, rot=i * 47)

def launch(img, cam, t, lt, st):
    """ignition, liftoff, climb: the flame, the steam cloud at the pad, light thrown on everything."""
    H, W = img.shape[:2]
    pos = ascent_pos(max(0.0, lt)); st["_flame_pos"] = pos
    ign = sstep(-0.5, 0.3, lt)
    pxm = cam.px_per_m(-PAD[2])
    # the steam/exhaust cloud boiling out of the flame trench to both sides, low and wide, lit from inside
    burn_light = math.exp(-max(0.0, lt - 2.5) * 0.2)
    for i in range(90):
        born = -0.45 + (i // 2) * 0.09
        if lt < born: continue
        age = lt - born
        side = 1 if i % 2 else -1
        rr = np.random.default_rng(i + 7).random(4)
        out = (18 + 210 * (1 - math.exp(-age * (0.32 + 0.2 * rr[0])))) * (0.6 + 0.4 * rr[1])
        rise = age * (2.0 + 3.0 * rr[2]) + max(0.0, age - 3) ** 1.3 * 2.5
        p = PAD + np.array([side * out + age * 4.0, 5 + rise + rr[3] * 10, (rr[0] - 0.5) * 70], F32)
        x, y, z = cam.p1(p); r = (14 + 30 * (1 - math.exp(-age * 0.3)) + rr[1] * 10) * cam.px_per_m(z)
        a = 0.7 * min(1.0, age * 2.0)
        near = math.exp(-out / 120.0)
        K.smoke_sprite(img, x, y, r, a, K.FLAME_W * (0.20 * burn_light * (0.4 + near) + 0.012) + K.MOON * 0.004, i, rot=i * 33,
                       emissive=K.FLAME_W * 0.9 * burn_light * near * math.exp(-age * 0.25))
    x, y, z = cam.p1(pos)
    alt = float(pos[1])
    g = ign
    # flame + exhaust column (in dense air the plume trails as a glowing column)
    tail = []
    for k in range(48):
        u = k / 47; s_back = max(0.0, lt - u * min(lt, 4.0 + lt * 0.15))
        tail.append(cam.p1(ascent_pos(s_back))[:2])
    if lt > 0.2:
        K.polyline_glow(img, tail, K.FLAME_W * 0.9, width=max(2.0, 3.0 * pxm), glow=4.0 + 3 * pxm, gain=0.8 * ign, glow_gain=0.6)
    K.splat(img, x, y, 2.5 + 5.0 * pxm ** 0.5, K.FLAME_HOT, 14.0 * g)
    img += K.glow_layer(W, H, [(x, y, 70 + 40 * pxm, K.FLAME_W, 0.08 * g), (x, y, 380 + 90 * pxm, K.FLAME_W, 0.016 * g)], 0.25)
    cast = g * (1.0 + 1.6 * math.exp(-max(0.0, lt) * 0.5)) * math.exp(-max(0.0, alt) / 9000.0)
    return K.FLAME_W * cast * 0.35

def draw_arcs(img, cam, arcs, gain=1.0):
    up, down = arcs if isinstance(arcs, (tuple, list)) else (arcs, arcs)
    H, W = img.shape[:2]
    if up > 0:
        pts = []
        for k in range(260):
            s = 175.0 * (k / 259) * up
            x, y, z = cam.p1(ascent_pos(s))
            if z < 1: break
            pts.append((x, y))
            if y < -H * 0.3 or x > W * 1.3: break
        if len(pts) > 1:
            K.polyline_glow(img, pts, K.FLAME_W * 1.05, width=2.0, glow=5.0, gain=1.7 * gain, glow_gain=0.55)
    if down > 0:
        pts = [cam.p1(descent_path((k / 199) * down))[:2] for k in range(200)]
        if len(pts) > 1:
            K.polyline_glow(img, pts, K.FLAME_O * 1.15, width=2.4, glow=6.5, gain=1.9 * gain, glow_gain=0.75)
            if down >= 0.999:
                x, y, z = cam.p1(LZ); K.splat(img, x, y, 4.0, K.FLAME_O2, 5.0 * gain)

def descent_dot(img, cam, t, u, burn):
    x, y, z = cam.p1(descent_path(u))
    K.splat(img, x, y, 2.0 + 4 * burn, K.FLAME_O2 if burn > 0 else K.WHITE, 0.4 + 8 * burn)

def lz_parts(img, cam, t, st):
    lzf = st.get("lz_floods", 0.7)
    for dx, dz in [(-90, 40), (90, 40), (0, -95)]:
        x, y, z = cam.p1(LZ + np.array([dx, 14, dz], F32))
        K.splat(img, x, y, 1.3 + 0.3 * cam.px_per_m(z), K.FLOOD, 1.0 * lzf)
    if not st.get("lz_booster"): return
    lights = K.Lights(ambient=K.MOON * 0.02)
    lights.point(LZ + np.array([-60, 10, 50], F32), K.FLOOD * 7 * lzf, 60).point(LZ + np.array([60, 10, 50], F32), K.FLOOD * 5 * lzf, 60)
    b = K.stage1_mesh(seg=32, soot=0.7, legs=1.0, fins=1.0)
    K.draw_mesh(img, cam, K.transform(b, None, LZ + np.array([0, 2.9, 0], F32)), lights, ss=4)
    sm = st.get("lz_smoke", 30.0)
    for i in range(20):
        age = sm + i * 0.8
        p = LZ + np.array([8 + age * 3.0 + (i % 4) * 8, 6 + age * 1.3 + (i % 3) * 6, (i % 5 - 2) * 10], F32)
        x, y, z = cam.p1(p); r = (16 + age * 2.0) * cam.px_per_m(z)
        K.smoke_sprite(img, x, y, r, 0.3 * math.exp(-age / 45), K.FLOOD * 0.08 * lzf, i + 3, rot=i * 50)

def sat_pass(img, t, u, hy):
    """eleven faint points of light crossing the sky in a line (the ones that kept going)."""
    H, W = img.shape[:2]
    for k in range(11):
        v = u * 1.25 - k * 0.022
        if v < 0 or v > 1: continue
        x = W * (0.08 + 0.84 * v); y = hy * (0.18 + 0.10 * math.sin(v * math.pi)) + k * 1.2
        K.splat(img, x, y, 1.3, K.WHITE, 1.4)

def render_mirror(t, W, H, st, pitch=-6.0, calm=0.5):
    """looking DOWN at the water from the shore: the far treeline at the top of the frame and, below it, the sky reflected
    in near-calm water. The reflection is rendered properly (a mirrored camera looking UP, flipped), so the whole of
    the arcs shows in the water even though the camera never looks up."""
    yaw = st.get("pan", (0.0, 0.0))[0]
    st_dn = dict(st); st_dn["pan"] = (yaw, pitch); st_dn["ripple"] = 0.0
    img, cam, hy = render(t, W, H, st_dn)
    st_up = dict(st); st_up["pan"] = (yaw, -pitch)
    up, cam_u, hy_u = render(t, W, H, st_up)
    ref = up[::-1].copy()                                         # mirror: the up-view's horizon lands on hy
    if hy >= H - 2: return img, cam, hy
    n = H - hy
    tex = K.noise_tex(256, 21, 4, 0.5)
    ys = np.arange(n, dtype=F32); d = (ys / max(1, n))[:, None]
    amp = (0.3 + 5.0 * d) * calm
    nx = K.tile_sample(tex, W, n, 0.5, 1.8, t * 25, t * 11) - 0.5
    ny = K.tile_sample(tex, W, n, 0.3, 2.8, 40 + t * 13, 7 + t * 37) - 0.5
    gx = np.arange(W, dtype=F32)[None, :] + nx * amp * 2.0
    gy = (hy + ys)[:, None] + ny * amp * 1.2
    r = cv2.remap(ref, gx.astype(F32), gy.astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    r = cv2.GaussianBlur(r, (0, 0), sigmaX=0.8, sigmaY=2.5)
    dawn = st.get("dawn", 0.0)
    wcol = lerp(np.array([0.0010, 0.0013, 0.0024], F32), np.array([0.035, 0.028, 0.032], F32), dawn)
    fres = (0.30 + 0.25 * (1 - d))[..., None]                       # grazing reflections are stronger near the horizon
    img[hy:] = wcol + r * fres
    return img, cam, hy
