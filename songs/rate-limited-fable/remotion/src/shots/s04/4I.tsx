// 4I "Don't tell me it's the servers / Don't tell me it's not about me".
// rl_l4_props (cut 4, S07: "a board of typed papers with NO / SEE METER stamps" is out; her overall note: him acting, not signs): he has
// opened the server closet in the lobby's side wall: the racks are asleep (steady green lights, the middle one in a striped nightcap, its
// LEDs breathing slowly: it's snoring), his open hand presenting them: see? (line 1). On line 2 he holds his 429 up beside his face and
// glances off right, to where the meter is (4J shows it). No notice board anywhere. Plates: L4_4I_T12 (T12a / T12b, one camera).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutCubic, outBack } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, gb, hit, pulse, c916 } from '../s03/_lib';
import { L4IMG, L4LAY } from '../l4data';

const K = 2560 / 2880;
const SN = (L4LAY['4I'].snorer_box as number[]).map((v) => v * K);     // the nightcap rack (its cap + pom)
const DW = (L4LAY['4I'].doorway_box as number[]).map((v) => v * K);
const tl = (f: number, shot: any) => {
  const cut = gb(shot, 3) - 1;                                         // line 2: the 429
  const k = inOutCubic(clamp(f / Math.max(1, cut)));
  const A0: [number, number, number] = [1300, 740, 1.04], A1: [number, number, number] = [(DW[0] + DW[2]) / 2 + 140, (SN[1] + DW[3]) / 2, 1.16];   // a slow push toward the sleeping rack
  const B: [number, number, number] = [1500, 700, 1.10];
  const punch = outBack(clamp((f - cut) / 6), 1.5);
  const c: [number, number, number] = f < cut ? [lerp(A0[0], A1[0], k), lerp(A0[1], A1[1], k), lerp(A0[2], A1[2], k)] : [B[0], B[1], B[2] * (1 + 0.02 * (1 - punch))];
  return { cut, cx: c[0], cy: c[1], s: c[2] };
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const t = tl(f, shot); const b = f >= t.cut;
  const s = t.s * (1 + pulse(g) + hit(f, t.cut, 0.015, 8));
  const breath = 0.5 - 0.5 * Math.cos((g / 30) * 2 * Math.PI / 1.6);     // the snore: one breath every 1.6 s
  const cx = (SN[0] + SN[2]) / 2, cy = SN[3] + (DW[3] - SN[3]) * 0.35, rw = (SN[2] - SN[0]) * 1.3, rh = (DW[3] - SN[3]) * 0.55;
  return (
    <Cam creep={f / shot.dur} cx={t.cx} cy={t.cy} s={s}>
      <PlateImg src={L4IMG[b ? 'I4_T12b' : 'I4_T12a'].src} />
      {/* the snoring rack's LEDs breathe (a soft green glow on its front, under the nightcap; screen blend, nothing drawn) */}
      <div style={{ position: 'absolute', left: cx - rw / 2, top: cy - rh / 2, width: rw, height: rh, borderRadius: '45%', mixBlendMode: 'screen', pointerEvents: 'none',
        background: 'radial-gradient(ellipse at 50% 50%, rgba(90,255,150,0.30) 0%, rgba(90,255,150,0.10) 45%, rgba(90,255,150,0) 72%)', opacity: 0.35 + 0.65 * breath }} />
    </Cam>
  );
};
// 9:16 (vertical later: not re-checked this round)
export const S4_4I: ShotDef = { stage: Stage, cx916: (f, shot) => { const t = tl(f, shot); return c916(t.cx, t.cx, t.s); } };
