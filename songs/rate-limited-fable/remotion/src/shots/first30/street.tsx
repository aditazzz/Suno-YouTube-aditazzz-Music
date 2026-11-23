// rl_first30: the night street (1A, 1B, 1C, 1H). Everything here is keyed to a STREET layout in stage px, so the plate
// swap (NS1/NS2 from rl_street/rl_stills, overnight) = new src + new layout numbers, nothing else.
// PLACEHOLDER: the approved dawn street (`dawn.jpg`) graded to night in code; the 40 windows, the rooftop BUILD PASSING
// sign, the street clock, the lobby glow and the tail are code layers measured on that plate.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { clamp, lerp, noise1 } from '../../ease';
import { FONT } from '../../theme';
import { AnalogClock } from '../../blocks/Clock';
import { H, PlateImg, W, flick, flickOut } from './kit';
import { LampHalos, SkyHaze } from './glow';

const K = 4 / 3; // dawn.jpg is 1920x1080
// windows measured on dawn.jpg (1920 px): [y, x, h, w], 5 rows x 8 columns, top row first
const RAW: [number, number, number, number][] = [
  [190, 636, 85, 64], [199, 728, 84, 61], [208, 817, 83, 60], [217, 904, 82, 60], [226, 989, 80, 56], [234, 1071, 79, 57], [242, 1150, 79, 56], [250, 1227, 78, 55],
  [307, 632, 86, 63], [315, 724, 85, 64], [322, 815, 84, 61], [330, 904, 82, 60], [337, 989, 82, 59], [344, 1072, 80, 55], [350, 1152, 80, 54], [357, 1230, 79, 57],
  [427, 627, 88, 65], [434, 721, 86, 63], [439, 814, 86, 60], [445, 903, 84, 60], [451, 990, 83, 57], [457, 1074, 81, 54], [462, 1155, 80, 53], [467, 1234, 80, 57],
  [552, 623, 90, 65], [556, 718, 88, 63], [561, 812, 87, 60], [565, 903, 85, 57], [569, 990, 84, 56], [573, 1076, 83, 54], [576, 1158, 83, 55], [580, 1238, 82, 53],
  [679, 620, 87, 64], [682, 716, 86, 63], [685, 811, 84, 60], [687, 903, 83, 57], [689, 991, 82, 57], [691, 1077, 81, 56], [694, 1161, 76, 54], [696, 1242, 74, 53],
];
export const STREET = {
  plate: 'plates/dawn.jpg', placeholder: true,
  windows: RAW.map(([y, x, h, w]) => ({ x: x * K, y: y * K, w: w * K, h: h * K })),
  door: { x: 1178, y: 1073, w: 230, h: 194 },        // the lobby glass
  roof: { x: 1262, y: 196, rot: 5.5 },                // sign base centre on the roofline
  clock: { cx: 1566, cy: 905, r: 46, post: [1566, 951, 1296] as [number, number, number] },
  lamps: [[551, 350], [1716, 368]] as [number, number][],
  tailPivot: [300, -330] as [number, number],
  facade: { x0: 770, x1: 1755, y0: 150, y1: 1270 },
  tenants: { merge: 10, cursor: 21, shutdown: 25 },  // window indices
};
export const NIGHT_GRADE = 'brightness(0.52) saturate(0.8) contrast(1.06) hue-rotate(-8deg)';

/** order of the window wave: from the lobby outward */
const LOBBY: [number, number] = [1293, 1170];
export const WAVE_ORDER = STREET.windows.map((w, i) => [i, Math.hypot(w.x + w.w / 2 - LOBBY[0], (w.y + w.h / 2 - LOBBY[1]) * 1.2)] as [number, number])
  .sort((a, b) => a[1] - b[1]).map(([i]) => i);

const TINTS = ['linear-gradient(180deg, #ffd9a0 0%, #f7b96c 70%, #e39a52 100%)', 'linear-gradient(180deg, #fff0cf 0%, #f6d39a 75%, #e4b574 100%)',
  'linear-gradient(180deg, #ffcf8f 0%, #f0a85c 70%, #d98b45 100%)', 'linear-gradient(180deg, #e9f0f2 0%, #cfdde0 70%, #b5c6cb 100%)', 'linear-gradient(180deg, #ffe2b0 0%, #f4c27d 70%, #e2a35e 100%)'];
