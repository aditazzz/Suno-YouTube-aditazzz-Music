"""Landing Zone 1 up close: the floodlit concrete circle, the last few hundred metres on one engine, touchdown in a
burst of smoke, the booster standing upright in it, and its feet on the concrete."""
import math
from functools import lru_cache
import numpy as np, cv2
import ekg as K
import rt
from ekg import F32, sstep, clamp, lerp, ease_io, ease_out

PAD_R = 43.0                      # concrete circle radius (m)
TEX_M = 520.0                     # texture covers TEX_M x TEX_M metres centred on the pad
TEX_N = 2048
FLOODS = [(-150.0, 30.0, -120.0), (150.0, 30.0, -110.0), (140.0, 30.0, 140.0), (-145.0, 30.0, 130.0)]
FLOOD_I = 27000.0                 # on-axis radiant intensity of one flood tower (same law on the ground and on the vehicle)
FLOOD_AIM = np.array([0.0, 8.0, 0.0], F32)
FLOOD_BEAM = math.radians(14.0)   # beam half-width (gaussian); 4% spill outside
FLAME_I = 900.0                   # the landing-burn flame as a light (x burn gain)
MOON_E = K.MOON_E

def spot(f, px, py, pz):
    """beam factor of flood tower f toward points (px, py, pz) (arrays or floats)."""
    f = np.asarray(f, F32); a = FLOOD_AIM - f; a = a / np.linalg.norm(a)
    vx, vy, vz = px - f[0], py - f[1], pz - f[2]
    n = np.sqrt(vx * vx + vy * vy + vz * vz) + 1e-6
    c = np.clip((vx * a[0] + vy * a[1] + vz * a[2]) / n, -1, 1)
    th = np.arccos(c)
    return 0.015 + 0.985 * np.exp(-(th / FLOOD_BEAM) ** 2)

