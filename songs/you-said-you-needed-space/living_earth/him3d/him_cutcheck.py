"""him_cutcheck.py: render checks on the film ranges WITH him (the comp, not only his layer): streams, length, blank frames, and
one-frame pops (a frame that differs from both neighbours far more than they differ from each other). Slot starts are printed next
to anything found, so a designed cut is told from a fault. `--plant` blanks / shifts a frame of a scratch copy and must catch both.
  .venv/bin/python living_earth/him3d/him_cutcheck.py [--plant] <mp4> <first film frame> [...pairs]"""
import cv2, json, numpy as np, os, subprocess, sys
SONG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def slots():
    out = []
    for p in sorted(os.listdir(os.path.join(SONG, 'build/him_wire/tracks'))):
        d = json.load(open(os.path.join(SONG, 'build/him_wire/tracks', p)))
        out += [(a, s) for s, a, b in d.get('slotFrames', [])] + [(b + 1, 'after ' + s) for s, a, b in d.get('slotFrames', [])]
    return sorted(set(out))
def him_edges():
    """first and last film frame each clip of him is on screen (16:9 manifest entries of the staging manifest)"""
    out = []; md = os.path.join(SONG, 'build/him_wire/manifest')
    for p in sorted(os.listdir(md)):
        if not p.endswith('_169.json'): continue
        m = json.load(open(os.path.join(md, p))); fs = sorted(int(k) for k, v in m['frames'].items() if v[4] >= 50)
        if fs: out.append((m['run'], fs[0], fs[-1]))
    return out
def cut_align(cuts):
    """he may only arrive ON a cut or leave ON a cut: a first / last frame of his within 3 frames of a cut but not on it is a one-frame fault"""
    bad = []; flash = [c for c in cuts if c + 1 in cuts]      # two big changes in a row: a one-frame picture right before the real cut (reported, it is the plate's)
    for c in flash: bad.append((c, 'flash', f'the whole picture changes at {c} and again at {c + 1}: one odd frame before the cut (the plate, not him: look)', ''))
    for c in [c for c in cuts if c not in flash]:
        for run, a, b in him_edges():
            if 0 < abs(a - c) <= 3: bad.append((a, 'cut-align', f'{run}: he arrives at {a}, the cut is at {c}', ''))
            if 0 < abs(b + 1 - c) <= 3: bad.append((b, 'cut-align', f'{run}: his last frame is {b}, the cut is at {c}', ''))
    return bad
def read(mp4, mutate=None):
    cap = cv2.VideoCapture(mp4); fr = []
    while True:
        ok, im = cap.read()
        if not ok: break
        fr.append(cv2.resize(im, (640, int(im.shape[0] * 640 / im.shape[1])), interpolation=cv2.INTER_AREA).astype(np.int16))
    if mutate: mutate(fr)
    return fr
def scan(fr, first):
    found = []; S = slots(); near = lambda f: next((f'{s} starts {a}' for a, s in S if abs(a - f) <= 1), '')
    d = [0.0] + [float(np.abs(fr[i] - fr[i - 1]).mean()) for i in range(1, len(fr))]
    for i, im in enumerate(fr):
        if im.mean() < 1.5: found.append((first + i, 'blank', f'mean {im.mean():.2f}', near(first + i)))
    for i in range(1, len(fr) - 1):
        skip = float(np.abs(fr[i + 1] - fr[i - 1]).mean())
        if d[i] > 2.5 and d[i + 1] > 2.5 and min(d[i], d[i + 1]) > 3.0 * skip + 0.6: found.append((first + i, 'pop', f'{d[i]:.1f} in, {d[i + 1]:.1f} out, neighbours apart {skip:.1f}', near(first + i)))
    cuts = [(first + i, f'{d[i]:.1f}', near(first + i)) for i in range(1, len(fr)) if d[i] > 9 and (i < 2 or d[i] > 4 * (d[i - 1] + 0.3))]
    return found, cuts
if __name__ == '__main__':
    args = sys.argv[1:]; planting = '--plant' in args; args = [a for a in args if a != '--plant']; bad = 0
    if not args: print('no clips given'); sys.exit(2)
    for mp4, first in zip(args[0::2], args[1::2]):
        first = int(first)
        if not os.path.exists(mp4): print(f'[cutcheck] {mp4}: MISSING'); bad += 1; continue
        pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', mp4], capture_output=True, text=True).stdout)['streams']
        v = next(s for s in pr if s['codec_type'] == 'video'); has_a = any(s['codec_type'] == 'audio' for s in pr)
        if planting:
            def mut(fr): fr[20][:] = 0; fr[40][:] = np.roll(fr[40], 60, axis=1)
            found, _ = scan(read(mp4, mut), first); kinds = {(f, k) for f, k, _, _ in found}; ok = (first + 20, 'blank') in kinds and (first + 40, 'pop') in kinds
            ed = him_edges(); fake = cut_align([ed[0][1] + 1]) if ed else []; ok = ok and (not ed or any(k == 'cut-align' for _, k, _, _ in fake))   # a cut one frame after he arrives must be caught
            print(f'[plant] {os.path.basename(mp4)}: blanked {first + 20}, shifted {first + 40} -> ' + ('both caught' if ok else f'NOT CAUGHT, got {sorted(kinds)}')); bad += 0 if ok else 1; continue
        fr = read(mp4); found, cuts = scan(fr, first); found += cut_align([c for c, _, _ in cuts])
        print(f"[cutcheck] {os.path.basename(mp4)}: {v['width']}x{v['height']} {v.get('pix_fmt')} {v.get('color_space', '?')} frames {len(fr)} audio {'yes' if has_a else 'NO'} -> " + ('PASS' if not found and has_a else f'LOOK {len(found)}'))
        for f, k, why, nr in found: print(f'    {k} at {f}: {why} {("[" + nr + "]") if nr else ""}')
        print('    cuts seen: ' + ', '.join(f'{f}{(" (" + nr + ")") if nr else " (?)"}' for f, _, nr in cuts) if cuts else '    cuts seen: none')
        bad += 1 if (found or not has_a) else 0
    sys.exit(1 if bad else 0)
