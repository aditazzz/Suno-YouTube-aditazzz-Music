// THE HOOK, s01-s17 (0:00-41.65): one continuous picture, a pure function of film time. Registered for every hook shot
// id, so the shot Sequences cut nowhere: the world is continuous across them. ROUGHCUT_PLAN.md "The first 30 seconds".
//
// World = the artboard (16:9: 0,0-1920,1080) on an infinite canvas, seen through a camera {cx, cy, z, r}. Everything in
// the artboard is SVG in world units; text (labels, tooltip, swatch, flying payoff words) is HTML placed by projecting
// world points to the screen, so the text-fit probe can measure it. The prompt bar / meter / REC clock are the overlays
// (RunIt.tsx, theme from ./overlay.ts).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { C, MED, PAPER, mixC, useLayout, useT, Layout } from '../../theme';
import { lines, tshot } from '../../timing';
import type { ShotProps } from '../../shots';
import { clamp, easeIn2, easeInOut3, easeOut3, impact, lerp, mixHex, prog, rgbOf, smooth, spring } from './anim';
import { BEAT, H, INTRO, beatAfter, introBeats, introPush, kicksIn, worldT } from './times';
import { IRIS_ORIGIN, irisR } from './overlay';
import { barCharPos, barHeight, barRows } from '../../components/barWrap';

// ---------- world geometry ----------
// ax/ay: the screen point the camera centre sits on (default the frame centre). 9:16 (LAYOUT_916.md, rc_916): the
// camera is centred on the dot, which sits at screen (540, 640), so the zoom/roll of s13-s14 pivot on the dot; the
// paper intro zooms about the artboard's centre (ART_C9), so the zoomed-out artboard sits centred on the page.
type Cam = { cx: number; cy: number; z: number; r: number; ax?: number; ay?: number };
type Base = { cx: number; cy: number; z: number; art: { x: number; y: number; w: number; h: number }; ax?: number; ay?: number };
const baseOf = (L: Layout): Base => L.fmt === '16x9'
  ? { cx: 960, cy: 540, z: 1, art: { x: 0, y: 0, w: 1920, h: 1080 } }
  // 9:16: zoom 1.35 (the phone sees the dot bigger); DOTP -> screen (540, 640); the 9:16 artboard fills the frame
  : { cx: 960, cy: 470, z: 1.35, art: { x: 560, y: -4, w: 800, h: 1422 }, ax: 540, ay: 640 };
const ART_C9 = { x: 960, y: 707 };
const DOTP = { x: 960, y: 470 };
const BTNP = { x: 1380, y: 650 };
const BTNP9 = { x: 1145, y: 660 }; // 9:16: below-right of the dot (screen 790, 896), a diagonal that reads top to bottom
const btnOf = (L: Layout) => (L.fmt === '16x9' ? BTNP : BTNP9);
/** the button at world time tw: 9:16 flies it out to CH1's orbit place (the 16:9 offset from the dot) with the drop's x3 */
const btnAt = (L: Layout, tw: number) => {
  if (L.fmt === '16x9' || tw < H.DROP) return btnOf(L);
  const g = spring(tw - H.DROP + SNAP_LEAD, 2.4, 0.55); return { x: lerp(BTNP9.x, BTNP.x, g), y: lerp(BTNP9.y, BTNP.y, g) };
};
const DOT_R = 74;
const PINK1 = '#ff8fc0', PINK2 = C.pink, DOT_WHITE = '#f4f1f6';
const BTN_RGB = rgbOf(C.red); // palette v1.redButton #ff4630
const DROP_FLASH = true;
// the drop's springs run one frame ahead, so frame 1190 (the drop kick's frame) already moves, with the flash on it
const SNAP_LEAD = 1 / 30;      // HOOK_NOTES fix 4 (see rc_hook2 STATUS for the verdict)

const toScreen = (cam: Cam, L: Layout, x: number, y: number) => {
  const a = (cam.r * Math.PI) / 180, dx = (x - cam.cx) * cam.z, dy = (y - cam.cy) * cam.z;
  return { x: (cam.ax ?? L.W / 2) + dx * Math.cos(a) - dy * Math.sin(a), y: (cam.ay ?? L.H / 2) + dx * Math.sin(a) + dy * Math.cos(a) };
};
const toWorld = (cam: Cam, L: Layout, x: number, y: number) => ({ x: cam.cx + (x - (cam.ax ?? L.W / 2)) / cam.z, y: cam.cy + (y - (cam.ay ?? L.H / 2)) / cam.z });

