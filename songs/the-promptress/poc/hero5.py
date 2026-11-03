"""V5: a 28.9 s sequence (song 4.44-33.34: the intro and the 8-bar instrumental drop, ending as the first verse
begins). V4 is frozen in poc/v4_frozen/. Shots (cues from the recording):
 S1 4.44  your moon, still; a speck crosses its face, and on "...midnight query" (8.56) it is plainly a woman walking
 S2 8.64  the moon opens (V4 portal: your clouds pass the lens, its light on your clouds); through on the 12.82 downbeat
 S3 12.82 inside: she stands before the moon-door; she lifts her arm on "I asked the dark" (14.0)
 S4 14.86 CUT close-up (V4 gesture): reach, hold on "to answer me", the moon carried out on the 16.95 drop; that world goes
          dark on the same frame
 S5 17.97 CUT medium profile, camera still: she holds it at her face, lit by it; on 19.02 she lets it go up into the sky
 S6 21.01 CUT wide, camera still: on the four kicks 21.01/21.53/22.04/22.55 it divides 1>2>3>4>5; on 23.57 they settle
          into a row; on the eighths from 24.09 their faces fill in: your moving clouds, a spellbook, the moon, a tiny
          her, your heart branches
 S7 25.17 CUT medium close: she reaches for the tiny-her moon; during the fill (27.16-28.19) it comes to her hand on its
          own, landing on the 28.19 hit before her reach is done. She stops. Inside it, the tiny her reaches back.
 S8 29.22 CUT on the strongest hit: we fly backward out of her world, out through a moon, into your real sky. On the
          eighths 31.25/31.51/31.77/32.28 four small moons appear beside your moon. Hold; ends as "Grandma" begins.
usage: python3 poc/hero5.py <out_dir> [first last] [--still t,...]"""
import os, sys, math, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
_argv = sys.argv; sys.argv = [sys.argv[0]]
import hero4 as H4
sys.argv = _argv
import portal as P, wkit as K, door2 as D, witch2
from witch2 import raster2, rimlight, figure
from witch import stroke, bez
W, H = K.W, K.H; FPS = 30.0
eio, ein2, eout2, eout4, lin, keys = H4.eio, H4.ein2, H4.eout2, H4.eout4, H4.lin, H4.keys
T0, T1 = 4.44, 33.34
T_S5, T_REL, T_S6, T_ROW, T_FILL, T_S7, T_LAND, T_S8 = 17.97, 19.02, 21.01, 23.57, 24.09, 25.17, 28.19, 29.22
KICKS = [21.01, 21.53, 22.04, 22.55]
APPEAR = [31.25, 31.51, 31.77, 32.28]
MOONCOL = H4.MOONCOL
HD, RM, R_HOLD = H4.HD, H4.RM, H4.R_HOLD

# ---------------- S1-S4: V4's machinery, with the V5 changes ----------------
H4.her_z = lambda t: -10.0 + 25.0 * eio((t - 4.6) / 7.6)          # she starts nearer, so on the moon's face she reads as a woman
H4.rel = lambda t: 1 - 0.88 * eio((t - H4.T_DROP) / 0.07)         # the light goes out on the frame the moon leaves
H4.DRAIN_T = 999.0
H4.R_KEYS = [k for k in H4.R_KEYS if k[0] <= 17.97] + [(T_S8, HD * 1.04, lin), (31.0, R_HOLD * 1.10, eout4), (T1, R_HOLD * 1.05, lin)]
H4.G_KEYS = [k for k in H4.G_KEYS if k[0] <= 17.97] + [(T_S8, (0.5 * W, 0.5 * H), lin), (31.0, (0.40 * W, 0.47 * H), eout4), (T1, (0.395 * W, 0.468 * H), lin)]
_pt4 = H4.plate_time
H4.plate_time = lambda t: 12.0 + (t - T_S8) * 1.0 if t >= T_S8 else _pt4(t)
_fly4 = H4.fly
def _fly5(t, r):
    if t >= T_S8:
        x = math.log(r / (HD * 0.75)); return 0.40 * math.exp(-(x / 0.35) ** 2)
    return _fly4(t, r) if t < 13.4 else 0.0
