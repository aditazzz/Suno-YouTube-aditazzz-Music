// 5C "Rate, rate, rate limited": straight down into his drawer of status-code paddles. A slow push and a light sweep across the paddles on
// the three "Rate"s.
// rl_l4_props (cut 4; S24 "5C objects unclear": show each object and its paddle): a closer drawer (L4_5C_T14: 402, 404 empty, 418, 429)
// with her bribes FILED under their codes: the bank card under 402 (Payment Required), her mug (the kit mug, coffee still in it) under 418
// (I'm a teapot). 404 is engraved on the empty slot's brass label (code) with a chalk outline where the missing paddle would be and
// NOT FOUND in it. Paddles, card and mug are all in the render (no code shapes over them).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutSine } from '../../ease';
import { FONT } from '../../theme';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, ez, Vignette, Grain, pulse, c916, HAND } from '../s03/_lib';
import { L4IMG, L4LAY } from '../l4data';

const K = 2560 / 2880;
const C = L4LAY['5C'];
const LBL = C.empty_slot_label as number[];
const D402 = C.discs['402'] as number[];
const DR = (D402[2] - D402[0]) / 2 * K;                     // disc radius on the stage
const CY = (D402[1] + D402[3]) / 2 * K;                     // the discs' centre row
const CX = (C.slots['404'][0] as number) * K;               // the empty slot
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const rates = (shot.cues ?? []).map((c) => c.frame - shot.from);
  const sweeps = rates.map((r) => clamp((f - r) / 14));
  const s = lerp(1.0, 1.07, ez(f, 0, shot.dur)) * (1 + pulse(g));
  const dash = 'rgba(238,232,214,0.62)';
  return (
    <Cam creep={f / shot.dur} s={s} cx={1280} cy={700}>
      <PlateImg src={L4IMG.C5_T14.src} />
      {/* the missing paddle: a chalk dashed disc + handle at the same place as its neighbours */}
      <svg width={2560} height={1440} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
        <circle cx={CX} cy={CY} r={DR * 0.9} fill="none" stroke={dash} strokeWidth={7} strokeDasharray="26 18" />
        <path d={`M${CX - 14},${CY + DR * 0.9} L${CX - 14},${CY + DR * 0.9 + 470} L${CX + 14},${CY + DR * 0.9 + 470} L${CX + 14},${CY + DR * 0.9}`} fill="none" stroke={dash} strokeWidth={6} strokeDasharray="20 15" />
      </svg>
      {/* engraved on the brass label (in-world plate text) */}
      <div data-fit="off" style={{ position: 'absolute', left: LBL[0] * K, top: LBL[1] * K, width: (LBL[2] - LBL[0]) * K, height: (LBL[3] - LBL[1]) * K, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: 52, color: 'rgba(62,44,16,0.9)', lineHeight: 1, textShadow: '0 1px 0 rgba(255,240,200,0.5)' }}>404</div>
      </div>
      <div data-fit="box" style={{ position: 'absolute', left: CX - DR * 0.8, top: CY + 60, width: DR * 1.6, height: 90, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontFamily: HAND, fontSize: 60, color: 'rgba(240,234,218,0.9)', whiteSpace: 'nowrap', lineHeight: 1 }}>NOT FOUND</div>
      </div>
      {/* light sweeps left to right across the drawer, one per "Rate" */}
      {sweeps.map((k, i) => k > 0 && k < 1 ? (
        <div key={i} style={{ position: 'absolute', inset: 0, mixBlendMode: 'screen', background: `linear-gradient(100deg, rgba(255,230,180,0) ${lerp(-30, 110, inOutSine(k)) - 18}%, rgba(255,230,180,0.2) ${lerp(-30, 110, inOutSine(k))}%, rgba(255,230,180,0) ${lerp(-30, 110, inOutSine(k)) + 18}%)` }} />
      ) : null)}
      <Vignette k={0.45} />
      <Grain g={g} />
    </Cam>
  );
};
// 9:16 (vertical later: not re-checked this round): centred between the empty 404 and the 418 + mug
const PAIR_X = ((C.slots['404'][0] as number) + (C.slots['418'][0] as number)) / 2 * K;
export const S5_5C: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const s = lerp(1.0, 1.07, ez(f, 0, shot.dur)) * (1 + pulse(shot.from + f)) * (1 + 0.014 * clamp(f / shot.dur));
  return c916(PAIR_X, 1280, s);
} };
