"""Hand-drawn contours, animated along their arc length on the actual dune surface."""
import re
from world import *
from rails import sampled,pen
def path(s):
    tokens=re.findall(r'[MLCQZ]|-?(?:\d*\.\d+|\d+)',s);out=[];i=0
    while i<len(tokens):
        cmd=tokens[i];i+=1
        if cmd=='Z':out.append(out[0]);continue
        n={'M':2,'L':2,'Q':4,'C':6}[cmd];p=np.array(tokens[i:i+n],float).reshape(-1,2);i+=n
        if cmd=='M':out.append(p[0]);continue
        a=np.asarray(out[-1]);steps=max(3,min(70,int(sum(np.linalg.norm(np.diff(np.vstack([a,p]),axis=0),axis=1))*.65)))
        u=np.linspace(0,1,steps)[1:,None]
        if cmd=='L':out.extend(mix(a,p[0],u))
        if cmd=='Q':out.extend((1-u)**2*a+2*(1-u)*u*p[0]+u*u*p[1])
        if cmd=='C':out.extend((1-u)**3*a+3*(1-u)**2*u*p[0]+3*(1-u)*u*u*p[1]+u**3*p[2])
    return np.array(out)
def oval(x,y,rx,ry,ang=0,n=67):
    t=np.linspace(0,TAU,n);p=np.c_[rx*np.cos(t)*(1+.028*np.sin(3*t)),ry*np.sin(t)]
    return p@np.array([[math.cos(ang),math.sin(ang)],[-math.sin(ang),math.cos(ang)]])+[x,y]
class Board:
    def __init__(self,S,cx,cy,scale):self.S=S;self.c=np.array([cx,cy]);self.scale=scale
    def xy(self,pts):
        return np.asarray(pts)*[self.scale,-self.scale]+self.c
    def at(self,x,y,z=0):return self.S.ground(*self.xy([x,y]),z)
    def stroke(self,label,p,start,duration,r=.115,mat=None,erase=None):
        return Stroke(self,label,path(p) if isinstance(p,str) else p,start,duration,r,mat,erase)
class Stroke:
    def __init__(self,B,label,points,start,duration,r,mat,erase):
        self.B=B;self.start=start;self.finish=start+duration;self.erase=erase;self.r=r
        length=np.linalg.norm(np.diff(points,axis=0),axis=1).sum()
        self.uv=sampled(points,np.linspace(0,1,max(12,min(540,round(length*B.scale/.18)+1))))
        self.xyz=B.S.surface(B.xy(self.uv),r*.56)
        radii=.90+.095*np.sin(np.linspace(.21,15.92,len(self.uv)))+.045*np.sin(np.linspace(2.2,36,len(self.uv)))
        radii*=.52+.48*np.minimum(1,np.minimum(np.linspace(0,1,len(radii)),np.linspace(1,0,len(radii)))*14)
        self.obj=tube(label,self.xyz,mat or B.S.gold,r,radii=radii)
        self.obj.data.bevel_factor_mapping_end='SPLINE';self.obj.data.bevel_factor_mapping_start='SPLINE'
    def frame(self,fr,offset=None,warp=None,force=None):
        finish=smooth(self.start,self.finish,fr) if self.finish>self.start else float(fr>=self.start)
        begin=0 if self.erase is None else smooth(*self.erase,fr)
        if force is not None:finish=force
        self.obj.hide_render=bool(finish<=.001 or begin>=finish-.001)
        if self.obj.hide_render:return
        self.obj.data.bevel_factor_start=min(.998,begin);self.obj.data.bevel_factor_end=max(.001,finish)
        if offset is not None or warp is not None:
            p=self.uv if warp is None else warp(self.uv,fr)
            if offset is not None:p=p+offset
            self.xyz=self.B.S.surface(self.B.xy(p),self.r*.56)
            coords(self.obj.data.splines[0],self.xyz)
def series(B,label,lines,start,end,r=.11,mat=None,erase=None):
    p=[path(line) if isinstance(line,str) else line for line in lines];length=np.array([np.linalg.norm(np.diff(s,axis=0),axis=1).sum() for s in p])
    d=np.r_[0,np.cumsum(length**.71)];d=start+(end-start)*d/d[-1]
    return [Stroke(B,label+' '+str(i),s,d[i],d[i+1]-d[i],r,mat,erase) for i,s in enumerate(p)]
