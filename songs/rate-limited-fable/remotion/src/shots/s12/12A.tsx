// 12A "Rate, rate, rate limited" (cut 4, lane L2; S28: her knock, her own acting): through the glass from his dim side, she knocks, gently, three
// times on the three "Rate"s (knuckles on the glass for 3 frames, drawn back), the hopeful little smile, brows up. The lobby he dimmed at 5:50
// stays dim (S22); the panda clock reads 5:58 (in the plates). Plates: l2/12A_on, l2/12A_back.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit } from '../first30/kit';
import { L2Img } from '../l2kit';
import { FixPlate } from '../c7/fix713/FixPlate';   // rl7_fixb: tube-family neon baked into the (out-of-focus) plate
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const ks = (shot.cues ?? []).map((c) => Math.max(0, c.frame - shot.from)); const knocks = ks.length ? ks : [0, 9, 18];
  const on = knocks.some((k) => f >= k && f < k + 3);
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  const s = lerp(1.0, 1.06, k) * (1 + knocks.reduce((a, kk) => a + hit(f, kk, 0.006, 8), 0));
  return <Cam cx={1280} cy={720} s={s}><FixPlate src={on ? 'c7/apt/12A_on_retire.jpg' : 'c7/apt/12A_back_retire.jpg'} /></Cam>;
};
export const S12_12A: ShotDef = { stage: Stage, cx916: () => 0.5 };
