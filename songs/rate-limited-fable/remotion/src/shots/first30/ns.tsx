// rl_first30_v3 (CD V3 order 2): the REAL night street (rl_stills_street finals), replacing the graded-dawn stand-in in
// 1A/1B (NS1 tall 5760x5400), 1C (NS2 tall 5760x8640, flat-on) and 1H (NS2 whole 4320x2430, night -> grey).
// Every beat stays code on top of the plates, keyed exactly as before:
//   windows   NS1 plate_dark + the 40 lit-window crops of plate_lit (rect composite = exact; the wave/tenants as v1/v2)
//   sign      BUILD PASSING: sign_add.png (sign_on_region minus plate_lit), added with plus-lighter; opacity = the flicker
//   clock     hands only, in code (the renders have the hands removed), hour .64 r / minute .95 r like the 3D clock
//   tail      tail.png rotated about its pivot (a 2D rotation is exact: the tail lies in a plane parallel to the image)
//   fg        NS1 fg.png (lit lamp at the left edge, branch upper right, defocused) replaces the code branch
//   1H        whole_night with whole_grey revealed floor by floor (top first) on the five eighths; the sign drains
// All positions from the stills' layout.json (copied into assets.json by build/first30/tools/prep_v3.py).
import { c5p } from '../c5d/plates';   // rl5_d2: cut 5 plate swaps (rl5_b facade patches)
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { clamp } from '../../ease';
import { Tenant, WinState } from './street';
import assets from './assets.json';
import l5 from './l5.json';
import { PostPanda, pxPerM } from './l5clock';

const NSA = ((assets as any).NS ?? {}) as Record<string, any>;
export const HAVE_NS1 = !!NSA.NS1;
export const HAVE_NS2T = !!NSA.NS2t;
export const HAVE_NS2W = !!NSA.NS2w;
const N1 = NSA.NS1, N2T = NSA.NS2t, N2W = NSA.NS2w;
export const K1 = N1 ? 2560 / N1.size[0] : 1;
export const NS1_PH = N1 ? N1.size[1] * K1 : 1440;           // 2400: NS1 in stage px is 2560 x 2400
export const K2T = N2T ? 2560 / N2T.size[0] : 1;
export const NS2T_PH = N2T ? N2T.size[1] * K2T : 1440;       // 3840
export const K2W = N2W ? 2560 / N2W.size[0] : 1;
export const NS1_FG = !!N1?.fg;

// rl7_ra: P1's roof sign (SHIP IT! neon) light, lit minus unlit, at its own region (c7/street/NS1_sign_add.json)
import { has } from '../c7/kit/trans';
import signAddJson from '../../../public/c7/street/p2/NS1_sign_add.json';   // rl7_sign2: the bigger roof sign's region (p2 png + json land together)
import s2SignJson from '../../../public/c7/street/p2/NS2_whole_sign.json';   // rl7_sign2: 1H sign-drain box of the bigger roof sign
const NEW_SIGN = has('c7/street/NS1_sign_add.png');
const NEW_SIGN_REGION = (signAddJson as any).region_px_5760x5400 as number[];
const abs = (b: number[], k: number): React.CSSProperties => ({ position: 'absolute', left: b[0] * k, top: b[1] * k, width: (b[2] - b[0]) * k, height: (b[3] - b[1]) * k });

