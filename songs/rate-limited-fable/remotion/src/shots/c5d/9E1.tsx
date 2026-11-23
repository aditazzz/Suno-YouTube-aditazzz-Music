// rl5_d cut 5 9E1, THE hero beat (CUT5_PLAN §3 9E1 + §5 D; her C08 "Cooper should be flying off when she's on the vibration plate",
// N41 "Cooper should fly off around here", N44 "cooper should fly off the plate at the same time as the party streamers come out of the
// TV at the Outlook news"). 9A's camera. Beat 4593 (local 0): the Outlook headline flashes on the TV (rl5_c's layer). Beat 4610 (local
// 17): streamers + the clay guests burst out of the TV and, the SAME frame, Cooper is launched off the plate: 4-frame squash before,
// ~22 frames airborne on a parabola with one full turn, stretched along the path, shutter-sample blur; lands on the sofa with a
// squash, one small bounce and a settle. She wobbles, arms out, mask askew. 2% push with the burst.
// Layers from rl5_a2 (public/c5/9E1/, contract in workers/rl5_d/STATUS.md); every frame a pure function of the frame.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam } from '../first30/kit';
import { lerp } from '../../ease';
import { Confetti } from '../s09/_party';

export type Box = { x: number; y: number; w: number; h: number };
export type L9 = { cooper_braced: Box; cooper_squash: Box; cooper_air: Box; cooper_landed?: Box; land: [number, number]; tv_quad: [number, number][] };
export const BURST = 17;               // 4610 - 4593
const SQUASH = 4;                      // frames of crouch before the launch
// rl5_d3: CUT5_PLAN §7 fallback taken (the spinning, shutter-blurred cutout read pasted on at full size: ribbed smear, ghosts):
// three held poses on three beats: launch (squash, beat 4610 lead-in), mid-air (A2's air pose where A2 rendered it, beat 4610),
// landed on the sofa (beat 4628). Each hold drifts a little so it's alive; the burst carries the motion.
export const HELD = true;
const AIR = HELD ? 18 : 22;            // airborne frames (HELD: one beat, 4610 -> 4628)
const LAND = BURST + AIR;              // touches the sofa
let D = 'c5/9E1/';
const im = (n: string) => staticFile(D + n);
const cubicInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const cl = (t: number) => Math.min(1, Math.max(0, t));

/** Cooper's state at (fractional) shot-local frame t: which cutout, its centre (stage px), rotation (deg), scale x/y along/against the path */
export const cooperAt = (L: L9, t: number) => {
  const b = L.cooper_braced; const c0: [number, number] = [b.x + b.w / 2, b.y + b.h / 2];
  const feet0: [number, number] = [b.x + b.w / 2, b.y + b.h];
  if (t < BURST - SQUASH) {                    // braced on the plate (the plate's buzz moves him with her: done by the jiggle)
    return { img: 'cooper_braced.png', box: b, cx: c0[0], cy: c0[1], rot: 0, sx: 1, sy: 1, ox: 0.5, oy: 1 };
  }
  if (t < BURST) {                             // anticipation: squash down into the plate
    const k = cubicInOut(cl((t - (BURST - SQUASH)) / SQUASH)); const q = 1 + 0.16 * k;
    const s = L.cooper_squash; return { img: 'cooper_squash.png', box: s, cx: s.x + s.w / 2, cy: s.y + s.h / 2, rot: -4 * k, sx: q, sy: 1 / q, ox: 0.5, oy: 1 };
  }
  const a = L.cooper_air; const land = L.land;
  if (HELD && t < LAND) {                      // the held mid-air pose: a small drift toward the sofa and a slight nose-down tilt
    // ballistic, not floating: constant speed toward the sofa, gravity pulling him down (u^2), the nose tipping down
    const u = cl((t - BURST) / AIR); const dir = Math.sign(land[0] - feet0[0]) || 1;
    return { img: 'cooper_air.png', box: a, cx: a.x + a.w / 2 + dir * lerp(-30, 90, u), cy: a.y + a.h / 2 - 22 + 75 * u * u, rot: dir * lerp(-4, 9, u), sx: 1, sy: 1, ox: 0.5, oy: 0.5 };
  }
  if (t < LAND) {                              // the arc: parabola from his feet on the plate to the sofa cushion, peak well above both
    const u = (t - BURST) / AIR;
    const x = lerp(feet0[0], land[0], u);
    const peak = Math.min(Math.min(feet0[1], land[1]) - 420, a.y + a.h / 2);   // rl5_d2: at least as high as A2's rendered air pose
    // quadratic through (0, y0), (0.5, ~peak), (1, y1)
    const y0 = feet0[1] - a.h / 2, y1 = land[1] - a.h / 2;
    const mid = peak - (y0 + y1) / 2;
    const y = lerp(y0, y1, u) + 4 * mid * u * (1 - u);
    const vx = (land[0] - feet0[0]) / AIR, vy = (y1 - y0) / AIR + 4 * mid * (1 - 2 * u) / AIR;
    const speed = Math.hypot(vx, vy);
    const stretch = 1 + Math.min(0.22, speed / 260) * (u < 0.12 ? u / 0.12 : u > 0.88 ? (1 - u) / 0.12 : 1);
    const dir = Math.sign(land[0] - feet0[0]) || 1;
    return { img: 'cooper_air.png', box: a, cx: x, cy: y, rot: dir * 360 * cubicInOut(u), sx: stretch, sy: 1 / stretch, ox: 0.5, oy: 0.5, pathDeg: Math.atan2(vy, vx) * 180 / Math.PI };
  }
  // landed: squash on contact, one bounce (~8 f), settle by ~16 f
  const d = t - LAND; const lb = L.cooper_landed ?? { x: land[0] - a.w / 2, y: land[1] - a.h, w: a.w, h: a.h };
  const bounceH = d < 9 ? 38 * Math.sin(Math.PI * d / 9) * (d > 2 ? 1 : 0) : d < 14 ? 8 * Math.sin(Math.PI * (d - 9) / 5) : 0;
  const sq = d < 3 ? 1 + 0.2 * Math.sin(Math.PI * d / 3) : d >= 9 && d < 11 ? 1 + 0.07 * Math.sin(Math.PI * (d - 9) / 2) : 1;
  return { img: L.cooper_landed ? 'cooper_landed.png' : 'cooper_air.png', box: lb, cx: lb.x + lb.w / 2, cy: lb.y + lb.h / 2 - bounceH, rot: 0, sx: sq, sy: 1 / sq, ox: 0.5, oy: 1 };
};

