// 1G (cut 5; plan §3: f478-530; OV, N47, C11): her phone, the real Claude app at 2:01. Above: her "Hey Claude? Can you help me
// write a song?" and his "Sure, let's go!" (request 1, the one that shipped: the A SONG parcel). She sends request 2, "Can you make
// me famous?"; on "Then the screen went grey" (f496) the limit banner lands over the composer and the whole screen greys (the wash
// matches 1H's facade). Chip: Fable 5.2 (Medium, the app's format). The phone drifts down 2%.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { MobileChat, Msg } from '../../blocks/real/ClaudeChat';
import { CHIP, LADDER } from '../../blocks/real/script';
import { PhoneStage, ez, loc } from './kit';

export const G1 = { SEND: 486, BANNER: 496 };            // absolute frames
const TYPED = LADDER[1].her;

export const Screen1G: React.FC<{ f: number; send: number; banner: number }> = ({ f, send, banner }) => {
  const sent = f >= send;
  const msgs: Msg[] = [{ who: 'user', text: LADDER[0].her }, { who: 'claude', text: LADDER[0].claude! }, ...(sent ? [{ who: 'user' as const, text: TYPED }] : [])];
  const tap = f >= send - 3 && f < send + 2 ? Math.sin(((f - send + 3) / 5) * Math.PI) : 0;
  return (
    <MobileChat title="Help writing a song" msgs={msgs}
      composer={{ text: sent ? '' : TYPED, caret: !sent, caretOn: f % 16 < 10, banner: f >= banner, disabled: f >= banner, model: CHIP.early, sendPressed: tap }} />
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const send = loc(shot, G1.SEND), banner = loc(shot, G1.BANNER);
  const grey = 0.85 * ez(f, banner, banner + 14);
  // §2f: one eased move; the screen drifts down 2% (focus moves up the page by ~2% of the frame height)
  return (
    <PhoneStage f={f} dur={shot.dur} k0={3.05} k1={3.11} focus0={598} focus1={588} time="2:01" seed={41} grey={grey}>
      <Screen1G f={f} send={send} banner={banner} />
    </PhoneStage>
  );
};
export const C5_1G: ShotDef = { stage: Stage, cx916: () => 0.5 };
