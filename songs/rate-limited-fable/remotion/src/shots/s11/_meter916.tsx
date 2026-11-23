// rl_fix3_qa1: the 9:16 meter framing shared by 11B and 13D (QA3: in 9:16 the payoff digit sat at x ~0.92, in the like
// column, and the LAST MEAL plate reached 72% height). The plate text spans 610 stage px; the safe width of the 9:16
// window (9%..80% of 810 stage px at scale 1) is only 575, so 9:16 frames the meter at s ~0.85-0.91. Below scale 1 the
// 16:9 plate runs out top and bottom, so 9:16 draws fix3/qa1/M1_916col.jpg instead: the same S6 M1 pixels for stage
// x >= 1350 (the 9:16 window never goes left of ~1510), with 120 stage px of mirrored wall above and 300 px of
// mirror-tiled teal wainscot below (both plain, so the seams can't be seen). Free camera (no clamp): stage point
// (cx, cy) goes to the stage centre at scale s; the Film's 9:16 crop is centred (cx916 = 0.5).
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';

export const COL916 = { src: 'fix3/qa1/M1_916col.jpg', left: 3038 / 2.25, top: -120, width: 2722 / 2.25, height: 4185 / 2.25 };
/** plate text centre for 9:16: digit right edge (2256) lands at ~0.79 of the window, GLASSES at ~0.10 */
export const CX916 = 1998, CY916 = 800;
export const MeterCam916: React.FC<{ cx: number; cy: number; s: number; children?: React.ReactNode }> = ({ cx, cy, s, children }) => (
  <AbsoluteFill style={{ transformOrigin: '0 0', transform: `translate(1280px, 720px) scale(${s.toFixed(5)}) translate(${(-cx).toFixed(2)}px, ${(-cy).toFixed(2)}px)` }}>
    <Img src={staticFile(COL916.src)} style={{ position: 'absolute', left: COL916.left, top: COL916.top, width: COL916.width, height: COL916.height }} />
    {children}
  </AbsoluteFill>
);
