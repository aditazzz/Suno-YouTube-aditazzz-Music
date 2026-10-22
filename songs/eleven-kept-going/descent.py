"""After the Turn the camera only looks DOWN: the booster flipping in the dark, the boostback burn, grid fins and
cold gas, the long way down to a small light on the coast, the entry burn (the first orange), falling faster than it
should, the landing burn on one engine, four legs unfolding into the dark."""
import math
import numpy as np, cv2
import ekg as K
import rt, ground as G
from ekg import F32, sstep, clamp, lerp, ease_io, ease_out

def booster_R(pitch_deg, yaw_deg=0.0, roll=0.0):
    """orientation: pitch 0 = engines down (upright), 90 = lying along +x with the engines toward -x (pointing west)."""
    R = K.rot_axis((0, 0, 1), math.radians(pitch_deg))
    if yaw_deg: R = K.rot_axis((0, 1, 0), math.radians(yaw_deg)) @ R
    if roll: R = R @ K.rot_axis((0, 1, 0), roll)
    return R

def draw_booster(img, cam, B, R, lights, legs=0.0, fins=0.0, soot=0.0, eng=0.0, eng_col=K.FLAME_W, center_only=False, ss=2):
    return rt.draw_vehicle(img, cam, B, R, lights, stage="booster", legs=legs, fins=fins, soot=soot, eng_glow=eng, eng_col=eng_col, center_only=center_only, ss=ss)

def engine_points(B, R, which="three"):
    """nozzle-exit positions (world) of the firing engines."""
    pos = rt.ENG_POS
    ids = [0] if which == "center" else ([0, 1, 5] if which == "three" else list(range(9)))
    return [np.asarray(B, F32) + R @ np.array([pos[i][0], -1.25, pos[i][1]], F32) for i in ids]

def burn(img, cam, B, R, t, gain, col, which="three", length=60.0, radius=1.3, expand=1.0, plume_scale=1.0, thin_air=0.0, occ=None, diamonds=0.0):
    """engine flames along -axis, plus (high up) a huge faint plume."""
    H, W = img.shape[:2]
    ax = R @ np.array([0, 1, 0], F32); d = -ax
    for k, p in enumerate(engine_points(B, R, which)):
        K.flame(img, cam, p, d, length=length, radius=radius, col=col, gain=gain, flick=0.8, t=t, expand=expand, occ=occ, seed=k, diamonds=diamonds)
    if thin_air > 0:
        pts = []
        base = np.asarray(B, F32) - ax * 2
        for i in range(12):
            u = (i + 0.5) / 12
            p = base + d * (30 + 600 * u ** 1.2) * plume_scale
            x, y, z = cam.p1(p)
            if z < 1: continue
            r = (15 + 380 * u) * plume_scale * cam.px_per_m(z)
            pts.append((x, y, r, col, 0.05 * gain * thin_air * (1 - u) ** 1.3 / max(1.0, r * 0.003)))
        if pts: img += K.glow_layer(W, H, pts, 0.125)

def cold_gas(img, cam, B, R, t, t0, side=1, n=6):
    """nitrogen thruster puffs near the top of the interstage."""
    if t < t0: return
    ax = R @ np.array([0, 1, 0], F32)
    top = np.asarray(B, F32) + ax * (K.L_S1 + K.L_INT - 1.0)
    out = R @ np.array([side * 1.0, 0, 0.3], F32)
    for i in range(n):
        age = (t - t0) - i * 0.05
        if age < 0 or age > 1.6: continue
        p = top + out * (K.R_BODY + age * 9.0) + ax * (age * 0.8)
        x, y, z = cam.p1(p)
        if z < 0.5: continue
        r = (0.6 + age * 3.2) * cam.px_per_m(z)
        K.smoke_sprite(img, x, y, r, 0.55 * (1 - age / 1.6) ** 1.3, np.array([0.06, 0.07, 0.09], F32), i + 40, rot=i * 60,
                       emissive=np.array([0.02, 0.025, 0.035], F32) * (1 - age / 1.6))

def lights_for(B, R, burn_gain=0.0, burn_col=K.FLAME_W, moon=1.0, ground_glow=0.0):
    L = K.Lights(ambient=K.MOON * 0.004)
    L.dir(-G.moon_local(), K.MOON * K.MOON_E * moon)
    if burn_gain > 0:
        ax = R @ np.array([0, 1, 0], F32)
        L.lamp(np.asarray(B, F32) - ax * 8, burn_col * 150 * burn_gain, 4.0)
    if ground_glow > 0: L.dir((0, 1, 0), np.array([1.0, 0.9, 0.75], F32) * ground_glow)
    return L

