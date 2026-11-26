"""The exterior story stage. Terrain, ink and the rider use the same metre grid."""
import sys, os, math
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'work/story'
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'src/rough')]
os.environ.update(ONEGRAIN_ROUGH2='1',ONEGRAIN_WALKWIND='1',ONEGRAIN_DEVICE=os.environ.get('ONEGRAIN_DEVICE','CPU'),STORY_PLAIN_SHOES='1')
from stage import node,connect,op,vector,split,join,noise,mul,add,blend,sun,point,roughmat,mesh_obj,sky
from wardrobe import obj,cloth,curve_obj
from cycles_device import configure
TAU=math.tau
def smooth(a,b,x):
    u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
def mix(a,b,u):return np.asarray(a)*(1-u)+np.asarray(b)*u
def unit(a):
    a=np.asarray(a,float);return a/np.maximum(1e-9,np.linalg.norm(a,axis=-1,keepdims=True))
def interpolate(t,keys):
    # Local cubic Hermite interpolation on the authored time axis.
    times=np.array([p[0] for p in keys]);p=np.array([p[1:] for p in keys]);i=np.clip(np.searchsorted(times,t)-1,0,len(keys)-2)
    dt=times[i+1]-times[i];u=np.clip((t-times[i])/dt,0,1)
    j=max(0,i-1);k=min(len(keys)-1,i+2)
    va=(p[i+1]-p[j])/(times[i+1]-times[j])*dt;vb=(p[k]-p[i])/(times[k]-times[i])*dt
    return mix(p[i],p[i+1],u*u*(3-2*u))+u*(1-u)*((1-u)*va-u*vb)
def material(name,color,emission=0,rough=.72):
    m,b,n=roughmat(name,color,rough)
    if emission:
        b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emission
    return m
def tube(name,pts,m,r,parent=None,radii=None):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=2;cu.use_fill_caps=True
    p=cu.splines.new('POLY');p.points.add(len(pts)-1);coords(p,pts)
    if radii is not None:p.points.foreach_set('radius',np.asarray(radii,'f'))
    cu.materials.append(m);return obj(name,cu,parent)
def coords(spline,pts):spline.points.foreach_set('co',np.c_[pts,np.ones(len(pts))].astype('f').ravel())
def sphere(name,centre,radii,m,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=14)
    o=bpy.context.object;o.name=name;o.parent=parent;o.location=centre;o.scale=radii;o.data.materials.append(m)
    o.data.polygons.foreach_set('use_smooth',np.ones(len(o.data.polygons),bool));return o
