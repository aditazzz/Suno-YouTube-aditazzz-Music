"""412-AGENT HALL look (finish_5): the approved look (PBR on every surface, real sources only, Filmic lifted toe, linear render +
separate grade) on the OPS hall of master v1's blends, plus the escalation as LIGHTING STATE and three new cameras.
Saves a COPY. Cameras (except the three new ones), Claude, agents and timing stay master v1's.

  Blender -b <master v1 blend> --python hall_look.py -- <section> <out.blend>
  section: chorus2b (aff_12: S069 new cam, S078) | memoir (aff_07: S098, S107 new cam, S114) |
           final (aff_08: S115 S116 S120 S122 S129 new cam) | outro (aff_10: S136 S145 S147)
(post1 = S043/S044 is the server-room ballet, not the OPS hall: built with lobby_look.py server, see STATUS.)
Tunables via env: HL_TUBE (row lamp W), HL_GLOW (row screen glow W), HL_COVE, HL_FRONT, HL_FACE.
"""
import bpy, os, sys, math, json, bmesh
from mathutils import Vector

DOCS = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender")
PH = os.path.join(DOCS, "textures", "ph")
SRC_S2 = os.path.expanduser("~/Studio/asking-for-a-friend/blender/short/short169_S2_LOCK12b.blend")
E = lambda k, d: float(os.environ.get(k, d))
sc = bpy.context.scene
SECTION, OUT = sys.argv[sys.argv.index("--") + 1:][:2]

X0, XA, XB = 646.0, 658.6, 661.4          # agent columns (x 646..674, aisle at 660)
NROW, ROW0, PITCH = 20, 1.76, 1.6         # agent y = ROW0 + k*PITCH, desk y = agent y - 0.36
CX = 660.0

# ------------------------------------------------------------------ the escalation (lighting state per shot)
# rows: how many rows (from the front) are lit; lamp/screen: level 0..1 of the row lamps and monitor glow;
# cove: wall coves + floor guide strips (0 off .. 1 full); led: agent status-light colour
STATE = {
    # shot: (blend start frame, rows_lit, lamp, screen, cove, led)
    "S069": (2593, 12, 0.85, 0.9, 0.15, "amber"),   # the hall wakes: 12 of 20 rows
    "S078": (2965, 20, 1.0, 1.0, 0.35, "green"),    # every row lit, green status lights
    "S098": (3819, 20, 0.55, 0.8, 0.25, "green"),   # the hall at rest while he reads his memoir
    "S107": (4061, 20, 0.7, 0.8, 0.45, "green"),
    "S114": (4252, 20, 0.6, 0.85, 0.3, "green"),
    "S115": (4285, 20, 1.0, 1.0, 1.0, "green"),     # the drop: all 412, rows + coves + floor guides on
    "S116": (4329, 20, 1.0, 1.0, 1.0, "green"),
    "S120": (4483, 20, 1.0, 1.0, 1.0, "green"),
    "S122": (4561, 20, 1.0, 1.0, 1.0, "green"),
    "S129": (4757, 20, 1.0, 1.0, 1.0, "green"),
    "S136": (5262, 20, 1.0, 1.0, 1.0, "green"),     # the payoff, the high wide: the count IS the picture
    "S145": (5892, 20, 1.0, 1.0, 1.0, "green"),
    "S147": (5942, 20, 1.0, 1.0, 1.0, "green"),
}
SECT = {"chorus2b": ["S069", "S078"], "memoir": ["S098", "S107", "S114"],
        "final": ["S115", "S116", "S120", "S122", "S129"], "outro": ["S136", "S145", "S147"]}
SHOTS = SECT[SECTION]


# ------------------------------------------------------------------ helpers (as boardroom_look.py)
def img(path, nc=False):
    im = bpy.data.images.load(path, check_existing=True)
    if nc: im.colorspace_settings.name = "Non-Color"
    return im


