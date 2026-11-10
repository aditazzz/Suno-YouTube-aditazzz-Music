// Bridge A + B + instrumental (br_point .. inst), 148.40-173.75 s: the quiet heart of the film. (earth_sec_br, Nov 8)
//
// ONE scene function of song time for all nine slots (every slot's builder is `scene`), so the engine's 0.45 s slot blend
// always blends a frame with itself and the shot changes are exactly where this file puts them:
//   shot 1  148.40  "I'll still point you out at night"   the night over her dome: his stars come back out, and the sky
//                                                         clears a little ring around ONE warm star (him). Cut in (hold key).
//   shot 2  151.20  "Tell the children where you've gone" CUT to a hill (her limb, close): small figures of light, one points
//                                                         at his star, a dotted line of light climbs to it, the star answers.
//                                                         ENGINE VERSION; the ground v2 clip replaces it (inserts below).
//   shot 3  153.60  "Every word you speak up there /      CUT to her horizon over Europe: on each word lights lift off her
//                    You learned from everyone"           cities and rivers (HER cyan / violet) in ropes and DRAW his outline: the approved
//                                                         3D satellite's own edges, around his star, which becomes his eye (closed on "everyone").
//                                                         earth_him_wire renders the real him over it (himTrack / HIM_POSE below).
//           158.08  "past the moon / other sands /        the same shot pulls all the way back: he shrinks into the distance past
//                    leave the ground behind"             a crescent of stars, toward far worlds drawn in stars; she becomes small.
//           164.64  "But you can't leave where you began" the one thread of light that never let go (river mouth to him, there since
//                                                         "everyone") swells; a bead of light climbs it on every word.
//   inst    167.10  "began" + the instrumental         CUT 2 (Nov 9): on "began" CUT to the hill again, closer: the thread ends in the
//                                                         smallest child's hand like a kite string; a hop, a tug, a bead of light climbs to
//                                                         his star, it answers; her flowers come up along the crest, spreading from the
//                                                         child's feet, on the beat. The final chorus cuts in at 173.75. (GROUND = false:
//                                                         the first cut's dive down the thread into her.)
// The camera is returned by the builder (a pure function of time, per format); the one camera key below only gives the
// engine the same camera at the cut in. 9:16 is framed by hand here (the engine's reframe drops low horizons out of frame):
// `inv916` hands the engine the camera whose 9:16 reframe is exactly the one wanted. All geometry below is in final screen units.
import { Section, Builder, smooth, lerp, env, hits, clamp01, flow, C, RIVERS } from './api';
import { Anchor, at, words } from '../anchor';
import { projGeo, SPIN_DEG_S } from '../camera';
import { ASPECT, N_CAST, rng } from '../stars';
import { Cam, Flow, Fmt, Pulse, Spark, StarKey } from '../types';
import { Grade, RGB } from '../grade';
import { LOOK } from './coldOpen'; // the approved look (lux planet, deep stars, Milky Way mist): read only
import { TIMING } from '../timing.gen';

type P = [number, number];
type P3 = [number, number, number];
const D2R = Math.PI / 180;
const smoother = (a: number, b: number, x: number) => { const u = clamp01((x - a) / (b - a)); return u * u * u * (u * (6 * u - 15) + 10); };
const backOut = (u: number) => { const s = 1.6, v = clamp01(u) - 1; return 1 + v * v * ((s + 1) * v + s); };
const mix3 = (a: RGB, b: RGB, u: number): RGB => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
const WHITE: RGB = [1, 1, 1];

// ---- times (cuts sit 2 ms before their frame, so the frame AT the sung time is already the new shot) ----
const FR = (a: Anchor, off = 0) => Math.round((at(a) + off) * 30) / 30 - 0.002;
const T0 = at('bridgeA/L0'), CUT1 = FR('bridgeA/L1'), CUT2 = FR('bridgeA/L2');
const TB = at('bridgeB/L0'), TB3 = at('bridgeB/L3'), TI = at('instrumental'), END = at('finalChorus/L0');
const W = (sec: string, li: number) => words(sec, li).map((w) => w[0]);
const WA1 = W('bridgeA', 1), WB3 = W('bridgeB', 3);
const RISE_WORDS = [...W('bridgeA', 2), ...W('bridgeA', 3).slice(0, 3)];     // every word you speak up there / you learned from
const BEAT = TIMING.bar / 4, BEATS_INST = Array.from({ length: 12 }, (_, i) => TI + i * BEAT).filter((b) => b < END);
const THREAD0 = at('bridgeA/L3/w3'); // "everyone": the last rope leaves the river mouth and stays
const BLEND = 0.45;      // engine.ts BLEND_S
const PULL1 = 165.6;      // the pull-back has settled
const DIVE0 = 166.5, DIVE1 = END + 0.7; // the first cut's long dive down the thread (only its first, barely moving half second is left: see GROUND)
// CUT 2 (Nov 9: "every shot must carry an idea ... cut or shorten pure beauty holds" / "onto the ground"): ON the word "began" we cut to
// the hill again, closer: the thread she never let go of ends in the smallest child's hand, like a kite string, and the whole
// instrumental stays on the ground while the bloom gathers from there. (A shortened dive was tried first: 3 s from the wide to Europe
// strobed on the close city lights.) false = the first cut's dive into her through the instrumental.
const GROUND = true;
const CUT3 = GROUND ? Math.ceil(TI * 30) / 30 - 0.002 : END + 99; // the first frame of the `inst` slot = the frame "began" is sung on (167.12)
const REP_BEATS = BEATS_INST.filter((b) => b > CUT3 - 0.05), HOPS = [2, 5, 8].map((i) => REP_BEATS[i]).filter((x) => x !== undefined);

// ---- the camera: her disk on screen, per format (x, y = centre, r = radius; top = the highest point of her limb) ----
type V = { x: number; y: number; r: number; lat: number; lon: number; sun: P3 };
// night all through the bridge (the sun below her horizon: no warm rim, his star is the only warm thing)
const SUN1: P3 = [0.3, -0.5, -0.81], SUN3: P3 = [0.1, -0.5, -0.86], SUNW: P3 = [0.25, -0.4, -0.88];
const K0 = { x: 0, y: -1.6, r: 1.8, lat: 6, lon: 16 };  // shot 1 in 16:9 (the engine's own 9:16 reframe of it is good)
const SHOT3 = { '169': { r: 4.0, top0: -0.25, top1: -0.42 }, '916': { r: 3.0, top0: -0.2, top1: -0.32 } };
const WIDE = { '169': { x: -0.95, y: -0.5, r: 0.46 }, '916': { x: -0.12, y: -0.05, r: 0.34 } };
const DIVE = { '169': { x: -0.1, y: -0.08, r: 2.3 }, '916': { x: -0.02, y: -0.12, r: 1.5 } };
// the hill, second time (the instrumental): closer and lower than shot 2. HZ = how much bigger the people are; design camera + a settling push-in
const HZ = { '169': 1.5, '916': 1.4 };
const HILL2 = { '169': { fx: -0.62, crest: -0.5 }, '916': { fx: 0.04, crest: -0.36 } };
const zoom2 = (t: number) => 0.95 + 0.04 * (1 - Math.pow(1 - clamp01((t - CUT3) / 1.8), 3)) + 0.07 * clamp01((t - CUT3) / (END - CUT3)); // lands, then keeps creeping in
function hill2(t: number, fmt: Fmt): { v: V; zc: P; zf: number } { // v = the design camera (before the push-in), zc = what the push-in closes on
  const w = fmt === '169', r = (w ? 7 : 6) * HZ[fmt], h2 = HILL2[fmt];
  return { v: { x: w ? -0.35 : -0.1, y: h2.crest - r, r, lat: -44, lon: 21 + SPIN_DEG_S * (t - 152.4), sun: [0.2, -0.45, -0.87] }, zc: [h2.fx + 0.2 * HZ[fmt] * (w ? 0.4 : 0.33), h2.crest + 0.22], zf: zoom2(t) };
}
const DELTA: P = [45.2, 29.7]; // where the thread is tied: the Danube's mouth
function view(t: number, fmt: Fmt): V {
  const w = fmt === '169';
  if (t >= CUT3 && t < END) { const { v, zc, zf } = hill2(t, fmt); return { ...v, x: zc[0] + (v.x - zc[0]) * zf, y: zc[1] + (v.y - zc[1]) * zf, r: v.r * zf }; }
  if (t < CUT1) { // shot 1: the dome, a slow push
    const u = clamp01((t - T0) / (CUT1 - T0)), r = K0.r + 0.07 * u, y = 0.2 - r;
    return { x: 0, y: w ? y : y * 0.8, r: w ? r : r * 0.62, lat: K0.lat, lon: K0.lon + SPIN_DEG_S * (t - 149.8), sun: SUN1 };
  }
  if (t < CUT2) { // shot 2: the hill = her limb, close; the crest stays put while we push
    const u = (t - CUT1) / (CUT2 - CUT1), r = (w ? 7 : 6) + 0.5 * u;
    return { x: w ? -0.35 : -0.1, y: (w ? -0.42 : -0.3) - r, r, lat: -44, lon: 21 + SPIN_DEG_S * (t - 152.4), sun: [0.2, -0.45, -0.87] };
  }
  return view3(t, fmt);
}
// shot 3 -> the pull-back -> the wide -> the dive: one move
function view3(t: number, fmt: Fmt): V {
  const s3 = SHOT3[fmt], wd = WIDE[fmt], dv = DIVE[fmt];
  const tilt = smooth(154.3, 157.6, t), p = smoother(TB, PULL1, t), q = smoother(DIVE0, DIVE1, t);
  const top3 = lerp(s3.top0, s3.top1, tilt);
  let r = Math.exp(lerp(Math.log(s3.r), Math.log(wd.r), p)), x = lerp(0, wd.x, p), y = lerp(top3, wd.y + wd.r, p) - r;
  let lat = lerp(-22, 20, p), lon = lerp(16, 12, p);
  if (q > 0) { r = Math.exp(lerp(Math.log(wd.r), Math.log(dv.r), q)); x = lerp(wd.x, dv.x, q); y = lerp(wd.y, dv.y, q); lat = lerp(20, 45, q); lon = lerp(12, 33, q); }
  const sun: P3 = [lerp(SUN3[0], SUNW[0], p), lerp(SUN3[1], SUNW[1], p), lerp(SUN3[2], SUNW[2], p)];
  return { x, y, r, lat, lon: lon + SPIN_DEG_S * (t - 160), sun };
}
// the camera to hand the engine so that its 9:16 reframe (camera.ts camFor) gives exactly v
const K916 = ASPECT['916'] / ASPECT['169'];
function inv916(v: V) {
  const q = Math.abs(v.x) / K916, ax = q <= 0.24 ? (1 - Math.sqrt(1 - 4 * q)) / 2 : q / 0.4, side = Math.min(1, ax / 0.6);
  return { x: Math.sign(v.x) * ax, y: (v.y + 0.5 * side) / 0.8, r: v.r / 0.62 };
}
const camOf = (v: V): Cam => ({ x: v.x, y: v.y, r: v.r, lat: v.lat, lon: v.lon, roll: 0, sun: v.sun, par: [0, 0] });
const geo = (cam: Cam, g: P): { p: P; vis: boolean } => { const q = projGeo(cam, g); return { p: [q.x, q.y], vis: q.visible && q.z > 0.02 }; };

