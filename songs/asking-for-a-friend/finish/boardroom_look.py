"""BOARDROOM look (finish_2): port of the approved look (CD 13: PBR on every surface, real sources only, Filmic lifted toe,
linear render + separate grade) to the boardroom of master v1's aff_03_chorus1.blend. Sets/materials/lights/screen only:
NEVER touches cameras, Claude, timing. Saves a COPY.

  Blender -b <master v1 chorus1.blend> --python boardroom_look.py -- <out.blend>
Tunables via env (so an exposure note is a one-line re-run): BRL_PEND, BRL_SCREEN, BRL_CITY, BRL_SCR_EM, BRL_FILL.
"""
import bpy, os, sys, math, random, mathutils
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender")
PH = os.path.join(DOCS, "textures", "ph")
FONTS = os.environ.get("STUDIO_FONTS", "assets/fonts")   # the studio fonts (repo root assets/fonts)
E = lambda k, d: float(os.environ.get(k, d))
sc = bpy.context.scene
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None


# ------------------------------------------------------------------ helpers
def img(path, nc=False):
    im = bpy.data.images.load(path, check_existing=True)
    if nc: im.colorspace_settings.name = "Non-Color"
    return im


def pbr(name, asset, tile_m, tint=(1, 1, 1), rough_gain=1.0, rough_bias=0.0, metal=0.0, bump=0.3, bump_dist=0.01,
        coat=0.0, coat_rough=0.12, hsv=None, spec=0.5, anisotropic=0.0):
    """Real PBR material (Poly Haven maps) on world-position box projection (no UVs needed, no stretching)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    N = nt.nodes.new; L = nt.links.new
    out = N("ShaderNodeOutputMaterial"); bs = N("ShaderNodeBsdfPrincipled")
    geo = N("ShaderNodeNewGeometry"); mp = N("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile_m,) * 3
    L(geo.outputs["Position"], mp.inputs["Vector"])
    d = os.path.join(PH, asset)

    def tex(kind, nc):
        n = N("ShaderNodeTexImage")
        fn = [f for f in os.listdir(d) if f"_{kind}_" in f][0]
        n.image = img(os.path.join(d, fn), nc); n.projection = "BOX"; n.projection_blend = 0.25
        n.interpolation = "Cubic"
        L(mp.outputs["Vector"], n.inputs["Vector"]); return n
    td, tr, tdisp = tex("diff", False), tex("rough", True), tex("disp", True)
    mix = N("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0; mix.inputs["B"].default_value = (*tint, 1)
    L(td.outputs["Color"], mix.inputs["A"]); last = mix.outputs["Result"]
    if hsv:
        h = N("ShaderNodeHueSaturation"); h.inputs["Saturation"].default_value = hsv[0]; h.inputs["Value"].default_value = hsv[1]
        L(last, h.inputs["Color"]); last = h.outputs["Color"]
    L(last, bs.inputs["Base Color"])
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


def principled(name, color, rough, metal=0.0, **kw):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*color, 1); bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    for k, v in kw.items(): bs.inputs[k.replace("_", " ")].default_value = v
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"]); return m


def emissive_tex(name, path, strength, generated=True):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    N = nt.nodes.new; L = nt.links.new
    out = N("ShaderNodeOutputMaterial"); em = N("ShaderNodeEmission"); t = N("ShaderNodeTexImage")
    tc = N("ShaderNodeTexCoord"); t.image = img(path); t.interpolation = "Cubic"; t.extension = "EXTEND"
    L(tc.outputs["Generated" if generated else "UV"], t.inputs["Vector"])
    L(t.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = strength
    L(em.outputs["Emission"], out.inputs["Surface"]); return m


def box(name, loc, size, mat, coll, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    sx, sy, sz = (s / 2 for s in size)
    vs = [(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(vs, [], fs); me.update()
    ob = bpy.data.objects.new(name, me); ob.location = loc; ob.rotation_euler = rot
    ob.data.materials.append(mat); coll.objects.link(ob); return ob


def cyl(name, loc, r, h, mat, coll, verts=32, r2=None, caps=True):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, segments=verts, radius1=r, radius2=(r if r2 is None else r2), depth=h)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.location = loc; ob.data.materials.append(mat); coll.objects.link(ob); return ob


def light(name, kind, loc, rot, color, energy, size=0.3, size_y=None, coll=None, spot=None, blend=0.6):
    ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, kind)
    ld.type = kind; ld.color = color; ld.energy = energy
    if kind == "AREA":
        ld.size = size
        if size_y: ld.shape = "RECTANGLE"; ld.size_y = size_y
    else:
        ld.shadow_soft_size = size
    if kind == "SPOT": ld.spot_size = spot or math.radians(90); ld.spot_blend = blend
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, ld); (coll or sc.collection).objects.link(ob)
    ob.data = ld; ob.location = loc; ob.rotation_euler = rot; return ob


# ------------------------------------------------------------------ 0. the set's objects
BR = bpy.data.collections["BOARDROOM"]
# the capsule execs go (they become call tiles later): chairs stay, empty
hidden = 0
for ob in list(bpy.data.objects):
    if ob.name.startswith("EX") and ob.name[2:3].isdigit():
        ob.animation_data_clear(); ob.hide_render = True; ob.hide_viewport = True; hidden += 1
print("[brl] execs hidden:", hidden)

# ------------------------------------------------------------------ 1. real PBR on every surface
pbr("br_carpet", "dirty_carpet", 1.1, tint=(0.45, 0.48, 0.55), rough_gain=1.0, rough_bias=0.0, bump=0.9, bump_dist=0.012, spec=0.3)
pbr("br_wall", "plaster_grey_04", 2.2, tint=(0.55, 0.6, 0.7), rough_gain=1.0, bump=0.5, bump_dist=0.01)
pbr("br_wall2", "plaster_grey_04", 2.2, tint=(0.30, 0.34, 0.40), rough_gain=1.0, bump=0.5, bump_dist=0.01)
pbr("srv_ceil", "painted_concrete_02", 2.0, tint=(0.22, 0.23, 0.26), bump=0.4)
pbr("br_doorm", "black_walnut_veneer_01", 0.9, tint=(0.4, 0.3, 0.25), rough_gain=0.8, bump=0.3, coat=0.3, coat_rough=0.3)
pbr("br_table", "black_walnut_veneer_01", 1.3, tint=(0.22, 0.155, 0.13), rough_gain=0.7, rough_bias=0.08, bump=0.25, coat=0.4, coat_rough=0.2, spec=0.5)
pbr("br_tbase", "metal_plate_02", 0.8, tint=(0.35, 0.36, 0.38), metal=0.9, rough_gain=0.8, bump=0.5)
pbr("br_sf", "metal_plate_02", 0.6, tint=(0.09, 0.09, 0.10), metal=0.8, rough_gain=0.7, bump=0.4)
pbr("chair_blk", "fabric_leather_02", 0.5, tint=(0.3, 0.3, 0.34), hsv=(0.1, 1.0), rough_gain=0.9, bump=0.7, bump_dist=0.004, spec=0.45)
pbr("srv_steel", "metal_plate_02", 0.4, tint=(0.55, 0.56, 0.60), metal=1.0, rough_gain=0.7, bump=0.3)
pbr("ped_dark", "metal_plate_02", 0.4, tint=(0.18, 0.19, 0.21), metal=0.9, rough_gain=0.8)
walnut = pbr("br_walnut_slat", "black_walnut_veneer_01", 0.7, tint=(0.8, 0.62, 0.5), rough_gain=0.8, bump=0.3, coat=0.2, coat_rough=0.3)
skirt = pbr("br_skirt", "metal_plate_02", 0.5, tint=(0.14, 0.14, 0.15), metal=0.8, rough_gain=0.8)
brass = pbr("br_brass", "metal_plate_02", 0.4, tint=(0.80, 0.55, 0.28), metal=1.0, rough_gain=0.5)
# the big red button's dome stays "red = failure", glossy plastic (not emissive)
bpy.data.materials["bigred"].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.22
# button label: a printed sticker, not a light (v1 had it glow at 2.5)
lab = bpy.data.materials["bb_label_glow2"]; lab.node_tree.nodes.clear()
o_ = lab.node_tree.nodes.new("ShaderNodeOutputMaterial"); b_ = lab.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
b_.inputs["Base Color"].default_value = (0.86, 0.87, 0.9, 1); b_.inputs["Roughness"].default_value = 0.6
lab.node_tree.links.new(b_.outputs["BSDF"], o_.inputs["Surface"])
bl = bpy.data.objects["br_blabel"]
bl.data.font = bpy.data.fonts.load(os.path.join(FONTS, "Anton-Regular.ttf"))

# ------------------------------------------------------------------ 2. main screen: a real light with company-voice graphics
SCR_PNG = os.path.join(DOCS, "textures", "screens", "br_main_screen.png")
scr = bpy.data.objects["br_screen"]
scr.data.materials.clear(); scr.data.materials.append(emissive_tex("br_scr_L", SCR_PNG, E("BRL_SCR_EM", 1.25)))
for n in [o.name for o in BR.all_objects if o.name.startswith("fc_") or o.name.startswith("fa")]:
    bpy.data.objects[n].hide_render = True; bpy.data.objects[n].hide_viewport = True
# the call tile stays where it is (execs-as-tiles come later); give its name the company face
t = bpy.data.objects["br_tile_name"]; t.data.font = bpy.data.fonts.load(os.path.join(FONTS, "Inter-SemiBold.otf"))

# ------------------------------------------------------------------ 3. window + city, slat wall, skirting, pendants
CITY_PNG = os.path.join(DOCS, "textures", "screens", "br_city_night.png")
city_m = emissive_tex("br_city_L", CITY_PNG, E("BRL_CITY_EM", 5.0))
cy = bpy.data.meshes.new("br_city"); cy.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)]); cy.update()
cob = bpy.data.objects.new("br_city", cy); cob.location = (-124.0, 15.0, 4.0); cob.scale = (22.0, 5.5, 1.0)
cob.rotation_euler = (math.pi / 2, 0, 0); cy.materials.append(city_m); BR.objects.link(cob)

# glass pane material (see-through, faint reflection) + dark mullions
pm = bpy.data.materials.new("br_glass"); pm.use_nodes = True; pnt = pm.node_tree; pnt.nodes.clear()
po = pnt.nodes.new("ShaderNodeOutputMaterial"); pt = pnt.nodes.new("ShaderNodeBsdfTransparent"); pg = pnt.nodes.new("ShaderNodeBsdfGlossy")
pg.inputs["Roughness"].default_value = 0.03; pf = pnt.nodes.new("ShaderNodeFresnel"); pf.inputs["IOR"].default_value = 1.5
px_ = pnt.nodes.new("ShaderNodeMixShader")
px_.inputs["Fac"].default_value = 0.04; pnt.links.new(pt.outputs[0], px_.inputs[1]); pnt.links.new(pg.outputs[0], px_.inputs[2])
pnt.links.new(px_.outputs[0], po.inputs["Surface"])
mull = pbr("br_mullion", "metal_plate_02", 0.4, tint=(0.07, 0.07, 0.08), metal=0.85, rough_gain=0.8)
# back-wall window (left of the screen): x -126 .. -122.5, z 0.45 .. 2.95 ; wall is at y 4.5 (thickness face at 4.5)
WX0, WX1, WZ0, WZ1, WY = -126.0, -122.55, 0.45, 2.95, 4.46
bpy.data.objects["br_back"].hide_render = True; bpy.data.objects["br_back"].hide_viewport = True
wm = bpy.data.materials["br_wall"]
BWY = 4.61
box("br_back_r", ((WX1 + -113.0) / 2, BWY, 1.6), (-113.0 - WX1, 0.2, 3.2), wm, BR)
box("br_back_l", ((-127.0 + WX0) / 2, BWY, 1.6), (WX0 + 127.0, 0.2, 3.2), wm, BR)
box("br_back_lo", ((WX0 + WX1) / 2, BWY, WZ0 / 2), (WX1 - WX0, 0.2, WZ0), wm, BR)
box("br_back_hi", ((WX0 + WX1) / 2, BWY, (WZ1 + 3.2) / 2), (WX1 - WX0, 0.2, 3.2 - WZ1), wm, BR)
box("br_win_glass", ((WX0 + WX1) / 2, 4.5, (WZ0 + WZ1) / 2), (WX1 - WX0, 0.01, WZ1 - WZ0), pm, BR)
for i, x in enumerate((WX0, (WX0 + WX1) / 2 - 0.02, (WX0 + WX1) / 2 + 0.9, WX1)):
    box(f"br_win_mull{i}", (x, 4.45, (WZ0 + WZ1) / 2), (0.07, 0.07, WZ1 - WZ0 + 0.07), mull, BR)
for i, z in enumerate((WZ0, 1.55, WZ1)):
    box(f"br_win_tran{i}", ((WX0 + WX1) / 2, 4.45, z), (WX1 - WX0, 0.07, 0.07), mull, BR)
# left-wall slat panel (walnut slats on a dark backing) y -3.2 .. 4.3, z 0.12 .. 3.1, wall at x -126
for i in range(54):
    y = -3.0 + i * 0.135
    box(f"br_slat{i}", (-125.93, y, 1.62), (0.05, 0.065, 2.95), walnut, BR)
box("br_slat_back", (-125.97, 0.65, 1.62), (0.02, 7.5, 2.98), bpy.data.materials["br_wall2"], BR)
# skirting boards (dark steel) so the room has edges
box("br_skirt_back", (-120.0, 4.47, 0.06), (12.0, 0.04, 0.12), skirt, BR)
box("br_skirt_left", (-125.96, 0.0, 0.06), (0.04, 12.0, 0.12), skirt, BR)
# a ceiling cove: dark steel beams so the ceiling has structure (not a black plane)
for i, y in enumerate((-2.5, 0.6, 3.7)):
    box(f"br_beam{i}", (-120.0, y, 3.12), (13.8, 0.22, 0.16), skirt, BR)

# pendants over the table: brass shade, bulb is the light; cable to the ceiling
bulb_m = bpy.data.materials.new("br_bulb"); bulb_m.use_nodes = True; bnt = bulb_m.node_tree; bnt.nodes.clear()
bo = bnt.nodes.new("ShaderNodeOutputMaterial"); be = bnt.nodes.new("ShaderNodeEmission"); be.inputs["Color"].default_value = (1.0, 0.72, 0.42, 1); be.inputs["Strength"].default_value = 60.0
bnt.links.new(be.outputs[0], bo.inputs["Surface"])
shade_m = principled("br_shade", (0.05, 0.05, 0.055), 0.35, 0.8)
PEND = []
for i, y in enumerate((-1.0, 0.6, 2.2)):
    z = 2.35
    cyl(f"br_pend_cable{i}", (-120.0, y, (z + 3.2) / 2 + 0.1), 0.006, 3.2 - z, shade_m, BR, 8)
    cyl(f"br_pend_shade{i}", (-120.0, y, z), 0.045, 0.2, shade_m, BR, 40, r2=0.17, caps=False)
    cyl(f"br_pend_inner{i}", (-120.0, y, z - 0.005), 0.044, 0.19, brass, BR, 40, r2=0.165, caps=False)
    sp = bpy.data.objects.new(f"br_bulb{i}", bpy.data.meshes.new(f"br_bulb{i}"))
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.035); bm.to_mesh(sp.data); bm.free()
    sp.data.materials.append(bulb_m); sp.location = (-120.0, y, z - 0.07); BR.objects.link(sp)
    PEND.append((y, z))

# ------------------------------------------------------------------ 4. lights: only things you could point at
for n in ("BR_key", "BR_fill"):                                    # v1's invisible key + camera-side fill are gone
    bpy.data.objects[n].hide_render = True
pend = E("BRL_PEND", 130)
for i, (y, z) in enumerate(PEND):
    light(f"L_pend{i}", "SPOT", (-120.0, y, z - 0.13), (0, 0, 0), (1.0, 0.74, 0.46), pend, size=0.05, coll=BR, spot=math.radians(115), blend=0.9)
# a fourth pendant over where Claude stands at the screen (c4/c5), and wall-washer downlights (recessed cans you could point at)
def aim(frm, to):
    return (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
light("L_pend3", "SPOT", (-118.45, 2.0, 2.22), aim((-118.45, 2.0, 2.22), (-118.4, 2.75, 0.78)), (1.0, 0.76, 0.5), E("BRL_CLAUDE", 300), size=0.05, coll=BR, spot=math.radians(70), blend=0.8)
cyl("br_pend_cable3", (-118.45, 2.0, 2.8), 0.006, 0.9, shade_m, BR, 8)
cyl("br_pend_shade3", (-118.45, 2.0, 2.36), 0.045, 0.2, shade_m, BR, 40, r2=0.17, caps=False)
cyl("br_pend_inner3", (-118.45, 2.0, 2.355), 0.044, 0.19, brass, BR, 40, r2=0.165, caps=False)
sp3 = bpy.data.objects.new("br_bulb3", bpy.data.meshes.new("br_bulb3")); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.035); bm.to_mesh(sp3.data); bm.free()
sp3.data.materials.append(bulb_m); sp3.location = (-118.45, 2.0, 2.29); BR.objects.link(sp3)
can_m = bpy.data.materials.new("br_can"); can_m.use_nodes = True; cnt = can_m.node_tree; cnt.nodes.clear()
co = cnt.nodes.new("ShaderNodeOutputMaterial"); ce = cnt.nodes.new("ShaderNodeEmission"); ce.inputs["Color"].default_value = (0.85, 0.92, 1.0, 1); ce.inputs["Strength"].default_value = 40.0
cnt.links.new(ce.outputs[0], co.inputs["Surface"])
WASH = E("BRL_WASH", 300)
for i, x in enumerate((-124.6, -122.4, -117.9, -115.4)):            # back wall (y 4.5), skipping nothing: the screen wall needs a wash either side
    p = (x, 3.55, 3.15)
    light(f"L_wash_b{i}", "SPOT", (p[0], p[1], p[2] - 0.03), aim(p, (x, 4.5, 1.1)), (0.84, 0.9, 1.0), WASH, size=0.04, coll=BR, spot=math.radians(95), blend=1.0)
    cyl(f"br_can_b{i}", (p[0], p[1], p[2] - 0.01), 0.055, 0.04, can_m, BR, 24)
for i, y in enumerate((-2.2, -0.5, 1.4, 3.1)):                      # left slat wall (x -126)
    p = (-124.7, y, 3.15)
    light(f"L_wash_l{i}", "SPOT", (p[0], p[1], p[2] - 0.03), aim(p, (-125.95, y, 1.1)), (0.84, 0.9, 1.0), WASH, size=0.04, coll=BR, spot=math.radians(95), blend=1.0)
    cyl(f"br_can_l{i}", (p[0], p[1], p[2] - 0.01), 0.055, 0.04, can_m, BR, 24)
# ceiling cans over the near aisle so the floor reads (recessed downlights)
for i, x in enumerate((-124.0, -121.0, -118.0, -115.0)):
    p = (x, -2.2, 3.15)
    light(f"L_can_f{i}", "SPOT", (p[0], p[1], p[2] - 0.03), (0, 0, 0), (0.88, 0.92, 1.0), E("BRL_CAN", 140), size=0.04, coll=BR, spot=math.radians(110), blend=1.0)
    cyl(f"br_can_f{i}", (p[0], p[1], p[2] - 0.01), 0.055, 0.04, can_m, BR, 24)
# LED cove strips at the top of the back and left walls (emissive strips you can point at) + their light washing the wall down
cove_m = bpy.data.materials.new("br_cove"); cove_m.use_nodes = True; cnt2 = cove_m.node_tree; cnt2.nodes.clear()
c2o = cnt2.nodes.new("ShaderNodeOutputMaterial"); c2e = cnt2.nodes.new("ShaderNodeEmission"); c2e.inputs["Color"].default_value = (0.8, 0.88, 1.0, 1); c2e.inputs["Strength"].default_value = 8.0
cnt2.links.new(c2e.outputs[0], c2o.inputs["Surface"])
box("br_cove_back", (-120.0, 4.3, 3.1), (13.0, 0.05, 0.02), cove_m, BR)
box("br_cove_left", (-125.7, 0.6, 3.1), (0.05, 11.0, 0.02), cove_m, BR)
COVE = E("BRL_COVE", 90)
light("L_cove_back", "AREA", (-120.0, 4.25, 3.08), aim((-120.0, 4.25, 3.08), (-120.0, 4.5, 1.2)), (0.88, 0.92, 1.0), COVE, size=13.0, size_y=0.2, coll=BR)
light("L_cove_left", "AREA", (-125.65, 0.6, 3.08), aim((-125.65, 0.6, 3.08), (-125.95, 0.6, 1.2)), (0.88, 0.92, 1.0), COVE, size=0.2, size_y=11.0, coll=BR)
light("L_cove_up", "AREA", (-120.0, 4.2, 3.09), (0, 0, 0), (0.88, 0.92, 1.0), E("BRL_COVE_UP", 40), size=13.0, size_y=0.3, coll=BR)
bpy.data.objects["L_cove_up"].rotation_euler = (math.pi, 0, 0)   # emits up (+z) toward the ceiling
# ---- practicals that motivate face light (CD: key:fill <= 4:1, shadow side >= 0.10): a table lamp, the lit button, the laptop screen
lamp_m = bpy.data.materials.new("br_lamp_glass"); lamp_m.use_nodes = True; lnt = lamp_m.node_tree; lnt.nodes.clear()
lo_ = lnt.nodes.new("ShaderNodeOutputMaterial"); le_ = lnt.nodes.new("ShaderNodeEmission"); le_.inputs["Color"].default_value = (1.0, 0.72, 0.42, 1); le_.inputs["Strength"].default_value = 6.0
lnt.links.new(le_.outputs[0], lo_.inputs["Surface"])
cyl("br_lamp_base", (-120.58, 2.1, 0.745), 0.07, 0.04, brass, BR, 32)
cyl("br_lamp_stem", (-120.58, 2.1, 0.82), 0.01, 0.13, brass, BR, 12)
cyl("br_lamp_glass", (-120.58, 2.1, 0.95), 0.055, 0.15, lamp_m, BR, 32, r2=0.045)
light("L_lamp", "POINT", (-120.58, 2.1, 0.96), (0, 0, 0), (1.0, 0.72, 0.42), E("BRL_LAMP", 6), size=0.06, coll=BR)
# the button is an illuminated one (a lamp inside the dome): red = the failure it triggers
bm_ = bpy.data.materials["bigred"]; bsd = next(n for n in bm_.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bsd.inputs["Emission Color"].default_value = (0.9, 0.02, 0.04, 1); bsd.inputs["Emission Strength"].default_value = 1.6
light("L_button", "POINT", (-119.1, 2.5, 1.05), (0, 0, 0), (1.0, 0.08, 0.06), E("BRL_BTN", 6), size=0.05, coll=BR)
# laptop screen: lights up when the lid opens (f1464-1469, same keys as v1's lid)
lp = light("L_laptop", "AREA", (-120.4, 1.86, 0.98), (math.pi / 2, 0, 0), (0.72, 0.82, 1.0), E("BRL_LAPTOP", 9), size=0.3, size_y=0.2, coll=BR)
lp.data.animation_data_clear()
for f, v in ((1382, 0.0), (1464, 0.0), (1469, 1.0)):
    lp.data.energy = E("BRL_LAPTOP", 9) * v; lp.data.keyframe_insert("energy", frame=f)
# floor uplight can by the screen wall (a real fixture: lens glows, throws up/in): lights the underside of Claude at the screen
fu_m = bpy.data.materials.new("br_uplens"); fu_m.use_nodes = True; fnt = fu_m.node_tree; fnt.nodes.clear()
fo_ = fnt.nodes.new("ShaderNodeOutputMaterial"); fe_ = fnt.nodes.new("ShaderNodeEmission"); fe_.inputs["Color"].default_value = (0.95, 0.9, 0.85, 1); fe_.inputs["Strength"].default_value = 10.0
fnt.links.new(fe_.outputs[0], fo_.inputs["Surface"])
for i, (x, y) in enumerate(((-117.45, 3.55), (-121.9, 3.6))):
    cyl(f"br_upcan{i}", (x, y, 0.07), 0.09, 0.14, shade_m, BR, 32)
    cyl(f"br_uplens{i}", (x, y, 0.145), 0.065, 0.01, fu_m, BR, 32)
    light(f"L_upcan{i}", "SPOT", (x, y, 0.16), aim((x, y, 0.16), ((-118.4, 2.75, 0.85) if i == 0 else (-120.95, 2.75, 0.85))), (0.95, 0.9, 0.85), E("BRL_UPCAN", 110), size=0.04, coll=BR, spot=math.radians(70), blend=0.8)
# c5 (the stare, f1495-1531): one soft cool window-light key off camera-left, on for that shot only (shot-by-shot lighting; off-frame, motivated by the city window)
k5 = light("L_c5_key", "AREA", (-119.5, 0.8, 1.55), aim((-119.5, 0.8, 1.55), (-118.38, 2.75, 0.95)), (0.84, 0.9, 1.0), E("BRL_C5", 26), size=0.9, size_y=0.6, coll=BR)
k5.data.animation_data_clear()
for f, v in ((1382, 0.0), (1494, 0.0), (1495, 1.0), (1531, 1.0), (1532, 0.0)):
    k5.data.energy = E("BRL_C5", 26) * v; k5.data.keyframe_insert("energy", frame=f)
for fc in (k5.data.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if k5.data.animation_data and k5.data.animation_data.action else []):
    for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
# the main screen throws cool light on the table, the room and Claude (it is a 2.45 x 1.38 m panel)
light("L_screen", "AREA", (-120.0, 3.08, 1.65), (-math.pi / 2, 0, 0), (0.66, 0.78, 1.0), E("BRL_SCREEN", 8), size=2.45, size_y=1.38, coll=BR)
light("L_screen_lo", "AREA", (-120.0, 3.05, 1.0), (-math.pi / 2.6, 0, 0), (0.66, 0.78, 1.0), E("BRL_SCREEN", 8) * 0.4, size=2.2, size_y=0.6, coll=BR)
# city light through the back-left window and the opening on the left (cool, from outside)
light("L_city_back", "AREA", (-124.2, 4.2, 1.7), (-math.pi / 2, 0, 0), (0.55, 0.68, 1.0), E("BRL_CITY", 14), size=3.4, size_y=2.4, coll=BR)
# the corridor beyond the door: a warm sliver of light under the door edge (a real practical)
light("L_door", "AREA", (-116.4, 4.2, 0.9), (-math.pi / 2, 0, 0), (1.0, 0.68, 0.42), E("BRL_DOOR", 4), size=0.9, size_y=1.6, coll=BR)
# a low warm bounce off the table/walnut to keep darks readable would be a fill: none. Detail comes from the lights above.
if E("BRL_FILL", 0) > 0:
    light("L_floor_bounce", "AREA", (-120, -0.5, 0.05), (0, 0, 0), (0.75, 0.8, 0.95), E("BRL_FILL", 0), size=6, size_y=4, coll=BR)

# ------------------------------------------------------------------ 5. colour management: Filmic, linear in, grade later
sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium Contrast"
sc.display_settings.display_device = "sRGB"
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.0015, 0.0018, 0.003, 1)
sc.eevee.use_raytracing = True
try:
    sc.eevee.ray_tracing_options.resolution_scale = "1"
except Exception as ex: print("[brl] rt opts", ex)
for k, v in (("use_shadows", True),):
    setattr(sc.eevee, k, v)

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=True); print("[brl] saved", OUT)
