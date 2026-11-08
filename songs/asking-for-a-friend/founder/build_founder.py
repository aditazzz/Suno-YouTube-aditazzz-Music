"""Build the founder in Blender (background):

  Blender -b --python founder/build_founder.py -- <out.blend>

One rig (FOUNDER_rig), the head from the studio's toon3d (real mouth, shape keys), the swoop (with its one shape key,
'fallen'), the short hair cap, body, hands, the watch, and five wardrobe collections (FOUNDER_quarterzip, _robe,
_goggles, _linen, _pyjamas), only the quarter-zip visible. Never writes over an existing file.
"""
import math, os, sys, time
import numpy as np
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '_bpylib'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'great-idea-ted', 'toon3d'))
sys.path.insert(0, HERE)
import build as TB          # toon3d Blender helpers (head parts, materials, mesh/skin helpers)
import features as FT
from sdf import smoothstep, grad as sgrad
import fbody as FB
import spec as SP

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else None
TEX = os.path.expanduser('~/Documents/Original Music/Asking for a Friend 2/blender/founder/textures')
if OUT and os.path.exists(OUT) and '--force' not in sys.argv:
    raise SystemExit('refusing to overwrite ' + OUT)
t0 = time.time()
def log(*a): print(f'[{time.time() - t0:6.1f}s]', *a, flush=True)

# ---------------------------------------------------------------- clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

root = bpy.data.collections.new('FOUNDER'); scene.collection.children.link(root)

S = dict(name='F', HEAD=SP.HEAD, EYE=SP.EYE, BROW=SP.BROW, EAR=SP.EAR, TEETH=SP.TEETH, BODY=SP.BODY, HAIR=SP.HAIR,
         COLORS=dict(skin=SP.COLORS['skin'], lips=SP.COLORS['lips'], lash=SP.COLORS['lash'], brow=SP.COLORS['brow'],
                     hair_dark=SP.COLORS['hair_dark'], hair_light=SP.COLORS['hair_light']))
Bd = SP.BODY; C = SP.COLORS
J = FB.skeleton(Bd)

