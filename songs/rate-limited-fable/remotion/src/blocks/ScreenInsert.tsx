// ScreenInsert: put a flat layer (a PNG from build/screens, or live HTML/JSX) onto a plate with a 4-corner pin, so it
// sits exactly in the phone / laptop / TV / glass in the still. Corners are stage px (2560x1440), in the order
// top-left, top-right, bottom-right, bottom-left, measured on the plate at the camera's REST position: put the insert
// INSIDE the <Plate> (as its child) so it rides the same camera move.
//
//   <Plate src="plates/room_routine.jpg" dur={d} move="push">
//     <ScreenInsert corners={[[1120,610],[1470,600],[1480,830],[1125,845]]} w={1170} h={2532} src="screens/3C_phone.png"
//                   glare={0.12} light={0.9} />
//   </Plate>
//
// w/h are the layer's native size (the PNG's pixels, or the HTML layout box). glare = a soft diagonal sheen (glass);
// light = brightness of the screen so it matches the plate's exposure (no blown highlights: keep <= 1).
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';

export type Pt = [number, number];
export type Quad = [Pt, Pt, Pt, Pt];

/** CSS matrix3d mapping a w x h box (origin top-left) onto the quad (TL, TR, BR, BL) */
export function pinMatrix(q: Quad, w: number, h: number): string {
  const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = q;
  const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3;
  const dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
  let a, b, c, d, e, f, g, hh;
  if (Math.abs(dx3) < 1e-9 && Math.abs(dy3) < 1e-9) {
    a = x1 - x0; b = x3 - x0; c = x0; d = y1 - y0; e = y3 - y0; f = y0; g = 0; hh = 0;
  } else {
    const det = dx1 * dy2 - dx2 * dy1;
    g = (dx3 * dy2 - dx2 * dy3) / det; hh = (dx1 * dy3 - dx3 * dy1) / det;
    a = x1 - x0 + g * x1; b = x3 - x0 + hh * x3; c = x0;
    d = y1 - y0 + g * y1; e = y3 - y0 + hh * y3; f = y0;
  }
  const m = [a / w, d / w, 0, g / w, b / h, e / h, 0, hh / h, 0, 0, 1, 0, c, f, 0, 1];
  return `matrix3d(${m.map((v) => +v.toFixed(9)).join(',')})`;
}
/** linear blend of two quads (k 0..1): animate a pin when the device moves inside a shot */
export const lerpQuad = (a: Quad, b: Quad, k: number): Quad => a.map((p, i) => [p[0] + (b[i][0] - p[0]) * k, p[1] + (b[i][1] - p[1]) * k]) as Quad;

export const ScreenInsert: React.FC<{
  corners: Quad; w: number; h: number; src?: string; children?: React.ReactNode;
  glare?: number; light?: number; opacity?: number; radius?: number;
}> = ({ corners, w, h, src, children, glare = 0, light = 1, opacity = 1, radius = 0 }) => (
  <AbsoluteFill style={{ pointerEvents: 'none' }}>
    <div data-fit="off" style={{ position: 'absolute', left: 0, top: 0, width: w, height: h, transformOrigin: '0 0',
      transform: pinMatrix(corners, w, h), opacity, overflow: 'hidden', borderRadius: radius, filter: light !== 1 ? `brightness(${light})` : undefined }}>
      {src ? <Img src={src.startsWith('/') || src.startsWith('http') ? src : staticFile(src)} style={{ width: w, height: h, display: 'block' }} /> : null}
      {children}
      {glare > 0 ? <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(115deg, rgba(255,255,255,0) 30%, rgba(255,255,255,${glare}) 48%, rgba(255,255,255,0) 62%)` }} /> : null}
    </div>
  </AbsoluteFill>
);
