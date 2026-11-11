"""blasm <pct> <t_in> <t_out> <H/10> <tag>:  (H/10: 72, 108 or 144; the watcher only takes numbers up to 999)
 assemble the film in Blender's sequencer and encode it (H.264 + AAC).
  the 2D film (build/hero/mst4.mp4) up to the dissolve at 70.97-71.13,
  the workbench frames (build/bl/frames/c<pct>/NNNN.jpg|png) from 2129 to 4659,
  the 2D ending (build/hero/mst5.mp4, which starts at film frame 4660) if it exists, else mst4,
  and the film audio (build/audio/run_it_edit_v1.wav).
Writes build/bl/asm/film_<tag>.mp4 covering film seconds [t_in, t_out)."""
import bpy, os


def main(a):
    import wb
    pct = int(a[0]); t_in = a[1]; t_out = a[2]; H = int(a[3]) * 10; W = H * 16 // 9; tag = int(a[4]) if len(a) > 4 else 0
    R = os.path.join(wb.ROOT, 'songs/run-it/build'); A = R + '/hero/mst4.mp4'; C = R + '/hero/mst5.mp4'; snd = R + '/audio/run_it_edit_v1.wav'
    fdir = f'{R}/bl/frames/c{pct}'; ext = 'jpg'; FX0, FX1, FB1, FC0 = 2129, 2134, 4659, 4660
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100; sc.render.fps = 30
    sc.frame_start = int(round(t_in * 30)); sc.frame_end = int(round(t_out * 30)) - 1
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    se = sc.sequence_editor_create(); S = se.strips if hasattr(se, 'strips') else se.sequences
    def movie(name, path, ch, f0):
        try: return S.new_movie(name, path, ch, f0, fit_method='FIT')
        except TypeError: return S.new_movie(name, path, ch, f0)
    if sc.frame_start < FX1:
        sa = movie('A', A, 1, 0); sa.frame_final_end = FX1; print('[blasm] A', sa.frame_final_start, sa.frame_final_end)
    files = [f'{f:04d}.{ext}' for f in range(FX0, FB1 + 1) if os.path.exists(f'{fdir}/{f:04d}.{ext}')]
    print('[blasm] workbench frames', len(files), 'of', FB1 - FX0 + 1)
    try: sb = S.new_image('B', f'{fdir}/{files[0]}', 2, FX0, fit_method='FIT')
    except TypeError: sb = S.new_image('B', f'{fdir}/{files[0]}', 2, FX0)
    for fn in files[1:]: sb.elements.append(fn)
    if files[-1] == f'{FB1:04d}.{ext}': sb.elements.append(files[-1])      # hold the last (frozen) frame over film frame 4660: the 2D ending's own first frame is still the old 2D crash (Final starts at 4661)
    sb.blend_type = 'ALPHA_OVER'
    for f, v in ((FX0, 1 / 6), (FX1, 1.0)): sb.blend_alpha = v; sb.keyframe_insert('blend_alpha', frame=f)
    if sc.frame_end >= FC0:
        if os.path.exists(C): sc_ = movie('C', C, 1, FC0)
        else:
            sc_ = movie('C', A, 3, 0); sc_.frame_final_start = FC0
        print('[blasm] C', sc_.frame_final_start, sc_.frame_final_end, os.path.exists(C))
    ss = S.new_sound('S', snd, 5, 0)
    r = sc.render; im = r.image_settings
    try: im.media_type = 'VIDEO'
    except Exception as e: print('[blasm] media_type', e)
    im.file_format = 'FFMPEG'; ff = r.ffmpeg; ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH' if pct < 100 else 'PERC_LOSSLESS'; ff.ffmpeg_preset = 'GOOD'; ff.gopsize = 15
    ff.audio_codec = 'AAC'; ff.audio_bitrate = 256
    try: ff.audio_mixrate = 48000
    except Exception: pass
    os.makedirs(R + '/bl/asm', exist_ok=True); r.filepath = f'{R}/bl/asm/film_{tag}.mp4'; r.use_file_extension = False
    try: r.use_sequencer = True
    except Exception: pass
    bpy.ops.render.render(animation=True); print('[blasm] wrote', r.filepath, os.path.getsize(r.filepath) if os.path.exists(r.filepath) else 'MISSING')
