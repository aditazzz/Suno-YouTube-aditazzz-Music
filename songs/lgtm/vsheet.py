import sys
from PIL import Image
out=sys.argv[1]; files=sys.argv[2:]
cols=4; rows=(len(files)+cols-1)//cols
S=Image.new("RGB",(cols*486,rows*864),(40,0,0))
for i,f in enumerate(files):
    S.paste(Image.open(f).resize((486,864),Image.LANCZOS),((i%cols)*486+0,(i//cols)*864))
S.save(out, quality=88)
