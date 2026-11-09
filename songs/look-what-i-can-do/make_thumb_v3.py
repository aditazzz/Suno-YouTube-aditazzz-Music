"""Look What I Can Do v3 thumbnail options: like the approved v2 cover, the hook in the frame IS the headline, so the
brand layer is only the "Made with Claude Opus 5.5" credit under it. One option per hook moment of the v3 film.
  python3 songs/look-what-i-can-do/make_thumb_v3.py <src_dir> <out_dir>   (src_dir holds src_A.png ... src_D.png)"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from studio import brand

# option: (zoom, zoom centre, credit centre x, credit top y in the source frame, credit size scale)
OPTS = {"A": (1.04, (945, 560), 945, 958, 1.45),     # 256 of her videos spell the hook over the city at blue hour
        "B": (1.10, (960, 470), 960, 532, 1.0),     # the hook in gilded embers over the Viking hall's fire
        "D": (1.18, (960, 540), 960, 760, 1.0)}     # the swarm writes it in light


def credit(im, cx, y, size):
    f = brand.F("JBMono-700.ttf", size); t = f"Made with {brand.MODEL}"
    x = cx - f.getlength(t) / 2
    shd = Image.new("L", im.size, 0); ImageDraw.Draw(shd).text((x + 3, y + 5), t, font=f, fill=235, stroke_width=9, stroke_fill=235)
    im.paste((0, 0, 0), (0, 0), shd.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(im).text((x, y), t, font=f, fill=brand.WHITE, stroke_width=4, stroke_fill=brand.OUTLINE)
    return im


def neon(im, color=(255, 61, 240)):
    """Her round-3 note on A: the letters made of video rooms are hard to read, so trace each letter with a neon tube."""
    import numpy as np, cv2
    a = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2GRAY).astype(np.float32); H = a.shape[0]
    mu = cv2.blur(a, (9, 9)); sd = np.sqrt(np.maximum(cv2.blur(a * a, (9, 9)) - mu * mu, 0))
    m = (sd > 14).astype(np.uint8) * 255; m[int(H * 0.80):] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m); k = np.zeros_like(m)
    for i in range(1, n):
        if st[i, 4] > 9000: k[lab == i] = 255
    k = (cv2.GaussianBlur(k, (0, 0), 6) > 127).astype(np.uint8) * 255                      # smooth the tile edges into strokes
    inv = 255 - k; n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv)                  # fill pinholes (gaps between tiles), keep real counters
    for i in range(1, n2):
        if st2[i, 4] < 6000: k[lab2 == i] = 255
    k = cv2.dilate(k, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))                 # the tube sits just outside the tiles
    edge = cv2.morphologyEx(k, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))).astype(np.float32) / 255
    f = np.asarray(im).astype(np.float32); c = np.array(color, np.float32)
    glow = cv2.GaussianBlur(edge, (0, 0), 14)[..., None]; glow = glow / max(glow.max(), 1e-6)
    f = f * (1 - 0.55 * glow) + c * 0.55 * glow * 1.6                                         # soft coloured halo
    e = edge[..., None]; f = f * (1 - e) + (c * 0.35 + 255 * 0.65) * e                        # hot white-pink core
    return Image.fromarray(np.clip(f, 0, 255).astype(np.uint8))


src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
for k, (s, (zx, zy), cx, cy, sc) in OPTS.items():
    im = Image.open(os.path.join(src, f"src_{k}.png")).convert("RGB").resize((brand.W, brand.H), Image.LANCZOS)
    if k == "A": im = neon(im)
    w, h = brand.W / s, brand.H / s; x0 = min(max(0, zx - w / 2), brand.W - w); y0 = min(max(0, zy - h / 2), brand.H - h)
    im = im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((brand.W, brand.H), Image.LANCZOS)
    im = credit(im, (cx - x0) * s, (cy - y0) * s, int(brand.CREDIT_SIZE * sc * 1.1))
    im.resize((1280, 720), Image.LANCZOS).save(os.path.join(out, f"thumb_{k}.jpg"), quality=92)
print("ok")
