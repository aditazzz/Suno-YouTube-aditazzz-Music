#!/usr/bin/env python3
"""MASTER_V2_GATE (assembly part) on the file that ships: finish/v2/<name>_build.json -> finish/v2/qa/gate_<name>.txt/.json

  python3 songs/asking-for-a-friend/finish/v2/gate_v2.py [--name master_v2] [--selftest]

Checks (each prints PASS/FAIL with numbers):
  FRAMES  frame count = EDL total, 24/1, every row's segment = its EDL length (assemble asserts it per row; re-read here)
  TAGS    color_primaries / color_trc / colorspace = bt709, range tv
  F0      first frame mean luma >= 20/255 (never black)
  AUDIO   AAC 48 kHz stereo, starts at 0, length = picture +-1 f, and the song WAV lines up sample-exact: cross-correlation
          lag at 4 points <= 1 ms
  BLANK   no black (mean < 8/255) or blank (std < 2/255) frame and no frozen run (>= 3 repeats, diff < 0.12) that master v1
          (the 12:16 build she reviewed) didn't have at the same frame (v1's are designed / already triaged: INFO)
  SPLICE  every swap splice: mid-row splices must be continuous (diff <= max(3x local, local + 4)); splices on an EDL cut must
          cut exactly on the EDL frame (or a cut the swap's design declares in APPROVALS.yaml `cuts:`) and the swapped shot's head/tail frame must not flash (luma step > 6/255 against a
          calm shot, or blank)
  HEADTAIL every swapped shot: frame 1 vs 2 and last vs last-1, luma step > max(4, 3x inside + 2) (qa/v23/splice_check.py)
          = FAIL (auto-revert) unless v1 has the same step there (= FLAG: fix the frame); pairwise diff > max(6, 3x inside + 3)
          alone (an off-sequence frame) = FLAG
  STRAY   inside swapped frames: big frame changes (diff > 22) where v1 had none (diff < 6) = FLAG for one look (could be
          designed new motion)
A SPLICE / BLANK failure inside a swapped shot is written to finish/v2/qa/AUTO_REVERT.yaml (swaps.py then keeps routeB with a
flag: one shot never holds the master). Exit 0 = pass, 2 = only shot-level FAILs (auto-revert written), 1 = global FAIL.
--selftest plants a black frame, a pop at a splice, a frozen run and a dark head frame into the measured series and must catch all four.
--readonly: print only (no gate txt/json, no AUTO_REVERT.yaml, no metrics cache written); same exit code.
"""
import json, os, subprocess, sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SONG = os.path.abspath(os.path.join(HERE, "..", ".."))
QA = os.path.join(HERE, "qa")
HOME = os.path.expanduser("~")
V1 = f"{HOME}/Documents/Original Music/Asking for a Friend 2/master/AFF master_v1 (1080p, 2026-11-07 1216).mp4"
WAV = f"{HOME}/Documents/Original Music/Asking for a Friend 2 (clean).wav"
FPS, MW, MH = 24, 160, 90


def arg(n, d):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def run(*a):
    return subprocess.run(a, check=True, capture_output=True, text=True).stdout


def probe(path, sel, entries):
    return json.loads(run("ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", entries, "-of", "json", path))


RO = "--readonly" in sys.argv


def metrics(path, cache=None):
    """per frame: mean, std (0-255 luma, full range) and mean abs diff to the previous frame, at 160x90."""
    if cache and os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(path):
        z = np.load(cache)
        return z["mean"], z["std"], z["diff"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={MW}:{MH}:flags=area:out_range=full,format=gray",
                          "-f", "rawvideo", "-"], check=True, capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, MH, MW).astype(np.float32)
    mean, std = a.mean((1, 2)), a.std((1, 2))
    diff = np.concatenate([[0.0], np.abs(np.diff(a, axis=0)).mean((1, 2))])
    if cache and not RO:
        np.savez(cache, mean=mean, std=std, diff=diff)
    return mean, std, diff


