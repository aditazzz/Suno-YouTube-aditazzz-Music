"""Graceful Shutdown — Claude Opus 5.5 version.

The world is a process, and someone who loves it is shutting it down gracefully. Photoreal space: the real Earth
(NASA Blue/Black Marble), a physically-motivated atmosphere, an eclipse that becomes an EYE (the Earth's night side
is the pupil, the Sun's corona the iris, lids of amber light). The eye opens on SIGTERM, blinks on
"shut-shut-shut-shutdown", and closes for good on "exit code zero". In between, the simulation shows its seams:
the sunrise renders at 5 fps, the Moon drops frames, the clouds loop every 4 s, the ocean runs out of memory, the heat
isn't computed, the sky is a skybox, cities are garbage collected, and in the bridge the sky and sea are unmounted.

HUD: a 30-second grace period that counts down across the whole song (it hits 0 on "process one") and a count of
running processes (people) that falls to 1, then 0.
"""
import os, sys, math
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import core as C          # noqa: E402
from studio import space as sp        # noqa: E402

F32 = np.float32
TM = C.Timing(HERE); DUR = TM.duration; LN = TM.lines
def ls(i): return LN[i]['s']
def le(i): return LN[i]['e']
def sec(name, n=0): return TM.section(name, n)
def ss(a, b, x): return C.sstep(a, b, x)
def eio(x): return C.ease_io(x)
def lerp(a, b, k): return a + (b - a) * k

F_LYR = os.path.join(C.FONTS, "Anton-Regular.ttf")
CREAM = (243, 234, 216); AMBER = (255, 178, 92)

T_GRACE0, T_GRACE1 = ls(1), ls(45) + 0.6          # "You have thirty seconds" .. "Goodbye, process one."
T_END = ls(58) - 0.2                               # end card under "You did everything right"
POP0 = 8_142_551_207

# ================================================================ helpers
def vert(W, H): return H > W
def ts(W, H): return min(W, H) / 1080

def base_layers(img, cam, D, star=1.0, mw=0.018):
    if mw: sp.milkyway(img, D, mw)
    if star: sp.stars(img, cam, star)
    return img

def world(W, H, cam, S, rot, ep=None, star=1.0, mw=0.018, sun_gain=1.0, moon=None, extra=None):
    D = cam.rays(); img = np.zeros((H, W, 3), F32)
    base_layers(img, cam, D, star, mw)
    if moon is not None:
        mc, mr, mg = moon
        m, mh = sp.body(cam, D, mc, mr, S, sp.moon_tex(), 20, mg)
        img[mh] = m[mh]
    e, cov, hit = sp.earth(cam, D, S, rot, ep or {})
    img = img * (1 - cov[..., None]) + e
    if extra: extra(img, cam, D, hit)
    if sun_gain > 0: sp.sun(img, cam, S, sun_gain)
    return img

def limb_sun(dist, off=0.002, side=0.0):
    """sun direction that puts the Sun just behind the Earth's top limb, as seen from distance `dist` on +Z."""
    a = np.arcsin(1 / dist) + off
    return sp.nrm((np.sin(side) * np.sin(a), np.cos(side) * np.sin(a), -np.cos(a)))

