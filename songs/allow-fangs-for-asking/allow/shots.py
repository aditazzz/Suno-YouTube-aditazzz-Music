"""Generic close-up / insert shots built on one plate each (plates 10-17).

A PlateShot = plate + optional rain on a glass region + flickering candle/lamp light + a phone screen mapped with
system UI + a warm->cold grade. Specific beats (bite badges, the blue pulse, the sister's room) are small extras."""
import math
import numpy as np, cv2
from .fx import F32, rgb, blur, fast_blur, n1, sstep, clamp, ease_io, ease_out, luma, paste_add, to_lin
from .kit import load_plate, grid, flame
from .glass import Glass
from . import ui as UI


def cold_grade(img, amt, keep_emissive=0.6):
    """Warm candle look -> cold screen look. Bright warm sources survive a little (they are lights, not surfaces)."""
    if amt <= 0: return img
    Y = luma(img)[..., None]
    cool = Y * rgb(0.30, 0.56, 1.0) * 1.15
    hot = np.clip((Y - 0.35) / 0.4, 0, 1) * keep_emissive
    k = amt * (1 - hot)
    return img * (1 - k) + cool * k


class PlateShot:
    def __init__(self, W, H, plate, glass_polys=(), flames=(), lamps=(), screen=None, seed=81, rain=0.6, drops=1.6):
        self.W, self.H = W, H
        L, s, (ox, oy), up = load_plate(plate, W, H)
        self.s = s; self.P = P = (lambda x, y: (x * s - ox, y * s - oy)); self.base = L
        self.yy, self.xx = grid(H, W)
        self.glass = None
        if glass_polys:
            gm = np.zeros((H, W), np.uint8)
            for poly in glass_polys:
                cv2.fillPoly(gm, [np.round(np.array([P(*p) for p in poly], np.float32)).astype(np.int32)], 255, cv2.LINE_AA)
            self.glass = Glass(gm.astype(F32) / 255, s, seed=seed, density=rain, big_drops=14, drop_scale=drops, fog_base=0.0)
        self.flames = [(P(x, y), w * s, h * s) for (x, y, w, h) in flames]
        self.lamps = []
        for (x, y, r) in lamps:
            cx, cy = P(x, y); d2 = ((self.xx - cx) ** 2 + (self.yy - cy) ** 2) / (r * s) ** 2
            self.lamps.append((1 / (1 + d2)).astype(F32))
        self.screen = None
        if screen is not None:
            self.screen = np.float32([P(*p) for p in screen])
            # the real screen's shape (rounded corners, perspective) from the plate itself: its bright blank glow
            r_, g_, b_ = L[..., 0], L[..., 1], L[..., 2]
            sm = ((b_ > 0.35) & (b_ > r_ * 1.25)).astype(np.uint8)
            n, lab, st_, _ = cv2.connectedComponentsWithStats(sm)
            sm = (lab == 1 + int(np.argmax(st_[1:, 4]))).astype(np.uint8)
            sm = cv2.morphologyEx(sm, cv2.MORPH_CLOSE, np.ones((int(9 * s),) * 2, np.uint8))
            self.screen_m = np.clip(blur(cv2.dilate(sm, np.ones((3, 3), np.uint8)).astype(F32), 0.8 * s), 0, 1)
            self.screen_glow = fast_blur(self.screen_m, 30 * s)

    def render(self, t, st):
        img = self.base * st.get('expo', 1.0)
        for i, L in enumerate(self.lamps):
            fl = 0.08 * n1(t, 90 + i, 6.0) + 0.04 * n1(t, 95 + i, 17.0)
            img = img * (1 + fl * L * 2.0)[..., None]
        if self.screen is not None and st.get('ui') is not None:
            scr = st['ui']
            ex = st.get('screen_expo', 1.0)
            img = UI.map_to(img, scr, self.screen, glow=1.0, exposure=1.1 * ex, mask=self.screen_m)
            img = img + (self.screen_glow * 0.10 * ex)[..., None] * rgb(0.35, 0.55, 1.0)
        img = cold_grade(img, st.get('cold', 0.0))
        if self.glass is not None:
            g, (y0, y1, x0, x1) = self.glass.render(img, t, fog_amt=0.0, tap_rings=st.get('taps', ()),
                                                    drop_light=rgb(1.0, 0.75, 0.5) * 0.25 * (1 - st.get('cold', 0)) + rgb(0.3, 0.5, 1.0) * 0.25 * st.get('cold', 0) + 0.03)
            m = self.glass.m[..., None]
            img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + g * m
        for (pos, fw, fh) in self.flames:
            img = img + flame(self.H, self.W, t, pos[0], pos[1], fw, fh, self.s, strength=st.get('flame', 1.0), seed=int(pos[0]) % 13)
        return img


# ---------------------------------------------------------------- the shots
def sill(W, H):      # plate 10: crucifix + garlic, rain behind
    return PlateShot(W, H, 10, glass_polys=[[(660, 0), (1536, 0), (1536, 345), (660, 345)]], lamps=[(40, 120, 260)], seed=101)


def bed(W, H):       # plate 11: her in bed, phone-lit
    return PlateShot(W, H, 11, lamps=[], seed=111)


def phone_sill(W, H):  # plate 13: phone face-up on the sill, blank screen
    return PlateShot(W, H, 13, glass_polys=[[(745, 0), (1536, 0), (1536, 330), (745, 330)]], lamps=[(410, 40, 220)],
                     screen=[(826, 548), (1436, 757), (1048, 870), (484, 619)], seed=131)   # far edge = top of the UI (landscape)


def phone_hand(W, H):  # plate 14: phone in her hand
    return PlateShot(W, H, 14, lamps=[(760, 60, 200)], screen=[(1017, 177), (1254, 225), (1095, 819), (847, 739)], seed=141)


def sister_room(W, H):  # plate 16: from inside her sister's room, she is outside the glass
    return PlateShot(W, H, 16, glass_polys=[[(662, 0), (1165, 0), (1165, 735), (662, 735)]], lamps=[(250, 300, 220)],
                     seed=161, rain=0.7, drops=1.4)


class Neck(PlateShot):
    """Plate 12: the side of her neck. Two red notification badges surface like puncture marks."""
    def __init__(self, W, H):
        super().__init__(W, H, 12, seed=121)
        self.marks = [self.P(905, 640), self.P(955, 668)]

    def render(self, t, st):
        img = super().render(t, st)
        b = st.get('badges', 0.0)
        if b > 0:
            s = self.s
            for k, (cx, cy) in enumerate(self.marks):
                r = 9.5 * s * (0.6 + 0.4 * ease_out(b * 1.5 - k * 0.25))
                d = np.sqrt((self.xx - cx) ** 2 + (self.yy - cy) ** 2)
                disc = np.clip((r - d) / (1.2 * s), 0, 1) * clamp(b * 1.6 - k * 0.3)
                glow = np.exp(-(d / (r * 2.2)) ** 2) * 0.35 * clamp(b * 1.6 - k * 0.3)
                img = img * (1 - disc[..., None]) + disc[..., None] * rgb(0.62, 0.02, 0.02) + glow[..., None] * rgb(0.5, 0.0, 0.0) * 0.4
        return img


def face(W, H):      # plate 17: her face behind her sister's window, hand on the glass
    return PlateShot(W, H, 17, glass_polys=[[(355, 0), (1515, 0), (1515, 905), (355, 905)]], seed=171, rain=0.5, drops=1.8)
