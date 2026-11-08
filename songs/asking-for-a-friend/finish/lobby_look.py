"""LOBBY / SERVER ROOM / HALL look (finish_3): port of the approved look (LOCK12 blends) onto master v1's blends.
Cameras, characters and their animation stay master v1's. Saves a COPY (never the input).

  Blender -b <master v1 blend> --python lobby_look.py -- <mode> <out.blend>
  mode: intro  (aff_01_intro_v3 -> act1_lobby_look.blend)
        outro  (aff_09_outro_lobby -> outro_lobby_look.blend)
        server (aff_02_verse1_v3 -> preC1_serverroom_look.blend)
        hall   (aff_07_memoir -> memoir_lobby_look.blend)  [HALL set re-lit, S100/101]
The LOCK12 sets are appended (not hand-copied): collections, materials, lights, world, eevee + colour settings.
"""
import bpy, os, sys, json, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")
SHORT = os.path.expanduser("~/Studio/asking-for-a-friend/blender/short")
SRC_S1 = os.path.join(SHORT, "short169_S1_LOCK12.blend")
SRC_S2 = os.path.join(SHORT, "short169_S2_LOCK12b.blend")
DOCS = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender")
sc = bpy.context.scene
args = sys.argv[sys.argv.index("--") + 1:]
MODE, OUT = args[0], args[1]
OD = {"S1": json.load(open(os.path.join(LOGS, "od_l12.json"))), "S2": json.load(open(os.path.join(LOGS, "od_s2.json")))}


def has_anim(o):
    return bool(o.animation_data and o.animation_data.action)


def transplant(src, key, drop_colls, bring_colls, keep_fn):
    od = OD[key]
    for m in bpy.data.materials:
        if not m.name.startswith("v1_"): m.name = "v1_" + m.name
    drop, keep = [], []
    for c in drop_colls:
        for o in list(bpy.data.collections[c].objects):
            if o.type == "LIGHT": drop.append(o)
            else: (keep if keep_fn(o) else drop).append(o)
    dropn = {o.name for o in drop}
    reparent = [(o.name, o.parent.name, o.parent_type, o.parent_bone, o.matrix_parent_inverse.copy()) for o in bpy.data.objects if o.parent and o.parent.name in dropn and o not in drop]
    keepn = {o.name: o for o in keep}
    for n, o in keepn.items(): o.name = "KEEP__" + n
    for o in drop: bpy.data.objects.remove(o, do_unlink=True)
    for c in drop_colls:                                    # kept objects stay in the (now otherwise empty) old collection
        pass
    with bpy.data.libraries.load(src, link=False) as (s, d):
        d.collections = [c for c in bring_colls if c in s.collections]
        d.materials = list(s.materials)
        d.worlds = list(s.worlds)
        d.objects = [n for n in s.objects if n == "L_rcp_face"]
    for c in d.collections: sc.collection.children.link(c)
    for o in d.objects:
        if o and o.name not in sc.collection.objects: sc.collection.objects.link(o)
    # twins: the source copy of a kept object is removed after its materials went onto ours
    nt = 0
    for n, o in keepn.items():
        tw = bpy.data.objects.get(n)
        if tw is not None and tw is not o:
            if len(tw.material_slots) == len(o.material_slots):
                for i, sl in enumerate(tw.material_slots): o.material_slots[i].material = sl.material
            bpy.data.objects.remove(tw, do_unlink=True); nt += 1
        o.name = n
    # reparent kept children whose parent was a set object
    for cn, pn, pt, pb, inv in reparent:
        c, p = bpy.data.objects.get(cn), bpy.data.objects.get(pn)
        if c and p: c.parent = p; c.parent_type = pt; c.matrix_parent_inverse = inv
        else: print("[look] WARN lost parent", cn, pn)
    # same-named base objects outside the set (receptionist, Claude, ...) get the approved materials
    na = 0
    for o in bpy.data.objects:
        if o.name in od and od[o.name]["mats"] and len(o.material_slots) == len(od[o.name]["mats"]) and o.type == "MESH" and not o.name.startswith("KEEP"):
            ms = [bpy.data.materials.get(m) if m else None for m in od[o.name]["mats"]]
            if all(m is not None or n is None for m, n in zip(ms, od[o.name]["mats"])):
                for i, m in enumerate(ms):
                    if o.material_slots[i].material is not m: o.material_slots[i].material = m; na += 1
    print(f"[look] dropped {len(drop)}, kept {len(keep)}, twins {nt}, material swaps outside the set {na}")


