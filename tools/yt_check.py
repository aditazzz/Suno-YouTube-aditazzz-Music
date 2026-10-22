"""Print YouTube's processing/upload status for video ids (why a video shows "unavailable").
usage: python3 tools/yt_check.py ID [ID ...]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import youtube_upload as Y
yt = Y.service()
r = yt.videos().list(part="status,processingDetails,snippet,contentDetails", id=",".join(sys.argv[1:])).execute()
found = set()
for it in r.get("items", []):
    found.add(it["id"]); st = it["status"]; pd = it.get("processingDetails", {})
    print(f"{it['id']}  {it['snippet']['title'][:60]}")
    print(f"   privacy={st.get('privacyStatus')} upload={st.get('uploadStatus')} rejection={st.get('rejectionReason')} failure={st.get('failureReason')}")
    print(f"   processing={pd.get('processingStatus')} {pd.get('processingFailureReason', '')}  duration={it['contentDetails'].get('duration')}  region={it['contentDetails'].get('regionRestriction')}")
for i in sys.argv[1:]:
    if i not in found: print(i, " not returned by the API (deleted, or not on this channel)")
