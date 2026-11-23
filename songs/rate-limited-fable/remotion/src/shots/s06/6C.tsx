// 6C "I could go to sleep" (cut 4, lane L2; her R3/S12/S13): in her living room, mid forearm stand (6D's own build: one moment, one her),
// close on the panda on her right wrist, upside down, 3:59, the chrono hand sweeping; she cranes to read it. No text: the watch is the clock.
// Plate: l2/6C (blrl4_act 6C). The face is L3's PandaPin on the dial square from the plate's layout (the face turns with the watch).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { PandaPin, pt } from '../../blocks/PandaClock';
import { Quad } from '../../blocks/ScreenInsert';
import { L2Img, beat, settle, shrinkQuad } from '../l2kit';
import { L2Q } from '../l2data';
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const k = inOutSine(clamp(f / (shot.dur - 1)));
  const q = L2Q['6C']?.dial as Quad | undefined; const c = (L2Q['6C']?.dial_c as [number, number] | undefined) ?? [1280, 720];
  const b2 = beat(shot, 2, 35);
  return (
    <Cam cx={lerp(1280, c[0], 0.35 * k)} cy={lerp(720, c[1], 0.35 * k)} s={lerp(1.0, 1.10, k) * (1 + settle(f, b2, 0.008))}>
      <L2Img id="6C" />
      {q ? <PandaPin corners={shrinkQuad(q, 0.84)} time={pt(3, 59)} chrono={(44 + f / 30) % 60} running={1} light={0.92} uid="w6c" /> : null}
    </Cam>
  );
};
export const S6_6C: ShotDef = { stage: Stage, cx916: () => 0.5 };
