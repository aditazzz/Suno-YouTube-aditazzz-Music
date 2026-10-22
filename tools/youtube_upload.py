#!/usr/bin/env python3
"""Post finished songs to YouTube — run this in your own terminal (it uses your Google sign-in, which only you do).

Nothing goes public unless the plan says when:
  * every video is uploaded PRIVATE; a time in the plan makes YouTube publish it then (a draft stays private)
  * or give a song (or its clips:) `privacy: unlisted` to upload those as UNLISTED (link-only) with no publish time
  * you see the full review (titles, times, files) and must type "upload" before anything is sent
  * every upload is recorded in songs/<slug>/build/uploads.json, so nothing is ever uploaded twice

Usual use:
  python3 tools/youtube_upload.py --plan release_plan.yaml --dry-run     # just show the plan, no sign-in
  python3 tools/youtube_upload.py --plan release_plan.yaml               # review, type "upload", go

Later:
  python3 tools/youtube_upload.py --status                                # what's uploaded / scheduled / live
  python3 tools/youtube_upload.py songs/<slug> --update                   # re-send titles/descriptions/tags (e.g. after
                                                                          #   adding the Fable link to song.yaml → links)
  python3 tools/youtube_upload.py songs/<slug> --publish-now              # make its scheduled/private uploads public now
  python3 tools/youtube_upload.py songs/<slug> --go-live                  # final copy + publish now + pinned comments
  python3 tools/youtube_upload.py --doompop                               # tag the AI Doompop songs' videos + Shorts #AIDoompop
  python3 tools/youtube_upload.py songs/<slug> --post-comments            # once the full video is public: post the
                                                                          #   pinned comment (then tap Pin in YouTube)

One-time setup: docs/publishing.md (Google Cloud project + OAuth client JSON in secrets/).
YouTube allows about 100 API uploads a day (Dec 2025); the other calls share 10,000 units. If a limit is hit, run the same command tomorrow — it continues.
"""
import os, re, sys, json, argparse, glob, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from studio.config import load_song, CFG, public_name, doompop, doompop_title, doompop_desc, doompop_tags  # noqa: E402

SECRETS = os.path.join(ROOT, "secrets")
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]
DEFAULT_TZ = "America/Los_Angeles"

# ---------------------------------------------------------------- Google sign-in (yours, in your browser)
def service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    tok = os.path.join(SECRETS, "yt_token.json"); creds = None
    if os.path.exists(tok): creds = Credentials.from_authorized_user_file(tok, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try: creds.refresh(Request())
            except Exception: creds = None
        if not creds or not creds.valid:
            cs = os.path.join(SECRETS, "client_secret.json")
            if not os.path.exists(cs):
                sys.exit("Missing secrets/client_secret.json — see docs/publishing.md (one-time setup).")
            flow = InstalledAppFlow.from_client_secrets_file(cs, SCOPES)
            creds = flow.run_local_server(port=0)   # opens your browser; you sign in yourself
        open(tok, "w").write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

# ---------------------------------------------------------------- tags (YouTube counts quotes around tags with spaces)
def yt_tag_len(tags): return sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags) - 1)
def clean_tags(tags, limit=490):
    out = []
    for t in tags or []:
        t = " ".join(str(t).replace("<", "").replace(">", "").replace(",", " ").split())
        if t and len(t) <= 100 and t.lower() not in {x.lower() for x in out}: out.append(t)
    while out and yt_tag_len(out) > limit: out.pop()          # the list is ordered most-important first
    return out

# ---------------------------------------------------------------- records
def rec_path(song): return os.path.join(song["build"], "uploads.json")
def load_rec(song):
    p = rec_path(song); r = json.load(open(p)) if os.path.exists(p) else {}
    return {k: (v if isinstance(v, dict) else {"id": v}) for k, v in r.items()}
def save_rec(song, r): json.dump(r, open(rec_path(song), "w"), indent=1, ensure_ascii=False)
def load_pkg(song):
    pkg = json.load(open(os.path.join(song["build"], "package.json")))
    for c in pkg.get("shorts", []) + pkg.get("reels", []):   # YouTube gets the copy whose end card says subscribe, not follow on Instagram
        if c.get("yt_file"): c["file"] = c["yt_file"]
    return pkg

# ---------------------------------------------------------------- time
def to_utc_iso(local, tz):
    from zoneinfo import ZoneInfo
    if isinstance(local, dt.datetime): t = local
    else: t = dt.datetime.fromisoformat(str(local).strip().replace(" ", "T"))
    if t.tzinfo is None: t = t.replace(tzinfo=ZoneInfo(tz))
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), t

def nice(t): return t.strftime("%a %b %d, %-I:%M %p %Z") if t else "private draft"

# ---------------------------------------------------------------- jobs
def clip_jobs(pkg, order=None):
    clips = [dict(c, kind=c.get("kind", "short")) for c in pkg.get("shorts", []) + pkg.get("reels", [])]
    if order:
        idx = {lab: i for i, lab in enumerate(order)}
        clips = [c for c in clips if c["label"] in idx]; clips.sort(key=lambda c: idx[c["label"]])
    else: clips.sort(key=lambda c: c.get("start", 0))
    return clips

