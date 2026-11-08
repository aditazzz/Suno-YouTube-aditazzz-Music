"""act1_fix: fixes on top of the finish_3 *_look.blend copies (never saves them), then renders like render3.py.

  FRAMES=180,260 OUT=<dir> Blender -b act1_lobby_look.blend --python act1_fix.py -- intro
  modes: intro (f180 NOW SERVING insert, f260 portrait) | hall (f3925) | outro (f5200 printer, frosted glass, f4941/6100/6170)
Light levels are env-tunable (W_* below) so a re-render can retune without editing.
"""
import bpy, os, sys, math, bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sc = bpy.context.scene
MODE = sys.argv[sys.argv.index("--") + 1]
E = lambda k, d: float(os.environ.get(k, d))
TEX = os.path.expanduser("~/Documents/Original Music/Asking for a Friend 2/blender/textures/screens/ns")


def fcurves_of(ad):
    """fcurves of an animation_data (Blender 5 layered actions, or the old action.fcurves)"""
    a = ad.action
    if hasattr(a, "fcurves"): return list(a.fcurves)
    return [fc for ly in a.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]


def link(o, coll=None):
    (coll or sc.collection).objects.link(o)
    return o


def spot(name, loc, target, energy, size=70, blend=0.8, color=(1.0, 0.85, 0.65), soft=0.1):
    ld = bpy.data.lights.new(name, "SPOT"); ld.energy = energy; ld.spot_size = math.radians(size); ld.spot_blend = blend
    ld.color = color; ld.shadow_soft_size = soft
    lo = link(bpy.data.objects.new(name, ld)); lo.location = loc
    lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return lo


def area(name, loc, target, energy, w, h, color=(1.0, 0.9, 0.75)):
    ld = bpy.data.lights.new(name, "AREA"); ld.shape = "RECTANGLE"; ld.size = w; ld.size_y = h; ld.energy = energy; ld.color = color
    lo = link(bpy.data.objects.new(name, ld)); lo.location = loc
    lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return lo


def box(name, loc, dim, mat, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); o.location = loc; o.scale = dim; o.rotation_euler = rot
    o.data.materials.append(mat); return o


