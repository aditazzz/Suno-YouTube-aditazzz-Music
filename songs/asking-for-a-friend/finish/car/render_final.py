"""Final frames for the GT3 RS shots, resumable, MASTER frame numbers on disk.
Blender -b <copy.blend> --python render_final.py -- <outdir> <master_a> <master_b> <offset> [samples] [W H]
 blend frame = master + offset (v1/post1: +1; outro: -3738). One animation render of the missing span (Eevee keeps its
 shaders between frames), then files are renamed f_<blend>.png -> f_<master>.png. Writes sec.json (s/frame)."""
import bpy, sys, os, time, json, glob
A = sys.argv[sys.argv.index("--") + 1:]
out, ma, mb, off = A[0], int(A[1]), int(A[2]), int(A[3]); os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; r = sc.render
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plate.py")).read())   # r1_fix: licence plate (text in plate/PLATE_TEXT.txt)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wheels.py")).read())   # fix_wheels: spin = ground speed, radial smear, tyre detail (WHEELS=0 = old)
SM = int(A[4]) if len(A) > 4 and A[4] != "-" else 64
W, H = (int(A[5]), int(A[6])) if len(A) > 6 else (2560, 1440)
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
sc.eevee.taa_render_samples = SM
if os.environ.get("SHUTTER"): r.motion_blur_shutter = float(os.environ["SHUTTER"]); print("[final] shutter", r.motion_blur_shutter)
r.image_settings.file_format = "PNG"; r.image_settings.color_depth = "16"; r.image_settings.color_mode = "RGB"
# leftovers from a killed run (blend-numbered or empty) go
for p in glob.glob(os.path.join(out, "b_*.png")): os.remove(p)
todo = [m for m in range(ma, mb + 1) if not os.path.exists(os.path.join(out, f"f_{m:04d}.png")) or os.path.getsize(os.path.join(out, f"f_{m:04d}.png")) == 0]
if not todo: print("[final] nothing to do", ma, mb); sys.exit(0)
sc.frame_start, sc.frame_end = todo[0] + off, todo[-1] + off
r.filepath = os.path.join(out, "b_####"); r.use_file_extension = True; r.use_overwrite = True; r.use_placeholder = False
T = {}
def pre(scene, *a): T["t"] = time.time()
def post(scene, *a):
    sj = os.path.join(out, "sec.json"); S = json.load(open(sj)) if os.path.exists(sj) else {}
    S[str(scene.frame_current - off)] = round(time.time() - T["t"], 2); json.dump(S, open(sj, "w"))
    print("[final]", scene.frame_current - off, S[str(scene.frame_current - off)], "s", flush=True)
bpy.app.handlers.render_pre.append(pre); bpy.app.handlers.render_post.append(post)
t0 = time.time(); bpy.ops.render.render(animation=True)
n = 0
for m in todo:
    p = os.path.join(out, f"b_{m + off:04d}.png")
    if os.path.exists(p): os.replace(p, os.path.join(out, f"f_{m:04d}.png")); n += 1
print("[final] done", todo[0], todo[-1], n, "frames", round(time.time() - t0, 1), "s total", flush=True)
