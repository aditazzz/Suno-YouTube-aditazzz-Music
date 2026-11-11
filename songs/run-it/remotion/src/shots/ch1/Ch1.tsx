// CH1 + POST1, s18-s27 (41.65-73.12): one continuous picture, a pure function of film time, registered for every shot id
// s18..s27 so the world never cuts between them (same pattern as src/shots/hook/). ROUGHCUT_PLAN.md: "flat maximalism;
// 1 -> 4 -> 16 -> a wall of variants -> one dot".
//
// It starts on the hook's last frame (s17 at 41.65: dot x3 at 960,470, the red button with its open lid, the tiny red
// button and the pigeon, camera z 1.07) and ends on the clean slate s28 builds the city from (the dot, r 74, three faint
// rings, the dot grid, camera z 1).
//
//   s18 fire   flat vector flames ring the dot, amber light beams sweep
//   s19 spin   the composition orbits the dot (a tilted 2.5D orbit), the lid flies off, the red button spins the other way;
//              "shine" on beat 3: a specular sweep across every shape
//   s20 whole  every element hops on every beat in unison; the grid ticks on the downbeat (one grid dot is a beat late)
//   s21 louder the artboard resizes 1920x1080 -> 3840x2160 (frame handles), the camera pulls back, 16 new shapes fill it,
//              speaker-cone rings pulse out on the kicks, the ghost artboards from 0:12 are pushed back into view
//   s22 tower  the bass becomes a stacked tower behind the dot: a floor per 16th, every floor's windows and width driven by
//              the Suno bass stem's level; the camera tilts up with it
//   s23 run    a "Run" chip presses, everything plays at full speed, the camera swoops 180 degrees around it (2.5D yaw),
//              and on bar 29 every shape snaps into the loop symbol (a ring with an arrowhead)
//   s24 x4     a collaborator cursor types "(run it)"; the composition duplicates into 2x2 variants (copies slide out)
//   s25 x16    2x2 -> 4x4 (one tile is the film's last frame: white dot + cursor)
//   s26 wall   hundreds of variants ripple in, a slow diagonal truck (one tile is upside down)
//   s27 one    the wall spirals into the dot (the outro's undo move), the camera pushes in: the clean slate
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { C, MED, mixC, useLayout, useT, Layout } from '../../theme';
import { beatPos, downbeats, hatEnv, kickEnv, kicks, lines, promptAt, tshot } from '../../timing';
import type { ShotProps } from '../../shots';
import { clamp, easeIn2, easeInOut3, easeOut3, impact, lerp, mixHex, prog, smooth, spring } from '../hook/anim';
import { BAR, BEAT, COLLAPSE_END, SHINE, SIX, T, bassAt, beatAfter } from './times';
import { barCharPos, barHeight, barRows } from '../../components/barWrap';
import { LIGHT_SWAP, P, SWAPS, TILE_DARK, TILE_LIGHT } from './palette';

const DEG = Math.PI / 180;
const D = { x: 960, y: 470 };      // the dot (world)
const R0 = 222;                     // the dot after s17's x3
const A1 = { x: 0, y: 0, w: 1920, h: 1080 };
const A2 = { x: -960, y: -540, w: 3840, h: 2160 };
const A3 = { x: 0, y: -70, w: 1920, h: 1080 }; // bar 30: the frame fits to the formation (16:9, centred on the dot)
const TILE = A3;
// 9:16 (rc_916): the artboard is the hook's portrait 9:16 artboard (1080x1920 -> 2160x3840 about its centre), then fits
// to the formation as the landscape tile (the variant tiles stay 16:9 tiles)
const A1_9 = { x: 560, y: -4, w: 800, h: 1422 };
const A2_9 = { x: 160, y: -715, w: 1600, h: 2844 };
const artsOf = (L: Layout) => (L.fmt === '16x9' ? { a1: A1, a2: A2 } : { a1: A1_9, a2: A2_9 });
const PITCH = { x: 2160, y: 1260 }; // variant tiles (TILE + gaps)
const FOCAL = 1800;                 // 2.5D perspective
const SLOT = 54;                    // formation element size
const hash = (n: number) => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };

// ---------- camera ----------
type Cam = { z: number; cx: number; cy: number };
/** zoom/pan from a to b: log zoom, and b's centre glides to the screen centre in a straight line (no swing) */
const tween = (a: Cam, b: Cam, e: number): Cam => {
  const z = Math.exp(lerp(Math.log(a.z), Math.log(b.z), e)), w = (a.z / z) * (1 - e);
  return { z, cx: b.cx + (a.cx - b.cx) * w, cy: b.cy + (a.cy - b.cy) * w };
};
const K0: Cam = { z: 1.07, cx: 960, cy: 540 };   // = the hook's camera at 41.65
const K18: Cam = { z: 1.12, cx: 960, cy: 540 };
const K21: Cam = { z: 0.36, cx: 960, cy: 470 };
const K22: Cam = { z: 0.42, cx: 960, cy: 300 };
const KF: Cam = { z: 0.9, cx: 960, cy: 490 };
const KF2: Cam = { z: 0.95, cx: 960, cy: 490 };
const GRID_C = { x: TILE.x + TILE.w / 2 + PITCH.x / 2, y: TILE.y + TILE.h / 2 + PITCH.y / 2 }; // centre of the 2x2 and the 4x4
const K4: Cam = { z: 0.338, cx: GRID_C.x, cy: GRID_C.y + 44 };
const K4b: Cam = { z: 0.346, cx: GRID_C.x, cy: GRID_C.y + 44 };
const K16: Cam = { z: 0.1626, cx: GRID_C.x, cy: GRID_C.y + 92 };
const K16b: Cam = { z: 0.172, cx: GRID_C.x, cy: GRID_C.y + 92 };
const KW: Cam = { z: 0.07, cx: GRID_C.x, cy: GRID_C.y };
const TRUCK = { x: -5000, y: -2900 };
const LOD0 = 0.075, LOD1 = 0.095; // tiles simplify below this zoom (formation elements < ~4 px)
const KEND: Cam = { z: 1, cx: 960, cy: 540 };

const truckK = (u: number) => (u < 0.3 ? (u * u) / 0.6 : u - 0.15) / 0.85; // eased-in start, then a steady drift
function camWall(t: number): Cam {
  const c = tween(K16b, KW, easeInOut3(prog(t, T.WALL, T.WALL + 1.3)));
  const k = truckK(prog(t, T.WALL, T.ONE));
  return { z: c.z, cx: c.cx + TRUCK.x * k, cy: c.cy + TRUCK.y * k };
}
function cam16(t: number): Cam {
  if (t < T.SPIN) return tween(K0, K18, smooth(prog(t, T.START, T.SPIN)));            // s18 slow push
  if (t < T.LOUD) return K18;                                                          // s19-s20 locked (the unison reads)
  if (t < T.TOWER) return tween(K18, K21, clamp(spring(t - T.LOUD, 1.25, 0.82), 0, 1.03)); // s21 pull back
  if (t < T.RUN + 0.6) return tween(K21, K22, easeInOut3(prog(t, T.TOWER, T.TOWER + 1.8))); // s22 tilt up with the tower
  if (t < T.FORM) return tween(K22, KF, easeInOut3(prog(t, T.RUN + 0.6, T.FORM)));    // s23 the swoop pushes in
  if (t < T.X4) return tween(KF, KF2, smooth(prog(t, T.FORM, T.X4)));
  if (t < T.X16) return t < T.X4 + 1.1 ? tween(KF2, K4, easeInOut3(prog(t, T.X4, T.X4 + 1.1))) : tween(K4, K4b, smooth(prog(t, T.X4 + 1.1, T.X16)));
  if (t < T.WALL) return t < T.X16 + 1.1 ? tween(K4b, K16, easeInOut3(prog(t, T.X16, T.X16 + 1.1))) : tween(K16, K16b, smooth(prog(t, T.X16 + 1.1, T.WALL)));
  if (t < T.ONE) return camWall(t);
  return tween(camWall(T.ONE), KEND, easeInOut3(prog(t, T.ONE, T.ONE + 1.25)));       // s27 push in to the dot
}
type View = Cam & { sx: number; sy: number }; // sx, sy = the screen point the camera centre maps to
/** 16:9 = cam16. 9:16 = viewAt9 (LAYOUT_916.md). */
function viewAt(t: number, L: Layout): View {
  const c = cam16(t);
  if (L.fmt === '16x9') return { ...c, sx: L.W / 2, sy: L.H / 2 };
  return viewAt9(t, c);
}
// ---- 9:16 (rc_916): 16:9's camera at zoom x1.0 (the fire burst fills the width), its centre on screen (540, 735) so the
// dot sits at (540, 660) on the hook's hand-over; the 2x2 / 4x4 at x0.78 so they fill the width; the wall is a FEED:
// the camera scrolls down it one row per beat, accelerating like a flick, the wall tipped 16 deg back; s27 collapses to
// one dot at (540, 680).
const SY9 = 735, GRIDF9 = 0.78;
const WALLZ9 = 0.148;                       // row pitch on screen 1260 x 0.148 = 187 px; 3 full columns + two halves
const WALL_SY9 = 820;
const FLICK = [0, 1, 2, 3, 4, 5, 7, 9, 11, 13]; // rows scrolled after n beats (the flick accelerates)
function wallRows(t: number) {
  const b0 = beatAfter(T.WALL, 0), BT = BEAT, u = (t - b0) / BT;
  if (u <= 0) return 0;
  const n = Math.min(FLICK.length - 2, Math.floor(u)), f = u - Math.floor(u);
  const step = easeOut3(clamp(f / 0.55)); // each beat: a quick flick, then it glides to rest
  return Math.floor(u) >= FLICK.length - 1 ? FLICK[FLICK.length - 1] : lerp(FLICK[n], FLICK[n + 1], step);
}
function wallView9(t: number): View {
  return { z: WALLZ9, cx: TILE.x + TILE.w / 2, cy: GRID_C.y + wallRows(t) * PITCH.y, sx: 540, sy: WALL_SY9 };
}
const tweenV = (a: View, b: View, e: number): View => {
  // the screen anchors glide too: express both as "world point at screen centre" so tween() stays straight
  const ca = { z: a.z, cx: a.cx + (540 - a.sx) / a.z, cy: a.cy + (960 - a.sy) / a.z }, cb = { z: b.z, cx: b.cx + (540 - b.sx) / b.z, cy: b.cy + (960 - b.sy) / b.z };
  const c = tween(ca, cb, e); return { ...c, sx: 540, sy: 960 };
};
function viewAt9(t: number, c: Cam): View {
  const gf = lerp(1, GRIDF9, easeInOut3(prog(t, T.X4, T.X4 + 1.1)));
  const pre: View = { z: c.z * gf, cx: c.cx, cy: c.cy, sx: 540, sy: SY9 };
  if (t < T.WALL) return pre;
  const k16: View = { z: K16b.z * GRIDF9, cx: K16b.cx, cy: K16b.cy, sx: 540, sy: SY9 };
  const wall = (tt: number) => tweenV(k16, wallView9(tt), easeInOut3(prog(tt, T.WALL, T.WALL + 0.7)));
  if (t < T.ONE) return wall(t);
  // the clean slate s28 builds from: the city's 9:16 frame (x1.25, road on 1060) puts the dot at (540, 635), r 92
  const end: View = { z: 1.25 * KEND.z, cx: D.x, cy: D.y, sx: 540, sy: 635 };
  return tweenV(wall(T.ONE), end, easeInOut3(prog(t, T.ONE, T.ONE + 1.25)));
}
/** 9:16: the wall's backward tip (deg), on with the wall, off as it collapses */
const wallTilt9 = (t: number) => 16 * smooth(prog(t, T.WALL, T.WALL + 0.7)) * (1 - smooth(prog(t, T.ONE, T.ONE + 0.8)));
const toS = (v: View, x: number, y: number) => ({ x: v.sx + (x - v.cx) * v.z, y: v.sy + (y - v.cy) * v.z });
const toW = (v: View, x: number, y: number) => ({ x: v.cx + (x - v.sx) / v.z, y: v.cy + (y - v.sy) / v.z });

