"""Ground v2 for the Living Earth pitch ("I've got all the life down here"): a night jungle floor from CC0 library assets
(Poly Haven calathea_orbifolia_01, fern_02, moss_01, rock_moss_set_01, pine_roots; textures mud_forest, roots, mossy_rock;
ambientCG Moss002), leaves translucent with the glow carried by their own veins and edges (masks from prep_tex.py),
wet coat + dew, real depth of field.  Renders on alpha as a multilayer EXR (Combined, Depth, Emit) and dumps an .npz
for the CPU comp (comp2.py: sky, mist by depth, motes, bloom from the Emit pass, grade).
Run: Blender -b --factory-startup --python ground2.py -- <scale> <out_prefix> <layer: main|fg> [samples]"""
import bpy, sys, math, random, bmesh
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
SC = float(argv[0]); OUT = argv[1]; LAYER = argv[2]; SAMPLES = int(argv[3]) if len(argv) > 3 else 24
from pathlib import Path
ROOT = str(Path(__file__).resolve().parents[4]) + '/'
LIB = ROOT + 'assets/earth_library/polyhaven/'
ACG = ROOT + 'assets/earth_library/ambientcg/'
TEX = ROOT + 'songs/you-said-you-needed-space/build/pitch_mockups/ground2/tex/'
random.seed(1108)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = eng; break
    except TypeError as e:
        print('engine', eng, 'no:', e)
print('ENGINE', scene.render.engine)

TEAL = (0.01, 0.72, 0.74, 1); CYAN = (0.12, 0.78, 1.0, 1); VIOLET = (0.42, 0.16, 1.0, 1); MAGENTA = (0.90, 0.16, 0.80, 1)


# ---------------------------------------------------------------- node helpers
def S(nt, v):
    return v


def mth(nt, op, a, b=None, c=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b, c)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def rng(nt, x, a, b, lo=0.0, hi=1.0):
    n = nt.nodes.new('ShaderNodeMapRange'); n.interpolation_type = 'SMOOTHSTEP'
    nt.links.new(x, n.inputs['Value'])
    n.inputs['From Min'].default_value = a; n.inputs['From Max'].default_value = b
    n.inputs['To Min'].default_value = lo; n.inputs['To Max'].default_value = hi
    return n.outputs[0]


def mixc(nt, f, a, b, blend='MIX'):
    n = nt.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = blend
    for idx, v in ((0, f), (6, a), (7, b)):
        if isinstance(v, (int, float)): n.inputs[idx].default_value = v
        elif isinstance(v, tuple): n.inputs[idx].default_value = v
        else: nt.links.new(v, n.inputs[idx])
    return n.outputs[2]


def noise(nt, vec, scale, detail=2.0):
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail
    if vec is not None: nt.links.new(vec, n.inputs['Vector'])
    return n.outputs[0]


def image(nt, path, cs='Non-Color', vec=None, box=False):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path, check_existing=True)
    t.image.colorspace_settings.name = cs
    if box: t.projection = 'BOX'; t.projection_blend = 0.35
    if vec is not None: nt.links.new(vec, t.inputs['Vector'])
    return t


def sep(nt, col):
    n = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(col, n.inputs[0]); return n.outputs


def base_tex(mat):
    bs = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None: return None, None
    n = bs.inputs['Base Color'].links[0].from_node if bs.inputs['Base Color'].links else None
    seen = 0
    while n is not None and n.type != 'TEX_IMAGE' and seen < 6:
        nxt = None
        for i in n.inputs:
            if i.links: nxt = i.links[0].from_node; break
        n = nxt; seen += 1
    return bs, n


def set_in(bs, name, v):
    try: bs.inputs[name].default_value = v
    except Exception as e: print('no input', name, e)


def wet(nt, bs, rough_mul=0.5, coat=0.8):
    for l in list(bs.inputs['Roughness'].links):
        nt.links.new(mth(nt, 'MULTIPLY', l.from_socket, rough_mul), bs.inputs['Roughness'])
    set_in(bs, 'Coat Weight', coat); set_in(bs, 'Coat Roughness', 0.06); set_in(bs, 'Coat IOR', 1.33)


