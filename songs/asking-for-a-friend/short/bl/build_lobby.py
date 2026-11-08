"""sets_lobby: the lobby's emergency corner at full quality (what CAM_916 and the 16:9 camera see in f366-572).

  Blender -b blocking/AFF_blk_s01_intro.blend --python build_lobby.py -- <out name, e.g. sets_lobby_v1>

Opens the blocking blend READ-ONLY and saves at once as blender/short/<out>.blend (never over an existing file).
Removes the characters (the animation worker's), the draft cameras and every stand-in light, then dresses the set:
PBR materials on every surface, new geometry where the direction asks for it (walnut slat wall, hung dashboard,
pendant, brass placard, the case's lit sign), only real light sources, the fire sim (fire_sim_*.blend) linked with
its cache. Props the characters handle (EXTINGUISHER, shards, the case door) keep their approved animation here.
"""
import bpy, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_look as L
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
NAME = ARGS[0]
FIRE = ARGS[1] if len(ARGS) > 1 else None   # fire_sim_<tag>
SHORT = os.path.join(L.BLENDER, "short")
OUT = os.path.join(SHORT, NAME + ".blend")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert not os.path.exists(OUT), "never save over an existing blend: " + OUT
bpy.ops.wm.save_as_mainfile(filepath=OUT)
O = bpy.data.objects
sc = bpy.context.scene

# ------------------------------------------------------------------ strip what isn't the set
DROP_COLLS = {"CLAUDE_CHAR", "RECEPTIONIST", "FOUNDER", "CUSTOMER_SRC", "QUEUE", "PORTRAIT_TMP", "CAMS_G1"}
drop = set()
for o in O:
    if o.type == "CAMERA" or o.type == "LIGHT":
        drop.add(o)
    if any(c.name in DROP_COLLS for c in o.users_collection):
        drop.add(o)
# the stand-in fire (flame cones, smoke puffs) is replaced by the sim
for o in O:
    if o.name.startswith(("flm_", "puff_")):
        drop.add(o)
for o in list(drop):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    if c.name in DROP_COLLS:
        bpy.data.collections.remove(c)
L.log("removed", len(drop), "objects (characters, cameras, stand-in lights, stand-in fire)")

SET = L.coll("SET_lobby")
LIG = L.coll("LIGHTS_lobby")
NEW = L.coll("SET_lobby_new")

# ------------------------------------------------------------------ materials
M = {}
M["walnut"] = L.pbr("AFF_walnut_slat", "black_walnut_veneer_01", scale=0.9, tint=(0.42, 0.30, 0.22), tint_mix=1.0,
                    rough=(0.38, 0.62), nstr=0.6, coat=0.25, coat_rough=0.35)
M["walnut_back"] = L.pbr("AFF_walnut_backing", "black_walnut_veneer_01", scale=0.9, tint=(0.08, 0.06, 0.05),
                         rough=(0.6, 0.8), nstr=0.3)
M["travertine"] = L.pbr("AFF_travertine", "coral_ground_02", scale=1.1, base=(0.70, 0.62, 0.50), tint_mix=0.55,
                        rough=(0.32, 0.55), nstr=0.45, coat=0.15, coat_rough=0.25)
M["brass"] = L.pbr("AFF_brass", "metal_plate_02", scale=2.0, base=(0.80, 0.58, 0.30), tint_mix=0.25, rough=(0.22, 0.42),
                   metal=1.0, nstr=0.15)
M["brass_dark"] = L.pbr("AFF_brass_engraved", "metal_plate_02", scale=6.0, base=(0.10, 0.07, 0.04), tint_mix=0.2,
                        rough=(0.5, 0.7), metal=0.6, nstr=0.1)
M["floor"] = L.pbr("AFF_polished_concrete", "concrete_floor_02", scale=0.35, base=(0.10, 0.095, 0.09), tint_mix=0.7,
                   rough=(0.12, 0.42), nstr=0.35, coat=0.35, coat_rough=0.08)
M["ceiling"] = L.pbr("AFF_ceiling_plaster", "painted_concrete_02", scale=0.4, base=(0.10, 0.10, 0.10), tint_mix=0.4,
                     rough=(0.75, 0.95), nstr=0.4)
M["red_steel"] = L.pbr("AFF_red_painted_steel", "metal_plate_02", scale=2.5, base=(0.30, 0.015, 0.012), tint_mix=0.35,
                       rough=(0.4, 0.6), nstr=0.25, coat=0.15, coat_rough=0.3)
M["ext_red"] = L.pbr("AFF_extinguisher_red", "metal_plate_02", scale=5.0, base=(0.50, 0.025, 0.02), tint_mix=0.2,
                     rough=(0.16, 0.32), nstr=0.08, coat=0.8, coat_rough=0.06)
M["chrome"] = L.pbr("AFF_chrome", "metal_plate_02", scale=6.0, base=(0.75, 0.75, 0.76), tint_mix=0.1, rough=(0.08, 0.22),
                    metal=1.0, nstr=0.05)
