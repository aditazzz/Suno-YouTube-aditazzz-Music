// 9G "Cool. / Cool, cool, cool." (cut 4, lane L2; S18): on her mat, arms folded, deadpan to the lens; the party has frozen and every guest has
// turned to look at her; on each quick "cool" one group of guests is gone (reverse-pop), until she is alone with the vacuum and the dazed
// Cooper on the sofa. A dead-pan step in on each "cool". Plates: l2/9G + its pop1..3 states (same camera).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../s07/_lib';
import { L2Img } from '../l2kit';
import { LobbyPanda } from '../c4clock';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const c = (shot.cues ?? []).map((q) => q.frame - shot.from).filter((x) => x > 2); const [c1, c2, c3] = [c[0] ?? 17, c[1] ?? 26, c[2] ?? 34];
  const st = f < c1 ? 'src' : f < c2 ? 'pop1' : f < c3 ? 'pop2' : 'pop3';
  // rl_master_fix (rl_watch4d: the step on the first "cool" at f4801 read as a 1-frame jump/glitch in the locked wide; not a chunk-seam bug):
  // each dead-pan step in now eases over 6 f from its cue (inOutSine); the guests still pop on the cue. Was a hard +3.5% snap per cue.
  const ease = (k: number) => { const x = Math.min(1, Math.max(0, k)); return -(Math.cos(Math.PI * x) - 1) / 2; };   // inOutSine: no snap frame
  const steps = ease((f - c1) / 6) + ease((f - c2) / 6) + ease((f - c3) / 6);
  // rl_cut4: a slow creep under the pop steps (the sweep found 41 dead-still frames between them)
  return <Cam cx={1300} cy={700} s={(1.0 + 0.035 * steps) * (1 + 0.025 * f / Math.max(1, shot.dur - 1))}><L2Img id="9G" layer={st as 'src'} /><LobbyPanda id="9G" h={4} m={44} /></Cam>;
};
export const S9_9G: ShotDef = { stage: Stage, cx916: () => 0.5 };
