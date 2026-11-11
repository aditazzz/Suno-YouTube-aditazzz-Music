// What the in-scene UI (prompt bar, memory meter, REC clock) does at film time t. Pure function of time.
// Sections override the defaults by adding a provider here (first provider that returns non-null wins).
import { hookOverlay } from './shots/hook/overlay';
import { mid3dOverlay } from './shots/mid3d/overlay';
import { finalOverlay } from './shots/final/overlay';
import { tshot } from './timing';

export type OverlayState = {
  barTheme: number;    // 0 paper .. 1 dark
  barLift: number;     // px up from the dock
  barScale: number;
  barOpacity: number;
  meterTheme: number;
  meterDraw: number;   // 0..1 builds in
  meterTick: number;   // 0..1 pulse of the empty track
  recFrom: number | null; // REC clock start (film sec) or null = hidden
  recTheme: number;
  meterPct?: number;   // overrides the meter's value (s62 stutter climbs to 99%)
  barError?: boolean;  // red error bar, no cursor (the crash from 151.42)
  // rc_final (additive; unset = old behaviour):
  barText?: string;    // overrides the typed lyric ('' = empty bar, e.g. after the reboot)
  barHint?: string;    // grey autocomplete suggestion in an empty bar (s77 '› subscribe')
  barHintOpacity?: number;
  meterOpacity?: number;
  recOpacity?: number;
  recStop?: number;    // the REC clock freezes here (the click, s78)
  recLabel?: string;   // label after recStop ('SHIPPED')
  recDot?: string;     // REC dot colour (white from s71)
};
export const OVERLAY_DEFAULT: OverlayState = {
  barTheme: 1, barLift: 0, barScale: 1, barOpacity: 1, meterTheme: 1, meterDraw: 1, meterTick: 0, recFrom: tshot('s12').land, recTheme: 1, // REC starts on the press (s12) and runs to the end; later sections may hide it
};
const providers: ((t: number) => Partial<OverlayState> | null)[] = [hookOverlay, mid3dOverlay, finalOverlay];
export function overlayAt(t: number): OverlayState {
  for (const p of providers) { const o = p(t); if (o) return { ...OVERLAY_DEFAULT, ...o }; }
  return OVERLAY_DEFAULT;
}