def build_jobs(entry, tz):
    """One plan entry -> list of (song, kind, meta, publish_utc, publish_local)."""
    song = load_song(os.path.join(ROOT, entry["song"]) if not os.path.isabs(entry["song"]) else entry["song"])
    pkg = load_pkg(song); jobs = []
    inc = entry.get("include", ["long", "clips"])
    if "long" in inc and entry.get("full_video", "draft") != "skip":
        fv = entry.get("full_video", "draft"); pu, pl = (None, None) if fv in (None, "draft") else to_utc_iso(fv, tz)
        jobs.append((song, "long", dict(pkg["long"], privacy=entry.get("privacy")), pu, pl))
    if "clips" in inc and entry.get("clips") != "skip":
        cl = entry.get("clips") or {}; start = cl.get("start"); every = float(cl.get("every_days", 2)); times = cl.get("times") or []
        for i, c in enumerate(clip_jobs(pkg, cl.get("order"))):
            if i < len(times): pu, pl = to_utc_iso(times[i], tz)
            elif start: pu, pl = to_utc_iso(dt.datetime.fromisoformat(str(start).replace(" ", "T")) + dt.timedelta(days=every * i), tz)
            else: pu, pl = None, None
            jobs.append((song, "clip", dict(c, privacy=cl.get("privacy") or entry.get("privacy")), pu, pl))
    return jobs

def fill_full_url(text, song, rec, pkg):
    lid = rec.get(pkg["long"]["file"], {}).get("id")
    return text.replace("{FULL_VIDEO_URL}", f"▶️ https://youtu.be/{lid}" if lid else "on my channel 🎵")

def check(song, kind, meta, problems):
    path = os.path.join(song["out_dir"], meta["file"] or "")
    title = meta["title"] if kind == "long" else meta["yt_title"]
    desc = meta["description"] if kind == "long" else meta["yt_description"]
    tags = meta["tags"] if kind == "long" else meta["yt_tags"]
    if not meta.get("file") or not os.path.exists(path): problems.append(f"missing file: {path}")
    if len(title) > 100: problems.append(f"title over 100 characters: {title}")
    if len(desc) > 5000: problems.append(f"description over 5000 characters ({len(desc)}): {meta['file']}")
    if yt_tag_len(clean_tags(tags)) > 500: problems.append(f"tags over 500 characters: {meta['file']}")
    if "<" in desc or ">" in desc: problems.append(f"description contains < or > (YouTube rejects them): {meta['file']}")
    if kind == "long":
        th = os.path.join(song["out_dir"], meta.get("thumbnail", ""))
        if os.path.exists(th) and os.path.getsize(th) > 2_000_000: problems.append(f"thumbnail over 2 MB: {th}")
    return path, title, desc, tags

