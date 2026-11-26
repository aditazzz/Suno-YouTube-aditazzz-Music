"""Develop native plates in the kept camera. Inputs and masks are in the output raster."""
import subprocess
from functools import cached_property,lru_cache
import json
from math import ceil,floor
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

from film import ROOT, FINISH_SURVEY, REVISED_SURVEYS, BLENDER_PY, GUIDE, addr, wind_stage, reveal_time, SHOTS, EDL
from inputs import displayed,stagefile
from develop import Grade,smooth
from reveal import Reveal
from lift import Lift
from gold import Grain
from orbit import CampOrbit
from slide_join import join as slide_join
from water import Water
from walkwind.air import camera_packets,develop as crest_air
from finish_look import moonlit_detail,through_quartz,mineral_moonlight,quiet_footways,develop_starlight
from finish import tree_light,heel_sand
from plates import over

def blend(a,b,q):
    return cv2.addWeighted(a,1-float(q),b,float(q),0)

def asbyte(a):return np.uint8(np.clip(a,0,255)+.5)

def develop_heel(rgb,mask,f):
    mask=mask.copy()
    mask[...,3]=asbyte(mask[...,3]*smooth(628,636,f)*.94)
    return over(heel_sand(rgb,f),mask)

@lru_cache(1)
def heel_light():
    return json.loads(Path(__file__).with_name('v5-optics.json').read_text())['heel_handle_meter']

def read_hero_return(path):
    raw=cv2.imread(str(path),cv2.IMREAD_UNCHANGED)
    if raw is None or raw.shape!=(1080,1920,4) or not np.isfinite(raw).all():raise ValueError(path)
    if raw.dtype.kind!='f' or raw[...,3].max()<.5:raise ValueError(f'Invalid hero coverage in {path.name}')
    return raw

