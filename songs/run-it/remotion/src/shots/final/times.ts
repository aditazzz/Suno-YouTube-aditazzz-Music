// FINAL + OUTRO clock (rc_final): every world change is a shot's `land` from timeline.json (shots.yaml). Nothing hard-coded
// except the loop tail (the bloom after frame 6's moment at s78 t = 196.89) which is placed relative to the land.
import { beats, downbeats, kicks, lines, tshot } from '../../timing';

const L = (id: string) => tshot(id).land;
export const F = {
  REBOOT: L('s64'), SMALLER: L('s65'), QUIET: L('s66'), RIOT: L('s67'), DARK: L('s68'), HEART: L('s69'), SIMPLE: L('s70'),
  WHITE: L('s71'), RUNIT: L('s72'), BACK: L('s73'), UNDO1: L('s74'), UNDO2: L('s75'), UNDO3: L('s76'), PERFECT: L('s77'),
  CLICK: L('s78'), END: 198.0,
};
export const FRAME_DT = 1 / 30;
export const LAST_T = F.END - FRAME_DT; // 197.9667: the frame that must equal frame 0
// the loop tail: frame 6 holds to ~196.9; the light grows from BLOOM0, covers the frame by BLOOM1, settles into frame 0
export const BLOOM0 = F.CLICK + 0.56;   // 197.00
export const BLOOM1 = F.CLICK + 1.30;   // 197.74
/** the downbeats of bars 89 and 90: the white light's two pulses (s72) */
export const RUNIT_PULSES = downbeats.filter((d) => d >= F.RUNIT - 0.02 && d < F.BACK - 0.02);
export const beatAfter = (t: number, n = 0) => { const i = beats.findIndex((b) => b >= t - 0.02); return beats[Math.min(beats.length - 1, i + n)]; };
export const BEAT = beatAfter(F.HEART, 1) - beatAfter(F.HEART, 0);
export const kicksIn = (a: number, b: number) => kicks.filter((x) => x >= a - 1e-6 && x <= b + 1e-6);
/** the subscribe suggestion: one beat, ending when 'Perfect.' starts typing (it replaces the suggestion) */
const PERFECT_ON = lines.find((l) => l.shot === 's77')!.wt[0];
export const HINT = { a: Math.min(PERFECT_ON - BEAT, L('s76') + 1.9), b: PERFECT_ON };
