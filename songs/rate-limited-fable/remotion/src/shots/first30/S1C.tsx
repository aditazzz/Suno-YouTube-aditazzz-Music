// 1C, the drop (first30.md): the first dead-level symmetrical frame, the top row of forty windows each lit with its small x;
// the camera falls down the centre line like a lift letting go, motion-blurred at speed, and lands on "terminal" with a
// 1% overshoot, a 3-frame bounce and a settle, on the one door and its brass plate. Plate NS2 when it lands
// (placeholder: the graded dawn street, which is three-quarter, not flat-on).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { TextBox } from '../../blocks/Type';
import { Cam, MBlur } from './kit';
import { NightStreet, STREET } from './street';
import { tailTheta } from './S1AB';
import { cueFrame } from '../../timing';

const S = 2.35;
const camC = (f: number, land: number) => {
  const top = 330, bottom = 1105;
  if (f <= land) { const k = Math.max(0, f) / land; return { cy: lerp(top, bottom, Math.pow(k, 2.4)), s: S }; }
  const d = f - land; const ov = 14 * Math.exp(-d / 3.2) * Math.cos((d / 3) * Math.PI);   // 1% overshoot + bounce
  return { cy: bottom + ov, s: S };
};

export const BrassPlate: React.FC = () => {
  const d = STREET.door;
  return (
    <TextBox x={d.x + d.w / 2 - 175} y={d.y - 64} w={350} h={54} size={34} kind="head" pad={7} radius={6} align="center" color="#2b1d0c"
      bg="linear-gradient(180deg,#e7c77d 0%,#b98c3e 55%,#8f6a2a 100%)" style={{ boxShadow: '0 3px 8px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,240,200,0.6)' }}>
      1 TERMINAL PLACE
    </TextBox>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const land = cueFrame(shot, 'terminal') ?? 51;
  const v = Math.abs(camC(f + 0.5, land).cy - camC(f - 0.5, land).cy) * S;
  return (
    <MBlur n={v > 8 ? 7 : 1} shutter={0.6} render={(dt) => {
      const c = camC(f + dt, land);
      return (
        <Cam cx={1293} cy={c.cy} s={c.s}>
          <NightStreet g={g} win={() => ({ lit: 1 })} sign={1} signLight={1} clockMin={480 + (g - 216) / 30 / 60}
            tailAngle={(u) => tailTheta(g - 3 * u)} xmarks parcels={[(f - 30) / 18]} />
          <BrassPlate />
        </Cam>
      );
    }} />
  );
};

// v3: the real flat-on NS2 tall plate (stage 2560 x 3840). Dead-level and symmetrical; the frame is 2560 plate px wide at the
// landing (s 2.25, so 1 TERMINAL PLACE in brass reads at 34+ px), starting on the top row of lit windows under the sign and
// falling down the centre line (accelerating like a lift letting go, shutter blur scaled to the speed), landing on
// "terminal" on the door and its address with the same 1% overshoot and 3-frame bounce. The address is in the render.
import { HAVE_NS2T, K2T, NS2TScene, NS2T_PH } from './ns';
const S2 = 2.25;
// rl6_edit (FRAMES blocker 12): 1C no longer starts a second drop from the top row. It picks up 1B's fall already moving (mid-facade, fast,
// blurred) and eases it out into the door: decelerating (out-power 2.5) to land on LAND6 (frame 250, the beat at 251), then a held frame on
// the door and `We ship worldwide` to the cut (36 frames, 'terminal' sung at 267 inside the hold) with a slow 1.5% creep so it isn't frozen.
export const LAND6 = 34;
const camC2 = (f: number, _land: number) => {
  const start = 4500 * K2T, bottom = 7390 * K2T - 44;   // 7390: the ShipIt awning sign whole in the hold (FRAMES 1C weak); rl7_ra -44: it was still cut at the top (PLAN7 row 2)
  if (f <= LAND6) { const k = Math.max(0, f) / LAND6; return lerp(start, bottom, 1 - Math.pow(1 - k, 2.5)); }
  return bottom;
};
const s2At = (f: number) => S2 * (1 + 0.015 * Math.max(0, Math.min(1, (f - LAND6) / 36)));
const StageNS: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const land = cueFrame(shot, 'terminal') ?? 51;
  const v = Math.abs(camC2(f + 0.5, land) - camC2(f - 0.5, land)) * S2;
  const n = v > 120 ? 11 : v > 40 ? 9 : v > 8 ? 7 : 1;
  return (
    <MBlur n={n} shutter={0.6} render={(dt) => (
      <Cam cx={1280} cy={camC2(f + dt, land)} s={s2At(f + dt)} ph={NS2T_PH}>
        <NS2TScene clockMin={480 + (g - 216) / 30 / 60} />
      </Cam>
    )} />
  );
};
export const S1_1C: ShotDef = HAVE_NS2T ? { stage: StageNS, cx916: () => 0.5 } : { stage: Stage, cx916: () => 1293 / 2560 };

