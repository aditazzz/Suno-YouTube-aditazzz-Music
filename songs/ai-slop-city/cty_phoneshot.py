"""The close-up: her phone in her left hand, seen from her own eyes, thumb on the screen; her lap and the plaza
beneath, far out of focus. The phone and hand are inked like the rest of the city; the screen is crisp UI.

Phone-local units: width 1.0, height 2.164, origin at the centre, u right, v down.
"""
import math
import numpy as np, cv2
from cty_eng import F32, AA, hexc, mix, clamp

PW, PH = 1.0, 2.164
SCR_U, SCR_V = 0.462, 1.064          # half extents of the screen
INK = hexc('1d1620')
SKIN = hexc('e6bfa0'); SKIN_SH = hexc('c4907a')
COAT = hexc('c9a47a')
BODY = hexc('2b2b33'); BODY_HI = hexc('5a5a66')


def rrect_pts(hu, hv, r, n=10):
    pts = []
    for cu, cv, a0 in ((hu - r, -hv + r, 180), (hu - r, hv - r, 270), (-hu + r, hv - r, 0), (-hu + r, -hv + r, 90)):
        pass
    for cu, cv, a0 in ((hu - r, -hv + r, -90), (hu - r, hv - r, 0), (-hu + r, hv - r, 90), (-hu + r, -hv + r, 180)):
        for a in np.linspace(a0, a0 + 90, n):
            pts.append((cu + r * math.cos(math.radians(a)), cv + r * math.sin(math.radians(a))))
    return np.array(pts)


class PhoneXf:
    """Phone-local (u, v) -> pixels: tilt about the horizontal axis (bottom toward us), rotation, perspective."""

    def __init__(self, cx, cy, wpx, rot=0.0, tilt=12.0, f=3.0):
        self.cx, self.cy, self.w = cx, cy, wpx
        self.rot = math.radians(rot); self.tilt = math.radians(tilt); self.D = f * wpx

    def __call__(self, P):
        P = np.asarray(P, np.float64)
        x = P[..., 0] * self.w; y = P[..., 1] * self.w
        y3 = y * math.cos(self.tilt); z3 = -y * math.sin(self.tilt)
        s = self.D / (self.D + z3)
        xp, yp = x * s, y3 * s
        c, sn = math.cos(self.rot), math.sin(self.rot)
        return np.stack([self.cx + xp * c - yp * sn, self.cy + xp * sn + yp * c], -1)


def _fill(img, pts, col, alpha=1.0):
    H, W = img.shape[:2]
    P = np.asarray(pts, np.float64)
    x0, y0 = max(0, int(P[:, 0].min()) - 2), max(0, int(P[:, 1].min()) - 2)
    x1, y1 = min(W, int(P[:, 0].max()) + 3), min(H, int(P[:, 1].max()) + 3)
    if x1 <= x0 or y1 <= y0: return None
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(m, [np.round((P - [x0, y0]) * 16).astype(np.int32)], 255, AA, shift=4)
    mf = m.astype(F32)[..., None] / 255 * alpha
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - mf) + np.asarray(col, F32) * mf
    return (x0, y0, x1, y1, mf[..., 0])


def _ink(img, pts, w, closed=True, col=INK, alpha=1.0):
    H, W = img.shape[:2]
    P = np.asarray(pts, np.float64)
    pad = int(w) + 3
    x0, y0 = max(0, int(P[:, 0].min()) - pad), max(0, int(P[:, 1].min()) - pad)
    x1, y1 = min(W, int(P[:, 0].max()) + pad), min(H, int(P[:, 1].max()) + pad)
    if x1 <= x0 or y1 <= y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.polylines(m, [np.round((P - [x0, y0]) * 16).astype(np.int32)], closed, 255, max(1, int(round(w))), AA, shift=4)
    mf = m.astype(F32)[..., None] / 255 * alpha
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - mf) + np.asarray(col, F32) * mf


