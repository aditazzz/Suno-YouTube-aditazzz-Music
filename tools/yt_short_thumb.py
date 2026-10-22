#!/usr/bin/env python3
"""Set a posted Short's custom thumbnail from an image in the song's output folder.

usage: python3 tools/yt_short_thumb.py songs/<slug> "<clip label>" "<image path relative to the song's output folder>"
The Short is found in songs/<slug>/build/uploads.json by its clip file (from build/package.json)."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from youtube_upload import service, load_rec, save_rec, load_pkg, is_quota, ROOT
from studio.config import load_song

def main(song_dir, label, rel):
    from googleapiclient.http import MediaFileUpload
    from PIL import Image
    song = load_song(os.path.join(ROOT, song_dir) if not os.path.isabs(song_dir) else song_dir)
    pkg = load_pkg(song); rec = load_rec(song)
    clip = next((c for c in pkg.get("shorts", []) + pkg.get("reels", []) if c["label"] == label), None)
    if not clip: sys.exit(f"no clip labelled '{label}' in package.json")
    f = clip["file"]
    if f not in rec or not rec[f].get("id"): sys.exit(f"'{f}' is not recorded as uploaded in uploads.json")
    th = os.path.join(song["out_dir"], rel)
    if not os.path.exists(th): sys.exit(f"image not found: {th}")
    up = th
    if os.path.getsize(th) > 1_900_000:          # YouTube's limit is 2 MB
        up = os.path.join(tempfile.mkdtemp(), "thumb.jpg"); Image.open(th).convert("RGB").save(up, quality=85)
    yt = service(); vid = rec[f]["id"]
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(up, mimetype="image/jpeg")).execute()
    except Exception as e:
        if is_quota(e): sys.exit("Daily YouTube quota is used up; run this again tomorrow.")
        sys.exit(f"thumbnail not set: {str(e)[:200]}")
    rec[f]["thumbnail"] = rel; rec[f]["thumbnail_set"] = f"{os.path.basename(th)}|{int(os.path.getmtime(th))}"; save_rec(song, rec)
    print(f"  thumbnail set: {clip.get('yt_title', label)}  https://youtu.be/{vid}  ({os.path.basename(th)})")

if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
