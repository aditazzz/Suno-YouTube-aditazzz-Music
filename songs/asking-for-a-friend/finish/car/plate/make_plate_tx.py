"""make_plate_tx.py  (studio python). Texas-style plate texture -> plate/plate_texas.png (text from PLATE_TEXT.txt, the one variable).
Generic Texas look: white plate, dark-blue TEXAS header with lone stars, black plate text, thin red/blue rule, small slogan line.
No dealer/brand marks. Text fit-checked with studio.textfit."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../..")))   # repo root (studio.textfit)
from PIL import Image, ImageDraw, ImageFont
from studio import textfit
HERE = os.path.dirname(os.path.abspath(__file__)); FD = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../..")), "assets", "fonts") + "/"
BLUE = (22, 40, 100); RED = (176, 30, 44); INK = (14, 14, 18)
def star(d, cx, cy, r, fill):
    import math
    pts = [(cx + (r if i % 2 == 0 else r * .4) * math.sin(i * math.pi / 5), cy - (r if i % 2 == 0 else r * .4) * math.cos(i * math.pi / 5)) for i in range(10)]
    d.polygon(pts, fill=fill)
def draw(text, W=1160, H=340):
    im = Image.new("RGB", (W, H), (244, 243, 238)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, W - 7, H - 7), 22, outline=BLUE, width=8)
    d.rectangle((14, 14, W - 15, 22), fill=(0, 0, 0, 0)) if False else None
    rec = textfit.Recorder((W, H), name="plate_texas", pad=8)
    if True:
        with rec.container((130, 28, W - 130, 104), "header"):
            textfit.fit_text(d, "TEXAS", (130, 28, W - 130, 104), ImageFont.truetype(FD + "Anton-Regular.ttf", 76), min_px=40, pad=8, fill=BLUE, align="m", valign="m", recorder=rec)
        with rec.container((60, 100, W - 60, 268), "plate text"):
            textfit.fit_text(d, text, (60, 100, W - 60, 268), ImageFont.truetype(FD + "InterDisplay-Black.otf", 190), min_px=60, pad=10, fill=INK, align="m", valign="m", recorder=rec)
        with rec.container((200, 276, W - 200, 322), "slogan"):
            textfit.fit_text(d, "THE LONE STAR STATE", (200, 276, W - 200, 322), ImageFont.truetype(FD + "InterDisplay-Bold.otf", 34), min_px=30, pad=4, fill=RED, align="m", valign="m", recorder=rec)
    rec.assert_ok(); rec.save(HERE)
    star(d, 92, 66, 30, BLUE); star(d, W - 92, 66, 30, BLUE)
    d.rectangle((40, 268, W - 40, 272), fill=BLUE)
    star(d, 130, 299, 14, RED); star(d, W - 130, 299, 14, RED)
    return im
if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else open(os.path.join(HERE, "PLATE_TEXT.txt")).read().strip()
    draw(text).save(os.path.join(HERE, "plate_texas.png")); print("plate_texas", text)
