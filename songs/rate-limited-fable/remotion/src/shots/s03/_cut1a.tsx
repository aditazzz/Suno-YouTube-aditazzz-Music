// rl_cut1 helper A1: the finished stills for 3A 3B 3D 4A 4B 4C 4E 4F 4G (build/stills/<ID>/, copies in public/cut1/a1/),
// their layout.json numbers converted to stage px (2560x1440 = the plate's 16:9 window), and a camera for plates that are
// taller or wider than the stage (S22 D3 is 2560x2560 stage, S14 T9 5200x1440, S10 D5 2560x2389 with 949 px of headroom).
import React from 'react';
import { Img, staticFile } from 'remotion';
import { clamp } from '../../ease';
import { W, H } from './_lib';
import { c5p } from '../c5d/plates';   // rl5_d3: cut-5 plate swaps (same camera)

export const A1 = {
  D3: 'cut1/a1/d3.jpg', D3btn: 'cut1/a1/d3_button.png', D3lamp: 'cut1/a1/d3_lamp.png',                 // S22 (3840 sq)
  T7a: 'cut1/a1/t7a.jpg', T7b: 'cut1/a1/t7b.jpg', T7pad: 'cut1/a1/t7_paddle.png',                       // S21a (T7b's paddle+arm alone, for the smear)
  T8: 'cut1/a1/t8.jpg', T8pen: 'cut1/a1/t8_pen.png',                                                    // S21b (pen = crop at pen_box)
  T9: 'cut1/a1/t9.jpg', T9him1: 'cut1/a1/t9_him1.png',                                                  // S14 (7800 -> 6900 px)
  D5: 'cut1/a1/d5.jpg', D5d4: 'cut1/a1/d5_d4.png', D5cat: 'cut1/a1/d5_cat.png', D5padup: 'cut1/a1/d5_padup.png',                         // S10 full (headroom), 3200 px
  D5e: 'cut1/a1/d5_4e.jpg', D5note: 'cut1/a1/d5_note.png',                                              // S10 approved window + nonote_region, 4864 px
  T10: 'cut1/a1/t10.jpg', T10flap: 'cut1/a1/t10_flap.png', T10half: 'cut1/a1/t10_hand_half.png', T10out: 'cut1/a1/t10_hand_out.png',  // S21c
  H1t1: 'cut1/a1/h1_t1.jpg', H1t2: 'cut1/a1/h1_t2.jpg', H1t4: 'cut1/a1/h1_t4.jpg', H1t4p: 'cut1/a1/h1_t4p.jpg',       // S11 (T6 camera)
};

/** an image placed in stage px (x, y, w, h); optional CSS */
export const Lay: React.FC<{ src: string; x: number; y: number; w: number; h: number; style?: React.CSSProperties }> = ({ src, x, y, w, h, style }) => (
  <Img src={staticFile(c5p(src))} style={{ position: 'absolute', left: x, top: y, width: w, height: h, ...style }} />
);

/** camera numbers for a plate spanning stage x0..x1, y0..y1: clamps (cx, cy) so the frame never shows past it. Pass to Cam with free. */
export const clampCam = (cx: number, cy: number, s: number, x0 = 0, x1 = W, y0 = 0, y1 = H) => {
  const hw = W / 2 / s, hh = H / 2 / s;
  return { cx: clamp(cx, x0 + hw, x1 - hw), cy: clamp(cy, y0 + hh, y1 - hh), s };
};
/** 9:16 crop centre (0..1 of the output) that keeps stage x in view under a camera already clamped (free plates) */
export const c916f = (x: number, cx: number, s: number) => clamp((W / 2 + (x - cx) * s) / W, 0.16, 0.84);

// ---- S10 D5: stage = the approved window (D5 y 2136..5376); k = 2560/5760; the headroom sits above y 0
export const K5 = 2560 / 5760, D5_TOP = -2136 * K5, D5_H = 5376 * K5;
export const d5 = (x: number, y: number): [number, number] => [x * K5, y * K5 + D5_TOP];
/** the door's bottom rail (its lower edge on the floor), measured on D5: y at stage x */
export const railY = (x: number) => 1364.4 - 0.0786 * (x - 667);