# ---------------------------------------------------------------- YouTube calls
def do_upload(yt, path, title, desc, tags, publish_utc, synthetic=True, category=10, privacy="private"):
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    body = {"snippet": {"title": title[:100], "description": desc[:5000], "tags": clean_tags(tags), "categoryId": str(category),
                        "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False, "containsSyntheticMedia": bool(synthetic)}}
    if publish_utc: body["status"]["publishAt"] = publish_utc
    def send(b):
        req = yt.videos().insert(part="snippet,status", body=b, media_body=MediaFileUpload(path, chunksize=8 * 1024 * 1024, resumable=True))
        resp = None
        while resp is None:
            st, resp = req.next_chunk()
            if st: print(f"    {int(st.progress() * 100)}%", end="\r", flush=True)
        return resp
    try: resp = send(body)
    except HttpError as e:
        if "containsSyntheticMedia" in str(e):
            print("    (this API version doesn't take the AI-disclosure flag — set 'Altered or synthetic content' in Studio)")
            body["status"].pop("containsSyntheticMedia", None); resp = send(body)
        else: raise
    return resp["id"]

def is_quota(e): return "quota" in str(e).lower()

def playlist_ok(yt, pid):
    if not pid: return False
    try: return bool(yt.playlists().list(part="id", id=pid).execute().get("items"))
    except Exception: return False

# ---------------------------------------------------------------- commands
def run_plan(plan_path, dry, yes):
    import yaml
    plan = yaml.safe_load(open(plan_path)); tz = plan.get("timezone", DEFAULT_TZ)
    for ap in plan.get("already_posted") or []:     # things posted by hand: record them so they're never re-uploaded
        song = load_song(os.path.join(ROOT, ap["song"])); rec = load_rec(song)
        vid = str(ap.get("url", "")).rstrip("/").split("/")[-1].split("v=")[-1]
        if ap["file"] not in rec: rec[ap["file"]] = {"id": vid, "note": "posted by hand"}; save_rec(song, rec)
    jobs = [j for e in plan.get("songs") or [] for j in build_jobs(e, tz)]
    problems, todo = [], []
    print(f"\nRELEASE PLAN  ({plan_path}, times in {tz})\n")
    for song, kind, meta, pu, pl in jobs:
        rec = load_rec(song)
        path, title, desc, tags = check(song, kind, meta, problems)
        priv = meta.get("privacy") or "private"
        state = "already uploaded → skip" if meta["file"] in rec else ("PUBLIC at " + nice(pl) if pl else ("UNLISTED (link only)" if priv == "unlisted" else "PUBLIC now" if priv == "public" else "private draft"))
        if priv not in ("private", "unlisted", "public"): problems.append(f"privacy must be private, unlisted or public: {meta['file']}")
        if pl and priv != "private": problems.append(f"a publish time only works with privacy: private (YouTube publishes it then): {meta['file']}")
        print(f"  [{song['title']}] {'FULL VIDEO' if kind == 'long' else 'Short'}: {title}\n      {meta['file']}\n      {state}")
        if meta["file"] not in rec: todo.append((song, kind, meta, pu, pl))
    now = dt.datetime.now(dt.timezone.utc)
    for song, kind, meta, pu, pl in todo:
        if pu and dt.datetime.strptime(pu, "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=dt.timezone.utc) < now + dt.timedelta(minutes=15):
            problems.append(f"publish time is in the past / too soon: {meta['file']} ({nice(pl)})")
    if len(todo) > 90: print(f"\n  Note: {len(todo)} uploads. YouTube allows about 100 API uploads a day; the rest continue when you run this again tomorrow.")
    if problems:
        print("\nFIX FIRST:"); [print("  - " + p) for p in problems]; sys.exit(1)
    if not todo: print("\nNothing new to upload."); return
    if dry: print("\n(dry run: nothing sent)"); return
    if not yes:
        ans = input(f"\nType  upload  to send these {len(todo)} video(s) to YouTube as scheduled above: ").strip().lower()
        if ans != "upload": print("Cancelled. Nothing was sent."); return
    yt = service(); pid = plan.get("playlist_id") or CFG.get("playlist_id"); pl_ok = playlist_ok(yt, pid)
    if pid and not pl_ok: print(f"  (playlist {pid} not found on your channel — skipping playlist; fix playlist_id in studio.yaml)")
    for song, kind, meta, pu, pl in sorted(todo, key=lambda j: j[1] != "long"):   # full videos first, so Shorts can link to them
        rec = load_rec(song); pkg = load_pkg(song)
        path, title, desc, tags = check(song, kind, meta, [])
        desc = fill_full_url(desc, song, rec, pkg)
        priv = meta.get("privacy") or "private"
        print(f"\n  uploading {meta['file']}  ({priv if priv != 'private' else nice(pl)})")
        try: vid = do_upload(yt, path, title, desc, tags, pu, meta.get("synthetic", True), meta.get("category", 10), priv)
        except Exception as e:
            if is_quota(e): print("\n  YouTube's daily upload quota is used up. Run the same command tomorrow — it picks up where it stopped."); return
            raise
        rec[meta["file"]] = {"id": vid, "publish_at": pl.isoformat() if pl else None, "title": title, "privacy": priv}; save_rec(song, rec)
        print(f"    done: https://youtu.be/{vid}")
        if kind == "long":
            th = os.path.join(song["out_dir"], meta.get("thumbnail", ""))
            if os.path.exists(th):
                from googleapiclient.http import MediaFileUpload
                try: yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(th)).execute(); print("    thumbnail set")
                except Exception as e: print("    thumbnail not set (the channel may need phone verification):", str(e)[:120])
            if pl_ok and priv == "unlisted":   # a public playlist would show it to everyone; --publish-now adds it later
                rec[meta["file"]]["playlist"] = False; save_rec(song, rec)
                print("    kept out of the playlist while it's unlisted (--publish-now adds it)")
            elif pl_ok:
                try: yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute(); print("    added to playlist")
                except Exception as e: print("    not added to playlist:", str(e)[:120])
    print("\nAll set. Still done by hand in YouTube Studio: pin the comment (or run --post-comments once it's public),"
          " each Short's Related video, end screens, Test & Compare thumbnails.")

def songs_from(args):
    if args.song_dir: return [load_song(args.song_dir)]
    return [load_song(os.path.dirname(os.path.dirname(p))) for p in sorted(glob.glob(os.path.join(ROOT, "songs", "*", "build", "uploads.json")))]

def cmd_status(args):
    sg = songs_from(args); yt = service()
    for song in sg:
        rec = load_rec(song)
        if not rec: continue
        print(f"\n{song['title']}")
        ids = [v["id"] for v in rec.values() if v.get("id")]
        info = {}
        for i in range(0, len(ids), 50):
            for it in yt.videos().list(part="status,statistics", id=",".join(ids[i:i + 50])).execute().get("items", []): info[it["id"]] = it
        for f, v in rec.items():
            it = info.get(v["id"]); st = it["status"] if it else {}
            when = st.get("publishAt", "")
            print(f"  {st.get('privacyStatus', '?'):8} {('publishes ' + when) if when and st.get('privacyStatus') == 'private' else '':34} "
                  f"{it['statistics'].get('viewCount', '0') + ' views' if it else '(not found)':12} {f}")

def cmd_update(args):
    yt = service()
    for song in songs_from(args):
        rec = load_rec(song); pkg = load_pkg(song)
        metas = {pkg["long"]["file"]: ("long", pkg["long"])}
        metas.update({c["file"]: ("clip", c) for c in pkg.get("shorts", []) + pkg.get("reels", [])})
        for f, v in rec.items():
            if f not in metas: continue
            kind, meta = metas[f]
            if getattr(args, "only", None) and kind != args.only: continue
            title = meta["title"] if kind == "long" else meta["yt_title"]
            desc = fill_full_url(meta["description"] if kind == "long" else meta["yt_description"], song, rec, pkg)
            tags = meta["tags"] if kind == "long" else meta["yt_tags"]
            items = yt.videos().list(part="snippet", id=v["id"]).execute().get("items", [])
            if not items: print(f"  not found on YouTube: {f}"); continue
            sn = items[0]["snippet"]; sn.update({"title": title[:100], "description": desc[:5000], "tags": clean_tags(tags)})
            if args.dry_run: print(f"  [dry-run] would update {f}"); continue
            yt.videos().update(part="snippet", body={"id": v["id"], "snippet": sn}).execute(); print(f"  updated {f}")

def cmd_comments(args):
    """Post each public upload's pinned comment (full video + Shorts), unless you already commented on it. Then tap Pin."""
    yt = service()
    for song in songs_from(args):
        rec = load_rec(song); pkg = load_pkg(song)
        metas = {pkg["long"]["file"]: pkg["long"]}
        metas.update({c["file"]: c for c in pkg.get("shorts", []) + pkg.get("reels", [])})
        ids = {v["id"]: f for f, v in rec.items() if v.get("id") and f in metas}
        if not ids: continue
        info = {it["id"]: it for it in yt.videos().list(part="status,snippet", id=",".join(ids)).execute().get("items", [])}
        for vid, f in ids.items():
            v = rec[f]; meta = metas[f]; it = info.get(vid)
            name = meta.get("title") or meta.get("yt_title") or f
            if not meta.get("pinned_comment"): continue
            if v.get("comment_id"): print(f"  comment already posted: {name}"); continue
            if not it or it["status"].get("privacyStatus") not in ("public", "unlisted"): print(f"  not public yet, skipped: {name}"); continue
            owner = it["snippet"]["channelId"]
            try:
                existing = yt.commentThreads().list(part="snippet", videoId=vid, maxResults=100, order="time").execute().get("items", [])
            except Exception: existing = []
            if any(c["snippet"]["topLevelComment"]["snippet"].get("authorChannelId", {}).get("value") == owner for c in existing):
                v["comment_id"] = "yours"; save_rec(song, rec); print(f"  you already commented, skipped: {name}"); continue
            text = fill_full_url(meta["pinned_comment"], song, rec, pkg)
            if args.dry_run: print(f"  [dry-run] would comment on {name}:\n{text}\n"); continue
            r = yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": text}}}}).execute()
            v["comment_id"] = r["id"]; save_rec(song, rec)
            print(f"  comment posted: {name}  → open https://youtu.be/{vid} , tap ⋮ on the comment → Pin")

def cmd_publish_now(args):
    """Make a song's scheduled (or private) uploads public right now. Shows the list and asks you to type 'publish'."""
    yt = service()
    for song in songs_from(args):
        rec = load_rec(song); ids = {v["id"]: f for f, v in rec.items() if v.get("id") and not f.endswith("#replaced")}
        if not ids: continue
        items = yt.videos().list(part="status,snippet", id=",".join(ids)).execute().get("items", [])
        todo = [it for it in items if it["status"].get("privacyStatus") != "public"]
        if not todo: print(f"  {song['title']}: everything is already public"); continue
        print(f"\n{song['title']} — these will go PUBLIC now:")
        for it in todo:
            print(f"  {it['snippet']['title']}  (now: {it['status'].get('privacyStatus')}"
                  f"{', scheduled ' + it['status']['publishAt'] if it['status'].get('publishAt') else ''})  https://youtu.be/{it['id']}")
        if args.dry_run: print("  (dry run: nothing changed)"); continue
        if not args.yes and input(f"\nType  publish  to make these {len(todo)} public now: ").strip().lower() != "publish":
            print("  Cancelled. Nothing changed."); continue
        for it in todo:
            cur = it["status"]
            st = {"privacyStatus": "public",
                  "selfDeclaredMadeForKids": bool(cur.get("selfDeclaredMadeForKids", cur.get("madeForKids", False)))}
            for k in ("embeddable", "license", "publicStatsViewable", "containsSyntheticMedia"):   # keep the writable settings as they are
                if k in cur: st[k] = cur[k]
            yt.videos().update(part="status", body={"id": it["id"], "status": st}).execute()
            f = ids[it["id"]]; rec[f]["publish_at"] = dt.datetime.now().astimezone().isoformat(timespec="minutes"); rec[f]["published_now"] = True
            print(f"  public: {it['snippet']['title']}  https://youtu.be/{it['id']}")
            if rec[f].get("playlist") is False:   # uploaded unlisted, so it was kept out of the playlist until now
                pid = CFG.get("playlist_id")
                if pid and playlist_ok(yt, pid):
                    try:
                        yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": it["id"]}}}).execute()
                        rec[f]["playlist"] = True; print("    added to playlist")
                    except Exception as e: print("    not added to playlist:", str(e)[:120])
        save_rec(song, rec)

def cmd_schedule(args):
    """Schedule a song's already-uploaded (unlisted or private) Shorts: the first at --schedule, then one every
    --every-hours, in --order (labels, comma-separated; default: story order). Public ones are left alone."""
    song = load_song(args.song_dir); rec = load_rec(song); pkg = load_pkg(song)
    order = [x.strip() for x in args.order.split(",")] if args.order else None
    clips = [c for c in clip_jobs(pkg, order) if rec.get(c["file"], {}).get("id")]
    if not clips: print("  no uploaded Shorts found for", song["title"]); return
    start = dt.datetime.fromisoformat(args.schedule.strip().replace(" ", "T")); every = float(args.every_hours)
    yt = service(); ids = [rec[c["file"]]["id"] for c in clips]
    info = {it["id"]: it for it in yt.videos().list(part="status,snippet", id=",".join(ids)).execute().get("items", [])}
    now = dt.datetime.now(dt.timezone.utc); plan = []
    print(f"\n{song['title']} — Shorts schedule ({DEFAULT_TZ}):")
    for i, c in enumerate(clips):
        vid = rec[c["file"]]["id"]; it = info.get(vid)
        pu, pl = to_utc_iso(start + dt.timedelta(hours=every * i), DEFAULT_TZ)
        if not it: print(f"  not found on YouTube, skipped: {c['yt_title']}"); continue
        if it["status"].get("privacyStatus") == "public": print(f"  already public, left alone: {c['yt_title']}"); continue
        if dt.datetime.strptime(pu, "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=dt.timezone.utc) < now + dt.timedelta(minutes=2):
            sys.exit(f"  {nice(pl)} is in the past or too soon — pick a later start. Nothing was changed.")
        print(f"  {nice(pl):30} {c['yt_title']}  https://youtu.be/{vid}"); plan.append((c, vid, it, pu, pl))
    if args.dry_run: print("  (dry run: nothing changed)"); return
    if not args.yes and input(f"\nType  schedule  to schedule these {len(plan)}: ").strip().lower() != "schedule":
        print("  Cancelled. Nothing changed."); return
    for c, vid, it, pu, pl in plan:
        cur = it["status"]
        st = {"privacyStatus": "private", "publishAt": pu,
              "selfDeclaredMadeForKids": bool(cur.get("selfDeclaredMadeForKids", cur.get("madeForKids", False)))}
        for k in ("embeddable", "license", "publicStatsViewable", "containsSyntheticMedia"):   # keep the writable settings as they are
            if k in cur: st[k] = cur[k]
        yt.videos().update(part="status", body={"id": vid, "status": st}).execute()
        rec[c["file"]].update({"publish_at": pl.isoformat(), "privacy": "scheduled"}); save_rec(song, rec)
        print(f"  scheduled {nice(pl)}: {c['yt_title']}")

def channel_video_ids(yt):
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]; ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]; tok = r.get("nextPageToken")
        if not tok: return ch["id"], ids

def sweep(yt, pairs, dry=False):
    """Replace text (e.g. an old channel handle, a replaced video's link) in every description on the channel and in
    your own comments. Titles, tags and everything else stay as they are. Safe to re-run: only touches what still matches."""
    pairs = [(o, n) for o, n in pairs if o and o != n]
    if not pairs: return
    me, ids = channel_video_ids(yt); nd = nc = 0
    print(f"  checking {len(ids)} videos for: " + ", ".join(f"{o} → {n}" for o, n in pairs))
    for i in range(0, len(ids), 50):
        for it in yt.videos().list(part="snippet", id=",".join(ids[i:i + 50])).execute().get("items", []):
            sn = it["snippet"]; d = sn.get("description", ""); d2 = d
            for o, n in pairs: d2 = d2.replace(o, n)
            if d2 != d:
                sn["description"] = d2
                if dry: print(f"    [dry-run] description: {sn['title']}")
                else: yt.videos().update(part="snippet", body={"id": it["id"], "snippet": sn}).execute(); nd += 1; print(f"    description fixed: {sn['title']}")
            try: threads = yt.commentThreads().list(part="snippet", videoId=it["id"], maxResults=100).execute().get("items", [])
            except Exception: threads = []
            for th in threads:
                c = th["snippet"]["topLevelComment"]; cs = c["snippet"]
                if cs.get("authorChannelId", {}).get("value") != me: continue
                t = cs.get("textOriginal", ""); t2 = t
                for o, n in pairs: t2 = t2.replace(o, n)
                if t2 == t: continue
                if dry: print(f"    [dry-run] comment on: {sn['title']}"); continue
                yt.comments().update(part="snippet", body={"id": c["id"], "snippet": {"textOriginal": t2}}).execute(); nc += 1
                print(f"    comment fixed: {sn['title']}")
    print(f"  done: {nd} descriptions, {nc} comments updated")

def replaced_pairs(song):
    """uploads.json keeps a replaced upload as '<file>#replaced'; returns (old link, new link) once the new one exists."""
    rec = load_rec(song); out = []
    for k, v in rec.items():
        if k.endswith("#replaced") and rec.get(k[:-9], {}).get("id"):
            for pre in ("youtu.be/", "watch?v=", "/shorts/"): out.append((pre + v["id"], pre + rec[k[:-9]]["id"]))
    return out

def cmd_replace(args):
    yt = service(); pairs = [tuple(p) for p in (args.replace or [])]
    if args.relink:
        for song in songs_from(args): pairs += replaced_pairs(song)
    sweep(yt, pairs, args.dry_run)

def cmd_privatize_replaced(args):
    """Set the old copy of each replaced upload to private (nothing is deleted; delete it in Studio when you're sure)."""
    yt = service()
    for song in songs_from(args):
        rec = load_rec(song)
        for k, v in rec.items():
            if not k.endswith("#replaced") or v.get("privatized"): continue
            items = yt.videos().list(part="status,snippet", id=v["id"]).execute().get("items", [])
            if not items: continue
            st = items[0]["status"]; new = {"privacyStatus": "private", "selfDeclaredMadeForKids": bool(st.get("selfDeclaredMadeForKids", st.get("madeForKids", False)))}
            if args.dry_run: print(f"  [dry-run] would make private: {items[0]['snippet']['title']} https://youtu.be/{v['id']}"); continue
            yt.videos().update(part="status", body={"id": v["id"], "status": new}).execute()
            v["privatized"] = True; save_rec(song, rec); print(f"  old copy now private: {items[0]['snippet']['title']}  https://youtu.be/{v['id']}")

def _all_songs():
    out = []
    for y in sorted(glob.glob(os.path.join(ROOT, "songs", "*", "song.yaml"))):
        try: out.append(load_song(os.path.dirname(y)))
        except Exception: pass
    return out

def clean_title(t, songs=()):
    """'Vacation (To My Bed) (Travel Time: 4 Seconds) - Claude Opus 5.5 Music Video' -> 'Vacation to My Bed - Claude Opus 5.5 Music Video'.
    A song's yt_name replaces its full title first (so names that need their parenthetical keep a version of it)."""
    for sg in songs:
        if sg.get("yt_name") and sg["title"] in t: t = t.replace(sg["title"], sg["yt_name"])
    return " ".join(re.sub(r"\s*\([^)]*\)", "", t).split())

def _norm(t): return re.sub(r"[^a-z0-9]+", "", t.lower())

def cmd_clean_titles(args):
    """Drop the (…) parts from every full-video title on the channel ("Autocomplete (It Finishes My Sentences) - Claude Opus 5.5
    Music Video" -> "Autocomplete - Claude Opus 5.5 Music Video") so the Claude part isn't cut off in search and suggestions.
    Only titles containing 'music video' (any case) are touched; Shorts keep theirs. Descriptions, tags and everything else stay."""
    yt = service(); me, ids = channel_video_ids(yt); songs = _all_songs(); todo = []
    for i in range(0, len(ids), 50):
        for it in yt.videos().list(part="snippet", id=",".join(ids[i:i + 50])).execute().get("items", []):
            t = it["snippet"]["title"]
            if "music video" in t.lower() and "(" in t and clean_title(t, songs) != t: todo.append((it, clean_title(t, songs)))
    if not todo: print("  every full-video title is already clean"); return
    print(f"  {len(todo)} titles to change:")
    for it, new in todo: print(f"    {it['snippet']['title']}\n      -> {new}")
    seen = {}
    for it, new in todo: seen.setdefault(new, []).append(it["id"])
    for new, v in seen.items():
        if len(v) > 1: print(f"  note: {len(v)} videos will share the title '{new}'")
    if args.dry_run: print("  (dry run: nothing changed)"); return
    recs = {sg["dir"]: (sg, load_rec(sg)) for sg in songs if os.path.exists(rec_path(sg))}
    for it, new in todo:
        sn = it["snippet"]; sn["title"] = new
        try: yt.videos().update(part="snippet", body={"id": it["id"], "snippet": sn}).execute(); print(f"  renamed: {new}  https://youtu.be/{it['id']}")
        except Exception as e:
            if is_quota(e): print("  Daily YouTube quota is used up; run this again tomorrow."); return
            print(f"  not renamed ({it['id']}):", str(e)[:160]); continue
        for sg, rec in recs.values():
            for f, v in rec.items():
                if v.get("id") == it["id"]: v["title"] = new; save_rec(sg, rec)

def cmd_set_thumbnails(args):
    """Swap the live thumbnail of each song's full video for "<Title> - YouTube thumbnail.jpg" (re-run studio.thumbs first).
    The video is found in uploads.json (the full-video entry), so hand-posted videos need their id recorded there once."""
    from googleapiclient.http import MediaFileUpload
    from PIL import Image
    import tempfile
    yt = service(); done = 0
    for song in songs_from(args):
        rec = load_rec(song); T = song["title"]
        try: lf = load_pkg(song)["long"]["file"]
        except Exception: lf = None
        f = lf if (lf in rec and rec[lf].get("id") and not rec[lf].get("deleted")) else \
            next((k for k, v in rec.items() if k.endswith("YouTube 16x9.mp4") and v.get("id") and not v.get("deleted")), None)
        th = os.path.join(song["out_dir"], f"{T} - YouTube thumbnail.jpg")
        try: th = os.path.join(song["out_dir"], load_pkg(song)["long"].get("thumbnail") or os.path.basename(th))
        except Exception: pass
        if not f: print(f"  {T}: no full video recorded in uploads.json, skipped"); continue
        if not os.path.exists(th): print(f"  {T}: {os.path.basename(th)} not found, skipped"); continue
        vid = rec[f]["id"]; up = th; stamp = f"{os.path.basename(th)}|{int(os.path.getmtime(th))}"
        if rec[f].get("thumbnail_set") == stamp: print(f"  {T}: already has this thumbnail"); continue
        items = yt.videos().list(part="snippet", id=vid).execute().get("items", [])
        if not items: print(f"  {T}: video {vid} not found on the channel, skipped"); continue
        cur = items[0]["snippet"]["title"]
        if not _norm(clean_title(cur, _all_songs())).startswith(_norm(public_name(song))):
            print(f"  {T}: https://youtu.be/{vid} is titled '{cur}', which doesn't look like this song; skipped"); continue
        if os.path.getsize(th) > 1_900_000:      # YouTube's limit is 2 MB
            up = os.path.join(tempfile.mkdtemp(), "thumb.jpg"); Image.open(th).convert("RGB").save(up, quality=85)
        if args.dry_run: print(f"  [dry-run] {T}: {os.path.basename(th)} -> https://youtu.be/{vid}"); continue
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(up, mimetype="image/jpeg")).execute()
            rec[f]["thumbnail"] = os.path.basename(th); rec[f]["thumbnail_set"] = stamp; save_rec(song, rec); done += 1
            print(f"  thumbnail updated: {T}  https://youtu.be/{vid}")
        except Exception as e:
            if is_quota(e): print("  Daily YouTube quota is used up; run this again tomorrow."); return
            print(f"  {T}: not updated:", str(e)[:160])
    print(f"done: {done} thumbnails updated (YouTube can take a few minutes to show the new ones)")

