"""wheels2.py (fix_wheels2, Sat Nov 7): exec'd at the end of wheels.py when WHEELS2=1 (default OFF until she approves).
fix_wheels made the spin right; at phone size the near wheels in S048 still read as a uniform dark disc (in the car's own
shade) and the fixed yellow caliper looks "stuck" because nothing visible turns around it. Realistic fix, calipers untouched:
 A. ROAD BOUNCE. A real wheel on a sunlit road gets its face lit from below by the bright asphalt; a flat outward-facing
    spoke face seen by a camera a little higher reflects exactly that patch of road. One soft area light per wheel, low and
    outboard at road level, LIGHT-LINKED to the spoke face + tyre only. The rim is split at r=WHEEL2_LIP (0.226 m) into the
    spoke face and the lip; the lip is NOT linked, so no chrome ring (the fault of fix_wheels' glint test).
 B. ONE SIDEWALL MARKING. fix_wheels' two lettering arcs sit 180 deg apart, so at 106 deg/frame they can read as -74 deg
    (backwards) once visible. Now one ~70 deg lettering arc (generic letter blocks, no text, no brand) plus a small code
    block 140 deg away: one dominant feature, so the eye follows it forward; at speed it smears into a grey arc that jumps
    ahead every frame (the rolling read), slow it reads as tyre lettering.
Env: WHEEL2_E (W per wheel), WHEEL2_SIZE, WHEEL2_OUT/WHEEL2_Z (m from the hub), WHEEL2_MARK_V (marking albedo),
WHEEL2_MARK_RGB "r,g,b" overrides it, WHEEL2_BOUNCE=0 / WHEEL2_MARK=0 turn a part off."""
import bpy, os, math, bmesh
from mathutils import Vector

