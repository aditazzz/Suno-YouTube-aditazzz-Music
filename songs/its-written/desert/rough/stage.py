"""CPU Cycles stage shared by the approach, the walk, the wind, the oasis and the well."""
from pathlib import Path
import ctypes as C
import math
import os
import bpy
import numpy as np
from mathutils import Vector
from clockfilm import *
P=ROOT/'work/rough'
R2=os.environ.get('ONEGRAIN_ROUGH2')=='1' and os.environ.get('ONEGRAIN_LOCK_GRAIN')!='1'
D=ROOT/'work/rough2'
TREAD=D if os.environ.get('ONEGRAIN_SOLE_11')=='1' else D/'plain'
def node(nt,kind):return nt.nodes.new(kind)
def connect(nt,n,key,val):
    if isinstance(val,bpy.types.NodeSocket):nt.links.new(val,n.inputs[key])
    else:n.inputs[key].default_value=val
def op(nt,kind,a,b=None):
    n=node(nt,'ShaderNodeMath');n.operation=kind;connect(nt,n,0,a)
    if b is not None:connect(nt,n,1,b)
    return n.outputs[0]
def vector(nt,kind,a,b):
    n=node(nt,'ShaderNodeVectorMath');n.operation=kind;connect(nt,n,0,a);connect(nt,n,1,b);return n.outputs[0]
def normlen(nt,a):
    n=node(nt,'ShaderNodeVectorMath');n.operation='LENGTH';connect(nt,n,0,a);return n.outputs['Value']
def dot(nt,a,b):
    n=node(nt,'ShaderNodeVectorMath');n.operation='DOT_PRODUCT';connect(nt,n,0,a);connect(nt,n,1,b);return n.outputs['Value']
def split(nt,a):
    n=node(nt,'ShaderNodeSeparateXYZ');connect(nt,n,0,a);return n.outputs
def join(nt,x,y,z=0):
    n=node(nt,'ShaderNodeCombineXYZ')
    for i,a in enumerate((x,y,z)):connect(nt,n,i,a)
    return n.outputs[0]
def remap(nt,x,a,b):
    n=node(nt,'ShaderNodeMapRange');n.interpolation_type='SMOOTHSTEP'
    for k,v in [('Value',x),('From Min',a),('From Max',b)]:connect(nt,n,k,v)
    return n.outputs[0]
def add(nt,*items):
    v=items[0]
    for b in items[1:]:v=op(nt,'ADD',v,b)
    return v
def mul(nt,*items):
    v=items[0]
    for b in items[1:]:v=op(nt,'MULTIPLY',v,b)
    return v
def gauss(nt,x):
    return op(nt,'EXPONENT',mul(nt,-1,x,x))
def blend(nt,t,a,b):
    n=node(nt,'ShaderNodeMixRGB');connect(nt,n,0,t);connect(nt,n,1,a);connect(nt,n,2,b);return n.outputs[0]
def coords(nt,pos,scale,offset=(0,0,0)):
    return vector(nt,'ADD',vector(nt,'MULTIPLY',pos,scale),offset)
def image(nt,path,uv,data=False,clip=False):
    n=node(nt,'ShaderNodeTexImage');n.image=bpy.data.images.load(str(path),check_existing=True)
    if data:n.image.colorspace_settings.name='Non-Color'
    if clip:n.extension='CLIP'
    connect(nt,n,'Vector',uv);return n.outputs['Color']
def noise(nt,co,scale,detail=2):
    n=node(nt,'ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=detail;connect(nt,n,0,co);return n.outputs[0]
def roughmat(name,color,rough=.77):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough
    return m,bs,m.node_tree
def bump(nt,bs,height,strength,dist,prev=None):
    n=node(nt,'ShaderNodeBump');connect(nt,n,'Height',height);connect(nt,n,'Strength',strength);n.inputs['Distance'].default_value=dist
    if prev is not None:connect(nt,n,'Normal',prev)
    connect(nt,bs,'Normal',n.outputs[0]);return n.outputs[0]
def mesh_obj(name,verts,faces,material=None,smooth=True):
    mesh=bpy.data.meshes.new(name)
    xyz=np.ascontiguousarray(verts,np.float32).reshape(-1,3);ix=np.ascontiguousarray(faces,np.int32)
    mesh.vertices.add(len(xyz));mesh.vertices.foreach_set('co',xyz.ravel())
    mesh.loops.add(ix.size);mesh.loops.foreach_set('vertex_index',ix.ravel())
    mesh.polygons.add(len(ix));mesh.polygons.foreach_set('loop_start',np.arange(0,ix.size,ix.shape[1],dtype=np.int32))
    if smooth:mesh.polygons.foreach_set('use_smooth',np.ones(len(ix),bool))
    mesh.update(calc_edges=True);o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o)
    if material:mesh.materials.append(material)
    return o
