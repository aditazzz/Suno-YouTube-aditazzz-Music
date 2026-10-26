"""Her: an anonymous woman in a camel trench coat, seated on the bench in profile (facing right), head bowed over her
phone. Built like vector cut-out animation: every part is a closed spline whose control points are authored for key
poses (bowed / looking up, phone up / phone in lap) and blended, so her moves stay on-model.

Coordinates: metres, u forward (right), v up, origin at the seat top under her hip (the bench seat is v = 0, the
ground v = -SEAT). draw() returns an RGBA sprite plus the pixel of the origin; silhouette() gives the shadow mask.
"""
import math
from dataclasses import dataclass
import numpy as np, cv2

F32 = np.float32
AA = cv2.LINE_AA
SEAT = 0.455


def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], F32)


COAT = hexc('c9a47a'); COAT_DK = hexc('8a6a4c')
LINING = hexc('6b4f3a')
PANTS = hexc('2e2f3c')
BOOT = hexc('231e22')
SKIN = hexc('e6bfa0')
HAIR = hexc('2a1c17'); HAIR_HI = hexc('5e4234')
PHONE = hexc('15151b')
INK = hexc('1d1620')
NOTE = hexc('2f4a5e')


@dataclass
class Pose:
    bow: float = 1.0        # 1 head bowed over the phone .. 0 head up, looking ahead
    phone: float = 1.0      # 1 phone held up .. 0 phone resting in her lap
    thumb: float = 0.0      # thumb travel 0..1 (scrolling)
    breathe: float = 0.0    # phase (radians)
    sway: float = 0.0       # hair sway phase
    screen: tuple = (0.78, 0.88, 1.0)
    screen_k: float = 1.0   # 0 = phone locked (dark)
    write: float = 0.0      # 0 holding the phone .. 1 writing in the notebook on her lap (phone set down)
    pen: float = 0.0        # pen travel phase
    face_us: float = 0.0    # (shadow only) the head turns to face the camera
    wave: float = 0.0       # (shadow only) a hand comes up and waves
    wave_ph: float = 0.0


