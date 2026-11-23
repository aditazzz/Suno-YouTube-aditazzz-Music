// B11 (913-1121) FLOW, PLAN7 row 11 / W5: ONE 3-bar slide on rl5_a1's 2E5 panorama (shelf -> door -> her + FAME under the neon);
// 2F's repeated BACK AT punch-ins are cut (the same sign as 2A 14 s earlier). Cut 6's 2E geometry (5760 x 2200 drawn at 0.72,
// slid 0 -> 1404 stage px) now spans 208 frames, moving at frame 0 and still moving at the last (no ease-in hold), plus a slow
// push (1.0 -> 1.06) and a hair of rise, so the slide has a dolly's weight. Grain as cut 6.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../../types';
import { flow } from '../kit/cam';
import { SliceCam } from '../kit/SliceCam';
import { has } from '../kit/trans';
import { neonBuzz, Glow } from '../kit/life';   // the panorama with the new logo (her H7.1): workers/rl7_ra/relogo_2e5.py

const K = 0.72, PW = 5760 * K, PH = 2200 * K, X = 1950 * K;
const RELOGO = has('c7/relogo/2E/2E5.jpg'); const APT = 'c7/apt/2E5_slop.jpg';   // rl7_master: locked room, sign A baked
// her H7.5 ("make the neon sign bigger for the second line 'make slop'"): the room neon in rl7_logo's tube style (one typeface all night,
// as 6A's LIVE LOVE / CLICK CLICK / SHIP IT!), ~1.45x the old script sign, where it hung (plate px centre 4104, 600), live: hum + flicker
const Neon2E: React.FC<{ abs: number }> = ({ abs }) => {
  const b = neonBuzz(abs, 23); const w = 790 * K, h = w * 2369 / 4096, x = 4104 * K, y = 600 * K;
  return (
    <>
      <Glow x={x} y={y - h * 0.18} rx={w * 0.7} ry={h * 0.42} color="rgba(255,95,168,0.8)" op={0.12 * b} />
      <Glow x={x} y={y + h * 0.2} rx={w * 0.72} ry={h * 0.42} color="rgba(69,227,255,0.8)" op={0.12 * b} />
      <Img src={staticFile('c7/neon/live_love_make_slop.png')} style={{ position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, opacity: 0.25 + 0.75 * b }} />
    </>
  );
};
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const n = shot.dur - 1;
  // x: 0 -> X with moving ends (start at 40% of the mean speed, end at 60%)
  const v = X / n;
  const c = flow(f, [{ f: 0, cx: 0, cy: 0, s: 1.0 }, { f: n * 0.5, cx: X * 0.52, cy: -6, s: 1.03 }, { f: n, cx: X, cy: -12, s: 1.06 }],
    { v0: { cx: 0.4 * v, cy: 0, s: 0.0002 }, v1: { cx: 0.6 * v, cy: -0.05, s: 0.0003 } });
  return (
    <AbsoluteFill style={{ background: '#140d09', overflow: 'hidden' }}>
      <AbsoluteFill style={{ transformOrigin: '1280px 720px', transform: `scale(${c.s.toFixed(5)})` }}>
        <div style={{ position: 'absolute', left: 0, top: -30 + c.cy, width: PW, height: PH, transform: `translateX(${(-c.cx).toFixed(2)}px)` }}>
          <Img src={staticFile(APT)} style={{ position: 'absolute', left: 0, top: 0, width: PW, height: PH }} />
          {RELOGO && false ? <Neon2E abs={shot.from + f} /> : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
void SliceCam;
export const B11: ShotDef = { stage: Stage, cx916: (f, shot) => 0.35 + 0.3 * (f / Math.max(1, shot.dur - 1)) };
