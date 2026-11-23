// rl5_d4 cut 5 1F (plan row 1F, rl5_b c5/1F): new camera high over the counter from the doorway; he stamps her A SONG parcel's
// top label on "sure, let's go" (C02: the parcel that ships, seen again in 1G/4H). Same grammar as 4e's S1F: T3a raised ->
// (no baked smear: a pose cut, one soft frame) -> T3b down with the nod on the 'stamp' cue (1.2% hit) -> back up on beat 3 and the
// label carries SURE, LET'S GO in blue ink (never red), spreading in 3 frames. B's label_top_px is degenerate (2 px tall), so the
// label corners are measured on T3a by hand (plate px): TL 1371,1046 TR 1619,1042 BR 1627,1104 BL 1371,1109. Ink = where the stamp
// face sat on T3b (u .30-.80, upper half of the label, over A SONG like 13E's SHIPPED over RETIREMENT).
// Camera (§2f): one gentle push, framed so the plant is a frame edge and the parcel sits in the lower third, toward the label (1.20 -> 1.24).
// The a <-> b changes are pose cuts with one soft frame (a crossfade ghosted his head).
import { has } from '../c7/kit/trans';
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutCubic, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { FONT } from '../../theme';
import { cueFrame, frameOf } from '../../timing';
import { Cam, hit } from '../first30/kit';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import L1F from '../../../public/c5/1F/layout.json';

const K = 2560 / 2880;
// rl5_d6: v3 (rl5_b_1f3) layout label_top_px (real, 89 px tall at 2880) replaces v2's hand-measured corners
const LABEL: Quad = ((L1F as any).label_top_px as [number, number][]).map(([x, y]) => [x * K, y * K]) as Quad;
const INK = '#2f57c9';
// rl7_ra: the stamp pose held >= 8 frames (cut 6: 'up' landed 1 frame after 'down' = a one-frame pop at 444, the motion gate's pop)
const phases = (shot: ShotProps['shot']) => { const down = cueFrame(shot, 'stamp') ?? 18; return { down, up: Math.max(down + 8, frameOf(shot.grid?.[2] ?? 15.362) - shot.from) }; };
const P = (n: string, op = 1, blur = 0) => (
  <Img src={staticFile(has(`c7/1F/p2/${n}.jpg`) ? `c7/1F/p2/${n}.jpg` : `c5/1F/${n}.jpg`)}   /* rl7_rb: rl7_p2's re-lettered shelf (T3a/T3b) */ style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, opacity: op, filter: blur ? `blur(${blur}px)` : undefined }} />
);
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const { down, up } = phases(shot);
  const k = inOutCubic(clamp(f / (shot.dur - 1)));
  const s = lerp(1.03, 1.07, k) * (1 + hit(f, down, 0.012, 12));   // rl5_d6: v3 plate is already tight; 1.2x cropped its label
  const cx = lerp(1243, 1284, k), cy = lerp(760, 1244, k);   // rl5_d6: toward the label; right edge <= stage 2486 so the rack plate "SURE, LET'S GO" cut by the v3 plate edge (stage x 2497+) stays out
  // pose cuts, no dissolve (a dissolve ghosts his nodding head): b from the 'stamp' cue to beat 3; one soft frame on each change
  const bOp = f >= down && f < up ? 1 : 0;
  const moving = f === down || f === up;
  const ink = clamp((f - up + 1) / 3);
  return (
    <AbsoluteFill style={{ background: '#0d0d0f' }}>
      <Cam cx={cx} cy={cy} s={s}>
        {P('T3a', 1, moving ? 1.5 : 0)}
        {bOp > 0 ? P('T3b', bOp, moving ? 1.5 : 0) : null}
        {ink > 0 ? (
          <ScreenInsert corners={LABEL} w={1000} h={250}>
            <div data-fit="off" style={{ position: 'absolute', left: 270, width: 560, top: 14, height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: FONT.head, fontWeight: 900, fontSize: 64, whiteSpace: 'nowrap', color: INK, opacity: 0.86 * ink, transform: `rotate(-3deg) scale(${lerp(0.96, 1, ink)})`,
              filter: `blur(${((1 - ink) * 2 + 0.5).toFixed(2)}px)`, letterSpacing: '0.01em', border: `9px solid ${INK}`, borderRadius: 14, mixBlendMode: 'multiply' }}>SURE, LET&apos;S GO</div>
          </ScreenInsert>
        ) : null}
      </Cam>
    </AbsoluteFill>
  );
};
export const C5_1F: ShotDef = { stage: Stage, cx916: () => 0.5 };
