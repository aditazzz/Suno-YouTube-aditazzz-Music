"""Her: an elegant silhouette with a mass of backlit curls. Never a face in detail, never lip-sync.

The figure is drawn in 2-D screen space (she is always small, far, backlit or seen from behind) from hand-placed
outline curves in a unit frame (y down, 1 unit = one head height, origin at the crown), then filled dark.
Her hair is a lobed mass whose edge is broken into hundreds of small curls (overlapping discs), with a band of
translucency where light shines through and a few flyaway strands. Edges that face the light catch a rim.

draw(img, pose, cx, cy, h, light_dir, rim, ...)
    pose       'profile' (head + shoulders in profile, facing screen-right; mirror=True faces left),
               'lean' (the cover pose: leaning on a railing, chin on her hand, profile right),
               'stand_back' (full figure from behind, long coat), 'sit_back' (on the edge of the bed, from behind),
               'stand_profile' (full figure in profile at a window, facing right)
    cx, cy     screen position of the crown of her head; h = head height in px
    light_dir  2-D vector pointing FROM her TOWARD the light, screen coords (y down)
Returns her alpha mask (H, W).
"""
import math
from functools import lru_cache
import numpy as np, cv2
import ys_eng as E
from ys_eng import F32, hexc, sample, fbm_tex