// ---------- the composition's motion ----------
const theta = (t: number) => (t < T.SPIN ? 0 : 360 * spring(t - T.SPIN, 0.85, 0.72) + 16 * (t - T.SPIN) + 540 * easeInOut3(prog(t, T.RUN, T.RUN + BAR)));
const persp = (t: number) => smooth(prog(t, T.SPIN, T.SPIN + 1.0));
const yawOf = (t: number) => 180 * easeInOut3(prog(t, T.RUN + 0.6, T.FORM));
/** s20: every element hops on every beat in unison (8ths while "Run" plays at full speed) */
function hop(t: number) {
  const amp = (t < T.WORLD ? 0 : 1) * (1 - 0.5 * smooth(prog(t, T.TOWER, T.TOWER + 1))) * (1 - smooth(prog(t, T.RUN + 0.6, T.RUN + 1.6)));
  if (amp <= 0) return { dy: 0, sx: 1, sy: 1 };
  const bp = beatPos(t), p = t >= T.RUN && t < T.RUN + BAR ? (bp * 2) % 1 : bp % 1;
  const sq = Math.exp(-p * 14);
  return { dy: -30 * amp * 4 * p * (1 - p), sx: 1 + 0.1 * amp * sq, sy: 1 - 0.14 * amp * sq };
}
/** formation snap on bar 29 (crosses 1 on the downbeat, a little overshoot), and its slow spinner turn after */
const snapOf = (t: number) => (t < T.FORM - 0.12 ? 0 : spring(t - (T.FORM - 0.12), 2.4, 0.6));
const rhoOf = (t: number, spd = 1) => Math.max(0, t - T.FORM) * 22 * spd;
/** the dot's kick breath (same as the hook): +14% on the hit, back over the beat */
const breathOf = (t: number) => { let b = 0; for (const k of kicks) { const d = t - k; if (d >= 0 && d < BEAT && d < 0.75) b = Math.max(b, Math.pow(1 - d / BEAT, 2)); } return b; };
const kickPulse = (t: number) => { let b = 0; for (const k of kicks) { const d = t - k; if (d >= 0 && d < BEAT) b = Math.max(b, Math.pow(1 - d / BEAT, 2)); } return b; };
/** s27: 0 -> 1, accelerating (gravity), the tiles reach the dot at COLLAPSE_END */
const collapseOf = (t: number) => Math.pow(prog(t, T.ONE, COLLAPSE_END), 2.2);
/** s27 spiral angle: a vortex (inner tiles turn more), so the wall swirls instead of turning as one rigid lattice */
const vortex = (rel: { x: number; y: number }, col: number) => col * Math.PI * (2.0 - 1.3 * clamp(Math.hypot(rel.x, rel.y) / 1100));
const dotBaseR = (t: number) => lerp(R0, 74, easeInOut3(prog(t, T.ONE, COLLAPSE_END)));

// ---------- elements ----------
type Kind = 'flame' | 'tri' | 'sq' | 'semi' | 'ring' | 'circ' | 'plus' | 'zig' | 'pill' | 'btn' | 'mini' | 'pigeon' | 'floor';
type El = { i: number; g: 'A' | 'F' | 'S' | 'O' | 'T'; kind: Kind; col: string; col2?: string; size: number; born: number; a0: number; rx: number; ry: number; k?: number };
const ELS: El[] = (() => {
  const e: El[] = [];
  const add = (x: Omit<El, 'i'>) => e.push({ ...x, i: e.length });
  // from the hook (positions = the hook's at 41.65, as tilted-orbit parameters: x = rx cos a, y = ry sin a)
  add({ g: 'A', kind: 'btn', col: C.red, size: 80, born: -1, a0: 35.5, rx: 516, ry: 310 });
  add({ g: 'A', kind: 'mini', col: C.red, size: 32, born: -1, a0: -54.5, rx: 477, ry: 286.2 });
  add({ g: 'A', kind: 'pigeon', col: '#e9e6f2', size: 36.4, born: -1, a0: -130.6, rx: 455.6, ry: 273.4 });
  // s18: ten flames, born from the top (where "fire" lands) around both sides
  for (let i = 0; i < 10; i++) add({ g: 'F', kind: 'flame', col: i % 2 ? P.amber : P.gold, col2: P.core, size: 120,
    born: T.FIRE + Math.min(i, 10 - i) * 0.025, a0: -90 + i * 36, rx: 0, ry: 0 });
  // s19: eight satellites flung out by the spin
  const sk: Kind[] = ['tri', 'sq', 'semi', 'ring', 'tri', 'sq', 'semi', 'ring'];
  const sc = [P.blue, P.amber, P.core, P.slate, P.gold, P.blue, P.amber, P.core];
  for (let k = 0; k < 8; k++) add({ g: 'S', kind: sk[k], col: sc[k], size: 100, born: T.SPIN + k * 0.03, a0: 22.5 + 45 * k, rx: 640, ry: 384 });
  // s21: sixteen new shapes fill the doubled artboard
  const ok: Kind[] = ['plus', 'zig', 'pill', 'circ', 'ring', 'tri', 'sq', 'semi'];
  const oc = [P.amber, P.blue, P.core, P.gold, P.slate, P.core, P.blue, P.amber, P.blue, P.gold, P.amber, P.slate, P.core, P.amber, P.gold, P.blue];
  for (let k = 0; k < 16; k++) {
    const outer = k >= 8, rx = outer ? 1560 : 1150;
    add({ g: 'O', kind: ok[(k + (outer ? 3 : 0)) % 8], col: oc[k], size: 150, born: T.LOUD + 0.05 + (outer ? 0.2 : 0) + (k % 8) * 0.02,
      a0: outer ? (k - 8) * 45 + 32 : k * 45 + 10, rx, ry: 0.56 * rx });
  }
  // s22: fourteen tower floors, one per 16th
  for (let k = 0; k < 14; k++) add({ g: 'T', kind: 'floor', col: P.towerBody, size: 400, born: T.TOWER + k * SIX, a0: 0, rx: 0, ry: 0, k });
  return e;
})();

