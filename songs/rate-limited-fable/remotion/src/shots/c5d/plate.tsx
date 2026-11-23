// rl5_d cut 5: one helper to land a new plate (CUT5_PLAN §2f camera rules built in).
//  plateShot({ src, cam: [from, to], ease, layers, over, under, grain }):
//   - src: the plate (public/ path), any 16:9 size, drawn on the 2560x1440 stage
//   - cam: ONE move, from -> to ({cx, cy, s} in stage px), inOut cubic over [a, b] shot-local frames (default the whole shot).
//     `arrive`: the move starts already moving (a continuation from the previous shot: out-cubic instead of inOut);
//     `leave`: it ends still moving (in-cubic: the next shot continues it). Keep pushes <=1.5% scale/s (§2f.3).
//   - layers: plates on top inside the camera (RGBA passes, visor states), each with an opacity function of the shot-local frame
//   - over: any React layer inside the camera (stage px) that rides the move (screens on the glass, needles, signs)
//   - screen: an unscaled layer on top (screen space), e.g. a notification
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { c5p } from './plates';   // rl7_ra: plate swaps (C5PATH) apply to plateShot too

export type CamKey = { cx: number; cy: number; s: number };
export type Layer = { src: string; op: (f: number, dur: number) => number; blend?: React.CSSProperties['mixBlendMode'] };
export type PlateSpec = {
  src: string | ((f: number, dur: number) => string);
  cam: [CamKey, CamKey]; a?: number; b?: number; arrive?: boolean; leave?: boolean;
  layers?: Layer[];
  over?: React.FC<{ f: number; shot: ShotProps['shot'] }>;
  under?: React.FC<{ f: number; shot: ShotProps['shot'] }>;
  screen?: ShotDef['screen'];
  ph?: number;
  cx916?: number;
};
const cubicIn = (t: number) => t * t * t;
const cubicOut = (t: number) => 1 - Math.pow(1 - t, 3);
const cubicInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const camAt = (p: PlateSpec, f: number, dur: number): CamKey => {
  const a = p.a ?? 0, b = p.b ?? dur - 1; const t = Math.min(1, Math.max(0, (f - a) / Math.max(1, b - a)));
  // a continuation that also leaves moving is linear; otherwise ease the open end(s)
  const k = p.arrive && p.leave ? t : p.arrive ? cubicOut(t) : p.leave ? cubicIn(t) : cubicInOut(t);
  const [A, B] = p.cam;
  return { cx: lerp(A.cx, B.cx, k), cy: lerp(A.cy, B.cy, k), s: lerp(A.s, B.s, k) };
};
const Plate: React.FC<{ src: string; op?: number; blend?: React.CSSProperties['mixBlendMode'] }> = ({ src, op = 1, blend }) => (
  <Img src={staticFile(c5p(src))} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, opacity: op, mixBlendMode: blend }} />
);
export const plateShot = (p: PlateSpec): ShotDef => ({
  stage: ({ shot }) => {
    const f = useCurrentFrame(); const c = camAt(p, f, shot.dur);
    const src = typeof p.src === 'function' ? p.src(f, shot.dur) : p.src;
    const Over = p.over, Under = p.under;
    return (
      <AbsoluteFill>
        <Cam cx={c.cx} cy={c.cy} s={c.s} ph={p.ph}>
          {Under ? <Under f={f} shot={shot} /> : null}
          <Plate src={src} />
          {(p.layers ?? []).map((l, i) => { const o = l.op(f, shot.dur); return o > 0.001 ? <Plate key={i} src={l.src} op={Math.min(1, o)} blend={l.blend} /> : null; })}
          {Over ? <Over f={f} shot={shot} /> : null}
        </Cam>
      </AbsoluteFill>
    );
  },
  screen: p.screen,
  cx916: () => p.cx916 ?? 0.5,
});
/** a still frame (no move): for "dead still" holds */
export const still = (k: CamKey): [CamKey, CamKey] => [k, k];
