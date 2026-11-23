"""Render the real-device screens to build/screens_real/<name>/ (frames named by master frame, 30 fps), the same layer contract as
build/screens/<name>/ so the Remotion build swaps them in:
  phones  phone_3C / phone_6B / phone_8D: screen/ 1320x2868 texture (19.5:9, as the approved phone_real), screen_1320x2772/ for
          the existing 3D phone mesh (reflowed, not stretched), 16x9/ 2560x1440 (the phone in her room), 9x16/ 1080x1920 (the screen
          is the frame), key_*.png, layer.json, textfit/
  watch_6C   screen/ 1000x1200, 16x9/, 9x16/
  laptop_5E  screen/ 2560x1600, 16x9/ (the screen filling the frame), 9x16/ (the editor's gutter, caret and hint, x1.2)
  laptop_13E screen/ 2560x1600, overlay/ (the composer alone, alpha)
  .venv/bin/python songs/rate-limited/screens/run_devices_real.py [3C,6B,8D,6C,5E,13E] [--key] [--out <dir>]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K, phone_real as P, devices_real as D
from PIL import Image
from studio import textfit

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]; KEY = '--key' in sys.argv
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(K.SONG, 'build', 'screens_real')
ARGS = [a for a in ARGS if a != OUT]


def _cam(sid, keys):
    return keys


S = {k: K.shot(k) for k in ('3C', '6B', '8D', '6C', '5E', '13E')}
# phones: draw fn, textfit frame (settled), key frame (the old layer's), camera keys (t, scale, focus line on the screen, tilt), kind
PHONES = {
    '3C': (D.usage, 1398, 1398, [(S['3C']['start'], .66, 1030, -2.6), (S['3C']['end'], .9, 1000, -1.6)], '2D insert'),
    '6B': (D.sleep_story, 2975, 2975, [(S['6B']['start'], .66, 1500, -2.4), (S['6B']['start'] + .7, .76, 1700, -1.8), (S['6B']['end'], .9, 1450, -1.4)],
           'screen texture for the phone on the yoga block (2D on 3D: use screen_1320x2772/ on the current mesh); inserts as options'),
    '8D': (D.notes, 3960, 3960, [(S['8D']['start'], .66, 1030, -2.6), (S['8D']['end'], .9, 1000, -1.6)], '2D insert'),
}


def rec_draw(fn, t, size, name, base, **kw):
    rec = textfit.Recorder(size, name=name)
    with rec:
        im = fn(t, rec=rec, **kw)
    rec.save(os.path.join(base, 'textfit')); pr = rec.problems()
    print(name, 'textfit problems:', pr, flush=True)
    return im


def phone(sid):
    fn, recf, keyf, cam, kind = PHONES[sid]; s = S[sid]; frames = K.frames_for(sid); base = os.path.join(OUT, f'phone_{sid}')
    todo = frames if not KEY else sorted({keyf, recf})
    for f in todo:
        t = f / K.FPS
        scr = rec_draw(fn, t, (P.SW, P.SH), f'real_{sid}_screen', base) if f == recf else fn(t)
        scr = K.clamp_white(scr).convert('RGB')
        a, _ = P.insert_16x9(scr, t, cam)
        s9 = rec_draw(fn, t, (P.SW, P.H9), f'real_{sid}_screen9x16', base, H=P.H9) if f == recf else fn(t, H=P.H9)
        b, _ = P.insert_9x16(K.clamp_white(s9), t, s['start'], s['end'])
        s72 = K.clamp_white(fn(t, H=2772)).convert('RGB')
        if f == keyf:
            os.makedirs(base, exist_ok=True)
            scr.save(os.path.join(base, 'key_screen.png')); a.save(os.path.join(base, 'key_16x9.png')); b.save(os.path.join(base, 'key_9x16.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, 'screen_1320x2772'), f, s72)
            K.save_seq(os.path.join(base, '16x9'), f, a); K.save_seq(os.path.join(base, '9x16'), f, b)
    K.write_meta(base, shot=sid, kind=kind, screen_size=[P.SW, P.SH], screen_corner_radius_px=P.CORNER, screen_1320x2772=True,
                 insert_16x9=[2560, 1440], insert_9x16=[1080, 1920],
                 text_scale={'16x9_open': cam[0][1], '16x9_settled': cam[-1][1], '9x16': round(1080 / P.SW, 3)}, min_text_px_on_texture=42,
                 frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf, textfit_frame=recf, camera_16x9=cam,
                 replaces=f'build/screens/phone_{sid}')


def watch():
    sid = '6C'; s = S[sid]; frames = K.frames_for(sid); base = os.path.join(OUT, 'watch_6C'); keyf = 3024
    for f in (frames if not KEY else [keyf]):
        t = f / K.FPS
        scr = rec_draw(D.watch_screen, t, (D.WW, D.WH), 'real_watch_6C_screen', base) if f == keyf else D.watch_screen(t)
        scr = scr.convert('RGB'); a = D.watch_insert_16x9(scr, t); b = D.watch_insert_9x16(scr, t)
        if f == keyf:
            os.makedirs(base, exist_ok=True)
            scr.save(os.path.join(base, 'key_screen.png')); a.save(os.path.join(base, 'key_16x9.png')); b.save(os.path.join(base, 'key_9x16.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, '16x9'), f, a); K.save_seq(os.path.join(base, '9x16'), f, b)
    K.write_meta(base, shot=sid, kind='watch stand reminder: screen texture + 2D insert (the face fills the frame, the buzz at the shot start); the shot then goes low and wide in 3D',
                 screen_size=[D.WW, D.WH], screen_corner_radius_px=D.WCORNER, frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf,
                 note='upright to the viewer (kept from rl_screens; no CD note asks for the upside-down gag)', replaces='build/screens/watch_6C')


def editor():
    sid = '5E'; s = S[sid]; frames = K.frames_for(sid); base = os.path.join(OUT, 'laptop_5E'); keyf = 2583
    for f in (frames if not KEY else [keyf]):
        t = f / K.FPS
        scr = rec_draw(D.editor, t, (D.LW, D.LH), 'real_laptop_5E_screen', base) if f == keyf else D.editor(t)
        scr = scr.convert('RGB')
        a = scr.crop((0, 80, 2560, 1520)); b = K.clamp_white(scr.crop(D.ED9_BOX).resize((1080, 1920), Image.LANCZOS))
        if f == keyf:
            os.makedirs(base, exist_ok=True)
            scr.save(os.path.join(base, 'key_screen.png')); a.save(os.path.join(base, 'key_16x9.png')); b.save(os.path.join(base, 'key_9x16.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, '16x9'), f, a); K.save_seq(os.path.join(base, '9x16'), f, b)
    K.write_meta(base, shot=sid, kind='laptop screen texture 2560x1600 (16:10) for the 3D laptop (the cat on the lid and its tail are 3D); 16x9 = the screen filling the frame (y 80-1520); 9x16 = the editor crop x%d-%d y130-1570 x1.333 (gutter, caret, inline hint)' % (D.ED9_BOX[0], D.ED9_BOX[2]),
                 screen_size=[D.LW, D.LH], frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf,
                 blinks=D.editor_cues(), replaces='build/screens/laptop_5E')


def prompt():
    sid = '13E'; s = S[sid]; frames = K.frames_for(sid, handle=0); base = os.path.join(OUT, 'laptop_13E'); keyf = 6496
    for f in (frames if not KEY else [keyf]):
        t = f / K.FPS
        scr = rec_draw(D.prompt, t, (D.LW, D.LH), 'real_laptop_13E_screen', base) if f == keyf else D.prompt(t)
        scr = scr.convert('RGB'); ov = D.prompt(t, opaque=False)
        if f == keyf:
            os.makedirs(base, exist_ok=True)
            scr.save(os.path.join(base, 'key_screen.png')); ov.save(os.path.join(base, 'key_overlay.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'screen'), f, scr); K.save_seq(os.path.join(base, 'overlay'), f, ov)
    K.write_meta(base, shot=sid, kind="laptop screen texture 2560x1600: morning, 'Where were we?' and the composer; overlay = the composer alone (alpha) to sit over the door picture as the pull-back lands",
                 screen_size=[D.LW, D.LH], composer_box=list(D.CB), frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf,
                 typing={'starts_s': s['start'] + 2.4, 'per_char_s': .075, 'text': 'Make the font bigger.'},
                 note='the tag has no measured cues yet: typing starts 2.4 s into the tag; change t_type in devices_real.prompt and re-run if the lid timing moves',
                 replaces='build/screens/laptop_13E')


if __name__ == '__main__':
    want = ARGS[0].split(',') if ARGS else ['3C', '6B', '8D', '6C', '5E', '13E']
    for sid in want:
        if sid in PHONES:
            phone(sid)
        elif sid == '6C':
            watch()
        elif sid == '5E':
            editor()
        elif sid == '13E':
            prompt()
        print('done', sid, flush=True)
