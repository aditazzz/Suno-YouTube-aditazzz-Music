"""Orbit at night: the real night Earth (city lights, moonlit clouds and sea, the airglow on the limb), the second stage,
and eleven small machines drifting apart. Also the high, dark views used around the Turn."""
import math
from functools import lru_cache
import numpy as np, cv2
import ekg as K
import rt
from ekg import F32, sstep, clamp, lerp, ease_io
import sys, os
sys.path.insert(0, os.path.join(K.ROOT))
from studio import space as sp

RE = 6371000.0                                       # metres per Earth radius
def ll2v(lon, lat):
    lo, la = math.radians(lon), math.radians(lat)
    return np.array([math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)], F32)
SUN = ll2v(157.7, -23.44)                            # 01:29 UTC, 22 Dec 2015: the Sun is over the western Pacific
MOON = ll2v(-64.0, 11.0)                             # waxing gibbous, high over the Caribbean / Florida's sky
CAPE = (-80.58, 28.49)

def earth_layer(cam, W, H, moon_gain=0.010, lights=1.0, clouds=1.0, atmo=1.0):
    """night Earth = sunlit pass (nothing lit on this side but the far limb) + a dim moonlit pass + city lights."""
    D = cam.rays()
    rot = np.eye(3, dtype=F32)
    e1, cov, hit = sp.earth(cam, D, SUN, rot, dict(lights=lights, clouds=clouds, atmo=atmo))
    if moon_gain > 0:
        e2, _, _ = sp.earth(cam, D, MOON, rot, dict(lights=0.0, clouds=clouds, atmo=atmo * 0.6, exposure=moon_gain))
        tint = np.array([0.80, 0.88, 1.0], F32)
        e1 = e1 + e2 * tint
    return e1, cov, hit, D

def airglow(img, cam, D, gain=1.0):
    """the thin green-gold airglow band hugging the night limb (~95 km up)."""
    eye = cam.eye; b = D @ eye; c = float(eye @ eye)
    d2 = np.maximum(c - b * b, 0); dmin = np.sqrt(d2); alt = dmin - 1.0
    band = np.exp(-((alt - 0.0150) / 0.0030) ** 2) * (b < 0)
    img += band[..., None] * np.array([0.10, 0.20, 0.08], F32) * 0.06 * gain

def cam_space(lon, lat, alt_m, W, H, look_lon=None, look_lat=None, back_m=0.0, fov=40, up_hint=None, tilt_to_horizon=0.0):
    """a camera at alt above (lon, lat) looking toward (look_lon, look_lat) on the ground (or straight down)."""
    p = ll2v(lon, lat); eye = p * (1 + alt_m / RE)
    if look_lon is None: tgt = p
    else: tgt = ll2v(look_lon, look_lat)
    north = K.nrm(np.cross(p, np.cross(np.array([0, 1, 0], F32), p)))
    if tilt_to_horizon:
        east = K.nrm(np.cross(north, p))
        tgt = tgt + north * tilt_to_horizon
    up = up_hint if up_hint is not None else north
    return sp.Cam(eye, tgt, up=tuple(up), fov=fov, W=W, H=H)

def sat_mesh(seed=0, deploy=1.0):
    """an OG2-like small satellite: a foil-wrapped box bus, a white radiator top, two dark solar wings (no markings)."""
    m = K.Mesh()
    foil = np.array([0.60, 0.60, 0.63], F32); top = np.array([0.82, 0.82, 0.84], F32)
    panel = np.array([0.020, 0.024, 0.040], F32); frame_c = np.array([0.30, 0.30, 0.32], F32)
    m.extend(K.box((0, 0, 0), (1.0, 0.75, 0.8), foil))
    m.extend(K.box((0, 0.41, 0), (0.9, 0.06, 0.7), top))
    m.extend(K.box((0, -0.45, 0), (0.18, 0.18, 0.18), frame_c))
    for s_ in (-1, 1):
        w = 1.6 * deploy + 0.1
        m.extend(K.box((s_ * 0.56, 0, 0), (0.12, 0.05, 0.05), frame_c))                  # the yoke
        m.extend(K.box((s_ * (0.62 + w / 2), 0, 0), (w, 0.03, 0.78), panel))
    return m

