#!/usr/bin/env python3
"""Song data -> src/data/*.json for the Remotion film. Re-run whenever the shot list, beats or plates change.

Shots: build/shots/shots.json (rl_shots, the beat-checked list) when it exists, else build/shots/boards_parsed.json
(BOARDS.md parsed: section times, lyric, set, words on screen, "Grows from").
Plates: each shot's still. A shot listed in plates_override.json gets that plate; else its "Grows from" frame; else a
guess from its set. Approved frames win over in-rework ones (b2b, routine, party come from Approved/sets).
Beats: bts_reel/work/beats_midi.json (MIDI time) + 0.23 s = audio time; a downbeat every 4 beats.
Words: build/words.json ([t, word] pairs).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SONG = os.path.dirname(PROJ)
OUT = os.path.join(PROJ, 'src', 'data')
FPS = 30
GRID_LAG = 0.23

# "Grows from" frame file -> plate key (public/plates/<key>.jpg)
GROWS = {
    '01_door': 'door', '02_close': 'close', '03_meter': 'meter', '04_dawn': 'dawn',
    '05_b2b': 'room_b2b', '06_date': 'date', '07_date_close': 'date_close',
    '08_routine': 'room_routine', '09_routine_outlook': 'room_party',
}
# set keyword -> plate key, for shots with no frame yet (first match wins)
SETS = [
    ('her real room', 'room_routine'), ('two rooms', 'room_b2b'), ('her room', 'room_routine'),
    ('door, her side', 'door'), ('door +', 'door'), ('lobby through the glass', 'door'), ('lobby', 'close'),
    ('street', 'dawn'), ('insert: her phone', None), ('insert: her laptop', 'room_routine'),
    ('insert: his logbook', 'meter'), ('insert', 'close'),
]
# 9:16 crop centre (0..1 of the 16:9 frame width) per plate; per-shot cx916 in plates_override.json wins
CX916 = {'door': 0.5, 'close': 0.5, 'meter': 0.5, 'dawn': 0.5, 'room_b2b': 0.43, 'date': 0.3, 'date_close': 0.5,
         'room_routine': 0.5, 'room_party': 0.5}


def load(p):
    with open(p) as f:
        return json.load(f)


def section_no(s):
    m = re.match(r'\s*(\d+)', str(s))
    return int(m.group(1)) if m else 0


def shots_from_boards():
    out = []
    for s in load(os.path.join(SONG, 'build/shots/boards_parsed.json')):
        f = s['fields']
        out.append(dict(id=s['id'], s=float(s['start_b']), e=float(s['end_b']), sec=section_no(s['section']),
                        section=s['section'], clock=s.get('clock', ''), lyric=f.get('Lyric', ''), set=f.get('Set', ''),
                        words=f.get('Words on screen', ''), grows=f.get('Grows from', '')))
    return out


def shots_from_rl_shots(p):
    """rl_shots' build/shots/shots.json: {meta, shots: [{id, start, end, frames: [a, b), clock, lyric, text, set_camera,
    beats, cues: [{cue, word, t, frame, kind, confidence}], ...}]}. Grows-from comes from BOARDS (by id)."""
    d = load(p)
    rows = d['shots'] if isinstance(d, dict) else d
    by_id = {s['id']: s for s in shots_from_boards()}
    out = []
    for r in rows:
        sid = str(r['id'])
        b = by_id.get(sid, {})
        sh = {**b, 'id': sid, 's': float(r.get('start', b.get('s', 0))), 'e': float(r.get('end', b.get('e', 0)))}
        for k_out, k_in in (('clock', 'clock'), ('lyric', 'lyric'), ('words', 'text'), ('set', 'set_camera')):
            if r.get(k_in):
                sh[k_out] = r[k_in]
        if isinstance(r.get('frames'), list) and len(r['frames']) == 2:
            sh['frames'] = [int(r['frames'][0]), int(r['frames'][1])]
        if 'section' not in sh and r.get('section'):  # rl5_d: cut 5's new ids (4T, 7E1, 9E1, 9E2) have no BOARDS row
            sh['section'] = r['section']; sh['sec'] = section_no(r['section'])
        for k in ('outfit', 'c4e'):  # rl5_d: cut 5 extras
            if r.get(k):
                sh[k] = r[k]
        sh['cues'] = [{k: c.get(k) for k in ('cue', 'word', 't', 'frame', 'kind', 'confidence')} for c in r.get('cues', [])]
        sh['grid'] = r.get('beats', [])
        out.append(sh)
    return out


def plate_for(sh, over):
    o = over.get(sh['id'], {})
    if 'plate' in o:
        return o['plate']
    m = re.search(r'frames/(\d\d_[a-z0-9_]+?)(?:_r\d+)?\.jpg', sh.get('grows', ''))
    if m and m.group(1) in GROWS:
        return GROWS[m.group(1)]
    st = sh.get('set', '').lower()
    for kw, key in SETS:
        if kw in st:
            return key
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    rl = os.path.join(SONG, 'build/shots/shots.json')
    src = 'rl_shots' if os.path.exists(rl) else 'boards'
    shots = shots_from_rl_shots(rl) if src == 'rl_shots' else shots_from_boards()
    shots.sort(key=lambda x: x['s'])
    op = os.path.join(PROJ, 'plates_override.json')
    over = load(op) if os.path.exists(op) else {}
    plates = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(PROJ, 'public/plates'))}
    gaps = []
    for i, sh in enumerate(shots):
        fr = sh.pop('frames', None)  # rl_shots' own frame numbers win (its rule: round(t * fps), [a, b))
        sh['from'] = fr[0] if fr else round(sh['s'] * FPS)
        sh['to'] = fr[1] if fr else round(sh['e'] * FPS)
        sh['dur'] = sh['to'] - sh['from']
        p = plate_for(sh, over)
        sh['plate'] = p if p in plates else None
        sh['new'] = 'no frame' in sh.get('grows', '') or not sh.get('grows')
        sh['cx916'] = over.get(sh['id'], {}).get('cx916', CX916.get(sh['plate'] or '', 0.5))
        sh['move'] = over.get(sh['id'], {}).get('move', ['push', 'driftR', 'push', 'driftL', 'rise'][i % 5])
        sh.pop('grows', None)
        if i and shots[i - 1]['to'] != sh['from']:
            gaps.append((shots[i - 1]['id'], sh['id'], shots[i - 1]['to'], sh['from']))
    beats = [round(b + GRID_LAG, 4) for b in load(os.path.join(SONG, 'bts_reel/work/beats_midi.json'))]
    words = load(os.path.join(SONG, 'build/words.json'))
    end = max(s['e'] for s in shots)
    json.dump({'source': src, 'fps': FPS, 'end': end, 'frames': max(x['to'] for x in shots), 'shots': shots},
              open(os.path.join(OUT, 'shots.json'), 'w'), indent=1)
    json.dump({'beats': beats, 'downbeats': beats[::4]}, open(os.path.join(OUT, 'beats.json'), 'w'))
    json.dump([[round(t, 3), w] for t, w in words], open(os.path.join(OUT, 'words.json'), 'w'))
    noplate = [s['id'] for s in shots if not s['plate']]
    print(f'shots: {len(shots)} from {src}, {round(end * FPS)} frames ({end:.2f} s); beats {len(beats)}; words {len(words)}')
    print(f'no plate (code-drawn insert placeholder): {noplate}')
    if gaps:
        print('GAPS/OVERLAPS between shots:', gaps)
        sys.exit(1)


if __name__ == '__main__':
    main()
