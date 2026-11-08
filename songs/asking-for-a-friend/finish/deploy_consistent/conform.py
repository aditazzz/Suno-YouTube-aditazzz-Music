"""deploy_consistent (Sun Nov 8): ONE DEPLOY button across the film. Her words: "the deploy button is inconsistent across scenes".
Master design = S133's DEPLOY lamp as approved (followups_fix S133 recipe on outro_lobby_look_setsfix.blend's dl_* objects):
green dome on a dark round base, a light matte plaque, DEPLOY in near-black InterDisplay Black, dome lit mid green (emission
0.65, frosted view-angle falloff), its own green point light at 0.4x. This file appends that object into another set, applies the
same recipe, hides the old key and lands Claude's finger on the dome. exec() it in a loaded scene before render3; never saves.

env SHOT = S038 | S074 | S075, CONFORM_SCALE (lamp scale vs S133; S038 1.0: Claude is the same size in both sets),
    PLAQUE_FACE = cam (default: the plaque faces the shot camera).
"""
import bpy, os, math
from mathutils import Matrix, Vector

SHOT_ = os.environ["SHOT"]
O_ = bpy.data.objects
sc_ = bpy.context.scene
LOBBY = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender/finish/outro_lobby_look_setsfix.blend")
FONTS_ = os.environ.get("STUDIO_FONTS", "assets/fonts")   # the studio fonts (repo root assets/fonts)
PARTS = ["dl_base", "dl_green", "dl_plq", "dl_txt", "dl_glow"]
clog = []


def _bsdf(m):
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def _matte(m, base, rough):
    b = _bsdf(m)
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Emission Strength"].default_value = 0.0
    for nm in ("Specular IOR Level", "Coat Weight", "Sheen Weight"):
        if nm in b.inputs: b.inputs[nm].default_value = 0.0


def _own(ob, name):
    m = ob.material_slots[0].material.copy(); m.name = name; ob.material_slots[0].material = m; return m


def _green_dome(m, strength=0.65, color=(0.02, 0.85, 0.16)):
    """S133 final: glowfix lobby frosted falloff (Facing -> x1.0 .. x0.4) times followups' 0.65 saturated green."""
    nt = m.node_tree
    if nt.animation_data: nt.animation_data_clear()
    em = next(n for n in nt.nodes if n.type == "EMISSION")
    em.inputs["Color"].default_value = (*color, 1)
    s = em.inputs["Strength"]
    for l in list(nt.links):
        if l.to_socket == s: nt.links.remove(l)
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"; mul.inputs[1].default_value = -0.6; mul.inputs[2].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], mul.inputs[0])
    k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = strength
    nt.links.new(mul.outputs[0], k.inputs[0]); nt.links.new(k.outputs[0], s)