M["rubber"] = L.pbr("AFF_rubber_black", "rubber_tiles", scale=8.0, base=(0.018, 0.018, 0.02), tint_mix=0.2,
                    rough=(0.55, 0.75), nstr=0.3)
M["steel_dark"] = L.pbr("AFF_steel_dark_anodised", "metal_plate_02", scale=1.5, base=(0.05, 0.05, 0.055), tint_mix=0.3,
                        rough=(0.3, 0.5), metal=1.0, nstr=0.2)
M["rack"] = L.pbr("AFF_rack_painted_steel", "metal_plate_02", scale=1.2, base=(0.035, 0.038, 0.045), tint_mix=0.4,
                  rough=(0.35, 0.6), metal=0.7, nstr=0.35)
M["srv_floor"] = L.pbr("AFF_srv_concrete", "concrete_floor_worn_001", scale=0.4, base=(0.12, 0.12, 0.12), tint_mix=0.8,
                       rough=(0.45, 0.85), nstr=0.6)
M["srv_wall"] = L.pbr("AFF_srv_wall", "painted_concrete_02", scale=0.4, base=(0.06, 0.07, 0.08), tint_mix=0.5,
                      rough=(0.7, 0.9), nstr=0.5)
M["scorch"] = L.pbr("AFF_scorched_steel", "rust_coarse_01", scale=2.0, base=(0.03, 0.025, 0.02), tint_mix=0.6,
                    rough=(0.6, 0.9), metal=0.4, nstr=0.8)
M["glass"] = L.thin_glass("AFF_glass_partition_thin")
M["case_glass"] = L.glass("AFF_case_glass", 0.0, 0.06)
M["shard"] = L.glass("AFF_glass_shard", 0.0, 0.05)
M["ceramic"] = L.pbr("AFF_ceramic_pot", "white_stucco", scale=3.0, base=(0.12, 0.11, 0.10), tint_mix=0.4,
                     rough=(0.25, 0.45), nstr=0.2, coat=0.5)
M["leaf"] = L.pbr("AFF_leaf", "white_stucco", scale=4.0, base=(0.03, 0.07, 0.03), tint_mix=0.3, rough=(0.35, 0.55), nstr=0.1)
M["paper"] = L.pbr("AFF_paper", "white_stucco", scale=10.0, base=(0.62, 0.60, 0.55), tint_mix=0.2, rough=(0.7, 0.9), nstr=0.05)
M["ink"] = L.pbr("AFF_print_ink", "white_stucco", scale=30.0, base=(0.02, 0.02, 0.025), tint_mix=0.05, rough=(0.5, 0.6), nstr=0.0)
M["felt"] = L.pbr("AFF_velvet_rope", "rubber_tiles", scale=10.0, base=(0.12, 0.02, 0.03), tint_mix=0.3, rough=(0.8, 1.0), nstr=0.2)
# real lights (screens, LEDs, the lit sign)
M["dash_screen"] = L.emissive("AFF_dash_screen_bg", (0.012, 0.035, 0.03), 1.0)
M["dash_text"] = L.emissive("AFF_dash_text_green", (0.42, 1.0, 0.62), 4.5)
M["dash_text_w"] = L.emissive("AFF_dash_text_white", (0.85, 0.95, 0.9), 2.6)
M["screen_dim"] = L.emissive("AFF_screen_dim", (0.05, 0.12, 0.16), 0.7)
M["sign_red"] = L.emissive("AFF_case_sign_red", (1.0, 0.06, 0.04), 3.0)
M["sign_white"] = L.emissive("AFF_case_sign_letters", (1.0, 0.92, 0.88), 6.0)
M["led_green"] = L.emissive("AFF_led_green", (0.15, 1.0, 0.35), 30.0)
M["led_amber"] = L.emissive("AFF_led_amber", (1.0, 0.45, 0.05), 25.0)
M["led_red"] = L.emissive("AFF_led_red", (1.0, 0.05, 0.03), 25.0)
M["led_off"] = L.pbr("AFF_led_off", "metal_plate_02", scale=20, base=(0.02, 0.02, 0.02), rough=(0.2, 0.3))
M["bulb"] = L.emissive("AFF_bulb_2700K", (1.0, 0.62, 0.32), 35.0, base=(0.9, 0.8, 0.6))
M["spark"] = L.emissive("AFF_spark", (1.0, 0.55, 0.18), 120.0)

