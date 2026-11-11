"""blclip t0 t1 [pct] [samples] [step]: render film.blend frames for film seconds [t0, t1) to build/bl/frames/c<pct>/NNNNN.jpg"""
import bpy, os, time


def main(a):
    import wb
    bpy.ops.wm.open_mainfile(filepath=os.path.join(wb.ROOT, 'songs/run-it/blender/film.blend'))
    import wbfilm
    wbfilm.load_screen(); wbfilm.install_handlers()
    sc = bpy.context.scene; t0, t1 = a[0], a[1]; pct = int(a[2]) if len(a) > 2 else 50; samples = int(a[3]) if len(a) > 3 else 24; step = int(a[4]) if len(a) > 4 else 1
    sc.render.resolution_percentage = pct; sc.eevee.taa_render_samples = samples
    # measured on the M5 at 1440p (blprof2): the haze at tile 4 / 96 samples and shadow maps for the tiny accent lights cost 60% of the
    # frame time and change nothing you can see. KEY, CLAUDE_KEY, RIM, RIM2, HAIR, MOON, FILL, mon_glow, dot_light keep their shadows.
    sc.eevee.volumetric_tile_size = '8'; sc.eevee.volumetric_samples = 64
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name in ('FLAME_l', 'MFLAME_l', 'MOON_A_glow', 'MOON_B_glow', 'wheel_kiss', 'WALLWASH', 'NIGHT_FILL'): o.data.use_shadow = False
    out = f'{wb.OUT}/frames/c{pct}'; os.makedirs(out, exist_ok=True)
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 96 if pct >= 100 else 93      # JPEG, not PNG: her disk has ~13 GB free
    sc.frame_start = wbfilm.F(t0); sc.frame_end = wbfilm.F(t1) - 1; sc.frame_step = step
    sc.render.filepath = out + '/'; sc.render.use_overwrite = (len(a) <= 5 or a[5] != 1); sc.render.use_file_extension = True      # 6th arg 1 = keep frames that already exist (resume)
    # a way to stop a long render from the chat (files cannot be deleted from there): write the word stop into build/bl/STOP
    stopf = f'{wb.OUT}/STOP'; open(stopf, 'w').write('go\n')
    def check_stop(*_):
        try:
            if open(stopf).read().strip() == 'stop': print('[blclip] STOP file says stop: quitting at frame', sc.frame_current, flush=True); os._exit(0)
        except Exception: pass
    bpy.app.handlers.render_pre.append(check_stop)
    t = time.time(); bpy.ops.render.render(animation=True); n = (sc.frame_end - sc.frame_start) // step + 1
    print('[blclip] rendered', n, 'frames in', round(time.time() - t, 1), 's =', round((time.time() - t) / max(1, n), 2), 's/frame', flush=True)
