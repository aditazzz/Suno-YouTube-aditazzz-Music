"""Develop the two original pen cameras onto continuous wind-laid quartz."""
import ctypes as ct
from functools import lru_cache
from math import floor,ceil
import cv2
import numpy as np

from film import ROOT,reveal_time
from develop import smooth,D,registration

@lru_cache(1)
def cameras():
    lib=ct.CDLL(str(ROOT/'work/rough2/hero-scene.dylib'));lib.scene_init()
    lib.scene_frame.argtypes=[ct.c_int,ct.c_void_p]
    lib.scene_shift.argtypes=[ct.c_void_p]
    old=registration()
    old.drawing_frame.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_int,ct.c_int]
    return lib,old

@lru_cache(220)
def hero_filmback(frame):
    lib,_=cameras()
    params=np.zeros(30,'f');shift=np.zeros(2,'f')
    lib.scene_frame(frame-1391,params.ctypes.data);lib.scene_shift(shift.ctypes.data)
    right,up,back,eye=params[:12].reshape(4,3).astype('d')
    # Project the tangent plane through the actual optical target. The camera
    # translates, rolls, shifts and changes altitude on the pull-up.
    z=(eye-back*float(params[12]))[2]
    ground=np.array([[-22,-2,z],[-3,-2,z],[-3,7,z],[-22,7,z]])
    delta=ground-eye
    eye_z=-delta@back
    proj=np.c_[.5-shift[0]+.695*(delta@right)/eye_z,
                9/32+shift[1]-.695*(delta@up)/eye_z]
    return ground[:,:2].astype('f'),proj.astype('f')

def filmback(f):
    if f<2000:
        time=f-139 if f<1682 else reveal_time(f)
        ground,a=hero_filmback(floor(time));_,b=hero_filmback(ceil(time))
        return ground,(a+(b-a)*(time-floor(time)))*960
    _,lib=cameras()
    raw=np.array([[20,8],[400,8],[400,68],[20,68]],'f')
    ground=np.ascontiguousarray((raw-[436,42])*[.041,.043],dtype='f')
    pix=np.empty_like(ground);lib.drawing_frame(pix.ctypes.data,ground.ctypes.data,4,min(f,2285))
    if f>2285:
        data,flat=coaster_ground()
        cam=data[f-2286];delta=flat-cam[:3];z=delta@cam[9:12]
        new=np.c_[480+960*cam[12]*(delta@cam[3:6])/z,270-960*cam[12]*(delta@cam[6:9])/z]
        pix=pix+(new-pix)*smooth(2285,2307,f)
    return ground,np.float32(pix)

@lru_cache(1)
def coaster_ground():
    from scipy.interpolate import RegularGridInterpolator
    survey=np.load(D/'survey/coaster.npz')
    axis=survey['axis'];field=RegularGridInterpolator((axis,axis),survey['heights'])
    xy=(np.array([[20,8],[400,8],[400,68],[20,68]])-[230,1])*[.270,.285]
    return survey['cameras'],np.c_[xy,field(xy[:,::-1])+.105]

@lru_cache(1)
def mineral():
    # Public production sand textures already used on the exterior set.
    base=ROOT/'work/ref'
    colour=cv2.imread(str(base/'sand-color.jpg'),0).astype('f')
    norm=cv2.imread(str(base/'sand-nor_gl.jpg'),cv2.IMREAD_COLOR).astype('f')
    relief=cv2.imread(str(base/'sand-disp.jpg'),0).astype('f')
    shadow=norm[...,2]*.72-norm[...,1]*.54
    def standard(a):
        a=a-cv2.GaussianBlur(a,(0,0),8);return a/max(a.std(),1e-4)
    txt=np.clip(.64*standard(colour)+.59*standard(shadow)+.26*standard(relief),-3,3)
    mips=[txt]
    while mips[-1].shape[0]>8:mips.append(cv2.pyrDown(mips[-1]))
    return mips

