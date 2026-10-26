"""At the pad: low angles up the floodlit vehicle (the instrumental intro), the folded legs and grid fins, the nine
engines, the eleven satellites seen through an x-ray fairing, ignition and liftoff from up close.
Camera always looks UP (the rule until the Turn).

Lighting is a night-photography setup made of physical lamps (irradiance I/d^2, the same law everywhere): a hard key
from the front-left floods, a strong rim from behind-right, almost no fill, light shafts in the humid air."""
import math
from functools import lru_cache
import numpy as np, cv2
import ekg as K
import rt
from ekg import F32, sstep, clamp, lerp, ease_io

STEEL = np.array([0.035, 0.035, 0.038], F32)
BASE_Y = 3.2                                 # rocket base height above the ground (on the launch mount)
AIM = np.array([0.0, 30.0, 0.0], F32)
# the light rig is placed relative to the camera's bearing (cheated per shot, like a film set), so every angle gets the
# same look: hard key low from the camera's left, a strong rim from behind-right, a whisper of fill.
# entries: (position, intensity rgb, beam half-width deg)
RIG = [(-70.0, 95.0, 5.0, 7600.0, 16.0),       # key  (bearing offset deg, distance m, height m, intensity, beam)
       (158.0, 95.0, 9.0, 11000.0, 13.0),      # rim
       (-150.0, 100.0, 6.0, 2200.0, 14.0),     # kicker on the left edge
       (35.0, 90.0, 3.0, 260.0, 20.0)]         # fill
LAMPS = []
def set_rig(eye):
    global LAMPS
    phi = math.degrees(math.atan2(float(eye[0]), float(eye[2])))
    LAMPS = []
    for off, dist, h, I, beam in RIG:
        a = math.radians(phi + off)
        LAMPS.append(((math.sin(a) * dist, h, math.cos(a) * dist), K.FLOOD * I, beam))
    return LAMPS
set_rig((0.0, 0.0, 1.0))

def spot(lamp, P):
    p, I, beam = lamp
    p = np.asarray(p, F32); a = K.nrm(AIM - p)
    v = np.asarray(P, F32) - p
    n = np.linalg.norm(v, axis=-1) + 1e-6
    c = np.clip((v @ a) / n, -1, 1)
    return 0.03 + 0.97 * np.exp(-(np.arccos(c) / math.radians(beam)) ** 2)

def floods_lights(floods=1.0, flame=0.0, flame_col=K.FLAME_W, at=(0, 25, 0)):
    L = K.Lights(ambient=K.MOON * 0.006)
    for lamp in LAMPS:
        L.lamp(lamp[0], lamp[1] * floods * float(spot(lamp, at)), 3.0)
    L.dir((0.45, -0.75, -0.5), K.MOON * K.MOON_E * 0.6)
    if flame > 0: L.lamp((0, 0.5, 0), flame_col * 70.0 * flame, 3.0)
    return L

def strongback_lines(t):
    """the lattice tower beside the vehicle: a list of 3-D segments (posts + braces)."""
    x0, z0, w = -6.6, 0.0, 3.0; h = 70.0
    posts = [(x0 - w / 2, z0 - w / 2), (x0 + w / 2, z0 - w / 2), (x0 + w / 2, z0 + w / 2), (x0 - w / 2, z0 + w / 2)]
    segs = []
    for (px, pz) in posts: segs.append(((px, 0, pz), (px, h, pz), 0.35))
    y = 0.0; k = 0
    while y < h - 3:
        y1 = y + 3.0
        for i in range(4):
            a, b = posts[i], posts[(i + 1) % 4]
            segs.append(((a[0], y1, a[1]), (b[0], y1, b[1]), 0.16))
            if k % 2 == 0: segs.append(((a[0], y, a[1]), (b[0], y1, b[1]), 0.10))
            else: segs.append(((b[0], y, b[1]), (a[0], y1, a[1]), 0.10))
        y = y1; k += 1
    for ya in (22.0, 44.0, 60.0):                                   # arms reaching to the vehicle
        segs.append(((x0 + w / 2, ya, z0), (-K.R_BODY - 0.2, ya, z0), 0.4))
    return segs

