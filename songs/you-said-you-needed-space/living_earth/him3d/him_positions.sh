#!/bin/bash
# his placement per frame for every run, both formats (no render): tracks from the engine -> meta (him_slots.py meta=1) -> build/him_wire/positions/<run>.json
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; SONG="$(cd "$HERE/../.." && pwd)"; ROOT="$(cd "$SONG/../.." && pwd)"; W="$SONG/build/him_wire"
"$HERE/him_export.sh" "$W/tracks" > "$W/tmp/export.log"
for run in ${RUNS:-co_count c1_chase c1_heat br fc_hold fc_cool fc_end p2_estate}; do for fmt in 169 916; do
  /Applications/Blender.app/Contents/MacOS/Blender -b "$HERE/him.blend" --python "$HERE/him_slots.py" -- $run $fmt "$W/meta/${run}_$fmt" meta=1 2>&1 | grep -E "Error|Traceback|File \"" || true
done; done
"$ROOT/.venv/bin/python" - "$W" <<'PY'
import json, sys, os, time
W = sys.argv[1]
for run in os.environ.get('RUNS', 'co_count c1_chase c1_heat br fc_hold fc_cool fc_end p2_estate').split():
    tr = json.load(open(f'{W}/tracks/{run}.json')); doc = {'run': run, 'slots': tr['slots'], 'slotFrames': tr['slotFrames'], 'f0': tr['f0'], 'f1': tr['f1'], 'written': time.strftime('%a %b %d %H:%M'),
        'note': 'Where the 3D him is, per film frame (30 fps). c: his centre in engine screen units (y up, frame height 2); span: his wing span (the rocket: its length) in the same units; px/span_px in the master size of the format; alpha 0..1 = how much of the 3D him is on screen (0 = the engine spark is still drawn).'}
    for fmt in ('169', '916'):
        m = json.load(open(f'{W}/meta/{run}_{fmt}/meta.json')); Wd, H = m['res']; A = Wd / H
        doc[fmt] = {'res': m['res'], 'frames': [{'f': x['f'], 'c': [round((x['px'][0] / Wd * 2 - 1) * A, 4), round(1 - x['px'][1] / H * 2, 4)], 'span': round(x['span'] / (H / 2), 4), 'px': x['px'], 'span_px': x['span'], 'alpha': x['alpha']} for x in m['frames']]}
    json.dump(doc, open(f'{W}/positions/{run}.json', 'w')); fr = doc['169']['frames']; on = [x for x in fr if x['alpha'] > 0.5]
    print(run, 'frames', tr['f0'], tr['f1'], '| 16:9 on', (on[0]['f'], on[-1]['f']) if on else None, '| first c/span', fr[0]['c'], fr[0]['span'], '| last', fr[-1]['c'], fr[-1]['span'])
PY
