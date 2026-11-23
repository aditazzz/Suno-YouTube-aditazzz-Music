// 3D "(tail of the bar)": straight down on his logbook. Three earlier entries on the right page; on the beats he writes
// tonight's "2:11 refreshing." (stroke-on, left to right, his hand + pen riding the stroke).
// rl_fix2_read (Nov 16, WATCH 3D: "the pen writes on its own (no hand) ... about 9 px ... the left page is blank"):
// Framed on the right page only: 16:9 s 2.2 (entries ~82 px at 1920), 9:16 s 1.32 (~88 px); the pen's top runs out of frame
// (it is held just off frame) and his hand's soft shadow lies on the page above the stroke.
// PLATE: S21b T8 (open logbook) + the pen RGBA (tip at layout.pen_tip_px). His hand ON the pen is still open: blrl_fix2_read
// T8h (his arm in, the book turned for him) was rendered as a preview, and his hand did not hold the pen convincingly at this
// scale (see workers/rl_fix2_read/STATUS.md); not used.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutSine } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, ez, HAND, INK, Vignette, gb, c916 } from './_lib';
import { A1, Lay } from './_cut1a';

const K = 2560 / 2880;
const RULE = [95.4, 178.9, 262.4, 345.9, 429.4, 512.9].map((y) => y * K);   // the right page's ruled lines from the top (T8h px -> stage)
const X0 = 1415;                                   // text start (stage): just right of the right page's margin
const FS = 50;
const LINES: { t: string; x?: number }[] = [
  // rl_l3_ui (cut 4, S04: the log starts at the limit, 2:01, not before it): 2:01 asked nicely · 2:03 IN CAPITALS · 2:05 · 2:11
  { t: '2:01  asked nicely.' }, { t: '2:03  asked again,' }, { t: 'IN CAPITALS.', x: 92 }, { t: '2:05  "one last thing" (4th).' },
];
const TONIGHT = '2:11  refreshing.', WR = 360;     // written width of tonight's line
const PEN = { x: 1611 * K, y: 0, w: 340 * K, h: 626 * K, tipX: 1668.3 * K, tipY: 549 * K };   // pen_box crop + pen_tip_px
const top = (line: number) => RULE[line] - FS * 0.86;
const cam = (v: boolean, f: number, k: number, dur: number) => v
  ? { cx: lerp(1640, 1660, k), cy: 560, s: lerp(1.30, 1.34, ez(f, 0, dur)) }
  : { cx: lerp(1700, 1730, k), cy: 380, s: lerp(2.16, 2.24, ez(f, 0, dur)) };

const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame();
  const a = gb(shot, 0) + 2, b = gb(shot, 2) + 10;                       // writes from beat 1 to just past beat 3
  const k = inOutSine(clamp((f - a) / (b - a)));
  const writing = k > 0 && k < 1;
  const tipX = X0 + WR * k, tipY = RULE[5] - 16 + (writing ? Math.sin(f * 1.9) * 7 : 0) - (writing ? 0 : 6);
  const c = cam(fmt === '9x16', f, k, shot.dur);
  return (<>
    <Cam cx={c.cx} cy={c.cy} s={c.s}>
      <Lay src={A1.T8} x={0} y={0} w={2560} h={1440} />
      {LINES.map((l, i) => (
        <div key={i} data-fit="off" style={{ position: 'absolute', left: X0 + (l.x ?? 0), top: top(i + 1), whiteSpace: 'nowrap', fontFamily: HAND, fontSize: FS, lineHeight: 1, color: INK, opacity: 0.9 }}>{l.t}</div>
      ))}
      <div data-fit="off" style={{ position: 'absolute', left: X0, top: top(5) - 10, width: WR * k + 4, height: FS + 24, overflow: 'hidden', whiteSpace: 'nowrap', fontFamily: HAND, fontSize: FS, lineHeight: 1, color: INK, paddingTop: 10, boxSizing: 'border-box' }}>{TONIGHT}</div>
      {/* his hand's shadow, just off frame above the pen (the key light is up-left, as the pen's own shadow says) */}
      <div style={{ position: 'absolute', left: tipX + 40, top: c.cy - 720 / c.s - 60, width: 300, height: 230, borderRadius: '50%',
        background: 'radial-gradient(ellipse, rgba(30,24,18,0.30) 0%, rgba(30,24,18,0.14) 50%, rgba(30,24,18,0) 75%)', filter: 'blur(18px)', mixBlendMode: 'multiply' }} />
      {/* the pen: the RGBA layer moved so its tip rides the stroke; its top runs out of frame (held just off frame) */}
      <Lay src={A1.T8pen} x={PEN.x + tipX - PEN.tipX} y={PEN.y + tipY - PEN.tipY} w={PEN.w} h={PEN.h} style={{ filter: 'drop-shadow(9px 13px 7px rgba(0,0,0,0.38))' }} />
    </Cam>
    <Vignette k={0.4} />
  </>);
};
export const S3_3D: ShotDef = { stage: Stage, cx916: (f, shot) => {
  const k = inOutSine(clamp((f - gb(shot, 0) - 2) / (gb(shot, 2) + 8 - gb(shot, 0)))); const c = cam(true, f, k, shot.dur); return c916(1650, c.cx, c.s); } };
