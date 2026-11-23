// rl5_c: his visor (CUT5_PLAN §2b) and the date model's visor lines (7E1).
//
// <VisorSwap>: swaps B's visor passes (same plate, same camera: EYES, sorry EYES, 4, 42, 429, 200, 418 ...) on cue frames.
//   A change between looks (eyes <-> digits, eyes <-> sorry) = a 3-frame blink shut (the visor goes dark over its region, the old
//   pass under it), then 3 frames opening on the new pass. Digits lighting on a sung "four-two-nine" ('4' -> '42' -> '429') never
//   blink: each new digit flickers on over 2 frames (on, dip, on).
//   passes: state -> public/ path (full-stage plates, or RGBA layers drawn at `layer`); track: [localFrame, state][] ascending.
//   region: the visor glass in stage px [x, y, w, h] (for the shut); shutColor: the visor's dark glass.
//   Example (2B, K plate): <VisorSwap f={f} passes={{eyes:'c5/K/eyes.jpg', '4':'c5/K/v4.jpg', '42':'c5/K/v42.jpg', '429':'c5/K/v429.jpg',
//     sorry:'c5/K/sorry.jpg'}} track={[[0,'eyes'], [20,'4'], [28,'42'], [36,'429'], [58,'sorry']]} region={[1180, 420, 420, 170]} />
//   The first digit after eyes blinks shut first (eyes close, the 4 opens), then 2 and 9 light without a blink.
//
// <VisorLines>: 7E1, the other model's visor agreeing with everything: one line per beat (script.VISOR_DATE), pinned to A2's visor
//   quad (stage px, TL TR BR BL) as LED type; each change = 2 dark frames then the new line (the same blink grammar, shorter).
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { VISOR_DATE } from '../../blocks/real/script';
import { clamp } from './kit';

export type Track = [number, string][];
const isDigits = (s: string) => /^\d+$/.test(s);
/** one digit added to the previous digits ('4' -> '42'): a light-up, not a look change */
const isLightUp = (a: string, b: string) => isDigits(a) && isDigits(b) && b.startsWith(a) && b.length === a.length + 1;

/** what to draw at frame f: the pass, the shut amount 0..1 over the region, and a flicker dip 0..1 */
export const visorAt = (f: number, track: Track) => {
  let i = 0; while (i + 1 < track.length && f >= track[i + 1][0]) i++;
  const [t, cur] = track[i]; const prev = i > 0 ? track[i - 1][1] : cur; const d = f - t;
  if (i === 0 || d >= 6) return { pass: cur, shut: 0, dip: 0 };
  if (isLightUp(prev, cur)) return { pass: d === 1 ? prev : cur, shut: 0, dip: d === 0 ? 0.0 : d === 1 ? 0 : 0 };   // on (f0), back off (f1), on (f2+)
  // blink: shut on the old (d 0..2), open on the new (d 3..5)
  if (d <= 2) return { pass: prev, shut: [0.55, 1, 1][d], dip: 0 };
  return { pass: cur, shut: [0.7, 0.35, 0.1][d - 3], dip: 0 };
};

export const VisorSwap: React.FC<{
  f: number; passes: Record<string, string>; track: Track; region: [number, number, number, number]; layer?: { x: number; y: number; w: number; h: number };
  shutColor?: string; feather?: number;
}> = ({ f, passes, track, region, layer, shutColor = '#06070a', feather = 0.22 }) => {
  const v = visorAt(f, track);
  const src = passes[v.pass]; const [rx, ry, rw, rh] = region;
  const mask = `radial-gradient(ellipse 50% 50% at 50% 50%, #000 ${Math.round((1 - feather) * 100)}%, transparent 100%)`;
  return (
    <AbsoluteFill>
      {src ? <Img src={staticFile(src)} style={layer ? { position: 'absolute', left: layer.x, top: layer.y, width: layer.w, height: layer.h } : { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} /> : null}
      {v.shut > 0 ? <div style={{ position: 'absolute', left: rx, top: ry, width: rw, height: rh, background: shutColor, opacity: clamp(v.shut), WebkitMaskImage: mask, maskImage: mask }} /> : null}
    </AbsoluteFill>
  );
};

/** the date model's visor: LED words, one per beat. beats = local frames of the five changes (the first is on at the cut) */
export const VisorLines: React.FC<{ f: number; beats: number[]; quad: Quad; w?: number; h?: number; color?: string; lines?: string[]; fill?: number; wfrac?: number }> = ({
  f, beats, quad, w = 900, h = 260, color = '#BFF4FF', lines = VISOR_DATE, fill = 0.62, wfrac = 0.9 }) => {
  let i = 0; while (i + 1 < beats.length && f >= beats[i + 1]) i++;
  const d = f - beats[i]; const dark = i > 0 && d >= 0 && d < 2;     // 2 dark frames, then the new line
  const line = lines[Math.min(i, lines.length - 1)];
  const fs = Math.min(h * fill, (w * wfrac) / Math.max(4, line.length * 0.62));   // fill/wfrac: rl5_d3 (7E1 >= 34 px)
  return (
    <ScreenInsert corners={quad} w={w} h={h}>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: dark ? 0 : i > 0 && d === 2 ? 0.6 : 1 }}>
        <div data-fit="box" style={{ fontFamily: '"SF Mono", Menlo, ui-monospace, monospace', fontWeight: 800, fontSize: fs, letterSpacing: fs * 0.04, color, whiteSpace: 'nowrap',
          textShadow: `0 0 ${fs * 0.18}px ${color}, 0 0 ${fs * 0.5}px rgba(120,220,255,0.55)` }}>{line}</div>
      </div>
    </ScreenInsert>
  );
};
