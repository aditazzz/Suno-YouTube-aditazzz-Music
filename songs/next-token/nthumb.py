import nt as N
from PIL import Image
t = 58.9
f = Image.new("RGB", (N.W, N.H), N.BG)
N.tunnel_layer(f, t, 1.0)
sp = N.halo(N.text_sprite("I don't know the answer", N.F(N.CORM, 150), N.IVORY), 26, 1.8)
N.paste_c(f, sp, N.W / 2, 330, 1.0)
words = ["I", "know", "what", "comes", "next"]
chips = [N.big_chip(w, w == "next") for w in words]
gap = 22
tw = sum(c.width for c in chips) + gap * (len(chips) - 1)
x = (N.W - tw) / 2
nextpos = None
for w, c in zip(words, chips):
    if w == "next": nextpos = x
    else: N.paste(f, c, x, 560, 1.0)
    x += c.width + gap
# the runner-up guesses under the chosen token
fm = N.F(N.MONO, 40)
lx = x - chips[-1].width - gap + 6
for j, (w, p, col) in enumerate((("next", "0.99", N.IVORY), ("true", "0.01", N.DIM), ("after", "0.00", N.FAINT))):
    N.txt(f, w, fm, col, lx, 750 + j * 54)
    N.txt(f, p, fm, col, lx + 300, 750 + j * 54, 1.0, "r")
f = N.bloom(f, 0.8)
N.paste(f, chips[-1], nextpos, 560, 1.0)
f.save("out/NextToken_thumbnail_full.png")
f.resize((1280, 720), Image.LANCZOS).save("out/Next_Token_thumbnail.png")
f.resize((320, 180), Image.LANCZOS).save("out/Next_Token_thumbnail_small.png")
