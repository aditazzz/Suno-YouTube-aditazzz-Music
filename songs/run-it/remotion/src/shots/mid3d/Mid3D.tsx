// THE 3D MIDDLE, s46-s62 (116.21-151.42): rough-cut STAND-INS (blocking-first). Grey-box shapes in three.js keyed to
// the real lands, camera paths as data (./cam/*.json), so the real Blender build reuses the same timing and paths.
// One component for every shot id in the range, so the world never cuts except where the plan cuts (s58 in/out).
// The UI pieces drawn here (pass label, fps readout, calendar, cursor, flying payoff words, render tiles) are the
// finished look; the prompt bar / meter / REC clock are the shared overlays (RunIt.tsx; ./overlay.ts feeds them).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import * as THREE from 'three';
import { C, MED, Layout, useLayout, useT } from '../../theme';
import { lines, tshot } from '../../timing';
import type { ShotProps } from '../../shots';
import { Canvas as DesignCanvas } from '../../components/Canvas';
import { clamp, easeInOut3, easeOut3, lerp, prog, smooth, spring } from './anim';
import { M, STUTTER, fpsReadout, worldT } from './times';
import { VP, camAt, camFor, makeCamera, project } from './camera';
import { CropGuide } from './CropGuide';
import { barCharPos } from '../../components/barWrap';
import { Rig, World, X0 } from './Scene';
import { HERO, FAR, moonsAt, passes, sunPos, tasteful } from './world';
import { City } from '../city/City';
import { BR, bridgeSkyFade, wipeY } from './bridge';
import { P as PAL, rgbaOf } from '../../theme';

/** the picture's viewport at t: the s58 squeeze to a 9:16 phone frame (16:9), or to a 16:9 band (9:16, the joke inverts) */
export function viewportAt(t: number, L: Layout): VP & { k: number } {
  const k = t < M.S58 || t >= M.S59 ? 0 : t < M.S58 + 0.3 ? easeInOut3(prog(t, M.S58, M.S58 + 0.3)) : t >= M.S59 - 0.25 ? 1 - easeInOut3(prog(t, M.S59 - 0.25, M.S59)) : 1;
  if (L.fmt === '16x9') { const w = Math.round(lerp(L.W, (L.H * 9) / 16, k) / 2) * 2; return { x: (L.W - w) / 2, y: 0, w, h: L.H, k }; }
  // 9:16 (LAYOUT_916.md): no band. The hero car shot never shrinks in the format it was made for; the joke is the crop
  // guide (CropGuide.tsx) turning the 16:9 frame vertical
  return { x: 0, y: 0, w: L.W, h: L.H, k: 0 };
}

export const Mid3D: React.FC<ShotProps> = (props) => {
  const t = useT();
  const L = useLayout();
  const wt = worldT(t);
  const cam = camFor(camAt(wt), L.fmt);
  const vp = viewportAt(t, L);
  const tf = tasteful(wt);
  const jit = 0;
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {vp.k > 0 && <DesignCanvas />}
      <div style={{ position: 'absolute', left: vp.x + jit, top: vp.y, width: vp.w, height: vp.h, overflow: 'hidden', filter: tf > 0 ? `saturate(${1 - 0.22 * tf})` : undefined,
        boxShadow: vp.k > 0 ? '0 0 0 2px rgba(255,255,255,.16)' : undefined }}>
        <ThreeCanvas width={vp.w} height={vp.h} flat shadows gl={{ antialias: true, preserveDrawingBuffer: true }} style={{ background: '#04080e' }}>
          <Rig cam={cam} fmt={L.fmt} />
          <World t={wt} cam={cam} />
        </ThreeCanvas>
      </div>
      {/* the match-cut: the city's own vignette (.4) over the 3D copy, easing off as the city re-lays */}
      {t >= BR.CUT && t < M.S48 && <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none',
        background: `radial-gradient(circle at 50% 50%, rgba(0,0,0,0) ${0.35 * L.H}px, rgba(0,0,0,${(0.4 * bridgeSkyFade(t)).toFixed(3)}) ${1.05 * L.H}px)` }} />}
      {t < BR.WIPE1 && <CityUnderWipe t={t} L={L} props={props} />}
      {/* rc_916, 9:16 only: flying out of the window (s48) the tall frame looks steeply down onto the lit roofs just below the
          camera (a pale slate wedge under the composer, 126.2-126.6); a soft night gradient keeps that non-key strip dark */}
      {L.fmt === '9x16' && t >= M.S48 && t < M.S48 + 1.0 && <div style={{ position: 'absolute', left: 0, top: 1100, width: L.W, height: L.H - 1100, pointerEvents: 'none',
        opacity: smooth(prog(t, M.S48, M.S48 + 0.12)) * (1 - smooth(prog(t, M.S48 + 0.7, M.S48 + 1.0))),
        background: 'linear-gradient(to bottom, rgba(4,8,14,0) 0px, rgba(4,8,14,.9) 260px, rgba(4,8,14,.94) 100%)' }} />}
      <Layer2D t={t} wt={wt} L={L} vp={vp} />
      {L.fmt === '9x16' && <CropGuide t={t} />}
    </AbsoluteFill>
  );
};

