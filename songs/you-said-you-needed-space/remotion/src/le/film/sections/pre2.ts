// Pre-chorus 2: p2_milky .. p2_celebrate (song 101.2-111.92 s). Built by earth_sec_v2, Sun Nov 8 2026 (was: rough defaults by le_engine).
//   E  p2_milky / p2_estate / p2_wish   one continuous tilt up from verse 2's horizon: the last box ships, his rocket leaves into
//        the sky, and the stars swirl into the Milky Way itself, a slowly turning spiral. On "empty real estate" a land survey is
//        plotted over it: lot lines following the arms, MILKY WAY ESTATES / 100 BILLION LOTS AVAILABLE, VACANT stakes dropping
//        one by one, and one tiny lot outside the rim already SOLD in his warm white.
//        "wish you well": the survey lets go and one shooting star crosses (the wish she doesn't make).
//   F  p2_celebrate   CUT on "But" to her night side: the stars rush together and burst as fireworks on "celebrate".
//        Slightly hollow on purpose: her own glow doesn't join in, the embers droop, one small late pop goes off alone,
//        and the camera backs away to a small planet before chorus 2 swoops in.
// POLISH (earth_pol_v2, Mon Nov 9): look pass (lux planet under every slot, the deep sky kept quiet under the survey and the
// fireworks), bigger header lettering (9:16: the sub line on two lines), LIGHT's stars are the ones that become the galaxy, a clean
// cut into the fireworks. The survey itself is as cut 1 had it. Cut 1's version: build/le_pol_v2/orig/pre2.ts.cut1.
// inserts: none. The old pitch mockup beats/03 (flat grid) was marked NEEDS CHANGES, so it is no longer wired here; this engine
// version is built to that decision. All lettering is plotted light (no DOM text): sizes and safe zones are in LAYT below.
import { PAL, Section, Builder, hits, smooth, spark, flow, C, lerp } from './api';
import { at } from '../anchor';
import { rng } from '../stars';
import { Flow, Fmt, Spark, StarSet } from '../types';
import { RGB } from '../grade';
import { lonAt, moveOut, herAfter, GAL_T, GLYPH, GAP, textWidth, QUIET, withLookB, cutTo, line } from './verse2';
import { chorus2 } from './chorus2'; // read only: its first builder, for the cut at the seam (earth_first_cut)

// ---- the property map (pitch decision on beat 03, Nov 8 22:25: "a land-survey map drawn ON the real spiral galaxy: plot lines
// around star clusters, irregular lots following the arms, little VACANT pins/stakes, a SOLD sign on one tiny lot (his). Stars
// forming the map, not boxes over stars." Header copy kept: MILKY WAY ESTATES / 100 BILLION LOTS AVAILABLE) ----
// The cast stars swirl into a tilted spiral galaxy that turns slowly; the survey is plotted over it in dots of light.
type V2 = [number, number];
// CUT 2 (earth_c2_v2, Nov 9): the galaxy sits left of centre (16:9) / in the upper middle (9:16) so that his SOLD lot and the 3D him
// beside it have their own clean part of the frame (HIM_SPOT below; frozen for earth_him_wire at 01:30 Mon).
const GAL: Record<Fmt, { c: V2; R: number; tilt: number; rot: number }> = { '169': { c: [-0.42, 0.13], R: 1.17, tilt: 0.42, rot: 8 }, '916': { c: [0, 0.16], R: 0.40, tilt: 0.5, rot: 12 } };
const SPIN = (t: number) => 0.04 * (t - 103); // the galaxy's slow turn (rad)
const proj = (fmt: Fmt, r: number, th: number): V2 => { const g = GAL[fmt], px = r * Math.cos(th), py = r * Math.sin(th) * g.tilt, a = g.rot * Math.PI / 180, cr = Math.cos(a), sr = Math.sin(a);
  return [g.c[0] + g.R * (px * cr - py * sr), g.c[1] + g.R * (px * sr + py * cr)]; };