# ---------------------------------------------------------------- the leaf: translucent, veins + edges carry the light
def leaf(mat, plant, use_alpha, k_vein, k_edge, k_trans):
    bs, tex = base_tex(mat)
    nt = mat.node_tree; N = nt.nodes; L = nt.links
    out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    g = sep(nt, image(nt, f'{TEX}{plant}_glow.png').outputs['Color'])       # R fine veins, G broad bands, B edge
    vein, band, edge = g[0], g[1], g[2]
    oi = N.new('ShaderNodeObjectInfo'); oc = sep(nt, oi.outputs['Color'])    # object colour: R = glow gain, G = hue (0 cyan .. 1 violet)
    gain, hue = oc[0], oc[1]
    geo = N.new('ShaderNodeNewGeometry')
    if plant.startswith('calathea'):
        mm = sep(nt, image(nt, f'{TEX}{plant}_mid.png').outputs['Color']); midprox, midline = mm[0], mm[1]
    else:
        midprox, midline = band, mth(nt, 'MULTIPLY', vein, 0.0)
    # body: the plant's own albedo, pulled to deep teal (or violet) and kept dark
    bw = N.new('ShaderNodeRGBToBW'); L.new(tex.outputs['Color'], bw.inputs[0])
    lum = mth(nt, 'MULTIPLY', bw.outputs[0], 4.0)                    # the albedo's own light/dark pattern, re-tinted
    L.new(mixc(nt, 1.0, mixc(nt, hue, (0.02, 0.26, 0.34, 1), (0.20, 0.05, 0.42, 1)), lum, 'MULTIPLY'), bs.inputs['Base Color'])
    # wet sheen + dew: a clear coat, low roughness, a few beaded drops (bump + mirror-smooth) to catch the cool rim light
    uv = N.new('ShaderNodeTexCoord')
    vor = N.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 110.0; L.new(uv.outputs['UV'], vor.inputs['Vector'])
    pick = rng(nt, sep(nt, vor.outputs['Color'])[0], 0.93, 0.95)
    drop = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', rng(nt, vor.outputs['Distance'], 0.26, 0.10), pick), oc[2])
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 1.0; bump.inputs['Distance'].default_value = 0.004
    L.new(drop, bump.inputs['Height'])
    for l in list(bs.inputs['Normal'].links): L.new(l.from_socket, bump.inputs['Normal'])
    L.new(bump.outputs[0], bs.inputs['Normal'])
    try: L.new(bump.outputs[0], bs.inputs['Coat Normal'])
    except Exception as e: print('coat normal', e)
    rsrc = bs.inputs['Roughness'].links[0].from_socket if bs.inputs['Roughness'].links else None
    r0 = mth(nt, 'MULTIPLY', rsrc, mth(nt, 'MULTIPLY_ADD', oc[2], -0.5, 1.05)) if rsrc is not None else 0.3
    L.new(mth(nt, 'MULTIPLY', r0, mth(nt, 'SUBTRACT', 1.0, drop)), bs.inputs['Roughness'])
    L.new(mth(nt, 'MULTIPLY_ADD', oc[2], 0.9, 0.1), bs.inputs['Coat Weight']); set_in(bs, 'Coat Roughness', 0.05); set_in(bs, 'Coat IOR', 1.33)
    # glow: fine veins + the edge band, patchy from leaf to leaf, never the whole sheet
    patch = mth(nt, 'MULTIPLY', rng(nt, noise(nt, geo.outputs['Position'], 2.5), 0.36, 0.66, 0.30, 1.0), rng(nt, noise(nt, geo.outputs['Position'], 14.0, 3.0), 0.30, 0.70, 0.50, 1.0))
    vsharp = mth(nt, 'POWER', vein, 1.7)
    e = mth(nt, 'ADD', mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', vsharp, k_vein), mth(nt, 'MULTIPLY_ADD', midprox, 0.65, 0.50)), mth(nt, 'MULTIPLY', mth(nt, 'POWER', edge, 1.5), k_edge))
    e = mth(nt, 'ADD', e, mth(nt, 'ADD', mth(nt, 'MULTIPLY', midline, 2.6), mth(nt, 'MULTIPLY', midprox, 0.07)))
    e = mth(nt, 'ADD', e, mth(nt, 'MULTIPLY', band, 0.10))
    net = N.new('ShaderNodeTexVoronoi'); net.feature = 'DISTANCE_TO_EDGE'; net.inputs['Scale'].default_value = 140.0; L.new(uv.outputs['UV'], net.inputs['Vector'])
    netm = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', rng(nt, net.outputs['Distance'], 0.035, 0.0), rng(nt, noise(nt, uv.outputs['UV'], 22.0, 3.0), 0.38, 0.62, 0.15, 1.0)), mth(nt, 'SUBTRACT', 1.0, mth(nt, 'POWER', edge, 0.35), clamp=True))
    e = mth(nt, 'ADD', e, mth(nt, 'MULTIPLY', netm, 0.34))
    e = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', e, patch), gain)
    L.new(e, bs.inputs['Emission Strength'])
    hot = rng(nt, vein, 0.3, 1.0)
    ca = mixc(nt, hot, TEAL, CYAN); cb = mixc(nt, hot, VIOLET, MAGENTA)
    L.new(mixc(nt, mth(nt, 'MULTIPLY', netm, mth(nt, 'SUBTRACT', 1.0, hot)), mixc(nt, hue, ca, cb), (0.04, 0.90, 0.50, 1)), bs.inputs['Emission Color'])
    # translucency: light from behind comes through the blade, more through the pale bands, less through the veins
    tr = N.new('ShaderNodeBsdfTranslucent')
    tk = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY_ADD', band, 0.60, 0.40), mth(nt, 'MULTIPLY_ADD', vein, -0.6, 1.0))
    tk = mth(nt, 'MULTIPLY', tk, mth(nt, 'MULTIPLY_ADD', midprox, 1.1, 0.45))
    L.new(mixc(nt, 1.0, mixc(nt, hue, (0.02, 0.60, 0.85, 1), (0.50, 0.12, 0.95, 1)), mth(nt, 'MULTIPLY', lum, mth(nt, 'MULTIPLY', tk, k_trans * 1.5)), 'MULTIPLY'), tr.inputs['Color'])
    L.new(bump.outputs[0], tr.inputs['Normal'])
    add = N.new('ShaderNodeAddShader'); L.new(bs.outputs[0], add.inputs[0]); L.new(tr.outputs[0], add.inputs[1])
    final = add.outputs[0]
    if use_alpha:
        al = image(nt, f'{TEX}{plant}_alpha.png').outputs['Color']
        tp = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader')
        L.new(rng(nt, al, 0.35, 0.65), mx.inputs[0]); L.new(tp.outputs[0], mx.inputs[1]); L.new(final, mx.inputs[2]); final = mx.outputs[0]
    L.new(final, out.inputs['Surface'])
    try:
        th = N.new('ShaderNodeValue'); th.outputs[0].default_value = 0.004; L.new(th.outputs[0], out.inputs['Thickness'])
    except Exception as e: print('thickness', e)
    for k, v in (('use_backface_culling', False), ('use_transparent_shadow', True), ('thickness_mode', 'SLAB')):
        try: setattr(mat, k, v)
        except Exception as e: print('mat', k, e)


def specks(nt, pos, scale, patch_scale, k, p0=0.5, p1=0.66, size=0.07):
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = scale; nt.links.new(pos, vor.inputs['Vector'])
    dot = rng(nt, vor.outputs['Distance'], size, 0.0)
    patch = rng(nt, noise(nt, pos, patch_scale), p0, p1)
    return mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', dot, patch), k)


def rocky(mat, kind):
    """rocks / root mounds / moss cushions: wet, with glowing lichen where the asset's own maps say moss or crevice."""
    bs, tex = base_tex(mat)
    if bs is None or tex is None: return
    nt = mat.node_tree; N = nt.nodes; L = nt.links
    wet(nt, bs, 0.9 if kind == 'rock' else 0.5, 0.1 if kind == 'rock' else 0.7)
    geo = N.new('ShaderNodeNewGeometry'); pos = geo.outputs['Position']
    hs = N.new('ShaderNodeHueSaturation'); L.new(tex.outputs['Color'], hs.inputs['Color']); hs.inputs['Value'].default_value = 0.42
    hs.inputs['Saturation'].default_value = 0.85; L.new(hs.outputs['Color'], bs.inputs['Base Color'])
    c = sep(nt, tex.outputs['Color'])
    if kind == 'rock':        # moss = greener than it is red/blue
        m = rng(nt, mth(nt, 'SUBTRACT', c[1], mth(nt, 'MAXIMUM', c[0], c[2])), 0.02, 0.10)
        e = mth(nt, 'MULTIPLY', m, rng(nt, noise(nt, pos, 6.0, 4.0), 0.50, 0.70, 0.0, 0.55))
        e = mth(nt, 'ADD', e, specks(nt, pos, 70.0, 2.0, 1.2, 0.56, 0.70))
    elif kind == 'roots':     # crevices between the roots: dark in the albedo
        lum = mth(nt, 'ADD', mth(nt, 'ADD', c[0], c[1]), c[2])
        m = rng(nt, lum, 0.42, 0.16)
        e = mth(nt, 'MULTIPLY', m, rng(nt, noise(nt, pos, 2.2, 3.0), 0.48, 0.66, 0.0, 0.9))
        e = mth(nt, 'ADD', e, specks(nt, pos, 60.0, 1.6, 2.5))
    else:                     # moss cushion: pin-points on the tips
        e = specks(nt, pos, 240.0, 5.0, 2.2, 0.42, 0.6, 0.12)
    L.new(e, bs.inputs['Emission Strength'])
    L.new(mixc(nt, rng(nt, noise(nt, pos, 0.9), 0.56, 0.62), CYAN if kind != 'roots' else TEAL, VIOLET), bs.inputs['Emission Color'])


# ---------------------------------------------------------------- library models
def import_model(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f'{LIB}models/{name}/{name}_2k.gltf')
    meshes = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    print('IMPORT', name, [(o.name, tuple(round(d, 3) for d in o.dimensions)) for o in meshes])
    return meshes


NAMES = ('calathea_orbifolia_01', 'fern_02', 'rock_moss_set_01', 'pine_roots')
srcs = {n: import_model(n) for n in NAMES}
done = set()
for n, ms in srcs.items():
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
        for m in o.data.materials:
            if not m or m.name in done: continue
            done.add(m.name)
            if n == 'calathea_orbifolia_01': leaf(m, n, False, 3.3, 1.5, 1.0)
            elif n == 'fern_02': leaf(m, n, True, 2.8, 1.3, 0.8)
            elif n == 'rock_moss_set_01': rocky(m, 'rock')
            elif n == 'pine_roots': rocky(m, 'roots')
            else: rocky(m, 'moss')
        o.hide_render = True
bpy.context.view_layer.update()
FG, MAIN = [], []


def put(name, x, y, size, rot=None, z=0.0, idx=None, gain=1.0, hue=0.0, tilt=(0.0, 0.0), fg=False, by_height=False, dew=0.0):
    ms = srcs[name]; src = ms[idx % len(ms)] if idx is not None else random.choice(ms)
    o = src.copy(); bpy.context.collection.objects.link(o)
    d = max(src.dimensions.z, 1e-4) if by_height else max(src.dimensions.x, src.dimensions.y, 1e-4)
    s = size / d * (src.scale.x if src.scale.x else 1)
    o.scale = (s, s, s); o.rotation_mode = 'XYZ'
    o.rotation_euler = (tilt[0], tilt[1], rot if rot is not None else random.uniform(0, 6.283))
    o.location = (0, 0, 0); o.hide_render = False
    o.color = (gain, hue, dew, 1)
    bpy.context.view_layer.update()
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(v.x for v in bb) / 8; cy = sum(v.y for v in bb) / 8; zmin = min(v.z for v in bb)
    o.location = (x - cx, y - cy, z - zmin - 0.012)
    (FG if fg else MAIN).append(o)
    return o


def creek_x(y):
    return -0.30 + 0.50 * math.sin(0.50 * y + 0.2) + 0.10 * math.sin(1.3 * y)


def creek_w(y):
    return 0.16 + 0.03 * max(y, 0) + 0.05 * math.sin(y * 1.7)


CAL, FERN, ROCK, PINE = NAMES
# ---- the hero: one big calathea, right of centre, its blades back-lit; a violet companion; ferns at its feet
put(CAL, 0.14, -0.12, 0.94, rot=math.radians(205), idx=0, gain=1.25, dew=1.0)
put(CAL, 1.15, 0.55, 0.80, rot=math.radians(40), idx=1, gain=0.9, hue=1.0, dew=1.0)
put(FERN, 0.90, -0.35, 0.80, idx=0, gain=0.9, dew=1.0)
put(FERN, -1.05, 0.35, 0.95, idx=1, gain=1.0, dew=1.0)
put(CAL, -1.35, 1.10, 0.75, idx=2, gain=0.8, hue=1.0)
put(FERN, 0.25, 0.95, 0.70, idx=2, gain=0.8)
put(ROCK, 1.20, 0.25, 0.50, idx=0); put(ROCK, -1.75, 1.6, 0.75, idx=3)
put(CAL, -0.15, 1.9, 0.55, idx=3, gain=0.8); put(CAL, 0.9, 1.7, 0.6, idx=4, gain=0.7)
# ---- soft foreground framing (rendered as its own layer): a blade at the left edge, a frond low right
put(CAL, -0.40, -0.70, 0.46, rot=math.radians(150), idx=1, gain=0.6, fg=True, dew=1.0)
put(FERN, 0.34, -0.80, 0.40, rot=math.radians(20), idx=3, gain=0.5, fg=True)
# ---- trunks (bark stand-in: mossy_rock on a displaced column) on pine_roots mounds, with a canopy of big fronds
TRUNKS = ((-2.3, 3.2, 0.34), (2.7, 4.2, 0.40), (-4.6, 6.5, 0.5), (1.6, 8.5, 0.45), (5.2, 7.5, 0.5), (-1.6, 11.5, 0.5), (6.5, 12.0, 0.6), (-7.5, 10.0, 0.6), (-3.4, 15.0, 0.6), (3.2, 15.5, 0.6))
tm = bpy.data.materials.new('trunk'); tm.use_nodes = True
tnt = tm.node_tree; tb = next(n for n in tnt.nodes if n.type == 'BSDF_PRINCIPLED')
tco = tnt.nodes.new('ShaderNodeTexCoord'); tmap = tnt.nodes.new('ShaderNodeMapping'); tmap.inputs['Scale'].default_value = (0.9, 0.9, 0.35)
tnt.links.new(tco.outputs['Object'], tmap.inputs['Vector'])
P = LIB + 'textures/mossy_rock/mossy_rock_'
td = image(tnt, P + 'diff_2k.jpg', 'sRGB', tmap.outputs[0], box=True); tr_ = image(tnt, P + 'rough_2k.jpg', vec=tmap.outputs[0], box=True)
tn = image(tnt, P + 'nor_gl_2k.jpg', vec=tmap.outputs[0], box=True)
ths = tnt.nodes.new('ShaderNodeHueSaturation'); ths.inputs['Value'].default_value = 0.30; tnt.links.new(td.outputs['Color'], ths.inputs['Color'])
tnt.links.new(ths.outputs['Color'], tb.inputs['Base Color']); tnt.links.new(mth(tnt, 'MULTIPLY', tr_.outputs['Color'], 0.6), tb.inputs['Roughness'])
tnm = tnt.nodes.new('ShaderNodeNormalMap'); tnm.inputs['Strength'].default_value = 2.0; tnt.links.new(tn.outputs['Color'], tnm.inputs['Color']); tnt.links.new(tnm.outputs[0], tb.inputs['Normal'])
tc = sep(tnt, td.outputs['Color']); tgeo = tnt.nodes.new('ShaderNodeNewGeometry')
tmoss = rng(tnt, mth(tnt, 'ADD', mth(tnt, 'ADD', tc[0], tc[1]), tc[2]), 0.75, 1.25)
tpos = tnt.nodes.new('ShaderNodeSeparateXYZ'); tnt.links.new(tgeo.outputs['Position'], tpos.inputs[0])
tfade = rng(tnt, tpos.outputs['Z'], 4.5, 0.2)
te = mth(tnt, 'MULTIPLY', mth(tnt, 'MULTIPLY', tmoss, rng(tnt, noise(tnt, tgeo.outputs['Position'], 1.8, 4.0), 0.42, 0.62)), tfade)
tvm = tnt.nodes.new('ShaderNodeMapping'); tvm.inputs['Scale'].default_value = (5.0, 5.0, 1.1); tnt.links.new(tco.outputs['Object'], tvm.inputs['Vector'])
tv = tnt.nodes.new('ShaderNodeTexVoronoi'); tv.feature = 'DISTANCE_TO_EDGE'; tv.inputs['Scale'].default_value = 1.0; tnt.links.new(tvm.outputs[0], tv.inputs['Vector'])
fis = mth(tnt, 'MULTIPLY', mth(tnt, 'MULTIPLY', rng(tnt, mth(tnt, 'ABSOLUTE', mth(tnt, 'SUBTRACT', noise(tnt, tvm.outputs[0], 0.55, 4.0), 0.5)), 0.010, 0.0), rng(tnt, noise(tnt, tgeo.outputs['Position'], 0.8, 3.0), 0.46, 0.62)), tfade)
tbump = tnt.nodes.new('ShaderNodeBump'); tbump.inputs['Strength'].default_value = 0.9; tbump.inputs['Distance'].default_value = 0.05
tnt.links.new(rng(tnt, tv.outputs['Distance'], 0.0, 0.12), tbump.inputs['Height']); tnt.links.new(tnm.outputs[0], tbump.inputs['Normal']); tnt.links.new(tbump.outputs[0], tb.inputs['Normal'])
te = mth(tnt, 'ADD', mth(tnt, 'MULTIPLY', te, 0.4), mth(tnt, 'MULTIPLY', fis, 0.8))
tdot = tnt.nodes.new('ShaderNodeVectorMath'); tdot.operation = 'DOT_PRODUCT'; tnt.links.new(tgeo.outputs['Normal'], tdot.inputs[0]); tdot.inputs[1].default_value = (-0.80, -0.55, 0.15)
tside = mth(tnt, 'MULTIPLY', rng(tnt, tdot.outputs['Value'], 0.15, 0.85), rng(tnt, tpos.outputs['Z'], 7.5, 0.3))
te = mth(tnt, 'ADD', te, mth(tnt, 'MULTIPLY', tside, mth(tnt, 'ADD', specks(tnt, tgeo.outputs['Position'], 42.0, 1.1, 2.2, 0.40, 0.58, 0.10), rng(tnt, noise(tnt, tgeo.outputs['Position'], 2.6, 5.0), 0.50, 0.72, 0.0, 0.16))))
tnt.links.new(mth(tnt, 'ADD', mth(tnt, 'MULTIPLY', te, 1.6), mth(tnt, 'MULTIPLY', specks(tnt, tgeo.outputs['Position'], 55.0, 1.2, 3.0, 0.46, 0.62, 0.09), tfade)), tb.inputs['Emission Strength'])
tnt.links.new(mixc(tnt, rng(tnt, noise(tnt, tgeo.outputs['Position'], 0.5), 0.5, 0.6), TEAL, VIOLET), tb.inputs['Emission Color'])
ctex = bpy.data.textures.new('tr_clouds', 'CLOUDS'); ctex.noise_scale = 0.6
for i, (x, y, r) in enumerate(TRUNKS):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=14, location=(x, y, 6.6), end_fill_type='NOTHING')
    t = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(t.data)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1], cuts=40)
    for v in bm.verts:
        k = 1.0 + 0.9 * math.exp(-(v.co.z + 7.0) / 0.9)          # flare at the foot
        v.co.x *= k; v.co.y *= k
    bm.to_mesh(t.data); bm.free()
    t.rotation_euler = (random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), random.uniform(0, 6.28))
    md = t.modifiers.new('d', 'DISPLACE'); md.texture = ctex; md.strength = 0.22; md.texture_coords = 'GLOBAL'
    for p in t.data.polygons: p.use_smooth = True
    t.data.materials.append(tm); MAIN.append(t)
    put(PINE, x + 0.1, y - r * 0.6, r * 5.0, idx=i)
    for j in range(5):       # canopy: big fronds and blades high up, mostly silhouettes with a thread of light
        a = random.uniform(0, 6.283); rr = random.uniform(0.4, 2.6)
        put(FERN if j % 3 else CAL, x + math.cos(a) * rr, y + math.sin(a) * rr, random.uniform(3.0, 5.0), z=random.uniform(3.4, 6.5),
            gain=0.45, hue=1.0 if random.random() < 0.3 else 0.0, tilt=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)))
