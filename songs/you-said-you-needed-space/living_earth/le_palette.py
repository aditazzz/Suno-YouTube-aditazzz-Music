"""Earth palette + colourist grade (earth_palette, creative director, Nov 9 2026; QA gate 7). Source of truth for
PALETTE.md's numbers. The grade is per-pixel in display space (after ACES + sRGB), so it is baked exactly into one 3D LUT
per section and applied to rendered masters by living_earth/le_grade.py (no re-render).
  .venv/bin/python living_earth/le_palette.py      -> build/palette/palette.json + build/palette/lut/earth_<section>.cube (65^3)
Change a number here, re-run, re-grade: nothing else to touch."""
import json, os, colorsys, numpy as np
SW = {  # name: (hex, owner, role)
 'Biolume':     ('#2FE0E8', 'her', 'BASE A: her light. veins, rivers, coasts, her glow, thread home'),
 'Ember':       ('#FF8A3D', 'his', 'BASE B: his light. rocket spark/trail, satellite rim, his joke props (rack, luggage, boxes), his crammed stars'),
 'Aurora':      ('#8E63F5', 'her', 'her accent: oceans deeps, aurora curtains, atmosphere outer edge, her shadows'),
 'Filament':    ('#FFD49A', 'his', 'his highlight: city windows (Black Marble), chip seated, gold star glitter'),
 'Overheat':    ('#FF4B2B', 'his', 'ONLY "no atmosphere": his satellite overheating'),
 'Dusk Rose':   ('#E89BB5', 'seam', 'ONLY the dusk line + sunrise rim (thin)'),
 'Star Ivory':  ('#F2ECE1', 'neutral', 'star-type, the Elon post, numerals, star cores, top highlight'),
 'Night Navy':  ('#0A1022', 'neutral', 'night-side relief, mid shadows'),
 'Deep Space':  ('#04060E', 'neutral', 'black point: no pixel darker'),
}
def hx(h): return np.array([int(h[i:i+2],16) for i in (1,3,5)])/255
def hue(h): return colorsys.rgb_to_hsv(*hx(h))[0]*360
SEC = [  # name, t0, t1, params (display space)
 ('cold open', 0.0, 17.706),
 ('verse 1', 17.706, 35.816),
 ('pre/chorus 1', 35.816, 83.354),
 ('verse 2', 83.354, 112.782),
 ('chorus 2', 112.782, 149.002),
 ('bridge', 149.002, 176.167),
 ('final chorus/countdown', 176.167, 212.386),
 ('houston/end', 212.386, 217.6),
]
BASE = dict(lift=[0.020,0.022,0.052], gamma=1.0, gain=[1.0,1.0,1.0], sat=1.0, satMax=0.80, tealToCyan=0.5, cyanHue=186.0,
            blueToViolet=0.6, violetHue=258.0, hiTint=[1.035,1.0,0.93], hiAmt=0.35, shTint=[0.96,0.98,1.08], shAmt=0.0,
            knee=0.80, ceil=0.955, warmKeep=1.35, xfade=0.5)
P = {
 'cold open':   dict(blueToViolet=0.35, satMax=0.78, ceil=0.94, hiAmt=0.25, gamma=1.0),
 'verse 1':     dict(blueToViolet=0.5, satMax=0.76, tealToCyan=0.55, hiAmt=0.35),
 'pre/chorus 1':dict(blueToViolet=0.55, satMax=0.80, hiAmt=0.40, gamma=1.03),
 'verse 2':     dict(blueToViolet=0.5, satMax=0.74, tealToCyan=0.25, hiAmt=0.30, gamma=1.04),
 'chorus 2':    dict(blueToViolet=0.6, satMax=0.80, tealToCyan=0.60, hiAmt=0.40, gamma=1.02),
 'bridge':      dict(blueToViolet=0.75, satMax=0.72, tealToCyan=0.50, hiAmt=0.30, lift=[0.024,0.020,0.058], ceil=0.94),
 'final chorus/countdown': dict(blueToViolet=0.6, satMax=0.84, tealToCyan=0.55, hiAmt=0.40, gamma=1.02),
 'houston/end': dict(blueToViolet=0.45, satMax=0.78, hiAmt=0.55, hiTint=[1.05,1.0,0.90], knee=0.74, ceil=0.94, gamma=0.98),
}
def params(name):
  d=dict(BASE); d.update(P[name]); return d
def smooth(a,b,x): t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
def rgb2hsv(x):
  r,g,b=x[...,0],x[...,1],x[...,2]; mx=x.max(-1); mn=x.min(-1); d=mx-mn+1e-8
  h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60
  s=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-8),0); return h,s,mx
