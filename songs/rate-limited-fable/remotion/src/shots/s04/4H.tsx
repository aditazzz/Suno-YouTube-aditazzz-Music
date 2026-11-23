// 4H "Who else you up with at 2 a.m.? / Who else you calling 'great question'?": her view, long lens. Focus travels past his
// soft head to the intercom (7C, 2A, 5F light, one per beat), then the camera tilts down to the stamp rack: the worn
// GREAT QUESTION stamp.
// PLATE (rl_cut1 a2): S21d T11 (tall 2880x2700 = 2560x2400 on the stage). The focus pull is a crossfade T11_near -> T11_far
// (no code blur); the code tags and stamp rack are gone (baked). The three lit lamps are covered with their unlit neighbour's
// pixels until their beat; the clock's 2:51 is code on the plate's blank face.
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutCubic } from '../../ease';
import { FONT } from '../../theme';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { ShotDef, ShotProps } from '../types';
import { gb, keys, pulse, c916, MBlur, W } from '../s03/_lib';
import { IMG, LAY, K, CamT, quadSt, st } from '../s05/_cut1b';

const PH = 2700 * K;                                                   // plate height on the stage (2400)
const LIT: [string, string][] = [['7C', '7D'], ['2A', '2B'], ['5F', '5E']];   // lit lamp, unlit neighbour (same row)
const R = 38 * K;                                                     // patch radius (lamp ~20 px sharp, ~28 px soft)
const CLOCK = quadSt(LAY.T11.clock);
const GQ = LAY.T11.great_question.stamp as number[];

/** one focus state: the plate, the unlit patches (fade out on their beat), a bloom as each lamp comes on, the clock */
const Focus: React.FC<{ n: 'T11_far' | 'T11_near'; on: number[]; blur: number; opacity: number }> = ({ n, on, blur, opacity }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: W, height: PH, opacity }}>
    <Img src={staticFile(IMG[n].src)} style={{ position: 'absolute', left: 0, top: 0, width: W, height: PH }} />
    {LIT.map(([lit, nb], i) => {
      const [x, y] = st(LAY.T11.lamps[lit]), [xn, yn] = st(LAY.T11.lamps[nb]);
      const k = on[i];
      return (
        <React.Fragment key={lit}>
          <div style={{ position: 'absolute', left: x - R, top: y - R, width: 2 * R, height: 2 * R, opacity: 1 - k, overflow: 'hidden',
            WebkitMaskImage: 'radial-gradient(circle, #000 62%, transparent 100%)', maskImage: 'radial-gradient(circle, #000 62%, transparent 100%)' }}>
            <Img src={staticFile(IMG[n].src)} style={{ position: 'absolute', left: -(xn - R), top: -(yn - R), width: W, height: PH, maxWidth: 'none' }} />
          </div>
          {/* the lamp coming on: a short warm bloom that settles to a faint halo */}
          <div style={{ position: 'absolute', left: x - 3 * R, top: y - 3 * R, width: 6 * R, height: 6 * R, mixBlendMode: 'screen', opacity: k * (0.35 + 0.65 * Math.max(0, 1 - (on[i + 3] ?? 0))),
            background: 'radial-gradient(circle, rgba(255,196,110,0.55) 0, rgba(255,170,80,0.18) 30%, rgba(255,160,70,0) 62%)' }} />
        </React.Fragment>
      );
    })}
  </div>
);

// rl_l3_ui (cut 4, S27 "4H lamps unreadable"; §2a the digital box goes): the focus pull now pushes IN on the intercom panel (2.05x,
// all three lit lamps 7C / 2A / 5F and their tags inside the frame, tags ~60 px at 1440), holds while they light on the beats, then
// pulls back and tilts down to the GREAT QUESTION stamp. The code "2:51" is gone and every framing keeps the old digital box (plate
// x < 513 stage, y 1268-1607) out of frame (opening 1.2x from the right, the stamp end shifted right).
const cam = (t: number, shot: any) => ({
  cx: keys(t, [[0, 1500], [30, 1357], [gb(shot, 4), 1366], [gb(shot, 5) + 6, 1460]], inOutCubic),
  cy: keys(t, [[0, 600], [30, 590], [gb(shot, 4), 596], [gb(shot, 5) + 6, 1880]], inOutCubic),
  s: keys(t, [[0, 1.2], [30, 2.05], [gb(shot, 4), 2.1], [gb(shot, 5) + 6, 1.36], [shot.dur, 1.4]]),
});
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const focus = keys(f, [[0, 0], [12, 0], [30, 1]]);                           // 0 = on his head (near), 1 = on the intercom (far)
  const moving = (f > 2 && f < 34) || (f > gb(shot, 4) && f < gb(shot, 5) + 6);
  // lamp k (0 off .. 1 on, a two-step flicker), then the bloom decay (index +3)
  const on = LIT.map((_, i) => { const d = f - gb(shot, 1 + i); return d < 0 ? 0 : d < 1 ? 0.7 : d < 2 ? 0.2 : 1; });
  const decay = LIT.map((_, i) => clamp((f - gb(shot, 1 + i) - 2) / 10));
  const lamps = [...on, ...decay];
  const stamp = clamp((f - gb(shot, 6)) / 6) * (1 - 0.4 * clamp((f - gb(shot, 6) - 10) / 14));
  const [sx0, sy0] = st([GQ[0], GQ[1]]), [sx1, sy1] = st([GQ[2], GQ[3]]);
  return (
    <MBlur n={moving ? 5 : 1} shutter={0.6} render={(dt) => {
      const c = cam(f + dt, shot);
      return (
        <CamT cx={c.cx} cy={c.cy} s={c.s * (1 + pulse(g))} ph={PH}>
          <Focus n="T11_near" on={lamps} blur={5} opacity={1} />
          <Focus n="T11_far" on={lamps} blur={1.5} opacity={focus} />
          {/* the worn GREAT QUESTION stamp catches the light on its beat (a soft warm pass, nothing clips) */}
          <div style={{ position: 'absolute', left: sx0 - 120, top: sy0 - 80, width: sx1 - sx0 + 240, height: sy1 - sy0 + 160, mixBlendMode: 'screen', opacity: stamp,
            background: 'radial-gradient(ellipse 50% 50% at 50% 50%, rgba(255,214,150,0.32), rgba(255,200,130,0) 70%)' }} />
        </CamT>
      );
    }} />
  );
};
// 9:16: the crop follows the lamp that lights (7C, 2A, 5F), then the stamp
export const S4_4H: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const c = cam(f, shot); const L = LAY.T11.lamps;
  const x = keys(f, [[0, 1700], [34, 1356], [gb(shot, 1), L['7C'][0] * K], [gb(shot, 2), 1200], [gb(shot, 3), 1450], [gb(shot, 4), 1356], [gb(shot, 5) + 6, 1203]], inOutCubic);
  return c916(x, c.cx, c.s);
} };
