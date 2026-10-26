"""Render the film (or a range) to H.264 with the clean audio, in resumable chunks.
  python3 render.py START END out.mp4 [--w 2560] [--workers 2] [--crf 16] [--chunk 150]
Each chunk (default 150 frames = 5 s) is its own file in out.mp4.parts/ and is skipped if it already exists, so a
render can be stopped and resumed. Chunks are concatenated losslessly and muxed with the audio at the end."""
import os, sys, subprocess, argparse, time, multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
_F = {}


def work(args):
    f0, f1, W, H, crf, preset, path = args[:7]; hook = args[7] if len(args) > 7 else None
    if os.path.exists(path): return path
    sys.path.insert(0, HERE)
    import cv2
    cv2.setNumThreads(1)
    if 'F' not in _F:
        from allow.film import Film
        _F['F'] = Film(W, H, hook=hook)
    F = _F['F']
    tmp = path + '.tmp.mp4'
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p', '-profile:v', 'high',
           '-x264-params', 'keyint=60:min-keyint=60:scenecut=0:threads=2:rc-lookahead=20',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(f0, f1):
        p.stdin.write(F.frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()
    os.replace(tmp, path)
    print(f'chunk {f0}-{f1} done in {time.time() - t0:.0f}s', flush=True)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('start', type=float); ap.add_argument('end', type=float); ap.add_argument('out')
    ap.add_argument('--w', type=int, default=2560); ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--crf', type=int, default=16); ap.add_argument('--preset', default='medium')
    ap.add_argument('--chunk', type=int, default=150); ap.add_argument('--no-mux', action='store_true')
    ap.add_argument('--h', type=int, default=None, help='height (default 16:9 of --w)')
    ap.add_argument('--hook', default=None, help='on-screen hook text for the first 3 s (vertical clips)')
    a = ap.parse_args()
    W = a.w; H = a.h or W * 9 // 16
    hook = (a.hook, a.start, a.start + 3.0) if a.hook else None
    f0, f1 = int(round(a.start * FPS)), int(round(a.end * FPS))
    tmp = a.out + '.parts'; os.makedirs(tmp, exist_ok=True)
    jobs = [(c, min(f1, c + a.chunk), W, H, a.crf, a.preset, os.path.join(tmp, f'c{c:06d}.mp4'), hook) for c in range(f0, f1, a.chunk)]
    todo = [j for j in jobs if not os.path.exists(j[6])]
    print(f'{len(jobs)} chunks, {len(todo)} to render', flush=True)
    t0 = time.time()
    if todo:
        with mp.get_context('spawn').Pool(a.workers, maxtasksperchild=6) as pool:
            for k, _ in enumerate(pool.imap(work, todo)):
                el = time.time() - t0
                print(f'[{k + 1}/{len(todo)}] {el / 60:.1f} min, ~{el / (k + 1) * (len(todo) - k - 1) / 60:.0f} min left', flush=True)
    if a.no_mux: return
    lst = os.path.join(tmp, 'list.txt')
    open(lst, 'w').write(''.join(f"file '{os.path.abspath(j[6])}'\n" for j in jobs))
    dur = (f1 - f0) / FPS
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-ss', f'{f0 / FPS:.3f}', '-t', f'{dur:.3f}', '-i', os.path.join(HERE, 'audio_clean.wav'),
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-af', 'apad',
                    '-shortest', '-movflags', '+faststart', a.out], check=True)
    print(f'done {a.out} in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
