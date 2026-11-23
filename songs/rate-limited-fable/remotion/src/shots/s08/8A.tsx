// 8A "Rate, rate, rate limited" (fix round 4, rl_l5_street; her cut 3 note: "The car looks like it's floating. Also make the car brighter,
// clearer, absolutely gorgeous looking. Maybe give it a parking ticket something related to rate limited. Like the meter for it has also run out.")
// L5 8A (build/stills/L5_8A, blrl4_street): low 3/4 front from the road at 4:21 a.m. Her GT3 RS grounded (tyres pressed into the wet road,
// measured), lit by the kerb lamp and the lobby, reflected in the wet asphalt; the parking meter on the kerb by her nose with its red EXPIRED
// flag up; an orange citation under the driver's wiper; Cooper (cream, red bow) sniffing the meter post. No cat (it never leaves the building).
//   0..34   the wide. The three "Rate"s: the car's lamps chirp amber (her fob), a small camera kick each.
//   35..    (the downbeat after "limited") hard cut to the punchline, her point of view from the pavement: the meter's screen close,
//           "429 / RETRY AFTER 6:00", the red EXPIRED flag up in its dome, and past it her windshield with the orange ticket under the wiper.
// Her (date dress + LOVE hat) walking in to her mark left of the meter is a separate pass (rollout: see workers/rl_l5_street/PATCH.md);
// until it lands the wide plays with Cooper alone at the meter. Falls back to the cut 3 version if the L5 stills are missing.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutSine, outCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, Grain, flick, flickOut } from '../s07/_lib';
import { PlateImg } from '../first30/kit';
import l5 from '../first30/l5.json';
import B from './cut1b.json';
import HR from './herrig_8a.json';

const L8 = (l5 as any).A8 as undefined | { files: Record<string, string>; her?: { frames: Record<string, string> } };
const HAVE_L5 = !!(L8 && L8.files?.plate_cooper && L8.files?.meter);
export const CUT_METER = 35;                       // shot-local frame of the cut to the meter (grid beat 3)

const StageL5: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const g = shot.from + f; const F = L8!.files;
  const rates = (shot.cues ?? []).map((c) => c.frame - shot.from);          // 0, 9, 17
  if (f >= CUT_METER) {
    // the punchline: hold, a slow 4% push toward the LCD, one small settle on the cut
    const k = inOutSine(clamp((f - CUT_METER) / Math.max(1, shot.dur - 1 - CUT_METER)));
    const set = 1 + 0.012 * Math.exp(-(f - CUT_METER) / 3) * Math.cos((f - CUT_METER) * 0.9);
    return (
      <Cam cx={1280} cy={lerp(760, 800, k)} s={lerp(1.0, 1.04, k) * set}>
        <PlateImg src={`l5/${F.meter}`} />
        <Grain g={g} k={0.035} />
      </Cam>
    );
  }
  const ind = rates.reduce((m, r) => Math.max(m, f >= r && f < r + 8 ? (f < r + 4 ? flick(f, r) : flickOut(f, r + 4)) : 0), 0);
  const kick = 1 + rates.reduce((m, r) => m + (f >= r && f < r + 8 ? 0.010 * Math.exp(-(f - r) / 2.5) : 0), 0);
  const v = fmt === '9x16';
  const k = inOutSine(clamp(f / (CUT_METER - 1)));
  // rl_cut4 (prep FOR DIRECTOR: her mark C is at x 188, small at the left edge): on her "really?" (Rate 3 -> the meter cut) the camera
  // drifts left and pushes in on her and the meter, so she reads at phone size before the insert. 16:9 only.
  const r2 = rates[2] ?? 17, kc = v ? 0 : inOutSine(clamp((f - r2 + 2) / Math.max(1, CUT_METER - r2)));
  const s = kick * (v ? lerp(1.25, 1.30, k) : lerp(1.0, 1.045, outCubic(k)) * lerp(1, 1.3, kc));
  return (
    <Cam cx={v ? 1180 : lerp(lerp(1290, 1270, k), 960, kc)} cy={v ? 760 : lerp(730, 800, kc)} s={s}>
      <PlateImg src={`l5/${F.plate_cooper}`} />
      {F.ind ? <PlateImg src={`l5/${F.ind}`} opacity={ind} /> : null}
      {/* rl_l1_roll C5 (via rl_cut4_prep): her walking home from the date, A < Rate 2 <= B < Rate 3 <= C (RGBA, L5's plate_cooper camera) */}
      {(() => { const ph = f < (rates[1] ?? 9) ? 'A' : f < (rates[2] ?? 17) ? 'B' : 'C';
        return <Img src={staticFile(`l1r/8A/walk_${ph}.png`)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} />; })()}
      <AbsoluteFill style={{ opacity: ind * 0.10, background: 'rgb(255,168,64)', mixBlendMode: 'soft-light' }} />
      <Grain g={g} k={0.035} />
    </Cam>
  );
};

