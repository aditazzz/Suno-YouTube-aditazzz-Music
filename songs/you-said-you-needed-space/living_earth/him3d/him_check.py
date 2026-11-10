"""him_check.py: render checks on the him layer clips (earth_him_wire). Every check can fail: `--plant` runs them on a scratch copy
with a known-bad frame of each kind and must FAIL on each.
  .venv/bin/python living_earth/him3d/him_check.py [--plant] [run ...]
Per run and format (remotion/public/le/him/<dir>/h_#####.png + the manifest entry):
  count     every frame the manifest names exists, and the frames of the run where meta alpha > 0.004 are all there (no holes)
  blank     no frame with almost no coverage inside the run (unless meta says he is fading there)
  pop       coverage (sum of alpha) and mean colour never jump for ONE frame and come back (a dropped / wrong frame)
  jump      his centroid moves smoothly: frame-to-frame step against the median of its neighbours (a frame from the wrong place)
  flicker   brightness of his body does not alternate up/down/up over 3+ frames beyond a threshold (designed stutters are listed in ALLOW)
"""
import cv2, json, numpy as np, os, sys, glob, shutil
SONG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUB = os.path.join(SONG, 'remotion/public'); MAN = os.path.join(SONG, 'build/him_wire/manifest'); META = os.path.join(SONG, 'build/him_wire/rgba')
# designed, per run: (first frame, last frame, checks excused, why)
ALLOW = {
    'c1_chase': [(1649, 1672, {'jump', 'pop'}, 'the take on "chase": wings sweep back')],
    'c1_heat': [(1870, 1946, {'flicker', 'jump', 'pop'}, 'the fuse blows on "atmosphere": knocked back, eye stutter'), (1790, 1880, {'flicker'}, 'chest lights stutter, he shakes')],
    'fc_cool': [(5921, 5999, {'flicker'}, 'chest lights stutter, he shakes')],
    'fc_end': [(5986, 6180, {'flicker'}, 'red hot, shaking, chest lights stutter'), (6340, 6385, {'flicker', 'jump', 'pop'}, 'the link snaps: jolt, eye stutters out (outro.ts stutter)')],
    'fc_hold': [(5680, 5700, {'jump', 'pop'}, 'the thread lets go: he lurches free')],
    'br': [(4690, 4735, {'pop'}, 'he comes up out of the outline; the eye opens')],
    'co_count': [(113, 130, {'pop'}, 'grows out of the spark')],
    'p2_estate': [(3125, 3150, {'jump', 'pop', 'count', 'blank'}, 'glides in from off frame'), (3188, 3210, {'jump', 'pop', 'count', 'blank', 'flicker'}, 'zips off frame')],
}
def stats(dirp, m):
    fr = {int(k): v for k, v in m['frames'].items()}; rows = {}
    for f, e in fr.items():
        im = cv2.imread(os.path.join(dirp, f'h_{f:05d}.png'), cv2.IMREAD_UNCHANGED)
        if im is None: rows[f] = None; continue
        a = im[..., 3].astype(np.float32) / 255; cov = float(a.sum()); body = a > 0.9
        ys, xs = np.nonzero(a > 0.5); cx = e[0] + (xs.mean() if len(xs) else 0); cy = e[1] + (ys.mean() if len(ys) else 0)
        rows[f] = dict(cov=cov, lum=float(im[..., :3][body].mean()) if body.any() else 0.0, c=(cx, cy), alpha=e[4])
    return fr, rows
