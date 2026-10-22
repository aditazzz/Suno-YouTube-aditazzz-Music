"""Per-pixel ray tracing of the vehicle's surfaces of revolution (tanks, interstage, fairing, engine bells):
smooth normals, soft point-light falloff, semi-gloss specular, soot/frost/panel detail from (height, angle) textures.
Supersampled inside the screen bounding box; returns premultiplied colour, coverage and depth so the flat-shaded
parts (legs, grid fins) can be composited in the right order.
"""
import math
from functools import lru_cache
import numpy as np, cv2
import ekg as K
from ekg import F32

class Part:
    """a surface of revolution about local +Y. prof: [(y, r), ...] bottom->top. mat(y, ang, ins) -> (alb (n,3), ks (n,), emi (n,3) or None).
    B: base position (world), R: local->world rotation (3x3)."""
    def __init__(self, prof, mat, B=(0, 0, 0), R=None, caps=(), two_sided=False, tag=""):
        self.prof = [(float(y), float(r)) for y, r in prof]; self.mat = mat
        self.B = np.asarray(B, F32); self.R = np.eye(3, dtype=F32) if R is None else np.asarray(R, F32)
        self.caps = caps; self.two_sided = two_sided; self.tag = tag
        self.ymin = min(y for y, _ in self.prof); self.ymax = max(y for y, _ in self.prof); self.rmax = max(r for _, r in self.prof)

def bbox_px(cam, part, pad=3):
    ys = (part.ymin, part.ymax); r = part.rmax
    pts = []
    for y in ys:
        for a in range(8):
            ang = a * math.pi / 4
            pts.append(part.B + part.R @ np.array([math.cos(ang) * r * 1.09, y, math.sin(ang) * r * 1.09], F32))
    pts = np.array(pts, F32)
    x, y, z = cam.project(pts)
    if (z <= 0.2).all(): return (0, 0, 0, 0)            # entirely behind the camera: nothing to trace
    if (z <= 0.2).any(): return None                     # crosses the camera plane: trace the whole frame
    return (int(math.floor(x.min())) - pad, int(math.floor(y.min())) - pad, int(math.ceil(x.max())) + pad, int(math.ceil(y.max())) + pad)

def _rays(cam, X, Y):
    D = (cam.f[None] * cam.fpx + cam.r[None] * (X - cam.W / 2 - cam.sx)[:, None] + cam.u[None] * (cam.H / 2 + cam.sy - Y)[:, None])
    return (D / np.linalg.norm(D, axis=1, keepdims=True)).astype(F32)

