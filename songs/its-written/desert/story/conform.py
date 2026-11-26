"""Edit the song in exact, zero-based frame ranges and mux the release master from its first sample."""
from pathlib import Path
from contextlib import contextmanager
import sys,subprocess,os,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src/story'))
from develop import *
from reveal import Reveal
from gold import Grain
from water import Water
from plates import returned,rgba,over
from orbit import CampOrbit
from impressions import quartz,entry
from lift import Lift
from slide_join import join as match_slide
V4=R/'out/its-written_roughcut_v4.mp4';VINE=R.parent/'review/chat_watch/its-written_roughcut_v4_with_vine.mp4'
SKY=R.parent/'inner/out/inner_sky_1080.mp4';E=D/'edit';E.mkdir(exist_ok=True)
MASTER=next((Path.home()/"Documents/Original Music/It's Written").glob('*DistroKid*'))
SECTIONS=[('open',0,628),('heel',629,680),('driver',681,1182),('tally',1183,1366),('grain-entry',1367,1505),
          ('slide',1506,1681),('first-reveal',1682,1927),('sneaker',1928,1968),('first-print',1969,2011),
          ('montage',2012,2285),('coaster',2286,2566),('dive',2567,2631),('inner',2632,3321),
          ('wind',3322,3655),('oasis',3656,3997),('atlas',3998,4197),('walkout',4198,4468),
          ('star-writing',4469,4498),('night',4499,4750),('well',4751,4879),('reflection',4880,5627)]
def run(cmd):subprocess.run([str(p) for p in cmd],check=True)
def nframes(path):
    if not path.is_file():return 0
    p=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','csv=p=0',str(path)],capture_output=True)
    try:return int(p.stdout.strip())
    except ValueError:return 0
def interior():
    if SKY.exists() and nframes(SKY)==690:return SKY,0
    return VINE,2632
def source(path,a,n,resize=True):
    cmd=['ffmpeg','-v','error','-ss',f'{a/30:.9f}','-i',str(path),'-map','0:v:0','-frames:v',str(n)]
    if resize:cmd+=['-vf','scale=960:540:flags=lanczos']
    cmd+=['-fps_mode','passthrough','-pix_fmt','rgb24','-f','rawvideo','-']
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE)
    try:
        for i in range(n):
            raw=p.stdout.read(960*540*3)
            if len(raw)!=960*540*3:raise IOError((path,a+i))
            yield np.frombuffer(raw,'u1').reshape(540,960,3)
        p.stdout.close()
        if p.wait():raise ValueError(path)
    finally:
        p.stdout.close()
        if p.poll() is None:p.terminate();p.wait()
def picture(path,f):return next(source(path,f,1))
def shot(name,f):return read(D/f'shots/{name}/{f:04d}.jpg')
def dry(f):
    if f in returned('well'):return rgba(returned('well')[f])
    p=cv2.imread(str(D/f'shots/portrait/{f:04d}.png'),cv2.IMREAD_UNCHANGED)
    if p is None:raise FileNotFoundError(f'portrait {f}')
    return cv2.cvtColor(p,cv2.COLOR_BGRA2RGBA)
def take(f,arr,lo):return arr[f-lo]
def clock(f):
    from scipy.interpolate import PchipInterpolator
    key=np.array([[1682,1543],[1698,1560],[1730,1595],[1758,1643],[1789,1713],[1814,1765],[1831,1821],[1846,1846]])
    return PchipInterpolator(key[:,0],key[:,1])(f)
