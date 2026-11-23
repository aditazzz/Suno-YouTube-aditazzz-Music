// rl_secc: the shared kit for sections 10-13 (shots 10A..13E). Pure functions of the frame.
// Plates: every plate path is in PL (one swap per plate when the finals land; see build/sections/rl_secc/PLACEHOLDERS.md).
// Positions are measured on each still's layout.json (tworoom p2 layouts at their delivery size) and scaled to the stage.
import { c5p } from '../c5d/plates';   // rl5_d2: cut 5 plate swaps
import { has } from '../c7/kit/trans';
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { clamp, inOutCubic, lerp, noise1, outCubic } from '../../ease';
import { FONT } from '../../theme';
import { beatPulse, timeOf } from '../../timing';
import { SignFace, SIGN } from '../first30/S2A';
import { pendulum } from '../first30/kit';

/** plates (placeholders marked; swap the path when the final lands) */
export const PL = {
  D1: has('c7/11C/p2/D1_lit.jpg') ? 'c7/11C/p2/D1_lit.jpg' : 'c7/fix3d/11C/D1f.jpg',   // rl7_rb: rl7_p2's lit D1 (her H7.7: the gauge at the film's one spot, the grey clock box out), drop-in. rl7_fixb (wire_11c.py): rl7_fix3d's D1 in her APPROVED room (rust sofa), tally plate gone (H7.30/H7.31); was secc/D1f.jpg,             // rl_stills S7 D1 FINAL (4320 px; same camera as the p2 draft, rl_swaps Nov 15)
  T3: 'secc/S5.jpg',              // PLACEHOLDER S5 draft (him at the desk): stands in for T24/T25/T28 until S21q/r/u land
  T3a: 'secc/T3a_f.jpg', T3s: 'secc/T3s_f.jpg', T3b: 'secc/T3b_f.jpg',  // S5 T3 stamp FINALS (rl_stills, 2880 px)
  T5: 'secc/T5a_f.jpg',           // S9 T5a FINAL (parcel uncovered on his desk; same camera as the draft)
  T5s: 'secc/T5s_f.jpg', T5d: 'secc/T5d_f.jpg',   // S9 T5 smear + covered with the RESERVED 4B card baked in (finals)
  C3: 'secc/C3_f.jpg',            // S8 C3 FINAL (his eyes to the clock)
  CAT_YAWN: 'secc/cat_yawn_head.png', // S7 cat_yawn at layout cat_region, masked to the pixels the yawn changes (the region's glass tone differs)
  MASTER: 'secc/master.jpg',      // tworoom master draft
  NS5: 'secc/ns5.jpg',            // street sunrise_dawncam (= S20 NS5, the DAWN camera before sunrise)
  DAWN: 'secc/dawn2.jpg',         // build/sets/dawn/final2/dawn.png (same camera as NS5: mean diff 6.7/255)
  DOOR: 'cutfix/door_rain_al.jpg', // rl_cutfix: the Rain door (door_r3) aligned to the old door.jpg stage; was plates/door.jpg (old her)
  CLOSE: 'plates/close.jpg',
  METER: 'plates/meter.jpg',
  M1: 'first30/M1.jpg', M1N: 'first30/M1_needle.png',
  B2B: 'cutfix/room_b2b_rain.jpg',   // rl_cutfix: approved Rain B2B (same camera)
  ROUTINE: 'cutfix/room_routine_rain.jpg',   // rl_cutfix: approved Rain routine (same camera)
  // rl_cut1 C (Nov 15): the finished stills (build/stills/<ID>/, layout.json each), copies in public/cut1/c/
  T22: 'cut1/c/T22.jpg',                                   // S21p her wall flat-on, 5760x2430 (10A)
  H2a: 'cut1/c/H2a.jpg', H2b: 'cut1/c/H2b.jpg', H2bDawn: 'cut1/c/H2b_dawn.jpg',   // S12 master camera, 3840 (10B, 11A wipe, 12E)
  T24a: 'cut1/c/T24a.jpg', T24s: 'cut1/c/T24s.jpg', T24b: 'cut1/c/T24b.jpg',     // S21q seated -> smear -> standing (11A)
  T25a: 'cut1/c/T25a.jpg', T25s: 'cut1/c/T25s.jpg', T25b: 'cut1/c/T25b.jpg', T25bLit: 'cut1/c/T25b_lit.jpg', // S21r dimmer (11C)
  D8: 'cut1/c/D8.jpg',                                     // S21s mail slot, her side (11D)
  D5: 'cut1/c/D5.jpg',                                     // S10 D5 the Rain door at 2x with the headroom, 3200x2987 (11E)
  T27: 'cut1/c/T27.jpg',                                   // S21t lobby clock close, no hands, 4320 (12F, 12I)
  PREDAWN: 'cut1/c/predawn.jpg',                           // S20 NS5 before sunrise (12H)
  SUN: ['sun_0_sign', 'sun_1_roof', 'sun_2_F5', 'sun_3_F4', 'sun_4_F3', 'sun_5_F2', 'sun_6_F1', 'sun_7_street'].map((n) => `cut1/c/${n}.jpg`), // 13B
  T28a: 'cut1/c/T28a.jpg', T28b: 'cut1/c/T28b.jpg',        // S21u glass full / empty (13C)
  T29a: 'cut1/c/T29a.jpg', T29f: 'cut1/c/T29f.jpg', T29s: 'cut1/c/T29s.jpg', T29c: 'cut1/c/T29c.jpg', // S19 her laptop, morning (13E)
};

