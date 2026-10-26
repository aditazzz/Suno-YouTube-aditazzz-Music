#!/usr/bin/env python3
"""Cut a video from a JPEG frame sequence (f_%05d.jpg at 30 fps, frame n = time n/30) plus the clean song audio.

  AUDIO=song.wav python3 cut.py FRAMES_DIR OUT.mp4 W H SEGMENTS [--bv MBPS] [--fadein S] [--fadeout S] [--hold S]

SEGMENTS: "t0-t1,t0-t1,..." in song seconds. Joins between segments get a short equal-power audio crossfade centred
on the cut (so picture and sound stay in sync); the picture cuts hard. --hold freezes the last frame for S seconds
while the audio runs on (for a word that ends just after a shot change). Audio fades in/out at the very ends.
"""
import argparse, os, subprocess, sys, tempfile

AUDIO = os.environ.get('AUDIO', '')   # the song (not in this repo): AUDIO=path/to/song.wav python3 cut.py ...
FPS = 30
XF = 0.03   # crossfade at joins (s)

ap = argparse.ArgumentParser()
ap.add_argument('frames'); ap.add_argument('out'); ap.add_argument('W', type=int); ap.add_argument('H', type=int); ap.add_argument('segs')
ap.add_argument('--bv', type=float, default=8); ap.add_argument('--fadein', type=float, default=0.0); ap.add_argument('--fadeout', type=float, default=0.0)
ap.add_argument('--hold', type=float, default=0.0); ap.add_argument('--preset', default='slow'); ap.add_argument('--sharpen', type=float, default=0.3)
ap.add_argument('--xf', default='', help='crossfade per join in seconds, comma-separated (default 0.03 each)')
a = ap.parse_args(); a.frames = os.path.abspath(a.frames)

segs = [tuple(round(float(x) * FPS) / FPS for x in s.split('-')) for s in a.segs.split(',')]   # snapped to frames, so sound and picture cut together
# frames: segment [t0, t1) -> frames round(t0*30) .. round(t1*30)-1
frames = []
for t0, t1 in segs:
    n0, n1 = round(t0 * FPS), round(t1 * FPS)
    frames += list(range(n0, n1))
hold_n = round(a.hold * FPS)
frames += [frames[-1]] * hold_n
miss = [n for n in set(frames) if not os.path.exists(os.path.join(a.frames, f'f_{n:05d}.jpg'))]
if miss: print('MISSING', len(miss), 'frames, first', sorted(miss)[:8]); sys.exit(1)
dur = len(frames) / FPS

if not os.path.exists(AUDIO): sys.exit('set AUDIO to the song file')
tmp = tempfile.mkdtemp(prefix='cut_')
lst = os.path.join(tmp, 'frames.txt')
with open(lst, 'w') as f:
    f.write('ffconcat version 1.0\n')
    for n in frames: f.write(f"file '{os.path.join(a.frames, f'f_{n:05d}.jpg')}'\nduration {1 / FPS:.6f}\n")
    f.write(f"file '{os.path.join(a.frames, f'f_{frames[-1]:05d}.jpg')}'\n")   # concat demuxer needs the last file repeated

XFS = [float(x) for x in a.xf.split(',')] if a.xf else [XF] * (len(segs) - 1)
# audio: each segment widened by half its crossfade at inner joins, then crossfaded; the hold extends the last segment
ain = []; fc = [f'[1:a]asplit={len(segs)}' + ''.join(f'[r{i}]' for i in range(len(segs))) if len(segs) > 1 else '[1:a]anull[r0]']
for i, (t0, t1) in enumerate(segs):
    s0 = t0 - (XFS[i - 1] / 2 if i > 0 else 0); s1 = t1 + (XFS[i] / 2 if i < len(segs) - 1 else 0) + (a.hold if i == len(segs) - 1 else 0)
    fc.append(f'[r{i}]atrim=start={s0:.4f}:end={s1:.4f},asetpts=PTS-STARTPTS[s{i}]')
cur = 's0'
for i in range(1, len(segs)):
    fc.append(f'[{cur}][s{i}]acrossfade=d={XFS[i - 1]}:c1=qsin:c2=qsin[x{i}]'); cur = f'x{i}'
post = []
if a.fadein > 0: post.append(f'afade=t=in:st=0:d={a.fadein}')
if a.fadeout > 0: post.append(f'afade=t=out:st={max(0, dur - a.fadeout):.4f}:d={a.fadeout}')
fc.append(f'[{cur}]' + (','.join(post) if post else 'anull') + f',atrim=end={dur:.4f}[aout]')
fc.append(f'[0:v]scale={a.W}:{a.H}:flags=lanczos' + (f',unsharp=3:3:{a.sharpen}:3:3:0' if a.sharpen > 0 else '') + ',format=yuv420p[vout]')
bv = a.bv
cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-i', AUDIO,
       '-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]', '-r', str(FPS),
       '-c:v', 'libx264', '-preset', a.preset, '-b:v', f'{bv}M', '-maxrate', f'{bv * 1.5}M', '-bufsize', f'{bv * 2}M',
       '-pix_fmt', 'yuv420p', '-frames:v', str(len(frames)), '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', '-t', f'{dur:.4f}', a.out]
r = subprocess.run(cmd)
if r.returncode: sys.exit(r.returncode)
p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=codec_type,width,height,nb_frames,duration', '-of', 'compact', a.out], capture_output=True, text=True)
print(p.stdout.strip()); print('frames', len(frames), 'dur', round(dur, 3))
