// rl6_edit (FRAMES blocker 10: four whole-frame lurches in 1.1 s, a scale kick on every step, frozen in between): 4F is now ONE continuous
// camera move. The tight on her feet (1851-1868) cuts to the wide on "one"; from there the camera slides left toward the door at a constant
// speed (no kick, no reframing per step) while she backs off to the right: her three stops (1s / 2s / 4s plates, same camera, registered:
// <0.01 px apart) change on the sung "one" / "two" / "four" and are held between them. The last 16 frames the slide turns into the
// accelerating push into the door (c5d/index.tsx wrapper), so the move never stops before 4G.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { FONT } from '../../theme';
import { cueFrame } from '../../timing';
import { ShotDef, ShotProps } from '../types';
import { Cam, c916 } from '../s03/_lib';
import { A1, Lay } from '../s03/_cut1a';
import { Img, staticFile } from 'remotion';
import { TubeNeon } from '../c7/kit/sets';

const K = 2560 / 5760;
const PLATES = [A1.H1t1, A1.H1t1, A1.H1t2, A1.H1t4];
const HER = [1189, 1189, 1372, 1743];
// rl7_ra (cut 7 B19, PLAN7 row 19 / K11): the floor-tape labels bigger (72 px stencil-weight type, >= 64 px at master) and the never-seen
// '8s' tag (off frame, the known text-fit FAIL W22) dropped.
const TAGS = [{ x: 2632.4 * K, t: '1s', r: -3 }, { x: 3150.5 * K, t: '2s', r: 2 }, { x: 4100.5 * K, t: '4s', r: -2 }];
const TAG_Y = 3104.6 * K - 70;   // rl7_master: on the blue tape marks, inside the frame (text-fit FAIL: glyphs cut by the frame bottom)
const TIGHT = { s: 2.0, cx: 1340, cy: 1080 };
const WIDE = { s: 1.08, cx0: 1372, cx1: 1250, cy: 780 };
const cutsOf = (shot: ShotProps['shot']) => ['one', 'two', 'four'].map((w, i) => cueFrame(shot, w) ?? 18 * (i + 1));
const camOf = (f: number, shot: ShotProps['shot']) => {
  const c = cutsOf(shot);
  if (f < c[0]) return { s: TIGHT.s * (1 + 0.01 * f / c[0]), cx: TIGHT.cx, cy: TIGHT.cy };
  const t = (f - c[0]) / (shot.dur - c[0]);
  return { s: WIDE.s * (1 + 0.012 * t), cx: WIDE.cx0 + (WIDE.cx1 - WIDE.cx0) * t, cy: WIDE.cy };
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const cs = cutsOf(shot); const i = cs.filter((c) => f >= c).length;
  const c = camOf(f, shot);
  // rl7_ra: each step is smeared over 3 frames (motion blur in the step's direction), not a one-frame hop (PLAN7 row 19)
  const near = cs.slice(1).map((x) => f - x).find((d) => d >= -1 && d <= 1);
  const smear = near === undefined ? 0 : [5, 7, 3][near + 1];
  return (
    <Cam cx={c.cx} cy={c.cy} s={c.s}>
      <div style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, filter: smear ? `blur(${smear}px)` : undefined }}>
        <Lay src={PLATES[i]} x={0} y={0} w={2560} h={1440} />
        {/* rl7_ra (her H7.5): the room neon LIVE LOVE / BE FAMOUS in the tube style, live; she stands in front of it in t2/t4 (occluder; rect = relogo_4f.py's, P1's re-render) */}
        {false && <TubeNeon abs={shot.from + f} src="c7/neon/live_love_be_famous.png" x={1582} y={522} w={470} aspect={4096 / 2369} colors={['rgba(255,95,168,0.8)', 'rgba(69,227,255,0.8)']} seed={41} />}
        {false && i >= 2 ? <Img src={staticFile(`c7/relogo/4F/occ_t${i === 2 ? 2 : 4}.png`)} style={{ position: 'absolute', left: 3040 / 2.25, top: 850 / 2.25, width: 1080 / 2.25, height: 640 / 2.25 }} /> : null}
      </div>
      {TAGS.map((m, j) => (
        <div key={j} data-fit="box" style={{ position: 'absolute', left: m.x - 82, top: TAG_Y - 52, width: 164, height: 104, transform: `rotate(${m.r}deg)`,
          background: 'linear-gradient(180deg, rgba(226,216,190,0.95), rgba(208,197,168,0.95))', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 3px rgba(0,0,0,0.28)' }}>
          <div style={{ fontFamily: FONT.brand, fontWeight: 400, fontSize: 72, lineHeight: 1, letterSpacing: '0.04em', color: '#22201c' }}>{m.t}</div>
        </div>
      ))}
    </Cam>
  );
};
export const C5_4F_BASE: ShotDef = { stage: Stage, cx916: (f, shot) => { const i = cutsOf(shot).filter((c) => f >= c).length; const c = camOf(f, shot); return c916(HER[i], c.cx, c.s); } };
