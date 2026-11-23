// rl5_d5 cut 5: rl5_a2's b chain (landed 18:54; workers/rl5_a2/PATCH.md), looked at on workers/rl5_d5/a2b.jpg. All plates 2880 x 1620.
//  4E (1712-1851): rl5_c's phone part (Phone4E, local 0-52), then a cut to her face through the glass: begging A -> on "begged" (1816,
//     local 104) begging B with Cooper's face beside hers; one slow push on her to the end (plan row 4E). No robot.
//  5D (2511-2580): knelt behind parcel three (CEO, SLOPCORP / SHIPS AT 6:00), palms on its taped top, deadpan; Cooper by the pile. Slow push.
//  9E2 (4662-4732): warrior 2 among the guests, the vacuum at her ankle, Cooper dazed on the sofa; rl5_c's notification on top. Slow push
//     through the party toward the door (left).
//  9G (4784-4836): arms folded; the neon lights one "Cool" per sung "cool" (4801 / 4810 / 4818). Before the first: 9E2's "Not Mad" line
//     (same camera; only the sign box, feathered: 9E2's sign area matches 9G's but for the words), then A2's Cool / Cool Cool Regions, then
//     9G.jpg (Cool Cool Cool). Slow eased creep.
import { TubeNeon } from '../c7/kit/sets';
import { ROOM_5D } from './plates';   // rl7_final: the locked-room 5D has sign A baked (no live neon)
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { plateShot } from './plate';
import { seq } from './K';
import { Phone4E, P4E } from '../c5/S4E';
import { Grain2 } from '../../blocks/real/Scene';
import { VacuumNotif, NOTIF } from '../c5/Notif';

const G: React.FC = () => { const f = useCurrentFrame(); return <Grain2 f={f} />; };
const withGrain = (d: ShotDef): ShotDef => ({ ...d, stage: (p) => { const S = d.stage; return <AbsoluteFill><S {...p} /><G /></AbsoluteFill>; } });

const BEG = 1816 - 1712;   // local frame of "begged"
const face4E = withGrain(plateShot({ src: (f) => (f < BEG - P4E.END ? 'c5/4E/beg_A.jpg' : 'c5/4E/beg_B.jpg'),
  cam: [{ cx: 1240, cy: 730, s: 1.02 }, { cx: 1200, cy: 718, s: 1.06 }] }));
const Ph: React.FC<ShotProps> = () => { const f = useCurrentFrame(); return <Phone4E f={f} />; };
export const C5_4E_FULL: ShotDef = seq({ stage: Ph, cx916: () => 0.5 }, P4E.END, face4E);

// rl7_ra: the room neon in the tube family (director 10:15), live, where the script sign hung (painted out of the plate)
export const C5_5D = withGrain(plateShot({ src: 'c5/5D/5D.jpg', cam: [{ cx: 1280, cy: 720, s: 1.0 }, { cx: 1300, cy: 715, s: 1.04 }],
  over: ({ f, shot }) => ROOM_5D ? null : <TubeNeon abs={shot.from + f} src="c7/neon/live_love_be_famous.png" x={1780} y={10} w={500} aspect={4096 / 2369} colors={['rgba(255,95,168,0.8)', 'rgba(69,227,255,0.8)']} seed={51} /> }));

const Notif: React.FC<{ f: number; shot: ShotProps['shot'] }> = ({ f }) => <VacuumNotif f={f} at={NOTIF.IN - 4662} />;
const p9E2 = withGrain(plateShot({ src: 'c7/9E2/9E2.jpg', cam: [{ cx: 1280, cy: 720, s: 1.0 }, { cx: 1190, cy: 730, s: 1.05 }] }));
export const C5_9E2: ShotDef = { ...p9E2, screen: ({ shot }) => { const f = useCurrentFrame(); return <Notif f={f} shot={shot} />; } };

// 9G sign: Not Mad (9E2's sign box) -> Cool (17) -> Cool Cool (26) -> Cool Cool Cool (34). Box in 2880 px -> stage x 2560/2880.
const KS = 2560 / 2880, BOX = [1230, 200, 1960, 540].map((v) => v * KS);
const FE = 18, MX = `linear-gradient(90deg, transparent 0, #000 ${FE}px, #000 calc(100% - ${FE}px), transparent 100%)`,
  MY = `linear-gradient(180deg, transparent 0, #000 ${FE}px, #000 calc(100% - ${FE}px), transparent 100%)`;
