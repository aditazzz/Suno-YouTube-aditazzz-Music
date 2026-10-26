"""The other approval shots: the mirror (plate 3), her sister's window (plates 4 + 5), the city (plate 6)."""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw
from .fx import F32, rgb, blur, fast_blur, fbm2, n1, sstep, luma, paste_add, font, to_lin
from .kit import load_plate, grid, flame, paint_out, _read
from .glass import Glass


# ====================================================================== mirror
class Mirror:
    """Her shoulder in front of the gilded mirror. The mirror shows the room and not her (as generated)."""
    def __init__(self, W, H):
        self.W, self.H = W, H
        L, s, (ox, oy), up = load_plate(3, W, H)
        self.s = s; P = lambda x, y: (x * s - ox, y * s - oy); self.P = P
        fm = np.zeros((H, W), np.uint8)
        cv2.ellipse(fm, tuple(map(int, P(977, 449))), (int(5 * s), int(12 * s)), 0, 0, 360, 255, -1)
        patched = paint_out(up, fm, radius=4)
        fmf = blur(fm.astype(F32) / 255, 1.2 * s)[..., None]
        self.base = (L * (1 - fmf) + patched * fmf).astype(F32)
        Y = luma(self.base)
        illum = np.exp(fast_blur(np.log(Y + 2e-3), 10 * s)).astype(F32)
        d = self.base / (illum[..., None] + 2e-3); self.detail_n = (d * 0.3 + luma(d)[..., None] * 0.7).astype(F32)
        yy, xx = grid(H, W)
        lx, ly = P(10, 215)                       # soft foreground candle at the left edge
        dd = np.sqrt((xx - lx) ** 2 + (yy - ly) ** 2) / (s * 260)
        self.lfall = (1 / (1 + dd * dd)).astype(F32)
        self.lcore = np.exp(-(((xx - lx) / (s * 30)) ** 2 + ((yy - P(10, 240)[1]) / (s * 80)) ** 2)).astype(F32)
        # phone glow seen in the mirror
        r, g, b = self.base[..., 0], self.base[..., 1], self.base[..., 2]
        self.blue = (np.clip(b - r * 1.2, 0, None) * (yy > P(0, 470)[1]) * (yy < P(0, 540)[1]))[..., None]
        self.fpos = (P(977.5, 458.5), 1.7 * s, 17 * s)
        self.night = fast_blur(((xx > P(880, 0)[0]) & (xx < P(1460, 0)[0])).astype(F32), 200 * s)

    def render(self, t, st):
        warm = st.get('warm', 1.0); cold = st.get('cold', 0.0); phone = st.get('phone', 1.0)
        fl = 1 + 0.08 * n1(t, 21, 6.0) + 0.04 * n1(t, 22, 17.0)
        img = self.base * (warm * (1 + (fl - 1) * self.lfall * 1.5))[..., None]
        img = img + self.base * (self.lcore * (fl - 1) * 2.0)[..., None]
        if cold > 0:
            img = img + self.detail_n * (0.018 + 0.03 * self.night)[..., None] * rgb(0.22, 0.45, 0.9) * cold
        img = img + self.base * self.blue * 3.0 * (phone * (1 + 0.25 * n1(t, 23, 0.7)) - 1)
        (bx, by), fw, fh = self.fpos
        img = img + flame(self.H, self.W, t, bx, by, fw, fh, self.s, strength=warm * 0.8, seed=9, halo=0.6)
        return img


# ====================================================================== sister's window
PANES5 = [[(592, 145), (955, 98), (955, 652), (592, 600)], [(1042, 62), (1640, 12), (1640, 762), (1042, 672)]]
TIPS5 = [(716, 362), (781, 312), (826, 302), (876, 338), (897, 470)]