const PITCH = 2.4, R0 = 0.14, CORE = 0.17, armTh = (r: number) => PITCH * Math.log(r / R0); // a log spiral: about 3/4 of a turn from the core to the rim
const GR = rng(5150), gauss = () => (GR() + GR() + GR() + GR() - 2) * 0.87;
const GP: V2[] = Array.from({ length: 2600 }, () => { // each star's place in the galaxy's own plane: [r, theta]
  const u = GR();
  if (u < 0.15) return [Math.abs(gauss()) * 0.1, GR() * Math.PI * 2] as V2;                       // the bulge
  if (u < 0.87) { const r = R0 + (1 - R0) * Math.pow(GR(), 0.8); return [r * (1 + gauss() * 0.03), armTh(r) + (GR() < 0.5 ? 0 : Math.PI) + gauss() * 0.2 * (1 - 0.35 * r)] as V2; } // two arms
  return [Math.sqrt(GR()) * 1.02, GR() * Math.PI * 2] as V2;                                      // the thin disk between them
});
const GALAXY: StarSet = { kind: 'fn', front: true, fn: (i, t, home, _n, fmt) => (i % 12 === 0 ? home : proj(fmt, GP[i][0], GP[i][1] + SPIN(t))) };
// the survey, in the galaxy's plane: four spiral boundaries midway between the arms' ridges (lots follow the arms), the rim,
// the core's ring, and cross cuts at uneven radii. Bands 1 and 3 hold the arms (the star clusters), 0 and 2 the gaps.
const CUTS = [[0.34, 0.5, 0.68, 0.84], [0.3, 0.44, 0.6, 0.78], [0.38, 0.56, 0.72, 0.9], [0.28, 0.46, 0.64, 0.82]];
const bandTh = (k: number, r: number) => armTh(r) + (k + 0.5) * Math.PI / 2;
type Curve = { f: (u: number) => V2; len: number; t0: number; dur: number }; // plane curve [r, theta] over u 0..1, its plane length, when it is plotted
const MAP_T = at('pre2/L1') - 0.1, MAP_OUT = at('pre2/L2') + 0.45, REF_T = MAP_T + 1.6; // plotting starts with "All that empty real estate"; lets go on "I was gonna"
// the title goes up as the galaxy forms, on "the Milky Way" (cloud chat, Nov 9 00:40: pre-chorus 2 must read as MILKY WAY ESTATES; it used to open on the LIGHT box and the title came 2 s in)
const TITLE_T = at('pre2/L0') + 1.0;
const CURVES: Curve[] = [
  ...[0, 1, 2, 3].map((k): Curve => ({ f: (u) => { const r = CORE + (1 - CORE) * u; return [r, bandTh(k, r)]; }, len: 2.2, t0: MAP_T + 0.06 * k, dur: 0.8 })),
  { f: (u) => [1, u * Math.PI * 2], len: 6.3, t0: MAP_T + 0.3, dur: 0.8 }, { f: (u) => [CORE, u * Math.PI * 2], len: 1.07, t0: MAP_T, dur: 0.4 },
  ...CUTS.flatMap((cs, k) => cs.map((rc, j): Curve => ({ f: (u) => [rc, bandTh(k, rc) + u * Math.PI / 2], len: rc * Math.PI / 2, t0: MAP_T + 0.25 + 0.5 * rc + 0.05 * ((k * 3 + j) % 4), dur: 0.25 }))),
];
const lot = (k: number, r0: number, r1: number): V2 => { const r = (r0 + r1) / 2; return [r, bandTh(k, r) + Math.PI / 4]; }; // a lot's middle
// pins: [plane r, theta], when it drops, labelled or just a stake. The labelled ones sit in the gaps between the arms (the empty lots).
const E0 = at('pre2/L1/w2'); // "empty"
const PINS: { p: V2; t0: number; label: boolean; only?: Fmt; no916?: boolean }[] = [ // no916 (earth_cut2, gate 2 / fresh eyes): in 9:16 the galaxy fills the safe width, so that label sat ON its arms and read 'VACAN' / 'ACANT'; the stake stays, the label is 16:9 only
  { p: lot(0, 0.5, 0.68), t0: E0, label: true, no916: true }, { p: lot(2, 0.56, 0.72), t0: E0 + 0.16, label: true }, { p: lot(2, 0.9, 1.0), t0: E0 + 0.32, label: true, no916: true },
  { p: lot(0, 0.84, 1.0), t0: E0 + 0.5, label: true, only: '169' }, { p: lot(1, 0.44, 0.6), t0: E0 + 0.66, label: true, only: '169' },
  { p: lot(3, 0.46, 0.64), t0: E0 + 0.24, label: false }, { p: lot(1, 0.78, 1.0), t0: E0 + 0.4, label: false }, { p: lot(3, 0.82, 1.0), t0: E0 + 0.58, label: false, only: '169' },
  { p: lot(0, 0.34, 0.5), t0: E0 + 0.72, label: false }, { p: lot(2, 0.38, 0.56), t0: E0 + 0.8, label: false }, { p: lot(3, 0.28, 0.46), t0: E0 + 0.88, label: false },
];
// ---- his lot (the button of the joke: 100 BILLION LOTS AVAILABLE, and he has bought one tiny one, out past the rim) ----
// A small staked lot with a dotted driveway to the rim, his four moving boxes dropped on it, and a real-estate sign (post, arm,
// hanging board) that swings in on SOLD_T. All of it in his warm white. The 3D him parks beside it and looks at the sign
// (earth_him_wire renders him; here he is one warm placeholder spark, the only warm spark of the slot).
export const SOLD_T = at('pre2/L1') + 1.55;
type Sign = { lot: V2; hw: number; hh: number; skew: number; post: number; top: number; board: [number, number, number, number]; cap: number; parcel: V2; rimTh: number; gate: V2 };
const SIGN: Record<Fmt, Sign> = { // screen units. board = x0, y0, x1, y1; parcel = one box's w, h; rimTh = where the driveway meets the rim (plane angle)
  '169': { lot: [0.64, -0.275], hw: 0.19, hh: 0.07, skew: 0.05, post: 0.565, top: 0.005, board: [0.585, -0.17, 0.885, -0.035], cap: 0.07, parcel: [0.042, 0.032], rimTh: -0.95, gate: [0.45, -0.275] },
  '916': { lot: [-0.28, -0.335], hw: 0.125, hh: 0.04, skew: 0.03, post: -0.35, top: -0.1, board: [-0.33, -0.26, -0.07, -0.142], cap: 0.06, parcel: [0.034, 0.025], rimTh: -3.0, gate: [-0.405, -0.31] },
};
// HIM (hero slot p2_estate): where the 3D him is, per format. rest / from = his centre parked / where he glides in from (off frame);
// half = half his wing span; box = the part of the frame kept empty for him (x0, y0, x1, y1). FROZEN 01:30 Mon Nov 9 (briefs/STATUS_earth_c2_v2.md "HERO SLOTS").
export const HIM_SPOT: Record<Fmt, { rest: V2; from: V2; half: number; box: [number, number, number, number] }> = {
  '169': { rest: [1.30, -0.16], from: [2.25, 0.20], half: 0.36, box: [0.90, -0.62, 1.76, 0.30] },
  '916': { rest: [0.15, -0.22], from: [0.80, -0.10], half: 0.17, box: [-0.04, -0.36, 0.335, -0.09] },
};
export const HIM_IN = 104.27, HIM_REST = 104.90; // frames 3128 -> 3147: he glides in and settles
export function himSpot(t: number, fmt: Fmt): { p: V2; on: number } { // his centre and how much of him is there (0 before he enters, fades with the survey)
  const S = HIM_SPOT[fmt], x = Math.max(0, Math.min(1, (t - HIM_IN) / (HIM_REST - HIM_IN))) - 1, e = 1 + 2.1 * x * x * x + 1.1 * x * x; // ease out, a small overshoot
  return { p: [S.from[0] + (S.rest[0] - S.from[0]) * e, S.from[1] + (S.rest[1] - S.from[1]) * e], on: (t < HIM_IN ? 0 : 1) * (1 - smooth(MAP_OUT, MAP_OUT + 0.5, t)) };
}
// (the one-stroke plotter alphabet GLYPH lives in verse2.ts: the moving boxes' star labels use the same letters)
export { textWidth };
const TXT = new Map<string, V2[]>();
// the dots of a line of text in reading order (so a growing count writes it on); x,y = baseline at the left / centre / right
function textDots(text: string, x: number, y: number, cap: number, align: 'l' | 'c' | 'r', step: number): V2[] {
  const key = `${text}|${x.toFixed(4)}|${y.toFixed(4)}|${cap}|${align}|${step}`; const hit = TXT.get(key); if (hit) return hit;
  const k = cap / 6, out: V2[] = []; let pen = x - (align === 'l' ? 0 : align === 'c' ? 0.5 : 1) * textWidth(text, cap);
  for (const ch of text) { const g = GLYPH[ch];
    for (const st of g.s) for (let i = 0; i + 1 < st.length; i++) { const a = st[i], b = st[i + 1], n = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) * k / step));
      for (let j = i === 0 ? 0 : 1; j <= n; j++) out.push([pen + (a[0] + (b[0] - a[0]) * j / n) * k, y + (a[1] + (b[1] - a[1]) * j / n) * k]); }
    pen += (g.w + GAP) * k; }
  if (TXT.size > 400) TXT.clear(); TXT.set(key, out); return out;
}
const dot = (p: V2, size: number, color: RGB, intensity: number): Flow => flow({ space: 'screen', pts: [p] }, 0, { tail: 0, count: 1, size: size / 2.2, color, intensity });
// title / sub: [x, baseline y, cap height, align]; sub lines are written one after the other. Cap heights at 1080p / 1920: 16:9 title 54 px,
// sub 43 px, VACANT 30 px, SOLD 38 px; 9:16 title 58 px, sub 48 px on two lines, VACANT 38 px, SOLD 58 px, all inside the 9:16 safe zone.
// CUT 2: 9:16 reads top to bottom in the order of the joke: title, 100 BILLION LOTS AVAILABLE, the map, then his one SOLD lot and him.
type Al = 'l' | 'c' | 'r';
const LAYT: Record<Fmt, { title: [number, number, number, Al]; sub: { text: string; at: [number, number, number, Al] }[]; sz: [number, number]; pin: number; xmax: number; step: number; stake: number }> = {
  '169': { title: [-1.615, 0.8, 0.1, 'l'], sub: [{ text: '100 BILLION LOTS AVAILABLE', at: [1.615, 0.81, 0.08, 'r'] }], sz: [10, 9], pin: 0.055, xmax: 1.66, step: 0.007, stake: 0.1 },
  '916': { title: [0, 0.665, 0.06, 'c'], sub: [{ text: '100 BILLION', at: [0, 0.57, 0.05, 'c'] }, { text: 'LOTS AVAILABLE', at: [0, 0.488, 0.05, 'c'] }], /* earth_cut2: was '100 BILLION LOTS' / 'AVAILABLE', a lone word on its own line */ sz: [8.5, 7.5], pin: 0.04, xmax: 0.46, step: 0.0052, stake: 0.075 },
};
// where no VACANT label may go: his box, his sign and lot (a label that fits on neither side of its stake is left off: the stake stays)
const NOGO = (fmt: Fmt): [number, number, number, number][] => { const H = HIM_SPOT[fmt].box, G = SIGN[fmt], m = 0.03;
  return [H, [Math.min(G.post, G.lot[0] - G.hw) - m, G.lot[1] - G.hh - m, Math.max(G.board[2], G.lot[0] + G.hw + G.skew) + m, G.top + m]]; };
