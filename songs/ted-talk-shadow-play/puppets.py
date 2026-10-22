"""Cut-paper shadow puppets, side view (the way shadow theatre is always seen).

A puppet is built from smooth parts — a profile head with a cut-out eye, hair, a curved torso, tapered two-segment
arms and legs, shoes, clothes — posed by joint angles and drawn as one silhouette into a mask. Small holes (buttons,
lace, the eye) are cut out of the paper, like real cut-paper puppets. Parts can carry coloured gel (the narrator's
red hair clip), which lets the lamp's light through in colour.

Body units: a standing adult is 1.0 tall; y grows downward; the feet are at (0, 0); the puppet faces +x."""
import math
import numpy as np, cv2

SH = 3; SC = 1 << SH

def rot(v, a):
    c, s = math.cos(a), math.sin(a); return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])

_BASIS = {}
def _basis(n):
    if n not in _BASIS:
        u = np.linspace(0, 1, n, endpoint=False)
        _BASIS[n] = 0.5 * np.stack([-u + 2 * u ** 2 - u ** 3, 2 - 5 * u ** 2 + 3 * u ** 3, u + 4 * u ** 2 - 3 * u ** 3, -u ** 2 + u ** 3], 1)
    return _BASIS[n]

def smooth(P, n=6, closed=True):
    """Catmull-Rom through the points"""
    P = np.asarray(P, float); m = len(P)
    if closed:
        idx = np.arange(m); i0, i1, i2, i3 = (idx - 1) % m, idx, (idx + 1) % m, (idx + 2) % m
    else:
        idx = np.arange(m - 1); i0 = np.maximum(idx - 1, 0); i1 = idx; i2 = idx + 1; i3 = np.minimum(idx + 2, m - 1)
    seg = np.stack([P[i0], P[i1], P[i2], P[i3]], 1)
    out = np.einsum('nk,skd->snd', _basis(n), seg).reshape(-1, 2)
    if not closed: out = np.vstack([out, P[-1:]])
    return out

def ellipse_pts(c, rx, ry, ang=0.0, n=40):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    P = np.stack([rx * np.cos(t), ry * np.sin(t)], 1)
    c_, s_ = math.cos(ang), math.sin(ang)
    return np.asarray(c, float) + P @ np.array([[c_, s_], [-s_, c_]])

def limb(J, Wf, Wb=None, cap=True):
    """a tapered limb along joint chain J; Wf/Wb: half-widths on the front/back side at each joint"""
    J = np.asarray(J, float); Wb = Wf if Wb is None else Wb
    L = [], []
    for i in range(len(J)):
        d = J[min(i + 1, len(J) - 1)] - J[max(i - 1, 0)]; d = d / (np.hypot(*d) + 1e-9); nrm = np.array([-d[1], d[0]])
        L[0].append(J[i] + nrm * Wf[i]); L[1].append(J[i] - nrm * Wb[i])
    a, b = L
    out = list(a)
    if cap:   # round end
        d = J[-1] - J[-2]; ang = math.atan2(d[1], d[0]); r = (Wf[-1] + Wb[-1]) / 2
        for t in np.linspace(-math.pi / 2, math.pi / 2, 7)[1:-1]: out.append(J[-1] + rot(np.array([r, 0]), ang - t))
    out += list(b[::-1])
    if cap:
        d = J[0] - J[1]; ang = math.atan2(d[1], d[0]); r = (Wf[0] + Wb[0]) / 2
        for t in np.linspace(-math.pi / 2, math.pi / 2, 7)[1:-1]: out.append(J[0] + rot(np.array([r, 0]), ang - t))
    return smooth(out, 3)

