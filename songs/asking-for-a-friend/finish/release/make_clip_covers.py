"""Per-clip 9:16 covers (Short 2, Short 3, Instagram edit) through the brand pipeline, the same way as
finish/thumb/make_covers.py's Short cover: two-line Anton "ASKING FOR / A FRIEND" (last line amber) + "Made with <model>",
in the 9:16 safe zone's top band (13%..43%), over a clean frame of the clip (the 9:16 cuts carry no lyrics or hook pill).
tools/clip_covers.py is not used: it draws the CLAUDE ANIMATED THIS badge her Oct 31 rule removed, and needs a Python scene.
python3 make_clip_covers.py   -> <out_dir>/Asking for a Friend - Covers/<clip> - cover.jpg + textfit json in build/finals_release/textfit"""
import sys, os, json, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../..")); sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tools")
import numpy as np
from PIL import Image, ImageDraw
from studio import brand, textfit
from studio.config import load_song
S = ROOT + "/songs/asking-for-a-friend"; song = load_song(S); O = song["out_dir"]; OD = O + "/Asking for a Friend - Covers/"
TF = S + "/build/finals_release/textfit/"; os.makedirs(TF, exist_ok=True); os.makedirs(OD, exist_ok=True)
MODEL = song.get("model_credit", "Claude Opus 5.5")
ITEMS = [  # cover for, source file, frame in that file, slide down (fraction of H)
    # Short 2's own frames put the headline over Claude's head; its lyric is "with my finger on deploy", so its cover is the
    # DEPLOY lamp close-up (S133, film 3:31.3), taken from the edit (frame 3223). The edit itself gets the Porsche hero cover.
    ("Asking for a Friend - Short 2 (The Ghost Is Self-Employed, 22s).mp4", "Asking for a Friend - Instagram 9x16 (under 3 min).mp4", 3223, 0.0),
    ("Asking for a Friend - Short 3 (Do Not Call 911, 23s).mp4", "Asking for a Friend - Short 3 (Do Not Call 911, 23s).mp4", 137, 0.0),
]
W, H = 1080, 1920
BASE = dict(HEAD_SIZE=184, BOTTOM=56, SUB_SIZE=88, MX=64, MY=56, CREDIT_SIZE=60, TAG_SIZE=46, TAG_H=96)
for n, v in BASE.items(): setattr(brand, n, v)
brand.W, brand.H = W, H; brand.MX = int(W * 0.09) + 28; brand.CREDIT_SIZE = 52
lh = int(brand.HEAD_SIZE * 1.04); slh = int(brand.CREDIT_SIZE * 1.12); block_h = 2 * lh + slh + 10 + 18
brand.BOTTOM = H - int(H * 0.15) - block_h
from clip_covers import shift_down

class NoShadow:
    def __init__(s, rec): s.rec = rec
    def __enter__(s):
        s.orig = ImageDraw.ImageDraw.text; rec, orig = s.rec, s.orig
        def t2(d, *a, **k):
            if getattr(d, "mode", None) == "L" or getattr(getattr(d, "im", None), "mode", None) == "L": rec.paused = True
            try: return orig(d, *a, **k)
            finally: rec.paused = False
        ImageDraw.ImageDraw.text = t2
    def __exit__(s, *a): ImageDraw.ImageDraw.text = s.orig

log = {}
for f, src, fr, sy in ITEMS:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", O + "/" + src, "-vf", f"select=eq(n\\,{fr})", "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
    a = shift_down(a, sy).astype(np.float32) / 255
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    a *= 1 - 0.55 * np.clip((0.46 - yy) / 0.46, 0, 1) ** 0.8          # soft shade behind the headline, none lower down
    pic = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    zone = (int(W * 0.09), int(H * 0.13), int(W * 0.91), int(H * 0.43))
    name = os.path.splitext(f)[0].replace("Instagram 9x16", "Instagram") + " - cover"
    with textfit.Recorder(image_size=(W, H), name="aff_" + name.split(" - ")[1].replace(" ", "_")) as rec, NoShadow(rec):
        with rec.container(zone, "9:16 safe zone top band"):
            im = brand.brand_cover(pic, ["ASKING FOR", "A FRIEND"], None, "left", brand.ACCENTS["amber"], None, MODEL)
    rec.save(TF)
    try: rec.assert_ok(); ok = "PASS"
    except Exception as e: ok = "FAIL " + str(e)[:300]
    p = OD + name + ".jpg"; im.save(p, quality=92); log[name] = {"file": p, "frame": fr, "shift": sy, "bytes": os.path.getsize(p), "textfit": ok}
    print(name, os.path.getsize(p), ok, flush=True)
# the Instagram edit (the main IG post): the Porsche hero Short cover (thumb_porsche, brand pipeline, text-fit PASS there)
pc = OD + "Asking for a Friend - Instagram (under 3 min) - cover.jpg"
Image.open(OD + "Short cover.png").convert("RGB").save(pc, quality=92); log["Instagram edit"] = {"file": pc, "from": "Short cover.png (thumb_porsche T1 9:16)"}
json.dump(log, open(S + "/build/finals_release/clip_covers_log.json", "w"), indent=1)
