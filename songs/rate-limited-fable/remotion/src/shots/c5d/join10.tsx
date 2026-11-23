// rl6_edit (FRAMES blocker 4: the 10B -> 11A join was scrambled: the EMPLOYEE wall for 6 frames, a wipe BACK to the 10B wide, a hard cut to the
// wall again, then the two-shot; and 10B's travel hit the plate edge (Cam clamp at cx 820 for s 1.56) and dropped dead at 5057).
// Now ONE travel: 10B is the slow push on the two of them (her "great shot", no clamped travel), its last 12 frames start the camera
// travelling left as the door's dark edge crosses the lens (c5d/edge.tsx, the same move as 3A -> 3B); 11A arrives behind the edge on the
// EMPLOYEE OF THE MONTH wall, still drifting (the world moving right, same speed at the cut), shown ONCE, then the cut to him on beat 2.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit } from '../first30/kit';
import { cueFrame } from '../../timing';
import { Pl, clamp, gl, lerp, pulse } from '../s10/_lib';
import { inOutSine, outBack, outCubic } from '../../ease';
import { FX } from '../s11/_fix2';
import { Breath } from '../s10/10B';
import { CertWall } from '../s11/11A';
import { edgeIn, edgeOut } from './edge';

export const EDGE10 = 12;

const Stage10B: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const push = inOutSine(clamp(f / (shot.dur - 1)));
  const breath = 0.5 - 0.5 * Math.cos((2 * Math.PI * g) / 96);
  return (
    <Cam cx={lerp(930, 905, push)} cy={lerp(925, 935, push)} s={lerp(1.48, 1.54, push) * pulse(g)}>
      <Pl src={FX.H2a} />
      <Breath src={FX.H2a} a={breath} />
      {/* cut 6: the comp'd WallClock is gone; rl6_lobby's plate carries the 3D panda clock (out of frame at this framing) */}
    </Cam>
  );
};
const hw = (s: number) => 1280 / s;
const BASE_10B: ShotDef = { stage: Stage10B, cx916: (f, shot) => {
  const push = inOutSine(clamp(f / (shot.dur - 1))); const s = lerp(1.48, 1.54, push); const cx = Math.min(Math.max(lerp(930, 905, push), hw(s)), 2560 - hw(s));
  return clamp(((865 - cx) * s + 1280) / 2560); } };
export const C5_10B: ShotDef = edgeOut(BASE_10B, EDGE10, -1);

/** cut 6 (rl6_lobby plates, her note "He should be facing her talking towards her ear"): seated (c6/10B seat, = FX.H2a5k via C5PATH) ->
 *  3 frames half up facing camera on the heartbeat (c6/11A/H2a_mid) -> turned to the glass, bent to her ear (c6/11A/H2a_ear). His head in
 *  'ear' is ~(656, 752) stage, eyes ~(720, 816), her face ~(990, 960): the frame lifts only 905 -> 770 and widens 1.84 -> 1.72 (no hard tilt-up), both in. */
const MID11A = 3;
const His11A: React.FC<{ f: number; g: number; cut: number; stand: number }> = ({ f, g, cut, stand }) => {
  const pre = clamp((f - cut) / Math.max(1, stand - cut));
  const rise = outBack(clamp((f - stand) / 9), 1.1);
  const src = f < stand ? FX.H2a5k : f < stand + MID11A ? 'c6/11A/H2a_mid.jpg' : 'c6/11A/H2a_ear.jpg';
  const s = lerp(lerp(1.8, 1.84, clamp((f - cut) / 50)), 1.72, rise);       // a touch wider on the rise: his spikes whole, her face in
  return (
    <Cam cx={1280 / s} cy={lerp(lerp(905, 895, pre), 770, rise)} s={s * (1 + hit(f, stand, 0.015, 12)) * pulse(g)}>
      <Pl src={src} />
    </Cam>
  );
};

/** 11A: the wall (once, drifting right as the camera keeps travelling left, landing SEPTEMBER centre), then the old 11A from beat 2 */
export const make11A = (OLD11A: ShotDef): ShotDef => {
  const Old = OLD11A.stage;
  const Stage: React.FC<ShotProps> = (p) => {
    const f = useCurrentFrame(); const g = p.shot.from + f;
    const cut = gl(p.shot, 2, 35);
    if (f >= cut) return <His11A f={f} g={g} cut={cut} stand={cueFrame(p.shot, 'stands') ?? 52} />;
    return <CertWall slide={outCubic(clamp(f / (cut - 1)))} g={g} dx0={-260} />;
  };
  return edgeIn({ ...OLD11A, stage: Stage }, EDGE10, -1);
};
