"""Render the phone inserts to build/screens/phone_<shot>/{screen,16x9,9x16}/ (frames named by master frame, 30 fps).
  .venv/bin/python songs/rate-limited/screens/run_phone.py [3C,6B,7G,7H,8D] [--key]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K, phone as P
from studio import textfit

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]; KEY = '--key' in sys.argv
# shot -> (draw fn, focus line on the texture for the inserts, key time offset from the shot start, kind)
SPEC = {
    '3C': (lambda t, rec=None: P.usage(t, rec=rec), 1100, 2.27, '2D insert', 1.136),
    '6B': (lambda t, rec=None: P.sleep_story(t, rec=rec), 1560, 1.60, 'screen texture for the phone on the yoga block (2D on 3D); inserts as options', 1.136),
    '7G': (lambda t, rec=None: P.chat(t, rec=rec), 1270, 2.10, '2D insert', 1.30),
    '7H': (lambda t, rec=None: P.chat(t, sid='7H', rec=rec, reply=True), 1560, 1.60, 'screen texture for the phone over her shoulder (3D shot); inserts as options', 1.22),
    '8D': (lambda t, rec=None: P.notes(t, rec=rec), 1250, 2.00, '2D insert', 0.96),
}


def render(sid):
    fn, focus, kofs, kind, bsc = SPEC[sid]; s = K.shot(sid); frames = K.frames_for(sid); base = os.path.join(K.OUT, f'phone_{sid}')
    keyf = int(round((s['start'] + kofs) * K.FPS))
    for f in (frames if not KEY else [keyf]):
        t = f / K.FPS
        rec = textfit.Recorder((P.SW, P.SH), name=f'phone_{sid}_screen') if f == keyf else None
        scr = K.clamp_white(fn(t, rec=rec)).convert('RGB')
        a, sc16 = P.insert_16x9(scr, t, s['start'], s['end'], focus, bsc); b, sc9 = P.insert_9x16(scr, t, s['start'], s['end'], focus)
        if rec:
            rec.save(os.path.join(base, 'textfit'))
            scr.save(os.path.join(base, 'key_screen.png')); a.save(os.path.join(base, 'key_16x9.png')); b.save(os.path.join(base, 'key_9x16.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, '16x9'), f, a); K.save_seq(os.path.join(base, '9x16'), f, b)
    K.write_meta(base, shot=sid, kind=kind, screen_size=[P.SW, P.SH], screen_corner_radius_px=150, insert_16x9=[2560, 1440], insert_9x16=[1080, 1920],
                 text_scale={'16x9': round(bsc, 3), '9x16': round(1080 / P.SW * 1.04, 3)}, min_text_px_on_texture=42,
                 frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf)


if __name__ == '__main__':
    for sid in (ARGS[0].split(',') if ARGS else SPEC):
        render(sid); print('done', sid, flush=True)
