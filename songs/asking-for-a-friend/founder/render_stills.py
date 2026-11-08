"""Look-dev stills of the founder (Eevee, 1920x1080 by default), in a dark photo studio lit by real sources
(two softboxes, a strip rim, a background spot on the wall), Claude appended from his LOCKED file at true scale.

  Blender -b <founder.blend> --python founder/render_stills.py -- --out <dir> --shots a,b,c
  (add --scratch to render at half samples; --list to print the shots)

Never saves the .blend.
"""
import math, os, sys, json
import numpy as np
import bpy
from mathutils import Matrix, Vector, Quaternion, Euler

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
OUT = opt('--out', '/tmp/x'); SHOTS = (opt('--shots', '') or '').split(',')
SCRATCH = '--scratch' in ARGS
AFF = os.path.expanduser('~/Documents/Original Music/Asking for a Friend 2/blender')
TEX = os.path.join(AFF, 'founder', 'textures')
CLAUDE_BLEND = os.path.join(AFF, 'claude_character_LOCKED_v1.blend')
scene = bpy.context.scene
# the project folder was renamed (13:38): repoint any image still pointing at the old one
for im_ in bpy.data.images:
    if '/Asking for a Friend/' in im_.filepath:
        im_.filepath = im_.filepath.replace('/Asking for a Friend/', '/Asking for a Friend 2/')
rig = bpy.data.objects['FOUNDER_rig']
# marching-cubes meshes are already dense: subdividing them stalls the GPU subdivision; keep it only on the light ones
for o in bpy.data.objects:
    if o.type == 'MESH' and o.get('founder') and not (o.name in ('F_head', 'F_swoop') or o.name.startswith('F_brow')):
        for m in [m for m in o.modifiers if m.type == 'SUBSURF']: o.modifiers.remove(m)

# ---------------------------------------------------------------- render settings
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.resolution_percentage = 100
ee = scene.eevee
for k, v in (('taa_render_samples', 32 if SCRATCH else 96), ('use_raytracing', True), ('use_shadows', True),
             ('shadow_ray_count', 2), ('shadow_step_count', 8), ('use_volumetric_shadows', True),
             ('fast_gi_method', 'GLOBAL_ILLUMINATION'), ('use_fast_gi', True)):
    try: setattr(ee, k, v)
    except Exception as e: print('eevee', k, e)
try: ee.ray_tracing_options.resolution_scale = '1'
except Exception as e: print('rt res', e)
scene.view_settings.view_transform = 'AgX'
try: scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False

# ---------------------------------------------------------------- the set: a dark studio (floor, back wall), real lights
def tex_mat(name, tex, tint, density, rough_add=0.0, normal=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (density,) * 3
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    def img(kind, nc):
        n = N.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(TEX, tex, f'{tex}_{kind}_1k.jpg'), check_existing=True)
        if nc: n.image.colorspace_settings.name = 'Non-Color'
        L.new(mp.outputs['Vector'], n.inputs['Vector']); return n
    d, r, n_ = img('diff', False), img('rough', True), img('nor_gl', True)
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    [i for i in mix.inputs if i.name == 'Factor' and i.type == 'VALUE'][0].default_value = 1.0
    ci = [i for i in mix.inputs if i.type == 'RGBA']; L.new(d.outputs['Color'], ci[0]); ci[1].default_value = tint
    L.new([o for o in mix.outputs if o.type == 'RGBA'][0], b.inputs['Base Color'])
    ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'; ad.inputs[1].default_value = rough_add; ad.use_clamp = True
    L.new(r.outputs['Color'], ad.inputs[0]); L.new(ad.outputs[0], b.inputs['Roughness'])
    nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal
    L.new(n_.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m

setc = bpy.data.collections.new('SET'); scene.collection.children.link(setc)
def add_plane(name, size, loc, rot, mat):
    me = bpy.data.meshes.new(name)
    s = size / 2
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me); setc.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot; me.materials.append(mat)
    return ob
