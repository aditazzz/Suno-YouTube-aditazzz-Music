"""Run It: the workbench set. Everything except Claude and the car is built here, by hand, from primitives with bevels.
Layout (metres, Z up): Claude stands at (0, .47) behind the bench facing -Y (toward the camera). The city sits on a
turntable in the middle of the bench. Screen right = +X."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler
from wb import *
BZ = BENCH_Z
C = Vector((0.0, 0.02, 0.0))          # turntable centre on the bench
R_TABLE, R_WATER, R_ISLE = 0.30, 0.292, 0.205
WATER_Z = BZ + 0.0215; ISLE_Z = BZ + 0.0275       # top of water, top of island
CLAUDE_Y = 0.45
PAL = {'teal': (.03, .30, .32), 'cobalt': (.035, .10, .42), 'sky': (.22, .50, .78), 'sage': (.30, .50, .36), 'cream': (.82, .76, .62),
       'butter': (.85, .66, .22), 'char': (.045, .05, .06), 'mint': (.45, .78, .66)}
# the city's blocks get deeper paints than the props (Nov 11, her note: the pale ones blew out under the lamp); same hues, lower value
BPAL = {'teal': (.03, .30, .32), 'cobalt': (.035, .10, .42), 'sky': (.10, .30, .62), 'sage': (.17, .34, .22), 'cream': (.50, .38, .22),
        'butter': (.62, .38, .07), 'char': (.045, .05, .06), 'mint': (.16, .46, .36)}


def cutting_mat():
    m = D.materials.new('WB_cutmat'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord'); br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0
    br.inputs['Scale'].default_value = 20; br.inputs['Mortar Size'].default_value = .012; br.inputs['Brick Width'].default_value = 1; br.inputs['Row Height'].default_value = 1
    br.inputs['Color1'].default_value = (.012, .075, .07, 1); br.inputs['Color2'].default_value = (.012, .075, .07, 1); br.inputs['Mortar'].default_value = (.30, .46, .40, 1)
    nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .62
    return m


def mats():
    M = {}
    M['bench'] = wood('WB_bench', (.040, .026, .018), (.105, .066, .040), 3.0, .40)
    M['ply'] = wood('WB_ply', (.32, .28, .23), (.46, .41, .34), 6.0, .55)
    M['leg'] = wood('WB_leg', (.02, .017, .015), (.05, .04, .034), 2.0, .6)
    M['water'] = mat('WB_water', (.006, .075, .095), rough=.04, coat=1.0, spec=.9)
    nt = M['water'].node_tree; b = nt.nodes.get('Principled BSDF'); tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.name = 'WATER_MAP'
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 55; nz.inputs['Detail'].default_value = 2.5; nz.inputs['Roughness'].default_value = .5
    bp = nt.nodes.new('ShaderNodeBump'); bp.name = 'WATER_BUMP'; bp.inputs['Strength'].default_value = .16; bp.inputs['Distance'].default_value = .004
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector']); nt.links.new(nz.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    M['ground'] = mat('WB_ground', (.25, .27, .255), rough=.8)
    M['sand'] = mat('WB_sand', (.49, .45, .36), rough=.9)
    M['road'] = mat('WB_road', (.03, .033, .04), rough=.7)
    M['plaza'] = mat('WB_plaza', (.50, .48, .42), rough=.7)
    M['line'] = mat('WB_line', (.85, .83, .75), rough=.6)
    M['steel'] = mat('WB_steel', (.55, .57, .60), rough=.28, metal=1.0)
    M['black'] = mat('WB_black', (.012, .013, .016), rough=.45)
    M['enamel'] = mat('WB_enamel', (.03, .16, .17), rough=.18, coat=1.0)        # lamp shade: deep teal enamel
    M['white'] = mat('WB_white', (.85, .84, .80), rough=.4)
    M['bulb'] = mat('WB_bulb', (1, .9, .75), emit=(1.0, .80, .52), es=40.0)
    M['dot'] = mat('WB_dot', (1.0, .10, .45), emit=(1.0, .08, .42), es=14.0, rough=.3)
    M['can'] = mat('WB_can', (.62, .62, .57), rough=.2, coat=1.0)              # watering can: pale sage enamel
    M['canrim'] = mat('WB_canrim', (.02, .05, .16), rough=.25, coat=1.0)
    M['drop'] = mat('WB_drop', (.75, .9, 1.0), rough=.02, spec=1.0, emit=(.60, .82, 1.0), es=1.6)
    M['wall'] = mat('WB_wall', (.016, .026, .032), rough=.9)
    M['floor'] = wood('WB_floor', (.012, .011, .011), (.035, .030, .028), 1.2, .55)
    M['peg'] = mat('WB_peg', (.035, .042, .046), rough=.85)
    M['fairy'] = mat('WB_fairy', (1, .85, .6), emit=(1.0, .78, .46), es=22.0)
    M['win'] = mat('WB_win', (.2, .35, .8), emit=(.10, .22, .60), es=3.0)
    M['glass'] = mat('WB_glass', (.8, .9, .9), rough=.05, alpha=.28, spec=.8)
    M['mat'] = cutting_mat()
    M['tree'] = mat('WB_tree', (.10, .34, .20), rough=.9)
    M['trunk'] = mat('WB_trunk', (.08, .07, .06), rough=.8)
    for k, c in BPAL.items(): M['b_' + k] = building_mat('WB_b_' + k, c)
    for k, c in BPAL.items(): M['h_' + k] = mat('WB_h_' + k, c, rough=.5)            # the little houses
    for k, c in PAL.items(): M['p_' + k] = mat('WB_p_' + k, c, rough=.5)
    return M


def prism(name, L, w, r, loc, m, coll='SET'):
    """A pitched roof: ridge along X, half-width w, height r, base at loc."""
    me = D.meshes.new(name); h = L / 2
    me.from_pydata([(-h, -w, 0), (-h, w, 0), (-h, 0, r), (h, -w, 0), (h, w, 0), (h, 0, r)], [], [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)])
    me.update(); o = D.objects.new(name, me); o.location = loc; bpy.context.scene.collection.objects.link(o); return finish(o, m, 0, smooth=False, coll=coll)


# ---------------------------------------------------------------- room and bench
WALL_Y = 1.5; WIN = (-1.3, 1.3, .62, 2.30)          # the big workshop window behind him: x0, x1, z0, z1


def outside_mat(name, scale):
    m = building_mat(name, (.010, .014, .022), lit=(1., .80, .50), bias=.72)
    for n in m.node_tree.nodes:
        if n.type == 'TEX_BRICK': n.inputs['Scale'].default_value = scale
        if n.type == 'BSDF_PRINCIPLED': n.inputs['Emission Strength'].default_value = 1.6
    return m


def room(M):
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0)); finish(bpy.context.active_object, M['floor'], smooth=False).name = 'floor'
    x0, x1, z0, z1 = WIN
    box('wall_L', (4.0, .12, 3.4), (x0 - 2.0, WALL_Y + .06, 1.7), M['wall'], 0); box('wall_R', (4.0, .12, 3.4), (x1 + 2.0, WALL_Y + .06, 1.7), M['wall'], 0)
    box('wall_sill', (x1 - x0, .12, z0), (0, WALL_Y + .06, z0 / 2), M['wall'], 0); box('wall_lintel', (x1 - x0, .12, 3.4 - z1), (0, WALL_Y + .06, (3.4 + z1) / 2), M['wall'], 0)
    box('wall_left', (.12, 6, 3.4), (-3.2, 0, 1.7), M['wall'], 0)
    box('sill', (x1 - x0 + .12, .20, .035), (0, WALL_Y - .04, z0 + .017), M['leg'], .004)
    nx, nz = 5, 3
    for i in range(nx + 1): box(f'mull_v{i}', (.028 if 0 < i < nx else .05, .05, z1 - z0), (x0 + (x1 - x0) * i / nx, WALL_Y + .02, (z0 + z1) / 2), M['black'], .003)
    for j in range(nz + 1): box(f'mull_h{j}', (x1 - x0, .05, .028 if 0 < j < nz else .05), (0, WALL_Y + .02, z0 + (z1 - z0) * j / nz), M['black'], .003)
    # the night outside: a sky card, dark towers with lit windows, and loose lights that turn into bokeh
    sky = D.materials.new('WB_sky'); sky.use_nodes = True; nt = sky.node_tree; b = nt.nodes.get('Principled BSDF'); tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ')
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = .30; rp.color_ramp.elements[0].color = (.012, .085, .12, 1); rp.color_ramp.elements[1].position = .62; rp.color_ramp.elements[1].color = (.004, .010, .035, 1)
    nt.links.new(tc.outputs['Generated'], sx.inputs[0]); nt.links.new(sx.outputs['Z'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.6; b.inputs['Base Color'].default_value = (0, 0, 0, 1)
    box('sky', (22, .05, 9), (0, 9.5, 2.2), sky, 0)
    random.seed(31); om = [outside_mat('WB_out_a', 13.0), outside_mat('WB_out_b', 9.0)]
    for i in range(16):
        w = random.uniform(.6, 1.3); h = random.uniform(.7, 2.2) + (1.2 if i in (2, 11) else 0); x = -6.4 + i * .85 + random.uniform(-.25, .25); y = random.uniform(6.6, 9.0)
        box(f'tower{i}', (w, w, h), (x, y, h / 2 - .2), om[i % 2], 0)['lit'] = 1.0
    cols = [(1.0, .80, .52), (1.0, .88, .70), (.70, .84, 1.0), (.20, .85, .80), (.25, .45, 1.0), (1.0, .80, .52)]
    for i in range(70):
        c = random.choice(cols); m = mat(f'WB_bk{cols.index(c)}_{i % 3}', c, emit=c, es=[5, 10, 18][i % 3])
        z = .45 + abs(random.gauss(0, .38)); sph(f'bokeh{i}', random.uniform(.012, .028), (random.uniform(-4.6, 4.6), random.uniform(4.0, 6.2), z), m, seg=8)
    # fairy lights draped across the top of the window
    n = 30
    for i in range(n):
        u = i / (n - 1); x = x0 - .15 + (x1 - x0 + .3) * u; sag = .13 * math.sin(math.pi * ((u * 2) % 1.0)); z = z1 - .03 - sag + random.uniform(-.008, .008)
        sph(f'fairy{i}', .0095, (x, WALL_Y - .03, z), M['fairy'], seg=12)
    # shelves either side of the window, low key
    for sgn in (-1, 1):
        for k, zz in enumerate((.92, 1.38, 1.84)):
            box(f'shelf{sgn}{k}', (.9, .22, .025), (sgn * 1.95, WALL_Y - .12, zz), M['leg'], .004)
            x = sgn * 1.95 - .38
            while x < sgn * 1.95 + .36:
                w_ = random.uniform(.07, .2); h_ = random.uniform(.09, .26); kk = random.choice(['cream', 'sage', 'teal', 'char', 'cobalt', 'char', 'cream'])
                if random.random() < .3: cyl(f'jar{sgn}{k}{int(x * 100)}', w_ * .4, h_, (x + w_ / 2, WALL_Y - .12, zz + .0125 + h_ / 2), M['p_' + kk], 24, .004)
                else: box(f'sbox{sgn}{k}{int(x * 100)}', (w_, .16, h_), (x + w_ / 2, WALL_Y - .12, zz + .0125 + h_ / 2), M['p_' + kk], .005)
                x += w_ + random.uniform(.015, .05)


def bench(M):
    box('bench_top', (1.70, .70, .045), (0, -.03, BZ - .0225), M['bench'], .006)
    for i, (x, y) in enumerate([(-.78, -.32), (.78, -.32), (-.78, .26), (.78, .26)]): box(f'bench_leg{i}', (.07, .07, BZ - .045), (x, y, (BZ - .045) / 2), M['leg'], .005)
    box('bench_apron_f', (1.56, .025, .07), (0, -.335, BZ - .08), M['leg'], .004); box('bench_apron_b', (1.56, .025, .07), (0, .275, BZ - .08), M['leg'], .004)
    box('bench_shelf', (1.56, .5, .02), (0, -.03, .10), M['leg'], .004)
    box('cutmat', (1.05, .62, .004), (0, -.03, BZ + .002), M['mat'], .002)


# ---------------------------------------------------------------- the turntable, the ocean, the island
def table(M):
    root = empty('TABLE', (C.x, C.y, BZ))
    P = lambda o: parent(o, root)
    P(cyl('tt_base', R_TABLE, .014, (C.x, C.y, BZ + .011), M['ply'], 96, .003))
    P(cyl('tt_foot', .12, .008, (C.x, C.y, BZ + .004), M['black'], 48, .001))
    P(torus('tt_rim', R_TABLE - .004, .0065, (C.x, C.y, BZ + .024), M['white']))
    P(cyl('ocean_bed', R_WATER, .002, (C.x, C.y, BZ + .019), M['sand'], 96, 0))
    P(cyl('ocean', R_WATER, .002, (C.x, C.y, WATER_Z - .001), M['water'], 96, 0))
    P(cyl('beach', R_ISLE + .012, .0035, (C.x, C.y, WATER_Z + .0008), M['sand'], 96, .0015))
    P(cyl('island', R_ISLE, ISLE_Z - WATER_Z + .004, (C.x, C.y, (ISLE_Z + WATER_Z - .004) / 2), M['ground'], 96, .002))
    z = ISLE_Z + .0006
    # the boulevard runs from the plaza straight at the camera; the cross avenue and the back street are narrower
    P(box('boulevard', (.046, R_ISLE - .004, .0012), (C.x, C.y - R_ISLE / 2, z), M['road'], 0)); P(box('street_n', (.020, R_ISLE - .01, .0012), (C.x, C.y + R_ISLE / 2, z), M['road'], 0))
    P(box('avenue', (R_ISLE * 1.94, .026, .0012), (C.x, C.y, z), M['road'], 0))
    for sgn in (-1, 1):
        P(box(f'street_a{sgn}', (R_ISLE * 1.66, .012, .0012), (C.x, C.y + sgn * .111, z), M['road'], 0)); P(box(f'street_b{sgn}', (.012, R_ISLE * 1.66, .0012), (C.x + sgn * .111, C.y, z), M['road'], 0))
    for i in range(3, 13): P(box(f'dash{i}', (.0016, .009, .0004), (C.x, C.y - i * .0155, z + .0008), M['line'], 0))
    for sgn in (-1, 1): P(box(f'kerb{sgn}', (.0022, R_ISLE - .05, .0016), (C.x + sgn * .0245, C.y - R_ISLE / 2 - .012, z + .0006), M['plaza'], .0004))
    P(cyl('plaza', .043, .002, (C.x, C.y, z + .0006), M['plaza'], 64, .0006))
    P(torus('plaza_ring', .034, .0012, (C.x, C.y, z + .0018), M['p_teal']))
    P(cyl('dot_stand', .0050, .012, (C.x, C.y, z + .007), M['white'], 24, .0008))
    P(sph('DOT', .0085, (C.x, C.y, z + .0205), M['dot']))
    dl = light('dot_light', 'POINT', (C.x, C.y, z + .034), .42, (1.0, .15, .5), .01); parent(dl, root)
    # pier, toward the camera on screen left
    a = math.radians(214); ex, ey = math.cos(a), math.sin(a)
    for i in range(7):
        r = R_ISLE + .004 + i * .0105; P(box(f'pier{i}', (.009, .026, .0016), (C.x + ex * r, C.y + ey * r, WATER_Z + .006), M['ply'], .0004, rot=(0, 0, a)))
    for i in (1, 3, 5):
        r = R_ISLE + .004 + i * .0105
        for s in (-1, 1): P(cyl(f'pierpost{i}{s}', .0014, .012, (C.x + ex * r - ey * s * .012, C.y + ey * r + ex * s * .012, WATER_Z + .002), M['trunk'], 8, 0))
    return root


def city(M, root, seed=7):
    """Painted blocks on a street grid, tall in the middle, low at the shore. Returns a list of (obj, x, y, h)."""
    random.seed(seed); out = []
    xs = [-.170, -.134, -.088, -.050, .050, .088, .134, .170]; ys = [-.170, -.134, -.088, -.052, .050, .086, .134, .170]
    cols = ['teal', 'cobalt', 'sky', 'sage', 'cream', 'butter', 'mint', 'cream', 'teal', 'sky']
    n = 0
    for x in xs:
        for y in ys:
            d = math.hypot(x, y)
            if d > R_ISLE - .026: continue
            if abs(x) < .06 and y < -.16: continue                              # keep the mouth of the boulevard open to the camera
            fx = random.uniform(.026, .032); fy = random.uniform(.026, .032)
            h = (.155 * max(0, 1 - d / .215) ** 1.25 + .020) * random.uniform(.62, 1.22)
            if y < 0: h *= .82                                                  # terraced toward the camera
            h = max(.016, min(.17, h)); k = random.choice(cols); px, py = C.x + x + random.uniform(-.002, .002), C.y + y + random.uniform(-.002, .002)
            kind = random.random()
            if h < .034 and kind < .55:                                         # a little house with a pitched roof
                o = box(f'blk{n}', (fx, fy, h), (px, py, ISLE_Z + h / 2), M['h_' + k], .0012)
                parent(prism(f'roof{n}', fx * 1.06, fy * .56, fy * .42, (px, py, ISLE_Z + h), M['p_char']), root)
            elif kind > .90 and h > .05:                                        # a round tower
                o = cyl(f'blk{n}', fx * .52, h, (px, py, ISLE_Z + h / 2), M['b_' + k], 40, .0012); o['lit'] = 1.0
            else:
                o = box(f'blk{n}', (fx, fy, h), (px, py, ISLE_Z + h / 2), M['b_' + k], .0012); o['lit'] = 1.0
                if kind < .30 and h > .06:                                      # stepped top
                    h2 = h * random.uniform(.18, .34); s = box(f'step{n}', (fx * .62, fy * .62, h2), (px, py, ISLE_Z + h + h2 / 2), M['b_' + k], .001); s['lit'] = 1.0; parent(s, root); h += h2
                    if random.random() < .5: parent(cyl(f'mast{n}', .0007, .03, (px, py, ISLE_Z + h + .015), M['steel'], 8, 0), root)
                elif kind < .55 and h > .045:                                   # a roof box and a tank
                    parent(box(f'ac{n}', (fx * .3, fy * .25, .004), (px - fx * .18, py + fy * .15, ISLE_Z + h + .002), M['p_char'], .0005), root)
                    if random.random() < .5: parent(cyl(f'tank{n}', .004, .007, (px + fx * .2, py - fy * .15, ISLE_Z + h + .0035), M['p_cream'], 16, .0006), root)
            parent(o, root); out.append((o, px, py, h)); n += 1
    # trees round the plaza and along the shore
    random.seed(seed + 1)
    for i in range(26):
        a = random.uniform(0, math.tau); r = random.choice([.039, .039, R_ISLE - .012, R_ISLE - .008, R_ISLE - .016]); x, y = C.x + r * math.cos(a), C.y + r * math.sin(a)
        if abs(y - C.y) < .018 or abs(x - C.x) < .028: continue
        if any(abs(x - bx) < .022 and abs(y - by) < .022 for _, bx, by, _ in out): continue
        s = random.uniform(.0045, .0075); parent(cyl(f'trunk{i}', .0009, .008, (x, y, ISLE_Z + .004), M['trunk'], 8, 0), root); parent(sph(f'tree{i}', s, (x, y, ISLE_Z + .008 + s * .7), M['tree'], seg=16), root)
    return out


# ---------------------------------------------------------------- the lamp (the sun)
def lamp(M, base=(.70, .20), elbow=(.80, .30, .80), head=(.47, -.06, 1.00), aim=None, watts=45):      # 140 burnt the city out once it was really aimed at it
    aim = aim or (C.x + .02, C.y, BZ + .04)
    root = empty('LAMP', (base[0], base[1], BZ)); P = lambda o: parent(o, root)
    P(cyl('lamp_base', .055, .018, (base[0], base[1], BZ + .009), M['black'], 48, .003))
    P(cyl('lamp_stem', .011, .03, (base[0], base[1], BZ + .033), M['steel'], 24, .001))

    def rod(name, a, b, r=.0045, m=None):
        a, b = Vector(a), Vector(b); d = b - a; o = cyl(name, r, d.length, (a + b) / 2, m or M['steel'], 16, 0); o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); return P(o)
    p0 = Vector((base[0], base[1], BZ + .048)); e = Vector(elbow); h = Vector(head)
    for k, off in enumerate((Vector((.012, 0, 0)), Vector((-.012, 0, 0)))): rod(f'lamp_arm1_{k}', p0 + off, e + off); rod(f'lamp_arm2_{k}', e + off, h + off)
    P(sph('lamp_j0', .013, p0, M['black'], seg=16)); P(sph('lamp_j1', .013, e, M['black'], seg=16)); P(sph('lamp_j2', .013, h, M['black'], seg=16))
    hd = empty('LAMP_HEAD', h); parent(hd, root)
    d = (Vector(aim) - h).normalized(); q = d.to_track_quat('Z', 'Y')            # shade axis +Z points at the aim

    def along(o, dist): o.location = h + d * dist; o.rotation_euler = q.to_euler(); bpy.context.view_layer.update(); return parent(o, hd)
    sh = cyl('lamp_shade', .034, .12, (0, 0, 0), M['enamel'], 64, 0, r2=.085)
    bm = bmesh.new(); bm.from_mesh(sh.data); bm.faces.ensure_lookup_table()                     # open the wide end
    f = max([f for f in bm.faces if len(f.verts) > 4], key=lambda f: f.calc_center_median().z); bmesh.ops.delete(bm, geom=[f], context='FACES_ONLY'); bm.to_mesh(sh.data); bm.free()
    sh.data.materials.append(M['white']); so = sh.modifiers.new('sol', 'SOLIDIFY'); so.thickness = .0025; so.offset = 1; so.material_offset = 1; so.use_rim = True
    along(sh, .075)
    along(cyl('lamp_cap', .036, .03, (0, 0, 0), M['enamel'], 48, .004), .004)
    along(sph('lamp_bulb', .026, (0, 0, 0), M['bulb'], seg=24), .075)
    key = light('KEY', 'SPOT', h + d * .10, watts, (1.0, .80, .58), .035, spot=74, blend=.75); key.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update(); parent(key, hd)
    return root


# ---------------------------------------------------------------- props
def watering_can(M):
    """Enamelware can with a bail handle over the top. Origin = the top of the handle (where his hand closes).
    +X is toward the spout; the handle bar runs along X at the origin."""
    root = empty('CAN', (0, 0, 0), 'PROPS'); P = lambda o: parent(col_link(o, 'PROPS'), root)
    zt = -.050                                                                    # body top
    P(cyl('can_body', .043, .080, (0, 0, zt - .040), M['can'], 64, .005, r2=.038))
    P(torus('can_lip', .038, .0032, (0, 0, zt), M['canrim']))
    P(torus('can_band', .0425, .0022, (0, 0, zt - .060), M['canrim']))
    P(cyl('can_water', .035, .002, (0, 0, zt - .010), M['water'], 48, 0))
    P(torus('can_handle', .050, .0046, (0, 0, zt), M['can'], rot=(math.pi / 2, 0, 0)))
    a = Vector((.036, 0, zt - .062)); b = Vector((.158, 0, zt + .020)); d = b - a; q = d.to_track_quat('Z', 'Y').to_euler(); n = d.normalized()
    sp = cyl('can_spout', .0105, d.length, (a + b) / 2, M['can'], 32, 0, r2=.0058); sp.rotation_euler = q; P(sp)
    P(box('can_brace', (.05, .004, .004), (.065, 0, zt - .012), M['can'], .001, rot=(0, math.radians(-12), 0)))
    rs = cyl('can_rose', .0060, .024, b + n * .010, M['can'], 32, .001, r2=.024); rs.rotation_euler = q; P(rs)
    rf = cyl('can_roseface', .0235, .002, b + n * .0225, M['canrim'], 32, 0); rf.rotation_euler = q; P(rf)
    tip = empty('CAN_TIP', b + n * .024, 'PROPS'); tip.rotation_euler = q; parent(tip, root)
    return root


FONT = None


def font():
    global FONT
    if FONT is None:
        import os
        FONT = D.fonts.load(os.path.join(ROOT, 'songs/run-it/remotion/public/fonts/JBMono-500.ttf'))
    return FONT


def text(name, body, size, loc, m, rot=(math.pi / 2, 0, 0), coll='PROPS', align='LEFT'):
    cu = D.curves.new(name, 'FONT'); cu.body = body; cu.font = font(); cu.size = size; cu.align_x = align; cu.space_line = 1.25
    o = D.objects.new(name, cu); o.location = loc; o.rotation_euler = rot; bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); return col_link(o, coll)


def monitor(M, loc=(-.60, .13), yaw=27):
    """His terminal: a chunky 16:9 monitor on the bench. It is the screen the first minute of the film plays on, and the
    prompts keep landing here. The screen's local frame (left x, glass y, top z, width, height) is stored on the root."""
    root = empty('MONITOR', (loc[0], loc[1], BZ), 'PROPS'); P = lambda o: parent(col_link(o, 'PROPS'), root)
    case = mat('WB_case', (.60, .57, .50), rough=.45); bez = mat('WB_bezel', (.03, .033, .04), rough=.35)
    scr = mat('WB_screen', (.002, .004, .008), rough=.08, coat=1.0, emit=(.008, .016, .034), es=1.0)
    x, y = loc; w, h, d = .372, .250, .20; zc = BZ + .034 + h / 2
    P(box('mon_foot', (.22, .15, .034), (x, y + .02, BZ + .017), case, .008))
    P(box('mon_case', (w, d, h), (x, y, zc), case, .024))
    P(box('mon_bezel', (w - .026, .012, h - .030), (x, y - d / 2 - .001, zc), bez, .006))
    sw = w - .060; sh = sw * 9 / 16
    P(box('mon_screen', (sw, .006, sh), (x, y - d / 2 - .006, zc + .004), scr, .010))
    P(cyl('mon_led', .004, .004, (x + w / 2 - .028, y - d / 2 - .002, zc - h / 2 + .012), mat('WB_led', (.1, 1, .5), emit=(.1, 1, .45), es=6), 12, 0, rot=(math.pi / 2, 0, 0)))
    for i in range(7): P(box(f'mon_vent{i}', (.012, .09, .004), (x - .072 + i * .024, y + .02, zc + h / 2 + .0005), bez, 0))
    sl = light('mon_glow', 'AREA', (x, y - d / 2 - .05, zc), 1.6, (.55, .78, 1.0), .16); sl.rotation_euler = (-math.pi / 2, 0, 0); sl.data.volume_factor = 0; parent(sl, root)
    root['screen'] = (x - sw / 2, y - d / 2 - .0098, zc + .004 + sh / 2, sw, sh)
    # the screen furniture, in the layout of the 2D film: prompt bar along the bottom, MEMORY top right, the dot in the middle
    ink = mat('WB_ink', (.8, .9, 1), emit=(.74, .90, 1.0), es=6.0); dim = mat('WB_inkdim', (.3, .4, .5), emit=(.22, .40, .60), es=1.6)
    bar = mat('WB_bar', (.01, .014, .02), emit=(.030, .045, .075), es=1.0)
    x0, y0, zt = x - sw / 2, y - d / 2 - .0098, zc + .004 + sh / 2
    T = {}
    T['mem_l'] = text('SCR_mem_l', 'MEMORY', .0095, (x0 + sw - .074, y0, zt - .020), dim)
    T['mem'] = text('SCR_mem', '33%', .0095, (x0 + sw - .014, y0, zt - .020), ink, align='RIGHT')
    P(box('SCR_mem_bg', (.060, .0004, .0022), (x0 + sw - .044, y0 + .0002, zt - .0265), dim, 0)); mf = box('SCR_mem_fill', (.060, .0005, .0022), (x0 + sw - .044, y0, zt - .0265), ink, 0); T['mem_fill'] = mf
    T['h1'] = text('SCR_h1', '', .0105, (x0 + .016, y0, zt - .026), dim); T['h2'] = text('SCR_h2', '', .0105, (x0 + .016, y0, zt - .044), dim)
    T['l1'] = text('SCR_l1', '', .0245, (x0 + .016, y0, zt - .130), ink); T['l2'] = text('SCR_l2', '', .0245, (x0 + .016, y0, zt - .158), ink)
    T['big'] = text('SCR_big', '', .040, (x0 + sw - .016, y0, zt - .088), ink, align='RIGHT')
    T['cur'] = box('SCR_cur', (.0245 * .397 * .82, .0006, .0245 * .62), (x0 + .016, y0, zt - .124 + .0245 * .27), ink, 0, coll='PROPS')
    T['dot'] = cyl('SCR_dot', .018, .0004, (x0 + sw / 2, y0, zt - .078), M['dot'], 48, 0, rot=(math.pi / 2, 0, 0), coll='PROPS')
    for o in T.values(): parent(col_link(o, 'PROPS'), root)
    root.rotation_euler = (0, 0, math.radians(yaw))
    return root