def spline(pts, n=10, closed=True):
    P = np.asarray(pts, np.float64)
    P = np.vstack([P[-1:], P, P[:2]]) if closed else np.vstack([P[:1], P, P[-1:]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            s = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    if not closed: out.append(P[-2])
    return np.array(out)


def hand_shapes(thumb_u, thumb_v, press=0.0):
    """Her left hand in phone units: the palm is behind the phone; we see the thumb over the screen, the heel of the
    hand below the phone's corner, the sleeve, and fingertips curling round the right edge."""
    sleeve = [(-1.7, 3.4), (-1.2, 1.78), (-0.98, 1.5), (-0.56, 1.56), (-0.22, 1.82), (-0.32, 3.4)]
    heel = [(-1.02, 1.62), (-0.86, 1.2), (-0.62, 0.92), (-0.42, 0.96), (-0.18, 1.12), (0.12, 1.16), (0.3, 1.14),
            (0.38, 1.24), (0.2, 1.36), (-0.12, 1.42), (-0.4, 1.58), (-0.62, 1.7), (-0.86, 1.76)]
    tu, tv = thumb_u, thumb_v
    bu, bv = -0.56 + 0.25 * (tu + 0.04), 0.98 + 0.25 * (tv - 0.55)          # the base follows the tip a little
    d = np.array([tu - bu, tv - bv]); Lt = np.linalg.norm(d); d /= Lt
    nr = np.array([-d[1], d[0]])
    bend = 0.05
    def P(t, o): return np.array([bu, bv]) + d * Lt * t + nr * (o + bend * math.sin(math.pi * t))
    w0, w1 = 0.15, 0.095 * (1 + press * 0.12)
    thumb = [P(-0.15, -w0), P(0.3, -w0 * 0.92), P(0.66, -w1 * 1.02), P(0.92, -w1 * 0.86), P(1.02, -w1 * 0.3),
             P(1.03, w1 * 0.25), P(0.93, w1 * 0.8), P(0.66, w1 * 0.95), P(0.3, w0 * 0.85), P(-0.15, w0)]
    nail = [P(0.78, -w1 * 0.52), P(0.97, -w1 * 0.5), P(1.0, 0.0), P(0.97, w1 * 0.48), P(0.78, w1 * 0.52)]
    knuckle = [P(0.5, -w1 * 0.7), P(0.54, -w1 * 0.1), P(0.5, w1 * 0.5)]
    fingers = []
    for k, (v0, ln, hh) in enumerate(((-0.46, 0.05, 0.13), (-0.18, 0.075, 0.15), (0.1, 0.078, 0.15), (0.38, 0.065, 0.14))):
        fingers.append([(0.46, v0), (0.5 + ln * 0.7, v0 - 0.005), (0.5 + ln, v0 + hh * 0.35), (0.5 + ln * 0.85, v0 + hh * 0.85),
                        (0.5 + ln * 0.3, v0 + hh), (0.46, v0 + hh * 0.95)])
    return dict(sleeve=sleeve, palm=heel, thumb=thumb, nail=nail, knuckle=knuckle, fingers=fingers)


def compose(bg, screen, xf, t=0.0, thumb=(0.0, 0.62), press=0.0, light=None, screen_k=1.0, reflection=None):
    """Draw the phone (with `screen`, an RGB image of the UI) and her hand over `bg` (float RGB, modified in place)."""
    L = dict(key=np.array([1.0, 0.97, 0.94], F32), amb=np.array([0.62, 0.62, 0.72], F32), glow=1.0)
    if light: L.update(light)
    img = bg
    w = xf.w
    lw = max(1.0, w * 0.006)
    hs = hand_shapes(thumb[0], thumb[1], press)
    key, amb = np.asarray(L['key'], F32), np.asarray(L['amb'], F32)
    # fingertips behind the right edge first
    for fpts in hs['fingers']:
        P = xf(spline(fpts, 8))
        _fill(img, P, SKIN * key * 0.92); _ink(img, P, lw)
    # phone body
    body = xf(rrect_pts(0.5, PH / 2, 0.14, 12))
    _fill(img, body, BODY * (amb * 0.6 + key * 0.4))
    # edge highlight
    _ink(img, xf(rrect_pts(0.49, PH / 2 - 0.01, 0.13, 12)), max(1, lw * 0.8), col=BODY_HI * key, alpha=0.6)
    # screen
    sq = xf(np.array([(-SCR_U, -SCR_V), (SCR_U, -SCR_V), (SCR_U, SCR_V), (-SCR_U, SCR_V)]))
    h, ww = screen.shape[:2]
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [ww, 0], [ww, h], [0, h]]), np.float32(sq))
    x0, y0 = max(0, int(sq[:, 0].min()) - 2), max(0, int(sq[:, 1].min()) - 2)
    x1, y1 = min(img.shape[1], int(sq[:, 0].max()) + 3), min(img.shape[0], int(sq[:, 1].max()) + 3)
    Hr = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ Hm
    warped = cv2.warpPerspective(screen.astype(F32) * screen_k, Hr, (x1 - x0, y1 - y0), flags=cv2.INTER_AREA if ww > (x1 - x0) else cv2.INTER_LINEAR)
    sm = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(sm, [np.round((xf(rrect_pts(SCR_U, SCR_V, 0.11, 12)) - [x0, y0]) * 16).astype(np.int32)], 255, AA, shift=4)
    smf = sm.astype(F32)[..., None] / 255
    glass = hexc('050508')
    region = img[y0:y1, x0:x1]
    region[:] = region * (1 - smf) + (glass * (1 - screen_k) + warped) * smf
    if reflection is not None:
        region[:] = region + reflection[y0:y1, x0:x1] * smf
    # glass sheen
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
    band = np.exp(-(((xx - xf.cx) * 0.6 + (yy - xf.cy) * 0.8 + w * 0.5) / (w * 0.35)) ** 2) * 0.05
    region[:] = region + band[..., None] * smf
    # dynamic island
    isl = xf(rrect_pts(0.15, 0.045, 0.045, 8) + np.array([0, -SCR_V + 0.075]))
    _fill(img, isl, hexc('050506'))
    _ink(img, body, lw * 1.2)
    # sleeve and palm, thumb on top
    P = xf(spline(hs['sleeve'], 8)); _fill(img, P, COAT * mix(amb, key, 0.6)); _ink(img, P, lw)
    _ink(img, xf(spline([(-1.12, 1.84), (-0.7, 1.74), (-0.3, 1.9)], 8, closed=False)), lw * 0.8, closed=False)
    P = xf(spline(hs['palm'], 8)); _fill(img, P, SKIN * key); _ink(img, P, lw)
    P = xf(spline(hs['thumb'], 8)); r = _fill(img, P, SKIN * key)
    if r is not None:
        # the screen lights the underside of the thumb
        X0, Y0, X1, Y1, m = r
        sub = img[Y0:Y1, X0:X1]
        sh = np.roll(m, -int(w * 0.02), 0)
        k = np.clip(m - sh, 0, 1)[..., None]
        sub[:] = sub * (1 - k * 0.35) + SKIN_SH * k * 0.35
    _ink(img, P, lw)
    _fill(img, xf(spline(hs['nail'], 6)), mix(SKIN * key, np.ones(3, F32), 0.35)); _ink(img, xf(spline(hs['nail'], 6)), lw * 0.7)
    _ink(img, xf(spline(hs['knuckle'], 6, closed=False)), lw * 0.7, closed=False)
    return img


