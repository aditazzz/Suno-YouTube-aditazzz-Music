"""The slop: a dozen glossy, over-polished 'AI pictures' for the feed. They are deliberately airbrushed (smooth
gradients, glows, no ink) so they clash with the hand-inked city around them. Each has its tell (six fingers, a
garbled sign, a second sun...). Rendered once at 512 px and cached."""
import math
import numpy as np, cv2

F32 = np.float32
AA = cv2.LINE_AA


def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], F32)


def vgrad(h, w, stops):
    ys = np.linspace(0, 1, h, dtype=F32)
    xs = np.array([s for s, _ in stops], F32)
    col = np.stack([np.interp(ys, xs, np.array([hexc(c)[i] for _, c in stops], F32)) for i in range(3)], -1)
    return np.repeat(col[:, None, :], w, 1)


def blob(img, pts, col, blur=0.0, alpha=1.0):
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m, [np.round(np.asarray(pts, np.float64) * 16).astype(np.int32)], 255, AA, shift=4)
    m = m.astype(F32) / 255
    if blur: m = cv2.GaussianBlur(m, (0, 0), blur)
    c = np.asarray(col, F32)
    if c.ndim == 1: c = c[None, None]
    img[:] = img * (1 - m[..., None] * alpha) + c * m[..., None] * alpha
    return m


def disc(img, cx, cy, r, col, blur=0.0, alpha=1.0):
    a = np.linspace(0, 2 * math.pi, 64, endpoint=False)
    return blob(img, np.stack([cx + np.cos(a) * r, cy + np.sin(a) * r], 1), col, blur, alpha)


def ellipse(img, cx, cy, rx, ry, col, blur=0.0, alpha=1.0, ang=0.0):
    a = np.linspace(0, 2 * math.pi, 64, endpoint=False)
    x = np.cos(a) * rx; y = np.sin(a) * ry
    ca, sa = math.cos(ang), math.sin(ang)
    return blob(img, np.stack([cx + x * ca - y * sa, cy + x * sa + y * ca], 1), col, blur, alpha)


