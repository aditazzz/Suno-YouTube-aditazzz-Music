"""Supervise the serial return, keeping decoded and verified edit sections on disk."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import sys
import time

import numpy as np
from film import ROOT,OUT,WORK,GUIDE,EDL,ORDER,SECTIONS,SAMPLES,MASTER,CREDITS,jungle,REVISED_SURVEYS,FINISH_SURVEY
from picture import levels,read_hero_return
from section import handles
from inputs import requirements,stagefile

LOG=OUT/'FINISH_LOG.md'
G=10**9
class Stop(RuntimeError):pass

def log(msg):
    stamp=time.strftime('%Y-%m-%d %H:%M:%S %Z')
    line=f'{stamp}  {msg}'
    with LOG.open('a') as out:out.write(line+'\n')
    print(line,flush=True)

def sha(path):
    with path.open('rb') as file:return hashlib.file_digest(file,'sha256').hexdigest()

def usage():
    def blocks(path):
        try:st=path.stat()
        except FileNotFoundError:return 0  # A worker has just renamed its atomic frame.
        return max(st.st_size,st.st_blocks*512)
    own=sum(blocks(Path(root)/f) for root,_,files in os.walk(WORK) for f in files)
    own+=sum(blocks(p) for p in OUT.glob('its-written_final_1080*.mp4'))
    own+=blocks(LOG)+blocks(OUT/'FINISH_DONE.txt')
    return own,shutil.disk_usage(WORK).free

def guard():
    used,free=usage()
    # Reserve one native render buffer and mux write burst between checks.
    if free<4.16*G:raise Stop(f'{free/G:.2f} GB free, reached 4 GB disk reserve')
    if used>7.84*G:raise Stop(f'{used/G:.2f} GB in finish files, reached 8 GB footprint reserve')
    if os.environ.get('FINISH_TEST_DEADLINE') and time.time()>=int(os.environ['FINISH_TEST_DEADLINE']):raise Stop('CPU proof deadline reached')
    return used,free

def signal_group(pgid,sig):
    # A process group in the middle of exiting can briefly return EPERM on
    # macOS. A probe still means "present"; real signals retry the transition.
    for attempt in range(5):
        try:
            os.killpg(pgid,sig)
            return True
        except ProcessLookupError:return False
        except PermissionError:
            if sig==0:return True
            if attempt==4:raise
            time.sleep(.06)

def monitored(command,env=None):
    guard()
    proc=subprocess.Popen(list(map(str,command)),start_new_session=True,env=env)
    finished=False
    try:
        while True:
            try:rc=proc.wait(timeout=.8)
            except subprocess.TimeoutExpired:
                guard();continue
            if rc:raise Stop(f'{Path(str(command[0])).name} exited {rc}')
            guard();finished=True;break
    finally:
        if not finished:
            # The section can die before one of its workers. Signal its isolated
            # process group even if the leader has already returned a status.
            try:
                if signal_group(proc.pid,signal.SIGTERM):
                    until=time.monotonic()+3
                    while time.monotonic()<until:
                        proc.poll()
                        if not signal_group(proc.pid,0):break
                        time.sleep(.06)
                    signal_group(proc.pid,signal.SIGKILL)
            finally:proc.wait()

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)],timeout=30))['streams']

def check(path,w,n,sound=False):
    streams=probe(path);v=streams[0]
    tags=('codec_name','profile','pix_fmt','avg_frame_rate','r_frame_rate','color_transfer','color_space','color_primaries','color_range')
    values=('h264','High','yuv420p','30/1','30/1','bt709','bt709','bt709','tv')
    if tuple(v.get(k) for k in tags)!=values or (v['width'],v['height'],int(v.get('nb_frames',0)))!=(w,w*9//16,n):
        raise ValueError(f'{path.name} stream shape, colour or clock')
    if abs(float(v['start_time']))>1e-6 or abs(float(v['duration'])-n/30)>.00001:raise ValueError('Video timestamps')
    if len(streams)!=1+int(sound):raise ValueError('Unexpected media stream')
    if sound:
        a=streams[1]
        if (a['codec_name'],a['channels'],a['sample_rate'])!=('aac',2,'48000') or abs(float(a['start_time']))>1e-6 or abs(float(a['duration'])-n/30)>.001:raise ValueError('Stereo master timing')
    # -xerror makes corrupt slices fatal. Read every decoded image, including the dark well.
    result=subprocess.check_output(['ffmpeg','-v','error','-xerror','-i',str(path),'-map','0:v','-vf','scale=96:54:flags=area,format=gray','-fps_mode','passthrough','-f','rawvideo','-'])
    images=np.frombuffer(result,'u1').reshape(-1,54*96)
    if len(images)!=n:raise ValueError('Decoded frame count')
    bad=np.flatnonzero((images.max(1)<6)|(images.mean(1)<.55))
    if len(bad):raise ValueError(f'{path.name} black frame at {bad[0]}')
    if sound:
        stamps=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','packet=pts','-of','csv=p=0',str(path)])
        pts=np.fromstring(stamps.decode(),sep='\n',dtype='i8')
        if not np.array_equal(pts,np.arange(n)*512):raise ValueError('Non-contiguous picture timestamps')
        verify_audio(path,n)
        if not front_index(path):raise ValueError('MP4 movie index is after the picture payload')

def front_index(path):
    with path.open('rb') as file:
        total=path.stat().st_size
        while file.tell()+8<=total:
            start=file.tell();length,kind=struct.unpack('>I4s',file.read(8))
            if length==1:length=struct.unpack('>Q',file.read(8))[0]
            if kind==b'moov':return True
            if kind==b'mdat' or length<8 or start+length>total:return False
            file.seek(start+length)
    return False

def verify_audio(path,n):
    # Compare both decoded channels to the release WAV at identical sample offsets.
    from scipy.signal import correlate
    for t in ([.1] if n<100 else [3.1,82.7,181.9]):
        def window(src):
            out=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(src),'-map','0:a:0','-t','0.45','-ac','2','-ar','48000','-f','f32le','-'])
            return np.frombuffer(out,'<f4').reshape(-1,2)
        a,b=window(MASTER),window(path)
        if a.shape!=b.shape:raise ValueError('Audio sample count')
        for i in range(2):
            x,y=a[:,i],b[:,i]
            if np.max(np.abs(x))<1e-6:continue
            lag=np.argmax(correlate(y,x,mode='full',method='fft'))-len(x)+1
            if lag!=0 or np.corrcoef(x,y)[0,1]<.94:raise ValueError(f'Audio at {t}s channel {i+1}, lag {lag}')

def preflight():
    # Fail before starting the first camera if a studio slot or native stage is incomplete.
    required=[MASTER,GUIDE,ROOT/'work/rough2/hero-render',ROOT/'work/story/hero-print',
              ROOT/'work/rough/optical.dylib',ROOT/'work/rough2/optical.dylib',
              ROOT/'work/story/registration.dylib',ROOT/'work/story/ground.dylib']
    required.extend([ROOT/'work/rough2/hero-scene.dylib',*(FINISH_SURVEY/(n+'.npz') for n in (*REVISED_SURVEYS,'slide-rail','night-rail','letter-drawings','gate-path'))])
    native_assets=required[2:].copy()
    portraits=[]
    for slot,role,first,last in [('ride_front','ride',2417,2476),('well_look_up','well',4880,4960)]:
        portraits.extend(ROOT.parent/'hero/out'/slot/f'{role}_{f:04d}.exr' for f in range(first,last+1))
    required.extend(portraits)
    missing=[str(p) for p in required if not p.is_file() or not p.stat().st_size]
    if missing:raise Stop(f'Missing source {missing[0]} ({len(missing)} unavailable)')
    for path in portraits:
        read_hero_return(path)
    audio=probe(MASTER)[0]
    if (audio.get('codec_name'),audio.get('sample_rate'),audio.get('channels'),audio.get('duration_ts'))!=('pcm_s24le','48000',2,5628*1600):
        raise Stop('Expected the 24-bit 48 kHz stereo release WAV, 9,004,800 samples per channel')
    return native_assets

def section_key(code,name,mode,inner):
    sources=[GUIDE]
    if name in ('inner','wind','dive'):sources.append(inner)
    if name=='coaster':sources+=sorted((ROOT.parent/'hero/out/ride_front').glob('ride_*.exr'))
    if name=='reflection':sources+=sorted((ROOT.parent/'hero/out/well_look_up').glob('well_*.exr'))
    return hashlib.sha256((code+mode+name+repr([(str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in sources])).encode()).hexdigest()

def atomic_text(p,data):
    tmp=p.with_suffix(p.suffix+'.pending');tmp.write_text(data);tmp.replace(p)

def cleanup(folder,jobs):
    # Derive exact filenames from this section's dependency list, including its handles.
    if not folder.exists() or folder.is_symlink() or folder.parent.is_symlink():return
    if folder.resolve().parent.parent!=(WORK/'scratch').resolve():raise ValueError(folder)
    for stage,frames in jobs.items():
        d=folder/stage
        if not d.is_dir() or d.is_symlink():continue
        if stage in ('dune','boot'):
            files=[d/f'plate{f:04d}.cp' for f in frames]+[d/'framebuffer.exr']
        else:
            files=[stagefile(folder,stage,f) for f in frames]
            if stage in ('oasis','walkout'):
                files += [d/f'{f:04d}.cloth.png' for f in frames if f>=3728]
        if stage in ('grain','opening','walk','grove','wide-grove','owl'):
            files.append(d/'.cycles.png')
        if stage in ('grove','wide-grove'):
            files.append(d/('oasis-wide.bin' if stage=='wide-grove' else 'oasis-departure.bin'))
        for path in files:
            if not path.is_symlink() and path.is_file():path.unlink()

def ready(p,receipt,key,w,n):
    if not p.is_file():return False
    try:
        if receipt.is_file():
            try:row=json.loads(receipt.read_text())
            except ValueError:row={}
            if not isinstance(row,dict):row={}
            if row.get('source')==key:
                if sha(p)!=row.get('sha256'):return False
                check(p,w,n);return True
        # A power loss can occur after the verified MP4 was promoted but before
        # its JSON was promoted. Its embedded recipe identifies that exact take.
        blob=subprocess.check_output(['ffprobe','-v','error','-show_entries','format_tags=comment','-of','json',str(p)])
        tag=json.loads(blob).get('format',{}).get('tags',{}).get('comment')
        if tag=='finish-source '+key:
            check(p,w,n)
            atomic_text(receipt,json.dumps(dict(source=key,frames=n,sha256=sha(p))))
            return True
    except (ValueError,KeyError,subprocess.CalledProcessError):pass
    return False

def main(test):
    mode='test' if test else 'metal';w=480 if test else 1920
    folder=WORK/mode;folder.mkdir(exist_ok=True,parents=True)
    lock=(WORK/'queue.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError as exc:raise Stop('Another finish queue holds work/finish/queue.lock') from exc
    guard()
    native=preflight()
    inner=jungle()
    v=probe(inner)[0]
    if (v['width'],v['height'],int(v['nb_frames']),v['avg_frame_rate'])!=(1920,1080,690,'30/1'):raise ValueError(inner)
    cursor=0
    if len(ORDER)!=21 or len(EDL)!=21 or set(ORDER)!=set(EDL):raise ValueError('Edit section list')
    for name,first,last in SECTIONS:
        if first!=cursor or last<first:raise ValueError(f'Discontinuous edit at {name}')
        samples=SAMPLES[name]
        if len(samples)!=2 or not first<=samples[0]<samples[1]<=last:raise ValueError(f'Proof frames for {name}')
        cursor=last+1
    if cursor!=5628:raise ValueError('Edit must contain 5628 frames')
    log(f'{mode} | jungle {inner.name} | clean rebuild estimate {estimate():.1f} GPU hours at 11 s/24 spp; optics, checks and mux additional')
    meter=levels(GUIDE)
    if len(meter)!=5628:raise ValueError('v5 exposure count')
    np.save(WORK/'v5-meter.npy',meter)
    from section_recipes import section_signatures
    from finish_pickups import WINDOWS
    old,recipes=section_signatures()
    native_stamp=repr([(p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in native])
    for name in ORDER:
        a,b=EDL[name];n=2 if test else b-a+1
        p=folder/(name+'.mp4');tmp=folder/(name+'.pending.mp4')
        receipt=folder/(name+'.json');key=section_key(recipes[name]+native_stamp,name,mode,inner)
        scratch=WORK/'scratch'/mode/(name+'-'+key[:12])
        begin=time.monotonic()
        if ready(p,receipt,key,w,n):action='reused'
        else:
            scratch.mkdir(exist_ok=True,parents=True)
            diag=folder/(name+'.log');env=dict(os.environ,FINISH_SECTION_LOG=str(diag),FINISH_SOURCE_KEY=key)
            log(f'{mode} | start {name} {a}–{b}, {n} frames')
            command=[sys.executable,'src/finish/section.py',name,mode,scratch,tmp,inner]
            if not test and old and name in WINDOWS and WINDOWS[name]!=[(a,b)]:
                previous=section_key(old+native_stamp,name,mode,inner)
                if ready(p,receipt,previous,w,n):
                    command=[sys.executable,'src/finish/finish_pickups.py',name,mode,scratch,tmp,inner,p]
                    log(f'{mode} | {name} certified v1 source, native pickups {WINDOWS[name]}')
            try:monitored(command,env)
            except Stop as e:raise Stop(f'{name}: {e}; {diag.relative_to(ROOT)}') from e
            check(tmp,w,n);tmp.replace(p)
            atomic_text(receipt,json.dumps(dict(source=key,frames=n,sha256=sha(p))))
            action='verified'
        peak,free=guard()
        cleanup(scratch,requirements(handles(SAMPLES[name] if test else range(a,b+1))))
        log(f'{mode} | {name} {action} | {n} frames | {(time.monotonic()-begin)/60:.2f} minutes | {peak/G:.3f} GB before cleanup, {free/G:.2f} GB free')
    n=42 if test else 5628
    listing=folder/'film.ffconcat'
    atomic_text(listing,'ffconcat version 1.0\n'+''.join(f"file '{name}.mp4'\n" for name,_,_ in SECTIONS))
    dest=folder/'finish-test.mp4' if test else OUT/'its-written_final_1080.mp4'
    tmp=dest.with_suffix('.pending.mp4')
    # A stream-copy mux can write faster than the periodic monitor. The verified
    # container sizes bound the picture payload; reserve the full AAC track and index.
    upper=sum((folder/(name+'.mp4')).stat().st_size for name,_,_ in SECTIONS)+n*1600+4_000_000
    growth=max(0,upper-(tmp.stat().st_size if tmp.is_file() else 0))
    used,free=guard()
    if used+growth>7.84*G or free-growth<4.16*G:raise Stop(f'Mux needs {growth/G:.3f} GB within the 8 GB footprint and 4 GB free reserve')
    monitored(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',listing,'-i',MASTER,'-map','0:v:0','-map','1:a:0','-c:v','copy',
               '-bsf:v','setts=pts=N*512:dts=N*512:duration=512:time_base=1/15360','-video_track_timescale','15360',
               '-c:a','aac','-b:a','320k','-ar','48000','-af',f'atrim=end_sample={n*1600},asetpts=PTS-STARTPTS',
               '-metadata',"title=It’s Written",'-metadata','artist=Aditazzz','-metadata','comment='+CREDITS,'-movflags','+faststart',tmp])
    check(tmp,w,n,True);digest=sha(tmp);tmp.replace(dest)
    message=f'{time.strftime("%Y-%m-%d %H:%M:%S %Z")}\n{n} frames at 30 fps\nSHA-256 {digest}\nJungle {inner.name}\n'
    atomic_text(folder/'TEST_DONE.txt' if test else OUT/'FINISH_DONE.txt',message)
    log(f'{mode} | verified master {dest.relative_to(ROOT)}, {n} frames, SHA-256 {digest}')

def estimate():
    from film import SHOTS
    legacy=story=0
    for name,(a,b) in EDL.items():
        jobs=requirements(handles(range(a,b+1)))
        for stage,ids in jobs.items():
            if stage in SHOTS or stage=='coaster-clean':story+=len(ids)
            elif stage not in ('hero','macro','old-ink','original','turns','optics','atlas-plate'):legacy+=len(ids)
    return (story*32/24+legacy)*11/3600

if __name__=='__main__':
    def stop(signum,frame):raise Stop(f'interrupted by signal {signum}')
    for sig in [signal.SIGINT,signal.SIGTERM,signal.SIGHUP]:signal.signal(sig,stop)
    try:main(sys.argv[1:]==['--test'])
    except Exception as e:
        log('STOP '+str(e).replace('\n',' ')[:800]);raise
