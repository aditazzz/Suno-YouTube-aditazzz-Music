// FINAL + OUTRO, s64-s78 (155.34-198.00), one continuous component (rc_final). Approved frames 5 and 6 ported from
// design/frames.html; palette PALETTE.md FINAL/OUTRO (Flag 8: generic shards blue/amber/white only, purple only on the car
// and its own fragments; pink only on the dot). Every world change on its shot's land (times.ts), every frame a pure
// function of t, nothing pops in.
//   s64 reboot: the crashed world shrinks to a card, HISTORY opens, "Out of memory." files itself as the last (red) row
//   s65 the card shrinks to a thumbnail   s66 its magenta goes quiet   s67 it shatters, shards spiral into the pink dot
//   s68 the grid goes, just the dot and the dark (breathing on the real kicks)   s69 half size, a heartbeat
//   s70 the panel slides off, the dot recentres   s71 the dot turns white (8 frames, through light pink)
//   s72 "Run it, run it" types itself, the light pulses on bars 89 and 90   s73 HISTORY back, the world's pieces return
//   s74-s76 Undo x3: the highlight climbs a block each time and the pieces spiral into the light (frame 5)
//   s77 the panel closes, the light recentres with frame 6's rings   s78 the cursor clicks the light (frame 6); the light
//   fills the frame and becomes frame 0 (the last frame IS the Hook at t = 0, rendered under a growing mask).
import React, { useMemo } from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { FromCtx, Layout, MED, useLayout, useT } from '../../theme';
import type { ShotProps } from '../../shots';
import { lines, tshot } from '../../timing';
import { Hook } from '../hook/Hook';
import { EpicFrozen } from '../../epic/Epic';
import { clamp, easeIn2, easeInOut3, easeOut3, lerp, mixHex, prog, smooth, spring } from '../hook/anim';
import { BLOOM0, BLOOM1, F } from './times';
import { barCharPos } from '../../components/barWrap';
import { FL, ITEMS, OOM, PITCH, ROW0, THUMB, TX, bloomR, dotCol, dotPos, dotPulse, dotR, highlight, layoutOf, panelOpen, strikeOf, whiteK } from './world';
import { Car } from './Car';

const K = { bg: '#050507', panel: 'rgba(17,18,24,.92)', border: '#ffffff1f', ink: '#e9e6f2', soft: '#b4b2c0', ghost: '#6b6878',
  blue: '#2a3a54', amber: '#ffcf7a', white: '#e8eef8', carShard: '#5b2d94', halo: '255,243,234', oom: 'rgba(255,59,82,.62)' };
const CH = 0.6; // JetBrains Mono advance (em)
const ELL = 0.62; // the spiral's vertical squash (frame 5)

