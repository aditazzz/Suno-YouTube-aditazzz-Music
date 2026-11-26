"""A camp on the through-road, with woven tents, raked earth walls and date palms."""
from world import *
from ink import Board,path,caravan,move_camels
from rails import bezier,sampled
from mathutils import Matrix
from camp_surfaces import adobe,fabric,headcloth
def quad_object(name,verts,faces,materials,indices,smooth=False):
    m=mesh_obj(name,verts,faces,None,smooth)
    for mat in materials:m.data.materials.append(mat)
    m.data.polygons.foreach_set('material_index',np.asarray(indices,'i'));return m
def palm(S,x,y,height,seed,materials):
    rng=np.random.default_rng(seed);base=S.ground(x,y,-.1)
    yaw=rng.uniform(0,TAU);lean=np.array([np.cos(yaw),np.sin(yaw)])
    ts=np.linspace(0,1,36);pts=np.c_[ts[:,None]**1.48*lean[None,:]*height*.116,ts*height]
    vert=[];faces=[];ids=[]
    for j,t in enumerate(ts):
        r=height*(.023-.011*t)*(1+.065*np.sin(t*55)+.038*np.cos(t*91))
        for a in np.arange(12)*TAU/12:vert.append(pts[j]+[r*np.cos(a),r*np.sin(a),.04*np.sin(a*3+j)])
        if j:
            for k in range(12):
                b=(j-1)*12;faces.append([b+k,b+(k+1)%12,b+12+(k+1)%12,b+12+k]);ids.append(int(j%4==0))
    trunk=quad_object('Date palm • scarred trunk',vert,faces,materials[:2],ids);trunk.location=base
    vert=[];faces=[];ids=[]
    def segment(a,b,c,d,mat):
        i=len(vert);vert.extend([a,b,c,d]);faces.append((i,i+1,i+2,i+3));ids.append(mat)
    for j in range(13):
        a=j*2.4+rng.uniform(-.13,.13);direction=np.array([np.cos(a),np.sin(a),0]);side=np.array([-np.sin(a),np.cos(a),0])
        length=height*rng.uniform(.38,.51);droop=rng.uniform(.30,.73);lift=rng.uniform(.23,.43)
        if j>9:length*=.73;lift*=1.64;droop*=.60
        def rib(t):return length*(direction*t+np.array([0,0,t*lift+np.sin(np.pi*t)*.23-droop*t*t]))
        for k in range(22):
            t0=k/22;t1=(k+1)/22;w=.019*height/6
            segment(rib(t0)-side*w,rib(t0)+side*w,rib(t1)+side*w*(1-.77*t1),rib(t1)-side*w*(1-.77*t1),0)
        for k in range(1,26):
            t=k/27;at=rib(t);w=.016*length*(1-.44*t);lateral=length*(.11+.16*np.sin(np.pi*t)**.68)*(1-t**2.7)
            for sign in [-1,1]:
                tip=at+side*sign*lateral+direction*lateral*(.29+.60*t)+[0,0,-lateral*(.25+.71*t+rng.uniform(-.12,.14))]
                middle=mix(at,tip,.49)+[0,0,.068*length*(1-t*.8)]
                root=at-direction*w*.53
                ridge=middle+[0,0,w*1.33]
                segment(root,middle-direction*w,tip,ridge,1+(j+k)%3);segment(root,ridge,tip,middle+direction*w,1+(j+k+1)%3)
    frond=quad_object('Feathered green crown',vert,faces,materials[2:],ids,True);frond.location=base+pts[-1]
    return frond