type Pre = { x: number; y: number; z: number; rot: number; sc: number; sy?: number };
/** an element's place in the composition before the formation (relative to the dot, 3D, before the yaw) */
function prePos(e: El, t: number, dotR: number): Pre | null {
  if (t < e.born) return null;
  const th = theta(t), pz = persp(t);
  if (e.g === 'F') {
    const grow = spring(t - e.born, 2.4, 0.55), ang = (e.a0 + th) * DEG, r = dotR + 8 + 14 * grow;
    return { x: Math.cos(ang) * r, y: Math.sin(ang) * r, z: 0, rot: e.a0 + th + 90, sc: grow };
  }
  if (e.g === 'T') {
    const grow = spring(t - e.born, 3.2, 0.7);
    return { x: 0, y: 40 - (e.k + 0.5) * 70 + 70 * (1 - grow), z: 260, rot: 0, sc: 1, sy: clamp(grow, 0, 1.2) };
  }
  let rx = e.rx, ry = e.ry, sc = 1;
  if (e.g === 'S') { const fl = easeOut3(prog(t, e.born, e.born + 0.6)); rx = lerp(dotR + 30, e.rx, fl); ry = lerp(dotR + 30, e.ry, fl); sc = spring(t - e.born, 2.4, 0.55); }
  if (e.g === 'O') { const fl = easeOut3(prog(t, e.born, e.born + 0.7)); rx = lerp(e.rx * 0.55, e.rx, fl); ry = lerp(e.ry * 0.55, e.ry, fl); sc = spring(t - e.born, 2.4, 0.55); }
  const ang = (e.a0 + th) * DEG;
  const rot = e.g === 'A' ? (e.kind === 'btn' || e.kind === 'mini' ? -2 * th : 0) : th * 1.5 + e.i * 37;
  return { x: Math.cos(ang) * rx, y: Math.sin(ang) * ry, z: -Math.sin(ang) * rx * 0.45 * pz, rot, sc };
}
/** yaw about the vertical axis through the dot + perspective: rel 3D -> rel 2D and a scale */
function project(x: number, y: number, z: number, yawDeg: number) {
  const a = yawDeg * DEG, X = x * Math.cos(a) + z * Math.sin(a), Z = -x * Math.sin(a) + z * Math.cos(a);
  const s = FOCAL / (FOCAL + Z);
  return { x: X * s, y: y * s, s, depth: Z };
}

// ---------- the formation (the loop symbol) ----------
type Var = { swap: Record<string, string>; bg: string; rot0: number; dir: number; rs: number; ds: number; kind?: Kind; spd: number; upside?: boolean; final?: boolean; ph: number };
const V0: Var = { swap: {}, bg: P.ground, rot0: 0, dir: 1, rs: 1, ds: 1, spd: 1, ph: 0 };
const ARC_N = ELS.length - 7;
const slotCache = new Map<number, { x: number; y: number; ang: number }[]>();
function slotGeom(rs: number) {
  if (slotCache.has(rs)) return slotCache.get(rs)!;
  const RF = 420 * rs, a0 = -75, span = 290, out: { x: number; y: number; ang: number }[] = [];
  for (let k = 0; k < ARC_N; k++) { const a = a0 + (span * k) / (ARC_N - 1); out.push({ x: Math.cos(a * DEG) * RF, y: Math.sin(a * DEG) * RF, ang: a + 90 }); }
  const ae = (a0 + span) * DEG, tg = { x: -Math.sin(ae), y: Math.cos(ae) }, nr = { x: Math.cos(ae), y: Math.sin(ae) };
  const tip = { x: Math.cos(ae) * RF + tg.x * 78, y: Math.sin(ae) * RF + tg.y * 78 }, ang = a0 + span + 90;
  out.push({ ...tip, ang });
  for (let s = 1; s <= 3; s++) for (const side of [-1, 1]) {
    const d = s * 46 * 0.7071;
    out.push({ x: tip.x + (-tg.x + side * nr.x) * d, y: tip.y + (-tg.y + side * nr.y) * d, ang });
  }
  slotCache.set(rs, out);
  return out;
}
/** element i -> slot index: elements keep their angular order around the dot when they snap (no crossings) */
let ASSIGN: number[] | null = null;
function assignment() {
  if (ASSIGN) return ASSIGN;
  const ta = T.FORM - 0.12, dr = R0 * (1 + 0.14 * breathOf(ta));
  const angs = ELS.map((e) => {
    const p = prePos(e, ta, dr)!; const q = project(p.x, p.y, p.z, yawOf(ta));
    let a = Math.atan2(q.y, q.x) / DEG + 75; a = ((a % 360) + 360) % 360; return { i: e.i, a };
  }).sort((u, v) => u.a - v.a);
  ASSIGN = new Array(ELS.length);
  angs.forEach((o, n) => { ASSIGN[o.i] = n; });
  return ASSIGN;
}
function slotPos(e: El, v: Var, t: number) {
  const s = slotGeom(v.rs)[assignment()[e.i]];
  const r = (rhoOf(t, v.spd) + v.rot0) * DEG * v.dir, pulse = 1 + 0.035 * kickPulse(t);
  const x = s.x * v.dir, y = s.y;
  return { x: (x * Math.cos(r) - y * Math.sin(r)) * pulse, y: (x * Math.sin(r) + y * Math.cos(r)) * pulse, rot: (s.ang * v.dir + r / DEG) + (e.i * 29) % 40 - 20 };
}

// ---------- shapes (local coords, centred, `size` = nominal diameter) ----------
const Shape: React.FC<{ e: El; kind?: Kind; col: string; col2?: string; size: number; t: number; mono?: boolean; formation?: number; spin?: number }> = ({ e, kind, col, col2, size: S, t, mono, formation = 0, spin = 0 }) => {
  const k = kind ?? e.kind, f = mono ? '#fff' : col;
  switch (k) {
    case 'tri': { const r = S / 2; return <polygon points={`0,${-r} ${r * 0.866},${r * 0.5} ${-r * 0.866},${r * 0.5}`} fill={f} />; }
    case 'sq': return <rect x={-S * 0.38} y={-S * 0.38} width={S * 0.76} height={S * 0.76} rx={S * 0.1} fill={f} />;
    case 'semi': { const r = S / 2; return <path d={`M ${-r} ${r * 0.2} A ${r} ${r} 0 0 1 ${r} ${r * 0.2} Z`} fill={f} />; }
    case 'ring': return <circle r={S * 0.36} fill="none" stroke={f} strokeWidth={S * 0.16} />;
    case 'circ': return <circle r={S * 0.4} fill={f} />;
    case 'plus': return <g fill={f}><rect x={-S * 0.13} y={-S * 0.45} width={S * 0.26} height={S * 0.9} rx={S * 0.06} /><rect x={-S * 0.45} y={-S * 0.13} width={S * 0.9} height={S * 0.26} rx={S * 0.06} /></g>;
    case 'zig': return <polyline points={`${-S * 0.45},${S * 0.13} ${-S * 0.22},${-S * 0.13} 0,${S * 0.13} ${S * 0.22},${-S * 0.13} ${S * 0.45},${S * 0.13}`} fill="none" stroke={f} strokeWidth={S * 0.13} strokeLinecap="round" strokeLinejoin="round" />;
    case 'pill': return <rect x={-S / 2} y={-S * 0.19} width={S} height={S * 0.38} rx={S * 0.19} fill={f} />;
    case 'flame': {
      // flat, geometric, not photoreal: a teardrop (tip outward), an inner tongue; flickers on the hats
      const fl = 1 + 0.18 * hatEnv(t + e.i * 0.013) + 0.07 * Math.sin(t * 11 + e.i * 1.7);
      const h = S * fl, w = S * 0.55;
      const tear = (hh: number, ww: number) => `M ${-ww / 2} 0 C ${-ww / 2} ${-hh * 0.38} ${-ww * 0.12} ${-hh * 0.62} 0 ${-hh} C ${ww * 0.12} ${-hh * 0.62} ${ww / 2} ${-hh * 0.38} ${ww / 2} 0 A ${ww / 2} ${ww / 2} 0 0 1 ${-ww / 2} 0 Z`;
      if (mono) return <g transform={`translate(0 ${h * 0.45})`}><path d={tear(h, w)} fill={f} /></g>;
      return <g transform={`translate(0 ${h * 0.45})`}><path d={tear(h, w)} fill={P.ember} /><path d={tear(h * 0.84, w * 0.96)} fill={f} />
        <path d={tear(h * 0.5, w * 0.5)} fill={col2 ?? P.core} transform={`translate(0 ${-w * 0.05})`} /></g>;
    }
    case 'btn': case 'mini': {
      const r = k === 'btn' ? 40 : 16, sp = spin * DEG;
      if (mono) return <circle r={r} fill="#fff" />;
      return <g><circle cy={r * 0.15} r={r} fill="#3a0d12" /><circle r={r} fill={col} />
        <circle cx={r * 0.42 * Math.cos(sp - 2.3)} cy={r * 0.42 * Math.sin(sp - 2.3)} r={r * 0.25} fill="rgba(255,255,255,.25)" /></g>;
    }
    case 'pigeon': {
      const s = 1.3 * (S / 36.4), up = 6 + 6 * Math.sin(t * 9);
      return <path d={`M ${-14 * s} ${-up * s} Q ${-5 * s} ${-(up + 7) * s} 0 0 Q ${5 * s} ${-(up + 7) * s} ${14 * s} ${-up * s}`} fill="none" stroke={f} strokeWidth={3.2 * s} strokeLinecap="round" strokeLinejoin="round" />;
    }
    case 'floor': {
      // a tower floor: body, lit edge, five windows driven by the bass (a VU per floor, cascading upward)
      const lvl = clamp((bassAt(t - (e.k ?? 0) * 0.025) - 0.25) / 0.7);
      const w = lerp(400, SLOT * 1.1, formation), h = lerp(62, SLOT * 0.62, formation), nw = formation > 0.5 ? 3 : 5;
      if (mono) return <rect x={-w / 2} y={-h / 2} width={w} height={h} fill="#fff" />;
      const lit = Math.round(lvl * nw + 0.3 * (hash((e.k ?? 0) + 3) - 0.5));
      const ww = w / (nw * 1.6 + 0.6), wh = h * 0.42, warm = Math.pow((e.k ?? 0) / 13, 1.6) * 0.92;
      const body = mixHex(P.towerBody, P.amber, warm), edge = mixHex(P.towerEdge, P.gold, warm), off = mixHex(P.winOff, P.gold, warm * 0.8);
      return <g><rect x={-w / 2} y={-h / 2} width={w} height={h} fill={body} /><rect x={-w / 2} y={-h / 2} width={w * 0.04} height={h} fill={edge} />
        {Array.from({ length: nw }, (_, j) => <rect key={j} x={-w / 2 + ww * 0.6 + j * ww * 1.6} y={-wh / 2} width={ww} height={wh} fill={j < lit ? (warm > 0.45 ? P.core : P.amber) : off} />)}</g>;
    }
  }
  return null;
};

