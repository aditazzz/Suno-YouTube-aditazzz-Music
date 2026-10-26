"""The ribbon cutting (V1) and her cousin's booth at the gate (V2): silhouettes of men in suits, a red ribbon that is
cut on "ribbon", gold shovels in a mound of fresh dirt, the security fence, the booth and the man inside it.
Silhouettes are 2-D (screen space), the ribbon / fence / booth are in the valley's 3-D space.
"""
import math
from functools import lru_cache
import numpy as np, cv2
import ys_eng as E
from ys_eng import F32, hexc, nrm, sample, fbm_tex, sstep, ease_out, ease_io
import ys_world as WD
import ys_her as HER

# a man in a suit, front/back view; unit = head height, origin at the crown, y down (about 7.4 heads)
SUIT = [(-0.17, 0.92), (-0.20, 1.04), (-0.62, 1.20), (-1.02, 1.38), (-1.10, 1.70), (-1.12, 2.60), (-1.06, 3.55),
        (-0.96, 3.90), (-0.84, 3.66), (-0.82, 2.70), (-0.76, 3.90), (-0.62, 4.05), (-0.52, 5.4), (-0.48, 7.2),
        (-0.62, 7.38), (-0.10, 7.38), (-0.08, 7.2), (-0.04, 4.4), (0.04, 4.4), (0.08, 7.2), (0.10, 7.38),
        (0.62, 7.38), (0.48, 7.2), (0.52, 5.4), (0.62, 4.05), (0.76, 3.90), (0.82, 2.70), (0.84, 3.66),
        (0.96, 3.90), (1.06, 3.55), (1.12, 2.60), (1.10, 1.70), (1.02, 1.38), (0.62, 1.20), (0.20, 1.04), (0.17, 0.92)]
HEAD = [(0.0, 0.0), (0.30, 0.07), (0.38, 0.38), (0.32, 0.72), (0.17, 0.94), (-0.17, 0.94), (-0.32, 0.72), (-0.38, 0.38), (-0.30, 0.07)]
CAP = [(-0.40, 0.30), (-0.36, 0.0), (0.0, -0.10), (0.36, 0.0), (0.40, 0.30), (0.62, 0.36), (0.62, 0.42), (-0.40, 0.42)]

