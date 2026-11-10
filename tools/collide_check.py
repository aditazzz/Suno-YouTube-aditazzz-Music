"""collide_check.py: objects cutting through each other, checked on the exact scene a render sees (her rule, Nov 7 2026:
"an automatic check run every time a video frame is generated, catching objects cutting through each other (e.g. a donut
box cutting the laptop) and bodies going through furniture").

Two ways to run it (Blender 5.x, headless, CPU only, renders nothing):

1. HOOK / dry render (what tools/gpuq.sh does after every Blender job, and the faithful way to check a shot): put this
   script FIRST and repeat the job's own command. Every bpy.ops.render.render call the job's scripts make becomes a
   check of that frame (write_still = the current frame; animation=True = frame_start..frame_end by COLLIDE_STEP), and a
   CLI -a / -f render is turned into the same by tools/collide_post.py. The scene is exactly what the render would have
   seen: every setup script (look fixes, props added at load time, cameras) has already run.
       COLLIDE_OUT=<out.jsonl> Blender -b X.blend --python tools/collide_check.py --python render3.py ...
2. STANDALONE on a blend (no setup scripts):
       Blender -b X.blend --python tools/collide_check.py -- --frames 900-935,940 [--off 1] [--step 1] --out <out.jsonl>
   --frames are MASTER frames, blend frame = master + --off (default 0); the camera is the scene's after frame_set
   (timeline markers bound to cameras switch it, as in a render).

Env (both modes): COLLIDE_OUT (jsonl, one line per checked frame; required in hook mode), COLLIDE_STEP (animation step,
default 1), COLLIDE_EPS (metres; deeper than this is penetration, shallower is contact; default 0.01), COLLIDE_FOFF
(master = blend frame - FOFF when writing frame numbers; default 0), COLLIDE_RES (render width for pixel sizes; default
the scene's).

Per frame it tests every pair of mesh-like objects (meshes, curves, text; instances included) that the camera can see
(frustum + renderable: hide_render off, ray visibility camera on, collection not render-disabled; evaluated, deformed,
world space) whose bounding boxes overlap, with mathutils.bvhtree.BVHTree.overlap. Pairs meant to touch are skipped:
one is an ancestor of the other, they share a rig (same armature parent/deformer: hands holding props, body parts), or a
constraint ties one to the other. For each remaining pair it reports:
  depth_m   deepest vertex of a crossing triangle that lies INSIDE the other mesh (nearest-surface distance) - contact
            (<= eps) vs cutting through is separable
  depth_px  that depth in pixels at that distance
  vis       fraction of the crossing points the camera actually sees (scene ray cast, first hit is one of the pair)
  where     screen box of the crossing region (normalised 0-1, y down) and its centre
tools/collide_report.py groups the lines into pair x frame-range hits, applies the allowlist and decides pass/fail.
"""
import bpy, os, sys, json, math, time, builtins
_REAL_OPEN = builtins.open
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

EPS = float(os.environ.get("COLLIDE_EPS", "0.01"))
STEP = max(1, int(os.environ.get("COLLIDE_STEP", "1")))
FOFF = int(os.environ.get("COLLIDE_FOFF", "0"))
MESHLIKE = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
DEFORMERS = {"ARMATURE", "MESH_DEFORM", "LATTICE", "HOOK", "SURFACE_DEFORM", "CLOTH", "SOFT_BODY", "NODES", "DISPLACE",
             "WAVE", "SHRINKWRAP", "CAST", "SIMPLE_DEFORM", "CORRECTIVE_SMOOTH", "LAPLACIANDEFORM", "SMOOTH", "OCEAN",
             "DYNAMIC_PAINT", "EXPLODE", "SCREW", "BUILD", "WARP", "MESH_CACHE", "MESH_SEQUENCE_CACHE", "PARTICLE_SYSTEM"}
MAX_V = 600          # crossing-triangle vertices sampled per pair for depth
MAX_VIS = 10         # crossing points ray-cast for visibility
SAMPLES_UV = [(i / 4, j / 4) for i in range(5) for j in range(5 - i)]   # 15 barycentric points per crossing triangle

_geo = {}            # local-space (verts, tris, closed) per static mesh key
_wbvh = {}           # world BVH per (key, matrix) for static objects
_prepared = [False]


