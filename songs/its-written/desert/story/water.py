"""Develop the existing owl and final push through the photographed surface of the well."""
from pathlib import Path
from functools import lru_cache
import cv2,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'work/story'
cv2.setNumThreads(2)
def smooth(a,b,x):
    q=np.clip((x-a)/(b-a),0,1);return q*q*(3-2*q)
def image(name):
    im=cv2.imread(str(ROOT/'work/rough2'/name),cv2.IMREAD_COLOR)
    return cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
def lookup(im,u,v):
    h,w=im.shape[:2]
    return cv2.remap(im,np.asarray(u*w-.5,'f'),np.asarray((1-v)*h-.5,'f'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
class Water:
    def __init__(self,finish=False):
        self.finish=finish
        data=np.load(D/'water-camera.npz');self.cam=data['camera'];self.verts=data['verts'];tri=data['tri']
        n=len(self.verts);graph=coo_matrix((np.ones(tri.size), (tri.ravel(),np.roll(tri,1,axis=1).ravel())),shape=(n,n))
        count,ids=connected_components(graph,directed=False)
        self.chunks=[np.where(ids==i)[0] for i in range(count)]
        self.owl=image('moon-eyes.png');self.branch=image('branch-tips.png')
        self.reflected_alpha=cv2.imread(str(ROOT/'work/rough2/reflection.png'),cv2.IMREAD_UNCHANGED)[...,3].copy()
        self.star=cv2.imread(str(ROOT/'work/rough2/water-pins.png'),0)
        rng=np.random.default_rng(5321);h=1152
        pts=np.zeros((h,h),np.uint8)
        for _ in range(1100):
            x,y=rng.uniform(0,h,2);r=rng.choice([.45,.56,.72,1.12,1.45],p=[.4,.23,.21,.11,.05])
            cv2.circle(pts,(round(x*16),round(y*16)),round(r*16),int(rng.uniform(98,243)),-1,cv2.LINE_AA,4)
        self.pins=cv2.GaussianBlur(pts,(3,3),.37)
    def field(self,fr,w=960,h=540):
        c=self.cam[fr-4751]
        if self.finish and 4751<=fr<4778:
            from well_arrival import arrival
            c=arrival(c,fr)
        eye=c[:3];right=c[3:6];up=c[6:9];fw=c[9:12];lens=c[-1]
        def project(xyz):
            delta=xyz-eye;z=delta@fw
            return np.c_[w*(.5+lens*(delta@right)/z), h*.5-w*lens*(delta@up)/z]
        a=np.linspace(0,2*np.pi,145);disc=project(np.c_[.984*np.cos(a),.984*np.sin(a),np.zeros(len(a))])
        # Work only in the water's bounding rectangle.
        lo=np.maximum(0,np.floor(disc.min(0)-3)).astype(int);hi=np.minimum([w,h],np.ceil(disc.max(0)+4)).astype(int)
        if (hi<=lo).any():return
        x0,y0=lo;x1,y1=hi;xx=np.arange(x0,x1,dtype='f')[None,:];yy=np.arange(y0,y1,dtype='f')[:,None]
        sx=(xx+.5-w*.5)/w;sy=(h*.5-yy-.5)/w
        ray=[np.float32(fw[k]*lens)+np.float32(right[k])*sx+np.float32(up[k])*sy for k in range(3)]
        d=-np.float32(eye[2])/ray[2]
        x=np.float32(eye[0])+d*ray[0];y=np.float32(eye[1])+d*ray[1]
        mask=np.zeros(x.shape,np.uint8)
        cv2.fillConvexPoly(mask,np.rint((disc-lo)*16).astype('i'),255,cv2.LINE_AA,4)
        pix=np.rint((project(self.verts)-lo)*16).astype('i')
        for ids in self.chunks:
            if len(ids)>2:cv2.fillConvexPoly(mask,cv2.convexHull(pix[ids]),0,cv2.LINE_AA,4)
        return (slice(y0,y1),slice(x0,x1)),x,y,mask.astype('f')/255
    def develop(self,rgb,fr,portrait=None):
        sampled=self.field(fr,rgb.shape[1],rgb.shape[0])
        if sampled is None:return rgb
        box,x,y,wet=sampled;dry=rgb[box].astype('f');t=fr/30;tt=(fr-4751)/30
        phase=t-159+1.55*max(0,(fr-4981)/30-.70*(1-np.exp(-max(0,(fr-4981)/30)/.70)))
        A=np.sin(27*y+3.2*x+1.36*phase+1.4*np.sin(4*x+.36*phase))
        B=np.sin(64*y+.86*phase+2.1*x);C=np.sin(6.6*x+8.1*y-.59*phase)
        swell=np.sin(16.1*y+6.4*x-1.88*phase+1.6*C)
        comb=np.sin(66*y+10.4*x-5.8*phase+2.4*swell+1.9*A)
        u=.705*x+.5+.0031*A+.0011*B+.0019*C+.0021*comb
        v=.705*y+.515+.0021*C+.0017*swell+.0012*comb
        maps=lookup(self.owl,u,v).astype('f')/255
        eyes,oldmoon,bird=maps.transpose(2,0,1)
        # Mirror a broader, slow capillary wave from the actual scene, so it crosses both wing and reflected sky.
        s1=np.sin(40*y+3.6*x-tt*2.28+1.9*np.sin(9*x+tt*.51))
        s2=np.sin(87*y+12*x-tt*3.1+.9*s1)
        yy,xx=np.indices(wet.shape,dtype='f')
        bent=cv2.remap(dry,xx+(1.11*s1+.54*s2)*(rgb.shape[1]/960),yy+.28*s2*(rgb.shape[1]/960),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        # The photographed moon originally touched the wing tip. Return that patch to the passing night.
        lunar=np.maximum(oldmoon,lookup(self.owl[...,1],.705*x+.5+.00065*A,.705*y+.515+.0004*B).astype('f')/255)
        moon_rows,moon_cols=np.where(lunar>.30)
        if len(moon_cols):
            width=float(max(2,moon_cols.max()-moon_cols.min()))
            # Reconstruct the raked sky from just windward of this highlight, preserving the feather below it.
            repl=cv2.remap(bent,xx-width*1.44,yy-width*.18,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            cover=cv2.GaussianBlur(cv2.dilate(lunar,np.ones((3,3),'u1')),(0,0),1.2)
            bent+=(repl-bent)*smooth(.001,.12,cover)[...,None]
        l=bent@np.array([.24,.61,.15],'f')
        glow=np.maximum(0,(bent[...,0]-bent[...,2]-5)/155)*bird
        # Keep the eye and tree timings while letting light scatter under the reflected feathers.
        grade=bent*np.array([.62,.74,.91],'f')+np.array([.3,1.5,3.2],'f')
        grade*=1-.155*bird[...,None]
        grade+=(bent-grade)*np.minimum(.86,eyes*1.8+.26*glow)[...,None]
        diffuse=cv2.GaussianBlur(glow,(0,0),max(2.1,wet.shape[1]*.009))
        grade+=diffuse[...,None]*np.array([79,48,16],'f')
        # A field of fine crests passes across the bird, its stars and the face below.
        silver=(smooth(.07,1,s1)*(.45+.55*np.cos(13*x-3*y+tt*.8)))**2
        grade*=1-(.027+.084*bird[...,None])*s1[...,None]
        grade+=silver[...,None]*np.array([4.9,7.1,10.8],'f')
        stars=lookup(self.pins,.48+.43*x+.0019*A,.51+.43*y+.0024*C).astype('f')/255
        stars*=.67+.33*np.cos(21*x+27*y-1.83*tt+1.6*s1)
        night=(np.array([8.4,15.6,25.0],'f')+((2+s1+1.6*swell+.55*s2)[...,None]*np.array([.84,1.16,1.5],'f')))
        night+=stars[...,None]*np.array([134.,149.,172.],'f')
        grade+=stars[...,None]*(.83-.22*bird)[...,None]*np.array([124.,144.,169.],'f')
        # The second moon sits *inside* the left wing, softly broken by the same ripple.
        mx=(u-.280)/.024;my=(v-.668)/.029;rho=mx*mx+my*my
        moon=(1-smooth(.68,1.20,rho))*(.30+.65*smooth(-.81,.49,mx+.18*my))*(.80+.12*s1+.08*np.sin(15*mx+3*my))+.07*np.exp(-rho*.33)
        grade+=moon[...,None]*bird[...,None]*np.array([77,83,90],'f')
        q=smooth(4908,4962,fr)
        water=night*(1-q)+grade*q
        if self.finish and 4880<=fr<=4962:
            # Expose the entire water surface together. Local timing follows the
            # same crossing wavelets that refract the feathers and her face.
            ripple_time = 1.7*swell + .82*s1 + .33*s2
            q = smooth(4917,4955,fr + ripple_time)
            water = night+(grade-night)*q[...,None]
        if 4785<=fr<=4893:
            # Her cap and shoulders first darken the reflected sky as she leans
            # over the lip. Keep the owl above them for its later entrance.
            shadow=lookup(self.reflected_alpha,.625*u+.1875,.625*v+.1875).astype('f')/255
            shadow*=1-smooth(.004,.09,bird)
            shadow*=smooth(.46,.34,v)*smooth(4785,4841,fr)*(1-smooth(4876,4893,fr))
            silhouette=bent*np.array([.91,.92,1.03],'f')+night*.055
            water+=(silhouette-water)*(shadow*.90)[...,None]
        if portrait is not None:
            # The dry RGBA plate is refracted once on the world-space plane.
            rise=smooth(4883,4910,fr);withdraw=smooth(4918,4960,fr)
            w=2.29-1.02*withdraw;h=w*9/16
            cu=.5+(x+.017+.0058*A+.0041*comb)/w
            cv=.5+(y+.22+.21*withdraw+.0062*s1+.0035*comb)/h
            if self.finish:
                cu+=(.0084*A+.0061*swell+.0030*s2)/w
                cv+=(.0048*C+.0037*s1)/h
            part=lookup(portrait,cu,cv).astype('f');a=part[...,3]/255
            a*=smooth(0,.36,cv)*smooth(0,.045,cu)*(1-smooth(.955,1,cu))
            head=part[...,:3]*np.array([.56,.65,.81],'f')+night*.18
            head*=(.94-.085*s1-.026*s2)[...,None]
            head+=(silver*3.2+stars*29)[...,None]*np.array([.63,.78,1.0],'f')
            alpha=a*smooth(4878,4891,fr)*(1-smooth(4939,4961,fr))*(1-.93*q*bird)
            if self.finish:
                head=part[...,:3]*np.array([.44,.532,.681],'f')+night*.28
                head*=(.96-.103*s1-.033*s2)[...,None]
                head+=(silver*6.8+stars*68)[...,None]*np.array([.60,.80,1.],'f')
                alpha=a*smooth(4878,4891,fr)*(1-q)
            water+=(head-water)*alpha[...,None]
        result=rgb.copy();result[box]=np.uint8(np.clip(dry+(water-dry)*wet[...,None],0,255))
        return result
