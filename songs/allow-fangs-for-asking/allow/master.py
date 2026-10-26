"""Plate 1, the master: her bedroom window at midnight, rebuilt as a lit set.

The plate is the candle-lit state. The engine separates it into
  glass (four panes, with the arch)  ->  rain, condensation, writing, reflections (glass.py)
  candle (body, holder, flame)       ->  procedural flame that flickers and leans, relighting the room with it
  phone (on the sill)                ->  a screen that wakes up and lights the sill, glass, lace and candle
  everything else                    ->  relit between candlelight and cold night light as the song goes on
Geometry is measured in plate pixels (1672 x 941) and scaled to the output.
"""
import math
from functools import lru_cache
import numpy as np, cv2
from .fx import (F32, to_lin, luma, rgb, blur, fast_blur, fbm2, n1, sstep, clamp, lerp, paste_add)
from .glass import Glass
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PW, PH = 1672, 941

# ---------------------------------------------------------------- measured geometry (plate px)
ARCH_C, ARCH_R = (852.5, 237.2), 282.9
PANES = [  # x0, x1, y0 (None = arch), y1
    (632, 821, None, 145), (888, 1073, None, 145),
    (630, 821, 160, 697), (888, 1076, 160, 697),
]
CANDLE_BODY = (652, 617, 690, 702)          # x0, y0, x1, y1
FLAME = (671.0, 619.0, 4.6, 34.0)           # base x, base y, half-width, height
HOLDER = [(640, 700), (704, 700), (700, 712), (684, 718), (676, 760), (711, 772), (712, 783), (630, 783), (632, 772), (666, 760), (660, 718), (644, 712)]
PHONE = [(724, 766), (838, 769), (842, 778), (720, 776)]   # top face, face-up, screen dark at start
CLOCK = (1555, 560, 1650, 735)
CLOCK_FACE = (1600.5, 645.0, 37.0)


def arch_y(x):
    cx, cy = ARCH_C
    d = ARCH_R ** 2 - (x - cx) ** 2
    return cy - math.sqrt(max(d, 0.0))


def pane_polys():
    polys = []
    for x0, x1, y0, y1 in PANES:
        if y0 is None:
            xs = np.linspace(x0, x1, 40)
            top = [(x, max(-20.0, arch_y(x))) for x in xs]
            polys.append(top + [(x1, y1), (x0, y1)])
        else:
            polys.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    return polys


