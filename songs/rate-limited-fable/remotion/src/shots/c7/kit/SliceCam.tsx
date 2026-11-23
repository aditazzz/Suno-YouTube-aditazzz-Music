// Cut 7 SliceCam (PLAN7 §2): a plate drawn as N depth slices (lane P1's packs, tools/slice_plate.py) inside one camera; each slice
// moves at its own parallax rate, so a push / truck / arc has real depth. Without a pack it draws the flat plate (the cut 6 look),
// so nothing waits on P1: the same block code becomes 2.5D the moment src/data/c7packs.json lists its pack (tools/c7_packs.py).
//  cam: the camera now; cam0: the reference camera (default: the block's first frame) parallax is measured from.
//  depth: parallax gain (1 = nearest slice moves 25% more than the focus slice per unit of camera travel); focus: the slice that
//  stays locked to the camera (a name, default the slice named her/him, else par 0.5). Relative offsets are soft-clamped to 1.5%
//  of the frame (38 stage px), inside slice_plate's bleed.
//  mods: per slice name, an extra transform (Breathe, Jitter: dx, dy px; sx, sy scale about (ox, oy) in stage px; op opacity).
//  on: per slice name, nodes drawn in that slice's space (a blink patch, a glow riding the character). children: on top, in
//  the base camera (screens, needles, emission passes).
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import packs from '../../../data/c7packs.json';
import { c5p } from '../../c5d/plates';
import { CamK } from './cam';

const W = 2560, H = 1440, LIM = 38;
export type Mod = { dx?: number; dy?: number; sx?: number; sy?: number; ox?: number; oy?: number; op?: number; blur?: number };
type Pack = { w: number; h: number; slices: { src: string; name: string; par: number; bbox?: number[] }[] };
export const PACKS = packs as unknown as Record<string, Pack>;
export const hasPack = (k?: string) => !!(k && PACKS[k]);
const soft = (x: number) => LIM * Math.tanh(x / LIM);

/** idle life by slice name, anchored at the slice's feet (bbox bottom centre, stage px) */
const autoLife = (name: string, bb: number[] | undefined, abs: number): Mod | undefined => {
  if (!bb) return undefined;
  const ox = (bb[0] + bb[2]) / 2, oy = bb[3], t = abs / 30;
  if (name === 'her') { const k = 0.5 + 0.5 * Math.sin(t * 0.22 * 2 * Math.PI); return { sy: 1 + 0.0035 * k, sx: 1 + 0.0009 * k, ox, oy }; }
  if (name === 'cooper') { const k = 0.5 + 0.5 * Math.sin(t * 0.45 * 2 * Math.PI + 1); return { sy: 1 + 0.006 * k, sx: 1 + 0.002 * k, ox, oy }; }
  if (name === 'him') { const k = Math.sin(t * 0.35 * 2 * Math.PI + 2); return { dy: 0.8 * k, ox, oy }; }
  return undefined;
};
/** keep the frame inside the plate (roll needs a little more room) */
export const clampCam = (c: Required<CamK>, ph = H): Required<CamK> => {
  const m = (Math.abs(c.r) * Math.PI / 180) * 1500 + 2;
  const hw = W / 2 / c.s + m / c.s, hh = H / 2 / c.s + m / c.s;
  const cl = (v: number, a: number, b: number) => (a > b ? (a + b) / 2 : Math.min(b, Math.max(a, v)));
  return { ...c, cx: cl(c.cx, hw, W - hw), cy: cl(c.cy, hh, ph - hh) };
};
const camTf = (cx: number, cy: number, s: number, r: number) =>
  `translate(${W / 2}px, ${H / 2}px) rotate(${r.toFixed(4)}deg) scale(${s.toFixed(5)}) translate(${(-cx).toFixed(2)}px, ${(-cy).toFixed(2)}px)`;