H4.fly = _fly5

# ---------------- the world after the theft (S5-S8): her plain, the dark door, the far door ----------------
_bgc = {}
def plain_bg(key, hz, cx_shift, blur):
    if key in _bgc: return _bgc[key].copy()
    c = K.cam(z=-2.0, x=cx_shift, hz=hz)
    img = K.sky_grad((0.024, 0.026, 0.034), (0.085, 0.095, 0.115), (0.16, 0.17, 0.20), hz=c["hz"])
    g, d = K.ground(tint=(0.60, 0.68, 0.78), haze=(0.13, 0.14, 0.17), haze_m=300.0, exposure=1.05, c=c)
    img = np.where((d < 1e8)[..., None], g, img)
    img = K.fog_band(img, c["hz"] + 4, 40, 0.6, (0.15, 0.16, 0.19), scale=2.2, offset=0.2, name="cloudframe_46", soft=0.8)
    fb, fk = K.project(c, -26.0, 70.0); fr = 3.2 * fk
    if fr > 2: img, _ = D.draw(img, fb[0], fb[1] - fr, fr, 0.0, interior_scale=1.3, fog=0.0, spill=0.5)
    base, k = K.project(c, 0.0, 34.0); r = 7.0 * k
    img, _ = D.draw(img, base[0], base[1] - r, r, 0.0, interior_scale=1.3, slide=(0, r * 0.02), ground_y=base[1], fog=0.4, spill=1.2,
                    moon_left=0.0, relight=0.12)
    if blur > 0: img = cv2.GaussianBlur(img, (0, 0), blur)
    _bgc[key] = img
    return img.copy()

def glow(img, c, r, amt, col=MOONCOL, fall=1.6):
    ys, xs = np.ogrid[0:H, 0:W]; d = np.sqrt((xs - c[0]) ** 2 + (ys - c[1]) ** 2) / max(r, 1)
    return img + (amt * np.exp(-np.clip(d - 1, 0, None) / fall) * (d > 0.98))[..., None] * col

def mirror(fig):
    f = lambda p: np.asarray(p) * np.array([-1.0, 1.0])
    return dict(solid=[f(p) for p in fig["solid"]], sheer=[(f(p), a) for p, a in fig["sheer"]], hair=[(f(p), w) for p, w in fig["hair"]], A=fig["A"])

def draw_her(img, fig, org, hgt, light, light_col, rim_k=1.0, fill_k=0.10, ground_y=None, shadow_dir=None, haze=0.03):
    a, sh = raster2(fig, np.asarray(org, float), hgt, (H, W))
    if ground_y is not None and shadow_dir is not None: img = H4.cast(img, a, org, shadow_dir, 0.45, ground_y - 2)
    ctr = np.asarray(org, float) + np.array([0, -0.55 * hgt]); L = np.asarray(light, float) - ctr
    ys, xs = np.ogrid[0:H, 0:W]
    dl = np.sqrt((xs - light[0]) ** 2 + (ys - light[1]) ** 2)
    lm = np.exp(-dl / (0.30 * hgt)).astype(np.float32)
    ink = K.INK * (1 - haze) + np.array([0.14, 0.15, 0.18], np.float32) * haze
    col = ink + (img - ink) * (sh * 0.42)[..., None]
    w_ = max(hgt / 260, 0.8)
    rim = rimlight(a, L, w_ * 1.3, rim_k) * (0.35 + 0.65 * np.clip(lm * 2.5, 0, 1))
    lw = a * np.clip(1 - cv2.GaussianBlur(a, (0, 0), 5), 0, 1)
    out = img * (1 - a[..., None]) + col * a[..., None] + rim[..., None] * light_col + (a * lm * fill_k)[..., None] * light_col
    out = out + lw[..., None] * cv2.GaussianBlur(img, (0, 0), 8) * 0.45
    return out, a

