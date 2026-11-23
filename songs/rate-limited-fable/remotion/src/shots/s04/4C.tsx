// 4C "Tried your little brother": low at knee height on the little JR. door beside the big one. Her slip is already pushed
// into its letter slot (held by the shut flap); on beat 2 it is snatched inside (the flap kicks); on beat 3 the flap swings
// up and a small orange hand slides out holding a crayon drawing, and settles. The little one says yes straight away.
// PLATE: rl_cut1 a1 = S21c T10 (JR. door, JR. plate baked) + flap_open_region + hand_half / hand_out RGBA (full frame);
// the crayon art (code, ./_drawing) is pinned to the paper in each hand pose (layout paper_corners).
// rl_fix3_qa1 (QA3 pops): (1) the "please?" slip no longer vanishes in one frame: it slides up through the slot over 6 frames
// (inOutSine, <= 32 stage px a frame), the flap kicks open as its last edge goes in and drops shut 2 frames after.
// (2) the drawing no longer snaps from lying flat to hanging in one frame: from the hand_out pose it tips down about its top
// edge (the hinge in the little hand's fingers) over 6 frames (gravity: inQuad), then the existing overshoot + swing settle it. During
// the tip the hand_out layer is clipped above the hinge (its baked hanging paper is hidden) and the code paper is pinned
// to a quad rotating from the flat PAPER_HALF to the hanging PAPER_OUT.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, lerp, outBack, inOutSine } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { Cam, ez, gb, pulse, HAND, INK, c916 } from '../s03/_lib';
import { A1, Lay } from '../s03/_cut1a';
import { Drawing } from './_drawing';

const K = 2560 / 2880;
const q = (c: number[][]) => c.map(([x, y]) => [x * K, y * K]) as Quad;
const MOUTH = q([[1212.6, 781.2], [1555.3, 790.4], [1554.9, 872.0], [1213.4, 860.0]]);   // layout.slot_mouth_corners
const FLAP = { x: 1070 * K, y: 714 * K, w: 626 * K, h: 225 * K };                         // layout.flap_open_region
const PAPER_HALF = q([[1240.5, 856.1], [1520.1, 865.6], [1478.3, 912.5], [1175.4, 900.9]]);
const PAPER_OUT = q([[1217.8, 865.6], [1504.5, 873.3], [1506.7, 1088.8], [1224.2, 1076.5]]);
/** the paper tipping about its top edge: deg 90 = flat (sticking out at us, PAPER_HALF) .. 0 = hanging (PAPER_OUT) */
const tipQuad = (deg: number): Quad => {
  const a = (deg * Math.PI) / 180, c = Math.cos(a), sn = Math.sin(a), w = 1 - deg / 90;
  const top = [0, 1].map((i) => [lerp(PAPER_HALF[i][0], PAPER_OUT[i][0], w), lerp(PAPER_HALF[i][1], PAPER_OUT[i][1], w)]);
  const bot = (bi: number, ti: number, t: number[]) => [
    t[0] + (PAPER_OUT[bi][0] - PAPER_OUT[ti][0]) * c + (PAPER_HALF[bi][0] - PAPER_HALF[ti][0]) * sn,
    t[1] + (PAPER_OUT[bi][1] - PAPER_OUT[ti][1]) * c + (PAPER_HALF[bi][1] - PAPER_HALF[ti][1]) * sn];
  return [top[0], top[1], bot(2, 1, top[1]), bot(3, 0, top[0])] as Quad;
};
/** hand_out clipped to above its paper's top edge (+2 px): hides the baked hanging paper while the code paper tips */
const HINGE = (x: number) => PAPER_OUT[0][1] + ((PAPER_OUT[1][1] - PAPER_OUT[0][1]) * (x - PAPER_OUT[0][0])) / (PAPER_OUT[1][0] - PAPER_OUT[0][0]) + 2;
const aboveHinge = `polygon(0px 0px, 2560px 0px, 2560px ${HINGE(2560).toFixed(1)}px, 0px ${HINGE(0).toFixed(1)}px)`;
const SLOT_X = (MOUTH[0][0] + MOUTH[1][0]) / 2;                                            // 1231 stage
/** the slot's lower lip (stage line through the mouth's bottom corners): the slip hangs from it; things above it are inside */
const lipY = (x: number) => MOUTH[3][1] + ((MOUTH[2][1] - MOUTH[3][1]) * (x - MOUTH[3][0])) / (MOUTH[2][0] - MOUTH[3][0]);
const topY = (x: number) => MOUTH[0][1] + ((MOUTH[1][1] - MOUTH[0][1]) * (x - MOUTH[0][0])) / (MOUTH[1][0] - MOUTH[0][0]);
const below = (yAt: (x: number) => number) => `polygon(0px ${yAt(0).toFixed(1)}px, 2560px ${yAt(2560).toFixed(1)}px, 2560px 1440px, 0px 1440px)`;