def _trace_rays(cam, parts, boxes, lights, X, Y, env=None):
    """intersect + shade flat arrays of rays through pixel coords (X, Y). Each part only tests the rays inside its own
    screen box. returns colour (n,3), depth (n,) (inf = miss), part index (n,) (-1 = miss)."""
    n = X.shape[0]
    D = _rays(cam, X, Y); O = cam.eye
    best = np.full(n, np.inf, F32); col = np.zeros((n, 3), F32); pid = np.full(n, -1, np.int32)
    for pi, (p, bb) in enumerate(zip(parts, boxes)):
        sel = np.nonzero((X >= bb[0]) & (X < bb[2]) & (Y >= bb[1]) & (Y < bb[3]))[0]
        if len(sel) == 0: continue
        RT = p.R.T
        o = RT @ (O - p.B); d = D[sel] @ RT.T
        m_ = len(sel)
        hit_s = np.full(m_, np.inf, F32); hy = np.zeros(m_, F32); hk = np.zeros(m_, F32); hrho = np.ones(m_, F32)
        for (ya, ra), (yb, rb) in zip(p.prof[:-1], p.prof[1:]):
            if yb - ya < 1e-6: continue
            k = (rb - ra) / (yb - ya)
            c = ra + k * (o[1] - ya); e = k * d[:, 1]
            A = d[:, 0] ** 2 + d[:, 2] ** 2 - e * e
            Bq = 2 * (o[0] * d[:, 0] + o[2] * d[:, 2] - c * e)
            Cq = o[0] ** 2 + o[2] ** 2 - c * c
            disc = Bq * Bq - 4 * A * Cq
            ok = disc >= 0
            if not ok.any(): continue
            sq = np.sqrt(np.where(ok, disc, 0))
            Aa = np.where(np.abs(A) < 1e-9, 1e-9, A)
            for sgn in (-1, 1):
                sr = (-Bq + sgn * sq) / (2 * Aa)
                yy = o[1] + sr * d[:, 1]
                rho = c + sr * e
                good = ok & (sr > 0.05) & (yy >= ya) & (yy <= yb) & (rho >= 0) & (sr < hit_s)
                if good.any():
                    hit_s = np.where(good, sr, hit_s); hy = np.where(good, yy, hy); hk = np.where(good, k, hk); hrho = np.where(good, rho, hrho)
        for (yc, ri, ro, calb, cemi) in p.caps:
            sr = (yc - o[1]) / np.where(np.abs(d[:, 1]) < 1e-9, 1e-9, d[:, 1])
            px = o[0] + sr * d[:, 0]; pz = o[2] + sr * d[:, 2]; rr = np.sqrt(px * px + pz * pz)
            good = (sr > 0.05) & (rr <= ro) & (rr >= ri) & (sr < hit_s)
            if good.any():
                hit_s = np.where(good, sr, hit_s); hy = np.where(good, yc, hy); hk = np.where(good, np.nan, hk)
        m = np.isfinite(hit_s) & (hit_s < best[sel])
        if not m.any(): continue
        li = np.nonzero(m)[0]; idx = sel[li]
        s_ = hit_s[li]; Pl = o[None] + d[li] * s_[:, None]
        is_cap = np.isnan(hk[li])
        nl = np.stack([Pl[:, 0], -np.nan_to_num(hk[li]) * hrho[li], Pl[:, 2]], 1)
        nl[is_cap] = [0, 1, 0]
        nl /= np.maximum(np.linalg.norm(nl, axis=1, keepdims=True), 1e-6)
        inside = (nl * d[li]).sum(1) > 0
        if p.two_sided: nl[inside] *= -1
        ang = np.arctan2(Pl[:, 2], Pl[:, 0])
        alb, ks, emi = p.mat(Pl[:, 1], ang, inside & ~is_cap)
        if is_cap.any():
            for (yc, ri, ro, calb, cemi) in p.caps:
                cm = is_cap & (np.abs(Pl[:, 1] - yc) < 1e-3)
                if cm.any():
                    alb[cm] = calb
                    if cemi is not None:
                        emi = np.zeros_like(alb) if emi is None else emi; emi[cm] = cemi
        Pw = Pl @ p.R.T + p.B; Nw = nl @ p.R.T; V = -D[idx]
        c = shade(Pw, Nw, V, alb, ks, lights, env)
        if emi is not None: c = c + emi
        best[idx] = s_; col[idx] = c; pid[idx] = pi
    return col, best, pid

def trace(img, cam, parts, lights, ss=2, env=None, depth_out=None):
    """ray-trace `parts` and composite over img (in place). One ray per pixel, then ss x ss rays only on the pixels at
    silhouettes and part boundaries (adaptive anti-aliasing). returns (coverage (H,W), depth (H,W) with inf where empty)."""
    H, W = img.shape[:2]
    boxes = []
    for p in parts:
        b = bbox_px(cam, p)
        boxes.append((0, 0, W, H) if b is None else b)
    x0 = max(0, min(b[0] for b in boxes)); y0 = max(0, min(b[1] for b in boxes))
    x1 = min(W, max(b[2] for b in boxes)); y1 = min(H, max(b[3] for b in boxes))
    cov_full = np.zeros((H, W), F32); dep_full = np.full((H, W), np.inf, F32)
    if x1 <= x0 or y1 <= y0: return cov_full, dep_full
    w, h = x1 - x0, y1 - y0
    Yg, Xg = np.mgrid[y0:y1, x0:x1].astype(F32)
    X = Xg.ravel() + 0.5; Y = Yg.ravel() + 0.5
    col, best, pid = _trace_rays(cam, parts, boxes, lights, X, Y, env)
    col = col.reshape(h, w, 3); best = best.reshape(h, w); pid = pid.reshape(h, w)
    hit = np.isfinite(best)
    cov = hit.astype(F32)
    if ss > 1 and hit.any():
        # edge pixels: a neighbour differs in part id (silhouettes, part boundaries) or depth jumps
        pz = np.pad(pid, 1, mode="edge"); dz = np.pad(np.where(hit, best, 1e9), 1, mode="edge")
        edge = np.zeros((h, w), bool)
        for dy, dx in ((0, 1), (1, 0), (2, 1), (1, 2)):
            edge |= pz[dy:dy + h, dx:dx + w] != pid
            nb = dz[dy:dy + h, dx:dx + w]
            edge |= np.abs(nb - np.where(hit, best, 1e9)) > 0.04 * np.minimum(nb, np.where(hit, best, 1e9))
        ey, ex = np.nonzero(edge)
        if len(ey):
            acc = np.zeros((len(ey), 3), F32); hits = np.zeros(len(ey), F32); dmin = np.full(len(ey), np.inf, F32)
            for oy in range(ss):
                for ox in range(ss):
                    c2, b2, p2 = _trace_rays(cam, parts, boxes, lights, (ex + x0 + (ox + 0.5) / ss).astype(F32), (ey + y0 + (oy + 0.5) / ss).astype(F32), env)
                    h2 = np.isfinite(b2)
                    acc += c2 * h2[:, None]; hits += h2; dmin = np.minimum(dmin, b2)
            n2 = ss * ss
            col[ey, ex] = acc / n2; cov[ey, ex] = hits / n2; best[ey, ex] = dmin
            hit[ey, ex] = hits > 0
    colr = col * hit[..., None] if True else col
    roi = img[y0:y1, x0:x1]
    roi *= (1 - cov)[..., None]; roi += colr
    cov_full[y0:y1, x0:x1] = cov
    dep_full[y0:y1, x0:x1] = np.where(cov > 0.01, best, np.inf)
    return cov_full, dep_full

