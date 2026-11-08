"""make_plate.py [TEXT] [out.png]  (studio python). TEXT defaults to plate/PLATE_TEXT.txt. Writes plate/plate.png (the texture
car/plate.py puts on the GT3 RS rear) and records TEXT in PLATE_TEXT.txt: the ONE variable her pick swaps in.
Also: make_plate.py --strip  -> plate/options_strip.png (every option from plate/options.txt drawn as a plate)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../..")), "assets", "fonts", "InterDisplay-Black.otf")
def draw(text, W=1160, H=340):
    im = Image.new("RGB", (W, H), (236, 233, 222)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, W - 9, H - 9), 26, outline=(24, 40, 82), width=10)
    d.rounded_rectangle((34, 34, W - 35, H - 35), 14, outline=(24, 40, 82), width=3)
    f = ImageFont.truetype(FONT, 250); sp = 40
    ws = [d.textlength(c, font=f) for c in text]; tw = sum(ws) + sp * (len(text) - 1)
    k = min(1.0, (W - 150) / tw)
    if k < 1: f = ImageFont.truetype(FONT, int(250 * k)); ws = [d.textlength(c, font=f) for c in text]; tw = sum(ws) + sp * (len(text) - 1)
    x = (W - tw) / 2
    for c, w in zip(text, ws):
        d.text((x, H / 2 + 8), c, font=f, fill=(20, 34, 78), anchor="lm"); x += w + sp
    return im
if __name__ == "__main__":
    if sys.argv[1:2] == ["--strip"]:
        opts = [l.strip() for l in open(os.path.join(HERE, "options.txt")) if l.strip()]
        W, H, pad = 1160, 340, 40; lab = ImageFont.truetype(os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../..")), "assets", "fonts", "Inter-SemiBold.otf"), 44)
        S = Image.new("RGB", (2 * W + 3 * pad, 3 * (H + 110) + pad), (24, 24, 28)); d = ImageDraw.Draw(S)
        for i, o in enumerate(opts):
            t, note = o.split("|"); x = pad + (i % 2) * (W + pad); y = pad + (i // 2) * (H + 110)
            S.paste(draw(t), (x, y)); d.text((x, y + H + 16), "%d. %s" % (i + 1, note), font=lab, fill=(235, 235, 235))
        S = S.resize((S.width // 2, S.height // 2), Image.LANCZOS); S.save(os.path.join(HERE, "options_strip.png")); print("strip", S.size); sys.exit()
    tp = os.path.join(HERE, "PLATE_TEXT.txt")
    text = sys.argv[1] if len(sys.argv) > 1 else open(tp).read().strip()
    open(tp, "w").write(text + "\n"); draw(text).save(os.path.join(HERE, "plate.png")); print("plate", text)
