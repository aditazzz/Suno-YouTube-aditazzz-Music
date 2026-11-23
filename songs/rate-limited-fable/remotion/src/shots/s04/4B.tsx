// 4B "Tried incognito": open on the cat on the door frame, in disguise (a moustache), then tilt down to the door: him behind
// the glass with the paddle DOWN, her at the glass. Her side goes dark mode (beat 2); he holds the look one beat; on beat 4
// the paddle comes up (two smear frames + camera hit). Every scheme ends on the same calm paddle.
// PLATE: rl_cut1 a1 = S10 D5 (5760x5376: the approved Rain door at 2x with the headroom: ledge + cat) + D4_region (paddle
// down) + cat_moustache_region; the dark mode darkens outside layout.door_glass_corners (the lobby through the glass stays lit)
// and her (right of the glass edge). The code paper moustache is gone: the cat wears it.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { lerp, inOutCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, ez, gb, hit, MBlur, pulse } from '../s03/_lib';
import { A1, Lay, clampCam, c916f, K5, D5_TOP, D5_H, d5 } from '../s03/_cut1a';

const HIM = { x: 2108 * K5, y: 1751 * K5 + D5_TOP, w: 1920 * K5, h: 3288 * K5 };   // layout.him_box (D4_region, d5_padup)
const CAT = { x: 1820 * K5, y: D5_TOP, w: 1534 * K5, h: 1958 * K5 };                // layout.cat_region
const GLASS = [[1167.6, 1029.2], [4526.5, 1298.4], [4380.7, 4876.5], [1339.1, 5102.6]].map(([x, y]) => d5(x, y));
const CAT_X = 924, PAD_X = 1520;                                                    // 9:16 subjects: the cat's face, him + paddle
// rl_fix2_end (the watch: "no paper moustache is visible (nor on the cat)"): it opens CLOSE on the cat's face (3.2x, the
// moustache ~90 px; the cat layer is the native-res region now, public/fix2/end/d5_cat_hi.png), holds 8 frames, then pulls back and
// tilts down to the door in one move.
// rl_cut4 (one cat): THE cat from L4's 11E plate (same scene + camera) over the ledge, its tail matted over the lit lobby, the old toy
// cat and its tail cleaned (workers/rl_cut4/fix4b_cat.py -> public/c4/4B_cat.png, D5 px 1450..3750 x 0..1950). No moustache on it now: her
// moustache carries 'incognito'. The open frames THE cat's face.
const CAT4 = { x: 1450 * K5, y: D5_TOP, w: 2300 * K5, h: 1950 * K5 };
const FACE = d5(1850, 360);
// rl_fix2_herrig (Nov 16; the watch: "her back is to camera, and no paper moustache is visible"): HER, turned from the glass toward the
// camera's left in the approved squat, a black handlebar moustache on a stick held to her upper lip with her left hand, a sly sideways look
// to camera (decide-epic: from this camera a face turned to him would be the back of her head). Region renders over D5 from the same scene
// (build/stills/F2H_4B), matted to her (old + new silhouette) so his paddle and its smear outside her still come from the layers below.
const FACE4B = [1870, 575];                                                                          // her face + the moustache (F2H_4B layout, stage px)
const HER = { x: 2891 * K5, y: 2016 * K5 + D5_TOP, w: 2869 * K5, h: 3360 * K5 };                 // F2H_4B layout.region (rl_l1_roll approved look; rl_cut4_prep re-matted, d5_her.json)
const cam = (t: number, f: number, dur: number) => ({ cx: lerp(FACE[0], lerp(1560, 1600, f / dur), t), cy: lerp(FACE[1], 700, t), s: lerp(3.2, 1.12, t) });

const Dark: React.FC<{ k: number }> = ({ k }) => {
  const poly = GLASS.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <svg width={2560} height={2560} viewBox={`0 ${D5_TOP} 2560 2560`} style={{ position: 'absolute', left: 0, top: D5_TOP }}>
        <defs><linearGradient id="dk4b" x1="0" x2="1" y1="0" y2="0"><stop offset="0.85" stopColor="rgb(5,6,10)" stopOpacity="0" /><stop offset="0.93" stopColor="rgb(5,6,10)" stopOpacity="0.62" /></linearGradient>
          {/* rl_fix2_herrig: her face + moustache stay lit (the lobby light through the glass), so the disguise reads under dark mode */}
          <radialGradient id="hole4b"><stop offset="0.45" stopColor="black" stopOpacity="1" /><stop offset="1" stopColor="black" stopOpacity="0" /></radialGradient>
          <mask id="m4b" maskUnits="userSpaceOnUse" x="0" y={D5_TOP} width="2560" height="2560"><rect x="0" y={D5_TOP} width="2560" height="2560" fill="white" />
            <ellipse cx={FACE4B[0]} cy={FACE4B[1]} rx={330} ry={270} fill="url(#hole4b)" /></mask></defs>
        <g mask="url(#m4b)">
          <path d={`M0,${D5_TOP} H2560 V1440 H0 Z M${poly.replace(/ /g, ' L')} Z`} fillRule="evenodd" fill="rgba(5,6,10,0.76)" />
          <polygon points={poly} fill="url(#dk4b)" />
        </g>
      </svg>
    </AbsoluteFill>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const t0 = 8, t1 = gb(shot, 1) + 4;                                  // the tilt down lands just after beat 2
  const dark = ez(f, gb(shot, 1) + 2, gb(shot, 1) + 7);
  const up = gb(shot, 3);                                              // the paddle comes up on beat 4
  const smear = f === up ? [150, 100, 55] : f === up + 1 ? [45, 20, 0] : [];
  const d4 = f < up ? 1 : f === up ? 0.55 : 0;
  const moving = f > t0 && f < t1;
  return (
    <MBlur n={moving ? 6 : 1} shutter={0.5} render={(dt) => {
      const c0 = cam(inOutCubic(ez(f + dt, t0, t1, (x) => x)), f, shot.dur);
      const s = c0.s * (1 + pulse(g) + hit(f, up, 0.014, 10));
      const c = clampCam(c0.cx, c0.cy, s, 0, 2560, D5_TOP, 1440);
      return (
        <Cam cx={c.cx} cy={c.cy} s={s} free>
          <Lay src={A1.D5} x={0} y={D5_TOP} w={2560} h={D5_H} />
          <Lay src="c4/4B_cat.png" x={CAT4.x} y={CAT4.y} w={CAT4.w} h={CAT4.h} />{/* rl_cut4: THE cat (was the old toy cat) */}
          {d4 > 0 ? <Lay src={A1.D5d4} x={HIM.x} y={HIM.y} w={HIM.w} h={HIM.h} style={{ opacity: d4 }} /> : null}
          {smear.map((dy, i) => (
            <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}><Lay src={A1.D5padup} x={HIM.x} y={HIM.y + dy} w={HIM.w} h={HIM.h} /></AbsoluteFill>
          ))}
          <Lay src={d4 > 0.5 ? 'fix2/herrig/d5_her_dn.png' : 'fix2/herrig/d5_her_up.png'} x={HER.x} y={HER.y} w={HER.w} h={HER.h} />
          <Dark k={dark} />
        </Cam>
      );
    }} />
  );
};
export const S4_4B: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const t = inOutCubic(ez(f, 8, gb(shot, 1) + 4, (x) => x)); const c0 = cam(t, f, shot.dur); const c = clampCam(c0.cx, c0.cy, c0.s, 0, 2560, D5_TOP, 1440);
  return c916f(lerp(CAT_X, PAD_X, t), c.cx, c0.s); } };