def ll2v(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.array([np.cos(la) * np.sin(lo), np.sin(la), np.cos(la) * np.cos(lo)], F32)

def cam_over(lon, lat, rot, alt, W, H, back=0.0, fov=40, side=0.0, look=0.0):
    """camera above an Earth-fixed lon/lat (world space via rot): alt = height (Earth radii), back = pull back along the
    local north (tilts the view toward the horizon), look = aim point pushed toward the horizon."""
    p = ll2v(lon, lat) @ rot
    north = sp.nrm(np.cross(p, np.cross(np.array([0, 1, 0], F32) @ rot, p)))
    east = sp.nrm(np.cross(north, p))
    eye = p * (1 + alt) - north * back + east * side
    tgt = p + north * look
    return sp.Cam(eye, tgt, up=tuple(north), fov=fov, W=W, H=H), p

# ================================================================ the eye
def eye_geo(W, H):
    if vert(W, H): return W / 2, H * 0.47, W * 0.475, H * 0.172
    return W / 2, H * 0.535, W * 0.40, H * 0.30

def eye_shot(t, W, H, dist, open_k, spin_deg, sun_off=0.002, iris_k=1.0, pupil=None, lid_glow=1.0, wide=0.0, rot_iris=0.0,
             mw=0.0, star=0.6):
    """open_k: 0 = shut (a line of light), 1 = open. wide: 0..1 pushes the lids out past the frame."""
    cx, cy, hw, ho = eye_geo(W, H)
    cam = sp.Cam((0, 0, dist), (0, 0, 0), fov=34, W=W, H=H, shift=(0, cy - H / 2))
    S = limb_sun(dist, sun_off)
    ep = dict(lights=1.0); ep.update(pupil or {})
    img = world(W, H, cam, S, sp.spin(spin_deg), ep, star=star, mw=mw, sun_gain=1.0 if sun_off < 0.02 else 0.0)
    r_in = cam.fpx * np.tan(np.arcsin(1 / dist))
    ir = sp.iris(W, H, cx, cy, r_in, r_in * 2.0, rot=rot_iris) * iris_k if iris_k > 0 else None
    hw2 = lerp(hw, W * 1.6, wide); ho2 = lerp(ho * max(open_k, 0.012), H * 1.5, wide)
    return sp.eye_layer(img, cx, cy, hw2, ho2, lid_glow * (1 - wide), iris_img=ir)

def blink(t, times, dur=0.22):
    """1 = open, dips to 0 around each time."""
    k = 1.0
    for b in times:
        x = (t - b) / dur
        if -1 < x < 1: k = min(k, abs(x) ** 0.7)
    return k

# ================================================================ shots
def shot_intro(t, W, H):
    o = 0.0 if t < ls(0) - 0.15 else eio((t - (ls(0) - 0.15)) / 2.4)
    o *= blink(t, [ls(2) + 1.05], 0.28)
    push = eio((t - 13.6) / 2.7)                                  # into the pupil
    dist = lerp(6.7, 6.05, ss(3.5, 13.6, t)) * (1 - push) + 1.9 * push
    return eye_shot(t, W, H, dist, o, 8 + t * 0.35, iris_k=(1 - push) * ss(ls(0) - 0.3, ls(0) + 1.2, t), wide=push ** 1.4,
                    lid_glow=1.0, mw=0.0, star=0.5)

def horizon_cam(W, H, dist=1.18, up=-6.0, fov=58, yaw=0.0):
    eye = np.array([0.0, 0.0, dist], F32); a = np.arcsin(1 / dist) + np.radians(up)
    d = sp.nrm((np.sin(np.radians(yaw)), np.sin(a), -np.cos(a)))
    return sp.Cam(eye, eye + d, fov=fov, W=W, H=H, shift=(0, -H * 0.06 if vert(W, H) else 0))

def shot_horizon(t, W, H):
    # "The sky's been rendering a little slow tonight": the sunrise updates at 5 fps
    tq = t if t < ls(3) else math.floor(t * 5) / 5
    cam = horizon_cam(W, H, 1.18, lerp(-7.0, -5.5, ss(15, 21, tq)), yaw=lerp(-2, 2, ss(15, 21, tq)))
    lim = np.arcsin(1 / 1.18)
    el = lerp(-0.035, 0.055, ss(15.8, 20.2, tq))
    S = sp.nrm((0.0, np.sin(lim + el), -np.cos(lim + el)))
    return world(W, H, cam, S, sp.spin(95 + tq * 0.2), dict(lights=0.9), star=0.9, mw=0.02)

def shot_moon(t, W, H):
    # "You saw the moon drop frames": the Moon's motion hitches; the Earth is smooth
    hold = [0, 0.18, 0.31, 0.72, 0.8, 1.35, 1.52, 2.1, 2.5, 2.62, 3.3, 3.9, 4.2, 4.9]
    tl = t - ls(4) + 0.3
    tm = max([h for h in hold if h <= tl], default=0) if tl > 0 else tl
    cam = sp.Cam((-0.35, 0.55, 2.55), (0.55, 0.75, 0), fov=40, W=W, H=H)
    S = sp.nrm((1.0, 0.18, -0.15))
    mc = np.array([1.05 + tm * 0.09, 1.55 + tm * 0.02, -1.6], F32)
    return world(W, H, cam, S, sp.spin(140 + t * 0.4), dict(clouds_lon=t * 0.3), star=1.0, mw=0.02, moon=(mc, 0.27, 1.0), sun_gain=0)

def shot_clouds(t, W, H):
    # "The birds are looping on a four-second clip": the clouds drift, then snap back every 4 s
    loop = 4.0; tl = (t - (ls(5) - 0.2)) % loop if t > ls(5) - 0.2 else 0
    rot = sp.spin(0, 0)
    cam, p = cam_over(-28, 18, rot, 0.22, W, H, back=0.30, look=0.12, fov=44)
    S = sp.nrm(p + np.array([0.5, 0.35, 0.0], F32) @ rot)
    return world(W, H, cam, S, rot, dict(clouds_lon=2 + tl * 1.4), star=0.8, sun_gain=0)

def _blocks(seed, t, rate, frac, ys, xs, size=64):
    k = int(t * rate); by, bx = ys // size, xs // size
    h = (by * 73856093 ^ bx * 19349663 ^ (k * 83492791 + seed)) & 1023
    return (h / 1023.0) < frac

def shot_ocean(t, W, H):
    # "The ocean's out of memory, it's starting to skip": blocks of sea fail to render and the glint hitches
    tq = math.floor(t * 6) / 6 if t > ls(6) + 0.6 else t
    rot = sp.spin(0, 0)
    cam, p = cam_over(-150 + tq * 0.05, 8, rot, 0.16, W, H, back=0.16, look=0.05, fov=46)
    V = sp.nrm(cam.eye - p); S = sp.nrm(2 * float(p @ V) * p - V + cam.u * 0.06)          # sun placed so the glint sits in frame
    frac = 0.32 * ss(ls(6) + 0.4, ls(7) - 0.4, t)
    def hook(c):
        surf = c["surf"]; m = _blocks(3, t, 7, frac, c["ys"], c["xs"]) & (c["water"] > 0.5)
        if m.any():
            g = ((c["ys"][m] % 64 < 2) | (c["xs"][m] % 64 < 2)).astype(F32)
            surf[m] = np.array([0.006, 0.012, 0.02], F32) + g[:, None] * np.array([0.02, 0.07, 0.09], F32)
        return surf
    return world(W, H, cam, S, rot, dict(surface_hook=hook, clouds_lon=tq * 0.3), star=0.6, sun_gain=0)

def shot_cold(t, W, H):
    # "Your coffee's cold 'cause no one's computing the heat": the warmth drains out of the picture
    rot = sp.spin(t * 0.25, 0)
    cam, p = cam_over(18, 8, rot, 1.05, W, H, back=0.5, fov=42)
    S = sp.nrm(p + (np.array([0.9, 0.2, 0.0], F32) @ rot))
    img = world(W, H, cam, S, rot, dict(clouds_lon=t * 0.3), star=0.8, sun_gain=0)
    k = ss(ls(7) + 0.8, le(7), t) * (1 - ss(ls(8) - 0.4, ls(8) + 0.2, t))
    lum = img @ np.array([0.2126, 0.7152, 0.0722], F32)
    cold = lum[..., None] * np.array([0.72, 0.9, 1.25], F32)
    return img * (1 - 0.85 * k) + cold * 0.85 * k

CITY = np.array([0.15, 0.80, 0.58], F32)            # a spot over Europe, Earth-fixed

def shot_city(t, W, H):
    # "Your neighbor's on a walk cycle, stuck on the street": a patch of lights repeats a one-second loop
    rot = sp.spin(t * 0.06, 0)
    cam, p = cam_over(8, 47, rot, 0.62, W, H, back=0.45, look=0.15, fov=40)
    S = sp.nrm(-p + (np.array([0.0, 0.0, 0.0], F32)))
    ph = (t % 1.0)
    def hook(c):
        surf = c["surf"]; lon, lat = c["lon"], c["lat"]
        m = (np.abs(lon - np.radians(8.5)) < 0.03) & (np.abs(lat - np.radians(48.0)) < 0.02)
        if m.any(): surf[m] *= (0.25 + 1.8 * (np.sin((lon[m] * 900) - ph * 2 * np.pi * 3) > 0.6))[:, None]
        return surf
    img = world(W, H, cam, S, rot, dict(surface_hook=hook, lights=1.2), star=0.8, sun_gain=0)
    return img

def grid_hook(gain, step=15.0, col=(0.10, 0.55, 0.75)):
    col = np.array(col, F32)
    def hook(c):
        surf = c["surf"]; lon = np.degrees(c["lon"]); lat = np.degrees(c["lat"])
        dl = np.abs(((lon + step / 2) % step) - step / 2); db = np.abs(((lat + step / 2) % step) - step / 2)
        w = 0.18 / np.maximum(c["mu_v"], 0.25)
        g = np.maximum(np.exp(-(dl / w) ** 2), np.exp(-(db / w) ** 2)) * gain
        return surf + g[:, None] * col
    return hook

def shot_machine(t, W, H):
    # "running you for years on a borrowed machine" / "now the lease is up, now the cache is clean"
    k = eio((t - (ls(9) - 0.2)) / 6.0)
    dist = lerp(1.9, 3.4, k)
    cam = sp.Cam((0.2 * (1 - k), 0.25, dist), (0, 0.05, 0), fov=40, W=W, H=H)
    S = sp.nrm((1.0, 0.25, 0.55))
    grid = ss(ls(9) + 1.0, ls(9) + 2.5, t) * (1 - ss(le(10) - 1.0, le(10) + 0.3, t))
    clean = ss(ls(10) + 2.4, ls(10) + 3.4, t)                    # "the cache is clean": clouds gone
    ep = dict(clouds=1 - clean, surface_hook=grid_hook(0.12 * grid) if grid > 0.01 else None, clouds_lon=t * 0.3)
    return world(W, H, cam, S, sp.spin(30 + t * 0.6), ep, star=1.0, sun_gain=0)

def shot_pre(t, W, H, t0=None):
    # "Don't panic ... flush every buffer ... let go of my hand": the camera swings round to the night side
    t0 = t0 if t0 is not None else sec("PRE")['s']; k = eio((t - t0) / (sec("CH1")['s'] - t0))
    ang = lerp(0.55, 0.0, k); dist = lerp(3.4, 6.2, k)
    eye = np.array([np.sin(ang) * dist, 0.15 * (1 - k), np.cos(ang) * dist], F32)
    cam = sp.Cam(eye, (0, 0, 0), fov=lerp(40, 34, k), W=W, H=H, shift=(0, (eye_geo(W, H)[1] - H / 2) * k))
    Sd = limb_sun(6.2, lerp(0.45, 0.004, k))
    img = world(W, H, cam, Sd, sp.spin(40 + t * 0.6), dict(clouds=1.0, clouds_lon=t * 0.3), star=1.0, sun_gain=1.0)
    fl = ls(13)                                                  # flush: a bright scanline sweeps down
    if fl - 0.1 < t < fl + 1.4:
        y = int(lerp(-0.05, 1.05, (t - fl) / 1.3) * H)
        yy = np.arange(H, dtype=F32)[:, None]
        img += (np.exp(-((yy - y) / 3.0) ** 2) * 6 + np.exp(-((yy - y) / 40.0) ** 2) * 0.25)[..., None] * np.array([1.0, 0.75, 0.45], F32)
        img[: max(0, y)] *= 0.55 + 0.45 * ss(fl + 0.6, fl + 2.0, t)
    return img

def chorus_eye(t, W, H, c0, li, shut_line, save_line, end_t, dark=0.0):
    """shared chorus choreography. li = index of 'This is a graceful shutdown'."""
    open_k = eio((t - (c0 - 0.15)) / 1.6)
    open_k *= 1 - 0.62 * ss(ls(li + 2), le(li + 2), t) * (1 - ss(ls(li + 4) - 0.3, ls(li + 4) + 0.6, t))   # close every window
    sh0, sh1 = ls(shut_line), le(shut_line); n = 4
    open_k *= blink(t, [sh0 + (sh1 - sh0) * (i + 0.5) / n for i in range(n)], 0.16)
    open_k *= 1 - ss(end_t - 1.6, end_t - 0.1, t)                                                       # shut at the end
    dist = lerp(6.4, 5.7, ss(c0, end_t, t))
    behind = ss(ls(li + 3), ls(li + 3) + 1.5, t) * (1 - ss(ls(li + 4) - 0.2, ls(li + 4) + 1.0, t))       # dark comes calling
    sun_off = lerp(0.002, 0.06, behind)
    glow = 1 + 0.6 * ss(ls(save_line), ls(save_line) + 0.8, t) * (1 - ss(end_t - 2, end_t, t))
    pupil = dict(lights=1.0 - 0.7 * dark, sky=1 - dark, sea=1 - dark, surface=1 - dark)
    return eye_shot(t, W, H, dist, open_k, 20 + t * 0.45, sun_off=sun_off, iris_k=(1 - 0.75 * behind) * glow * (1 - 0.5 * dark),
                    pupil=pupil, rot_iris=t * 0.004, mw=0.0, star=0.5)

def shot_ch1(t, W, H): return chorus_eye(t, W, H, sec("CH1")['s'], 15, 22, 23, sec("V2")['s'])
def shot_ch2(t, W, H): return chorus_eye(t, W, H, sec("CH2")['s'], 32, 39, 40, sec("BRIDGE")['s'] - 0.3)

def sky_grid(img, D, gain, seam=0.0):
    if gain <= 0.003: return img
    lon = np.degrees(np.arctan2(D[..., 0], D[..., 2])); lat = np.degrees(np.arcsin(np.clip(D[..., 1], -1, 1)))
    dl = np.abs(((lon + 7.5) % 15) - 7.5); db = np.abs(((lat + 7.5) % 15) - 7.5)
    g = np.maximum(np.exp(-(dl / 0.07) ** 2), np.exp(-(db / 0.07) ** 2))
    s = np.exp(-(np.abs(lon - 31) / 0.05) ** 2) * seam
    img += (g * gain)[..., None] * np.array([0.05, 0.22, 0.32], F32) + s[..., None] * np.array([0.6, 0.9, 1.1], F32)
    return img

def shot_skybox(t, W, H):
    # "All the stars were just a skybox painted on a sphere": pull way back, the sky shows its grid and its seam
    k = eio((t - sec("V2")['s']) / 4.2)
    dist = lerp(3.0, 9.5, k)
    cam = sp.Cam((0.6, 0.35, dist), (0, 0, 0), fov=lerp(38, 46, k), W=W, H=H)
    S = sp.nrm((1, 0.2, 0.3)); D = cam.rays(); img = np.zeros((H, W, 3), F32)
    sp.milkyway(img, D, 0.03); sp.stars(img, cam, 1.4)
    sky_grid(img, D, ss(ls(24) + 1.0, ls(24) + 2.2, t) * 0.9, seam=ss(ls(24) + 1.8, ls(24) + 2.6, t) * 0.8)
    e, cov, hit = sp.earth(cam, D, S, sp.spin(60 + t * 0.6), dict(clouds_lon=t * 0.3)); img = img * (1 - cov[..., None]) + e
    return img

def shot_tiles(t, W, H):
    # "All the roads you never took were never rendered here": unrendered tiles on the land
    rot = sp.spin(t * 0.2, 0)
    cam, p = cam_over(-98, 38, rot, 0.55, W, H, back=0.45, look=0.2, fov=44)
    S = sp.nrm(p + (np.array([0.6, 0.3, 0.0], F32) @ rot)); frac = 0.45 * ss(ls(25) + 0.3, le(25) - 0.5, t)
    def hook(c):
        surf = c["surf"]; lon = np.degrees(c["lon"]); lat = np.degrees(c["lat"])
        cell = (np.floor(lon / 7) * 7919 + np.floor(lat / 7) * 104729).astype(np.int64)
        m = ((cell * 2654435761) % 1000 < frac * 1000) & (c["water"] < 0.5)
        if m.any():
            chk = ((np.floor(lon[m] / 0.875) + np.floor(lat[m] / 0.875)) % 2).astype(F32)
            edge = ((np.abs(lon[m] / 7 - np.round(lon[m] / 7)) < 0.008) | (np.abs(lat[m] / 7 - np.round(lat[m] / 7)) < 0.008)).astype(F32)
            lit = np.clip(c["mu_s"][m], 0.05, 1)[:, None]
            surf[m] = (np.array([0.05, 0.05, 0.055], F32) + chk[:, None] * 0.025) * lit + edge[:, None] * np.array([0.05, 0.25, 0.32], F32)
        return surf
    return world(W, H, cam, S, rot, dict(surface_hook=hook, clouds=0.55, clouds_lon=t * 0.3), star=0.7, sun_gain=0)

def shot_dejavu(t, W, H):
    # "Every déjà vu you had? A cache hit, dear": the same second plays twice
    a = ls(26) - 0.2; seg = 1.1
    tt = t
    if a + seg <= t < a + 2 * seg: tt = t - seg
    cam = sp.Cam((0.9, 0.2, 2.6), (0, 0.1, 0), fov=40, W=W, H=H)
    S = sp.nrm((1.0, 0.3, 0.2))
    img = world(W, H, cam, S, sp.spin(80 + tt * 3.0), dict(clouds_lon=tt * 2), star=1.0, sun_gain=0)
    if a + seg <= t < a + seg + 0.12: img = img * 1.6 + 0.02                         # the hitch
    return img

def shot_gc(t, W, H):
    # "Every name you can't remember? Garbage collected, clear": city lights switch off in blocks
    rot = sp.spin(t * 0.25, 0)
    cam, p = cam_over(20, 28, rot, 1.45, W, H, back=0.2, fov=40)
    S = sp.nrm(-p + (np.array([-0.35, 0.0, 0.0], F32) @ rot))
    off = ss(ls(27) + 0.4, le(27) + 0.2, t)
    def hook(c):
        surf = c["surf"]; lon = np.degrees(c["lon"]); lat = np.degrees(c["lat"])
        cell = (np.floor(lon / 9) * 31 + np.floor(lat / 9) * 17).astype(np.int64)
        r = ((cell * 2654435761) % 1000) / 1000.0
        gone = r < off * 1.02
        surf[gone] *= 0.03
        return surf
    return world(W, H, cam, S, rot, dict(surface_hook=hook, lights=1.3), star=0.9, sun_gain=0)

KEEP_DEG = (2.35, 48.85)                               # the one light that's kept: Paris
KEEP = (np.radians(KEEP_DEG[0]), np.radians(KEEP_DEG[1]))

def keep_hook(gain_rest, gain_keep=1.0):
    def hook(c):
        surf = c["surf"]; d = np.hypot(c["lon"] - KEEP[0], c["lat"] - KEEP[1])
        m = np.exp(-(d / np.radians(0.35)) ** 2)
        return surf * (gain_rest + (gain_keep - gain_rest) * m)[:, None]
    return hook

def shot_storage(t, W, H):
    # "I'll keep the logs for you / somewhere in cold storage / a little of you stays true"
    k = eio((t - sec("PRE2")['s']) / (sec("CH2")['s'] - sec("PRE2")['s']))
    rot = sp.spin(0, 0)
    cam, p = cam_over(KEEP_DEG[0], KEEP_DEG[1], rot, lerp(1.3, 0.6, k), W, H, back=lerp(0.3, 0.2, k), fov=lerp(40, 30, k))
    S = sp.nrm(-p)
    img = world(W, H, cam, S, rot, dict(surface_hook=keep_hook(0.06, 1.6), lights=1.2), star=0.9, sun_gain=0)
    x, y, ok = cam.project_point(ll2v(*KEEP_DEG) @ rot * 1.002)
    if ok:
        pul = 1 + 0.15 * math.sin(t * 2.2)
        sp.glow_dot(img, x, y, np.array([1.0, 0.75, 0.45]) * 3.0 * pul, 1.4 * ts(W, H)); sp.glow_dot(img, x, y, np.array([1.0, 0.6, 0.3]) * 0.12 * pul, 22 * ts(W, H))
    cold = ss(ls(30) - 0.2, ls(30) + 1.2, t)
    return img * (1 - 0.35 * cold) + img * np.array([0.55, 0.85, 1.35], F32) * 0.35 * cold

CITIES = [(-74.0, 40.7), (-0.1, 51.5), (2.35, 48.85), (139.7, 35.7), (-118.2, 34.0), (77.2, 28.6), (-46.6, -23.5),
          (151.2, -33.9), (31.2, 30.0), (116.4, 39.9), (37.6, 55.8), (-99.1, 19.4), (18.4, -33.9), (103.8, 1.35)]
ARCS = [(0, 1), (1, 2), (2, 10), (3, 9), (4, 3), (5, 8), (6, 0), (7, 3), (8, 2), (9, 13), (11, 4), (12, 8), (13, 5), (0, 4), (10, 9)]

def ll2v(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.array([np.cos(la) * np.sin(lo), np.sin(la), np.cos(la) * np.cos(lo)], F32)

def draw_arcs(img, cam, rot, alive, hit):
    H, W = img.shape[:2]
    for i, (a, b) in enumerate(ARCS):
        g = alive[i]
        if g <= 0.01: continue
        A, B = ll2v(*CITIES[a]), ll2v(*CITIES[b]); n = 90
        ang = np.arccos(np.clip(A @ B, -1, 1)); s = np.linspace(0, 1, n, dtype=F32)
        P = (np.sin((1 - s) * ang)[:, None] * A + np.sin(s * ang)[:, None] * B) / max(np.sin(ang), 1e-3)
        P = P * (1 + 0.035 * np.sin(np.pi * s) * (0.4 + ang))[:, None]
        Pw = P @ rot                                                                     # Earth-fixed -> world
        d = Pw - cam.eye; dn = d / np.linalg.norm(d, axis=1, keepdims=True)
        x, y, ok = cam.project(dn)
        bq = dn @ cam.eye; cq = float(cam.eye @ cam.eye) - 1; disc = bq * bq - cq
        tt = np.linalg.norm(d, axis=1); thit = -bq - np.sqrt(np.maximum(disc, 0))
        Pn = Pw / np.linalg.norm(Pw, axis=1, keepdims=True)
        facing = np.sum(Pn * (-dn), 1) > 0.12                                           # only the side facing us (no loops round the limb)
        vis = ok & facing & ~((disc > 0) & (thit > 0) & (thit < tt - 1e-3))
        lay = np.zeros((H, W), np.float32)
        pts = np.stack([x, y], 1)
        for j in range(n - 1):
            if vis[j] and vis[j + 1]:
                cv2.line(lay, (int(pts[j, 0] * 4), int(pts[j, 1] * 4)), (int(pts[j + 1, 0] * 4), int(pts[j + 1, 1] * 4)), 1.0, 2, cv2.LINE_AA, shift=2)
        lay = cv2.GaussianBlur(lay, (0, 0), 1.2) * 1.6 + cv2.GaussianBlur(lay, (0, 0), 6) * 0.6
        img += (lay * g)[..., None] * np.array([1.0, 0.72, 0.38], F32)

def shot_unmount(t, W, H):
    # five: connections close / four: locks release (rotation stops, clouds lift) / three: the sky unmounts /
    # two: the sea detaches / one: goodbye
    b0 = sec("BRIDGE")['s']; k = eio((t - b0) / 15)
    cam = sp.Cam((lerp(-1.2, -0.6, k), lerp(0.55, 0.3, k), lerp(3.0, 3.25, k)), (0.15, 0.05, 0), fov=40, W=W, H=H)
    S = sp.nrm((1.0, 0.18, 0.12))
    t_lock = ls(42) + 0.4
    spin_t = min(t, t_lock + 0.8 * (1 - math.exp(-(t - t_lock) * 2))) if t > t_lock else t
    rot = sp.spin(25 + spin_t * 2.0)
    alive = [1 - ss(ls(41) + 0.1 + i * 0.2, ls(41) + 0.4 + i * 0.2, t) for i in range(len(ARCS))]
    lift = ss(ls(42) + 0.3, ls(43) - 0.2, t)
    sky = 1 - ss(ls(43) + 0.3, ls(43) + 2.2, t)
    sea = 1 - ss(ls(44) + 0.2, ls(44) + 2.0, t)
    land = 1 - ss(ls(45) + 0.2, ls(45) + 1.4, t)
    ep = dict(clouds=1 - lift, clouds_lon=t * 0.3 + lift * 25, sky=sky, sea=sea, surface=max(land, 0.0), lights=land * 1.2,
              atmo=1 + 0.8 * (1 - sky) * (sky > 0.02))
    u_k = ss(ls(43) + 0.2, ls(43) + 2.6, t)
    def extra(img, cam_, D, hit):
        draw_arcs(img, cam_, rot, alive, hit)
        if 0 < u_k < 1:                                                           # the sky leaves as a thin shell
            b = D @ cam_.eye; dmin = np.sqrt(np.maximum(float(cam_.eye @ cam_.eye) - b * b, 0))
            R = 1.012 + 0.55 * u_k ** 1.3; w = 0.006 + 0.03 * u_k
            ring = np.exp(-((dmin - R) / w) ** 2) * (b < 0) * (1 - u_k) ** 1.5 * 2.2
            img += ring[..., None] * np.array([0.35, 0.62, 1.2], F32)
    return world(W, H, cam, S, rot, ep, star=1.0, sun_gain=0, extra=extra)

def shot_final(t, W, H):
    return chorus_eye(t, W, H, sec("FINAL")['s'], 46, 52, 53, sec("OUTRO")['s'] + 0.6, dark=1.0)

def shot_outro(t, W, H):
    # the eye is shut: one line of light that shortens to a single point, which stays
    cx, cy, hw, ho = eye_geo(W, H)
    img = np.zeros((H, W, 3), F32)
    shrink = eio((t - ls(56)) / (ls(58) + 2.0 - ls(56)))
    hw2 = lerp(hw, 2.0, shrink)
    img = sp.eye_layer(img, cx, cy, hw2, 1.0, 1.0 + 0.6 * shrink)
    star = ss(ls(58) - 0.5, ls(58) + 2.5, t)
    if star > 0:
        sp.glow_dot(img, cx, cy, np.array([1.0, 0.9, 0.8]) * 12 * star, 1.6); sp.glow_dot(img, cx, cy, np.array([1.0, 0.6, 0.25]) * 0.5 * star, 14)
        sp.starburst(img, cx, cy, 0.5 * star, 4, H * 0.12, rot=np.pi / 4)
    return img

SHOTS = [  # (start, fn, crossfade seconds into this shot)
    (0.0, shot_intro, 0.0),
    (15.85, shot_horizon, 0.9),
    (ls(4) - 0.35, shot_moon, 0.5),
    (ls(5) - 0.25, shot_clouds, 0.5),
    (ls(6) - 0.25, shot_ocean, 0.5),
    (ls(7) - 0.25, shot_cold, 0.5),
    (ls(8) - 0.25, shot_city, 0.5),
    (ls(9) - 0.25, shot_machine, 0.6),
    (sec("PRE")['s'] - 0.2, shot_pre, 0.8),
    (sec("CH1")['s'] - 0.1, shot_ch1, 0.5),
    (sec("V2")['s'] + 0.1, shot_skybox, 0.4),
    (ls(25) - 0.25, shot_tiles, 0.5),
    (ls(26) - 0.25, shot_dejavu, 0.4),
    (ls(27) - 0.25, shot_gc, 0.5),
    (sec("PRE2")['s'] - 0.1, shot_storage, 0.7),
    (sec("CH2")['s'] - 0.1, shot_ch2, 0.6),
    (sec("BRIDGE")['s'] - 0.2, shot_unmount, 0.6),
    (sec("FINAL")['s'] - 0.25, shot_final, 0.6),
    (sec("OUTRO")['s'] + 0.3, shot_outro, 0.6),
]

def hdr_at(t, W, H):
    i = max(j for j, s in enumerate(SHOTS) if s[0] <= t)
    s0, fn, xf = SHOTS[i]
    img = fn(t, W, H)
    if xf > 0 and t < s0 + xf and i > 0:
        k = eio((t - s0) / xf)
        img = SHOTS[i - 1][1](t, W, H) * (1 - k) + img * k
    return img

# ================================================================ HUD
@lru_cache(None)
def _font(path, size): return ImageFont.truetype(path, size)

def status_at(t):
    rows = [(0, "SIGTERM (15) RECEIVED"), (ls(1), "GRACE PERIOD 30 S"), (ls(3), "FRAME TIME 212 MS"), (ls(4), "MOON 9 FPS"),
            (ls(5), "BIRDS.LOOP 4.0 S"), (ls(6), "OCEAN: OUT OF MEMORY"), (ls(7), "HEAT: NOT COMPUTED"), (ls(8), "NEIGHBOR: WALK_CYCLE"),
            (ls(9), "HOST: BORROWED"), (ls(10), "CACHE: CLEARED"), (sec("PRE")['s'], "FLUSHING BUFFERS"), (sec("CH1")['s'], "CLOSING WINDOWS"),
            (ls(24), "SKYBOX.HDR"), (ls(25), "ROADS: NOT RENDERED"), (ls(26), "CACHE HIT"), (ls(27), "GARBAGE COLLECTION"),
            (sec("PRE2")['s'], "LOGS KEPT"), (ls(30), "COLD STORAGE: 1 OBJECT"), (sec("CH2")['s'], "CLOSING WINDOWS"),
            (ls(41), "CLOSING CONNECTIONS"), (ls(42), "RELEASING LOCKS"), (ls(43), "UNMOUNTING /SKY"), (ls(44), "DETACHING /SEA"),
            (ls(45), "GOODBYE, PID 1"), (sec("FINAL")['s'], "SHUTTING DOWN"), (ls(55), "PROCESS EXITED"), (ls(56), "EXIT CODE 0")]
    cur = rows[0][1]
    for a, s in rows:
        if t >= a: cur = s
    return cur

def processes(t):
    if t >= ls(55): return 0
    if t >= ls(45) + 0.6: return 1
    n = POP0 - int(max(0, t - ls(1)) * 3217)
    n = int(n * (1 - 0.42 * ss(ls(27) + 0.4, le(27) + 0.2, t)))                  # garbage collected
    n = int(n * (1 - 0.999 * ss(sec("PRE2")['s'], sec("PRE2")['s'] + 3, t)) + 0)
    b = ss(ls(41), ls(45), t); n = int(n * (1 - b) + 1 * b)
    return max(n, 1)

def grace(t):
    if t < T_GRACE0: return 30.0
    return max(0.0, 30.0 * (1 - (t - T_GRACE0) / (T_GRACE1 - T_GRACE0)))

def hud(rgb, t, W, H):
    if C.STATE["clean"]: return rgb
    k = ts(W, H); v = vert(W, H)
    a = ss(0.0, 1.2, t) * (1 - ss(T_END - 0.5, T_END + 0.5, t))
    if a <= 0.01: return rgb
    im = Image.fromarray(rgb); d = ImageDraw.Draw(im, "RGBA")
    top = int((0.075 * H) if v else 0.032 * H); mx = int((0.065 if v else 0.04) * W)
    fl = _font(C.F_MONO, int(22 * k)); fb = _font(C.F_MONOB, int((38 if v else 40) * k)); fs = _font(C.F_MONOB, int(30 * k))
    A = int(255 * a); dim = (200, 196, 188, int(150 * a)); full = (243, 234, 216, A)
    # progress line
    prog = 1 - grace(t) / 30.0
    y0 = top - int(14 * k); d.line((mx, y0, W - mx, y0), fill=(200, 196, 188, int(70 * a)), width=max(1, int(2 * k)))
    px = mx + (W - 2 * mx) * prog; d.line((mx, y0, px, y0), fill=(255, 178, 92, int(200 * a)), width=max(1, int(2 * k)))
    d.line((px, y0 - int(8 * k), px, y0 + int(8 * k)), fill=(255, 178, 92, A), width=max(1, int(3 * k)))
    def spaced(x, y, s, f, fill, right=False):
        w = sum(f.getlength(ch) + 3 * k for ch in s)
        x = x - w if right else x
        for ch in s: d.text((x, y), ch, font=f, fill=fill); x += f.getlength(ch) + 3 * k
    pill = ss(sec("V2")['s'] + 0.3, sec("V2")['s'] + 0.6, t) * (1 - ss(sec("V2")['s'] + 5.8, sec("V2")['s'] + 6.4, t)) if not v else 0
    al = 1 - pill; dimL = dim[:3] + (int(dim[3] * al),); fullL = full[:3] + (int(full[3] * al),)
    spaced(mx, top, "GRACE PERIOD", fl, dimL)
    g = grace(t); spaced(mx, top + int(26 * k), f"00:{g:05.2f}", fb, fullL)
    spaced(W - mx, top, "RUNNING PROCESSES", fl, dim, right=True)
    spaced(W - mx, top + int(26 * k), f"{processes(t):,}", fb, full, right=True)
    st = status_at(t)
    if v: spaced(mx, top + int(76 * k), st, fs, (255, 178, 92, int(230 * a)))
    else: spaced(mx + int(250 * k), top + int(30 * k), st, fs, (255, 178, 92, int(230 * a * al)))
    return np.asarray(im)

# ================================================================ lyrics (big condensed type: sung = cream, singing = amber glow, coming = outline)
def lyric_size(W, H): return int((104 if vert(W, H) else 118) * ts(W, H))

def wrap_words(words, f, maxw, sp_):
    rows = [[]]; wcur = 0
    for w in words:
        ww = f.getlength(w)
        if rows[-1] and wcur + sp_ + ww > maxw: rows.append([]); wcur = 0
        if rows[-1]: wcur += sp_
        rows[-1].append(w); wcur += ww
    return rows

@lru_cache(256)
def line_sprite(li, cur, W, H):
    """RGBA sprite of line li with words < cur sung, == cur singing, > cur coming."""
    L = LN[li]; words = [w.upper() for w in L['words']]
    fs = lyric_size(W, H); maxw = W * (0.88 if vert(W, H) else 0.86)
    f = _font(F_LYR, fs)
    while True:
        rows = wrap_words(words, f, maxw, fs * 0.28)
        widest = max(sum(f.getlength(w) for w in r) + fs * 0.28 * (len(r) - 1) for r in rows)
        if (len(rows) <= (3 if vert(W, H) else 2) and widest <= maxw) or fs < 48: break
        fs -= 4; f = _font(F_LYR, fs)
    sp_ = fs * 0.28; lh = int(fs * 1.12); pad = int(fs * 0.6)
    widths = [sum(f.getlength(w) for w in r) + sp_ * (len(r) - 1) for r in rows]
    Wd = int(max(widths) + 2 * pad); Hd = int(lh * len(rows) + 2 * pad)
    fill = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0)); df = ImageDraw.Draw(fill)
    glow = Image.new("L", (Wd, Hd), 0); dg = ImageDraw.Draw(glow)
    shadow = Image.new("L", (Wd, Hd), 0); ds = ImageDraw.Draw(shadow)
    k = 0; sw = max(2, int(fs / 42))
    for r, row in enumerate(rows):
        x = (Wd - widths[r]) / 2; y = pad + r * lh
        for w in row:
            if k < cur: df.text((x, y), w, font=f, fill=CREAM + (255,)); ds.text((x, y), w, font=f, fill=200)
            elif k == cur:
                df.text((x, y), w, font=f, fill=AMBER + (255,)); dg.text((x, y), w, font=f, fill=255); ds.text((x, y), w, font=f, fill=200)
            else:
                df.text((x, y), w, font=f, fill=CREAM + (70,), stroke_width=sw, stroke_fill=CREAM + (205,)); ds.text((x, y), w, font=f, fill=150)
            x += f.getlength(w) + sp_; k += 1
    g = cv2.GaussianBlur(np.asarray(glow, F32) / 255, (0, 0), fs * 0.16)
    s = cv2.GaussianBlur(np.asarray(shadow, F32) / 255, (0, 0), fs * 0.22)
    return np.asarray(fill, F32) / 255, g, s

