// 9C "There was anything else!" (cut 4, lane L2; her #22/#23 notes): mid-squat on the jiggling plate she shoves her phone at us, indignant;
// then the insert: her phone, big: the real Claude input, and on each beat of "there was anything else" another Pasted text card stacks up
// (L3's PastedPileScreen, 1..9) until the pile pushes the input off the top. Behind it, her (the same plate) soft and shaking.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../s07/_lib';
import { Phone } from '../../blocks/real/Phone';
import { PastedPileScreen, chipsAt } from '../../blocks/real/Dropins';
import { PlateJiggle, beat, settle, jiggleSamples } from '../l2kit';
import { L2Q } from '../l2data';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { Img, staticFile } from 'remotion';
import { clamp, inOutSine, lerp, outCubic } from '../../ease';

/** rl_cut4 (the watch: "empty phone screens"): her phone in the 9C still is a blank lit panel; her Claude chat (the limit banner, his
 *  last reply: L3's screen with no cards yet) pinned on it, masked to the screen's own pixels (her fingers stay in front), riding the
 *  plate's jiggle. Used by 9C (before the insert) and 9D. Mask: workers/rl_cut4/phonemask9c.py -> public/c4/9C_phonemask.png. */
export const PhoneScreen9C: React.FC<{ g: number; amp: number }> = ({ g, amp }) => {
  const q = L2Q['9C']?.phone as Quad | undefined; if (!q) return null;
  const mask = `url(${staticFile('c4/9C_phonemask.png')})`;
  return (
    <AbsoluteFill>
      {jiggleSamples('9C', g, amp).map(({ dx, dy, op }, i) => (
        <AbsoluteFill key={i} style={{ opacity: op, transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)`,
          WebkitMaskImage: mask, maskImage: mask, WebkitMaskSize: '2560px 1440px', maskSize: '2560px 1440px', WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat' } as React.CSSProperties}>
          <ScreenInsert corners={q} w={393} h={852} light={0.86}><PastedPileScreen n={0} /></ScreenInsert>
        </AbsoluteFill>
      ))}
    </AbsoluteFill>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const b1 = beat(shot, 1, 17); const ins = f >= b1;
  if (!ins) {
    const k = inOutSine(clamp(f / b1));
    return <Cam cx={1280} cy={720} s={lerp(1.0, 1.05, k)}><PlateJiggle id="9C" g={g} amp={5.5} /><PhoneScreen9C g={g} amp={5.5} /></Cam>;
  }
  const span = shot.dur - b1 - 6; const beats = Array.from({ length: 9 }, (_, i) => b1 + 2 + Math.round((i * span) / 9));
  const n = chipsAt(f, beats); const e = outCubic(clamp((f - b1) / 6));
  const shake = (a: number) => 3 * a * Math.sin(2 * Math.PI * 13.5 * (g / 30));
  return (
    <AbsoluteFill>
      <Cam cx={1280} cy={720} s={1.18 * (1 + settle(f, b1, 0.02))}>
        <AbsoluteFill style={{ filter: 'blur(14px) brightness(0.72)' }}><PlateJiggle id="9C" g={g} amp={5.5} /></AbsoluteFill>
      </Cam>
      <Phone cx={1280 + shake(0.6)} cy={lerp(1900, 330, e) + shake(1)} w={1150} rot={-2 + 2 * (1 - e)} time="4:41" fit>      {/* L3: >= ~1100 px wide so the PASTED tags read; we see its lower half, where the pile grows */}
        <PastedPileScreen n={n} />
      </Phone>
    </AbsoluteFill>
  );
};
export const S9_9C: ShotDef = { stage: Stage, cx916: () => 0.5 };