# canopy fronds reaching in over the camera from both sides (frame the gap, keep the centre open)
for (x, y, z, sz, nm, hu) in ((-2.4, 0.8, 2.3, 3.2, FERN, 0), (2.9, 1.5, 2.6, 3.4, FERN, 0), (-3.0, 2.5, 3.2, 3.6, CAL, 1), (3.4, 3.0, 3.4, 3.2, CAL, 0), (-1.8, 5.0, 4.6, 4.0, FERN, 0), (2.2, 6.0, 4.8, 4.0, FERN, 1)):
    put(nm, x, y, sz, z=z, gain=0.5, hue=hu, tilt=(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4)))
y = 1.3
while y < 13.0:
    for side in (-1, 1):
        if random.random() < 0.25: continue
        x = creek_x(y) + side * (creek_w(y) + random.uniform(0.22, 0.55))
        nm = FERN if random.random() < 0.6 else CAL
        put(nm, x, y + random.uniform(-0.2, 0.2), random.uniform(0.35, 0.7), gain=random.uniform(0.9, 1.25), hue=1.0 if random.random() < 0.22 else 0.0)
    y += 0.42 + y * 0.05
# ---- mid and far understorey, kept off the creek
for i in range(190):
    y = random.uniform(1.4, 15.0)
    x = random.uniform(-1.0, 1.0) * (1.6 + y * 0.75)
    if abs(x - creek_x(y)) < creek_w(y) + 0.30: continue
    nm = random.choice((FERN, FERN, FERN, CAL, CAL, ROCK))
    sz = {FERN: random.uniform(0.6, 1.2), CAL: random.uniform(0.45, 0.9), ROCK: random.uniform(0.4, 1.1)}[nm]
    put(nm, x, y, sz, gain=random.uniform(0.45, 1.0), hue=1.0 if random.random() < 0.28 else 0.0)

