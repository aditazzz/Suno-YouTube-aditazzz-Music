// 2A, BACK AT 6:00 (first30.md): the door fills the frame, him soft behind; on the downbeat the little shop sign high on
// the glass flips (scale through zero in 5 frames, shutter blur) to BACK AT 6:00 with its clock hands at six, and swings
// as a damped pendulum (14 degrees, two swings, at rest by ~22.9). The tail hangs into the top of the glass and sways.
// The title picture. Plate D1 (S7) + sign RGBA when they land; this version: door.jpg softened, the sign in code.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp, noise1 } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { TextBox } from '../../blocks/Type';
import { AnalogClock } from '../../blocks/Clock';
import { Cam, PlateImg, pendulum } from './kit';
import { DOOR, GlassSheen } from './door';
import { Tail } from './street';
import { HAVE_S7, Locks7, Plate7, S7, At7 } from './door7';
import { Img, staticFile } from 'remotion';
import { has } from '../c7/kit/trans';
const NEW_D1 = has('c7/2A/D1.jpg');

export const SIGN = { x: 1280, top: 270, w: 700, h: 330, hookY: -20 };
const CREAM = '#e8dec6', INK = '#1f2a2c';

import { PandaSignFace as SignFace } from '../../blocks/PandaClock';
export { SignFace };

export const HangingSign: React.FC<{ f: number; flipAt: number; restBy: number }> = ({ f, flipAt, restBy }) => {
  const k = clamp((f - flipAt) / 5);                         // 0..1 through the flip
  const sx = Math.abs(Math.cos(Math.PI * k));               // scale through zero
  const side = k < 0.5 ? 'open' : 'back';
  const period = (restBy - flipAt) / 2.3;
  const ang = pendulum(f, flipAt + 2, 14, period, 2.0);
  const face = (kk: number) => {
    const sxx = Math.abs(Math.cos(Math.PI * clamp(kk))); const sd = clamp(kk) < 0.5 ? 'open' : 'back';
    return (
      <div style={{ position: 'absolute', left: 0, top: 0, width: SIGN.w, height: SIGN.h, transform: `scaleX(${Math.max(0.02, sxx)})`, filter: `brightness(${0.75 + 0.25 * sxx})` }}>
        <SignFace side={sd as 'open' | 'back'} />
      </div>
    );
  };
  return (
    <div style={{ position: 'absolute', left: SIGN.x, top: SIGN.hookY, width: 0, height: 0, transformOrigin: '0 0', transform: `rotate(${ang.toFixed(3)}deg)` }}>
      <svg width={SIGN.w} height={SIGN.top + 40} style={{ position: 'absolute', left: -SIGN.w / 2, top: 0, overflow: 'visible' }}>
        <path d={`M ${SIGN.w / 2} 0 L ${SIGN.w * 0.2} ${SIGN.top - SIGN.hookY + 12} M ${SIGN.w / 2} 0 L ${SIGN.w * 0.8} ${SIGN.top - SIGN.hookY + 12}`} stroke="#3a3328" strokeWidth={5} fill="none" />
        <circle cx={SIGN.w / 2} cy={4} r={16} fill="#8a8f96" />
      </svg>
      <div style={{ position: 'absolute', left: -SIGN.w / 2, top: SIGN.top - SIGN.hookY, width: SIGN.w, height: SIGN.h }}>
        {k > 0 && k < 1 ? <>{[-0.3, 0, 0.3].map((dt, i) => <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}>{face(k + dt / 5)}</AbsoluteFill>)}</> : face(k)}
      </div>
      {void sx}{void side}
    </div>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const s = lerp(1.06, 1.08, clamp(f / (shot.dur - 1)));
  return (
    <Cam cx={1290} cy={lerp(740, 720, clamp(f / (shot.dur - 1)))} s={s}>
      <PlateImg src={DOOR.plate} filter="blur(5px) brightness(0.92)" />
      <GlassSheen pos={0.62} k={0.8} />
      <Tail pivot={[700, -560]} scale={0.8} angle={(u) => -30 + 3 * Math.sin((g - 4 * u) / 30 * 1.3) + noise1(g / 25, 7)} />
      <HangingSign f={f} flipAt={0} restBy={52} />
    </Cam>
  );
};

// v2 (rl_first30_v2): the real S7 D1 door (shut, three locks locked, the cat on top with its tail hanging into the glass).
// The code sign (the CD's title picture: clock hands at six) hangs from the S7 sign hook at 0.6 scale; the camera sits in
// close (1.70 -> 1.75) so BACK AT 6:00 reads at phone size, him soft behind it. The 3D sign faces (sign_open /
// sign_back_at_6) are plainer and their type is small at this size, so the code sign stays (CD's call to swap).
const SC = 0.6;
const Stage7: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const s = lerp(1.70, 1.75, clamp(f / (shot.dur - 1)));
  const [hx, hy] = S7.signHook;
  return (
    <Cam cx={1280} cy={lerp(650, 640, clamp(f / (shot.dur - 1)))} s={s}>
      {NEW_D1 ? (
        // rl7_ra: P1's re-render (her H7.7 / H7.9: the grey box above the gauge gone, the HOURS AWAKE gauge at its one spot, new logo,
        // chain latched in the render). Only the floor bolt's locked state is laid on (the strip's upper part would cut the moved gauge).
        <>
          <Img src={staticFile('c7/2A/D1.jpg')} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
          <At7 file="lockstrip_s3.png" box={S7.lockBox} style={{ clipPath: 'inset(74% 0 0 0)' }} />
        </>
      ) : <><Plate7 name="D1" /><Locks7 k={3} /></>}
      <div style={{ position: 'absolute', left: 0, top: 0, transformOrigin: '0 0', transform: `translate(${(hx - SIGN.x * SC).toFixed(2)}px, ${(hy - SIGN.hookY * SC).toFixed(2)}px) scale(${SC})` }}>
        <HangingSign f={f} flipAt={0} restBy={52} />
      </div>
    </Cam>
  );
};
export const S2_2A: ShotDef = HAVE_S7 ? { stage: Stage7, cx916: () => 0.5 } : { stage: Stage, cx916: () => 0.5 };
