"""BOARDROOM2 look: ports the approved boardroom look (boardroom_look.py) to the aff_08_final / aff_12 BOARDROOM2 set
(7 x 10 m room along y, x=780: door wall y=0, portrait wall y=8.1, table x780 y1.3-6.7). Sets/materials/lights only; never
touches cameras, Claude, timing. Saves a COPY.
  Blender -b <master.blend> --python boardroom2_look.py -- <out.blend>
"""
import bpy, os, sys, math
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "boardroom_look.py")).read()
exec(compile(src[:src.index("# ------------------------------------------------------------------ 0. the set's objects")], "boardroom_look_helpers", "exec"))
import bmesh
from mathutils import Vector
BR = bpy.data.collections["BOARDROOM2"]
CX = 780.0

def aim(frm, to): return (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
def emis(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs["Surface"]); return m

# --- 1. PBR on every surface (same recipes as the approved look; names are the set's own so every object picks them up)
pbr("br_floorm", "dirty_carpet", 1.1, tint=(0.45, 0.48, 0.55), bump=0.9, bump_dist=0.012, spec=0.3)
pbr("br_wall", "plaster_grey_04", 2.2, tint=(0.55, 0.6, 0.7), bump=0.5, bump_dist=0.01)
wall2 = pbr("br_wall2", "plaster_grey_04", 2.2, tint=(0.30, 0.34, 0.40), bump=0.5, bump_dist=0.01)
pbr("br_wood", "black_walnut_veneer_01", 1.3, tint=(0.22, 0.155, 0.13), rough_gain=0.7, rough_bias=0.08, bump=0.25, coat=0.4, coat_rough=0.2)
pbr("br_leather", "fabric_leather_02", 0.5, tint=(0.3, 0.3, 0.34), hsv=(0.1, 1.0), rough_gain=0.9, bump=0.7, bump_dist=0.004, spec=0.45)
pbr("srv_steel", "metal_plate_02", 0.4, tint=(0.55, 0.56, 0.60), metal=1.0, rough_gain=0.7, bump=0.3)
brass = pbr("br_brass", "metal_plate_02", 0.4, tint=(0.80, 0.55, 0.28), metal=1.0, rough_gain=0.5)
skirt = pbr("br_skirt", "metal_plate_02", 0.5, tint=(0.14, 0.14, 0.15), metal=0.8, rough_gain=0.8)
pbr("srv_ceil", "painted_concrete_02", 2.0, tint=(0.22, 0.23, 0.26), bump=0.4)
pbr("gold", "metal_plate_02", 0.4, tint=(0.80, 0.55, 0.28), metal=1.0, rough_gain=0.5)
mull = pbr("br_mullion", "metal_plate_02", 0.4, tint=(0.07, 0.07, 0.08), metal=0.85, rough_gain=0.8)
shade_m = principled("br_shade", (0.05, 0.05, 0.055), 0.35, 0.8)
# sconce lamps: real fixtures (emissive glass) but tamed
bpy.data.materials["br_lamp_e"].node_tree.nodes.clear()
lm = bpy.data.materials["br_lamp_e"]; o_ = lm.node_tree.nodes.new("ShaderNodeOutputMaterial"); e_ = lm.node_tree.nodes.new("ShaderNodeEmission")
e_.inputs["Color"].default_value = (1.0, 0.72, 0.42, 1); e_.inputs["Strength"].default_value = 5.0
lm.node_tree.links.new(e_.outputs[0], o_.inputs["Surface"])
# corridor beyond the door: warm, dimmer
hm = bpy.data.materials["br_hall_e"]
for n in hm.node_tree.nodes:
    if n.type == "EMISSION": n.inputs["Strength"].default_value = 0.35

# portraits: the master points at the old v1 folder (missing = magenta); repoint to this project's textures
for im in bpy.data.images:
    if im.name.startswith("portrait_"):
        q = os.path.join(DOCS, "textures", im.name)
        if os.path.exists(q): im.filepath = q; im.reload()
# --- 2. invisible v1 lights go; ceiling + window + skirting + beams give the room structure
for n in ("br_key", "br_fill", "br_por"):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render = True
box("br_ceiling", (CX, 4.0, 3.65), (7.0, 10.4, 0.1), bpy.data.materials["srv_ceil"], BR)
for i, y in enumerate((1.0, 4.0, 7.0)):
    box(f"br_beam{i}", (CX, y, 3.52), (6.8, 0.22, 0.16), skirt, BR)
box("br_skirt_back", (CX, 7.98, 0.06), (6.8, 0.04, 0.12), skirt, BR)
box("br_skirt_l", (776.62, 4.0, 0.06), (0.04, 10.0, 0.12), skirt, BR)
box("br_skirt_r", (783.38, 4.0, 0.06), (0.04, 10.0, 0.12), skirt, BR)
# window in the left (x 776.5) wall, y 2.6..5.4, z 0.5..2.9; city plane outside
CITY = os.path.join(DOCS, "textures", "screens", "br_city_night.png")
city_m = emissive_tex("br_city_L", CITY, 5.0)
cy = bpy.data.meshes.new("br_city"); cy.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)]); cy.update()
cob = bpy.data.objects.new("br_city", cy); cob.location = (762.0, 4.0, 4.0); cob.scale = (22.0, 5.5, 1.0)
cob.rotation_euler = (math.pi / 2, 0, math.pi / 2); cy.materials.append(city_m); BR.objects.link(cob)
pm = bpy.data.materials.new("br_glass"); pm.use_nodes = True; pnt = pm.node_tree; pnt.nodes.clear()
po = pnt.nodes.new("ShaderNodeOutputMaterial"); pt = pnt.nodes.new("ShaderNodeBsdfTransparent"); pg = pnt.nodes.new("ShaderNodeBsdfGlossy")
pg.inputs["Roughness"].default_value = 0.03; px_ = pnt.nodes.new("ShaderNodeMixShader"); px_.inputs["Fac"].default_value = 0.04
pnt.links.new(pt.outputs[0], px_.inputs[1]); pnt.links.new(pg.outputs[0], px_.inputs[2]); pnt.links.new(px_.outputs[0], po.inputs["Surface"])
WY0, WY1, WZ0, WZ1, WX = 2.6, 5.4, 0.5, 2.9, 776.5
if "br_side-1" in bpy.data.objects:
    bpy.data.objects["br_side-1"].hide_render = True; bpy.data.objects["br_side-1"].hide_viewport = True
