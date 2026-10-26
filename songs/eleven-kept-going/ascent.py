"""High above the Cape, looking UP at the climbing stack: the plume blooming in the thin air, main engine cutoff,
the first stage falling away, the second stage lighting and carrying on; then the ladder of spent stages
("you wanted the sky, you left the ladder behind") and the light splitting into eleven."""
import math
import numpy as np, cv2
import ekg as K
import rt
from ekg import F32, sstep, clamp, lerp, ease_io, ease_out

def sky_up(W, H, t, cam, alt_km=40.0, glow=0.0):
    """black upper-atmosphere sky with stars; a faint airglow low (we look up, so mostly black)."""
    img = K.vgrad(W, H, np.array([0.0008, 0.0010, 0.0022], F32), np.array([0.0030, 0.0040, 0.0085], F32) * max(0.2, 1 - alt_km / 120))
    K.stars(img, t, gain=0.55 + 0.3 * clamp(alt_km / 80), n=4200, ox=float(cam.f[0]) * 0.4, oy=-float(cam.f[1]) * 0.4, density=0.55, twinkle=0.12)
    return img

def plume(img, cam, nozzle, direction, t, scale=1.0, gain=1.0, col=K.FLAME_W, alt_km=40.0):
    """high-altitude plume: a hot core and a huge, faint, expanding bell of exhaust (the 'jellyfish')."""
    H, W = img.shape[:2]; d = K.nrm(direction)
    K.flame(img, cam, nozzle, d, length=40 * scale, radius=2.2 * scale, col=col, gain=1.4 * gain, flick=0.6, t=t, n=18, expand=1.0 + alt_km / 30)
    pts = []
    for i in range(14):
        u = (i + 0.5) / 14
        p = np.asarray(nozzle, F32) + d * (60 + 900 * u ** 1.3) * scale
        x, y, z = cam.p1(p)
        if z < 1: continue
        r = (20 + 420 * u ** 1.1 * (0.5 + alt_km / 60)) * scale * cam.px_per_m(z)
        pts.append((x, y, r, col * (0.7 + 0.3 * (1 - u)), 0.035 * gain * (1 - u) ** 1.2 / max(1.0, r * 0.004)))
    if pts: img += K.glow_layer(W, H, pts, 0.125)

def render_sep(t, W, H, st):
    """st: u (0..1 progress through the separation shot). Below and behind the stack, looking up along it: the first
    stage's plume blooming in the thin air, MECO, the pushers, the first stage falling back past the camera, the second
    stage lighting its long blue-white flame and carrying on."""
    u = st["u"]
    axis = K.nrm((0.10, 1.0, -0.16))
    R = K._rot_to(axis)
    base = np.array([0, 0, 0], F32)
    meco = st.get("meco", 0.25); sep = st.get("sep", 0.42); mvac = st.get("mvac", 0.62)
    # the camera rides below the stack, drifting back as the first stage falls toward it
    eye = np.array([-22.0, -34.0, 30.0], F32) + np.array([-4.0, -14.0, 6.0], F32) * u
    tgt = base + axis * lerp(26.0, 44.0, ease_io(u))
    cam = K.Cam(eye, tgt, W, H, fov=st.get("fov", 54), roll=st.get("roll", 0.10))
    img = sky_up(W, H, t, cam, 70)
    L = K.Lights(ambient=K.MOON * 0.01).dir((0.6, -0.2, -0.7), K.MOON * K.MOON_E)
    g1 = 1.0 if u < meco else max(0.0, 1 - (u - meco) * 30)
    # first stage drifts back (down-screen, toward us) after separation, slowly starting to tumble
    ds = max(0.0, u - sep)
    b1 = base - axis * (ds * 34) ** 1.3 + np.array([ds * 6, 0, ds * 5], F32)
    R1 = K.rot_axis((1, 0, 0.3), ds * 0.5) @ R
    L1 = K.Lights(ambient=K.MOON * 0.01).dir((0.6, -0.2, -0.7), K.MOON * K.MOON_E)
    if g1 > 0: L1.lamp(b1 - axis * 6, K.FLAME_W * 150 * g1, 4.0)
    occ1 = rt.draw_vehicle(img, cam, b1, R1, L1, stage="booster", eng_glow=g1 * 0.8)
    if g1 > 0: plume(img, cam, b1 - axis * 1.3, -(R1 @ np.array([0, 1, 0], F32)), t, 1.0, g1, alt_km=60)
    # second stage + fairing continue up
    b2 = base + axis * (K.L_S1 + K.L_INT) + axis * max(0.0, u - sep) * 18
    m2 = clamp((u - mvac) / 0.06)
    L2 = K.Lights(ambient=K.MOON * 0.01).dir((0.6, -0.2, -0.7), K.MOON * K.MOON_E)
    if m2 > 0: L2.lamp(b2 - axis * 4, K.FLAME_W * 100 * m2, 3.0)
    occ2 = rt.draw_vehicle(img, cam, b2, R, L2, stage="upper", mvac_glow=m2)
    if m2 > 0:
        K.flame(img, cam, b2 - axis * 3.0, -axis, length=90, radius=1.3, col=np.array([0.80, 0.88, 1.0], F32), gain=1.3 * m2, flick=0.3, t=t,
                expand=2.6, occ=occ2)
    # separation puffs (pneumatic pushers + cold gas)
    if sep - 0.02 < u < sep + 0.25:
        k = (u - sep + 0.02) / 0.27
        for i in range(10):
            ang = i * 2 * math.pi / 10
            p = base + axis * (K.L_S1 + K.L_INT) + np.array([math.cos(ang) * (2 + k * 10), -k * 4, math.sin(ang) * (2 + k * 10)], F32)
            x, y, z = cam.p1(p)
            K.smoke_sprite(img, x, y, (1.5 + k * 6) * cam.px_per_m(z), 0.35 * (1 - k), K.MOON * 0.05, i)
    return img, cam

