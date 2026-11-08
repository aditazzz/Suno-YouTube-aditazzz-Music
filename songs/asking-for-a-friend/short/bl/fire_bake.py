"""Bake ONE Mantaflow fire+smoke sim for the burning rack (lobby, behind the glass) and cache it for both formats.

  Blender -b --factory-startup --python fire_bake.py -- <res> [frame_end]

Writes blender/short/fire_sim_v1.blend (domain + flow, cache in blender/short/cache/fire_v1) and
short/data/fire_flame_v1.json: per-frame summed flame + its centroid, so the fire's light follows the sim.
Coordinates: the lobby of AFF_blk_s01_intro (burn_rack at x -3.75..-3.15, y 5.45..6.25, z 0..1.2).
CPU sim (not the GPU queue).
"""
import bpy, sys, os, json, math

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
RES = int(ARGS[0]) if ARGS else 96
F0, F1 = int(os.environ.get("FIRE_F0", "300")), int(ARGS[1]) if len(ARGS) > 1 else 580
SHORT = os.path.expanduser("~/Documents/Original Music/" + os.environ.get("AFF_PROJ", "Asking for a Friend 2") + "/blender/short")
TAG = ARGS[2] if len(ARGS) > 2 else "v1"
OUT = os.path.join(SHORT, f"fire_sim_{TAG}.blend")
CACHE = os.path.join(SHORT, "cache", f"fire_{TAG}")
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
assert not os.path.exists(OUT), "never save over an existing blend: " + OUT
os.makedirs(CACHE, exist_ok=True)

sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
sc.frame_start, sc.frame_end = F0, F1
sc.render.fps = 24


def cube(name, mn, mx):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.location = [(mn[i] + mx[i]) / 2 for i in range(3)]
    o.scale = [(mx[i] - mn[i]) for i in range(3)]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


DZ = float(os.environ.get("FIRE_DZ", "4.95"))
dom = cube("FIRE_domain", (-4.45, 5.22, 0.0), (-2.45, 6.95, DZ))
flow = cube("FIRE_flow", (-3.68, 5.52, 1.205), (-3.22, 6.18, 1.45))     # the rack's top, where the fire sits
flow2 = cube("FIRE_flow_vent", (-3.70, 5.30, float(os.environ.get("FIRE_VENT_Z0", "0.62"))), (-3.20, 5.44, 1.10))  # the hot front vents (door side)
rack = cube("FIRE_rack_collider", (-3.75, 5.45, 0.0), (-3.15, 6.25, 1.2))

m = dom.modifiers.new("Fluid", "FLUID"); m.fluid_type = "DOMAIN"
d = m.domain_settings
d.domain_type = "GAS"
d.resolution_max = RES
d.cache_directory = CACHE
d.cache_type = "ALL"
d.cache_frame_end = F1
d.cache_frame_start = F0
d.cache_frame_end = F1
d.cache_data_format = "OPENVDB"
d.use_adaptive_domain = False
d.alpha = 0.6           # smoke buoyancy
d.beta = 1.4            # heat buoyancy
d.vorticity = float(os.environ.get("FIRE_VORT", "0.25"))
d.use_dissolve_smoke = True
d.dissolve_speed = 60
d.flame_vorticity = 0.6
d.burning_rate = 0.8
d.flame_smoke = 1.2
d.flame_ignition = 1.25
d.flame_max_temp = 2.2
d.timesteps_max = 4
d.timesteps_min = 1
d.use_noise = False
try:
    d.openvdb_cache_compress_type = "BLOSC"
except Exception:
    pass
for side in ("use_collision_border_bottom",):
    if hasattr(d, side):
        setattr(d, side, True)

for fo, rate in ((flow, 1.0), (flow2, 0.55)):
    mf = fo.modifiers.new("Fluid", "FLUID"); mf.fluid_type = "FLOW"
    s = mf.flow_settings
    s.flow_type = "BOTH"
    s.flow_behavior = "INFLOW"
    s.flow_source = "MESH"
    s.surface_distance = 1.0
    s.volume_density = 1.0
    s.fuel_amount = 1.4 * rate
    s.temperature = 1.6
    s.density = 0.6
    s.smoke_color = (0.12, 0.11, 0.10)
    s.use_initial_velocity = True
    s.velocity_normal = 0.25
    s.subframes = 1
    # flicker the inflow with seeded noise so the fire breathes (texture-driven fuel)
    tx = bpy.data.textures.new("fire_noise", "CLOUDS"); tx.noise_scale = 0.12
    s.noise_texture = tx
    s.texture_map_type = "AUTO"
    s.texture_size = 1.0
    s.texture_offset = 0.0
    s.use_texture = os.environ.get("FIRE_TEX", "1") == "1"
    s.texture_offset = 0.0
    fo.hide_render = True

mc = rack.modifiers.new("Fluid", "FLUID"); mc.fluid_type = "EFFECTOR"
rack.hide_render = True

bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
# move the noise offset over time so the fuel pattern changes (keyed: a pure function of the frame)
for fo in (flow, flow2):
    s = fo.modifiers["Fluid"].flow_settings
    s.texture_offset = 0.0
    s.keyframe_insert("texture_offset", frame=F0)
    s.texture_offset = (F1 - F0) * 0.035
    s.keyframe_insert("texture_offset", frame=F1)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("[fire] saved", OUT, "res", RES, "frames", F0, F1)
bpy.context.view_layer.objects.active = dom
dom.select_set(True)
with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom]):
    bpy.ops.fluid.bake_all()
print("[fire] baked")

rows = {}
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    dd = dom.evaluated_get(bpy.context.evaluated_depsgraph_get()).modifiers["Fluid"].domain_settings
    fl = list(dd.flame_grid) if len(dd.flame_grid) else []
    rows[f] = round(sum(fl), 3)
json.dump({"frames": rows, "res": RES, "note": "sum of the flame grid per frame (drives FireLight energy)"},
          open(os.path.join(DATA, f"fire_flame_{TAG}.json"), "w"), indent=0)
bpy.ops.wm.save_mainfile()
print("[fire] flame json written", len(rows))
