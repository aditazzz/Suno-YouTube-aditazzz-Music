#!/usr/bin/env python3
"""Master v2 swap manifest: which version of every EDL row goes into master v2.

  python3 songs/asking-for-a-friend/finish/v2/swaps.py [--accept-gated]

Writes finish/v2/SWAPS.yaml. Per EDL row (finish/edl_routeB.csv) the source is the NEWEST candidate version that
  (a) is complete on disk (every frame of its range, routeB names fNNNNN.png),
  (b) passed its gate (.gate first line "<id> fA-B PASS" or "PASS+FLAG"; FAIL never enters), and
  (c) the director approved (finish/v2/APPROVALS.yaml: `<shot>: {chain: <chain or [chains]>, gate?: <text>, note?: }`;
      `gate:` stands in for a chain that writes no .gate file, e.g. a fix checked in its own STATUS),
else routeB (assemble_master's rule: routeB/<shot> -> _old_<shot> -> 2D kit) with `flag: <why>`.
--accept-gated: also take candidates whose gate is a clean PASS without an approval line (flagged "not director-approved").
A candidate may cover frames past its own row (S016 v2 = f769-784 also replaces S017's first 6 f): it is applied as an
overlay on exactly the frames it carries. Reads files only.
"""
import csv, datetime, glob, os, re, sys

import yaml

SONG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V2 = os.path.join(SONG, "finish", "v2")

# chain name -> folder holding <shot>/fNNNNN.png (+ <shot>/.gate). Order doesn't matter: newest gate/frames wins.
CHAINS = {
    "3d_a": "finish/v2/3d_a",            # rr_3d_a (+ rr_3d_b's fixed restart writes here too)
    "3d_b": "finish/v2/3d_b",
    "car": "finish/v2/car",              # rr_car (16:9)
    "lobby": "finish/v2/lobby",          # rr_lobby (brief: finish/v2/lobby/<shot>/)
    "rr_lobby": "finish/qa/rr_lobby/out",
    "port2d": "finish/v2/port2d",        # port_2d (2D kit ports)
    "fix452": "finish/qa/hook30/fix452/out",   # S008/S009
    "car_uv": "finish/v2/car_uv",        # car_uv_fix: Ultraviolet hue secondary on rr_car frames (finish/qa/car_uv/fix_uv.py)
    "car_uv_rb": "finish/v2/car_uv",     # v22: car_uv on the routeB v1 source (S048 fallback: v2 has a white bumper smear)
    "founder_clothes": "finish/v2/founder_clothes",   # founder_print: K02 print bg ultraviolet -> charcoal in post (finish/qa/founder_clothes/fix_founder.py)
}
# chains whose shot folders keep the 16:9 frames one level down (<chain>/<shot>/<sub>/fNNNNN.png)
CHAIN_SUB = {"car_uv": "16x9", "car_uv_rb": "16x9_routeB", "founder_clothes": "16x9"}
# fixed one-off folders: name -> (folder, shot it belongs to)
SINGLES = {
    "s016_v2": ("finish/qa/sets/work/s016_v1/swap", "S016"),   # her f776 note; f769-784 (S016 769-778 + S017 779-784)
}
GATE_RE = re.compile(r"^\s*(\S+)\s+f(\d+)-(\d+)\s+(PASS\+FLAG|PASS|FAIL)\b(.*)$")


def edl():
    rows = []
    for r in csv.DictReader(open(os.path.join(SONG, "finish", "edl_routeB.csv"))):
        if r["new_frames"].strip() and int(r["n"] or 0) > 0:
            a, b = map(int, r["new_frames"].split("-"))
            rows.append(dict(shot=r["shot"], a=a, b=b, world=r["world"], set=r["set"]))
    rows.sort(key=lambda r: r["a"])
    return rows


def frames_in(d):
    nums = sorted(int(m.group(1)) for f in os.listdir(d) if (m := re.match(r"^f(\d{5})\.png$", f)))
    return nums


