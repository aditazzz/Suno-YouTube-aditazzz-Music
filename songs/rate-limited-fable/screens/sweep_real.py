"""Sweep every frame of every real-device layer in build/screens_real (rl_screensreal; sweep.py logic, warnings as errors)
no pixel above the white ceiling (no blown highlights), and the biggest frame-to-frame jump per layer (pops) with where it is.
  .venv/bin/python songs/rate-limited/screens/sweep.py     -> build/screens/sweep.json (+ prints; exit 1 on a FAIL)"""
import glob, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K

OUT = os.path.join(K.SONG, 'build', 'screens_real')
SEQS = sorted(set(os.path.dirname(p) for p in glob.glob(os.path.join(OUT, '*', '*', 'f_*.png'))))
rep = {}; fails = []
for d in SEQS:
    name = os.path.relpath(d, OUT); files = sorted(glob.glob(os.path.join(d, 'f_*.png')))
    nums = [int(os.path.basename(f)[2:7]) for f in files]
    missing = sorted(set(range(nums[0], nums[-1] + 1)) - set(nums)) if nums else []
    prev = None; jumps = []; maxv = 0; blank = []
    for f, n in zip(files, nums):
        a = np.asarray(Image.open(f).convert('RGBA').resize((320, int(320 * Image.open(f).height / Image.open(f).width))), dtype=np.float32)
        full = np.asarray(Image.open(f).convert('RGBA'))
        rgb = full[..., :3][full[..., 3] > 8] if full[..., 3].min() < 255 else full[..., :3].reshape(-1, 3)
        if rgb.size: maxv = max(maxv, int(rgb.max()))
        if not np.isfinite(a).all(): fails.append(f'{name} f{n}: non-finite')
        lum = (a[..., :3].mean(-1) * a[..., 3] / 255)
        if a[..., 3].max() < 8 and 'sleep' not in name and 'height' not in name and 'highlight' not in name and 'overlay' not in name and 'glass_' not in name:
            blank.append(n)
        if full[..., 3].min() == 255 and lum.mean() < 3: blank.append(n)
        if prev is not None:
            jumps.append((float(np.abs(a - prev).mean()), n))
        prev = a
    jumps.sort(reverse=True)
    rep[name] = dict(frames=[nums[0], nums[-1]] if nums else None, count=len(nums), missing=missing, blank=blank, max_rgb=maxv, top_jumps=jumps[:3])
    if missing: fails.append(f'{name}: missing frames {missing[:6]}')
    if blank: fails.append(f'{name}: blank frames {blank[:6]}')
    if maxv > K.WHITE_MAX + 1 and 'height' not in name: fails.append(f'{name}: pixel {maxv} above the white ceiling {K.WHITE_MAX}')
    print(f'{name:34s} {len(nums):4d} frames  max_rgb {maxv:3d}  biggest jump {jumps[0][0] if jumps else 0:.1f} at f{jumps[0][1] if jumps else -1}', flush=True)
json.dump(dict(layers=rep, fails=fails), open(os.path.join(OUT, 'sweep.json'), 'w'), indent=1)
print('FAILS:' if fails else 'sweep: PASS', *fails, sep='\n  ')
sys.exit(1 if fails else 0)
