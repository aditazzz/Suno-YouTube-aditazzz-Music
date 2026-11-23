// 5H "Don't leave me on read like this": close on him behind the glass; the glass is a screen between them.
// rl_fix2_read (Nov 16, WATCH 5H blocker: her three messages were tiny pills in a corner): the messages are on the glass at real
// size (about a third of the frame), and the focus racks from him to the glass as the first one pops on the drum roll:
// Quick question. / It's small. / It's a font. -> Delivered -> Read 3:59 AM on the roll end, the lobby clock turning over with it.
// PLATE: S8 C1 (clean close, final) + code clock + the glass bezel. The old glass_5H layer (tiny bubbles) is dropped.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutCubic } from '../../ease';
import { cueFrame } from '../../timing';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, P, LobbyClock } from '../s03/_lib';
import { GlassMsgs, Msg } from './_fix2_glass';

const msgs = (c: number[]): Msg[] => [{ text: 'Quick question.', at: c[0] }, { text: "It's small.", at: c[1] }, { text: "It's a font.", at: c[2] }];
const cues = (shot: any) => [cueFrame(shot, 'q1') ?? 19, cueFrame(shot, 'q2') ?? 36, cueFrame(shot, 'q3') ?? 53, cueFrame(shot, 'roll end') ?? 66];
const local = (shot: any) => (shot.cues ?? []).length >= 4 ? (shot.cues as any[]).slice(0, 4).map((c) => c.frame - shot.from) : cues(shot);
const rack = (f: number, a: number) => inOutCubic(clamp((f - (a - 6)) / 9));       // focus pulls to the glass as the first message lands

const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const c = local(shot); const end = c[3];
  const s = lerp(1.06, 1.0, inOutCubic(clamp(f / (end - 1))));
  const k = rack(f, c[0]);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: k > 0.01 ? `blur(${(6 * k).toFixed(2)}px) brightness(${(1 - 0.12 * k).toFixed(3)})` : undefined }}>
        <Cam s={s} cx={1300} cy={700}>
          <PlateImg src={P.C1} />
          <LobbyClock text={f >= end ? '3:59' : '3:58'} />
        </Cam>
      </AbsoluteFill>
      {fmt === '16x9' ? (
        <>
          <GlassMsgs f={f} msgs={msgs(c)} receipt={[{ text: 'Delivered', at: c[2] + 5 }, { text: 'Read 3:59 AM', at: end }]} right={1700} top={300} size={92} blur={2.2 * (1 - k)} />
          <Img src={staticFile('seca/screens/bezel_16x9.png')} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
        </>
      ) : null}
    </AbsoluteFill>
  );
};
// 9:16: the messages in the safe zone (under the top 13%, ending above half height, clear of the like column)
const Screen: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); if (fmt !== '9x16') return null;
  const c = local(shot); const k = rack(f, c[0]);
  return (
    <AbsoluteFill>
      <GlassMsgs f={f} msgs={msgs(c)} receipt={[{ text: 'Delivered', at: c[2] + 5 }, { text: 'Read 3:59 AM', at: c[3] }]} right={958} top={300} size={64} blur={1.5 * (1 - k)} />
      <Img src={staticFile('seca/screens/bezel_9x16.png')} style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1920 }} />
    </AbsoluteFill>
  );
};
export const S5_5H: ShotDef = { stage: Stage, screen: Screen, cx916: () => 0.5 };
