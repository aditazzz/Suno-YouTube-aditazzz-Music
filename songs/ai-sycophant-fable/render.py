import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)  # repo layout (the chat used an absolute path)
import numpy as np
import skia
from lib import *
from timeline import SECTIONS, END
import scenes

# ---------------------------------------------------------------- audio features at FPS
_an = np.load(os.path.join(HERE, 'analysis.npz'))
_t = _an['t']
_low = _an['low']
_rms = _an['rms']
on = np.maximum(0, np.diff(np.log1p(_low), prepend=0))
on = np.maximum(on - np.convolve(on, np.ones(43) / 43, 'same'), 0)
on = on / (np.percentile(on, 99) + 1e-9)
NF = int(END * FPS) + 1
ft = np.arange(NF) / FPS
kick_raw = np.zeros(NF)
for i, tt in enumerate(ft):
    sel = (_t >= tt - 0.5 / FPS) & (_t < tt + 0.5 / FPS)
    kick_raw[i] = on[sel].max() if sel.any() else 0
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


def render_frame(t, surf=None):
    fi = int(round(t * FPS))
    A = features(fi)
    surf = surf or skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(BG)
    c.drawImage(BGIMG, 0, 0)
    # camera: slow drift + kick breath
    dx = noise1(t * 0.15, 1) * 10
    dy = noise1(t * 0.13, 2) * 7
    rot = noise1(t * 0.1, 3) * 0.25
    z = 1 + 0.006 * A['kick']
    c.save()
    c.translate(W / 2 + dx, H / 2 + dy)
    c.rotate(rot)
    c.scale(z, z)
    c.translate(-W / 2, -H / 2)
    for name, a, b in SECTIONS:
        if a - 0.7 <= t <= b + 0.7:
            scenes.SECTION_FN[name](c, t, A)
    c.restore()
    scenes.lyric_track(c, t)
    scenes.hud(c, t, A)
    # grain + vignette
    g = GRAIN[fi % len(GRAIN)]
    gp = skia.Paint(BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10)
    c.drawImageRect(g, skia.Rect(0, 0, W, H), skia.SamplingOptions(), gp)
    c.drawImage(VIG, 0, 0)
    return surf


VW, VH = 1080, 1920
V_SCALE = 0.75
V_Y0 = 520
V_X0 = (VW - W * V_SCALE) / 2


def _vbg():
    surf = skia.Surface(VW, VH)
    c = surf.getCanvas()
    shader = skia.GradientShader.MakeRadial(
        (VW / 2, V_Y0 + 400), VW * 1.0,
        [skia.Color4f(19 / 255, 19 / 255, 21 / 255, 1), skia.Color4f(10 / 255, 10 / 255, 11 / 255, 1)], [0.0, 1.0])
    c.drawRect(skia.Rect(0, 0, VW, VH), skia.Paint(Shader=shader))
    return surf.makeImageSnapshot()


def _vvig():
    surf = skia.Surface(VW, VH)
    c = surf.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 0))
    shader = skia.GradientShader.MakeRadial(
        (VW / 2, VH / 2), VH * 0.62,
        [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0.7)], [0.0, 0.5, 1.0])
    c.drawRect(skia.Rect(0, 0, VW, VH), skia.Paint(Shader=shader))
    return surf.makeImageSnapshot()


VBG, VVIG = None, None
_scene_surf = None


