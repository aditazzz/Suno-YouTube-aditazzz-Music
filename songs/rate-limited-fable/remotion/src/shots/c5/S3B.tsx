// 3B (cut 5; plan §3: f1260-1330; N09, N10): flat-on over his counter, his finished crossword, central, in pen. Every clue is the
// same ("What she needs"); the four words highlight on the four beats (1260 SLEEP / 1277 WATER / 1295 REST / 1312 FRIENDS), the
// grid word and its clue line together. The grid is built and validated in code (crossword.ts; workers/rl5_c/tools/check_crossword.mjs).
//   <CrosswordSheet f={f} at={[...]} />   the newspaper puzzle at its own size (XW.w x XW.h px): pin it with
//   <ScreenInsert corners={paperQuad} w={XW.w} h={XW.h} light={..}> on B's desk plate (B delivers the plate + paper quad).
// Until B's desk plate lands, the shot stands it on cut 4e's T7c desk plate (soft) as a placeholder.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { CROSSWORD } from '../../blocks/real/script';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { buildGrid, validateGrid } from './crossword';
import { clamp, ez, loc, lerp, sweep } from './kit';
import { Grain2, Vig } from '../../blocks/real/Scene';

validateGrid();                                             // throws at bundle time if a crossing is wrong
const G = buildGrid();
export const XW = { w: 1800, h: 1100 };
export const C3B = { HL: [1260, 1277, 1295, 1312] };       // absolute: SLEEP, WATER, REST, FRIENDS
const CELL = 128, GX = 70, GY = 150;                         // grid: 7 x 128 = 896 px
const INK = 'rgba(24,38,110,0.92)';                          // blue ballpoint
const PRINT = '#1b1a18', PAPER = '#efebe1';
const HAND = '"Noteworthy", "Marker Felt", "Chalkboard SE", cursive';
const SERIF = '"Times New Roman", Georgia, serif';
const HL = 'rgba(255,214,0,0.62)';
const JIT = [-3, 2, -1, 3, -2, 1, -2, 2, 0, -3];             // the pen's small tilt per letter