export type WinState = (i: number) => { lit: number; tint?: string };

const Blinds: React.FC<{ w: number; h: number }> = ({ w, h }) => (
  <svg width={w} height={h} style={{ position: 'absolute', inset: 0 }}>
    {Array.from({ length: 9 }, (_, j) => <line key={j} x1={0} x2={w} y1={(j + 0.5) * h / 9} y2={(j + 0.5) * h / 9} stroke="rgba(120,70,30,0.28)" strokeWidth={1.6} />)}
  </svg>
);

/** tenant silhouettes behind lit blinds (BOARDS 1B): Merge Conflict, Spinning Cursor, Graceful Shutdown */
export const Tenant: React.FC<{ kind: 'merge' | 'cursor' | 'shutdown'; w: number; h: number; g: number }> = ({ kind, w, h, g }) => {
  const sil = 'rgba(38,22,14,0.82)';
  const t = g / 30;
  if (kind === 'merge') {
    const a1 = 25 + 35 * Math.sin(t * 9), a2 = -20 - 35 * Math.sin(t * 8 + 1.3);
    const fig = (x: number, arm: number, flip: number, bob: number) => (
      <g transform={`translate(${x},${h * 0.98 + bob})`}>
        <ellipse cx={0} cy={-h * 0.62} rx={w * 0.075} ry={w * 0.09} fill={sil} />
        <path d={`M ${-w * 0.1} 0 L ${-w * 0.08} ${-h * 0.5} Q 0 ${-h * 0.55} ${w * 0.08} ${-h * 0.5} L ${w * 0.1} 0 Z`} fill={sil} />
        <line x1={0} y1={-h * 0.46} x2={flip * w * 0.2} y2={-h * 0.46} stroke={sil} strokeWidth={w * 0.045} strokeLinecap="round" transform={`rotate(${arm * flip} 0 ${-h * 0.46})`} />
      </g>
    );
    return <svg width={w} height={h} style={{ position: 'absolute', inset: 0 }}>{fig(w * 0.3, a1, 1, 2 * Math.sin(t * 9))}{fig(w * 0.7, a2, -1, 2 * Math.sin(t * 8 + 2))}</svg>;
  }
  if (kind === 'cursor') {
    const ph = t * 2.6; const x = w * (0.5 + 0.28 * Math.sin(ph)); const sc = 0.88 + 0.12 * Math.cos(ph);
    return (
      <svg width={w} height={h} style={{ position: 'absolute', inset: 0 }}>
        <g transform={`translate(${x},${h * 0.98}) scale(${sc})`}>
          <ellipse cx={0} cy={-h * 0.62} rx={w * 0.075} ry={w * 0.09} fill={sil} />
          <path d={`M ${-w * 0.1} 0 L ${-w * 0.08} ${-h * 0.5} Q 0 ${-h * 0.55} ${w * 0.08} ${-h * 0.5} L ${w * 0.1} 0 Z`} fill={sil} />
        </g>
      </svg>
    );
  }
  const br = 1 + 0.04 * Math.sin(t * 2.2);
  return (
    <svg width={w} height={h} style={{ position: 'absolute', inset: 0 }}>
      <rect x={w * 0.08} y={h * 0.74} width={w * 0.84} height={h * 0.08} rx={4} fill={sil} />
      <g transform={`translate(${w * 0.5},${h * 0.74}) scale(1,${br})`}>
        <ellipse cx={-w * 0.26} cy={-h * 0.06} rx={w * 0.075} ry={w * 0.07} fill={sil} />
        <path d={`M ${-w * 0.18} 0 Q ${-w * 0.1} ${-h * 0.16} ${w * 0.32} ${-h * 0.07} L ${w * 0.32} 0 Z`} fill={sil} />
      </g>
    </svg>
  );
};

