"""hero.py -- <plate> <mode> [frames]      It's Written: the two hero plates of her (Rate Limited look), Nov 24 2026.
  plate: well (The water looks up, film frames 4880-4960) | ride (On the raised stroke, 2417-2476)
  mode : dry   build + pose + numbers, no render
         still frames at 960x540 -> hero/work/stills/<plate>_<frame>.png (+ exposure probe, saved to expo_<plate>.json)
         final frames at 1920x1080 -> hero/out/<dir>/<name>_####.exr (straight alpha, half, DWAA) + 960x540 PNG proxies
  frames: "4880-4960" or "4885,4910" (default: the plate's own range)
  env  : HERO_DEVICE=GPU|CPU (default CPU), HERO_SPP, HERO_HAIR (strands, default 40000)
She is built ONCE per run on a base pose with the shared Rate Limited look (copies of characters/rain_her_r2 in ./rain_her_r2:
her_look.hat / curls / love / natural_lashes, look.apply); then every frame is a pure function of the frame number: the rig's
head, eyes and face controls are set, the hat and lashes ride the head bone, the hair is carried by head and chest, and (ride)
the wind bends it aft. Rain Rig (c) Blender Foundation | cloud.blender.org, modified."""
import bpy, sys, os, math, time, json, traceback
import numpy as np
from mathutils import Vector, Matrix
D = bpy.data; rad = math.radians
HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = '~/Projects/deadletter-studio'
sys.path.insert(0, os.path.join(HERE, 'rain_her_r2'))
SRC = STUDIO + '/assets/characters/rain_v2/rain_rig.blend'
MAPS = STUDIO + '/assets/characters/rain_her_r2/maps'
OUT = os.path.abspath(os.path.join(HERE, '..', 'out'))
argv = sys.argv[sys.argv.index('--') + 1:]
PLATE, MODE = argv[0], argv[1]
RANGE = dict(well=(4880, 4960), ride=(2417, 2476))[PLATE]
BASE_F = dict(well=4940, ride=2450)[PLATE]
OUTDIR = dict(well='well_look_up', ride='ride_front')[PLATE]
SC = 1.70 / 1.6239                                             # her height on Rain's rig
COAT = (.102, .077, .061); COLLAR = (.105, .080, .065); THREAD = (.55, .004, .020)      # the film figure's swatches (codex/src/walkwind/materials.py)
T0 = time.time()


def log(*a): print(f'[hero {PLATE} {time.time() - T0:6.1f}s]', *a, flush=True)


def frames_arg():
    if len(argv) < 3: return list(range(RANGE[0], RANGE[1] + 1))
    out = []
    for part in argv[2].split(','):
        if '-' in part: a, b = part.split('-'); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return out


