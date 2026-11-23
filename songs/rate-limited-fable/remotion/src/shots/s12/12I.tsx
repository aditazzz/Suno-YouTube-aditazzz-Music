// 12I "Don't leave me on read like this" (cut 4, rl_l3_ui; her note #30 "Clock is a key thing ... Rolex panda even on the wall clock.
// Time should be easy to see"; §2a; S22 the lobby stays dim until 6:00): very close on the lobby's panda wall clock, dead still.
// The red chronograph hand climbs the last seconds, one tick per clap (measured cues): 5:59:54 .. :59; each tick overshoots and
// settles in 3 frames. The minute hand sits a hair before twelve; on the last frame (the downbeat, the cut to 13A) the chrono hand
// reaches twelve and the minute hand clicks onto it: 6:00. The lobby is still dimmed (he dimmed it at 11C).
// Plate: S21t T27 (the wall and its light; the old gold face is covered by the panda, r +8% over its rim).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { ClockWall, T27_CLOCK } from './12F';
import { PandaClock, pt } from '../../blocks/PandaClock';
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const ticks = (shot.cues ?? []).filter((c) => !/twelve/.test(c.cue)).map((c) => c.frame - shot.from);
  const n = ticks.filter((t) => f >= t).length; const last = ticks[n - 1] ?? -99;
  const d = f - last; const over = n > 0 && d < 3 ? [0.3, -0.14, 0.05][d] : 0;
  const end = f >= shot.dur - 1;
  const sec = end ? 0 : 53 + n + over;
  const time = end ? pt(6, 0) : pt(5, 59, 0) + 0.0;            // the minute hand rests on :59 until the click
  const { cx, cy, r } = T27_CLOCK;
  return (
    <AbsoluteFill>
      {/* rl_cut4_fix (rl_watch4 12I: 3.4 s with almost no motion read as a freeze): a slow push in on the dial, 1.55 -> 1.68 */}
      <Cam cx={cx} cy={cy} s={lerp(1.55, 1.68, inOutSine(clamp(f / (shot.dur - 1))))}>
        <ClockWall />
        <div style={{ position: 'absolute', left: cx - r * 1.08 + r * 0.05, top: cy - r * 1.08 + r * 0.08, width: r * 2.16, height: r * 2.16, borderRadius: '50%',
          background: 'rgba(40,26,14,0.45)', filter: `blur(${r * 0.06}px)` }} />
        <PandaClock cx={cx} cy={cy} r={r * 1.08} time={time} chrono={sec} running={sec} variant="wall" light={0.86} shadow={0} uid="t27" />
      </Cam>
      {/* the lobby is dimmed (11C): a cool, low wash over everything but the dial's centre */}
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 60% 70% at 50% 50%, rgba(10,14,24,0) 40%, rgba(10,14,24,0.45) 100%)' }} />
    </AbsoluteFill>
  );
};
export const S12_12I: ShotDef = { stage: Stage, cx916: () => 0.5 };