/** clock hands only (the plate has the face); minutes like AnalogClock (only the angles matter) */
export const Hands: React.FC<{ cx: number; cy: number; r: number; minutes: number }> = ({ cx, cy, r, minutes }) => {
  const total = minutes + 18 * 60; const hA = ((total / 60) % 12) * 30, mA = (total % 60) * 6;
  const hand = (deg: number, len: number, wd: number) => <line x1={0} y1={len * 0.14} x2={0} y2={-len} stroke="#1d1b18" strokeWidth={wd} strokeLinecap="round" transform={`rotate(${deg.toFixed(2)})`} />;
  return (
    <svg data-fit="off" width={2 * r} height={2 * r} viewBox={`${-r} ${-r} ${2 * r} ${2 * r}`} style={{ position: 'absolute', left: cx - r, top: cy - r, overflow: 'visible' }}>
      {hand(hA, r * 0.64, r * 0.075)}{hand(mA, r * 0.95, r * 0.05)}<circle r={r * 0.07} fill="#1d1b18" />
    </svg>
  );
};
const clockOf = (c: any, k: number) => ({ cx: c.pivot[0] * k, cy: c.pivot[1] * k, r: Math.abs(c.points_12_3_6_9[1][0] - c.pivot[0]) * k });
// rl_l5_street (round 4, §2a one clock): the post clock is the PANDA face (l5clock.tsx) over the old plain face, same hands spec as the
// Blender renders; `minutes` here is minutes since 6 PM (the old Hands convention), the face takes minutes past midnight.
const PANDA = true;
const ClockHands: React.FC<{ c: any; k: number; minutes: number | ((dt: number) => number) }> = ({ c, k, minutes }) => {
  const p = clockOf(c, k);
  if (PANDA) {
    const pp = { cx: p.cx, cy: p.cy, ppm: pxPerM(c) * k };
    if (typeof minutes === 'number') return <PostPanda {...pp} minutes={minutes + 18 * 60} />;
    return <>{[-0.4, -0.2, 0, 0.2, 0.4].map((dt, i) => <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}><PostPanda {...pp} minutes={minutes(dt) + 18 * 60} /></AbsoluteFill>)}</>;
  }
  if (typeof minutes === 'number') return <Hands {...p} minutes={minutes} />;
  return <>{[-0.4, -0.2, 0, 0.2, 0.4].map((dt, i) => <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}><Hands {...p} minutes={minutes(dt)} /></AbsoluteFill>)}</>;
};
/** rl_l5_street (her 1C note "Hard to read terminal place"): the gilded transom address, a region re-render of the same camera
 *  (build/stills/L5_1C) feathered over the plate; `filter` greys it with the building in 1H */
const L5A = ((l5 as any).addr ?? {}) as Record<string, { region: number[]; file: string }>;
export const Gilded: React.FC<{ tag: 'ns1' | 'ns2t' | 'ns2w'; k: number; filter?: string }> = ({ tag, k, filter }) => {
  const a = L5A[tag]; if (!a) return null;
  return <Img src={staticFile(a.file)} style={{ ...abs(a.region, k), filter }} />;
};

/** rl_fix2_open (WATCH nit 1A/1B: the tail read as a brown blob at phone size): the night render lifted to a warm ginger so its
 *  rings read, with a soft warm fur rim against the sky. Max channel stays ~200 (no clipping). 1H's grey droop is unchanged. */
const TAIL_LOOK = 'brightness(1.6) saturate(1.2) contrast(1.12) drop-shadow(0 0 10px rgba(255,176,104,0.4))';
/** the tail RGBA rotated about its pivot. theta = the code's swing (deg, + = tip to screen right, as street.tsx Tail);
 *  the layer convention is + = low end to screen LEFT, rendered at `rendered` deg -> CSS rotate(-theta - rendered) */
const TailLayer: React.FC<{ file: string; t: any; k: number; theta: number; css?: number; filter?: string }> = ({ file, t, k, theta, css, filter }) => {
  const r = t.region as number[]; const piv = t.pivot as number[];
  const rot = css ?? (-theta - (t.rendered_swing_deg ?? 0));     // css = a rotation relative to the render itself
  return (
    <Img src={staticFile(file)} style={{ ...abs(r, k), transformOrigin: `${((piv[0] - r[0]) * k).toFixed(2)}px ${((piv[1] - r[1]) * k).toFixed(2)}px`,
      transform: `rotate(${rot.toFixed(3)}deg)`, filter }} />
  );
};

const Parcels: React.FC<{ rect: number[]; k: number; p: number[] }> = ({ rect, k, p }) => {
  const b = abs(rect, k); const h = b.height as number, w = b.width as number;
  return (
    <div style={{ ...b, overflow: 'hidden' }}>
      {p.map((u, i) => u > 0 && u < 1 ? (
        <div key={i} style={{ position: 'absolute', left: -0.3 * w + u * 1.45 * w, top: h * 0.70, width: h * 0.17, height: h * 0.13, borderRadius: 2,
          background: 'linear-gradient(180deg,#b88a56,#8a6238)', boxShadow: '0 3px 4px rgba(0,0,0,0.35)', filter: 'blur(0.6px)', opacity: 0.92 }}>
          <div style={{ position: 'absolute', left: '40%', top: 0, width: '16%', height: '100%', background: 'rgba(80,50,25,0.45)' }} />
        </div>
      ) : null)}
    </div>
  );
};

