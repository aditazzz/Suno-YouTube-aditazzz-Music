// 5E (cut 5; plan §3: f2580-2719, 4.6 s; N27, N28): Claude Code on her laptop, the cat on the lid. She asks ("write
// do_it_myself.py. I'll take it from here"), Enter on 2598, the limit line (the same wording as the app). So she opens the file
// herself, in Claude Code's own bash mode (`! cat do_it_myself.py`: runs without the model, so it works at the limit), Enter on
// 2632: it has one line, `# TODO: ask Claude at 6:00`. On 2684 the cat's paw lands on the keys: a row of j's and semicolons types
// into the prompt. One slow push, no cut (the lid slam of cut 4e is gone: her N27 "stay longer").
// Plate: cut 4e's 5E (fix2/end/t16.jpg + the cat cut-out t16_cat.png over the screen, its paw dipping on the keystrike).
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { Cam, PlateImg } from '../s03/_lib';
import { LAY, quadSt } from '../s05/_cut1b';
import { CHIP, CODE_5E } from '../../blocks/real/script';
import { ClaudeCode5, CodeState } from './ClaudeCode5';
import { clamp, ez, lerp, loc } from './kit';

export const E5 = { ENTER: 2598, BANG: 2615, RUN: 2632, PAW: 2684 };   // absolute
const CMD = `cat ${CODE_5E.file}`;
const STRAY = 'jjjjjjjjjjjjjjjjjj;;;;;;;;;;;;';

export const codeAt5E = (f: number, c: { ENTER: number; BANG: number; RUN: number; PAW: number }): CodeState => {
  const caret = f % 14 < 9;
  if (f < c.ENTER) { const n = Math.floor(clamp((f - 1) / (c.ENTER - 4)) * CODE_5E.ask.length); return { typed: CODE_5E.ask.slice(0, n), caret: true, model: CHIP.night }; }
  const base: CodeState = { typed: CODE_5E.ask, sent: true, limit: clamp((f - c.ENTER - 2) / 8), caret, model: CHIP.night };
  if (f < c.BANG) return base;
  const n = Math.floor(clamp((f - c.BANG - 1) / (c.RUN - c.BANG - 3)) * CMD.length);
  const bash = { cmd: CMD, n, sent: f >= c.RUN, out: clamp((f - c.RUN - 3) / 4), file: CODE_5E.line };
  const stray = f >= c.PAW ? STRAY.slice(0, Math.min(STRAY.length, 2 + Math.floor((f - c.PAW) * 1.6))) : undefined;
  return { ...base, bash, stray, caret: f < c.RUN ? true : caret };
};

const SC = quadSt(LAY.T16.screen_corners);
const K = 2560 / 2880;
const CAT = { x: 509 * K, y: 0, w: (2225 - 509) * K, h: 1463 * K };
const TW = 2560, TH = Math.round(2560 * (((SC[2][1] - SC[1][1]) + (SC[3][1] - SC[0][1])) / 2) / (((SC[1][0] - SC[0][0]) + (SC[2][0] - SC[3][0])) / 2));
const onScreen = (u: number, v: number) => {
  const top = [SC[0][0] + (SC[1][0] - SC[0][0]) * u, SC[0][1] + (SC[1][1] - SC[0][1]) * u], bot = [SC[3][0] + (SC[2][0] - SC[3][0]) * u, SC[3][1] + (SC[2][1] - SC[3][1]) * u];
  return { x: top[0] + (bot[0] - top[0]) * v, y: top[1] + (bot[1] - top[1]) * v };
};
const MID = onScreen(0.5, 0.5), LOW = onScreen(0.46, 0.62);

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const c = { ENTER: loc(shot, E5.ENTER), BANG: loc(shot, E5.BANG), RUN: loc(shot, E5.RUN), PAW: loc(shot, E5.PAW) };
  const e = ez(f, 0, shot.dur - 1);
  const s = lerp(1.55, 1.95, e), cx = lerp(MID.x, LOW.x, e), cy = lerp(MID.y - 40, LOW.y, e);
  const dip = 0;                                            // the cat stays put on the lid (nothing floats); the stray keys are the joke
  return (
    <Cam cx={cx} cy={cy} s={s}>
      <PlateImg src="fix2/end/t16.jpg" />
      <ScreenInsert corners={SC} w={TW} h={TH} glare={0.05} light={0.86}>
        <ClaudeCode5 w={TW} h={TH} fs={70} ui={TW / 1512} state={codeAt5E(f, c)} />
      </ScreenInsert>
      <Img src={staticFile('fix2/end/t16_cat.png')} style={{ position: 'absolute', left: CAT.x, top: CAT.y + dip, width: CAT.w, height: CAT.h }} />
    </Cam>
  );
};
export const C5_5E: ShotDef = { stage: Stage, cx916: () => 0.5 };
