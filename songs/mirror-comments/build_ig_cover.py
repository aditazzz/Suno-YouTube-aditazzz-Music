"""Instagram (under 3 min) cover for Mirror, Mirror - The Comment Section, with the mirror image as the picture.

The whole mirror from the cover art (bulbs, frame, vanity table) at full width, its face between the hook and the
title pill, over a soft blurred extension of the same image; the text is the same as the other covers.
usage: python3 songs/mirror-comments/build_ig_cover.py <out.jpg> [--no-text]
"""
import sys, os
import numpy as np, cv2
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # songs/<slug>/ -> repo root
os.chdir(ROOT); sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tools"))
from studio.config import load_song, public_name
import reel_covers as RC

W, H = 1080, 1920
song = load_song("songs/mirror-comments")
art = np.asarray(Image.open("songs/mirror-comments/assets/cover_clean.png").convert("RGB")).astype(np.float32)

S = 1500                      # the square art at 1500 px: its frame (16%..84% of the width) fits inside 1080
EYES, Y_EYES = 0.39, 905      # the eyes (39% down the art) sit just under the hook block
y0 = int(Y_EYES - EYES * S); x0 = (W - S) // 2
fg = cv2.resize(art, (S, S), interpolation=cv2.INTER_LANCZOS4)

# backdrop: the same image filling the frame, blurred and darkened, so the margins above and below aren't a box
bs = H
bg = cv2.resize(art, (bs, bs), interpolation=cv2.INTER_AREA)[:, (bs - W) // 2:(bs - W) // 2 + W]
bg = cv2.GaussianBlur(bg, (0, 0), 38) * 0.5

canvas = bg.copy(); mask = np.zeros((H, W), np.float32)
ys, ye = max(0, y0), min(H, y0 + S); xs, xe = max(0, x0), min(W, x0 + S)
canvas[ys:ye, xs:xe] = fg[ys - y0:ye - y0, xs - x0:xe - x0]; mask[ys:ye, xs:xe] = 1
f = 60                                                            # feather the top and bottom edges of the picture
ramp = np.ones(H, np.float32)
for y in range(H):
    d = min(y - ys, ye - 1 - y)
    ramp[y] = np.clip(d / f, 0, 1) if ys <= y < ye else 0
m = (mask * ramp[:, None])[..., None]
out = np.clip(canvas * m + bg * (1 - m), 0, 255).astype(np.uint8)

img = Image.fromarray(out)
if "--no-text" not in sys.argv:
    img = RC.cover(img, public_name(song), "ANIMATED THIS", "#4da3ff", lines=song.get("thumb_lines"), sub=song.get("thumb_sub"))
img.save(sys.argv[1], quality=92)
print("wrote", sys.argv[1], img.size)
