// 1I, politely, no (first30.md + HEROES.md): H2 DOOR frames 565-603 then a hold, the three locks on the three sung
// "Rate"s (617 / 621 / 626) with a 1-frame camera tick each. Until H2 lands, the fallback: the door is open (no glass
// between us and him) and on "no" the glass leaf swings shut toward us about its hinge (6 frames, shutter blur, a
// 2-frame settle, a light sweep across the glass); then the locks. The bow on "politely" needs the D1 bow stills (S7).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inCubic, inOutSine, lerp, outCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { ScreenInsert } from '../../blocks/ScreenInsert';
import { cueFrame, frameOf, wordAt } from '../../timing';
import { Cam, HeroClip, PlateImg, heroReady } from './kit';
import { Chain, DOOR, Deadbolt, FloorBolt, GlassSheen, leafQuad } from './door';
import { GlassSheen7, HAVE_S7, Leaf7, Locks7, OpenLeafErase, Plate7, swingAng } from './door7';
import { MBlur, ez } from './kit';

const Leaf: React.FC<{ k: number; sheen: number }> = ({ k, sheen }) => (
  <ScreenInsert corners={leafQuad(k)} w={1388} h={1653}>
    <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(120,145,170,0.20), rgba(90,110,135,0.26))',
      boxShadow: 'inset 0 0 0 26px #1b1d22, inset 0 0 0 30px rgba(150,140,120,0.55), inset 0 0 0 34px rgba(10,10,12,0.6)' }} />
    <div style={{ position: 'absolute', right: 70, top: 760, width: 26, height: 150, borderRadius: 8, background: 'linear-gradient(90deg,#8a6526,#e2bf74,#8a6526)' }} />
    <GlassSheen pos={sheen} k={1.6} />
  </ScreenInsert>
);

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const no = frameOf(wordAt('no', shot.s) ?? 19.92) - shot.from;          // the leaf lands on "no"
  const L = [cueFrame(shot, 'deadbolt') ?? 52, cueFrame(shot, 'chain') ?? 56, cueFrame(shot, 'floor') ?? 61];
  const swingA = no - 6;
  const leafK = (t: number) => {
    if (t < swingA) return 0;
    if (t < no) return inCubic(clamp((t - swingA) / 6));          // accelerates shut
    const d = t - no; return d < 1 ? 0.985 : d < 2 ? 1.004 : 1;     // 2-frame settle
  };
  const tick = L.reduce((a, at) => a + (f === at ? 1 : 0), 0);
  const s = lerp(1.02, 1.05, clamp(f / (shot.dur - 1))) * (1 + 0.006 * tick) * (f >= no && f < no + 2 ? 1.004 : 1);
  const sweep = lerp(-0.2, 1.2, outCubic(clamp((f - no) / 10)));
  const lk = (at: number) => clamp((f - at) / 3);
  const fallback = (
    <>
      <PlateImg src={DOOR.plate} filter={f < no ? 'brightness(1.04) contrast(1.03)' : undefined} />
      {f >= swingA ? <AbsoluteFill style={{ clipPath: DOOR.frontClip }}>{(
        f < no + 1 ? <>{[-0.3, -0.1, 0.1, 0.3].map((dt, i) => <AbsoluteFill key={i} style={{ opacity: 1 / (i + 1) }}><Leaf k={leafK(f + dt)} sheen={0.3} /></AbsoluteFill>)}</>
          : <Leaf k={leafK(f)} sheen={sweep} />
      )}</AbsoluteFill> : null}
    </>
  );
  return (
    <Cam cx={1290} cy={700} s={s} dy={tick * 3}>
      <HeroClip id="H2" g={g} fallback={fallback} />
      {heroReady('H2') || f < no ? null : <AbsoluteFill style={{ clipPath: DOOR.frontClip, opacity: clamp((f - no + 1) / 2) }}><Deadbolt k={lk(L[0])} /><Chain k={lk(L[1])} /><FloorBolt k={lk(L[2])} /></AbsoluteFill>}
    </Cam>
  );
};

