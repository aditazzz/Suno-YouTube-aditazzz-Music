// 3C (cut 5; plan §3: f1330-1451, 4 s; N11, C03): her phone, Settings > Usage. On each stressed "try" she pulls to refresh
// (1345/1363/1382): the spinner, the page snaps back, nothing changes. Then, after the third, the one thing that changes: the
// countdown ticks 3 hr 52 min -> 3 hr 51 min (1401). The phone enters by a pull-in from below (her hand bringing it up), then a
// slow drift. Page copy as cut 4e (built from public screenshots of the Settings > Usage page: "Plan usage limits", "Current
// session", "Resets in ...", the weekly rows, "Last updated"); her own screenshot would let us match it exactly (§1b ask).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { outCubic } from '../../ease';
import { UsagePage } from '../../blocks/real/UsagePage';
import { PhoneStage, clamp, ez, loc } from './kit';

export const C3 = { REFRESH: [1345, 1363, 1382], TICK: 1401 };

/** pull-to-refresh 0..1 around each refresh cue: drag in over 7 frames, hold + spin, snap back */
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

export const Screen3C: React.FC<{ f: number; cues: number[]; tick: number }> = ({ f, cues, tick }) => {
  const pull = pullAt(f, cues);
  return (
    <UsagePage resetsIn={f >= tick ? 'Resets in 3 hr 51 min' : 'Resets in 3 hr 52 min'} reachedAt="2:01 AM" pull={pull} spin={f / 9}
      updated={f > cues[0] ? 'just now' : 'less than a minute ago'} />
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const cues = C3.REFRESH.map((c) => loc(shot, c)); const tick = loc(shot, C3.TICK);
  const rise = 1 - ez(f, 0, 12, outCubic);                 // the pull-in: the phone comes up from her hand over 12 frames
  return (
    <PhoneStage f={f} dur={shot.dur} k0={3.45} k1={3.9} focus0={250 - 300 * rise} focus1={232} time="2:08" seed={11} rot={-1.2 + 3 * rise}>
      <Screen3C f={f} cues={cues} tick={tick} />
    </PhoneStage>
  );
};
export const C5_3C: ShotDef = { stage: Stage, cx916: () => 0.5 };
export { clamp };
