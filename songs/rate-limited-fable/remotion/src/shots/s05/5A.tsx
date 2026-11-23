// 5A "Rate, rate, rate limited": the mail slot, lobby side, from over his desk. One thing per "Rate" is pushed through the slot
// (a mug, a bank card, a slip) and each gets its own paddle rising from below: 418, 402, 429. Each offering is pulled back
// out through the slot before the next one comes (rejected); the slip stays stuck half through under the 429.
// PLATE (rl_cut1 a2): S21f D6 + mug / card / slip RGBA (half-through pose) + pad418 / pad402 / pad429 RGBA (top of their rise).
// The items slide along the slot (clipped at the slot's top edge: above it they are inside the door); the paddles rise from
// behind the near edge (clipped at still row 1536, where their renders end). Paddles staggered sideways (they overlap when all up).
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, outBack, inCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, ez, gb, hit, pulse, Vignette, Grain, W } from '../s03/_lib';
import { IMG, LAY, Lyr, K, ImgKey } from './_cut1b';
import { IMG9, LAY9 } from './_fix3_5a_data';
import { L4IMG } from '../l4data';

// rl_l4_props (cut 4, her note f2307 "What is that cylinder object?" + S02): 16:9 plate L4_5A_D6 (S21f's camera, same layout) with the
// doormat at RETRY-AFTER: 2h04m, and HER mug (the kit mug: speckled cream, big handle, the A) through the slot on its side, rim and handle
// to us so it reads as a mug. The card / slip / paddle layers are S21f's (same camera). The mug's clip at the slot's top edge only holds
// while it slides out; once out it is in front of the door (its own render already has the door's occlusion), so the clip opens.
const L4M = L4IMG.A5_mug;
const MugL4: React.FC<{ dy: number; open: number }> = ({ dy, open }) => (
  <div style={{ position: 'absolute', inset: 0, clipPath: `inset(${SLOT[1] * K * (1 - open)}px 0 0 0)` }}>
    <Img src={staticFile(L4M.src)} style={{ position: 'absolute', left: L4M.x * K, top: (L4M.y + dy) * K, width: L4M.w * K, height: L4M.h * K }} />
  </div>
);

