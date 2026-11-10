#!/usr/bin/env python3
"""collide_report.py: groups tools/collide_check.py output (jsonl, one line per frame) into hits and decides pass/fail.

  python3 tools/collide_report.py <run.jsonl> [more.jsonl ...] [--allow <file>]... [--px 2] [--json out.json] [--label S043]
          [--frame-offset N]

A hit = one object pair over a run of frames. It FAILS the check when, on at least one frame, it is
  class "penetration" (deeper than COLLIDE_EPS, not parts of one model, not two static set pieces), on screen, seen by the
  camera (vis > 0: not hidden behind something) and at least --px pixels deep (default 2), and no allowlist line covers it.
Exit code 0 = pass, 3 = fail (new visible penetration), 2 = bad input.

Allowlist (text, one pair per line, '#' comment = why it's designed):  <globA> <globB> [max_depth_m]
  "group <name> <glob> <glob> ..." defines a set of parts (e.g. every part of the Claude robot, whose joints are separate
  roots); "@<name>" in a pair line stands for any member: "@robot @robot" = robot parts meeting each other are designed.
  Globs match object names with any ".001" suffix and any "<instancer>>" prefix removed, in either order. A max depth
  means "allowed up to this deep" (a later, deeper version of the same pair fails again). Files read by default: every
  collide_allow.txt next to each checked blend and up to 3 folders above it, plus tools/collide_allow.txt.
"""
import fnmatch, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def base(n):
    n = n.split(">")[-1]
    return re.sub(r"\.\d{3}$", "", n)


GROUPS = {}


def prefix(n):
    return re.split(r"[_.\- ]", base(n), maxsplit=1)[0].lower()


def load_allow(paths):
    rules = []
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        for ln in open(p):
            why = ln.split("#", 1)[1].strip() if "#" in ln else ""
            t = ln.split("#", 1)[0].split()
            if t and t[0] == "group" and len(t) > 2:
                GROUPS.setdefault(t[1], []).extend(t[2:]); continue
            if len(t) < 2:
                continue
            rules.append((t[0], t[1], float(t[2]) if len(t) > 2 else None, why, p))
    return rules


def m(name, g):
    if g.startswith("@"):   # "@robot_hand_?" = any group whose name matches
        return any(fnmatch.fnmatchcase(name, x) for k, v in GROUPS.items() if fnmatch.fnmatchcase(k, g[1:]) for x in v)
    return fnmatch.fnmatchcase(name, g)


def allowed(a, b, depth, rules):
    A, B = base(a), base(b)
    for ga, gb, md, why, src in rules:
        if (m(A, ga) and m(B, gb)) or (m(A, gb) and m(B, ga)):
            if md is None or depth <= md:
                return why or "allowlisted"
    return None


def ranges(fr):
    fr = sorted(set(fr)); out = []
    for f in fr:
        if out and f - out[-1][1] <= 2:
            out[-1][1] = f
        else:
            out.append([f, f])
    return ",".join(f"{a}-{b}" if a != b else str(a) for a, b in out)


def default_allow(blends):
    ps = [os.path.join(HERE, "collide_allow.txt")]
    for b in blends:
        d = os.path.dirname(b)
        for _ in range(4):
            ps.append(os.path.join(d, "collide_allow.txt")); d = os.path.dirname(d)
    return list(dict.fromkeys(ps))


