// rl7_fixb (her H7.8/H7.18 "same square computer font for the visor"): 7E1's date-visor words in rl7_ra's LED dot-matrix face (c7/kit/seg.tsx VisorText)
// instead of the monospace type: one line per beat, the same blink grammar as c5/Visor.tsx VisorLines (2 dark frames, then the new line), ONE dot pitch for
// the whole shot (the longest line fits), so the dots never change size between words.
import React from 'react';
import { VisorText } from '../kit/seg';
import { VISOR_DATE } from '../../../blocks/real/script';
import type { Quad } from '../../../blocks/ScreenInsert';

export const Visor7Led: React.FC<{ f: number; beats: number[]; quad: Quad; lines?: string[]; color?: string }> = ({ f, beats, quad, lines = VISOR_DATE, color = '#BFF4FF' }) => {
  let i = 0; while (i + 1 < beats.length && f >= beats[i + 1]) i++;
  const d = f - beats[i]; const dark = i > 0 && d >= 0 && d < 2;
  const line = lines[Math.min(i, lines.length - 1)];
  const w = 780, h = 300;                                   // canvas with the quad's own aspect (104 x 40 stage px)
  const cols = Math.max(...lines.map((l) => l.length * 6 - 1));
  const pitch = Math.min((w * 0.9) / cols, (h * 0.8) / 7);
  if (dark) return null;
  return <div style={{ opacity: i > 0 && d === 2 ? 0.6 : 1 }}><VisorText lines={[line]} quad={quad} w={w} h={h} pitch={pitch} color={color} bulge={0} /></div>;
};