floor_m = tex_mat('SET_floor', 'concrete_floor_02', (0.16, 0.16, 0.17, 1), 0.35, rough_add=0.05, normal=0.6)
wall_m = tex_mat('SET_wall', 'brushed_concrete', (0.10, 0.10, 0.11, 1), 0.4, rough_add=0.1, normal=0.5)
add_plane('SET_floor', 30, (0, 0, 0), (0, 0, 0), floor_m)
add_plane('SET_wall', 30, (0, 4.5, 0), (math.radians(90), 0, 0), wall_m)
scene.world = bpy.data.worlds.new('dark') if scene.world is None else scene.world
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value = (0.004, 0.004, 0.005, 1); bg.inputs['Strength'].default_value = 1.0

def area(name, loc, target, power, size, size_y=None, color=(1, 1, 1), spread=180):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.color = color
    ld.shape = 'RECTANGLE' if size_y else 'SQUARE'; ld.size = size
    if size_y: ld.size_y = size_y
    try: ld.spread = math.radians(spread)
    except Exception: pass
    ob = bpy.data.objects.new(name, ld); setc.objects.link(ob); ob.location = loc
    d = Vector(target) - Vector(loc); ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob
def spot(name, loc, target, power, angle, blend=0.6, color=(1, 1, 1), radius=0.05):
    ld = bpy.data.lights.new(name, 'SPOT'); ld.energy = power; ld.color = color; ld.spot_size = math.radians(angle); ld.spot_blend = blend
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld); setc.objects.link(ob); ob.location = loc
    d = Vector(target) - Vector(loc); ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob

def lights(rig_xy=(0, 0), yaw_cam=0.0):
    """key softbox front-left of camera, fill softbox front-right (low), strip rim behind right, a spot on the back wall.
    Warm key (3600 K-ish), cooler rim: the founder's world is a commercial shoot."""
    for o in [o for o in setc.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o, do_unlink=True)
    cx, cy = rig_xy
    area('L_key', (cx - 2.0, cy - 2.4, 2.5), (cx, cy, 1.45), 380, 1.0, 1.4, (1.0, 0.90, 0.78), spread=110)
    area('L_fill', (cx + 2.4, cy - 2.6, 1.5), (cx, cy, 1.2), 90, 1.6, 1.6, (0.92, 0.95, 1.0), spread=120)
    area('L_rim', (cx + 1.5, cy + 1.9, 2.3), (cx, cy, 1.4), 420, 0.3, 1.6, (0.85, 0.90, 1.0), spread=90)
    area('L_rim2', (cx - 1.7, cy + 1.7, 2.0), (cx, cy, 1.3), 180, 0.3, 1.4, (0.90, 0.92, 1.0), spread=90)
    spot('L_wall', (cx + 0.3, cy + 1.2, 3.6), (cx + 0.2, 4.5, 1.2), 900, 40, 0.8, (1.0, 0.92, 0.85))

# ---------------------------------------------------------------- Claude (appended from his LOCKED file, never edited)
def append_claude():
    with bpy.data.libraries.load(CLAUDE_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n not in ('Camera', 'Fill', 'Key', 'Rim', 'RimL', 'cyc', 'cyc_wall')]
    cc = bpy.data.collections.new('CLAUDE'); scene.collection.children.link(cc)
    for o in dst.objects:
        if o is not None: cc.objects.link(o)
    return bpy.data.objects['CLAUDE'], cc
CLAUDE, CLAUDE_COLL = append_claude()

# ---------------------------------------------------------------- posing helpers
pb = rig.pose.bones
def reset_pose():
    for b in pb:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0); b.scale = (1, 1, 1)
    bpy.context.view_layer.update()

def rot_bone(name, axis, deg):
    """rotate a pose bone about a world axis (applied on top of its current pose)"""
    b = pb[name]; bpy.context.view_layer.update()
    Mw = rig.matrix_world @ b.matrix
    R = Quaternion(Vector(axis).normalized(), math.radians(deg)).to_matrix().to_4x4()
    t = Mw.translation.copy()
    Mn = Matrix.Translation(t) @ R @ Matrix.Translation(-t) @ Mw
    b.matrix = rig.matrix_world.inverted() @ Mn
    bpy.context.view_layer.update()