// ---------- the camera ----------
const LN6 = Math.log(6);
// rc_hook2 (HOOK_NOTES fix 1): the intro gets a change on every downbeat. s01 a slow push on the bar (1.6 -> her first
// word), undone with the bar's dock spring; from bar 5 (7.98) a slow eased creep out to ZC so the page shows its edges
// and the neighbouring ghost artboards peek in by ~11 s; bar 6 (9.97) the selection snaps on; a small anticipation
// push-in (11.62 -> 11.96), then s03's pull-back to the full canvas.
// ZC = 0.58 (x3.5 above the canvas, not the notes' x4.2): at the approved ghost pitch (2520) the neighbours' edges only
// enter the frame below z 0.615, and "ghosts peek in by about 11 s" is the tell; the 11.96 pull is still x3.5.
function introZoom(t: number) {
  const { CREEP0 } = introBeats();
  const creep = Math.exp(Math.log(INTRO.ZC) * easeInOut3(prog(t, CREEP0, INTRO.ANT0)));
  const ant = Math.exp(INTRO.ANT * easeInOut3(prog(t, INTRO.ANT0, H.BLANK)));
  return introPush(t) * creep * ant;
}
// s04-s12 (HOOK_NOTES fix 2): a continuous slow push 1.00 -> 1.10 over the dot's land -> the press, so the press punch hits from closer
export const PUSH_DARK = 1.10;
const darkPush = (t: number) => 1 + (PUSH_DARK - 1) * easeInOut3(prog(t, H.DOT, H.PRESS));
function camAt(t: number, B: Base): Cam {
  const c0 = { x: B.cx, y: B.cy };
  const P = (zr: number, p: { x: number; y: number }) => ({ x: p.x + (c0.x - p.x) / zr, y: p.y + (c0.y - p.y) / zr }); // zoom about p
  const out0 = (zr: number, c = c0, r = 0): Cam => (B.ax === undefined ? { cx: c.x, cy: c.y, z: B.z * zr, r } : { cx: c.x, cy: c.y, z: B.z * zr, r, ax: B.ax, ay: B.ay });
  // 9:16: before the dark (the paper page and the slam) the zoom is about the artboard's centre, not the dot
  const out = (zr: number, c?: { x: number; y: number }, r = 0): Cam => out0(zr, c ?? (B.ax !== undefined && t < H.GO + 0.5 ? P(zr, ART_C9) : c0), r);
  const drift = (tt: number) => 1 + 0.01 * (1 - Math.cos((2 * Math.PI * tt) / 3.98)); // s01-s02: a 2% breathing drift
  const { BLANK, GO, PRESS, ZOOM, ROLL, MORE, STOP, DROP } = H;
  if (t < BLANK) return out(drift(t) * introZoom(t));
  if (t < GO) {
    // s03: one fast eased pull-back to the canvas (0.9 s), a slow creep in, a breath of anticipation, then the slam
    const z0 = Math.log(drift(BLANK) * introZoom(BLANK));
    let lz = z0 + (-LN6 - z0) * spring(t - BLANK, 1.05, 0.82);
    lz += Math.log(6 / 5.3) * smooth(prog(t, BLANK + 0.9, GO - 0.3));
    lz -= 0.09 * easeInOut3(prog(t, GO - 0.3, GO));
    return out(Math.exp(lz));
  }
  if (t < GO + 0.5) {
    // s04: 3-frame slam, 1-frame overshoot (1.04), settle
    const f = (t - GO) * 30, zA = camAt(GO - 1e-4, B).z / B.z;
    if (f < 3) return out(Math.exp(Math.log(zA) + (Math.log(1.04) - Math.log(zA)) * easeIn2(f / 3)));
    return out(1 + 0.04 * Math.exp(-(f - 3) / 1.6));
  }
  if (t < PRESS) return out(darkPush(t));
  if (t < ZOOM) {
    // s12: zoom punch 6% in 2 frames about the button (on top of the 1.10 push), settle over 10
    const f = (t - PRESS) * 30; const pr = f < 2 ? f / 2 : Math.pow(clamp(1 - (f - 2) / 10), 2);
    const k = 1 + 0.06 * pr; return out(PUSH_DARK * k, P(k, B.ax === undefined ? BTNP : BTNP9));
  }
  if (t < ROLL) {
    // s13: from the 1.10 push, x3 into the dot on the downbeat, out past the full frame (0.78) on beat 3
    const b3 = beatAfter(ZOOM, 2);
    const s1 = spring(t - ZOOM, 1.9, 0.72), s2 = spring(t - b3, 1.5, 0.78);
    const lz = Math.log(PUSH_DARK) * (1 - s1) * (1 - s2) + Math.log(3) * s1 * (1 - s2) + Math.log(0.78) * s2;
    const zr = Math.exp(lz), cin = P(zr / PUSH_DARK, DOTP);
    return out(zr, { x: lerp(cin.x, c0.x, s2), y: lerp(cin.y, c0.y, s2) });
  }
  if (t < MORE) {
    // s14: the whole canvas rolls 180 over the bar, easing back to the full frame
    const zA = camAt(ROLL - 1e-4, B), e = easeInOut3(prog(t, ROLL, MORE));
    return out(Math.exp(Math.log(zA.z / B.z) * (1 - e)), { x: lerp(zA.cx, c0.x, e), y: lerp(zA.cy, c0.y, e) }, 180 * e);
  }
  if (t < DROP) {
    // s15: roll on round to upright from the downbeat; s16 freezes it mid-move (worldT)
    const tc = Math.min(t, STOP);
    return out(1 + 0.015 * impact(tc - MORE, 2, 7), c0, 180 + 180 * easeInOut3(prog(tc, MORE, MORE + 0.7)));
  }
  // s17: snap upright on the drop's kick, then a slow push in (parallax per layer is applied by the layers)
  const rF = camAt(STOP, B).r, s = spring(t - DROP + SNAP_LEAD, 3.2, 0.5);
  if (B.ax !== undefined) {
    // 9:16: with the dot's x3 the camera eases from the phone's x1.35 to CH1's framing (x1.0, the dot at (540, 660)),
    // so the hook's last frame is CH1's first (rc_916)
    const g = spring(t - DROP + SNAP_LEAD, 2.4, 0.55);
    return { cx: c0.x, cy: c0.y, z: lerp(B.z, 1, g) * (1 + 0.07 * easeOut3((t - DROP) / 2.0)), r: rF + (360 - rF) * s, ax: B.ax, ay: lerp(B.ay ?? 640, 660, g) };
  }
  return out(1 + 0.07 * easeOut3((t - DROP) / 2.0), c0, rF + (360 - rF) * s);
}

// ---------- grid light: kick shockwaves, the dot's light, the button's light, the press flash ----------
const SHOCK_V = 1700, SHOCK_LIFE = 0.75;
function shocks(tw: number) {
  if (tw < H.GO - 0.01) return [] as number[];
  return kicksIn(tw - SHOCK_LIFE, tw).map((k) => tw - k);
}

type GridDot = { x: number; y: number };
const gridCache = new Map<string, GridDot[]>();
function gridOf(B: Base) {
  const key = `${B.art.x},${B.art.y},${B.art.w},${B.art.h}`;
  if (!gridCache.has(key)) {
    const g: GridDot[] = [];
    const x0 = Math.ceil((B.art.x - 24) / 48) * 48 + 24, y0 = Math.ceil((B.art.y - 24) / 48) * 48 + 24;
    for (let y = y0; y < B.art.y + B.art.h; y += 48) for (let x = x0; x < B.art.x + B.art.w; x += 48) g.push({ x, y });
    gridCache.set(key, g);
  }
  return gridCache.get(key)!;
}

// ---------- the dot ----------
function dotState(tw: number) {
  const { DOT, BREATH, PINK, DROP } = H;
  const fallStart = DOT - 0.3;
  if (tw < fallStart) return null;
  let y = DOTP.y, sx = 1, sy = 1;
  if (tw < DOT) { const p = (tw - fallStart) / 0.3; y = lerp(-140, DOTP.y, p * p); sy = 1 + 0.16 * p * p; sx = 1 - 0.08 * p * p; }
  else { const w = impact(tw - DOT, 3.0, 7.5); sx = 1 + 0.26 * w; sy = 1 - 0.26 * w; y = DOTP.y + DOT_R * 0.26 * w; }
  // egg: lands 1 px off centre, nudges itself to centre on beat 2
  const x = DOTP.x + 1 - smooth(prog(tw, beatAfter(DOT, 1), beatAfter(DOT, 1) + 0.15));
  // breathing on the real kicks from s07: +14% on the hit, easing back over the beat
  let breath = 0;
  if (tw >= BREATH - 0.01) for (const d of shocks(tw)) if (d < BEAT) breath = Math.max(breath, Math.pow(1 - d / BEAT, 2));
  // pink on the downbeat, a little pinker one beat later
  const b2 = PINK + 0.96; // 'pinker' as sung
  const col = tw < PINK ? DOT_WHITE : tw < b2 ? mixHex(DOT_WHITE, PINK1, prog(tw, PINK, PINK + 0.1)) : mixHex(PINK1, PINK2, prog(tw, b2, b2 + 0.1));
  // s17 bigger: x3 on the drop with a spring
  const big = tw >= DROP ? 1 + 2 * spring(tw - DROP + SNAP_LEAD, 2.4, 0.55) : 1;
  return { x, y, sx, sy, r: DOT_R * big * (1 + 0.14 * breath), rBase: DOT_R * big, breath, col, big };
}

// ---------- shapes ----------
const Pigeon: React.FC<{ x: number; y: number; s?: number; flap?: number; color?: string }> = ({ x, y, s = 1, flap = 0, color = '#e9e6f2' }) => {
  const up = 6 + 6 * flap;
  return <path d={`M ${x - 14 * s} ${y - up * s} Q ${x - 5 * s} ${y - (up + 7) * s} ${x} ${y} Q ${x + 5 * s} ${y - (up + 7) * s} ${x + 14 * s} ${y - up * s}`}
    fill="none" stroke={color} strokeWidth={3.2 * s} strokeLinecap="round" strokeLinejoin="round" />;
};
const Cursor: React.FC<{ x: number; y: number; s?: number; press?: number; opacity?: number }> = ({ x, y, s = 1, press = 0, opacity = 1 }) => {
  const k = s * (1 - 0.14 * press);
  return (
    <g transform={`translate(${x} ${y}) scale(${k})`} opacity={opacity}>
      <path d="M0 0 L0 44 L11 33 L19 51 L27 47 L19 30 L34 30 Z" fill="#ffffff" stroke="#0b0b10" strokeWidth={3} strokeLinejoin="round"
        style={{ filter: 'drop-shadow(0 4px 6px rgba(0,0,0,.45))' }} />
    </g>
  );
};