def man(img, cx, cy, h, rim, light_dir=(0, -1), body=None, arm_up=0.0, cap=False, op=1.0, emis=None, seed=0, sway=0.0):
    """a man in a suit (or a guard's jacket) as a silhouette; cx, cy = crown; h = head height px."""
    body = hexc('040506') if body is None else body
    H, W = img.shape[:2]
    x0 = int(max(0, cx - h * 1.6)); x1 = int(min(W, cx + h * 1.6)); y0 = int(max(0, cy - h * 0.5)); y1 = int(min(H, cy + h * 7.6))
    if x1 <= x0 or y1 <= y0: return None
    m = np.zeros((y1 - y0, x1 - x0), F32)
    def fill(pts):
        P = np.asarray(HER._spline(pts, 8), F32) * h + [cx + sway * h, cy]
        cv2.fillPoly(m, [np.round((P - [x0, y0]) * 8).astype(np.int32)], 1.0, cv2.LINE_AA, shift=3)
    fill(SUIT); fill(HEAD)
    if cap: fill(CAP)
    if arm_up > 0:   # the right arm raised forward (holding the scissors / the ribbon)
        a0 = np.array([0.95, 1.55]); a1 = a0 + np.array([0.55, 0.9 - 1.6 * arm_up])
        P = np.array([a0, a1], F32) * h + [cx, cy]
        cv2.line(m, tuple(np.round((P[0] - [x0, y0]) * 8).astype(int)), tuple(np.round((P[1] - [x0, y0]) * 8).astype(int)), 1.0, max(1, int(h * 0.42)), cv2.LINE_AA, shift=3)
    m *= op
    ld = np.asarray(light_dir, F32); ld = ld / max(1e-6, np.linalg.norm(ld))
    b = cv2.GaussianBlur(m, (0, 0), max(0.8, h / 25))
    gx = cv2.Sobel(b, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(b, cv2.CV_32F, 0, 1, ksize=3)
    rimk = np.clip(-(gx * ld[0] + gy * ld[1]) * (h / 6), 0, 1) * m
    rimk = cv2.GaussianBlur(rimk, (0, 0), max(0.6, h / 60))
    reg = img[y0:y1, x0:x1]
    A = m[..., None]
    reg *= (1 - A); reg += (body + np.asarray(rim, F32) * rimk[..., None]) * A
    if emis is not None: emis[y0:y1, x0:x1] *= (1 - A)
    full = np.zeros((H, W), F32); full[y0:y1, x0:x1] = m
    return full

# ---------------------------------------------------------------- ribbon cutting
CER = np.array([-618.0, 0.0, 84.0], F32)           # at the campus entrance, the facility 150 m behind

def ceremony_cam(W, H, t, u):
    eye = CER + np.array([3.5 - 1.2 * u, 1.35, -12.5 + 1.5 * u], F32)
    tgt = CER + np.array([-2.0, 21.0 + 1.0 * u, 150.0], F32)
    return E.Cam(eye, tgt, fov=38, W=W, H=H, drift=0.015, t=t, seed=31)

def draw_ceremony(W, H, t, u, S, t_cut, t_shovel):
    """S: valley state (dusk). t_cut: when the scissors close (the ribbon parts), t_shovel: the gold glint."""
    cam = ceremony_cam(W, H, t, u)
    VS = dict(S)
    men = [(-7.5, 0.98), (-4.2, 1.03), (-1.5, 0.97), (1.4, 1.05), (4.4, 1.0), (7.6, 0.96)]     # (x offset m, height scale)
    def extra(cv):
        # gold shovels in a mound of fresh dirt (left foreground)
        mound_c = CER + np.array([-5.6, 0, -6.5], F32)
        draw_mound(cv, mound_c, VS, t, t_shovel)
        # the ribbon on two stanchions, cut at t_cut: the two halves fall and sway
        draw_ribbon(cv, CER + np.array([-10.0, 0, 0.0], F32), CER + np.array([10.0, 0, 0.0], F32), 1.05, t, t_cut, VS)
    cv = WD.render(cam, VS, t, extra=extra, town_on=True)
    img = WD.compose(cv)
    # the men (behind the ribbon, a step back), backlit by the dusk sky
    for i, (dx, hs) in enumerate(men):
        P = CER + np.array([dx, 1.82 * hs, 1.2 + (i % 2) * 0.6], F32)
        x, y, z = cam.project(P[None])
        hh = 0.245 * hs * cam.fpx / z[0]
        arm = 0.0
        if i == 2: arm = 0.55 if t < t_cut else 0.35       # the one with the scissors
        man(img, float(x[0]), float(y[0]), hh, rim=hexc('ff9a7a') * 0.25 * S.get('dusk', 1.0) + hexc('cfe2ee') * 0.04, light_dir=(0.1, -1.0),
            body=hexc('050607') * 0.6, arm_up=arm, emis=cv.emis, seed=i, sway=0.01 * math.sin(t * 0.8 + i))
        if i == 2: draw_scissors(img, cam, P + np.array([0.75, -0.55, -0.9], F32), t, t_cut)
    # her, in the right foreground, back to us, watching (soft: out of focus)
    hp = CER + np.array([4.4, 1.72, -9.6], F32)
    x, y, z = cam.project(hp[None]); hh = 0.235 * cam.fpx / z[0]
    lay = np.zeros_like(img)
    m = HER.draw(lay, 'profile', float(x[0]), float(y[0]), hh, light_dir=(-0.4, -1.0), rim=hexc('ff9a7a') * 0.5, mirror=True, t=t, backlit=0.6, seed=3)
    if m is not None:
        mb = cv2.GaussianBlur(m, (0, 0), 3.0 * E.pxs(W, H))
        lb = cv2.GaussianBlur(lay, (0, 0), 3.0 * E.pxs(W, H))
        img = img * (1 - mb[..., None]) + lb
    return img

def draw_ribbon(cv, A, B, h, t, t_cut, S):
    cam = cv.cam
    red = hexc('c8102e')
    sheen = hexc('ff7d8a') * 0.15 * S.get('dusk', 1.0) + hexc('cfe2ee') * 0.02
    for P in (A, B):   # stanchions
        cv.line3(P, P + np.array([0, h + 0.05, 0], F32), hexc('c9a24a') * 0.08, width_m=0.05, min_px=1.2)
    n = 40
    s = np.linspace(0, 1, n, dtype=F32)[:, None]
    if t < t_cut:
        sag = 0.05 + 0.02 * math.sin(t * 1.3)
        Pts = A[None] * (1 - s) + B[None] * s + np.array([0, h, 0], F32)
        Pts[:, 1] -= sag * 4 * s[:, 0] * (1 - s[:, 0])
        Pts[:, 2] += 0.08 * np.sin(s[:, 0] * 9 + t * 2.0)
        segs = [Pts]
    else:
        k = ease_out(min(1.0, (t - t_cut) / 1.1))
        mid = (A + B) / 2
        segs = []
        for P0 in (A, B):
            L = float(np.linalg.norm(mid - P0)) - 0.15
            dirv = (mid - P0) / max(1e-6, np.linalg.norm(mid - P0))
            pts = []
            for a_ in np.linspace(0, 1, n // 2, dtype=F32):
                fall = min(1.0, k * (0.15 + 1.9 * a_))
                y = max(0.03, h * (1 - fall) - 0.04 * math.sin(a_ * 6 + t * 3) * (1 - k))
                along = a_ * L * (1 - 0.18 * k * a_)
                wig = 0.25 * math.sin(a_ * 7 + 1.3) * k * a_
                pts.append(P0 + dirv * along + np.array([0, y, wig], F32))
            segs.append(np.array(pts, F32))
    for Pts in segs:
        for a, b in zip(Pts[:-1], Pts[1:]):
            cv.line3(a, b, red * 0.20 + sheen, width_m=0.11, min_px=1.4, emis=red * 0.03)

def draw_scissors(img, cam, P, t, t_cut):
    """giant ceremonial scissors in silhouette with a gold edge; they close on t_cut."""
    x, y, z = cam.project(P[None])
    if z[0] < 0.5: return
    s = cam.fpx / z[0] * 0.45
    k = 0.0 if t < t_cut - 0.25 else ease_out(min(1.0, (t - (t_cut - 0.25)) / 0.25))
    open_a = math.radians(26) * (1 - k)
    cx, cy = float(x[0]), float(y[0])
    for sgn in (1, -1):
        a = sgn * open_a / 2
        tip = (cx + math.cos(a) * s * 1.0, cy - math.sin(a) * s * 1.0)
        piv = (cx - s * 0.05, cy)
        ring = (cx - math.cos(-a) * s * 0.38, cy + math.sin(-a) * s * 0.38 * 2.2 * sgn * 0.3)
        cv2.line(img, (int(piv[0]), int(piv[1])), (int(tip[0]), int(tip[1])), (hexc('d8b45a') * 0.4).tolist(), max(1, int(s * 0.07)), cv2.LINE_AA)
        cv2.circle(img, (int(ring[0]), int(ring[1])), max(2, int(s * 0.11)), (hexc('d8b45a') * 0.35).tolist(), max(1, int(s * 0.04)), cv2.LINE_AA)

def draw_mound(cv, C, S, t, t_shovel):
    cam = cv.cam
    x, y, z = cam.project(C[None])
    if z[0] < 0.5: return
    s = cam.fpx / z[0]
    rx = 1.8 * s; ry = 0.55 * s
    H, W = cv.H, cv.W
    x0, x1 = int(max(0, x[0] - rx * 1.2)), int(min(W, x[0] + rx * 1.2)); y0, y1 = int(max(0, y[0] - ry * 1.3)), int(min(H, y[0] + ry * 0.3))
    if x1 > x0 and y1 > y0:
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(F32)
        u = (xx - x[0]) / rx; v = (yy - y[0]) / ry
        nz = sample(fbm_tex(256, 1.6, 141), xx * 0.3, yy * 0.3, 1.0)
        m = np.clip((1 - u * u - (v + 1) ** 2 * 0.0 - np.maximum(-v, 0) ** 1.4 * 1.0 + (nz - 0.5) * 0.4) * 5, 0, 1) * (v < 0.15)
        col = hexc('2a1e16') * (WD.ambient_light(S) * 4 + 0.003) * (0.7 + 0.6 * nz[..., None])
        reg = cv.img[y0:y1, x0:x1]; reg *= (1 - m[..., None]); reg += col * m[..., None]
    # three gold shovels stuck in at an angle; a glint runs down each blade on "shovel"
    for i, (dx, ang) in enumerate(((-0.7, 0.18), (0.1, -0.08), (0.8, 0.25))):
        base = C + np.array([dx, 0.35, 0.1 * i], F32)
        top = base + np.array([math.sin(ang) * 1.3, 1.25, 0], F32)
        cv.line3(base, top, hexc('8a6a30') * 0.03, width_m=0.045, min_px=1.0)
        glint = math.exp(-((t - t_shovel - i * 0.12) / 0.12) ** 2)
        bl0 = base - np.array([math.sin(ang) * 0.45, 0.45, 0], F32)
        cv.line3(bl0, base, hexc('d8b45a') * (0.08 + 0.9 * glint), width_m=0.22, min_px=1.5, emis=hexc('ffd890') * glint * 0.8)

# ---------------------------------------------------------------- the fence, the gate and the booth
def draw_fence(cv, S, t, x0=-835.0, x1=-405.0):
    """chain-link perimeter fence with barbed wire, posts every 3 m, and the gate opening at GATE."""
    cam = cv.cam; z = WD.FENCE_Z; hF = 3.2
    amb = WD.ambient_light(S)
    post_col = hexc('2a2d30') * (amb * 3 + 0.002)
    gx = float(WD.GATE[0])
    for a, b in ((x0, gx - 5.0), (gx + 5.0, x1)):
        def alpha(X, Y, Z, m):
            P = WD._world_from_screen(cam, X, Y, Z)
            u = P[..., 0] / 0.06; v = P[..., 1] / 0.06
            d1 = np.abs(((u + v) % 1.0) - 0.5); d2 = np.abs(((u - v) % 1.0) - 0.5)
            px = np.maximum(1e-3, Z / cam.fpx) / 0.06          # mesh cells per pixel
            wire = np.clip((np.maximum(d1, d2) - 0.5 + 0.08 + px * 0.5) / (0.08 + px), 0, 1)
            return np.clip(wire * 0.6 + np.clip(px * 0.5, 0, 0.45), 0, 0.85)
        P = np.array([[a, hF, z], [b, hF, z], [b, 0, z], [a, 0, z]], F32)
        cv.poly(P, post_col * 1.3 + hexc('cfe2ee') * 0.003, alpha=alpha, ztest=True, write_depth=False)
        xs = np.arange(a, b + 0.01, 3.0, dtype=F32)
        A = np.stack([xs, np.zeros_like(xs), np.full_like(xs, z)], 1); B = A + np.array([0, hF + 0.6, 0], F32)
        E.lines_batch(cv, A, B, post_col, width_m=0.07, min_px=0.7)
        E.lines_batch(cv, np.array([[a, hF, z], [a, hF + 0.3, z - 0.2], [a, hF + 0.55, z - 0.35]], F32), np.array([[b, hF, z], [b, hF + 0.3, z - 0.2], [b, hF + 0.55, z - 0.35]], F32),
                      post_col, width_m=0.02, min_px=0.6)

def draw_booth(cv, S, t, inside_light=1.0):
    """the guard booth just outside the gate: a small box with wide windows, warm-lit, a flat roof, a lamp."""
    cam = cv.cam; c = WD.BOOTH
    w, d, h = 2.4, 2.0, 2.7
    amb = WD.ambient_light(S)
    warm = hexc('ffd49a')
    def B(x, y, z): return np.array([c[0] + x, y, c[2] + z], F32)
    faces = [([B(-w / 2, h, -d / 2), B(w / 2, h, -d / 2), B(w / 2, 0, -d / 2), B(-w / 2, 0, -d / 2)], (0, 0, -1)),
             ([B(w / 2, h, -d / 2), B(w / 2, h, d / 2), B(w / 2, 0, d / 2), B(w / 2, 0, -d / 2)], (1, 0, 0)),
             ([B(-w / 2, h, d / 2), B(-w / 2, h, -d / 2), B(-w / 2, 0, -d / 2), B(-w / 2, 0, d / 2)], (-1, 0, 0)),
             ([B(w / 2, h, d / 2), B(-w / 2, h, d / 2), B(-w / 2, 0, d / 2), B(w / 2, 0, d / 2)], (0, 0, 1))]
    for pts, n in faces:
        P = np.array(pts, F32); nn = np.array(n, F32)
        if np.dot(nn, P.mean(0) - cam.eye) >= 0: continue
        cv.poly(P, hexc('9a968c') * (amb * 2.5 + 0.004), ztest=True)
        # a wide window in each wall (warm light inside)
        q = P.copy(); ctr = q.mean(0)
        win = ctr + (q - ctr) * np.array([0.78, 1, 0.78], F32)
        win[:, 1] = np.array([h - 0.35, h - 0.35, 1.05, 1.05], F32)
        cv.poly(win - nn * 0.01, warm * 0.12 * inside_light, emis=warm * 0.55 * inside_light, ztest=True, write_depth=False)
    roof = np.array([B(-w / 2 - 0.25, h + 0.25, -d / 2 - 0.25), B(w / 2 + 0.25, h + 0.25, -d / 2 - 0.25), B(w / 2 + 0.25, h, -d / 2 - 0.25), B(-w / 2 - 0.25, h, -d / 2 - 0.25)], F32)
    cv.poly(roof, hexc('1a1b1d') * (amb * 3 + 0.002), ztest=True)
    E.lights(cv, [B(0, h + 0.45, -d / 2 - 0.2)], hexc('fff0d8'), 2.5, size_m=0.12)
    # the barrier arm across the gate road
    a0 = np.array([WD.GATE[0] + 4.2, 1.0, WD.GATE[2] - 1.0], F32); a1 = a0 + np.array([-8.0, 0, 0], F32)
    cv.line3(a0, a1, hexc('d8d4c8') * 0.04 + hexc('b3203a') * 0.0, width_m=0.09, min_px=1.0)
    for k in range(4):
        p0 = a0 + (a1 - a0) * (k / 4 + 0.06); p1 = a0 + (a1 - a0) * (k / 4 + 0.16)
        cv.line3(p0, p1, hexc('b3203a') * 0.05, width_m=0.095, min_px=1.0)
