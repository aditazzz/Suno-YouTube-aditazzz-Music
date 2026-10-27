#!/usr/bin/env python3
"""The last step of the pipeline: put a posted video on the website (aditazzz.github.io).

  python3 tools/release.py <slug> --id <YouTube id> [--date 2026-10-27T08:48:43-07:00] [--secs 213]
                           [--pages ../aditazzz.github.io] [--push]

It adds the video to site/videos.json (YouTube id, publish time, length), redraws the wall of thumbnails at the top of
the README (tools/wall.py) and rebuilds the site into the GitHub Pages repo (tools/build_site.py): the video's own page
(the video, the story, the lyrics, the numbers and a panel of its code), the home page, the sitemap and the share card.
With --push it commits and pushes both repos. Running it again for a released video updates its entry.

The song folder has to be in songs/ first, with its README (linking the video), lyrics.txt, thumbnail.jpg and every
file its code table lists. The publish time is the video's "publishDate" on YouTube (default: now); the length
defaults to the song (build/beats.json) plus its end card (song.yaml tail).
"""
import argparse, datetime, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://aditazzz.github.io"


def run(cmd, cwd=ROOT):
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def staged(repo):
    return subprocess.run(["git", "-C", repo, "diff", "--cached", "--name-only"], check=True, capture_output=True,
                          text=True).stdout.split()


def commit_push(repo, paths, message, footer):
    run(["git", "-C", repo, "add", *paths])
    if not staged(repo):
        print(f"  nothing to commit in {repo}", flush=True); return
    run(["git", "-C", repo, "commit", "-q", "-m", message] + (["-m", footer] if footer else []))
    run(["git", "-C", repo, "push", "-q"])


def check_folder(slug, vid):
    folder = os.path.join(ROOT, "songs", slug)
    missing = [f for f in ("README.md", "lyrics.txt", "thumbnail.jpg") if not os.path.exists(os.path.join(folder, f))]
    if missing:
        sys.exit(f"songs/{slug} is missing {', '.join(missing)}: add the song folder to the repo first")
    md = open(os.path.join(folder, "README.md"), encoding="utf-8").read()
    if vid not in md:
        print(f"  WARNING: songs/{slug}/README.md doesn't link https://youtu.be/{vid}", flush=True)
    for f in re.findall(r"^\| \[`([^`]+)`\]", md, flags=re.M):          # every file the README's code table lists
        if not os.path.exists(os.path.join(folder, f)):
            sys.exit(f"songs/{slug}/README.md lists {f}, which isn't in the folder")
    return folder, md.splitlines()[0].lstrip("# ").strip()


def length_secs(folder):
    """The video's length: the song (build/beats.json) plus song.yaml's tail (the end card)."""
    b, y = os.path.join(folder, "build", "beats.json"), os.path.join(folder, "song.yaml")
    if not os.path.exists(b): return None
    tail = 0.0
    if os.path.exists(y):
        import yaml
        tail = float((yaml.safe_load(open(y, encoding="utf-8")) or {}).get("tail", 0))
    return round(json.load(open(b))["duration"] + tail)


def main():
    ap = argparse.ArgumentParser(description="Put a posted video on aditazzz.github.io (the pipeline's last step).")
    ap.add_argument("slug", help="the song folder in songs/ (its name, or songs/<name>)")
    ap.add_argument("--id", required=True, help="the YouTube video id")
    ap.add_argument("--date", help="when it was published, ISO 8601 with the UTC offset (default: now)")
    ap.add_argument("--secs", type=int, help="the video's length in seconds (default: beats.json + song.yaml tail)")
    ap.add_argument("--pages", default=os.path.join(ROOT, "..", "aditazzz.github.io"), help="the GitHub Pages repo")
    ap.add_argument("--push", action="store_true", help="commit and push this repo and the Pages repo")
    ap.add_argument("--footer", default="", help="a last paragraph for both commit messages (e.g. co-author lines)")
    a = ap.parse_args()
    a.slug = os.path.basename(os.path.normpath(a.slug))

    folder, title = check_folder(a.slug, a.id)
    secs = a.secs or length_secs(folder)
    if not secs: sys.exit("give --secs: there's no build/beats.json to work the length out from")
    date = a.date or datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    pages = os.path.abspath(a.pages)
    if not os.path.isdir(os.path.join(pages, ".git")):
        sys.exit(f"no Pages repo at {pages}: clone https://github.com/aditazzz/aditazzz.github.io there, or pass --pages")

    p = os.path.join(ROOT, "site", "videos.json")
    vids = json.load(open(p, encoding="utf-8"))
    vids[a.slug] = {"id": a.id, "date": date, "secs": int(secs)}
    open(p, "w", encoding="utf-8").write(json.dumps(vids, indent=1, ensure_ascii=False))
    print(f"site/videos.json: {a.slug} = {vids[a.slug]}", flush=True)

    run([sys.executable, "tools/wall.py"])                         # the README's wall of thumbnails (and the site's)
    run([sys.executable, "tools/build_site.py", pages])            # every page, the sitemap and the share card

    if a.push:
        commit_push(ROOT, ["site/videos.json", "docs/img/wall.jpg"], f"{title}: on the website and the wall", a.footer)
        commit_push(pages, ["-A"], f"{title}: its video page, on the home page, in the sitemap and on the share card", a.footer)
    print(f"released: {SITE}/videos/{a.slug}/  (GitHub Pages takes a minute or two to update)", flush=True)


if __name__ == "__main__":
    main()
