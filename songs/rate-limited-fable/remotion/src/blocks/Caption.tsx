// The caption line: OFF by default (her Nov 4 call), its own layer so it can go back in without touching any shot.
// Turn on with inputProps {captions: true}. Plain white words, soft dark shadow, word-by-word fade, no particles.
// Lines come from build/words.json (a new line after a 0.7 s gap or 7 words). 16:9: bottom band of the stage.
// 9:16: a band inside the safe zone (out of the top 13%, bottom 30%, 9% each side). Check every line's spot on a
// contact sheet before finals; for 9:16 finals the studio's caplayer.py picks per-line bands from the caption-free master.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { FONT, FPS, Fmt, SIZE } from '../theme';
import { WORDS } from '../timing';
import { clamp } from '../ease';

type CLine = { s: number; e: number; words: [number, string][] };
const LINES: CLine[] = (() => {
  const out: CLine[] = []; let cur: [number, string][] = [];
  WORDS.forEach((w, i) => {
    const prev = WORDS[i - 1];
    if (cur.length && (cur.length >= 7 || (prev && w[0] - prev[0] > 0.7))) { out.push({ s: cur[0][0], e: w[0], words: cur }); cur = []; }
    cur.push(w);
  });
  if (cur.length) out.push({ s: cur[0][0], e: cur[cur.length - 1][0] + 1.2, words: cur });
  return out.map((l) => ({ ...l, e: Math.min(l.e, l.words[l.words.length - 1][0] + 1.6) }));
})();

export const CaptionLayer: React.FC<{ on?: boolean; fmt: Fmt }> = ({ on = false, fmt }) => {
  const t = useCurrentFrame() / FPS;
  if (!on) return null;
  const l = LINES.find((x) => t >= x.s - 0.1 && t < x.e); if (!l) return null;
  const out = clamp((l.e - t) / 0.25);
  const band: React.CSSProperties = fmt === '16x9'
    ? { left: 320, right: 320, top: 1230, height: 130 }
    : { left: 98, right: 98, top: 1110, height: 220 };
  return (
    <div data-fit="off" style={{ position: 'absolute', ...band, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center',
      fontFamily: FONT.ui, fontWeight: 600, fontSize: fmt === '16x9' ? SIZE.lyric : 58, lineHeight: 1.15, color: '#fff', opacity: out,
      textShadow: '0 2px 18px rgba(0,0,0,0.75), 0 0 4px rgba(0,0,0,0.6)' }}>
      <div>{l.words.map(([wt, w], i) => <span key={i} style={{ opacity: clamp((t - wt + 0.05) / 0.12) }}>{w}{' '}</span>)}</div>
    </div>
  );
};
