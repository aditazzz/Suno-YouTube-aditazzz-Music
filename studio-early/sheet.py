import sys
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
cols = 2
ims = [Image.open(f).resize((960, 540)) for f in files]
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (960 * cols, 540 * rows), (40, 40, 40))
d = ImageDraw.Draw(sh)
for i, (im, f) in enumerate(zip(ims, files)):
    x, y = (i % cols) * 960, (i // cols) * 540
    sh.paste(im, (x, y)); d.text((x + 8, y + 8), f.split('_')[-1], fill=(255, 80, 80))
sh.save(out)