const CooperCut: React.FC<{ L: L9; t: number; op: number }> = ({ L, t, op }) => {
  const c = cooperAt(L, t); const bx = c.box;
  // the transform: place the crop's centre at (cx, cy); scale along the path (stretch) then spin
  const along = (c as any).pathDeg as number | undefined;
  const tf = along !== undefined
    ? `translate(${(c.cx - bx.w / 2).toFixed(2)}px, ${(c.cy - bx.h / 2).toFixed(2)}px) rotate(${along.toFixed(2)}deg) scale(${c.sx.toFixed(4)}, ${c.sy.toFixed(4)}) rotate(${(-along + c.rot).toFixed(2)}deg)`
    : `translate(${(c.cx - bx.w / 2).toFixed(2)}px, ${(c.cy - bx.h / 2).toFixed(2)}px) rotate(${c.rot.toFixed(2)}deg) scale(${c.sx.toFixed(4)}, ${c.sy.toFixed(4)})`;
  return <Img src={im(c.img)} style={{ position: 'absolute', left: 0, top: 0, width: bx.w, height: bx.h, opacity: op, transformOrigin: `${c.ox * 100}% ${c.oy * 100}%`, transform: tf }} />;
};

/** shutter-sample motion blur for Cooper while he moves fast (5 samples over half a frame) */
const CooperBlur: React.FC<{ L: L9; f: number }> = ({ L, f }) => {
  const fast = !HELD && f >= BURST - 1 && f < LAND + 2; const N = fast ? 7 : 1, shutter = 0.5;
  return <>{Array.from({ length: N }, (_, i) => <CooperCut key={i} L={L} t={f + (N > 1 ? (i / (N - 1) - 0.5) * shutter : 0)} op={1 / (i + 1)} />)}</>;
};

