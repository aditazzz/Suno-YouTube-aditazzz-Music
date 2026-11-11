// The in-scene UI for FINAL + OUTRO (rc_final), s64-s78 (155.34-198.00). Pure function of time.
// - the reboot (155.34): the bar is no longer red; "Out of memory." flies from the bar to the history panel, the bar is empty
//   until "Make it smaller" types (156.88).
// - REC keeps recording (it started on the press, s12); its dot turns white with the light (s71); the click stops it and it
//   reads SHIPPED (s78 egg).
// - s77: the grey '› subscribe' suggestion for one beat in the empty bar, replaced by "Perfect." as she types.
// - the loop tail: the light from the clicked dot passes the bar, the REC clock and the meter and they go with it, the bar
//   rising into the light to its frame-0 spot (centred, paper), so the last frame's UI = hookOverlay(0): bar opacity 0, no
//   meter, no REC.
import type { OverlayState } from '../../overlay';
import { hookOverlay } from '../hook/overlay';
import { clamp, easeInOut3, prog, smooth } from '../hook/anim';
import { lines } from '../../timing';
import { BLOOM0, BLOOM1, F, HINT } from './times';
import { whiteK } from './world';

const MAKE_SMALLER_ON = lines.find((l) => l.shot === 's65')!.wt[0];

export function finalOverlay(t: number): Partial<OverlayState> | null {
  if (t < F.REBOOT) return null;
  const o: Partial<OverlayState> = { barError: false };
  if (t < MAKE_SMALLER_ON) o.barText = '';
  if (t >= HINT.a - 0.2 && t < HINT.b) { o.barHint = 'subscribe'; o.barHintOpacity = smooth(prog(t, HINT.a, HINT.a + 0.1)); }
  if (t >= F.WHITE) o.recDot = whiteK(t) >= 0.5 ? '#ffffff' : '#ffc4dd';
  if (t >= F.CLICK) { o.recStop = F.CLICK; o.recLabel = 'SHIPPED'; }
  if (t >= BLOOM0) {
    // the light's front reaches the bar (~0.35 of the way), the REC clock and the meter (~0.6)
    const k = prog(t, BLOOM0, BLOOM1);
    const h0 = hookOverlay(0)!; // the loop target: frame 0's UI
    const up = easeInOut3(prog(k, 0.25, 0.95));
    // the bar rises into the light and goes before it can read as a grey slab (frame 0 has it at opacity 0 anyway)
    o.barLift = (h0.barLift ?? 440) * up;
    o.barOpacity = 1 - smooth(prog(k, 0.12, 0.45));
    o.meterOpacity = 1 - smooth(prog(k, 0.45, 0.75));
    o.recOpacity = 1 - smooth(prog(k, 0.42, 0.72));
    if (k >= 1) { o.barOpacity = h0.barOpacity; o.meterDraw = h0.meterDraw; o.meterTheme = h0.meterTheme; o.barTheme = h0.barTheme; o.recFrom = null; }
  }
  return o;
}
void clamp;
