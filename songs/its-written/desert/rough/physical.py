"""Render serial CPU Cycles frames. The compositor receives one colour-managed image at a time."""
from pathlib import Path
import argparse
import math
import os
import signal
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from props import *
def controls(obj,label):
    return [n.outputs[0] for m in obj.data.materials for n in m.node_tree.nodes if n.label==label]
import OpenImageIO as oi
ap=argparse.ArgumentParser()
ap.add_argument('stage',choices=['walk','wind','oasis','well'])
ap.add_argument('width',type=int);ap.add_argument('samples',type=int)
ap.add_argument('first',type=int);ap.add_argument('last',type=int);ap.add_argument('dest',type=Path)
ap.add_argument('--frames');ap.add_argument('--stills',action='store_true')
args=ap.parse_args();os.chdir(ROOT)
reserve=int((ROOT/'START_ROUGH.txt').read_text())+12600-900
if args.dest.parent.name=='final' and args.dest.name=='v1.mp4' and reserve-time.time()<900:
    # Across this wide timelapse the moon, crest and shadow carry the passage.
    args.width,args.samples=768,4
well_insert=args.stage=='well' and args.dest.parent.name=='rev' and not args.stills
if well_insert:
    remaining=reserve-time.time()
    if remaining<560:args.width,args.samples=800,4
    if remaining<390:args.width,args.samples=704,4
    if remaining<265:args.width,args.samples=640,3