/** the plate's buzz on her (and on Cooper while braced): 13.5 Hz with shutter blur, like cut 4e's PlateJiggle */
const jig = (g: number, amp: number, lag = 0) => { const ph = 2 * Math.PI * 13.5 * (g / 30) - lag; return [amp * 0.35 * Math.sin(ph * 0.5 + 1.1), amp * Math.sin(ph)]; };
const Jiggle: React.FC<{ g: number; amp: number; lag?: number; children: React.ReactNode }> = ({ g, amp, lag = 0, children }) => (
  <>{Array.from({ length: 5 }, (_, i) => { const [dx, dy] = jig(g + (i / 4 - 0.5) * 0.5, amp, lag); return <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1), transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)` }}>{children}</AbsoluteFill>; })}</>
);

/** the burst out of the TV on BURST: streamers fly from the screen into the room, confetti, the clay guests pop out (party kit) */
const Burst: React.FC<{ L: L9; f: number }> = ({ L, f }) => {
  if (f < BURST) return null;
    return (
    <>
      {/* rl5_d2: code streamers dropped (flat scribbles on the wall read homemade); the burst = rl5_a2's clay guests (Guests) + confetti */}
      <Confetti f={f} bursts={[BURST]} n={40} />
    </>
  );
};

export type Make9E1 = { dir?: string; cam: { cx: number; cy: number; s: number }; L: L9; Tv?: React.FC<{ f: number }>; Guests?: React.FC<{ f: number }>; hair?: boolean };
export const make9E1 = ({ dir, cam, L, Tv, Guests, hair }: Make9E1): ShotDef => ({
  stage: ({ shot }: ShotProps) => {
    if (dir) D = dir;
    const f = useCurrentFrame(); const g = shot.from + f;
    const push = 1 + 0.02 * cubicInOut(cl((f - BURST + 2) / 30));     // the 2% push with the burst
    const amp = f < BURST ? 2.3 : 2.3 * Math.max(0.35, 1 - (f - BURST) / 40);   // the plate keeps buzzing; she fights it
    const wob = f >= BURST;
    // her wobble: a slow sway (arms out) on top of the buzz, decaying
    const sway = wob ? 9 * Math.sin((f - BURST) / 4.2) * Math.exp(-(f - BURST) / 26) : 0;
    return (
      <AbsoluteFill>
        <Cam cx={cam.cx} cy={cam.cy} s={cam.s * push}>
          <Img src={im('clean.jpg')} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
          {Tv ? <Tv f={f} /> : null}
          {Guests ? <Guests f={f} /> : null}
          <Burst L={L} f={f} />
          <Jiggle g={g} amp={amp}>
            <AbsoluteFill style={{ transformOrigin: '50% 80%', transform: `rotate(${(sway * 0.12).toFixed(3)}deg) translateX(${sway.toFixed(2)}px)` }}>
              <Img src={im(wob ? 'her_wobble.png' : 'her_on.png')} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
            </AbsoluteFill>
          </Jiggle>
          {/* curls / pom-pom: rl5_a2's split hair layer, a lagged, bigger jiggle (her_wobble has its hair baked in) */}
          {!wob && hair ? <Jiggle g={g} amp={amp * 1.4} lag={1.3}><Img src={im('her_on_hair.png')} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} /></Jiggle> : null}
          {f < BURST - SQUASH ? <Jiggle g={g} amp={amp * 0.8}><CooperCut L={L} t={f} op={1} /></Jiggle> : <CooperBlur L={L} f={f} />}
        </Cam>
      </AbsoluteFill>
    );
  },
  cx916: () => 0.55,
});

/** rl5_d2: rl5_a2's c5/9E1/layout.json -> L9 (crops.<name> = stage boxes; land; tv_quad) */
export const L9fromA2 = (j: any): L9 => ({
  cooper_braced: j.crops.cooper_braced, cooper_squash: j.crops.cooper_squash, cooper_air: j.crops.cooper_air, cooper_landed: j.crops.cooper_landed,
  land: j.land as [number, number], tv_quad: j.tv_quad as [number, number][],
});

/** rl5_a2's clay guests (crops.guest_N, RGBA at 2x) pop out of the TV on the burst, staggered 2 f: scale 0 -> 1.1 out of the screen
 *  (5 f), then (rl5_d3) hop down out of the screen onto the media console (arc, 9 f; they stood on the ticker and covered the real
 *  headline), a landing squash, then a small bob on the beat. A soft contact shadow under each once down. Console top: y ~1010-1030. */
const CONSOLE = (x: number) => 1012 + (x - 1700) * 0.022;
export const GuestsFrom = (j: any): React.FC<{ f: number }> => ({ f }) => {
  const gs = [1, 2, 3].map((n) => j?.crops?.[`guest_${n}`]).filter(Boolean) as Box[];
  return <>{gs.map((b, i) => {
    const t = f - (BURST + i * 2); if (t < 0) return null;
    const spread = (b.x + b.w / 2 - 1980) * 0.12;                      // they fan out a little as they jump
    const y0 = b.y + b.h; const y1 = CONSOLE(b.x + b.w / 2) + 4;       // feet: screen base -> console top
    let k = 1, dy = 0, dx = 0, sq = 1, sh = 0;
    if (t < 5) { k = 1.1 * cubicInOut(t / 5); }
    else if (t < 14) { const u = (t - 5) / 9; k = lerp(1.1, 1, u); dy = lerp(0, y1 - y0, u * u) - 70 * Math.sin(Math.PI * Math.min(1, u * 1.15)) * (1 - u * 0.4); dx = spread * u; sh = u > 0.7 ? (u - 0.7) / 0.3 : 0; }
    else { const d = t - 14; dy = y1 - y0; dx = spread; sh = 1;
      sq = d < 4 ? 1 + 0.12 * Math.sin(Math.PI * d / 4) : 1;
      dy -= d >= 4 ? 5 * Math.abs(Math.sin(Math.PI * (f - 34.7) / 17.3)) : 0; }
    const cxp = b.x + b.w / 2 + dx;
    return <React.Fragment key={i}>
      {sh > 0 ? <div style={{ position: 'absolute', left: cxp - b.w * 0.42, top: y1 - 10, width: b.w * 0.84, height: 18, borderRadius: '50%',
        background: 'rgba(30,18,10,0.42)', filter: 'blur(5px)', opacity: sh }} /> : null}
      <Img src={im(`guest_${i + 1}.png`)} style={{ position: 'absolute', left: b.x, top: b.y, width: b.w, height: b.h, transformOrigin: '50% 100%',
        transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px) scale(${(k * sq).toFixed(4)}, ${(k / sq).toFixed(4)})` }} />
    </React.Fragment>;
  })}</>;
};