def append_master():
    with bpy.data.libraries.load(LOBBY, link=False) as (src, dst):
        dst.objects = [n for n in PARTS if n in src.objects]
    got = {}
    for ob in dst.objects:
        sc_.collection.objects.link(ob)
        base = ob.name.split(".")[0] if ob.name.split(".")[0] in PARTS else ob.name
        got[base] = ob
        if ob.animation_data: ob.animation_data_clear()
        if ob.type == "LIGHT" and ob.data.animation_data: ob.data.animation_data_clear()
        ob.hide_render = False; ob.hide_viewport = False
    missing = [n for n in PARTS if n not in got]
    assert not missing, f"master lamp parts missing: {missing}"
    # --- the S133 recipe, in the lobby's own frame (plaque on the base's -Y side, read from -Y) ---
    g = got["dl_green"]; gm = _own(g, "dc_dl_green"); _green_dome(gm)
    plq, txt = got["dl_plq"], got["dl_txt"]
    k = 1.25; h0 = plq.dimensions.z
    plq.scale = (plq.scale.x * k, plq.scale.y, plq.scale.z * k)
    bpy.context.view_layer.update(); plq.location.z += (plq.dimensions.z - h0) / 2
    _matte(_own(plq, "dc_dl_plaque"), (0.42, 0.42, 0.38), 0.7)
    txt.data = txt.data.copy()
    txt.data.font = bpy.data.fonts.load(os.path.join(FONTS_, "InterDisplay-Black.otf"), check_existing=True)
    txt.data.align_x = "CENTER"; txt.data.align_y = "CENTER"
    bpy.context.view_layer.update()
    s = min(0.76 * plq.dimensions.x / txt.dimensions.x, 0.6 * plq.dimensions.z / txt.dimensions.y)
    txt.scale = (txt.scale.x * s, txt.scale.y * s, txt.scale.z)
    bpy.context.view_layer.update()
    pc = sum((plq.matrix_world @ Vector(v) for v in plq.bound_box), Vector()) / 8
    tc = sum((txt.matrix_world @ Vector(v) for v in txt.bound_box), Vector()) / 8
    nrm = Vector((0, -1, 0))
    face = pc + nrm * (plq.dimensions.y / 2 + 0.002)
    txt.matrix_world = Matrix.Translation(face - tc) @ txt.matrix_world
    _matte(_own(txt, "dc_dl_ink"), (0.006, 0.008, 0.007), 1.0)
    L = got["dl_glow"].data = got["dl_glow"].data.copy()
    L.energy = 25.0 * 0.4; L.color = (0.1, 1.0, 0.3)
    # --- one rig: an empty at the base's bottom centre ---
    bpy.context.view_layer.update()
    bb = [got["dl_base"].matrix_world @ Vector(v) for v in got["dl_base"].bound_box]
    piv = Vector((sum(v.x for v in bb) / 8, sum(v.y for v in bb) / 8, min(v.z for v in bb)))
    e = bpy.data.objects.new("DC_DEPLOY", None); sc_.collection.objects.link(e); e.location = piv
    bpy.context.view_layer.update()
    for ob in got.values():
        mw = ob.matrix_world.copy(); ob.parent = e; ob.matrix_parent_inverse = e.matrix_world.inverted(); ob.matrix_world = mw
    clog.append(f"master lamp appended ({', '.join(o.name for o in got.values())}), plaque x1.25, legend {tuple(round(v, 3) for v in txt.dimensions)}")
    return e, got


def shot_cam(fm):
    sc_.frame_set(fm + 1); cam = sc_.camera
    for mk in sorted(sc_.timeline_markers, key=lambda m_: m_.frame):
        if mk.frame <= fm + 1 and mk.camera: cam = mk.camera
    return cam


def place(e, got, loc, s, cam):
    """base bottom centre at loc, uniform scale s, plaque (local -Y) turned toward the camera."""
    d = cam.matrix_world.translation - Vector(loc)
    th = math.atan2(d.y, d.x) + math.pi / 2 + math.radians(float(os.environ.get("PLAQUE_YAW", 0.0)))   # yaw: swing the plaque out from behind an arm
    e.location = loc; e.rotation_euler = (0, 0, th); e.scale = (s, s, s)
    got["dl_glow"].data.energy *= s * s
    bpy.context.view_layer.update()


def zmin_of(ob):
    return min((ob.matrix_world @ Vector(v)).z for v in ob.bound_box)


def top_of(ob):
    return max((ob.matrix_world @ Vector(v)).z for v in ob.bound_box)


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


