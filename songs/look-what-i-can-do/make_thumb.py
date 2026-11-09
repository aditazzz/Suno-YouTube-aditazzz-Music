"""Look What I Can Do thumbnail: her pick, the final-chorus frame where the hook is a constellation over a galaxy of her
videos. The constellation is the headline (like ted-talk-charts, whose banner is its headline), so the brand layer is
just the "Made with Claude Opus 5.5" credit, centred under it.
  python3 songs/look-what-i-can-do/make_thumb.py <frame.jpg> <out_dir>"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from studio import brand

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
base = Image.open(src).convert("RGB").resize((brand.W, brand.H), Image.LANCZOS)
CX, TEXT_BOTTOM = 960, 410          # the constellation's centre line and the bottom of "I CAN DO" in the 1080p frame


def credit(im, y, size=brand.CREDIT_SIZE):
    f = brand.F("JBMono-700.ttf", size); t = f"Made with {brand.MODEL}"
    w = f.getlength(t); x = CX - w / 2 if im.width == brand.W else (im.width - w) / 2
    shd = Image.new("L", im.size, 0); ImageDraw.Draw(shd).text((x + 3, y + 5), t, font=f, fill=235, stroke_width=9, stroke_fill=235)
    im.paste((0, 0, 0), (0, 0), shd.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(im).text((x, y), t, font=f, fill=brand.WHITE, stroke_width=4, stroke_fill=brand.OUTLINE)
    return im


def crop(im, s, cy):    # zoom s about (CX, cy), back to 1920x1080
    w, h = brand.W / s, brand.H / s; x0 = CX - w / 2; y0 = min(max(0, cy - h / 2), brand.H - h)
    return im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((brand.W, brand.H), Image.LANCZOS), y0, s

a = credit(base.copy(), TEXT_BOTTOM + 34)
a.save(os.path.join(out, "thumb_A_as_picked.jpg"), quality=94)
b, y0, s = crop(base, 1.3, 420)
b = credit(b, (TEXT_BOTTOM - y0) * s + 40, size=int(brand.CREDIT_SIZE * 1.1))
b.save(os.path.join(out, "thumb_B_closer.jpg"), quality=94)
print("ok")