/** NS1, the tall night street (1A/1B). Stage space 2560 x 2400 (frame 0 = y 960..2400). */
export const NS1Scene: React.FC<{
  g: number; win: WinState; sign: number; clockMin: number | ((dt: number) => number); tailAngle: (u: number) => number;
  parcels?: number[]; tail?: boolean; fgOff?: number; tailLift?: number;
}> = ({ g, win, sign, clockMin, tailAngle, parcels = [], tail = true, fgOff = 0, tailLift = 0 }) => {
  const ten = (N1.tenants ?? {}) as Record<string, { code_index: number }>;
  const tenOf = (i: number) => Object.entries(ten).find(([, v]) => v.code_index === i)?.[0] as 'merge' | 'cursor' | 'shutdown' | undefined;
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: NS1_PH }}>
      <Img src={staticFile(c5p('first30/NS1/plate_dark.jpg'))} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: NS1_PH }} />
      {(N1.windows as { i: number; box: number[]; file: string }[]).map((w) => {
        const L = clamp(win(w.i).lit); if (L < 0.005) return null;
        const t = tenOf(w.i); const b = abs(w.box, K1);
        return (
          <div key={w.i} style={{ ...b, opacity: L }}>
            <Img src={staticFile(w.file)} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} />
            {t ? <div style={{ position: 'absolute', inset: 0, opacity: 0.85 }}><Tenant kind={t} w={b.width as number} h={b.height as number} g={g} /></div> : null}
          </div>
        );
      })}
      <Gilded tag="ns1" k={K1} />
      {sign > 0.005 ? <Img src={staticFile(NEW_SIGN ? (has('c7/street/p2/NS1_sign_add.png') ? 'c7/street/p2/NS1_sign_add.png' : 'c7/street/NS1_sign_add.png') : 'first30/NS1/sign_add.png')} style={{ ...abs(NEW_SIGN ? NEW_SIGN_REGION : N1.sign_region, K1), mixBlendMode: 'plus-lighter', opacity: clamp(sign) } as any} /> : null}
      <ClockHands c={N1.clock} k={K1} minutes={clockMin} />
      {N1.lobby_glass ? <Parcels rect={N1.lobby_glass} k={K1} p={parcels} /> : null}
      {tail && N1.tail_file && N1.tail ? <div style={{ position: 'absolute', inset: 0, transform: tailLift ? `translateY(${(-tailLift).toFixed(2)}px)` : undefined }}>
        <TailLayer file="first30/NS1/tail.png" t={N1.tail} k={K1} theta={tailAngle(0.5)} filter={TAIL_LOOK} /></div> : null}
      {/* frame-0 glow (CD order 2, on the real plate): soft halos on the two street lamps (heads measured in plate_lit), a faint
          city glow over the roofline; screen blend, so the lamp heads (247) can't clip */}
      {[[1114, 4788], [4016, 4803]].map(([x, y], i) => (
        <div key={i} style={{ position: 'absolute', left: x * K1 - 110, top: y * K1 - 110, width: 220, height: 220, borderRadius: '50%', mixBlendMode: 'screen',
          background: 'radial-gradient(circle, rgba(255,214,150,0.30) 0%, rgba(255,200,130,0.12) 32%, rgba(255,190,120,0.04) 60%, rgba(0,0,0,0) 75%)' }} />
      ))}
      <div style={{ position: 'absolute', left: 0, top: 2700 * K1, width: 2560, height: 800 * K1, mixBlendMode: 'screen',
        background: 'linear-gradient(180deg, rgba(90,90,140,0) 0%, rgba(120,104,130,0.10) 60%, rgba(140,110,110,0) 100%)' }} />
      {N1.fg ? <Img src={staticFile('first30/NS1/fg.png')} style={{ position: 'absolute', left: 0, top: fgOff, width: 2560, height: NS1_PH }} /> : null}
      {N1.fg ? <div style={{ position: 'absolute', left: 775 * K1 - 300, top: 3335 * K1 - 300 + fgOff, width: 600, height: 600, borderRadius: '50%', mixBlendMode: 'screen',
        background: 'radial-gradient(circle, rgba(255,210,150,0.22) 0%, rgba(255,196,128,0.08) 35%, rgba(0,0,0,0) 70%)' }} /> : null}
    </div>
  );
};

/** NS2 tall, flat-on (1C): all forty lit with their x, the sign on, 1 TERMINAL PLACE in brass on the transom. 2560 x 3840. */
export const NS2TScene: React.FC<{ clockMin: number }> = ({ clockMin }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: NS2T_PH }}>
    <Img src={staticFile(c5p('first30/NS2/tall_night.jpg'))} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: NS2T_PH }} />
    <Gilded tag="ns2t" k={K2T} />
    <ClockHands c={N2T.clock} k={K2T} minutes={clockMin} />
  </div>
);
export const NS2T = N2T;