@lru_cache(2)
def pad_tex(scorch=0):
    """albedo (linear) of the pad area: concrete circle, painted ring, perimeter road, scrub, scorch."""
    n = TEX_N; m_per_px = TEX_M / n
    y, x = np.mgrid[0:n, 0:n].astype(F32); x = (x + 0.5) * m_per_px - TEX_M / 2; z = (y + 0.5) * m_per_px - TEX_M / 2
    r = np.sqrt(x * x + z * z)
    nz = K.noise_tex(512, 33, 6, 0.6); nz = cv2.resize(nz, (n, n), interpolation=cv2.INTER_CUBIC)
    nz2 = cv2.resize(K.noise_tex(256, 34, 5, 0.6), (n, n), interpolation=cv2.INTER_CUBIC)
    scrub = np.stack([0.046 + 0.03 * nz, 0.046 + 0.03 * nz, 0.040 + 0.02 * nz], 2) * (0.7 + 0.5 * nz2[..., None])
    alb = scrub.astype(F32)
    conc = (r < PAD_R)
    cc = np.array([0.36, 0.355, 0.34], F32) * (0.85 + 0.25 * nz2[..., None])
    alb[conc] = cc[conc]
    # expansion joints (grid) on the concrete
    gj = ((np.abs((x % 6.0) - 3.0) > 2.93) | (np.abs((z % 6.0) - 3.0) > 2.93)) & conc
    alb[gj] *= 0.55
    # painted ring + a cross-hair (no logos)
    ring = (np.abs(r - 18.0) < 0.6)
    alb[ring] = np.array([0.6, 0.6, 0.58], F32)
    ring2 = (np.abs(r - PAD_R + 0.8) < 0.35)
    alb[ring2] = np.array([0.55, 0.55, 0.53], F32)
    # apron road around the circle and a road out to the south-west
    road = (np.abs(r - (PAD_R + 9)) < 4.5) | ((np.abs(x + z * 0.3 + 60) < 4.0) & (z > PAD_R) & (z < 300))
    alb[road & ~conc] = np.array([0.08, 0.08, 0.085], F32)
    if scorch:
        sc = np.exp(-(r / 14.0) ** 2) * (0.7 + 0.3 * nz[..., None] if False else 1.0)
        ang_ = (np.arctan2(z, x) / (2 * math.pi) + 0.5) * 1024
        nzs = K.noise_tex(256, 77, 5, 0.6)
        streak = cv2.remap(nzs, (ang_ % 256).astype(F32), ((r * 1.5) % 256).astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        s = np.clip(np.exp(-(r / 16.0) ** 1.6) * (0.75 + 0.35 * streak) * 0.95, 0, 0.95)
        alb = alb * (1 - s[..., None]) + np.array([0.02, 0.018, 0.016], F32) * s[..., None]
    return alb

def body_shadow(px, pz, f, B, top=K.L_S1 + K.L_INT):
    """1 where the segment from ground point (px, 0, pz) to lamp f passes through the booster's body (a vertical
    cylinder of radius R_BODY standing from B.y to B.y + top), else 0 (soft at the edge)."""
    fx, fy, fz = f
    bx, by, bz = float(B[0]), float(B[1]), float(B[2])
    ox = px - bx; oz = pz - bz; dx = fx - px; dz = fz - pz
    a = dx * dx + dz * dz + 1e-6; b = 2 * (ox * dx + oz * dz); c = ox * ox + oz * oz - K.R_BODY ** 2
    disc = b * b - 4 * a * c
    ok = disc > 0
    sq = np.sqrt(np.where(ok, disc, 0))
    s1 = (-b - sq) / (2 * a); s2 = (-b + sq) / (2 * a)
    sm = np.clip((s1 + s2) / 2, 0, 1)
    y = sm * fy
    inside = ok & (s2 > 0) & (s1 < 1) & (y > by - 1.0) & (y < by + top)
    # soften: how deep the ray goes through the cylinder (chord length vs diameter)
    depth = np.clip(np.sqrt(np.where(ok, disc, 0)) / a * np.sqrt(a) / (2 * K.R_BODY) * 1.6, 0, 1)
    return np.where(inside, depth, 0.0).astype(F32)

def ground_plane(cam, W, H, t, floods=1.0, flame=0.0, flame_pos=(0, 0, 0), flame_col=K.FLAME_O, scorch=0, moon=1.0, sky_gain=1.0, shadow_B=None):
    """ray/plane render of the pad area lit by the floodlights, the flame and the moon; night sky above the horizon."""
    ys_, xs_ = np.mgrid[0:H, 0:W].astype(F32)
    D = (cam.f[None, None] * cam.fpx + cam.r[None, None] * (xs_ - W / 2 - cam.sx)[..., None] + cam.u[None, None] * (H / 2 + cam.sy - ys_)[..., None])
    D /= np.linalg.norm(D, axis=2, keepdims=True)
    eye = cam.eye
    dn = D[..., 1]
    hit = dn < -1e-4
    s = np.where(hit, -eye[1] / np.where(hit, dn, -1), np.inf)
    px = np.where(hit, eye[0] + D[..., 0] * np.where(hit, s, 0), 0); pz = np.where(hit, eye[2] + D[..., 2] * np.where(hit, s, 0), 0)
    # sky
    sky_c = K.vgrad(W, H, K.SKY_TOP, K.SKY_HOR * 1.5)
    img = np.where(hit[..., None], 0, sky_c * sky_gain)
    if (~hit).any():
        st = np.zeros_like(img); K.stars(st, t, gain=0.35, n=2600, ox=float(cam.f[0]) * 0.3, oy=-float(cam.f[1]) * 0.3, density=0.8)
        img += st * (~hit)[..., None]
    alb = pad_tex(int(scorch))
    m_per_px = TEX_M / TEX_N
    mx = ((px + TEX_M / 2) / m_per_px).astype(F32); my = ((pz + TEX_M / 2) / m_per_px).astype(F32)
    a = cv2.remap(alb, np.where(hit, mx, -5).astype(F32), np.where(hit, my, -5).astype(F32), cv2.INTER_LINEAR,
                  borderMode=cv2.BORDER_CONSTANT, borderValue=(0.04, 0.045, 0.035))
    # irradiance
    E = np.zeros((H, W, 3), F32) + K.MOON[None, None] * MOON_E * moon
    for f in FLOODS:
        fx, fy, fz = f
        dx = fx - px; dz = fz - pz; dist2 = dx * dx + dz * dz + fy * fy
        cosv = fy / np.sqrt(dist2)
        sh = 1.0 if shadow_B is None else (1 - 0.92 * body_shadow(px, pz, f, shadow_B))
        E += (K.FLOOD * FLOOD_I * floods)[None, None] * (cosv / dist2 * spot(f, px, 0.0, pz) * sh)[..., None]
    if flame > 0:
        fx, fy, fz = flame_pos
        dx = fx - px; dz = fz - pz; dist2 = dx * dx + dz * dz + max(1.0, fy) ** 2
        cosv = max(1.0, fy) / np.sqrt(dist2)
        E += (np.asarray(flame_col, F32) * FLAME_I * flame)[None, None] * (cosv / dist2)[..., None]
    gcol = a * E
    dist = np.where(hit, s, 0)
    hz = 1 - np.exp(-dist / 2500.0)
    gcol = gcol * (1 - hz[..., None] * 0.7) + np.array([0.004, 0.005, 0.009], F32) * hz[..., None]
    img = np.where(hit[..., None], gcol, img)
    return img.astype(F32), hit

def world_background(img, cam, W, H, t, hit, st):
    """beyond the detailed pad area: the real night Cape (coast, town lights, sea, sky) from the ground renderer,
    blended in where the pad texture runs out and wherever the sky shows."""
    ys_, xs_ = np.mgrid[0:H, 0:W].astype(F32)
    D = (cam.f[None, None] * cam.fpx + cam.r[None, None] * (xs_ - W / 2 - cam.sx)[..., None] + cam.u[None, None] * (H / 2 + cam.sy - ys_)[..., None])
    D /= np.linalg.norm(D, axis=2, keepdims=True)
    dn = D[..., 1]
    s = np.where(dn < -1e-4, -cam.eye[1] / np.where(dn < -1e-4, dn, -1), 1e9)
    px = cam.eye[0] + D[..., 0] * np.minimum(s, 1e6); pz = cam.eye[2] + D[..., 2] * np.minimum(s, 1e6)
    rr = np.maximum(np.abs(px), np.abs(pz))
    w = np.clip((rr - (TEX_M / 2 - 70)) / 60, 0, 1) * hit + (~hit)
    if w.max() <= 0.001: return
    import ground as G
    sc = 0.5
    w2, h2 = max(16, int(W * sc)), max(16, int(H * sc))
    c2 = K.scaled_cam(cam, sc)
    bg, _ = G.view(c2, w2, h2, t, dict(moon=1.0, lights=1.0, clouds=st.get("clouds", 0.08), cloud_alt=2200, stars=0.35, lz=0.0, haze=0.8))
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR)
    img *= (1 - w)[..., None]; img += bg * w[..., None]

