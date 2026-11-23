// 4D "Not the same, I know": the crayon drawing is pressed to the glass from her side (comes in out of focus, lands flat),
// two tape strips slap on (beats 2 and 3); behind the glass the proud nod (S7 D1nod region, a pose cut on beat 3, held a beat).
// PLATE: S7 D1 (final) + D1nod region. Drawing and tape are code (drawn 2D art).
// rl_fix3_qa1 (QA3): (1) no snap at the cut: the drawing now starts fully below the frame and rises in (still out of focus,
// outCubic, lands flat on the same frame as before), instead of sitting half in frame at f1642 and jumping. (2) it rests on
// the glass: the two tape strips are matte, a shade darker than the paper and straddle its top corners onto the glass, so they
// read on the cream paper too (they vanished on it before). (3) 9:16 has its own layout: closer on him (s 1.36, his head
// centred, spikes in frame) with the drawing at 0.54 x under his chin, at 48-68% height (was 58-96%, in the Shorts UI);
// DATABASE stays >= 34 px at 1080 (~63 px). 16:9 framing unchanged.
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, lerp, outCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, P, ez, gb, pulse, c916, D1L } from '../s03/_lib';
import { Drawing } from './_drawing';

const PLATE = P.D1;
const D = { x: 790, y: 975, w: 520, h: 385 };
const HEAD_X = D1L.head[0];                                                          // 1293 stage: 9:16 centres on him
const Tape: React.FC<{ x: number; y: number; rot: number; k: number }> = ({ x, y, rot, k }) => (
  <div style={{ position: 'absolute', left: x - 100, top: y - 28, width: 200, height: 56, transform: `rotate(${rot}deg) scale(${lerp(1.5, 1, outCubic(clamp(k)))})`, opacity: clamp(k * 3),
    background: 'linear-gradient(180deg, rgba(222,206,160,0.92), rgba(206,190,146,0.92) 55%, rgba(214,198,154,0.92))', boxShadow: '0 2px 4px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(120,100,60,0.25)',
    clipPath: 'polygon(3% 0,97% 4%,100% 50%,97% 100%,2% 96%,0 50%)' }} />
);
const cam = (f: number, dur: number, fmt: string) => fmt === '9x16'
  ? { cx: lerp(HEAD_X + 8, HEAD_X - 4, ez(f, 0, dur)), cy: 911, s: 1.36 }        // 9:16: cy at the plate-bottom clamp for s 1.36
  : { cx: lerp(1230, 1200, ez(f, 0, dur)), cy: 870, s: 1.32 };
const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const press = ez(f, 0, gb(shot, 1) - 2, outCubic);
  const t1 = clamp((f - gb(shot, 1)) / 4), t2 = clamp((f - gb(shot, 2)) / 4);
  const thud = f >= gb(shot, 1) && f < gb(shot, 1) + 3 ? 0.004 : 0;
  const nod = f >= gb(shot, 2) + 3 && f < gb(shot, 3) + 3;
  const c = cam(f, shot.dur, fmt); const [nx, ny, nw, nh] = D1L.nod;
  // where the drawing lands (stage px) and its scale; ty0 starts it wholly below the visible frame (incl. the 1.35 scale)
  const L = fmt === '9x16' ? { x: HEAD_X - (D.w * 0.54) / 2, y: 890, sc: 0.54, ty0: 640 } : { x: D.x, y: D.y, sc: 1, ty0: 560 };
  return (
    <Cam creep={f / shot.dur} cx={c.cx} cy={c.cy} s={c.s * (1 + pulse(g) + thud)}>
      <PlateImg src={PLATE} />
      {nod ? <Img src={staticFile(P.D1nod)} style={{ position: 'absolute', left: nx, top: ny, width: nw, height: nh }} /> : null}
      {/* data-fit off while it travels in (blurred, crossing the frame edge): the text check measures it once it has landed */}
      <div data-fit={press < 1 ? 'off' : undefined} style={{ position: 'absolute', left: L.x, top: L.y, width: D.w, height: D.h, transformOrigin: '0 0', transform: `translateY(${lerp(L.ty0, 0, press).toFixed(2)}px) scale(${L.sc})` }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: D.w, height: D.h, transform: `scale(${lerp(1.35, 1, press).toFixed(4)})`, filter: `blur(${lerp(14, 0, press).toFixed(2)}px)`, transformOrigin: '50% 50%' }}>
          <Drawing w={D.w} h={D.h} rot={-3} />
          <Tape x={40} y={10} rot={-28} k={t1} />
          <Tape x={D.w - 30} y={0} rot={24} k={t2} />
        </div>
      </div>
    </Cam>
  );
};
export const S4_4D: ShotDef = { stage: Stage, cx916: (f, shot) => { const c = cam(f, shot.dur, '9x16'); return c916(HEAD_X, c.cx, c.s); } };
