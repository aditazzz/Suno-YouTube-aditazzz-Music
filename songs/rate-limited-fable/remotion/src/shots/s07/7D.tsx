// 7D "You looked right through me like we'd never met" (cut 4, lane L2; her S08 note): close on him, the polite blank look (C4a, as approved);
// on beat 3 a cut through the glass to her, over his shoulder: the hopeful little wave and smile (l2/7D_smile), and on beat 4 the smile
// freezes on her face while he looks right through her (l2/7D_frozen). No notice board any more.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg } from '../s07/_lib';
import { L2Img, beat, settle } from '../l2kit';
import { clamp, inOutSine, lerp } from '../../ease';
import { TextBox } from '../../blocks/Type';

// rl_cut4_fix (rl_watch4 7D: the focus pull landed on a corkboard of five blank white papers, her "no plain papers" rule): the lobby's notices,
// printed, on the papers as they hang (frontal; stage px measured on c4a), softened to the plate's depth of field. Each pays off a beat:
// NOW SERVING 41 (her FEATURE 41 parcel, 5D's guest 42), QUIET HOURS 10 PM - 6 AM (the 6:00 reset), PARCELS ... RETRY AFTER 6 AM (the 429's
// Retry-After), ROOFTOP YOGA 6 AM (her yoga at 9E/9G). Dark ink, a touch of paper texture through multiply.
const INK = '#2b2622';
const NOTICES: { b: [number, number, number, number]; lines: [string, number, string][] }[] = [
  { b: [230, 112, 710, 600], lines: [['ROOFTOP', 96, 'brand'], ['YOGA', 120, 'brand'], ['6 AM · all welcome', 46, 'head']] },
  { b: [982, 132, 1558, 556], lines: [['QUIET HOURS', 100, 'brand'], ['10 PM – 6 AM', 74, 'head']] },
  { b: [142, 732, 808, 1188], lines: [['PARCELS AFTER 10 PM', 62, 'brand'], ['RETRY AFTER', 88, 'brand'], ['6 AM', 104, 'brand']] },
  { b: [882, 702, 1558, 1178], lines: [['NOW SERVING', 86, 'brand'], ['41', 230, 'brand']] },
];
const Notices: React.FC = () => (
  <div style={{ position: 'absolute', inset: 0, filter: 'blur(4.5px)', mixBlendMode: 'multiply', opacity: 0.9 }}>
    {NOTICES.map((n, i) => {
      const [x0, y0, x1, y1] = n.b; const H = y1 - y0; const tot = n.lines.reduce((a, l) => a + l[1] * 1.08, 0); let y = y0 + (H - tot) / 2;
      return <React.Fragment key={i}>{n.lines.map(([t, sz, kind], j) => { const el = (
        <TextBox key={j} x={x0} y={y + sz * 0.54 - (sz + 32) / 2} w={x1 - x0} h={sz + 32} size={sz} kind={kind as 'brand' | 'head'} weight={kind === 'head' ? 700 : 400} color={INK}
          align="center" pad={18} lineHeight={1} style={{ whiteSpace: 'nowrap', letterSpacing: kind === 'brand' ? '0.02em' : 0 }}>{t}</TextBox>); y += sz * 1.08; return el; })}</React.Fragment>;
    })}
  </div>
);

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const b2 = beat(shot, 2, 35), b3 = beat(shot, 3, 52);
  if (f < b2) {
    const k = inOutSine(clamp(f / (b2 - 1)));
    return <Cam cx={1280} cy={720} s={lerp(1.0, 1.04, k)}><PlateImg src="cut1/b/c4a.jpg" /><Notices /></Cam>;
  }
  const k = inOutSine(clamp((f - b2) / (shot.dur - 1 - b2)));
  return (
    <Cam cx={1280} cy={700} s={lerp(1.02, 1.07, k) * (1 + settle(f, b2) + settle(f, b3, 0.006))}>
      <L2Img id={f < b3 ? '7D_smile' : '7D_frozen'} fallback="cut1/b/c4b.jpg" />
    </Cam>
  );
};
export const S7_7D: ShotDef = { stage: Stage, cx916: () => 0.5 };
