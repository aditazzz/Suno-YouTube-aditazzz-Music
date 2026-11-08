"""ops_fix round: dress the billing office (warm, props, signs, parcels, paper stacks, the customer's sleeve).
  Blender -b ops_look_verse1.blend|ops_look_bridge.blend --python ops_fix_billing.py -- <out.blend>
Copies only: the source blend is never saved. Tunables (env): WARM_K light gain on the added lights."""
import bpy, os, sys, math, random, bmesh
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
E = lambda k, d: float(os.environ.get(k, d))
sc = bpy.context.scene; M = bpy.data.materials
DOCS = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender")
FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ops_fix")   # textures from ops_fix_tex.py
bl = bpy.data.collections["BILLING"]
random.seed(7)


def tint_copy(src, new, rgb, rough=None):
    if new in M: return M[new]
    m = M[src].copy(); m.name = new; nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    l = bs.inputs["Base Color"].links[0] if bs.inputs["Base Color"].links else None
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
    mx.inputs["Factor"].default_value = 1.0; mx.inputs["B"].default_value = (*rgb, 1)
    if l: nt.links.new(l.from_socket, mx.inputs["A"])
    else: mx.inputs["A"].default_value = bs.inputs["Base Color"].default_value
    nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
    if rough is not None: bs.inputs["Roughness"].default_value = rough
    return m