function rng(seed: number) { return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const polar = (c: { x: number; y: number }, th: number, r: number) => ({ x: c.x + Math.cos(th) * r, y: c.y + Math.sin(th) * r * ELL });

// ---------- the crash card (s64-s67) ----------
function cardAt(t: number, L: Layout, fl: FL) {
  const a = spring(t - F.REBOOT, 1.4, 0.74), b = t >= F.SMALLER ? spring(t - F.SMALLER, 2.0, 0.66) : 0;
  const s = lerp(lerp(1, 0.5, a), fl.card ? fl.card.s : 0.2, b);
  const k = clamp(a, 0, 1.2);
  return { s, cx: lerp(L.W / 2, fl.DL.x, k), cy: lerp(L.H / 2, fl.DL.y, k) };
}

// ---------- FINAL shards: the card's cells (12 x 7) burst out and spiral into the pink dot (s67) ----------
type Shard = { x0: number; y0: number; th0: number; r0: number; th1: number; r1: number; size: number; a: number; col: string; rot: number; s0: number; d: number };
function finalShards(fl: FL): Shard[] {
  const CD = fl.card ?? { s: 0.2, w: 1920, h: 1080, cols: 12, rows: 7 };
  const r = rng(67), out: Shard[] = [], c = fl.DL, cw = CD.w * CD.s / CD.cols, chh = CD.h * CD.s / CD.rows;
  for (let j = 0; j < CD.rows; j++) for (let i = 0; i < CD.cols; i++) {
    const x0 = c.x - (CD.w * CD.s) / 2 + (i + 0.5) * cw, y0 = c.y - (CD.h * CD.s) / 2 + (j + 0.5) * chh;
    const th0 = Math.atan2((y0 - c.y) / ELL, x0 - c.x), r0 = Math.hypot(x0 - c.x, (y0 - c.y) / ELL);
    const u = r(); const th1 = th0 + (r() - 0.5) * 1.2; let r1 = 110 + u * 450;
    const cx = Math.cos(th1); if (c.x + cx * r1 > fl.maxX) r1 = Math.max(110, (fl.maxX - c.x) / Math.max(cx, 1e-3));
    // 9:16: keep-out: no shard comes to rest in the chrome block (top right: MEMORY / REC / fps)
    if (fl.keepOut) { const K0 = fl.keepOut; while (r1 > 110) { const q = polar(c, th1, r1); if (q.x > K0.x0 && q.y < K0.y1) r1 -= 12; else break; } r1 = Math.min(r1, 520); }
    const pick = r(); const col = pick < 0.52 ? K.blue : pick < 0.78 ? K.amber : K.white; // Flag 8: no purple here
    out.push({ x0, y0, th0, r0, th1, r1, size: 4 + u * 44, a: 0.25 + u * 0.7, col, rot: r() * 6.28, s0: F.RIOT + 0.35 + r() * 0.65 + (1 - u) * 0.1, d: 0.7 + r() * 0.3 });
  }
  return out;
}
const ShardsFinal: React.FC<{ t: number; fl: FL; list: Shard[] }> = ({ t, fl, list }) => {
  if (t < F.RIOT || t > F.DARK + 0.3) return null;
  const c = fl.DL;
  return <g>{list.map((s, i) => {
    const pb = easeOut3(prog(t, F.RIOT, F.RIOT + 0.45));
    const p = prog(t, s.s0, s.s0 + s.d); if (p >= 1) return null;
    const e = easeIn2(p);
    const rr = lerp(s.r0, s.r1, pb) * (1 - e) + s.r1 * 0.04 * Math.sin(Math.PI * Math.min(1, p / 0.3)) * (1 - p);
    const th = lerp(s.th0, s.th1, pb) + 0.3 * (t - F.RIOT) + 2.6 * e;
    const pt = polar(c, th, rr);
    const CD = fl.card ?? { s: 0.2, w: 1920, h: 1080, cols: 12, rows: 7 };
    const w = lerp(CD.w * CD.s / CD.cols, s.size, pb) * (1 - 0.85 * e), h = lerp(CD.h * CD.s / CD.rows, s.size * 1.4, pb) * (1 - 0.85 * e);
    const flash = Math.exp(-(t - F.RIOT) / 0.06);
    const col = mixHex(mixHex('#3c4659', s.col, pb), '#ffffff', 0.6 * flash);
    const op = lerp(0.9, s.a, pb) * (1 - smooth(prog(p, 0.82, 1)));
    const rot = (s.rot + th + 2 * (s.r1 / 560)) * pb * 57.3;
    return <rect key={i} x={-w / 2} y={-h / 2} width={w} height={h} fill={col} opacity={op} transform={`translate(${pt.x} ${pt.y}) rotate(${rot})`} />;
  })}</g>;
};

// ---------- OUTRO pieces: the world comes back around the white light (s73) and Undo x3 pulls it in (s74-s76) ----------
type Piece = { kind: 'shard' | 'moon' | 'car' | 'bld' | 'pigeon'; th: number; r: number; size: number; a: number; col: string; rot: number; g: 1 | 2 | 3; ap: number; st: number; d: number; seed: number };
function outroPieces(fl: FL): Piece[] {
  const r = rng(44), out: Piece[] = [], c = fl.DL;
  for (let i = 0; i < 90; i++) { // frame 5's own distribution (rng 44): t -> distance, size, opacity
    const u = r(); const th = r() * Math.PI * 2 + u * 2.6; const dist = 60 + u * 560;
    const pt = polar(c, th, dist); const pick = r();
    if (dist < 112 || pt.y > fl.maxY - 30 || pt.y < fl.minY || pt.x > fl.maxX || pt.x < 30) continue;
    const col = pick < 0.5 ? K.blue : pick < 0.78 ? K.amber : K.white; // Flag 8: frame 5's purple pick goes to blue/amber/white
    const g = dist > 380 ? 1 : dist > 240 ? 2 : 3;
    out.push({ kind: 'shard', th, r: dist, size: 4 + u * 44, a: 0.25 + u * 0.7, col, rot: th + u * 2, g, ap: F.BACK + 0.05 + r() * 0.55, st: r() * 0.45, d: 1.25 + r() * 0.4, seed: i });
  }
  const P = (kind: Piece['kind'], thDeg: number, dist: number, size: number, g: 1 | 2 | 3, col = '#e8eef8', rot = 0, seed = 0): Piece =>
    ({ kind, th: (thDeg * Math.PI) / 180, r: dist, size, a: 1, col, rot, g, ap: F.BACK + 0.1 + (seed % 5) * 0.09, st: (seed % 3) * 0.12, d: 1.5, seed });
  out.push(P('moon', -51, 577, 30, 2, '#e8eef8', 0, 1), P('moon', -122, 420, 22, 2, '#e8eef8', 0, 2));
  out.push(P('car', 119.4, 513, 0.55, 2, '', -4, 3));
  out.push(P('bld', 200, 430, 1, 2, '', 0, 4), P('bld', 28, 360, 0.85, 2, '', 0, 5), P('bld', 252, 330, 0.75, 2, '', 0, 6));
  out.push(P('pigeon', 160, 480, 1, 1, '#b4b2c0', 0, 7), P('pigeon', -18, 440, 0.9, 1, '#b4b2c0', 0, 8), P('pigeon', 78, 360, 0.8, 1, '#b4b2c0', 0, 9));
  // the car's own fragments (purple: the only purple off the car itself, PALETTE Flag 8)
  for (let i = 0; i < 6; i++) out.push({ kind: 'shard', th: ((119.4 + (r() - 0.5) * 22) * Math.PI) / 180, r: 513 + (r() - 0.5) * 120, size: 8 + r() * 16, a: 0.85,
    col: K.carShard, rot: r() * 6, g: 2, ap: F.BACK + 0.2 + r() * 0.4, st: 0.05 + r() * 0.3, d: 1.4, seed: 100 + i });
  return out;
}
const UNDO = { 1: F.UNDO1, 2: F.UNDO2, 3: F.UNDO3 } as const;
/** spiral progress of a piece 0..1 (1 = inside the light) */
const pieceP = (p: Piece, t: number) => prog(t, UNDO[p.g] + p.st, UNDO[p.g] + p.st + p.d);
const pieceArrive = (p: Piece) => UNDO[p.g] + p.st + p.d * 0.92;

const Building: React.FC<{ s: number; seed: number }> = ({ s, seed }) => {
  const r = rng(seed * 31), w = 64 * s, h = (120 + seed * 14) * s, cols = 3, rows = Math.floor(h / (22 * s));
  return <g>
    <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={3} fill="#17202f" stroke="#2a3a54" strokeWidth={2} />
    {Array.from({ length: rows * cols }, (_, k) => { const cx = k % cols, cy = Math.floor(k / cols); const lit = r() < 0.4;
      return <rect key={k} x={-w / 2 + 9 * s + cx * 17 * s} y={-h / 2 + 10 * s + cy * 22 * s} width={9 * s} height={12 * s} fill={lit ? '#ffcf7a' : '#223047'} opacity={lit ? 0.9 : 1} />; })}
  </g>;
};
const Pigeon: React.FC<{ s: number; flap: number }> = ({ s, flap }) => (
  <g transform={`scale(${s})`}>
    <ellipse cx={0} cy={0} rx={18} ry={9} fill="#9a98a6" />
    <circle cx={16} cy={-6} r={6.5} fill="#b4b2c0" /><path d="M22,-6 L29,-4 L22,-2 Z" fill="#ffcf7a" />
    <path d={`M-4,-3 Q-12,${-20 - 8 * flap} -24,${-12 - 10 * flap} Q-12,-6 -4,-3 Z`} fill="#b4b2c0" />
    <path d="M-17,0 L-28,4 L-17,4 Z" fill="#7d7b88" />
  </g>
);
const PiecesOutro: React.FC<{ t: number; fl: FL; list: Piece[]; c: { x: number; y: number } }> = ({ t, fl, list, c }) => {
  if (t < F.BACK) return null;
  return <g>{list.map((p, i) => {
    const pp = pieceP(p, t); if (pp >= 1) return null;
    const ap = easeOut3(prog(t, p.ap, p.ap + 0.55)); if (ap <= 0) return null;
    const e = easeIn2(pp);
    const r0 = p.r * (1.18 - 0.18 * ap);
    const rr = r0 * (1 - e) + r0 * 0.05 * Math.sin(Math.PI * Math.min(1, pp / 0.3)) * (1 - pp); // a breath out, then the pull
    const th = p.th + 0.035 * (t - F.BACK) + 2.6 * e;
    const pt = polar(c, th, rr);
    const sc = (0.5 + 0.5 * ap) * (1 - 0.88 * e);
    const op = ap * (1 - smooth(prog(pp, 0.8, 1)));
    const spin = (p.rot + th * 0.4 + 1.8 * e) * 57.3;
    const tr = `translate(${pt.x} ${pt.y})`;
    if (p.kind === 'shard') { const w = p.size * sc, h = p.size * 1.4 * sc;
      return <rect key={i} x={-w / 2} y={-h / 2} width={w} height={h} fill={p.col} opacity={p.a * op} transform={`${tr} rotate(${spin})`} />; }
    if (p.kind === 'moon') return <circle key={i} cx={pt.x} cy={pt.y} r={p.size * sc} fill={p.col} opacity={op} />;
    if (p.kind === 'car') { const s = p.size * sc, tilt = p.rot + 140 * e; // origin rear-wheel ground; centre ~(233,-96)
      return <g key={i} opacity={0.92 * op} transform={`${tr} rotate(${tilt}) scale(${s}) translate(-233 96)`}><Car id={`o${i}`} /></g>; }
    if (p.kind === 'bld') return <g key={i} opacity={op} transform={`${tr} rotate(${spin * 0.25 * e})`}><Building s={p.size * sc} seed={p.seed} /></g>;
    return <g key={i} opacity={op} transform={`${tr} rotate(${-8 + 90 * e})`}><Pigeon s={p.size * sc} flap={Math.sin((t - F.BACK) * 9 + p.seed)} /></g>;
  })}</g>;
};

// ---------- the history panel ----------
const OOM_FLY = { a: F.REBOOT, d: 0.6 };
const row0Of = (fl: FL) => fl.row0 ?? ROW0, pitchOf = (fl: FL) => fl.pitch ?? PITCH;
/** 9:16: the panel opens upward (a bottom sheet: translateY(+90 * (1 - open))); 16:9 slides in x as approved */
const panelY = (fl: FL, t: number) => fl.slideY ? fl.panel.y + (1 - panelOpen(t)) * 90 : fl.panel.y;
const rowY = (fl: FL, i: number, t?: number) => (fl.slideY && t !== undefined ? panelY(fl, t) : fl.panel.y) + (row0Of(fl) + i * pitchOf(fl)) * fl.panel.s;
// the panel slides 90 px and fades (never leaves through the frame edge: no text cut by the frame, QA gate 2)
const panelX = (fl: FL, L: Layout, t: number) => fl.slideY ? fl.panel.x : fl.panel.x + (1 - panelOpen(t)) * 90 + 0 * L.W;
const History: React.FC<{ t: number; fl: FL; L: Layout }> = ({ t, fl, L }) => {
  const open = panelOpen(t); if (open <= 0.001 && t > F.REBOOT + 1) return null;
  const { w, h, s } = fl.panel; const x = panelX(fl, L, t), y = panelY(fl, t);
  const R0w = row0Of(fl), PI = pitchOf(fl), HL = fl.hl ?? { x: 18, w: w - 40, h: 56 }, RX = fl.rowX ?? TX;
  const hl = highlight(t); const cur = Math.round(hl);
  const oomIn = t >= OOM_FLY.a + OOM_FLY.d;
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, transform: s !== 1 ? `scale(${s})` : undefined, transformOrigin: '0 0',
      background: K.panel, border: `2px solid ${K.border}`, borderRadius: 22, boxSizing: 'border-box', boxShadow: '0 30px 80px rgba(0,0,0,.55)', opacity: clamp(open) }}>
      <div style={{ ...MED, position: 'absolute', left: fl.rowX ?? 36, top: fl.head ?? 26, height: 44, fontSize: 34, lineHeight: '44px', letterSpacing: '0.04em', color: 'rgba(233,230,242,.5)' }}>HISTORY</div>
      <div style={{ position: 'absolute', left: HL.x, width: HL.w, top: R0w + hl * PI - HL.h / 2, height: HL.h, boxSizing: 'border-box', borderRadius: 12,
        border: '2px solid #ffffff', background: 'rgba(255,255,255,.07)', opacity: easeOut3(prog(t, F.REBOOT + 0.22 + 8 * 0.035, F.REBOOT + 0.57 + 8 * 0.035)) }} />
      {ITEMS.map((it, i) => {
        const rin = easeOut3(prog(t, F.REBOOT + 0.22 + i * 0.035, F.REBOOT + 0.57 + i * 0.035));
        const st = i === OOM ? (oomIn ? easeOut3(prog(t, OOM_FLY.a + OOM_FLY.d, OOM_FLY.a + OOM_FLY.d + 0.25)) : 0) : strikeOf(i, t);
        const col = i === OOM ? K.oom : i === cur ? '#ffffff' : mixHex(K.soft, K.ghost, st);
        const vis = i === OOM ? (oomIn ? 1 : 0) : rin;
        if (vis <= 0) return null;
        const tw = it.length * 34 * CH, dx = 24 * (1 - rin);
        const thOp = i === OOM || i === cur ? 1 : 1 - 0.5 * st; // undone rows dim their frame with their text
        return <React.Fragment key={i}>
          <div data-fit="off" style={{ position: 'absolute', left: THUMB.x + dx, top: R0w + i * PI - THUMB.h / 2, width: THUMB.w, height: THUMB.h, borderRadius: 6, overflow: 'hidden',
            boxSizing: 'border-box', border: `1px solid ${i === OOM ? K.oom : 'rgba(255,255,255,.22)'}`, background: '#000', opacity: vis * thOp }}>
            <Img src={staticFile(`history/h${i}.jpg`)} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
          </div>
          <div style={{ ...MED, position: 'absolute', left: RX + dx, top: R0w + i * PI - 22, height: 44, fontSize: 34, lineHeight: '44px', whiteSpace: 'nowrap', color: col, opacity: vis }}>
            {it}
            {st > 0 && <span data-fit="off" style={{ position: 'absolute', left: 0, top: 23, width: tw * st, height: 2, background: col }} />}
          </div>
        </React.Fragment>;
      })}
    </div>
  );
};