const NotMad: React.FC<{ f: number; shot: ShotProps['shot'] }> = ({ f }) => (f >= 17 ? null : (
  <div style={{ position: 'absolute', left: BOX[0], top: BOX[1], width: BOX[2] - BOX[0], height: BOX[3] - BOX[1], overflow: 'hidden',
    WebkitMaskImage: `${MX}, ${MY}`, maskImage: `${MX}, ${MY}`, WebkitMaskComposite: 'source-in', maskComposite: 'intersect' }}>
    <Img src={staticFile('c7/fix713/c9/9E2.jpg')} style={{ position: 'absolute', left: -BOX[0], top: -BOX[1], width: 2560, height: 1440 }} />
  </div>));
export const C5_9G = withGrain(plateShot({ src: (f) => (f < 17 ? 'c7/9G/9G_sign_Not_Mad.jpg' : f < 26 ? 'c7/9G/9G_sign_Cool.jpg' : f < 34 ? 'c7/9G/9G_sign_Cool_Cool.jpg' : 'c7/9G/9G.jpg'),   // rl7_master: hero2 PATCH s2 (whole plates, no patch)
  cam: [{ cx: 1280, cy: 720, s: 1.0 }, { cx: 1290, cy: 712, s: 1.03 }] }));
void NotMad;

// rl5_d5: rl5_a2's c chain (landed 19:02), looked at on workers/rl5_d5/a2c.jpg.
//  11E (5320-5390): side-on at the glass, his palm (on his step parcel) and hers meeting on it, both profiles. Slow push toward the palms;
//     no beat pulse (the drum stops). A2's new angle has no BACK AT 6:00 sign in frame (cut 4e's hung sign doesn't fit a side-on glass).
export const C5_11E = withGrain(plateShot({ src: 'c5/11E/11E.jpg', cam: [{ cx: 1280, cy: 720, s: 1.0 }, { cx: 1235, cy: 695, s: 1.06 }] }));
//  13B (6185-6254): cut 4e's structure: door open, warm light floods in, his bow (13B_open) -> the exterior beat (L5's Ext13B, ShipIt! relit,
//     B's facade via C5PATH) -> she pushes all six through on the hand truck, RETIREMENT on top, Cooper bounding after (13B_push).
import { Ext13B, HAVE_13B_EXT } from '../s13/13B_ext';
import { Cam, hit } from '../first30/kit';
import { beat } from '../l2kit';
const Pl13: React.FC<{ src: string; filter?: string }> = ({ src, filter }) => <Img src={staticFile(src)} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, filter }} />;
const ease = (t: number) => (t <= 0 ? 0 : t >= 1 ? 1 : 0.5 - 0.5 * Math.cos(Math.PI * t));
const S13B: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const b1 = beat(shot, 1, 17), b2 = b1 + 28, XS = 1.5;
  if (f < b1) {
    const k = ease(f / (b1 - 1)); const flood = Math.min(1, f / 8);
    return <Cam cx={1280} cy={720} s={1 + 0.04 * k}><Pl13 src="c5/13B/13B_open.jpg" filter={`brightness(${(0.8 + 0.2 * flood).toFixed(3)})`} /></Cam>;
  }
  if (f < b2 && HAVE_13B_EXT) return <AbsoluteFill><Ext13B f={(f - b1) * XS} dur={(b2 - b1) * XS} g={g} /></AbsoluteFill>;
  const k = ease((f - b2) / (shot.dur - 1 - b2));
  return <Cam cx={1280} cy={lerp13(720, 700, k)} s={(1.03 + 0.07 * k) * (1 + hit(f, b2, 0.012, 10))}><Pl13 src="c5/13B/13B_push.jpg" /></Cam>;
};
const lerp13 = (a: number, b: number, k: number) => a + (b - a) * k;
export const C5_13B: ShotDef = { stage: S13B, cx916: () => 0.5 };
