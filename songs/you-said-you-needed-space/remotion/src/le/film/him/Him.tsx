// The 3D "him" in the film (earth_him_wire, Nov 9): Blender renders of the satellite / his rocket, one RGBA PNG per film frame,
// cropped, placed where the engine draws his spark (living_earth/him3d: him_export.sh -> him_slots.py -> him_post.py).
// The film stays live underneath: only his spark is dimmed (track.ts dimHim), so section work in a hero slot is never covered.
// Only frames listed in manifest.gen.ts are shown, so a render never fails on a clip that is not there yet. Film prop `him: false` = off.
import React from 'react';
import { Img, staticFile } from 'remotion';
import { HIM_CLIPS, HimClip, HimFr } from './manifest.gen';
import { dimHim } from './track';
import { Fmt, Frame } from '../types';
const at = (f: number, fmt: Fmt): { c: HimClip; e: NonNullable<HimFr> }[] => {
  const out: { c: HimClip; e: NonNullable<HimFr> }[] = [];
  for (const c of HIM_CLIPS[fmt] ?? []) { const e = c.fr[f - c.f0]; if (e) out.push({ c, e }); }
  return out;
};
export function himFrame(frame: Frame, f: number, t: number, fmt: Fmt): Frame {
  const cs = at(f, fmt); if (!cs.length) return frame;
  const cover: Record<string, number> = {};
  for (const { c, e } of cs) for (const s of c.slots) cover[s] = Math.max(cover[s] ?? 0, e[4] / 100);
  return dimHim(frame, t, fmt, (s) => cover[s] ?? 0);
}
export const HimLayer: React.FC<{ f: number; fmt: Fmt }> = ({ f, fmt }) => (
  <>
    {at(f, fmt).map(({ c, e }) => (
      <Img key={c.run} src={staticFile(`${c.dir}/h_${String(f).padStart(5, '0')}.png`)}
        style={{ position: 'absolute', left: `${(e[0] / c.res[0]) * 100}%`, top: `${(e[1] / c.res[1]) * 100}%`, width: `${(e[2] / c.res[0]) * 100}%`, height: `${(e[3] / c.res[1]) * 100}%` }} />
    ))}
  </>
);
