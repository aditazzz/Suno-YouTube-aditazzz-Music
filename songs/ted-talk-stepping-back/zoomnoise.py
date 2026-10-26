"""Zoomable fractal noise: the same world-anchored pattern at any scale, with the octaves that would alias at the
current zoom faded out. Used for land cover, clouds and nebulae, so a pattern seen at one scale is still the same
pattern a power of ten later."""
import math
from functools import lru_cache
import numpy as np, cv2

F32 = np.float32
N = 512                                     # tile size (texels)

@lru_cache(None)
def tile(seed):
    """tileable smooth noise in [0,1]: a few frequencies inside one tile."""
    rng = np.random.default_rng(seed); acc = np.zeros((N, N), np.float64); tot = 0.0
    for k, a in ((4, 1.0), (8, 0.55), (16, 0.3)):
        g = rng.random((k, k))
        gp = np.concatenate([g[:, -3:], g, g[:, :3]], 1); gp = np.concatenate([gp[-3:], gp, gp[:3]], 0)
        s = N / k; up = cv2.resize(gp, (int(round((k + 6) * s)), int(round((k + 6) * s))), interpolation=cv2.INTER_CUBIC)
        o = int(round(3 * s)); acc += up[o:o + N, o:o + N] * a; tot += a
    acc /= tot; acc = (acc - acc.min()) / (acc.max() - acc.min())
    return acc.astype(F32)

def octave_sample(X, Y, wavelength, seed, i):
    """sample tile `seed` with feature size ~wavelength (world units) at world coords X, Y (float64 arrays)."""
    T = tile(seed); per = wavelength * 4.0                      # the tile holds 4 features across
    ang = 0.7 + i * 1.3; c, s = math.cos(ang), math.sin(ang)    # each octave rotated + offset: no grid alignment
    xr = X * c - Y * s; yr = X * s + Y * c
    u = np.mod(xr / per + i * 0.371, 1.0) * N; v = np.mod(yr / per + i * 0.619, 1.0) * N
    sh = u.shape
    if u.ndim != 2: u = u.reshape(1, -1); v = v.reshape(1, -1)
    return cv2.remap(T, u.astype(F32), v.astype(F32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP).reshape(sh)

def fbm(X, Y, px_world, seed=1, lam_max=1e5, lam_min=1.0, gain=0.55, px_cut=3.0):
    """sum of octaves from lam_max down to lam_min (halving); octaves whose features are smaller than ~px_cut pixels
    (px_world = world units per pixel) fade out. Normalised over ALL octaves, so the amplitude is the same at every zoom.
    Returns values roughly in [0,1] centred on 0.5."""
    out = np.zeros(X.shape, F32); amp = 1.0; tot = 0.0; lam = lam_max; i = 0
    while lam >= lam_min:
        feat_px = lam / max(px_world, 1e-12)
        w = np.clip((feat_px - px_cut) / px_cut, 0, 1)            # fade between px_cut and 2*px_cut pixels
        if w > 0: out += (octave_sample(X, Y, lam, seed, i) - 0.5) * (amp * w)
        else: out += 0.0
        tot += amp; amp *= gain; lam *= 0.5; i += 1
    return out / max(tot, 1e-9) * 1.6 + 0.5