# ---------------------------------------------------------------- ground: wet forest mud + moss, a glowing root web
def ground_mat():
    m = bpy.data.materials.new('ground'); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    geo = N.new('ShaderNodeNewGeometry'); pos = geo.outputs['Position']
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.55, 0.55, 0.55); L.new(pos, mp.inputs['Vector']); uv = mp.outputs[0]
    mp2 = N.new('ShaderNodeMapping'); mp2.inputs['Scale'].default_value = (0.8, 0.8, 0.8); mp2.inputs['Rotation'].default_value = (0, 0, 0.6); L.new(pos, mp2.inputs['Vector'])
    M = LIB + 'textures/mud_forest/mud_forest_'; R = LIB + 'textures/roots/roots_'; A = ACG + 'Moss002/Moss002_2K-JPG_'
    md, mr, mn, mh = (image(nt, M + k + '_2k.jpg', cs, uv).outputs['Color'] for k, cs in (('diff', 'sRGB'), ('rough', 'Non-Color'), ('nor_gl', 'Non-Color'), ('disp', 'Non-Color')))
    rd, rn, rh = (image(nt, R + k + '_2k.jpg', cs, mp2.outputs[0]).outputs['Color'] for k, cs in (('diff', 'sRGB'), ('nor_gl', 'Non-Color'), ('disp', 'Non-Color')))
    ad, ar, an = (image(nt, A + k + '.jpg', cs, mp2.outputs[0]).outputs['Color'] for k, cs in (('Color', 'sRGB'), ('Roughness', 'Non-Color'), ('NormalGL', 'Non-Color')))
    moss = rng(nt, mth(nt, 'ADD', noise(nt, pos, 0.9, 4.0), mth(nt, 'MULTIPLY', mh, 0.25)), 0.58, 0.72)
    rootm = mth(nt, 'MULTIPLY', rng(nt, noise(nt, pos, 0.5, 2.0), 0.30, 0.50), mth(nt, 'SUBTRACT', 1.0, moss))
    puddle = mth(nt, 'MULTIPLY', rng(nt, mh, 0.42, 0.30), mth(nt, 'SUBTRACT', 1.0, moss))
    col = mixc(nt, rootm, md, rd); col = mixc(nt, moss, col, mixc(nt, 1.0, ad, (0.55, 1.0, 0.85, 1), 'MULTIPLY'))
    hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = 0.34; hs.inputs['Saturation'].default_value = 0.9
    L.new(col, hs.inputs['Color']); L.new(mixc(nt, puddle, hs.outputs['Color'], (0.004, 0.010, 0.014, 1)), bs.inputs['Base Color'])
    rough = mth(nt, 'MULTIPLY', mr, 0.38); rough = mixc(nt, moss, rough, mth(nt, 'MULTIPLY', ar, 0.75))
    L.new(mixc(nt, puddle, rough, (0.02, 0.02, 0.02, 1)), bs.inputs['Roughness'])
    nc = mixc(nt, rootm, mn, rn); nc = mixc(nt, moss, nc, an); nc = mixc(nt, puddle, nc, (0.5, 0.5, 1.0, 1))
    nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.6; L.new(nc, nm.inputs['Color']); L.new(nm.outputs[0], bs.inputs['Normal'])
    set_in(bs, 'Coat Weight', 0.7); set_in(bs, 'Coat Roughness', 0.05); set_in(bs, 'Coat IOR', 1.33)
    # the root web: the roots texture's own displacement map lights its raised roots, in drifting patches
    web = mth(nt, 'MULTIPLY', image(nt, TEX + 'roots_web.png', vec=mp2.outputs[0]).outputs['Color'], mth(nt, 'SUBTRACT', 1.0, puddle))
    web = mth(nt, 'MULTIPLY', web, rng(nt, noise(nt, pos, 1.1, 3.0), 0.40, 0.66, 0.04, 1.0))
    e = mth(nt, 'ADD', mth(nt, 'MULTIPLY', web, 1.5), mth(nt, 'MULTIPLY', specks(nt, pos, 110.0, 1.4, 3.0, 0.5, 0.66, 0.10), moss))
    L.new(e, bs.inputs['Emission Strength'])
    L.new(mixc(nt, rng(nt, noise(nt, pos, 0.35), 0.55, 0.62), CYAN, VIOLET), bs.inputs['Emission Color'])
    return m


