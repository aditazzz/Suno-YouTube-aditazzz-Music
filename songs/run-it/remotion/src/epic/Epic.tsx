// THE 3D FILM LAYER (Fable, Nov 10): verse 2 through the crash, 73.12 - 155.34 s, as one persistent canvas (the world is built
// once and never remounts at shot boundaries). ./film.ts says what the world looks like at t, ./world.ts draws it.
// The prompt bar, memory meter and REC clock stay the film's shared overlays (RunIt.tsx); the few UI pieces that belong to
// these shots (render fps, the week, the cursor that moves the sun, the 9:16 guide, the crash's error labels) are drawn here.
import React from 'react';
import { AbsoluteFill, cancelRender, continueRender, delayRender, staticFile } from 'remotion';
import { useLayout, useT } from '../theme';
import { createWorld } from './world';
import { CAL_IN, CAL_OUT, EPIC_FROM, EPIC_TO, PFX, T, stateAt } from './film';
// pixelfx (MIT, Patch; parts adapted from Hugo Duprez's Sprite Fusion effects): see ../vendor/pixelfx/LICENSE and NOTICE.md
import { createFx, createFrame, clearFrame, composite } from '../vendor/pixelfx/core/index.js';
import * as fxFw from '../vendor/pixelfx/fx/explosions/firework-burst.js';
import * as fxTor from '../vendor/pixelfx/fx/fire/fire-tornado.js';
import * as fxPil from '../vendor/pixelfx/fx/fire/flame-pillar.js';
import * as fxPow from '../vendor/pixelfx/fx/explosions/cartoon-pow.js';
const FXMOD: any = { fw: fxFw, tor: fxTor, pil: fxPil, pow: fxPow };
const FWPAL = [['#4a2c08', '#86520c', '#c48412', '#f0b424', '#ffe066', '#fff6c4', '#ffffff'], ['#06283d', '#0b4f6c', '#1282a2', '#27b5d6', '#7fe3f5', '#d4fbff', '#ffffff'], ['#3a3a44', '#6a6a78', '#9a9aa8', '#c4c4d0', '#e2e2ea', '#f4f4f8', '#ffffff']];

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
// Monday, as booked. (No pink, purple or magenta: those belong to the dot, the car and the crash.)
const MONDAY: [string, string][] = [['Standup', '#2c4a78'], ['Pre-sync', '#2a6a66'], ['Sync', '#7a5a22'], ['Re: sync', '#4a5068'], ['1:1', '#35608f'], ['All-hands', '#6b4630'],
  ['Planning', '#2f6f5f'], ['Retro', '#58606e'], ['Catch-up', '#2c4a78']];
const OTHERS: Record<number, [number, string, string]> = { 2: [4, 'Lunch', '#3a3f52'], 4: [6, 'Demo', '#3a3f52'] };
const LABELS: [number, number, string][] = [[1056, 150, 'sun.mat — not found'], [300, 430, 'city_lod3 — failed'], [1290, 800, 'ocean.tex — missing']];