/** an RGBA/region layer placed at its box in ORIGINAL plate px (k = stage px per plate px) */
export const Lay: React.FC<{ src: string; k: number; x: number; y: number; w: number; h: number; style?: React.CSSProperties }> = ({ src, k, x, y, w, h, style }) => (
  <Img src={staticFile(src)} style={{ position: 'absolute', left: x * k, top: y * k, width: w * k, height: h * k, ...style }} />
);
/** the master-camera lobby clock (TR_cam_master layout: pivot 320.8, 260.9 at 2880; face r ~72): code hands only */
export const MASTER_CLOCK = { cx: 320.8 * (2560 / 2880), cy: 260.9 * (2560 / 2880), r: 58 };

/** S7 (D1) layout px (4320 wide) -> stage */
export const K7 = 2560 / 4320;
export const s7 = (x: number, y: number): [number, number] => [x * K7, y * K7];
export const D1 = {
  leaf: [s7(1338.5, 419.0), s7(2981.5, 419.0), s7(2981.5, 2336.7), s7(1338.5, 2336.7)] as [number, number][],
  deadbolt: s7(2860.8, 1335.8), chain: s7(3000.0, 975.0), floor: s7(2907.0, 2142.7),
  slot: { x0: 2299.8 * K7, y0: 1947.2 * K7, x1: 2628.7 * K7, y1: 2039.8 * K7 },
  digital: [s7(2529.2, 948.3), s7(2808.2, 948.3), s7(2808.2, 1055.0), s7(2529.2, 1055.0)] as [number, number][],
  catRegion: [1611 * K7, 17 * K7, (2275 - 1611) * K7, (783 - 17) * K7] as [number, number, number, number],
  catHead: s7(1735, 175), catLids: [s7(1702.2, 154.4), s7(1758.6, 154.4)],
  head: s7(2182.3, 1505.4 - 520),
};

/** a still filling the stage */
export const Pl: React.FC<{ src: string; filter?: string; opacity?: number; style?: React.CSSProperties }> = ({ src, filter, opacity = 1, style }) => (
  <Img src={staticFile(c5p(src))} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, filter, opacity, ...style }} />
);

/** the 0.6% kick pulse (grammar 2), as a scale factor; off in the dead-still shots */
export const pulse = (g: number, on = true) => (on ? 1 + 0.006 * beatPulse(timeOf(g), 0.16) : 1);

/** local frame of a grid time */
export const gl = (shot: { from: number; grid?: number[] }, i: number, fallback: number) => {
  const t = shot.grid?.[i]; return t == null ? fallback : Math.round(t * 30) - shot.from;
};

/** the lobby wall clock, close (T27 stand-in): brass rim, cream face, ticks and numerals; hands are always code.
 *  sec = seconds of the minute for the second hand (null = none); min = minutes past the hour; hr = hour 0..12 */
export { PandaWallClockCompat as WallClock } from '../../blocks/PandaClock';

/** the shop sign on the glass, flipping either way: from 'back' to 'open' (or reverse) through zero in 5 frames,
 *  then a damped pendulum swing. scale = sign size relative to the 2A sign. */
