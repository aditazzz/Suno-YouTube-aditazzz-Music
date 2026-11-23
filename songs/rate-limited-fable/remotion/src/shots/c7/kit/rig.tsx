// Cut 7 rig(): one continuous camera over a whole block (PLAN7 §1 "Move"), drawn over the cut 6 picture of the block (or any
// inner ShotDef), so every block moves from frame 0 to its last frame, across the old shots it merges (a push-through keeps
// its velocity across the inner cut). Identity camera = {cx 1280, cy 720, s 1}; s stays >= 1.0 so no edge ever shows (clamped).
//  keys/opt: kit/cam flow() keys in BLOCK-local frames. hand: hand-held noise; jit: vibration; bumps: beat accents (block-local).
//  dollyIn/dollyOut: WallDolly on the block's first/last n frames. match: Match re-frame on the first n frames.
//  over: drawn inside the camera over the picture (stage px; only where the inner picture's own camera is static or known).
//  top: drawn on top of the block in stage space, outside the camera (vignettes, transitions).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../../types';
import { flow, FlowOpt, handheld, jitter, bumps as bumpsF, Key } from './cam';
import { clampCam, Rig, SliceCam, Mod } from './SliceCam';
import { WallDolly, Match, Feat } from './trans';
import { fallback } from './fallback';
import { Grain2 } from '../../../blocks/real/Scene';

