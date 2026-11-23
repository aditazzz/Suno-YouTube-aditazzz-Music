// Cut 7 idle life for the shared plates (stage px of the 2560x1440 plate; drawn inside the camera, so they ride every move).
//  Room6Life: c5/6A/room_rain.jpg (two-room wide, 4 AM): neon hum + rare flicker (Live Love / Click Click Ship It), rain on her
//  window, the two candle flames, the phone's screen glow on the yoga block, dust in the lamp light.
import React from 'react';
import { Img, staticFile } from 'remotion';
import { noise1 } from '../../../ease';
import { LOGO } from './logo';
import { Glow, neonBuzz, Rain, Dust, visorK } from './life';

export const NeonFlicker: React.FC<{ abs: number; x: number; y: number; rx: number; ry: number; color: string; seed?: number; avoid?: number[] }> = ({ abs, x, y, rx, ry, color, seed = 2, avoid }) => {
  const b = neonBuzz(abs, seed, avoid);
  return (
    <>
      <Glow x={x} y={y} rx={rx * 1.25} ry={ry * 1.6} color={color} op={0.16 * b} />
      {b < 0.9 ? <div style={{ position: 'absolute', left: x - rx, top: y - ry, width: 2 * rx, height: 2 * ry, borderRadius: '40%', background: 'rgba(20,16,14,1)',
        opacity: (1 - b) * 0.85, mixBlendMode: 'multiply', filter: 'blur(14px)' }} /> : null}
    </>
  );
};
export const Candle: React.FC<{ abs: number; x: number; y: number; seed?: number; size?: number }> = ({ abs, x, y, seed = 1, size = 1 }) => {
  const k = 0.75 + 0.25 * noise1(abs / 2.3, seed) + 0.1 * noise1(abs / 0.9, seed + 3);
  return <Glow x={x} y={y} rx={46 * size} ry={60 * size} color="rgba(255,190,110,0.9)" op={0.32 * k} />;
};
/** her H7.24 (cut 6 frame 3104: "Love love sign could be bigger and if needed it can be three lines / Live love / Click click / Ship
 *  it!"): rl7_logo's 3-line room neon, ~30% of the frame wide, on the wall where the script neon was (painted out of the plate:
 *  c7/relogo/6A/room_rain.jpg, workers/rl7_ra/relogo_room6.py). A live layer, so the hum and flicker dim the tubes and their spill on
 *  the wall together. Stage px of the 2560-wide plate. */
export const ROOM6_NOSIGN = 'c7/apt/6A_room_rain_click.jpg'   // rl7_master: locked room, sign A baked (no live neon);
export const RoomNeon3: React.FC<{ abs: number; x?: number; y?: number; w?: number; seed?: number; avoid?: number[] }> = ({ abs, x = 1644, y = 488, w = 770, seed = 62, avoid }) => {
  const b = neonBuzz(abs, seed, avoid); const h = w / (4096 / 3288);
  return (
    <>
      <Glow x={x} y={y - h * 0.25} rx={w * 0.62} ry={h * 0.32} color="rgba(255,95,168,0.8)" op={0.13 * b} />
      <Glow x={x} y={y} rx={w * 0.66} ry={h * 0.3} color="rgba(69,227,255,0.8)" op={0.12 * b} />
      <Glow x={x} y={y + h * 0.26} rx={w * 0.62} ry={h * 0.32} color="rgba(255,138,61,0.8)" op={0.13 * b} />
      <Img src={staticFile(LOGO.roomNeon)} style={{ position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, opacity: 0.25 + 0.75 * b }} />
    </>
  );
};
export const Room6Life: React.FC<{ abs: number; avoid?: number[] }> = ({ abs, avoid }) => (
  <>
    <Rain abs={abs} x={1032} y={128} w={116} h={430} n={14} op={0.42} scale={0.9} seed={61} />
    {/* rl7_master: sign A is baked into the locked-room plate: no live neon */}
    <Candle abs={abs} x={1947} y={1012} seed={1} size={0.8} />
    <Candle abs={abs} x={1988} y={1040} seed={2} size={0.8} />   {/* rl7_master: the locked-room flames (measured on the plate) */}
    <Glow x={1356} y={1318} rx={70} ry={90} color="rgba(200,220,255,0.8)" op={0.1 + 0.06 * Math.sin(abs / 30 * 2 * Math.PI * 0.25)} />
    <Dust abs={abs} x={2050} y={640} w={340} h={380} n={18} op={0.35} seed={63} />
  </>
);

