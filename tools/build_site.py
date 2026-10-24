#!/usr/bin/env python3
"""Build the static site at aditazzz.github.io from this repo.

Every song folder with a public video becomes a page: the video, the story, the lyrics, the numbers, and a panel of
real code from its scene that "decrypts" when the video starts playing. The home page is a gallery of all of them.
Everything is plain HTML and CSS with one small script, so search engines read it all and pages load fast.

usage:
  python3 tools/build_site.py ../aditazzz.github.io          # writes the site into that folder (the Pages repo)

Video dates and lengths live in site/videos.json (slug -> YouTube id, upload date, length in seconds). Add a line there
when a video goes public; songs without an entry are left off the site.
"""
import ast, html, io, json, keyword, os, re, shutil, sys, tokenize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://aditazzz.github.io"
REPO = "https://github.com/aditazzz/Suno-YouTube-aditazzz-Music"
YT = "https://www.youtube.com/@adita_zzz"
SUB = YT + "?sub_confirmation=1"
SPOTIFY = "https://open.spotify.com/artist/7mi7sz2NTgTWUAj1zmijJv"
INSTAGRAM = "https://www.instagram.com/aditazzz.music/"
LINKTREE = "https://linktr.ee/aditazzz"
LINKEDIN = "https://www.linkedin.com/in/aditazeqollari"
REDDIT = "https://www.reddit.com/r/aidoompop/"   # the AI Doompop subreddit
# Google Search Console ownership token (URL-prefix property for SITE). It is public by design: Google reads it from the
# live home page. Keep it here so a rebuild never drops it.
GSC_VERIFY = "KsjTLDJ1Qvirn6xuLeXUbLTs20i_d3ELdcQKPKiwSVM"
ABOUT = ("aditazzz makes AI-assisted music about technology, artificial intelligence, coding, philosophy and the human "
         "experience. Every music video is animated entirely in code with Claude.")
ARTIST = {"@type": "MusicGroup", "@id": SITE + "/#artist", "name": "aditazzz", "url": SITE + "/", "image": SITE + "/assets/aditazzz.jpg",
          "description": ABOUT, "genre": ["AI Doompop", "Darkwave", "Synthpop"],
          "sameAs": [YT, SPOTIFY, INSTAGRAM, LINKTREE, LINKEDIN, REDDIT, "https://github.com/aditazzz"]}
WEBSITE = {"@type": "WebSite", "@id": SITE + "/#site", "name": "aditazzz", "url": SITE + "/", "inLanguage": "en",
           "description": ABOUT, "publisher": {"@id": ARTIST["@id"]}}
# The social card: a 1200x630 (1.91:1) crop of the right four tile columns of the video wall, which keeps the "27 music videos"
# and @adita_zzz panel. The full wall is 3.1:1, which Facebook, X and LinkedIn crop at the edges.
CARD = "/assets/card.jpg"
IMG_SIZES = {CARD: (1200, 630)}   # filled in for the thumbnails as they are copied
SECTION_NAMES = {"INTRO": "Intro", "V": "Verse", "PRE": "Pre-chorus", "CH": "Chorus", "POST": "Post-chorus",
                 "BRIDGE": "Bridge", "BREAK": "Break", "BREAKDOWN": "Breakdown", "FINAL": "Final chorus",
                 "OUTRO": "Outro", "BUILD": "Build", "TAG": "Tag", "TURN": "Turn", "REFRAIN": "Refrain", "PEAK": "Peak"}
esc = html.escape


# ------------------------------------------------------------------ reading a song folder
def md_inline(s):
    """The little markdown the READMEs use inside a paragraph: code, bold, italics, links."""
    s = esc(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?!\w)", r"<em>\1</em>", s)
    def link(m):
        text, url = m.group(1), m.group(2)
        if not re.match(r"https?://", url):   # a path inside the repo
            url = REPO + "/tree/main/" + os.path.normpath(os.path.join("songs", CUR_SLUG, url)).replace(os.sep, "/")
        return f'<a href="{url}">{text}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, s)


def md_section(md, name):
    """Paragraphs of one '## name' section of a README, as HTML."""
    m = re.search(r"^## " + re.escape(name) + r"\s*\n(.*?)(?=^## |\Z)", md, re.M | re.S)
    if not m: return ""
    out = []
    for block in re.split(r"\n\s*\n", m.group(1).strip()):
        block = block.strip()
        if not block or block.startswith("|") or block.startswith("```") or block == "---": continue
        if block.startswith("- "):
            items = [md_inline(x[2:].strip()) for x in block.splitlines() if x.startswith("- ")]
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
        else:
            out.append(f"<p>{md_inline(' '.join(block.split()))}</p>")
    return "\n".join(out)