// ---- him: one warm star all through; in shot 3 the lights draw the machine around it; then he shrinks into the distance ----
const HIM1 = { '169': [0.72, 0.6] as P, '916': [0.2, 0.5] as P };
const HIM2 = { '169': [0.95, 0.6] as P, '916': [0.25, 0.52] as P };
const HIM3 = { '169': [0.05, 0.22] as P, '916': [0.0, 0.33] as P }; // the centre of his body (model origin) once he is drawn
const HIMR = { '169': [1.3, 0.7] as P, '916': [0.3, 0.62] as P };  // his star over the hill when we come back to it in the instrumental
const HIM_S = { '169': 0.92, '916': 0.48 };             // his size: half his wingspan (SPAN / 2 model units) in screen units
const HIM_REL = { '169': [4.46, 2.17] as P, '916': [1.24, 1.47] as P }; // far away: in her radii from her centre (so the dive leaves him behind)
const FAR_S = 0.17;
function him(t: number, fmt: Fmt, v: V): { p: P; s: number; far: number } {
  if (t < CUT1) return { p: HIM1[fmt], s: 0, far: 0 };
  if (t < CUT2) return { p: HIM2[fmt], s: 0, far: 0 };
  if (t >= CUT3 && t < END) return { p: HIMR[fmt], s: 0, far: 0 };
  const far = smoother(TB, 163.2, t), a = HIM3[fmt], rel = HIM_REL[fmt], wd = WIDE[fmt];
  const drift = 0.012 * Math.sin((t - CUT2) * 0.7); // he is never quite still
  // through the pull-back he travels to a fixed place on screen (far upper right); in the dive he stays where he is in space, so we leave him behind
  const b: P = t > DIVE0 ? [v.x + v.r * rel[0], v.y + v.r * rel[1]] : [wd.x + wd.r * rel[0], wd.y + wd.r * rel[1]];
  return { p: [lerp(a[0], b[0], far), lerp(a[1] + drift * (1 - far), b[1], far)], s: HIM_S[fmt] * lerp(1, FAR_S, far), far };
}
// HIM = the APPROVED 3D satellite (living_earth/him3d/him_build.py; cut-2 decision Nov 9: "3D HIM: APPROVED"), drawn as an outline of HER lights:
// the gold bus, the camera-turret head with his one big eye and brow, two wings of three hinged panels, the dish, the whip aerial, the
// engine bell. Model space is his Blender model (x = toward his left wing, y = back: he faces -y, z = up; his wingspan = SPAN), in the
// look-dev pose of br_learned (build/him3d/job_stills.json), without the idle wobble. earth_him_wire renders the real him over this
// plate with the same placement (see build/him_wire/positions/FROM_earth_c2_br.md and `himTrack` below): the outline is his own edges.
export const HIM_POSE = { yaw: -14, pitch: 20, roll: 5, head_pan: 8, head_tilt: 14, head_roll: 9,
  wingL: { twist: 18, flap: -5, fold: [7, 9, 12] }, wingR: { twist: 18, flap: -3, fold: [8, 10, 13] }, dish_az: 8, dish_el: 112 };