def simple_mesh(name,verts,faces,m=None,smooth=False):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob)
    if m:mesh.materials.append(m)
    if smooth:
        for poly in mesh.polygons:poly.use_smooth=True
    return ob
def ctl(nt,name,value=0):
    n=node(nt,'ShaderNodeValue');n.label=name;n.outputs[0].default_value=value
    return n.outputs[0]
def color(a):return (*a,1)
class Terrain:
    def __init__(self,mode):
        self.mode=mode
        self.close_stamp=None;self.floor_displacement=0
        self.D=np.load(P/'dunes2.npy');self.H=np.load(P/'hummocks.npy');self.R=np.load(P/'ripples.npy')
        self.ox=0;self.oy=0
        self.walkwind_land=0.;self.walkwind=R2 and os.environ.get('ONEGRAIN_WALKWIND')=='1'
        # The well and water share a nearly level shelf. The twenty-metre falloff returns to the same natural erg.
        self.flatten=mode in ('well','oasis') or (R2 and mode=='wind')
        self.x0=1.9 if mode=='well' else 0.;self.y0=3.4 if mode=='well' else 0.
    def sample(self,m,u,v):
        h,w=m.shape;u=np.asarray(u)*w;v=np.asarray(v)*h
        xx=np.floor(u).astype(int);yy=np.floor(v).astype(int);fx=u-xx;fy=v-yy
        return ((1-fx)*m[yy%h,xx%w]+fx*m[yy%h,(xx+1)%w])*(1-fy)+((1-fx)*m[(yy+1)%h,xx%w]+fx*m[(yy+1)%h,(xx+1)%w])*fy
    def h(self,x,y):
        d=self.sample(self.D,(x+self.ox)/182+.72,(y+self.oy)/182+.64)
        hm=self.sample(self.H,(x+self.ox*.37)/23+.18,(y+self.oy*.31)/23+.714)
        z=.80*d+.37*hm
        if self.walkwind_land:
            from walkwind.landform import relief
            z+=self.walkwind_land*relief(x+self.ox*.42,y+self.oy*.42)
        if self.flatten:
            r=np.hypot(x-self.x0,y-self.y0);z=z*smooth(2.6,17,r)+1.15*(1-smooth(2.6,17,r))
        return z
    def build(self):
        def axis(a,b,step,far=850):
            mid=list(np.arange(a,b+step*.5,step));u=mid[0];s=step
            left=[]
            while u>-far:s=min(17,s*1.055);u-=s;left.append(u)
            right=[];u=mid[-1];s=step
            while u<far:s=min(17,s*1.055);u+=s;right.append(u)
            return np.array(left[::-1]+mid+right)
        ax=axis(-9,9,.28);ay=axis(-27,27,.32)
        if self.close_stamp is not None:
            cx,cy=foot_xy(self.close_stamp)
            ax=np.unique(np.r_[ax,cx+np.arange(-.132,.133,.0023)])
            ay=np.unique(np.r_[ay,cy+np.arange(-.192,.193,.0023)])
        self.ax,self.ay=ax,ay
        self.xx,self.yy=np.meshgrid(ax,ay)
        x=self.xx.ravel();y=self.yy.ravel()
        if self.close_stamp is not None:
            # Use real recessed sand beneath the raking moon, including the ribs on
            # the flat sole. Only the final print gets the millimetre-scale grid.
            import struct
            stamp_file='settled-11.map' if self.mode=='well' else 'sole-11.map'
            with (TREAD/stamp_file).open('rb') as f:
                width,height,channels=struct.unpack('<iii',f.read(12))
                depth=np.fromfile(f,'<f4').reshape(height,width,channels)[...,0]
            cx,cy=foot_xy(self.close_stamp);a=math.atan(float(pathdx((self.close_stamp-36)*.49)))
            dx=x-cx;dy=y-cy
            u=.5+5*(dx*math.cos(a)-dy*math.sin(a))
            v=.5-(dx*math.sin(a)+dy*math.cos(a))/.326
            window=(u>=0)&(u<=1)&(v>=0)&(v<=1)
            self.floor_displacement=np.zeros(len(x),np.float32)
            self.floor_displacement[window]=.0135*self.sample(depth,u[window],v[window])
        self.xyz=np.column_stack([x,y,self.h(x,y)+self.floor_displacement]).astype('float32')
        q=np.arange(len(x),dtype='int32').reshape(self.xx.shape);faces=np.stack([q[:-1,:-1],q[:-1,1:],q[1:,1:],q[1:,:-1]],2).reshape(-1,4)
        self.obj=mesh_obj('Erg · displaced dune sea',self.xyz,faces)
    def surface(self,x,y):
        ix=np.clip(np.searchsorted(self.ax,x)-1,0,len(self.ax)-2);iy=np.clip(np.searchsorted(self.ay,y)-1,0,len(self.ay)-2)
        u=(x-self.ax[ix])/(self.ax[ix+1]-self.ax[ix]);v=(y-self.ay[iy])/(self.ay[iy+1]-self.ay[iy])
        z=self.xyz[:,2].reshape(len(self.ay),len(self.ax))
        return np.where(u>v,z[iy,ix]*(1-u)+z[iy,ix+1]*(u-v)+z[iy+1,ix+1]*v,z[iy,ix]*(1-v)+z[iy+1,ix]*(v-u)+z[iy+1,ix+1]*u)
    def wave(self,x,y):
        self.ox=x;self.oy=y
        self.xyz[:,2]=self.h(self.xyz[:,0],self.xyz[:,1])+self.floor_displacement;self.obj.data.vertices.foreach_set('co',self.xyz.ravel());self.obj.data.update()
    def sand(self, surface=None):
        if surface is None:
            m,bs,n=roughmat('Sand · low moon, mica and powder',(.26,.17,.095),.86);self.obj.data.materials.append(m)
        else:
            m,bs,n=surface
        pos=node(n,'ShaderNodeNewGeometry').outputs['Position'];x,y,z=split(n,pos)
        self.warp=ctl(n,'wind in the ripples')
        self.slip=ctl(n,'Exposed granular slip faces',0)
        rx=add(n,x,self.warp,mul(n,.045,op(n,'SINE',mul(n,y,1.6))))
        if R2 and self.mode=='wind':
            # Wind ripples bend around the lee face and widen on the exposed slip face.
            rx=add(n,rx,mul(n,.095,op(n,'SINE',add(n,mul(n,1.27,y),mul(n,.38,x)))),mul(n,.13,noise(n,pos,.29)))
        ry=y
        if self.walkwind and self.mode=='wind':
            # Gentle sand waves converge, run out and begin again around a lip.
            # The packed lee and windward face do not share a uniform comb.
            fan=noise(n,coords(n,pos,(.47,.93,.34),(0,0,0)),.73,3.3)
            curl=noise(n,coords(n,pos,(.94,.41,.29),(.17,.63,0)),.89,3.0)
            rx=add(n,x,mul(n,.26,self.warp),mul(n,.96,op(n,'SUBTRACT',fan,.5)),
                   mul(n,.17,op(n,'SINE',add(n,mul(n,.91,y),mul(n,.37,x)))))
            ry=add(n,y,mul(n,.76,op(n,'SUBTRACT',curl,.5)),mul(n,.22,op(n,'SINE',mul(n,.45,x))))
        ripple=image(n,ROOT/'work/maps/ripple.png',coords(n,join(n,rx,ry),(.422,.422,1),(.121,.68,0)),True)
        if self.walkwind and self.mode=='wind':
            # Smaller, oblique ripples overtake the broad bed in irregular patches.
            side=join(n,add(n,mul(n,.92,rx),mul(n,.30,ry)),add(n,mul(n,-.30,rx),mul(n,.92,ry)))
            fine=image(n,ROOT/'work/maps/ripple.png',coords(n,side,(.791,.684,1),(.31,.117,0)),True)
            ripple=blend(n,remap(n,curl,.38,.61),ripple,fine)
        albedo=image(n,ROOT/'work/ref/sand-color.jpg',coords(n,pos,(.66,.66,1),(.2,.31,0)))
        grain=image(n,P/'grain-light.jpg',coords(n,pos,(14.2,14.2,1),(.23,.17,0)))
        micro=image(n,P/'grain-height.png',coords(n,pos,(14.2,14.2,1),(.23,.17,0)),True)
        tint=blend(n,.47,(.147,.158,.183,1),albedo)
        tint=blend(n,.13,tint,grain)
        # Interleaving ripple light and shadow holds the ground texture down to phone scale.
        crest_lit=remap(n,ripple,.28,.76)
        tint=blend(n,.32,tint,blend(n,crest_lit,(.062,.080,.110,1),(.37,.395,.435,1)))
        tint=blend(n,mul(n,.27,ripple),tint,(.295,.306,.337,1))
        if R2 and self.mode=='wind':
            lit=remap(n,ripple,.30,.70)
            tint=blend(n,.26,tint,blend(n,lit,(.027,.039,.060,1),(.49,.53,.60,1)))
        if R2 and self.mode=='walk':
            self.opening_rake=ctl(n,'Raking light on the near ridge',0)
            rip=remap(n,ripple,.30,.72)
            tint=blend(n,self.opening_rake,tint,blend(n,rip,(.021,.032,.053,1),(.46,.51,.59,1)))
        if self.walkwind and self.mode in ('walk','wind','oasis'):
            # Rake the real land normal. Widen the sand scale on the slip face and
            # break the repeated light/dark pattern with displaced patches of exposed sand.
            normal=node(n,'ShaderNodeNewGeometry').outputs['Normal']
            lee=remap(n,dot(n,normal,(-.82,-.47,.19)),-.10,.45)
            lentil=noise(n,coords(n,pos,(.48,1.19,.56),(0,0,0)),.97,3.2)
            separation=add(n,mul(n,.76,lee),mul(n,.24,lentil))
            coarse=blend(n,separation,(.094,.082,.072,1),(.36,.316,.255,1))
            granular=blend(n,.13,coarse,grain)
            tint=blend(n,mul(n,self.slip,add(n,.46,mul(n,.41,lentil))),tint,granular)
        if self.walkwind and self.mode=='oasis':
            from walkwind.land_shade import exposed_erg
            tint=exposed_erg(n,pos,x,y,tint,self.slip)
        connect(n,bs,'Base Color',tint)
        raylen=node(n,'ShaderNodeLightPath').outputs['Ray Length']
        micro_strength=mul(n,.29,op(n,'SUBTRACT',1,remap(n,raylen,1.4,6.5)))
        ripple_strength=mul(n,.64,op(n,'SUBTRACT',1,mul(n,.80,remap(n,raylen,8,49))))
        if self.walkwind and self.mode=='wind':
            ripple_strength=mul(n,ripple_strength,op(n,'SUBTRACT',1,mul(n,.64,lee)))
        normal=bump(n,bs,micro,micro_strength,.0009);relief=bump(n,bs,ripple,ripple_strength,.022,normal)
        if surface is not None:return tint,relief
        self.front=ctl(n,'last illuminated boot');self.road=ctl(n,'faint road');self.ink=ctl(n,'walked road')
        trackpos=pos
        if self.mode=='wind':
            behind=remap(n,op(n,'SUBTRACT',self.front,y),.18,4.2)
            shear=add(n,mul(n,.48,op(n,'SINE',add(n,mul(n,1.6,y),mul(n,-2.3,self.warp)))),mul(n,.22,op(n,'COSINE',add(n,mul(n,.52,y),mul(n,-3.2,self.warp)))))
            trackpos=join(n,add(n,x,mul(n,behind,shear)),y)
        track=split(n,image(n,TREAD/'walk-11.png' if R2 else P/'walker-track.png',coords(n,trackpos,(.1,1/76,1),(.5,28/76,0)),True,True))
        self.draw=ctl(n,'first road drawing');self.gait=ctl(n,'gait');self.network=ctl(n,'through the oasis');self.footheat=ctl(n,'kick reflected in sand')
        gate=remap(n,op(n,'SUBTRACT',self.front,y),-.05,.16)
        existing=remap(n,op(n,'SUBTRACT',self.draw,y),-.9,.5)
        # Resolve the patterned sole at its true local coordinates. The large route map
        # integrates the same alternating marks when the camera rises beyond the heel.
        ordinal=op(n,'FLOOR',add(n,mul(n,y,1/.49),.5));landy=mul(n,ordinal,.49)
        side=add(n,mul(n,2,op(n,'SUBTRACT',ordinal,mul(n,2,op(n,'FLOOR',mul(n,.5,ordinal))))),-1)
        a=add(n,.42,mul(n,.115,landy));b=add(n,-.5,mul(n,.253,landy))
        path=add(n,mul(n,2.35,op(n,'SINE',a)),mul(n,.57,op(n,'SINE',b)))
        deriv=add(n,mul(n,.27025,op(n,'COSINE',a)),mul(n,.14421,op(n,'COSINE',b)))
        ca=op(n,'DIVIDE',1,op(n,'SQRT',add(n,1,mul(n,deriv,deriv))));sa=mul(n,ca,deriv)
        wx,wy,_=split(n,trackpos)
        dx=add(n,wx,mul(n,-1,path),mul(n,-.076,side,ca));dy=add(n,wy,mul(n,-1,landy),mul(n,.076,side,sa))
        across=mul(n,side,add(n,mul(n,dx,ca),mul(n,-1,dy,sa)))
        along=add(n,mul(n,dx,sa),mul(n,dy,ca))
        sole_uv=join(n,add(n,.5,mul(n,5,op(n,'MULTIPLY',side,across) if R2 else across)),add(n,.5,mul(n,.5/.163,along)))
        settled=R2 and self.mode=='well'
        local_file=TREAD/('settled-11.png' if settled else 'sole-11.png') if R2 else P/'qilim-sole.png'
        local=split(n,image(n,local_file,sole_uv,True,True))
        near=op(n,'SUBTRACT',1,remap(n,raylen,4.7,12.2))
        shape=add(n,mul(n,local[1],near),mul(n,track[1],op(n,'SUBTRACT',1,near)))
        tread=add(n,mul(n,local[2],near),mul(n,track[2],op(n,'SUBTRACT',1,near)))
        self.weather=ctl(n,'wind erases the sole',0)
        erosion=mul(n,self.weather,remap(n,op(n,'SUBTRACT',self.front,y),.58,5.6))
        shape=mul(n,shape,op(n,'SUBTRACT',1,erosion))
        pressed=mul(n,gate,remap(n,self.ink,.015,.37),near,shape)
        depression=mul(n,-1,pressed,add(n,.38,mul(n,.62,tread)))
        bump(n,bs,depression,.74,.024,relief)
        granules=add(n,.30,mul(n,.85,ripple),mul(n,1.35,grain))
        band=add(n,.65,mul(n,.35,op(n,'COSINE',op(n,'SUBTRACT',mul(n,y,2.5),mul(n,self.gait,6.283)))))
        road=mul(n,self.road,existing,track[0],.65,granules)
        if R2:
            # Resolve a fine predetermined path beyond the footprint texture. Its angular width integrates
            # as distance grows, so the horizon still contains a thread on the crest reveal.
            curve=add(n,mul(n,2.35,op(n,'SINE',add(n,.42,mul(n,.115,y)))),mul(n,.57,op(n,'SINE',add(n,-.50,mul(n,.253,y)))))
            cross=op(n,'SUBTRACT',wx,curve)
            width=add(n,.019,mul(n,.00082,raylen))
            stroke=gauss(n,op(n,'DIVIDE',cross,width))
            compensation=op(n,'DIVIDE',.034,add(n,.033,mul(n,.00040,raylen)))
            road=mul(n,self.road,existing,stroke,compensation,add(n,.69,mul(n,.33,ripple)))
        if R2 and self.mode=='oasis':
            behind=remap(n,op(n,'SUBTRACT',self.front,y),-.16,.87)
            trace=add(n,.029,mul(n,.971,behind))
            if self.walkwind:
                # The lit route at the approved frond handover is already exposed.
                # As she re-enters the frame, ownership returns to her last footfall.
                self.arrival_trace=ctl(n,'Gold carried through the frond handover',0)
                trace=add(n,self.arrival_trace,mul(n,op(n,'SUBTRACT',1,self.arrival_trace),trace))
            road=mul(n,road,trace)
        walk=mul(n,self.ink,gate,granules,band,add(n,mul(n,.26 if R2 else .62,track[0]),mul(n,shape,add(n,.06 if R2 else .32,mul(n,.65 if R2 else 1.77,tread)))))
        if R2:
            lip,dark,granular=split(n,image(n,TREAD/('settled-rake.png' if settled else 'sole-rake.png'),sole_uv,True,True))
            # Low raking light and the shadow of the upper wall give both strokes actual depth.
            warm=add(n,mul(n,.86 if self.close_stamp is not None else 1.02,lip),mul(n,.31 if self.close_stamp is not None else .44,granular))
            walk=mul(n,self.ink,gate,granules,band,add(n,mul(n,.18,track[0]),mul(n,shape,add(n,.008 if settled else .036,warm))))
            press_col=blend(n,mul(n,gate,near,remap(n,self.ink,.015,.36),op(n,'MINIMUM',1,add(n,mul(n,.42,tread),mul(n,.86,dark)))),tint,(.016,.022,.032,1))
            connect(n,bs,'Base Color',press_col)
        nr=split(n,image(n,D/'footways.png' if R2 else P/'oasis-routes.png',coords(n,pos,(1/216,1/216,1),(.5,.5,0)),True,True))
        if R2 and self.mode=='oasis':
            self.far_paths=ctl(n,'Only the more travelled routes survive the ascent',0)
            distant=split(n,image(n,D/'distant-footways.png',coords(n,pos,(1/216,1/216,1),(.5,.5,0)),True,True))
            nr=[add(n,mul(n,op(n,'SUBTRACT',1,self.far_paths),near),mul(n,self.far_paths,dim)) for near,dim in zip(nr,distant)]
        wave=op(n,'SINE',add(n,mul(n,normlen(n,join(n,x,y)),.3),mul(n,self.gait,-2.4),mul(n,.10,x)))
        routes=mul(n,self.network,add(n,mul(n,2.6,nr[0]),mul(n,1.65,nr[1]),mul(n,.37,nr[2])),add(n,.74,mul(n,.26,wave)),add(n,.78,mul(n,.45,ripple)))
        self.centers=[];self.radii=[];self.width=[];self.power=[];total=add(n,road,walk)
        if self.walkwind and self.mode=='wind':
            # Her outgoing track lives behind her along the same station used for planting.
            X=add(n,x,1.85)
            axis=add(n,-23.97,mul(n,-.117,X),mul(n,1.46,op(n,'SINE',mul(n,.207,X))),mul(n,.51,op(n,'SINE',mul(n,.412,X))))
            off=op(n,'SUBTRACT',y,axis)
            self.heel_x=ctl(n,'Wind heel position',-4)
            trail=remap(n,op(n,'SUBTRACT',self.heel_x,x),-.05,.20)
            width=add(n,.049,mul(n,.00125,raylen))
            grit=add(n,.45,mul(n,.36,ripple),mul(n,.34,noise(n,pos,4.4,2)))
            hot=mul(n,trail,grit,add(n,mul(n,2.35,gauss(n,op(n,'DIVIDE',off,width))),mul(n,.27,gauss(n,mul(n,5.8,off)))))
            self.grove_arrival=ctl(n,'Arrival in the palm stand',0)
            total=add(n,mul(n,hot,op(n,'SUBTRACT',1,self.grove_arrival)),mul(n,total,self.grove_arrival))
        if R2 and self.mode in ('walk','oasis'):
            self.step_surface=ctl(n,'Footfall in granular sand',0)
        for i in range(3):
            co=node(n,'ShaderNodeCombineXYZ');self.centers.append(co)
            rad=ctl(n,'ring radius');wd=ctl(n,'inverse width',6);power=ctl(n,'raking light');self.radii.append(rad);self.width.append(wd);self.power.append(power)
            d=normlen(n,vector(n,'SUBTRACT',join(n,x,y),co.outputs[0]))
            wrinkle=mul(n,.084,op(n,'SUBTRACT',noise(n,pos,4.8),.5))
            crest=gauss(n,mul(n,add(n,op(n,'SUBTRACT',d,rad),wrinkle),wd))
            broad=gauss(n,mul(n,op(n,'SUBTRACT',d,mul(n,.74,rad)),mul(n,.26,wd)))
            if R2 and self.mode in ('walk','oasis'):
                rough=add(n,mul(n,.23,op(n,'SUBTRACT',noise(n,pos,2.5),.5)),
                          mul(n,.067,op(n,'SINE',add(n,mul(n,x,6.7),mul(n,y,3.9)))))
                edge=gauss(n,mul(n,add(n,op(n,'SUBTRACT',d,rad),rough),wd))
                lit=mul(n,remap(n,ripple,.27,.68),remap(n,noise(n,pos,3.2,2),.32,.67))
                broken=mul(n,add(n,mul(n,1.18,edge,lit),mul(n,.10,broad,lit)),add(n,.56,mul(n,1.40,grain)))
                complete=mul(n,add(n,mul(n,.95,crest),mul(n,.23,broad)),add(n,.16,mul(n,1.12,ripple)),add(n,.53,mul(n,1.65,grain)))
                total=add(n,total,mul(n,power,blend(n,self.step_surface,complete,broken)))
            else:
                total=add(n,total,mul(n,power,add(n,mul(n,.95,crest),mul(n,.23,broad)),add(n,.16,mul(n,1.12,ripple)),add(n,.53,mul(n,1.65,grain))))
        # Moving bands illuminate the *relief*. No camera-facing sheets.
        self.roll=ctl(n,'raking crest light');self.rollpos=ctl(n,'dune wave');self.wellstar=ctl(n,'distant well')
        roll=op(n,'COSINE',add(n,mul(n,.65,x),mul(n,.31,y),mul(n,1.95,noise(n,pos,.22)),self.rollpos))
        normal_geo=node(n,'ShaderNodeNewGeometry').outputs['Normal']
        crest=remap(n,dot(n,normal_geo,(-.80,.38,.24)),-.03,.55)
        moonwash=mul(n,self.roll,remap(n,roll,-.7,.94),add(n,.15,mul(n,.85,crest)),add(n,.28,mul(n,.54,ripple)))
        silver=add(n,routes,moonwash)
        # Her path is gold; the crossing routes are cool fibres.
        emission=vector(n,'ADD',vector(n,'MULTIPLY',join(n,total,total,total),((1,.65,.25) if R2 else (1,.46,.135))),vector(n,'MULTIPLY',join(n,silver,silver,silver),(.63,.73,.83)))
        connect(n,bs,'Emission Color',emission);bs.inputs['Emission Strength'].default_value=1
        # Fine mineral haze separates the far dune layers without a camera-facing mesh.
        dist=node(n,'ShaderNodeLightPath').outputs['Ray Length']
        haze=mul(n,.50 if R2 else .78,remap(n,dist,8 if R2 else 6,155 if R2 else 119))
        fog=node(n,'ShaderNodeEmission');fog.inputs['Color'].default_value=(.077,.092,.142,1);fog.inputs['Strength'].default_value=.70
        shader=node(n,'ShaderNodeMixShader');connect(n,shader,0,haze);connect(n,shader,1,bs.outputs[0]);connect(n,shader,2,fog.outputs[0])
        connect(n,n.nodes.get('Material Output'),'Surface',shader.outputs[0])
    def ring(self,i,x,y,radius,width,power):
        c=self.centers[i];c.inputs['X'].default_value=x;c.inputs['Y'].default_value=y
        self.radii[i].default_value=radius;self.width[i].default_value=1/max(.001,width);self.power[i].default_value=power
