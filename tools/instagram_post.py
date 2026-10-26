#!/usr/bin/env python3
"""Post finished songs to Instagram as Reels — run in your own terminal.

How it works (Instagram's rules):
  * Instagram only takes a video from a public link, so each video (and its cover) is parked in a private-named file in
    your Google Cloud bucket for a few minutes and deleted right after it's posted (the bucket also auto-deletes after 1 day).
  * Posts go out when you run this (Instagram's API has no scheduler).
  * Before posting it reads your recent Instagram posts and SKIPS any whose caption is already up, so nothing doubles.
  * You see the full list and must type "post" before anything is sent. Posted reels are recorded in build/ig_posts.json.

Usage:
  python3 tools/instagram_post.py --set-token                 # paste your Instagram token once (Meta app dashboard)
  python3 tools/instagram_post.py --plan release_plan.yaml --dry-run
  python3 tools/instagram_post.py --plan release_plan.yaml    # review, type "post", go
  python3 tools/instagram_post.py --recent                    # your last 25 posts (to check what's up)

One-time setup: docs/publishing.md.
"""
import os, sys, json, time, argparse, getpass, uuid, datetime as dt, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from studio.config import load_song, CFG  # noqa: E402

SECRETS = os.path.join(ROOT, "secrets"); IG_TOKEN = os.path.join(SECRETS, "instagram.json")
GRAPH = "https://graph.instagram.com/v23.0"
GCS_SCOPES = ["https://www.googleapis.com/auth/devstorage.read_write"]

# ---------------------------------------------------------------- Instagram token (yours; pasted in your own Terminal)
def http():
    import requests
    return requests

def ig_get(path, **params):
    r = http().get(f"{GRAPH}/{path}", params=params, timeout=60)
    if r.status_code >= 400: raise RuntimeError(f"Instagram said: {r.text[:400]}")
    return r.json()

def ig_post(path, **data):
    r = http().post(f"{GRAPH}/{path}", data=data, timeout=120)
    if r.status_code >= 400: raise RuntimeError(f"Instagram said: {r.text[:400]}")
    return r.json()

def load_token():
    if not os.path.exists(IG_TOKEN): sys.exit("No Instagram token yet: run  python3 tools/instagram_post.py --set-token")
    t = json.load(open(IG_TOKEN))
    saved = dt.datetime.fromisoformat(t.get("saved_at", "2000-01-01T00:00:00+00:00"))
    if dt.datetime.now(dt.timezone.utc) - saved > dt.timedelta(days=7):      # long-lived tokens last 60 days; keep it fresh
        try:
            r = http().get("https://graph.instagram.com/refresh_access_token",
                           params={"grant_type": "ig_refresh_token", "access_token": t["access_token"]}, timeout=30).json()
            if r.get("access_token"):
                t.update(access_token=r["access_token"], saved_at=dt.datetime.now(dt.timezone.utc).isoformat()); json.dump(t, open(IG_TOKEN, "w"))
        except Exception: pass
    return t

def set_token():
    tok = getpass.getpass("Paste your Instagram access token (it won't show while you paste), then press Return: ").strip()
    me = http().get(f"{GRAPH}/me", params={"fields": "user_id,username,account_type", "access_token": tok}, timeout=30).json()
    if "error" in me: sys.exit(f"That token didn't work: {me['error'].get('message')}")
    os.makedirs(SECRETS, exist_ok=True)
    json.dump({"access_token": tok, "user_id": me["user_id"], "username": me.get("username"),
               "saved_at": dt.datetime.now(dt.timezone.utc).isoformat()}, open(IG_TOKEN, "w"))
    print(f"Saved. Connected to @{me.get('username')} ({me.get('account_type', '?')}).")