const SPAN = 5.37, HALF_SPAN = SPAN / 2; // him_render.py SPAN
type X3 = (p: P3) => P3;
const rotX = (d: number): X3 => { const c = Math.cos(d * D2R), s = Math.sin(d * D2R); return (p) => [p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c]; };
const rotY = (d: number): X3 => { const c = Math.cos(d * D2R), s = Math.sin(d * D2R); return (p) => [p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c]; };
const rotZ = (d: number): X3 => { const c = Math.cos(d * D2R), s = Math.sin(d * D2R); return (p) => [p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]]; };
const mv = (o: P3): X3 => (p) => [p[0] + o[0], p[1] + o[1], p[2] + o[2]];
const chain = (...f: X3[]): X3 => (p) => f.reduceRight((q, g) => g(q), p); // chain(A, B)(p) = A(B(p)): B is the child's own transform
const ID: X3 = (p) => p;
const toView: X3 = (p) => [p[0], p[2], -p[1]]; // him_render.py view_matrix: Rx(-90) first, so model (x, y, z) -> view (x, z, -y), z toward the camera
// a line of him: a polyline with evenly spaced points (the engine spreads a flow's lights evenly per vertex), in view-ready coordinates
type Seg = { pts: P3[]; ord: number; c: P3; rope: boolean };
const SEGS: Seg[] = [];
function resample(pts: P3[], n: number): P3[] {
  const d = [0]; for (let i = 1; i < pts.length; i++) d.push(d[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1], pts[i][2] - pts[i - 1][2]));
  const L = d[d.length - 1], out: P3[] = []; let j = 0;
  for (let k = 0; k < n; k++) { const s = (k / (n - 1)) * L; while (j < pts.length - 2 && d[j + 1] < s) j++; const u = (s - d[j]) / Math.max(1e-9, d[j + 1] - d[j]); out.push([lerp(pts[j][0], pts[j + 1][0], u), lerp(pts[j][1], pts[j + 1][1], u), lerp(pts[j][2], pts[j + 1][2], u)]); }
  return out;
}
const addSeg = (pts: P3[], ord: number, xf: X3 = ID, n = 0, rope = true): number => {
  const q = (n > 2 ? resample(pts, n) : pts).map((p) => toView(xf(p)));
  SEGS.push({ pts: q, ord, c: [q.reduce((s, p) => s + p[0], 0) / q.length, q.reduce((s, p) => s + p[1], 0) / q.length, q.reduce((s, p) => s + p[2], 0) / q.length], rope });
  return SEGS.length - 1;
};
const ringXZ = (c: P3, r: number, a0 = 0, a1 = 360, n = 25): P3[] => Array.from({ length: n }, (_, i) => { const a = (a0 + ((a1 - a0) * i) / (n - 1)) * D2R; return [c[0] + r * Math.cos(a), c[1], c[2] + r * Math.sin(a)] as P3; });
const ringXY = (c: P3, r: number, n = 25): P3[] => Array.from({ length: n }, (_, i) => { const a = (i / (n - 1)) * 2 * Math.PI; return [c[0] + r * Math.cos(a), c[1] + r * Math.sin(a), c[2]] as P3; });
const boxEdges = (x0: number, x1: number, y0: number, y1: number, z0: number, z1: number): [P3, P3][] => {
  const e: [P3, P3][] = [];
  for (const y of [y0, y1]) for (const z of [z0, z1]) e.push([[x0, y, z], [x1, y, z]]);
  for (const x of [x0, x1]) for (const y of [y0, y1]) e.push([[x, y, z0], [x, y, z1]]);
  for (const x of [x0, x1]) for (const z of [z0, z1]) e.push([[x, y0, z], [x, y1, z]]);
  return e;
};
const roundRectXZ = (cx: number, cz: number, w2: number, h2: number, r: number, y: number): P3[] => { // closed, in the XZ plane at depth y
  const out: P3[] = [];
  for (const [sx, sz, a0] of [[1, 1, 0], [-1, 1, 90], [-1, -1, 180], [1, -1, 270]] as [number, number, number][])
    for (let i = 0; i <= 5; i++) { const a = (a0 + 18 * i) * D2R; out.push([cx + sx * (w2 - r) + r * Math.cos(a), y, cz + sz * (h2 - r) + r * Math.sin(a)]); }
  out.push(out[0]); return out;
};
// the panels of his wings: filled with her light once their two ribs are drawn (quad corners in order; u = 0 at the body .. 1 at the tip)
type Cell = { q: [P3, P3, P3, P3]; i0: number; i1: number; u: number; side: number };
const CELLS: Cell[] = [];
let EYE_I = 0;          // the line that is his eye (the last thing drawn)
let EYE_C: P3 = [0, 0, 0]; // the centre of his eye, view-ready
{
  const P = HIM_POSE;
  // the bus (his torso), the chest plate, the engine bell
  boxEdges(-0.5, 0.5, -0.4, 0.4, -0.55, 0.55).forEach((e, i) => addSeg(e, 0.02 + 0.007 * i, ID, 0, i % 2 === 0));
  addSeg([[-0.3, -0.42, -0.245], [0.3, -0.42, -0.245], [0.3, -0.42, 0.215], [-0.3, -0.42, 0.215], [-0.3, -0.42, -0.245]], 0.12, ID, 17, false);
  for (const s of [-1, 1]) addSeg([[s * 0.07, 0, -0.585], [s * 0.215, 0, -0.885]], 0.13, ID, 0, false);
  addSeg(ringXY([0, 0, -0.885], 0.215, 17), 0.14, ID, 0, false);
  // his head: a camera turret on the neck (pan, then tilt / roll), the lens hood = his one big eye, the brow visor over it
  const head = chain(mv([0, -0.1, 0.7]), rotZ(P.head_pan), rotY(P.head_roll), rotX(P.head_tilt));
  addSeg(roundRectXZ(0, 0.27, 0.35, 0.23, 0.13, -0.3), 0.26, head, 33);
  addSeg(roundRectXZ(0, 0.27, 0.35, 0.23, 0.13, 0.26), 0.3, head, 33, false);
  for (const [x, z] of [[-0.3, 0.46], [0.3, 0.46], [-0.3, 0.08], [0.3, 0.08]]) addSeg([[x, -0.3, z], [x, 0.26, z]], 0.32, head, 0, false);
  addSeg([[0, 0, -0.06], [0, 0, 0.04]], 0.24, head, 0, false); // the neck
  // the dish (his ear / hat) on its mast, and the whip aerial
  const dish = chain(mv([0.26, 0.24, 1.0]), rotZ(P.dish_az), rotX(P.dish_el)), rimz = (0.42 * 0.42) / 1.2 + 0.07;
  addSeg([[0.26, 0.24, 0.58], [0.26, 0.24, 1.0]], 0.5, ID, 0, false);
  addSeg(ringXY([0, 0, rimz], 0.42, 33), 0.55, dish);
  addSeg([[0, 0, 0.07], [0, 0, 0.4]], 0.6, dish, 0, false);
  addSeg([[-0.34, 0.28, 0.64], [-0.34, 0.28, 1.86]], 0.64, ID);
  // the wings: a yoke, then three hinged panels a side (frame, two cross ribs, the spar)
  for (const [s, wp] of [[1, P.wingL], [-1, P.wingR]] as [number, typeof P.wingL][]) {
    const root = chain(mv([s * 0.555, 0, 0.08]), rotY(-s * wp.flap), rotX(wp.twist));
    addSeg([[0, 0, 0], [s * 0.2, 0, 0]], 0.16, root, 0, false); addSeg([[s * 0.2, 0, -0.34], [s * 0.2, 0, 0.34]], 0.18, root);
    let par = root;
    for (let i = 0; i < 3; i++) {
      const h = chain(par, mv([s * (i === 0 ? 0.22 : 0.64), 0, 0]), rotZ(-s * wp.fold[i])), o = 0.24 + 0.2 * i, z = 0.47;
      const i0 = addSeg([[s * 0.02, 0, -z], [s * 0.02, 0, z]], o, h), i1 = addSeg([[s * 0.62, 0, -z], [s * 0.62, 0, z]], o + 0.16, h);
      for (const zz of [-z, z]) addSeg([[s * 0.02, 0, zz], [s * 0.62, 0, zz]], o + 0.06, h);
      addSeg([[s * 0.02, 0, 0], [s * 0.62, 0, 0]], o + 0.08, h, 0, false);
      for (const x of [0.22, 0.42]) addSeg([[s * x, 0, -z], [s * x, 0, z]], o + 0.04 + 0.16 * x, h, 0, false);
      const c = (x: number, zz: number) => toView(h([s * x, 0, zz]));
      CELLS.push({ q: [c(0.02, -z), c(0.62, -z), c(0.62, z), c(0.02, z)], i0, i1, u: (i + 0.5) / 3, side: s });
      par = h;
    }
  }
  // his face comes last ("you learned from everyone"): the eye opens, then the brow
  EYE_I = addSeg(ringXZ([0, -0.445, 0.27], 0.225, 90, 450, 33), 0.9, head);
  addSeg(ringXZ([0, -0.445, 0.27], 0.1, 90, 450, 17), 0.94, head, 0, false);
  addSeg(ringXZ([0, -0.47, 0.27], 0.275, 28, 152, 17), 0.97, head, 0, false);
  EYE_C = toView(head([0, -0.445, 0.27]));
}
// view-ready point -> flat (orthographic), exactly him_render.py view_matrix: roll (Z) x pitch (X) x yaw (Y)
const proj3 = (p: P3, yaw: number, pitch: number, roll: number): P => {
  const cy = Math.cos(yaw), sy = Math.sin(yaw), x1 = p[0] * cy + p[2] * sy, z1 = -p[0] * sy + p[2] * cy, y1 = p[1] * Math.cos(pitch) - z1 * Math.sin(pitch);
  const cr = Math.cos(roll), sr = Math.sin(roll); return [x1 * cr - y1 * sr, x1 * sr + y1 * cr];
};
const YAW0 = HIM_POSE.yaw * D2R, PITCH = HIM_POSE.pitch * D2R, ROLL = HIM_POSE.roll * D2R;
const flat = (p: P3): P => { const q = proj3(p, YAW0, PITCH, ROLL); return [q[0] / HALF_SPAN, q[1] / HALF_SPAN]; }; // in half wingspans: x S = screen units
const FLAT = SEGS.map((sg) => sg.pts.map(flat));
const EYE_F = flat(EYE_C);
// how many lights each line of him is made of (per run): set once, at his full size
const SEG_N: Partial<Record<Fmt, number[]>> = {};
function segN(fmt: Fmt): number[] {
  const hit = SEG_N[fmt]; if (hit) return hit;
  const S = HIM_S[fmt] * 720, dens = fmt === '169' ? 3.0 : 2.2;
  return (SEG_N[fmt] = FLAT.map((f) => Math.max(2, Math.round((plen(f) * S) / dens / 2))));
}
// how many points fill each panel (across, along): set once, at his full size, about one soft point every 9 px of a 1440 frame
const CELL_GRID: Partial<Record<Fmt, [number, number][]>> = {};
function cellGrid(fmt: Fmt): [number, number][] {
  const hit = CELL_GRID[fmt]; if (hit) return hit;
  const S = HIM_S[fmt] * 720, sp = fmt === '169' ? 10.5 : 8;
  return (CELL_GRID[fmt] = CELLS.map((ce) => { const q = ce.q.map(flat);
    return [Math.max(2, Math.round((Math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]) * S) / sp)), Math.max(3, Math.round((Math.hypot(q[3][0] - q[0][0], q[3][1] - q[0][1]) * S) / sp) + 1)] as [number, number]; }));
}
const HR = rng(5150), SEGR = SEGS.map(() => [HR(), HR(), HR()]);
// when each line of him is drawn: the box first, then outward along the wings and fins, a batch leaving her on every sung word
const TRAVEL = 1.15, DRAW = 0.45;
// (cut 2: everything has left her by "there", so he is complete ON "everyone" and holds at full size before the pull-back; the thread then rises alone)
const LAUNCH = SEGS.map((s, i) => RISE_WORDS[Math.min(5, Math.floor(s.ord * 6.6))] + 0.1 * SEGR[i][0]);
LAUNCH[EYE_I] = at('bridgeA/L3/w3') + 0.03 - TRAVEL * 0.94 - DRAW; // his eye closes exactly on "everyone"
const EYE_T = LAUNCH[EYE_I] + TRAVEL * 0.94 + DRAW; // his eye is complete
// where the lights come from: real places in frame (cities = warm = people, rivers = her cyan/violet)
const SOURCES: { g: P; river: boolean }[] = [
  ...([[51.5, -0.1], [48.86, 2.35], [40.42, -3.7], [41.9, 12.5], [45.46, 9.19], [52.52, 13.4], [48.2, 16.37], [47.5, 19.04], [41.0, 28.98], [37.98, 23.73], [52.23, 21.0], [50.45, 30.52],
    [55.75, 37.62], [41.39, 2.17], [40.85, 14.27], [48.14, 11.58], [44.43, 26.1], [44.8, 20.47], [52.37, 4.9], [38.72, -9.14], [36.75, 3.06], [36.8, 10.18], [39.93, 32.86], [43.3, 5.37],
    [50.08, 14.44], [53.55, 10.0], [59.33, 18.07], [45.76, 4.84], [50.85, 4.35], [53.35, -6.26], [59.94, 30.31], [47.0, 28.85], [46.48, 30.73], [42.7, 23.32], [45.8, 16.0], [43.85, 18.4]] as P[]).map((g) => ({ g, river: false })),
  ...([[48.4, 10], [48.3, 14.3], [45.8, 18.9], [43.75, 26], [45.05, 9.7], [44.95, 12.4], [50, 8.2], [51.95, 4.3], [49, 32.5], [46.5, 32.3], [43.9, 4.8], [54.3, 18.9], [39.5, -7], [49.4, 0.5],
    [53.9, 9], [41.2, 0.6], [42.5, 12.5], [47.8, 35.1], [44.6, 22.7], [52, 30.8]] as P[]).map((g) => ({ g, river: true })),
];
const LIFTR = SOURCES.map(() => [HR(), HR(), HR()]);
const SRC_OF: Partial<Record<Fmt, number[]>> = {};
function srcOf(fmt: Fmt): number[] { // left lights go to his left side, so the ropes never cross (decided once, at a fixed time)
  const hit = SRC_OF[fmt]; if (hit) return hit;
  const cam = camOf(view(155.6, fmt)), A = ASPECT[fmt];
  const vis = SOURCES.map((s, i) => ({ i, q: geo(cam, s.g) })).filter((s) => s.q.vis && Math.abs(s.q.p[0]) < A * 0.97 && s.q.p[1] > -0.98).sort((a, b) => a.q.p[0] - b.q.p[0]);
  const order = SEGS.map((_s, i) => ({ i, x: FLAT[i][0][0] })).sort((a, b) => a.x - b.x);
  const out = new Array<number>(SEGS.length).fill(0);
  order.forEach((o, k) => { out[o.i] = vis.length ? vis[Math.min(vis.length - 1, Math.floor(((k + 0.5) / order.length) * vis.length))].i : 0; });
  return (SRC_OF[fmt] = out);
}
// a smooth curve through points (Catmull-Rom), n samples
function curve(pts: P[], n: number): P[] {
  const g = (i: number) => pts[Math.max(0, Math.min(pts.length - 1, i))], out: P[] = [];
  for (let k = 0; k < n; k++) {
    const f = (k / (n - 1)) * (pts.length - 1), i = Math.min(pts.length - 2, Math.floor(f)), u = f - i, p0 = g(i - 1), p1 = g(i), p2 = g(i + 1), p3 = g(i + 2);
    const c = (a: number, b: number, cc: number, d: number) => 0.5 * (2 * b + (-a + cc) * u + (2 * a - 5 * b + 4 * cc - d) * u * u + (-a + 3 * b - 3 * cc + d) * u * u * u);
    out.push([c(p0[0], p1[0], p2[0], p3[0]), c(p0[1], p1[1], p2[1], p3[1])]);
  }
  return out;
}
const screen = (pts: P[]) => ({ space: 'screen' as const, pts });
const HALF = (n: number) => (0.5 * (1 + 1 / n)) / Math.max(1, n - 1); // half the spacing of a flow of n points with tail 1 + 1/n
const plen = (pts: P[]) => pts.slice(1).reduce((s, p, i) => s + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);
// a line of separate lights, evenly lit (two opposite runs), about one light every `px` pixels of a 1440 frame
function line(out: Flow[], pts: P[], o: { color: RGB; size: number; intensity: number; px?: number }) {
  if (o.intensity <= 0.004) return;
  const n = Math.max(2, Math.round((plen(pts) * 720) / (o.px ?? 2.6) / 2));
  out.push(flow(screen(pts), 1 + 0.5 / n, { tail: 1 + 1 / n, count: n, color: o.color, size: o.size, intensity: o.intensity }));
  out.push(flow(screen(pts.slice().reverse()), 1 + 0.5 / n + HALF(n), { tail: 1 + 1 / n, count: n, color: o.color, size: o.size, intensity: o.intensity }));
}

