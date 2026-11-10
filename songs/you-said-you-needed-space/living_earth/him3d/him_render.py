"""him_render.py: poses "him", lights him like the plate he goes over, renders RGBA (Eevee). Look-dev (Nov 9).
  Blender -b him.blend --python him_render.py -- <job.json>
The camera sits at the origin looking down -Z with +Y up: Blender camera space = the film engine's view space
(remotion/src/le/film/types.ts `sun`: view space, z toward the camera), so a shot's `sun` vector is used as is.
Every pose is a pure function of time (act(t)); nothing is keyed, frames can render in any order.
"""
import bpy, json, math, os, sys
from mathutils import Matrix, Vector, Euler

R = math.radians
TAN = 18.0 / 50.0   # half sensor / focal length
SPAN = 5.37         # his wingspan in model units (wings flat)
HER = (0.15, 0.95, 1.0)

def ob(n): return bpy.data.objects[n]
def clamp01(x): return max(0.0, min(1.0, x))
def smooth(a, b, x):
    u = clamp01((x - a) / (b - a)) if b != a else float(x >= b); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def settle(u, k=6.0, w=14.0):
    """0 -> 1 with a damped overshoot, zero slope at u = 0 (animation-principles 2)."""
    if u <= 0: return 0.0
    return 1 - math.exp(-k * u) * (math.cos(w * u) + (k / w) * math.sin(w * u))
def move(t, t0, dur, ant=0.2, amt=0.18):
    """hold -> anticipation (the other way) -> action with overshoot -> settle. Returns ~0..1 (dips to -amt first)."""
    if t < t0 - ant: return 0.0
    if t < t0: u = (t - (t0 - ant)) / ant; return -amt * math.sin(u * math.pi / 2) ** 2
    u = (t - t0) / dur; s = settle(u * 0.55, 5.0, 9.0)
    return lerp(-amt, 1.0, s) if u < 6 else 1.0
def spring_at(t, target, k=90.0, c=9.0, dt=1 / 120):
    x, v = target(0.0), 0.0; n = int(t / dt)
    for i in range(n):
        s = i * dt; v += (k * (target(s) - x) - c * v) * dt; x += v * dt
    h = t - n * dt; v += (k * (target(n * dt) - x) - c * v) * h; x += v * h
    return x
def nz(t, seed, f=0.23):
    """smooth seeded drift in -1..1 (sum of sines: a pure function of time)."""
    return (math.sin(t * f * 6.283 + seed * 1.7) + 0.6 * math.sin(t * f * 2.31 * 6.283 + seed * 4.1) + 0.3 * math.sin(t * f * 4.07 * 6.283 + seed * 9.3)) / 1.9

REST = dict(
    yaw=0.0, pitch=0.0, roll=0.0, dz=0.0, lean=0.0,
    head_pan=0.0, head_tilt=0.0, head_roll=0.0, brow_tilt=0.0, brow_roll=0.0, lid=0.0, pupil=(0.0, 0.0), pupil_size=1.0,
    wingL=dict(twist=0.0, flap=5.0, fold=(-3.0, 2.0, 3.0)), wingR=dict(twist=0.0, flap=5.0, fold=(-3.0, 2.0, 3.0)),
    dish_az=25.0, dish_el=38.0, whip=(0.0, 0.0), leds=(1.0, 1.0, 1.0), beacon=1.0, eye=1.0,
)

def merged(P):
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in REST.items()}
    for k, v in (P or {}).items():
        if isinstance(v, dict): out[k].update(v)
        else: out[k] = v
    return out

def apply_pose(P):
    P = merged(P)
    b = ob('HIM_bob'); b.location = (0, 0, P['dz']); b.rotation_euler = (R(P['lean']), 0, 0)
    ob('HIM_neck').rotation_euler = (0, 0, R(P['head_pan']))
    ob('HIM_head').rotation_euler = (R(P['head_tilt']), R(P['head_roll']), 0)
    ob('HIM_brow').rotation_euler = (R(P['brow_tilt']), R(P['brow_roll']), 0)
    if 'HIM_lid' in bpy.data.objects: ob('HIM_lid').scale = (1, 1, max(0.02, P['lid']))
    px, pz = P['pupil']; r2 = px * px + pz * pz
    ob('HIM_pupil').location = (px, -0.335 - 0.42 * math.sqrt(max(0.0, 0.168 ** 2 - r2)) + 0.002, 0.27 + pz)
    s = P['pupil_size']; ob('HIM_pupil').scale = (s, 1, s)
    for nm, sg in (('L', 1), ('R', -1)):
        w = P['wing' + nm]; ob('HIM_wing' + nm).rotation_euler = (R(w['twist']), R(-sg * w['flap']), 0)
        for i in range(3): ob(f'HIM_wing{nm}_h{i}').rotation_euler = (0, 0, R(-sg * w['fold'][i]))
    ob('HIM_dish_az').rotation_euler = (0, 0, R(P['dish_az'])); ob('HIM_dish_el').rotation_euler = (R(P['dish_el']), 0, 0)
    wx, wy = P['whip']
    for i in range(5): ob(f'HIM_whip{i}').rotation_euler = (R(wx * (0.4 + 0.3 * i)), R(wy * (0.4 + 0.3 * i)), 0)
    apply_pose_lights(P)

