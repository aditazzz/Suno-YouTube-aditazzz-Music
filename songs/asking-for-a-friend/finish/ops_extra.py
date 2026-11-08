"""finish_6 stage 2: billing / pile / ops-wall / per-shot face light on top of lobby_look.py's `server` output (own file, edited in place).
  Blender -b <ops_look_X.blend> --python ops_extra.py -- <verse1|chorus1|verse2|bridge|memoir>
Tunables (env): BLG billing light gain, FACE_K face-light W per m^2, OPS_RED red-alert scale, PILE_GAIN."""
import bpy, os, sys, math
from mathutils import Vector
E = lambda k, d: float(os.environ.get(k, d))
sc = bpy.context.scene
MODE = sys.argv[sys.argv.index("--") + 1]
DOCS = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender")
M = bpy.data.materials


def tint_copy(src, new, rgb, rough=None):
    """copy of an approved textured material with the texture multiplied by a colour."""
    if new in M: return M[new]
    m = M[src].copy(); m.name = new; nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    l = bs.inputs["Base Color"].links[0] if bs.inputs["Base Color"].links else None
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0; mx.inputs["B"].default_value = (*rgb, 1)
    if l:
        nt.links.new(l.from_socket, mx.inputs["A"]); nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
    else:
        mx.inputs["A"].default_value = bs.inputs["Base Color"].default_value; nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
    if rough is not None: bs.inputs["Roughness"].default_value = rough
    return m


def remap(mp):
    n = 0
    for o in bpy.data.objects:
        for s in o.material_slots:
            if s.material and s.material.name in mp and mp[s.material.name] in M:
                s.material = M[mp[s.material.name]]; n += 1
    print("[ops] remapped", n, "slots")


# ---- billing + pile materials (approved textures, the room's own colours)
tint_copy("AFF_paper", "ops_paper", (1.0, 0.97, 0.88))
tint_copy("AFF_paper", "ops_paper_pile", (0.95, 0.93, 0.85))
tint_copy("AFF_paper", "ops_kraft", (0.62, 0.42, 0.22), rough=0.8)
tint_copy("AFF_rack_painted_steel", "ops_teal_frame", (0.1, 0.9, 0.75))
tint_copy("AFF_plastic_black", "ops_stamp_red", (6.0, 0.35, 0.3))
tint_copy("AFF_desk_laminate", "ops_stamp_wood", (0.5, 0.3, 0.2))
remap({"v1_srv_floor": "AFF_srv_concrete_dusty", "v1_srv_wall": "AFF_srv_wall", "v1_srv_steel": "AFF_steel_dark_anodised",
       "v1_belt_rubber": "AFF_rubber_black", "v1_desk_top_dark": "AFF_desk_laminate", "v1_invoice_paper": "ops_paper",
       "v1_invoice_pile": "ops_paper_pile", "v1_stamp_wood": "ops_stamp_wood", "v1_stamp_red": "ops_stamp_red",
       "v1_bl_frame_teal": "ops_teal_frame", "v1_beige_case": "ops_kraft"})

# the founder's photo in the pile: the missing path points at the old folder
for im in bpy.data.images:
    if im.name == "portrait_visionary.png":
        p = os.path.join(DOCS, "textures", "portrait_visionary.png")
        if os.path.exists(p): im.filepath = p; im.reload()

# billing room lights: a bit more of the same sources
BLG = E("BLG", 2.2)
for o in bpy.data.objects:
    if o.type == "LIGHT" and o.name.startswith("BL_") and not (o.data.animation_data and o.data.animation_data.action):
        o.data.energy *= BLG