def ground_bg(cam, W, H, t, p, scale=0.5):
    """the Earth below at reduced resolution (it's soft at night), upscaled."""
    w, h = max(16, int(W * scale)), max(16, int(H * scale))
    c2 = K.Cam(cam.eye, cam.eye + cam.f, w, h, fov=1.0)
    c2.r, c2.u, c2.f = cam.r, cam.u, cam.f; c2.fpx = cam.fpx * scale; c2.sx, c2.sy = cam.sx * scale, cam.sy * scale
    img, hit = G.view(c2, w, h, t, p)
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
    return img

# ---------------------------------------------------------------- shots
CAPE = np.array([0.0, 0.0, 0.0], F32)

def cam_at(B, off, look, W, H, fov, roll=0.0):
    """camera at B + off, looking at a point `look` of the way from the booster toward Landing Zone 1
    (0 = straight at the booster, 1e-3 = ~100 m past it toward the coast ...)."""
    B = np.asarray(B, F32); eye = B + np.asarray(off, F32)
    tgt = B + (CAPE - B) * look
    return K.Cam(eye, tgt, W, H, fov=fov, up=(0, 1, 0), roll=roll)

def vframe(mk, W, H, A, Bp, cy=0.45):
    """9:16 frames keep the 16:9 pixel scale, so a subject off to the side of a wide composition falls out of a tall one.
    mk(roll) -> Cam. Rebuild the camera rolled so A sits straight above Bp (looking down at the Earth any roll is
    natural), then shift the lens so their midpoint is centred."""
    cam = mk(0.0)
    if H <= W: return cam
    xa, ya, za = cam.p1(A); xb, yb, zb = cam.p1(Bp)
    if za <= 0 or zb <= 0: return cam
    th = math.atan2(xb - xa, yb - ya)
    best = None
    for r in (th, -th, th + math.pi, -th + math.pi):
        c = mk(r); xa, ya, za = c.p1(A); xb, yb, zb = c.p1(Bp)
        err = abs(xb - xa) + (0.0 if yb > ya else 1e6)
        if best is None or err < best[0]: best = (err, r)
    cam = mk(best[1])
    xa, ya, _ = cam.p1(A); xb, yb, _ = cam.p1(Bp)
    cam.sx += W / 2 - (xa + xb) / 2; cam.sy += H * cy - (ya + yb) / 2
    return cam

def hcenter(cam, P, W, H, keep=0.25):
    """9:16 only: shift the lens so P moves toward the centre line (keep = how much of its offset survives)."""
    if H <= W: return cam
    x, y, z = cam.p1(P)
    if z > 0: cam.sx += (1 - keep) * (W / 2 - x)
    return cam

def flip(t, W, H, u, st):
    """the booster alone in the dark, swinging end over end; the night Earth below with the coast far off. (117.65-118.58)"""
    B = np.array([88000.0, 140000.0, -6000.0], F32)
    pitch = lerp(-25, 95, ease_io(u))                                     # engines swinging up and over toward the east
    R = booster_R(pitch, 0, 0.2)
    mid = B + R @ np.array([0, 22, 0], F32)
    cam = cam_at(mid, np.array([-40.0, 78.0, 70.0], F32), 0.00025, W, H, st.get("fov", 52))
    img = ground_bg(cam, W, H, t, dict(stars=0.6, clouds=0.12, cloud_scale=1 / 90.0, moon=1.0), 0.45)
    L = lights_for(B, R)
    draw_booster(img, cam, B, R, L, ss=2)
    cold_gas(img, cam, B, R, t, st.get("puff_t", 117.7), side=1)
    return img, cam

