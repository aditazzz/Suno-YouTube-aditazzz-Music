"""Run It: the small things on the bench that he works with. Each returns its root object.
Tools are modelled along -Z from their origin, so they line up with his fingers (the hand's rest direction)."""
import bpy, math, random
from mathutils import Vector, Matrix, Euler
from wb import *
import wbset
BZ = wbset.BZ; IZ = wbset.ISLE_Z; C = wbset.C


def _root(name, loc=(0, 0, 0), coll='PROPS'):
    return empty(name, loc, coll)


def _P(root, coll='PROPS'):
    return lambda o: parent(col_link(o, coll), root)


def tweezers(M, L=.21):
    r = _root('TWEEZERS'); P = _P(r)
    for s in (-1, 1):
        b = box(f'tw_blade{s}', (.0014, .0050, L), (s * .0045, 0, -L / 2), M['steel'], .0005, rot=(0, s * math.radians(1.25), 0)); P(b)
    P(box('tw_back', (.011, .0052, .012), (0, 0, -.004), M['steel'], .001))
    r['len'] = L
    return r


def brush(M, L=.11):
    r = _root('BRUSH'); P = _P(r)
    P(cyl('br_handle', .0019, L - .018, (0, 0, -(L - .018) / 2), M['p_cream'], 16, .0004))
    P(cyl('br_ferrule', .0020, .010, (0, 0, -(L - .018) - .005), M['steel'], 16, 0))
    P(cyl('br_tip', .0019, .009, (0, 0, -(L - .008) - .0045), mat('WB_yellow', (1.0, .72, .0), rough=.35), 16, 0, r2=.0002))
    r['len'] = L + .001
    return r


def traffic_light(M, name):
    """Origin at the foot. Lamps face -Y. The three lamps are separate so they can be lit one by one."""
    r = _root(name); P = _P(r)
    P(cyl(name + '_base', .0045, .0016, (0, 0, .0008), M['black'], 16, 0)); P(cyl(name + '_post', .0010, .030, (0, 0, .016), M['black'], 8, 0))
    P(box(name + '_head', (.0075, .0055, .0195), (0, 0, .0385), M['p_char'], .0012))
    lamps = []
    for i, (cname, col) in enumerate((('g', (.05, 1.0, .35)), ('y', (1.0, .80, .05)), ('r', (1.0, .06, .04)))):
        m = D.materials.new(f'{name}_{cname}'); m.use_nodes = True; b = m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (*[c * .12 for c in col], 1)
        b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = 0.0
        o = sph(f'{name}_{cname}', .0024, (0, -.0026, .0325 + i * .006), m, seg=12); P(o); lamps.append(m)
    r['h'] = .048
    return r


def set_lamp(tl_name, which, on, f):
    """which in 'g','y','r'. Keys the lamp's glow at frame f (constant interpolation set by the caller's shot)."""
    m = D.materials[f'{tl_name}_{which}']; i = m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength']; i.default_value = 9.0 if on else 0.0; i.keyframe_insert('default_value', frame=f)


def crown(M):
    """The last piece of the city: the top of the tallest tower. Origin at its base."""
    r = _root('CROWN'); P = _P(r)
    o = box('crown_a', (.020, .020, .024), (0, 0, .012), M['b_cream'], .001); o['lit'] = 1.0; P(o)
    o = box('crown_b', (.012, .012, .012), (0, 0, .030), M['b_cream'], .0008); o['lit'] = 1.0; P(o)
    P(cyl('crown_candle', .0026, .030, (0, 0, .051), M['white'], 12, .0006)); P(cyl('crown_wick', .0004, .004, (0, 0, .068), M['p_char'], 6, 0))
    r['h'] = .070
    return r


