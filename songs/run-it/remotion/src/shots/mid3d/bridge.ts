// The s45 -> s46 match-cut (116.20): the 2.5D city made real. The city's own buildings (city/world.ts, read only) are
// rebuilt as 3D boxes in metres, and the 3D camera reproduces the city's pinhole camera exactly (city/cam.ts poseAt),
// so frame 3486 shows the same buildings in the same pixels. The "pass 2 · shadows" wipe (Mid3D.tsx) swaps the 2.5D
// picture for this 3D one top -> bottom while the push keeps accelerating; then the camera hands off (position,
// velocity, fov) to the s46 path at 122.08 and the city re-lays itself into the 3D world's own near city (NEAR).
//
// Mapping (city px -> metres): x right, y down, z into screen  ->  X right, Y up, Z toward the camera.
//   X = (x - PUSHWIN.cx) * SM + HERO.win.x, Y = (GROUND - y) * SM, Z = -z * SM
// SM is chosen so the window the s45 push heads for lands exactly on the 3D hero window (4, 18, 0): the push target
// never moves, only the buildings around it re-lay.
import * as THREE from 'three';
import { hash, BLDS, CROWN, DROPS, F, GROUND, LAMP, LIGHTS, PIVOT, PUSHWIN, RAIN_EDGE, RAIN_SPAN, RAIN_TOP, RAIN_Z, TOWER, CAR, type Bld as CBld } from '../city/world';
import { camAt as cityCamAt } from '../city/cam';
import { LOCK, T as CT } from '../city/times';
import { clamp, easeInOut3, prog, smooth } from './anim';
import { HERO, NEAR, type Bld } from './world';

/** the city's buildings stand 1.1x their layout height after s38's jump (heightOf: 1 + 0.1 * settled spring) */
export const HS = 1.1;
const HERO_Y_PX = (GROUND - PUSHWIN.cy) * HS;
export const SM = HERO.win.y / HERO_Y_PX; // metres per city px (~0.071: a 44 px floor = 3.1 m, close to NEAR's 2.7 m)
export const mX = (x: number) => (x - PUSHWIN.cx) * SM + HERO.win.x;
export const mY = (y: number) => (GROUND - y) * SM;
export const mZ = (z: number) => -z * SM;
/** a city building's real height (px) and window centre height at t >= the lock */
export const yOf = (b: CBld, y: number) => b.base - (b.base - y) * HS;

// ---------- times ----------
export const BR = {
  CUT: 116.2,              // frame 3486: the first 3D frame (s46 lands 116.21)
  WIPE0: 116.24, WIPE1: 117.3, // pass 2 · shadows: the 2.5D picture wipes off top -> bottom (s45's grammar, slower)
  HAND: 117.3,             // the camera leaves the city's formula here (velocity carried) ...
  KEY: 122.08,             // ... and lands on the s46 path's key (s47 lands)
  LIGHT: 117.95,            // the push window (dark in the city's frozen cycle) switches on as the push lands: the guy is home
};
export const wipeY = (t: number, H: number) => (t < BR.WIPE0 ? -60 : t > BR.WIPE1 ? H + 60 : -60 + (H + 120) * easeInOut3(prog(t, BR.WIPE0, BR.WIPE1)));
/** the city's screen-space look (its sky gradient, its vignette) fading into the 3D world's with pass 3 (reflections, 117.41 -> s47) */
export const bridgeSkyFade = (t: number) => (t < BR.CUT ? 0 : 1 - smooth(prog(t, CT.END + 1.2, 122.08)));

// ---------- the city camera in metres ----------
export type BCam = { pos: THREE.Vector3; target: THREE.Vector3; fov: number; roll: number; tall?: { fov: number; offY: number } };
const FOV169 = (2 * Math.atan(540 / F) * 180) / Math.PI; // 37.3 deg: F 1600 on a 1080-high frame
// 9:16: the city keeps F 1600 on a 1920-high frame with its centre at 0.47 H (City.tsx makeView)
// rc_916: the city's 9:16 frame is x1.25 (F 2000) with its principal point at y 722.5 (the road on 1060), centred in x at
// the match-cut (City.tsx CITY9 / SUBJ9: s45 follows the city's centre, so no horizontal shift there)
const TALL = (() => { const H = 1920, SCY = 1060 - 1.25 * (GROUND - 540), FT = 1.25 * F, Hf = 2 * (H - SCY); return { fov: (2 * Math.atan(Hf / 2 / FT) * 180) / Math.PI, offY: (Hf / 2 - SCY) / H }; })();
function cityCam(t: number): BCam {
  const c = cityCamAt(t);
  const cs = Math.cos(c.yaw), sn = Math.sin(c.yaw);
  const rx1 = c.x - PIVOT.x, rz1 = c.dz - F - PIVOT.z;
  const wx = PIVOT.x + cs * rx1 + sn * rz1, wz = PIVOT.z - sn * rx1 + cs * rz1;
  const pos = new THREE.Vector3(mX(wx), mY(c.y), mZ(wz));
  const dist = pos.z / cs; // along the view to the facade plane Z = 0
  const target = pos.clone().add(new THREE.Vector3(sn, 0, -cs).multiplyScalar(dist));
  return { pos, target, fov: FOV169, roll: 0, tall: { ...TALL } };
}
const chan = (c: BCam) => [c.pos.x, c.pos.y, c.pos.z, c.target.x, c.target.y, c.target.z, c.fov, c.tall!.fov, c.tall!.offY];
const fromChan = (v: number[]): BCam => ({ pos: new THREE.Vector3(v[0], v[1], v[2]), target: new THREE.Vector3(v[3], v[4], v[5]), fov: v[6], roll: 0, tall: { fov: v[7], offY: v[8] } });

