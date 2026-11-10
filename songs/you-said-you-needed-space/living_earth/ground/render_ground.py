"""Living Earth Cut 3: one habitat, photographed for the bridge and final chorus.

Run via render_ground.sh. Reuses the approved Ground v2 asset and material
setup. All actors, the hill, and its lighting are built and animated here.
"""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector


parser = argparse.ArgumentParser()
parser.add_argument("shot", choices=("br_children", "inst", "fc_life"))
parser.add_argument("fmt", choices=("169", "916"))
parser.add_argument("output", type=Path)
parser.add_argument("--still", type=int, help="Zero-based frame within the insert")
parser.add_argument("--draft", action="store_true")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

song = Path(__file__).resolve().parents[2]
approved = song / "pitch_mockups/ground2/ground2.py"
timing_source = (song / "remotion/src/le/film/timing.gen.ts").read_text()
timing, _ = json.JSONDecoder().raw_decode(timing_source.split("} = ", 1)[1])
fps = timing["fps"]
beat = timing["bar"] / 4
lines = timing["lines"]

# Load the approved material and glTF setup, stopping before its pitch-specific
# object placement, camera and EXR render. Its textures are already on the M5.
recipe, separator, _ = approved.read_text().partition("CAL, FERN, ROCK, PINE = NAMES")
if not separator:
    raise RuntimeError(f"Cannot locate the asset setup in {approved}")
recipe = recipe.replace(
    "argv = sys.argv[sys.argv.index('--') + 1:]",
    "argv = ['1', '', 'main', '16']",
)
palette = {"__file__": str(approved)}
exec(compile(recipe, str(approved), "exec"), palette)
scene = bpy.context.scene
put = palette["put"]
calathea, fern, rock, roots = palette["NAMES"]
rng = random.Random(923)
cyan = (0.02, 0.72, 0.85)
violet = (0.30, 0.10, 0.76)
pale = (0.34, 0.84, 1.0)