def shade(P, N, V, alb, ks, lights, env=None):
    """Lambert + Blinn-Phong with fresnel, point lights with soft inverse-square falloff."""
    amb = lights.ambient[None] * (0.55 + 0.45 * np.clip(N[:, 1:2], 0, 1))
    L = amb.copy(); S = np.zeros_like(L)
    fres = 0.04 + 0.96 * np.power(1 - np.clip((N * V).sum(1, keepdims=True), 0, 1), 5)
    for d, c in lights.dirs:
        l = -np.asarray(d, F32)[None]
        nd = np.clip((N * l).sum(1, keepdims=True), 0, 1)
        Hh = l + V; Hh /= np.maximum(np.linalg.norm(Hh, axis=1, keepdims=True), 1e-6)
        sp = np.power(np.clip((N * Hh).sum(1, keepdims=True), 0, 1), 60) * nd
        L += nd * c[None]; S += sp * c[None]
    for p, c, rr in lights.points:
        dv = p[None] - P; dist = np.linalg.norm(dv, axis=1, keepdims=True) + 1e-3; l = dv / dist
        att = 1.0 / (1.0 + (dist / rr) ** 2)
        nd = np.clip((N * l).sum(1, keepdims=True), 0, 1)
        Hh = l + V; Hh /= np.maximum(np.linalg.norm(Hh, axis=1, keepdims=True), 1e-6)
        sp = np.power(np.clip((N * Hh).sum(1, keepdims=True), 0, 1), 60) * nd
        L += nd * att * c[None]; S += sp * att * c[None]
    out = alb * L + S * (ks[:, None] * (0.3 + 0.7 * fres) * 2.0)
    if env is not None: out += env(N) * alb * 0.5 + env(N) * fres * ks[:, None] * 0.3
    return out

# ---------------------------------------------------------------- vehicle materials
@lru_cache(4)
def _tex(seed):
    return K.noise_tex(256, seed, 6, 0.6)

def _samp(tex, u, v):
    """u: angle (rad) wraps, v: height in metres."""
    th, tw = tex.shape
    xs = ((u / (2 * math.pi)) % 1.0) * tw; ys = (v * 4.0) % th
    xi = xs.astype(np.int32) % tw; yi = ys.astype(np.int32) % th
    return tex[yi, xi]

