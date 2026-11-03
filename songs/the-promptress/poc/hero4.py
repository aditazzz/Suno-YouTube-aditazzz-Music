"""V4 hero sequence (song 4.44-23.10, 18.7 s; V3 is frozen in poc/v3_frozen/).
Beats: 1 the real moon (a tiny figure walks across its face) -> 2 it opens: her clouds pass the lens, the opening's
light spills onto the real clouds around it, the world inside has its own parallax -> 3 she stands before the
moon-door; a slow push to her as she lifts her arm -> CUT on the 14.86 downbeat -> 4 the door, still; her hand comes
in and reaches through to the moon; a held beat with the moonlight on her fingertips -> 5 thumb and index close, the
moon tears free of its sky and is carried out through the surface exactly on the 16.95 drop -> 6 that world loses
its light (its clouds lose their silver, the door's light on her hand dies, the moon now lights her hand) -> CUT
17.97 wide: the door is dark, she is lit by the moon in her hand, her shadow has moved -> 7 pull back out through
the moon to the real night: the moon has gone dark but for one point of light, and the silver drains out of the
real clouds around it.
usage: python3 poc/hero4.py <out_dir> [first last] [--still t,t,...]"""
import os, sys, math, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
import portal as P
import portal2 as P2
import wkit as K, scenes as S, door2 as D, witch2
from witch2 import raster2, rimlight
from witch_back import back_figure
from witch import stroke, bez
from hand4 import hand4
D.DRAIN = 2; D.HOLEFILL = "patch"; D.MENISCUS = 0.10; D.HALO = 0.07; witch2.HAIR_SOFT = 0.0022
W, H = K.W, K.H; HD = P2.HD; RM = P2.RM; FPS = 30.0
eio, ein2, eout2, eout4, lin, keys = P2.eio, P2.ein2, P2.eout2, P2.eout4, P2.lin, P2.keys
T0, T1 = 4.44, 23.10
T_PASS, T_CUT, T_TAKE, T_DROP, T_BACK, T_EXIT = 12.82, 14.86, 16.55, 16.95, 17.97, 19.02
HZ3 = 0.78 * H
XD, ZD, RD = 0.0, 34.0, 7.0
XW = -0.55
R_HOLD = RM * 2.0
R_KEYS = [(4.44, R_HOLD, lin), (8.64, R_HOLD * 1.07, lin), (11.7, HD * 0.50, ein2), (12.82, HD * 1.04, eout2), (T_EXIT, HD * 1.04, lin),
          (21.5, R_HOLD * 1.12, eio), (23.10, R_HOLD * 1.06, lin)]
G_KEYS = [(4.44, (0.5 * W, 0.44 * H), lin), (8.64, (0.5 * W, 0.44 * H), lin), (12.82, (0.5 * W, 0.5 * H), eio), (T_EXIT, (0.5 * W, 0.5 * H), lin),
          (21.5, (0.53 * W, 0.40 * H), eio), (23.10, (0.53 * W, 0.395 * H), lin)]
Z_KEYS = [(4.44, -16.0, lin), (8.64, -16.0, lin), (12.82, -6.0, ein2), (T_CUT, 8.0, eout2), (T_BACK - 0.001, 8.0, lin), (T_BACK, 3.0, lin),
          (T_EXIT, 2.2, lin), (21.5, -16.0, eio), (23.10, -16.5, lin)]

def plate_time(t): return 10.3 + (t - 4.44) * 0.82 if t < 15.0 else 10.4 + (t - 16.95)
def m_of(t, r): return 1.0 if t >= T_DROP else eio((r - RM * 2.25) / (RM * 3.6))
def fly(t, r):
    x = math.log(r / (HD * 0.75)); w = math.exp(-(x / 0.35) ** 2)
    if t < 13.4: return 0.40 * w
    if 19.2 < t < 22.0: return 0.40 * w
    return 0.0
def her_z(t): return 9.0 + 6.0 * eio((t - 5.0) / 7.0)
def walking(t): return 1.0 if 5.0 < t < 12.0 else 0.0
def rel(t): return 1 - 0.88 * eio((t - 16.62) / 1.8)          # how much light that world still has
def cam_at(t): return K.cam(z=float(keys(t, Z_KEYS)), x=0.0, hz=HZ3)
MOONCOL = np.array([0.95, 0.94, 0.88], np.float32)