# ---------------------------------------------------------------- the ladder
STAGES = [  # (length, radius, fins, nozzle count) generic historical first stages (no specific vehicles)
    (21, 1.2, 4, 1), (28, 1.5, 4, 1), (42, 5.0, 4, 5), (24, 1.2, 3, 1), (30, 1.8, 0, 2), (36, 2.0, 4, 1), (26, 1.6, 0, 1),
    (33, 1.9, 4, 1), (40, 2.4, 0, 1), (29, 1.5, 3, 1), (45, 4.2, 0, 4), (34, 1.8, 0, 1)]

def ghost_stage(img, cam, p, axis, L, r, fins, col, op, w=1.6):
    """a white line-drawing of a spent stage (outline only), tumbling."""
    a = K.nrm(axis); side = K.nrm(np.cross(a, cam.f)); pts = []
    for (u, s) in [(0, -1), (1, -1), (1, 1), (0, 1), (0, -1)]:
        pts.append(cam.p1(p + a * (u * L) + side * s * r)[:2])
    K.polyline_glow(img, pts, col, width=w, glow=4.0, gain=op, glow_gain=0.4)
    # nose / skirt detail + fins
    K.polyline_glow(img, [cam.p1(p + a * (L * 0.92) + side * -r)[:2], cam.p1(p + a * (L * 0.92) + side * r)[:2]], col, width=w * 0.7, glow=2, gain=op * 0.6, glow_gain=0.3)
    if fins:
        for s in (-1, 1):
            K.polyline_glow(img, [cam.p1(p + side * s * r)[:2], cam.p1(p - a * r * 1.2 + side * s * r * 2.6)[:2], cam.p1(p + a * r * 2.5 + side * s * r)[:2]],
                            col, width=w * 0.8, glow=2, gain=op * 0.8, glow_gain=0.3)

