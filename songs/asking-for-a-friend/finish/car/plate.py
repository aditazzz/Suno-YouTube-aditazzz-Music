"""plate.py: exec'd by render_stills.py / render_final.py after the .blend opens (never saved into it). Adds the rear licence
plate to the GT3 RS (parent CAR_ROOT). The text is ONE variable: plate/PLATE_TEXT.txt (set with plate/make_plate.py "TEXT",
which also redraws plate/plate.png). No real state, brand or slogan. Rear-only (what S024/S139-141 see)."""
import bpy, os
from mathutils import Vector
_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plate")
# PLATE_STYLE (env wins, else plate/PLATE_STYLE.txt): "plain" = the old flat plate, "texas" = Texas plate (plate_texas.png) in a plate frame.
_STYLE = os.environ.get("PLATE_STYLE") or (open(os.path.join(_P, "PLATE_STYLE.txt")).read().strip() if os.path.exists(os.path.join(_P, "PLATE_STYLE.txt")) else "plain")
def _add_frame(car, w, h):
    """Plate frame as real geometry: four thin raised satin-black bars (blank, no dealer/brand text) around the plate, slightly proud of it."""
    bw, bb, d = 0.022, 0.040, 0.018     # side/top bar width, thicker bottom bar, depth
    ow, oh = w + 2*bw, h + bw + bb
    cz = -(bb - bw) / 2                # frame centre is lower than plate centre (thicker bottom bar)
    verts, faces = [], []
    def box(x0, x1, z0, z1):
        i = len(verts)
        for y in (0, -d):
            verts.extend([(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)])
        faces.extend([(i,i+1,i+2,i+3),(i+4,i+7,i+6,i+5),(i,i+4,i+5,i+1),(i+1,i+5,i+6,i+2),(i+2,i+6,i+7,i+3),(i+3,i+7,i+4,i)])
    box(-ow/2, ow/2, h/2, h/2+bw); box(-ow/2, ow/2, -h/2-bb, -h/2); box(-ow/2, -w/2, -h/2, h/2); box(w/2, ow/2, -h/2, h/2)
    me = bpy.data.meshes.new("GT3_PLATE_FRAME_m"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new("GT3_PLATE_FRAME", me); bpy.context.scene.collection.objects.link(o)
    o.parent = car; o.location = (0.0, 2.27 - 0.003, 0.45); o.rotation_euler = (0, 0, 3.1415926)   # local +y of the object = away from the plate face toward the viewer after the 180-degree turn
    m = bpy.data.materials.new("GT3_PLATE_FRAME_mat"); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.02, 0.02, 0.022, 1); b.inputs["Roughness"].default_value = 0.35; b.inputs["Metallic"].default_value = 0.6
    o.data.materials.append(m)
def _add_plate():
    car = bpy.data.objects.get("CAR_ROOT")
    if not car or bpy.data.objects.get("GT3_PLATE"): return
    me = bpy.data.meshes.new("GT3_PLATE_m")
    w, h = 0.66, 0.19   # a hair larger than a real plate so it reads at phone size
    me.from_pydata([(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2),(-w/2,0,h/2)], [], [(0,1,2,3)]); me.update()
    uv = me.uv_layers.new(name="UV"); 
    for l, (u, v) in zip(me.loops, ((0,0),(1,0),(1,1),(0,1))): uv.data[l.index].uv = (u, v)
    o = bpy.data.objects.new("GT3_PLATE", me); bpy.context.scene.collection.objects.link(o)
    o.parent = car; o.location = (0.0, 2.27, 0.45)         # car-local; the car's REAR is +y here: rear face y=2.22-2.25 at z .40-.45 (ray-cast), plate ~1 cm proud
    o.rotation_euler = (0, 0, 3.1415926)      # faces +y, text readable from behind (viewer's right = -x)
    m = bpy.data.materials.new("GT3_PLATE_mat"); m.use_nodes = True; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(_P, os.environ.get("PLATE_FILE") or ("plate_texas.png" if _STYLE == "texas" else "plate.png")), check_existing=False)   # notes_r1: PLATE_FILE=<name in plate/> overrides (unset = unchanged)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.45
    o.data.materials.append(m)
    if _STYLE == "texas": _add_frame(car, w, h)
    bpy.context.view_layer.update()
_add_plate()
