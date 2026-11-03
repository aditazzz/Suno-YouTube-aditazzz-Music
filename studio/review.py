"""Review pages: anything that needs the creator's approval (video frames, thumbnails, covers, designs, slides, copy options)
goes on a page where they approve each item or marks it "Needs changes" with a note, round by round.

  # a film's frames, one per shot (shots from songs/<slug>/shots.yaml)
  python3 -m studio.review songs/<slug> frames --times                    # the frame times (render them as stills)
  python3 -m studio.review songs/<slug> frames --video <render.mp4>       # round 1 from a render
  python3 -m studio.review songs/<slug> frames --stills <dir>             # round 1 from stills named s_<t>.jpg
  # any other batch: an items.yaml (see ITEMS below)
  python3 -m studio.review songs/<slug> thumbs --items <items.yaml>
  # the decisions, read from the page's database by Claude and saved as JSON
  python3 -m studio.review songs/<slug> <batch> --answers <answers.json>  # -> state.json + REVIEW_round_N.md
  # the next round: only what changed (plus anything a change put back up), on the same page
  python3 -m studio.review songs/<slug> <batch> --next <changes.yaml> [--video|--stills|--items ...]
  # once everything is approved
  python3 -m studio.review songs/<slug> <batch> --save-approved           # -> <music folder>/<Song>/Approved/<batch>/

Out: songs/<slug>/build/review/<batch>/: index.html, img/, items.json, state.json, round_N/answers.json, REVIEW_round_N.md.
Claude publishes index.html as an Artifact (files: every img/* path, capabilities: {db: {}}, icon "film"); the
decisions land in the page's database, collection `round_N` (one document per item id: decision "approve" |
"changes" | "", note; and `_overall`: note, done). Each round is a fresh collection on the same page.

ITEMS (items.yaml): heading, covers (what the batch is), video (optional preview), and
  items: [{id, img (path), title, pos (position or timestamp), text (on-screen text / caption), notes (design notes)}]
SHOTS (shots.yaml): video, label, end, fps, covers, and
  shots: [{at, t?, title, lyric?, text?, notes, intent?}]
CHANGES (changes.yaml): changed: {id: "what changed, one line"}, reopened: {id: "why it's back"}, top_notes: [..]
"""
import argparse, glob, hashlib, json, math, os, re, shutil, subprocess, sys

import yaml

from studio import config

HERE = os.path.dirname(os.path.abspath(__file__))
FPS_DEFAULT = 30
WIDTH = 1280


def _tc(t):
    m = int(t // 60)
    return f"{m}:{t - 60 * m:05.2f}"


def _probe_duration(path):
    try:
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                    capture_output=True, text=True, check=True).stdout.strip())
    except Exception:
        return None


def _md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------- shots -> items
def _sung(lines, a, b):
    parts = []
    for ln in lines:
        wt, words = ln.get("wt") or [], ln.get("words") or []
        idx = [i for i, w in enumerate(wt) if a - 0.02 <= w < b - 0.02]
        if not idx:
            continue
        txt = re.sub(r"[,;:]$", "", " ".join(words[i] for i in idx).strip())
        parts.append(("…" if idx[0] > 0 else "") + txt + ("…" if idx[-1] < len(words) - 1 else ""))
    return " / ".join(parts)


def _line_sec(lines, a, b):
    for ln in lines:
        if any(a - 0.02 <= w < b - 0.02 for w in (ln.get("wt") or [])) and ln.get("sec"):
            return ln["sec"]
    return ""


def _section(secs, t):
    for s in secs:
        if s.get("s", 0) <= t < s.get("e", 1e9):
            return s.get("name", "")
    return ""