def mat(name, color, rough=0.5, metal=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = es
    return m


def fixture(name, loc, size=(0.5, 0.06, 0.05)):
    return box(name, loc, size, mat("fx_brass", (0.55, 0.38, 0.18), 0.35, 1.0))


def key_scene_prop(name, v):
    """scale every key of a keyed scene property that is below 1 down to v (the dim windows); works on layered actions too"""
    act = sc.animation_data.action
    fcs = []
    if hasattr(act, "fcurves"): fcs = list(act.fcurves)
    else:
        for l in act.layers:
            for st in l.strips:
                for cb in st.channelbags: fcs += list(cb.fcurves)
    n = 0
    for fc in fcs:
        if name in fc.data_path:
            for k in fc.keyframe_points:
                if k.co.y < 0.99: k.co.y = v; k.handle_left.y = v; k.handle_right.y = v; n += 1
            fc.update()
    print("[fix] dimmed", name, "keys", n)


# ------------------------------------------------------------------------------------------------ intro
def intro():
    # f180: the NOW SERVING board sits on a dark slat wall -> real wall washers (two ceiling-mounted wall-wash spots, fixtures visible)
    for i, x in enumerate((4.1, 5.9)):
        fixture("ns_wash_fx%d" % i, (x, 4.62, 4.35), (0.22, 0.22, 0.16))
        spot("L_ns_wash%d" % i, (x, 4.55, 4.3), (5.0, 4.98, 2.7), E("W_NSWASH", 1300), 80, 0.9, (1.0, 0.86, 0.66), 0.15)
    area("L_ns_corr", (6.4, 3.2, 4.6), (6.5, 5.0, 2.2), E("W_NSCORR", 1000), 2.0, 2.0, (1.0, 0.84, 0.62))      # the dark corridor wall right of the board
    # f260: the portrait + prism reads: a real gallery wash from the front + warmer picture light, wall washer on the wall behind
    spot("L_pt_wash", (0.0, 2.2, 5.0), (0.0, 4.35, 3.5), E("W_PTWASH", 1400), 55, 0.6, (1.0, 0.88, 0.7), 0.2)
    if E("W_PTWALL", 0) > 0: spot("L_pt_wallL", (-2.8, 2.5, 5.0), (-2.2, 4.97, 3.4), E("W_PTWALL", 0), 70, 0.9, (1.0, 0.82, 0.6), 0.2)
    if E("W_PTWALL", 0) > 0: spot("L_pt_wallR", (2.8, 2.5, 5.0), (2.2, 4.97, 3.4), E("W_PTWALL", 0), 70, 0.9, (1.0, 0.82, 0.6), 0.2)
    for m in bpy.data.materials:                                   # the prism faces are self-lit a little more (they are lit panels)
        if m.name.startswith("PT_") and m.use_nodes:
            b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if b and "Emission Strength" in b.inputs and m.name != "PT_frame_brass": b.inputs["Emission Strength"].default_value = E("PT_EMIT", 0.25)
    # gap right of the board (a dark void in the insert): close it with the same walnut wall, lit by the washers
    wm = bpy.data.materials.get("AFF_walnut_backing") or mat("fill_walnut", (0.12, 0.06, 0.03), 0.5)
    box("ns_gap_wall", (6.55, 5.05, 2.5), (1.3, 0.2, 5.0), wm)
    area("L_pt_low", (0.0, 2.5, 0.9), (0.0, 5.0, 2.3), E("W_PTLOW", 1400), 4.0, 1.6, (1.0, 0.84, 0.64))
    # the new lights belong to the wides + inserts: they are keyed off from f315 so the S005 close-up still matches the finished f366
    for o in list(bpy.data.objects):
        if o.type == "LIGHT" and (o.name.startswith("L_ns_") or o.name.startswith("L_pt_")) and o.name != "L_ns_board":
            e = o.data.energy
            o.data.energy = e; o.data.keyframe_insert("energy", frame=1)
            o.data.keyframe_insert("energy", frame=314)
            o.data.energy = 0.0; o.data.keyframe_insert("energy", frame=316)
            for fc in (o.data.animation_data.action.fcurves if hasattr(o.data.animation_data.action, "fcurves") else []):
                for k in fc.keyframe_points: k.interpolation = "CONSTANT"
    if os.environ.get("DOTS", "1") == "1": pulse_dots()


def pulse_dots():
    """ALL SYSTEMS board: its green status dots pulse (emission keyed by frame): the image is split into 'dot' (green) pixels,
    whose brightness gets 1 + A*sin(frame) while the rest stays as it was."""
    m = bpy.data.materials.get("AFF_board")
    if not m or not m.node_tree: return
    nt = m.node_tree
    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
    if not tex: return
    emis = None
    for n in nt.nodes:
        if n.type == "BSDF_PRINCIPLED" and "Emission Strength" in n.inputs: emis = n
        if n.type == "EMISSION": emis = n
    if emis is None: return
    st = emis.inputs["Strength"] if emis.type == "EMISSION" else emis.inputs["Emission Strength"]
    # green-ness mask: g - max(r, b)
    sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(tex.outputs["Color"], sep.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; nt.links.new(sep.outputs["Red"], mx.inputs[0]); nt.links.new(sep.outputs["Blue"], mx.inputs[1])
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.use_clamp = True; nt.links.new(sep.outputs["Green"], sub.inputs[0]); nt.links.new(mx.outputs[0], sub.inputs[1])
    ramp = nt.nodes.new("ShaderNodeMath"); ramp.operation = "MULTIPLY"; ramp.use_clamp = True; ramp.inputs[1].default_value = 6.0; nt.links.new(sub.outputs[0], ramp.inputs[0])
    ph = nt.nodes.new("ShaderNodeValue"); ph.name = "dot_phase"
    d = ph.outputs[0].driver_add("default_value").driver; d.type = "SCRIPTED"; d.expression = "0.5+0.5*sin(frame*0.45)"
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; nt.links.new(ramp.outputs[0], mul.inputs[0]); nt.links.new(ph.outputs[0], mul.inputs[1])
    mul2 = nt.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"; mul2.inputs[1].default_value = E("DOT_AMT", 2.2); nt.links.new(mul.outputs[0], mul2.inputs[0])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"; add.inputs[1].default_value = 1.0; nt.links.new(mul2.outputs[0], add.inputs[0])
    base = st.default_value
    # strength = base * (1 + amt*mask*phase)
    sm = nt.nodes.new("ShaderNodeMath"); sm.operation = "MULTIPLY"; sm.inputs[1].default_value = base; nt.links.new(add.outputs[0], sm.inputs[0])
    nt.links.new(sm.outputs[0], st)


# ------------------------------------------------------------------------------------------------ hall
def hall():
    """S100/101 hall: make it a place. Grey plaster walls get a wainscot + brass rail, baseboards, framed pictures with picture
    lights, a runner floor, a darker paper scroll so it does not clip, door light shaping the space."""
    X0, X1 = 540.0, 554.0
    wood = mat("hall_wain", (0.045, 0.03, 0.025), 0.45)
    brass = mat("hall_brass", (0.6, 0.42, 0.2), 0.3, 1.0)
    # wainscot (lower wall), rail, baseboard on both walls
    for s in (-1, 1):
        y = s * 1.52
        box("hl_wain%d" % s, ((X0 + X1) / 2, y, 0.45), (X1 - X0, 0.05, 0.9), wood)
        box("hl_rail%d" % s, ((X0 + X1) / 2, y - s * 0.02, 0.92), (X1 - X0, 0.07, 0.04), brass)
        box("hl_base%d" % s, ((X0 + X1) / 2, y - s * 0.03, 0.05), (X1 - X0, 0.04, 0.1), mat("hl_baseb", (0.03, 0.025, 0.02), 0.5))
        box("hl_crown%d" % s, ((X0 + X1) / 2, y - s * 0.04, 2.9), (X1 - X0, 0.08, 0.1), mat("hl_crownb", (0.1, 0.1, 0.11), 0.6))
    # a runner: dark red felt along the hall, floor reflects the lights
    fl = bpy.data.objects["hl_floor"]
    fm = mat("hall_floor", (0.05, 0.05, 0.055), E("HALL_FLOOR_R", 0.32))
    fl.data.materials.clear(); fl.data.materials.append(fm)
    rn = mat("hall_runner", (0.28, 0.035, 0.04), 0.9)
    box("hl_runner", ((X0 + X1) / 2, 0.0, 0.004), (X1 - X0, 1.5, 0.008), rn)
    box("hl_runner_edge0", ((X0 + X1) / 2, 0.78, 0.007), (X1 - X0, 0.04, 0.006), brass)
    box("hl_runner_edge1", ((X0 + X1) / 2, -0.78, 0.007), (X1 - X0, 0.04, 0.006), brass)
    # the scroll (paper): sits over the runner, not a white-out
    st = bpy.data.objects["hl_strip"]; st.location.z += 0.016
    pm = mat("hall_scroll", (E("SCROLL_V", 0.3),) * 3, 0.85)
    b = next(n for n in pm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.34, 0.32, 0.29, 1)
    nt = pm.node_tree
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.inputs["Scale"].default_value = 90; wv.inputs["Distortion"].default_value = 0.0
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeMix"); cr.data_type = "RGBA"; cr.blend_type = "MULTIPLY"; cr.inputs["Factor"].default_value = 0.0
    bmp = nt.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.15; bmp.inputs["Distance"].default_value = 0.002
    nt.links.new(wv.outputs["Fac"], bmp.inputs["Height"]); nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])
    st.data.materials.clear(); st.data.materials.append(pm)
    # framed pictures along the +y wall, each with a picture light
    pic = mat("hall_print", (0.02, 0.02, 0.025), 0.5)
    for i, x in enumerate((541.9, 546.6, 549.4, 551.9)):
        frm = box("hl_pf%d" % i, (x, 1.50, 1.7), (0.7, 0.03, 0.9), brass)
        box("hl_pp%d" % i, (x, 1.48, 1.7), (0.62, 0.02, 0.82), pic)
        box("hl_plb%d" % i, (x, 1.46, 2.25), (0.3, 0.05, 0.03), brass)
        spot("L_hall_pl%d" % i, (x, 1.38, 2.22), (x, 1.5, 1.6), E("W_HALLPL", 120), 80, 0.9, (1.0, 0.82, 0.58), 0.04)
    # wall sconces on the -y wall (warm uplight; you can point at them)
    for i, x in enumerate((541.5, 545.5, 549.5, 552.5)):
        sm = mat("hall_sconce", (0.9, 0.75, 0.5), 0.3, 0, (1.0, 0.8, 0.5), 6.0)
        box("hl_scx%d" % i, (x, -1.42, 1.9), (0.14, 0.06, 0.28), sm)
        area("L_hall_sc%d" % i, (x, -1.32, 1.9), (x, 0.0, 2.9), E("W_SCONCE", 35), 0.3, 0.3, (1.0, 0.78, 0.5))
    # door light: stronger bloom spill from the open door at the end, a bit cooler than the warm lamps
    for n in ("hl_ceil0", "hl_ceil1"):
        bpy.data.objects[n].data.energy = E("W_HALLCEIL", 45)
    bpy.data.objects["hl_door"].data.energy = E("W_HALLDOOR", 200)
    bpy.data.objects["hl_portrait"].data.materials[0].node_tree.nodes  # keep


