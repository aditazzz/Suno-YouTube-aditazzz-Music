"""Render the TV textures (2250 x 1290, the size blroom maps on RT_scr) to build/screens/tv_<shot>/.
  .venv/bin/python songs/rate-limited/screens/run_tv.py [9A,9C,9D,9G] [--key]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K, tv as T
from studio import textfit

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]; KEY = '--key' in sys.argv
FN = {'9A': T.tv_9A, '9C': T.tv_9C, '9D': T.tv_9D}
KEYOFS = {'9A': 2.0, '9C': 1.6, '9D': 1.0}


def render(sid):
    s = K.shot(sid); frames = K.frames_for(sid); base = os.path.join(K.OUT, f'tv_{sid}'); keyf = int(round((s['start'] + KEYOFS[sid]) * K.FPS))
    for f in (frames if not KEY else [keyf]):
        im = FN[sid](f / K.FPS).convert('RGB')
        if f == keyf:
            os.makedirs(base, exist_ok=True); im.save(os.path.join(base, 'key.png'))
        if not KEY:
            K.save_seq(os.path.join(base, 'tex'), f, im)
    K.write_meta(base, shot=sid, kind='TV screen texture for blroom RT_scr (emission), same size and layout as the approved tv_news*.png', size=[T.TW, T.TH],
                 frames=[frames[0], frames[-1]], fps=K.FPS, timing_src=s['src'], key_frame=keyf,
                 headlines={'9A': 'Jensen Huang summoned to testify before Congress after resigning as Nvidia CEO | Source: CNN · Nov 11, 2026',
                            '9C/9D': 'Microsoft Outlook outage stretches on for hours | ABC News, Nov 13, 2026 (tv_news2.png still old: see tv.py)'})


def frozen():
    base = os.path.join(K.OUT, 'tv_9G'); os.makedirs(base, exist_ok=True)
    T.tv_party(0.0, frozen=True).convert('RGB').save(os.path.join(base, 'frozen.png'))
    K.write_meta(base, shot='9G', kind='one held frame: the party frozen (no bounce, no falling confetti); the guests who climb back in are 3D', size=[T.TW, T.TH])


def record_textfit():
    """the TV's own words (LIVE, the time, both headline cards) measured on the key frames"""
    from PIL import Image, ImageDraw
    rec = textfit.Recorder((T.TW, T.TH), name='tv_live_badge')
    d = ImageDraw.Draw(Image.new('RGBA', (T.TW, T.TH))); ft = K.font('bold', int(40 * T.S))
    rec.add('LIVE', d.textbbox((133 * T.S, 83 * T.S), 'LIVE', font=ft, anchor='mm'), (60 * T.S, 50 * T.S, 206 * T.S, 116 * T.S), 'badge')
    rec.add('4:41 AM', d.textbbox((232 * T.S, 83 * T.S), '4:41 AM', font=ft, anchor='lm'), (40 * T.S, 34 * T.S, 440 * T.S, 132 * T.S), 'scrim')
    rec.save(os.path.join(K.OUT, 'tv_9D', 'textfit'))


if __name__ == '__main__':
    for sid in (ARGS[0].split(',') if ARGS else ['9A', '9C', '9D', '9G']):
        if sid == '9G': frozen()
        else: render(sid)
        print('done', sid, flush=True)
    record_textfit()
