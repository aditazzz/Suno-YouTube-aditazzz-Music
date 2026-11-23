// Cut 7 move curves (PLAN7 §2). A camera is {cx, cy, s, r}: stage point (cx, cy) at the frame centre, scale s, roll r (deg).
//  flow(f, keys, opt): one continuous move through keyframes. Cubic Hermite per channel with Catmull-Rom tangents, scale in log
//    space (a push reads at a constant rate). Ends are MOVING by default (one-sided tangents: the block starts and leaves in motion);
//    opt.start='rest' / opt.land=true ease the open end to zero velocity (only where a block truly starts or lands, §2).
//  pushRate(s0, pct, dur): end scale of a push at pct %/s over dur frames (camera rule: pushes 2.5-4 %/s, punches up to 8 %/s).
//  matched-velocity push-through: give block A `leaveV` and block B `arriveV` the same screen velocity (tangents in flow's opt).
//  handheld(f, seed, amp, roll): low-pass noise (+-amp stage px, +-roll deg); jitter(f, seed, amp): 2-4 px high-frequency buzz.
//  Camera rule (replaces CUT5_PLAN §2f.3): never < 0.5 %/s on any block; drifts 15-40 stage px/s; up to 2.2x on 5760 plates.
import { noise1 } from '../../../ease';

export type CamK = { cx: number; cy: number; s: number; r?: number };
export type Key = CamK & { f: number };
export type FlowOpt = { start?: 'moving' | 'rest'; land?: boolean; v0?: Partial<CamK>; v1?: Partial<CamK> };

const CH = ['cx', 'cy', 's', 'r'] as const;
const val = (k: Key, c: (typeof CH)[number]) => (c === 's' ? Math.log(k.s) : c === 'r' ? k.r ?? 0 : (k as any)[c]);
const herm = (p0: number, p1: number, m0: number, m1: number, t: number) => {
  const t2 = t * t, t3 = t2 * t;
  return (2 * t3 - 3 * t2 + 1) * p0 + (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) * p1 + (t3 - t2) * m1;
};
/** per-frame tangents (Catmull-Rom; ends one-sided, or 0 for rest/land, or given velocities per frame) */
const tangents = (ks: Key[], c: (typeof CH)[number], o: FlowOpt) => ks.map((k, i) => {
  if (ks.length === 1) return 0;
  if (i === 0) {
    if (o.start === 'rest') return 0;
    if (o.v0 && (o.v0 as any)[c] !== undefined) return c === 's' ? (o.v0 as any).s : (o.v0 as any)[c];
    return (val(ks[1], c) - val(k, c)) / (ks[1].f - k.f);
  }
  if (i === ks.length - 1) {
    if (o.land) return 0;
    if (o.v1 && (o.v1 as any)[c] !== undefined) return c === 's' ? (o.v1 as any).s : (o.v1 as any)[c];
    return (val(k, c) - val(ks[i - 1], c)) / (k.f - ks[i - 1].f);
  }
  return (val(ks[i + 1], c) - val(ks[i - 1], c)) / (ks[i + 1].f - ks[i - 1].f);
});
export const flow = (f: number, ks: Key[], o: FlowOpt = {}): Required<CamK> => {
  const out: any = {};
  for (const c of CH) {
    const m = tangents(ks, c, o);
    let v: number;
    if (f <= ks[0].f) v = val(ks[0], c) + m[0] * (f - ks[0].f);            // extrapolate: keeps moving before/after the keys
    else if (f >= ks[ks.length - 1].f) v = val(ks[ks.length - 1], c) + m[ks.length - 1] * (f - ks[ks.length - 1].f);
    else {
      let i = 0; while (ks[i + 1].f < f) i++;
      const a = ks[i], b = ks[i + 1], d = b.f - a.f, t = (f - a.f) / d;
      v = herm(val(a, c), val(b, c), m[i] * d, m[i + 1] * d, t);
    }
    out[c] = c === 's' ? Math.exp(v) : v;
  }
  return out;
};
/** velocity (per frame) of a flow at f: for matching a push-through on the other side of a cut */
export const flowV = (f: number, ks: Key[], o: FlowOpt = {}): Required<CamK> => {
  const a = flow(f - 0.5, ks, o), b = flow(f + 0.5, ks, o);
  return { cx: b.cx - a.cx, cy: b.cy - a.cy, s: Math.log(b.s) - Math.log(a.s), r: b.r - a.r };
};
/** end scale of a push at pct %/s for dur frames, from s0 */
export const pushTo = (s0: number, pct: number, dur: number) => s0 * Math.pow(1 + pct / 100, dur / 30);
/** low-pass hand-held: +-amp stage px, +-roll deg (two octaves of smooth noise, ~0.6 Hz and ~1.7 Hz) */
export const handheld = (f: number, seed = 1, amp = 6, roll = 0.4) => {
  const t = f / 30;
  const n = (k: number) => 0.75 * noise1(t * 0.6, seed * 7 + k) + 0.25 * noise1(t * 1.7, seed * 13 + k);
  return { dx: amp * n(1), dy: amp * 0.8 * n(2), r: roll * n(3) };
};
/** vibration buzz: amp px at ~18 Hz-ish on 30 fps (alternating, seeded, never periodic) */
export const jitter = (f: number, seed = 3, amp = 3) => {
  const h = (n: number) => { const x = Math.sin(n * 91.7 + seed * 47.3) * 43758.5453; return (x - Math.floor(x)) * 2 - 1; };
  return { dx: amp * h(f * 2 + 1), dy: amp * 0.6 * h(f * 2 + 2) };
};
/** speed bumps on the beats: extra log-scale that only ever increases (a velocity surge after each beat frame, never a
 *  reversal), so a push gets beat accents without a punch-in. Multiply the camera scale by exp(bumps(...)). */
export const bumps = (f: number, beats: number[], amt = 0.012, len = 10) => {
  let k = 0;
  for (const b of beats) { const u = Math.min(1, Math.max(0, (f - b) / len)); k += amt * (1 - Math.pow(1 - u, 3)); }
  return k;
};
