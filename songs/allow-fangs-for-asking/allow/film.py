"""The edit: every shot, its camera and its state, cut to cues measured from the recording (cues.json).
Render any time t to a finished frame with Film(W, H).frame(t)."""
import math
import numpy as np, cv2
from .fx import finish, sstep, clamp, lerp, ease_io, ease_out, rgb, n1, F32, blur, paste_add, font
from .kit import lyric
from . import timeline as T

C = T.C
SONG_END = 239.2
TAIL = 6.0                               # silent end card for YouTube's end-screen elements
DUR = SONG_END + TAIL


def camera(img, zoom=1.0, cx=0.5, cy=0.5, dx=0.0, dy=0.0):
    """Push in / drift: scale about (cx, cy) (fractions of the frame), then shift by (dx, dy) (fractions)."""
    if abs(zoom - 1) < 1e-4 and abs(dx) < 1e-5 and abs(dy) < 1e-5: return img
    H, W = img.shape[:2]
    px, py = cx * W, cy * H
    M = np.array([[zoom, 0, px - zoom * px + dx * W], [0, zoom, py - zoom * py + dy * H]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def u(t, a, b): return clamp((t - a) / max(1e-3, b - a))


# (shot, start, end): hard cuts on measured musical moments
EDIT = [
    ('pane', 0.0, 17.07),            # intro: the pane, his words in the fog, three taps in the silence
    ('master', 17.07, 30.45),        # band returns: the room; "Allow" in frost; a tap on the glass
    ('shoulder', 30.45, 38.0),       # manners, velvet voice: his silhouette beyond the rain
    ('sill', 38.0, 45.3),            # the stories, garlic and crosses
    ('bolts', 45.3, 51.0),           # three bolts shut... one slides back
    ('master', 51.0, 53.28),         # "just for tonight": the flame leans toward the glass
    ('shoulder', 53.28, 60.4),       # pre: he only comes when he's invited (closer)
    ('master', 60.4, 68.46),         # "May I?" an oval clears in the fog; the phone wakes
    ('master', 68.46, 78.08),        # CHORUS 1: every Allow pulls the room toward blue
    ('phone_sill', 78.08, 83.76),    # "oh so politely": the first prompt
    ('neck', 83.76, 88.0),           # "Fangs for asking": two red badges
    ('phone_sill', 88.0, 93.28),     # Allow, allow: Location
    ('bed', 93.28, 95.76),           # "I'll sleep when I'm undead"
    ('master', 95.76, 98.9),         # VERSE 2: time has passed; blue
    ('phone_hand', 98.9, 103.44),    # 3 a.m.; "You look tired"
    ('neck', 103.44, 110.24),        # two little marks; I check, and I check
    ('master', 110.24, 117.52),      # the sun rings at seven; snooze; curtains
    ('mirror', 117.52, 124.64),      # the room looks back, but I'm not there
    ('shoulder', 124.64, 131.68),    # PRE 2: he is right at the glass now
    ('master', 131.68, 139.74),      # "May I?" again, closer
    ('master', 139.74, 149.36),      # CHORUS 2: nearly all blue
    ('phone_hand', 149.36, 153.6),   # Camera, Microphone
    ('neck', 153.6, 157.6),          # Fangs for asking
    ('phone_sill', 157.6, 161.5),    # Allow, allow
    ('master', 161.5, 167.12),       # undead: the candle goes out
    ('bolts', 167.12, 170.64),       # BRIDGE: the bolt is open, nothing broken
    ('master', 170.64, 174.08),      # I held the door
    ('phone_hand', 174.08, 177.6),   # Contacts -> Send to Sister
    ('street', 177.6, 185.76),       # the light travels to her sister's window
    ('sister', 185.76, 192.24),      # BREAK: three taps; her hand; "Allow?" written backwards
    ('sister_room', 192.24, 197.04), # "Allow? Allow?" from inside: she is the one outside now
    ('face', 197.04, 204.56),        # FINAL: funny how I'm the one who's asking now
    ('sister_room', 204.56, 209.63), # you answer, like I taught you to
    ('face', 209.63, 214.5),         # Fangs for asking
    ('city', 214.5, 235.3),          # windows go blue one by one; a warm light comes on; taps
    ('black', 235.3, DUR),           # cut to black on the chord; aditazzz
]


class Film:
    def __init__(self, W, H, hook=None):
        """hook: (text, t0, t1) on-screen hook for vertical clips (the first seconds of a Short)."""
        self.W, self.H = W, H; self.scenes = {}; self.hook = hook

    def scene(self, name):
        if name not in self.scenes:
            for k in list(self.scenes): del self.scenes[k]          # big scenes: keep only the one on screen
            import gc; gc.collect()
            W, H = self.W, self.H
            if name == 'master':
                from .master import Master; obj = Master(W, H)
            elif name == 'shoulder':
                from .shoulder import Shoulder; obj = Shoulder(W, H)
            elif name == 'mirror':
                from .others import Mirror; obj = Mirror(W, H)
            elif name == 'sister':
                from .others import Sister; obj = Sister(W, H)
            elif name == 'city':
                from .others import City; obj = City(W, H)
            elif name == 'pane':
                from .macro import Pane; obj = Pane(W, H)
            elif name == 'bolts':
                from .macro import Bolts; obj = Bolts(W, H)
            elif name == 'street':
                from .street import Street; obj = Street(W, H)
            else:
                from . import shots as S
                obj = {'sill': S.sill, 'bed': S.bed, 'phone_sill': S.phone_sill, 'phone_hand': S.phone_hand,
                       'sister_room': S.sister_room, 'neck': S.Neck, 'face': S.face}[name](W, H)
            self.scenes[name] = obj
        return self.scenes[name]

    def shot(self, t):
        for name, a, b in EDIT:
            if a <= t < b: return name, a, b
        return EDIT[-1]

    # ================================================================ shots
    def pane(self, t, a, b):
        P = self.scene('pane'); s = P.s
        words = [10.32, 12.72, 13.04, 13.2, 13.36, 13.6, 13.76]
        wr = P.writing(t, words, ['“Midnight” would like to', 'send you notifications'],
                       'CormorantGaramond-MediumItalic.ttf', 64 * s, P.P(800, 330))
        wr = wr * (1 - 0.6 * sstep(15.0, 17.0, t))                       # his breath fades as the taps come
        taps = [(*P.P(985, 420), t - tt, 1.0) for tt in C['intro']['taps'] if 0 <= t - tt < 2.5]
        st = dict(writing=wr, taps=taps, expo=lerp(0.0, 1.0, ease_io(u(t, 0.1, 6.5))),
                  presence=0.85 * ease_io(u(t, 14.2, 15.4)), fog=1.0)
        img = P.render(t, st)
        return camera(img, 1.02 + 0.05 * ease_io(u(t, 0, 17.07)), 0.55, 0.42)

    def _fog_oval(self, M, t, t0):
        """'May I?': condensation clears in an oval, as if a face leaned to the glass."""
        k = sstep(t0 - 0.1, t0 + 0.5, t) * (1 - sstep(t0 + 2.6, t0 + 4.5, t))
        if k <= 0: return None, None
        cx, cy = M.P(985, 400)
        e = ((M.xx - cx) / (M.s * 70)) ** 2 + ((M.yy - cy) / (M.s * 95)) ** 2
        clear = (np.exp(-e ** 2) * k).astype(F32)
        extra = (0.35 * sstep(t0 - 3, t0, t) * M.glass_mask_full).astype(F32)
        return extra, clear

    def master(self, t, a, b):
        M = self.scene('master')
        if not hasattr(M, 'glass_mask_full'):
            g = np.zeros((self.H, self.W), F32); gl = M.glass
            g[gl.y0:gl.y1, gl.x0:gl.x1] = gl.m; M.glass_mask_full = g
        st = T.master_state(t)
        B = T.blue(t)
        # the frost Allow: his first word, then it keeps catching whatever light rules the room
        fx, fy = M.P(982, 585)
        p = ease_io(u(t, 21.95, 23.85))
        if p > 0:
            lt = rgb(1.0, 0.72, 0.45) * 0.45 * (1 - B) + rgb(0.25, 0.55, 1.0) * (0.6 + 0.6 * T.pulse(t)) * B
            st['frost'] = M.glass.frost_word('Allow', 'CormorantGaramond-MediumItalic.ttf', 64 * M.s, fx, fy, p, t, lt,
                                             opacity=0.7 + 0.15 * B)
        tx, ty = M.P(1012, 455)
        st['taps'] = T.tap_rings(t, [C['v1']['taps_on_glass']], [(tx, ty)], 0.8)
        for t0 in (C['pre1']['may_i'], C['pre2']['may_i']):
            if t0 - 3.2 < t < t0 + 4.6:
                ex, cl = self._fog_oval(M, t, t0)
                if ex is not None: st['extra_fog'], st['clear'] = ex, cl
        # dawn at seven: warm daylight tries the window; snooze; the curtains shut it out
        if 110.0 < t < 117.6:
            d = sstep(110.3, 111.6, t) * (1 - 0.7 * sstep(112.5, 113.2, t)) * (1 - sstep(114.9, 116.6, t))
            st['night'] = st['night'] * (1 - 0.5 * d)
            st['street'] = 1.0 + 1.8 * d - 0.85 * sstep(114.9, 116.6, t)
            st['pulse'] = st['pulse'] + 1.2 * math.exp(-max(0, t - 111.44) * 1.8) * (t > 111.4) * (t < 112.6)
        if t >= 114.9 and t < 139.74:
            st['street'] = min(st.get('street', 1.0), 1.0 - 0.85 * sstep(114.9, 116.6, t) if t < 117.6 else 0.15)
        # the candle: lower in verse 2, fighting in chorus 2, out on "undead"
        flame = 1.0 - 0.25 * sstep(95.0, 96.0, t) - 0.25 * sstep(139.0, 141.0, t)
        flame *= 1 - sstep(164.3, 164.9, t)
        st['flame'] = flame; st['gutter'] = 0.5 * sstep(139.0, 141.0, t)
        if t > 164.4:
            st['warm'] = st['warm'] * (1 - 0.85 * sstep(164.3, 165.2, t)); st['warm_near'] = st['warm']
        img = M.render(t, st)
        # the screen's blue takes the whole room, the street beyond the glass included (lights keep a little warmth)
        if B > 0.05:
            from .shots import cold_grade
            img = cold_grade(img, min(0.9, 0.95 * B), keep_emissive=0.5)
        # smoke from the wick after it goes out
        if 164.5 < t < 170:
            img = img + self._smoke(M, t - 164.5)
        if a == 17.07:   z = 1 + 0.035 * u(t, a, b)
        elif a == 60.4:  z = 1.06 + 0.10 * ease_io(u(t, a, b))             # pre-chorus: lean in toward the glass
        elif a == 131.68: z = 1.10 + 0.08 * ease_io(u(t, a, b))
        elif a in (68.46, 139.74): z = 1.0 + 0.03 * u(t, a, b)
        elif a == 170.64: z = 1.18 - 0.06 * u(t, a, b)
        else: z = 1.02 + 0.02 * u(t, a, b)
        return camera(img, z, 0.51, 0.47)

    def _smoke(self, M, age):
        bx, by = M.flame_xy
        out = np.zeros((self.H, self.W, 3), F32)
        for k in range(26):
            v = k / 26.0; h = age * 40 * M.s * (0.3 + v)
            x = bx + M.s * 8 * math.sin(v * 9 + age * 1.3) * v * 3
            y = by - h - v * 60 * M.s
            r = M.s * (2 + 10 * v)
            a = 0.025 * (1 - v) * math.exp(-age * 0.45)
            x0, y0 = int(x - r * 3), int(y - r * 3); x1, y1 = int(x + r * 3), int(y + r * 3)
            if x1 <= 0 or y1 <= 0 or x0 >= self.W or y0 >= self.H: continue
            ys, xs = np.mgrid[max(0, y0):min(self.H, y1), max(0, x0):min(self.W, x1)].astype(F32)
            g = np.exp(-((xs - x) ** 2 + (ys - y) ** 2) / r ** 2) * a
            out[max(0, y0):min(self.H, y1), max(0, x0):min(self.W, x1)] += g[..., None] * rgb(0.5, 0.6, 0.8)
        return out

    def shoulder(self, t, a, b):
        S = self.scene('shoulder')
        B = T.blue(t)
        if a == 30.45:  pres, close = ease_io(u(t, 31.0, 33.6)), 0.12 + 0.18 * ease_io(u(t, 31.0, 38.0))
        elif a == 53.28: pres, close = 1.0, 0.45 + 0.2 * u(t, a, b)
        else:           pres, close = 1.0, 0.85 + 0.15 * u(t, a, b)
        st = dict(warm=1.0 - 0.6 * B, phone=1.0 + 0.4 * T.pulse(t) + 0.6 * B, presence=pres, closeness=close,
                  lean=0.3 * B)
        img = S.render(t, st)
        if B > 0.05:
            from .shots import cold_grade
            img = cold_grade(img, min(0.9, 1.0 * B))
        uu = u(t, a, b)
        return camera(img, 1 + 0.03 * uu + (0.05 if a == 124.64 else 0), 0.62, 0.42, dx=-0.004 * uu)

    def sill(self, t, a, b):
        S = self.scene('sill')
        img = S.render(t, dict(flame=1.0))
        return camera(img, 1.0 + 0.05 * ease_io(u(t, a, b)), 0.35, 0.5, dx=0.012 * u(t, a, b))

    def bolts(self, t, a, b):
        Bo = self.scene('bolts')
        if a == 45.3:
            v = C['v1']
            tt = [v['bolt'], v['window'], v['tight']]
            sh = [ease_out(u(t, x - 0.05, x + 0.16)) for x in tt]
            mv = [math.exp(-((t - x - 0.06) / 0.06) ** 2) for x in tt]
            # "Then I open the door...": the middle bolt slides back, slowly
            back = ease_io(u(t, v['open'], v['door'] + 0.6))
            sh[1] = sh[1] * (1 - back)
            gl = [math.exp(-max(0, t - x - 0.1) * 4) * (t > x) for x in tt]
            img = Bo.render(t, dict(bolts=sh, moving=mv, glint=gl))
            return camera(img, 1.03 + 0.02 * u(t, a, b), 0.55, 0.55)
        # bridge: all open, nothing broken; cold now
        from .shots import cold_grade
        img = cold_grade(Bo.render(t, dict(bolts=(0, 0, 0))), 0.75)
        return camera(img, 1.08 + 0.06 * ease_io(u(t, a, b)), 0.45, 0.55)

    def _prompt_for(self, t):
        if t < 85: return 'notifications'
        if t < 95: return 'location'
        if t < 151.5: return 'camera'
        if t < 165: return 'microphone'
        return 'contacts'

    def _press(self, t):
        best = 0.0
        for a_, b_ in T.ALLOWS:
            x = t - b_
            if -0.05 < x < 0.5: best = max(best, math.exp(-max(0, x) * 6))
        return best

    def phone_sill(self, t, a, b):
        from . import ui as UI
        S = self.scene('phone_sill'); B = T.blue(t)
        n_allow = sum(1 for _, b_ in T.ALLOWS if b_ <= t)
        scr = UI.screen('prompt', self._prompt_for(t), w=2532, h=1170, press=self._press(t),
                        allow_scale=1.0 + 0.09 * n_allow, time_str='12:%02d' % min(59, int(t // 4)))
        img = S.render(t, dict(ui=scr, cold=0.25 + 0.5 * B, screen_expo=1.0 + 0.5 * T.pulse(t)))
        return camera(img, 1.04 + 0.04 * u(t, a, b), 0.6, 0.62)

    def phone_hand(self, t, a, b):
        from . import ui as UI
        S = self.scene('phone_hand'); B = T.blue(t)
        if a == 98.9:
            scr = UI.screen('lock', w=1170, h=2532, time_str='3:07')
        elif a == 174.08:
            if t < C['bridge']['send'] - 0.2:
                scr = UI.screen('prompt', 'contacts', w=1170, h=2532, press=self._press(t), allow_scale=2.0)
            else:
                scr = UI.screen('share', w=1170, h=2532, press=sstep(C['bridge']['link'] - 0.3, C['bridge']['link'], t))
        else:
            k = 'camera' if t < 151.5 else 'microphone'
            scr = UI.screen('prompt', k, w=1170, h=2532, press=self._press(t), allow_scale=1.9)
        img = S.render(t, dict(ui=scr, cold=0.35 + 0.5 * B, screen_expo=1.0 + 0.4 * T.pulse(t)))
        # the sent light leaves the phone
        if a == 174.08 and t > C['bridge']['link']:
            q = S.screen.mean(0); k = math.exp(-max(0, t - C['bridge']['link']) * 1.5)
            r2 = ((S.xx - q[0]) ** 2 + (S.yy - q[1]) ** 2) / (S.s * 60) ** 2
            img = img + (np.exp(-r2) * 0.5 * k)[..., None] * rgb(0.3, 0.55, 1.0)
        return camera(img, 1.03 + 0.05 * ease_io(u(t, a, b)), 0.62, 0.45)

    def neck(self, t, a, b):
        S = self.scene('neck'); B = T.blue(t)
        if a == 103.44:
            badges = ease_out(u(t, C['v2']['marks'][0] + 0.3, C['v2']['marks'][0] + 1.6)) * (1 - sstep(109.9, 110.2, t))
            checks = sum(math.exp(-max(0, t - c) * 5) * (t > c) for c in C['v2']['checks'])
            badges = badges * (0.75 + 0.25 * checks) if t < 106.6 else 0.15 + 0.85 * checks
        else:
            f0 = C['ch1']['fangs'] if a == 83.76 else C['ch2']['fangs']
            badges = ease_out(u(t, f0 + 0.15, f0 + 0.9)) * (1 - sstep(b - 0.6, b - 0.1, t))
        img = S.render(t, dict(badges=badges, cold=0.15 + 0.4 * B))
        return camera(img, 1.04 + 0.05 * ease_io(u(t, a, b)), 0.6, 0.62)

    def bed(self, t, a, b):
        S = self.scene('bed')
        img = S.render(t, dict(cold=0.2))
        return camera(img, 1.02 + 0.015 * u(t, a, b), 0.7, 0.5)       # held almost still

    def mirror(self, t, a, b):
        Mi = self.scene('mirror')
        img = Mi.render(t, dict(warm=0.65, cold=0.8, phone=1.25))
        return camera(img, 1.0 + 0.025 * ease_io(u(t, a, b)), 0.68, 0.48)   # a slow lean toward the glass

    def street(self, t, a, b):
        S = self.scene('street')
        tr = ease_io(u(t, C['bridge']['link'] + 1.0, C['bridge']['her_door']))
        arr = math.exp(-max(0, t - C['bridge']['her_door']) * 1.4) * (t > C['bridge']['her_door'])
        img = S.render(t, dict(travel=tr, arrive=arr))
        # the camera follows: wide, then a long push toward her sister's window
        z = 1.0 + 0.55 * ease_io(u(t, a + 1.0, b))
        return camera(img, z, 0.79, 0.27)

    def sister(self, t, a, b):
        Si = self.scene('sister'); s = Si.s
        taps = C['break']['taps']
        rise = ease_out(u(t, taps[0] - 1.0, taps[0] + 0.05))
        tp = [(*Si.tips[2], t - x, 0.9) for x in taps if 0 <= t - x < 2.5]
        wr = ease_io(u(t, C['break']['allow_q'] - 0.15, C['break']['allow_q'] + 0.9))
        img = Si.render(t, dict(hand=1.0 if t > taps[0] - 1.0 else 0.0, rise=rise, taps=tp, write=wr,
                                tips=sstep(taps[0], taps[2] + 0.5, t)))
        return camera(img, 1.0 + 0.04 * ease_io(u(t, a, b)), 0.6, 0.45)

    def sister_room(self, t, a, b):
        S = self.scene('sister_room')
        if a == 192.24: cold = 0.1
        else:           cold = 0.15 + 0.7 * ease_io(u(t, C['final']['drink_you'] + 2, C['final']['answer'] + 3.5))
        img = S.render(t, dict(cold=cold))
        if a == 204.56:   # her phone wakes on the nightstand: 'Sis' would like to send you notifications
            lx, ly = S.P(470, 560)
            k = sstep(C['final']['answer'] + 0.2, C['final']['answer'] + 1.2, t)
            r2 = ((S.xx - lx) ** 2 + (S.yy - ly) ** 2) / (S.s * 120) ** 2
            img = img + (k * 0.20 / (1 + r2))[..., None] * rgb(0.25, 0.5, 1.0)
        return camera(img, 1.02 + 0.06 * ease_io(u(t, a, b)), 0.62, 0.4)

    def face(self, t, a, b):
        S = self.scene('face')
        img = S.render(t, dict(cold=0.25))
        return camera(img, 1.03 + 0.04 * u(t, a, b), 0.42, 0.42)

    def city(self, t, a, b):
        Ci = self.scene('city')
        spread = 0.15 + 0.85 * ease_io(u(t, 214.5, 226.5))
        on = sstep(C['outro']['light_comes_on'] - 0.1, C['outro']['light_comes_on'] + 0.6, t)
        img = Ci.render(t, dict(spread=spread, last_on=on))
        # the rise over the street, then three punch-ins toward the warm window on the stabs
        z = 1.0 + 0.10 * ease_io(u(t, 214.5, 227.5))
        stabs = C['outro']['stabs']
        for i, sx in enumerate(stabs[:3]):
            if t >= sx: z = 1.35 + 0.45 * i
        lx, ly = Ci.P(428, 268)
        if t >= stabs[0]:
            return camera(img, z, lx / self.W, ly / self.H)
        return camera(img, z, 0.5, 0.42, dy=-0.02 * ease_io(u(t, 214.5, 227.5)))

    def black(self, t, a, b):
        img = np.zeros((self.H, self.W, 3), F32)
        k = sstep(236.2, 237.4, t) * (1 - sstep(DUR - 1.2, DUR - 0.2, t))
        if k > 0:
            img = lyric(img, 'aditazzz', self.W, self.H, op=k * 0.9, size=0.040, y_frac=0.52, track=0.18,
                        color=(0.80, 0.76, 0.70))
            img = lyric(img, 'Allow (Fangs for Asking)', self.W, self.H, op=k * 0.55, italic=True, size=0.026,
                        y_frac=0.585, track=0.04, color=(0.70, 0.66, 0.60))
        return img

    # ================================================================ frame
    def frame(self, t, fi=0):
        name, a, b = self.shot(t)
        img = getattr(self, name)(t, a, b)
        if name != 'black':
            txt, op, it = T.lyric_at(t)
            if txt: img = lyric(img, txt, self.W, self.H, op=op, italic=it)
        if self.hook and self.hook[1] - 0.01 <= t < self.hook[2] + 0.4:
            k = 1 - sstep(self.hook[2], self.hook[2] + 0.4, t)
            img = img * (1 - 0.35 * k)
            img = lyric(img, self.hook[0], self.W, self.H, op=k, size=0.085, y_frac=0.30, color=(0.95, 0.92, 0.86))
        return finish(img, t, seed=7, grain=0.026 if name != 'black' else 0.012, letterbox=2.0 if self.W > self.H else 0)