// ghost storyboard: the whole film, greyed (s03 egg)
const GHOSTS: { c: number; r: number; label: string; kind: string }[] = [
  { c: -2, r: -1, label: '02 · the dot', kind: 'dot' }, { c: -1, r: -1, label: '03 · red button', kind: 'button' },
  { c: 0, r: -1, label: '04 · bigger', kind: 'bigger' }, { c: 1, r: -1, label: '05 · variants', kind: 'variants' },
  { c: 2, r: -1, label: '06 · city', kind: 'city' }, { c: -2, r: 0, label: '07 · gravity', kind: 'gravity' },
  { c: -1, r: 0, label: '08 · the car', kind: 'car' }, { c: 1, r: 0, label: '09 · render', kind: 'render' },
  { c: 2, r: 0, label: '10 · ocean', kind: 'ocean' }, { c: -2, r: 1, label: '11 · moons', kind: 'moons' },
  { c: -1, r: 1, label: '12 · eclipse', kind: 'eclipse' }, { c: 0, r: 1, label: '13 · out of memory', kind: 'oom' },
  { c: 1, r: 1, label: '14 · undo', kind: 'undo' }, { c: 2, r: 1, label: '15 · ship it', kind: 'ship' },
  ...[-2, -1, 0, 1, 2].flatMap((c) => [{ c, r: -2, label: '', kind: 'blank' }, { c, r: 2, label: '', kind: 'blank' }]),
];
const PITCH16 = { x: 2520, y: 1560 };
// spacing of the ghost artboards: 16:9 = the approved grid; 9:16 (portrait artboards) needs its own so ghosts/labels never overlap
// 9:16 (LAYOUT_916.md): portrait artboards at 1.145 x the width, 1.115 x the height, so the plan you pause on is a phone storyboard
const pitchOf = (B: Base) => (B.art.w > B.art.h ? PITCH16 : { x: B.art.w * 1.145, y: B.art.h * 1.115 });
// the ghost art (drawn in 1920 x 1080 units): 16:9 fills the artboard; portrait = uniform scale (A.w/1920), centred at 42% height
const ghostT = (A: Base['art']) => A.w > A.h ? `translate(${A.x} ${A.y}) scale(${A.w / 1920} ${A.h / 1080})`
  : `translate(${A.x} ${A.y + 0.42 * A.h - (A.w / 1920) * 540}) scale(${A.w / 1920})`;