def cast(img, a, org, sdir, k, hz):
    if k <= 0.01: return img
    org = np.asarray(org, float)
    Msh = np.float32([[1, sdir[0], -sdir[0] * org[1]], [0, sdir[1], org[1] * (1 - sdir[1])]])
    s = cv2.warpAffine(a, Msh, (W, H)); s = cv2.GaussianBlur(s, (0, 0), 2.5); s[:max(0, int(hz))] = 0
    return img * (1 - k * s[..., None])

_moon08 = None
def moon_sprite(img, c, r, glow, gain=1.15, tint=None, tint_k=0.0):
    global _moon08
    if _moon08 is None:
        mx, my, mr = D.MOON08; R = int(mr * 1.3); _moon08 = D._p08[int(my) - R:int(my) + R, int(mx) - R:int(mx) + R].copy()
    R0 = _moon08.shape[0] / 2; s = r / D.MOON08[2]
    M = np.float32([[s, 0, c[0] - s * R0], [0, s, c[1] - s * R0]])
    spr = cv2.warpAffine(_moon08, M, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    spr = np.clip(spr * gain, 0, 1)
    if tint is not None: spr = spr * (1 - tint_k) + np.asarray(tint, np.float32) * tint_k
    yy, xx = np.ogrid[0:H, 0:W]; d = np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2) / max(r, 1e-3)
    a = np.clip((1.0 - d) * max(r, 1) / 1.2 + 0.5, 0, 1)[..., None]
    out = img * (1 - a) + spr * a
    return out + (glow * np.exp(-np.clip(d - 1, 0, None) / 0.6) * (d > 1))[..., None] * np.array([0.85, 0.92, 1.0], np.float32)

# ------------------------------------------------------------------ beats 3 and 6: wide, inside
def approach(t):
    c = cam_at(t); hz = c["hz"]; after = t >= T_DROP
    img = K.sky_grad((0.022, 0.024, 0.030), (0.08, 0.09, 0.11), (0.15, 0.16, 0.19), hz=hz)
    g, d = K.ground(tint=(0.62, 0.70, 0.80), haze=(0.13, 0.14, 0.17), haze_m=300.0, exposure=1.10, c=c)
    img = np.where((d < 1e8)[..., None], g, img)
    img = K.fog_band(img, hz + 4, 40, 0.6, (0.15, 0.16, 0.19), scale=2.2, offset=0.2, name="cloudframe_46", soft=0.8)
    fb, fk = K.project(c, -26.0, 70.0); fr = 3.2 * fk
    if fr > 2: img, _ = D.draw(img, fb[0], fb[1] - fr, fr, t, interior_scale=1.3, fog=0.0, spill=0.5)
    base, k = K.project(c, XD, ZD); r = RD * k
    r_ref = RD * K.project(K.cam(z=-16.0, hz=HZ3), XD, ZD)[1]
    isc = 1.35 * (r_ref / r) ** 0.45; rl = rel(t)
    img, info = D.draw(img, base[0], base[1] - r, r, t, interior_scale=isc, slide=(0, r * 0.02), ground_y=base[1], fog=0.4 + 0.6 * rl,
                       spill=1.2, moon_left=0.0 if after else 1.0, relight=rl)
    z = her_z(t); approach.held = None
    if z - c["z"] < 0.5: return S.dof(img, c)
    fig = back_figure(t=t, reach_u=1.0 if after else eio((t - 14.25) / 0.62), wind=0.7, walk=walking(t))
    feet, kk = K.project(c, XW, z); hgt = 1.7 * kk; org = np.array(feet, float)
    a, sh = raster2(fig, org, hgt, (H, W))
    img = cast(img, a, org, (0.12, -0.6), 0.6 * (rl if after else 1.0), hz)          # the door's light throws her shadow at us
    ys, xs = np.ogrid[0:H, 0:W]
    if after:
        tip = org + fig["A"]["hand_tip"] * hgt + np.array([0, -0.010 * hgt])
        img = cast(img, a, org, (-0.30, -0.16), 0.50, hz)                             # the moon above her: a short shadow at her feet
        pool = np.exp(-(((xs - org[0]) / (hgt * 0.75)) ** 2 + ((ys - org[1]) / (hgt * 0.10)) ** 2)) * (ys > hz)
        img = img + pool[..., None] * MOONCOL * 0.16
    w_ = max(hgt / 260, 0.8); dcol = np.array(info["col"], np.float32) * 1.3 * (rl if after else 1.0)
    rim = np.maximum(rimlight(a, (0, -1), w_, 1.6), 0.6 * np.maximum(rimlight(a, (1, 0), w_, 1.3), rimlight(a, (-1, 0), w_, 1.3)))
    col = K.INK + (img - K.INK) * (sh * 0.42)[..., None]
    out = img * (1 - a[..., None]) + col * a[..., None] + rim[..., None] * dcol
    if after:
        dd = np.sqrt((xs - tip[0]) ** 2 + (ys - tip[1]) ** 2)
        lm = np.exp(-dd / (hgt * 0.28)).astype(np.float32)
        mdir = tip - (org + np.array([0, -0.6 * hgt]))
        out = out + (a * lm)[..., None] * MOONCOL * 0.10 + (rimlight(a, (mdir[0], mdir[1]), w_, 1.8) * np.clip(lm * 3, 0, 1))[..., None] * MOONCOL * 1.3
        out = moon_sprite(out, tip, max(0.026 * hgt, 2.5), 0.45)
        approach.held = tip
    return S.dof(out, c)