// ---------------------------------------------------------------- the cut 3 version (fallback until the L5 stills are in public/l5)
const A8 = (B as any)['8A'];
const KP = 2560 / 2880;
const WALK = (HR as any).walk as Record<string, number[]>;
const CATD = (HR as any).cat as { region: number[]; box: number[]; src: string };
const rb = (r: number[]) => ({ left: r[0] * KP, top: r[1] * KP, width: (r[2] - r[0]) * KP, height: (r[3] - r[1]) * KP });
const bx = (b: number[]) => ({ left: b[0], top: b[1], width: b[2] - b[0], height: b[3] - b[1] });
/** stage px (2560 wide) of the car's plate, roof and indicator lamps on S23 */
export const CAR = { plate: A8.plate as number[], roof: A8.roof as [number, number] };

const StageCut3: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const rates = (shot.cues ?? []).map((c) => c.frame - shot.from);
  const ind = rates.reduce((m, r) => Math.max(m, f >= r && f < r + 8 ? (f < r + 4 ? flick(f, r) : flickOut(f, r + 4)) : 0), 0);
  const v = fmt === '9x16';
  const kick = 1 + rates.reduce((m, r) => m + (f >= r && f < r + 8 ? 0.012 * Math.exp(-(f - r) / 2.5) : 0), 0);
  const s = kick * (v ? lerp(1.3, 1.36, inOutSine(clamp(f / shot.dur))) : lerp(1.0, 1.06, inOutSine(clamp(f / shot.dur))));
  const sq = 1 + 0.14 * Math.exp(-f / 3.2) * Math.cos(f * 0.95);
  const cb = rb(CATD.region); const ox = (CATD.box[0] + CATD.box[2]) / 2 * KP - cb.left, oy = CATD.box[3] * KP - cb.top;
  const step = f >= (rates[2] ?? 17) ? 'C' : f >= (rates[1] ?? 9) ? 'B' : 'A';
  return (
    <Cam cx={1280} cy={v ? 1000 : 800} s={s}>
      <PlateImg src="cut1/b/s23_plate.jpg" />
      <Img src={staticFile('cut1/b/s23_ind.png')} style={{ position: 'absolute', ...bx(A8.ind_box), opacity: ind }} />
      <AbsoluteFill style={{ opacity: ind * 0.14, background: 'rgb(255,168,64)', mixBlendMode: 'soft-light' }} />
      <Img src={staticFile(CATD.src)} style={{ position: 'absolute', ...cb, transformOrigin: `${ox}px ${oy}px`, transform: `scale(${sq.toFixed(4)}, ${(1 / sq).toFixed(4)})` }} />
      <Img src={staticFile(`fix2/herrig/s23_walk_${step}.png`)} style={{ position: 'absolute', ...rb(WALK[step]) }} />
      <Grain g={g} />
    </Cam>
  );
};
export const S8_8A: ShotDef = HAVE_L5 ? { stage: StageL5, cx916: (f) => (f >= CUT_METER ? 0.5 : 0.46) } : { stage: StageCut3, cx916: () => 0.5 };