# ---------------- the moon-tabs: small moons, each with something in it ----------------
_p01 = cv2.imread(f"{K.AS}/photo_01.jpg").astype(np.float32) / 255
_p14 = cv2.imread(f"{K.AS}/photo_14.jpg").astype(np.float32) / 255
_tex = cv2.imread("build/poc/moon_1976_stack.png", 0)
def _sq(im, cx_f=0.5, cy_f=0.45, frac=0.62):
    h, w = im.shape[:2]; s = int(min(h, w) * frac); x0 = int(w * cx_f - s / 2); y0 = int(h * cy_f - s / 2)
    x0 = max(0, min(w - s, x0)); y0 = max(0, min(h - s, y0)); return im[y0:y0 + s, x0:x0 + s]
_c14 = _sq(_p14, 0.5, 0.42, 0.75)

def book_patch(n, t):
    """an old spellbook, open, a page lifting, warm light behind it (a little of B's editorial warmth)"""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
    d = np.sqrt((xx - 0.5) ** 2 + (yy - 0.42) ** 2)
    img = (np.array([0.08, 0.13, 0.20], np.float32) + np.exp(-(d / 0.30) ** 2)[..., None] * np.array([0.38, 0.62, 0.80], np.float32))
    a = np.zeros((n, n), np.uint8); s = n
    sp = np.array([0.5, 0.70]) * s
    left = np.array([[0.5, 0.70], [0.18, 0.66], [0.15, 0.50], [0.30, 0.47], [0.5, 0.53]]) * s
    right = left * np.array([-1, 1]) + np.array([s, 0])
    cv2.fillPoly(a, [np.int32(left * 16)], 255, cv2.LINE_AA, 4); cv2.fillPoly(a, [np.int32(right * 16)], 255, cv2.LINE_AA, 4)
    cv2.fillPoly(a, [np.int32(np.array([[0.14, 0.67], [0.86, 0.67], [0.86, 0.71], [0.5, 0.74], [0.14, 0.71]]) * s * 16)], 255, cv2.LINE_AA, 4)
    ph = ((t * 0.55) % 1.0); ang = math.pi * eio(ph)                       # a page turning over, slowly
    ex = 0.5 + 0.34 * math.cos(ang); ey = 0.48 - 0.16 * math.sin(ang)
    page = np.array([[0.5, 0.53], [0.5 + (ex - 0.5) * 0.5, ey - 0.03], [ex, ey], [ex, ey + 0.13], [0.5 + (ex - 0.5) * 0.5, ey + 0.12], [0.5, 0.70]]) * s
    pa = np.zeros((n, n), np.uint8); cv2.fillPoly(pa, [np.int32(page * 16)], 255, cv2.LINE_AA, 4)
    af = a.astype(np.float32) / 255; pf = pa.astype(np.float32) / 255 * 0.75
    img = img * (1 - af[..., None]) + np.array([0.03, 0.035, 0.05], np.float32) * af[..., None]
    img = img * (1 - pf[..., None]) + np.array([0.28, 0.42, 0.55], np.float32) * pf[..., None]   # the lifted page catches the light
    return img

def witch_patch(n, t, reach):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
    d = np.sqrt((xx - 0.62) ** 2 + (yy - 0.35) ** 2)
    img = np.array([0.40, 0.34, 0.30], np.float32) + np.exp(-(d / 0.45) ** 2)[..., None] * np.array([0.62, 0.60, 0.56], np.float32)
    fig = mirror(figure(t=t, raise_u=reach, look_u=0.3 + 0.4 * reach, wind=0.8, strands=140, seed=5))
    a, sh = raster2(fig, np.array([n * 0.60, n * 0.93]), n * 0.78, (n, n))
    col = K.INK + (img - K.INK) * (sh * 0.42)[..., None]
    return img * (1 - a[..., None]) + col * a[..., None]

