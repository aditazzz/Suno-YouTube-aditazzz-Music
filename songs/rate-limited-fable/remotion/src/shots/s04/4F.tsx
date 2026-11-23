// 4F "Backed off one, then two, then four": exponential backoff, done on foot. Opens tight on the floor: blue painter's tape
// strips with masking-tape tags 1s 2s 4s (8s off to the right), her boots at the 1s strip; on "one" cut to the wide (she is at
// one tile), on "two" she is at two, on "four" at four: jump cuts in one locked wide, a small hit on each.
// PLATE: rl_cut1 a1 = S11 H1_t1 / H1_t2 / H1_t4 (5760x3240, T6's camera: her standing, arms folded, toes at the tape).
// The tags are code at layout.tape_labels.label_anchor_px (8s's anchor is off-frame: its tag sits on the strip's visible end).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { FONT } from '../../theme';
import { cueFrame } from '../../timing';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit, pulse, c916 } from '../s03/_lib';
import { A1, Lay } from '../s03/_cut1a';

const K = 2560 / 5760;
const PLATES = [A1.H1t1, A1.H1t1, A1.H1t2, A1.H1t4];        // tight on the tape, then 1, 2, 4 tiles
const CAMS = [{ s: 2.0, cx: 1340, cy: 1080 }, { s: 1.08, cx: 1400, cy: 780 }, { s: 1.08, cx: 1400, cy: 780 }, { s: 1.08, cx: 1400, cy: 780 }];
const HER = [1189, 1189, 1372, 1743];                       // her centre x (layout her_1 / her_2 / her_4)
const TAGS = [{ x: 2632.4 * K, t: '1s', r: -3 }, { x: 3150.5 * K, t: '2s', r: 2 }, { x: 4100.5 * K, t: '4s', r: -2 }, { x: 2480, t: '8s', r: 3 }];
const TAG_Y = 3104.6 * K;                                   // 1380: the strips' near ends
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const cuts = ['one', 'two', 'four'].map((w, i) => cueFrame(shot, w) ?? 18 * (i + 1));
  const i = cuts.filter((c) => f >= c).length;
  const c = CAMS[i];
  const s = c.s * (1 + pulse(g) + (i > 0 ? hit(f, cuts[i - 1], 0.012, 8) : 0));
  return (
    <Cam creep={f / shot.dur} cx={c.cx} cy={c.cy} s={s}>
      <Lay src={PLATES[i]} x={0} y={0} w={2560} h={1440} />
      {TAGS.map((m, j) => (
        <div key={j} data-fit="box" style={{ position: 'absolute', left: m.x - 56, top: TAG_Y - 35, width: 112, height: 70, transform: `rotate(${m.r}deg)`,
          background: 'linear-gradient(180deg, rgba(226,216,190,0.95), rgba(208,197,168,0.95))', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 3px rgba(0,0,0,0.28)' }}>
          <div style={{ fontFamily: FONT.mono, fontWeight: 700, fontSize: 44, lineHeight: 1, color: '#22201c' }}>{m.t}</div>
        </div>
      ))}
    </Cam>
  );
};
export const S4_4F: ShotDef = { stage: Stage, cx916: (f, shot) => { const i = ['one', 'two', 'four'].map((w, j) => cueFrame(shot, w) ?? 18 * (j + 1)).filter((c) => f >= c).length; return c916(HER[i], CAMS[i].cx, CAMS[i].s); } };