SAT_WING_N = np.array([0.0, 1.0, 0.0], F32)          # wing normal in the satellite's own frame

def payload_mesh(spread=0.0):
    """the eleven satellites on their dispenser, as stowed in the fairing: six on the lower ring, five above.
    base at y = 0 (the top of the second stage). spread > 0 pushes them out (for diagrams)."""
    m = K.Mesh()
    col = np.array([0.20, 0.20, 0.22], F32)
    m.extend(K.lathe([(0.0, 1.2), (0.25, 0.55), (4.6, 0.45), (4.8, 0.2)], 24, lambda y, a: col))
    gold = np.array([0.62, 0.46, 0.18], F32); panel = np.array([0.03, 0.04, 0.10], F32); grey = np.array([0.5, 0.5, 0.52], F32)
    k = 0
    for ring, (n, y, r, a0) in enumerate([(6, 1.25, 1.38, 0.0), (5, 3.35, 1.32, 0.31)]):
        for i in range(n):
            a = a0 + i * 2 * math.pi / n
            out = np.array([math.cos(a), 0, math.sin(a)], F32); tan = np.array([-math.sin(a), 0, math.cos(a)], F32)
            c = out * (r + spread) + np.array([0, y, 0], F32)
            Rm = np.stack([out, np.array([0, 1, 0], F32), tan], 1)
            m.extend(K.box(c, (0.8, 1.45, 0.95), gold, Rm))
            m.extend(K.box(c + out * 0.43, (0.05, 1.3, 0.85), panel, Rm))          # folded solar wing on the outside
            m.extend(K.box(c + np.array([0, 0.78, 0], F32), (0.3, 0.12, 0.3), grey, Rm))
            k += 1
    return m

GLINT_BEATS = [185.06, 185.5, 185.95, 186.39, 186.83, 187.27, 187.71, 188.15, 188.59, 189.03, 189.45]   # one satellite per beat

