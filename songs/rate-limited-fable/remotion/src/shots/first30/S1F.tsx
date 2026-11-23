// 1F, the stamp (first30.md): him chest-up at the desk, the stamp up over her slip; the rack shows SURE, LET'S GO · GREAT
// QUESTION · YOU'RE ABSOLUTELY RIGHT; the brass meter behind him, needle a hair from the red, its label out of frame.
// rl_fix2_open (WATCH blocker: the old stand-in showed HOURS AWAKE + the GLASSES OF WATER / LAST MEAL plates at 0:14): now the
// rendered S5 T3 finals (TR_cam_S5, the meter's label hidden, no plates in frame): T3a stamp raised -> T3s smear (2 frames) ->
// T3b stamp down with the nod on clap 2 (1.5% camera hit) -> beat 3 back up (1 smear frame) and the slip carries SURE, LET'S GO
// in blue ink (never red), spreading in 3 frames; then a push in to the slip so the ink reads (him still in frame).
// rl_fix3_qa2 (Nov 16, QA3: in 9:16 the SURE, LET'S GO slip sat at 88-92% height, under the Shorts UI): the slip is only ~130 stage
// px above the plate's bottom edge, so no crop can lift it. 9:16 only, after the stamp comes up: a quicker, closer push onto the
// slip (s 2.2, 18 frames) with the frame raised 250 px so the ink lands at ~60% height; the 17% strip under the plate (all inside
// the bottom 30% UI zone) is the plate's own edge mirrored, blurred and falling off into shadow. 16:9 unchanged; 9:16 identical
// until the stamp is back up.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, inOutCubic, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { FONT } from '../../theme';
import { cueFrame, frameOf } from '../../timing';
import { Cam, PlateImg, hit } from './kit';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';

const K5 = 2560 / 2880;
// S5 layout slip_S5 corners (far-left, far-right, near-right, near-left) -> TL, TR, BR, BL on the stage
const SLIP: Quad = ([[1043.1, 1415.7], [1299.2, 1429.7], [1255.7, 1529.4], [967.1, 1511.5]] as [number, number][]).map(([x, y]) => [x * K5, y * K5]) as Quad;
const INK = '#2f57c9';
const SLIP_C: [number, number] = [1005, 1300];      // stage px: the slip centre (the push aims here)
const HEAD: [number, number] = [1137.5 * K5, 758.8 * K5];

const camAt = (f: number, down: number, up: number, dur: number) => {
  const p = inOutCubic(clamp((f - up - 3) / (dur - up - 6)));
  const s = lerp(1.0, 1.02, clamp(f / up)) * (1 + hit(f, down, 0.015, 12)) * lerp(1, 1.52, p);
  return { cx: lerp(1280, SLIP_C[0], p), cy: lerp(720, SLIP_C[1], p), s };
};
// 9:16 (rl_fix3_qa2): the push onto the slip, closer and quicker, the frame raised by dy (stage px at the output) below the plate
const S916 = 2.2, DY916 = -250, PUSH916 = 18;
const camAt916 = (f: number, down: number, up: number) => {
  const p = inOutCubic(clamp((f - up - 1) / PUSH916));
  const s = lerp(1.0, 1.02, clamp(f / up)) * (1 + hit(f, down, 0.015, 12)) * lerp(1, S916, p);
  return { cx: lerp(1280, SLIP_C[0], p), cy: lerp(720, SLIP_C[1], p), s, dy: DY916 * p, p };
};
const phases = (shot: ProShot) => ({ down: cueFrame(shot, 'stamp') ?? 18, up: frameOf(shot.grid?.[2] ?? 15.362) - shot.from });
type ProShot = ShotProps['shot'];

/** 9:16: under the plate's bottom edge, the plate mirrored, blurred and falling off into shadow (only once the frame is raised) */
const Under: React.FC<{ src: string }> = ({ src }) => (
  <>
    <div style={{ position: 'absolute', left: 0, top: 1440, width: 2560, height: 360, overflow: 'hidden' }}>
      <PlateImg src={src} filter="blur(10px) brightness(0.5) saturate(0.8)" style={{ transform: 'scaleY(-1)', transformOrigin: '50% 50%' }} />
    </div>
    <div style={{ position: 'absolute', left: 0, top: 1372, width: 2560, height: 68, background: 'linear-gradient(180deg, rgba(10,8,7,0) 0%, rgba(10,8,7,0.5) 100%)' }} />
    <div style={{ position: 'absolute', left: 0, top: 1440, width: 2560, height: 360, background: 'linear-gradient(180deg, rgba(10,8,7,0.5) 0%, rgba(10,8,7,0.88) 45%, rgba(10,8,7,0.96) 100%)' }} />
  </>
);
const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame();
  const { down, up } = phases(shot);
  const v = fmt === '9x16' ? camAt916(f, down, up) : null;
  const plate = f < down ? 'T3a' : f < down + 2 ? 'T3s' : f < up ? 'T3b' : f < up + 1 ? 'T3s' : 'T3a';
  const ink = clamp((f - up + 1) / 3);
  const { cx, cy, s } = v ?? camAt(f, down, up, shot.dur);
  return (
    <Cam cx={cx} cy={cy} s={s} dy={v ? v.dy : 0}>
      <PlateImg src={`fix2/open/${plate}.jpg`} />
      {v && v.p > 0 ? <Under src={`fix2/open/${plate}.jpg`} /> : null}
      {ink > 0 ? (
        <ScreenInsert corners={SLIP} w={1000} h={360}>
          <div data-fit="off" style={{ position: 'absolute', left: 70, right: 70, top: 70, height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: FONT.head, fontWeight: 900, fontSize: 92, whiteSpace: 'nowrap', color: INK, opacity: 0.86 * ink, transform: `rotate(-4deg) scale(${lerp(0.96, 1, ink)})`,
            filter: `blur(${((1 - ink) * 2 + 0.6).toFixed(2)}px)`, letterSpacing: '0.02em', border: `12px solid ${INK}`, borderRadius: 20, mixBlendMode: 'multiply' }}>SURE, LET&apos;S GO</div>
        </ScreenInsert>
      ) : null}
    </Cam>
  );
};
const c916 = (x: number, cx: number, s: number) => { const c = clamp(cx, 1280 / s, 2560 - 1280 / s); return clamp((1280 + (x - c) * s) / 2560, 0.16, 0.84); };
export const S1_1F: ShotDef = {
  stage: Stage,
  // 9:16: between his head and the slip; rl_fix3_qa2: then onto the slip as the 9:16 push lands
  cx916: (f, shot) => { const { down, up } = phases(shot); const { cx, s, p } = camAt916(f, down, up); return c916(lerp((HEAD[0] + SLIP_C[0]) / 2, SLIP_C[0], p), cx, s); },
};
