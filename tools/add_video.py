#!/usr/bin/env python3
"""Add a Short or a "Behind the code" video to the website's other two tabs, then rebuild the site.

  python3 tools/add_video.py behind <YouTube id> --title "How I sync lyrics to the vocals" --secs 612 \
      --blurb "The sync step, from the separated vocal to a timestamp on every word"
  python3 tools/add_video.py short <YouTube id> --title "One nit. Proof of life." --song lgtm

behind: a how-it's-made video (a tutorial, a making-of, a session). It goes first in the "Behind the code" tab.
short:  a Short. It goes first in the Shorts tab; --song links it to that song's page on the site, and --cover saves
        its cover (any vertical image) as site/shorts/<id>.jpg. Without one the tile shows YouTube's frame grab.
Running it again with the same id updates the entry instead of adding a second one.
Full music videos still go through tools/release.py, which gives each one its own page.
"""
import argparse, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser(description="Add a Short or a Behind the code video to aditazzz.github.io.")
    ap.add_argument("kind", choices=["behind", "short"])
    ap.add_argument("id", help="the YouTube video id")
    ap.add_argument("--title", required=True)
    ap.add_argument("--blurb", default="", help="behind: one line on what the video covers")
    ap.add_argument("--secs", type=int, help="behind: the video's length in seconds")
    ap.add_argument("--song", help="short: the slug of the song it's cut from (as in site/videos.json)")
    ap.add_argument("--cover", help="short: the Short's cover image (vertical); saved 360x640 as site/shorts/<id>.jpg")
    ap.add_argument("--pages", default=os.path.join(ROOT, "..", "aditazzz.github.io"), help="the GitHub Pages repo")
    ap.add_argument("--no-build", action="store_true", help="only update the list, don't rebuild the site")
    a = ap.parse_args()
    if not re.fullmatch(r"[\w-]{11}", a.id):
        sys.exit(f"{a.id!r} doesn't look like a YouTube video id (11 characters, the part after youtu.be/)")

    if a.kind == "short":
        path = os.path.join(ROOT, "site", "shorts.json")
        if a.song and a.song not in json.load(open(os.path.join(ROOT, "site", "videos.json"), encoding="utf-8")):
            sys.exit(f"--song {a.song}: no such video in site/videos.json")
        entry = {"id": a.id, "title": a.title, "song": a.song}
        if a.cover:
            from PIL import Image, ImageOps
            os.makedirs(os.path.join(ROOT, "site", "shorts"), exist_ok=True)
            ImageOps.fit(Image.open(a.cover).convert("RGB"), (360, 640), Image.LANCZOS).save(
                os.path.join(ROOT, "site", "shorts", a.id + ".jpg"), quality=80, optimize=True, progressive=True)
    else:
        path = os.path.join(ROOT, "site", "behind.json")
        entry = {"id": a.id, "title": a.title, "blurb": a.blurb}
        if a.secs: entry["secs"] = a.secs

    items = [x for x in json.load(open(path, encoding="utf-8")) if x["id"] != a.id]
    items.insert(0, entry)                                    # newest first
    open(path, "w", encoding="utf-8").write(json.dumps(items, indent=1, ensure_ascii=False) + "\n")
    print(f"{os.path.relpath(path, ROOT)}: {a.title} ({len(items)} in the list)")

    if not a.no_build:
        pages = os.path.abspath(a.pages)
        if not os.path.isdir(os.path.join(pages, ".git")):
            sys.exit(f"no Pages repo at {pages}: clone https://github.com/aditazzz/aditazzz.github.io there, or pass --pages")
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_site.py"), pages], check=True)
        print("site rebuilt; commit and push both repos to publish it")


if __name__ == "__main__":
    main()
