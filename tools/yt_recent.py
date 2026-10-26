#!/usr/bin/env python3
"""List the channel's most recent uploads: privacy, scheduled publish time, processing state and upload time.

usage: python3 tools/yt_recent.py [N]        # default: the last 30 uploads
Read-only: it changes nothing on YouTube.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import youtube_upload as U  # noqa: E402


def main(n=30):
    yt = U.service()
    up = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while len(ids) < n:
        r = yt.playlistItems().list(part="contentDetails", playlistId=up, maxResults=min(50, n - len(ids)), pageToken=tok).execute()
        ids += [it["contentDetails"]["videoId"] for it in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    rows = []
    for i in range(0, len(ids), 50):
        rows += yt.videos().list(part="snippet,status,processingDetails,contentDetails", id=",".join(ids[i:i + 50])).execute().get("items", [])
    rows.sort(key=lambda it: it["snippet"].get("publishedAt", ""), reverse=True)
    for it in rows:
        st, sn, pd = it["status"], it["snippet"], it.get("processingDetails", {})
        when = ("publishAt " + st["publishAt"]) if st.get("publishAt") else ""
        print(f"{it['id']}  {st.get('privacyStatus', '?'):8} {when:34} upload={st.get('uploadStatus')} "
              f"processing={pd.get('processingStatus')} length={it['contentDetails'].get('duration')} uploaded={sn.get('publishedAt')}\n"
              f"    {sn.get('title')}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