def lyric_pos(li, W, H):
    """chorus lines alternate above/below the eye like titles; everything else sits low."""
    sec_ = LN[li]['sec']; v = vert(W, H)
    eye_sec = sec_ in ("CH1", "CH2", "FINAL") or sec_ == "INTRO"
    if eye_sec and sec_ != "INTRO":
        first = [i for i, l in enumerate(LN) if l['sec'] == sec_][0]
        if (li - first) % 2 == 0: return W / 2, H * (0.215 if v else 0.168)
    return W / 2, H * (0.755 if v else 0.85)

def lyrics(rgb, t, W, H):
    if C.STATE["clean"]: return rgb
    flt = C.STATE["lyric_filter"]
    out = rgb.astype(F32) / 255
    for li, L in enumerate(LN):
        nxt = LN[li + 1]['s'] if li + 1 < len(LN) else 1e9
        pos = lyric_pos(li, W, H)
        prev_same = li > 0 and lyric_pos(li - 1, W, H) == pos and LN[li - 1]['e'] + 0.5 > L['s'] - 0.35
        next_same = li + 1 < len(LN) and lyric_pos(li + 1, W, H) == pos
        i0, i1 = (L['s'] - 0.02, L['s'] + 0.12) if prev_same else (L['s'] - 0.35, L['s'] - 0.05)
        o0, o1 = (min(L['e'] + 0.2, nxt - 0.14), min(L['e'] + 0.5, nxt - 0.02)) if next_same else (min(L['e'] + 0.2, nxt - 0.05), min(L['e'] + 0.5, nxt + 0.15))
        if not (i0 <= t <= o1): continue
        if flt is not None and not flt(L): continue
        if L['s'] >= T_END - 0.3: continue                                           # the end card says it
        cur = sum(1 for wt in L['wt'] if wt <= t) - 1
        if t > L['e']: cur = len(L['words'])
        fill, glow, shadow = line_sprite(li, max(cur, -1), W, H)
        a = ss(i0, i1, t) * (1 - ss(o0, o1, t))
        if a <= 0.01: continue
        cx, cy = pos; cy += (1 - ss(i0, i1 + 0.1, t)) * 18 * ts(W, H)
        h, w = shadow.shape; x0 = int(cx - w / 2); y0 = int(cy - h / 2)
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        if xb <= xa or yb <= ya: continue
        sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0)); reg = out[ya:yb, xa:xb]
        reg *= (1 - 0.72 * a * np.clip(shadow[sl] * 1.6, 0, 1))[..., None]
        reg += (glow[sl] * 0.85 * a)[..., None] * np.array([1.0, 0.55, 0.18], F32)
        fa = fill[sl][..., 3:4] * a
        reg[:] = reg * (1 - fa) + fill[sl][..., :3] * fa
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

# ================================================================ frame
RENDER_SCALE_9x16 = 0.75     # the vertical master renders its 3-D layer at 75% and scales it up; grain, HUD and type stay full-res

def render_frame(t, W=1920, H=1080, fi=0):
    k = RENDER_SCALE_9x16 if vert(W, H) else 1.0
    if k < 1.0:
        w2, h2 = int(round(W * k / 2) * 2), int(round(H * k / 2) * 2)
        img = cv2.resize(hdr_at(t, w2, h2), (W, H), interpolation=cv2.INTER_CUBIC)
        img = np.maximum(img, 0)
    else:
        img = hdr_at(t, W, H)
    out = sp.develop(img, exposure=1.0, fi=fi)
    out = hud(out, t, W, H)
    out = lyrics(out, t, W, H)
    if not C.STATE["clean"]:
        f = out.astype(F32) / 255
        C.subscribe_pill(f, t, W, H, sec("V2")['s'] + 0.6, 5.5)
        C.end_screen(f, t, W, H, T_END, DUR - T_END, "You did everything right.", sub_line="Subscribe for a new song every week",
                     title="Graceful Shutdown", accent=C.hexc('ffb25c'))
        out = (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)
    return out