# ------------------------------------------------------------------ beats 4, 5, 6: the close-up
_bg = None
def closeup_bg():
    global _bg
    if _bg is None:
        c = K.cam(hz=0.55 * H, F=K.F * 1.6)
        img = K.sky_grad((0.020, 0.022, 0.028), (0.07, 0.08, 0.10), (0.12, 0.13, 0.16), hz=c["hz"])
        g, d = K.ground(tint=(0.55, 0.62, 0.72), haze=(0.11, 0.12, 0.15), haze_m=200.0, exposure=1.0, c=c)
        img = np.where((d < 1e8)[..., None], g, img)
        _bg = cv2.GaussianBlur(img, (0, 0), 14)
    return _bg.copy()

DCX, DCY, DR, ELL, ISC = 0.70 * W, 0.62 * H, 0.66 * H, 0.60, 1.30
S_ = 0.24 * W / 0.085
def slide(t): return (-(t - T_CUT) * 30, DR * 0.05)
def home(t): return D.moon_home(DCX, DCY, DR, t, slide(t), ELL, ISC)
def rr_of(p): return math.hypot((p[0] - DCX) / (DR * ELL), (p[1] - DCY) / DR)

_mp = None
def moon_path(t):
    """the moon's centre once she has it: torn free at T_TAKE, through the surface exactly on the drop, then lifted"""
    global _mp
    if _mp is None:
        h0, _ = home(T_TAKE); pout = np.array([0.42 * W, 0.66 * H]); plift = np.array([0.40 * W, 0.56 * H])
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if rr_of(h0 + (pout - h0) * mid) < 1.0: lo = mid
            else: hi = mid
        B = h0 + (pout - h0) * lo
        _mp = [(T_TAKE, tuple(h0), lin), (T_DROP, tuple(B), ein2), (17.40, tuple(pout), eout2), (T_BACK, tuple(plift), eio)]
    return np.array(keys(t, _mp), float)

def hand_pose(t):
    ang = -50 + 3 * math.sin(t * 1.1) + 16 * eio((t - T_TAKE) / 0.9)
    d3 = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    pin = 0.35 * eio((t - 15.75) / 0.55) + 0.65 * eio((t - 16.30) / 0.25)
    sp = 0.7 * (1 - eio((t - 15.2) / 0.6))
    return d3, pin, sp

_fg = None
def fg_wisps(img, t, lightcol, k):
    """her clouds, out of focus, drifting between us and the hand (the close-up shares the world's air)"""
    global _fg
    if _fg is None:
        d = K.cloud_tex("cloudframe_40"); _fg = cv2.GaussianBlur(d, (0, 0), 6)
    th, tw = _fg.shape
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    u = ((xs / W) * 0.55 + t * 0.018) % 1 * (tw - 1); v = np.clip(ys / H * 0.55 + 0.22, 0, 0.999) * (th - 1)
    dens = cv2.remap(_fg, u, v, cv2.INTER_LINEAR)
    dens = np.clip((dens - 0.48) * 2.2, 0, 1) * np.clip(1.15 - ys / H, 0, 1)
    a = (dens * k)[..., None]
    return img * (1 - a) + lightcol * a

