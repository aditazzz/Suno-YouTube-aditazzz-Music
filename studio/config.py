"""Paths + song.yaml loading."""
import os, re, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cfg_path = os.path.join(ROOT, "studio.yaml")
CFG = yaml.safe_load(open(_cfg_path)) if os.path.exists(_cfg_path) else {}

def _first_existing(cands):
    """The first folder that exists (relative paths are relative to the repo), else the first candidate."""
    cands = [os.path.join(ROOT, os.path.expanduser(os.path.expandvars(c))) for c in cands if c]
    for c in cands:
        if os.path.isdir(c): return c
    return cands[0]

# the song audio and the finished videos: $MUSIC_DIR, else studio.yaml music_dir_candidates, else ./music
MUSIC_DIR = _first_existing([os.environ.get("MUSIC_DIR", ""), *CFG.get("music_dir_candidates", []), "music"])
MODELS = os.path.join(ROOT, "models")
SONGS = os.path.join(ROOT, "songs")

def load_song(song_dir):
    s = yaml.safe_load(open(os.path.join(song_dir, "song.yaml")))
    s["dir"] = os.path.abspath(song_dir)
    s.setdefault("slug", os.path.basename(os.path.abspath(song_dir)))
    a = s["audio"]
    s["audio"] = a if os.path.isabs(a) else os.path.join(MUSIC_DIR, a)
    s["out_dir"] = os.path.join(MUSIC_DIR, s.get("folder", s["title"]))
    s["build"] = os.path.join(song_dir, "build")
    return s

def public_name(song):
    """The song's name as it appears in YouTube titles and on covers: no parentheses, so a title reads
    'Name - Claude Opus 5.5 Music Video' and the Claude part stays visible. song.yaml `yt_name` overrides."""
    return song.get("yt_name") or " ".join(re.sub(r"\([^)]*\)", "", song["title"]).split())

# ---------------------------------------------------------------- AI Doompop (the AI-risk pop genre named on LessWrong, Oct 2026)
DOOMPOP = "AIDoompop"
DOOMPOP_TAGS = ["ai doompop", "aidoompop", "doompop"]

def doompop(song):
    """True for songs in the AI Doompop genre: studio.yaml `doompop:` lists their slugs; song.yaml youtube.doompop: true/false overrides."""
    v = (song.get("youtube") or {}).get("doompop")
    return bool(v) if v is not None else song.get("slug") in (CFG.get("doompop") or [])

def _has_doompop(t): return re.search(r"#aidoompop\b", t or "", re.I) is not None
def n_hashtags(t): return len(re.findall(r"(?<![\w#])#\w", t or ""))

def doompop_title(t, limit=100):
    """'Name - Claude Opus 5.5 Music Video' -> 'Name - Claude Opus 5.5 Music Video #AIDoompop' (unchanged if already there or too long)."""
    if _has_doompop(t): return t
    n = f"{t.rstrip()} #{DOOMPOP}"
    return n if len(n) <= limit else t

def doompop_desc(d, title="", max_tags=15):
    """#AIDoompop at the front of the description's last hashtag line (or as a new last line). Skipped if it would push the
    video past 15 hashtags (YouTube then ignores them all) or past 5,000 characters."""
    if _has_doompop(d) or n_hashtags(d) + n_hashtags(title) + (0 if _has_doompop(title) else 1) > max_tags: return d
    lines = d.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        ws = lines[i].split()
        if ws and all(w.startswith("#") for w in ws):
            lines[i] = f"#{DOOMPOP} " + lines[i].lstrip(); out = "\n".join(lines); break
    else: out = d.rstrip() + f"\n\n#{DOOMPOP}"
    return out if len(out) <= 5000 else d

def doompop_tags(tags):
    """'ai doompop', 'aidoompop', 'doompop' first (tag lists are trimmed from the end), then the rest without duplicates."""
    low = {t.lower() for t in DOOMPOP_TAGS}
    return [*DOOMPOP_TAGS, *[t for t in (tags or []) if str(t).lower() not in low]]
