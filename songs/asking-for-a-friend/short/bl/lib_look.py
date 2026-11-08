"""Shared look code for the Short's sets (runs inside Blender). Materials from Poly Haven CC0 maps, lights, render settings.

Rules it enforces (look-and-light): every surface a real PBR material (albedo, roughness, normal), zero emission on
anything that isn't a light; lights are real sources with inverse-square falloff (Blender's default) and short custom
distances for small practicals.
"""
import bpy, os, math, json
from mathutils import Vector

# where the film's Blender project lives (the .blend files and the CC0 textures; not in the repo): AFF_BLENDER_DIR,
# else <home>/Documents/Original Music/<AFF_PROJ>/blender
HOME_ROOT = os.path.expanduser("~")
BLENDER = os.environ.get("AFF_BLENDER_DIR") or os.path.join(HOME_ROOT, "Documents", "Original Music",
                                                             os.environ.get("AFF_PROJ", "Asking for a Friend 2"), "blender")
PH = os.path.join(BLENDER, "textures", "ph")
LOG = []
bpy.context.preferences.filepaths.save_version = 0   # no .blend1 backups of our own builds


def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print("[look]", s)


def _img(path, noncolor):
    im = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def ph_map(aid, kind):
    d = os.path.join(PH, aid)
    for f in sorted(os.listdir(d)):
        if f.startswith(f"{aid}_{kind}_"):
            return os.path.join(d, f)
    return None


def _new_mat(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt


def _coords(nt, scale, mode="OBJECT"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale) if not isinstance(scale, (tuple, list)) else scale
    src = {"OBJECT": "Object", "GENERATED": "Generated", "UV": "UV"}[mode]
    nt.links.new(tc.outputs[src], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def _tex(nt, vec, path, noncolor, box=True):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = _img(path, noncolor)
    if box:
        t.projection = "BOX"
        t.projection_blend = 0.25
    nt.links.new(vec, t.inputs["Vector"])
    return t


def pbr(name, aid, scale=1.0, tint=None, tint_mix=1.0, rough=(0.0, 1.0), metal=0.0, nstr=1.0, coat=0.0,
        coat_rough=0.1, spec=0.5, mode="OBJECT", base=None, extra=None, ior=1.5):
    """Principled material from a Poly Haven set. scale = repeats per metre (Object coords, box projection).
    tint: RGB multiplied over the albedo (mixed by tint_mix; base replaces it). rough: remap (lo, hi) of the roughness map."""
    m, nt = _new_mat(name)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    vec = _coords(nt, scale, mode)
    dif = ph_map(aid, "diff")
    if dif:
        td = _tex(nt, vec, dif, False, box=(mode != "UV"))
        col = td.outputs["Color"]
        if base is not None:
            # keep the map's luminance variation around a chosen base colour
            bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(col, bw.inputs[0])
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.6
            mr.inputs["To Min"].default_value = 1 - tint_mix * 0.5; mr.inputs["To Max"].default_value = 1 + tint_mix * 0.5
            nt.links.new(bw.outputs[0], mr.inputs["Value"])
            mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
            mul.inputs["Factor"].default_value = 1.0
            mul.inputs["A"].default_value = (*base, 1)
            nt.links.new(mr.outputs[0], mul.inputs["B"])
            col = mul.outputs["Result"]
        elif tint is not None:
            mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
            mul.inputs["Factor"].default_value = tint_mix
            nt.links.new(col, mul.inputs["A"]); mul.inputs["B"].default_value = (*tint, 1)
            col = mul.outputs["Result"]
        nt.links.new(col, b.inputs["Base Color"])
    elif base is not None:
        b.inputs["Base Color"].default_value = (*base, 1)
    rp = ph_map(aid, "rough")
    if rp:
        tr = _tex(nt, vec, rp, True, box=(mode != "UV"))
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = rough
        nt.links.new(tr.outputs["Color"], mr.inputs["Value"])
        nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = sum(rough) / 2
    npth = ph_map(aid, "nor_gl")
    if npth and nstr > 0:
        tn = _tex(nt, vec, npth, True, box=(mode != "UV"))
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = nstr
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])
        if coat > 0:
            pass  # coat stays smooth (lacquer over grain)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rough
    b.inputs["IOR"].default_value = ior
    b.inputs["Specular IOR Level"].default_value = spec
    if extra:
        extra(nt, b, vec)
    m["look"] = f"pbr:{aid}"
    return m


