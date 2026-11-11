// The in-scene UI for s46-s63 (rc_3dstand): the meter climbs to 99% in the stutter (149.95 on), the bar goes red with
// no cursor from the crash's first frame (151.42; sections.json only starts BREAK at 153.62). Pure function of time.
import type { OverlayState } from '../../overlay';
import { memoryAt } from '../../timing';
import { M, STUTTER } from './times';

export function mid3dOverlay(t: number): Partial<OverlayState> | null {
  if (t < M.S46 || t >= M.REBOOT) return null;
  const o: Partial<OverlayState> = {};
  if (t >= STUTTER[1].t && t < M.CRASH) {
    const k = (a: number) => Math.min(1, (t - a) / 0.32);
    const base = memoryAt(t);
    o.meterPct = t >= STUTTER[2].t ? 98 + k(STUTTER[2].t) : Math.max(base, base + (98 - base) * k(STUTTER[1].t));
  }
  if (t >= M.CRASH) o.barError = true;
  if (t >= M.CRASH && t < M.OOM) o.barText = ''; // the bar is empty in the silence (the s62 line would otherwise hang 3 frames into the crash)
  return o;
}