# visible fixtures for the billing room lights: a steel hood + a frosted tube under each (the area light sits at the tube)
bl = bpy.data.collections.get("BILLING")
if bl and "AFF_aisle_tube_cold" in M:
    import bmesh
    for o in [x for x in bpy.data.objects if x.type == "LIGHT" and x.name.startswith("BL_room")]:
        for kind, sc_, dz, mat in (("tube", (1.6, 0.12, 0.04), -0.02, "AFF_aisle_tube_cold"), ("hood", (1.7, 0.3, 0.05), 0.04, "AFF_steel_dark_anodised")):
            me = bpy.data.meshes.new(f"fx_{kind}_{o.name}"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
            fx = bpy.data.objects.new(me.name, me); fx.scale = sc_; fx.location = o.location + Vector((0, 0, dz)); fx.data.materials.append(M[mat]); bl.objects.link(fx)

# red alert on the ops wall: it lights the room, not Claude's face
for n in ("OPS_red",):
    o = bpy.data.objects.get(n)
    if o and o.data.animation_data and o.data.animation_data.action:
        for lay in o.data.animation_data.action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        if fc.data_path == "energy":
                            for k in fc.keyframe_points: k.co.y *= E("OPS_RED", 0.5); k.handle_left.y *= E("OPS_RED", 0.5); k.handle_right.y *= E("OPS_RED", 0.5)

# global stop-down: the first stills measured median 0.4-0.6 (washed, over the 0.32 mean ceiling): every static light and the world x LG
LG = E("LG", 0.5)
for o in bpy.data.objects:
    if o.type == "LIGHT" and not o.name.startswith("L_face") and not (o.data.animation_data and o.data.animation_data.action):
        if o.data.animation_data and o.data.animation_data.drivers: continue
        o.data.energy *= LG
if sc.world and sc.world.node_tree:
    for n in sc.world.node_tree.nodes:
        if n.type == "BACKGROUND": n.inputs["Strength"].default_value *= LG

# ---- per-shot face/key light: a soft area light on the camera, on only inside its shot
SHOTS = {
    "verse1": [("S025", 969, 1009, "CAM_v1i_bill", 990, 1.0), ("S026", 1010, 1053, "CAM_v1j_3q", 1035, 1.0)],
    "chorus1": [("S039", 1615, 1627, "CAM_c7b_hub", 1622, 1.6)],
    "verse2": [("S054", 2143, 2158, "CAM_v2d2_claude", 2150, 0.8), ("S060", 2295, 2345, "CAM_v2h_pile", 2330, 2.0),
               ("S061", 2346, 2387, "CAM_p2a_binder", 2370, 0.8), ("S062", 2388, 2404, "CAM_p2a_face", 2398, 0.8),
               ("S063", 2405, 2422, "CAM_p2b_wall", 2415, 1.0), ("S064", 2423, 2446, "CAM_p2b_face", 2440, 0.7),
               ("S065", 2447, 2496, "CAM_p2c_fix", 2480, 1.2), ("S068", 2568, 2591, "CAM_p2d_claude", 2585, 0.8)],
    "bridge": [("S081", 3197, 3261, "CAM_b1_cu", 3240, 1.0), ("S082", 3262, 3310, "CAM_b2_wide", 3300, 1.6),
               ("S092", 3509, 3558, "CAM_b7_seasons", 3545, 1.0), ("S094", 3586, 3648, "CAM_b8_claude", 3600, 1.0)],
    "memoir": [("S096", 3680, 3776, "CAM_m2_cu", 3760, 0.8)],
    # chorus2b (c2b_relook): only the Claude-in-frame cameras get a face light (c2b_6/7/8 shoot the C2_KEY/WALL/BADGE gag sets, no Claude)
    "chorus2b": [("S072", 2741, 2785, "CAM_c2b_4", 2763, 1.0), ("S079", 3040, 3129, "CAM_c2b_10", 3085, 1.0), ("S080", 3130, 3196, "CAM_c2b_11", 3160, 1.0)],
}[MODE]
FK = E("FACE_K", 30.0)
for name, a, b, cn, pf, mult in SHOTS:
    cam = bpy.data.objects[cn]
    sc.frame_set(pf + 1)
    hd = bpy.data.objects["head"].matrix_world.translation
    d = max(0.5, (hd - cam.matrix_world.translation).length)
    en = FK * d * d * mult * E("FK_" + name, 1.0)
    ld = bpy.data.lights.new("L_face_" + name, "AREA"); ld.shape = "RECTANGLE"; ld.size = 0.6 * max(1, d * 0.6); ld.size_y = ld.size * 0.7
    ld.color = (1.0, 0.92, 0.82)
    lo = bpy.data.objects.new("L_face_" + name, ld); sc.collection.objects.link(lo)
    lo.parent = cam; lo.location = (-0.12 * d, 0.10 * d, -0.1); lo.rotation_euler = (0, 0, 0)
    ld.energy = 0.0; ld.keyframe_insert("energy", frame=1)
    ld.energy = en; ld.keyframe_insert("energy", frame=a + 1)
    ld.energy = 0.0; ld.keyframe_insert("energy", frame=b + 2)
    for lay in ld.animation_data.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points: k.interpolation = "CONSTANT"
    print(f"[ops] face light {name}: d={d:.2f} W={en:.0f}")
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("[ops] saved", bpy.data.filepath)