const INK: RGB = PAL.ivory, SOLDC: RGB = PAL.ember; // (earth_cut2, gate 7) the survey in Star Ivory; his SOLD lot is the only Ember on the map
// each VACANT label's side of its stake, decided ONCE per format from where the pin is at REF_T (deciding per frame made labels jump
// sides as the galaxy turns): outward if it fits; never in his part of the frame, over the header or over another label; else no label
const SIDES: Partial<Record<Fmt, ('l' | 'r' | null)[]>> = {};
function labelSides(fmt: Fmt): ('l' | 'r' | null)[] {
  const hit = SIDES[fmt]; if (hit) return hit;
  const L = LAYT[fmt], g = GAL[fmt], w = textWidth('VACANT', L.pin), taken = [...NOGO(fmt)];
  taken.push([-9, Math.min(L.title[1], ...L.sub.map((x) => x.at[1])) - 0.02, 9, 9]); // the header
  const out = PINS.map((pin) => {
    if (!pin.label || (pin.only && pin.only !== fmt) || (fmt === '916' && pin.no916)) return null;
    const b = proj(fmt, pin.p[0], pin.p[1] + SPIN(REF_T)), y0 = b[1] + L.stake - L.pin / 2, m = 0.05;
    const free = (x0: number) => x0 >= -L.xmax && x0 + w <= L.xmax && !taken.some((n) => x0 - m < n[2] && x0 + w + m > n[0] && y0 - 0.035 < n[3] && y0 + L.pin + 0.035 > n[1]);
    const xr = b[0] + 0.03, xl = b[0] - 0.03 - w, order: ['l' | 'r', number][] = b[0] >= g.c[0] ? [['r', xr], ['l', xl]] : [['l', xl], ['r', xr]];
    for (const [sd, x0] of order) if (free(x0)) { taken.push([x0, y0, x0 + w, y0 + L.pin]); return sd; }
    return null; });
  return (SIDES[fmt] = out);
}
// the whole survey as a function of time (p2_milky, p2_estate and p2_wish all draw it, so slot blends are seamless)
export type TextBox = { text: string; x0: number; y0: number; x1: number; y1: number; cap: number; box?: [number, number, number, number] }; // box = the container it must fit (the SOLD board)
export function survey(t: number, fmt: Fmt, boxes?: TextBox[]): { flows: Flow[]; sparks: Spark[] } {
  const flows: Flow[] = [], sparks: Spark[] = []; if (t < TITLE_T - 0.05 || t > MAP_OUT + 0.6) return { flows, sparks };
  const L = LAYT[fmt], g = GAL[fmt], ph = SPIN(t), out = 1 - smooth(MAP_OUT, MAP_OUT + 0.5, t);
  const P = (p: V2): V2 => proj(fmt, p[0], p[1] + ph);
  // (budget: the engine draws 9,000 flow particles a frame and the slot blend into p2_wish draws the survey twice, so one survey stays under 4,500)
  for (const c of CURVES) { // plot lines: dotted, quieter than the lettering, so the stars stay the map
    if (t < c.t0) continue; const n = Math.max(2, Math.round(c.len * g.R * 0.8 / (L.step * 2.1))), m = Math.ceil(n * smooth(c.t0, c.t0 + c.dur, t));
    for (let i = 0; i < m; i++) flows.push(dot(P(c.f(i / (n - 1))), 5.2, INK, 1.0 * out));
  }
  const write = (text: string, x: number, y: number, cap: number, al: 'l' | 'c' | 'r', t0: number, dur: number, col: RGB, a: number, sz = 6.2) => {
    if (t < t0) return; const tw = textWidth(text, cap), xl = x - (al === 'l' ? 0 : al === 'c' ? 0.5 : 1) * tw; boxes?.push({ text, x0: xl, y0: y, x1: xl + tw, y1: y + cap, cap });
    const d = textDots(text, x, y, cap, al, L.step), m = Math.ceil(d.length * Math.min(1, (t - t0) / dur));
    for (let i = 0; i < m; i++) flows.push(dot(d[i], sz, col, a * out)); };
  write('MILKY WAY ESTATES', L.title[0], L.title[1], L.title[2], L.title[3], TITLE_T, 0.7, INK, 1.9, L.sz[0]);
  L.sub.forEach((ln, i) => write(ln.text, ln.at[0], ln.at[1], ln.at[2], ln.at[3], MAP_T + 0.3 + 0.34 * i, 0.6 / L.sub.length + 0.1 * i, INK, 1.6, L.sz[1])); // read before his SOLD sign lands (the set-up of the joke)
  const sides = labelSides(fmt);
  const stake = (p: V2, t0: number, label: string | null, col: RGB, side: 'l' | 'r' | null = null) => { // a survey stake: it drops in, overshoots, settles; the label writes on beside its head
    if (t < t0) return; const s = t - t0, grow = Math.min(1, s / 0.12) * (1 + 0.35 * Math.exp(-s * 9) * Math.sin(s * 30)), b = P(p), h: V2 = [b[0], b[1] + L.stake * grow];
    const n = Math.round(L.stake / L.step); for (let i = 0; i <= n; i++) flows.push(dot([b[0], b[1] + (h[1] - b[1]) * i / n], 4.6, col, 1.1 * out));
    sparks.push(spark(h[0], h[1], { size: 9, color: col, intensity: (1.3 + 1.6 * hits(t, [t0], 0.25, 0.04)) * out }));
    if (!label || !side) return;
    const w = textWidth(label, L.pin), right = side === 'r';
    const x = right ? Math.min(h[0] + 0.03, L.xmax - w) : Math.max(h[0] - 0.03, -L.xmax + w); // held inside the safe edge
    write(label, x, h[1] - L.pin / 2, L.pin, right ? 'l' : 'r', t0 + 0.08, 0.28, col, 1.6); };
  PINS.forEach((pin, i) => { if (!pin.only || pin.only === fmt) stake(pin.p, pin.t0, pin.label ? 'VACANT' : null, INK, sides[i]); });
  // ---- his lot: surveyed last, in his warm white ----
  const G = SIGN[fmt], a0 = SOLD_T - 1.05;
  if (t >= a0) {
    const [lx, ly] = G.lot, q: V2[] = [[lx - G.hw - G.skew, ly - G.hh], [lx + G.hw - G.skew, ly - G.hh], [lx + G.hw + G.skew, ly + G.hh], [lx - G.hw + G.skew, ly + G.hh], [lx - G.hw - G.skew, ly - G.hh]];
    line(flows, q, L.step * 1.5, 5.4, SOLDC, 1.7 * out, smooth(a0, a0 + 0.4, t));                                    // the lot
    line(flows, [proj(fmt, 1, G.rimTh), G.gate], L.step * 4.2, 4.4, SOLDC, 0.85 * out, smooth(a0 + 0.25, a0 + 0.55, t)); // a dotted driveway out to it from the rim
    for (let b = 0; b < 4; b++) { // his four moving boxes, dropped on it one by one (verse 2's CHIPS, SNACKS, HUM, LIGHT: he has moved in)
      const tb = SOLD_T - 0.66 + 0.11 * b, sb = t - tb; if (sb < 0) continue;
      const [pw, ph] = G.parcel, fall = Math.min(1, sb / 0.13), bounce = sb > 0.13 ? 0.3 * ph * Math.exp(-(sb - 0.13) * 11) * Math.abs(Math.sin((sb - 0.13) * 21)) : 0;
      const cx = G.post + 0.055 * (pw / 0.05) + pw * 0.5 + b * pw * 1.28, cy = ly - G.hh * 0.25 + ph / 2 + 2.6 * ph * (1 - fall * fall) + bounce, a = Math.min(1, sb / 0.06) * out;
      line(flows, [[cx - pw / 2, cy + ph / 2], [cx + pw / 2, cy + ph / 2], [cx + pw / 2, cy - ph / 2], [cx - pw / 2, cy - ph / 2], [cx - pw / 2, cy + ph / 2]], L.step * 1.1, 4.4, SOLDC, 1.25 * a);
      line(flows, [[cx, cy + ph / 2], [cx, cy + ph * 0.1]], L.step * 1.1, 3.6, SOLDC, 1.0 * a); // tape
    }
    const p0 = SOLD_T - 0.45, armY = G.top - 0.012, [bx0, by0, bx1, by1] = G.board, mx = (bx0 + bx1) / 2; // the sign: post, arm, then the board swings in on SOLD_T
    line(flows, [[G.post, ly - G.hh * 0.2], [G.post, G.top]], L.step * 1.1, 6.4, SOLDC, 1.5 * out, smooth(p0, p0 + 0.2, t));
    line(flows, [[G.post, armY], [bx1 - 0.015, armY]], L.step * 1.1, 5.6, SOLDC, 1.4 * out, smooth(p0 + 0.18, p0 + 0.32, t));
    if (t >= SOLD_T - 0.12) {
      const sw = t - SOLD_T, ang = sw < 0 ? 0.42 : 0.42 * Math.exp(-sw * 3.4) * Math.cos(sw * 10.5), ca = Math.cos(ang), sa = Math.sin(ang), a = smooth(SOLD_T - 0.12, SOLD_T - 0.02, t) * out;
      const Rt = (p: V2): V2 => { const dx = p[0] - mx, dy = p[1] - armY; return [mx + dx * ca - dy * sa, armY + dx * sa + dy * ca]; }; // it hangs from the arm and swings about it
      const flash = 1 + 1.3 * hits(t, [SOLD_T], 0.3, 0.05);
      line(flows, [[bx0, by1], [bx1, by1], [bx1, by0], [bx0, by0], [bx0, by1]].map((p) => Rt(p as V2)), L.step * 1.05, 6.0, SOLDC, 1.5 * a * flash);
      for (const hx of [bx0 + 0.04, bx1 - 0.04]) line(flows, [Rt([hx, armY]), Rt([hx, by1])], L.step * 1.1, 4.0, SOLDC, 1.1 * a);
      const d = textDots('SOLD', mx, (by0 + by1) / 2 - G.cap / 2, G.cap, 'c', L.step), tw = textWidth('SOLD', G.cap);
      for (const p of d) flows.push(dot(Rt(p), L.sz[0], [1.0, 0.86, 0.66], 1.9 * a * flash));
      boxes?.push({ text: 'SOLD', x0: mx - tw / 2, y0: (by0 + by1) / 2 - G.cap / 2, x1: mx + tw / 2, y1: (by0 + by1) / 2 + G.cap / 2, cap: G.cap, box: G.board });
    }
  }
  // HIM: his placeholder (the ONE warm spark of this slot; earth_him_wire finds his place by it and hides it under the 3D him)
  { const hs = himSpot(t, fmt); sparks.push(spark(hs.p[0], hs.p[1], { size: 22, intensity: 1.9 * hs.on * out })); }
  return { flows, sparks };
}

