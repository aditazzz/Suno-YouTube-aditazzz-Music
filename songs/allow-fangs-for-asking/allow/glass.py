"""Window glass: rain on the outside surface, condensation on the inside, and everything written into either.

Order of light through a pane (camera inside the room):  street -> raindrops (outside surface) -> glass ->
condensation (inside surface) -> camera, plus a faint reflection of the room on the glass.
Raindrops refract an inverted, minified view of what is behind them (a tiny lens each), with a dark rim and a glint.
Sliding drops move in stick-slip jumps and leave a clear trail through the drops and the fog that slowly refills.
"""
import math
import numpy as np, cv2
from .fx import F32, fbm2, blur, fast_blur, luma, rgb, sstep, clamp, text_mask, n1


class Glass:
    def __init__(self, mask, scale, seed=1, density=1.0, big_drops=26, drop_scale=1.0, fog_base=0.22):
        """mask: (H, W) float glass coverage in output pixels. scale: output px per plate px."""
        self.H, self.W = mask.shape
        ys, xs = np.nonzero(mask > 0.01)
        pad = int(24 * scale)
        self.x0, self.x1 = max(0, xs.min() - pad), min(self.W, xs.max() + pad + 1)
        self.y0, self.y1 = max(0, ys.min() - pad), min(self.H, ys.max() + pad + 1)
        self.m = mask[self.y0:self.y1, self.x0:self.x1].astype(F32)
        self.h, self.w = self.m.shape
        self.s = scale; self.seed = seed; self.drop_scale = drop_scale
        rng = np.random.RandomState(seed)
        # ---- static drops (outside surface): many small, a few medium
        area = float(self.m.sum()) / (scale * scale)            # in plate px^2
        n = int(area * 0.0105 * density)
        X = rng.uniform(0, self.w, n); Y = rng.uniform(0, self.h, n)
        R = (np.exp(rng.normal(0.0, 0.55, n)) * 0.75 + 0.25) * scale * drop_scale
        R = np.clip(R, 0.6 * scale, 4.2 * scale)
        keep = self.m[np.clip(Y.astype(int), 0, self.h - 1), np.clip(X.astype(int), 0, self.w - 1)] > 0.5
        self.static = (X[keep], Y[keep], R[keep])
        self.sdx, self.sdy, self.sa, self.srim, self.sspec = self._drop_field(*self.static, k=2.2)
        # ---- sliding drops: stick-slip tracks
        self.tracks = []
        for i in range(big_drops):
            x = rng.uniform(0.03, 0.97) * self.w
            r = rng.uniform(2.6, 5.2) * scale * drop_scale
            period = rng.uniform(26, 60)
            self.tracks.append(dict(x=x, r=r, t0=rng.uniform(0, period), period=period, speed=rng.uniform(0.7, 1.7),
                                    seed=int(rng.randint(1e6)), wob=rng.uniform(0.2, 1.0)))
        # ---- condensation: denser toward the bottom and corners, patchy
        yy = np.linspace(0, 1, self.h, dtype=F32)[:, None]
        edge = cv2.distanceTransform((self.m > 0.5).astype(np.uint8), cv2.DIST_L2, 5) / (40 * scale)
        edge = np.exp(-np.clip(edge, 0, 4)).astype(F32)
        patch = fbm2(self.h, self.w, 90 * scale, seed + 3, 5)
        self.fog0 = np.clip(fog_base * (0.55 + 0.9 * patch) + 0.32 * edge * patch + 0.18 * yy ** 3, 0, 0.95) * self.m
        self.fog_tex = fbm2(self.h, self.w, 6 * scale, seed + 5, 3)      # fine droplet grain inside the fog
        self.frost_cache = {}

    # -------------------------------------------------------------- drops -> offset/alpha fields
    def _drop_field(self, X, Y, R, k=2.2):
        h, w = self.h, self.w
        dx = np.zeros((h, w), F32); dy = np.zeros((h, w), F32); a = np.zeros((h, w), F32)
        rim = np.zeros((h, w), F32); spec = np.zeros((h, w), F32)
        for cx, cy, r in zip(X, Y, R):
            rr = int(math.ceil(r)) + 1
            xa, xb = int(cx) - rr, int(cx) + rr + 1; ya, yb = int(cy) - rr, int(cy) + rr + 1
            if xb <= 0 or yb <= 0 or xa >= w or ya >= h: continue
            xa2, xb2, ya2, yb2 = max(0, xa), min(w, xb), max(0, ya), min(h, yb)
            gx = (np.arange(xa2, xb2, dtype=F32) + 0.5 - cx) / r
            gy = (np.arange(ya2, yb2, dtype=F32) + 0.5 - cy) / (r * 1.06)   # drops sag a little
            U, V = np.meshgrid(gx, gy); d2 = U * U + V * V
            inside = d2 < 1.0
            if not inside.any(): continue
            cov = np.clip((1.0 - np.sqrt(d2)) * r, 0, 1)                    # 1 px anti-aliased edge
            sl = (slice(ya2, yb2), slice(xa2, xb2))
            take = cov > a[sl]
            dx[sl] = np.where(take, -U * r * (k + 1), dx[sl]); dy[sl] = np.where(take, -V * r * (k + 1) * 1.06, dy[sl])
            a[sl] = np.maximum(a[sl], cov)
            rim[sl] = np.where(take, np.clip((np.sqrt(d2) - 0.62) / 0.38, 0, 1) ** 1.5 * (0.55 + 0.45 * np.clip(V, 0, 1)), rim[sl])
            sp = np.exp(-(((U + 0.32) ** 2 + (V + 0.42) ** 2) / 0.035)) * inside
            spec[sl] = np.maximum(spec[sl], sp)
        return dx, dy, a, rim, spec

    def _track_pos(self, tr, t, flow=1.0):
        """Stick-slip descent, re-spawning every `period` seconds. Returns (x, y, age, cycle)."""
        u = (t - tr['t0'])
        cyc = math.floor(u / tr['period']); u = u - cyc * tr['period']
        sd = tr['seed'] + 31 * cyc
        x = (tr['x'] + 0.37 * self.w * cyc) % self.w
        rate = tr['speed'] * self.s * 26.0 * (0.8 + 0.4 * ((sd * 0.61803) % 1.0))
        steps = u * 0.9
        k = math.floor(steps); f = steps - k
        slip = sstep(0.55, 0.85, f)
        y = (k + slip) * rate * (1.0 + 0.05 * k) * flow
        x = x + tr['wob'] * self.s * 5 * n1(y / (self.s * 40), sd + 9, 1.0)
        return x, y - 0.08 * self.h, u, cyc

    # -------------------------------------------------------------- main
    def render(self, behind, t, *, fog_glow=None, fog_amt=1.0, extra_fog=None, clear=None, flow=1.0,
               refl=None, refl_amt=0.0, tap_rings=(), drop_light=None, frost=None):
        """behind: (H, W, 3) linear full-frame image of what is seen through the glass (the plate).
        Returns (glass_rgb_bbox, bbox) for compositing with self.m."""
        y0, y1, x0, x1 = self.y0, self.y1, self.x0, self.x1
        B = behind[y0:y1, x0:x1]
        h, w = self.h, self.w
        # ---- moving drops this frame (+ the trails they have cleared)
        mX, mY, mR = [], [], []
        wipe = np.zeros((h, w), F32)
        film = np.zeros((h, w), F32)
        for tr in self.tracks:
            x, y, age, cyc = self._track_pos(tr, t, flow)
            ystart = -0.08 * h
            if y > ystart:
                # trail: a thin clear film behind the drop, fading with distance (time since it passed)
                L = min(y - ystart, 0.75 * h)
                th = max(1, int(tr['r'] * 0.9))
                segs = 10
                for k in range(segs):
                    ya = y - L * k / segs; yb = y - L * (k + 1) / segs
                    if ya < 0: break
                    a_ = 0.95 * (1 - k / segs) ** 1.3
                    xa = x + tr['wob'] * self.s * 5 * n1(ya / (self.s * 40), tr['seed'] + 31 * cyc + 9, 1.0) - (x - x)
                    cv2.line(wipe, (int(x), int(max(0, yb))), (int(x), int(min(h - 1, ya))), a_, th, cv2.LINE_AA)
                    cv2.line(film, (int(x), int(max(0, yb))), (int(x), int(min(h - 1, ya))), a_, max(1, th // 2 + 1), cv2.LINE_AA)
            if -tr['r'] < y < h + tr['r']:
                mX.append(x); mY.append(y); mR.append(tr['r'])
                mX += [x + 0.3 * tr['r'], x - 0.2 * tr['r'], x + 0.1 * tr['r']]
                mY += [y - 3.0 * tr['r'], y - 7.5 * tr['r'], y - 13 * tr['r']]
                mR += [tr['r'] * 0.42, tr['r'] * 0.3, tr['r'] * 0.25]
        wipe = blur(wipe, 1.2 * self.s)
        if mX:
            ddx, ddy, da, drim, dsp = self._drop_field(np.array(mX), np.array(mY), np.array(mR), k=2.6)
        sa = self.sa * (1 - wipe)
        # ---- refraction through drops (outside surface)
        gx, gy = np.meshgrid(np.arange(w, dtype=F32), np.arange(h, dtype=F32))
        dx, dy, a, rim, spec = self.sdx, self.sdy, sa, self.srim, self.sspec
        if mX:
            take = da > a
            dx = np.where(take, ddx, dx); dy = np.where(take, ddy, dy); a = np.maximum(a, da)
            rim = np.where(take, drim, rim); spec = np.maximum(spec * (1 - wipe), dsp)
        else:
            spec = spec * (1 - wipe)
        Bs = blur(B, 0.8 * self.s)                       # what a drop sees is a touch soft
        film = blur(film, 0.8 * self.s)
        fdx = cv2.Sobel(film, cv2.CV_32F, 1, 0, ksize=3) * 2.5 * self.s
        dx = dx + fdx * (1 - a) if False else dx
        refr = cv2.remap(Bs, gx + dx, gy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        out = B * (1 - a[..., None]) + (refr * 0.86) * a[..., None]
        if film.any():
            fw = cv2.remap(B, gx + fdx, gy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            fm = np.clip(film * 1.2, 0, 1)[..., None] * (1 - a[..., None])
            out = out * (1 - fm) + fw * 1.08 * fm
        out = out * (1 - 0.55 * (rim * a)[..., None])
        if drop_light is None: drop_light = rgb(1.0, 0.75, 0.5) * 0.5
        dl = drop_light[y0:y1, x0:x1] if np.ndim(drop_light) == 3 else drop_light
        out = out + (spec * a)[..., None] * dl * 1.8
        # ---- condensation (inside surface)
        D = self.fog0 * fog_amt * (1 - 0.92 * wipe)
        if extra_fog is not None: D = D + extra_fog[y0:y1, x0:x1]
        if clear is not None: D = D * (1 - clear[y0:y1, x0:x1])
        D = np.clip(D, 0, 1) * self.m
        Bf = fast_blur(out, 14 * self.s)
        fogged = Bf * 0.82
        if fog_glow is not None:
            fg = fog_glow[y0:y1, x0:x1] if fog_glow.ndim == 3 else fog_glow
            fogged = fogged + fg * (0.6 + 0.4 * self.fog_tex[..., None])
        out = out * (1 - D[..., None]) + fogged * D[..., None]
        # ---- tap rings: a pulse through the drops and a ring in the fog
        for (tx, ty, age, strength) in tap_rings:
            if age < 0 or age > 2.5: continue
            lx, ly = tx - x0, ty - y0
            rr = np.sqrt((gx - lx) ** 2 + (gy - ly) ** 2)
            R0 = (6 + 70 * (1 - math.exp(-age * 2.2))) * self.s
            ring = np.exp(-((rr - R0) / (3.5 * self.s)) ** 2) * math.exp(-age * 1.6) * strength
            core = np.exp(-(rr / (5 * self.s)) ** 2) * math.exp(-age * 0.8) * strength
            if fog_glow is not None:
                glow = (fog_glow[y0:y1, x0:x1] if fog_glow.ndim == 3 else fog_glow)
                out = out + glow * (ring * 1.4)[..., None]
            out = out * (1 - 0.35 * core[..., None]) + Bs * (0.35 * core)[..., None]
        # ---- reflection of the room on the glass
        if refl is not None and refl_amt > 0:
            out = out + refl[y0:y1, x0:x1] * refl_amt
        # ---- frost lettering (inside surface, on top)
        if frost is not None:
            fa, fc = frost
            fa = fa[y0:y1, x0:x1]; fc = fc[y0:y1, x0:x1]
            diffuse = fast_blur(out, 6 * self.s)
            out = out * (1 - fa[..., None]) + (diffuse * 0.75 + fc) * fa[..., None]
        return out, (y0, y1, x0, x1)

    # -------------------------------------------------------------- lettering helpers
    def frost_word(self, word, font_name, size, cx, cy, progress, t, light, seed=7, opacity=0.5):
        """Frost that grows into a word. Returns (alpha, colour) full-frame arrays.
        progress 0..1 grows left to right with ragged crystalline edges; light (3,) is the light it catches."""
        key = (word, font_name, int(size), int(cx), int(cy), seed)
        if key not in self.frost_cache:
            m = text_mask(word, font_name, size, pad=int(size * 0.6))
            h, w = m.shape
            core = blur(m, size * 0.008)
            dist = cv2.distanceTransform((m < 0.5).astype(np.uint8), cv2.DIST_L2, 5).astype(F32)
            # crystalline texture: ridged multi-scale noise, streaked like fern frost
            r1 = 1 - np.abs(fbm2(h, w, size * 0.05, seed, 4) * 2 - 1)
            r2 = 1 - np.abs(fbm2(h, w, size * 0.018, seed + 1, 3) * 2 - 1)
            vein = np.clip((r1 * 0.55 + r2 * 0.45 - 0.45) / 0.5, 0, 1) ** 2
            grain = fbm2(h, w, max(2.0, size * 0.004), seed + 2, 2)
            fringe = np.clip(1 - dist / (size * (0.03 + 0.07 * r1)), 0, 1) ** 2
            feather = np.clip(core * (0.55 + 0.45 * vein) + fringe * vein * 0.6, 0, 1) * (0.6 + 0.4 * grain)
            grow = (np.linspace(0, 1, w, dtype=F32)[None, :] * 0.85 + 0.15 * r1)
            sparkle = (fbm2(h, w, max(2.0, size * 0.005), seed + 3, 1) > 0.80).astype(F32) * core
            self.frost_cache[key] = (feather.astype(F32), grow.astype(F32), sparkle.astype(F32), (cx - w / 2, cy - h / 2))
        feather, grow, sparkle, (px, py) = self.frost_cache[key]
        reveal = np.clip((progress * 1.15 - grow) / 0.10, 0, 1)
        from .fx import paste_add
        A = np.zeros((self.H, self.W), F32); paste_add(A, feather * reveal * opacity, px, py)
        sp = np.zeros((self.H, self.W), F32)
        tw = 0.5 + 0.5 * math.sin(t * 5.0 + seed)
        paste_add(sp, sparkle * reveal * tw, px, py)
        col = np.ones((self.H, self.W, 1), F32) * (rgb(0.55, 0.62, 0.70) * 0.05 + light * 0.30)[None, None, :]
        col = col + sp[..., None] * (light * 2.5 + 0.08)
        return A, col
