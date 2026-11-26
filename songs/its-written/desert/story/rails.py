"""One pen seen on a slip face, lifted through the air and carried between stars."""
from world import *
from performer import Girl
from mathutils import Matrix
from functools import lru_cache

@lru_cache(maxsize=1)
def pen():
    src=(ROOT/'src/assets.py').read_text()
    code=src[src.index('strokes=[]'):src.index('# World coords:')]
    ns={'np':np};exec(compile(code,'Original writing curves','exec'),ns)
    return ns['strokes']
def sampled(points,d):
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    a=np.asarray(d)*arc[-1];return np.stack([np.interp(a,arc,points[:,i]) for i in range(points.shape[1])],axis=-1)
def bezier(start,segments,n=54):
    out=[start];a=np.array(start,float)
    u=np.linspace(0,1,n)[1:,None]
    for seg in segments:
        b,c,d=np.array(seg).reshape(3,-1)
        out.extend((1-u)**3*a+3*u*(1-u)**2*b+3*u*u*(1-u)*c+u**3*d);a=d
    return np.array(out)
def bend(t,keys):return interpolate(t,keys)[0]
class SandSpray:
    def __init__(self,S,N=480):
        self.rng=np.random.default_rng(710).random((N,9));self.seed=N
        self.mesh=mesh_obj('Grains thrown at her ankles',np.zeros((N*4,3)),np.arange(N*4).reshape(N,4),S.hot,False)
        self.mesh.data.materials.append(S.gold);self.mesh.data.polygons.foreach_set('material_index',(self.rng[:,3]>.28).astype('i'))
    def frame(self,g,fr,strength):
        r=self.rng;u=(fr/30*(1.03+r[:,0])+.97*r[:,1])%1
        sign=np.where(r[:,2]>.5,1,-1);age=u*(.27+.46*r[:,3])
        p=np.c_[sign*(.06+age*(.47+1.18*r[:,4])),.36-age*(2.95+4.5*r[:,6]),.015+age*(.72+2.1*r[:,5])-2.75*age**2]
        pos=g.pos+(p*g.scale)@g.rot.T
        rad=(.002+.009*r[:,8]**2)*np.sin(np.pi*u)**.52*strength
        axes=np.array([[-1,0,-.3],[0,-.76,.73],[1,0,.3],[0,.84,-.48]])
        verts=pos[:,None,:]+rad[:,None,None]*axes[None,:,:]
        self.mesh.data.vertices.foreach_set('co',verts.astype('f').ravel());self.mesh.data.update()
class Ribbon:
    def __init__(self,S,name,xyz,width=.25):
        self.w=width;self.n=len(xyz);self.world=S
        # The broad mark has two bright rims and a deeper, worn centre in cross section.
        self.side=material(name+' • bevel',(.43,.18,.024),.68,.37)
        self.mid=material(name+' • satin gold',(.89,.42,.055),.92,.41)
        cross=[(-1.,0),(-.86,.055),(-.58,.070),(0,.045),(.58,.070),(.86,.055),(1,0),(.76,-.10),(-.76,-.10)]
        self.cross=np.array(cross);self.taper=1.;nr=len(cross)
        faces=[(j*nr+i,(j+1)*nr+i,(j+1)*nr+(i+1)%nr,j*nr+(i+1)%nr) for j in range(self.n-1) for i in range(nr)]
        self.mesh=mesh_obj(name,np.zeros((self.n*nr,3)),faces,self.mid)
        self.mesh.data.materials.append(S.gold);self.mesh.data.materials.append(self.side)
        self.mesh.data.polygons.foreach_set('material_index',np.tile([1,1,0,0,1,1,2,2,2],self.n-1).astype('i'))
        self.update(xyz)
    def update(self,xyz):
        # Width is normal to the path in plan, so lifted loop crests retain their broad face.
        self.xyz=xyz;v=unit(np.gradient(xyz,axis=0));side=unit(np.cross(v,[0,0,1]));up=unit(np.cross(side,v))
        co=xyz[:,None,:]+self.w*self.taper*(side[:,None,:]*self.cross[None,:,0:1]+up[:,None,:]*self.cross[None,:,1:])
        self.mesh.data.vertices.foreach_set('co',co.astype('f').ravel());self.mesh.data.update()