def draw_segments(img, cam, segs, alb, floods=1.0, lit=True):
    """steel members as anti-aliased strokes, each shaded by the lamps (a thin cylinder catches light from any side
    perpendicular to it): dark against the sky, with bright edges where the key and rim lights hit.
    Each stroke is drawn in its own small bounding box (cheap at any resolution)."""
    H, W = img.shape[:2]
    for a, b, wm in segs:
        a = np.asarray(a, F32); b = np.asarray(b, F32)
        xa, ya, za = cam.p1(a); xb, yb, zb = cam.p1(b)
        if za < 0.3 or zb < 0.3: continue
        w = max(1.0, wm * cam.px_per_m((za + zb) / 2) * 0.5)
        x0 = int(math.floor(min(xa, xb) - w - 2)); x1 = int(math.ceil(max(xa, xb) + w + 2))
        y0 = int(math.floor(min(ya, yb) - w - 2)); y1 = int(math.ceil(max(ya, yb) + w + 2))
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        if X1 <= X0 or Y1 <= Y0: continue
        ax = K.nrm(b - a); mid = (a + b) / 2
        E = K.MOON * K.MOON_E * 0.3
        if lit:
            for lamp in LAMPS:
                p = np.asarray(lamp[0], F32); dv = p - mid; d2 = float(dv @ dv)
                l = dv / math.sqrt(d2); perp = math.sqrt(max(0.0, 1 - float(l @ ax) ** 2))
                E = E + lamp[1] * floods * float(spot(lamp, mid)) / (d2 + 9) * perp * 0.6
        col = np.asarray(alb, F32) * E
        m = np.zeros((Y1 - Y0, X1 - X0), np.uint8)
        cv2.line(m, (int((xa - X0) * 8), int((ya - Y0) * 8)), (int((xb - X0) * 8), int((yb - Y0) * 8)), 255, max(1, int(round(w))), cv2.LINE_AA, shift=3)
        A = (m.astype(F32) / 255)[..., None]
        roi = img[Y0:Y1, X0:X1]
        roi *= (1 - A); roi += A * col
    return None

def sky(W, H, cam, t, glow=0.0, glow_col=K.FLAME_W, stars_gain=0.5, floods=1.0):
    """night sky seen looking up: deep blue-black, darker toward the zenith, the floods lighting the humid air low down."""
    up = float(cam.f[1])
    img = K.vgrad(W, H, K.SKY_TOP * (1.0 - 0.3 * up), K.SKY_HOR * (1.6 - 0.8 * up))
    K.stars(img, t, gain=stars_gain, n=4200, ox=float(cam.f[0]) * 0.3 + float(cam.f[2]) * 0.2, oy=-up * 0.5, density=0.55)
    # the floods' glow in the air around the vehicle
    x, y, z = cam.p1(AIM)
    if z > 1:
        img += K.glow_layer(W, H, [(x, y, min(W, H) * 0.9, K.FLOOD, 0.010 * floods), (x, y, min(W, H) * 0.4, K.FLOOD, 0.010 * floods)], 0.125)
    if glow > 0:                                   # the flame lights the humid air low down, not the whole sky
        yy = np.linspace(0, 1, H, dtype=F32)[:, None, None]
        img += glow * glow_col * 0.016 * np.clip((yy - 0.35) / 0.65, 0, 1) ** 1.5
    return img

@lru_cache(1)
def _concrete():
    n = 1024; nz = cv2.resize(K.noise_tex(512, 51, 6, 0.6), (n, n), interpolation=cv2.INTER_CUBIC)
    nz2 = cv2.resize(K.noise_tex(256, 52, 5, 0.6), (n, n), interpolation=cv2.INTER_CUBIC)
    a = (0.20 + 0.08 * nz + 0.05 * nz2).astype(F32)
    y, x = np.mgrid[0:n, 0:n]
    a[((x % 128) < 2) | ((y % 128) < 2)] *= 0.6                    # expansion joints every 8 m
    return a