def code_table(md):
    m = re.search(r"^## The code\s*\n(.*?)(?=^## |\Z)", md, re.M | re.S)
    rows = []
    for line in (m.group(1) if m else "").splitlines():
        c = re.match(r"\| \[`([^`]+)`\]\([^)]+\) \| ([\d,]+) \| (.*) \|$", line)
        if c: rows.append((c.group(1), int(c.group(2).replace(",", "")), c.group(3).replace("\\|", "|")))
    return rows


def lyrics_html(path):
    stanzas, cur, label = [], [], None
    for line in open(path, encoding="utf-8").read().splitlines():
        line = line.strip()
        if line.startswith("#"):
            if cur: stanzas.append((label, cur))
            tag = line[1:].strip().upper(); base = re.sub(r"\d+$", "", tag)
            label = SECTION_NAMES.get(base, base.title()); cur = []
        elif line:
            cur.append(line)
    if cur: stanzas.append((label, cur))
    return "\n".join(f'<div class="stanza"><p class="sec">{esc(l or "")}</p><p>' + "<br>".join(esc(x) for x in lines) +
                     "</p></div>" for l, lines in stanzas), sum(len(l) for _, l in stanzas)


def excerpt(folder):
    """The heart of the scene: render_frame() from scene.py, or the top of the file. The earlier standalone videos have no
    scene.py: their main file is the first row of the README's code table, and the excerpt is its render() or chorus."""
    path = os.path.join(folder, "scene.py")
    if not os.path.exists(path):
        rows = code_table(open(os.path.join(folder, "README.md"), encoding="utf-8").read()); path = os.path.join(folder, rows[0][0])
    src = open(path, encoding="utf-8").read(); lines = src.splitlines()
    a, b = 0, min(len(lines), 48)
    for want in ("render_frame", "render", "sec_chorus"):
        hit = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == want]
        if hit:
            node = hit[0]; a, b = node.lineno - 1, min(node.end_lineno, node.lineno - 1 + 56); break
    return "\n".join(lines[a:b]), a + 1, b < len(lines) and b != len(lines), os.path.basename(path)


def highlight(code):
    """Python syntax colours from the tokenizer (no library)."""
    out, pos_lines = [], code.splitlines(keepends=True)
    offs = [0]
    for l in pos_lines: offs.append(offs[-1] + len(l))
    def at(rc): return offs[rc[0] - 1] + rc[1]
    last = 0
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return esc(code)
    prev = None
    for t in toks:
        if t.type in (tokenize.ENDMARKER,): break
        s, e = at(t.start), at(t.end)
        if s < last: continue
        out.append(esc(code[last:s]))
        txt = esc(code[s:e]); cls = None
        if t.type == tokenize.COMMENT: cls = "c"
        elif t.type == tokenize.STRING or (hasattr(tokenize, "FSTRING_START") and t.type in (tokenize.FSTRING_START, tokenize.FSTRING_MIDDLE, tokenize.FSTRING_END)): cls = "s"
        elif t.type == tokenize.NUMBER: cls = "n"
        elif t.type == tokenize.NAME and keyword.iskeyword(t.string): cls = "k"
        elif t.type == tokenize.NAME and prev == "def": cls = "f"
        out.append(f'<span class="{cls}">{txt}</span>' if cls else txt)
        prev = t.string if t.type == tokenize.NAME else None
        last = e
    out.append(esc(code[last:]))
    return "".join(out)


def iso_dur(sec):
    m, s = divmod(int(sec), 60); return f"PT{m}M{s}S"


def mmss(sec):
    m, s = divmod(int(sec), 60); return f"{m}:{s:02d}"


def icon(name):
    """A brand logo from site/icons (Simple Icons, CC0), inlined so it takes the text colour."""
    svg = open(os.path.join(ROOT, "site", "icons", name + ".svg")).read()
    path = re.search(r'<path d="([^"]+)"', svg).group(1)
    return f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="{path}"/></svg>'


