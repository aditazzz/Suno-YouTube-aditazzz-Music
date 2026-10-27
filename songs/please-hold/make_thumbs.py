"""Please Hold thumbnails: the brand cover (studio/brand.py, the same lockup chip, Anton headline and italic line as every
other video) over 3D plates rendered for the purpose (web: ?look=thumb). What the cover says and how the plate is framed
are in song.yaml (thumb_lines, thumb_sub, brand_accent, ctx_shift_y), like any other song.

usage: python3 songs/please-hold/make_thumbs.py OUT_DIR PLATE.jpg [OPTION_PLATE.jpg ...]
Writes "Please Hold - YouTube thumbnail.jpg", "(no text)" and "option N" for each extra plate (Test & Compare)."""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, ROOT)
from studio import brand
from studio.config import load_song


if __name__ == "__main__":
    out = sys.argv[1]; plates = sys.argv[2:]; os.makedirs(out, exist_ok=True)
    song = load_song(HERE); T = song["title"]
    for k, p in enumerate(plates):
        base = Image.open(p).convert("RGB").resize((1920, 1080), Image.LANCZOS)
        if k == 0: base.save(os.path.join(out, f"{T} - YouTube thumbnail (no text).jpg"), quality=93)
        nm = f"{T} - YouTube thumbnail.jpg" if k == 0 else f"{T} - YouTube thumbnail option {k + 1}.jpg"
        brand.song_cover(song, base, slug="please-hold").save(os.path.join(out, nm), quality=93); print("wrote", nm)