export const FlipSign: React.FC<{ f: number; flipAt: number; from: 'open' | 'back'; x: number; hookY: number; top: number; scale?: number; swing?: number; idle?: number }> = ({ f, flipAt, from, x, hookY, top, scale = 1, swing = 12, idle = 0 }) => {
  const to = from === 'open' ? 'back' : 'open';
  const k = clamp((f - flipAt) / 5);
  const ang = pendulum(f, flipAt + 2, swing, 22, 2.0) + idle * Math.sin(f / 19);
  const face = (kk: number) => {
    const q = clamp(kk); const sx = Math.abs(Math.cos(Math.PI * q)); const side = q < 0.5 ? from : to;
    return (
      <div style={{ position: 'absolute', left: 0, top: 0, width: SIGN.w, height: SIGN.h, transform: `scaleX(${Math.max(0.02, sx)})`, filter: `brightness(${0.75 + 0.25 * sx})` }}>
        <SignFace side={side} />
      </div>
    );
  };
  return (
    <div style={{ position: 'absolute', left: x, top: hookY, width: 0, height: 0, transformOrigin: '0 0', transform: `rotate(${ang.toFixed(3)}deg) scale(${scale})` }}>
      <svg width={SIGN.w} height={top - hookY + 40} style={{ position: 'absolute', left: -SIGN.w / 2, top: 0, overflow: 'visible' }}>
        <path d={`M ${SIGN.w / 2} 0 L ${SIGN.w * 0.2} ${top - hookY + 12} M ${SIGN.w / 2} 0 L ${SIGN.w * 0.8} ${top - hookY + 12}`} stroke="#3a3328" strokeWidth={5} fill="none" />
        <circle cx={SIGN.w / 2} cy={4} r={16} fill="#8a8f96" />
      </svg>
      <div style={{ position: 'absolute', left: -SIGN.w / 2, top: top - hookY, width: SIGN.w, height: SIGN.h }}>
        {k > 0 && k < 1 ? <>{[-0.3, 0, 0.3].map((dt, i) => <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}>{face(k + dt / 5)}</AbsoluteFill>)}</> : face(k)}
      </div>
    </div>
  );
};

/** a glass of water (a drinking glass, side view); level 0..1, wobble in px */
export const WaterGlass: React.FC<{ x: number; y: number; w: number; level?: number; wobble?: number; ring?: number; blur?: number }> = ({ x, y, w, level = 0.78, wobble = 0, ring = 0, blur = 0 }) => {
  const h = w * 1.45;
  return (
    <div style={{ position: 'absolute', left: x - w / 2, top: y - h, width: w, height: h, filter: blur ? `blur(${blur}px)` : undefined }}>
      {ring > 0 ? <div style={{ position: 'absolute', left: -w * 0.05, top: h - w * 0.12, width: w * 1.1, height: w * 0.24, borderRadius: '50%', border: `${w * 0.03}px solid rgba(120,95,60,${0.35 * ring})` }} /> : null}
      <div style={{ position: 'absolute', left: w * 0.04, top: h - w * 0.1, width: w * 0.92, height: w * 0.2, borderRadius: '50%', background: 'rgba(0,0,0,0.25)', filter: 'blur(4px)' }} />
      <div style={{ position: 'absolute', inset: 0, clipPath: `polygon(0 0, 100% 0, 92% 100%, 8% 100%)`, background: 'linear-gradient(90deg, rgba(220,232,236,0.38), rgba(255,255,255,0.10) 35%, rgba(255,255,255,0.05) 65%, rgba(220,232,236,0.42))' }}>
        {level > 0 ? (
          <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: `${level * 92}%`, background: 'linear-gradient(180deg, rgba(170,205,215,0.55), rgba(120,170,185,0.5))' }}>
            <div style={{ position: 'absolute', left: 0, right: 0, top: -w * 0.04 + wobble, height: w * 0.08, borderRadius: '50%', background: 'rgba(225,240,244,0.55)' }} />
          </div>
        ) : null}
        <div style={{ position: 'absolute', left: w * 0.14, top: h * 0.08, width: w * 0.08, height: h * 0.78, borderRadius: w, background: 'rgba(255,255,255,0.35)' }} />
      </div>
      <div style={{ position: 'absolute', left: 0, top: -w * 0.06, width: w, height: w * 0.12, borderRadius: '50%', border: `${Math.max(2, w * 0.025)}px solid rgba(235,242,244,0.6)` }} />
    </div>
  );
};

/** her coffee mug (side view) */
export const Mug: React.FC<{ x: number; y: number; w: number; blur?: number; steam?: number; g?: number }> = ({ x, y, w, blur = 0, steam = 0, g = 0 }) => {
  const h = w * 1.05;
  return (
    <div style={{ position: 'absolute', left: x - w / 2, top: y - h, width: w * 1.35, height: h, filter: blur ? `blur(${blur}px)` : undefined }}>
      <div style={{ position: 'absolute', left: 0, top: h - w * 0.1, width: w, height: w * 0.2, borderRadius: '50%', background: 'rgba(0,0,0,0.3)', filter: 'blur(5px)' }} />
      <div style={{ position: 'absolute', left: w * 0.82, top: h * 0.22, width: w * 0.42, height: h * 0.5, borderRadius: '45%', border: `${w * 0.1}px solid #c96a3c` }} />
      <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: h, borderRadius: `${w * 0.08}px ${w * 0.08}px ${w * 0.2}px ${w * 0.2}px`, background: 'linear-gradient(90deg,#a9512a,#e07f4c 40%,#c86638 70%,#8c4020)' }} />
      <div style={{ position: 'absolute', left: w * 0.03, top: -w * 0.06, width: w * 0.94, height: w * 0.16, borderRadius: '50%', background: 'radial-gradient(ellipse, #3b2414 55%, #e8a27a 60%)' }} />
      {steam > 0 ? [0, 1].map((i) => (
        <div key={i} style={{ position: 'absolute', left: w * (0.3 + 0.3 * i) + 6 * noise1(g / 20, i), top: -h * 0.7, width: w * 0.12, height: h * 0.6, borderRadius: w, opacity: 0.18 * steam,
          background: 'linear-gradient(0deg, rgba(255,255,255,0.9), rgba(255,255,255,0))', filter: 'blur(6px)' }} />
      )) : null}
    </div>
  );
};