def emissive(name, color, strength, base=(0.02, 0.02, 0.02), rough=0.2):
    """For real lights only (screens, LEDs, bulbs, lit windows, fire)."""
    m, nt = _new_mat(name)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    m["look"] = "light"
    return m


def glass(name, rough_lo=0.0, rough_hi=0.12, smudge_scale=1.2, tint=(1, 1, 1), ior=1.5):
    """Clear glass with a smudge roughness map (procedural noise over a grunge map)."""
    m, nt = _new_mat(name)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = ior
    vec = _coords(nt, smudge_scale)
    g = _tex(nt, vec, ph_map("metal_plate_02", "rough"), True)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
    nt.links.new(vec, nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY"
    nt.links.new(g.outputs["Color"], mx.inputs[0]); nt.links.new(nz.outputs["Fac"], mx.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.15; mr.inputs["From Max"].default_value = 0.6
    mr.inputs["To Min"].default_value = rough_lo; mr.inputs["To Max"].default_value = rough_hi
    nt.links.new(mx.outputs[0], mr.inputs["Value"])
    nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "DITHERED"
    try:
        m.use_raytrace_refraction = True
    except Exception:
        pass
    m["look"] = "glass"
    return m


def assign(ob, mat, all_slots=True):
    if ob.type not in ("MESH", "CURVE", "FONT", "SURFACE", "META"):
        return
    if not ob.data.materials:
        ob.data.materials.append(mat)
    else:
        for i in range(len(ob.data.materials)):
            ob.data.materials[i] = mat
            if not all_slots:
                break
    for s in ob.material_slots:
        if s.link == "OBJECT":
            s.material = mat


def apply_scale(ob):
    """So Object-space texture coords keep a true metre scale on scaled boxes (static, single-user meshes only)."""
    if ob.type != "MESH" or ob.data.users > 1 or ob.animation_data:
        return False
    s = ob.scale
    if abs(s.x - 1) + abs(s.y - 1) + abs(s.z - 1) < 1e-4:
        return False
    if ob.children:
        return False
    from mathutils import Matrix
    ob.data.transform(Matrix.Diagonal((s.x, s.y, s.z, 1.0)))
    ob.scale = (1, 1, 1)
    return True


def light(name, kind, loc, energy, color=(1, 1, 1), size=0.1, rot=None, spot=None, blend=0.3, dist=None,
          shadow=True, soft=0.05, temp=None, coll=None, volume=1.0):
    ob = bpy.data.objects.get(name)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    if temp:
        ld.use_temperature = True
        ld.temperature = temp
    ld.color = color
    ld.use_shadow = shadow
    ld.volume_factor = volume
    if kind == "AREA":
        ld.shape = "RECTANGLE"
        if isinstance(size, (tuple, list)):
            ld.size, ld.size_y = size
        else:
            ld.size = ld.size_y = size
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = soft
    if kind == "SPOT" and spot:
        ld.spot_size = math.radians(spot)
        ld.spot_blend = blend
    if dist:
        ld.use_custom_distance = True
        ld.cutoff_distance = dist
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    if rot:
        ob.rotation_euler = [math.radians(a) for a in rot]
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def box(name, mn, mx, mat=None, coll=None, bevel=0.0):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector([(mn[i] + mx[i]) / 2 + v.co[i] * (mx[i] - mn[i]) for i in range(3)])
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    if mat:
        me.materials.append(mat)
    if bevel > 0:
        md = ob.modifiers.new("bevel", "BEVEL"); md.width = bevel; md.segments = 2; md.limit_method = "ANGLE"
    return ob


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def render_settings(sc, samples=64, mb_steps=8, final=True, res=(1080, 1920)):
    r = sc.render
    r.engine = "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.fps, r.fps_base = 24, 1.0
    e = sc.eevee
    e.taa_render_samples = samples
    e.use_raytracing = True
    e.ray_tracing_method = "SCREEN"
    o = e.ray_tracing_options
    o.resolution_scale = "1"
    o.trace_max_roughness = 0.6
    try:
        o.use_denoise = True
    except Exception:
        pass
    e.use_fast_gi = True
    e.fast_gi_method = "GLOBAL_ILLUMINATION"
    e.fast_gi_resolution = "2"
    e.fast_gi_ray_count = 2
    e.fast_gi_step_count = 8
    e.fast_gi_distance = 2.0
    e.use_shadows = True
    e.shadow_pool_size = "2048"   # "Shadow buffer full" at 512 in the busy sets; f461 512 vs 2048: noise-level diff
    e.shadow_ray_count = 2
    e.shadow_step_count = 8
    e.shadow_resolution_scale = 1.0
    e.use_volumetric_shadows = True
    e.volumetric_tile_size = "4"
    e.volumetric_samples = 96
    e.volumetric_shadow_samples = 32
    e.volumetric_light_clamp = 0.0
    e.volumetric_ray_depth = 8
    e.clamp_surface_indirect = 10.0
    e.gi_diffuse_bounces = 3
    e.light_threshold = 0.004
    e.bokeh_max_size = 100
    e.use_overscan = True
    e.overscan_size = 3.0
    # true motion blur from shutter samples: 180 deg (half the frame interval), shutter opens AT the frame, so a
    # camera cut keyed constant on frame k never mixes the shots on either side (rendering skill: reset at cuts).
    r.use_motion_blur = final
    r.motion_blur_shutter = 0.5
    r.motion_blur_position = "START"
    e.motion_blur_steps = mb_steps
    e.motion_blur_max = 64
    r.film_transparent = False
    r.filter_size = 1.3
    r.use_compositing = True
    # renders are scene-linear half-float EXR (multilayer: the composite + the object-index pass for the measuring
    # masks); the grade (tone curve, exposure, toe) is a separate step, so exposure notes never need a re-render (CD 13.4)
    try:
        r.image_settings.media_type = "MULTI_LAYER_IMAGE"   # Blender 5.x
    except Exception:
        pass
    r.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    r.image_settings.color_depth = "16"
    r.image_settings.exr_codec = "ZIP"
    r.use_compositing = False   # the grade (tools/grade.py) does the halation
    vs = sc.view_settings
    sc.display_settings.display_device = "sRGB"
    # Filmic, not AgX: AgX pushes Claude's saturated orange to salmon pink on rendered pixels (f860 test: AgX MHC head
    # median RGB 255,150,122; Filmic MHC 239,134,21; approved design 213,109,62). CREATIVE 10.6 L3.
    vs.view_transform = "Filmic"
    vs.look = "Medium High Contrast"
    vs.exposure = 0.0
    vs.gamma = 1.0
    sc.sequencer_colorspace_settings.name = "sRGB" if "sRGB" in [i.identifier for i in bpy.types.ColorManagedSequencerColorspaceSettings.bl_rna.properties["name"].enum_items] else sc.sequencer_colorspace_settings.name


def halation_compositor(sc, threshold=1.6, mix=-0.86, size=6):
    """Light halation on practicals only: a bloom whose threshold sits above every lit surface, so only light sources
    (screens, bulbs, fire, LEDs) bloom. Warm-tinted, very low mix."""
    ng = bpy.data.node_groups.new("AFF_short_comp", "CompositorNodeTree")
    sc.compositing_node_group = ng
    n = ng.nodes
    rl = n.new("CompositorNodeRLayers")
    gl = n.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Bloom"
    gl.inputs["Quality"].default_value = "High"
    # 5.x exposes glare parameters as inputs
    def setin(node, key, val):
        if key in node.inputs:
            node.inputs[key].default_value = val
            return True
        return False
    setin(gl, "Threshold", threshold)
    setin(gl, "Strength", 0.12)
    setin(gl, "Size", 0.55)
    setin(gl, "Saturation", 1.0)
    if "Tint" in gl.inputs:
        gl.inputs["Tint"].default_value = (1.0, 0.82, 0.70, 1.0)
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    out = n.new("NodeGroupOutput")
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs["Image"], out.inputs[0])
    return ng


def emission_census():
    """Every material that emits, with its strength (look-and-light Verify)."""
    rows = []
    for m in bpy.data.materials:
        if not (m.use_nodes and m.node_tree) or m.users == 0:
            continue
        s = 0
        for nd in m.node_tree.nodes:
            if nd.type == "EMISSION":
                s = max(s, nd.inputs["Strength"].default_value)
            if nd.type == "BSDF_PRINCIPLED":
                if nd.inputs["Emission Strength"].default_value > 0 and tuple(nd.inputs["Emission Color"].default_value)[:3] != (0, 0, 0):
                    s = max(s, nd.inputs["Emission Strength"].default_value)
        if s > 0:
            rows.append((m.name, round(s, 3), m.get("look", "?"), m.users))
    return rows


def light_census():
    return [(o.name, o.data.type, round(o.data.energy, 2), o.data.cutoff_distance if o.data.use_custom_distance else None,
             tuple(round(x, 2) for x in o.location), o.hide_render) for o in bpy.data.objects if o.type == "LIGHT"]


def finalize_paths():
    """Portable: fonts packed into the blend, every other path relative ('//...'), so the file renders the same on another
    machine or folder (preflight: no ABSOLUTE lines)."""
    for f in bpy.data.fonts:
        if f.packed_file is None and f.filepath and not f.filepath.startswith("<"):
            try:
                f.pack()
            except Exception as ex:
                log("font pack failed", f.name, ex)
    bpy.ops.file.make_paths_relative()
    for d in bpy.data.objects:
        for m in d.modifiers:
            if m.type == "FLUID" and m.fluid_type == "DOMAIN":
                cd = m.domain_settings.cache_directory
                if not cd.startswith("//"):
                    m.domain_settings.cache_directory = bpy.path.relpath(cd)
    log("paths made relative; fonts packed")


def shadow_transparent(mat):
    """Eevee ignores the object 'shadow' visibility toggle, so a bulb around its own light (or the glass in front of the
    fire) blacks the light out. Make the material transparent to shadow rays only: mix(surface, transparent, Is Shadow
    Ray), with transparent shadows on. Camera and reflections still see the surface."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    link = next((l for l in nt.links if l.to_socket == out.inputs["Surface"]), None)
    if link is None or mat.get("shadow_transparent"):
        return
    src = link.from_socket
    lp = nt.nodes.new("ShaderNodeLightPath"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0]); nt.links.new(src, mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    mat.use_transparent_shadow = True
    if mat.surface_render_method != "BLENDED":
        mat.surface_render_method = "DITHERED"
    mat["shadow_transparent"] = True


def shadow_transparent_all():
    n = 0
    for m in bpy.data.materials:
        if m.library is None and m.use_nodes and m.get("look") in ("light", "glass", "light (lit windows)"):
            shadow_transparent(m); n += 1
    log("shadow-transparent materials (bulbs, screens, LEDs, glass):", n)


def thin_glass(name, smudge_scale=1.2, rough_lo=0.02, rough_hi=0.12):
    """A glass partition as a thin pane: reflection by Fresnel over a transparent pass-through, blended. Eevee's
    refracting glass doesn't show volumes behind it (the fire and smoke vanished behind the partition); a thin pane
    has no refraction to speak of anyway. Shadow-transparent."""
    m, nt = _new_mat(name)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vec = _coords(nt, smudge_scale)
    g = _tex(nt, vec, ph_map("metal_plate_02", "rough"), True)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
    nt.links.new(vec, nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY"
    nt.links.new(g.outputs["Color"], mx.inputs[0]); nt.links.new(nz.outputs["Fac"], mx.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.15; mr.inputs["From Max"].default_value = 0.6
    mr.inputs["To Min"].default_value = rough_lo; mr.inputs["To Max"].default_value = rough_hi
    nt.links.new(mx.outputs[0], mr.inputs["Value"])
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(mr.outputs[0], gl.inputs["Roughness"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.92, 0.95, 0.94, 1)
    fr = nt.nodes.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs[0], mix.inputs[0]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    m.use_transparent_shadow = True
    m["look"] = "glass"
    return m


def fcurves_of(idblock):
    """All F-curves of an ID's action (Blender 5 layered actions, or the old flat list)."""
    ad = idblock.animation_data
    if not (ad and ad.action):
        return []
    out = []
    try:
        for lay in ad.action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    out += list(cb.fcurves)
    except AttributeError:
        out = list(getattr(ad.action, "fcurves", []))
    return out
