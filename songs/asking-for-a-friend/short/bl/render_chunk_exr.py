"""LOCK 11 film: render_chunk.py writing scene-linear EXR film_fNNNN.exr (the grade, tools/grade.py, is the next step). Resumable: Blender -b <short_SX.blend> --python render_chunk.py -- <outdir> <fa> <fb> [samples]
Renders f_<NNNN>.png for fa..fb as ONE animation render (Eevee keeps its compiled shaders between frames; a still
per frame re-compiles them: ~28 s of fixed cost a frame, measured), skipping frames already on disk (no overwrite,
placeholders: a killed job leaves an empty placeholder, which is removed and re-rendered on the next run).
Logs s/frame to <outdir>/sec.json."""
import bpy, sys, os, time, json
A = sys.argv[sys.argv.index("--") + 1:]
out, fa, fb = A[0], int(A[1]), int(A[2]); os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; r = sc.render; r.resolution_percentage = 100; r.use_compositing = False
if len(A) > 3 and A[3] != "-": sc.eevee.taa_render_samples = int(A[3])
for f in range(fa, fb + 1):   # empty placeholders from a killed run go
    p = os.path.join(out, f"film_f{f:04d}.exr")
    if os.path.exists(p) and os.path.getsize(p) == 0: os.remove(p)
todo = [f for f in range(fa, fb + 1) if not os.path.exists(os.path.join(out, f"film_f{f:04d}.exr"))]
if not todo:
    print("[chunk] nothing to do", fa, fb); sys.exit(0)
sc.frame_start, sc.frame_end = todo[0], todo[-1]
r.filepath = os.path.join(out, "film_f####"); r.use_file_extension = True
r.use_overwrite = False; r.use_placeholder = True
T = {}
def pre(scene, *a): T["t"] = time.time()
def post(scene, *a):
    sj = os.path.join(out, "sec.json"); S = json.load(open(sj)) if os.path.exists(sj) else {}
    S[str(scene.frame_current)] = round(time.time() - T["t"], 2); json.dump(S, open(sj, "w"))
    print("[chunk]", scene.frame_current, S[str(scene.frame_current)], "s", flush=True)
bpy.app.handlers.render_pre.append(pre); bpy.app.handlers.render_post.append(post)
t0 = time.time(); bpy.ops.render.render(animation=True)
print("[chunk] done", todo[0], todo[-1], round(time.time() - t0, 1), "s total", flush=True)
