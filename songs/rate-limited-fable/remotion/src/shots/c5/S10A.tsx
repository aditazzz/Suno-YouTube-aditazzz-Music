// 10A (cut 5; plan §3/§6: f4836-4975; N47, OV, C11): her phone, the same thread as 1G ("Help writing a song"): the whole night, one
// request per beat, all stay. Lines 1-2 (+ his "Sure, let's go!") are there at the cut; then 3 (4853), 4 (4870), 5 (4888), 6 (4905),
// 7 (4923, the biggest landing: "Can you retire me?! I'm exhausted"); his one reply "You're absolutely right." types from 4940 and
// holds; a 12-frame pull-out toward 10B to the cut (her N47: "make sure it stays long enough to be readable. No need to hammer
// you're absolutely right"). The thread scrolls up as each lands, so the newest five always read.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { MobileChat5 } from './AppField';
import { Msg } from '../../blocks/real/ClaudeChat';
import { ABS_RIGHT, CHIP, LADDER } from '../../blocks/real/script';
import { PhoneStage, clamp, ez, lerp, loc, pop } from './kit';

export const A10 = { LINES: [4853, 4870, 4888, 4905, 4923], REPLY: 4940, PULL: 12 };

/** the thread at local frame f. lines[i] = when request i+3 lands */
export const thread10A = (f: number, lines: number[], reply: number): Msg[] => {
  const m: Msg[] = [{ who: 'user', text: LADDER[0].her }, { who: 'claude', text: LADDER[0].claude! }, { who: 'user', text: LADDER[1].her }];
  lines.forEach((at, i) => { if (f >= at) m.push({ who: 'user', text: LADDER[i + 2].her }); });
  if (f >= reply) m.push({ who: 'claude', text: ABS_RIGHT, chars: ((f - reply) / 30) * 40 });
  return m;
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const lines = A10.LINES.map((F) => loc(shot, F)); const reply = loc(shot, A10.REPLY);
  const msgs = thread10A(f, lines, reply);
  // the newest bubble springs up from below (the thread is bottom-anchored: a landing lifts everything by its height)
  const lastAt = Math.max(...[0, ...lines, reply].filter((x) => f >= x));
  const lift = (1 - clamp(pop(f, lastAt, 8))) * 46;
  // line 7: the biggest landing (a small punch on the phone, settling)
  const l7 = lines[4]; const punch = f >= l7 ? 0.035 * Math.exp(-(f - l7) / 6) * Math.cos((f - l7) / 2.2) : 0;
  // the pull-out toward 10B over the last 12 frames: the phone recedes and darkens into her room
  const pull = ez(f, shot.dur - A10.PULL, shot.dur - 1);
  return (
    <AbsoluteFill style={{ transform: `scale(${1 + punch})` }}>
      <PhoneStage f={f} dur={shot.dur} k0={3.0} k1={lerp(3.08, 2.2, pull)} focus0={590} focus1={lerp(590, 470, pull)} time="4:50" seed={31} rot={-0.6}>
        <MobileChat5 title="Help writing a song" msgs={msgs} scroll={lift}
          field={{ banner: true, disabled: true, model: CHIP.night, placeholder: 'Reply to Claude' }} />
      </PhoneStage>
      <AbsoluteFill style={{ background: '#0b0806', opacity: 0.55 * pull }} />
    </AbsoluteFill>
  );
};
export const C5_10A: ShotDef = { stage: Stage, cx916: () => 0.5 };