# ------------------------------------------------------------------ assign by name
def mat_for(o):
    n = o.name
    if n in ("lobby_floor", "corr_floor"):
        return M["floor"]
    if n == "ceiling":
        return M["ceiling"]
    if n in ("wall_left", "wall_right", "wall_back_right", "corr_wall_L", "corr_end"):
        return M["walnut_back"]
    if n in ("glass_left", "wall_back_center"):
        return M["glass"]
    if n.startswith("mullion") or n == "glass_mullion_h":
        return M["steel_dark"]
    if n in ("desk", "desk_top"):
        return M["travertine"]
    if n == "desk_goldline":
        return M["brass"]
    if n.startswith("shard"):
        return M["shard"]
    if n == "case_door_glass":
        return M["case_glass"]
    if n.startswith("case_") and o.type == "MESH":
        return M["red_steel"]
    if n in ("ext_body", "ext_dome"):
        return M["ext_red"]
    if n in ("ext_neck", "ext_handle", "ext_nozzle"):
        return M["chrome"]
    if n == "ext_hose":
        return M["rubber"]
    if n == "ext_label":
        return M["paper"]
    if n == "dash_screen":
        return M["dash_screen"]
    if n in ("dash_title", "dash_title2"):
        return M["dash_text"]
    if n in ("dash_sub", "dash_ticker"):
        return M["dash_text_w"]
    if n.startswith("srv_led"):
        # the stand-in's colour code: green where it was green, off otherwise; a few amber/red for the failure
        cur = o.data.materials[0].name if o.data.materials else ""
        if "green" in cur:
            return M["led_green"]
        h = sum(ord(ch) for ch in n) % 9
        return M["led_amber"] if h == 0 else M["led_off"]
    if n.startswith(("srv_rack", "srv_ext_p2", "srv_ext_p3", "srv_ext_p4", "srv_ext_p5", "srv_ext_p6", "srv_ext_p7",
                     "srv_ext_p8")):
        return M["rack"]
    if n in ("burn_rack_scorch", "burn_rack"):   # the burning rack is scorched (its painted face read as a lit cream block)
        return M["scorch"]
    if n in ("srv_floor", "srv_ext_p0"):
        return M["srv_floor"]
    if n in ("srv_back", "srv_ext_p1"):
        return M["srv_wall"]
    if n.startswith("spark_"):
        return M["spark"]
    if n.startswith("planter_pot"):
        return M["ceramic"]
    if n.startswith("planter_leaf"):
        return M["leaf"]
    if n.startswith("post_"):
        return M["brass"]
    if n.startswith("rope_"):
        return M["felt"]
    if n == "wait_txt":
        return M["ink"]
    if n.startswith(("ticket", "wait_board", "tickets_pile")):
        return M["paper"]
    if n in ("wait_base", "wait_pole") or n.startswith("pf_"):
        return M["brass"]
    if n in ("queue_screen", "portrait_prism") or o.type == "FONT":
        return M["screen_dim"]
    return None


unmatched = []
for o in O:
    if o.type not in ("MESH", "CURVE", "FONT"):
        continue
    m = mat_for(o)
    if m is None:
        m = M["steel_dark"]
        unmatched.append(o.name)
    L.assign(o, m)
    L.apply_scale(o)
L.log("unmatched -> dark steel:", unmatched[:40], len(unmatched))

# glass lets the fire's light through (no shadow), the way real glass does
for o in O:
    if o.name in ("glass_left", "wall_back_center", "case_door_glass") or o.name.startswith("shard"):
        o.visible_shadow = False

# ------------------------------------------------------------------ in-world text (CREATIVE 10.3 / 10.4)
def txt(o, body):
    if o and o.type == "FONT":
        o.data.body = body


# the case's sign (CD 13.6 d; SPEC §2): IN CASE OF / EMERGENCY / FILE A TICKET, the design's texture on a 0.64 x 0.48 m
# lit red acrylic sign hung above the case. The blocking's text stand-in goes (its body emptied: it may be keyed).
import screens_lib as SL
cs = O.get("case_sign")
if cs:
    txt(cs, " ")
def _wb(o):
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(c[i] for c in cs) for i in range(3)], [max(c[i] for c in cs) for i in range(3)]


def _follow(obs, parent):
    """parent our new pieces to the blocking's group empty (its keys, if any, carry them)"""
    if parent is None: return
    bpy.context.view_layer.update()
    for o_ in obs:
        mw = o_.matrix_world.copy(); o_.parent = parent; o_.matrix_world = mw


ES_W, ES_H = 0.64, 0.48
es_p = O.get("esign_p0")
if es_p:   # the blocking's stand-in (LOCK 7): its spot, its group
    a_, b_ = _wb(es_p)
    ES_C = ((a_[0] + b_[0]) / 2, a_[1] - 0.002, (a_[2] + b_[2]) / 2)
    ES_PAR = O.get("esign")
    es_p.data = bpy.data.meshes.new("esign_p0_off")
    for o_ in O:
        if o_.name.startswith("esign_t") and o_.type == "FONT": o_.data.body = " "
else:
    ES_C = (-5.55, 4.640, float(os.environ.get("AFF_ESIGN_Z", "1.73")))   # bottom ~1.49, above the case top (1.45)
    ES_PAR = None
im_, rng_ = SL._img("emergency/sign.png")
esm = SL.material("AFF_esign", "sign", im_, rng_, strength=float(os.environ.get("AFF_ESIGN_S", "1.6")))
_ef = SL.plane("esign_face", ES_C, ES_W, ES_H, (0, -1, 0), NEW, esm)
_eb = L.box("sign_backplate_e", (ES_C[0] - ES_W / 2 - 0.012, ES_C[1] + 0.001, ES_C[2] - ES_H / 2 - 0.012),
      (ES_C[0] + ES_W / 2 + 0.012, ES_C[1] + 0.022, ES_C[2] + ES_H / 2 + 0.012), M["steel_dark"], NEW, bevel=0.004)
