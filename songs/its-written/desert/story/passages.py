"""The driver's camp, the tally, three losses and the settlement behind the wall."""
from world import *
from performer import Girl
from ink import Board,Stroke,series,path,oval,RESTING,DRIVER,FINGER,caravan,move_camels,Scatter
from rails import pen,sampled,well,bezier
def key(f,*pairs):return interpolate(f,pairs)[0]
def ground_view(S,B,cx,cy,width,elevation,az=0,lens=31,roll=0):
    target=B.at(cx,cy,.18)
    distance=width*B.scale*lens/36
    el=np.radians(elevation)
    eye=target+distance*np.array([np.sin(az)*np.cos(el),-np.cos(az)*np.cos(el),np.sin(el)])
    S.view(eye,target,lens,roll)
def line(B,name,p,r=.095,mat=None):return B.stroke(name,p,-100,-1,r,mat)
def hide(obj,hidden):
    obj.hide_render=hidden
    for child in obj.children_recursive:child.hide_render=hidden
class Passage:
    def __init__(self,S,name):
        self.S=S;self.name=name;self.finish=os.environ.get('FINISH_STORY')=='1';self.g=Girl(S);self.lines=[]
        getattr(self,'build_'+name)()
    def frame(self,fr):getattr(self,self.name)(fr)
    def build_driver(self):
        S=self.S;self.B=B=Board(S,-21,11,.42)
        self.road=line(B,'The road reaches the sleeper','M -110 102 C -50 79 -26 91 4 83 C 21 76 25 79 39 73 C 48 67 53 69 60 72 C 82 78 107 72 126 64 C 144 57 160 55 174 55',.10)
        self.shoe_fill=point('Silver return on the passing canvas',(.77,.85,1.),.72);self.shoe_fill.data.energy=0
        self.spur=B.stroke('A hairline branches out of her step','M 38 74 C 36 70 20 74 16 67 C 12 60 24 54 17 49 Q 9 43 2 41',916,13,.10,erase=(1122,1168))
        self.camel=series(B,'Dromedary at rest',RESTING,923,953,.13,erase=(1126,1172))
        self.driver_body=series(B,'Man sitting against the camel',DRIVER,946,969,.115,erase=(1139,1178))
        self.finger=series(B,'The raised finger',FINGER,965,980,.122,erase=(1140,1179))
        words=[np.c_[104+(p[:,0]+58)*.086,32-p[:,1]*.090-.008*(p[:,0]+58)] for p in pen()]
        self.words=series(B,'Words from the fingertip',words,1042,1066,.089,erase=(1149,1184))
        self.fingertip=B.stroke('The fingertip gives the pen away','M 101 35 C 102 33 103 33 104 32',1040,5,.083,erase=(1133,1160))
        self.scatter=Scatter(S,[self.spur,*self.camel,*self.driver_body,*self.finger,*self.words])
        if self.finish:
            self.closed_eye=B.stroke('Eyelid lowered in sleep','M 88.5 38 Q 89.9 39.5 91.1 38.1',1116,6,.116,erase=(1142,1178))
        self.trackpoints=[]
        self.pressed_rim=material('Moon on the worn edge of a step',(.295,.238,.163),.07,.96)
        for j in range(34):
            t=j/32
            x=-1+j*1.24;y=83-.26*x+.89*np.sin(x*.19)+(-1)**j*.32
            ellipse=oval(x,y,.45,.17,.08)
            self.trackpoints.append(B.stroke('Worn step in her road',ellipse,680+12*j,8,.027,S.hot,erase=(1076+j,1100+j)))
        self.caster=obj('Low flight across the road',None);self.caster.scale=(13.1,7.21,1)
        self.shadow_power=[]
        shade=[S.land.data.materials[0],self.g.coat,self.g.edge,self.g.pants,self.g.skin]
        for thing in self.g.head.children_recursive:
            if thing.type in ('MESH','CURVE'):shade.extend(list(thing.data.materials))
        for mat in set(shade):
            if mat is None or not mat.use_nodes:continue
            n=mat.node_tree;b=n.nodes.get('Principled BSDF')
            if b is None:continue
            co=node(n,'ShaderNodeTexCoord');co.object=self.caster
            x,y,z=split(n,co.outputs['Object'])
            uv=join(n,add(n,.5,x,mul(n,z,-.026)),add(n,.5,y,mul(n,z,.053)))
            shade_tex=node(n,'ShaderNodeTexImage');shade_tex.image=bpy.data.images.load(str(D/'wing-shadow.png'),check_existing=True)
            shade_tex.image.colorspace_settings.name='Non-Color';shade_tex.extension='CLIP';connect(n,shade_tex,'Vector',uv)
            power=node(n,'ShaderNodeValue');power.outputs[0].default_value=0;self.shadow_power.append(power.outputs[0])
            ink=mul(n,shade_tex.outputs[0],power.outputs[0])
            original=b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else tuple(b.inputs['Base Color'].default_value)
            connect(n,b,'Base Color',blend(n,ink,original,(.014,.018,.025,1)))
    def driver(self,fr):
        B=self.B;S=self.S;g=self.g
        x=key(fr,(665,1),(727,6),(803,11),(910,20),(981,25),(1093,32.2),(1183,40))
        y=83-.26*x+.89*np.sin(x*.19)
        p=B.at(x,y,.02)
        g.pose(fr,p,heading=-1.41+.13*np.sin(fr*.024),opening=.2,wind=.39,gaze=.64*smooth(878,940,fr)-.29*smooth(1090,1148,fr))
        self.road.frame(fr);self.road.obj.data.bevel_factor_end=np.clip(.62+.004*(x-11),.45,.92)
        for s in [self.spur,*self.camel,*self.driver_body,self.fingertip,*self.words,*self.trackpoints]:s.frame(fr)
        def droop(uv,f):
            q=smooth(1097,1142,f);u=uv.copy();w=smooth(90,101,u[:,0])
            u[:,1]+=q*(7.6*w+3.6*w*smooth(49,35,u[:,1]));u[:,0]+=q*.68*w;return u
        if self.finish:
            from finish_story import sleepy
            sleepy(self,fr)
            def droop(uv,f):
                q=smooth(1095,1140,f);p=uv.copy();hand=smooth(88,101,p[:,0])
                p[:,1]+=q*hand*(10.2+13.1*smooth(53,35,p[:,1]))
                p[:,0]-=q*hand*6.3
                return p
        for s in self.finger:s.frame(fr,warp=droop)
        self.scatter.frame(fr,1113,1182)
        u=(fr-878)/31
        self.caster.location=p+np.array([u*13.7,u*4.3,0]);self.caster.rotation_euler[2]=-.44+.072*u
        dim=.61*smooth(840,852,fr)*(1-smooth(900,913,fr))
        for power in self.shadow_power:power.default_value=dim
        close=787<=fr<=813
        self.shoe_fill.data.energy=39 if close else 0
        for old_step in self.trackpoints:
            old_step.obj.data.bevel_depth=.0055 if close else old_step.r
            old_step.obj.location.z=-.011 if close else 0
            old_step.obj.data.materials[0]=self.pressed_rim if close else S.hot
        self.shoe_fill.location=g.world([-.76,.71,.73])
        self.road.obj.data.bevel_depth=.018 if close else self.road.r
        self.road.obj.location.z=-.044 if close else 0
        S.gold.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.82 if close else 3.3
        if close:
            # A low lens sees the cotton step plant at the edge of the same incised stroke.
            S.view(g.world([-.99,.89-.011*(fr-787),.33]),g.world([0,.035,.164]),37,-.024)
        elif fr<910:
            az=key(fr,(681,-.44),(707,-.53),(745,-.08),(778,.56),(811,1.00),(845,.74),(878,.24),(910,-.21))
            width=key(fr,(680,40),(705,44),(748,58),(786,42),(818,51),(857,77),(884,65),(910,87))
            look=smooth(880,910,fr)
            cx=mix(x+3.4+4.3*np.sin((fr-700)*.030),25,look)
            cy=mix(y-2.4+5*np.sin((fr-701)*.028),68,look)
            roll=.048*np.sin(fr*.017)
            ground_view(S,B,cx,cy,width,61+5.5*np.cos((fr-713)*.025),az,33-2*look,roll)
            if fr<=(719 if self.finish else 704):
                q=smooth(680,719 if self.finish else 704,fr)
                if self.finish:q=np.expm1(q*np.log(29.))/28
                eye=mix(g.world([-.66,-.76,.26]),np.array(S.cam.location),q)
                target=mix(g.world([0,.14,.24]),B.at(cx,cy,.18),q)
                S.view(eye,target,32+q,q*roll)
        else:
            cx=key(fr,(910,25),(926,45),(951,57),(989,59),(1023,76),(1042,96),(1069,107),(1100,97),(1141,84),(1182,73))
            cy=key(fr,(910,68),(940,54),(973,49),(1024,48),(1053,38),(1092,41),(1140,49),(1182,56))
            width=key(fr,(910,87),(943,128),(973,134),(1023,103),(1050,87),(1081,86),(1131,111),(1182,135))
            az=key(fr,(910,-.21),(941,.015),(978,.23),(1009,.30),(1042,.04),(1078,-.13),(1105,-.19),(1140,-.02),(1182,.28))
            ground_view(S,B,cx,cy,width,61.6+10.3*smooth(941,1045,fr),az,31,-.037*np.sin(fr*.018))
    def build_tally(self):
        S=self.S;self.B=B=Board(S,-19,6,.46)
        self.road=line(B,'Track in the lee','M -64 60 C -31 44 -19 49 3 51 C 37 57 45 50 72 50 S 100 58 134 47'.replace('S 100 58 134 47','C 91 50 100 58 134 47'),.109)
        self.ticks=[]
        for b in range(8):
            for k in range(5):
                x=b*11.4+5;y=39+2.1*np.sin(b*.8);start=1204+(b*5+k)*2.17
                if k<4:p=bezier([x+1.79*k,y],[[[x+.4+1.79*k,y-3],[x+1.05+1.79*k,y-5.2],[x+1.7+1.79*k,y-9.4]]])
                else:p=bezier([x-.9,y-2.5],[[[x+1.8,y-4],[x+4.9,y-6.6],[x+8.9,y-8.2]]])
                self.ticks.append(B.stroke('Day '+str(b*5+k+1),p,start,2,.098,erase=(1307+1.72*b,1331+2.1*b)))
        self.scatter=Scatter(S,self.ticks)
        self.prints=[B.stroke('Impression '+str(j),oval(-20+j*2.55,52+1.4*np.sin(j*.4)+.68*(-1)**j,.59,.24),1180+j*.6,7,.039,S.cool,erase=(1309+j*.37,1331+j*.5)) for j in range(44)]
    def tally(self,fr):
        S=self.S;B=self.B;g=self.g
        x=(fr-1183)*.42;pp=B.at(x,50+2*np.sin(x*.08),.03)
        g.pose(fr,pp,-1.31,wind=.59,scale=1.12)
        for s in [self.road,*self.ticks,*self.prints]:s.frame(fr)
        self.scatter.frame(fr,1306,1351)
        y=key(fr,(1183,51),(1203,44),(1248,37),(1292,40),(1323,47),(1366,52))
        cx=key(fr,(1183,3),(1205,12),(1252,36),(1293,52),(1329,61),(1366,73))
        width=key(fr,(1183,64),(1213,83),(1254,105),(1292,122),(1316,127),(1354,75),(1366,45))
        angle=key(fr,(1183,19),(1204,7),(1241,6),(1279,6),(1290,7),(1298,39),(1308,63),(1344,45),(1366,62))
        azimuth=-.13+.056*np.sin(fr*.019)
        target=B.at(cx,y,.32);distance=width*B.scale*27/36;el=np.radians(angle)
        eye=target+distance*np.array([np.sin(azimuth)*np.cos(el),-np.cos(azimuth)*np.cos(el),np.sin(el)])
        eye[2]=max(eye[2],S.floor(*eye[:2])+3.3)
        target[2]+=2.15*smooth(1187,1205,fr)*(1-smooth(1288,1308,fr))
        S.view(eye,target,27)
        # A true disc in the sky, projected on the low skyline as the ground scrolls in the foreground.
        # The arc stays above the ridge even when the camera changes altitude near the last tally.
        # Forty continuous east-to-west sweeps across the exposure, depositing one pen stroke apiece.
        u=((fr-1203.5)/2.17)%1
        az=-.52+u*1.10;el=.122+.073*np.sin(np.pi*u)
        v=[np.sin(az)*np.cos(el),np.cos(az)*np.cos(el),np.sin(el)]
        for i,val in enumerate(v):S.moon.inputs[i].default_value=val
    def build_montage(self):
        S=self.S;self.B1=A=Board(S,-122,33,.34);self.B2=B=Board(S,-48,29,.36);self.B3=C=Board(S,16,31,.35)
        self.letter=[]
        self.oldink=material('Road already travelled',(.16,.151,.134),.03)
        n=self.oldink.node_tree;b=n.nodes.get('Principled BSDF');self.recall=node(n,'ShaderNodeMixShader')
        connect(n,self.recall,1,node(n,'ShaderNodeBsdfTransparent').outputs[0]);connect(n,self.recall,2,b.outputs[0])
        connect(n,n.nodes.get('Material Output'),'Surface',self.recall.outputs[0])
        self.arriving=A.stroke('Her road reaches the overturned purse','M -73 85 C -31 76 -6 85 14 73 Q 22 66 28 58',1997,36,.088)
        hat=next(ob for ob in self.g.head.children if ob.name.startswith('Madder cap'))
        hat.data.materials[0].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.44
        for s in pen():
            xy=(s-[220,0])*[.58,.56]
            self.letter.append(tube('Her earlier footways',S.surface(xy,.073),self.oldink,.066))
        self.purse=series(A,'Overturned clasp purse',[
            'M 1 68 C 12 62 16 50 21 47 C 28 43 34 43 39 40',
            'M 21 47 C 18 42 16 40 15 33 C 13 26 24 19 34 18 Q 39 17 41 19 C 44 22 45 33 47 38 Q 46 40 42 42',
            'M 20 47 Q 29 41 45 37 L 48 40 Q 34 43 22 50 L 20 47',
            'M 30 43 Q 28 39 31 38 Q 34 38 34 42','M 34 41 Q 36 37 38 38 Q 40 40 37 42',
            'M 21 29 Q 24 25 28 25','M 22 33 Q 24 30 25 30'],2016,2036,.113)
        self.coins=[]
        for j in range(3):
            self.coins.append(A.stroke('A coin rolls into the crystal',oval(0,0,3.8+j*.25,3.3+j*.2),2026+4*j,5,.106))
        self.glasses=[];self.glasspos=[]
        for j,(x,y,rx) in enumerate([(63,37,5.6),(81,30,6.4),(97,34,4.8)]):
            self.glasspos.append((x,y,rx))
            s=[f'M {x-rx} {y} Q {x-rx+.4} {y+11} {x-.7} {y+13} L {x-.7} 56 Q {x-2} 58 {x-4.5} 58.5 Q {x} 60 {x+5} 58.5 Q {x+1} 58 {x+.4} 56 L {x+.4} {y+13} Q {x+rx} {y+11} {x+rx} {y}',f'M {x-rx+2} {y+3} Q {x-rx+2} {y+6} {x-rx+3} {y+7}']
            self.glasses+=series(A,'Crystal glass',s,2047+j*4,2061+j*3,.110)
        self.shelf=series(A,'Shelf and its brackets',['M 48 61 Q 72 61.8 107 60.6 L 108 63 Q 84 64 49 64','M 54 64 L 54 69 L 61 64','M 98 64 L 100 68 L 104 63'],2055,2070,.115)
        self.lunar=[];cx,cy=47,43
        for j in range(12):
            a=-np.pi/2+j*TAU/12;xx=cx+31*np.cos(a);yy=cy+27*np.sin(a)
            t=np.linspace(-np.pi/2,np.pi/2,40)
            phase=(j+.50)*TAU/12;light=max(.14,.5-.5*np.cos(phase));side=1 if j<6 else -1
            # Trace the visible face of each lunation. Its shadow side opens, so the narrow moons are true crescents.
            limb=np.c_[xx+side*4.10*np.cos(t),yy+4.37*np.sin(t)]
            terminator=np.c_[xx+side*(1-2*light)*4.10*np.cos(t),yy+4.37*np.sin(t)]
            contour=np.vstack((limb,terminator[-2::-1]))
            self.lunar.append(B.stroke('Lunation '+str(j+1),contour,2084+j*2.05,7,.109))
            if light>.81:
                small=oval(xx+side*1.66,yy+1.06,.52,.38,-.32,16)[3:12]
                self.lunar.append(B.stroke('Crater in the full face',small,2091+j*2.05,3,.044))
        self.ring=[]
        for j in range(12):
            t=np.linspace(-np.pi/2+j*TAU/12+.137,-np.pi/2+(j+1)*TAU/12-.137,22)
            self.ring.append(B.stroke('Closing the year',np.c_[cx+31*np.cos(t),cy+27*np.sin(t)],2093+j*2.2,8,.0255))
        self.missed=caravan(C,17,7,.49,3,2143,S.white,gap=45)
        self.next=caravan(C,-33,38,.63,3,2163,S.white,gap=45)
        self.newroad=C.stroke('The second caravan picks her up','M -27 68 C -4 62 11 69 29 61 C 45 54 60 60 75 54 C 91 49 110 50 122 39',2164,40,.121)
        self.trip=A.stroke('From the mouth of the purse','M 32 47 Q 38 56 46 54 Q 53 54 60 46',2023,21,.072)
        self.yearroad=B.stroke('The way in to the year','M -45 69 C -9 60 5 59 19 49 Q 31 41 47 43',2077,24,.10)
        if self.finish:
            from finish_story import shop
            shop(self)
    def montage(self,fr):
        S=self.S;g=self.g;A=self.B1;B=self.B2;C=self.B3
        for s in [self.arriving,*self.purse,*self.glasses,*self.shelf,*self.lunar,*self.ring,self.trip,self.yearroad,self.newroad]:s.frame(fr)
        if self.finish:
            from finish_story import purse_fold
            for stroke in self.purse:stroke.frame(fr,warp=purse_fold)
        for j,coin in enumerate(self.coins):
            q=smooth(2025+j*4,2054+j*4,fr);x,y,r=self.glasspos[j];stand=smooth(2044+j*3,2056+j*4,fr)
            pos=mix([30+j*1.6,43],[x,y],q);pos[1]+=14*np.sin(np.pi*q)**.85
            def tilt(uv,f,j=j):
                u=uv.copy();angle=4.3*np.pi*q*(1-stand)
                u=u@np.array([[np.cos(angle),np.sin(angle)],[-np.sin(angle),np.cos(angle)]])
                u[:,0]*=1+.44*stand;u[:,1]*=1-.66*stand;return u
            coin.frame(fr,pos,tilt)
        off1=max(0,fr-2142)*(.61 if self.finish else .28);off2=min(39,max(0,fr-2160)*.49)
        move_camels(self.missed,fr,off1,min(0,-.097*(fr-2142)),step=(fr-2142)*.115,size=.49)
        move_camels(self.next,fr,off2,-.059*max(0,fr-2164),step=(fr-2164)*.126,size=.63)
        if fr<2084:
            q=(fr-2012)/71;g.pose(fr,A.at(23+17*q+(15*smooth(2042,2076,fr) if self.finish else 0),63-8*q,.03),-1.09,wind=.35,gaze=-.55,scale=1.28)
            # Travel from the overturned purse to the shelf as the same coins catch their light.
            ground_view(S,A,9+62*q,49-5*q,112+20*q,49+24*q,-.44+.89*q,32,-.058+.093*q)
        elif fr<2144:
            u=smooth(2084,2113,fr)
            q=(fr-2084)/60
            g.pose(fr,B.at(25+22*u,48-5*u,.04),-.97,seat=smooth(2107,2123,fr),wind=.28,gaze=.21,opening=.31,scale=1.48,step=min(fr-2084,30)+(fr-2084)*.08)
            ground_view(S,B,24+37*q,49-10*q,116+13*q,49+29*q,-.69+1.18*q,32,-.046+.09*q)
        else:
            q=smooth(2175,2215,fr)
            g.pose(fr,C.at(23+19*q,61-7*q,.02),-1.46,wind=.52,scale=1.41)
            if fr<=2214:
                a=(fr-2143)/71
                ground_view(S,C,18+47*a,34+19*a,132+17*a,53+20*a,-.54+.93*a,32,.033-.07*a)
            else:
                q=smooth(2214,2254,fr);target=mix(C.at(52,43),[-18.0,19,0],q)
                distance=40+253*q
                S.view(target+[1.1,-distance*(.61-.20*q),distance*(.79+.11*q)],target,33,-.024*(1-q))
        bs=self.oldink.node_tree.nodes.get('Principled BSDF');q=smooth(2203,2238,fr)
        if self.finish:
            # A single trailing stroke resolves before the rest of the road comes into view.
            for j,penstroke in enumerate(self.letter):
                penstroke.data.bevel_factor_end=.001+.999*smooth(2210+min(j,4)*3,2245+min(j,4),fr)
        self.recall.inputs[0].default_value=q
        bs.inputs['Emission Color'].default_value=(*mix([.07,.04,.025],[1,.53,.12],q),1)
        bs.inputs['Emission Strength'].default_value=.16+3.5*q
    def build_oasis(self):
        from camp import Camp
        self.camp=Camp(self.S,True)
        self.grove_colors=[(.046,.178,.083),(.122,.307,.162),(.082,.250,.118)]
    def oasis(self,fr):
        S=self.S;g=self.g;camp=self.camp;camp.animate(fr);camp.war_frame(fr)
        for mat,colour in zip(camp.mats[3:],self.grove_colors):
            c=mix([.078,.087,.095],colour,smooth(3728,3751,fr))
            mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*c,1)
        if fr<=3727:
            B=camp.B;x=36+5.3*smooth(3656,3714,fr);halt=smooth(3688,3713,fr)
            p=B.at(x,82,.014)
            g.pose(fr,p,heading=-1.36,opening=.26,wind=.51-.43*halt,slack=halt,gaze=.94*halt,scale=1.17,
                   step=mix(fr-3656,53+.13*(fr-3713),halt))
            approach=fr-3656
            c0=B.at(46+.96*approach,161-.53*approach,13.8-.072*approach)
            t0=B.at(64+.40*approach,26+.23*approach,2.37)
            q=smooth(3682,3709,fr)
            t1=B.at(74+.65*(fr-3702),64,.13);angle=np.radians(61+.19*(fr-3702))
            c1=t1+(54-.31*(fr-3702))*np.array([-.15*np.cos(angle),-.99*np.cos(angle),np.sin(angle)])
            S.view(mix(c0,c1,q),mix(t0,t1,q),28+4*q,-.023*np.cos(fr*.032))
        elif fr<=3802:
            a=(fr-3728)/74;q=.55*a+.45*smooth(3728,3802,fr);pp=sampled(camp.path,.335+.098*q)
            p=S.ground(*pp,.02);g.pose(fr,p,-1.37,wind=.22,gaze=.38,scale=1.08)
            target=mix(S.ground(-2.9,8.2,4.1),S.ground(-6.9,1.1,2.02),q)
            c=mix(S.ground(-34.6,-26.5,12.3),S.ground(-13.7,-11.9,3.9),q)
            c+=np.array([-3.9,4.2,.65])*np.sin(np.pi*q)
            S.view(c,target,28.6+1.2*q,-.026+.035*q)
        elif fr<=3856:
            q=(fr-3803)/53;p=S.ground(-7.23,-1.74,.012)
            g.pose(fr,p,.23,seat=1 if self.finish else smooth(3797,3814,fr),opening=.23,wind=.18,slack=.53,gaze=-.39+.36*q,scale=1.1)
            # Across her shoulder to the people sharing the light and the spare dark tent beyond them.
            c=S.ground(-11.38+2.49*q,-4.33-2.20*q,1.57+.57*q);target=S.ground(-7.03,-.24,.86)
            S.view(c,target,35,.018*np.sin(fr*.043))
        else:
            q=key(fr,(3857,0),(3874,.15),(3890,.39),(3906,.61),(3928,.79),(3956,.90),(3997,1));p=S.ground(-7.23,-1.74,.01)
            g.pose(fr,p,.23,seat=1,opening=.31,wind=.21,slack=.46,gaze=-.15)
            target=mix(S.ground(-7.04,.26,.87),S.ground(-1.4,5.04,0),q)
            lift=2.45*np.exp(4.02*q);distance=4.9+13*q
            ang=-.19+.69*q-.43*np.sin(np.pi*q)
            c=target+[distance*np.sin(ang),-distance*np.cos(ang),lift]
            if self.finish:target+=np.array([-.19,-.76,-.11])*(1-smooth(3857,3888,fr))
            S.view(c,target,31-q*2.1,.014+.061*q)
    def build_walkout(self):
        from camp import Camp
        self.camp=Camp(self.S)
        if self.finish:
            from walkout_sand import lay_bed
            lay_bed(self.S)
    def walkout(self,fr):
        S=self.S;g=self.g;camp=self.camp;camp.animate(fr)
        u=key(fr,(4198,.57),(4259,.627),(4312,.678),(4373,.738),(4435,.798),(4468,.827))
        p=sampled(camp.path,u);q=sampled(camp.path,u+.004);heading=-math.atan2(q[0]-p[0],q[1]-p[1])
        p=S.ground(*p,.015);g.pose(fr,p,heading,wind=.37,gaze=.12*np.sin(fr*.025),tilt=.12*smooth(4354,4418,fr))
        front=self.camp.gold.data;front.bevel_factor_end=u+.001
        # Watch her through the gate from the outside. The camera then lets her pass it toward the ridge.
        x,y,z=interpolate(fr,[(4198,20.2,-11.6,18.8),(4220,24.2,-5.1,13.2),(4242,26.6,2.9,7.9),
                             (4268,28.8,7.0,4.2),(4292,30.9,10.5,2.40),(4318,34.4,12.40,2.10),
                             (4334,36.8,9.57,2.26),(4350,37.6,5.75,2.46),(4380,34.0,.32,3.22),
                             (4427,26.6,-.47,3.37),(4468,24.4,-.16,3.55)])
        c=S.ground(x,y,z);target=p+[0,.05,.94+16.4*smooth(4406,4468,fr)]
        # Clear the ground immediately in front of the planted foot even from outside the wall.
        u=np.linspace(.07,.94,28);foot=p+[0,0,.10];ray=c+(foot-c)*u[:,None]
        c[2]=max(c[2],float(np.max((S.floor(ray[:,0],ray[:,1])+.06-foot[2]*u)/(1-u))))
        if self.finish and fr<4376:
            from finish_story import exit_camera
            exit_camera(self,fr,p,c,target)
        else:S.view(c,target,25.7+.75*np.sin(fr*.018),.016*np.sin(fr*.019))