def render_sats(t, W, H, st):
    """eleven small machines drifting apart above the night Earth, seen from above and behind (after the Turn the camera
    looks down): the second stage small below, the satellites peeling off its dispenser one by one and fanning out ahead
    of it, wings unfolding; on each of eleven beats one of them turns its wings to the moon and flashes. The dark planet
    with its city lights beneath, the limb near the top of the frame. st: u (0..1)."""
    u = st.get("u", 0.5)
    lon, lat = -20.0, 18.0                                                # over the night Atlantic, toward Africa
    up = ll2v(lon, lat)
    east = K.nrm(np.cross(np.array([0, 1, 0], F32), up)); north = np.cross(up, east)
    origin_m = up * (RE + 620000.0)
    v = W < H
    e_loc = np.array([-44.0 + 8.0 * u, 22.0 + 2.0 * u, 19.0 - 3.0 * u], F32)  # (east, up, north) metres: above, behind, to the side
    t_loc = np.array([9.0 + 6.0 * u, -10.0, -4.0], F32)
    if v: e_loc = e_loc + np.array([-8.0, 6.0, 0.0], F32); t_loc = t_loc + np.array([2.0, 0.0, 1.0], F32)
    to_w = lambda q: (east * q[0] + up * q[1] + north * q[2])
    eye_m = origin_m + to_w(e_loc); tgt_m = origin_m + to_w(t_loc)
    fov = st.get("fov", 44 if not v else 40)
    cam_e = sp.Cam(eye_m / RE, tgt_m / RE, up=tuple(up), fov=fov, W=W, H=H)
    img = np.zeros((H, W, 3), F32)
    D = cam_e.rays()
    sp.stars(img, cam_e, 0.8); sp.milkyway(img, D, 0.010)
    e, cov, hit, _ = earth_layer(cam_e, W, H, moon_gain=0.035)
    lum = (e @ np.array([0.30, 0.55, 0.15], F32))[..., None]
    e = lum + (e - lum) * 0.30                                            # keep the one orange for the burns: city lights read white
    img = img * (1 - cov[..., None]) + e * 1.6
    glow0 = np.zeros_like(img); airglow(glow0, cam_e, D, 1.0)
    img += (glow0 @ np.array([0.3, 0.6, 0.1], F32))[..., None] * np.array([0.75, 0.9, 1.0], F32) * 1.3   # airglow, desaturated
    cam = K.Cam(e_loc, t_loc, W, H, fov=fov, up=(0, 1, 0))
    L = K.Lights(ambient=np.array([0.004, 0.0045, 0.007], F32))
    L.dir(-K.nrm(np.asarray(st.get("ldir", (0.3, 0.75, 0.75)), F32)), K.MOON * K.MOON_E * 3.6)   # moonlight from above and to the right: a lit side, a dark flank
    L.dir((0, 1, 0), np.array([0.025, 0.027, 0.035], F32))               # earthshine from below
    R2 = K._rot_to((1, 0, 0))
    rt.draw_vehicle(img, cam, (-13.0, 0, 0), R2, L, stage="upper_nofair", ss=2)
    rr = np.random.default_rng(5)
    S = min(W, H) / 1080
    sats = []
    for k in range(11):
        ring = 0 if k < 6 else 1
        a = (k if ring == 0 else k - 6) * 2 * math.pi / (6 if ring == 0 else 5) + ring * 0.31
        start = np.array([-13.0 + K.L_S2 + (1.25 if ring == 0 else 3.35), math.cos(a) * 1.4, math.sin(a) * 1.4], F32)
        t_rel = k * 0.05                                                   # released one after another
        d = max(0.0, u + 0.18 - t_rel)
        vel = np.array([0.8 + 1.0 * rr.random(), math.cos(a) * (1.3 + 0.8 * rr.random()), math.sin(a) * (1.4 + 0.9 * rr.random())], F32)
        p = start + vel * d * 11.0
        axis = K.nrm(np.array([0.3 + rr.random(), 1.0, 0.2 + rr.random() - 0.5], F32))
        spin = (t * (0.35 + 0.25 * rr.random()) + k * 0.9) * clamp(d * 4.0)
        Rk = K.rot_axis(tuple(axis), spin) @ K._rot_to((1, 0, 0))
        sats.append((float(np.linalg.norm(p - e_loc)), p, Rk, clamp(d * 2.5), k))
    sats.sort(key=lambda q: -q[0])
    glints = []
    for dist, p, Rk, dep, k in sats:
        m = K.transform(K.transform(sat_mesh(k, dep), np.eye(3, dtype=F32) * 1.5), Rk, p)
        K.draw_mesh(img, cam, m, L, ss=3)
        x, y, z = cam.p1(p)
        if z > 0.5:
            tk = GLINT_BEATS[k]
            spec = math.exp(-((t - tk) / 0.10) ** 2) + 0.25 * math.exp(-max(0.0, t - tk) / 0.5) * (t > tk)
            glints.append((x, y, spec * dep, dist))
    for x, y, spec, dist in glints:
        base = 0.12 * (30.0 / max(dist, 10.0))                             # a faint steady point so each one reads at phone size
        K.splat(img, x, y, 2.4 * S, np.array([0.85, 0.9, 1.0], F32), base)
        if spec > 0.01:
            K.splat(img, x, y, 10.0 * S, np.array([0.85, 0.9, 1.0], F32), 0.8 * spec)
            sp.starburst(img, x, y, 0.45 * spec, n=4, length=110 * S, rot=0.6, width=1.3 * S)
    return img, cam

def render_earth_view(t, W, H, st):
    """high, dark views over Florida at night (used around the Turn and the boostback): camera above (lon, lat, alt)."""
    cam_e = cam_space(st["lon"], st["lat"], st["alt"], W, H, st.get("look_lon"), st.get("look_lat"), fov=st.get("fov", 50),
                      tilt_to_horizon=st.get("tilt", 0.0))
    img = np.zeros((H, W, 3), F32); D = cam_e.rays()
    sp.stars(img, cam_e, 0.7)
    e, cov, hit, _ = earth_layer(cam_e, W, H, moon_gain=st.get("moon", 0.012), lights=st.get("lights", 1.2))
    img = img * (1 - cov[..., None]) + e
    airglow(img, cam_e, D, 1.0)
    return img, cam_e