export const CrosswordSheet: React.FC<{ f: number; at: number[] }> = ({ f, at }) => {
  const order = CROSSWORD.highlight;
  const hlK = (w: string) => { const i = order.indexOf(w); return i < 0 ? 0 : sweep(f, at[i], 7); };
  const across = G.words.filter((w) => w.dir === 'across').sort((a, b) => a.num - b.num);
  const down = G.words.filter((w) => w.dir === 'down').sort((a, b) => a.num - b.num);
  const ClueLine: React.FC<{ w: (typeof G.words)[number] }> = ({ w }) => {
    const k = hlK(w.w);
    return (
      <div style={{ position: 'relative', height: 66, display: 'flex', alignItems: 'center', fontFamily: SERIF, fontSize: 50, color: PRINT, whiteSpace: 'nowrap' }}>
        <div data-fit="off" style={{ position: 'absolute', left: -10, top: 6, height: 54, width: `${k * 100}%`, background: HL, borderRadius: 6, transform: 'skewX(-6deg)' }} />
        <span style={{ position: 'relative', padding: '0 4px' }}><b>{w.num}</b>&nbsp; {(CROSSWORD as any).clues?.[w.w] ?? CROSSWORD.clue} ({w.w.length})</span>
      </div>
    );
  };
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: XW.w, height: XW.h, background: PAPER, overflow: 'hidden',
      boxShadow: 'inset 0 0 120px rgba(120,100,60,0.18)' }}>
      {/* the newsprint: a faint fibre tone */}
      <div style={{ position: 'absolute', inset: 0, background: 'repeating-linear-gradient(90deg, rgba(0,0,0,0.012) 0 2px, rgba(0,0,0,0) 2px 7px)' }} />
      <div data-fit="box" style={{ position: 'absolute', left: GX, top: 44, padding: '0 6px', fontFamily: SERIF, fontWeight: 700, fontSize: 58, letterSpacing: 6, color: PRINT }}>{(CROSSWORD as any).title ?? 'THE DAILY MINI'}</div>
      <div data-fit="box" style={{ position: 'absolute', right: GX, top: 62, padding: '0 6px', fontFamily: SERIF, fontStyle: 'italic', fontSize: 40, color: PRINT }}>{(CROSSWORD as any).subtitle ?? ''}</div>
      <div style={{ position: 'absolute', left: GX, top: 128, width: XW.w - 2 * GX, height: 3, background: PRINT }} />
      {/* the grid */}
      <div style={{ position: 'absolute', left: GX, top: GY, width: CELL * G.n, height: CELL * G.n, border: `5px solid ${PRINT}`, boxSizing: 'content-box' }}>
        {Array.from({ length: G.n * G.n }, (_, i) => {
          const r = Math.floor(i / G.n) + 1, c = (i % G.n) + 1; const ch = G.g[r][c];
          return <div key={i} style={{ position: 'absolute', left: (c - 1) * CELL, top: (r - 1) * CELL, width: CELL, height: CELL, boxSizing: 'border-box',
            border: `2px solid ${PRINT}`, background: ch ? 'transparent' : PRINT }} />;
        })}
        {/* highlighter strokes under the ink, one per word, sweeping along the word on its beat */}
        {G.words.map((w) => {
          const k = hlK(w.w); if (k <= 0) return null;
          const [r, c] = w.cells[0]; const n = w.cells.length;
          const across = w.dir === 'across';
          return <div key={w.w} data-fit="off" style={{ position: 'absolute', left: (c - 1) * CELL + 10, top: (r - 1) * CELL + 10, width: across ? (n * CELL - 20) * k : CELL - 20,
            height: across ? CELL - 20 : (n * CELL - 20) * k, background: HL, borderRadius: 14 }} />;
        })}
        {G.cells.map((cell, i) => (
          <React.Fragment key={i}>
            {cell.num ? <div data-fit="off" style={{ position: 'absolute', left: (cell.c - 1) * CELL + 9, top: (cell.r - 1) * CELL + 5, fontFamily: SERIF, fontSize: 30, color: PRINT }}>{cell.num}</div> : null}
            <div data-fit="off" style={{ position: 'absolute', left: (cell.c - 1) * CELL, top: (cell.r - 1) * CELL + 8, width: CELL, height: CELL, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: HAND, fontWeight: 700, fontSize: 86, color: INK, transform: `rotate(${JIT[i % JIT.length]}deg)` }}>{cell.ch}</div>
          </React.Fragment>
        ))}
      </div>
      {/* the clues: the running joke on three, then what she has lost (rl7_ra, her H7.14) */}
      <div style={{ position: 'absolute', left: GX + CELL * G.n + 90, top: GY - 6, width: XW.w - (GX + CELL * G.n + 90) - 40 }}>
        <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 52, letterSpacing: 3, color: PRINT, marginBottom: 10, padding: '0 4px' }}>ACROSS</div>
        {across.map((w) => <ClueLine key={w.w} w={w} />)}
        <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 52, letterSpacing: 3, color: PRINT, margin: '44px 0 10px', padding: '0 4px' }}>DOWN</div>
        {down.map((w) => <ClueLine key={w.w} w={w} />)}
      </div>
    </div>
  );
};

// placeholder staging: the sheet flat on the counter (cut 4e's T7c desk plate, soft) until B's desk plate + paper quad land
export const PAPER_QUAD_PLACEHOLDER: Quad = [[300, 150], [2262, 162], [2250, 1352], [292, 1340]];
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const at = C3B.HL.map((F) => loc(shot, F));
  // settles from 3A's door-edge travel (D lands the travel; here: the last of it, eased), then still while read
  const s = lerp(1.04, 1.0, ez(f, 0, 14)); const x = lerp(-40, 0, ez(f, 0, 14));
  return (
    <AbsoluteFill style={{ background: '#1c140e' }}>
      <AbsoluteFill style={{ transform: `translateX(${x}px) scale(${s})` }}>
        <Img src={staticFile('fix2/read/t7c_plate.jpg')} style={{ position: 'absolute', width: 2560, height: 1440, filter: 'blur(18px) brightness(0.55)' }} />
        <ScreenInsert corners={PAPER_QUAD_PLACEHOLDER} w={XW.w} h={XW.h} light={0.9}><CrosswordSheet f={f} at={at} /></ScreenInsert>
      </AbsoluteFill>
      <Vig k={0.4} />
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const C5_3B: ShotDef = { stage: Stage, cx916: () => 0.5 };
export { clamp };