# ---------------------------------------------------------------- Google Cloud Storage: the temporary public link
def gcs():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request, AuthorizedSession
    tok = os.path.join(SECRETS, "gcs_token.json"); creds = None
    if os.path.exists(tok): creds = Credentials.from_authorized_user_file(tok, GCS_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try: creds.refresh(Request())
            except Exception: creds = None
        if not creds or not creds.valid:
            creds = InstalledAppFlow.from_client_secrets_file(os.path.join(SECRETS, "client_secret.json"), GCS_SCOPES).run_local_server(port=0)
        open(tok, "w").write(creds.to_json())
    return AuthorizedSession(creds)

def project_id():
    cs = json.load(open(os.path.join(SECRETS, "client_secret.json")))
    return (cs.get("installed") or cs.get("web") or {}).get("project_id")

def ensure_bucket(s):
    name = CFG.get("ig_bucket") or f"{project_id()}-ig-temp"
    r = s.get(f"https://storage.googleapis.com/storage/v1/b/{name}")
    if r.status_code == 404:
        body = {"name": name, "location": "US-WEST1",
                "iamConfiguration": {"uniformBucketLevelAccess": {"enabled": True}, "publicAccessPrevention": "inherited"},
                "lifecycle": {"rule": [{"action": {"type": "Delete"}, "condition": {"age": 1}}]}}
        r = s.post(f"https://storage.googleapis.com/storage/v1/b", params={"project": project_id()}, json=body)
        if r.status_code >= 400:
            msg = r.text[:300]
            if "billing" in msg.lower(): sys.exit("Google Cloud needs billing turned on for this project to hold the temporary files "
                                                  "(docs/publishing.md → Instagram, step 1). Nothing was posted.")
            sys.exit(f"Couldn't create the temporary bucket: {msg}")
        pol = s.get(f"https://storage.googleapis.com/storage/v1/b/{name}/iam").json()
        pol.setdefault("bindings", []).append({"role": "roles/storage.objectViewer", "members": ["allUsers"]})
        r = s.put(f"https://storage.googleapis.com/storage/v1/b/{name}/iam", json=pol)
        if r.status_code >= 400: sys.exit(f"Couldn't make the temporary bucket readable by Instagram: {r.text[:300]}")
        print(f"  created temporary bucket {name} (files auto-delete after 1 day)")
    elif r.status_code >= 400: sys.exit(f"Couldn't reach the temporary bucket: {r.text[:300]}")
    return name

def park(s, bucket, path, ctype):
    name = f"{uuid.uuid4().hex}{os.path.splitext(path)[1]}"
    with open(path, "rb") as f:
        r = s.post(f"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o", params={"uploadType": "media", "name": name},
                   data=f, headers={"Content-Type": ctype})
    if r.status_code >= 400: raise RuntimeError(f"temporary upload failed: {r.text[:300]}")
    return name, f"https://storage.googleapis.com/{bucket}/{urllib.parse.quote(name)}"

def unpark(s, bucket, name):
    try: s.delete(f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{urllib.parse.quote(name, safe='')}")
    except Exception: pass

# ---------------------------------------------------------------- what to post
def rec_path(song): return os.path.join(song["build"], "ig_posts.json")
def load_rec(song): p = rec_path(song); return json.load(open(p)) if os.path.exists(p) else {}
def save_rec(song, r): json.dump(r, open(rec_path(song), "w"), indent=1, ensure_ascii=False)

def items_for(song, wanted):
    pkg = json.load(open(os.path.join(song["build"], "package.json")))
    by = {}
    if pkg.get("instagram_full"): by["edit"] = dict(pkg["instagram_full"], label="edit", name="Instagram full (under 3 min)")
    for c in pkg.get("reels", []) + pkg.get("shorts", []): by[c["label"]] = dict(c, name=f"{c['kind'].title()}: {c['label']}")
    out = []
    for w in wanted:
        if w not in by: print(f"  (no clip called '{w}' in {song['title']}; skipped)"); continue
        it = by[w]; f = it["file"]; cov = os.path.join(song["out_dir"], "Covers", os.path.splitext(f)[0].replace("Instagram 9x16", "Instagram") + " - cover.jpg")
        if not os.path.exists(cov): cov = os.path.join(song["out_dir"], f"{song['title']} - Short cover (9x16).jpg")
        out.append(dict(it, path=os.path.join(song["out_dir"], f), cover=cov if os.path.exists(cov) else None))
    return out

def norm(s): return " ".join((s or "").split()).lower()[:60]

def run_plan(plan_path, dry, yes):
    import yaml
    plan = yaml.safe_load(open(plan_path)); entries = plan.get("instagram") or []
    if not entries: sys.exit("release_plan.yaml has no 'instagram:' section yet.")
    tok = None if dry else load_token()
    recent = []
    if tok:
        recent = ig_get(f"{tok['user_id']}/media", fields="caption,permalink,timestamp", limit=50, access_token=tok["access_token"]).get("data", [])
    recent_caps = {norm(m.get("caption")): m.get("permalink") for m in recent}
    todo, problems = [], []
    print(f"\nINSTAGRAM PLAN  ({plan_path}) — posts go out now, in this order\n")
    for e in entries:
        song = load_song(os.path.join(ROOT, e["song"])); rec = load_rec(song)
        for it in items_for(song, e.get("post") or []):
            cap = it["ig_caption"]
            if not os.path.exists(it["path"]): problems.append(f"missing file: {it['path']}")
            if len(cap) > 2200: problems.append(f"caption over 2,200 characters: {it['file']}")
            if cap.count("#") > 30: problems.append(f"more than 30 hashtags: {it['file']}")
            if it["file"] in rec: state = f"already posted → skip ({rec[it['file']].get('permalink', '')})"
            elif norm(cap) in recent_caps: state = f"same caption already on your profile → skip ({recent_caps[norm(cap)]})"
            else: state = "POST NOW"; todo.append((song, it))
            print(f"  [{song['title']}] {it['name']}\n      {os.path.basename(it['path'])}   cover: {os.path.basename(it['cover']) if it['cover'] else 'first frame'}\n"
                  f"      “{cap.splitlines()[0][:90]}”\n      {state}")
    if problems: print("\nFIX FIRST:"); [print("  - " + p) for p in problems]; sys.exit(1)
    if not todo: print("\nNothing new to post."); return
    if dry: print(f"\n(dry run: nothing sent{'; sign-in skipped, so posts already on your profile are not detected yet' if not tok else ''})"); return
    lim = ig_get(f"{tok['user_id']}/content_publishing_limit", fields="quota_usage,config", access_token=tok["access_token"]).get("data", [{}])[0]
    print(f"\n  Instagram API posts used in the last 24 h: {lim.get('quota_usage', '?')} of {lim.get('config', {}).get('quota_total', '?')}")
    if not yes and input(f"\nType  post  to publish these {len(todo)} Reel(s) to @{tok.get('username')} now: ").strip().lower() != "post":
        print("Cancelled. Nothing was posted."); return
    s = gcs(); bucket = ensure_bucket(s)
    for song, it in todo:
        print(f"\n  {it['name']}  ({song['title']})")
        parked = []
        try:
            vname, vurl = park(s, bucket, it["path"], "video/mp4"); parked.append(vname); print("    video ready")
            data = dict(media_type="REELS", video_url=vurl, caption=it["ig_caption"], share_to_feed="true", access_token=tok["access_token"])
            if it["cover"]:
                cname, curl = park(s, bucket, it["cover"], "image/jpeg"); parked.append(cname); data["cover_url"] = curl
            cid = ig_post(f"{tok['user_id']}/media", **data)["id"]
            for _ in range(120):            # Instagram processes the video (usually under a minute)
                st = ig_get(cid, fields="status_code,status", access_token=tok["access_token"])
                if st.get("status_code") == "FINISHED": break
                if st.get("status_code") in ("ERROR", "EXPIRED"): raise RuntimeError(f"Instagram couldn't process it: {st.get('status')}")
                time.sleep(5)
            else: raise RuntimeError("Instagram took too long to process the video; run again later")
            mid = ig_post(f"{tok['user_id']}/media_publish", creation_id=cid, access_token=tok["access_token"])["id"]
            link = ig_get(mid, fields="permalink", access_token=tok["access_token"]).get("permalink", "")
            rec = load_rec(song); rec[it["file"]] = {"id": mid, "permalink": link, "posted_at": dt.datetime.now().astimezone().isoformat(timespec="minutes")}; save_rec(song, rec)
            print(f"    posted: {link}")
        except Exception as ex:
            print(f"    NOT posted: {ex}")
            if "limit" in str(ex).lower(): print("    (Instagram's posting limit) — run again tomorrow; it continues where it stopped."); break
        finally:
            for n in parked: unpark(s, bucket, n)
    print("\nDone. In the app you can still add a location or tag people on each Reel (the API can't).")

def recent():
    tok = load_token()
    for m in ig_get(f"{tok['user_id']}/media", fields="caption,permalink,timestamp,media_product_type", limit=25, access_token=tok["access_token"]).get("data", []):
        print(f"  {m.get('timestamp', '')[:16]}  {m.get('media_product_type', ''):6}  {(m.get('caption') or '').splitlines()[0][:70] if m.get('caption') else ''}  {m.get('permalink')}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan"); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--yes", action="store_true")
    ap.add_argument("--set-token", action="store_true"); ap.add_argument("--recent", action="store_true")
    a = ap.parse_args()
    if a.set_token: return set_token()
    if a.recent: return recent()
    if a.plan: return run_plan(a.plan, a.dry_run, a.yes)
    ap.print_help()

if __name__ == "__main__":
    main()