/** the bridge camera, 116.20 -> 122.08: the city's own push (exact) until HAND, then a cubic Hermite carrying its
 *  velocity into the s46 path's key at 122.08 (with the path's own velocity there). `pathAt` = the s46+ path. */
export function bridgeCam(t: number, pathAt: (t: number) => BCam): BCam {
  if (t <= BR.HAND) return cityCam(t);
  const H = HANDOFF(pathAt), u = clamp((t - BR.HAND) / H.h);
  const sv = warp(u, H.m0, H.m1, H.lam, H.c) / warp(1, H.m0, H.m1, H.lam, H.c);
  const h00 = 2 * sv ** 3 - 3 * sv ** 2 + 1, h10 = sv ** 3 - 2 * sv ** 2 + sv, h01 = -2 * sv ** 3 + 3 * sv ** 2, h11 = sv ** 3 - sv ** 2;
  return fromChan(H.A.map((a, i) => h00 * a + h10 * H.TA[i] + h01 * H.B[i] + h11 * H.TB[i]));
}
/** The hand-off: a Hermite CURVE from the city's camera at HAND to the path's key at KEY whose end tangents point along
 *  the real velocities (position tangent = the chord length, so the curve can't loop), travelled with a monotone time
 *  warp s(u) whose end slopes give the real speeds: the push's ~28 m/s decays smoothly (never stops, never backs up)
 *  into the path's own speed at 122.08. */
let HCACHE: { A: number[]; B: number[]; TA: number[]; TB: number[]; m0: number; m1: number; lam: number; c: number; h: number } | null = null;
function HANDOFF(pathAt: (t: number) => BCam) {
  if (HCACHE) return HCACHE;
  const e = 1 / 240, h = BR.KEY - BR.HAND;
  const A = chan(cityCam(BR.HAND)), A0 = chan(cityCam(BR.HAND - e));
  const B = chan(pathAt(BR.KEY)), B1 = chan(pathAt(BR.KEY + e));
  const v0 = A.map((a, i) => (a - A0[i]) / e), vB = B.map((b, i) => (B1[i] - b) / e);
  const n3 = (v: number[]) => Math.hypot(v[0], v[1], v[2]);
  const D = n3(B.map((b, i) => b - A[i]));
  const m0 = (n3(v0) * h) / D, m1 = (n3(vB) * h) / D;
  const TA = v0.map((v) => (v * h) / m0), TB = vB.map((v) => (v * h) / m1);
  // the speed profile w'(u) = c + (m0 - c) e^(-a u) + (m1 - c) e^(-a (1 - u)): the push's speed decays, a slow creep
  // (c > 0: never stops), then the path's speed builds into s47; a = the gentlest decay whose creep stays >= CMIN
  const K = (q: number) => (1 - Math.exp(-q)) / q, cOf = (q: number) => (1 - (m0 + m1) * K(q)) / (1 - 2 * K(q));
  const CMIN = 0.18;
  let lo = 0.5, hi = 80; for (let k = 0; k < 80; k++) { const mid = (lo + hi) / 2; if (cOf(mid) < CMIN) lo = mid; else hi = mid; }
  const q = hi, c = cOf(q);
  HCACHE = { A, B, TA, TB, m0, m1, lam: q, c, h };
  return HCACHE;
}
const warp = (u: number, m0: number, m1: number, q: number, c: number) =>
  c * u + ((m0 - c) * (1 - Math.exp(-q * u))) / q + ((m1 - c) * (Math.exp(-q * (1 - u)) - Math.exp(-q))) / q;