const GhostArt: React.FC<{ kind: string }> = ({ kind }) => {
  const s = '#c6c3bb', f = '#dcd9d2', sw = 16;
  const sk = { fill: 'none', stroke: s, strokeWidth: sw, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  switch (kind) {
    case 'dot': return <g><circle cx={960} cy={470} r={120} fill={f} />{[1, 2, 3].map((i) => <circle key={i} cx={960} cy={470} r={120 + i * 60} {...sk} strokeWidth={8} />)}</g>;
    case 'button': return <g><circle cx={960} cy={470} r={120} fill={f} /><circle cx={1380} cy={650} r={60} fill={s} /></g>;
    case 'bigger': return <g><circle cx={960} cy={500} r={360} fill={f} /></g>;
    case 'variants': return <g>{Array.from({ length: 16 }, (_, i) => <circle key={i} cx={360 + (i % 4) * 400} cy={170 + Math.floor(i / 4) * 250} r={80} fill={i % 3 ? f : s} />)}</g>;
    case 'city': case 'gravity': return <g>{[0, 1, 2, 3, 4, 5, 6, 7].map((i) => <rect key={i} x={100 + i * 220} y={kind === 'city' ? 1080 - 300 - ((i * 137) % 260) : 1080 - 260 - ((i * 97) % 200) - (i % 2) * 300} width={180} height={300 + ((i * 137) % 260)} fill={i % 2 ? f : s} />)}</g>;
    case 'car': return <g><path d="M420 760 L640 600 L1180 590 L1460 700 L1520 780 L420 790 Z" fill={f} /><circle cx={650} cy={800} r={90} fill={s} /><circle cx={1290} cy={800} r={90} fill={s} /></g>;
    case 'render': return <g>{[0, 1, 2, 3, 4].map((i) => <path key={i} d={`M${260 + i * 300} 900 l120 -70 l0 ${-200 - i * 60} l-120 70 Z M${260 + i * 300} 900 l-120 -70 l0 ${-200 - i * 60} l120 70`} fill={i % 2 ? f : s} />)}</g>;
    case 'ocean': return <g>{[0, 1, 2, 3, 4].map((i) => <path key={i} d={`M 120 ${620 + i * 90} q 140 -50 280 0 t 280 0 t 280 0 t 280 0 t 280 0 t 280 0`} {...sk} />)}</g>;
    case 'moons': return <g><circle cx={830} cy={460} r={190} fill={f} /><circle cx={1100} cy={460} r={190} fill={s} opacity={0.7} /></g>;
    case 'eclipse': return <g><circle cx={960} cy={480} r={260} {...sk} strokeWidth={34} /><circle cx={960} cy={480} r={220} fill={s} /></g>;
    case 'oom': return <g>{Array.from({ length: 48 }, (_, i) => (i + Math.floor(i / 8)) % 2 ? <rect key={i} x={360 + (i % 8) * 150} y={140 + Math.floor(i / 8) * 150} width={150} height={150} fill={f} /> : null)}</g>;
    case 'undo': return <g>{[0, 1, 2, 3, 4].map((i) => <rect key={i} x={560} y={220 + i * 140} width={800 - i * 90} height={70} rx={35} fill={i ? f : s} />)}<path d="M 470 290 q -120 120 0 240" {...sk} /></g>;
    case 'ship': return <g><circle cx={960} cy={540} r={70} fill={s} /></g>;
    default: return null;
  }
};

// ---------- the component ----------
export const Hook: React.FC<ShotProps> = () => {
  const t = useT();
  const L = useLayout();
  const B = baseOf(L);
  const tw = worldT(t);
  const cam = camAt(t, B);
  const { DARK, BTN, TIP, COVER, PRESS, MORE, STOP, DROP, BLANK, GO } = H;

  // the slam smears over its 3 frames (4 sub-frame camera samples, equal-weight stack)
  const slamF = (t - GO) * 30;
  const camSamples: Cam[] = slamF >= 0 && slamF < 3.5 ? [0, 0.25, 0.5, 0.75].map((k) => camAt(t - (k * 0.9) / 30, B)) : [cam];

  const paper = t < DARK + IRIS_FRAMES_S;
  const iris = irisR(t);
  const irisW = toWorld(cam, L, ...(L.fmt === '16x9' ? [IRIS_ORIGIN.x, IRIS_ORIGIN.y] as [number, number] : irisOrigin9(L)));
  const dark = t >= DARK;

  const dot = dotState(tw);
  const sh = shocks(tw);
  const flash = tw >= PRESS ? Math.exp(-(tw - PRESS) / 0.12) : 0;
  // s17 (HOOK_NOTES fix 4): after E1's 1.47 s of silence the drop re-uses the press flash: one grid flash on the drop kick, 2 frames
  const dropF = Math.round((t - DROP) * 30), dropFlash = DROP_FLASH && dropF === 0 ? 1 : DROP_FLASH && dropF === 1 ? 0.45 : 0;
  const lift = tw >= DROP ? spring(tw - DROP + SNAP_LEAD, 2, 0.8) : 0; // s17: the canvas brightens a stop
  const btnIn = tw >= BTN ? spring(tw - BTN, 2.6, 0.45) : 0;
  const dotCol = dot ? rgbOf(dot.col) : [255, 255, 255];
  const dotPresence = dot ? clamp((tw - (H.DOT - 0.05)) / 0.15) : 0;

  // grid dots (artboard): paper = ink dots r 1.6 (3.2 px) at 22%, dark = white at 14%; lit by the shockwaves, the dot, the button, the press
  // (rc_hook2 fix 1: the paper grid was 2.2 px at 13%, invisible on a phone; fix 2: dark 0.08 -> 0.14)
  const grid = gridOf(B);
  const zrNow = cam.z / B.z;
  const paperZoomFade = clamp((zrNow - 0.22) / 0.3); // like a design tool, the dot grid fades out as you zoom out (no moire at x1/6)
  const gridDots = (isDark: boolean) => grid.map((g, i) => {
    let a = isDark ? 0.14 * (1 + lift) : 0.22 * paperZoomFade;
    let rs = 1; // crest dots swell
    if (!isDark && t < H.NEW) a *= 0.45; // s01: faint; s02's ring wave brings the grid in
    else if (!isDark && t < H.NEW + 1.2) {
      const rr = (t - H.NEW) * 1500, dd = Math.hypot(g.x - 960, g.y - 540), band = 220;
      const crest = dd < rr && dd > rr - band ? 1 - (rr - dd) / band : 0;
      a *= dd < rr ? 1 : 0.45; a += 0.2 * crest; rs = 1 + 0.6 * crest;
    }
    let lr = 0, lg = 0, lb = 0, la = 0; // light sources: summed amplitude-weighted colour
    const add = (amp: number, c: number[]) => { la += amp; lr += c[0] * amp; lg += c[1] * amp; lb += c[2] * amp; };
    const dd = Math.hypot(g.x - (dot ? dot.x : DOTP.x), g.y - (dot ? dot.y : DOTP.y));
    for (const d of sh) { const rr = DOT_R + d * SHOCK_V; const w = Math.exp(-Math.pow((dd - rr) / 60, 2)) * Math.pow(1 - d / SHOCK_LIFE, 2); a += (isDark ? 0.45 : 0.12) * w; }
    // fix 2: the dot's light pools on the grid (amp 0.34 -> 0.6, radius 430 -> 560): light on the surface, not bloom on the dot
    if (dot && isDark) { const R = 560 * (dot.big > 1 ? 1.6 : 1); if (dd < R) add(0.6 * Math.pow(1 - dd / R, 2) * dotPresence * (0.7 + 0.3 * dot.breath), dotCol); }
    // and the button's red light gets the same lift (0.22/260 -> 0.39/340), so its arrival at 25.83 lights the floor
    if (btnIn > 0 && isDark) { const db = Math.hypot(g.x - btnAt(L, tw).x, g.y - btnAt(L, tw).y); if (db < 340) add(0.39 * Math.pow(1 - db / 340, 2) * clamp(btnIn), BTN_RGB); }
    a += (isDark ? 0.3 : 0) * (flash + dropFlash);
    let col = isDark ? [255, 255, 255] : [23, 23, 28];
    if (la > 1e-4) { const lc = [lr / la, lg / la, lb / la], k = la / (a + la); col = col.map((v, j) => Math.round(lerp(v, lc[j], k))); }
    const op = clamp(a + la, 0, 0.9);
    if (!isDark) return op < 0.004 ? null : <circle key={i} cx={g.x} cy={g.y} r={1.6 * rs} fill={`rgb(${col[0]},${col[1]},${col[2]})`} fillOpacity={op} />;
    return <rect key={i} x={g.x - 1.1} y={g.y - 1.1} width={2.2} height={2.2} fill={`rgb(${col[0]},${col[1]},${col[2]})`} fillOpacity={op} />;
  });

  const A = B.art;
  // ---- world contents (world units) ----
  const world = (
    <>
      {/* the infinite canvas around the artboard (seen in the pull-back and the zoom-out) */}
      <rect x={A.x - 40000} y={A.y - 40000} width={80000 + A.w} height={80000 + A.h} fill={dark ? '#0b0c11' : PAPER.canvas} />
      {!dark && t >= introBeats().SEL - 0.1 && t < GO + 0.4 && GHOSTS.map((g, i) => {
        const PITCH = pitchOf(B), gx = A.x + g.c * PITCH.x, gy = A.y + g.r * PITCH.y;
        return (
          <g key={i} transform={`translate(${gx - A.x} ${gy - A.y})`} opacity={0.95}>
            <rect x={A.x} y={A.y} width={A.w} height={A.h} fill="#efeee9" stroke="#d3d0c8" strokeWidth={10} />
            <g transform={ghostT(A)}><GhostArt kind={g.kind} /></g>
          </g>
        );
      })}
      {dark && <rect x={A.x - 3} y={A.y - 3} width={A.w + 6} height={A.h + 6} fill="none" stroke="rgba(255,255,255,.14)" strokeWidth={3 / cam.z} />}
      {/* the paper artboard */}
      {paper && <rect x={A.x} y={A.y} width={A.w} height={A.h} fill={PAPER.page} />}
      {paper && <g>{gridDots(false)}</g>}
      {/* the dark artboard, opened by the iris from the prompt bar (s05) */}
      {dark && (
        <g clipPath={iris < 1400 ? 'url(#iris)' : undefined}>
          <rect x={A.x} y={A.y} width={A.w} height={A.h} fill={mixHex(C.bg, '#0d0f17', lift)} />
          {gridDots(true)}
        </g>
      )}
      {/* selection outline on Frame 1 in the pull-back (design-tool chrome) */}
      {/* rc_hook2 fix 1: snaps on at bar 6 (9.97) in night blue #16233a (the film's base pair): outline + 4 corner handles, spring ~4 frames */}
      {!dark && t >= introBeats().SEL && t < GO + 0.2 && <Selection t={t} cam={cam} A={A} />}
      {/* the dot's kick ripples (s07 on) */}
      {dot && tw >= H.BREATH - 0.01 && sh.map((d, i) => {
        const rr = dot.rBase + d * SHOCK_V * 0.55; const a = 0.42 * Math.pow(1 - d / SHOCK_LIFE, 1.6);
        return <circle key={`rp${i}`} cx={dot.x} cy={dot.y} r={rr} fill="none" stroke={mixC('rgba(255,255,255,1)', dot.col, 0.5)} strokeOpacity={a} strokeWidth={2} />;
      })}
      {/* the three breathing rings (approved frame 1), drawn on at s07 */}
      {dot && [3, 2, 1].map((i) => {
        const on = clamp((tw - H.BREATH - (3 - i) * 0.06) / 0.45); if (on <= 0) return null;
        const rr = dot.rBase + i * 34 + dot.breath * i * 7; const circ = 2 * Math.PI * rr;
        return <circle key={`ring${i}`} cx={dot.x} cy={dot.y} r={rr} fill="none" stroke={`rgba(255,255,255,${0.05 * i * (1 + 0.6 * lift)})`} strokeWidth={2}
          strokeDasharray={`${circ * easeOut3(on)} ${circ}`} transform={`rotate(-90 ${dot.x} ${dot.y})`} />;
      })}
      {/* the dot */}
      {dot && (
        <g transform={`translate(${dot.x} ${dot.y}) scale(${dot.sx} ${dot.sy})`}>
          {lift > 0 && <circle r={dot.r * 1.25} fill={dot.col} opacity={0.10 * lift} style={{ filter: 'blur(28px)' }} />}
          <circle r={dot.r} fill={dot.col} />
        </g>
      )}
      {/* the red button (s09), its glass cover (s11), the press (s12) */}
      {btnIn > 0 && <RedButton tw={tw} t={t} btnIn={btnIn} btn={btnAt(L, tw)} />}
      {/* s15: one more thing, one more thing (a tiny red button, the pigeon) */}
      {tw >= MORE && <MoreThings tw={tw} dot={dot} />}
      {/* s11 egg: the pigeon crosses the top of frame for 6 frames */}
      {(() => { const f = (tw - (COVER + 0.5)) * 30; if (f < 0 || f > 6) return null; return <Pigeon x={lerp(A.x - 60, A.x + A.w + 60, f / 6)} y={L.fmt === '16x9' ? A.y + 150 : DOTP.y - 141} s={1.1} flap={Math.sin(f * 2.4)} />; })()}
    </>
  );

  const svgT = (c: Cam) => `translate(${c.ax ?? L.W / 2} ${c.ay ?? L.H / 2}) rotate(${c.r}) scale(${c.z}) translate(${-c.cx} ${-c.cy})`;
  const unfreeze = t >= DROP ? Math.exp(-(t - DROP) / 0.08) : 0;

  return (
    <AbsoluteFill style={{ background: dark ? '#0b0c11' : PAPER.canvas, overflow: 'hidden' }}>
      <svg width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0 }}>
        <defs>
          <clipPath id="iris"><circle cx={irisW.x} cy={irisW.y} r={iris / cam.z} /></clipPath>
        </defs>
        {camSamples.map((c, i) => <g key={i} transform={svgT(c)} opacity={1 / (i + 1)}>{world}</g>)}
      </svg>
      {/* s16 the stop holds the picture (worldT); s17 the drop flashes it back */}
      {unfreeze > 0.01 && <AbsoluteFill style={{ background: `rgba(255,255,255,${0.07 * unfreeze})` }} />}
      {/* s01: frame 0 is the loop's last frame, the white bloom from the clicked dot, settling into the page */}
      {t < 1.4 && <Bloom t={t} cam={cam} />}
      <ScreenText t={t} tw={tw} cam={cam} L={L} B={B} />
      <CursorLayer t={t} cam={cam} L={L} />
    </AbsoluteFill>
  );
};
const IRIS_FRAMES_S = 6 / 30;
// 9:16: the iris opens from the docked composer's centre, sized for the s05 line's wrap
const irisOrigin9 = (L: Layout): [number, number] => {
  const ln = lines.find((l) => l.shot === 's05'); const n = ln ? barRows(L, ln.words.join(' ')).length : 1;
  return [L.bar.x + L.bar.w / 2, (L.bar.bottom ?? L.bar.y + L.bar.h) - barHeight(L, n) / 2];
};