def hsv2rgb(h,s,v):
  c=v*s; hp=(h%360)/60; xx=c*(1-np.abs(hp%2-1)); z=np.zeros_like(h); m=v-c
  conds=[(hp<1,(c,xx,z)),(hp<2,(xx,c,z)),(hp<3,(z,c,xx)),(hp<4,(z,xx,c)),(hp<5,(xx,z,c)),(hp<=6,(c,z,xx))]
  r=np.zeros_like(h); g=np.zeros_like(h); b=np.zeros_like(h)
  for cond,(a1,a2,a3) in reversed(conds): r=np.where(cond,a1,r); g=np.where(cond,a2,g); b=np.where(cond,a3,b)
  return np.stack([r+m,g+m,b+m],-1)
def grade(x, p):
  """x: HxWx3 display-referred 0..1 (after ACES+sRGB). Returns graded."""
  h,s,v=rgb2hsv(x)
  # 1 teal -> her cyan: pull greenish teals (150..184) toward cyanHue (kills muddy green-teal, keeps forest green < 140)
  # (lit pixels only: bright teals AND bright azures 190..204 join one clean cyan cluster)
  bw=smooth(140,156,h)*(1-smooth(200,208,h))*smooth(0.10,0.22,v); h=h+p['tealToCyan']*bw*(p['cyanHue']-h)*0.7
  # 2 dark blues -> her violet: shadow/mid blues (204..240) rotate toward violetHue, weighted to the darks
  # (the dim azure/navy mass 196..238 -> deep indigo-violet: cyan vs indigo instead of cyan vs more-cyan)
  bv=smooth(203,213,h)*(1-smooth(244,256,h))*(1-smooth(0.25,0.55,v)); h=h+p['blueToViolet']*bv*(p['violetHue']-h)
  # 3 saturation, soft-limited at satMax (no neon)
  # 2b his warm is protected: warm hues (5..72) get warmKeep x saturation and skip the cool black point below
  ww=smooth(5,15,h)*(1-smooth(60,72,h))*smooth(0.04,0.12,s)
  s=s*(1+(p['warmKeep']-1)*ww)
  s=s*p['sat']; m=p['satMax']; k=0.72*m; s=np.where(s>k,k+(m-k)*(1-np.exp(-(s-k)/(m-k))),s)
  y=hsv2rgb(h,s,v)
  L=(y*[0.2126,0.7152,0.0722]).sum(-1,keepdims=True)
  # 4 split tone: shadows cool (navy/violet), highlights warm (ivory): ONE direction, warm top -> cool bottom
  ht=np.array(p['hiTint']); ht=ht/(ht*[0.2126,0.7152,0.0722]).sum(); st=np.array(p['shTint']); st=st/(st*[0.2126,0.7152,0.0722]).sum()
  wh=smooth(0.50,0.95,L)*p['hiAmt']; ws=(1-smooth(0.04,0.35,L))*p['shAmt']
  y=y*(1-wh+wh*ht); y=y*(1-ws+ws*st)
  # 5 gamma, gain, black point (lift = the darkest colour any pixel can be)
  y=np.clip(y,0,None)**(1/p['gamma'])*np.array(p['gain'])
  lift=np.array(p['lift'])*(1-0.9*ww[...,None]); y=lift+(1-lift)*y
  # 6 highlight shoulder: nothing above ceil (exposure gate: luma 250 can't be reached)
  kn,c=p['knee'],p['ceil']; y=np.where(y>kn,kn+(c-kn)*(1-np.exp(-(y-kn)/(c-kn))),y)
  return np.clip(y,0,1)
if __name__=='__main__':
  out=dict(swatches={k:dict(hex=v[0],hue=round(hue(v[0])),owner=v[1],role=v[2]) for k,v in SW.items()},
           sections=[dict(name=n,t0=a,t1=b,grade=params(n)) for n,a,b in SEC])
  BD=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'build','palette'); os.makedirs(os.path.join(BD,'lut'),exist_ok=True)
  json.dump(out,open(os.path.join(BD,'palette.json'),'w'),indent=1)
  N=65; g=np.linspace(0,1,N); b,gg,r=np.meshgrid(g,g,g,indexing='ij'); cube=np.stack([r,gg,b],-1).reshape(-1,1,3)  # .cube order: R fastest
  for n,a,bb in SEC:
    y=grade(cube,params(n)).reshape(-1,3); slug=n.replace('/','_').replace(' ','_')
    with open(os.path.join(BD,'lut',f'earth_{slug}.cube'),'w') as f:
      f.write(f'TITLE "Earth {n} (earth_palette Nov 9)"\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
      for q in y: f.write('%.6f %.6f %.6f\n'%tuple(q))
  print('luts written')
