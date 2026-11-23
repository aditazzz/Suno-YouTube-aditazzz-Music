// rl_fix2_open: the meter's dial seen very close (1G, 4J), from a FULL-resolution crop of the S6 M1 plate
// (fix2/open/M1_dial2.jpg = S6 px x 3960-5480, y 380-1720; its needle layer M1_dial_needle.png, same crop).
// The framing is in S6 plate px: (cx, cy) at the frame centre, w plate px across the 2560 stage, rotated r deg.
// Twist rule (WATCH 1F/1G/4J): the HOURS AWAKE label (S6 x 4200-4660, y 740-815) and the GLASSES OF WATER / LAST MEAL plates
// (y >= 1800) never enter the frame; build/fix2/open/tools/check_dial.py checks every frame of both shots against them.
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import assets from './assets.json';

const lay = (assets as any).S6_M1_layout;
export const DIAL_CROP = [3960, 380, 5480, 1720];
export const DIAL_PIV: [number, number] = [lay.pivot[0], lay.pivot[1]];          // hub, S6 px
const V0 = lay.needle.rendered_at_value as number;
/** clockwise screen degrees for a needle value (angle = 225 - 270 v / 24, CCW) relative to the rendered layer */
export const dialRot = (v: number) => (270 * (v - V0)) / 24;
/** S6 px of the needle tip for a value (tip ~ 0.72 of the dial radius, 560 px) */
export const dialTip = (v: number): [number, number] => { const a = ((225 - (270 * v) / 24) * Math.PI) / 180; return [DIAL_PIV[0] + 400 * Math.cos(a), DIAL_PIV[1] - 400 * Math.sin(a)]; };

export const DialView: React.FC<{ cx: number; cy: number; w: number; r?: number; v: number; filter?: string; children?: React.ReactNode }> = ({ cx, cy, w, r = 0, v, filter, children }) => {
  const k = 2560 / w; const [x0, y0, x1, y1] = DIAL_CROP;
  return (
    <AbsoluteFill style={{ overflow: 'hidden', background: '#c9a77a' }}>
      <AbsoluteFill style={{ transformOrigin: '0 0', transform: `translate(1280px, 720px) rotate(${r.toFixed(3)}deg) scale(${k.toFixed(5)}) translate(${(-cx).toFixed(2)}px, ${(-cy).toFixed(2)}px)`, filter }}>
        <Img src={staticFile('fix2/open/M1_dial2.jpg')} style={{ position: 'absolute', left: x0, top: y0, width: x1 - x0, height: y1 - y0 }} />
        <Img src={staticFile('fix2/open/M1_dial2_needle.png')} style={{ position: 'absolute', left: x0, top: y0, width: x1 - x0, height: y1 - y0,
          transformOrigin: `${DIAL_PIV[0] - x0}px ${DIAL_PIV[1] - y0}px`, transform: `rotate(${dialRot(v).toFixed(3)}deg)` }} />
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
