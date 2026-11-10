// What a section file exports, and the small helpers builders share. A section file owns its slots (beats.ts `sec`):
//   builders: { <slot id>: (ctx) => Partial<Frame> }   what the frame changes in that slot (camera, grade, flows, sparks...)
//   camera:   CamKey[]                                  camera keys inside its time range (anchors)
//   stars:    StarKey[]                                 star arrangement keys inside its time range
//   inserts:  Insert[]                                  a finished clip (e.g. a pitch mockup) shown over a slot in the rough cut
import { Anchor } from '../anchor';
import { CamKey } from '../camera';
import { Cam, Flow, Fmt, Frame, Path, Spark, StarKey } from '../types';
import { Grade, GRADE_DEFAULT, RGB } from '../grade';
export type Ctx = {
  t: number; fmt: Fmt; lt: number; u: number; dur: number; // song time, local time in the slot, 0..1 through it, slot length
  slot: { id: string; t0: number; t1: number; plan: string };
  base: Frame; at: (a: Anchor) => number; word: (sec: string, line: number, word: number) => number;
};
export type Out = Partial<Omit<Frame, 'cam' | 'grade'>> & { cam?: Partial<Cam>; grade?: Partial<Grade> };
export type Builder = (c: Ctx) => Out;
export type Insert = { slot: string; src: string; src916?: string; from: number; to?: Anchor; label?: string }; // src under public/; from = song second of the clip's frame 0; shown from max(slot start, from) to `to` (default: slot end)
export type Section = { name: string; builders: Record<string, Builder>; camera?: CamKey[]; stars?: StarKey[]; inserts?: Insert[] };

// ---- helpers ----
export const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
export const smooth = (a: number, b: number, x: number) => { const u = clamp01((x - a) / (b - a)); return u * u * (3 - 2 * u); };
export const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
// an envelope: 0 before t0, rises over atk, holds, falls over rel after t1 (t1 defaults to t0)
export const env = (t: number, t0: number, atk: number, rel: number, t1 = t0) => (t < t0 ? 0 : t < t0 + atk ? smooth(t0, t0 + atk, t) : t < t1 + atk ? 1 : 1 - smooth(t1 + atk, t1 + atk + rel, t));
// a sharp hit that decays (for per-word / per-beat pulses): sum over times
export const hits = (t: number, times: number[], decay = 0.35, atk = 0.1) => times.reduce((s, h) => s + (t < h ? 0 : (t - h < atk ? smooth(0, atk, t - h) : Math.exp(-(t - h - atk) / decay))), 0);
export const C = { her: GRADE_DEFAULT.herColor, violet: GRADE_DEFAULT.violetColor, his: GRADE_DEFAULT.hisColor, white: [1, 1, 1] as RGB, red: [1.0, 0.18, 0.08] as RGB, teal: [0.1, 1.0, 0.7] as RGB };
// (earth_cut2, gate 7) PALETTE.md swatches, engine linear: his = ember / filament / overheat; hers = biolume / aurora; type = ivory
export const PAL = { ember: [1.0, 0.254, 0.047] as RGB, filament: [1.0, 0.658, 0.323] as RGB, overheat: [1.0, 0.07, 0.024] as RGB, ivory: [0.888, 0.839, 0.753] as RGB, biolume: [0.028, 0.745, 0.807] as RGB, aurora: [0.27, 0.125, 0.913] as RGB, rose: [0.807, 0.328, 0.462] as RGB };
export const flow = (path: Path, head: number, o: Partial<Flow> = {}): Flow => ({ path, head, tail: 0.25, color: C.her, size: 5, intensity: 1, ...o });
export const spark = (x: number, y: number, o: Partial<Spark> = {}): Spark => ({ x, y, size: 14, color: C.his, intensity: 1.4, ...o });
// a few of her great rivers as [lat, lon] polylines, mouth last (light flows downstream toward the sea, or reversed)
export const RIVERS: Record<string, [number, number][]> = {
  nile: [[-2.3, 29.3], [3.6, 32.0], [9.5, 31.6], [15.6, 32.5], [19.0, 33.0], [22.0, 31.5], [24.1, 32.9], [27.2, 31.2], [30.0, 31.2], [31.5, 31.0]],
  congo: [[-11.0, 27.0], [-7.0, 26.5], [-2.0, 25.2], [0.5, 25.2], [2.0, 22.0], [1.0, 18.0], [-2.0, 16.4], [-4.3, 15.3], [-6.0, 12.4]],
  amazon: [[-10.0, -75.0], [-4.5, -73.5], [-3.8, -70.0], [-3.1, -64.0], [-3.1, -60.0], [-2.5, -56.0], [-1.9, -53.0], [-1.0, -50.5], [0.0, -49.0]],
  niger: [[9.5, -10.5], [12.6, -8.0], [14.5, -4.2], [16.8, -3.0], [16.3, -0.1], [13.5, 2.1], [11.0, 4.0], [7.8, 6.7], [5.3, 6.4], [4.3, 6.0]],
};
export const reverse = <X>(a: X[]) => a.slice().reverse();