const SLOT = LAY.D6.slot_lobby as number[];          // [850, 565, 2029, 857] still px
const EDGE = 1536;                                    // the paddles' renders end here (the near edge occludes them)
const ITEMS: ImgKey[] = ['mug', 'card', 'slip'];
const PADS: { n: ImgKey; dx: number; rest: number }[] = [{ n: 'pad418', dx: -210, rest: 0 }, { n: 'pad402', dx: -150, rest: 260 }, { n: 'pad429', dx: 40, rest: 300 }];   // rest: lower than rendered, keeps the slot clear
const Stage169: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const at = [0, 1, 2].map((i) => gb(shot, i));
  const s = 1 + pulse(g) + hit(f, at[1] + 5, 0.008, 6) + hit(f, at[2] + 5, 0.012, 7) + 0.03 * ez(f, 0, shot.dur);
  return (
    <Cam creep={f / shot.dur} s={s}>
      <PlateImg src={L4IMG.A5_D6.src} />
      {/* her mug (L4): slides out of the slot, then sits proud of the door */}
      {(() => {
        const e = outBack(clamp((f - at[0] + 3) / 7), 1.2); const r = inCubic(clamp((f - (at[1] - 9)) / 6));
        const vis = clamp(e - r, -0.2, 1.2); if (f < at[0] - 3 || r >= 1) return null;
        const D = L4M.y + L4M.h - SLOT[1];
        return <MugL4 dy={-D * (1 - vis)} open={clamp(e * 1.2 - 0.2) * (1 - r)} />;
      })()}
      {/* offerings: clipped above the slot's top edge (inside the door) */}
      <div style={{ position: 'absolute', inset: 0, clipPath: `inset(${SLOT[1] * K}px 0 0 0)` }}>
        {ITEMS.map((n, i) => {
          if (n === 'mug') return null;
          const a = IMG[n]; const D = a.y + a.h - SLOT[1];
          const e = outBack(clamp((f - at[i] + 3) / 7), 1.2);
          const r = i < 2 ? inCubic(clamp((f - (at[i + 1] - 9)) / 6)) : 0;
          const vis = clamp(e - r, -0.2, 1.2);
          if (f < at[i] - 3 || r >= 1) return null;
          return <Lyr key={n} n={n} dy={-D * (1 - vis)} />;
        })}
      </div>
      {/* paddles: rise from behind the near edge */}
      <div style={{ position: 'absolute', inset: 0, clipPath: `inset(0 0 ${(1620 - EDGE) * K}px 0)` }}>
        {PADS.map((p, i) => {
          const k = outBack(clamp((f - at[i] - 4) / 9), 1.3);
          if (k <= 0) return null;
          const a = IMG[p.n]; const D = EDGE - a.y + 10;
          return <Lyr key={p.n} n={p.n} dx={p.dx} dy={p.rest + (D - p.rest) * (1 - k)} />;
        })}
      </div>
      <Vignette k={0.4} />
      <Grain g={g} />
    </Cam>
  );
};
// 9:16 (rl_fix3_5a, QA3: the 402 / 429 numbers sat at 80-97% height, under the Shorts UI): its own portrait re-render of the same set
// (blrl_fix3_5a -> F3_D6_916, 1620 x 2880: same camera side, higher and wider), drawn into the 810 px column at the stage centre
// (cx916 0.5, a fixed frame: slot + slip at ~34-40% height, all three numbers at ~37-52%, the desk's near edge at ~57%). 418 left, 402 right
// (beside the slot), 429 in the middle, in front, under the stuck slip. Same timing, same eases, same push as 16:9.
// The paddles rise from behind the desk edge (clip at EDGE9); under each paddle its stkL layer (the same paddle, sticks down to the
// floor, rendered with the desk hidden) fills the stick while the rise overshoots; dy is also clamped so the stick's end never shows.
type K9 = keyof typeof IMG9;
const Q = 810 / 1620, X9 = W / 2 - 405;
const SLOT9 = LAY9.slot_lobby as number[];
const PADS9: { n: K9; s: K9 }[] = [{ n: 'pad418', s: 'stkL418' }, { n: 'pad402', s: 'stkL402' }, { n: 'pad429', s: 'stkL429' }];
const SB = (n: K9) => (IMG9[n] as { solid_bottom?: number }).solid_bottom ?? 0;          // last solid row (pads: the desk edge cuts them there)
const EDGE9 = Math.max(...PADS9.map((p) => SB(p.n))) + 1;
const L9: React.FC<{ n: K9; dy?: number }> = ({ n, dy = 0 }) => {
  const a = IMG9[n];
  return <Img src={staticFile(a.src)} style={{ position: 'absolute', left: a.x * Q, top: (a.y + dy) * Q, width: a.w * Q, height: a.h * Q }} />;
};
const Stage916: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const at = [0, 1, 2].map((i) => gb(shot, i));
  const s = 1 + pulse(g) + hit(f, at[1] + 5, 0.008, 6) + hit(f, at[2] + 5, 0.012, 7) + 0.03 * ez(f, 0, shot.dur);
  return (
    <Cam creep={f / shot.dur} s={s}>
      <div style={{ position: 'absolute', left: X9, top: 0, width: 810, height: 1440, overflow: 'hidden' }}>
        <Img src={staticFile(IMG9.D6v.src)} style={{ position: 'absolute', left: 0, top: 0, width: 810, height: 1440 }} />
        {/* offerings: clipped above the slot's top edge (inside the door) */}
        <div style={{ position: 'absolute', inset: 0, clipPath: `inset(${SLOT9[1] * Q}px 0 0 0)` }}>
          {(['mug', 'card', 'slip'] as K9[]).map((n, i) => {
            const a = IMG9[n]; const D = a.y + a.h - SLOT9[1];
            const e = outBack(clamp((f - at[i] + 3) / 7), 1.2);
            const r = i < 2 ? inCubic(clamp((f - (at[i + 1] - 9)) / 6)) : 0;
            const vis = clamp(e - r, -0.2, 1.2);
            if (f < at[i] - 3 || r >= 1) return null;
            return <L9 key={n} n={n} dy={-D * (1 - vis)} />;
          })}
        </div>
        {/* paddles: rise from behind the desk's near edge */}
        <div style={{ position: 'absolute', inset: 0, clipPath: `inset(0 0 ${(2880 - EDGE9) * Q}px 0)` }}>
          {PADS9.map((p, i) => {
            const k = outBack(clamp((f - at[i] - 4) / 9), 1.3);
            if (k <= 0) return null;
            const D = EDGE9 - IMG9[p.n].y + 10; const dy = Math.max(D * (1 - k), EDGE9 + 6 - SB(p.s));   // overshoot never lifts the stick's end above the edge
            return <React.Fragment key={p.n}><L9 n={p.s} dy={dy} /><L9 n={p.n} dy={dy} /></React.Fragment>;
          })}
        </div>
      </div>
      <Vignette k={0.4} />
      <Grain g={g} />
    </Cam>
  );
};
const Stage: React.FC<ShotProps> = (p) => (p.fmt === '9x16' ? <Stage916 {...p} /> : <Stage169 {...p} />);
export const S5_5A: ShotDef = { stage: Stage, cx916: () => 0.5 };
