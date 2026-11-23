// rl_first30_v3 (CD order 2, v1's frame-0 note): the night street's glow, so frame 0 lifts. Lamp halos (a soft bloom and
// a faint cone of light under each lamp), a sky haze over the roofline (city glow, cool above, warm low), and an out-of-focus
// CC0 branch in the foreground (tree_small_02 silhouette, build/first30/tools/branch_silhouette.py). The warm windows stay
// the brightest things in frame: the haze and halos are kept under the windows' level (no clipped highlights).
// Halos are drawn in stage px (they ride the camera); the branch is frame-fixed and moves 1.3x the camera for depth.
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { STREET } from './street';

export const SkyHaze: React.FC<{ k?: number }> = ({ k = 1 }) => {
  const f = STREET.facade;
  return (
    <>
      <div style={{ position: 'absolute', left: 0, top: -400, width: 2560, height: f.y0 + 700, opacity: k, mixBlendMode: 'screen',
        background: 'linear-gradient(180deg, rgba(40,48,92,0) 0%, rgba(58,66,118,0.22) 55%, rgba(132,104,120,0.20) 85%, rgba(150,110,100,0) 100%)' }} />
      <div style={{ position: 'absolute', left: f.x0 - 500, top: f.y0 - 260, width: f.x1 - f.x0 + 1000, height: 520, opacity: 0.55 * k, mixBlendMode: 'screen',
        borderRadius: '50%', background: 'radial-gradient(ellipse at 50% 60%, rgba(150,120,130,0.30) 0%, rgba(110,96,130,0.12) 45%, rgba(0,0,0,0) 72%)' }} />
    </>
  );
};

export const LampHalos: React.FC<{ k?: number }> = ({ k = 1 }) => (
  <>
    {STREET.lamps.map(([x, y], i) => (
      <React.Fragment key={i}>
        {/* bloom: a wide soft disc and a tighter ring of scatter */}
        <div style={{ position: 'absolute', left: x - 330, top: y - 330, width: 660, height: 660, borderRadius: '50%', mixBlendMode: 'screen', opacity: k,
          background: 'radial-gradient(circle, rgba(236,196,140,0.30) 0%, rgba(220,170,110,0.14) 30%, rgba(200,150,100,0.05) 55%, rgba(0,0,0,0) 72%)' }} />
        {/* the cone of light falling to the pavement (haze in the air), narrow at the lamp head */}
        <div style={{ position: 'absolute', left: x - 260, top: y + 10, width: 520, height: 1180 - y + 140, opacity: 0.35 * k, mixBlendMode: 'screen',
          clipPath: 'polygon(44% 0%, 56% 0%, 100% 100%, 0% 100%)',
          background: 'linear-gradient(180deg, rgba(240,196,130,0.22) 0%, rgba(240,190,120,0.08) 60%, rgba(240,190,120,0.03) 100%)', filter: 'blur(18px)' }} />
      </React.Fragment>
    ))}
  </>
);

/** foreground branch, frame-fixed: off = vertical parallax in px (the caller passes 1.3x the camera's move) */
export const FgBranch: React.FC<{ off: number; fmt: string; cx916?: number }> = ({ off, fmt, cx916 = 0.5 }) => {
  // 16:9: in from the top-right corner. 9:16: in from the top-right of the crop (crop = 0.316 of the stage width)
  const w = fmt === '9x16' ? 900 : 1500, h = w * 1600 / 2400;
  const right = fmt === '9x16' ? (cx916 + 0.158) * 2560 + 60 : 2560 + 90;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      <Img src={staticFile('first30/fg/branch.png')} style={{ position: 'absolute', left: right - w, top: -150 + off, width: w, height: h, filter: 'blur(7px)', opacity: 0.96 }} />
    </AbsoluteFill>
  );
};