# a profile, facing +x; head radius 1, centre (0, 0)
PROFILE = np.array([(0.0, -1.06), (0.42, -0.98), (0.74, -0.76), (0.88, -0.44), (0.90, -0.24), (0.97, -0.17), (0.93, -0.08),
                    (1.02, 0.06), (1.12, 0.17), (1.02, 0.23), (0.93, 0.27), (0.98, 0.33), (0.95, 0.39), (0.90, 0.42),
                    (0.95, 0.47), (0.90, 0.54), (0.84, 0.58), (0.85, 0.68), (0.78, 0.78), (0.58, 0.84), (0.36, 0.86),
                    (0.22, 1.02), (-0.22, 1.02), (-0.56, 0.66), (-0.86, 0.22), (-0.95, -0.25), (-0.80, -0.70), (-0.42, -1.00)])
NOSE = slice(5, 10); CHIN = slice(15, 20)

HAIR = {
    "short": [(-0.96, 0.25), (-1.06, -0.30), (-0.88, -0.86), (-0.42, -1.18), (0.20, -1.20), (0.66, -1.00), (0.88, -0.70),
              (0.82, -0.52), (0.52, -0.64), (0.12, -0.70), (-0.30, -0.52), (-0.56, -0.12), (-0.66, 0.30)],
    "bob": [(-0.66, 1.06), (-1.04, 0.70), (-1.16, 0.10), (-1.06, -0.55), (-0.70, -1.06), (-0.10, -1.26), (0.50, -1.16),
            (0.86, -0.86), (0.96, -0.50), (0.80, -0.42), (0.56, -0.62), (0.22, -0.70), (0.02, -0.42), (-0.10, 0.30),
            (-0.18, 0.96)],
    "pony": [(-0.94, 0.12), (-1.06, -0.40), (-0.84, -0.92), (-0.30, -1.20), (0.36, -1.15), (0.78, -0.88), (0.90, -0.58),
             (0.60, -0.66), (0.14, -0.66), (-0.36, -0.46), (-0.80, -0.36), (-1.30, -0.30), (-1.62, 0.10), (-1.70, 0.70),
             (-1.52, 1.25), (-1.46, 0.70), (-1.32, 0.25), (-1.02, 0.18)],
    "long": [(-0.50, 1.90), (-1.02, 1.55), (-1.20, 0.80), (-1.18, 0.0), (-1.06, -0.60), (-0.70, -1.08), (-0.06, -1.25),
             (0.52, -1.12), (0.88, -0.82), (0.94, -0.52), (0.62, -0.60), (0.24, -0.60), (-0.08, 0.10), (-0.20, 1.10)],
    "bun": [(-0.94, 0.12), (-1.04, -0.42), (-0.84, -0.94), (-0.30, -1.20), (0.36, -1.15), (0.78, -0.88), (0.90, -0.58),
            (0.60, -0.66), (0.14, -0.66), (-0.36, -0.46), (-0.70, 0.12)],
    "curly": None, "bald": None,
}

class Pose:
    """joint angles in radians. Arms: 0 = hanging down, + = swung forward. Legs: hip + = thigh forward, knee + = bend."""
    def __init__(s, **k):
        s.lean = 0.0; s.head = 0.0
        s.sh_f = 0.10; s.el_f = 0.20; s.sh_b = -0.08; s.el_b = 0.15
        s.hip_f = 0.0; s.kn_f = 0.0; s.hip_b = 0.0; s.kn_b = 0.0
        s.slump = 0.0; s.sit = 0.0; s.mouth = 0.0; s.hand_open = 0.0
        for a, b in k.items(): setattr(s, a, b)
    def copy(s, **k):
        p = Pose(**s.__dict__)
        for a, b in k.items(): setattr(p, a, b)
        return p