def bench_dressing(M):
    random.seed(21)
    for i, k in enumerate(['teal', 'sky', 'butter', 'sage', 'cobalt']):          # paint pots in the city's colours
        x, y = -.70 + i * .058 + random.uniform(-.006, .006), -.26 + random.uniform(-.015, .02) + (i % 2) * .05
        cyl(f'pot{i}', .022, .030, (x, y, BZ + .019), M['white'], 32, .002, coll='PROPS'); cyl(f'potpaint{i}', .019, .002, (x, y, BZ + .0335), M['p_' + k], 32, 0, coll='PROPS')
    cyl('jar', .028, .075, (-.33, -.16, BZ + .0415), M['glass'], 32, .003, coll='PROPS')
    for i in range(5):
        a = random.uniform(0, math.tau); t = random.uniform(.08, .16)
        cyl(f'brush{i}', .003, .15, (-.33 + .012 * math.cos(a), -.16 + .012 * math.sin(a), BZ + .085), M['p_cream'] if i % 2 else M['black'], 12, 0, rot=(t * math.cos(a), t * math.sin(a), 0), coll='PROPS')
        cyl(f'bristle{i}', .004, .016, (-.33 + .02 * math.cos(a), -.16 + .02 * math.sin(a), BZ + .165), M['p_' + ['teal', 'sky', 'char', 'sage', 'cobalt'][i]], 12, .001, coll='PROPS')
    box('rule', (.30, .028, .0015), (.50, -.27, BZ + .005), M['steel'], .0004, rot=(0, 0, math.radians(8)), coll='PROPS')
    for i in range(7):
        k = random.choice(['teal', 'sky', 'cream', 'sage', 'butter', 'cobalt']); s = (random.uniform(.024, .034), random.uniform(.024, .03), random.uniform(.02, .06))
        box(f'spare{i}', s, (.50 + random.uniform(-.09, .14), -.12 + random.uniform(-.07, .09), BZ + .004 + s[2] / 2), M['p_' + k], .0012, rot=(0, 0, random.uniform(0, 1.5)), coll='PROPS')
    for i in range(7, 24):
        k = random.choice(['teal', 'sky', 'cream', 'sage', 'butter', 'cobalt', 'mint']); sz = (random.uniform(.018, .03), random.uniform(.018, .028), random.uniform(.014, .04))
        x = random.choice([random.uniform(-.80, -.42), random.uniform(.36, .80)]); y = random.uniform(-.34, -.14)
        box(f'spare{i}', sz, (x, y, BZ + .004 + sz[2] / 2), M['p_' + k], .0012, rot=(0, 0, random.uniform(0, 1.5)), coll='PROPS')
    cyl('pencil', .0035, .16, (-.42, -.30, BZ + .0075), M['p_char'], 6, 0, rot=(0, math.pi / 2, math.radians(20)), coll='PROPS')


