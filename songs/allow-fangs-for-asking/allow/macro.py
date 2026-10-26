"""Close-ups: the brass bolts (plates 8 / 8b) and the windowpane that opens the film (plate 9)."""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw
from .fx import F32, rgb, blur, fast_blur, fbm2, n1, sstep, clamp, ease_io, ease_out, luma, paste_add, font
from .kit import load_plate, grid, silhouette
from .glass import Glass


# ====================================================================== the bolts
BOLT_BOXES = [(120, 330, 480, 540), (480, 380, 910, 630), (950, 450, 1520, 780)]   # plate px: left, middle, right
BOLT_AXIS = [(1.0, 0.03), (1.0, 0.05), (0.985, 0.17)]                                # slide direction per bolt
BOLT_TRAVEL = [38, 62, 78]                                                           # knob travel 8 -> 8b (plate px)


class Bolts:
    """Plate 8 = all open, plate 8b = all shut (aligned). Each bolt snaps between them on its own cue."""
    def __init__(self, W, H, seed=61):
        self.W, self.H = W, H
        A, s, (ox, oy), upA = load_plate(8, W, H)
        B, _, _, upB = load_plate('8b', W, H)
        self.s = s; P = lambda x, y: (x * s - ox, y * s - oy); self.P = P
        self.A, self.B = A, B
        d = blur(np.abs(upA.astype(F32) - upB.astype(F32)).max(2), 2 * s)
        self.masks = []
        for (x0, y0, x1, y1) in BOLT_BOXES:
            m = np.zeros((H, W), F32)
            a0, b0 = map(int, P(x0, y0)); a1, b1 = map(int, P(x1, y1))
            m[max(0, b0):b1, max(0, a0):a1] = 1
            core = m * (d > 40)
            m = m * (d > 14)
            m = cv2.dilate(m, np.ones((int(14 * s),) * 2, np.uint8))
            self.masks.append(np.clip(blur(m, 6 * s), 0, 1))
            self.cores = getattr(self, 'cores', []) + [np.clip(blur(cv2.dilate(core, np.ones((int(8 * s),) * 2, np.uint8)), 4 * s), 0, 1)]
        self.yy, self.xx = grid(H, W)
        gm = np.zeros((H, W), np.uint8)
        for poly in ([(205, 0), (455, 0), (455, 330), (205, 330)], [(590, 0), (1050, 0), (1050, 345), (590, 345)],
                     [(1180, 0), (1536, 0), (1536, 395), (1180, 395)]):
            cv2.fillPoly(gm, [np.round(np.array([P(*p) for p in poly], np.float32)).astype(np.int32)], 255)
        self.glass = Glass(gm.astype(F32) / 255, s, seed=seed, density=0.25, big_drops=10, drop_scale=1.6, fog_base=0.0)
        cx, cy = P(20, 140)
        dd = np.sqrt((self.xx - cx) ** 2 + (self.yy - cy) ** 2) / (s * 300)
        self.cfall = (1 / (1 + dd * dd)).astype(F32)

    def render(self, t, st):
        """st['bolts']: three values 0 (open) .. 1 (shut); st['moving']: per-bolt 0..1 speed for motion blur."""
        s = self.s
        img = self.A.copy()
        jolt = 0.0
        for k, (m, v) in enumerate(zip(self.masks, st.get('bolts', (0, 0, 0)))):
            if v <= 0: continue
            ax, ay = BOLT_AXIS[k]; L = BOLT_TRAVEL[k] * s
            off = (1 - v) * L                                    # the shut state arrives from the open side
            M = np.float32([[1, 0, -ax * off], [0, 1, -ay * off]])
            Bs = cv2.warpAffine(self.B, M, (self.W, self.H), borderMode=cv2.BORDER_REFLECT)
            mv = st.get('moving', (0, 0, 0))[k]
            if mv > 0.05:                                        # motion blur along the slide
                kl = max(3, int(mv * 0.35 * L)) | 1
                ker = np.zeros((kl, kl), F32); ker[kl // 2, :] = 1.0 / kl
                ang = math.degrees(math.atan2(ay, ax))
                R = cv2.getRotationMatrix2D((kl / 2, kl / 2), -ang, 1.0); ker = cv2.warpAffine(ker, R, (kl, kl)); ker /= ker.sum()
                Bb = cv2.filter2D(Bs, -1, ker)
                c = self.cores[k][..., None] * min(1.0, mv * 1.5)
                Bs = Bs * (1 - c) + Bb * c
            w = (m * min(1.0, v * 3.0))[..., None]
            img = img * (1 - w) + Bs * w
            # a glint runs along the brass as it lands
            g = st.get('glint', (0, 0, 0))[k]
            if g > 0:
                img = img + img * (m * g * 0.6)[..., None]
        fl = 1 + 0.07 * n1(t, 61, 6.5) + 0.03 * n1(t, 62, 17.0)
        img = img * (1 + (fl - 1) * self.cfall * 1.8)[..., None]
        img = img * (1 + st.get('cold', 0.0) * 0)                # (blue arrives later in the master)
        g, (y0, y1, x0, x1) = self.glass.render(img, t, fog_amt=0.0, drop_light=(self.cfall * 0.6)[..., None] * rgb(1.0, 0.7, 0.4) + 0.05)
        m = self.glass.m[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + g * m
        return img


# ====================================================================== the windowpane (opening shot)
class Pane:
    """Plate 9: one rainy pane, the lamp blooming through it. Fog takes his words; three taps ring it."""
    def __init__(self, W, H, seed=71):
        self.W, self.H = W, H
        L, s, (ox, oy), up = load_plate(9, W, H)
        self.s = s; P = lambda x, y: (x * s - ox, y * s - oy); self.P = P
        self.base = L
        self.yy, self.xx = grid(H, W)
        gm = np.zeros((H, W), np.uint8)
        poly = [(205, 0), (1536, 0), (1536, 1024), (205, 1024)]
        cv2.fillPoly(gm, [np.round(np.array([P(*p) for p in poly], np.float32)).astype(np.int32)], 255)
        # the frame at the bottom-left is not glass
        ys = self.yy; xs = self.xx
        gm = gm.astype(F32) / 255 * (ys < P(0, 905)[1] - (xs - P(205, 0)[0]) * 0.02)
        self.gm = np.clip(blur(gm, 2 * s), 0, 1)
        self.glass = Glass(self.gm, s, seed=seed, density=0.45, big_drops=22, drop_scale=2.2, fog_base=0.10)
        self.lamp = P(450, 200)
        dd = np.sqrt((xs - self.lamp[0]) ** 2 + (ys - self.lamp[1]) ** 2) / (s * 260)
        self.lfall = (1 / (1 + dd * dd)).astype(F32)
        self.words = None

    def writing(self, t, word_times, lines, font_name, size, origin):
        """Breath-written words: each fogs in as it is whispered. Returns a fog-density map."""
        s = self.s
        if self.words is None:
            f = font(font_name, size)
            self.words = []
            x0, y0 = origin; lh = size * 1.25; k = 0
            for li, line in enumerate(lines):
                x = x0
                for w in line.split(' '):
                    tw = f.getlength(w); asc, desc = f.getmetrics(); pad = int(size * 0.4)
                    im = Image.new('L', (int(tw) + 2 * pad, asc + desc + 2 * pad), 0)
                    ImageDraw.Draw(im).text((pad, pad), w, font=f, fill=255)
                    m = np.asarray(im, F32) / 255
                    m = blur(m, size * 0.025) * 1.6 + blur(m, size * 0.10) * 0.55      # breath blooms around strokes
                    self.words.append((m, x - pad, y0 + li * lh - pad - asc * 0.15, k)); k += 1
                    x += tw + f.getlength(' ')
        D = np.zeros((self.H, self.W), F32)
        for (m, x, y, k) in self.words:
            if k >= len(word_times): continue
            a = ease_out((t - word_times[k]) / 0.6)
            if a > 0: paste_add(D, m, x, y, a)
        return np.clip(D, 0, 1.2)

    def render(self, t, st):
        s = self.s
        img = self.base * st.get('expo', 1.0)
        # the shape beyond the rain, against the lamp
        pres = st.get('presence', 0.0)
        if pres > 0:
            a = silhouette(); hh = int(self.H * 1.25); ww = int(a.shape[1] * hh / a.shape[0])
            A = blur(cv2.resize(a, (ww, hh), interpolation=cv2.INTER_AREA), 9 * s)
            full = np.zeros((self.H, self.W), F32); paste_add(full, A, self.lamp[0] - ww * 0.55, self.lamp[1] - hh * 0.08)
            img = img * (1 - full[..., None] * 0.92 * pres)
        extra = st.get('writing')
        fog_glow = (self.lfall * 0.06)[..., None] * rgb(1.0, 0.62, 0.3) + rgb(0.012, 0.012, 0.016)
        g, (y0, y1, x0, x1) = self.glass.render(img, t, fog_glow=fog_glow, fog_amt=st.get('fog', 1.0), extra_fog=extra,
                                                tap_rings=st.get('taps', ()),
                                                drop_light=(self.lfall * 0.9)[..., None] * rgb(1.0, 0.7, 0.4) + 0.04)
        m = self.glass.m[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + g * m
        # breath letters catch the lamp a little more than the plain fog
        if extra is not None:
            img = img + (np.clip(extra, 0, 1) * 0.085)[..., None] * (rgb(0.75, 0.78, 0.85) + self.lfall[..., None] * rgb(0.6, 0.35, 0.15))
        return img