def content(kind, n, t, reach=0.0):
    if kind == "clouds":   # your real footage, moving
        j = int(np.clip((10.4 + (t % 7.5) - P.PT0) * P.PFPS, 0, len(P.TR) - 1))
        pl = P.plate(j).astype(np.float32) / 255; R = int(RM * 2.4); cx, cy = int(P.cx[j]), int(P.cy[j])
        crop = pl[max(0, cy - R):cy + R, max(0, cx - R):cx + R]
        return cv2.resize(crop, (n, n), interpolation=cv2.INTER_AREA) * 1.25
    if kind == "book": return book_patch(n, t)
    if kind == "moon":
        mx, my, mr = D.MOON08; R = int(mr * 1.05); return cv2.resize(D._p08[int(my) - R:int(my) + R, int(mx) - R:int(mx) + R], (n, n), interpolation=cv2.INTER_AREA) * 1.1
    if kind == "witch": return witch_patch(n, t, reach)
    if kind == "heart": return cv2.resize(_c14, (n, n), interpolation=cv2.INTER_AREA) * 1.15
    return np.zeros((n, n, 3), np.float32)

_tx = {}
def tab(img, c, r, kind, t, fill=1.0, blur=0.0, reach=0.0, halo=0.12, alpha=1.0):
    """a small moon with something inside it: content seen through a moon's face (limb darkening, your moon's mottling)"""
    if r < 1.0 or alpha <= 0: return img
    n = max(8, int(2 * r)); x0, y0 = int(round(c[0] - n / 2)), int(round(c[1] - n / 2))
    if x0 >= W or y0 >= H or x0 + n <= 0 or y0 + n <= 0: return img
    if n not in _tx: _tx[n] = cv2.resize(_tex, (n, n), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); rho = np.sqrt((xx - n / 2 + 0.5) ** 2 + (yy - n / 2 + 0.5) ** 2) / (n / 2)
    base = content("moon", n, t)
    pic = base if fill <= 0 else base * (1 - fill) + content(kind, n, t, reach) * fill
    tex = _tx[n]; mot = 0.80 + 0.35 * (tex / (tex.mean() + 1e-3) - 1) * 0.6
    pic = pic * mot[..., None] * (1 - 0.35 * np.clip(rho, 0, 1) ** 4)[..., None]
    a = np.clip((1 - rho) * n / 2.4 + 0.5, 0, 1)[..., None] * alpha
    if blur > 0:   # defocus with room to spread (no square edges)
        pd = int(blur * 3) + 2
        pic = cv2.GaussianBlur(np.pad(pic, ((pd, pd), (pd, pd), (0, 0)), mode="edge"), (0, 0), blur)
        a = cv2.GaussianBlur(np.pad(a[..., 0], pd), (0, 0), blur)[..., None]
        n = n + 2 * pd; x0 -= pd; y0 -= pd
    out = img
    if halo > 0: out = glow(out, c, r, halo * alpha, np.clip(pic.mean((0, 1)), 0.2, 1.0), fall=0.9)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + n), min(H, y0 + n)
    sub = out[ya:yb, xa:xb]; pa = pic[ya - y0:yb - y0, xa - x0:xb - x0]; aa = a[ya - y0:yb - y0, xa - x0:xb - x0]
    out[ya:yb, xa:xb] = sub * (1 - aa) + pa * aa
    return out

KINDS = ["clouds", "book", "moon", "witch", "heart"]
def row_layout(t, P0, row, r0, rad):
    """moon positions through the division: born on the kicks, pushed apart, then settled into the row on T_ROW"""
    n_born = 1 + sum(t >= k for k in KICKS)
    order = [2, 3, 1, 4, 0]                    # which row slot each new moon goes to (it buds from the middle outward)
    pos, rr, alive = {}, {}, []
    for bi in range(n_born):
        slot = order[bi]
        born = KICKS[bi - 1] if bi > 0 else -1
        u = eout2((t - born) / 0.22) if bi > 0 else 1.0
        live = [order[i] for i in range(n_born)]; ls = sorted(live)
        k = ls.index(slot); cl = P0 + np.array([(k - (len(ls) - 1) / 2) * r0 * 1.7, 0.0])     # the cluster while dividing
        parent = P0 if bi == 0 else pos.get(order[max(0, bi - 1)], P0)
        p_cl = parent + (cl - parent) * u
        s = eio((t - T_ROW) / 0.45)
        pos[slot] = p_cl + (row[slot] - p_cl) * s
        rr[slot] = (r0 * (0.75 + 0.25 * u)) * (1 - s) + rad[slot] * s
        alive.append(slot)
    return pos, rr, alive