def ss(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def ease(f, a, b): return ss((f - a) / float(b - a))
def mix(a, b, t): return a + (b - a) * t
def npm(m): return np.array(m, dtype=float)


# ---------------------------------------------------------------- the acting: every frame a pure function of the frame number
def well_params(S, f):
    """looking down into the water under the cap; the chin lifts 4894-4910; eyes meet the viewer on 4910; then she holds: breath, one small eye
    adjustment (4931), the start of a smile"""
    lift = ease(f, 4894, 4910); eyes = ease(f, 4896, 4909); lidp = ease(f, 4897, 4908)
    over = math.exp(-(f - 4910) / 6.0) * math.sin((f - 4910) / 6.0 * math.pi) * 0.9 if f > 4910 else 0.0        # the lift overshoots a touch and settles
    br = math.sin(2 * math.pi * (f - 4880) / 98.0)                                                              # breath, ~3.3 s
    sm = ease(f, 4917, 4958)
    cam = S['cam_pos']; E = S['E0']
    down = Vector((E[0] + 0.02, E[1] - 1.50, 0.0))                                                              # the water just ahead of her feet
    adj = Vector((0.065, 0, 0.012)) * ease(f, 4930, 4933)                                                       # the small eye adjustment
    look = down.lerp(Vector(cam) + adj, eyes)
    return dict(loc=(0, 0, 0.0028 * br), rot=(0, 0, 0),
                neck=(mix(16, 9, lift) + 0.15 * br, mix(-3, 0, lift), mix(1.5, 0.6, lift)),
                head=(mix(27, 13, lift) - over - 0.35 * br, mix(-4, 0, lift), mix(3.5, 1.6, lift)),
                look=look, smile=mix(0.24, 0.32, lidp) + 0.50 * sm, lids=mix(0.64, 0.26, lidp), brows=0.0 + 0.05 * lidp + 0.08 * sm, lids_low=0.08 + 0.30 * sm, lash=lidp, jaw=0.0)


def ride_params(S, f):
    """a ride: banked at the start, her eyes pick up the next rise beyond the camera, her shoulders open (she leans back, chin up), the first smile
    comes before the rail levels near the end"""
    k = f - 2417
    level = ease(f, 2452, 2474)
    bank = -5.5 * (1 - level) + 0.9 * math.sin(2 * math.pi * k / 23.0)                  # degrees, about her forward axis
    opn = ease(f, 2423, 2450)
    bob = 0.0035 * math.sin(2 * math.pi * k / 7.3) + 0.0022 * math.sin(2 * math.pi * k / 3.1 + 1.0)
    sm = ease(f, 2427, 2449); br = ease(f, 2421, 2438)
    look = Vector((mix(0.75, -0.15, ease(f, 2420, 2446)), -8.0, mix(0.95, 2.05, ease(f, 2419, 2444))))
    b0 = S['base_loc']
    return dict(loc=(b0[0], b0[1], b0[2] + bob), rot=(rad(-3.5 * opn), rad(bank), 0),
                neck=(mix(5, -3, opn), mix(5, -1.5, opn), -0.25 * bank), head=(mix(8, -5, opn), mix(7, -2, opn), -0.35 * bank + 1.0),
                look=look, smile=0.40 + 0.55 * sm, lids=0.17, brows=0.06 + 0.22 * br, lids_low=0.12 + 0.26 * sm, lash=1.0,
                jaw=(1.5 + 6.5 * sm) * float(os.environ.get('HERO_JAW', '1')))


PARAMS = dict(well=well_params, ride=ride_params)[PLATE]


def apply_pose(S, f):
    import rain_her as H
    rig = S['rig']; p = PARAMS(S, f)
    rig.location = p['loc']; rig.rotation_euler = p['rot']
    for bn, key in (('FK-Neck', 'neck'), ('FK-Head', 'head')):
        pb = rig.pose.bones[bn]; pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
        H.turn(rig, bn, pitch=p[key][0], yaw=p[key][1], roll=p[key][2])
    pb = rig.pose.bones['MSTR-Jaw']; pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
    if p.get('jaw'): H.turn(rig, 'MSTR-Jaw', pitch=p['jaw'])
    H.upd()
    H.face(rig, look_at=p['look'], smile=p['smile'], lids=p['lids'], brows=p['brows'], lids_low=p['lids_low'])
    H.upd(); return p


def bone_w(rig, name): return rig.matrix_world @ rig.pose.bones[name].matrix


def bone_parent(o, rig, bone):
    mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = mw; bpy.context.view_layer.update()


# ---------------------------------------------------------------- what follows the pose each frame
def followers(S, f, p):
    rig = S['rig']; Mh = bone_w(rig, 'DEF-Head'); Mc = bone_w(rig, S['chest'])
    Dh = npm(Mh @ S['Mh0'].inverted()); Dc = npm(Mc @ S['Mc0'].inverted())
    P0 = S['hairP0']; w = S['hairW'][:, None]
    P = (P0 @ Dh[:3, :3].T + Dh[:3, 3]) * w + (P0 @ Dc[:3, :3].T + Dc[:3, 3]) * (1 - w)
    if PLATE == 'ride': P = wind_hair(S, P, f, Dc)
    hd = S['hair'].data; hd.points.foreach_set('position', P.reshape(-1).astype('f')); hd.update_tag()
    if S.get('lashA') is not None:
        L = S['lashA'] * (1 - p['lash']) + S['lashB'] * p['lash']
        ld = S['lashes'].data; ld.points.foreach_set('position', L.reshape(-1).astype('f')); ld.update_tag()
    if PLATE == 'ride': thread_points(S, f)
    bpy.context.view_layer.update()


def wind_hair(S, P, f, Dc):
    """the ride's wind: every lock swings aft about its root, more toward its end, and flutters; then anything blown into her coat or collar is
    lifted back out"""
    nh, pts = S['nh'], S['pts']; Q = P.reshape(nh, pts, 3); root = Q[:, :1]; d = Q - root; t = (f - 2417) / 30.0
    u = S['u'][None, :]; r = np.clip((u - 0.10) / 0.45, 0, 1); ramp = r * r * (3 - 2 * r); g = S['gain'][:, None]; ph = S['phase'][:, None]
    phi = ramp * (rad(S['wind_deg']) * g + rad(9) * np.sin(2 * np.pi * (2.2 * u - 2.3 * t) + ph) + rad(4) * np.sin(2 * np.pi * (5.0 * u - 4.1 * t) + 1.7 * ph))
    c, s_ = np.cos(phi), np.sin(phi)
    y = d[..., 1] * c - d[..., 2] * s_; z = d[..., 1] * s_ + d[..., 2] * c
    x = d[..., 0] + ramp * (S['side'][:, None] * 0.030 * u + 0.016 * u * np.sin(2 * np.pi * (1.6 * u - 1.9 * t) + 0.7 * ph))
    Q2 = root + np.stack([x, y, z], -1); out = Q2.reshape(-1, 3)
    # collision with her coat + collar (built in base space): only points inside their box
    Di = np.linalg.inv(Dc); B = out @ Di[:3, :3].T + Di[:3, 3]; lo, hi = S['col_box']
    m = np.all((B > lo) & (B < hi), axis=1) & (np.tile(S['u'], nh) > 0.12); idx = np.nonzero(m)[0]; bvh = S['col_bvh']; h = 0.004; nfix = 0
    for i in idx:
        loc, nrm, _, dist = bvh.find_nearest(Vector(B[i]), 0.03)
        if loc is None: continue
        v = Vector(B[i]) - loc; sd = dist if v.dot(nrm) >= 0 else -dist
        if sd < h: B[i] = np.array(loc) + np.array(nrm) * h; nfix += 1
    out[idx] = B[idx] @ Dc[:3, :3].T + Dc[:3, 3]
    S['last_fix'] = (len(idx), nfix); return out


def thread_points(S, f):
    """the red thread: once round her collar, then (ride) the loose end streaming aft over her left shoulder / (well) a short end hanging"""
    ring = S['thread_ring']; a = S['thread_anchor']; n = 44; s = np.linspace(0, 1, n)[:, None]
    if PLATE == 'ride':
        t = (f - 2417) / 30.0; Lt = 0.60 * SC
        d = np.array((0.62, 0.70, 0.36)); d /= np.linalg.norm(d)
        tail = a + s * Lt * d
        tail[:, 0] += (0.040 * s[:, 0] ** 1.2) * np.sin(2 * np.pi * (2.1 * s[:, 0] - 2.9 * t))
        tail[:, 2] += (0.034 * s[:, 0] ** 1.2) * np.sin(2 * np.pi * (1.6 * s[:, 0] - 2.3 * t) + 1.3)
    else:
        out_d = S['thread_out']; tail = a + s * 0.042 * SC * np.array((0.10, 0, -1.0)) + (s ** 0.5) * out_d * 0.012
    pts = np.concatenate([ring, ring[:1], tail[1:]])
    sp = S['thread'].data.splines[0]
    if len(sp.points) != len(pts): sp.points.add(len(pts) - len(sp.points))
    flat = np.concatenate([pts, np.ones((len(pts), 1))], 1).reshape(-1); sp.points.foreach_set('co', flat.astype('f')); S['thread'].data.update_tag()


# ---------------------------------------------------------------- the build
def build():
    import rain_her as H, look as LK, hair as HR, wear_door as WD, her_look as HL
    HL.OAT = tuple(c * 0.34 for c in COAT)                        # the cozy knit, in the film figure's coat colour (the knit image reads lighter than its swatch)
    for o in list(D.objects): D.objects.remove(o, do_unlink=True)
    sc = bpy.context.scene
    rig = H.load(SRC); body = H.strip(rig); LK.apply(MAPS, log=log); H.upd(); rest = WD.rest_shape(rig, body)
    rig.scale = (SC, SC, SC); rig.rotation_mode = 'XYZ'; H.upd()
    S = dict(rig=rig, body=body, sc=sc)
    names = [b.name for b in rig.pose.bones]
    S['chest'] = next(n for n in ('DEF-Chest', 'DEF-RibCage', 'DEF-Spine3', 'DEF-Spine2') if n in names)
    log('bones:', [n for n in names if n.startswith('DEF-') and any(k in n for k in ('Neck', 'Head', 'Chest', 'Rib', 'Spine'))], '| chest =', S['chest'])
    log('face/jaw controls:', [n for n in names if any(k in n for k in ('Jaw', 'Mouth')) and not n.startswith(('DEF', 'ORG', 'MCH', 'TGT'))][:24])
    # ---- body pose (everything below her neck holds this for the whole plate)
    H.set_ik(rig)
    if PLATE == 'well':
        for s, sg in (('L', 1), ('R', -1)):
            H.hand(rig, s, (sg * 0.225, 0.03, 0.86), (sg * 0.10, -0.10, -1), (sg * 1, 0.0, 0.1), (sg * 0.45, 0.50, 1.10))
            for fg in ('Index', 'Middle', 'Ring', 'Pinky'): H.curl(rig, s, fg, 16, 22, 14)
        H.turn(rig, 'FK-Chest', pitch=3.0)
        S['base_loc'] = (0, 0, 0)
    else:
        import pose_h2 as PH
        PH.pose_body(rig, body, variant='a', lean=10.0, look_at=None, log=log)
        for s, sg in (('L', 1), ('R', -1)):
            H.hand(rig, s, (sg * 0.30 + 0.01, 0.18 + 0.02 * sg, 0.055), (sg * 0.40, -1, -0.12), (0, -0.1, 1), (sg * 0.62, 0.72, 0.40))
            for fg in ('Index', 'Middle', 'Ring', 'Pinky'): H.curl(rig, s, fg, 10, 14, 10)
        H.turn(rig, 'FK-Chest', yaw=5.0, roll=-2.0)
        H.upd(); sl = PH.seat_low(rig, body, rest); rig.location.z += 0.006 - sl; H.upd()
        S['base_loc'] = tuple(rig.location); log(f'seated: seat skin was at z {sl:.3f}; rig lifted to {rig.location.z:.3f}')
    # ---- a first guess of the camera (the well's is fitted to her after the hat is on)
    E0 = (Vector(H.wpos(rig, 'DEF-Eye.L')) + Vector(H.wpos(rig, 'DEF-Eye.R'))) / 2
    S['E0'] = E0; S['cam_pos'] = (E0 + Vector((0.0, -1.72, -0.66))) if PLATE == 'well' else Vector((0, -1.61, 1.04))
    apply_pose(S, BASE_F)
    E0 = (Vector(H.wpos(rig, 'DEF-Eye.L')) + Vector(H.wpos(rig, 'DEF-Eye.R'))) / 2
    if PLATE == 'well': S['E0'] = E0; S['cam_pos'] = E0 + Vector((0.0, -1.72, -0.66)); apply_pose(S, BASE_F)
    log('eyes (world) at', [round(v, 3) for v in E0], ' head bone', [round(v, 3) for v in H.wpos(rig, 'DEF-Head')])
    # ---- the coat (the cozy knit in the coat's colour), the collar, the thread
    before = set(D.objects)
    M = WD.materials(STUDIO); O = HL.cozy_outfit(rig, body, rest, M, log=log); sweater = O['top']; S['sweater'] = sweater
    collar = make_collar(S, H, HR, [body, sweater]); S['collar'] = collar
    make_thread(S)
    # ---- her head: scalp, curls, hat, LOVE, lashes (the shared Rate Limited look)
    head = D.objects['GEO-rain_head']; NH = int(os.environ.get('HERO_HAIR', '40000')); PTS = 48
    cap = D.materials.new('HER_scalp'); cap.use_nodes = True; b = next(x for x in cap.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value = (0.27, 0.165, 0.072, 1); b.inputs['Roughness'].default_value = .7
    pre_head = set(D.objects)
    HR.scalp_cap(rig, head, cap)
    hair, hinfo = HL.curls(rig, head, [body, sweater, collar], n_hair=NH, pts=PTS, log=log)
    hb = HL.press_hair(rig, hair, head, log=log)
    hat, pom, hat_info = HL.hat(rig, hb, log=log); love = HL.love(hat_info, log=log)
    lashes = HL.natural_lashes(rig, log=log)
    S.update(hair=hair, hat=hat, pom=pom, lashes=lashes)
    head_objs = [o for o in D.objects if o not in pre_head and o is not hair]
    log('rides her head:', [o.name for o in head_objs])
    Mh0 = bone_w(rig, 'DEF-Head').copy(); Mc0 = bone_w(rig, S['chest']).copy(); S['Mh0'] = Mh0; S['Mc0'] = Mc0
    for o in head_objs: bone_parent(o, rig, 'DEF-Head')
    for o in [o for o in D.objects if o not in before and o not in head_objs and o is not hair and o.parent is None]: bone_parent(o, rig, S['chest'])
    # ---- hair: base points, how much each follows her head (above her jaw: all; on her shoulders: none)
    n = len(hair.data.points); P0 = np.empty(n * 3, 'f'); hair.data.points.foreach_get('position', P0); P0 = P0.reshape(-1, 3).astype(float)
    Lx, Fw, Up = HR.head_axes(rig); hc = np.array(H.wpos(rig, 'DEF-Head')) + Up * 0.115 * SC; zl = ((P0 - hc) @ Up) / SC
    r = np.clip((zl + 0.215) / 0.105, 0, 1); S['hairP0'] = P0; S['hairW'] = r * r * (3 - 2 * r); S['nh'] = n // PTS; S['pts'] = PTS; S['u'] = np.linspace(0, 1, PTS)
    log(f'hair: {S["nh"]} strands x {PTS}; head-carried share {float((S["hairW"] > .5).mean()):.2f}; zl range {zl.min():.2f}..{zl.max():.2f}')
    if PLATE == 'ride':
        rng = np.random.default_rng(21); roots = P0.reshape(S['nh'], PTS, 3)[:, 0]
        gr = hinfo['roots']; lock = np.concatenate([np.argmin(np.linalg.norm(roots[c0:c0 + 4000, None, :] - gr[None, :, :], axis=2), axis=1) for c0 in range(0, S['nh'], 4000)])
        gl = 0.84 + 0.30 * rng.random(len(gr)); pl = 14.0 * gr[:, 0] + 9.0 * gr[:, 2] + rng.normal(0, 0.30, len(gr))          # each lock swings as one
        S['gain'] = gl[lock] + rng.normal(0, 0.018, S['nh']); S['phase'] = pl[lock] + rng.normal(0, 0.07, S['nh'])
        S['side'] = np.where(gr[lock, 0] - hc[0] >= 0, 1.0, -1.0); S['wind_deg'] = float(os.environ.get('HERO_WIND', '48'))
        allc = []; allt = []; off = 0
        for o in (sweater, collar):
            c, tr, _ = H.eval_mesh(o); allc.append(c); allt.append(tr + off); off += len(c)
        cc = np.concatenate(allc); S['col_bvh'] = H.bvh_of(cc, np.concatenate(allt)); S['col_box'] = (cc.min(0) - 0.012, cc.max(0) + 0.012)
    # ---- lashes: a second state for the lowered lids of the well's first frames
    nl = len(lashes.data.points); LB = np.empty(nl * 3, 'f'); lashes.data.points.foreach_get('position', LB); S['lashB'] = LB.reshape(-1, 3).astype(float); S['lashA'] = None
    if PLATE == 'well':
        apply_pose(S, RANGE[0]); tmp = HL.natural_lashes(rig, name='HER_lashes_low', log=log)
        LA = np.empty(nl * 3, 'f'); tmp.data.points.foreach_get('position', LA); LA = LA.reshape(-1, 3).astype(float)
        Dl = npm(Mh0 @ bone_w(rig, 'DEF-Head').inverted()); S['lashA'] = LA @ Dl[:3, :3].T + Dl[:3, 3]
        D.objects.remove(tmp, do_unlink=True); apply_pose(S, BASE_F)
        log(f'lashes: lowered-lid state differs from open by up to {float(np.abs(S["lashA"] - S["lashB"]).max()) * 1000:.1f} mm')
    # ---- skin under her clothes left out (as blrdoor.hide_skin)
    vg = body.vertex_groups.new(name='under_clothes'); idx = [v.index for v in body.data.vertices if v.co.z < 1.297 and abs(v.co.x) < 0.425]; vg.add(idx, 1.0, 'REPLACE')
    m = body.modifiers.new('under_clothes', 'MASK'); m.vertex_group = 'under_clothes'; m.invert_vertex_group = True
    try: body.modifiers.move(len(body.modifiers) - 1, 1)
    except Exception: traceback.print_exc()
    H.upd(); stage(S); return S


def make_collar(S, H, HR, objs):
    """a soft stand collar round her neck in the coat's wool: outside her neck and the knit at every height, low at the front (clear of her chin)"""
    rig = S['rig']; names = [b.name for b in rig.pose.bones]; nk = next(n for n in ('DEF-Neck', 'DEF-Neck1', 'DEF-Neck.001') if n in names)
    nb = np.array(H.wpos(rig, nk)); hbp = np.array(H.wpos(rig, 'DEF-Head')); ax = hbp - nb; nlen = float(np.linalg.norm(ax)); ax /= nlen
    Rw = np.array(rig.matrix_world.to_3x3().normalized()); e1 = Rw[:, 0] - ax * (Rw[:, 0] @ ax); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)      # her left, her back
    allc = []; allt = []; off = 0
    for o in objs:
        c, tr, _ = H.eval_mesh(o); allc.append(c); allt.append(tr + off); off += len(c)
    bvh = H.bvh_of(np.concatenate(allc), np.concatenate(allt)); NT, NJ = 56, 7; th = np.linspace(0, 2 * np.pi, NT, endpoint=False)
    front = -np.sin(th)                                           # +1 at her front (dir = -e2)
    h_bot = -0.034 * SC; h_top = (0.026 - 0.017 * front) * SC      # low at the front, higher at the back
    V = np.zeros((NJ, NT, 3)); R = np.zeros((NJ, NT))
    for j in range(NJ):
        hn = j / (NJ - 1.0)
        for i in range(NT):
            h = h_bot + (h_top[i] - h_bot) * hn; c = nb + ax * h; dv = math.cos(th[i]) * e1 + math.sin(th[i]) * e2
            hit = bvh.ray_cast(Vector(c + dv * 0.30), Vector(-dv), 0.30); r = (0.30 - hit[3]) if hit[0] is not None else 0.055 * SC
            R[j, i] = r
    rtop = np.minimum(R[-1], np.median(R[-1]) * 1.25); NP = 12; verts = []; faces = []; ring = []; outs = []
    rolls = ((0.010, 0.0165, 0.0215, 0.0), (-0.021, 0.0185, 0.0225, 0.5))          # (height of its middle, radial half-width, vertical half-height, phase): the upper turn, the lower turn
    hs = np.array([h_bot + (np.mean(h_top) - h_bot) * j / (NJ - 1.0) for j in range(NJ)])
    for hm, ra, rb, ph in rolls:
        base = len(verts); cen = np.zeros((NT, 3)); dvs = np.zeros((NT, 3))
        hh = (hm - 0.011 * front + 0.003 * np.sin(3 * th + ph * 5)) * SC
        rr = np.array([np.interp(hh[i], hs, np.minimum(R[:, i], rtop[i] + 0.030 * SC)) for i in range(NT)]) + (ra + 0.0025) * SC
        for _ in range(4): rr = (np.roll(rr, 1) + 2 * rr + np.roll(rr, -1)) / 4
        for i in range(NT):
            dv = math.cos(th[i]) * e1 + math.sin(th[i]) * e2; dvs[i] = dv; cen[i] = nb + ax * hh[i] + dv * rr[i]
            for q in range(NP):
                a_ = 2 * np.pi * q / NP; verts.append(cen[i] + dv * (ra * SC * math.cos(a_)) + ax * (rb * SC * math.sin(a_)))
        for i in range(NT):
            for q in range(NP):
                i2 = (i + 1) % NT; q2 = (q + 1) % NP; faces.append((base + i * NP + q, base + i2 * NP + q, base + i2 * NP + q2, base + i * NP + q2))
        if not ring:                                                              # the thread lies in the crease under the upper turn, on its outside
            a_ = rad(-6)
            for i in range(NT): ring.append(cen[i] + dvs[i] * (ra * SC * math.cos(a_) + 0.0030 * SC) + ax * (rb * SC * math.sin(a_))); outs.append(dvs[i])
    me = D.meshes.new('HERO_collar'); me.from_pydata([tuple(map(float, v)) for v in verts], [], faces); me.update()
    for p in me.polygons: p.use_smooth = True
    o = D.objects.new('HERO_collar', me); bpy.context.scene.collection.objects.link(o)
    sb = o.modifiers.new('sub', 'SUBSURF'); sb.levels = 1; sb.render_levels = 2
    m = D.materials.new('HERO_collar_wool'); m.use_nodes = True; nt = m.node_tree; b = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*[c * 0.45 for c in COLLAR], 1); b.inputs['Roughness'].default_value = 0.93
    try: b.inputs['Sheen Weight'].default_value = 0.6; b.inputs['Sheen Roughness'].default_value = 0.5
    except Exception: pass
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 340.0; nz.inputs['Detail'].default_value = 5.0
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.55; bp.inputs['Distance'].default_value = 0.0016
    nt.links.new(nz.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal'])
    me.materials.append(m)
    S['thread_ring'] = np.array(ring); ia = int(np.argmin(np.abs(th - rad(14))))        # at her left side (ride) ...
    if PLATE == 'well': ia = int(np.argmin(np.abs(th - rad(300))))                      # ... or at her front left (well)
    S['thread_anchor'] = np.array(ring[ia]); S['thread_out'] = np.array(outs[ia])
    S['thread_ring'] = np.roll(S['thread_ring'], -ia, axis=0)
    log(f'collar: neck bone {nk}, neck length {nlen:.3f}, radius {R[-1].min():.3f}..{R[-1].max():.3f} at its top, {R[0].min():.3f}..{R[0].max():.3f} at its foot')
    bpy.context.view_layer.update(); return o


def make_thread(S):
    cu = D.curves.new('HERO_thread', 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('NURBS'); sp.points.add(3); sp.use_endpoint_u = True; sp.order_u = 3
    cu.bevel_depth = 0.0016 * SC; cu.bevel_resolution = 3; cu.resolution_u = 4; cu.use_fill_caps = True
    o = D.objects.new('HERO_thread', cu); bpy.context.scene.collection.objects.link(o)
    m = D.materials.new('HERO_thread_red'); m.use_nodes = True; b = next(x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*THREAD, 1); b.inputs['Roughness'].default_value = 0.75
    try: b.inputs['Sheen Weight'].default_value = 0.5
    except Exception: pass
    cu.materials.append(m); S['thread'] = o; thread_points(S, BASE_F)


# ---------------------------------------------------------------- camera, light, film
def aim(o, p): o.rotation_euler = (Vector(p) - o.location).to_track_quat('-Z', 'Y').to_euler()


def area(name, pos, at, size, watts, col, size_y=None):
    ld = D.lights.new(name, 'AREA'); ld.size = size; ld.energy = watts; ld.color = col
    if size_y: ld.shape = 'RECTANGLE'; ld.size_y = size_y
    o = D.objects.new(name, ld); bpy.context.scene.collection.objects.link(o); o.location = pos; aim(o, at); return o


def sun(name, from_dir, strength, col, angle=0.06):
    ld = D.lights.new(name, 'SUN'); ld.energy = strength; ld.color = col; ld.angle = angle
    o = D.objects.new(name, ld); bpy.context.scene.collection.objects.link(o); d = Vector(from_dir).normalized(); o.location = d * 5; aim(o, (0, 0, 0)); return o


def stage(S):
    sc = S['sc']; rig = S['rig']; E = Vector(S['E0'])
    cam = D.cameras.new('HERO_cam'); co = D.objects.new('HERO_cam', cam); sc.collection.objects.link(co); sc.camera = co; cam.sensor_width = 36.0; cam.sensor_fit = 'HORIZONTAL'
    cam.clip_start = 0.05; cam.clip_end = 50; S['cam'] = co
    w = D.worlds.new('HERO_w'); sc.world = w; w.use_nodes = True; bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    if PLATE == 'well':
        # low on the water, looking up at her; the frame is fitted from the top of her pom-pom to her upper shoulders
        co.location = S['cam_pos']; bb = [S['pom'].matrix_world @ Vector(c) for c in S['pom'].bound_box]; top = max(bb, key=lambda v: v.z)
        top = Vector((E.x, top.y, top.z)); sh = Vector((E.x, E.y + 0.06, E.z - 0.30 * SC))
        d1 = (top - co.location).normalized(); d2 = (sh - co.location).normalized(); ang = d1.angle(d2); vfov = ang / 0.80
        cam.lens = (36.0 * 9 / 16 / 2) / math.tan(vfov / 2); mid = (d1 + d2).normalized(); aim(co, co.location + mid)
        log(f'well camera: at {[round(v, 3) for v in co.location]}, lens {cam.lens:.1f} mm, {math.degrees(math.asin(-mid.z)):.1f} deg up-look')
        bg.inputs[0].default_value = (0.010, 0.020, 0.060, 1); bg.inputs[1].default_value = 1.0
        S['lights'] = [area('HERO_moon', E + Vector((1.15, -1.05, 1.55)), E, 1.6, 300, (0.55, 0.72, 1.0)),            # the moon: above, to her left, soft, blue
                       area('HERO_water', Vector(S['cam_pos']) + Vector((-0.45, 0.25, -0.05)), E, 2.2, 80, (0.34, 0.52, 1.0)),   # the water's own sky light, from below
                       area('HERO_road', E + Vector((-0.55, 1.7, -0.45)), E, 1.5, 85, (1.0, 0.66, 0.36))]             # weak warm bounce from the road behind her
    else:
        cam.lens = 44.0; co.location = (0, -1.61, 1.04); aim(co, (0, 0.025, 0.79))
        bg.inputs[0].default_value = (0.012, 0.022, 0.055, 1); bg.inputs[1].default_value = 1.0
        S['lights'] = [sun('HERO_moon', (0.82, -0.43, 0.20), 3.0, (0.55, 0.72, 1.0), 0.07),                           # low blue key (spec, turned into her frame)
                       sun('HERO_rim', (-0.44, 0.84, 0.23), 2.3, (0.84, 0.90, 1.0), 0.05),                            # softer silver rim
                       area('HERO_rail', (0, -0.55, 0.02), (0, -0.55, 1.0), 0.30, 20, (1.0, 0.60, 0.16), size_y=1.7),  # the gold rail's amber, from below her knees
                       area('HERO_sand', (0.35, -2.3, 0.62), (0, 0, 0.80), 2.6, 210, (0.62, 0.75, 1.0))]                  # cool sand bounce on her face
    for L in S['lights']:
        try: L.visible_camera = False
        except Exception: pass
    sc.render.engine = 'CYCLES'; cy = sc.cycles
    dev = os.environ.get('HERO_DEVICE', 'CPU').upper()
    if dev == 'GPU':
        prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'METAL'; prefs.refresh_devices()
        mets = [d for d in prefs.devices if d.type == 'METAL']
        if not mets: raise RuntimeError('GPU asked for but Cycles lists no Metal device')
        for d in prefs.devices: d.use = d.type == 'METAL'
        log('Metal:', ', '.join(d.name for d in mets))
    cy.device = dev; cy.use_denoising = True; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
    try: cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception: traceback.print_exc()
    cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 4; cy.transmission_bounces = 8; cy.transparent_max_bounces = 24
    sc.render.film_transparent = True; sc.render.use_motion_blur = False; sc.render.resolution_x = 1920; sc.render.resolution_y = 1080
    im = sc.render.image_settings
    try: im.media_type = 'IMAGE'
    except Exception: pass
    im.file_format = 'OPEN_EXR'; im.color_mode = 'RGBA'; im.color_depth = '16'; im.exr_codec = 'ZIP'
    sc.view_settings.view_transform = 'Standard'
    k = 1.0; ef = os.path.join(HERE, f'expo_{PLATE}.json')
    if os.path.exists(ef) and os.environ.get('HERO_PROBE') != '1': k = json.load(open(ef))['k']
    set_gain(S, k)


def set_gain(S, k):
    base = S.setdefault('light_base', [L.data.energy for L in S['lights']])
    for L, e in zip(S['lights'], base): L.data.energy = e * k
    bg = next(n for n in S['sc'].world.node_tree.nodes if n.type == 'BACKGROUND'); S.setdefault('bg_base', bg.inputs[1].default_value); bg.inputs[1].default_value = S['bg_base'] * k
    S['gain_k'] = k


def cam_frame(S, f):
    if PLATE == 'ride':
        t = (f - 2417) / 59.0; co = S['cam']; co.location = (-0.072 * math.cos(math.pi * t), -1.61, 1.04); aim(co, (0, 0.025, 0.79))


def view_px(S, p):
    from bpy_extras.object_utils import world_to_camera_view
    v = world_to_camera_view(S['sc'], S['cam'], Vector(p)); return round(v.x, 3), round(v.y, 3), round(v.z, 3)


# ---------------------------------------------------------------- pixels
def read_exr(path):
    import OpenImageIO as oiio
    b = oiio.ImageBuf(path); px = np.array(b.get_pixels(oiio.FLOAT)); return px[..., :4].astype(np.float32)


def straight(px):
    a = np.clip(px[..., 3:4], 0, 1); rgb = np.where(a > 1.0 / 1024, px[..., :3] / np.maximum(a, 1e-6), 0.0); a = np.where(a > 1.0 / 1024, a, 0.0)
    return np.concatenate([np.clip(rgb, 0, 64.0), a], -1).astype(np.float32)


def srgb(x): x = np.clip(x, 0, 1); return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def write_exr(path, st):
    import OpenImageIO as oiio
    h, w, _ = st.shape; spec = oiio.ImageSpec(w, h, 4, oiio.HALF); spec.channelnames = ('R', 'G', 'B', 'A'); spec.attribute('compression', 'dwaa')
    spec.attribute('ImageDescription', 'straight (unassociated) alpha; scene-linear Rec.709; film frame number in the filename')
    out = oiio.ImageOutput.create(path); out.open(path, spec); ok = out.write_image(st); out.close()
    if not ok: raise RuntimeError('EXR write failed: ' + path)


def write_png(path, st):
    import OpenImageIO as oiio
    h, w, _ = st.shape; d8 = np.concatenate([srgb(st[..., :3]), st[..., 3:4]], -1); d8 = (np.clip(d8, 0, 1) * 255 + 0.5).astype(np.uint8)
    spec = oiio.ImageSpec(w, h, 4, oiio.UINT8); spec.attribute('oiio:UnassociatedAlpha', 1); spec.attribute('oiio:ColorSpace', 'sRGB')
    out = oiio.ImageOutput.create(path); out.open(path, spec); ok = out.write_image(d8); out.close()
    if not ok: raise RuntimeError('PNG write failed: ' + path)


def half(px):
    h, w, c = px.shape; return px.reshape(h // 2, 2, w // 2, 2, c).mean((1, 3))


def render_to(S, tmp):
    S['sc'].render.filepath = tmp; bpy.ops.render.render(write_still=True); return read_exr(tmp)


def face_stats(S, px):
    """luminance of her face (between her eyes and her chin), for the exposure probe"""
    h, w, _ = px.shape; E = Vector(S['E_now']); pts = [E + Vector((dx, 0, dz)) for dx in (-0.06, 0.06) for dz in (-0.10 * SC, 0.015)]
    v = [view_px(S, p) for p in pts]; x0 = int(min(a[0] for a in v) * w); x1 = int(max(a[0] for a in v) * w); y0 = int((1 - max(a[1] for a in v)) * h); y1 = int((1 - min(a[1] for a in v)) * h)
    box = px[max(y0, 0):y1, max(x0, 0):x1]; a = box[..., 3]; rgb = box[..., :3] / np.maximum(box[..., 3:4], 1e-6); Y = (rgb @ np.array((0.2126, 0.7152, 0.0722)))[a > 0.95]
    if not len(Y): return None
    return dict(p25=float(np.percentile(Y, 25)), p50=float(np.percentile(Y, 50)), p75=float(np.percentile(Y, 75)), p99=float(np.percentile(Y, 99)), n=int(len(Y)), box=(x0, y0, x1, y1))


def do_frame(S, f):
    import rain_her as H
    S['sc'].frame_set(f); cam_frame(S, f); p = apply_pose(S, f); followers(S, f, p)
    S['E_now'] = (Vector(H.wpos(S['rig'], 'DEF-Eye.L')) + Vector(H.wpos(S['rig'], 'DEF-Eye.R'))) / 2
    return p


def main():
    S = build(); sc = S['sc']; frames = frames_arg(); import rain_her as H
    tmpdir = os.path.join(HERE, 'tmp'); os.makedirs(tmpdir, exist_ok=True); tmp = os.path.join(tmpdir, f'raw_{PLATE}_{MODE}.exr')
    try:
        import OpenImageIO as oiio; log('OpenImageIO', oiio.VERSION_STRING)
    except Exception as ex: log('NO OpenImageIO:', repr(ex))
    if MODE == 'dry':
        for f in sorted(set([RANGE[0], BASE_F, RANGE[1]] + frames[:1])):
            p = do_frame(S, f); rig = S['rig']
            pomtop = max((S['pom'].matrix_world @ Vector(c) for c in S['pom'].bound_box), key=lambda v: v.z)
            log(f'frame {f}: eyes {view_px(S, S["E_now"])} pom top {view_px(S, pomtop)} hands L {view_px(S, H.wpos(rig, "DEF-Hand.L"))} R {view_px(S, H.wpos(rig, "DEF-Hand.R"))} '
                f'feet L {view_px(S, H.wpos(rig, "DEF-Foot.L"))} R {view_px(S, H.wpos(rig, "DEF-Foot.R"))} shoulders {view_px(S, H.wpos(rig, "DEF-Upperarm1.L"))} {view_px(S, H.wpos(rig, "DEF-Upperarm1.R"))} '
                f'hat follows head: {[round(v, 4) for v in S["hat"].matrix_world.translation]} wind fix {S.get("last_fix")}')
        return
    if MODE == 'still':
        sc.render.resolution_percentage = 50; sc.cycles.samples = int(os.environ.get('HERO_SPP', '48')); od = os.path.join(HERE, 'stills'); os.makedirs(od, exist_ok=True)
        if os.environ.get('HERO_PROBE') == '1':
            do_frame(S, BASE_F); sc.render.resolution_percentage = 25; spp = sc.cycles.samples; sc.cycles.samples = 16
            st = face_stats(S, render_to(S, tmp)); log('probe', st)
            k = min(max(0.34 / max(st['p75'], 1e-4), 0.05), 40.0) if st else 1.0; json.dump(dict(k=k, probe=st), open(os.path.join(HERE, f'expo_{PLATE}.json'), 'w')); set_gain(S, k); log(f'exposure gain {k:.3f}')
            sc.render.resolution_percentage = 50; sc.cycles.samples = spp
        for f in frames:
            t1 = time.time(); do_frame(S, f); px = render_to(S, tmp); st = straight(px); write_png(os.path.join(od, f'{PLATE}_{f}.png'), st)
            log(f'still {f}: {time.time() - t1:.1f}s; face {face_stats(S, px)}; alpha cover {float((px[..., 3] > 0.5).mean()):.3f}; wind fix {S.get("last_fix")}')
        return
    # final
    sc.render.resolution_percentage = 100; sc.cycles.samples = int(os.environ.get('HERO_SPP', '64'))
    name = dict(well='well', ride='ride')[PLATE]; od = os.path.join(OUT, OUTDIR); pd = os.path.join(OUT, 'proxy', OUTDIR); os.makedirs(od, exist_ok=True); os.makedirs(pd, exist_ok=True)
    done = 0
    for f in frames:
        ep = os.path.join(od, f'{name}_{f:04d}.exr'); pp = os.path.join(pd, f'{name}_{f:04d}.png')
        if os.path.exists(ep) and os.path.exists(pp) and os.path.getsize(ep) > 20000: continue
        t1 = time.time(); do_frame(S, f); px = render_to(S, tmp)
        if not np.isfinite(px).all(): raise RuntimeError(f'frame {f}: non-finite pixels')
        cover = float((px[..., 3] > 0.5).mean())
        if cover < 0.02: raise RuntimeError(f'frame {f}: she is not in the picture (alpha cover {cover:.4f})')
        write_exr(ep, straight(px)); write_png(pp, straight(half(px))); done += 1
        log(f'FRAME {f} done in {time.time() - t1:.1f}s (alpha cover {cover:.3f}, wind fix {S.get("last_fix")}) -> {os.path.basename(ep)}')
    log(f'PLATE {PLATE} DONE: {done} frames rendered, {len(frames) - done} already there')


try:
    main()
except Exception:
    traceback.print_exc(); sys.exit(1)