def load_shots(song, video=None):
    b = song["build"]
    lines = json.load(open(os.path.join(b, "timed.json"))) if os.path.exists(os.path.join(b, "timed.json")) else []
    secs = json.load(open(os.path.join(b, "sections.json"))) if os.path.exists(os.path.join(b, "sections.json")) else []
    p = os.path.join(song["dir"], "shots.yaml")
    spec = yaml.safe_load(open(p)) if os.path.exists(p) else {}
    fps = spec.get("fps", FPS_DEFAULT)
    end = spec.get("end") or (video and _probe_duration(video)) or _probe_duration(song["audio"])
    if not end:
        sys.exit("review: can't tell where the film ends; set `end:` in shots.yaml")
    if spec.get("shots"):
        raw = [dict(x) for x in spec["shots"]]
    else:  # one shot per lyric line, plus the instrumental stretches between them
        raw, prev_e = [], 0.0
        for ln in lines:
            if ln["s"] - prev_e > 3.0 or not raw:
                raw.append({"at": 0.0 if not raw else prev_e})
            raw.append({"at": ln["s"]})
            prev_e = ln["e"]
        if end - prev_e > 3.0:
            raw.append({"at": prev_e})
        raw = [r for i, r in enumerate(raw) if i == 0 or r["at"] - raw[i - 1]["at"] > 0.3]
    items = []
    for i, r in enumerate(raw):
        a = float(r["at"])
        e = float(raw[i + 1]["at"]) if i + 1 < len(raw) else float(end)
        if e <= a:
            sys.exit(f"review: shot {i + 1} starts at {a} but the next starts at {e}; shots must be in order")
        t = float(r["t"]) if r.get("t") is not None else a + 0.6 * (e - a)
        t = round(min(max(round(t * fps) / fps, round(a * fps) / fps + 1 / fps), round(e * fps) / fps - 2 / fps), 4)
        n = i + 1
        lyric = r.get("lyric") if r.get("lyric") is not None else _sung(lines, a, e)
        sec = r.get("sec") or _line_sec(lines, a, e) or _section(secs, a + 0.05)
        items.append({
            "id": f"s{n:02d}", "n": n, "label": f"SHOT {n:02d}" + (f" · {sec}" if sec else ""),
            "pos": f"{_tc(a)}–{_tc(e)} · frame {int(round(t * fps))} ({_tc(t)})",
            "start": round(a, 3), "end": round(e, 3), "t": t,
            "title": r.get("title") or (r.get("intent") or "").split(".")[0], "lyric": lyric or "",
            "text": r.get("text", ""), "notes": (r.get("notes") or r.get("intent") or "").strip(),
        })
    return spec, items


def frames_from_video(video, items, imgdir, suffix):
    for it in items:
        dst = os.path.join(imgdir, f"{it['id']}{suffix}.jpg")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{it['t']:.4f}", "-i", video, "-frames:v", "1",
                        "-vf", f"scale={WIDTH}:-2:flags=lanczos", "-q:v", "2", dst], check=True)
        it["src"] = dst


def frames_from_stills(d, items, imgdir, suffix, fps):
    from PIL import Image
    have = {}
    for p in glob.glob(os.path.join(d, "s_*.jpg")) + glob.glob(os.path.join(d, "s_*.png")):
        m = re.match(r"s_([0-9.]+)\.(jpg|png)$", os.path.basename(p))
        if m:
            have[float(m.group(1))] = p
    for it in items:
        k = min(have, key=lambda x: abs(x - it["t"])) if have else None
        if k is None or abs(k - it["t"]) > 0.6 / fps:
            sys.exit(f"review: no still for {it['id']} at {it['t']:.2f}; render the --times list")
        im = Image.open(have[k]).convert("RGB")
        if im.width != WIDTH:
            im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        dst = os.path.join(imgdir, f"{it['id']}{suffix}.jpg")
        im.save(dst, quality=88, optimize=True, progressive=True)
        it["src"] = dst


def images_from_items(spec_path, items, imgdir, suffix):
    from PIL import Image
    base = os.path.dirname(os.path.abspath(spec_path))
    for it in items:
        src = it["img"] if os.path.isabs(it["img"]) else os.path.join(base, it["img"])
        im = Image.open(src).convert("RGB")
        if im.width > WIDTH * 1.5:
            im = im.resize((int(WIDTH * 1.5), round(im.height * WIDTH * 1.5 / im.width)), Image.LANCZOS)
        dst = os.path.join(imgdir, f"{it['id']}{suffix}.jpg")
        im.save(dst, quality=90, optimize=True, progressive=True)
        it["src"] = dst
        if it.get("compare"):            # an image to compare it with (e.g. the current cut's shot), shown small on the card
            cs = it["compare"]["img"]; cs = cs if os.path.isabs(cs) else os.path.join(base, cs)
            ci = Image.open(cs).convert("RGB"); ci.thumbnail((WIDTH, WIDTH))
            cd = os.path.join(imgdir, f"{it['id']}{suffix}_cmp.jpg"); ci.save(cd, quality=86, optimize=True, progressive=True)
            it["compare"] = dict(it["compare"], src=cd)