/** a tube-style neon state (public/c7/neon/*.png, rl7_logo's tubes) as a live layer at stage (x, y), w wide: hum + flicker dim the tubes
 *  and their spill on the wall together. colors: the spill per line, top to bottom. */
export const TubeNeon: React.FC<{ abs: number; src: string; x: number; y: number; w: number; aspect: number; colors: string[]; seed?: number; avoid?: number[]; spill?: number }> = ({ abs, src, x, y, w, aspect, colors, seed = 5, avoid, spill = 0.12 }) => {
  const b = neonBuzz(abs, seed, avoid); const h = w / aspect; const n = colors.length;
  return (
    <>
      {colors.map((c, i) => <Glow key={i} x={x} y={y - h * 0.5 + h * (i + 0.5) / n} rx={w * 0.68} ry={h * 0.75 / n + h * 0.12} color={c} op={spill * b} />)}
      <Img src={staticFile(src)} style={{ position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, opacity: 0.25 + 0.75 * b }} />
    </>
  );
};
const PINK = 'rgba(255,95,168,0.8)', CYAN = 'rgba(69,227,255,0.8)';
/** c6/1D/T1s.jpg (1D master wide, ~2 AM): the room neon LIVE LOVE / MAKE SLOP in the tube style, ~1.5x the old script sign (her H7.5; the
 *  script sign painted out: c7/relogo/1D/T1s.jpg), rain on her window, candles, dust in the lamp light */
export const ROOM1D_NOSIGN = 'c7/apt/1D_T1s_slop.jpg'   // rl7_master: locked room, sign A baked;
export const Room1DLife: React.FC<{ abs: number; avoid?: number[] }> = ({ abs, avoid }) => (
  <>
    {/* rl7_master: no rain layer in 1D: the locked room's window is elsewhere (it fell on her head) */}
    {void PINK}{void CYAN}
    <Candle abs={abs} x={1867} y={975} seed={3} size={0.7} />
    <Candle abs={abs} x={1904} y={1000} seed={4} size={0.7} />
    <Dust abs={abs} x={1930} y={600} w={330} h={360} n={16} op={0.35} seed={73} />
  </>
);

/** a live visor: a soft reflection band sweeping down the glass every ~3.3 s + a faint pulse (visorK: his voice, else idle), clipped to
 *  the glass (a rounded rect, stage px of the plate). K plate: centre (1316, 669), 430 x 200. */
export const VisorSweep: React.FC<{ abs: number; x: number; y: number; w: number; h: number; r?: number; period?: number; seed?: number; k?: number }> = ({ abs, x, y, w, h, r = 90, period = 100, seed = 0, k = 1 }) => {
  const u = ((abs + seed * 37) % period) / period;            // 0..1 through one sweep
  const band = -0.4 + 1.8 * u;                                  // band centre in glass heights
  const op = (u < 0.55 ? 0.11 : 0) * k;
  const pulse = 0.05 * visorK(abs) * k;
  return (
    <div style={{ position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, borderRadius: r, overflow: 'hidden', mixBlendMode: 'screen', pointerEvents: 'none' }}>
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(170,215,255,1)', opacity: pulse }} />
      {op > 0 ? <div style={{ position: 'absolute', left: 0, right: 0, top: (band - 0.18) * h, height: 0.36 * h, opacity: op,
        background: 'linear-gradient(180deg, rgba(255,255,255,0), rgba(235,245,255,1) 50%, rgba(255,255,255,0))', transform: 'skewY(-8deg)' }} /> : null}
    </div>
  );
};
