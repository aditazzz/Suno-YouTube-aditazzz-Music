"""Generic renderer. usage: python3 render.py <projdir> still|vstill|range|vrange args..."""
import sys, os, subprocess
PROJ = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # repo layout (the chat used an absolute path)
sys.path.insert(0, PROJ)
import numpy as np
import skia
from kit import *
import importlib.util
_spec = importlib.util.spec_from_file_location('scenes', os.path.join(PROJ, 'scenes.py'))
S = importlib.util.module_from_spec(_spec); sys.modules['scenes'] = S; _spec.loader.exec_module(S)

_an = np.load(os.path.join(PROJ, 'analysis.npz'))
_t, _low, _rms = _an['t'], _an['low'], _an['rms']
on = np.maximum(0, np.diff(np.log1p(_low), prepend=0))
on = np.maximum(on - np.convolve(on, np.ones(43) / 43, 'same'), 0)
on = on / (np.percentile(on, 99) + 1e-9)
NF = int(S.END * FPS) + 1
ft = np.arange(NF) / FPS
idx = np.clip(np.searchsorted(_t, ft), 0, len(_t) - 1)
kick_raw = np.array([on[max(0, i - 1):i + 2].max() for i in idx])
kick = np.zeros(NF)
for i in range(NF):
    kick[i] = max(min(kick_raw[i], 1.0), (kick[i - 1] * 0.8) if i else 0)
energy = np.interp(ft, _t, np.convolve(_rms, np.ones(20) / 20, 'same'))
energy = energy / energy.max()

BGIMG = make_bg()
VIG = make_vignette()
GRAIN = make_grain(12)


def features(fi):
    fi = min(fi, NF - 1)
    return {'kick': float(kick[fi]), 'energy': float(energy[fi])}


def draw_scenes(c, t, A):
    dx = noise1(t * 0.15, 1) * 10
    dy = noise1(t * 0.13, 2) * 7
    rot = noise1(t * 0.1, 3) * 0.25
    z = 1 + 0.006 * A['kick']
    c.save()
    c.translate(W / 2 + dx, H / 2 + dy); c.rotate(rot); c.scale(z, z); c.translate(-W / 2, -H / 2)
    for name, a, b in S.SECTIONS:
        if a - 0.7 <= t <= b + 0.7:
            S.SECTION_FN[name](c, t, A)
    c.restore()


def render_frame(t, surf=None):
    fi = int(round(t * FPS))
    A = features(fi)
    surf = surf or skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(BG)
    c.drawImage(BGIMG, 0, 0)
    draw_scenes(c, t, A)
    S.LYR.draw(c, t)
    S.hud(c, t, A, False)
    g = GRAIN[fi % len(GRAIN)]
    c.drawImageRect(g, skia.Rect(0, 0, W, H), skia.SamplingOptions(),
                    skia.Paint(BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10))
    c.drawImage(VIG, 0, 0)
    return surf


VW, VH = 1080, 1920
V_SCALE = 0.75
V_Y0 = 520
V_X0 = (VW - W * V_SCALE) / 2
VBG = VVIG = None
_scene_surf = None


def _vimgs():
    s1 = skia.Surface(VW, VH); c = s1.getCanvas()
    c.drawRect(skia.Rect(0, 0, VW, VH), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (VW / 2, V_Y0 + 400), VW * 1.0,
        [skia.Color4f(19 / 255, 19 / 255, 21 / 255, 1), skia.Color4f(10 / 255, 10 / 255, 11 / 255, 1)], [0.0, 1.0])))
    s2 = skia.Surface(VW, VH); c = s2.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
    c.drawRect(skia.Rect(0, 0, VW, VH), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (VW / 2, VH / 2), VH * 0.62,
        [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0.7)], [0.0, 0.5, 1.0])))
    return s1.makeImageSnapshot(), s2.makeImageSnapshot()