def socials():
    links = [("Instagram", INSTAGRAM, "instagram"), ("r/aidoompop on Reddit", REDDIT, "reddit"),
             ("LinkedIn", LINKEDIN, "linkedin"), ("GitHub", REPO, "github"), ("All links", LINKTREE, "linktree")]
    return '<p class="socials">' + "".join(f'<a href="{u}" aria-label="{n}" title="{n}">{icon(i)}</a>' for n, u, i in links) + "</p>"


# ------------------------------------------------------------------ page shell
FONTS = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Sans:wght@400;500;600"
         "&family=JetBrains+Mono:wght@400;600&display=swap")


def song_title(t):
    """A search title that keeps the artist name inside the ~60 characters Google shows."""
    for c in (f"{t} by aditazzz: music video made in code", f"{t} by aditazzz: music video", f"{t} by aditazzz"):
        if len(c) <= 62: return c
    return f"{t} | aditazzz"


def clip(s, n=158):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n - 1].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"


def page(*, path, title, desc, image, image_alt, body, ld, og_type="website", extra_head="", indexable=True):
    url = SITE + path
    w, h = IMG_SIZES.get(image, (None, None))
    size = f'\n<meta property="og:image:width" content="{w}">\n<meta property="og:image:height" content="{h}">' if w else ""
    # a page that isn't meant to be indexed (the 404) gets noindex and no canonical or og:url
    meta = (f'<meta name="robots" content="index, follow, max-image-preview:large">\n<link rel="canonical" href="{url}">'
            if indexable else '<meta name="robots" content="noindex">')
    og_url = f'\n<meta property="og:url" content="{url}">' if indexable else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{extra_head}<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{meta}
<meta name="author" content="aditazzz">
<meta name="theme-color" content="#0c0c0b">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="aditazzz">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">{og_url}
<meta property="og:image" content="{SITE + image}">{size}
<meta property="og:image:alt" content="{esc(image_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE + image}">
<meta name="twitter:image:alt" content="{esc(image_alt)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap bar">
  <a class="mark" href="/" aria-label="aditazzz home">aditazzz</a>
  <nav aria-label="Main"><a href="/#videos">Videos</a><a href="/#how">How it's made</a><a href="{REPO}">Code</a><a class="sub" href="{SUB}">Subscribe</a></nav>
</div></header>
<main id="main">
{body}
</main>
<footer class="foot"><div class="wrap">
  <p class="links"><a href="{SUB}">YouTube</a><a href="{SPOTIFY}">Spotify</a><a href="{INSTAGRAM}">Instagram</a><a href="{REDDIT}">r/aidoompop</a><a href="{REPO}">GitHub</a><a href="{LINKEDIN}">LinkedIn</a><a href="{LINKTREE}">All links</a></p>
  <p class="fine">Songs, lyrics and concepts by aditazzz. Videos written in code by Claude. The code is MIT-licensed; the songs, lyrics and artwork are all rights reserved.</p>
</div></footer>
<script src="/assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


