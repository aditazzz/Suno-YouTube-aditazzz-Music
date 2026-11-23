// 9C (cut 5; plan §3: f4455-4593, 4.6 s; N43): her phone, the chat from 9B (his "Let me know if there's anything else!"). She pastes
// her asks into the input, one Pasted card per beat from 4455 (script.CHIPS_9C: make me MORE famous / my Oscars speech / my AI
// Grammys speech / CEO of SLOPCORP / the font / undo the font), each ringed as it lands; on "so much else" (4558) more flood in
// behind them and the field swallows the thread. Framed close so each card's words read; the camera eases back as the pile grows.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { BEFORE, CHIP, CHIPS_9C, CHIPS_9C_FLOOD } from '../../blocks/real/script';
import { MobileChat5 } from './AppField';
import { PhoneStage, clamp, ez, loc } from './kit';

export const C9 = { BEATS: [4455, 4472, 4489, 4507, 4524, 4541], FLOOD: 4558 };
const FLOOD_GAP = 3;                                            // the flood: a card every 3 frames

export const Screen9C: React.FC<{ f: number; beats: number[]; flood: number }> = ({ f, beats, flood }) => {
  const n = beats.filter((b) => f >= b).length;
  const m = f >= flood ? Math.min(CHIPS_9C_FLOOD.length, 1 + Math.floor((f - flood) / FLOOD_GAP)) : 0;
  const chips = [...CHIPS_9C.slice(0, n), ...CHIPS_9C_FLOOD.slice(0, m)];
  const ring = (i: number) => (i < n ? 1 - clamp((f - beats[i] - 6) / 10) : 0);
  return (
    <MobileChat5 title="make the font bigger" msgs={BEFORE} hideThread={chips.length >= 9}
      field={{ chips, chipW: 112, chipRing: ring, banner: true, disabled: true, model: CHIP.night, placeholder: '' }} />
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const beats = C9.BEATS.map((b) => loc(shot, b)); const flood = loc(shot, C9.FLOOD);
  // close on the field (cards' type >= 34 px), easing back a touch as the flood lands
  const back = ez(f, flood - 4, flood + 20);
  return (
    <PhoneStage f={f} dur={shot.dur} k0={4.25} k1={4.25 - 0.9 * back} focus0={640} focus1={600 - 60 * back} time="4:41" seed={9} rot={-1.4}>
      <Screen9C f={f} beats={beats} flood={flood} />
    </PhoneStage>
  );
};
export const C5_9C: ShotDef = { stage: Stage, cx916: () => 0.5 };