def box(name, loc, dim, mat, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.scale = dim; o.rotation_euler = rot
    o.data.materials.append(M[mat] if isinstance(mat, str) else mat); bl.objects.link(o)
    return o


# ---------- materials
tint_copy("AFF_paper", "ops_kraft", (0.62, 0.42, 0.22), rough=0.8)
tint_copy("AFF_srv_wall", "ops_wall_warm", (1.0, 0.80, 0.58), rough=0.85)
tint_copy("AFF_srv_concrete_dusty", "ops_floor_warm", (0.95, 0.74, 0.56))
tint_copy("AFF_desk_laminate", "ops_shelf_wood", (0.75, 0.52, 0.34))
tint_copy("AFF_filing_cabinet", "ops_cab_green", (0.45, 0.62, 0.52))
tint_copy("AFF_rack_painted_steel", "ops_shelf_steel", (0.55, 0.62, 0.6))
tint_copy("AFF_desk_laminate", "ops_sign_board", (0.26, 0.42, 0.40))
if "ops_tube_warm" not in M:
    t = M["AFF_aisle_tube_cold"].copy(); t.name = "ops_tube_warm"
    for n in t.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            for k in ("Emission Color", "Base Color"):
                if k in n.inputs: n.inputs[k].default_value = (1.0, 0.78, 0.5, 1)


def kraft_parcel():
    """kraft box, tape band (|x-.5|<.07) and a paper label on front/back faces (object-coordinate masks)."""
    if "ops_parcel" in M: return M["ops_parcel"]
    m = M["ops_kraft"].copy(); m.name = "ops_parcel"; nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    base = bs.inputs["Base Color"].links[0].from_socket if bs.inputs["Base Color"].links else None
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nrm = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Normal"], nrm.inputs[0])
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.5; nt.links.new(sep.outputs["X"], sub.inputs[0])
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; nt.links.new(sub.outputs[0], ab.inputs[0])
    tp = nt.nodes.new("ShaderNodeMath"); tp.operation = "LESS_THAN"; tp.inputs[1].default_value = 0.07; nt.links.new(ab.outputs[0], tp.inputs[0])
    ny = nt.nodes.new("ShaderNodeMath"); ny.operation = "ABSOLUTE"; nt.links.new(nrm.outputs["Y"], ny.inputs[0])
    nyg = nt.nodes.new("ShaderNodeMath"); nyg.operation = "GREATER_THAN"; nyg.inputs[1].default_value = 0.5; nt.links.new(ny.outputs[0], nyg.inputs[0])

    def rng(src, lo, hi):
        a = nt.nodes.new("ShaderNodeMath"); a.operation = "GREATER_THAN"; a.inputs[1].default_value = lo; nt.links.new(src, a.inputs[0])
        b = nt.nodes.new("ShaderNodeMath"); b.operation = "LESS_THAN"; b.inputs[1].default_value = hi; nt.links.new(src, b.inputs[0])
        c = nt.nodes.new("ShaderNodeMath"); c.operation = "MULTIPLY"; nt.links.new(a.outputs[0], c.inputs[0]); nt.links.new(b.outputs[0], c.inputs[1]); return c.outputs[0]
    lx = rng(sep.outputs["X"], 0.12, 0.52); lz = rng(sep.outputs["Z"], 0.45, 0.85)
    l1 = nt.nodes.new("ShaderNodeMath"); l1.operation = "MULTIPLY"; nt.links.new(lx, l1.inputs[0]); nt.links.new(lz, l1.inputs[1])
    l2 = nt.nodes.new("ShaderNodeMath"); l2.operation = "MULTIPLY"; nt.links.new(l1.outputs[0], l2.inputs[0]); nt.links.new(nyg.outputs[0], l2.inputs[1])
    m1 = nt.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.inputs["B"].default_value = (0.78, 0.66, 0.42, 1); nt.links.new(tp.outputs[0], m1.inputs["Factor"])
    if base: nt.links.new(base, m1.inputs["A"])
    else: m1.inputs["A"].default_value = (0.5, 0.33, 0.18, 1)
    m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.inputs["B"].default_value = (0.93, 0.9, 0.82, 1); nt.links.new(l2.outputs[0], m2.inputs["Factor"])
    nt.links.new(m1.outputs["Result"], m2.inputs["A"]); nt.links.new(m2.outputs["Result"], bs.inputs["Base Color"])
    return m


def stack_mat():
    """page stack: invoice sheet (printed text, red PAID stamp) on the top face, page edges on the sides."""
    if "ops_stack" in M: return M["ops_stack"]
    m = M["ops_paper"].copy(); m.name = "ops_stack"; nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord"); nrm = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Normal"], nrm.inputs[0])
    top = nt.nodes.new("ShaderNodeMath"); top.operation = "GREATER_THAN"; top.inputs[1].default_value = 0.7; nt.links.new(nrm.outputs["Z"], top.inputs[0])
    inv = nt.nodes.new("ShaderNodeTexImage"); inv.image = bpy.data.images.load(FIX + "/invoice_sheet.png", check_existing=True); inv.extension = "EXTEND"
    nt.links.new(tc.outputs["Generated"], inv.inputs["Vector"])
    eg = nt.nodes.new("ShaderNodeTexImage"); eg.image = bpy.data.images.load(FIX + "/page_edges.png", check_existing=True); eg.extension = "REPEAT"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    cmb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(sep.outputs["X"], cmb.inputs["X"]); nt.links.new(sep.outputs["Z"], cmb.inputs["Y"])
    nt.links.new(cmb.outputs[0], eg.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; nt.links.new(top.outputs[0], mx.inputs["Factor"])
    nt.links.new(eg.outputs["Color"], mx.inputs["A"]); nt.links.new(inv.outputs["Color"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
    return m


kraft_parcel(); stack_mat()
for o in bpy.data.objects:
    if o.type != "MESH": continue
    for s in o.material_slots:
        if not s.material: continue
        n = s.material.name
        if n == "ops_paper_pile":
            s.material = M["ops_parcel"] if o.name.startswith(("bl_tower", "bl_mech")) else M["ops_stack"]
        elif n == "ops_paper" and o.name.startswith("bl_") and o.name != "bl_invoice_src":
            s.material = M["ops_parcel"] if o.dimensions.z > 0.09 else M["ops_stack"]
        elif n == "AFF_srv_wall" and o.name.startswith("bl_"): s.material = M["ops_wall_warm"]
        elif n == "AFF_srv_concrete_dusty" and o.name == "bl_floor": s.material = M["ops_floor_warm"]
# the customer's suit/sleeve: fabric texture, not a flat tube
if "ops_sleeve" not in M:
    sm = M["v1_Cust_Suit"].copy(); sm.name = "ops_sleeve"; nt = sm.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    img = nt.nodes.new("ShaderNodeTexImage"); img.image = bpy.data.images.load(os.path.join(DOCS, "textures/ph/fabric_leather_02/fabric_leather_02_diff_2k.jpg"), check_existing=True)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (6, 6, 6)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], img.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0; mx.inputs["B"].default_value = (0.42, 0.45, 0.6, 1)
    nt.links.new(img.outputs["Color"], mx.inputs["A"]); nt.links.new(mx.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.8
for o in bpy.data.objects:
    if o.name in ("cust_armlimb", "cust_body"):
        for s in o.material_slots: s.material = M["ops_sleeve"]

# ---------- room: end walls, shelving, filing cabinets, paper stacks, parcels, signs
box("fx_leftwall", (-43.6, 2.0, 1.7), (0.2, 14, 3.4), "ops_wall_warm")
box("fx_frontwall", (-34.0, -4.6, 1.7), (20, 0.2, 3.4), "ops_wall_warm")
pm = M["ops_parcel"]
for bay in range(3):
    x0 = -42.2 + bay * 2.6
    for u in (0.0, 2.5):
        box(f"fx_up_{bay}_{u}", (x0 + u - 1.25, 2.85, 1.2), (0.05, 0.42, 2.4), "ops_shelf_steel")
    for lv in range(5):
        z = 0.12 + lv * 0.52
        box(f"fx_bd_{bay}_{lv}", (x0, 2.85, z), (2.55, 0.42, 0.03), "ops_shelf_wood")
        xx = x0 - 1.15
        while xx < x0 + 1.2:
            w = random.choice((0.14, 0.18, 0.22)); h = random.choice((0.32, 0.36, 0.40))
            box(f"fx_bx_{bay}_{lv}_{xx:.2f}", (xx + w / 2, 2.8, z + 0.015 + h / 2), (w * 0.95, 0.34, h), pm)
            xx += w + 0.02
for i in range(5):
    y = -2.0 + i * 0.72
    box(f"fx_cab_{i}", (-43.2, y, 0.65), (0.6, 0.66, 1.3), "ops_cab_green")
    for k in range(3):
        box(f"fx_cabd_{i}_{k}", (-42.89, y, 0.25 + k * 0.42), (0.02, 0.56, 0.015), "AFF_steel_dark_anodised")
        box(f"fx_cabh_{i}_{k}", (-42.88, y, 0.34 + k * 0.42), (0.025, 0.14, 0.03), "AFF_steel_dark_anodised")
    if i in (1, 3):
        box(f"fx_cabs_{i}", (-43.2, y, 1.36), (0.34, 0.26, 0.12), "ops_stack")
box("fx_tbl", (-36.5, 2.2, 0.38), (1.6, 0.7, 0.04), "ops_shelf_wood")
for lx_ in (-1, 1):
    for ly_ in (-1, 1):
        box(f"fx_tl_{lx_}{ly_}", (-36.5 + lx_ * 0.72, 2.2 + ly_ * 0.28, 0.18), (0.04, 0.04, 0.36), "ops_shelf_steel")
for i in range(5):
    box(f"fx_ts_{i}", (-37.1 + i * 0.33, 2.2 + random.uniform(-0.15, 0.15), 0.40 + 0.04 * (1 + i % 3)), (0.2, 0.14, 0.08 * (1 + i % 3)), "ops_stack", rot=(0, 0, random.uniform(-0.15, 0.15)))
for i, (px, py, s) in enumerate(((-37.6, 2.5, 0.5), (-36.9, 2.5, 0.38), (-35.7, 2.4, 0.46), (-41.0, 2.4, 0.42), (-41.7, 1.9, 0.34), (-38.8, 2.5, 0.4))):
    box(f"fx_par_{i}", (px, py, s / 2), (s, s * 0.8, s), pm, rot=(0, 0, random.uniform(-0.3, 0.3)))
box("fx_sign_board", (-40.0, 3.08, 2.75), (2.6, 0.06, 0.62), "ops_sign_board")


def text(name, s, loc, size, rot, mat):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = s; cu.size = size; cu.align_x = "CENTER"; cu.extrude = 0.004
    o = bpy.data.objects.new(name, cu); o.location = loc; o.rotation_euler = rot; cu.materials.append(M[mat]); bl.objects.link(o); return o


text("fx_sign_t1", "BILLING", (-40.0, 3.04, 2.72), 0.34, (math.pi / 2, 0, 0), "ops_paper")
text("fx_sign_t2", "ALL INVOICES FINAL", (-40.0, 3.04, 2.55), 0.11, (math.pi / 2, 0, 0), "ops_paper")
box("fx_sign_b2", (-43.46, 0.4, 2.05), (0.06, 2.0, 0.5), "ops_sign_board")
text("fx_sign_t3", "PAID. STAMPED. FILED.", (-43.42, 0.4, 1.96), 0.14, (math.pi / 2, 0, -math.pi / 2), "ops_paper")

# ---------- light: warm, every source visible (hood + frosted tube)
for o in bpy.data.objects:
    if o.type == "LIGHT" and o.name.startswith("BL_room"): o.data.color = (1.0, 0.74, 0.46)
K = E("WARM_K", 1.0)


def fixture(name, loc, length, energy, rot=(0, 0, 0)):
    ld = bpy.data.lights.new(name, "AREA"); ld.shape = "RECTANGLE"; ld.size = length; ld.size_y = 0.2; ld.color = (1.0, 0.76, 0.5); ld.energy = energy * K
    lo = bpy.data.objects.new(name, ld); lo.location = loc; lo.rotation_euler = rot; bl.objects.link(lo)
    box(name + "_tube", (loc[0], loc[1], loc[2] - 0.03), (length * 0.9, 0.12, 0.04), "ops_tube_warm", rot=rot)
    box(name + "_hood", (loc[0], loc[1], loc[2] + 0.03), (length, 0.3, 0.05), "AFF_steel_dark_anodised", rot=rot)


fixture("BLX_shelf0", (-41.0, 2.45, 2.95), 2.6, 110)
fixture("BLX_shelf1", (-38.4, 2.45, 2.95), 2.6, 110)
fixture("BLX_left", (-42.2, 0.2, 3.0), 2.6, 130, rot=(0, 0, math.pi / 2))
fixture("BLX_desk", (-40.0, -0.9, 2.8), 2.0, 80)
GAIN = E("GAIN", 1.0)
for o in bpy.data.objects:
    if o.type == "LIGHT" and not o.name.startswith("L_face") and not (o.data.animation_data and o.data.animation_data.action):
        if o.data.animation_data and o.data.animation_data.drivers: continue
        o.data.energy *= GAIN
if sc.world and sc.world.node_tree:
    for n in sc.world.node_tree.nodes:
        if n.type == "BACKGROUND": n.inputs["Strength"].default_value *= GAIN
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=True)
print("[opsfix] saved", OUT)