if SHOT_ == "S038":
    S = float(os.environ.get("CONFORM_SCALE", 1.0))
    for n in ("dp_button", "dp_bezel", "dp_label"):
        O_[n].hide_render = True; O_[n].hide_viewport = True
    O_["DP_glow"].data.energy = 0.0
    e, got = append_master()
    tip = O_["index_dist_R"]
    # where the finger rests (master 1566-1586): the dome goes right under it, on the console top
    pts = []
    for fm in range(1566, 1587, 2):
        sc_.frame_set(fm + 1); mw = tip.matrix_world
        pts.append(sum((mw @ Vector(v) for v in tip.bound_box), Vector()) / 8)
    cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
    ztop = max((O_["dp_top"].matrix_world @ Vector(v)).z for v in O_["dp_top"].bound_box)
    # SHIFT_R: slide the lamp toward camera-right (m) so Claude's arm doesn't cover the plaque; the hand follows it (below)
    SHR = float(os.environ.get("SHIFT_R", 0.0))
    cr = shot_cam(1560).matrix_world.to_3x3() @ Vector((1, 0, 0)); cr.z = 0; cr.normalize()
    shv = cr * SHR
    place(e, got, (cx + shv.x, cy + shv.y, ztop), S, shot_cam(1560))
    dome_top = top_of(got["dl_green"])
    # raise the IK hand target so the fingertip lands ON the dome (it was keyed for a 3 cm key): bake per frame
    rig = O_["RIG_Claude"]; pb = rig.pose.bones["CTRL_hand_R"]
    act = rig.animation_data.action
    try:
        fcs = list(act.fcurves)
    except Exception:
        fcs = [fc for ly in act.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
    loc_fc = {fc.array_index: fc for fc in fcs if fc.data_path == 'pose.bones["CTRL_hand_R"].location'}
    key_top = top_of(O_["dp_button"])   # the approved key's face (screens_fix scales it in x/y only)
    lift = dome_top - key_top
    gb = got["dl_green"]; gbb = [gb.matrix_world @ Vector(v) for v in gb.bound_box]
    gcx = sum(v.x for v in gbb) / 8; gcy = sum(v.y for v in gbb) / 8
    rxy = (max(v.x for v in gbb) - min(v.x for v in gbb)) / 2; rz = (dome_top - top_of(got["dl_base"]))
    CLEAR = float(os.environ.get("CLEAR", 0.001)); FR_ = 0.0125   # fingertip radius (index_dist_R 2.5 cm)

    def surface(x, y):   # the dome's (ellipsoid cap) height under a point; base top outside it
        d = math.hypot(x - gcx, y - gcy) - FR_ * float(os.environ.get("FR_K", 0.5))
        if d >= rxy: return top_of(got["dl_base"])
        d = max(d, 0.0); return dome_top - rz * (1 - math.sqrt(max(0.0, 1 - (d / rxy) ** 2)))
    A0, A1 = int(os.environ.get("RAMP_IN0", 1531)), int(os.environ.get("RAMP_IN1", 1546))
    B0, B1 = int(os.environ.get("RAMP_OUT0", 1596)), int(os.environ.get("RAMP_OUT1", 1606))
    R = (rig.matrix_world.to_3x3() @ pb.bone.matrix_local.to_3x3())
    par = pb.parent
    if par is not None:
        R = rig.matrix_world.to_3x3() @ par.matrix.to_3x3() @ (par.bone.matrix_local.to_3x3().inverted() @ pb.bone.matrix_local.to_3x3())
    dl = R.inverted() @ Vector((0, 0, 1))
    dlat = R.inverted() @ shv   # the lateral follow, in the hand target's own space
    frames = list(range(A0 + 1, B1 + 2))   # blend frames
    base = {f: [loc_fc[i].evaluate(f) for i in range(3)] for f in frames}
    orig = {}; oxy = {}
    for f in frames:
        sc_.frame_set(f); orig[f] = zmin_of(tip)
        mw = tip.matrix_world; c0 = sum((mw @ Vector(v) for v in tip.bound_box), Vector()) / 8; oxy[f] = (c0.x, c0.y)
    for f in frames:   # key every frame first (so each frame evaluates exactly its own key)
        for i in range(3): loc_fc[i].keyframe_points.insert(f, base[f][i], options={"FAST"})
    for fc in loc_fc.values(): fc.update()
    res = []
    Rinv = R.inverted()
    from mathutils.bvhtree import BVHTree
    import re as _re
    HAND = [o for o in O_ if o.type == "MESH" and _re.search(r"(thumb|index|middle|ring|pinky|palm|hand|finger)", o.name, _re.I) and o.name.endswith("_R")]
    def wbvh(ob, dg):   # world-space BVH of the evaluated mesh (FromObject alone is object-local)
        ev_ = ob.evaluated_get(dg); me = ev_.to_mesh(); mw = ev_.matrix_world
        t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(pl.vertices) for pl in me.polygons])
        ev_.to_mesh_clear(); return t
    _dg = bpy.context.evaluated_depsgraph_get()
    LAMP_BVH = [wbvh(got[n], _dg) for n in ("dl_green", "dl_base", "dl_plq")]
    bvh_lift = []
    for f in frames:
        fm = f - 1
        w = smooth((fm - A0) / max(1, A1 - A0)) if fm < A1 else (1.0 - smooth((fm - B0) / max(1, B1 - B0)) if fm > B0 else 1.0)
        if A0 <= fm <= A1: w = max(w, 0.3)
        Ub = dl * (lift * w) + dlat * w   # bone-space offset of the hand target, solved in x, y and z together
        tx, ty = oxy[f][0] + shv.x * w, oxy[f][1] + shv.y * w
        best = None
        for it in range(12):
            for i in range(3): loc_fc[i].keyframe_points.insert(f, base[f][i] + Ub[i], options={"FAST", "REPLACE"})
            for fc in loc_fc.values(): fc.update()
            sc_.frame_set(f)
            mw = tip.matrix_world; c = sum((mw @ Vector(v) for v in tip.bound_box), Vector()) / 8; z = zmin_of(tip)
            want = orig[f] + lift * w
            if math.hypot(c.x - gcx, c.y - gcy) < rxy + FR_: want = max(want, surface(c.x, c.y) + CLEAR)   # never into the dome
            ev = Vector((tx - c.x, ty - c.y, want - z))
            # z must be met (no penetration, finger on the dome); xy is best effort (the arm's reach)
            sc = (max(ev.z, 0.0) * 50 + max(-ev.z, 0.0) * 3) + ev.xy.length   # below the surface is never acceptable
            if best is None or sc < best[0]: best = (sc, Ub.copy(), c.copy(), z, want)
            if ev.length < 0.002: break
            Ub = Ub + Rinv @ (ev * 0.7)
        sc, Ub, c, z, want = best
        for i in range(3): loc_fc[i].keyframe_points.insert(f, base[f][i] + Ub[i], options={"FAST", "REPLACE"})
        for fc in loc_fc.values(): fc.update()
        # exact check: no hand mesh may overlap the dome/base/plaque (BVH); lift the hand target 3 mm at a time until clear
        for k in range(25):
            sc_.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            hits = [(h.name, j) for h in HAND for j, bv in enumerate(LAMP_BVH) if wbvh(h, dg).overlap(bv)]
            if os.environ.get("DC_BVHDBG") and k == 0 and fm in (1531, 1545, 1566, 1580): print("[bvhdbg]", fm, hits, flush=True)
            if not hits: break
            Ub = Ub + Rinv @ Vector((0, 0, 0.003))
            for i in range(3): loc_fc[i].keyframe_points.insert(f, base[f][i] + Ub[i], options={"FAST", "REPLACE"})
            for fc in loc_fc.values(): fc.update()
        if k: bvh_lift.append((fm, round(0.003 * k, 3)))
        sc_.frame_set(f); z = zmin_of(tip)
        u = Ub.length
        res.append((fm, round(z, 3), round(want, 3), round(u, 3), round((Vector((tx, ty)) - Vector((c.x, c.y))).length, 3)))
    worst = max(res, key=lambda r: abs(r[1] - r[2]))
    lows2 = [r[1] for r in res if 1562 <= r[0] <= 1591]
    dz = max(r[3] for r in res)
    if os.environ.get("DC_DUMP"): print("[conform] solve (master f, tip zmin, want, u):", res, flush=True)
    clog.append(f"S038 hand meshes checked {len(HAND)}; BVH lifts (f, m) {bvh_lift}")
    clog.append(f"S038: dp_* hidden, lamp at ({cx:.3f},{cy:.3f},{ztop:.3f}) x{S}, dome top {dome_top:.3f}; hand target up to +{dz:.3f} m (lift {lift:.3f} over the old key face {key_top:.3f}; "
                f"ramp {A0}-{A1}, out {B0}-{B1}); tip zmin 1562-1591 now {min(lows2):.3f}..{max(lows2):.3f}; worst solve {worst}")

