"""bllook [variant ...]: look-dev on film.blend without a rebuild. Renders TIMES for each variant to build/bl/stills/look_v<k>_<t>.jpg.
A variant = dict(key, bounce: lamp scales; roof: scale of the paint on up-facing faces; bloom, thresh: the Glare node; win: window emission;
spark: scale on the strand bulbs / glints / rain / flame emission; ground: scale on ground, plaza, sand)."""
import bpy, os

TIMES = [75.4, 77.0, 97.4, 99.0, 106.3, 123.3, 133.7, 111.7]
BASE = dict(key=1.0, bounce=1.0, roof=1.0, bloom=.38, thresh=2.2, win=2.6, spark=1.0, ground=1.0)
VARIANTS = {0: {},
            1: dict(key=.90, roof=.55, bloom=.22, thresh=3.0, win=1.9, spark=.65, ground=.9),
            2: dict(key=.80, roof=.45, bloom=.15, thresh=3.6, win=1.5, spark=.50, ground=.85),
            3: dict(key=.90, roof=.50, bloom=.18, thresh=3.2, win=1.7, spark=.55, ground=.85, bounce=.8)}


def scale_curve(idb, path, k):
    ad = idb.animation_data
    if not (ad and ad.action): setattr(idb, path, getattr(idb, path) * k); return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if fc.data_path == path:
                        for kp in fc.keyframe_points: kp.co.y *= k; kp.handle_left.y *= k; kp.handle_right.y *= k
                        fc.update()


def apply(v):
    D = bpy.data; P = dict(BASE); P.update(VARIANTS[v])
    scale_curve(D.objects['KEY'].data, 'energy', P['key']); scale_curve(D.objects['BOUNCE'].data, 'energy', P['bounce'])
    for m in D.materials:
        if m.get('is_building') and m.name.startswith('WB_b_'):
            nt = m.node_tree; nt.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = P['win']
            for n in nt.nodes:
                if n.type == 'MIX' and n.data_type == 'RGBA' and tuple(n.inputs['A'].default_value)[:3] != (0, 0, 0):
                    c = n.inputs['A'].default_value; n.inputs['A'].default_value = (c[0] * P['roof'], c[1] * P['roof'], c[2] * P['roof'], 1)
        if m.name.startswith(('WB_fl_', 'WB_glint')):
            for n in m.node_tree.nodes:
                if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value) > 20 and not n.inputs[1].is_linked: n.inputs[1].default_value *= P['spark']; break
        if m.name in ('WB_flame', 'WB_drop', 'WB_tinybulb'):
            e = m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']; e.default_value *= P['spark']
    for name in ('WB_ground', 'WB_plaza', 'WB_sand'):
        b = D.materials[name].node_tree.nodes['Principled BSDF'].inputs['Base Color']; c = b.default_value; b.default_value = (c[0] * P['ground'], c[1] * P['ground'], c[2] * P['ground'], 1)
    for n in D.node_groups['WB_comp'].nodes:
        if n.bl_idname == 'CompositorNodeGlare': n.inputs['Strength'].default_value = P['bloom']; n.inputs['Threshold'].default_value = P['thresh']


def main(a):
    import wb, wbfilm
    for v in [int(x) for x in a] or [0, 1, 2, 3]:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(wb.ROOT, 'songs/run-it/blender/film.blend'))
        wbfilm.load_screen(); wbfilm.install_handlers(); apply(v)
        sc = bpy.context.scene; sc.render.resolution_percentage = 50; sc.eevee.taa_render_samples = 16; sc.eevee.volumetric_tile_size = '8'; sc.eevee.volumetric_samples = 64
        sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
        for t in TIMES:
            sc.frame_set(wbfilm.F(t)); sc.render.filepath = f'{wb.OUT}/stills/look_v{v}_{t:07.2f}.jpg'; bpy.ops.render.render(write_still=True)
        print('[bllook] variant', v, 'done', flush=True)