# ---------------------------------------------------------------- lights, air, cameras
def lights():
    def L(*a, vol=0.0, **k): o = light(*a, **k); o.data.volume_factor = vol; return o
    L('RIM', 'AREA', (-1.05, 1.32, 1.75), 130, (.40, .60, 1.0), .6, aim=(0, CLAUDE_Y, .9))
    L('RIM2', 'AREA', (1.0, 1.32, 1.55), 70, (.45, .62, 1.0), .5, aim=(0, CLAUDE_Y, .85))
    L('MOON', 'AREA', (-.2, 1.25, 2.15), 55, (.36, .56, 1.0), 1.2, aim=(0, -.05, .4), vol=.15)
    L('FILL', 'AREA', (.3, -1.9, 1.0), 3.0, (.70, .80, 1.0), 2.0, aim=(0, .2, .7))
    L('CLAUDE_KEY', 'SPOT', (.50, -.14, 1.02), 21, (1.0, .84, .68), .22, aim=(0, CLAUDE_Y - .10, .97), spot=70, blend=.9, vol=.15)
    L('HAIR', 'SPOT', (.15, .95, 2.0), 30, (1.0, .86, .70), .15, aim=(0, CLAUDE_Y, 1.12), spot=40, blend=.9)
    L('WALLWASH', 'AREA', (0, .9, .25), 7, (.30, .50, .95), 1.5, aim=(0, WALL_Y, .5))
    b = L('BOUNCE', 'AREA', (C.x, C.y - .02, ISLE_Z + .03), 1.75, (1.0, .84, .66), .42, aim=(C.x, C.y + .12, 1.0)); b.data.use_shadow = False; b.data.specular_factor = .2


