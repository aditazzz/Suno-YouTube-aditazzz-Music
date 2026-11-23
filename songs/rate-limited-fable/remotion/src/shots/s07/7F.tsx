// 7F "He agreed with everything, no chemistry": a ping-pong on the drum fill between crops of DATE: the other model, her, Cooper's stare;
// it lands on DATELOOK with her side-eye (S18 R4, final) for the last beat.
// rl_l4_props (cut 4, her note f3486: "Great choice should flicker brightly on his visor. Not sure why it says please hold"): the
// visor now reads GREAT CHOICE! in his own LED dot-matrix (the words cycle one per robot crop, the way an LED visor shows a phrase too long
// for it: GREAT, CHOICE!, GREAT), bright saturated green with a glow (it's a light), a 1-frame flicker as each robot crop lands on "agreed".
// The baked PLEASE H... is painted over with the band's own black; the phone handset stays in front (the visible band starts at its edge).
// The chest display box is gone (dark); the robot crop is tighter on his head so the visor reads at phone size.
// Visor quad measured on cutfix/date_rain.jpg (2880 x 1620; workers/rl_l4_props/visor_zoom.png). If L1's new 7E date plate moves the camera, re-measure VQ.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, gridF, Grain } from './_lib';
import { CandleLight, DATE_PLATE } from './7E';

const KP = 2560 / 2880;                                   // plate px -> stage px
// the visor band's visible quad (plate px): TL at the handset's edge, TR, BR, BL at the handset's edge
const VQ: [number, number][] = [[2105, 424], [2223.5, 417.5], [2224.5, 459.5], [2074, 473]].map(([x, y]) => [x * KP, y * KP] as [number, number]);
const ROBOT = { cx: 1915, cy: 520, s: 2.7 }, HER = { cx: 640, cy: 470, s: 2.0 }, COOPER = { cx: 1262, cy: 330, s: 2.1 };

// 5 x 7 dot-matrix glyphs (his visor's own LED grid)
const G5: Record<string, string[]> = {
  G: ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.###.'], R: ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
  E: ['#####', '#....', '#....', '####.', '#....', '#....', '#####'], A: ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
  T: ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'], C: ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
  H: ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'], O: ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
  I: ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'], '!': ['..#..', '..#..', '..#..', '..#..', '..#..', '.....', '..#..'],
};
const bil = (u: number, v: number): [number, number] => {           // bilinear map of (u along, v across) onto the visor quad
  const [a, b, c, d] = VQ; const top = [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]; const bot = [d[0] + (c[0] - d[0]) * u, d[1] + (c[1] - d[1]) * u];
  return [top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v];
};
const Visor: React.FC<{ word: string; bright: number }> = ({ word, bright }) => {
  const cols = word.length * 6 - 1; const u0 = 0.06, u1 = 0.94, v0 = 0.16, v1 = 0.84;
  const du = (u1 - u0) / cols; const dv = (v1 - v0) / 7;
  const dots: React.ReactNode[] = [];
  [...word].forEach((ch, i) => (G5[ch] ?? []).forEach((row, r) => [...row].forEach((px, c) => {
    if (px !== '#') return;
    const [x, y] = bil(u0 + (i * 6 + c + 0.5) * du, v0 + (r + 0.5) * dv); dots.push(<circle key={`${i}-${r}-${c}`} cx={x} cy={y} r={2.05} />);
  })));
  const poly = VQ.map((p) => p.join(',')).join(' ');
  return (
    <svg width={2560} height={1440} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
      <polygon points={poly} fill="#121314" />
      <g fill="#7dffa0" opacity={bright} style={{ filter: 'drop-shadow(0 0 2.5px rgba(110,255,150,0.95)) drop-shadow(0 0 6px rgba(90,255,140,0.55))' }}>{dots}</g>
    </svg>
  );
};

const Crop: React.FC<{ c: { cx: number; cy: number; s: number }; g: number; visor?: { word: string; bright: number } }> = ({ c, g, visor }) => (
  <AbsoluteFill>
    <Cam cx={c.cx} cy={c.cy} s={c.s}><PlateImg src={DATE_PLATE} /><CandleLight g={g} />{visor ? <Visor {...visor} /> : null}</Cam>
  </AbsoluteFill>
);

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const bt = gridF(shot); const e = ((bt[1] ?? 17) - (bt[0] ?? 0)) / 2;   // an eighth note
  const step = Math.floor(f / e);
  const land = Math.round(e * 6);
  let pic: React.ReactNode;
  // rl_cut4c_fix (rl_watch4b blocker, f3534-3552: the old S18 R4 close was off-model: no hat, sunglasses on her head, red lipstick): the landing
  // is now L1 roll's on-model date close (build/stills/L1R/date/date_rain_close.png: same camera, pose and side-eye; LOVE hat, no glasses,
  // natural lips; rendered with her_look.py and checked by rl_l1_roll), as c4fix/7F_close.jpg. Same push and timing.
  if (f >= land) pic = <Cam cx={1280} cy={720} s={1.0 + 0.02 * clamp((f - land) / 20)}><PlateImg src="c4fix/7F_close.jpg" /></Cam>;
  else {
    const seqn = [0, 1, 0, 2, 0, 1][step] ?? 0; const local = f - step * e;
    // the visor cycles the phrase one word per robot crop (each crop is an eighth note, too short for both words at a readable size):
    // GREAT, CHOICE!, GREAT; it flickers as each crop lands (frame 1 dim, the LED catching)
    const word = ['GREAT', 'CHOICE!', 'GREAT'][Math.floor(step / 2)] ?? 'GREAT'; const bright = local >= 1 && local < 2 ? 0.25 : 1;
    pic = seqn === 0 ? <Crop c={ROBOT} g={g} visor={{ word, bright }} /> : seqn === 1 ? <Crop c={HER} g={g} /> : <Crop c={COOPER} g={g} />;
  }
  return <AbsoluteFill>{pic}<Grain g={g} /></AbsoluteFill>;
};
export const S7_7F: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const e = ((gridF(shot)[1] ?? 17) - (gridF(shot)[0] ?? 0)) / 2; const step = Math.floor(f / e);
  if (f >= e * 6) return 0.45; return [0.5, 0.5, 0.5, 0.5, 0.5, 0.5][step] ?? 0.5; } };