def apply_pose_lights(P):
    """the part of a pose that is light, not transform (him_slots.py sets it per frame; transforms come from baked keys)"""
    def emit(mat, v):
        n = next(n for n in bpy.data.materials[mat].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); n.inputs['Emission Strength'].default_value = v
    for i in range(3): emit(f'HIM_ledmat{i}', 5.0 * P['leds'][i])
    emit('HIM_beaconmat', 12.0 * P['beacon']); emit('HIM_eye', 7.0 * P['eye']); emit('HIM_pupilmat', 8.0 * P['eye'])
    bpy.data.lights['HIM_eyelight'].energy = 2.2 * P['eye']

def idle(t, P=None):
    """Alive is never static: breath, per-wing drift, a scanning dish, eye saccades, the beacon."""
    P = merged(P)
    P['dz'] += 0.018 * math.sin(t * 6.283 / 4.5); P['lean'] += 1.2 * math.sin(t * 6.283 / 4.5 + 0.8)
    for i, nm in enumerate(('L', 'R')):
        w = P['wing' + nm]; w['flap'] += 1.8 * nz(t, 3 + 5 * i); w['twist'] += 2.0 * nz(t, 11 + 5 * i, 0.17)
        w['fold'] = tuple(f + 1.5 * nz(t - 0.12 * j, 20 + 7 * i + j, 0.3) for j, f in enumerate(w['fold']))
    P['dish_az'] += 4 * nz(t, 40, 0.15); P['dish_el'] += 2.5 * nz(t, 41, 0.2)
    P['head_roll'] += 1.2 * nz(t, 50, 0.2)
    sx = 0.012 * round(1.5 * nz(t, 60, 0.45)); P['pupil'] = (P['pupil'][0] + sx, P['pupil'][1])
    ph = (t % 1.3) / 1.3; P['beacon'] *= 0.12 + 1.6 * math.exp(-((ph - 0.08) / 0.05) ** 2)
    return P

