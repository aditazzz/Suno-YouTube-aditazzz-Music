"""Her: a woman in a long camel coat with long dark hair, seen from behind, looking down at her phone.

She lives in billboard space: metres, x right, y up, feet at (0, 0). draw() renders her (colour + alpha) at any scale;
mask() gives the silhouette that casts her shadow. Poses: scroll (head down, phone up), down (phone lowered), turn
(0 = back to us, 1 = profile facing right), walk (stride phase).
"""
import math
from dataclasses import dataclass
import numpy as np, cv2
from studio.core import hexc

F32 = np.float32
AA = cv2.LINE_AA
HAIR = hexc('2a1c16'); HAIR_HI = hexc('6a4632'); COAT = hexc('c99a69'); COAT_SH = hexc('8e6748'); COAT_HI = hexc('ecc497')
LEGS = hexc('1c1a1f'); SKIN = hexc('d9a988')


@dataclass
class Pose:
    head: float = 1.0      # 1 = looking down at the phone, 0 = up
    phone: float = 1.0     # 1 = phone held up in front, 0 = lowered
    turn: float = 0.0      # 0 = back to us, 1 = profile (facing right)
    walk: float = 0.0      # stride amount
    phase: float = 0.0


def spline(pts, n=8, closed=True):
    P = np.asarray(pts, F32)
    P = np.vstack([P[-1:], P, P[:2]]) if closed else np.vstack([P[:1], P, P[-1:]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            s = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    return np.array(out, F32)


def mirror(half):
    return list(half) + [(-u, v) for u, v in reversed(half[1:-1])]


def parts(p):
    """Polygons (metres) for each part, back view; the side view squeezes and shifts things as she turns."""
    sq = 1 - 0.45 * p.turn                                  # a turned body is narrower
    hd = 0.035 * p.head                                     # head bows forward: from behind it sinks a little
    el = 0.03 * p.phone                                     # elbows out when the phone is up
    sw = math.sin(p.phase) * p.walk
    coat = mirror([(0.0, 1.455), (0.075, 1.452), (0.15, 1.44), (0.205, 1.415), (0.222, 1.36), (0.228 + el, 1.25),
                   (0.236 + el, 1.14), (0.226 + el, 1.075), (0.186, 1.035), (0.168, 0.99), (0.178, 0.90), (0.196, 0.78),
                   (0.208, 0.62), (0.218, 0.47), (0.0, 0.455)])
    hair = mirror([(0.0, 1.715 - hd), (0.058, 1.705 - hd), (0.094, 1.66 - hd), (0.106, 1.59 - hd), (0.112, 1.50),
                   (0.126, 1.42), (0.128, 1.30), (0.122, 1.19), (0.10, 1.12), (0.05, 1.095), (0.0, 1.09)])
    legs = []
    for s in (-1, 1):
        k = s * sw
        top = (s * 0.062, 0.50); knee = (s * 0.062 + 0.02 * k, 0.27 + 0.03 * max(0, k)); ank = (s * 0.058 + 0.05 * k, 0.07 + 0.06 * max(0, k))
        legs.append((top, knee, ank))
    T = lambda poly: [(u * sq + 0.03 * p.turn, v) for u, v in poly]
    return T(coat), T(hair), [((a[0] * sq, a[1]), (b[0] * sq, b[1]), (c[0] * sq, c[1])) for a, b, c in legs]


def _fill(m, pts, sc, ox, oy, val=1.0):
    P = np.asarray(pts, F32)
    q = np.stack([ox + P[:, 0] * sc, oy - P[:, 1] * sc], 1)
    cv2.fillPoly(m, [np.round(q * 4).astype(np.int32)], val, AA, shift=2)


def _limb(m, a, b, c, w0, w1, sc, ox, oy, val=1.0):
    P = spline([a, b, c], 6, False)
    n = len(P); L, R = [], []
    for i in range(n):
        d = P[min(n - 1, i + 1)] - P[max(0, i - 1)]; d = d / (np.linalg.norm(d) + 1e-6)
        nr = np.array([-d[1], d[0]]); w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        L.append(P[i] + nr * w); R.append(P[i] - nr * w)
    _fill(m, L + R[::-1], sc, ox, oy, val)


def mask(p, sc, size):
    """Silhouette (float, [0,1]) in a square canvas of `size` px; sc px per metre; feet at the bottom centre."""
    m = np.zeros((size, size), F32)
    ox, oy = size / 2, size - size * 0.04
    coat, hair, legs = parts(p)
    for a, b, c in legs:
        _limb(m, a, b, c, 0.10, 0.072, sc, ox, oy)
        _fill(m, [(c[0] - 0.05, 0.0), (c[0] + 0.05, 0.0), (c[0] + 0.045, 0.075), (c[0] - 0.045, 0.075)], sc, ox, oy)
    _fill(m, spline(coat, 6), sc, ox, oy)
    _fill(m, spline(hair, 6), sc, ox, oy)
    return m


def draw(p, sc, light=1.0, warm=1.0, night=0.0):
    """Colour + alpha of her, lit from behind the camera by low sun (warm) or by the city at night."""
    size = int(sc * 2.0) + 8
    ox, oy = size / 2, size - size * 0.04
    coat, hair, legs = parts(p)
    rgb = np.zeros((size, size, 3), F32); a = np.zeros((size, size), F32)
    def paint(m, col):
        nonlocal rgb
        rgb = rgb * (1 - m[..., None]) + m[..., None] * col
        np.maximum(a, m, out=a)
    lm = np.zeros((size, size), F32)
    for (aa, bb, cc) in legs:
        _limb(lm, aa, bb, cc, 0.10, 0.072, sc, ox, oy)
        _fill(lm, [(cc[0] - 0.05, 0.0), (cc[0] + 0.05, 0.0), (cc[0] + 0.045, 0.075), (cc[0] - 0.045, 0.075)], sc, ox, oy)
    paint(lm, LEGS)
    cm = np.zeros((size, size), F32); _fill(cm, spline(coat, 6), sc, ox, oy)
    # coat: lit from behind us and a little from the left; rounder at the edges
    xs = (np.arange(size, dtype=F32)[None, :] - ox) / (0.22 * sc)
    ys = (oy - np.arange(size, dtype=F32)[:, None]) / sc
    shade = np.clip(1.0 - 0.55 * np.clip(xs, 0, 1) ** 2 - 0.25 * np.clip(-xs, 0, 1) ** 3, 0, 1)
    coat_col = COAT_SH[None, None] * (1 - shade[..., None]) + COAT[None, None] * shade[..., None]
    coat_col = coat_col * (0.92 + 0.08 * np.clip((ys - 0.5) / 1.0, 0, 1))[..., None]
    paint(cm, coat_col)
    # seams: the back vent and a belt
    det = np.zeros((size, size), F32)
    cv2.line(det, (int(ox + 0.03 * p.turn * sc), int(oy - 0.98 * sc)), (int(ox + 0.03 * p.turn * sc), int(oy - 0.47 * sc)), 1.0, max(1, int(sc * 0.006)), AA)
    cv2.line(det, (int(ox - 0.17 * sc), int(oy - 1.0 * sc)), (int(ox + 0.17 * sc), int(oy - 1.0 * sc)), 1.0, max(1, int(sc * 0.016)), AA)
    rgb = rgb * (1 - det[..., None] * cm[..., None] * 0.35) + (det * cm)[..., None] * COAT_SH * 0.35
    # hair with a soft sheen down the middle
    hm = np.zeros((size, size), F32); _fill(hm, spline(hair, 6), sc, ox, oy)
    sheen = np.exp(-((xs * 0.22 * sc / (0.06 * sc)) + 0.4) ** 2) * np.clip((ys - 1.15) / 0.5, 0, 1)
    paint(hm, HAIR[None, None] * (1 - sheen[..., None] * 0.5) + HAIR_HI[None, None] * sheen[..., None] * 0.5)
    # light: golden rim on the left edges, cool fill at night
    edge = cv2.morphologyEx((a * 255).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(F32) / 255
    left = np.clip(-xs * 0.6 + 0.4, 0, 1)
    rgb += (edge * left * a)[..., None] * hexc('ffd49a') * 0.35 * light * warm
    rgb *= (0.55 + 0.45 * light)
    if night > 0: rgb = rgb * (1 - night * 0.55) + night * 0.55 * rgb * hexc('8fa0ff')
    return np.concatenate([rgb, a[..., None]], -1), ox, oy