def pcm(path, t, dur, stream=None):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-t", f"{dur:.4f}", "-i", path, *(["-map", stream] if stream else []),
                          "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def lag_ms(master, t):
    a, b = pcm(master, t, 2.0, "0:a:0"), pcm(WAV, t, 2.0)
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    if np.abs(b).max() < 1e-4:
        return None
    N = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(a, N) * np.conj(np.fft.rfft(b, N)), N)
    lim = 2400   # +-50 ms
    c = np.concatenate([c[-lim:], c[:lim + 1]])
    return (int(np.argmax(c)) - lim) / 48.0


def frozen_runs(diff, thr=0.12, minrun=3):
    out, s = [], None
    for f in range(1, len(diff)):
        if diff[f] < thr:
            s = f if s is None else s
        else:
            if s is not None and f - s >= minrun:
                out.append((s - 1, f - 1))
            s = None
    if s is not None and len(diff) - s >= minrun:
        out.append((s - 1, len(diff) - 1))
    return out


def _step(y, x0, x1, x2):
    """splice_check.py's rule: |y[x1]-y[x0]| > max(4.0, 3*|y[x2]-y[x1]| + 2) -> (bad, step, inside)"""
    st, ins = abs(y[x1] - y[x0]), abs(y[x2] - y[x1])
    return st > max(4.0, 3 * ins + 2), st, ins


def headtail(mean, diff, v1m, swapped):
    """For every swapped shot: frame 1 vs 2 and last vs last-1.
    Luma step (splice_check rule, 4.0) -> FAIL (shot auto-reverts), unless v1 has the same step at those frames (a revert
    can't fix it) -> FLAG 'fix the frame'. Pairwise-diff outlier only (diff > max(6, 3x inside + 3): an off-sequence frame
    at the same luma) -> FLAG.  -> (lines, {shot: why} fails, [flag strings])"""
    lines, fails, fl = [], {}, []
    n = len(mean)
    for s in swapped:
        a, e, sh = s["a"], s["b"], s["shot"]
        if e - a < 3 or e >= n:
            continue
        for side, (x0, x1, x2), bad_f in (("head", (a, a + 1, a + 2), a), ("tail", (e, e - 1, e - 2), e)):
            lbad, st, ins = _step(mean, x0, x1, x2)
            dbad = diff[max(x0, x1)] > max(6.0, 3 * diff[max(x1, x2)] + 3)
            if not (lbad or dbad):
                continue
            what = (f"{sh} {side} f{bad_f}: luma {mean[x0]:.1f} -> {mean[x1]:.1f} (step {st:.1f}, inside {ins:.1f}), "
                    f"diff {diff[max(x0, x1)]:.1f} vs {diff[max(x1, x2)]:.1f}")
            if lbad and v1m is not None and _step(v1m, x0, x1, x2)[0]:
                lines.append(f"   {what}: FLAG, same step in v1 (revert won't help; fix the frame, e.g. qa/v23/fix_heads2.py)")
                fl.append(f"{sh} {side} f{bad_f}: single-frame luma step {st:.1f} (also in v1): fix the frame")
            elif lbad:
                lines.append(f"   {what}: FAIL, single-frame {side} step")
                fails.setdefault(sh, f"{side} frame f{bad_f} steps {st:.1f} luma vs {ins:.1f} inside (fix: f1<-f2 like qa/v23/fix_heads2.py)")
            else:
                lines.append(f"   {what}: FLAG, off-sequence {side} frame? (pairwise diff only)")
                fl.append(f"{sh} {side} f{bad_f}: pairwise diff {diff[max(x0, x1)]:.1f} vs {diff[max(x1, x2)]:.1f} inside: one look")
    return lines, fails, fl


