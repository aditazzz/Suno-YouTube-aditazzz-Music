// 9A "Okay / I'm not mad / I'm not mad" (cut 4, lane L2; her #21/#22 notes): on the vibration plate in her room, the whole plate and its base in
// frame, the panda on her right wrist, no sunglasses, natural lips, the robe (9A on). Standing jiggle ("Okay", hands on hips, the tight
// "I'm not mad" smile) and squat jiggle (the first "not mad"), alternating on the cues; Cooper braced beside her, bow slipping with the buzz.
// The TV: the approved Outlook headline only (S17). The jiggle is code on the still (§2c): her + Cooper + the plate shake at 13.5 Hz with
// shutter blur, her curls and pom-pom on a lagged layer; it grows on each "I'm not mad".
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { noise1 } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../s07/_lib';
import { PlateJiggle, settle } from '../l2kit';
import { clamp, inOutSine, lerp } from '../../ease';

// kept for 9B (it shakes her phone with the same buzz)
export const jitterAmp = (f: number, m1: number, m2: number) => (f < m1 ? 0.6 : f < m2 ? 1.3 : 2.3);
export const jit = (g: number, a: number): [number, number] => [a * noise1(g * 1.7, 1) * 1.6, a * noise1(g * 1.9, 2) * 1.2];

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const cues = (shot.cues ?? []).map((c) => c.frame - shot.from); const m1 = cues[0] ?? 42, m2 = cues[1] ?? 83;
  const id = f >= m1 && f < m2 ? '9A_squat' : '9A';                                // stand, squat, stand: a cut on each cue
  const amp = f < m1 ? 3.0 : f < m2 ? 5.0 : 7.5;
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  return (
    <Cam cx={lerp(1280, 1420, k)} cy={lerp(720, 700, k)} s={lerp(1.0, 1.07, k) * (1 + settle(f, m1) + settle(f, m2))}>
      <PlateJiggle id={id} g={g} amp={amp} />
    </Cam>
  );
};
export const S9_9A: ShotDef = { stage: Stage, cx916: () => 0.56 };