def aim_bone(name, direction, twist=0.0):
    """point a bone (its y axis) along a world direction, minimal rotation from its current pose, then twist (deg)"""
    b = pb[name]; bpy.context.view_layer.update()
    Mw = rig.matrix_world @ b.matrix
    y = (Mw.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = y.rotation_difference(Vector(direction).normalized())
    t = Mw.translation.copy()
    R = q.to_matrix().to_4x4()
    if twist: R = Quaternion(Vector(direction).normalized(), math.radians(twist)).to_matrix().to_4x4() @ R
    Mn = Matrix.Translation(t) @ R @ Matrix.Translation(-t) @ Mw
    b.matrix = rig.matrix_world.inverted() @ Mn
    bpy.context.view_layer.update()

def head_of(name): bpy.context.view_layer.update(); return rig.matrix_world @ pb[name].head
def tail_of(name): bpy.context.view_layer.update(); return rig.matrix_world @ pb[name].tail

def two_bone(up, lo, target, pole):
    """aim upper/lower bones so the lower bone's tail reaches target, elbow toward pole (world)"""
    S = head_of(up); l1 = (tail_of(up) - S).length; l2 = (tail_of(lo) - head_of(lo)).length
    T = Vector(target); d = T - S; L = min(d.length, l1 + l2 - 1e-4)
    dn = d.normalized()
    a = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L); a = max(-1, min(1, a))
    pv = Vector(pole) - S; pv = (pv - dn * pv.dot(dn)).normalized()
    E = S + dn * (l1 * a) + pv * (l1 * math.sqrt(1 - a * a))
    aim_bone(up, E - S); aim_bone(lo, T - E)

# ---------------------------------------------------------------- face controls
OBJ = bpy.data.objects
head = OBJ['F_head']
def keys(**kw):
    kb = head.data.shape_keys.key_blocks
    for k in kb[1:]: k.value = 0.0
    for k, v in kw.items():
        if k in kb: kb[k].value = v
def brows(**kw):
    for t in ('L', 'R'):
        kb = OBJ['F_brow_' + t].data.shape_keys.key_blocks
        for k in kb[1:]: k.value = 0.0
        for k, v in kw.items():
            if k in kb: kb[k].value = v
def lids(up_deg=None, lo_deg=None):
    for t in ('L', 'R'):
        if up_deg is not None: OBJ['F_lidU_' + t].rotation_euler.x = math.radians(up_deg)
        if lo_deg is not None: OBJ['F_lidD_' + t].rotation_euler.x = math.radians(lo_deg)
def teeth(show):
    for k in ('F_teeth_up', 'F_teeth_lo', 'F_tongue'):
        if k in OBJ: OBJ[k].hide_render = not show
def jaw(deg): pb['jaw'].rotation_mode = 'XYZ'; pb['jaw'].rotation_euler = (math.radians(deg), 0, 0)
def swoop(fallen):
    OBJ['F_swoop'].data.shape_keys.key_blocks['fallen'].value = fallen
def look_at(p):
    lk = OBJ['F_look']; lk.parent = None; lk.location = Vector(p); bpy.context.view_layer.update()

GRIN = dict(smile_L=1.45, smile_R=1.45, upper=1.25, lower=0.25, wide=0.9)
def face_grin():
    teeth(True); keys(**GRIN); jaw(1.0); brows(out=0.35, up=0.1); lids(-26, 40)
def face_gone():
    teeth(False); keys(frown_L=0.7, frown_R=0.7, press=0.35); jaw(0.0); brows(inner=1.0, up=0.25); lids(-8, 44)