def candidate(name, d, shot, rows_by_shot):
    """-> dict describing one candidate folder (or None if it has no frames)."""
    full = os.path.join(SONG, d)
    if not os.path.isdir(full):
        return None
    nums = frames_in(full)
    if not nums:
        return None
    r = rows_by_shot.get(shot)
    c = dict(chain=name, dir=d, shot=shot, frames=f"{nums[0]}-{nums[-1]}", n=len(nums), gate=None, status="NO GATE",
             mtime=max(os.path.getmtime(os.path.join(full, f"f{n:05d}.png")) for n in (nums[0], nums[-1])))
    a, b = nums[0], nums[-1]
    g = os.path.join(full, ".gate")
    if os.path.exists(g):
        line = open(g).readline().strip()
        c["gate"] = line[:400]
        c["mtime"] = max(c["mtime"], os.path.getmtime(g))
        m = GATE_RE.match(line)
        if m:
            c["status"] = m.group(4)
            ga, gb = int(m.group(2)), int(m.group(3))
            a, b = ga, gb
    c["a"], c["b"] = a, b
    missing = [f for f in range(a, b + 1) if f not in set(nums)]
    c["complete"] = not missing
    if missing:
        c["missing"] = f"{len(missing)} f (e.g. {missing[:3]})"
    if r and not (a <= r["b"] and b >= r["a"]):
        c["complete"] = False
        c["missing"] = f"range {a}-{b} doesn't overlap the EDL row {r['a']}-{r['b']}"
    return c