_follow([_ef, _eb], ES_PAR)
L.log("esign", "centre", tuple(round(x, 3) for x in ES_C), "from the blocking's" if es_p else "default")

# the status board (CD 13.2, SPEC §1): one 3.20 x 1.80 m asset, the design's per-frame texture (board/board_f####.png,
# f366-572: dots on the beats, bars scrolling, the lobby temp climbing, the one orange bar), hung from the ceiling in a
# dark bezel. A real light: the screen's own area light at the board's size and colour is his key from above.
ds = O.get("board_p1") or O.get("dash_screen")     # LOCK 7's board stand-in (group `board`), else the old one
B_PAR = O.get("board") if ds and ds.name == "board_p1" else None
if ds:
    mn, mx = _wb(ds)
    BW_, BH_ = 3.20, 1.80
    cx = (mn[0] + mx[0]) / 2
    # take the stand-in's centre if it's already the new size, else the SPEC's raised spot
    cz = (mn[2] + mx[2]) / 2 if abs((mx[2] - mn[2]) - BH_) < 0.05 else 2.75
    cz = float(os.environ.get("AFF_BOARD_Z", cz)); cx = float(os.environ.get("AFF_BOARD_X", cx))
    fy = min(mn[1], 4.975) - 0.025          # the face sits in front of the glass wall (y 5.00) with its bezel
    imb, rngb = SL._img("board", seq=(366, 572))
    bm = SL.material("AFF_board", "display", imb, rngb, strength=float(os.environ.get("AFF_BOARD_S", "0.42")))
    _bf = SL.plane("board_face", (cx, fy, cz), BW_, BH_, (0, -1, 0), NEW, bm)
    for o_ in list(O):    # the stand-ins (may be keyed): meshes go, text emptied, the objects stay
        if o_.name in ("dash_screen",) or (o_.name.startswith("board_p") and o_.type == "MESH"):
            o_.data = bpy.data.meshes.new(o_.name + "_off")
        if o_.type == "FONT" and (o_.name.startswith("board_t") or o_.name in ("dash_title", "dash_title2", "dash_sub", "dash_uptime", "dash_ticker")):
            o_.data.body = " "
    for n_ in ("ticker_bar", "ticker_bezel"):
        t_ = O.get(n_)
        if t_: bpy.data.objects.remove(t_, do_unlink=True)
    L.box("board_bezel", (cx - BW_ / 2 - 0.04, fy + 0.001, cz - BH_ / 2 - 0.04), (cx + BW_ / 2 + 0.04, fy + 0.022, cz + BH_ / 2 + 0.04),
          M["steel_dark"], NEW, bevel=0.008)
    for x in (cx - BW_ / 2 + 0.4, cx + BW_ / 2 - 0.4):
        L.box(f"board_rod_{x:.2f}", (x - 0.012, fy + 0.006, cz + BH_ / 2 + 0.04), (x + 0.012, fy + 0.018, 5.0), M["steel_dark"], NEW)
    a = L.light("L_dash_screen", "AREA", (cx, fy - 0.03, cz), float(os.environ.get("AFF_BOARD_W", "800")),
                color=(0.42, 1.0, 0.72), size=(BW_, BH_), coll=LIG, rot=(90, 0, 180))
    a.data.spread = math.radians(130)      # less wash on the ceiling (the 9:16 top band read as a mint slab)
    _follow([_bf, a] + [o_ for o_ in O if o_.name.startswith(("board_bezel", "board_rod_"))], B_PAR)
    L.log("board", "centre", (round(cx, 3), round(fy, 3), round(cz, 3)), "size", BW_, BH_)

for o_ in [o for o in O if o.type == "FONT" and o.name.startswith(("esign_t", "board_t"))]:
    bpy.data.objects.remove(o_, do_unlink=True)     # the stand-ins' text: ours replaces it (textcheck reads real text only)

# walnut slat wall: vertical slats 45 mm wide, 30 mm deep, 18 mm gaps, on the opaque walls the cameras see
import bmesh


def slats(name, axis, plane, a0, a1, z0, z1, normal_sign, w=0.045, d=0.03, gap=0.018):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    a = a0
    k = 0
    while a + w <= a1:
        if axis == "y":   # wall at x = plane, slats along y
            x0 = plane if normal_sign > 0 else plane - d
            mn, mx = (x0, a, z0), (x0 + d, a + w, z1)
        else:             # wall at y = plane, slats along x
            y0 = plane - d if normal_sign < 0 else plane
            mn, mx = (a, y0, z0), (a + w, y0 + d, z1)
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector([(mn[i] + mx[i]) / 2 + v.co[i] * (mx[i] - mn[i]) for i in range(3)])
        a += w + gap
        k += 1
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    NEW.objects.link(ob)
    me.materials.append(M["walnut"])
    md = ob.modifiers.new("bevel", "BEVEL"); md.width = 0.003; md.segments = 1
    L.log("slats", name, k)
    return ob


