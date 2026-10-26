import sys, glob
from PIL import Image
out=sys.argv[1]; files=sys.argv[2:]
n=len(files); cols=2; rows=(n+1)//2
S=Image.new("RGB",(cols*960,rows*540))
for i,f in enumerate(files):
    S.paste(Image.open(f).resize((960,540),Image.LANCZOS),((i%cols)*960,(i//cols)*540))
S.save(out, quality=88)