class Sister:
    """From outside her sister's window. Plate 4 (empty) / plate 5 (her hand) are aligned, so the hand can rise in."""
    def __init__(self, W, H, seed=31):
        self.W, self.H = W, H
        A, s, (ox, oy), upA = load_plate(4, W, H)
        B, _, _, upB = load_plate(5, W, H)
        self.s = s; P = lambda x, y: (x * s - ox, y * s - oy); self.P = P
        self.A, self.B = A, B
        d = np.abs(upA.astype(F32) - upB.astype(F32)).max(2)
        roi = np.zeros(d.shape, F32)
        x0, y0 = map(int, P(380, 250)); x1, y1 = map(int, P(1010, 941))
        roi[max(0, y0):y1, max(0, x0):x1] = 1
        m = (blur(d, 2 * s) > 26).astype(F32) * roi
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((int(9 * s),) * 2, np.uint8))
        m = cv2.dilate(m, np.ones((int(18 * s),) * 2, np.uint8))
        arm = np.zeros((H, W), np.uint8)
        cv2.fillPoly(arm, [np.round(np.array([P(700, 520), P(800, 560), P(800, 640), P(560, 941), P(300, 941)], np.float32)).astype(np.int32)], 1)
        m = np.maximum(m, arm.astype(F32))
        self.hand = np.clip(blur(m, 14 * s), 0, 1)
        gm = np.zeros((H, W), np.uint8)
        for poly in PANES5:
            cv2.fillPoly(gm, [np.round(np.array([P(*p) for p in poly], np.float32) * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        self.gm = gm.astype(F32) / 255
        self.yy, self.xx = grid(H, W)
        self.glass = Glass(self.gm, s, seed=seed, density=0.7, big_drops=30, drop_scale=1.5, fog_base=0.0)
        self.tips = [P(*p) for p in TIPS5]
        # the lamp inside, for a breathing flicker
        lx, ly = P(1370, 300)
        self.lamp = (1 / (1 + ((self.xx - lx) ** 2 + (self.yy - ly) ** 2) / (s * 220) ** 2)).astype(F32)
        self.word_cache = None

    def writing(self, progress):
        """'Allow?' traced backwards (it is written for the person inside) in the rain on the right pane."""
        s = self.s
        if self.word_cache is None:
            fs = 92 * s
            f = font('CormorantGaramond-MediumItalic.ttf', fs)
            txt = 'Allow?'; tw = int(f.getlength(txt)); asc, desc = f.getmetrics(); pad = int(fs * 0.3)
            im = Image.new('L', (tw + 2 * pad, asc + desc + 2 * pad), 0)
            ImageDraw.Draw(im).text((pad, pad), txt, font=f, fill=255)
            m = np.asarray(im, F32)[:, ::-1] / 255          # mirrored: we are on the wrong side of the glass
            m = cv2.dilate(m, np.ones((max(1, int(2.2 * s)),) * 2, np.uint8))
            h, w = m.shape
            ang = -4.8
            M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
            m = cv2.warpAffine(m, M, (w, h))
            order = np.linspace(1, 0, w, dtype=F32)[None, :] * np.ones((h, 1), F32)   # traced right-to-left from our side
            cx, cy = self.P(1215, 168)
            self.word_cache = (m, order, (cx - w / 2, cy - h / 2))
        m, order, (px, py) = self.word_cache
        rev = np.clip((progress * 1.1 - order) / 0.08, 0, 1) * m
        full = np.zeros((self.H, self.W), F32); paste_add(full, rev, px, py)
        return full

    def render(self, t, st):
        s = self.s
        hand = st.get('hand', 0.0)
        rise = st.get('rise', 1.0)
        w = self.hand * hand
        if rise < 1:
            ymask = np.clip((self.yy - (self.H * (1.05 - rise * 1.0))) / (self.H * 0.25) + 1, 0, 1)
            w = w * ymask
        img = self.A * (1 - w[..., None]) + self.B * w[..., None]
        img = img * (1 + 0.04 * n1(t, 51, 0.6) * self.lamp)[..., None]
        blue_amt = st.get('blue', 0.0)
        if blue_amt > 0:
            Y = luma(img)[..., None]
            cool = Y * rgb(0.32, 0.55, 1.0) * 1.1
            inside = self.gm[..., None] * blue_amt
            img = img * (1 - inside) + cool * inside
        # the writing: rain wiped away in the strokes (clearer, smoother view inside) with a wet rim
        wr = st.get('write', 0.0)
        if wr > 0:
            W_ = self.writing(wr)
            clean = cv2.medianBlur(np.clip(img * 255, 0, 255).astype(np.uint8), 5).astype(F32) / 255
            clean = blur(clean, 1.5 * s)
            stroke = blur(W_, 1.0 * s)[..., None]
            img = img * (1 - stroke) + clean * 0.55 * stroke          # the wiped channel: darker, smooth, no beads
            rim = np.clip(blur(W_, 1.8 * s) * 1.6 - W_, 0, 1)
            img = img + (rim * 0.10)[..., None] * rgb(1.0, 0.72, 0.42)   # the ridge of water at its edges catches the lamp
        # rain on this side of the glass, running
        behind = img
        g, (y0, y1, x0, x1) = self.glass.render(behind, t, fog_amt=0.0, tap_rings=st.get('taps', ()),
                                                drop_light=(self.lamp * 0.6)[..., None] * rgb(1.0, 0.7, 0.4) + 0.05)
        m = self.glass.m[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + g * m
        # cold at her fingertips
        tip = st.get('tips', 0.0) * hand
        if tip > 0:
            for (tx, ty) in self.tips:
                r2 = ((self.xx - tx) ** 2 + (self.yy - ty) ** 2) / (s * 9) ** 2
                img = img + (np.exp(-r2) * 0.05 + 0.012 / (1 + r2 * 0.3))[..., None] * rgb(0.25, 0.55, 1.0) * tip
        return img


# ====================================================================== the city
class City:
    """High over the street. Windows go blue one at a time; one warm light comes on far away."""
    def __init__(self, W, H, seed=41):
        self.W, self.H = W, H
        L, s, (ox, oy), up = load_plate(6, W, H)
        self.s = s; P = lambda x, y: (x * s - ox, y * s - oy); self.P = P
        self.base = L
        src = _read(6).astype(F32) / 255
        r, g, b = src[..., 0], src[..., 1], src[..., 2]
        warm = ((r > 0.32) & (r > b * 1.7) & (g > 0.14)).astype(np.uint8)
        warm[:int(0.17 * src.shape[0])] = 0
        street = np.zeros(warm.shape, np.uint8)
        cv2.fillPoly(street, [np.array([(452, 285), (532, 285), (1065, 700), (1270, 941), (535, 941), (500, 650)], np.int32)], 1)
        warm = warm * (1 - street)
        grp = cv2.dilate(warm, np.ones((7, 7), np.uint8))           # a window's panes flip together
        n, lab, stats, cents = cv2.connectedComponentsWithStats(grp)
        lab = lab * warm                                              # recolour only the lit pixels
        wins = []
        for k in range(1, n):
            a_ = int((lab == k).sum())
            if a_ < 4: continue
            wins.append((k, cents[k], a_))
        self.labels = cv2.resize(lab.astype(np.float32), (int(round(src.shape[1] * s)), int(round(src.shape[0] * s))), interpolation=cv2.INTER_NEAREST)[oy:oy + H, ox:ox + W].astype(np.int32)
        rng = np.random.RandomState(seed)
        # order: spreading outward from the near houses on the right, with some randomness
        def key(w):
            (cx, cy) = w[1]; return -cy * 1.0 + abs(cx - 1100) * 0.6 + rng.uniform(0, 140)
        wins.sort(key=key)
        self.wins = wins
        # the final warm window: a small one far down the street
        far = [w for w in wins if 395 < w[1][0] < 460 and 235 < w[1][1] < 300]
        far.sort(key=lambda w: -w[2])
        self.last = far[0][0] if far else wins[-1][0]
        self.wins = [w for w in self.wins if w[0] != self.last]
        self.yy, self.xx = grid(H, W)
        self.mist = fbm2(H // 4, W // 4, 60, seed, 4)

    def render(self, t, st):
        s = self.s
        spread = st.get('spread', 0.0)        # 0..1 fraction of windows gone blue
        img = self.base.copy()
        n = len(self.wins)
        k_blue = int(spread * n)
        blue_ids = [w[0] for w in self.wins[:k_blue] if w[0] != self.last]
        sel = np.isin(self.labels, blue_ids).astype(F32)
        sel = blur(sel, 0.8 * s)
        if sel.any():
            Y = luma(img)[..., None]
            cool = np.clip(Y, 0, None) * rgb(0.28, 0.55, 1.0) * 1.6
            img = img * (1 - sel[..., None]) + cool * sel[..., None]
            img = img + fast_blur(sel, 6 * s)[..., None] * rgb(0.05, 0.13, 0.35) * 0.35
        # the last warm window: dark until it comes on
        lm = (self.labels == self.last).astype(F32)
        on = st.get('last_on', 0.0)
        img = img * (1 - lm[..., None] * (1 - on) * 0.92)
        img = img + fast_blur(lm, 5 * s)[..., None] * rgb(1.0, 0.6, 0.25) * 0.3 * on
        # rain falling through the lamplight, and drifting mist
        rng = np.random.RandomState(int(t * 30) % 100000)
        rain = np.zeros((self.H, self.W), F32)
        for _ in range(int(900 * (self.W / 1920))):
            x = rng.uniform(0, self.W); y = rng.uniform(0, self.H); L = rng.uniform(10, 26) * s
            cv2.line(rain, (int(x), int(y)), (int(x - L * 0.12), int(y + L)), float(rng.uniform(0.2, 1.0)), 1, cv2.LINE_AA)
        rain = blur(rain, 0.5 * s)
        light = fast_blur(np.clip(luma(self.base) - 0.08, 0, None), 30 * s)
        img = img + (rain * (0.004 + light * 0.25))[..., None] * rgb(0.9, 0.8, 0.7)
        mist = cv2.resize(self.mist, (self.W, self.H))
        drift = np.roll(mist, int(t * 6 * s), axis=1)
        img = img + (drift * (0.006 + 0.01 * (self.yy / self.H)))[..., None] * rgb(0.35, 0.42, 0.55)
        return img
