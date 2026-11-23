// 8B (+8C's time, one shot) "Hit me with a four-two-nine / Rate, rate, rate limited": THE 429 moment of section 8.
// rl_cut1 B (Nov 15): S15 NS4 swapped in (rl_stills_street, 5760x4320: the block holding its breath / the digits / the tenants
// / the tail, window masks). Plate drawn 4:3 (2560x1920 stage, Cam ph 1920); the approved 8B framing = frame_16x9 (y 240-1680).
//  - 8B: the crane starts low and tight on the hero (1.75x, the plate file is 4480 px = 1:1 there) with the whole block dark;
//    each sung digit LIGHTS FLOOR BY FLOOR (a mask sweep up its windows over 4 frames) with a warm glow pop and a camera hit:
//    4 on the hero, 2 on the right neighbour, 9 on the far right; the crane pulls up and back so the frame lands on the full
//    approved block on "nine" (thumbnail frame) and the tail in the sky twitches.
//  - 8C: one tenant window per "Rate" bursts on (snap push to it, its blinds light, the silhouettes: Merge Conflict stop
//    arguing, Spinning Cursor stops pacing; Graceful Shutdown stays asleep); on "limited" the crane snaps back to the whole
//    block and every digit flares. Street clock hands drawn at 4:37 (the plate's are removed).
//  The 4 (curtained rooms, mean 158 vs 186-193 for the 2 and 9) uses n4_d4b.png: x1.16 then the same knee.
//  Highlights: every layer kneed to <= 248, glows are plain alpha-over in colours <= 236 (cannot clip).
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, inOutCubic, lerp, outCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, Grain, flick, hit, pendulum } from '../s07/_lib';
import { Tenant } from '../first30/street';
import B from './cut1b.json';

const N4 = (B as any)['8B'];
const FROM = 3761, PH = N4.ph as number;
const bx = (b: number[]) => ({ position: 'absolute' as const, left: b[0], top: b[1], width: b[2] - b[0], height: b[3] - b[1] });
type DG = '4' | '2' | '9';
type TN = 'merge' | 'cursor' | 'shutdown';
const RATES = [3830, 3848, 3865].map((x) => x - FROM), LIMITED = 3882 - FROM;   // 8C's beat grid
const TEN: TN[] = ['merge', 'cursor', 'shutdown'];

/** a digit: its windows fill bottom -> top over 4 frames from `at`, a glow that pops then settles; `flare` adds on top */
const Digit: React.FC<{ d: DG; f: number; at: number; flare: number }> = ({ d, f, at, flare }) => {
  if (f < at) return null;
  const D = N4.digits[d]; const k = clamp((f - at) / 4);
  const p = lerp(-14, 104, outCubic(k));                                  // the sweep line, % from the bottom of the layer
  const mask = `linear-gradient(to top, #000 ${p}%, transparent ${p + 12}%)`;
  const pop = Math.exp(-Math.max(0, f - at - 2) / 7);
  const glow = clamp(0.62 + 0.38 * pop + flare) * clamp((f - at) / 3);
  return (
    <>
      <Img src={staticFile(`cut1/b/n4_g${d}.png`)} style={{ ...bx(D.glow), opacity: glow }} />
      <Img src={staticFile(`cut1/b/n4_d${d === '4' ? '4b' : d}.png`)} style={{ ...bx(D.box), WebkitMaskImage: mask, maskImage: mask, opacity: 0.88 + 0.12 * flick(f, at) }} />
    </>
  );
};
/** a tenant window bursting on: blinds lit (S15 tenants pass), the code silhouettes, a glow pop; they freeze 8 frames in */
const TenantWin: React.FC<{ n: TN; f: number; at: number }> = ({ n, f, at }) => {
  if (f < at) return null;
  const T = N4.tenants[n]; const w = T.win; const k = flick(f, at);
  const pop = Math.exp(-Math.max(0, f - at - 1) / 6);
  const gFrozen = FROM + Math.min(f, at + 8);                             // the joke: they stop and stare
  return (
    <>
      <Img src={staticFile(`cut1/b/n4_tg_${n}.png`)} style={{ ...bx(T.glow), opacity: k * (0.55 + 0.45 * pop) }} />
      <Img src={staticFile(`cut1/b/n4_t_${n}.png`)} style={{ ...bx(T.box), opacity: k }} />
      <div style={{ ...bx(w), opacity: k, overflow: 'hidden' }}><Tenant kind={n} w={w[2] - w[0]} h={w[3] - w[1]} g={n === 'shutdown' ? FROM + f : gFrozen} /></div>
    </>
  );
};
/** the street clock's hands at 4:37 (the still's face has none) */
const Hands: React.FC<{ h: number; m: number }> = ({ h, m }) => {
  const [cx, cy] = N4.clock.c as number[]; const r = N4.clock.r as number;
  const hand = (a: number, len: number, w: number) => (
    <div style={{ position: 'absolute', left: cx - w / 2, top: cy - len, width: w, height: len + w, borderRadius: w / 2, background: '#16171a', transformOrigin: `${w / 2}px ${len}px`, transform: `rotate(${a}deg)` }} />);
  return <div style={{ filter: 'blur(0.5px)' }}>{hand(((h % 12) + m / 60) * 30, r * 0.64, 3)}{hand(m * 6, r * 0.95, 2.2)}<div style={{ position: 'absolute', left: cx - 2.5, top: cy - 2.5, width: 5, height: 5, borderRadius: 3, background: '#16171a' }} /></div>;
};

