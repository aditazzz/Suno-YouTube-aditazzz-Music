// The hook's clock: every world change is a shot's `land` from timeline.json (shots.yaml). Nothing hard-coded.
import { beats, kicks, tshot } from '../../timing';
import { clamp, easeIn2, prog, spring } from './anim';

const L = (id: string) => tshot(id).land;
// rc_hook2: the stop and the drop sit on the frame grid (the frame whose display interval holds the audio cut / the drop
// kick): s16 freeze = frame 1146 (38.21 -> 38.200), s17 snap = frame 1190 (39.68 / kick 39.675 -> 39.667).
const LF = (id: string) => Math.round(tshot(id).land * 30) / 30 - 1e-6; // (1e-6: frame/30 float equality)
export const H = {
  NEW: L('s02'), BLANK: L('s03'), GO: L('s04'), DARK: L('s05'), DOT: L('s06'), BREATH: L('s07'), PINK: L('s08'),
  BTN: L('s09'), TIP: L('s10'), COVER: L('s11'), PRESS: L('s12'), ZOOM: L('s13'), ROLL: L('s14'), MORE: L('s15'),
  STOP: LF('s16'), DROP: LF('s17'), END: L('s18'),
};
/** the n-th beat at or after t (n = 0: the beat at/after t). Lands in shots.yaml are rounded to 0.01 s, so a beat up to
 *  20 ms before t still counts as "at" t. */
export const beatAfter = (t: number, n = 0) => { const i = beats.findIndex((b) => b >= t - 0.02); return beats[Math.min(beats.length - 1, i + n)]; };
export const BEAT = beatAfter(H.GO, 1) - beatAfter(H.GO, 0);
/** last kick at or before t (drum MIDI), -Infinity if none */
export const lastKick = (t: number) => { let k = -Infinity; for (const x of kicks) { if (x <= t + 1e-6) k = x; else break; } return k; };
export const kicksIn = (a: number, b: number) => kicks.filter((x) => x >= a - 1e-6 && x <= b + 1e-6);
/** world-time: the picture freezes at the stop (s16) until the drop (s17); the UI keeps running */
export const worldT = (t: number) => (t >= H.STOP && t < H.DROP ? H.STOP : t);

// rc_hook2 intro timing (used by Hook.tsx's camera and ./overlay.ts's bar push)
export const INTRO = { PUSH0: 1.6, PUSH: 0.08, ZC: 0.58, ANT0: 11.62, ANT: 0.035 };
export const introBeats = () => ({ PUSH1: beatAfter(H.NEW, -3), CREEP0: beatAfter(H.NEW, 4), SEL: beatAfter(H.NEW, 8) });
const dockSpring = (t: number) => clamp(spring(t - H.NEW - 0.04, 1.35, 0.62)); // = the bar's dock move (./overlay.ts)
export const introPush = (t: number) => 1 + INTRO.PUSH * easeIn2(prog(t, INTRO.PUSH0, introBeats().PUSH1)) * (1 - dockSpring(t));