export const Windows: React.FC<{ state: WinState; g: number; xmarks?: boolean; tenants?: boolean }> = ({ state, g, xmarks = false, tenants = true }) => (
  <>
    {STREET.windows.map((w, i) => {
      const st = state(i); const L = clamp(st.lit);
      const ten = tenants ? (Object.entries(STREET.tenants).find(([, j]) => j === i)?.[0] as 'merge' | 'cursor' | 'shutdown' | undefined) : undefined;
      return (
        <div key={i} style={{ position: 'absolute', left: w.x, top: w.y, width: w.w, height: w.h, background: '#141a2b', borderRadius: 2,
          boxShadow: L > 0.05 ? `0 0 ${18 * L}px ${6 * L}px rgba(255,190,110,${0.18 * L})` : undefined }}>
          <div style={{ position: 'absolute', inset: 0, opacity: L, borderRadius: 2, filter: 'brightness(0.9)',
            background: st.tint ?? TINTS[(i * 7 + 3) % TINTS.length] }}>
            {ten ? <><Blinds w={w.w} h={w.h} /><Tenant kind={ten} w={w.w} h={w.h} g={g} /></> : null}
            {xmarks ? (
              <svg width={w.w} height={w.h} style={{ position: 'absolute', inset: 0 }}>
                <g stroke="rgba(90,45,20,0.75)" strokeWidth={3} strokeLinecap="round">
                  <line x1={w.w - 17} y1={9} x2={w.w - 8} y2={18} /><line x1={w.w - 8} y1={9} x2={w.w - 17} y2={18} />
                </g>
              </svg>
            ) : null}
          </div>
          {/* the window frame mullion keeps the plate's look */}
          <div style={{ position: 'absolute', left: '46%', top: '18%', width: '8%', height: '48%', background: 'rgba(20,24,40,0.55)', opacity: 0.6 }} />
        </div>
      );
    })}
  </>
);

/** BUILD PASSING on the roof. on = 0..1 lit, green = 1 green / 0 drained grey */
export const RoofSign: React.FC<{ on: number; green?: number }> = ({ on, green = 1 }) => {
  const { x, y, rot } = STREET.roof; const L = clamp(on);
  const col = `rgb(${Math.round(lerp(150, 84, green))},${Math.round(lerp(150, 234, green))},${Math.round(lerp(150, 140, green))})`;   // capped: no channel clips
  return (
    <div data-fit="off" style={{ position: 'absolute', left: x, top: y, transform: `translate(-50%, -100%) rotate(${rot}deg)`, transformOrigin: '50% 100%' }}>
      {/* rails */}
      <div style={{ position: 'absolute', left: 30, right: 30, bottom: 0, height: 24, borderLeft: '5px solid #20232c', borderRight: '5px solid #20232c' }} />
      <div style={{ position: 'relative', bottom: 22, padding: '6px 22px', border: '4px solid #262a35', borderRadius: 8, background: 'rgba(12,14,20,0.85)',
        fontFamily: FONT.head, fontWeight: 900, fontSize: 78, letterSpacing: '0.04em', whiteSpace: 'nowrap',
        color: L > 0.05 ? col : '#3a3f48', opacity: 0.55 + 0.45 * L,
        textShadow: L > 0.05 ? `0 0 ${6 * L}px ${col}, 0 0 ${22 * L}px ${col}, 0 0 ${60 * L}px ${col}99` : 'none' }}>
        BUILD PASSING
      </div>
    </div>
  );
};

/** the green light the sign throws on the cornice and the top two floors */
export const SignLight: React.FC<{ k: number; green?: number }> = ({ k, green = 1 }) => {
  const { x0, x1, y0 } = STREET.facade; const c = green > 0.5 ? '93,255,154' : '160,170,170';
  return <div style={{ position: 'absolute', left: x0 - 40, top: y0 - 60, width: x1 - x0 + 80, height: 420, mixBlendMode: 'screen', opacity: clamp(k) * 0.55,
    background: `radial-gradient(ellipse 60% 70% at 50% 0%, rgba(${c},0.55) 0%, rgba(${c},0.12) 55%, rgba(${c},0) 100%)` }} />;
};

export const StreetClock: React.FC<{ minutes: number }> = ({ minutes }) => {
  const c = STREET.clock;
  return (
    <>
      <div style={{ position: 'absolute', left: c.post[0] - 7, top: c.post[1], width: 14, height: c.post[2] - c.post[1], background: 'linear-gradient(90deg,#1b1e26,#3a3f4c,#1b1e26)' }} />
      <div style={{ position: 'absolute', left: c.cx - c.r - 6, top: c.cy - c.r - 6, width: 2 * c.r + 12, height: 2 * c.r + 12, borderRadius: '50%', background: '#23262f',
        boxShadow: '0 0 30px 8px rgba(255,220,160,0.18)' }} />
      <AnalogClock cx={c.cx} cy={c.cy} r={c.r} minutes={minutes} face="#e4d9bd" ink="#2a2620" hand="#1c1a17" />
    </>
  );
};

