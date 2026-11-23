// 7G "My friends all say you're just a tool": her phone (rl_screens real-phone kit, phone_7G 16x9): the group chat
// scrolls in on the beat; "he is A TOOL" lands on beat 4. The layer carries its own push and room; nothing added.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { SeqImg, seqSrc } from './_lib';
// rl_cutfix (Nov 15): 16:9 frames re-composited on the LIFTED room (warm lamp practical; was near-black): cutfix/screens/. Screen content unchanged.
const liftSrc = (id: string, g: number) => seqSrc(id, g).replace(`secb/${id}/`, `cutfix/screens/${id}_16x9/`).replace(/\.\w+$/, '.png');
const Stage: React.FC<ShotProps> = ({ shot }) => <AbsoluteFill><Img src={staticFile(liftSrc("phone_7G", shot.from + useCurrentFrame()))} style={{ position: "absolute", left: 0, top: 0, width: 2560, height: 1440 }} /></AbsoluteFill>;
// 9:16: the phone's own 9:16 layer (the screen is the frame, key line inside the safe zone), drawn after the reframe
const Screen: React.FC<ShotProps> = ({ shot, fmt }) => fmt === '9x16'
  ? <Img src={staticFile(seqSrc('phone_7G_916', shot.from + useCurrentFrame()))} style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1920 }} /> : null;
export const S7_7G: ShotDef = { stage: Stage, screen: Screen, cx916: () => 0.5 };