// ---- shot 2: the hill (engine version of the ground beat; polish Nov 9: filled figures of light, a tree of light, grass) ----
// a filled band of light from a to b (widths wa, wb): hatch lines a few pixels apart, alternate directions, so the fill is even.
// head just past the end hides the engine's big head point (no dots along the edges)
function band(out: Flow[], a: P, b: P, wa: number, wb: number, o: { color: RGB; intensity: number; size?: number; px?: number }) {
  if (o.intensity <= 0.004) return;
  const px = o.px ?? 3.6, dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1e-6, nx = -dy / L, ny = dx / L;
  const K = Math.max(1, Math.round((Math.max(wa, wb) * 720) / px)), n = Math.max(3, Math.round((L * 720) / px) + 1);
  for (let j = 0; j < K; j++) {
    const u = K === 1 ? 0 : (j / (K - 1)) * 2 - 1, p: P = [a[0] + nx * wa * 0.5 * u, a[1] + ny * wa * 0.5 * u], q: P = [b[0] + nx * wb * 0.5 * u, b[1] + ny * wb * 0.5 * u];
    out.push(flow(screen(j % 2 ? [q, p] : [p, q]), 1 + 0.5 / n, { tail: 1 + 1 / n, count: n, color: o.color, size: o.size ?? 18, intensity: o.intensity }));
  }
}
const disc = (out: Flow[], c: P, rx: number, ry: number, o: { color: RGB; intensity: number; size?: number; px?: number }) => {
  const K = Math.max(2, Math.round((2 * ry * 720) / (o.px ?? 3.6)));
  for (let j = 0; j < K; j++) { const v = ((j + 0.5) / K) * 2 - 1, hw = rx * Math.sqrt(1 - v * v); band(out, [c[0] - hw, c[1] + ry * v], [c[0] + hw, c[1] + ry * v], 0, 0, o); }
};
// the tree of light on the crest: a trunk, three levels of branches, hanging strands with drops of light running down them
type Twig = { a: P; b: P; w0: number; w1: number; lvl: number; tip: boolean; r: number };
const TREE: Twig[] = [];
{
  const R = rng(1977);
  const grow = (a: P, ang: number, len: number, w: number, lvl: number) => {
    const b: P = [a[0] + len * Math.sin(ang), a[1] + len * Math.cos(ang)], w1 = w * 0.62;
    TREE.push({ a, b, w0: w, w1, lvl, tip: lvl >= 4, r: R() });
    if (lvl >= 4) return;
    const kids = lvl === 0 ? 3 : 2 + (R() < 0.45 ? 1 : 0);
    for (let k = 0; k < kids; k++) { const sp = (k / (kids - 1) - 0.5) * (lvl === 0 ? 1.5 : 1.25) + (R() - 0.5) * 0.3; grow(b, ang * 0.55 + sp, len * (0.6 + 0.16 * R()), w1, lvl + 1); }
  };
  grow([0, 0], 0.07, 0.33, 0.056, 0); // unit tree: about 1 tall, 1.1 wide
}
const GRASS = (() => { const R = rng(808); return Array.from({ length: 200 }, () => [R(), R(), R(), R()]); })();
// rep = the second visit (the instrumental): closer (pz = how much bigger), nobody points: the smallest child holds the thread; g = the bloom gathering 0..1
type HillO = { fx: number; H: number; pz: number; rep: boolean; g: number };
const FLOWERS = (() => { const R = rng(2026); return Array.from({ length: 66 }, () => [R(), R(), R(), R(), R()]); })();
function hill(t: number, fmt: Fmt, v: V, hp: P, flows: Flow[], sparks: Spark[], o?: HillO): P {
  const w = fmt === '169', A = ASPECT[fmt], gy = (x: number) => v.y + Math.sqrt(Math.max(0, v.r * v.r - (x - v.x) * (x - v.x))) + 0.002;
  const col = mix3(C.her, WHITE, 0.3), breathe = 0.92 + 0.08 * Math.sin(t * 2.1), lt = t - CUT1;
  const fx = o ? o.fx : w ? -0.42 : 0.1, H = o ? o.H : w ? 0.4 : 0.33; // the grown-up: where they stand, how tall
  const pz = o ? o.pz : 1, rp = !!o && o.rep, gb = o ? o.g : 0, AX = A / (rp ? 0.9 : 1); // (the push-in starts a little wide: cover past the frame edge)
  const kid3 = fx + 0.5 * H; // where the smallest one stands
  // the second visit: on every beat a wave of light runs out through the grass from the child's feet
  const beatWave = (x: number) => rp ? REP_BEATS.reduce((sum, tb) => sum + (t < tb ? 0 : smooth(0, 0.14, t - tb) * Math.exp(-Math.pow((Math.abs(x - kid3) - 2.4 * (t - tb)) / 0.17, 2)) * Math.exp(-(t - tb) / 1.1)), 0) : 0; // (a short attack: no one-frame flash on the beat)
  // grass along the crest: blades of her light leaning in a slow wind, thicker around the people and the tree
  for (const g of GRASS) {
    const x = -AX + 2 * AX * g[0], near = Math.exp(-Math.pow((x - fx) / ((w ? 0.9 : 0.5) * pz), 2)), bw = beatWave(x), hgt = (0.018 + 0.05 * g[1] * g[1]) * (0.6 + 0.9 * near) * (w ? 1 : 0.8) * pz * (1 + 0.3 * bw);
    const sway = 0.35 * Math.sin(lt * 1.3 + x * 4.0 + g[2] * 2.0) + 0.5 * (g[3] - 0.5), y0 = gy(x) - 0.004;
    flows.push(flow(screen(curve([[x, y0], [x + hgt * 0.12 * sway, y0 + hgt * 0.55], [x + hgt * 0.5 * sway, y0 + hgt]], 5)), 1, { tail: 1.25, count: rp ? 11 : 14, size: 7 * (rp ? 1.3 : 1), color: g[2] < 0.22 ? C.violet : mix3(C.teal, C.her, g[3]), intensity: (0.5 + 0.35 * near) * (rp && !w ? 0.8 : 1) * (1 + 0.5 * gb + 1.1 * bw) }));
  }
  // the second visit: flowers of light come up along the crest, spreading outward from where the child stands (she gathers toward full bloom)
  if (rp) for (const f of FLOWERS) {
    const x = -AX + 2 * AX * f[0], dist = Math.abs(x - kid3), born = CUT3 + 0.35 + (dist / (AX + Math.abs(kid3))) * (END - CUT3 - 1.5) + 0.25 * f[1], u = (t - born) / 0.5; if (u <= 0) continue;
    const grow = backOut(u), hgt = (0.08 + 0.15 * f[2]) * pz * grow, sway = 0.25 * Math.sin(lt * 1.2 + x * 3.1 + f[3] * 6), y0 = gy(x) - 0.004, top: P = [x + hgt * 0.35 * sway, y0 + hgt];
    const c: RGB = f[4] < 0.38 ? mix3(C.violet, WHITE, 0.25) : f[4] < 0.72 ? mix3(C.her, WHITE, 0.45) : mix3(C.teal, WHITE, 0.3), tw = 0.85 + 0.25 * Math.sin(lt * (2 + 3 * f[3]) + f[1] * 9) + 0.5 * beatWave(x);
    flows.push(flow(screen(curve([[x, y0], [x + hgt * 0.1 * sway, y0 + hgt * 0.55], top], 5)), 1, { tail: 1.2, count: 9, size: 7, color: mix3(C.teal, C.her, 0.5), intensity: 0.55 * clamp01(u * 2) }));
    flows.push(flow(screen([top, [x, y0]]), 0, { tail: 1, count: 1, size: (8 + 6 * f[2]) * (w ? 1 : 0.72) * clamp01(grow), color: c, intensity: 1.0 * tw * clamp01(u * 1.5) }));
    flows.push(flow(screen([top, [x, y0]]), 0, { tail: 1, count: 1, size: (24 + 18 * f[2]) * (w ? 1 : 0.72) * clamp01(grow), color: c, intensity: 0.17 * tw * clamp01(u * 1.5) }));
  }
  // the tree, behind them to the left
  {
    const tzs = rp ? (w ? 1.3 : 0.98) : 1, tx = fx - (rp ? (w ? 0.52 * pz * 0.9 : 0.41) : w ? 0.52 : 0.38), ts = (w ? 0.74 : 0.5) * tzs, ty = gy(tx) - 0.006, P2 = (p: P, bend = 0): P => [tx + ts * (p[0] + bend * p[1] * p[1]), ty + ts * p[1]];
    const wind = 0.02 * Math.sin(lt * 0.9);
    TREE.forEach((tw, i) => {
      const a = P2(tw.a, wind), b = P2(tw.b, wind), c: RGB = mix3(C.her, tw.lvl >= 2 ? C.violet : WHITE, tw.lvl >= 2 ? 0.35 : 0.2);
      band(flows, a, b, tw.w0 * ts, tw.w1 * ts, { color: c, intensity: (tw.lvl >= 3 ? 0.3 : 0.135) * breathe, size: (tw.lvl >= 3 ? 10 : 17) * tzs * (rp ? 1.12 : 1), px: 4.0 * tzs * (rp ? 1.12 : 1) });
      if (!tw.tip) return;
      // a blossom of light at every tip, each twinkling on its own
      flows.push(flow(screen([b, a]), 0, { tail: 1, count: 1, size: (7.5 + 4 * tw.r) * tzs * (1 + (w ? 0.5 : 0.2) * gb), color: i % 4 === 0 ? C.violet : mix3(C.her, WHITE, 0.35), intensity: (0.75 + 0.45 * Math.sin(lt * (1.5 + 2 * tw.r) + i)) * (1 + (w ? 0.7 : 0.3) * gb) })); // (blossoming harder as the bloom gathers)
      if (i % 2) return;
      // a hanging strand from the branch tip, swaying; a drop of light runs down it now and then
      const L = ts * (0.14 + 0.24 * tw.r), sw = 0.03 * Math.sin(lt * 1.1 + i * 1.7) * ts, strand = curve([b, [b[0] + sw * 0.4, b[1] - L * 0.5], [b[0] + sw, b[1] - L]], 6);
      flows.push(flow(screen(strand.slice().reverse()), 1, { tail: 1.15, count: 20, size: 6.5, color: i % 3 ? C.her : C.violet, intensity: 0.5 }));
      const cyc = (lt * (0.22 + 0.2 * tw.r) + tw.r * 7) % 1;
      flows.push(flow(screen(strand), cyc * 1.2, { tail: 0.16, count: 5, size: 9, color: mix3(C.her, WHITE, 0.5), intensity: 1.1 * Math.sin(Math.PI * Math.min(1, cyc * 1.15)) }));
    });
  }
  // a person: a long coat, legs, a round head, two arms. All filled with her light
  const person = (px0: number, h: number, armU: number, look: number, other: P | null, k: number, lift = 0) => {
    const y0 = gy(px0) + lift, I = (rp ? 0.2 : 0.15) * k * breathe, o = { color: col, intensity: I, px: 3.6 * pz * (rp ? 1.08 : 1), size: 18 * pz * (rp ? 1.08 : 1) };
    const hem: P = [px0, y0 + 0.2 * h], waist: P = [px0 + 0.005 * h, y0 + 0.55 * h], sh: P = [px0 + 0.012 * h, y0 + 0.79 * h], head: P = [sh[0] + look * 0.03 * h, sh[1] + 0.135 * h];
    for (const sx of [-1, 1]) band(flows, [px0 + sx * 0.06 * h, y0], [px0 + sx * 0.05 * h, y0 + 0.24 * h], 0.06 * h, 0.07 * h, o);                 // legs
    band(flows, hem, waist, 0.3 * h, 0.17 * h, o); band(flows, waist, sh, 0.17 * h, 0.2 * h, o);                                                // the coat
    disc(flows, head, 0.078 * h, 0.085 * h, { ...o, intensity: I * 1.15 });
    // the pointing arm: from hanging at the side up to the star (a small overshoot, then held)
    const s1: P = [sh[0] + 0.085 * h, sh[1] - 0.03 * h], tgt = Math.atan2(hp[0] - s1[0], hp[1] - s1[1]), ang = lerp(Math.PI * 0.9, tgt, backOut(armU)), L = 0.4 * h;
    const hand: P = [s1[0] + L * Math.sin(ang), s1[1] + L * Math.cos(ang)];
    band(flows, s1, hand, 0.062 * h, 0.042 * h, o);
    const s2: P = [sh[0] - 0.085 * h, sh[1] - 0.03 * h];
    band(flows, s2, other ?? [s2[0] - 0.05 * h, s2[1] - 0.36 * h], 0.062 * h, 0.042 * h, o);
    return { hand, head };
  };
  const armA = rp ? 0 : smooth(WA1[0] + 0.05, WA1[0] + 0.7, t), kx = fx - 0.52 * H, kh = 0.56 * H; // (second visit: the grown-up's arm is down; they all just look up)
  const kidHand: P = [kx + 0.2 * kh, gy(kx) + 0.86 * kh];              // the child reaches up to the grown-up's hand
  const adult = person(fx, H, armA, 1, kidHand, 1);
  { // the child holding the grown-up's hand, head tipped up to the star
    const y0 = gy(kx), I = (rp ? 0.2 : 0.15) * breathe, o = { color: col, intensity: I, px: 3.6 * pz * (rp ? 1.08 : 1), size: 18 * pz * (rp ? 1.08 : 1) }, sh: P = [kx + 0.01 * kh, y0 + 0.76 * kh];
    for (const sx of [-1, 1]) band(flows, [kx + sx * 0.07 * kh, y0], [kx + sx * 0.06 * kh, y0 + 0.26 * kh], 0.075 * kh, 0.085 * kh, o);
    band(flows, [kx, y0 + 0.22 * kh], sh, 0.34 * kh, 0.22 * kh, o);
    disc(flows, [sh[0] + 0.05 * kh, sh[1] + 0.16 * kh], 0.105 * kh, 0.11 * kh, { ...o, intensity: I * 1.15 });
    band(flows, [sh[0] + 0.09 * kh, sh[1] - 0.03 * kh], kidHand, 0.07 * kh, 0.05 * kh, o);
    band(flows, [sh[0] - 0.1 * kh, sh[1] - 0.03 * kh], [sh[0] - 0.15 * kh, sh[1] - 0.36 * kh], 0.07 * kh, 0.05 * kh, o);
  }
  // the smallest one copies the point a beat later (the button), with a little hop
  const hop = rp ? HOPS.reduce((m, tb) => m + 0.04 * H * Math.sin(Math.PI * clamp01((t - tb + 0.06) / 0.34)), 0) : 0.035 * H * Math.sin(Math.PI * clamp01((t - WA1[3] - 0.1) / 0.36));
  const small = person(kid3, (rp ? 0.5 : 0.44) * H, rp ? 1 : smooth(WA1[3] + 0.1, WA1[3] + 0.6, t), 1, null, rp ? 1.05 : 0.95, hop);
  if (rp) { sparks.push({ x: small.hand[0], y: small.hand[1], size: 9 * pz, color: mix3(C.her, WHITE, 0.5), intensity: 1.0 * breathe }); return small.hand; } // the thread is in this hand (drawn by the scene)
  // a dotted line of light climbs from the fingertip to his star on "where you've gone"
  const a = adult.hand, dx = hp[0] - a[0], dy = hp[1] - a[1], head = smooth(WA1[2] + 0.25, WA1[5] + 0.05, t) * 0.94;
  if (head > 0.01) flows.push(flow(screen([[a[0] + dx * 0.05, a[1] + dy * 0.05], [a[0] + dx, a[1] + dy]]), head, { tail: head, dash: Math.max(1, Math.round(22 * head)), count: Math.round(380 * head) + 8, size: 11, color: mix3(C.her, WHITE, 0.25), intensity: 1.0 }));
  sparks.push({ x: a[0], y: a[1], size: 9, color: mix3(C.her, WHITE, 0.5), intensity: 0.9 * armA * breathe });  // the fingertip
  return a;
}