def _prepare(sc):
    """Make the (viewport) depsgraph match the render: render visibility, render modifiers, subsurf capped at 1 level."""
    if _prepared[0]:
        return
    _prepared[0] = True
    for c in bpy.data.collections:
        try:
            c.hide_viewport = c.hide_render
        except Exception:
            pass
    for o in sc.objects:
        try:
            o.hide_viewport = o.hide_render
            o.hide_set(False)
        except Exception:
            pass
        for m in getattr(o, "modifiers", []):
            try:
                m.show_viewport = m.show_render
                if m.type == "SUBSURF":
                    m.levels = min(m.render_levels, 1)
                if m.type == "MULTIRES":
                    m.levels = 0
            except Exception:
                pass


def _sync_hide(sc):
    """hide_render can be keyed (props appearing): copy it to hide_viewport for this frame."""
    ch = False
    for o in sc.objects:
        if o.hide_viewport != o.hide_render:
            try:
                o.hide_viewport = o.hide_render; ch = True
            except Exception:
                pass
    return ch


def _rig(o):
    p = o
    while p is not None:
        if p.type == "ARMATURE":
            return p.name
        p = p.parent
    for m in getattr(o, "modifiers", []):
        if m.type == "ARMATURE" and m.object:
            return m.object.name
    return None


def _ancestors(o):
    s, p = set(), o.parent
    while p is not None:
        s.add(p.name); p = p.parent
    return s


def _ctargets(o):
    s = set()
    for c in getattr(o, "constraints", []):
        t = getattr(c, "target", None)
        if t is not None:
            s.add(t.name)
    return s


def _deforming(o):
    if getattr(o.data, "shape_keys", None):
        return True
    if any(m.type in DEFORMERS for m in getattr(o, "modifiers", [])):
        return True
    ad = getattr(o.data, "animation_data", None)
    return bool(ad and (ad.action or ad.drivers))


def _moving(o):
    p = o
    while p is not None:
        ad = p.animation_data
        if (ad and (ad.action or ad.drivers)) or len(getattr(p, "constraints", [])):
            return True
        p = p.parent
    return False


BIG = float(os.environ.get("COLLIDE_BIG", "2.5"))   # metres: two static pieces both this big meeting = set construction


import re as _re
NATURE = _re.compile(os.environ.get("COLLIDE_NATURE", r"(scrub|grass|leaf|leaves|plant|tree|bush|shrub|cact|fern|foliage|flower|weed|ivy|moss|branch|frond|palm|agave|yucca|reed|muhly|sotol|cedar|oak|juniper|hedge|lily|succulent)"), _re.I)
GROUND = _re.compile(os.environ.get("COLLIDE_GROUND", r"(terrain|ground|soil|dirt|road|shoulder|verge|kerb|curb|edge|lawn|gravel|rock|stone|pot|planter|bed|mulch|floor|land|hill|path|drive|court|paver|patio|deck|slab|plaza|asphalt|tarmac|concrete|carpet|rug)"), _re.I)


SURF = _re.compile(os.environ.get("COLLIDE_SURF", r"(terrain|ground|soil|dirt|road|shoulder|verge|kerb|curb|lawn|gravel|mulch|floor|land|hill|path|drive|court|paver|patio|deck|slab|plaza|asphalt|tarmac|concrete|carpet|rug)"), _re.I)


def prefix(n):
    n = n.split(">")[-1]
    return _re.split(r"[_.\- ]", n, maxsplit=1)[0].lower()


def classify(a, b, depth):
    na, nb = a["orig"].name, b["orig"].name
    if (NATURE.search(na) and (NATURE.search(nb) or GROUND.search(nb))) or (NATURE.search(nb) and GROUND.search(na)):
        return "nature"          # vegetation rooted in ground / leaves crossing leaves: how plants are
    if a["root"] and a["root"] == b["root"] and prefix(na) == prefix(nb):
        return "assembly"        # parts of one model (AG1_body + AG1_head, a cabinet + its doors): designed. A chair and the
                                 # body sitting in it share a parent but not a name (CH0_seat / EX0_body): they ARE tested
    if not a["moving"] and not b["moving"] and (SURF.search(na) or SURF.search(nb)):
        return "grounded"        # a static thing set into a static floor/ground/slab: the opaque ground hides what's below
    if not a["moving"] and not b["moving"] and min(a["size"], b["size"]) >= BIG:
        return "construction"    # two static set pieces (wall into wall, floor under wall, city blocks)
    if depth <= EPS:
        return "contact"
    return "penetration"


