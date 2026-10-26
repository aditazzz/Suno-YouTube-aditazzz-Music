import lgtm as L
from PIL import Image
t = 36.2
f = Image.new("RGB", (L.W, L.H), L.BG)
f.paste(Image.fromarray(L.diff_layer(t, 0.42)), (L.DX0, 0))
L.add_light(f, L.RAYS, 0, 0, 1.0)
L.window_layer(f, t, 1.0, 1.0, 1.0, 1.25)
L.choir_layer(f, 150.0, 1.0)
for i, sp in enumerate(L.LETTERS):
    L.paste_c(f, sp, L.LETX[i], 440, 1.0)
st = L.STAMP0.resize((440, 220), Image.LANCZOS).rotate(-9, expand=True, resample=Image.BICUBIC)
L.paste_c(f, st, 1580, 160, 1.0)
L.paste(f, L.SCRIM, 0, 0, 1.0)
font = L.F(L.CORM, 118)
sp = L.text_sprite("I did not read a single line", font, L.IVORY)
L.paste_c(f, sp, L.W / 2, 950, 1.0)
f.save("out/LGTM_thumbnail_full.png")
f.resize((1280, 720), Image.LANCZOS).save("out/LGTM_thumbnail.png")
f.resize((320, 180), Image.LANCZOS).save("out/LGTM_thumbnail_small.png")
