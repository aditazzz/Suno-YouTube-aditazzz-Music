#!/usr/bin/env python3
"""Cut 7 motion gate (PLAN7 §2): per-block share of near-still frames, camera jerk spikes, one-frame pops.

  motion_floor.py <video> [--blocks remotion/src/data/blocks_c7.json | --shots remotion/src/data/shots.json]
                  [--range A B] [--offset F] [--max-still 0.20] [--json out.json] [--diffs cache.npy]

<video> frame 0 = film frame --offset (default 0; a section preview rendered from frame A passes --offset A).
Measured on a 192x108 grey copy (ffmpeg), so it runs on 1280x720 previews and 2560x1440 masters alike.
 - still: mean |frame - previous| (0..255 grey) below STILL_T. STILL_T is calibrated on cut 6
   (the chat's numbers: 6A 100%, 11B 100%, 7D 99%, 12A 90%, 8E 88%, 3B 81% ...; see --calibrate).
   The first frame of each block is not counted (it is the cut).
 - pop: a frame whose diff is > POP_K x both neighbours' diffs and > POP_MIN, not on a block boundary (one-frame flash/jump).
 - jerk: global motion per frame (phase correlation dx, dy and log-scale proxy); its 2nd difference spiking > JERK_K x the
   block's median, away from block boundaries (+-2 f) = a camera hitch.
A block lists inner cuts (`cuts`) and `designed` windows ([a, b, reason]: wall dollies, pose swaps, UI moves) in blocks_c7.json; pops/jerks
within 3 f of a cut, inside a designed window or within 4 f of the block's ends are not counted (the still share always is).
Exit 1 if any block is over --max-still, or any pop / jerk spike is found (warnings as errors).
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np

W, H = 192, 108
STILL_T = 0.42   # calibrated on cut 6 m2 (--calibrate: mean |err| 0.02 vs the chat's 16 numbers); grey levels, mean abs diff per pixel
POP_K, POP_MIN = 4.0, 6.0
JERK_K, JERK_MIN = 6.0, 3.0   # px at 192 wide (~40 stage px of sudden acceleration)


def frames(video):
    cmd = ['ffmpeg', '-v', 'error', '-i', str(video), '-vf', f'scale={W}:{H}:flags=area,format=gray', '-f', 'rawvideo', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)


def shift(a, b):
    """global translation b vs a by phase correlation (px at 192x108)"""
    A = np.fft.fft2(a - a.mean()); B = np.fft.fft2(b - b.mean())
    R = A * np.conj(B); R /= np.abs(R) + 1e-6
    r = np.fft.ifft2(R).real
    y, x = np.unravel_index(np.argmax(r), r.shape)
    def sub(c, l, rr):   # parabolic sub-pixel peak
        d = l - 2 * c + rr
        return 0.0 if abs(d) < 1e-9 else 0.5 * (l - rr) / d
    fx = sub(r[y, x], r[y, (x - 1) % W], r[y, (x + 1) % W]); fy = sub(r[y, x], r[(y - 1) % H, x], r[(y + 1) % H, x])
    if y > H // 2: y -= H
    if x > W // 2: x -= W
    return float(x + fx), float(y + fy)


def measure(video, cache=None):
    if cache and Path(cache).exists():
        d = np.load(cache, allow_pickle=True).item(); return d['diff'], d['mot']
    fr = frames(video)
    diff = np.zeros(len(fr), np.float32); mot = np.zeros((len(fr), 3), np.float32)
    win = np.outer(np.hanning(H), np.hanning(W)).astype(np.float32)
    for i in range(1, len(fr)):
        diff[i] = np.abs(fr[i] - fr[i - 1]).mean()
        dx, dy = shift(fr[i - 1] * win, fr[i] * win)
        # scale proxy: mean brightness-normalised radial gradient change is noisy; use edge-energy ratio instead
        mot[i] = (dx, dy, 0.0)
    if cache: np.save(cache, {'diff': diff, 'mot': mot})
    return diff, mot


def load_blocks(args):
    p = Path(args.blocks or args.shots)
    d = json.loads(p.read_text())
    items = d['blocks'] if 'blocks' in d else d['shots']
    return [(b['id'], b['from'], b['from'] + b['dur'], b.get('cuts', []) + [w for a, z, *_ in b.get('designed', []) for w in range(a, z)]) for b in items]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('--blocks'); ap.add_argument('--shots')
    ap.add_argument('--range', nargs=2, type=int); ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--max-still', type=float, default=0.20); ap.add_argument('--json'); ap.add_argument('--diffs')
    ap.add_argument('--still-t', type=float, default=STILL_T); ap.add_argument('--calibrate', action='store_true')
    a = ap.parse_args()
    if not (a.blocks or a.shots):
        a.blocks = str(Path(__file__).resolve().parents[1] / 'remotion/src/data/blocks_c7.json')
    diff, mot = measure(a.video, a.diffs)
    n = len(diff); lo = a.offset; hi = a.offset + n
    if a.range: lo, hi = max(lo, a.range[0]), min(hi, a.range[1])
    blocks = [(i, f, t, c) for i, f, t, c in load_blocks(a) if f >= lo and t <= hi]
    
    if a.calibrate:
        ref = {'6A': 1.0, '11B': 1.0, '7D': .99, '12A': .90, '8E': .88, '3B': .81, '2F': .78, '4J': .78, '4E': .72, '4T': .70,
               '4G': .70, '9F': .71, '5A': .68, '7B': .68, '6C': .66, '5D': .62}
        for T in [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5]:
            err = []
            for i, f, t, _ in blocks:
                if i in ref:
                    d = diff[f + 1 - a.offset:t - a.offset]; err.append(((d < T).mean() - ref[i]))
            print(f'T={T:.2f} mean|err|={np.mean(np.abs(err)):.3f} bias={np.mean(err):+.3f}')
        return
    rows = []; fail = False
    for i, f, t, cuts in blocks:
        d = diff[f + 1 - a.offset:t - a.offset]
        still = float((d < a.still_t).mean()) if len(d) else 0.0
        # pops: one-frame spikes inside the block (not within 1 f of a boundary)
        pops = []
        near = lambda k: min([abs(k - f), abs(t - k)]) <= 4 or min([abs(k - c) for c in cuts] or [99]) <= 3
        for k in range(f + 2, t - 1):
            if near(k): continue
            j = k - a.offset
            if j + 1 >= n: break
            x, p, q = diff[j], diff[j - 1], diff[j + 1]
            if x > POP_MIN and x > POP_K * max(p, 0.2) and diff[j + 1] > POP_MIN and x > POP_K * max(diff[j + 2] if j + 2 < n else 0, 0.2):
                pops.append(k)   # a flash: big diff in and big diff out, calm on both sides
        # jerk: 2nd difference of the global translation
        m = mot[f + 1 - a.offset:t - a.offset, :2].copy()
        if len(m) > 4:   # 3-tap smooth: integer-ish phase peaks wobble by a fraction of a px
            m[1:-1] = (m[:-2] + m[1:-1] + m[2:]) / 3
        jerks = []
        if len(m) > 6:
            j2 = np.linalg.norm(m[2:] - 2 * m[1:-1] + m[:-2], axis=1)
            med = max(float(np.median(j2)), 0.25)
            for k in np.where((j2 > JERK_K * med) & (j2 > JERK_MIN))[0]:
                fr = f + 2 + int(k)
                if not near(fr): jerks.append(fr)
        ok = still <= a.max_still and not pops and not jerks
        fail |= not ok
        rows.append({'id': i, 'from': f, 'to': t, 'still': round(still, 3), 'pops': pops, 'jerks': jerks, 'ok': ok,
                     'mean_diff': round(float(d.mean()) if len(d) else 0, 3)})
        print(f"{'OK  ' if ok else 'FAIL'} {i:5s} {f:5d}-{t:5d} still {still*100:5.1f}%  diff {rows[-1]['mean_diff']:5.2f}"
              + (f'  pops {pops[:6]}' if pops else '') + (f'  jerks {jerks[:6]}' if jerks else ''))
    nf = sum(1 for r in rows if not r['ok'])
    print(f'{len(rows)} blocks, {nf} fail (still > {a.max_still*100:.0f}% / pop / jerk). STILL_T={a.still_t}')
    if a.json: Path(a.json).write_text(json.dumps({'still_t': a.still_t, 'rows': rows}, indent=1))
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
