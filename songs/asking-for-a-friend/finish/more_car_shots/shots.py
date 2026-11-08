"""more_car_build: the three approved extra GT3 RS beats as real shots (her OK, Sat Nov 7 07:32: road, garage, posted).
Blender -b <copy.blend> --python shots.py -- <beat road|garage|posted> <fmt 169|916> <mode stills|final> <outdir> <samples> [master frames, comma-sep, stills only]
Builds the beat at load time on a COPY (never saved): the approved board look (finish/more_car/more_stills.py) plus the
flagged fixes (darker night, readable ON AIR ring light / phone UV / hazards, calipers in view, big car in 9:16, CC0
surfaces in the garage). Files: stills -> <outdir>/<beat>_<fmt>_<master>.png; final -> <outdir>/f_<master>.png (16-bit,
resumable, master-numbered; graded by short/tools/finish_still.py afterwards).
CHECK lines print the car's projected box per format (9:16: car inside x .06-.94, y above the bottom 30%)."""
import bpy, sys, os, math, glob, json, time
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view

A = sys.argv[sys.argv.index("--") + 1:]
BEAT, FMT, MODE, OUT, SM = A[0], A[1], A[2], A[3], int(A[4])
STILLS = [int(x) for x in A[5].split(",")] if len(A) > 5 and A[5] else []
os.makedirs(OUT, exist_ok=True)
W, H = (1920, 1080) if FMT == "169" else (1080, 1920)
HERE = os.path.dirname(os.path.abspath(__file__))
CARDIR = os.path.join(HERE, "..", "car")
TEX = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender/textures/ph")
sc = bpy.context.scene
_me = __file__
__file__ = os.path.join(CARDIR, "render_final.py")      # plate.py resolves plate/ next to its caller (Texas plate + frame, D WHEEL)
exec(open(os.path.join(CARDIR, "plate.py")).read())
exec(open(os.path.join(CARDIR, "wheels.py")).read())   # fix_wheels: spin = ground speed, radial smear, tyre detail (WHEELS=0 = old); garage/posted clear the spin keys after
__file__ = _me
ROOT = bpy.data.objects["CAR_ROOT"]
SPANS = {"road": (4039, 4059), "garage": (4406, 4430), "posted": (5658, 5697)}
MA, MB = SPANS[BEAT]