def _spline(pts, n=16, closed=True):
    """Catmull-Rom through control points -> dense polyline."""
    P = np.asarray(pts, F32)
    if closed: P = np.vstack([P[-1:], P, P[:2]])
    else: P = np.vstack([P[:1], P, P[-1:]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed: out.append(P[-2])
    return np.array(out, F32)

# ---------------------------------------------------------------- outlines (unit = head height, origin at the crown, y down)
# head + neck + shoulders in profile, facing right
PROFILE = [(0.02, 0.0), (0.22, 0.05), (0.33, 0.16), (0.38, 0.30), (0.395, 0.38), (0.385, 0.425), (0.43, 0.50),
           (0.475, 0.565), (0.455, 0.59), (0.425, 0.605), (0.44, 0.645), (0.425, 0.675), (0.435, 0.715),
           (0.415, 0.75), (0.40, 0.775), (0.41, 0.82), (0.37, 0.87), (0.27, 0.90), (0.20, 0.93), (0.17, 1.02),
           (0.18, 1.20), (0.26, 1.34), (0.42, 1.46), (0.58, 1.62), (0.66, 1.95), (0.70, 2.6), (-0.95, 2.6),
           (-0.95, 1.95), (-0.86, 1.62), (-0.62, 1.44), (-0.34, 1.30), (-0.22, 1.12), (-0.22, 0.95), (-0.34, 0.78),
           (-0.42, 0.55), (-0.40, 0.28), (-0.28, 0.08)]
PROFILE_HAIR = [(0.10, -0.10), (0.30, -0.02), (0.40, 0.12), (0.38, 0.24), (0.27, 0.22), (0.16, 0.30), (0.08, 0.50),
                (0.02, 0.78), (-0.04, 1.06), (-0.10, 1.34), (-0.26, 1.58), (-0.56, 1.68), (-0.82, 1.50), (-0.86, 1.10),
                (-0.74, 0.70), (-0.62, 0.34), (-0.46, 0.06), (-0.20, -0.10)]
# leaning on a railing (cover): profile right, forearm up, hand under the chin; the railing cuts her at the chest
LEAN = [(0.02, 0.0), (0.22, 0.05), (0.33, 0.16), (0.38, 0.30), (0.395, 0.38), (0.385, 0.425), (0.43, 0.50),
        (0.475, 0.565), (0.455, 0.59), (0.425, 0.605), (0.44, 0.645), (0.425, 0.675), (0.435, 0.715),
        (0.415, 0.75), (0.40, 0.775), (0.41, 0.82), (0.39, 0.86), (0.47, 0.90), (0.52, 1.02), (0.50, 1.25),
        (0.56, 1.60), (0.66, 1.95), (0.70, 2.10), (0.52, 2.18), (0.32, 2.02), (0.30, 1.70), (0.24, 1.30),
        (0.18, 1.08), (0.16, 1.22), (0.30, 1.52), (0.50, 1.95), (0.95, 2.30), (1.30, 2.45), (1.30, 2.9),
        (-1.10, 2.9), (-1.05, 2.1), (-0.80, 1.55), (-0.55, 1.36), (-0.30, 1.22), (-0.22, 0.98), (-0.34, 0.78),
        (-0.42, 0.55), (-0.40, 0.28), (-0.28, 0.08)]
# full figure from behind in a long coat (about 7.6 heads)
STAND_BACK = [(-0.17, 0.92), (-0.20, 1.06), (-0.52, 1.22), (-0.86, 1.36), (-0.97, 1.55), (-1.00, 2.10),
              (-0.98, 2.90), (-0.92, 3.70), (-0.86, 3.86), (-0.80, 3.72), (-0.66, 2.95), (-0.72, 3.40),
              (-0.86, 4.40), (-0.96, 5.55), (-0.84, 5.62), (-0.40, 5.66), (-0.36, 6.40), (-0.34, 7.30),
              (-0.40, 7.50), (-0.14, 7.50), (-0.12, 7.30), (-0.08, 6.40), (-0.06, 5.66), (0.06, 5.66),
              (0.08, 6.40), (0.12, 7.30), (0.14, 7.50), (0.40, 7.50), (0.34, 7.30), (0.36, 6.40), (0.40, 5.66),
              (0.84, 5.62), (0.96, 5.55), (0.86, 4.40), (0.72, 3.40), (0.66, 2.95), (0.80, 3.72), (0.86, 3.86),
              (0.92, 3.70), (0.98, 2.90), (1.00, 2.10), (0.97, 1.55), (0.86, 1.36), (0.52, 1.22), (0.20, 1.06),
              (0.17, 0.92)]
BACK_HAIR = [(0.0, -0.10), (0.36, -0.03), (0.54, 0.22), (0.60, 0.62), (0.66, 1.05), (0.70, 1.42), (0.52, 1.72),
             (0.22, 1.84), (-0.06, 1.86), (-0.36, 1.80), (-0.62, 1.62), (-0.72, 1.30), (-0.64, 0.92), (-0.58, 0.52),
             (-0.52, 0.18), (-0.34, -0.04)]
HEAD_BACK = [(0.0, 0.0), (0.30, 0.08), (0.38, 0.38), (0.33, 0.70), (0.18, 0.95), (-0.18, 0.95), (-0.33, 0.70),
             (-0.38, 0.38), (-0.30, 0.08)]
# sitting on the edge of the bed, seen from behind, turned a little to her right (toward the window)
SIT_BACK = [(-0.17, 0.92), (-0.20, 1.06), (-0.50, 1.24), (-0.84, 1.42), (-0.95, 1.62), (-0.93, 2.10),
            (-0.80, 2.55), (-0.72, 2.80), (-0.86, 3.20), (-1.10, 3.45), (-1.20, 3.70), (1.25, 3.70), (1.12, 3.42),
            (0.88, 3.18), (0.72, 2.80), (0.78, 2.50), (0.92, 2.05), (0.96, 1.58), (0.86, 1.36), (0.52, 1.20),
            (0.20, 1.06), (0.17, 0.92)]
# standing in profile at the window, facing right, a hand at the window frame
STAND_PROFILE = [(0.02, 0.0), (0.22, 0.05), (0.33, 0.16), (0.38, 0.30), (0.395, 0.38), (0.385, 0.425), (0.43, 0.50),
                 (0.475, 0.565), (0.455, 0.59), (0.425, 0.605), (0.44, 0.645), (0.425, 0.675), (0.435, 0.715),
                 (0.415, 0.75), (0.40, 0.775), (0.41, 0.82), (0.37, 0.87), (0.27, 0.90), (0.20, 0.95), (0.20, 1.20),
                 (0.36, 1.45), (0.46, 1.85), (0.42, 2.30), (0.30, 2.80), (0.36, 3.30), (0.50, 3.95), (0.52, 4.60),
                 (0.42, 5.40), (0.34, 6.40), (0.36, 7.20), (0.52, 7.40), (0.10, 7.45), (0.00, 7.20), (-0.04, 6.40),
                 (-0.22, 5.40), (-0.36, 4.60), (-0.44, 3.95), (-0.40, 3.30), (-0.30, 2.80), (-0.30, 2.30),
                 (-0.36, 1.85), (-0.40, 1.45), (-0.24, 1.12), (-0.22, 0.95), (-0.34, 0.78), (-0.42, 0.55),
                 (-0.40, 0.28), (-0.28, 0.08)]
POSES = {
    'profile': (PROFILE, PROFILE_HAIR, None, 2.6),
    'lean': (LEAN, PROFILE_HAIR, None, 2.9),
    'stand_back': (STAND_BACK, BACK_HAIR, HEAD_BACK, 7.6),
    'sit_back': (SIT_BACK, BACK_HAIR, HEAD_BACK, 3.7),
    'stand_profile': (STAND_PROFILE, PROFILE_HAIR, None, 7.5),
}

@lru_cache(32)
def _curls(pose, seed, n):
    """small discs scattered along the hair outline (unit coords): (x, y, r, outward normal x, y)."""
    r = np.random.default_rng(seed)
    poly = _spline(POSES[pose][1], 30)
    seg = np.diff(np.vstack([poly, poly[:1]]), axis=0); L = np.r_[0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
    res = []
    for k in range(n):
        s = r.uniform(0, L[-1]); i = max(0, min(int(np.searchsorted(L, s)) - 1, len(poly) - 1))
        p = poly[i]; q = poly[(i + 1) % len(poly)]
        tg = (q - p) / max(1e-6, np.linalg.norm(q - p)); nr = np.array([tg[1], -tg[0]], F32)   # outward (clockwise poly)
        rad = r.uniform(0.022, 0.065) * (1.2 if r.random() < 0.2 else 1.0)
        off = r.uniform(-0.05, 0.035)
        c = p + nr * off
        res.append((c[0], c[1], rad, nr[0], nr[1]))
    return np.array(res, F32)

@lru_cache(8)
def _curls_fine(pose, seed, n):
    """(large renders only) a second, finer layer of curls along the hair edge, so a big close-up reads as hair and
    not as a scalloped outline."""
    r = np.random.default_rng(seed + 77)
    poly = _spline(POSES[pose][1], 40)
    seg = np.diff(np.vstack([poly, poly[:1]]), axis=0); L = np.r_[0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
    res = []
    for k in range(n):
        s = r.uniform(0, L[-1]); i = max(0, min(int(np.searchsorted(L, s)) - 1, len(poly) - 1))
        p = poly[i]; q = poly[(i + 1) % len(poly)]
        tg = (q - p) / max(1e-6, np.linalg.norm(q - p)); nr = np.array([tg[1], -tg[0]], F32)
        rad = r.uniform(0.007, 0.022)
        c = p + nr * r.uniform(0.005, 0.075) + tg * r.uniform(-0.01, 0.01)
        res.append((c[0], c[1], rad))
    return np.array(res, F32)

@lru_cache(32)
def _flyaways(pose, seed, n):
    r = np.random.default_rng(seed + 1)
    poly = _spline(POSES[pose][1], 30)
    seg = np.diff(np.vstack([poly, poly[:1]]), axis=0); L = np.r_[0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
    out = []
    for k in range(n):
        s = r.uniform(0, L[-1]); i = max(0, min(int(np.searchsorted(L, s)) - 1, len(poly) - 1))
        p = poly[i]; q = poly[(i + 1) % len(poly)]
        tg = (q - p) / max(1e-6, np.linalg.norm(q - p)); nr = np.array([tg[1], -tg[0]], F32)
        out.append((p, tg, nr, r.uniform(0.05, 0.14), r.uniform(-1, 1), r.uniform(0, 6.28)))
    return out

def _px(P, cx, cy, h, mirror, rot):
    P = np.asarray(P, F32).copy()
    if mirror: P[..., 0] = -P[..., 0]
    if rot:
        c, s = math.cos(rot), math.sin(rot); x = P[..., 0] * c - P[..., 1] * s; y = P[..., 0] * s + P[..., 1] * c; P = np.stack([x, y], -1)
    return np.stack([cx + P[..., 0] * h, cy + P[..., 1] * h], -1)

def draw(img, pose, cx, cy, h, light_dir=(1.0, -0.2), rim=None, rim_amt=1.0, body=None, t=0.0, mirror=False, wind=0.4,
         emis=None, op=1.0, seed=7, rot=0.0, clip=None, dep=None, depth=None, glow=1.0, hair_light=None, backlit=0.0, fine=0):
    """draw her into img (linear float); returns her alpha mask."""
    H, W = img.shape[:2]
    rim = hexc('ffd2a0') if rim is None else np.asarray(rim, F32)
    body = hexc('050607') if body is None else np.asarray(body, F32)
    outline, hair, head, ext = POSES[pose]
    x0 = int(max(0, cx - h * 1.6)); x1 = int(min(W, cx + h * 1.6)); y0 = int(max(0, cy - h * 0.35)); y1 = int(min(H, cy + h * (ext + 0.1)))
    if x1 <= x0 or y1 <= y0: return None
    w_, h_ = x1 - x0, y1 - y0
    S8 = 8.0
    def fill(m, pts, val=1.0):
        q = np.round((pts - [x0, y0]) * S8).astype(np.int32)
        cv2.fillPoly(m, [q], val, cv2.LINE_AA, shift=3)
    sway = math.sin(t * 0.9) * 0.010 * wind + math.sin(t * 2.3 + 1) * 0.005 * wind
    def swayed(P):
        P = np.asarray(P, F32).copy(); P[:, 0] += sway * np.clip(P[:, 1], 0, 2) ** 1.3; return P
    body_m = np.zeros((h_, w_), F32); hair_m = np.zeros((h_, w_), F32)
    fill(body_m, _px(_spline(outline, 12), cx, cy, h, mirror, rot))
    if head is not None: fill(body_m, _px(_spline(head, 10), cx, cy, h, mirror, rot))
    fill(hair_m, _px(swayed(_spline(hair, 16)), cx, cy, h, mirror, rot))
    # curls: discs along the hair edge (they make the outline lacy)
    n = int(min(900, max(120, h * 3.0)))
    C = _curls(pose, seed, n)
    Cp = C.copy(); Cp[:, 0] += sway * np.clip(C[:, 1], 0, 2) ** 1.3 + np.sin(t * 1.7 + C[:, 1] * 9) * 0.004 * wind
    xy = _px(Cp[:, :2], cx, cy, h, mirror, rot)
    rr = np.maximum(0.6, C[:, 2] * h)
    for (x, y), r_ in zip(xy, rr):
        cv2.circle(hair_m, (int((x - x0) * S8), int((y - y0) * S8)), int(r_ * S8), 1.0, -1, cv2.LINE_AA, shift=3)
    if fine:
        Cf = _curls_fine(pose, seed, int(fine))
        Cfp = Cf.copy(); Cfp[:, 0] += sway * np.clip(Cf[:, 1], 0, 2) ** 1.3
        for (x, y), r_ in zip(_px(Cfp[:, :2], cx, cy, h, mirror, rot), np.maximum(0.6, Cf[:, 2] * h)):
            cv2.circle(hair_m, (int((x - x0) * S8), int((y - y0) * S8)), int(r_ * S8), 1.0, -1, cv2.LINE_AA, shift=3)
    # flyaway strands: thin arcs beyond the edge (they catch the light most)
    fly = np.zeros((h_, w_), F32)
    lw = max(1, int(round(h / 220)))
    for (p, tg, nr, ln, bend, ph) in _flyaways(pose, seed, int(min(28 if not fine else 90, max(6, h / 14)))):
        u = np.linspace(0, 1, 10, dtype=F32)[:, None]
        Pp = p[None] + nr[None] * u * ln * 0.7 + tg[None] * (u ** 2) * ln * bend * 1.2 + nr[None] * np.sin(u * 5 + ph + t * 0.7) * 0.012
        q = _px(Pp, cx, cy, h, mirror, rot)
        cv2.polylines(fly, [np.round((q - [x0, y0]) * S8).astype(np.int32)], False, 0.35, lw, cv2.LINE_AA, shift=3)
    hair_all = np.clip(hair_m, 0, 1)
    sil = np.clip(np.maximum(body_m, hair_all), 0, 1)
    if clip is not None: sil *= clip[y0:y1, x0:x1]; fly *= clip[y0:y1, x0:x1]
    if dep is not None and depth is not None:
        vis = (dep[y0:y1, x0:x1] > depth).astype(F32); sil *= vis; fly *= vis
    sil *= op; fly *= op
    # lighting: rim where the outward normal faces the light (from the blurred mask's gradient)
    ld = np.asarray(light_dir, F32); ld = ld / max(1e-6, np.linalg.norm(ld))
    sig = max(0.7, h / 95)
    blur = cv2.GaussianBlur(sil, (0, 0), sig)
    gx = cv2.Sobel(blur, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(blur, cv2.CV_32F, 0, 1, ksize=3)
    facing = np.clip(-(gx * ld[0] + gy * ld[1]) * (sig * 4.0), 0, 1)
    if backlit > 0:   # light from behind her: edges glow where what is behind them is bright (the window)
        gl = np.sqrt(gx * gx + gy * gy) + 1e-6
        gm = np.clip(gl * (sig * 4.0), 0, 1)
        side = np.clip(0.5 - 0.5 * (gx * ld[0] + gy * ld[1]) / gl, 0, 1)      # 1 on edges toward the light
        bgl = img[y0:y1, x0:x1].mean(2)
        bgl = cv2.GaussianBlur(bgl, (0, 0), max(1.0, h / 12))
        bgn = np.clip(bgl / max(1e-5, float(np.percentile(bgl, 99))), 0, 1) ** 0.8
        facing = np.clip(facing * 0.45 + backlit * gm * bgn * (0.12 + 0.88 * side ** 1.5), 0, 1)
    # the rim is never an even stroke: it breaks up along the edge (curls, folds, fabric)
    yy_, xx_ = np.mgrid[0:h_, 0:w_].astype(F32)
    brk = sample(fbm_tex(256, 1.5, 211 + seed % 5), (xx_ + x0 - cx) * (40.0 / max(8.0, h)) + seed * 13, (yy_ + y0 - cy) * (40.0 / max(8.0, h)), 1.0)
    facing = facing * np.clip(0.35 + 1.1 * brk, 0, 1.2)
    # light from behind catches the hair and shoulders; the hem and the lower body stay dark
    vy = np.clip((yy_ + y0 - cy) / max(4.0, h * ext * 0.85), 0, 1)
    facing = facing * (1.0 - 0.8 * vy ** 1.2)
    rim_amt = rim_amt * float(np.clip(h / 150.0, 0.3, 1.0))       # a small far figure gets a faint rim, not an outline
    rim_band = facing * sil
    # hair is translucent near its edge: light passes through the outer curls
    hair_edge = np.clip(hair_all - cv2.erode(hair_all, np.ones((3, 3), np.uint8), iterations=max(1, int(h / 50))), 0, 1)
    hair_edge = cv2.GaussianBlur(hair_edge, (0, 0), max(0.7, h / 160)) * cv2.GaussianBlur(facing, (0, 0), sig * 2) * 1.6
    hair_frac = cv2.GaussianBlur(hair_all, (0, 0), sig * 1.5)
    rim_band = rim_band * (0.35 + 0.65 * np.clip(hair_frac * 1.4, 0, 1))
    soft = cv2.GaussianBlur(rim_band, (0, 0), max(0.6, h / 120))
    rimk = np.clip(soft * 1.25 + hair_edge * 0.9, 0, 1.4) * rim_amt
    hl = rim if hair_light is None else np.asarray(hair_light, F32)
    reg = img[y0:y1, x0:x1]
    A = np.clip(sil + fly * 0.0, 0, 1)[..., None]
    col = body[None, None] * (1 - rimk[..., None] * 0.3) + rim[None, None] * rimk[..., None]
    reg *= (1 - A); reg += col * A
    # flyaways are mostly light, not shadow
    fl = (fly * np.clip(cv2.GaussianBlur(facing, (0, 0), sig * 3) * 2.5, 0, 1))[..., None]
    reg += hl[None, None] * fl * 0.6 * rim_amt
    if emis is not None:
        er = emis[y0:y1, x0:x1]; er *= (1 - A)
        er += rim[None, None] * (rimk * 0.30 * glow)[..., None] * A + hl[None, None] * fl * 0.25 * rim_amt * glow
    if dep is not None and depth is not None:
        d = dep[y0:y1, x0:x1]; d[sil > 0.5] = depth
    full = np.zeros((H, W), F32); full[y0:y1, x0:x1] = sil
    return full
