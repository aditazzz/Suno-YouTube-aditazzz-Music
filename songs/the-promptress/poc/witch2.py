"""The Promptress, character v2: same silhouette and rig as witch.py (hat, profile, bodice, skirt, the arm), plus what
gives her presence: hair as ~220 individual strands, sheer chiffon built from overlapping translucent ribbons, a
real hand for close-ups, and (in the compositor) rim light from the moon. Units: her height h = 1, feet at y = 0."""
import numpy as np, cv2, math
from witch import bez, chain, rot, stroke, lerp, ease, pose as pose_v1

def _tapered(path, w0, w1, cap=True):
    p = stroke(path, w0, w1)
    return p

def finger(base, ang0, segs, flex, w0):
    """a finger as a chain of phalanges: base point, starting angle, segment lengths, bend per joint -> (polygon, tip)"""
    pts = [np.asarray(base, float)]; a = ang0; n = 8
    for i, (L, f) in enumerate(zip(segs, flex)):
        nxt = flex[i + 1] if i + 1 < len(flex) else 0.0
        for k in range(1, n + 1):
            a += (f * 0.5 + nxt * 0.5) / n if i + 1 < len(flex) else f / n
            pts.append(pts[-1] + (L / n) * np.array([math.cos(a), math.sin(a)]))
    pts = np.array(pts)
    poly = stroke(pts, w0, w0 * 0.62)
    tip_r = w0 * 0.31
    th = np.linspace(0, 2 * math.pi, 12); cap = pts[-1] + np.stack([np.cos(th), np.sin(th)], 1) * tip_r
    return [poly, cap], pts[-1]

def _finger(base, ang, L, bend, w0):
    """a slender finger: a smooth arc (bend spread along it), tapered, with a rounded tip"""
    d0 = np.array([math.cos(ang), math.sin(ang)])
    d1 = np.array([math.cos(ang + bend * 0.5), math.sin(ang + bend * 0.5)])
    d2 = np.array([math.cos(ang + bend), math.sin(ang + bend)])
    p0 = np.asarray(base, float); p1 = p0 + d0 * L * 0.40; p2 = p1 + d1 * L * 0.35; p3 = p2 + d2 * L * 0.30
    path = bez(p0, p1, p2, p3, 22)
    poly = stroke(path, w0, w0 * 0.62)
    th = np.linspace(0, 2 * math.pi, 16); cap = path[-1] + np.stack([np.cos(th), np.sin(th)], 1) * w0 * 0.31
    return [poly, cap], path[-1]

def _finger_to(base, tip, bow, w0, w1r=0.60):
    """a finger from base to an exact tip, bowed sideways by `bow` (fraction of its length; + = left of travel)"""
    base = np.asarray(base, float); tip = np.asarray(tip, float); v = tip - base; L = np.linalg.norm(v) + 1e-9
    nv = np.array([-v[1], v[0]]) / L
    path = bez(base, base + v * 0.30 + nv * bow * L, base + v * 0.68 + nv * bow * L * 0.85, tip, 22)
    poly = stroke(path, w0, w0 * w1r)
    th = np.linspace(0, 2 * math.pi, 16); cap = tip + np.stack([np.cos(th), np.sin(th)], 1) * w0 * w1r * 0.5
    return [poly, cap], tip

