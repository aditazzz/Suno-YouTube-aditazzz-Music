// rl5_d5 cut 5: rl5_b's f2 plates (workers/rl5_b/PATCH.md), looked at on workers/rl5_d5/b.jpg.
//  4H (1990-2129) the outgoing shelf panorama (5760 x 2160 -> 3840 x 1440 on the stage): one slow slide left -> right across 7C, 2A, 5F
//     (every word stays >= 330 stage px inside the frame at both ends). Plan row 4H, her N22 "signs off frame".
//  5A (2302-2372) his side of the slot: her mug on the brass tray, steam; eyes -> closed 3 f -> 418 on "li-(mited)" (2328). Low slow push.
//  5B (2372-2511) first half = K plate 4-2-9 (C5_5B1, leaves moving at 68); second half (2441) = THE cat crossing the lobby floor, him
//     leaning down to it: dark 3 f (B's 5B has no 429 state) -> eyes (looking at the cat) -> closed 3 f -> 200 (green). The drift continues (arrive).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { plateShot } from './plate';
import { seq, C5_5B1_LEAVE } from './K';
import { Grain2 } from '../../blocks/real/Scene';
import { VisorSeg, VISOR_ROWS } from '../c7/kit/seg';
import { SignFace } from '../c7/kit/logo';
import { has } from '../c7/kit/trans';
import { Steam, Glow, visorK } from '../c7/kit/life';

const io = (t: number) => (t <= 0 ? 0 : t >= 1 ? 1 : 0.5 - 0.5 * Math.cos(Math.PI * t));
const S4H: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const k = io(f / Math.max(1, shot.dur - 1));
  const x = -1280 * k;                                             // window 0..2560 -> 1280..3840 of the 3840-wide panorama
  return (
    <AbsoluteFill style={{ background: '#140d09', overflow: 'hidden' }}>
      <Img src={staticFile('c5/4H/plate.jpg')} style={{ position: 'absolute', left: 0, top: 0, width: 3840, height: 1440, transform: `translateX(${x.toFixed(2)}px)` }} />
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const C5_4H: ShotDef = { stage: S4H, cx916: (f, shot) => 0.3 + 0.4 * io(f / Math.max(1, shot.dur - 1)) };

const withGrain = (d: ShotDef): ShotDef => ({ ...d, stage: (p) => { const S = d.stage; return <AbsoluteFill><S {...p} /><G /></AbsoluteFill>; } });
const G: React.FC = () => { const f = useCurrentFrame(); return <Grain2 f={f} />; };

// 5A: 418 fully on at local 26 ("li-" 2328 - 2302); the push leans toward the mug and his visor, top edge kept
// rl7_ra (her H7.18): 418 in the seven-segment visor face (dark plate + c7/kit/seg)
export const S5A_SRC = (f: number) => `c5/5A/plate_${f < 23 ? 'eyes' : f < 26 ? 'closed' : 'dark'}.jpg`;
export const Seg5A: React.FC<{ f: number }> = ({ f }) => (f >= 26 ? <VisorSeg text="418" quad={VISOR_ROWS['5A'].quad} color={VISOR_ROWS['5A'].color} /> : null);
// rl7_ra: the mug steams (her mug on his tray, PLAN7 row 23) and his chest light breathes
export const C5_5A = withGrain(plateShot({ src: S5A_SRC, cam: [{ cx: 1280, cy: 720, s: 1.0 }, { cx: 1250, cy: 700, s: 1.045 }], over: ({ f, shot }) => (
  <><Steam abs={shot.from + f} x={1010} y={872} h={460} w={95} n={7} op={0.2} seed={23} /><Glow x={1652} y={1205} rx={70} color="rgba(120,255,220,0.9)" op={0.22 * visorK(shot.from + f)} /><Seg5A f={f} /></>) }));

// 5B second half: local 0 = 2441
// B's 5B plate has no 429 state: the cut lands on `dark` (digits -> eyes protocol), 3 f, then eyes; closed 3 f; 200 from 44
// rl7_ra: 200 = seven-segment (H7.8); rl7_fix3d's 5B (her H7.19: desk glass, logo in 3D) when it lands
const FIX5B = has('c7/fix3d/5B/plate_dark.jpg');
const v5B = (f: number) => `${FIX5B ? 'c7/fix3d/5B' : 'c5/5B'}/plate_${f < 3 ? 'dark' : f < 41 ? 'eyes' : f < 44 ? 'closed' : 'dark'}.jpg`;
const C5_5B2 = withGrain(plateShot({ src: v5B,
  cam: [{ cx: 1300, cy: 740, s: 1.07 }, { cx: 1250, cy: 760, s: 1.03 }], arrive: true,
  over: ({ f }) => <>{FIX5B ? null : <SignFace dir="5B" />}{f >= 44 ? <VisorSeg text="200" quad={VISOR_ROWS['5B'].quad} color={VISOR_ROWS['5B'].color} /> : null}</> }));
export const C5_5B = seq(C5_5B1_LEAVE, 69, C5_5B2);

// rl5_d5 2E (913-1052, plan row 2E "one slow slide from his outgoing shelf, full of shipped parcels, across the door to her and her one
// unshipped parcel under the neon"): rl5_a1's c5/2E/2E5.jpg, a 5760 x 2200 cylindrical panorama (verticals straight). Drawn at 0.72
// (4147 x 1584 stage; 30 px off the top so her pom-pom keeps air, FAME's label stays above the bottom edge), slid 0 -> 1404 stage px:
// opens on the lobby (ShipIt!, the shelf, him at the counter) through the glass, ends on the door edge, her, FAME and the neon.
const K2E = 0.72, W2E = 5760 * K2E, H2E = 2200 * K2E, X2E = 1950 * K2E;
const S2E: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const k = io(f / Math.max(1, shot.dur - 1));
  return (
    <AbsoluteFill style={{ background: '#140d09', overflow: 'hidden' }}>
      <Img src={staticFile('c5/2E/2E5.jpg')} style={{ position: 'absolute', left: 0, top: -30, width: W2E, height: H2E, transform: `translateX(${(-X2E * k).toFixed(2)}px)` }} />
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const C5_2E: ShotDef = { stage: S2E, cx916: (f, shot) => 0.35 + 0.3 * io(f / Math.max(1, shot.dur - 1)) };