def tent(S,x,y,size,heading,colors,seed):
    rng=np.random.default_rng(seed);base=S.ground(x,y,0)
    root=obj('Travellers’ woven shelter',None);root.location=base;root.rotation_euler.z=heading
    roof,binding,poles=colors
    V=[];F=[];idx=[]
    for side in [-1,1]:
        offset=len(V)
        for row in range(9):
            v=row/8
            for j in range(19):
                u=j/18
                V.append([side*(v*1.92*size),size*(-2.2+4.4*u),size*(2.47-.23*np.sin(np.pi*u)-1.69*v-.25*np.sin(np.pi*v)+.04*np.sin(u*TAU*4)*v**2)])
        for i in range(8):
            for j in range(18):
                k=offset+19*i+j;F.append((k,k+1,k+20,k+19));idx.append(int(j in [2,14,15]))
    o=quad_object('Slung woven roof',V,F,[roof,binding],idx);o.parent=root
    for y0 in [-2.16,2.16]:
        tube('Tent pole',np.array([[0,y0,0],[.016,y0,2.54]])*size,poles,.043*size,root)
        for sign in [-1,1]:
            tube('Taut guy',np.array([[sign*1.88,y0,.78],[sign*2.7,y0+np.sign(y0)*.40,.04]])*size,binding,.013*size,root)
    # Windward end is closed; two folded flaps leave an entrance on the lee end.
    for sign in [-1,1]:
        vv=np.array([[0,2.2,2.45],[sign*1.92,2.2,.78],[sign*1.94,2.2,0],[0,2.22,0]])*size
        vv2=np.array([[0,-2.2,2.45],[sign*1.92,-2.2,.78],[sign*1.88,-2.14,0],[sign*1.48,-2.04,.46]])*size
        ob=quad_object('Shelter panels',np.vstack([vv,vv2]),[(0,1,2,3),(4,5,6,7)],[roof],[0,0]);ob.parent=root
    return root
def lamp(S,x,y,h=.70):
    z=S.floor(x,y);base=S.ground(x,y,.02)
    metal=material('Patinated lamp bronze',(.12,.094,.063),.02,.47);milk=material('Pale tent light',(1.,.578,.239),4.2)
    sphere('Lamp foot',base+[0,0,.078],(.135,.135,.080),metal)
    tube('Lamp stem',np.array([base+[0,0,.07],base+[0,0,h]]),metal,.026)
    sphere('Clouded lamp bowl',base+[0,0,h],(.082,.082,.107),milk)
    for z0,r in [(h-.092,.082),(h+.099,.091)]:
        a=np.linspace(0,TAU,33);tube('Lamp gallery',base+np.c_[np.cos(a)*r,np.sin(a)*r,np.full(len(a),z0)],metal,.014)
    for angle in (0,TAU/3,2*TAU/3):
        vec=np.array([.086*np.cos(angle),.086*np.sin(angle),0])
        tube('Three lamp stays',[base+vec+[0,0,h-.09],base+vec+[0,0,h+.105]],metal,.0065)
    a=np.linspace(0,TAU,20,endpoint=False);rim=base+np.c_[.113*np.cos(a),.113*np.sin(a),np.full(len(a),h+.097)]
    verts=np.vstack([rim,base+[0,0,h+.170]])
    mesh_obj('Bronze rain cap',verts,[(j,(j+1)%len(a),len(a)) for j in range(len(a))],metal,False)
    light=point('Amber wick through the lamp glass',(1.,.64,.36),.27);light.location=base+[0,-.03,h+.22];light.data.energy=29