def hand(Wr, d3, pinch=1.0, moon_r=0.034, s=1.0, rest=0.0, moon_px=None):
    """an elegant hand at the wrist Wr pointing along d3. Thumb and index hold the moon between their fingertips
    (like a pearl); middle, ring and little finger lift away in a soft fan (a dancer's hand, not a claw).
    pinch 0 = open and reaching, 1 = holding. rest: relaxed. s: px per h-unit. moon_px: moon radius in px.
    -> (polys, moon_center, moon_radius)"""
    d3 = np.asarray(d3, float) / np.linalg.norm(d3); n3 = np.array([-d3[1], d3[0]])     # n3: thumb side
    ang = math.atan2(d3[1], d3[0])
    P = lambda u, v: Wr + d3 * u * s + n3 * v * s
    palm = np.vstack([bez(P(-0.010, -0.0090), P(0.010, -0.0108), P(0.026, -0.0118), P(0.037, -0.0098), 10),
                      bez(P(0.037, -0.0098), P(0.042, -0.004), P(0.041, 0.004), P(0.034, 0.0100), 8)[1:],
                      bez(P(0.034, 0.0100), P(0.024, 0.0128), P(0.008, 0.0118), P(-0.010, 0.0090), 10)[1:]])
    polys = [palm]; k = rest
    mrp = moon_px if moon_px is not None else moon_r * s
    ru = mrp / s
    mc = P(0.050 + ru * 0.55, 0.004 + ru * 0.25)                     # the moon floats just ahead of the hand
    def on_moon(a_deg):                                  # a point on the moon's back edge, a_deg from -d3
        a = math.radians(a_deg); return mc + (-d3 * math.cos(a) - n3 * math.sin(a)) * mrp
    ci = on_moon(100); ct = on_moon(-78)                  # index above, thumb below
    oi = P(0.072, -0.012); ot = P(0.050, 0.022)          # open: reaching, apart
    pe = pinch * pinch * (3 - 2 * pinch)
    ti = oi + (ci - oi) * pe; tt = ot + (ct - ot) * pe
    idx, _ = _finger_to(P(0.035, -0.0068), ti, 0.16, 0.0078 * s)
    thb, _ = _finger_to(P(0.020, 0.0100), tt, -0.20, 0.0088 * s)
    mid, _ = _finger(P(0.036, -0.0074), ang - 0.16 - 0.06 * k, 0.034 * s, -0.08 + 0.3 * k, 0.0070 * s)
    rng_, _ = _finger(P(0.034, -0.0088), ang - 0.32 - 0.04 * k, 0.029 * s, -0.12 + 0.3 * k, 0.0064 * s)
    pky, _ = _finger(P(0.031, -0.0098), ang - 0.50 - 0.02 * k, 0.022 * s, -0.16 + 0.3 * k, 0.0054 * s)
    polys += pky + rng_ + mid + thb + idx
    return polys, mc, mrp

