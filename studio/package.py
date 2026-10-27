"""Step 6 — package: all titles, descriptions, tags, captions + upload checklist.

usage: python -m studio.package songs/<slug>
Reads song.yaml (creative copy written per song), build/{sections,timed,clips}.json.
Writes  <output folder>/<Title> - copy.md   (copy-paste ready, one code block per field)
        songs/<slug>/build/package.json      (machine-readable, used by tools/youtube_upload.py)
"""
import os, sys, json
from .config import load_song, CFG, public_name, doompop, doompop_title, doompop_desc, doompop_tags, DOOMPOP_TAGS

def mmss(t): t = int(t); return f"{t // 60}:{t % 60:02d}"

import re
def fill_links(text, links):
    """Copy can contain {name|fallback}: replaced by links[name] when set (e.g. the Fable version's URL), else the fallback.
    {FULL_VIDEO_URL} is left for tools/youtube_upload.py, which knows the full video's URL once it is uploaded."""
    return re.sub(r"\{(\w+)\|([^}]*)\}", lambda m: (links or {}).get(m.group(1)) or m.group(2), text or "")

def lyrics_block(song_dir):
    out, prev_blank = [], True
    for l in open(os.path.join(song_dir, "lyrics.txt")):
        l = l.rstrip()
        if l.startswith("#"):
            if not prev_blank: out.append(""); prev_blank = True
            continue
        if l: out.append(l); prev_blank = False
    return "\n".join(out).strip()

def chapters(song, secs, lines):
    yt = song.get("youtube", {}); cm = yt.get("chapters", {}); marks = []
    for s in secs:   # priority 2 = song sections, 1 = extra lyric marks
        if s["name"] in cm: marks.append((s["s"] if s["name"] != "INTRO" else 0.0, cm[s["name"]], 2.5 if s["kind"] == "chorus" else 2))
    for x in yt.get("extra_chapters", []):
        hit = [L for L in lines if x["line"].lower() in L["text"].lower()]
        if hit: marks.append((max(0.0, hit[0]["s"] - 0.3), x["label"], 1))
    marks.sort()
    if not marks or marks[0][0] > 0.5: marks.insert(0, (0.0, marks[0][1] if marks and marks[0][0] < 3 else "Intro", 3))
    else: marks[0] = (0.0, marks[0][1], 3)
    # YouTube needs >= 10 s between chapters: drop the lower-priority mark of any close pair
    changed = True
    while changed:
        changed = False
        for i in range(1, len(marks)):
            if marks[i][0] - marks[i - 1][0] < 10:
                drop = i if marks[i][2] <= marks[i - 1][2] else i - 1
                marks.pop(drop); changed = True; break
    return [(t, lab) for t, lab, _ in marks]