// v2 (rl_first30_v2): the real S7 D1 set. He bows on "politely" (upright -> smear -> bow -> smear -> upright), the glass
// leaf swings shut toward us and lands on "no" (6 frames, accelerating, shutter blur), then the camera pushes 1.03 -> 1.45
// toward the latch side so the three locks read at phone size: knob turn (deadbolt), chain across, floor bolt down, on the
// three sung "Rate"s, each with a 1-frame camera tick and a short lift on the lock that turned. No paddle in his hand here:
// D1 has it parked down out of sight, so the 429 reveal stays in 2B.
const LAND_PUSH = 14;
const Stage7: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const no = frameOf(wordAt('no', shot.s) ?? 19.92) - shot.from;
  const L = [cueFrame(shot, 'deadbolt') ?? 52, cueFrame(shot, 'chain') ?? 56, cueFrame(shot, 'floor') ?? 61];
  const a = no - 6;
  const pose = f < 1 ? 'D1open_upright' : f < 3 ? 'D1open_smear' : f < 15 ? 'D1open_bow' : f < 17 ? 'D1open_smear' : 'D1open_upright';
  const lockK = clamp((f - L[0]) / 2) + clamp((f - L[1]) / 2) + clamp((f - L[2]) / 2);
  const last = [...L].reverse().find((t) => f >= t); const glint = last === undefined ? 0 : Math.exp(-(f - last) / 2.2);
  const tick = L.reduce((acc, at) => acc + (f === at ? 1 : 0), 0) + (f === no ? 1 : 0);
  const kp = ez(f, no, no + LAND_PUSH, outCubic);
  // after the push lands the camera keeps creeping (1.45 -> 1.50 and a small pan) so the frames between the locks never freeze
  const post = clamp((f - no - LAND_PUSH) / Math.max(1, shot.dur - 1 - no - LAND_PUSH));
  const s = lerp(lerp(1.03, 1.05, clamp(f / Math.max(1, no))), 1.45, kp) * (1 + 0.035 * post) * (1 + 0.006 * tick);
  const cx = lerp(1280, 1560, kp) + 40 * post, cy = lerp(720, 900, kp) + 12 * post;
  const sweep = lerp(-0.2, 1.2, outCubic(clamp((f - no) / 10)));
  return (
    <Cam cx={cx} cy={cy} s={s} dy={tick * 3}>
      {f < no ? (
        <>
          <Plate7 name={pose} />
          {f >= a ? <><OpenLeafErase /><MBlur n={5} shutter={0.6} render={(dt) => <Leaf7 ang={swingAng(f + dt, a)} />} /></> : null}
        </>
      ) : (
        <>
          <Plate7 name="D1" />
          <Locks7 k={lockK} glint={glint} />
          <GlassSheen7 pos={sweep} k={1.4 * (1 - clamp((f - no - 10) / 8))} />
        </>
      )}
    </Cam>
  );
};

