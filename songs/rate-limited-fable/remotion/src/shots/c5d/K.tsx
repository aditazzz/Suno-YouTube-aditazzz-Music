// rl5_d2 cut 5: rl5_b's K plate (him behind the shut glass) + 4G variant, with his visor (CUT5_PLAN §2b, workers/rl5_b/PATCH.md).
// B's visor passes are whole frames (same render, only the head region differs): swap whole frames.
//  Protocol (B / §2b): eyes -> digits = `closed` 3 frames, then the digit state; digits light one per sung word (4, 42, 429, a 2-frame
//  flicker on each new digit); digits -> eyes = `dark` 3 frames, then `sorry`/`eyes`; eyes <-> sorry = `closed` 3 frames.
//  Digit cues (vocal onsets, build/words.json + vocals16.wav): 2B four 720 / two 730 / nine 740; 4G four 1918 (sung in 4F) / two 1927 /
//  nine 1939; 5B four 2390 / two 2400 / nine 2408 (words.json misses them; onsets ~2391 / ~2402, nine from shots.json).
import React from 'react';
import { V8 } from '../../v8';   // rl8_fix2: v8 flag
import { AbsoluteFill, Img, Sequence, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { plateShot, PlateSpec, CamKey } from './plate';
import { GlassChat, glassCues } from '../c5/Glass';
import { Grain2 } from '../../blocks/real/Scene';
import { VisorSeg, VISOR_ROWS } from '../c7/kit/seg';
import { SignFace } from '../c7/kit/logo';
import { has } from '../c7/kit/trans';
import { VisorSweep } from '../c7/kit/sets';
import { Glow, visorK } from '../c7/kit/life';
// rl7_ra (PLAN7 §0.3 idle life): his visor glass alive (a reflection sweep + a faint pulse) and his chest light breathing, on every
// K-family shot (stage px of each plate; K chest light measured on 2B, 4G visor from its layout eyes)
const KLife: React.FC<{ dir: string; abs: number }> = ({ dir, abs }) => (dir === 'K' ? (
  <><VisorSweep abs={abs} x={1316} y={669} w={430} h={200} /><Glow x={1377} y={1098} rx={60} color="rgba(120,255,220,0.9)" op={0.25 * visorK(abs)} /></>
) : dir === '4G' ? <VisorSweep abs={abs} x={1205} y={431} w={450} h={210} seed={3} /> : null);

type VTrack = [number, string][];   // [shot-local frame the state is fully on, state]
const isDig = (s: string) => /^\d+$/.test(s);
/** the visor state at local frame f (B's blink grammar inserted before each cue) */
export const visorState = (f: number, tr: VTrack): string => {
  let i = 0; while (i + 1 < tr.length && f >= tr[i + 1][0] - 3) i++;
  const [t, cur] = tr[i]; const prev = i > 0 ? tr[i - 1][1] : cur;
  if (i === 0 || f >= t) {
    // a digit light-up flickers: on (t), previous (t+1), on (t+2..)
    if (i > 0 && f === t + 1 && isDig(prev) && isDig(cur) && cur.startsWith(prev)) return prev;
    return cur;
  }
  // the 3 frames before the cue
  if (isDig(prev) && isDig(cur)) return prev;            // light-ups need no blink
  if (isDig(prev)) return 'dark';                        // digits -> eyes
  return 'closed';                                       // eyes -> digits, eyes <-> sorry
};
export type { VTrack };
// rl7_ra (her H7.8 / H7.18): digit states draw the visor's `dark` plate + the seven-segment alarm-clock face in code (c7/kit/seg.tsx),
// one face for every number he shows. visorDigits = that overlay (kShot adds it to every K-family shot).
// rl7_ra: P1's re-render of K / 4G (her H7.1 logo + lightbox x1.6, H7.7 gauge raised, K9 shelf requests) when it lands: one full plate
// (eyes neutral) + the visor state as a head-region crop at layout.head_region (c7/<dir>/regions/<state>.jpg), drawn by VisorRegion.
// rl7_fix3d's K (her H7.19/21/22: P1's K + desk glass + chain) supersedes P1's: full plates per state, like c5/K (c7/fix3d/K/plate_<state>.jpg)
export const FIXK = (dir: string) => dir === 'K' && has('c7/fix3d/K/plate_dark.jpg');
const P1K = (dir: string) => has(`c7/${dir}/plate.jpg`) && has(`c7/${dir}/regions/dark.jpg`);
/** the new-logo K/4G plates are in (P1's or fix3d's): no 2D sign patch, messages below the bigger lightbox */
export const NEWK = (dir: string) => FIXK(dir) || P1K(dir);
/** the 2.5D pack that matches the K plate in use (my re-slice of P1's K; none yet for fix3d's) */
export const KPACK = (dir: string) => (FIXK(dir) ? (has(`c7/relogo/${dir}/fix3d_pack/pack.json`) ? `c7/relogo/${dir}/fix3d_pack` : undefined)
  : P1K(dir) && has(`c7/relogo/${dir}/plate_pack/pack.json`) ? `c7/relogo/${dir}/plate_pack` : undefined);   // fix3d's: P1's depth (same camera) on fix3d's eyes plate
const HEAD_REGION: Record<string, number[]> = { K: [1402, 558, 2542, 1446], '4G': [1196, 174, 2410, 1108] };
export const visorSrc = (dir: string, tr: VTrack) => (f: number) => {
  const st = visorState(f, tr);
  if (FIXK(dir)) return `c7/fix3d/${dir}/plate_${isDig(st) ? 'dark' : st}.jpg`;
  if (P1K(dir)) return `c7/${dir}/plate.jpg`;
  return `c5/${dir}/plate_${isDig(st) ? 'dark' : st}.jpg`;
};
export const VisorRegion: React.FC<{ dir: string; tr: VTrack; f: number }> = ({ dir, tr, f }) => {
  if (!P1K(dir) && !FIXK(dir)) return null;
  const st = visorState(f, tr); const r = HEAD_REGION[dir]; const k = 1 / 1.5;
  const dirp = FIXK(dir) ? `c7/relogo/${dir}/fix3d_regions` : `c7/${dir}/regions`;   // fix3d's states cropped at the same head region
  return <Img src={staticFile(`${dirp}/${isDig(st) ? 'dark' : st}.jpg`)} style={{ position: 'absolute', left: r[0] * k, top: r[1] * k, width: (r[2] - r[0]) * k, height: (r[3] - r[1]) * k }} />;
};
export const visorDigits = (dir: string, tr: VTrack): React.FC<{ f: number; shot: ShotProps['shot'] }> => ({ f }) => {
  const st = visorState(f, tr); const row = VISOR_ROWS[dir];
  return isDig(st) && row ? <VisorSeg text={st} quad={row.quad} color={row.color} /> : null;
};

/** K-family shot: plate with visor track, one move, grain, optional glass messages (stage px, ride the move) */
const kShot = (dir: 'K' | '4G', tr: VTrack, cam: [CamKey, CamKey], o: Partial<PlateSpec> = {}): ShotDef => {
  const D = visorDigits(dir, tr), O = o.over;
  // rl7_ra (her H7.1): the new ShipIt logo on the lobby sign's face (c7/kit/logo.tsx)
  const over: PlateSpec['over'] = ({ f, shot }) => (
    <><VisorRegion dir={dir} tr={tr} f={f} />{NEWK(dir) ? null : <SignFace dir={dir} />}{O ? <O f={f} shot={shot} /> : null}<D f={f} shot={shot} /><KLife dir={dir} abs={shot.from + f} /></>);
  const base = plateShot({ src: visorSrc(dir, tr), cam, ...o, over });
  return {
    ...base,
    stage: (props) => {
      const S = base.stage;
      return <AbsoluteFill><S {...props} /><GrainLayer /></AbsoluteFill>;
    },
  };
};
const GrainLayer: React.FC = () => { const f = useCurrentFrame(); return <Grain2 f={f} />; };

// K plate on the stage (3840x2160 -> 2560x1440, /1.5): his head (1296, 864), eyes y 669, him x 984-1611; glass x 0-2306.
const HEAD = { cx: 1296, cy: 700 };

// 2B (704-774): close on him through the glass, hands on the counter; 4-2-9 on the sung digits, then sorry eyes. One slow push.
export const C5_2B = kShot('K', [[0, 'eyes'], [16, '4'], [26, '42'], [36, '429'], [58, 'sorry']],
  [{ ...HEAD, s: 1.30 }, { ...HEAD, cy: 690, s: 1.345 }]);

// 1A teaser beat 2 (frames 24-41, rl5_d3): his visor close, eyes blink to 429 (plan row 1A). 18 frames: eyes, closed 3 f, 429 at 9.
// rl8_fix2 (Nov 20): V8 only (off = the 05:03 film): close-ups reframed (a touch wider + up-left) so Claude's whole SHIP IT! wall (cursor tab + word) clears the frame edges; the plate is unchanged, so the approved wides 2G/5H stay identical
export const C5_TZ_K = kShot('K', [[0, 'eyes'], [9, '429']], V8 ? [{ cx: 1240, cy: 690, s: 1.12 }, { cx: 1222, cy: 676, s: 1.15 }] : [{ ...HEAD, s: 1.30 }, { ...HEAD, cy: 695, s: 1.36 }]);

// 2G (1121-1190): K plate, him behind the glass, her message on the glass, read. Push slower than 2F.
// rl7_ra: with P1's x1.6 lightbox (her H7.13) the messages sit below it, never over SHIP IT!
export const Glass2G: React.FC<{ f: number; shot: ShotProps['shot'] }> = ({ f, shot }) => (
  <GlassChat f={f} {...glassCues('2G', shot.from)} right={940} top={NEWK('K') ? 460 : 300} size={92} />);
export const C5_2G = kShot('K', [[0, 'eyes']], [{ cx: 1280, cy: 720, s: 1.0 }, { cx: 1260, cy: 720, s: 1.025 }], { over: Glass2G });

// 5H (2719-2858): her three messages land on 2719/2737/2754, receipt 2789 holds 2.3 s. One slow push.
export const Glass5H: React.FC<{ f: number; shot: ShotProps['shot'] }> = ({ f, shot }) => (
  // rl7_final (judge nit B26: "Quick question." cut by the left frame edge on the push): bubbles 9% smaller, right edge +20 px (clear of his head)
  <GlassChat f={f} {...glassCues('5H', shot.from)} right={960} top={NEWK('K') ? 450 : 210} size={84} />);
export const C5_5H = kShot('K', [[0, 'eyes']], [{ cx: 1280, cy: 720, s: 1.0 }, { cx: 1250, cy: 715, s: 1.045 }], { over: Glass5H });

// 8F (4108-4177): 429 visor, then eyes. Single push.
export const C5_8F = kShot('K', [[0, '429'], [40, 'eyes']], [{ ...HEAD, cy: 660, s: 1.18 }, { ...HEAD, cy: 650, s: 1.24 }]);   // rl7_fixb (rl7_fix3d note 09:47, her H7.28): cy 700/695 -> 660/650 brings the latched door chain into frame

// 5B first half (2372-2441): to her, 4-2-9 ("nine" 2408). The drift starts here and continues on B's 5B plate (second half).
// Until B's 5B plate lands this covers the whole shot (one drift); then b = 68 + leave and seq() into the 5B plate at 69.
export const C5_5B1 = kShot('K', [[0, 'eyes'], [18, '4'], [28, '42'], [36, '429']],
  [{ cx: 1296, cy: 720, s: 1.12 }, { cx: 1340, cy: 770, s: 1.09 }]);

// rl5_d5: the same first half, leaving moving at 68 into B's 5B plate (c5d/b5.tsx C5_5B)
export const C5_5B1_LEAVE = kShot('K', [[0, 'eyes'], [18, '4'], [28, '42'], [36, '429']],
  V8 ? [{ cx: 1250, cy: 680, s: 1.06 }, { cx: 1285, cy: 705, s: 1.04 }] : [{ cx: 1296, cy: 720, s: 1.12 }, { cx: 1340, cy: 770, s: 1.09 }], { b: 68, leave: true });   // rl8_fix2: V8 reframe (see C5_TZ_K)

// 4G (1920-1990): 4F's push continues through the glass onto him, fully framed; lands by 1955 (local 35), holds.
// The 4 was sung at 1918 (end of 4F): the cut opens on the blink, the 4 lights at 3, 2 at 7, 9 at 19.
// 4G plate /1.5: him x 887-1552, head (1216, 635). Plan: no clock in frame (her N20): the set's wall clock right of his head
// (plate x 2430-2770) needs rl5_b's clock-free patch (requested); it lands as a layer here.
// rl5_d5: rl5_b_g landed 18:35: noclock_patch.png (542x536 RGB) at layout noclock_region [2328, 134, 2870, 670] (3840 px; /1.5 on the
// stage), over every visor state (clear of head_region), outer 24 plate px (16 stage px) feathered.
const NC = [2328, 134, 2870, 670].map((v) => v / 1.5);
const FE = 16, MX = `linear-gradient(90deg, transparent 0, #000 ${FE}px, #000 calc(100% - ${FE}px), transparent 100%)`,
  MY = `linear-gradient(180deg, transparent 0, #000 ${FE}px, #000 calc(100% - ${FE}px), transparent 100%)`;
const NoClock4G: React.FC<{ f: number; shot: ShotProps['shot'] }> = () => (
  <Img src={staticFile('c5/4G/noclock_patch.png')} style={{ position: 'absolute', left: NC[0], top: NC[1], width: NC[2] - NC[0], height: NC[3] - NC[1],
    WebkitMaskImage: `${MX}, ${MY}`, maskImage: `${MX}, ${MY}`, WebkitMaskComposite: 'source-in', maskComposite: 'intersect' }} />);
export const C5_4G = kShot('4G', [[0, 'eyes'], [3, '4'], [7, '42'], [19, '429']],
  [{ cx: 1250, cy: 720, s: 1.0 }, { cx: 1225, cy: 715, s: 1.05 }], { a: 0, b: 35, arrive: true, over: NoClock4G });

// a cut-5 shot made of two new defs: A for [0, n), B after (B sees its own shot object: from + n, dur - n, and local frames from 0)
export const seq = (A: ShotDef, n: number, B: ShotDef): ShotDef => ({
  stage: (props) => {
    const SA = A.stage, SB = B.stage; const sh = { ...props.shot, from: props.shot.from + n, dur: props.shot.dur - n };
    return (<>
      <Sequence from={0} durationInFrames={n} layout="none"><SA {...props} /></Sequence>
      <Sequence from={n} layout="none"><SB {...props} shot={sh} /></Sequence>
    </>);
  },
  cx916: () => 0.5,
});