// the design-tool selection on Frame 1 (rc_hook2): screen-constant 3 px outline + 14 px handles, snapping in from 16 px outside
export const SEL_BLUE = '#16233a';
export const selOn = (t: number) => (t < introBeats().SEL ? 0 : spring(t - introBeats().SEL, 4.5, 0.55));
const Selection: React.FC<{ t: number; cam: Cam; A: Base['art'] }> = ({ t, cam, A }) => {
  const s = selOn(t), z = cam.z, inf = (1 - s) * 16 / z, op = clamp(s * 3), hs = 14 * Math.max(0, s) / z;
  const corners = [[A.x, A.y], [A.x + A.w, A.y], [A.x, A.y + A.h], [A.x + A.w, A.y + A.h]];
  return (
    <g opacity={op}>
      <rect x={A.x - inf} y={A.y - inf} width={A.w + 2 * inf} height={A.h + 2 * inf} fill="none" stroke={SEL_BLUE} strokeWidth={3 / z} />
      {corners.map(([x, y], i) => {
        const cx = x + (x > A.x ? inf : -inf), cy = y + (y > A.y ? inf : -inf);
        return <rect key={i} x={cx - hs / 2} y={cy - hs / 2} width={hs} height={hs} fill="#ffffff" stroke={SEL_BLUE} strokeWidth={2.5 / z} />;
      })}
    </g>
  );
};

const Bloom: React.FC<{ t: number; cam: Cam }> = ({ t, cam }) => {
  // the loop seam: the white light from the clicked dot (end of 'Ship it.') settling into the page. Peak #fafaf9 (luma ~250)
  // over the #f4f3f0 page: reads as light, never clips (QA gate 3).
  const L = useLayout();
  const p = toScreen(cam, L, DOTP.x, DOTP.y);
  const k = 1 - easeOut3(t / 1.4);
  const c = (a: number) => `rgba(250,250,249,${(a * k).toFixed(3)})`;
  return <AbsoluteFill style={{ background: `radial-gradient(circle at ${p.x}px ${p.y}px, ${c(1)} 0px, ${c(0.95)} ${220 + 500 * (1 - k)}px, ${c(0.6)} ${760 + 700 * (1 - k)}px, ${c(0)} ${1500 + 600 * (1 - k)}px)` }} />;
};

// ---------- the red button, cover, press ----------
const RedButton: React.FC<{ tw: number; t: number; btnIn: number; btn: { x: number; y: number } }> = ({ tw, btnIn, btn }) => {
  const { COVER, PRESS, DROP } = H;
  const { x, y } = btn;
  // press: squash on the bar-17 kick, release over 0.25 s
  const pr = tw >= PRESS - 0.034 ? Math.exp(-Math.max(0, tw - PRESS) / 0.09) * clamp((tw - (PRESS - 0.034)) / 0.034) : 0;
  const kick = tw >= DROP ? (() => { const d = tw - kicksIn(DROP, tw).pop()!; return d < BEAT ? Math.pow(1 - d / BEAT, 2) : 0; })() : 0;
  const s = btnIn * (1 - 0.1 * pr) * (1 + 0.05 * kick);
  // the cover: falls on the downbeat (gravity), clicks shut; the cursor flips it up before the press
  const fallS = COVER - 0.28;
  let coverY = 0, coverFlip = 1, coverOn = tw >= fallS;
  if (tw < COVER) { const p = (tw - fallS) / 0.28; coverY = -360 * (1 - p * p); }
  else coverY = -10 * Math.abs(impact(tw - COVER, 4, 14));
  const flipA = PRESS - 0.72, flipB = PRESS - 0.42;
  if (tw >= flipA) coverFlip = 1 - 1.85 * easeInOut3(prog(tw, flipA, flipB)) + 0.06 * impact(tw - flipB, 3, 9);
  const click = tw >= COVER ? Math.exp(-(tw - COVER) / 0.06) : 0;
  const hingeY = y - 58;
  return (
    <g>
      <g transform={`translate(${x} ${y}) scale(${s})`}>
        <circle cx={0} cy={6 - 3 * pr} r={40} fill="#3a0d12" />
        <circle cx={0} cy={2 * pr} r={40} fill={mixHex(C.red, '#c81e31', pr)} />
        <circle cx={-12} cy={-14 + 2 * pr} r={10} fill="rgba(255,255,255,.25)" />
      </g>
      {coverOn && (
        <g transform={`translate(0 ${coverY})`}>
          <g transform={`translate(0 ${hingeY}) scale(1 ${coverFlip}) translate(0 ${-hingeY})`}>
            <rect x={x - 58} y={hingeY} width={116} height={116} rx={18} fill="rgba(190,214,255,.09)" stroke="rgba(235,242,255,.46)" strokeWidth={2} />
            <path d={`M ${x - 38} ${hingeY + 96} L ${x + 22} ${hingeY + 16}`} stroke="rgba(255,255,255,.22)" strokeWidth={7} strokeLinecap="round" />
            <path d={`M ${x - 18} ${hingeY + 104} L ${x + 38} ${hingeY + 30}`} stroke="rgba(255,255,255,.10)" strokeWidth={4} strokeLinecap="round" />
          </g>
          <rect x={x - 46} y={hingeY - 6} width={92} height={12} rx={6} fill="#2a2a34" stroke="rgba(255,255,255,.25)" strokeWidth={1.5} />
          {click > 0.02 && <rect x={x - 46} y={hingeY - 6} width={92} height={12} rx={6} fill={`rgba(255,255,255,${0.7 * click})`} />}
        </g>
      )}
    </g>
  );
};

