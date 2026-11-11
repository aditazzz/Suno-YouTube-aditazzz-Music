"""Run It: the workbench. Builds the whole set from scratch around her real Claude and GT3 RS (appended from Asking for a Friend).
Units: metres, Z up. Claude faces -Y; the camera sits on the -Y side looking +Y, so +X is screen right."""
import bpy, math, os, random
from mathutils import Vector, Matrix, Euler
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
AUS = os.path.join(ROOT, 'songs/asking-for-a-friend/finish/lookdev/blends/ld_car_outro_austin.blend')
OUT = os.path.join(ROOT, 'songs/run-it/build/bl')
BENCH_Z = 0.27          # bench top (he is 1.1 m tall with short arms: the bench is built to him)
D = bpy.data

def col_link(o, coll='SET'):
    c = D.collections.get(coll) or D.collections.new(coll)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o); return o

def mat(name, color=(.5, .5, .5), rough=.5, metal=0., emit=None, es=0., alpha=1., coat=0., spec=.5, trans=0., ior=1.45):
    m = D.materials.get(name)
    if m: return m
    m = D.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes.get('Principled BSDF')
    def S(k, v):
        i = b.inputs.get(k)
        if i is not None: i.default_value = v
    S('Base Color', (*color, 1)); S('Roughness', rough); S('Metallic', metal); S('Alpha', alpha); S('Coat Weight', coat); S('Specular IOR Level', spec); S('Transmission Weight', trans); S('IOR', ior)
    if emit: S('Emission Color', (*emit, 1)); S('Emission Strength', es)
    return m

def finish(o, m=None, bevel=0., smooth=True, segs=3, coll='SET'):
    if m is not None: o.data.materials.clear(); o.data.materials.append(m)
    if smooth and o.type == 'MESH':
        o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = segs; b.limit_method = 'ANGLE'; b.angle_limit = math.radians(40)
        try: b.harden_normals = True
        except Exception: pass
    return col_link(o, coll)

def box(name, size, loc, m, bevel=.004, rot=(0, 0, 0), coll='SET'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); return finish(o, m, bevel, smooth=bool(bevel), coll=coll)

def cyl(name, r, h, loc, m, verts=48, bevel=.002, rot=(0, 0, 0), r2=None, coll='SET'):
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    else: bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; return finish(o, m, bevel, coll=coll)

def sph(name, r, loc, m, coll='SET', seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc); o = bpy.context.active_object; o.name = name; return finish(o, m, 0, coll=coll)

def torus(name, R, r, loc, m, rot=(0, 0, 0), coll='SET'):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot, major_segments=48, minor_segments=16); o = bpy.context.active_object; o.name = name; return finish(o, m, 0, coll=coll)

def empty(name, loc, coll='SET'):
    o = D.objects.new(name, None); o.location = loc; bpy.context.scene.collection.objects.link(o); return col_link(o, coll)

def light(name, kind, loc, energy, color=(1, 1, 1), size=.2, aim=None, spot=70, blend=.4, coll='LIGHTS'):
    l = D.lights.new(name, kind); l.energy = energy; l.color = color
    if kind == 'AREA': l.size = size
    else: l.shadow_soft_size = size
    if kind == 'SPOT': l.spot_size = math.radians(spot); l.spot_blend = blend
    o = D.objects.new(name, l); o.location = loc; bpy.context.scene.collection.objects.link(o); col_link(o, coll)
    if aim is not None: look_at(o, aim)
    return o

def look_at(o, target):
    d = Vector(target) - Vector(o.location); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def parent(child, par):
    child.parent = par; child.matrix_parent_inverse = par.matrix_world.inverted(); return child

