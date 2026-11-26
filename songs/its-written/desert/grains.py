# A tiled bed of rounded, chipped mineral grains. Each gets a curved crown,
# small conchoidal facets, a shadowed seam, and its own internal colour.
import numpy as np,struct
from scipy.ndimage import gaussian_filter
N=1024;count=26; step=N/count;r=np.random.default_rng(947)
z=np.full((N,N),-.8); tag=np.zeros_like(z); mineral=np.zeros_like(z); facet=np.zeros_like(z)
for j in range(count):
 for i in range(count):
  cx=(i+.2+.62*r.random())*step;cy=(j+.2+.62*r.random())*step
  a=step*r.uniform(.43,.79);b=step*r.uniform(.38,.66); ang=r.uniform(0,6.28)
  X=np.arange(int(cx-1.5*step),int(cx+1.5*step));Y=np.arange(int(cy-1.5*step),int(cy+1.5*step));xx,yy=np.meshgrid(X-cx,Y-cy)
  u=(xx*np.cos(ang)+yy*np.sin(ang))/a;v=(-xx*np.sin(ang)+yy*np.cos(ang))/b
  radius=u*u+v*v; apex=np.sqrt(np.maximum(0,1-radius)); val=apex
  for k in range(5):
   th=r.uniform(0,6.28); val=np.minimum(val,r.uniform(.55,1.15)-u*np.cos(th)*.58-v*np.sin(th)*.58)
  val=val*r.uniform(.42,.83)+r.uniform(-.12,.1);val[radius>1]=-9
  sl=np.ix_(Y%N,X%N);old=z[sl];mask=val>old;z[sl]=np.maximum(val,old);tag[sl]=np.where(mask,r.uniform(.1,1),tag[sl]);mineral[sl]=np.where(mask,r.random(),mineral[sl]);facet[sl]=np.where(mask,apex,facet[sl])
z=np.maximum(z,-.07);z=gaussian_filter(z,.58,mode='wrap')
a=np.stack([z,tag,mineral,facet],2).astype('float32')
with open('work/maps/grains.map','wb') as f:f.write(struct.pack('<iii',N,N,4));a.tofile(f)
