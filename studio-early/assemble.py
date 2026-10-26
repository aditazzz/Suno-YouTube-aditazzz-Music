"""usage: assemble.py projdir audio.wav END "Song Title" clips.json"""
import sys, os, json, subprocess, glob
P, wav, END, title, clips = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], json.loads(sys.argv[5])
os.makedirs(f'{P}/out', exist_ok=True)
def run(cmd): subprocess.run(cmd, check=True)
run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-af', f'apad=whole_dur={END}', '-t', str(END), '-c:a', 'pcm_s16le', f'{P}/audio_pad.wav'])
for mode, name in (('range', f'{title} - YouTube 16x9'), ('vrange', f'{title} - Instagram 9x16 full')):
    parts = sorted(glob.glob(f'{P}/chunks/{mode}_*.mp4'))
    parts = [p for p in parts if not p.endswith('.tmp.mp4')]
    with open(f'{P}/{mode}_list.txt', 'w') as f:
        f.write(''.join(f"file '{p}'\n" for p in parts))
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{P}/{mode}_list.txt', '-c', 'copy', f'{P}/{mode}_noaudio.mp4'])
    run(['ffmpeg', '-v', 'error', '-y', '-i', f'{P}/{mode}_noaudio.mp4', '-i', f'{P}/audio_pad.wav', '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-movflags', '+faststart', '-shortest', f'{P}/out/{name}.mp4'])
for name, a, b in clips:
    d = round(b - a, 3)
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a), '-t', str(d), '-i', f'{P}/vrange_noaudio.mp4', '-ss', str(a), '-t', str(d),
         '-i', f'{P}/audio_pad.wav', '-map', '0:v', '-map', '1:a',
         '-vf', f'fade=t=in:st=0:d=0.25,fade=t=out:st={d - 0.6}:d=0.6',
         '-af', f'afade=t=in:st=0:d=0.2,afade=t=out:st={d - 1.2}:d=1.2',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
         '-movflags', '+faststart', f'{P}/out/{title} - {name}.mp4'])
for f in sorted(glob.glob(f'{P}/out/*.mp4')):
    dur = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip()
    print(f'{os.path.getsize(f) / 1e6:7.1f} MB  {dur:>10}s  {os.path.basename(f)}')