# ---------------------------------------------------------------- materials
def tex_mat(name, tex, tint, density=3.0, rough_mul=1.0, rough_add=0.0, normal=0.6, sheen=0.0, coat=0.0, spec=0.35,
            tint_mix=0.85, metallic=0.0):
    """a PBR fabric/leather from Poly Haven maps, box-projected from the undeformed mesh (Generated coords scaled to
    metres), its colour pulled toward the design colour (tint) so the palette holds."""
    m, nt, b = TB.node_mat(name); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.name = 'MAP'
    L.new(tc.outputs['Generated'], mp.inputs['Vector']); mp.inputs['Scale'].default_value = (density, density, density)
    def img(kind, non_color):
        p = os.path.join(TEX, tex, f'{tex}_{kind}_1k.jpg')
        n = N.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(p, check_existing=True)
        if non_color: n.image.colorspace_settings.name = 'Non-Color'
        n.projection = 'BOX'; n.projection_blend = 0.25
        L.new(mp.outputs['Vector'], n.inputs['Vector']); return n
    d = img('diff', False); r = img('rough', True); n_ = img('nor_gl', True)
    # colour: the texture's luminance variation over the design colour
    bw = N.new('ShaderNodeRGBToBW'); L.new(d.outputs['Color'], bw.inputs['Color'])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.7
    mr.inputs['To Min'].default_value = 0.72; mr.inputs['To Max'].default_value = 1.12; L.new(bw.outputs['Val'], mr.inputs['Value'])
    mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    cin = [i for i in mul.inputs if i.type == 'RGBA']; fin = [i for i in mul.inputs if i.name == 'Factor' and i.type == 'VALUE'][0]
    fin.default_value = 1.0; cin[0].default_value = TB.hexrgb(tint)
    cv = N.new('ShaderNodeCombineColor'); L.new(mr.outputs[0], cv.inputs[0]); L.new(mr.outputs[0], cv.inputs[1]); L.new(mr.outputs[0], cv.inputs[2])
    L.new(cv.outputs[0], cin[1])
    out_c = [o for o in mul.outputs if o.type == 'RGBA'][0]
    mix2 = TB.mix_rgb(nt, tint_mix, d.outputs['Color'], out_c)
    L.new(mix2, b.inputs['Base Color'])
    rm = N.new('ShaderNodeMath'); rm.operation = 'MULTIPLY_ADD'; rm.inputs[1].default_value = rough_mul; rm.inputs[2].default_value = rough_add
    rm.use_clamp = True
    L.new(r.outputs['Color'], rm.inputs[0]); L.new(rm.outputs[0], b.inputs['Roughness'])
    nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal
    L.new(n_.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Specular IOR Level'].default_value = spec
    b.inputs['Metallic'].default_value = metallic
    if sheen: b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = 0.45; b.inputs['Sheen Tint'].default_value = TB.hexrgb(tint)
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.08
    m.diffuse_color = TB.hexrgb(tint)
    return m

mats = TB.default_mats(S)
# the Claude family: skin a touch glossier and smoother than Ted's, the teeth a bright veneer white (not lit; glossy)
for k in ('skin', 'face', 'ear'):
    bb = mats[k].node_tree.nodes['Principled BSDF']; bb.inputs['Roughness'].default_value = 0.52; bb.inputs['Specular IOR Level'].default_value = 0.30
tb = mats['teeth'].node_tree.nodes['Principled BSDF']; tb.inputs['Base Color'].default_value = TB.hexrgb('#F2EEE6'); tb.inputs['Roughness'].default_value = 0.18
tb.inputs['Coat Weight'].default_value = 0.6; tb.inputs['Coat Roughness'].default_value = 0.05
mats['hair'] = TB.hair_mat('F_hair', C['hair_dark'], C['hair_light'], coat=0.5, sheen=0.0, rough=0.34, spec=0.5, bump=0.3)
hb = mats['hair'].node_tree.nodes['Principled BSDF']; hb.inputs['Coat Roughness'].default_value = 0.06
mats['swoop'] = TB.hair_mat('F_swoop', C['hair_dark'], C['hair_light'], coat=0.7, sheen=0.0, rough=0.28, spec=0.55, bump=0.2)
mats['swoop'].node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = 0.14
mats['swoop'].node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.6
W = dict(
    knit_cream=tex_mat('F_knit_cream', 'knitted_fleece', '#DCD1BB', density=4.0, rough_add=0.15, normal=0.8, sheen=0.25),
    rib_cream=tex_mat('F_rib_cream', 'cotton_jersey', '#E2D8C4', density=6.0, rough_add=0.2, normal=1.0, sheen=0.2),
    jersey_charcoal=tex_mat('F_jersey_charcoal', 'cotton_jersey', C['charcoal'], density=5.0, rough_add=0.15, normal=0.6, sheen=0.15),
    wool_charcoal=tex_mat('F_wool_charcoal', 'poly_wool_herringbone', '#202126', density=3.0, rough_add=0.1, normal=0.5, sheen=0.1, tint_mix=0.95),
    leather=tex_mat('F_leather_cream', 'leather_white', '#EFE8DA', density=5.0, rough_mul=0.8, normal=0.4, coat=0.2, spec=0.5),
    sole=TB.plain_mat('F_sole', '#F1ECE2', rough=0.55, spec=0.3),
    sole_dark=TB.plain_mat('F_sole_dark', '#1E1F23', rough=0.6, spec=0.3),
    uv_satin=tex_mat('F_uv_satin', 'crepe_satin', C['uv'], density=4.0, rough_mul=0.6, normal=0.4, sheen=0.5, spec=0.6),
    uv_metal=TB.plain_mat('F_uv_metal', C['uv'], rough=0.2, spec=0.5, metallic=0.9),
    charcoal_gloss=TB.plain_mat('F_zip', '#1F2024', rough=0.3, spec=0.5, coat=0.3),
    charcoal_satin=tex_mat('F_charcoal_satin', 'crepe_satin', C['charcoal'], density=4.0, rough_mul=0.6, normal=0.4, sheen=0.4, spec=0.6),
    terry_cream=tex_mat('F_terry_cream', 'terry_cloth', C['cream'], density=3.0, rough_add=0.2, normal=1.2, sheen=0.35),
    fur_cream=tex_mat('F_fur_cream', 'curly_teddy_natural', '#E9DFC9', density=2.5, rough_add=0.25, normal=1.5, sheen=0.5, tint_mix=0.7),
    linen_cream=tex_mat('F_linen_cream', 'rough_linen', '#EDE6D6', density=3.0, rough_add=0.15, normal=0.9, sheen=0.2),
    linen_oat=tex_mat('F_linen_oat', 'rough_linen', '#CDBFA6', density=3.0, rough_add=0.15, normal=0.9, sheen=0.2),
    button=TB.plain_mat('F_button', '#F4F0E8', rough=0.25, spec=0.5, coat=0.5),
    suede=tex_mat('F_suede', 'poly_wool_herringbone', '#2B2B30', density=8.0, rough_add=0.3, normal=0.3, sheen=0.4),
    velvet=tex_mat('F_velvet', 'crepe_satin', '#26262B', density=5.0, rough_add=0.3, normal=0.3, sheen=0.8),
    satin_charcoal=tex_mat('F_satin_charcoal', 'crepe_satin', '#26272D', density=3.5, rough_mul=0.8, rough_add=0.22, normal=0.5, sheen=0.15, spec=0.4, tint_mix=1.0),
    satin_cream=tex_mat('F_satin_cream', 'crepe_satin', C['cream'], density=6.0, rough_mul=0.5, normal=0.3, sheen=0.4, spec=0.6),
    steel=TB.plain_mat('F_steel', C['steel'], rough=0.16, spec=0.5, metallic=1.0),
    dial=TB.plain_mat('F_dial', C['uv'], rough=0.22, spec=0.6, coat=1.0),
    strap=TB.plain_mat('F_strap', C['steel'], rough=0.24, spec=0.5, metallic=1.0),
    lens=TB.plain_mat('F_lens', '#2A1846', rough=0.04, spec=0.8, metallic=0.85),
    goggle_frame=tex_mat('F_goggle_leather', 'leather_white', '#2A2522', density=6.0, rough_mul=0.9, normal=0.5, coat=0.2),
    mask_satin=tex_mat('F_mask_satin', 'crepe_satin', C['uv'], density=6.0, rough_mul=0.5, normal=0.4, sheen=0.5, spec=0.6),
)

def fix_mapping(ob):
    """scale the Generated -> metres mapping by the object's undeformed size so the weave is the same size everywhere"""
    me = ob.data
    if not me.materials: return
    V = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    dims = np.maximum(V.max(0) - V.min(0), 1e-3)
    for m in me.materials:
        if m is None or not m.node_tree: continue
        mp = m.node_tree.nodes.get('MAP')
        if mp is None: continue
        # one material per object kind: make a per-object copy when the sizes differ
        key = 'dims_' + ob.name
        if m.get('_mapped'):
            m2 = m.copy(); m2.name = m.name + '_' + ob.name; me.materials[list(me.materials).index(m)] = m2; m = m2
            mp = m.node_tree.nodes['MAP']
        dens = mp.inputs['Scale'].default_value[0] if not m.get('_dens') else m['_dens']
        m['_dens'] = dens
        mp.inputs['Scale'].default_value = tuple(float(dens * d) for d in dims)
        m['_mapped'] = 1

# ---------------------------------------------------------------- rig
head_c = np.array([0, -0.004, Bd['head_center_z']]); hsc = Bd['head_scale']; H = SP.HEAD
bl = FB.bones(J)
bl.append(('jaw', head_c + hsc * np.array([0, H['hinge_y'], H['hinge_z']]), head_c + hsc * np.array([0, -0.085, -0.095]), 'head'))
rig = TB.armature('FOUNDER_rig', bl, root)
log('rig', len(rig.data.bones), 'bones')

# ---------------------------------------------------------------- head
P = TB.build_head_parts(S, root, mats)
hs = bpy.data.objects.new('F_headspace', None); root.objects.link(hs); hs.empty_display_size = 0.05
TB.bone_parent(hs, rig, 'head', Matrix.Translation(Vector(head_c)) @ Matrix.Scale(hsc, 4))
for k, ob in P.items():
    if not isinstance(ob, bpy.types.Object): continue
    if k in ('head', 'mouth', 'teeth_lo', 'tongue'):
        ob.location = Vector(head_c) + ob.location * hsc; ob.scale = (hsc, hsc, hsc)
        if k in ('teeth_lo', 'tongue'): TB.vgroup(ob, 'jaw', np.ones(len(ob.data.vertices)))
        m = ob.modifiers.new('rig', 'ARMATURE'); m.object = rig; ob.modifiers.move(ob.modifiers.find('rig'), 0)
        ob.parent = rig; ob.matrix_parent_inverse = rig.matrix_world.inverted()
    elif not k.startswith('lashes_'):
        ob.parent = hs
for k in ('teeth_up', 'teeth_lo', 'tongue', 'mouth'):   # veneers: the whole arch wider, so the grin is a wall of teeth
    P[k].scale = (P[k].scale[0] * 1.42, P[k].scale[1] * 1.05, P[k].scale[2])
log('head parts', [k for k in P if isinstance(P[k], bpy.types.Object)])

# hair cap (short, tight, hard part)
fh, _ = FT.hair_sdf(P['sdf'], SP.HAIR)
hv, hf = FT.mesh(fh, [-0.12, -0.14, -0.10], [0.12, 0.15, 0.16], SP.HAIR['step'])
hn = sgrad(fh, hv.astype(np.float32)); hv = FT.hair_grooves(hv, hn, P['sdf'], SP.HAIR)
cap = TB.mk_mesh('F_hair', hv, hf, root, subsurf=0); cap.data.materials.append(mats['hair']); cap.parent = hs
log('hair cap', len(hv))

# the swoop: one sculpted volume ('set'), its fall as a shape key ('fallen') on the same vertices
fsw = FB.swoop_sdf(P['sdf'])
sv, sf = FT.mesh(fsw, [-0.13, -0.18, 0.04], [0.13, 0.10, 0.25], 0.0014)
sn = sgrad(fsw, sv.astype(np.float32)); sv = FB.swoop_grooves(sv, sn)
fv = FB.swoop_fall(sv, P['sdf'])
sw = TB.mk_mesh('F_swoop', sv, sf, root, subsurf=0); sw.data.materials.append(mats['swoop']); sw.parent = hs
TB.add_keys(sw, sv, {'fallen': fv - sv})
log('swoop', len(sv))

# eyes look at a target; lids default
look = bpy.data.objects.new('F_look', None); root.objects.link(look)
look.location = (0, -2.0, Bd['head_center_z'] + 0.01); look.parent = rig
for t in ('L', 'R'):
    c = P['eye_' + t].constraints.new('DAMPED_TRACK'); c.target = look; c.track_axis = 'TRACK_NEGATIVE_Y'

# ---------------------------------------------------------------- body skin, neck, hands
def skinned(name, f, lo, hi, step, mat, parts, coll, subsurf=0):
    v, fc = FT.mesh(f, lo, hi, step)
    ob = TB.mk_mesh(name, v, fc, coll, subsurf=0); ob.data.materials.append(mat)
    if isinstance(parts, str):
        TB.skin(ob, rig, [parts], np.ones((len(v), 1), np.float32))
    else:
        names, Wt = FB.weights(parts, v.astype(np.float32)); TB.skin(ob, rig, names, Wt)
    if subsurf:
        m_ = ob.modifiers.new('subsurf', 'SUBSURF'); m_.levels = 0; m_.render_levels = subsurf
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    if mat.node_tree and mat.node_tree.nodes.get('MAP'): fix_mapping(ob)
    return ob

tp, ap, lp, fp = FB.torso_parts(Bd, J), FB.arm_parts(Bd, J), FB.leg_parts(Bd, J), FB.foot_parts(Bd, J)
body_parts = tp + ap + lp + fp
f_body = FB.union([FB.blend(tp, 0.06), FB.blend(ap, 0.03), FB.blend(lp, 0.03), FB.blend(fp, 0.02)], 0.035)
body = skinned('F_body', f_body, (-0.42, -0.24, 0.0), (0.42, 0.20, 1.60), 0.005, mats['skin'], body_parts, root)
log('body', len(body.data.vertices))
nb, nf = FB.neck_part(Bd)
nv, nfc = FT.mesh(nf, (-0.09, -0.09, 1.40), (0.09, 0.10, Bd['head_center_z'] + 0.04), 0.004)
neck = TB.mk_mesh('F_neck', nv, nfc, root, subsurf=0); neck.data.materials.append(mats['skin'])
a = smoothstep(1.44, 1.50, nv[:, 2]); b2 = smoothstep(Bd['head_pivot_z'] - 0.02, Bd['head_pivot_z'] + 0.04, nv[:, 2])
TB.skin(neck, rig, ['chest', 'neck', 'head'], np.stack([1 - a, a * (1 - b2), b2], 1)); neck.matrix_parent_inverse = rig.matrix_world.inverted()
for t in ('L', 'R'):
    fh_ = FB.hand(Bd, J, t)
    c0 = J['wrist.' + t]; c1 = J['hand.' + t]
    lo = np.minimum(c0, c1) - 0.10; hi = np.maximum(c0, c1) + 0.10
    hv_, hf_ = FT.mesh(fh_, lo, hi, 0.0021)
    hd_ = TB.mk_mesh('F_hand_' + t, hv_, hf_, root, subsurf=0); hd_.data.materials.append(mats['skin'])
    d = c1 - c0; d /= np.linalg.norm(d); u = (hv_ - c0) @ d; a = smoothstep(-0.03, 0.01, u)
    TB.skin(hd_, rig, ['forearm.' + t, 'hand.' + t], np.stack([1 - a, a], 1)); hd_.matrix_parent_inverse = rig.matrix_world.inverted()
log('neck + hands')

# the watch (always on: his left wrist)
Wd = FB.watch(J, 'L')
for nm, key, mat, step in (('strap', 'strap', W['strap'], 0.0010), ('case', 'case', W['steel'], 0.0007), ('dial', 'dial', W['dial'], 0.0005)):
    c = J['wrist.L']
    ob = skinned('F_watch_' + nm, Wd[key], c - 0.08, c + 0.08, step, mat, 'forearm.L', root, subsurf=0)
log('watch')

# ---------------------------------------------------------------- wardrobe
WARD = {}
ONLY = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
for kind in ('quarterzip', 'robe', 'goggles', 'linen', 'pyjamas'):
    if ONLY and kind not in ONLY: continue
    coll = bpy.data.collections.new('FOUNDER_' + kind); root.children.link(coll); WARD[kind] = coll
    for name, f, mk, lo, hi, step, parts in FB.garments(kind, Bd, J):
        ob = skinned(f'F_{kind}_{name}', f, lo, hi, step, W[mk], parts, coll)
        log(kind, name, len(ob.data.vertices))
    if kind == 'goggles':
        ec = (H['eye_x'], H['eye_y'], H['eye_z'])
        fr, ln, st = FB.goggles_sdf(ec)
        for nm, f, mat, step in (('frame', fr, W['goggle_frame'], 0.0012), ('lens', ln, W['lens'], 0.0008), ('strap', st, W['goggle_frame'], 0.0012)):
            v, fc = FT.mesh(f, (-0.13, -0.15, -0.06), (0.13, 0.15, 0.08), step)
            ob = TB.mk_mesh(f'F_goggles_{nm}', v, fc, coll, subsurf=0); ob.data.materials.append(mat); ob.parent = hs
            if mat.node_tree.nodes.get('MAP'): fix_mapping(ob)
    if kind == 'pyjamas':
        ec = (H['eye_x'], H['eye_y'], H['eye_z'])
        mk_, st = FB.mask_sdf(ec, P['sdf'])
        for nm, f, step in (('mask', mk_, 0.0012), ('mask_strap', st, 0.0012)):
            v, fc = FT.mesh(f, (-0.13, -0.15, -0.06), (0.13, 0.15, 0.08), step)
            ob = TB.mk_mesh(f'F_pyjamas_{nm}', v, fc, coll, subsurf=0); ob.data.materials.append(W['mask_satin']); ob.parent = hs
            fix_mapping(ob)
for kind, coll in WARD.items():
    coll.hide_render = kind != 'quarterzip'; coll.hide_viewport = kind != 'quarterzip'

# record the defaults the stills/animation scripts read
rig['eye_lid_up'] = SP.EYE['lid_up']; rig['eye_lid_lo'] = SP.EYE['lid_lo']
rig['outfits'] = ','.join(WARD)
for o in root.all_objects:
    if o.type == 'MESH': o['founder'] = 1
log('built', len([o for o in root.all_objects]), 'objects')
if OUT:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    log('saved', OUT)
