"""wheels.py (fix_wheels, Sat Nov 7): exec'd right after plate.py by render_final.py, render_stills.py and
more_car_shots/shots.py (never saved into a .blend). WHEELS=0 turns all of it off (the old wheels).
Her f1877 S048 note + her call "keep that then" = realistic: the yellow calipers stay fixed (they sit on the body, not on
the wheel pivots); the wheels must READ as spinning. Three parts:
 1. SPIN = GROUND SPEED. Every wheel_piv_* spin (local X, the only keyed channel) is re-keyed from the car's own travel:
    angle(t) = s(t) / R, s = distance the wheel centre has moved along the car's forward axis (car front = local -y),
    R = 0.3398 m (tyre tread radius, measured), sampled every 1/4 frame, LINEAR keys. Measured before: post1 (S045-48,
    S103b) spun 0.72-3.3x the speed (52x at S045's start), S049 0.76x; v1road and outro were already right (1.014).
    Direction unchanged (top of the tyre moves forward, checked). Parked beats (shots.py garage/posted) clear these keys
    afterwards, so they stay parked.
 2. SMOOTH RADIAL SMEAR. Eevee accumulation motion blur: steps 4 -> WHEEL_MB_STEPS (default 24) so the rim is drawn at
    24 rotations inside the shutter (<= 4 deg apart at 100 deg/frame) instead of 4 ghosts; motion_blur_max 32 -> 96 px.
    The rim has 10 spokes (36 deg apart): at 24 fps a spoke pattern only stops strobing when the smear arc
    (deg/frame x shutter) covers a spoke gap, v1road gets 1.0 (= what S023/S024 already use); post1/more_car
    keep 0.75 (smear 39-80 deg > 36 everywhere they move fast); outro keeps 0.6 (1.0 blurred the body). WHEEL_SHUTTER=x forces one. SHUTTER env in render_final.py still wins (it is applied after this).
 3. TYRE THAT ROLLS. The tyre was a plain black ring (nothing to blur, so nothing reads as rolling). WHEEL_SIDEWALL=1
    (default) gives each tyre a near-black rubber sidewall with a fine rib ring near the rim and raised generic marking
    blocks in two lettering-like arcs (no brand, no text): still = real tyre detail; spinning = soft grey rings.
Calipers, paint, plate and grade are not touched."""
import bpy, os, math
from mathutils import Vector, Matrix, Euler

def _wfc(action):
    fcs = getattr(action, "fcurves", None)
    if fcs is not None and len(fcs): return list(fcs)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out