// ---- the thread: a strand from the river mouth to him, sagging a little ----
const threadPath = (cam: Cam, hp: P, n = 18): P[] => strandPath(geo(cam, DELTA).p, hp, n);
function strandPath(a: P, hp: P, n = 18, k = 0.1): P[] {
  const dx = hp[0] - a[0], dy = hp[1] - a[1], L = Math.hypot(dx, dy) || 1e-6;
  const nx = dy / L, ny = -dx / L, sag = k * L;
  return curve([a, [a[0] + dx * 0.3 + nx * sag * 0.8, a[1] + dy * 0.3 + ny * sag * 0.8], [a[0] + dx * 0.7 + nx * sag, a[1] + dy * 0.7 + ny * sag], hp], n);
}
// a few of her rivers around the place the thread is tied (mouth last)
const DANUBE: P[] = [[48.1, 8.5], [48.4, 10], [48.9, 12.1], [48.3, 14.3], [48.2, 16.4], [47.8, 18.8], [45.8, 18.9], [44.8, 20.5], [44.6, 22.7], [43.7, 23.7], [43.75, 26], [44.1, 27.3], [45.3, 28.2], [45.2, 29.7]];
const DNIEPER: P[] = [[55.2, 33.5], [53.9, 30.3], [52, 30.8], [50.45, 30.5], [49, 32.5], [48.4, 35], [47.8, 35.1], [46.8, 33.2], [46.5, 32.3]];
const VOLGA: P[] = [[57, 34], [56.3, 44], [55.8, 49], [53.2, 50.1], [51.5, 46], [48.7, 44.5], [46.3, 48]];
const RHINE: P[] = [[47.6, 7.6], [49, 8.4], [50, 8.2], [50.9, 6.96], [51.8, 6.1], [51.95, 4.3]];
const TIGRIS: P[] = [[38.5, 39.5], [37.9, 40.2], [36.3, 43.1], [33.3, 44.4], [32.5, 45.8], [31, 47.4], [30, 48.5]];