/** 9:16 framing of a path camera (LAYOUT_916.md, rc_916): horizontal field 62% of 16:9's (vertical tan x1.96), and a lens
 *  shift up (principal point y 855 of 1920) so the typical shot's horizon sits on y 920: the city band above it, the ocean
 *  and the gold path below it to the bottom of the frame. Verticals stay vertical (a shift, not a pitch). */
export const TALL_K = 1.96, TALL_PY = 855;
export const pathTall = (fov: number) => {
  const H = 1920, f = H / 2 / (Math.tan((fov * Math.PI) / 360) * TALL_K), Hf = 2 * (H - TALL_PY);
  return { fov: (2 * Math.atan(Hf / 2 / f) * 180) / Math.PI, offY: (Hf / 2 - TALL_PY) / H };
};

// ---------- the city's buildings in metres ----------
export type MB = { id: string; x: number; y0: number; z: number; w: number; d: number; h: number; layer: CBld['layer']; colour: string; hero?: boolean; crown?: boolean;
  wins: { x: number; y: number; lit: boolean; k: number; cool: boolean; push: boolean }[]; at: number /* re-lay start */ };
const COL = { front: '#1d2a40', back: '#152034', far: '#111a2b', rear: '#17213a', side: '#141d2c', roof: '#26344d', winOff: '#172235', road: '#0e1522', kerb: '#24324a', frontShade: '#243349' };
export const BCOL = COL;
/** re-lay order: out from the hero window, ~0.9 s across 40 m */
const relayAt = (x: number) => BR.LIGHT + Math.min(1.2, Math.abs(x - HERO.win.x) / 46); // (unused stagger; kept for the props' `at`)
export const CITY_M: MB[] = BLDS.filter((b) => b.layer !== 'far').map((b) => {
  const h = b.h * HS;
  const x = mX(b.x), w = b.w * SM;
  return {
    id: `c${b.id}`, layer: b.layer, x, w, h: h * SM, y0: mY(b.base), z: mZ(b.z + b.d), d: b.d * SM,
    colour: b.layer === 'front' ? COL.front : b.layer === 'back' ? COL.back : COL.rear, hero: b === PUSHWIN.b, crown: b === CROWN,
    // the city's window state from the s44 lock on (City.tsx windowLight: the frozen cycle; rear row: lit0 at 0.8)
    wins: b.wins.map((wn) => { const k = b.layer === 'rear' ? (wn.lit0 ? 0.8 : 0) : hash(Math.floor(wn.r2 * 1000), Math.floor((LOCK - CT.RUN) * 9)) < 0.6 ? 1 : 0;
      return { x: mX(wn.x + 9), y: mY(yOf(b, wn.y + 12)), lit: k > 0, k, cool: wn.cool, push: wn === PUSHWIN.w }; }),
    at: relayAt(x + w / 2),
  };
});
export const NEAR_AT = (b: Bld) => relayAt(b.x + b.w / 2) + 0.22;
export const HERO_NEAR = NEAR.find((b) => b.hero)!;
export const WIN_W = 18 * SM, WIN_H = 24 * HS * SM;

// ---------- street furniture, the tower, the car, the rain (stand-ins of the 2.5D drawings, same places) ----------
export const LIGHTS_M = LIGHTS.map((p, i) => ({ x: mX(p.x), y: mY(p.y), z: mZ(p.z), red: i === 0, at: relayAt(mX(p.x)) }));
export const LAMP_M = { x: mX(LAMP.x), y: mY(LAMP.y), z: mZ(LAMP.z), at: relayAt(mX(LAMP.x)) };
export const TOWER_M = { x: mX(TOWER.x), w: TOWER.w * SM, z: mZ(TOWER.z + TOWER.d), d: TOWER.d * SM, base: mY(TOWER.base), floors: TOWER.floors, floorH: TOWER.floorH * SM,
  at: relayAt(mX(TOWER.x + TOWER.w / 2)) };
export const CAR_M = { x: mX(CAR.x), z: mZ(CAR.z), scale: (1.12 * 1) /* drawn at identity scale 1.12 */ };
export const RAIN_M = { edge: mX(RAIN_EDGE), z: mZ(RAIN_Z), top: mY(RAIN_TOP), span: RAIN_SPAN * SM };
export const rainDrops = (t: number) => {
  const rc = t - CT.RAIN, out: { x: number; y: number; l: number }[] = [];
  for (const d of DROPS) {
    const fd = rc * 1500 * d.v - d.o * RAIN_SPAN; if (fd < 0) continue;
    out.push({ x: mX(d.x), y: mY(RAIN_TOP + (fd % RAIN_SPAN)), l: d.l * SM });
  }
  return out;
};
export const GROUND_M = 0;