def wrap_line(s, tf, size, maxw):
    if text_width(s, tf, size) <= maxw:
        return [s]
    words = s.split(' ')
    best = None
    for i in range(1, len(words)):
        a, b = ' '.join(words[:i]), ' '.join(words[i:])
        m = max(text_width(a, tf, size), text_width(b, tf, size))
        if best is None or m < best[0]:
            best = (m, [a, b])
    return best[1]


def render_frame_v(t, surf=None):
    global VBG, VVIG, _scene_surf
    if VBG is None:
        VBG, VVIG = _vimgs()
        _scene_surf = skia.Surface(W, H)
    fi = int(round(t * FPS))
    A = features(fi)
    surf = surf or skia.Surface(VW, VH)
    c = surf.getCanvas()
    c.clear(BG)
    c.drawImage(VBG, 0, 0)
    sc = _scene_surf.getCanvas()
    sc.clear(skia.Color4f(0, 0, 0, 0))
    draw_scenes(sc, t, A)
    fade = skia.GradientShader.MakeLinear([(0, 0), (0, H)],
        [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 1), skia.Color4f(0, 0, 0, 1), skia.Color4f(0, 0, 0, 0)],
        [0.0, 0.1, 0.9, 1.0])
    sc.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=fade, BlendMode=skia.BlendMode.kDstIn))
    c.drawImageRect(_scene_surf.makeImageSnapshot(), skia.Rect(V_X0, V_Y0, V_X0 + W * V_SCALE, V_Y0 + H * V_SCALE),
                    skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    for (t0, t1, s_, st) in S.LYR.lines:
        if st != 'lyric' or t < t0 - 0.1 or t > t1 + 0.5:
            continue
        lines = wrap_line(s_, TF_SERIF_I, 58, 900)
        for k, ln in enumerate(lines):
            y = 1430 + k * 70 - (len(lines) - 1) * 35
            reveal_text(c, ln, VW / 2, y, TF_SERIF_I, 58, t, t0 + k * 0.25, t1, IVORY, 0.96, stagger=0.018, dur=0.4,
                        glow=0.35, out_dur=0.3)
    ta = window(t, 0.6, S.END + 1, 1.0, 0.5) * (1 - ease_io(ramp(t, S.END - 3.6, S.END - 2.8)))
    draw_text(c, 'aditazzz', VW / 2, 330, TF_MONO, 24, IVORY, ta * 0.8, tracking=9)
    draw_text(c, S.TITLE, VW / 2, 368, TF_MONO, 15, SILVER, ta * 0.55, tracking=6)
    S.hud(c, t, A, True)
    g = GRAIN[fi % len(GRAIN)]
    c.drawImageRect(g, skia.Rect(0, 0, VW, VH), skia.SamplingOptions(),
                    skia.Paint(BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10))
    c.drawImage(VVIG, 0, 0)
    return surf


def render_both(f0, f1, out_h, out_v):
    """render the scene once per frame, compose 16:9 and 9:16 from it"""
    global VBG, VVIG, _scene_surf
    if VBG is None:
        VBG, VVIG = _vimgs()
        _scene_surf = skia.Surface(W, H)
    def enc(w, h, out, crf):
        return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}',
                                 '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', crf,
                                 '-pix_fmt', 'yuv420p', '-tune', 'grain', out], stdin=subprocess.PIPE)
    ph, pv = enc(W, H, out_h, '16'), enc(VW, VH, out_v, '17')
    sh, sv = skia.Surface(W, H), skia.Surface(VW, VH)
    ih = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    iv = skia.ImageInfo.Make(VW, VH, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    bh = np.empty((H, W, 4), np.uint8); bv = np.empty((VH, VW, 4), np.uint8)
    fade = skia.GradientShader.MakeLinear([(0, 0), (0, H)],
        [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 1), skia.Color4f(0, 0, 0, 1), skia.Color4f(0, 0, 0, 0)],
        [0.0, 0.1, 0.9, 1.0])
    for fi in range(f0, f1):
        t = fi / FPS
        A = features(fi)
        sc = _scene_surf.getCanvas(); sc.clear(skia.Color4f(0, 0, 0, 0))
        draw_scenes(sc, t, A)
        img = _scene_surf.makeImageSnapshot()
        g = GRAIN[fi % len(GRAIN)]
        # 16:9
        c = sh.getCanvas(); c.clear(BG); c.drawImage(BGIMG, 0, 0); c.drawImage(img, 0, 0)
        S.LYR.draw(c, t); S.hud(c, t, A, False)
        c.drawImageRect(g, skia.Rect(0, 0, W, H), skia.SamplingOptions(), skia.Paint(BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10))
        c.drawImage(VIG, 0, 0)
        sh.readPixels(ih, bh, W * 4, 0, 0); ph.stdin.write(bh.tobytes())
        # 9:16
        sc.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=fade, BlendMode=skia.BlendMode.kDstIn))
        imgv = _scene_surf.makeImageSnapshot()
        c = sv.getCanvas(); c.clear(BG); c.drawImage(VBG, 0, 0)
        c.drawImageRect(imgv, skia.Rect(V_X0, V_Y0, V_X0 + W * V_SCALE, V_Y0 + H * V_SCALE),
                        skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
        for (t0, t1, s_, st) in S.LYR.lines:
            if st != 'lyric' or t < t0 - 0.1 or t > t1 + 0.5:
                continue
            lines = wrap_line(s_, TF_SERIF_I, 58, 900)
            for k, ln in enumerate(lines):
                y = 1430 + k * 70 - (len(lines) - 1) * 35
                reveal_text(c, ln, VW / 2, y, TF_SERIF_I, 58, t, t0 + k * 0.25, t1, IVORY, 0.96, stagger=0.018,
                            dur=0.4, glow=0.35, out_dur=0.3)
        ta = window(t, 0.6, S.END + 1, 1.0, 0.5) * (1 - ease_io(ramp(t, S.END - 3.6, S.END - 2.8)))
        draw_text(c, 'aditazzz', VW / 2, 330, TF_MONO, 24, IVORY, ta * 0.8, tracking=9)
        draw_text(c, S.TITLE, VW / 2, 368, TF_MONO, 15, SILVER, ta * 0.55, tracking=6)
        S.hud(c, t, A, True)
        c.drawImageRect(g, skia.Rect(0, 0, VW, VH), skia.SamplingOptions(), skia.Paint(BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10))
        c.drawImage(VVIG, 0, 0)
        sv.readPixels(iv, bv, VW * 4, 0, 0); pv.stdin.write(bv.tobytes())
    for p_ in (ph, pv):
        p_.stdin.close(); p_.wait()


def render_range(f0, f1, out, vertical=False):
    w, h = (VW, VH) if vertical else (W, H)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17' if vertical else '16', '-pix_fmt', 'yuv420p',
           '-tune', 'grain', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = skia.Surface(w, h)
    info = skia.ImageInfo.Make(w, h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    buf = np.empty((h, w, 4), np.uint8)
    fn = render_frame_v if vertical else render_frame
    for fi in range(f0, f1):
        fn(fi / FPS, surf)
        surf.readPixels(info, buf, w * 4, 0, 0)
        p.stdin.write(buf.tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    mode = sys.argv[2]
    os.makedirs(os.path.join(PROJ, 'stills'), exist_ok=True)
    if mode == 'still':
        for ts in sys.argv[3:]:
            render_frame(float(ts)).makeImageSnapshot().save(os.path.join(PROJ, 'stills', f's_{float(ts):07.2f}.png'), skia.kPNG)
    elif mode == 'vstill':
        for ts in sys.argv[3:]:
            render_frame_v(float(ts)).makeImageSnapshot().save(os.path.join(PROJ, 'stills', f'v_{float(ts):07.2f}.png'), skia.kPNG)
    elif mode == 'range':
        render_range(int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
    elif mode == 'both':
        render_both(int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6])
    elif mode == 'vrange':
        render_range(int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], vertical=True)
