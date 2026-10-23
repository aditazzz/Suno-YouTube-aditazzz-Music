"""Her shadow: her silhouette (a mask in her own plane) projected from a point light onto the first surface each ray hits
(plaza, the Feed Tower's two hero faces), warped straight into the screen with homographies.

The light is wherever the story needs it: the sun far away gives her honest shadow; a light pulled close behind her
makes the shadow grow out of all proportion and climb the tower.
"""
import math
import numpy as np, cv2
import cty_city as CC
from cty_eng import F32

BIG = 1e5


def receivers():
    """(id, Q, N, ea, eb, (a0, a1, b0, b1)) — plane through Q with normal N (facing the light side), in-plane axes."""
    out = [(CC.GROUND, np.array([0.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([1.0, 0, 0]), np.array([0, 0, 1.0]),
            (-BIG, BIG, -BIG, BIG))]
    for nm, fid in (('S', CC.T1F), ('W', CC.T1W)):
        C, n, u = CC.T1FACES[nm]
        ea = (C[1] - C[0]) / np.linalg.norm(C[1] - C[0])
        out.append((fid, C[0], n, ea, np.array([0, 1.0, 0]), (0.0, float(np.linalg.norm(C[1] - C[0])), 0.0, CC.T1H)))
    return out


RECV = receivers()


def plane_maps(origin, e1, e2, Lp, Q, N, ea, eb):
    """Homography M: her-plane (u, v, 1) -> receiver-plane (a, b, 1), and the scalar c for the ray parameter."""
    d0 = origin - Lp
    c = float(np.dot(Q - Lp, N))
    row_w = np.array([np.dot(e1, N), np.dot(e2, N), np.dot(d0, N)])
    ka = float(np.dot(Lp - Q, ea)); kb = float(np.dot(Lp - Q, eb))
    row_a = ka * row_w + c * np.array([np.dot(e1, ea), np.dot(e2, ea), np.dot(d0, ea)])
    row_b = kb * row_w + c * np.array([np.dot(e1, eb), np.dot(e2, eb), np.dot(d0, eb)])
    return np.stack([row_a, row_b, row_w]), c, row_w


class Shadow:
    """Her silhouette + a light: assigns every silhouette pixel to the first receiver its ray hits."""

    def __init__(self, sil, ox, oy, ppm, origin, e1, e2, Lp):
        self.sil, self.ox, self.oy, self.ppm = sil, ox, oy, ppm
        self.origin, self.e1, self.e2, self.Lp = np.asarray(origin, float), np.asarray(e1, float), np.asarray(e2, float), np.asarray(Lp, float)
        hs, ws = sil.shape
        self.T = np.array([[1 / ppm, 0, -ox / ppm], [0, -1 / ppm, oy / ppm], [0, 0, 1]])
        yy, xx = np.mgrid[0:hs, 0:ws].astype(np.float64)
        U = (xx - ox) / ppm; Vv = (oy - yy) / ppm
        best_s = np.full((hs, ws), np.inf); best = np.full((hs, ws), -1, np.int32)
        self.maps = []
        for k, (rid, Q, N, ea, eb, ext) in enumerate(RECV):
            M, c, row_w = plane_maps(self.origin, self.e1, self.e2, self.Lp, Q, N, ea, eb)
            w = row_w[0] * U + row_w[1] * Vv + row_w[2]
            with np.errstate(divide='ignore', invalid='ignore'):
                s = c / w
                a = (M[0, 0] * U + M[0, 1] * Vv + M[0, 2]) / w
                b = (M[1, 0] * U + M[1, 1] * Vv + M[1, 2]) / w
            ok = (s > 1.0005) & np.isfinite(s) & (a >= ext[0]) & (a <= ext[1]) & (b >= ext[2]) & (b <= ext[3])
            better = ok & (s < best_s)
            best_s[better] = s[better]; best[better] = k
            self.maps.append((rid, M, Q, ea, eb, ext))
        self.best = best

    def part(self, k):
        return (self.sil * (self.best == k)).astype(F32)

    def coverage(self, res=4.0):
        """{face id: coverage map in plane coords (row 0 = top of the tower)} for the Feed Tower faces."""
        out = {}
        for k, (rid, M, Q, ea, eb, ext) in enumerate(self.maps):
            if rid == CC.GROUND: continue
            mk = self.part(k)
            if mk.max() < 0.01: out[rid] = None; continue
            a1, b1 = ext[1], ext[3]
            S = np.array([[res, 0, 0], [0, -res, b1 * res], [0, 0, 1]])
            out[rid] = cv2.warpPerspective(mk, S @ M @ self.T, (int(a1 * res) + 1, int(b1 * res) + 1), flags=cv2.INTER_LINEAR)
        return out

    def screen(self, ctx, side_n=None, blur=1.0):
        cam = ctx.cam; W, H = cam.W, cam.H
        out = np.zeros((H, W), F32)
        for k, (rid, M, Q, ea, eb, ext) in enumerate(self.maps):
            mk = self.part(k)
            if mk.max() < 0.01: continue
            Hm = cam.homography_plane(Q, ea, eb) @ M @ self.T
            warped = cv2.warpPerspective(mk, Hm, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
            rec = (ctx.idb == rid)
            if rid == CC.GROUND and side_n is not None and hasattr(ctx, 'gs'):
                gx, gz, dist, st = ctx.gs
                side = ((gx - self.origin[0]) * side_n[0] + (gz - self.origin[2]) * side_n[2]) > 0.0
                side = cv2.resize(side.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST).astype(bool)
                rec &= side
            out = np.maximum(out, warped * rec)
        if blur > 0: out = cv2.GaussianBlur(out, (0, 0), blur)
        return out


def window_cover(cover, res):
    """Fraction of each Feed Tower window (row 0 = lowest floor, cols left->right on the face) inside the shadow."""
    out = np.zeros((CC.T1_ROWS, CC.T1_COLS), F32)
    if cover is None: return out
    h, w = cover.shape
    for r in range(CC.T1_ROWS):
        y0 = CC.T1Y0 + (r + 0.2) * CC.FLOOR; y1 = CC.T1Y0 + (r + 0.9) * CC.FLOOR
        py0 = int((CC.T1H - y1) * res); py1 = max(py0 + 1, int((CC.T1H - y0) * res))
        for c in range(CC.T1_COLS):
            px0 = int((c + 0.16) * CC.BAY * res); px1 = max(px0 + 1, int((c + 0.84) * CC.BAY * res))
            blk = cover[max(0, py0):min(h, py1), max(0, px0):min(w, px1)]
            out[r, c] = float(blk.mean()) if blk.size else 0.0
    return out