export const Lamps: React.FC = () => (
  <>
    {STREET.lamps.map(([x, y], i) => (
      <React.Fragment key={i}>
        <div style={{ position: 'absolute', left: x - 70, top: y - 70, width: 140, height: 140, borderRadius: '50%', mixBlendMode: 'screen',
          background: 'radial-gradient(circle, rgba(236,208,160,0.88) 0%, rgba(236,190,120,0.32) 25%, rgba(255,190,110,0) 70%)' }} />
        <div style={{ position: 'absolute', left: x - 170, top: 1180, width: 340, height: 150, borderRadius: '50%', mixBlendMode: 'screen',
          background: 'radial-gradient(ellipse, rgba(255,200,130,0.22) 0%, rgba(255,200,130,0) 70%)' }} />
      </React.Fragment>
    ))}
  </>
);

/** the lobby glass, lit warm from inside; parcels cross it on the beat (p = list of 0..1 crossing progress) */
export const LobbyGlow: React.FC<{ k?: number; parcels?: number[] }> = ({ k = 1, parcels = [] }) => {
  const d = STREET.door;
  return (
    <>
      <div style={{ position: 'absolute', left: d.x, top: d.y, width: d.w, height: d.h, mixBlendMode: 'screen', opacity: 0.85 * k,
        background: 'linear-gradient(180deg, rgba(255,196,120,0.55), rgba(255,170,90,0.35))' }} />
      <div style={{ position: 'absolute', left: d.x, top: d.y, width: d.w, height: d.h, overflow: 'hidden' }}>
        {parcels.map((p, i) => p > 0 && p < 1 ? (
          <div key={i} style={{ position: 'absolute', left: lerp(-40, d.w + 10, p), top: d.h - 46, width: 34, height: 26, borderRadius: 3,
            background: 'linear-gradient(180deg,#c99a62,#9c7040)', boxShadow: '0 4px 4px rgba(0,0,0,0.35)' }}>
            <div style={{ position: 'absolute', left: 12, top: 0, width: 6, height: 26, background: 'rgba(80,50,25,0.5)' }} />
            <svg width={12} height={10} style={{ position: 'absolute', left: 20, top: 4 }}><path d="M1 5 L4 8 L11 1" stroke="#3ddc84" strokeWidth={2.4} fill="none" /></svg>
          </div>
        ) : null)}
      </div>
    </>
  );
};

/** Cooper's tail hanging into the sky from above frame. angle(u) = the swing angle at fraction u along the tail
 *  (pass a function so the bend can trail the swing). PLACEHOLDER for H3 TAIL (0-2.60 s) and S1's tail RGBA after. */
