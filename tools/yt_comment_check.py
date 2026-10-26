#!/usr/bin/env python3
"""Check the comment the upload tool posted on each of a song's YouTube uploads: is it live, held for review, marked as spam,
or gone? And is the video public yet?

usage: python3 tools/yt_comment_check.py songs/<slug> [songs/<slug> ...]
Read-only: it changes nothing on YouTube. (Pinning can't be done through the API; that part is by hand or in the browser.)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import youtube_upload as U  # noqa: E402
from studio.config import load_song  # noqa: E402  (youtube_upload puts the project root on sys.path)


def held(yt, vid):
    """Thread ids of the owner's comments that YouTube is holding back on this video (review queue or spam)."""
    out = {}
    for status in ("heldForReview", "likelySpam"):
        try:
            r = yt.commentThreads().list(part="snippet", videoId=vid, moderationStatus=status, maxResults=100).execute()
            for it in r.get("items", []):
                out[it["id"]] = status
        except Exception as e:  # noqa: BLE001
            out[f"?{status}"] = f"could not check ({str(e)[:80]})"
    return out


def main(dirs):
    yt = U.service()
    for d in dirs:
        song = load_song(d); rec = U.load_rec(song)
        vids = {f: v for f, v in rec.items() if v.get("id") and not f.endswith("#replaced")}
        if not vids:
            print(f"{song['title']}: nothing uploaded"); continue
        info = {it["id"]: it for it in yt.videos().list(part="status,snippet,statistics", id=",".join(v["id"] for v in vids.values())).execute().get("items", [])}
        print(f"\n== {song['title']} ({os.path.basename(os.path.normpath(d))})")
        for f, v in vids.items():
            vid = v["id"]; it = info.get(vid)
            if not it:
                print(f"  {vid}  NOT FOUND on YouTube   {f}"); continue
            st = it["status"]; priv = st.get("privacyStatus"); when = st.get("publishAt", "")
            cid = v.get("comment_id")
            if not cid:
                state = "no comment posted"
            elif cid == "yours":
                state = "you commented by hand (not tracked)"
            else:
                try:
                    live = yt.commentThreads().list(part="snippet", id=cid).execute().get("items", [])
                except Exception as e:  # noqa: BLE001
                    live = []; state = f"could not check ({str(e)[:60]})"
                if live:
                    sn = live[0]["snippet"]; tl = sn["topLevelComment"]["snippet"]
                    state = f"LIVE (public={sn.get('isPublic')}, likes={tl.get('likeCount')}, status={tl.get('moderationStatus', 'published')})"
                else:
                    h = held(yt, vid)
                    state = ("HELD: " + h[cid]) if cid in h else "MISSING (deleted or hidden)"
                    extra = {k: s for k, s in h.items() if k.startswith("?")}
                    if extra: state += "  " + "; ".join(extra.values())
            comments = it.get("statistics", {}).get("commentCount", "?")
            print(f"  {vid}  {priv:9} {when[:16]:16} comments={comments:>3}  {state}\n      {it['snippet']['title']}")
    print("\nNothing was changed. Pinning is by hand: open the video, ⋮ on the comment → Pin.")


if __name__ == "__main__":
    main(sys.argv[1:] or ["songs/omg-agents-walls", "songs/omg-agents-swarm"])