def boostback(t, W, H, u, st):
    """three engines light and push it back toward the coast: from above and to the side, the plume trailing east,
    the lights of the Cape far below and ahead. close=1: tight on the engines, looking down along the body."""
    x = lerp(86000, 70000, u); y = lerp(141000, 139000, u)
    B = np.array([x, y, -6000.0], F32)
    R = booster_R(95 + 4 * math.sin(u * 2.0), 0, 0.3)                    # lying on its side, engines east, nose west
    g = sstep(0.0, 0.025, u) * (1 + 0.08 * math.sin(t * 30)) if not st.get("close") else (1 + 0.08 * math.sin(t * 30))
    if st.get("close"):
        cam = cam_at(B, np.array([18.0 + 6 * u, 34.0, 30.0 - 8 * u], F32), 0.00055, W, H, st.get("fov", 54), roll=0.05)
    else:
        cam = cam_at(B, np.array([-60.0 + 20 * u, 150.0, 120.0], F32), 0.0011, W, H, st.get("fov", 50))
    cam = hcenter(cam, B + R @ np.array([0, 12.0 if st.get("close") else 22.0, 0], F32), W, H, keep=0.35 if st.get("close") else 0.15)
    img = ground_bg(cam, W, H, t, dict(stars=0.5, clouds=0.12, cloud_scale=1 / 90.0, moon=1.0), 0.5)
    L = lights_for(B, R, g * 0.7, K.FLAME_W)
    occ = draw_booster(img, cam, B, R, L, eng=g)
    burn(img, cam, B, R, t, 1.4 * g, K.FLAME_W, "three", length=70, radius=1.4, expand=2.0, plume_scale=1.6, thin_air=1.0, occ=occ)
    return img, cam

def fins_close(t, W, H, u, st):
    """grid fins swing out; cold gas turns it slow. Beside and above the interstage, looking down the length of the
    booster to the Earth: the four lattice fins opening like hands."""
    B = np.array([62000.0, 128000.0, -5000.0], F32)
    R = booster_R(-6 + 5 * math.sin(u * 1.4), 0, 0.15 + u * 0.35)         # tail-first, nearly upright (engines down)
    top = B + R @ np.array([0, K.L_S1 + K.L_INT, 0], F32)
    ang = math.radians(lerp(20, 48, u))
    eye = top + np.array([math.cos(ang) * 13.0, 5.5 + 1.0 * u, math.sin(ang) * 13.0], F32)
    cam = K.Cam(eye, top + np.array([0, -11.0, 0], F32), W, H, fov=st.get("fov", 54), up=(0, 1, 0))
    img = ground_bg(cam, W, H, t, dict(stars=0.0, clouds=0.12, cloud_scale=1 / 90.0, moon=1.0), 0.45)
    L = lights_for(B, R, moon=1.2)
    fins = ease_io(clamp(st.get("fin_u", u) / 0.9))
    draw_booster(img, cam, B, R, L, fins=fins, ss=2)
    for k, t0 in enumerate(st.get("puffs", [])): cold_gas(img, cam, B, R, t, t0, side=1 if k % 2 else -1)
    return img, cam

def long_way(t, W, H, u, st):
    """high above and behind: the booster small, the whole coast of Florida far below."""
    B = np.array([lerp(58000, 44000, u), lerp(124000, 106000, u), -4500.0], F32)
    R = booster_R(-8, 0, 0.6 + u)
    cam = cam_at(B + np.array([0, 20, 0], F32), np.array([150.0 - 25 * u, 260.0 - 40 * u, 140.0], F32), 0.0011 + 0.0003 * u, W, H, st.get("fov", 50))
    img = ground_bg(cam, W, H, t, dict(stars=0.3, clouds=0.12, cloud_scale=1 / 90.0, moon=1.1), 0.5)
    L = lights_for(B, R, moon=1.3)
    draw_booster(img, cam, B, R, L, fins=1.0, ss=3)
    return img, cam

def lerpv(a, b, u): return np.asarray(a, F32) * (1 - u) + np.asarray(b, F32) * u