export const Tail: React.FC<{ angle: (u: number) => number; scale?: number; pivot?: [number, number] }> = ({ angle, scale = 1, pivot = STREET.tailPivot }) => {
  const N = 26, L = 900 * scale;
  const pts: [number, number][] = []; let x = pivot[0], y = pivot[1];
  // rest curve: hangs down, curling toward the tip (a question-mark curl)
  for (let i = 0; i <= N; i++) {
    const u = i / N; pts.push([x, y]);
    const curl = -0.15 + 1.9 * Math.pow(u, 2.2);       // radians off vertical, growing toward the tip
    const a = curl + (angle(u) * Math.PI) / 180;
    x += Math.sin(a) * (L / N); y += Math.cos(a) * (L / N);
  }
  const wid = (u: number) => (64 - 36 * u) * scale * (u > 0.93 ? Math.sqrt(Math.max(0, (1 - u) / 0.07)) * 0.85 + 0.15 : 1);
  const left: string[] = [], right: string[] = [];
  for (let i = 0; i <= N; i++) {
    const [px, py] = pts[i]; const [qx, qy] = pts[Math.min(N, i + 1)]; const [ox, oy] = pts[Math.max(0, i - 1)];
    const tx = qx - ox, ty = qy - oy, tl = Math.hypot(tx, ty) || 1; const nx = -ty / tl, ny = tx / tl; const w = wid(i / N);
    left.push(`${(px + nx * w).toFixed(1)},${(py + ny * w).toFixed(1)}`); right.unshift(`${(px - nx * w).toFixed(1)},${(py - ny * w).toFixed(1)}`);
  }
  const d = `M ${left.join(' L ')} L ${right.join(' L ')} Z`;
  const stripes = [0.18, 0.3, 0.42, 0.54, 0.65, 0.76, 0.86].map((u) => {
    const i = Math.round(u * N); const [px, py] = pts[i]; const [qx, qy] = pts[Math.min(N, i + 1)]; const tx = qx - px, ty = qy - py, tl = Math.hypot(tx, ty) || 1;
    const nx = -ty / tl, ny = tx / tl, w = wid(u) * 1.1;
    return `M ${(px + nx * w).toFixed(1)},${(py + ny * w).toFixed(1)} Q ${(px + tx * 0.8).toFixed(1)},${(py + ty * 0.8).toFixed(1)} ${(px - nx * w).toFixed(1)},${(py - ny * w).toFixed(1)}`;
  });
  return (
    <svg width={W} height={H} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
      <defs>
        <linearGradient id="tailg" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stopColor="#7a3f1c" /><stop offset="0.45" stopColor="#c7743a" /><stop offset="1" stopColor="#6b3416" /></linearGradient>
        <clipPath id="tailc"><path d={d} /></clipPath>
      </defs>
      <path d={d} fill="url(#tailg)" style={{ filter: 'brightness(0.82)' }} />
      <g clipPath="url(#tailc)">{stripes.map((s, i) => <path key={i} d={s} stroke="rgba(70,32,12,0.55)" strokeWidth={16 * scale} fill="none" />)}</g>
      <path d={d} fill="none" stroke="rgba(255,215,170,0.32)" strokeWidth={4} />
    </svg>
  );
};

/** the night street, all layers: plate (graded), lamps, windows, lobby, clock, sign, tail */
export const NightStreet: React.FC<{
  g: number; win: WinState; sign: number; signGreen?: number; signLight?: number; clockMin: number | ((dt: number) => number); tailAngle: (u: number) => number;
  xmarks?: boolean; parcels?: number[]; tail?: boolean;
}> = ({ g, win, sign, signGreen = 1, signLight = 0, clockMin, tailAngle, xmarks, parcels, tail = true }) => (
  <AbsoluteFill>
    <PlateImg src={STREET.plate} filter={NIGHT_GRADE} />
    <AbsoluteFill style={{ background: 'linear-gradient(180deg, rgba(40,52,110,0.75) 0%, rgba(70,84,140,0.55) 55%, rgba(40,46,80,0.6) 100%)', mixBlendMode: 'multiply' }} />
    <SkyHaze k={STREET.placeholder ? 1 : 0.6} />
    <Lamps />
    <LampHalos k={STREET.placeholder ? 1 : 0.5} />
    <Windows state={win} g={g} xmarks={xmarks} />
    <SignLight k={signLight} green={signGreen} />
    <LobbyGlow parcels={parcels} />
    {typeof clockMin === 'number' ? <StreetClock minutes={clockMin} /> : (
      <>{[-0.4, -0.2, 0, 0.2, 0.4].map((dt, i) => <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}><StreetClock minutes={clockMin(dt)} /></AbsoluteFill>)}</>
    )}
    <RoofSign on={sign} green={signGreen} />
    {tail ? <Tail angle={tailAngle} /> : null}
  </AbsoluteFill>
);

/** the hook's window wave: 6 lit at frame 0, 17 / 28 / 40 after each "Mm" (onsets m1..m3, global frames) */
export const waveLit = (g: number, m: number[]): WinState => (i: number) => {
  const rank = WAVE_ORDER.indexOf(i);
  if (rank < 6) return { lit: 1 };
  const groups = [[6, 17, m[0]], [17, 28, m[1]], [28, 40, m[2]]];
  for (const [a, b, at] of groups) if (rank >= a && rank < b) return { lit: flick(g, at + (rank - a) * 1.2) };
  return { lit: 0 };
};
export const flickerWindowOut = flickOut;
export const tailSway = (g: number, u: number) => 4 * Math.sin((g - 3 * u) / 30 * 1.7) + 1.5 * noise1((g - 3 * u) / 20, 3);