const cueOf = (shot: ShotProps['shot'], w: string, d: number) => { const c = (shot.cues ?? []).find((x) => x.word.startsWith(w)); return c ? c.frame - FROM : d; };
const D4 = N4.digits['4'].c as number[], D2 = N4.digits['2'].c as number[], D9 = N4.digits['9'].c as number[];
const tw = (n: TN) => { const w = N4.tenants[n].win; return [(w[0] + w[2]) / 2, (w[1] + w[3]) / 2]; };
/** the crane: [frame, scale, cx, cy] keys (plate px of the 4:3 stage); full approved block = s 1, cy 960 */
const keysOf = (four: number, two: number, nine: number): [number, number, number, number][] => [
  [0, 1.75, D4[0], 1290], [four - 2, 1.62, D4[0] + 20, 1190], [two, 1.3, (D4[0] + D2[0]) / 2 + 60, 1040], [nine + 4, 1.0, 1280, 960], [RATES[0] - 1, 1.02, 1280, 960],
  [RATES[0] + 5, 1.45, tw('merge')[0], tw('merge')[1]], [RATES[1] - 1, 1.48, tw('merge')[0] + 10, tw('merge')[1]],
  [RATES[1] + 5, 1.6, tw('cursor')[0], tw('cursor')[1]], [RATES[2] - 1, 1.63, tw('cursor')[0], tw('cursor')[1]],
  [RATES[2] + 5, 1.75, tw('shutdown')[0], tw('shutdown')[1]], [LIMITED - 1, 1.78, tw('shutdown')[0], tw('shutdown')[1]],
  [LIMITED + 7, 1.0, 1280, 960], [200, 1.015, 1280, 960]];
const crane = (f: number, K: [number, number, number, number][]) => {
  let i = 0; while (i < K.length - 2 && f >= K[i + 1][0]) i++;
  const a = K[i], b = K[i + 1]; const k = inOutCubic(clamp((f - a[0]) / Math.max(1, b[0] - a[0])));
  const s = lerp(a[1], b[1], k), hw = 1280 / s, hh = 720 / s;
  return { s, cx: clamp(lerp(a[2], b[2], k), hw, 2560 - hw), cy: clamp(lerp(a[3], b[3], k), hh, PH - hh) };
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const g = shot.from + useCurrentFrame(); const f = g - FROM;
  const four = cueOf(shot, 'four', 17), two = cueOf(shot, 'two', 24), nine = cueOf(shot, 'nine', 36);
  const { s: s0, cx, cy } = crane(f, keysOf(four, two, nine));
  const s = s0 * (1 + hit(f, four, 0.012, 10) + hit(f, two, 0.012, 10) + hit(f, nine, 0.022, 14) + RATES.reduce((m, r) => m + hit(f, r + 5, 0.012, 10), 0) + hit(f, LIMITED + 7, 0.02, 14));
  const flare = f >= LIMITED ? 0.5 * Math.exp(-(f - LIMITED) / 10) : 0;   // on "limited": every digit flares
  const tailA = pendulum(f, nine, 3.2, 16) + RATES.reduce((m, r) => m + pendulum(f, r, 1.4, 12), 0);
  const T = N4.tail; const piv = T.pivot as number[];
  return (
    <AbsoluteFill>
    <Cam cx={cx} cy={cy} s={s} ph={PH}>
      <Img src={staticFile('cut1/b/n4_none.jpg')} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: PH }} />
      <Img src={staticFile('cut1/b/n4_tail.png')} style={{ ...bx(T.box), transformOrigin: `${piv[0] - T.box[0]}px ${piv[1] - T.box[1]}px`, transform: `rotate(${tailA.toFixed(3)}deg)` }} />
      <Hands h={4} m={37} />
      <Digit d="4" f={f} at={four} flare={flare} /><Digit d="2" f={f} at={two} flare={flare} /><Digit d="9" f={f} at={nine} flare={flare} />
      {TEN.map((n, i) => <TenantWin key={n} n={n} f={f} at={RATES[i]} />)}
      <AbsoluteFill style={{ pointerEvents: 'none', height: PH, opacity: flare * 0.5, background: 'radial-gradient(ellipse at 55% 55%, rgba(236,168,92,0.22), rgba(0,0,0,0) 70%)' }} />
    </Cam>
    <Grain g={g} />
    </AbsoluteFill>
  );
};
// 9:16: the crop follows what the beat is about: the digit being sung (4 -> 2 -> 9), then each tenant window, then the 2
// (the block's middle) on "limited" (plate x -> screen x through the crane)
const SUBJ = (f: number, two: number, nine: number) => {
  const seq: [number, number][] = [[0, D4[0]], [two, D2[0]], [nine, D9[0]], [RATES[0], tw('merge')[0]], [RATES[1], tw('cursor')[0]], [RATES[2], tw('shutdown')[0]], [LIMITED, D2[0]]];
  let i = 0; while (i < seq.length - 1 && f >= seq[i + 1][0]) i++;
  const prev = i > 0 ? seq[i - 1][1] : seq[0][1];
  return lerp(prev, seq[i][1], inOutCubic(clamp((f - seq[i][0]) / 6)));
};
export const S8_8B: ShotDef = { stage: Stage, cx916: (fl, shot) => {
  const f = shot.from + fl - FROM; const two = cueOf(shot, 'two', 24), nine = cueOf(shot, 'nine', 36), four = cueOf(shot, 'four', 17);
  const { s, cx } = crane(f, keysOf(four, two, nine));
  return clamp(((SUBJ(f, two, nine) - cx) * s + 1280) / 2560, 0.16, 0.84); } };
