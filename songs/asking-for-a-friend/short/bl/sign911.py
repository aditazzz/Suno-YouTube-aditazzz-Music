"""Blender -b <in.blend> --python sign911.py -- <out.blend>: the emergency sign becomes CALL 911 (design round 2: 0.62 x 0.52 m, 1860x1560).
Reloads the texture (already swapped on disk) and resizes the face and backplate about their centres. Nothing else changes."""
import bpy, sys
O = bpy.data.objects
for im in bpy.data.images:
    if im.filepath.endswith("emergency/sign.png"): im.reload(); print("[sign911] reloaded", im.size[:])
def resize(o, hw, hh):   # box/plane, local verts: x -> half width hw, z -> half height hh about the bbox centre
    vs = o.data.vertices; xs = [v.co.x for v in vs]; zs = [v.co.z for v in vs]
    cx = (min(xs)+max(xs))/2; cz = (min(zs)+max(zs))/2
    for v in vs:
        v.co.x = cx + (hw if v.co.x > cx else -hw); v.co.z = cz + (hh if v.co.z > cz else -hh)
    o.data.update()
resize(O["esign_face"], 0.31, 0.26)
resize(O["sign_backplate_e"], 0.322, 0.272)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--")+1], copy=False)