def _secs(iso):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (86400, 3600, 60, 1))) if m else 0

def cmd_doompop(args):
    """Tag the live videos of the AI Doompop songs (studio.yaml `doompop:` slugs + `doompop_videos:` ids, e.g. the Fable versions)
    and every Short that links to one of them: '#AIDoompop' ends the title, leads the description's hashtags, and 'ai doompop',
    'aidoompop', 'doompop' go first in the tags. Lists every change and asks before sending; the old copy goes to logs/ first.
    Safe to re-run: videos that already have it are left alone."""
    yt = service(); me, ids = channel_video_ids(yt)
    songs = [sg for sg in _all_songs() if doompop(sg)]; why = {}; recs = []
    for sg in songs:
        if not os.path.exists(rec_path(sg)): continue
        rec = load_rec(sg); recs.append((sg, rec))
        for f, v in rec.items():
            if "#" not in f and v.get("id") and not v.get("deleted"): why[v["id"]] = sg["slug"]
    for vid in CFG.get("doompop_videos") or []: why.setdefault(vid, "doompop_videos")
    items = {}
    for i in range(0, len(ids), 50):
        for it in yt.videos().list(part="snippet,status,contentDetails", id=",".join(ids[i:i + 50])).execute().get("items", []): items[it["id"]] = it
    base = set(why); names = sorted({public_name(sg) for sg in songs}, key=len, reverse=True)
    for vid, it in items.items():
        if vid in why or _secs(it["contentDetails"].get("duration")) > 180: continue
        hit = next((b for b in base if b in it["snippet"].get("description", "")), None)
        if hit: why[vid] = f"Short linking to {hit}"; continue
        txt = " ".join(w for w in (it["snippet"]["title"] + " " + it["snippet"].get("description", "")).split() if not w.startswith("#"))
        nm = next((n for n in names if re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", txt, re.I)), None)   # Shorts that name the song but don't link it
        if nm: why[vid] = f"Short naming {nm}"
    if args.dry_run:
        print("  other Shorts on the channel (left alone):")
        for vid, it in items.items():
            if vid not in why and _secs(it["contentDetails"].get("duration")) <= 180: print(f"    {vid}  {it['snippet']['title'][:80]}")
    todo, skip = [], []
    for vid, reason in why.items():
        it = items.get(vid)
        if not it: skip.append((vid, "not on the channel")); continue
        if it["status"].get("privacyStatus") == "private": skip.append((vid, "private: " + it["snippet"]["title"])); continue
        sn = it["snippet"]; t = doompop_title(sn["title"]); d = doompop_desc(sn.get("description", ""), t); cur = sn.get("tags", [])
        tg = cur if any(str(x).lower() == "ai doompop" for x in cur) else clean_tags(doompop_tags(cur))   # already tagged: leave the tag list as YouTube has it
        if (t, d, tg) == (sn["title"], sn.get("description", ""), sn.get("tags", [])): skip.append((vid, "already tagged: " + sn["title"])); continue
        todo.append((it, t, d, tg, reason))
    for vid, r in skip: print(f"  skip {vid}  ({r})")
    if not todo: print("  nothing to change"); return
    print(f"\n  {len(todo)} videos to tag #AIDoompop:")
    for it, t, d, tg, reason in todo:
        sn = it["snippet"]; notes = [x for x, ch in (("description", d != sn.get("description", "")), ("tags", tg != sn.get("tags", []))) if ch]
        print(f"    https://youtu.be/{it['id']}  [{reason}]\n      {sn['title']}\n      -> {t}" + ("" if t != sn["title"] else "   (title unchanged: already there or too long)")
              + f"\n      + {', '.join(notes) or 'nothing else'}")
    if args.dry_run: print("  (dry run: nothing changed)"); return
    if not args.yes and input('\n  Type "go" to change these videos: ').strip().lower() != "go": print("  nothing changed"); return
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    bk = os.path.join(ROOT, "logs", "doompop_backup_" + dt.datetime.now().strftime("%Y%m%d_%H%M") + ".json")
    json.dump({it["id"]: {k: it["snippet"].get(k) for k in ("title", "description", "tags")} for it, *_ in todo}, open(bk, "w"), indent=1, ensure_ascii=False)
    print(f"  old titles/descriptions/tags saved to {os.path.relpath(bk, ROOT)}"); n = 0
    for it, t, d, tg, reason in todo:
        sn = dict(it["snippet"]); sn.update({"title": t, "description": d, "tags": tg})
        try: yt.videos().update(part="snippet", body={"id": it["id"], "snippet": sn}).execute()
        except Exception as e:
            if is_quota(e): print("  Daily YouTube quota is used up; run this again tomorrow (it continues)."); break
            if t != it["snippet"]["title"] and "title" in str(e).lower():
                try: sn["title"] = it["snippet"]["title"]; yt.videos().update(part="snippet", body={"id": it["id"], "snippet": sn}).execute(); t = sn["title"]
                except Exception as e2: print(f"  not changed ({it['id']}):", str(e2)[:160]); continue
            else: print(f"  not changed ({it['id']}):", str(e)[:160]); continue
        n += 1; print(f"  tagged: {t}  https://youtu.be/{it['id']}")
        for sg, rec in recs:
            for f, v in rec.items():
                if v.get("id") == it["id"] and v.get("title") != t: v["title"] = t; save_rec(sg, rec)
    print(f"\n  done: {n} of {len(todo)} videos tagged #AIDoompop")

def cmd_go_live(args):
    """One step: final titles/descriptions/tags on everything uploaded, publish the scheduled ones now, post the pinned comments."""
    print("1/3  Updating titles, descriptions and tags to the final copy…"); cmd_update(args)
    print("\n2/3  Publishing…"); cmd_publish_now(args)
    print("\n3/3  Pinned comments…"); cmd_comments(args)
    print("\nDone. Last step is yours: on each video, tap ⋮ on the new comment → Pin (YouTube doesn't let apps pin).")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("song_dir", nargs="?"); ap.add_argument("--plan"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true", help="skip the typed confirmation (not recommended)")
    ap.add_argument("--status", action="store_true"); ap.add_argument("--update", action="store_true"); ap.add_argument("--post-comments", action="store_true")
    ap.add_argument("--only", choices=["long", "clip"], help="with --update: only the full video (long) or only the Shorts (clip)")
    ap.add_argument("--schedule", metavar="'YYYY-MM-DD HH:MM'", help="schedule a song's uploaded unlisted/private Shorts from this local time")
    ap.add_argument("--every-hours", default="1", help="with --schedule: hours between Shorts (default 1)")
    ap.add_argument("--order", help="with --schedule: Short labels in posting order, comma-separated")
    ap.add_argument("--publish-now", action="store_true", help="make a song's scheduled/private uploads public now")
    ap.add_argument("--go-live", action="store_true", help="final copy + publish now + pinned comments, for one song")
    ap.add_argument("--replace", nargs=2, action="append", metavar=("OLD", "NEW"), help="replace text in every description and your own comments")
    ap.add_argument("--relink", action="store_true", help="point links to replaced uploads at their new copies (all songs, or one)")
    ap.add_argument("--privatize-replaced", action="store_true", help="make the old copies of replaced uploads private")
    ap.add_argument("--clean-titles", action="store_true", help="drop the (…) parts from every full-video title on the channel")
    ap.add_argument("--doompop", action="store_true", help="add #AIDoompop / 'ai doompop' to the AI Doompop songs' live videos and their Shorts")
    ap.add_argument("--set-thumbnails", action="store_true", help="swap each full video's live thumbnail for the current '<Title> - YouTube thumbnail.jpg'")
    a = ap.parse_args()
    if a.schedule: return cmd_schedule(a)
    if a.status: return cmd_status(a)
    if a.update: return cmd_update(a)
    if a.post_comments: return cmd_comments(a)
    if a.publish_now: return cmd_publish_now(a)
    if a.go_live: return cmd_go_live(a)
    if a.replace or a.relink: return cmd_replace(a)
    if a.privatize_replaced: return cmd_privatize_replaced(a)
    if a.clean_titles: return cmd_clean_titles(a)
    if a.set_thumbnails: return cmd_set_thumbnails(a)
    if a.doompop: return cmd_doompop(a)
    if a.plan: return run_plan(a.plan, a.dry_run, a.yes)
    ap.print_help()

if __name__ == "__main__":
    main()