from mathutils.kdtree import KDTree
def hide_covered(kind):
    """skin and under-layers that sit right under this outfit's cloth are masked out, so a pose can't push them
    through (rest positions; only verts within 18 mm of the cloth's own verts)"""
    garms = [o for o in bpy.data.collections['FOUNDER_' + kind].objects if o.type == 'MESH' and not o.name.endswith(('tee', 'tank'))]
    pts = []
    for g in garms:
        if g.parent is not rig: continue
        pts += [g.matrix_world @ v.co for i, v in enumerate(g.data.vertices) if i % 3 == 0]
    kd = KDTree(len(pts))
    for i, p in enumerate(pts): kd.insert(p, i)
    kd.balance()
    targets = [OBJ['F_body']] + [o for o in bpy.data.collections['FOUNDER_' + kind].objects if o.name.endswith(('tee', 'tank'))]
    for ob in targets:
        for m in [m for m in ob.modifiers if m.type == 'MASK']: ob.modifiers.remove(m)
        g = ob.vertex_groups.get('covered') or ob.vertex_groups.new(name='covered')
        g.remove(list(range(len(ob.data.vertices))))
        keep = [rig.matrix_world @ rig.data.bones['hand.' + t].head_local for t in ('L', 'R')]   # wrists stay solid: you can see into a sleeve
        idx = [v.index for v in ob.data.vertices if kd.find(ob.matrix_world @ v.co)[2] < 0.018
               and min(((ob.matrix_world @ v.co) - k).length for k in keep) > 0.09]
        g.add(idx, 1.0, 'REPLACE')
        m = ob.modifiers.new('cover', 'MASK'); m.vertex_group = 'covered'; m.invert_vertex_group = True
def outfit(kind):
    if kind == 'quarterzip': hide_covered(kind)    # only the posed outfit needs it; elsewhere it opened holes at open necklines
    else:
        for o in [OBJ['F_body']]:
            for m in [m for m in o.modifiers if m.type == 'MASK']: o.modifiers.remove(m)
    if 'F_robe_robe_piping' in OBJ: OBJ['F_robe_robe_piping'].hide_render = True   # floated in front of the chest; dropped for now
    if 'F_linen_rolls' in OBJ: OBJ['F_linen_rolls'].hide_render = True   # the sleeve's own edge reads as the roll; the extra band floated
    for c in bpy.data.collections:
        if c.name.startswith('FOUNDER_'):
            on = c.name == 'FOUNDER_' + kind
            c.hide_render = not on; c.hide_viewport = not on

def stance():
    """the founder's default: chest up, chin up a hair, arms hanging easy, a touch of weight on his right leg"""
    rot_bone('chest', (1, 0, 0), -3)
    rot_bone('head', (1, 0, 0), -3)
    for t, s in (('L', 1), ('R', -1)):
        rot_bone('upper_arm.' + t, (0, 1, 0), -s * 3)
        rot_bone('forearm.' + t, (1, 0, 0), 10)

# ---------------------------------------------------------------- camera
cam_d = bpy.data.cameras.new('CAM'); cam = bpy.data.objects.new('CAM', cam_d); scene.collection.objects.link(cam); scene.camera = cam
def camera(loc, target, lens=50, fstop=4.0, focus=None):
    cam.location = loc; d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lens; cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36
    cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = fstop
    cam_d.dof.focus_distance = (Vector(focus or target) - Vector(loc)).length
    cam_d.clip_start = 0.05; cam_d.clip_end = 60

def place(x=0.0, y=0.0, yaw=0.0):
    rig.location = (x, y, 0); rig.rotation_euler = (0, 0, math.radians(yaw)); bpy.context.view_layer.update()
def place_claude(x=None, y=0.0, yaw=0.0, show=True):
    CLAUDE_COLL.hide_render = not show
    if x is not None: CLAUDE.location = (x, y, 0); CLAUDE.rotation_euler = (0, 0, math.radians(yaw))
    bpy.context.view_layer.update()

def res(w, h): scene.render.resolution_x, scene.render.resolution_y = w, h

# ---------------------------------------------------------------- shots
def base(kind='quarterzip', yaw=0, x=0.0, claude=False, cx=-0.55):
    reset_pose(); outfit(kind); place(x, 0, yaw); stance(); face_grin(); swoop(0.0)
    place_claude(cx, 0.05, 0, show=claude)
    lights((x, 0))