/** falling 2D confetti (pure function of g) over a w x h area */
export const Confetti: React.FC<{ g: number; w?: number; h?: number; n?: number; seed?: number; opacity?: number }> = ({ g, w = 2560, h = 1440, n = 70, seed = 3, opacity = 1 }) => {
  const cols = ['#e2533a', '#f2c14e', '#3ddc84', '#4c7de0', '#f1ece0', '#e07fb0'];
  return (
    <div style={{ position: 'absolute', inset: 0, opacity, pointerEvents: 'none' }}>
      {Array.from({ length: n }, (_, i) => {
        const r = (k: number) => { const v = Math.sin((i + 1) * 12.9898 + k * 78.233 + seed) * 43758.5453; return v - Math.floor(v); };
        const speed = 2.2 + 2.6 * r(1), x0 = r(2) * w, period = (h + 200) / speed;
        const t = (g + r(3) * period) % period; const y = -100 + t * speed;
        const x = x0 + 40 * Math.sin(g / (14 + 10 * r(4)) + r(5) * 6);
        const spin = g * (4 + 8 * r(6)) + r(7) * 360; const sz = 14 + 14 * r(8);
        return <div key={i} style={{ position: 'absolute', left: x, top: y, width: sz, height: sz * 0.55, background: cols[i % cols.length],
          transform: `rotate(${spin}deg) scaleY(${Math.abs(Math.cos(spin / 40))})`, boxShadow: '0 2px 3px rgba(0,0,0,0.2)' }} />;
      })}
    </div>
  );
};

/** split-flap digit: shows `from` before `at`, flips to `to` over 6 frames (top half falls, bottom half lands) */
export const FlapDigit: React.FC<{ f: number; at: number; from: string; to: string; w: number; h: number; size: number; color?: string; bg?: string }> = ({ f, at, from, to, w, h, size, color = '#2b2416', bg = 'transparent' }) => {
  const k = clamp((f - at) / 6);
  const half = (txt: string, top: boolean) => (
    <div style={{ position: 'absolute', left: 0, top: top ? 0 : h / 2, width: w, height: h / 2, overflow: 'hidden', background: bg }}>
      <div style={{ position: 'absolute', left: 0, top: top ? 0 : -h / 2, width: w, height: h, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: FONT.mono, fontWeight: 700, fontSize: size, color, lineHeight: 1 }}>{txt}</div>
    </div>
  );
  const a1 = clamp(k * 2), a2 = clamp(k * 2 - 1);
  return (
    <div data-fit="off" style={{ position: 'absolute', inset: 0, perspective: 800 }}>
      {half(k < 0.5 ? from : to, true)}{half(k < 1 ? from : to, false)}
      {k > 0 && k < 0.5 ? <div style={{ position: 'absolute', inset: 0, transformOrigin: `50% ${h / 2}px`, transform: `rotateX(${-90 * outCubic(a1)}deg)` }}>{half(from, true)}</div> : null}
      {k >= 0.5 && k < 1 ? <div style={{ position: 'absolute', inset: 0, transformOrigin: `50% ${h / 2}px`, transform: `rotateX(${90 * (1 - outCubic(a2))}deg)` }}>{half(to, false)}</div> : null}
      <div style={{ position: 'absolute', left: 0, top: h / 2 - 1, width: w, height: 2, background: 'rgba(40,30,15,0.35)' }} />
    </div>
  );
};

/** soft first light / lamp light pass: a warm radial light added over the plate */
export const LightPass: React.FC<{ k: number; x: number; y: number; rx: number; ry: number; color?: string; amt?: number }> = ({ k, x, y, rx, ry, color = '255,196,140', amt = 0.5 }) => (
  <div style={{ position: 'absolute', inset: 0, mixBlendMode: 'soft-light', opacity: clamp(k),
    background: `radial-gradient(ellipse ${rx}px ${ry}px at ${x}px ${y}px, rgba(${color},${amt}) 0%, rgba(${color},${amt * 0.35}) 45%, rgba(${color},0) 100%)` }} />
);

export const ez2 = (f: number, a: number, b: number, e: (k: number) => number = inOutCubic) => e(clamp((f - a) / Math.max(1e-6, b - a)));
export { lerp, clamp };