def air(density=.014):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, .2, 1.3)); o = bpy.context.active_object; o.name = 'AIR'; o.scale = (5, 4, 2.8)
    m = D.materials.new('WB_air'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes.get('Principled BSDF'))
    v = nt.nodes.new('ShaderNodeVolumePrincipled'); v.inputs['Density'].default_value = density; v.inputs['Anisotropy'].default_value = .5; v.inputs['Color'].default_value = (.8, .86, 1, 1)
    nt.links.new(v.outputs[0], nt.nodes.get('Material Output').inputs['Volume']); o.data.materials.append(m); o.display_type = 'WIRE'; col_link(o, 'LIGHTS'); return o


def camera(name, loc, aim, lens=35, fstop=2.8, focus=None):
    cd = D.cameras.new(name); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = .01; cd.clip_end = 60
    o = D.objects.new(name, cd); o.location = loc; bpy.context.scene.collection.objects.link(o); col_link(o, 'CAMS'); look_at(o, aim)
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop; cd.dof.focus_distance = (Vector(focus if focus is not None else aim) - Vector(loc)).length
    return o


def build(with_air=True):
    M = mats(); room(M); bench(M); root = table(M); blocks = city(M, root); lamp(M); can = watering_can(M); bench_dressing(M); mon = monitor(M); lights()
    if with_air: air()
    return dict(M=M, table=root, blocks=blocks, can=can, monitor=mon)