# ---------------------------------------------------------------- the page
def write_page(out, meta, shown, carried):
    rel = lambda p: os.path.relpath(p, out)
    items = [{k: v for k, v in it.items() if k not in ("src",)} | {"img": rel(it["src"])} for it in shown]
    for it in items:
        if it.get("compare") and it["compare"].get("src"):
            it["compare"] = {k: v for k, v in it["compare"].items() if k != "src"} | {"img": rel(it["compare"]["src"])}
    car = [{"id": c["id"], "label": c.get("label", c["id"]), "title": c.get("title", ""), "img": rel(c["src"])} for c in carried]
    meta = dict(meta, carried=car)
    page = open(os.path.join(HERE, "review_page.html"), encoding="utf-8").read()
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    page = (page.replace("__TITLE__", meta["title"].replace("<", "&lt;"))
                .replace("__META_JSON__", js(meta)).replace("__ITEMS_JSON__", js(items)))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    files = sorted({it["img"] for it in items} | {it["compare"]["img"] for it in items if it.get("compare")} | {c["img"] for c in car} | ({meta["video"]} if meta.get("video") else set()))
    json.dump(files, open(os.path.join(out, "publish_files.json"), "w"), indent=0)
    return files


def load_state(out):
    p = os.path.join(out, "state.json")
    return json.load(open(p)) if os.path.exists(p) else None


def save_state(out, st):
    json.dump(st, open(os.path.join(out, "state.json"), "w"), indent=1, ensure_ascii=False)


def base_meta(song, spec, batch, rnd, n_items):
    heading = spec.get("heading") or spec.get("video") or song["title"]
    return {
        "title": spec.get("page_title") or f"{heading} Review",
        "heading": heading, "round": rnd, "collection": f"round_{rnd}",
        "eyebrow": f"{song['title']} · {batch} · {n_items} items" + (f" · {spec['label']}" if spec.get("label") else ""),
        "covers": spec.get("covers", ""), "key": f"{song['slug']}:{batch}",
        "video": spec.get("preview"), "video_note": spec.get("preview_note", ""), "video_open": bool(spec.get("preview_open")), "top_notes": spec.get("top_notes", []),
    }


def make_items(a, song, batch, imgdir, suffix):
    if batch == "frames" and not a.items:
        spec, items = load_shots(song, a.video)
        if a.times:
            print(" ".join(f"{it['t']:.2f}" for it in items)); sys.exit(0)
        if a.video:
            frames_from_video(a.video, items, imgdir, suffix)
        elif a.stills:
            frames_from_stills(a.stills, items, imgdir, suffix, spec.get("fps", FPS_DEFAULT))
        else:
            sys.exit("review: give --video <render> or --stills <dir>")
        return spec, items
    if not a.items:
        sys.exit("review: give --items <items.yaml> for this batch")
    spec = yaml.safe_load(open(a.items))
    items = [dict(x) for x in spec["items"]]
    for i, it in enumerate(items):
        it.setdefault("label", it["id"].upper())
        it.setdefault("n", i + 1)
    images_from_items(a.items, items, imgdir, suffix)
    return spec, items


# ---------------------------------------------------------------- the answers
def read_answers(path):
    a = json.load(open(path))
    docs = a.get("documents", a) if isinstance(a, dict) else a
    if isinstance(docs, dict):
        return docs
    return {(d.get("id") or d.get("doc_id")): (d.get("data") or d) for d in docs}