// ---------- the match-cut (116.20): the 2.5D city itself continues under the 'pass 2 · shadows' wipe ----------
/** The city component keeps running (its push, rain, car, lights) below the wipe line; above it, the 3D copy (registered
 *  to the same camera) shows. Same grammar as s45's pass-1 wipe: top -> bottom, a cyan leading edge. The city's own
 *  'pass 1' label is cut out: this component's 'pass 2' label sits exactly on it. */
const LABEL = (L: Layout) => ({ x: L.fmt === '16x9' ? 64 : L.chip?.x ?? 116, y: L.fmt === '16x9' ? 52 : L.chip?.y ?? 262, h: 56 });
const CityUnderWipe: React.FC<{ t: number; L: Layout; props: ShotProps }> = ({ t, L, props }) => {
  const y = wipeY(t, L.H), lb = LABEL(L);
  const clip = `inset(${Math.max(0, y).toFixed(2)}px 0px 0px 0px)`;
  // the city's own 'pass 1' chip (City.tsx PassLabel, at the same spot) is taken out of the page, not just clipped: this
  // component's 'pass 2' chip replaces it in place (same box, same type)
  const hide = `.rcCityUnder div[style*="left: ${lb.x}px"][style*="top: ${lb.y}px"][style*="height: ${lb.h}px"]{display:none !important}`;
  return <>
    <style>{hide}</style>
    <div className="rcCityUnder" style={{ position: 'absolute', inset: 0, clipPath: clip, WebkitClipPath: clip }}><City {...props} /></div>
    {y > -40 && y < L.H + 40 && <>
      <div style={{ position: 'absolute', left: 0, top: y - 14, width: L.W, height: 12, background: rgbaOf(PAL.ch2.wire, 0.12) }} />
      <div style={{ position: 'absolute', left: 0, top: y - 1, width: L.W, height: 2, background: rgbaOf(PAL.ch2.wire, 0.85) }} />
    </>}
  </>;
};

// ---------- the HTML layer ----------
const CH = 0.6; // JetBrains Mono advance / em
const PLATE: React.CSSProperties = { background: 'rgba(14,14,20,.72)', border: '2px solid rgba(255,255,255,.16)', borderRadius: 12, boxSizing: 'border-box' };