def _local_geo(ob_eval, key, static):
    """Local-space triangles of a REAL evaluated object (never a temporary from depsgraph.object_instances: those die with
    the iterator and to_mesh_clear on them crashed Blender). Meshes are read straight from the evaluated data."""
    if static and key in _geo:
        return _geo[key]
    tmp = False
    try:
        if ob_eval.type == "MESH":
            me = ob_eval.data
        else:
            me = ob_eval.to_mesh(); tmp = True
    except Exception:
        return None
    try:
        if me is None or not len(me.polygons):
            return None
        verts = [v.co.copy() for v in me.vertices]
        tris = [tuple(t.vertices) for t in me.loop_triangles]
        ecount = {}
        for p in me.polygons:
            for ek in p.edge_keys:
                ecount[ek] = ecount.get(ek, 0) + 1
        closed = bool(ecount) and all(c == 2 for c in ecount.values())
    finally:
        if tmp:
            try:
                ob_eval.to_mesh_clear()
            except Exception:
                pass
    g = (verts, tris, closed)
    if static:
        _geo[key] = g
    return g


def _inside(bvh, closed, p):
    """p inside the mesh: nearest-face normal side; for closed meshes also ray parity (two directions must agree)."""
    loc, nor, idx, dist = bvh.find_nearest(p)
    if loc is None:
        return False, 0.0
    side = (p - loc).dot(nor) < 0
    if not side:
        return False, dist
    if not closed:
        return True, dist
    votes = 0
    for d in (Vector((0.123, 0.456, 0.881)).normalized(), Vector((-0.71, 0.33, -0.62)).normalized()):
        o, n = p.copy(), 0
        for _ in range(24):
            h = bvh.ray_cast(o, d)
            if h[0] is None:
                break
            n += 1; o = h[0] + d * 1e-5
        votes += n % 2
    return votes >= 1, dist


