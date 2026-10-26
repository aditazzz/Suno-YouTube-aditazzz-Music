"""The film's clock: every shot, cut and event, driven by cues measured from the recording (cues.json).

`shot_at(t)` returns which scene renders at time t and the state that scene needs. Nothing here is guessed from a
tempo grid: Allow hits, taps, cuts and lyric lines all come from the vocal and band analysis.
"""
import json, math, os
from .fx import sstep, clamp, ease_io, ease_out, rgb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = json.load(open(os.path.join(ROOT, 'cues.json')))
LINES = json.load(open(os.path.join(ROOT, 'timed.json')))

# every sung Allow: (onset, stressed syllable)
ALLOWS = ([(C['intro']['allow_whisper'], C['intro']['allow_whisper'] + 0.35)] + C['ch1']['allows'] + C['ch1']['allows2']
          + C['ch2']['allows'] + C['ch2']['allows2'] + [(C['break']['allow_q'], C['break']['allow_q'] + 0.3)]
          + [(a, a + 0.45) for a in C['final']['allow_q']] + C['final']['allows'])


def pulse(t, k=2.2, which=ALLOWS):
    """Decaying flare after each Allow's stressed syllable (0..1)."""
    best = 0.0
    for a, b in which:
        x = t - b + 0.12
        if 0 <= x < 3: best = max(best, math.exp(-x * k))
        elif -0.12 < x < 0: best = max(best, (x + 0.12) / 0.12)   # rise into it
    return best


def blue(t):
    """How far the night has been drunk: 0 (candle) .. 1 (all screen blue). Steps on every Allow, eased."""
    steps = 0.0
    for i, (a, b) in enumerate(ALLOWS):
        w = 0.035 if i == 0 else (0.09 if b < 100 else 0.07)
        steps += w * ease_io((t - b + 0.1) / 1.6)
    drift = 0.25 * sstep(95.0, 98.0, t)            # verse 2: time has passed
    return clamp(steps + drift, 0, 1)


def master_state(t):
    B = blue(t)
    p = pulse(t)
    st = dict(warm=1 - 0.55 * B, warm_near=1 - 0.4 * B, warm_far=1 - 0.88 * B, night=B * 1.05,
              phone=0.08 + 0.25 * sstep(63.8, 64.6, t) + 0.6 * B, pulse=0.9 * p, phone_fill=0.3 + 0.7 * B,
              lean=0.0, fog=1.0)
    # whispered Allow: the phone wakes, then settles
    st['phone'] += 0.35 * math.exp(-max(0.0, t - 22.2) * 0.9) * (t > 21.9)
    # "then I open the door... just for tonight": the flame leans toward the glass
    st['lean'] = 0.5 * sstep(50.8, 52.2, t) * (1 - sstep(56.0, 58.0, t))
    return st


def tap_rings(t, taps, where, strength=1.0):
    return [(where[i % len(where)][0], where[i % len(where)][1], t - tt, strength) for i, tt in enumerate(taps) if 0 <= t - tt < 2.5]


# -------------------------------------------------------------- lyrics
SHOW_SECTIONS = ('V1', 'PRE1', 'V2', 'PRE2', 'BRIDGE')         # choruses carry the in-world Allow instead
LYR_FIX = {}                                                    # line text -> (start, end) overrides from cues.json


def lyric_at(t):
    """(text, opacity, italic) for the quiet subtitle line at time t."""
    for i, L in enumerate(LINES):
        if L['sec'] not in SHOW_SECTIONS: continue
        s, e = LYR_FIX.get(L['text'], (L['s'], L['e']))
        nxt = LINES[i + 1]['s'] if i + 1 < len(LINES) else e + 1
        e2 = min(e + 0.6, nxt - 0.08)
        if s - 0.25 <= t <= e2 + 0.25:
            op = sstep(s - 0.25, s + 0.05, t) * (1 - sstep(e2, e2 + 0.25, t))
            return L['text'], op, False
    return None, 0.0, False