def finish_scene(src):
    """Scene settings from the approved blend (eevee), Filmic + Medium Contrast, linear EXR out; the approved world."""
    with bpy.data.libraries.load(src, link=False) as (s, d):
        d.scenes = [s.scenes[0]]
    ss = d.scenes[0]
    for k in dir(sc.eevee):
        if k.startswith(("_", "bl_", "rna")) or k in ("ray_tracing_options",): continue
        try: setattr(sc.eevee, k, getattr(ss.eevee, k))
        except Exception: pass
    for k in dir(sc.eevee.ray_tracing_options):
        if k.startswith(("_", "bl_", "rna")): continue
        try: setattr(sc.eevee.ray_tracing_options, k, getattr(ss.eevee.ray_tracing_options, k))
        except Exception: pass
    sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium Contrast"; sc.view_settings.exposure = 0.0
    sc.display_settings.display_device = "sRGB"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.render.use_motion_blur = ss.render.use_motion_blur
    w = ss.world
    if w: sc.world = bpy.data.worlds.get(w.name) or sc.world
    bpy.data.scenes.remove(ss)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def lobby_common():
    transplant(SRC_S1, "S1", ["LOBBY", "PROPS"],
               ["LOBBY", "PROPS", "LIGHTS_lobby", "SET_lobby_new", "SHORT_SET_lobby", "LL_board_skips", "LL_grazer_skips", "LL_wash_only"],
               lambda o: o.type == "CAMERA")
    finish_scene(SRC_S1)
    # the founder is never 3D footage again
    for o in bpy.data.objects:
        if any(c.name == "FOUNDER" for c in o.users_collection): o.hide_render = True
    # the receptionist's hover light is v1's; the approved face light replaces it
    if "RCP_hover" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects["RCP_hover"], do_unlink=True)
    f = bpy.data.objects.get("L_rcp_face"); p = bpy.data.objects.get("rcp_facescreen")
    if f and p:
        f.parent = p; f.location = (0, -0.05, 0); f.rotation_euler = (0, 0, 0)


if MODE in ("intro", "outro"):
    lobby_common()
elif MODE == "server":
    KEEP = {"srv_floor", "mug", "clock_body", "clock_face"}
    srvod = OD["S2"]
    transplant(SRC_S2, "S2", ["SERVER"], ["SERVER", "LIGHTS_server", "SET_server_new", "SHORT_SET_server"],
               lambda o: o.type == "CAMERA" or has_anim(o) or o.name in KEEP or o.name not in srvod)
    finish_scene(SRC_S2)
    for o in bpy.data.objects:
        if any(c.name == "FOUNDER" for c in o.users_collection): o.hide_render = True



# ---------------------------------------------------------------- shared lobby pieces
TEX = os.path.join(DOCS, "textures", "screens", "ns")
KIT = os.path.join(HERE, "kit2d", "stills", "F30.png")


def emis_tex_mat(name, path, strength, interp="Linear", ext="CLIP"):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    N = nt.nodes.new; L = nt.links.new
    out = N("ShaderNodeOutputMaterial"); bs = N("ShaderNodeBsdfPrincipled"); t = N("ShaderNodeTexImage")
    tc = N("ShaderNodeTexCoord"); mp = N("ShaderNodeMapping")
    t.image = bpy.data.images.load(path, check_existing=True); t.interpolation = interp; t.extension = ext
    L(tc.outputs["UV"], mp.inputs["Vector"]); L(mp.outputs["Vector"], t.inputs["Vector"])
    bs.inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1); bs.inputs["Roughness"].default_value = 0.5
    if "Specular IOR Level" in bs.inputs: bs.inputs["Specular IOR Level"].default_value = 0.15
    L(t.outputs["Color"], bs.inputs["Emission Color"]); bs.inputs["Emission Strength"].default_value = strength
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    return m, mp


def key_vec(mp, f, v, const=True):
    sock = mp.inputs["Location"]; sock.default_value = v; sock.keyframe_insert("default_value", frame=f)


def set_interp(idb, kind):
    ad = idb.animation_data
    if ad and ad.action:
        for lay in ad.action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for k in fc.keyframe_points: k.interpolation = kind