def spline(pts, n=10, closed=True):
    P = np.asarray(pts, np.float64)
    if closed: P = np.vstack([P[-1:], P, P[:2]])
    else: P = np.vstack([P[:1], P, P[-1:]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            s = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    if not closed: out.append(P[-2])
    return np.array(out)


def rot(P, c, deg):
    P = np.asarray(P, np.float64); c = np.asarray(c, np.float64)
    a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
    d = P - c
    return c + np.stack([d[..., 0] * ca - d[..., 1] * sa, d[..., 0] * sa + d[..., 1] * ca], -1)


def A(*pts): return np.array(pts, np.float64)


def lerp(a, b, t):
    a = np.asarray(a, np.float64); b = np.asarray(b, np.float64)
    return a + (b - a) * t


# ------------------------------------------------------------------ key shapes (seat-relative metres)
HS = 0.93                                   # head scale (a touch small reads more elegant)
# head in its own upright frame: centre of skull at (0,0), facing right
HEAD = HS * A((0.0, 0.103), (0.058, 0.09), (0.086, 0.056), (0.094, 0.026), (0.091, 0.008), (0.1, -0.012), (0.117, -0.034),
              (0.105, -0.045), (0.105, -0.055), (0.104, -0.068), (0.097, -0.086), (0.094, -0.1), (0.072, -0.116),
              (0.03, -0.112), (0.0, -0.095), (-0.05, -0.085), (-0.088, -0.045), (-0.1, 0.01), (-0.08, 0.07), (-0.04, 0.098))
# hair cap over the skull (head frame): forehead hairline, crown, back, nape, then the hairline over the ear back to the temple
CAP = HS * A((0.079, 0.07), (0.05, 0.106), (0.0, 0.122), (-0.055, 0.112), (-0.1, 0.075), (-0.118, 0.015), (-0.108, -0.045),
             (-0.078, -0.095), (-0.04, -0.075), (-0.012, -0.03), (0.012, 0.0), (0.03, 0.03), (0.055, 0.045))
NECK_PIVOT = HS * np.array([-0.012, -0.09])
EYE = HS * np.array([0.062, 0.006])

TORSO_B = A((-0.135, 0.02), (-0.148, 0.11), (-0.142, 0.23), (-0.112, 0.36), (-0.058, 0.47), (0.012, 0.54), (0.07, 0.578),
            (0.092, 0.618), (0.158, 0.598), (0.184, 0.556), (0.196, 0.5), (0.2, 0.42), (0.18, 0.31), (0.13, 0.225),
            (0.1, 0.17), (0.02, 0.12), (-0.07, 0.02))
TORSO_U = A((-0.135, 0.02), (-0.146, 0.12), (-0.136, 0.25), (-0.114, 0.39), (-0.093, 0.515), (-0.052, 0.592), (0.0, 0.632),
            (0.01, 0.683), (0.08, 0.664), (0.102, 0.615), (0.124, 0.548), (0.14, 0.45), (0.134, 0.33), (0.112, 0.235),
            (0.098, 0.17), (0.02, 0.12), (-0.07, 0.02))
NECKBASE_B = np.array([0.122, 0.575]); NECKBASE_U = np.array([0.042, 0.65])
HEAD_C_B = np.array([0.222, 0.648]); HEAD_C_U = np.array([0.072, 0.784])
HEAD_ROT_B = -56.0; HEAD_ROT_U = -3.0

SKIRT = A((-0.15, 0.03), (-0.05, 0.13), (0.1, 0.162), (0.25, 0.165), (0.385, 0.152), (0.448, 0.118), (0.462, 0.06),
          (0.448, 0.0), (0.425, -0.04), (0.36, -0.028), (0.2, -0.012), (0.0, -0.008), (-0.12, -0.012), (-0.155, -0.004))
SHIN = A((0.378, 0.0), (0.44, 0.0), (0.448, -0.1), (0.452, -0.24), (0.448, -0.35), (0.405, -0.35), (0.396, -0.24),
         (0.374, -0.12))
BOOTP = A((0.402, -0.34), (0.452, -0.34), (0.462, -0.372), (0.548, -0.398), (0.615, -0.414), (0.627, -0.438), (0.618, -0.447),
          (0.43, -0.447), (0.428, -0.455), (0.404, -0.455), (0.398, -0.42))
SHIN2 = SHIN + np.array([0.035, 0.0]); BOOT2 = BOOTP + np.array([0.035, 0.0])

# sleeves: closed outlines (shoulder cap, upper arm, elbow, forearm, cuff) for the four arm key poses
ARM_B_UP = A((0.015, 0.47), (0.058, 0.532), (0.122, 0.508), (0.158, 0.41), (0.172, 0.312), (0.252, 0.334), (0.322, 0.366),
             (0.338, 0.324), (0.248, 0.276), (0.13, 0.226), (0.072, 0.31), (0.03, 0.4))
ARM_B_LAP = A((0.015, 0.47), (0.058, 0.532), (0.122, 0.508), (0.15, 0.4), (0.155, 0.272), (0.228, 0.226), (0.298, 0.214),
              (0.304, 0.17), (0.218, 0.17), (0.102, 0.198), (0.062, 0.31), (0.03, 0.4))
ARM_U_UP = A((-0.035, 0.53), (0.01, 0.594), (0.074, 0.57), (0.104, 0.47), (0.118, 0.362), (0.198, 0.354), (0.28, 0.386),
             (0.296, 0.342), (0.2, 0.3), (0.075, 0.28), (0.022, 0.37), (-0.02, 0.46))
ARM_U_LAP = A((-0.035, 0.53), (0.01, 0.594), (0.074, 0.57), (0.094, 0.46), (0.1, 0.33), (0.178, 0.236), (0.258, 0.221),
              (0.264, 0.176), (0.178, 0.176), (0.06, 0.23), (0.016, 0.36), (-0.02, 0.46))
ARM_WRITE = A((0.015, 0.47), (0.058, 0.532), (0.122, 0.508), (0.158, 0.41), (0.17, 0.3), (0.24, 0.255), (0.31, 0.25),
               (0.318, 0.205), (0.235, 0.205), (0.122, 0.205), (0.07, 0.31), (0.03, 0.4))
PH_B_UP = (np.array([0.392, 0.385]), 24.0); PH_B_LAP = (np.array([0.352, 0.21]), 4.0)
PH_U_UP = (np.array([0.35, 0.405]), 30.0); PH_U_LAP = (np.array([0.31, 0.215]), 4.0)

# long hair, hanging under gravity (seat-relative; same point counts so the two head poses blend)
HANG_F_B = A((0.352, 0.708), (0.392, 0.69), (0.416, 0.63), (0.42, 0.55), (0.414, 0.48), (0.402, 0.432), (0.386, 0.452),
             (0.37, 0.5), (0.36, 0.56), (0.344, 0.63))
HANG_F_U = A((0.082, 0.872), (0.112, 0.846), (0.124, 0.78), (0.122, 0.71), (0.116, 0.645), (0.105, 0.6), (0.094, 0.625),
             (0.088, 0.68), (0.086, 0.74), (0.078, 0.8))
HANG_B_B = A((0.262, 0.715), (0.2, 0.69), (0.142, 0.645), (0.092, 0.598), (0.052, 0.548), (0.024, 0.5), (0.004, 0.462),
             (0.042, 0.47), (0.092, 0.518), (0.148, 0.57), (0.204, 0.605), (0.24, 0.645))
HANG_B_U = A((0.03, 0.885), (-0.045, 0.86), (-0.09, 0.79), (-0.118, 0.69), (-0.14, 0.58), (-0.158, 0.48), (-0.162, 0.395),
             (-0.118, 0.415), (-0.082, 0.52), (-0.05, 0.63), (-0.02, 0.73), (0.012, 0.8))


def head_poly(bow):
    c = lerp(HEAD_C_U, HEAD_C_B, bow)
    r = float(lerp(HEAD_ROT_U, HEAD_ROT_B, bow))
    return rot(HEAD + c, c + NECK_PIVOT, r), c, r


def parts(p: Pose):
    b = float(np.clip(p.bow, 0, 1)); ph = float(np.clip(p.phone, 0, 1))
    br = 0.004 * math.sin(p.breathe)
    torso = lerp(TORSO_U, TORSO_B, b)
    torso = torso + np.array([0, br]) * (torso[:, 1:2] > 0.3)
    head, hc, hr = head_poly(b)
    head = head + np.array([0, br])
    cap = rot(CAP + hc, hc + NECK_PIVOT, hr) + np.array([0, br])
    nb = lerp(NECKBASE_U, NECKBASE_B, b)
    pivot = hc + rot(NECK_PIVOT[None], (0, 0), hr)[0]
    d = pivot - nb; d = d / (np.linalg.norm(d) + 1e-9); nr = np.array([-d[1], d[0]])
    neck = np.array([nb - nr * 0.045 - d * 0.03, nb + nr * 0.04 - d * 0.03, pivot + nr * 0.036 + d * 0.01, pivot - nr * 0.034 + d * 0.02])
    arm = lerp(lerp(ARM_U_LAP, ARM_U_UP, ph), lerp(ARM_B_LAP, ARM_B_UP, ph), b) + np.array([0, br * 0.6])
    wr = float(np.clip(p.write, 0, 1))
    if wr > 0:
        aw = ARM_WRITE + np.array([0.012 * math.sin(p.pen * 7.0), 0.004 * math.sin(p.pen * 13.0)]) * (ARM_WRITE[:, 0:1] > 0.2)
        arm = lerp(arm, aw, wr)
    pc = lerp(lerp(PH_U_LAP[0], PH_U_UP[0], ph), lerp(PH_B_LAP[0], PH_B_UP[0], ph), b)
    pa = float(lerp(lerp(PH_U_LAP[1], PH_U_UP[1], ph), lerp(PH_B_LAP[1], PH_B_UP[1], ph), b))
    sw = 0.006 * math.sin(p.sway)
    hf = lerp(HANG_F_U, HANG_F_B, b); hf[2:6, 0] += sw * 0.8
    hb = lerp(HANG_B_U, HANG_B_B, b); hb[3:8, 0] += sw
    return dict(torso=torso, head=head, cap=cap, neck=neck, arm=arm, pc=pc, pa=pa, hb=hb, hf=hf, hc=hc, hr=hr, b=b, ph=ph, wr=wr)


def notebook_lap(q, pen):
    """Open notebook on her lap (two pages seen edge-on-ish) + the pen in her near hand."""
    c = np.array([0.33, 0.185])
    book = A(c + (-0.13, 0.0), c + (0.12, -0.012), c + (0.125, 0.012), c + (-0.125, 0.026))
    spine = A(c + (-0.005, 0.008), c + (0.0, 0.03))
    tip = c + np.array([0.02 + 0.03 * math.sin(pen * 7.0), 0.03 + 0.004 * math.sin(pen * 13.0)])
    pen_l = A(tip, tip + (-0.05, 0.11))
    return book, spine, pen_l


def tube(c, widths, n=8):
    P = spline(c, n, closed=False)
    w = np.interp(np.linspace(0, 1, len(P)), np.linspace(0, 1, len(widths)), widths)
    L, R = [], []
    for i in range(len(P)):
        d = P[min(len(P) - 1, i + 1)] - P[max(0, i - 1)]; d = d / (np.linalg.norm(d) + 1e-9)
        nr = np.array([-d[1], d[0]])
        L.append(P[i] + nr * w[i] / 2); R.append(P[i] - nr * w[i] / 2)
    return np.array(L + R[::-1])


def phone_quad(pc, pa, hw=0.074, hh=0.0055):
    ax = np.array([math.cos(math.radians(pa)), math.sin(math.radians(pa))]); ay = np.array([-ax[1], ax[0]])
    return np.array([pc - ax * hw - ay * hh, pc + ax * hw - ay * hh, pc + ax * hw + ay * hh, pc - ax * hw + ay * hh]), ax, ay


def hand_shapes(pc, ax, ay, thumb):
    """Near hand cradling the phone from below, thumb on the screen; far-hand fingertips at the far end."""
    def P(a, b): return pc + ax * a + ay * b
    palm = A(P(-0.088, -0.012), P(-0.062, -0.032), P(-0.02, -0.04), P(0.018, -0.034), P(0.04, -0.02), P(0.046, -0.006),
             P(0.03, -0.003), P(-0.03, -0.004), P(-0.07, 0.004))
    t = -0.01 + 0.032 * thumb
    thumbp = A(P(-0.052, 0.0), P(-0.03, 0.012), P(t - 0.004, 0.0165), P(t + 0.01, 0.0135), P(t + 0.012, 0.008), P(t - 0.004, 0.0065),
               P(-0.034, 0.002))
    far = A(P(0.05, -0.012), P(0.068, 0.006), P(0.082, 0.012), P(0.088, 0.004), P(0.08, -0.012), P(0.064, -0.02))
    return palm, thumbp, far


# ------------------------------------------------------------------ rendering
class Canvas:
    def __init__(self, ppm, w=1.15, h=1.5, ox_m=0.32, oy_m=0.5):
        self.ppm = ppm
        self.W = int(w * ppm) + 4; self.H = int(h * ppm) + 4
        self.ox = ox_m * ppm + 2; self.oy = self.H - oy_m * ppm - 2
        self.rgb = np.zeros((self.H, self.W, 3), F32); self.a = np.zeros((self.H, self.W), F32)

    def px(self, P):
        P = np.asarray(P, np.float64)
        return np.stack([self.ox + P[..., 0] * self.ppm, self.oy - P[..., 1] * self.ppm], -1)

    def mask(self, poly):
        m = np.zeros((self.H, self.W), np.uint8)
        cv2.fillPoly(m, [np.round(self.px(poly) * 16).astype(np.int32)], 255, AA, shift=4)
        return m.astype(F32) / 255

    def put(self, m, col):
        # same maths as a full-canvas blend, but only over the mask's bounding box (everything outside is untouched)
        rows = np.flatnonzero(m.any(1))
        if len(rows) == 0: return
        y0, y1 = rows[0], rows[-1] + 1
        cols = np.flatnonzero(m[y0:y1].any(0)); x0, x1 = cols[0], cols[-1] + 1
        mm = m[y0:y1, x0:x1]; m3 = mm[..., None]
        self.rgb[y0:y1, x0:x1] = self.rgb[y0:y1, x0:x1] * (1 - m3) + np.asarray(col, F32) * m3
        self.a[y0:y1, x0:x1] = np.maximum(self.a[y0:y1, x0:x1], mm)

    def line(self, poly, w, closed=True, col=INK, alpha=1.0):
        pts = np.round(self.px(poly) * 16).astype(np.int32)
        th = max(1, int(round(w))); pad = th + 3
        x0 = max(0, int(pts[:, 0].min()) // 16 - pad); x1 = min(self.W, int(pts[:, 0].max()) // 16 + pad + 1)
        y0 = max(0, int(pts[:, 1].min()) // 16 - pad); y1 = min(self.H, int(pts[:, 1].max()) // 16 + pad + 1)
        if x1 <= x0 or y1 <= y0: return
        lay = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.polylines(lay, [pts - np.array([x0 * 16, y0 * 16], np.int32)], closed, 255, th, AA, shift=4)
        m = lay.astype(F32) / 255 * alpha
        self.rgb[y0:y1, x0:x1] = self.rgb[y0:y1, x0:x1] * (1 - m[..., None]) + np.asarray(col, F32) * m[..., None]
        self.a[y0:y1, x0:x1] = np.maximum(self.a[y0:y1, x0:x1], m)


def _shift(m, dx, dy):
    dx, dy = int(round(dx)), int(round(dy))
    out = np.zeros_like(m)
    H, W = m.shape
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = m[ys, xs]
    return out


def draw(p: Pose, ppm, light=None, notebook=None, win=None):
    """light: key (rgb, the sunlit colour multiplier), amb (rgb, shade multiplier), dir (2D toward the key light in her
    plane: +u right, +v up), rim (rgb) and rimdir, phone (glow strength). Returns rgba, origin px, info."""
    L = dict(dir=(-0.4, 0.9), key=np.array([1.0, 0.97, 0.92], F32), amb=np.array([0.58, 0.6, 0.72], F32),
             rim=np.array([1.0, 0.8, 0.55], F32), rimdir=(-1.0, 0.2), rimk=0.0, phone=1.0)
    if light: L.update({k: v for k, v in light.items() if v is not None})
    ld = np.array(L['dir'], np.float64); ld /= (np.linalg.norm(ld) + 1e-9)
    key = np.asarray(L['key'], F32); amb = np.asarray(L['amb'], F32)
    C = Canvas(ppm, *win) if win else Canvas(ppm)   # win = (w, h, ox_m, oy_m): only the part the camera sees
    q = parts(p)
    lw = max(1.0, ppm * 0.0036)
    band = ppm * 0.028

    def part(poly, base, bandk=1.0, outline=True, w=None, smooth=10):
        sp = spline(poly, smooth) if smooth else poly
        m = C.mask(sp)
        C.put(m, base * key)
        if bandk > 0:
            s = np.clip(m - _shift(m, ld[0] * band * bandk, -ld[1] * band * bandk), 0, 1)
            C.put(s, base * amb)
        if outline: C.line(sp, w or lw)
        return m

    part(SHIN2, PANTS * 0.78, 1.4)
    part(BOOT2, BOOT * 0.85, 0.8)
    part(SHIN, PANTS, 1.2)
    part(BOOTP, BOOT, 0.8)
    C.line(spline(A((0.41, -0.428), (0.52, -0.43), (0.61, -0.436)), 6, closed=False), lw * 0.7, closed=False, col=hexc('4a4046'))
    if notebook is not None:
        notebook(C, part)
    # far arm, a little behind and darker
    part(q['arm'] + np.array([0.03, 0.012]), COAT * 0.8, 1.0)
    part(q['neck'], SKIN * 0.8, 0.0)
    part(q['torso'], COAT, 1.5)
    t = q['torso']
    C.line(spline(A(t[7], (t[7][0] + 0.03, t[7][1] - 0.05), (t[9][0] - 0.03, t[9][1] - 0.06)), 6, closed=False), lw * 0.8, closed=False)
    bw_ = 1 - q['b']
    bl = A(lerp((-0.148, 0.205), (-0.142, 0.215), bw_), lerp((0.19, 0.235), (0.14, 0.245), bw_))
    belt = np.array([bl[0] + (0, 0.02), bl[1] + (0, 0.02), bl[1] + (0, -0.017), bl[0] + (0, -0.017)])
    C.put(C.mask(belt) * C.mask(spline(q['torso'], 10)), COAT_DK * key * 0.9)
    C.line(belt, lw * 0.7)
    part(SKIRT, COAT, 1.3)
    C.line(spline(A((0.06, 0.148), (0.22, 0.1), (0.4, 0.07)), 6, closed=False), lw * 0.6, closed=False, alpha=0.55)
    C.line(spline(A((0.458, 0.04), (0.41, 0.022), (0.34, -0.004)), 6, closed=False), lw * 0.6, closed=False, alpha=0.55)
    # head, then the hair over the nape and collar, the cap, the front curtain
    part(q['head'], SKIN, 0.8, w=lw * 0.75)
    e = rot((q['hc'] + EYE)[None], q['hc'] + NECK_PIVOT, q['hr'])[0]
    ed = rot(np.array([[-0.004, 0.002], [0.008, -0.003], [0.02, -0.004]]), (0, 0), q['hr'])
    C.line(spline(np.array([e + ed[0], e + ed[1], e + ed[2]]), 4, closed=False), lw * 0.9, closed=False)
    # the mouth: a short line between the lips
    mo = rot((q['hc'] + HS * np.array([0.104, -0.061]))[None], q['hc'] + NECK_PIVOT, q['hr'])[0]
    md = rot(np.array([[0.0, 0.0], [-0.012, 0.001]]), (0, 0), q['hr'])
    C.line(np.array([mo + md[0], mo + md[1]]), max(1.0, lw * 0.5), closed=False, alpha=0.6)
    # the hair throws a soft shadow across her cheek (drawn before the hair itself)
    hm = np.maximum(C.mask(spline(q['hf'], 10)), C.mask(spline(q['cap'], 10)))
    face_m = C.mask(spline(q['head'], 10))
    cast = np.clip(_shift(hm, ppm * 0.014, ppm * 0.012) - hm, 0, 1) * face_m
    cast = cv2.GaussianBlur(cast, (0, 0), max(0.6, ppm * 0.003))
    C.rgb = C.rgb * (1 - cast[..., None] * 0.45) + (SKIN * amb * 0.8)[None, None] * cast[..., None] * 0.45
    part(q['hb'], HAIR, 0.6)
    part(q['cap'], HAIR, 0.5)
    part(q['hf'], HAIR, 0.5)
    hf = q['hf']
    for i0, i1 in ((0, 4), (1, 5), (9, 7)):
        s0, s1 = hf[i0], hf[i1]
        C.line(spline(A(s0, (s0 + s1) / 2 + (0.006, 0.0), s1), 6, closed=False), lw * 0.6, closed=False, col=HAIR_HI, alpha=0.75)
    cp = q['cap']
    C.line(spline(A(cp[1], cp[3], cp[5]), 6, closed=False), lw * 0.6, closed=False, col=HAIR_HI, alpha=0.7)
    hb = q['hb']
    C.line(spline(A(hb[1], hb[3], hb[5]), 6, closed=False), lw * 0.6, closed=False, col=HAIR_HI, alpha=0.6)
    if q['wr'] > 0.5:
        book, spine, pen_l = notebook_lap(q, p.pen)
        C.put(C.mask(book), hexc('f3eee2') * key); C.line(book, lw)
        C.line(spine, lw * 0.8, closed=False)
        part(q['arm'], COAT, 1.1)
        cuff = q['arm'][6]
        hand = A(cuff + (-0.005, 0.0), cuff + (0.05, 0.012), cuff + (0.075, -0.012), cuff + (0.05, -0.04), cuff + (0.0, -0.03))
        part(hand, SKIN, 0.5)
        C.line(pen_l, max(1.0, lw * 1.4), closed=False, col=hexc('1b1b22'))
        rgba = np.concatenate([C.rgb, C.a[..., None]], -1)
        return rgba, C.ox, C.oy, q
    # phone, sleeve, hands
    quad, ax, ay = phone_quad(q['pc'], q['pa'])
    palm, thumb, far = hand_shapes(q['pc'], ax, ay, p.thumb)
    part(far, SKIN * 0.86, 0.0)
    part(quad, PHONE, 0.0, smooth=0)
    scr = np.asarray(p.screen, F32) * p.screen_k
    if p.screen_k > 0.01:
        C.line(np.array([quad[3] + ax * 0.005, quad[2] - ax * 0.005]), max(1.0, lw * 1.0), closed=False,
               col=np.clip(scr * 0.85 + 0.15, 0, 1))
    part(q['arm'], COAT, 1.1)
    ar = q['arm']
    C.line(spline(A(ar[4] + (-0.005, 0.03), ar[4] + (0.02, 0.0), ar[4] + (0.01, -0.03)), 6, closed=False), lw * 0.7, closed=False)
    cuff = np.array([ar[6] * 0.82 + ar[7] * 0.18, ar[7] * 0.82 + ar[6] * 0.18])
    d = ar[6] - ar[5]; d = d / np.linalg.norm(d)
    C.line(np.array([cuff[0] - d * 0.03, cuff[1] - d * 0.03]), lw * 0.8, closed=False)
    part(palm, SKIN, 0.6)
    part(thumb, SKIN, 0.0)
    # screen light on the face and hands
    if p.screen_k > 0.01 and L['phone'] > 0:
        src = q['pc'] + ay * 0.03
        yy, xx = np.mgrid[0:C.H, 0:C.W].astype(F32)
        c = C.px(src)
        dd = np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2) / ppm
        g = np.exp(-(dd / 0.11) ** 2) * 0.32 + np.exp(-(dd / 0.28) ** 2) * 0.14
        k_ = (g * C.a * p.screen_k * L['phone'])[..., None]
        C.rgb = C.rgb * (1 - k_ * 0.25) + k_ * scr * (C.rgb * 0.75 + 0.05)
    if L['rimk'] > 0:
        rd = np.array(L['rimdir'], np.float64); rd /= np.linalg.norm(rd)
        rim = np.clip(C.a - _shift(C.a, rd[0] * ppm * 0.01, -rd[1] * ppm * 0.01), 0, 1)
        C.rgb = C.rgb + rim[..., None] * np.asarray(L['rim'], F32) * L['rimk']
    rgba = np.concatenate([C.rgb, C.a[..., None]], -1)
    return rgba, C.ox, C.oy, q


FRONT_HEAD = A((0.0, 0.125), (0.058, 0.112), (0.092, 0.07), (0.1, 0.0), (0.085, -0.07), (0.05, -0.115), (0.0, -0.128),
               (-0.05, -0.115), (-0.085, -0.07), (-0.1, 0.0), (-0.092, 0.07), (-0.058, 0.112))
FRONT_HAIR = A((0.0, 0.142), (0.075, 0.125), (0.118, 0.06), (0.128, -0.05), (0.135, -0.2), (0.14, -0.3), (0.09, -0.3),
               (0.0, -0.22), (-0.09, -0.3), (-0.14, -0.3), (-0.135, -0.2), (-0.128, -0.05), (-0.118, 0.06), (-0.075, 0.125))


def silhouette(p: Pose, ppm, extra=()):
    """Her silhouette as a float mask (same canvas layout as draw). The shadow can do what she doesn't: turn its
    head to face us (face_us) or lift a hand and wave."""
    C = Canvas(ppm)
    q = parts(p)
    m = np.zeros((C.H, C.W), F32)
    body = [SHIN2, BOOT2, SHIN, BOOTP, q['arm'] + np.array([0.03, 0.012]), q['torso'], SKIRT]
    for poly in body:
        m = np.maximum(m, C.mask(spline(poly, 10)))
    m = np.maximum(m, C.mask(q['neck']))
    fu = float(np.clip(p.face_us, 0, 1))
    if fu < 0.999:
        prof = np.zeros_like(m)
        for poly in (q['hb'], q['head'], q['cap'], q['hf']):
            prof = np.maximum(prof, C.mask(spline(poly, 10)))
        m = np.maximum(m, prof * (1 - fu))
    if fu > 0.001:
        hc = q['hc'] + np.array([0.0, 0.02])
        fr = np.maximum(C.mask(spline(FRONT_HAIR + hc, 8)), C.mask(spline(FRONT_HEAD + hc, 8)))
        m = np.maximum(m, fr * fu)
    if q['wr'] > 0.5:
        book, spine, pen_l = notebook_lap(q, p.pen)
        m = np.maximum(m, C.mask(book))
        m = np.maximum(m, C.mask(spline(q['arm'], 10)))
    else:
        quad, ax, ay = phone_quad(q['pc'], q['pa'])
        palm, thumb, far = hand_shapes(q['pc'], ax, ay, p.thumb)
        for poly in (far, q['arm'], palm, thumb):
            m = np.maximum(m, C.mask(spline(poly, 10)))
        m = np.maximum(m, C.mask(quad))
    if p.wave > 0.001:
        sho = lerp(np.array([0.02, 0.555]), np.array([0.07, 0.495]), q['b'])
        ang = math.radians(88 + 20 * math.sin(p.wave_ph))
        elbow = sho + np.array([math.cos(math.radians(14)), math.sin(math.radians(14))]) * 0.3 * p.wave
        hand = elbow + np.array([math.cos(ang), math.sin(ang)]) * 0.25 * p.wave
        arm = tube(np.array([sho, (sho + elbow) / 2, elbow, (elbow + hand) / 2, hand]), [0.1, 0.09, 0.085, 0.072, 0.064])
        m = np.maximum(m, C.mask(arm))
        for k in range(5):
            fa = ang + math.radians(-48 + k * 22)
            f0 = hand + np.array([math.cos(ang), math.sin(ang)]) * 0.03
            f1 = f0 + np.array([math.cos(fa), math.sin(fa)]) * (0.085 if k not in (0, 4) else 0.06) * p.wave
            m = np.maximum(m, C.mask(tube(np.array([f0, (f0 + f1) / 2, f1]), [0.03, 0.026, 0.02], 3)))
        m = np.maximum(m, C.mask(spline(A(hand + (-0.05, -0.035), hand + (0.05, -0.035), hand + (0.055, 0.04), hand + (-0.05, 0.045)), 6)))
    for poly in extra:
        m = np.maximum(m, C.mask(poly))
    return m, C.ox, C.oy, C
