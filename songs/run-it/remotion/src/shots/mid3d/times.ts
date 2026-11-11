// The 3D middle's clock (s46-s63). Every world change is a shot's `land` from timeline.json (shots.yaml), every beat
// from the drum-MIDI grid. Nothing hard-coded except where the plan names a beat ("beat 3 of bar 65" = beatAfter(...)).
import { beats, lines, tshot } from '../../timing';

const L = (id: string) => tshot(id).land;
/** the n-th beat at or after t (lands are rounded to 0.01 s, so a beat 20 ms before still counts) */
export const beatAfter = (t: number, n = 0) => { const i = beats.findIndex((b) => b >= t - 0.02); return beats[Math.min(beats.length - 1, i + n)]; };
/** sung onset of word `w` (0-based) in the line with this exact text */
const onset = (text: string, w = 0) => { const l = lines.find((x) => x.text === text); return l ? l.wt[w] : NaN; };

export const M = {
  // POST2b
  S46: L('s46'), S47: L('s47'), S48: L('s48'),
  // BRIDGE
  MOON1: beatAfter(L('s48'), 2),           // bar 65 beat 3 (126.98): moon 1 rises on "moon"
  S49: L('s49'), S50: L('s50'), S51: L('s51'), S52: L('s52'), S53: L('s53'),
  BACK: beatAfter(L('s53'), 4),            // bar 69 beat 3 (134.80): "Bring it back" snaps the ocean back mirror-flat
  S54: L('s54'), S55: L('s55'), S56: L('s56'), S57: L('s57'), S58: L('s58'), S59: L('s59'), S60: L('s60'),
  S61: L('s61'), S62: L('s62'),
  CRASH: L('s63'), REBOOT: L('s64'),
  // sung moments inside shots
  SIXTY: onset("Sixty frames, don't make me wait"),   // 135.28: the fps readout appears at "24 fps", motion stepped
  DELETE: onset('Delete Mondays'),                     // 137.28: the calendar springs in
  SUNDAY: onset('Make it Sunday, make it night', 3),   // 146.40 "Sunday": gold floods in
  NIGHT: beatAfter(L('s60'), 2),                       // bar 75 beat 3 (146.53): the moons slide across the sun
  DRUMS_OUT: beatAfter(L('s62'), 1),                   // 149.95: the song drops its drums, the render chokes
  OOM: onset('Out of memory.'),                        // 154.40
};

/** The stutter: fps steps 60 -> 24 -> 8 -> 2 on the beats after the drums drop. */
export const STUTTER = [
  { t: M.DRUMS_OUT, fps: 24 },
  { t: beatAfter(M.DRUMS_OUT, 1), fps: 8 },
  { t: beatAfter(M.DRUMS_OUT, 2), fps: 2 },
];
/** Crash debug labels, on the silent grid (bar 78 beat 3, bar 79 beat 1, bar 79 beat 3) + the pigeon on bar 78 beat 4. */
export const CRASH_BEATS = { b3: beatAfter(M.CRASH, 2), b4: beatAfter(M.CRASH, 3), b5: beatAfter(M.CRASH, 4), b7: beatAfter(M.CRASH, 6) };

/** World time: what the 3D world sees. Stepped before "Sixty frames" lands (the readout says 24 fps), stepped harder
 *  in the stutter, frozen in the crash. The UI layer always runs on true time. */
export function worldT(t: number) {
  const q = (t0: number, f: number) => t0 + Math.floor((t - t0) * f + 1e-6) / f;
  if (t >= M.CRASH) return M.CRASH - 1 / 30;
  for (let i = STUTTER.length - 1; i >= 0; i--) if (t >= STUTTER[i].t) return q(STUTTER[i].t, STUTTER[i].fps);
  if (t >= M.SIXTY && t < M.S55) return q(M.SIXTY, 12); // reads as "24 fps" (true 24 on a 30 fps cut is near invisible)
  return t;
}
/** what the fps readout says at t (null = hidden) */
export function fpsReadout(t: number): number | null {
  if (t < M.SIXTY || t >= M.CRASH) return null;
  for (let i = STUTTER.length - 1; i >= 0; i--) if (t >= STUTTER[i].t) return STUTTER[i].fps;
  return t >= M.S55 ? 60 : 24;
}
