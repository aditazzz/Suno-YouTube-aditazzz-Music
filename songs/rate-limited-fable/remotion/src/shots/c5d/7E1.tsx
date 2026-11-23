// rl5_d cut 5 7E1, THE date in one take (CUT5_PLAN §3 7E1 + §5 D; her C06 "Just one continuous shot with his visor changing her and
// cooper looking increasingly bored", N35 "an uninterrupted date looking somewhat bored and his visor agreeing", N36 "Cooper's head could
// also go down on the table towards the end of the date"). One camera, ONE eased push 1.00 -> 1.22, no cut. rl5_a2's four stage plates
// (same camera/light) and one mask per character; each character's region dissolves to its next stage on ITS OWN beat (8 frames, a
// small downward settle: a slump, not a flicker), never two characters on the same beat. rl5_c's visor lines ride on top (Visor prop).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { lerp } from '../../ease';

const D = 'c5/7E1/';
const STAGES = ['A', 'B', 'C', 'D'] as const;
export type Who = 'her' | 'cooper' | 'model';
// beat index (of the shot's 8 beats) at which each character moves to its next stage; the model on the off-beats (x.5)
// rl6_edit (FRAMES blockers 7 + 8): every change is a clean SNAP on its beat (no cross-dissolve: no two heads, no ghost arm), and the push
// now ends 2x tighter on him + Cooper (s 2.7), so her three changes come while she is still in frame (1 / 2.5 / 3.5), Cooper droops in two
// steps (2: droop, 4: head to the table, 6: flat, her N36 "towards the end"), the model gestures on 1.5 / 3 / 4.5 (never two on one beat).
export const SCHEDULE: Record<Who, number[]> = { cooper: [2, 4, 6], her: [1, 2.5, 3.5], model: [1.5, 3, 4.5] };
const DISSOLVE = 8;
const cubicInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const cl = (t: number) => Math.min(1, Math.max(0, t));

/** shot-local frame of (fractional) beat index b, from the shot's beat grid */
export const beatF = (shot: ShotProps['shot'], b: number) => {
  const gr = (shot.grid ?? []).map((t) => Math.round(t * 30) - shot.from).filter((x) => x >= 0);
  const step = gr.length > 1 ? (gr[gr.length - 1] - gr[0]) / (gr.length - 1) : 17.4;
  const i = Math.floor(b), fr = b - i;
  const at = (k: number) => (gr[k] ?? (gr[0] ?? 0) + k * step);
  return Math.round(at(i) + fr * step);
};

const Region: React.FC<{ who: Who; stage: string; op: number; dy: number }> = ({ who, stage, op, dy }) => {
  // rl6_edit: c6 masks (hard-edged, her | Cooper split at plate x 1615 above the table, model mask covering his raised arm: build/cut6/masks7e1.py)
  const m = `url(${staticFile(`c6/7E1/mask_${who}.png`)})`;
  return (
    <Img src={staticFile(`${D}stage_${stage}.jpg`)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, opacity: op,
      transform: `translateY(${dy.toFixed(2)}px)`, WebkitMaskImage: m, maskImage: m, WebkitMaskSize: '100% 100%', maskSize: '100% 100%',
      maskMode: 'luminance' }} />   // A2's masks are grayscale (no alpha): read luminance, else the whole plate swaps (rl5_d3)
  );
};

export type Make7E1 = { from: { cx: number; cy: number }; to: { cx: number; cy: number }; s1?: number; Visor?: React.FC<{ f: number; shot: ShotProps['shot'] }>; Phone?: React.FC<{ f: number }> };
export const make7E1 = ({ from, to, s1 = 1.22, Visor, Phone }: Make7E1): ShotDef => ({
  stage: ({ shot }: ShotProps) => {
    const f = useCurrentFrame(); const k = 0.5 - 0.5 * Math.cos(Math.PI * cl(f / (shot.dur - 1)));   // rl6_edit: sine (a long push, no lurch mid-shot)
    const layers: React.ReactNode[] = [];
    (['model', 'cooper', 'her'] as Who[]).forEach((who) => {
      const at = SCHEDULE[who].map((b) => beatF(shot, b));
      let si = 0; at.forEach((a) => { if (f >= a) si++; });
      if (si === 0) return;                                   // still stage A: the base plate has it
      void DISSOLVE;
      layers.push(<Region key={who} who={who} stage={STAGES[si]} op={1} dy={0} />);   // rl6_edit: a snap on the beat
    });
    return (
      <AbsoluteFill>
        <Cam cx={lerp(from.cx, to.cx, k)} cy={lerp(from.cy, to.cy, k)} s={lerp(1.0, s1, k)}>
          <Img src={staticFile(`${D}stage_A.jpg`)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
          {layers}
          {Visor ? <Visor f={f} shot={shot} /> : null}
          {Phone ? <Phone f={f} /> : null}
        </Cam>
      </AbsoluteFill>
    );
  },
  cx916: () => 0.5,
});
