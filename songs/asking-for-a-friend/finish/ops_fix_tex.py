from PIL import Image, ImageDraw, ImageFont
import math
S="/System/Library/Fonts/Supplemental/"
W,H=640,880
im=Image.new("RGB",(W,H),(246,240,226)); d=ImageDraw.Draw(im)
f1=ImageFont.truetype(S+"Impact.ttf",78); f2=ImageFont.truetype(S+"Courier New Bold.ttf",34); f3=ImageFont.truetype(S+"Courier New.ttf",28)
d.rectangle([0,0,W,120],fill=(40,60,70)); d.text((36,22),"INVOICE",font=f1,fill=(245,240,226))
d.text((36,150),"BILL TO: A. CUSTOMER",font=f2,fill=(40,40,40))
y=230
for a,b in (("Seat licence","$ 12.00"),("Seat licence","$ 12.00"),("Overage fee","$ 38.50"),("Late fee","$ 9.00"),("Convenience fee","$ 4.99")):
    d.text((36,y),a,font=f3,fill=(60,60,60)); d.text((400,y),b,font=f3,fill=(60,60,60)); d.line([36,y+38,W-36,y+38],fill=(180,175,160),width=2); y+=58
d.text((36,y+20),"TOTAL DUE   $ 76.49",font=f2,fill=(30,30,30))
st=Image.new("RGBA",(420,150),(0,0,0,0)); sd=ImageDraw.Draw(st)
sd.rounded_rectangle([4,4,416,146],18,outline=(190,40,40,235),width=10); sd.text((40,34),"PAID",font=ImageFont.truetype(S+"Impact.ttf",96),fill=(190,40,40,235))
st=st.rotate(14,expand=True,resample=Image.BICUBIC); im.paste(st,(150,610),st)
im.save("ops_fix/invoice_sheet.png")
# manila stack side (page edges): fine stripes
e=Image.new("RGB",(64,256),(236,228,206)); ed=ImageDraw.Draw(e)
for i in range(0,256,4): ed.line([0,i,64,i],fill=(205,196,172),width=1)
e.save("ops_fix/page_edges.png")