const MoreThings: React.FC<{ tw: number; dot: ReturnType<typeof dotState> }> = ({ tw, dot }) => {
  const { MORE, DROP } = H;
  const R = (dot ? dot.rBase : DOT_R) + 140, cx = dot ? dot.x : DOTP.x, cy = dot ? dot.y : DOTP.y;
  const tb = spring(tw - MORE, 2.8, 0.42);
  const pgT = MORE + BEAT / 2, pg = tw >= pgT ? spring(tw - pgT, 2.8, 0.42) : 0;
  const kick = tw >= DROP ? (() => { const d = tw - kicksIn(DROP, tw).pop()!; return d < BEAT ? Math.pow(1 - d / BEAT, 2) : 0; })() : 0;
  const a1 = (-40 * Math.PI) / 180, a2 = (215 * Math.PI) / 180;
  const p1 = { x: cx + Math.cos(a1) * R, y: cy + Math.sin(a1) * R }, p2 = { x: cx + Math.cos(a2) * R, y: cy + Math.sin(a2) * R };
  return (
    <g>
      <g transform={`translate(${p1.x} ${p1.y}) scale(${tb * (1 + 0.08 * kick)})`}>
        <circle cy={3} r={16} fill="#3a0d12" /><circle r={16} fill={C.red} /><circle cx={-5} cy={-6} r={4} fill="rgba(255,255,255,.25)" />
      </g>
      {pg > 0 && <g transform={`translate(${p2.x} ${p2.y}) scale(${pg * (1 + 0.08 * kick)})`}><Pigeon x={0} y={0} s={1.3} flap={Math.sin(tw * 9)} /></g>}
    </g>
  );
};