def cheat_pose(yaw_body=-38):
    """body turned away from the lens, head and eyes cheating back to it, adjusting the watch on his left wrist"""
    place(0, 0, yaw_body)
    rot_bone('chest', (1, 0, 0), -3)
    # left arm: forearm across the body, watch up toward the lens
    rz = math.radians(yaw_body)
    Rz = Matrix.Rotation(rz, 3, 'Z')
    sh = head_of('upper_arm.L')
    # the upper arm stays almost where it hangs (only 18 deg forward), the elbow does the work: the forearm comes up
    # across the front of the body, so the knit at the shoulder and the lat isn't dragged
    aim_bone('upper_arm.L', Rz @ Vector((0.10, -0.32, -0.94)))
    camp = Vector(cam.location)
    rest = rig.data.bones['forearm.L'].matrix_local
    fdir = Rz @ Vector((-0.70, -0.62, 0.30))
    best = None
    for tw in range(-180, 180, 10):
        aim_bone('forearm.L', fdir, twist=tw)
        M = rig.matrix_world @ pb['forearm.L'].matrix
        out_w = (M.to_3x3() @ rest.to_3x3().inverted() @ Vector((1, 0, 0))).normalized()   # the dial's facing
        wc = tail_of('forearm.L')
        sc = out_w.dot((camp - wc).normalized()) + 0.5 * out_w.z
        if best is None or sc > best[0]: best = (sc, tw)
        aim_bone('forearm.L', fdir, twist=-tw)       # undo (twist is applied about the same axis)
    aim_bone('forearm.L', fdir, twist=best[1])
    print('watch twist', best)
    aim_bone('hand.L', (tail_of('forearm.L') - head_of('forearm.L')).normalized() * 0.9 + Rz @ Vector((0, -0.1, -0.3)))
    # right hand: fingertips onto the watch case
    wc = tail_of('forearm.L') - (tail_of('forearm.L') - head_of('forearm.L')).normalized() * 0.03
    two_bone('upper_arm.R', 'forearm.R', wc + Rz @ Vector((-0.10, -0.07, 0.06)), head_of('upper_arm.R') + Rz @ Vector((-0.35, 0.25, -0.6)))
    aim_bone('hand.R', wc - tail_of('forearm.R'))
    # head cheats back to the lens
    rot_bone('neck', (0, 0, 1), -yaw_body * 0.35)
    rot_bone('head', (0, 0, 1), -yaw_body * 0.55)
    rot_bone('head', (1, 0, 0), -4)
    look_at(cam.location)

SHOT = {}
def shot(fn): SHOT[fn.__name__] = fn; return fn

@shot
def lineup_front():
    base(claude=True, x=0.42, cx=-0.50)
    camera((0, -5.4, 1.02), (0, 0, 0.98), lens=42, fstop=8.0, focus=(0, 0, 1.0)); look_at(cam.location)

@shot
def lineup_34():
    base(claude=True, x=0.40, yaw=12, cx=-0.48)
    CLAUDE.rotation_euler = (0, 0, math.radians(-12))
    camera((-2.7, -4.6, 1.1), (0, 0, 0.98), lens=45, fstop=8.0, focus=(0.0, 0, 1.0)); look_at(cam.location)

@shot
def lineup_true_scale():
    base(claude=True, x=0.40, yaw=0, cx=-0.40)
    camera((0, -9.0, 0.95), (0, 0, 0.95), lens=80, fstop=11.0); look_at(cam.location)

def turn(yaw, name):
    res(480, 1080)
    base(yaw=yaw)
    camera((0, -7.2, 1.0), (0, 0, 0.96), lens=70, fstop=11.0)
    if abs(yaw) < 100: look_at(cam.location)
    else: look_at((0, 3.0, 1.7))
for yaw, nm in ((0, 'turn_front'), (40, 'turn_34'), (90, 'turn_side'), (180, 'turn_back')):
    SHOT[nm] = (lambda yaw=yaw, nm=nm: turn(yaw, nm))

@shot
def grin():
    base(yaw=-18)
    camera((-0.10, -1.45, 1.76), (0.0, 0.0, 1.71), lens=85, fstop=2.8, focus=(0.0, -0.10, 1.72)); look_at(cam.location)

