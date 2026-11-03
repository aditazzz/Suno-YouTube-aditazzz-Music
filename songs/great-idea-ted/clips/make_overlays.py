# the subscribe asks for the 16:9 master, drawn by the studio's own core (subscribe pill after the first chorus,
# end card over the last seconds), written as RGBA PNGs so they composite onto the clean three.js master.
import os, sys, numpy as np, cv2
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')); sys.path.insert(0, ROOT)   # the repo root
from studio import core as C
W, H, FPS = int(sys.argv[1]), int(sys.argv[2]), 30
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overlay', f'{W}x{H}'); os.makedirs(OUT, exist_ok=True)
PILL_T, END_T, END = 57.0, 260.2, 266.92
def layer(t, fn):
    a = np.zeros((H, W, 3), np.float32); b = np.ones((H, W, 3), np.float32); fn(a, t); fn(b, t)
    al = np.clip(1 - (b - a).mean(axis=2), 0, 1); col = np.where(al[..., None] > 1e-4, a / np.maximum(al[..., None], 1e-4), 0)
    return np.dstack([np.clip(col, 0, 1)[..., ::-1] * 255, al * 255]).astype(np.uint8)   # BGRA for cv2
pill = lambda img, t: C.subscribe_pill(img, t, W, H, PILL_T, 5.0)
card = lambda img, t: C.end_screen(img, t, W, H, END_T, END - END_T, "To subscribe, raise your hand.", None, title="Great Idea, Ted")
ONLY = sys.argv[3] if len(sys.argv) > 3 else None
for name, t0, t1, fn in (('pill', PILL_T, PILL_T + 5.0, pill), ('end', END_T, END, card)):
    if ONLY and name != ONLY: continue
    ns = range(round(t0 * FPS), round(t1 * FPS) + 1)
    if os.environ.get('TEST'): ns = [round((t0 + 1.0) * FPS), round((t0 + 3.0) * FPS)]
    for n in ns:
        f = os.path.join(OUT, f'{name}_{n:05d}.png')
        if os.path.exists(f) and os.path.getsize(f) > 0 and not os.environ.get('TEST'): continue   # resumable
        cv2.imwrite(f + '.tmp.png', layer(n / FPS, fn)); os.replace(f + '.tmp.png', f)
print('ok', OUT)
