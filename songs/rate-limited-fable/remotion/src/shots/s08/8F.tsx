// 8F "Rate limited, rate limited" (4:39), the chorus pair. Cut 4 (rl_l3_ui; R6: the 429 close was the same picture nine times;
// §2a: the digital box goes, the panda wall clock takes its spot): beats 1-2 = from her side, close on his face behind the glass
// with the lobby's panda clock at 4:39 over his shoulder (the time is the point: the second chorus, still waiting); beats 3-4 =
// pull back to the whole door (her side), a quick punch that settles. The time agrees with 8E's "Read 4:37".
// PLATE: S7 D1 (final). Clock in code.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, outCubic, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, Grain, PlateImg, gridF, hit } from '../s07/_lib';
import { LobbyPanda, S7_CLOCK, pt } from '../../blocks/PandaClock';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const second = gridF(shot)[2] ?? 35;
  const punch = (a: number, s0: number, s1: number) => lerp(s0, s1, outCubic(clamp((f - a) / 5))) * (1 + hit(f, a + 5, 0.008, 10));
  const t = pt(4, 39, 5 + f / 30);
  return (
    <AbsoluteFill>
      {f < second ? (
        <Cam cx={(1290 + S7_CLOCK.cx) / 2 + 10} cy={640} s={punch(0, 2.2, 2.32)}><PlateImg src="secb/D1.jpg" /><LobbyPanda time={t} chrono={(5 + f / 30) % 60} /></Cam>
      ) : (
        <Cam cx={1290} cy={720} s={punch(second, 1.0, 1.06)}><PlateImg src="secb/D1.jpg" /><LobbyPanda time={t} /></Cam>
      )}
      <Grain g={g} />
    </AbsoluteFill>
  );
};
export const S8_8F: ShotDef = { stage: Stage, cx916: (f, shot) => (f < (gridF(shot)[2] ?? 35) ? 0.5 : 0.505) };
