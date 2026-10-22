"""Adopt a video that was uploaded by hand (e.g. through YouTube Studio) as a song's full video, so the uploader can finish it:
records its id in uploads.json, adds it to the playlist and sets category Music, not made for kids, AI disclosure.
usage: python3 tools/yt_adopt.py songs/<slug> "words in the title"      (picks the newest upload whose title contains them)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import youtube_upload as Y
from studio.config import load_song, CFG
song = load_song(sys.argv[1]); needle = sys.argv[2].lower()
yt = Y.service(); rec = Y.load_rec(song); pkg = Y.load_pkg(song); f = pkg["long"]["file"]
if rec.get(f, {}).get("id"): print("already recorded:", rec[f]["id"]); sys.exit(0)
me, ids = Y.channel_video_ids(yt)
hit = None
for i in range(0, min(len(ids), 100), 50):
    for it in yt.videos().list(part="snippet,status", id=",".join(ids[i:i + 50])).execute().get("items", []):
        if needle in it["snippet"]["title"].lower():
            if hit is None or it["snippet"]["publishedAt"] > hit["snippet"]["publishedAt"]: hit = it
if not hit: print("no upload with that title found"); sys.exit(1)
vid = hit["id"]; print(f"found: {hit['snippet']['title']}  ({hit['status']['privacyStatus']})  https://youtu.be/{vid}")
rec[f] = {"id": vid, "title": hit["snippet"]["title"], "note": "uploaded in YouTube Studio, adopted"}; Y.save_rec(song, rec)
sn = hit["snippet"]; sn["categoryId"] = str(pkg["long"].get("category", 10))
yt.videos().update(part="snippet", body={"id": vid, "snippet": sn}).execute(); print("  category set to Music")
st = {"privacyStatus": hit["status"]["privacyStatus"], "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
for k in ("embeddable", "license", "publicStatsViewable"):
    if k in hit["status"]: st[k] = hit["status"][k]
try: yt.videos().update(part="status", body={"id": vid, "status": st}).execute(); print("  audience: not made for kids; AI content disclosed")
except Exception as e:
    st.pop("containsSyntheticMedia", None); yt.videos().update(part="status", body={"id": vid, "status": st}).execute(); print("  audience: not made for kids")
pid = CFG.get("playlist_id")
if pid and Y.playlist_ok(yt, pid):
    try: yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute(); print("  added to playlist")
    except Exception as e: print("  not added to playlist:", str(e)[:120])
