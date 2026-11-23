// 13A "Limit reset" (cut 4, lane L2; her #37 note, §2g): 6:00:00, silence. Her face, close, the hat filling the top of the frame, breath held,
// eyes wide (l2/13A_held). The three locks clack, one per beat, each a tiny flinch on her face (a camera hit + a shiver); on the third the
// lobby lights come up full (S22) and her face breaks into joy (l2/13A_joy). This is the Fable hero shot: the stills here are lane L2's
// Opus preview; the hero pass replaces l2/13A_held / 13A_joy with the same names. DigitalTime stays exported (older shots used it).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert, Quad } from '../../blocks/ScreenInsert';
import { FONT } from '../../theme';
import { Cam, hit } from '../first30/kit';
import { D1, clamp, lerp } from '../s10/_lib';
import { inOutSine } from '../../ease';

/** a first30 lock component re-seated at a D1 point (they are drawn at door.jpg positions) */
const At: React.FC<{ from: [number, number]; to: [number, number]; s: number; children: React.ReactNode }> = ({ from, to, s, children }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, transformOrigin: `${from[0]}px ${from[1]}px`,
    transform: `translate(${to[0] - from[0]}px, ${to[1] - from[1]}px) scale(${s})` }}>{children}</div>
);
export const DigitalTime: React.FC<{ text: string }> = ({ text }) => (
  <ScreenInsert corners={D1.digital as Quad} w={330} h={126}>
    <div data-fit="off" style={{ position: 'absolute', inset: 0, background: '#14110e', display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: FONT.mono, fontWeight: 700, fontSize: 96, color: 'rgb(219,204,168)', filter: 'blur(1.2px)' }}>{text}</div>
  </ScreenInsert>
);
import { L2Img, beat } from '../l2kit';

// rl_cut4_fix: the joy end 1.04 -> 0.97 (with c4fix/13A_joy's grade: the face was blown out, rl_watch4)
// rl_cut4c_fix (rl_watch4b 13A: the joy face still a step paler than f6116-6164): measured on the cut 4b render, face centre luma held 148 vs
// joy 173 (and redder): the joy end 0.97 -> 0.875 and a touch less saturation, so it lands ~156 (a hair of the lights-up left).
const JOY_END = 0.875;
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const b = [beat(shot, 1, 17), beat(shot, 2, 35), beat(shot, 3, 52)];
  const joy = f >= b[2];
  const shiver = b.slice(0, 2).reduce((a, t) => a + (f >= t && f < t + 5 ? Math.sin((f - t) * 2.6) * Math.exp(-(f - t) / 2) : 0), 0);
  const k = inOutSine(clamp(f / (shot.dur - 1)));
  const s = lerp(1.0, 1.06, k) * (1 + hit(f, b[0], 0.010, 7) + hit(f, b[1], 0.012, 7) + hit(f, b[2], 0.02, 12));
  const up = joy ? clamp((f - b[2]) / 6) : 0;
  return (
    <Cam cx={1280 + shiver * 3} cy={720} s={s}>
      <L2Img id={joy ? '13A_joy' : '13A_held'} style={{ filter: joy ? `brightness(${lerp(0.86, JOY_END, up).toFixed(3)}) saturate(${lerp(1, 0.93, up).toFixed(3)})` : 'brightness(0.860)' }} />
    </Cam>
  );
};
export const S13_13A: ShotDef = { stage: Stage, cx916: () => 0.5 };