gm = ground_mat()
bpy.ops.mesh.primitive_grid_add(x_subdivisions=520, y_subdivisions=520, size=1, location=(0, 2.4, 0)); g1 = bpy.context.object; g1.scale = (9, 8.4, 1)
dt = bpy.data.textures.new('mud_disp', 'IMAGE'); dt.image = bpy.data.images.load(LIB + 'textures/mud_forest/mud_forest_disp_2k.jpg', check_existing=True)
dt.image.colorspace_settings.name = 'Non-Color'; dt.repeat_x = 5; dt.repeat_y = 5; dt.extension = 'REPEAT'
dm = g1.modifiers.new('d', 'DISPLACE'); dm.texture = dt; dm.texture_coords = 'UV'; dm.strength = 0.05; dm.mid_level = 0.55
for p in g1.data.polygons: p.use_smooth = True
g1.data.materials.append(gm); MAIN.append(g1)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 14, -0.012)); g2 = bpy.context.object; g2.scale = (70, 44, 1); g2.data.materials.append(gm); MAIN.append(g2)

# ---- the creek: still black water that mirrors the glow, with a drift of living light in it; the path into depth
bm = bmesh.new(); prev = None
for i in range(161):
    y = -1.6 + i * 0.11
    xc = creek_x(y); wd = creek_w(y)
    v0 = bm.verts.new((xc - wd, y, 0.004)); v1 = bm.verts.new((xc + wd, y, 0.004))
    if prev: bm.faces.new((prev[0], prev[1], v1, v0))
    prev = (v0, v1)