def _w_fix():
    sc = bpy.context.scene; car = bpy.data.objects.get("CAR_ROOT")
    pivs = [o for o in bpy.data.objects if o.name.startswith("wheel_piv_") and o.parent is not None]
    if not car or not pivs: print("[wheels] no CAR_ROOT / wheel pivots, skipped"); return
    R = float(os.environ.get("WHEEL_R", "0.3398"))
    blend = os.path.basename(bpy.data.filepath)
    # ---- 1. spin from travel ----
    ad = car.animation_data
    if ad and ad.action and not (car.parent or car.constraints):
        fcs = _wfc(ad.action)
        if fcs:
            rng = [k.co.x for fc in fcs for k in fc.keyframe_points]
            for p in pivs:
                if p.animation_data and p.animation_data.action:
                    rng += [k.co.x for fc in _wfc(p.animation_data.action) for k in fc.keyframe_points]
            f0, f1 = int(math.floor(min(rng))) - 12, int(math.ceil(max(rng))) + 12
            f0 = min(f0, sc.frame_start - 2); f1 = max(f1, sc.frame_end + 2)
            if f1 - f0 > 4000: f0, f1 = sc.frame_start - 12, sc.frame_end + 12
            base = {(fc.data_path, fc.array_index): fc for fc in fcs}
            L0, R0, S0 = car.location.copy(), car.rotation_euler.copy(), car.scale.copy()
            def car_mat(t):
                loc = Vector([base[("location", i)].evaluate(t) if ("location", i) in base else L0[i] for i in range(3)])
                rot = Euler([base[("rotation_euler", i)].evaluate(t) if ("rotation_euler", i) in base else R0[i] for i in range(3)], car.rotation_mode if car.rotation_mode in ("XYZ","XZY","YXZ","YZX","ZXY","ZYX") else "XYZ")
                scl = Vector([base[("scale", i)].evaluate(t) if ("scale", i) in base else S0[i] for i in range(3)])
                return Matrix.LocRotScale(loc, rot, scl)
            # verify the fcurve evaluation against Blender's own at 3 frames (delta transforms / drivers would break it)
            ok = True
            for t in (f0 + 12, (f0 + f1) // 2, f1 - 12):
                sc.frame_set(t); d = (car.matrix_world.translation - car_mat(t).translation).length
                if d > 1e-3: ok = False; print("[wheels] car matrix mismatch", t, round(d, 4))
            if ok:
                for p in pivs:
                    a = (p.rotation_euler[0] if not (p.animation_data and p.animation_data.action) else
                         next((fc.evaluate(f0) for fc in _wfc(p.animation_data.action) if fc.data_path == "rotation_euler" and fc.array_index == 0), p.rotation_euler[0]))
                    loc_p = (p.matrix_parent_inverse @ p.matrix_basis).translation.copy()   # pivot centre in car space (spin does not move it)
                    p.animation_data_clear()
                    N = 4; prev = car_mat(f0) @ loc_p; keys = [(f0, a)]
                    for i in range(1, (f1 - f0) * N + 1):
                        t = f0 + i / N; M = car_mat(t); c = M @ loc_p
                        fwd = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
                        a += (c - prev).dot(fwd) / R; prev = c
                        keys.append((t, a))
                    p.rotation_euler[0] = keys[0][1]; p.keyframe_insert("rotation_euler", index=0, frame=keys[0][0])
                    act = p.animation_data.action
                    fc = next(fc for fc in _wfc(act) if fc.data_path == "rotation_euler" and fc.array_index == 0)
                    fc.keyframe_points.add(len(keys) - 1)
                    for kp, (t, v) in zip(list(fc.keyframe_points)[1:], keys[1:]): kp.co = (t, v)
                    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
                    fc.update()
                print(f"[wheels] spin re-keyed from travel f{f0}-{f1} R={R} ({len(pivs)} wheels, {blend})", flush=True)
    # ---- 2. motion blur ----
    r = sc.render; ee = sc.eevee
    steps = int(os.environ.get("WHEEL_MB_STEPS", "24"))
    for o, k in ((r, "motion_blur_steps"), (ee, "motion_blur_steps")):
        if hasattr(o, k): setattr(o, k, max(getattr(o, k), steps))
    if hasattr(ee, "motion_blur_max"): ee.motion_blur_max = max(ee.motion_blur_max, int(os.environ.get("WHEEL_MB_MAX", "96")))
    r.use_motion_blur = True
    # v1road (S023/S024) already renders at 1.0 (clips_3b wheel test, in the master). The outro stays at its approved 0.6:
    # 1.0 smeared the car BODY in S141 (static camera, test Sat 16:30) and its wheels are small / seen from behind.
    # post1 (S045-S048): cameras ride the car, so 1.0 only lengthens the spoke smear (test Sat 16:40: body unchanged,
    # background +1/255): at 1.0 the smear equals the turn, so the 36/72/108 deg "frozen" speeds S045 accelerates through
    # blur the spokes out instead of freezing them. more_car (S103b, 89-107 deg/frame) keeps 0.75 (garage door blur shares the blend).
    SH = {"car_v1road": 1.0, "car_post1": 1.0}
    want = float(os.environ["WHEEL_SHUTTER"]) if os.environ.get("WHEEL_SHUTTER") else next((v for k, v in SH.items() if blend.startswith(k)), 0.0)
    if want > r.motion_blur_shutter: r.motion_blur_shutter = want
    print(f"[wheels] motion blur steps {steps} max {getattr(ee, 'motion_blur_max', '-')} shutter {round(r.motion_blur_shutter, 2)}", flush=True)
    # ---- 3. sidewall ----
    if os.environ.get("WHEEL_SIDEWALL", "1") == "1":
        for p in pivs:
            ty = next((c for c in p.children if c.type == "MESH" and c.name.startswith("tyre")), None)
            if not ty or not ty.material_slots or not ty.material_slots[0].material: continue
            src = ty.material_slots[0].material
            m = src.copy(); m.name = "WHEEL_tyre_" + p.name[-2:]; nt = m.node_tree
            b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            tc = nt.nodes.new("ShaderNodeTexCoord"); tc.object = p
            sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
            def M(op, a, bb=None, v=None):
                n = nt.nodes.new("ShaderNodeMath"); n.operation = op
                for i, x in enumerate((a, bb)):
                    if x is None: continue
                    if isinstance(x, (int, float)): n.inputs[i].default_value = x
                    else: nt.links.new(x, n.inputs[i])
                return n.outputs[0]
            y, z = sep.outputs["Y"], sep.outputs["Z"]
            rad = M("SQRT", M("ADD", M("MULTIPLY", y, y), M("MULTIPLY", z, z)))
            ang = M("ARCTAN2", z, y)                                      # -pi..pi around the spin axis
            # rib ring just outside the rim lip (tyre r .266-.340, rim covers to .275): 90 fine radial ribs
            ribs = M("GREATER_THAN", M("SINE", M("MULTIPLY", ang, 90.0)), 0.2)
            ring = M("MULTIPLY", M("GREATER_THAN", rad, 0.281), M("LESS_THAN", rad, 0.291))
            # raised marking blocks (r .298-.318): two ~50 deg arcs on opposite sides (where a real tyre carries its
            # lettering), uneven letter-width blocks from two incommensurate sines; generic, no text, no brand
            grp = M("GREATER_THAN", M("SINE", M("MULTIPLY", ang, 2.0)), 0.6)
            blk = M("GREATER_THAN", M("ADD", M("SINE", M("MULTIPLY", ang, 97.0)), M("MULTIPLY", M("SINE", M("MULTIPLY", ang, 41.0)), 0.6)), 0.1)
            band = M("MULTIPLY", M("GREATER_THAN", rad, 0.298), M("LESS_THAN", rad, 0.318))
            mark = M("MAXIMUM", M("MULTIPLY", ribs, ring), M("MULTIPLY", M("MULTIPLY", grp, blk), band))
            # raised rubber: a touch lighter, a lot glossier (catches the sun), never grey paint
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
            nt.links.new(mark, mix.inputs["Factor"])
            bc = b.inputs["Base Color"].default_value
            sv = float(os.environ.get("WHEEL_SIDEWALL_V", "0.05"))
            mix.inputs["A"].default_value = tuple(bc); mix.inputs["B"].default_value = (sv, sv, sv * 1.04, 1)
            nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
            rr = M("ADD", M("MULTIPLY", mark, -0.33), b.inputs["Roughness"].default_value)
            nt.links.new(rr, b.inputs["Roughness"])
            bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6; bump.inputs["Distance"].default_value = 0.002
            nt.links.new(mark, bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
            ty.material_slots[0].link = "OBJECT"; ty.material_slots[0].material = m
        print("[wheels] sidewall detail on", len(pivs), "tyres", flush=True)

def _w_glint():
    """4. WHEEL GLINT (WHEEL_GLINT=1; default OFF, rejected in the tests: lip ring): one small specular-led area light per wheel, outboard and low, parented to
    the car and LIGHT-LINKED to the rims + tyres only (body, calipers, road untouched). Motivated by the sunlit road/sky
    bounce; it gives the metallic spokes and the sidewall ribs something to reflect, so the spin smear shows bright circular
    arcs (the 'rolling shot' read) instead of a dark uniform disc. Strength WHEEL_GLINT_E (W, default 3); WHEEL_GLINT_TYRE=1 links the tyres too."""
    car = bpy.data.objects.get("CAR_ROOT"); sc = bpy.context.scene
    pivs = [o for o in bpy.data.objects if o.name.startswith("wheel_piv_") and o.parent is car]
    if not car or not pivs: return
    rx = bpy.data.collections.new("WHEEL_GLINT_RX")
    for p in pivs:
        for c in p.children:
            if c.type == "MESH" and (c.name.startswith("rim") or (c.name.startswith("tyre") and os.environ.get("WHEEL_GLINT_TYRE") == "1")): rx.objects.link(c)
    E = float(os.environ.get("WHEEL_GLINT_E", "3"))
    for p in pivs:
        lp = (p.matrix_parent_inverse @ p.matrix_basis).translation.copy()
        out = 1.0 if lp.x > 0 else -1.0
        # high and forward of each wheel, only a little outboard: the rim lip (a torus) reflects it as a short arc at the
        # top-front, not a full ring; the spokes catch it in one sector, which the spin smears into bright arcs there
        pos = lp + Vector((out * 0.55, -0.55, 0.62))
        d = bpy.data.lights.new("WHEEL_glint_" + p.name[-2:], "AREA"); d.energy = E; d.size = 0.25; d.color = (1.0, 0.93, 0.84)
        d.diffuse_factor = 0.1; d.specular_factor = 1.0; d.volume_factor = 0.0
        o = bpy.data.objects.new(d.name, d); sc.collection.objects.link(o); o.parent = car
        o.location = pos; o.rotation_euler = (lp - pos).to_track_quat("-Z", "Y").to_euler()
        try: o.light_linking.receiver_collection = rx
        except Exception as e: print("[wheels] glint link failed", e)
    print(f"[wheels] glint lights {len(pivs)} x {E} W, linked to {len(rx.objects)} rim/tyre objects", flush=True)

if os.environ.get("WHEELS", "1") != "0":
    _w_fix()
    if os.environ.get("WHEEL_GLINT", "0") == "1": _w_glint()   # tried Sat 16:20, OFF: any light the rims see draws a full chrome ring on the lip (look change)
    if os.environ.get("WHEELS2", "0") == "1":   # fix_wheels2 (Sat 17:xx): road bounce on the spoke faces + one sidewall marking; OFF until approved
        exec(open(os.path.join(os.environ.get("AFF_SONG", "songs/asking-for-a-friend"), "finish", "car", "wheels2.py")).read())   # AFF_SONG: shots.py lives in another folder
else:
    print("[wheels] WHEELS=0: old wheels", flush=True)