frames=[int(s) for s in args.frames.split(',')] if args.frames else range(args.first,args.last+1)
if args.stills and args.dest.parent.name=='bench' and args.samples==8:
    # The finishing price uses the 24-sample frames. Keep a cheap control in each scene.
    groups=[(0,632),(633,1183),(1184,1390)] if args.stage=='walk' else [(frames[0],frames[-1])]
    samples_by_section=[[f for f in frames if a<=f<=b] for a,b in groups]
    frames=[sample[len(sample)//2] for sample in samples_by_section if sample]
w=args.width;h=round(w*9/16);name=args.stage
scene=bpy.context.scene;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cycles_device import configure
scene.render.engine='CYCLES';configure(scene);scene.cycles.samples=args.samples
scene.cycles.use_denoising=True;scene.cycles.max_bounces=3;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2
scene.cycles.transparent_max_bounces=1
scene.render.threads_mode='FIXED';scene.render.threads=min(16,os.cpu_count() or 8)
scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.resolution_percentage=100
scene.render.use_persistent_data=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=0
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.18
moon=sky(scene)
light=sun('Low desert moon',(-.87,.38,.25),1.38,(.46,.65,1),.084)
rim=sun('Last light on the crests',(-.67,.72,.15),.60,(.63,.76,1),.060)
sun('Dark sky counterlight',(.46,.73,.37),.53,(.31,.54,1),.22)
terr=Terrain(name)
if R2 and name=='walk' and args.first<=1390 and args.last>=1183:terr.close_stamp=76
if R2 and name=='well' and args.first<=4751 and args.last>=4670:terr.close_stamp=33
if R2 and 'ONEGRAIN_CLOSE_STAMP' in os.environ:
    terr.close_stamp=int(os.environ['ONEGRAIN_CLOSE_STAMP'])
terr.build();terr.sand()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam
cam.data.sensor_width=36;cam.data.clip_start=.0004;cam.data.clip_end=2200;cam.data.lens=28
cam.data.dof.use_dof=False
actor=Actor(model_boots=R2)
contact=point('Sand bright beneath the planted heel',(1,.45,.095),.18)
foot_lights=[contact]+[point('Afterglow of the previous step '+str(k),(1,.45,.095),.18) for k in (1,2)]
for lamp in foot_lights:lamp.data.energy=0
if name=='walk':
    gem=crystal();gem.scale=(.0118,)*3
    bed=grain_bed(terr,float(pathx(-16.5)),-16.5)
    secondgem=crystal();secondgem.scale=(.057,)*3
    gemdream=controls(gem,'Stars caught in quartz')[0];ringr=controls(bed,'Grain impact radius');ringp=controls(bed,'Grain impact power')
    innerlight=point('The mote catches the last light',(1,.58,.22),.015)
if name=='wind':dust=Saltation()
if name=='oasis':palms(terr)
if name=='well':well=Well(terr,actor)
def view(pos,target,lens=30,roll=0,lookx=0,looky=0,focus=None,fstop=5.6):
    pos=np.asarray(pos,float);target=np.asarray(target,float)
    cam.location=pos
    direction=Vector(target-pos)
    rotation=direction.to_track_quat('-Z','Y')
    if roll:
        from mathutils import Quaternion
        rotation=rotation@Quaternion((0,0,1),roll)
    cam.rotation_euler=rotation.to_euler();cam.data.lens=lens;cam.data.shift_x=lookx;cam.data.shift_y=looky
    cam.data.dof.use_dof=focus is not None
    if focus is not None:cam.data.dof.focus_distance=max(.001,focus);cam.data.dof.aperture_fstop=fstop
def above(x,y,z):return np.array([x,y,terr.h(x,y)+z],float)
def traveller(i,ph,t,y,visible=True,lateral=0,wind_heading=None):
    actor.obj.hide_render=not visible
    x=float(pathx(y))+lateral;angle=math.atan(float(pathdx(y)));z=float(terr.surface(x,y))-.018
    if wind_heading is not None:
        x,y,heading=wind_heading;angle=-heading;z=float(terr.surface(x,y))-.010
    if visible:
        gx=(terr.h(x+.04,y)-terr.h(x-.04,y))/.08;gy=(terr.h(x,y+.04)-terr.h(x,y-.04))/.08
        ca=math.cos(angle);sa=math.sin(angle)
        actor.pose(i,ph,t,x,y,z,angle,ca*gx-sa*gy,sa*gx+ca*gy)
    return np.array([x,y,z])
def walking_rings(i,t,origin,y0=0,strength=1,spread=1):
    for k in range(3):
        x,y=foot_xy(i-k,origin,y0);age=max(0,t-CONTACTS[i-k])
        if R2:
            # Each heel strikes a fixed patch of sand. The previous step decays to zero by the next-but-one.
            old=i-k
            a=math.atan(float(pathdx(y)))
            x-=.093*math.sin(a);y-=.093*math.cos(a)
            if name=='oasis' and (CONTACTS[old]*30<3740 or getattr(actor,'walkwind',False)):
                # The grove pickup carries her forwards. Register the mark to her stance at
                # contact, so its position stays fixed even as the camera and her body leave.
                root_y=mix(-23.05,y0+(old-origin)*.49-.205,smooth(3656,3740,CONTACTS[old]*30))
                if getattr(actor,'walkwind',False):
                    from walkwind.landform import grove_y
                    root_y=grove_y(old)
                a=math.atan(float(pathdx(root_y)))
                side=.076 if old%2 else -.076
                x=float(pathx(root_y))+side*math.cos(a)+.112*math.sin(a)
                y=root_y-side*math.sin(a)+.112*math.cos(a)
            fade=(1-smooth(.62,1.08,age)) if k<2 and old>=origin else 0
            attack=float(smooth(-.015,.14,age))
            power=strength*fade*attack*math.exp(-age*1.32)
            terr.ring(k,x,y,.035+1.31*age,.066-.038*min(age,1),.73*power)
            lamp=foot_lights[k];lamp.location=above(x,y,.095)
            lamp.data.use_custom_distance=True;lamp.data.cutoff_distance=1.8
            lamp.data.energy=3.4*power*math.exp(-age*2.8)
            continue
        size=spread*(2.0*age+.014)
        terr.ring(k,x,y,size,.052+.12*age,1.8*strength*smooth(-.016,.145,age)*math.exp(-age*1.95))
        lamp=foot_lights[k];lamp.location=above(x,y,.10);lamp.data.energy=14*strength*smooth(-.016,.145,age)*math.exp(-max(0,age-.14)*3.7)
def first_world(fr):
    t,i,ph,gait,v=musical(fr)
    # Time-lapse wind shifts the close swales under a distant horizon.
    if t>BAR[18]-.54:
        dur=max(0,v-BAR[18]+.54);amp=smooth(BAR[18]-.54,BAR[18]+.62,v)
        terr.wave(amp*(2.70*dur+.85*math.sin(dur*2.68)),amp*(.85*dur+.60*math.sin(dur*1.59)))
    yg=-16.5;xg=float(pathx(yg));zg=float(terr.surface(xg,yg))
    y=(gait-36)*.49-.205
    actorpos=traveller(i,ph,t,y,t>17.74,-4.6*(1-smooth(17.55,20.985,t)))
    strike=1.810
    fall=1-smooth(0,strike,t)**1.45
    vertical=.0065+.143*fall
    gem.location=(xg+.012*fall,yg-.009*fall,zg+vertical)
    gem.rotation_euler=(.28+1.21*fall,-.36+.74*fall,.45+1.17*fall+.085*math.exp(-max(0,t-strike)*3.1)*math.sin(22*max(0,t-strike)))
    gem.hide_render=t>12
    gemdream.default_value=.16+.92*smooth(2.60,4.35,t)*(1-smooth(4.75,5.61,t))
    for control in ringr:control.default_value=.053*max(0,t-strike)+.0145*max(0,t-strike)**2
    for control in ringp:control.default_value=(3.2*smooth(strike-.016,strike+.12,t)*math.exp(-max(0,t-strike)*1.40) if t>=strike-1/60 else 0)
    bed.hide_render=t>10.85
    # A second foreground fleck offers a glimpse of the constellation on the repeated invocation.
    d2y=-7.41;d2x=float(pathx(d2y))+.075
    secondgem.location=(d2x,d2y,float(terr.surface(d2x,d2y))+.027);secondgem.rotation_euler=(.49,.22,1.5)
    secondgem.hide_render=t<6.7 or t>16
    innerlight.location=(xg-.021,yg-.015,zg+vertical+.04);innerlight.data.energy=.12*(1-smooth(5,7,t))
    if os.environ.get('ONEGRAIN_ROUGH2')=='1' and fr<230:
        innerlight.data.use_custom_distance=True;innerlight.data.cutoff_distance=.11
        innerlight.data.energy*=.35;innerlight.data.color=(1,.73,.46)
        for control in ringp:control.default_value*=.43
    terr.gait.default_value=gait;terr.front.default_value=foot_xy(i)[1]+.07
    terr.ink.default_value=smooth(20.955,21.108,t)*.83
    terr.road.default_value=.09+.36*smooth(6.63,7.22,t)+.19*smooth(15.77,16.29,t)
    terr.draw.default_value=anim(v,[(0,-25),(6.55,-18.8),(6.94,-15.4),(7.67,-12.1),(9.4,-8.7),(11.1,-6.4),(15.55,-2.4),(16.14,-.7),(17.85,38),(20.3,75)])
    terr.network.default_value=0
    terr.weather.default_value=smooth(BAR[18]-.25,BAR[18]+1.15,t)
    terr.warp.default_value=.0018*v+.116*(v-5.42)*smooth(5.25,6.26,t)+.195*(v-14.7)*smooth(14.6,15.45,t)
    if t>=BAR[10]:terr.warp.default_value+=.057*(v-BAR[10])
    terr.roll.default_value=.0
    terr.rollpos.default_value=-1.23*v-.26*math.sin(gait*2*math.pi)
    if t<CONTACTS[36]-1/60:
        contact.data.energy=0
        age=max(0,t-strike);on=float(smooth(strike-1/60,strike+.13,t))
        terr.ring(0,xg,yg,.053*age+.0145*age**2,.0045+.004*age,3.55*math.exp(-age*.94)*on)
        terr.ring(1,xg,yg,.036*age+.007*age**2,.0035+.008*age,1.36*math.exp(-age*.93)*on)
        terr.ring(2,xg,yg,2.6*age,.025+.045*age,.37*math.exp(-age*.37)*on)
        if os.environ.get('ONEGRAIN_ROUGH2')=='1' and fr<230:
            for k,control in enumerate(terr.power):
                control.default_value*=([.33,.075,0][k]*float(smooth(strike-.012,strike+.19,t)))
    else:walking_rings(i,t,36,strength=1.1)
    if t<21.34:
        # At grain height the camera travels with the falling subject. After the first ring it
        # passes across the fracture, rocks back and finds the road drawing itself ahead.
        d=loganim(v,[(0,.074),(1.23,.052),(1.82,.076),(2.72,.126),(3.5,.074),(4.38,.040),(4.88,.048),(5.58,.23),(6.16,.52),(7.25,1.22),(9.8,2.32),(11.65,1.50),(13.6,.66),(14.8,.91),(16.14,1.38),(18.55,1.79),(20.2,.91)])
        travel=anim(v,[(0,0),(4.92,.0001),(6.1,.13),(7.1,.84),(9.39,3.8),(11.69,6.9),(13.66,8.65),(15.14,10.4),(17.2,13.2),(19,15.2),(20.2,16.08)])
        yy=yg+travel;xx=float(pathx(yy));mixlow=smooth(4.95,6.62,t)
        # Travel diagonally across the ridges while the first road outruns the lens.
        xx+=1.47*math.sin((v-6.4)*1.12)*smooth(5.8,7.3,t)*(1-smooth(10.8,13.37,t))
        xx+=.61*math.sin((v-14.7)*1.34)*smooth(14.11,15.14,t)*(1-smooth(18.6,20,t))
        gaze_y=yy+mixlow*anim(v,[(5,.05),(7,.83),(9.2,2.3),(12.3,1.1),(14.1,.56),(16.1,2.26),(18.72,2.8),(20.2,.72)])
        gaze_x=float(pathx(gaze_y))
        target=above(gaze_x,gaze_y,(1-mixlow)*vertical+.022*mixlow)
        angle=anim(v,[(0,-.47),(1.83,-.15),(3.3,.69),(4.68,1.22),(6.27,.52),(8.7,-.39),(11.4,.61),(13.7,.94),(16.4,-.46),(18.93,-.32),(20.2,.68)])
        posxy=(xx+d*math.sin(angle),yy-d*math.cos(angle))
        clearance=anim(v,[(0,.009),(1.79,.031),(3.32,.077),(4.4,.012),(5.9,.083),(7.08,.16),(9.7,.43),(11.66,.28),(13.6,.13),(15.1,.20),(17.4,.38),(19.21,.31),(20.2,.18)])
        pos=above(*posxy,clearance+(1-mixlow)*vertical)
        dream_pass=smooth(12.81,13.58,v)*(1-smooth(13.73,14.64,v))
        if dream_pass>0:
            mark=np.array(secondgem.location)
            close=above(mark[0]+.164,mark[1]-.23+.048*(v-13.59),.112)
            pos=mix(pos,close,dream_pass);target=mix(target,mark+np.array([.006,.012,.008]),dream_pass)
        # Run cross-grain through the two road phrases. The close ground has its own parallax.
        rush=(smooth(6.95,8.10,v)*(1-smooth(10.71,12.42,v))+
              smooth(14.51,15.67,v)*(1-smooth(17.97,19.28,v)))
        if rush>0:
            offset=.68*math.sin(v*1.23+.36)
            gx,gy=float(pathx(yy))+.70*math.sin(v*.92-.50),yy
            x0=gx+offset
            C=above(x0,gy-.72,.52+.12*math.sin(v*.83))
            T=above(gx-.32*offset,gy+.50+.11*math.cos(v*1.06),.005)
            pos=mix(pos,C,rush);target=mix(target,T,rush)
        roll=math.radians(anim(v,[(0,-8),(2.45,3),(4.55,-6),(6.06,1),(8.89,-2),(13.21,4),(15.27,-3),(18.77,1),(20.2,0)]))
        view(pos,target,29,roll,.018*math.sin(v*.63),0,float(np.linalg.norm(target-pos)) if t<5.6 else None,22 if t<5 else 28)
    if t>=19.21:
        if t<21.34:entry_pos=pos.copy();entry_target=target.copy()
        sec=v-BAR[10]
        dist=loganim(sec,[(-1,.93),(0,.62),(.59,.92),(1.72,2.8),(3.44,3.38),(5.5,4.3),(7.9,3.48),(10.4,4.1),(12.8,3.63),(15.6,5.4),(17.55,6.9),(18.47,12.2),(20.3,16.7),(22.6,20.9),(24.18,17),(25.5,8.2)])
        bearing=anim(sec,[(-1,.60),(0,.75),(1.4,1.28),(3.6,.60),(5.9,-.52),(8.2,-1.36),(10.8,-.72),(13.3,.63),(15.5,1.20),(18,.31),(20.2,-.8),(22.8,-1.20),(25.5,-1.4)])
        # The long side-arc changes elevation as it changes direction, leaving the far ridge stable.
        if 1.2<sec<18.6:
            q=smooth(1.2,3.0,sec)*(1-smooth(16.5,18.6,sec))
            dist+=q*(.77*math.sin(sec*.84)+.26*math.cos(sec*1.36))
            bearing+=q*.36*math.sin(sec*.96+.20)
            terr.roll.default_value=.165*q;terr.rollpos.default_value=-1.28*sec
        elevation=anim(sec,[(-1,.17),(0,.14),(.63,.25),(1.62,.91),(3.8,1.44),(6.3,.89),(8.3,1.27),(10.5,1.68),(13.3,1.21),(16.5,2.52),(18.3,3.38),(20.6,3.07),(23.5,3.65),(25.48,4.14)])
        eye=anim(sec,[(-1,.079),(0,.059),(.76,.28),(1.9,.89),(4,1),(9,.91),(15,.98),(18,.78),(23,.52),(25.5,.15)])
        target=actorpos+np.array([0,.075,eye])
        xx=actorpos[0]+dist*math.sin(bearing); yy=actorpos[1]-dist*math.cos(bearing)
        pos=above(xx,yy,elevation)
        # The low approach swings into the heel without a cut before the first planted foot.
        if t<21.34:
            q=smooth(19.21,20.92,t)
            pos=mix(entry_pos,pos,q);target=mix(entry_target,target,q)
        # Stay above the displaced triangle under the lens as it swings past the first heel.
        pos[2]=max(pos[2],float(terr.surface(pos[0],pos[1]))+.095)
        view(pos,target,29,math.radians(-2.3*math.sin(sec*.41)),.067*math.sin(sec*.51)*smooth(.8,2.5,sec),-.03*smooth(1,3,sec))
    if t>=BAR[18]-.50:
        previous=np.array(cam.location)
        forward=cam.rotation_euler.to_quaternion()@Vector((0,0,-1))
        target_previous=previous+np.array(forward)*max(.2,float(np.linalg.norm(previous-actorpos)))
        tt=v-BAR[18]
        # A travelling wide shot. The fore-ridge crosses the frame as the distant profile holds.
        wide=loganim(tt,[(-.5,9.1),(0,13.0),(1.10,16.7),(2.30,15.2),(3.6,18.4),(4.65,15.9),(5.65,13.0),(6.92,8.9)])
        heading=-1.54+.31*tt+.44*math.sin(tt*1.17-.32)
        X=actorpos[0]+wide*math.sin(heading);Y=actorpos[1]-wide*math.cos(heading)+1.45*math.sin(tt*1.24)
        C=above(X,Y,1.45+.67*math.sin(tt*1.17+.37))
        C[2]=max(C[2],actorpos[2]+1.27)
        T=actorpos+np.array([.69*math.sin(tt*.85),1.55*math.sin(tt*.91-.27),.23])
        q=smooth(-.50,.42,tt)
        C=mix(previous,C,q);T=mix(target_previous,T,q)
        # Hold the far traveller on her crest as the time-lapse moves larger ridges between us.
        keep_crest=smooth(.20,.96,tt)*(1-smooth(4.84,5.57,tt))
        if keep_crest>0:
            u=np.linspace(.045,.965,54)
            crest=terr.surface(C[0]+u*(actorpos[0]-C[0]),C[1]+u*(actorpos[1]-C[1]))+.18
            limit=float(np.max((crest-u*(actorpos[2]+.92))/(1-u)))
            C[2]+=keep_crest*(.41+.33*float(np.logaddexp(0,(limit-C[2])/.33)))
        # The camera slips down the light to a grain in a print, ready for the locked pickup.
        pickup=smooth(4.74,6.49,tt)
        if pickup>0:
            fx,fy=foot_xy(76);ground=terr.surface(fx,fy)
            secondgem.hide_render=False;secondgem.scale=(.013,)*3
            secondgem.location=(fx,fy,ground+.009);secondgem.rotation_euler=(.35,.17,-.35)
            mark=np.array([fx,fy,ground+.012])
            close=loganim(tt,[(4.74,9.8),(5.41,5.5),(5.88,2.30),(6.18,.91),(6.42,.31),(6.66,.095),(6.91,.036)])
            entry=mark+np.array([-.22,-.36,.91])*close
            C=mix(C,entry,pickup);T=mix(T,mark,pickup)
            # Follow the windward face above the actual triangulated surface as it drops to the quartz.
            clearance=mix(.32,.009,pickup)
            floor=float(terr.surface(C[0],C[1]))+clearance
            C[2]=max(C[2],floor)
            # Clear the intermediate crest so its dark underside can never cross the lens.
            u=np.linspace(.08,.94,28)
            ridge=terr.surface(C[0]+u*(T[0]-C[0]),C[1]+u*(T[1]-C[1]))+.004
            C[2]=max(C[2],float(np.max((ridge-u*T[2])/(1-u))))
            # An old print still glows, more faintly than the heel that formed it.
            # Expose for the mineral as it comes forward into the approved pickup.
            approach=smooth(5.40,6.70,tt)
            terr.ink.default_value*=1-.56*approach
            terr.road.default_value*=1-.60*approach
            scene.view_settings.exposure=.18-.91*approach
        view(C,T,29,math.radians(2.1*math.sin(tt*.74)),.023*math.sin(tt*1.19)*(1-pickup),-.050*(1-pickup))
    # Forty days in three bars. A moving low source throws long shadows over the same horizon.
    if t>BAR[18]-1:
        a=(v-BAR[18])/2.30*2*math.pi;amount=smooth(BAR[18]-1,BAR[18]+.36,t)
        d=np.array([-.87+.87*amount*math.sin(a),.38+.83*amount*math.cos(a),.12+.15*(1+math.sin(a-.8))])
        rim.rotation_euler=(-Vector(d)).to_track_quat('-Z','Y').to_euler()
        rim.data.energy=.78+amount*(.64+.91*math.sin(a))
        direction=np.array([-.43+.91*amount*math.sin(a*.61),.875,.19+.20*amount*math.cos(a*.78)]);direction/=np.linalg.norm(direction)
        # The accelerated moon arcs over the same far profile once per musical bar.
        fw=cam.rotation_euler.to_quaternion()@Vector((0,0,-1));rr=cam.rotation_euler.to_quaternion()@Vector((1,0,0))
        az=math.atan2(fw.x,fw.y)+.55*math.sin(a-.66);elev=.145+.123*math.cos(a-.66)
        D=np.array([math.sin(az)*math.cos(elev),math.cos(az)*math.cos(elev),math.sin(elev)])
        direction=mix(direction,D,smooth(BAR[18]-.4,BAR[18]+.27,t));direction/=np.linalg.norm(direction)
        for j in range(3):moon.inputs[j].default_value=direction[j]
        light.rotation_euler=(-Vector(d)).to_track_quat('-Z','Y').to_euler()
        light.data.energy=1.38+amount*.64
        terr.roll.default_value=.30*amount;terr.rollpos.default_value=-3.28*v+a*.14
def wind_world(fr):
    t,i,ph,gait,v=musical(fr);sec=v-BAR[49];ae=max(0,sec)
    terr.wave(2.55*sec+1.15*math.sin(ae*2.76),.70*sec+1.24*math.sin(ae*1.45))
    y=(gait-192)*.49-3.92-.205;center=traveller(i,ph,t,y)
    angle=-1.33+.211*sec+.21*math.sin(sec*.71-.62)
    dist=anim(sec,[(0,11.3),(2.25,5.6),(4.55,8.9),(6.86,5.0),(9.2,7.8),(11.8,13.0)])
    x=center[0]+dist*math.sin(angle);cy=y-dist*math.cos(angle)
    hh=max(float(terr.h(x,cy))+.63,center[2]+.74+1.16*(.51+.49*math.cos(sec*1.31)))
    # Ride over the intervening crest before it can hide the red cap.
    lift=smooth(3374,3400,fr)*(1-smooth(3455,3482,fr))
    if lift>0:
        u=np.linspace(.035,.965,44)
        ridge=terr.h(x+u*(center[0]-x),cy+u*(y-cy))+.115
        keep=np.max((ridge-(center[2]+1.58)*u)/(1-u))
        excess=(keep-hh)/.25
        hh+=lift*(.52+.25*float(np.logaddexp(0,excess)))
    view((x,cy,hh),center+np.array([.13,.16,.79]),27,math.radians(3.5*math.sin(sec*.68)),.025,-.026)
    terr.road.default_value=.44;terr.draw.default_value=80;terr.ink.default_value=1.6;terr.front.default_value=y+.30
    terr.weather.default_value=.83
    terr.warp.default_value=sec*.77;terr.roll.default_value=.23;terr.rollpos.default_value=-sec*2.72;terr.gait.default_value=gait
    walking_rings(i,t,192,-3.92,strength=.86,spread=1.65)
def oasis_world(fr):
    t,i,ph,gait,v=musical(fr);sec=v-BAR[54]
    y=-3.92-.205+(gait-(54-1)*4)*.49;center=traveller(i,ph,t,y)
    lift=loganim(sec,[(0,3.0),(1.25,3.85),(2.45,6.8),(3.40,10.8),(5,19),(6.80,34),(8.67,57),(10,82),(11.46,116)])
    az=-.07+.095*sec+.12*math.sin(sec*.58);side=anim(sec,[(0,9.8),(1.8,8.6),(3.62,6.6),(5.5,4.05),(8.25,2.4),(10,1.8)])
    aim=mix(center,above(.6,1.2,0),smooth(1.2,8.8,sec))
    x=aim[0]+side*math.sin(az);yy=aim[1]-side*math.cos(az)
    view(above(x,yy,lift),aim+np.array([0,2.3*(1-smooth(.8,4,sec)),.45+3.5*(1-smooth(.3,4.7,sec))]),28,.12*smooth(1.9,8.5,sec)+.02*sec)
    terr.network.default_value=.012+.275*smooth(1.48,8.8,sec)
    terr.road.default_value=.75;terr.draw.default_value=90;terr.ink.default_value=1.9;terr.front.default_value=y+.21;terr.gait.default_value=gait
    terr.warp.default_value=.085*sec;terr.roll.default_value=.0;terr.rollpos.default_value=-sec*1.83
    walking_rings(i,t,(54-1)*4,-3.92,strength=1.0,spread=1+.33*max(0,sec))
def well_world(fr):
    t,i,ph,gait,v=musical(fr);sec=t-BAR[70];cx,cy,cz=well.x,well.y,well.z
    # She reaches the near rim on the sung 'well'. Each step before she stops is planted.
    reach=CONTACTS[282];limit=282.
    prog=min(limit,gait);y=1.96-.205-(limit-prog)*.49
    center=traveller(i if t<reach else int(limit),ph if t<reach else .0,min(t,169.7),y,True)
    if t>=reach:actor.obj.rotation_euler[2]=-.30
    actor.obj.rotation_euler[0]=-.30*smooth(reach-.45,reach+1.75,t)*(1-smooth(167.6,169.38,t))
    walking_rings(i if t<reach else int(limit),t,round(limit),1.96,.60,.62)
    terr.road.default_value=.18;terr.draw.default_value=cy;terr.ink.default_value=.70;terr.front.default_value=y+.16;terr.gait.default_value=prog
    terr.warp.default_value=.012*sec;terr.roll.default_value=.0;terr.rollpos.default_value=-.46*sec
    well.line.default_value=.12+.74*smooth(159.9,163.85,t)
    well.hat.default_value=smooth(160.69,162.71,t)
    well.osc.default_value=sec*.50
    hit=166.307
    well.radius.default_value=(-2 if t<hit else (t-hit)*.49)
    well.amplitude.default_value=smooth(hit-.016,hit+.14,t)*math.exp(-max(0,t-hit-.34)*.27)
    well.grain.hide_render=not (163.86<t<hit+.22)
    well.grain.scale=(.027,)*3
    fall=smooth(164.19,hit,t)**1.63
    well.grain.location=(cx-.93*(1-fall),cy+.73*(1-fall),cz+.080+1.57*(1-fall)-.12*smooth(hit,hit+.21,t))
    well.grain.rotation_euler=(.3+.9*fall,.14+1.2*fall,1.42*fall)
    height=loganim(t,[(158.3,7.5),(160,6.98),(161.62,4.90),(163.66,3.98),(165.2,3.83),(166.3,4.01),(168.2,6.38),(171.7,12.5),(175,25.5),(178.32,52),(182,103),(187.60,221)])
    dx=anim(t,[(158.3,-.20),(161.61,-.08),(164.1,.15),(166.3,.13),(170,-.12),(179,-.83),(187.6,-1.9)])
    dy=anim(t,[(158.3,-.50),(161.61,-.57),(164,-.45),(166.3,-.36),(172,.36),(180,1.1),(187.6,2.1)])
    roll=.045*sec-.00092*sec**2
    focal=31+13*smooth(159.1,162.4,t)*(1-smooth(166.5,169.1,t))
    view((cx+dx,cy+dy,cz+height*focal/31),(cx+dx,cy+dy+.00001,cz),focal,roll)
functions={'walk':first_world,'wind':wind_world,'oasis':oasis_world,'well':well_world}
if os.environ.get('ONEGRAIN_ROUGH2')=='1':
    sys.path.insert(0,str(ROOT/'src/rough2'))
    if os.environ.get('ONEGRAIN_BAKE_AIR')=='1':
        from walkwind.air_geometry import bake
        bake(globals())
    else:
        from plates import run
        run(globals())
    raise SystemExit(0)
dest=args.dest;dest.parent.mkdir(parents=True,exist_ok=True)
if args.stills:dest.mkdir(exist_ok=True,parents=True)
scratch=P/'cycles-frame.png';scene.render.filepath=str(scratch)
enc=None
if not args.stills:
    tmp=dest.with_suffix('.partial.mp4')
    enc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate','30','-i','-','-an','-vf','scale=960:540:flags=lanczos:out_color_matrix=bt709,setsar=1,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','15','-threads','4','-colorspace','bt709','-color_range','tv','-video_track_timescale','15360',str(tmp)],stdin=subprocess.PIPE)
def stop(sig,frame):
    if enc and enc.poll() is None:enc.terminate()
    raise SystemExit(1)
signal.signal(signal.SIGTERM,stop)
from post import composite,last_light
began=time.monotonic();deadline=int((ROOT/'START_ROUGH.txt').read_text())+12600
try:
    timings=[];cpu_seconds=[]
    for j,fr in enumerate(frames):
        frame_time=time.monotonic();cpu_time=time.process_time()
        if well_insert and j>=60 and time.time()>reserve-95:break
        if time.time()>deadline-900:raise TimeoutError('Final assembly reserve')
        if args.stills and (dest/f'{fr:04d}.png').is_file():continue
        functions[name](fr)
        overscan=name=='oasis' and dest.name=='grove-wide'
        if overscan:cam.data.lens*=.36
        bpy.ops.render.render(write_still=True)
        inp=oi.ImageInput.open(str(scratch));data=np.ascontiguousarray(inp.read_image(format=oi.UINT8)[:,:,:3]);inp.close()
        if name=='wind':
            _,_,_,gait,v=musical(fr);dust.draw(data,cam,terr,actor.obj.location,v,gait)
        composite(data,fr)
        if name=='well' and fr>=5035:
            from bpy_extras.object_utils import world_to_camera_view
            pos=world_to_camera_view(scene,cam,Vector((well.x,well.y,well.z+.070)))
            sec=fr/30-BAR[70]
            last_light(data,fr,w*pos.x,h*(1-pos.y),.045*sec-.00092*sec**2,cam.location.z-well.z-.070)
        if name=='oasis' and fr==3997:
            # The exact camera and palm plate furnish the near surface of the continuing orbital pull-out.
            import struct
            matrix=np.array(cam.matrix_world)
            with (P/('oasis-wide.bin' if overscan else 'oasis-departure.bin')).open('wb') as f:
                f.write(struct.pack('<ii',w,h))
                np.asarray([*cam.location,*matrix[:3,0],*matrix[:3,1],*-matrix[:3,2],2*cam.data.lens/36,1.15],'<f4').tofile(f)
                data.tofile(f)
        if args.stills:
            out=oi.ImageOutput.create(str(dest/f'{fr:04d}.png'));out.open(str(dest/f'{fr:04d}.png'),oi.ImageSpec(w,h,3,oi.UINT8));out.write_image(data);out.close()
        else:enc.stdin.write(data.tobytes())
        timings.append(time.monotonic()-frame_time);cpu_seconds.append(time.process_time()-cpu_time)
        if j%20==0 or fr==frames[-1]:print(f'rough frame {fr}, {time.monotonic()-began:.1f} s / {j+1}',flush=True)
    import json
    if not timings:raise SystemExit(0)
    finished_frames=list(frames)[:len(timings)]
    (P/(dest.stem+'-'+str(w)+'-'+str(args.samples)+'-perf.json')).write_text(json.dumps(dict(stage=name,width=w,samples=args.samples,first=finished_frames[0],last=finished_frames[-1],frames=finished_frames,times=timings,cpu_seconds=cpu_seconds)))
    if enc:
        enc.stdin.close()
        if enc.wait():raise RuntimeError('picture encoder failed')
        tmp.replace(dest)
finally:
    if enc and enc.poll() is None:enc.terminate();enc.wait()