def figure(t=0.0, raise_u=0.0, look_u=0.0, pinch=0.0, wind=1.0, walk=0.0, strands=560, seed=7):
    """-> dict(solid=[polys], sheer=[(poly, alpha)], hair=[(polyline, width)], A=anchors)"""
    L, A = pose_v1(raise_u, look_u, t=t, walk=walk, wind=wind, pinch=pinch)
    solid = [p for name, p, a in L if a >= 1 and name not in ("strand",)]
    rng = np.random.default_rng(seed)
    sw = math.sin(t * 1.7) * wind
    # ---- the hand: replace the v1 bracket fingers with a real hand ----
    Wr = A["wrist"]; el = A["elbow"]
    d3 = A["moon_c"] - Wr; d3 = d3 / np.linalg.norm(d3)
    u = ease(raise_u)
    rest = 1 - ease(raise_u * 2.5 - 1.5)
    hp, mc, mr = hand(Wr - d3 * 0.006, d3, pinch=pinch, s=1.0, rest=rest)
    solid += hp
    A["moon_c"], A["moon_r"] = mc, mr
    # ---- hair: ~14 locks of strands (clumped like real hair), falling in waves and lifting in the wind ----
    th = -math.radians(16) * look_u; piv = np.array([0.005, -0.628])
    hair = []
    nl = 14; per = max(1, strands // nl)
    for li in range(nl):
        r0 = li / (nl - 1)
        lroot = np.array([lerp(-0.028, -0.088, r0), lerp(-0.740, -0.650, r0 ** 1.3)])
        LnL = lerp(0.30, 0.44, rng.random()) * (0.85 + 0.25 * r0)
        ph = rng.uniform(0, 6.28); k = rng.uniform(15, 22); amp = rng.uniform(0.008, 0.016)
        outward = lerp(-0.020, -0.085, r0) + rng.normal(0, 0.010)
        for j in range(per):
            s_ = np.linspace(0, 1, 34)[:, None]
            jit = rng.normal(0, 1, 2) * [0.009, 0.006]
            Ln = LnL * rng.uniform(0.82, 1.06)
            x = lroot[0] + jit[0] + outward * s_ ** 1.2 + amp * np.sin(s_ * k * Ln + ph + t * 1.7) * s_ ** 0.8 \
                + rng.normal(0, 0.0025) * s_ * np.sin(s_ * 30 + rng.uniform(0, 6))
            x = x - (0.050 + 0.025 * math.sin(t * 1.3 + ph * 0.3)) * wind * s_ ** 1.5
            y = lroot[1] + jit[1] + Ln * s_ - 0.016 * wind * s_ ** 2 * (0.5 + 0.5 * math.sin(t * 2.0 + ph))
            pts = np.hstack([x, y]); pts = rot(pts, th * 0.7, piv)
            hair.append((pts, rng.uniform(0.0009, 0.0021)))
    # a soft core under the strands, close to the head and back (so the hair has mass where it's thickest)
    core = chain(bez((-0.03, -0.738), (-0.07, -0.72), (-0.085, -0.66), (-0.082, -0.60)),
                 bez((-0.082, -0.60), (-0.08, -0.55), (-0.075, -0.50), (-0.06, -0.47)),
                 bez((-0.06, -0.47), (-0.05, -0.50), (-0.045, -0.56), (-0.04, -0.62)),
                 bez((-0.04, -0.62), (-0.025, -0.67), (-0.015, -0.71), (-0.03, -0.738)))
    solid = [p for p in solid if not (p.shape == L[1][1].shape and np.allclose(p, L[1][1]))]   # drop v1's hair slab
    solid.append(rot(core, th * 0.8, piv))
    # ---- sheer: one chiffon cape from the shoulders, trailing on the wind, with a few soft folds ----
    sheer = []
    hem = []
    for k in range(40):
        f = k / 39
        hem.append([lerp(-0.07, -0.36 - 0.05 * sw, f) + 0.012 * math.sin(f * 9 + t * 2.1), lerp(-0.30, 0.0, f ** 0.7) - 0.018 * math.sin(f * 7 + t * 1.6) * f])
    hem = np.array(hem)
    top = bez((-0.045, -0.59), (-0.06, -0.50), (-0.07, -0.40), (-0.07, -0.30), 20)
    back_edge = bez((-0.36 - 0.05 * sw, 0.0), (-0.20, 0.004), (-0.09, 0.0), (-0.07, -0.02), 16)
    cape = np.vstack([top, hem[1:], back_edge[1:], np.array([[-0.05, -0.2], [-0.04, -0.45]])])
    sheer.append((cape, 0.30))
    for k in range(7):
        f = (k + 0.5) / 7
        p0 = np.array([lerp(-0.05, -0.07, f), lerp(-0.56, -0.32, f)]); p3 = hem[int(f * 39)]
        sheer.append((stroke(bez(p0, p0 + [-0.03, 0.12], p3 + [0.05, -0.1], p3, 24), 0.003, 0.012), 0.16))
    # the raised arm's sleeve: v1's drape, sheer, plus folds that hang from the forearm
    sl = [p for name, p, a in L if name == "sleeve"][0]
    sheer.append((sl, 0.34))
    S = A["shoulder"]
    for k in range(5):
        f = (k + 0.5) / 5
        top = el + (Wr - el) * f
        end = top + np.array([-0.01 - 0.02 * f + 0.01 * math.sin(t * 2.0 + k) * wind, 0.10 + 0.08 * u * (1 - f * 0.5)])
        sheer.append((stroke(bez(top, top + [0, 0.04], end + [0.01, -0.03], end, 12), 0.002, 0.008), 0.14))
    sb = [p for name, p, a in L if name == "sleeve_back"][0]
    sheer.append((sb, 0.30))
    # drop v1's single-polygon sleeves and its bracket fingers (replaced above)
    return dict(solid=solid, sheer=sheer, hair=hair, A=A, hand=hp)

HAIR_SOFT = 0.0
def raster2(fig, origin, scale, shape, flip_y=False):
    """-> (alpha 0..1 float32 for the whole figure, alpha of the sheer parts alone)"""
    H, W = shape
    def tx(p):
        p = np.asarray(p, np.float64).copy()
        if flip_y: p[:, 1] = -p[:, 1]
        return p * scale + origin
    solid = np.zeros((H, W), np.uint8)
    for p in fig["solid"]:
        q = np.round(tx(p) * 16).astype(np.int32); cv2.fillPoly(solid, [q], 255, cv2.LINE_AA, shift=4)
    hair = np.zeros((H, W), np.uint8)
    for pts, w in fig["hair"]:
        q = np.round(tx(pts) * 16).astype(np.int32); wp = w * scale
        n = len(q); cut = int(n * 0.66)
        if wp >= 1.5:
            cv2.polylines(hair, [q[:cut + 1]], False, 255, max(1, int(round(wp))), cv2.LINE_AA, shift=4)
            cv2.polylines(hair, [q[cut:]], False, 255, max(1, int(round(wp * 0.5))), cv2.LINE_AA, shift=4)
        elif wp >= 1.0:
            cv2.polylines(hair, [q], False, 255, 1, cv2.LINE_AA, shift=4)
        else:
            tmp = np.zeros_like(hair); cv2.polylines(tmp, [q], False, int(255 * wp), 1, cv2.LINE_AA, shift=4); np.maximum(hair, tmp, out=hair)
    if HAIR_SOFT > 0 and fig["hair"]:      # V4: strands merge into soft locks instead of reading as scribbles
        hb = cv2.GaussianBlur(hair.astype(np.float32) / 255, (0, 0), max(0.6, HAIR_SOFT * scale))
        hb = np.clip((hb - 0.18) / 0.45, 0, 1); hair = (hb * hb * (3 - 2 * hb) * 255).astype(np.uint8)
    sheer = np.zeros((H, W), np.float32)
    for p, a in fig["sheer"]:
        m = np.zeros((H, W), np.uint8); q = np.round(tx(p) * 16).astype(np.int32)
        x0, y0 = q.min(0) // 16; x1, y1 = q.max(0) // 16 + 2
        if x1 < 0 or y1 < 0 or x0 >= W or y0 >= H: continue
        cv2.fillPoly(m, [q], 255, cv2.LINE_AA, shift=4)
        sheer = 1 - (1 - sheer) * (1 - m.astype(np.float32) / 255 * a)
    so = solid.astype(np.float32) / 255; ha = hair.astype(np.float32) / 255
    a = 1 - (1 - so) * (1 - ha) * (1 - sheer)
    # chiffon is see-through only where nothing solid is behind it (it never lightens her body)
    return a, sheer * (1 - so) * (1 - ha)

def rimlight(alpha, light_dir, width_px, strength=1.0):
    """light wrapping the silhouette's edges that face the light (light_dir: screen vector toward the light).
    Thin parts (hair, chiffon) glow through. -> float32 0..1"""
    w = max(width_px, 0.6)
    ab = cv2.GaussianBlur(alpha, (0, 0), w)
    gx = cv2.Sobel(ab, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(ab, cv2.CV_32F, 0, 1, ksize=3)
    g = np.sqrt(gx * gx + gy * gy) + 1e-6
    L = np.asarray(light_dir, np.float32); L = L / np.linalg.norm(L)
    facing = np.clip(-(gx * L[0] + gy * L[1]) / g, 0, 1)
    edge = np.clip(alpha - cv2.GaussianBlur(cv2.erode(alpha, np.ones((3, 3), np.uint8), iterations=max(1, int(w))), (0, 0), w * 0.6), 0, 1)
    facing = facing ** 1.5
    return np.clip(edge * facing * 1.5 * strength, 0, 1) * alpha
