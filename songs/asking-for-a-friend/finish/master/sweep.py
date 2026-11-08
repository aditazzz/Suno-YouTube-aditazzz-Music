#!/usr/bin/env python3
"""Pre-master sweep of the assembled master, per EDL row (render-checks skill). Reads the mp4 that would ship.

  .venv/bin/python songs/asking-for-a-friend/finish/master/sweep.py <master.mp4> [--selftest] [--out <json>]

Decodes at 480x270. Per frame pair inside a row (the pair across a row boundary is the EDL's own cut, not checked):
  BLANK      mean luma < 0.02 or > 0.98, or std < 0.01
  FROZEN     runs of >= 12 identical frames (max abs diff < 1.5/255) inside a row (a designed hold or a stalled render)
  POP        motion-compensated residual (Farneback, prev warped onto cur, 99th pct) far above the row's median
  LUMA STEP  global luma step far above the row's median; FLICKER a luma step that reverses next frame
  FLICK1     one-frame flicker: cur differs from both warped neighbours while they agree (score quieted by motion)
  CUT        colour-histogram jump (16 bins/channel at 160x90, half L1) inside a row
  JITTER     1 s window: no step > 9 px, path >= 10.5 px, net < 35% of path (skill's 12/14 px at 640 wide, scaled)
Thresholds: robust z > 6 against the row (rows < 16 frames use the film's median) AND an absolute floor.
--selftest plants each fault in a copy of real frames and asserts it is caught (checks must be able to fail).
"""
import csv, json, os, subprocess, sys
import numpy as np, cv2

SONG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
W, H = 480, 270


def frames_of(mp4):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", mp4, "-vf", f"scale={W}:{H}:flags=area", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)


def edl_rows():
    rows = []
    for r in csv.DictReader(open(os.path.join(SONG, "finish", "edl_routeB.csv"))):
        if r["new_frames"].strip() and int(r["n"] or 0) > 0:
            a, b = map(int, r["new_frames"].split("-"))
            rows.append((r["shot"], a, b, r["world"]))
    return sorted(rows, key=lambda x: x[1])


GX, GY = np.meshgrid(np.arange(W), np.arange(H))


def flow_warp(src, dst):
    """warp src onto dst (gray float); returns warped, mean flow speed"""
    fl = cv2.calcOpticalFlowFarneback((dst * 255).astype(np.uint8), (src * 255).astype(np.uint8), None, 0.5, 3, 21, 3, 5, 1.1, 0)
    wp = cv2.remap(src, (GX + fl[..., 0]).astype(np.float32), (GY + fl[..., 1]).astype(np.float32), cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REPLICATE)
    return wp, np.sqrt((fl ** 2).sum(-1))


def hist(f):
    s = cv2.resize(f, (160, 90), interpolation=cv2.INTER_AREA)
    return np.concatenate([np.histogram(s[..., c], 16, (0, 256))[0] for c in range(3)]) / (160 * 90)


def metrics(frames):
    """per-frame and per-pair metrics; streams (keeps 3 frames)"""
    L, S, res, dl, same, jump, shift, fl1 = [], [], [], [], [], [], [], []
    prev = prevg = prevh = None
    win = []  # (gray) last 3 frames for one-frame flicker centred on the middle one
    m = 12
    for f in frames:
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        h = hist(f)
        L.append(float(g.mean())); S.append(float(g.std()))
        if prevg is not None:
            wp, sp = flow_warp(prevg, g)
            r = cv2.GaussianBlur(np.abs(wp - g), (0, 0), 2.0)[m:-m, m:-m]
            res.append(float(np.percentile(r, 99))); dl.append(float(g.mean() - prevg.mean()))
            same.append(float(np.abs(f.astype(np.int16) - prev.astype(np.int16)).max()) / 255.0)
            jump.append(float(0.5 * np.abs(h - prevh).sum()))
            (dx, dy), _ = cv2.phaseCorrelate(prevg.astype(np.float64), g.astype(np.float64))
            shift.append((float(dx), float(dy)))
        win.append(g); win = win[-3:]
        if len(win) == 3:
            a, c, b = win
            wa, _ = flow_warp(a, c); wb, _ = flow_warp(b, c)
            _, sab = flow_warp(a, b)   # motion from the neighbours only (a flickering patch on c can't fake speed)
            sab = cv2.GaussianBlur(sab, (0, 0), 4.0) / 2
            d_a, d_b, d_ab = np.abs(c - wa), np.abs(c - wb), np.abs(wa - wb)
            sc = np.clip(np.minimum(d_a, d_b) - d_ab, 0, None)
            sc = sc / (1 + (sab / (8 * H / 720)) ** 2)
            sc = cv2.GaussianBlur(sc, (0, 0), 1.5)[m:-m, m:-m]
            fl1.append(float(np.percentile(sc, 99.9)))
        prev, prevg, prevh = f, g, h
    return dict(L=np.array(L), S=np.array(S), res=np.array(res), dl=np.array(dl), same=np.array(same),
                jump=np.array(jump), shift=np.array(shift).reshape(-1, 2), fl1=np.array([0.0] + fl1 + [0.0]))


def rz(x, ref):
    med = np.median(ref); mad = np.median(np.abs(ref - med)) * 1.4826 + 1e-4
    return (x - med) / mad