def light_shafts(img, cam, t, floods=1.0):
    """the four towers' beams in the humid air, converging on the pad."""
    for i, f in enumerate(FLOODS):
        p = np.asarray(f, F32); d = K.nrm(FLOOD_AIM - p)
        K.flame_lowres(img, cam, p, d, float(np.linalg.norm(FLOOD_AIM - p)) * 1.4, 1.2, s=0.25, col=K.FLOOD, gain=0.006 * floods, flick=0.0,
                       t=t, core_gain=0.0, expand=7.0, seed=i)

def flood_lamps(img, cam, floods=1.0):
    for (fx, fy, fz) in FLOODS:
        x, y, z = cam.p1((fx, fy, fz))
        if z > 1:
            K.splat(img, x, y, 1.5 + 0.6 * cam.px_per_m(z), K.FLOOD, 4.0 * floods)
            # the mast
            x0, y0, z0 = cam.p1((fx, 0, fz))
            m = np.zeros(img.shape[:2], np.uint8)
            cv2.line(m, (int(x0 * 8), int(y0 * 8)), (int(x * 8), int(y * 8)), 255, max(1, int(0.5 * cam.px_per_m(z))), cv2.LINE_AA, shift=3)
            aa = m.astype(F32) / 255; img *= (1 - aa * 0.9)[..., None]

