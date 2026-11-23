#!/usr/bin/env python3
"""Cut 7 (PLAN7 §2): split one approved plate into 3-5 depth slices for the Remotion SliceCam (2.5D parallax).

  .venv/bin/python songs/rate-limited/tools/slice_plate.py <plate.jpg|png> --depth <depth> --out <pack dir>
        [--n 4 | --cuts z1,z2,...] [--far-white] [--mask name=<png> ...] [--bleed 24] [--max-w 5760] [--preview]

Inputs
  plate   the approved still (any size; the pack keeps its pixel size, capped at --max-w).
  bands   cut at the emptiest valleys of the depth histogram (a surface at one depth is never split; fewer bands if no clean valley);
          --cuts z1,z2 forces them.
  depth   the SAME scene and camera's depth: a 16-bit/8-bit PNG, .npy or .exr (Blender Z or Mist pass).
          Default: larger value = farther (Z / Mist). --far-white is the same thing said explicitly; --near-white flips it
          (an inverted normalised map). Background/sky with no hit (inf / 0 alpha) counts as farthest.
  --mask  name=<png>: force a region (white) into its own slice (e.g. her=..., him=...); it is placed at its median depth.
          Use it for characters so a Breathe/Jitter/Blink layer can address them: the slice is called `name`.
Out (<pack dir>):
  s0.png (the back: opaque, the occluded areas filled by push-pull from its own band) ... sN-1.png (RGBA, nearest last),
  pack.json: {"w", "h", "plate": "<copied plate name>", "slices": [{"src", "name", "z", "par", "bbox"}]}, back to front.
  `par` = parallax factor 0 (back) .. 1 (nearest) from 1/z, normalised; SliceCam multiplies it into the camera move.
Every front slice carries a --bleed px (default 24) edge-extended skirt into the area nearer slices cover (alpha 1 there,
colour pushed out from its own pixels), so a relative slice offset up to the bleed never shows a hole (SliceCam limits the
offset to 1.5% of the frame = 38 stage px at 2560 wide; the skirt is in plate px, so at 5760 wide 24 px = 11 stage px:
pass --bleed 64 for 5760-wide plates).
--preview writes preview.jpg: the slices shifted by +-1.5% of the width (the worst case SliceCam allows) so holes show.
"""
import argparse, json, shutil
from pathlib import Path
import numpy as np
import cv2


def load_depth(p, w, h):
    p = Path(p)
    if p.suffix == '.npy':
        d = np.load(p).astype(np.float32)
    else:
        if p.suffix.lower() == '.exr':
            import os; os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
        d = cv2.imread(str(p), cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH)
        if d is None: raise SystemExit(f'cannot read depth {p}')
        if d.ndim == 3: d = d[..., 2] if d.shape[2] >= 3 else d[..., 0]   # BGR(A): R channel holds Z/Mist
        d = d.astype(np.float32)
    d[~np.isfinite(d)] = np.nan
    if d.shape[:2] != (h, w): d = cv2.resize(d, (w, h), interpolation=cv2.INTER_NEAREST)
    big = np.nanmax(d) if np.isfinite(np.nanmax(d)) else 1.0
    d[np.isnan(d)] = big * 1.0001
    return d


def valley_cuts(inv, n):
    """n-1 cut values in 1/z at the emptiest valleys of the depth histogram, so a surface at one depth (a box front, a wall) is never
    split across two slices (quantile cuts tore the 4H labels in two). Falls back to fewer bands when there are no clean valleys."""
    v = inv[np.isfinite(inv)].ravel()
    lo, hi = np.percentile(v, 0.2), np.percentile(v, 99.8)
    if hi <= lo: return []
    hist, edges = np.histogram(np.clip(v, lo, hi), bins=400, range=(lo, hi))
    k = np.exp(-0.5 * (np.arange(-9, 10) / 3.0) ** 2); hs = np.convolve(hist.astype(float), k / k.sum(), mode='same')
    tot = hs.sum(); cands = []
    for i in range(3, len(hs) - 3):
        if hs[i] <= hs[i - 1] and hs[i] <= hs[i + 1]:
            left, right = hs[:i].max(), hs[i + 1:].max()
            share = hs[:i].sum() / tot
            if 0.03 < share < 0.97: cands.append((hs[i] / max(1e-9, min(left, right)), i))
    cands.sort(); picked = []
    for score, i in cands:
        if score > 0.35: break                                   # not a real valley: stop (fewer, cleaner bands)
        if all(abs(i - j) > 12 for j in picked): picked.append(i)
        if len(picked) == n - 1: break
    return sorted(edges[i] + (edges[1] - edges[0]) / 2 for i in picked)


