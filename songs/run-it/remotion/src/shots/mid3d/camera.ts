// The 3D middle's camera: one path, pure function of time, read from the per-shot JSONs in ./cam (conventions in
// cam/_make.py). The same THREE.PerspectiveCamera drives the render (Rig) and the screen projection of 3D anchors for
// the HTML layer (labels, flying words, the cursor), so they can never disagree.
import * as THREE from 'three';
import type { Layout } from '../../theme';
import { BR, bridgeCam, pathTall } from './bridge';
import s46 from './cam/s46.json'; import s47 from './cam/s47.json'; import s48 from './cam/s48.json';
import s49 from './cam/s49.json'; import s50 from './cam/s50.json'; import s51 from './cam/s51.json';
import s52 from './cam/s52.json'; import s53 from './cam/s53.json'; import s54 from './cam/s54.json';
import s55 from './cam/s55.json'; import s56 from './cam/s56.json'; import s57 from './cam/s57.json';
import s58 from './cam/s58.json'; import s59 from './cam/s59.json'; import s60 from './cam/s60.json';
import s61 from './cam/s61.json'; import s62 from './cam/s62.json'; import s63 from './cam/s63.json';

export type CamKey = { t: number; pos: number[]; target: number[]; fov: number; roll: number; cut?: boolean; still?: boolean };
export type CamPath = { shot: string; what: string; keys: CamKey[] };
export const PATHS: CamPath[] = [s46, s47, s48, s49, s50, s51, s52, s53, s54, s55, s56, s57, s58, s59, s60, s61, s62, s63] as CamPath[];

const KEYS: CamKey[] = PATHS.flatMap((p) => p.keys).sort((a, b) => a.t - b.t || (a.cut ? 1 : 0) - (b.cut ? 1 : 0));
// runs between cuts, each interpolated on its own
const RUNS: CamKey[][] = [];
for (const k of KEYS) { if (!RUNS.length || k.cut) RUNS.push([k]); else RUNS[RUNS.length - 1].push(k); }

const chan = (k: CamKey): number[] => [...k.pos, ...k.target, k.fov, k.roll];
/** monotone cubic Hermite (Fritsch-Carlson clamp): never overshoots a key */
function sample(run: CamKey[], t: number): number[] {
  const n = run.length;
  if (t <= run[0].t || n === 1) return chan(run[0]);
  if (t >= run[n - 1].t) return chan(run[n - 1]);
  let i = 0; while (i < n - 2 && t >= run[i + 1].t) i++;
  const a = run[i], b = run[i + 1], A = chan(a), B = chan(b), h = b.t - a.t, u = (t - a.t) / h;
  const tan = (j: number, c: number) => {
    const k = run[j]; if (k.still || j === 0 || j === n - 1) return 0;
    const p = chan(run[j - 1])[c], q = chan(run[j + 1])[c], v = chan(k)[c];
    const d0 = (v - p) / (k.t - run[j - 1].t), d1 = (q - v) / (run[j + 1].t - k.t);
    if (d0 * d1 <= 0) return 0;
    const m = (q - p) / (run[j + 1].t - run[j - 1].t);
    return Math.sign(m) * Math.min(Math.abs(m), 3 * Math.abs(d0), 3 * Math.abs(d1));
  };
  const h00 = 2 * u ** 3 - 3 * u ** 2 + 1, h10 = u ** 3 - 2 * u ** 2 + u, h01 = -2 * u ** 3 + 3 * u ** 2, h11 = u ** 3 - u ** 2;
  return A.map((va, c) => h00 * va + h10 * h * tan(i, c) + h01 * B[c] + h11 * h * tan(i + 1, c));
}

export type Cam = { pos: THREE.Vector3; target: THREE.Vector3; fov: number; roll: number; tall?: { fov: number; offY: number } };
/** the camera at world time t: the match-cut bridge (./bridge.ts: the city's exact camera, then a velocity-matched hand-off)
 *  until the s46 key at 122.08, the per-shot paths after */
export function camAt(t: number): Cam {
  if (t >= BR.CUT - 1e-6 && t < BR.KEY) return bridgeCam(t, (u) => { const c = pathAt(u); return { ...c, tall: pathTall(c.fov) }; });
  return pathAt(t);
}
/** the camera as a format sees it: 9:16 frames carry the tall framing (bridge.ts pathTall) on the s46+ path; 16:9 (incl.
 *  its s58 pillarbox) is untouched */
export const camFor = (c: Cam, fmt: '16x9' | '9x16'): Cam => {
  if (fmt !== '9x16' || c.tall) return c;
  // the s58 car set (x > 2500): 3.1 m lower, so after the roll the car climbs nearer the centre of the tall frame
  const low = c.pos.x > 2500 ? new THREE.Vector3(0, -3.1, 0) : null;
  return { ...c, pos: low ? c.pos.clone().add(low) : c.pos, target: low ? c.target.clone().add(low) : c.target, tall: pathTall(c.fov) };
};
function pathAt(t: number): Cam {
  let run = RUNS[0];
  for (const r of RUNS) if (t >= r[0].t - 1e-6) run = r;
  const v = sample(run, t);
  return { pos: new THREE.Vector3(v[0], v[1], v[2]), target: new THREE.Vector3(v[3], v[4], v[5]), fov: v[6], roll: v[7] };
}

/** vertical fov for this frame's aspect: 16:9 uses the path's value; taller frames keep the 16:9 horizontal-ish coverage
 *  (a phone frame sees the same height x 1.6, so the 9:16 deliverable isn't a keyhole). */
export const fovFor = (fov: number, aspect: number) => aspect >= 1.7 ? fov
  : (2 * Math.atan(Math.tan((fov * Math.PI) / 360) * Math.min(1.6, 1.7778 / aspect)) * 180) / Math.PI;

/** A THREE camera set exactly as the render uses it. roll + = picture turns counter-clockwise. */
export function makeCamera(c: Cam, aspect: number, fovOverride?: number) {
  // tall frames during the bridge: the city's F 1600 with its centre at 0.47 H (a principal-point offset)
  const tall = aspect < 1.7 && c.tall && fovOverride === undefined ? c.tall : null;
  const H = 1000, W = H * aspect, Hf = tall ? H * (1 + tall.offY) : H;
  const cam = new THREE.PerspectiveCamera(fovOverride ?? (tall ? tall.fov : fovFor(c.fov, aspect)), tall ? W / Hf : aspect, 0.05, 6000);
  if (tall && tall.offY > 1e-6) cam.setViewOffset(W, Hf, 0, tall.offY * H, W, H);
  cam.position.copy(c.pos);
  cam.up.set(0, 1, 0);
  cam.lookAt(c.target);
  cam.rotateZ((-c.roll * Math.PI) / 180); // rotateZ(+) turns the camera CCW = the picture CW, so picture-CCW roll = -roll
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();
  return cam;
}

/** world point -> screen px inside a viewport {x,y,w,h} of the layout; behind = true when it's behind the camera */
export function project(cam: THREE.PerspectiveCamera, p: THREE.Vector3 | number[], vp: { x: number; y: number; w: number; h: number }) {
  const v = Array.isArray(p) ? new THREE.Vector3(p[0], p[1], p[2]) : p.clone();
  const behind = v.clone().applyMatrix4(cam.matrixWorldInverse).z > 0;
  v.project(cam);
  return { x: vp.x + ((v.x + 1) / 2) * vp.w, y: vp.y + ((1 - v.y) / 2) * vp.h, behind };
}
export type VP = { x: number; y: number; w: number; h: number };
export const fullVP = (L: Layout): VP => ({ x: 0, y: 0, w: L.W, h: L.H });