def ground(img, cam, floods, flame=0.0, flame_col=K.FLAME_W, t=0.0):
    """the concrete apron (ray/plane), lit by the floods' spill and the flame; only where the camera sees it."""
    H, W = img.shape[:2]
    ys_, xs_ = np.mgrid[0:H, 0:W].astype(F32)
    D = (cam.f[None, None] * cam.fpx + cam.r[None, None] * (xs_ - W / 2 - cam.sx)[..., None] + cam.u[None, None] * (H / 2 + cam.sy - ys_)[..., None])
    D /= np.linalg.norm(D, axis=2, keepdims=True)
    dn = D[..., 1]; hit = dn < -1e-4
    if not hit.any(): return None
    s = np.where(hit, -cam.eye[1] / np.where(hit, dn, -1), 0)
    px = cam.eye[0] + D[..., 0] * s; pz = cam.eye[2] + D[..., 2] * s
    alb = _concrete(); n = alb.shape[0]
    a = cv2.remap(alb, ((px / 8.0 * 128) % n).astype(F32), ((pz / 8.0 * 128) % n).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    E = np.zeros((H, W, 3), F32) + K.MOON[None, None] * K.MOON_E * 0.9
    P = np.stack([px, np.zeros_like(px), pz], -1)
    for lamp in LAMPS:
        lp = np.asarray(lamp[0], F32)
        d2 = (lp[0] - px) ** 2 + (lp[2] - pz) ** 2 + lp[1] ** 2
        E += (lamp[1] * floods)[None, None] * (lp[1] / np.sqrt(d2) / d2 * spot(lamp, P) * 3.0)[..., None]
    if flame > 0:
        d2 = px ** 2 + pz ** 2 + 4.0
        E += (np.asarray(flame_col, F32) * 260.0 * flame)[None, None] * (2.0 / np.sqrt(d2) / d2)[..., None]
    col = a[..., None] * E
    hz = 1 - np.exp(-s / 900.0)
    col = col * (1 - hz[..., None] * 0.8) + K.SKY_HOR * 1.4 * hz[..., None]
    img[hit] = col[hit]
    return hit

def light_shafts(img, cam, floods, t):
    """the floods' beams in humid air: faint emitting cones from each lamp toward the vehicle (and past it)."""
    for i, lamp in enumerate(LAMPS[:3]):
        p = np.asarray(lamp[0], F32); d = K.nrm(AIM + np.array([0, 6 * math.sin(i * 2.1), 0], F32) - p)
        L = float(np.linalg.norm(AIM - p)) * 1.6
        K.flame_lowres(img, cam, p, d, L, 0.9, s=0.25, col=K.FLOOD, gain=0.010 * floods * (1.0 if i == 0 else 0.7), flick=0.0, t=t,
                       core_gain=0.0, expand=9.0, seed=i)

def lamp_head(img, cam, p, gain=1.0):
    """a flood lamp seen directly: a hot point, a soft halo and a faint horizontal streak."""
    x, y, z = cam.p1(p)
    if z < 0.5: return
    H, W = img.shape[:2]
    if not (-200 < x < W + 200 and -200 < y < H + 200): return
    K.splat(img, x, y, 1.5 + 0.35 * cam.px_per_m(z), K.FLOOD, 6.0 * gain)
    img += K.glow_layer(W, H, [(x, y, 40 + 3 * cam.px_per_m(z), K.FLOOD, 0.06 * gain)], 0.25)
    xs = np.arange(W, dtype=F32)
    row = np.exp(-np.abs(xs - x) / (W * 0.10)) * 0.02 * gain
    yi = int(round(y))
    if 2 <= yi < H - 2:
        img[yi - 1:yi + 2] += row[None, :, None] * K.FLOOD[None, None] * np.array([0.5, 1.0, 0.5], F32)[:, None, None]

def render(t, W, H, st):
    """st: eye, target, fov, roll, floods, vapor, legs, fins, ignite (0..1 ramp), lift (m above the mount), flame_t (s since
    ignition), whiteout (0..1), frost, xray (0..1: the fairing turns to glass and shows the payload), strongback, shafts, stars."""
    cam = K.Cam(st["eye"], st["target"], W, H, fov=st.get("fov", 50), roll=st.get("roll", 0.0))
    set_rig(st.get("rig_eye", st["eye"]))
    floods = st.get("floods", 1.0)
    ign = st.get("ignite", 0.0); ft = st.get("flame_t", -1.0); lift = st.get("lift", 0.0)
    img = sky(W, H, cam, t, glow=ign * 0.6, stars_gain=st.get("stars", 0.2), floods=floods)
    ground(img, cam, floods, ign, t=t)
    # the four lightning masts as dark lines against the sky, red beacons on top
    masts = [((-62, 0, -50), (-62, 96, -50), 1.8), ((62, 0, -50), (62, 96, -50), 1.8), ((62, 0, 58), (62, 96, 58), 1.8), ((-62, 0, 58), (-62, 96, 58), 1.8)]
    draw_segments(img, cam, masts, STEEL * 0.5, floods)
    for x_, z_ in [(-62, -50), (62, -50), (62, 58), (-62, 58)]:
        x, y, z = cam.p1((x_, 96, z_))
        if z > 0: K.splat(img, x, y - 2, 1.5, (1.0, 0.05, 0.02), 0.4 * (0.5 + 0.5 * math.sin(t * math.pi + x_)) ** 6 + 0.02)
    if st.get("shafts", 1.0) > 0: light_shafts(img, cam, floods * st.get("shafts", 1.0), t)
    L = floods_lights(floods, ign * (1 + 2 * st.get("whiteout", 0)))
    # launch mount: a dark steel table, its top edges catching the light
    mount = K.box((0, 1.6, 0), (9, 3.2, 9), np.array([0.07, 0.07, 0.075], F32))
    K.draw_mesh(img, cam, mount, L)
    if st.get("strongback", True):
        draw_segments(img, cam, strongback_lines(t), STEEL, floods)
    B = np.array([0, BASE_Y + 1.25 + lift, 0], F32)
    xr = st.get("xray", 0.0)
    if xr <= 0:
        rt.draw_vehicle(img, cam, B, None, L, stage="full", legs=st.get("legs", 0.0), fins=st.get("fins", 0.0),
                        frost=st.get("frost", 0.6), eng_glow=st.get("eng_glow", 0.0))
    else:
        xray_vehicle(img, cam, B, L, xr, st)
    if st.get("vapor", 0) > 0: vapor(img, cam, t, st["vapor"], floods, lift)
    if ign > 0 or ft >= 0: ignition(img, cam, t, ft, ign, lift, st)
    for p in st.get("lamps", [LAMPS[0][0], LAMPS[1][0]]): lamp_head(img, cam, p, floods)
    wo = st.get("whiteout", 0.0)
    if wo > 0: img = img * (1 - wo) + K.FLAME_HOT * 6.0 * wo
    return img, cam

def W_H(img): return img.shape[1], img.shape[0]

def xray_vehicle(img, cam, B, L, xr, st):
    """the vehicle with its fairing turned to glass: the eleven satellites stacked on their dispenser inside, a faint
    blueprint glow on the fairing's outline."""
    import orbit as O
    rt.draw_vehicle(img, cam, B, None, L, stage="full", legs=st.get("legs", 0.0), fins=st.get("fins", 0.0),
                    frost=st.get("frost", 0.6), fairing=False)
    top_s2 = B + np.array([0, K.L_S1 + K.L_INT + K.L_S2, 0], F32)
    PL = K.Lights(ambient=np.array([0.02, 0.024, 0.032], F32))
    PL.dir((-0.5, -0.3, -0.8), K.FLOOD * 0.9).dir((0.7, -0.2, 0.6), np.array([0.35, 0.45, 0.7], F32) * 0.5)
    pm = K.transform(O.payload_mesh(st.get("spread", 0.0)), K.rot_axis((0, 1, 0), st.get("spin", 0.0)), top_s2)
    k = clamp(xr)
    K.draw_mesh_wire(img, cam, pm, np.array([0.85, 0.92, 1.0], F32) * 0.55 * k, np.array([0.10, 0.14, 0.22], F32), fill_a=0.85 * k,
                     width=1.1 * min(W_H(img)) / 1080, lights=PL)
    shell = img.copy()
    cov, dep = rt.trace(shell, cam, [rt.fairing_part(B)], L, ss=2)
    k = clamp(xr)
    img *= 1.0; img[:] = shell * (1 - k) + img * k
    # outline: the edge of the fairing's coverage, glowing faintly white-blue
    e = np.abs(cv2.Sobel(cov, cv2.CV_32F, 1, 0, ksize=3)) + np.abs(cv2.Sobel(cov, cv2.CV_32F, 0, 1, ksize=3))
    e = np.clip(e, 0, 1)
    img += (e + cv2.GaussianBlur(e, (0, 0), 3) * 0.6)[..., None] * np.array([0.55, 0.7, 1.0], F32) * 0.35 * k
    img += cov[..., None] * np.array([0.5, 0.65, 1.0], F32) * 0.012 * k

def vapor(img, cam, t, amt, floods, lift=0.0):
    """LOX boil-off: white plumes curling off the vents and sliding down the side, drifting right, plus cold fog
    rolling off the mount. Lit by the floods (shaded toward the key lamp)."""
    key = np.asarray(LAMPS[0][0], F32)
    for i in range(34):
        per = 6.0; age = (t * 0.9 + i * per / 34) % per
        vent = [39.0, 40.5, 53.0][i % 3] + lift
        side = 1 if (i // 3) % 2 else -1
        p = np.array([side * (K.R_BODY + 0.3 + age * 1.5) + age * 1.9, vent - age * 1.3 + age ** 2 * 0.22, 0.8 + 0.3 * side], F32)
        x, y, z = cam.p1(p)
        if z < 0.5: continue
        r = (0.9 + age * 1.4) * cam.px_per_m(z)
        a = 0.30 * amt * sstep(0, 0.5, age) * (1 - age / per) ** 1.4
        E = K.MOON * K.MOON_E * 0.5
        for lamp in LAMPS: E = E + lamp[1] * floods * float(spot(lamp, p)) / (float(np.sum((np.asarray(lamp[0], F32) - p) ** 2)) + 9)
        kd = K.nrm(key - p); sd = np.array([float(kd @ cam.r), -float(kd @ cam.u)], F32); sd /= max(1e-3, float(np.linalg.norm(sd)))
        K.smoke_sprite(img, x, y, r, a, E * 0.22, i, rot=i * 41, col2=E * 0.05, ldir=sd)
    # cold fog pooling around the mount
    for i in range(16):
        per = 9.0; age = (t * 0.5 + i * per / 16) % per
        ang = i * 2.399
        p = np.array([math.cos(ang) * (4 + age * 2.2), 0.6 + age * 0.15, math.sin(ang) * (4 + age * 2.2)], F32)
        x, y, z = cam.p1(p)
        if z < 0.5: continue
        r = (2.5 + age * 1.2) * cam.px_per_m(z)
        a = 0.22 * amt * sstep(0, 1.0, age) * (1 - age / per)
        E = K.MOON * K.MOON_E * 0.5
        for lamp in LAMPS: E = E + lamp[1] * floods * float(spot(lamp, p)) / (float(np.sum((np.asarray(lamp[0], F32) - p) ** 2)) + 9)
        K.smoke_sprite(img, x, y, r, a, E * 0.18, i + 50, rot=i * 23, col2=E * 0.06, ldir=(0.0, -1.0))

def ignition(img, cam, t, ft, ign, lift, st):
    """nine engines lighting, the plume hammering the mount, steam boiling out of the trench."""
    H, W = img.shape[:2]
    y_exit = BASE_Y + 1.25 - 1.25 + lift
    pos = [(0, 0)] + [(1.25 * math.cos(k * math.pi / 4 + math.pi / 8), 1.25 * math.sin(k * math.pi / 4 + math.pi / 8)) for k in range(8)]
    order = [0, 1, 5, 3, 7, 2, 6, 4, 8]                       # the ignition ripple
    for j, k in enumerate(order):
        tk = ft - j * 0.06
        if tk < 0: continue
        g = sstep(0, 0.25, tk) * (1 + 0.15 * math.sin(t * 53 + k))
        px, pz = pos[k]
        K.flame(img, cam, (px, y_exit, pz), (0, -1, 0), length=6 + 10 * sstep(0, 0.6, tk) + lift * 0.3, radius=0.45,
                col=K.FLAME_W, gain=1.4 * g, flick=1.0, t=t, diamonds=0.8, seed=k)
    if ft > 0.25:
        # exhaust smashing into the trench and rolling out as steam, low along the ground, lit from inside
        for i in range(64):
            born = 0.25 + i * 0.05
            if ft < born: continue
            age = ft - born
            rr = np.random.default_rng(i + 31).random(5)
            side = 1 if i % 2 else -1
            dist = 5 + 55 * (1 - math.exp(-age * (0.55 + 0.35 * rr[0])))
            p = np.array([side * dist, 0.8 + age * (0.9 + 1.4 * rr[1]) + rr[2] * 2.5, (rr[3] - 0.5) * 26 + 4], F32)
            x, y, z = cam.p1(p)
            if z < 0.5: continue
            r = (2.5 + 7 * (1 - math.exp(-age * 0.45)) + rr[4] * 2.5) * cam.px_per_m(z)
            near = math.exp(-dist / 22)
            K.smoke_sprite(img, x, y, r, 0.36 * min(1, age * 2.0), K.FLAME_W * (0.05 + 0.28 * near) * ign, i, rot=i * 29,
                           emissive=K.FLAME_W * 0.8 * near * math.exp(-age * 0.45) * ign, col2=K.FLAME_W * 0.015 * ign, ldir=(0.0, 1.0))
    x, y, z = cam.p1((0, y_exit - 2, 0))
    if z > 0 and ign > 0:
        img += K.glow_layer(W, H, [(x, y, 14 * cam.px_per_m(z), K.FLAME_W, 0.30 * ign), (x, y, 45 * cam.px_per_m(z), K.FLAME_W, 0.010 * ign)], 0.25)
