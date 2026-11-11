"""blcover: square stills for the album cover from film.blend (he looks at us over the running city, 1:59).
Each candidate = (name, film seconds, camera location, aim, lens mm, f-stop). -> build/cover3k/plate_<name>.jpg at 3000x3000."""
import bpy, os
from mathutils import Vector

CANDS = [
    ('A', 119.75, (-.08, -.70, .47), (-.03, .14, .67), 27, 5.6),
    ('D', 119.75, (-.08, -.70, .47), (-.03, .14, .705), 26, 5.6),
]


def main(a):
    import wb, wbfilm, wbrig
    bpy.ops.wm.open_mainfile(filepath=os.path.join(wb.ROOT, 'songs/run-it/blender/film.blend'))
    wbfilm.load_screen(); wbfilm.install_handlers()
    sc = bpy.context.scene; S = int(a[0]) * 10 if a else 3000; sc.eevee.taa_render_samples = int(a[1]) if len(a) > 1 else 128
    sc.render.resolution_x = S; sc.render.resolution_y = S; sc.render.resolution_percentage = 100
    sc.eevee.volumetric_tile_size = '4'; sc.eevee.volumetric_samples = 96
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 97
    out = os.path.join(wb.ROOT, 'songs/run-it/build/cover3k'); os.makedirs(out, exist_ok=True)
    for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
    R = wbrig.Rig(); pick = int(a[2]) if len(a) > 2 else 0
    for i, (name, t, loc, aim, lens, fs) in enumerate(CANDS):
        if pick and pick != i + 1: continue
        f = int(round(t * 30)); cd = bpy.data.cameras.new('cov' + name); cam = bpy.data.objects.new('cov' + name, cd); sc.collection.objects.link(cam)
        cam.location = loc; wb.look_at(cam, aim); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = .01; cd.clip_end = 60
        sc.camera = cam; sc.frame_set(f); bpy.context.view_layer.update()
        eye = (bpy.data.objects['eye_L'].matrix_world.translation + bpy.data.objects['eye_R'].matrix_world.translation) / 2
        cd.dof.use_dof = True; cd.dof.aperture_fstop = fs; cd.dof.focus_distance = (eye - Vector(loc)).length * .86
        R.eyes(Vector(loc), f); sc.frame_set(f)
        bpy.app.handlers.frame_change_pre.clear()
        for o in bpy.data.objects:
            if o.name in ('SCR_l1', 'SCR_l2', 'SCR_h1', 'SCR_h2', 'SCR_cur', 'SCR_big'): o.hide_render = True
        sc.camera = cam; sc.render.filepath = f'{out}/plate_{name}.jpg'; bpy.ops.render.render(write_still=True); print('[blcover] wrote', name, flush=True)