def sitter(S,x,y,scale,heading,colour):
    root=obj('A fellow traveller',None);root.location=S.ground(x,y,.016);root.scale=(scale,)*3;root.rotation_euler.z=heading
    dark=fabric('Faded travelling cloak',colour);hood=fabric('Cotton headcloth',tuple(np.array(colour)*1.55))
    ts=np.linspace(0,1,12);angles=np.linspace(0,TAU,28,endpoint=False);verts=[];faces=[]
    for i,t in enumerate(ts):
        width=np.interp(t,[0,.14,.32,.58,1],[.11,.18,.212,.185,.285])
        for a in angles:
            fold=.011*np.cos(8*a+.7*t)+.009*np.sin(5*a-1.4*t)
            verts.append([(width+fold)*np.cos(a),.031+.11*t+.81*(width+fold)*np.sin(a),.78-.665*t+.02*t*np.sin(3*a)])
        for k in range(len(angles)):
            if i:
                q=(i-1)*len(angles);l=(k+1)%len(angles);faces.append((q+k,q+l,q+len(angles)+l,q+len(angles)+k))
    coat=mesh_obj('Cloak over folded knees',verts,faces,dark);coat.parent=root
    face=material('Traveller in shadow',(.123,.064,.041))
    for side in [-1,1]:
        sphere('Folded leg',(side*.174,.20,.135),(.145,.222,.102),dark,root)
        sleeve=sphere('Elbow resting on knee',(side*.137,.114,.51),(.065,.097,.18),dark,root);sleeve.rotation_euler=(.56,0,side*.21)
        sphere('Resting hand',(side*.103,.211,.372),(.050,.051,.042),face,root)
    headcloth(root,heading,dark,hood,face)
    wool=material('Shade in the shawl folds',tuple(np.array(colour)*.67))
    for j in range(4):
        side=-1 if j<2 else 1;u=np.linspace(0,1,23)
        line=np.c_[side*(.099+.165*u+.019*np.sin(np.pi*u+j)),.098+.166*u+.027*np.sin(np.pi*u),.73-.54*u+.018*np.sin(6*u+j)]
        tube('Falling cloak fold',line,wool,.0062,root,radii=.32+.68*np.sin(np.pi*u))
    return root