// the red button's glass lid (flipped open in s12; flies off with the spin in s19). Local coords: button centre = 0,0
const Lid: React.FC = () => {
  const hy = -58;
  return (
    <g>
      <g transform={`translate(0 ${hy}) scale(1 -0.85) translate(0 ${-hy})`}>
        <rect x={-58} y={hy} width={116} height={116} rx={18} fill="rgba(190,214,255,.09)" stroke="rgba(235,242,255,.46)" strokeWidth={2} />
        <path d={`M -38 ${hy + 96} L 22 ${hy + 16}`} stroke="rgba(255,255,255,.22)" strokeWidth={7} strokeLinecap="round" />
        <path d={`M -18 ${hy + 104} L 38 ${hy + 30}`} stroke="rgba(255,255,255,.10)" strokeWidth={4} strokeLinecap="round" />
      </g>
      <rect x={-46} y={hy - 6} width={92} height={12} rx={6} fill="#2a2a34" stroke="rgba(255,255,255,.25)" strokeWidth={1.5} />
    </g>
  );
};

// ---------- variants ----------
const FINAL_TILE = '2,-1', UPSIDE_TILE = '-3,-2';
const varCache = new Map<string, Var>();
function variant(i: number, j: number): Var {
  const key = `${i},${j}`;
  if (i === 0 && j === 0) return V0;
  if (varCache.has(key)) return varCache.get(key)!;
  const n = (i + 40) * 97 + (j + 40) * 31, h = (m: number) => hash(n + m * 13.7);
  const kinds: (Kind | undefined)[] = [undefined, undefined, 'circ', 'sq', 'tri', 'plus', 'ring', 'semi', undefined];
  const hb = h(2), light = hb > 0.76;
  const v: Var = { swap: light ? LIGHT_SWAP : SWAPS[Math.floor(h(1) * SWAPS.length)], bg: light ? TILE_LIGHT[hb > 0.88 ? 1 : 0] : TILE_DARK[Math.floor(hb / 0.76 * TILE_DARK.length) % TILE_DARK.length], rot0: Math.floor(h(3) * 8) * 45,
    dir: h(4) < 0.5 ? -1 : 1, rs: [0.86, 0.94, 1, 1.06][Math.floor(h(5) * 4)], ds: [0.72, 0.86, 1, 1.12][Math.floor(h(6) * 4)],
    kind: kinds[Math.floor(h(7) * kinds.length)], spd: 0.7 + 0.6 * h(8), ph: h(9) * 0.25, upside: key === UPSIDE_TILE, final: key === FINAL_TILE };
  varCache.set(key, v);
  return v;
}

/** one variant tile's art in tile-local coords (= the original artboard's coords). lodK 0 = full .. 1 = simplified */
const TileArt: React.FC<{ v: Var; t: number; lodK: number; z: number }> = ({ v, t, lodK, z }) => {
  const A = TILE;
  if (v.final) {
    // egg: the film's last frame (approved frame 6): one white light, three rings, the cursor on it
    return (
      <g>
        <rect x={A.x} y={A.y} width={A.w} height={A.h} fill="#050507" />
        {[3, 2, 1].map((i) => <circle key={i} cx={D.x} cy={D.y} r={60 + i * 44} fill="none" stroke={`rgba(255,255,255,${0.06 * i})`} strokeWidth={3} />)}
        <circle cx={D.x} cy={D.y} r={76} fill="rgba(255,255,255,.08)" />
        <circle cx={D.x} cy={D.y} r={60} fill="#ffffff" />
        <g transform={`translate(${D.x + 14} ${D.y + 12}) scale(1.4)`}><path d="M0 0 L0 44 L11 33 L19 51 L27 47 L19 30 L34 30 Z" fill="#ffffff" stroke="#0b0b10" strokeWidth={3} strokeLinejoin="round" /></g>
      </g>
    );
  }
  const dotR = R0 * v.ds * (1 + 0.1 * breathOf(t - v.ph));
  const els: React.ReactNode[] = [];
  if (lodK < 1) {
    for (const e of ELS) {
      const p = slotPos(e, v, t - v.ph), kind = e.kind === 'btn' || e.kind === 'mini' || e.kind === 'pigeon' || e.kind === 'floor' ? e.kind : v.kind ?? e.kind;
      const sz = e.kind === 'floor' ? 400 : e.size, sc = e.kind === 'floor' ? 1 : SLOT / e.size;
      els.push(<g key={e.i} transform={`translate(${D.x + p.x} ${D.y + p.y}) rotate(${p.rot}) scale(${sc})`}>
        <Shape e={e} kind={kind} col={v.swap[e.col] ?? e.col} col2={v.swap[e.col2] ?? e.col2} size={sz} t={t} formation={1} spin={-2 * theta(t)} /></g>);
    }
  }
  let lod: React.ReactNode = null;
  if (lodK > 0) {
    // simplified at wall distance: the ring as 11 coloured arcs + the arrowhead
    const RF = 420 * v.rs, r0 = (rhoOf(t - v.ph, v.spd) + v.rot0) * v.dir;
    const segs = Array.from({ length: 11 }, (_, s) => {
      const a = (-75 + (290 * s) / 11) * v.dir + r0, b = (-75 + (290 * (s + 1)) / 11 - 4) * v.dir + r0;
      const e = ELS[(s * 4 + 5) % ELS.length], col = v.swap[e.col] ?? e.col;
      const p = (q: number) => `${D.x + Math.cos(q * DEG) * RF} ${D.y + Math.sin(q * DEG) * RF}`;
      return <path key={s} d={`M ${p(a)} A ${RF} ${RF} 0 0 ${v.dir > 0 ? 1 : 0} ${p(b)}`} fill="none" stroke={col === P.towerBody ? P.slate : col} strokeWidth={SLOT} />;
    });
    const ae = (-75 + 290) * v.dir + r0, tg = { x: -Math.sin(ae * DEG) * v.dir, y: Math.cos(ae * DEG) * v.dir }, nr = { x: Math.cos(ae * DEG), y: Math.sin(ae * DEG) };
    const tip = { x: D.x + nr.x * RF + tg.x * 100, y: D.y + nr.y * RF + tg.y * 100 };
    const w1 = { x: tip.x - tg.x * 130 + nr.x * 110, y: tip.y - tg.y * 130 + nr.y * 110 }, w2 = { x: tip.x - tg.x * 130 - nr.x * 110, y: tip.y - tg.y * 130 - nr.y * 110 };
    lod = <g opacity={lodK}>{segs}<polygon points={`${tip.x},${tip.y} ${w1.x},${w1.y} ${w2.x},${w2.y}`} fill={v.swap[P.core] ?? P.core} /></g>;
  }
  void z;
  return (
    <g>
      <rect x={A.x} y={A.y} width={A.w} height={A.h} fill={v.bg} />
      <circle cx={D.x} cy={D.y} r={dotR * 3.2} fill="url(#ch1glow)" />
      {[3, 2, 1].map((i) => <circle key={i} cx={D.x} cy={D.y} r={dotR + i * 34} fill="none" stroke={v.swap === LIGHT_SWAP ? `rgba(22,35,58,${0.1 * i})` : `rgba(255,255,255,${0.07 * i})`} strokeWidth={2 / Math.max(z, 0.05)} />)}
      <g opacity={1 - lodK}>{els}</g>
      {lod}
      <circle cx={D.x} cy={D.y} r={dotR} fill={C.pink} />
    </g>
  );
};

// ---------- ghost artboards (the hook's storyboard, now dark), pushed outward by the resize ----------
const GHOSTS = [{ c: -1, r: -1, k: 'city' }, { c: 0, r: -1, k: 'eclipse' }, { c: 1, r: -1, k: 'wire' }, { c: -1, r: 0, k: 'car' }, { c: 1, r: 0, k: 'spiral' },
  { c: -1, r: 1, k: 'dot' }, { c: 0, r: 1, k: 'city' }, { c: 1, r: 1, k: 'eclipse' }];