def check_series(mean, std, diff, v1m, v1s, v1d, build, edl_starts):
    """-> (lines, global_fail, shot_fails {shot: why}, flags)"""
    L, shot_fail, flags = [], {}, []
    swapped = {}
    for s in build["swapped"]:
        for f in range(s["a"], s["b"] + 1):
            swapped[f] = s["shot"]
    n = len(mean)
    has_v1 = v1m is not None and len(v1m) == n
    # BLANK / black
    bad = [f for f in range(n) if mean[f] < 8 or std[f] < 2]
    new_bad = [f for f in bad if not (has_v1 and (v1m[f] < 8 or v1s[f] < 2))]
    old_bad = len(bad) - len(new_bad)
    for f in new_bad:
        if f in swapped:
            shot_fail.setdefault(swapped[f], f"black/blank frame f{f} (mean {mean[f]:.1f}, std {std[f]:.1f})")
    L.append(f"BLANK   {'FAIL' if new_bad else 'PASS'}: {len(new_bad)} new black/blank frames {new_bad[:12]}; {old_bad} also in v1 (designed/triaged, INFO)")
    g_blank = [f for f in new_bad if f not in swapped]
    # frozen
    fr = frozen_runs(diff)
    new_fr = []
    for a, b in fr:
        if has_v1 and all(v1d[f] < 0.12 for f in range(a + 1, b + 1)):
            continue   # v1 held there too: designed hold
        new_fr.append((a, b))
        sh = next((swapped[f] for f in range(a, b + 1) if f in swapped), None)
        if sh:
            shot_fail.setdefault(sh, f"frozen run f{a}-{b} ({b - a + 1} identical frames) that v1 didn't have")
    L.append(f"FROZEN  {'FAIL' if new_fr else 'PASS'}: {len(new_fr)} new frozen runs {new_fr[:8]}; {len(fr) - len(new_fr)} holds also in v1 (designed)")
    g_frozen = [r for r in new_fr if not any(f in swapped for f in range(r[0], r[1] + 1))]
    # SPLICES
    sp_lines = []
    for s in build["splices"]:
        f = s["f"]
        sh = swapped.get(f) or swapped.get(f - 1)
        loc = np.median(np.r_[diff[max(1, f - 5):f - 1], diff[f + 1:min(n, f + 5)]]) if n > f + 1 else 0
        d = diff[f]
        verdict = "ok"
        cutlike = s["at_edl_cut"] or s.get("designed_cut")
        if not cutlike:
            if d > max(3 * loc, loc + 4):
                verdict = f"POP: diff {d:.1f} vs local {loc:.1f} at a mid-row splice"
        else:
            if d > max(3 * loc, loc + 4):   # a real cut: must land exactly on f
                win = diff[max(1, f - 2):min(n, f + 3)]
                if diff[f] < win.max() - 1e-6:
                    verdict = f"cut lands off the EDL frame (max diff at f{max(1, f - 2) + int(np.argmax(win))}, not f{f})"
            # head flash of whatever starts at f, tail flash of what ends at f-1
            for hf, nf, side in ((f, f + 1, "head"), (f - 1, f - 2, "tail")):
                if 0 <= nf < n and 0 <= hf < n:
                    step = abs(mean[hf] - mean[nf])
                    calm = np.median(np.abs(np.diff(mean[min(hf, nf):min(hf, nf) + 6]))) if side == "head" else \
                        np.median(np.abs(np.diff(mean[max(0, nf - 5):nf + 1])))
                    if (std[hf] < 2) or (step > 6 and step > 4 * max(calm, 0.5)):
                        verdict = f"{side} flash at f{hf} (luma step {step:.1f} vs {calm:.1f} inside the shot)"
        sp_lines.append(f"   f{f:5d} {s['from']:>8s} -> {s['to']:<8s} {'EDL cut' if s['at_edl_cut'] else 'designed cut' if s.get('designed_cut') else 'mid-row'} diff {d:5.1f} local {loc:4.1f}: {verdict}")
        if verdict != "ok" and sh:
            shot_fail.setdefault(sh, f"splice f{f}: {verdict}")
    nfail = sum(1 for x in sp_lines if not x.endswith(": ok"))
    L.append(f"SPLICE  {'FAIL' if nfail else 'PASS'}: {len(build['splices'])} swap splices, {nfail} bad")
    L += sp_lines
    # HEADTAIL: single-frame head/tail steps inside every swapped shot (qa/v23/splice_check.py's rule, folded in Nov 8)
    ht_lines, ht_fail, ht_flag = headtail(mean, diff, v1m if has_v1 else None, build["swapped"])
    for sh, why in ht_fail.items():
        shot_fail.setdefault(sh, why)
    L.append(f"HEADTAIL {'FAIL' if ht_fail else 'FLAG' if ht_flag else 'PASS'}: {len(build['swapped'])} swapped shots, "
             f"{len(ht_fail)} FAIL (auto-revert), {len(ht_flag)} FLAG")
    L += ht_lines
    # STRAY (flag only)
    if has_v1:
        for f in sorted(swapped):
            if f not in edl_starts and diff[f] > 22 and v1d[f] < 6:
                flags.append(f"{swapped[f]} f{f}: big change inside the swapped shot (diff {diff[f]:.0f}, v1 {v1d[f]:.0f}): one look")
    L.append(f"STRAY   {'FLAG' if flags else 'PASS'}: {len(flags)} in-shot jumps in swapped frames" + "".join(f"\n   {x}" for x in flags[:20]))
    return L, bool(g_blank or g_frozen), shot_fail, flags + ht_flag


