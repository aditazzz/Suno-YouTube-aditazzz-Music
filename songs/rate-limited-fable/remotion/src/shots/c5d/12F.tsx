// rl5_d cut 5: cut 4e 12F with the tap camera hits taken out (CUT5_PLAN §3 12F "Single push (no double punch-in)"). Until A1s plain-strap plate.
// 12F "Rate limited, rate limited" (cut 4, lane L2; her #34 note "Yet another wall clock?!"): her watch, not another clock: tight on her right
// wrist, the panda at 5:59 (the same face as the wall clock: one object), her other finger tapping the crystal, her eyes above it, wide and
// out of focus. Plate: l2/12F; the face is L3's PandaPin on the dial square (chrono hand sweeping), a small hit on each tap.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit } from '../first30/kit';
import { PL, Pl } from '../s10/_lib';
import { clamp, inOutSine, lerp } from '../../ease';

/** T27: the lobby clock close; the code hands sit on its pivot (stage centre). r = hand scale (minute hand 0.76 r) */
export const T27_CLOCK = { cx: 2160 * (2560 / 4320), cy: 1215 * (2560 / 4320), r: 400 };
export const ClockWall: React.FC = () => <Pl src={PL.T27} />;
import { PandaPin, pt } from '../../blocks/PandaClock';
import { Quad } from '../../blocks/ScreenInsert';
import { L2Img, beat, shrinkQuad } from '../l2kit';
import { L2Q } from '../l2data';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const q = L2Q['12F']?.dial as Quad | undefined; const c = (L2Q['12F']?.dial_c as [number, number] | undefined) ?? [1280, 720];
  const taps = [beat(shot, 1, 17), beat(shot, 2, 35), beat(shot, 3, 52)];
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  const s = lerp(1.0, 1.08, k); void taps; void hit;
  return (
    <Cam cx={lerp(1280, c[0], 0.3 * k)} cy={lerp(720, c[1], 0.3 * k)} s={s}>
      <L2Img id="12F" />
      {q ? <PandaPin corners={shrinkQuad(q, 0.84)} time={pt(5, 59)} chrono={(48 + f / 30) % 60} running={1} light={0.95} uid="w12f" /> : null}
    </Cam>
  );
};
export const C5_12F: ShotDef = { stage: Stage, cx916: () => 0.5 };