class Puppet:
    def __init__(s, name, height=1.0, hair="short", build=1.0, dress=None, nose=1.0, chin=1.0, details=()):
        s.name, s.h, s.hair, s.build, s.dress, s.nose, s.chin = name, height, hair, build, dress, nose, chin
        s.details = set(details)

    def parts(s, pose, x, y, scale, facing=1):
        """polygons in screen coordinates: (polys, holes, gels, rods, anchors)"""
        S = scale * s.h; f = facing; b = s.build
        def P(v):
            v = np.asarray(v, float)
            return np.stack([x + f * v[..., 0] * S, y + v[..., 1] * S], -1)
        polys, holes, gels, rods = [], [], [], []
        sit = pose.sit; lean = pose.lean + 0.12 * pose.slump
        hip = np.array([-0.05 * sit, -0.475 + 0.205 * sit])
        def T(v): return hip + rot(np.asarray(v, float) - np.array([0, -0.475]), lean)    # torso space -> body
        # ---------------- legs (trousers or bare under a skirt), shoes
        def leg(ha, ka, back):
            h0 = hip + np.array([-0.01 if back else 0.008, 0.0])
            if sit > 0: ha = ha + 1.45 * sit; ka = ka + 1.5 * sit
            k = h0 + rot(np.array([0.0, 0.245]), -ha)
            a = k + rot(np.array([0.0, 0.24]), -ha + ka)
            th = [0.050 * b, 0.038 * b, 0.030 * b, 0.022 * b]
            mid = (k + a) / 2 + rot(np.array([-0.004, 0]), -ha + ka)
            J = [h0, (h0 + k) / 2, k, mid, a]
            Wf = [0.046 * b, 0.040 * b, 0.031 * b, 0.029 * b, 0.022 * b]
            Wb = [0.050 * b, 0.042 * b, 0.031 * b, 0.036 * b, 0.022 * b]
            out = [limb(J, Wf, Wb)]
            sole = rot(np.array([1.0, 0.0]), ka - ha) if sit > 0.5 else np.array([1.0, 0.0])
            toe = a + sole * 0.088 + np.array([0, 0.012]); heel = a - sole * 0.032 + np.array([0, 0.018])
            shoe = smooth([a + np.array([-0.025, -0.012]), a + np.array([0.02, -0.018]), toe + np.array([-0.01, -0.022]), toe,
                           toe + np.array([-0.012, 0.014]), heel + np.array([0.0, 0.012]), heel + np.array([-0.006, -0.012])], 4)
            out.append(shoe)
            return out
        for part in leg(pose.hip_b, pose.kn_b, True) + leg(pose.hip_f, pose.kn_f, False): polys.append(P(part))
        # ---------------- torso
        tor = [(0.034, -0.815), (0.074, -0.772), (0.090, -0.706), (0.074, -0.630), (0.060, -0.572), (0.072, -0.512),
               (0.070, -0.462), (0.0, -0.445), (-0.074, -0.452), (-0.088, -0.505), (-0.062, -0.585), (-0.068, -0.665),
               (-0.082, -0.735), (-0.064, -0.798), (-0.022, -0.818)]
        tor = [(px * b, py) for px, py in tor]
        polys.append(P(smooth([T(p) for p in tor], 5)))
        if s.dress == "dress":
            w0 = T((0.0, -0.585))
            hem_y = 0.30 - 0.14 * sit
            pts = [w0 + np.array([-0.07, 0.0]), w0 + np.array([0.068, 0.0]), w0 + np.array([0.13, hem_y * 0.6]),
                   w0 + np.array([0.17, hem_y]), w0 + np.array([0.06, hem_y + 0.012]), w0 + np.array([-0.05, hem_y + 0.004]),
                   w0 + np.array([-0.15, hem_y]), w0 + np.array([-0.11, hem_y * 0.6])]
            polys.append(P(smooth(pts, 5)))
            if "lace" in s.details:
                for i in range(8): holes.append(P(ellipse_pts(w0 + np.array([-0.125 + i * 0.037, hem_y - 0.025]), 0.0085, 0.0085, n=10)))
        if s.dress == "blazer":
            pts = [T((0.074, -0.60)), T((0.084, -0.50)), T((0.086, -0.40)), T((0.02, -0.39)), T((-0.08, -0.40)), T((-0.094, -0.50)), T((-0.07, -0.60))]
            polys.append(P(smooth(pts, 4)))
            holes.append(P(np.array([T((0.050, -0.79)), T((0.064, -0.776)), T((0.056, -0.70)), T((0.048, -0.702))])))     # a short lapel notch
        if s.dress == "cardigan":
            pts = [T((0.076, -0.62)), T((0.082, -0.52)), T((0.080, -0.44)), T((-0.08, -0.44)), T((-0.09, -0.52)), T((-0.07, -0.62))]
            polys.append(P(smooth(pts, 4)))
        if "buttons" in s.details:
            for i in range(4): holes.append(P(ellipse_pts(T((0.056 * b, -0.74 + i * 0.07)), 0.0075, 0.0075, n=10)))
        # ---------------- neck + head
        neck0 = T((0.004, -0.808)); ha = lean + pose.head + 0.42 * pose.slump
        head_c = neck0 + rot(np.array([0.010, -0.082]), ha)
        polys.append(P(limb([neck0 + np.array([0, 0.015]), head_c + rot(np.array([0.0, 0.04]), ha)], [0.026, 0.024], [0.028, 0.026])))
        if "turtleneck" in s.details:
            polys.append(P(limb([neck0 + np.array([0, 0.02]), neck0 + rot(np.array([0.004, -0.032]), ha)], [0.036, 0.034], [0.036, 0.034])))
        R = 0.071
        prof = PROFILE.copy()
        prof[NOSE, 0] = 0.92 + (prof[NOSE, 0] - 0.92) * s.nose
        prof[CHIN, 0] = 0.80 + (prof[CHIN, 0] - 0.80) * s.chin
        if pose.mouth > 0.05:     # the jaw drops a little
            prof[14:21, 1] += 0.10 * pose.mouth; prof[14:21, 0] -= 0.03 * pose.mouth
        def H(pts): return np.array([head_c + rot(np.asarray(p, float) * R, ha) for p in pts])
        polys.append(P(smooth(H(prof), 4)))
        if pose.mouth > 0.05:
            holes.append(P(H([(0.86, 0.43), (1.02, 0.42 + 0.03 * pose.mouth), (1.0, 0.47 + 0.12 * pose.mouth), (0.86, 0.47 + 0.06 * pose.mouth)])))
        hs = HAIR.get(s.hair)
        if s.hair == "curly":
            t = np.linspace(-2.2, 3.6, 70); r = 1.12 + 0.10 * np.abs(np.sin(t * 6.5))
            pts = [(r_ * math.cos(a) * 1.02 - 0.08, r_ * math.sin(a) - 0.06) for r_, a in zip(r, t)]
            pts = [p for p in pts if not (p[0] > 0.55 and p[1] > -0.55)]
            polys.append(P(H(pts)))
        elif hs is not None:
            polys.append(P(smooth(H(hs), 4)))
        if s.hair == "bun": polys.append(P(H(ellipse_pts((-0.88, -0.86), 0.42, 0.40, n=28))))
        holes.append(P(smooth(H([(0.36, -0.20), (0.50, -0.27), (0.66, -0.22), (0.68, -0.17), (0.52, -0.12), (0.38, -0.15)]), 3)))
        if "glasses" in s.details:
            polys.append(P(H(ellipse_pts((0.56, -0.18), 0.27, 0.21, n=24))))
            holes.append(P(H(ellipse_pts((0.56, -0.18), 0.19, 0.13, n=24))))
            polys.append(P(H(limb([(0.30, -0.20), (-0.42, -0.24)], [0.035, 0.035]))))
        if "headset" in s.details:   # the keynote microphone
            polys.append(P(H(limb([(-0.05, -0.02), (0.20, 0.38), (0.62, 0.56), (0.82, 0.52)], [0.045, 0.04, 0.035, 0.03]))))
            polys.append(P(H(ellipse_pts((0.87, 0.52), 0.10, 0.08, n=14))))
        if "clip" in s.details:      # the red hair clip: a little bow of red gel
            c = (-0.30, -1.00)
            for bb in (ellipse_pts((c[0] - 0.19, c[1]), 0.23, 0.14, ang=0.4, n=20), ellipse_pts((c[0] + 0.19, c[1]), 0.23, 0.14, ang=-0.4, n=20)):
                gels.append((P(H(bb)), (1.0, 0.10, 0.06)))
            gels.append((P(H(ellipse_pts(c, 0.075, 0.075, n=12))), (0.7, 0.04, 0.02)))
        # ---------------- arms
        def arm(sa, ea, back):
            s0 = T((-0.008 if back else 0.006, -0.775))
            e = s0 + rot(np.array([0.0, 0.158]), -sa - lean)
            w = e + rot(np.array([0.0, 0.150]), -sa - ea - lean)
            d = rot(np.array([0.0, 1.0]), -sa - ea - lean)
            hand_tip = w + d * 0.068
            J = [s0, (s0 + e) / 2, e, (e + w) / 2, w]
            Wf = [0.026 * b, 0.024 * b, 0.019 * b, 0.018 * b, 0.014 * b]
            out = [limb(J, Wf)]
            nrm = np.array([-d[1], d[0]])
            mitt = smooth([w - nrm * 0.016, w + d * 0.02 - nrm * 0.02, hand_tip - nrm * 0.008, hand_tip + nrm * 0.006,
                           w + d * 0.035 + nrm * 0.02, w + d * 0.022 + nrm * (0.03 + 0.012 * pose.hand_open), w + d * 0.008 + nrm * 0.016, w + nrm * 0.015], 3)
            out.append(mitt)
            return out, hand_tip, w
        pa, hb, wb = arm(pose.sh_b, pose.el_b, True)
        pf, hf, wf = arm(pose.sh_f, pose.el_f, False)
        polys = [P(p) for p in pa] + polys + [P(p) for p in pf]
        rods.append((P(wf), P(wf + np.array([0.04, 1.2]))))
        rods.append((P(wb), P(wb + np.array([-0.02, 1.2]))))
        anchors = dict(hand_f=P(hf), hand_b=P(hb), head=P(head_c), mouth=P(head_c + rot(np.array([1.0, 0.45]) * R, ha)),
                       top=P(head_c + rot(np.array([0, -1.3]) * R, ha)), hip=P(hip), wrist_f=P(wf))
        return polys, holes, gels, rods, anchors