// rl_fix2_end (Nov 16): 8C is its own picture now (the watch: "a second take of 8B's windows"). A hard cut on the first "Rate" to a
// closer row of the block (2.9-3.05x; S15 NS4 at its native 2.25x: public/fix2/end/n4_row.jpg, stage 150..1290 x 790..1430): the three
// tenant windows in one frame, one bursting on per "Rate" (the same TenantWin layers), a slow push; on "limited" it cuts to
// 8B's crane snapping back to the whole block with the flare.
const ROW = { x: 150, y: 790, w: 1140, h: 640 }, ROW_C = { x: 713, y: 1101 };
// rl_fix3_b (Nov 16, WATCH2 8C: "in its last ~0.3 s it cuts back to the 8B wide ... reads as a stray cut"): 8C now stays on the
// row to its last frame. "limited" lands ON the row instead: all three tenant windows flare (an extra glow pass, alpha-over, colours
// <= 236 so nothing clips) and a harder push-hit; the slow push carries on to the cut to 8D.
const Stage8C: React.FC<ShotProps> = (props) => {
  const g = props.shot.from + useCurrentFrame(); const f = g - FROM;
  const k = clamp((f - RATES[0]) / (props.shot.to - FROM - 1 - RATES[0]));
  const s = lerp(2.9, 3.05, inOutCubic(k)) * (1 + RATES.reduce((m, r) => m + hit(f, r, 0.016, 9), 0) + hit(f, LIMITED, 0.025, 12));
  const flare = f >= LIMITED ? 0.45 * clamp((f - LIMITED + 1) / 2) * Math.exp(-Math.max(0, f - LIMITED - 2) / 9) : 0;
  return (
    <AbsoluteFill>
      <Cam cx={ROW_C.x} cy={ROW_C.y} s={s} ph={PH}>
        <Img src={staticFile('fix2/end/n4_row.jpg')} style={{ position: 'absolute', left: ROW.x, top: ROW.y, width: ROW.w, height: ROW.h }} />
        {TEN.map((n, i) => <TenantWin key={n} n={n} f={f} at={RATES[i]} />)}
        {flare > 0 ? TEN.map((n) => <Img key={`fl_${n}`} src={staticFile(`cut1/b/n4_tg_${n}.png`)} style={{ ...bx(N4.tenants[n].glow), opacity: flare }} />) : null}
      </Cam>
      <Grain g={g} />
    </AbsoluteFill>
  );
};
export const S8_8C: ShotDef = { stage: Stage8C, cx916: (fl, shot) => {
  const f = shot.from + fl - FROM;   // rl_fix3_b: on "limited" a crop cut on the beat (like each "Rate") to merge + shutdown in one frame (x 585:
  // both lit windows inside the 270 stage-px crop), no cut back to the 8B crane
  const i = RATES.filter((r) => f >= r).length - 1; const x = f >= LIMITED ? 585 : tw(TEN[Math.max(0, i)])[0];
  return clamp(((x - ROW_C.x) * 2.95 + 1280) / 2560, 0.16, 0.84); } };