def render_ladder(t, W, H, st):
    """st: u (0..1 over 83.2-114.0), split (0..1 the light becoming eleven). Camera looks up a column of night."""
    u = st["u"]
    cam = K.Cam((0, 0, 0), (0, 1000, -260), W, H, fov=st.get("fov", 52), roll=0.0)
    img = sky_up(W, H, t, cam, 90)
    vert = H > W
    # the second stage: a climbing point of light at the top of the frame, getting smaller
    top_y = H * (0.16 if not vert else 0.12)
    x_s = W * 0.5 + math.sin(u * 2.0) * W * 0.02
    y_s = top_y + H * 0.05 * (1 - u)
    split = st.get("split", 0.0)
    if split <= 0:
        K.splat(img, x_s, y_s, 3.0, K.FLAME_W, 7.0)
        img += K.glow_layer(W, H, [(x_s, y_s, 60, K.FLAME_W, 0.06)], 0.25)
    else:
        for k in range(11):
            ang = -math.pi / 2 + (k - 5) * 0.21
            rr = split * H * 0.10 * (0.6 + 0.4 * ((k * 7) % 11) / 11)
            K.splat(img, x_s + math.cos(ang) * rr, y_s + math.sin(ang) * rr * 0.8, 1.8, K.WHITE, 3.5 * (1 - 0.3 * split))
    # the ladder: two rails of light from the bottom up to the climbing point; rungs below it fall away
    rail_gap = W * (0.06 if not vert else 0.11)
    lad = st.get("ladder", 0.0)                             # 0 none .. 1 fully drawn
    fall = st.get("fall", 0.0)                              # 0..1 how much of the ladder has dropped away
    if lad > 0:
        n_r = 12
        for k in range(n_r):
            v = (k + 0.5) / n_r                             # 0 bottom .. 1 top
            yk = H * 1.02 - (H * 1.02 - y_s - H * 0.05) * v
            gone = clamp((fall * n_r - (n_r - 1 - k)) / 1.0)  # bottom rungs leave first
            dy = (gone ** 2) * H * 0.9
            op = lad * (1 - gone) * (0.35 + 0.65 * v)
            if op <= 0.01: continue
            tilt = gone * (0.8 if k % 2 else -0.8)
            xa, xb = x_s - rail_gap / 2, x_s + rail_gap / 2
            ya = yk + dy - math.sin(tilt) * rail_gap / 2; yb = yk + dy + math.sin(tilt) * rail_gap / 2
            K.polyline_glow(img, [(xa, ya), (xb, yb)], K.FLAME_W * 0.9, width=2.0, glow=5, gain=op, glow_gain=0.5)
        top_rail = y_s + H * 0.03
        bot = H * 1.02 - (H * 1.02 - top_rail) * clamp(fall * 1.05)
        for sx in (-1, 1):
            K.polyline_glow(img, [(x_s + sx * rail_gap / 2, top_rail), (x_s + sx * rail_gap / 2, max(top_rail, bot))], K.FLAME_W * 0.8,
                            width=1.6, glow=4, gain=lad * 0.8, glow_gain=0.4)
    # ghost stages tumbling down past the camera (the expendable past)
    ghosts = st.get("ghosts", 0.0)
    if ghosts > 0:
        for i, (Ls, rs, fins, nz) in enumerate(STAGES):
            ph = (u * 3.4 + i * 0.29) % 1.0
            if (u * 3.4 + i * 0.29) < 1.0 and u < 0.05: continue
            sc = H / 1080
            x = W * (0.12 + 0.76 * ((i * 0.37) % 1.0)); y = -H * 0.25 + ph * H * 1.6
            ang = i * 1.3 + ph * (1.5 if i % 2 else -1.8)
            a = np.array([math.cos(ang), math.sin(ang)])
            size = (0.55 + 0.6 * ((i * 0.53) % 1.0)) * sc * (0.9 + ph * 0.7)
            Lp = Ls * 6.5 * size; rp = rs * 6.5 * size
            pts = []
            for (uu, s) in [(0, -1), (1, -1), (1, 1), (0, 1), (0, -1)]:
                pts.append((x + a[0] * uu * Lp - a[1] * s * rp, y + a[1] * uu * Lp + a[0] * s * rp))
            op = ghosts * 0.45 * math.sin(ph * math.pi) ** 0.7
            K.polyline_glow(img, pts, np.array([0.8, 0.85, 1.0], F32), width=1.3, glow=3.0, gain=op, glow_gain=0.35)
            if fins:
                for s in (-1, 1):
                    f0 = (x - a[1] * s * rp, y + a[0] * s * rp)
                    f1 = (x - a[0] * rp * 1.4 - a[1] * s * rp * 2.6, y - a[1] * rp * 1.4 + a[0] * s * rp * 2.6)
                    f2 = (x + a[0] * rp * 2.6 - a[1] * s * rp, y + a[1] * rp * 2.6 + a[0] * s * rp)
                    K.polyline_glow(img, [f0, f1, f2], np.array([0.8, 0.85, 1.0], F32), width=1.1, glow=2, gain=op * 0.8, glow_gain=0.3)
    return img, cam


def render_leaving(t, W, H, st):
    """from beside the spent first stage, looking up past it: the second stage leaving, a bright point with the faint
    disc of its vacuum plume around it, shrinking among the stars; the booster's dark body down the left of the frame."""
    u = st["u"]
    axis1 = K.nrm((0.06, 1.0, -0.10))
    R1 = K.rot_axis((1, 0, 0.2), 0.05 + 0.18 * u) @ K._rot_to(axis1)
    top = np.array([0, 0, 0], F32)
    ax = R1 @ np.array([0, 1, 0], F32)
    side = K.nrm(np.array([-0.6, 0.0, 0.7], F32))                     # the moonlit side of the body
    perp = K.nrm(np.cross(side, np.array([0, 1, 0], F32)))
    eye = top - ax * 9.0 + side * 6.5
    dist = lerp(180.0, 3200.0, u ** 1.3)
    up_dir = K.nrm(side * 0.38 + perp * 0.12 + np.array([0, 1.0, 0], F32))
    s2 = eye + up_dir * dist
    look = eye + K.nrm(up_dir - side * 0.30) * 100.0
    cam = K.Cam(eye, look, W, H, fov=st.get("fov", 62), up=tuple(-perp), roll=0.0)
    img = sky_up(W, H, t, cam, 120)
    L = K.Lights(ambient=K.MOON * 0.004).dir((0.6, -0.3, -0.7), K.MOON * K.MOON_E * 1.2)
    B1 = top - ax * (K.L_S1 + K.L_INT)
    cov, dep = rt.draw_vehicle(img, cam, B1, R1, L, stage="booster", ss=2)
    x, y, z = cam.p1(s2)
    if z > 1:
        pr = cam.px_per_m(z)
        lay = np.zeros_like(img)
        lay += K.glow_layer(W, H, [(x, y, max(10.0, 700 * pr), np.array([0.70, 0.82, 1.0], F32), 0.035),
                                   (x, y, max(4.0, 90 * pr), np.array([0.80, 0.88, 1.0], F32), 0.10)], 0.25)
        K.splat(lay, x, y, max(1.6, 3.0 * pr), K.FLAME_HOT, 6.0)
        img += lay * (1 - cov)[..., None]
    return img, cam