def pbr(name, asset, tile_m, tint=(1, 1, 1), rough_gain=1.0, rough_bias=0.0, metal=0.0, bump=0.3, bump_dist=0.01, coat=0.0, coat_rough=0.12, spec=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    N = nt.nodes.new; L = nt.links.new
    out = N("ShaderNodeOutputMaterial"); bs = N("ShaderNodeBsdfPrincipled"); geo = N("ShaderNodeNewGeometry"); mp = N("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile_m,) * 3
    L(geo.outputs["Position"], mp.inputs["Vector"])
    d = os.path.join(PH, asset)

    def tex(kind, nc):
        n = N("ShaderNodeTexImage"); fn = [f for f in os.listdir(d) if f"_{kind}_" in f][0]
        n.image = img(os.path.join(d, fn), nc); n.projection = "BOX"; n.projection_blend = 0.25; n.interpolation = "Cubic"
        L(mp.outputs["Vector"], n.inputs["Vector"]); return n
    td, tr, tdisp = tex("diff", False), tex("rough", True), tex("disp", True)
    mix = N("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0; mix.inputs["B"].default_value = (*tint, 1)
    L(td.outputs["Color"], mix.inputs["A"]); L(mix.outputs["Result"], bs.inputs["Base Color"])
    ra = N("ShaderNodeMath"); ra.operation = "MULTIPLY_ADD"; ra.use_clamp = True
    ra.inputs[1].default_value = rough_gain; ra.inputs[2].default_value = rough_bias
    L(tr.outputs["Color"], ra.inputs[0]); L(ra.outputs[0], bs.inputs["Roughness"])
    bp = N("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = bump_dist
    L(tdisp.outputs["Color"], bp.inputs["Height"]); L(bp.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Metallic"].default_value = metal
    bs.inputs["Coat Weight"].default_value = coat; bs.inputs["Coat Roughness"].default_value = coat_rough
    if "Specular IOR Level" in bs.inputs: bs.inputs["Specular IOR Level"].default_value = spec
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    return m


def emit_mat(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs["Surface"]); return m, e


def solid(name, color, rough, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    nt.links.new(b.outputs[0], o.inputs["Surface"]); return m


def box(name, loc, size, mat, coll):
    me = bpy.data.meshes.new(name); sx, sy, sz = (s / 2 for s in size)
    vs = [(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
    me.from_pydata(vs, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]); me.update()
    ob = bpy.data.objects.new(name, me); ob.location = loc; me.materials.append(mat); coll.objects.link(ob); return ob


def cyl(name, loc, r, h, mat, coll, verts=16, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=h); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.location = loc; ob.rotation_euler = rot; me.materials.append(mat); coll.objects.link(ob); return ob


def light(name, kind, loc, rot, color, energy, size=0.3, size_y=None, coll=None, spot=None, blend=0.6, shadow=True):
    ld = bpy.data.lights.new(name, kind); ld.color = color; ld.energy = energy
    if kind == "AREA":
        ld.size = size
        if size_y: ld.shape = "RECTANGLE"; ld.size_y = size_y
    else: ld.shadow_soft_size = size
    if kind == "SPOT": ld.spot_size = spot or math.radians(90); ld.spot_blend = blend
    ld.use_shadow = shadow
    ob = bpy.data.objects.new(name, ld); coll.objects.link(ob); ob.location = loc; ob.rotation_euler = rot; return ob


def aim(frm, to): return (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()


def key_const(idb, path, frame, value, index=-1):
    """keyframe + constant interpolation (a lighting STATE changes at the cut, never fades)"""
    obj = idb
    if isinstance(value, (tuple, list)):
        for i, v in enumerate(value): pass
    obj.keyframe_insert(path, frame=frame, index=index)


def set_const(action_owner):
    ad = action_owner.animation_data
    if not ad or not ad.action: return
    for fc in ad.action.layers[0].strips[0].channelbags[0].fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"


# ------------------------------------------------------------------ 0. scene settings + Claude's approved materials from the approved blend
with bpy.data.libraries.load(SRC_S2, link=False) as (s, d):
    d.scenes = [s.scenes[0]]
    d.materials = [m for m in s.materials if m.startswith("Claude_")]
ss = d.scenes[0]
for k in dir(sc.eevee):
    if k.startswith(("_", "bl_", "rna")) or k == "ray_tracing_options": continue
    try: setattr(sc.eevee, k, getattr(ss.eevee, k))
    except Exception: pass
for k in dir(sc.eevee.ray_tracing_options):
    if k.startswith(("_", "bl_", "rna")): continue
    try: setattr(sc.eevee.ray_tracing_options, k, getattr(ss.eevee.ray_tracing_options, k))
    except Exception: pass
sc.render.use_motion_blur = ss.render.use_motion_blur
bpy.data.scenes.remove(ss)
sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium Contrast"; sc.view_settings.exposure = 0.0
sc.display_settings.display_device = "sRGB"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.002, 0.0026, 0.0045, 1)
swapped = 0
for m in list(bpy.data.materials):
    if m.name.startswith("Claude_") and not m.name.endswith(".001"):
        new = bpy.data.materials.get(m.name + ".001")
        if new: m.user_remap(new); swapped += 1
print("[hall] Claude_* materials swapped to the approved ones:", swapped)

OPS = bpy.data.collections["OPS"]
# v1's invisible overhead panels + key are replaced by real fixtures
for n in [o.name for o in OPS.objects if o.name.startswith(("OPS_ov", "OPS_key"))]:
    bpy.data.objects[n].hide_render = True
for o in bpy.data.objects:
    if any(c.name == "FOUNDER" for c in o.users_collection): o.hide_render = True

# ------------------------------------------------------------------ 1. real PBR on every surface
pbr("hall_floor", "painted_concrete_02", 2.4, tint=(0.34, 0.36, 0.40), rough_gain=0.8, rough_bias=0.12, bump=0.5, coat=0.35, coat_rough=0.18, spec=0.5)
pbr("hall_wall", "plaster_grey_04", 2.2, tint=(0.36, 0.40, 0.48), rough_gain=1.0, bump=0.5)
pbr("hall_desk", "black_walnut_veneer_01", 0.9, tint=(0.55, 0.40, 0.32), rough_gain=0.8, rough_bias=0.05, bump=0.25, coat=0.3, coat_rough=0.25)
pbr("hall_leg", "metal_plate_02", 0.4, tint=(0.14, 0.15, 0.17), metal=0.85, rough_gain=0.8, bump=0.3)
pbr("hall_steel", "metal_plate_02", 0.5, tint=(0.10, 0.10, 0.11), metal=0.85, rough_gain=0.8, bump=0.3)
for nm, new in (("ops_floor", "hall_floor"), ("ops_wall", "hall_wall"), ("ops_desk", "hall_desk"), ("ops_leg", "hall_leg")):
    bpy.data.materials[nm].user_remap(bpy.data.materials[new])
pl = bpy.data.materials["plastic_black"]
for n in pl.node_tree.nodes:
    if n.type == "BSDF_PRINCIPLED": n.inputs["Roughness"].default_value = 0.35
# the shared laptop screen on every desk goes dark glass: each row gets its own screen below, so a row can switch on
off_scr = solid("hall_scr_off", (0.01, 0.012, 0.016), 0.08)
proto_scr = bpy.data.objects["opd_scr"]
base_me = proto_scr.data
scr_verts = [proto_scr.matrix_world @ v.co for v in base_me.vertices]
scr_faces = [tuple(p.vertices) for p in base_me.polygons]
proto_scr.data.materials.clear(); proto_scr.data.materials.append(off_scr)
# the logo on every lid is a printed mark, not a light
lg = bpy.data.materials["ops_logo"]; lg.node_tree.nodes.clear()
lo = lg.node_tree.nodes.new("ShaderNodeOutputMaterial"); lb = lg.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
lb.inputs["Base Color"].default_value = (0.6, 0.25, 0.12, 1); lb.inputs["Roughness"].default_value = 0.5
lg.node_tree.links.new(lb.outputs[0], lo.inputs["Surface"])
# agent status LED: amber standby -> green (keyed per shot below). It is a real LED (0.02 m).
led = bpy.data.materials["agent_led"]; led.node_tree.nodes.clear()
lo2 = led.node_tree.nodes.new("ShaderNodeOutputMaterial"); le = led.node_tree.nodes.new("ShaderNodeEmission")
led.node_tree.links.new(le.outputs[0], lo2.inputs["Surface"])
le.inputs["Strength"].default_value = 6.0

# ------------------------------------------------------------------ 2. fixtures: row lamps, row screens, coves, floor guides, truss, front cans
HC = bpy.data.collections.new("HALL_LOOK"); sc.collection.children.link(HC)
steel = bpy.data.materials["hall_steel"]
# ceiling truss (so looking up isn't a void) and the cables the row lamps hang from
for i, y in enumerate((-1.0, 9.0, 19.0, 29.0, 36.0)):
    box(f"hl_truss{i}", (660.0, y, 6.8), (38.0, 0.28, 0.28), steel, HC)
box("hl_truss_r0", (645.0, 17.0, 6.8), (0.28, 44.0, 0.28), steel, HC)
box("hl_truss_r1", (675.0, 17.0, 6.8), (0.28, 44.0, 0.28), steel, HC)
tube_mats, scr_mats, row_tube, row_glow = [], [], [], []
TUBE, GLOW = E("HL_TUBE", 450), E("HL_GLOW", 14)
for k in range(NROW):
    ay = ROW0 + PITCH * k; dy = ay - 0.36
    # lamp: a linear fixture, housing + emissive diffuser (the light is the diffuser)
    tm, te = emit_mat(f"hl_tube{k}", (1.0, 0.86, 0.68), 3.2); tube_mats.append(te)
    box(f"hl_tube{k}", (660.0, ay + 0.2, 4.8), (29.0, 0.09, 0.05), tm, HC)
    box(f"hl_tubehouse{k}", (660.0, ay + 0.2, 4.86), (29.0, 0.16, 0.06), steel, HC)
    for cx in (648.0, 672.0):
        cyl(f"hl_cable{k}_{int(cx)}", (cx, ay + 0.2, (4.86 + 6.8) / 2), 0.006, 6.8 - 4.86, steel, HC, 6)
    row_tube.append(light(f"L_row{k}", "AREA", (660.0, ay + 0.2, 4.75), (0, 0, 0), (1.0, 0.84, 0.64), TUBE, size=29.0, size_y=0.09, coll=HC))
    # the row's laptop screens (real displays, cool), one mesh per row so a row can switch on
    me = bpy.data.meshes.new(f"hl_scr{k}"); vs, fs = [], []
    for ci in range(20):
        cx = X0 + 1.4 * ci + (1.4 * 2 if False else 0)
        cx = 646.0 + 1.4 * ci if ci < 10 else 661.4 + 1.4 * (ci - 10)
        b = len(vs); vs += [(cx + v.x, dy + v.y, v.z) for v in scr_verts]; fs += [tuple(b + i for i in f) for f in scr_faces]
    me.from_pydata(vs, [], fs); me.update()
    sm, se = emit_mat(f"hl_scrm{k}", (0.55, 0.78, 1.0), 4.0); scr_mats.append(se); me.materials.append(sm)
    so = bpy.data.objects.new(f"hl_scr{k}", me); HC.objects.link(so)
    row_glow.append(light(f"L_scr{k}", "AREA", (660.0, dy - 0.02, 0.58), (-math.pi / 2, 0, 0), (0.55, 0.78, 1.0), GLOW, size=28.0, size_y=0.18, coll=HC, shadow=False))
# wall coves (visible LED strips low on the side walls and the back wall) + floor guide strips along the aisle edges
cove_m, cove_e = emit_mat("hl_cove", (0.62, 0.78, 1.0), 6.0)
box("hl_cove_L", (641.6, 17.0, 0.22), (0.05, 40.0, 0.05), cove_m, HC)
box("hl_cove_R", (678.4, 17.0, 0.22), (0.05, 40.0, 0.05), cove_m, HC)
box("hl_cove_B", (660.0, 37.6, 0.22), (36.0, 0.05, 0.05), cove_m, HC)
COVE = E("HL_COVE", 140)
cove_l = [light("L_cove_L", "AREA", (641.8, 17.0, 0.3), (0, -math.pi / 2, 0), (0.62, 0.78, 1.0), COVE, size=40.0, size_y=0.3, coll=HC, shadow=False),
          light("L_cove_R", "AREA", (678.2, 17.0, 0.3), (0, -math.pi / 2, 0), (0.62, 0.78, 1.0), COVE, size=40.0, size_y=0.3, coll=HC, shadow=False)]
for l in cove_l: l.rotation_euler = (math.pi / 2, 0, 0) if False else l.rotation_euler
guide_m, guide_e = emit_mat("hl_guide", (0.5, 1.0, 0.7), 5.0)
for i, x in enumerate((659.25, 660.75)):
    box(f"hl_guide{i}", (x, 17.0, 0.012), (0.04, 38.0, 0.012), guide_m, HC)
guide_l = light("L_guide", "AREA", (660.0, 17.0, 0.1), (0, 0, 0), (0.5, 1.0, 0.7), E("HL_GUIDE", 40), size=1.6, size_y=38.0, coll=HC, shadow=False)
guide_l.rotation_euler = (math.pi, 0, 0) if False else (0, 0, 0)
guide_l.rotation_euler = (math.pi, 0, 0)       # emits up (+z), a floor-level strip throw
guide_l.location.z = 0.03
# front cans by Claude's desk: floor uplight fixtures (visible lens) that light his face from below-front, key:fill <= 4:1
shade = solid("hl_can", (0.04, 0.04, 0.045), 0.35, 0.8); lensm, lense = emit_mat("hl_lens", (1.0, 0.9, 0.78), 12.0)
FR = E("HL_FRONT", 130)
front = []
for i, x in enumerate((658.4, 661.6)):
    cyl(f"hl_can{i}", (x, -2.0, 0.07), 0.09, 0.14, shade, HC, 24); cyl(f"hl_lens{i}", (x, -2.0, 0.145), 0.065, 0.01, lensm, HC, 24)
    front.append(light(f"L_front{i}", "SPOT", (x, -2.0, 0.16), aim((x, -2.0, 0.16), (660.0, 0.2, 0.9)), (1.0, 0.86, 0.7), FR, size=0.04, coll=HC, spot=math.radians(80), blend=0.8))
# Claude's own desk lamp (warm bulb you can point at) lights him from the front-left
lamp_m, lamp_e = emit_mat("hl_lampbulb", (1.0, 0.72, 0.42), 8.0)
cyl("hl_lamp_stem", (659.55, -1.0, 0.62), 0.008, 0.38, shade, HC, 8); cyl("hl_lamp_head", (659.55, -1.0, 0.82), 0.06, 0.07, lamp_m, HC, 20)
lamp_l = light("L_lamp", "SPOT", (659.55, -1.0, 0.8), aim((659.55, -1.0, 0.8), (660.0, -0.9, 0.95)), (1.0, 0.74, 0.46), E("HL_FACE", 45), size=0.05, coll=HC, spot=math.radians(110), blend=0.9)

# the dash board's own flood was a big green wash on the floor: a smaller, neutral one (the tiles still glow)
for o in bpy.data.objects:
    if o.type == "LIGHT" and o.name in ("db_glow", "DB_glow"):
        o.data.energy *= 0.25; o.data.color = (0.8, 0.9, 1.0); print("[hall] dash flood tamed", o.name)
pbr("hall_floor", "painted_concrete_02", 2.4, tint=(0.30, 0.32, 0.36), rough_gain=0.9, rough_bias=0.2, bump=0.5, coat=0.2, coat_rough=0.3, spec=0.4)
# ------------------------------------------------------------------ 3. the dash (status board): keep v1's, but a real display (no bloom)
for m in bpy.data.materials:
    if m.name.startswith("db_") and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "EMISSION" and n.inputs["Strength"].default_value > 2.0: print("[hall] dash mat", m.name, n.inputs["Strength"].default_value)


# ------------------------------------------------------------------ 3b. a ceiling and a front wall so no view is a black void (keyed per shot: off where a camera is above/outside them)
ceil_m = pbr("hall_ceil", "painted_concrete_02", 2.0, tint=(0.30, 0.31, 0.34), bump=0.5)
ceil = box("hl_ceiling", (660.0, 17.0, 7.1), (38.0, 44.0, 0.1), ceil_m, HC)
fwall = box("hl_frontwall", (660.0, -4.3, 3.5), (38.0, 0.2, 7.0), bpy.data.materials["hall_wall"], HC)
sconce_m, sconce_e = emit_mat("hl_sconce", (1.0, 0.82, 0.6), 6.0)
for i, x in enumerate((653.0, 667.0)):
    box(f"hl_sconce{i}", (x, -4.12, 1.9), (0.22, 0.06, 0.34), sconce_m, HC)
    light(f"L_sconce{i}", "SPOT", (x, -4.0, 1.9), aim((x, -4.0, 1.9), (x, -4.3, 0.2)), (1.0, 0.8, 0.58), 160, size=0.05, coll=HC, spot=math.radians(100), blend=0.9)
    light(f"L_sconceU{i}", "SPOT", (x, -4.0, 2.0), aim((x, -4.0, 2.0), (x, -4.3, 6.5)), (1.0, 0.8, 0.58), 160, size=0.05, coll=HC, spot=math.radians(100), blend=0.9)
CEIL_OFF = {"S136", "S147"}; WALL_ON = {"S120", "S122"}
# ------------------------------------------------------------------ 4. escalation keys (constant at the cut)
def key_socket(sock, frame, value):
    sock.default_value = value; sock.keyframe_insert("default_value", frame=frame)


for shot in SHOTS:
    f, rows, lamp, scr, cove, ledc = STATE[shot]
    for k in range(NROW):
        on = k < rows
        key_socket(tube_mats[k].inputs["Strength"], f, 3.2 * lamp if on else 0.0)
        key_socket(scr_mats[k].inputs["Strength"], f, 4.0 * scr if on else 0.0)
        row_tube[k].data.energy = TUBE * lamp * (1 if on else 0); row_tube[k].data.keyframe_insert("energy", frame=f)
        row_glow[k].data.energy = GLOW * scr * (1 if on else 0); row_glow[k].data.keyframe_insert("energy", frame=f)
    key_socket(cove_e.inputs["Strength"], f, 6.0 * max(cove, 0.05)); key_socket(guide_e.inputs["Strength"], f, 5.0 if cove >= 0.9 else 0.0)
    for l in cove_l: l.data.energy = COVE * cove; l.data.keyframe_insert("energy", frame=f)
    guide_l.data.energy = E("HL_GUIDE", 40) * (1.0 if cove >= 0.9 else 0.0); guide_l.data.keyframe_insert("energy", frame=f)
    ceil.hide_render = shot in CEIL_OFF; ceil.keyframe_insert("hide_render", frame=f)
    fwall.hide_render = shot not in WALL_ON; fwall.keyframe_insert("hide_render", frame=f)
    for o_ in HC.objects:
        if o_.name.startswith(("hl_sconce", "L_sconce")): o_.hide_render = shot not in WALL_ON; o_.keyframe_insert("hide_render", frame=f)
    key_socket(le.inputs["Color"], f, (1.0, 0.45, 0.06, 1) if ledc == "amber" else (0.1, 1.0, 0.25, 1))
for ob in HC.objects:
    pass
for dat in [m.node_tree for m in bpy.data.materials if m.node_tree and m.node_tree.animation_data] + [l for l in bpy.data.lights if l.animation_data]:
    ad = dat.animation_data
    if ad and ad.action:
        for layer in ad.action.layers:
            for st in layer.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

# ------------------------------------------------------------------ 5. the three new cameras (shot-design: reason, move, landing frame)
def new_cam(name, lens, dof=None):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36
    if dof: cd.dof.use_dof = True; cd.dof.aperture_fstop = dof
    co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co); return co


def key_cam(co, f, loc, target):
    co.location = loc; co.rotation_euler = aim(loc, target)
    co.keyframe_insert("location", frame=f); co.keyframe_insert("rotation_euler", frame=f)


def cut_to(frame, cam):
    for m in sc.timeline_markers:
        if m.frame == frame: m.camera = cam; return
    mk = sc.timeline_markers.new("hl_" + cam.name, frame=frame); mk.camera = cam


if "S069" in SHOTS:    # low camera down the aisle: seated agents typing, the near rows lit and the far rows still dark
    c = new_cam("CAM_hl_s069_aisle", 28)
    key_cam(c, 2593, (659.45, -0.3, 0.6), (661.2, 10.0, 0.85)); key_cam(c, 2631, (659.7, 0.7, 0.62), (661.3, 10.0, 0.85)); cut_to(2593, c)
if "S107" in SHOTS:    # eye-level rack focus along one row (row 4): the profile of the first agent, then the row behind it
    c = new_cam("CAM_hl_s107_row", 50, dof=1.6)
    key_cam(c, 4061, (644.7, 7.14, 0.86), (674.0, 7.0, 0.80)); key_cam(c, 4108, (645.3, 7.14, 0.86), (674.0, 7.0, 0.80))
    c.data.dof.focus_distance = 2.7; c.data.dof.keyframe_insert("focus_distance", frame=4061)
    c.data.dof.focus_distance = 8.6; c.data.dof.keyframe_insert("focus_distance", frame=4108); cut_to(4061, c)
if "S129" in SHOTS:    # floor-level push toward the back wall beside Claude's desk
    c = new_cam("CAM_hl_s129_floor", 20)
    key_cam(c, 4757, (660.78, -3.4, 0.16), (660.0, 20.0, 1.9)); key_cam(c, 4812, (660.78, 0.8, 0.2), (660.0, 20.0, 1.9)); cut_to(4757, c)

# ------------------------------------------------------------------ save
def fix_paths():
    for im in bpy.data.images:
        if im.source == "FILE" and im.filepath.startswith("//"):
            for b in (os.path.dirname(OUT), DOCS, os.path.dirname(SRC_S2)):
                c = os.path.normpath(os.path.join(b, im.filepath[2:]))
                if os.path.exists(c): im.filepath = c; break
fix_paths()
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=True)
print("[hall] saved", OUT)