def well(S,x,y):
    # The final approach looks back on these same three courses and sees the same worn arrises.
    with np.load(D/'water-camera.npz') as registration:
        vv=registration['verts'].copy();faces=registration['tri'].copy()
    ground=S.ground(x,y,.034);vv+=ground
    stone=material('Calcareous stone in low moonlight',(.365,.26,.167),.012,.88)
    nodes=stone.node_tree;shader=nodes.nodes.get('Principled BSDF');p=node(nodes,'ShaderNodeNewGeometry').outputs['Position']
    color=blend(nodes,noise(nodes,p,12.3,3),(.125,.099,.069,1),(.43,.36,.272,1));connect(nodes,shader,'Base Color',color)
    bump=node(nodes,'ShaderNodeBump');bump.inputs['Strength'].default_value=.32;bump.inputs['Distance'].default_value=.017
    connect(nodes,bump,'Height',noise(nodes,p,99,3));connect(nodes,shader,'Normal',bump.outputs[0])
    mesh_obj('The same three courses of the well',vv,faces,stone)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.984,depth=.027,location=ground+[0,0,.005])
    bpy.context.object.data.materials.append(material('Still well water',(.007,.018,.029),.045,.12))
class Ride:
    def __init__(self,S,which):
        self.S=S;self.which=which;self.finish=os.environ.get('FINISH_STORY')=='1';self.g=Girl(S);self.spray=SandSpray(S)
        if which=='slide':
            xy=bezier([0,-20],[[[-.5,-13],[-4,-10],[-3,-5]],[[-2,1],[8,6],[8,13]],[[8,20],[-4,22],[-3,30]],[[-2,39],[13,36],[18,34]]])
            self.xyz=S.surface(sampled(xy,np.linspace(0,1,500)),.078)
            self.rail=Ribbon(S,'The downstroke',self.xyz,.215)
        elif which=='coaster':
            self.strokes=[];self.rails=[]
            # Scale the original pen into the erg. Fold the page up about its baseline;
            # each stroke has a small depth component, separating its returning strokes.
            for k,raw in enumerate(pen()):
                count=max(50,len(raw)//2)
                if k==4:count=1120
                xy=sampled(raw,np.linspace(0,1,count))
                x=(xy[:,0]-230)*.270; y=(xy[:,1]-1)*.285
                flat=S.surface(np.c_[x,y],.105)
                u=np.linspace(0,1,len(x))
                lifted=np.c_[x,-.08*x+3.6*np.sin(x*.074)+y*.40+2.2*np.sin(u*5*np.pi)+u*(54 if k==4 else 11),S.floor(x,-.08*x)+3.0+.40*(1+np.sin(.08*x))+np.maximum(y,-1.1)*.99]
                if k==4:
                    # Swing the written page open along the depth of the dune. Round the tiny pen
                    # inflections before they take a person, leaving the original nib intact on the sand.
                    radius=max(4,round(count*.058));i=np.arange(-radius,radius+1);kernel=np.exp(-.5*(i/(radius/2.75))**2);kernel/=kernel.sum()
                    def soften(v):return np.convolve(np.pad(v,radius,mode='edge'),kernel,'valid')
                    xx=soften(x);zz=soften(y)
                    lifted=np.c_[xx,-3.0-.065*xx+u*117+2.8*np.sin(2.7*np.pi*u),S.floor(xx,-.08*xx)+6.4+1.1*np.sin(u*2.4*np.pi)+np.maximum(zz,-1.1)*.94]
                    # Keep the flourish high enough to see the full print before we descend into it.
                    lifted[:,2]+=6.8*smooth(.71,.99,u)
                self.strokes.append((flat,lifted))
                self.rails.append(Ribbon(S,'Raised handwriting '+str(k),flat,.235 if k==4 else .13))
            # Leave the final stroke at height, then follow it all the way into the print.
            end=self.strokes[4][1][-1]
            self.drop_rel=bezier([0,0,0],[[[3,1,1.4],[6,2,5],[8,6,5.9]],[[10,10,6.1],[11.4,14,3.6],[11.8,16.5,.6]],[[12.3,19,-3.8],[12.4,20.8,-11],[12.2,21.5,-15]]])
            self.drop_rel[:,2]+=(S.floor(end[0]+12.2,end[1]+21.5)+.12-end[2]-self.drop_rel[-1,2])*np.linspace(0,1,len(self.drop_rel))**4
            self.drop=Ribbon(S,'Flourish into the grain',end+self.drop_rel,.21)
            self.drop.taper=(1-.985*smooth(.64,.99,np.linspace(0,1,len(self.drop_rel))))[:,None,None]
            toe=(end+self.drop_rel[-1])[:2];self.toe=S.ground(*toe,.12);press(S,*toe)
            sphere('Grain inside the dropped stroke',S.ground(*toe,.11),(.078,.061,.089),S.hot)
        else:
            self.setup_sky()
    def oriented(self,path,u,fr,seat,opening,eyes=False,bank=0,gaze=0,tilt=0):
        g=self.g
        delta={'night':.052,'coaster':.035}.get(self.which,.012)
        p=sampled(path,u);ahead=sampled(path,min(1,u+delta));back=sampled(path,max(0,u-delta));v=unit(ahead-back)
        # She can side-slip on the stroke. The seated body keeps its bearing as the pen curls beneath it.
        lateral=v[0];forward=v[1]
        if self.which=='night':lateral*=.80;forward=.42+.82*forward
        if self.which=='coaster':lateral*=.86;forward=.24+.9*forward
        yaw=-math.atan2(lateral,forward);pitch=.77*math.asin(np.clip(v[2],-.96,.96))
        if self.finish and self.which=='night' and 4625<=fr<=4725:
            # Bank towards the well before the capital doubles back; her eyes lead the descent.
            # The old tangent swung past zero and reversed yaw on three adjacent pictures.
            target=self.wellmark-p
            towards=-math.atan2(target[0],target[1])
            weight=smooth(4625,4650,fr)*(1-smooth(4703,4725,fr))
            yaw+=weight*math.atan2(math.sin(towards-yaw),math.cos(towards-yaw))
            pitch=mix(pitch,-.26-.27*smooth(4650,4691,fr),weight)
        g.pose(fr,p+[0,0,.010],heading=yaw,seat=seat,opening=opening,wind=.83 if self.which!='slide' else .62,
               pitch=pitch,bank=bank,gaze=gaze,tilt=tilt,eyes=eyes)
        return p,v
    def from_eyes(self,fr,down,lens,roll=.0):
        g=self.g;S=self.S
        C=g.world(g.eyes+[0,.035,.018]);look=C+g.rot@np.array([.023*math.sin(fr*.027),2.1,-(down*.68+.83)])
        S.view(C,look,lens,roll,up=g.rot[:,2])
    def settle_eye(self,fr,first,last,eye_local,down,lens):
        s=self.S;g=self.g;q=smooth(first,last,fr)
        start=np.array(s.cam.location);basis=np.array(s.cam.rotation_quaternion.to_matrix())
        goal=g.world(g.eyes+eye_local);swing=g.rot@np.array([-.56,.04,.43])
        pos=mix(start,goal,q)+swing*np.sin(np.pi*q)
        direction=unit(mix(-basis[:,2],unit(g.rot@np.array([.01,2.1,-down])),q))
        s.view(pos,pos+direction,mix(s.cam.data.lens,lens,q),0,up=unit(mix(basis[:,1],g.rot[:,2],q)))
    def slide(self,fr):
        S=self.S;g=self.g
        u=bend(fr,[(1505,.08),(1528,.10),(1547,.108),(1561,.14),(1585,.31),(1616,.49),(1645,.64),(1668,.80),(1681,.91)])
        seated=smooth(1520,1555,fr)*(1-.84*smooth(1666,1681,fr));opening=.22+.78*smooth(1632,1658,fr)
        if self.finish:
            u=bend(fr,[(1505,.050),(1520,.085),(1533,.141),(1561,.252),(1585,.401),(1616,.552),(1645,.700),(1668,.81),(1681,.91)])
            seated=smooth(1505,1520,fr)*(1-.84*smooth(1666,1681,fr))
        pov=fr>=(1626 if self.finish else 1601)
        eyes=smooth(1612,1626,fr) if self.finish else pov
        p,v=self.oriented(self.xyz,u,fr,seated,opening,eyes,bank=.045*np.sin(fr*.059),gaze=.18)
        self.rail.taper=(.20+.80*np.exp(-(np.linalg.norm(self.xyz-p,axis=1)/3.9)**2))[:,None,None];self.rail.update(self.xyz)
        if fr>=1659:
            # Rise out ahead of her hands, clear the pom, then look back along the stroke she has just ridden.
            q=smooth(1658,1681,fr);eye=g.world(g.eyes+[0,.035,.018]);v0=g.rot@np.array([.023*math.sin(fr*.027),2.1,-1.34])
            c=eye+g.rot@(np.array([5.1,-5.6,5.55])*q**1.41+[0,.66*np.sin(np.pi*q),.59*np.sin(np.pi*q)])
            lens=15.6+14.4*q
            # The original reveal finds her cap on the upper right. Let the
            # ridden stroke recede to the lower left as she stands up at its end.
            ray=unit(eye-c);fw=ray.copy()
            alpha=.428*q*36/lens;beta=.276*q*(9/16)*36/lens
            for _ in range(6):
                right=unit(np.cross(fw,[0,0,1]));up=unit(np.cross(right,fw))
                fw=unit(ray*np.sqrt(1+alpha*alpha+beta*beta)-alpha*right-beta*up)
            t=mix(eye+v0,c+fw*max(.35,np.linalg.norm(eye-c)),smooth(.08,.76,q))
            if fr>=1664:
                for ob in [*g.head_objects,g.mantle[0],g.collar,g.throat,g.wrap]:ob.hide_render=False
            S.view(c,t,lens,.027*np.sin(fr*.053)*(1-q),up=mix(g.rot[:,2],[0,0,1],q))
        elif pov:self.from_eyes(fr,1.07-.32*smooth(1636,1656,fr),15.6,.027*np.sin(fr*.053))
        else:
            cam=interpolate(fr,[(1505,-3.0,-4.8,2.10),(1530,-2.9,-3.65,1.70),(1554,-3.6,-2.12,1.24),(1586,-3.20,-1.45,1.05),(1601,-2.7,-.92,.93)])
            if self.finish:
                cam=interpolate(fr,[(1505,-3.0,-4.3,2.15),(1520,-3.55,-3.4,1.90),(1548,-4.35,-1.85,1.25),
                                    (1582,-4.51,-.65,1.02),(1608,-3.16,-2.35,1.54),(1626,-1.34,-2.05,1.45)])
            C=g.world(cam);look=g.world([.03,.32,.64-.14*seated])
            # Keep the slip face below the seated rider even across the nearer, irregular lip.
            centre=g.world([0,.03,.10]);q=np.linspace(0,.96,44);ray=C+(centre-C)*q[:,None]
            ground=S.floor(ray[:,0],ray[:,1])+.13*(1-q)
            C[2]=max(C[2]+.32,float(np.max((ground-centre[2]*q)/(1-q))))
            S.view(C,look,28,.053*np.sin((fr-1510)*.036))
        if self.finish and 1612<=fr<1626:
            self.settle_eye(fr,1612,1626,np.array([0,.035,.018]),1.558,15.6)
        self.spray.frame(g,fr,smooth(1512,1532,fr) if self.finish else smooth(1547,1567,fr))
    def coaster(self,fr):
        S=self.S;g=self.g;q=smooth(2288,2345,fr)
        for (flat,high),rail in zip(self.strokes,self.rails):
            # The tail rises a handful of frames after the loop ahead of it.
            factor=smooth(0,1,np.clip(q*1.15-.15*np.linspace(0,1,len(flat)),0,1))[:,None]
            rail.update(mix(flat,high,factor))
        end=self.rails[4].xyz[-1];ext=self.drop_rel.copy()
        ext[:,2]*=q
        drop=end+ext
        self.drop.update(drop);self.drop.mesh.hide_render=bool(q<.016)
        line=np.vstack([self.rails[4].xyz,drop[1:]])
        u=bend(fr,[(2285,.06),(2320,.10),(2343,.17),(2374,.29),(2409,.47),(2442,.58),(2477,.69),(2500,.77),(2529,.855),(2547,.923),(2566,.999)])
        # Between the pen's more tightly folded letters, use the approaching tangent to damp yaw.
        pov=fr>=2477
        p,v=self.oriented(line,u,fr,1,.68+.32*smooth(2457,2488,fr),pov,.108*np.sin((fr-2300)*.055),gaze=-.06,tilt=-.02)
        if fr<2417:
            # One crane passes from above the sheet to her left shoulder, around to the front.
            # Extending the track in depth leaves the entire camera arm clear of the adjacent strokes.
            a=bend(fr,[(2286,-2.75),(2340,-2.72),(2365,-2.44),(2383,-1.82),(2397,-1.32),(2408,-1.17),(2417,-1.00)])
            radius=bend(fr,[(2286,8.0),(2341,7.8),(2363,6.1),(2393,4.55),(2402,3.94),(2417,2.86)])
            ht=bend(fr,[(2286,4.2),(2340,3.95),(2362,2.09),(2384,1.44),(2397,1.16),(2417,1.02)])
            arm=g.world([radius*np.sin(a),radius*np.cos(a),ht])
            lift=smooth(2276,2358,fr)
            wide=np.array([-14.3+.093*(fr-2286),-56.6+.23*(fr-2286),135-.32*(fr-2286)])
            C=mix(wide,arm,lift)
            near=g.world([0,.91*(1-smooth(2398,2417,fr))-.025,.77+.02*smooth(2400,2417,fr)])
            T=mix(np.array([-10.4,9,2.18]),near,lift)
            up=mix([0,1,0],g.rot[:,2],smooth(2286,2350,fr))
            lens=bend(fr,[(2286,28),(2358,28),(2385,32),(2401,34),(2417,34.5)])
            S.view(C,T,lens,.041*np.sin((fr-2286)*.034)*lift*(1-smooth(2398,2417,fr)),up=up)
        elif fr<=2476:
            # The studio performs looking along -Y; a half-turn registers its camera to the seated rider's +Y.
            t=(fr-2417)/59
            C=g.world([.072*np.cos(np.pi*t),1.61,1.04])
            T=g.world([0,-.025,.79]);S.view(C,T,44,0,up=g.rot[:,2])
        elif fr<=2537:
            down=bend(fr,[(2477,.58),(2496,.76),(2520,.62),(2537,.62)])
            self.from_eyes(fr,down,15.6,roll=.028*np.sin(fr*.051))
        else:
            # Over the last stroke. Her hands pass below the lens as the camera falls straight into the footway.
            dive=smooth(2537,2552,fr);toe=self.toe
            c0=g.world(g.eyes+[0,.035,.018]);t0=c0+g.rot@np.array([0,2.1,-1.25])
            h=bend(fr,[(2537,18.0),(2547,13.8),(2552,10.4),(2560,7.21),(2566,5.4)])
            c1=toe+[-.11*h,-.18*h,h];t1=toe+[.01,.08,0]
            cam=mix(c0,c1,dive);target=mix(t0,t1,dive)
            S.view(cam,target,15.6+12.4*dive,.010*(1-dive),up=mix(g.rot[:,2],[-.32,.94,0],dive))
            if fr>=2551:
                for ob in g.root.children_recursive:ob.hide_render=True
        self.spray.frame(g,fr,.62)
    def setup_sky(self):
        S=self.S
        # The rising approach, a loop of the original capital, and a long descent to the well.
        raw=sampled(pen()[0],np.linspace(0,1,180))
        z=34+raw[:,1]*.225
        # The pen doubles back in its plane, but the journey always advances across the night.
        # Open that fold into depth so the rider banks through the capital without a reversed bearing.
        u=np.linspace(0,1,len(raw));inscription=np.c_[(raw[:,0]+10)*.30,18+.083*raw[:,0]+.10*raw[:,1]+u*65,z]
        begin=inscription[0];tip=inscription[-1]
        launch=bezier([-21,-29,S.floor(-21,-29)+.13],[[[-23,-20,1],[-27,-11,7],[-24,-3,15]],[[-22,4,23],begin-[3,5,2],begin]])
        yend=tip[1]+(35 if self.finish else 54)
        S.settle(16.0,yend+3.45,2.6,6.8)
        e=S.ground(15,yend,.13);self.arrival=e;self.wellmark=S.ground(16.0,yend+3.45,.55)
        # The last star spills down the long face. The tangent levels out by the water.
        fall=bezier(tip,[[tip+[3,4,1],[16,tip[1]+8,tip[2]+2],[18,tip[1]+13,tip[2]]],[[20,tip[1]+21,tip[2]-3.3],[19,tip[1]+26,tip[2]-8.8],[17.7,tip[1]+34,e[2]+12]],[[16.7,tip[1]+43,e[2]+5.2],e-[.23,3.9,0],e]])
        if self.finish:
            fall=bezier(tip,[[tip+[2,2.5,1],[17,tip[1]+5,tip[2]+1.6],[18,tip[1]+8,tip[2]-.9]],
                        [[19,tip[1]+12,tip[2]-4],[17.8,tip[1]+18,e[2]+12],[16.2,tip[1]+26,e[2]+6.1]],
                        [[15.5,tip[1]+30,e[2]+2.4],e-[.14,2.2,0],e]])
        path=sampled(np.vstack([launch,inscription[1:],fall[1:]]),np.linspace(0,1,1100))
        tr=np.arange(-41,42);kernel=np.exp(-.5*(tr/13.5)**2);kernel/=kernel.sum()
        floating=np.column_stack([np.convolve(np.pad(axis,41,mode='edge'),kernel,'valid') for axis in path.T])
        u=np.linspace(0,1,len(path));self.xyz=mix(path,floating,(smooth(.008,.055,u)*(1-smooth(.95,.993,u)))[:,None])
        if self.finish:
            # Leave the crest on one falling stroke. The return leg of the old
            # capital folded across the eye and briefly filled the frame with gold.
            old_arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(self.xyz,axis=0),axis=1))]
            self.pen_clock=old_arc/old_arc[-1]
            i,j=np.searchsorted(self.pen_clock,[.530,.900])
            t=np.linspace(0,1,j-i+1)[:,None]
            p0,p3=self.xyz[i].copy(),self.xyz[j].copy()
            length=(old_arc[j]-old_arc[i])/3
            p1=p0+length*unit(self.xyz[i+1]-self.xyz[i-1])
            p2=p3-length*unit(self.xyz[j+1]-self.xyz[j-1])
            fall=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3
            fall[:,0]-=4.8*np.sin(np.pi*t[:,0])**2
            self.xyz[i:j+1]=fall
            new_arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(self.xyz,axis=0),axis=1))]
            self.ride_clock=new_arc/new_arc[-1]
            with np.load(D/'water-camera.npz') as w:
                self.landing_camera=w['camera'][:2]
            self.water_level=S.ground(16.0,yend+3.45,.034)
        self.rail=Ribbon(S,'Stellar road',self.xyz,.18)
        if self.finish:
            self.rail.taper=(1-.85*smooth(.946,.998,self.pen_clock))[:,None,None]
            self.rail.update(self.xyz)
        for raw in pen()[1:]:
            # The detached letter strokes project as vertical scratches during the bank.
            # The travelled capital and star knots remain the writing in this view.
            if self.finish:continue
            xx=(raw[:,0]+10)*.30;yy=18+.083*raw[:,0]+.10*raw[:,1];zz=34+raw[:,1]*.225
            points=np.c_[xx,yy,zz];tube('The other strokes',points,S.gold,.048)
            self.star_nodes(sampled(points,np.linspace(0,1,max(3,int(len(raw)/10)))),S,.043,4)
        self.star_nodes(sampled(inscription,np.linspace(0,1,70)),S,.045,1)
        rng=np.random.default_rng(890);spr=rng.normal(size=(2800,3));spr[:,2]=np.abs(spr[:,2]);spr=unit(spr)*rng.uniform(260,710,(len(spr),1))
        self.star_nodes(spr,S,.19,3,sky=True)
        dust=sampled(self.xyz,np.linspace(0,1,1900))
        dust+=rng.normal(size=dust.shape)*[2.6,2.6,1.2]
        self.star_nodes(dust,S,.009,8)
        # Grain near the lens changes size and bears across the far stars as she climbs.
        near=sampled(self.xyz,rng.uniform(.08,.90,6200))
        offsets=rng.normal(size=near.shape)*[7.9,4.5,3.3];near+=offsets
        near=near[np.linalg.norm(offsets,axis=1)>1.3]
        self.star_nodes(near,S,.014,29,nearby=True)
        press(S,e[0]-.13,yend+1.32,.47,1.04)
        well(S,16.0,yend+3.45)
    def star_nodes(self,points,S,radius,seed,sky=False,nearby=False):
        rng=np.random.default_rng(seed);sz=radius*rng.uniform(.28,1.65,len(points))**1.7
        corners=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]])
        verts=points[:,None,:]+sz[:,None,None]*corners;local=np.array([(0,2,4),(2,1,4),(1,3,4),(3,0,4),(0,5,2),(2,5,1),(1,5,3),(3,5,0)])
        faces=(np.arange(len(points))[:,None,None]*6+local[None,:,:]).reshape(-1,3)
        mat=material('Silver stars',(.70,.83,1),5.4) if sky else S.hot
        if not sky:
            mat=material('Motes at the limit of focus',(.56,.55,.49) if nearby else (1,.74,.35),1.38 if nearby else 3.80)
            n=mat.node_tree;eye=node(n,'ShaderNodeCameraData');ramp=node(n,'ShaderNodeMapRange')
            ramp.inputs['From Min'].default_value=1.44;ramp.inputs['From Max'].default_value=4.8
            connect(n,ramp,'Value',eye.outputs['View Distance'])
            transparent=node(n,'ShaderNodeBsdfTransparent');blend_shader=node(n,'ShaderNodeMixShader')
            connect(n,blend_shader,0,ramp.outputs[0]);connect(n,blend_shader,1,transparent.outputs[0])
            connect(n,blend_shader,2,n.nodes.get('Principled BSDF').outputs[0]);connect(n,n.nodes.get('Material Output'),'Surface',blend_shader.outputs[0])
        mesh_obj('Star sand',verts.reshape(-1,3),faces,mat,False)
    def night(self,fr):
        S=self.S;g=self.g
        u=bend(fr,[(4499,.001),(4520,.035),(4548,.124),(4583,.227),(4603,.306),(4624,.445),(4642,.545),(4662,.655),(4685,.79),(4707,.91),(4726,.973),(4751,.999)])
        if self.finish:u=float(np.interp(u,self.pen_clock,self.ride_clock))
        pov=fr>=4654
        eyes=smooth(4638,4654,fr)*(1-smooth(4728,4740,fr)) if self.finish else pov
        p,v=self.oriented(self.xyz,u,fr,1-smooth(4727,4749,fr),.62+.38*smooth(4652,4679,fr)-.77*smooth(4729,4750,fr),eyes,.051*math.sin(fr*.054))
        if self.finish and pov:
            # Orient the eye towards the destination before leaning into the fall.
            # Smooth the aim in world space across the folded letters' changing tangent.
            c=g.world(g.eyes+[0,.055,.050])
            ahead=sampled(self.xyz,min(1.,u+.080));forward=unit(ahead-c)
            well=unit(self.wellmark-c)
            sight=unit(mix(forward,well,.18+.82*smooth(4654,4680,fr)))
            side=unit(np.cross(sight,[0,0,1]));up=unit(np.cross(side,sight))
            sight=unit(sight+up*(.13-.09*smooth(4708,4748,fr))-.038*side)
            tilt=smooth(4669,4687,fr)
            hands=unit(g.rot@np.array([.01,2.1,-1.58]))
            look=unit(mix(hands,sight,tilt))
            lens=16.8+9.1*tilt
            up=mix(g.rot[:,2],[0,0,1],tilt)
            landing=smooth(4726,4750,fr)
            if landing>0:
                # Peel away over her shoulder to the next camera's actual film
                # gate. She plants her shoes and the following shot picks up the step.
                first,second=self.landing_camera
                gate=first+(second-first)*max(-5,fr-4751)
                c=mix(c,self.water_level+gate[:3],landing)+g.rot@np.array([-.63*np.sin(np.pi*landing),0,.17*np.sin(np.pi*landing)])
                framed=unit(gate[9:12]+.10*gate[3:6]-.11*gate[6:9])
                look=unit(mix(look,framed,landing))
                up=unit(mix(up,gate[6:9],landing));lens=mix(lens,36*gate[12],landing)
            S.view(c,c+5*look,lens,.017*math.sin(fr*.031)*(1-landing),up=up)
        elif pov:
            down=bend(fr,[(4654,.44),(4682,.85),(4708,1.24),(4724,.87),(4751,.41)])
            self.from_eyes(fr,down,16,.031*math.sin(fr*.058))
            if fr>=4726:
                c=g.world(g.eyes+[0,.035,.018]);t=c+g.rot@np.array([.01,2.1,-(.68*down+.83)])
                e=self.arrival;target=mix(t,mix(e+[0,1.32,.06],self.wellmark,.73),smooth(4726,4748,fr))
                S.view(c,target,16+9*smooth(4726,4750,fr),.016*np.sin(fr*.058),up=[0,0,1])
        else:
            cam=interpolate(fr,[(4499,-2.3,-4.3,1.55),(4522,-3.7,-6.6,1.10),(4545,-4.9,-8.4,1.92),(4583,-3.8,-5.90,1.35),(4606,-3.4,-4.7,1.49),(4633,-2.5,-3.9,1.44),(4654,-1.28,-2.6,1.44)])
            if self.finish:
                cam=interpolate(fr,[(4499,-2.3,-4.3,1.55),(4522,-2.8,-4.1,1.47),(4545,-3.3,-5.05,1.68),
                                    (4583,-2.8,-4.25,1.62),(4606,-2.6,-3.90,1.55),(4633,-2.12,-3.13,1.43),(4654,-.87,-2.1,1.33)])
            C=g.world(cam);T=g.world([0,1.6,.57])
            if fr<4544:
                # Clear the line from the camera to the planted heel during the launch.
                u=np.linspace(0,.96,55);foot=g.world([0,.47,.13]);ray=C+(foot-C)*u[:,None]
                level=S.floor(ray[:,0],ray[:,1])+.42*(1-u)+.03
                C[2]=max(C[2]+.74*(1-smooth(4519,4544,fr)),float(np.max((level-foot[2]*u)/(1-u))))
            S.view(C,T,25.4,.076*math.sin(fr*.048))
        if self.finish and 4638<=fr<4654:
            self.settle_eye(fr,4638,4654,np.array([0,.055,.050]),1.58,16.8)
        strength=.7+1.2*smooth(4661,4699,fr)
        if self.finish:strength*=1-smooth(4724,4746,fr)
        self.spray.frame(g,fr,strength)
    def frame(self,fr):
        {'slide':self.slide,'coaster':self.coaster,'night':self.night}[self.which](fr)