const GhostArt: React.FC<{ k: string }> = ({ k }) => {
  const f = 'rgba(255,255,255,.07)', s = 'rgba(255,255,255,.11)';
  switch (k) {
    case 'city': return <g fill={f}>{[0, 1, 2, 3, 4, 5, 6, 7].map((i) => <rect key={i} x={160 + i * 200} y={1080 - 300 - ((i * 137) % 330)} width={150} height={300 + ((i * 137) % 330)} />)}</g>;
    case 'eclipse': return <g><circle cx={960} cy={420} r={190} fill={f} /><circle cx={1010} cy={420} r={180} fill="none" stroke={s} strokeWidth={10} /></g>;
    case 'wire': return <g stroke={s} strokeWidth={8} fill="none"><rect x={500} y={300} width={900} height={500} /><path d="M500 300 L1400 800 M1400 300 L500 800" /></g>;
    case 'car': return <g fill={f}><rect x={560} y={560} width={800} height={150} rx={60} /><rect x={760} y={470} width={380} height={120} rx={40} /><circle cx={740} cy={720} r={70} /><circle cx={1180} cy={720} r={70} /></g>;
    case 'spiral': return <g fill={f}>{Array.from({ length: 22 }, (_, i) => { const a = i * 0.7, r = 60 + i * 20; return <rect key={i} x={960 + Math.cos(a) * r - 26} y={520 + Math.sin(a) * r - 26} width={52} height={52} />; })}</g>;
    default: return <circle cx={960} cy={470} r={120} fill={f} />;
  }
};