class Camp:
    def __init__(self,S,war=False):
        self.S=S
        self.path=bezier([-43,-12],[[[-26,-12],[-22,-11],[-17,-6]],[[-13,-.3],[-8,0],[-5,-1]],[[-1,-3],[2,-.2],[4,3]],[[6,7],[10.5,7],[14,7.3]],[[19,8],[27,14],[50,16]]])
        self.gold=tube('Her road through the gate',S.surface(self.path,.028),S.gold,.057,radii=np.linspace(.87,1.1,len(self.path)))
        self.mats=[material(n,c) for n,c in [('Leathery palm bark',(.115,.091,.062)),('Raised leaf scars',(.186,.137,.082)),('Raked midrib',(.20,.236,.129)),('Leaflet • deep underside',(.056,.217,.087)),('Leaflet • silver-green',(.151,.376,.174)),('Leaflet • sap',(.104,.294,.129))]]
        rng=np.random.default_rng(4897);self.fronds=[]
        for j in range(34):
            centres=[(-14,5),(-7,13),(6,15),(11,-1),(-11,20),(2,21)]
            a=centres[j%len(centres)]+rng.normal(size=2)*[2.2,1.9];h=rng.uniform(5.3,10.6)
            self.fronds.append(palm(S,*a,h,j+211,self.mats))
        self.wall(S)
        roof=fabric('Undyed blue-grey sailcloth',(.143,.144,.161));ivory=fabric('Faded strip of cotton',(.31,.31,.29));wood=material('Date wood stakes',(.12,.084,.059))
        rust=fabric('Worn camel hair tent',(.183,.146,.113))
        for j,(x,y,sc,ang) in enumerate([(-8,4,1.34,-.6),(-1,8,1.00,.72),(7,10,.94,-.77),(4,-3,.91,-1.18),(-13,13,.87,1.47),(0,17,1.07,2.0),(8,18,.70,.81)]):
            tent(S,x,y,sc,ang,[roof if j%2==0 else rust,ivory,wood],j)
        for x,y in [(-7.3,-.65),(-2.5,5.4),(4.7,5.65),(3.1,-5.7),(-15,10),(6.1,16.35)]:lamp(S,x,y)
        self.travellers=[]
        self.robed=None
        self.lamp_seats=[]
        for j,(x,y,h) in enumerate([(-7.7,.18,2.7),(-6.60,-.23,1.1),(-2.7,6.0,-1.3),(4.6,6.1,.8),(3.5,-6.4,-.34),(6.9,16.8,2.2)]):
            self.lamp_seats.append((x,y))
            self.travellers.append(sitter(S,x,y,.93+.08*(j%3),h+([-.34,1.04,.1][j%3]),[(.148,.073,.049),(.21,.160,.114),(.123,.092,.063)][j%3]))
        # She settles her weight on the folded blanket from her travelling bundle.
        blanket=fabric('Folded camel-hair travelling blanket',(.179,.133,.095))
        band=fabric('Worn blanket selvedge',(.255,.211,.155))
        xx,yy=-7.23,-1.74;u=np.linspace(-1,1,23);v=np.linspace(-1,1,18)
        verts=[];faces=[];ids=[]
        for j,b in enumerate(v):
            for i,a in enumerate(u):
                x=xx+.44*a+.10*b;y=yy+.39*b+.05*a
                height=.046+.125*(1-a**4)*(1-b**4)+.026*np.cos(13*a+1.2*b)*(1-b*b)
                verts.append(S.ground(x,y,height))
                if i and j:
                    q=j*len(u)+i;faces.append((q-len(u)-1,q-len(u),q,q-1));ids.append(int(i in (3,4,19)))
        pad=quad_object('Blanket supporting her seated hips',verts,faces,[blanket,band],ids,True)
        back=pad.modifiers.new('Bound layers of wool','SOLIDIFY');back.thickness=.045
        if (D/'footways.png').exists():
            n,b,ch=terrain_image(S,D/'footways.png',-1,5,132,100)
            old=b.inputs['Base Color'].links[0].from_socket;connect(n,b,'Base Color',blend(n,mul(n,.92,ch[0]),old,(.445,.425,.353,1)))
            old=b.inputs['Normal'].links[0].from_socket
            bn=node(n,'ShaderNodeBump');bn.invert=True;bn.inputs['Distance'].default_value=.073;bn.inputs['Strength'].default_value=.62
            connect(n,bn,'Normal',old);connect(n,bn,'Height',ch[0]);connect(n,b,'Normal',bn.outputs[0])
        if war:self.battle()
    def wall(self,S):
        mud=adobe('Rammed ochre clay',(.49,.255,.108),(.18,.078,.041))
        cap=adobe('Sun-dried clay coping',(.55,.307,.152),(.205,.100,.052))
        self.wallpoints=[];verts=[];faces=[];ids=[]
        # Two uninterrupted battered runs leave the actual road openings clear.
        runs=[[(-18,-4),(-23,4),(-19,17),(-11,24),(7,26),(14,19),(14.7,9.1)],
              [(14.7,5.0),(13,-4),(4,-9),(-10,-10),(-16,-8.2)]]
        for corners in runs:
            chain=[]
            for a,b in zip(corners,corners[1:]):
                n=max(3,round(np.linalg.norm(np.subtract(b,a))/.7))
                chain.extend(np.linspace(a,b,n,endpoint=False))
            xy=np.vstack([chain,corners[-1]]);axis=unit(np.gradient(xy,axis=0))
            side=np.c_[-axis[:,1],axis[:,0]]
            arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
            # The crown is hand-packed, slightly scoured at the open ends.
            crown=2.98+.115*np.sin(.63*arc)+.057*np.sin(1.82*arc+.7)
            near=np.minimum(np.linalg.norm(xy-[14.7,9.1],axis=1),np.linalg.norm(xy-[14.7,5.0],axis=1))
            crown-=.52*(1-smooth(0,3.6,near))
            buttress=(.5+.5*np.cos(arc*1.03+.6))**13
            widths=[.65+.33*buttress,.55+.24*buttress,.405+.09*buttress,.36+.024*buttress,.33+.02*buttress]
            heights=[np.full(len(xy),-.33),crown*.28,crown*.77,crown-.13,crown]
            first=len(verts)
            for i,(pt,normal) in enumerate(zip(xy,side)):
                for z,w in zip(heights,widths):
                    for sign in [-1,1]:
                        corner=pt+normal*sign*w[i]
                        verts.append(S.ground(*corner,z[i]))
            for i in range(len(xy)-1):
                q=first+10*i
                for j in range(4):
                    lo=q+2*j;hi=lo+2
                    faces.extend([(lo,hi,hi+10,lo+10),(lo+1,lo+11,hi+11,hi+1)]);ids.extend([int(j==3)]*2)
                faces.append((q+8,q+9,q+19,q+18));ids.append(1)
            for i in (0,len(xy)-1):
                q=first+10*i
                for j in range(4):
                    lo=q+2*j;faces.append((lo,lo+1,lo+3,lo+2));ids.append(int(j==3))
            # Follow the earthen crown with the faint trace by which her road drew it.
            edge=tube('Ink caught on the adobe crown',np.asarray([S.ground(*pt,z+.012) for pt,z in zip(xy,crown)]),cap,.036)
            self.wallpoints.append(edge)
        ob=quad_object('Continuous rammed-earth enclosure',verts,faces,[mud,cap],ids)
        bevel=ob.modifiers.new('Eroded edges in the adobe','BEVEL');bevel.width=.075;bevel.segments=2
        for y in [5.05,9.10]:
            x=14.66;base=S.ground(x,y,.0)
            rings=[(-.11,.58,.68),(.35,.56,.665),(1.24,.50,.623),(2.21,.415,.522),(2.49,.426,.534),(2.64,.401,.514)]
            corners=[(-1,-.81),(-.80,-1),(.80,-1),(1,-.80),(1,.80),(.81,1),(-.81,1),(-1,.81)]
            vv=[base+[xx*w+.018*np.sin(2*j+i),yy*d+.022*np.cos(i+j*.7),z+.016*np.sin(i*2+j)] for j,(z,w,d) in enumerate(rings) for i,(xx,yy) in enumerate(corners)]
            ff=[(8*j+i,8*j+(i+1)%8,8*(j+1)+(i+1)%8,8*(j+1)+i) for j in range(len(rings)-1) for i in range(8)];ff.extend([(40,41,42,43),(40,43,44,45),(40,45,46,47)])
            o=mesh_obj('Tapered earthen gate pier',vv,ff,mud,False)
            be=o.modifiers.new('Rounded mud coping','BEVEL');be.width=.055;be.segments=2
        a=S.ground(14.66,5.05,2.56);b=S.ground(14.66,9.10,2.56)
        beam=adobe('Date timber',(.164,.148,.098),(.060,.047,.036));rope=material('Palm-fibre lashing',(.245,.225,.146))
        v=b-a;v=v/np.linalg.norm(v);
        for j in [-1,1]:
            start=a-v*.44+[j*.21,0,-.015*j];end=b+v*.47+[j*.21,0,.02*j];u=np.linspace(0,1,40)
            spine=start+(end-start)*u[:,None]+np.c_[.036*np.sin(np.pi*u)*j,np.zeros_like(u),-.067*np.sin(np.pi*u)]
            tube('Weathered date-wood lintel',spine,beam,.111,radii=.89+.08*np.sin(7*u)+.033*np.sin(19*u))
        for end in [a,b]:
            for k in range(3):
                a0=np.linspace(0,TAU,45);tube('Palm-fibre binding over lintel',end+[0,(k-1)*.061,0]+np.c_[.355*np.cos(a0),np.zeros_like(a0),.150*np.sin(a0)],rope,.0135)
    def animate(self,fr):
        for j,c in enumerate(self.fronds):c.rotation_euler=(.026*np.sin(fr*.032+j),.043*np.sin(fr*.041+j*2.11),.033*np.sin(fr*.021+j*.68))
        use_robes = os.environ.get('FINISH_STORY')=='1' and fr>=3728
        if use_robes and self.robed is None:
            from camp_travellers import traveller
            self.robed=[]
            lamps=[(-7.3,-.65),(-7.3,-.65),(-2.5,5.4),(4.7,5.65),(3.1,-5.7),(6.1,16.35)]
            for j,((x,y),(lx,ly)) in enumerate(zip(self.lamp_seats,lamps)):
                if j==0:
                    # Move the blue hood clear of the windward tent flap.
                    x-=.16
                    y-=.22
                turn=-math.atan2(lx-x,ly-y)+(.19 if j%2 else -.17)
                self.robed.append(traveller(self.S,x,y,.96+.047*(j%3),turn,j))
        if self.robed is not None:
            for group,hidden in [(self.travellers,use_robes),(self.robed,not use_robes)]:
                for o in group:
                    for child in o.children_recursive:child.hide_render=hidden
        for j,o in enumerate(self.travellers):o.rotation_euler.y=.027*np.sin(fr*.033+.7*j)
        for j,e in enumerate(self.wallpoints):
            if 3656<=fr<3800:
                q=smooth(3730+j*1.4,3753+j*1.5,fr);e.hide_render=bool(q<.001);e.data.bevel_factor_end=max(.001,q)
    def battle(self):
        S=self.S
        self.B=B=Board(S,-91,-8,.33)
        self.halted=caravan(B,14,38,.83,4,3615,S.white,gap=44,halted=True)
        self.line=B.stroke('Her caravan in the lee','M -40 81 C -16 70 6 78 23 73 Q 45 67 66 72',3600,14,.111,S.gold)
        self.riders=[]
        horse=['M 1 24 Q 6 16 12 16 Q 17 17 21 18 Q 23 10 27 9 L 27 6 L 29 9 L 34 13 Q 34 16 29 15 L 26 15 Q 26 23 22 25 L 21 34 L 24 38 M 21 24 Q 15 26 10 24 L 7 33 L 3 36',
               'M 10 24 L 11 31 L 14 36 M 24 23 L 28 30 L 32 31','M 4 19 Q 2 19 0 24','M 14 17 L 16 10 Q 15 8 15 6 Q 17 3 19 5 Q 21 8 18 9 L 19 13 L 22 13 M 13 17 L 18 20 L 21 23','M 19 15 L 30 -4']
        for j in range(8):
            x=-85+j*5.2;y=15+2.4*np.sin(.83*j)
            root=obj('Cold outline along the crest',None);root.location=S.ground(x,y,2.8+.59*np.sin(j))
            for s in horse:
                pp=path(s);v=np.c_[(pp[:,0]-17)*.122,np.zeros(len(pp)),(38-pp[:,1])*.128]
                tube('Rider beyond the ridge',v,S.white,.058,root)
            self.riders.append(root)
        if os.environ.get('FINISH_STORY')=='1':
            from finish_story import ridge
            ridge(self)
        self.flashes=[]
        for j,(x,y) in enumerate([(-82,20),(-64,23),(-47,18)]):
            l=point('Cold distant flash',(.54,.73,1),4.8);l.location=S.ground(x,y,3.2);self.flashes.append(l)
    def war_frame(self,fr):
        for j,l in enumerate(self.flashes):
            flash=0
            for start,lane in [(3658,0),(3670,2),(3687,1),(3707,2),(3736,0),(3817,1),(3843,0)]:
                if lane==j:flash+=smooth(start,start+5,fr)*(1-smooth(start+5,start+15,fr))
            l.data.energy=flash*(8800+1200*j)
        for j,o in enumerate(self.riders):o.location.x=-85+j*(8.8 if os.environ.get('FINISH_STORY')=='1' else 5.2)+.65*np.sin((fr-3656)*.023+j)
        q=smooth(3689,3712,fr);dx=4.0*smooth(3656,3712,fr)
        move_camels(self.halted,fr,dx,fold=(.93 if os.environ.get('FINISH_STORY')=='1' else .29)*q,step=min(fr-3656,55)*.11,size=.83)
        self.line.frame(fr)