def material(name, color, roughness=0.65, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Emission Color"].default_value = (*color, 1)
    shader.inputs["Emission Strength"].default_value = emission
    return mat


def mesh(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for poly in data.polygons:
        poly.use_smooth = True
    return obj


def sphere(name, where, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, location=where)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def filament(name, points, radius, mat):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 1
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def terrain(x, y):
    crest = 0.62 * math.exp(-((y - 1.6) / 2.5) ** 2 - ((x + 0.4) / 5.0) ** 2)
    ripples = 0.038 * math.sin(x * 1.9 + y * 0.5) + 0.022 * math.sin(y * 2.6 - x * 1.3)
    weathered = 0.026 * math.sin(4.3 * x + 3.6 * y) * math.sin(5.4 * y - 0.8 * x)
    return crest + ripples + weathered


ground = material("Wet forest loam", (0.017, 0.046, 0.052), 0.72)
nt = ground.node_tree
shader = nt.nodes.get("Principled BSDF")
shader.inputs["Specular IOR Level"].default_value = 0.19
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 7
noise.inputs["Detail"].default_value = 4
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.18
ramp.color_ramp.elements[0].color = (0.004, 0.012, 0.016, 1)
ramp.color_ramp.elements[1].position = 0.84
ramp.color_ramp.elements[1].color = (0.016, 0.044, 0.049, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs[0])
nt.links.new(ramp.outputs[0], shader.inputs["Base Color"])
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.33
bump.inputs["Distance"].default_value = 0.14
nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
nx, ny = 89, 102
verts = [(x, y, terrain(x, y))
         for j in range(ny) for i in range(nx)
         for x, y in [(-13 + i * 0.30, -7 + j * 0.30)]]
faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
         for j in range(ny - 1) for i in range(nx - 1)]
mesh("The hillside", verts, faces, ground)

# A clear stage around the three figures, with the approved jungle at the
# edges, a wet footpath, and luminous understory stepping back into darkness.
hero_plants = (
    (calathea, -1.33, -1.45, 0.83, 0.2),
    (fern, 1.48, -1.35, 0.96, 0.0),
    (calathea, -1.85, -0.3, 0.92, 0.75),
    (fern, 1.55, 0.18, 0.81, 0.22),
    (calathea, 1.76, 0.8, 0.75, 0.95),
    (fern, -1.10, 0.12, 0.58, 0.35),
    (calathea, 0.30, -2.22, 0.47, 0.12),
    (fern, 0.77, -2.0, 0.60, 0.08),
)
for asset, x, y, size, hue in hero_plants:
    put(asset, x, y, size, z=terrain(x, y), hue=hue, gain=0.9, dew=1.0)
for _ in range(98):
    y = rng.uniform(-2.8, 13)
    x = rng.uniform(-9, 9)
    if abs(x + 0.12) < 1.17 and y < 3.1:
        continue
    asset = rng.choices((calathea, fern, rock, roots), (28, 40, 20, 12))[0]
    put(asset, x, y, rng.uniform(0.28, 1.05), z=terrain(x, y),
        hue=rng.uniform(0, 0.75), gain=rng.uniform(0.36, 0.85), dew=0.5)

bark = material("Wet indigo bark", (0.014, 0.037, 0.062), 0.53)
vein = material("Tree cambium", cyan, 0.42, 0.42)
tree_bloom = material("Tree flowers", violet, 0.55, 1.3)
tree_origin = Vector((-1.06, 2.15, terrain(-1.06, 2.15)))
tree_rng = random.Random(776)
leaf_clusters = []
flower_mesh = sphere("Tree flower source", (0, 0, -10), (1, 1, 1), tree_bloom)


def branch(start, drift, length, radius, depth):
    drift = drift.normalized()
    middle = start + drift * (0.46 * length) + Vector((0.03, 0, 0.035))
    end = start + drift * length + Vector((0, 0, 0.10 * length))
    filament("Tree branch", [start, middle, end], radius, bark)
    offset = Vector((radius * 0.28, -radius * 0.98, radius * 0.11))
    filament("Tree cambium", [start + offset, middle + offset, end + offset], radius * 0.095, vein)
    if depth == 0:
        for _ in range(4):
            bud = flower_mesh.copy()
            bud.data = flower_mesh.data
            scene.collection.objects.link(bud)
            bud.location = end + Vector((tree_rng.uniform(-0.14, 0.14), tree_rng.uniform(-0.14, 0.14), tree_rng.uniform(-0.13, 0.12)))
            s = tree_rng.uniform(0.018, 0.042)
            bud.scale = (s, s, 0.62 * s)
            leaf_clusters.append(bud)
        return
    for k in range(3 if depth > 1 else 2):
        spread = (k - 1.0) * 0.91
        child = drift * 0.58 + Vector((spread, tree_rng.uniform(-0.54, 0.65), 0.38))
        branch(middle if k == 0 and depth > 1 else end, child, length * tree_rng.uniform(0.54, 0.66), radius * 0.59, depth - 1)


branch(tree_origin, Vector((0.11, 0.03, 1)), 0.96, 0.10, 4)

# Narrow capillary strands hug the loam at the margins of the clearing.
loam_light = material("Wet capillary light", (0.035, 0.45, 0.57), 0.72, 0.24)
for i in range(14):
    side = -1 if i % 2 else 1
    x0 = side * rng.uniform(0.52, 2.45)
    y0 = rng.uniform(-2.8, 1.1)
    stride = rng.uniform(0.045, 0.105)
    trace = []
    for j in range(13):
        x = x0 + side * (0.018 * j + 0.045 * math.sin(i + j * 0.7))
        y = y0 + stride * j
        trace.append((x, y, terrain(x, y) + 0.018))
    filament("Ground plant vein", trace, 0.0016, loam_light)

coat = material("Indigo silhouette", (0.028, 0.10, 0.14), 0.58, 0.06)
seam = material("The figures' edge light", pale, 0.45, 1.0)
skin = material("The figures' blue light", (0.17, 0.50, 0.63), 0.50, 0.48)
thread_mat = material("Earth's thread", (0.16, 0.76, 0.92), 0.37, 1.9)
bead_mat = material("Thread pulse", pale, 0.36, 2.9)
star_mat = material("His amber star", (1.0, 0.57, 0.25), 0.4, 3.7)
star = sphere("His star", (2.1, 11.0, 3.1), (0.027, 0.027, 0.027), star_mat)
thread = filament("Thread from the child's hand", [(0, 0, -10)] * 25, 0.0023, thread_mat)
beads = [sphere("Pulse on the thread", (0, 0, -10), (0.011,) * 3, bead_mat) for _ in range(3)]
dots = [sphere("The pointing trace", (0, 0, -10), (0.008,) * 3, thread_mat) for _ in range(14)]


def cone(name, start, end, r0, r1, mat):
    a, b = Vector(start), Vector(end)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r0, radius2=r1, depth=(b - a).length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def figure(name, prefix, x, y, height):
    rig = bpy.data.objects.new(name, None)
    scene.collection.objects.link(rig)
    rig.location = (x, y, terrain(x, y))
    h = height
    pieces = [
        cone("Tapered coat", (0, 0, 0.23*h), (0, 0, 0.71*h), 0.149*h, 0.115*h, coat),
        cone("Shoulders", (0, 0, 0.65*h), (0, 0, 0.80*h), 0.115*h, 0.082*h, coat),
        sphere("Head tipped to the light", (0.012*h, 0, 0.90*h), (0.075*h, 0.077*h, 0.095*h), skin),
        filament("Coat piping", [(-0.105*h,-0.065*h,0.27*h),(-0.087*h,-0.073*h,0.61*h),(-0.077*h,-0.048*h,0.75*h)], 0.005*h, seam),
    ]
    for side in (-1, 1):
        dx = side * 0.063 * h
        pieces.append(cone("Boot", (dx, -0.018*h, 0.012*h), (dx*0.82, 0.008*h, 0.27*h), 0.043*h, 0.032*h, coat))
    for obj in pieces:
        obj.name = f"{prefix}_{obj.name}"
        obj.parent = rig
    return rig


people = [figure("Adult", "Person0", -0.29, 1.73, 0.69),
          figure("Child holding their hand", "Person1", -0.68, 1.68, 0.44),
          figure("Smallest child with the thread", "Person2", 0.12, 1.62, 0.35)]
rest = [obj.location.copy() for obj in people]
heights = (0.69, 0.44, 0.35)
arms = [[filament("Sleeve", [(0, 0, 0)] * 3, height * 0.032, skin) for _ in (-1, 1)]
        for height in heights]
hands = [[sphere("Hand", (0, 0, -10), (height * 0.032,) * 3, skin) for _ in (-1, 1)]
         for height in heights]
for i, person in enumerate(people):
    for obj in (*arms[i], *hands[i]):
        obj.name = f"Person{i}_{obj.name}"
        obj.parent = person
    if args.shot == "fc_life":
        for obj in person.children:
            obj.hide_render = True

seed_mesh = sphere("Ground seed light", (0, 0, -10), (1, 1, 1), tree_bloom)
flowers = []
bpy.context.view_layer.update()
plant_bounds = []
for obj in scene.objects:
    if obj.type == "MESH" and any(k in obj.name.lower() for k in ("fern", "calathea")):
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        plant_bounds.append(([min(c[k] for c in corners) for k in range(3)],
                             [max(c[k] for c in corners) for k in range(3)]))
for _ in range(88):
    x, y = rng.uniform(-4.0, 4.0), rng.uniform(-2.6, 4.4)
    if y > 0.8 and abs(x) < 0.73:
        continue
    z = terrain(x, y)
    h = rng.uniform(0.025, 0.21)
    top = Vector((x + rng.uniform(-0.035, 0.035), y, z + h))
    # Small blooms occupy open loam, clear of the approved foliage.
    if any(lo[0] - .04 <= x <= hi[0] + .04 and lo[1] - .04 <= y <= hi[1] + .04
           and lo[2] <= z + h + .03 and hi[2] >= z for lo, hi in plant_bounds):
        continue
    stem = filament("Growing stem", [(x, y, z), (x, y, z + h * 0.6), top], 0.0018, vein)
    bud = seed_mesh.copy()
    scene.collection.objects.link(bud)
    radius = rng.uniform(0.009, 0.025)
    flowers.append((stem, bud, Vector((x, y, z)), top, radius))

world = bpy.data.worlds.new("Deep indigo night")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.007, 0.012, 0.035, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.64
scene.world = world


def light(name, kind, where, target, color, energy, size):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if kind == "AREA":
        data.shape = "DISK"
        data.size = size
    else:
        data.shadow_soft_size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = where
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


light("Cold horizon", "AREA", (0.2, 6.0, 4.4), (0, 0, 0.3), (0.16, 0.58, 1.0), 380, 7)
light("Vein spill", "AREA", (-2.0, -1.5, 1.55), (0, 0.6, 0.1), (0.19, 0.76, 1.0), 76, 4)
light("Violet understory", "AREA", (3.0, 2.0, 1.65), (0, 1, 0.35), (0.45, 0.18, 1.0), 88, 3)
light("Light from the leaves", "POINT", (0.55, -2.0, 0.49), (0, 0, 0), (0.18, 0.70, 1.0), 8, 0.31)
light("Hill figures' cool rim", "AREA", (0, 3.2, 1.53), (0, 1.7, 0.9), (0.36, 0.78, 1.0), 26, 2.2)

# Sparse distant lights and small volumetric motes give three depth planes.
sky_mat = material("Distant blue starlight", (0.38, 0.53, 0.79), 0.5, 0.38)
seed = sphere("Blue starlight source", (0, 0, -12), (1, 1, 1), sky_mat)
for _ in range(100):
    obj = seed.copy()
    scene.collection.objects.link(obj)
    obj.location = (rng.uniform(-25, 25), 24 + rng.uniform(-1, 1), rng.uniform(1.7, 14))
    obj.scale = (rng.uniform(0.012, 0.032),) * 3
motes = []
for _ in range(34):
    obj = seed.copy()
    scene.collection.objects.link(obj)
    position = Vector((rng.uniform(-3.6, 3.6), rng.uniform(-2.0, 6.0), rng.uniform(0.35, 1.9)))
    obj.scale = (rng.uniform(0.003, 0.014),) * 3
    motes.append((obj, position, rng.uniform(0, math.tau)))

camera = bpy.data.cameras.new("Ground lens")
camera_obj = bpy.data.objects.new("Ground lens", camera)
scene.collection.objects.link(camera_obj)
scene.camera = camera_obj
camera.sensor_fit = "VERTICAL"
camera.sensor_height = 20.25
camera.dof.use_dof = True

first_visit = lines["bridgeA"][1]
first_visit_end = lines["bridgeA"][2]["t"]
inst = timing["sections"]["instrumental"][0]
inst_end = lines["finalChorus"][0]["t"]
life = lines["finalChorus"][9]["t"]
life_end = lines["finalChorus"][10]["t"]
nearest = lambda t: math.floor(t * fps + 0.5)
spans = {
    "br_children": (nearest(first_visit["t"]), nearest(first_visit_end)),
    "inst": (math.ceil(inst * fps), math.ceil((inst_end - 0.001) * fps)),
    "fc_life": (nearest(life), nearest(life_end)),
}
start, end = spans[args.shot]
count = end - start


def sat(x):
    return max(0.0, min(1.0, x))


def smooth(a, b, x):
    u = sat((x - a) / (b - a))
    return u * u * (3 - 2 * u)


def path(a, b, u, sag):
    return a.lerp(b, u) + Vector((0, 0, -sag * math.sin(math.pi * u)))


def points(obj, coords):
    for p, co in zip(obj.data.splines[0].points, coords):
        p.co = (*co, 1)


def pose(frame):
    t = (start + frame) / fps
    sec = frame / fps
    u = sat(frame / max(1, count - 1))
    vertical = args.fmt == "916"
    repeat = args.shot == "inst"
    on_hill = args.shot != "fc_life"
    tugs = [inst + i * beat for i in (2, 5, 8)]
    for obj, p, phase in motes:
        obj.location = p + Vector((0.055 * math.sin(sec * 0.54 + phase), 0, 0.08 * math.sin(sec * 0.74 + phase)))
    for stem, bud, bottom, top, rad in flowers:
        born = 0.3 + (top - rest[2]).length * 0.63
        grow = 0.62 if not on_hill else smooth(born, born + 0.72, sec) if repeat else 0.21
        stem.scale = (1, 1, 1)
        p = bottom.lerp(top, grow)
        points(stem, [bottom, bottom.lerp(p, 0.55), p])
        bud.location = p
        bud.scale = (rad * grow, rad * grow, rad * grow * 0.58)

    for person, p in zip(people, rest):
        person.location = p
    if repeat:
        people[2].location.z += sum(0.018 * math.sin(math.pi * sat((t - b + 0.04) / 0.32)) for b in tugs)
    elif on_hill:
        people[2].location.z += 0.038 * math.sin(math.pi * sat((t - first_visit["words"][3][0] - 0.1) / 0.36))

    star.location = (1.45 if vertical else 2.55, 10.2, 3.04 if vertical else 2.85)
    if repeat:
        answer = sum(math.exp(-((t - b - 1.1) / 0.17) ** 2) for b in tugs)
    else:
        answer = math.exp(-((t - first_visit["words"][-1][0] - 0.12) / 0.18) ** 2)
    star.scale = (0.025 * (1 + 0.5 * min(answer, 1)),) * 3

    clasp = rest[0].lerp(rest[1], 0.54) + Vector((0, -0.019, 0.25))
    raised = {}
    for i, (obj, h) in enumerate(zip(people, heights)):
        for j, side in enumerate((-1, 1)):
            shoulder = obj.location + Vector((side * 0.115 * h, 0, 0.75 * h))
            down = Vector((side * 0.08, -0.12, -0.40)).normalized()
            if (i, j) in ((0, 0), (1, 1)):
                end_hand = clasp + Vector(((1 if i == 0 else -1) * (0.032 * h + 0.003), 0, 0))
            else:
                pointing = 0
                if on_hill and side == 1 and i in (0, 2):
                    if repeat:
                        pointing = int(i == 2)
                    else:
                        onset = first_visit["words"][0 if i == 0 else 3][0] + 0.06
                        pointing = smooth(onset, onset + 0.5, t)
                aim = Vector((0.43, 0.42, 0.76))
                end_hand = shoulder + down.lerp(aim, pointing).normalized() * (0.37 * h)
                if repeat and i == 2 and side == 1:
                    pull = sum(math.exp(-((t - b) / 0.14) ** 2) for b in tugs)
                    end_hand += Vector((-0.024, -0.034, -0.055)) * pull
            elbow = shoulder.lerp(end_hand, 0.52) + Vector((side * 0.032 * h, -0.029 * h, -0.01 * h))
            points(arms[i][j], [p - obj.location for p in (shoulder, elbow, end_hand)])
            hands[i][j].location = end_hand - obj.location
            if side == 1:
                raised[i] = end_hand

    thread.hide_render = not repeat
    sag = 0.48 - 0.11 * sum(math.exp(-((t - b) / 0.19) ** 2) for b in tugs)
    star_line = (star.location - raised[2]).normalized()
    thread_start = raised[2] + star_line * (heights[2] * 0.032 + 0.003)
    thread_end = star.location - star_line * (star.scale.x + 0.004)
    if repeat:
        points(thread, [path(thread_start, thread_end, i / 24, sag) for i in range(25)])
    for obj, b in zip(beads, tugs):
        progress = (t - b - 0.10) / 1.0
        obj.hide_render = not repeat or not (0 <= progress <= 1)
        obj.location = path(thread_start, thread_end, sat(progress), sag)
    reveal = smooth(first_visit["words"][2][0] + 0.20, first_visit["words"][-1][0] + 0.08, t)
    for i, obj in enumerate(dots):
        v = (i + 1) / (len(dots) + 1)
        obj.hide_render = args.shot != "br_children" or reveal < v
        obj.location = path(raised[0], star.location, v, 0.20)

    if on_hill:
        camera_obj.location = ((-0.32 if vertical else -0.52) + 0.15 * u,
                               (-4.45 if vertical else -3.72) + (0.70 if repeat else 0.31) * u,
                               0.48 + (0.04 if repeat else 0.02) * u)
        camera.lens = (27 if vertical else 23) + (4 if repeat else 0)
        target = Vector((0.05 if vertical else 0.18, 2.0, 1.31 if vertical else 1.18))
        camera.dof.focus_distance = (rest[0] - camera_obj.location).length
        camera.dof.aperture_fstop = 4.0
    else:
        # Three cuts on the original beat boundaries. Same habitat, from a
        # damp leaf edge, to a fern canopy, to a low bloom against the hill.
        cut1, cut2 = nearest(life + beat), nearest(life + 2 * beat)
        index = 0 if start + frame < cut1 else 1 if start + frame < cut2 else 2
        loc, target, lens = [
            ((0.17, -2.92, 0.27), (0.31, -1.97, 0.31), 39),
            ((-2.28, -0.55, 0.35), (-1.63, 0.19, 0.62), 32),
            ((2.30, -2.65, terrain(2.30, -2.65) + 0.40), (1.48, -1.35, terrain(1.48, -1.35) + 0.38), 35),
        ][index]
        camera_obj.location = Vector(loc) + Vector((0.055 * u, 0.064 * u, 0.018 * u))
        target = Vector(target)
        camera.lens = lens - (3 if vertical else 0)
        camera.dof.focus_distance = (target - camera_obj.location).length
        camera.dof.aperture_fstop = 3.0
    camera_obj.rotation_euler = (target - camera_obj.location).to_track_quat("-Z", "Y").to_euler()


# Mild emitter glare. The film's existing grade handles the final ceiling.
scene.view_settings.view_transform = "AgX"
scene.view_settings.exposure = 0.18
if bpy.app.version < (5, 0, 0):
    scene.use_nodes = True
    comp = scene.node_tree
else:
    comp = bpy.data.node_groups.new("Ground glow", "CompositorNodeTree")
    scene.compositing_node_group = comp
comp.nodes.clear()
layers = comp.nodes.new("CompositorNodeRLayers")
glare = comp.nodes.new("CompositorNodeGlare")
if bpy.app.version < (5, 0, 0):
    glare.glare_type = "FOG_GLOW"
    glare.quality = "MEDIUM"
    glare.threshold = 1.25
    glare.size = 7
    output = comp.nodes.new("CompositorNodeComposite")
else:
    comp.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    output = comp.nodes.new("NodeGroupOutput")
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Quality"].default_value = "High"
    for key, value in (("Threshold", 1.25), ("Strength", 0.30), ("Size", 0.5)):
        if key in glare.inputs:
            glare.inputs[key].default_value = value
comp.links.new(layers.outputs["Image"], glare.inputs["Image"])
comp.links.new(glare.outputs["Image"], output.inputs["Image"])

render = scene.render
render.fps = fps
render.resolution_x, render.resolution_y = (2560, 1440) if args.fmt == "169" else (1080, 1920)
render.resolution_percentage = 50 if args.draft else 100
render.film_transparent = False
scene.eevee.taa_render_samples = 12 if args.draft else 24
scene.eevee.use_raytracing = False
args.output.parent.mkdir(parents=True, exist_ok=True)
render.filepath = str(args.output)
print(f"GROUND {args.shot} {args.fmt}: song frames {start}–{end - 1}, {count} source frames, {fps}fps", flush=True)
if args.still is not None:
    if not 0 <= args.still < count:
        parser.error(f"--still must be within 0–{count - 1}")
    render.image_settings.file_format = "PNG"
    pose(args.still)
    bpy.ops.render.render(write_still=True)
else:
    # Stream to Blender's H.264 encoder to avoid keeping a frame sequence.
    settings = render.image_settings
    if hasattr(settings, "media_type"):
        settings.media_type = "VIDEO"
    else:
        settings.file_format = "FFMPEG"
    render.ffmpeg.format = "MPEG4"
    render.ffmpeg.codec = "H264"
    render.ffmpeg.constant_rate_factor = "HIGH"
    render.use_file_extension = False
    scene.frame_start = 0
    scene.frame_end = count - 1

    def on_frame(current_scene, _depsgraph=None):
        pose(current_scene.frame_current)

    bpy.app.handlers.frame_change_pre.append(on_frame)
    pose(0)
    bpy.ops.render.render(animation=True)