// ---------- the component ----------
export const Ch1: React.FC<ShotProps> = () => {
  const t = useT();
  const L = useLayout();
  const v = viewAt(t, L);
  const z = L.fmt === '16x9' ? v.z / 1 : v.z / (t >= T.X4 ? GRIDF9 : 1); // the 16:9-equivalent zoom (LOD thresholds)
  const tilt = L.fmt === '16x9' ? 0 : wallTilt9(t);
  const yaw = yawOf(t);
  const yawOn = yaw > 0.01 && yaw < 179.99;
  const snap = snapOf(t);
  const col = collapseOf(t);
  const breath = breathOf(t);
  const hp = hop(t);
  const lift = 1 - smooth(prog(t, T.ONE + 0.4, COLLAPSE_END + 0.3)); // the hook's "brighter" lift, settling for the clean slate
  const dotRb = dotBaseR(t), dotR = dotRb * (1 + 0.14 * breath);
  const dotY = D.y + hp.dy;
  const rsz = spring(t - T.LOUD, 1.5, 0.8); // s21 artboard resize
  const fit = t >= T.FIT ? spring(t - T.FIT, 1.4, 0.8) : 0; // bar 30: fit the frame to the formation
  const { a1: B1, a2: B2 } = artsOf(L);
  const AA = { x: lerp(B1.x, B2.x, rsz), y: lerp(B1.y, B2.y, rsz), w: lerp(B1.w, B2.w, rsz), h: lerp(B1.h, B2.h, rsz) };
  const A = { x: lerp(AA.x, A3.x, fit), y: lerp(AA.y, A3.y, fit), w: lerp(AA.w, A3.w, fit), h: lerp(AA.h, A3.h, fit) };
  const ground = t < T.ONE ? mixHex(P.ground0, P.ground, smooth(prog(t, T.START, T.START + 1.5))) : mixHex(P.ground, P.groundEnd, smooth(prog(t, T.ONE, COLLAPSE_END)));
  const canvas = mixHex(P.canvas, P.canvasCH, smooth(prog(t, T.START, T.START + 1.5)));
  const P3 = (x: number, y: number, zz = 0) => { if (!yawOn) return { x: D.x + (x - D.x), y: D.y + (y - D.y), s: 1, depth: zz }; const q = project(x - D.x, y - D.y, zz, yaw); return { x: D.x + q.x, y: D.y + q.y, s: q.s, depth: q.depth }; };

  // ---- the infinite canvas, ghost artboards, variant tiles (under the original) ----
  const back: React.ReactNode[] = [];
  const front: React.ReactNode[] = []; // s27: collapsing tiles, over the original artboard
  back.push(<rect key="cv" x={-400000} y={-400000} width={800000} height={800000} fill={canvas} />);
  // ghosts: from the hook's pitch around A1 to just outside A2; they fade as the variant copies take their places
  const gIn = clamp((t - T.LOUD) / 0.25), gOut = 1 - smooth(prog(t, T.RUN + 0.1, T.RUN + 0.6));
  if (t >= T.LOUD && gOut > 0 && !yawOn) {
    const off = { x: lerp(2520, 3200, rsz), y: lerp(1560, 1940, rsz) };
    for (const g of GHOSTS) {
      const cx = 960 + g.c * off.x, cy = 540 + g.r * off.y;
      back.push(<g key={`gh${g.c}${g.r}`} opacity={gIn * gOut}><rect x={cx - 960} y={cy - 540} width={1920} height={1080} fill="#0f131d" stroke="rgba(255,255,255,.10)" strokeWidth={3 / v.z} />
        <g transform={`translate(${cx - 960} ${cy - 540})`}><GhostArt k={g.k} /></g></g>);
    }
  }
  // variant tiles
  const tiles: { i: number; j: number; ox: number; oy: number; sc: number; layer: number }[] = [];
  if (t >= T.X4) {
    const sl = (dt: number) => spring(dt, 1.4, 0.78);
    const half = { x: (TILE.w / 2) * 1.05, y: (TILE.h / 2) * 1.05 };
    const visible = (ox: number, oy: number, s: number) => {
      const c = toS(v, TILE.x + TILE.w / 2 + ox, TILE.y + TILE.h / 2 + oy), hw = half.x * v.z * s, hh = half.y * v.z * s;
      const top = tilt > 0 ? 900 : 0; // 9:16 wall: the tipped-back top shows rows above the flat frame
      return c.x + hw > -20 - top && c.x - hw < L.W + 20 + top && c.y + hh > -20 - top && c.y - hh < L.H + 20;
    };
    const R = col > 0 ? { i0: -15, i1: 15, j0: -16, j1: 16 } : t >= T.WALL ? (L.fmt === '16x9' ? { i0: -9, i1: 9, j0: -9, j1: 9 } : { i0: -2, i1: 2, j0: -17, j1: 17 }) : t >= T.X16 ? { i0: -1, i1: 2, j0: -1, j1: 2 } : { i0: 0, i1: 1, j0: 0, j1: 1 };
    for (let j = R.j0; j <= R.j1; j++) for (let i = R.i0; i <= R.i1; i++) {
      if (i === 0 && j === 0) continue;
      const in4 = i >= 0 && i <= 1 && j >= 0 && j <= 1, in16 = i >= -1 && i <= 2 && j >= -1 && j <= 2;
      let ox = i * PITCH.x, oy = j * PITCH.y, sc = 1;
      if (in4) { const k = sl(t - T.X4 - (i + j) * 0.04); ox *= k; oy *= k; }
      else if (in16) { const si = clamp(i, 0, 1), sj = clamp(j, 0, 1), k = sl(t - T.X16 - (Math.abs(i - si) + Math.abs(j - sj)) * 0.04);
        ox = lerp(si * PITCH.x, ox, k); oy = lerp(sj * PITCH.y, oy, k); }
      else { const ring = Math.max(i < -1 ? -1 - i : i - 2, j < -1 ? -1 - j : j - 2); sc = clamp(spring(t - T.WALL - (ring - 1) * 0.05, 1.8, 0.7), 0, 1.1); }
      if (sc <= 0.001) continue;
      tiles.push({ i, j, ox, oy, sc, layer: in4 ? 2 : in16 ? 1 : 0 });
    }
    tiles.sort((a, b) => a.layer - b.layer);
    const lodK = clamp((LOD1 - z) / (LOD1 - LOD0));
    // s27: tiles spiral into the dot in screen space while the camera pushes in
    const v1 = viewAt(T.ONE, L), dS = toS(v, D.x, dotY), dS1 = toS(v1, D.x, D.y);
    for (const tl of tiles) {
      const vv = variant(tl.i, tl.j);
      const cxW = TILE.x + TILE.w / 2, cyW = TILE.y + TILE.h / 2;
      let tr = `translate(${tl.ox} ${tl.oy})`, s = tl.sc;
      if (col > 0) {
        const p0 = toS(v1, cxW + tl.ox, cyW + tl.oy), rel = { x: p0.x - dS1.x, y: p0.y - dS1.y };
        const k = Math.pow(1 - col, 1.5), ps = vortex(rel, col);
        const q = { x: dS.x + (rel.x * Math.cos(ps) - rel.y * Math.sin(ps)) * k, y: dS.y + (rel.x * Math.sin(ps) + rel.y * Math.cos(ps)) * k };
        const fade = clamp(1 - col * 1.6 * (Math.hypot(rel.x, rel.y) / 1100)); // far tiles go first: the wall never shows an edge
        const w = toW(v, q.x, q.y), ss = (v1.z * tl.sc * Math.pow(1 - col, 1.3) * fade) / v.z;
        if (ss * v.z < 0.004) continue;
        const hw = TILE.w * 0.75 * ss * v.z; // on-screen cull (the rotated tile's half diagonal)
        if (q.x + hw < -20 || q.x - hw > L.W + 20 || q.y + hw < -20 || q.y - hw > L.H + 20) continue;
        tr = `translate(${w.x} ${w.y}) scale(${ss}) translate(${-cxW} ${-cyW})`; s = 1;
      } else if (!visible(tl.ox, tl.oy, s)) continue;
      if (vv.upside) tr += ` rotate(180 ${cxW} ${cyW})`;
      if (s !== 1) tr += ` translate(${cxW} ${cyW}) scale(${s}) translate(${-cxW} ${-cyW})`;
      (col > 0 ? front : back).push(<g key={`t${tl.i},${tl.j}`} transform={tr}><TileArt v={vv} t={t} lodK={col > 0 ? Math.max(lodK, clamp((LOD1 - v1.z * Math.pow(1 - col, 1.3)) / (LOD1 - LOD0))) : lodK} z={z} /></g>);
    }
  }

  // ---- the original artboard ----
  const art: React.ReactNode[] = [];
  if (yawOn) {
    const cs = [P3(B2.x, B2.y), P3(B2.x + B2.w, B2.y), P3(B2.x + B2.w, B2.y + B2.h), P3(B2.x, B2.y + B2.h)];
    const pts = cs.map((c) => `${c.x},${c.y}`).join(' ');
    art.push(<polygon key="ab" points={pts} fill={ground} />, <polygon key="abb" points={pts} fill="none" stroke="rgba(255,255,255,.14)" strokeWidth={3 / v.z} />);
  } else {
    art.push(<rect key="abb" x={A.x - 3} y={A.y - 3} width={A.w + 6} height={A.h + 6} fill="none" stroke="rgba(255,255,255,.14)" strokeWidth={3 / v.z} />,
      <rect key="ab" x={A.x} y={A.y} width={A.w} height={A.h} fill={ground} />);
  }
  // the grid (the hook's: lit by the dot and by the kick shockwaves), ticking on the downbeat in s20-s22; fades when zoomed out
  const gridLod = clamp((z - 0.3) / 0.4);
  if (gridLod > 0.01) {
    const metro = t >= T.WORLD && t < T.RUN + 1 ? (1 - smooth(prog(t, T.RUN, T.RUN + 1))) : 0;
    const lastDb = (tt: number) => { let b = -1e9; for (const d of downbeats) { if (d <= tt) b = d; else break; } return b; };
    const tick = metro * Math.exp(-(t - lastDb(t)) / 0.15), lateTick = metro * Math.exp(-(t - BEAT - lastDb(t - BEAT)) / 0.15);
    const sh = kicks.filter((k) => k <= t && k > t - 0.75).map((k) => t - k);
    const lo = toW(v, -60, -60), hi = toW(v, L.W + 60, L.H + 60), pad = yawOn ? 1400 : 0;
    const x0 = Math.max(A.x, lo.x - pad), x1 = Math.min(A.x + A.w, hi.x + pad), y0 = Math.max(A.y, lo.y), y1 = Math.min(A.y + A.h, hi.y);
    const gx0 = Math.ceil((x0 - 24) / 48) * 48 + 24, gy0 = Math.ceil((y0 - 24) / 48) * 48 + 24;
    const pinkRGB = [255, 111, 174], LR = 688;
    const dots: React.ReactNode[] = [];
    for (let y = gy0; y < y1; y += 48) for (let x = gx0; x < x1; x += 48) {
      let a = 0.08 * (1 + lift);
      const late = x === 1176 && y === 264;
      a += 0.12 * (late ? lateTick : tick);
      const dd = Math.hypot(x - D.x, y - dotY);
      for (const d of sh) { const r = 74 + d * 1700; a += 0.24 * Math.exp(-Math.pow((dd - r) / 60, 2)) * Math.pow(1 - d / 0.75, 2); }
      let la = 0;
      if (dd < LR) la = 0.34 * Math.pow(1 - dd / LR, 2) * (0.7 + 0.3 * breath) * (dotRb / R0 * 0.6 + 0.4);
      const k = la / (a + la + 1e-6);
      const c = [255, 255, 255].map((w, i) => Math.round(lerp(w, pinkRGB[i], k)));
      const op = clamp(a + la, 0, 0.9) * gridLod;
      if (op < 0.01) continue;
      const p = P3(x, y);
      const s = 2.2 * p.s;
      dots.push(<rect key={`${x},${y}`} x={p.x - s / 2} y={p.y - s / 2} width={s} height={s} fill={`rgb(${c[0]},${c[1]},${c[2]})`} fillOpacity={op} />);
    }
    art.push(<g key="grid">{dots}</g>);
  }
  // s21: selection outline, corner handles (the resize)
  const selA = clamp((t - (T.LOUD - 0.15)) / 0.15) * (1 - smooth(prog(t, T.LOUD + 1.2, T.LOUD + 1.6)));
  if (selA > 0.01 && !yawOn) {
    const hs = 14 / v.z;
    art.push(<g key="sel" opacity={selA}><rect x={A.x} y={A.y} width={A.w} height={A.h} fill="none" stroke={P.select} strokeWidth={2.5 / v.z} />
      {[[A.x, A.y], [A.x + A.w, A.y], [A.x, A.y + A.h], [A.x + A.w, A.y + A.h], [A.x + A.w / 2, A.y], [A.x + A.w / 2, A.y + A.h], [A.x, A.y + A.h / 2], [A.x + A.w, A.y + A.h / 2]].map(([x, y], i) =>
        <rect key={i} x={x - hs / 2} y={y - hs / 2} width={hs} height={hs} fill="#ffffff" stroke={P.select} strokeWidth={2 / v.z} />)}</g>);
  }

  // ---- the composition: depth-sorted items (far first) ----
  type Item = { d: number; n: React.ReactNode };
  const items: Item[] = [];
  const mask: React.ReactNode[] = [];
  const shineK = prog(t, SHINE - 0.05, SHINE + 0.5);
  const shineOn = shineK > 0 && shineK < 1;
  // beams (s18): soft amber wedges from behind the dot, sweeping; gone by the formation
  const beamA = smooth(prog(t, T.FIRE, T.FIRE + 0.5)) * (1 - smooth(prog(t, T.RUN + 0.6, T.FORM - 0.4)));
  if (beamA > 0.01) {
    const base = t * 9 + theta(t) * 0.3;
    const wedges = Array.from({ length: 6 }, (_, b) => {
      const a = (base + b * 60) * DEG, w = (1.5 + 0.7 * kickEnv(t)) * DEG, Ln = 2600;
      const p1 = P3(D.x + Math.cos(a - w) * Ln, dotY + Math.sin(a - w) * Ln), p2 = P3(D.x + Math.cos(a + w) * Ln, dotY + Math.sin(a + w) * Ln);
      return <polygon key={b} points={`${D.x},${dotY} ${p1.x},${p1.y} ${p2.x},${p2.y}`} fill="url(#ch1beam)" />;
    });
    items.push({ d: 5000, n: <g key="beams" opacity={beamA * (0.75 + 0.25 * kickEnv(t))}>{wedges}</g> });
  }
  // elements
  const coll = col > 0;
  const v1 = coll ? viewAt(T.ONE, L) : null;
  for (const e of ELS) {
    const pre = prePos(e, t, dotR);
    if (!pre && snap <= 0) continue;
    let x: number, y: number, s: number, rot: number, depth: number, sy = 1;
    const fsc = e.kind === 'floor' ? 1 : SLOT / e.size;
    if (pre && t < T.FORM + 1.3) {
      const q = project(pre.x, pre.y, pre.z, yaw);
      const preX = D.x + q.x, preY = dotY + q.y, preS = pre.sc * q.s;
      if (snap > 0) {
        const sp = slotPos(e, V0, t);
        x = lerp(preX, D.x + sp.x, snap); y = lerp(preY, D.y + sp.y, snap); s = lerp(preS, fsc, snap); rot = lerp(pre.rot, sp.rot, snap);
        sy = lerp(pre.sy ?? 1, 1, clamp(snap));
      } else { x = preX; y = preY; s = preS; rot = pre.rot; sy = pre.sy ?? 1; }
      depth = lerp(q.depth, -1 - e.i * 0.01, clamp(snap));
    } else {
      const sp = slotPos(e, V0, t); x = D.x + sp.x; y = D.y + sp.y; s = fsc; rot = sp.rot; depth = -1 - e.i * 0.01;
    }
    if (coll && v1) {
      // spiral into the dot (screen space), like the outro's undo
      const sp1 = slotPos(e, V0, T.ONE), p0 = toS(v1, D.x + sp1.x, D.y + sp1.y), c0 = toS(v1, D.x, D.y), dS = toS(v, D.x, dotY);
      const rel = { x: p0.x - c0.x, y: p0.y - c0.y }, k = Math.pow(1 - col, 1.5), ps = vortex(rel, col);
      const w = toW(v, dS.x + (rel.x * Math.cos(ps) - rel.y * Math.sin(ps)) * k, dS.y + (rel.x * Math.sin(ps) + rel.y * Math.cos(ps)) * k);
      x = w.x; y = w.y; s = (fsc * v1.z * Math.pow(1 - col, 1.3)) / v.z; rot += 300 * col;
      if (s * v.z < 0.02) continue;
    }
    const kick = e.g === 'A' ? kickPulse(t) * (e.kind === 'btn' ? 0.05 : 0.08) : 0;
    const sx = (e.kind === 'floor' && snap < 0.5 ? 1 + 0.05 * clamp((bassAt(t - (e.k ?? 0) * 0.025) - 0.25) / 0.7) : 1) * hp.sx;
    const tf = `translate(${x} ${y}) rotate(${e.kind === 'btn' || e.kind === 'mini' ? 0 : rot}) scale(${s * (1 + kick) * sx} ${s * (1 + kick) * sy * hp.sy})`;
    const formation = clamp(snap);
    const shapeEl = <Shape e={e} col={e.col} col2={e.col2} size={e.kind === 'floor' ? 400 : e.size} t={t} formation={formation} spin={rot} />;
    items.push({ d: depth + (e.g === 'F' ? 1 : 0), n: <g key={`e${e.i}`} transform={tf}>{shapeEl}</g> });
    if (shineOn) mask.push(<g key={`m${e.i}`} transform={tf}><Shape e={e} col="#fff" size={e.kind === 'floor' ? 400 : e.size} t={t} mono formation={formation} /></g>);
  }
  // the tower's roof (setback + antenna + a white light on the beat), on the top floor once it's built
  const top = ELS[ELS.length - 1];
  const roofIn = t >= top.born ? spring(t - top.born - SIX, 3, 0.7) : 0;
  if (roofIn > 0 && snap < 1) {
    const pre = prePos(top, t, dotR)!, q = project(pre.x, pre.y - 31 - 18, pre.z, yaw);
    const x = D.x + q.x, y = dotY + q.y, s = q.s * clamp(roofIn, 0, 1.1), light = 0.35 + 0.65 * kickEnv(t, 0.3);
    items.push({ d: q.depth + 0.5, n: <g key="roof" transform={`translate(${x} ${y}) scale(${s})`} opacity={1 - clamp(snap)}>
      <rect x={-130} y={-36} width={260} height={36} fill={mixHex(P.towerBody, P.amber, 0.92)} /><rect x={-130} y={-36} width={10} height={36} fill={P.gold} />
      <rect x={-3} y={-126} width={6} height={92} fill={P.towerEdge} /><circle cy={-130} r={9} fill={P.core} opacity={light} /></g> });
  }
  // the lid flies off with the spin (s19)
  if (t < T.SPIN + 1.2) {
    const btn = ELS[0];
    const tb = Math.min(t, T.SPIN), pb = prePos(btn, tb, R0)!, qb = project(pb.x, pb.y, pb.z, 0);
    const dt = Math.max(0, t - T.SPIN);
    const lx = D.x + qb.x + 900 * dt, ly = D.y + qb.y - 700 * dt + 1300 * dt * dt, lr = 420 * dt;
    items.push({ d: -400, n: <g key="lid" transform={`translate(${lx} ${ly}) rotate(${lr})`}><Lid /></g> });
  }
  // the dot: glow, rings, the kick ripples (the hook's), s21's speaker-cone rings
  {
    const dotS = (() => { if (!coll) return { sx: hp.sx, sy: hp.sy }; const w = impact(t - COLLAPSE_END, 3.0, 7.5); return { sx: 1 + 0.18 * w, sy: 1 - 0.18 * w }; })();
    const sh = kicks.filter((k) => k <= t && k > t - 0.75).map((k) => t - k);
    const cone = smooth(prog(t, T.LOUD, T.LOUD + 0.1)) * (1 - smooth(prog(t, T.RUN, T.FORM)));
    const lw = Math.max(1, 1 / Math.max(0.2, v.z));
    const n = (
      <g key="dot">
        {sh.map((d, i) => <circle key={`rp${i}`} cx={D.x} cy={dotY} r={dotRb + d * 1700 * 0.55} fill="none" stroke={mixC('rgba(255,255,255,1)', C.pink, 0.5)} strokeOpacity={0.42 * Math.pow(1 - d / 0.75, 1.6)} strokeWidth={2 * lw} />)}
        {cone > 0.01 && sh.map((d, i) => <circle key={`cn${i}`} cx={D.x} cy={dotY} r={dotRb + 40 + d * 2400} fill="none" stroke={P.core} strokeOpacity={0.16 * cone * Math.pow(1 - d / 0.75, 1.5)} strokeWidth={12} />)}
        {[3, 2, 1].map((i) => <circle key={`ring${i}`} cx={D.x} cy={dotY} r={dotRb + i * 34 + breath * i * 7} fill="none" stroke={`rgba(255,255,255,${0.05 * i * (1 + 0.6 * lift)})`} strokeWidth={2 * lw} />)}
        <g transform={`translate(${D.x} ${dotY}) scale(${dotS.sx} ${dotS.sy})`}>
          <circle r={dotR * 1.25} fill={C.pink} opacity={0.1 * lift} style={{ filter: 'blur(28px)' }} />
          <circle r={dotR} fill={C.pink} />
        </g>
      </g>
    );
    items.push({ d: 0, n });
    if (shineOn) mask.push(<circle key="mdot" cx={D.x} cy={dotY} r={dotR} fill="#fff" />);
  }
  // s23: the formation lands: one white ring opens from it on bar 29
  const fr = (t - T.FORM) / 0.6;
  if (fr >= 0 && fr <= 1) items.push({ d: -2, n: <circle key="fring" cx={D.x} cy={D.y} r={420 + 260 * easeOut3(fr)} fill="none" stroke="rgba(255,255,255,.5)" strokeOpacity={1 - fr} strokeWidth={4 / v.z} /> });
  items.sort((a, b) => b.d - a.d);

  const svgT = `translate(${v.sx} ${v.sy}) scale(${v.z}) translate(${-v.cx} ${-v.cy})`;
  const band = lerp(-0.25, 1.25, easeInOut3(shineK));
  return (
    <AbsoluteFill style={{ background: canvas, overflow: 'hidden' }}>
      <svg width={L.W} height={L.H} style={tilt > 0.01 ? { position: 'absolute', left: 0, top: 0, transform: `perspective(1700px) rotateX(${tilt}deg)`, transformOrigin: '540px 1000px' } : { position: 'absolute', left: 0, top: 0 }}>
        <defs>
          <radialGradient id="ch1beam" gradientUnits="userSpaceOnUse" cx={D.x} cy={dotY} r={2600}>
            <stop offset="0" stopColor={P.amber} stopOpacity={0.3} /><stop offset="0.3" stopColor={P.amber} stopOpacity={0.09} /><stop offset="0.75" stopColor={P.amber} stopOpacity={0} />
          </radialGradient>
          <radialGradient id="ch1glow"><stop offset="0" stopColor={C.pink} stopOpacity={0.16} /><stop offset="1" stopColor={C.pink} stopOpacity={0} /></radialGradient>
          <linearGradient id="ch1shine" gradientUnits="userSpaceOnUse" x1={D.x - 1300} y1={D.y - 900} x2={D.x + 1300} y2={D.y + 900}>
            <stop offset={clamp(band - 0.09)} stopColor="#fff" stopOpacity={0} /><stop offset={clamp(band)} stopColor={P.core} stopOpacity={0.6} /><stop offset={clamp(band + 0.09)} stopColor="#fff" stopOpacity={0} />
          </linearGradient>
          {shineOn && <mask id="ch1mask" maskUnits="userSpaceOnUse" x={-6000} y={-6000} width={12000} height={12000}>{mask}</mask>}
        </defs>
        <g transform={svgT}>
          {back}
          {art}
          {front}
          {items.map((it) => it.n)}
          {shineOn && <rect x={D.x - 3000} y={D.y - 3000} width={6000} height={6000} fill="url(#ch1shine)" mask="url(#ch1mask)" />}
        </g>
      </svg>
      <ScreenText t={t} v={v} L={L} A={AA} rsz={clamp(rsz)} />
    </AbsoluteFill>
  );
};

