import sys
from PIL import Image, ImageDraw
files=sys.argv[2:]
cols=2
ims=[Image.open(f).resize((960,540)) for f in files]
rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(960*cols,540*rows),(40,40,40))
d=ImageDraw.Draw(sheet)
for i,(im,f) in enumerate(zip(ims,files)):
    x,y=(i%cols)*960,(i//cols)*540
    sheet.paste(im,(x,y)); d.text((x+8,y+8),f.split('_')[-1],fill=(255,80,80))
sheet.save(sys.argv[1])