const EpicInner: React.FC<{ frozen?: number }> = ({ frozen }) => {
  const tLive = useT();
  const t = frozen ?? tLive;
  const L = useLayout();
  const W = L.W, H = L.H;
  const ref = React.useRef<HTMLCanvasElement>(null);
  const cur = React.useRef<HTMLDivElement>(null);
  const pix = React.useRef<HTMLCanvasElement>(null);
  const fx = React.useRef<any>({ frame: null, inst: {} });
  const world = React.useRef<any>(null);
  const now = React.useRef(t); now.current = t;
  const [handle] = React.useState(() => delayRender('epic world', { timeoutInMilliseconds: 240000 }));
  const draw = () => { if (!world.current) return; const S = stateAt(now.current); const info = world.current.render(S);
    if (cur.current) cur.current.style.transform = `translate(${info.sun[0] + 26}px, ${info.sun[1] + 30}px)`; };
  const drawPix = () => { const c = pix.current; if (!c) return; const tt = now.current, S = stateAt(tt); const ctx = c.getContext('2d')!;
    if (S.style !== 5 || (S.tiles || 1) > 1) { ctx.clearRect(0, 0, 320, 180); return; }
    const F = fx.current; if (!F.frame) F.frame = createFrame(320, 180, 0, 0); clearFrame(F.frame);
    PFX.forEach((ev, i) => { const age = tt - ev[0]; if (age < 0) { delete F.inst[i]; return; }
      let it = F.inst[i]; if (!it || it.t > age + 1e-6) { const o: any = { x: ev[2], y: ev[3], seed: ev[4] }; if (ev[1] === 'fw') o.palette = FWPAL[ev[5]]; it = F.inst[i] = createFx(FXMOD[ev[1]], o); }
      if (age > it.t) it.update(age - it.t); if (!it.done()) it.draw(F.frame); });
    const img = ctx.createImageData(320, 180); composite(F.frame, img.data, null, 1); ctx.putImageData(img, 0, 0); };
  React.useEffect(() => {
    createWorld(ref.current!, W, H, { car: staticFile('car/gt3rs.glb'), plate: staticFile('car/plate_texas_DKWHEEL.png') }, 2)
      .then((w) => { world.current = w; draw(); continueRender(handle); }).catch((e) => cancelRender(e));
  }, []);
  React.useLayoutEffect(() => { draw(); drawPix(); }, [t]);
  const S = stateAt(t), k = W / 1920, vw = (H * 9) / 16, side = ((W - vw) / 2) * S.crop;
  const calOn = S.cal > 0;
  return (
    <AbsoluteFill style={{ background: '#04080e', fontFamily: 'JBM, monospace' }}>
      <canvas ref={ref} width={W * 2} height={H * 2} style={{ position: 'absolute', left: 0, top: 0, width: W, height: H,
        filter: S.sat < 1 ? `saturate(${S.sat})` : undefined, clipPath: S.crop > 0 ? `inset(0 ${side}px 0 ${side}px)` : undefined }} />
      <canvas ref={pix} width={320} height={180} style={{ position: 'absolute', left: 0, top: 0, width: W, height: H, imageRendering: 'pixelated' }} />
      {S.crop > 0 && L.fmt === '16x9' && <>
        <div style={{ position: 'absolute', left: side, top: 0, width: W - 2 * side, height: H, boxSizing: 'border-box', border: `${2 * k}px solid rgba(255,255,255,.75)` }} />
        <div style={{ position: 'absolute', left: side + 18 * k, top: 18 * k, font: `500 ${34 * k}px JBM`, color: '#f4f1f6', opacity: S.crop }}>9:16</div>
      </>}
      {calOn && <div style={{ position: 'absolute', left: 64 * k, top: 48 * k, display: 'flex', gap: 12 * k, font: `500 ${34 * k}px JBM`, opacity: smooth01((t - (CAL_OUT + .08)) / .2) }}>
        {DAYS.map((d, i) => (S.cal >= 2 && i === 0) ? null : (
          <div key={d} style={{ padding: `${6 * k}px ${14 * k}px`, borderRadius: 10 * k, background: S.cal === 3 && i === 6 ? '#f4f1f6' : 'rgba(14,14,20,.72)',
            color: S.cal === 3 && i === 6 ? '#0e0e14' : i === 0 ? '#8a8794' : '#f4f1f6', border: `${2 * k}px solid rgba(255,255,255,.16)`,
            textDecoration: S.cal === 1 && i === 0 && t >= T.MONDAY - 0.2 ? 'line-through' : undefined }}>{d}</div>))}
      </div>}
      {S.fps !== null && <div style={{ position: 'absolute', left: L.meter.x, top: L.meter.y + 122 * k, width: L.meter.w, display: 'flex', justifyContent: 'space-between',
        font: `500 ${34 * k}px JBM`, letterSpacing: '.04em', color: '#b9b6c2' }}><span>RENDER</span><span style={{ color: '#f4f1f6' }}>{S.fps} fps</span></div>}
      <div ref={cur} style={{ position: 'absolute', left: 0, top: 0, opacity: S.cursor, width: 0, height: 0 }}>
        <svg width={44 * k} height={56 * k} viewBox="0 0 22 28"><path d="M2 2 L2 22 L7.5 17 L11 25.5 L14.5 24 L11 15.5 L18.5 15.5 Z" fill="#fff" stroke="#0e0e14" strokeWidth="1.6" strokeLinejoin="round" /></svg>
      </div>
      {LABELS.map((l, i) => S.labels >= i + 2 ? (
        <div key={l[2]} style={{ position: 'absolute', left: l[0] * k, top: l[1] * k, font: `500 ${34 * k}px JBM`, color: '#f4f1f6', background: 'rgba(8,8,12,.88)', padding: `${6 * k}px ${14 * k}px`, borderRadius: 6 * k, whiteSpace: 'nowrap' }}>{l[2]}</div>) : null)}
      {/* "Delete Mondays": the week, with Monday booked solid */}
      {frozen === undefined && t >= CAL_IN && t < CAL_OUT + .3 && (() => {
        const inK = out01((t - CAL_IN) / .2), outK = smooth01((t - CAL_OUT) / .28), sel = t >= T.CAL, del = smooth01((t - T.MONDAY) / .3);
        const X = lerp01(120, 64, outK), Y = lerp01(232, 48, outK) + 16 * (1 - inK), Wd = 1680, Hd = 660, pad = 22, head = 64, gridH = Hd - pad * 2 - head, inner = Wd - pad * 2;
        const wMon = (inner / 7) * (1 - del), wDay = (inner - wMon) / 6, bh = 55, gap = 6;
        return (<>
          <div style={{ position: 'absolute', inset: 0, background: `rgba(4,6,12,${.42 * inK * (1 - outK)})` }} />
          <div style={{ position: 'absolute', left: X * k, top: Y * k, width: Wd * k, height: Hd * k, boxSizing: 'border-box', padding: pad * k, borderRadius: 18 * k, background: 'rgba(12,13,19,.95)',
            border: `${2 * k}px solid rgba(255,255,255,.16)`, boxShadow: `0 ${26 * k}px ${80 * k}px rgba(0,0,0,.55)`, opacity: inK * (1 - outK), transform: `scale(${1 - .76 * outK})`, transformOrigin: '0 0',
            font: `500 ${34 * k}px JBM`, color: '#f4f1f6', display: 'flex', overflow: 'hidden' }}>
            {DAYS.map((d, i) => { const w = i === 0 ? wMon : wDay; const mon = i === 0;
              return (<div key={d} style={{ width: w * k, flex: 'none', overflow: 'hidden', boxSizing: 'border-box', borderLeft: i > 0 ? `${2 * k}px solid rgba(255,255,255,.07)` : undefined,
                outline: mon && sel ? `${3 * k}px solid rgba(244,241,246,${1 - del})` : undefined, outlineOffset: -3 * k, borderRadius: mon ? 10 * k : 0, opacity: mon ? 1 - .6 * del : 1 }}>
                <div style={{ height: head * k, display: 'flex', alignItems: 'center', paddingLeft: 14 * k, whiteSpace: 'nowrap' }}>
                  <span style={{ padding: `${3 * k}px ${10 * k}px`, borderRadius: 8 * k, background: mon && sel ? '#f4f1f6' : 'transparent', color: mon && sel ? '#0e0e14' : i >= 5 ? '#8a8794' : '#f4f1f6',
                    textDecoration: mon && t >= T.MONDAY ? 'line-through' : undefined }}>{d}</span></div>
                <div style={{ position: 'relative', height: gridH * k, backgroundImage: `repeating-linear-gradient(to bottom, rgba(255,255,255,.06) 0, rgba(255,255,255,.06) ${2 * k}px, transparent ${2 * k}px, transparent ${(bh + gap) * k}px)` }}>
                  {mon && MONDAY.map(([name, col], j) => { const a = out01((t - (CAL_IN + .14 + j * .042)) / .16);
                    return (<div key={name + j} style={{ position: 'absolute', left: 6 * k, top: j * (bh + gap) * k, width: (inner / 7 - 14) * k, height: bh * k, boxSizing: 'border-box', borderRadius: 10 * k, background: col,
                      borderLeft: `${6 * k}px solid rgba(255,255,255,.55)`, paddingLeft: 10 * k, display: 'flex', alignItems: 'center', whiteSpace: 'nowrap', opacity: a, transform: `scaleY(${.4 + .6 * a})`, transformOrigin: '50% 0',
                      textDecoration: t >= T.MONDAY ? 'line-through' : undefined }}>{name}</div>); })}
                  {OTHERS[i] && (() => { const [row, name, col] = OTHERS[i]; const a = out01((t - (CAL_IN + .2)) / .2);
                    return (<div style={{ position: 'absolute', left: 6 * k, top: row * (bh + gap) * k, right: 8 * k, height: bh * k, boxSizing: 'border-box', borderRadius: 10 * k, background: col, borderLeft: `${6 * k}px solid rgba(255,255,255,.3)`,
                      paddingLeft: 10 * k, display: 'flex', alignItems: 'center', whiteSpace: 'nowrap', color: '#c9c6d2', opacity: a }}>{name}</div>); })()}
                </div></div>); })}
          </div></>); })()}
      {/* "Turn off gravity": a setting, switched off; the next lines correct who it applies to */}
      {t >= T.GRAV - .5 && t < T.BIGGER && (() => { const kn = smooth01((t - (T.GRAV - .03)) / .14); const lab = t < T.GRAV ? 'on' : t < T.JUSTBIRDS ? 'off' : t < T.ALL ? 'off · birds only' : t < T.CARBACK ? 'off · everybody' : 'off · everybody but the car';
        const op = Math.min(1, (t - (T.GRAV - .5)) / .15) * Math.min(1, (T.BIGGER - t) / .12);
        return (<div style={{ position: 'absolute', left: 64 * k, top: 48 * k, display: 'flex', alignItems: 'center', gap: 18 * k, padding: `${12 * k}px ${22 * k}px`, borderRadius: 14 * k, background: 'rgba(14,14,20,.80)',
          border: `${2 * k}px solid rgba(255,255,255,.16)`, font: `500 ${36 * k}px JBM`, color: '#f4f1f6', opacity: op, whiteSpace: 'nowrap' }}>
          <span style={{ color: '#b9b6c2' }}>gravity</span>
          <div style={{ position: 'relative', width: 78 * k, height: 42 * k, borderRadius: 21 * k, background: `rgba(244,241,246,${1 - .78 * kn})` }}>
            <div style={{ position: 'absolute', top: 5 * k, left: (41 - 36 * kn) * k, width: 32 * k, height: 32 * k, borderRadius: 16 * k, background: kn > .5 ? '#f4f1f6' : '#0e0e14' }} /></div>
          <span>{lab}</span></div>); })()}
      {/* "Make it spin": the tonearm comes down on the record */}
      {(S.vinyl || 0) > 0 && (() => { const a = -26 * (1 - out01((t - T.SPIN) / .38)) - 26 * smooth01((t - (T.MOVE - .16)) / .16);
        return (<svg width={W} height={H} viewBox="0 0 1920 1080" style={{ position: 'absolute', left: 0, top: 0, filter: `drop-shadow(0 ${14 * k}px ${18 * k}px rgba(0,0,0,.55))` }}>
          <circle cx={1700} cy={330} r={74} fill="#0c0c12" stroke="rgba(255,255,255,.16)" strokeWidth={3} />
          <g transform={`translate(1700 330) rotate(${137.9 + a})`}>
            <rect x={-118} y={-24} width={84} height={48} rx={12} fill="#2b2b34" />
            <rect x={-34} y={-7} width={566} height={14} rx={7} fill="#d8d5cc" />
            <rect x={516} y={-26} width={80} height={52} rx={9} fill="#16161c" stroke="#d8d5cc" strokeWidth={3} transform="rotate(16 516 0)" />
            <circle r={44} fill="#16161c" stroke="#5a5a66" strokeWidth={4} /><circle r={13} fill="#d8d5cc" />
          </g></svg>); })()}
      {/* the crash is 3.9 s of true silence: say so on screen, with a countdown, so nobody thinks the film is over */}
      {frozen === undefined && t >= T.CRASH + .55 && t < T.END && (() => { const p = (t - (T.CRASH + .55)) / (T.END - (T.CRASH + .55)); const n = Math.max(1, Math.min(3, Math.ceil(T.END - t)));
        const inK = out01((t - (T.CRASH + .55)) / .22);
        return (<div style={{ position: 'absolute', left: 580 * k, top: (596 + 16 * (1 - inK)) * k, width: 760 * k, boxSizing: 'border-box', padding: `${26 * k}px ${32 * k}px ${24 * k}px`, borderRadius: 16 * k, background: 'rgba(10,10,14,.95)',
          border: `${2 * k}px solid rgba(255,255,255,.20)`, boxShadow: `0 ${24 * k}px ${70 * k}px rgba(0,0,0,.6)`, opacity: inK, color: '#f4f1f6' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 * k, font: `500 ${42 * k}px JBM` }}>
            <svg width={44 * k} height={44 * k} viewBox="-22 -22 44 44">{[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
              <rect key={i} x={-2.5} y={-20} width={5} height={11} rx={2.5} fill="#f4f1f6" opacity={.18 + .82 * (((i - Math.floor(t * 10)) % 8 + 8) % 8) / 7} transform={`rotate(${i * 45})`} />))}</svg>
            <span>Not responding</span></div>
          <div style={{ marginTop: 20 * k, height: 10 * k, borderRadius: 5 * k, background: 'rgba(255,255,255,.14)', overflow: 'hidden' }}><div style={{ width: `${Math.min(100, p * 100)}%`, height: '100%', background: '#f4f1f6' }} /></div>
          <div style={{ marginTop: 16 * k, font: `500 ${34 * k}px JBM`, color: '#b9b6c2' }}>Restarting in {n}</div></div>); })()}
    </AbsoluteFill>
  );
};
const lerp01 = (a: number, b: number, x: number) => a + (b - a) * x;
const smooth01 = (x: number) => { const v = Math.max(0, Math.min(1, x)); return v * v * (3 - 2 * v); };
const out01 = (x: number) => { const v = Math.max(0, Math.min(1, x)); return 1 - Math.pow(1 - v, 3); };
/** the crashed world, frozen at its last frame, for the card it shrinks into after the crash (shots/final) */
export const EpicFrozen: React.FC = () => <EpicInner frozen={EPIC_TO - 1 / 30} />;

/** mounted only inside its time range, so the world is created once, at the first frame that needs it */
export const EpicLayer: React.FC = () => { const t = useT(); return t >= EPIC_FROM && t < EPIC_TO ? <EpicInner /> : null; };