// ---- the scene ----
const scene: Builder = (c) => {
  const t = c.t, fmt = c.fmt, w = fmt === '169';
  if (t >= END - 1e-3) { const ve = view3(END, fmt); return { grade: { ...look(END, fmt, him(END, fmt, ve)), ...grade(END, ve.r) } }; } // past the range (the engine's blend into the final chorus): no camera, no lights of ours
  const v = view(t, fmt), cam = camOf(v), k = w ? v : inv916(v);
  const h = him(t, fmt, v), flows: Flow[] = [], sparks: Spark[] = [], pulses: Pulse[] = [];
  const star = (size: number, intensity: number, p: P = h.p) => sparks.push({ x: p[0], y: p[1], size, color: C.his, intensity }, { x: p[0], y: p[1], size: size * 4.2, color: C.his, intensity: intensity * 0.16 }); // his star: a core and a wide soft halo
  if (t < CUT1) {
    // shot 1: quiet. Light runs slowly down two of her rivers; his star twinkles once on "night" when the sky has cleared around him
    const tw = env(t, at('bridgeA/L0/w6'), 0.12, 0.7);
    star(19 + 7 * tw, 1.9 + 1.5 * tw);
    for (const [riv, ph] of [[DANUBE, 0], [RIVERS.nile, 0.55], [RHINE, 0.3]] as [P[], number][]) flows.push(flow({ space: 'geo', pts: riv }, (((t - T0) * 0.22 + ph) % 1) * 1.35, { tail: 0.35, size: 9, intensity: 0.55, count: 140 }));
  } else if (t < CUT2) {
    const ans = env(t, WA1[5] + 0.05, 0.12, 0.8); // the star answers on "gone"
    star(19 + 10 * ans, 1.9 + 2.2 * ans);
    hill(t, fmt, v, h.p, flows, sparks);
  } else if (t >= CUT3) {
    // the instrumental, on the ground: the thread comes down out of the sky into the smallest child's hand. The child gives it a
    // little hop and a tug, a bead of light climbs to him, his star answers; around them her flowers come up on the beat
    const { v: vd, zc, zf } = hill2(t, fmt), Z = (q: P): P => [zc[0] + (q[0] - zc[0]) * zf, zc[1] + (q[1] - zc[1]) * zf];
    const hf: Flow[] = [], hs: Spark[] = [], g = smooth(CUT3, END, t);
    const hand = Z(hill(t, fmt, vd, h.p, hf, hs, { fx: HILL2[fmt].fx, H: (w ? 0.4 : 0.33) * HZ[fmt], pz: HZ[fmt], rep: true, g }));
    for (const f of hf) flows.push({ ...f, size: f.size * zf, path: f.path.space === 'screen' ? { space: 'screen', pts: f.path.pts.map(Z) } : f.path }); // the push-in (the sky does not come closer: his star stays put)
    for (const x of hs) sparks.push({ ...x, x: Z([x.x, x.y])[0], y: Z([x.x, x.y])[1], size: x.size * zf });
    const tug = HOPS.reduce((m, tb) => m + Math.sin(Math.PI * clamp01((t - tb + 0.06) / 0.5)), 0), ans = HOPS.reduce((m, tb) => m + env(t, tb + 1.1, 0.18, 0.8), 0);
    star(19 + (w ? 9 : 5) * Math.min(1, ans), 1.9 + (w ? 2.0 : 1.2) * Math.min(1, ans)); // his star answers each bead (gently: no flash, least of all in the narrow frame)
    const path = strandPath(hand, h.p, 18, 0.1 - 0.035 * Math.min(1, tug)), n = Math.max(40, Math.min(1050, Math.round((plen(path) * 720) / 2.6 / 2))), I = 1.0 + 0.3 * g, sz = 12.5;
    flows.push(flow(screen(path), 1 + 0.5 / n, { tail: 1 + 1 / n, count: n, size: sz, color: C.her, intensity: I }), flow(screen(path.slice().reverse()), 1 + 0.5 / n + HALF(n), { tail: 1 + 1 / n, count: n, size: sz, color: C.her, intensity: I }));
    { const ns = Math.round(n / 3), os = { tail: 1 + 4 / ns, count: ns, size: sz * 3.2, color: mix3(C.her, C.violet, 0.25), intensity: 0.11 }; flows.push(flow(screen(path), 1 + 2 / ns, os), flow(screen(path.slice().reverse()), 1 + 2 / ns, os)); }
    HOPS.forEach((tb) => { const u = (t - tb - 0.12) / 1.0; if (u > 0 && u < 1.08) flows.push(flow(screen(path), u, { tail: 0.07, count: 22, size: 17, color: mix3(C.her, WHITE, 0.4), intensity: 1.7 * smooth(0, 0.08, u) * (1 - smooth(0.98, 1.08, u)) })); });
  } else {
    // shot 3 onward
    const S = h.s, src = srcOf(fmt); // (no turning: the real him is rendered over this in exactly this pose)
    const pf = (q: P): P => [h.p[0] + S * q[0], h.p[1] + S * q[1]], pt = (p: P3): P => pf(flat(p));
    const limbY = (x: number) => v.y + Math.sqrt(Math.max(0, v.r * v.r - (x - v.x) * (x - v.x)));
    const big = clamp01((S - 0.1) / 0.4), lsize = lerp(7.5, w ? 13 : 10.5, big);
    const inFrame = Math.abs(h.p[0]) < ASPECT[fmt] + 1.15 * S && Math.abs(h.p[1]) < 1 + 1.15 * S;   // once the dive has left him outside the frame none of his lights are drawn
    const gone = inFrame ? 1 - smooth(DIVE0 + 0.5, DIVE0 + 3.2, t) : 0; // he has left the frame in the dive
    const segn = segN(fmt);
    if (gone > 0.01) SEGS.forEach((sg, i) => {
      const pts = FLAT[i].map(pf), a = pts[0], s = SOURCES[src[i]], tl = LAUNCH[i], colS: RGB = SEGR[i][1] < 0.3 ? C.violet : C.her; // her people's words: cyan / violet, never gold (pitch decision 05)
      // the rope of light from her to this line's start
      const e = (t - tl) / TRAVEL;
      if (sg.rope && e > 0 && e < 1.45) {
        const g0 = geo(cam, s.g), sp: P = g0.vis ? g0.p : [g0.p[0], limbY(g0.p[0])], ph = SEGR[i][2] * 6.28, bx = (u: number) => 0.03 * Math.sin(Math.PI * u) * Math.sin(u * 9 + ph);
        const dx = a[0] - sp[0], dy = a[1] - sp[1];
        const path = curve([sp, [sp[0] + bx(0.2), sp[1] + 0.2 * dy + 0.05], [sp[0] + dx * 0.45 + bx(0.55), sp[1] + dy * 0.62], a], 14);
        const head = smooth(0, 1, e / 1.0) * 1.0 + Math.max(0, e - 1) * 0.9;
        flows.push(flow(screen(path), head, { tail: 0.36, count: 84, size: 9.5, color: colS, intensity: 1.0 * smooth(0, 0.18, e) }));
      }
      // the line itself: drawn on arrival, then alive (a wave of brightness keeps running through him)
      const d = (t - tl - TRAVEL * 0.94) / DRAW;
      if (d > 0) {
        // HER lights (cut-2 decision: "his outline from HER cyan lights"): cyan, some violet, pale where they are packed; never his gold
        const colL = SEGR[i][1] > 0.8 ? mix3(C.violet, WHITE, 0.38) : mix3(C.her, WHITE, SEGR[i][1] < 0.25 ? 0.5 : 0.3), wave = 0.72 + 0.34 * Math.pow(0.5 + 0.5 * Math.sin((11 / HALF_SPAN) * (sg.c[0] + 0.6 * sg.c[1]) - 2.6 * t), 2);
        const I = 0.78 * wave * gone * lerp(1, 0.9, h.far);
        const n = segn[i]; // the same lights all the way (set once at his full size): they close up as he shrinks, never crawl along the line
        const hd = smooth(0, 1, d) * (1 + 0.5 / n * smooth(1.0, 1.4, d)); // once the line is drawn its head point steps off the end (no dots at the joints: a body, not a diagram)
        flows.push(flow(screen(pts), hd, { tail: 1 + 1 / n, count: n, size: lsize, color: colL, intensity: I }));
        const back = smooth(0.7, 1.6, d);
        if (back > 0.01) flows.push(flow(screen(pts.slice().reverse()), 1 + 0.5 / n + HALF(n), { tail: 1 + 1 / n, count: n, size: lsize, color: colL, intensity: I * back })); // the second run sits half a step off the first: a continuous line, not a string of beads
      }
    });
    // his panels fill with the light that drew them (her cyan, her violet toward the tips): cell by cell as its ribs arrive, a slow
    // shimmer running outward. Soft wide points, so a panel is a sheet of light and he reads as a body, not a wire diagram
    if (gone > 0.01) { const grid = cellGrid(fmt); CELLS.forEach((ce, ci) => {
      const d = (t - Math.max(LAUNCH[ce.i0], LAUNCH[ce.i1]) - TRAVEL * 0.94 - DRAW * 0.7) / 0.6; if (d <= 0) return;
      const q = ce.q.map(pt), span = Math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]), len = Math.hypot(q[3][0] - q[0][0], q[3][1] - q[0][1]), [K, n] = grid[ci];
      const sp = 720 * Math.max(span / K, len / (n - 1)); // pixels between its points right now (they stay the same points: the sheet scales with him)
      const sh = 0.6 + 0.4 * Math.pow(0.5 + 0.5 * Math.sin(7 * ce.u - 2.2 * t + ce.side), 2), I = 0.055 * sh * smooth(0, 1, d) * gone * (0.75 + 0.25 * big);
      const cc = mix3(C.her, C.violet, 0.15 + 0.55 * ce.u);
      for (let j = 0; j < K; j++) { const u = (j + 0.5) / K, a: P = [lerp(q[0][0], q[1][0], u), lerp(q[0][1], q[1][1], u)], b: P = [lerp(q[3][0], q[2][0], u), lerp(q[3][1], q[2][1], u)];
        flows.push(flow(screen((j + ci) % 2 ? [b, a] : [a, b]), 1 + 0.5 / n, { tail: 1 + 1 / n, count: n, size: sp * 4.6, color: cc, intensity: I })); }
    }); }
    // everywhere else her lights lift off too and drift up a little way (they don't all become him)
    const lift = smooth(RISE_WORDS[0] - 0.1, RISE_WORDS[0] + 0.5, t) * (1 - smooth(TB - 0.3, TB + 1.2, t));
    if (lift > 0.01) SOURCES.forEach((s, j) => {
      const g0 = geo(cam, s.g); if (!g0.vis || Math.abs(g0.p[0]) > ASPECT[fmt] || g0.p[1] < -1) return;
      const r1 = LIFTR[j], cyc = ((t - RISE_WORDS[0]) * (0.34 + 0.2 * r1[0]) + r1[1]) % 1, hgt = 0.22 + 0.3 * r1[2];
      flows.push(flow(screen([g0.p, [g0.p[0] + 0.03 * (r1[0] - 0.5), g0.p[1] + hgt * 0.5], [g0.p[0] + 0.08 * (r1[1] - 0.5), g0.p[1] + hgt]]), cyc * 1.25, { tail: 0.3, dash: 3, count: 20, size: 7.5, color: r1[2] < 0.3 ? C.violet : C.her, intensity: 0.75 * lift * Math.sin(Math.PI * Math.min(1, cyc * 1.1)) }));
    });
    const drawn = smooth(RISE_WORDS[0], RISE_WORDS[0] + 1.6, t);
    // beads of light climb the thread on the words of "can't leave where you began"; each one lands in his star
    const land = hits(t, WB3.slice(2).map((x) => x + 1.25), 0.4, 0.08);
    // his star is his EYE: the one warm light she pointed at sits in the lens once the outline closes around it, and it flares as the eye is drawn ("everyone")
    const open = env(t, EYE_T, 0.14, 0.9);
    star(lerp(15, 12, h.far) + 5 * Math.min(1, land) + 6 * open, (1.4 + 0.5 * drawn + 1.2 * Math.min(1, land) + 1.3 * open) * gone, pf(EYE_F));
    if (t >= THREAD0) {
      // the thread (pitch decision 05: it "must stay clearly visible as the payoff"): the last rope, from the river mouth, never drains.
      // It stretches as he leaves, and swells on "can't leave where you began"
      const path = threadPath(cam, h.p), lit = smooth(THREAD0, THREAD0 + 1.1, t), swell = smooth(TB3, TB3 + 0.5, t), bloom = smooth(TI, END, t);
      const L = plen(path), n = Math.max(40, Math.min(1050, Math.round((L * 720) / 2.6 / 2))), I = 0.7 + 0.4 * swell + 0.25 * bloom, sz = 10.5 + 3 * swell;
      flows.push(flow(screen(path), lit * (1 + 0.5 / n), { tail: 1 + 1 / n, count: n, size: sz, color: C.her, intensity: I }));
      const back = smooth(THREAD0 + 1.0, THREAD0 + 1.8, t);
      if (back > 0.01) flows.push(flow(screen(path.slice().reverse()), 1 + 0.5 / n + HALF(n), { tail: 1 + 1 / n, count: n, size: sz, color: C.her, intensity: I * back }));
      // a soft sheath of light around it, so the strand still reads at phone size on the wide
      { const ns = Math.round(n / 3), os = { tail: 1 + 4 / ns, count: ns, size: sz * 3.2, color: mix3(C.her, C.violet, 0.25) }, Is = 0.07 + 0.05 * swell;
        flows.push(flow(screen(path), lit * (1 + 2 / ns), { ...os, intensity: Is })); if (back > 0.01) flows.push(flow(screen(path.slice().reverse()), 1 + 2 / ns, { ...os, intensity: Is * back })); }
      WB3.slice(2).forEach((tw) => { const u = (t - tw) / 1.25; if (u > 0 && u < 1.08) flows.push(flow(screen(path), u, { tail: 0.07, count: 22, size: 17, color: mix3(C.her, WHITE, 0.4), intensity: 1.7 * smooth(0, 0.08, u) * (1 - smooth(0.98, 1.08, u)) })); });
      // "began": a ring of light spreads from the river mouth, and keeps answering through the instrumental
      pulses.push({ lat: DELTA[0], lon: DELTA[1], t0: WB3[6], speed: 9, strength: 0.9 });
    }
    if (t >= TI - 0.3) { // the instrumental: her rivers run to the sea, harder on every beat; forests bloom in rings on the bars
      const g = smooth(TI, END, t);
      for (const [riv, ph, sz] of [[DANUBE, 0, 11], [DNIEPER, 0.35, 10], [VOLGA, 0.6, 10], [RHINE, 0.15, 9], [RIVERS.nile, 0.75, 10], [TIGRIS, 0.5, 9]] as [P[], number, number][])
        flows.push(flow({ space: 'geo', pts: riv }, (((t - TI) * (0.34 + 0.12 * g) + ph) % 1) * 1.4, { tail: 0.4, size: sz, intensity: (0.4 + 0.7 * g) * smooth(TI - 0.3, TI + 0.6, t), count: 170 }));
      const B = TIMING.bar;
      pulses.push({ lat: 47.5, lon: 19, t0: TI + B, speed: 10, strength: 0.5 }, { lat: 41, lon: 29, t0: TI + 2 * B, speed: 12, strength: 0.55 }, { lat: 50, lon: 31, t0: TI + 2 * B + 2 * BEAT, speed: 13, strength: 0.5 });
    }
  }
  // The engine cross-fades every slot start for 0.45 s: (previous slot's builder) x (1 - u) + (this slot's) x u, and it ADDS the two
  // lists of lights and pulses. Both builders are this function, so inside our range that would double the point count (past the
  // 9000-point buffer at the peak of the rise: lights cut off, then popping back) and double every pulse ring. So in a cross-fade
  // between two of our slots only the "previous" side carries the lights (scaled back up to full), and only the "current" side the pulses.
  const asPrev = c.lt >= c.dur, inBlend = c.lt < BLEND && c.slot.id !== 'br_point';
  let fl = flows, sp = sparks, pu = pulses.filter((p) => t >= p.t0 && t - p.t0 < 6);
  if (asPrev) { const u0 = clamp01((t - c.slot.t1) / BLEND), kk = 1 / Math.max(1e-4, 1 - u0 * u0 * (3 - 2 * u0)); fl = flows.map((f) => ({ ...f, intensity: f.intensity * kk })); sp = sparks.map((x) => ({ ...x, intensity: x.intensity * kk })); pu = []; }
  else if (inBlend) { fl = []; sp = []; }
  return { cam: { x: k.x, y: k.y, r: k.r, lat: v.lat, lon: v.lon, roll: 0, sun: v.sun }, grade: { ...look(t, fmt, h), ...grade(t, v.r) }, flows: fl, sparks: sp, pulses: pu, motes: t < CUT1 ? 'drift' : 'rise' };
};
// THE LOOK (polish pass, Nov 9): the whole bridge sits on the film's approved look (coldOpen.ts LOOK: the lux planet, the 42k deep
// stars, the Milky Way mist), like the first 80 s. Instead of fading the deep sky out behind the drawings, the deep stars STEP BACK
// from him (grade.room, centred on him: the cold open's move, his "space"), so the sky stays rich and his outline, the crescent and
// the far worlds are drawn on clear dark. `deep` / `galaxy` only dip where the cast draws in stars (moon, worlds).
const ROOM_FULL = 1.099; // proof30 roomR() once the cold open's room is fully open: grade.room = radius / ROOM_FULL
const ROOM1 = { '169': 0.4, '916': 0.24 }, ROOM2 = { '169': 0.26, '916': 0.17 }, ROOM3 = { '169': [0.22, 0.86], '916': [0.14, 0.44] };
function look(t: number, fmt: Fmt, h: { p: P; s: number; far: number }): Partial<Grade> {
  let R = 0, deep = 1, galaxy = 1;
  if (t < CUT1) R = ROOM1[fmt] * smooth(T0 + 0.1, T0 + 2.2, t);
  else if (t < CUT2 || (t >= CUT3 && t < END)) R = ROOM2[fmt];
  else {
    const r3 = ROOM3[fmt], open = smooth(CUT2 + 0.15, CUT2 + 2.6, t), drawn = smooth(TB, TB + 1.2, t) * (1 - smooth(at('bridgeB/L2'), at('bridgeB/L2') + 2.0, t));
    R = lerp(r3[0], r3[1], open) * (h.s / HIM_S[fmt]) * lerp(1, 1.7, h.far);
    deep = lerp(1, 0.42, drawn); galaxy = lerp(1, 0.55, drawn);
  }
  return { ...LOOK, seam: 0.14, haloWide: 0, deep, galaxy, room: R / ROOM_FULL, roomX: h.p[0], roomY: h.p[1], roomKeep: 0.28 };
}
// the look through the bridge: quiet and dark-skied, her glow low and steady, then gathering through the instrumental
function grade(t: number, r = 1) {
  const atmos = Math.min(0.95, 1.9 / r); // her air is thin from close up (a wide white band otherwise)
  if (t < CUT1) return { castWarm: 1 - smooth(T0 + 0.2, T0 + 1.7, t), glow: 0.85, stars: 1.3, mist: 0.6, violet: 0.9, atmos, // (earth_cut2: his crammed stars arrive from post 2 still gold and cool to starlight as they are released)
    motes: 0.35, rivers: 1.1, riverPulse: 0.4, herCyan: 0.7, hisWarm: 0.5, bloom: 0.62, aurora: 0.1, forest: 0.35 };
  if (t >= CUT3 && t < END) { const g = smooth(CUT3, END, t), beat = hits(t, REP_BEATS, 0.3, 0.16); // the ground again: still dark and quiet under the hill, the bloom gathering in the air
    return { glow: 0.5 + 0.2 * g, kick: (0.05 + 0.07 * g) * Math.min(1.2, beat), stars: 1.3, mist: 0.8 + 0.3 * g, violet: 1.0, atmos: atmos * (1.2 + 0.3 * g), motes: 1.0 + 0.6 * g, rivers: 0.3, riverPulse: 0, herCyan: 0.05, hisWarm: 0.0, bloom: 0.72 + 0.06 * g, forest: 1.0, clouds: 0.1 }; }
  if (t < CUT2) return { glow: 0.5, stars: 1.3, mist: 0.8, violet: 1.0, atmos: atmos * 1.2, motes: 1.0, rivers: 1.0, herCyan: 0.12, hisWarm: 0.04, bloom: 0.72, forest: 1.0, clouds: 0.1 }; // the ground stays dark and quiet (no soft city glare under the hill): the figures are the light
  const up = smooth(CUT2, 157.5, t), far = smoother(TB, PULL1, t), g = smooth(TI, END, t);
  const word = hits(t, [...RISE_WORDS, ...W('bridgeA', 3).slice(3)], 0.3) * (1 - far), began = hits(t, WB3.slice(2), 0.35), beat = hits(t, BEATS_INST, 0.3);
  return {
    glow: lerp(lerp(0.95, 1.05, up), 1.05, far) + 0.16 * g, kick: 0.25 * Math.min(1.3, word) + 0.3 * Math.min(1.2, began) + (0.12 + 0.3 * g) * Math.min(1.2, beat) * smooth(TI - 0.1, TI + 0.1, t),
    stars: lerp(lerp(1.05, 1.25, far), 0.7, g), mist: lerp(0.65, 0.35, far), violet: lerp(0.9, 1.0, g), atmos: atmos * (1 + 0.15 * g), motes: lerp(0.8, 0.4, far) + 0.6 * g,
    rivers: lerp(1.2, 1.0, far) + 0.5 * g, riverPulse: 0.6 + 0.7 * g, herCyan: lerp(0.85, 0.7, far) + 0.25 * g, hisWarm: lerp(0.5, 0.42, far) - 0.12 * g, forest: lerp(0.6, 0.35, smooth(TB, TI, t)), ocean: 0.55 + 0.3 * g, // (the engine's forest shimmer also lights snow and ice: kept low when the Arctic is in frame)
    bloom: 0.62 + 0.08 * g, aurora: 0.45 * smooth(0.3, 1, g),
  };
}

