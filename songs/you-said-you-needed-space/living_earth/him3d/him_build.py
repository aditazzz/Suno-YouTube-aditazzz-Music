"""him_build.py: builds "him" (the satellite) and the rocket he rides at the open, from nothing, in code.
Run inside Blender (headless):  Blender -b --python him_build.py -- <out.blend>
Model space: Z up, his front is -Y, wings along +-X, 1 unit = his bus width. Every object is HIM_* or RKT_*.
The rig is plain parenting (empties); him_rig.py poses it as a pure function of time. Look-dev only (Nov 9).
"""
import bpy, bmesh, math, sys
from mathutils import Matrix, Vector

R = math.radians
HIS = (1.0, 0.72, 0.42)  # grade.ts hisColor (linear)

# ----------------------------------------------------------------------------- materials (PBR, procedural maps)
def _nt(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    return m, nt, b

def _n(nt, typ, **kw):
    n = nt.nodes.new(typ)
    for k, v in kw.items():
        if k.startswith('i_'): n.inputs[k[2:].replace('_', ' ')].default_value = v
        else: setattr(n, k, v)
    return n

def _coords(nt, scale=(1, 1, 1), swap_xz=False):
    tc = _n(nt, 'ShaderNodeTexCoord'); mp = _n(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale
    if swap_xz: mp.inputs['Rotation'].default_value = (R(90), 0, 0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); return mp.outputs['Vector']

def mat_foil():
    """Gold multilayer insulation: metallic, crinkled, quilted."""
    m, nt, b = _nt('HIM_foil'); L = nt.links.new; v = _coords(nt)
    b.inputs['Metallic'].default_value = 1.0
    wn = _n(nt, 'ShaderNodeTexNoise'); wn.inputs['Scale'].default_value = 5.0; wn.inputs['Detail'].default_value = 3; L(v, wn.inputs['Vector'])
    wm = _n(nt, 'ShaderNodeMix'); wm.data_type = 'VECTOR'; wm.inputs[0].default_value = 0.16; L(v, wm.inputs[4]); L(wn.outputs['Color'], wm.inputs[5])
    vor = _n(nt, 'ShaderNodeTexVoronoi', feature='F1'); vor.inputs['Scale'].default_value = 15.0; L(wm.outputs[1], vor.inputs['Vector'])
    noi = _n(nt, 'ShaderNodeTexNoise'); noi.inputs['Scale'].default_value = 26; noi.inputs['Detail'].default_value = 6; L(v, noi.inputs['Vector'])
    big = _n(nt, 'ShaderNodeTexNoise'); big.inputs['Scale'].default_value = 2.2; big.inputs['Detail'].default_value = 2; L(v, big.inputs['Vector'])
    col = _n(nt, 'ShaderNodeValToRGB'); col.color_ramp.elements[0].color = (0.90, 0.44, 0.07, 1); col.color_ramp.elements[1].color = (1.0, 0.66, 0.20, 1)
    L(big.outputs['Fac'], col.inputs['Fac']); L(col.outputs['Color'], b.inputs['Base Color'])
    rg = _n(nt, 'ShaderNodeMapRange'); rg.inputs['To Min'].default_value = 0.16; rg.inputs['To Max'].default_value = 0.42
    L(noi.outputs['Fac'], rg.inputs['Value']); L(rg.outputs['Result'], b.inputs['Roughness'])
    crk = _n(nt, 'ShaderNodeMapRange'); crk.inputs['From Max'].default_value = 0.7; L(vor.outputs['Distance'], crk.inputs['Value'])
    b1 = _n(nt, 'ShaderNodeBump'); b1.inputs['Strength'].default_value = 0.5; b1.inputs['Distance'].default_value = 0.012; L(crk.outputs['Result'], b1.inputs['Height'])
    b2 = _n(nt, 'ShaderNodeBump'); b2.inputs['Strength'].default_value = 0.35; b2.inputs['Distance'].default_value = 0.006
    L(noi.outputs['Fac'], b2.inputs['Height']); L(b1.outputs['Normal'], b2.inputs['Normal']); L(b2.outputs['Normal'], b.inputs['Normal'])
    return m

def mat_white():
    """Warm white thermal paint: panel lines, a little wear."""
    m, nt, b = _nt('HIM_white'); L = nt.links.new; v = _coords(nt)
    noi = _n(nt, 'ShaderNodeTexNoise'); noi.inputs['Scale'].default_value = 9; noi.inputs['Detail'].default_value = 5; L(v, noi.inputs['Vector'])
    col = _n(nt, 'ShaderNodeValToRGB'); col.color_ramp.elements[0].color = (0.74, 0.70, 0.62, 1); col.color_ramp.elements[1].color = (0.95, 0.91, 0.82, 1)
    col.color_ramp.elements[0].position = 0.25; col.color_ramp.elements[1].position = 0.6
    L(noi.outputs['Fac'], col.inputs['Fac']); L(col.outputs['Color'], b.inputs['Base Color'])
    rg = _n(nt, 'ShaderNodeMapRange'); rg.inputs['To Min'].default_value = 0.30; rg.inputs['To Max'].default_value = 0.55
    L(noi.outputs['Fac'], rg.inputs['Value']); L(rg.outputs['Result'], b.inputs['Roughness'])
    b.inputs['Coat Weight'].default_value = 0.25; b.inputs['Coat Roughness'].default_value = 0.15
    fine = _n(nt, 'ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = 90; L(v, fine.inputs['Vector'])
    bp = _n(nt, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; bp.inputs['Distance'].default_value = 0.003
    L(fine.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def mat_cells():
    """Solar cells under cover glass: deep blue, a warm gold grid, cell-to-cell variation."""
    m, nt, b = _nt('HIM_cells'); L = nt.links.new; v = _coords(nt, swap_xz=True)
    br = _n(nt, 'ShaderNodeTexBrick'); br.offset = 0.0
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.0028; br.inputs['Mortar Smooth'].default_value = 0.1
    br.inputs['Brick Width'].default_value = 0.1; br.inputs['Row Height'].default_value = 0.1533
    br.inputs['Color1'].default_value = (0.010, 0.034, 0.17, 1); br.inputs['Color2'].default_value = (0.018, 0.060, 0.26, 1)
    br.inputs['Mortar'].default_value = (0.70, 0.58, 0.42, 1); L(v, br.inputs['Vector'])
    L(br.outputs['Color'], b.inputs['Base Color'])
    # fine bus bars inside each cell
    wv = _n(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y'); wv.inputs['Scale'].default_value = 60; wv.inputs['Distortion'].default_value = 0; L(v, wv.inputs['Vector'])
    rr = _n(nt, 'ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.10; rr.inputs['To Max'].default_value = 0.22
    L(wv.outputs['Fac'], rr.inputs['Value'])
    mx = _n(nt, 'ShaderNodeMix'); mx.inputs[3].default_value = 0.38; L(br.outputs['Fac'], mx.inputs[0]); L(rr.outputs['Result'], mx.inputs[2]); L(mx.outputs[0], b.inputs['Roughness'])
    b.inputs['Metallic'].default_value = 0.55
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.04
    bp = _n(nt, 'ShaderNodeBump'); bp.invert = True; bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.004
    L(br.outputs['Fac'], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def mat_metal(name, color, rough, metallic=1.0):
    m, nt, b = _nt(name); L = nt.links.new; v = _coords(nt, scale=(1, 1, 14))
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metallic
    noi = _n(nt, 'ShaderNodeTexNoise'); noi.inputs['Scale'].default_value = 40; L(v, noi.inputs['Vector'])
    rg = _n(nt, 'ShaderNodeMapRange'); rg.inputs['To Min'].default_value = rough * 0.75; rg.inputs['To Max'].default_value = rough * 1.3
    L(noi.outputs['Fac'], rg.inputs['Value']); L(rg.outputs['Result'], b.inputs['Roughness'])
    return m

def mat_glass():
    m, nt, b = _nt('HIM_glass')
    b.inputs['Base Color'].default_value = (0.004, 0.005, 0.012, 1); b.inputs['Roughness'].default_value = 0.03
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.02
    b.inputs['Coat Tint'].default_value = (0.75, 0.6, 1.0, 1)
    return m

def mat_emit(name, color, strength):
    """A real light source only: the eye, the status lights, the beacon, the engine."""
    m, nt, b = _nt(name)
    b.inputs['Base Color'].default_value = (0, 0, 0, 1); b.inputs['Roughness'].default_value = 0.4
    b.inputs['Emission Color'].default_value = (*color, 1); b.inputs['Emission Strength'].default_value = strength
    return m

def mat_flame():
    m, nt, b = _nt('RKT_flame'); L = nt.links.new
    tc = _n(nt, 'ShaderNodeTexCoord'); sp = _n(nt, 'ShaderNodeSeparateXYZ'); L(tc.outputs['Generated'], sp.inputs['Vector'])
    ramp = _n(nt, 'ShaderNodeValToRGB'); e = ramp.color_ramp.elements
    e[0].position = 0.0; e[0].color = (1.0, 0.25, 0.04, 1); e[1].position = 1.0; e[1].color = (1.0, 0.93, 0.78, 1)
    mid = ramp.color_ramp.elements.new(0.7); mid.color = (1.0, 0.62, 0.22, 1)
    L(sp.outputs['Z'], ramp.inputs['Fac'])
    a = _n(nt, 'ShaderNodeMath', operation='POWER'); a.inputs[1].default_value = 1.6; L(sp.outputs['Z'], a.inputs[0])
    lw = _n(nt, 'ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    inv = _n(nt, 'ShaderNodeMath', operation='SUBTRACT'); inv.inputs[0].default_value = 1.0; L(lw.outputs['Facing'], inv.inputs[1])
    mul = _n(nt, 'ShaderNodeMath', operation='MULTIPLY'); L(a.outputs[0], mul.inputs[0]); L(inv.outputs[0], mul.inputs[1])
    st = _n(nt, 'ShaderNodeMath', operation='MULTIPLY'); st.inputs[1].default_value = 9.0; L(mul.outputs[0], st.inputs[0])
    b.inputs['Base Color'].default_value = (0, 0, 0, 1)
    L(ramp.outputs['Color'], b.inputs['Emission Color']); L(st.outputs[0], b.inputs['Emission Strength']); L(mul.outputs[0], b.inputs['Alpha'])
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m

# ----------------------------------------------------------------------------- geometry: groups of parts in one mesh
class Grp:
    """One rigid group = one mesh object (parts merged, a material slot per material)."""
    def __init__(self, name):
        self.name = name; self.bm = bmesh.new(); self.mats = []
    def _slot(self, mat):
        if mat not in self.mats: self.mats.append(mat)
        return self.mats.index(mat)
    def _merge(self, tb, mat, M, by_normal=None):
        tb.faces.ensure_lookup_table(); idx = self._slot(mat)
        for f in tb.faces: f.material_index = idx; f.smooth = True
        if by_normal:
            tb.normal_update()
            for test, m2 in by_normal:
                i2 = self._slot(m2)
                for f in tb.faces:
                    if test(f.normal): f.material_index = i2
        bmesh.ops.transform(tb, matrix=M, verts=tb.verts)
        me = bpy.data.meshes.new('_tmp'); tb.to_mesh(me); tb.free(); self.bm.from_mesh(me); bpy.data.meshes.remove(me)
    def box(self, size, mat, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, segs=3, by_normal=None):
        tb = bmesh.new(); bmesh.ops.create_cube(tb, size=1.0)
        bmesh.ops.scale(tb, vec=size, verts=tb.verts)
        if bevel > 0: bmesh.ops.bevel(tb, geom=tb.edges[:], offset=bevel, segments=segs, profile=0.5, affect='EDGES')
        self._merge(tb, mat, T(loc, rot), by_normal)
    def cyl(self, r, h, mat, loc=(0, 0, 0), rot=(0, 0, 0), r2=None, segs=32):
        tb = bmesh.new(); bmesh.ops.create_cone(tb, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
        self._merge(tb, mat, T(loc, rot))
    def tube(self, p0, p1, r, mat, segs=14):
        p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
        tb = bmesh.new(); bmesh.ops.create_cone(tb, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length)
        self._merge(tb, mat, Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4())
    def sphere(self, r, mat, loc=(0, 0, 0), scale=(1, 1, 1), segs=32):
        tb = bmesh.new(); bmesh.ops.create_uvsphere(tb, u_segments=segs, v_segments=segs // 2, radius=r)
        self._merge(tb, mat, Matrix.Translation(loc) @ Matrix.Diagonal((*scale, 1)))
    def lathe(self, profile, mat, loc=(0, 0, 0), rot=(0, 0, 0), segs=48, sweep=360.0, start=0.0, closed=False):
        """Surface of revolution about Z from [(r, z), ...]. sweep < 360 = an open shell (fairing halves)."""
        tb = bmesh.new(); full = sweep >= 359.9; n = segs if full else segs + 1; rings = []
        for (r, z) in profile:
            ring = []
            for i in range(n):
                a = R(start + sweep * i / segs)
                ring.append(tb.verts.new((r * math.cos(a), r * math.sin(a), z)))
            rings.append(ring)
        pairs = list(zip(rings[:-1], rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
        for a, b_ in pairs:
            for i in range(segs):
                j = (i + 1) % n
                if not full and i + 1 >= n: continue
                try: tb.faces.new((a[i], a[j], b_[j], b_[i]))
                except ValueError: pass
        bmesh.ops.remove_doubles(tb, verts=tb.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(tb, faces=tb.faces)
        self._merge(tb, mat, T(loc, rot))
    def torus(self, Rr, r, mat, loc=(0, 0, 0), rot=(0, 0, 0), segs=48, tsegs=12):
        prof = [(Rr + r * math.cos(2 * math.pi * i / tsegs), r * math.sin(2 * math.pi * i / tsegs)) for i in range(tsegs)]
        self.lathe(prof, mat, loc, rot, segs=segs, closed=True)
    def poly_plate(self, pts2d, thick, mat, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0):
        """A flat plate from an outline in XZ, thickness along Y (fins)."""
        tb = bmesh.new(); vs = [tb.verts.new((x, -thick / 2, z)) for x, z in pts2d]; f = tb.faces.new(vs)
        ex = bmesh.ops.extrude_face_region(tb, geom=[f]); bmesh.ops.translate(tb, vec=(0, thick, 0), verts=[g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)])
        bmesh.ops.recalc_face_normals(tb, faces=tb.faces)
        if bevel > 0: bmesh.ops.bevel(tb, geom=tb.edges[:], offset=bevel, segments=2, profile=0.5, affect='EDGES')
        self._merge(tb, mat, T(loc, rot))
    def done(self, parent=None, loc=(0, 0, 0), bevel=0.006, solidify=0.0):
        me = bpy.data.meshes.new(self.name); self.bm.normal_update(); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats: me.materials.append(m)
        try: me.set_sharp_from_angle(angle=R(38))
        except Exception: pass
        ob = bpy.data.objects.new(self.name, me); bpy.context.scene.collection.objects.link(ob)
        ob.parent = parent; ob.location = loc
        if solidify:
            s = ob.modifiers.new('solid', 'SOLIDIFY'); s.thickness = solidify; s.offset = 0
        if bevel:
            bv = ob.modifiers.new('bevel', 'BEVEL'); bv.width = bevel; bv.segments = 2; bv.limit_method = 'ANGLE'; bv.angle_limit = R(40); bv.harden_normals = True
        return ob

def T(loc=(0, 0, 0), rot=(0, 0, 0)):
    from mathutils import Euler
    return Matrix.Translation(loc) @ Euler(rot, 'XYZ').to_matrix().to_4x4()

def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.1; bpy.context.scene.collection.objects.link(e)
    e.parent = parent; e.location = loc; e.rotation_mode = 'XYZ'; return e

# ----------------------------------------------------------------------------- him
def build_him(M):
    root = empty('HIM_root'); bob = empty('HIM_bob', root)
    # ---- the bus (his torso): gold foil, decks, chest plate with three warm status lights, radiator, rails, engine
    g = Grp('HIM_body')
    g.box((1.0, 0.8, 1.1), M['foil'], bevel=0.075, segs=4)
    for z in (0.565, -0.565): g.box((1.05, 0.85, 0.045), M['alu'], loc=(0, 0, z), bevel=0.012, segs=2)
    for z in (0.27, -0.30): g.box((1.016, 0.816, 0.028), M['alu'], loc=(0, 0, z), bevel=0.006, segs=1)        # straps over the foil
    g.box((0.60, 0.035, 0.46), M['white'], loc=(0, -0.405, -0.015), bevel=0.014, segs=2)                       # chest plate
    for i in range(5): g.box((0.34, 0.016, 0.018), M['dark'], loc=(0, -0.425, -0.12 - 0.032 * i), bevel=0.003, segs=1)  # vent slats
    for x in (-0.14, 0.0, 0.14): g.cyl(0.036, 0.02, M['dark'], loc=(x, -0.425, 0.10), rot=(R(90), 0, 0), segs=20)       # light bezels
    for x in (-0.24, 0.24):                                                                                     # chest bolts
        for z in (0.17, -0.20): g.cyl(0.012, 0.012, M['alu'], loc=(x, -0.425, z), rot=(R(90), 0, 0), segs=6)
    g.box((0.74, 0.03, 0.84), M['white'], loc=(0, 0.405, 0.0), bevel=0.012, segs=2)                             # back radiator
    for i in range(9): g.box((0.62, 0.02, 0.05), M['alu'], loc=(0, 0.428, -0.32 + 0.08 * i), rot=(R(28), 0, 0), bevel=0.004, segs=1)
    for s in (-1, 1):
        g.cyl(0.11, 0.07, M['dark'], loc=(s * 0.52, 0, 0.08), rot=(0, R(90), 0))                                # shoulder bearings
        g.torus(0.11, 0.012, M['gold'], loc=(s * 0.556, 0, 0.08), rot=(0, R(90), 0))
        g.tube((s * 0.44, -0.445, -0.36), (s * 0.44, -0.445, 0.36), 0.013, M['alu'])                            # handrails
        for z in (-0.3, 0.0, 0.3): g.tube((s * 0.44, -0.39, z), (s * 0.44, -0.445, z), 0.009, M['alu'], segs=8)
        g.box((0.03, 0.30, 0.22), M['white'], loc=(s * 0.505, 0.18, -0.28), bevel=0.008, segs=1)                # side equipment boxes
        g.tube((s * 0.515, 0.10, -0.12), (s * 0.515, 0.26, 0.42), 0.008, M['dark'], segs=8)                     # a cable run
    g.cyl(0.19, 0.14, M['dark'], loc=(0, -0.10, 0.645), r2=0.165)                                              # neck collar
    g.torus(0.172, 0.014, M['gold'], loc=(0, -0.10, 0.70))
    bell = [(0.07, 0.0), (0.085, -0.04), (0.13, -0.12), (0.185, -0.22), (0.215, -0.30), (0.20, -0.30), (0.17, -0.22), (0.115, -0.12), (0.06, -0.03)]
    g.lathe(bell, M['dark'], loc=(0, 0, -0.585), closed=True, segs=40)                                          # main engine bell
    for sx in (-1, 1):
        for sy in (-1, 1):                                                                                      # attitude thrusters
            g.box((0.07, 0.07, 0.05), M['alu'], loc=(sx * 0.43, sy * 0.33, -0.61), bevel=0.008, segs=1)
            g.cyl(0.012, 0.05, M['dark'], loc=(sx * 0.47, sy * 0.33, -0.63), rot=(0, R(sx * 60), 0), r2=0.024, segs=12)
            g.cyl(0.012, 0.05, M['dark'], loc=(sx * 0.43, sy * 0.37, -0.63), rot=(R(-sy * 60), 0, 0), r2=0.024, segs=12)
    g.cyl(0.035, 0.42, M['alu'], loc=(0.26, 0.24, 0.79))                                                        # dish mast
    g.cyl(0.05, 0.04, M['dark'], loc=(0.26, 0.24, 0.60), segs=20)
    g.cyl(0.03, 0.06, M['dark'], loc=(-0.34, 0.28, 0.61), segs=16)                                              # whip socket
    for sx in (-1, 1):                                                                                          # his two warm work lamps (real sources)
        g.cyl(0.03, 0.05, M['dark'], loc=(sx * 0.42, -0.36, 0.612), segs=16); g.cyl(0.045, 0.05, M['dark'], loc=(sx * 0.42, -0.385, 0.66), rot=(R(62), 0, 0), r2=0.055, segs=20)
    body = g.done(bob)
    for sx, nm in ((-1, 'R'), (1, 'L')):
        lg = Grp(f'HIM_lamp{nm}'); lg.sphere(0.04, M['lamp'], loc=(sx * 0.42, -0.408, 0.672), scale=(1, 0.5, 1), segs=16); lg.done(bob, bevel=0)
        ld = bpy.data.lights.new(f'HIM_lamplight{nm}', 'POINT'); ld.energy = 5.0; ld.color = (1.0, 0.66, 0.36); ld.shadow_soft_size = 0.04
        lo = bpy.data.objects.new(f'HIM_lamplight{nm}', ld); bpy.context.scene.collection.objects.link(lo); lo.parent = bob; lo.location = (sx * 0.46, -0.50, 0.70)
    leds = []
    for i, x in enumerate((-0.14, 0.0, 0.14)):
        lg = Grp(f'HIM_led{i}'); lg.sphere(0.028, M[f'led{i}'], loc=(x, -0.432, 0.10), scale=(1, 0.55, 1), segs=16); leds.append(lg.done(bob, bevel=0))
    # ---- his head: a camera turret with one big warm eye, a brow visor, a monocle star tracker
    neck = empty('HIM_neck', bob, (0, -0.10, 0.70))          # pan (Z) then tilt (X)
    head = empty('HIM_head', neck)
    g = Grp('HIM_headshell')
    g.box((0.70, 0.56, 0.46), M['white'], loc=(0, -0.02, 0.27), bevel=0.14, segs=6)
    g.box((0.708, 0.568, 0.05), M['gold'], loc=(0, -0.02, 0.105), bevel=0.02, segs=2)                           # trim band
    g.cyl(0.13, 0.06, M['dark'], loc=(0, 0, 0.02))                                                              # neck stub
    hood = [(0.215, 0.0), (0.225, 0.02), (0.225, 0.17), (0.212, 0.18), (0.195, 0.17), (0.185, 0.03), (0.185, 0.0)]
    g.lathe(hood, M['dark'], loc=(0, -0.27, 0.27), rot=(R(90), 0, 0), closed=True)                              # lens hood (opens to -Y)
    g.torus(0.222, 0.012, M['gold'], loc=(0, -0.445, 0.27), rot=(R(90), 0, 0))                                  # hood lip
    g.torus(0.228, 0.010, M['gold'], loc=(0, -0.305, 0.27), rot=(R(90), 0, 0))
    g.sphere(0.168, M['glass'], loc=(0, -0.335, 0.27), scale=(1, 0.42, 1))                                      # the lens
    g.cyl(0.055, 0.20, M['dark'], loc=(0.385, -0.06, 0.33), rot=(R(90), 0, 0), segs=24)                         # star tracker (his monocle)
    g.cyl(0.045, 0.012, M['glass'], loc=(0.385, -0.162, 0.33), rot=(R(90), 0, 0), segs=24)
    g.box((0.05, 0.10, 0.07), M['alu'], loc=(0.345, -0.02, 0.33), bevel=0.008, segs=1)
    g.cyl(0.012, 0.16, M['alu'], loc=(-0.30, 0.10, 0.56), segs=10)                                              # a stub aerial
    g.sphere(0.02, M['alu'], loc=(-0.30, 0.10, 0.645), segs=12)
    for x in (-0.2, 0.2): g.cyl(0.014, 0.012, M['alu'], loc=(x, -0.302, 0.44), rot=(R(90), 0, 0), segs=6)
    g.box((0.30, 0.012, 0.012), M['dark'], loc=(0, 0.262, 0.30), bevel=0.003, segs=1)                           # seams on the back of his head
    g.box((0.30, 0.012, 0.012), M['dark'], loc=(0, 0.262, 0.22), bevel=0.003, segs=1)
    headshell = g.done(head)
    g = Grp('HIM_iris'); g.torus(0.160, 0.024, M['eye'], loc=(0, -0.330, 0.27), rot=(R(90), 0, 0)); g.done(head, bevel=0)   # him_wire: a bolder ring (was 0.013), the lit eye is his face
    pupil = empty('HIM_pupil', head, (0, -0.405, 0.27))
    g = Grp('HIM_pupilglow'); g.sphere(0.064, M['pupil'], scale=(1, 0.3, 1), segs=20); g.done(pupil, bevel=0)
    brow = empty('HIM_brow', head, (0, -0.30, 0.525))        # tilt (X) = mood, roll (Y) = a cocked brow
    # him_wire (Nov 9): the brow was a thin gold arc lying back over the head and did not read under a quarter of the frame.
    # Now a thick dark visor that overhangs the eye (0.25 forward of the face, past the hood lip) with a gold lip and end
    # caps: dark over the bright eye, so its angle reads small; tilted down its front edge drops over the top of the eye.
    g = Grp('HIM_browplate')
    arc = [(0.262, 0.0), (0.304, 0.0), (0.304, 0.25), (0.262, 0.25)]
    g.lathe(arc, M['dark'], loc=(0, 0, -0.255), rot=(R(90), 0, 0), sweep=136, start=22, closed=True, segs=28)
    lip = [(0.257, 0.25), (0.310, 0.25), (0.310, 0.278), (0.257, 0.278)]
    g.lathe(lip, M['gold'], loc=(0, 0, -0.255), rot=(R(90), 0, 0), sweep=136, start=22, closed=True, segs=28)
    for a in (22, 158):
        g.box((0.058, 0.278, 0.014), M['gold'], loc=(0.283 * math.cos(R(a)), -0.139, -0.255 + 0.283 * math.sin(R(a))), rot=(0, -R(a), 0), bevel=0.003, segs=1)
    g.done(brow, bevel=0.004)
    # his eyelid: a shutter inside the lens hood, hinged at the top (scale Z of HIM_lid: 0.02 open .. 1 half shut .. 2 shut).
    # It changes the SHAPE of the lit eye (a half moon = smug / tired / hurt), which reads at any size.
    lid = empty('HIM_lid', head, (0, -0.432, 0.27 + 0.184)); lid.scale = (1, 1, 0.02)
    g = Grp('HIM_lidplate')
    g.lathe([(0.004, 0.0), (0.184, 0.0), (0.184, 0.010), (0.004, 0.010)], M['dark'], loc=(0, 0, -0.184), rot=(R(90), 0, 0), sweep=180, start=0, closed=True, segs=24)
    g.box((0.366, 0.014, 0.014), M['gold'], loc=(0, -0.005, -0.184), bevel=0.002, segs=1)
    g.done(lid, bevel=0)
    # the eye is a light: it spills on the hood and brow
    ld = bpy.data.lights.new('HIM_eyelight', 'POINT'); ld.energy = 2.2; ld.color = HIS; ld.shadow_soft_size = 0.06
    lo = bpy.data.objects.new('HIM_eyelight', ld); bpy.context.scene.collection.objects.link(lo); lo.parent = head; lo.location = (0, -0.47, 0.27)
    # ---- wings: a yoke and three hinged panels a side
    wings = {}
    for s, nm in ((1, 'L'), (-1, 'R')):
        wr = empty(f'HIM_wing{nm}', bob, (s * 0.555, 0, 0.08))       # twist (X), flap (Y)
        g = Grp(f'HIM_yoke{nm}')
        g.tube((0, 0, 0), (s * 0.20, 0, 0), 0.034, M['alu'])
        g.tube((s * 0.20, 0, -0.34), (s * 0.20, 0, 0.34), 0.022, M['alu'])
        g.tube((s * 0.08, 0, 0), (s * 0.20, 0, 0.30), 0.012, M['alu'], segs=8); g.tube((s * 0.08, 0, 0), (s * 0.20, 0, -0.30), 0.012, M['alu'], segs=8)
        g.done(wr)
        par, segs = wr, []
        for i in range(3):
            h = empty(f'HIM_wing{nm}_h{i}', par, (s * (0.22 if i == 0 else 0.64), 0, 0))   # fold (Z)
            g = Grp(f'HIM_panel{nm}{i}')
            g.box((0.60, 0.022, 0.94), M['kapton'], loc=(s * 0.32, 0, 0), bevel=0.004, segs=1, by_normal=[(lambda n: n.y < -0.9, M['cells'])])
            for z in (-0.235, 0.235): g.tube((s * 0.02, 0.016, z), (s * 0.62, 0.016, z), 0.007, M['alu'], segs=6)
            for xx in (0.22, 0.42): g.tube((s * xx, 0.016, -0.47), (s * xx, 0.016, 0.47), 0.007, M['alu'], segs=6)
            for a, b_ in (((0.02, 0.47), (0.62, 0.47)), ((0.02, -0.47), (0.62, -0.47)), ((0.02, -0.47), (0.02, 0.47)), ((0.62, -0.47), (0.62, 0.47))):
                g.tube((s * a[0], 0, a[1]), (s * b_[0], 0, b_[1]), 0.013, M['alu'], segs=8)                 # frame
            g.tube((s * 0.02, 0.016, 0.0), (s * 0.62, 0.016, 0.0), 0.010, M['alu'], segs=8)                # back spar
            for z in (-0.3, 0.3): g.cyl(0.02, 0.10, M['dark'], loc=(0, 0, z), segs=12)                      # hinge barrels
            g.done(h)
            segs.append(h); par = h
        wings[nm] = (wr, segs)
    # ---- dish: his ear / hat, on a two-axis gimbal
    daz = empty('HIM_dish_az', bob, (0.26, 0.24, 1.0)); delv = empty('HIM_dish_el', daz)
    g = Grp('HIM_dish')
    f = 0.30; prof = [(r, r * r / (4 * f)) for r in [0.03 + 0.39 * i / 14 for i in range(15)]]
    g.lathe(prof, M['white'], loc=(0, 0, 0.07))
    g.done(delv, bevel=0, solidify=0.014)
    g = Grp('HIM_dishparts')
    rimz = 0.42 * 0.42 / (4 * f) + 0.07
    g.torus(0.42, 0.013, M['gold'], loc=(0, 0, rimz))
    g.cyl(0.05, 0.08, M['dark'], loc=(0, 0, 0.035), segs=20); g.sphere(0.055, M['dark'], segs=16)
    for k in range(3):
        a = R(90 + 120 * k); g.tube((0.40 * math.cos(a), 0.40 * math.sin(a), rimz), (0.03 * math.cos(a), 0.03 * math.sin(a), 0.36), 0.008, M['alu'], segs=8)
    g.cyl(0.04, 0.07, M['alu'], loc=(0, 0, 0.365), r2=0.028, segs=16)
    g.done(delv)
    # ---- whip aerial with a warm beacon at the tip: follow-through
    whip = []; par = empty('HIM_whip0', bob, (-0.34, 0.28, 0.64)); whip.append(par)
    for i in range(5):
        g = Grp(f'HIM_whipseg{i}'); g.cyl(0.011 - 0.0012 * i, 0.2, M['alu'], loc=(0, 0, 0.1), r2=0.011 - 0.0012 * (i + 1), segs=8); g.done(par, bevel=0)
        if i < 4: par = empty(f'HIM_whip{i + 1}', par, (0, 0, 0.2)); whip.append(par)
    g = Grp('HIM_beacon'); g.sphere(0.028, M['beacon'], loc=(0, 0, 0.215), segs=16); g.done(par, bevel=0)
    return root

# ----------------------------------------------------------------------------- the rocket he rides at the open
def build_rocket(M):
    root = empty('RKT_root')
    g = Grp('RKT_body')
    prof = [(0.0, 0.25), (0.62, 0.25), (0.80, 0.0), (0.86, 0.02), (0.86, 3.3), (0.875, 3.32), (0.875, 3.62), (0.86, 3.64), (0.86, 7.0), (0.80, 7.06), (0.52, 7.55), (0.0, 7.55)]
    g.lathe(prof, M['rwhite'], segs=64)
    g.lathe([(0.878, 3.30), (0.878, 3.64)], M['dark'], segs=64)                                                 # interstage
    g.lathe([(0.864, 5.25), (0.872, 5.27), (0.872, 5.68), (0.864, 5.70)], M['foil'], segs=64)                   # his gold band
    g.lathe([(0.864, 0.02), (0.864, 0.55)], M['dark'], segs=64)                                                 # engine skirt, scorched
    for z in (1.4, 2.4, 4.5, 6.3): g.torus(0.862, 0.008, M['alu'], loc=(0, 0, z), segs=64, tsegs=6)             # weld rings
    g.tube((0.87, 0, 0.7), (0.87, 0, 6.8), 0.03, M['alu'], segs=8)                                              # cable raceway
    bell = [(0.20, 0.0), (0.24, -0.10), (0.36, -0.32), (0.48, -0.60), (0.53, -0.80), (0.50, -0.80), (0.44, -0.60), (0.32, -0.32), (0.18, -0.06)]
    g.lathe(bell, M['dark'], loc=(0, 0, 0.26), closed=True)
    for k in range(4):
        a = R(45 + 90 * k)
        g.lathe([(r * 0.42, z * 0.42) for r, z in bell], M['dark'], loc=(0.52 * math.cos(a), 0.52 * math.sin(a), 0.22), closed=True, segs=24)
        g.poly_plate([(0.84, 0.05), (0.84, 1.9), (1.05, 1.25), (1.75, 0.25), (1.75, -0.25), (1.0, -0.05)], 0.05, M['rwhite'], rot=(0, 0, R(90 * k)), bevel=0.012)
        g.poly_plate([(1.02, 1.30), (1.07, 1.28), (1.77, 0.27), (1.75, 0.22)], 0.056, M['gold'], rot=(0, 0, R(90 * k)))  # gold leading edge
    g.lathe([(0.52, 7.55), (0.50, 7.60), (0.36, 7.78), (0.30, 7.78), (0.30, 7.55)], M['alu'], closed=True)      # payload adapter (he sits in it)
    g.done(root)
    # fairing halves, open like petals
    ogive = [(0.86 * math.sqrt(max(0.0, 1 - (z / 3.0) ** 1.8)), z) for z in [3.0 * i / 16 for i in range(16)]] + [(0.03, 2.98)]
    fair = []
    for k, nm in ((0, 'A'), (1, 'B')):
        hz = empty(f'RKT_fairing{nm}', root, ((0.86 if k == 0 else -0.86), 0, 7.0))     # opens about Y
        g = Grp(f'RKT_fairshell{nm}')
        g.lathe(ogive, M['rwhite'], loc=((-0.86 if k == 0 else 0.86), 0, 0.0), sweep=176, start=(-88 if k == 0 else 92), segs=32)
        g.done(hz, bevel=0, solidify=0.03); fair.append(hz)
    fl = empty('RKT_flame', root, (0, 0, -0.5))
    g = Grp('RKT_flamecone'); g.lathe([(0.02, -6.5), (0.25, -4.0), (0.46, -1.6), (0.52, -0.3), (0.42, 0.0)], M['flame'], segs=32); g.done(fl, bevel=0)
    ld = bpy.data.lights.new('RKT_flamelight', 'POINT'); ld.energy = 900; ld.color = (1.0, 0.62, 0.3); ld.shadow_soft_size = 0.5
    lo = bpy.data.objects.new('RKT_flamelight', ld); bpy.context.scene.collection.objects.link(lo); lo.parent = fl; lo.location = (0, 0, -1.2)
    seat = empty('RKT_seat', root, (0, 0, 8.38))      # where his HIM_root goes when he rides
    return root

def materials():
    M = {
        'foil': mat_foil(), 'white': mat_white(), 'cells': mat_cells(), 'glass': mat_glass(),
        'alu': mat_metal('HIM_alu', (0.78, 0.78, 0.80), 0.30), 'dark': mat_metal('HIM_dark', (0.035, 0.035, 0.04), 0.42),
        'gold': mat_metal('HIM_goldtrim', (1.0, 0.62, 0.22), 0.26), 'kapton': mat_metal('HIM_kapton', (0.80, 0.40, 0.08), 0.34, 0.9),
        'eye': mat_emit('HIM_eye', (1.0, 0.52, 0.20), 7.0), 'pupil': mat_emit('HIM_pupilmat', (1.0, 0.60, 0.28), 8.0),
        'beacon': mat_emit('HIM_beaconmat', (1.0, 0.30, 0.08), 12.0), 'lamp': mat_emit('HIM_lampmat', (1.0, 0.58, 0.26), 6.0), 'flame': mat_flame(),
    }
    for i in range(3): M[f'led{i}'] = mat_emit(f'HIM_ledmat{i}', (1.0, 0.48, 0.15), 5.0)
    rw = mat_white().copy(); rw.name = 'RKT_white'; M['rwhite'] = rw
    return M

def main(out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = materials(); build_him(M); build_rocket(M)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print('[him_build] saved', out, 'objects', len(bpy.data.objects), 'tris~', sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'))

if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1])
