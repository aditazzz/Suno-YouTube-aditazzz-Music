import sys
from PIL import Image, ImageDraw
out=sys.argv[1]; files=sys.argv[2:]
S=Image.new("RGB",(3*800,((len(files)+2)//3)*450),(60,0,0))
for i,f in enumerate(files):
    im=Image.open(f).resize((800,450),Image.LANCZOS)
    ImageDraw.Draw(im).text((6,4), f.split("_")[-1][:-4], fill=(255,80,80))
    S.paste(im,((i%3)*800,(i//3)*450))
S.save(out, quality=86)