def thumb_motion(t, mode='scroll', t0=0.0, period=1.2):
    """Thumb tip (u, v) and press amount. scroll: flick up repeatedly; tap: double tap at t0 (on the picture); rest."""
    if mode == 'rest': return (-0.1, 0.62), 0.0
    if mode == 'tap':
        dt = t - t0
        press = 0.0
        for k in (0.0, 0.16):
            press = max(press, math.exp(-((dt - k) / 0.05) ** 2))
        lift = 1 - math.exp(-max(0.0, dt + 0.25) * 6) if dt < 0 else 1.0
        return (-0.04, 0.18 + 0.03 * (1 - press)), press
    ph = ((t - t0) / period) % 1.0
    if ph < 0.35:
        k = ph / 0.35; k = k * k * (3 - 2 * k)
        return (-0.08 + 0.05 * k, 0.74 - 0.42 * k), 0.6 * math.sin(math.pi * k)
    k = (ph - 0.35) / 0.65; k = k * k * (3 - 2 * k)
    return (-0.03 - 0.05 * k, 0.32 + 0.42 * k), 0.0


def scroll_offset(t, t0=0.0, period=1.2, per=480.0):
    """Feed scroll position (points) matching thumb_motion('scroll'): eases one post per flick."""
    n = (t - t0) / period
    i = math.floor(n); ph = n - i
    k = clamp(ph / 0.5); k = 1 - (1 - k) ** 3
    return (i + k) * per