def mat_stage1(soot=0.0, frost=0.0, burn_glow=0.0):
    def m(y, ang, inside):
        n = y.shape[0]
        alb = np.empty((n, 3), F32); alb[:] = K.WHITE_PAINT
        ks = np.full(n, 0.35, F32)
        inter = y > K.L_S1
        alb[inter] = K.BLACK_CF; ks[inter] = 0.25
        # panel seams
        for ys in (1.0, 2.2, 15.5, 29.5, K.L_S1 - 0.6):
            seam = np.abs(y - ys) < 0.05
            alb[seam] *= 0.6
        # the raceway: a narrow cable tunnel running up one side
        rw = (np.abs(((ang - 1.2 + math.pi) % (2 * math.pi)) - math.pi) < 0.07) & (y > 1.2) & (y < K.L_S1 - 0.3)
        alb[rw] *= 0.72; ks[rw] *= 0.6
        rwe = (np.abs(np.abs(((ang - 1.2 + math.pi) % (2 * math.pi)) - math.pi) - 0.07) < 0.008) & (y > 1.2) & (y < K.L_S1 - 0.3)
        alb[rwe] *= 0.5
        if soot > 0:
            st = _samp(_tex(5), ang * 3.0, y * 0.25)
            streak = _samp(_tex(9), ang * 9.0, y * 0.02)
            h = np.clip((y - 4) / 32, 0, 1)
            a = np.clip(soot * (0.2 + 0.85 * h) * (0.35 + 0.9 * streak) * (0.7 + 0.5 * st), 0, 0.94)
            a[inter] = 0
            alb = alb * (1 - a[:, None]) + K.SOOT[None] * a[:, None]
            ks = ks * (1 - 0.7 * a)
        if frost > 0:
            fz = (y > 19.5) & (y < 40.6)
            fr = _samp(_tex(13), ang * 4, y)
            alb[fz] = alb[fz] * (1 - 0.2 * frost) + np.array([0.95, 0.97, 1.0], F32) * 0.2 * frost * fr[fz][:, None]
        alb[y < 0.9] *= 0.45                       # the base skirt / octaweb heat shield
        alb[inside] = alb[inside] * 0.1
        return alb, ks, None
    return m

def mat_upper(seam=True):
    def m(y, ang, inside):
        n = y.shape[0]
        alb = np.empty((n, 3), F32); alb[:] = K.WHITE_PAINT * 0.99
        ks = np.full(n, 0.4, F32)
        if seam:
            sm = (np.abs(np.sin(ang)) < 0.004) & (y > K.L_S2)
            alb[sm] *= 0.5
            ring = np.abs(y - (K.L_S2 + 1.4)) < 0.06
            alb[ring] *= 0.7
            rw = (np.abs(((ang - 1.2 + math.pi) % (2 * math.pi)) - math.pi) < 0.06) & (y < K.L_S2 - 0.2)
            alb[rw] *= 0.74
        return alb, ks, None
    return m

def mat_bell(glow=0.0, col=K.FLAME_W):
    def m(y, ang, inside):
        n = y.shape[0]
        alb = np.empty((n, 3), F32); alb[:] = np.array([0.30, 0.27, 0.24], F32)
        ks = np.full(n, 0.6, F32)
        emi = None
        if glow > 0:
            emi = np.zeros((n, 3), F32)
            emi[inside] = col * glow * 6.0 * (0.5 + 0.5 * np.clip(-y[inside] / 1.25, 0, 1))[:, None]
            emi[~inside] = col * glow * 0.15 * np.clip(-y[~inside] / 1.25, 0, 1)[:, None]
        alb[inside] *= 0.3
        return alb, ks, emi
    return m

def mat_mvac(glow=0.0, col=K.FLAME_W):
    def m(y, ang, inside):
        n = y.shape[0]
        alb = np.empty((n, 3), F32); alb[:] = np.array([0.18, 0.16, 0.15], F32)
        ks = np.full(n, 0.5, F32); emi = None
        if glow > 0:
            emi = np.zeros((n, 3), F32)
            emi[:] = col * glow * (0.4 + 2.5 * np.clip(-y / 3.0, 0, 1) ** 2)[:, None] * np.where(inside, 3.0, 0.6)[:, None]
        return alb, ks, emi
    return m

# ---------------------------------------------------------------- vehicle assemblies
BELL = [(-1.25, 0.46), (-0.9, 0.40), (-0.55, 0.32), (-0.25, 0.25), (0.0, 0.21)]
ENG_POS = [(0.0, 0.0)] + [(1.25 * math.cos(k * math.pi / 4 + math.pi / 8), 1.25 * math.sin(k * math.pi / 4 + math.pi / 8)) for k in range(8)]

def fairing_profile(yb):
    """the payload fairing: a gentle boat-tail cone up from the second stage, the 5.2 m cylinder, then a tangent-ogive
    nose with a small rounded tip (a pointed ogive, not a dome)."""
    fp = [(yb, K.R_BODY), (yb + 0.7, K.R_BODY + 0.42), (yb + 1.4, K.R_FAIR), (yb + 6.2, K.R_FAIR)]   # the boat-tail: a gentle cone, not a lip
    R = K.R_FAIR; Ln = K.L_FAIR - 6.2; rho = (R * R + Ln * Ln) / (2 * R)
    for k in range(1, 19):
        x = Ln * (1 - (1 - k / 18) ** 1.25)
        r = math.sqrt(max(0.0, rho * rho - x * x)) - (rho - R)
        fp.append((yb + 6.2 + x, max(0.0, r) + 0.01))
    return fp