def closeup(t):
    img = closeup_bg(); rl = rel(t)
    hm, pmr = home(t)
    d3, pin, sp = hand_pose(t)
    off = hand4(np.zeros(2), d3, pin, S_, pmr)["mc"]
    taken = t >= T_TAKE
    target = moon_path(t) if taken else hm
    wt = target - off
    if t < 15.75:
        u = eout2((t - 14.98) / 0.77); start = wt + np.array([-0.22 * W, 0.70 * H])
        nrm = np.array([-(wt - start)[1], (wt - start)[0]]); nrm /= np.linalg.norm(nrm) + 1e-9
        wr = start + (wt - start) * u + nrm * math.sin(math.pi * u) * 0.04 * H
    else:
        wr = wt + np.array([0.0, 1.5 * math.sin(t * 2.1)]) * (not taken)
    hd = hand4(wr, d3, pin, S_, pmr, spread=sp); mc = hd["mc"]
    # where the moon is drawn: home until she takes it; then with her fingers, lagging a breath as it tears free
    if taken:
        h0, _ = home(T_TAKE); mp = moon_path(t)
        moon = mp + (h0 - mp) * math.exp(-(t - T_TAKE) / 0.08) * 0.30
    else:
        moon = hm
    # the door (its picture has no moon of its own: the moon is a body in that world's air, not a printed image)
    ripple = None
    if 15.22 <= t < T_TAKE: ripple = (DCX - DR * ELL * 0.97, hm[1] + 60, t - 15.22)
    elif T_TAKE + 0.03 <= t < T_DROP: ripple = (hm[0], hm[1], t - T_TAKE - 0.03)
    elif t >= T_DROP: B = moon_path(T_DROP); ripple = (B[0], B[1], t - T_DROP)
    img, info = D.draw(img, DCX, DCY, DR, t, ellipse=ELL, interior_scale=ISC, slide=slide(t), moon_left=0.0, relight=rl,
                       ground_y=H * 1.25, fog=0.35, spill=0.8, ripple=ripple)
    ys, xs = np.ogrid[0:H, 0:W]
    if taken:   # where it was: a faint residual glow in the darkening clouds
        g0 = 0.12 * math.exp(-(t - T_TAKE) / 0.8); hh, _ = home(t)
        gd = np.sqrt((xs - hh[0]) ** 2 + (ys - hh[1]) ** 2) / (pmr * 1.4)
        img = img + (np.exp(-gd ** 2) * info["m"] * g0)[..., None] * np.array([0.75, 0.84, 0.95], np.float32)
    inside = t < T_DROP
    flash = 0.45 * math.exp(-((t - T_DROP) / 0.07) ** 2)
    img = moon_sprite(img, moon, pmr, 0.14 + (0.06 if not inside else 0.0) + flash, gain=1.06 if inside else 1.12,
                      tint=np.array(info["col"], np.float32), tint_k=0.12 if inside else 0.0)
    # her arm: a fitted dark sleeve to the wrist, a chiffon ruffle at the cuff and a few long chiffon ribbons trailing
    # in the air (thin, moving fabric; no flat translucent slabs). The forearm is nearer the lens and softer.
    n3 = np.array([-d3[1], d3[0]]); n3 = n3 if n3[1] > 0 else -n3
    el = wr - d3 * 0.30 * S_ + np.array([0.0, 0.03 * S_])
    armp = bez(el, el + (wr - el) * 0.35 + n3 * 0.012 * S_, wr - d3 * 0.08 * S_ + n3 * 0.004 * S_, wr - d3 * 0.036 * S_, 18)
    arm = stroke(armp, 0.034 * S_, 0.0148 * S_)
    cf = wr - d3 * 0.042 * S_
    sheer = []
    for i in range(6):          # the ruffle: short petals of chiffon around the cuff, each fluttering on its own
        th_ = -1.9 + i * 0.55 + 0.12 * math.sin(t * 4.1 + i * 1.7)
        dirv = -d3 * math.cos(th_) * 0.5 + n3 * math.sin(th_)
        L = (0.028 + 0.008 * math.sin(i * 2.3)) * S_
        p0 = cf + n3 * (0.006 * S_) * math.sin(th_)
        tipp = p0 + dirv * L + np.array([0, 0.004 * S_])
        side = np.array([-dirv[1], dirv[0]]) * L * 0.35
        petal = np.vstack([bez(p0, p0 + dirv * L * 0.4 + side, tipp + side * 0.3, tipp, 8), bez(tipp, tipp - side * 0.3, p0 + dirv * L * 0.4 - side, p0, 8)[1:]])
        pass   # (petals read as wings at this framing: left out)
    for i in range(3):          # ribbons trailing back and down from the cuff
        ss_ = np.linspace(0, 1, 30)[:, None]
        path = cf + (-d3 * 0.12 * S_) * ss_ + np.array([0, 1.0]) * (0.13 * S_) * ss_ ** 1.4 \
               + n3 * (0.022 * S_) * np.sin(t * 2.3 - ss_ * 6 + i * 2.1) * ss_ + n3 * (0.010 * S_ * (i - 1))
        pass   # (ribbons read as flat strips in this framing: left out of V4)
    fig = dict(solid=[arm] + hd["solid"], sheer=sheer, hair=[])
    a, sh = raster2(fig, np.zeros(2), 1.0, (H, W))
    dist = ((xs - wr[0]) * -d3[0] + (ys - wr[1]) * -d3[1]) / S_
    wdef = np.clip((dist - 0.06) / 0.14, 0, 1).astype(np.float32)
    a = a * (1 - wdef) + cv2.GaussianBlur(a, (0, 0), 5) * wdef; sh = sh * (1 - wdef) + cv2.GaussianBlur(sh, (0, 0), 5) * wdef
    # lighting: the other world's light (dies with it), the moon (near her fingers, then in them), the air around
    pre = img
    ink = K.INK + np.array(info["col"], np.float32) * 0.035
    col = ink + (img - ink) * (sh * 0.45)[..., None]
    dmn = np.sqrt((xs - moon[0]) ** 2 + (ys - moon[1]) ** 2) / pmr
    lm = np.exp(-(np.clip(dmn - 1, 0, None) / 1.4) ** 1.2).astype(np.float32)
    ms = (0.15 + 0.85 * eio((t - 15.45) / 0.5)) * (1.0 if inside else 1.5)
    out = pre * (1 - a[..., None]) + col * a[..., None]
    out = out + (a * lm * 0.13 * ms)[..., None] * MOONCOL
    out = out + (rimlight(a, (moon[0] - wr[0], moon[1] - wr[1]), 2.2, 1.0) * np.clip(lm * 1.6, 0, 1) * ms)[..., None] * MOONCOL * 0.50
    out = out + rimlight(a, (DCX - wr[0], DCY - wr[1]), 2.4, 1.0)[..., None] * np.array(info["col"], np.float32) * (0.15 + 0.55 * rl)
    insid = info["m"] * a * (rl ** 0.7)
    out = out + (rimlight(insid, (0.9, -0.2), 3.0, 1.2) * info["m"])[..., None] * np.array([0.78, 0.86, 0.95], np.float32) * 0.7
    band = np.exp(-((info["rr"] - 1.0) * DR / 3.0) ** 2)
    touch = cv2.GaussianBlur(cv2.dilate(a, np.ones((11, 11), np.uint8)) * band, (0, 0), 4) * (1 - a)
    out = out + touch[..., None] * np.array([0.85, 0.92, 1.0], np.float32) * 0.7 * (0.3 + 0.7 * rl)
    lw = a * np.clip(1 - cv2.GaussianBlur(a, (0, 0), 6), 0, 1)
    out = out + lw[..., None] * cv2.GaussianBlur(pre, (0, 0), 10) * 0.55
    lightc = np.array(info["col"], np.float32) * (0.35 + 0.65 * rl) + MOONCOL * 0.10 * (not inside)
    out = out + (sh * 0.9)[..., None] * lightc * (0.35 + 0.65 * np.clip(1 - wdef, 0, 1))[..., None] + rimlight(sh, (DCX - wr[0], DCY - wr[1]), 3.0, 1.0)[..., None] * lightc * 0.6
    out = fg_wisps(out, t, lightc * 0.55, 0.10)
    closeup.held = None
    return out

