// The hook's in-scene UI: bar centred on the white page, springs to its dock on "New session.", meter builds in,
// both flip to the dark theme as the iris (s05) passes them. Pure function of time.
import type { OverlayState } from '../../overlay';
import { beats, lines } from '../../timing';
import { clamp, easeOut3, spring } from './anim';
import { H, introPush } from './times';

export const IRIS_FRAMES = 6;
export const IRIS_MAX = 1420; // px: past the farthest corner from the bar
/** iris radius (screen px at z = 1) at t: 0 before the dark land, IRIS_MAX after 6 frames, accelerating */
export const irisR = (t: number) => { const k = clamp((t - H.DARK) / (IRIS_FRAMES / 30)); return k <= 0 ? 0 : IRIS_MAX * (0.04 + 0.96 * k * k); };
export const IRIS_ORIGIN = { x: 960, y: 980 }; // the prompt bar's centre (16:9 screen)
export const BAR_CENTRE_LIFT = 440;           // bar centred on the page (top 490) vs its dock (930)

// rc_hook2 fix 1: s02's line stays in the bar until the next line starts typing (an s02-only exception to land + 1.2 s),
// so the frame is never an empty bar on an empty page
const S02_LINE = lines.findIndex((l) => l.shot === 's02');
const S02_HOLD = S02_LINE >= 0 && lines[S02_LINE + 1] ? { from: H.NEW + 0.6, till: lines[S02_LINE + 1].wt[0], text: lines[S02_LINE].text } : null;

export function hookOverlay(t: number): Partial<OverlayState> | null {
  if (t >= H.DARK + 0.5) return null;
  const down = spring(t - H.NEW - 0.04, 1.35, 0.62);
  const r = irisR(t);
  const meterDist = Math.hypot(1690 - IRIS_ORIGIN.x, 85 - IRIS_ORIGIN.y);
  let tick = 0;
  if (t >= H.NEW && t < H.GO) { const b = beats.filter((x) => x <= t).pop() ?? 0; tick = Math.exp(-(t - b) / 0.12); }
  return {
    barTheme: clamp((r - 60) / 520), // flips as the dark disc spreads under the bar (half-width 590)
    barLift: BAR_CENTRE_LIFT * (1 - down),
    barScale: introPush(t), // s01: the slow push on the bar (with the camera), undone by the dock spring
    ...(S02_HOLD && t >= S02_HOLD.from && t < S02_HOLD.till ? { barText: S02_HOLD.text } : {}),
    barOpacity: easeOut3(t / 0.9),
    meterTheme: clamp((r - meterDist) / 90 + 0.5),
    meterDraw: clamp(spring(t - H.NEW - 0.12, 1.1, 0.8)),
    meterTick: tick,
  };
}