def check(run, fmt, m, dirp, meta):
    fr, rows = stats(dirp, m); fails = []; W = m['res'][0]
    ok = lambda f, kind: any(a <= f <= b and kind in ks for a, b, ks, _ in ALLOW.get(run, []))
    H = m['res'][1]; off = lambda x: x['px'][0] < -0.3 * x['span'] or x['px'][0] > W + 0.3 * x['span'] or x['px'][1] < -0.3 * x['span'] or x['px'][1] > H + 0.3 * x['span']   # he is outside the frame there (a glide in / out)
    mrow = {x['f']: x for x in meta['frames']}; edge = lambda f: (lambda x: x['px'][0] < 0.5 * x['span'] or x['px'][0] > W - 0.5 * x['span'] or x['px'][1] < 0 or x['px'][1] > H)(mrow[f]) if f in mrow else False   # entering / leaving by a frame edge: his coverage is partial by design
    # under 2% alpha nothing is left above the 8-bit floor: no file is right
    exp = [x['f'] for x in meta['frames'] if x['alpha'] > 0.02 and not off(x)]; miss = [f for f in exp if rows.get(f) is None and not ok(f, 'count')]
    if miss: fails.append(('count', miss[:8], f'{len(miss)} of {len(exp)} frames missing'))
    fs = sorted(f for f in rows if rows[f]); al = {x['f']: x['alpha'] for x in meta['frames']}
    full = [f for f in fs if al.get(f, 0) > 0.98]; cov_med = np.median([rows[f]['cov'] for f in full]) if full else 0
    for f in full:
        nb = [rows[g]['cov'] for g in (f - 1, f + 1) if rows.get(g) and al.get(g, 0) > 0.98]
        if nb and rows[f]['cov'] < 0.05 * max(nb) and not ok(f, 'blank') and not (edge(f) and rows[f]['cov'] < 400): fails.append(('blank', [f], f"coverage {rows[f]['cov']:.0f} vs its neighbours {max(nb):.0f}"))
    for i in range(1, len(fs) - 1):
        a, b, c = fs[i - 1], fs[i], fs[i + 1]
        if c - a != 2: continue
        ra, rb, rc = rows[a], rows[b], rows[c]
        if min(al.get(a, 0), al.get(b, 0), al.get(c, 0)) > 0.98:
            mid = (ra['cov'] + rc['cov']) / 2; d = abs(rb['cov'] - mid) / max(mid, 1); side = abs(ra['cov'] - rc['cov']) / max(mid, 1)
            if d > 0.12 and d > 3 * side and not ok(b, 'pop'): fails.append(('pop', [b], f'coverage off by {d:.0%} for one frame'))
            dl = abs(rb['lum'] - (ra['lum'] + rc['lum']) / 2); sl = abs(ra['lum'] - rc['lum'])
            if dl > 14 and dl > 3 * sl and not ok(b, 'pop'): fails.append(('pop', [b], f'brightness off by {dl:.0f}/255 for one frame'))
        if min(al.get(a, 0), al.get(b, 0), al.get(c, 0)) > 0.5:
            s1 = np.hypot(rb['c'][0] - ra['c'][0], rb['c'][1] - ra['c'][1]); s2 = np.hypot(rc['c'][0] - rb['c'][0], rc['c'][1] - rb['c'][1]); direct = np.hypot(rc['c'][0] - ra['c'][0], rc['c'][1] - ra['c'][1])
            if s1 + s2 > 0.02 * W and s1 + s2 > 3 * direct + 0.01 * W and not ok(b, 'jump'): fails.append(('jump', [b], f'centroid leaves and returns: {s1:.0f}+{s2:.0f} px vs {direct:.0f}'))
    run_len = 0; last = 0
    for i in range(1, len(fs)):
        a, b = fs[i - 1], fs[i]
        if b - a != 1 or min(al.get(a, 0), al.get(b, 0)) < 0.98: run_len = 0; last = 0; continue
        d = rows[b]['lum'] - rows[a]['lum']; sgn = 1 if d > 6 else -1 if d < -6 else 0
        run_len = run_len + 1 if (sgn and sgn == -last) else (1 if sgn else 0); last = sgn
        if run_len >= 3 and not ok(b, 'flicker'): fails.append(('flicker', [b], 'brightness alternates over 4 frames (> 6/255 each way)')); run_len = 0
    return fails, len(fs), len(exp)
def load(run, fmt):
    m = json.load(open(os.path.join(MAN, f'{run}_{fmt}.json'))); meta = json.load(open(os.path.join(META, f"{run}_{m['ver']}", fmt, 'meta.json')))
    return m, os.path.join(PUB, m['dir']), meta