def push_pull(rgb, a):
    """fill rgb where a==0 from the a>0 pixels (pyramid push-pull); returns float32 rgb"""
    levels = []; c = rgb * a[..., None]; w = a.copy()
    while min(w.shape) > 4:
        levels.append((c, w))
        c = cv2.resize(c, (max(1, c.shape[1] // 2), max(1, c.shape[0] // 2)), interpolation=cv2.INTER_AREA)
        w = cv2.resize(w, (max(1, w.shape[1] // 2), max(1, w.shape[0] // 2)), interpolation=cv2.INTER_AREA)
    fill = c / np.maximum(w, 1e-6)[..., None]
    for c0, w0 in reversed(levels):
        up = cv2.resize(fill, (c0.shape[1], c0.shape[0]), interpolation=cv2.INTER_LINEAR)
        k = np.clip(w0, 0, 1)[..., None]
        fill = np.where(w0[..., None] > 1e-3, c0 / np.maximum(w0, 1e-6)[..., None], up) * k + up * (1 - k)
    return fill


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('plate'); ap.add_argument('--depth', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=4); ap.add_argument('--cuts')
    ap.add_argument('--far-white', action='store_true'); ap.add_argument('--near-white', action='store_true')
    ap.add_argument('--mask', action='append', default=[]); ap.add_argument('--bleed', type=int, default=24)
    ap.add_argument('--max-w', type=int, default=5760); ap.add_argument('--preview', action='store_true')
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    img = cv2.imread(a.plate, cv2.IMREAD_COLOR)
    if img is None: raise SystemExit(f'cannot read plate {a.plate}')
    if img.shape[1] > a.max_w:
        s = a.max_w / img.shape[1]; img = cv2.resize(img, (a.max_w, round(img.shape[0] * s)), interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]; rgb = img.astype(np.float32)
    d = load_depth(a.depth, w, h)
    if a.near_white: d = d.max() - d + 1e-3
    d = np.maximum(d, 1e-3)

    # bands: by --cuts (depth values) or quantiles of 1/z (parallax-uniform bands)
    inv = 1.0 / d
    if a.cuts:
        cuts = sorted(float(x) for x in a.cuts.split(','))
        band = np.digitize(d, cuts)          # 0 = nearest
        band = band.max() - band             # 0 = farthest
    else:
        qs = valley_cuts(inv, a.n)
        band = np.digitize(inv, qs)          # 0 = farthest (smallest 1/z)
    nb = int(band.max()) + 1
    names = [f'd{k}' for k in range(nb)]
    # forced masks: their own bands, placed in order of median depth
    forced = []
    for m in a.mask:
        nm, p = m.split('=', 1)
        mk = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        mk = cv2.resize(mk, (w, h), interpolation=cv2.INTER_LINEAR) > 127
        forced.append((nm, mk, float(np.median(inv[mk])) if mk.any() else 0.0))
    # assemble the ordered layer list: (name, membership mask, mean inv depth)
    layers = []
    taken = np.zeros((h, w), bool)
    for nm, mk, _ in forced: taken |= mk
    for k in range(nb):
        mk = (band == k) & ~taken
        if mk.sum() > 0.0005 * w * h: layers.append((names[k], mk, float(inv[mk].mean())))
        elif mk.any() and layers: layers[-1] = (layers[-1][0], layers[-1][1] | mk, layers[-1][2])
        elif mk.any(): layers.append((names[k], mk, float(inv[mk].mean())))
    layers += [(nm, mk, iv) for nm, mk, iv in forced]
    layers.sort(key=lambda l: l[2])
    ivs = [l[2] for l in layers]; lo, hi = ivs[0], ivs[-1]
    meta = []
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * a.bleed + 1, 2 * a.bleed + 1))
    for i, (nm, mk, iv) in enumerate(layers):
        m8 = mk.astype(np.uint8)
        near_all = np.zeros((h, w), bool)
        for _, mk2, _ in layers[i + 1:]: near_all |= mk2
        # pixels within 3 px of anything nearer were anti-aliased against it (its dark edge): rebuilt from further in, never kept
        ring = (cv2.dilate(near_all.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) & ~near_all
        if i == 0:
            # the back: opaque; everything nearer (and the ring around it) is filled from the back band's own clean pixels
            src_ok = mk & ~ring
            col = push_pull(rgb, src_ok.astype(np.float32)); col = np.where(src_ok[..., None], rgb, col)
            alpha = np.ones((h, w), np.float32)
        else:
            nearer = np.zeros((h, w), bool)
            for _, mk2, _ in layers[i + 1:]: nearer |= mk2
            skirt = (cv2.dilate(m8, kern) > 0) & nearer & ~mk
            hard = mk | skirt
            # edge decontamination: the member's outermost 2 px carry the background they were anti-aliased against (a dark
            # cut-out outline once the slice moves), so colour comes from the eroded interior and alpha ends 1 px inside the member
            core = (cv2.erode(m8, np.ones((5, 5), np.uint8)) > 0) & ~ring
            col = push_pull(rgb, core.astype(np.float32)); col = np.where(core[..., None], rgb, col)
            hard = (cv2.erode(m8, np.ones((3, 3), np.uint8)) > 0) | skirt
            alpha = cv2.GaussianBlur(hard.astype(np.float32), (0, 0), 0.9)
            # keep the member pixels exactly opaque except a 1 px soft rim on the outer (non-skirt) edge
            alpha[core | skirt] = 1.0
        rgba = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
        ys, xs = np.where(alpha > 0.01)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else [0, 0, w, h]
        src = f's{i}.png' if i else 's0.jpg'
        if i == 0: cv2.imwrite(str(out / src), rgba[..., :3], [cv2.IMWRITE_JPEG_QUALITY, 94])
        else: cv2.imwrite(str(out / src), rgba, [cv2.IMWRITE_PNG_COMPRESSION, 6])
        par = 0.0 if hi == lo else (iv - lo) / (hi - lo)
        meta.append({'src': src, 'name': nm, 'z': round(1.0 / iv, 4), 'par': round(par, 4), 'bbox': bbox})
    shutil.copy(a.plate, out / ('plate' + Path(a.plate).suffix.lower()))
    (out / 'pack.json').write_text(json.dumps({'w': w, 'h': h, 'plate': 'plate' + Path(a.plate).suffix.lower(), 'bleed': a.bleed,
                                               'slices': meta}, indent=1))
    print(f'{out}: {len(meta)} slices ' + ', '.join(f"{m['name']} par {m['par']:.2f}" for m in meta))
    if a.preview:
        sh = int(0.015 * w); canvas = np.zeros((h, w, 3), np.float32)
        for m in meta:
            p = cv2.imread(str(out / m['src']), cv2.IMREAD_UNCHANGED).astype(np.float32)
            if p.shape[2] == 3: p = np.dstack([p, np.full(p.shape[:2], 255, np.float32)])
            dx = int(round((m['par'] - 0.5) * 2 * sh))
            p = np.roll(p, dx, axis=1); al = p[..., 3:4] / 255
            canvas = canvas * (1 - al) + p[..., :3] * al
        pv = cv2.resize(canvas, (1600, round(1600 * h / w)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(out / 'preview.jpg'), pv.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == '__main__':
    main()