// ---- v3 (rl_first30_v3, CD V3 order 4: the locks become three macro close-ups on "Rate, rate, rate") ----
// 600-616 keeps the door landing and push (Stage7). Then hard cuts: knob ECU (the lock turns 1 frame after the cut),
// chain ECU (slides across, a smear frame), floor-bolt ECU (drops), each with a 1-frame tick and a slow push toward the
// lock; then the cut to 2A. Stills: build/stills/S7_locks (rl_stills_2c_locks), copied by build/first30/tools/prep_v3.py.
import assets from './assets.json';
import { Img, staticFile } from 'remotion';
import { outBack } from './v3ease';
const A1 = assets as any;
const LK = (A1.S7_locks ?? {}) as Record<string, { file: string; lock_px?: number[]; size?: number[] }>;
export const HAVE_ECU = ['knob_open', 'knob_locked', 'chain_open', 'chain_locked', 'floor_open', 'floor_locked'].every((k) => !!LK[k]);
const ECU: React.FC<{ name: string; f: number; a: number; n: number; tick: boolean }> = ({ name, f, a, n, tick }) => {
  const e = LK[name]; const sz = [4320, 2430]; const K = 2560 / sz[0];     // lock_px is in the layout's 4320 px (previews are half size)
  // one aim per lock (its LOCKED box), so the open -> locked swap never moves the camera
  const aim = LK[name.split('_')[0] + '_locked']?.lock_px ?? e.lock_px;
  const px = (aim ?? [sz[0] / 2, sz[1] / 2]).map((v) => v * K);
  const u = clamp((f - a) / Math.max(1, n - 1));
  const s = lerp(1.0, 1.05, u) * (tick ? 1.006 : 1);
  return (
    <Cam cx={lerp(1280, px[0], 0.5 * u)} cy={lerp(720, px[1], 0.5 * u)} s={s} dy={tick ? 3 : 0}>
      <Img src={staticFile(e.file)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />
    </Cam>
  );
};
const StageV3: React.FC<ShotProps> = (props) => {
  const { shot } = props; const f = useCurrentFrame();
  const L = [cueFrame(shot, 'deadbolt') ?? 52, cueFrame(shot, 'chain') ?? 56, cueFrame(shot, 'floor') ?? 61];
  if (f < L[0]) return <Stage7 {...props} />;
  if (f < L[1]) return <ECU name={f < L[0] + 1 ? 'knob_open' : 'knob_locked'} f={f} a={L[0]} n={L[1] - L[0]} tick={f === L[0] + 1} />;
  if (f < L[2]) {
    const nm = f < L[1] + 1 ? 'chain_open' : f < L[1] + 2 && LK.chain_smear ? 'chain_smear' : 'chain_locked';
    return <ECU name={nm} f={f} a={L[1]} n={L[2] - L[1]} tick={f === L[1] + 1} />;
  }
  return <ECU name={f < L[2] + 1 ? 'floor_open' : 'floor_locked'} f={f} a={L[2]} n={shot.dur - L[2]} tick={f === L[2] + 1} />;
};

// FALLBACK (macros not in): after the landing push the camera keeps pushing 1.45 -> 2.1 on the latch, a step on each "Rate"
// (1.70 / 1.90 / 2.10, 3 frames, outBack) aimed at the lock that turns (deadbolt mid, chain top, floor bolt low), the
// existing lock layers doing the turning.
const LOCK_AIM = [[2861, 1336], [3000, 1040], [2907, 2140]].map(([x, y]) => [x * 2560 / 4320, y * 2560 / 4320]);
const StagePush: React.FC<ShotProps> = (props) => {
  const { shot } = props; const f = useCurrentFrame();
  const no = frameOf(wordAt('no', shot.s) ?? 19.92) - shot.from;
  const L = [cueFrame(shot, 'deadbolt') ?? 52, cueFrame(shot, 'chain') ?? 56, cueFrame(shot, 'floor') ?? 61];
  if (f < L[0]) return <Stage7 {...props} />;
  // where Stage7 is at L[0] (same formulas), so the first step starts from the exact frame before
  const post0 = clamp((L[0] - no - LAND_PUSH) / Math.max(1, shot.dur - 1 - no - LAND_PUSH));
  const s0 = 1.45 * (1 + 0.035 * post0), c0 = [1560 + 40 * post0, 900 + 12 * post0];
  const lv = [s0, 1.7, 1.9, 2.1]; const aims = [c0, ...LOCK_AIM];
  let s = s0, cx = c0[0], cy = c0[1];
  L.forEach((at, i) => { if (f >= at) { const k = outBack(clamp((f - at) / 3), 1.2); s = lerp(lv[i], lv[i + 1], k); cx = lerp(aims[i][0], aims[i + 1][0], k); cy = lerp(aims[i][1], aims[i + 1][1], k); } });
  s *= (1 + 0.0035 * (f - L[0])) * (1 + 0.01 * clamp((f - L[2]) / 8));   // a creep under the steps, so no frame between them freezes
  const lockK = clamp((f - L[0]) / 2) + clamp((f - L[1]) / 2) + clamp((f - L[2]) / 2);
  const tick = L.some((at) => f === at);
  return (
    <Cam cx={cx} cy={cy} s={s * (tick ? 1.006 : 1)} dy={tick ? 3 : 0}>
      <Plate7 name="D1" />
      <Locks7 k={lockK} />
    </Cam>
  );
};
const cx1I = (f: number, shot: ShotProps['shot']) => { const n = frameOf(wordAt('no', shot.s) ?? 19.92) - shot.from; return lerp(0.5, 0.58, ez(f, n, n + LAND_PUSH, outCubic)); };
const cx1IPush = (f: number, shot: ShotProps['shot']) => {
  const L0 = cueFrame(shot, 'deadbolt') ?? 52;
  return f < L0 ? cx1I(f, shot) : 0.5;            // the push centres the lock in the stage, so the 9:16 crop sits mid
};
export const S1_1I: ShotDef = HAVE_S7
  ? (HAVE_ECU ? { stage: StageV3, cx916: (f, shot) => (f < (cueFrame(shot, 'deadbolt') ?? 52) ? cx1I(f, shot) : 0.5) }
    : { stage: StagePush, cx916: cx1IPush })
  : { stage: Stage, cx916: () => 0.56 };