# ---------------- S5 and S7: hand close-ups (the V4 hand; the profile rig does not hold up this large) ----------------
from hand4 import hand4
SH = 0.24 * W / 0.085
def sky_bg(blur):
    return plain_bg(("sky", blur), 0.90 * H, -15.0, blur)

def arm_hand(img, t, wr, d3, pin, sp, moon_c, moon_r, light_col=MOONCOL, light_k=1.0, back_col=(0.30, 0.32, 0.36)):
    """the V4 close-up arm and hand, lit by a moon at moon_c (fill and rim fall off with distance), light-wrapped"""
    hd = hand4(wr, d3, pin, SH, moon_r, spread=sp)
    el = wr - d3 * 0.30 * SH + np.array([0.0, 0.03 * SH])
    n3 = np.array([-d3[1], d3[0]]); n3 = n3 if n3[1] > 0 else -n3
    armp = bez(el, el + (wr - el) * 0.35 + n3 * 0.012 * SH, wr - d3 * 0.08 * SH + n3 * 0.004 * SH, wr - d3 * 0.036 * SH, 18)
    fig = dict(solid=[stroke(armp, 0.034 * SH, 0.0148 * SH)] + hd["solid"], sheer=[], hair=[])
    a, sh = raster2(fig, np.zeros(2), 1.0, (H, W))
    ys, xs = np.ogrid[0:H, 0:W]
    dist = ((xs - wr[0]) * -d3[0] + (ys - wr[1]) * -d3[1]) / SH
    wdef = np.clip((dist - 0.06) / 0.14, 0, 1).astype(np.float32)
    a = a * (1 - wdef) + cv2.GaussianBlur(a, (0, 0), 5) * wdef
    pre = img
    ink = K.INK + np.array(back_col, np.float32) * 0.04
    dmn = np.sqrt((xs - moon_c[0]) ** 2 + (ys - moon_c[1]) ** 2) / max(moon_r, 1)
    lm = np.exp(-(np.clip(dmn - 1, 0, None) / 1.4) ** 1.2).astype(np.float32) * light_k
    out = pre * (1 - a[..., None]) + ink * a[..., None]
    out = out + (a * lm * 0.20)[..., None] * light_col
    out = out + (rimlight(a, (moon_c[0] - wr[0], moon_c[1] - wr[1]), 2.2, 1.0) * np.clip(lm * 1.6, 0, 1))[..., None] * light_col * 0.55
    out = out + rimlight(a, (0.3, -1.0), 2.4, 1.0)[..., None] * np.array(back_col, np.float32) * 0.6
    lw = a * np.clip(1 - cv2.GaussianBlur(a, (0, 0), 6), 0, 1)
    out = out + lw[..., None] * cv2.GaussianBlur(pre, (0, 0), 10) * 0.55
    return out, hd

S5_SKY = np.array([0.66 * W, 0.12 * H])
def s5(t):
    """she holds it, lit by it; on 19.02 her fingers open and it rises away into the empty sky (camera still)"""
    img = sky_bg(6.0)
    rel_ = t >= T_REL
    pin = 1.0 - eio((t - T_REL) / 0.16)
    sp = 0.5 * eio((t - T_REL) / 0.3)
    ang = -58 + 2.0 * math.sin(t * 1.1) - 6 * eio((t - T_REL) / 0.6)
    d3 = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    mr0 = 0.090 * H
    wr = np.array([0.36 * W, 0.86 * H]) + np.array([0, -0.03 * H]) * eio((t - T_REL) / 0.5) + np.array([0, 2.0 * math.sin(t * 2.0)])
    hd0 = hand4(wr, d3, 1.0, SH, mr0); mc = hd0["mc"]
    u = eout2((t - (T_REL + 0.10)) / 1.7)                              # rising away, slowing, small
    p = mc + (S5_SKY - mc) * u + np.array([0.05 * W, 0]) * math.sin(math.pi * u) * 0.5
    rr = mr0 + (0.030 * H - mr0) * u
    img = glow(img, p, rr, 0.22, fall=2.0)
    img = H4.moon_sprite(img, p, rr, 0.10, gain=1.12)
    img, _ = arm_hand(img, t, wr, d3, pin, sp, p, mr0 if u < 0.05 else max(rr, 0.04 * H), light_k=1.0 - 0.75 * u)
    return img

