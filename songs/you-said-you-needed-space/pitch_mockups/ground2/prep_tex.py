from pathlib import Path
ROOT = str(Path(__file__).resolve().parents[4]) + "/"
"""Ground v2, step 1 (CPU): glow masks read from each Poly Haven plant's OWN textures (CC0), so veins and edges carry
the light and the leaf body stays dark.  Writes <out>/<plant>_glow.png  (R = fine veins, G = broad soft bands for the
translucency, B = edge band) and <out>/<plant>_alpha.png (leaf cut-out, from the roughness channel of the ARM map; the
fern's jpg has no alpha of its own).   prep_tex.py <outdir>"""
import sys, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter as gf, distance_transform_edt as edt, binary_opening, binary_closing
LIB = ROOT + 'assets/earth_library/polyhaven/models/'
out = sys.argv[1]


def load(m, k):
    return np.asarray(Image.open(f'{LIB}{m}/textures/{m}_{k}_2k.jpg').convert('RGB')).astype(np.float32) / 255


def norm(x, p=99.5):
    return np.clip(x / max(np.percentile(x, p), 1e-6), 0, 1)


def make(m, g_cut, vein_s, band_s, edge_px, vein_gain=1.0):
    d = load(m, 'diff'); n = load(m, 'nor_gl'); arm = load(m, 'arm')
    leaf = arm[..., 1] < g_cut                       # the padding is a flat high-roughness fill, the leaf is not
    leaf = binary_closing(binary_opening(leaf, iterations=1), iterations=2)
    lum = d @ np.array([0.25, 0.6, 0.15], np.float32)
    # fine veins: narrow ridges of the albedo (pale vein lines) + narrow ridges of the normal map (the raised veins)
    v_l = np.clip(gf(lum, vein_s * 0.6) - gf(lum, vein_s * 2.5), 0, None)
    nx = n[..., 0] - gf(n[..., 0], vein_s * 2.5); ny = n[..., 1] - gf(n[..., 1], vein_s * 2.5)
    v_n = gf(np.hypot(nx, ny), vein_s * 0.5)
    vein = norm(v_l) * 0.65 + norm(v_n) * 0.55
    vein = np.clip((vein - 0.16) / 0.55, 0, 1) ** 1.2 * vein_gain
    # broad bands: the plant's own stripe pattern, soft (drives how much light comes THROUGH the leaf)
    band = norm(np.clip(gf(lum, band_s * 0.5) - gf(lum, band_s * 3), -1, None) + 0.02, 99)
    band = np.clip(band, 0, 1)
    # edge: a thin band just inside the outline
    dist = edt(leaf)
    edge = np.exp(-(dist / edge_px) ** 1.3) * leaf
    lf = gf(leaf.astype(np.float32), 0.8)
    rgb = np.stack([np.clip(vein, 0, 1) * lf, band * lf, edge], -1)
    Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(f'{out}/{m}_glow.png')
    Image.fromarray((np.clip(lf, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'{out}/{m}_alpha.png')
    print(m, 'leaf %.1f%%' % (leaf.mean() * 100), 'vein mean %.3f' % vein[leaf].mean(), 'edge %.3f' % edge[leaf].mean())
    return rgb, lf


a, la = make('calathea_orbifolia_01', 0.62, 2.2, 9.0, 7.0)
b, lb = make('fern_02', 0.86, 1.6, 5.0, 2.2, vein_gain=1.1)
s = Image.new('RGB', (1600, 800))
for i, (x, l) in enumerate(((a, la), (b, lb))):
    s.paste(Image.fromarray((x * 255).astype(np.uint8)).resize((400, 400), Image.LANCZOS), (i * 800, 0))
    s.paste(Image.fromarray((l * 255).astype(np.uint8)).resize((400, 400)).convert('RGB'), (i * 800 + 400, 0))
s.paste(Image.fromarray((a[300:700, 300:700] * 255).astype(np.uint8)), (0, 400))
s.paste(Image.fromarray((a[300:700, 300:700, 0] * 255).astype(np.uint8)).convert('RGB'), (400, 400))
s.paste(Image.fromarray((b[200:600, 250:650] * 255).astype(np.uint8)), (800, 400))
s.paste(Image.fromarray((b[200:600, 250:650, 0] * 255).astype(np.uint8)).convert('RGB'), (1200, 400))
s.save(f'{out}/../look1_masks.jpg', quality=85)

# ---- the root web for the ground: thin ridges of the Poly Haven `roots` displacement map (the raised roots), as lines
R = ROOT + 'assets/earth_library/polyhaven/textures/roots/roots_disp_2k.jpg'
h = np.asarray(Image.open(R).convert('L')).astype(np.float32) / 255
fine = np.clip(gf(h, 1.2, mode='wrap') - gf(h, 5, mode='wrap'), 0, None); thick = np.clip(gf(h, 3, mode='wrap') - gf(h, 14, mode='wrap'), 0, None)
web = np.clip((norm(fine, 99.7) - 0.22) / 0.5, 0, 1) * 0.8 + np.clip((norm(thick, 99.7) - 0.35) / 0.5, 0, 1) * 0.7
web = np.clip(web, 0, 1) ** 1.3
Image.fromarray((web * 255 + 0.5).astype(np.uint8)).save(f'{out}/roots_web.png')
print('roots web: %.1f%% above 0.5' % ((web > 0.5).mean() * 100))
Image.fromarray((web[:800, :800] * 255).astype(np.uint8)).save(f'{out}/../look1b_web.jpg', quality=80)

# ---- calathea midribs: tracked per leaf on the albedo (R = soft nearness to the midrib, G = the midrib line itself)
from scipy.ndimage import label, median_filter
d = load('calathea_orbifolia_01', 'diff'); arm = load('calathea_orbifolia_01', 'arm')
lum = d @ np.array([0.25, 0.6, 0.15], np.float32)
leafm = binary_opening(arm[..., 1] < 0.62, iterations=6)
lab, nlab = label(leafm); sizes = np.bincount(lab.ravel()); sizes[0] = 0
resp = gf(lum, (10, 1.6)) - gf(lum, (10, 7))
mid = np.zeros(lum.shape + (2,), np.float32); XX = np.arange(lum.shape[1], dtype=np.float32)
for k in np.argsort(sizes)[::-1][:4]:
    m = lab == k; rows = np.where(m.any(1))[0]; cols = np.where(m.any(0))[0]
    cx = np.array([np.where(m[r])[0].mean() for r in rows]); wd = np.array([m[r].sum() for r in rows]).astype(np.float32)
    c0 = float(np.median(cx)); wmax = float(wd.max()); path = []
    for r in rows:
        a_, b_ = int(c0 - 0.10 * wmax), int(c0 + 0.10 * wmax)
        path.append(a_ + int(np.argmax(resp[r, a_:b_])))
    path = gf(median_filter(np.array(path, np.float32), 41), 12)
    for r, pc, w in zip(rows, path, wd):
        dx = np.abs(XX - pc)
        mid[r, :, 0] = np.maximum(mid[r, :, 0], np.exp(-(dx / (0.20 * wmax)) ** 2) * m[r])
        mid[r, :, 1] = np.maximum(mid[r, :, 1], np.exp(-(dx / 2.6) ** 2) * m[r])
    print('midrib leaf', k, 'x %.0f +- %.0f' % (path.mean(), path.std()), 'rows', len(rows))
Image.fromarray((np.dstack([mid, np.zeros(lum.shape, np.float32)]) * 255 + 0.5).astype(np.uint8)).save(f'{out}/calathea_orbifolia_01_mid.png')
