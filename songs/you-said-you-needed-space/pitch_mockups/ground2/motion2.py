"""Ground v2, 2.5D motion test from the ONE still render (CPU): a slow push-in with parallax by depth (the passes are
re-projected with their own depth map; the soft foreground layer zooms faster; the sky does not move), motes drifting,
mist sheets sliding, a slow wave of light through the veins.   motion2.py <passes.npz> <frames_dir> [seconds] [fps]"""
import sys, os, numpy as np, cv2
from PIL import Image
from scipy.ndimage import minimum_filter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comp2
src = dict(np.load(sys.argv[1])); outdir = sys.argv[2]; SEC = float(sys.argv[3]) if len(sys.argv) > 3 else 4.5; FPS = int(sys.argv[4]) if len(sys.argv) > 4 else 24
os.makedirs(outdir, exist_ok=True)
W, H = 1280, 720
d0 = {k: cv2.resize(v.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST if k == 'z_main' else cv2.INTER_AREA) for k, v in src.items()}
comp2.PUSH = 0.055 / SEC; comp2.GRAIN = 0.004
zn = minimum_filter(np.where(d0['z_main'] > 1e3, 60.0, d0['z_main']), 9)        # nearest depth wins at edges: leaves stay whole, the stretch falls in the soft background
Y, X = np.mgrid[0:H, 0:W].astype(np.float32); cx, cy = W / 2, H / 2
N = int(SEC * FPS)
for i in range(N):
    t = i / FPS; m = comp2.PUSH * t
    k = zn / np.maximum(zn - m, 0.2)
    mx = (cx + (X - cx) / k).astype(np.float32); my = (cy + (Y - cy) / k).astype(np.float32)
    d = {'rgba_main': cv2.remap(d0['rgba_main'], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE),
         'emit_main': cv2.remap(d0['emit_main'], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE),
         'z_main': cv2.remap(d0['z_main'], mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE) - m}
    kf = 0.5 / (0.5 - m)
    A = np.array([[kf, 0, cx * (1 - kf)], [0, kf, cy * (1 - kf)]], np.float32)
    d['rgba_fg'] = cv2.warpAffine(d0['rgba_fg'], A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    o = comp2.frame(d, t, stats=(i in (0, N - 1)))
    Image.fromarray(o).save(f'{outdir}/f{i:04d}.png', compress_level=1)
print('frames', N, outdir)