def vehicle_parts(B, R=None, stage="full", soot=0.0, frost=0.0, eng_glow=0.0, eng_col=K.FLAME_W, center_only=False, mvac_glow=0.0, fairing=True):
    """stage: 'full' (on the pad / ascent), 'booster' (first stage + interstage), 'upper' (second stage + fairing),
    'upper_nofair' (second stage only, after fairing sep). B = base point (bottom of the first-stage tank)."""
    R = np.eye(3, dtype=F32) if R is None else np.asarray(R, F32); B = np.asarray(B, F32)
    parts = []
    if stage in ("full", "booster"):
        top = K.L_S1 + K.L_INT
        prof = [(0.0, K.R_BODY), (top, K.R_BODY)]
        caps = [(0.0, 0.0, K.R_BODY, np.array([0.05, 0.048, 0.045], F32), None)]
        if stage == "booster": caps.append((top, 0.0, K.R_BODY * 0.97, np.array([0.015, 0.015, 0.016], F32), None))
        parts.append(Part(prof, mat_stage1(soot, frost), B, R, caps=caps, tag="s1"))
        for k, (px, pz) in enumerate(ENG_POS):
            g = eng_glow if (not center_only or k == 0) else 0.0
            parts.append(Part(BELL, mat_bell(g, eng_col), B + R @ np.array([px, 0, pz], F32), R, two_sided=True, tag="bell"))
    if stage in ("full", "upper", "upper_nofair"):
        yb = (K.L_S1 + K.L_INT) if stage == "full" else 0.0
        prof = [(yb, K.R_BODY), (yb + K.L_S2, K.R_BODY)]
        parts.append(Part(prof, mat_upper(), B, R, tag="s2"))
        if stage != "upper_nofair" and fairing:
            parts.append(Part(fairing_profile(yb + K.L_S2), mat_upper(), B, R, tag="fair"))
        if stage in ("upper", "upper_nofair"):
            parts.append(Part([(-3.0, 1.55), (-1.6, 1.0), (-0.4, 0.45), (0.0, 0.35)], mat_mvac(mvac_glow), B, R, two_sided=True, tag="mvac"))
    return parts

def attachments(B, R=None, legs=0.0, fins=0.0, soot=0.0):
    """legs + grid fins as flat-shaded meshes in world space."""
    R = np.eye(3, dtype=F32) if R is None else np.asarray(R, F32)
    m = K.Mesh().extend(K.fins_mesh(fins)).extend(K.legs_mesh(legs, soot))
    return K.transform(m, R, B)

def draw_vehicle(img, cam, B, R=None, lights=None, stage="full", legs=0.0, fins=0.0, soot=0.0, frost=0.0, eng_glow=0.0,
                 eng_col=K.FLAME_W, center_only=False, mvac_glow=0.0, ss=2, fairing=True):
    """ray-traced body + engines, with legs/fins drawn behind or in front depending on which side they are on."""
    R = np.eye(3, dtype=F32) if R is None else np.asarray(R, F32); B = np.asarray(B, F32)
    lights = lights or K.Lights()
    att = attachments(B, R, legs, fins, soot) if stage in ("full", "booster") else None
    axis_mid = B + R @ np.array([0, 20, 0], F32)
    back, front = K.Mesh(), K.Mesh()
    if att is not None:
        ax = R @ np.array([0, 1, 0], F32)
        for f in att.faces:
            c = f[0].mean(0)
            # split by which side of the axis the face is relative to the camera
            rel = c - B; radial = rel - ax * float(rel @ ax)
            to_cam = cam.eye - c
            (front if float(radial @ to_cam) > 0 else back).faces.append(f)
    if back.faces: K.draw_mesh(img, cam, back, lights, ss=3)
    parts = vehicle_parts(B, R, stage, soot, frost, eng_glow, eng_col, center_only, mvac_glow, fairing)
    cov, dep = trace(img, cam, parts, lights, ss=ss)
    if front.faces: K.draw_mesh(img, cam, front, lights, ss=3)
    return cov, dep

def fairing_part(B, R=None, stage="full"):
    R = np.eye(3, dtype=F32) if R is None else np.asarray(R, F32)
    yb = (K.L_S1 + K.L_INT) if stage == "full" else 0.0
    return Part(fairing_profile(yb + K.L_S2), mat_upper(), B, R, tag="fair")