def scene_layer_image(t, A):
    global _scene_surf
    if _scene_surf is None:
        _scene_surf = skia.Surface(W, H)
    c = _scene_surf.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 0))
    dx = noise1(t * 0.15, 1) * 10
    dy = noise1(t * 0.13, 2) * 7
    rot = noise1(t * 0.1, 3) * 0.25
    z = 1 + 0.006 * A['kick']
    c.save()
    c.translate(W / 2 + dx, H / 2 + dy); c.rotate(rot); c.scale(z, z); c.translate(-W / 2, -H / 2)
    for name, a, b in SECTIONS:
        if a - 0.7 <= t <= b + 0.7:
            scenes.SECTION_FN[name](c, t, A)
    c.restore()
    # soft fade at the top and bottom of the band
    fade = skia.GradientShader.MakeLinear(
        [(0, 0), (0, H)],
        [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 1), skia.Color4f(0, 0, 0, 1), skia.Color4f(0, 0, 0, 0)],
        [0.0, 0.1, 0.9, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=fade, BlendMode=skia.BlendMode.kDstIn))
    return _scene_surf.makeImageSnapshot()


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
    global VBG, VVIG
    if VBG is None:
        VBG, VVIG = _vbg(), _vvig()
    fi = int(round(t * FPS))
    A = features(fi)
    surf = surf or skia.Surface(VW, VH)
    c = surf.getCanvas()
    c.clear(BG)
    c.drawImage(VBG, 0, 0)
    img = scene_layer_image(t, A)
    c.drawImageRect(img, skia.Rect(V_X0, V_Y0, V_X0 + W * V_SCALE, V_Y0 + H * V_SCALE),
                    skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    # lyrics, wrapped, inside the safe frame
    for (t0, t1, s_, st) in scenes.LINES:
        if st != 'lyric' or t < t0 - 0.1 or t > t1 + 0.5:
            continue
        lines = wrap_line(s_, TF_SERIF_I, 58, 900)
        for k, ln in enumerate(lines):
            y = 1430 + k * 70 - (len(lines) - 1) * 35
            reveal_text(c, ln, VW / 2, y, TF_SERIF_I, 58, t, t0 + k * 0.25, t1, IVORY, 0.96, stagger=0.018, dur=0.4,
                        glow=0.35, out_dur=0.3)
    # title + reward
    ta = window(t, 0.6, END + 1, 1.0, 0.5) * (1 - ease_io(ramp(t, 259.6, 260.4)))
    draw_text(c, 'aditazzz', VW / 2, 330, TF_MONO, 24, IVORY, ta * 0.8, tracking=9)
    draw_text(c, 'AI SYCOPHANT (RLHF)', VW / 2, 368, TF_MONO, 15, SILVER, ta * 0.55, tracking=6)
    ha = window(t, 12.5, 259.8, 1.5, 0.6) * 0.6
    if ha > 0:
        r = scenes.reward_at(t)
        draw_text(c, 'REWARD', VW / 2 - 90, 440, TF_MONO, 14, SILVER, ha * 0.8, align='left', tracking=4)
        draw_text(c, f'{r:0.3f}', VW / 2 + 90, 440, TF_MONO, 14, IVORY if t < 258.0 else COOL, ha, align='right', tracking=3)
        bar = skia.Path(); bar.moveTo(VW / 2 - 90, 455); bar.lineTo(VW / 2 + 90, 455)
        c.drawPath(bar, stroke_paint(SILVER, ha * 0.4, 1.0))
        fb = skia.Path(); fb.moveTo(VW / 2 - 90, 455); fb.lineTo(VW / 2 - 90 + 180 * r, 455)
        c.drawPath(fb, stroke_paint(IVORY, ha, 2.0))
    g = GRAIN[fi % len(GRAIN)]
    c.drawImageRect(g, skia.Rect(0, 0, VW, VH), skia.SamplingOptions(),
                    skia.Paint(BlendMode=skia.BlendMode.kOverlay, Alphaf=0.10))
    c.drawImage(VVIG, 0, 0)
    return surf


def render_range_v(f0, f1, out):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{VW}x{VH}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-tune', 'grain', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = skia.Surface(VW, VH)
    info = skia.ImageInfo.Make(VW, VH, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    buf = np.empty((VH, VW, 4), np.uint8)
    for fi in range(f0, f1):
        render_frame_v(fi / FPS, surf)
        surf.readPixels(info, buf, VW * 4, 0, 0)
        p.stdin.write(buf.tobytes())
        if fi % 150 == 0:
            print(out, fi, flush=True)
    p.stdin.close()
    p.wait()


def still(t, path):
    render_frame(t).makeImageSnapshot().save(path, skia.kPNG)


def render_range(f0, f1, out):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-tune', 'grain', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    buf = np.empty((H, W, 4), np.uint8)
    for fi in range(f0, f1):
        render_frame(fi / FPS, surf)
        surf.readPixels(info, buf, W * 4, 0, 0)
        p.stdin.write(buf.tobytes())
        if fi % 150 == 0:
            print(out, fi, flush=True)
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    if sys.argv[1] == 'still':
        for ts in sys.argv[2:]:
            still(float(ts), os.path.join(HERE, 'stills', f's_{float(ts):07.2f}.png'))
    elif sys.argv[1] == 'vstill':
        for ts in sys.argv[2:]:
            render_frame_v(float(ts)).makeImageSnapshot().save(os.path.join(HERE, 'stills', f'v_{float(ts):07.2f}.png'), skia.kPNG)
    elif sys.argv[1] == 'vrange':
        render_range_v(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif sys.argv[1] == 'range':
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