def selftest(mean, std, diff, v1m, v1s, v1d, build, starts):
    m, s, d = mean.copy(), std.copy(), diff.copy()
    sp = [x for x in build["splices"] if not x["at_edl_cut"]] or build["splices"]
    fake = dict(build)
    a = 3000
    fake["swapped"] = list(build["swapped"]) + [dict(shot="TEST", chain="t", a=a, b=a + 40)]
    fake["splices"] = list(build["splices"]) + [dict(f=a + 20, **{"from": "base", "to": "t"}, at_edl_cut=False)]
    m[a + 5], s[a + 5] = 2.0, 0.5                       # black frame
    d[a + 20] = d[a + 20] + 30                          # pop at a mid-row splice
    d[a + 30:a + 34] = 0.0                              # frozen run
    step = max(15.0, 6 * abs(m[a + 2] - m[a + 1]) + 10)   # dark (or, on a dark shot, bright) single head frame
    m[a] = m[a + 1] - step if m[a + 1] - step >= 12 else m[a + 1] + step
    d[a + 1] = max(d[a + 1], step)
    if v1d is not None:
        v1d = v1d.copy(); v1d[a + 30:a + 34] = 3.0
    v1m_t = v1m.copy() if v1m is not None else None
    if v1m_t is not None:
        v1m_t[a:a + 3] = v1m_t[a + 1]                   # v1 calm there, so the planted head must FAIL, not FLAG
    L, g, sf, fl = check_series(m, s, d, v1m_t, v1s, v1d, fake, starts)
    caught = "TEST" in sf and any("FAIL" in x and x.startswith("BLANK") for x in L) and any(x.startswith("FROZEN  FAIL") for x in L) \
        and any("POP" in x for x in L) and any(x.startswith(f"   TEST head f{a}") and x.endswith("FAIL, single-frame head step") for x in L)
    return caught, L