@lru_cache(1)
def aeolian():
    rng=np.random.default_rng(6147)
    noise=rng.normal(0,1,(256,256)).astype('f')
    noise=cv2.GaussianBlur(noise,(0,0),1.35)
    noise/=noise.std()
    # Embedded pale and dark grains share the moon's low-left illumination.
    # Stamp their lit shoulders and small lee shadows at three physical scales.
    n=1024;stones=np.zeros((n,n),'f')
    for i in range(19500):
        x,y=rng.integers(0,n,2);rad=rng.choice([.72,1.10,1.6,2.6,3.5],p=[.40,.32,.19,.075,.015])
        angle=rng.uniform(-.85,.85);lift=rng.uniform(.35,1.)
        dy,dx=np.ogrid[-9:10,-9:10]
        a=(dx*np.cos(angle)+dy*np.sin(angle))/rad;b=(-dx*np.sin(angle)+dy*np.cos(angle))/(.69*rad)
        grit=np.exp(-1.9*(a*a+b*b))*(32*lift+8)
        shade=np.exp(-1.46*((a-.96)**2+(b-.56)**2))*(-23*lift)
        stones[np.ix_((y+dy.ravel())%n,(x+dx.ravel())%n)]+=grit+shade
    return noise,stones-stones.mean()

def tile(img,u,v):
    sz=img.shape[0]
    return cv2.remap(img,np.float32(np.remainder(u,1)*sz),np.float32(np.remainder(v,1)*sz),cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)

