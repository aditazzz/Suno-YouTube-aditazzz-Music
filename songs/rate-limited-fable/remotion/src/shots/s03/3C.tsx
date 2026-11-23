// 3C "Retry, retry, retry after" (cut 4, rl_l3_ui; R1 + S03, her standing rule "a real Claude chat app ... nothing homemade"):
// her phone, close: the real Claude Settings > Usage page. Current session 100% used, "Resets in 3 hr 52 min" (2:08 + 3:52 = 6:00),
// "Limit reached at 2:01 AM" (was "since 11:58 PM"). On each stressed "try" she pulls to refresh: the iOS spinner, the page
// snaps back, nothing changes (that is the joke). The phone is framed close enough that the page's smallest type is >= 34 px.
// 9:16 keeps rl_screensreal's layer (vertical later).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { cueFrame } from '../../timing';
import { clamp, inOutSine, lerp, outCubic } from '../../ease';
import { Seq, SCREENS } from './_lib';
import { Phone } from '../../blocks/real/Phone';
import { UsagePage } from '../../blocks/real/UsagePage';
import { Grain2, SoftPlate, Spill, Vig, hand } from '../../blocks/real/Scene';

/** pull-to-refresh 0..1 around each stressed "try": drag in over 7 frames, hold + spin, snap back */
const pullAt = (f: number, cues: number[]) => {
  let p = 0;
  for (const c of cues) {
    const d = f - c;
    if (d >= -7 && d < 0) p = Math.max(p, outCubic((d + 7) / 7));
    else if (d >= 0 && d < 9) p = Math.max(p, 1);
    else if (d >= 9 && d < 15) p = Math.max(p, 1 - outCubic((d - 9) / 6));
  }
  return p;
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const cues = [cueFrame(shot, 'refresh 1') ?? 15, cueFrame(shot, 'refresh 2') ?? 33, cueFrame(shot, 'refresh 3') ?? 52];
  const pull = pullAt(f, cues);
  const k = lerp(3.45, 4.0, inOutSine(clamp(f / (shot.dur - 1))));          // stage px per iOS point (the push in)
  const focusPt = lerp(250, 228, inOutSine(clamp(f / (shot.dur - 1))));      // the page point at frame centre
  const h = hand(f, 1, 11);
  const cx = 1280 + h.x, cy = 720 + (426 - focusPt) * k + h.y + pull * 10;
  return (
    <AbsoluteFill>
      <SoftPlate x={-h.x * 0.4} y={-h.y * 0.4} />
      <Spill cx={1280} cy={700} r={1500} k={0.12} />
      <Phone cx={cx} cy={cy} w={393 * k} rot={-1.2 + h.r} time="2:08" glare={0.07} silent>
        <UsagePage resetsIn="Resets in 3 hr 52 min" reachedAt="2:01 AM" pull={pull} spin={f / 9} updated={f > cues[0] ? 'just now' : 'less than a minute ago'} />
      </Phone>
      <Vig k={0.38} />
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
const [A, B] = SCREENS.phone_3C;
const Screen: React.FC<ShotProps> = ({ shot, fmt }) => {
  const g = shot.from + useCurrentFrame(); if (fmt !== '9x16') return null;
  return <AbsoluteFill style={{ background: '#000' }}><Seq dir="seca/screens/phone_3C_9x16" g={g} first={A} last={B} w={1080} h={1920} /></AbsoluteFill>;
};
export const S3_3C: ShotDef = { stage: Stage, screen: Screen, cx916: () => 0.5 };
