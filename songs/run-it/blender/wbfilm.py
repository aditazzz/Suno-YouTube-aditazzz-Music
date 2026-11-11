"""Run It: the workbench film. Blender frame == film frame (30 fps, frame = round(seconds * 30)).
build() makes the whole scene; each shot function keys Claude, the props and its camera for its own frame range.
The monitor text is driven by a frame handler (install_handlers), so it must be installed in every render job."""
import bpy, os, json, math, random
from mathutils import Vector, Matrix, Euler, Quaternion
import wb, wbset, wbrig, wbprops
from wbrig import RX, RY, RZ
D = bpy.data; FPS = 30
def F(t): return int(round(t * FPS))
def rad(a): return math.radians(a)
def smooth(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def V(*a): return Vector(a)
TL = json.load(open(os.path.join(wb.ROOT, 'songs/run-it/remotion/src/data/timeline.json')))
LINES = TL['lines']
C = wbset.C; BZ = wbset.BZ; IZ = wbset.ISLE_Z; CY = wbset.CLAUDE_Y
# hand orientations (rotation on top of the rest hand: fingers down, palm toward the body's midline, thumb forward)
H_DOWN = Matrix.Identity(4)
H_FWD = RX(rad(-90))                                   # fingers toward the camera, thumb up
def H_PALM(s, pitch=-90): return RX(rad(pitch)) @ RZ(rad(90 if s == 'L' else -90))    # fingers forward, palm down
def H_PITCH(a): return RX(rad(-a))                     # fingers a degrees forward of straight down
REACH = .262


# ---------------------------------------------------------------- the animation recorder
class Anim:
    """Channel-wise keys with a running pose, so actions overlap naturally (each channel eases between its own keys).
    channels: hips=(dx,dy,dz)  spine=(lean,twist,side)  hL/hR=(world pos, 4x4 rot)  pL/pR=world pole  head=(x,y,z) local
              lids=close  brow=tilt  fL/fR=(curl, thumb)  look=world point (baked per frame at the end of the shot)"""
    def __init__(self, arm):
        self.R = wbrig.Rig(arm); self.cur = {}; self.looks = []; self.held = []; self.lastq = {}; self.sc = bpy.context.scene; self._lean0 = 6; self.off = Vector((0, 0, 0)); self.prev = None

    @property
    def lean0(self): return self._lean0

    @lean0.setter
    def lean0(self, v): self._lean0 = v; self.prev = None              # a new posture: solve it fresh

    def k(self, f, **ch):
        self.sc.frame_set(f)
        for name in ('hips', 'spine', 'feet', 'pL', 'pR', 'hL', 'hR', 'head', 'lids', 'brow', 'fL', 'fR', 'look'):
            if name in ch: self.cur[name] = ch[name]; self._write(name, ch[name], f)

    def hold(self, f, *names):
        self.sc.frame_set(f)
        for n in (names or [n for n in self.cur if n != 'look']): self._write(n, self.cur[n], f)

    def _fixq(self, bone, f):
        p = self.R.PB[bone]; q = p.rotation_quaternion.copy(); l = self.lastq.get(bone)
        if l is not None and q.dot(l) < 0: q.negate(); p.rotation_quaternion = q; p.keyframe_insert('rotation_quaternion', frame=f)
        self.lastq[bone] = q

    def _write(self, name, v, f):
        R = self.R
        if name == 'hips': R.hips(v, f=f)
        elif name == 'spine': R.spine(*v, f=f); self._fixq('spine', f)
        elif name in ('hL', 'hR'): R.hand(name[1], v[0], v[1], f); self._fixq('CTRL_hand_' + name[1], f)
        elif name in ('pL', 'pR'): R.at('POLE_elbow_' + name[1], v, None, f)
        elif name == 'feet':
            for sd in 'LR': R.bone('CTRL_foot_' + sd, (0, v[0], v[1]), RX(v[2]) if len(v) > 2 else None, f)
        elif name == 'head': R.head(v, f)
        elif name == 'lids': R.lids(v, f) if not isinstance(v, tuple) else R.lids(0, f, L=v[0], R=v[1])
        elif name == 'brow': R.brows(v, f) if not isinstance(v, tuple) else R.brows(0, f, L=v[0], R=v[1])
        elif name in ('fL', 'fR'): R.fingers(name[1], v[0], f, v[1], each=(v[2] if len(v) > 2 else None))
        elif name == 'look': self.looks.append((f, Vector(v[0]), v[1]) if len(v) == 2 else (f, Vector(v), 3))

    # ---- the body follows the hands
    def shoulder(self, s, dy, dz, lean, twist):
        v = (RZ(twist) @ RX(lean)) @ Vector((-.2 if s == 'L' else .2, 0, .235)); return Vector((0, CY + dy, .33 + dz)) + v + self.off

    def solve(self, wL=None, wR=None, lean0=6, bias_twist=0):
        """smallest lean / twist / step-in that puts both wrists within reach of the shoulders. If nothing reaches, the pose
        that misses by least (the arm simply ends up straight). Returns (hips, spine)."""
        best = None; near = None
        for dy in (0, -.02, -.04, -.06, -.08):
            dz = -(.23 - math.sqrt(.23 ** 2 - dy ** 2)) - .004
            for lean in range(4, 53, 2):
                for tw in range(-36, 37, 4):
                    ex = 0.0
                    for s, w in (('L', wL), ('R', wR)):
                        if w is not None: ex = max(ex, (Vector(w) - self.shoulder(s, dy, dz, rad(lean), rad(tw))).length - REACH)
                    cost = (lean - lean0) ** 2 + .5 * (tw - bias_twist) ** 2 + 6 * (dy * 100) ** 2
                    if self.prev is not None: cost += .6 * (lean - self.prev[0]) ** 2 + .5 * (tw - self.prev[1]) ** 2 + 4 * ((dy - self.prev[2]) * 100) ** 2      # stay near the last pose: no flapping between close keys
                    if ex <= 0:
                        if best is None or cost < best[0]: best = (cost, dy, dz, lean, tw)
                    elif near is None or ex + cost * 4e-5 < near[0]: near = (ex + cost * 4e-5, dy, dz, lean, tw)
        if best is None:
            print('[film] WARNING: out of reach by %.3f' % near[0], [round(x, 3) for x in wL] if wL is not None else None, [round(x, 3) for x in wR] if wR is not None else None); best = near
        _, dy, dz, lean, tw = best; self.prev = (lean, tw, dy)
        return (0, dy, dz), (rad(lean), rad(tw), 0)

    def pose(self, f, L=None, R=None, head=None, lean0=None, bias_twist=0, extra=None):
        """key the hands (pos, rot) and the body that lets them get there. head = world (pitch down, yaw to +X, tilt) in degrees.
        L / R may be 'relax' (hangs by his side) or None (stays where it is)."""
        wl = L[0] if isinstance(L, tuple) else (self.cur['hL'][0] if L is None and 'hL' in self.cur and not self.cur.get('relL') else None)
        wr = R[0] if isinstance(R, tuple) else (self.cur['hR'][0] if R is None and 'hR' in self.cur and not self.cur.get('relR') else None)
        hips, spine = self.solve(wl, wr, self.lean0 if lean0 is None else lean0, bias_twist)
        ch = dict(hips=hips, spine=spine)
        for s, v in (('L', L), ('R', R)):
            if isinstance(v, tuple): ch['h' + s] = v; self.cur['rel' + s] = False
            elif v == 'relax' or (v is None and self.cur.get('rel' + s)):
                sh = self.shoulder(s, hips[1], hips[2], spine[0], spine[1]); sg = -1 if s == 'L' else 1
                ch['h' + s] = (sh + Vector((sg * .035, -.05, -.245)), RX(rad(-12))); self.cur['rel' + s] = True
        if head is not None:                                           # the head is keyed only when asked: it eases from its last key, and rides the torso in between
            ch['head'] = (rad(head[0]) - spine[0] * .85, rad(head[2]) if len(head) > 2 else 0, rad(head[1]) - spine[1]); self.cur['headw'] = head
        if extra: ch.update(extra)
        self.k(f, **ch)

    def rig(self, f, off, interp=None):
        """float / move the whole of him: off = (dx, dy, dz) from his standing spot."""
        self.off = Vector(off); arm = self.R.arm; arm.location = Vector((0, CY, 0)) + self.off; arm.keyframe_insert('location', frame=f); self.sc.frame_set(f)

    def blink(self, f, close=6, hold=9, open_=8, base=0.0):
        """the slow blink (rules: 6 close / 8-12 hold / 8 open, at most one per ~10 s)."""
        for ff, v in ((f, base), (f + close, 1.0), (f + close + hold, 1.0), (f + close + hold + open_, base)): self.sc.frame_set(ff); self.R.lids(v, ff)
        self.cur['lids'] = base

    def bake_looks(self, f0, f1, up=0.0):
        """eyes: each look key starts a move that lands `dur` frames later (3 = a saccade); baked every frame so the eyes
        hold their target while the head moves under them."""
        ks = sorted(self.looks, key=lambda x: x[0])
        if not ks: return
        for f in range(f0, f1):
            i = max([j for j, k in enumerate(ks) if k[0] <= f], default=0); kf, kt, dur = ks[i]; p = ks[i - 1][1] if i > 0 else kt
            u = smooth((f - kf) / max(1, dur)) if i > 0 else 1.0
            self.sc.frame_set(f); self.R.eyes(p.lerp(kt, u), f)
            ex = self.R.O['aim_L'].rotation_euler.x                     # + = looking down: the lid comes down with the iris
            if up and f == f1 - 1: print('[looks] gaze pitch at', f, round(ex, 3), flush=True)
            for sd in 'LR':
                lp = self.R.O['lidpivot_' + sd]; lp.delta_rotation_euler = (.20 + .42 * max(0.0, ex) + up * min(0.0, ex), 0, 0)      # up > 0: the lid also lifts when he looks up past his brow (a low camera), or it hides the iris; lp.keyframe_insert('delta_rotation_euler', frame=f)
        self.looks = []

    def attach(self, prop, bone, f0, f1, at=None):
        """prop rides a bone over [f0, f1). The grip offset is taken from the scene as it stands at frame `at` (default f0)."""
        self.sc.frame_set(f0 if at is None else at); bpy.context.view_layer.update()
        off = self.R.bone_world(bone).inverted() @ prop.matrix_world; self.held.append((prop, bone, f0, f1, off))

    def bake_held(self):
        for prop, bone, f0, f1, off in self.held:
            prop.rotation_mode = 'QUATERNION'; last = None; sc0 = prop.scale.copy()
            for f in range(f0, f1):
                self.sc.frame_set(f); prop.matrix_world = self.R.bone_world(bone) @ off; prop.scale = sc0; q = prop.rotation_quaternion.copy()
                if last is not None and q.dot(last) < 0: q.negate(); prop.rotation_quaternion = q
                last = q.copy(); prop.keyframe_insert('location', frame=f); prop.keyframe_insert('rotation_quaternion', frame=f)
        self.held = []


def place(o, M):
    """set an object's world matrix, keeping its scale (works for parented objects)."""
    s = o.scale.copy(); o.matrix_world = M; o.scale = s; bpy.context.view_layer.update()


def key_w(o, f, M=None, hide=None, scale=None):
    """key an object's world placement (location + rotation) and/or visibility at frame f."""
    bpy.context.scene.frame_set(f)
    if M is not None:
        place(o, M); o.keyframe_insert('location', frame=f); o.keyframe_insert('rotation_quaternion' if o.rotation_mode == 'QUATERNION' else 'rotation_euler', frame=f)
    if scale is not None: o.scale = scale if hasattr(scale, '__len__') else (scale,) * 3; o.keyframe_insert('scale', frame=f)
    if hide is not None:
        for c in [o] + list(o.children_recursive):
            c.hide_render = hide; c.keyframe_insert('hide_render', frame=f); c.hide_viewport = hide; c.keyframe_insert('hide_viewport', frame=f)


def key_prop(o, name, v, f):
    o[name] = v; o.keyframe_insert(f'["{name}"]', frame=f)


def fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in ad.action.layers:
        for st in layer.strips:
            for bag in st.channelbags: out.extend(bag.fcurves)
    return out


def set_interp(o, kind='LINEAR', paths=None):
    for fc in fcurves(o):
        if paths and not any(p in fc.data_path for p in paths): continue
        for k in fc.keyframe_points: k.interpolation = kind


def tool_matrix(wrist, Rh, off=(0, 0, 0)):
    """world matrix of a tool that lies along his fingers: origin at the wrist + off in the hand's frame."""
    return Matrix.Translation(Vector(wrist)) @ Rh.to_4x4() @ Matrix.Translation(Vector(off))


# ---------------------------------------------------------------- cameras
def shot_cam(name, f0, f1, loc0, aim0, loc1=None, aim1=None, lens=35, fstop=2.8, focus0=None, focus1=None, lens1=None, ease=True, mids=()):
    """mids = [(u, loc, aim, focus)] extra keys at fraction u of the shot."""
    cam = wbset.camera(name, loc0, aim0, lens, fstop, focus0)
    sc = bpy.context.scene; m = sc.timeline_markers.new(name, frame=f0); m.camera = cam
    def K(f, loc, aim, focus, ln):
        cam.location = loc; wb.look_at(cam, aim); cam.data.dof.focus_distance = (Vector(focus if focus is not None else aim) - Vector(loc)).length; cam.data.lens = ln
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f); cam.data.keyframe_insert('dof.focus_distance', frame=f); cam.data.keyframe_insert('lens', frame=f)
    K(f0, loc0, aim0, focus0, lens)
    for u, loc, aim, focus in mids: K(int(round(f0 + u * (f1 - 1 - f0))), loc, aim, focus, lens)
    if loc1 is not None or aim1 is not None or lens1 is not None or focus1 is not None:
        K(f1 - 1, loc1 if loc1 is not None else loc0, aim1 if aim1 is not None else aim0, focus1 if focus1 is not None else focus0, lens1 or lens)
        if not ease: set_interp(cam, 'LINEAR'); set_interp(cam.data, 'LINEAR')
    return cam


# ---------------------------------------------------------------- the monitor
SCREEN = []          # (frame, dict(l1, l2, h1, h2, mem, dot)) sorted; the handler shows the latest entry at or before the frame


def screen(f, **kw):
    before = [s for s in SCREEN if s[0] <= f]; prev = dict(before[-1][1]) if before else dict(l1='', l2='', h1='', h2='', mem=33, dot=0.0, big='')
    prev.update(kw); SCREEN.append((f, prev)); SCREEN.sort(key=lambda x: x[0])