me = bpy.data.meshes.new('creek'); bm.to_mesh(me); bm.free()
ro = bpy.data.objects.new('creek', me); bpy.context.collection.objects.link(ro); MAIN.append(ro)
rm = bpy.data.materials.new('creek'); rm.use_nodes = True
rnt = rm.node_tree; rb = next(n for n in rnt.nodes if n.type == 'BSDF_PRINCIPLED')
rb.inputs['Base Color'].default_value = (0.0, 0.012, 0.02, 1); rb.inputs['Roughness'].default_value = 0.03
rgeo = rnt.nodes.new('ShaderNodeNewGeometry'); rmap = rnt.nodes.new('ShaderNodeMapping'); rmap.inputs['Scale'].default_value = (9.0, 1.6, 1.0)
rnt.links.new(rgeo.outputs['Position'], rmap.inputs['Vector'])
flow = rng(rnt, noise(rnt, rmap.outputs[0], 2.2, 6.0), 0.60, 0.74)
spk = specks(rnt, rgeo.outputs['Position'], 130.0, 1.0, 5.0, 0.30, 0.52, 0.12)
rsx = rnt.nodes.new('ShaderNodeSeparateXYZ'); rnt.links.new(rgeo.outputs['Position'], rsx.inputs[0])
rnt.links.new(mth(rnt, 'ADD', mth(rnt, 'ADD', mth(rnt, 'MULTIPLY', flow, 0.16), spk), rng(rnt, rsx.outputs['Y'], 1.5, 9.0, 0.03, 0.55)), rb.inputs['Emission Strength']); rb.inputs['Emission Color'].default_value = CYAN
rbump = rnt.nodes.new('ShaderNodeBump'); rbump.inputs['Strength'].default_value = 0.06; rnt.links.new(noise(rnt, rmap.outputs[0], 6.0, 2.0), rbump.inputs['Height'])
rnt.links.new(rbump.outputs[0], rb.inputs['Normal'])
me.materials.append(rm)