def build(song_dir):
    song = load_song(song_dir); b = song["build"]; yt = song.get("youtube", {}); ig = song.get("instagram", {})
    secs = json.load(open(os.path.join(b, "sections.json"))); lines = json.load(open(os.path.join(b, "timed.json")))
    clips = json.load(open(os.path.join(b, "clips.json"))) if os.path.exists(os.path.join(b, "clips.json")) else {"clips": []}
    artist = CFG.get("artist", "aditazzz"); model = song["model_credit"]; T = song["title"]
    long_title = yt.get("title") or f"{public_name(song)} - {model} Music Video"   # no (…) in titles: keeps "Claude" visible
    dp = doompop(song)   # AI Doompop songs: "#AIDoompop" in titles and hashtags, "ai doompop" in tags (studio.yaml doompop:)
    if dp: long_title = doompop_title(long_title)
    chs = chapters(song, secs, lines)
    handle = CFG.get("channel_handle", "@adita_zzz"); sub_url = f"https://www.youtube.com/{handle}?sub_confirmation=1"
    pinned = fill_links(yt.get("pinned", "").strip(), song.get("links", {}))
    if "sub_confirmation" not in pinned: pinned += f"\n\n🔔 Subscribe so you don't miss the next one: {sub_url}"
    claude_made = not yt.get("credit")
    hs = list(yt.get("hashtags", []))
    if claude_made: hs = hs[:1] + ["ClaudeAI", "AIMusicVideo"] + hs[1:]
    tags3 = " ".join("#" + h for h in hs[:int(yt.get("hashtag_count", 3))])   # song.yaml youtube.hashtag_count: more topic hashtags
    made_with = numbers = ""
    if claude_made:
        made_with = ("MADE WITH\nSong: Suno (lyrics, concept and direction by " + artist + ")\n"
                     f"Animation, editing, timing and kinetic type: {model}, every frame rendered from code\n\n")
        try:
            scene_lines = sum(sum(1 for _ in open(os.path.join(song["dir"], f))) for f in os.listdir(song["dir"]) if f.endswith(".py"))
            for wd in ("web_dev", "web"):   # a 3D film's source (three.js); web_dev is the live copy of web, so count one
                wp = os.path.join(song["dir"], wd)
                if not os.path.isdir(wp): continue
                for r, ds, fs in os.walk(wp):
                    ds[:] = [d for d in ds if d != "node_modules"]
                    scene_lines += sum(sum(1 for _ in open(os.path.join(r, f))) for f in fs if f.endswith((".js", ".mjs", ".html")))
                break
            bt = json.load(open(os.path.join(b, "beats.json"))); frames = int((bt["duration"] + float(song.get("tail", 0))) * 30) * 2
            words = sum(len(L["words"]) for L in lines)
            numbers = (f"BY THE NUMBERS\n{scene_lines:,} lines of scene code written for this song\n{frames:,} frames rendered (16:9 + 9:16)\n"
                       f"{len(lines)} lyric lines and {words} words synced to the vocal\n{len(secs)} sections, every cut timed to the song\n\n")
        except Exception: pass
    credit_line = (yt['credit'].strip() + " ") if yt.get('credit') else (yt['story'].strip() + " ") if yt.get('story') else f"Every frame was written as code by {model}, all synced to the vocals: {yt.get('visuals', '').strip()}. "
    links = song.get("links", {}) or {}
    intro = fill_links(yt.get("intro", "").strip(), links)
    code_line = ""   # the video's own code on GitHub (studio.yaml code_repo + code_songs)
    if CFG.get("code_repo") and song["slug"] in (CFG.get("code_songs") or []):
        code_line = f"💻 Every line of code behind this video is open source: {CFG['code_repo'].rstrip('/')}/tree/main/songs/{song['slug']}\n\n"
    news = fill_links(" ".join(yt.get("news", "").split()), links)   # a topical song: the story it's about, in a few sentences
    desc = ((intro + "\n\n" if intro else "") + f"{yt.get('hook', '').strip()}\n\n"
            + (f"THE NEWS BEHIND THE SONG\n{news}\n\n" if news else "")
            + f"{credit_line}"
            f"Song, lyrics and concept by {artist}.\n\n{code_line}"
            f"💬 {yt.get('question', 'What did you think?')} 👇\n"
            f"🔔 Subscribe so you don't miss the next one: {sub_url}\n"
            f"▶️ The whole series of music videos made by Claude: {CFG.get('playlist', '')}\n\n"
            f"🎵 Spotify: {CFG.get('spotify', '')}\n📸 Instagram: {CFG.get('instagram', '')}\n"
            + (f"👽 AI Doompop on Reddit: {CFG['reddit']}\n" if CFG.get('reddit') else "")
            + (f"🔗 All my links: {CFG['linktree']}\n" if CFG.get('linktree') else "") + "\n"
            + (f"{fill_links(yt['note'].strip(), links)}\n\n" if yt.get("note") else "")
            + made_with + numbers
            + ((yt.get("pause_line") or "⏸ Pause anywhere: the screens are full of hidden jokes.") + "\n\n" if yt.get("hidden_jokes", claude_made) else "")
            + "CHAPTERS\n" + "\n".join(f"{mmss(t)} {lab}" for t, lab in chs) + "\n\n"
            + "LYRICS\n" + lyrics_block(song_dir) + "\n\n" + tags3)
    if dp: desc = doompop_desc(desc, long_title)
    if code_line and len(desc) > 5000: desc = desc.replace(code_line, "", 1)   # YouTube's limit: drop the code line rather than the lyrics
    tags = list(dict.fromkeys([*(DOOMPOP_TAGS if dp else []), *yt.get("tags", []), model.lower(), "claude ai", artist]))
    ytlen = lambda ts: sum(len(t) + (2 if " " in t else 0) for t in ts) + max(0, len(ts) - 1)   # YouTube quotes tags with spaces
    while ytlen(tags) > 480: tags.pop(-4)
    pkg = {"title": T, "long": {"file": f"{T} - YouTube 16x9.mp4", "title": long_title, "description": desc, "tags": tags,
                                 "thumbnail": f"{T} - YouTube thumbnail.jpg", "pinned_comment": pinned,
                                 "synthetic": bool(song.get("ai_music", True)), "category": 10}, "shorts": [], "reels": []}
    short_tags = " ".join("#" + h for h in (yt.get("short_hashtags") or yt.get("hashtags", []))[:5])
    ig_credit = yt.get("credit_short") or "Every frame of this video is code written by Claude."
    ig_tail = lambda cap: (f"{cap}\n\n{ig_credit} Full video on YouTube, link in bio 🎵 {artist}"
                           + "\n" * 6 + " ".join("#" + h for h in ig.get("hashtags", [])[:5]) + "\n" * 6
                           + ", ".join([*ig.get("keywords", []), artist]))
    cc = song.get("clip_copy", {})
    for c in clips.get("clips", []):
        cp = cc.get(c["label"], {}); hook = cp.get("hook", yt.get("hook", "").split(".")[0] + ".")
        full_name = public_name(song)
        if cp.get("yt_description"):
            d = fill_links(cp["yt_description"].strip(), links).replace("{SUB_URL}", sub_url)
        else:
            d = (f"{hook} {yt.get('credit_short') or 'Every frame is code written by ' + model + '.'}\n\nFull music video: \"{full_name}\" {{FULL_VIDEO_URL}}"
                 f"\n💬 {yt.get('question', '')} 👇\n🔔 Subscribe so you don't miss the next one: {sub_url}\n\n{short_tags}")
        yt_title = cp.get("yt_title", f"{T} — {c['label']}"); yt_tags = cp.get("yt_tags") or tags
        if dp: yt_title = doompop_title(yt_title); d = doompop_desc(d, yt_title); yt_tags = doompop_tags(yt_tags)
        entry = {"file": c.get("file"), "kind": c["kind"], "label": c["label"], "start": c["start"], "end": c["end"],
                 "yt_title": yt_title, "yt_description": d,
                 "yt_tags": yt_tags, "ig_caption": cp.get("ig_full") or ig_tail(cp.get("ig", hook)), "synthetic": pkg["long"]["synthetic"]}
        if c.get("file"):   # YouTube copy whose end card says subscribe (tools/yt_short_endcard.py); Reels go up as Shorts too
            yf = os.path.splitext(c["file"])[0] + " (YouTube).mp4"
            if os.path.exists(os.path.join(song["out_dir"], yf)): entry["yt_file"] = yf
        if yt.get("short_pinned"):
            entry["pinned_comment"] = fill_links(cp.get("pinned") or yt["short_pinned"], links).replace("{SUB_URL}", sub_url).strip()
        (pkg["shorts"] if c["kind"] == "short" else pkg["reels"]).append(entry)
    if clips.get("edit"):
        hero = cc.get("chorus", {}).get("ig") or yt.get("hook", "")
        pkg["instagram_full"] = {"file": clips["edit"]["file"], "ig_caption": fill_links(ig.get("edit_caption", ""), links) or ig_tail(hero)}
    json.dump(pkg, open(os.path.join(b, "package.json"), "w"), indent=1, ensure_ascii=False)
    write_md(song, pkg)