const modTf = (m?: Mod) => {
  if (!m) return undefined;
  const ox = m.ox ?? W / 2, oy = m.oy ?? H / 2;
  return `translate(${(m.dx ?? 0).toFixed(2)}px, ${(m.dy ?? 0).toFixed(2)}px) translate(${ox}px, ${oy}px) scale(${(m.sx ?? 1).toFixed(5)}, ${(m.sy ?? 1).toFixed(5)}) translate(${-ox}px, ${-oy}px)`;
};

export const SliceCam: React.FC<{
  plate: string; pack?: string; cam: CamK; cam0?: CamK; depth?: number; focus?: string; ph?: number; noClamp?: boolean;
  mods?: Record<string, Mod | undefined>; on?: Record<string, React.ReactNode>; children?: React.ReactNode; filter?: string;
  /** film frame: when given, character slices (her / cooper breathe, him a slow idle bob) get idle life automatically */
  abs?: number;
}> = ({ plate, pack, cam, cam0, depth = 1, focus, ph = H, noClamp, mods = {}, on = {}, children, filter, abs }) => {
  const c0 = { r: 0, ...cam } as Required<CamK>;
  const c = noClamp ? c0 : clampCam(c0, ph);
  const P = pack ? PACKS[pack] : undefined;
  const base = { position: 'absolute' as const, left: 0, top: 0, width: W, height: ph };
  if (!P) {
    return (
      <AbsoluteFill style={{ overflow: 'hidden', filter }}>
        <AbsoluteFill style={{ transformOrigin: '0 0', transform: camTf(c.cx, c.cy, c.s, c.r) }}>
          <div style={{ ...base, transform: modTf(mods.plate) }}>
            <Img src={staticFile(c5p(plate))} style={{ ...base }} />
            {Object.values(on)}
          </div>
          {children}
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }
  const r0 = { r: 0, ...(cam0 ?? cam) } as Required<CamK>;
  // the camera's pivot depth: a named slice, else the middle of the depth range (offsets split both ways: half the hole-risk of
  // locking the nearest character while the back wall travels)
  const fpar = focus ? P.slices.find((s) => s.name === focus)?.par ?? 0.5 : 0.5;
  const sh = W * P.h / P.w;
  return (
    <AbsoluteFill style={{ overflow: 'hidden', filter }}>
      {P.slices.map((sl, i) => {
        const k = (sl.par - fpar) * depth;
        const fac = Math.exp(Math.max(-0.03, Math.min(0.03, k * 0.25 * (Math.log(c.s) - Math.log(r0.s)))));
        const ex = soft(-k * 0.25 * (c.cx - r0.cx) * c.s), ey = soft(-k * 0.25 * (c.cy - r0.cy) * c.s);
        const sk = c.s * fac, cxk = c.cx - ex / sk, cyk = c.cy - ey / sk;
        const auto = abs !== undefined ? autoLife(sl.name, sl.bbox, abs) : undefined; const m = mods[sl.name] || auto ? { ...auto, ...mods[sl.name] } : undefined;
        return (
          <AbsoluteFill key={i} style={{ transformOrigin: '0 0', transform: camTf(cxk, cyk, sk, c.r), opacity: m?.op ?? 1 }}>
            <div style={{ ...base, height: sh, transform: modTf(m), filter: m?.blur ? `blur(${m.blur}px)` : undefined }}>
              <Img src={staticFile(sl.src)} style={{ position: 'absolute', left: 0, top: 0, width: W, height: sh }} />
              {on[sl.name] ?? null}
            </div>
          </AbsoluteFill>
        );
      })}
      <AbsoluteFill style={{ transformOrigin: '0 0', transform: camTf(c.cx, c.cy, c.s, c.r) }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};
/** a stage-space camera wrapper for anything (a cut 6 shot, a screen): same transform as SliceCam's base, no clamp */
export const Rig: React.FC<{ cam: CamK; children: React.ReactNode }> = ({ cam, children }) => (
  <AbsoluteFill style={{ overflow: 'hidden' }}>
    <AbsoluteFill style={{ transformOrigin: '0 0', transform: camTf(cam.cx, cam.cy, cam.s, cam.r ?? 0) }}>{children}</AbsoluteFill>
  </AbsoluteFill>
);