def judge(M, rows):
    issues = []
    gres, gdl, gfl = M["res"], M["dl"], M["fl1"]
    for shot, a, b, world in rows:
        n = b - a + 1
        pr = np.arange(a, b)          # pair index i = (i, i+1), inside the row only
        if len(pr) == 0:
            continue
        small = n < 16
        res, dl, jm, sm = M["res"][pr], M["dl"][pr], M["jump"][pr], M["same"][pr]
        ref_res = gres if small else res
        ref_dl = gdl if small else dl
        for i in range(a, b + 1):
            if M["L"][i] < 0.02 or M["L"][i] > 0.98 or M["S"][i] < 0.01:
                issues.append((shot, "BLANK", f"f{i}", round(float(M["L"][i]), 3)))
        z = rz(res, ref_res)
        for k, i in enumerate(pr):
            pair = f"f{i}->f{i + 1}"
            if z[k] > 6 and res[k] > 0.03:
                issues.append((shot, "POP", pair, f"{res[k]:.3f} (row median {np.median(res):.3f})"))
            if abs(rz(dl[k:k + 1], ref_dl)[0]) > 6 and abs(dl[k]) > 0.008:
                issues.append((shot, "LUMA STEP", pair, round(float(dl[k]), 4)))
            if k + 1 < len(dl) and dl[k] * dl[k + 1] < 0 and min(abs(dl[k]), abs(dl[k + 1])) > 0.006:
                issues.append((shot, "FLICKER", pair, round(float(dl[k]), 4)))
            if jm[k] > 0.30:
                issues.append((shot, "CUT", pair, round(float(jm[k]), 3)))
        fz = sm < 1.5 / 255
        run = 0
        for k in range(len(fz) + 1):
            if k < len(fz) and fz[k]:
                run += 1
            else:
                if run >= 11:
                    issues.append((shot, "FROZEN", f"f{pr[k - run]}-f{pr[k - run] + run}", f"{run + 1} identical frames"))
                run = 0
        fr = np.arange(a + 1, b)      # flicker centred on interior frames
        if len(fr):
            fv = M["fl1"][fr]
            zf = rz(fv, gfl if small else fv)
            for k, i in enumerate(fr):
                if zf[k] > 6 and fv[k] > 0.10:
                    issues.append((shot, "FLICK1", f"f{i}", f"{fv[k]:.3f}"))
        sh = M["shift"][pr]
        for s in range(0, max(1, len(sh) - 24 + 1), 6):
            wnd = sh[s:s + 24]
            if len(wnd) < 24:
                break
            step = np.sqrt((wnd ** 2).sum(1))
            path = step.sum(); net = np.sqrt((wnd.sum(0) ** 2).sum())
            if step.max() <= 9 and path >= 10.5 and net < 0.35 * path:
                issues.append((shot, "JITTER", f"f{pr[s]}-f{pr[s] + 24}", f"path {path:.1f}px net {net:.1f}px"))
                break
    return issues


AT = int(sys.argv[sys.argv.index("--at") + 1]) if "--at" in sys.argv else 30


def selftest(mp4):
    fr = []
    for i, f in enumerate(frames_of(mp4)):
        if AT <= i < AT + 60:   # a span inside one EDL row
            fr.append(f.copy())
        if i >= AT + 60:
            break
    assert len(fr) == 60, "selftest: could not read 60 frames"
    rows = [("T", 0, 59, "3D")]
    ok = True
    plants = {
        "BLANK": lambda F: F.__setitem__(30, F[30] * 0),
        "FROZEN": lambda F: [F.__setitem__(j, F[20].copy()) for j in range(21, 34)],
        "POP": lambda F: F.__setitem__(30, np.where((np.arange(W)[None, :, None] < W // 3), np.roll(F[30], 40, 0), F[30])),
        "LUMA STEP": lambda F: [F.__setitem__(j, np.clip(F[j].astype(np.int16) * 1.1 + 6, 0, 255).astype(np.uint8)) for j in range(30, 60)],
        "FLICK1": lambda F: F[30].__setitem__((slice(100, 140), slice(200, 240)), np.clip(F[30][100:140, 200:240].astype(np.int16) + 90, 0, 255).astype(np.uint8)),
        "CUT": lambda F: F.__setitem__(30, np.ascontiguousarray(255 - F[30])),
    }
    base = judge(metrics(fr), rows)
    print(f"[selftest] frames {AT}-{AT + 59}; clean span issues:", base)
    for label, plant in plants.items():
        F = [f.copy() for f in fr]
        plant(F)
        got = [i for i in judge(metrics(F), rows) if i[1] == label]
        hit = bool(got)
        print("[selftest]", label, "planted ->", "caught" if hit else "MISSED", got[:2])
        ok &= hit
    print("[selftest]", "PASS" if ok else "FAIL")
    return ok


def main():
    mp4 = sys.argv[1]
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest(mp4) else 1)
    rows = edl_rows()
    total = rows[-1][2] + 1
    M = metrics(frames_of(mp4))
    n = len(M["L"])
    assert n == total, f"compared {n} frames, EDL has {total}"
    iss = judge(M, rows)
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(SONG, "finish", "master", "sweep.json")
    np.savez_compressed(out.replace(".json", "_metrics.npz"), **{k: v for k, v in M.items()})
    json.dump(dict(master=mp4, frames=n, issues=iss), open(out, "w"), indent=1)
    print(f"[sweep] {n} frames compared (EDL {total}), {len(iss)} flags")
    for i in iss:
        print("  ", *i)


main()
