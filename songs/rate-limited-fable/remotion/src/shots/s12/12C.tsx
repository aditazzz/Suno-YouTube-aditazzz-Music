// 12C "Rate, rate, rate limited" (cut 4, lane L2; her #30 note, S28): the yawn goes round, really in it: the cat on the ledge over the door
// (L4's one cat), then Cooper beside her, then her (hand to her mouth), one per "rate"; behind the glass the dim lobby and its panda clock at
// 5:58 (in the plates). Plates: l2/12C_cat, 12C_coop, 12C_her (one camera, her side of the door).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { L2Img, settle } from '../l2kit';
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const c = (shot.cues ?? []).map((q) => q.frame - shot.from); const c2 = c[1] ?? 9, c3 = c[2] ?? 17;
  const id = f < c2 ? '12C_cat' : f < c3 ? '12C_coop' : '12C_her';
  // the camera follows the yawn down the chain: the cat on the ledge, then Cooper, then her (6-frame eases on the cues; Cam keeps it on the plate)
  const P = [[1420, 520, 1.34], [1390, 980, 1.30], [1150, 1000, 1.34]] as const;
  const a = inOutSine(clamp((f - c2 + 3) / 6)), b = inOutSine(clamp((f - c3 + 3) / 6));
  const cx = lerp(lerp(P[0][0], P[1][0], a), P[2][0], b), cy = lerp(lerp(P[0][1], P[1][1], a), P[2][1], b), sc = lerp(lerp(P[0][2], P[1][2], a), P[2][2], b);
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  return <Cam cx={cx} cy={cy} s={sc * lerp(1.0, 1.03, k) * (1 + settle(f, c2, 0.006) + settle(f, c3, 0.006))}><L2Img id={id} /></Cam>;
};
export const S12_12C: ShotDef = { stage: Stage, cx916: () => 0.45 };
