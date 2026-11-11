// The city's clock (V2 -> POST2a, s28-s45, 73.12-116.21): every world change is a shot's `land` from timeline.json
// (shots.yaml). Nothing hard-coded except the beat counts the shots name ("beat 3", "beat 4").
import { beats, tshot } from '../../timing';

const L = (id: string) => tshot(id).land;
export const T = {
  CITY: L('s28'), RAIN: L('s29'), CAR: L('s30'), LIGHTS: L('s31'), GUYS: L('s32'), WIRED: L('s33'), PIGEONS: L('s34'),
  GRAV: L('s35'), BIRDS: L('s36'), ZERO: L('s37'), IMPACT: L('s38'), FIRE: L('s39'), SPIN: L('s40'), WHOLE: L('s41'),
  LOUD: L('s42'), TOWER: L('s43'), RUN: L('s44'), PASS: L('s45'), END: L('s46'),
};
/** the n-th beat at or after t (n = 0: the beat at/after t; lands are rounded to 0.01 s, so 20 ms early still counts) */
export const beatAfter = (t: number, n = 0) => { const i = beats.findIndex((b) => b >= t - 0.02); return beats[Math.min(beats.length - 1, i + n)]; };
export const BEAT = beatAfter(T.CITY, 1) - beatAfter(T.CITY, 0);
export const SIXTEENTH = BEAT / 4;
// E2 (ROUGHCUT_PLAN audio edits): the music is out 92.75-94.70; nothing moves on the drums in there
export const E2 = { cut: T.ZERO, back: T.IMPACT };
export const inSilence = (t: number) => t >= E2.cut && t < E2.back;
// named beats inside shots
export const HIGHER = [beatAfter(T.PIGEONS, 1), beatAfter(T.PIGEONS, 2)]; // s34: the flock climbs on beats 2 and 3
export const TOUCH = beatAfter(T.ZERO, 3);                                   // s38: the car touches down on beat 4 (94.21)
export const SHINE = beatAfter(T.SPIN, 2);                                   // s40: 'shine' on beat 3
export const LOCK = beatAfter(T.RUN, 8);                                     // s44: bar 57 ('do'): the still pose
export const BURSTS = [T.FIRE, beatAfter(T.FIRE, 0) + 0.235, beatAfter(T.FIRE, 1), beatAfter(T.FIRE, 2), beatAfter(T.FIRE, 3)];