/** her slip hanging out of the slot (top edge in the slot, tilted a touch toward us), pulled up by `inK` (0 out .. 1 gone) */
const Slip: React.FC<{ inK: number }> = ({ inK }) => {
  const x0 = SLOT_X - 112, x1 = SLOT_X + 112, hang = 128 * (1 - inK), lift = 128 * inK;
  const quad: Quad = [[x0, lipY(x0) - 6 - lift], [x1, lipY(x1) - 6 - lift], [x1 + 4, lipY(x1) - 6 - lift + 128], [x0 - 4, lipY(x0) - 6 - lift + 128]];
  return hang <= 0 ? null : (
    <div style={{ position: 'absolute', inset: 0, clipPath: below((x) => lipY(x) - 4) }}>
      <ScreenInsert corners={quad} w={300} h={170}>
        <div style={{ width: 300, height: 170, background: 'linear-gradient(180deg,#cfc6b4,#e6dfcf 40%,#ddd5c3)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'inset 0 10px 14px rgba(0,0,0,0.25)' }}>
          <div style={{ fontFamily: HAND, fontSize: 78, color: INK, marginTop: 34 }}>please?</div>
        </div>
      </ScreenInsert>
    </div>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const snatch = gb(shot, 1), out = gb(shot, 2);
  const inK = inOutSine(clamp((f - snatch) / 6));                                  // pulled up through the slot over 6 frames
  const kick = f >= snatch + 5 && f < snatch + 8;                                   // the flap kicks open as its last edge goes in
  const flapOpen = kick || f >= out - 2;
  const half = f >= out && f < out + 4, full = f >= out + 4;
  const tk = clamp((f - out - 4) / 6), tipping = full && tk < 1;                     // the paper tips down from flat to hanging
  const tipDeg = 90 * (1 - tk * tk);
  const ho = clamp((f - out - 4) / 10);                                             // hand_out: slides the last bit out and settles
  const dy = full ? lerp(-26, 0, outBack(ho, 1.6)) : half ? lerp(-34, -8, (f - out) / 4) : 0;
  const swing = full ? 2.2 * Math.exp(-Math.max(0, f - out - 10) / 9) * Math.sin(Math.max(0, f - out - 10) / 2.4) : 0;
  const s = lerp(1.18, 1.22, ez(f, 0, shot.dur)) * (1 + pulse(g));
  return (
    <Cam cx={lerp(1263, 1250, ez(f, 0, shot.dur))} cy={720} s={s}>
      <Lay src={A1.T10} x={0} y={0} w={2560} h={1440} />
      {flapOpen ? <Lay src={A1.T10flap} x={FLAP.x} y={FLAP.y} w={FLAP.w} h={FLAP.h} /> : null}
      <Slip inK={inK} />
      {half || full ? (
        <div style={{ position: 'absolute', inset: 0, clipPath: below(topY) }}>
          <div style={{ position: 'absolute', inset: 0, transformOrigin: `${SLOT_X}px ${lipY(SLOT_X)}px`, transform: `translateY(${dy.toFixed(2)}px) rotate(${swing.toFixed(3)}deg)` }}>
            <Lay src={full ? A1.T10out : A1.T10half} x={0} y={0} w={2560} h={1440} style={tipping ? { clipPath: aboveHinge } : undefined} />
            <ScreenInsert corners={tipping ? tipQuad(tipDeg) : full ? PAPER_OUT : PAPER_HALF} w={330} h={240} light={0.86}><Drawing w={330} h={240} /></ScreenInsert>
          </div>
        </div>
      ) : null}
    </Cam>
  );
};
export const S4_4C: ShotDef = { stage: Stage, cx916: (f, shot) => c916(SLOT_X, lerp(1263, 1250, ez(f, 0, shot.dur)), lerp(1.18, 1.22, ez(f, 0, shot.dur))) };