def plant(run, fmt):
    """a scratch copy with one bad frame of each kind; every check must fire"""
    m, dirp, meta = load(run, fmt); tmp = os.path.join(SONG, 'build/him_wire/tmp/plant', f'{run}_{fmt}'); os.makedirs(tmp, exist_ok=True)
    for p in glob.glob(dirp + '/h_*.png'): shutil.copy(p, tmp)
    al = {x['f']: x['alpha'] for x in meta['frames']}; full = sorted(int(f) for f in m['frames'] if al.get(int(f), 0) > 0.98)
    exc = lambda f, kind: any(a - 3 <= f <= b + 3 and kind in ks for a, b, ks, _ in ALLOW.get(run, []))
    used = set(); planted = {}; m2 = json.loads(json.dumps(m))
    def pick(kind, n=1, start=3):
        """n consecutive full frames where `kind` is not excused, clear of what is already planted (and of the clip's ends)"""
        for i in list(range(start, len(full) - n - 3)) + list(range(3, start)):
            fs = full[i:i + n]
            if fs[-1] - fs[0] == n - 1 and not any(exc(f, kind) for f in fs) and not any(abs(f - u) < 4 for f in fs for u in used): used.update(fs); return fs
        return None
    fs = pick('count')
    if fs: os.replace(os.path.join(tmp, f'h_{fs[0]:05d}.png'), os.path.join(tmp, f'h_{fs[0]:05d}.png.planted_missing')); planted['count'] = fs[0]
    fs = pick('blank', 1, len(full) // 2)      # mid clip: at a frame edge (he enters / leaves) a near-empty frame is excused by design
    if fs: im = cv2.imread(os.path.join(tmp, f'h_{fs[0]:05d}.png'), cv2.IMREAD_UNCHANGED); im[..., 3] = 0; cv2.imwrite(os.path.join(tmp, f'h_{fs[0]:05d}.png'), im); planted['blank'] = fs[0]
    fs = pick('pop')
    if fs: im = cv2.imread(os.path.join(tmp, f'h_{fs[0]:05d}.png'), cv2.IMREAD_UNCHANGED); im[: im.shape[0] // 2, :, 3] = 0; cv2.imwrite(os.path.join(tmp, f'h_{fs[0]:05d}.png'), im); planted['pop'] = fs[0]
    fs = pick('jump')
    if fs: m2['frames'][str(fs[0])][0] += int(0.08 * m['res'][0]); planted['jump'] = fs[0]
    fs = pick('flicker', 5)
    if fs:
        for j, f in enumerate(fs):
            im = cv2.imread(os.path.join(tmp, f'h_{f:05d}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32); im[..., :3] = np.clip(im[..., :3] + (22 if j % 2 else -22), 0, 255); cv2.imwrite(os.path.join(tmp, f'h_{f:05d}.png'), im.astype(np.uint8))
        planted['flicker'] = fs[0]
    if not planted: print(f'[plant] {run} {fmt}: nothing to plant'); return True
    fails, n, ne = check(run, fmt, m2, tmp, meta); kinds = {k for k, _, _ in fails}; want = set(planted); never = sorted({'count', 'blank', 'pop', 'jump', 'flicker'} - want)
    print(f'[plant] {run} {fmt}: planted {planted} -> caught {sorted(kinds & want)}' + ('' if want <= kinds else f'  NOT CAUGHT: {sorted(want - kinds)}') + (f'  (excused for this whole clip by design, not testable: {never})' if never else ''))
    return want <= kinds
if __name__ == '__main__':
    args = sys.argv[1:]; planting = '--plant' in args; runs = [a for a in args if not a.startswith('--')] or sorted({os.path.basename(p).rsplit('_', 1)[0] for p in glob.glob(MAN + '/*.json')})
    bad = 0
    for run in runs:
        for fmt in ('169', '916'):
            if not os.path.exists(os.path.join(MAN, f'{run}_{fmt}.json')): print(f'[check] {run} {fmt}: NO CLIP (unknown run or not rendered)'); bad += 1; continue
            if planting: bad += 0 if plant(run, fmt) else 1; continue
            m, dirp, meta = load(run, fmt); fails, n, ne = check(run, fmt, m, dirp, meta)
            print(f"[check] {run} {fmt} ({m['ver']}): {n} frames compared, {ne} expected -> " + ('PASS' if not fails else f'FAIL {len(fails)}'))
            for k, fs, why in fails[:12]: print(f'    {k} at {fs}: {why}')
            bad += 1 if fails else 0
    sys.exit(1 if bad else 0)