def material(x,y,texel):
    # Asymmetric slip-faces split and rejoin where the crosswind shifts. Aperiodic
    # cross-ripple phase prevents the uninterrupted parallel creases of the old bed.
    bend=.37*np.sin(1.19*x+.79*y)+.19*np.sin(2.33*y-.48*x)+.10*np.sin(3.25*y+.21*x)
    a=.81*x-.41*y;b=.38*x+.86*y
    large=2*np.pi*(a*.53+.15*np.sin(.65*b)+.087*np.sin(1.36*b+.68*a))
    fine=2*np.pi*(a*4.1+bend+.14*np.sin(2.65*b+.51*a))
    secondary=2*np.pi*(a*3.82+.85*bend+.11*np.sin(2.49*b+.29*a))
    cross=smooth(-.65,.72,np.sin(.72*b+1.16*a)+.62*np.sin(1.78*b))
    def slope(phase):return np.cos(phase)+.37*np.cos(2*phase+.63)+.16*np.cos(3*phase+1.2)
    ripple=((1-cross)*slope(fine)+cross*slope(secondary))*(1-smooth(.024,.12,texel))
    crest=slope(large)*(1-smooth(.18,.75,texel))
    deeper=1.9*np.sin(a*.97+.68*np.sin(.31*b))+2.3*np.sin(b*.56+a*.34)
    # Select the scan's mip level by the footprint of a delivery pixel in metres.
    # Interpolate adjacent levels and scales as the camera climbs.
    scan=mineral()
    def sample(period,rot,offset):
        u=(x*np.cos(rot)+y*np.sin(rot))/period+offset
        v=(y*np.cos(rot)-x*np.sin(rot))/period-offset*.62
        lod=np.clip(np.log2(max(1e-7,texel)*scan[0].shape[0]/period),0,len(scan)-1)
        i=int(lod);frac=float(lod-i)
        def level(j):
            size=scan[j].shape[0]
            mx=np.float32(np.remainder(u,1)*size);my=np.float32(np.remainder(v,1)*size)
            return cv2.remap(scan[j],mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
        return level(i) if frac<.02 else (1-frac)*level(i)+frac*level(i+1)
    grit=sample(4.2,.34,.27)*10.5+sample(12.4,-.67,.83)*5.4+sample(1.34,.88,.41)*8.4
    n,stones=aeolian()
    patch=tile(n,.018*x+.008*y,.022*y-.006*x)
    bank=tile(n,.0041*x-.001*y,.0036*y+.0013*x)
    # Wind-scoured tops are smoother, recessed swales trap darker coarse inclusions.
    ripple*=smooth(-1.35,1.35,patch+.38*bank)
    grit*=1.4
    pockets=tile(n,.056*x+.011*y,.063*y-.012*x)
    chips=tile(stones,(x+.13*y)/7.3,(y-.17*x)/7.3)*(1-smooth(.008,.032,texel))
    chips+=tile(stones,(.87*x-.48*y)/17+.23,(.48*x+.87*y)/17+.56)*.69*(1-smooth(.021,.085,texel))
    return 1.6*deeper+3.6*crest+3.8*ripple+grit+3.5*bank+3.4*patch+2.3*pockets+chips

def replace(im,f):
    w=im.shape[1];h=im.shape[0];k=w/960
    amount=(smooth(1668,1682,f)*(1-smooth(1761,1782,f)) if f<2000 else
            smooth(2232,2249,f)*(1-smooth(2289,2305,f)))
    if amount<.0001:return im
    ground,source=filmback(f)
    hom=cv2.getPerspectiveTransform(np.float32(source*k),ground)
    yy,xx=np.ogrid[:h,:w]
    denom=hom[2,0]*xx+hom[2,1]*yy+hom[2,2]
    x=np.float32((hom[0,0]*xx+hom[0,1]*yy+hom[0,2])/denom)
    y=np.float32((hom[1,0]*xx+hom[1,1]*yy+hom[1,2])/denom)
    texel=max(.0001,float(np.median(np.hypot(np.diff(x[h//2]),np.diff(y[h//2])))))
    detail=material(x,y,texel)
    if 1682<=f<1778:
        # The departing lens follows low sheets of sand moving obliquely
        # over the stationary mineral bed beneath the handwriting.
        t=(f-1682)/30
        grains,_=aeolian()
        wind=tile(grains,.034*(x-2.65*t)+.012*y,.063*(y-.59*t)-.016*x)
        lee=tile(grains,.010*x-.004*y,.006*y+.002*x)
        moving=np.clip(wind,-1.5,2.0)*11.2
        detail+=moving*(.43+.57*smooth(-1.1,.95,lee))*smooth(1682,1695,f)*(1-smooth(1755,1778,f))
    if 2241<=f<=2304:
        # A shallow wind blows loose sand over the stationary inscription bed.
        # The sheets advect along the ground and break around fixed gravel patches.
        time=(f-2241)/30
        dx=x-3.9*time;dy=y-.77*time
        grains,_=aeolian()
        salt=tile(grains,.024*dx+.009*dy,.076*dy-.017*dx)
        patches=tile(grains,.0043*x-.0011*y,.0057*y+.0019*x)
        moving=(np.clip(salt,-1.7,2.3)*11.5+3.3*np.maximum(0,salt-.50))
        detail+=moving*(.28+.72*smooth(-1.0,.95,patches))*smooth(2241,2256,f)*(1-smooth(2289,2304,f))
    rgb=im.astype('f');r,g,b=rgb.transpose(2,0,1)
    lum=.23*r+.62*g+.15*b
    # Take the gold pen, its surrounding light, the small white drawings, shadow,
    # boots and red travelling thread from the photographed plate.
    hot=np.maximum(smooth(-2,24,r-b),smooth(112,172,lum)*smooth(-11,4,r-b))
    hot=np.maximum(hot,smooth(44,74,lum)*smooth(-4,10,g-b))
    bright=cv2.GaussianBlur(hot,(0,0),max(.6,7*k))
    protected=np.maximum(hot,bright*.96)
    if f<1783:
        small=cv2.resize(im,(480,270),interpolation=cv2.INTER_AREA).astype('f')
        sr,sg,sb=small.transpose(2,0,1)
        cap=np.uint8((sr>1.32*sg+9)&(sr>1.20*sb+4))
        # Search near the far end of the stroke. The pen itself is yellow.
        cap[:,:270]=0
        n,_,sizes,centres=cv2.connectedComponentsWithStats(cap)
        ids=[i for i in range(1,n) if sizes[i,4]>=3 and sizes[i,2]<37]
        if ids:
            i=max(ids,key=lambda i:sizes[i,4]);cx,cy=centres[i]*w/480
            u=max(2.5*k,min(22*k,sizes[i,2]*w/480))
            figure=np.exp(-.5*((xx-cx)/(.90*u+2*k))**2-.5*((yy-cy-1.7*u)/(2.5*u+2*k))**2)
            protected=np.maximum(protected,smooth(.09,.57,figure))
    cold=1-np.maximum(hot,bright)
    blur=lambda a:cv2.GaussianBlur(a,(0,0),max(2,w*.044))
    base=blur(rgb*cold[...,None])/np.maximum(.05,blur(cold)[...,None])
    global_tone=np.median(base[::12,::12],axis=(0,1))
    tone=base*.29+global_tone*.71
    tone=tone*np.array([1.118,1.028,.899],'f')
    # Restore only the short-distance spill of the lettering, without driving
    # the surrounding soil towards its raw neon value.
    bloom=cv2.GaussianBlur(hot,(0,0),max(1,12*k))
    fresh=tone+detail[...,None]*np.array([.95,1.,1.04],'f')+bloom[...,None]*np.array([10.,6.,2.],'f')
    q=(.965*amount*(1-protected))[...,None]
    out=rgb+(fresh-rgb)*q
    # Match the exposure of the keep through the change in substrate.
    prior=lum.mean();current=out.mean((0,1))@np.array([.23,.62,.15])
    out+=(prior-current)*q/max(.08,float(q.mean()))
    return np.uint8(np.clip(out,0,255)+.5)