// ---------- payoff flights (the grammar: the payoff word lifts out of the bar 0.30 s before the land) ----------
type Flight = { id: string; to: (t: number) => { x: number; y: number } };
const Flights: React.FC<{ t: number; L: Layout; fl: FL; list: Flight[] }> = ({ t, L, fl, list }) => {
  const els: React.ReactNode[] = [];
  const font = L.bar.font, ch = font * CH;
  // the reboot: "Out of memory." files itself into the panel's last row
  if (t >= OOM_FLY.a && t < OOM_FLY.a + OOM_FLY.d) {
    const p = (t - OOM_FLY.a) / OOM_FLY.d, e = easeInOut3(p);
    const b0 = barCharPos(L, 'Out of memory.', 0), y0 = b0.y;
    const x0 = b0.x, x1 = panelX(fl, L, t) + (fl.rowX ?? TX) * fl.panel.s + 2, y1 = rowY(fl, OOM, t);
    const ctrl = { x: lerp(x0, x1, 0.5), y: Math.min(y0, y1) - 120 };
    const bx = (1 - e) ** 2 * x0 + 2 * (1 - e) * e * ctrl.x + e * e * x1, by = (1 - e) ** 2 * y0 + 2 * (1 - e) * e * ctrl.y + e * e * y1;
    els.push(<div key="oom" data-fit="off" style={{ ...MED, position: 'absolute', left: bx, top: by, transform: 'translateY(-50%)', fontSize: lerp(font, 34 * fl.panel.s, e), lineHeight: 1,
      whiteSpace: 'nowrap', color: e < 0.5 ? '#ff8a96' : K.oom }}>Out of memory.</div>);
  }
  for (const f of list) {
    const s = tshot(f.id); if (!s.payoff) continue;
    const ln = lines[s.lines[s.lines.length - 1]];
    const words = ln.text.split(' ');
    const wi = words.map((w) => w.replace(/[^\w']/g, '').toLowerCase()).lastIndexOf(s.payoff.word.toLowerCase()); if (wi < 0) continue;
    if (ln.wt[wi] + 0.14 > s.payoff.lift + 0.05) continue; // not typed by the lift (sung on/after the land): no flight
    const t0 = s.payoff.lift, t1 = s.land; if (t < t0 || t > t1 + 0.12) continue;
    const idx = words.slice(0, wi).join(' ').length + (wi ? 1 : 0), word = words[wi].replace(/[.,!?]$/, '');
    const bc = barCharPos(L, ln.text, idx), x0 = bc.x + (word.length * ch) / 2, y0 = bc.y;
    const tgt = f.to(t1);
    const p = clamp((t - t0) / (t1 - t0)), e = easeInOut3(p);
    const ctrl = { x: lerp(x0, tgt.x, 0.5), y: Math.min(y0, tgt.y) - 140 };
    const bx = (1 - e) ** 2 * x0 + 2 * (1 - e) * e * ctrl.x + e * e * tgt.x, by = (1 - e) ** 2 * y0 + 2 * (1 - e) * e * ctrl.y + e * e * tgt.y;
    const op = t > t1 ? 0 : 1 - smooth(prog(p, 0.72, 1));
    els.push(<div key={`fly${f.id}`} data-fit="off" style={{ ...MED, position: 'absolute', left: bx, top: by, transform: 'translate(-50%,-50%)', fontSize: lerp(font, 34, e), lineHeight: 1,
      color: '#f4f1f6', opacity: op, whiteSpace: 'nowrap', textShadow: '0 0 18px rgba(255,255,255,.35)' }}>{word}</div>);
    const ar = (t - t1) / 0.12;
    if (ar >= 0 && ar <= 1) els.push(<div key={`spk${f.id}`} style={{ position: 'absolute', left: tgt.x - 10 - 40 * ar, top: tgt.y - 10 - 40 * ar, width: 20 + 80 * ar, height: 20 + 80 * ar,
      borderRadius: '50%', border: '2px solid rgba(255,255,255,.6)', opacity: 1 - ar, boxSizing: 'border-box' }} />);
  }
  return <>{els}</>;
};

// ---------- the cursor (s78): it comes for the light and clicks it on bar 101 ----------
const CURSOR_PATH = 'M0,0 L0,26 L7,20 L12,31 L16,29 L11,18 L20,18 Z';
function cursorAt(t: number, fl: FL) {
  const a = F.CLICK - 1.2, arrive = F.CLICK - 0.24;
  if (t < a || t > BLOOM0 + 0.3) return null;
  const tip = { x: fl.DC.x + 20, y: fl.DC.y + 18 }, from = { x: fl.DC.x + 560, y: fl.DC.y + 330 };
  const e = easeInOut3(prog(t, a + 0.05, arrive)), settle = t > arrive ? 4 * Math.exp(-(t - arrive) / 0.07) * Math.sin((t - arrive) * 30) : 0;
  const ctrl = { x: lerp(from.x, tip.x, 0.35), y: from.y + 40 };
  const x = (1 - e) ** 2 * from.x + 2 * (1 - e) * e * ctrl.x + e * e * tip.x + settle, y = (1 - e) ** 2 * from.y + 2 * (1 - e) * e * ctrl.y + e * e * tip.y;
  const press = t >= F.CLICK - 0.034 ? Math.exp(-Math.max(0, t - F.CLICK) / 0.09) * clamp((t - (F.CLICK - 0.034)) / 0.034) : 0;
  const op = smooth(prog(t, a, a + 0.2)) * (1 - smooth(prog(t, BLOOM0, BLOOM0 + 0.22)));
  return { x, y, press, op };
}

// ---------- the component ----------
export const Final: React.FC<ShotProps> = ({ shot }) => {
  const t = useT();
  const L = useLayout();
  const rel = useCurrentFrame();
  const fl = useMemo(() => layoutOf(L), [L]);
  const shardsF = useMemo(() => finalShards(fl), [fl]);
  const pieces = useMemo(() => outroPieces(fl), [fl]);
  const flights: Flight[] = useMemo(() => [
    { id: 's67', to: () => ({ x: fl.DL.x, y: fl.DL.y }) }, { id: 's68', to: () => ({ x: fl.DL.x, y: fl.DL.y }) },
    ...(['s74', 's75', 's76'] as const).map((id) => ({ id, to: (tt: number) => ({ x: fl.panel.x + ((fl.rowX ?? TX) + 120) * fl.panel.s, y: rowY(fl, highlight(tt + 0.4), tt) }) })),
    { id: 's78', to: () => ({ x: fl.DC.x, y: fl.DC.y }) },
  ], [fl]);

  const c = dotPos(t, fl);
  // arrivals of OUTRO pieces make the light swell a touch
  let arrive = 0; for (const p of pieces) { const d = t - pieceArrive(p); if (d >= 0 && d < 0.5) arrive += (p.kind === 'shard' ? 0.05 : 0.22) * Math.exp(-d / 0.12); }
  const press = t >= F.CLICK - 0.034 ? Math.exp(-Math.max(0, t - F.CLICK) / 0.09) * clamp((t - (F.CLICK - 0.034)) / 0.034) : 0;
  const R0 = dotR(t), pulse = dotPulse(t) + Math.min(0.35, arrive);
  const R = R0 * (1 + 0.1 * pulse) * (1 - 0.07 * press);
  const wk = whiteK(t), col = dotCol(t);
  const grid = 0.06 * (1 - smooth(prog(t, F.DARK, F.DARK + 0.6)));
  const card = t < F.RIOT + 0.1 ? cardAt(t, L, fl) : null;
  const quiet = smooth(prog(t, F.QUIET, F.QUIET + 0.6));
  const cardOp = 1 - clamp((t - F.RIOT) / (2 / 30));
  const boot = Math.exp(-Math.max(0, t - F.REBOOT) / 0.09);
  // rings: frame 5's single ring (FINAL + early OUTRO), frame 6's three rings from "Perfect."
  const ringsOn = (i: number) => easeOut3(prog(t, F.PERFECT + 0.15 + (3 - i) * 0.08, F.PERFECT + 0.75 + (3 - i) * 0.08));
  const oneRing = 1 - smooth(prog(t, F.PERFECT + 0.1, F.PERFECT + 0.6));
  const ripple = t >= F.CLICK ? prog(t, F.CLICK, F.CLICK + 1.1) : -1;
  const cur = cursorAt(t, fl);
  const bR = bloomR(t, fl), bk = prog(t, BLOOM0, BLOOM1);
  // the page is revealed from the dot outward: the mask's soft edge starts inside the dot (nothing shows on the first frame)
  const mr = bR - 230, mask = `radial-gradient(circle at ${c.x}px ${c.y}px, #000 ${Math.max(0, mr - 170)}px, transparent ${Math.max(1, mr + 170)}px)`;
  const coreA = smooth(prog(bk, 0, 0.2)) * (1 - smooth(prog(bk, 0.35, 0.95)));

  return (
    <AbsoluteFill style={{ background: K.bg, overflow: 'hidden' }}>
      {grid > 0.002 && (
        <svg width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0 }}>
          <defs><pattern id="fgrid" width={48} height={48} patternUnits="userSpaceOnUse"><rect x={23} y={23} width={2} height={2} fill={`rgba(255,255,255,${grid})`} /></pattern></defs>
          <rect width={L.W} height={L.H} fill="url(#fgrid)" />
        </svg>
      )}
      {/* s64-s66: the crashed world as a card (the real crash picture, frozen at its last frame) */}
      {card && cardOp > 0 && (
        <div data-fit="off" style={{ position: 'absolute', left: card.cx - L.W / 2, top: card.cy - L.H / 2, width: L.W, height: L.H, transform: `scale(${card.s})`, transformOrigin: '50% 50%',
          borderRadius: 22 / card.s, overflow: 'hidden', opacity: cardOp, boxShadow: `0 0 0 ${2 / card.s}px rgba(255,255,255,${0.14 * clamp((1 - card.s) * 4)}), 0 ${30 / card.s}px ${80 / card.s}px rgba(0,0,0,.6)`,
          filter: `saturate(${1 - 0.9 * quiet}) brightness(${(1 - 0.3 * quiet) * (1 + 0.5 * boot * (t >= F.REBOOT ? 1 : 0))})` }}>
          {/* the workbench, frozen: the last frame of the Blender film (Fable, Nov 10). Was <EpicFrozen />. */}
          <Img src={staticFile('wb_frozen.jpg')} style={{ position: 'absolute', left: 0, top: 0, width: L.W, height: L.H, objectFit: 'cover' }} />
          {quiet > 0 && <AbsoluteFill style={{ background: `rgba(42,58,84,${0.35 * quiet})`, mixBlendMode: 'color' }} />}
        </div>
      )}
      <svg width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
        <defs>
          <radialGradient id="fhalo" gradientUnits="userSpaceOnUse" cx={c.x} cy={c.y} r={Math.max(1, R * 2.7)}>
            <stop offset={0.28} stopColor={`rgb(${K.halo})`} stopOpacity={0.3 * wk} />
            <stop offset={0.6} stopColor={`rgb(${K.halo})`} stopOpacity={0.07 * wk} />
            <stop offset={1} stopColor={`rgb(${K.halo})`} stopOpacity={0} />
          </radialGradient>
        </defs>
        <ShardsFinal t={t} fl={fl} list={shardsF} />
        <PiecesOutro t={t} fl={fl} list={pieces} c={c} />
        {R0 > 0.5 && <>
          {wk > 0 && <circle cx={c.x} cy={c.y} r={R * 2.7} fill="url(#fhalo)" />}
          {oneRing > 0 && <circle cx={c.x} cy={c.y} r={R + 36 * (R0 / 64) + 6 * pulse} fill="none" stroke={`rgba(255,255,255,${0.16 * oneRing * clamp((t - F.RIOT) / 0.4)})`} strokeWidth={2} />}
          {[3, 2, 1].map((i) => { const on = ringsOn(i); if (on <= 0) return null; const rr = R + i * 44 + pulse * i * 5; const circ = 2 * Math.PI * rr;
            return <circle key={i} cx={c.x} cy={c.y} r={rr} fill="none" stroke={`rgba(255,255,255,${0.05 * i})`} strokeWidth={2} strokeDasharray={`${circ * on} ${circ}`} transform={`rotate(-90 ${c.x} ${c.y})`} />; })}
          <circle cx={c.x} cy={c.y} r={R} fill={col} />
          {ripple >= 0 && ripple < 1 && <circle cx={c.x} cy={c.y} r={84 + 40 * easeOut3(ripple)} fill="none" stroke={`rgba(255,255,255,${0.55 * (1 - smooth(ripple))})`} strokeWidth={3} />}
        </>}
      </svg>
      <Flights t={t} L={L} fl={fl} list={flights} />
      <History t={t} fl={fl} L={L} />
      {cur && cur.op > 0 && (
        <svg width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
          <path d={CURSOR_PATH} transform={`translate(${cur.x} ${cur.y}) scale(${2.2 * (1 - 0.12 * cur.press)})`} fill="#0a0a0f" stroke="#ffffff" strokeWidth={1.6} strokeLinejoin="round" opacity={cur.op} />
        </svg>
      )}
      {/* the loop: the light fills the frame and becomes frame 0 (the Hook itself at t = 0, under a growing soft mask) */}
      {t >= BLOOM0 && (
        <>
          <div style={{ position: 'absolute', inset: 0, WebkitMaskImage: mask, maskImage: mask }}>
            <FromCtx.Provider value={-rel}><Hook shot={shot} /></FromCtx.Provider>
          </div>
          {coreA > 0 && <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(circle at ${c.x}px ${c.y}px, rgba(250,250,249,${coreA.toFixed(3)}) ${Math.max(R, bR * 0.35)}px, rgba(250,250,249,0) ${Math.max(R + 60, bR * 0.9)}px)` }} />}
        </>
      )}
    </AbsoluteFill>
  );
};
void easeIn2;