class Actor:
    def __init__(self,model_boots=False):
        self.walkwind=R2 and os.environ.get('ONEGRAIN_WALKWIND')=='1'
        lib=C.CDLL(str(ROOT/'work/walkwind/actor.dylib' if self.walkwind else P/'actor.dylib'));self.lib=lib
        lib.rough_pose.argtypes=[C.c_int]+[C.c_float]*4
        lib.rough_data.argtypes=[C.c_void_p]*3
        N=lib.rough_pose(0,0,3,0,0)
        self.points=np.empty((N*3,3),np.float32);uv=np.empty((N*3,2),np.float32);mat=np.empty(N,np.int32)
        lib.rough_data(self.points.ctypes.data,uv.ctypes.data,mat.ctypes.data)
        # Index by sewn panel corners, preserving the independently moving panels.
        _,self.index,inv=np.unique(np.round(self.points,6),axis=0,return_index=True,return_inverse=True)
        keep=~np.isin(mat,[5,13]) if model_boots else np.ones(len(mat),dtype=bool)
        self.obj=mesh_obj('Traveller · original coat, gait and LOVE cap',self.points[self.index],inv.reshape(-1,3)[keep])
        mesh=self.obj.data
        palette=[(.40,.306,.204),(.34,.242,.152),(.47,.386,.278),(.32,.20,.09),(.14,.102,.075),(.12,.066,.044),(.23,.142,.079),(.63,.007,.017),(.66,.009,.019),(.80,.71,.56),(.49,.36,.205),(.25,.18,.12),(.22,.15,.078),(.074,.056,.040)]
        names=['Wrap','Sleeve','Hood','Cord','Trousers','Worn boot','Gloves','Madder knit','Folded cuff','Wool pom','Scarf','Hem','Bag','Leather welt']
        if self.walkwind:
            from walkwind.materials import character_palette
            character_palette(palette,names)
            self.rig_state=np.empty(15,np.float32);lib.ww_rigs.argtypes=[C.c_void_p]
        for k,(name,col) in enumerate(zip(names,palette)):
            m,bs,n=roughmat(name,col,.63 if k==5 else .84);mesh.materials.append(m)
            co=node(n,'ShaderNodeTexCoord').outputs['UV']
            if self.walkwind and k in (0,1,2,11):
                bs.inputs['Emission Color'].default_value=(*col,1);bs.inputs['Emission Strength'].default_value=.070
                bs.inputs['Sheen Weight'].default_value=.20
            if self.walkwind and k==14:
                bs.inputs['Roughness'].default_value=.44;bs.inputs['Sheen Weight'].default_value=.30
            if k in (7,8):
                bs.inputs['Sheen Weight'].default_value=.31
                bs.inputs['Emission Color'].default_value=(*col,1);bs.inputs['Emission Strength'].default_value=.14
            if k==8:
                text=image(n,ROOT/'work/maps/love.png',coords(n,co,(1/.323,1/.87,0),(.5-.603/.323,1-.94/.87,0)),True,True)
                connect(n,bs,'Base Color',blend(n,text,(*col,1),(.93,.86,.72,1)))
            if k==10 and R2:
                bs.inputs['Base Color'].default_value=(.57,.005,.018,1)
                bs.inputs['Emission Color'].default_value=(.46,.005,.017,1);bs.inputs['Emission Strength'].default_value=.38
                bs.inputs['Sheen Weight'].default_value=.38
            if k==0 or (k==10 and not R2):
                u,v,_=split(n,co)
                stripe=mul(n,op(n,'GREATER_THAN',v,.024 if k==0 else .84),op(n,'LESS_THAN',v,.09 if k==0 else .91))
                diamonds=add(n,.59,mul(n,.36,op(n,'COSINE',add(n,mul(n,285,u),mul(n,145,op(n,'ABSOLUTE',op(n,'SUBTRACT',v,.055)))))))
                connect(n,bs,'Base Color',blend(n,mul(n,stripe,diamonds),(*col,1),(.129,.081,.041,1)))
        if R2:
            self.point_mats=np.repeat(mat,3)
            self.point_uv=uv.copy()
        mesh.polygons.foreach_set('material_index',mat[keep])
        tex=mesh.uv_layers.new(name='Sewn panels');tex.data.foreach_set('uv',np.ascontiguousarray(uv.reshape(-1,3,2)[keep]).ravel())
    def pose(self,i,ph,t,x,y,z,angle,sx,sy):
        key=(i%2,ph,t,x,y,z,angle,sx,sy)
        if getattr(self,'last_pose',None)==key:return
        self.last_pose=key
        if self.walkwind:
            self.lib.rough_pose(i%2,ph,t,sx,sy);self.lib.rough_data(self.points.ctypes.data,None,None)
            self.lib.ww_rigs(self.rig_state.ctypes.data)
            self.obj.data.vertices.foreach_set('co',np.ascontiguousarray(self.points[self.index]).ravel())
            self.obj.data.update();self.obj.location=(x,y,z);self.obj.rotation_euler[2]=-angle
            return
        performance_phase=ph
        if R2:
            # Let the swing linger at her look back, then catch the next actual heel
            # contact. Its speed varies by phrase without displacing the planted shoe.
            hesitate=smooth(23.7,25.0,t)*(1-smooth(26.5,28.1,t))
            breath=.086*math.sin(.73*t)+.035*math.sin(1.17*t)-.145*hesitate
            performance_phase+=math.sin(math.pi*ph)**2*breath*(1-smooth(160.1,163,t))
        self.lib.rough_pose(i%2,performance_phase,t,sx,sy);self.lib.rough_data(self.points.ctypes.data,None,None)
        if R2:
            advance=.49*(performance_phase-ph)
            self.points[:,1]+=advance;self.points[:,2]+=sy*advance
            for leg in np.split(np.flatnonzero(self.point_mats==4),2):
                height=self.points[leg,2];bottom=height.min()
                self.points[leg,2]+=.063*(1-smooth(0,.20,height-bottom))
            coat=self.point_mats==0
            u=self.point_uv[coat,0];v=self.point_uv[coat,1]
            self.points[coat,0]+=(1-v)**2*(.051*np.sin(9*u-3.7*t)-.036)
            from gesture import pose as gesture_pose
            gesture_pose(self,i,performance_phase,t)
        self.obj.data.vertices.foreach_set('co',np.ascontiguousarray(self.points[self.index]).ravel());self.obj.data.update()
        self.obj.location=(x,y,z);self.obj.rotation_euler[2]=-angle