def ss(x):  # smoothstep
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def ease_out(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

# ---------- helpers (same building blocks as the approved boards) ----------
def hide_driver():
    for o in bpy.data.objects:
        if o.name.startswith("drv_"): o.hide_render = True; o.hide_viewport = True

def car_parts(root):
    return [o for o in [root] + list(root.children_recursive) if o.type != "CAMERA" and not o.hide_render]

def car_pts(root):
    pts = []
    for o in car_parts(root):
        if o.type == "MESH" and not o.name.startswith("MORE_"):
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    return pts

def light(name, kind, loc, energy, col, rot=(0, 0, 0), size=None, spot=None, parent=None, coll=None, aim=None):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
    if size is not None:
        if kind == "AREA": d.size = size
        else: d.shadow_soft_size = size
    if spot: d.spot_size = math.radians(spot); d.spot_blend = 0.4
    o = bpy.data.objects.new(name, d); (coll or sc.collection).objects.link(o)
    if parent: o.parent = parent
    o.location = loc; o.rotation_euler = rot
    if aim is not None: o.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()   # parent space
    return o

def mat_emit(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = strength
    return m

def mat_plain(name, col, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    return m

def mat_pbr(name, tex, scale=1.0, tint=None, rough=None, metal=None):
    """Poly Haven CC0 texture set (diff / rough / nor_gl 2k) from blender/textures/ph."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    def img(suffix, noncolor):
        p = os.path.join(TEX, tex, f"{tex}_{suffix}_2k.jpg")
        if not os.path.exists(p): return None
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(p, check_existing=True)
        t.projection = "BOX"; t.projection_blend = 0.2
        if noncolor: t.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    d = img("diff", False)
    if d:
        if tint:
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
            mx.inputs["Factor"].default_value = 1.0; nt.links.new(d.outputs["Color"], mx.inputs[6])
            mx.inputs[7].default_value = (*tint, 1); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
        else: nt.links.new(d.outputs["Color"], b.inputs["Base Color"])
    r = img("rough", True)
    if r and rough is None: nt.links.new(r.outputs["Color"], b.inputs["Roughness"])
    if rough is not None: b.inputs["Roughness"].default_value = rough
    if metal is not None: b.inputs["Metallic"].default_value = metal
    n = img("nor_gl", True)
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nm.inputs["Strength"].default_value = 0.6; nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m

def box(name, loc, dims, mat, coll, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    x, y, z = [d / 2 for d in dims]
    v = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    f = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    me.from_pydata(v, [], f); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); o.location = loc; o.rotation_euler = rot
    if mat: o.data.materials.append(mat)
    return o

def prim(kind, name, loc, mat, coll, rot=(0, 0, 0), **kw):
    """torus / cylinder / uv sphere via bpy.ops (background-safe), linked into coll."""
    if kind == "torus": bpy.ops.mesh.primitive_torus_add(location=loc, rotation=rot, **kw)
    elif kind == "cyl": bpy.ops.mesh.primitive_cylinder_add(location=loc, rotation=rot, **kw)
    else: bpy.ops.mesh.primitive_uv_sphere_add(location=loc, rotation=rot, **kw)
    o = bpy.context.active_object; o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    coll.objects.link(o)
    if mat: o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    return o

def night_world(top=(0.004, 0.006, 0.016), horizon=(0.03, 0.04, 0.075), strength=1.0):
    w = bpy.data.worlds.new("MORE_night"); w.use_nodes = True; nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sp.inputs[0]); nt.links.new(sp.outputs["Z"], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (*horizon, 1)
    cr.color_ramp.elements[1].position = 0.35; cr.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(cr.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = strength
    sc.world = w

UV = (0.55, 0.28, 1.0)
def on_air(root, coll, energy=150, ring_strength=9.0):
    """His podcast is the car: a ring light on the dash (an emissive ring you can see through the 22%-alpha tinted glass)
    lighting the cabin ultraviolet (his colour), a red REC dot. Real sources; car-local (front is -y, cabin z .55-1.15)."""
    # r2: ring moved INSIDE the cabin (dash-mounted, ~0.45 m ahead of the driver; r1 sat on the windscreen) and dimmed so
    # it reads violet, not blown white
    ring = prim("torus", "MORE_ringlight", (0, 0, 0), mat_emit("MORE_ring_m", UV, ring_strength), coll,
                major_radius=0.09, minor_radius=0.011, major_segments=48, minor_segments=8)
    ring.parent = root; ring.location = (0.28, -0.15, 0.95); ring.rotation_euler = (math.radians(90), 0, 0)
    light("MORE_cabin_uv", "AREA", (0.28, -0.10, 0.95), energy, UV, size=0.18, parent=root, coll=coll, aim=(0.25, 0.8, 0.95))
    light("MORE_cabin_fill", "POINT", (0.0, 0.2, 1.08), energy * 0.5, UV, size=0.2, parent=root, coll=coll)
    rec = prim("sphere", "MORE_rec", (0, 0, 0), mat_emit("MORE_rec_m", (1.0, 0.04, 0.02), 40.0), coll, radius=0.010, segments=12, ring_count=8)
    rec.parent = root; rec.location = (0.28, -0.15, 1.07)
    cabin_shell(root, coll)
    return ring

def cabin_shell(root, coll):
    """r3: the car model has no interior, so cabin light had nothing to land on (r2 posted: no UV through the glass).
    Two seat backs + a headliner in mid-grey fabric, inside the window line (car-local; windows z .83-1.19)."""
    fab = mat_plain("MORE_fabric", (0.22, 0.22, 0.24), 0.9)
    for sx in (-0.36, 0.36):
        sb = box(f"MORE_seat_{sx}", (0, 0, 0), (0.48, 0.12, 0.62), fab, coll); sb.parent = root
        sb.location = (sx, 0.62, 0.80); sb.rotation_euler = (math.radians(-14), 0, 0)
    hl = box("MORE_headliner", (0, 0, 0), (1.15, 1.0, 0.015), fab, coll); hl.parent = root; hl.location = (0.0, 0.25, 1.115)

def headlights(root, coll, energy=450):
    for sx in (-0.68, 0.68):   # car-local: FRONT is -y
        light(f"MORE_head_{sx}", "SPOT", (sx, -2.25, 0.68), energy, (1.0, 0.95, 0.88), rot=(math.radians(-86), 0, 0), size=0.05, spot=55, parent=root, coll=coll)
    for sx in (-0.72, 0.72):
        light(f"MORE_tail_{sx}", "POINT", (sx, 2.2, 0.86), 6, (1.0, 0.04, 0.02), size=0.08, parent=root, coll=coll)

def car_lenses(root, groups):
    """Light lenses as real emitters: faces of the Lights1Mtl object split by where they sit on the car (car-local).
    groups = [(test(x, y, z), material)], first match wins; unmatched faces keep the lens material."""
    inv = root.matrix_world.inverted()
    for o in car_parts(root):
        if o.type != "MESH" or not any(sl.material and sl.material.name == "Lights1Mtl" for sl in o.material_slots): continue
        li = next(i for i, sl in enumerate(o.material_slots) if sl.material and sl.material.name == "Lights1Mtl")
        base = len(o.data.materials)
        for _, m in groups: o.data.materials.append(m)
        M = inv @ o.matrix_world; cnt = [0] * len(groups)
        for p in o.data.polygons:
            if p.material_index != li: continue
            c = M @ p.center
            for gi, (test, _) in enumerate(groups):
                if test(c.x, c.y, c.z): p.material_index = base + gi; cnt[gi] += 1; break
        print("[lenses]", o.name, cnt, flush=True)

def front_plate(root):
    """Texas has front plates: a copy of the approved D WHEEL plate (+ frame) on the front bumper, found by ray cast."""
    dg = bpy.context.evaluated_depsgraph_get(); RW = root.matrix_world
    org = RW @ Vector((0, -4.0, 0.36)); dirv = (RW.to_quaternion() @ Vector((0, 1, 0))).normalized()
    hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, org, dirv)
    yl = (RW.inverted() @ loc).y - 0.012 if hit else -2.22
    print("[front_plate] hit", hit, ob.name if hit else None, round(yl, 3), flush=True)
    for n, dy in (("GT3_PLATE", 0.0), ("GT3_PLATE_FRAME", -0.003)):
        src = bpy.data.objects.get(n)
        if not src: continue
        o = src.copy(); sc.collection.objects.link(o); o.name = n + "_FRONT"
        o.parent = root; o.location = (0.0, yl + dy, 0.36); o.rotation_euler = (0, 0, 0)

def duplicate_car(root, coll):
    mp = {}
    for o in car_parts(root):
        n = o.copy(); coll.objects.link(n); mp[o] = n
    for o, n in mp.items():
        if o.parent in mp: n.parent = mp[o.parent]; n.matrix_parent_inverse = o.matrix_parent_inverse.copy()
    return mp[root]

def new_cam(name, lens):
    d = bpy.data.cameras.new(name); d.lens = lens; d.sensor_width = 36; d.sensor_fit = "AUTO"
    d.clip_start = 0.05; d.clip_end = 3000
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.rotation_mode = "QUATERNION"
    return o

def look(loc, target):
    return (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y")

def key_cam(camo, frames, posefn, parent=None):
    """posefn(master) -> (loc, target[, shift_y]); keys loc + quaternion (+ lens shift) on every blend frame a-1..b+1."""
    if parent: camo.parent = parent
    prev = None
    for m in frames:
        p = posefn(m); loc, tgt = Vector(p[0]), Vector(p[1])
        q = look(loc, tgt)
        if prev is not None and prev.dot(q) < 0: q.negate()
        prev = q
        camo.location = loc; camo.rotation_quaternion = q
        f = m + OFF
        camo.keyframe_insert("location", frame=f); camo.keyframe_insert("rotation_quaternion", frame=f)
        if len(p) > 2:
            camo.data.shift_y = p[2]; camo.data.keyframe_insert("shift_y", frame=f)
    for ad in (camo.animation_data, camo.data.animation_data):
        if ad and ad.action:
            for fc in _fcurves(ad.action):
                for k in fc.keyframe_points: k.interpolation = "LINEAR"

def _fcurves(action):
    fcs = getattr(action, "fcurves", None)
    if fcs is not None and len(fcs): return list(fcs)
    out = []   # Blender 5 layered actions
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out

def key_const(idb, path, frame, value):
    setattr(idb, path, value); idb.keyframe_insert(path, frame=frame)

def const_interp(idb):
    ad = idb.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for k in fc.keyframe_points: k.interpolation = "CONSTANT"

def check(camo, roots, label):
    sc.camera = camo
    sc.render.resolution_x, sc.render.resolution_y = W, H
    for m in sorted({MA, (MA + MB) // 2, MB} | set(STILLS)):
        sc.frame_set(m + OFF); bpy.context.view_layer.update()
        for r in roots:
            uv = [world_to_camera_view(sc, camo, p) for p in car_pts(r)]
            xs = [u.x for u in uv]; ys = [u.y for u in uv]
            if FMT == "916": ok = min(xs) > 0.06 and max(xs) < 0.94 and min(ys) > 0.28 and max(ys) < 0.90
            else: ok = min(xs) > 0.03 and max(xs) < 0.97 and min(ys) > 0.03 and max(ys) < 0.97
            if label == "posted" and m > MA + 12: ok = True   # the push ends on the plate: the car leaves frame on purpose
            print(f"CHECK {label} {FMT} m{m} {r.name}: x {min(xs):.3f}-{max(xs):.3f} y {min(ys):.3f}-{max(ys):.3f} "
                  f"w {max(xs)-min(xs):.2f} {'OK' if ok else 'CLIPS/SMALL-MARGIN'}", flush=True)

# ---------- scene prep ----------
sc.eevee.taa_render_samples = SM
try: sc.eevee.shadow_pool_size = "1024"     # r1 posted: "Shadow buffer full (2586/2048)" on the house set
except Exception as e: print("[shadow_pool]", e)
hide_driver()
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)   # markers would switch our cameras
COL = bpy.data.collections.new("MORE_CAR"); sc.collection.children.link(COL)
roots = [ROOT]

if BEAT == "road":
    # "He's on a podcast, ON THE ROAD!" f4039 (on "road") - 4059. The car at speed on the env2 road (post1 copy, blend
    # 1852-1872, ~14 m/s, front faces +y world). Camera rides with the car (parented): a front 3/4 that eases toward the side.
    OFF = 1852 - 4039
    sc.frame_set(1856); cpos = ROOT.matrix_world.translation.copy()
    for n in ("GH_sun", "GH_skyfill"):
        o = bpy.data.objects.get(n)
        if o: o.hide_render = True
    night_world(top=(0.0015, 0.0022, 0.006), horizon=(0.010, 0.013, 0.026), strength=0.6)   # fix: darker night
    light("MORE_moon", "SUN", (0, 0, 50), 0.07, (0.62, 0.72, 1.0), rot=(math.radians(62), 0, math.radians(-35)), coll=COL)
    sc.view_settings.exposure = -0.1
    headlights(ROOT, COL); on_air(ROOT, COL)
    car_lenses(ROOT, [(lambda x, y, z: y < 0, mat_emit("MORE_headlens", (1.0, 0.95, 0.88), 3.5)),
                      (lambda x, y, z: y > 0, mat_emit("MORE_taillens", (1.0, 0.03, 0.02), 5.0))])
    pole_m = mat_pbr("MORE_pole", "metal_plate_02", 2.0, tint=(0.35, 0.36, 0.38), rough=0.5)
    head_m = mat_emit("MORE_lamp_head", (1.0, 0.86, 0.68), 30.0)
    for i in range(-3, 6):     # highway lamps on the camera side every 38 m (real sources for paint + calipers)
        y = cpos.y + 1.5 + i * 38; x = cpos.x + 5.6
        box(f"MORE_pole_{i}", (x, y, 3.6), (0.16, 0.16, 7.2), pole_m, COL)
        box(f"MORE_arm_{i}", (x - 1.3, y, 7.15), (2.6, 0.1, 0.1), pole_m, COL)
        box(f"MORE_head_{i}", (x - 2.4, y, 7.05), (0.7, 0.28, 0.08), head_m, COL)
        light(f"MORE_lampL_{i}", "SPOT", (x - 2.4, y, 6.95), 1700, (1.0, 0.86, 0.68), size=0.3, spot=110, coll=COL)
    # the tracking car's soft light, low on the camera side: the yellow caliper and wheel read (motivated: camera car)
    light("MORE_trackfill", "AREA", (-3.0, -3.2, 0.5), 120, (0.85, 0.88, 1.0), size=1.2, parent=ROOT, coll=COL, aim=(-0.6, -1.3, 0.35))
    camo = new_cam("CAM_more_road", 34 if FMT == "169" else 27)
    # car-local camera positions (front is -y local; camera on the car's left-local = world +x side)
    if FMT == "169": P0, P1, AIM, SH = Vector((-3.7, -5.0, 0.72)), Vector((-4.6, -3.5, 0.70)), Vector((-0.15, -0.55, 0.55)), 0.0
    else:            P0, P1, AIM, SH = Vector((-4.7, -6.8, 1.05)), Vector((-5.7, -5.0, 1.0)), Vector((-0.05, -0.35, 0.55)), -0.06   # r2: farther, no clip
    key_cam(camo, range(MA - 1, MB + 2), lambda m: (P0.lerp(P1, ss((m - MA) / (MB - MA))), AIM, SH), parent=ROOT)

elif BEAT == "garage":
    # "He raised another TWENTY MILLION" f4406-4430: the door rolls up from "twenty" (4409) to open by "million" (4418)
    # on two identical GT3 RSs parked NOSE-OUT (calipers in view). Built away from the set at x=420 on the post1 copy.
    OFF = 1856 - 4406
    sc.frame_set(1856)
    if ROOT.animation_data: ROOT.animation_data_clear()
    for w in ("wheel_piv_FL", "wheel_piv_FR", "wheel_piv_RL", "wheel_piv_RR"):   # parked: wheels don't turn
        o = bpy.data.objects.get(w)
        if o and o.animation_data: o.animation_data_clear()
    G = Vector((420.0, 0.0, 0.0)); CY = 0.7
    ROOT.location = G + Vector((-1.4, CY, 0)); ROOT.rotation_euler = (0, 0, 0)     # rot 0: front (-y local) faces the door
    bpy.context.view_layer.update()
    front_plate(ROOT); bpy.context.view_layer.update()
    car2 = duplicate_car(ROOT, COL); car2.location = G + Vector((1.4, CY, 0)); roots.append(car2)
    for n in ("GH_sun", "GH_skyfill"):
        o = bpy.data.objects.get(n)
        if o: o.hide_render = True
    night_world(strength=0.55)
    sc.view_settings.exposure = -0.25
    # CC0 surfaces (Poly Haven, on disk; logged in assets/polyhaven/SOURCES.md)
    floor = mat_pbr("MORE_conc", "concrete_floor_worn_001", 0.35)
    wall = mat_pbr("MORE_wall", "concrete_wall_006", 0.45, tint=(0.80, 0.79, 0.76))
    drive = mat_pbr("MORE_drive", "concrete_floor_02", 0.25, tint=(0.55, 0.55, 0.55))
    paintc = mat_pbr("MORE_paintc", "painted_concrete_02", 0.5, tint=(0.62, 0.62, 0.64))
    steel = mat_pbr("MORE_steel", "metal_plate_02", 1.5, tint=(0.30, 0.31, 0.33), rough=0.45, metal=0.8)
    benchtop = mat_pbr("MORE_bench", "wood_table_001", 0.8)
    mat_rub = mat_pbr("MORE_mat", "rubber_tiles", 0.6, tint=(0.35, 0.35, 0.36))
    door_m = mat_plain("MORE_door", (0.11, 0.115, 0.12), 0.42, 0.6)
    bin_m = mat_plain("MORE_bin", (0.06, 0.065, 0.07), 0.55); lid_m = mat_plain("MORE_lid", (0.75, 0.62, 0.10), 0.5)
    tyre = bpy.data.materials.get("Tyre1Mtl") or mat_plain("MORE_tyre", (0.02, 0.02, 0.02), 0.8)
    red = mat_plain("MORE_ext", (0.55, 0.02, 0.02), 0.35)
    D0 = G.y - 3.0
    box("MORE_gfloor", (G.x, G.y + 1.0, -0.02), (7.4, 8.4, 0.04), floor, COL)
    box("MORE_drive", (G.x, D0 - 7.0, -0.03), (9.0, 14.0, 0.04), drive, COL)
    box("MORE_back", (G.x, G.y + 5.2, 1.5), (7.4, 0.2, 3.0), wall, COL)
    box("MORE_sideL", (G.x - 3.8, G.y + 1.0, 1.5), (0.2, 8.6, 3.0), wall, COL)
    box("MORE_sideR", (G.x + 3.8, G.y + 1.0, 1.5), (0.2, 8.6, 3.0), wall, COL)
    box("MORE_ceil", (G.x, G.y + 1.0, 3.0), (7.8, 8.6, 0.12), paintc, COL)
    box("MORE_pierL", (G.x - 3.45, D0, 1.5), (0.9, 0.3, 3.0), wall, COL)
    box("MORE_pierR", (G.x + 3.45, D0, 1.5), (0.9, 0.3, 3.0), wall, COL)
    box("MORE_header", (G.x, D0, 2.75), (6.0, 0.3, 0.5), wall, COL)
    box("MORE_facade", (G.x, D0 - 0.01, 4.0), (9.0, 0.3, 2.2), wall, COL)
    for sx in (-1.4, 1.4):      # rubber mats under each car
        box(f"MORE_rmat_{sx}", (G.x + sx, G.y + CY, 0.006), (2.5, 4.9, 0.012), mat_rub, COL)
    # steel shelving, left wall: uprights, 4 shelves, storage bins with yellow lids
    for j, y in enumerate((G.y + 1.6, G.y + 4.4)):
        for dx in (0.0, 0.55):
            box(f"MORE_up_{j}_{dx}", (G.x - 3.65 + dx, y, 1.1), (0.04, 0.04, 2.2), steel, COL)
    for k, z in enumerate((0.25, 0.85, 1.45, 2.05)):
        box(f"MORE_shelf_{k}", (G.x - 3.375, G.y + 3.0, z), (0.6, 2.85, 0.03), steel, COL)
        for b in range(4):
            if (k + b) % 3 == 2: continue
            by = G.y + 1.95 + b * 0.68; h = 0.34 if k < 3 else 0.28
            box(f"MORE_bin_{k}_{b}", (G.x - 3.40, by, z + 0.015 + h / 2), (0.46, 0.55, h), bin_m, COL)
            box(f"MORE_lid_{k}_{b}", (G.x - 3.40, by, z + 0.02 + h), (0.48, 0.57, 0.025), lid_m, COL)
    # tyre rack, back wall left: 4 spare tyres on a steel bar
    box("MORE_tbar", (G.x - 2.0, G.y + 4.95, 1.9), (1.6, 0.05, 0.05), steel, COL)
    for t in range(4):
        prim("torus", f"MORE_spare_{t}", (G.x - 2.6 + t * 0.4, G.y + 4.78, 1.55), tyre, COL, rot=(0, math.radians(90), 0),
             major_radius=0.29, minor_radius=0.11, major_segments=40, minor_segments=12)
    # workbench + wall cabinet, back wall right
    box("MORE_benchtop", (G.x + 2.2, G.y + 4.75, 0.92), (2.2, 0.7, 0.05), benchtop, COL)
    box("MORE_benchbase", (G.x + 2.2, G.y + 4.78, 0.45), (2.15, 0.62, 0.88), steel, COL)
    for d in range(4):
        box(f"MORE_drawer_{d}", (G.x + 1.42 + d * 0.52, G.y + 4.46, 0.45), (0.48, 0.02, 0.8), mat_plain(f"MORE_drw{d}", (0.07, 0.075, 0.08), 0.4, 0.5), COL)
    box("MORE_cab", (G.x + 2.2, G.y + 4.9, 2.15), (2.15, 0.4, 0.75), steel, COL)
    prim("cyl", "MORE_extinguisher", (G.x + 3.55, D0 + 0.55, 0.42), red, COL, radius=0.08, depth=0.5)
    tube = mat_emit("MORE_tube", (0.92, 0.96, 1.0), 25.0)
    for sx in (-1.4, 1.4):   # one LED batten over each car: real sources
        box(f"MORE_tube_{sx}", (G.x + sx, G.y + 0.6, 2.92), (0.07, 1.6, 0.05), tube, COL)
        light(f"MORE_tubeL_{sx}", "AREA", (G.x + sx, G.y + 0.6, 2.88), 300, (0.92, 0.96, 1.0), size=1.4, coll=COL)
    light("MORE_tubeL_bench", "AREA", (G.x + 2.2, G.y + 4.2, 1.7), 60, (1.0, 0.9, 0.75), size=1.0, coll=COL, aim=(G.x + 2.2, G.y + 4.9, 0.9))
    sconce = mat_emit("MORE_sconce", (1.0, 0.78, 0.5), 12.0)
    for sx in (-3.45, 3.45):
        box(f"MORE_sconce_{sx}", (G.x + sx, D0 - 0.2, 2.2), (0.14, 0.1, 0.24), sconce, COL)
        light(f"MORE_sconceL_{sx}", "POINT", (G.x + sx, D0 - 0.35, 2.2), 60, (1.0, 0.78, 0.5), size=0.1, coll=COL)
    # sectional door: 5 panels on a track (vertical in the opening, then horizontal under the ceiling), s = travel in m
    NP, PH, HOPEN = 5, 0.53, 2.6
    panels = [box(f"MORE_door_{i}", (0, 0, 0), (6.0, 0.045, PH - 0.01), door_m, COL) for i in range(NP)]
    def door_at(s):
        # r2 (finals check): a roll-up shutter going straight up behind the header into the ceiling slab. The r1 track
        # flipped each panel vertical->horizontal between two frames and motion blur smeared it over the battens (f4410-11).
        for i, p in enumerate(panels):
            p.location = (G.x, D0 + 0.2, i * PH + PH / 2 + s); p.rotation_euler = (0, 0, 0)
    for m in range(MA - 1, MB + 2):
        s = HOPEN * ease_out((m - 4409) / (4418 - 4409))
        door_at(s); f = m + OFF
        for p in panels: p.keyframe_insert("location", frame=f); p.keyframe_insert("rotation_euler", frame=f)
    for p in panels:
        for fc in _fcurves(p.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = "LINEAR"
    t = G + Vector((0, CY - 0.6, 0.62))
    if FMT == "169":
        camo = new_cam("CAM_more_garage", 30)
        C0, C1 = G + Vector((2.5, D0 - G.y - 7.6, 0.55)), G + Vector((1.9, D0 - G.y - 4.6, 0.62))   # r2: push in on the reveal
        key_cam(camo, range(MA - 1, MB + 2), lambda m: (C0.lerp(C1, ss((m - MA) / (MB - MA))), t + Vector((0, 0, 0.35)), -0.02))
    else:   # 9:16: a steeper 3/4 so the two cars stack diagonally and fill the narrow frame
        camo = new_cam("CAM_more_garage", 26)
        C0, C1 = G + Vector((4.4, D0 - G.y - 6.6, 0.75)), G + Vector((3.6, D0 - G.y - 4.5, 0.85))   # r2: push in
        key_cam(camo, range(MA - 1, MB + 2), lambda m: (C0.lerp(C1, ss((m - MA) / (MB - MA))), t + Vector((0.2, 0, 0.55)), -0.08))

elif BEAT == "posted":
    # "He has just POSTED ON LINKEDIN" f5658-5697: pulled over at the house (outro copy), hazards blinking, the cabin lit
    # ultraviolet by his phone; rear 3/4 (rear caliper) pushing to the D WHEEL plate, landing on "posted" (5696).
    OFF = int(os.environ.get("POSTED_BLEND_FRAME", "1919")) - 5658
    sc.frame_set(MA + OFF)
    if ROOT.animation_data:          # hold the parked pose for the whole beat
        mw = ROOT.matrix_world.copy(); ROOT.animation_data_clear(); ROOT.matrix_world = mw
    for w in ("wheel_piv_FL", "wheel_piv_FR", "wheel_piv_RL", "wheel_piv_RR"):
        o = bpy.data.objects.get(w)
        if o and o.animation_data: o.animation_data_clear()
    bpy.context.view_layer.update()
    on_air(ROOT, COL, energy=170, ring_strength=0.0)        # phone, not ring: hide the ring, keep the UV light (r2: stronger)
    bpy.data.objects["MORE_ringlight"].hide_render = True; bpy.data.objects["MORE_rec"].hide_render = True
    light("MORE_cabin_roof", "POINT", (0.1, 0.6, 1.10), 60, UV, size=0.25, parent=ROOT, coll=COL)   # glow toward the rear glass
    # low warm fill from the house porch side on the near rear wheel: the yellow caliper reads on the rear 3/4
    light("MORE_wheelfill", "AREA", (2.6, 3.4, 0.45), 45, (1.0, 0.85, 0.65), size=0.8, parent=ROOT, coll=COL, aim=(0.85, 1.35, 0.35))
    phone = box("MORE_phone", (0, 0, 0), (0.075, 0.008, 0.155), mat_emit("MORE_phone_m", (0.78, 0.62, 1.0), 30.0), COL)
    phone.parent = ROOT; phone.location = (0.28, -0.40, 0.93); phone.rotation_euler = (math.radians(-20), 0, 0)   # dash mount: nobody's at the wheel
    uvl = bpy.data.objects["MORE_cabin_uv"]; uvl.location = (0.28, -0.34, 0.95)
    uvl.rotation_euler = (Vector((0.1, 0.8, 1.0)) - Vector((0.28, -0.34, 0.95))).to_track_quat("-Z", "Y").to_euler()
    amber = (1.0, 0.45, 0.04)
    hzm = mat_emit("MORE_hazlens", amber, 0.0)
    car_lenses(ROOT, [(lambda x, y, z: y > 0 and abs(x) > 0.55, hzm),                                         # corner lamps blink amber
                      (lambda x, y, z: y > 0, mat_emit("MORE_taillens", (1.0, 0.03, 0.02), 3.0))])  # running tails, dim
    haz = []
    for sx in (-0.80, 0.80):        # spill on the bumper / road from each corner (real sources)
        for sy, z in ((2.30, 0.86), (-2.25, 0.70)):
            haz.append(light(f"MORE_haz_{sx}_{sy}", "POINT", (sx * 1.02, sy, z), 0, amber, size=0.06, parent=ROOT, coll=COL))
    em = next(n for n in hzm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Emission Strength"]
    for m in range(MA - 2, MB + 3):   # 8 frames on / 8 off (1.5 Hz), on at the cut
        on = ((m - MA) // 8) % 2 == 0; f = m + OFF
        for L in haz: key_const(L.data, "energy", f, 35.0 if on else 0.0)
        em.default_value = 40.0 if on else 0.0; em.keyframe_insert("default_value", frame=f)
    for L in haz: const_interp(L.data)
    const_interp(hzm.node_tree)
    RM = ROOT.matrix_world.copy()
    def wl(v): return RM @ Vector(v)     # car-local -> world (rear is +y local)
    PLATE = (0.0, 2.27, 0.45)
    if FMT == "169":
        camo = new_cam("CAM_more_posted", 40)
        S0, S1 = (2.3, 7.4, 1.05), (0.12, 3.95, 0.62)      # rear 3/4 (car's right side, caliper) -> square on the plate
        T0, T1 = (0.15, 0.6, 0.62), PLATE
    else:
        camo = new_cam("CAM_more_posted", 30)
        S0, S1 = (2.0, 8.6, 1.25), (0.10, 3.75, 0.66)
        T0, T1 = (0.10, 0.6, 0.72), PLATE
    def pose(m):
        k = ss((m - MA) / (5694 - MA))
        loc = Vector(S0).lerp(Vector(S1), k); tg = Vector(T0).lerp(Vector(T1), k)
        return (wl(loc), wl(tg), 0.0)
    key_cam(camo, range(MA - 1, MB + 2), pose)

sc.camera = camo
if os.environ.get("CAR_POST_HOOK"):   # rr_car (Sat Nov 7): render-time hook (light pass / glowfix), unset = unchanged
    os.environ["RR_RANGE"] = f"{MA + OFF},{MB + OFF}"; exec(open(os.environ["CAR_POST_HOOK"]).read())
check(camo, roots, BEAT)
if os.environ.get("DRY"): print("DRY done"); sys.exit(0)

r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"
if MODE == "stills":
    r.image_settings.color_depth = "8"
    for m in STILLS:
        sc.frame_set(m + OFF); r.filepath = os.path.join(OUT, f"{BEAT}_{FMT}_{m}.png")
        bpy.ops.render.render(write_still=True); print("[still]", r.filepath, flush=True)
    sys.exit(0)
r.image_settings.color_depth = "16"
for p in glob.glob(os.path.join(OUT, "b_*.png")): os.remove(p)
todo = [m for m in range(MA, MB + 1) if not (os.path.exists(os.path.join(OUT, f"f_{m:04d}.png")) and os.path.getsize(os.path.join(OUT, f"f_{m:04d}.png")) > 0)]
if not todo: print("[final] nothing to do"); sys.exit(0)
sc.frame_start, sc.frame_end = todo[0] + OFF, todo[-1] + OFF
r.filepath = os.path.join(OUT, "b_####"); r.use_file_extension = True; r.use_overwrite = True; r.use_placeholder = False
T = {}
def pre(scene, *a): T["t"] = time.time()
def post(scene, *a):
    sj = os.path.join(OUT, "sec.json"); S = json.load(open(sj)) if os.path.exists(sj) else {}
    S[str(scene.frame_current - OFF)] = round(time.time() - T["t"], 2); json.dump(S, open(sj, "w"))
    print("[final]", scene.frame_current - OFF, S[str(scene.frame_current - OFF)], "s", flush=True)
bpy.app.handlers.render_pre.append(pre); bpy.app.handlers.render_post.append(post)
t0 = time.time(); bpy.ops.render.render(animation=True)
n = 0
for m in todo:
    p = os.path.join(OUT, f"b_{m + OFF:04d}.png")
    if os.path.exists(p): os.replace(p, os.path.join(OUT, f"f_{m:04d}.png")); n += 1
print("[final] done", n, "frames", round(time.time() - t0, 1), "s", flush=True)