def hero_world(t):
    return closeup(t) if T_CUT <= t < T_BACK else approach(t)

# ------------------------------------------------------------------ the camera through the real moon (from portal2.render)
def hold_shadow(out, t, Cm, r, dm):
    c = cam_at(t); feet, kk = K.project(c, XW, her_z(t)); k = r / HD
    sp = Cm + (feet - np.array([W / 2, H / 2])) * k
    fig = back_figure(t=t, reach_u=0.0, wind=0.6, walk=walking(t), strands=120)
    a, _ = raster2(fig, sp, 1.7 * kk * k, (H, W))
    return out * (1 - 0.8 * (a * dm)[..., None])

_fgc = {}
def fg_clouds(out, t, C, cm_col):
    """beat 2: two banks of her clouds pass the lens on the way in (much faster than the moon grows: near, out of focus)"""
    for name, t0, dur, offv in (("cloudframe_30", 9.5, 2.9, (-0.30, 0.22)), ("cloudframe_34", 10.5, 2.3, (0.28, -0.20))):
        u = (t - t0) / dur
        if not 0 < u < 1: continue
        if name not in _fgc: _fgc[name] = K.cloud_tex(name)
        if name + "w" not in _fgc:
            d0 = _fgc[name]; th, tw = d0.shape
            wy = np.sin(np.linspace(0, math.pi, th))[:, None] ** 1.5; wx = np.sin(np.linspace(0, math.pi, tw // 2))[None, :] ** 1.5
            _fgc[name + "w"] = np.ascontiguousarray((d0[:, :tw // 2] - 0.38) * 3.2 * wy * wx + 0.38)
        d = _fgc[name + "w"]; th, tw = d.shape; tw *= 2
        sc = 0.45 * math.exp(2.6 * u)                                     # layer width in frame widths
        cx = C[0] + offv[0] * W * math.exp(1.6 * u); cy = C[1] + offv[1] * H * math.exp(1.6 * u)
        s = sc * W / (tw * 0.5)
        M = np.float32([[s, 0, cx - s * tw * 0.25], [0, s, cy - s * th * 0.5]])
        dens = cv2.warpAffine(d, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0.38)
        dens = cv2.GaussianBlur(dens, (0, 0), 3 + 16 * u)
        dens = np.clip((dens - 0.40) * 2.5, 0, 1)
        ys, xs = np.ogrid[0:H, 0:W]
        lit = np.exp(-np.sqrt((xs - C[0]) ** 2 + (ys - C[1]) ** 2) / (0.45 * W))[..., None]
        colr = np.array([0.10, 0.11, 0.13], np.float32) + lit * cm_col * 0.75
        a = (dens * 0.55 * math.sin(math.pi * u) ** 0.8)[..., None]
        out = out * (1 - a) + colr * a
    return out

DRAIN_T = 19.4; POST = None
SKY_REF = np.array([0.198, 0.168, 0.150], np.float32)   # measured on the held frame (t=4.44), annulus 1.3-1.7 moon radii
def render(t, check=None):
    r = float(keys(t, R_KEYS, log=True)); C = np.array(keys(t, G_KEYS), float)
    pt = plate_time(t); j = int(np.clip((pt - P.PT0) * P.PFPS, 0, len(P.TR) - 1))
    lock = eio((t - 7.5) / 2.5); follow = 0.45 + 0.55 * lock
    mx = P.sx[j] + follow * (P.cx[j] - P.sx[j]); my = P.sy[j] + follow * (P.cy[j] - P.sy[j])
    S_p = r / RM; Cm = C + S_p * np.array([P.cx[j] - mx, P.cy[j] - my])
    out = np.zeros((H, W, 3), np.float32)
    if r < HD * 2.6:
        dl = abs(math.log(float(keys(t + 1 / FPS, R_KEYS, log=True))) - math.log(r)); n = 1 if dl < 0.004 else 7
        Pl = P.plate(j); acc = np.zeros_like(out)
        for k in range(n):
            s = S_p * math.exp(-dl * 0.9 * k / max(n - 1, 1)) if n > 1 else S_p
            M = np.float32([[s, 0, C[0] - s * mx], [0, s, C[1] - s * my]])
            acc += cv2.warpAffine(Pl, M, (W, H), flags=cv2.INTER_CUBIC if s < 6 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        out = acc / n / 255.0
        out = out * np.array([1.06, 1.0, 0.95]) * 0.95 + np.array([0.012, 0.006, 0.0])
        hi = np.clip((out.mean(2, keepdims=True) - 0.35) / 0.4, 0, 1); out = out * (1 - hi) + out * np.array([0.90, 0.97, 1.06]) * hi
        out = out.astype(np.float32)
    m = m_of(t, r)
    ys, xs = np.ogrid[0:H, 0:W]; rho = np.sqrt((xs - Cm[0]) ** 2 + (ys - Cm[1]) ** 2) / r
    dm = np.clip((1 - rho) * r / (1.2 + 2.0 * (r < 400)) + 0.5, 0, 1).astype(np.float32)
    lim = 1.0 - 0.80 * eio((r - RM * 3.2) / (RM * 3.5))
    global SKY_REF
    if SKY_REF is None:   # the sky next to the moon, measured once on the held frame (a stable reference, no flicker)
        SKY_REF = np.array([0.075, 0.085, 0.11], np.float32) if r > RM * 2.5 else np.percentile(out[(rho > 1.3) & (rho < 1.7)], 45, axis=0)
    if lim < 0.999 and m_of(t, r) > 0.001:   # the plate moon's limb never peeks around the window; it settles to the sky around it, not black
        sky = SKY_REF
        ring = (np.clip((rho - 0.97) / 0.05, 0, 1) * np.clip((1.35 - rho) / 0.2, 0, 1) * m_of(t, r))[..., None]
        out = out - ring * np.clip(out - sky, 0, None) * (1 - lim) / 0.8
    after = t >= T_DROP
    inner_col = np.array([0.55, 0.62, 0.72], np.float32)
    if m > 0.001:
        wimg = hero_world(t); k = r / HD
        px_, py_ = int(W * 0.35), int(H * 0.62)
        big = np.pad(wimg, ((0, 0), (px_, px_), (0, 0)), mode="reflect")
        big = np.pad(big, ((py_, py_), (0, 0), (0, 0)), mode="edge")
        if k < 1:
            small = cv2.resize(big, (max(1, int(big.shape[1] * k)), max(1, int(big.shape[0] * k))), interpolation=cv2.INTER_AREA)
            M2 = np.float32([[1, 0, Cm[0] - small.shape[1] / 2], [0, 1, Cm[1] - small.shape[0] / 2]])
            wv = cv2.warpAffine(small, M2, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            wv = wv * (1 - 0.30 * np.clip((rho - 0.80) / 0.20, 0, 1))[..., None]
        else:
            M = np.float32([[k, 0, Cm[0] - k * big.shape[1] / 2], [0, k, Cm[1] - k * big.shape[0] / 2]])
            wv = cv2.warpAffine(big, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        far = 1 - eio((r - RM * 3) / (RM * 11))
        if far > 0.01:   # from outside, the moon's own face lies over the window (after the theft: a dark face)
            mot = cv2.GaussianBlur(out.mean(2), (0, 0), max(1.0, r * 0.03))
            sel = rho < 0.7
            mot = mot / (np.percentile(mot[sel], 80) + 1e-4) if sel.any() else mot
            lift = ((0.38 if not after else 0.16) * far) * np.clip(mot, 0, 1.2)[..., None] * np.array([0.80, 0.90, 0.95], np.float32)
            wv = wv + lift * (1 - wv)
            wv = wv * (1 - 0.25 * far * (rho ** 3)[..., None])
        held = getattr(approach, "held", None) if t >= T_BACK else None
        if held is not None and k < 0.8:   # the one point of light left in it: the moon in her hand
            p = Cm + (np.asarray(held) - np.array([W / 2, H / 2])) * k
            dp = np.sqrt((xs - p[0]) ** 2 + (ys - p[1]) ** 2)
            wv = wv + (np.exp(-(dp / 2.2) ** 2) * 1.0 + np.exp(-dp / 6.0) * 0.22)[..., None] * MOONCOL * min(1.0, (0.8 - k) / 0.4)
        if after: wv = wv * (0.30 + 0.70 * min(1.0, max(0.0, (k - 0.15) / 0.45)))   # seen from outside again: a dark moon
        a = (dm * m)[..., None]
        if after:   # nothing of the old bright limb may show around it
            ring = np.clip((1.20 - rho) / 0.12, 0, 1) * (rho > 0.96)
            out = out - (ring * 0.95)[..., None] * np.clip(out - 0.10, 0, None)
        out = out * (1 - a) + wv * a
        if not after:   # the opening's light falls on the real clouds around it (multiplicative: only where there is cloud)
            lum = out.mean(2)
            spill = m * np.exp(-np.clip(rho - 1, 0, None) / 0.45) * (rho > 1) * np.clip((lum - 0.05) / 0.3, 0, 1)
            out = out * (1 + 0.9 * spill[..., None] * inner_col)
    else:
        out = hold_shadow(out, t, Cm, r, dm)
    if t < T_PASS + 0.3:
        out = fg_clouds(out, t, Cm, inner_col)
    fa = fly(t, r)
    if fa > 0.01 and r < HD * 2.6:
        Pl = P.plate(j).astype(np.float32) / 255; s_ = S_p * 1.08
        M = np.float32([[s_, 0, C[0] - s_ * mx], [0, s_, C[1] - s_ * my]])
        cl = cv2.warpAffine(Pl, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        g = cv2.GaussianBlur(cl.mean(2), (0, 0), 3)
        dens = np.clip((g - cv2.GaussianBlur(g, (0, 0), 25)) * 14 - 0.10, 0, 1) ** 1.5
        dens = dens * np.clip((0.42 - cv2.GaussianBlur(g, (0, 0), 6)) / 0.15, 0, 1)      # not the moon's own limb
        edge = np.clip((rho - 0.62) / 0.38, 0, 1) * np.clip((1.25 - rho) / 0.25, 0, 1)
        a = np.clip(dens * edge * fa * 0.9, 0, 0.38)[..., None]
        cl_col = (0.18 + 1.1 * cl) * (np.array([0.92, 0.97, 1.03], np.float32) if not after else np.array([0.55, 0.60, 0.70], np.float32))
        out = out * (1 - a) + cl_col * a
    if t > DRAIN_T:    # beat 7: the silver drains out of the real clouds, outward from the moon
        front = 1.0 + 9.0 * eio((t - 19.4) / 3.0)
        wave = np.clip((front - rho) / 1.5, 0, 1) * (rho > 0.98)
        lum = out.mean(2)
        lit = np.clip((lum - 0.08) / 0.35, 0, 1)
        kk = (0.75 * wave * lit)[..., None]
        out = out * (1 - kk) + out.mean(2, keepdims=True) * np.array([0.70, 0.78, 0.95], np.float32) * 0.55 * kk
    fl = 0.08 * math.exp(-max(t - T_DROP, 0) / 0.08) * (t >= T_DROP - 1 / FPS)
    out = out * (1 + fl)
    if POST is not None: out = POST(out, t, Cm, r)
    if check is not None and T_CUT > t or (check is not None and t >= T_BACK):
        pass
    return K.finish(out, grain=0.026, vign=0.26, hal=0.20, seed=int(t * 1000) % 100000)

if __name__ == "__main__":
    ARGS = sys.argv[1:]; out_dir = ARGS[0]; os.makedirs(out_dir, exist_ok=True)
    if "--still" in ARGS:
        for ts in ARGS[ARGS.index("--still") + 1].split(","):
            t = float(ts); t0 = time.time()
            K.save(render(t), f"{out_dir}/still_{t:06.2f}.jpg"); print(f"t={t:.2f} {time.time() - t0:.1f}s")
        sys.exit()
    NF = int(round((T1 - T0) * FPS))
    a = int(ARGS[1]) if len(ARGS) > 1 else 0; b = int(ARGS[2]) if len(ARGS) > 2 else NF
    for f in range(a, min(b, NF)):
        p = f"{out_dir}/{f:04d}.jpg"
        if os.path.exists(p): continue
        K.save(render(T0 + f / FPS), p + ".tmp.jpg", q=95); os.replace(p + ".tmp.jpg", p)
