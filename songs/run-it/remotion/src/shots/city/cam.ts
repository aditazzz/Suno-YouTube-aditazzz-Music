// The city camera: a pure function of film time. Keys are "look-at" poses: world point (px, py) on the z = 0 plane appears
// at screen (sx, sy) with scale S; yaw turns the city on its turntable (PIVOT). Scale interpolates in log space (a zoom
// reads as constant speed), everything else linearly, each segment with its own ease.
import { clamp, easeInOut3, easeOut3, impact, lerp, prog, smooth, spring } from '../hook/anim';
import { F, PIVOT, TARGET, PUSHWIN, FLOCK } from './world';
import { LOCK, T } from './times';

export type Pose = { px: number; py: number; S: number; sx: number; sy: number; yaw: number };
export type Cam = { x: number; y: number; dz: number; yaw: number; shx: number; shy: number };
const P = (px: number, py: number, S = 1, sx = 960, sy = 540, yaw = 0): Pose => ({ px, py, S, sx, sy, yaw });
const mix = (a: Pose, b: Pose, k: number): Pose => ({
  px: lerp(a.px, b.px, k), py: lerp(a.py, b.py, k), S: Math.exp(lerp(Math.log(a.S), Math.log(b.S), k)),
  sx: lerp(a.sx, b.sx, k), sy: lerp(a.sy, b.sy, k), yaw: lerp(a.yaw, b.yaw, k),
});
export const ID = P(960, 540);
// the poses
const PUSH28 = P(960, 470, 1.06, 960, 470);
const TRUCK29 = P(850, 515, 1.07, 960, 540);
const PUSH32 = P(TARGET.cx, TARGET.cy, 1.75, 900, 520);
const CU = 1680 / 78;                              // s33 close-up: the three target windows span ~1680 px
const CLOSE = P(TARGET.cx, TARGET.cy, CU, 960, 470);
const CLOSE2 = P(TARGET.cx, TARGET.cy, CU * 1.035, 960, 470);
const SKY34 = P(960, 430, 1, 960, 540);
const SKY35 = P(960, 400, 1, 960, 540);
const DRIFT37 = P(990, 430, 1.05, 960, 540, 0.035);
const UP38 = P(960, 470, 1.0, 960, 540);
const CRANE39 = P(960, 330, 0.96, 960, 540);
const ORBIT40 = P(960, 520, 0.86, 960, 540, 0.36);
const WIDE41 = P(960, 500, 0.8, 960, 540);
const WIDE42 = P(960, 380, 0.5, 960, 540);
const TOWER43 = P(960, -170, 0.52, 960, 540);
const ARC44a = P(960, -40, 0.56, 960, 540, -0.42);
const ARC44b = P(960, 300, 0.64, 960, 540, 0.42);
export const LOCKPOSE = P(960, 360, 0.62, 960, 560, 0.14);
const PUSH45 = P(PUSHWIN.cx, PUSHWIN.cy, 1.55, 1020, 470, 0.05);

/** pose at film time t (before shake) */
export function poseAt(t: number): Pose {
  if (t < T.RAIN) return mix(ID, PUSH28, easeInOut3(prog(t, T.CITY, T.RAIN)));
  if (t < T.CAR - 1.0) return mix(PUSH28, TRUCK29, easeInOut3(prog(t, T.RAIN, T.CAR - 1.0)));
  if (t < T.CAR + 0.5) { // s30: the truck matches the car (constant braking: quadratic ease-out), stops with it, settles
    const k = prog(t, T.CAR - 1.0, T.CAR), e = easeInOut3(k); // eases in as the car enters, stops with it
    const p = mix(TRUCK29, ID, e);
    return { ...p, px: p.px + 6 * impact(t - T.CAR, 2.4, 9) };
  }
  if (t < T.GUYS) return ID;                                                  // s31 locked wide
  if (t < T.WIRED) return mix(ID, PUSH32, smooth(prog(t, T.GUYS, T.WIRED)));    // s32 slow push toward one building
  if (t < T.WIRED + 0.5) return mix(PUSH32, CLOSE, easeInOut3(prog(t, T.WIRED, T.WIRED + 0.5))); // s33 into the window row (fast: he's wired)
  const back0 = T.PIGEONS - 0.75;
  if (t < back0) return mix(CLOSE, CLOSE2, prog(t, T.WIRED + 0.5, back0));    // hold (creep) on the readable screens
  if (t < T.PIGEONS + 0.35) return mix(CLOSE2, SKY34, easeInOut3(prog(t, back0, T.PIGEONS + 0.35))); // pull back + tilt up
  if (t < T.GRAV) return SKY34;
  if (t < T.BIRDS) return mix(SKY34, SKY35, smooth(prog(t, T.GRAV, T.BIRDS))); // s35 slow tilt up
  if (t < T.ZERO) return SKY35;                                                 // s36 locked
  if (t < T.IMPACT) return mix(SKY35, DRIFT37, smooth(prog(t, T.ZERO, T.IMPACT))); // s37 slow drift in the silence
  if (t < T.FIRE) return mix(DRIFT37, UP38, clamp(spring(t - T.IMPACT, 1.4, 0.7), 0, 1.05)); // s38 push up off the impact
  if (t < T.SPIN) return mix(UP38, CRANE39, easeInOut3(prog(t, T.FIRE, T.FIRE + 1.6))); // s39 crane up
  if (t < T.WHOLE) return mix(CRANE39, ORBIT40, easeInOut3(prog(t, T.SPIN, T.WHOLE)));     // s40 the turntable
  if (t < T.LOUD) return mix(ORBIT40, WIDE41, clamp(spring(t - T.WHOLE, 1.3, 0.75), 0, 1.04)); // s41 locked wide
  if (t < T.TOWER) return mix(WIDE41, WIDE42, easeInOut3(prog(t, T.LOUD, T.LOUD + 1.7)));   // s42 pull back
  if (t < T.RUN) return mix(WIDE42, TOWER43, easeInOut3(prog(t, T.TOWER, T.RUN)));          // s43 tilt up the tower
  if (t < LOCK) { const k = prog(t, T.RUN, LOCK); return mix(TOWER43, mix(ARC44a, ARC44b, easeInOut3(k)), smooth(prog(t, T.RUN, T.RUN + 0.8))); }
  if (t < T.PASS) return mix(ARC44b, LOCKPOSE, clamp(spring(t - LOCK, 1.1, 0.8), 0, 1.03)); // the still pose
  // s45: slow push toward one lit window, accelerating into the match-cut (it keeps going in s46)
  return mix(LOCKPOSE, PUSH45, Math.pow(prog(t, T.PASS, T.END + 1.2), 1.6) * 1.0);
}
/** camera at t (pose -> projection params, plus the impact shake) */
export function camAt(t: number): Cam {
  const p = poseAt(t);
  const dz = F * (1 - 1 / p.S);
  // shake: 2 frames on the car's impact (s38), offsets in px
  const fi = Math.round((t - T.IMPACT) * 30);
  const sh = fi === 0 ? [7, -5] : fi === 1 ? [-5, 4] : [0, 0];
  return { x: p.px - (p.sx - 960) / p.S, y: p.py - (p.sy - 540) / p.S, dz, yaw: p.yaw, shx: sh[0], shy: sh[1] };
}
export { PIVOT, FLOCK, easeOut3 };