def mask_cuffs():
    """the rib cuff bands don't follow a bent wrist yet (they fold into a disc), so posed shots show the knit's own
    sleeve end instead"""
    ob = OBJ.get('F_quarterzip_qz_rib')
    if ob is None: return
    g = ob.vertex_groups.get('cuffs') or ob.vertex_groups.new(name='cuffs')
    g.add([v.index for v in ob.data.vertices if abs(v.co.x) > 0.2], 1.0, 'REPLACE')
    if not any(m.type == 'MASK' for m in ob.modifiers):
        m = ob.modifiers.new('cuffs', 'MASK'); m.vertex_group = 'cuffs'; m.invert_vertex_group = True

@shot
def cheat():
    base()
    mask_cuffs()
    camera((0.30, -2.3, 1.40), (0.0, 0.0, 1.50), lens=55, fstop=3.2, focus=(0.0, -0.1, 1.55))
    reset_pose(); cheat_pose(-38); face_grin(); brows(out=0.5, up=0.25); lids(-24, 40)
    cam_d.dof.focus_distance = (Vector(cam.location) - Vector((0.05, -0.05, 1.65))).length

@shot
def watch_cu():
    cheat()
    w = OBJ['F_watch_dial']; bpy.context.view_layer.update()
    wc = tail_of('forearm.L')
    wc = wc + (tail_of('forearm.L') - head_of('forearm.L')).normalized() * 0.012
    camera(tuple(wc + Vector((0.30, -0.80, 0.34))), tuple(wc), lens=85, fstop=5.6, focus=tuple(wc))

@shot
def unfollow():
    base(yaw=-12)
    rot_bone('neck', (1, 0, 0), 6); rot_bone('head', (1, 0, 0), 8)
    face_gone(); swoop(1.0)
    camera((-0.12, -1.55, 1.80), (0.0, 0.0, 1.73), lens=75, fstop=2.8, focus=(0.0, -0.10, 1.72))
    look_at((0.25, -0.9, 1.05))

@shot
def swoop_cu():
    base(yaw=-35)
    camera((-0.55, -1.05, 2.05), (0.0, -0.02, 1.78), lens=85, fstop=3.5, focus=(0.0, -0.06, 1.80)); look_at(cam.location)

@shot
def grin_9x16():
    res(1080, 1920)
    base(claude=True, x=0.22, cx=-0.30, yaw=10)
    camera((0, -4.2, 1.05), (0, 0, 1.0), lens=30, fstop=8.0); look_at(cam.location)

def ward(kind, yaw=-28, face='grin'):
    def f():
        res(960, 1080); base(kind, yaw=yaw)
        camera((-1.1, -5.0, 1.02), (0, 0, 0.97), lens=50, fstop=8.0, focus=(0, 0, 1.2)); look_at(cam.location)
        if kind == 'pyjamas': face_grin(); lids(-60, 40)
    return f
def ward_cu(kind, yaw=-28):
    def f():
        res(960, 1080); base(kind, yaw=yaw)
        camera((-0.55, -1.75, 1.45), (0, 0, 1.40), lens=60, fstop=3.5, focus=(0.0, -0.12, 1.45)); look_at(cam.location)
    return f
for k in ('quarterzip', 'robe', 'goggles', 'linen', 'pyjamas'):
    SHOT['ward_' + k] = ward(k); SHOT['wardcu_' + k] = ward_cu(k)

@shot
def wardrobe_line():
    res(1920, 1080)
    base('quarterzip')   # (composited from the ward_* renders instead)

if '--list' in ARGS:
    print('SHOTS', ' '.join(SHOT)); raise SystemExit
os.makedirs(OUT, exist_ok=True)
for name in SHOTS:
    if not name: continue
    res(1920, 1080)
    SHOT[name]()
    scene.render.filepath = os.path.join(OUT, name + '.png')
    if '--dry' in ARGS: print('dry', name, flush=True); continue
    bpy.ops.render.render(write_still=True)
    print('rendered', scene.render.filepath, flush=True)