def hero_plate(role,f,w):
    name='ride_front' if role=='ride' else 'well_look_up'
    path=ROOT.parent/'hero/out'/name/f'{role}_{f:04d}.exr'
    raw=read_hero_return(path)
    alpha=np.clip(raw[...,3:],0,1)
    rgb=np.maximum(0,raw[...,:3][...,::-1])
    if w!=1920:
        # Box-filter associated radiance and coverage together; restore straight RGB after resampling.
        rgb=cv2.resize(rgb*alpha,(w,w*9//16),interpolation=cv2.INTER_AREA)
        alpha=cv2.resize(alpha,(w,w*9//16),interpolation=cv2.INTER_AREA)[...,None]
        rgb=np.divide(rgb,alpha,out=np.zeros_like(rgb),where=alpha>1e-6)
    return rgb,alpha

def encode_straight(rgb,alpha):
    srgb=np.where(rgb<.0031308,12.92*rgb,1.055*np.maximum(rgb,0)**(1/2.4)-.055)
    return asbyte(np.concatenate([srgb,alpha],axis=2)*255)

def retimed(a,b,q):
    if q<.015:return a
    if q>.985:return b
    h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w].astype('f')
    a0,b0=[cv2.resize(cv2.cvtColor(i,cv2.COLOR_RGB2GRAY),(320,180)) for i in (a,b)]
    flow=cv2.resize(cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST).calc(a0,b0,None),(w,h))*(w/320)
    def warp(im,weight):
        return cv2.remap(im,xx+weight*flow[...,0],yy+weight*flow[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    return blend(warp(a,-q),warp(b,1-q),q)

def levels(path):
    data=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v','-vf','scale=160:90,format=gray','-fps_mode','passthrough','-f','rawvideo','-'])
    return np.frombuffer(data,'u1').reshape(-1,90*160).mean(1)

def match_meter(im,target):
    small=cv2.resize(im,(160,90),interpolation=cv2.INTER_AREA)
    measured=small.mean((0,1))@np.array([.2126,.7152,.0722])
    gain=np.clip((target+.35)/(measured+.35),.48,1.95)
    y=im@np.array([.2126,.7152,.0722],'f')
    light=y[...,None]*gain
    return asbyte(light+(im-y[...,None])*np.sqrt(gain))

class Picture:
    def __init__(self,folder,width,inner,meter):
        self.folder=folder;self.w=width;self.h=width*9//16;self.inner=inner
        self.meter=meter;self.grades={};self.ocio=None
        self.video=cv2.VideoCapture(str(inner))
        if int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))!=690:raise ValueError(inner)
        self.next_video=-1
    def close(self):
        for g in self.grades.values():g.close()
        self.video.release()
        if self.ocio:
            self.ocio.stdin.close();self.ocio.stdout.close()
            if self.ocio.wait():raise RuntimeError('Blender colour transform failed')
        self.photo.cache_clear();self.hero.cache_clear();self.exposure.cache_clear()
    def grade(self,n):
        if n not in self.grades:
            survey=FINISH_SURVEY if n in REVISED_SURVEYS else None
            self.grades[n]=Grade(n,self.w,survey)
        return self.grades[n]
    @cached_property
    def reveal(self):return Reveal(self.w,FINISH_SURVEY)
    @cached_property
    def lift(self):return Lift(self.grade('coaster'))
    @cached_property
    def water(self):return Water(finish=True)
    @cached_property
    def grain(self):return Grain(self.w)
    @cached_property
    def camp(self):return CampOrbit(self.story('oasis',3997))
    def sky(self,i):
        if self.next_video!=i:self.video.set(cv2.CAP_PROP_POS_FRAMES,i)
        ok,im=self.video.read();self.next_video=i+1
        if not ok:raise ValueError((self.inner,i))
        rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
        return rgb if self.w==1920 else cv2.resize(rgb,(self.w,self.h),interpolation=cv2.INTER_AREA)
    @lru_cache(5)
    def exposure(self,n,f):
        path=stagefile(self.folder,n,f)
        cloth=(n in ('oasis','walkout') and f>=3728)
        if not self.ocio:
            self.ocio=subprocess.Popen([str(BLENDER_PY),'src/finish/colour.py'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        self.ocio.stdin.write((str(path)+'\n').encode())
        self.ocio.stdin.flush()
        data=self.ocio.stdout.read(self.h*self.w*3)
        if len(data)!=self.h*self.w*3:raise ValueError(path)
        rgb=np.frombuffer(data,'u1',count=self.h*self.w*3).reshape(self.h,self.w,3)
        mask=None
        if cloth:
            ids=cv2.imread(str(path.with_suffix('.cloth.png')),cv2.IMREAD_GRAYSCALE)
            if ids is None or ids.shape!=(self.h,self.w):raise ValueError(f'Missing cloth holdout for {path}')
            # Feather one physical pixel at the true occluding edge.
            mask=cv2.GaussianBlur(ids,(3,3),.55).astype('f')/255
        return rgb,mask
    @lru_cache(5)
    def photo(self,n,f):
        path=stagefile(self.folder,n,f)
        if path.suffix=='.exr':
            return self.exposure(n,f)[0]
        rgb=displayed(path)
        if rgb.shape!=(self.h,self.w,3):raise ValueError((path,rgb.shape))
        return rgb
    def story(self,n,f):
        clean=n=='coaster' and 2417<=f<=2476
        g=self.grade(n)
        rgb,cloth=self.exposure('coaster-clean' if clean else n,f)
        im=g.apply(rgb,f,clay_camp=n in ('oasis','walkout'),cloth=cloth)
        if clean:
            rgb,alpha=hero_plate('ride',f,self.w)
            from finish_fixes import seat
            im=seat(im,rgb,alpha,f)
        return im
    @lru_cache(4)
    def hero(self,f):
        im=self.photo('hero',f)
        if 1391<=f<=1408:im=through_quartz(im,Image.fromarray(self.photo('walk',1390)),f-1390)
        if 1414<f<1451:im=mineral_moonlight(im,.91*smooth(1414,1429,f)*(1-smooth(1438,1451,f)))
        if 1448<f<1698:
            im=moonlit_detail(im,.84*smooth(1448,1460,f)*(1-smooth(1525,1540,f))+1.34*smooth(1512,1572,f)*(1-smooth(1667,1698,f)))
        if f>=1999:
            z=1+.17*(1-smooth(1999,2012,f))
            w,h=self.w,self.h
            dx=(w-w/z)*.51;dy=(h-h/z)*.48
            end=Image.fromarray(self.photo('turns',2012)).resize((w,h),Image.Resampling.BICUBIC,box=(dx,dy,dx+w/z,dy+h/z))
            im=blend(im,np.asarray(end),smooth(1999,2012,f))
        if 1397<=f<=1429 or 1961<=f<=2011:
            q=smooth(1397,1407,f)*(1-smooth(1425,1429,f)) if f<1500 else smooth(1960,1966,f)
            im=asbyte(im+q*(self.photo('macro',f).astype('f')-self.photo('hero',f)))
        return im
    def original_dive(self,f):
        im=self.photo('optics',f)
        if f<2563:im=blend(im,self.photo('turns',f),1-smooth(2549,2563,f))
        if f>=2615:im=blend(im,self.photo('original',f),smooth(2615,2625,f))
        if f>=2616:
            from handover import flying_sand
            im=flying_sand(im,f)
        return im
    def heel(self,f):
        mask=cv2.imread(str(stagefile(self.folder,'heel-mask',f)),-1)
        return develop_heel(self.photo('walk',f),cv2.cvtColor(mask,cv2.COLOR_BGRA2RGBA),f)
    def base(self,n,f):
        if n=='open':
            if f<161:im=moonlit_detail(self.photo('grain',f),.78*(1-smooth(151,204,f)))
            elif 350<=f<=547:
                im=moonlit_detail(self.photo('opening',f),(1.08+1.48*smooth(344,365,f)*(1-smooth(493,539,f)))*(1-smooth(530,548,f)))
                if f<=361 or f>=536:im=blend(self.photo('walk',f),im,smooth(349,362,f)*(1-smooth(535,548,f)))
            else:
                im=self.photo('walk',f)
                amount=.78*(1-smooth(151,204,f))+1.06*smooth(257,300,f)*(1-smooth(511,564,f))
                im=moonlit_detail(im,amount)
            return im
        if n=='heel':
            return self.heel(f)
        if n=='grain-entry' and f<1391:
            im=self.photo('walk',f)
            if f<=1387:
                pressed=self.photo('early-print',f)
                pressed=asbyte(pressed*np.clip((im.mean()+4)/(pressed.mean()+4),.64,1.42))
                im=blend(im,pressed,1-smooth(1379,1386,f))
            return im
        if n in ('sneaker','first-print','grain-entry'):return self.hero(f)
        if n=='first-reveal':
            t=reveal_time(f)
            return retimed(self.hero(floor(t)),self.hero(ceil(t)),t-floor(t))
        if n=='montage' and f>2226:
            old=self.photo('old-ink',f)
            return self.reveal.ink(old,f) if f>=2255 else self.reveal.match(self.story(n,f),old,f)
        if n in SHOTS:
            im=self.story(n,f)
            if n=='slide' and f>=1669:return slide_join(im,self.hero(f-139),f)
            if n=='coaster':
                if f<=2307:return self.lift.develop(im,self.photo('old-ink',2285),f)
                if f>=2551:return blend(im,self.original_dive(f),smooth(2551,2564,f))
            if n=='walkout' and f>=4440:
                old=develop_starlight(self.photo('optics',f),.96)
                depth=cv2.resize(self.grade(n).field[...,2],(self.w,self.h))
                im=asbyte(im+(old.astype('f')-im)*((1-smooth(0,.0022,depth))*smooth(4440,4468,f))[...,None])
            return im
        if n=='inner':return self.sky(f-2632)
        if n=='dive':
            im=self.original_dive(f)
            if f>=2616:im=self.grain.mix(im,self.sky(0),f,True)
            if 2614<f<2630:
                from crystal import passing_facet
                im=passing_facet(im,self.photo('optics',2614),f)
            return im
        if n=='wind':
            im=self.photo(wind_stage(f),f)
            if f>=3346:
                a=im.astype('f');r,g,b=a.transpose(2,0,1);lum=.23*r+.62*g+.15*b
                k=self.w/960
                fine=lum-cv2.GaussianBlur(lum,(0,0),2*k)
                rake=cv2.GaussianBlur(lum,(0,0),1.1*k)-cv2.GaussianBlur(lum,(0,0),7.3*k)
                mask=smooth(12,28,lum)*(1-smooth(149,193,lum))*smooth(-5,12,b-r)*smooth(3346,3372,f)*(1-smooth(3641,3655,f))
                im=asbyte(a+(14*np.tanh((.68*fine+.94*rake)/14)*mask)[...,None])
            if f>3477:im=crest_air(im,camera_packets(f),float(smooth(3477,3506,f))*.93)
            if f<=3345:
                amber=self.sky(689)
                old=self.grain.mix(im,amber,f,False)
                im=self.grain.mix(im,amber,f,False,finish=True)
                self.gate_shift=(im[::4,::4].astype('f')-old[::4,::4]).mean((0,1))@np.array([.2126,.7152,.0722])
            return im
        if n=='atlas':
            im=self.photo('atlas-plate',f)
            dep=1-smooth(3998,4047,f)
            im=quiet_footways(moonlit_detail(im,2.53*dep),.33*dep)
            im=develop_starlight(im,.64*smooth(3998,4024,f))
            if f<=4054:return self.camp.step(im,f)
            if not hasattr(self,'origin'):
                from atlas_route import Origin
                self.origin=Origin()
            return self.origin.develop(im,f)
        if n=='star-writing':return develop_starlight(self.photo('optics',f),.96)
        if n in ('well','reflection'):
            im=self.photo('approach-well' if n=='well' else 'owl',f)
            if n=='reflection':im=tree_light(im,f)
            plate=encode_straight(*hero_plate('well',f,self.w)) if 4880<=f<=4960 else None
            return self.water.develop(im,f,plate)
        raise ValueError(n)
    def frame(self,f):
        self.gate_shift=0.
        n=addr(f);im=self.base(n,f)
        from finish_fixes import OWL_CLEAN,clear_curl
        if f in OWL_CLEAN:im=clear_curl(im,self.base(n,OWL_CLEAN[f]))
        if n=='inner':return im
        # The approved camera exposure is stored at every film frame. Read a single
        # luminance per frame from v5, then develop native scene pixels and colours.
        im=match_meter(im,self.meter[f]+self.gate_shift)
        if 681<=f<701:
            from heel_join import take
            im=take(match_meter(self.heel(f),heel_light()[str(f)]),im,f)
        if n=='atlas' and f>=4095:
            from night_colour import galaxy
            im=galaxy(im,f)
        if n=='night' and f>=4697:
            from night_colour import descent
            im=descent(im,f)
        if 4737<=f<=4750:
            from landing_join import take,surface_light
            step=match_meter(self.photo('approach-well',f),surface_light()[str(f)])
            im=take(im,step,f)
        from finish_fixes import polish
        return polish(im,f)
