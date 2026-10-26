#!/bin/bash
# The vertical versions from the 9:16 masters, upscaled to 1080x1920: the full song, the under-3-minute cut for
# Instagram, and one Short per card (cuts.json). Output: build/cuts/.
#   AUDIO=path/to/song.wav ./cuts.sh
set -e
cd "$(dirname "$0")"
export AUDIO=${AUDIO:?set AUDIO to the song file}
O=build/cuts; mkdir -p "$O"; VF=build/frames_9x16
python3 cut.py $VF "$O/full 9x16.mp4" 1080 1920 "0-244.8" --bv 6 --fadeout 0.3 --preset medium
S=$(python3 -c "import json; print(json.load(open('cuts.json'))['under3']['segs'])")
X=$(python3 -c "import json; print(json.load(open('cuts.json'))['under3']['xf'])")
python3 cut.py $VF "$O/under 3 min 9x16.mp4" 1080 1920 "$S" --xf "$X" --bv 6 --fadeout 0.3 --preset medium
python3 - <<'PY'
import json, subprocess
for i, s in enumerate(json.load(open('cuts.json'))['shorts']):
    subprocess.run(['python3', 'cut.py', 'build/frames_9x16', f"build/cuts/Short {i + 1} ({s['key']}, {s['dur']}s).mp4", '1080', '1920', s['segs'],
                    '--bv', '8', '--preset', 'medium', '--fadein', str(s['fadein']), '--fadeout', str(s['fadeout']), '--hold', str(s['hold'])], check=True)
PY
