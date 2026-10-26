"""Plate 2: over her shoulder at the sill. He waits outside, beyond the rain.

Layers: the room plate (her, candle, lace, phone in her hand) / the glass (two panes) / what is behind the glass:
the street plus his silhouette (plate 7), defocused, dark against the lamp, with a thin warm rim from it.
"""
import numpy as np, cv2
from .fx import F32, rgb, blur, fast_blur, n1, sstep, luma, paste_add
from .kit import load_plate, grid, flame, paint_out, silhouette
from .glass import Glass

PANES2 = [[(630, 18), (865, 18), (865, 663), (630, 663)], [(960, 0), (1222, 0), (1222, 690), (960, 690)]]
CANDLE2 = (627, 516, 691, 652)
HOLDER2 = (622, 648, 700, 740)
FLAME2 = (658.0, 518.0, 4.6, 46.0)


class Shoulder:
    def __init__(self, W, H, seed=21):
        self.W, self.H = W, H
        L, s, (ox, oy), up = load_plate(2, W, H)
        self.s = s
        P = lambda x, y: (x * s - ox, y * s - oy); self.P = P
        gm = np.zeros((H, W), np.uint8)
        for poly in PANES2:
            cv2.fillPoly(gm, [np.round(np.array([P(*p) for p in poly], np.float32) * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        cm = np.zeros((H, W), np.uint8)
        for (a, b, c, d) in (CANDLE2, HOLDER2):
            cv2.rectangle(cm, tuple(map(int, P(a, b))), tuple(map(int, P(c, d))), 255, -1)
        self.gm = (gm.astype(F32) / 255) * (1 - blur(cm.astype(F32) / 255, 0.8))
        fx_, fy_, fw, fh = FLAME2
        fmask = np.zeros((H, W), np.uint8)
        cv2.ellipse(fmask, tuple(map(int, P(fx_, fy_ - fh * 0.45))), (int(fw * 2.8 * s), int(fh * 0.75 * s)), 0, 0, 360, 255, -1)
        patched = paint_out(up, fmask)
        fmf = blur(fmask.astype(F32) / 255, 2 * s)[..., None]
        self.base = (L * (1 - fmf) + patched * fmf).astype(F32)
        self.flame_pos = (P(fx_, fy_), fw * s, fh * s)
        # the blue the phone already throws on her face and hand, so it can pulse
        r, g, b = self.base[..., 0], self.base[..., 1], self.base[..., 2]
        self.blue = np.clip(b - r * 0.9, 0, None)[..., None] * rgb(0.25, 0.55, 1.0) * 1.0
        yy, xx = grid(H, W); self.yy, self.xx = yy, xx
        fxo, fyo = P(fx_, fy_ - 20)
        d = np.sqrt((xx - fxo) ** 2 + (yy - fyo) ** 2) / (s * 170)
        self.cfall = (1 / (1 + d * d)).astype(F32)
        self.glass = Glass(self.gm, s, seed=seed, density=0.9, big_drops=26, drop_scale=1.3, fog_base=0.16)
        # his silhouette, sized to the window, placed outside the right pane
        a = silhouette()
        self.sil_src = a

    def man_layer(self, presence, closeness, t):
        """(alpha, rim) full-frame for the silhouette outside. closeness 0..1 moves him nearer the glass."""
        H, W, s = self.H, self.W, self.s
        a = self.sil_src
        sc_plate = 0.62 + 0.30 * closeness                     # figure height relative to plate 941
        hh = int(941 * s * sc_plate); ww = int(a.shape[1] * hh / a.shape[0])
        A = cv2.resize(a, (ww, hh), interpolation=cv2.INTER_AREA)
        sway = 2.0 * s * n1(t, 41, 0.25)
        cx, top = self.P(1112 + 10 * closeness, 112 - 60 * closeness)
        defocus = (4.2 - 2.0 * closeness) * s
        A = blur(A, defocus)
        full = np.zeros((H, W), F32); paste_add(full, A, cx - ww / 2 + sway, top)
        rim = np.clip(full - blur(full, 3 * s), 0, 1) * 2.0
        return full * presence, rim * presence

    def render(self, t, st):
        s = self.s
        warm = st.get('warm', 1.0); phone = st.get('phone', 1.0); pulse = st.get('pulse', 0.0)
        flick = 0.06 * n1(t, 3, 7.0) + 0.035 * n1(t, 5, 19.0)
        img = self.base * (warm * (1 + flick * self.cfall * 2.0))[..., None]
        img = img + self.blue * (phone * (1 + pulse) - 1.0)
        # behind the glass: the street, then him
        behind = self.base.copy()
        pres = st.get('presence', 0.0)
        if pres > 0:
            A, rim = self.man_layer(pres, st.get('closeness', 0.0), t)
            dark = rgb(0.006, 0.005, 0.006)
            behind = behind * (1 - A[..., None]) + A[..., None] * dark
            lx, ly = self.P(1165, 300)
            lamp = np.exp(-(((self.xx - lx) ** 2 + (self.yy - ly) ** 2) / (self.s * 70) ** 2))
            behind = behind + (blur(rim, 1.5 * self.s) * 0.6 * lamp)[..., None] * rgb(1.0, 0.62, 0.3)
            # the lamp's glow spills around him (the lamp itself is behind his shoulder)
            behind = behind + (fast_blur(A, 8 * self.s) * lamp * 0.35 * (1 - A))[..., None] * rgb(1.0, 0.6, 0.28)
        fog_glow = (self.cfall * 0.045 * warm)[..., None] * rgb(1.0, 0.6, 0.3) + 0.002
        drop_light = (self.cfall * 0.8 * warm)[..., None] * rgb(1.0, 0.7, 0.4) + 0.05
        g, (y0, y1, x0, x1) = self.glass.render(behind, t, fog_glow=fog_glow, fog_amt=st.get('fog', 1.0),
                                                tap_rings=st.get('taps', ()), drop_light=drop_light,
                                                extra_fog=st.get('extra_fog'), clear=st.get('clear'))
        m = self.glass.m[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + g * m
        (bx, by), fw, fh = self.flame_pos
        img = img + flame(self.H, self.W, t, bx, by, fw, fh, s, strength=warm * st.get('flame', 1.0), lean=st.get('lean', 0.0), seed=4)
        return img