slats("walnut_slats_left", "y", -6.95, -4.8, 5.0, 0.0, 5.0, +1)
slats("walnut_slats_back_right", "x", 5.0, 3.0, 5.9, 0.0, 5.0, -1)
# a linear wall-grazer in a ceiling slot along the walnut wall (CD 13.1: the slats read as wood, the corner isn't a void)
M["grazer"] = L.emissive("AFF_grazer_lens", (1.0, 0.80, 0.60), 1.0, base=(0.8, 0.8, 0.8))
L.box("grazer_slot", (-6.92, -4.7, 4.975), (-6.80, 4.9, 4.99), M["grazer"], NEW).visible_shadow = False
gz = L.light("L_grazer", "AREA", (-6.86, 0.1, 4.96), float(os.environ.get("AFF_GRAZE_W", "380")), temp=3000,
             size=(0.08, 9.6), coll=LIG, rot=(0, -8, 0))   # tipped 8 deg toward the wall
gz.data.spread = math.radians(100)
# brass skirting along the slat walls
L.box("skirt_left", (-6.95, -4.8, 0.0), (-6.90, 5.0, 0.06), M["brass"], NEW)

# pendant over the desk end (one warm pendant): brass cylinder, a 2700 K bulb, a real point light
px, py, pz = -1.25, 1.55, 2.55   # the desk end (in the 9:16 corner it hung in front of the dashboard)
L.box("pendant_shade", (px - 0.11, py - 0.11, pz), (px + 0.11, py + 0.11, pz + 0.26), M["brass"], NEW, bevel=0.02)
L.box("pendant_rod", (px - 0.006, py - 0.006, pz + 0.26), (px + 0.006, py + 0.006, 5.0), M["steel_dark"], NEW)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(px, py, pz - 0.01))
bulb = bpy.context.active_object; bulb.name = "pendant_bulb"; L.assign(bulb, M["bulb"]); bulb.visible_shadow = False
for c in bulb.users_collection: c.objects.unlink(bulb)
NEW.objects.link(bulb)
# the pendant row over the desk (CD 13.1): two more of the same pendant either side, warm, at a working level
for k_, dx in enumerate((-0.8, 0.8)):
    qx = px + dx
    L.box(f"pendant_shade_{k_}", (qx - 0.11, py - 0.11, pz), (qx + 0.11, py + 0.11, pz + 0.26), M["brass"], NEW, bevel=0.02)
    L.box(f"pendant_rod_{k_}", (qx - 0.006, py - 0.006, pz + 0.26), (qx + 0.006, py + 0.006, 5.0), M["steel_dark"], NEW)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(qx, py, pz - 0.01))
    b_ = bpy.context.active_object; b_.name = f"pendant_bulb_{k_}"; L.assign(b_, M["bulb"]); b_.visible_shadow = False
    for c_ in b_.users_collection: c_.objects.unlink(b_)
    NEW.objects.link(b_)
    L.light(f"L_pendant_{k_}", "SPOT", (qx, py, pz - 0.02), float(os.environ.get("AFF_PEND_W", "220")), temp=2900, spot=110,
            blend=0.8, soft=0.06, coll=LIG, rot=(0, 0, 0))
pl = L.light("L_pendant", "SPOT", (px, py, pz - 0.02), float(os.environ.get("AFF_PEND_W", "220")), temp=2900, spot=110, blend=0.8, soft=0.06, coll=LIG,
             rot=(0, 0, 0))

# PLEASE DO NOT TOUCH ANYTHING moves onto the emergency case (CREATIVE 10.6 B1): a bright brushed-brass plaque under
# IN CASE OF EMERGENCY, letters engraved and filled with black enamel, lit by the pendant. The blocking's foreground
# placard goes (it covered the gag). Letter size is set from CAM_916 at f461 (>= 58 px type, cap >= 42 px), see below.
for n in ("placard", "placard_p0", "placard_p3", "placard_t1", "placard_t2"):
    o = O.get(n)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
M["brass_brushed"] = L.pbr("AFF_brass_brushed_plate", "metal_plate_02", scale=3.0, base=(0.85, 0.62, 0.32), tint_mix=0.2,
                           rough=(0.30, 0.42), metal=1.0, nstr=0.1)
M["enamel"] = L.pbr("AFF_black_enamel_infill", "white_stucco", scale=30.0, base=(0.010, 0.009, 0.008), tint_mix=0.05,
                    rough=(0.3, 0.4), nstr=0.0)