def pad_lights(floods=1.0, flame=0.0, flame_pos=(0, 0, 0), flame_col=K.FLAME_O, at=(0.0, 20.0, 0.0)):
    L = K.Lights(ambient=K.MOON * 0.004)
    for f in FLOODS: L.lamp(f, K.FLOOD * FLOOD_I * floods * float(spot(f, *at)), 3.0)
    L.dir((0.35, -0.6, 0.5), K.MOON * MOON_E)
    if flame > 0: L.lamp(flame_pos, np.asarray(flame_col, F32) * FLAME_I * flame, 2.0)
    return L

def smoke_light(p, floods=1.0, flame=0.0, flame_pos=(0, 0, 0), flame_col=K.FLAME_O):
    """light reaching a smoke puff at p: returns (irradiance rgb, unit direction toward the strongest source)."""
    E = K.MOON * MOON_E; best = 0.0; key = np.array([0.35, 0.8, -0.45], F32)
    p = np.asarray(p, F32)
    for f in FLOODS:
        fv = np.asarray(f, F32); d2 = float(np.sum((fv - p) ** 2)) + 9.0
        e = FLOOD_I * floods / d2 * float(spot(f, float(p[0]), float(p[1]), float(p[2])))
        E = E + K.FLOOD * e
        if e > best: best = e; key = K.nrm(fv - p)
    if flame > 0:
        fv = np.asarray(flame_pos, F32); d2 = float(np.sum((fv - p) ** 2)) + 4.0
        e = FLAME_I * flame / d2
        E = E + np.asarray(flame_col, F32) * e
        if e > best: best = e; key = K.nrm(fv - p)
    return E, key

def touchdown_smoke(img, cam, t, ts, floods=1.0, flame_k=0.0, n=170, seed=3, flame_pos=(0, 1.0, 0), wind=(1.6, 0.0, 0.4), dens=1.0,
                    albedo=0.16):
    """the burst at touchdown (ts = seconds since contact; negative = the engine blasting the pad just before): exhaust
    hits the concrete and rolls outward in a ring of billows that slow, rise and drift downwind, lit by the floods
    (and orange from the flame while it burns), each billow shaded toward its key light."""
    H, W = img.shape[:2]
    rr = np.random.default_rng(seed)
    R = rr.random((n, 8))
    parts = []
    wind = np.asarray(wind, F32)
    for i in range(n):
        born = -1.7 + R[i, 0] * 1.9                      # emitted during the last ~1.7 s of the burn (+ a little after)
        if ts < born: continue
        age = ts - born
        ang = R[i, 1] * 2 * math.pi
        sp = 18 + 55 * R[i, 2] ** 1.5                    # outward speed off the impingement point (m/s)
        k = 0.8 + 0.6 * R[i, 3]                          # drag
        dist = 2.0 + sp * (1 - math.exp(-age * k)) / k
        rise = 0.6 + 0.03 * dist + age * (0.35 + 1.3 * R[i, 4]) + max(0.0, age - 3) * 0.5 * R[i, 4]
        p = np.array([math.cos(ang) * dist, rise, math.sin(ang) * dist], F32) + wind * age
        x, y, z = cam.p1(p)
        if z < 0.5: continue
        r_m = 2.6 + 0.16 * dist + 2.6 * (1 - math.exp(-age * 0.25)) * (1 + R[i, 5]) + age * 0.3
        r = r_m * cam.px_per_m(z)
        a = 0.42 * dens * min(1.0, age * 3.0 + 0.25) * math.exp(-max(0.0, age - 5) / 12) * (0.6 + 0.4 * R[i, 6])
        E, key = smoke_light(p, floods, flame_k, flame_pos)
        inner = 0.55 + 0.45 * clamp(dist / 30.0)         # the core of the cloud is in its own shadow
        lit = E * albedo * inner * (0.8 + 0.4 * R[i, 7])
        sd = np.array([float(key @ cam.r), -float(key @ cam.u)], F32); nn = float(np.linalg.norm(sd))
        sd = sd / nn if nn > 1e-3 else np.array([0.0, -1.0], F32)
        near = math.exp(-dist / 14)
        emi = K.FLAME_O * 1.4 * flame_k * near * math.exp(-max(0.0, age) * 0.8)
        parts.append((z, x, y, r, a, lit, lit * 0.3, sd, emi, i))
    parts.sort(key=lambda q: -q[0])
    for z, x, y, r, a, lit, lit2, sd, emi, i in parts:
        K.smoke_sprite(img, x, y, r, a, lit, i, rot=i * 37, emissive=emi, col2=lit2, ldir=sd)

