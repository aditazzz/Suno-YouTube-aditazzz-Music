"""The lens finish for stills, the same as the final's encode path: 16-bit PNG -> shadow grain (seeded by frame) ->
8-bit PNG (the grain is the dither). python3 finish_still.py <in.png> <frame> <out.png> [--grain 1.0]"""
import sys, numpy as np, cv2
src, f, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
gr = float(sys.argv[sys.argv.index("--grain") + 1]) if "--grain" in sys.argv else 1.0
im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
x = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
h, w = x.shape[:2]
rng = np.random.default_rng(1000003 * f + 17)
g = cv2.GaussianBlur(rng.standard_normal((h, w), dtype=np.float32), (0, 0), 0.65); g /= g.std() + 1e-6
lum = x[..., ::-1] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
amp = gr * (0.0035 + 0.016 * np.clip(1.0 - lum, 0, 1) ** 2.2)
y = np.clip(x + (g * amp)[..., None], 0, 1)
cv2.imwrite(dst, (y * 255.0 + 0.5).astype(np.uint8))