elif SHOT_ in ("S074", "S075"):
    S = float(os.environ.get("CONFORM_SCALE", 2.7))
    key = O_["kb_deploy"]
    sc_.frame_set(2823)
    key_top0 = top_of(key); key_c = key.matrix_world.translation.copy()
    kz0 = key.matrix_world.translation.z
    for n in ("kb_deploy", "kb_dt"):
        O_[n].hide_render = True; O_[n].hide_viewport = True
    e, got = append_master()
    plane = min((key.matrix_world @ Vector(v)).z for v in key.bound_box)
    DX = float(os.environ.get("CONFORM_DX", 0.12)); FDX = float(os.environ.get("FINGER_DX", -0.07))
    DY = float(os.environ.get("CONFORM_DY", 0.0))
    place(e, got, (key_c.x + DX, key_c.y + DY, plane), S, shot_cam(2840))
    dome_top = top_of(got["dl_green"])
    # the lamp is mounted IN the keyboard: hide every keycap its footprint (base, plaque) would cut through
    MG = float(os.environ.get("KEY_MARGIN", 0.01)); hid = []
    fp = []
    for n in ("dl_base", "dl_plq", "dl_green"):
        bb = [got[n].matrix_world @ Vector(v) for v in got[n].bound_box]
        fp.append((min(v.x for v in bb) - MG, max(v.x for v in bb) + MG, min(v.y for v in bb) - MG, max(v.y for v in bb) + MG))
    for ob in list(O_):
        if not ob.name.startswith("kb_k") or ob.type != "MESH": continue
        kb = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
        kx0, kx1 = min(v.x for v in kb), max(v.x for v in kb); ky0, ky1 = min(v.y for v in kb), max(v.y for v in kb)
        if any(kx0 < x1 and kx1 > x0 and ky0 < y1 and ky1 > y0 for x0, x1, y0, y1 in fp):
            ob.hide_render = True; ob.hide_viewport = True; hid.append(ob.name)
    clog.append(f"keys hidden under the lamp: {hid}; lamp footprint {[tuple(round(v, 3) for v in f) for f in fp]}")
    dz0 = dome_top - key_top0 + float(os.environ.get("CLEAR", 0.0))
    # the press: the dome rides the old key's travel (same frames, same depth); the finger rides up by dz0 throughout
    fin = O_["kb_finger"]
    try:
        ffc = [fc for fc in fin.animation_data.action.fcurves if fc.data_path == "location" and fc.array_index == 2]
    except Exception:
        ffc = [fc for ly in fin.animation_data.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves
               if fc.data_path == "location" and fc.array_index == 2]
    for fc in ffc:
        for kp in fc.keyframe_points:
            kp.co[1] += dz0; kp.handle_left[1] += dz0; kp.handle_right[1] += dz0
        fc.update()
    if fin.animation_data and fin.animation_data.action and any(True for _ in [0]):
        try:
            xfc = [fc for fc in fin.animation_data.action.fcurves if fc.data_path == "location" and fc.array_index == 0]
        except Exception:
            xfc = [fc for ly in fin.animation_data.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves
                   if fc.data_path == "location" and fc.array_index == 0]
        if xfc:
            for fc in xfc:
                for kp in fc.keyframe_points:
                    kp.co[1] += FDX; kp.handle_left[1] += FDX; kp.handle_right[1] += FDX
                fc.update()
        else:
            fin.location.x += FDX
    # dome press: follow kb_deploy's own z travel (driver-free: bake a z key per frame on the empty)
    e0 = e.location.z
    for f in range(2593, 3198):
        sc_.frame_set(f)
        dzk = key.matrix_world.translation.z - kz0
        e.location.z = e0 + dzk
        e.keyframe_insert("location", index=2, frame=f)
    sc_.frame_set(2823)
    clog.append(f"{SHOT_}: kb_deploy/kb_dt hidden, lamp x{S} at ({key_c.x + DX:.3f},{key_c.y:.3f},{plane:.3f}), finger dx {FDX}, dome top {dome_top:.3f}; "
                f"finger +{dz0:.3f} m; dome rides the key's press travel; dl_glow {got['dl_glow'].data.energy:.1f} W")

if os.environ.get("CAM_FIT"):   # native 9:16 renders: the shot camera's sensor fit (AUTO = the long side keeps the 16:9 width's FOV)
    for c_ in bpy.data.cameras: c_.sensor_fit = os.environ["CAM_FIT"]
    clog.append(f"cameras sensor_fit {os.environ['CAM_FIT']}")
print("[conform] " + " | ".join(clog), flush=True)