wm = bpy.data.materials["br_wall"]
box("br_sw_a", (WX, (-1.0 + WY0) / 2, 1.8), (0.2, WY0 + 1.0, 3.6), wm, BR)
box("br_sw_b", (WX, (WY1 + 9.0) / 2, 1.8), (0.2, 9.0 - WY1, 3.6), wm, BR)
box("br_sw_lo", (WX, (WY0 + WY1) / 2, WZ0 / 2), (0.2, WY1 - WY0, WZ0), wm, BR)
box("br_sw_hi", (WX, (WY0 + WY1) / 2, (WZ1 + 3.6) / 2), (0.2, WY1 - WY0, 3.6 - WZ1), wm, BR)
box("br_sw_glass", (WX + 0.05, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2), (0.01, WY1 - WY0, WZ1 - WZ0), pm, BR)
for i, y in enumerate((WY0, (WY0 + WY1) / 2, WY1)):
    box(f"br_sw_mull{i}", (WX + 0.08, y, (WZ0 + WZ1) / 2), (0.07, 0.07, WZ1 - WZ0 + 0.07), mull, BR)
for i, z in enumerate((WZ0, 1.7, WZ1)):
    box(f"br_sw_tran{i}", (WX + 0.08, (WY0 + WY1) / 2, z), (0.07, WY1 - WY0 + 0.07, 0.07), mull, BR)

# --- 3. pendants over the table (brass shade, the bulb is the light)
bulb_m = emis("br_bulb", (1.0, 0.72, 0.42), 60.0)
PEND = float(os.environ.get("BRL_PEND", 260))
for i, y in enumerate((1.4, 3.0, 4.6)):
    z = 2.75
    cyl(f"br_pend_cable{i}", (CX, y, (z + 3.6) / 2 + 0.1), 0.006, 3.6 - z, shade_m, BR, 8)
    cyl(f"br_pend_shade{i}", (CX, y, z), 0.045, 0.2, shade_m, BR, 40, r2=0.17, caps=False)
    cyl(f"br_pend_inner{i}", (CX, y, z - 0.005), 0.044, 0.19, brass, BR, 40, r2=0.165, caps=False)
    sp = bpy.data.objects.new(f"br_bulb{i}", bpy.data.meshes.new(f"br_bulb{i}"))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.035); bm.to_mesh(sp.data); bm.free()
    sp.data.materials.append(bulb_m); sp.location = (CX, y, z - 0.07); BR.objects.link(sp)
    light(f"L_pend{i}", "SPOT", (CX, y, z - 0.13), (0, 0, 0), (1.0, 0.74, 0.46), PEND, size=0.05, coll=BR, spot=math.radians(115), blend=0.9)