L.shadow_transparent(M["enamel"])
# the blocking's locked plaque (case_plaque at (-5.55, 4.40, 1.05), 0.42 x 0.14 m, facing -Y): made real, then checked
# against CAM_916 at f461-502; cut if its type can't reach 58 px (cap 42 px)
grp = O.get("case_plaque")
if grp:
    for ch in grp.children:
        if ch.type == "MESH":
            L.assign(ch, M["brass_brushed"]); md = ch.modifiers.new("bevel", "BEVEL"); md.width = 0.003; md.segments = 2
        elif ch.type == "FONT":
            L.assign(ch, M["enamel"]); ch.data.extrude = 0.0004
    bpy.context.view_layer.update()
    t1 = next((c for c in grp.children if c.type == "FONT"), None)
    cap = (t1.dimensions.y * 0.80) if t1 else 0.0       # the line's height ~ cap height for all-caps text
    EXP = os.path.join(HERE, "..", "blocking", "export", "short_cams.json")
    rows = [r["9x16"] for r in json.load(open(EXP))["frames"] if 461 <= r["f"] <= 502]
    c0 = grp.matrix_world.translation
    best = max(cap * 1920 / (2 * (Vector(r["loc"]) - c0).length * math.tan(math.radians(r["vfov_deg"]) / 2)) for r in rows)
    L.log("case plaque (blocking's): cap", round(cap, 4), "m; best cap px in f461-502:", round(best, 1))
    if best < 42 and os.environ.get("AFF_KEEP_PLAQUE") != "1":
        for ch in list(grp.children):
            bpy.data.objects.remove(ch, do_unlink=True)
        bpy.data.objects.remove(grp, do_unlink=True)
        L.log("case plaque CUT: can't reach 58 px type in f461-502 at the locked framing (CD 10.6 B1)")