def draw(mask, polys, holes, aa=True):
    lt = cv2.LINE_AA if aa else cv2.LINE_8
    for p in polys:
        cv2.fillPoly(mask, [np.round(np.asarray(p) * SC).astype(np.int32)], 255, lt, SH)
    for p in holes:
        cv2.fillPoly(mask, [np.round(np.asarray(p) * SC).astype(np.int32)], 0, lt, SH)

CAST = {
    "Ted": Puppet("Ted", 1.07, "short", 1.10, "blazer", nose=1.25, chin=1.15, details=("headset", "turtleneck")),
    "Me": Puppet("Me", 0.94, "bob", 0.92, "cardigan", nose=0.80, chin=0.9, details=("clip", "buttons")),
    "Dana": Puppet("Dana", 0.97, "pony", 0.95, "dress", nose=0.9, details=("lace",)),
    "Priya": Puppet("Priya", 0.95, "long", 0.93, None, nose=0.95),
    "Marcus": Puppet("Marcus", 1.04, "curly", 1.12, None, nose=1.05, chin=1.1),
    "Sam": Puppet("Sam", 0.99, "short", 1.0, None, nose=1.1, details=("glasses",)),
    "Lee": Puppet("Lee", 1.0, "short", 1.02, "blazer", nose=1.0),
    "Jo": Puppet("Jo", 0.96, "bun", 0.95, "dress", nose=0.9),
}