def main(argv):
    files, allow, px, jout, label, foff = [], [], 2.0, None, "", 0
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--allow": allow.append(argv[i + 1]); i += 2
        elif a == "--px": px = float(argv[i + 1]); i += 2
        elif a == "--json": jout = argv[i + 1]; i += 2
        elif a == "--label": label = argv[i + 1]; i += 2
        elif a == "--frame-offset": foff = int(argv[i + 1]); i += 2
        else: files.append(a); i += 1
    recs = []
    for f in files:
        if not os.path.exists(f):
            print(f"[collide] no such file {f}"); return 2
        for ln in open(f):
            ln = ln.strip()
            if ln:
                try: recs.append(json.loads(ln))
                except Exception: pass
    if not recs:
        print(f"[collide] {label} no frames checked"); return 2
    blends = sorted({r.get("blend", "") for r in recs if r.get("blend")})
    rules = load_allow(allow + default_allow(blends))
    H = {}
    nframes = len(recs); npairs = sum(r.get("pairs_tested", 0) for r in recs)
    eps = float(os.environ.get("COLLIDE_EPS", "0.01"))
    GROUND = re.compile(os.environ.get("COLLIDE_GROUND", r"(terrain|ground|soil|dirt|road|shoulder|verge|kerb|curb|edge|lawn|gravel|rock|stone|pot|planter|bed|mulch|floor|land|hill|path|drive|court|paver|patio|deck|slab|plaza|asphalt|tarmac|concrete|carpet|rug)"), re.I)
    NATURE = re.compile(os.environ.get("COLLIDE_NATURE", r"(scrub|grass|leaf|leaves|plant|tree|bush|shrub|cact|fern|foliage|flower|weed|ivy|moss|branch|frond|palm|agave|yucca|reed|muhly|sotol|cedar|oak|juniper|hedge|lily|succulent)"), re.I)
    SURF = re.compile(os.environ.get("COLLIDE_SURF", r"(terrain|ground|soil|dirt|road|shoulder|verge|kerb|curb|lawn|gravel|mulch|floor|land|hill|path|drive|court|paver|patio|deck|slab|plaza|asphalt|tarmac|concrete|carpet|rug)"), re.I)
    sig = {}
    for r in recs:
        for h in r.get("hits", []):
            k = tuple(sorted((base(h["a"]), base(h["b"]))))
            sig.setdefault(k, set()).add((h["depth_m"], h["n_tris"]))
    cnt = {}
    for r in recs:
        for h in r.get("hits", []):
            k = tuple(sorted((base(h["a"]), base(h["b"])))); cnt[k] = cnt.get(k, 0) + 1
    def static_pair(h):
        if "mv" in h:
            return not any(h["mv"])
        k = tuple(sorted((base(h["a"]), base(h["b"]))))
        return cnt.get(k, 0) >= 3 and len(sig.get(k, ())) == 1
    def reclass(h):
        A, B = base(h["a"]), base(h["b"])
        if h.get("cls") in ("penetration", "contact", "assembly", "construction"):
            if (NATURE.search(A) and (NATURE.search(B) or GROUND.search(B))) or (NATURE.search(B) and GROUND.search(A)):
                h["cls"] = "nature"
            elif h["cls"] == "penetration" and (SURF.search(A) or SURF.search(B)) and static_pair(h):
                h["cls"] = "grounded"
    for r in recs:
        fr = (r.get("frame") or 0) + foff
        for h in r.get("hits", []):
            if h.get("cls") == "assembly" and prefix(h["a"]) != prefix(h["b"]):
                h["cls"] = "penetration" if h["depth_m"] > eps else "contact"   # same parent, different models (chair + body)
            reclass(h)
            k = tuple(sorted((base(h["a"]), base(h["b"])))) + (h.get("cls", "?"),)
            g = H.setdefault(k, dict(a=k[0], b=k[1], cls=k[2], frames=[], vis_frames=[], max_px=0, max_m=0, max_vis=0, at=None,
                                     where=None, blend=r.get("blend"), camera=None))
            g["frames"].append(fr)
            seen = h["vis"] > 0 and h["onscreen"] > 0
            if seen: g["vis_frames"].append(fr)
            score = h["depth_px"] if seen else h["depth_px"] * 0.01
            best = g["max_px"] if g["at"] is None else (g["_score"])
            if g["at"] is None or score > best:
                g["_score"] = score; g["at"] = fr; g["where"] = h.get("where"); g["camera"] = r.get("camera")
            g["max_px"] = max(g["max_px"], h["depth_px"] if seen else 0); g["max_m"] = max(g["max_m"], h["depth_m"])
            g["max_vis"] = max(g["max_vis"], h["vis"])
    out = []
    for g in H.values():
        g.pop("_score", None)
        fail = g["cls"] == "penetration" and g["vis_frames"] and g["max_px"] >= px
        why = allowed(g["a"], g["b"], g["max_m"], rules) if fail else None
        g["status"] = "FAIL" if fail and not why else ("allowed" if why else "ok")
        g["allow_why"] = why
        g["range"] = ranges(g["frames"]); g["vis_range"] = ranges(g["vis_frames"])
        g["n_frames"] = len(set(g["frames"]))
        g.pop("frames"); g.pop("vis_frames")
        out.append(g)
    out.sort(key=lambda g: ({"FAIL": 0, "allowed": 1, "ok": 2}[g["status"]], -g["max_px"]))
    by = {}
    for g in out:
        by[g["cls"]] = by.get(g["cls"], 0) + 1
    fails = [g for g in out if g["status"] == "FAIL"]
    summary = dict(label=label, frames=nframes, pairs_tested=npairs, hit_pairs=len(out), by_class=by, fails=len(fails),
                   allowed=sum(g["status"] == "allowed" for g in out), px=px, blends=blends)
    if jout:
        os.makedirs(os.path.dirname(os.path.abspath(jout)), exist_ok=True)
        json.dump(dict(summary=summary, hits=out), open(jout, "w"), indent=1)
    print(f"[collide] {label} frames={nframes} pairs_tested={npairs} hit_pairs={len(out)} {by} -> "
          f"{'FAIL ' + str(len(fails)) + ' visible penetration(s)' if fails else 'PASS'}")
    for g in fails[:30]:
        print(f"[collide]   FAIL {g['a']} x {g['b']}: {g['max_m']*100:.1f} cm / {g['max_px']:.0f} px deep, seen f{g['vis_range']}, "
              f"worst f{g['at']} at {g['where']}")
    return 3 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
