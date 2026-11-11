"""blthumb: purpose-built thumbnail stills from film.blend (the moment he looks at us over the running city, 1:59).
Each candidate = (name, film seconds, camera location, aim, lens mm, f-stop, eyes on the lens?). -> build/thumbs/hero_<name>.jpg at 2560x1440."""
import bpy, os
from mathutils import Vector

IZ = .2975
CANDS = [
    ('T8', 119.75, (-.08, -.70, .47), (-.12, .14, .66), 19, 5.6, True),
    ('T7', 119.70, (.42, -.74, .52), (.12, .12, .66), 22, 5.6, True),
    ('T9', 119.75, (-.07, -.60, .46), (-.11, .14, .68), 18, 5.6, True),
]


def main(a):
    import wb, wbfilm, wbrig
    bpy.ops.wm.open_mainfile(filepath=os.path.join(wb.ROOT, 'songs/run-it/blender/film.blend'))
    wbfilm.load_screen(); wbfilm.install_handlers()
    sc = bpy.context.scene; sc.render.resolution_percentage = int(a[0]) if a else 100; sc.eevee.taa_render_samples = int(a[1]) if len(a) > 1 else 96
    sc.eevee.volumetric_tile_size = '4'; sc.eevee.volumetric_samples = 96
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 96
    out = os.path.join(wb.ROOT, 'songs/run-it/build/thumbs'); os.makedirs(out, exist_ok=True)
    for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
    R = wbrig.Rig()
    for name, t, loc, aim, lens, fs, look in CANDS:
        f = int(round(t * 30)); cd = bpy.data.cameras.new(name); cam = bpy.data.objects.new(name, cd); sc.collection.objects.link(cam)
        cam.location = loc; wb.look_at(cam, aim); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = .01; cd.clip_end = 60
        sc.camera = cam; sc.frame_set(f); bpy.context.view_layer.update()
        eye = (bpy.data.objects['eye_L'].matrix_world.translation + bpy.data.objects['eye_R'].matrix_world.translation) / 2
        cd.dof.use_dof = True; cd.dof.aperture_fstop = fs; cd.dof.focus_distance = (eye - Vector(loc)).length * .86      # between the city and his face
        if look: R.eyes(Vector(loc), f); sc.frame_set(f)
        bpy.app.handlers.frame_change_pre.clear()                      # the headline sits over the monitor on the cover: no prompt text behind it
        for o in bpy.data.objects:
            if o.name in ('SCR_l1', 'SCR_l2', 'SCR_h1', 'SCR_h2', 'SCR_cur', 'SCR_big'): o.hide_render = True
        sc.camera = cam; sc.render.filepath = f'{out}/hero_{name}.jpg'; bpy.ops.render.render(write_still=True); print('[blthumb] wrote', name, 'eye', [round(x, 3) for x in eye], flush=True)
