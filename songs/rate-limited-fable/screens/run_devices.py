"""Render the watch (6C), the editor (5E) and the morning prompt (13E) to build/screens/.
  .venv/bin/python songs/rate-limited/screens/run_devices.py [6C,5E,13E] [--key]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K, devices as D
from PIL import Image
from studio import textfit

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]; KEY = '--key' in sys.argv


def want(n):
    return not ARGS or n in ARGS[0].split(',')


def watch():
    sid = '6C'; s = K.shot(sid); frames = K.frames_for(sid); base = os.path.join(K.OUT, 'watch_6C'); keyf = int(round((s['start'] + .9) * K.FPS))
    for f in (frames if not KEY else [keyf]):
        t = f / K.FPS; rec = textfit.Recorder((D.WW, D.WH), name='watch_6C_screen') if f == keyf else None
        scr = D.watch_screen(t, rec=rec).convert('RGB'); a = D.watch_insert_16x9(scr, t); b = D.watch_insert_9x16(scr, t)
        if rec:
            rec.save(os.path.join(base, 'textfit')); scr.save(os.path.join(base, 'key_screen.png')); a.save(os.path.join(base, 'key_16x9.png')); b.save(os.path.join(base, 'key_9x16.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, '16x9'), f, a); K.save_seq(os.path.join(base, '9x16'), f, b)
    K.write_meta(base, shot=sid, kind='watch face: screen texture + 2D insert (the face fills the frame, the buzz at the shot start); the shot then goes low and wide in 3D',
                 screen_size=[D.WW, D.WH], screen_corner_radius_px=170, frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf,
                 note='upright to the viewer; the BOARDS gag is that she is upside down: rotate 180 in comp only if the text may read upside down')


def editor():
    sid = '5E'; s = K.shot(sid); frames = K.frames_for(sid); base = os.path.join(K.OUT, 'laptop_5E'); keyf = int(round((s['start'] + .1) * K.FPS))
    for f in (frames if not KEY else [keyf]):
        t = f / K.FPS; rec = textfit.Recorder((D.LW, D.LH), name='laptop_5E_screen') if f == keyf else None
        scr = D.editor(t, rec=rec).convert('RGB')
        a = scr.crop((0, 80, 2560, 1520)); b = K.clamp_white(scr.crop((1280 - 405, 80, 1280 + 405, 1520)).resize((1080, 1920), Image.LANCZOS))
        if rec:
            rec.save(os.path.join(base, 'textfit')); scr.save(os.path.join(base, 'key_screen.png')); a.save(os.path.join(base, 'key_16x9.png')); b.save(os.path.join(base, 'key_9x16.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, '16x9'), f, a); K.save_seq(os.path.join(base, '9x16'), f, b)
    K.write_meta(base, shot=sid, kind='laptop screen texture 2560x1600 (16:10) for the 3D laptop (the cat on the lid and its tail are 3D); 16x9 = the screen filling the frame; 9x16 = the centre band x1.333',
                 screen_size=[D.LW, D.LH], frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf,
                 blinks=[K.onset(sid, f'cursor blink {i + 1}', 0) for i in range(4)])


def prompt():
    sid = '13E'; s = K.shot(sid); frames = K.frames_for(sid, handle=0); base = os.path.join(K.OUT, 'laptop_13E'); keyf = int(round((s['start'] + 4.6) * K.FPS))
    for f in (frames if not KEY else [keyf]):
        t = f / K.FPS; rec = textfit.Recorder((D.LW, D.LH), name='laptop_13E_screen') if f == keyf else None
        scr = D.prompt(t, rec=rec).convert('RGB'); ov = D.prompt(t, opaque=False)
        if rec:
            rec.save(os.path.join(base, 'textfit')); scr.save(os.path.join(base, 'key_screen.png')); ov.save(os.path.join(base, 'key_overlay.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, 'overlay'), f, ov)
    K.write_meta(base, shot=sid, kind="laptop screen texture 2560x1600: morning, 'Where were we?' and the composer; overlay = the composer alone (alpha) to sit over the door picture as the pull-back lands",
                 screen_size=[D.LW, D.LH], frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf,
                 typing={'starts_s': s['start'] + 2.4, 'per_char_s': .075, 'text': 'Make the font bigger.'},
                 note='the tag has no measured cues yet: typing starts 2.4 s into the tag and ends at 4.0 s; change t_type in devices.prompt and re-run if the lid timing moves')


if __name__ == '__main__':
    if want('6C'): watch(); print('done 6C', flush=True)
    if want('5E'): editor(); print('done 5E', flush=True)
    if want('13E'): prompt(); print('done 13E', flush=True)
