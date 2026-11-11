"""blcam [pct]: camera look-dev on film.blend. Renders each candidate in CANDS (edit this file) to build/bl/stills/cam_<k>.jpg"""
import bpy, os
from mathutils import Vector

# (film seconds, location, aim, lens mm, f-stop, focus point)
CANDS = [
    (155.30, (-.21, -.63, .55), (-.24, .25, .62), 24, 5.6, (-.552, .036, .433)),
    (155.30, (-.30, -.52, .50), (-.30, .25, .60), 22, 5.6, (-.552, .036, .433)),
    (155.30, (-.36, -.60, .47), (-.30, .25, .62), 26, 5.6, (-.552, .036, .433)),
    (155.30, (-.16, -.72, .60), (-.25, .25, .62), 28, 5.6, (-.552, .036, .433)),
]


def main(a):
    import wb, wbfilm
    bpy.ops.wm.open_mainfile(filepath=os.path.join(wb.ROOT, 'songs/run-it/blender/film.blend'))
    wbfilm.load_screen(); wbfilm.install_handlers()
    sc = bpy.context.scene; sc.render.resolution_percentage = int(a[0]) if a else 34; sc.eevee.taa_render_samples = 16
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
    for k, (t, loc, aim, lens, fs, foc) in enumerate(CANDS):
        cd = bpy.data.cameras.new(f'CAND{k}'); cam = bpy.data.objects.new(f'CAND{k}', cd); sc.collection.objects.link(cam)
        cam.location = loc; wb.look_at(cam, aim); cd.lens = lens; cd.sensor_width = 36; cd.dof.use_dof = True; cd.dof.aperture_fstop = fs; cd.dof.focus_distance = (Vector(foc) - Vector(loc)).length
        cd.clip_start = .01; cd.clip_end = 60
        for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
        sc.camera = cam; sc.frame_set(wbfilm.F(t)); sc.camera = cam
        sc.render.filepath = f'{wb.OUT}/stills/cam_{k}.jpg'; bpy.ops.render.render(write_still=True); print('[blcam] rendered', k, flush=True)