def compositor(bloom=.15, thresh=3.6, vignette=.38, dispersion=.008):
    """Bloom on the practicals, a breath of lens dispersion, a soft vignette."""
    sc = bpy.context.scene; ng = D.node_groups.new('WB_comp', 'CompositorNodeTree'); ng.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    N = ng.nodes; Lk = ng.links.new; rl = N.new('CompositorNodeRLayers'); out = N.new('NodeGroupOutput')
    gl = N.new('CompositorNodeGlare'); gl.inputs['Type'].default_value = 'Bloom'; gl.inputs['Threshold'].default_value = thresh; gl.inputs['Strength'].default_value = bloom; gl.inputs['Size'].default_value = .55
    try: gl.inputs['Quality'].default_value = 'High'
    except Exception as e: print('glare quality', e)
    Lk(rl.outputs['Image'], gl.inputs['Image']); last = gl.outputs['Image']
    if dispersion:
        ld = N.new('CompositorNodeLensdist'); ld.inputs['Dispersion'].default_value = dispersion; Lk(last, ld.inputs['Image']); last = ld.outputs['Image']
    if vignette:
        em = N.new('CompositorNodeEllipseMask'); em.inputs['Size'].default_value = (.86, .80)
        bl = N.new('CompositorNodeBlur'); bl.inputs['Size'].default_value = (420, 420); Lk(em.outputs['Mask'], bl.inputs['Image'])
        mp = N.new('ShaderNodeMath'); mp.operation = 'MULTIPLY_ADD'; mp.inputs[1].default_value = vignette; mp.inputs[2].default_value = 1 - vignette
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        try:
            Lk(bl.outputs['Image'], mp.inputs[0]); Lk(last, mx.inputs['A']); Lk(mp.outputs[0], mx.inputs['B']); last = mx.outputs[2]
        except Exception as e: print('vignette', e)
    Lk(last, out.inputs[0]); sc.compositing_node_group = ng
    try: sc.render.use_compositing = True
    except Exception: pass
    return ng
