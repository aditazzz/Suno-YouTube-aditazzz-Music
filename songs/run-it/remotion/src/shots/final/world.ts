// FINAL + OUTRO state as pure functions of film time (rc_final). Positions in screen px of the current layout.
import type { Layout } from '../../theme';
import { kicks } from '../../timing';
import { clamp, easeIn2, easeInOut3, easeOut3, lerp, mixHex, prog, spring } from '../hook/anim';
import { BEAT, BLOOM0, BLOOM1, F, RUNIT_PULSES } from './times';

const PANEL_W = 760;
// ---------- layout (16:9 = approved frames 5 and 6; 9:16 = placeholder inside the safe zone) ----------
export type FL = { DL: { x: number; y: number }; DC: { x: number; y: number }; panel: { x: number; y: number; w: number; h: number; s: number };
  maxX: number; minY: number; maxY: number; corner: number;
  // rc_916 (9:16 only; unset = 16:9's values): rows, the vertical (bottom sheet) slide, the card, a shard keep-out box
  row0?: number; pitch?: number; head?: number; rowX?: number; hl?: { x: number; w: number; h: number }; slideY?: boolean;
  card?: { s: number; w: number; h: number; cols: number; rows: number }; keepOut?: { x0: number; y1: number } };
export function layoutOf(L: Layout): FL {
  if (L.fmt === '16x9') return { DL: { x: 600, y: 470 }, DC: { x: 960, y: 470 }, panel: { x: 1100, y: 186, w: PANEL_W, h: 678, s: 1 },
    maxX: 1080, minY: 40, maxY: 880, corner: Math.hypot(960, 610) };
  // 9:16 (LAYOUT_916.md): the history docks above the composer (one column, x 110-860, a chat log over its composer), rows
  // at 34 px (s = 1), it opens upward; the dot glides up/down (DL above the panel, DC = the hook's dot at (540, 640), so the
  // loop's bloom starts where frame 0's does); the crash card shrinks to 0.16 at DL (173 x 307, 20 px above the panel)
  return { DL: { x: 540, y: 360 }, DC: { x: 540, y: 640 }, panel: { x: 110, y: 534, w: 750, h: 576, s: 1 },
    maxX: 1040, minY: 40, maxY: 1110, corner: Math.hypot(540, 1280),
    row0: 96, pitch: 50, head: 20, rowX: 116, hl: { x: 18, w: 710, h: 48 }, slideY: true,
    card: { s: 0.16, w: 1080, h: 1920, cols: 7, rows: 12 }, keepOut: { x0: 610, y1: 470 } };
}
export const ROW0 = 110, PITCH = 56; // history rows: first row centre (from the panel top), row pitch
// s65 egg: every history row carries a thumbnail, a real frame of the film after that prompt (public/history/h<i>.jpg, pulled
// from the rough cut). The panel grew 700 -> 760 (and moved 40 px left) so the longest row still clears the highlight.
export const THUMB = { x: 30, w: 64, h: 36 }, TX = THUMB.x + THUMB.w + 22; // row text starts at TX (was 48)
export const THUMB_T = [7.5, 19.0, 24.8, 74.6, 78.5, 129.4, 131.5, 138.6, 148.6, 154.0]; // film time of each thumbnail (for the record)

// ---------- history panel ----------
export const ITEMS = ['New session', 'Make the screen go dark', 'Make it pink, a little pinker', 'Turn the dot into a city',
  'Purple Porsche, yellow brakes', 'Add a moon', 'Make them fall in love', 'Delete Mondays', 'Make it Sunday, make it night', 'Out of memory.'];
export const OOM = ITEMS.length - 1;
/** 0 closed (off to the right) .. 1 open. Springs open on the reboot and on "Take me back"; eases off on "simple" and "Perfect." */
export function panelOpen(t: number) {
  if (t < F.REBOOT) return 0;
  if (t < F.SIMPLE) return spring(t - F.REBOOT - 0.1, 1.5, 0.78);
  if (t < F.BACK) return 1 - easeIn2(prog(t, F.SIMPLE, F.SIMPLE + 0.5));
  if (t < F.PERFECT) return spring(t - F.BACK, 1.5, 0.78);
  return 1 - easeIn2(prog(t, F.PERFECT, F.PERFECT + 0.55));
}
/** highlighted row (fractional while it springs): the last good state, then a block up on each Undo */
export function highlight(t: number) {
  const steps: [number, number][] = [[F.UNDO1, 6], [F.UNDO2, 2], [F.UNDO3, 0]];
  let h = 8;
  for (const [at, to] of steps) if (t >= at) h = h + (to - h) * clamp(spring(t - at, 2.2, 0.72), 0, 1.15);
  return h;
}
/** 0..1 strike-through progress for row i (undone rows strike as the highlight passes them, bottom-up) */
export function strikeOf(i: number, t: number) {
  if (i === OOM) return 1;
  const steps: [number, number][] = [[F.UNDO1, 6], [F.UNDO2, 2], [F.UNDO3, 0]];
  let from = 8;
  for (const [at, to] of steps) { if (i > to && i <= from) return easeOut3(prog(t, at + (from - i) * 0.05, at + (from - i) * 0.05 + 0.28)); from = to; }
  return 0;
}

