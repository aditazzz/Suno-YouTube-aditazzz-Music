// 2C, the knocks (first30.md): her side of the door; three knocks on the three "Rate"s, each a soft ripple on the glass
// like a dead touch screen (rl_screens glass_2C_ripple highlight, pinned to the glass), a 1-frame camera tick and a
// sheen shift. (He lowers the paddle on beat 4 in the plan: needs the D1p region still from S7, not in this version.)
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { Cam, PlateImg } from './kit';
import { DOOR, GlassSheen } from './door';
import assets from './assets.json';
import { tealSrc } from './teal';
import { At7, GlassSheen7, HAVE_S7, Locks7, Plate7, S7, box7 } from './door7';
import { frameOf } from '../../timing';
import { Img, staticFile } from 'remotion';
import { keys } from './kit';
import { outBack } from './v3ease';

const RIP = (assets as any).ripple as { frames: number[] };

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const knocks = (shot.cues ?? []).map((c) => c.frame - shot.from);   // -1, 8, 18 (the first is sung on the cut)
  const tick = knocks.some((k) => f === Math.max(0, k)) ? 1 : 0;
  const sheen = 0.38 + 0.035 * knocks.filter((k) => f >= Math.max(0, k)).length;
  const fr = clamp(g, RIP.frames[0], RIP.frames[RIP.frames.length - 1]);
  const s = lerp(1.03, 1.06, clamp(f / (shot.dur - 1))) * (1 + 0.005 * tick);
  return (
    <Cam cx={1290 + tick * 4} cy={700} s={s}>
      <PlateImg src={DOOR.plate} />
      <ScreenInsert corners={DOOR.glass} w={1360} h={1620} src={`first30/ripple/f_${String(fr).padStart(5, '0')}.png`} />
      {tick ? <AbsoluteFill style={{ opacity: 0.3 }}><ScreenInsert corners={DOOR.glass} w={1360} h={1620} src={`first30/ripple/f_${String(fr).padStart(5, '0')}.png`} /></AbsoluteFill> : null}
      <ScreenInsert corners={DOOR.glass} w={1360} h={1620}><GlassSheen pos={sheen} k={0.9} /></ScreenInsert>
    </Cam>
  );
};

// v2 (rl_first30_v2): the real S7 D1 door, locks locked. He holds the paddle up beside his head (D1p, continuing 2B) and
// lowers it on beat 4 (a 2-frame blend to D1 = paddle parked). The three knocks ripple on the glass (rl_screens ripple
// pinned to the S7 leaf), each knock's first frame +30% ripple opacity (CD: soft at phone size), a 1-frame tick, sheen shift.
const Stage7: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const knocks = (shot.cues ?? []).map((c) => c.frame - shot.from);
  const tick = knocks.some((k) => f === Math.max(0, k)) ? 1 : 0;
  const sheen = 0.38 + 0.035 * knocks.filter((k) => f >= Math.max(0, k)).length;
  const fr = clamp(g, RIP.frames[0], RIP.frames[RIP.frames.length - 1]);
  const lower = frameOf(shot.grid?.[3] ?? 27.526) - shot.from;      // beat 4
  const up = 1 - clamp((f - lower) / 2);
  const s = lerp(1.08, 1.12, clamp(f / (shot.dur - 1))) * (1 + 0.005 * tick);
  const b = box7(S7.leafBox);
  const glass = [[b.left, b.top], [b.left + b.width, b.top], [b.left + b.width, b.top + b.height], [b.left, b.top + b.height]] as any;
  const rip = `first30/ripple/f_${String(fr).padStart(5, '0')}.png`;
  return (
    <Cam cx={1280 + tick * 4} cy={760} s={s}>
      <Plate7 name="D1" />
      {up > 0 ? <At7 file="D1p_region.jpg" box={S7.d1p} opacity={up} /> : null}
      <Locks7 k={3} />
      <ScreenInsert corners={glass} w={1360} h={1620} src={rip} />
      {tick ? <AbsoluteFill style={{ opacity: 0.3 }}><ScreenInsert corners={glass} w={1360} h={1620} src={rip} /></AbsoluteFill> : null}
      <GlassSheen7 pos={sheen} k={0.9} />
    </Cam>
  );
};

// ---- v3 (rl_first30_v3, CD V3 order 3: "2C reverse, over his shoulder": her number-two 429 moment) ----
const knockFrames = (shot: ShotProps['shot']) => (shot.cues ?? []).map((c) => Math.max(0, c.frame - shot.from));   // 0, 8, 18
const lowerAt = (shot: ShotProps['shot']) => frameOf(shot.grid?.[3] ?? 27.526) - shot.from;                        // beat 4

