"""V4 close-up hand: same pose language as round 3 (thumb and index hold the moon like a pearl, the other three
fingers lift in a soft fan) but built with articulation: each digit tapers, swells slightly at its two joints and
ends in a rounded pad; the palm runs into a slender wrist with no step; a short bare wrist leaves a chiffon cuff.
hand4(...) -> dict(solid=[polys], mc=moon centre, mr=moon radius, tips={...})"""
import math, numpy as np
from witch import bez

def _ribbon(path, widths):
    path = np.asarray(path, float); d = np.gradient(path, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    n = np.stack([-d[:, 1], d[:, 0]], 1); w = np.asarray(widths)[:, None] / 2
    return np.vstack([path + n * w, (path - n * w)[::-1]])

def _circle(c, r, n=24):
    th = np.linspace(0, 2 * math.pi, n, endpoint=False); return np.asarray(c) + np.stack([np.cos(th), np.sin(th)], 1) * r

def digit(base, tip, bow, w0, joints=(0.44, 0.75), taper=0.42):
    base = np.asarray(base, float); tip = np.asarray(tip, float); v = tip - base; L = np.linalg.norm(v) + 1e-9
    nv = np.array([-v[1], v[0]]) / L
    N = 30; path = bez(base, base + v * 0.33 + nv * bow * L, base + v * 0.70 + nv * bow * L * 0.80, tip, N)
    s = np.linspace(0, 1, N)
    w = w0 * (1 - taper * s) * (1 + 0.075 * np.exp(-((s - joints[0]) / 0.07) ** 2) + 0.055 * np.exp(-((s - joints[1]) / 0.06) ** 2))
    return [_ribbon(path, w), _circle(tip - (tip - path[-3]) * 0.0, w[-1] * 0.5)]

def digit_dir(base, ang, L, bend, w0):
    """a digit given a direction and a bend (radians spread over the joints, mostly distal)"""
    base = np.asarray(base, float)
    a = [ang, ang + bend * 0.30, ang + bend * 0.75]; seg = [0.46, 0.30, 0.24]
    p = [base]
    for ai, si in zip(a, seg): p.append(p[-1] + np.array([math.cos(ai), math.sin(ai)]) * L * si)
    tip = p[-1]
    return digit(base, tip, -bend * 0.10, w0)

def hand4(Wr, d3, pinch=1.0, s=1.0, moon_px=None, rest=0.0, spread=0.0):
    d3 = np.asarray(d3, float) / np.linalg.norm(d3); n3 = np.array([-d3[1], d3[0]])
    ang = math.atan2(d3[1], d3[0])
    P = lambda u, v: np.asarray(Wr, float) + d3 * u * s + n3 * v * s
    # palm + wrist as one outline: the wrist narrows behind the heel of the hand and runs on into the forearm
    top = bez(P(-0.040, -0.0072), P(-0.010, -0.0078), P(0.014, -0.0112), P(0.037, -0.0098), 16)
    knuck = bez(P(0.037, -0.0098), P(0.0425, -0.004), P(0.041, 0.004), P(0.034, 0.0100), 8)[1:]
    bot = bez(P(0.034, 0.0100), P(0.022, 0.0132), P(0.006, 0.0124), P(-0.006, 0.0088), 12)[1:]
    wristb = bez(P(-0.006, 0.0088), P(-0.016, 0.0074), P(-0.028, 0.0072), P(-0.040, 0.0074), 10)[1:]
    palm = np.vstack([top, knuck, bot, wristb])
    polys = [palm]
    mrp = moon_px if moon_px is not None else 0.016 * s
    ru = mrp / s
    mc = P(0.050 + ru * 0.55, 0.004 + ru * 0.25)
    def on_moon(a_deg):
        a = math.radians(a_deg); return mc + (-d3 * math.cos(a) - n3 * math.sin(a)) * mrp
    pe = pinch * pinch * (3 - 2 * pinch)
    ci, ct = on_moon(100), on_moon(-78)
    oi, ot = P(0.078, -0.028 - 0.006 * spread), P(0.044, 0.036 + 0.004 * spread)
    ti = oi + (ci - oi) * pe; tt = ot + (ct - ot) * pe
    k = rest
    pky = digit_dir(P(0.031, -0.0094), ang - 0.56 - 0.10 * spread - 0.02 * k, 0.028 * s, 0.16 + 0.25 * k, 0.0060 * s)
    rng = digit_dir(P(0.034, -0.0086), ang - 0.37 - 0.07 * spread - 0.04 * k, 0.036 * s, 0.12 + 0.25 * k, 0.0068 * s)
    mid = digit_dir(P(0.036, -0.0074), ang - 0.19 - 0.04 * spread - 0.06 * k, 0.041 * s, 0.08 + 0.25 * k, 0.0074 * s)
    thb = digit(P(0.020, 0.0100), tt, -0.20, 0.0094 * s, joints=(0.40, 0.72), taper=0.36)
    idx = digit(P(0.035, -0.0068), ti, 0.16, 0.0080 * s)
    tb = bez(P(0.020, 0.0100), P(0.020, 0.0100) + (tt - P(0.020, 0.0100)) * 0.25, tt, tt, 6)[1]
    web = np.array([P(0.012, 0.0095), tb, P(0.036, 0.0040), P(0.030, 0.0105)])
    polys += pky + rng + mid + [web] + thb + idx
    return dict(solid=polys, mc=mc, mr=mrp, tips=dict(index=ti, thumb=tt), P=P)