# ---------------------------------------------------------------- materials with texture
def wood(name, c1, c2, scale=3.0, rough=.42):
    m = D.materials.get(name)
    if m: return m
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale * 9, scale * .7, scale * 9)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6; nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = .6
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 2.2; wv.inputs['Distortion'].default_value = 5; wv.inputs['Detail'].default_value = 3
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (*c1, 1); rp.color_ramp.elements[1].color = (*c2, 1)
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'ADD'
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector']); nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], mx.inputs[0]); nt.links.new(wv.outputs['Fac'], mx.inputs[1]); mx2 = nt.nodes.new('ShaderNodeMath'); mx2.operation = 'MULTIPLY'; mx2.inputs[1].default_value = .5
    nt.links.new(mx.outputs[0], mx2.inputs[0]); nt.links.new(mx2.outputs[0], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = .08; nt.links.new(mx2.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def building_mat(name, paint, lit=(1., .78, .46), bias=.30):
    """A painted block with a grid of tiny windows, some lit. Windows only on the walls (not the roof)."""
    m = D.materials.get(name)
    if m: return m
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs[0])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; nt.links.new(sx.outputs['X'], ad.inputs[0]); nt.links.new(sx.outputs['Y'], ad.inputs[1])
    cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(ad.outputs[0], cb.inputs['X']); nt.links.new(sx.outputs['Z'], cb.inputs['Y'])
    oi = nt.nodes.new('ShaderNodeObjectInfo'); ofs = nt.nodes.new('ShaderNodeVectorMath'); ofs.operation = 'ADD'; nt.links.new(cb.outputs[0], ofs.inputs[0])
    rs = nt.nodes.new('ShaderNodeVectorMath'); rs.operation = 'SCALE'; rs.inputs['Scale'].default_value = 7.3; nt.links.new(oi.outputs['Random'], rs.inputs[0]); nt.links.new(rs.outputs[0], ofs.inputs[1])
    br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0; br.inputs['Scale'].default_value = 215; br.inputs['Mortar Size'].default_value = .34; br.inputs['Mortar Smooth'].default_value = .05
    br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = 1.3; br.inputs['Bias'].default_value = bias
    br.inputs['Color1'].default_value = (*lit, 1); br.inputs['Color2'].default_value = (.015, .02, .03, 1); br.inputs['Mortar'].default_value = (*paint, 1)
    nt.links.new(ofs.outputs[0], br.inputs['Vector'])
    ge = nt.nodes.new('ShaderNodeNewGeometry'); sn = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(ge.outputs['Normal'], sn.inputs[0])
    ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; nt.links.new(sn.outputs['Z'], ab.inputs[0])
    wall = nt.nodes.new('ShaderNodeMath'); wall.operation = 'LESS_THAN'; wall.inputs[1].default_value = .5; nt.links.new(ab.outputs[0], wall.inputs[0])
    mixc = nt.nodes.new('ShaderNodeMix'); mixc.data_type = 'RGBA'; mixc.inputs['A'].default_value = (*[c * .45 for c in paint], 1); nt.links.new(wall.outputs[0], mixc.inputs['Factor']); nt.links.new(br.outputs['Color'], mixc.inputs['B'])      # mix A = roofs: a darker shade of the paint (they face the lamp head-on)
    nt.links.new(mixc.outputs['Result'], b.inputs['Base Color'])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; nt.links.new(br.outputs['Fac'], inv.inputs[1])
    em = nt.nodes.new('ShaderNodeMath'); em.operation = 'MULTIPLY'; nt.links.new(inv.outputs[0], em.inputs[0]); nt.links.new(wall.outputs[0], em.inputs[1])
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'lit'            # per-object switch: o['lit'] 0..1
    em2 = nt.nodes.new('ShaderNodeMath'); em2.operation = 'MULTIPLY'; nt.links.new(em.outputs[0], em2.inputs[0]); nt.links.new(at.outputs['Fac'], em2.inputs[1])
    emc = nt.nodes.new('ShaderNodeMix'); emc.data_type = 'RGBA'; emc.inputs['A'].default_value = (0, 0, 0, 1); nt.links.new(em2.outputs[0], emc.inputs['Factor']); nt.links.new(br.outputs['Color'], emc.inputs['B'])
    nt.links.new(emc.outputs['Result'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.5; b.inputs['Roughness'].default_value = .55
    m['is_building'] = 1
    return m

# ---------------------------------------------------------------- her real assets
def append_real():
    with D.libraries.load(AUS, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c in ('CLAUDE_CHAR', 'PORSCHE')]
    sc = bpy.context.scene
    for c in dst.collections: sc.collection.children.link(c)
    cc = D.collections['CLAUDE_CHAR']; arm = D.objects['RIG_Claude']
    for o in cc.all_objects:
        o.animation_data_clear()
        if o.type == 'EMPTY' and o.parent is not None:
            o.rotation_euler = (0, 0, 0); o.delta_rotation_euler = (0, 0, 0)
    if arm.animation_data: arm.animation_data_clear()
    for p in arm.pose.bones: p.location = (0, 0, 0); p.rotation_mode = 'QUATERNION'; p.rotation_quaternion = (1, 0, 0, 0); p.scale = (1, 1, 1)
    Dg = math.radians
    for s, sg in (('L', -1), ('R', 1)):          # her approved rest pose (anim_lib.rest_pose) with the deadpan v2 lids
        D.objects['lidpivot_' + s].rotation_euler = (-0.567, 0, 0); D.objects['browpivot_' + s].rotation_euler = (0, sg * Dg(-6), 0)
        for f in ('index', 'middle', 'ring'):
            D.objects[f + '1_' + s].rotation_euler = (0, sg * Dg(14), 0); D.objects[f + '2_' + s].rotation_euler = (0, sg * Dg(18), 0)
        D.objects['thumb1_' + s].rotation_euler = (Dg(-22), sg * Dg(26), 0); D.objects['thumb2_' + s].rotation_euler = (Dg(-6), sg * Dg(16), 0)
    arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0)
    # the 16 hair spikes carry a deform + subsurf stack that costs ~9 s a frame to evaluate: freeze them to plain meshes
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); nfz = 0
    for o in list(cc.all_objects):
        if o.type == 'MESH' and o.name.startswith('spike'):
            dr = o.animation_data.drivers if o.animation_data else []
            print('[wb] spike', o.name, [(m.type, m.show_render) for m in o.modifiers], 'drivers', len(dr)) if nfz == 0 else None
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
            o.modifiers.clear(); o.animation_data_clear(); o.data = me; nfz += 1
    print('[wb] froze', nfz, 'spikes')
    cc.hide_render = False; cc.hide_viewport = False
    # the car: keep only CAR_ROOT's visible tree (drops the hidden driver and blackout shells), then hang it from one
    # empty, TOYCAR, at the middle of its footprint on the ground: nose toward TOYCAR's -Y, 1 unit = 1 m of real car
    pc = D.collections['PORSCHE']; car = D.objects['CAR_ROOT']; keep = set([car] + [o for o in car.children_recursive if not o.hide_render or o.type == 'EMPTY'])
    keep = set(o for o in keep if not o.name.startswith('drv_'))
    for o in list(pc.all_objects):
        if o not in keep: D.objects.remove(o, do_unlink=True)
    for o in keep: o.animation_data_clear()
    car.location = (0, 0, 0); car.rotation_euler = (0, 0, 0); car.scale = (1, 1, 1); bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in car.children_recursive if o.type == 'MESH' for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    print('[wb] car bbox', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    toy = D.objects.new('TOYCAR', None); toy.location = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z); pc.objects.link(toy); bpy.context.view_layer.update()
    car.parent = toy; car.matrix_parent_inverse = toy.matrix_world.inverted(); toy['length'] = hi.y - lo.y; toy['width'] = hi.x - lo.x; toy['height'] = hi.z - lo.z
    cal = D.materials.get('Caliper1Mtl')
    if cal:
        b = cal.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (1.0, .72, .0, 1); b.inputs['Roughness'].default_value = .35
    return arm, toy

# ---------------------------------------------------------------- render settings
def setup_render(res=(2560, 1440), samples=64, pct=100):
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = pct; sc.render.fps = 30
    e = sc.eevee
    for k, v in dict(taa_render_samples=samples, use_raytracing=True, use_shadows=True, shadow_ray_count=3, shadow_step_count=8, use_volumetric_shadows=True, volumetric_tile_size='4',
                     volumetric_samples=96, volumetric_end=12.0, use_bokeh_jittered=True, bokeh_max_size=160.0, fast_gi_method='GLOBAL_ILLUMINATION').items():
        try: setattr(e, k, v)
        except Exception as ex: print('eevee', k, ex)
    try: e.ray_tracing_options.resolution_scale = '1'; e.ray_tracing_options.trace_max_roughness = .6
    except Exception as ex: print('rt', ex)
    sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'Medium High Contrast'; sc.view_settings.exposure = 0; sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    w = D.worlds.new('WB_world'); w.use_nodes = True; bg = w.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value = (.004, .006, .012, 1); bg.inputs['Strength'].default_value = 1.0; sc.world = w
    return sc