def act(t):
    """The acting test (5 s): idle -> notices us (take) -> a wing flourish -> smug brow -> looks beyond. Slow turn throughout."""
    P = merged(None)
    P['yaw'] = lerp(-38, 34, smooth(0.0, 5.0, t)) ; P['pitch'] = 6 + 3 * math.sin(t * 0.9); P['roll'] = -6 + 2.5 * nz(t, 2, 0.12)
    # 1. the take: he is looking off; hears us; head snaps round (anticipation the other way first), dish follows 4 frames later
    a = move(t, 1.15, 0.30, ant=0.22, amt=0.22); a2 = move(t, 1.15 + 4 / 30, 0.36, ant=0.2, amt=0.15)
    look_cam = -P['yaw']                                             # the pan that keeps his eye on the camera as he turns
    P['head_pan'] = lerp(-P['yaw'] - 52, look_cam, a); P['head_tilt'] = lerp(10, -4, a)
    P['dish_az'] = lerp(140, 20 - P['yaw'] * 0.6, a2); P['dish_el'] = lerp(30, 52, a2)
    P['brow_tilt'] = lerp(4, -16, move(t, 1.2, 0.22, ant=0.1, amt=0.5))   # brow lifts: surprise
    P['pupil_size'] = lerp(0.85, 1.25, smooth(1.15, 1.4, t))
    # 2. the flourish: wings pull in (anticipation), then throw wide, a wave running root -> tip, status lights chase
    for i, nm in enumerate(('L', 'R')):
        w = P['wing' + nm]; d = 0.05 * i
        fl = move(t, 2.25 + d, 0.34, ant=0.3, amt=0.55); back = smooth(3.0, 3.9, t)
        w['flap'] = lerp(5, 21, fl) - 11 * back
        w['fold'] = tuple(lerp(f, f - 13 - 5 * j, move(t, 2.25 + d + 0.07 * j, 0.34, ant=0.3, amt=0.9)) + (9 + 4 * j) * back * 0.8 for j, f in enumerate(w['fold']))
        w['twist'] = 14 * math.sin(clamp01((t - 2.2 - d) / 0.9) * math.pi) * (1 if i == 0 else -1)
    hop = math.sin(clamp01((t - 2.22) / 0.55) * math.pi); P['dz'] += 0.07 * hop - 0.03 * math.sin(clamp01((t - 1.95) / 0.27) * math.pi)
    P['leds'] = tuple(0.35 + 1.5 * math.exp(-(((t - 2.3 - 0.11 * j) % 5.0) / 0.12) ** 2) + 0.65 * smooth(2.9, 3.2, t) for j in range(3))
    # 3. smug: one brow corner cocks, the head tips
    sm = move(t, 3.35, 0.3, ant=0.15, amt=0.2) * (1 - smooth(4.15, 4.4, t))
    P['brow_tilt'] += 24 * sm; P['brow_roll'] = 11 * sm; P['head_roll'] = 9 * sm; P['pupil'] = (0.0, -0.02 * sm)
    # 4. looks beyond: up and away, the dish first this time (it hears it before he looks)
    g = move(t, 4.3, 0.4, ant=0.2, amt=0.12); g0 = move(t, 4.18, 0.4, ant=0.15, amt=0.1)
    P['head_pan'] += 42 * g; P['head_tilt'] += -22 * g; P['dish_az'] += 55 * g0; P['dish_el'] += -20 * g0; P['brow_tilt'] += -10 * g
    # follow-through: the whip lags every turn of the head and every hop
    drive = lambda s: (move(s, 1.15, 0.30, 0.22, 0.22) + 0.7 * move(s, 2.25, 0.34, 0.3, 0.55) + 0.6 * move(s, 4.3, 0.4, 0.2, 0.12))
    lag = spring_at(t, drive, 70.0, 5.0) - drive(t)
    P['whip'] = (10 * lag + 2 * nz(t, 70), 26 * lag + 2 * nz(t, 71))
    return idle(t, P)