export type RigSpec = {
  keys: Key[]; opt?: FlowOpt;
  hand?: { amp?: number; roll?: number; seed?: number };
  jit?: { amp?: number; seed?: number; from?: number; to?: number };
  bumps?: { at: number[]; amt?: number; len?: number };
  dollyIn?: { n: number; dir: 1 | -1; travel?: number }; dollyOut?: { n: number; dir: 1 | -1; travel?: number };
  /** WallDollies at inner cuts (block-local frame of the cut): out over [at-n, at), in over [at, at+n) */
  dollies?: { at: number; n: number; dir: 1 | -1; travel?: number }[];
  match?: { n: number; a: Feat; b: Feat };
  inner?: ShotDef;
  /** draw a plate through SliceCam instead of an inner def: 2.5D the moment its pack is listed (kit/SliceCam). `over` rides the camera. */
  plate?: { src: string | ((f: number) => string); pack?: string | ((f: number) => string | undefined); ph?: number; depth?: number; focus?: string;
    mods?: (f: number, abs: number) => Record<string, Mod | undefined>; on?: (f: number, abs: number) => Record<string, React.ReactNode> };
  over?: React.FC<{ f: number; abs: number; shot: ShotProps['shot'] }>;
  top?: React.FC<{ f: number; abs: number; shot: ShotProps['shot'] }>;
  screen?: ShotDef['screen'] | null;
  /** cut 6's film grain on top (Grain2), for plate rigs replacing a cut 6 shot that had it */
  grain?: boolean;
  cx916?: ShotDef['cx916'];
  /** extra camera multiplier (e.g. a whip or a designed beat), applied after flow */
  mod?: (f: number) => { dx?: number; dy?: number; ds?: number; r?: number };
};
/** the rig's camera at block-local frame f (exported so overlays / the next block can match it) */
export const rigCam = (r: RigSpec, f: number) => {
  const c = flow(f, r.keys, r.opt);
  let { cx, cy, s, r: roll } = c;
  if (r.bumps) s *= Math.exp(bumpsF(f, r.bumps.at, r.bumps.amt, r.bumps.len));
  if (r.hand) { const h = handheld(f, r.hand.seed, r.hand.amp, r.hand.roll); cx -= h.dx / s; cy -= h.dy / s; roll += h.r; }
  if (r.jit && f >= (r.jit.from ?? -1e9) && f < (r.jit.to ?? 1e9)) { const j = jitter(f, r.jit.seed, r.jit.amp); cx -= j.dx / s; cy -= j.dy / s; }
  if (r.mod) { const m = r.mod(f); cx -= (m.dx ?? 0) / s; cy -= (m.dy ?? 0) / s; s *= 1 + (m.ds ?? 0); roll += m.r ?? 0; }
  return clampCam({ cx, cy, s: Math.max(1, s), r: roll });
};
export const rig = (r: RigSpec, shotForFallback?: ShotProps['shot']): ShotDef => {
  const innerOf = (shot: ShotProps['shot']) => r.inner ?? fallback(shotForFallback ?? shot);
  return {
    stage: (p) => {
      const f = useCurrentFrame(); const c = rigCam(r, f); const I = innerOf(p.shot).stage; const Over = r.over, Top = r.top;
      const abs = p.shot.from + f; const P = r.plate;
      let pic: React.ReactNode = P ? (
        <SliceCam plate={typeof P.src === 'function' ? P.src(f) : P.src} pack={typeof P.pack === 'function' ? P.pack(f) : P.pack}
          cam={c} cam0={rigCam(r, 0)} abs={abs} ph={P.ph} depth={P.depth} focus={P.focus} mods={P.mods?.(f, abs)} on={P.on?.(f, abs)}>
          {Over ? <Over f={f} abs={abs} shot={p.shot} /> : null}
        </SliceCam>
      ) : (
        <Rig cam={c}>
          <I {...p} />
          {Over ? <Over f={f} abs={abs} shot={p.shot} /> : null}
        </Rig>
      );
      if (r.match && f < r.match.n) pic = <Match f={f} n={r.match.n} a={r.match.a} b={r.match.b}>{pic}</Match>;
      if (r.dollyIn && f < r.dollyIn.n) pic = <WallDolly f={f} dur={p.shot.dur} n={r.dollyIn.n} dir={r.dollyIn.dir} side="in" travel={r.dollyIn.travel}>{pic}</WallDolly>;
      for (const d of r.dollies ?? []) {
        if (f >= d.at - d.n && f < d.at) pic = <WallDolly f={f - (d.at - d.n)} dur={d.n} n={d.n} dir={d.dir} side="out" travel={d.travel}>{pic}</WallDolly>;
        else if (f >= d.at && f < d.at + d.n) pic = <WallDolly f={f - d.at} dur={d.n} n={d.n} dir={d.dir} side="in" travel={d.travel}>{pic}</WallDolly>;
      }
      if (r.dollyOut && f >= p.shot.dur - r.dollyOut.n) pic = <WallDolly f={f} dur={p.shot.dur} n={r.dollyOut.n} dir={r.dollyOut.dir} side="out" travel={r.dollyOut.travel}>{pic}</WallDolly>;
      return <AbsoluteFill style={{ overflow: 'hidden' }}>{pic}{r.grain ? <Grain2 f={f} /> : null}{Top ? <Top f={f} abs={p.shot.from + f} shot={p.shot} /> : null}</AbsoluteFill>;
    },
    screen: r.screen === null || (r.plate && !r.screen) ? undefined : r.screen ?? ((p) => { const S = innerOf(p.shot).screen; return S ? <S {...p} /> : null; }),
    cx916: r.cx916 ?? (r.plate ? () => 0.5 : (f, shot) => { const d = innerOf(shot); return d.cx916 ? d.cx916(f, shot) : shot.cx916; }),
  };
};
/** a constant-rate push (pct %/s, log space) from (cx, cy, s0) drifting by (dx, dy) stage px over the block: two moving keys */
export const pushKeys = (dur: number, o: { cx?: number; cy?: number; s0?: number; pct?: number; dx?: number; dy?: number; r0?: number; r1?: number }): Key[] => {
  const { cx = 1280, cy = 720, s0 = 1.0, pct = 3, dx = 0, dy = 0, r0 = 0, r1 = 0 } = o;
  return [{ f: 0, cx, cy, s: s0, r: r0 }, { f: dur - 1, cx: cx + dx, cy: cy + dy, s: s0 * Math.pow(1 + pct / 100, (dur - 1) / 30), r: r1 }];
};

/** several rigs inside one block (a PUNCH x3, a teaser): part i runs from its `at` (block-local) with its own keys (local to `at`) */
export const rigs = (parts: (RigSpec & { at: number })[]): ShotDef => {
  const defs = parts.map((p) => ({ at: p.at, d: rig({ ...p, keys: p.keys.map((k) => ({ ...k, f: k.f + p.at })) }) }));
  const pick = (f: number) => { let i = 0; while (i + 1 < defs.length && f >= defs[i + 1].at) i++; return defs[i].d; };
  return {
    stage: (p) => { const f = useCurrentFrame(); const S = pick(f).stage; return <S {...p} />; },
    screen: (p) => { const f = useCurrentFrame(); const S = pick(f).screen; return S ? <S {...p} /> : null; },
    cx916: (f, shot) => { const d = pick(f); return d.cx916 ? d.cx916(f, shot) : shot.cx916; },
  };
};
