"""Builds the GT3 RS look copies. Run on a COPY (never a source):
  Blender -b <copy.blend> --python build_car.py -- <v1|post1|outro>
Edits in place and saves the copy. Source blends are never opened for writing.
 v1    S023-S024 (verse 1 road)        post1 S045-S048 (post-chorus 1)      outro  S139-S141 (outro drive)
Common: Filmic MHC (film look), YELLOW calipers (her Nov 4 call), the founder's driver model hidden, other sets hidden,
        badge/brand check. v1+post1: the flat driveway/cyc set is replaced by a golden-hour road. outro: keeps the Austin
        house at dusk, fixes the dark stretch."""
import bpy, sys, math, random
from mathutils import Vector, Euler
import bmesh

MODE = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
LOG = []
def log(*a):
    print("[build]", *a, flush=True); LOG.append(" ".join(str(x) for x in a))

# ---------------------------------------------------------------- colour management: the film's Filmic MHC
vs = sc.view_settings
vs.view_transform = "Filmic"; vs.look = "Medium High Contrast"; vs.exposure = 0.0; vs.gamma = 1.0
log("view", vs.view_transform, vs.look)

# ---------------------------------------------------------------- calipers: PCCB yellow, slightly satin
def srgb2lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
YEL = tuple(srgb2lin(x / 255.0) for x in (0xF2, 0xC2, 0x00)) + (1.0)  if False else (srgb2lin(0xF2/255), srgb2lin(0xC2/255), srgb2lin(0x00/255), 1.0)
cm = bpy.data.materials["Caliper1Mtl"]
b = next(n for n in cm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
before = tuple(round(v, 3) for v in b.inputs["Base Color"].default_value)
b.inputs["Base Color"].default_value = YEL
b.inputs["Roughness"].default_value = 0.34
try: b.inputs["Metallic"].default_value = 0.0
except Exception: pass
log("caliper before", before, "after", tuple(round(v, 3) for v in YEL), "(sRGB #F2C200)")
# any other caliper-looking material or object
for m in bpy.data.materials:
    if "cal" in m.name.lower() and m.name != "Caliper1Mtl": log("OTHER caliper-like material:", m.name)

# ---------------------------------------------------------------- the founder is never in 3D: hide the driver model and the founder set
hid = 0
for o in bpy.data.objects:
    if o.name.startswith("drv_") and o.name != "drv_cabin":
        o.hide_render = True; o.hide_viewport = True; hid += 1
log("driver parts hidden:", hid)
dc = bpy.data.objects.get("drv_cabin")
if dc: dc.hide_render = True   # the cabin point light existed to light the driver

# hide everything that is not the car/road: all collections except PORSCHE (and ROAD_GH); the founder walks near x=170 here
for c in bpy.data.collections:
    if c.name not in ("PORSCHE", "CAMS_V1", "CAMS_V2", "ROAD_GH"):
        c.hide_render = True
log("collections hidden:", [c.name for c in bpy.data.collections if c.hide_render])

# ---------------------------------------------------------------- badge / brand check: names + merged-material parts
BAD = [o.name for o in bpy.data.objects if any(k in o.name.lower() for k in ("badge", "emblem", "crest", "logo", "decal"))
       and not o.name.startswith("CAM_")]
log("badge-like object names:", BAD)
for n in BAD: bpy.data.objects[n].hide_render = True

# ---------------------------------------------------------------- shared helpers
def N(nt, typ, loc=(0, 0), **inp):
    n = nt.nodes.new(typ); n.location = loc
    for k, v in inp.items():
        if k in n.inputs: n.inputs[k].default_value = v
    return n
def L(nt, a, ai, b, bi): nt.links.new(a.outputs[ai], b.inputs[bi])
def mk_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    return m, nt
def mesh_obj(name, bm, mat=None, col=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc
    (col or sc.collection).objects.link(o)
    if mat: o.data.materials.append(mat)
    return o

def build_road_set(sun_side, sun_xy=None, el_deg=7.5, keep_house=False, ymax=400.0, sun_e=6.8, sky_k=0.6):
    """sun_side +1: sun from the +x side (verse 1 cameras are on +x), -1: from the -x side (post1 cameras are on -x).
    The sun is low, ahead of the car (+y) and to that side: front-lit, long shadows back across the road."""
    col = bpy.data.collections.new("ROAD_GH"); sc.collection.children.link(col)
    # hide the flat set + its lights + the old house/billboard/balcony dressing in PORSCHE
    for o in list(bpy.data.collections["PORSCHE"].all_objects):
        if o.name.startswith(("drive_", "au_", "bb_", "mh_", "qr", "PC_", "AU_")) and o.name != "CAR_ROOT":
            if keep_house and (o.name in ("drive_house", "drive_glass", "drive_wall") or o.name.startswith(("mh_", "drive_cypress")) and not o.name.startswith("drive_cypressS")):
                continue
            o.hide_render = True; o.hide_viewport = True
    for o in bpy.data.objects:
        if o.type == "LIGHT": o.hide_render = True
    CX = 180.0; ROADX0, ROADX1 = 174.6, 181.8   # car lane 178.2..181.8 (car centre x=180)
    # --- materials
    # ground: dry grass + scrub
    gm, nt = mk_mat("gh_ground")
    out = N(nt, "ShaderNodeOutputMaterial", (900, 0)); bs = N(nt, "ShaderNodeBsdfPrincipled", (600, 0))
    tc = N(nt, "ShaderNodeTexCoord", (-900, 0))
    n1 = N(nt, "ShaderNodeTexNoise", (-600, 200), **{"Scale": 0.35, "Detail": 6.0, "Roughness": 0.6})
    n2 = N(nt, "ShaderNodeTexNoise", (-600, -50), **{"Scale": 6.0, "Detail": 8.0, "Roughness": 0.65})
    n3 = N(nt, "ShaderNodeTexNoise", (-600, -300), **{"Scale": 70.0, "Detail": 3.0, "Roughness": 0.6})
    L(nt, tc, "Object", n1, "Vector"); L(nt, tc, "Object", n2, "Vector"); L(nt, tc, "Object", n3, "Vector")
    r1 = N(nt, "ShaderNodeValToRGB", (-350, 200))
    r1.color_ramp.elements[0].position = 0.38; r1.color_ramp.elements[0].color = (0.30, 0.235, 0.085, 1)     # straw
    r1.color_ramp.elements[1].position = 0.62; r1.color_ramp.elements[1].color = (0.085, 0.10, 0.035, 1)      # olive
    L(nt, n1, "Fac", r1, "Fac")
    mx = N(nt, "ShaderNodeMix", (-100, 100)); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 0.55
    r2 = N(nt, "ShaderNodeValToRGB", (-350, -50)); r2.color_ramp.elements[0].color = (0.55, 0.5, 0.42, 1); r2.color_ramp.elements[1].color = (1.15, 1.1, 1.0, 1)
    L(nt, n2, "Fac", r2, "Fac"); L(nt, r1, "Color", mx, 6); L(nt, r2, "Color", mx, 7)
    L(nt, mx, 2, bs, "Base Color")
    bp = N(nt, "ShaderNodeBump", (300, -250), **{"Strength": 0.35, "Distance": 0.05}); L(nt, n3, "Fac", bp, "Height"); L(nt, bp, "Normal", bs, "Normal")
    bs.inputs["Roughness"].default_value = 0.92; L(nt, bs, 0, out, "Surface")
    # asphalt with wheel-track wear
    am, nt = mk_mat("gh_asphalt")
    out = N(nt, "ShaderNodeOutputMaterial", (1200, 0)); bs = N(nt, "ShaderNodeBsdfPrincipled", (900, 0))
    tc = N(nt, "ShaderNodeTexCoord", (-1200, 0)); sp = N(nt, "ShaderNodeSeparateXYZ", (-1000, 300)); L(nt, tc, "Object", sp, "Vector")
    nf = N(nt, "ShaderNodeTexNoise", (-900, 0), **{"Scale": 160.0, "Detail": 8.0, "Roughness": 0.7}); L(nt, tc, "Object", nf, "Vector")
    nc = N(nt, "ShaderNodeTexNoise", (-900, -250), **{"Scale": 0.8, "Detail": 5.0, "Roughness": 0.6}); L(nt, tc, "Object", nc, "Vector")
    rf = N(nt, "ShaderNodeValToRGB", (-600, 0)); rf.color_ramp.elements[0].color = (0.030, 0.030, 0.034, 1); rf.color_ramp.elements[1].color = (0.085, 0.082, 0.078, 1)
    rf.color_ramp.elements[0].position = 0.35; rf.color_ramp.elements[1].position = 0.7
    L(nt, nf, "Fac", rf, "Fac")
    # wheel tracks at local x = lane centre +-0.8 (object coords are world-centred on the road object)
    def gauss(cx, y):
        sub = N(nt, "ShaderNodeMath", (-700, y)); sub.operation = "SUBTRACT"; L(nt, sp, "X", sub, 0); sub.inputs[1].default_value = cx
        sq = N(nt, "ShaderNodeMath", (-550, y)); sq.operation = "MULTIPLY"; L(nt, sub, 0, sq, 0); L(nt, sub, 0, sq, 1)
        sc_ = N(nt, "ShaderNodeMath", (-400, y)); sc_.operation = "MULTIPLY"; L(nt, sq, 0, sc_, 0); sc_.inputs[1].default_value = -9.0
        ex = N(nt, "ShaderNodeMath", (-250, y)); ex.operation = "EXPONENT"; L(nt, sc_, 0, ex, 0)
        return ex
    laneL = (178.2 + 1.8) - 180.0 - 0.0  # placeholder to keep names; tracks are set below from the object origin
    ROAD_ORIGIN = 178.2
    tracks = []
    for cxw in (ROAD_ORIGIN + 0.9, ROAD_ORIGIN + 2.7, ROAD_ORIGIN - 0.9, ROAD_ORIGIN - 2.7):   # 4 tracks (2 lanes x 2 wheels) relative to the road centre line
        tracks.append(gauss(cxw - ROAD_ORIGIN, -500 - 120 * len(tracks)))
    acc = tracks[0]
    for t in tracks[1:]:
        ad = N(nt, "ShaderNodeMath", (-100, -500)); ad.operation = "ADD"; L(nt, acc, 0, ad, 0); L(nt, t, 0, ad, 1); acc = ad
    wear = N(nt, "ShaderNodeMath", (50, -500)); wear.operation = "MULTIPLY"; L(nt, acc, 0, wear, 0); wear.inputs[1].default_value = 0.55
    dk = N(nt, "ShaderNodeMix", (300, 100)); dk.data_type = "RGBA"; dk.blend_type = "MULTIPLY"
    dkr = N(nt, "ShaderNodeMath", (200, -300)); dkr.operation = "MULTIPLY"; L(nt, wear, 0, dkr, 0); dkr.inputs[1].default_value = 0.6
    L(nt, dkr, 0, dk, 0); L(nt, rf, "Color", dk, 6); dk.inputs[7].default_value = (0.45, 0.45, 0.47, 1)
    pa = N(nt, "ShaderNodeMath", (-300, -250)); pa.operation = "MULTIPLY"; L(nt, nc, "Fac", pa, 0); pa.inputs[1].default_value = 0.25
    L(nt, dk, 2, bs, "Base Color")
    rr = N(nt, "ShaderNodeMath", (400, -450)); rr.operation = "SUBTRACT"; rr.inputs[0].default_value = 0.78; L(nt, wear, 0, rr, 1)
    L(nt, rr, 0, bs, "Roughness")
    bp = N(nt, "ShaderNodeBump", (700, -300), **{"Strength": 0.6, "Distance": 0.006}); L(nt, nf, "Fac", bp, "Height"); L(nt, bp, "Normal", bs, "Normal")
    L(nt, bs, 0, out, "Surface")
    # lane paint: worn
    def paint(name, rgb):
        m, nt = mk_mat(name)
        out = N(nt, "ShaderNodeOutputMaterial", (600, 0)); bs = N(nt, "ShaderNodeBsdfPrincipled", (300, 0))
        tc = N(nt, "ShaderNodeTexCoord", (-700, 0)); nz = N(nt, "ShaderNodeTexNoise", (-450, 0), **{"Scale": 60.0, "Detail": 6.0, "Roughness": 0.65})
        L(nt, tc, "Object", nz, "Vector")
        rp = N(nt, "ShaderNodeValToRGB", (-200, 0)); rp.color_ramp.elements[0].color = tuple(c * 0.55 for c in rgb) + (1,); rp.color_ramp.elements[1].color = tuple(rgb) + (1,)
        rp.color_ramp.elements[0].position = 0.35; rp.color_ramp.elements[1].position = 0.6
        L(nt, nz, "Fac", rp, "Fac"); L(nt, rp, "Color", bs, "Base Color"); bs.inputs["Roughness"].default_value = 0.6
        bp = N(nt, "ShaderNodeBump", (100, -250), **{"Strength": 0.3, "Distance": 0.004}); L(nt, nz, "Fac", bp, "Height"); L(nt, bp, "Normal", bs, "Normal")
        L(nt, bs, 0, out, "Surface"); return m
    wp = paint("gh_paint_white", (0.55, 0.55, 0.52)); yp = paint("gh_paint_yellow", (0.62, 0.40, 0.03))
    gv = mk_mat("gh_gravel"); m_g, nt = gv
    out = N(nt, "ShaderNodeOutputMaterial", (600, 0)); bs = N(nt, "ShaderNodeBsdfPrincipled", (300, 0))
    tc = N(nt, "ShaderNodeTexCoord", (-700, 0)); nz = N(nt, "ShaderNodeTexNoise", (-450, 0), **{"Scale": 120.0, "Detail": 7.0, "Roughness": 0.7})
    L(nt, tc, "Object", nz, "Vector")
    rg = N(nt, "ShaderNodeValToRGB", (-200, 0)); rg.color_ramp.elements[0].color = (0.16, 0.13, 0.095, 1); rg.color_ramp.elements[1].color = (0.40, 0.33, 0.24, 1)
    L(nt, nz, "Fac", rg, "Fac"); L(nt, rg, "Color", bs, "Base Color"); bs.inputs["Roughness"].default_value = 0.95
    bp = N(nt, "ShaderNodeBump", (100, -250), **{"Strength": 1.0, "Distance": 0.02}); L(nt, nz, "Fac", bp, "Height"); L(nt, bp, "Normal", bs, "Normal")
    L(nt, bs, 0, out, "Surface")

    def box(name, x0, x1, y0, y1, z, mat):
        bm = bmesh.new()
        v = [bm.verts.new((x0, y0, z)), bm.verts.new((x1, y0, z)), bm.verts.new((x1, y1, z)), bm.verts.new((x0, y1, z))]
        bm.faces.new(v)
        return mesh_obj(name, bm, mat, col)
    Y0, Y1 = -400.0, ymax
    # ground + shoulders + road + paint
    box("gh_ground", CX - 800, CX + 800, Y0 * 2, Y1 * 2, -0.06, gm)
    box("gh_shoulderL", 173.0, 174.6, Y0, Y1, -0.015, m_g); box("gh_shoulderR", 181.8, 183.6, Y0, Y1, -0.015, m_g)
    road = box("gh_road", ROADX0, ROADX1, Y0, Y1, 0.0, am); road.location = (0, 0, 0)
    # the object origin is world 0, so make the asphalt texture coords relative to the centre line: shift the mesh origin
    road.data.transform(__import__("mathutils").Matrix.Translation((-ROAD_ORIGIN, 0, 0))); road.location = (ROAD_ORIGIN, 0, 0)
    box("gh_edgeL", 174.9, 175.05, Y0, Y1, 0.003, wp); box("gh_edgeR", 181.45, 181.6, Y0, Y1, 0.003, wp)
    box("gh_cl1", 178.05, 178.17, Y0, Y1, 0.003, yp); box("gh_cl2", 178.23, 178.35, Y0, Y1, 0.003, yp)
    # --- scrub clumps + tree line (seeded)
    rnd = random.Random(7)
    def clumps(name, n, mat, rmin, rmax, dmin, dmax, ysp, hz):
        bm = bmesh.new()
        for _ in range(n):
            side = rnd.choice((-1, 1)); x = (173.0 - rnd.uniform(dmin, dmax)) if side < 0 else (183.6 + rnd.uniform(dmin, dmax)); y = rnd.uniform(-ysp, ysp)
            s = rnd.uniform(rmin, rmax)
            res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
            M = __import__("mathutils").Matrix
            mt = M.Translation((x, y, 0.0)) @ M.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ M.Diagonal(Vector((s * rnd.uniform(0.8, 1.6), s * rnd.uniform(0.8, 1.6), s * hz, 1)))
            bmesh.ops.transform(bm, matrix=mt, verts=res["verts"])
        return mesh_obj(name, bm, mat, col)
    def flatmat(name, rgb, rough=0.9):
        m, nt = mk_mat(name); out = N(nt, "ShaderNodeOutputMaterial", (300, 0)); bs = N(nt, "ShaderNodeBsdfPrincipled", (0, 0))
        bs.inputs["Base Color"].default_value = rgb + (1,); bs.inputs["Roughness"].default_value = rough; L(nt, bs, 0, out, "Surface"); return m
    clumps("gh_scrub_olive", 520, flatmat("gh_olive", (0.05, 0.065, 0.022)), 0.25, 0.8, 2.2, 28.0, 120, 0.7)
    clumps("gh_scrub_straw", 420, flatmat("gh_straw", (0.20, 0.15, 0.055)), 0.2, 0.6, 1.9, 24.0, 120, 0.45)
    clumps("gh_bush_big", 60, flatmat("gh_bush", (0.035, 0.05, 0.02)), 0.9, 1.8, 9.0, 60.0, 140, 0.9)
    # far tree line + low hills (hazy, lit by the same sun)
    bm = bmesh.new()
    M = __import__("mathutils").Matrix
    for i in range(46):
        side = rnd.choice((-1, 1)); x = CX + side * rnd.uniform(70, 160); y = rnd.uniform(-250, 150); h = rnd.uniform(5, 11)
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=h * 0.22, radius2=0.0, depth=h)
        bmesh.ops.transform(bm, matrix=M.Translation((x, y, h / 2)), verts=res["verts"])
    mesh_obj("gh_trees_far", bm, flatmat("gh_tree", (0.03, 0.045, 0.03)), col)
    bm = bmesh.new()
    for sx in (-1, 1):
        res = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
        bmesh.ops.transform(bm, matrix=M.Translation((CX + sx * 330, 40, -3)) @ M.Diagonal(Vector((120, 420, 28, 1))), verts=res["verts"])
    mesh_obj("gh_hills", bm, flatmat("gh_hill", (0.10, 0.095, 0.06), 1.0), col)
    # --- sky
    ax = {1: 1.0, -1: -1.0}[sun_side]
    sun_dir = Vector(sun_xy) if sun_xy else Vector((0.58 * ax, 0.74, 0.0)); el = math.radians(el_deg)
    sdir = Vector((sun_dir.normalized().x * math.cos(el), sun_dir.normalized().y * math.cos(el), math.sin(el)))
    w = bpy.data.worlds.new("GH_sky"); sc.world = w
    try: w.use_nodes = True
    except Exception: pass
    nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = N(nt, "ShaderNodeOutputWorld", (2400, 0)); bg = N(nt, "ShaderNodeBackground", (2100, 0)); bg.inputs["Strength"].default_value = 1.0
    tcw = N(nt, "ShaderNodeTexCoord", (-1500, 0))
    sp = N(nt, "ShaderNodeSeparateXYZ", (-1250, 200)); L(nt, tcw, "Generated", sp, "Vector")
    def M_(op, x, y, a=None, b_=None, clamp=False):
        m = N(nt, "ShaderNodeMath", (x, y)); m.operation = op; m.use_clamp = clamp
        if a is not None:
            if isinstance(a, (int, float)): m.inputs[0].default_value = a
            else: L(nt, a[0], a[1], m, 0)
        if b_ is not None:
            if isinstance(b_, (int, float)): m.inputs[1].default_value = b_
            else: L(nt, b_[0], b_[1], m, 1)
        return m
    zc = M_("MAXIMUM", -1050, 300, (sp, "Z"), 0.0)
    zp = M_("POWER", -900, 300, (zc, 0), 0.42)
    # sky gradient: horizon peach -> mid periwinkle -> zenith deep blue
    gr = N(nt, "ShaderNodeValToRGB", (-700, 300)); e = gr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (1.00, 0.52, 0.27, 1)
    e[1].position = 1.0; e[1].color = (0.06, 0.15, 0.42, 1)
    e.new(0.35).color = (0.55, 0.36, 0.42, 1)
    L(nt, zp, 0, gr, "Fac")
    # sun glow: dot(dir, sdir)
    dp = N(nt, "ShaderNodeVectorMath", (-1250, -100)); dp.operation = "DOT_PRODUCT"; L(nt, tcw, "Generated", dp, 0); dp.inputs[1].default_value = tuple(sdir)
    dm = M_("MAXIMUM", -1050, -100, (dp, "Value"), 0.0)
    g1 = M_("POWER", -900, -100, (dm, 0), 5.0); g2 = M_("POWER", -900, -250, (dm, 0), 40.0)
    g1c = N(nt, "ShaderNodeMix", (-700, -100)); g1c.data_type = "RGBA"; g1c.blend_type = "ADD"; g1c.inputs[0].default_value = 1.0
    gl = N(nt, "ShaderNodeRGB", (-900, -400)); gl.outputs[0].default_value = (1.0, 0.45, 0.16, 1)
    glm = N(nt, "ShaderNodeVectorMath", (-700, -300)); glm.operation = "SCALE"; L(nt, gl, 0, glm, 0); L(nt, g1, 0, glm, "Scale"); glm.inputs["Scale"].default_value = 1.0
    g1s = N(nt, "ShaderNodeVectorMath", (-500, -250)); g1s.operation = "SCALE"; L(nt, gl, 0, g1s, 0); L(nt, g2, 0, g1s, "Scale")
    # sky + glow
    add1 = N(nt, "ShaderNodeVectorMath", (-300, 100)); add1.operation = "ADD"; L(nt, gr, "Color", add1, 0); L(nt, glm, 0, add1, 1)
    add2 = N(nt, "ShaderNodeVectorMath", (-100, 100)); add2.operation = "ADD"; L(nt, add1, 0, add2, 0); L(nt, g1s, 0, add2, 1)
    # clouds: perspective-projected noise on the sky dome, lit warm from below, fading out at the horizon
    zd = M_("MAXIMUM", -1050, 700, (sp, "Z"), 0.06)
    cx_ = M_("DIVIDE", -900, 800, (sp, "X"), (zd, 0)); cy_ = M_("DIVIDE", -900, 650, (sp, "Y"), (zd, 0))
    cb = N(nt, "ShaderNodeCombineXYZ", (-750, 720)); L(nt, cx_, 0, cb, "X"); L(nt, cy_, 0, cb, "Y")
    mp = N(nt, "ShaderNodeMapping", (-600, 720)); mp.inputs["Scale"].default_value = (1.0, 2.2, 1.0); L(nt, cb, 0, mp, "Vector")
    cn = N(nt, "ShaderNodeTexNoise", (-400, 720), **{"Scale": 0.55, "Detail": 7.0, "Roughness": 0.58, "Distortion": 0.8}); L(nt, mp, 0, cn, "Vector")
    cr = N(nt, "ShaderNodeValToRGB", (-200, 720)); cr.color_ramp.elements[0].position = 0.50; cr.color_ramp.elements[1].position = 0.78
    L(nt, cn, "Fac", cr, "Fac")
    fz = M_("SMOOTH_MIN", 0, 0)  # placeholder removed below
    nt.nodes.remove(fz)
    hz = M_("MULTIPLY", -200, 560, (sp, "Z"), 7.0, clamp=True)   # fades the clouds out toward the horizon
    cm_ = M_("MULTIPLY", 0, 700, (cr, "Color"), (hz, 0))
    cm2 = M_("MULTIPLY", 150, 700, (cm_, 0), 0.85)
    ccol = N(nt, "ShaderNodeMix", (150, 400)); ccol.data_type = "RGBA"; ccol.inputs[0].default_value = 0.55
    ccol.inputs[6].default_value = (1.0, 0.55, 0.34, 1); ccol.inputs[7].default_value = (0.55, 0.40, 0.50, 1)
    # lit side: warmer toward the sun
    L(nt, dm, 0, ccol, 0)
    fin = N(nt, "ShaderNodeMix", (500, 100)); fin.data_type = "RGBA"; L(nt, cm2, 0, fin, 0); L(nt, add2, 0, fin, 6); L(nt, ccol, 2, fin, 7)
    # below the horizon: haze colour
    bz = M_("MULTIPLY", 350, -250, (sp, "Z"), -40.0, clamp=True)
    fin2 = N(nt, "ShaderNodeMix", (800, 0)); fin2.data_type = "RGBA"; L(nt, bz, 0, fin2, 0); L(nt, fin, 2, fin2, 6); fin2.inputs[7].default_value = (0.20, 0.10, 0.06, 1)
    L(nt, fin2, 2, bg, "Color"); L(nt, bg, 0, out, "Surface")
    bg.inputs["Strength"].default_value = sky_k
    # --- sun lamp
    sd = bpy.data.lights.new("GH_sun", "SUN"); sd.energy = sun_e; sd.color = (1.0, 0.64, 0.36); sd.angle = math.radians(1.4)
    so = bpy.data.objects.new("GH_sun", sd); col.objects.link(so)
    so.rotation_euler = sdir.to_track_quat("Z", "Y").to_euler()
    # cool bounce fill from the opposite sky side (a real source: the blue sky) kept low
    fd = bpy.data.lights.new("GH_skyfill", "SUN"); fd.energy = 0.35; fd.color = (0.55, 0.65, 1.0); fd.angle = math.radians(25)
    fo = bpy.data.objects.new("GH_skyfill", fd); col.objects.link(fo)
    fo.rotation_euler = Vector((-sdir.x, -sdir.y, 0.7)).normalized().to_track_quat("Z", "Y").to_euler()
    log("road set built; sun_dir", tuple(round(x, 2) for x in sdir))

if MODE == "v1":
    build_road_set(+1)
elif MODE == "post1":
    build_road_set(-1)
elif MODE == "outro":
    # DIAGNOSIS: the take is blacked out f5620-5629 (blend 1882-1891) because CAM_od_rear (x=177.5, parented to the car) rides
    # THROUGH the left gate pillar (drive_gateL x177.5-178.1), the south wall (drive_wallS_L y-8.6..-8.1) and the S cypress row
    # (y-9.5): the lens sits inside lit stone. Fix: the gate + south wall + S cypresses are hidden; camera path unchanged.
    for n in ("drive_gateL", "drive_gateR", "drive_wallS_L", "drive_wallS_R"):
        bpy.data.objects[n].hide_render = True
    for o in bpy.data.objects:
        if o.name.startswith("drive_cypressS"): o.hide_render = True
    # sun behind the camera (low, from -y): the car's rear and the house front catch the last light, sky ahead is dusk
    build_road_set(-1, sun_xy=(-0.30, -0.95), el_deg=4.5, keep_house=True, ymax=7.4, sun_e=5.0, sky_k=0.5)

# ---------------------------------------------------------------- eevee: shadows + ray tracing for ground contact
ev = sc.eevee
for k in ("use_shadows", "use_raytracing"):
    if hasattr(ev, k):
        try: setattr(ev, k, True)
        except Exception as ex: log("eevee", k, ex)
if MODE in ("post1", "outro"):
    sc.render.use_motion_blur = True
    for k, v in (("motion_blur_shutter", 0.5),):
        try: setattr(sc.render, k, v)
        except Exception as ex: log("mb", k, ex)
    try: sc.eevee.motion_blur_steps = 4
    except Exception as ex: log("mb steps", ex)
log("eevee samples", ev.taa_render_samples, "motion blur", sc.render.use_motion_blur)

bpy.ops.wm.save_mainfile()
open(bpy.data.filepath.replace(".blend", "_build.log"), "w").write("\n".join(LOG))
