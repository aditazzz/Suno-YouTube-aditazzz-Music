"""The Promptress seen from behind (walking toward / reaching into a door). Same character: the bent-tip hat, wide
brim, long loose hair, fitted bodice, flared skirt, chiffon sleeves and cape. Units as witch.py (h = 1, feet y = 0,
y down). Compatible with witch2.raster2 (dict: solid, sheer, hair, A, hand)."""
import numpy as np, math
from witch import bez, chain, stroke, lerp, ease, rot

def back_figure(t=0.0, reach_u=0.0, wind=1.0, walk=0.0, strands=380, seed=11, look_u=0.0):
    rng = np.random.default_rng(seed)
    sw = math.sin(t * 1.6) * wind; gait = math.sin(t * 6.5) * walk
    solid, sheer = [], []
    # bodice + skirt (back): sloped shoulders, a narrow waist, a skirt that flares and sways as she walks
    hemL, hemR = -0.14 - 0.012 * gait - 0.01 * sw, 0.13 - 0.012 * gait - 0.01 * sw
    body = chain(bez((0.0, -0.636), (-0.012, -0.636), (-0.02, -0.634), (-0.024, -0.628)),
                 bez((-0.024, -0.628), (-0.04, -0.612), (-0.07, -0.600), (-0.082, -0.585)),
                 bez((-0.082, -0.585), (-0.090, -0.570), (-0.082, -0.545), (-0.074, -0.525)),
                 bez((-0.074, -0.525), (-0.060, -0.49), (-0.046, -0.46), (-0.042, -0.43)),
                 bez((-0.042, -0.43), (-0.052, -0.40), (-0.058, -0.37), (-0.062, -0.34)),
                 bez((-0.062, -0.34), (-0.085, -0.22), (-0.115, -0.09), (hemL, 0.0)),
                 bez((hemL, 0.0), (-0.07, 0.016), (0.05, 0.016), (hemR, 0.0)),
                 bez((hemR, 0.0), (0.11, -0.09), (0.082, -0.22), (0.062, -0.34)),
                 bez((0.062, -0.34), (0.058, -0.37), (0.052, -0.40), (0.042, -0.43)),
                 bez((0.042, -0.43), (0.046, -0.46), (0.060, -0.49), (0.074, -0.525)),
                 bez((0.074, -0.525), (0.082, -0.545), (0.090, -0.570), (0.082, -0.585)),
                 bez((0.082, -0.585), (0.07, -0.600), (0.04, -0.612), (0.024, -0.628)),
                 bez((0.024, -0.628), (0.02, -0.634), (0.012, -0.636), (0.0, -0.636)))
    solid.append(body)
    a = np.linspace(0, 2 * math.pi, 48)
    piv = np.array([0.0, -0.63]); th = -math.radians(6) * look_u
    head = np.stack([0.041 * np.cos(a), -0.680 + 0.052 * np.sin(a)], 1)
    brim = np.stack([0.178 * np.cos(a), -0.742 + 0.036 * np.sin(a)], 1)
    brim[:, 1] += np.where(np.abs(brim[:, 0]) > 0.12, (np.abs(brim[:, 0]) - 0.12) * 0.15, 0)     # a soft droop at the edges
    crown = chain(bez((-0.064, -0.748), (-0.058, -0.84), (-0.035, -0.92), (0.0, -0.955)),
                  bez((0.0, -0.955), (0.03, -0.985), (0.07, -0.995), (0.10, -0.985)),
                  bez((0.10, -0.985), (0.075, -0.97), (0.05, -0.95), (0.04, -0.91)),
                  bez((0.04, -0.91), (0.055, -0.85), (0.062, -0.79), (0.064, -0.748)))
    solid += [rot(p, th, piv) for p in (head, brim, crown)]
    # hair: a narrow wavy core close to the head and back, then strands that fall and fan out in the wind
    hair = []
    ys = np.linspace(-0.725, -0.44, 30)
    wv = lambda y, ph: 0.004 * np.sin(y * 60 + ph + t * 1.5)
    left = np.stack([-0.036 - 0.03 * ((ys + 0.725) / 0.285) ** 1.2 + wv(ys, 0) + 0.012 * sw * ((ys + 0.725) / 0.285), ys], 1)
    right = np.stack([0.036 + 0.03 * ((ys + 0.725) / 0.285) ** 1.2 + wv(ys, 2) + 0.012 * sw * ((ys + 0.725) / 0.285), ys], 1)[::-1]
    core = np.vstack([left, right])
    solid.append(core)
    for i in range(strands):
        r0 = rng.random()
        root = np.array([lerp(-0.050, 0.050, r0), lerp(-0.70, -0.50, rng.random() ** 1.5)])
        Ln = rng.uniform(0.16, 0.30); ph = rng.uniform(0, 6.28); amp = rng.uniform(0.006, 0.014)
        s_ = np.linspace(0, 1, 30)[:, None]
        spread = (r0 - 0.5) * rng.uniform(0.07, 0.14)
        x = root[0] + spread * s_ ** 1.1 + amp * np.sin(s_ * 20 * Ln + ph + t * 1.8) * s_ + (0.03 * sw + 0.012 * math.sin(t * 2.3 + ph)) * s_ ** 1.5
        y = root[1] + Ln * s_
        hair.append((np.hstack([x, y]), rng.uniform(0.0010, 0.0021)))
    # arms: left hangs; right reaches up and forward (foreshortened, seen from behind)
    u = ease(reach_u)
    SL, SR = np.array([-0.080, -0.578]), np.array([0.080, -0.578])
    EL, WL = np.array([-0.097, -0.455]), np.array([-0.090, -0.335])
    ER = lerp(np.array([0.097, -0.455]), np.array([0.128, -0.700]), u)
    WR = lerp(np.array([0.090, -0.335]), np.array([0.142, -0.805]), u)
    def arm(S, E, Wr):
        p = np.vstack([bez(S, S + (E - S) * 0.6, E - (E - S) * 0.2, E, 10), bez(E, E + (Wr - E) * 0.3, Wr - (Wr - E) * 0.3, Wr, 10)[1:]])
        return stroke(p, 0.026, 0.0125)
    solid += [arm(SL, EL, WL), arm(SR, ER, WR)]
    # the reaching hand, back of the hand toward us: fingers fanned, long and tapered, the tips slightly curled
    d = (WR - ER) / np.linalg.norm(WR - ER); n = np.array([-d[1], d[0]])
    def fing(base, ang, L, w):
        c, s2 = math.cos(ang), math.sin(ang); dd = d * c + n * s2; nn = np.array([-dd[1], dd[0]])
        p = np.array([base, base + dd * L * 0.5, base + dd * L * 0.85 + nn * L * 0.06, base + dd * L + nn * L * 0.14])
        return stroke(bez(p[0], p[1], p[2], p[3], 12), w, w * 0.45)
    palm = np.vstack([WR - n * 0.0085, WR + d * 0.012 - n * 0.0105, WR + d * 0.027 - n * 0.0105, WR + d * 0.030, WR + d * 0.027 + n * 0.0105, WR + d * 0.012 + n * 0.0105, WR + n * 0.0085])
    spreadk = 0.10 + 0.12 * u
    hand = [palm] + [fing(WR + d * 0.027 + n * off, (k - 1.5) * spreadk, L, 0.0068) for k, (off, L) in enumerate([(-0.0075, 0.034), (-0.0025, 0.040), (0.0025, 0.038), (0.0075, 0.030)])]
    hand.append(fing(WR + d * 0.008 + n * 0.009, 0.9, 0.024, 0.0075))
    lh = stroke(bez(WL, WL + np.array([0.0, 0.02]), WL + np.array([0.003, 0.04]), WL + np.array([0.004, 0.055]), 6), 0.015, 0.007)
    solid += hand + [lh]
    # chiffon: a cape that streams to one side, and sleeves that hang from each arm
    cape = chain(bez((-0.07, -0.585), (-0.12, -0.42), (-0.22 - 0.04 * sw, -0.18), (-0.30 - 0.05 * sw, 0.012)),
                 bez((-0.30 - 0.05 * sw, 0.012), (-0.18, 0.04 + 0.01 * math.sin(t * 2.1)), (-0.04, 0.03), (0.10, 0.014)),
                 bez((0.10, 0.014), (0.07, -0.20), (0.06, -0.42), (0.07, -0.585)))
    sheer.append((cape, 0.22))
    for k in range(7):
        f = (k + 0.5) / 7; x0 = lerp(-0.06, 0.06, f)
        sheer.append((stroke(bez((x0, -0.57), (x0 - 0.04, -0.35), (x0 * 1.5 - 0.10 - 0.03 * sw, -0.12), (lerp(-0.28, 0.08, f) - 0.04 * sw, 0.02), 20), 0.003, 0.010), 0.12))
    for S, E, Wr, side, uu in [(SL, EL, WL, -1, 0.0), (SR, ER, WR, 1, u)]:
        top = np.vstack([bez(S, S + (E - S) * 0.5, E - (E - S) * 0.1, E, 8), bez(E, E + (Wr - E) * 0.4, Wr - (Wr - E) * 0.25, Wr - (Wr - E) * 0.08, 8)[1:]])
        sag = 0.10 + 0.13 * uu
        hang = top[-1] + np.array([side * 0.012 + 0.008 * math.sin(t * 2.2), sag])
        bottom = bez(hang, hang + np.array([-side * 0.03, 0.02]), S + np.array([side * 0.03, 0.16]), S + np.array([side * 0.006, 0.04]), 14)
        sheer.append((np.vstack([top, bottom[1:]]), 0.30))
    A = dict(hand_tip=WR + d * 0.065, wrist=WR, brim=brim, hat=crown, face=head)
    return dict(solid=solid, sheer=sheer, hair=hair, A=A, hand=hand)