class Master:
    def __init__(self, W=3840, H=2160, seed=11):
        self.W, self.H = W, H
        s = max(W / PW, H / PH); self.s = s          # cover the frame (landscape or the vertical cuts)
        from .kit import plate_pixels
        pw2, ph2 = int(round(PW * s)), int(round(PH * s))
        up = plate_pixels(1, pw2, ph2)
        self.ox = int(min(max(0, 852 * s - W / 2), pw2 - W))      # vertical frames stay centred on the window
        self.oy = (ph2 - H) // 2
        up = up[self.oy:self.oy + H, self.ox:self.ox + W]
        L = to_lin(up)
        P = lambda x, y: (x * s - self.ox, y * s - self.oy)
        self.P = P
        # ---------------- masks
        gm = np.zeros((H, W), np.uint8)
        for poly in pane_polys():
            pts = np.array([P(x, y) for x, y in poly], np.float32)
            cv2.fillPoly(gm, [np.round(pts * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        cand = np.zeros((H, W), np.uint8)
        x0, y0, x1, y1 = CANDLE_BODY
        cv2.rectangle(cand, tuple(map(int, P(x0, y0))), tuple(map(int, P(x1, y1))), 255, -1)
        hold = np.array([P(x, y) for x, y in HOLDER], np.float32)
        cv2.fillPoly(cand, [np.round(hold).astype(np.int32)], 255, cv2.LINE_AA)
        # flame + its baked halo are painted out and re-rendered
        fx, fy, fw, fh = FLAME
        flame_m = np.zeros((H, W), np.uint8)
        cv2.ellipse(flame_m, tuple(map(int, P(fx, fy - fh * 0.45))), (int(fw * 2.6 * s), int(fh * 0.72 * s)), 0, 0, 360, 255, -1)
        self.cand_m = cand.astype(F32) / 255
        glass = gm.astype(F32) / 255 * (1 - blur(self.cand_m, 0.7))
        self.gm = np.clip(glass, 0, 1)
        # paint out the baked flame (inpaint in sRGB at a working size, then back)
        k = 2
        small = cv2.resize(up, (W // k, H // k), interpolation=cv2.INTER_AREA)
        fm_small = cv2.resize(flame_m, (W // k, H // k), interpolation=cv2.INTER_NEAREST)
        inp = cv2.inpaint(small, fm_small, 6, cv2.INPAINT_TELEA)
        inp_up = to_lin(cv2.resize(inp, (W, H), interpolation=cv2.INTER_CUBIC))
        fmf = blur(flame_m.astype(F32) / 255, 2 * s)[..., None]
        self.base = (L * (1 - fmf) + inp_up * fmf).astype(F32)
        # ---------------- lighting decomposition
        Y = luma(self.base)
        illum = np.exp(fast_blur(np.log(Y + 2e-3), 10 * s)).astype(F32)
        detail = self.base / (illum[..., None] + 2e-3)
        dl = luma(detail)[..., None]
        self.detail_n = (detail * 0.3 + dl * 0.7).astype(F32)        # warm cast removed: albedo-ish
        self.illum = illum
        # light positions (output px)
        self.flame_xy = P(fx, fy - fh * 0.42)
        ph_pts = np.array([P(x, y) for x, y in PHONE], np.float32)
        self.phone_pts = ph_pts
        self.phone_xy = ph_pts.mean(0)
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        # candle falloff (for flicker and for draining)
        d = np.sqrt((xx - self.flame_xy[0]) ** 2 + ((yy - self.flame_xy[1]) * 1.15) ** 2) / (s * 160)
        self.cfall = (1.0 / (1.0 + d * d)).astype(F32)
        # phone light: a glow pooled on the sill and thrown up the glass, lace and candle
        dp = np.sqrt(((xx - self.phone_xy[0]) / 1.0) ** 2 + ((yy - self.phone_xy[1]) * 1.6) ** 2) / (s * 85)
        up_bias = np.clip(1.0 - (yy - self.phone_xy[1]) / (s * 30), 0.15, 1.0)
        self.pfall = (up_bias / (1.0 + dp * dp * 1.4)).astype(F32)
        dw = np.sqrt((xx - self.phone_xy[0]) ** 2 + ((yy - self.phone_xy[1]) * 1.2) ** 2) / (s * 420)
        self.pwide = (1.0 / (1.0 + dw * dw)).astype(F32)
        # night light through the window: cold, strongest near the glass and on the lace
        win = fast_blur(self.gm, 120 * s)
        self.nightmap = (0.06 + 0.9 * win / max(1e-3, win.max())).astype(F32)
        # room depth proxy for draining the warmth toward the window
        cx_w = P(852, 420)
        self.rdist = (np.sqrt(((xx - cx_w[0]) / W) ** 2 + ((yy - cx_w[1]) / H) ** 2)).astype(F32)
        # glass + its behaviour
        self.glass = Glass(self.gm, s, seed=seed, density=1.0, big_drops=34, drop_scale=1.25)
        # what is behind the glass: the plate itself (street, lamp, houses)
        self.behind = self.base
        # phone screen quad as a mask
        sm = np.zeros((H, W), np.uint8)
        cv2.fillPoly(sm, [np.round(ph_pts * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        self.screen_m = blur(sm.astype(F32) / 255, 0.6)
        # face-down phone: light seeps from under its edges onto the sill
        slab = np.zeros((H, W), np.uint8)
        body = ph_pts.copy(); body[2:, 1] += 3.2 * s          # include its thickness
        cv2.fillPoly(slab, [np.round(body * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        slab = slab.astype(F32) / 255
        ring = np.clip(blur(slab, 2.2 * s) * 1.8 - slab * 1.6, 0, 1)
        ring = ring * np.clip((yy - (self.phone_xy[1] - 4 * s)) / (6 * s), 0.25, 1.0)   # strongest where it meets the sill
        self.leak = ring.astype(F32)
        self.slab = slab
        self.leak_glow = (fast_blur(ring, 10 * s) * 2.5 + fast_blur(ring, 40 * s) * 5.0).astype(F32)
        self.screen_grad = (0.55 + 0.45 * np.clip((xx - ph_pts[:, 0].min()) / max(1, np.ptp(ph_pts[:, 0])), 0, 1)).astype(F32)
        self.yy, self.xx = yy, xx

    # ------------------------------------------------------------- flame
    def flame(self, t, strength, lean, gutter=0.0):
        """Additive linear RGB of the flame and its halo. lean: -1..1 (positive = toward the glass/right-up)."""
        H, W, s = self.H, self.W, self.s
        fx, fy, fw, fh = FLAME
        bx, by = self.P(fx, fy)
        flick = 1.0 + 0.10 * n1(t, 3, 7.0) + 0.05 * n1(t, 5, 19.0)
        hgt = fh * s * (0.92 + 0.12 * n1(t, 8, 3.0)) * (0.55 + 0.45 * strength) * (1 - 0.45 * gutter)
        wid = fw * s * (1.0 + 0.08 * n1(t, 9, 5.0))
        sway = (0.10 * n1(t, 11, 1.3) + 0.06 * n1(t, 12, 4.0) + 0.55 * lean) * hgt
        pad = int(hgt * 1.4)
        x0, y0 = int(bx - pad), int(by - hgt - pad)
        x1, y1 = int(bx + pad), int(by + pad * 0.4)
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(F32)
        v = np.clip((by - ys) / hgt, -0.3, 1.4)                     # 0 at wick, 1 at tip
        bend = sway * np.clip(v, 0, 1) ** 1.7
        u = (xs - bx - bend) / wid
        # teardrop profile: widest at ~0.25 of the height
        prof = np.where(v < 0.25, np.sqrt(np.clip(v / 0.25, 0, 1)) * (0.75 + 0.25 * v / 0.25),
                        np.clip(1 - (v - 0.25) / 0.75, 0, 1) ** 0.85)
        r = np.abs(u) / np.maximum(prof, 1e-3)
        body = np.clip(1 - r, 0, 1) ** 0.6 * (v > -0.05) * (v < 1.0)
        body = blur(body.astype(F32), 0.6 * s)
        core = np.clip(1 - r * 1.6, 0, 1) * np.clip(1 - np.abs(v - 0.35) * 2.2, 0, 1)
        blue_base = np.exp(-((v + 0.02) / 0.09) ** 2) * np.clip(1 - r, 0, 1)
        col = (body[..., None] * rgb(1.0, 0.62, 0.22) * 3.2 + core[..., None] * rgb(1.0, 0.92, 0.75) * 5.5
               - blue_base[..., None] * rgb(0.6, 0.4, 0.1) * 1.5 + blue_base[..., None] * rgb(0.05, 0.12, 0.45) * 1.2)
        col = np.clip(col, 0, None) * flick * strength
        out = np.zeros((H, W, 3), F32)
        paste_add(out, col.astype(F32), x0, y0)
        # halo
        hx, hy = bx + sway * 0.5, by - hgt * 0.5
        d2 = ((self.xx - hx) ** 2 + ((self.yy - hy) * 0.8) ** 2) / (s * 18) ** 2
        halo = (np.exp(-d2) * 0.35 + 0.12 / (1 + d2 * 0.4)) * strength * flick
        out += halo[..., None] * rgb(1.0, 0.55, 0.2)
        return out

    # ------------------------------------------------------------- main
    def render(self, t, st):
        """st keys: warm (candle strength 0..1), night (cold fill 0..1), drain (0..1), phone (screen 0..1),
        pulse (extra phone flare), lean, gutter, fog, extra_fog, clear, taps, frost, refl, refl_amt, flow."""
        s = self.s
        warm = st.get('warm', 1.0); night = st.get('night', 0.0); phone = st.get('phone', 0.0)
        pulse = st.get('pulse', 0.0); drain = st.get('drain', 0.0)
        flick = 0.07 * n1(t, 3, 7.0) + 0.04 * n1(t, 5, 19.0)
        near = st.get('warm_near', warm)                # candle light close to the flame
        far = st.get('warm_far', warm)                  # candle light reaching the rest of the room
        lvl = phone * (1.0 + pulse)
        if not hasattr(self, '_pre'):
            # every light is linear in its strength: precompute each light's contribution once
            C = self.cfall[..., None]; keep = (1 - self.slab)[..., None]
            self._pre = dict(
                base=self.base, bc=self.base * C, bc2=self.base * C * C,
                night=(self.detail_n * (self.nightmap * 0.30 + 0.012)[..., None] * rgb(0.22, 0.46, 0.88)).astype(F32),
                pf=(self.detail_n * (self.pfall * 0.65)[..., None] * rgb(0.20, 0.50, 1.0) * keep).astype(F32),
                pw=(self.detail_n * (self.pwide * 0.09)[..., None] * rgb(0.20, 0.50, 1.0) * keep).astype(F32))
        q = self._pre
        if drain > 0:   # (rare) the slow path: warmth pulled toward the window
            C = self.cfall
            wmap = (near * C + far * (1 - C)) * (1.0 + flick * C * 2.2)
            wmap = wmap * (1 - drain * np.clip(self.rdist * 3.2 - 0.25, 0, 1))
            img = self.base * wmap[..., None]
        else:
            # (near*C + far*(1-C)) * (1 + 2.2*flick*C), expanded
            img = q['base'] * far
            img += q['bc'] * (near - far + 2.2 * flick * far)
            img += q['bc2'] * (2.2 * flick * (near - far))
        if night > 0: img += q['night'] * night
        if lvl > 0:
            img += q['pf'] * lvl
            img += q['pw'] * (lvl * st.get('phone_fill', 0.5))
        # glass
        fog_glow = (self.cfall * 0.05 * warm)[..., None] * rgb(1.0, 0.6, 0.3) + \
                   (self.pfall * 0.14 * lvl)[..., None] * rgb(0.25, 0.5, 1.0) + \
                   (self.nightmap * 0.006 * (0.4 + night))[..., None] * rgb(0.4, 0.55, 0.8)
        drop_light = (self.cfall * 0.9 * warm)[..., None] * rgb(1.0, 0.7, 0.4) + (self.pfall * 0.9 * lvl)[..., None] * rgb(0.5, 0.7, 1.0) + 0.04
        behind = self.behind * (st.get('street', 1.0))
        g, (y0, y1, x0, x1) = self.glass.render(behind, t, fog_glow=fog_glow, fog_amt=st.get('fog', 1.0),
                                                extra_fog=st.get('extra_fog'), clear=st.get('clear'),
                                                flow=st.get('flow', 1.0), refl=st.get('refl'), refl_amt=st.get('refl_amt', 0.0),
                                                tap_rings=st.get('taps', ()), drop_light=drop_light, frost=st.get('frost'))
        m = self.glass.m[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + g * m
        # the phone screen itself
        if phone > 0:
            on = phone ** 1.3 * (1.0 + pulse)
            img = img + (self.leak * 1.6 * on)[..., None] * rgb(0.10, 0.34, 1.0)
            img = img + (self.leak_glow * 0.22 * on)[..., None] * rgb(0.10, 0.30, 1.0)
        # flame
        img = img + self.flame(t, warm * st.get('flame', 1.0), st.get('lean', 0.0), st.get('gutter', 0.0))
        return img