def aiming(t, W, H, u, st):
    """it knows where it is going: from above the booster, the line of its future path drawn down to one light."""
    B = np.array([lerp(36000, 27000, u), lerp(96000, 80000, u), -3000.0], F32)
    R = booster_R(-6, 0, 1.2 + u)
    mk = lambda roll: cam_at(B, np.array([-35.0, 120.0, 46.0], F32), lerp(0.0012, 0.0016, u), W, H, st.get("fov", 52 if W >= H else 58), roll=roll)
    cam = vframe(mk, W, H, B + R @ np.array([0, 30.0, 0], F32), np.array([0.0, 0.0, 0.0], F32), cy=0.38)
    img = ground_bg(cam, W, H, t, dict(stars=0.0, clouds=0.14, cloud_scale=1 / 70.0, moon=1.1), 0.5)
    L = lights_for(B, R, moon=1.3)
    draw_booster(img, cam, B, R, L, fins=1.0, ss=2)
    lk = st.get("line", 0.0); lock = st.get("lock", 0.0)
    S = min(W, H) / 1080
    if lk > 0:
        pts = []
        n = 120
        for k in range(n):
            v = k / (n - 1) * lk
            p = np.array([B[0] * (1 - v) ** 1.35, B[1] * (1 - v) ** 1.9, B[2] * (1 - v)], F32)
            x, y, z = cam.p1(p)
            if z > 1: pts.append((x, y))
        if len(pts) > 1:
            for i in range(0, len(pts) - 1, 2):
                K.polyline_glow(img, pts[i:i + 2], K.WHITE, width=1.6 * S, glow=3.0 * S, gain=0.9, glow_gain=0.35)
    x, y, z = cam.p1((0, 0, 0))
    if lock > 0 and z > 0:
        r = lerp(min(W, H) * 0.12, min(W, H) * 0.028, ease_out(lock))
        op = sstep(0, 0.3, lock)
        circ = [(x + math.cos(a) * r, y + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, 90)]
        K.polyline_glow(img, circ, K.WHITE, width=1.4 * S, glow=2.5 * S, gain=0.9 * op, glow_gain=0.3)
        for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
            K.polyline_glow(img, [(x + math.cos(a) * r * 1.35, y + math.sin(a) * r * 1.35), (x + math.cos(a) * r * 0.7, y + math.sin(a) * r * 0.7)],
                            K.WHITE, width=1.4 * S, glow=2 * S, gain=0.9 * op, glow_gain=0.3)
    return img, cam

def entry(t, W, H, u, st):
    """ENTRY BURN: the first orange. Three engines into the thickening air; the sky around it turns orange."""
    B = np.array([lerp(22000, 15000, u), lerp(70000, 42000, u), -2500.0], F32)
    R = booster_R(-3, 0, 2.0 + u * 0.6)
    cam = cam_at(B + np.array([0, 18, 0], F32), np.array([-26.0 + 6 * u, 70.0, 34.0], F32), 0.00035, W, H, st.get("fov", 58))
    img = ground_bg(cam, W, H, t, dict(stars=0.0, clouds=0.18, cloud_scale=1 / 60.0, moon=1.0), 0.45)
    g = sstep(0, 0.03, u) * (1 - sstep(0.93, 1.0, u)) * (1 + 0.12 * math.sin(t * 37))
    sky = st.get("sky", 0.0)
    if sky > 0:                                    # the thin air lit orange around the burn
        H_, W_ = img.shape[:2]
        x, y, z = cam.p1(B - np.array([0, 30, 0], F32))
        img += K.glow_layer(W_, H_, [(x, y, min(W_, H_) * 0.9, K.FLAME_O, 0.25 * sky * g), (x, y, min(W_, H_) * 0.35, K.FLAME_O2, 0.35 * sky * g)], 0.125)
    L = lights_for(B, R, g * 1.2, K.FLAME_O)
    occ = draw_booster(img, cam, B, R, L, fins=1.0, eng=g, eng_col=K.FLAME_O)
    burn(img, cam, B, R, t, 2.2 * g, K.FLAME_O, "three", length=90, radius=1.6, expand=3.0, plume_scale=1.0, thin_air=0.8, occ=occ)
    return img, cam

def falling(t, W, H, u, st):
    """falling faster than something that size should ever fall: the coast swelling below, heat glowing at its base,
    and at the end the cloud deck rushing up past it."""
    alt = lerp(38000, 4200, ease_io(u) * 0.6 + u * 0.4)
    B = np.array([lerp(12000, 1500, u), alt, -1500.0 * (1 - u)], F32)
    R = booster_R(-2, 0, 2.6 + u * 0.8)
    cam = cam_at(B + np.array([0, 20, 0], F32), np.array([-20.0, 72.0, 26.0], F32), 0.0011, W, H, st.get("fov", 62))
    img = ground_bg(cam, W, H, t, dict(stars=0.0, clouds=0.35, cloud_alt=2800, cloud_scale=1 / 30.0, moon=1.0), 0.45)
    L = lights_for(B, R, 0.12, K.FLAME_O)
    draw_booster(img, cam, B, R, L, fins=1.0, soot=0.35 * u)
    H_, W_ = img.shape[:2]
    x, y, z = cam.p1(B - np.array([0, 2, 0], F32))
    img += K.glow_layer(W_, H_, [(x, y, 26 * cam.px_per_m(z), K.FLAME_O, 0.05 + 0.05 * u)], 0.25)
    return img, cam