// ---------- screen-space text: artboard labels, tooltip, swatch, flying payoff words ----------
const CH = 0.6; // JetBrains Mono advance (em)
const ScreenText: React.FC<{ t: number; tw: number; cam: Cam; L: Layout; B: Base }> = ({ t, tw, cam, L, B }) => {
  const els: React.ReactNode[] = [];
  const A = B.art;
  const { BLANK, GO, TIP, COVER, PINK } = H;
  // artboard labels (constant 34 px on screen, like a design tool), only while zoomed out on the paper canvas
  const zr = cam.z / B.z;
  const labA = t >= BLANK && t < GO + 0.12 ? clamp((0.32 - zr) / 0.08) : 0;
  // rc_hook2: Frame 1's own label arrives with the selection at bar 6 (9.97), then rides the pull-back as before
  const mainA = t < GO ? Math.max(labA, clamp(selOn(t) * 2)) : labA;
  if (mainA > 0) {
    const items = [{ c: 0, r: 0, label: t >= GO && t < GO + 1 / 30 + 1e-6 ? 'Frame 1 · recording?' : `Frame 1 · ${L.fmt === '16x9' ? '1920×1080' : '1080×1920'}`, main: true },
      ...(labA > 0 ? GHOSTS.filter((g) => g.label) : [])];
    const PITCH = pitchOf(B);
    for (const g of items) {
      const p = toScreen(cam, L, A.x + g.c * PITCH.x, A.y + g.r * PITCH.y);
      const w = g.label.length * 34 * CH;
      // labels fade out before they reach the frame edge (never cut, never popping)
      const edge = L.fmt === '16x9' ? clamp((p.x - 16) / 60) * clamp((L.W - 16 - (p.x + w)) / 60) * clamp((p.y - 48 - 16) / 40) * clamp((L.H - 16 - p.y) / 40)
        // 9:16: they fade before they leave the safe zone (x 116-964, top 262, never below the stage)
        : clamp((p.x - 116) / 60) * clamp((964 - (p.x + w)) / 60) * clamp((p.y - ((g as any).main ? 54 : 46) - 262) / 40) * clamp((1110 - p.y) / 40);
      // and never run under the memory meter (top right UI)
      const M = L.meter, mx0 = M.x - 40, my1 = M.y + 120;
      const meterFade = p.x + w > mx0 ? clamp((p.y - 46 - my1) / 40) : 1;
      // nor under the prompt bar (fade as the label nears it)
      const Bb = L.fmt === '16x9' ? L.bar : { ...L.bar, y: (L.bar.bottom ?? 0) - barHeight(L, 2), h: barHeight(L, 2) }, lt = p.y - 46, lb = p.y - 6;
      const horiz = p.x + w > Bb.x - 20 && p.x < Bb.x + Bb.w + 20;
      const barFade = horiz ? clamp(Math.max((Bb.y - 24 - lb) / 40, (lt - (Bb.y + Bb.h + 24)) / 40)) : 1;
      if (edge * meterFade * barFade <= 0.01) continue;
      // (the main label sits 8 px higher than the ghosts' so it clears the selection's corner handle)
      els.push(<div key={`lab${g.c},${g.r}`} style={{ ...MED, position: 'absolute', left: p.x, top: p.y - ((g as any).main ? 54 : 46), fontSize: 34, lineHeight: '40px', whiteSpace: 'nowrap',
        color: (g as any).main ? SEL_BLUE : 'rgba(23,23,28,.42)', opacity: ((g as any).main ? mainA : labA) * edge * meterFade * barFade }}>{g.label}</div>);
    }
  }
  // s05 egg: the artboard renamed 'Frame 1 (dark mode)', seen whenever the camera shows the artboard edge (s13 zoom-out, s14 roll)
  let darkLab = t >= H.DARK ? clamp((0.97 - zr) / 0.07) : 0;
  if (darkLab > 0.01) {
    const p = toScreen(cam, L, A.x, A.y);
    if (L.fmt !== '16x9') { // 9:16: it fades before it leaves the safe zone (its box turns with the canvas: mirrored when upside down)
      const up = Math.cos((cam.r * Math.PI) / 180) >= 0, bx0 = up ? p.x : p.x - 390, bx1 = up ? p.x + 390 : p.x, by0 = up ? p.y - 50 : p.y + 10, by1 = up ? p.y - 10 : p.y + 50;
      darkLab *= clamp((bx0 - 116) / 40) * clamp((964 - bx1) / 40) * clamp((by0 - 262) / 40) * clamp((1110 - by1) / 40);
    }
  }
  if (darkLab > 0.01) {
    const p = toScreen(cam, L, A.x, A.y);
    els.push(<div key="darklab" style={{ ...MED, position: 'absolute', left: p.x, top: p.y, fontSize: 34, lineHeight: '40px', whiteSpace: 'nowrap',
      color: 'rgba(255,255,255,.42)', opacity: darkLab, transformOrigin: '0 0', transform: `rotate(${cam.r}deg) translate(0px, -50px)` }}>Frame 1 (dark mode)</div>);
  }
  // s10: the tooltip rises from the button; on the downbeat each hidden word gets its own redaction bar (rc_hook2 fix 3).
  // Two lines so the box fits right of the dot's rings and inside the 9:16 side margin:
  //   "This button ██████" / "█████████ ████ █████"  (= "starts recording this video")
  // Before the land the hidden words are light skeleton bars (a loading tooltip); one frame before the land reads the
  // truth (the egg); from the downbeat a cap-height #111 bar slams onto each word left to right, one per 16th (4 frames),
  // 1 px overshoot on its first frame.
  const tipA = TIP - 0.3;
  if (tw >= tipA && tw < COVER + 0.05) {
    const inK = spring(tw - tipA, 2.4, 0.7), outK = easeInOut3(prog(tw, COVER - 0.22, COVER + 0.02));
    const landF = Math.round(TIP * 30), f = Math.round(tw * 30);
    const g9 = L.fmt !== '16x9', ch = 34 * CH;
    // 9:16: the tooltip hangs BELOW the button (arrow up, near its right end) so it clears the dot above-left and keeps
    // its right edge inside x 856 (the button column); scaled by the camera's push only, so its text stays ~34-37 px
    const box = g9 ? { x: BTNP9.x - TIP_ARROW_X9, y: BTNP9.y + 66, w: TIP_BOX.w, h: TIP_BOX.h } : TIP_BOX, ax = g9 ? TIP_ARROW_X9 : TIP_ARROW_X;
    const anchor = toScreen(cam, L, box.x + ax, g9 ? box.y : box.y + box.h), s = g9 ? cam.z / B.z : cam.z; // the arrow's base stays on its world point
    const egg = f === landF - 1;
    const words = TIP_WORDS.map((w, i) => {
      const slamF = landF + 4 * i, on = f >= slamF, over = f === slamF ? 1 : 0;
      const x = TIP_PAD + w.c * ch, y = TIP_PAD_Y + w.line * 40;
      if (egg) return <span key={i} style={{ position: 'absolute', left: x, top: y, height: 40, lineHeight: '40px', whiteSpace: 'nowrap' }}>{w.word}</span>;
      return <div key={i} style={{ position: 'absolute', left: x - over, top: y + TIP_CAP_TOP - over, width: w.word.length * ch + 2 * over, height: TIP_CAP_H + 2 * over,
        borderRadius: 3, background: on ? '#111111' : '#dedbe2' }} />;
    });
    els.push(
      <div key="tip" style={{ position: 'absolute', left: anchor.x - ax, top: g9 ? anchor.y : anchor.y - box.h, width: box.w, height: box.h, transformOrigin: g9 ? `${ax}px 0%` : `${TIP_ARROW_X}px 100%`,
        transform: g9 ? `scale(${s}) translateY(${-(1 - inK) * 26 - outK * 20}px)` : `scale(${s}) translateY(${(1 - inK) * 26 + outK * 20}px)`, opacity: clamp(inK * 1.4) * (1 - outK) }}>
        <div style={{ ...MED, position: 'absolute', inset: 0, boxSizing: 'border-box', background: '#f4f1f6', borderRadius: 14,
          fontSize: 34, lineHeight: '40px', color: PAPER.ink, whiteSpace: 'nowrap', boxShadow: '0 10px 30px rgba(0,0,0,.45)' }}>
          <span style={{ position: 'absolute', left: TIP_PAD, top: TIP_PAD_Y, height: 40, lineHeight: '40px', whiteSpace: 'nowrap' }}>This button</span>
          {words}
        </div>
        {g9 ? <div style={{ position: 'absolute', left: ax - 12, top: -11, width: 0, height: 0, borderLeft: '12px solid transparent', borderRight: '12px solid transparent', borderBottom: '12px solid #f4f1f6' }} />
          : <div style={{ position: 'absolute', left: TIP_ARROW_X - 12, top: box.h - 1, width: 0, height: 0, borderLeft: '12px solid transparent', borderRight: '12px solid transparent', borderTop: '12px solid #f4f1f6' }} />}
      </div>,
    );
  }
  // s08 egg: the colour picker swatch flashes by the dot for 4 frames
  const b2 = beatAfter(PINK, 1), sf = Math.round(tw * 30) - Math.round(b2 * 30);
  if (sf >= 0 && sf < 4) {
    const p = L.fmt === '16x9' ? toScreen(cam, L, 1172, 446) : toScreen(cam, L, 1100, 330); // 9:16: above-right of the dot, inside x 964
    els.push(<div key="sw" style={{ ...MED, position: 'absolute', left: p.x, top: p.y, height: 56, padding: '0 18px 0 10px', boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 14,
      background: '#15151c', border: '2px solid rgba(255,255,255,.16)', borderRadius: 12, fontSize: 34, lineHeight: '40px', color: '#f4f1f6', opacity: sf === 0 || sf === 3 ? 0.6 : 1 }}>
      <span style={{ width: 34, height: 34, borderRadius: 8, background: C.pink }} />#FF6FAE</div>);
  }
  // the grammar: 0.30 s before each land the payoff word lifts out of the bar and flies to what it changes
  for (const f of FLIGHTS) {
    const s = tshot(f.id); if (!s.payoff) continue;
    const t0 = s.payoff.lift, t1 = s.land;
    if (t < t0 || t > t1 + 0.12) continue;
    const ln = lines[s.lines[s.lines.length - 1]];
    const words = ln.text.split(' ');
    const wi = words.map((w) => w.replace(/[^\w']/g, '').toLowerCase()).lastIndexOf(s.payoff.word.toLowerCase());
    if (wi < 0) continue;
    const idx = words.slice(0, wi).join(' ').length + (wi ? 1 : 0), word = words[wi].replace(/[.,!?]$/, '');
    const font = L.bar.font;
    const ov = t < H.NEW + 1 ? (1 - spring(t - H.NEW - 0.04, 1.35, 0.62)) * 440 : 0; // the bar's centred lift (overlay barLift)
    const { x: x0, y: y0, ch } = barCharPos(L, ln.text, idx, ov);
    const g9 = L.fmt !== '16x9', fp = g9 ? (f.at9 ?? { x: f.x, y: f.y }) : { x: f.x, y: f.y };
    const tgt = g9 ? (f.screen9 ? { ...f.screen9 } : toScreen(cam, L, fp.x, fp.y)) : f.screen ? f.screen : toScreen(cam, L, f.x, f.y);
    const p = clamp((t - t0) / (t1 - t0)), e = easeInOut3(p);
    const cx0 = x0 + (word.length * ch) / 2;
    const ctrl = { x: lerp(cx0, tgt.x, 0.5), y: Math.min(y0, tgt.y) - 140 };
    const bx = (1 - e) * (1 - e) * cx0 + 2 * (1 - e) * e * ctrl.x + e * e * tgt.x, by = (1 - e) * (1 - e) * y0 + 2 * (1 - e) * e * ctrl.y + e * e * tgt.y;
    const size = lerp(font, 34, e), op = t > t1 ? 0 : 1 - smooth(prog(p, 0.72, 1));
    const ink = t < H.DARK ? PAPER.ink : '#f4f1f6';
    els.push(<div key={`fly${f.id}`} data-fit="off" style={{ ...MED, position: 'absolute', left: bx, top: by, transform: 'translate(-50%,-50%)', fontSize: size, lineHeight: 1,
      color: ink, opacity: op, whiteSpace: 'nowrap', textShadow: t < H.DARK ? 'none' : '0 0 18px rgba(255,255,255,.35)' }}>{word}</div>);
    // arrival: a small spark ring where the word lands
    const ar = (t - t1) / 0.12;
    if (ar >= 0 && ar <= 1) els.push(<div key={`spk${f.id}`} style={{ position: 'absolute', left: tgt.x - 10 - 40 * ar, top: tgt.y - 10 - 40 * ar, width: 20 + 80 * ar, height: 20 + 80 * ar,
      borderRadius: '50%', border: `2px solid ${t < H.DARK ? 'rgba(23,23,28,.5)' : 'rgba(255,255,255,.6)'}`, opacity: 1 - ar, boxSizing: 'border-box' }} />);
  }
  return <>{els}</>;
};
// the s10 tooltip (world units; the box is scaled by the camera): 2 lines x 40 px, 24 px side padding, 16 top/bottom.
// Line 2 is the longest (20 chars): 24 + 20 x 20.4 + 24 = 456. The arrow sits over the button (x 1380).
const TIP_PAD = 24, TIP_PAD_Y = 16, TIP_ARROW_X = 200, TIP_ARROW_X9 = 420;
const TIP_BOX = { x: 1180, y: 472, w: 456, h: 112 };
// JetBrains Mono at 34 px in a 40 px line: baseline ~32.3, cap height 0.73 em ~24.8 -> the cap band is y 7.5-32.3
const TIP_CAP_TOP = 7, TIP_CAP_H = 26;
const TIP_WORDS = [{ word: 'starts', line: 0, c: 12 }, { word: 'recording', line: 1, c: 0 }, { word: 'this', line: 1, c: 10 }, { word: 'video', line: 1, c: 15 }];
// payoff targets (world points unless `screen`)
// 9:16 (rc_916): screen9 / at9 replace the 16:9 screen point / world point (the button moved to BTNP9, the tooltip hangs below it)
type Flight = { id: string; x: number; y: number; screen?: { x: number; y: number }; screen9?: { x: number; y: number }; at9?: { x: number; y: number } };
const FLIGHTS: Flight[] = [
  { id: 's02', x: 0, y: 0, screen: { x: 1560, y: 84 }, screen9: { x: 740, y: 292 } },   // session -> the meter builds
  { id: 's03', x: 960, y: 540, at9: ART_C9 },                                            // page -> the artboard (pull back)
  { id: 's04', x: 960, y: 540, screen: { x: 960, y: 540 }, screen9: { x: 540, y: 680 } }, // go -> the slam
  { id: 's05', x: 0, y: 0, screen: { x: 960, y: 860 }, screen9: { x: 485, y: 1080 } },   // dark -> the iris opens from the bar
  { id: 's06', x: 960, y: 470 }, { id: 's07', x: 960, y: 470 }, { id: 's08', x: 960, y: 470 },
  { id: 's09', x: 1380, y: 650, at9: BTNP9 }, { id: 's10', x: 1408, y: 548, at9: { x: BTNP9.x - 60, y: BTNP9.y + 150 } },
  { id: 's11', x: 1380, y: 640, at9: { x: BTNP9.x, y: BTNP9.y - 10 } }, { id: 's12', x: 1380, y: 650, at9: BTNP9 },
  { id: 's13', x: 960, y: 470 }, { id: 's14', x: 960, y: 540, at9: DOTP }, { id: 's15', x: 1125, y: 330 },
];

// ---------- the cursor (screen space; s12 press, s16 hover) ----------
const CursorLayer: React.FC<{ t: number; cam: Cam; L: Layout }> = ({ t, cam, L }) => {
  const { PRESS, STOP, DROP, ZOOM } = H;
  const t0 = PRESS - 1.25;
  if (t < t0 || t > DROP + 0.35) return null;
  const S = (x: number, y: number) => toScreen(cam, L, x, y);
  // the path is keyed off the button (9:16: BTNP9; its start comes in from the bottom right, its hover sits up-left)
  const Bt = btnOf(L), bx = Bt.x - BTNP.x, by = Bt.y - BTNP.y, g9 = L.fmt !== '16x9';
  const lidBottom = Bt.y + 58, lidTop = Bt.y - 58 - 100, HOV = { x: 1250 + bx, y: 600 + by };
  // keyed path (world points at the press, then screen-fixed hover)
  const keys: [number, { x: number; y: number }][] = [
    [t0, g9 ? { x: Bt.x + 200, y: Bt.y + 300 } : { x: 1760, y: 960 }], [PRESS - 0.78, { x: 1392 + bx, y: lidBottom + 2 }], [PRESS - 0.72, { x: 1392 + bx, y: lidBottom }],
    [PRESS - 0.42, { x: 1392 + bx, y: lidTop }], [PRESS - 0.2, { x: 1384 + bx, y: Bt.y - 4 }], [PRESS - 0.07, { x: 1384 + bx, y: Bt.y - 10 }], [PRESS, { x: 1384 + bx, y: Bt.y }],
    [PRESS + 0.35, { x: 1384 + bx, y: Bt.y + 6 }], [ZOOM - 0.2, HOV],
  ];
  let pt: { x: number; y: number };
  if (t <= keys[keys.length - 1][0]) {
    let i = 0; while (i < keys.length - 2 && t > keys[i + 1][0]) i++;
    const [ta, a] = keys[i], [tb, b] = keys[i + 1]; const e = easeInOut3(prog(t, ta, tb));
    const camLock = camAt(Math.min(t, PRESS - 0.001), baseOf(L));
    const pa = toScreen(camLock, L, a.x, a.y), pb = toScreen(camLock, L, b.x, b.y);
    pt = { x: lerp(pa.x, pb.x, e), y: lerp(pa.y, pb.y, e) };
  } else {
    const camLock = camAt(PRESS - 0.001, baseOf(L)); const h = toScreen(camLock, L, HOV.x, HOV.y);
    const idle = t >= STOP ? 0.6 : 1; // s16: the cursor hovers, one held breath
    pt = { x: h.x + 6 * Math.sin(t * 1.3) * idle, y: h.y + 4 * Math.sin(t * 1.9 + 1) * idle };
  }
  if (t > DROP) { const e = easeIn2((t - DROP) / 0.35); pt = { x: pt.x + 900 * e, y: pt.y + 500 * e }; }
  void S;
  const press = t >= PRESS - 0.07 && t < PRESS + 0.25 ? (t < PRESS ? 0 : Math.exp(-(t - PRESS) / 0.07)) : 0;
  const op = clamp((t - t0) / 0.2) * (t > DROP ? 1 - clamp((t - DROP) / 0.3) : 1);
  return (
    <svg width={L.W} height={L.H} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
      <Cursor x={pt.x} y={pt.y} s={L.fmt === '16x9' ? 1.15 : 1.0} press={press} opacity={op} />
    </svg>
  );
};
