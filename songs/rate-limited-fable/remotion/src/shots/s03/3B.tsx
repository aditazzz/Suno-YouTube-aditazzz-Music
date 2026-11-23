// 3B "(Four-two-nine)": he does the crossword in pen and puts the paddle up on "nine" without looking up; SLEEP is in the grid.
// rl_fix2_read (Nov 16, WATCH 3B: "the crossword can't be read ... insert the crossword clue"): the shot opens on an INSERT,
// straight down on the crossword (S30b T7c plate: paper + camera turned 180 deg so it reads the right way up for him; his hand
// was tried and did not read at this scale; the insert is the paper alone): "ACROSS / 7 What she needs (5)" printed in code
// and SLEEP already inked in its row, a slow push. Cut on beat 3 (f35) to the wide (T7a -> smear -> T7b, the 429 up on
// "nine"), unchanged from cut 1.
// rl_fix3_qa2 (Nov 16, QA3: in 9:16 the clue sat in the bottom 30% and at the crop's left edge, the P of SLEEP at its right edge):
// 9:16 only, the insert's crop is centred on the SLEEP cells (stage x 1238-1874, 87 px side margins) and the clue column prints just
// the joke, "7  What she needs (5)", indented into the crop at the top of the column (64-69% height). 16:9 unchanged.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutCubic } from '../../ease';
import { FONT } from '../../theme';
import { cueFrame } from '../../timing';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { Cam, swap, hit } from './_lib';
import { gb, Vignette } from '../s03/_lib';
import { A1, Lay } from './_cut1a';

const K = 2560 / 2880;
const q = (c: number[][]) => c.map(([x, y]) => [x * K, y * K]) as Quad;
// ---- the wide (cut 1): layout.sleep_cells r2c1..r2c5 (T7 px): the SLEEP row, in pen
const CELLS: Quad[] = [
  [[1493.9, 1117.7], [1517.1, 1117.6], [1518.4, 1122.2], [1495.0, 1122.4]],
  [[1517.1, 1117.6], [1540.3, 1117.5], [1541.7, 1122.1], [1518.4, 1122.2]],
  [[1540.3, 1117.5], [1563.5, 1117.4], [1565.1, 1122.0], [1541.7, 1122.1]],
  [[1563.5, 1117.4], [1586.7, 1117.3], [1588.4, 1121.9], [1565.1, 1122.0]],
  [[1586.7, 1117.3], [1609.8, 1117.1], [1611.8, 1121.7], [1588.4, 1121.9]],
].map((c) => q(c));
const PAD = { x: 628 * K, y: 101 * K, w: 513 * K, h: 1173 * K };   // layout.paddle_box: the t7_paddle.png layer
// ---- the insert: S30b T7c layout (T7c px)
const ICELLS: Quad[] = [
  [[1394.8, 297.0], [1537.6, 299.5], [1535.1, 442.3], [1392.3, 439.8]], [[1537.6, 299.5], [1680.4, 302.0], [1677.9, 444.8], [1535.1, 442.3]],
  [[1680.4, 302.0], [1823.2, 304.5], [1820.7, 447.2], [1677.9, 444.8]], [[1823.2, 304.5], [1965.9, 306.9], [1963.4, 449.7], [1820.7, 447.2]],
  [[1965.9, 306.9], [2108.7, 309.4], [2106.2, 452.2], [1963.4, 449.7]],
].map((c) => q(c));
const CLUE: Quad = q([[1200.2, 1022.3], [2262.4, 1040.8], [2253.0, 1581.8], [1190.7, 1563.2]]);
const INK = 'rgba(28,40,96,0.9)';
const CUT = (shot: any) => gb(shot, 2);              // beat 3 (f35)

const Insert: React.FC<{ f: number; v: boolean; cut: number }> = ({ f, v, cut }) => {
  const s = v ? 1.0 : lerp(1.02, 1.07, inOutCubic(clamp(f / cut)));   // 9:16: the cells + the clue just fit the 810 px crop at s 1
  return (
    <Cam cx={v ? 1466 : 1500} cy={v ? 720 : 640} s={s}>
      <Lay src="fix2/read/t7c_plate.jpg" x={0} y={0} w={2560} h={1440} />
      <ScreenInsert corners={CLUE} w={1060} h={540}>
        {v ? (
          <div data-fit="box" style={{ position: 'absolute', left: 170, top: -10, width: 780, padding: '20px 24px', fontFamily: '"Times New Roman", Georgia, serif', color: 'rgba(26,26,28,0.92)', lineHeight: 1.18 }}>
            <div style={{ fontSize: 62 }}><b>7</b>&nbsp; What she needs (5)</div>
          </div>
        ) : (
          <div data-fit="box" style={{ position: 'absolute', left: 14, top: 18, width: 1020, fontFamily: '"Times New Roman", Georgia, serif', color: 'rgba(26,26,28,0.92)', lineHeight: 1.18 }}>
            <div style={{ fontWeight: 700, fontSize: 64, letterSpacing: 2 }}>ACROSS</div>
            <div style={{ fontSize: 62 }}><b>7</b>&nbsp; What she needs (5)</div>
            <div style={{ fontSize: 62, opacity: 0.85 }}><b>9</b>&nbsp; Wait patiently</div>
          </div>
        )}
      </ScreenInsert>
      {'SLEEP'.split('').map((ch, k) => (
        <ScreenInsert key={k} corners={ICELLS[k]} w={143} h={143}>
          <div style={{ width: 143, height: 143, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT.head, fontWeight: 700, fontSize: 96, color: INK,
            transform: `rotate(${[-3, 2, -1, 3, -2][k]}deg)` }}>{ch}</div>
        </ScreenInsert>
      ))}
      <Vignette k={0.38} />
    </Cam>
  );
};

const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame();
  const cut = CUT(shot);
  if (f < cut) return <AbsoluteFill><Insert f={f} v={fmt === '9x16'} cut={cut} /></AbsoluteFill>;
  const nine = cueFrame(shot, 'nine') ?? 53;
  const st = swap(f, nine, 2);
  const s = lerp(1.0, 1.035, clamp((f - cut) / (shot.dur - 1 - cut))) * (1 + hit(f, nine + 1, 0.014, 12));
  const smear = st === 'S' ? (f === nine ? [190, 150, 110, 75] : [70, 45, 22, 0]) : [];
  return (
    <Cam creep={f / shot.dur} cx={1280 + (s - 1) * 1600} cy={720} s={s}>
      <Lay src={st === 'B' ? A1.T7b : A1.T7a} x={0} y={0} w={2560} h={1440} />
      {smear.map((dy, i) => (
        <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}><Lay src={A1.T7pad} x={PAD.x} y={PAD.y + dy} w={PAD.w} h={PAD.h} /></AbsoluteFill>
      ))}
      {'SLEEP'.split('').map((ch, i) => (
        <ScreenInsert key={i} corners={CELLS[i]} w={60} h={60}>
          <div style={{ width: 60, height: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT.head, fontWeight: 700, fontSize: 50, color: 'rgba(28,40,96,0.85)' }}>{ch}</div>
        </ScreenInsert>
      ))}
    </Cam>
  );
};
export const S3_3B: ShotDef = { stage: Stage, cx916: (f, shot) => {
  if (f < CUT(shot)) return 1556 / 2560;   // Cam clamps to the centre at s 1: the crop sits centred on the SLEEP cells (1238-1874); rl_fix3_qa2 (was 0.574)
  return lerp(0.5, 0.4, inOutCubic(clamp((f - (cueFrame(shot, 'nine') ?? 53)) / 10))); } };