def main():
    rows = edl()
    by_shot = {r["shot"]: r for r in rows}
    appr_p = os.path.join(V2, "APPROVALS.yaml")
    appr = (yaml.safe_load(open(appr_p)) or {}) if os.path.exists(appr_p) else {}
    accept_gated = "--accept-gated" in sys.argv
    cands, ignored = {}, []
    for name, d in CHAINS.items():
        root = os.path.join(SONG, d)
        if not os.path.isdir(root):
            continue
        for sub in sorted(os.listdir(root)):
            fsub = CHAIN_SUB.get(name, "")
            if not os.path.isdir(os.path.join(root, sub)) or not glob.glob(os.path.join(root, sub, fsub, "f*.png")):
                continue
            if sub not in by_shot:
                ignored.append(f"{d}/{sub}: not an EDL shot id (bad id / parked), ignored")
                continue
            c = candidate(name, f"{d}/{sub}" + (f"/{fsub}" if fsub else ""), sub, by_shot)
            if c:
                cands.setdefault(sub, []).append(c)
    for name, (d, shot) in SINGLES.items():
        c = candidate(name, d, shot, by_shot)
        if c:
            cands.setdefault(shot, []).append(c)

    ar_p = os.path.join(V2, "qa", "AUTO_REVERT.yaml")   # written by gate_v2.py: a swap that failed the master gate
    auto_rev = (yaml.safe_load(open(ar_p)) or {}) if os.path.exists(ar_p) else {}
    chosen, flags, rows_out = [], [], {}
    for shot, cs in cands.items():
        rev = auto_rev.get(shot)
        if rev:   # only versions newer than the failed one are considered again
            cs = [c for c in cs if c["mtime"] > rev["at"]] or [dict(cs[0], status="REVERTED", gate=rev["why"])]
        a = appr.get(shot) or {}
        want = a.get("chain") or []
        want = [want] if isinstance(want, str) else list(want)
        for c in cs:
            if c["status"] == "NO GATE" and c["chain"] in want and a.get("gate"):
                c["status"], c["gate"] = "PASS", f"(manual, APPROVALS.yaml) {a['gate']}"
            c["approved"] = c["chain"] in want
        ok = [c for c in cs if c["complete"] and c["status"] in ("PASS", "PASS+FLAG")
              and (c["approved"] or (accept_gated and c["status"] == "PASS"))]
        ok.sort(key=lambda c: c["mtime"], reverse=True)
        if ok:
            c = ok[0]
            chosen.append(c)
            note = None
            if not c["approved"]:
                note = f"{c['chain']} gate PASS, entered by --accept-gated: not director-approved yet"
            elif c["status"] == "PASS+FLAG":
                note = f"{c['chain']} gate PASS+FLAG: " + (c["gate"].split("FLAG:", 1)[1].split("|")[0].strip() if "FLAG:" in c["gate"] else "see gate")
            rows_out[shot] = dict(source=c["chain"], dir=c["dir"], swap_frames=f"{c['a']}-{c['b']}", gate=c["gate"], flag=note)
            if note:
                flags.append(f"{shot}: {note}")
            continue
        # nothing usable: say why (the newest candidate decides the wording)
        cs.sort(key=lambda c: c["mtime"], reverse=True)
        c = cs[0]
        if c["status"] == "REVERTED":
            why = f"{c['gate']}: routeB kept (auto-revert)"
        elif c["status"] == "FAIL":
            why = f"{c['chain']} gate FAIL ({c['gate'].split('|')[1].strip() if '|' in c['gate'] else c['gate']}): routeB kept"
        elif not c["complete"]:
            why = f"{c['chain']} incomplete/rendering ({c.get('missing')}): routeB kept"
        elif c["status"] == "NO GATE":
            why = f"{c['chain']} has frames but no gate yet: routeB kept"
        else:
            why = f"{c['chain']} gate {c['status']}, waiting for the director's approval: routeB kept"
        rows_out[shot] = dict(source="routeB", flag=why, candidate=c["dir"], candidate_gate=c["gate"])
        flags.append(f"{shot}: {why}")
    # approved but nothing landed yet
    for shot, a in appr.items():
        if shot not in rows_out and shot in by_shot:
            why = f"approved ({a.get('chain')}) but not rendered/landed yet: routeB kept" + (f" ({a['note']})" if a.get("note") else "")
            rows_out[shot] = dict(source="routeB", flag=why)
            flags.append(f"{shot}: {why}")

    out = dict(
        built=f"{datetime.datetime.now():%a %b %d %H:%M}",
        rule="newest candidate that is complete + gate PASS/PASS+FLAG + director-approved (APPROVALS.yaml), else routeB with a flag",
        accept_gated=accept_gated,
        overlays=[dict(shot=c["shot"], chain=c["chain"], dir=c["dir"], a=c["a"], b=c["b"],
                       cuts=list((appr.get(c["shot"]) or {}).get("cuts") or [])) for c in sorted(chosen, key=lambda c: c["a"])],
        flags=flags,
        rows={r["shot"]: dict(frames=f"{r['a']}-{r['b']}", **rows_out.get(r["shot"], dict(source="routeB")))
              for r in rows},
        ignored=ignored,
    )
    # an overlay that runs into the next row: note it on that row
    for o in out["overlays"]:
        for r in rows:
            if r["shot"] != o["shot"] and o["a"] <= r["b"] and o["b"] >= r["a"]:
                out["rows"][r["shot"]]["overlay"] = f"{o['chain']} f{max(o['a'], r['a'])}-{min(o['b'], r['b'])} (from {o['shot']})"
    with open(os.path.join(V2, "SWAPS.yaml"), "w") as f:
        f.write("# master v2 swap manifest, written by finish/v2/swaps.py (edit APPROVALS.yaml, not this file)\n")
        yaml.safe_dump(out, f, sort_keys=False, width=200, allow_unicode=True)
    print(f"SWAPS.yaml: {len(out['overlays'])} swaps, {len(flags)} flags, {len(ignored)} ignored folders")
    for o in out["overlays"]:
        print(f"  SWAP {o['shot']:6s} f{o['a']}-{o['b']} <- {o['dir']}")
    for fl in flags:
        print(f"  FLAG {fl}")


main()
