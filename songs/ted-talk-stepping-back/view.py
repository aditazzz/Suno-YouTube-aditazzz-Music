"""A 2-D map camera: world (x east, y south) -> screen pixels, with zoom (metres per pixel) and rotation."""
import math
import numpy as np

SC = 16                                           # cv2 sub-pixel shift 4 -> x16

class View:
    def __init__(s, W, H, cx, cy, mpp, rot=0.0):
        s.W, s.H, s.cx, s.cy, s.mpp, s.rot = W, H, float(cx), float(cy), float(mpp), float(rot)
        c, n = math.cos(rot), math.sin(rot)
        s.A = np.array([[c, -n], [n, c]]) / s.mpp
        s.b = np.array([W / 2.0, H / 2.0]) - s.A @ np.array([s.cx, s.cy])
        s.Ai = np.linalg.inv(s.A)
        cn = np.array([[0, 0], [W, 0], [W, H], [0, H]], float)
        wc = (cn - s.b) @ s.Ai.T
        s.box = (wc[:, 0].min(), wc[:, 1].min(), wc[:, 0].max(), wc[:, 1].max())
    def to_px(s, P): return np.asarray(P, np.float64) @ s.A.T + s.b
    def to_px16(s, P):
        Q = np.round((np.asarray(P, np.float64) @ s.A.T + s.b) * SC)
        return np.clip(Q, -2 ** 30, 2 ** 30).astype(np.int32)
    def to_world(s, S): return (np.asarray(S, np.float64) - s.b) @ s.Ai.T
    def grid(s, step=1):
        """world coordinates (X, Y) of the pixel centres of a frame sampled every `step` pixels"""
        xs = np.arange(0, s.W, step) + step / 2.0; ys = np.arange(0, s.H, step) + step / 2.0
        PX, PY = np.meshgrid(xs, ys)
        X = s.Ai[0, 0] * (PX - s.b[0]) + s.Ai[0, 1] * (PY - s.b[1])
        Y = s.Ai[1, 0] * (PX - s.b[0]) + s.Ai[1, 1] * (PY - s.b[1])
        return X, Y
    def sees(s, x0, y0, x1, y1, m=0.0):
        b = s.box; return not (x1 < b[0] - m or x0 > b[2] + m or y1 < b[1] - m or y0 > b[3] + m)