def s7(t):
    """camera still: she reaches toward the tiny-her moon; during the fill it comes down into her open hand by itself,
    landing on the 28.19 hit before her reach is done. She stops. Inside it, the tiny her reaches back."""
    img = sky_bg(6.0)
    rowc = {0: (0.42, 0.10, 0.058), 1: (0.55, 0.075, 0.064), 2: (0.68, 0.065, 0.068), 3: (0.81, 0.075, 0.064), 4: (0.94, 0.10, 0.058)}
    for s in (0, 1, 2, 4):
        x_, y_, r_ = rowc[s]
        img = tab(img, np.array([x_ * W, y_ * H]), r_ * H, KINDS[s], t, fill=1.0, blur=6.0, halo=0.08)
    reach = eio((t - 25.5) / 3.6)                                      # slow, deliberate
    stop = eio((T_LAND - 25.5) / 3.6)
    rv = reach if t < T_LAND else stop                                 # ...frozen where it was when the moon arrived
    wr = np.array([0.30 * W, 1.10 * H]) + (np.array([0.50 * W, 0.42 * H]) - np.array([0.30 * W, 1.10 * H])) * rv
    if t >= T_LAND: wr = wr + np.array([0, 1.0]) * 3.0 * eout2((t - T_LAND) / 0.10) * math.exp(-(t - T_LAND) / 0.25)   # the tiny flinch
    ang = -62 + 4 * rv; d3 = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
    mr = 0.085 * H
    hd0 = hand4(wr, d3, 0.0, SH, mr, spread=0.6); hand_c = hd0["mc"]
    home = np.array([rowc[3][0] * W, rowc[3][1] * H]); r_home = rowc[3][2] * H
    land = eio((t - 27.16) / (T_LAND - 27.16))
    p = home + (hand_c - home) * land + np.array([0.04 * W, -0.02 * H]) * math.sin(math.pi * land)
    rr = r_home + (mr - r_home) * land
    reach_back = eio((t - 28.65) / 0.45)
    img = glow(img, p, rr, 0.16, fall=1.8)
    img = tab(img, p, rr, "witch", t, fill=1.0, blur=6.0 * (1 - land), halo=0.10, reach=reach_back)
    img, _ = arm_hand(img, t, wr, d3, 0.0, 0.6, p, max(rr, 0.04 * H), light_k=0.35 + 0.65 * land)
    return img

# ---------------- S6: wide, camera still: the division and the row ----------------
P0_6 = np.array([0.635 * W, 0.215 * H])
ROW6 = {0: np.array([0.405 * W, 0.255 * H]), 1: np.array([0.52 * W, 0.228 * H]), 2: np.array([0.635 * W, 0.215 * H]),
        3: np.array([0.75 * W, 0.228 * H]), 4: np.array([0.865 * W, 0.255 * H])}
RAD6 = {0: 0.062 * H, 1: 0.068 * H, 2: 0.072 * H, 3: 0.068 * H, 4: 0.062 * H}
HER6 = (np.array([0.24 * W, 0.90 * H]), 0.46 * H)
def fills(t):   # each face fills in on its own eighth note
    return {s: eio((t - (T_FILL + i * 0.255)) / 0.18) for i, s in enumerate([2, 1, 3, 0, 4])}