const Layer2D: React.FC<{ t: number; wt: number; L: Layout; vp: VP }> = ({ t, wt, L, vp }) => {
  const cam3 = makeCamera(camFor(camAt(wt), L.fmt), vp.w / vp.h);
  const pr = (p: number[] | THREE.Vector3) => project(cam3, p, vp);
  const els: React.ReactNode[] = [];
  const s = L.fmt === '16x9' ? 1 : 1;
  // the stutter: tiles fall behind and re-render in buckets (the render choking), stepped on the world clock; under the UI text
  if (t >= STUTTER[0].t + 0.1 && t < M.CRASH) els.push(<Tiles key="tiles" t={t} wt={wt} vp={vp} />);
  // pass label: s45's corner chip, continued (pass 2 · shadows at the cut, 3 · reflections, 4 · light), gone through the window
  if (t >= BR.CUT && t < M.S48) {
    const ps = passes(t), a = 1 - smooth(prog(t, M.S48 - 0.45, M.S48 - 0.1)), lb = LABEL(L);
    els.push(<div key="pass" style={{ ...MED, position: 'absolute', left: lb.x, top: lb.y, height: lb.h, boxSizing: 'border-box', padding: '0 20px',
      display: 'flex', alignItems: 'center', gap: 14, background: 'rgba(14,14,20,.72)', border: `2px solid ${rgbaOf(PAL.ch2.wire, 0.55)}`, borderRadius: 12,
      fontSize: 34, lineHeight: '40px', color: PAL.ui.promptText, opacity: a, whiteSpace: 'nowrap' }}>
      <span style={{ width: 14, height: 14, borderRadius: 7, background: PAL.ch2.wire, flex: 'none' }} />pass {t < M.S46 ? 2 : ps.n} · {t < M.S46 ? 'shadows' : ps.label}</div>);
  }
  // fps readout, under the meter ("Sixty frames": 24 -> 60; the stutter: 60 -> 24 -> 8 -> 2)
  const fps = fpsReadout(t);
  if (fps !== null) {
    const m = L.meter, a = easeOut3(prog(t, M.SIXTY, M.SIXTY + 0.25));
    const flip = t >= M.S55 ? spring(t - M.S55, 3, 0.55) : 0;
    const warn = fps <= 8;
    els.push(<div key="fps" style={{ ...MED, position: 'absolute', left: m.x, top: L.fmt === '16x9' ? m.y + 110 : 386, width: m.w, height: 44, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      fontSize: 34, lineHeight: '44px', opacity: a, transform: `translateY(${(1 - a) * 10}px)` }}>
      <span style={{ color: 'rgba(255,255,255,.55)' }}>RENDER</span>
      <span style={{ color: warn ? C.meterAmber : '#ececf2', display: 'inline-block', transform: `scale(${1 + 0.18 * (1 - flip) * (t >= M.S55 ? 1 : 0)})`, transformOrigin: '100% 50%' }}>{fps} fps</span>
    </div>);
  }
  // s56: the week calendar; Monday Nov 9 2026 strikes through and collapses, the week reflows to six days
  if (t >= M.DELETE && t < M.S57) els.push(<Calendar key="cal" t={t} L={L} />);
  // s57: the cursor grabs the gizmo and drags the sun to where the dot was
  if (t >= M.S57 - 0.5 && t < M.S57 + 1.7) {
    const sp = pr(sunPos(wt));
    const g = pr(sunPos(wt).map((v, i) => v + (i === 1 ? 0.075 * 1.08 * Math.hypot(...sunPos(wt).map((q, j) => q - [camAt(wt).pos.x, camAt(wt).pos.y, camAt(wt).pos.z][j])) : 0)));
    const a = smooth(prog(t, M.S57 - 0.5, M.S57 - 0.25)) * (1 - smooth(prog(t, M.S57 + 1.3, M.S57 + 1.7)));
    const approach = easeInOut3(prog(t, M.S57 - 0.5, M.S57 - 0.05));
    const from = { x: sp.x + 180, y: sp.y + 140 };
    const cx = lerp(from.x, g.x + 4, approach), cy = lerp(from.y, g.y + 6, approach);
    const press = t >= M.S57 && t < M.S57 + 1.0 ? 0.88 : 1;
    els.push(<svg key="cur" width={44} height={56} viewBox="0 0 22 28" style={{ position: 'absolute', left: cx, top: cy, opacity: a, transform: `scale(${press})`, transformOrigin: '0 0', overflow: 'visible' }}>
      <path d="M1 1 L1 22 L6.5 16.8 L10.2 25.5 L13.6 24 L10 15.6 L17.5 15.6 Z" fill="#f4f1f6" stroke="#0b0a12" strokeWidth={1.6} strokeLinejoin="round" /></svg>);
    void sp;
  }
  // s58: the phone frame's caption-free edge (the frame itself is the joke; no platform UI)
  // payoff words: 0.30 s before each land the word lifts out of the bar and flies to what it changes
  for (const f of FLIGHTS) {
    if (f.id === 's46') continue; // drawn by the city under the wipe (it lifts inside s45 and lands on the same window)
    const sh = tshot(f.id); if (!sh.payoff) continue;
    const t0 = sh.payoff.lift, t1 = sh.land;
    if (t < t0 || t > t1 + 0.12) continue;
    const ln = lines[sh.lines[sh.lines.length - 1]];
    const words = ln.text.split(' ');
    const wi = words.map((w) => w.replace(/[^\w']/g, '').toLowerCase()).lastIndexOf(sh.payoff.word.toLowerCase());
    if (wi < 0) continue;
    const idx = words.slice(0, wi).join(' ').length + (wi ? 1 : 0), word = words[wi].replace(/[.,!?)(]/g, '');
    const font = L.bar.font;
    const bc = barCharPos(L, ln.text, idx), ch = bc.ch;
    const x0 = bc.x + (word.length * ch) / 2, y0 = bc.y;
    const tg = f.screen ? (L.fmt === '16x9' ? f.screen : f.screen9 ?? { x: (f.screen.x / 1920) * L.W, y: 300 + (f.screen.y / 1080) * 700 }) : pr(f.at!(t1));
    const tgt = { x: clamp(tg.x, 120, L.W - 120), y: clamp(tg.y, 120, L.H - 200) };
    const p = clamp((t - t0) / (t1 - t0)), e = easeInOut3(p);
    const ctrl = { x: lerp(x0, tgt.x, 0.5), y: Math.min(y0, tgt.y) - 140 };
    const bx = (1 - e) * (1 - e) * x0 + 2 * (1 - e) * e * ctrl.x + e * e * tgt.x, by = (1 - e) * (1 - e) * y0 + 2 * (1 - e) * e * ctrl.y + e * e * tgt.y;
    const size = lerp(font, 34, e), op = t > t1 ? 0 : 1 - smooth(prog(p, 0.72, 1));
    els.push(<div key={`fly${f.id}`} data-fit="off" style={{ ...MED, position: 'absolute', left: bx, top: by, transform: 'translate(-50%,-50%)', fontSize: size, lineHeight: 1,
      color: '#f4f1f6', opacity: op, whiteSpace: 'nowrap', textShadow: '0 0 18px rgba(255,255,255,.35)' }}>{word}</div>);
    const ar = (t - t1) / 0.12;
    if (ar >= 0 && ar <= 1) els.push(<div key={`spk${f.id}`} style={{ position: 'absolute', left: tgt.x - 10 - 40 * ar, top: tgt.y - 10 - 40 * ar, width: 20 + 80 * ar, height: 20 + 80 * ar,
      borderRadius: '50%', border: '2px solid rgba(255,255,255,.6)', opacity: 1 - ar, boxSizing: 'border-box' }} />);
  }
  void s;
  return <>{els}</>;
};

// payoff targets: a 3D point (projected live) or a screen point (16:9 px)
const moonP = (i: number) => (tt: number) => moonsAt(tt).p[i];
const FLIGHTS: { id: string; at?: (t: number) => number[]; screen?: { x: number; y: number }; screen9?: { x: number; y: number } }[] = [
  { id: 's46', at: () => [HERO.win.x, HERO.win.y, 0] },        // run -> the window (shadows switch on)
  { id: 's47', at: () => [-12, 14, 0] },                         // do -> the city (full light)
  { id: 's48', at: () => [HERO.win.x, HERO.win.y, 0] },        // do -> through the window
  { id: 's49', at: moonP(1) },                                    // another -> moon 2
  { id: 's50', at: (t) => { const m = moonsAt(t).p; return [(m[0][0] + m[1][0]) / 2, (m[0][1] + m[1][1]) / 2, m[0][2]]; } }, // other -> the pair
  { id: 's51', at: moonP(0) },                                    // tasteful -> the halo
  { id: 's52', at: () => [0, 0, -170] },                         // weird -> the ocean
  { id: 's53', at: () => [0, 0, -170] },                         // disappear -> the ocean
  { id: 's54', at: () => [0, 0, -170] },                         // wave -> the centre the waves rise from
  { id: 's55', screen: { x: 1760, y: 196 }, screen9: { x: 880, y: 408 } },  // wait -> the fps readout
  { id: 's56', screen: { x: 960 - 6 * 64 + 4, y: 465 }, screen9: { x: 540 - 380 + 16 + 52, y: 765 } }, // mondays -> the MON column
  { id: 's57', at: (t) => sunPos(t) },                            // sun -> the sun
  { id: 's58', screen: { x: 960, y: 470 }, screen9: { x: 480, y: 290 } }, // everyone -> the frame (9:16: the crop guide's pill)
  { id: 's59', at: () => [0, 20, -270] },                        // four -> the city
  { id: 's60', screen: { x: 960, y: 470 }, screen9: { x: 540, y: 680 } }, // floor -> the roll
  { id: 's61', at: (t) => sunPos(t) },                            // night -> the eclipse
  { id: 's62', at: () => { const b = FAR.find((x) => x.tower)!; return [b.x + b.w / 2, b.h - 6.4, b.z + b.d]; } }, // time -> the tower clock
];

/** s56 calendar: a clean week card over the city. Week of Mon Nov 9 2026 (release night): MON 9 .. SUN 15. */
const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
const Calendar: React.FC<{ t: number; L: Layout }> = ({ t, L }) => {
  const inA = spring(t - M.DELETE, 2.2, 0.75), out = smooth(prog(t, M.S57 - 0.45, M.S57 - 0.1));
  const strike = easeOut3(prog(t, M.S56, M.S56 + 0.14));
  const col = 1 - easeInOut3(prog(t, M.S56 + 0.16, M.S56 + 0.56));
  // 9:16 (LAYOUT_916.md): 760 x 150 at y 690, 7 cells of 104, day labels 34 px, dates 48 px
  const g9 = L.fmt !== '16x9';
  const CW = L.fmt === '16x9' ? 128 : 104, PADX = g9 ? 16 : 32, CH9 = g9 ? 122 : 150, DF = g9 ? 48 : 58, DL = g9 ? 54 : 64, ST = g9 ? 70 : 74;
  const w = 6 * CW + CW * col + 2 * PADX;
  const cx = L.W / 2, top = L.fmt === '16x9' ? 360 : 690;
  return (
    <div style={{ ...PLATE, position: 'absolute', left: cx - w / 2, top, width: w, height: g9 ? 150 : 210, padding: `0 ${PADX}px`, display: 'flex', alignItems: 'center', overflow: 'hidden',
      opacity: clamp(inA) * (1 - out), transform: `translateY(${(1 - clamp(inA)) * 24 - out * 20}px) scale(${0.96 + 0.04 * clamp(inA)})`, background: 'rgba(14,14,20,.78)' }}>
      {DAYS.map((d, i) => {
        const mon = i === 0;
        const cw = mon ? CW * col : CW;
        return (
          <div key={d} style={{ ...MED, position: 'relative', width: cw, flex: 'none', height: CH9, overflow: 'hidden', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10,
            opacity: mon ? smooth(prog(col, 0.86, 1)) : 1, borderLeft: i > 0 ? '2px solid rgba(255,255,255,.08)' : undefined }}>
            {/* Monday's text is gone before its column gets narrower than the word (no clipped glyphs) */}
            {(!mon || col > 0.86) && <div style={{ fontSize: 34, lineHeight: '40px', color: mon ? '#f4f1f6' : 'rgba(255,255,255,.55)', whiteSpace: 'nowrap' }}>{d}</div>}
            {(!mon || col > 0.86) && <div style={{ fontSize: DF, lineHeight: `${DL}px`, color: '#f4f1f6', whiteSpace: 'nowrap' }}>{9 + i}</div>}
            {mon && strike > 0 && col > 0.86 && <div style={{ position: 'absolute', left: 14, top: ST, height: 4, width: (CW - 28) * strike, background: '#f4f1f6', borderRadius: 2 }} />}
          </div>
        );
      })}
    </div>
  );
};

/** render tiles falling behind: pending tiles (flat, unrendered) grow with each fps step; buckets walk them */
const Tiles: React.FC<{ t: number; wt: number; vp: VP }> = ({ t, wt, vp }) => {
  const S = 120, cols = Math.ceil(vp.w / S), rows = Math.ceil(vp.h / S);
  const pend = t < STUTTER[1].t ? 0.08 : t < STUTTER[2].t ? 0.3 : lerp(0.45, 0.72, prog(t, STUTTER[2].t, M.CRASH));
  const h = (i: number) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const step = Math.floor((wt - STUTTER[0].t) * 24 + 1e-6);
  const cells: React.ReactNode[] = [];
  const pending: number[] = [];
  for (let i = 0; i < cols * rows; i++) if (h(i) < pend) pending.push(i);
  pending.forEach((i) => {
    const x = vp.x + (i % cols) * S, y = vp.y + Math.floor(i / cols) * S;
    cells.push(<div key={i} style={{ position: 'absolute', left: x, top: y, width: S, height: S, background: 'rgba(26,32,48,.94)', boxShadow: 'inset 0 0 0 1px rgba(232,238,248,.10)' }} />);
  });
  // three buckets (white corner brackets) re-rendering pending tiles in scan order
  for (let b = 0; b < 3 && pending.length; b++) {
    const i = pending[(step + b * Math.floor(pending.length / 3)) % pending.length];
    const x = vp.x + (i % cols) * S, y = vp.y + Math.floor(i / cols) * S, c = 'rgba(232,238,248,.85)', L = 22;
    cells.push(<svg key={`b${b}`} width={S} height={S} style={{ position: 'absolute', left: x, top: y }}>
      <path d={`M2 ${L} V2 H${L} M${S - L} 2 H${S - 2} V${L} M${S - 2} ${S - L} V${S - 2} H${S - L} M${L} ${S - 2} H2 V${S - L}`} stroke={c} strokeWidth={3} fill="none" /></svg>);
  }
  return <>{cells}</>;
};
void X0; void tasteful;