// ---- fireworks: each star belongs to one burst; it rushes to the burst's centre, then flies out along a spoke and droops ----
const T0 = at('pre2/L3/w4'); // "celebrate"
const BURSTS: { c: [number, number]; R: number; dt: number; w: number; col: RGB }[] = [ // 16:9 centre, radius, s after "celebrate", share of stars
  { c: [-0.95, 0.38], R: 0.4, dt: 0.0, w: 4, col: C.her }, { c: [0.25, 0.56], R: 0.46, dt: 0.3, w: 5, col: C.violet }, { c: [1.1, 0.32], R: 0.36, dt: 0.58, w: 4, col: C.teal },
  { c: [-0.38, 0.64], R: 0.28, dt: 0.92, w: 3, col: C.her }, { c: [0.8, 0.7], R: 0.14, dt: 1.42, w: 1, col: C.violet }, // the last one: small, late, alone
];
const PICK = BURSTS.flatMap((b, i) => Array.from({ length: b.w }, () => i));
const R = rng(77); const DIRS = Array.from({ length: 4000 }, () => [R(), R(), R()]);
const S = (fmt: Fmt, p: [number, number]): [number, number] => (fmt === '169' ? p : [p[0] * 0.36, p[1] * 0.75 + 0.08]); // sky points for 9:16
const fire = (i: number, t: number, home: [number, number], _n: number, fmt: Fmt): [number, number] => {
  if (i % 4 === 0) return home; // a quarter of the sky stays put
  const d = DIRS[i % DIRS.length], bi = PICK[Math.floor(d[0] * PICK.length) % PICK.length], b = BURSTS[bi], tb = T0 + b.dt, [cx, cy] = S(fmt, b.c), k = fmt === '916' ? 0.62 : 1;
  if (t < tb - 0.5) return home;
  if (t < tb) { const u = Math.pow((t - (tb - 0.5)) / 0.5, 2); return [home[0] + (cx - home[0]) * u, home[1] + (cy - home[1]) * u]; }
  const nSp = 16 + bi * 2, a = (Math.floor(d[1] * nSp) / nSp) * Math.PI * 2 + (d[2] - 0.5) * 0.05 + bi, m = 0.22 + 0.78 * Math.pow(d[2], 0.6);
  const s = t - tb, rad = b.R * k * m * (1 - Math.exp(-s * 3.4));
  return [cx + Math.cos(a) * rad, cy + Math.sin(a) * rad - 0.07 * k * s * s];
};
const HER = { hisOff: 1, hisWarm: 0.5, herCyan: 1.3, forest: 1.6, rivers: 1.3, violet: 1 }; // she stays as verse 2 left her
// 9:16: the tilt up to the sky would take her out of the frame (cut 1 / polish: "she is still only a sliver at the bottom"), so in 9:16
// she stays where the move-out shot had her: her limb glows in the bottom quarter under the map, his lot and him. (camFor: y9 = y * 0.8)
const cam9 = (c: { fmt: Fmt; base: { cam: { y: number } } }) => (c.fmt === '916' ? { cam: { y: Math.max(c.base.cam.y, -2.375) } } : {});
const milky: Builder = (c) => { // box 4 ships, the rocket leaves into the Milky Way, the sky becomes the map
  const m = moveOut(c), k = smooth(at('pre2/L0') + 0.4, at('pre2/L0') + 1.8, c.t), a = herAfter(c.t, m.packed);
  const sv = survey(c.t, c.fmt);
  return { ...cam9(c), flows: [...m.flows, ...sv.flows], sparks: [...m.sparks, ...sv.sparks], grade: { ...a, ...HER, glow: lerp(a.glow, 0.95, k), aurora: lerp(a.aurora, 0.25, k), atmos: lerp(a.atmos, 1.1, k), motes: lerp(a.motes, 0.5, k), mist: lerp(0.6, 0.95, k), stars: lerp(QUIET.stars, SKY.stars, k), deep: QUIET.deep, galaxy: lerp(QUIET.galaxy, SKY.galaxy, k) } };
};
// the sky under the survey: the cast stars are the galaxy, so the deep field and the Milky Way mist stay low (they come back in p2_wish)
const SKY = { ...HER, glow: 0.95, aurora: 0.25, atmos: 1.1, motes: 0.5, mist: 0.95, stars: 1.9, deep: QUIET.deep, galaxy: 0.3, bloom: 0.8, bloomThreshold: 0.24 };
export const pre2: Section = {
  name: 'pre2',
  camera: [
    // E: tilt up from verse 2's horizon: she sinks to the bottom edge, the sky is the subject
    { at: 'pre2/L0+1.5', cam: { x: 0, y: -2.95, r: 2.2, lon: lonAt(-106, 'pre2/L0+1.5'), lat: -22, roll: 0, sun: [0.4, -0.2, -0.9], par: [0, 0.05] }, ease: 'smooth' },
    { at: 'pre2/L3-0.02', cam: { lon: lonAt(-112, 'pre2/L3'), par: [-0.05, 0.03] }, ease: 'linear' },
    // F: cut on "But" to her night side (Africa / Europe, near chorus 2's side of her), fireworks above her horizon
    { at: 'pre2/L3', cam: { x: 0, y: -1.35, r: 1.25, lon: lonAt(12, 'pre2/L3'), lat: -20, roll: -4, sun: [0.5, -0.5, -0.7], par: [0.15, -0.1] }, ease: 'hold' },
    { at: 'pre2/L3+2.4', cam: { r: 1.31, y: -1.4 }, ease: 'linear' },
    // G: back away, small and alone, turning toward chorus 2's view (its own key at chorus2/L0 swoops in from here)
    { at: 'chorus2/L0-0.5', cam: { x: 0, y: -0.2, r: 0.52, lon: -31, lat: 3, roll: -11, sun: [0.8, 0.1, -0.55], par: [0.05, 0] }, ease: 'smooth' },
  ],
  stars: [
    { at: GAL_T, set: GALAXY, dur: 1.15, straggle: 0.2, curve: 0.3 },            // LIGHT lets go: its stars (and the rest of the sky) swirl into the galaxy
    { at: MAP_OUT, set: { kind: 'sky' }, dur: 1.5, straggle: 0.2, curve: 0.25 },
    // starts right after the cut and takes 0.6 s, so the stars come to the front layer gradually (in one frame they would pop on over her disk);
    // fire() itself keeps every star at home until its burst gathers (from T0 - 0.5)
    { at: T0 - 1.1, set: { kind: 'fn', fn: fire, front: true }, dur: 0.6, straggle: 0, curve: 0 },
    { at: 'pre2/L3+2.83', set: { kind: 'sky' }, dur: 1.15, straggle: 0.2 },    // embers drift home before chorus 2
  ],
  builders: {
    p2_milky: milky,
    p2_estate: (c) => ({ ...cam9(c), ...survey(c.t, c.fmt), grade: { ...SKY } }),
    p2_wish: (c) => { // the map lets go; one shooting star (the wish she doesn't make)
      const w = at('pre2/L2/w3'), u = (c.t - (w - 0.08)) / 0.6, p: [number, number][] = [S(c.fmt, [-1.6, 0.50]), S(c.fmt, [1.0, 0.18])];
      const sv = survey(c.t, c.fmt);
      const home = smooth(0.15, 0.9, c.u); // the map lets go and the whole sky comes back
      return { ...cam9(c), sparks: sv.sparks, grade: { ...SKY, stars: lerp(SKY.stars, 0.55, smooth(MAP_OUT - 0.1, MAP_OUT + 0.4, c.t)) + 0.45 * smooth(MAP_OUT + 1.0, MAP_OUT + 1.65, c.t), // held low while the stars fly home (the engine brightens stars that travel: at full gain the release was a white cloud, brighter than the wish)
        mist: lerp(0.95, 0.6, c.u), deep: lerp(SKY.deep, 1, home), galaxy: lerp(SKY.galaxy, 1, home) },
        flows: u > 0 && u < 1.6 ? [...sv.flows, flow({ space: 'screen', pts: p }, u * 1.35, { tail: 0.4, count: 220, size: 8, color: PAL.ivory, intensity: 3.0 * (1 - smooth(0.9, 1.5, u)) })] : sv.flows };
    },
    p2_celebrate: (c) => { // fireworks over her night side; her own glow stays where it was (the hollow part)
      const t = c.t, fade = smooth(T0 + 1.3, T0 + 2.5, t);
      return { grade: { ...HER, glow: lerp(1.0, 0.85, fade), stars: lerp(1.0, 1.75, smooth(T0 - 0.5, T0, t)) * lerp(1, 0.5, fade), bloom: 0.7, aurora: 0.2, mist: 0.5, motes: 0.5, atmos: 1.1,
          deep: lerp(1, 0.18, smooth(T0 - 0.9, T0 - 0.2, t)), galaxy: lerp(1, 0.45, smooth(T0 - 0.9, T0 - 0.2, t)) }, // the sky goes quiet as the stars gather
        flows: BURSTS.flatMap((b, bi) => { // her colours under the star bursts: streaks out along the same spokes, drooping, gone in a second
          const s = t - (T0 + b.dt); if (s < 0 || s > 1.5) return [];
          const p = S(c.fmt, b.c), k = c.fmt === '916' ? 0.62 : 1, nSp = 16 + bi * 2, rad = b.R * k * (1 - Math.exp(-s * 3.4)), a = 1.5 * (1 - smooth(0.25, 1.4, s));
          return Array.from({ length: nSp }, (_, j) => { const an = (j / nSp) * Math.PI * 2 + bi;
            return flow({ space: 'screen', pts: [p, [p[0] + Math.cos(an) * rad, p[1] + Math.sin(an) * rad - 0.07 * k * s * s]] }, 1, { tail: 0.55, count: 26, size: 6, color: b.col, intensity: a }); });
        }),
        sparks: BURSTS.map((b) => { const p = S(c.fmt, b.c); return spark(p[0], p[1], { size: 60 * b.R, color: b.col, intensity: 2.4 * hits(t, [T0 + b.dt], 0.22, 0.04) }); }) };
    },
  },
};
withLookB(pre2.builders); // the lux look under every slot (before the hand-over below: chorus 2's own shot keeps chorus 2's look)
cutTo(pre2.builders, 'p2_wish', pre2.builders.p2_celebrate, 'p2_celebrate', at('pre2/L3'), at('chorus2/L0')); // the cut on "But" stays a cut
// SEAM (earth_first_cut, Nov 8): chorus 2 opens on a hard cut (its first camera key is a 'hold'). The engine cross-fades every slot
// change over 0.45 s, so the fireworks grade/sparks faded over chorus 2's first shot, and in 9:16 its own framing arrived as a whip.
// From the downbeat on, p2_celebrate draws chorus 2's first slot (the fix earth_sec_c2 asked for; same idea as pre1.ts hardCut).
// Pulses are left to the incoming side only (the engine adds both sides' pulses during the blend).
{ const mine = pre2.builders.p2_celebrate, tC = at('chorus2/L0'), t1 = at('chorus2/L1');
  pre2.builders.p2_celebrate = (c) => { if (c.t < tC) return mine(c);
    const o = chorus2.builders.c2_space({ ...c, slot: { ...c.slot, id: 'c2_space', t0: tC, t1 }, lt: c.t - tC, u: Math.min(1, (c.t - tC) / (t1 - tC)), dur: t1 - tC });
    return { ...o, pulses: [] }; }; }