def collect(sc, dg, cam):
    # pixel sizes at the render's width, never below 1920 (a small test render must not hide a cut that shows in the master)
    res_x = int(os.environ.get("COLLIDE_RES", max(1920, sc.render.resolution_x * sc.render.resolution_percentage // 100)))
    res_y = int(res_x * sc.render.resolution_y / max(1, sc.render.resolution_x))
    items = []
    for inst in dg.object_instances:
        ob = inst.object
        if ob.type not in MESHLIKE:
            continue
        orig = ob.original
        owner = inst.parent.original if inst.is_instance and inst.parent else orig
        if owner.hide_render or orig.hide_render and not inst.is_instance:
            continue
        if not getattr(ob, "visible_camera", True):
            continue
        mw = inst.matrix_world.copy()
        corners = [mw @ Vector(c) for c in ob.bound_box]
        # frustum (conservative: anything straddling the camera plane counts as visible)
        pc = [world_to_camera_view(sc, cam, c) for c in corners]
        front = [q for q in pc if q.z > 0]
        if not front:
            continue
        if len(front) == 8:
            xs = [q.x for q in front]; ys = [q.y for q in front]
            if max(xs) < 0 or min(xs) > 1 or max(ys) < 0 or min(ys) > 1:
                continue
        lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        if inst.is_instance and (orig is owner or orig.name not in bpy.data.objects):
            continue                 # geometry made inside a node tree (no real source object): not checked
        src = orig.evaluated_get(dg)  # a real evaluated object, valid after the instance iterator moves on
        if inst.is_instance:
            label = f"{owner.name}>{orig.name}"
            key = ("I", owner.name, orig.name, tuple(inst.persistent_id))
            gkey = ("O", orig.name)
        else:
            label = orig.name
            key = ("O", orig.name)
            gkey = ("O", orig.name)
        static = not _deforming(orig)
        top = owner
        while top.parent is not None:
            top = top.parent
        items.append(dict(ob=src, orig=orig, owner=owner, label=label, key=key, gkey=gkey, mw=mw, lo=lo, hi=hi,
                          static=static, inst=inst.is_instance, root=top.name if top is not orig else None,
                          moving=_moving(owner) or _moving(orig) or not static, size=max(hi - lo),
                          pid=tuple(inst.persistent_id) if inst.is_instance else ()))
    return items, res_x, res_y


def _skip(a, b):
    oa, ob_ = a["orig"], b["orig"]
    if a["inst"] and b["inst"] and a["owner"] is b["owner"]:
        # two parts of the same instanced prefab: identical in every copy; checked once (first copy) via dedupe later
        pass
    na, nb = oa.name, ob_.name
    if na == nb and a["owner"] is b["owner"]:
        return "same"
    A, B = _ancestors(oa) | {na}, _ancestors(ob_) | {nb}
    if na in B or nb in A:
        return "parented"
    if a["owner"] is not oa and (a["owner"].name in B):
        return "parented"
    if b["owner"] is not ob_ and (b["owner"].name in A):
        return "parented"
    ra, rb = _rig(oa), _rig(ob_)
    if ra and ra == rb:
        return "rig"
    ta, tb = _ctargets(oa), _ctargets(ob_)
    if (ta & B) or (tb & A):
        return "constraint"
    return None


def _world_bvh(it):
    g = _local_geo(it["ob"], it["gkey"], it["static"])
    if g is None:
        return None
    verts, tris, closed = g
    mkey = None
    if it["static"]:
        mkey = (it["key"], tuple(round(x, 6) for r in it["mw"] for x in r))
        if mkey in _wbvh:
            return _wbvh[mkey]
    mw = it["mw"]
    wv = [mw @ v for v in verts]
    try:
        bvh = BVHTree.FromPolygons(wv, tris, all_triangles=True)
    except Exception:
        return None
    r = (bvh, wv, tris, closed)
    if mkey is not None:
        if len(_wbvh) > 4000:
            _wbvh.clear()
        _wbvh[mkey] = r
    return r


def check_frame(sc, master_frame=None):
    t0 = time.time()
    _prepare(sc)
    if _sync_hide(sc):
        bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    cam = sc.camera
    if cam is None:
        return dict(frame=master_frame, err="no camera")
    items, rx, ry = collect(sc, dg, cam)
    # sweep-and-prune on x
    order = sorted(range(len(items)), key=lambda i: items[i]["lo"].x)
    cand = []
    active = []
    for i in order:
        a = items[i]
        active = [j for j in active if items[j]["hi"].x + EPS >= a["lo"].x]
        for j in active:
            b = items[j]
            if (a["lo"].y <= b["hi"].y + EPS and b["lo"].y <= a["hi"].y + EPS and
                    a["lo"].z <= b["hi"].z + EPS and b["lo"].z <= a["hi"].z + EPS):
                cand.append((j, i))
        active.append(i)
    camloc = cam.matrix_world.translation
    camright = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    hits, skipped, tested = [], {}, 0
    seen_prefab = set()
    for j, i in cand:
        a, b = items[j], items[i]
        why = _skip(a, b)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        # parts of the same instanced prefab repeat in every copy: test the pair once per frame
        if a["inst"] and b["inst"] and a["owner"] is b["owner"] and a["pid"][:-1] == b["pid"][:-1] and len(a["pid"]) > 1:
            pk = tuple(sorted((a["orig"].name, b["orig"].name)))
            if pk in seen_prefab:
                continue
            seen_prefab.add(pk)
        A, B = _world_bvh(a), _world_bvh(b)
        if A is None or B is None:
            continue
        tested += 1
        ov = A[0].overlap(B[0])
        if not ov:
            # no crossing triangles: one may sit wholly inside the other (buried; invisible unless the outer one is glass)
            for X, Y, xi, yi in ((A, B, a, b), (B, A, b, a)):
                if Y[3] and all(yi["lo"][k] <= xi["lo"][k] and xi["hi"][k] <= yi["hi"][k] for k in range(3)):
                    ins, d = _inside(Y[0], True, X[1][0])
                    if ins:
                        dd = max(_inside(Y[0], True, X[1][q])[1] for q in range(0, len(X[1]), max(1, len(X[1]) // 40)))
                        hits.append(dict(a=xi["label"], b=yi["label"], cls="buried", depth_m=round(dd, 4), depth_px=0.0,
                                         n_tris=0, vis=0.0, onscreen=0, where=None))
                        break
            continue
        ta = {p[0] for p in ov}; tb = {p[1] for p in ov}
        pre = classify(a, b, 1e9)
        if pre != "penetration":
            # one model / set construction / plants / grounded can't fail the check: no depth sampling, no ray casts (speed)
            hits.append(dict(a=a["label"], b=b["label"], cls=pre, mv=[int(a["moving"]), int(b["moving"])], depth_m=0.0,
                             depth_px=0.0, n_tris=len(ov), vis=0.0, onscreen=0, where=None))
            continue
        va = list({v for t in ta for v in A[2][t]})[:MAX_V]
        vb = list({v for t in tb for v in B[2][t]})[:MAX_V]
        depth, deep_pt = 0.0, None
        for idx in va:
            p = A[1][idx]; ins, d = _inside(B[0], B[3], p)
            if ins and d > depth:
                depth, deep_pt = d, p
        for idx in vb:
            p = B[1][idx]; ins, d = _inside(A[0], A[3], p)
            if ins and d > depth:
                depth, deep_pt = d, p
        if depth <= EPS:
            # a thin part pushed right through a slab has no vertex inside it: sample inside the crossing triangles
            for X, Y, tset in ((A, B, ta), (B, A, tb)):
                tl = list(tset); tl = tl[:: max(1, len(tl) // 60)]
                for t in tl:
                    p0, p1, p2 = X[1][X[2][t][0]], X[1][X[2][t][1]], X[1][X[2][t][2]]
                    for (u, v) in SAMPLES_UV:
                        p = p0 + (p1 - p0) * u + (p2 - p0) * v
                        ins, d = _inside(Y[0], Y[3], p)
                        if ins and d > depth:
                            depth, deep_pt = d, p
                if depth > EPS:
                    break
        # crossing region points (triangle centres of A's crossing tris)
        pts = [(A[1][A[2][t][0]] + A[1][A[2][t][1]] + A[1][A[2][t][2]]) / 3 for t in list(ta)[:200]]
        pv = [world_to_camera_view(sc, cam, p) for p in pts]
        pvf = [q for q in pv if q.z > 0]
        if pvf:
            x0, x1 = min(q.x for q in pvf), max(q.x for q in pvf); y0, y1 = min(q.y for q in pvf), max(q.y for q in pvf)
            where = [round(x0, 4), round(1 - y1, 4), round(x1, 4), round(1 - y0, 4)]
        else:
            where = None
        onscreen = [p for p, q in zip(pts, pv) if q.z > 0 and 0 <= q.x <= 1 and 0 <= q.y <= 1]
        vis_n = 0
        samp = onscreen[:: max(1, len(onscreen) // MAX_VIS)][:MAX_VIS]
        names = {a["orig"].name, b["orig"].name, a["owner"].name, b["owner"].name}
        for p in samp:
            d = p - camloc; L = d.length
            if L < 1e-6:
                continue
            r = sc.ray_cast(dg, camloc, d / L, distance=L + 0.05)
            if r[0] and r[4] is not None and r[4].original.name in names and (r[1] - p).length < max(0.03, 0.01 * L):
                vis_n += 1
        dpx = 0.0
        ref = deep_pt
        if ref is not None:
            q = world_to_camera_view(sc, cam, ref)
            if not (q.z > 0 and 0 <= q.x <= 1 and 0 <= q.y <= 1):
                ref = onscreen[0] if onscreen else None
        if ref is not None and depth > 0:
            q0 = world_to_camera_view(sc, cam, ref); q1 = world_to_camera_view(sc, cam, ref + camright * depth)
            if q0.z > 0 and q1.z > 0:
                dpx = abs(q1.x - q0.x) * rx
        hits.append(dict(a=a["label"], b=b["label"], cls=classify(a, b, depth), mv=[int(a["moving"]), int(b["moving"])], depth_m=round(depth, 4), depth_px=round(dpx, 1),
                         n_tris=len(ov), vis=round(vis_n / len(samp), 2) if samp else 0.0, onscreen=len(onscreen),
                         where=where))
    hits.sort(key=lambda h: -h["depth_px"])
    return dict(frame=master_frame, blend_frame=sc.frame_current, camera=cam.name, objects=len(items),
                pairs_bbox=len(cand), pairs_tested=tested, skipped=skipped, hits=hits, sec=round(time.time() - t0, 2))


def _write(rec):
    out = os.environ.get("COLLIDE_OUT")
    rec["blend"] = bpy.data.filepath
    rec["v"] = 2                     # v2 (Nov 7 13:20): instance geometry from the real source object
    line = json.dumps(rec)
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with _REAL_OPEN(out, "a") as f:
            f.write(line + "\n")
    n = sum(1 for h in rec.get("hits", []) if h["depth_m"] > EPS)
    print(f"[collide] f{rec.get('frame')} cam={rec.get('camera')} objs={rec.get('objects')} tested={rec.get('pairs_tested')} "
          f"hits={len(rec.get('hits', []))} deeper_than_eps={n} {rec.get('sec')}s", flush=True)


def _marker_cam(sc, f):
    cam = None
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= f and m.camera:
            cam = m.camera
    return cam


def check_blend_frame(sc, bf, use_markers=False):
    sc.frame_set(bf)
    if use_markers:
        c = _marker_cam(sc, bf)
        if c:
            sc.camera = c
    _write(check_frame(sc, bf - FOFF))


def sandbox():
    """The dry run runs NEXT TO the real render (tools/gpuq.sh), so the job's scripts must not touch any file: writes go to
    /dev/null, deletes/moves/copies and subprocesses do nothing (render_final.py, shots.py tidy and rename frames)."""
    import shutil, subprocess
    outp = os.path.abspath(os.environ.get("COLLIDE_OUT", "")) if os.environ.get("COLLIDE_OUT") else None
    def s_open(file, mode="r", *a, **k):
        if isinstance(file, (str, bytes, os.PathLike)) and any(c in mode for c in "wax+"):
            if not outp or os.path.abspath(os.fsdecode(file)) != outp:
                return _REAL_OPEN(os.devnull, "wb" if "b" in mode else "w")
        return _REAL_OPEN(file, mode, *a, **k)
    builtins.open = s_open
    def nop(*a, **k):
        return None
    for n in ("remove", "unlink", "rename", "replace", "rmdir", "removedirs", "renames", "truncate"):
        if hasattr(os, n):
            setattr(os, n, nop)
    os.system = lambda *a, **k: 0
    for n in ("rmtree", "move", "copy", "copy2", "copyfile", "copytree", "copyfileobj"):
        setattr(shutil, n, nop)
    class _P:
        returncode = 0; stdout = b""; stderr = b""; pid = 0
        def __init__(self, *a, **k): pass
        def wait(self, *a, **k): return 0
        def communicate(self, *a, **k): return (b"", b"")
        def poll(self): return 0
    subprocess.Popen = _P
    subprocess.run = lambda *a, **k: _P()
    subprocess.call = subprocess.check_call = lambda *a, **k: 0
    subprocess.check_output = lambda *a, **k: b""


def install_hook():
    """Dry render: every bpy.ops.render.render call checks instead of rendering."""
    m = bpy.ops.render
    def fake_render(*a, **k):
        sc = bpy.context.scene
        if k.get("animation"):
            f0 = sc.frame_current
            for bf in range(sc.frame_start, sc.frame_end + 1, STEP):
                check_blend_frame(sc, bf, use_markers=True)
            sc.frame_set(f0)
        else:
            _write(check_frame(sc, sc.frame_current - FOFF))
        return {"FINISHED"}
    m.render = fake_render
    bpy.ops.render = m
    sandbox()
    w = bpy.ops.wm                 # a dry run never writes a blend (it changed viewport visibility/modifier levels)
    def no_save(*a, **k):
        print("[collide] dry run: save skipped", flush=True); return {"CANCELLED"}
    w.save_mainfile = no_save; w.save_as_mainfile = no_save
    bpy.ops.wm = w
    print("[collide] hook installed: renders become collision checks", flush=True)


def _parse_frames(s):
    out = []
    for part in s.split(","):
        if "-" in part[1:]:
            a, b = part.split("-", 1) if not part.startswith("-") else (part, part)
            out += list(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--frames" in argv and os.path.basename(__file__) == "collide_check.py" and argv and argv[0].startswith("--"):
        def A(k, d=None):
            return argv[argv.index(k) + 1] if k in argv else d
        if A("--out"):
            os.environ["COLLIDE_OUT"] = A("--out")
        off = int(A("--off", "0")); step = int(A("--step", "1")); FOFF = off
        sc = bpy.context.scene
        for fm in _parse_frames(A("--frames"))[::step]:
            check_blend_frame(sc, fm + off, use_markers=True)
    else:
        install_hook()