# ------------------------------------------------------------------------------------------------ outro
def outro():
    # S135 macro: the desk top and lamp wash down a notch further; paper stays readable (its own page light)
    ad = sc.animation_data
    from_keys = 0
    for fc in (ad.action.fcurves if ad and ad.action and hasattr(ad.action, "fcurves") else []):
        pass
    v = E("DESKMAT", 0.1)
    key_scene_prop("pw_deskmat", v)
    # real frosted glass for the left partition (and the wall_back_center that shares it)
    m = bpy.data.materials.get("AFF_glass_partition_thin")
    if m:
        nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        b.inputs["Base Color"].default_value = (E("FROST_TINT", 0.28),) * 3 + (1,)  # r1_fix: was (0.78,0.86,0.84), clipped white
        b.inputs["Roughness"].default_value = E("FROST_R", 0.38)
        for k in ("Transmission Weight", "Transmission"):
            if k in b.inputs: b.inputs[k].default_value = 1.0
        b.inputs["IOR"].default_value = 1.45
        # fine grain in the roughness/normal so it reads as etched glass, not a flat slab
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 260; nz.inputs["Detail"].default_value = 6
        tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08; bp.inputs["Distance"].default_value = 0.002
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
        rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = E("FROST_R", 0.38) - 0.12; rr.inputs["To Max"].default_value = E("FROST_R", 0.38) + 0.12
        nt.links.new(nz.outputs["Fac"], rr.inputs["Value"]); nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
        nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
        if hasattr(m, "surface_render_method"): m.surface_render_method = "BLENDED" if os.environ.get("FROST_BLEND") else "DITHERED"
    # something behind it: a dark teal back office with warm lit windows and a few shapes, so the pane has a glow and silhouettes to diffuse
    backm = mat("fr_back", (0.02, 0.05, 0.05), 0.8)
    box("fr_back_wall", (-5.0, 7.0, 2.5), (6.0, 0.1, 5.0), backm)
    win = mat("fr_win", (0.9, 0.7, 0.4), 0.5, 0, (1.0, 0.72, 0.4), E("FROST_WIN", 0.9))
    for i, x in enumerate((-7.0, -5.8, -4.6, -3.4)):
        box("fr_win%d" % i, (x, 6.9, 2.9), (0.7, 0.04, 1.1), win)
    shapem = mat("fr_shape", (0.015, 0.02, 0.02), 0.7)
    for i, (x, h) in enumerate(((-6.4, 1.7), (-5.2, 1.5), (-3.9, 1.8))):
        box("fr_sil%d" % i, (x, 6.2, h / 2), (0.55, 0.4, h), shapem)
    sm = bpy.data.materials.get("AFF_steel_dark_anodised") or mat("fr_steel", (0.03, 0.03, 0.035), 0.4, 0.8)
    for i in range(5):
        box("fr_mull%d" % i, (-7.0 + i, 5.08, 2.5), (0.07, 0.1, 5.0), sm)
    box("fr_sill", (-5.0, 5.08, 0.9), (4.1, 0.1, 0.06), sm)
    area("L_fr_back", (-5.0, 6.0, 3.6), (-5.0, 5.15, 2.0), E("W_FRBACK", 50), 3.0, 1.0, (1.0, 0.82, 0.6))


    # r1_fix (her note on f4941, "light looks blown out"): glass tint 0.28 + dimmer back office keep the pane silver, not clipped;
    # a soft cool-neutral wash on the dark back wall keeps "lights fully back" reading bright (median) without touching the desk highlights.
    wl = area("L_r1_wallwash", (3.0, -4.0, 4.2), (3.0, 5.0, 1.8), E("W_R1WASH", 90), 6.0, 2.5, (0.95, 0.9, 0.82))
    # on only for f4900-5099 (the S132 CAM_out_A take) so the approved f5100/f5200/f6100/f6170 stay exactly as approved
    for fr, v in ((4899, 0.0), (4900, E("W_R1WASH", 90)), (5099, E("W_R1WASH", 90)), (5100, 0.0)):
        wl.data.energy = v; wl.data.keyframe_insert("energy", frame=fr)
    for fc in fcurves_of(wl.data.animation_data):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"


    # glass tint + back light keyed (constant) for the f4900-5099 take only: the other outro frames keep their approved look
    if m:
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); bl = bpy.data.objects["L_fr_back"].data
        T = E("FROST_TINT", 0.28)
        for fr, c, e in ((4899, 0.82, 50), (4900, T, E("W_FRBACK_R1", 18)), (5099, T, E("W_FRBACK_R1", 18)), (5100, 0.82, 50)):
            bsdf.inputs["Base Color"].default_value = (0.78 * c / 0.82, 0.86 * c / 0.82, 0.84 * c / 0.82, 1) if c != 0.82 else (0.78, 0.86, 0.84, 1)
            bsdf.inputs["Base Color"].keyframe_insert("default_value", frame=fr); bl.energy = e; bl.keyframe_insert("energy", frame=fr)
        for ad in (m.node_tree.animation_data, bl.animation_data):
            for fc in fcurves_of(ad):
                for k in fc.keyframe_points: k.interpolation = "CONSTANT"


# ------------------------------------------------------------------------------------------------ run
{"intro": intro, "hall": hall, "outro": outro}[MODE]()
exec(open(os.path.join(HERE, "render3.py")).read())
