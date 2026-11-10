"""earth_ground: fetch a few more Poly Haven models (CC0) through the official API, asset files only (same rules as
assets/earth_library/_tools/fetch_ph.py).  fetch_models.py <library root> <asset id> [...]"""
import json, os, sys, urllib.request, urllib.parse
ROOT = sys.argv[1]
UA = {"User-Agent": "earth-assets-fetch/1.0"}
OK_EXT = {".jpg", ".png", ".exr", ".gltf", ".bin"}
OK_HOSTS = {"dl.polyhaven.org", "cdn.polyhaven.com", "api.polyhaven.com"}


def get(url, dest=None):
    u = urllib.parse.urlparse(url)
    assert u.scheme == "https" and u.hostname in OK_HOSTS, url
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        data = r.read()
    if dest is None: return data
    assert os.path.splitext(dest)[1].lower() in OK_EXT, dest
    full = os.path.realpath(dest)
    assert full.startswith(os.path.realpath(ROOT) + os.sep), dest
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f: f.write(data)
    return len(data)


for aid in sys.argv[2:]:
    try:
        f = json.loads(get("https://api.polyhaven.com/files/" + aid))
        d = os.path.join(ROOT, "polyhaven", "models", aid)
        g = f["gltf"]["2k"]["gltf"]
        n = get(g["url"], os.path.join(d, aid + "_2k.gltf"))
        for rel, inc in g.get("include", {}).items():
            assert not rel.startswith("/") and ".." not in rel.split("/"), rel
            n += get(inc["url"], os.path.join(d, rel))
        n += get("https://cdn.polyhaven.com/asset_img/thumbs/%s.png?width=512&height=512" % aid, os.path.join(d, aid + "_preview.png"))
        print("OK", aid, "%.1f MB" % (n / 1e6), flush=True)
    except Exception as e:
        print("FAILED", aid, repr(e), flush=True)