# ---------------------------------------------------------------- light: night-sky fill, one cool rim, the plants' own light
w = bpy.data.worlds.new('w'); scene.world = w; w.use_nodes = True
WN = w.node_tree.nodes; WL = w.node_tree.links
bg = next(n for n in WN if n.type == 'BACKGROUND')
env = WN.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(f'{LIB}hdris/rogland_clear_night/rogland_clear_night_4k.hdr')
tint = WN.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs[0].default_value = 1.0
tint.inputs[7].default_value = (0.22, 0.50, 1.0, 1)
WL.new(env.outputs['Color'], tint.inputs[6]); WL.new(tint.outputs[2], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.50


def aim(o, to):
    d = Vector(to) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def lamp(kind, loc, to, col, energy, size=0.1, spot=None):
    l = bpy.data.lights.new('l', kind); l.energy = energy; l.color = col[:3]
    if kind == 'SUN': l.angle = math.radians(4)
    else: l.shadow_soft_size = size
    if spot: l.spot_size = math.radians(spot); l.spot_blend = 0.6; l.use_shadow = False
    if kind != 'SUN': l.specular_factor = 0.0
    o = bpy.data.objects.new('l', l); bpy.context.collection.objects.link(o); o.location = loc
    if to is not None: aim(o, to)
    return o


lamp('SUN', (1.5, 9, 7), (0, 0, 0), (0.50, 0.78, 1.0), 0.55)
lamp('SUN', (-7, 9, 2.6), (0, 4, 1.2), (0.35, 0.66, 1.0), 0.40)                    # low cool kicker: a rim up one side of the trunks                       # the gap in the canopy: cool rim, wet glints
lamp('SPOT', (0.7, 1.4, 0.75), (0.2, -0.12, 0.42), CYAN, 70.0, 0.25, spot=70)       # through the hero's blades
lamp('SPOT', (0.1, 0.75, 1.35), (0.2, -0.12, 0.72), CYAN, 60.0, 0.3, spot=60)                  # down through the top blade
lamp('SPOT', (-0.5, 0.9, 0.12), (0.2, -0.12, 0.5), TEAL, 12.0, 0.2, spot=80)        # the creek's light up under the hero
lamp('SPOT', (1.8, 1.6, 0.8), (1.15, 0.55, 0.4), VIOLET, 50.0, 0.25, spot=70)        # through the violet companion
for (x, y, z, c, e) in ((0.42, -0.1, 0.22, TEAL, 0.5), (0.95, -0.3, 0.2, CYAN, 0.35), (-1.05, 0.4, 0.25, TEAL, 0.5), (-1.35, 1.1, 0.3, VIOLET, 0.6),
                        (0.25, 1.0, 0.25, CYAN, 0.5), (1.25, 0.6, 0.3, VIOLET, 0.5), (-0.3, 2.6, 0.3, CYAN, 0.9), (0.6, 4.2, 0.4, TEAL, 1.6),
                        (-2.0, 4.5, 0.5, VIOLET, 1.6), (2.2, 5.5, 0.5, CYAN, 1.8), (0.2, 7.5, 0.6, CYAN, 3.0), (-2.5, 8.5, 0.6, TEAL, 3.0), (3.0, 10, 0.6, VIOLET, 3.0)):
    lp = lamp('POINT', (x, y, z), None, c, e * 2.6, 0.1); lp.data.use_shadow = y < 1.5

# ---------------------------------------------------------------- camera: low, a little up; sharp on the hero
cam = bpy.data.cameras.new('cam'); cam.lens = 24; cam.sensor_width = 36
cam.dof.use_dof = True; cam.dof.focus_distance = 1.12; cam.dof.aperture_fstop = 1.1
co = bpy.data.objects.new('cam', cam); bpy.context.collection.objects.link(co)
co.location = (0, -1.2, 0.24); co.rotation_euler = (math.radians(90 + 9), 0, 0); scene.camera = co

r = scene.render; r.resolution_x = int(1920 * SC); r.resolution_y = int(1080 * SC); r.resolution_percentage = 100
r.film_transparent = True
r.image_settings.file_format = 'OPEN_EXR'; r.image_settings.color_depth = '32'; r.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Standard'
ee = scene.eevee
for k, v in (('taa_render_samples', SAMPLES), ('use_raytracing', True), ('use_shadows', True), ('use_bokeh_jittered', True), ('bokeh_max_size', 160.0),
             ('bokeh_overblur', 8.0), ('light_threshold', 0.003)):
    try: setattr(ee, k, v)
    except Exception as e: print('eevee', k, e)
try: ee.ray_tracing_options.resolution_scale = '1'
except Exception as e: print('rt', e)
import OpenImageIO as oiio, numpy as np, time
T0 = time.time(); dump = {}


def shot(tag):
    r.filepath = f'{OUT}_{tag}.exr'
    bpy.ops.render.render(write_still=True)
    inp = oiio.ImageInput.open(r.filepath); px = inp.read_image('float'); inp.close()
    print('WROTE', r.filepath, px.shape, 't=%.1f' % (time.time() - T0))
    return px


def show(objs_on, objs_off):
    for o in objs_off: o.hide_render = True
    for o in objs_on: o.hide_render = False


# 1) beauty, main layer and the soft foreground layer (LAYER 'main' skips the fg, for quick tests)
show(MAIN, FG); dump['rgba_main'] = shot('main').astype(np.float16)
if LAYER != 'main':
    show(FG, MAIN); dump['rgba_fg'] = shot('fg').astype(np.float16)
# 2) emitters only (lights and sky fill off): what glows, for the bloom and the light in the mist
show(MAIN, FG)
lights = [o for o in bpy.data.objects if o.type == 'LIGHT']
for o in lights: o.hide_render = True
bg.inputs['Strength'].default_value = 0.0
dump['emit_main'] = shot('emit')[..., :3].astype(np.float16)
# 3) depth: every material's surface replaced by its camera depth (cut-outs kept), no depth of field
cam.dof.use_dof = False; ee.taa_render_samples = 8
for m in bpy.data.materials:
    if not m.node_tree: continue
    nt = m.node_tree; out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None or not out.inputs['Surface'].links: continue
    cd = nt.nodes.new('ShaderNodeCameraData'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(cd.outputs['View Z Depth'], em.inputs['Color'])
    src = out.inputs['Surface'].links[0].from_node
    if src.type == 'MIX_SHADER': nt.links.new(em.outputs[0], src.inputs[2])
    else: nt.links.new(em.outputs[0], out.inputs['Surface'])
z = shot('z'); a = z[..., 3]
dump['z_main'] = np.where(a > 0.5, z[..., 0] / np.maximum(a, 1e-4), 1e4).astype(np.float32)
np.savez_compressed(OUT + '.npz', **dump)
print('WROTE', OUT + '.npz', {k: v.shape for k, v in dump.items()}, 'render seconds %.1f' % (time.time() - T0))