def block(s): return "```\n" + s.strip("\n") + "\n```\n"

def write_md(song, pkg):
    L = pkg["long"]; out = [f"# {pkg['title']} — release copy\n",
        "## YouTube — full music video\n", f"File: `{L['file']}`  ·  Thumbnail: `{L['thumbnail']}`\n",
        "**Title**\n", block(L["title"]), "**Description**\n", block(L["description"]),
        f"**Tags** ({len(', '.join(L['tags']))} characters)\n", block(", ".join(L["tags"])),
        "**Pinned comment**\n", block(L["pinned_comment"])]
    for kind, items in (("YouTube / Instagram — Shorts", pkg["shorts"]), ("YouTube / Instagram — Reels", pkg["reels"])):
        for c in items:
            out += [f"## {c['file'] or c['label']}\n", f"From {mmss(c['start'])} to {mmss(c['end'])} of the song.\n",
                    "**YouTube title**\n", block(c["yt_title"]), "**YouTube description**\n", block(c["yt_description"].replace("{FULL_VIDEO_URL}", "on my channel 🎵")),
                    "**YouTube tags**\n", block(", ".join(c["yt_tags"])), "**Instagram caption**\n", block(c["ig_caption"])]
    if pkg.get("instagram_full"):
        out += [f"## {pkg['instagram_full']['file']}\n", "**Instagram caption**\n", block(pkg["instagram_full"]["ig_caption"])]
    out += ["## Upload checklist\n",
            "- [ ] YouTube: upload the 16:9 file as a normal video (16:9 keeps it out of Shorts).",
            f"- [ ] YouTube: {'tick **Altered or synthetic content = Yes** (AI-generated music must be disclosed; it does not reduce reach)' if L['synthetic'] else 'synthetic-content disclosure not needed'}.",
            "- [ ] YouTube: category Music, add to the “Music videos made by Claude” playlist.",
            f"- [ ] YouTube end screen (from {mmss(song.get('end_screen_at', 0))} to the end): **Subscribe** element + **Best for viewer** video, both on the RIGHT half; the left half has the on-screen subscribe card.",
            "- [ ] YouTube: Test & Compare with the thumbnail + the no-text version (winner is picked by watch time).",
            "- [ ] YouTube: post and pin the pinned comment right after publishing.",
            "- [ ] Shorts: keep under 60 s (Content ID blocks longer Shorts with claims), set **Related video** → the full video (desktop Studio).",
            "- [ ] Shorts: pick the cover frame at the start of the clip (the hero clips open on it).",
            "- [ ] Instagram: post the under-3-min version as the full Reel (only ≤3:00 is recommended to non-followers).",
            "- [ ] Instagram: try 1–2 clips as Trial Reels first; invite relevant accounts as collaborators; set the cover image.",
            "- [ ] Space releases out: 3–5 vertical clips a week, one long video every 1–2 weeks (see PLAYBOOK.md)."]
    p = os.path.join(song["out_dir"], f"{pkg['title']} - copy.md"); os.makedirs(song["out_dir"], exist_ok=True)
    open(p, "w").write("\n".join(out) + "\n"); print("wrote", p)

if __name__ == "__main__":
    build(sys.argv[1])
