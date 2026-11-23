"""Render the real-phone 7G / 7H to build/screens_real/phone_<shot>/ (frames named by master frame, 30 fps). Same layer contract as
build/screens/phone_<shot>/ (16x9/ 2560x1440, 9x16/ 1080x1920, screen/ texture, layer.json, textfit/), so the Remotion build can swap it in.
  .venv/bin/python songs/rate-limited/screens/run_phone_real.py [7G,7H] [--key] [--out <dir>]
screen/ is the 19.5:9 texture (1320 x 2868). 7H also writes screen_1320x2772/ for the existing 3D phone mesh (same layout, reflowed
to that height, not stretched)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K, phone_real as P
from studio import textfit

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]; KEY = '--key' in sys.argv
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(K.SONG, 'build', 'screens_real')
if '--out' in sys.argv:
    ARGS = [a for a in ARGS if a != OUT]
S7G, S7H = K.shot('7G'), K.shot('7H')
# camera: (t, scale, focus line on the screen, tilt)
CAM = {
    '7G': [(S7G['start'], .47, P.SH / 2, -3.0), (S7G['start'] + .36, .49, P.SH / 2, -2.8),
           (K.beats_in('7G')[2], 1.02, 1570, -1.2), (S7G['end'], 1.06, 1585, -.8)],
    '7H': [(S7H['start'] - .2, 1.06, 1585, -.8), (S7H['end'], 1.10, 1610, -.3)],
}
SPEC = {   # draw fn, textfit frame (everything settled), key frame (old layer's), kind
    '7G': (P.chat_7g, 3625, 3616, '2D insert'),
    '7H': (P.chat_7h, 3670, 3670, 'screen texture for the phone over her shoulder (3D shot); inserts as options'),
}


def render(sid):
    fn, recf, keyf, kind = SPEC[sid]; s = K.shot(sid); frames = K.frames_for(sid); base = os.path.join(OUT, f'phone_{sid}')
    todo = frames if not KEY else sorted({keyf, recf})
    for f in todo:
        t = f / K.FPS
        rec = textfit.Recorder((P.SW, P.SH), name=f'phone_real_{sid}_screen') if f == recf else None
        if rec:
            with rec:
                scr = fn(t, rec=rec)
        else:
            scr = fn(t)
        scr = K.clamp_white(scr).convert('RGB')
        a, sc16 = P.insert_16x9(scr, t, CAM[sid])
        rec9 = textfit.Recorder((P.SW, P.H9), name=f'phone_real_{sid}_screen9x16') if f == recf else None
        if rec9:
            with rec9:
                s9 = fn(t, H=P.H9, rec=rec9)
        else:
            s9 = fn(t, H=P.H9)
        b, sc9 = P.insert_9x16(K.clamp_white(s9), t, s['start'], s['end'])
        if rec:
            rec.save(os.path.join(base, 'textfit')); rec9.save(os.path.join(base, 'textfit'))
            print(sid, 'textfit problems:', rec.problems(), rec9.problems(), flush=True)
        if f == keyf:
            os.makedirs(base, exist_ok=True)
            scr.save(os.path.join(base, 'key_screen.png')); a.save(os.path.join(base, 'key_16x9.png')); b.save(os.path.join(base, 'key_9x16.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, '16x9'), f, a); K.save_seq(os.path.join(base, '9x16'), f, b)
            if sid == '7H':
                K.save_seq(os.path.join(base, 'screen_1320x2772'), f, K.clamp_white(fn(t, H=2772)).convert('RGB'))
    K.write_meta(base, shot=sid, kind=kind, screen_size=[P.SW, P.SH], screen_corner_radius_px=P.CORNER,
                 screen_1320x2772=(sid == '7H'), insert_16x9=[2560, 1440], insert_9x16=[1080, 1920],
                 text_scale={'16x9_settled': round(CAM[sid][-1][1], 3), '16x9_open': round(CAM[sid][0][1], 3), '9x16': round(1080 / P.SW, 3)},
                 min_text_px_on_texture=42, frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf, textfit_frame=recf,
                 camera_16x9=CAM[sid], replaces=f'build/screens/phone_{sid}')


if __name__ == '__main__':
    for sid in (ARGS[0].split(',') if ARGS else SPEC):
        render(sid); print('done', sid, flush=True)