/** NS2 whole (1H): the floors go grey top to bottom (floorK[row] 0 = night .. 1 = grey, row 0 = top floor), the sign drains
 *  (signGrey 0..1), the tail droops (theta), and at the end the sky/exposure cross-fades (endK). Without the grey still the
 *  floors darken and the sign desaturates in code (stand-in until whole_grey lands). */
// rl7_final: storeGrey (0..1) drains the storefront SHIP IT! / WE SHIP WORLDWIDE sign on its own (plate px box below), so 1H's lights-out reads
const STORE = [1865, 1632, 2452, 1940];
export const NS2WScene: React.FC<{ floorK: number[]; signGrey: number; endK: number; theta: number; clockMin: number; droop?: number; storeGrey?: number }> = ({ floorK, signGrey, endK, theta, clockMin, droop, storeGrey = 0 }) => {
  const fl = ((N2W.floors?.floors ?? []) as { floor_from_bottom: number; y_top: number; y_bottom: number }[]).slice().sort((a, b) => b.floor_from_bottom - a.floor_from_bottom);
  const fx = (N2W.floors?.facade_x ?? [0, N2W.size[0]]) as number[];
  const grey = N2W.grey ? 'first30/NS2/whole_grey.jpg' : null;
  const ss = ((s2SignJson as any).structure ?? N2W.sign?.structure ?? [0, 0, N2W.size[0], 200]) as number[];
  const sr = [ss[0] - 40, Math.max(0, ss[1] - 40), ss[2] + 40, ss[3] + 40];      // the sign and its own glow only (the region would grey the top floor early)
  const full: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };
  const band = (y0: number, y1: number) => `inset(${(y0 * K2W).toFixed(1)}px ${(2560 - fx[1] * K2W).toFixed(1)}px ${(1440 - y1 * K2W).toFixed(1)}px ${(fx[0] * K2W).toFixed(1)}px)`;
  return (
    <AbsoluteFill>
      <Img src={staticFile(c5p('first30/NS2/whole_night.jpg'))} style={full} />
      {fl.map((f, row) => {
        const k = clamp(floorK[row] ?? 0); if (k < 0.005) return null;
        return grey ? <Img key={row} src={staticFile(c5p(grey))} style={{ ...full, opacity: k, clipPath: band(f.y_top, f.y_bottom) }} />
          : <div key={row} style={{ ...full, opacity: k, clipPath: band(f.y_top, f.y_bottom), background: 'rgba(28,34,48,0.72)', mixBlendMode: 'multiply' }} />;
      })}
      {signGrey > 0.005 ? (grey ? <Img src={staticFile(c5p(grey))} style={{ ...full, opacity: clamp(signGrey), clipPath: `inset(${sr[1] * K2W}px ${2560 - sr[2] * K2W}px ${1440 - sr[3] * K2W}px ${sr[0] * K2W}px)` }} />
        : <Img src={staticFile(c5p('first30/NS2/whole_night.jpg'))} style={{ ...full, opacity: clamp(signGrey), filter: 'grayscale(1) brightness(0.55)', clipPath: `inset(${sr[1] * K2W}px ${2560 - sr[2] * K2W}px ${1440 - sr[3] * K2W}px ${sr[0] * K2W}px)` }} />) : null}
      {grey && storeGrey > 0.005 ? <Img src={staticFile(c5p(grey))} style={{ ...full, opacity: clamp(storeGrey), clipPath: `inset(${(STORE[1] * K2W).toFixed(1)}px ${(2560 - STORE[2] * K2W).toFixed(1)}px ${(1440 - STORE[3] * K2W).toFixed(1)}px ${(STORE[0] * K2W).toFixed(1)}px)` }} /> : null}
      {grey && endK > 0.005 ? <Img src={staticFile(c5p(grey))} style={{ ...full, opacity: clamp(endK) }} /> : null}
      <Gilded tag="ns2w" k={K2W} filter={endK > 0.005 ? `grayscale(${clamp(endK).toFixed(3)}) brightness(${(1 - 0.35 * clamp(endK)).toFixed(3)})` : undefined} />
      <ClockHands c={N2W.clock} k={K2W} minutes={clockMin} />
      {N2W.tail_file && N2W.tail ? <TailLayer file="first30/NS2/whole_tail.png" t={N2W.tail} k={K2W} theta={theta} css={droop !== undefined ? -droop : undefined} /> : null}
    </AbsoluteFill>
  );
};
