"""The founder's body and wardrobe as soft SDF shapes (numpy only; build_founder.py turns them into Blender objects).

Standing, arms in a relaxed A. Every primitive belongs to a bone, so skin weights come straight from the shapes
(the toon3d way). Garments are the body pushed out by a thickness, cut by planes, plus their own details
(collars, plackets, cuffs, belts). World space: metres, z up, facing -y, his left = +x.
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
TOON = os.path.join(HERE, '..', '..', 'great-idea-ted', 'toon3d')
sys.path.insert(0, TOON)
from sdf import *          # noqa: E402  (sphere, ellipsoid, capsule, round_box, plane, smin, smax, union, ...)

def nrm(v): v = np.asarray(v, float); return v / np.linalg.norm(v)

# ---------------------------------------------------------------- skeleton
def skeleton(Bd):
    J = {}
    J['root'] = np.array([0, 0.01, 0.0])
    J['hips'] = np.array([0, 0.012, 0.975]); J['spine'] = np.array([0, 0.012, 1.120]); J['chest'] = np.array([0, 0.010, 1.270])
    J['neck'] = np.array([0, 0.014, Bd['neck_z']]); J['head'] = np.array([0, 0.0, Bd['head_pivot_z']])
    J['head_top'] = np.array([0, 0.0, Bd['head_pivot_z'] + 0.20])
    for s, t in ((1, 'L'), (-1, 'R')):
        J['clav.' + t] = np.array([s * 0.035, 0.012, 1.475])
        J['shoulder.' + t] = np.array([s * Bd['shoulder_x'], 0.014, Bd['shoulder_z']])
        J['elbow.' + t] = np.array([s * (Bd['shoulder_x'] + 0.048), 0.030, 1.168])
        J['wrist.' + t] = np.array([s * (Bd['shoulder_x'] + 0.080), 0.004, 0.925])
        J['hand.' + t] = np.array([s * (Bd['shoulder_x'] + 0.092), -0.004, 0.770])
        J['hip.' + t] = np.array([s * 0.094, 0.012, 0.930])
        J['knee.' + t] = np.array([s * 0.100, 0.002, 0.505])
        J['ankle.' + t] = np.array([s * 0.106, 0.030, 0.088])
        J['toe.' + t] = np.array([s * 0.112, -0.125, 0.030])
    return J

def bones(J):
    B = [('root', J['root'], J['root'] + [0, 0, 0.1], None), ('hips', J['hips'], J['spine'], 'root'),
         ('spine', J['spine'], J['chest'], 'hips'), ('chest', J['chest'], J['neck'], 'spine'),
         ('neck', J['neck'], J['head'], 'chest'), ('head', J['head'], J['head_top'], 'neck')]
    for t in ('L', 'R'):
        B += [('shoulder.' + t, J['clav.' + t], J['shoulder.' + t], 'chest'),
              ('upper_arm.' + t, J['shoulder.' + t], J['elbow.' + t], 'shoulder.' + t),
              ('forearm.' + t, J['elbow.' + t], J['wrist.' + t], 'upper_arm.' + t),
              ('hand.' + t, J['wrist.' + t], J['hand.' + t], 'forearm.' + t),
              ('thigh.' + t, J['hip.' + t], J['knee.' + t], 'hips'),
              ('shin.' + t, J['knee.' + t], J['ankle.' + t], 'thigh.' + t),
              ('foot.' + t, J['ankle.' + t], J['toe.' + t], 'shin.' + t)]
    return B

# ---------------------------------------------------------------- body parts
def torso_parts(Bd, J):
    P = [('chest', ellipsoid((0, 0.012, Bd['chest_z']), (Bd['chest_w'], Bd['chest_d'], Bd['chest_h']))),
         ('spine', ellipsoid((0, 0.010, Bd['waist_z']), (Bd['waist_w'], Bd['waist_d'], 0.12))),
         ('hips', ellipsoid((0, 0.016, Bd['pelvis_z']), (Bd['pelvis_w'], Bd['pelvis_d'], 0.105)))]
    for s, t in ((1, 'L'), (-1, 'R')):
        P.append(('chest', ellipsoid((s * 0.080, -0.058, 1.335), (0.092, 0.062, 0.070))))        # pecs
        P.append(('chest', ellipsoid((s * 0.150, 0.030, 1.240), (0.075, 0.085, 0.125))))         # lats (the V)
        P.append(('shoulder.' + t, sphere((s * Bd['shoulder_x'], 0.014, Bd['shoulder_z'] - 0.012), Bd['delt_r'])))
        P.append(('chest', capsule((0, 0.030, 1.485), (s * (Bd['shoulder_x'] - 0.04), 0.022, 1.462), Bd['trap_r'])))
    return P

def arm_parts(Bd, J):
    P = []
    for t in ('L', 'R'):
        sh, el, wr = J['shoulder.' + t] + [0, 0, -0.015], J['elbow.' + t], J['wrist.' + t]
        P.append(('upper_arm.' + t, capsule(sh, el, Bd['upper_r'], Bd['elbow_r'])))
        mid = sh + (el - sh) * 0.45
        P.append(('upper_arm.' + t, ellipsoid(mid + [0, -0.010, 0], (0.050, 0.053, 0.085))))       # biceps
        P.append(('forearm.' + t, capsule(el, wr, Bd['elbow_r'], Bd['wrist_r'])))
        P.append(('forearm.' + t, ellipsoid(el + (wr - el) * 0.28, (0.046, 0.046, 0.080))))
    return P

def leg_parts(Bd, J):
    P = []
    for t in ('L', 'R'):
        hp, kn, an = J['hip.' + t], J['knee.' + t], J['ankle.' + t]
        P.append(('thigh.' + t, capsule(hp + [0, 0, 0.02], kn, Bd['thigh_r'], Bd['knee_r'])))
        P.append(('shin.' + t, capsule(kn, an, Bd['knee_r'] * 0.98, Bd['ankle_r'])))
        P.append(('shin.' + t, ellipsoid(kn + (an - kn) * 0.30 + [0, 0.018, 0], (0.050, 0.052, 0.100))))  # calf
    return P

def foot_parts(Bd, J):
    P = []
    for t in ('L', 'R'):
        an, to = J['ankle.' + t], J['toe.' + t]
        P.append(('foot.' + t, capsule(an + [0, 0.02, -0.04], to + [0, 0, -0.005], 0.040, 0.030)))
    return P

def neck_part(Bd):
    return ('neck', capsule((0, 0.022, 1.44), (0, 0.004, Bd['head_center_z'] - 0.03), Bd['neck_r'], Bd['neck_r'] * 0.95))

def blend(parts, k): return union([g for _, g in parts], k)

def weights(parts, P, tau=0.016):
    names = sorted(set(b for b, _ in parts))
    W = np.zeros((len(P), len(names)), np.float32)
    for b, g in parts:
        d = np.maximum(g(P), 0)
        W[:, names.index(b)] = np.maximum(W[:, names.index(b)], np.exp(-d / tau))
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    return names, W

def hand_frame(J, t):
    s = 1 if t == 'L' else -1
    w, h = J['wrist.' + t], J['hand.' + t]
    y = nrm(h - w)
    x0 = np.array([0, -1.0 * s, 0])
    x = nrm(x0 - (x0 @ y) * y)
    z = np.cross(x, y)
    return w, np.stack([x, y, z], 1), s

def hand(Bd, J, t):
    """a relaxed hand: palm toward the thigh, fingers softly curled, the thumb forward."""
    w, M, s = hand_frame(J, t)
    sc = Bd['hand_scale']
    L = lambda p: (np.asarray(p, float) * sc) @ M.T + w
    parts = [round_box(L((0, 0.046, 0)), np.array((0.041, 0.047, 0.0150)) * sc, 0.013 * sc, M)]
    xs = [s * 0.027, s * 0.009, -s * 0.009, -s * 0.026]; ln = [0.056, 0.062, 0.058, 0.046]
    for i, (fx, fl) in enumerate(zip(xs, ln)):
        a = L((fx, 0.086, 0.001)); seg = fl / 2
        c1 = L((fx * 1.02, 0.086 + seg, -0.010)); c2 = L((fx * 1.04, 0.086 + seg * 1.65, -0.030))
        r0 = 0.0112 * sc * (0.9 if i == 3 else 1.0)
        parts += [capsule(a, c1, r0, r0 * 0.96), capsule(c1, c2, r0 * 0.96, r0 * 0.86)]
    tb = L((s * 0.036, 0.020, -0.004)); t1 = L((s * 0.054, 0.050, -0.010)); t2 = L((s * 0.050, 0.078, -0.020))
    parts += [capsule(tb, t1, 0.0140 * sc, 0.0128 * sc), capsule(t1, t2, 0.0128 * sc, 0.0112 * sc)]
    parts.append(capsule(w + (J['hand.' + t] - w) * -0.25, w + (J['hand.' + t] - w) * 0.12, Bd['wrist_r'] * 0.95, Bd['wrist_r'] * 1.05))
    return union(parts, 0.0075 * sc)

# ---------------------------------------------------------------- garment helpers
def slab_z(f, z0, z1, k=0.003):
    """keep f between heights z0 and z1"""
    return intersect(intersect(f, plane((0, 0, -1), z0), k), plane((0, 0, 1), -z1), k)

def cut_along(f, a, b, at, k=0.002, reach=0.085):
    """cut a sleeve: keep the part of f on a's side of the plane through a + (b - a) * at (normal along a -> b),
    but only near the limb (within `reach` of the segment a -> b, extended past b), so the body is untouched"""
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = nrm(b - a); c = a + (b - a) * at
    pl = plane(d, -(c @ d))
    near = capsule(a + (b - a) * 0.3, b + d * 0.25, reach)
    def g(p):
        v = f(p)
        m = near(p) < 0
        if m.any(): v = v.copy(); v[m] = smax(v[m], pl(p[m]), k)
        return v
    return g

def ring(f_body, off, thick, z0, z1, k=0.003):
    """a band hugging the body: the shell between off and off + thick, between heights z0 and z1"""
    shell = lambda p: np.abs(f_body(p) - off - thick / 2) - thick / 2
    return slab_z(shell, z0, z1, k)

def band_along(f_body, a, b, t0, t1, off, thick, k=0.003):
    """a cuff: the shell of f_body between fractions t0..t1 of the segment a -> b"""
    shell = lambda p: np.abs(f_body(p) - off - thick / 2) - thick / 2
    a = np.asarray(a); b = np.asarray(b); d = nrm(b - a)
    c0 = a + (b - a) * t0; c1 = a + (b - a) * t1
    g = intersect(shell, plane(-d, c0 @ d), k)
    return intersect(g, plane(d, -(c1 @ d)), k)

def polyline_tube(pts, r, k=0.004):
    pts = [np.asarray(p, float) for p in pts]
    rr = r if hasattr(r, '__len__') else [r] * len(pts)
    return union([capsule(pts[i], pts[i + 1], rr[i], rr[i + 1]) for i in range(len(pts) - 1)], k)

def v_open(z_bot, z_top, w_bot, w_top, y_max=-0.02):
    """the front opening of a garment: |x| < w(z) between z_bot and z_top, front half only. Inside < 0."""
    def f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        tz = np.clip((z - z_bot) / (z_top - z_bot), 0, 1)
        w = w_bot + (w_top - w_bot) * tz
        d = np.abs(x) - w
        d = np.maximum(d, z_bot - z)
        d = np.maximum(d, y - y_max)
        return d
    return f

# ---------------------------------------------------------------- shoes
def sneaker(J, t):
    """chunky designer sneaker: upper, sole, heel tab (separate SDFs, foot space)"""
    an, to = J['ankle.' + t], J['toe.' + t]
    x = an[0] * 1.0
    upper = union([round_box((x, -0.035, 0.070), (0.050, 0.118, 0.042), 0.036),
                   round_box((x, 0.025, 0.095), (0.046, 0.055, 0.048), 0.034),
                   ellipsoid((x, -0.115, 0.055), (0.049, 0.060, 0.035))], 0.02)
    collar = capsule((x, 0.040, 0.128), (x, 0.010, 0.122), 0.040)
    upper = subtract(union([upper, collar], 0.015), capsule((x, 0.018, 0.13), (x, 0.010, 0.20), 0.034), 0.006)
    sole = round_box((x, -0.035, 0.020), (0.056, 0.128, 0.021), 0.016)
    tab = round_box((x, 0.078, 0.105), (0.014, 0.010, 0.026), 0.008)
    return upper, sole, tab

def loafer(J, t):
    an = J['ankle.' + t]; x = an[0]
    upper = union([round_box((x, -0.035, 0.055), (0.049, 0.118, 0.032), 0.030),
                   ellipsoid((x, -0.110, 0.045), (0.048, 0.062, 0.030))], 0.02)
    upper = subtract(upper, ellipsoid((x, 0.020, 0.105), (0.040, 0.075, 0.040)), 0.008)
    sole = round_box((x, -0.035, 0.010), (0.052, 0.124, 0.011), 0.008)
    return upper, sole

def slide(J, t):
    an = J['ankle.' + t]; x = an[0]
    strap = intersect(round_box((x, -0.060, 0.045), (0.054, 0.050, 0.030), 0.026), plane((0, 0, -1), 0.030), 0.004)
    sole = round_box((x, -0.035, 0.014), (0.055, 0.125, 0.014), 0.010)
    return strap, sole

# ---------------------------------------------------------------- wardrobe
def garments(kind, Bd, J):
    """returns a list of (name, sdf, material key, box lo, box hi, step, parts-for-weights)"""
    tp, ap, lp = torso_parts(Bd, J), arm_parts(Bd, J), leg_parts(Bd, J)
    f_torso = blend(tp, 0.06); f_arms = blend(ap, 0.03); f_legs = blend(lp, 0.03)
    f_upper = union([f_torso, f_arms], 0.035)
    f_lower = union([blend([tp[2]], 0), f_legs], 0.05)
    out = []
    top_lo, top_hi = (-0.42, -0.24, 0.80), (0.42, 0.20, 1.62)
    bot_lo, bot_hi = (-0.24, -0.20, 0.06), (0.24, 0.20, 1.10)
    neck_hole = capsule((0, 0.020, 1.40), (0, 0.004, 1.75), Bd['neck_r'] + 0.008)
    def cut_wrists(f, at=0.97):
        for t in ('L', 'R'):
            f = cut_along(f, J['elbow.' + t], J['wrist.' + t] + (J['wrist.' + t] - J['elbow.' + t]) * 0.05, at)
        return f
    def hollow_cuffs(f, wall):
        """open sleeve ends: near each cuff the sleeve is a tube (the arm pushed out a little is carved away),
        so looking down a sleeve shows the wrist inside it, not a flat cap"""
        for t in ('L', 'R'):
            el, wr = J['elbow.' + t], J['wrist.' + t]; d = nrm(wr - el)
            inner = intersect(offset(f_arms, wall), capsule(wr - d * 0.07, wr + d * 0.10, 0.075), 0.0)
            f = subtract(f, inner, 0.002)
        return f
    def trousers(off=0.014, hem=0.100, flare=0.0):
        f = offset(f_lower, off)
        if flare:
            f = union([f] + [capsule(J['knee.' + t], J['ankle.' + t], Bd['knee_r'] + off, Bd['ankle_r'] + off + flare) for t in ('L', 'R')], 0.02)
        f = slab_z(f, hem, 1.035)
        # the front crease: a soft ridge down each leg
        cr = union([capsule(J['hip.' + t] + [0, -0.075, -0.05], J['ankle.' + t] + [0, -0.044, 0.04], 0.0045) for t in ('L', 'R')], 0)
        f = union([f, slab_z(cr, hem, 0.95)], 0.012)
        return f
    shoes = []
    if kind in ('quarterzip', 'goggles'):
        for t in ('L', 'R'):
            u, s_, tab = sneaker(J, t)
            lo, hi = (J['ankle.' + t][0] - 0.08, -0.20, -0.01), (J['ankle.' + t][0] + 0.08, 0.13, 0.20)
            shoes += [('sneaker_' + t, u, 'leather', lo, hi, 0.0022, 'foot.' + t), ('sole_' + t, s_, 'sole', lo, hi, 0.0022, 'foot.' + t),
                      ('tab_' + t, tab, 'uv_satin', lo, hi, 0.0015, 'foot.' + t)]
    if kind == 'linen':
        for t in ('L', 'R'):
            u, s_ = loafer(J, t)
            lo, hi = (J['ankle.' + t][0] - 0.08, -0.20, -0.01), (J['ankle.' + t][0] + 0.08, 0.13, 0.16)
            shoes += [('loafer_' + t, u, 'suede', lo, hi, 0.0022, 'foot.' + t), ('lsole_' + t, s_, 'sole_dark', lo, hi, 0.0022, 'foot.' + t)]
    if kind in ('robe', 'pyjamas'):
        for t in ('L', 'R'):
            st, s_ = slide(J, t)
            lo, hi = (J['ankle.' + t][0] - 0.08, -0.20, -0.01), (J['ankle.' + t][0] + 0.08, 0.13, 0.10)
            shoes += [('slide_' + t, st, 'velvet', lo, hi, 0.0022, 'foot.' + t), ('ssole_' + t, s_, 'sole_dark', lo, hi, 0.0022, 'foot.' + t)]
    out += shoes
    wp = tp + ap

    if kind == 'quarterzip':
        # the knit: torso and arms pushed out, cut at the wrists and the hip, a stand collar, a zip opening
        f_low = slab_z(f_lower, 0.90, 1.06)
        f = offset(union([f_upper, f_low], 0.03), 0.016)
        f = slab_z(f, 0.955, 1.60)
        f = cut_wrists(f, 0.985)
        f = hollow_cuffs(f, 0.007)
        f = subtract(f, neck_hole, 0.004)
        collar = slab_z(lambda p: np.abs(capsule((0, 0.020, 1.40), (0, 0.006, 1.70), Bd['neck_r'] + 0.016)(p)) - 0.007, 1.455, 1.575, 0.004)
        f = union([f, collar], 0.01)
        zipv = v_open(1.395, 1.58, 0.004, 0.030, y_max=-0.03)
        f = subtract(f, zipv, 0.003)
        out.append(('qz_knit', f, 'knit_cream', top_lo, top_hi, 0.0036, wp))
        hem = ring(union([f_torso, f_low], 0.03), 0.016, 0.011, 0.932, 0.980)
        cuffs = union([band_along(f_arms, J['elbow.' + t], J['wrist.' + t], 0.86, 0.99, 0.012, 0.009) for t in ('L', 'R')], 0)
        out.append(('qz_rib', union([hem, cuffs], 0), 'rib_cream', top_lo, top_hi, 0.0028, wp))
        # the zip: tape along both edges of the opening, and the pull (ultraviolet tab)
        # the zip: two tapes lying on the knit along the edges of the opening
        def tapes(p, fk=f, zv=zipv):
            x, y, z = p[:, 0], p[:, 1], p[:, 2]
            tz = np.clip((z - 1.395) / (1.58 - 1.395), 0, 1); w = 0.004 + 0.026 * tz
            edge = np.abs(np.abs(x) - w - 0.003) - 0.0032
            d = np.maximum(np.abs(fk(p) - 0.0012) - 0.0016, edge)
            d = np.maximum(d, y + 0.03)
            return np.maximum(d, np.maximum(1.392 - z, z - 1.575))
        out.append(('qz_zip', tapes, 'charcoal_gloss', (-0.06, -0.20, 1.36), (0.06, -0.04, 1.60), 0.0010, wp))
        pull = union([round_box((0, -0.150, 1.388), (0.007, 0.004, 0.011), 0.003),
                      round_box((0, -0.153, 1.365), (0.0065, 0.0035, 0.016), 0.003)], 0.002)
        out.append(('qz_pull', pull, 'uv_metal', (-0.03, -0.18, 1.33), (0.03, -0.12, 1.42), 0.0008, wp))
        # the tee under it (charcoal), seen in the opening
        tee = slab_z(offset(f_torso, 0.004), 1.15, 1.50)
        tee = subtract(tee, capsule((0, 0.020, 1.40), (0, 0.004, 1.75), Bd['neck_r'] + 0.003), 0.003)
        out.append(('qz_tee', tee, 'jersey_charcoal', top_lo, top_hi, 0.004, tp))
        out.append(('trousers', trousers(), 'wool_charcoal', bot_lo, bot_hi, 0.0036, lp + [tp[2]]))

    if kind == 'robe':
        # plush terry robe: big shawl collar, belt with a knot, wide sleeves to mid-forearm, knee length
        f = offset(f_upper, 0.026)
        skirt = lambda p: (np.sqrt((p[:, 0] / (0.172 + 0.10 * np.clip((1.0 - p[:, 2]) / 0.5, 0, 1))) ** 2 +
                                   ((p[:, 1] - 0.015) / (0.128 + 0.05 * np.clip((1.0 - p[:, 2]) / 0.5, 0, 1))) ** 2) - 1) * 0.15
        f = union([f, slab_z(skirt, 0.46, 1.10)], 0.05)
        f = slab_z(f, 0.47, 1.62)
        for t in ('L', 'R'):   # wide sleeves: flare toward the cuff, cut at 60 % of the forearm
            f = union([f, capsule(J['elbow.' + t], J['elbow.' + t] + (J['wrist.' + t] - J['elbow.' + t]) * 0.62, Bd['elbow_r'] + 0.030, Bd['wrist_r'] + 0.045)], 0.02)
            f = cut_along(f, J['elbow.' + t], J['wrist.' + t], 0.62)
        opening = v_open(1.06, 1.60, 0.004, 0.105, y_max=0.0)
        f = subtract(f, opening, 0.004)
        f = subtract(f, capsule((0, 0.020, 1.40), (0, 0.004, 1.75), Bd['neck_r'] + 0.014), 0.006)
        out.append(('robe', f, 'terry_cream', (-0.44, -0.26, 0.44), (0.44, 0.24, 1.64), 0.0040, wp + lp))
        # shawl collar: a fat roll from the belt up both edges of the opening and round the back of the neck
        pts_l = [(0.012, -0.165, 1.07), (0.040, -0.150, 1.22), (0.075, -0.130, 1.37), (0.095, -0.090, 1.47), (0.085, -0.010, 1.53), (0.0, 0.055, 1.56)]
        pts_r = [(-x, y, z) for x, y, z in pts_l]
        roll = union([polyline_tube(pts_l, [0.022, 0.026, 0.030, 0.030, 0.028, 0.026]), polyline_tube(pts_r, [0.022, 0.026, 0.030, 0.030, 0.028, 0.026])], 0.01)
        roll = subtract(roll, capsule((0, 0.020, 1.40), (0, 0.004, 1.75), Bd['neck_r'] + 0.008), 0.004)
        out.append(('robe_collar', roll, 'terry_cream', (-0.16, -0.22, 1.00), (0.16, 0.10, 1.62), 0.0030, tp))
        pip_l = polyline_tube([(x + 0.0, y - 0.024, z) for x, y, z in pts_l[:4]], 0.0040)
        pip_r = polyline_tube([(x + 0.0, y - 0.024, z) for x, y, z in pts_r[:4]], 0.0040)
        # belt: a band at the waist, a knot at the front, two tails
        belt = ring(f_torso, 0.026, 0.012, 1.035, 1.080)
        knot = ellipsoid((0.03, -0.165, 1.058), (0.030, 0.018, 0.024))
        tail1 = polyline_tube([(0.03, -0.170, 1.05), (0.045, -0.178, 0.95), (0.052, -0.180, 0.84)], [0.013, 0.012, 0.012])
        tail2 = polyline_tube([(0.03, -0.170, 1.05), (0.010, -0.176, 0.96), (0.000, -0.178, 0.87)], [0.013, 0.012, 0.012])
        tails = lambda p: np.maximum(union([tail1, tail2], 0.004)(p), np.abs(p[:, 1] + 0.176) - 0.006)
        out.append(('robe_belt', union([belt, knot, tails], 0.006), 'terry_cream', (-0.24, -0.22, 0.80), (0.24, 0.18, 1.12), 0.0030, tp + lp))
        out.append(('robe_piping', union([pip_l, pip_r], 0.002), 'charcoal_satin', (-0.14, -0.21, 1.02), (0.14, -0.08, 1.52), 0.0012, tp))
        # the wrap's front edge, running from the belt to the hem
        edge = polyline_tube([(0.02, -0.170, 1.04), (0.06, -0.185, 0.80), (0.08, -0.195, 0.50)], 0.008)
        out.append(('robe_edge', edge, 'terry_cream', (-0.05, -0.24, 0.46), (0.14, -0.12, 1.08), 0.0025, tp + lp))

    if kind == 'goggles':
        # the festival coat: a long, oversized cream faux-fur coat, open, with ultraviolet satin lapels; a charcoal tank
        f = offset(f_upper, 0.040)
        skirt = lambda p: (np.sqrt((p[:, 0] / (0.190 + 0.08 * np.clip((1.0 - p[:, 2]) / 0.5, 0, 1))) ** 2 +
                                   ((p[:, 1] - 0.015) / (0.140 + 0.04 * np.clip((1.0 - p[:, 2]) / 0.5, 0, 1))) ** 2) - 1) * 0.15
        f = union([f, slab_z(skirt, 0.50, 1.10)], 0.05)
        f = slab_z(f, 0.52, 1.62)
        f = cut_wrists(f, 0.94)
        opening = v_open(0.40, 1.60, 0.060, 0.120, y_max=0.0)
        f = subtract(f, opening, 0.006)
        f = subtract(f, capsule((0, 0.020, 1.40), (0, 0.004, 1.75), Bd['neck_r'] + 0.022), 0.006)
        out.append(('coat', f, 'fur_cream', (-0.46, -0.28, 0.48), (0.46, 0.26, 1.66), 0.0042, wp + lp))
        lap_l = [(0.062, -0.205, 0.95), (0.075, -0.195, 1.20), (0.105, -0.170, 1.40), (0.125, -0.110, 1.50), (0.095, -0.010, 1.55), (0.0, 0.060, 1.58)]
        lap_r = [(-x, y, z) for x, y, z in lap_l]
        lap = union([polyline_tube(lap_l, [0.016, 0.020, 0.026, 0.026, 0.022, 0.020]), polyline_tube(lap_r, [0.016, 0.020, 0.026, 0.026, 0.022, 0.020])], 0.01)
        lap = subtract(lap, capsule((0, 0.020, 1.40), (0, 0.004, 1.75), Bd['neck_r'] + 0.012), 0.004)
        out.append(('coat_lapel', lap, 'uv_satin', (-0.18, -0.25, 0.90), (0.18, 0.10, 1.64), 0.0028, tp))
        tank = slab_z(offset(f_torso, 0.004), 0.95, 1.50)
        tank = subtract(tank, v_open(1.36, 1.52, 0.02, 0.09, y_max=0.0), 0.006)
        for t, s in (('L', 1), ('R', -1)):
            tank = subtract(tank, sphere((s * 0.215, 0.01, 1.36), 0.095), 0.01)
        tank = subtract(tank, neck_hole, 0.004)
        out.append(('tank', tank, 'jersey_charcoal', top_lo, top_hi, 0.004, tp))
        out.append(('trousers', trousers(), 'wool_charcoal', bot_lo, bot_hi, 0.0036, lp + [tp[2]]))

    if kind == 'linen':
        # cream linen shirt: open collar, sleeves rolled to the forearm, untucked; oatmeal linen trousers
        f = offset(f_upper, 0.016)
        tail = lambda p: p[:, 2] - (0.915 + 0.050 * np.clip(np.abs(p[:, 0]) / 0.16, 0, 1) ** 2)    # curved shirttail
        f = intersect(f, lambda p: -tail(p), 0.004)
        f = slab_z(f, 0.80, 1.60)
        for t in ('L', 'R'):
            f = cut_along(f, J['elbow.' + t], J['wrist.' + t], 0.42)
        f = subtract(f, v_open(1.36, 1.58, 0.004, 0.060, y_max=-0.03), 0.004)
        f = subtract(f, capsule((0, 0.020, 1.40), (0, 0.004, 1.75), Bd['neck_r'] + 0.010), 0.004)
        out.append(('shirt', f, 'linen_cream', (-0.44, -0.24, 0.80), (0.44, 0.20, 1.62), 0.0036, wp))
        rolls = union([band_along(f_arms, J['elbow.' + t], J['wrist.' + t], 0.34, 0.44, 0.019, 0.011) for t in ('L', 'R')], 0)
        out.append(('rolls', rolls, 'linen_cream', top_lo, top_hi, 0.0026, wp))
        # collar flaps folded open onto the chest
        flap_l = polyline_tube([(0.006, -0.150, 1.37), (0.040, -0.140, 1.45), (0.070, -0.110, 1.52), (0.070, -0.040, 1.56), (0.0, 0.050, 1.565)], [0.006, 0.010, 0.012, 0.010, 0.008])
        flap_r = polyline_tube([(-0.006, -0.150, 1.37), (-0.040, -0.140, 1.45), (-0.070, -0.110, 1.52), (-0.070, -0.040, 1.56), (0.0, 0.050, 1.565)], [0.006, 0.010, 0.012, 0.010, 0.008])
        flaps = lambda p: np.maximum(union([flap_l, flap_r], 0.006)(p), -offset(f_torso, 0.016)(p))
        out.append(('shirt_collar', flaps, 'linen_cream', (-0.14, -0.20, 1.30), (0.14, 0.10, 1.62), 0.0020, tp))
        btn = union([lambda p, z=z: (length((p - np.array([0, -0.155 + 0.0, z], np.float32)) * np.array([1, 2.2, 1], np.float32)) - 0.0065) for z in (1.30, 1.21, 1.12)], 0)
        out.append(('buttons', btn, 'button', (-0.02, -0.20, 1.08), (0.02, -0.10, 1.34), 0.0008, tp))
        out.append(('trousers', trousers(0.020, 0.075, flare=0.010), 'linen_oat', bot_lo, bot_hi, 0.0036, lp + [tp[2]]))

    if kind == 'pyjamas':
        # charcoal silk pyjamas with cream piping (notch collar, cuffs, pocket, trouser hems), ultraviolet sleep mask
        f = offset(f_upper, 0.015)
        f = slab_z(f, 0.90, 1.60)
        f = cut_wrists(f, 0.96)
        f = subtract(f, v_open(1.30, 1.58, 0.004, 0.065, y_max=-0.03), 0.004)
        f = subtract(f, capsule((0, 0.020, 1.40), (0, 0.004, 1.75), Bd['neck_r'] + 0.012), 0.004)
        out.append(('pj_top', f, 'satin_charcoal', top_lo, top_hi, 0.0036, wp))
        lap_l = [(0.006, -0.150, 1.30), (0.040, -0.142, 1.42), (0.075, -0.112, 1.51), (0.080, -0.040, 1.555), (0.0, 0.052, 1.565)]
        lap_r = [(-x, y, z) for x, y, z in lap_l]
        lap = union([polyline_tube(lap_l, [0.006, 0.010, 0.012, 0.010, 0.008]), polyline_tube(lap_r, [0.006, 0.010, 0.012, 0.010, 0.008])], 0.006)
        lap = lambda p, g=lap: np.maximum(g(p), -offset(f_torso, 0.015)(p))
        out.append(('pj_collar', lap, 'satin_charcoal', (-0.14, -0.20, 1.24), (0.14, 0.10, 1.62), 0.0020, tp))
        pip = union([polyline_tube([(x, y - 0.010, z) for x, y, z in lap_l[:4]], 0.0032), polyline_tube([(x, y - 0.010, z) for x, y, z in lap_r[:4]], 0.0032)], 0.002)
        cuffs = union([band_along(f_arms, J['elbow.' + t], J['wrist.' + t], 0.93, 0.96, 0.016, 0.006) for t in ('L', 'R')], 0)
        hemp = union([band_along(f_legs, J['knee.' + t], J['ankle.' + t], 0.86, 0.89, 0.020, 0.006) for t in ('L', 'R')], 0)
        pocket = round_box((0.105, -0.182, 1.315), (0.042, 0.004, 0.045), 0.006)
        pocket_pipe = lambda p: np.maximum(np.abs(pocket(p)) - 0.0022, -(p[:, 2] - 1.355))
        hem_top = ring(f_upper, 0.015, 0.006, 0.900, 0.912)
        out.append(('pj_piping', union([pip, cuffs, hemp, hem_top], 0), 'satin_cream', (-0.42, -0.24, 0.10), (0.42, 0.20, 1.60), 0.0024, wp + lp))
        out.append(('pj_pocket', pocket_pipe, 'satin_cream', (0.04, -0.22, 1.25), (0.17, -0.14, 1.38), 0.0010, tp))
        out.append(('pj_trousers', trousers(0.020, 0.105, flare=0.008), 'satin_charcoal', bot_lo, bot_hi, 0.0036, lp + [tp[2]]))
    return out

# ---------------------------------------------------------------- the swoop (the signature)
def swoop_curve(state='set', S=48):
    """the spine of the swoop in head space, and its half width / height along it.
    'set': one glossy wave rising off the part on his left, rolling up and over to his right, the crest above the
    right brow. 'fallen': the same lock collapsed forward over his forehead (the unfollow)."""
    s = np.linspace(0, 1, S)
    if state == 'set':
        K = np.array([(0.058, 0.040, 0.118), (0.050, -0.010, 0.138), (0.028, -0.060, 0.152), (-0.006, -0.094, 0.160),
                      (-0.040, -0.106, 0.150), (-0.068, -0.096, 0.126), (-0.082, -0.070, 0.104)])
    else:
        K = np.array([(0.058, 0.040, 0.118), (0.046, -0.012, 0.128), (0.026, -0.070, 0.118), (0.004, -0.108, 0.088),
                      (-0.018, -0.124, 0.058), (-0.034, -0.126, 0.036), (-0.044, -0.122, 0.020)])
    u = np.linspace(0, 1, len(K))
    C = np.stack([np.interp(s, u, K[:, i]) for i in range(3)], 1)
    # Catmull-Rom-ish smoothing of the polyline
    for _ in range(40):
        C[1:-1] = 0.5 * C[1:-1] + 0.25 * (C[:-2] + C[2:])
    w = 0.012 + 0.036 * np.sin(np.pi * np.clip(s * 0.95 + 0.05, 0, 1)) ** 0.7           # half width across the lock
    h = 0.006 + 0.019 * np.sin(np.pi * np.clip(s, 0, 1)) ** 0.9                          # half thickness
    if state != 'set':
        w = w * 0.92; h = h * 0.85
    return C, w, h

def swoop_mesh(state='set', S=96, n_a=48, center=(0, 0.014, 0.0), grooves=7, groove=0.0016):
    """a lofted lock: an ellipse-ish section swept along the spine, the section's flat side against the skull,
    lengthwise grooves on top. Fixed topology (S x n_a), so 'fallen' is a shape key of 'set'."""
    C, w, h = swoop_curve(state, S)
    c = np.asarray(center, float)
    t = np.gradient(C, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True)
    out = C - c; out = out - (out * t).sum(1, keepdims=True) * t; out /= np.linalg.norm(out, axis=1, keepdims=True)
    if state != 'set':      # the fallen lock hangs: its "out" tips forward
        fw = np.array([0, -1.0, 0.0])
        mix = np.clip(np.linspace(-0.2, 1.2, S), 0, 1)[:, None]
        out = out * (1 - 0.5 * mix) + fw * 0.5 * mix
        out = out - (out * t).sum(1, keepdims=True) * t; out /= np.linalg.norm(out, axis=1, keepdims=True)
    b = np.cross(t, out)
    a = np.linspace(0, 2 * np.pi, n_a, endpoint=False)
    ca, sa = np.cos(a), np.sin(a)
    # section: top half rounder (the wave's crown), bottom half flatter (sits on the cap)
    hh = np.where(sa > 0, 1.0, 0.45)
    gro = 1 - groove / 0.02 * (0.5 + 0.5 * np.cos(grooves * 2 * np.pi * (0.5 + 0.5 * ca))) * (sa > 0)
    V = (C[:, None, :] + (ca[None, :, None] * w[:, None, None]) * b[:, None, :]
         + (sa * hh * gro)[None, :, None] * h[:, None, None] * out[:, None, :] + (h * 0.55)[:, None, None] * out[:, None, :])
    V = V.reshape(-1, 3)
    V = np.concatenate([V, C[:1] - t[:1] * 0.004, C[-1:] + t[-1:] * 0.006])
    F = []
    for i in range(S - 1):
        for j in range(n_a):
            F.append((i * n_a + j, (i + 1) * n_a + j, (i + 1) * n_a + (j + 1) % n_a, i * n_a + (j + 1) % n_a))
    c0, c1 = S * n_a, S * n_a + 1
    for j in range(n_a):
        F.append((c0, j, (j + 1) % n_a))
        F.append((c1, (S - 1) * n_a + (j + 1) % n_a, (S - 1) * n_a + j))
    return V, F

# ---------------------------------------------------------------- accessories
def watch(J, t='L'):
    """a luxury steel watch on the wrist (case, bezel, dial, strap), in world space at rest"""
    el, wr = J['elbow.' + t], J['wrist.' + t]
    d = nrm(wr - el); s = 1 if t == 'L' else -1
    c = wr + d * 0.012          # just past the cuff, so it shows below every sleeve
    outv = nrm(np.array([s, 0, 0]) - (np.array([s, 0, 0]) @ d) * d)    # back of the wrist faces out
    strap = lambda p: np.maximum(np.abs(length((p - c) - ((p - c) @ d)[:, None] * d) - 0.036) - 0.0045, np.abs((p - c) @ d) - 0.010)
    cc = c + outv * 0.036
    case = lambda p: np.maximum(length((p - cc) - ((p - cc) @ outv)[:, None] * outv) - 0.020, np.abs((p - cc) @ outv) - 0.0055)
    dialc = cc + outv * 0.0055
    dial = lambda p: np.maximum(length((p - dialc) - ((p - dialc) @ outv)[:, None] * outv) - 0.0165, np.abs((p - dialc) @ outv) - 0.0008)
    return dict(strap=strap, case=case, dial=dial, center=cc, out=outv)

def goggles_sdf(H_eye):
    """festival goggles over the eyes (head space): two round lenses in charcoal leather cups, a strap round the head"""
    ex, ey, ez = H_eye
    cups = union([capsule((s * ex, ey - 0.004, ez), (s * ex, ey - 0.026, ez), 0.026) for s in (-1, 1)], 0.004)
    bridge = capsule((-ex + 0.02, ey - 0.020, ez), (ex - 0.02, ey - 0.020, ez), 0.006)
    frame_ = subtract(union([cups, bridge], 0.006), union([capsule((s * ex, ey - 0.020, ez), (s * ex, ey - 0.040, ez), 0.019) for s in (-1, 1)], 0), 0.002)
    lens = union([capsule((s * ex, ey - 0.020, ez), (s * ex, ey - 0.023, ez), 0.0195) for s in (-1, 1)], 0)
    strap = lambda p: np.maximum(np.abs(length((p - np.array([0, 0.014, 0], np.float32)) * np.array([1 / 0.104, 1 / 0.120, 1e-3], np.float32)) - 1) * 0.1 - 0.0028,
                                 np.abs(p[:, 2] - ez) - 0.010)
    return frame_, lens, strap

def mask_sdf(H_eye, f_head):
    """a satin sleep mask over the eyes (head space): the face pushed out, between the brows and the cheekbones"""
    ex, ey, ez = H_eye
    shell = lambda p: np.abs(f_head(p) - 0.009) - 0.0045
    region = lambda p: np.maximum(np.maximum(np.abs(p[:, 2] - ez) - 0.026 + 0.010 * (np.abs(p[:, 0]) < 0.012), np.abs(p[:, 0]) - 0.088), p[:, 1] + 0.02)
    m = intersect(shell, region, 0.004)
    strap = lambda p: np.maximum(np.abs(length((p - np.array([0, 0.014, 0], np.float32)) * np.array([1 / 0.100, 1 / 0.116, 1e-3], np.float32)) - 1) * 0.1 - 0.0025,
                                 np.abs(p[:, 2] - ez - 0.004) - 0.008)
    return m, strap


# ---------------------------------------------------------------- the swoop, v2: a sculpted volume + a hinge for the fall
def swoop_sdf(f_head):
    """head space. One glossy wave: it rises off the hard part on his left, rolls up over the front of the head and
    breaks to his right, the crest standing proud above the right brow, a shadowed curl under the crest."""
    body = ellipsoid((0.000, -0.035, 0.118), (0.092, 0.092, 0.040))
    crest = capsule((0.050, -0.098, 0.128), (-0.056, -0.108, 0.152), 0.026, 0.032)
    rise = capsule((0.062, 0.000, 0.112), (0.026, -0.080, 0.140), 0.016, 0.026)
    root_ = ellipsoid((0.0, -0.080, 0.092), (0.080, 0.036, 0.034))      # the wave grows out of the hairline
    f = union([body, crest, rise, root_], 0.030)
    curl = capsule((0.050, -0.130, 0.104), (-0.062, -0.142, 0.122), 0.014, 0.016)      # the undercut of the crest
    f = subtract(f, curl, 0.010)
    f = subtract(f, offset(f_head, 0.002), 0.004)                                       # sits on the cap, never inside
    return f

def swoop_grooves(V, N, n=7, amp=0.0022):
    """lengthwise combing: ridges running back from the crest toward the part"""
    a = np.arctan2(V[:, 0] - 0.07, V[:, 1] - 0.03)
    g = np.sin(n * 2 * np.pi * (a / np.pi))
    return V + N * (amp * g)[:, None]

def swoop_fall(V, f_head):
    """the unfollow: the wave lets go. Every point hinges forward and down about the part, more the further forward it
    sits, squashes thinner, and is pushed back out of the head where the hinge would sink it."""
    piv = np.array([0.0, -0.020, 0.120])
    q = V - piv
    w = np.clip(-V[:, 1] / 0.12, 0, 1) ** 1.3
    ang = np.radians(45) * w
    y = q[:, 1] * np.cos(ang) - q[:, 2] * np.sin(ang)
    z = q[:, 1] * np.sin(ang) + q[:, 2] * np.cos(ang)
    P = np.stack([q[:, 0] * (1 - 0.08 * w) - 0.012 * w, y, z], 1) + piv
    # limp: the tip drops a little more over his right eye
    P[:, 2] -= 0.020 * w * np.clip(-P[:, 0] / 0.06, 0, 1)
    for _ in range(6):
        d = f_head(P.astype(np.float32))
        n = grad(f_head, P.astype(np.float32))
        P = P + n * np.maximum(0.008 - d, 0)[:, None]
    return P