def type_line(i, split=None, mem=None):
    """Type lyric line i onto the monitor word by word on the sung word times. split = number of words on the first row.
    The previous prompt scrolls up into the dim history as the first word lands."""
    ln = LINES[i]; words = [w.lower().strip('.,') for w in ln['words']]; split = split if split is not None else (len(words) if len(' '.join(words)) <= 17 else (len(words) + 1) // 2)
    f0 = F(ln['wt'][0]); before = [s for s in SCREEN if s[0] <= f0]; prev = dict(before[-1][1]) if before else None
    if prev and (prev['l1'] or prev['l2']):
        done = (prev['l1'] + ' ' + prev['l2']).strip(); screen(f0, h1=prev['h2'], h2='> ' + done + '   ok')
    for n, t in enumerate(ln['wt']):
        a = ' '.join(words[:min(n + 1, split)]); b = ' '.join(words[split:n + 1]) if n + 1 > split else ''
        kw = dict(l1=a, l2=b)
        if mem is not None and n == 0: kw['mem'] = mem
        screen(F(t), **kw)


def screen_apply(scene, *a):
    if not SCREEN: return
    f = scene.frame_current; st = SCREEN[0][1]
    for kf, s in SCREEN:
        if kf <= f: st = s
        else: break
    O = D.objects; mon = O.get('MONITOR')
    if mon is None: return
    x0, y0, zt, sw, sh = mon['screen']; size = .0245; adv = size * .397
    l1 = '> ' + st['l1']; l2 = ('  ' + st['l2']) if st['l2'] else ''
    for name, body in (('SCR_l1', l1), ('SCR_l2', l2), ('SCR_h1', st['h1']), ('SCR_h2', st['h2']), ('SCR_mem', f"{int(round(st['mem']))}%"), ('SCR_big', st.get('big', ''))):
        o = O.get(name)
        if o is not None and o.data.body != body: o.data.body = body
    cur = O.get('SCR_cur')
    if cur is not None:
        row2 = bool(st['l2']); n = len(l2) if row2 else len(l1)
        cur.location.x = x0 + .016 + adv * (n + .75); cur.location.z = (zt - .158 if row2 else zt - .130) + size * .27
        blink = (f // 9) % 2 == 0 or any(0 <= f - kf < 7 for kf, _ in SCREEN)
        if st.get('mem', 0) >= 100 and st['l1'].startswith('not'): blink = True
        cur.hide_render = not blink; cur.hide_viewport = not blink
    mf = O.get('SCR_mem_fill')
    if mf is not None:
        m = max(.02, min(1.0, st['mem'] / 100)); mf.scale.x = m; mf.location.x = (x0 + sw - .074) + .030 * m
    dot = O.get('SCR_dot')
    if dot is not None:
        v = st.get('dot', 0.0); dot.hide_render = v <= 0.001; dot.hide_viewport = dot.hide_render; dot.scale = (max(v, .001),) * 3


def install_handlers(save=False):
    h = bpy.app.handlers.frame_change_pre
    for x in list(h):
        if getattr(x, '__name__', '') == 'screen_apply': h.remove(x)
    h.append(screen_apply)
    if save: bpy.context.scene['screen_json'] = json.dumps(SCREEN)


def load_screen():
    s = bpy.context.scene.get('screen_json')
    if s: SCREEN[:] = [(int(f), d) for f, d in json.loads(s)]


# ---------------------------------------------------------------- rain
class Rain:
    """A pool of drops that fall from the can's rose. Baked per frame (constant keys). Slow gravity: it is a model."""
    def __init__(self, M, n=230, g=-3.4, seed=5, name='drop', mat=None, r=(.0016, .0027), speed=(.16, .30), spread=5.5, shape=(.7, .7, 3.6)):
        random.seed(seed); self.g = g; self.drops = []; self.speed = speed; self.spread = spread; self.shape = shape
        for i in range(n):
            d = wb.sph(f'{name}{i:03d}', random.uniform(*r), (0, 0, -5), mat or M['drop'], coll='FX', seg=8); d.rotation_mode = 'QUATERNION'; d.scale = (0, 0, 0); d['lit'] = 1.0
            self.drops.append(d)

    def bake(self, tip, f0, f1, f_on, f_off, blocks, ground):
        sc = bpy.context.scene; tips = {}
        for f in range(f_on - 1, f_off + 1):
            sc.frame_set(f); mw = tip.matrix_world.copy(); tips[f] = (mw.translation.copy(), (mw.to_quaternion() @ Vector((0, 0, 1))).normalized())
        n = len(self.drops); random.seed(9); births = sorted(random.uniform(f_on, f_off) for _ in range(n))
        for i, d in enumerate(self.drops):
            b = births[i]; fb = int(b); p0, ax = tips[min(max(fb, f_on - 1), f_off)]
            sp = Vector((random.gauss(0, .013), random.gauss(0, .013), random.gauss(0, .006))); v0 = ax * random.uniform(*self.speed) + sp * self.spread; p0 = p0 + sp * .55
            dead = False
            for f in range(f0, f1):
                tau = (f - b) / FPS
                if tau < 0 or dead: d.location = (0, 0, -5); d.scale = (0, 0, 0)
                else:
                    p = p0 + v0 * tau + Vector((0, 0, .5 * self.g * tau * tau)); v = v0 + Vector((0, 0, self.g * tau)); top = ground
                    for (_, bx, by, bh) in blocks:
                        if abs(p.x - bx) < .016 and abs(p.y - by) < .016: top = max(top, IZ + bh)
                    if p.z <= top + .001: d.location = (p.x, p.y, top + .0012); d.scale = (2.4, 2.4, .35); d.rotation_quaternion = (1, 0, 0, 0); dead = True
                    else: d.location = p; d.scale = self.shape; d.rotation_quaternion = v.to_track_quat('Z', 'Y') if self.shape[2] > 1.5 else Euler((tau * 9 + i, tau * 7, i)).to_quaternion()
                d.keyframe_insert('location', frame=f); d.keyframe_insert('scale', frame=f); d.keyframe_insert('rotation_quaternion', frame=f)
            d.location = (0, 0, -5); d.scale = (0, 0, 0); d.keyframe_insert('location', frame=f1); d.keyframe_insert('scale', frame=f1)
            set_interp(d, 'CONSTANT')


# ---------------------------------------------------------------- the scene
CAR_M = None; CAN_REST = None


def build(samples=32, pct=50):
    global CAR_M, CAN_REST
    sc = wb.setup_render(samples=samples, pct=pct)
    S = wbset.build(); wbset.compositor(); M = S['M']
    arm, car = wb.append_real()
    arm.location = (0, CY, 0); bpy.context.view_layer.update()
    car.scale = (.013,) * 3; car.rotation_mode = 'QUATERNION'; car.rotation_quaternion = Euler((0, 0, rad(10))).to_quaternion(); car.location = (C.x + .009, C.y - .118, IZ + .0013); bpy.context.view_layer.update(); wb.parent(car, S['table'])
    CAR_M = car.matrix_world.copy()
    S.update(arm=arm, car=car, A=Anim(arm), rain=Rain(M), glit=Rain(M, n=110, g=-.9, seed=8, name='glit', mat=wbprops.attr_emit_mat('WB_glitfall', (.92, .97, 1.0), 40), r=(.0012, .0020), speed=(.02, .10), spread=7.0, shape=(1.3, 1.3, .15)), tweezers=wbprops.tweezers(M), brush=wbprops.brush(M), tlL=wbprops.traffic_light(M, 'TL_L'), tlR=wbprops.traffic_light(M, 'TL_R'), crown=wbprops.crown(M))
    hb = wbprops.hero_building(M, (C.x + .056, C.y - .166)); wb.parent(hb, S['table']); cl = list(hb['cells']); S['cells'] = [V(*cl[i:i + 3]) for i in range(0, len(cl), 3)]; S['herob'] = hb
    S['guys'] = []
    for n, c in enumerate(S['cells']):
        g = wbprops.guy(M, f'GUY{n:02d}', ['teal', 'cobalt', 'sage', 'butter', 'mint', 'char'][(n * 5 + n // 4) % 6]); g.rotation_mode = 'QUATERNION'; place(g, Matrix.Translation(c)); wb.parent(g, S['table']); g.scale = (0, 0, 0); S['guys'].append(g)
    S['coffee'] = wbprops.coffee(M); S['mobile'] = wbprops.mobile(M); S['gswitch'] = wbprops.gravity_switch(M, (-.345, .215)); S['tape'] = wbprops.tape(M); S['blobs'] = wbprops.water_blobs(M)
    S['strand'] = wbprops.fairy_strand(M, S['blocks']); S['glints'] = wbprops.glints(M, S['blocks'])
    for o in S['strand'] + S['glints']: wb.parent(o, S['table'])
    S['match'] = wbprops.match(M); S['match'].rotation_mode = 'QUATERNION'; place(S['match'], Matrix.Translation((0, 0, -3)))
    S['flame'] = wbprops.flame('FLAME'); S['mflame'] = wbprops.flame('MFLAME', .0026, .03); S['flame'].scale = (0, 0, 0); S['mflame'].scale = (0, 0, 0)
    S['metronome'] = wbprops.metronome(M, (.27, .278)); S['speaker'] = wbprops.speaker(M, (.415, .185)); S['runbtn'] = wbprops.run_button(M, (-.225, .287))
    S['moonL'] = wbprops.moon(M, 'MOON_A', MOON_A); S['moonR'] = wbprops.moon(M, 'MOON_B', MOON_B)
    for m_ in (S['moonL'], S['moonR']): m_.location.z += 1.2
    S['plug'] = wbprops.plug(M, rad(90)); wb.parent(S['plug'], S['table']); S['rings'] = wbprops.wave_rings(M)
    S['planner'] = wbprops.planner(M); S['cordsw'] = wbprops.cord_switch(M, (.185, .305)); S['clock'] = wbprops.clock(M)
    for o in (S['planner'], S['clock']): o.rotation_mode = 'QUATERNION'; place(o, Matrix.Translation((0, 0, -3)))
    S['tape'].rotation_mode = 'QUATERNION'; place(S['tape'], Matrix.Translation(CAR_M.translation - V(0, .004, .0013)) @ RZ(rad(10))); wb.parent(S['tape'], S['table']); S['tape'].scale = (0, 0, 0)
    for i in range(5): wb.parent(D.objects[f'potpaint{i}'], D.objects[f'pot{i}'])
    place(S['tweezers'], Matrix.Translation((.40, -.20, BZ + .0075)) @ RZ(rad(65)) @ RX(rad(90))); place(S['brush'], Matrix.Translation((.33, -.27, BZ + .006)) @ RZ(rad(110)) @ RX(rad(90)))
    for o in (S['tweezers'], S['brush'], S['crown'], S['can'], S['tlL'], S['tlR'], S['coffee'], S['mobile']): o.rotation_mode = 'QUATERNION'
    for o in (S['coffee'], S['mobile']): place(o, Matrix.Translation((0, 0, -3)))
    CAN_REST = Matrix.Translation((.47, -.15, BZ + .1245)) @ RZ(rad(160))
    place(S['can'], CAN_REST)
    for o in (S['tlL'], S['tlR']): place(o, Matrix.Translation((0, 0, -3))); wb.parent(o, S['table'])
    S['table'].rotation_mode = 'ZYX'
    sc.frame_start = F(68.0); sc.frame_end = F(156.0)
    return S


def can_pose(grip, tilt, yaw=0.0):
    """world matrix of the can and the wrist target + hand rotation that holds its handle from above. yaw + swings the rose toward the camera."""
    Mc = Matrix.Translation(grip) @ RZ(yaw) @ RY(tilt) @ RZ(math.pi); Rh = RZ(yaw) @ RY(tilt) @ RZ(rad(-90)); wrist = Vector(grip) + (Rh @ Vector((.012, 0, .050)))
    return Mc, wrist, Rh


MOON_A = V(-.390, .255, IZ + .345); MOON_B = V(-.225, .255, IZ + .345)
def TW_REST(): return Matrix.Translation((.40, -.20, BZ + .0075)) @ RZ(rad(65)) @ RX(rad(90))
def BR_REST(): return Matrix.Translation((.33, -.27, BZ + .006)) @ RZ(rad(110)) @ RX(rad(90))
def rest_L(): return (V(-.24, .25, BZ + .105), RX(rad(-62)))          # left hand on the turntable's rim
POLE = dict(pL=V(-.7, .9, .40), pR=V(.9, .8, .50))
MON_EYE = V(-.52, .02, BZ + .16)                                       # where he reads the prompt


# ---------------------------------------------------------------- shots
def shot_city(S):
    """70.6 - 72.56  Turn the dot into a city. We come out of the monitor (the 2D film dissolves into it) to find him setting
    the last piece on the tallest tower. On 'city' it lands and the windows come on from the plaza outward."""
    A = S['A']; f0 = F(70.60); fp0 = F(71.10); fp1 = F(72.30); f1 = F(72.56); fcity = F(72.08); crown = S['crown']; can = S['can']
    screen(f0 - 1, l1='', l2='', h1='', h2='', mem=33, dot=1.0); type_line(28, split=4)
    screen(F(71.9), dot=.7); screen(F(71.97), dot=.4); screen(F(72.04), dot=.15); screen(fcity, dot=0.0)
    # the tallest tower: the block nearest (-.05, +.05) from the plaza
    blk = min(S['blocks'], key=lambda b: (b[1] - (C.x - .050)) ** 2 + (b[2] - (C.y + .050)) ** 2); top = V(blk[1], blk[2], IZ + blk[3])
    Mdown = Matrix.Translation(top); h = crown['h']
    def Lh(p_base, tilt=0): return (Vector(p_base) + V(.0, .012, h + .060), RX(rad(-18 + tilt)))      # pinch the mast from above-behind
    up = top + V(-.004, .020, .075)
    Mc, wr, Rh = can_pose(V(.300, .245, BZ + .285), rad(-4), rad(-25))
    A.k(f0, lids=0.0, brow=0.0, fL=(.75, .9), fR=(1.15, .9), **POLE)
    A.lean0 = 14; A.pose(f0, L=Lh(up), R=(wr, Rh), head=(24, -6, 0)); A.k(f0, look=top + V(0, 0, .02))
    place(can, Mc); A.attach(can, 'hand_R', f0, f1)
    place(crown, Matrix.Translation(up)); A.attach(crown, 'hand_L', f0, fcity + 1)
    A.pose(fcity - 12, L=Lh(up + V(.004, -.014, -.030)))
    A.pose(fcity, L=Lh(top)); A.k(fcity, fL=(.75, .9))                          # it lands on the word
    A.k(fcity + 4, fL=(.25, .2)); A.pose(fcity + 5, L=Lh(top + V(0, .004, .004), 6))   # let go
    A.pose(fcity + 13, L=rest_L()); A.k(fcity + 13, fL=(.15, .15))
    key_w(crown, fcity + 1, Mdown); wb.parent(crown, S['table'])
    # eyes to the monitor for the next prompt, head follows, the can starts up
    A.k(fcity + 7, look=MON_EYE); A.pose(fcity + 11, head=(24, -6, 0)); A.pose(f1 - 1, head=(14, -30, 3))
    Mc2, wr2, Rh2 = can_pose(V(.262, .125, IZ + .252), rad(-6), rad(-22)); A.pose(fcity + 8, R=(wr, Rh)); A.pose(f1 - 1, R=(wr2, Rh2))
    A.hold(f1 - 1); A.bake_held(); A.bake_looks(f0, f1)
    # the windows come on, plaza outward
    for o, bx, by, bh in S['blocks']:
        d = math.hypot(bx - C.x, by - C.y); fa = fcity + int(d * 85)
        if 'lit' not in o.keys(): continue
        key_prop(o, 'lit', 0.0, f0); key_prop(o, 'lit', 0.0, fa); key_prop(o, 'lit', 1.0, fa + 7)
        ch = D.objects.get('step' + o.name[3:])
        if ch is not None: key_prop(ch, 'lit', 0.0, f0); key_prop(ch, 'lit', 0.0, fa + 2); key_prop(ch, 'lit', 1.0, fa + 9)
    for o in crown.children:
        if 'lit' in o.keys(): key_prop(o, 'lit', 0.0, f0); key_prop(o, 'lit', 0.0, fcity + 2); key_prop(o, 'lit', 1.0, fcity + 9)
    # camera: on the glass, then back and round to the master
    mon = D.objects['MONITOR']; x0, y0, zt, sw, sh = mon['screen']; yaw = mon.rotation_euler.z; n = V(math.sin(yaw), -math.cos(yaw), 0)
    ctr = mon.location + (RZ(yaw) @ (V(x0 + sw / 2, y0, zt - sh / 2) - mon.location)); d0 = sw * 50 / 36 * 1.0
    p0 = ctr + n * d0; pw = V(0, -1.62, .70); aw = V(0, .22, .60)
    cam = shot_cam('C_city', f0, f1, p0, ctr, lens=50, fstop=4.0, focus0=ctr)
    def K(f, loc, aim, focus, lens):
        cam.location = loc; wb.look_at(cam, aim); cam.data.dof.focus_distance = (Vector(focus) - Vector(loc)).length; cam.data.lens = lens
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f); cam.data.keyframe_insert('dof.focus_distance', frame=f); cam.data.keyframe_insert('lens', frame=f)
    K(fp0, p0, ctr, ctr, 50)
    for u in (.2, .4, .6, .8, 1.0):
        e = smooth(u) ; e2 = 1 - (1 - u) ** 2.2
        K(int(fp0 + u * (fp1 - fp0)), p0.lerp(pw, e2), ctr.lerp(aw, smooth(min(1, u * 1.25))), ctr.lerp(V(0, .25, .62), e), 50 + (35 - 50) * e)
    K(f1 - 1, pw + V(0, .03, 0), aw, V(0, .25, .62), 35)


def shot_rain(S):
    """72.56 Make it rain on just one side. B1 low hero: he tips the can on 'rain'. B2 from the dry side's far corner: the rain
    walks down the east side between the lens and his face."""
    A = S['A']; can = S['can']; tip = D.objects['CAN_TIP']; f0 = F(72.56); fc = F(73.66); f1 = F(74.88); fr = F(72.88)
    type_line(29, split=4, mem=36); A.lean0 = 26
    g0 = V(.262, .125, IZ + .252); g1 = V(.262, .110, IZ + .234); g2 = V(.266, .085, IZ + .230)
    def canK(f, grip, tilt_deg, yaw_deg=0, **kw):
        Mc, wrist, Rh = can_pose(grip, rad(tilt_deg), rad(yaw_deg)); A.pose(f, R=(wrist, Rh), **kw); return Mc
    A.k(f0, lids=0.0, brow=0.0, fR=(1.15, .9), fL=(.15, .15), look=(.13, .12, IZ + .05), **POLE)
    Mc = canK(f0, g0, -6, -22, L=rest_L(), head=(26, 4, 2)); place(can, Mc); A.attach(can, 'hand_R', f0, f1)
    canK(fr - 5, g0 + V(0, 0, .012), -2, -22)                         # anticipation: a small lift back
    canK(fr + 3, g1, -43, -22); canK(fr + 7, g1, -37, -22); canK(fr + 12, g1, -39, -20)   # tip, a touch past, settle
    A.pose(fr + 8, head=(31, 5, 2))
    A.k(fr - 6, look=(.12, .14, IZ + .09)); A.k(fr + 4, look=(.12, .14, IZ + .04))
    # B2: he walks the rain down the east side, and stops dead at the kerb
    canK(fc, g1, -39, -16); canK(f1 - 9, g2, -39, 40); canK(f1 - 4, g2, -38, 37)
    A.pose(f1 - 6, head=(33, 9, 2))
    A.k(fc, look=((.12, .12, IZ + .04), 3)); A.k(fc + 2, look=((.13, -.02, IZ + .04), f1 - 12 - fc))
    A.hold(f1 - 1); A.bake_held(); A.bake_looks(f0, f1)
    S['rain'].bake(tip, f0, f1, fr + 3, f1 - 1, S['blocks'], IZ + .001)
    shot_cam('C_rain_low', f0, fc, (-.06, -.66, IZ + .043), (.03, .30, IZ + .255), loc1=(-.05, -.63, IZ + .045), lens=26, fstop=4.0, focus0=(.06, .08, IZ + .12))
    shot_cam('C_rain_side', fc, f1, (.53, -.40, IZ + .10), (.05, .14, IZ + .215), loc1=(.50, -.38, IZ + .10), lens=28, fstop=3.2, focus0=(.13, .06, IZ + .07))


def shot_porsche(S):
    """74.88 Purple Porsche: long tweezers set the toy GT3 RS on the boulevard on 'Porsche'. 75.72 yellow brakes: a brush
    puts the yellow on a caliper on 'brakes'."""
    A = S['A']; car = S['car']; tw = S['tweezers']; br = S['brush']; f0 = F(74.88); fland = F(75.28); fc = F(75.72); fdab = F(76.08); f1 = F(76.48)
    type_line(30, split=2, mem=39)
    key_w(S['can'], f0, CAN_REST); key_w(car, F(70.6), None, hide=True); key_w(car, f0, None, hide=False)
    for o in [car] + list(car.children_recursive): set_interp(o, 'CONSTANT', ['hide'])
    roof = CAR_M.translation + V(0, 0, .0165); L = tw['len']
    def grip(tipp, f, **kw):
        """right hand holds the tweezers like a pen; the tip is at tipp."""
        Rh = RZ(rad(-24)) @ RX(rad(-52)); d = Rh @ V(0, 0, -1); wrist = Vector(tipp) - d * (L + .035)
        A.pose(f, R=(wrist, Rh), **kw); return tool_matrix(wrist, Rh, (0, 0, -.035))
    A.k(f0, lids=0.0, brow=0.0, fR=(.9, .8), fL=(.15, .15), look=roof + V(0, 0, .05), **POLE)
    A.lean0 = 28; Mt = grip(roof + V(.02, .03, .075), f0, L=rest_L(), head=(36, 0, 0))
    place(tw, Mt); A.attach(tw, 'hand_R', f0, fc)
    grip(roof + V(.004, .006, .022), fland - 5); grip(roof, fland)                 # down, slowing, wheels touch on the word
    grip(roof, fland + 4); grip(roof + V(.01, .02, .03), fland + 9); grip(roof + V(.03, .06, .08), fc - 1)
    A.k(fland - 8, look=roof); A.k(fland + 8, look=roof + V(0, 0, .0))
    A.hold(fc - 1)
    # the car rides the tweezers down, then it is the table's
    place(car, CAR_M); A.attach(car, 'hand_R', f0, fland + 1, at=fland); A.bake_held()
    key_w(car, fland + 1, CAR_M); key_w(car, fland + 2, CAR_M @ Matrix.Translation((0, 0, -.045))); key_w(car, fland + 5, CAR_M)   # the suspension takes it (car units)
    key_w(tw, fc, TW_REST())
    A.bake_looks(f0, fc)
    shot_cam('C_porsche', f0, fc, (-.17, -.40, IZ + .21), CAR_M.translation + V(.0, .01, .012), loc1=(-.15, -.37, IZ + .19), lens=50, fstop=2.8, focus0=CAR_M.translation)
    # the caliper: red until the brush touches it
    cal = D.materials['Caliper1Mtl'].node_tree.nodes.get('Principled BSDF').inputs['Base Color']
    for f, c in ((F(70.6), (.45, .006, .011, 1)), (fdab + 1, (.45, .006, .011, 1)), (fdab + 2, (1.0, .72, .0, 1))): cal.default_value = c; cal.keyframe_insert('default_value', frame=f)
    bpy.context.scene.frame_set(fc); bpy.context.view_layer.update(); wheel = D.objects['wheel_piv_FL'].matrix_world.translation.copy()
    S['wheel'] = wheel; out = (wheel - CAR_M.translation); out.z = 0; out.normalize()
    side = RZ(rad(90)) @ out; dirn = (-out * .62 + V(0, 0, -.55) + side * .50).normalized()        # the brush comes in from the lens side, above
    tipp = wheel + out * .0022 + V(0, 0, .0008); Rb = dirn.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    def brK(f, p): key_w(br, f, Matrix.Translation(Vector(p) - (Rb @ V(0, 0, -1)) * br['len']) @ Rb)
    brK(fc, tipp - dirn * .05); brK(fdab - 3, tipp - dirn * .006); brK(fdab, tipp); brK(fdab + 3, tipp + V(0, 0, -.0012)); brK(fdab + 6, tipp + V(0, 0, .0006)); brK(f1 - 1, tipp - dirn * .04)
    key_w(br, f1, BR_REST()); key_w(br, fc - 1, BR_REST()); set_interp(br, 'BEZIER')
    camp = wheel + out * .060 + V(0, 0, .006) + side * (-.022)
    shot_cam('C_brakes', fc, f1, camp, wheel + V(0, 0, .001), loc1=camp - out * .010, lens=70, fstop=6.3, focus0=wheel + out * .003)
    wl = wb.light('wheel_kiss', 'POINT', wheel + out * .03 + V(0, 0, .012), .012, (1.0, .9, .8), .004); wl.data.volume_factor = 0
    A.pose(fc, L=rest_L(), R='relax', head=(30, 0, 0)); A.hold(f1 - 1)


def shot_lights(S):
    """76.48 Make the traffic lights collide: he walks two little traffic lights together behind the dot; on 'collide' they
    bonk, lean on each other and show every colour at once. Then the first look at us."""
    A = S['A']; a, b = S['tlL'], S['tlR']; f0 = F(76.48); fhit = F(77.60); f1 = F(78.48); y = C.y + .040; z = IZ + .0012; h = a['h']
    type_line(31, split=3, mem=42)
    SC = 1.9
    def M(x, lean=0): return Matrix.Translation((x, y, z)) @ RY(rad(lean)) @ Matrix.Scale(SC, 4)
    x0 = .090; x1 = .0058 * SC; h = h * SC
    for o in (a, b): o.scale = (SC,) * 3
    for o, sg in ((a, -1), (b, 1)):
        key_w(o, f0 - 1, M(sg * x0)); key_w(o, f0 + 6, M(sg * x0)); key_w(o, fhit - 1, M(sg * (x1 + .004))); key_w(o, fhit, M(sg * x1, -sg * 0))
        key_w(o, fhit + 3, M(sg * (x1 + .003), sg * 9)); key_w(o, fhit + 7, M(sg * x1, -sg * 11)); key_w(o, fhit + 11, M(sg * x1, -sg * 8)); key_w(o, f1 - 1, M(sg * x1, -sg * 8))
        wb_name = o.name
        for w in 'gyr': wbprops.set_lamp(wb_name, w, w == ('g' if sg < 0 else 'r'), f0); wbprops.set_lamp(wb_name, w, w == ('g' if sg < 0 else 'r'), fhit); wbprops.set_lamp(wb_name, w, True, fhit + 1)
        for w in 'gyr': set_interp(D.materials[f'{wb_name}_{w}'].node_tree, 'CONSTANT')
    def hand(s, x, lift=0, out=0):
        sg = -1 if s == 'L' else 1; return {s: (V(sg * (x + .034 + out), y + .006, z + .118 + lift), RY(rad(sg * 5)))}
    A.k(f0, lids=0.0, brow=0.0, fL=(.05, .3), fR=(.05, .3), look=(0, y, z + .03), **POLE)
    A.lean0 = 30; A.pose(f0, **hand('L', x0, 0, .012), **hand('R', x0, 0, .012), head=(42, 0, 0)); A.pose(f0 + 6, **hand('L', x0), **hand('R', x0))
    A.pose(fhit - 1, **hand('L', x1 + .004), **hand('R', x1 + .004)); A.pose(fhit + 3, **hand('L', x1 + .004, 0, .004), **hand('R', x1 + .004, 0, .004))
    A.pose(fhit + 12, **hand('L', x1, .02, .05), **hand('R', x1, .02, .05)); A.pose(f1 - 1, **hand('L', x1, .03, .07), **hand('R', x1, .03, .07))
    # the look at us (stare 1): eyes first, then the head
    fst = fhit + 9; lens = V(0, -.86, IZ + .22)
    A.k(fst, look=lens); A.pose(fst + 4, head=(42, 0, 0)); A.pose(fst + 11, head=(20, 0, 0)); A.k(fst, lids=0.0); A.k(fst + 6, lids=.14)
    A.hold(f1 - 1); A.bake_looks(f0, f1, up=1.3)
    shot_cam('C_lights', f0, fst + 2, (-.01, -.33, IZ + .25), (0, y + .004, IZ + .045), loc1=(-.008, -.30, IZ + .235), lens=50, fstop=5.6, focus0=(0, y, z + .05))
    bpy.context.scene.frame_set(f1 - 2); bpy.context.view_layer.update(); eye = (D.objects['eye_L'].matrix_world.translation + D.objects['eye_R'].matrix_world.translation) / 2
    shot_cam('C_lights_stare', fst + 2, f1, lens, eye + V(0, 0, -.06), loc1=lens + V(0, .03, 0), lens=50, fstop=2.0, focus0=eye)


def tw_matrix(tw, tip, d):
    d = Vector(d).normalized(); return Matrix.Translation(Vector(tip) - d * tw['len']) @ d.to_track_quat('-Z', 'Y').to_matrix().to_4x4()


def watch(A, f0, f1, target, head=(34, 0, 0), lean0=22):
    """he stands over the city with his hands on the rim and watches something (for the inserts)."""
    A.lean0 = lean0; A.k(f0, lids=0.0, brow=0.0, fL=(.15, .15), fR=(.15, .15), look=target, **POLE)
    A.pose(f0, L=rest_L(), R=(V(.24, .25, BZ + .105), RX(rad(-62))), head=head); A.hold(f1 - 1); A.bake_looks(f0, f1)


def shot_guys(S):
    """78.48 Put a little guy in every window. Tweezers seat one peg person at his desk on 'guy'; on 'every window' the rest
    of the block fills up, one a frame."""
    A = S['A']; tw = S['tweezers']; guys = S['guys']; cells = S['cells']; f0 = F(78.48); fg = F(78.96); fc = F(79.42); f1 = F(80.32); hi = 13; hero = guys[hi]; cell = cells[hi]
    type_line(32, split=4, mem=45)
    for g in guys: key_w(g, F(70.6), scale=0)
    d = V(-.42, .50, -.62).normalized(); head = V(0, 0, .0068)
    def tipK(f, p, guy=True):
        key_w(tw, f, tw_matrix(tw, Vector(p) + head, d))
        if guy: key_w(hero, f, Matrix.Translation(p))
    key_w(tw, f0 - 1, TW_REST()); key_w(hero, f0 - 1, scale=0); key_w(hero, f0, scale=1)
    tipK(f0, cell + V(.030, -.050, .040)); tipK(fg - 5, cell + V(.003, -.016, .004)); tipK(fg, cell); tipK(fg + 4, cell)
    tipK(fg + 8, cell + V(.006, -.008, .008), False); tipK(fc - 1, cell + V(.03, -.05, .05), False); key_w(tw, fc, TW_REST())
    set_interp(hero, 'CONSTANT', ['scale'])
    random.seed(12); order = [i for i in range(16) if i != hi]; random.shuffle(order); fe = F(79.50)
    for k, i in enumerate(order):
        fa = fe + int(k * .55); key_w(guys[i], fa - 1, scale=0); key_w(guys[i], fa + 2, scale=1.25); key_w(guys[i], fa + 4, scale=1.0)
    ctr = cells[5].lerp(cells[10], .5) + V(.003, -.012, .006)
    shot_cam('C_guy', f0, fc, cell + V(-.012, -.115, .004), cell + V(.002, 0, .002), loc1=cell + V(-.010, -.105, .004), lens=70, fstop=5.6, focus0=cell + V(0, -.004, .004))
    shot_cam('C_guys', fc, f1, ctr + V(-.03, -.20, .02), ctr, loc1=ctr + V(-.025, -.17, .018), lens=70, fstop=8, focus0=ctr + V(0, .010, 0))
    watch(A, f0, f1, cell)


def type_anim(guys, f0, f1, rate, amp=.0007, shake=0.0, seed=1):
    """arms drum on the keys: rate = frames per stroke."""
    random.seed(seed)
    for gi, g in enumerate(guys):
        arms = [o for o in g.children if '_arm' in o.name]; ph = random.randint(0, 3)
        for k, a in enumerate(arms):
            z0 = a.get('z0', None)
            if z0 is None: a['z0'] = a.location.z; z0 = a.location.z
            for f in range(f0, f1):
                up = ((f + ph + k * max(1, rate // 2)) // max(1, rate)) % 2 == 0
                a.location.z = z0 + (amp if up else -amp * .4); a.keyframe_insert('location', index=2, frame=f)
            set_interp(a, 'CONSTANT' if rate <= 1 else 'LINEAR', ['location'])


def shot_wired(S):
    """80.32 Make him type like he's wired. They start typing on 'type'; on 'wired' the tweezers put a coffee on his desk and he doubles his speed."""
    A = S['A']; tw = S['tweezers']; guys = S['guys']; cells = S['cells']; cof = S['coffee']; f0 = F(80.32); ft = F(80.88); fw = F(81.84); f1 = F(82.40); hi = 13; cell = cells[hi]
    type_line(33, split=3, mem=48)
    type_anim(guys, ft, fw + 2, 3); type_anim([guys[hi]], fw + 2, f1, 1, amp=.0009); type_anim([g for i, g in enumerate(guys) if i != hi], fw + 2, f1, 3)
    desk = cell + V(.0056, -.0034, .0036); d = V(-.42, .50, -.62).normalized()
    def tipK(f, p, cup=True):
        key_w(tw, f, tw_matrix(tw, Vector(p) + V(0, 0, .0022), d))
        if cup: key_w(cof, f, Matrix.Translation(p))
    key_w(tw, fw - 14, TW_REST()); key_w(cof, fw - 14, Matrix.Translation((0, 0, -3)))
    tipK(fw - 13, desk + V(.03, -.05, .04)); tipK(fw - 4, desk + V(.002, -.006, .004)); tipK(fw, desk); tipK(fw + 3, desk)
    tipK(fw + 7, desk + V(.006, -.008, .008), False); tipK(f1 - 1, desk + V(.03, -.05, .05), False); key_w(tw, f1, TW_REST())
    for o in (tw, cof): set_interp(o, 'BEZIER')
    hero = guys[hi]
    for f in range(fw + 3, f1):      # the caffeine reaches his whole body
        key_w(hero, f, Matrix.Translation(cell + V(0, 0, .0003 * ((f % 2) * 2 - 1))))
    key_w(hero, f1, Matrix.Translation(cell))
    wb.parent(cof, S['table'])
    shot_cam('C_wired', f0, f1, cell + V(-.004, -.070, .005), cell + V(.003, 0, .0035), loc1=cell + V(-.002, -.058, .005), lens=85, fstop=8.0, focus0=cell + V(0, -.003, .004))
    watch(A, f0, f1, cell)


def shot_pigeons(S):
    """82.40 Make the pigeons fly in circles: he twirls a little mobile of paper pigeons over the city, on a rod, and his eyes go
    round with them. 84.08 Now a little higher, higher: two notches up."""
    A = S['A']; mob = S['mobile']; f0 = F(82.40); fcirc = F(83.60); fh1 = F(84.56); fh2 = F(84.90); f1 = F(86.86); hub0 = V(.005, .045, IZ + .355); rod = mob['rod']
    type_line(34, split=3, mem=51); type_line(35, split=3, mem=54)
    W = V(.150, .262, IZ + .300)
    def handK(f, hub, **kw):
        d = (Vector(hub) - W).normalized(); wrist = Vector(hub) - d * (rod + .040); Rh = d.to_track_quat('-Z', 'Y').to_matrix().to_4x4() @ RZ(rad(-60))
        A.pose(f, R=(wrist, Rh), **kw); return tool_matrix(wrist, Rh, (0, 0, -.040))
    A.lean0 = 8; A.k(f0, lids=.14, brow=0.0, fL=(.15, .15), fR=(1.2, 1.0), **POLE)
    Mm = handK(f0, hub0 + V(0, .03, .05), L=rest_L(), head=(12, 2, 0)); place(mob, Mm); A.attach(mob, 'hand_R', f0, f1)
    handK(f0 + 8, hub0)
    for f in range(f0 + 8, fh1 - 2, 5):                               # a small stirring circle
        a = (f - f0) * .42; handK(f, hub0 + V(.006 * math.cos(a), .006 * math.sin(a), 0))
    handK(fh1 - 3, hub0); handK(fh1 + 2, hub0 + V(0, 0, .034)); handK(fh2 - 3, hub0 + V(0, 0, .034)); handK(fh2 + 2, hub0 + V(0, 0, .066)); handK(f1 - 1, hub0 + V(0, 0, .066))
    A.pose(fh2 + 6, head=(4, 2, 0)); A.hold(f1 - 1); A.bake_held()
    # the spin: up to speed by 'circles', the pigeons swing out as it goes
    hub = D.objects['MOB_HUB']; ang = 0.0; birds = [D.objects[f'MOB_ARM{i}'] for i in range(mob['n'])]; sc = bpy.context.scene
    for f in range(f0, f1):
        sp = smooth((f - f0 - 6) / (fcirc - f0 - 6)) * 1.0; ang += sp * rad(9.5); sc.frame_set(f)
        hub.location = mob.matrix_world @ V(0, 0, -rod); hub.rotation_euler = (0, 0, ang); hub.keyframe_insert('location', frame=f); hub.keyframe_insert('rotation_euler', frame=f)
        for i, b in enumerate(birds):
            b.rotation_euler = (0, .16 + .62 * sp + .05 * math.sin(f * .31 + i), b['az']); b.keyframe_insert('rotation_euler', frame=f)
            for k in (0, 1):
                w = D.objects[f'bird{i}_wing{k}']; w.rotation_euler = (0, (1 if k else -1) * (.25 + .55 * math.sin(f * 1.3 + i * 1.7)), 0); w.keyframe_insert('rotation_euler', frame=f)
    set_interp(hub, 'LINEAR'); hub.location = (0, 0, -3); hub.keyframe_insert('location', frame=f0 - 1)
    for f in range(f0, f1, 2):
        sc.frame_set(f); A.k(f, look=(D.objects['MOB_BIRD0'].matrix_world.translation.copy(), 2))
    A.bake_looks(f0, f1)
    sc.frame_set(fcirc); bpy.context.view_layer.update()
    print('[pigeons] hub', [round(x, 3) for x in hub.matrix_world.translation], 'bird0', [round(x, 3) for x in D.objects['MOB_BIRD0'].matrix_world.translation], 'hand', [round(x, 3) for x in A.R.bone_world('hand_R').translation], 'want hub', [round(x, 3) for x in hub0])
    shot_cam('C_pigeons', f0, f1, (-.10, -.66, IZ + .06), (0, .12, IZ + .30), loc1=(-.07, -.60, IZ + .07), aim1=(0, .12, IZ + .33), lens=26, fstop=4.0, focus0=(0, .0, IZ + .3))


# ---------------------------------------------------------------- zero g
def tumble(M0, rise, t, seed, drift=.03):
    """where a loose thing is t seconds after it lets go: it rises `rise`, drifts a little and turns slowly."""
    rnd = random.Random(seed); ax = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-.6, .6))).normalized(); rate = rnd.uniform(.25, .7); dr = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * drift
    u = 1 - math.exp(-t / 1.1); loc, q, sc = M0.decompose()
    p = loc + Vector((0, 0, rise * u + .006 * math.sin(t * 1.7 + seed))) + dr * u
    return Matrix.Translation(p) @ (Quaternion(ax, rate * t * (.4 + .6 * u)) @ q).to_matrix().to_4x4()


def float_bake(items, f_on, f_off, land=True, step=2, M_land=None):
    """items = [(obj, rise, delay_frames, seed)]. They let go at f_on + delay, hang until f_off, then drop and settle."""
    sc = bpy.context.scene
    for o, rise, delay, seed in items:
        o.rotation_mode = 'QUATERNION'; sc.frame_set(f_on); bpy.context.view_layer.update(); M0 = o.matrix_world.copy(); s0 = o.scale.copy(); fs = f_on + delay; last = None; ML = M_land or M0
        def K(f, M):
            nonlocal last
            o.matrix_world = M; o.scale = s0; q = o.rotation_quaternion.copy()
            if last is not None and q.dot(last) < 0: q.negate(); o.rotation_quaternion = q
            last = q.copy(); o.keyframe_insert('location', frame=f); o.keyframe_insert('rotation_quaternion', frame=f)
        K(f_on - 1, M0); K(fs, M0)
        for f in list(range(fs + step, f_off, step)) + [f_off]: K(f, tumble(M0, rise, (f - fs) / FPS, seed))
        if land:
            Mh = tumble(M0, rise, (f_off - fs) / FPS, seed); n = 5 + seed % 3
            for i in range(1, n + 1):
                u = (i / n) ** 2; K(f_off + i, Matrix.Translation(Mh.translation.lerp(ML.translation, u)) @ Mh.to_quaternion().slerp(ML.to_quaternion(), u).to_matrix().to_4x4())
            lz = Matrix.Translation((0, 0, .004 + .001 * (seed % 4)))
            K(f_off + n + 3, lz @ ML); K(f_off + n + 6, ML)


def loose_things(S):
    """everything on the bench that is not glued down."""
    out = []; O = D.objects; rnd = random.Random(8)
    for n in [f'spare{i}' for i in range(24)] + [f'pot{i}' for i in range(5)] + ['pencil', 'rule', 'CAN', 'TWEEZERS', 'BRUSH', 'TL_L', 'TL_R', 'COFFEE']:
        if n in O: out.append((O[n], rnd.uniform(.10, .46), rnd.randint(0, 22), rnd.randint(1, 999)))
    for g in S['guys']: out.append((g, rnd.uniform(.03, .12), rnd.randint(8, 26), rnd.randint(1, 999)))
    return out


def shot_gravity(S):
    """86.86 Turn off gravity: his finger throws the GRAVITY switch on 'off'. The pigeons' threads go slack and they drift up.
    89.06 Just for the birds."""
    A = S['A']; mob = S['mobile']; f0 = F(86.86); foff = F(87.35); fc = F(87.92); f1 = F(90.53); lev = D.objects['GS_LEVER']; lp = lev.matrix_world.translation.copy()
    type_line(36, mem=57); type_line(37, mem=60)
    key_w(lev, f0 - 1); lev.rotation_euler = (-.5, 0, 0); lev.keyframe_insert('rotation_euler', frame=foff - 2); lev.rotation_euler = (.5, 0, 0); lev.keyframe_insert('rotation_euler', frame=foff + 1)
    led = D.materials['GS_led'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength']
    for f, v in ((foff, 7.0), (foff + 1, 0.0)): led.default_value = v; led.keyframe_insert('default_value', frame=f)
    set_interp(D.materials['GS_led'].node_tree, 'CONSTANT')
    # the left index finger does it; the right hand keeps the rod
    Rf = RX(rad(-40)); tipv = Rf @ V(0, -.030, -.092)                                   # wrist -> index fingertip in this hand pose
    def fing(f, tip, **kw): A.pose(f, L=(Vector(tip) - tipv, Rf), **kw)
    A.lean0 = 12; A.k(f0, lids=0.0, brow=0.0, fL=(1.2, .9, {'index': -.1}), look=lp + V(0, 0, .03))
    on_tip = lp + V(0, .018, .034); off_tip = lp + V(0, -.016, .034)
    fing(f0, on_tip + V(0, .03, .05), head=(34, -22, 0)); fing(foff - 4, on_tip + V(0, .010, .004)); fing(foff, off_tip + V(0, .006, 0)); fing(foff + 3, off_tip + V(0, .012, .01)); fing(foff + 10, off_tip + V(0, .04, .06))
    A.pose(fc, L=rest_L()); A.k(fc, fL=(.15, .15))
    # birds: free copies take over from the threads at the flick
    hub = D.objects['MOB_HUB']; n = mob['n']; sc = bpy.context.scene; hub0 = V(.005, .045, IZ + .355 + .066); rod = mob['rod']; W = V(.150, .262, IZ + .300)
    d = (hub0 - W).normalized(); wrist = hub0 - d * (rod + .040); Rh = d.to_track_quat('-Z', 'Y').to_matrix().to_4x4() @ RZ(rad(-60))
    A.k(f0, fR=(1.2, 1.0)); A.pose(f0, R=(wrist, Rh)); place(mob, tool_matrix(wrist, Rh, (0, 0, -.040))); A.attach(mob, 'hand_R', f0, f1); A.hold(f1 - 1); A.bake_held()
    sc.frame_set(f0 - 1); ang = hub.rotation_euler.z
    for f in range(f0, f1):
        sp = 1.0 if f < foff else max(0.0, 1 - (f - foff) / 40); ang += sp * rad(9.5); sc.frame_set(f)
        hub.location = mob.matrix_world @ V(0, 0, -rod); hub.rotation_euler = (0, 0, ang); hub.keyframe_insert('location', frame=f); hub.keyframe_insert('rotation_euler', frame=f)
        for i in range(n):
            b = D.objects[f'MOB_ARM{i}']; b.rotation_euler = (0, .16 + .62 * sp, b['az']); b.keyframe_insert('rotation_euler', frame=f)
            for k in (0, 1):
                w = D.objects[f'bird{i}_wing{k}']; w.rotation_euler = (0, (1 if k else -1) * (.25 + .55 * math.sin(f * (1.3 if f < foff else .45) + i * 1.7)), 0); w.keyframe_insert('rotation_euler', frame=f)
    set_interp(hub, 'LINEAR')
    # threads let go a few frames after the switch: each bird becomes a free object and rises
    frel = foff + 4; sc.frame_set(frel); bpy.context.view_layer.update(); S['freebirds'] = []
    for i in range(n):
        be = D.objects[f'MOB_BIRD{i}']; fb = wb.empty(f'FREEBIRD{i}', (0, 0, 0), 'PROPS'); fb.rotation_mode = 'QUATERNION'; place(fb, be.matrix_world.copy())
        for ch in list(be.children): ch.parent = fb
        th = D.objects[f'mob_thread{i}']; key_w(th, F(70.6), hide=False); key_w(th, frel, hide=True)
        S['freebirds'].append(fb)
    # before the release the free birds simply ride where the threads would hold them
    for i, fb in enumerate(S['freebirds']):
        be = D.objects[f'MOB_BIRD{i}']
        for f in range(F(82.40), frel + 1):
            sc.frame_set(f); fb.matrix_world = be.matrix_world; fb.keyframe_insert('location', frame=f); fb.keyframe_insert('rotation_quaternion', frame=f)
        key_w(fb, F(82.40) - 1, Matrix.Translation((0, 0, -3)))
    float_bake([(fb, .13 + .03 * i, 0, 31 + i * 7) for i, fb in enumerate(S['freebirds'])], frel, F(94.70), land=False)
    A.k(fc, look=(V(0, .02, IZ + .30), 3))
    for f in range(fc + 4, f1, 3):
        sc.frame_set(f); A.k(f, look=(S['freebirds'][0].matrix_world.translation.copy(), 3))
    A.k(F(89.06), look=MON_EYE); A.k(F(89.06) + 14, look=(S['freebirds'][0].matrix_world.translation.copy(), 3))
    A.pose(fc, head=(8, 0, 0)); A.pose(f1 - 1, head=(-2, 4, 0)); A.hold(f1 - 1); A.bake_looks(f0, f1)
    shot_cam('C_switch', f0, fc, lp + V(-.07, -.24, .21), lp + V(-.016, 0, .008), loc1=lp + V(-.06, -.21, .20), lens=60, fstop=4.0, focus0=lp)
    shot_cam('C_birds', fc, f1, (-.10, -.66, IZ + .06), (0, .12, IZ + .33), loc1=(-.08, -.62, IZ + .06), aim1=(0, .12, IZ + .40), lens=26, fstop=4.0, focus0=(0, .0, IZ + .35))


def shot_everybody(S):
    """90.53 Now for everybody: everything on the bench that is not glued down lets go, him included."""
    A = S['A']; f0 = F(90.53); fe = F(91.27); f1 = F(92.25); fland = F(94.70); sc = bpy.context.scene
    type_line(38, mem=63)
    float_bake(loose_things(S), f0, fland)
    for i, b in enumerate(S['blobs']):                                 # the ocean lets a few beads of itself go
        fa = f0 + 6 + i * 2; sc.frame_set(f0); M0 = Matrix.Translation(b.matrix_world.translation)
        key_w(b, fa - 1, scale=0); key_w(b, fa + 8, scale=1)
        for f in range(fa, fland + 1, 2): key_w(b, f, tumble(M0, .05 + .012 * i, (f - fa) / FPS, 60 + i, drift=.015))
        key_w(b, fland + 5, M0, scale=1); key_w(b, fland + 7, scale=0)
    # him: the rod drifts out of his hand, his feet leave the floor on 'everybody'
    A.lean0 = 6; A.k(f0, lids=0.0, brow=0.0, fL=(.15, .15), fR=(.3, .3), look=(.3, -.1, BZ + .2))
    def arms(f, up):
        for s, sg in (('L', -1), ('R', 1)):
            sh = A.shoulder(s, 0, 0, rad(4), 0); A.k(f, **{'h' + s: (sh + V(sg * (.05 + .10 * up), -.06, -.24 + .17 * up), RY(rad(sg * 30 * up)) @ RX(rad(-12)))})
    A.rig(f0, (0, 0, 0)); A.pose(f0, L='relax', R='relax', head=(10, 8, 0)); A.k(f0, hips=(0, 0, 0), spine=(rad(4), 0, 0), feet=(0, 0)); arms(f0, 0)
    A.rig(fe - 6, (0, 0, 0)); arms(fe, .1); A.hold(fe - 6, 'feet')
    A.rig(f1 - 1, (0, 0, .085)); arms(f1 - 1, .8); A.k(f1 - 1, spine=(rad(-3), 0, 0), feet=(.03, .02, rad(22)))
    A.k(fe + 6, look=(-.3, -.2, BZ + .3)); A.k(fe + 16, look=(.35, -.2, BZ + .45))
    A.hold(f1 - 1); A.bake_looks(f0, f1)
    mob = S['mobile']; sc.frame_set(f0); float_bake([(mob, .10, 4, 77)], f0, fland, M_land=Matrix.Translation((-.36, -.24, BZ + .006)) @ RZ(rad(80)) @ RX(rad(90)))
    hub = D.objects['MOB_HUB']; rod = mob['rod']
    for f in range(f0, fland + 12):
        sc.frame_set(f); hub.location = mob.matrix_world @ V(0, 0, -rod); hub.keyframe_insert('location', frame=f)
    shot_cam('C_everybody', f0, f1, (0, -1.62, .66), (0, .22, .60), loc1=(0, -1.50, .67), aim1=(0, .22, .64), lens=35, fstop=2.0, focus0=(0, .25, .62))


def shot_carback(S):
    """92.25 Wait, put the car back first. In the silence his hand takes the drifting car out of the air, sets it on the boulevard
    on 'first', and tapes it down. Everything else stays up."""
    A = S['A']; car = S['car']; tape = S['tape']; f0 = F(92.25); fgrab = F(92.98); fland = F(93.72); f1 = F(94.40); sc = bpy.context.scene
    type_line(39, split=3, mem=66)
    roof = CAR_M.translation + V(0, 0, .0165); Rh = RX(rad(-16))
    def Wr(p): return Vector(p) + V(0, .020, .084)
    Pf = roof + V(-.012, .016, .085)                                   # where the car hangs
    A.rig(f0, (0, -.23, .17)); A.lean0 = 44; A.k(f0, feet=(.15, .11, rad(50)))
    A.k(f0, lids=0.0, brow=0.0, fL=(.15, .15), fR=(.5, .6), look=Pf)
    A.pose(f0, R=(Wr(Pf + V(.05, .06, .05)), Rh), L='relax', head=(46, 0, 0)); A.pose(fgrab, R=(Wr(Pf), Rh)); A.k(fgrab, fR=(.8, .9))
    A.pose(fland - 4, R=(Wr(roof + V(0, 0, .012)), Rh)); A.pose(fland, R=(Wr(roof), Rh)); A.pose(fland + 12, R=(Wr(roof), Rh))
    A.k(fland + 14, fR=(.3, .3)); A.pose(f1 - 1, R=(Wr(roof + V(.03, .05, .06)), Rh))
    A.k(fland - 8, look=roof); A.hold(f1 - 1); A.R.arm.keyframe_insert('location', frame=f1 - 1)
    # the car: floating (from 90.53) -> into his fingers -> down
    sc.frame_set(fland); place(car, CAR_M); A.attach(car, 'hand_R', fgrab, fland + 1, at=fland)
    sc.frame_set(fgrab); bpy.context.view_layer.update(); Mg = A.R.bone_world('hand_R') @ A.held[-1][4]
    fl0 = F(90.53) + 10; Mfl = Matrix.Translation(Pf - V(0, 0, .0165) + V(.004, -.006, 0)) @ RZ(rad(34)) @ RY(rad(14)) @ RX(rad(-9))
    key_w(car, F(90.53), CAR_M); key_w(car, fl0, CAR_M); key_w(car, fl0 + 34, Mfl); key_w(car, fgrab - 12, Matrix.Translation((0, 0, .003)) @ Mfl); key_w(car, fgrab, Mg)
    A.bake_held(); key_w(car, fland + 1, CAR_M); key_w(car, fland + 2, CAR_M @ Matrix.Translation((0, 0, -.045))); key_w(car, fland + 5, CAR_M)
    key_w(tape, fland + 3, scale=(0, 1, 1)); key_w(tape, fland + 4, scale=(.05, 1, 1)); key_w(tape, fland + 10, scale=(1, 1, 1)); key_w(tape, F(70.6), scale=(0, 0, 0)); set_interp(tape, 'LINEAR')
    # left index finger smooths the tape across
    Rf = RX(rad(-30)); tipv = Rf @ V(0, -.030, -.092); tp = CAR_M.translation + V(0, -.004, .0195)
    A.k(fland + 1, fL=(1.2, .9, {'index': -.1})); A.pose(fland + 3, L=(tp + V(-.020, 0, .02) - tipv, Rf)); A.pose(fland + 5, L=(tp + V(-.012, 0, .002) - tipv, Rf)); A.pose(fland + 10, L=(tp + V(.014, 0, .002) - tipv, Rf)); A.pose(f1 - 1, L=(tp + V(.03, .03, .05) - tipv, Rf))
    A.hold(f1 - 1); A.bake_looks(f0, f1)
    shot_cam('C_carback', f0, f1, (-.15, -.36, IZ + .105), Pf + V(0, .01, -.02), aim1=CAR_M.translation + V(0, .01, .02), loc1=(-.13, -.33, IZ + .075), lens=50, fstop=3.5, focus0=Pf, focus1=CAR_M.translation)


def shot_slam(S):
    """94.40 Bigger, brighter. He throws GRAVITY back on, on the downbeat (94.70): everything lands at once. On 'brighter' the lamp comes up."""
    A = S['A']; f0 = F(94.40); fon = F(94.70); fb = F(94.88); f1 = F(95.44); lev = D.objects['GS_LEVER']; lp = lev.matrix_world.translation.copy()
    type_line(40, mem=69)
    lev.rotation_euler = (.5, 0, 0); lev.keyframe_insert('rotation_euler', frame=fon - 2); lev.rotation_euler = (-.5, 0, 0); lev.keyframe_insert('rotation_euler', frame=fon)
    led = D.materials['GS_led'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength']
    for f, v in ((fon - 1, 0.0), (fon, 7.0)): led.default_value = v; led.keyframe_insert('default_value', frame=f)
    set_interp(D.materials['GS_led'].node_tree, 'CONSTANT')
    Rf = RX(rad(-40)); tipv = Rf @ V(0, -.030, -.092); on_tip = lp + V(0, .018, .034); off_tip = lp + V(0, -.016, .034)
    A.rig(f0, (0, 0, .115)); A.lean0 = 30
    A.k(f0, lids=0.0, brow=0.0, fL=(1.2, .9, {'index': -.1}), fR=(.15, .15), look=lp, feet=(.03, .02, rad(22)))
    A.pose(f0, L=(off_tip + V(0, -.03, .04) - tipv, Rf), R='relax', head=(40, -24, 0)); A.pose(fon - 3, L=(off_tip + V(0, -.008, .002) - tipv, Rf))
    A.rig(fon, (0, 0, .115)); A.pose(fon, L=(on_tip + V(0, -.004, 0) - tipv, Rf)); A.hold(fon, 'feet')
    A.rig(fon + 5, (0, 0, 0)); A.lean0 = 10; A.pose(fon + 5, L=(on_tip + V(0, -.02, .04) - tipv, Rf)); A.k(fon + 5, hips=(0, 0, -.035), feet=(0, 0, 0)); A.pose(fon + 12, L=rest_L(), head=(20, 0, 0)); A.k(fon + 12, fL=(.15, .15))
    A.k(fon + 2, look=(0, 0, IZ + .05)); A.k(fb + 4, look=(.40, -.1, 1.0)); A.pose(f1 - 1, head=(8, 16, 0)); A.hold(f1 - 1); A.bake_looks(f0, f1)
    # brighter: the lamp comes up
    for name, k in (('KEY', 1.45), ('CLAUDE_KEY', 1.3)):
        l = D.objects[name].data; e0 = l.energy
        for f, v in ((fb - 2, e0), (fb + 9, e0 * k)): l.energy = v; l.keyframe_insert('energy', frame=f)
    bulb = D.materials['WB_bulb'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength']
    for f, v in ((fb - 2, 40.0), (fb + 9, 90.0)): bulb.default_value = v; bulb.keyframe_insert('default_value', frame=f)
    shot_cam('C_slam', f0, f1, (0, -1.50, .67), (0, .22, .64), loc1=(0, -1.58, .68), aim1=(0, .22, .62), lens=35, fstop=2.0, focus0=(0, .25, .62))


def birds_orbit(S, f0, f1, r=.15, z=IZ + .30, rate=62):
    """the freed pigeons are birds: with gravity back they simply fly, round and round over the city, until the crash."""
    sc = bpy.context.scene; fbs = S['freebirds']; n = len(fbs)
    for i, fb in enumerate(fbs):
        sc.frame_set(f0); p0 = fb.matrix_world.translation.copy(); q0 = fb.matrix_world.to_quaternion(); last = None
        for f in range(f0, f1, 2):
            t = (f - f0) / FPS; u = smooth(t / 1.6); a = rad(rate) * t + i * math.tau / n + .3 * math.sin(t * .7 + i)
            p = V(C.x + r * math.cos(a), C.y - .02 + r * math.sin(a), z + .025 * math.sin(t * 1.9 + i * 2.1) + .02 * i / n)
            q = Euler((0, rad(-18), a + math.pi)).to_quaternion()             # nose along the tangent, banked into the turn
            fb.location = p0.lerp(p, u); qq = q0.slerp(q, u)
            if last is not None and qq.dot(last) < 0: qq.negate()
            last = qq.copy(); fb.rotation_quaternion = qq; fb.keyframe_insert('location', frame=f); fb.keyframe_insert('rotation_quaternion', frame=f)
        for k in (0, 1):
            w = D.objects[f'bird{i}_wing{k}']
            for f in range(f0, f1, 2):
                w.rotation_euler = (0, (1 if k else -1) * (.15 + .60 * math.sin(f * .9 + i * 1.7)), 0); w.keyframe_insert('rotation_euler', frame=f)


def lit_ramp(objs, f, dur=5, v0=0.0, v1=1.0):
    for o in objs: key_prop(o, 'lit', v0, f); key_prop(o, 'lit', v1, f + dur)


def idle(A, f0, f1, look, head=(22, 0, 0), lean0=12, L=None, R=None):
    A.prev = None; A.lean0 = lean0; A.k(f0, lids=0.0, brow=0.0, fL=(.15, .15), fR=(.15, .15), look=look, feet=(0, 0, 0), hips=(0, 0, 0))
    A.rig(f0, (0, 0, 0)); A.pose(f0, L=L or rest_L(), R=R or (V(.24, .25, BZ + .105), RX(rad(-62))), head=head)


def shot_lightup(S):
    """95.44 Light it up: he throws the switch on the strand and the bulbs come on from his side of the city to ours, landing on
    'up'. 96.40 set it on fire: a long match to the candle on the tallest tower; it takes on 'fire'."""
    A = S['A']; f0 = F(95.44); fup = F(96.16); fc = F(96.32); ffire = F(96.88); f1 = F(98.24); strand = S['strand']; sc = bpy.context.scene
    type_line(41, split=3, mem=72)
    n = len(strand)
    for i, o in enumerate(strand):
        fa = f0 + 2 + int((fup - f0 - 4) * i / n); key_prop(o, 'lit', 0.0, F(70.6)); key_prop(o, 'lit', 0.0, fa); key_prop(o, 'lit', 1.0, fa + 4)
    birds_orbit(S, F(94.70), F(151.42))
    idle(A, f0, fc, (0, .1, IZ + .05), head=(30, 0, 0), lean0=20); A.k(f0 + 2, look=((0, -.12, IZ + .03), fup - f0 - 4)); A.hold(fc - 1); A.bake_looks(f0, fc)
    shot_cam('C_lightup', f0, fc, (-.36, -.58, IZ + .56), (.03, .03, IZ + .03), loc1=(-.33, -.54, IZ + .52), lens=40, fstop=2.8, focus0=(0, 0, IZ + .06))
    # the candle
    crown = S['crown']; sc.frame_set(fc); wick = crown.matrix_world.translation + V(0, 0, crown['h'] + .001); mt = S['match']; fl = S['flame']; mf = S['mflame']; L = mt['len']
    d = V(.30, -.25, -.30).normalized()
    def mK(f, tip, **kw):
        Rh = d.to_track_quat('-Z', 'Y').to_matrix().to_4x4() @ RZ(rad(40)); wrist = Vector(tip) - d * (L + .040); A.pose(f, L=(wrist, Rh), **kw); return tool_matrix(wrist, Rh, (0, 0, -.040))
    A.lean0 = 20; A.k(fc, fL=(1.0, .9), look=wick)
    Mm = mK(fc, wick + V(-.03, .04, .05), head=(26, -8, 0)); key_w(mt, fc - 1, Matrix.Translation((0, 0, -3))); key_w(mt, fc, Mm); A.attach(mt, 'hand_L', fc, f1)
    mK(ffire - 4, wick + V(-.004, .004, .006)); mK(ffire, wick + V(0, 0, .002)); mK(ffire + 5, wick + V(0, 0, .003)); mK(ffire + 12, wick + V(-.03, .05, .05))
    for k in range(4): mK(ffire + 15 + k * 3, wick + V(-.03 + (.012 if k % 2 else -.012), .05, .05))     # shakes it out
    mK(f1 - 1, wick + V(-.06, .10, .04)); A.hold(f1 - 1); A.bake_held(); key_w(mt, f1, Matrix.Translation((0, 0, -3)))
    for f in range(fc, f1):                                           # the match's own flame rides its head until he shakes it out
        sc.frame_set(f); on = f < ffire + 16; mf.location = mt.matrix_world @ V(0, 0, -L - .004); mf.scale = [(1 + .08 * math.sin(f * 1.1)) * (1 if on else 0)] * 3; mf.scale.z *= 2.0
        mf.keyframe_insert('location', frame=f); mf.keyframe_insert('scale', frame=f)
    key_w(mf, fc - 1, scale=0); key_w(mf, f1, scale=0)
    wb.parent(fl, S['table']); fl.location = wick + V(0, 0, .005)
    key_w(fl, F(70.6), scale=0); key_w(fl, ffire, scale=0)
    for f in range(ffire + 1, F(151.42), 3):
        g = min(1.0, (f - ffire) / 6); w = 1 + .07 * math.sin(f * .9) + .04 * math.sin(f * 2.3); fl.scale = (g * w, g * w, g * 2.0 * (1 + .10 * math.sin(f * 1.3))); fl.keyframe_insert('scale', frame=f)
    A.bake_looks(fc, f1)
    shot_cam('C_fire', fc, f1, wick + V(-.10, -.21, .03), wick + V(.004, 0, -.010), loc1=wick + V(-.085, -.18, .028), lens=60, fstop=2.8, focus0=wick)


def table_spin(S, keys):
    """keys = [(frame, deg_per_s)]: the turntable's speed, linearly between keys; baked every frame."""
    tb = S['table']; sc = bpy.context.scene; ang = 0.0; f0 = keys[0][0]; f1 = keys[-1][0]
    for f in range(f0, f1 + 1):
        i = max(j for j, k in enumerate(keys) if k[0] <= f); a, b = keys[i], keys[min(i + 1, len(keys) - 1)]
        w = a[1] if b[0] == a[0] else a[1] + (b[1] - a[1]) * (f - a[0]) / (b[0] - a[0])
        ang += rad(w) / FPS; tb.rotation_euler = (0, 0, ang); tb.keyframe_insert('rotation_euler', frame=f)
    set_interp(tb, 'LINEAR', ['rotation_euler']); S['spin_end'] = ang


def shot_spin(S):
    """98.24 Make it spin: two fingers on the rim, a push on 'spin', and the island turns. 99.28 make it shine: a pinch of glitter
    let go over it on 'shine'; it settles on the roofs and keeps catching the lamp."""
    A = S['A']; f0 = F(98.24); fs = F(98.72); fsh = F(99.76); f1 = F(100.24); sc = bpy.context.scene
    type_line(42, split=3, mem=75)
    table_spin(S, [(fs - 2, 0), (fs + 8, 62), (F(105.68), 50), (F(106.1), 88), (F(126.0), 80), (F(128.0), 22), (F(135.3), 22), (F(136.0), 115), (F(139.0), 100), (F(139.5), 0), (F(151.42), 0)])
    rim0 = V(-.20, .245, BZ + .034); rim1 = V(-.27, .15, BZ + .034)
    def Lp(p, lift=0): return (Vector(p) + V(-.012, .012, .086 + lift), RX(rad(-14)))
    idle(A, f0, f1, rim0, head=(30, -10, 0), lean0=18, L=Lp(rim0, .03))
    A.pose(fs - 4, L=Lp(rim0)); A.pose(fs + 5, L=Lp(rim1)); A.pose(fs + 12, L=Lp(rim1 + V(-.03, .02, 0), .05)); A.pose(fsh - 6, L=rest_L())
    A.k(fs + 6, look=(0, 0, IZ + .06))
    # glitter: right hand, a pinch held over the middle
    pin = V(.03, .06, IZ + .30)
    A.k(f0, fR=(1.1, 1.1)); A.pose(f0 + 4, R=(pin + V(.10, .12, .0), RX(rad(-10)))); A.pose(fsh - 8, R=(pin + V(0, .02, .09), RX(rad(-10)))); A.pose(fsh - 2, R=(pin + V(0, .02, .085), RX(rad(-10))))
    A.k(fsh - 2, fR=(1.1, 1.1)); A.k(fsh + 3, fR=(-.1, -.2)); A.pose(fsh + 10, R=(pin + V(.02, .03, .10), RX(rad(-10)))); A.pose(f1 - 1, R=(pin + V(.05, .06, .09), RX(rad(-10))))
    A.k(fsh - 10, look=pin); A.k(fsh + 6, look=((0, 0, IZ + .08), 10)); A.hold(f1 - 1); A.bake_looks(f0, f1)
    tip = wb.empty('GLIT_TIP', pin, 'FX'); tip.rotation_euler = (math.pi, 0, 0)
    S['glit'].bake(tip, fsh, F(101.4), fsh, fsh + 9, [], IZ + .001)
    for i, g in enumerate(S['glints']): key_prop(g, 'lit', 0.0, F(70.6)); key_prop(g, 'lit', 0.0, fsh + 10 + i % 14); key_prop(g, 'lit', 1.0, fsh + 22 + i % 14)
    shot_cam('C_spin', f0, f1, (-.40, -.52, IZ + .30), (-.02, .06, IZ + .06), loc1=(-.34, -.50, IZ + .30), aim1=(0, .04, IZ + .08), lens=35, fstop=2.8, focus0=(-.1, .1, IZ + .05))


BEATS = [b for b in TL['beats']]; KICKS = sorted(set(round(k, 2) for k in TL['kicks']))


def stack_cands(S):
    sc = bpy.context.scene; sc.frame_set(F(101.0)); spk = S['speaker']; top = spk.matrix_world.translation.copy(); top.z = spk['top']
    return sorted([D.objects[f'spare{i}'] for i in range(24)], key=lambda o: (o.matrix_world.translation - top).length)[:7]


def hop_things(S, t0, t1, amp=.010):
    """the loose blocks on the bench hop on every beat between t0 and t1."""
    O = D.objects; rnd = random.Random(3); sc = bpy.context.scene; skip = set(o.name for o in stack_cands(S)); names = [n for n in [f'spare{i}' for i in range(24)] + [f'pot{i}' for i in range(5)] if n not in skip]
    for n in names:
        o = O.get(n)
        if o is None: continue
        sc.frame_set(F(t0) - 1); z0 = o.location.z; a = amp * rnd.uniform(.5, 1.3); lag = rnd.randint(0, 2)
        for tb in BEATS:
            if not (t0 <= tb < t1): continue
            f = F(tb) + lag
            for ff, z in ((f, z0), (f + 3, z0 + a), (f + 7, z0)): o.location.z = z; o.keyframe_insert('location', index=2, frame=ff)


def shot_time(S):
    """100.24 Make the whole world move in time: he sets the metronome going; from 'move' everything on the bench is on the beat."""
    A = S['A']; f0 = F(100.24); fm = F(101.20); f1 = F(102.16); arm = D.objects['MET_ARM']; sc = bpy.context.scene
    type_line(43, split=4, mem=78)
    tip = arm.matrix_world.translation + V(0, -.004, .062)
    Rf = RX(rad(-25)); tipv = Rf @ V(0, -.030, -.092)
    idle(A, f0, f1, tip, head=(26, 18, 0), lean0=14, R=(tip + V(.03, .03, .04) - tipv, Rf)); A.k(f0, fR=(1.2, .9, {'index': -.1}))
    A.pose(f0 + 8, R=(tip + V(.016, 0, 0) - tipv, Rf)); A.pose(f0 + 12, R=(tip + V(-.012, 0, 0) - tipv, Rf)); A.pose(f0 + 22, R=(V(.24, .25, BZ + .105), RX(rad(-62)))); A.k(f0 + 22, fR=(.15, .15))
    A.k(fm - 4, look=(0, 0, IZ + .06)); A.pose(fm, head=(22, 0, 0))
    # the pendulum: one swing per beat, from his flick to the crash
    per = 60 / 122.6 if False else (BEATS[10] - BEATS[0]) / 10
    arm.rotation_euler = (0, 0, 0); arm.keyframe_insert('rotation_euler', frame=f0 + 10)
    for tb in BEATS:
        if F(tb) < f0 + 12 or tb > 151.42: continue
        k = int(round(tb / per)); arm.rotation_euler = (0, rad(24) * (1 if k % 2 else -1), 0); arm.keyframe_insert('rotation_euler', frame=F(tb))
    hop_things(S, 101.20, 151.42)
    # his head keeps the beat, barely
    for tb in BEATS:
        if not (101.2 <= tb < f1 / FPS - .2): continue
        A.pose(F(tb), head=(26, 0, 0)); A.pose(F(tb) + 7, head=(22, 0, 0))
    A.hold(f1 - 1); A.bake_looks(f0, f1)
    shot_cam('C_time', f0, f1, (.10, -1.30, .62), (.05, .22, .56), loc1=(.04, -1.50, .66), aim1=(0, .22, .60), lens=35, fstop=2.0, focus0=(0, .25, .6))


def shot_louder(S):
    """102.16 Bigger, louder: his hand on the speaker's knob; a quarter turn on 'bigger', all the way on 'louder'. The cone starts to
    punch on the kick. 103.36 Turn the bass into a tower: every kick throws a block off the bench onto the speaker; they land stacked."""
    A = S['A']; f0 = F(102.16); fl = F(102.72); fc = F(103.36); f1 = F(105.68); sc = bpy.context.scene; knob = D.objects['SPK_KNOB']; cone = D.objects['SPK_CONE']; spk = S['speaker']
    type_line(44, mem=81); type_line(45, split=3, mem=84)
    sc.frame_set(f0); kp = knob.matrix_world.translation.copy(); Rk = RX(rad(-18))
    idle(A, f0, f1, kp, head=(24, 30, 0), lean0=22, R=(kp + V(.004, .014, .082), Rk)); A.k(f0, fR=(.7, .8))
    for f, a in ((f0, 0), (f0 + 5, -70), (fl - 3, -70), (fl + 6, -265)): knob.rotation_euler = (0, 0, rad(a)); knob.keyframe_insert('rotation_euler', frame=f)
    for f, a in ((f0, 0), (f0 + 5, -22), (fl - 3, -22), (fl + 6, -70)): A.pose(f, R=(kp + V(.004, .014, .082), RZ(rad(a)) @ Rk))
    A.pose(fc - 2, R=(kp + V(.02, .03, .12), Rk)); A.pose(fc + 10, R=(V(.24, .25, BZ + .105), RX(rad(-62)))); A.k(fc + 10, fR=(.15, .15))
    led = D.materials['SPK_led'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength']
    for f, v in ((f0 + 1, 0.0), (f0 + 2, 8.0)): led.default_value = v; led.keyframe_insert('default_value', frame=f)
    # the cone punches on every kick from 'bigger' to the crash; harder after 'louder'
    cone.scale = (1, 1, 1); cone.keyframe_insert('scale', frame=f0)
    for tk in KICKS:
        f = F(tk)
        if f < f0 + 3 or tk >= 151.42: continue
        a = 1.6 if f < fl else 3.4
        for ff, v in ((f - 1, 1.0), (f + 1, a), (f + 5, 1.0)): cone.scale = (1 + (v - 1) * .03, 1, v); cone.keyframe_insert('scale', frame=ff)
    # the tower: one block per beat jumps from the bench to the top of the speaker
    top = spk.matrix_world.translation + V(0, 0, 0); top.z = spk['top']; cx, cy = top.x - .012, top.y + .012; zt = top.z; rnd = random.Random(5); stack = []
    cands = stack_cands(S)
    beats = [tb for tb in BEATS if 103.36 <= tb < 105.60][:6]
    for j, tb in enumerate(beats):
        o = cands[j]; fj = F(tb); sc.frame_set(fj - 1); M0 = o.matrix_world.copy(); hgt = o.dimensions.z
        Mt = Matrix.Translation((cx + rnd.uniform(-.004, .004), cy + rnd.uniform(-.004, .004), zt + hgt / 2)) @ RZ(rnd.uniform(-.3, .3)); zt += hgt
        key_w(o, fj - 1, M0)
        for i in range(1, 9):
            u = i / 8; p = M0.translation.lerp(Mt.translation, u) + V(0, 0, .16 * math.sin(math.pi * u) * (1 - .3 * u))
            key_w(o, fj - 1 + i, Matrix.Translation(p) @ M0.to_quaternion().slerp(Mt.to_quaternion(), u).to_matrix().to_4x4() @ RX(rad(360 * u)))
        key_w(o, fj + 9, Matrix.Translation((0, 0, .004)) @ Mt); key_w(o, fj + 11, Mt); stack.append((o, Mt))
    S['stack'] = stack; S['stack_top'] = V(cx, cy, zt)
    A.k(fc + 4, look=(V(cx, cy, zt - .05), 4)); A.pose(fc + 12, head=(16, 34, 0)); A.hold(f1 - 1); A.bake_looks(f0, f1)
    sc.frame_set(f0)
    shot_cam('C_louder', f0, fc, kp + V(-.16, -.36, .10), kp + V(.0, -.02, -.07), loc1=kp + V(-.13, -.31, .09), lens=40, fstop=2.8, focus0=kp)
    shot_cam('C_tower', fc, f1, kp + V(-.10, -.50, .06), kp + V(.0, 0, .03), loc1=kp + V(-.08, -.46, .12), aim1=kp + V(.0, 0, .10), lens=30, fstop=2.8, focus0=kp)


def shot_run(S):
    """105.68 Run it, run it: one finger on the one red button, twice. 106.24 Let me see what we can do: we go up and round and
    look at all of it going at once."""
    A = S['A']; f0 = F(105.68); f2 = F(105.92); fc = F(106.30); f1 = F(111.10); sc = bpy.context.scene; cap = D.objects['RUN_CAP']; cp = cap.matrix_world.translation.copy()
    type_line(46, mem=87); type_line(47, split=4, mem=88)
    Rf = RX(rad(-22)); tipv = Rf @ V(0, -.030, -.092); top = cp + V(0, 0, .008)
    idle(A, f0 - 0, f1, top, head=(36, -16, 0), lean0=16, L=(top + V(0, 0, .02) - tipv, Rf)); A.k(f0, fL=(1.2, .9, {'index': -.1}))
    z0 = cap.location.z
    for fp in (f0, f2):
        A.pose(fp - 0, L=(top + V(0, 0, -.004) - tipv, Rf)) if fp == f0 else None
        for ff, dz in ((fp - 2, 0), (fp, -.006), (fp + 3, 0)): cap.location.z = z0 + dz; cap.keyframe_insert('location', index=2, frame=ff)
    A.pose(f0 + 3, L=(top + V(0, 0, .014) - tipv, Rf)); A.pose(f2, L=(top + V(0, 0, -.004) - tipv, Rf)); A.pose(f2 + 4, L=(top + V(0, 0, .02) - tipv, Rf))
    A.pose(fc + 8, L='relax', R='relax', head=(14, 0, 0)); A.k(fc + 8, fL=(.15, .15)); A.lean0 = 6
    A.k(fc + 2, look=((0, 0, IZ + .1), 4))
    for tb in BEATS:
        if not (106.6 <= tb < 110.9): continue
        A.pose(F(tb), head=(17, 0, 0)); A.pose(F(tb) + 7, head=(14, 0, 0))
    A.k(F(108.2), look=((.2, -.1, IZ + .32), 6)); A.k(F(109.6), look=((0, 0, IZ + .1), 5))
    A.hold(f1 - 1); A.bake_looks(f0, f1)
    # the strand starts to chase once it is running
    for i, o in enumerate(S['strand']):
        for f in range(fc, F(151.42), 4):
            key_prop(o, 'lit', .35 + .65 * (.5 + .5 * math.sin(f * .21 - i * .55)), f)
    shot_cam('C_run', f0, fc, cp + V(.10, -.30, .16), cp + V(.01, 0, .012), loc1=cp + V(.09, -.27, .15), lens=60, fstop=4.0, focus0=cp)
    cam = shot_cam('C_run_wide', fc, f1, (-.55, -1.25, .52), (0, .12, .52), lens=32, fstop=2.2, focus0=(0, .1, .5),
                   mids=[(.33, (-.20, -1.42, .72), (0, .14, .54), (0, .1, .5)), (.66, (.30, -1.40, .92), (0, .14, .52), (0, .1, .5))], loc1=(.62, -1.18, 1.05), aim1=(0, .12, .48), focus1=(0, .1, .5))


def expo(keys):
    """view exposure steps (stops) at cuts: keys = [(frame, value), ...], constant between."""
    vs = bpy.context.scene.view_settings
    for f, x in keys: vs.exposure = x; vs.keyframe_insert('exposure', frame=f)
    set_interp(bpy.context.scene, 'CONSTANT', ['exposure'])


def beat_nod(A, t0, t1, base, amp=3):
    for tb in BEATS:
        if not (t0 <= tb < t1 - .25): continue
        A.pose(F(tb), head=(base[0] + amp, base[1], 0)); A.pose(F(tb) + 7, head=base)


def ride_cam(S, name, f0, f1, loc0, aim0, loc1=None, aim1=None, **kw):
    """a camera that rides the turntable: positions are given as if the table were at rest."""
    cam = shot_cam(name, f0, f1, loc0, aim0, loc1=loc1, aim1=aim1, **kw); cam.parent = S['table']; cam.matrix_parent_inverse = Matrix.Translation(-Vector((C.x, C.y, BZ)))
    return cam


def shot_montage(S):
    """111.10 - 126.40  Run it (run it) / Ooh, look what we can do. Inside the thing while it runs: down the boulevard past the car,
    the office block typing, the candle; then his face watching it turn, and the second look at us; then straight down on all of it."""
    A = S['A']; f0 = F(111.10); m2 = F(113.06); m3 = F(115.02); m4 = F(116.21); m5 = F(121.04); m6 = F(124.00); f1 = F(126.40); sc = bpy.context.scene; cells = S['cells']
    type_line(48, mem=89); type_line(49, mem=90); type_line(50, split=2, mem=91); type_line(51, split=2, mem=92)
    type_anim(S['guys'], F(105.7), F(151.42), 2, seed=4)
    A.lean0 = 6; A.k(f0, lids=0.0, brow=0.0, fL=(.15, .15), fR=(.15, .15), look=(0, 0, IZ + .1), feet=(0, 0, 0)); A.rig(f0, (0, 0, 0)); A.pose(f0, L='relax', R='relax', head=(14, 0, 0))
    beat_nod(A, 111.1, 116.0, (14, 0, 0))
    # his face (m4): eyes ride the city round, then up to us
    A.pose(m4 - 2, head=(16, 0, 0)); A.pose(m4, L=rest_L(), R=(V(.24, .25, BZ + .105), RX(rad(-62))), head=(26, 0, 0), lean0=20)
    for k in range(5):
        fa = m4 + 4 + k * 17; A.k(fa, look=((.14, -.02, IZ + .06), 3)); A.k(fa + 3, look=((-.14, -.02, IZ + .06), 13))
    fst = F(119.20); lens = V(-.03, -.80, IZ + .36)
    A.k(fst, look=lens); A.pose(fst + 4, head=(26, 0, 0)); A.pose(fst + 12, head=(15, -2, 0)); A.k(fst, lids=0.0); A.k(fst + 8, lids=.16); A.blink(fst + 22, base=.16); A.k(m5 - 6, lids=.16); A.k(m5, lids=0.0); A.k(m5 - 8, look=(0, 0, IZ + .06)); A.pose(m5 - 4, head=(17, -2, 0)); A.pose(m5 + 6, head=(26, 0, 0))
    A.lean0 = 6; A.pose(m6 - 2, head=(26, 0, 0)); A.pose(m6, L='relax', R='relax', head=(14, 0, 0)); beat_nod(A, 124.0, 126.3, (14, 0, 0))
    A.hold(f1 - 1); A.bake_looks(f0, f1)
    cx = C.x; cy = C.y
    ride_cam(S, 'C_m1', f0, m2, (cx - .014, cy - .215, IZ + .014), (cx - .004, cy, IZ + .030), loc1=(cx - .014, cy - .085, IZ + .018), lens=22, fstop=8.0, focus0=(cx + .009, cy - .118, IZ + .01), focus1=(cx, cy, IZ + .02), ease=False)
    expo([(F(70.6), 0.0), (f0, -.9), (m2, -.7), (m3, 0.0), (m5, -.4), (m6, 0.0)])      # m5: straight down under the lamp, the roofs and the mat take it full on
    # as the table turns, the open offices swing round to face the lamp side and the shadowless bounce light burns them out (blveil): those lights come down for that ride
    for nm, k in (('BOUNCE', .12), ('SPK_LIGHT', .3), ('KEY', .6)):
        kd = D.objects[nm].data; sc.frame_set(m2 - 1); e0 = kd.energy
        for f, v in ((m2 - 1, e0), (m2, e0 * k), (m3 - 1, e0 * k), (m3, e0)): kd.energy = v; kd.keyframe_insert('energy', frame=f)
    hb = cells[5].lerp(cells[10], .5) + V(.003, -.012, .006)
    ride_cam(S, 'C_m2', m2, m3, hb + V(-.045, -.16, .012), hb, loc1=hb + V(.03, -.135, .01), lens=60, fstop=11, focus0=hb + V(0, .010, 0))      # focus on the people, not the front of the block
    sc.frame_set(F(98.0)); wick = S['crown'].matrix_world.translation + V(0, 0, S['crown']['h'] + .004)
    ride_cam(S, 'C_m3', m3, m4, wick + V(-.07, -.15, .012), wick + V(0, 0, -.012), loc1=wick + V(-.03, -.13, .02), lens=60, fstop=2.8, focus0=wick)
    sc.frame_set(fst + 14); bpy.context.view_layer.update(); eye = (D.objects['eye_L'].matrix_world.translation + D.objects['eye_R'].matrix_world.translation) / 2
    shot_cam('C_m4', m4, m5, lens + V(.10, -.12, -.03), eye + V(0, 0, -.05), loc1=lens, lens=50, fstop=2.4, focus0=eye, ease=False)
    cam = shot_cam('C_m5', m5, m6, (cx, cy - .02, IZ + 1.05), (cx, cy, IZ), loc1=(cx, cy - .02, IZ + .78), lens=35, fstop=4.0, focus0=(cx, cy, IZ + .05), ease=False)
    for f, r in ((m5, 0.0), (m6 - 1, rad(-38))): cam.rotation_euler.z = r; cam.keyframe_insert('rotation_euler', index=2, frame=f)
    shot_cam('C_m6', m6, f1, (0, -1.50, .66), (0, .22, .62), loc1=(0, -1.66, .68), lens=35, fstop=2.0, focus0=(0, .25, .62))


def swing(piv, f, ang, axis=1):
    e = list(piv.rotation_euler); e[axis] = ang; piv.rotation_euler = e; piv.keyframe_insert('rotation_euler', frame=f)


def shot_moons(S):
    """126.40 Add a moon / Add another: two paper moons come down on their threads, by the window on his left, each steadied by a
    fingertip on the word. 128.32 Make them fall in love with each other: one nudge, they swing together and stay.
    130.24 tasteful: the lamp comes down. 131.28 weird: a poke each, and they have eyes."""
    A = S['A']; a, b = S['moonL'], S['moonR']; f0 = F(126.40); fa = F(127.04); fb = F(127.68); fl = F(129.12); ft = F(130.56); fw = F(131.52); f1 = F(132.24); sc = bpy.context.scene
    type_line(52, mem=93); type_line(53, mem=93); type_line(54, split=4, mem=94); type_line(55, mem=95); type_line(56, mem=95)
    za = a.location.z - 1.2
    for m_, fx in ((a, fa), (b, fb)):
        for f, dz in ((F(70.6), 1.2), (fx - 11, 1.2), (fx - 2, -.012), (fx + 3, .006), (fx + 8, 0)): m_.location.z = za + dz; m_.keyframe_insert('location', index=2, frame=f)
    pa = MOON_A.copy(); pb = MOON_B.copy(); mid = (pa + pb) / 2
    Ru = RX(rad(-95)); tipu = Ru @ V(0, -.030, -.092)                         # index pointing forward and a little up: touches from his side
    def touch(p, back=0.0, dx=0.0, dz=0.0): return (Vector(p) + V(dx, .047 + back, dz) - tipu, Ru)
    idle(A, f0, f1, pa + V(0, 0, .3), head=(2, -30, 0), lean0=8, L='relax', R='relax'); A.k(f0, fL=(1.2, .9, {'index': -.1}))
    A.pose(fa - 7, L=touch(pa, .05, 0, -.03)); A.pose(fa + 1, L=touch(pa)); A.pose(fa + 8, L=touch(pa, .04, .03, -.02)); A.k(fa - 9, look=pa)
    A.k(fb - 9, look=pb); A.pose(fb - 6, L=touch(pb, .05, 0, -.03), head=(2, -22, 0)); A.pose(fb + 1, L=touch(pb)); A.pose(fb + 9, L=touch(pb, .05, .04, -.03))
    # the nudge: he pushes B toward A from its right side; both swing in and meet on 'love'
    th = math.asin(((pb.x - pa.x) / 2 - .0465) / 1.4); fn = F(128.72)
    Rs = RY(rad(35)) @ RX(rad(-60)); tips = Rs @ V(0, -.030, -.092)
    A.pose(fn - 7, L=(pb + V(.075, .03, 0) - tips, Rs)); A.pose(fn + 3, L=(pb + V(.050, .02, 0) - tips, Rs)); A.pose(fl + 2, L=(pb + V(.030, .02, 0) - tips, Rs)); A.pose(fl + 12, L=(pb + V(.09, .06, -.05) - tips, Rs)); A.k(fn - 8, look=mid)
    for m_, sg in ((a, -1), (b, 1)):
        swing(m_, fn - 1, 0); swing(m_, fl, sg * th); swing(m_, fl + 8, sg * th * .84); swing(m_, fl + 16, sg * th); swing(m_, f1, sg * th)
    # tasteful: the lamp comes down, he stands back. weird: a poke each
    key = D.objects['KEY'].data; e0 = key.energy; ck = D.objects['CLAUDE_KEY'].data; c0 = ck.energy
    for f, k in ((ft - 3, 1.0), (ft + 9, .5)): key.energy = e0 * k; key.keyframe_insert('energy', frame=f); ck.energy = c0 * (.6 + .4 * k); ck.keyframe_insert('energy', frame=f)
    A.pose(ft - 4, L='relax', head=(6, -20, 0)); A.k(ft - 2, look=(0, 0, IZ + .1)); A.k(ft + 10, look=mid)
    ja = pa + V(.034, 0, 0); jb = pb + V(-.034, 0, 0)                           # where they hang once they are together
    A.pose(fw - 9, L=touch(ja, .05, 0, .0)); A.pose(fw - 3, L=touch(ja, .0, 0, .0)); A.pose(fw, L=touch(ja, .03, .03, .0)); A.pose(fw + 3, L=touch(jb, .0, 0, .0)); A.pose(fw + 9, L=touch(jb, .06, .05, -.03)); A.pose(f1 - 1, L='relax'); A.k(f1 - 1, fL=(.15, .15))
    for nm, fe in (('MOON_A', fw - 3), ('MOON_B', fw + 3)):
        e = D.objects[nm + '_EYE']; pu = D.objects[nm + '_PUP']
        for f, sc_ in ((F(70.6), 0), (fe - 1, 0), (fe + 2, 1.25), (fe + 5, 1.0)): e.scale = (sc_,) * 3; e.keyframe_insert('scale', frame=f)
        x0 = pu.location.x; z0 = pu.location.z
        for f in range(fe, F(151.42), 4):
            pu.location.x = x0 + .004 * math.sin(f * .37 + (0 if nm == 'MOON_A' else 2)); pu.location.z = z0 - .003 + .0035 * math.cos(f * .29); pu.keyframe_insert('location', frame=f)
    lensp = V(-.24, -.86, IZ + .40)
    A.k(fw + 9, look=lensp); A.k(fw + 9, lids=0.0); A.k(fw + 14, lids=.16); A.pose(fw + 14, head=(8, -14, 0)); A.hold(f1 - 1); A.k(f1, lids=0.0); A.bake_looks(f0, f1)
    shot_cam('C_moons', f0, f1, lensp + V(0, -.08, 0), (-.16, .30, IZ + .43), loc1=lensp, lens=40, fstop=2.4, focus0=mid)


def shot_ocean(S):
    """132.24 Make the ocean disappear: he lifts the plug on its chain; the water goes. 133.76 Bring it back: the plug goes home, it
    fills. 134.48 Every wave: one fingertip in the water."""
    A = S['A']; f0 = F(132.24); fd = F(132.96); fb = F(134.16); fw = F(134.72); f1 = F(135.28); sc = bpy.context.scene; tb = S['table']; oc = D.objects['ocean']; pl = S['plug']
    type_line(57, split=3, mem=96); type_line(58, mem=96); type_line(59, mem=97)
    # put the plug where his hand will be: at the back of the ocean on 'disappear'
    back = V(C.x, C.y + wbset.R_WATER - .035, wbset.WATER_Z); sc.frame_set(fd); bpy.context.view_layer.update(); place(pl, Matrix.Translation(back)); pz = pl.location.z
    sc.frame_set(f0); bpy.context.view_layer.update()
    Rp = RX(rad(-12))
    def Hp(f): sc.frame_set(f); bpy.context.view_layer.update(); return D.objects['plug_ring'].matrix_world.translation.copy() + V(0, .012, .090)
    idle(A, f0, f1, back, head=(34, 0, 0), lean0=16, R=(Hp(f0) + V(0, .02, .05), Rp)); A.k(f0, fR=(.9, .9))
    for f in range(f0 + 4, fd - 1, 3): A.pose(f, R=(Hp(f), Rp))
    for f, dz in ((fd - 2, 0), (fd + 6, .05), (fb - 8, .05), (fb, 0)): pl.location.z = pz + dz; pl.keyframe_insert('location', index=2, frame=f)
    for f in range(fd - 1, fb + 2, 3):
        sc.frame_set(f); bpy.context.view_layer.update(); A.pose(f, R=(D.objects['plug_ring'].matrix_world.translation.copy() + V(0, .012, .090), Rp))
    A.pose(fb + 8, R=(back + V(.03, .03, .16), Rp)); A.k(fb + 8, fR=(.15, .15))
    oz = oc.location.z
    for f, dz, sx in ((fd, 0, 1.0), (fd + 16, -.0042, .96), (fb - 2, -.0042, .96), (fb + 12, 0, 1.0)): oc.location.z = oz + dz; oc.keyframe_insert('location', index=2, frame=f)
    # the wave: left index touches the water at the back; rings go out
    Rf = RX(rad(-35)); tipv = Rf @ V(0, -.030, -.092); wp = V(C.x - .10, C.y + wbset.R_WATER - .05, wbset.WATER_Z)
    A.k(fw - 8, fL=(1.2, .9, {'index': -.1})); A.pose(fw - 8, L=(wp + V(0, .01, .05) - tipv, Rf)); A.pose(fw, L=(wp - tipv, Rf)); A.pose(fw + 5, L=(wp + V(0, .01, .04) - tipv, Rf)); A.pose(f1 - 1, L=rest_L()); A.k(f1 - 1, fL=(.15, .15))
    for i, r in enumerate(S['rings']):
        fa = fw + i * 5; r.location = (wp.x, wp.y, wbset.WATER_Z + .001)
        for f, s_ in ((F(70.6), 0), (fa, 0.0), (fa + 1, .15), (fa + 22, 2.6 + .3 * i), (fa + 23, 0)): r.scale = (s_, s_, max(.001, 1 if 0 < s_ < 2.5 else 0)); r.keyframe_insert('scale', frame=f)
    bump = D.materials['WB_water'].node_tree.nodes['WATER_BUMP'].inputs['Strength']
    for f, v in ((fw - 1, .16), (fw + 6, .55), (f1 + 20, .22)): bump.default_value = v; bump.keyframe_insert('default_value', frame=f)
    A.k(fd + 4, look=(0, -.1, IZ)); A.k(fw - 6, look=wp); A.hold(f1 - 1); A.bake_looks(f0, f1)
    shot_cam('C_ocean', f0, f1, (-.36, -.56, IZ + .50), (.02, .06, IZ + .0), loc1=(-.32, -.52, IZ + .46), lens=40, fstop=2.8, focus0=(0, .1, IZ))


def shot_sixty(S):
    """135.28 Sixty frames, don't make me wait: the monitor counts 24 to 60 and the whole island winds up to speed."""
    A = S['A']; f0 = F(135.28); f60 = F(135.84); fc = F(136.20); f1 = F(137.28); sc = bpy.context.scene
    type_line(60, split=2, mem=98)
    for i, f in enumerate(range(f0 + 2, f60 + 1)): screen(f, big=f'{24 + int(36 * (i + 1) / (f60 - f0 - 1))} fps')
    screen(f1 + 14, big='')
    for f, d in SCREEN:
        if f0 <= f < f1 + 14: d['big'] = '60 fps' if f >= f60 else f'{24 + int(36 * max(0, f - f0) / (f60 - f0))} fps'
    idle(A, f0, f1, MON_EYE, head=(14, -34, 0), lean0=8, L='relax', R='relax'); A.k(fc - 4, look=(0, 0, IZ + .08)); A.pose(fc + 2, head=(22, 0, 0)); A.hold(f1 - 1); A.bake_looks(f0, f1)
    mon = D.objects['MONITOR']; x0, y0, zt, sw, sh = mon['screen']; yaw = mon.rotation_euler.z; n = V(math.sin(yaw), -math.cos(yaw), 0); ctr = mon.location + (RZ(yaw) @ (V(x0 + sw / 2, y0, zt - sh / 2) - mon.location))
    shot_cam('C_sixty', f0, fc, ctr + n * .62 + V(.05, 0, .03), ctr, loc1=ctr + n * .54 + V(.04, 0, .02), lens=50, fstop=4.0, focus0=ctr)
    shot_cam('C_sixty_top', fc, f1, (-.30, -.50, IZ + .62), (.02, .04, IZ + .04), loc1=(-.26, -.46, IZ + .56), lens=35, fstop=2.8, focus0=(0, 0, IZ + .06))


def tear(S, part, f0, fm, side):
    """a piece of the planner (child of PLANNER) rides the board until fm - 3, then comes away in his fingers, then falls."""
    A = S['A']; sc = bpy.context.scene; pl = S['planner']; bone = 'hand_' + side
    sc.frame_set(fm - 3); bpy.context.view_layer.update(); part.rotation_mode = 'QUATERNION'; M0 = part.matrix_world.copy(); h0 = A.R.bone_world(bone).copy(); rel = pl.matrix_world.inverted() @ M0
    part.parent = None; part.matrix_world = M0
    for f in range(F(137.28) - 1, fm - 2):                              # it rides the board (parked or held) from the first time the board is seen
        sc.frame_set(f); bpy.context.view_layer.update(); key_w(part, f, pl.matrix_world @ rel)
    for f in range(fm - 3, fm + 8):
        sc.frame_set(f); key_w(part, f, A.R.bone_world(bone) @ h0.inverted() @ M0)
    sc.frame_set(fm + 7); Mr = part.matrix_world.copy()
    for i in range(1, 16):
        t = i / FPS; key_w(part, fm + 7 + i, Matrix.Translation((.02 * t * 6, -.03 * t * 4, -4.9 * t * t)) @ Mr @ RZ(rad(160 * t)) @ RX(rad(240 * t)))
    key_w(part, fm + 23, Matrix.Translation((0, 0, -3))); set_interp(part, 'LINEAR')


def hold_planner(S, f0, f1, tilt=10):
    """right hand brings the week up in front of him; returns the planner's world matrix while held."""
    A = S['A']; pl = S['planner']; base = V(.03, .20, IZ + .15); Mp = Matrix.Translation(base) @ RX(rad(-tilt))
    grip = (Mp @ V(.135, .012, .06)); Rh = RZ(rad(-90)) @ RX(rad(-80))
    A.pose(f0, R=(grip + V(.01, .05, -.02), Rh)); A.k(f0, fR=(.9, .9)); key_w(pl, f0 - 1, Matrix.Translation((0, 0, -3))); key_w(pl, f0, Mp); A.attach(pl, 'hand_R', f0, f1)
    return Mp


def shot_mondays(S):
    """137.28 Delete Mondays: he holds up the week (Monday is all meetings), takes Monday's column by the top and pulls it off on
    'Mondays'. It drops."""
    A = S['A']; f0 = F(137.28); fm = F(137.68); f1 = F(138.40); sc = bpy.context.scene; pl = S['planner']; mon = D.objects['PL_MON']; W, H = pl['W'], pl['H']
    type_line(61, mem=98)
    idle(A, f0, f1, (-.15, .0, IZ + .40), head=(18, -8, 0), lean0=8, L='relax', R='relax')
    Mp = hold_planner(S, f0, f1); cw = (W - .024) / 7; top = Mp @ V(-W / 2 + .012 + .5 * cw, -.012, H * .15); Rr = RX(rad(-100)); tipv = Rr @ V(0, -.02, -.085)      # low on the strip: the six meetings above his fingers stay readable
    A.k(f0, fL=(.2, .2)); A.pose(f0, L=(top + V(-.06, -.06, .03) - tipv, Rr)); A.pose(fm - 4, L=(top - tipv, Rr)); A.k(fm - 3, fL=(1.0, 1.0)); A.pose(fm + 5, L=(top + V(-.05, -.07, .05) - tipv, Rr)); A.k(fm + 7, fL=(.1, .1)); A.pose(f1 - 1, L=(top + V(-.12, -.02, .0) - tipv, Rr))
    A.k(fm - 8, look=top); A.k(fm + 9, look=(top + V(-.05, -.07, -.2), 8)); A.hold(f1 - 1); A.bake_held()
    # Monday comes away with his fingers, then falls
    tear(S, mon, f0, fm, 'L')
    A.bake_looks(f0, f1)
    c = Mp @ V(0, 0, H / 2)
    shot_cam('C_mondays', f0, f1, c + V(-.01, -.66, .04), c + V(-.03, 0, .0), loc1=c + V(-.02, -.62, .04), lens=50, fstop=4.0, focus0=c)


def shot_sun(S):
    """138.40 Move the sun: he swings the lamp round; every shadow in the city turns."""
    A = S['A']; f0 = F(138.40); fs = F(138.88); f1 = F(139.52); sc = bpy.context.scene; lamp = D.objects['LAMP']; hd = D.objects['LAMP_HEAD']
    type_line(62, mem=98)
    key_w(S['planner'], f0, Matrix.Translation((0, 0, -3)))
    # The head is an empty at rest (identity); the shade and the KEY spot under it carry the aim. So the head only ever gets the
    # rotation that takes the rest aim direction to the new one, and rest is keyed before the move. (Nov 11: it used to be set to
    # a track-to quaternion with no key before f0, which turned the lamp to the ceiling for the whole film: the city was lit by
    # the shadowless bounce light alone, which is what blew out the pale buildings.)
    aim = V(C.x + .02, C.y, BZ + .04); hd.rotation_mode = 'QUATERNION'; hd.rotation_quaternion = (1, 0, 0, 0); hd.keyframe_insert('rotation_quaternion', frame=f0 - 1)
    sc.frame_set(f0 - 1); bpy.context.view_layer.update(); d0 = (aim - hd.matrix_world.translation).normalized()
    for f in range(f0, f1 + 1):
        u = smooth((f - (fs - 8)) / 22); lamp.rotation_euler = (0, 0, rad(-62) * u); lamp.keyframe_insert('rotation_euler', frame=f); sc.frame_set(f); bpy.context.view_layer.update()
        hp = hd.matrix_world.translation.copy(); q = d0.rotation_difference((aim - hp).normalized()); M = Matrix.Translation(hp) @ q.to_matrix().to_4x4(); s_ = hd.scale.copy(); hd.matrix_world = M; hd.scale = s_; hd.keyframe_insert('rotation_quaternion', frame=f)
    ck = D.objects['CLAUDE_KEY']; sc.frame_set(f1); ck.location = hd.matrix_world.translation + V(.02, -.06, .04); ck.keyframe_insert('location', frame=f1); ck.location = V(.50, -.14, 1.02); ck.keyframe_insert('location', frame=f0)
    idle(A, f0, f1, (.4, 0, .95), head=(-4, 22, 0), lean0=8, L='relax', R='relax')
    sc.frame_set(f0); hp0 = hd.matrix_world.translation.copy(); sc.frame_set(f1 - 1); hp1 = hd.matrix_world.translation.copy()
    Rr = RX(rad(-150)); tipv = Rr @ V(0, 0, -.09)
    A.k(f0, fR=(.4, .4)); A.pose(f0, R=(V(.30, .22, .78), Rr)); A.pose(fs - 6, R=(V(.33, .16, .82), Rr)); A.pose(fs + 10, R=(V(.30, .30, .82), Rr)); A.pose(f1 - 1, R='relax')
    for f in range(f0, f1, 3):
        sc.frame_set(f); A.k(f, look=(hd.matrix_world.translation.copy(), 3))
    A.hold(f1 - 1); A.bake_looks(f0, f1)
    shot_cam('C_sun', f0, f1, (-.50, -.70, IZ + .44), (.08, .10, IZ + .20), loc1=(-.46, -.66, IZ + .42), lens=30, fstop=2.8, focus0=(0, 0, IZ + .08))


def shot_vertical(S):
    """139.52 Make it vertical for everyone: he stops the island, takes it by the rim and stands it on its edge, facing us; his eyes
    come up over the top. 141.52 Make the city clap on two and four: the towers lean together and clap on the snare.
    143.44 Turn the ceiling into the floor: the whole room goes over."""
    A = S['A']; tb = S['table']; f0 = F(139.52); fv = F(139.84); fe = F(140.56); fc = F(141.52); fq = F(143.44); f1 = F(145.44); sc = bpy.context.scene
    type_line(63, split=3, mem=99); type_line(64, split=4, mem=99); type_line(65, split=3, mem=99)
    sc.frame_set(f0); ang = tb.rotation_euler.z; p0 = tb.location.copy(); up = V(C.x, C.y + .16, BZ + .312)
    for f in range(f0, F(151.42) + 1):
        u = smooth((f - (f0 + 2)) / (fv + 4 - f0)); tb.rotation_euler = (rad(90) * u, 0, ang); tb.keyframe_insert('rotation_euler', frame=f); tb.location = p0.lerp(up, u); tb.keyframe_insert('location', frame=f)
    def rim(u, sg): return (p0.lerp(up, u) + V(sg * .262, .016 + .02 * (1 - u), .03 * (1 - u) + .0 * u), RY(rad(sg * (20 + 50 * u))) @ RX(rad(-30 * (1 - u))))
    idle(A, f0, f1, (0, 0, IZ + .08), head=(30, 0, 0), lean0=10, L=rim(0, -1), R=rim(0, 1)); A.k(f0, fL=(.7, .7), fR=(.7, .7))
    A.pose(f0 + 2, L=rim(0, -1), R=rim(0, 1)); A.pose(fv + 6, L=rim(1, -1), R=rim(1, 1), head=(4, 0, 0)); A.k(fv + 2, look=(0, -1.4, .7)); A.k(fe, look=((.18, -1.4, .5), 4)); A.k(fe + 14, look=((-.18, -1.4, .5), 6)); A.k(fc - 6, look=(0, -1.4, .7))
    # for everyone: the little guys are not glued in
    for i, g in enumerate(S['guys']):
        fa = fe + (i * 5) % 9; sc.frame_set(fa); M0 = g.matrix_world.copy(); land = V(M0.translation.x + .02 * math.sin(i * 2.3), M0.translation.y - .03 - .01 * (i % 4), BZ + .004)
        key_w(g, fa, M0)
        n = 9
        for j in range(1, n + 1):
            u = j / n; key_w(g, fa + j, Matrix.Translation(M0.translation.lerp(land, u) + V(0, 0, (1 - u * u) * (M0.translation.z - land.z) - (1 - u) * (M0.translation.z - land.z))) @ RX(rad(90 + 200 * u)) @ RZ(rad(90 * u)))
        key_w(g, fa + n + 3, Matrix.Translation(land + V(0, 0, .006)) @ RX(rad(90)) @ RZ(rad(40 * i))); key_w(g, fa + n + 6, Matrix.Translation(land) @ RX(rad(90)) @ RZ(rad(40 * i)))
        S.setdefault('guy_land', []).append(Matrix.Translation(land) @ RX(rad(90)) @ RZ(rad(40 * i)))
    # clap on two and four
    snares = sorted(set(round(x, 2) for x in TL['snares'])); claps = [t for t in (142.12, 143.10)]
    cb = min(S['blocks'], key=lambda b: (b[1] - (C.x - .050)) ** 2 + (b[2] - (C.y + .050)) ** 2)[0]
    blocks = [(o, o.location.copy(), o.dimensions.copy()) for o, bx, by, bh in S['blocks'] if o.name.startswith('blk') and D.objects.get('step' + o.name[3:]) is None and o is not cb and 'lit' in o.keys()]
    pairs = []; used = set()
    for i, (o, l, d) in enumerate(blocks):
        if i in used: continue
        best = None
        for j, (o2, l2, d2) in enumerate(blocks):
            if j <= i or j in used: continue
            if abs(l2.y - l.y) < .012 and .02 < abs(l2.x - l.x) < .056 and min(d.z, d2.z) > .03:
                best = j; break
        if best is not None: used.add(i); used.add(best); pairs.append((blocks[i], blocks[best]))
    for (o, l, d), (o2, l2, d2) in pairs:
        gap = abs(l2.x - l.x) - (d.x + d2.x) / 2; sg = 1 if l2.x > l.x else -1
        for ob, lo, dm, s_ in ((o, l, d, sg), (o2, l2, d2, -sg)):
            th = math.asin(min(.9, (gap / 2 + .001) / max(.02, dm.z))) * s_
            def KK(f, a):
                ob.rotation_euler = (0, a, 0); ob.location = lo + V(math.sin(a) * dm.z / 2, 0, (math.cos(a) - 1) * dm.z / 2); ob.keyframe_insert('rotation_euler', frame=f); ob.keyframe_insert('location', frame=f)
            KK(fc, 0)
            for tc in claps: KK(F(tc) - 5, -th * .25); KK(F(tc), th); KK(F(tc) + 4, th * .2); KK(F(tc) + 9, 0)
    for tc in claps: A.k(F(tc) - 2, lids=0.0); A.k(F(tc) + 1, lids=.5); A.k(F(tc) + 5, lids=0.0)
    A.hold(f1 - 1); A.bake_looks(f0, f1)
    c0 = V(0, -1.10, IZ + .60); c1 = V(0, -.98, IZ + .60); aim = V(0, .12, IZ + .31)
    cam = shot_cam('C_vertical', f0, f1, c0, aim, loc1=c1, lens=40, fstop=2.4, focus0=(0, .1, IZ + .3), ease=False)
    cam.rotation_mode = 'QUATERNION'; fr0 = F(143.70); fr1 = F(145.10)
    for f in range(f0, f1):
        u = (f - f0) / (f1 - 1 - f0); loc = c0.lerp(c1, u); q = (aim - loc).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), math.pi * smooth((f - fr0) / (fr1 - fr0)))
        cam.rotation_quaternion = q; cam.keyframe_insert('rotation_quaternion', frame=f)


def shot_sunday(S):
    """145.44 Make it Sunday: the week again; Tuesday to Saturday come off in one sheet on 'Sunday'. 146.40 make it night: his
    thumb on the lamp's cord switch; on 'night' the lamp goes out and the room is lit by what he made."""
    A = S['A']; tb = S['table']; f0 = F(145.44); fs = F(145.84); fc = F(146.36); fn = F(146.72); f1 = F(147.20); sc = bpy.context.scene; pl = S['planner']; mid = D.objects['PL_MID']; W, H = pl['W'], pl['H']
    type_line(66, split=3, mem=99)
    sc.frame_set(F(139.4)); ang = tb.rotation_euler.z; p0 = V(C.x, C.y, BZ)
    for f in range(f0, F(151.42) + 1): tb.rotation_euler = (0, 0, ang); tb.keyframe_insert('rotation_euler', frame=f); tb.location = p0; tb.keyframe_insert('location', frame=f)
    set_interp(tb, 'CONSTANT', ['location'])
    sc.frame_set(f0 - 1)
    for g in S['guys']: g.keyframe_insert('location', frame=f0 - 1); g.keyframe_insert('rotation_quaternion', frame=f0 - 1)
    for g, Mg in zip(S['guys'], S.get('guy_land', [])): key_w(g, f0, Mg)
    idle(A, f0, f1, (0, .0, IZ + .40), head=(16, 0, 0), lean0=8, L='relax', R='relax')
    Mp = hold_planner(S, f0, fc); top = Mp @ V(0, -.012, H - .03); Rr = RX(rad(-100)); tipv = Rr @ V(0, -.02, -.085)
    A.k(f0, fL=(.2, .2)); A.pose(f0, L=(top + V(-.06, -.06, .03) - tipv, Rr)); A.pose(fs - 4, L=(top - tipv, Rr)); A.k(fs - 3, fL=(1.0, 1.0)); A.pose(fs + 5, L=(top + V(-.07, -.08, .05) - tipv, Rr)); A.k(fs + 7, fL=(.1, .1))
    A.k(fs - 8, look=top); A.hold(fc - 1); A.bake_held(); tear(S, mid, f0, fs, 'L'); key_w(pl, fc, Matrix.Translation((0, 0, -3)))
    c = Mp @ V(0, 0, H / 2)
    shot_cam('C_sunday', f0, fc, c + V(-.03, -.60, .05), c + V(0, 0, .02), loc1=c + V(-.02, -.55, .05), lens=50, fstop=4.0, focus0=c)
    # night
    rk = D.objects['CS_ROCKER']; rp = rk.matrix_world.translation.copy(); Rf = RX(rad(-25)); tipv = Rf @ V(0, -.030, -.092)
    Rf = RX(rad(-25)); tipv = Rf @ V(0, -.030, -.092)
    A.pose(fc, L='relax', R=(rp + V(0, .01, .04) - tipv, Rf), head=(30, 12, 0)); A.k(fc, fR=(1.2, .9, {'index': -.1}), fL=(.15, .15), look=rp)
    A.pose(fn - 1, R=(rp + V(0, -.004, .004) - tipv, Rf)); A.pose(fn + 5, R=(rp + V(0, .02, .05) - tipv, Rf)); A.pose(f1 - 1, R='relax', head=(12, 0, 0)); A.k(fn + 4, look=(0, 0, IZ + .1))
    for f, a in ((fn - 2, rad(10)), (fn, rad(-10))): rk.rotation_euler = (a, 0, 0); rk.keyframe_insert('rotation_euler', frame=f)
    for name in ('KEY', 'CLAUDE_KEY', 'BOUNCE', 'HAIR'):
        l = D.objects[name].data; sc.frame_set(fn - 1); e0 = l.energy
        for f, v in ((fn - 1, e0), (fn + 2, 0.0)): l.energy = v; l.keyframe_insert('energy', frame=f)
    bulb = D.materials['WB_bulb'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength']
    for f, v in ((fn - 1, 90.0), (fn + 2, .3)): bulb.default_value = v; bulb.keyframe_insert('default_value', frame=f)
    nf = wb.light('NIGHT_FILL', 'AREA', (-.3, -1.2, 1.1), 0.0, (.40, .58, 1.0), 1.6, aim=(0, .3, .8)); nf.data.volume_factor = 0
    for f, v in ((fn - 1, 0.0), (fn + 6, 1.8)): nf.data.energy = v; nf.data.keyframe_insert('energy', frame=f)
    A.hold(f1 - 1); A.bake_looks(f0, f1)
    shot_cam('C_night', fc, f1, (0, -1.58, .68), (0, .22, .62), loc1=(0, -1.52, .68), lens=35, fstop=2.0, focus0=(0, .25, .62))


def shot_ontime(S):
    """147.20 Make me feel like I'm on time: a little clock in his hand; one finger turns it back. On 'time' he looks at us.
    151.42 everything stops. 154.40 Out of memory."""
    A = S['A']; f0 = F(147.20); ft = F(149.36); fx = F(151.42); fm = F(154.40); f1 = F(155.34); sc = bpy.context.scene; ck = S['clock']
    type_line(67, split=4, mem=99)
    CS = 1.5; ck.scale = (CS,) * 3; Mc = Matrix.Translation(V(-.115, .185, IZ + .385)) @ RZ(rad(6)) @ RX(rad(-8)); grip = Mc @ V(-.060 * CS, .0, -.01); Rh = RZ(rad(90)) @ RX(rad(-80))
    idle(A, f0, f1, Mc.translation, head=(14, -8, 0), lean0=8, L=(grip + V(-.008, .04, -.01), Rh), R='relax'); A.k(f0, fL=(.9, .9))
    key_w(ck, f0 - 1, Matrix.Translation((0, 0, -3))); key_w(ck, f0, Mc); A.attach(ck, 'hand_L', f0, f1)
    mn = D.objects['CLK_MIN']; hr = D.objects['CLK_HR']
    a0 = rad(-12); mn.rotation_euler = (0, a0, 0); hr.rotation_euler = (0, rad(-1), 0)
    fa = f0 + 12; fb = ft - 4; turns = rad(300); kn = Mc @ V(.0685 * CS, -.012 * CS, 0)                  # he winds it back with the little key on its side
    key = D.objects['CLK_KEY']; wr = kn + V(.082, .030, .012)
    def Rk(a): return RX(rad(112 + a)) @ RY(rad(90))
    A.k(f0, fR=(.9, .9)); A.pose(fa - 6, R=(wr + V(.02, .01, 0), Rk(0)))
    for f in range(fa, fb + 1, 3):
        u = smooth((f - fa) / (fb - fa)); a = a0 - turns * u; mn.rotation_euler = (0, a, 0); mn.keyframe_insert('rotation_euler', frame=f); hr.rotation_euler = (0, rad(-1) - turns * u / 12, 0); hr.keyframe_insert('rotation_euler', frame=f)
        w = 22 * math.sin((f - fa) * .5); key.rotation_euler = (rad(w) + turns * u * 1.5, 0, 0); key.keyframe_insert('rotation_euler', frame=f)
        A.pose(f, R=(wr, Rk(w)))
    A.pose(fb + 8, R=(wr + V(.03, .02, .0), Rk(0))); A.pose(ft + 14, R='relax'); A.k(ft + 14, fR=(.15, .15))
    lens = V(-.03, -.56, IZ + .46)
    A.k(ft - 3, look=lens); A.pose(ft + 1, head=(14, -8, 0)); A.pose(ft + 9, head=(8, -2, 0)); A.k(ft - 3, lids=0.0); A.k(ft + 5, lids=.16); A.blink(F(150.20), base=.16)
    A.hold(fx); A.hold(f1 - 1); A.bake_held(); A.bake_looks(f0, f1)
    shot_cam('C_ontime', f0, fx, lens + V(.05, -.10, -.02), Mc.translation + V(.07, 0, .08), loc1=lens, aim1=Mc.translation + V(.08, 0, .11), lens=40, fstop=2.2, focus0=Mc.translation)
    # the crash: nothing moves but the monitor and his status light
    led = D.materials['Claude_LED'].node_tree.nodes.get('Principled BSDF'); ec = led.inputs['Emission Color']; es = led.inputs['Emission Strength']; g = tuple(ec.default_value)
    for f, c in ((fx - 1, g), (fx, (1.0, .50, .04, 1))): ec.default_value = c; ec.keyframe_insert('default_value', frame=f)
    for f in range(fx, f1, 6): es.default_value = 2.0 + 5.0 * (.5 + .5 * math.sin((f - fx) * .17)); es.keyframe_insert('default_value', frame=f)
    screen(fx, mem=100, l1='not responding', l2='', big='')
    for k, f in enumerate(range(fx + 10, fm - 4, 10)): screen(f, l2='.' * (1 + k % 3))
    type_line(68, mem=100)
    mon = D.objects['MONITOR']; x0, y0, zt, sw, sh = mon['screen']; yaw = mon.rotation_euler.z; n = V(math.sin(yaw), -math.cos(yaw), 0); ctr = mon.location + (RZ(yaw) @ (V(x0 + sw / 2, y0, zt - sh / 2) - mon.location))
    pw = V(0, -1.56, .68); aw = V(0, .22, .62); pend = V(-.30, -.55, .49); aend = V(-.305, .25, .625)      # ends on the two of them: the monitor in front, him frozen behind it
    cam = shot_cam('C_crash', fx, f1, pw, aw, lens=35, fstop=4.0, focus0=(0, .25, .62))
    def K(f, loc, aim, focus, lens_):
        cam.location = loc; wb.look_at(cam, aim); cam.data.dof.focus_distance = (Vector(focus) - Vector(loc)).length; cam.data.lens = lens_
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f); cam.data.keyframe_insert('dof.focus_distance', frame=f); cam.data.keyframe_insert('lens', frame=f)
    fpush = F(151.9)
    K(fpush, pw + V(0, .02, 0), aw, V(0, .25, .62), 35)
    for u in (.2, .4, .6, .8, 1.0):
        e = smooth(u); K(int(fpush + u * (F(154.6) - fpush)), pw.lerp(pend, e), aw.lerp(aend, e), V(0, .25, .62).lerp(ctr, e), 35 - 13 * e)
    K(f1 - 1, pend + V(.003, .010, 0), aend, ctr, 22)


SHOTS_B = []
SHOTS = [shot_city, shot_rain, shot_porsche, shot_lights, shot_guys, shot_wired, shot_pigeons, shot_gravity, shot_everybody, shot_carback, shot_slam, shot_lightup, shot_spin, shot_time, shot_louder, shot_run, shot_montage, shot_moons, shot_ocean, shot_sixty, shot_mondays, shot_sun, shot_vertical, shot_sunday, shot_ontime]


def animate(S, only=None):
    for sh in SHOTS:
        if only and sh.__name__ not in only: continue
        sh(S); print('[film] shot', sh.__name__, 'done', flush=True)
    install_handlers(save=True)
