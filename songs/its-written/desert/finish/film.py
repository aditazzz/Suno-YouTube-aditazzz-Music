"""Frame numbers are inclusive and film-local. Only the C++ hero camera uses a local clock."""
from pathlib import Path
import json
import os
import re
import sys
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0] = [str(ROOT/'src/story'), str(ROOT/'src'), str(ROOT/'src/prefinal'),
                 str(ROOT/'src/rough2')]
from conform import SECTIONS, MASTER, clock

MANIFEST = json.loads((ROOT/'out/render_manifest.json').read_text())
SHOTS = {s['shot']: (s['first'], s['last']) for s in MANIFEST['exterior_shots']}
EDL = {name: (a, b) for name, a, b in SECTIONS}
ORDER = ['open', 'heel', 'star-writing', 'well', 'inner', 'tally', 'first-print',
         'atlas', 'wind', 'dive', 'grain-entry', 'sneaker', 'first-reveal', 'montage',
         'driver', 'reflection', 'oasis', 'coaster', 'slide', 'walkout', 'night']
SAMPLES = {'open': (72, 476), 'heel': (632, 672), 'driver': (694, 1142),
           'tally': (1184, 1351), 'grain-entry': (1395, 1428), 'slide': (1559, 1677),
           'first-reveal': (1707, 1872), 'sneaker': (1949, 1964), 'first-print': (1977, 2009),
           'montage': (2068, 2248), 'coaster': (2442, 2540), 'dive': (2588, 2626),
           'inner': (2905, 3114), 'wind': (3375, 3654), 'oasis': (3803, 3857),
           'atlas': (3998, 4161), 'walkout': (4320, 4350), 'star-writing': (4474, 4493),
           'night': (4735, 4745), 'well': (4752, 4772), 'reflection': (4929, 4941)}
REVISED_SURVEYS=('driver','slide','night','montage','oasis','walkout')
FINISH_SURVEY=ROOT/'work/story/finish-survey'
WORK = ROOT/'work/finish'
OUT = ROOT/'out'
GUIDE = OUT/'its-written_roughcut_v5.mp4'
BLENDER_PY = Path('/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13')
CREDITS = 'Rain Rig © Blender Foundation | cloud.blender.org, modified. Milky Way panorama by ESO/S. Brunier.'

def jungle(area=None):
    area = area or ROOT.parent/'inner'
    newer = area/'out/inner_sky2_1080.mp4'
    notes = area/'out/NOTES_INNER_SKY2.md'
    status_file=area/'STATUS.md'
    status = status_file.read_text().strip().splitlines() if status_file.is_file() else []
    if status and status[-1].startswith('INNER SKY2 DONE') and notes.is_file():
        body = notes.read_text()
        rows=re.findall(r'(?im)^\s*(?:[-*|]\s*)?(PASS|MISS|FAIL)\s+(TRAVEL|GLIDE)\s+([^\n]+)',body)
        if rows:
            finished=rows[-6:]
            passed=(len(finished)==6 and all(result.upper()=='PASS' for result,_,_ in finished)
                    and all(len({text.strip() for _,tag,text in finished if tag.upper()==category})==3
                            for category in ('TRAVEL','GLIDE')))
        else:
            passed=re.search(r'(?im)^\s*(?:[-*]\s*)?all six (?:TRAVEL and GLIDE |TRAVEL/GLIDE )?(?:checks |tests )?pass(?:ed)?\b',body)
        if passed:
            if not newer.is_file():
                raise FileNotFoundError(newer)
            return newer
    return area/'out/inner_sky_1080.mp4'

def spans(ids):
    from itertools import groupby
    for _, group in groupby(enumerate(sorted(set(ids))), lambda row:row[1]-row[0]):
        seq = [v for i,v in group]
        yield seq[0],seq[-1]

def addr(f):
    return next(n for n,(a,b) in EDL.items() if a<=f<=b)

def wind_stage(f):
    if 3390<=f<=3443: return 'wind-stance'
    if 3377<=f<=3454: return 'wind-pickup'
    if 3569<=f<=3632: return 'wind-thread'
    return 'wind'

@lru_cache(200)
def reveal_time(f):
    return min(1846.,float(clock(f))) if f<=1846 else float(f)
