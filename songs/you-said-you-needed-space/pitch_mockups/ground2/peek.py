"""Quick look at the raw passes: beauty | fg / emit | depth.  peek.py <prefix.npz> <out.jpg>"""
import sys, numpy as np
from PIL import Image
d = np.load(sys.argv[1]); H, W = d['z_main'].shape
def tm(x, k=1.0):
    x = np.clip(x.astype(np.float32) * k, 0, None); return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1) ** (1 / 2.2)
def over(rgba, bgc=(0.01, 0.02, 0.05)):
    rgba = rgba.astype(np.float32); return rgba[..., :3] + np.array(bgc, np.float32) * (1 - rgba[..., 3:4])
tiles = [tm(over(d['rgba_main'])), tm(over(d['rgba_fg'])) if 'rgba_fg' in d else np.zeros((H, W, 3)), tm(d['emit_main']),
         np.repeat(np.clip(1.0 / np.maximum(d['z_main'], 0.3) / 1.2, 0, 1)[..., None], 3, -1)]
s = Image.new('RGB', (1600, 900))
for i, t in enumerate(tiles):
    s.paste(Image.fromarray((t * 255).astype(np.uint8)).resize((800, 450), Image.LANCZOS), ((i % 2) * 800, (i // 2) * 450))
s.save(sys.argv[2], quality=86)
m = d['rgba_main'].astype(np.float32); print('beauty max', m[..., :3].max(), 'p99', np.percentile(m[..., :3], 99), 'alpha mean', m[..., 3].mean(), 'z range', d['z_main'].min(), np.percentile(d['z_main'][d['z_main'] < 1e3], 99))