// For earth_him_wire (the 3D him is rendered over this plate): where the engine draws him at song time t. Screen units (x right, y up,
// 0 = frame centre, 1 = half the frame height). origin = his model origin (centre of the bus); eye = the centre of his lens (his star sits
// there from 153.6 s); halfSpan = SPAN / 2 model units in screen units; pose and orientation = HIM_POSE (him_render.py view_matrix angles).
export function himTrack(t: number, fmt: Fmt) { const v = view(t, fmt), h = him(t, fmt, v); return { origin: h.p, eye: [h.p[0] + h.s * EYE_F[0], h.p[1] + h.s * EYE_F[1]] as P, halfSpan: h.s, far: h.far, eyeDrawn: EYE_T, thread: THREAD0 }; }

// ---- the stars ----
const SR = rng(4711), U = Array.from({ length: N_CAST }, () => [SR(), SR(), SR(), SR()]);
type StarFn = (i: number, t: number, home: [number, number], n: number, fmt: Fmt) => [number, number];
// the sky makes room: every star steps back from a point (an ellipse ax wide), far stars barely move (the cold open's move)
const room = (pos: Record<Fmt, P>, R: Record<Fmt, number>, ax = 1): StarFn => (_i, _t, home, _n, fmt) => {
  const [cx, cy] = pos[fmt], dx = (home[0] - cx) / ax, dy = home[1] - cy, r = Math.hypot(dx, dy) || 1e-6, r2 = Math.cbrt(r * r * r + R[fmt] * R[fmt] * R[fmt]);
  return [cx + (dx / r) * r2 * ax, cy + (dy / r) * r2];
};
// "past the moon": a crescent of stars
const MOON = { '169': { c: [-0.98, 0.7] as P, s: 0.2 }, '916': { c: [-0.33, 0.67] as P, s: 0.105 } }; // upper left, on her side: he leaves it behind
const moon: StarFn = (i, _t, home, _n, fmt) => {
  const u = U[i]; if (u[3] < 0.55) return home;
  const m = MOON[fmt]; let x = 0, y = 0;
  for (let k = 0; k < 12; k++) { // a point on the lit limb (most) or inside the crescent
    const a = (u[0] + k * 0.618) % 1 * 6.2832, rr = u[1] < 0.6 ? 1 : Math.sqrt((u[2] + k * 0.381) % 1);
    x = rr * Math.cos(a); y = rr * Math.sin(a);
    if (Math.hypot(x - 0.46, y - 0.14) > 0.9) break;
  }
  return [m.c[0] + m.s * x, m.c[1] + m.s * y];
};
// "other sands": far worlds, drawn in stars (a ringed one and two small ones), ahead of him
const WORLDS = { '169': { ring: [1.4, 0.78] as P, rs: 0.16, b: [1.52, 0.1] as P, bs: 0.075, c: [0.82, 0.86] as P, cs: 0.035 }, '916': { ring: [0.02, 0.63] as P, rs: 0.085, b: [-0.33, 0.44] as P, bs: 0.04, c: [0.36, 0.7] as P, cs: 0.022 } };
const worlds: StarFn = (i, _t, home, _n, fmt) => {
  const u = U[i]; if (u[3] < 0.5) return home;
  const m = WORLDS[fmt], a = u[0] * 6.2832, pick = u[1];
  if (pick < 0.3) return [m.ring[0] + m.rs * Math.cos(a), m.ring[1] + m.rs * Math.sin(a)];                                     // the planet's limb
  if (pick < 0.4) { const rr = Math.sqrt(u[2]) * 0.92; return [m.ring[0] + m.rs * rr * Math.cos(a), m.ring[1] + m.rs * rr * Math.sin(a)]; } // a little of its body
  if (pick < 0.74) { // its ring: a tilted ellipse, hidden where it passes behind the planet
    let aa = a; const rw = 1.75 + 0.3 * u[2], tl = -20 * D2R;
    if (Math.sin(aa) > 0 && Math.abs(Math.cos(aa)) * rw < 1.02) aa = -aa;
    const ex = rw * Math.cos(aa), ey = 0.3 * rw * Math.sin(aa);
    return [m.ring[0] + m.rs * (ex * Math.cos(tl) - ey * Math.sin(tl)), m.ring[1] + m.rs * (ex * Math.sin(tl) + ey * Math.cos(tl))];
  }
  if (pick < 0.9) return [m.b[0] + m.bs * Math.cos(a), m.b[1] + m.bs * Math.sin(a)];
  return [m.c[0] + m.cs * Math.cos(a), m.c[1] + m.cs * Math.sin(a)];
};
const fn = (f: StarFn, front = false) => ({ kind: 'fn' as const, fn: f, front });
const starCut = (t: number, f: StarFn): StarKey => ({ at: t - 0.03, set: fn(f), dur: 0.028, straggle: 0, curve: 0 }); // the sky changes with the camera cut
const stars: StarKey[] = [
  { at: T0, set: fn(room(HIM1, { '169': 0.4, '916': 0.24 })), dur: 2.3, straggle: 0.5, curve: 0.12 },            // his stars come back out; the sky clears around him
  starCut(CUT1, room(HIM2, { '169': 0.26, '916': 0.17 })),
  starCut(CUT2, room(HIM3, { '169': 0.22, '916': 0.14 })),
  { at: 'bridgeA/L2+0.15', set: fn(room(HIM3, { '169': 0.62, '916': 0.4 }, 1.6)), dur: 2.6, straggle: 0.4, curve: 0.1 }, // the sky makes room for him as he is drawn
  { at: 'bridgeB/L0+0.05', set: fn(moon, true), dur: 1.35, straggle: 0.35, curve: 0.25 },
  { at: 'bridgeB/L1', set: fn(worlds, true), dur: 1.3, straggle: 0.35, curve: 0.3 },
  { at: 'bridgeB/L2', set: { kind: 'sky' }, dur: 2.2, straggle: 0.5 },                                           // only a dream: the worlds scatter back into the night
];

