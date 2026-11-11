"""blfilm [pct] [samples] [t ...]: build the whole workbench film scene, animate every shot, save film.blend, render stills at the given film times."""
import bpy, os, time


def cam_at(sc, f):
    best = None
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f and m.camera is not None: best = m.camera
    return best


def main(a):
    pct = int(a[0]) if a else 50; samples = int(a[1]) if len(a) > 1 else 24; times = a[2:]
    tf = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'bl', 'times.txt')
    if not times and os.path.isfile(tf): times = [float(x) for x in open(tf).read().split()]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import wb, wbfilm
    t0 = time.time(); S = wbfilm.build(samples, pct); wbfilm.animate(S); sc = bpy.context.scene
    print('[blfilm] built + animated in', round(time.time() - t0, 1), 's'); os.makedirs(wb.OUT + '/stills', exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(wb.ROOT, 'songs/run-it/blender/film.blend'))
    for t in times:
        f = wbfilm.F(t); sc.frame_set(f); sc.camera = cam_at(sc, f) or sc.camera
        if sc.camera is None: print('[blfilm] no camera at', t); continue
        sc.render.filepath = f'{wb.OUT}/stills/f_{t:07.2f}.png'; t1 = time.time(); bpy.ops.render.render(write_still=True); print('[blfilm] still', t, sc.camera.name, round(time.time() - t1, 1), 's', flush=True)
