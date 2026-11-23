// rl5_d (cut 5): cut 4e's shots as building blocks. C4E = the 85 cut-4e shot objects (src/data/shots_c4e.json), so a
// cut-4e component can still play inside a cut-5 shot with the frames/cues it was built for.
//  pieces([...]): one cut-5 shot made of cut-4e pieces in order. Each piece: def + old shot, where it starts in the new
//  shot (at), how long (len), which old local frame it starts on (from, default 0), and freezeTo (hold old frame N for
//  the first `freeze` frames, e.g. a shot that now starts earlier).
//  camera(def, fn): wraps a def's stage in an extra eased move (scale/translate about a point), for single pushes etc.
import React from 'react';
import { AbsoluteFill, Freeze, Sequence, useCurrentFrame } from 'remotion';
import c4e from '../../data/shots_c4e.json';
import { Shot } from '../../timing';
import { ShotDef, ShotProps } from '../types';

export const C4E: Record<string, Shot> = Object.fromEntries(((c4e as any).shots as Shot[]).map((s) => [s.id, s]));

export type Piece = { def: ShotDef; old: string; at: number; len: number; from?: number; freeze?: number; freezeAt?: number; rate?: number; play?: number };
// rate: old frames per new frame (0.5 = twice as long, for "stay longer" placeholders); play: play this many old frames, then hold the last
const PieceLayer: React.FC<{ p: Piece; layer: 'stage' | 'screen'; props: ShotProps }> = ({ p, layer, props }) => {
  const C = layer === 'stage' ? p.def.stage : p.def.screen;
  if (!C) return null;
  const inner = { ...props, shot: C4E[p.old] };
  const plain = !p.freeze && (p.rate ?? 1) === 1 && p.play === undefined;
  return (
    <Sequence from={p.at} durationInFrames={p.len} layout="none">
      {plain ? <Sequence from={-(p.from ?? 0)} layout="none"><C {...inner} /></Sequence> : <Remap p={p}><C {...inner} /></Remap>}
    </Sequence>
  );
};
const Remap: React.FC<{ p: Piece; children: React.ReactNode }> = ({ p, children }) => {
  const f = useCurrentFrame(); const from = p.from ?? 0; const n = p.freeze ?? 0;
  let o: number;
  if (f < n) o = p.freezeAt ?? 0;
  else { const u = (f - n) * (p.rate ?? 1); o = from + Math.floor(p.play !== undefined ? Math.min(u, p.play - 1) : u); }
  return <Freeze frame={o}>{children}</Freeze>;
};

export const pieces = (ps: Piece[]): ShotDef => {
  const hasScreen = ps.some((p) => p.def.screen);
  return {
    stage: (props) => <>{ps.map((p, i) => <PieceLayer key={i} p={p} layer="stage" props={props} />)}</>,
    screen: hasScreen ? (props) => <>{ps.map((p, i) => <PieceLayer key={i} p={p} layer="screen" props={props} />)}</> : undefined,
  };
};

/** a cut-4e shot playing as is, but against its old shot object (its cues/frames), optionally offset */
export const asOld = (def: ShotDef, old: string, len: number, from = 0, freeze = 0, freezeAt = 0): ShotDef =>
  pieces([{ def, old, at: 0, len, from, freeze, freezeAt }]);

export type Cam = { s: number; x?: number; y?: number; ox?: number; oy?: number }; // scale about (ox, oy) of the stage (0..1), then translate px
export const camera = (def: ShotDef, fn: (f: number, dur: number) => Cam): ShotDef => ({
  ...def,
  stage: (props) => {
    const f = useCurrentFrame(); const c = fn(f, props.shot.dur); const S = def.stage;
    return (
      <AbsoluteFill style={{ overflow: 'hidden' }}>
        <AbsoluteFill style={{ transform: `translate(${(c.x ?? 0).toFixed(2)}px, ${(c.y ?? 0).toFixed(2)}px) scale(${c.s.toFixed(5)})`, transformOrigin: `${((c.ox ?? 0.5) * 100).toFixed(2)}% ${((c.oy ?? 0.5) * 100).toFixed(2)}%` }}>
          <S {...props} />
        </AbsoluteFill>
      </AbsoluteFill>
    );
  },
});

/** inOut cubic 0..1 over [a, b] frames */
export const ioc = (f: number, a: number, b: number) => {
  const t = Math.min(1, Math.max(0, (f - a) / Math.max(1, b - a)));
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
};