export const bridge: Section = {
  name: 'bridge',
  camera: [{ at: 'bridgeA/L0', cam: { ...K0, lon: K0.lon - SPIN_DEG_S * 149.8, roll: 0, sun: SUN1, par: [0, 0] }, ease: 'hold' }],
  stars,
  inserts: [
    // RETIRED Nov 8 23:10: the pitch motion test of beat 05 (his outline) no longer plays over br_word / br_learned. The beat is built in
    // the engine above with the pitch decision applied (rising lights in her cyan/violet, the thread always visible); the old clip has
    // the gold particles the decision asked to change. To see it again in a rough cut, put this line back:
    //   { slot: 'br_word', src: 'le/inserts/05_his_outline.mp4', from: 153.3, to: 'bridgeB/L0', label: 'beats/05 his outline' },
    // PLACEHOLDERS for the ground v2 clips (pitch_mockups/ground2; a clip shows as soon as the file is in public/le/inserts and
    // listed in the render's inserts; until then the engine version plays): the hill figure, and the look up from the ground
    { slot: 'br_children', src: 'le/inserts/ground2_br_children.mp4', src916: 'le/inserts/ground2_br_children_916.mp4', from: CUT1 + 0.002, to: CUT2 + 0.002, label: 'the hill figure points at one star' },
    { slot: 'br_ground', src: 'le/inserts/ground2_br_ground.mp4', from: at('bridgeB/L2'), to: 'bridgeB/L3', label: 'ground v2 (optional): leave the ground behind' },
    // cut 2: the instrumental is on the same hill (the thread in the smallest child's hand). If ground v2 replaces br_children it needs this one too
    ...(GROUND ? [{ slot: 'inst', src: 'le/inserts/ground2_inst.mp4', src916: 'le/inserts/ground2_inst_916.mp4', from: CUT3 + 0.002, to: Math.ceil((END - 0.001) * 30) / 30, label: 'the hill again, the child holds the thread' }] : []),
  ],
  builders: { br_point: scene, br_children: scene, br_word: scene, br_learned: scene, br_moon: scene, br_sands: scene, br_ground: scene, br_began: scene, inst: scene },
};