# --- 4. other real sources: sconces, picture lights over the portraits, wall washers, city, corridor, bounce-free
for n, x in (("br_lamp0", 777.4), ("br_lamp1", 782.6)):
    light(f"L_{n}", "POINT", (x, 7.65, 1.2), (0, 0, 0), (1.0, 0.72, 0.42), float(os.environ.get("BRL_LAMP", 18)), size=0.08, coll=BR)
for i, (nm, z) in enumerate((("fp", 2.2),)):
    light("L_pic_f", "SPOT", (CX, 7.35, 3.45), aim((CX, 7.35, 3.45), (CX, 7.89, z)), (1.0, 0.82, 0.6), float(os.environ.get("BRL_PIC", 420)), size=0.05, coll=BR, spot=math.radians(60), blend=0.8)
can_m = emis("br_can", (0.85, 0.92, 1.0), 40.0)
WASH = float(os.environ.get("BRL_WASH", 500))
for i, x in enumerate((777.6, 782.4)):
    p = (x, 7.1, 3.5)
    light(f"L_wash_b{i}", "SPOT", (p[0], p[1], p[2] - 0.03), aim(p, (x, 8.0, 1.2)), (0.84, 0.9, 1.0), WASH, size=0.04, coll=BR, spot=math.radians(95), blend=1.0)
    cyl(f"br_can_b{i}", (p[0], p[1], p[2] - 0.01), 0.055, 0.04, can_m, BR, 24)
for i, y in enumerate((1.0, 3.0, 5.0, 7.0)):
    p = (783.0, y, 3.5)
    light(f"L_wash_r{i}", "SPOT", (p[0], p[1], p[2] - 0.03), aim(p, (783.45, y, 1.2)), (0.84, 0.9, 1.0), WASH * 0.7, size=0.04, coll=BR, spot=math.radians(95), blend=1.0)
    cyl(f"br_can_r{i}", (p[0], p[1], p[2] - 0.01), 0.055, 0.04, can_m, BR, 24)
light("L_city_side", "AREA", (775.8, 4.0, 1.7), (0, math.pi / 2, 0), (0.55, 0.68, 1.0), float(os.environ.get("BRL_CITY", 14)), size=2.8, size_y=2.4, coll=BR)
light("L_door", "AREA", (CX, -0.4, 1.1), (-math.pi / 2, 0, 0), (1.0, 0.68, 0.42), float(os.environ.get("BRL_DOOR", 4)), size=1.6, size_y=2.0, coll=BR)
# recessed can over the head chair (where Claude sits under the portrait): a real fixture, aimed at the chair
light("L_chair_can", "SPOT", (CX, 6.5, 3.55), aim((CX, 6.5, 3.55), (CX, 7.05, 0.95)), (1.0, 0.84, 0.66), float(os.environ.get("BRL_CHAIR", 600)), size=0.05, coll=BR, spot=math.radians(55), blend=0.7)
cyl("br_can_chair", (CX, 6.5, 3.58), 0.06, 0.04, can_m, BR, 24)
# a soft cool fill from the door end so the portrait wall's table end reads
light("L_cool_door", "AREA", (CX, 0.4, 2.8), aim((CX, 0.4, 2.8), (CX, 4.0, 0.7)), (0.66, 0.78, 1.0), float(os.environ.get("BRL_COOL", 60)), size=2.0, size_y=1.2, coll=BR)

# --- 5. colour management as the approved look (Filmic, linear render + separate grade)
sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium Contrast"; sc.display_settings.display_device = "sRGB"
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.0015, 0.0018, 0.003, 1)
sc.eevee.use_raytracing = True
try: sc.eevee.ray_tracing_options.resolution_scale = "1"
except Exception as ex: print("[b2l] rt opts", ex)
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=True); print("[b2l] saved", OUT)
