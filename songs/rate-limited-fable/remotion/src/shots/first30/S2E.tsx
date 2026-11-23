// 2E "You gave me everything / Now you give me nothing" (BOARDS): two rooms, wide, flat-on, a slow slide toward the door. Her
// room stacked with the forty parcels (green ticks), the neon in its first wording. She posts a slip through the mail slot; on
// "nothing" it comes straight back, unstamped. rl_fix2_open: built new (was the animatic default = the same wide as 6A/6D).
//  W1  0-68   S13 T6 (TR_cam_S13, 40 mm, door shut, her squat at the slot): slide 1.06 -> 1.55 from the parcels to the door;
//             the slip sticks out of the slot on her side and slides in (60-66). Lobby clock 2:05 (hands in code).
//  D8  69-95  cut on the beat before "nothing" to the slot close from her side (S21s D8, the flap): the flap is still swinging
//             shut; on "nothing" (cue, f984) it kicks open and the slip shoots straight back out at the lens (motion blur).
//  W2  96-end back on T6, pushed in on her and the slot: the slip slides to rest on the mat at her boots, blank (unstamped).
import React from 'react';
import { PandaClock, pt } from '../../blocks/PandaClock';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp, outCubic, inCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { cueFrame, frameOf, parseClock } from '../../timing';
import { Cam, MBlur, PlateImg, hit } from './kit';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';

const K6 = 2560 / 5760, K8 = 2560 / 2880;
const st6 = (x: number, y: number): [number, number] => [x * K6, y * K6];
const PAPER = 'linear-gradient(180deg,#f1ebdd,#e2d9c5)';

/** the lobby clock in T6 (pivot 1089.4, 741.4; rim r 114.8 S13 px): hands only, the face is in the plate */
const Hands: React.FC<{ minutes: number }> = ({ minutes }) => {
  const [cx, cy] = st6(1089.4, 741.4); const r = 114.8 * K6;
  const h = ((minutes / 60) % 12) * 30, m = (minutes % 60) * 6;
  return (
    <svg style={{ position: 'absolute', left: cx - r, top: cy - r, width: 2 * r, height: 2 * r, overflow: 'visible' }} viewBox={`${-r} ${-r} ${2 * r} ${2 * r}`}>
      <g style={{ filter: 'blur(0.5px)' }}>
        <line x1={0} y1={r * 0.12} x2={0} y2={-r * 0.48} stroke="#2a2622" strokeWidth={r * 0.085} strokeLinecap="round" transform={`rotate(${h})`} />
        <line x1={0} y1={r * 0.14} x2={0} y2={-r * 0.74} stroke="#2a2622" strokeWidth={r * 0.055} strokeLinecap="round" transform={`rotate(${m})`} />
        <circle r={r * 0.07} fill="#2a2622" />
      </g>
    </svg>
  );
};

/** W1/W2 framing: stage centre + scale; the 9:16 crop follows (parcels -> slot, then her + the slip) */
const T = (shot: ShotProps['shot']) => {
  const cut1 = frameOf(shot.grid?.[4] ?? 32.737) - shot.from;            // the beat before "nothing": cut to the slot close
  const back = cut1 + 27;                                                 // back to the wide-on-her
  const nothing = Math.max(cut1 + 3, (cueFrame(shot, 'slip') ?? 71) + 4);  // the slip comes back out (just after the word lands)
  return { cut1, back, nothing };
};
const camW1 = (f: number, cut1: number) => { const k = inOutSine(clamp(f / (cut1 - 1))); return { cx: lerp(1345, 1075, k), cy: lerp(722, 905, k), s: lerp(1.06, 1.55, k) }; };
const camW2 = (f: number, back: number, dur: number) => { const k = inOutSine(clamp((f - back) / (dur - back - 1))); return { cx: lerp(1062, 1070, k), cy: lerp(1030, 1040, k), s: lerp(2.05, 2.2, k) }; };

/** the slip in the slot on her side, edge-on (S13 px x 2170 = the door's face on her side): `out` px sticking out */
const SlotSlip: React.FC<{ out: number }> = ({ out }) => {
  if (out <= 0.5) return null;
  const [x, y] = st6(2170, 2240); const h = 104 * K6;
  return <div style={{ position: 'absolute', left: x, top: y, width: out * K6, height: h, background: 'linear-gradient(90deg,#b9ad98,#e9e1cf)', borderRadius: 1, boxShadow: '1px 1px 2px rgba(0,0,0,0.35)' }} />;
};

