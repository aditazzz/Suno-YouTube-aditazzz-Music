"""The Drive — sprites, drawn with PIL once and cached: road signs, billboards, the pier's neon, streetlights, the
cars in the queue, the lighthouse, the office, the gate. Each is a float32 RGBA array at PPU pixels per world unit."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from studio import core as C
from studio.core import hexc

PPU = 110.0
_CACHE = {}
F_SIGN = C.F_DISPB; F_HEAVY = C.F_DISP; F_MONO = C.F_MONOB

GREEN = (18, 94, 58); SIGN_WHITE = (246, 243, 232); YELLOW = (255, 204, 48); INK = (22, 22, 30)
RED = (214, 44, 52); POST = (120, 118, 112); NEON = (255, 92, 150)


def _font(path, size): return ImageFont.truetype(path, max(6, int(size)))


def _fit(draw, text, path, size, maxw):
    f = _font(path, size)
    while size > 8 and draw.textlength(text, font=f) > maxw:
        size -= 2; f = _font(path, size)
    return f


def _to_rgba(im):
    a = np.asarray(im, np.float32) / 255.0
    return np.ascontiguousarray(a)


def _canvas(w_units, h_units):
    w, h = int(w_units * PPU), int(h_units * PPU)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); return im, ImageDraw.Draw(im), w, h


def cached(key, fn):
    if key not in _CACHE: _CACHE[key] = fn()
    return _CACHE[key]


# ------------------------------------------------------------------ signs
def sign(lines, style='guide', w_units=3.4, h_units=3.6, arrow=None, sub=None):
    """A sign on a post. style: guide (green), no (white, red ring), warn (yellow diamond), bill (billboard),
    exit (green with an EXIT tab), notice (dark rounded), blank."""
    key = ('sign', tuple(lines), style, w_units, h_units, arrow, sub)
    def make():
        im, d, w, h = _canvas(w_units, h_units)
        if style in ('bill',):
            ph = int(h * 0.62); px = int(w * 0.04)
            for x in (int(w * 0.18), int(w * 0.82)):
                d.rectangle([x - px, ph - 4, x + px, h], fill=(70, 66, 62, 255))
            d.rounded_rectangle([0, 0, w - 1, ph], radius=int(w * 0.02), fill=(26, 24, 34, 255), outline=(230, 220, 200, 255), width=max(3, w // 70))
            y = int(ph * 0.14); n = len(lines)
            for i, ln in enumerate(lines):
                big = (i == 0)
                f = _fit(d, ln, F_HEAVY if big else F_SIGN, ph * (0.34 if n == 1 else 0.26 if big else 0.17), w * 0.9)
                tw = d.textlength(ln, font=f)
                col = (255, 232, 120, 255) if big else (236, 232, 222, 255)
                d.text(((w - tw) / 2, y), ln, font=f, fill=col); y += f.size * 1.18
            if sub:
                f = _fit(d, sub, F_MONO, ph * 0.11, w * 0.9); tw = d.textlength(sub, font=f)
                d.text(((w - tw) / 2, ph - f.size * 1.6), sub, font=f, fill=(255, 92, 150, 255))
            return _to_rgba(im)
        # post
        pw = max(6, int(w * 0.035)); d.rectangle([w // 2 - pw, int(h * 0.45), w // 2 + pw, h], fill=POST + (255,))
        if style == 'warn':
            s = int(min(w, h * 0.6) * 0.98); cx, cy = w // 2, int(h * 0.3)
            d.polygon([(cx, cy - s // 2), (cx + s // 2, cy), (cx, cy + s // 2), (cx - s // 2, cy)], fill=YELLOW + (255,), outline=INK + (255,), width=max(4, s // 30))
            y = cy - len(lines) * s * 0.11
            for ln in lines:
                f = _fit(d, ln, F_HEAVY, s * 0.2, s * 0.62); tw = d.textlength(ln, font=f)
                d.text((cx - tw / 2, y), ln, font=f, fill=INK + (255,)); y += f.size * 1.15
            return _to_rgba(im)
        ph = int(h * 0.52); x0, y0, x1, y1 = int(w * 0.02), 0, int(w * 0.98), ph
        if style == 'no':
            d.rounded_rectangle([x0, y0, x1, y1], radius=int(w * 0.04), fill=SIGN_WHITE + (255,), outline=INK + (255,), width=max(4, w // 60))
            r = int(min(w, ph) * 0.22); cx, cy = w // 2, int(ph * 0.3)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED + (255,), width=max(6, r // 4))
            d.line([(cx - r * 0.72, cy - r * 0.72), (cx + r * 0.72, cy + r * 0.72)], fill=RED + (255,), width=max(6, r // 4))
            f = _fit(d, lines[0], F_HEAVY, ph * 0.2, w * 0.86); tw = d.textlength(lines[0], font=f)
            d.text(((w - tw) / 2, cy + r * 1.12), lines[0], font=f, fill=INK + (255,))
            if len(lines) > 1:
                f2 = _fit(d, lines[1], F_SIGN, ph * 0.13, w * 0.88); tw = d.textlength(lines[1], font=f2)
                d.text(((w - tw) / 2, cy + r * 1.12 + f.size * 1.15), lines[1], font=f2, fill=INK + (255,))
            return _to_rgba(im)
        if style == 'notice':
            fill = (28, 28, 38, 255); fg = (240, 236, 226, 255); outline = (240, 236, 226, 255)
        elif style == 'red':
            fill = (190, 36, 44, 255); fg = (255, 245, 235, 255); outline = (255, 245, 235, 255)
        else:
            fill = GREEN + (255,); fg = SIGN_WHITE + (255,); outline = SIGN_WHITE + (255,)
        if style == 'exit':
            tabw = int(w * 0.42); d.rounded_rectangle([x1 - tabw, y0, x1, int(ph * 0.2)], radius=int(w * 0.03), fill=fill, outline=outline, width=max(3, w // 80))
            f = _fit(d, 'EXIT 459', F_SIGN, ph * 0.11, tabw * 0.85); tw = d.textlength('EXIT 459', font=f)
            d.text((x1 - tabw / 2 - tw / 2, ph * 0.03), 'EXIT 459', font=f, fill=fg)
            y0 = int(ph * 0.2)
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(w * 0.04), fill=fill, outline=outline, width=max(4, w // 70))
        n = len(lines); avail = (y1 - y0) * 0.86; y = y0 + (y1 - y0) * 0.07
        for i, ln in enumerate(lines):
            f = _fit(d, ln, F_SIGN, avail / max(n, 1.6) * 0.78, w * 0.86); tw = d.textlength(ln, font=f)
            d.text(((w - tw) / 2 - (w * 0.08 if arrow else 0), y), ln, font=f, fill=fg); y += f.size * 1.22
        if arrow:
            ax = x1 - int(w * 0.14); ay = (y0 + y1) // 2; s = int((y1 - y0) * 0.16)
            if arrow == 'up': pts = [(ax, ay - s), (ax + s * 0.7, ay), (ax + s * 0.3, ay), (ax + s * 0.3, ay + s), (ax - s * 0.3, ay + s), (ax - s * 0.3, ay), (ax - s * 0.7, ay)]
            elif arrow == 'right': pts = [(ax + s, ay), (ax, ay - s * 0.7), (ax, ay - s * 0.3), (ax - s, ay - s * 0.3), (ax - s, ay + s * 0.3), (ax, ay + s * 0.3), (ax, ay + s * 0.7)]
            else: pts = [(ax - s, ay), (ax, ay - s * 0.7), (ax, ay - s * 0.3), (ax + s, ay - s * 0.3), (ax + s, ay + s * 0.3), (ax, ay + s * 0.3), (ax, ay + s * 0.7)]
            d.polygon(pts, fill=fg)
        return _to_rgba(im)
    return cached(key, make)


def neon(text, color=NEON, w_units=3.2, h_units=1.4):
    """Glowing channel name on the pier (emissive)."""
    key = ('neon', text, color, w_units, h_units)
    def make():
        im, d, w, h = _canvas(w_units, h_units)
        f = _fit(d, text, F_MONO, h * 0.5, w * 0.94); tw = d.textlength(text, font=f)
        x, y = (w - tw) / 2, h * 0.2
        # halo
        halo = Image.new('RGBA', (w, h), (0, 0, 0, 0)); hd = ImageDraw.Draw(halo)
        hd.text((x, y), text, font=f, fill=color + (255,))
        from PIL import ImageFilter
        halo = halo.filter(ImageFilter.GaussianBlur(h * 0.09))
        im.alpha_composite(halo); im.alpha_composite(halo)
        d.text((x, y), text, font=f, fill=(255, 240, 246, 255))
        return _to_rgba(im)
    return cached(key, make)


# ------------------------------------------------------------------ objects
def streetlight(h_units=5.0):
    def make():
        im, d, w, h = _canvas(1.6, h_units)
        pw = max(5, int(w * 0.05)); x = int(w * 0.2)
        d.rectangle([x - pw, int(h * 0.06), x + pw, h], fill=(90, 92, 100, 255))
        d.line([(x, int(h * 0.07)), (int(w * 0.85), int(h * 0.02))], fill=(90, 92, 100, 255), width=pw * 2)
        d.ellipse([int(w * 0.72), 0, int(w * 0.98), int(h * 0.05)], fill=(255, 236, 190, 255))
        return _to_rgba(im)
    return cached(('streetlight', h_units), make)


def palm(seed=0, h_units=5.5):
    def make():
        r = np.random.default_rng(seed)
        im, d, w, h = _canvas(3.2, h_units)
        cx = w // 2; top = int(h * 0.22)
        pts = [(cx - w * 0.05, h), (cx + w * 0.05, h), (cx + w * 0.03 + r.uniform(-8, 8), top), (cx - w * 0.03 + r.uniform(-8, 8), top)]
        d.polygon(pts, fill=(48, 36, 30, 255))
        for k in range(7):
            a = -math.pi / 2 + (k - 3) * 0.42 + r.uniform(-0.1, 0.1); L = w * 0.46
            pts = [(cx, top)]
            for s in np.linspace(0, 1, 8):
                pts.append((cx + math.cos(a) * L * s, top + math.sin(a) * L * s + s * s * h * 0.12))
            d.line(pts, fill=(34, 74, 52, 255), width=max(8, int(w * 0.07)), joint='curve')
            for s in np.linspace(0.15, 1, 6):
                x, y = cx + math.cos(a) * L * s, top + math.sin(a) * L * s + s * s * h * 0.12
                d.line([(x, y), (x + math.cos(a + 1.2) * w * 0.12, y + math.sin(a + 1.2) * w * 0.12)], fill=(34, 74, 52, 255), width=max(5, int(w * 0.04)))
        return _to_rgba(im)
    return cached(('palm', seed, h_units), make)


def lighthouse(label='PROD', lit=True, h_units=9.0):
    def make():
        im, d, w, h = _canvas(3.2, h_units)
        cx = w // 2
        d.polygon([(cx - w * 0.22, h), (cx + w * 0.22, h), (cx + w * 0.15, int(h * 0.2)), (cx - w * 0.15, int(h * 0.2))], fill=(236, 230, 220, 255))
        for i in range(3):
            y = int(h * (0.32 + i * 0.2)); d.rectangle([cx - w * 0.22, y, cx + w * 0.22, y + int(h * 0.07)], fill=RED + (255,))
        d.rectangle([cx - w * 0.2, int(h * 0.12), cx + w * 0.2, int(h * 0.21)], fill=(30, 30, 40, 255))
        d.rectangle([cx - w * 0.14, int(h * 0.05), cx + w * 0.14, int(h * 0.13)], fill=(255, 236, 160, 255) if lit else (90, 90, 100, 255))
        d.polygon([(cx - w * 0.2, int(h * 0.05)), (cx + w * 0.2, int(h * 0.05)), (cx, 0)], fill=(30, 30, 40, 255))
        f = _fit(d, label, F_HEAVY, h * 0.055, w * 0.4); tw = d.textlength(label, font=f)
        d.text((cx - tw / 2, int(h * 0.6)), label, font=f, fill=INK + (255,))
        return _to_rgba(im)
    return cached(('lighthouse', label, lit, h_units), make)


def car_rear(color=(60, 60, 70), plate='RETRY', w_units=2.0, lights=True):
    def make():
        im, d, w, h = _canvas(w_units, w_units * 0.78)
        d.rounded_rectangle([int(w * 0.04), int(h * 0.3), int(w * 0.96), int(h * 0.92)], radius=int(w * 0.08), fill=color + (255,))
        d.rounded_rectangle([int(w * 0.18), int(h * 0.02), int(w * 0.82), int(h * 0.45)], radius=int(w * 0.1), fill=tuple(int(c * 0.7) for c in color) + (255,))
        d.rounded_rectangle([int(w * 0.24), int(h * 0.08), int(w * 0.76), int(h * 0.36)], radius=int(w * 0.06), fill=(40, 50, 70, 255))
        lc = (255, 40, 50, 255) if lights else (120, 30, 30, 255)
        d.rounded_rectangle([int(w * 0.07), int(h * 0.5), int(w * 0.28), int(h * 0.62)], radius=6, fill=lc)
        d.rounded_rectangle([int(w * 0.72), int(h * 0.5), int(w * 0.93), int(h * 0.62)], radius=6, fill=lc)
        d.rounded_rectangle([int(w * 0.36), int(h * 0.66), int(w * 0.64), int(h * 0.82)], radius=4, fill=(240, 236, 220, 255))
        f = _fit(d, plate, F_MONO, h * 0.11, w * 0.26); tw = d.textlength(plate, font=f)
        d.text((w / 2 - tw / 2, int(h * 0.675)), plate, font=f, fill=INK + (255,))
        d.rectangle([int(w * 0.06), int(h * 0.88), int(w * 0.22), h], fill=(20, 20, 24, 255)); d.rectangle([int(w * 0.78), int(h * 0.88), int(w * 0.94), h], fill=(20, 20, 24, 255))
        return _to_rgba(im)
    return cached(('car', color, plate, w_units, lights), make)


def traffic_light(state='green', check=True, h_units=5.0):
    def make():
        im, d, w, h = _canvas(1.4, h_units)
        cx = w // 2; pw = max(5, int(w * 0.06))
        d.rectangle([cx - pw, int(h * 0.42), cx + pw, h], fill=(70, 72, 80, 255))
        d.rounded_rectangle([int(w * 0.2), 0, int(w * 0.8), int(h * 0.44)], radius=int(w * 0.1), fill=(34, 36, 44, 255))
        for i, (col, on) in enumerate(((RED, state == 'red'), ((255, 190, 40), state == 'amber'), ((40, 220, 110), state == 'green'))):
            y = int(h * (0.04 + i * 0.135)); r = int(w * 0.2)
            c = col + (255,) if on else tuple(int(v * 0.25) for v in col) + (255,)
            d.ellipse([cx - r, y, cx + r, y + 2 * r], fill=c)
            if on and check and col[1] == 220:
                d.line([(cx - r * 0.55, y + r), (cx - r * 0.15, y + r * 1.45), (cx + r * 0.6, y + r * 0.5)], fill=(10, 60, 30, 255), width=max(4, r // 5))
        return _to_rgba(im)
    return cached(('tl', state, check, h_units), make)


def gate(lift=0.0, w_units=6.0):
    """Parking boom barrier across the road; lift 0 = down, 1 = up (quantized)."""
    q = int(round(lift * 12))
    def make():
        im, d, w, h = _canvas(w_units, 3.2)
        bx = int(w * 0.08); by = int(h * 0.55)
        d.rectangle([bx - int(w * 0.04), by, bx + int(w * 0.04), h], fill=(60, 60, 70, 255))
        d.rectangle([bx - int(w * 0.06), by - int(h * 0.1), bx + int(w * 0.06), by + int(h * 0.1)], fill=(200, 60, 60, 255))
        a = -q / 12 * math.radians(84); L = w * 0.88
        x1, y1 = bx + math.cos(a) * L, by + math.sin(a) * L
        d.line([(bx, by), (x1, y1)], fill=(240, 236, 226, 255), width=max(10, int(h * 0.06)))
        for k in range(8):
            s0, s1 = k / 8, (k + 0.5) / 8
            d.line([(bx + math.cos(a) * L * s0, by + math.sin(a) * L * s0), (bx + math.cos(a) * L * s1, by + math.sin(a) * L * s1)], fill=(214, 44, 52, 255), width=max(10, int(h * 0.06)))
        return _to_rgba(im)
    return cached(('gate', q, w_units), make)


def office(label='ACME', h_units=9.0, w_units=8.0, lit=0.4):
    def make():
        r = np.random.default_rng(5)
        im, d, w, h = _canvas(w_units, h_units)
        d.rectangle([0, int(h * 0.1), w, h], fill=(44, 46, 60, 255))
        d.rectangle([int(w * 0.25), 0, int(w * 0.75), int(h * 0.1)], fill=(38, 40, 52, 255))
        for j in range(10):
            for i in range(12):
                x = int(w * (0.05 + i * 0.077)); y = int(h * (0.15 + j * 0.08))
                on = r.random() < lit
                d.rectangle([x, y, x + int(w * 0.05), y + int(h * 0.05)], fill=(255, 222, 150, 255) if on else (70, 72, 90, 255))
        f = _fit(d, label, F_HEAVY, h * 0.06, w * 0.45); tw = d.textlength(label, font=f)
        d.text((w / 2 - tw / 2, int(h * 0.02)), label, font=f, fill=(230, 226, 216, 255))
        return _to_rgba(im)
    return cached(('office', label, h_units, w_units, lit), make)


def envelopes(n=14, seed=1, w_units=2.2):
    def make():
        r = np.random.default_rng(seed)
        im, d, w, h = _canvas(w_units, w_units * 0.8)
        for k in range(n):
            ew, eh = int(w * 0.34), int(w * 0.22)
            x = int(r.uniform(0, w - ew)); y = int(h - eh - r.uniform(0, h * 0.45) * (1 - k / n))
            d.rectangle([x, y, x + ew, y + eh], fill=(242, 236, 222, 255), outline=(120, 110, 100, 255), width=3)
            d.line([(x, y), (x + ew / 2, y + eh * 0.55), (x + ew, y)], fill=(120, 110, 100, 255), width=3)
            d.ellipse([x + ew * 0.62, y + eh * 0.5, x + ew * 0.8, y + eh * 0.78], fill=RED + (255,))
        return _to_rgba(im)
    return cached(('env', n, seed, w_units), make)


def pier(w_units=14.0, h_units=4.0, seed=2):
    """A run of pier: deck, railing, string lights, posts."""
    def make():
        im, d, w, h = _canvas(w_units, h_units)
        deck = int(h * 0.6)
        d.rectangle([0, deck, w, deck + int(h * 0.08)], fill=(70, 56, 46, 255))
        for k in range(7):
            x = int(w * (0.04 + k * 0.155)); d.rectangle([x - int(w * 0.012), deck, x + int(w * 0.012), h], fill=(52, 42, 36, 255))
            d.rectangle([x - int(w * 0.008), int(h * 0.22), x + int(w * 0.008), deck], fill=(60, 50, 44, 255))
        d.rectangle([0, int(h * 0.36), w, int(h * 0.36) + int(h * 0.025)], fill=(72, 62, 54, 255))
        for k in range(6):
            x0 = int(w * (0.04 + k * 0.155)); x1 = int(w * (0.04 + (k + 1) * 0.155))
            pts = [(x0 + (x1 - x0) * s, int(h * 0.22) + math.sin(s * math.pi) * h * 0.08) for s in np.linspace(0, 1, 9)]
            d.line(pts, fill=(40, 34, 30, 255), width=3)
            for px, py in pts[1:-1]:
                d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(255, 220, 140, 255))
        return _to_rgba(im)
    return cached(('pier', w_units, h_units, seed), make)


def small_sign(text, w_units=1.3, h_units=1.2, fill=(120, 90, 60), fg=(250, 240, 220)):
    """Little wooden signs in the seabed at low tide."""
    def make():
        im, d, w, h = _canvas(w_units, h_units)
        d.rectangle([w // 2 - 6, int(h * 0.5), w // 2 + 6, h], fill=(90, 70, 50, 255))
        d.rectangle([0, 0, w, int(h * 0.55)], fill=fill + (255,), outline=(60, 44, 30, 255), width=4)
        f = _fit(d, text, F_MONO, h * 0.24, w * 0.9); tw = d.textlength(text, font=f)
        d.text((w / 2 - tw / 2, h * 0.13), text, font=f, fill=fg + (255,))
        return _to_rgba(im)
    return cached(('ss', text, w_units, h_units, fill, fg), make)


def rock(seed=0, w_units=1.6):
    def make():
        r = np.random.default_rng(seed + 11)
        im, d, w, h = _canvas(w_units, w_units * 0.6)
        pts = [(w * (0.5 + 0.48 * math.cos(a)) , h * (0.6 + 0.4 * math.sin(a)) * (0.7 + 0.3 * r.random())) for a in np.linspace(math.pi, 2 * math.pi, 9)]
        pts = [(0, h), *pts, (w, h)]
        d.polygon(pts, fill=(96, 92, 100, 255))
        return _to_rgba(im)
    return cached(('rock', seed, w_units), make)


def cone(w_units=0.7):
    def make():
        im, d, w, h = _canvas(w_units, w_units * 1.5)
        d.polygon([(w * 0.5, 0), (w * 0.85, h * 0.9), (w * 0.15, h * 0.9)], fill=(255, 120, 40, 255))
        d.rectangle([0, h * 0.88, w, h], fill=(30, 30, 36, 255))
        d.rectangle([w * 0.3, h * 0.45, w * 0.7, h * 0.58], fill=(250, 250, 250, 255))
        return _to_rgba(im)
    return cached(('cone', w_units), make)


def lifering(label='ROLLBACK', px=520):
    """The life ring (screen-space sprite, bigger base resolution)."""
    def make():
        im = Image.new('RGBA', (px, px), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        cx = cy = px / 2; R = px * 0.46; r = px * 0.22
        for k in range(4):
            a0 = k * 90 + 15; col = (255, 120, 40, 255) if k % 2 == 0 else (248, 244, 236, 255)
            d.pieslice([cx - R, cy - R, cx + R, cy + R], a0, a0 + 90, fill=col)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, 0))
        d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(60, 44, 30, 255), width=max(4, px // 90))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(60, 44, 30, 255), width=max(4, px // 90))
        # rope wraps
        for a in (45, 135, 225, 315):
            x0, y0 = cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r
            x1, y1 = cx + math.cos(math.radians(a)) * R, cy + math.sin(math.radians(a)) * R
            d.line([(x0, y0), (x1, y1)], fill=(200, 180, 140, 255), width=max(5, px // 60))
        f = _fit(d, label, F_HEAVY, px * 0.1, R * 1.3); tw = d.textlength(label, font=f)
        d.rounded_rectangle([cx - tw / 2 - px * 0.03, cy + r * 0.95 - px * 0.01, cx + tw / 2 + px * 0.03, cy + r * 0.95 + f.size * 1.2], radius=px * 0.02, fill=(28, 26, 34, 255))
        d.text((cx - tw / 2, cy + r * 0.95), label, font=f, fill=(255, 244, 230, 255))
        return _to_rgba(im)
    return cached(('ring', label, px), make)


def bank(h_units=6.0, w_units=6.0, text='$ $ $'):
    def make():
        im, d, w, h = _canvas(w_units, h_units)
        d.rectangle([0, int(h * 0.18), w, h], fill=(214, 206, 190, 255))
        for i in range(4):
            x = int(w * (0.08 + i * 0.24)); d.rectangle([x, int(h * 0.3), x + int(w * 0.1), h], fill=(190, 182, 166, 255))
        d.polygon([(0, int(h * 0.18)), (w, int(h * 0.18)), (w // 2, 0)], fill=(190, 182, 166, 255))
        d.rectangle([int(w * 0.1), int(h * 0.42), int(w * 0.9), int(h * 0.6)], fill=(24, 24, 32, 255))
        f = _fit(d, text, F_MONO, h * 0.12, w * 0.76); tw = d.textlength(text, font=f)
        d.text((w / 2 - tw / 2, int(h * 0.45)), text, font=f, fill=(90, 255, 160, 255) if '$' in text else (255, 80, 90, 255))
        fb = _fit(d, 'PAYMENTS BANK', F_SIGN, h * 0.06, w * 0.8); tw = d.textlength('PAYMENTS BANK', font=fb)
        d.text((w / 2 - tw / 2, int(h * 0.24)), 'PAYMENTS BANK', font=fb, fill=(60, 56, 50, 255))
        return _to_rgba(im)
    return cached(('bank', h_units, w_units, text), make)
