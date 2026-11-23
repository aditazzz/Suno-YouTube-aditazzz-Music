// rl_fix2_robot: the meter (S6 M1, 5760 px) shared by 11B and 13D: needle layer, the GLASSES OF WATER digit cell, the output x helper.
// M1 layout (build/stills/S6_M1/layout.json): pivot 4426.8, 948.8; needle rendered at 20.4; digit box right-aligned at 5070.9.
import React from 'react';
import { FlapDigit, PL, Pl, clamp } from '../s10/_lib';

const K = 2560 / 5760;
export const M1_PIV = { x: 4426.8 * K, y: 948.8 * K };
export const M1_V0 = 20.4;
export const M1_GROUP = { x0: 3630 * K, x1: 5116 * K, y0: 320 * K, y1: 2423 * K, cx: 4373 * K };   // dial rim top .. plates bottom
export const PLATE_TEXT_CX = (3700 * K + 2254) / 2;                                                   // plate text spans stage x ~1644..2254
/** the needle at value v (clockwise on screen as the value rises: angle = 225 - 270 v / 24) */
export const M1Needle: React.FC<{ v: number }> = ({ v }) => (
  <Pl src={PL.M1N} style={{ transformOrigin: `${M1_PIV.x}px ${M1_PIV.y}px`, transform: `rotate(${((270 * (v - M1_V0)) / 24).toFixed(3)}deg)` }} />
);
/** where stage x lands on the 2560-wide output for a Cam at (cx, s) (Cam clamps cx so the plate always fills the frame) */
export const outX = (X: number, cx: number, s: number) => { const hw = 1280 / s; const c = clamp(cx, hw, 2560 - hw); return (X - c) * s + 1280; };
export const DIGIT_BOX = { x: 2186, y: 821, w: 70, h: 82 };   // the digit cell (stage px), right edge on the plate's right-align line
/** the GLASSES OF WATER digit (stage coordinates): flips from -> to at local frame `at` */
export const PlateDigit: React.FC<{ f: number; at: number; from: string; to: string }> = ({ f, at, from, to }) => (
  <div style={{ position: 'absolute', left: DIGIT_BOX.x, top: DIGIT_BOX.y, width: DIGIT_BOX.w, height: DIGIT_BOX.h, filter: 'drop-shadow(0 1px 0 rgba(255,236,180,0.35)) blur(0.4px)' }}>
    <FlapDigit f={f} at={at} from={from} to={to} w={DIGIT_BOX.w} h={DIGIT_BOX.h} size={60} color="#3a3729" />
  </div>
);
