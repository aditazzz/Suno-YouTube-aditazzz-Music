"""him_clip_preview.py: the acting clip's RGBA frames over a still plate (the bridge sky, old drawing painted out), with the
same comp as the stills. Preview only.  .venv/bin/python him_clip_preview.py <png dir> <plate.png> <out dir>"""
import cv2, glob, os, sys, numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import him_comp

def one(a):
    f, plate, out = a; o = os.path.join(out, os.path.basename(f))
    him_comp.comp({'plate': plate, 'him': f, 'out': o}); return o

if __name__ == '__main__':
    src, plate, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    p = cv2.imread(plate).astype(np.float32) / 255; p = him_comp.paint_out(p, (700, 0, 1960, 900))
    clean = os.path.join(out, '_plate_clean_1080.png'); cv2.imwrite(clean, cv2.resize(np.clip(p * 255 + 0.5, 0, 255).astype(np.uint8), (1920, 1080), interpolation=cv2.INTER_AREA))
    with Pool(8) as pool: pool.map(one, [(f, clean, out) for f in sorted(glob.glob(os.path.join(src, 'him_*.png')))])
