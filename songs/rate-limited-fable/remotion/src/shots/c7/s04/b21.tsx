// B21 (1990-2129) FLOW, PLAN7 row 21: her view down the outgoing shelf, long lens: the camera travels parcel to parcel and slows on each
// label (readable >= 1 s each), never stopping; focus breathes (soft in the quick passes, sharp on a label); dust in the light.
// Plate: rl5_b's 3840x1440-on-stage panorama (c5/4H/plate.jpg); P1's relabelled shelf (other people's requests, K9) swaps in when
// public/c7/4H/plate.jpg lands (same camera and size).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../../types';
import { flow, flowV } from '../kit/cam';
import { has } from '../kit/trans';
import { PACKS } from '../kit/SliceCam';
import { Dust } from '../kit/life';
import { Grain2 } from '../../../blocks/real/Scene';

const PW = 3840, PH = 1440, S = 1.24;
const KEYS = [   // slower on each label (readable >= 1 s) but never below ~5 stage px/f + a push on each hold (prev2 gate: 32% still on the dark wood)
  { f: 0, cx: 840, cy: 740, s: S }, { f: 34, cx: 1010, cy: 734, s: S * 1.035 },      // 7C (label centre x 855)
  { f: 52, cx: 1800, cy: 730, s: S * 1.03 }, { f: 84, cx: 2010, cy: 726, s: S * 1.065 },  // 2A (1950)
  { f: 102, cx: 2780, cy: 728, s: S * 1.05 }, { f: 138, cx: 2990, cy: 722, s: S * 1.09 }, // 5F (2955)
];
const Stage: React.FC<ShotProps> = () => {
  const f = useCurrentFrame(); const c = flow(f, KEYS); const v = Math.abs(flowV(f, KEYS).cx);
  const hw = 1280 / c.s, cx = Math.min(PW - hw, Math.max(hw, c.cx));
  const src = has('c7/4H/plate.jpg') ? 'c7/4H/plate.jpg' : 'c5/4H/plate.jpg';
  const blur = Math.min(3.5, Math.max(0, (v - 8) * 0.18));          // defocus in the quick passes only
  const fl = blur > 0.2 ? `blur(${blur.toFixed(2)}px)` : undefined;
  // 2.5D (P1's depth, re-sliced at the depth histogram's valleys: c7/4H/plate_v): the back wall slides behind the boxes as the camera
  // trucks; the boxes (nearest slice) stay locked. 0.025 px per px of travel, soft-limited inside the 64 px bleed.
  const P = PACKS['c7/4H/plate_v'];
  const off = (par: number) => 60 * Math.tanh(((1 - par) * 0.025 * (cx - KEYS[0].cx)) / 60);
  return (
    <AbsoluteFill style={{ background: '#140d09', overflow: 'hidden' }}>
      <AbsoluteFill style={{ transformOrigin: '0 0', transform: `translate(1280px, 720px) scale(${c.s.toFixed(5)}) translate(${(-cx).toFixed(2)}px, ${(-c.cy).toFixed(2)}px)` }}>
        {P && src.startsWith('c7/') ? P.slices.map((sl, i) => (
          <Img key={i} src={staticFile(sl.src)} style={{ position: 'absolute', left: off(sl.par), top: 0, width: PW, height: PH, filter: fl }} />
        )) : <Img src={staticFile(src)} style={{ position: 'absolute', left: 0, top: 0, width: PW, height: PH, filter: fl }} />}
        <Dust abs={1990 + f} x={200} y={120} w={3400} h={520} n={34} op={0.3} seed={21} size={4} />
      </AbsoluteFill>
      <Grain2 f={f} />
    </AbsoluteFill>
  );
};
export const B21: ShotDef = { stage: Stage, cx916: () => 0.5 };