def speed_streaks(img, t, u, amt):
    if amt <= 0: return
    H, W = img.shape[:2]; r = np.random.default_rng(7); S = H / 1080
    lay = np.zeros((H, W, 3), F32)
    for i in range(46):
        x = r.uniform(0, W); sp_ = r.uniform(0.7, 1.6)
        y = (r.uniform(0, 1) * H * 1.6 - (t * 1400 * S * sp_) % (H * 1.6)) % (H * 1.6) - H * 0.3
        L = r.uniform(80, 260) * S
        g = r.uniform(0.006, 0.02) * amt
        K.polyline_glow(lay, [(x, y), (x + r.uniform(-6, 6) * S, y + L)], np.array([0.6, 0.65, 0.75], F32), width=r.uniform(4, 16) * S, glow=8 * S, gain=g, glow_gain=1.0, ss=1)
    img += lay

def landing_burn(t, W, H, u, st):
    """then, landing burn: one engine. Above and beside the falling booster, looking down along it to the lit circle
    of the landing zone; the flame pointing at it."""
    alt = lerp(4200, 900, u)
    B = np.array([lerp(1500, 200, u), alt, -200.0 * (1 - u)], F32)
    R = booster_R(-1.5, 0, 3.4 + u * 0.3)
    mid = B + np.array([0, 22, 0], F32)
    eye = mid + np.array([-34.0, 34.0, 40.0], F32)
    tgt = mid + (np.array([0, 0, 0], F32) - mid) * lerp(0.035, 0.05, u)
    mk = lambda roll: K.Cam(eye, tgt, W, H, fov=st.get("fov", 58), up=(0, 1, 0), roll=roll)
    cam = vframe(mk, W, H, B + R @ np.array([0, 26.0, 0], F32), np.array([0.0, 0.0, 0.0], F32), cy=0.42)
    img = ground_bg(cam, W, H, t, dict(stars=0.0, clouds=0.0, moon=1.0, lz=1.0), 0.6)
    g = sstep(0, 0.04, u) * (1 + 0.1 * math.sin(t * 41)) if st.get("burn_ramp", True) else (1 + 0.1 * math.sin(t * 41))
    L = lights_for(B, R, g * 1.3, K.FLAME_O)
    legs = st.get("legs", 0.0)
    occ = draw_booster(img, cam, B, R, L, fins=1.0, legs=legs, soot=0.45, eng=g, eng_col=K.FLAME_O, center_only=True)
    burn(img, cam, B, R, t, 2.0 * g, K.FLAME_O, "center", length=40, radius=0.9, expand=1.4, occ=occ, diamonds=0.5)
    return img, cam

def legs_close(t, W, H, u, st):
    """'Four legs unfolding / Into the dark': close beside the lower body, looking down past the engine at the lit
    circle far below; the four legs swing out and down around the flame."""
    alt = lerp(900.0, 420.0, u)
    B = np.array([lerp(200, 60, u), alt, -30.0 * (1 - u)], F32)
    R = booster_R(-0.8, 0, 3.7 + u * 0.2)
    eye = B + np.array([7.5, 15.0 + 2 * u, 9.0], F32)
    tgt = B + np.array([-1.0, -10.0, -1.5], F32)
    cam = K.Cam(eye, tgt, W, H, fov=st.get("fov", 62), up=(0, 1, 0))
    img = ground_bg(cam, W, H, t, dict(stars=0.0, clouds=0.0, moon=1.0, lz=1.0), 0.6)
    g = 1 + 0.1 * math.sin(t * 41)
    L = lights_for(B, R, g * 1.3, K.FLAME_O)
    occ = draw_booster(img, cam, B, R, L, fins=1.0, legs=st.get("legs", 0.0), soot=0.5, eng=g, eng_col=K.FLAME_O, center_only=True, ss=2)
    burn(img, cam, B, R, t, 2.0 * g, K.FLAME_O, "center", length=40, radius=0.9, expand=1.4, occ=occ, diamonds=0.5)
    return img, cam
