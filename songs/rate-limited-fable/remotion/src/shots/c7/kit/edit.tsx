// rl7_final (Nov 20): the FINAL's edit layer for cut 7, applied by Film.tsx over the whole picture (no 3D re-renders).
//  REMAP: output frame -> the frame actually drawn (holds / one-frame replacements; Remotion <Freeze>). Judge rows: JUDGE.md.
//  GRADE: per-range SVG curves (sRGB): blacks down (B18, B33), a lift (B51), the pre-dawn blue start of B59.
import React from 'react';
import { interpolate } from 'remotion';
import B49 from './edit_b49.json';

const hold = (from: number, to: number, src: number) => Object.fromEntries(Array.from({ length: to - from + 1 }, (_, i) => [from + i, src]));
export const REMAP: Record<number, number> = {
  ...hold(911, 912, 910),     // B10 -> B11: the two smeared whip frames -> hold f910, B11 starts clean
  ...hold(4219, 4219, 4218),  // B41: the one frame with CLICK CLICK and BAN 429 overlapping -> the dark CLICK frame before BAN lights
  ...hold(5527, 5527, 5526),  // B53: the one-frame CLICK CLICK flash -> repeat f5526
  // B49 f5119-5122 head pop: hold f5118 (blocker 3 fallback), added only if rl7_room's head turn did not land
  ...(B49.holdHead ? hold(5119, 5122, 5118) : {}),
};
// B61 (judge nit: the last shot ran 1.0 s and hard-stopped with the camera still speeding up): the film now ends at FINAL_END and the
// top-down on the lid (from the cut at 6521) holds 3 s, time easing to rest (source 6521 -> 6575 over 91 frames, speed 1.2x -> 0;
// fractional frames, every layer is a pure function of the frame). Source 6552-6597 is the clean top-down (no pill since rl7_master).
export const FINAL_END = 6612;
const EASE_AT = 6521, EASE_SRC = 54;
export const srcFrame = (f: number) => {
  if (f >= EASE_AT) { const t = Math.min(1, (f - EASE_AT) / (FINAL_END - 1 - EASE_AT)); return EASE_AT + EASE_SRC * (1 - (1 - t) * (1 - t)); }
  return REMAP[f] ?? f;
};

// y = lo + (hi - lo) * clip((x - b) / (w - b)) ^ g, as a 33-point table per channel
const curve = (b: number, w: number, g: number, lo = 0, hi = 1) =>
  Array.from({ length: 33 }, (_, i) => { const x = i / 32; const t = Math.min(1, Math.max(0, (x - b / 255) / ((w - b) / 255))); return (lo + (hi - lo) * Math.pow(t, g)).toFixed(4); }).join(' ');
type G = { from: number; to: number; id: string; table?: string; matrix?: (f: number) => string | null };
const ID = '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0';
const DAWN = [0.78, 0.04, 0.02, 0, 0, 0.02, 0.8, 0.06, 0, 0.0, 0.04, 0.08, 1.06, 0, 0.05, 0, 0, 0, 1, 0];
export const GRADES: G[] = [
  { from: 1764, to: 1850, id: 'g18', table: curve(86, 238, 0.62, 0.065) },   // B18: blacks 88-91 -> ~17-20, mids kept
  { from: 3344, to: 3413, id: 'g33', table: curve(66, 228, 0.7, 0.06) },     // B33: blacks 70 -> ~17
  { from: 5269, to: 5319, id: 'g51', table: curve(4, 200, 0.7) },            // B51: about one stop up, blacks held
  { from: 6185, to: 6206, id: 'g59', matrix: (f) => {                          // B59: opens on pre-dawn blue, eases to the plate's own colour
      const k = interpolate(f, [6185, 6192, 6206], [1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      if (k <= 0) return null; const I = ID.split(/\s+/).map(Number); return I.map((v, i) => (v + (DAWN[i] - v) * k).toFixed(4)).join(' ');
    } },
];
export const gradeAt = (f: number) => GRADES.find((g) => f >= g.from && f <= g.to);
/** the SVG filter defs + the CSS filter for frame f (null = no grade) */
export const GradeDefs: React.FC<{ f: number }> = ({ f }) => {
  const g = gradeAt(f); if (!g) return null;
  const m = g.matrix ? g.matrix(f) : null; if (g.matrix && !m) return null;
  return (
    <svg width={0} height={0} style={{ position: 'absolute' }}>
      <defs>
        <filter id={g.id} colorInterpolationFilters="sRGB" x="0" y="0" width="100%" height="100%">
          {g.table ? (
            <feComponentTransfer>
              <feFuncR type="table" tableValues={g.table} /><feFuncG type="table" tableValues={g.table} /><feFuncB type="table" tableValues={g.table} />
            </feComponentTransfer>
          ) : <feColorMatrix type="matrix" values={m!} />}
        </filter>
      </defs>
    </svg>
  );
};
export const gradeFilter = (f: number): string | undefined => {
  const g = gradeAt(f); if (!g) return undefined; if (g.matrix && !g.matrix(f)) return undefined; return `url(#${g.id})`;
};
