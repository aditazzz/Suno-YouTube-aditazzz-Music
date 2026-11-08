"""The design worker's screens in the sets (CD 13.2, design/screens/SPEC.md) as swappable image textures.

Textures live in blender/textures/screens/ (made by tools/make_screen_seqs.py from design/screens/screens.py), loaded
by path (relative in the saved blend), so a design change is a re-run of that script, never a set rebuild. Animated
screens are image sequences named <name>_f####.png with the film frame in the name (board f366-572; clock and
scheduler f573-768), held on their first/last image outside that range.

Kinds:
  display  a lit screen behind glass: emission = texture x strength, a glossy dark coat on top (reflections), no bloom
  sign     lit acrylic (the emergency sign): the same, a satin coat
  clock    a steel panel with a 7-segment LED window: only the lit (red-amber) pixels emit, the rest is the panel
  paper    the tag / a stencil decal: diffuse, alpha from the texture, no emission
"""
import bpy, os, math
from mathutils import Vector, Matrix

import lib_look as _L
TEX = os.path.join(_L.BLENDER, "textures", "screens")


def _img(rel, seq=None):
    """rel: 'emergency/sign.png' (still) or 'board' with seq=(f0, f1) (an image sequence named board/board_f####.png)."""
    if seq:
        f0, f1 = seq
        p = os.path.join(TEX, rel, f"{rel}_f{f0:04d}.png")
        im = bpy.data.images.load(p, check_existing=True)
        im.source = "SEQUENCE"
        return im, (f0, f1)
    return bpy.data.images.load(os.path.join(TEX, rel), check_existing=True), None


def _tex_node(nt, im, rng, interp="Cubic"):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    t.interpolation = interp            # crisp type at phone size; Cubic keeps the edges clean when the screen is small
    t.extension = "CLIP"
    if rng:
        f0, f1 = rng
        iu = t.image_user
        iu.frame_start = f0             # image number = frame - start + 1 + offset = the film frame
        iu.frame_offset = f0 - 1
        iu.frame_duration = f1 - f0 + 1
        iu.use_auto_refresh = True
        iu.use_cyclic = False
    return t


def material(name, kind, im, rng, strength=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    t = _tex_node(nt, im, rng)
    if kind in ("display", "sign"):
        bs.inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1)
        bs.inputs["Roughness"].default_value = 0.42 if kind == "display" else 0.35   # anti-glare signage glass: no hot streaks across the type
        bs.inputs["Specular IOR Level"].default_value = 0.5
        nt.links.new(t.outputs["Color"], bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value = strength
    elif kind == "clock":
        # emission only where the LED is: red-amber pixels (R high, G and B low); ghost segments glow faintly
        nt.links.new(t.outputs["Color"], bs.inputs["Base Color"])
        bs.inputs["Roughness"].default_value = 0.45
        bs.inputs["Metallic"].default_value = 0.0
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(t.outputs["Color"], sp.inputs["Color"])
        g6 = nt.nodes.new("ShaderNodeMath"); g6.operation = "MULTIPLY"; g6.inputs[1].default_value = 0.6
        nt.links.new(sp.outputs["Green"], g6.inputs[0])
        a1 = nt.nodes.new("ShaderNodeMath"); a1.operation = "SUBTRACT"
        nt.links.new(sp.outputs["Red"], a1.inputs[0]); nt.links.new(g6.outputs[0], a1.inputs[1])
        a2 = nt.nodes.new("ShaderNodeMath"); a2.operation = "SUBTRACT"
        nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(sp.outputs["Blue"], a2.inputs[1])
        k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.use_clamp = True; k.inputs[1].default_value = 1.8
        nt.links.new(a2.outputs[0], k.inputs[0])
        s = nt.nodes.new("ShaderNodeMath"); s.operation = "MULTIPLY"; s.inputs[1].default_value = strength
        nt.links.new(k.outputs[0], s.inputs[0])
        nt.links.new(t.outputs["Color"], bs.inputs["Emission Color"])
        nt.links.new(s.outputs[0], bs.inputs["Emission Strength"])
        # the acrylic window over the digits: a light clear coat everywhere
        bs.inputs["Coat Weight"].default_value = 0.6
        bs.inputs["Coat Roughness"].default_value = 0.08
    else:   # paper
        nt.links.new(t.outputs["Color"], bs.inputs["Base Color"])
        nt.links.new(t.outputs["Alpha"], bs.inputs["Alpha"])
        bs.inputs["Roughness"].default_value = 0.85
        try:
            m.surface_render_method = "DITHERED"
        except Exception:
            pass
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m


def plane(name, centre, w, h, normal, coll, mat, up=(0, 0, 1)):
    """A w x h plane at centre facing `normal`, the image upright (u along right, v along up)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, lp in enumerate(me.loops):
        uv.data[i].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][lp.vertex_index]
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    n = Vector(normal).normalized(); u = Vector(up)
    right = u.cross(n).normalized(); upv = n.cross(right).normalized()
    R = Matrix((right, upv, n)).transposed()
    ob.matrix_world = Matrix.Translation(Vector(centre)) @ R.to_4x4()
    return ob