def answers(out, st, path):
    rnd = st["round"]
    d = read_answers(path)
    os.makedirs(os.path.join(out, f"round_{rnd}"), exist_ok=True)
    shutil.copyfile(path, os.path.join(out, f"round_{rnd}", "answers.json")) if os.path.abspath(path) != os.path.abspath(os.path.join(out, f"round_{rnd}", "answers.json")) else None
    fix, qs, ok_notes, open_ = [], [], [], []
    for iid in st["shown"]:
        it, v = st["items"][iid], d.get(iid) or {}
        dec, note = v.get("decision", ""), (v.get("note") or "").strip()
        it["note"] = note
        it["status"] = {"approve": "approved", "changes": "changes"}.get(dec, "open")
        row = f"- **{it['label']}** {it.get('title', '')}" + (f": {note}" if note else "")
        (fix if dec == "changes" else ok_notes if (dec == "approve" and note) else open_ if not dec else []).append(row)
        if "?" in note:
            qs.append(row)
    ov = (d.get("_overall") or {}).get("note", "").strip()
    st["overall"] = ov
    save_state(out, st)
    n_ok = sum(1 for x in st["items"].values() if x["status"] == "approved")
    md = [f"# Review round {rnd}", "",
          f"{len(st['items'])} items: {n_ok} approved, {len(fix)} need changes, {len(open_)} not reviewed.", "",
          "## Needs changes", *(fix or ["- (none)"]), ""]
    if qs:
        md += ["## Questions to answer", *qs, ""]
    if ok_notes:
        md += ["## Approved, with a note", *ok_notes, ""]
    if open_:
        md += ["## Not reviewed yet", *open_, ""]
    if ov:
        md += ["## Overall", ov, ""]
    p = os.path.join(out, f"REVIEW_round_{rnd}.md")
    open(p, "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(md)); print(f"wrote {p}")


def save_approved(song, out, st, batch):
    not_ok = [x["label"] for x in st["items"].values() if x["status"] != "approved"]
    if not_ok:
        sys.exit(f"review: not everything is approved yet ({len(not_ok)} left: {', '.join(not_ok[:8])}…)")
    dst = os.path.join(song["out_dir"], "Approved", batch)
    os.makedirs(dst, exist_ok=True)
    for iid, it in st["items"].items():
        safe = re.sub(r'[\\/:*?"<>|]', "-", it.get("title", ""))[:60].strip()
        shutil.copyfile(os.path.join(out, it["img"]), os.path.join(dst, f"{iid} - {safe}.jpg"))
    print(f"saved {len(st['items'])} approved images -> {dst}")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("song_dir")
    ap.add_argument("batch", nargs="?", default="frames")
    ap.add_argument("--video"); ap.add_argument("--stills"); ap.add_argument("--items")
    ap.add_argument("--times", action="store_true")
    ap.add_argument("--answers"); ap.add_argument("--next"); ap.add_argument("--save-approved", action="store_true")
    a = ap.parse_args()

    song = config.load_song(a.song_dir)
    out = os.path.join(song["build"], "review", a.batch)
    imgdir = os.path.join(out, "img")
    os.makedirs(imgdir, exist_ok=True)
    st = load_state(out)

    if a.answers:
        return answers(out, st, a.answers)
    if a.save_approved:
        return save_approved(song, out, st, a.batch)

    if not a.next:                                   # round 1
        spec, items = make_items(a, song, a.batch, imgdir, "_r1")
        st = {"round": 1, "batch": a.batch, "shown": [it["id"] for it in items], "items": {}}
        for it in items:
            st["items"][it["id"]] = {"label": it["label"], "title": it["title"], "status": "open", "note": "",
                                     "img": os.path.relpath(it["src"], out), "md5": _md5(it["src"])}
        meta = base_meta(song, spec, a.batch, 1, len(items))
        files = write_page(out, meta, items, [])
        save_state(out, st)
        print(f"round 1: {len(items)} items -> {out}/index.html; publish with files: {len(files)} paths (publish_files.json)")
        return

    # next round: rebuild everything, show only what changed or was put back up
    if not st:
        sys.exit("review: no earlier round here")
    ch = yaml.safe_load(open(a.next)) or {}
    changed, reopened = ch.get("changed") or {}, ch.get("reopened") or {}
    rnd = st["round"] + 1
    spec, items = make_items(a, song, a.batch, imgdir, f"_r{rnd}")
    shown, carried = [], []
    for it in items:
        prev = st["items"].get(it["id"], {"status": "open", "note": ""})
        new_md5 = _md5(it["src"])
        if it["id"] in changed or it["id"] in reopened or prev["status"] != "approved":
            if prev["status"] == "changes" and it["id"] not in changed:
                print(f"warning: {it['id']} was marked Needs changes but changes.yaml doesn't say what changed")
            it["changed"] = changed.get(it["id"], "Nothing yet" if prev["status"] == "changes" else "")
            it["reopened"] = reopened.get(it["id"], "")
            it["last"] = "Approved" if prev["status"] == "approved" else (prev["note"] or ("(no note)" if prev["status"] == "changes" else "Not reviewed yet"))
            shown.append(it)
            st["items"][it["id"]] = {"label": it["label"], "title": it["title"], "status": "open", "note": "",
                                     "img": os.path.relpath(it["src"], out), "md5": new_md5}
        else:                                        # approved and unchanged: keep its approved image
            it["src"] = os.path.join(out, prev["img"])
            carried.append(it)
    st.update(round=rnd, shown=[it["id"] for it in shown])
    meta = base_meta(song, spec, a.batch, rnd, len(items))
    notes = list(ch.get("top_notes") or [])
    if carried:
        notes.insert(0, {"kind": "ok", "text": f"{len(carried)} items you approved haven't changed and stay approved (listed under the tally)."})
    if reopened:
        notes.insert(1, {"kind": "chg", "text": f"{len(reopened)} approved items are back up because a change affects them; each card says why."})
    meta["top_notes"] = notes + meta["top_notes"]
    files = write_page(out, meta, shown, carried)
    save_state(out, st)
    print(f"round {rnd}: {len(shown)} to review, {len(carried)} carried as approved -> {out}/index.html ({len(files)} files)")


if __name__ == "__main__":
    main()