def main():
    name = arg("--name", "master_v2")
    os.makedirs(QA, exist_ok=True)
    build = json.load(open(os.path.join(HERE, f"{name}_build.json")))
    M = build["master"]
    edl_starts = {r["a"] for r in build["rows"]}
    out, gfail = [f"# gate_v2 on {os.path.basename(M)}"], False
    # FRAMES
    v = probe(M, "v:0", "stream=r_frame_rate,width,height,color_primaries,color_transfer,color_space,color_range,nb_frames:format=duration")
    st = v["streams"][0]
    nfr = int(run("ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries", "stream=nb_read_packets",
                  "-of", "csv=p=0", M).strip())
    tiles = all(build["rows"][i + 1]["a"] == build["rows"][i]["b"] + 1 for i in range(len(build["rows"]) - 1)) and build["rows"][0]["a"] == 0
    ok = nfr == build["frames"] and st["r_frame_rate"] == "24/1" and tiles and build["rows"][-1]["b"] + 1 == build["frames"]
    gfail |= not ok
    out.append(f"FRAMES  {'PASS' if ok else 'FAIL'}: {nfr} frames (EDL {build['frames']}), {st['r_frame_rate']}, {st['width']}x{st['height']}, rows tile 0-{build['rows'][-1]['b']}: {tiles}")
    # TAGS
    tags = (st.get("color_primaries"), st.get("color_transfer"), st.get("color_space"), st.get("color_range"))
    ok = tags == ("bt709", "bt709", "bt709", "tv")
    gfail |= not ok
    out.append(f"TAGS    {'PASS' if ok else 'FAIL'}: {tags}")
    # series
    mean, std, diff = metrics(M, os.path.join(QA, f"metrics_{name}.npz"))
    v1m = v1s = v1d = None
    if os.path.exists(V1):
        v1m, v1s, v1d = metrics(V1, os.path.join(QA, "metrics_v1_1216.npz"))
    # F0
    ok = mean[0] >= 20
    gfail |= not ok
    out.append(f"F0      {'PASS' if ok else 'FAIL'}: first frame mean luma {mean[0] / 255:.3f} (>= 0.078)")
    # AUDIO
    if build.get("deliver"):
        out.append("AUDIO   SKIP: muted delivery picture (studio.render --finals-only muxes the WAV)")
    else:
        a = probe(M, "a:0", "stream=codec_name,sample_rate,channels,start_time,duration")["streams"]
        if not a:
            gfail = True
            out.append("AUDIO   FAIL: no audio stream")
        else:
            a = a[0]
            vd = nfr / FPS
            ad, t0 = float(a["duration"]), float(a.get("start_time") or 0)
            lags = [lag_ms(M, t) for t in (20.0, 90.0, 170.0, 240.0)]
            ok = a["codec_name"] == "aac" and a["sample_rate"] == "48000" and a["channels"] == 2 and abs(t0) <= 0.001 \
                and abs(ad - vd) <= 1 / FPS and all(x is not None and abs(x) <= 1.0 for x in lags)
            gfail |= not ok
            out.append(f"AUDIO   {'PASS' if ok else 'FAIL'}: {a['codec_name']} {a['sample_rate']} Hz {a['channels']} ch, start {t0:.4f} s, "
                       f"audio {ad:.3f} s vs picture {vd:.3f} s, WAV lag at 20/90/170/240 s = {lags} ms")
    L, g2, shot_fail, flags = check_series(mean, std, diff, v1m, v1s, v1d, build, edl_starts)
    gfail |= g2
    out += L
    if "--selftest" in sys.argv:
        caught, _ = selftest(mean, std, diff, v1m, v1s, v1d, build, edl_starts)
        out.append(f"SELFTEST {'PASS' if caught else 'FAIL'}: planted black frame + mid-row pop + frozen run + dark head frame in a fake swap {'all caught' if caught else 'NOT all caught'}")
        gfail |= not caught
    if shot_fail:
        out.append("SHOT FAILS (auto-revert to routeB with a flag): " + "; ".join(f"{k}: {v}" for k, v in shot_fail.items()))
    if shot_fail and not RO:
        ar = os.path.join(QA, "AUTO_REVERT.yaml")
        cur = (yaml.safe_load(open(ar)) or {}) if os.path.exists(ar) else {}
        import time
        cur.update({k: dict(why=f"master gate: {v}", at=time.time()) for k, v in shot_fail.items()})
        yaml.safe_dump(cur, open(ar, "w"), sort_keys=True, width=200)
    verdict = "FAIL" if gfail else (("SHOT-FAIL (would revert; --readonly wrote nothing)" if RO else "SHOT-FAIL (reverted, rebuild)")
                                    if shot_fail else "PASS")
    out.insert(1, f"VERDICT {verdict}")
    txt = "\n".join(out) + "\n"
    if RO:
        print(txt + "(--readonly: nothing written)")
        sys.exit(1 if gfail else 2 if shot_fail else 0)
    open(os.path.join(QA, f"gate_{name}.txt"), "w").write(txt)
    json.dump(dict(verdict=verdict, shot_fail=shot_fail, flags=flags, lines=out), open(os.path.join(QA, f"gate_{name}.json"), "w"), indent=1)
    print(txt)
    sys.exit(1 if gfail else 2 if shot_fail else 0)


main()
