"""sets_server / sets_undercroft from the blocking blend AFF_blk_s02_verse1 (opened READ-ONLY, saved at once as a new file).

  Blender -b blocking/AFF_blk_s02_verse1.blend --python build_s02.py -- <server|undercroft> <out name>

server:     the night server room aisle, Claude's tiny desk, the clock, the legacy server with the scheduler, the grate.
undercroft: the codebase under the server room: board-formed concrete, the caged work lamp, the grate's light from
            above, the DO NOT DELETE column, the company's tower as a curtain-wall building (detail where cameras see it).
"""
import bpy, sys, os, math, json, bmesh, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_look as L
import screens_lib as SL
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index("--") + 1:]
AREA, NAME = ARGS[0], ARGS[1]
SHORT = os.path.join(L.BLENDER, "short")
OUT = os.path.join(SHORT, NAME + ".blend")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert not os.path.exists(OUT), "never save over an existing blend: " + OUT
bpy.ops.wm.save_as_mainfile(filepath=OUT)
O = bpy.data.objects
sc = bpy.context.scene


def wbox(o):
    mn = [min((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for i in range(3)]
    mx = [max((o.matrix_world @ Vector(c))[i] for c in o.bound_box) for i in range(3)]
    return mn, mx


def root(o):
    while o.parent:
        o = o.parent
    return o


KEEP_SCENE = {"server": {"cable", "clock_shelf", "clock_sb", "clock_sb7", "grate", "sched_txt", "crt", "crt_txt"},
              "undercroft": {"undercroft", "screw", "tag_dnd"}}[AREA]
KEEP_COLL = {"server": {"SERVER"}, "undercroft": {"CODEBASE"}}[AREA]
drop = []
for o in O:
    r = root(o)
    cols = {c.name for c in r.users_collection} | {c.name for c in o.users_collection}
    keep = bool(cols & KEEP_COLL) or r.name in KEEP_SCENE or r.name.startswith(tuple(k + "_" for k in KEEP_SCENE))
    if o.type in ("CAMERA", "LIGHT") or not keep:
        drop.append(o)
for o in drop:
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    if c.name not in KEEP_COLL and not c.objects and not c.children:
        bpy.data.collections.remove(c)
L.log("kept", len(O), "objects for", AREA)
NEW = L.coll("SET_%s_new" % AREA)
LIG = L.coll("LIGHTS_%s" % AREA)

M = {}
M["steel_dark"] = L.pbr("AFF_steel_dark_anodised", "metal_plate_02", scale=1.5, base=(0.05, 0.05, 0.055), tint_mix=0.3,
                        rough=(0.3, 0.5), metal=1.0, nstr=0.2)
M["rubber"] = L.pbr("AFF_rubber_black", "rubber_tiles", scale=8.0, base=(0.018, 0.018, 0.02), tint_mix=0.2,
                    rough=(0.55, 0.75), nstr=0.3)
M["paper"] = L.pbr("AFF_paper", "white_stucco", scale=10.0, base=(0.62, 0.60, 0.55), tint_mix=0.2, rough=(0.7, 0.9), nstr=0.05)

if AREA == "server":
    # ---------------------------------------------------------------- materials
    def perforated(nt, b, vec):
        # round perforations on a 6 mm pitch: dark, rough, recessed (bump), so the doors read as perforated steel
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (160, 160, 160)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = "F1"; vor.inputs["Randomness"].default_value = 0.0
        vor.voronoi_dimensions = "3D"
        nt.links.new(mp.outputs[0], vor.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.26; mr.inputs["From Max"].default_value = 0.30
        nt.links.new(vor.outputs["Distance"], mr.inputs["Value"])  # 0 in a hole, 1 on the steel
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        nt.links.new(mr.outputs[0], mix.inputs["Factor"])
        mix.inputs["A"].default_value = (0.003, 0.003, 0.004, 1)
        src = next((l.from_socket for l in nt.links if l.to_socket == b.inputs["Base Color"]), None)
        if src:
            nt.links.new(src, mix.inputs["B"])
        else:
            mix.inputs["B"].default_value = b.inputs["Base Color"].default_value
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.002
        nt.links.new(mr.outputs[0], bp.inputs["Height"])
        nsrc = next((l.from_socket for l in nt.links if l.to_socket == b.inputs["Normal"]), None)
        if nsrc:
            nt.links.new(nsrc, bp.inputs["Normal"])
        nt.links.new(bp.outputs[0], b.inputs["Normal"])

    M["rack_door"] = L.pbr("AFF_rack_door_perforated", "metal_plate_02", scale=1.2, base=(0.045, 0.048, 0.055),
                           tint_mix=0.35, rough=(0.35, 0.55), metal=0.8, nstr=0.25, extra=perforated)
    M["rack"] = L.pbr("AFF_rack_painted_steel", "metal_plate_02", scale=1.2, base=(0.035, 0.038, 0.045), tint_mix=0.4,
                      rough=(0.35, 0.6), metal=0.7, nstr=0.35)
    M["floor"] = L.pbr("AFF_srv_concrete_dusty", "concrete_floor_worn_001", scale=0.45, base=(0.15, 0.15, 0.15),
                       tint_mix=0.9, rough=(0.5, 0.9), nstr=0.7)
    M["wall"] = L.pbr("AFF_srv_wall", "painted_concrete_02", scale=0.4, base=(0.05, 0.06, 0.07), tint_mix=0.5,
                      rough=(0.7, 0.9), nstr=0.5)
    M["tray"] = L.pbr("AFF_galvanised_tray", "metal_plate_02", scale=2.0, base=(0.35, 0.36, 0.37), tint_mix=0.5,
                      rough=(0.3, 0.55), metal=1.0, nstr=0.3)
    M["diffuser_off"] = L.pbr("AFF_strip_diffuser_off", "white_stucco", scale=8.0, base=(0.25, 0.26, 0.27), tint_mix=0.1,
                              rough=(0.4, 0.5), nstr=0.05)
    M["tube_on"] = L.emissive("AFF_aisle_tube_cold", (0.86, 0.93, 1.0), 3.0, base=(0.8, 0.82, 0.85))
    M["laminate"] = L.pbr("AFF_desk_laminate", "wood_table_001", scale=1.6, tint=(0.75, 0.7, 0.65), rough=(0.35, 0.5),
                          nstr=0.25, coat=0.3, coat_rough=0.2)
    M["plastic"] = L.pbr("AFF_plastic_black", "rubber_tiles", scale=12.0, base=(0.02, 0.021, 0.024), tint_mix=0.1,
                         rough=(0.35, 0.5), nstr=0.05)
    M["beige"] = L.pbr("AFF_beige_server_case", "metal_plate_02", scale=2.0, base=(0.15, 0.135, 0.11), tint_mix=0.4,
                       rough=(0.4, 0.65), nstr=0.25)
    M["ceramic"] = L.pbr("AFF_mug_ceramic", "white_stucco", scale=14.0, base=(0.62, 0.60, 0.56), tint_mix=0.08,
                         rough=(0.12, 0.22), nstr=0.04, coat=0.6, coat_rough=0.05)
    M["sticky"] = L.pbr("AFF_sticky_note", "white_stucco", scale=14.0, base=(0.75, 0.62, 0.12), tint_mix=0.15,
                        rough=(0.7, 0.85), nstr=0.05)
    M["cabinet"] = L.pbr("AFF_filing_cabinet", "metal_plate_02", scale=2.0, base=(0.16, 0.17, 0.18), tint_mix=0.4,
                         rough=(0.35, 0.6), metal=0.6, nstr=0.3)
    M["acrylic"] = L.pbr("AFF_smoked_acrylic", "metal_plate_02", scale=10, base=(0.01, 0.005, 0.005), rough=(0.05, 0.12),
                         nstr=0.0, coat=1.0, coat_rough=0.02)
    M["led_green"] = L.emissive("AFF_led_green", (0.15, 1.0, 0.35), 30.0)
    M["led_blue"] = L.emissive("AFF_led_blue", (0.15, 0.55, 1.0), 25.0)
    M["led_amber"] = L.emissive("AFF_led_amber", (1.0, 0.45, 0.05), 25.0)
    M["led_red"] = L.emissive("AFF_led_red", (1.0, 0.05, 0.03), 25.0)
    M["clock_digits"] = L.emissive("AFF_clock_digits_red", (1.0, 0.06, 0.02), 4.5)
    M["screen_bg"] = L.emissive("AFF_monitor_bg", (0.06, 0.08, 0.11), 1.3)
    M["screen_text"] = L.emissive("AFF_monitor_text", (0.85, 0.92, 1.0), 4.0)
    M["lcd_bg"] = L.emissive("AFF_lcd_bg", (0.025, 0.07, 0.035), 1.0)
    M["lcd_text"] = L.emissive("AFF_lcd_text", (0.80, 1.0, 0.84), 12.0)

    def mat_for(o):
        n = o.name
        if n == "srv_floor": return M["floor"]
        if n.startswith("srv_"): return M["wall"]
        if "_door" in n and n.startswith("rack"): return M["rack_door"]
        if n.startswith("rack") and "_amber" in n: return M["led_amber"]
        if n.startswith("rack") and "_led" in n:
            h = sum(ord(c) * (i + 1) for i, c in enumerate(n)) % 11
            return M["led_blue"] if h < 3 else (M["led_amber"] if h == 3 else M["led_green"])
        if n.startswith("rack"): return M["rack"]
        if n.startswith("strip"): return M["tube_on"]
        if n.startswith("tray"): return M["tray"]
        if n.startswith(("floorcable", "hangcable", "cable")): return M["rubber"]
        if n == "tdesk_top": return M["laminate"]
        if n.startswith("tdesk_leg") or n == "clock_shelf": return M["steel_dark"]
        if n == "mon_screen": return M["screen_bg"]
        if n.startswith(("mon_", "kbd")): return M["plastic"]
        if n.startswith("ui_"): return M["screen_text"]
        if n == "mug": return M["ceramic"]
        if n == "clock_body" or (n.startswith("clock_sb") and o.type == "MESH"): return M["plastic"]
        if n == "clock_face": return M["acrylic"]
        if n.startswith("clock") and o.type == "FONT": return M["clock_digits"]
        if n in ("lg_lcd", "lg_lcd_on"): return M["lcd_bg"]
        if n in ("lg_msg", "sched_txt"): return M["lcd_text"]
        if n == "lg_beacon": return M["led_red"]
        if n == "lg_power": return M["led_green"]
        if n == "lg_sticky": return M["sticky"]
        if n.startswith("lg_") and o.type == "FONT": return M["paper"] if n == "lg_label" else M["plastic"]
        if n.startswith("lg_"): return M["beige"]
        if n.startswith("cab_note"): return M["sticky"] if o.type == "MESH" else M["plastic"]
        if n.startswith(("cab_lab",)): return M["paper"] if o.type == "MESH" else M["plastic"]
        if n.startswith("cab_"): return M["cabinet"]
        if n == "st_green": return M["led_green"]
        if n == "st_red": return M["led_red"]
        if n.startswith("st_"): return M["steel_dark"]
        if n == "baby_led_g": return M["led_green"]
        if n == "grate": return M["steel_dark"]
        if o.type == "FONT": return M["plastic"]
        return None
else:
    # ---------------------------------------------------------------- undercroft materials
    def board_formed(nt, b, vec):
        # board-formed lines: 150 mm boards (horizontal), each board a slightly different tone, a recessed joint
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
        mz = nt.nodes.new("ShaderNodeMath"); mz.operation = "MULTIPLY"; mz.inputs[1].default_value = 1 / 0.15
        nt.links.new(sep.outputs["Z"], mz.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"; nt.links.new(mz.outputs[0], fr.inputs[0])
        fl = nt.nodes.new("ShaderNodeMath"); fl.operation = "FLOOR"; nt.links.new(mz.outputs[0], fl.inputs[0])
        wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "1D"; nt.links.new(fl.outputs[0], wn.inputs["W"])
        jt = nt.nodes.new("ShaderNodeMapRange")
        jt.inputs["From Min"].default_value = 0.0; jt.inputs["From Max"].default_value = 0.06
        nt.links.new(fr.outputs[0], jt.inputs["Value"])
        tone = nt.nodes.new("ShaderNodeMapRange"); tone.inputs["To Min"].default_value = 0.8; tone.inputs["To Max"].default_value = 1.15
        nt.links.new(wn.outputs["Value"], tone.inputs["Value"])
        src = next((l.from_socket for l in nt.links if l.to_socket == b.inputs["Base Color"]), None)
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1
        if src: nt.links.new(src, mul.inputs["A"])
        nt.links.new(tone.outputs[0], mul.inputs["B"])
        nt.links.new(mul.outputs["Result"], b.inputs["Base Color"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.inputs["Distance"].default_value = 0.004
        nt.links.new(jt.outputs[0], bp.inputs["Height"])
        nsrc = next((l.from_socket for l in nt.links if l.to_socket == b.inputs["Normal"]), None)
        if nsrc: nt.links.new(nsrc, bp.inputs["Normal"])
        nt.links.new(bp.outputs[0], b.inputs["Normal"])

    def wet(nt, b, vec):
        # wet patches: a low-frequency noise mask drops the roughness to a puddle sheen and darkens the albedo
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 4
        nt.links.new(vec, nz.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.52; mr.inputs["From Max"].default_value = 0.6
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        rsrc = next((l.from_socket for l in nt.links if l.to_socket == b.inputs["Roughness"]), None)
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "FLOAT"
        nt.links.new(mr.outputs[0], mx.inputs["Factor"])
        if rsrc: nt.links.new(rsrc, mx.inputs["A"])
        mx.inputs["B"].default_value = 0.06
        nt.links.new(mx.outputs["Result"], b.inputs["Roughness"])
        csrc = next((l.from_socket for l in nt.links if l.to_socket == b.inputs["Base Color"]), None)
        dk = nt.nodes.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.blend_type = "MULTIPLY"
        nt.links.new(mr.outputs[0], dk.inputs["Factor"])
        if csrc: nt.links.new(csrc, dk.inputs["A"])
        dk.inputs["B"].default_value = (0.55, 0.55, 0.55, 1)
        nt.links.new(dk.outputs["Result"], b.inputs["Base Color"])

    M["wall"] = L.pbr("AFF_board_formed_concrete", "concrete_wall_006", scale=0.5, base=(0.23, 0.23, 0.235), tint_mix=0.9,
                      rough=(0.7, 0.95), nstr=0.9, extra=board_formed)
    M["floor"] = L.pbr("AFF_undercroft_floor_wet", "concrete_floor_damaged_01", scale=0.4, base=(0.2, 0.2, 0.2),
                       tint_mix=0.9, rough=(0.55, 0.9), nstr=0.8, extra=wet)
    M["ceiling"] = L.pbr("AFF_undercroft_ceiling", "concrete_wall_006", scale=0.4, base=(0.14, 0.14, 0.145), tint_mix=0.8,
                         rough=(0.75, 0.95), nstr=0.7, extra=board_formed)
    M["column"] = L.pbr("AFF_column_cast_concrete", "rebar_reinforced_concrete", scale=6.0, base=(0.42, 0.41, 0.40),
                        tint_mix=0.8, rough=(0.6, 0.9), nstr=0.7)
    M["rust"] = L.pbr("AFF_rebar_rust", "rust_coarse_01", scale=4.0, rough=(0.6, 0.9), metal=0.3, nstr=0.6)
    M["steel"] = L.pbr("AFF_structural_steel", "metal_plate_02", scale=3.0, base=(0.18, 0.18, 0.19), tint_mix=0.5,
                       rough=(0.3, 0.55), metal=1.0, nstr=0.3)
    M["mullion"] = L.pbr("AFF_tower_mullion", "metal_plate_02", scale=8.0, base=(0.12, 0.125, 0.13), tint_mix=0.3,
                         rough=(0.25, 0.4), metal=1.0, nstr=0.1)
    M["slab"] = L.pbr("AFF_tower_slab_edge", "concrete_wall_006", scale=6.0, base=(0.32, 0.32, 0.33), tint_mix=0.5,
                      rough=(0.6, 0.85), nstr=0.4)
    M["tag"] = L.pbr("AFF_paper_tag_yellow", "white_stucco", scale=24.0, base=(0.80, 0.62, 0.08), tint_mix=0.15,
                     rough=(0.75, 0.9), nstr=0.08)
    M["ink"] = L.pbr("AFF_tag_ink", "white_stucco", scale=30.0, base=(0.008, 0.007, 0.006), tint_mix=0.1, rough=(0.5, 0.6),
                     nstr=0.0)
    M["bulb"] = L.emissive("AFF_bulb_tungsten", (1.0, 0.55, 0.22), 16.0, base=(0.9, 0.8, 0.6))
    M["aviation"] = L.emissive("AFF_aviation_red", (1.0, 0.04, 0.02), 30.0)

    # tower glass: dark reflective curtain-wall glass; ~40% of the window cells lit warm (a few cool), uneven
    def tower_glass():
        m, nt = L._new_mat("AFF_tower_curtainwall_glass")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        b.inputs["Base Color"].default_value = (0.012, 0.016, 0.02, 1)
        b.inputs["Roughness"].default_value = 0.12
        b.inputs["Metallic"].default_value = 0.0
        b.inputs["Specular IOR Level"].default_value = 0.5
        b.inputs["Coat Weight"].default_value = 0.4; b.inputs["Coat Roughness"].default_value = 0.05
        tc = nt.nodes.new("ShaderNodeTexCoord"); oi = nt.nodes.new("ShaderNodeObjectInfo")
        sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
        # one cell per bay (the mullion pitch) per floor: x and y bays, the floor's own random as the 3rd axis
        bx = nt.nodes.new("ShaderNodeMath"); bx.operation = "MULTIPLY"; bx.inputs[1].default_value = 1 / 0.115
        nt.links.new(sx.outputs["X"], bx.inputs[0])
        by = nt.nodes.new("ShaderNodeMath"); by.operation = "MULTIPLY"; by.inputs[1].default_value = 1 / 0.115
        nt.links.new(sx.outputs["Y"], by.inputs[0])
        cmb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(bx.outputs[0], cmb.inputs["X"]); nt.links.new(by.outputs[0], cmb.inputs["Y"])
        r100 = nt.nodes.new("ShaderNodeMath"); r100.operation = "MULTIPLY"; r100.inputs[1].default_value = 100.0
        nt.links.new(oi.outputs["Random"], r100.inputs[0]); nt.links.new(r100.outputs[0], cmb.inputs["Z"])
        fl = nt.nodes.new("ShaderNodeVectorMath"); fl.operation = "FLOOR"; nt.links.new(cmb.outputs[0], fl.inputs[0])
        wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"; nt.links.new(fl.outputs[0], wn.inputs["Vector"])
        sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(wn.outputs["Color"], sp.inputs[0])
        # lit offices come in runs along a floor: a slow noise along the bays decides, the per-bay random breaks it up
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 1
        nt.links.new(cmb.outputs[0], nz.inputs["Vector"])
        mixr = nt.nodes.new("ShaderNodeMix"); mixr.data_type = "FLOAT"; mixr.inputs["Factor"].default_value = 0.35
        nt.links.new(nz.outputs["Fac"], mixr.inputs["A"]); nt.links.new(sp.outputs[0], mixr.inputs["B"])
        lit = nt.nodes.new("ShaderNodeMath"); lit.operation = "GREATER_THAN"; lit.inputs[1].default_value = 0.52
        nt.links.new(mixr.outputs["Result"], lit.inputs[0])
        lvl = nt.nodes.new("ShaderNodeMapRange"); lvl.inputs["To Min"].default_value = 0.5; lvl.inputs["To Max"].default_value = 1.8
        nt.links.new(sp.outputs[1], lvl.inputs["Value"])
        # the ceiling-light band: brightest near the top of each floor, falling to the floor (generated z 0..1 per floor)
        gz = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], gz.inputs[0])
        band = nt.nodes.new("ShaderNodeMapRange"); band.inputs["From Min"].default_value = 0.05
        band.inputs["From Max"].default_value = 0.92; band.inputs["To Min"].default_value = 0.35; band.inputs["To Max"].default_value = 1.0
        band.interpolation_type = "SMOOTHSTEP"
        nt.links.new(gz.outputs["Z"], band.inputs["Value"])
        st = nt.nodes.new("ShaderNodeMath"); st.operation = "MULTIPLY"
        nt.links.new(lit.outputs[0], st.inputs[0]); nt.links.new(lvl.outputs[0], st.inputs[1])
        st2 = nt.nodes.new("ShaderNodeMath"); st2.operation = "MULTIPLY"
        nt.links.new(st.outputs[0], st2.inputs[0]); nt.links.new(band.outputs[0], st2.inputs[1])
        cool = nt.nodes.new("ShaderNodeMath"); cool.operation = "LESS_THAN"; cool.inputs[1].default_value = 0.14
        nt.links.new(sp.outputs[2], cool.inputs[0])
        cm = nt.nodes.new("ShaderNodeMix"); cm.data_type = "RGBA"
        nt.links.new(cool.outputs[0], cm.inputs["Factor"])
        cm.inputs["A"].default_value = (1.0, 0.52, 0.18, 1); cm.inputs["B"].default_value = (0.70, 0.84, 1.0, 1)
        nt.links.new(cm.outputs["Result"], b.inputs["Emission Color"])
        nt.links.new(st2.outputs[0], b.inputs["Emission Strength"])
        # the floor boxes' top and bottom faces are soffits, not glass: plain dark concrete, no emission, no mirror
        # (they showed as blocky white cells from below; CD 10.7 L1)
        sn = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Normal"], sn.inputs[0])
        az = nt.nodes.new("ShaderNodeMath"); az.operation = "ABSOLUTE"; nt.links.new(sn.outputs["Z"], az.inputs[0])
        horiz = nt.nodes.new("ShaderNodeMath"); horiz.operation = "GREATER_THAN"; horiz.inputs[1].default_value = 0.5
        nt.links.new(az.outputs[0], horiz.inputs[0])
        conc = nt.nodes.new("ShaderNodeBsdfPrincipled")
        conc.inputs["Base Color"].default_value = (0.20, 0.195, 0.19, 1); conc.inputs["Roughness"].default_value = 0.85
        conc.inputs["Specular IOR Level"].default_value = 0.2
        ms = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(horiz.outputs[0], ms.inputs[0]); nt.links.new(b.outputs[0], ms.inputs[1]); nt.links.new(conc.outputs[0], ms.inputs[2])
        nt.links.new(ms.outputs[0], out.inputs["Surface"])
        m["look"] = "light (lit windows)"
        return m
    M["tower_glass"] = tower_glass()

    def mat_for(o):
        n = o.name
        if n == "undercroft_p0": return M["floor"]
        if n == "undercroft_p5": return M["ceiling"]
        if n in ("undercroft_p1", "undercroft_p2", "undercroft_p3", "undercroft_p4"): return M["wall"]
        if n == "undercroft_p6": return M["steel"]
        if n == "undercroft_p7": return M["steel"]
        if n in ("dnd_column",): return M["column"]
        if n in ("dnd_base", "dnd_cap"): return M["column"]
        if n == "dnd_tag": return M["tag"]
        if n == "dnd_txt": return M["ink"]
        if n.startswith("cb_floor"): return M["tower_glass"]
        if n.startswith("cb_slab"): return M["slab"]
        if n.startswith(("cb_stalk", "cb_antenna")): return M["steel"]
        if n == "screw": return M["steel"]
        return None

unmatched = []
for o in O:
    if o.type not in ("MESH", "CURVE", "FONT"):
        continue
    m = mat_for(o)
    if m is None:
        m = M["steel_dark"]; unmatched.append(o.name)
    L.assign(o, m)
    L.apply_scale(o)
L.log("unmatched -> dark steel:", unmatched[:50], len(unmatched))

if AREA == "server":
    # ---------------------------------------------------------------- the grate: real bars, and the warm pit below it
    g = O.get("grate")
    if g:
        mn, mx = wbox(g)
        me = bpy.data.meshes.new("grate_bars"); bm = bmesh.new()
        frame_w, bar = 0.03, 0.008
        def cube(a, b_):
            r = bmesh.ops.create_cube(bm, size=1.0)
            for v in r["verts"]:
                v.co = Vector([(a[i] + b_[i]) / 2 + v.co[i] * (b_[i] - a[i]) for i in range(3)])
        z0, z1 = -0.03, 0.0
        cube((mn[0], mn[1], z0), (mx[0], mn[1] + frame_w, z1)); cube((mn[0], mx[1] - frame_w, z0), (mx[0], mx[1], z1))
        cube((mn[0], mn[1], z0), (mn[0] + frame_w, mx[1], z1)); cube((mx[0] - frame_w, mn[1], z0), (mx[0], mx[1], z1))
        x = mn[0] + frame_w + 0.025
        while x < mx[0] - frame_w:
            cube((x, mn[1], z0 + 0.004), (x + bar, mx[1], z1 - 0.001)); x += 0.033
        y = mn[1] + frame_w + 0.06
        while y < mx[1] - frame_w:
            cube((mn[0], y, z0 + 0.012), (mx[0], y + 0.006, z1 - 0.012)); y += 0.1
        bm.to_mesh(me); bm.free()
        gb = bpy.data.objects.new("grate_bars", me); NEW.objects.link(gb)
        gb.parent = g; gb.matrix_parent_inverse = g.matrix_world.inverted()
        me.materials.append(M["steel_dark"])
        g.data = bpy.data.meshes.new('grate_empty')   # the stand-in plate's faces go (its keyed visibility would bring them
        # back); the object stays as the bars' parent so they keep its animation
        # a real opening in the floor (the floor plane covered the bars and the pit: f768 showed plain floor)
        fl = O.get("srv_floor")
        if fl:
            fmn, fmx = wbox(fl)
            z = fmx[2]
            me = bpy.data.meshes.new("srv_floor_holed"); bm2 = bmesh.new()
            hx0, hy0, hx1, hy1 = mn[0], mn[1], mx[0], mx[1]
            rects = [((fmn[0], fmn[1]), (fmx[0], hy0)), ((fmn[0], hy1), (fmx[0], fmx[1])),
                     ((fmn[0], hy0), (hx0, hy1)), ((hx1, hy0), (fmx[0], hy1))]
            for (x0, y0), (x1, y1) in rects:
                vs = [bm2.verts.new((x0, y0, z)), bm2.verts.new((x1, y0, z)), bm2.verts.new((x1, y1, z)), bm2.verts.new((x0, y1, z))]
                bm2.faces.new(vs)
            bm2.to_mesh(me); bm2.free()
            for m_ in fl.data.materials: me.materials.append(m_)
            fl.data = me; fl.matrix_world = Matrix.Identity(4)
        pit = L.box("grate_pit", (mn[0] - 0.02, mn[1] - 0.02, -1.2), (mx[0] + 0.02, mx[1] + 0.02, -0.031), None, NEW)
        pm = L.pbr("AFF_pit_concrete", "concrete_wall_006", scale=1.0, base=(0.2, 0.2, 0.2), rough=(0.7, 0.95), nstr=0.8)
        pit.data.materials.append(pm)
        # the pit's inside faces only: flip normals so we see the walls from inside
        bm = bmesh.new(); bm.from_mesh(pit.data)
        for f in bm.faces:
            f.normal_flip()
        top = [f for f in bm.faces if f.calc_center_median().z > -0.05]
        bmesh.ops.delete(bm, geom=top, context="FACES")
        bm.to_mesh(pit.data); bm.free()
        # sodium work light far below, seen through the bars (the undercroft's lamp)
        L.light("L_pit_sodium", "POINT", ((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, -1.0), 8.0, temp=2200, soft=0.2,
                coll=LIG, dist=2.5)
    # ---------------------------------------------------------------- the clock shelf: a thin steel board, same top
    # (the locked layout's 30 mm stand-in board met his spikes by 15 mm at f713-755; 10 mm steel keeps the clock where
    # the camera expects it and clears them)
    sh = O.get("clock_shelf")
    if sh:
        mn, mx = wbox(sh)
        # the board's underside at >= 1.432 m (producer 16:35: his tallest spike tops out at 1.41 f713-755); the clock rides up with it
        LIFT = max(0.0, (1.432 + 0.006) - mx[2])
        for gn in ("clock_sb", "clock_sb7"):
            g = O.get(gn)
            if g:
                g.delta_location.z += LIFT     # location is keyed: lift through the delta
        mx[2] += LIFT
        L.log("clock shelf lifted", round(LIFT, 3), "board", round(mx[2] - 0.006, 3), "-", round(mx[2], 3))
        nb = L.box("clock_shelf_steel", (mn[0], mn[1], mx[2] - 0.006), (mx[0], mx[1], mx[2]), M["steel_dark"], NEW, bevel=0.0015)
        sh.data = bpy.data.meshes.new("clock_shelf_off")
        L.box("clock_shelf_bracket_L", (mn[0] + 0.03, mx[1] - 0.012, mx[2] - 0.12), (mn[0] + 0.045, mx[1], mx[2] - 0.006), M["steel_dark"], NEW)
        L.box("clock_shelf_bracket_R", (mx[0] - 0.045, mx[1] - 0.012, mx[2] - 0.12), (mx[0] - 0.03, mx[1], mx[2] - 0.006), M["steel_dark"], NEW)
    # ---------------------------------------------------------------- the design's screens (CD 13.2, SPEC §2), on the
    # blocking's LOCK 7 stand-ins: the 7-segment clock panel and the SCHEDULED JOBS CRT on top of LEGACY-01
    def _facing(o_txt):
        n_ = (o_txt.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized(); n_.z = 0
        return n_.normalized()

    def _extent(o, c, n):
        return max((o.matrix_world @ Vector(b) - c).dot(n) for b in o.bound_box)

    def _follow(obs, parent):
        if parent is None: return
        bpy.context.view_layer.update()
        for o_ in obs:
            mw = o_.matrix_world.copy(); o_.parent = parent; o_.matrix_world = mw

    cp = O.get("clock_sb_p0"); ct = O.get("clock_sb_t1")
    if cp and ct:
        bpy.context.view_layer.update()
        n = _facing(ct)
        mn, mx = wbox(cp); c = Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
        cf = c + n * (_extent(cp, c, n) + 0.0015)
        imc, rngc = SL._img("clock", seq=(573, 768))
        cm = SL.material("AFF_clock_panel", "clock", imc, rngc, strength=float(os.environ.get("AFF_CLOCK_S", "9")))
        pf = SL.plane("clock_face_panel", tuple(cf), 0.180, 0.140, tuple(n), NEW, cm)
        # the scuffed steel case behind it, down to the shelf (no float)
        sh_top = wbox(O["clock_shelf"])[1][2] if O.get("clock_shelf") else mn[2]
        right = Vector((0, 0, 1)).cross(n).normalized()
        M["clock_steel"] = L.pbr("AFF_clock_steel_scuffed", "metal_plate_02", scale=9.0, base=(0.10, 0.10, 0.105), tint_mix=0.6,
                                 rough=(0.3, 0.55), nstr=0.25)
        cs_ = L.box("clock_case", (-0.096, 0.0005, sh_top - cf.z), (0.096, 0.07, 0.078), M["clock_steel"], NEW, bevel=0.006)   # behind the face (local +y = -n)
        R = Matrix((right, -n, Vector((0, 0, 1)))).transposed()
        cs_.matrix_world = Matrix.Translation(cf - n * 0.001) @ R.to_4x4()
        for gn in ("clock_sb", "clock_sb7"):
            for ch in O:
                if ch.parent and ch.parent.name == gn:
                    if ch.type == "MESH": ch.data = bpy.data.meshes.new(ch.name + "_off")
                    if ch.type == "FONT": ch.data.body = " "
        _follow([pf, cs_], O.get("clock_sb"))
        lc = L.light("L_clock_leds", "AREA", tuple(cf + n * 0.02), 1.6, color=(1.0, 0.22, 0.06), size=(0.16, 0.06), coll=LIG, dist=1.2)
        L.aim(lc, cf + n * 1.0)
        L.log("clock panel", tuple(round(x, 3) for x in cf), "facing", tuple(round(x, 2) for x in n), "case from z", round(sh_top, 3))
    crt = O.get("crt_p1"); crt_t = O.get("crt_txt_t1")
    if crt and crt_t:
        n = _facing(crt_t)
        mn, mx = wbox(crt); c = Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
        cf = c + n * (_extent(crt, c, n) + 0.002)
        ims, rngs = SL._img("sched", seq=(573, 768))
        smat = SL.material("AFF_sched_crt", "display", ims, rngs, strength=float(os.environ.get("AFF_SCHED_S", "0.9")))
        sf = SL.plane("crt_face", tuple(cf), 0.70, 0.50, tuple(n), NEW, smat)
        # the stand-ins: the body box stays as the CRT's case (bevelled, beige-grey plastic); the screen box and text go
        body = O.get("crt_p0")
        M["crt_plastic"] = L.pbr("AFF_crt_plastic", "rubber_tiles", scale=14.0, base=(0.20, 0.19, 0.17), tint_mix=0.7,
                                 rough=(0.45, 0.6), nstr=0.15)
        if body:
            L.assign(body, M["crt_plastic"]); bv = body.modifiers.new("bevel", "BEVEL"); bv.width = 0.02; bv.segments = 3
        crt.data = bpy.data.meshes.new("crt_p1_off")
        for o_ in O:
            if o_.name.startswith("crt_txt_t") and o_.type == "FONT": o_.data.body = " "
        _follow([sf], O.get("crt"))
        # the terminal's amber light: off until the ping (f728), 3-frame warm-up, like the texture
        ls = L.light("L_crt", "AREA", tuple(cf + n * 0.03), 1.0, color=(1.0, 0.62, 0.18), size=(0.66, 0.46), coll=LIG, dist=2.5)
        L.aim(ls, cf + n * 1.0); _follow([ls], O.get("crt"))
        for f_, e_ in ((727, 0.0), (728, 1.5), (730, 4.0), (731, 6.0)):
            ls.data.energy = e_; ls.data.keyframe_insert("energy", frame=f_)
        for fc in L.fcurves_of(ls.data):
            for k in fc.keyframe_points: k.interpolation = "LINEAR"
        for n_ in ("sched_txt", "lg_lcd", "lg_lcd_on", "lg_msg"):
            o = O.get(n_)
            if o and o.type == "FONT": o.data.body = " "
        L.log("CRT face", tuple(round(x, 3) for x in cf), "facing", tuple(round(x, 2) for x in n))
    for o_ in [o for o in O if o.type == "FONT" and (o.name.startswith(("crt_txt_t", "clock_sb_t", "clock_sb7_t")) if O.get("crt_face") else False)]:
        bpy.data.objects.remove(o_, do_unlink=True)     # the stand-ins' text: ours replaces it
    # ---------------------------------------------------------------- the scheduler, on the legacy server's front panel
    # (the pre-LOCK 7 version, only when the blocking has no CRT stand-in)
    bz = O.get("lg_bezel")
    if bz and not O.get("crt_p1"):
        import math as _m
        EXP = os.path.join(HERE, "..", "blocking", "export", "short_cams.json")
        rows = {r["f"]: r["9x16"] for r in json.load(open(EXP))["frames"] if 740 <= r["f"] <= 756}
        # placed and turned like the blocking's LOCK 2 stand-in `sched_txt` (it faces the OTS camera), on the server front
        st_ = O.get("sched_txt")
        if st_:
            nrm = (st_.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized(); nrm.z = 0; nrm.normalize()
            up_ = Vector((0, 0, 1)); right = up_.cross(nrm).normalized()
            R = Matrix((right, -nrm, up_)).transposed()
            c0 = st_.matrix_world.translation.copy() + nrm * 0.012
        else:
            R = bz.matrix_world.to_3x3().normalized()
            nrm = (R @ Vector((0, -1, 0))).normalized(); right = (R @ Vector((1, 0, 0))).normalized()
            c0 = bz.matrix_world.translation + nrm * 0.022 + right * 0.05 + Vector((0, 0, 0.30))
        L.log("scheduler panel centre", tuple(round(x, 3) for x in c0), "normal", tuple(round(x, 3) for x in nrm))
        def px_per_m(f):
            r = rows[f]; d = (Vector(r["loc"]) - c0).length
            return 1920 / (2 * d * _m.tan(_m.radians(r["vfov_deg"]) / 2))
        ppm = min(px_per_m(f) for f in rows) if rows else 900.0
        cap_main = 46 / ppm; cap_small = 27 / ppm             # >= 58 px type (cap 42) and >= 34 px type (cap 25), + margin
        W, Hh = 0.38, 0.27
        scr = L.box("sched_panel", (-W / 2, -0.004, -Hh / 2), (W / 2, 0.004, Hh / 2), M["lcd_bg"], NEW)
        scr.matrix_world = Matrix.Translation(c0) @ R.to_4x4()
        bez = L.box("sched_panel_bezel", (-W / 2 - 0.02, 0.004, -Hh / 2 - 0.02), (W / 2 + 0.02, 0.055, Hh / 2 + 0.02), M["plastic"], NEW)
        bez.matrix_world = scr.matrix_world.copy()
        fp = os.path.join(L.HOME_ROOT, "Projects/deadletter-studio/assets/fonts/Anton-Regular.ttf")
        lines = [("SCHEDULED JOBS", cap_small, 0.088), ("0 jobs", cap_main * 1.3, 0.0), ("scheduled", cap_main, -0.085)]
        for k, (body, cap, dz) in enumerate(lines):
            bpy.ops.object.text_add()
            t = bpy.context.active_object; t.name = f"sched_line{k}"
            for c in t.users_collection: c.objects.unlink(t)
            NEW.objects.link(t)
            t.data.body = body; t.data.align_x = "CENTER"; t.data.align_y = "CENTER"
            if os.path.exists(fp): t.data.font = bpy.data.fonts.load(fp, check_existing=True)
            t.data.size = cap / 0.72          # Anton's cap height is ~0.72 em
            t.matrix_world = Matrix.Translation(c0 + nrm * 0.0055 + Vector((0, 0, dz))) @ R.to_4x4() @ Matrix.Rotation(_m.radians(90), 4, "X")
            L.assign(t, M["lcd_text"])
        bpy.context.view_layer.update()
        L.log("scheduler panel px/m", round(ppm), "cap main m", round(cap_main, 4), "widths", [round(O[f"sched_line{k}"].dimensions.x, 3) for k in range(3)])
        for n in ("sched_txt", "lg_lcd", "lg_lcd_on", "lg_msg"):
            o = O.get(n)
            if o and o.type in ("MESH", "FONT"):
                o.data = bpy.data.meshes.new(n + "_off") if o.type == "MESH" else o.data
                if o.type == "FONT": o.data.body = " "
    # ---------------------------------------------------------------- steam from the mug (a thin wisp, a volume)
    mg = O.get("mug")
    if mg:
        mn, mx = wbox(mg)
        st = L.box("mug_steam", (mn[0] - 0.01, mn[1] - 0.01, mx[2] - 0.005), (mx[0] + 0.01, mx[1] + 0.01, mx[2] + 0.16), None, NEW)
        sm, nt = L._new_mat("AFF_steam")
        out = nt.nodes.new("ShaderNodeOutputMaterial"); pv = nt.nodes.new("ShaderNodeVolumePrincipled")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (40, 40, 14)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        # rising: the noise drifts up with the frame (driver on the mapping's Z location, a pure function of time)
        dr = mp.inputs["Location"].driver_add("default_value", 2).driver
        dr.expression = "-frame*0.012"
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 3
        nt.links.new(mp.outputs[0], nz.inputs["Vector"])
        gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
        mg2 = nt.nodes.new("ShaderNodeMapping"); mg2.inputs["Scale"].default_value = (1.0, 1.0, 0.35)
        nt.links.new(tc.outputs["Generated"], mg2.inputs["Vector"])
        mg2.inputs["Location"].default_value = (-0.5, -0.5, -0.17)
        mg2.inputs["Scale"].default_value = (2.0, 2.0, 0.7)
        nt.links.new(mg2.outputs[0], gr.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.55; mr.inputs["From Max"].default_value = 0.75
        mr.inputs["To Max"].default_value = 3.0
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        nt.links.new(mr.outputs[0], mul.inputs[0]); nt.links.new(gr.outputs["Fac"], mul.inputs[1])
        nt.links.new(mul.outputs[0], pv.inputs["Density"])
        pv.inputs["Color"].default_value = (0.9, 0.9, 0.9, 1)
        nt.links.new(pv.outputs[0], out.inputs["Volume"])
        st.data.materials.append(sm); st.visible_shadow = False
        st.parent = mg; st.matrix_parent_inverse = mg.matrix_world.inverted()   # the steam rides the mug
    # ---------------------------------------------------------------- lights (only real sources)
    ms = O.get("mon_screen")
    if ms:
        mn, mx = wbox(ms)
        a = L.light("L_monitor", "AREA", ((mn[0] + mx[0]) / 2, mn[1] - 0.01, (mn[2] + mx[2]) / 2), float(os.environ.get("AFF_MON_W", "40")),
                    color=(0.78, 0.86, 1.0), size=(mx[0] - mn[0], mx[2] - mn[2]), rot=(90, 0, 180), coll=LIG, dist=1.6)
        a.data.spread = math.radians(70)   # a monitor's light falls off sideways: his face, not the room behind him
    # the clock's digits light the air in front of them (the locked clock_sb/clock_sb7 stand-ins face +0.90,+0.44)
    for gname in (() if O.get("clock_face_panel") else ("clock_sb", "clock_sb7")):
        g = O.get(gname)
        if g:
            d = Vector((0.90, 0.44, 0.0)).normalized()
            a = L.light("L_" + gname + "_digits", "AREA", tuple(g.matrix_world.translation + d * 0.06), 1.2,
                        color=(1.0, 0.08, 0.03), size=(0.14, 0.06), coll=LIG, dist=1.2)
            L.aim(a, g.matrix_world.translation + d * 1.0)
            a.parent = g; a.matrix_parent_inverse = g.matrix_world.inverted()
            break   # both clocks sit at one spot (3:06 to f707, 3:07 from f708): one light
    bc = O.get("lg_beacon")
    if bc:
        mn, mx = wbox(bc)
        L.light("L_red_warning", "POINT", ((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mx[2] + 0.02), 22.0,
                color=(1.0, 0.04, 0.02), soft=0.04, coll=LIG, dist=4.0)
    lc = O.get("lg_lcd")
    if lc:
        mn, mx = wbox(lc)
        L.light("L_lcd", "AREA", ((mn[0] + mx[0]) / 2, mx[1] + 0.01, (mn[2] + mx[2]) / 2), 0.4, color=(0.55, 1.0, 0.6),
                size=(mx[0] - mn[0], mx[2] - mn[2]), rot=(-90, 0, 0), coll=LIG, dist=1.2)
    sg = O.get("st_green")
    if sg:
        mn, mx = wbox(sg)
        L.light("L_status_green", "POINT", ((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mx[2] + 0.01), 1.2,
                color=(0.2, 1.0, 0.45), soft=0.02, coll=LIG, dist=1.5)
    # the rack LED banks spill into the aisle: one low area light per rack face (the LEDs' own light), green/blue
    for o in list(O):
        if o.name.startswith(("rackA_", "rackB_", "rackC_")) and o.name.endswith("_door"):
            mn, mx = wbox(o)
            face_y = mn[1] if o.name.startswith(("rackA", "rackB")) else mx[1]
            sgn = -1 if o.name.startswith(("rackA", "rackB")) else 1
            h = sum(ord(c) for c in o.name) % 5
            col = (0.25, 0.6, 1.0) if h == 0 else (0.25, 1.0, 0.5)
            L.light("L_" + o.name, "AREA", ((mn[0] + mx[0]) / 2, face_y + sgn * 0.02, 1.0), 3.0, color=col,
                    size=(0.35, 1.5), rot=(90, 0, 180 if sgn < 0 else 0), coll=LIG, dist=3.0, shadow=False)
    # the aisle tubes (CD 13.1): a dim cold-white row on the ceiling, visible in the wides, so the racks read as objects
    for o in list(O):
        if o.name.startswith("strip") and o.type == "MESH":
            mn, mx = wbox(o)
            a_ = L.light("L_" + o.name + "_tube", "AREA", ((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2] - 0.01),
                         float(os.environ.get("AFF_TUBE_W", "35")), color=(0.86, 0.93, 1.0), size=(mx[0] - mn[0], 0.12), coll=LIG)
            a_.data.spread = math.radians(120)
    # haze in the room, lit only by those sources
    hz = L.box("srv_haze", (-7.9, -4.9, 0.0), (7.9, 7.9, 3.39), None, NEW)
    hm, nt = L._new_mat("AFF_haze_server")
    out = nt.nodes.new("ShaderNodeOutputMaterial"); pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 0.05; pv.inputs["Anisotropy"].default_value = 0.5
    nt.links.new(pv.outputs[0], out.inputs["Volume"]); hz.data.materials.append(hm); hz.visible_shadow = False
    # status lights on the hanging cables (cable status lights crossing near the lens)
    random.seed(7)
    for o in list(O):
        if o.name.startswith("hangcable") and o.type == "CURVE":
            sp = o.data.splines[0]
            pts = [o.matrix_world @ (p.co.xyz if hasattr(p, "co") else p.co) for p in (sp.bezier_points or sp.points)]
            for i, p in enumerate(pts[1:-1]):
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=p, segments=12, ring_count=6)
                s = bpy.context.active_object; s.name = f"cable_led_{o.name}_{i}"
                for c in s.users_collection: c.objects.unlink(s)
                NEW.objects.link(s)
                L.assign(s, M["led_green"] if random.random() > 0.2 else M["led_blue"])
else:
    # ---------------------------------------------------------------- the tower as a curtain-wall building
    tilt = O.get("CB_tilt")
    floors = sorted([o for o in O if o.name.startswith("cb_floor") and o.type == "MESH" and o.name[8:].isdigit()],
                    key=lambda o: int(o.name[8:]))
    MUL = 0.115   # mullion pitch (the window cell width the glass shader also uses)
    for fo in floors:
        # glass stays on the floor box; vertical mullions + a spandrel band per floor, as one mesh in the tilt's space
        mn, mx = wbox(fo)
        me = bpy.data.meshes.new(fo.name + "_mullions"); bm = bmesh.new()
        def cube(a, b_):
            r = bmesh.ops.create_cube(bm, size=1.0)
            for v in r["verts"]:
                v.co = Vector([(a[i] + b_[i]) / 2 + v.co[i] * (b_[i] - a[i]) for i in range(3)])
        d, w = 0.022, 0.012
        for side in range(4):
            if side in (0, 1):   # faces at y = mn / mx, mullions along x
                yy = mn[1] if side == 0 else mx[1]
                x = mn[0]
                while x <= mx[0] + 1e-6:
                    y0 = yy - d if side == 0 else yy
                    cube((x - w / 2, y0, mn[2]), (x + w / 2, y0 + d, mx[2])); x += MUL
            else:
                xx = mn[0] if side == 2 else mx[0]
                y = mn[1]
                while y <= mx[1] + 1e-6:
                    x0 = xx - d if side == 2 else xx
                    cube((x0, y - w / 2, mn[2]), (x0 + d, y + w / 2, mx[2])); y += MUL
        # spandrel: a dark metal band at the bottom of each floor, and a horizontal transom at 2/3 height
        cube((mn[0] - d, mn[1] - d, mn[2]), (mx[0] + d, mx[1] + d, mn[2] + 0.07))
        cube((mn[0] - d * 0.6, mn[1] - d * 0.6, mn[2] + 0.52), (mx[0] + d * 0.6, mx[1] + d * 0.6, mn[2] + 0.53))
        bm.to_mesh(me); bm.free()
        mo = bpy.data.objects.new(fo.name + "_mullions", me); NEW.objects.link(mo)
        me.materials.append(M["mullion"])
        mo.parent = tilt; mo.matrix_parent_inverse = tilt.matrix_world.inverted()
    for fo in floors:
        fo.visible_shadow = False   # the light inside the lit floors leaves through the glass (mullions still cast)
    # aviation light on the antenna
    an = O.get("cb_antenna")
    if an:
        mn, mx = wbox(an)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mx[2]))
        s = bpy.context.active_object; s.name = "aviation_light"; L.assign(s, M["aviation"]); s.visible_shadow = False
        for c in s.users_collection: c.objects.unlink(s)
        NEW.objects.link(s); s.parent = tilt; s.matrix_parent_inverse = tilt.matrix_world.inverted()
    # warm light from inside the lit floors (the windows' own light reaching the floor and Claude), parented to the tilt
    for i, fo in enumerate(floors):
        if i % 3 != 1:
            continue
        mn, mx = wbox(fo)
        p = L.light(f"L_tower_floor_{i}", "POINT", ((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2), 70.0,
                    temp=3200, soft=0.4, coll=LIG, dist=7.0)
        p.parent = tilt; p.matrix_parent_inverse = tilt.matrix_world.inverted()
    # ---------------------------------------------------------------- the caged tungsten work lamp at the column (2700 K)
    p6 = O.get("undercroft_p6")
    lamp_at = Vector((59.30, 0.55, 1.42))
    # the lamp hangs in front-left of the column (camera side), so it keys Claude's face in the stares and the tag's face
    # (CREATIVE 10.6 L5: "the caged work lamp as Claude's key"); the blocking's stand-in sat behind him.
    lamp_at = Vector((59.38, -0.78, 1.22))
    if p6:
        p6.data = bpy.data.meshes.new('p6_empty')   # stand-in faces removed (keyed visibility would show them)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=lamp_at)
    bl = bpy.context.active_object; bl.name = "worklamp_bulb"; L.assign(bl, M["bulb"]); bl.visible_shadow = False
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, location=lamp_at, segments=8, ring_count=4)
    cg = bpy.context.active_object; cg.name = "worklamp_cage"; L.assign(cg, M["steel"])
    wf = cg.modifiers.new("cage", "WIREFRAME"); wf.thickness = 0.0035
    # hook and cord up to the ceiling slab
    L.box("worklamp_cord", (lamp_at.x - 0.004, lamp_at.y - 0.004, lamp_at.z + 0.085), (lamp_at.x + 0.004, lamp_at.y + 0.004, 12.0),
          M["rubber"], NEW)
    for s in (bl, cg):
        for c in s.users_collection: c.objects.unlink(s)
        NEW.objects.link(s)
    L.light("L_worklamp", "POINT", tuple(lamp_at), float(os.environ.get("AFF_LAMP_W", "330")), temp=3000, soft=0.03, coll=LIG)   # tiny source: hard cage shadows
    # dust in the lamp's light (a volume sphere, low density, falling off)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=2.2, location=lamp_at)
    du = bpy.context.active_object; du.name = "worklamp_dust"
    for c in du.users_collection: c.objects.unlink(du)
    NEW.objects.link(du); du.visible_shadow = False
    dm, nt = L._new_mat("AFF_dust_beam")
    out = nt.nodes.new("ShaderNodeOutputMaterial"); pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
    nt.links.new(tc.outputs["Object"], gr.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMath"); mr.operation = "MULTIPLY"; mr.inputs[1].default_value = 0.05
    nt.links.new(gr.outputs["Fac"], mr.inputs[0])
    nt.links.new(mr.outputs[0], pv.inputs["Density"]); pv.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(pv.outputs[0], out.inputs["Volume"]); du.data.materials.append(dm)
    # ---------------------------------------------------------------- the grate above: cool light falling through bars
    p7 = O.get("undercroft_p7")
    if p7:
        mn, mx = wbox(p7)
        p7.data = bpy.data.meshes.new('p7_empty')   # stand-in faces removed (keyed visibility would show them)
        me = bpy.data.meshes.new("ceiling_grate"); bm = bmesh.new()
        def cube(a, b_):
            r = bmesh.ops.create_cube(bm, size=1.0)
            for v in r["verts"]:
                v.co = Vector([(a[i] + b_[i]) / 2 + v.co[i] * (b_[i] - a[i]) for i in range(3)])
        x = mn[0]
        while x <= mx[0]:
            cube((x, mn[1], 11.97), (x + 0.012, mx[1], 12.03)); x += 0.045
        for y in (mn[1], (mn[1] + mx[1]) / 2, mx[1] - 0.03):
            cube((mn[0], y, 11.95), (mx[0], y + 0.03, 12.05))
        bm.to_mesh(me); bm.free()
        cgo = bpy.data.objects.new("ceiling_grate", me); NEW.objects.link(cgo); me.materials.append(M["steel"])
        # the opening in the ceiling slab around it: the slab is a solid box, so the server room's light comes from a
        # spot just under the slab, shining down through the bars (its pattern on the floor), cool teal-white
        c = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, 12.08))
        sp = L.light("L_grate_from_above", "SPOT", tuple(c), 14000.0, color=(0.55, 0.85, 0.95), spot=46, blend=0.35,
                     soft=0.08, coll=LIG, rot=(0, 0, 0))
        L.aim(sp, (60.2, -0.2, 6.0))   # the server room's light through the grate rims the tower's top and edges (CD 10.8 L11)
        sp.data.shadow_soft_size = 0.05
        # the slab must not block it: cut a hole by hiding the slab's shadow there is not possible; move the slab's
        # underside opening: build the ceiling as a frame of four boxes round the opening instead of one plate
        p5 = O.get("undercroft_p5")
        if p5:
            a, b_ = wbox(p5)
            p5.data = bpy.data.meshes.new('p5_empty')   # stand-in faces removed (keyed visibility would show them)
            for nm, lo, hi in (("ceil_W", (a[0], a[1], a[2]), (mn[0], b_[1], b_[2])),
                               ("ceil_E", (mx[0], a[1], a[2]), (b_[0], b_[1], b_[2])),
                               ("ceil_S", (mn[0], a[1], a[2]), (mx[0], mn[1], b_[2])),
                               ("ceil_N", (mn[0], mx[1], a[2]), (mx[0], b_[1], b_[2]))):
                L.box(nm, lo, hi, M["ceiling"], NEW)
    # concrete columns and beams in the dark (structure, so the space reads as a space, not a void)
    for i, (x, y) in enumerate(((54.5, -5.5), (54.5, 5.5), (65.5, -5.5), (65.5, 5.5), (54.5, 0.0), (65.5, 0.0))):
        L.box(f"uc_col_{i}", (x - 0.35, y - 0.35, 0), (x + 0.35, y + 0.35, 12.0), M["wall"], NEW)
    for i, y in enumerate((-5.5, 0.0, 5.5)):
        L.box(f"uc_beam_{i}", (52.0, y - 0.3, 11.2), (68.0, y + 0.3, 12.0), M["ceiling"], NEW)
    def _ext_n(o, c, n):
        return max((o.matrix_world @ Vector(b) - c).dot(n) for b in o.bound_box)
    # the DO NOT DELETE tag (CD 13.2, SPEC §2): the design's 0.34 x 0.24 m tag (alpha) where the blocking's stand-in hangs,
    # and the stencil decal on the column's camera-side face
    col = O.get("dnd_column")
    if O.get("tag_dnd_p0"):      # LOCK 7's stand-in (group tag_dnd, under the stalk plate)
        tg = O.get("tag_dnd_p0"); tt = O.get("tag_dnd_t1")
    else:
        tg = O.get("dnd_tag"); tt = O.get("dnd_txt")
    if tg and tt:
        sc.frame_set(800)            # the tag's read frames (f796-809): it may be keyed (LOCK 7)
        bpy.context.view_layer.update()
        n = (tt.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized(); n.z = 0; n.normalize()
        mn, mx = wbox(tg); c = Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
        imt, _ = SL._img("tag/tag.png")
        tmat = SL.material("AFF_dnd_tag", "paper", imt, None)
        right_ = Vector((0, 0, 1)).cross(n).normalized()
        tw = max(0.2, max((tg.matrix_world @ Vector(b) - c).dot(right_) for b in tg.bound_box) * 2)   # the stand-in's width
        tp = SL.plane("dnd_tag_face", tuple(c + n * (_ext_n(tg, c, n) + 0.001)), tw, tw * 240 / 340, tuple(n), NEW, tmat)
        # ride the blocking's tag (its keys move it; its visibility keys are copied)
        mw = tp.matrix_world.copy(); tp.parent = tg; tp.matrix_world = mw
        if True:
            for fc in L.fcurves_of(tg):
                if fc.data_path == "hide_render":
                    for k in fc.keyframe_points:
                        tp.hide_render = bool(k.co[1]); tp.keyframe_insert("hide_render", frame=int(k.co[0]))
        tg.data = bpy.data.meshes.new(tg.name + "_off")
        for o_ in O:
            if o_.type == "FONT" and (o_ == tt or o_.name.startswith("tag_dnd_t")): o_.data.body = " "
        for o_ in [o for o in O if o.type == "FONT" and (o.name.startswith("tag_dnd_t") or o.name == "dnd_txt")]:
            bpy.data.objects.remove(o_, do_unlink=True)
        L.log("tag face", tuple(round(x, 3) for x in c), "facing", tuple(round(x, 2) for x in n))
    if col:
        mn, mx = wbox(col)
        ims_, _ = SL._img("tag/column_stencil.png")
        stm = SL.material("AFF_dnd_stencil", "paper", ims_, None)
        sp_ = SL.plane("dnd_stencil", ((mn[0] + mx[0]) / 2, mn[1] - 0.0008, (mn[2] + mx[2]) / 2), 0.084, min(0.62, mx[2] - mn[2]), (0, -1, 0), NEW, stm)
        sp_.parent = col; sp_.matrix_parent_inverse = col.matrix_world.inverted()
    # a second caged work lamp on the far column (CD 13.1): the far wall and the tower's near faces read; same fixture
    lamp2 = Vector((65.5, 0.45, 3.1))   # on uc_col_5's far face: it lights the far wall, uc_col_3 and the tower's side
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=lamp2)
    b2 = bpy.context.active_object; b2.name = "worklamp2_bulb"; L.assign(b2, M["bulb"]); b2.visible_shadow = False
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.085, location=lamp2, segments=8, ring_count=4)
    c2 = bpy.context.active_object; c2.name = "worklamp2_cage"; L.assign(c2, M["steel"])
    w2 = c2.modifiers.new("cage", "WIREFRAME"); w2.thickness = 0.0035
    L.box("worklamp2_bracket", (65.44, 0.34, 3.18), (65.56, 0.36, 3.30), M["steel"], NEW)
    L.box("worklamp2_arm", (65.49, 0.35, 3.17), (65.51, 0.45, 3.19), M["steel"], NEW)
    for o_ in (b2, c2):
        for c_ in o_.users_collection: c_.objects.unlink(o_)
        NEW.objects.link(o_)
    L.light("L_worklamp2", "POINT", tuple(lamp2), float(os.environ.get("AFF_LAMP2_W", "900")), temp=3000, soft=0.03, coll=LIG)
    # rebar stubs out of the slab edge near the column (detail where the 9:16 MCU sees it)
    for i in range(5):
        L.box(f"rebar_stub_{i}", (59.2 + i * 0.12, 0.9, 0.0), (59.212 + i * 0.12, 0.912, 0.18 + 0.05 * (i % 2)),
              M["rust"], NEW)

w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0, 0, 0, 1); bg.inputs["Strength"].default_value = 0.0

TOP = bpy.data.collections.new("SHORT_SET_%s" % AREA)
for c in list(sc.collection.children):
    TOP.children.link(c); sc.collection.children.unlink(c)
for o in list(sc.collection.objects):
    TOP.objects.link(o); sc.collection.objects.unlink(o)
sc.collection.children.link(TOP)
L.render_settings(sc)
json.dump({"emissive": L.emission_census(), "lights": L.light_census(), "log": L.LOG},
          open(os.path.join(HERE, "data", NAME + "_census.json"), "w"), indent=1)
L.shadow_transparent_all()
L.finalize_paths()
bpy.ops.wm.save_mainfile()
print("[look] saved", OUT)
