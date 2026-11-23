// 12B "Hit me with a four-two-nine" (cut 4, lane L2; her #5/#29 notes): yoga instead of the 429 paddle, one pose a beat, held:
// warrior 2 (deadpan focus over her hand) -> tree, wobbling, Cooper leaning his whole weight on her standing leg -> happy baby, Cooper licking
// her face -> the child's-pose collapse. The vacuum copies every pose on its own little mat: tipped on one edge, balanced on one wheel,
// upside down spinning its wheels, flat and still. Plates: l2/12B_w2, 12B_tree, 12B_baby, 12B_child (one camera on her mat by the door).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit } from '../first30/kit';
import { L2Img, beat } from '../l2kit';
import { LobbyPanda } from '../c4clock';
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const b = [0, beat(shot, 1, 17), beat(shot, 2, 35), beat(shot, 3, 52)];
  const i = f >= b[3] ? 3 : f >= b[2] ? 2 : f >= b[1] ? 1 : 0;
  const id = ['12B_w2', '12B_tree', '12B_baby', '12B_child'][i];
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  const s = lerp(1.0, 1.05, k) * (1 + hit(f, b[1], 0.010, 9) + hit(f, b[2], 0.010, 9) + hit(f, b[3], 0.016, 12));
  return <Cam cx={1280} cy={720} s={s}><L2Img id={id} /><LobbyPanda id={id} h={5} m={58} /></Cam>;
};
export const S12_12B: ShotDef = { stage: Stage, cx916: () => 0.45 };