def retime():
    # Keep the settling dwell of the first inscription, then carry the pullback faster through orbital distance.
    # Interpolate the narrow fraction between adjacent source pictures by following their image motion.
    o=source(V4,1543,1846-1543+2);a=next(o);b=next(o);i=1543
    yc,xc=np.mgrid[:540,:960].astype('f');est=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
    for src in clock(np.arange(1682,1847)):
        k=int(np.floor(src+.000001));q=float(np.clip(src-k,0,1))
        while i<k:a,b=b,next(o);i+=1
        if q<.015:yield a;continue
        if q>.985:yield b;continue
        l,r=[cv2.resize(cv2.cvtColor(v,cv2.COLOR_RGB2GRAY),(320,180)) for v in [a,b]]
        flow=cv2.resize(est.calc(l,r,None),(960,540))*3
        aw=cv2.remap(a,xc-q*flow[...,0],yc-q*flow[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        bw=cv2.remap(b,xc+(1-q)*flow[...,0],yc+(1-q)*flow[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        yield cv2.addWeighted(aw,1-q,bw,q,0)
    o.close()
    yield from source(V4,1847,1927-1847+1)
def pictures(name,lo,hi):
    if name in ('driver','tally','slide','coaster','night','walkout','oasis'):
        g=Grade(name)
        try:
            for f in range(lo,hi+1):
                if name=='coaster' and f in returned('ride'):
                    clean=shot('coaster-clean',f);rgb=over(g.apply(clean,f),rgba(returned('ride')[f]))
                else:rgb=g.apply(shot(name,f),f)
                if name=='slide' and f>=1669:
                    if f==1669:word=source(V4,1530,13)
                    rgb=match_slide(rgb,next(word),f)
                if name=='coaster' and f<=2307:
                    if f==2286:lift=Lift(g);page=picture(V4,2285)
                    rgb=lift.develop(rgb,page,f)
                if name=='coaster' and f>=2551:
                    # Transfer the falling lens onto the existing print once the rider has cleared it.
                    if f==2551:drop=source(V4,f,hi-f+1)
                    original=next(drop);q=float(smooth(2551,2564,f))
                    rgb=cv2.addWeighted(rgb,1-q,original,q,0)
                if name=='walkout' and f>=4440:
                    if f==4440:stars=source(V4,f,hi-f+1)
                    sky=next(stars);depth=cv2.resize(g.field[...,2],(960,540))
                    weight=(1-smooth(0,.0022,depth))*float(smooth(4440,4468,f))
                    rgb=np.uint8(np.clip(rgb+(sky.astype('f')-rgb)*weight[...,None],0,255))
                yield rgb
        finally:g.close()
    elif name=='montage':
        g=Grade(name);reveal=Reveal();old=source(V4,2227,2285-2227+1)
        try:
            for f in range(lo,hi+1):
                new=g.apply(shot(name,f),f) if f<2255 else None
                if f<=2226:yield new
                elif f<2255:yield reveal.match(new,next(old),f)
                else:yield reveal.ink(next(old),f)
        finally:g.close();old.close()
    elif name=='heel':
        for f,rgb in zip(range(lo,hi+1),source(V4,lo,hi-lo+1)):
            plate=rgba(D/f'heel/{f:04d}.png')
            # Leave the ring and all of the original contact shadow on their own photographed ground.
            plate=plate.copy();plate[...,3]=np.uint8(plate[...,3]*float(smooth(628,636,f))*.94)
            yield over(rgb,plate)
    elif name=='atlas':
        g=Grade('oasis')
        try:orbit=CampOrbit(g.apply(shot('oasis',3997),3997))
        finally:g.close()
        for f,im in zip(range(lo,hi+1),source(V4,lo,hi-lo+1)):yield orbit.step(im,f)
    elif name=='first-reveal':yield from retime()
    elif name in ('grain-entry','first-print'):
        for f,rgb in zip(range(lo,hi+1),source(V4,lo,hi-lo+1)):
            yield entry(rgb,f) if f<=1387 else quartz(rgb,f)
    elif name=='sneaker':
        for f in range(lo,hi+1):yield quartz(read(D/f'hero-shoe/{f:04d}.jpg'),f)
    elif name=='inner':
        path,index=interior();yield from source(path,index,690)
    elif name=='dive':
        grain=Grain();path,index=interior();inside=picture(path,index)
        for f,rgb in zip(range(lo,hi+1),source(V4,lo,hi-lo+1)):
            yield grain.mix(rgb,inside,f,True) if f>=2616 else rgb
    elif name=='wind':
        grain=Grain();path,index=interior();inside=picture(path,index+689)
        sys.path.insert(0,str(R/'src'));from walkwind.air import develop,camera_packets
        for f in range(lo,hi+1):
            folder='wind-stance' if 3390<=f<=3443 and (D/f'wind-stance/{f:04d}.jpg').is_file() else 'wind-pickup'
            p=D/('wind-thread' if 3569<=f<=3632 else folder)/f'{f:04d}.jpg'
            rgb=read(p if p.exists() else D/f'wind/{f:04d}.jpg')
            if f>=3346:
                # Rake the original single-exposure dune ripples to carry their
                # structure beneath the fast, low yarn camera.
                a=rgb.astype('f');r,green,b=a.transpose(2,0,1);lum=.23*r+.62*green+.15*b
                fine=lum-cv2.GaussianBlur(lum,(0,0),2.0)
                rake=cv2.GaussianBlur(lum,(0,0),1.1)-cv2.GaussianBlur(lum,(0,0),7.3)
                wet=smooth(12,28,lum)*(1-smooth(149,193,lum))*smooth(-5,12,b-r)
                wet*=smooth(3346,3372,f)*(1-smooth(3641,3655,f))
                detail=14*np.tanh((.68*fine+.94*rake)/14)*wet
                rgb=np.uint8(np.clip(a+detail[...,None],0,255)+.5)
            if f>=3328:
                # For the flight after the shoulder pass the unmodified red-thread camera matches the old plume projection.
                amt=float(smooth(3477,3506,f))*.93
                if amt:rgb=develop(rgb,camera_packets(f),amt)
            yield grain.mix(rgb,inside,f,False) if f<=3345 else rgb
    elif name in ('well','reflection'):
        water=Water()
        frames=source(V4,lo,hi-lo+1) if name=='reflection' else (read(D/f'well/{f:04d}.jpg') for f in range(lo,hi+1))
        for f,rgb in zip(range(lo,hi+1),frames):
            yield water.develop(rgb,f,dry(f) if 4880<=f<=4960 else None)
    else:yield from source(V4,lo,hi-lo+1)
def encode(name,lo,hi,force):
    path=E/(name+'.mp4');tmp=E/(name+'.partial.mp4')
    if not force and nframes(path)==hi-lo+1:return
    if name=='open':
        sys.path.insert(0,str(R/'src/rough2'));from locked_avc import source_hold
        source_hold(V4,lo,hi,tmp);tmp.replace(path);return
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','960x540','-r','30','-i','-','-an',
         '-vf','scale=out_color_matrix=bt709:out_range=tv,format=yuv420p','-c:v','libx264','-preset','fast','-crf','14','-bf','0','-g','60','-threads','3',
         '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-video_track_timescale','15360',str(tmp)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in pictures(name,lo,hi):p.stdin.write(frame.tobytes(order='C'))
        p.stdin.close()
        if p.wait() or nframes(tmp)!=hi-lo+1:raise RuntimeError(name)
        tmp.replace(path)
        if name=='inner':(E/'inner-source.txt').write_text(str(interior()[0])+'\n')
        if name in ('coaster','reflection'):
            slot='ride' if name=='coaster' else 'well'
            (E/(slot+'-source.txt')).write_text(('Studio RGBA' if returned(slot) else 'Blocking performance')+'\n')
        print('Conformed',name,lo,hi,flush=True)
    finally:
        if p.poll() is None:
            p.kill();p.wait()
        tmp.unlink(missing_ok=True)
def mux(target):
    dest=Path(target);tmp=dest.with_suffix('.partial.mp4');rows=[]
    for name,a,b in SECTIONS:
        p=E/(name+'.mp4')
        if nframes(p)!=b-a+1:raise ValueError((name,'count'))
        rows.extend([f"file '{p.resolve()}'",f'duration {(b-a+1)/30:.9f}'])
    file=E/'cut.ffconcat';file.write_text('ffconcat version 1.0\n'+'\n'.join(rows)+'\n')
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',file,'-i',MASTER,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','320k','-ar','48000','-t','187.600','-video_track_timescale','15360',
         '-bsf:v','setts=pts=PTS:dts=(N-2)*512:duration=512:time_base=1/15360',
         '-metadata',"title=It's Written",'-metadata','comment=Rain Rig © Blender Foundation | cloud.blender.org, modified. Milky Way panorama by ESO/S. Brunier.',
         '-movflags','+faststart',tmp])
    if nframes(tmp)!=5628:raise ValueError('Final frame count')
    fps=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate','-of','csv=p=0',str(tmp)]).strip()
    if fps!=b'30/1':raise ValueError(('Final constant frame rate',fps))
    tmp.replace(dest)
if __name__=='__main__':
    args=sys.argv[1:]
    if args[0]=='mux':mux(args[1]);sys.exit()
    for name,lo,hi in SECTIONS:
        if name in args or 'all' in args:encode(name,lo,hi,'--force' in args)