def plane(name, loc, w, h, mat, coll, rot=(math.pi / 2, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for lp, (u, v) in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[lp.index].uv = (u, v)
    me.update(); ob = bpy.data.objects.new(name, me); ob.location = loc; ob.rotation_euler = rot
    ob.data.materials.append(mat); coll.objects.link(ob); return ob


def flip_states(mp, frames_to_state, fps_off):
    """key the atlas window: state index i -> column i%4, row i//4 (row 0 = top)."""
    for f, i in frames_to_state:
        key_vec(mp, f + fps_off, (0.00025 + (i % 4) / 4, 0.00025 + (2 - i // 4) / 3, 0))
    set_interp(mp.id_data, "CONSTANT")


def board_ns(flips, ticker_keys=((1, 'press'),), ticker_on=True):
    """NOW SERVING board in the world (company voice). flips: [(master_frame, atlas_state)], blend frame = master + 1."""
    LB = bpy.data.collections.get("LOBBY.001") or bpy.data.collections.get("LOBBY")
    for n in ("queue_lbl", "queue_999", "queue_1000", "ticker"):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    qs = bpy.data.objects.get("queue_screen")
    if qs:                                                           # the dark bezel behind the new face
        bm = bpy.data.materials.new("ns_bezel"); bm.use_nodes = True
        b = next(n for n in bm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (0.02, 0.022, 0.024, 1); b.inputs["Roughness"].default_value = 0.4; b.inputs["Metallic"].default_value = 0.7
        qs.data.materials.clear(); qs.data.materials.append(bm)
    m, mp = emis_tex_mat("ns_board_face", os.path.join(TEX, "ns_atlas.png"), 0.45)
    mp.inputs["Scale"].default_value = (0.9995 / 4, 0.9995 / 3, 1)
    coll = bpy.data.collections["SET_lobby_new"] if "SET_lobby_new" in bpy.data.collections else sc.collection
    face = plane("ns_face", (5.0, 4.935, 2.9), 2.14, 1.2, m, coll)
    flips = sorted(flips); first = flips[0][1]
    key_vec(mp, 1, (0.00025 + (first % 4) / 4, 0.00025 + (2 - first // 4) / 3, 0))
    flip_states(mp, flips, 1)
    if ticker_on:
        tm, tmp = emis_tex_mat("ns_ticker_mat", os.path.join(TEX, "ns_ticker.png"), 0.45, ext="REPEAT")
        tmp.inputs["Scale"].default_value = (2140 / 5280, 1, 1)
        tk = plane("ns_ticker", (5.0, 4.935, 2.115), 2.14, 0.22, tm, coll)
        meta = json.load(open(os.path.join(TEX, "ns_ticker.json")))
        U = {"wait": 0.0, "press": ((meta["press_x0"] + meta["press_x1"]) / 2 - 1070) / meta["tw"]}
        for f, st in ticker_keys: key_vec(tmp, f, (U[st], 0, 0))
        set_interp(tmp.id_data, "BEZIER")
    # the board is a screen: a real light on the queue (area, facing the room), sized to the panel
    ld = bpy.data.lights.new("L_ns_board", "AREA"); ld.shape = "RECTANGLE"; ld.size = 2.14; ld.size_y = 1.2
    ld.color = (0.75, 1.0, 0.88); ld.energy = float(os.environ.get("NS_LIGHT", 160))
    lo = bpy.data.objects.new("L_ns_board", ld); lo.location = (5.0, 4.90, 2.9); lo.rotation_euler = (-math.pi / 2, 0, 0)
    sc.collection.objects.link(lo)
    return face


def portraits():
    """S004: the portrait wall's prism: 3 neutral placeholders (F30 on THE VISIONARY once finish_4 delivers it)."""
    o = bpy.data.objects.get("portrait_prism")
    if not o: return
    srcs = [KIT if os.path.exists(KIT) else os.path.join(TEX, "ph_portrait_visionary.png"),
            os.path.join(TEX, "ph_portrait_wellness.png"), os.path.join(TEX, "ph_portrait_finance.png")]
    mats = []
    for i, p in enumerate(srcs):
        m = bpy.data.materials.new(f"PT_{('visionary','wellness','finance')[i]}_L"); m.use_nodes = True; nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(p, check_existing=True)
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 0.06; b.inputs["Roughness"].default_value = 0.4
        mats.append(m)
    gold = bpy.data.materials.new("PT_frame_brass"); gold.use_nodes = True
    g = next(n for n in gold.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    g.inputs["Base Color"].default_value = (0.8, 0.55, 0.28, 1); g.inputs["Metallic"].default_value = 1.0; g.inputs["Roughness"].default_value = 0.35
    for i, m in enumerate(mats + [gold]):
        if i < len(o.material_slots): o.material_slots[i].material = m
    # a picture light on the wall above it (a real, visible fixture)
    br = bpy.data.materials.get("PT_frame_brass")
    me = bpy.data.meshes.new("pic_light_bar"); import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    bar = bpy.data.objects.new("pic_light_bar", me); bar.scale = (0.9, 0.08, 0.04); bar.location = (0, 4.95, 4.35); bar.data.materials.append(br)
    sc.collection.objects.link(bar)
    ld = bpy.data.lights.new("L_pic_light", "SPOT"); ld.energy = float(os.environ.get("PIC_LIGHT", 160)); ld.spot_size = math.radians(70); ld.spot_blend = 0.8
    ld.color = (1.0, 0.82, 0.58); ld.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("L_pic_light", ld); lo.location = (0, 4.78, 4.33); sc.collection.objects.link(lo)
    lo.rotation_euler = (Vector((0, 4.35, 3.3)) - lo.location).to_track_quat("-Z", "Y").to_euler()


def board_seq_hold():
    """the ALL SYSTEMS board: hold its first image before f366 (the sequence only exists for f366-572)."""
    for m in bpy.data.materials:
        if m.name == "AFF_board" and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image and n.image.source == "SEQUENCE":
                    n.image.source = "FILE"                       # a single still: the first board image (ALL SYSTEMS, 19 C)

def gain_lights(pairs):
    """wide lobby shots need ~2x the approved set's light to meet the exposure numbers; the S005 close-up (cut-matched to the
    finished f366) keeps the approved 1.0. pw_gain is keyed per shot (constant)."""
    prop_key("pw_gain", pairs)
    n = 0
    for o in bpy.data.objects:
        if o.type == "LIGHT" and not o.hide_render and o.data.energy > 0 and not (o.data.animation_data and o.data.animation_data.action) and o.name not in ("L_rcp_face",):
            if o.data.animation_data and o.data.animation_data.drivers: continue
            drv_scene_prop(o.data, "energy", o.data.energy, ["pw_gain"]); n += 1
    print("[look] gain drivers on", n, "lights")


def new_cam(name, loc, target, lens, dof=False):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = 0.05; cd.clip_end = 200
    co = bpy.data.objects.new(name, cd); co.location = loc; sc.collection.objects.link(co)
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cd.dof.use_dof = dof; return co


def set_marker(name, frame, cam):
    for m in sc.timeline_markers:
        if m.name == name: m.frame = frame; m.camera = cam; return m
    m = sc.timeline_markers.new(name, frame=frame); m.camera = cam; return m



def fcurves_of(o):
    ad = o.animation_data
    out = []
    if ad and ad.action:
        for lay in ad.action.layers:
            for st in lay.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
    return out


def shrug():
    """S005 (master f336-365): the receptionist shrugs on "which one" (~f330), her eyes slide to the board (~f350), and she
    settles into exactly her f366 pose. Blend frame = master + 1. Rest pose = what the rig evaluates to at blend 366."""
    E = lambda k, d: float(os.environ.get(k, d))
    sc.frame_set(366)
    rest = {}
    names = ["RCP", "rcp_head", "rcp_shoulder_L", "rcp_shoulder_R", "rcp_elbow_L", "rcp_elbow_R", "rcp_eye_L", "rcp_eye_R"]
    for n in names:
        o = bpy.data.objects[n]; rest[n] = (tuple(o.location), tuple(o.rotation_euler))
    # clear the per-frame idle keys of the channels we rework inside the window, then key our own
    LO, HI = 326, 366
    touch = {"RCP": ("location",), "rcp_head": ("rotation_euler",), "rcp_shoulder_L": ("rotation_euler",), "rcp_shoulder_R": ("rotation_euler",),
             "rcp_elbow_L": ("rotation_euler",), "rcp_elbow_R": ("rotation_euler",), "rcp_eye_L": ("location",), "rcp_eye_R": ("location",)}
    for n, paths in touch.items():
        o = bpy.data.objects[n]
        for fc in fcurves_of(o):
            if fc.data_path in paths:
                for k in list(fc.keyframe_points):
                    if LO <= k.co.x <= HI: fc.keyframe_points.remove(k)
    def key(n, frame, prop, delta=None, abs_=None):
        o = bpy.data.objects[n]; i = 0 if prop == "location" else 1
        base = list(rest[n][0] if prop == "location" else rest[n][1])
        v = base if abs_ is None else list(abs_)
        if delta:
            for ax, d in delta.items(): v[ax] += d
        setattr(o, prop, v); o.keyframe_insert(prop, frame=frame)
    UP = E("SH_UP", 0.035); SHO = E("SH_SHO", 0.55); ELB = E("SH_ELB", 0.5); ROLL = E("SH_ROLL", 0.14)
    TL = [  # frame, RCP dz, shoulder dx (L, R), elbow dx (L, R), head roll(y), head yaw(z)
        (326, 0.0, 0.0, 0.0, 0.0, 0.0),
        (330, -0.012, -0.05, 0.05, 0.0, 0.03),         # anticipation: she sinks a touch
        (334, UP, SHO, -ELB, ROLL, -0.06),             # up: shoulders lift, forearms open, head tilts ("which one?")
        (340, UP * 0.8, SHO * 0.85, -ELB * 0.8, ROLL * 0.9, -0.05),
        (346, 0.012, SHO * 0.3, -ELB * 0.3, ROLL * 0.3, -0.02),   # settle (overshoot a hair below rest)
        (350, -0.004, 0.0, 0.0, 0.0, 0.0),
        (356, 0.0, 0.0, 0.0, 0.0, 0.0),
        (366, 0.0, 0.0, 0.0, 0.0, 0.0),
    ]
    for f, dz, dsh, delb, roll, yaw in TL:
        key("RCP", f, "location", {2: dz})
        key("rcp_shoulder_L", f, "rotation_euler", {0: dsh}); key("rcp_shoulder_R", f, "rotation_euler", {0: -dsh})
        key("rcp_elbow_L", f, "rotation_euler", {0: delb}); key("rcp_elbow_R", f, "rotation_euler", {0: delb})
        key("rcp_head", f, "rotation_euler", {1: roll, 2: yaw})
    # eyes slide to the board (screen right + up) ~f350, then back to rest by f361
    for n in ("rcp_eye_L", "rcp_eye_R"):
        for f, dx, dz in ((345, 0, 0), (349, E("SH_EYE_X", 0.018), E("SH_EYE_Z", 0.008)), (357, E("SH_EYE_X", 0.018), E("SH_EYE_Z", 0.008)), (361, 0, 0), (366, 0, 0)):
            key(n, f, "location", {0: dx, 2: dz})
    for n in touch:
        for fc in fcurves_of(bpy.data.objects[n]):
            for k in fc.keyframe_points:
                if LO <= k.co.x <= HI: k.interpolation = "BEZIER"; k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
    sc.frame_set(1)

if MODE == "outro":
    board_seq_hold(); portraits()
    # blend = master + 1. 1000 until "one" (f5132), then flap -> 1001 (6 f), holds to the end
    board_ns([(0, 5), (5132, 6), (5133, 7), (5134, 8), (5135, 9), (5136, 10)], ticker_keys=((1, "press"),))


def hall_look():
    """S100/S101 (the IP-scroll hall, HALL set at x=544): dark charcoal walls with real texture, panel ceiling lights you can
    point at, the portrait wall hanging as a lit picture (placeholder until F30), sticky-note ink dark."""
    PH = os.path.join(DOCS, "textures", "ph", "plaster_grey_04")
    def pm(name, tint, rough=1.0, tile=2.0, bump=0.5):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        N = nt.nodes.new; L = nt.links.new
        out = N("ShaderNodeOutputMaterial"); bs = N("ShaderNodeBsdfPrincipled"); geo = N("ShaderNodeNewGeometry"); mp = N("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1 / tile,) * 3; L(geo.outputs["Position"], mp.inputs["Vector"])
        def tex(kind, nc):
            n = N("ShaderNodeTexImage"); fn = [f for f in os.listdir(PH) if f"_{kind}_" in f][0]
            n.image = bpy.data.images.load(os.path.join(PH, fn), check_existing=True)
            if nc: n.image.colorspace_settings.name = "Non-Color"
            n.projection = "BOX"; n.projection_blend = 0.25; L(mp.outputs["Vector"], n.inputs["Vector"]); return n
        td, tdisp = tex("diff", False), tex("disp", True)
        mix = N("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1; mix.inputs["B"].default_value = (*tint, 1)
        L(td.outputs["Color"], mix.inputs["A"]); L(mix.outputs["Result"], bs.inputs["Base Color"])
        bp = N("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
        L(tdisp.outputs["Color"], bp.inputs["Height"]); L(bp.outputs["Normal"], bs.inputs["Normal"]); bs.inputs["Roughness"].default_value = rough
        L(bs.outputs["BSDF"], out.inputs["Surface"]); return m
    wall = pm("hall_wall", (0.20, 0.22, 0.26))
    for n in ("hl_wall-1", "hl_wall1", "hl_endL", "hl_endR", "hl_endT"):
        o = bpy.data.objects[n]; o.data.materials.clear(); o.data.materials.append(wall)
    fl = bpy.data.materials.get("srv_floor")
    # ceiling: a dark panel ceiling plane with two real light panels
    me = bpy.data.meshes.new("hl_ceiling"); me.from_pydata([(-8, -1.6, 0), (8, -1.6, 0), (8, 1.6, 0), (-8, 1.6, 0)], [], [(0, 1, 2, 3)]); me.update()
    ce = bpy.data.objects.new("hl_ceiling", me); ce.location = (546.5, 0, 3.0); ce.rotation_euler = (math.pi, 0, 0)
    me.materials.append(pm("hall_ceil", (0.08, 0.085, 0.095))); bpy.data.collections["HALL"].objects.link(ce)
    pan = bpy.data.materials.new("hall_panel"); pan.use_nodes = True; pn = pan.node_tree; pn.nodes.clear()
    po = pn.nodes.new("ShaderNodeOutputMaterial"); pe = pn.nodes.new("ShaderNodeEmission"); pe.inputs["Color"].default_value = (1.0, 0.86, 0.68, 1); pe.inputs["Strength"].default_value = 18
    pn.links.new(pe.outputs[0], po.inputs["Surface"])
    for i, x in enumerate((543.0, 549.0)):
        pme = bpy.data.meshes.new("hl_panel%d" % i); pme.from_pydata([(-0.6, -0.25, 0), (0.6, -0.25, 0), (0.6, 0.25, 0), (-0.6, 0.25, 0)], [], [(0, 1, 2, 3)]); pme.update()
        po_ = bpy.data.objects.new("hl_panel%d" % i, pme); po_.location = (x, 0, 2.985); po_.rotation_euler = (math.pi, 0, 0); pme.materials.append(pan)
        bpy.data.collections["HALL"].objects.link(po_)
    for n, e, col in (("hl_ceil0", 90, (1.0, 0.86, 0.68)), ("hl_ceil1", 90, (1.0, 0.86, 0.68)), ("hl_door", 150, (0.8, 0.9, 1.0))):
        o = bpy.data.objects[n]; o.data.energy = e; o.data.color = col
    for n in ("hl_ceil0", "hl_ceil1"): bpy.data.objects[n].data.size = 1.2; bpy.data.objects[n].data.shape = "RECTANGLE"; bpy.data.objects[n].data.size_y = 0.5
    # the portrait: lit placeholder + a picture light
    port = bpy.data.objects["hl_portrait"]; m = bpy.data.materials.new("hl_portrait_L"); m.use_nodes = True; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(KIT if os.path.exists(KIT) else os.path.join(TEX, "ph_portrait_visionary.png"), check_existing=True)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.1
    port.data.materials.clear(); port.data.materials.append(m)
    ld = bpy.data.lights.new("L_hall_pic", "SPOT"); ld.energy = 120; ld.spot_size = math.radians(60); ld.spot_blend = 0.8; ld.color = (1.0, 0.82, 0.58); ld.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("L_hall_pic", ld); lo.location = (544.3, 1.1, 1.8); sc.collection.objects.link(lo)
    lo.rotation_euler = (Vector((544.3, 1.48, 0.95)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    dk = bpy.data.materials.new("hl_note_ink"); dk.use_nodes = True
    next(n for n in dk.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.01, 0.01, 0.015, 1)
    for n in ("hl_n1", "hl_n2"):
        o = bpy.data.objects[n]; o.data.materials.clear(); o.data.materials.append(dk)
    ink = None
    if ink and ink.use_nodes:
        for n in ink.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED": n.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1)
            if n.type == "EMISSION": n.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1)


# ---------------------------------------------------------------- power banks (S131 outage, S150 end)
PW_GROUPS = {}


def prop_key(name, pairs, kind="CONSTANT"):
    """key a scene custom property: pairs = [(blend_frame, value)]"""
    sc[name] = float(pairs[0][1])
    for f, v in pairs:
        sc[name] = float(v); sc.keyframe_insert('["%s"]' % name, frame=f)
    for fc in fcurves_of(sc):
        if fc.data_path == '["%s"]' % name:
            for k in fc.keyframe_points: k.interpolation = kind


def drv_scene_prop(idb, path, expr_base, props, index=-1):
    fc = idb.driver_add(path) if index < 0 else idb.driver_add(path, index)
    d = fc.driver; d.type = "SCRIPTED"
    names = []
    for i, pr in enumerate(props):
        v = d.variables.new(); v.name = "p%d" % i; v.type = "SINGLE_PROP"
        v.targets[0].id_type = "SCENE"; v.targets[0].id = sc; v.targets[0].data_path = '["%s"]' % pr; names.append(v.name)
    d.expression = "%s*%s" % (expr_base, "*".join(names)) if expr_base != 1 else "*".join(names)
    return fc


def gate_material(m, props):
    """wrap an emissive material: shader mixed with a dark satin by the product of the scene props (1 = on)."""
    nt = m.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None) or next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    if out is None or not out.inputs["Surface"].is_linked or any(n.name == "pw_gate" for n in nt.nodes): return False
    src = out.inputs["Surface"].links[0].from_socket
    off = nt.nodes.new("ShaderNodeBsdfPrincipled"); off.inputs["Base Color"].default_value = (0.03, 0.03, 0.032, 1); off.inputs["Roughness"].default_value = 0.4
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.name = "pw_gate"
    val = nt.nodes.new("ShaderNodeValue"); val.name = "pw_val"
    nt.links.new(off.outputs["BSDF"], mix.inputs[1]); nt.links.new(src, mix.inputs[2]); nt.links.new(val.outputs[0], mix.inputs["Fac"])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    drv_scene_prop(nt, 'nodes["pw_val"].outputs[0].default_value', 1, props)
    return True


def emissive_mats(visible_only=True):
    res = {}
    for o in bpy.data.objects:
        if o.type in ("MESH", "CURVE", "FONT") and not (visible_only and o.hide_render):
            for sl in o.material_slots:
                m = sl.material
                if m and m.use_nodes and m.name not in res:
                    for n in m.node_tree.nodes:
                        st = 0
                        if n.type == "EMISSION": st = n.inputs["Strength"].default_value
                        elif n.type == "BSDF_PRINCIPLED" and sum(n.inputs["Emission Color"].default_value[:3]) > 0.02: st = n.inputs["Emission Strength"].default_value
                        if st > 0.05: res[m.name] = m; break
    return res


def make_exit_sign(loc=(2.55, 4.93, 3.45)):
    m, mp = emis_tex_mat("exit_sign_mat", os.path.join(TEX, "exit_sign.png"), 1.4)
    coll = bpy.data.collections.get("SET_lobby_new") or sc.collection
    ob = plane("exit_sign", loc, 0.62, 0.25, m, coll)
    ld = bpy.data.lights.new("L_exit", "AREA"); ld.shape = "RECTANGLE"; ld.size = 0.6; ld.size_y = 0.24; ld.color = (0.35, 1.0, 0.6); ld.energy = float(os.environ.get("EXIT_E", 12))
    lo = bpy.data.objects.new("L_exit", ld); lo.location = (loc[0], loc[1] - 0.05, loc[2]); lo.rotation_euler = (-math.pi / 2, 0, 0); sc.collection.objects.link(lo)
    return m


def bank_on(f, d=1.0):
    """a bank 'clunks' on at master frame f (blend +1): on, a one-frame dip, on."""
    b = f + 1
    return [(b, 1.0 * d), (b + 2, 0.25 * d), (b + 3, 1.0 * d)]


def power_banks(mode):
    """Group the lobby's lights + emissive materials into banks driven by scene props pw_*: smile, exit, A (desk pendants),
    B (ceiling downlights), C (everything else), ns (the NOW SERVING board: always the last thing lit)."""
    exit_m = make_exit_sign()
    for n in ("L_fire", "L_fire_back", "L_fire_high"):                          # the fire is out in the outro
        o = bpy.data.objects.get(n)
        if o: o.data.animation_data_clear(); o.data.energy = 0.0
    grp_l = {"A": ["L_pendant", "L_pendant_0", "L_pendant_1"], "B": ["L_downlight_%d" % i for i in range(4)],
             "smile": ["L_rcp_face"], "exit": ["L_exit"], "ns": ["L_ns_board"]}
    in_grp = {n for v in grp_l.values() for n in v}
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.name not in in_grp and not (o.data.animation_data and o.data.animation_data.action) and o.data.energy > 0 and not o.hide_render:
            grp_l.setdefault("C", []).append(o.name)
    for g, names in grp_l.items():
        for n in names:
            o = bpy.data.objects.get(n)
            if not o or (o.data.animation_data and o.data.animation_data.action): continue
            props = ["pw_" + g, "pw_gain"] + (["pw_desk"] if g in ("A", "B", "C") else [])
            drv_scene_prop(o.data, "energy", o.data.energy, props)
    grp_m = {"smile": ("v1_Rcp_Glow",), "A": ("AFF_bulb_2700K",), "B": ("AFF_downlight_lens",), "exit": ("exit_sign_mat",), "ns": ("ns_board_face", "ns_ticker_mat")}
    mat_g = {n: g for g, ns in grp_m.items() for n in ns}
    for name, m in emissive_mats().items():
        if m.node_tree.animation_data and m.node_tree.animation_data.action and name not in mat_g: continue
        g = mat_g.get(name, "C")
        gate_material(m, ["pw_" + g])
    return grp_l


def outro_power():
    sc.frame_start = 4857                                         # master 4856
    set_marker("o0", 4857, bpy.data.objects["CAM_out_A"])
    # CAM_out_A holds its first key before 4940: the outage is shot from the same camera, f4856-4938
    T = {"smile": 4880, "exit": 4896, "A": 4906, "B": 4922, "C": 4938}   # master frames each thing returns
    OFF_END = {"A": 6158, "B": 6164, "C": 6170, "smile": 6170, "exit": 6164}
    for g, f in T.items():
        pairs = [(sc.frame_start, 0.0)] + bank_on(f)
        if g in OFF_END: pairs += [(OFF_END[g] + 1, 0.0)]
        prop_key("pw_" + g, pairs)
    prop_key("pw_ns", [(sc.frame_start, 0.0)] + bank_on(T["C"]))
    prop_key("pw_desk", [(sc.frame_start, 1.0), (5030, 1.0), (5036, DESK_DIM), (5072, DESK_DIM), (5078, 1.0), (5171, 1.0), (5177, DESK_DIM), (5258, DESK_DIM), (5264, 1.0)], "LINEAR")
    # S150: extend to master 6182 (blend 6183), the pull-back finishes straight back like the opening frame
    sc.frame_end = 6183
    prop_key("pw_deskmat", [(sc.frame_start, 1.0), (5172, 1.0), (5178, 0.25), (5258, 0.25), (5264, 1.0)], "LINEAR")
    gate_material(bpy.data.materials["AFF_travertine"], ["pw_deskmat"])      # S135 macro: the cream desk top reads as stone, not a white-out
    dg = bpy.data.objects.get("dl_glow")                               # the DEPLOY lamp's own light washes the desk after S133
    if dg:
        for fc in fcurves_of(dg.data):
            if fc.data_path == "energy":
                for k in fc.keyframe_points:
                    if k.co.x > 5100: k.co.y *= 0.1; k.handle_left.y *= 0.1; k.handle_right.y *= 0.1
    cam = bpy.data.objects["CAM_out_final"]
    for fc in fcurves_of(cam):
        if fc.data_path == "location" and fc.array_index == 0:
            for k in fc.keyframe_points: k.co.y = 0.0; k.handle_left.y = 0.0; k.handle_right.y = 0.0     # straight pull-back, x = 0
            fc.update()
    cam.location = (0.0, -6.0, 1.98); cam.keyframe_insert("location", frame=6183)
    cam.data.lens = 30; cam.data.keyframe_insert("lens", frame=6183)


DESK_DIM = float(os.environ.get("DESK_DIM", 0.02))
if MODE == "outro":
    bpy.data.objects.remove(bpy.data.objects["queue_1001"], do_unlink=True)
    GAIN = float(os.environ.get("LOBBY_GAIN", 3.4))
    prop_key("pw_gain", [(1, GAIN)])
    power_banks("outro"); outro_power()

if MODE == "hall":
    finish_scene(SRC_S1)
    hall_look()

if MODE == "intro":
    board_seq_hold(); portraits()
    gain_lights([(1, float(os.environ.get("LOBBY_GAIN", 3.4))), (315, 1.0)])
    board_ns([(0, 0), (177, 1), (178, 2), (179, 3), (180, 4), (181, 5)], ticker_keys=((1, 'wait'), (140, 'wait'), (166, 'press')))
    # S002 f125-189: the in-world board insert (blend = master + 1). A slow push-in on the board, 999 -> 1000 on "thousand".
    ins = new_cam("CAM_ns_insert", (2.5, 0.5, 2.8), (5.0, 4.93, 2.74), 45)
    for f, loc in ((126, (2.5, 0.5, 2.8)), (190, (3.1, 1.2, 2.78))):
        ins.location = loc; ins.keyframe_insert("location", frame=f)
        ins.rotation_euler = (Vector((5.0, 4.93, 2.74)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); ins.keyframe_insert("rotation_euler", frame=f)
    set_interp(ins, "BEZIER")
    set_marker("shot_B", 126, ins)
    set_marker("shot_B2", 191, bpy.data.objects["CAM_B_queue"])


if MODE == "intro":
    shrug()

# ==== MODE-SPECIFIC ADDITIONS GO ABOVE THIS LINE ====
def fix_paths():
    """Relative image paths from appended datablocks are remapped wrongly: make every one absolute and existing."""
    bases = [os.path.dirname(OUT), SHORT, DOCS, os.path.join(DOCS, "short"), os.path.expanduser("~/Studio/asking-for-a-friend/blender")]
    bad = 0
    for im in bpy.data.images:
        if im.source not in ("FILE", "SEQUENCE", "MOVIE") or not im.filepath: continue
        fp = im.filepath
        if fp.startswith("//"):
            rel = fp[2:]
            cands = [os.path.normpath(os.path.join(b, rel)) for b in bases]
            ok = next((c for c in cands if os.path.exists(c)), None)
            if ok is None:
                m = rel.replace("\\", "/").split("textures/", 1)
                if len(m) == 2:
                    ok = next((c for c in (os.path.join(DOCS, "textures", m[1]), os.path.expanduser("~/Studio/asking-for-a-friend/blender/textures/" + m[1])) if os.path.exists(c)), None)
            if ok: im.filepath = ok
            else: bad += 1; print("[look] MISSING image", im.name, fp)
        elif not os.path.exists(bpy.path.abspath(fp)):
            bad += 1; print("[look] MISSING image", im.name, fp)
    print("[look] image paths fixed, missing:", bad)
fix_paths()
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=True)
print("[look] saved", OUT)
