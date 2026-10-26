"""The bridge: the first time the camera leaves her room. Plate 15 (the street from her window).

A small point of cold light leaves her house and drifts down through the rain, along the wet street, to the warm
bay window on the right (her sister's). The camera follows: a slow push from the wide street into that window."""
import math
import numpy as np, cv2
from .fx import F32, rgb, blur, fast_blur, n1, sstep, clamp, ease_io, luma
from .kit import load_plate, grid

# the light's path in plate px (from top-left, out of frame where her window is, down to the sister's window)
PATH = [(-60, 120), (180, 300), (420, 520), (640, 640), (900, 560), (1080, 430), (1215, 300)]
SISTER_WIN = (1220, 250)


def _bez(pts, u):
    """Catmull-Rom through the points, u in 0..1."""
    n = len(pts) - 1; f = clamp(u) * n; i = min(int(f), n - 1); t = f - i
    p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(n, i + 2)]
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                        + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1))


class Street:
    def __init__(self, W, H, seed=151):
        self.W, self.H = W, H
        L, s, (ox, oy), up = load_plate(15, W, H)
        self.s = s; self.P = lambda x, y: (x * s - ox, y * s - oy); self.base = L
        self.yy, self.xx = grid(H, W)
        self.rng = np.random.RandomState(seed)

    def render(self, t, st):
        s = self.s; img = self.base.copy()
        u = st.get('travel', 0.0)
        # rain streaks in the light
        rng = np.random.RandomState(int(t * 30) % 100000)
        rain = np.zeros((self.H, self.W), F32)
        for _ in range(int(700 * self.W / 1920)):
            x = rng.uniform(0, self.W); y = rng.uniform(0, self.H); Lr = rng.uniform(14, 34) * s
            cv2.line(rain, (int(x), int(y)), (int(x - Lr * 0.1), int(y + Lr)), float(rng.uniform(0.2, 1.0)), 1, cv2.LINE_AA)
        light = fast_blur(np.clip(luma(self.base) - 0.06, 0, None), 25 * s)
        img = img + (blur(rain, 0.5 * s) * (0.003 + light * 0.3))[..., None] * rgb(0.95, 0.85, 0.7)
        # the travelling point of light: small, cold, quiet; a faint wake on the wet stones
        if 0 < u < 1.05:
            px, py = self.P(*_bez(PATH, min(u, 1.0)))
            r2 = ((self.xx - px) ** 2 + (self.yy - py) ** 2) / (s * 8.0) ** 2
            core = np.exp(-r2) * 2.2 + 0.16 / (1 + r2 * 0.06)
            fade = 1 - sstep(0.96, 1.05, u)
            img = img + (core * fade)[..., None] * rgb(0.30, 0.55, 1.0)
            # reflection on the street below it
            ry = py + (self.H * 0.05)
            rr = ((self.xx - px) / (s * 6)) ** 2 + ((self.yy - ry) / (s * 30)) ** 2
            img = img + (np.exp(-rr) * 0.10 * fade)[..., None] * rgb(0.3, 0.55, 1.0)
        # when it reaches her window, that window flickers cold for an instant
        hit = st.get('arrive', 0.0)
        if hit > 0:
            wx, wy = self.P(*SISTER_WIN)
            win = np.exp(-(((self.xx - wx) / (s * 60)) ** 2 + ((self.yy - wy) / (s * 95)) ** 2))
            img = img + (win * hit * 0.12)[..., None] * rgb(0.25, 0.5, 1.0)
        return img