class Stage:
    def __init__(self,w=864,samples=8,mode='',studio=False):
        if not (0<w<=(1920 if studio else 960)):raise ValueError('Width exceeds delivery')
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        s=bpy.context.scene;self.scene=s;s.render.engine='CYCLES';configure(s);s.cycles.samples=samples;s.cycles.use_denoising=True
        s.cycles.max_bounces=4;s.cycles.diffuse_bounces=2;s.cycles.glossy_bounces=2;s.cycles.transparent_max_bounces=8
        s.render.resolution_x=w;s.render.resolution_y=w*9//16;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=min(12,os.cpu_count())
        s.render.use_persistent_data=True;s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=96
        s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.18
        self.moon=sky(s);self.moon.inputs[0].default_value=-.49;self.moon.inputs[1].default_value=.84;self.moon.inputs[2].default_value=.20
        self.key=sun('Low blue moon',(-.82,.43,.20),2.15,(.57,.72,1),.042)
        self.rim=sun('Cool silver on the crests',(.44,-.84,.23),.87,(.65,.74,.92),.16)
        self.fill=sun('Scattered sky',(.18,.69,.75),.58,(.42,.55,.82),.43)
        bpy.ops.object.camera_add();self.cam=bpy.context.object;s.camera=self.cam;self.cam.data.sensor_width=36
        self.cam.data.clip_start=.018;self.cam.data.clip_end=4000
        self.gold=material('Incised road • honey gold',(1,.53,.115),3.3)
        self.hot=material('Fresh nib • wheat white',(1,.73,.29),4.9)
        self.white=material('Fellow travellers • moon chalk',(.48,.64,.79),1.10)
        self.cool=material('Worn by ordinary steps',(.13,.16,.20),.05)
        if mode=='night':
            nt=s.world.node_tree
            bg=next(n for n in nt.nodes if n.type=='BACKGROUND')
            base=bg.inputs['Color'].links[0].from_socket
            env=node(nt,'ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(ROOT/'work/r2/galactic-high.jpg'),check_existing=True)
            from stage import dot
            direction=node(nt,'ShaderNodeTexCoord').outputs['Generated']
            # Put the bright Scorpius dust lanes beyond the uphill turn of the original capital.
            pole=unit([.18,-.55,.815]);front=unit([.61,.73,.34]);right=unit(np.cross(pole,front));front=unit(np.cross(right,pole))
            coords=join(nt,dot(nt,direction,front.tolist()),dot(nt,direction,right.tolist()),mul(nt,.73,dot(nt,direction,pole.tolist())))
            connect(nt,env,'Vector',coords);band=vector(nt,'MULTIPLY',env.outputs[0],(2.44,2.62,3.19))
            camera=node(nt,'ShaderNodeLightPath').outputs['Is Camera Ray']
            skyline=vector(nt,'MULTIPLY',band,join(nt,camera,camera,camera));connect(nt,bg,'Color',vector(nt,'ADD',base,skyline))
        self.mode=mode;self.sand()
    def view(self,eye,target,lens=32,roll=0,up=None):
        eye=np.asarray(eye);target=np.asarray(target);cam=self.cam;cam.location=eye;cam.data.lens=lens
        fw=unit(target-eye)
        if up is None:rot=Vector(fw).to_track_quat('-Z','Y')
        else:
            from mathutils import Matrix
            right=unit(np.cross(fw,up));up=unit(np.cross(right,fw));rot=Matrix(np.column_stack((right,up,-fw)).tolist()).to_quaternion()
        cam.rotation_mode='QUATERNION';cam.rotation_quaternion=rot@Quaternion((0,0,1),roll)
    def sand(self):
        # Tighter spacing at the play area. The far range gives the skyline enough depth for the flying camera.
        axis=np.r_[-np.geomspace(91,850,102)[::-1],np.linspace(-90,90,381),np.geomspace(91,850,102)]
        self.axis=axis;x,y=np.meshgrid(axis,axis);n=len(axis)
        def crest(p,peak):
            q=p%1
            return np.where(q<peak,np.sin(.5*np.pi*np.minimum(q/peak,1))**1.7,
                            (1-np.clip((q-peak)/(1-peak),0,1))**1.45)
        phase=.027*x+.022*y+.15*np.sin(.079*y+.041*x)+.085*np.cos(.065*x-.052*y)
        h=(crest(phase,.72)-.45)*(2.7+.95*np.sin(.081*y-.036*x))
        broader=crest(.0092*x-.011*y+.22*np.sin(.035*y)+.095*np.sin(.056*x),.68)
        h+=4.1*(broader-.40)+.31*np.sin(.16*x+.096*y+.83*np.sin(.105*y))
        horizon=smooth(65,225,np.hypot(x,y))
        h+=horizon*(6+23*crest(.0062*y+.005*x+.28*np.cos(.018*x),.74)+12*broader)
        if self.mode=='slide':
            h+=10*np.exp(-((y+10+.18*x)/18)**2)*(.84+.16*np.cos(.08*x))
            if os.environ.get('FINISH_STORY')=='1':
                # A windward crest at the starting point and a continuous lee face below it.
                h+=17.8*(1-smooth(-22,11,y+.18*x))*(1-smooth(27,76,abs(x)))
        if self.mode in ('oasis','walkout'):
            basin=1-smooth(.83,1.27,np.hypot((x+1)/24,(y-6)/25))
            bed=.16+.28*np.sin(.14*x+.09*y)+.13*np.cos(.23*y-.075*x)
            h=mix(h,bed,.93*basin)
        if self.mode=='oasis':
            lee=(1-smooth(25,41,np.abs(x+65)))*(1-smooth(13,30,np.abs(y+29)))
            h=mix(h,-.61+.09*(y+30)+.15*np.sin(.14*x)+.075*np.sin(.24*y+.12*x),lee)
        self.zz=h
        corners=(np.arange(n-1)[:,None]*n+np.arange(n-1)[None,:]).ravel()
        # Match the diagonal sampled by floor().
        faces=np.concatenate((np.stack((corners,corners+1,corners+n+1),1),np.stack((corners,corners+n+1,corners+n),1)))
        v=np.stack((x,y,h),axis=-1).reshape(-1,3)
        me=bpy.data.meshes.new('Wind cut sand');me.vertices.add(len(v));me.vertices.foreach_set('co',v.astype('f').ravel())
        me.loops.add(3*len(faces));me.loops.foreach_set('vertex_index',faces.astype('i').ravel())
        me.polygons.add(len(faces));me.polygons.foreach_set('loop_start',np.arange(0,3*len(faces),3,dtype='i'));me.polygons.foreach_set('use_smooth',np.ones(len(faces),bool));me.update(calc_edges=True)
        self.land=obj('Dune sea',me)
        m,b,n=roughmat('Erg • silicate and ripples',(.24,.188,.15),.91);me.materials.append(m)
        p=node(n,'ShaderNodeNewGeometry').outputs['Position'];xx,yy,zz=split(n,p)
        def im(name,scale,colorspace):
            tex=node(n,'ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'work/ref'/name),check_existing=True)
            tex.image.colorspace_settings.name=colorspace;connect(n,tex,'Vector',join(n,mul(n,xx,scale),mul(n,yy,scale)));return tex.outputs[0]
        alb=im('sand-color.jpg',.28,'sRGB');gr=noise(n,p,.90,3.4)
        p1=add(n,mul(n,xx,11.3),mul(n,yy,8.1),mul(n,noise(n,p,.19,3),20.2),mul(n,noise(n,p,.83,2),6.8),mul(n,noise(n,p,2.8,2),1.7))
        r=op(n,'SINE',p1);patch=noise(n,p,.21,3.5)
        grain=im('sand-color.jpg',1.76,'sRGB')
        salt=noise(n,p,18.1,2.8)
        sand=blend(n,add(n,-.15,mul(n,.59,gr),mul(n,.59,alb),mul(n,.50,salt),mul(n,.28,grain),mul(n,.078,r,patch)),(.068,.066,.070,1),(.41,.345,.285,1))
        connect(n,b,'Base Color',sand)
        bump=node(n,'ShaderNodeBump');bump.inputs['Distance'].default_value=.039;bump.inputs['Strength'].default_value=.43
        connect(n,bump,'Height',add(n,mul(n,.62,r,patch),mul(n,.76,noise(n,p,35,2.2)),mul(n,.65,grain),mul(n,.45,alb)));connect(n,b,'Normal',bump.outputs[0])
        if self.mode=='driver' and os.environ.get('FINISH_STORY')=='1':
            bump.inputs['Distance'].default_value=.013
            rip=op(n,'SINE',add(n,mul(n,xx,20.1),mul(n,yy,5.7),mul(n,noise(n,p,.74,3),2.4)))
            connect(n,bump,'Height',add(n,mul(n,.42,rip,patch),mul(n,.55,grain),mul(n,.45,alb)))
    def settle(self,cx,cy,inside,outside):
        # The worn apron round a masonry well is level beneath the stone.
        x,y=np.meshgrid(self.axis,self.axis);weight=1-smooth(inside,outside,np.hypot(x-cx,y-cy))
        self.zz=mix(self.zz,self.floor(cx,cy),weight)
        self.land.data.vertices.foreach_set('co',np.stack((x,y,self.zz),axis=-1).astype('f').ravel());self.land.data.update()
    def floor(self,x,y):
        a=self.axis;i=np.clip(np.searchsorted(a,x)-1,0,len(a)-2);j=np.clip(np.searchsorted(a,y)-1,0,len(a)-2)
        fx=np.clip((x-a[i])/(a[i+1]-a[i]),0,1);fy=np.clip((y-a[j])/(a[j+1]-a[j]),0,1)
        h=self.zz
        return h[j,i]*(1-np.maximum(fx,fy))+h[j,i+1]*np.maximum(fx-fy,0)+h[j+1,i]*np.maximum(fy-fx,0)+h[j+1,i+1]*np.minimum(fx,fy)
    def surface(self,xy,offset=.035):
        xy=np.asarray(xy);return np.c_[xy,self.floor(*xy.T)+offset]
    def ground(self,x,y,up=0):return np.array([x,y,self.floor(x,y)+up])

def terrain_image(S,file,cx,cy,width,height):
    m=S.land.data.materials[0];n=m.node_tree;bs=n.nodes.get('Principled BSDF')
    x,y,_=split(n,node(n,'ShaderNodeNewGeometry').outputs['Position'])
    uv=join(n,add(n,.5,mul(n,add(n,x,-cx),1/width)),add(n,.5,mul(n,add(n,y,-cy),1/height)))
    tex=node(n,'ShaderNodeTexImage');tex.image=bpy.data.images.load(str(file),check_existing=True);tex.image.colorspace_settings.name='Non-Color';tex.extension='CLIP';connect(n,tex,'Vector',uv)
    ch=node(n,'ShaderNodeSeparateColor');connect(n,ch,'Color',tex.outputs['Color'])
    return n,bs,ch.outputs
def press(S,cx,cy,w=2.6,h=5.8):
    stamp=D/'tread/settled-11.png' if S.mode=='night' else ROOT/'work/rough2/plain/settled-11.png'
    n,b,c=terrain_image(S,stamp,cx,cy,w,h)
    base=b.inputs['Base Color'].links[0].from_socket
    shade=blend(n,c[1],base,blend(n,mul(n,c[0],1.7),(.014,.019,.031,1),(.22,.18,.13,1)))
    connect(n,b,'Base Color',shade)
    old=b.inputs['Normal'].links[0].from_socket
    bn=node(n,'ShaderNodeBump');bn.inputs['Strength'].default_value=.84;bn.inputs['Distance'].default_value=.18
    connect(n,bn,'Height',mul(n,c[0],c[1]));connect(n,bn,'Normal',old);connect(n,b,'Normal',bn.outputs[0])