def sky(scene):
    scene.world.use_nodes=True
    n=scene.world.node_tree;n.nodes.clear();out=node(n,'ShaderNodeOutputWorld');bg=node(n,'ShaderNodeBackground')
    normal=node(n,'ShaderNodeTexCoord').outputs['Generated'];x,y,z=split(n,normal)
    env=node(n,'ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(ROOT/'work/r2/galactic-high.jpg'),check_existing=True)
    # Sky texture points are world-locked while the camera passes under them.
    connect(n,env,0,vector(n,'ADD',normal,(.01,-.27,.1)))
    grad=remap(n,z,-.025,.49)
    horizon=blend(n,remap(n,x,-1,.78),(.076,.089,.139,1),(.080,.101,.163,1))
    c=blend(n,grad,horizon,(.007,.015,.041,1))
    c=vector(n,'ADD',c,vector(n,'MULTIPLY',env.outputs[0],(.069,.089,.147)))
    direction=node(n,'ShaderNodeCombineXYZ');direction.inputs['X'].default_value=-.43;direction.inputs['Y'].default_value=.875;direction.inputs['Z'].default_value=.19
    dv=normlen(n,vector(n,'SUBTRACT',normal,direction.outputs[0]));disc=op(n,'SUBTRACT',1,remap(n,dv,.0215,.023))
    halos=add(n,mul(n,.23,gauss(n,mul(n,dv,22))),mul(n,.08,gauss(n,mul(n,dv,6.2))))
    dx,dy,dz=split(n,vector(n,'SUBTRACT',normal,direction.outputs[0]))
    moonuv=join(n,add(n,.47,mul(n,16.8,dx)),add(n,.51,mul(n,14.3,dz)))
    craters=image(n,ROOT/'work/ref/moon.jpg',moonuv,True)
    limb=remap(n,add(n,dx,mul(n,.42,dz)),-.020,.006)
    moonlight=add(n,.47,mul(n,3.2,craters,add(n,.14,mul(n,.86,limb))))
    c=vector(n,'ADD',c,vector(n,'MULTIPLY',join(n,*([add(n,mul(n,moonlight,disc),halos)]*3)),(.75,.84,1)))
    connect(n,bg,'Color',c);bg.inputs['Strength'].default_value=.79
    connect(n,out,'Surface',bg.outputs[0]);return direction
def sun(name,dir,energy,col,angle):
    a=bpy.data.lights.new(name,'SUN');a.energy=energy;a.color=col;a.angle=angle;o=bpy.data.objects.new(name,a);bpy.context.scene.collection.objects.link(o)
    o.rotation_euler=(-Vector(dir)).to_track_quat('-Z','Y').to_euler();return o
def point(name,col,r):
    a=bpy.data.lights.new(name,'POINT');a.color=col;a.shadow_soft_size=r
    o=bpy.data.objects.new(name,a);bpy.context.scene.collection.objects.link(o);return o