def glow(img, cx, cy, r, col, k=1.0):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(F32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    img += (np.exp(-d * d) * k)[..., None] * hexc(col) if isinstance(col, str) else (np.exp(-d * d) * k)[..., None] * col


def sheen(img, k=0.18):
    """The airbrushed 'AI' finish: soft bloom + a diagonal gloss + gentle vignette."""
    b = cv2.GaussianBlur(img, (0, 0), 6)
    img[:] = img * 0.82 + b * 0.18 + np.clip(b - 0.7, 0, 1) * 0.6
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(F32)
    v = 1 - 0.25 * (((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2) * 2.2)
    img[:] = img * v[..., None]
    return img


def hand6(img, x, y, s, col='f2c4a6', ang=0.0):
    """A hand with six fingers — the classic tell."""
    sk = hexc(col)
    ellipse(img, x, y, 34 * s, 40 * s, sk, 0.8, ang=ang)
    for k in range(6):
        a = ang - 1.05 + k * 0.38
        fx = x + math.sin(a) * 52 * s; fy = y - math.cos(a) * 52 * s
        ellipse(img, (x + fx) / 2 + math.sin(a) * 6 * s, (y + fy) / 2 - math.cos(a) * 6 * s, 9 * s, 30 * s, sk, 0.6, ang=a)
    ellipse(img, x - 30 * s, y + 6 * s, 9 * s, 24 * s, sk * 0.96, 0.6, ang=ang + 1.2)


def _sunset(S):
    img = vgrad(S, S, [(0, '2b1a5e'), (0.32, 'c04a8a'), (0.55, 'ff8a5c'), (0.62, 'ffd08a'), (0.63, '5a2a6a'), (1.0, '1b1240')])
    glow(img, S * 0.5, S * 0.58, S * 0.3, 'ff9a5a', 0.7)
    disc(img, S * 0.5, S * 0.56, S * 0.13, hexc('fff0c0'), 1.5)
    disc(img, S * 0.71, S * 0.42, S * 0.05, hexc('ffe0b0'), 1.2)          # a second, smaller sun
    for i in range(14):
        y = S * (0.64 + i * 0.025); w = S * (0.2 - i * 0.008)
        blob(img, [(S * 0.5 - w, y), (S * 0.5 + w, y), (S * 0.5 + w * 0.8, y + 3), (S * 0.5 - w * 0.8, y + 3)], hexc('ffd890'), 1.0, 0.5)
    # palm silhouette
    blob(img, [(S * 0.14, S), (S * 0.17, S * 0.55), (S * 0.19, S * 0.55), (S * 0.18, S)], hexc('140b2a'), 0.6)
    for a in (-2.6, -2.0, -1.2, -0.6, 0.0):
        x0, y0 = S * 0.18, S * 0.55
        x1, y1 = x0 + math.cos(a) * S * 0.16, y0 + math.sin(a) * S * 0.08 + S * 0.03
        blob(img, [(x0, y0), (x1, y1 - 6), (x1, y1 + 4)], hexc('140b2a'), 0.6)
    return img


def _cake(S):
    img = vgrad(S, S, [(0, 'fbe3ec'), (1, 'f1b7cb')])
    glow(img, S * 0.5, S * 0.3, S * 0.4, 'ffffff', 0.35)
    blob(img, [(0, S * 0.78), (S, S * 0.74), (S, S), (0, S)], hexc('c98a5a'), 1.0)               # table
    for k, (y, w, c) in enumerate(((0.66, 0.30, 'ff9ec4'), (0.53, 0.25, 'ffb8d4'), (0.42, 0.19, 'ffd0e2'))):
        blob(img, [(S * (0.5 - w), S * y), (S * (0.5 + w), S * y), (S * (0.5 + w), S * (y + 0.12)), (S * (0.5 - w), S * (y + 0.12))], hexc(c), 1.0)
        ellipse(img, S * 0.5, S * y, S * w, S * 0.03, hexc('fff2f8'), 1.0)
        for d in range(9):
            disc(img, S * (0.5 - w + 0.03 + d * (2 * w - 0.06) / 8), S * (y + 0.02), S * 0.012, hexc('ff5f9e'), 0.6)
    for k in range(5):
        x = S * (0.4 + k * 0.05)
        blob(img, [(x - 3, S * 0.42), (x + 3, S * 0.42), (x + 3, S * 0.34), (x - 3, S * 0.34)], hexc('8fd0ff'), 0.6)
        ellipse(img, x, S * 0.325, 4, 9, hexc('ffd34d'), 1.2)
        glow(img, x, S * 0.32, 14, 'ffcf70', 0.4)
    hand6(img, S * 0.86, S * 0.62, S / 512 * 1.1, ang=-0.5)
    return img


def _catsuit(S):
    img = vgrad(S, S, [(0, '3a5a7a'), (1, '1d2c40')])
    glow(img, S * 0.5, S * 0.35, S * 0.45, 'a8d8ff', 0.25)
    blob(img, [(S * 0.18, S), (S * 0.25, S * 0.62), (S * 0.75, S * 0.62), (S * 0.82, S)], hexc('20232e'), 1.0)  # suit
    blob(img, [(S * 0.44, S * 0.62), (S * 0.56, S * 0.62), (S * 0.5, S * 0.86)], hexc('f4f4f8'), 0.8)
    blob(img, [(S * 0.48, S * 0.64), (S * 0.52, S * 0.64), (S * 0.53, S * 0.8), (S * 0.5, S * 0.84), (S * 0.47, S * 0.8)], hexc('c0303a'), 0.6)
    ellipse(img, S * 0.5, S * 0.44, S * 0.17, S * 0.15, hexc('e8a060'), 1.0)
    for sx in (-1, 1):
        blob(img, [(S * (0.5 + sx * 0.06), S * 0.33), (S * (0.5 + sx * 0.16), S * 0.22), (S * (0.5 + sx * 0.16), S * 0.37)], hexc('e8a060'), 0.8)
        ellipse(img, S * (0.5 + sx * 0.065), S * 0.43, S * 0.03, S * 0.035, hexc('3fe08a'), 0.8)
        disc(img, S * (0.5 + sx * 0.065), S * 0.43, S * 0.012, hexc('0b1a10'), 0.5)
    ellipse(img, S * 0.5, S * 0.5, S * 0.025, S * 0.016, hexc('ff8aa0'), 0.6)
    # a desk sign with garbled text
    blob(img, [(S * 0.62, S * 0.9), (S * 0.95, S * 0.9), (S * 0.93, S * 0.82), (S * 0.64, S * 0.82)], hexc('d8b070'), 0.8)
    for k in range(6):
        blob(img, [(S * (0.66 + k * 0.045), S * 0.85), (S * (0.69 + k * 0.045), S * 0.85), (S * (0.69 + k * 0.045), S * 0.87), (S * (0.66 + k * 0.045), S * 0.87)], hexc('3a2a10'), 0.3)
    return img


def _breadhouse(S):
    img = vgrad(S, S, [(0, '9fd8ff'), (0.7, 'e8f6ff'), (0.71, '7cc46a'), (1, '4f9a48')])
    glow(img, S * 0.8, S * 0.15, S * 0.3, 'fff2c0', 0.5)
    blob(img, [(S * 0.22, S * 0.78), (S * 0.22, S * 0.5), (S * 0.78, S * 0.5), (S * 0.78, S * 0.78)], hexc('d89a52'), 1.0)
    for r in range(4):
        for c in range(6):
            ellipse(img, S * (0.27 + c * 0.093), S * (0.54 + r * 0.065), S * 0.042, S * 0.028, hexc('e8b06a'), 1.0)
            ellipse(img, S * (0.27 + c * 0.093), S * (0.53 + r * 0.065), S * 0.03, S * 0.012, hexc('f6d39a'), 1.2)
    blob(img, [(S * 0.16, S * 0.52), (S * 0.5, S * 0.22), (S * 0.84, S * 0.52)], hexc('b8743a'), 1.0)
    for k in range(6):
        y = S * (0.3 + k * 0.04)
        blob(img, [(S * 0.5 - (y - S * 0.22) * 1.1, y), (S * 0.5 + (y - S * 0.22) * 1.1, y), (S * 0.5 + (y - S * 0.22) * 1.1, y + 4), (S * 0.5 - (y - S * 0.22) * 1.1, y + 4)], hexc('f0c080'), 1.0, 0.6)
    blob(img, [(S * 0.44, S * 0.78), (S * 0.44, S * 0.64), (S * 0.56, S * 0.64), (S * 0.56, S * 0.78)], hexc('6a3a1a'), 0.8)
    disc(img, S * 0.34, S * 0.62, S * 0.04, hexc('ffe9a8'), 0.8); disc(img, S * 0.66, S * 0.62, S * 0.04, hexc('ffe9a8'), 0.8)
    return img


def _teacup(S):
    img = vgrad(S, S, [(0, 'fff4e6'), (1, 'f2d6c0')])
    glow(img, S * 0.5, S * 0.4, S * 0.4, 'ffffff', 0.4)
    ellipse(img, S * 0.5, S * 0.86, S * 0.3, S * 0.05, hexc('e8d0c0'), 1.2)
    blob(img, [(S * 0.24, S * 0.56), (S * 0.76, S * 0.56), (S * 0.68, S * 0.84), (S * 0.32, S * 0.84)], hexc('f8f8ff'), 1.0)
    ellipse(img, S * 0.81, S * 0.66, S * 0.07, S * 0.08, hexc('f8f8ff'), 1.0); ellipse(img, S * 0.81, S * 0.66, S * 0.035, S * 0.045, hexc('f2d6c0'), 1.0)
    for k in range(5): disc(img, S * (0.35 + k * 0.075), S * 0.66, S * 0.018, hexc('8fb8ff'), 0.6)
    ellipse(img, S * 0.5, S * 0.45, S * 0.17, S * 0.16, hexc('f2e2c8'), 1.0)       # puppy
    ellipse(img, S * 0.33, S * 0.42, S * 0.06, S * 0.12, hexc('c89a6a'), 1.0, ang=0.4)
    ellipse(img, S * 0.67, S * 0.42, S * 0.06, S * 0.12, hexc('c89a6a'), 1.0, ang=-0.4)
    for sx in (-1, 1):
        disc(img, S * (0.5 + sx * 0.06), S * 0.42, S * 0.03, hexc('2a1a10'), 0.6)
        disc(img, S * (0.5 + sx * 0.06) - 3, S * 0.41 - 3, S * 0.009, hexc('ffffff'), 0.4)
    ellipse(img, S * 0.5, S * 0.5, S * 0.03, S * 0.022, hexc('2a1a10'), 0.6)
    ellipse(img, S * 0.5, S * 0.56, S * 0.02, S * 0.03, hexc('ff8aa0'), 0.6)
    return img


def _waterfall(S):
    img = vgrad(S, S, [(0, '5ad0ff'), (0.5, 'b8f0ff'), (1, '2a8a6a')])
    blob(img, [(0, S * 0.35), (S * 0.35, S * 0.2), (S * 0.42, S * 0.75), (0, S * 0.9)], hexc('3a7a5a'), 1.0)
    blob(img, [(S, S * 0.3), (S * 0.62, S * 0.18), (S * 0.56, S * 0.75), (S, S * 0.9)], hexc('35704f'), 1.0)
    blob(img, [(S * 0.4, S * 0.22), (S * 0.6, S * 0.22), (S * 0.62, S * 0.8), (S * 0.38, S * 0.8)], hexc('e8fbff'), 2.0)
    for k in range(7):
        a = math.pi * (1.05 + k * 0.03)
        cols = ['ff4a4a', 'ff9a3a', 'ffe84a', '4ae86a', '4ab0ff', '6a5aff', 'c05aff'][k]
        pts = [(S * 0.5 + math.cos(t) * S * (0.42 - k * 0.012), S * 0.62 + math.sin(t) * S * (0.42 - k * 0.012)) for t in np.linspace(math.pi * 1.05, math.pi * 1.95, 40)]
        pts2 = [(S * 0.5 + math.cos(t) * S * (0.42 - (k + 1) * 0.012), S * 0.62 + math.sin(t) * S * (0.42 - (k + 1) * 0.012)) for t in np.linspace(math.pi * 1.95, math.pi * 1.05, 40)]
        blob(img, pts + pts2, hexc(cols), 1.0, 0.45)
    for k in range(18):
        x = S * (0.05 + (k * 0.37) % 0.9); y = S * (0.8 + (k * 0.13) % 0.18)
        disc(img, x, y, S * 0.018, hexc(['ff5fc8', 'fff27a', '9a8cff'][k % 3]), 0.8); glow(img, x, y, 12, 'ffffff', 0.3)
    return img


def _quote(S, text_fn=None):
    img = vgrad(S, S, [(0, 'ffb36b'), (0.5, 'ff6fa0'), (1, '7a5cff')])
    glow(img, S * 0.3, S * 0.2, S * 0.5, 'ffffff', 0.25)
    return img


def _strawberry(S):
    img = vgrad(S, S, [(0, '7fd8ff'), (0.6, 'd8f6ff'), (0.61, 'f6e2b0'), (1, 'e8c890')])
    ellipse(img, S * 0.5, S * 0.85, S * 0.32, S * 0.05, hexc('c8a870'), 2.0)
    blob(img, [(S * 0.5, S * 0.86), (S * 0.24, S * 0.5), (S * 0.3, S * 0.3), (S * 0.5, S * 0.25), (S * 0.7, S * 0.3), (S * 0.76, S * 0.5)], hexc('ff2a4a'), 1.5)
    glow(img, S * 0.4, S * 0.38, S * 0.12, 'ffffff', 0.4)
    for k in range(30):
        x = S * (0.32 + (k * 0.137) % 0.36); y = S * (0.35 + (k * 0.071) % 0.42)
        ellipse(img, x, y, 2.5, 4, hexc('ffe98a'), 0.3)
    blob(img, [(S * 0.36, S * 0.28), (S * 0.5, S * 0.18), (S * 0.64, S * 0.28), (S * 0.5, S * 0.32)], hexc('2fb84a'), 1.0)
    # a tiny person for scale, standing next to it (with an extra arm)
    blob(img, [(S * 0.84, S * 0.84), (S * 0.86, S * 0.84), (S * 0.86, S * 0.76), (S * 0.84, S * 0.76)], hexc('2a2a3a'), 0.5)
    disc(img, S * 0.85, S * 0.745, 5, hexc('f2c4a6'), 0.5)
    return img


def _castle(S):
    img = vgrad(S, S, [(0, 'ff9ad8'), (0.5, 'ffd8ec'), (1, 'b8d8ff')])
    for k in range(6):
        ellipse(img, S * (0.1 + k * 0.17), S * (0.72 + (k % 2) * 0.05), S * 0.16, S * 0.07, hexc('ffffff'), 3.0, 0.8)
    blob(img, [(S * 0.3, S * 0.68), (S * 0.7, S * 0.68), (S * 0.5, S * 0.9)], hexc('8a7a9a'), 1.0)
    for x, w, h in ((0.33, 0.07, 0.3), (0.45, 0.1, 0.42), (0.6, 0.07, 0.34)):
        blob(img, [(S * x, S * 0.68), (S * (x + w), S * 0.68), (S * (x + w), S * (0.68 - h)), (S * x, S * (0.68 - h))], hexc('f6e8ff'), 0.8)
        blob(img, [(S * (x - 0.01), S * (0.68 - h)), (S * (x + w + 0.01), S * (0.68 - h)), (S * (x + w / 2), S * (0.68 - h - 0.12))], hexc('b06aff'), 0.8)
    glow(img, S * 0.5, S * 0.4, S * 0.3, 'fff2ff', 0.12)
    return img


def _chart(S):
    img = vgrad(S, S, [(0, '0f1a2e'), (1, '1a2a4a')])
    for k in range(6):
        y = S * (0.2 + k * 0.13)
        blob(img, [(S * 0.08, y), (S * 0.92, y), (S * 0.92, y + 1.5), (S * 0.08, y + 1.5)], hexc('2a3a5a'), 0.0)
    xs = np.linspace(S * 0.1, S * 0.9, 9)
    ys = S * np.array([0.82, 0.8, 0.83, 0.74, 0.7, 0.58, 0.5, 0.32, 0.12])
    for i in range(8):
        a, b = (xs[i], ys[i]), (xs[i + 1], ys[i + 1])
        d = np.array(b) - np.array(a); n = np.array([-d[1], d[0]]) / np.linalg.norm(d) * 6
        blob(img, [np.array(a) + n, np.array(b) + n, np.array(b) - n, np.array(a) - n], hexc('3dffa0'), 0.8)
    glow(img, xs[-1], ys[-1], 40, '3dffa0', 0.6)
    blob(img, [(xs[-1] - 26, ys[-1] + 4), (xs[-1] + 8, ys[-1] - 16), (xs[-1] + 2, ys[-1] + 22)], hexc('3dffa0'), 0.8)
    return img


def _heartsun(S):
    img = vgrad(S, S, [(0, 'ff6a8a'), (0.55, 'ffc08a'), (0.56, '4a6ad8'), (1, '1a2a7a')])
    cx, cy, r = S * 0.5, S * 0.42, S * 0.16
    t = np.linspace(0, 2 * math.pi, 80)
    hx = 16 * np.sin(t) ** 3; hy = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    blob(img, np.stack([cx + hx / 16 * r, cy + hy / 16 * r], 1), hexc('fff2d0'), 1.5)
    glow(img, cx, cy, S * 0.25, 'ffd0a0', 0.6)
    for i in range(10):
        y = S * (0.6 + i * 0.035); w = S * (0.16 - i * 0.012)
        blob(img, [(cx - w, y), (cx + w, y), (cx + w, y + 3), (cx - w, y + 3)], hexc('ffe0c0'), 1.0, 0.5)
    return img


def _bubble(S):
    img = vgrad(S, S, [(0, 'eef2ff'), (1, 'd8e0ff')])
    blob(img, [(S * 0.12, S * 0.25), (S * 0.88, S * 0.25), (S * 0.88, S * 0.68), (S * 0.4, S * 0.68), (S * 0.26, S * 0.82), (S * 0.28, S * 0.68), (S * 0.12, S * 0.68)], hexc('5a6aff'), 1.0)
    glow(img, S * 0.3, S * 0.3, S * 0.3, 'ffffff', 0.2)
    return img


def _page(S):
    img = vgrad(S, S, [(0, 'f7f2e6'), (1, 'efe6d2')])
    rng = np.random.default_rng(4)
    for r in range(9):
        y = S * (0.14 + r * 0.085)
        blob(img, [(S * 0.08, y), (S * 0.92, y), (S * 0.92, y + 1.2), (S * 0.08, y + 1.2)], hexc('b8c8e0'), 0.0)
        x = S * 0.1
        while x < S * (0.86 - 0.2 * (r % 3 == 2)):
            w = S * rng.uniform(0.03, 0.09)
            pts = [(x + w * i / 6, y - 6 - 5 * math.sin(i * 1.9 + r)) for i in range(7)]
            for i in range(6):
                a, b = np.array(pts[i]), np.array(pts[i + 1])
                d = b - a; n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6) * 1.4
                blob(img, [a + n, b + n, b - n, a - n], hexc('2a2c48'), 0.0)
            x += w + S * 0.02
        if r == 4:
            blob(img, [(S * 0.12, y - 8), (S * 0.6, y - 9), (S * 0.6, y - 6), (S * 0.12, y - 5)], hexc('2a2c48'), 0.0)   # crossed out
    return img


KINDS = {'sunset': _sunset, 'cake': _cake, 'catsuit': _catsuit, 'breadhouse': _breadhouse, 'teacup': _teacup,
         'waterfall': _waterfall, 'quote': _quote, 'strawberry': _strawberry, 'castle': _castle, 'chart': _chart,
         'heartsun': _heartsun, 'bubble': _bubble, 'page': _page}
ORDER = [kk for kk in KINDS if kk != 'page']
_CACHE = {}


BASE = 768


def image(kind, size=512):
    key = (kind, size)
    if key not in _CACHE:
        if (kind, BASE) not in _CACHE:
            im = KINDS[kind](BASE)
            _CACHE[(kind, BASE)] = np.clip(sheen(im), 0, 1).astype(F32)
        base = _CACHE[(kind, BASE)]
        _CACHE[key] = base if size == BASE else cv2.resize(base, (size, size), interpolation=cv2.INTER_AREA)
    return _CACHE[key]