# ------------------------------------------------------------------ build
def main(out):
    global CUR_SLUG
    vids = json.load(open(os.path.join(ROOT, "site", "videos.json")))
    songs = []
    for slug, v in vids.items():
        CUR_SLUG = slug
        folder = os.path.join(ROOT, "songs", slug); md = open(os.path.join(folder, "README.md"), encoding="utf-8").read()
        title = md.splitlines()[0].lstrip("# ").strip()
        story = " ".join(l.lstrip("> ").strip() for l in md.splitlines() if l.startswith(">")).strip()
        rows = code_table(md); lines = sum(n for _, n, _ in rows)
        lyr, nlines = lyrics_html(os.path.join(folder, "lyrics.txt"))
        code, first_line, more, main = excerpt(folder)
        mm = re.search(r"Video by (Claude [A-Za-z]+ [\d.]+)", md); model = mm.group(1) if mm else "Claude"
        songs.append(dict(slug=slug, id=v["id"], date=v["date"], secs=v["secs"], title=title, story=story, md=md,
                          rows=rows, lines=lines, lyrics=lyr, code=code, first=first_line, more=more, main=main, model=model))
    songs.sort(key=lambda s: s["date"], reverse=True)

    if os.path.isdir(out):
        for name in os.listdir(out):
            if name in (".git", "CNAME", "googleverify.html") or name.startswith("google"): continue
            p = os.path.join(out, name); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(os.path.join(out, "assets"), exist_ok=True)
    for f in ("site.css", "site.js", "favicon.svg", "aditazzz.jpg"):
        shutil.copy(os.path.join(ROOT, "site", f), os.path.join(out, "assets" if f != "favicon.svg" else "", f))
    shutil.copy(os.path.join(ROOT, "docs", "img", "wall.jpg"), os.path.join(out, "assets", "wall.jpg"))
    from PIL import Image
    wall = Image.open(os.path.join(ROOT, "docs", "img", "wall.jpg")).convert("RGB")
    cw = wall.width * 4 // 7; ch = round(cw * 630 / 1200); top = (wall.height - ch) // 2   # the last 4 of 7 tile columns
    wall.crop((wall.width - cw, top, wall.width, top + ch)).resize((1200, 630), Image.LANCZOS).save(
        os.path.join(out, CARD.lstrip("/")), quality=88, optimize=True, progressive=True)
    open(os.path.join(out, ".nojekyll"), "w").close()

    total = sum(s["lines"] for s in songs)
    # ---- song pages
    for i, s in enumerate(songs):
        CUR_SLUG = s["slug"]
        d = os.path.join(out, "videos", s["slug"]); os.makedirs(d, exist_ok=True)
        shutil.copy(os.path.join(ROOT, "songs", s["slug"], "thumbnail.jpg"), os.path.join(d, "thumbnail.jpg"))
        path = f"/videos/{s['slug']}/"; img = path + "thumbnail.jpg"
        IMG_SIZES[img] = Image.open(os.path.join(d, "thumbnail.jpg")).size
        watch = f"https://www.youtube.com/watch?v={s['id']}"
        story = re.sub(r"\*+|`|\[([^\]]+)\]\([^)]+\)", r"\1", s["story"])   # plain text for meta tags
        long_desc = story or f"{s['title']}, a music video by aditazzz animated entirely in code with Claude."
        # leading with the title and artist keeps every description unique (alternate versions share a story)
        desc = clip(f"{s['title']} by aditazzz. {long_desc}" if story else long_desc)
        title = song_title(s["title"])
        seen = md_section(s["md"], "What you see")
        nums = md_section(s["md"], "By the numbers")
        table = "".join(f'<tr><td><a href="{REPO}/blob/main/songs/{s["slug"]}/{f}"><code>{esc(f)}</code></a></td>'
                        f'<td class="num">{n:,}</td><td>{md_inline(w)}</td></tr>' for f, n, w in s["rows"])
        attrib = (f'# From "{s["title"]}" by aditazzz, a music video written in code with Claude.\n'
                  f"# Watch: https://youtu.be/{s['id']}\n# Subscribe: {SUB}\n"
                  f"# Code: {REPO}/tree/main/songs/{s['slug']} (MIT). If you use it, please credit aditazzz and link the video.\n\n")
        nxt = songs[(i + 1) % len(songs)]
        ld = {"@context": "https://schema.org", "@graph": [
            WEBSITE, ARTIST,
            {"@type": "WebPage", "@id": SITE + path, "url": SITE + path, "name": title, "description": desc,
             "inLanguage": "en", "isPartOf": {"@id": WEBSITE["@id"]}, "primaryImageOfPage": SITE + img,
             "mainEntity": {"@id": SITE + path + "#video"}, "breadcrumb": {"@id": SITE + path + "#crumbs"}},
            {"@type": "VideoObject", "@id": SITE + path + "#video", "name": s["title"], "description": long_desc,
             "thumbnailUrl": [SITE + img, f"https://i.ytimg.com/vi/{s['id']}/maxresdefault.jpg"],
             "uploadDate": s["date"], "duration": iso_dur(s["secs"]), "embedUrl": f"https://www.youtube.com/embed/{s['id']}",
             "url": watch, "author": {"@id": ARTIST["@id"]}, "genre": "AI Doompop", "inLanguage": "en"},
            {"@type": "MusicRecording", "@id": SITE + path + "#recording", "name": s["title"], "url": SITE + path,
             "image": SITE + img, "subjectOf": {"@id": SITE + path + "#video"}, "byArtist": {"@id": ARTIST["@id"]},
             "duration": iso_dur(s["secs"]), "recordingOf": {"@type": "MusicComposition", "name": s["title"],
             "lyricist": {"@id": ARTIST["@id"]}}},
            {"@type": "SoftwareSourceCode", "name": f"{s['title']} scene code", "codeRepository": f"{REPO}/tree/main/songs/{s['slug']}",
             "programmingLanguage": "Python", "license": "https://opensource.org/licenses/MIT"},
            {"@type": "BreadcrumbList", "@id": SITE + path + "#crumbs", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Videos", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": s["title"], "item": SITE + path}]}]}
        body = f"""<article class="wrap song">
  <p class="crumb"><a href="/#videos">Videos</a> <span aria-hidden="true">/</span> {esc(s['title'])}</p>
  <h1>{esc(s['title'])}</h1>
  {f'<p class="story">{md_inline(s["story"])}</p>' if s['story'] else ''}
  <div class="player">
    <button class="yt" data-id="{s['id']}" aria-label="Play {esc(s['title'])}">
      <img src="thumbnail.jpg" alt="{esc(s['title'])}: music video thumbnail" width="960" height="540">
      <span class="play" aria-hidden="true"></span>
    </button>
    <p class="under"><a href="{watch}">Watch on YouTube</a> · {mmss(s['secs'])} · video by {esc(s['model'])} · <a class="subscribe" href="{SUB}">Subscribe to @adita_zzz</a></p>
  </div>

  <section class="code" aria-labelledby="code-h">
    <div class="code-head"><h2 id="code-h">The code behind it</h2>
      <p>Every frame of this video is drawn by a Python program. This is the heart of it, from <code>{esc(s['main'])}</code>, line {s['first']}.</p></div>
    <div class="term" data-lock>
      <div class="term-bar"><span></span><span></span><span></span><b>songs/{s['slug']}/{esc(s['main'])}</b>
        <button class="copy" type="button" data-copy>Copy with credit</button></div>
      <pre><code>{highlight(s['code'])}{chr(10) + '    ...' if s['more'] else ''}</code></pre>
      <div class="veil" aria-hidden="true"><p class="veil-t">ENCRYPTED</p><p>Press play on the video to decrypt the code.</p>
        <button type="button" class="veil-b" data-unlock>Decrypt it now</button></div>
      <textarea hidden data-attrib>{esc(attrib)}</textarea>
    </div>
    <p class="more"><a href="{REPO}/tree/main/songs/{s['slug']}">Read all {s['lines']:,} lines on GitHub</a>. If you use it, credit aditazzz and link the video.</p>
  </section>

  {'<section><h2>What you see</h2>' + seen + '</section>' if seen else ''}

  <section class="files"><h2>Files</h2>
    <div class="tablewrap"><table><thead><tr><th>File</th><th class="num">Lines</th><th>What it draws</th></tr></thead><tbody>{table}</tbody></table></div>
  </section>

  {'<section><h2>By the numbers</h2>' + nums + '</section>' if nums else ''}

  <section class="lyrics"><h2>Lyrics</h2><p class="by">Words and music by aditazzz.</p>{s['lyrics']}</section>

  <aside class="next"><a href="/videos/{nxt['slug']}/"><img src="/videos/{nxt['slug']}/thumbnail.jpg" alt="" width="320" height="180" loading="lazy">
    <span><small>Next video</small>{esc(nxt['title'])}</span></a></aside>
</article>"""
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
            page(path=path, title=title, desc=desc, image=img, image_alt=f"{s['title']} by aditazzz: music video thumbnail",
                 body=body, ld=ld, og_type="video.other"))

    # ---- home
    cards = "".join(f"""<li><a href="/videos/{s['slug']}/"><img src="/videos/{s['slug']}/thumbnail.jpg" alt="{esc(s['title'])}" width="960" height="540" loading="{'eager' if i < 3 else 'lazy'}">
      <span class="t">{esc(s['title'])}</span><span class="m">{mmss(s['secs'])} · {s['lines']:,} lines of code</span></a></li>""" for i, s in enumerate(songs))
    home_title = "aditazzz: AI music & music videos made in code with Claude"
    home_desc = (f"aditazzz makes AI-assisted music about technology, AI, coding, philosophy and the human experience. "
                 f"{len(songs)} music videos, every frame animated in code with Claude.")
    ld = {"@context": "https://schema.org", "@graph": [
        WEBSITE, ARTIST,
        {"@type": "WebPage", "@id": SITE + "/", "url": SITE + "/", "name": home_title, "description": home_desc,
         "inLanguage": "en", "isPartOf": {"@id": WEBSITE["@id"]}, "about": {"@id": ARTIST["@id"]},
         "primaryImageOfPage": SITE + CARD, "mainEntity": {"@id": SITE + "/#videos"}},
        {"@type": "ItemList", "@id": SITE + "/#videos", "name": "Music videos made in code", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/videos/{s['slug']}/", "name": s["title"]} for i, s in enumerate(songs)]}]}
    body = f"""<section class="hero wrap"><div class="hero-text">
  <p class="eyebrow">AI Doompop · darkwave · synthpop</p>
  <h1>Music videos <em>written in code.</em></h1>
  <p class="lead">I'm aditazzz, a data and AI engineer who writes songs about AI, code and tech life. I write the lyrics and the concept and make each track in Suno. Claude then writes a Python program that draws the music video frame by frame, synced to the vocals word by word.</p>
  <p class="cta"><a class="btn" href="{SUB}">Subscribe on YouTube</a><a class="btn ghost" href="{SPOTIFY}">Listen on Spotify</a></p>
  {socials()}
  <dl class="stats"><div><dt>Videos</dt><dd>{len(songs)}</dd></div><div><dt>Lines of code</dt><dd>{total:,}</dd></div><div><dt>Video editors</dt><dd>0</dd></div></dl>
</div><img class="me" src="/assets/aditazzz.jpg" alt="Portrait of aditazzz" width="480" height="480"></section>
<section id="videos" class="wrap"><h2 class="h">The videos</h2><ul class="grid">{cards}</ul></section>
<section id="how" class="wrap how"><h2 class="h">How a video gets made</h2>
  <ol>
    <li><h3>The song</h3><p>I write the lyrics and the concept, then make the track in Suno.</p></li>
    <li><h3>The sync</h3><p>The vocals are separated, transcribed and lined up with the lyrics, so every sung word gets a timestamp. Beats and sections come from the audio too.</p></li>
    <li><h3>The scene</h3><p>Claude writes one program per song, a function that returns the picture at any moment of the song. I direct it and review every still.</p></li>
    <li><h3>The render</h3><p>Every frame is drawn at 1080p, 30 fps, for YouTube and for Shorts, then cut, packaged and uploaded by the same pipeline.</p></li>
  </ol>
  <p class="more">All of it is open source: <a href="{REPO}">the pipeline and every scene on GitHub</a>.</p>
</section>"""
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page(
        path="/", title=home_title, desc=home_desc, image=CARD, image_alt=f"aditazzz: {len(songs)} music videos, every frame is code",
        body=body, ld=ld, extra_head=f'<meta name="google-site-verification" content="{GSC_VERIFY}">\n'))

    # ---- 404, robots, sitemap
    open(os.path.join(out, "404.html"), "w", encoding="utf-8").write(page(
        path="/404.html", title="Not found | aditazzz", desc="That page isn't here.", image=CARD,
        image_alt="aditazzz music videos", indexable=False,
        body='<section class="wrap hero plain"><h1>Not found.</h1><p class="lead">You\'re absolutely right, that page doesn\'t exist. <a href="/">See all the videos</a>.</p></section>',
        ld={"@context": "https://schema.org", "@type": "WebPage", "name": "Not found"}))
    open(os.path.join(out, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    # lastmod is the date a page's content last changed: a video page on its upload day, the home page with the newest video
    def img_tag(u, t): return f"<image:image><image:loc>{SITE + u}</image:loc></image:image>"
    urls = [(SITE + "/", songs[0]["date"][:10], img_tag(CARD, "aditazzz"))] + [
        (f"{SITE}/videos/{s['slug']}/", s["date"][:10], img_tag(f"/videos/{s['slug']}/thumbnail.jpg", s["title"])) for s in songs]
    open(os.path.join(out, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' +
        "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod>{i}</url>\n" for u, d, i in urls) + "</urlset>\n")
    open(os.path.join(out, "README.md"), "w").write(
        f"# aditazzz.github.io\n\nThe website for [aditazzz]({SITE}): AI Doompop music videos written in code with Claude.\n\n"
        f"It's generated by [`tools/build_site.py`]({REPO}/blob/main/tools/build_site.py) in the "
        f"[code repo]({REPO}); edit there, not here.\n")
    print(f"built {len(songs)} video pages, {total:,} lines of code -> {out}")


import hashlib
ASSET_V = hashlib.sha1(b"".join(open(os.path.join(ROOT, "site", f), "rb").read() for f in ("site.css", "site.js", "aditazzz.jpg"))).hexdigest()[:8]
CUR_SLUG = ""
if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "..", "aditazzz.github.io")))
