"""The Promptress: a vector silhouette that stays crisp at any size (18 px on the moon's face to 800 px in close-up).
Local units: her height h = 1 (feet at y=0, hat tip near y=-1), x = the way she faces, y down.
pose(t-dependent dict) -> layers: list of (name, polygon Nx2, alpha). draw() rasterizes them at any scale with AA."""
import numpy as np, cv2, math

def bez(p0, p1, p2, p3, n=16):
    t = np.linspace(0, 1, n)[:, None]; p0, p1, p2, p3 = map(np.asarray, (p0, p1, p2, p3))
    return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3

def chain(*segs):
    out = [segs[0][:1]]
    for s in segs: out.append(s[1:])
    return np.vstack(out)

def rot(pts, ang, piv):
    c, s = math.cos(ang), math.sin(ang); p = np.asarray(pts) - piv
    return np.stack([p[:, 0]*c - p[:, 1]*s, p[:, 0]*s + p[:, 1]*c], 1) + piv

def stroke(path, w0, w1):
    """a tapered ribbon along a polyline (width w0 at start, w1 at end) -> polygon"""
    path = np.asarray(path, float); d = np.gradient(path, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    n = np.stack([-d[:, 1], d[:, 0]], 1); w = np.linspace(w0, w1, len(path))[:, None] / 2
    return np.vstack([path + n*w, (path - n*w)[::-1]])

def lerp(a, b, u): return a + (b - a) * u
def ease(u): u = min(max(u, 0.0), 1.0); return u*u*(3 - 2*u)

REST = dict(a1=math.radians(97), a2=math.radians(84), a3=math.radians(80))
RAISE = dict(a1=math.radians(-30), a2=math.radians(-58), a3=math.radians(-18))

def pose(raise_u=0.0, look_u=0.0, t=0.0, walk=0.0, wind=1.0, pinch=0.0):
    """raise_u: 0 arm at rest -> 1 raised to the moon. look_u: head tilts up. walk: gait phase amount (0 = standing).
    pinch: 0 hand open -> 1 thumb and index closed on the moon. Returns (layers, anchors)."""
    L = []; A = {}
    sw = math.sin(t * 1.7) * wind; sw2 = math.sin(t * 2.3 + 1.1) * wind
    gait = math.sin(t * 7.0) * walk
    # ---- head + hat (rotate together about the neck when she looks up) ----
    piv = np.array([0.005, -0.628]); th = -math.radians(16) * look_u
    hat = chain(bez((0.058, -0.745), (0.042, -0.84), (0.008, -0.915), (-0.032, -0.955)),
                bez((-0.032, -0.952), (-0.07, -0.985), (-0.11, -0.992), (-0.15, -0.978)),
                bez((-0.15, -0.978), (-0.118, -0.962), (-0.09, -0.945), (-0.072, -0.905)),
                bez((-0.07, -0.905), (-0.058, -0.85), (-0.064, -0.79), (-0.068, -0.745)))
    a = np.linspace(0, 2*math.pi, 64); brim = np.stack([0.178*np.cos(a) + 0.006, -0.744 + 0.0135*np.sin(a)], 1)
    brim = rot(brim, math.radians(-5), np.array([0.0, -0.744]))
    brim[:, 1] += np.where(brim[:, 0] > 0.1, (brim[:, 0] - 0.1) * 0.12, 0) + np.where(brim[:, 0] < -0.12, (-0.12 - brim[:, 0]) * 0.10, 0)
    face = chain(bez((-0.05, -0.738), (-0.0, -0.746), (0.04, -0.742), (0.052, -0.722)),
                 bez((0.052, -0.722), (0.056, -0.712), (0.058, -0.706), (0.062, -0.700)),
                 bez((0.062, -0.700), (0.07, -0.693), (0.078, -0.688), (0.074, -0.684)),
                 bez((0.074, -0.684), (0.068, -0.681), (0.064, -0.680), (0.066, -0.675)),
                 bez((0.066, -0.675), (0.068, -0.672), (0.062, -0.669), (0.061, -0.668)),
                 bez((0.061, -0.668), (0.066, -0.665), (0.066, -0.661), (0.061, -0.657)),
                 bez((0.061, -0.657), (0.058, -0.652), (0.06, -0.647), (0.054, -0.643)),
                 bez((0.054, -0.643), (0.044, -0.638), (0.034, -0.64), (0.026, -0.632)),
                 bez((0.026, -0.632), (0.022, -0.62), (0.024, -0.61), (0.03, -0.598)),
                 bez((0.03, -0.598), (0.0, -0.59), (-0.03, -0.6), (-0.04, -0.62)),
                 bez((-0.04, -0.62), (-0.06, -0.66), (-0.065, -0.7), (-0.05, -0.738)))
    # hair: a full, long fall of loose waves from under the brim to below her waist, pushed back by the wind
    hb = -0.018 * (1 + 0.35 * sw)
    def wave(y, amp, ph): return amp * math.sin(y * 38 + ph + t * 1.6)
    ys = np.linspace(-0.73, -0.33, 40)
    outer = np.stack([-0.072 - 0.055 * ((ys + 0.73) / 0.4) ** 0.8 + hb * ((ys + 0.73) / 0.4) * 1.6 + np.array([wave(y, 0.006, 0.0) for y in ys]), ys], 1)
    yi = np.linspace(-0.36, -0.73, 30)
    inner = np.stack([-0.040 - 0.012 * ((yi + 0.73) / 0.37) + hb * 0.4 * ((yi + 0.73) / 0.37) + np.array([wave(y, 0.003, 1.2) for y in yi]), yi], 1)
    # pointed locks along the bottom edge
    locks = []
    x_out, x_in = outer[-1, 0], inner[0, 0]
    for k in range(5):
        u0, u1 = k / 5, (k + 1) / 5; xa, xb = lerp(x_out, x_in, u0), lerp(x_out, x_in, u1)
        tipx = (xa + xb) / 2 + hb * 0.8 + 0.006 * math.sin(t * 2.0 + k * 1.7); tipy = -0.33 + 0.025 + 0.012 * ((k * 7) % 3)
        locks += [[xa, -0.335], [tipx, tipy]]
    hair = np.vstack([np.array([[-0.045, -0.738], [-0.062, -0.735]]), outer, np.array(locks), inner, np.array([[-0.03, -0.70], [-0.035, -0.735]])])
    strands = []
    for i, (y0, ln, ph) in enumerate([(-0.66, 0.24, 0.0), (-0.6, 0.26, 1.3), (-0.55, 0.22, 2.1), (-0.5, 0.2, 3.0), (-0.45, 0.16, 4.2), (-0.62, 0.2, 5.1)]):
        s = np.linspace(0, 1, 22); j = int((y0 + 0.73) / 0.4 * 39)
        x0 = outer[min(j, 39), 0] + 0.004
        px = x0 + hb * s * 0.8 + 0.010 * np.sin(s * 10 + ph + t * 2.1) * s - 0.022 * s * wind * (0.6 + 0.4 * math.sin(t * 1.3 + ph))
        py = y0 + s * ln
        strands.append(stroke(np.stack([px, py], 1), 0.0045, 0.0008))
    head = [rot(p, th, piv) for p in (hat, brim, face, hair)]
    strands = [rot(p, th * 0.5, piv) for p in strands]
    A["brim"] = head[1]; A["hat"] = head[0]; A["face"] = head[2]
    # ---- dress: fitted bodice, long skirt that pools and trails back in the wind ----
    hem_back = -0.20 - 0.03 * sw - 0.02 * abs(gait); hem_front = 0.10 + 0.025 * gait
    body = chain(bez((-0.035, -0.615), (0.0, -0.612), (0.02, -0.61), (0.03, -0.598)),
                 bez((0.03, -0.598), (0.05, -0.575), (0.064, -0.545), (0.06, -0.515)),
                 bez((0.06, -0.515), (0.055, -0.49), (0.03, -0.465), (0.033, -0.43)),
                 bez((0.033, -0.43), (0.05, -0.38), (0.06, -0.28), (0.075 + 0.01*gait, -0.15)),
                 bez((0.075 + 0.01*gait, -0.15), (0.088, -0.07), (hem_front - 0.01, -0.02), (hem_front, 0.0)),
                 bez((hem_front, 0.0), (0.03, 0.004), (-0.08, 0.004), (hem_back, 0.0)),
                 bez((hem_back, 0.0), (-0.16 - 0.02*sw, -0.03), (-0.1, -0.1), (-0.075, -0.2)),
                 bez((-0.075, -0.2), (-0.055, -0.3), (-0.05, -0.37), (-0.04, -0.43)),
                 bez((-0.04, -0.43), (-0.035, -0.47), (-0.055, -0.52), (-0.05, -0.56)),
                 bez((-0.05, -0.56), (-0.048, -0.59), (-0.042, -0.61), (-0.035, -0.615)))
    # far arm: a sheer bell sleeve hanging at her back
    sleeve_b = chain(bez((-0.035, -0.585), (-0.07, -0.5), (-0.10 - 0.02*sw, -0.4), (-0.115 - 0.03*sw, -0.3)),
                     bez((-0.115 - 0.03*sw, -0.3), (-0.09, -0.29 + 0.01*sw2), (-0.06, -0.31), (-0.045, -0.33)),
                     bez((-0.045, -0.33), (-0.04, -0.42), (-0.035, -0.5), (-0.035, -0.585)))
    # ---- near arm: shoulder -> elbow -> wrist -> hand, blended from rest to raised ----
    u = ease(raise_u)
    a1 = lerp(REST["a1"], RAISE["a1"], u); a2 = lerp(REST["a2"], RAISE["a2"], ease(raise_u * 1.15 - 0.1)); a3 = lerp(REST["a3"], RAISE["a3"], ease(raise_u * 1.3 - 0.25))
    S = np.array([0.012, -0.57]); L1, L2, L3 = 0.145, 0.13, 0.035
    E = S + L1 * np.array([math.cos(a1), math.sin(a1)]); Wr = E + L2 * np.array([math.cos(a2), math.sin(a2)])
    d3 = np.array([math.cos(a3), math.sin(a3)]); n3 = np.array([-d3[1], d3[0]])   # n3 points "down" of the hand when raised
    arm_path = np.vstack([bez(S, S + (E - S) * 0.6, E - (E - S) * 0.15, E, 10), bez(E, E + (Wr - E) * 0.25, Wr - (Wr - E) * 0.3, Wr, 10)[1:],
                          np.array([Wr + d3 * k for k in np.linspace(0, L3, 6)])[1:]])
    wid = np.concatenate([np.linspace(0.031, 0.022, 10), np.linspace(0.021, 0.0135, 9), np.linspace(0.015, 0.019, 5)])
    dd = np.gradient(arm_path, axis=0); dd /= np.linalg.norm(dd, axis=1, keepdims=True) + 1e-9; nn = np.stack([-dd[:, 1], dd[:, 0]], 1)
    armpoly = np.vstack([arm_path + nn * wid[:, None] / 2, (arm_path - nn * wid[:, None] / 2)[::-1]])
    upper = fore = palm = armpoly
    # pinch: the index finger arcs over the top, the thumb under; the moon sits in the gap
    gap = lerp(0.085, 0.072, pinch)   # gap between fingertips = moon diameter (h units)
    base = Wr + d3 * L3
    moon_c = base + d3 * 0.028 + (-n3) * 0.004
    idx = np.array([base + (-n3) * 0.004 + d3 * 0.004, base + d3 * 0.018 + (-n3) * (gap * 0.55), moon_c + (-n3) * (gap * 0.52) + d3 * 0.012, moon_c + (-n3) * (gap * 0.46) + d3 * 0.022])
    thb = np.array([base + n3 * 0.006, base + d3 * 0.01 + n3 * (gap * 0.5), moon_c + n3 * (gap * 0.5) + d3 * 0.006, moon_c + n3 * (gap * 0.46) + d3 * 0.016])
    def smooth(p):
        return bez(p[0], p[1], p[2], p[3], 14)
    f_idx = stroke(smooth(idx), 0.0085, 0.004); f_th = stroke(smooth(thb), 0.0095, 0.0045)
    f_rest = [stroke(smooth(np.array([base + (-n3)*0.002*k, base + d3*0.012 - n3*0.006*k, base + d3*0.016 + n3*(0.004 + 0.003*k), base + d3*0.010 + n3*(0.009 + 0.002*k)])), 0.007, 0.004) for k in (0, 1)]
    k_open = ease(raise_u * 2.5 - 1.5)   # fingers stay relaxed until the arm is most of the way up
    if k_open < 1:
        relaxed = [stroke(smooth(np.array([base + n3 * o, base + d3 * 0.012 + n3 * o, base + d3 * 0.024 + n3 * (o + 0.002), base + d3 * 0.034 + n3 * (o + 0.004)])), 0.0075, 0.0035) for o in (-0.004, 0.0, 0.004)]
        if k_open < 0.5: f_idx, f_th, f_rest = relaxed[0], relaxed[1], [relaxed[2]]
    A["moon_c"] = moon_c; A["moon_r"] = gap / 2; A["wrist"] = Wr; A["elbow"] = E; A["shoulder"] = S
    # sheer sleeve on the raised arm: hangs from the arm by gravity
    sag = 0.20 * u + 0.12 * (1 - u)
    edge_end = Wr + np.array([-0.006, 0.0])
    lo = E + np.array([0.0, sag * 0.55]) + np.array([0.01 * sw2, 0])
    sleeve = chain(bez(S + np.array([0, 0.012]), S + (E - S) * 0.5 + np.array([0, 0.01]), E + np.array([0, 0.005]), E),
                   bez(E, E + (Wr - E) * 0.4, Wr - (Wr - E) * 0.2, edge_end),
                   bez(edge_end, edge_end + np.array([0.01 + 0.012*sw2, sag * 0.6]), lo + np.array([0.04, 0.03]), lo),
                   bez(lo, lo + np.array([-0.04, -0.01]), np.array([0.03, -0.46]), np.array([0.025, -0.50])),
                   bez(np.array([0.025, -0.50]), np.array([0.02, -0.53]), S + np.array([0.0, 0.03]), S + np.array([0, 0.012])))
    L += [("sleeve_back", sleeve_b, 0.42), ("hair", head[3], 1.0)] + [("strand", s, 1.0) for s in strands]
    L += [("body", body, 1.0), ("hat", head[0], 1.0), ("brim", head[1], 1.0), ("face", head[2], 1.0)]
    L += [("arm", armpoly, 1.0), ("sleeve", sleeve, 0.40)]
    A["fingers"] = [("f_idx", f_idx, 1.0), ("f_th", f_th, 1.0)] + [("f", f, 1.0) for f in f_rest]
    A["arm"] = [armpoly]
    return L, A

def raster(layers, origin, scale, shape, flip_y=False, ss=4):
    """layers -> float32 alpha (0..1) of the given shape. origin = screen px of her feet; scale = px per h.
    Opaque layers are unioned; sheer ones add their own alpha (max). AA via cv2's subpixel LINE_AA fill."""
    H, W = shape; acc = np.zeros((H, W), np.float32)
    for name, poly, alpha in layers:
        p = np.asarray(poly, np.float64).copy()
        if flip_y: p[:, 1] = -p[:, 1]
        p = p * scale + origin
        x0, y0 = np.floor(p.min(0)).astype(int) - 2; x1, y1 = np.ceil(p.max(0)).astype(int) + 2
        if x1 < 0 or y1 < 0 or x0 >= W or y0 >= H: continue
        bx0, by0, bx1, by1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
        m = np.zeros((by1 - by0, bx1 - bx0), np.uint8)
        q = np.round((p - [bx0, by0]) * 16).astype(np.int32)
        cv2.fillPoly(m, [q], 255, cv2.LINE_AA, shift=4)
        a = m.astype(np.float32) / 255 * alpha
        sl = acc[by0:by1, bx0:bx1]; np.maximum(sl, a, out=sl) if alpha >= 1 else np.copyto(sl, 1 - (1 - sl) * (1 - a))
    return acc

def overlaps(polys_a, polys_b, res=600):
    """how much two groups of shapes cut through each other (in h^2): her rule, run on every frame"""
    def m(polys):
        acc = np.zeros((res, res), np.uint8)
        for p in polys:
            q = np.round((np.asarray(p) + [0.5, 1.1]) * res / 1.4 * 16).astype(np.int32)
            cv2.fillPoly(acc, [q], 1, cv2.LINE_8, shift=4)
        return acc
    return float((m(polys_a) & m(polys_b)).sum()) * (1.4 / res) ** 2