def wide6(t, missing=None, held=None):
    img = plain_bg("wide", 0.74 * H, 6.0, 0.0)
    pos, rr, alive = row_layout(t, P0_6, ROW6, 0.060 * H, RAD6); fl = fills(t)
    bob = lambda s: np.array([0.0, 0.004 * H * math.sin(t * 1.3 + s * 1.9)])
    # the moons light the plain a little
    lit = sum(rr[s] for s in alive) / (0.060 * H)
    ys, xs = np.ogrid[0:H, 0:W]
    img = img + (np.exp(-((xs - 0.62 * W) / (0.45 * W)) ** 2) * np.clip((ys - 0.74 * H) / (0.26 * H), 0, 1) * 0.025 * lit)[..., None] * MOONCOL
    for s in alive:
        if s == missing: continue
        img = tab(img, pos[s] + bob(s), rr[s], KINDS[s], t, fill=fl[s] * (t >= T_ROW), halo=0.10)
    org, hgt = HER6
    fig = figure(t=t, raise_u=0.30 if held is None else 0.55, look_u=0.85, pinch=0.0, wind=0.8, strands=560)
    img, a = draw_her(img, fig, org, hgt, P0_6, MOONCOL * 0.8, rim_k=0.75, fill_k=0.04, ground_y=org[1], shadow_dir=(-0.9, -0.12))
    if held is not None:
        mc = org + fig["A"]["moon_c"] * hgt
        img = tab(img, mc, fig["A"]["moon_r"] * hgt * 1.2, "witch", t, fill=1.0, halo=0.15)
    return img

# ---------------- S8: back out through a moon into your sky; then four more moons beside it ----------------
def world8(t):
    return wide6(T_S7 - 0.01, missing=3, held=True)

def post8(out, t, Cm, r):
    if t < 30.8: return out
    # four small moons appear in your real sky beside it, copies of your own moon (the plate's), one per eighth
    j = int(np.clip((H4.plate_time(t) - P.PT0) * P.PFPS, 0, len(P.TR) - 1))
    pl = P.plate(j).astype(np.float32) / 255; R = int(RM * 1.25); cx, cy = int(P.cx[j]), int(P.cy[j])
    crop = pl[cy - R:cy + R, cx - R:cx + R]
    crop = crop * np.array([1.06, 1.0, 0.95]) * 0.95 + np.array([0.012, 0.006, 0.0])
    for i, ta in enumerate(APPEAR):
        if t < ta: continue
        s_ = eout4((t - ta) / 0.14)
        rr = r * (0.36 - 0.03 * i) * (0.6 + 0.4 * s_)
        c = np.array([Cm[0] + r * 1.9 + i * r * 0.95, Cm[1] + r * 0.05 * math.sin(i * 1.7)])
        n = max(4, int(2 * rr * 1.25)); sm = cv2.resize(crop, (n, n), interpolation=cv2.INTER_AREA)
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); rho = np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (n / 2 / 1.25)
        a = (np.clip((1 - rho) * rr / 1.2 + 0.5, 0, 1) * s_)[..., None]
        x0, y0 = int(c[0] - n / 2), int(c[1] - n / 2)
        if x0 < 0 or y0 < 0 or x0 + n > W or y0 + n > H: continue
        out = glow(out, c, rr, 0.06 * s_, np.array([0.75, 0.80, 0.85], np.float32), fall=1.2)
        out[y0:y0 + n, x0:x0 + n] = out[y0:y0 + n, x0:x0 + n] * (1 - a) + sm * a
    return out

_hw4 = H4.hero_world
H4.hero_world = lambda t: world8(t) if t >= T_S8 else _hw4(t)
H4.POST = lambda out, t, Cm, r: post8(out, t, Cm, r) if t >= T_S8 else out

def render(t):
    H4.approach.held = None
    if t < T_S5 or t >= T_S8:
        if t >= T_S8: H4.T_DROP = 999.0
        try: return H4.render(t)
        finally: H4.T_DROP = 16.95
    if t < T_S6: img = s5(t)
    elif t < T_S7: img = wide6(t)
    else: img = s7(t)
    return K.finish(img, grain=0.026, vign=0.26, hal=0.20, seed=int(t * 1000) % 100000)

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