def render(t, W, H, st):
    """st: eye, target, fov, B (booster base world pos), legs, fins, soot, burn (0..1 landing-burn gain), ts (s since touchdown),
    scorch, floods, smoke (bool)."""
    cam = K.Cam(st["eye"], st["target"], W, H, fov=st.get("fov", 50), up=st.get("up", (0, 1, 0)), roll=st.get("roll", 0.0))
    B = np.asarray(st.get("B", (0, 3.4, 0)), F32)
    g = st.get("burn", 0.0)
    flame_pos = B - np.array([0, 3.0, 0], F32)
    img, hit = ground_plane(cam, W, H, t, st.get("floods", 1.0), g, flame_pos, K.FLAME_O, st.get("scorch", 0),
                            shadow_B=B if float(B[1]) < 30 else None)
    if st.get("world", True):
        world_background(img, cam, W, H, t, hit, st)
    flood_lamps(img, cam, st.get("floods", 1.0))
    if st.get("shafts", 1.0) > 0: light_shafts(img, cam, t, st.get("floods", 1.0) * st.get("shafts", 1.0))
    ts = st.get("ts", None)
    L = pad_lights(st.get("floods", 1.0), g, flame_pos, at=tuple(B + np.array([0, 20.0, 0], F32)))
    if ts is not None and st.get("smoke", True) and st.get("smoke_behind", True):
        pass
    occ = rt.draw_vehicle(img, cam, B, None, L, stage="booster", legs=st.get("legs", 1.0), fins=st.get("fins", 1.0), soot=st.get("soot", 0.7),
                          eng_glow=g, eng_col=K.FLAME_O, center_only=True)
    if g > 0:
        h = float(B[1])
        K.flame(img, cam, B - np.array([0, 1.25, 0], F32), (0, -1, 0), length=max(4.0, min(34.0, h + 2.0)), radius=0.85, col=K.FLAME_O,
                gain=1.6 * g, flick=1.0, t=t, diamonds=0.6, occ=occ, expand=1.2)
        if h < 40:                                   # the flame spreading across the concrete
            x, y, z = cam.p1((0, 0.5, 0))
            if z > 0.5:
                img += K.glow_layer(W, H, [(x, y, 22 * cam.px_per_m(z), K.FLAME_O, 0.35 * g * sstep(40, 8, h))], 0.25)
    if ts is not None and st.get("smoke", True):
        fk = g + (math.exp(-max(0.0, ts) * 1.5) * 0.6 if ts > -3 else 0)
        touchdown_smoke(img, cam, t, ts, st.get("floods", 1.0), fk, flame_pos=(0, 1.0, 0), dens=st.get("smoke_dens", 1.0))
    return img, cam