# A single weight-bearing contour. Folded knees, the pad of the lower lip, and the hump remain separate at distance.
RESTING=[
'M 2 41 C 3 38 8 37 10 35 Q 12 31 15 32 L 16 27 Q 20 27 18 34 C 22 42 18 48 21 51 C 26 55 33 46 35 39 C 38 30 40 20 47 21 C 54 19 56 34 63 37 C 68 38 74 39 78 45 C 82 51 77 59 81 62 Q 85 65 88 64',
'M 78 49 Q 84 51 85 58 Q 87 63 90 60',
'M 79 62 C 76 68 69 67 61 65 Q 56 64 53 60 Q 52 58 57 58 C 63 57 68 63 72 62',
'M 58 65 C 49 67 43 64 35 64 Q 27 70 18 66 Q 17 64 24 62 L 32 58',
'M 37 62 Q 30 63 24 60 C 16 56 14 51 13 46 Q 13 42 11 42 Q 4 47 1 44 L 2 41',
'M 4 42 Q 7 42 9 41','M 13 36 L 14.5 36']
DRIVER=[
'M 79 56 Q 84 52 85 47 L 87 44 Q 89 42 91 44 Q 94 52 94 56',
'M 85 47 Q 85 44 82 43 C 79 42 79 39 81 36 Q 81 32 85 32 C 89 31 92 34 92 36 L 94 39 L 92 40 Q 92 44 88 44',
'M 80 36 Q 85 35 91 36 M 91 36', 'M 89 38 L 91 38.5',
'M 80 56 Q 84 60 90 58 L 98 53 Q 101 52 103 55 Q 101 60 99 64 L 105 65',
'M 83 58 Q 87 65 92 65 L 99 64','M 81 55 Q 80 61 83 64']
FINGER=['M 88 47 Q 91 52 95 51 L 99 43 Q 99 41 100 41 L 100 36 Q 100.4 34 101.5 36 L 102 41 Q 106 41 104 44 L 102 46 Q 100 54 96 56 Q 91 57 88 53']
WALK_CAMEL=[
'M 0 26 Q 4 23 7 14 C 9 12 10 10 13 12 Q 16 15 18 16 C 22 15 20 8 24 5 Q 27 3 29 7 L 30 4 Q 31 7 30 9 L 36 11 Q 37 14 33 14 L 29 13 C 27 17 27 23 23 25 Q 17 28 10 25 Q 5 25 3 28',
'M 5 26 L 7 30 L 4 39 L 1 40','M 10 26 L 11 31 L 14 38 L 17 38','M 19 26 L 19 32 L 17 40 L 20 40','M 23 25 L 24 31 L 26 37 L 29 37','M 6 16 Q 2 19 2 24']
# A dromedary at the halt: dropped brisket, single high hump, long unladen neck,
# split lip, narrow hocks and broad padded feet. Each animal is drawn with the same nib.
HALTED_CAMEL=[
'M 4 23 C 6 20 7 18 10 17 C 12 16 13 6 16 5 C 20 2 21 14 25 16 C 28 18 29 17 31 12 C 33 7 32 2 34 -2 Q 35 -5 38 -4 L 38 -6 Q 40 -5 39 -3 Q 42 -2 45 -1 Q 46 1 44 2 L 40 2 C 37 4 37 11 36 17 C 35 23 32 27 27 27 Q 23 27 19 25 Q 13 28 8 25 Q 5 25 4 23',
'M 8 25 C 8 29 10 31 8 33 L 5 41 Q 4 43 8 42 L 10 41',
'M 13 26 Q 13 30 15 33 L 17 39 Q 18 41 21 40',
'M 26 27 L 27 33 Q 26 36 26 41 Q 27 43 31 42',
'M 31 26 Q 32 30 31 34 L 33 39 Q 34 41 37 40',
'M 7 19 Q 3 20 3 27 Q 3 30 1 31',
'M 41 0 Q 43 1 45 0']
def caravan(B,x,y,size,n,start,mat,direction=1,gap=38,halted=False):
    strokes=[]
    for j in range(n):
        offset=np.array([x+j*gap*size*direction,y+.75*np.sin(j*1.7)*size])
        finish=os.environ.get('FINISH_STORY')=='1'
        drawings=HALTED_CAMEL if halted or finish else WALK_CAMEL
        if finish:
            mat=B.S.gold
            drawings=drawings+['M 9 18 Q 15 16 23 18 L 24 23 Q 16 22 11 23 L 9 18',
                               'M 11 17 L 10 13 Q 13 10 16 13 L 17 17 M 18 17 L 19 13 Q 22 11 24 15 L 24 18']
        for k,p in enumerate(drawings):
            uv=path(p)*[size*direction,size]+offset
            strokes.append((j,k,offset,B.stroke('Caravan animal '+str(j),uv,start+j*2+k*.8,6 if k==0 else 3,max(.062,.35*size*B.scale),mat)))
    return strokes
def move_camels(strokes,fr,dx,dy=0,fold=0,step=0,size=1):
    for j,k,base,ink in strokes:
        def warp(uv,f):
            p=uv.copy();local_y=(uv[:,1]-base[1])/size
            low=smooth(24,39,local_y);phase=step*1.3+j*1.53+k*1.87
            p[:,0]+=low*(1-fold)*size*2.7*np.sin(phase)
            p[:,1]-=low*(1-fold)*size*2.45*max(0,np.cos(phase))
            p[:,1]+=size*(.62*np.sin(step*2.6+j)+fold*(1-low)*11.8)
            p[:,0]+=fold*low*size*(2 if k%2 else -2.6)
            return p
        ink.frame(fr,[dx,dy],warp)
class Scatter:
    def __init__(self,S,strokes,count=760):
        rng=np.random.default_rng(153);self.r=rng.random((count,6))
        curves=np.vstack([s.xyz[::2] for s in strokes]);self.b=curves[np.linspace(0,len(curves)-1,count).astype(int)]
        self.mesh=mesh_obj('Grains of erased handwriting',np.zeros((count*3,3)),np.arange(3*count).reshape(-1,3),S.gold,False)
    def frame(self,fr,a,b):
        age=(fr-(a+(b-a-15)*self.r[:,0]))/22
        live=(age>0)&(age<1);u=np.clip(age,0,1)
        p=self.b.copy();p[:,0]+=u*(1.1+5*self.r[:,2]);p[:,1]+=u*(.2+1.2*self.r[:,1]);p[:,2]+=.14*np.sin(np.pi*u)*(1+2*self.r[:,3])
        sz=(.014+.043*self.r[:,5])*np.sin(np.pi*u)**.51*live
        corners=np.array([[0,-.6,-.3],[-1,.1,.6],[1,.7,0]])
        self.mesh.hide_render=not live.any()
        if live.any():self.mesh.data.vertices.foreach_set('co',(p[:,None,:]+sz[:,None,None]*corners).astype('f').ravel());self.mesh.data.update()