# the burning rack's face: a scorched perforated steel door with rails and soot (CD 10.8 L8)
def _perf(nt, b_, vec):
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (150, 150, 150)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Randomness"].default_value = 0.0; nt.links.new(mp.outputs[0], vo.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.26; mr.inputs["From Max"].default_value = 0.30
    nt.links.new(vo.outputs["Distance"], mr.inputs["Value"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.7; bp.inputs["Distance"].default_value = 0.002
    nt.links.new(mr.outputs[0], bp.inputs["Height"])
    src = next((l.from_socket for l in nt.links if l.to_socket == b_.inputs["Normal"]), None)
    if src: nt.links.new(src, bp.inputs["Normal"])
    nt.links.new(bp.outputs[0], b_.inputs["Normal"])
    cs = next((l.from_socket for l in nt.links if l.to_socket == b_.inputs["Base Color"]), None)
    mx_ = nt.nodes.new("ShaderNodeMix"); mx_.data_type = "RGBA"; nt.links.new(mr.outputs[0], mx_.inputs["Factor"])
    mx_.inputs["A"].default_value = (0.002, 0.002, 0.002, 1)
    if cs: nt.links.new(cs, mx_.inputs["B"])
    nt.links.new(mx_.outputs["Result"], b_.inputs["Base Color"])
M["scorch_door"] = L.pbr("AFF_scorched_perforated_door", "rust_coarse_01", scale=2.5, base=(0.025, 0.02, 0.016), tint_mix=0.7,
                         rough=(0.7, 0.95), metal=0.3, nstr=0.9, extra=_perf)
br = O.get("burn_rack")
if br:
    rmn = [min((br.matrix_world @ Vector(c))[i] for c in br.bound_box) for i in range(3)]
    rmx = [max((br.matrix_world @ Vector(c))[i] for c in br.bound_box) for i in range(3)]
    fy_ = rmn[1]
    L.box("burn_rack_door", (rmn[0] + 0.04, fy_ - 0.012, 0.06), (rmx[0] - 0.04, fy_ - 0.002, rmx[2] - 0.05), M["scorch_door"], NEW, bevel=0.003)
    for k_, x_ in enumerate((rmn[0] + 0.015, rmx[0] - 0.035)):
        L.box(f"burn_rack_rail_{k_}", (x_, fy_ - 0.02, 0.0), (x_ + 0.02, fy_, rmx[2]), M["scorch"], NEW)

# the fire's light behind her at the desk (CD 10.8 L10): the second burning rack behind the centre glass (the blocking's
# fire_rack at x -1.4) throws its flicker onto the glass and the server room behind her in the 16:9 opener
fp0 = O.get("fire_rack_p0"); fp1 = O.get("fire_rack_p1")
if fp0: L.assign(fp0, M["scorch"])
if fp1: fp1.data = bpy.data.meshes.new("fire_rack_flame_standin_off")   # the stand-in flame block goes; its light stays
fb_ = L.light("L_fire_back", "POINT", (-1.4, 6.95, 1.3), 260.0, temp=1800, soft=0.2, coll=LIG, volume=0.2)
fb_.data.specular_factor = 0.0; fb_.data.transmission_factor = 0.0

# ------------------------------------------------------------------ lights (only real sources)
# the fire: a point light inside the rack's flames, strength from the sim (keyed below), 1800 K
fl = L.light("L_fire", "POINT", (-3.45, 5.95, 1.85), 320.0, temp=1800, soft=0.1, coll=LIG, volume=0.25)
fl.data.specular_factor = 0.0   # no mirror-disc of the light in the glass: the flames reflect themselves
fl2 = L.light("L_fire_high", "POINT", (-3.45, 5.8, 2.6), 120.0, temp=1900, soft=0.15, coll=LIG, volume=0.25)
fl2.data.specular_factor = 0.0
fl.data.transmission_factor = 0.0; fl2.data.transmission_factor = 0.0   # no disc of the light seen through the glass
# the case sign spills red
L.light("L_case_sign", "AREA", (-5.55, 4.60, float(os.environ.get("AFF_ESIGN_Z", "1.73"))), 6.0, color=(1.0, 0.12, 0.08), size=(0.64, 0.48), rot=(90, 0, 180),
        coll=LIG)
# the server room's own sources behind the glass: rack LED banks (low teal spill at each rack face), one red beacon
# (the rack LED banks light the room through their own emissive LEDs and GI; the area-light stand-ins for their
# spill made hot mint strips on the rack faces and are gone)
L.light("L_srv_beacon", "POINT", (-2.95, 9.0, 3.6), 25.0, color=(1.0, 0.05, 0.03), soft=0.05, coll=LIG, dist=6.0)

# recessed ceiling downlights over the emergency corner (a lobby at night keeps a few on): real fixtures, 3000 K,
# narrow, so Claude and the case get a top key from a source that exists (not specified in CREATIVE; my call, noted)
M["trim"] = L.pbr("AFF_downlight_trim", "metal_plate_02", scale=10, base=(0.03, 0.03, 0.03), rough=(0.3, 0.4), metal=1.0)
M["lens"] = L.emissive("AFF_downlight_lens", (1.0, 0.80, 0.62), 25.0, base=(0.8, 0.8, 0.8))
for i, (x, y, e_) in enumerate(((-5.3, 3.75, 480.0), (-4.25, 3.9, 480.0), (-4.8, 2.6, 480.0), (-4.75, 3.35, 420.0))):
    L.box(f"downlight_trim_{i}", (x - 0.09, y - 0.09, 4.985), (x + 0.09, y + 0.09, 5.0), M["trim"], NEW)
    L.box(f"downlight_lens_{i}", (x - 0.06, y - 0.06, 4.975), (x + 0.06, y + 0.06, 4.982), M["lens"], NEW).visible_shadow = False
    # CD 13.1: no hot floor pool: wider and softer, a little less power (the board is his key now)
    # the two front cans are gimbals tilted 25 deg toward the case: his front from above, not just his crown
    L.light(f"L_downlight_{i}", "SPOT", (x, y, 4.965), e_ * float(os.environ.get("AFF_DOWN_K", "0.8")), temp=4300, spot=44, blend=0.85, soft=0.05, coll=LIG,
            rot=((25, 0, 0) if y < 3.5 else (0, 0, 0)))

# ------------------------------------------------------------------ haze in the server room (lit only by its sources)
hz = L.box("srv_haze", (-7.05, 5.25, 0.0), (-2.95, 9.25, 4.9), None, NEW)
hm, nt = L._new_mat("AFF_haze_server")
out = nt.nodes.new("ShaderNodeOutputMaterial")
pv = nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.035
pv.inputs["Anisotropy"].default_value = 0.45
pv.inputs["Color"].default_value = (0.6, 0.6, 0.62, 1)
nt.links.new(pv.outputs[0], out.inputs["Volume"])
hz.data.materials.append(hm)
hz.visible_shadow = False

# ------------------------------------------------------------------ fire sim (append domain with its cache)
if FIRE:
    fpath = os.path.join(SHORT, FIRE + ".blend")
    with bpy.data.libraries.load(fpath, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == "FIRE_domain"]
    dom = dst.objects[0]
    SET.objects.link(dom)
    dom.hide_render = False
    fm, nt = L._new_mat("AFF_fire_smoke")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = 9.0
    pv.inputs["Color"].default_value = (0.08, 0.075, 0.07, 1)
    pv.inputs["Absorption Color"].default_value = (0.02, 0.02, 0.02, 1)
    pv.inputs["Blackbody Intensity"].default_value = 1.0
    pv.inputs["Temperature Attribute"].default_value = "temperature"
    pv.inputs["Density Attribute"].default_value = "density"
    # flame emission (a real light): flame attribute -> colour ramp -> emission
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = "GEOMETRY"; at.attribute_name = "flame"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0, 0, 0, 1)
    e[1].position, e[1].color = 1.0, (1.0, 0.42, 0.06, 1)
    mid = e.new(0.3); mid.color = (0.9, 0.18, 0.02, 1)
    fr_ = nt.nodes.new("ShaderNodeMapRange"); fr_.inputs["From Max"].default_value = 0.55   # thinner flame shows: taller fire
    # break up the flame with moving tongues (noise rising with the frame; a pure function of time), so the dense
    # front-vent sheet doesn't read as a flat lit block
    tc_ = nt.nodes.new("ShaderNodeTexCoord"); mp_ = nt.nodes.new("ShaderNodeMapping")
    mp_.inputs["Scale"].default_value = (7.0, 7.0, 3.5)
    nt.links.new(tc_.outputs["Object"], mp_.inputs["Vector"])
    dr_ = mp_.inputs["Location"].driver_add("default_value", 2).driver; dr_.expression = "-frame*0.09"
    nz_ = nt.nodes.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = 1.0; nz_.inputs["Detail"].default_value = 4
    nz_.inputs["Roughness"].default_value = 0.6
    nt.links.new(mp_.outputs[0], nz_.inputs["Vector"])
    tg_ = nt.nodes.new("ShaderNodeMapRange"); tg_.inputs["From Min"].default_value = 0.35; tg_.inputs["From Max"].default_value = 0.7
    tg_.inputs["To Min"].default_value = 0.15; tg_.inputs["To Max"].default_value = 1.1
    nt.links.new(nz_.outputs["Fac"], tg_.inputs["Value"])
    fm0 = nt.nodes.new("ShaderNodeMath"); fm0.operation = "MULTIPLY"
    nt.links.new(at.outputs["Fac"], fm0.inputs[0]); nt.links.new(tg_.outputs[0], fm0.inputs[1])
    # the dense sheet from the front vents is thinned to licks (it read as a lightbox, CD 10.8 L8): domain-local
    # y < -0.60 (in front of the rack's face) and z < -0.25 keep 30%
    sx_ = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc_.outputs["Object"], sx_.inputs[0])
    my_ = nt.nodes.new("ShaderNodeMath"); my_.operation = "LESS_THAN"; my_.inputs[1].default_value = -0.60
    nt.links.new(sx_.outputs["Y"], my_.inputs[0])
    mz_ = nt.nodes.new("ShaderNodeMath"); mz_.operation = "LESS_THAN"; mz_.inputs[1].default_value = -0.25
    nt.links.new(sx_.outputs["Z"], mz_.inputs[0])
    mm_ = nt.nodes.new("ShaderNodeMath"); mm_.operation = "MULTIPLY"
    nt.links.new(my_.outputs[0], mm_.inputs[0]); nt.links.new(mz_.outputs[0], mm_.inputs[1])
    mk_ = nt.nodes.new("ShaderNodeMapRange"); mk_.inputs["To Min"].default_value = 1.0; mk_.inputs["To Max"].default_value = 0.3
    nt.links.new(mm_.outputs[0], mk_.inputs["Value"])
    fm_ = nt.nodes.new("ShaderNodeMath"); fm_.operation = "MULTIPLY"
    nt.links.new(fm0.outputs[0], fm_.inputs[0]); nt.links.new(mk_.outputs[0], fm_.inputs[1])
    nt.links.new(fm_.outputs[0], fr_.inputs["Value"])
    nt.links.new(fr_.outputs[0], ramp.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 3.5
    nt.links.new(fr_.outputs[0], em.inputs[0])
    nt.links.new(ramp.outputs["Color"], pv.inputs["Emission Color"])
    nt.links.new(em.outputs[0], pv.inputs["Emission Strength"])
    pv.inputs["Blackbody Intensity"].default_value = 0.0
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    dom.data.materials.clear(); dom.data.materials.append(fm)
    # the fire light follows the sim: energy = base * flame(f) / mean(flame)
    fj = os.path.join(HERE, "data", FIRE.replace("fire_sim_", "fire_flame_") + ".json")
    if os.path.exists(fj):
        rows = {int(k): v for k, v in json.load(open(fj))["frames"].items()}
        vals = [v for v in rows.values() if v > 0]
        mean = sum(vals) / max(1, len(vals))
        bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
        for f, v in sorted(rows.items()):
            k = min(1.8, max(0.35, 1.0 + 4.0 * ((v / mean) - 1.0))) if mean else 1.0   # the sim's own variation, amplified x4
            fl.data.energy = 320.0 * k
            fl.data.keyframe_insert("energy", frame=f)
            fl2.data.energy = 120.0 * (0.7 + 0.3 * k)
            fl2.data.keyframe_insert("energy", frame=f)
            v2 = rows.get(f - 37, v); k2 = min(1.8, max(0.35, 1.0 + 4.0 * ((v2 / mean) - 1.0)))
            fb_.data.energy = 260.0 * k2; fb_.data.keyframe_insert("energy", frame=f)
        L.log("fire light keyed from", fj, len(rows), "frames, mean flame", round(mean, 1))

# ------------------------------------------------------------------ world: a dark space, no ambient fill
w = sc.world or bpy.data.worlds.new("World")
sc.world = w
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
bg.inputs["Strength"].default_value = 0.0

L.render_settings(sc)
L.halation_compositor(sc)
sc.frame_start, sc.frame_end = 366, 572

# one collection holds the whole set, so the assembly links it in one go
TOP = bpy.data.collections.new("SHORT_SET_lobby")
for c in list(sc.collection.children):
    TOP.children.link(c); sc.collection.children.unlink(c)
for o in list(sc.collection.objects):
    TOP.objects.link(o); sc.collection.objects.unlink(o)
sc.collection.children.link(TOP)

json.dump({"emissive": L.emission_census(), "lights": L.light_census(), "log": L.LOG},
          open(os.path.join(HERE, "data", NAME + "_census.json"), "w"), indent=1)
import sys as _s; _s.path.insert(0, os.path.join(HERE, "bl")); import lobby_fix; lobby_fix.apply()   # CD pre-render fixes (Nov 5 evening)
L.shadow_transparent_all()
L.finalize_paths()
bpy.ops.wm.save_mainfile()
print("[look] saved", OUT)