# ----------------------------------------------------------------------------- the shot: camera, sun, her light
def setup_scene(res, samples):
    sc = bpy.context.scene
    for e in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try: sc.render.engine = e; break
        except TypeError: pass
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.color_depth = '16'
    ee = sc.eevee
    for k, v in (('taa_render_samples', samples), ('use_raytracing', True), ('use_shadows', True), ('use_gtao', True)):
        try: setattr(ee, k, v)
        except Exception as ex: print('[eevee] skip', k, ex)
    try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception as ex:
        print('[view] look fallback', ex)
        try: sc.view_settings.look = 'Medium High Contrast'
        except Exception: pass
    if 'HIM_cam' not in bpy.data.objects:
        cd = bpy.data.cameras.new('HIM_cam'); cd.lens = 50; cd.sensor_width = 36; cd.clip_start = 0.05; cd.clip_end = 500
        co = bpy.data.objects.new('HIM_cam', cd); sc.collection.objects.link(co); sc.camera = co
        for nm, ang in (('HIM_sun', R(1.0)), ('HIM_earthshine', R(70))):
            ld = bpy.data.lights.new(nm, 'SUN'); ld.angle = ang; lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo); lo.rotation_mode = 'QUATERNION'
        w = bpy.data.worlds.new('HIM_world'); w.use_nodes = True; sc.world = w; nt = w.node_tree; L = nt.links.new
        bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
        tc = nt.nodes.new('ShaderNodeTexCoord'); dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.name = 'earth_dot'
        L(tc.outputs['Generated'], dot.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.15; mr.inputs['From Max'].default_value = 1.0; L(dot.outputs['Value'], mr.inputs['Value'])
        pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.4; L(mr.outputs['Result'], pw.inputs[0])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.name = 'her_mix'
        mx.inputs[6].default_value = (0.010, 0.012, 0.022, 1); mx.inputs[7].default_value = (*HER, 1)
        L(pw.outputs[0], mx.inputs[0]); L(mx.outputs[2], bg.inputs['Color'])
    return sc

def light_shot(sun, sun_energy, earth, earth_energy, her_world, her_color=(0.50, 0.86, 1.0), exposure=0.5, lamps=1.0):
    s = Vector(sun).normalized(); e = Vector(earth).normalized()
    so = ob('HIM_sun'); so.rotation_quaternion = s.to_track_quat('Z', 'Y'); so.data.energy = sun_energy; so.data.color = (1.0, 0.94, 0.86)
    eo = ob('HIM_earthshine'); eo.rotation_quaternion = e.to_track_quat('Z', 'Y'); eo.data.energy = earth_energy; eo.data.color = her_color; bpy.context.scene.view_settings.exposure = exposure
    for nm in ('L', 'R'): bpy.data.lights['HIM_lamplight' + nm].energy = 5.0 * lamps
    try: eo.data.use_shadow = False
    except Exception: pass
    nt = bpy.context.scene.world.node_tree
    nt.nodes['earth_dot'].inputs[1].default_value = tuple(e)
    nt.nodes['her_mix'].inputs[7].default_value = (her_color[0] * her_world, her_color[1] * her_world, her_color[2] * her_world, 1)

def view_matrix(px, span_px, d, yaw, pitch, roll, units, base=2560.0, aspect=9 / 16):
    """Place a model so its `units` wide reference spans span_px (in a 2560-wide frame) at pixel px, d from the camera."""
    x = (px[0] / base * 2 - 1) * TAN * d; y = -(px[1] / (base * aspect) * 2 - 1) * TAN * d * aspect
    sc = span_px / base * 2 * TAN * d / units
    Rv = Matrix.Rotation(R(roll), 4, 'Z') @ Matrix.Rotation(R(pitch), 4, 'X') @ Matrix.Rotation(R(yaw), 4, 'Y')
    return Matrix.Translation((x, y, -d)) @ Rv @ Matrix.Rotation(R(-90), 4, 'X') @ Matrix.Diagonal((sc, sc, sc, 1))

def hide_tree(root, hide):
    for o in [root] + list(root.children_recursive): o.hide_render = hide

def do_render(job, r, t=None, out=None):
    light_shot(r.get('sun', [0.85, 0.25, -0.46]), r.get('sun_energy', 8.0), r.get('earth', [0, -1, -0.2]), r.get('earth_energy', 0.35), r.get('her_world', 0.14), tuple(r.get('her_color', (0.50, 0.86, 1.0))), r.get('exposure', 0.5), r.get('lamps', 1.0))
    him, rk = ob('HIM_root'), ob('RKT_root'); him.rotation_mode = 'XYZ'
    P = act(t) if (t is not None and not r.get('pose_fn')) else merged(r.get('pose'))
    if r.get('idle_t') is not None: P = idle(r['idle_t'], P)
    apply_pose(P)
    if r.get('rocket'):
        k = r['rocket']; hide_tree(rk, False); rk.matrix_world = view_matrix(k['px'], k['len_px'], k.get('d', 40), k.get('yaw', 0), k.get('pitch', 0), k.get('roll', 0), 9.0)
        him.parent = ob('RKT_seat'); him.matrix_parent_inverse = Matrix.Identity(4); him.location = (0, 0, 0); him.rotation_euler = (0, 0, R(90)); him.scale = (1, 1, 1)
        ob('RKT_fairingA').rotation_euler = (0, R(k.get('open', 42)), 0); ob('RKT_fairingB').rotation_euler = (0, R(-k.get('open', 42)), 0)
        if not k.get('fairing', False): hide_tree(ob('RKT_fairingA'), True); hide_tree(ob('RKT_fairingB'), True)
        hide_tree(ob('RKT_flame'), not k.get('flame', True)); ob('RKT_flame').scale = (1, 1, k.get('flame_len', 0.42)); bpy.data.lights['RKT_flamelight'].energy = k.get('flame_light', 900)
    else:
        hide_tree(rk, True); him.parent = None
        h = r['him']; him.matrix_world = view_matrix(h['px'], h['span_px'], h.get('d', 14), P['yaw'] + h.get('yaw', 0), P['pitch'] + h.get('pitch', 0), P['roll'] + h.get('roll', 0), SPAN)
    hide_tree(him, False)
    sc = bpy.context.scene; sc.render.filepath = out or r['out']
    bpy.ops.render.render(write_still=True)
    print('[him_render] wrote', sc.render.filepath, flush=True)

def main(path):
    job = json.load(open(path))
    for r in job.get('renders', []):
        setup_scene(r.get('res', job.get('res', [2560, 1440])), r.get('samples', job.get('samples', 64)))
        do_render(job, r)
    c = job.get('clip')
    if c:
        setup_scene(c['res'], c.get('samples', 32)); os.makedirs(c['out_dir'], exist_ok=True)
        for f in range(c.get('first', 0), c['frames']):
            out = os.path.join(c['out_dir'], f'him_{f:04d}.png')
            if os.path.exists(out) and c.get('resume', True): continue
            do_render(job, c, t=f / c.get('fps', 30), out=out)

if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1])
