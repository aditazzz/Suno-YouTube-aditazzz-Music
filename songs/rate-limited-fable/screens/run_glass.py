"""Render the glass layers to build/screens/glass_*/ (PNG sequences named by master frame at 30 fps).
  .venv/bin/python songs/rate-limited/screens/run_glass.py [only,...] [--key]   (--key: key frames only, for checks)"""
import os, sys, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K, glass as G
from studio import textfit

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]; KEY = '--key' in sys.argv


def want(n):
    return not ARGS or n in ARGS[0].split(',')


def msg_spec(sid):
    s = K.shot(sid); b = K.beats_in(sid)
    if sid == '2G':
        tm = s['start'] + .10
        # 'Don't' at 38.22 and 'read' at 39.06, measured on build/vocals16.wav (no cue in shots.json): Delivered on 'Don't', Read on 'read'
        return dict(msgs=['One last thing.'], times=[tm], receipt_t=K.onset(sid, "don't", 38.20), read_t=K.onset(sid, 'read', 39.04), read_time=' 2:06 AM')
    if sid == '5H':
        ts = [K.onset(sid, f'message {i + 1}', b[i + 1]) for i in range(3)]          # the roll hits on beats 2, 3, 4 (measured)
        tr = K.onset(sid, 'receipt', 95.139)
        return dict(msgs=['Quick question.', "It's small.", "It's a font."], times=ts, receipt_t=ts[2] + .16, read_t=tr - .04, read_time=' 3:59 AM', read_rise=0, read_fade=.07)
    if sid == '12G':
        return dict(msgs=[''], times=[s['start'] + .08], receipt_t=None, read_t=K.onset(sid, 'read', 197.60), read_time=None, delivered=False, draft=True)   # 'read' ~197.62 on the vocal stem


def render_messages(sid):
    sp = msg_spec(sid); frames = K.frames_for(sid)
    for fmt in ('16x9', '9x16'):
        out = os.path.join(K.OUT, f'glass_{sid}', fmt)
        keyf = int(round((K.shot(sid)['end'] - 0.05) * K.FPS))
        for f in (frames if not KEY else [keyf]):
            rec = textfit.Recorder(G.LAYOUT[fmt]['size'], name=f'glass_{sid}_{fmt}') if f == keyf else None
            im = G.messages_frame(f / K.FPS, fmt, rec=rec, **sp)
            if rec:
                rec.save(os.path.join(K.OUT, f'glass_{sid}', 'textfit')); im.save(os.path.join(K.OUT, f'glass_{sid}', f'key_{fmt}.png'))
            if not KEY:
                K.save_seq(out, f, im)
        K.write_meta(os.path.join(K.OUT, f'glass_{sid}'), shot=sid, kind='screen-space overlay (alpha) for the close shot through the glass',
                     formats={'16x9': '2560x1440, approved layout (comp_close.py x4/3)', '9x16': '1080x1920, bubbles upper left inside the safe zone'},
                     frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=K.shot(sid)['src'],
                     events={k: v for k, v in sp.items() if k.endswith('_t') or k == 'times'}, key_frame=keyf)


def render_bezel():
    out = os.path.join(K.OUT, 'glass_bezel'); os.makedirs(out, exist_ok=True)
    for fmt in ('16x9', '9x16'):
        G.bezel(fmt).save(os.path.join(out, f'bezel_{fmt}.png'))
    K.write_meta(out, kind='static overlay: the screen edge, sheen and camera dot of the approved close frame; over the close shots 2G 5H 12G')


def render_typing():
    sid = '8E'; frames = K.frames_for(sid); out = os.path.join(K.OUT, 'glass_8E', 'glass_uv')
    keyf = int(round((K.shot(sid)['start'] + 1.9) * K.FPS))
    for f in (frames if not KEY else [keyf]):
        rec = textfit.Recorder((G.GW, G.GH), name='glass_8E_uv') if f == keyf else None
        im = G.typing_glass(f / K.FPS, rec=rec)
        if rec:
            rec.save(os.path.join(K.OUT, 'glass_8E', 'textfit')); im.save(os.path.join(K.OUT, 'glass_8E', 'key_uv.png'))
        if not KEY:
            K.save_seq(out, f, im)
    K.write_meta(os.path.join(K.OUT, 'glass_8E'), shot=sid, kind='glass texture (alpha), UV space of the door glass seen from her side',
                 size=[G.GW, G.GH], glass_m=[1.36, 1.62], frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=K.shot(sid)['src'])


def render_sleep():
    sid = '11C'; frames = K.frames_for(sid); out = os.path.join(K.OUT, 'glass_11C_sleep')
    curve = {f: round(G.sleep_curve(f / K.FPS), 4) for f in frames}
    if not KEY:
        for f in frames:
            K.save_seq(os.path.join(out, 'glass_uv'), f, G.sleep_glass(f / K.FPS))
    K.write_meta(out, shot=sid, kind='glass darkness: black matte with alpha = darkness (UV space); or key the glass emission/darkness from curve',
                 size=[G.GW, G.GH], fps=K.FPS, curve=curve, timing_src=K.shot(sid)['src'])


def render_ripple():
    sid = '2C'; frames = K.frames_for(sid); out = os.path.join(K.OUT, 'glass_2C_ripple')
    kt = G.knock_times(sid); os.makedirs(out, exist_ok=True)
    for f in (frames if not KEY else [int(round((kt[0] + .25) * K.FPS))]):
        hm, hl = G.ripple_maps(f / K.FPS)
        if KEY:
            hl.save(os.path.join(out, 'key_highlight.png')); continue
        os.makedirs(os.path.join(out, 'height_uv'), exist_ok=True); hm.save(os.path.join(out, 'height_uv', f'f_{f:05d}.png'))
        K.save_seq(os.path.join(out, 'highlight_uv'), f, hl)
    K.write_meta(out, shot=sid, kind='three knocks: height map (16-bit, 0.5 = flat; drive a Bump node, strength ~0.3) + soft ring highlight (alpha), glass UV from her side; mirror u for the lobby-side camera',
                 size=[G.GW, G.GH], knocks_s=kt, knock_uv=G.KNOCK_UV, fps=K.FPS, timing_src=K.shot(sid)['src'])


if __name__ == '__main__':
    os.makedirs(K.OUT, exist_ok=True)
    for sid in ('2G', '5H', '12G'):
        if want(sid): render_messages(sid); print('done', sid, flush=True)
    if want('bezel'): render_bezel()
    if want('8E'): render_typing(); print('done 8E', flush=True)
    if want('11C'): render_sleep(); print('done 11C', flush=True)
    if want('2C'): render_ripple(); print('done 2C', flush=True)