/** the slip lying on the mat in front of the slot: a flat paper on the floor (S13 px quad), sliding out from the door */
const MatSlip: React.FC<{ k: number }> = ({ k }) => {
  const dx = lerp(-170, 0, k);
  const q: Quad = ([[2200, 2758], [2445, 2752], [2468, 2808], [2188, 2816]] as [number, number][]).map(([x, y]) => st6(x + dx, y)) as Quad;
  const [sx0, sy0] = st6(2185 + dx, 2790); const [sx1] = st6(2480 + dx, 2790);
  return (
    <>
      <div style={{ position: 'absolute', left: sx0, top: sy0, width: sx1 - sx0, height: 34 * K6, borderRadius: '50%', background: 'radial-gradient(ellipse, rgba(10,8,6,0.45), rgba(10,8,6,0) 70%)' }} />
      <ScreenInsert corners={q} w={600} h={420}>
        <div style={{ position: 'absolute', inset: 0, background: PAPER, borderRadius: 6 }} />
        {[90, 160, 230, 300].map((y) => <div key={y} style={{ position: 'absolute', left: 60, right: 60, top: y, height: 8, background: 'rgba(90,80,65,0.22)' }} />)}
      </ScreenInsert>
    </>
  );
};

/** D8 (2880 px): the slip shooting straight back out of the slot at the lens. p 0..1 = slot mouth -> past the bottom-left of frame */
const FlyingSlip: React.FC<{ p: number }> = ({ p }) => {
  const e = inCubic(clamp(p)) * 0.35 + outCubic(clamp(p)) * 0.65;
  const cx = lerp(1290, 820, e), cy = lerp(640, 1560, e * e), w = lerp(380, 2100, e), h = w * lerp(0.08, 0.62, e);
  const rot = lerp(0, -22, e);
  return (
    <div style={{ position: 'absolute', left: cx - w / 2, top: cy - h / 2, width: w, height: h, transform: `rotate(${rot}deg)`, background: PAPER, borderRadius: w * 0.012,
      boxShadow: '0 20px 40px rgba(0,0,0,0.35)' }}>
      {[0.25, 0.42, 0.59, 0.76].map((y) => <div key={y} style={{ position: 'absolute', left: '8%', right: '8%', top: `${y * 100}%`, height: Math.max(1, h * 0.02), background: 'rgba(90,80,65,0.2)' }} />)}
    </div>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const { cut1, back, nothing } = T(shot);
  const clock = <PandaClock cx={st6(1089.4, 741.4)[0]} cy={st6(1089.4, 741.4)[1]} r={114.8 * K6 * 1.16} time={pt(2, 5)} variant="wall" light={0.9} uid="s2e" />;   // rl_cut4: THE panda wall clock at 2:05 over the plate's old gold face (the code hands read 8:05: film minutes)
  if (f < cut1) {
    const { cx, cy, s } = camW1(f, cut1);
    const out = f < cut1 - 9 ? 46 : lerp(46, 0, inCubic(clamp((f - (cut1 - 9)) / 6)));   // she pushes it in on the last beat
    return (
      <Cam cx={cx} cy={cy} s={s}>
        <PlateImg src="fix2/open/T6.jpg" />
        {clock}
        <SlotSlip out={out} />
      </Cam>
    );
  }
  if (f < back) {
    // the slot close: flap still settling shut from the post, then it kicks open on "nothing" and the slip flies out
    const d = f - nothing;
    const flapOpen = (f - cut1 < 2) || (d >= 0 && d < 5);
    const s = lerp(1.0, 1.04, clamp((f - cut1) / (back - cut1))) * (1 + hit(f, nothing, 0.02, 10));
    const [fx0, fy0, fx1, fy1] = [350 * K8, 580 * K8, 2531 * K8, 879 * K8];
    return (
      <AbsoluteFill>
        <Cam cx={1285} cy={700} s={s}>
          <PlateImg src="fix2/open/D8.jpg" />
          <Img src={staticFile(flapOpen ? 'fix2/open/flap_open.png' : 'fix2/open/flap_shut.png')} style={{ position: 'absolute', left: fx0, top: fy0, width: fx1 - fx0, height: fy1 - fy0 }} />
        </Cam>
        {d >= 0 && d < 9 ? <MBlur n={5} shutter={0.6} render={(dt) => <FlyingSlip p={(d + dt) / 8} />} /> : null}
      </AbsoluteFill>
    );
  }
  const { cx, cy, s } = camW2(f, back, shot.dur);
  const k = outCubic(clamp((f - back + 2) / 6));
  return (
    <Cam cx={cx} cy={cy} s={s}>
      <PlateImg src="fix2/open/T6.jpg" />
      {clock}
      {k < 1 ? <MBlur n={4} shutter={0.5} render={(dt) => <MatSlip k={outCubic(clamp((f + dt - back + 2) / 6))} />} /> : <MatSlip k={1} />}
    </Cam>
  );
};
const c916 = (x: number, cx: number, s: number) => { const c = clamp(cx, 1280 / s, 2560 - 1280 / s); return clamp((1280 + (x - c) * s) / 2560, 0.16, 0.84); };
export const S2_2E: ShotDef = {
  stage: Stage,
  cx916: (f, shot) => {
    const { cut1, back } = T(shot);
    if (f < cut1) { const { cx, s } = camW1(f, cut1); return c916(lerp(1430, 1010, inOutSine(clamp(f / (cut1 - 1)))), cx, s); }
    if (f < back) return 0.47;
    const { cx, s } = camW2(f, back, shot.dur); return c916(1055, cx, s);
  },
};