// ---------- screen-space UI and text: payoff flights, the dimension pill, the Run chip, the collaborator cursor ----------
const CH = 0.6; // JetBrains Mono advance (em)
const FLIGHTS: { id: string; x: number; y: number; screen?: { x: number; y: number } }[] = [
  { id: 's18', x: D.x, y: D.y - R0 - 70 }, { id: 's19', x: D.x, y: D.y }, { id: 's20', x: D.x, y: D.y + R0 + 120 },
  { id: 's21', x: D.x, y: D.y }, { id: 's22', x: D.x, y: -420 }, { id: 's23', x: 0, y: 0, screen: { x: 960, y: 96 } },
  { id: 's24', x: D.x, y: D.y }, { id: 's25', x: D.x, y: D.y }, { id: 's26', x: D.x, y: D.y }, { id: 's27', x: D.x, y: D.y },
];
const norm = (w: string) => w.replace(/[^\w']/g, '').toLowerCase();
const ScreenText: React.FC<{ t: number; v: View; L: Layout; A: { x: number; y: number; w: number; h: number }; rsz: number }> = ({ t, v, L, A, rsz }) => {
  const els: React.ReactNode[] = [];
  const is16 = L.fmt === '16x9';
  // the grammar: 0.30 s before each land the payoff word lifts out of the bar and flies to what it changes
  for (const f of FLIGHTS) {
    // s23 already has the animated Run chip at this destination. A second flying
    // "Run" overlaps its entrance and reads as a ghost label around frame 1542.
    if (f.id === 's23') continue;
    const s = tshot(f.id); if (!s || !s.payoff) continue;
    const t0 = s.payoff.lift, t1 = s.land;
    if (t < t0 || t > t1 + 0.12) continue;
    // the payoff word = the matching word whose sung onset is closest to the payoff time, in the line on screen at the lift
    let best = { li: -1, wi: -1, d: Infinity };
    for (const li of s.lines) { const ln = lines[li]; for (let wi = 0; wi < ln.words.length; wi++) { if (norm(ln.words[wi]) !== norm(s.payoff.word)) continue; const d = Math.abs(ln.wt[wi] - s.payoff.t); if (d < best.d) best = { li, wi, d }; } }
    if (best.li < 0) continue;
    const ln = lines[best.li], words = ln.text.split(' ');
    if (promptAt(t0).lineIndex !== best.li) continue;
    const idx = words.slice(0, best.wi).join(' ').length + (best.wi ? 1 : 0), word = words[best.wi].replace(/[.,!?]$/, '');
    const bc = barCharPos(L, ln.text, idx), font = L.bar.font;
    const tgt = f.screen ? (is16 ? f.screen : { x: L.W / 2, y: 300 }) : toS(viewAt(t1, L), f.x, f.y);
    const p = clamp((t - t0) / (t1 - t0)), e = easeInOut3(p);
    const cx0 = bc.x + (word.length * bc.ch) / 2, y0 = bc.y;
    const ctrl = { x: lerp(cx0, tgt.x, 0.5), y: Math.min(y0, tgt.y) - 140 };
    const bx = (1 - e) * (1 - e) * cx0 + 2 * (1 - e) * e * ctrl.x + e * e * tgt.x, by = (1 - e) * (1 - e) * y0 + 2 * (1 - e) * e * ctrl.y + e * e * tgt.y;
    const size = lerp(font, 34, e), op = t > t1 ? 0 : 1 - smooth(prog(p, 0.72, 1));
    els.push(<div key={`fly${f.id}`} data-fit="off" style={{ ...MED, position: 'absolute', left: bx, top: by, transform: 'translate(-50%,-50%)', fontSize: size, lineHeight: 1,
      color: '#f4f1f6', opacity: op, whiteSpace: 'nowrap', textShadow: '0 0 18px rgba(255,255,255,.35)' }}>{word}</div>);
    const ar = (t - t1) / 0.12;
    if (ar >= 0 && ar <= 1) els.push(<div key={`spk${f.id}`} style={{ position: 'absolute', left: tgt.x - 10 - 40 * ar, top: tgt.y - 10 - 40 * ar, width: 20 + 80 * ar, height: 20 + 80 * ar,
      borderRadius: '50%', border: '2px solid rgba(255,255,255,.6)', opacity: 1 - ar, boxSizing: 'border-box' }} />);
  }
  // s21: the artboard's size, live, in a selection-blue pill above its top edge
  const pillA = clamp((t - (T.LOUD - 0.1)) / 0.15) * (1 - smooth(prog(t, T.LOUD + 1.2, T.LOUD + 1.6)));
  if (pillA > 0.01) {
    const top = toS(v, A.x + A.w / 2, A.y);
    const yTop = Math.max(is16 ? 24 : 262, top.y - 78);
    const label = is16 ? `${Math.round(lerp(1920, 3840, rsz))} × ${Math.round(lerp(1080, 2160, rsz))}` : `${Math.round(lerp(1080, 2160, rsz))} × ${Math.round(lerp(1920, 3840, rsz))}`;
    els.push(<div key="dims" style={{ ...MED, position: 'absolute', left: top.x, top: yTop, transform: `translateX(-50%) scale(${0.9 + 0.1 * pillA})`, height: 64, padding: '0 22px',
      boxSizing: 'border-box', display: 'flex', alignItems: 'center', background: P.select, color: '#0b1020', borderRadius: 12, fontSize: 34, lineHeight: '40px', whiteSpace: 'nowrap', opacity: pillA }}>{label}</div>);
    void rsz;
  }
  // s23: the Run chip drops in on the lift, presses on the land, its progress fills to the formation snap
  const s23 = tshot('s23');
  const chipIn = t >= s23.payoff.lift ? spring(t - s23.payoff.lift, 2.2, 0.7) : 0;
  const chipOut = smooth(prog(t, T.FORM + 0.45, T.FORM + 0.85));
  if (chipIn > 0 && chipOut < 1) {
    const press = t >= T.RUN ? Math.exp(-(t - T.RUN) / 0.09) * clamp((t - T.RUN + 0.034) / 0.034) : 0;
    const run = clamp((t - T.RUN) / (T.FORM - T.RUN)), done = t >= T.FORM ? Math.exp(-(t - T.FORM) / 0.25) : 0;
    const cx = is16 ? 960 : 260, cy = is16 ? 96 : 300;
    // 9:16: it rises 40 px into place and fades out in place (never through the top 13%)
    const y = is16 ? cy - (1 - chipIn) * 170 - chipOut * 170 : cy + (1 - Math.min(1, chipIn)) * 40;
    const chipA = is16 ? 1 : clamp(chipIn * 1.5) * (1 - chipOut);
    els.push(<div key="run" style={{ position: 'absolute', left: cx, top: y, transform: `translate(-50%,-50%) scale(${1 - 0.08 * press})`, height: 68, padding: '0 30px 0 24px', boxSizing: 'border-box',
      display: 'flex', alignItems: 'center', gap: 16, opacity: is16 ? undefined : chipA, background: mixC('rgba(20,24,36,.92)', P.select, 0.85 * press + 0.5 * done), border: `2px solid ${t >= T.RUN ? P.select : 'rgba(255,255,255,.2)'}`, borderRadius: 16,
      boxShadow: '0 12px 30px rgba(0,0,0,.45)', overflow: 'hidden' }}>
      <svg width={24} height={26} style={{ flex: 'none' }}><polygon points="2,1 23,13 2,25" fill={press > 0.3 ? '#0b1020' : '#f4f1f6'} /></svg>
      <span style={{ ...MED, fontSize: 34, lineHeight: '40px', color: press > 0.3 ? '#0b1020' : '#f4f1f6', whiteSpace: 'nowrap' }}>Run</span>
      {run > 0 && <div style={{ position: 'absolute', left: 0, bottom: 0, height: 5, width: `${run * 100}%`, background: P.select }} />}
    </div>);
  }
  // s24-s25: the model's cursor (a collaborator cursor) types the parentheses: "(run it)"
  const g0 = tshot('s24').payoff.t - 0.45, g1 = tshot('s25').land + 0.35;
  if (t >= g0 - 0.3 && t <= g1 + 0.5) {
    // pointer x follows the end of the typed text (average of the last 4 frames: smooth, still a pure function of t)
    const ends = [0, 1, 2, 3].map((k) => { const pt = promptAt(t - k / 30); return barCharPos(L, pt.lineIndex >= 0 ? lines[pt.lineIndex].words.join(' ') : pt.text, pt.text.length).x; });
    const ex = ends.reduce((a, b) => a + b, 0) / ends.length + 40;
    const inK = spring(t - (g0 - 0.3), 2, 0.75), outK = smooth(prog(t, g1, g1 + 0.5));
    const barTop = is16 ? L.bar.y : (L.bar.bottom ?? 0) - barHeight(L, barRows(L, (() => { const pt = promptAt(t); return pt.lineIndex >= 0 ? lines[pt.lineIndex].words.join(' ') : ''; })()).length);
    const tip = { x: ex + (1 - inK) * 260 + outK * 320, y: barTop - 70 - outK * 120 };
    const tagLeft = !is16 && tip.x + 36 + 150 > 856; // 9:16: the tag flips to the pointer's left before it reaches the button column
    const op = clamp(inK * 1.5) * (1 - outK);
    const tagL = tagLeft ? tip.x - 18 - 150 : tip.x + 36, tagOp = is16 ? op : op * clamp((856 - (tagL + 150)) / 40) * clamp((tagL - 116) / 40); // 9:16: never into the button column
    els.push(<svg key="gcur" width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: op }}>
      <g transform={`translate(${tip.x} ${tip.y}) scale(1.1)`}><path d="M0 0 L0 40 L10 30 L17 46 L24 43 L17 28 L31 28 Z" fill={P.blue} stroke="#0b1020" strokeWidth={2.5} strokeLinejoin="round" /></g></svg>);
    els.push(<div key="gtag" style={{ ...MED, position: 'absolute', left: tagL, top: tip.y - 14, height: 66, padding: '0 20px', boxSizing: 'border-box', display: 'flex', alignItems: 'center',
      background: P.blue, color: '#0b1020', borderRadius: 12, fontSize: 34, lineHeight: '40px', whiteSpace: 'nowrap', opacity: tagOp }}>model</div>);
  }
  return <>{els}</>;
};
