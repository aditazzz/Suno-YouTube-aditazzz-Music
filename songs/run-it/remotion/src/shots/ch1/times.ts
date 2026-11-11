// CH1 + POST1 clock (s18-s27, 41.65-73.12): every world change is a shot's `land` from timeline.json. Nothing hard-coded
// except the formation snap on bar 29 (ROUGHCUT_PLAN s23: "every shape snaps into one formation on bar 29 (55.41)").
import { beats, downbeats, tshot } from '../../timing';
import bassRaw from '../../data/bass_ch1.json';

const L = (id: string) => tshot(id).land;
/** the n-th beat at or after t (lands are rounded to 0.01 s, so a beat up to 20 ms before t counts as "at" t) */
export const beatAfter = (t: number, n = 0) => { const i = beats.findIndex((b) => b >= t - 0.02); return beats[Math.min(beats.length - 1, i + n)]; };
const barAfter = (t: number, n = 0) => { const i = downbeats.findIndex((b) => b >= t - 0.02); return downbeats[Math.min(downbeats.length - 1, i + n)]; };

export const T = {
  START: L('s18'),            // 41.65 the hook's s17 hands over
  FIRE: L('s18'), SPIN: L('s19'), WORLD: L('s20'), LOUD: L('s21'), TOWER: L('s22'), RUN: L('s23'),
  FORM: barAfter(L('s23'), 2), // bar 29, 55.41: the formation snap
  FIT: barAfter(L('s23'), 3), // bar 30, 57.38: the artboard fits to the formation (the variant tiles' frame)
  X4: L('s24'), X16: L('s25'), WALL: L('s26'), ONE: L('s27'), CITY: L('s28'),
};
export const BEAT = beatAfter(T.FIRE, 1) - beatAfter(T.FIRE, 0);
export const BAR = 4 * BEAT;
export const SIX = BEAT / 4;
export const SHINE = beatAfter(T.SPIN, 2); // "shine" on beat 3 of bar 23
export const COLLAPSE_END = T.ONE + 1.1;     // the last tile reaches the dot

// the Suno bass stem's level per frame (build/rc_ch1/tools/bass_env.py), 0..1
const bass = bassRaw as { f0: number; fps: number; v: number[] };
export const bassAt = (t: number) => {
  const f = t * bass.fps - bass.f0, i = Math.floor(f), k = f - i;
  const a = bass.v[Math.max(0, Math.min(bass.v.length - 1, i))], b = bass.v[Math.max(0, Math.min(bass.v.length - 1, i + 1))];
  return a + (b - a) * k;
};