// ---------- the dot ----------
export function dotPos(t: number, fl: FL) {
  const { DL, DC } = fl;
  const mv = (a: typeof DL, b: typeof DL, t0: number) => { const k = spring(t - t0, 1.1, 0.8); return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k) }; };
  if (t < F.SIMPLE) return DL;
  if (t < F.BACK) return mv(DL, DC, F.SIMPLE + 0.05);
  if (t < F.PERFECT) return mv(DC, DL, F.BACK);
  return mv(DL, DC, F.PERFECT + 0.05);
}
/** base radius before breath (frame 5: 64; s69 halves it; "Take me back" grows it to frame 6's 60) */
export function dotR(t: number) {
  if (t < F.RIOT) return 0;
  if (t < F.HEART) return 64 * spring(t - F.RIOT, 2.4, 0.5);
  if (t < F.BACK) return lerp(64, 32, spring(t - F.HEART, 2.6, 0.55));
  return lerp(32, 60, spring(t - F.BACK, 1.8, 0.6));
}
/** pink -> light pink -> white over 8 frames on "light" (s71), never through grey */
export function dotCol(t: number) {
  const k = prog(t, F.WHITE, F.WHITE + 8 / 30);
  return k < 0.5 ? mixHex('#ff6fae', '#ffc4dd', k * 2) : mixHex('#ffc4dd', '#ffffff', (k - 0.5) * 2);
}
export const whiteK = (t: number) => prog(t, F.WHITE, F.WHITE + 8 / 30);
const lastIn = (a: number[], t: number) => { let r = -Infinity; for (const x of a) { if (x <= t + 1e-6) r = x; else break; } return r; };
/** the dot's pulse 0..~1: breath on the real kicks (s68), heartbeat lub-dub (s69-s71), two pulses (s72), soft breath (OUTRO) */
export function dotPulse(t: number) {
  if (t < F.DARK - 0.02) return 0;
  if (t < F.HEART) { const d = t - lastIn(kicks, t); return d < BEAT ? Math.pow(1 - d / BEAT, 2) : 0; }
  if (t < F.RUNIT) {
    // lub on beat 1, dub on the and of 1, every bar (heartbeat from the land of s69)
    const b0 = F.HEART, bar = 4 * BEAT, ph = ((t - b0) % bar + bar) % bar;
    const lub = Math.exp(-ph / 0.11), dub = ph >= BEAT / 2 ? 0.7 * Math.exp(-(ph - BEAT / 2) / 0.11) : 0;
    return Math.max(lub, dub);
  }
  if (t < F.BACK) { const p = lastIn(RUNIT_PULSES, t); return p > -Infinity ? 1.3 * Math.exp(-(t - p) / 0.28) : 0; }
  // OUTRO: the fading pulse (audio E4: the kick fades -10 -> -30 dB by s77): breath scaled down with it
  const d = t - lastIn(kicks, t); const fade = t >= F.UNDO3 + 0.6 ? 2.0 : 1 - 0.85 * prog(t, F.BACK, F.PERFECT);
  return d < BEAT ? 0.45 * fade * Math.pow(1 - d / BEAT, 2) : 0;
}

// ---------- the loop tail: the click and the bloom ----------
/** radius of the light that fills the frame after the click (0 before BLOOM0) */
export function bloomR(t: number, fl: FL) {
  if (t < BLOOM0) return 0;
  const e = easeInOut3(prog(t, BLOOM0, BLOOM1));
  return 60 * Math.pow((fl.corner + 660) / 60, e); // the mask (Final.tsx) runs 230 + 170 px behind this: fully open past the corners by k = 1
}
export const bloomK = (t: number) => prog(t, BLOOM0, BLOOM1);
export { clamp, lerp };