def _w2():
    sc = bpy.context.scene; car = bpy.data.objects.get("CAR_ROOT")
    pivs = [o for o in bpy.data.objects if o.name.startswith("wheel_piv_") and o.parent is not None]
    if not car or not pivs: print("[wheels2] no car/pivots, skipped"); return
    blend = os.path.basename(bpy.data.filepath)
    LIP = float(os.environ.get("WHEEL2_LIP", "0.226")); HUB = float(os.environ.get("WHEEL2_HUB", "0.065"))
    rx = bpy.data.collections.new("WHEEL2_RX"); rt = bpy.data.collections.new("WHEEL2_RT")   # spoke faces / tyres
    # ---- split each rim into face + lip ----
    for p in pivs:
        rim = next((c for c in p.children if c.type == "MESH" and c.name.startswith("rim")), None)
        ty = next((c for c in p.children if c.type == "MESH" and c.name.startswith("tyre")), None)
        if rim is None: continue
        M = p.matrix_world.inverted() @ rim.matrix_world
        parts = {}
        for tag in ("_lip", "_hub"):
            o2 = rim.copy(); o2.data = rim.data.copy(); o2.name = rim.name + tag
            for col in rim.users_collection: col.objects.link(o2)
            o2.parent = p; o2.matrix_parent_inverse = rim.matrix_parent_inverse.copy(); o2.matrix_basis = rim.matrix_basis.copy()
            parts[tag] = o2
        rim.data = rim.data.copy()
        # the face keeps HUB <= r < LIP; the lip (r >= LIP) and the centre lock (r < HUB) are not lit by the bounce:
        # the lip would draw a chrome ring, the polished centre lock blows out to a white dot that stands still
        for ob, lo, hi in ((rim, HUB, LIP), (parts["_lip"], LIP, 9.0), (parts["_hub"], -1.0, HUB)):
            bm = bmesh.new(); bm.from_mesh(ob.data)
            dead = []
            for f in bm.faces:
                q = M @ f.calc_center_median(); r = math.hypot(q.y, q.z)
                if not (lo <= r < hi): dead.append(f)
            bmesh.ops.delete(bm, geom=dead, context="FACES"); bm.to_mesh(ob.data); bm.free()
        rx.objects.link(rim)
        if ty is not None: rt.objects.link(ty)
    # ---- bounce lights ----
    if os.environ.get("WHEEL2_BOUNCE", "1") == "1":
        E = float(os.environ.get("WHEEL2_E", "22")); ET = float(os.environ.get("WHEEL2_ET", "7")); S = float(os.environ.get("WHEEL2_SIZE", "1.0"))
        OUT = float(os.environ.get("WHEEL2_OUT", "0.9")); Z = float(os.environ.get("WHEEL2_Z", "-0.30"))
        for p in pivs:
            lp = (p.matrix_parent_inverse @ p.matrix_basis).translation.copy()
            if p.parent is not car:   # pivots under another parent: express in car space
                lp = car.matrix_world.inverted() @ p.matrix_world.translation
            out = 1.0 if lp.x > 0 else -1.0
            pos = lp + Vector((out * OUT, 0.0, Z)); aim = lp + Vector((out * 0.12, 0.0, 0.0))
            for tag, en, coll in (("face", E, rx), ("tyre", ET, rt)):   # one light each: the tyre needs far less (a lit tyre goes whitewall)
                if en <= 0: continue
                d = bpy.data.lights.new(f"WHEEL2_bounce_{tag}_" + p.name[-2:], "AREA"); d.energy = en; d.size = S
                d.color = (0.92, 0.94, 1.0) if blend.startswith("car_more") else (1.0, 0.86, 0.72)   # night road lamps: neutral; golden hour asphalt: warm
                d.volume_factor = 0.0
                d.use_shadow = False   # 8 shadowed lights overflowed Eevee's shadow pool (2457/2048) in S045/S047 and cost +70%; a road bounce from below has nothing in its way
                o = bpy.data.objects.new(d.name, d); sc.collection.objects.link(o); o.parent = car
                o.location = pos; o.rotation_euler = (aim - pos).to_track_quat("-Z", "Y").to_euler()
                try: o.light_linking.receiver_collection = coll
                except Exception as e: print("[wheels2] link failed", e)
        print(f"[wheels2] bounce {len(pivs)} wheels: face {E} W, tyre {ET} W, size {S} out {OUT} z {Z}; lip r>={LIP} and hub r<{HUB} unlit", flush=True)
    # ---- one dominant sidewall marking ----
    if os.environ.get("WHEEL2_MARK", "1") == "1":
        v = float(os.environ.get("WHEEL2_MARK_V", "0.22"))
        rgb = tuple(float(x) for x in os.environ["WHEEL2_MARK_RGB"].split(",")) if os.environ.get("WHEEL2_MARK_RGB") else (v, v, v * 1.03)
        n = 0
        for p in pivs:
            ty = next((c for c in p.children if c.type == "MESH" and c.name.startswith("tyre")), None)
            if not ty or not ty.material_slots: continue
            m = ty.material_slots[0].material
            if not m or not m.name.startswith("WHEEL_tyre_"): continue
            nt = m.node_tree
            mix = next(nd for nd in nt.nodes if nd.type == "MIX" and nd.data_type == "RGBA")
            b = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED"); bump = next(nd for nd in nt.nodes if nd.type == "BUMP")
            tc = nt.nodes.new("ShaderNodeTexCoord"); tc.object = p
            sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
            def Mth(op, a, bb=None):
                nd = nt.nodes.new("ShaderNodeMath"); nd.operation = op
                for i, x in enumerate((a, bb)):
                    if x is None: continue
                    if isinstance(x, (int, float)): nd.inputs[i].default_value = x
                    else: nt.links.new(x, nd.inputs[i])
                return nd.outputs[0]
            y, z = sep.outputs["Y"], sep.outputs["Z"]
            rad = Mth("SQRT", Mth("ADD", Mth("MULTIPLY", y, y), Mth("MULTIPLY", z, z)))
            ang = Mth("ARCTAN2", z, y)
            ribs = Mth("GREATER_THAN", Mth("SINE", Mth("MULTIPLY", ang, 90.0)), 0.2)
            ring = Mth("MULTIPLY", Mth("GREATER_THAN", rad, 0.281), Mth("LESS_THAN", rad, 0.291))
            # lettering arc: ang in (-0.61, 0.61) rad (70 deg), letter blocks from two incommensurate sines, tall band
            arc = Mth("LESS_THAN", Mth("ABSOLUTE", ang), 0.61)
            blk = Mth("GREATER_THAN", Mth("ADD", Mth("SINE", Mth("MULTIPLY", ang, 97.0)), Mth("MULTIPLY", Mth("SINE", Mth("MULTIPLY", ang, 41.0)), 0.6)), -0.15)
            band = Mth("MULTIPLY", Mth("GREATER_THAN", rad, 0.296), Mth("LESS_THAN", rad, 0.326))
            # small code block ~140 deg away (r .300-.318, 16 deg)
            cod = Mth("LESS_THAN", Mth("ABSOLUTE", Mth("SUBTRACT", ang, 2.44)), 0.14)
            cblk = Mth("GREATER_THAN", Mth("SINE", Mth("MULTIPLY", ang, 160.0)), -0.3)
            cband = Mth("MULTIPLY", Mth("GREATER_THAN", rad, 0.300), Mth("LESS_THAN", rad, 0.318))
            letters = Mth("MULTIPLY", Mth("MULTIPLY", arc, blk), band)
            code = Mth("MULTIPLY", Mth("MULTIPLY", cod, cblk), cband)
            mark = Mth("MAXIMUM", Mth("MAXIMUM", Mth("MULTIPLY", ribs, Mth("MULTIPLY", ring, 0.5)), letters), code)
            nt.links.new(mark, mix.inputs["Factor"]); mix.inputs["B"].default_value = rgb + (1,)
            nt.links.new(mark, bump.inputs["Height"])
            # raised letters: matte (worn rubber), the rest keeps the source roughness
            rr = Mth("ADD", Mth("MULTIPLY", mark, 0.1), 0.75)
            nt.links.new(rr, b.inputs["Roughness"]); n += 1
        print(f"[wheels2] one sidewall marking on {n} tyres, rgb {tuple(round(c,3) for c in rgb)}", flush=True)

_w2()