// FALLBACK (the 2C stills not in): the v2 door, a stepped push on each knock toward his raised paddle,
// 1.0 -> 1.2 -> 1.4 -> 1.55 (the disc is 0.103 H in D1p at 1.0, so 0.16 H by the third knock). Each step lands in 3 frames
// with a small overshoot (outBack), then a slow creep so no frame freezes. Aim: between his face and the disc.
const PADDLE7 = p7c(2567, 1314), FACE7 = p7c(2127, 1319);
function p7c(x: number, y: number) { return [x * 2560 / 4320, y * 2560 / 4320]; }
const Stage7Step: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const K = knockFrames(shot);
  const tick = K.some((k) => f === k) ? 1 : 0;
  const sheen = 0.38 + 0.035 * K.filter((k) => f >= k).length;
  const fr = clamp(g, RIP.frames[0], RIP.frames[RIP.frames.length - 1]);
  const lower = lowerAt(shot); const up = 1 - clamp((f - lower) / 2);
  const lv = [1.0, 1.2, 1.4, 1.55];
  let s = lv[0];
  K.forEach((k, i) => { if (f >= k) s = lerp(lv[i], lv[i + 1], outBack(clamp((f - k) / 3))); });
  s *= 1 + 0.012 * clamp(f / (shot.dur - 1));
  const aim = clamp((s - 1) / 0.55);
  const cx = lerp(1280, (PADDLE7[0] + FACE7[0]) / 2 + 40, aim), cy = lerp(760, PADDLE7[1] - 10, aim);
  const b = box7(S7.leafBox);
  const glass = [[b.left, b.top], [b.left + b.width, b.top], [b.left + b.width, b.top + b.height], [b.left, b.top + b.height]] as any;
  const rip = `first30/ripple/f_${String(fr).padStart(5, '0')}.png`;
  return (
    <Cam cx={cx + tick * 4} cy={cy} s={s * (1 + 0.005 * tick)}>
      <Plate7 name="D1" />
      {up > 0 ? <At7 file="D1p_region.jpg" box={S7.d1p} opacity={up} /> : null}
      <Locks7 k={3} />
      <ScreenInsert corners={glass} w={1360} h={1620} src={rip} />
      {tick ? <AbsoluteFill style={{ opacity: 0.3 }}><ScreenInsert corners={glass} w={1360} h={1620} src={rip} /></AbsoluteFill> : null}
      <GlassSheen7 pos={sheen} k={0.9} />
    </Cam>
  );
};
const cxStep = (f: number, shot: ShotProps['shot']) => {
  const K = knockFrames(shot); const n = K.filter((k) => f >= k).length;
  return lerp(0.5, 0.56, clamp(n / 3));        // the 9:16 crop leans toward the disc as the push lands
};

// THE STILLS (rl_stills_2c_locks, build/stills/S7_2C): K0 knuckles back / K1 knuckles on the glass / P2 paddle lowered.
// The camera behind him: his shoulder + the raised 429 big in the foreground, her knocking beyond the glass. On each knock
// K1 for the contact frame and the next, a ripple ring on the glass at her knuckle, a 1-frame tick; on beat 4 a 2-frame
// lower (K0 -> P2); a slow push 1.0 -> 1.06 toward the knock point.
const A2 = assets as any;
export const HAVE_2C = !!A2['S7_2C/K0'] && !!A2['S7_2C/K1'];
const L2 = A2.S7_2C_layout ?? {};
const SZ2 = (L2.size ?? [4320, 2430]) as number[]; const K2 = 2560 / SZ2[0];
const KNOCK2 = ((L2.knock_px ?? [SZ2[0] * 0.585, SZ2[1] * 0.45]) as number[]).map((v) => v * K2);
const full2: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };
const Plate2C: React.FC<{ n: string; o?: number }> = ({ n, o = 1 }) => <Img src={staticFile(tealSrc(`first30/S7_2C/${n}.jpg`))} style={{ ...full2, opacity: o }} />;
const Ring: React.FC<{ d: number }> = ({ d }) => {
  // a dead-touchscreen ripple: a thin bright ring and a soft inner wash, expanding over 12 frames, faint at phone size by design
  if (d < 0 || d > 12) return null;
  const k = d / 12, r = lerp(18, 260, Math.sqrt(k)), o = 0.42 * (1 - k) * (1 - k);
  return (
    <div style={{ position: 'absolute', left: KNOCK2[0] - r, top: KNOCK2[1] - r * 0.92, width: 2 * r, height: 2 * r * 0.92, borderRadius: '50%', opacity: o,
      background: 'radial-gradient(closest-side, rgba(220,232,240,0.10) 0%, rgba(220,232,240,0.06) 70%, rgba(235,245,255,0.85) 92%, rgba(235,245,255,0) 100%)', mixBlendMode: 'screen' }} />
  );
};
const Stage2CK: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const K = knockFrames(shot);
  const contact = K.some((k) => f === k || f === k + 1);
  const tick = K.some((k) => f === k) ? 1 : 0;
  const lower = lowerAt(shot); const lw = clamp((f - lower) / 2);
  const last = [...K].reverse().find((k) => f >= k);
  const s = lerp(1.0, 1.06, clamp(f / (shot.dur - 1))) * (1 + 0.005 * tick);
  const cx = lerp(1280, lerp(1280, KNOCK2[0], 0.35), clamp(f / (shot.dur - 1))), cy = 720;
  const base = lw >= 1 && A2['S7_2C/P2'] ? 'P2' : contact ? 'K1' : 'K0';
  return (
    <Cam cx={cx + tick * 4} cy={cy} s={s}>
      <Plate2C n={base} />
      {lw > 0 && lw < 1 && A2['S7_2C/P2'] ? <Plate2C n="P2" o={lw} /> : null}
      {K.map((k, i) => <Ring key={i} d={f - k} />)}
      {last !== undefined && f - last < 1 ? <AbsoluteFill style={{ background: 'rgba(255,255,255,0.025)' }} /> : null}
    </Cam>
  );
};
// 9:16: one crop centred near x 0.48 holds his 429 and her knock (CD's framing for the stills)
const cx2C = () => ((L2.crop916_centre_x as number) ?? 0.48);

export const S2_2C: ShotDef = HAVE_2C ? { stage: Stage2CK, cx916: cx2C }
  : HAVE_S7 ? { stage: Stage7Step, cx916: cxStep } : { stage: Stage, cx916: () => 0.53 };
void Stage7; void keys;

