"""Blender -b <blend> --python render3.py   env: FRAMES=60,180 (MASTER frames; blend frame = master+OFF, default +1) OUT=<dir> SAMPLES=32 RX RY
CAMS=f:name,... overrides the camera for a master frame. Never saves the blend. Linear 16-bit EXR."""
import bpy, os
sc = bpy.context.scene
OFF = int(os.environ.get("OFF", 1))
RX, RY = int(os.environ.get("RX", 1920)), int(os.environ.get("RY", 1080))
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RX, RY, 100
sc.eevee.taa_render_samples = int(os.environ.get("SAMPLES", 32))
sc.render.image_settings.file_format = "OPEN_EXR"; sc.render.image_settings.color_depth = "16"; sc.render.image_settings.exr_codec = "ZIP"
ov = {}
for kv in filter(None, os.environ.get("CAMS", "").split(",")):
    k, v = kv.split(":"); ov[int(k)] = v
out = os.environ["OUT"]; os.makedirs(out, exist_ok=True)
for fm in [int(x) for x in os.environ["FRAMES"].split(",")]:
    f = fm + OFF
    sc.frame_set(f)
    cam = None
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f and m.camera: cam = m.camera
    if fm in ov: cam = bpy.data.objects[ov[fm]]
    if cam: sc.camera = cam
    sc.render.filepath = os.path.join(out, "f%04d" % fm)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", fm, sc.camera.name)