def hero_building(M, loc):
    """The open-fronted block at the mouth of the boulevard: 4 x 4 little offices, each with a desk and a screen.
    Returns root; root['cells'] = flat list of (x, y, z) floor centres in world space, row 0 = bottom."""
    bx, by = loc; cw, ch, d, t = .0130, .0142, .024, .0012; nx, nz = 4, 4; w = nx * cw + t; base = .005; h = base + nz * ch + t
    r = _root('HEROB', (bx, by, IZ)); P = _P(r); wall = M['p_sky']; inner = mat('WB_office', (.55, .50, .42), rough=.8, emit=(1.0, .80, .52), es=1.6)
    P(box('hb_base', (w + .004, d + .004, base), (bx, by, IZ + base / 2), M['p_char'], .0008))
    P(box('hb_back', (w, t, h - base), (bx, by + d / 2 - t / 2, IZ + base + (h - base) / 2), inner, 0))
    for i in range(nx + 1): P(box(f'hb_v{i}', (t, d, h - base), (bx - w / 2 + t / 2 + i * cw, by, IZ + base + (h - base) / 2), wall, 0))
    for j in range(nz + 1): P(box(f'hb_f{j}', (w, d, t), (bx, by, IZ + base + j * ch + t / 2), wall, 0))
    P(box('hb_roof', (w + .003, d + .003, .0022), (bx, by, IZ + h + .0011), M['p_char'], .0006)); P(cyl('hb_tank', .004, .006, (bx + .012, by + .003, IZ + h + .005), M['p_cream'], 16, .0006))
    scr = mat('WB_tinyscreen', (.5, .7, 1), emit=(.55, .78, 1.0), es=5.0); cells = []
    # a doll's-house block: every floor has its own wallpaper, every office its own lamp, picture, plant or shelf
    papers = [mat(f'WB_paper{k}', c, rough=.85, emit=c, es=.55) for k, c in enumerate(((.86, .62, .36), (.42, .66, .60), (.88, .50, .44), (.44, .56, .80)))]
    scrs = [scr, mat('WB_tinyscreen1', (.5, 1, .8), emit=(.45, 1.0, .72), es=5.0), mat('WB_tinyscreen2', (1, .8, .5), emit=(1.0, .74, .36), es=5.0)]
    bulbm = mat('WB_tinybulb', (1, .8, .5), emit=(1.0, .78, .46), es=8.0); dark = mat('WB_tinydark', (.05, .055, .07), rough=.5); leaf = mat('WB_leaf', (.08, .40, .20), rough=.7)
    arts = [mat(f'WB_art{k}', c, rough=.6, emit=c, es=.4) for k, c in enumerate(((.95, .82, .30), (.20, .62, .70), (.92, .40, .30), (.96, .94, .88)))]
    rnd = random.Random(7)
    for j in range(nz):
        for i in range(nx):
            cx = bx - w / 2 + t + (i + .5) * cw - t / 2; cz = IZ + base + j * ch + t; yb = by + d / 2 - t
            P(box(f'hb_paper{i}{j}', (cw - t, .0003, ch - t), (cx, yb - .0002, cz + (ch - t) / 2), papers[(j + (i // 2)) % 4], 0))
            P(box(f'hb_skirt{i}{j}', (cw - t, .0005, .0012), (cx, yb - .0004, cz + .0006), M['p_cream'], 0))
            P(box(f'hb_desk{i}{j}', (.0042, .0050, .0036), (cx + .0030, by - .002, cz + .0018), M['p_cream'], .0003))
            P(box(f'hb_scr{i}{j}', (.0004, .0034, .0026), (cx + .0046, by - .002, cz + .0052), scrs[rnd.randrange(3)], 0))
            P(box(f'hb_scrb{i}{j}', (.0003, .0036, .0028), (cx + .0050, by - .002, cz + .0052), dark, 0))
            P(box(f'hb_kb{i}{j}', (.0018, .0032, .0003), (cx + .0020, by - .002, cz + .00375), dark, 0))
            P(box(f'hb_chair{i}{j}', (.0005, .0036, .0052), (cx - .0050, by - .002, cz + .0026), dark, .0002))
            P(cyl(f'hb_cord{i}{j}', .00012, .0030, (cx - .0008, by + .004, cz + ch - t - .0015), dark, 6, 0)); P(sph(f'hb_bulb{i}{j}', .0008, (cx - .0008, by + .004, cz + ch - t - .0034), bulbm, seg=10))
            k = rnd.randrange(4)
            if k in (0, 1): P(box(f'hb_art{i}{j}', (.0034, .0003, .0026) if k == 0 else (.0022, .0003, .0032), (cx - .0026 + rnd.uniform(-.001, .001), yb - .0006, cz + .0088), arts[rnd.randrange(4)], 0))
            if k == 2:
                P(box(f'hb_shelf{i}{j}', (.0050, .0016, .0003), (cx - .0026, yb - .0010, cz + .0080), M['p_cream'], 0))
                for b in range(4): P(box(f'hb_book{i}{j}{b}', (.0007, .0012, rnd.uniform(.0016, .0024)), (cx - .0042 + b * .0009, yb - .0010, cz + .0092), arts[rnd.randrange(4)], 0))
            if k == 3:
                P(box(f'hb_shelf{i}{j}', (.0034, .0018, .0003), (cx - .0030, yb - .0011, cz + .0078), M['p_cream'], 0))
                P(cyl(f'hb_pot{i}{j}', .0007, .0011, (cx - .0030, yb - .0011, cz + .0085), M['white'], 10, 0)); P(sph(f'hb_leaf{i}{j}', .0013, (cx - .0030, yb - .0011, cz + .0100), leaf, seg=10))
            cells.append((cx - .0026, by - .002, cz))
    fl = light('herob_face', 'AREA', (bx - .01, by - .10, IZ + h * .6), .05, (1.0, .86, .68), .08); fl.rotation_euler = (math.pi / 2, 0, 0); fl.data.volume_factor = 0; fl.data.use_shadow = False; parent(fl, r)
    r['cells'] = [c for cell in cells for c in cell]; r['h'] = h
    return r


def guy(M, name, col):
    """A peg person in profile at his desk, facing +X, two arms out to the keyboard. Origin at his feet."""
    r = _root(name); P = _P(r)
    P(cyl(name + '_body', .0019, .0046, (0, 0, .0023), M['p_' + col], 16, .0005)); P(sph(name + '_head', .0019, (0, 0, .0064), M['p_cream'], seg=12))
    arms = []
    for k, y in enumerate((-.0012, .0012)):
        a = cyl(f'{name}_arm{k}', .00045, .0034, (.0024, y, .0036), M['p_' + col], 8, 0, rot=(0, math.radians(78), 0)); P(a); arms.append(a)
    return r


def coffee(M):
    r = _root('COFFEE'); P = _P(r)
    P(cyl('cof_cup', .0011, .0020, (0, 0, .0010), M['white'], 12, .0002)); P(cyl('cof_top', .0009, .0002, (0, 0, .0020), mat('WB_coffee', (.05, .025, .012), rough=.2), 12, 0))
    return r


def mobile(M, n=5, thread=.095, rod=.25):
    """Paper pigeons on threads from a hub at the tip of a rod he holds like a fishing pole. MOBILE = the rod (along -Z from his
    fist). MOB_HUB is its own object (keyed to the rod's tip each frame) so the threads always hang straight down; it spins
    about Z and each MOB_ARM_i swings outward (rotation_euler.y) as it speeds up."""
    r = _root('MOBILE'); P = _P(r); paper = mat('WB_paper', (.86, .85, .80), rough=.7); thr = mat('WB_thread', (.5, .5, .5), rough=.6)
    P(cyl('mob_rod', .0020, rod + .03, (0, 0, -(rod + .03) / 2 + .03), M['p_cream'], 12, .0005, r2=.0012))
    hub = empty('MOB_HUB', (0, 0, 0), 'PROPS'); hb = sph('mob_hubball', .004, (0, 0, 0), M['steel'], coll='PROPS', seg=12); parent(hb, hub)
    for i in range(n):
        a = i * math.tau / n; arm = empty(f'MOB_ARM{i}', (0, 0, 0), 'PROPS'); parent(arm, hub)                       # rotation_euler = (0, swing, a)
        t = cyl(f'mob_thread{i}', .0004, thread, (0, 0, -thread / 2), thr, 6, 0); col_link(t, 'PROPS'); parent(t, arm)
        b = empty(f'MOB_BIRD{i}', (0, 0, -thread), 'PROPS'); parent(b, arm)
        body = sph(f'bird{i}_body', .0085, (0, 0, -thread), paper, coll='PROPS', seg=12); body.scale = (.55, 1.5, .5); parent(body, b)
        hd = sph(f'bird{i}_head', .0042, (0, -.011, -thread + .003), paper, coll='PROPS', seg=10); parent(hd, b)
        bk = cyl(f'bird{i}_beak', .0012, .005, (0, -.0165, -thread + .003), M['p_char'], 8, 0, rot=(math.pi / 2, 0, 0), r2=.0001, coll='PROPS'); parent(bk, b)
        for k, sg in enumerate((-1, 1)):
            me = D.meshes.new(f'bird{i}_wing{k}'); me.from_pydata([(0, -.008, 0), (0, .007, 0), (sg * .024, .001, 0)], [], [(0, 1, 2)]); me.update()
            wg = D.objects.new(f'bird{i}_wing{k}', me); wg.location = (0, 0, -thread + .0016); bpy.context.scene.collection.objects.link(wg); finish(wg, paper, 0, smooth=False, coll='PROPS'); parent(wg, b)
            so = wg.modifiers.new('sol', 'SOLIDIFY'); so.thickness = .0004
        arm.rotation_euler = (0, .25, a); arm['az'] = a
    hub.location = (0, 0, -3)
    r['n'] = n; r['rod'] = rod; r['thread'] = thread
    return r


def gravity_switch(M, loc):
    """A chunky toggle on the bench, labelled. GS_LEVER.rotation_euler.x: -0.5 = ON (leaning away from us), +0.5 = OFF."""
    x, y = loc; r = _root('GSWITCH', (x, y, BZ)); P = _P(r); case = mat('WB_case2', (.62, .58, .50), rough=.45); ink = mat('WB_label', (.02, .022, .03), rough=.6)
    P(box('gs_box', (.096, .074, .030), (x, y, BZ + .015), case, .005)); P(box('gs_plate', (.030, .052, .002), (x + .024, y, BZ + .031), M['steel'], .001))
    lev = empty('GS_LEVER', (x + .024, y, BZ + .032), 'PROPS'); parent(lev, r)
    for o in (cyl('gs_stem', .0042, .032, (x + .024, y, BZ + .048), M['steel'], 16, .001), sph('gs_ball', .0072, (x + .024, y, BZ + .066), M['black'], seg=16)): col_link(o, 'PROPS'); parent(o, lev)
    lev.rotation_euler = (-.5, 0, 0)
    for nm, body, size, lx, ly in (('gs_t', 'GRAVITY', .0125, x - .043, y - .006), ('gs_on', 'ON', .0075, x + .0165, y + .0285), ('gs_off', 'OFF', .0075, x + .0150, y - .034)):
        P(wbset.text(nm, body, size, (lx, ly, BZ + .0303), ink, rot=(0, 0, 0)))
    led = D.materials.new('GS_led'); led.use_nodes = True; b = led.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (.02, .12, .05, 1); b.inputs['Emission Color'].default_value = (.1, 1, .45, 1); b.inputs['Emission Strength'].default_value = 7.0
    P(sph('gs_led', .0035, (x - .034, y + .022, BZ + .031), led, seg=12))
    return r


def tape(M):
    """A strip of blue tape over the car's roof and down to the road. Origin on the road under the car's middle; runs along X."""
    r = _root('TAPE'); P = _P(r); blue = mat('WB_tape', (.06, .22, .70), rough=.55); w = .0075; t = .0004; top = .0190; hw = .0128; out = .0235
    P(box('tape_top', (hw * 2, w, t), (0, 0, top), blue, 0))
    for sg in (-1, 1):
        a = Vector((sg * hw, 0, top)); b = Vector((sg * out, 0, .0006)); d = b - a
        o = box(f'tape_side{sg}', (d.length, w, t), (a + b) / 2, blue, 0, rot=(0, -math.atan2(d.z, d.x), 0)); P(o)
        P(box(f'tape_tab{sg}', (.009, w, t), (sg * (out + .0045), 0, .0005), blue, 0))
    return r


def water_blobs(M, n=12, seed=4):
    random.seed(seed); out = []
    for i in range(n):
        a = random.uniform(0, math.tau); rr = random.uniform(wbset.R_ISLE + .025, wbset.R_WATER - .02)
        o = sph(f'blob{i}', random.uniform(.006, .013), (C.x + rr * math.cos(a), C.y + rr * math.sin(a), wbset.WATER_Z), M['water'], coll='FX', seg=20); o.scale = (0, 0, 0); out.append(o)
    return out


def attr_emit_mat(name, col, strength, twinkle=False):
    """emission scaled by the object's 'lit' property; twinkle multiplies in a slow per-object shimmer driven by the frame number."""
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (*[c * .25 for c in col], 1); b.inputs['Emission Color'].default_value = (*col, 1)
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'lit'
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = strength; nt.links.new(at.outputs['Fac'], mul.inputs[0]); last = mul.outputs[0]
    if twinkle:
        tv = nt.nodes.new('ShaderNodeValue'); tv.name = 'TIME'; fc = tv.outputs[0].driver_add('default_value'); fc.driver.expression = 'min(frame, 4543) / 30'
        oi = nt.nodes.new('ShaderNodeObjectInfo'); sp = nt.nodes.new('ShaderNodeMath'); sp.operation = 'MULTIPLY_ADD'; sp.inputs[1].default_value = 2.6; sp.inputs[2].default_value = 1.6; nt.links.new(oi.outputs['Random'], sp.inputs[0])
        ph = nt.nodes.new('ShaderNodeMath'); ph.operation = 'MULTIPLY'; ph.inputs[1].default_value = 40.0; nt.links.new(oi.outputs['Random'], ph.inputs[0])
        ang = nt.nodes.new('ShaderNodeMath'); ang.operation = 'MULTIPLY_ADD'; nt.links.new(tv.outputs[0], ang.inputs[0]); nt.links.new(sp.outputs[0], ang.inputs[1]); nt.links.new(ph.outputs[0], ang.inputs[2])
        sn = nt.nodes.new('ShaderNodeMath'); sn.operation = 'SINE'; nt.links.new(ang.outputs[0], sn.inputs[0])
        tw = nt.nodes.new('ShaderNodeMath'); tw.operation = 'MULTIPLY_ADD'; tw.inputs[1].default_value = .42; tw.inputs[2].default_value = .58; nt.links.new(sn.outputs[0], tw.inputs[0])
        m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; nt.links.new(last, m2.inputs[0]); nt.links.new(tw.outputs[0], m2.inputs[1]); last = m2.outputs[0]
    nt.links.new(last, b.inputs['Emission Strength'])
    return m


def fairy_strand(M, blocks, n=84, seed=3):
    """a string of tiny bulbs laid through the streets and wound up the tall towers. Returns the bulbs in order along the strand
    (from his side of the island to the camera's)."""
    random.seed(seed); cols = [attr_emit_mat('WB_fl_warm', (1.0, .80, .48), 17), attr_emit_mat('WB_fl_teal', (.15, .95, .80), 15), attr_emit_mat('WB_fl_blue', (.30, .55, 1.0), 17), attr_emit_mat('WB_fl_white', (.9, .95, 1.0), 15)]
    pts = []
    # along the streets: an S through the grid, back to front
    for k, y in enumerate((.111, .0, -.111)):
        xs = [(-.17 + .34 * i / 13) for i in range(14)]
        if k % 2: xs = xs[::-1]
        for x in xs:
            if math.hypot(x, y) < wbset.R_ISLE - .02 and not (abs(x) < .05 and abs(y) < .05): pts.append((C.x + x + random.uniform(-.004, .004), C.y + y + random.uniform(-.006, .006), IZ + .004 + random.uniform(0, .002)))
    # round the roofs of the tallest blocks
    tall = sorted(blocks, key=lambda b: -b[3])[:7]
    for o, bx, by, bh in tall:
        for j in range(5):
            a = j * math.tau / 5 + random.uniform(0, 1); pts.append((bx + .019 * math.cos(a), by + .019 * math.sin(a), IZ + bh * random.uniform(.55, .98)))
    pts.sort(key=lambda p: -p[1]); out = []
    for i, p in enumerate(pts[:n]):
        o = sph(f'fl{i:03d}', .0022, p, cols[i % 4], coll='PROPS', seg=8); o['lit'] = 0.0; out.append(o)
    return out


def glints(M, blocks, n=130, seed=6):
    """glitter that has settled on the roofs and streets: tiny mirrors that shimmer slowly."""
    random.seed(seed); m = attr_emit_mat('WB_glint', (.92, .97, 1.0), 28, twinkle=True); out = []
    for i in range(n):
        if random.random() < .7:
            o, bx, by, bh = random.choice(blocks); p = (bx + random.uniform(-.012, .012), by + random.uniform(-.012, .012), IZ + bh + .0008)
        else:
            a = random.uniform(0, math.tau); r = random.uniform(.02, wbset.R_ISLE - .01); p = (C.x + r * math.cos(a), C.y + r * math.sin(a), IZ + .0022)
        g = sph(f'glint{i:03d}', random.uniform(.0007, .0013), p, m, coll='PROPS', seg=6); g['lit'] = 0.0; out.append(g)
    return out


def flame(name, r=.0034, power=.07):
    m = D.materials.get('WB_flame') or mat('WB_flame', (1, .8, .3), emit=(1.0, .70, .22), es=18.0)
    f = sph(name, r, (0, 0, 0), m, coll='PROPS', seg=12); f.scale = (1, 1, 2.0)
    l = light(name + '_l', 'POINT', (0, 0, r), power, (1.0, .72, .35), .004); l.data.volume_factor = 0; col_link(l, 'PROPS'); parent(l, f)
    return f


def match(M):
    """a long match, along -Z from his fingers; the head is at the far end."""
    r = _root('MATCH'); P = _P(r); L = .11
    P(cyl('match_stick', .0011, L, (0, 0, -L / 2), M['p_cream'], 8, 0)); P(sph('match_head', .0020, (0, 0, -L), M['p_char'], seg=10))
    r['len'] = L
    return r


def metronome(M, loc):
    """MET_ARM.rotation_euler.y swings."""
    x, y = loc; r = _root('METRONOME', (x, y, BZ)); P = _P(r)
    P(cyl('met_body', .030, .085, (x, y, BZ + .0425), M['p_char'], 4, .003, r2=.012, rot=(0, 0, math.radians(45))))
    P(box('met_face', (.020, .002, .060), (x, y - .0155, BZ + .042), M['p_cream'], .0008, rot=(math.radians(-12), 0, 0)))
    arm = empty('MET_ARM', (x, y - .020, BZ + .016), 'PROPS'); parent(arm, r)
    for o in (cyl('met_rod', .0011, .085, (x, y - .020, BZ + .058), M['steel'], 8, 0), box('met_weight', (.012, .006, .010), (x, y - .020, BZ + .078), M['steel'], .001)): col_link(o, 'PROPS'); parent(o, arm)
    return r


def speaker(M, loc, yaw=-28):
    """SPK_CONE.scale.y pumps (cone faces local -Y before the yaw). SPK_KNOB turns about Z."""
    x, y = loc; r = _root('SPEAKER', (x, y, BZ)); P = _P(r); w, d, h = .15, .13, .21; grille = mat('WB_grille', (.50, .47, .40), rough=.7); conem = mat('WB_cone', (.02, .022, .028), rough=.5)
    P(box('spk_box', (w, d, h), (x, y, BZ + h / 2), M['p_cream'], .008)); P(box('spk_face', (w - .016, .004, h - .016), (x, y - d / 2 - .0005, BZ + h / 2), M['p_teal'], .004))
    P(cyl('spk_ring', .058, .006, (x, y - d / 2 - .001, BZ + .115), grille, 48, .002, rot=(math.pi / 2, 0, 0)))
    cone = cyl('SPK_CONE', .050, .010, (x, y - d / 2 - .003, BZ + .115), conem, 48, .002, rot=(math.pi / 2, 0, 0), coll='PROPS'); parent(cone, r)
    cap = sph('spk_cap', .016, (x, y - d / 2 - .006, BZ + .115), M['steel'], coll='PROPS', seg=16); cap.scale = (1, .5, 1); parent(cap, cone)
    P(cyl('spk_tweet', .014, .005, (x - .040, y - d / 2 - .001, BZ + .185), conem, 24, .001, rot=(math.pi / 2, 0, 0)))
    knob = cyl('SPK_KNOB', .013, .012, (x - .040, y + .028, BZ + h + .006), M['p_char'], 24, .002, coll='PROPS'); parent(knob, r)
    P2 = box('spk_knobmark', (.002, .010, .002), (x - .040, y + .022, BZ + h + .0125), M['p_cream'], 0, coll='PROPS'); parent(P2, knob)
    led = D.materials.new('SPK_led'); led.use_nodes = True; b = led.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (.02, .05, .12, 1); b.inputs['Emission Color'].default_value = (.3, .7, 1.0, 1); b.inputs['Emission Strength'].default_value = 0.0
    P(sph('spk_led', .0035, (x + .056, y - d / 2 - .001, BZ + .190), led, seg=10))
    sl = light('SPK_LIGHT', 'AREA', (x - .12, y - .34, BZ + .42), 7.0, (1.0, .86, .68), .25, aim=(x, y, BZ + .12)); sl.data.volume_factor = 0; sl.data.use_shadow = False
    r.rotation_euler = (0, 0, math.radians(yaw)); r['top'] = BZ + h
    return r


def run_button(M, loc):
    """the one red button. RUN_CAP.location.z drops when pressed."""
    x, y = loc; r = _root('RUNBTN', (x, y, BZ)); P = _P(r); red = mat('WB_red', (.75, .02, .02), rough=.25, coat=1.0, emit=(1.0, .02, .02), es=.6); ink = mat('WB_label', (.02, .022, .03), rough=.6)
    P(box('run_box', (.074, .074, .026), (x, y, BZ + .013), mat('WB_case2', (.62, .58, .50), rough=.45), .005)); P(cyl('run_collar', .025, .006, (x, y + .006, BZ + .029), M['steel'], 32, .001))
    cap = cyl('RUN_CAP', .021, .014, (x, y + .006, BZ + .037), red, 32, .004, coll='PROPS'); parent(cap, r)
    P(wbset.text('run_t', 'RUN', .0105, (x - .014, y - .033, BZ + .0263), ink, rot=(0, 0, 0)))
    return r


def moon(M, name, loc, string=1.4):
    """a paper-lantern moon on a long thread. <name>_PIV at the top of the thread swings it (rotation_euler.y); the googly eye is
    <name>_EYE (scale 0 until he sticks it on) with pupil <name>_PUP."""
    x, y, z = loc; piv = empty(name + '_PIV', (x, y, z + string), 'PROPS'); P = lambda o: parent(col_link(o, 'PROPS'), piv)
    m = D.materials.new(name + '_mat'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (.85, .82, .72, 1); b.inputs['Roughness'].default_value = .9
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 4; rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = .35; rp.color_ramp.elements[0].color = (.55, .52, .44, 1); rp.color_ramp.elements[1].position = .7; rp.color_ramp.elements[1].color = (1, .96, .84, 1)
    nt.links.new(nz.outputs[0], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 2.6
    P(sph(name, .046, (x, y, z), m, seg=32)); P(cyl(name + '_thread', .0005, string - .046, (x, y, z + .046 + (string - .046) / 2), mat('WB_thread2', (.6, .6, .6), rough=.6), 6, 0))
    l = light(name + '_glow', 'POINT', (x, y - .02, z), .9, (1.0, .92, .76), .05); l.data.volume_factor = 0; parent(l, piv)
    eye = empty(name + '_EYE', (x, y - .0445, z + .006), 'PROPS'); parent(eye, piv)
    for o in (cyl(name + '_eyew', .0155, .003, (x, y - .0450, z + .006), M['white'], 32, .0008, rot=(math.pi / 2, 0, 0)),): col_link(o, 'PROPS'); parent(o, eye)
    pup = cyl(name + '_PUP', .0075, .002, (x, y - .0472, z + .002), M['black'], 24, 0, rot=(math.pi / 2, 0, 0)); col_link(pup, 'PROPS'); parent(pup, eye)
    eye.scale = (0, 0, 0)
    return piv


def plug(M, ang):
    """bath plug on a bead chain at the back of the ocean (table-local angle ang). PLUG.location.z lifts."""
    r_ = wbset.R_WATER - .035; x, y = C.x + r_ * math.cos(ang), C.y + r_ * math.sin(ang); root = _root('PLUG', (x, y, wbset.WATER_Z)); P = _P(root)
    P(cyl('plug_disc', .011, .004, (x, y, wbset.WATER_Z + .001), M['black'], 24, .001)); P(torus('plug_ring', .005, .0012, (x, y, wbset.WATER_Z + .008), M['steel'], rot=(math.pi / 2, 0, ang)))
    for i in range(7): P(sph(f'plug_bead{i}', .0016, (x + .006 * (i + 1) * math.cos(ang), y + .006 * (i + 1) * math.sin(ang), wbset.WATER_Z + .006 - .0007 * i), M['steel'], seg=8))
    return root


def wave_rings(M, n=4):
    out = []; m = mat('WB_ring', (.8, .95, 1.0), rough=.1, emit=(.5, .85, 1.0), es=1.2)
    for i in range(n):
        o = torus(f'wring{i}', .05, .0012, (C.x, C.y, wbset.WATER_Z + .0008), m, coll='FX'); o.scale = (0, 0, 0); out.append(o)
    return out


def planner(M):
    """A week on a clipboard. Origin = middle of the bottom edge, face toward -Y. PL_MON is the Monday column (a strip with its
    notes), PL_MID is Tuesday to Saturday as one sheet; Sunday stays."""
    r = _root('PLANNER'); P = _P(r); W, H = .34, .235; ink = mat('WB_label', (.02, .022, .03), rough=.6); paper = mat('WB_paper2', (.88, .86, .80), rough=.8)
    P(box('pl_board', (W, .006, H), (0, 0, H / 2), M['leg'], .003)); P(box('pl_clip', (.07, .012, .022), (0, -.004, H - .006), M['steel'], .003))
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']; cw = (W - .024) / 7; x0 = -W / 2 + .012; stick = [M['p_butter'], M['p_mint'], M['p_sky'], M['p_cream']]
    meetings = ['standup', 'sync', 're-sync', 'pre-read', 'all hands', '1:1', 'retro', 'planning']
    notes = {'MON': meetings, 'TUE': ['focus'], 'WED': ['ship it', 'lunch'], 'THU': ['demo'], 'FRI': ['write'], 'SAT': [], 'SUN': ['nothing']}
    random.seed(2); groups = {}
    for i, dname in enumerate(days):
        g = empty('PL_' + dname, (x0 + (i + .5) * cw, -.0036, H / 2), 'PROPS'); parent(g, r); groups[dname] = g
        col = box(f'pl_col{i}', (cw - .004, .0006, H - .034), (x0 + (i + .5) * cw, -.0036, H / 2 - .010), paper, 0, coll='PROPS'); parent(col, g)
        t = wbset.text(f'pl_h{i}', dname, .0120, (x0 + (i + .5) * cw, -.0042, H - .040), ink, align='CENTER'); parent(t, g)
        ns = notes[dname]; nh = (H - .062) / 8.2
        for j, nm in enumerate(ns):
            zc = H - .052 - (j + .5) * nh * (1.0 if len(ns) > 3 else 1.6); xo = random.uniform(-.002, .002)
            nb = box(f'pl_n{i}_{j}', (cw - .008, .0005, nh * .88), (x0 + (i + .5) * cw + xo, -.0044, zc), stick[(i + j) % 4], 0, rot=(0, random.uniform(-.05, .05), 0), coll='PROPS'); parent(nb, g)
            tt = wbset.text(f'pl_t{i}_{j}', nm, .0080, (x0 + (i + .5) * cw + xo, -.0049, zc - .003), ink, align='CENTER'); parent(tt, g)
    mid = empty('PL_MID', (0, -.0036, H / 2), 'PROPS'); parent(mid, r)
    bpy.context.view_layer.update()
    for dname in days[1:6]: g = groups[dname]; g.parent = mid; g.matrix_parent_inverse = mid.matrix_world.inverted()
    r['W'] = W; r['H'] = H
    return r


def cord_switch(M, loc):
    x, y = loc; r = _root('CORDSW', (x, y, BZ)); P = _P(r)
    P(box('cs_box', (.050, .034, .016), (x, y, BZ + .008), M['white'], .004)); rk = box('CS_ROCKER', (.018, .020, .006), (x, y, BZ + .018), M['black'], .002, rot=(math.radians(10), 0, 0), coll='PROPS'); parent(rk, r)
    P(cyl('cs_cord', .0025, .5, (x + .27, y + .01, BZ + .003), M['black'], 8, 0, rot=(0, math.pi / 2, .05)))
    return r


def clock(M):
    """a little alarm clock he holds. Origin = centre of the back; face toward -Y. CLK_MIN / CLK_HR turn about Y."""
    r = _root('CLOCK'); P = _P(r); face = mat('WB_clockface', (.9, .88, .8), rough=.6, emit=(.75, .9, .8), es=.5); ink = mat('WB_label', (.02, .022, .03), rough=.6)
    P(cyl('clk_body', .050, .030, (0, -.015, 0), M['p_teal'], 48, .004, rot=(math.pi / 2, 0, 0))); P(cyl('clk_face', .044, .002, (0, -.0305, 0), face, 48, 0, rot=(math.pi / 2, 0, 0)))
    for s in (-1, 1): P(sph(f'clk_bell{s}', .016, (s * .030, -.015, .050), M['steel'], seg=16)); P(cyl(f'clk_foot{s}', .004, .02, (s * .030, -.015, -.052), M['steel'], 8, 0))
    for k in range(12):
        a = k * math.tau / 12; P(box(f'clk_tick{k}', (.0022, .0008, .007 if k % 3 else .011), (.037 * math.sin(a), -.0318, .037 * math.cos(a)), ink, 0, rot=(0, a, 0)))
    for nm, L, w in (('CLK_HR', .022, .0034), ('CLK_MIN', .034, .0024)):
        e = empty(nm, (0, -.033, 0), 'PROPS'); parent(e, r); h = box(nm + '_m', (w, .0008, L), (0, -.033, L / 2 - .003), ink, 0, coll='PROPS'); parent(h, e)
    P(cyl('clk_hub', .003, .003, (0, -.0345, 0), M['steel'], 12, 0, rot=(math.pi / 2, 0, 0)))
    # the winding key, on the side he can reach: CLK_KEY turns about X
    k = empty('CLK_KEY', (.050, -.012, 0), 'PROPS'); parent(k, r)
    for o in (cyl('clk_keystem', .0032, .016, (.058, -.012, 0), M['steel'], 12, 0, rot=(0, math.pi / 2, 0)), box('clk_keytab', (.0035, .020, .015), (.0685, -.012, 0), M['steel'], .0012)):
        col_link(o, 'PROPS'); parent(o, k)
    return r
