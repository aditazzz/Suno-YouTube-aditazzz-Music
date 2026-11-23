// 6D "No, I'll wait": on the clap (beat 2) the neon stutters and re-lights as its SECOND wording; on the silent last beat the clock
// turns to 4:00 (his side, off this frame now).
// rl_fix2_robot (WATCH blocker: 6D was 2E/6A's still wide again, and its dropped letters "Log O f" read as a broken sign): a new
// picture, pushed in on her side - her upside-down stand against the glass and the neon over the sofa - and the neon's second wording
// is now a real one: "Live Laugh / Log Off" stutters (the dark-tube flicker region) and lands on "Live Laugh / Log On" (her answer to
// "No, I'll wait"; a sign-only region render of the same sign, blroom RL_SIGN, placed by matching the unchanged "Live Laugh" line).
// Plate FX.B2B (him in the new seat, at the left edge of this frame).
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, SignRegion, pulse } from '../s03/_lib';
import { lerp } from '../../ease';
import { ClockOnWall } from './_clock';
import { FX, SIGN_ON_BOX } from '../s11/_fix2';

const flick = (d: number) => (d < 0 ? 0 : d < 2 ? 1 : d < 3 ? 0 : d < 5 ? 1 : d < 6 ? 0.3 : 0);     // the dark-tube state, stuttering
const onA = (d: number) => (d < 5 ? 0 : d < 6 ? 0.45 : d < 7 ? 0.15 : d < 9 ? 0.8 : 1);             // "Log On" catching, then lit
// rl_cut4_prep (Nov 17): FX.B2B is now rl_l1_roll's approved room, but plates/sign_flicker.jpg and fix2/robot/sign_log_on.jpg are region
// renders of the OLD room (white wall) and show as a pale blob on it. Off until rl_l1_roll renders both regions on the new room (same
// B2B camera; then set this true and re-measure SIGN_REGION.flicker / SIGN_ON_BOX).
const OLD_ROOM_SIGN_REGIONS = false;
const MASK = 'radial-gradient(ellipse 48% 46% at 50% 50%, #000 70%, transparent 100%)';
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const clap = ((shot.cues ?? []).find((c) => c.word === 'clap')?.frame ?? shot.from + 18) - shot.from;
  const four = ((shot.cues ?? []).find((c) => c.word === 'beat 4')?.frame ?? shot.from + 52) - shot.from;
  const m = f >= four ? 4 * 60 : 3 * 60 + 59;
  const k = f / shot.dur; const d = f - clap;
  return (
    <Cam cx={lerp(1440, 1470, k)} cy={lerp(575, 560, k)} s={lerp(1.38, 1.46, k) * (1 + pulse(g))}>
      <PlateImg src={FX.B2B} />
      {OLD_ROOM_SIGN_REGIONS ? <SignRegion which="flicker" opacity={flick(d)} /> : null}
      {OLD_ROOM_SIGN_REGIONS && onA(d) > 0 ? <Img src={staticFile(FX.SIGN_ON)} style={{ position: 'absolute', left: SIGN_ON_BOX.x, top: SIGN_ON_BOX.y, width: SIGN_ON_BOX.w, height: SIGN_ON_BOX.h,
        opacity: onA(d), WebkitMaskImage: MASK, maskImage: MASK }} /> : null}
      <ClockOnWall minutes={m} secs={f >= four ? 0 : 52 + Math.floor(f / 8.7) % 8} />
    </Cam>
  );
};
export const S6_6D: ShotDef = { stage: Stage, cx916: () => 0.56 };   // 9:16: the neon over her (neon centre stage ~1610 -> output ~0.56)
