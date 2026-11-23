// Cut 7 sections 10-11 (the turn + HIS verse), blocks B48-B52 (PLAN7 §1; rl7_rb). One camera per block; his verse keeps the camera on
// HIM (K4) with his visor + chest light pulsing with his voice (kit voice(): robot WAV envelope, voiced 5071-5370).
import React from 'react';
import { ShotDef } from '../../types';
import { rig, rigs, pushKeys } from '../kit/rig';
import { Glow, visorK } from '../kit/life';
import { block } from '../kit/blocks';
import { has } from '../kit/trans';
import { B49, P10B, PlaquePatch } from './b49';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { PL, Pl } from '../../s10/_lib';
import { M1Needle, PlateDigit } from '../../s11/_meter';

const L = (pct: number) => Math.log(1 + pct / 100) / 30;
const d = (id: string) => block(id).dur;

// B48 (4836-4975) FLOW: slide along her wall (cut 6's 10A move, kept) under a steady push + drift so it never parks on the screen
const B48: ShotDef = rig({ keys: pushKeys(d('B48'), { cx: 1250, cy: 720, s0: 1.03, pct: 2.6, dx: 60, dy: -8 }) });

// B50 (5148-5217) FLOW, continues B49's move (push-through, one move): crane up from his risen face (ear plate) toward the HOURS AWAKE gauge
// on the lobby wall, then at "never" (5167) through into the meter plate (cut 6's 11B: the dial + GLASSES OF WATER 0 + LAST MEAL TUESDAY),
// labels readable 5168-5217 (1.6 s), his face in frame from ~5190.
const HisLightsEar: React.FC<{ g: number }> = ({ g }) => { const k = visorK(g);
  return <><Glow x={700} y={760} rx={70} ry={42} color="rgba(150,235,255,0.9)" op={0.32 * k} /><Glow x={640} y={1010} rx={26} color="rgba(90,255,190,0.95)" op={0.65 * k} /></>; };
// the meter plate (cut 6 11B's M1 + needle) drawn at identity under ONE camera: the needle strains against the stop past 24 (a visible
// tremble, his 24 hours and counting), GLASSES OF WATER 0 / LAST MEAL TUESDAY in frame; a steady push that never slows (prev2/3: 22-28% still)
const Meter11B: ShotDef = { stage: () => { const f = useCurrentFrame();
  const v = 24.25 + 0.22 * Math.sin(f * 1.9) * (0.6 + 0.4 * Math.sin(f * 0.37)) + 0.08 * Math.sin(f * 4.3);
  return <AbsoluteFill><Pl src={PL.M1} /><M1Needle v={v} /><PlateDigit f={f} at={1e9} from="0" to="0" /></AbsoluteFill>; } };
const B50: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 712, cy: 598, s: 1.82 }, { f: 19, cx: 712, cy: 520, s: 1.8 }], opt: { v0: { cy: -3, s: L(1) }, v1: { cy: -5, s: L(4) } },
    // rl7_final: continues rl7_room's head turn on its t10 ear pose (locked room through the glass; the new plate has the new plaque)
    plate: { src: has('c7/room/11A/t10.jpg') ? 'c7/room/11A/t10.jpg' : has('c7/11A/p2/st4.jpg') ? 'c7/11A/p2/st4.jpg' : P10B.ear },
    over: ({ abs }) => <>{has('c7/room/11A/t10.jpg') ? null : <PlaquePatch />}<HisLightsEar g={abs} /></>, grain: true },
  // M1 is the meter WITH HIM in the foreground (his eyes left, chest light bottom left) and a shelf of six untouched glasses of water under
// GLASSES OF WATER 0: the crane rises from the glasses + labels and pulls out to reveal his face beside the HOURS AWAKE dial as he sings
// "never for me" (K4 / PLAN7 row 50: the camera settles with HIS face in frame); his chest light pulses with his voice
  { at: 20, inner: Meter11B, keys: [{ f: 0, cx: 1720, cy: 940, s: 1.46 }, { f: 24, cx: 1350, cy: 760, s: 1.18 }, { f: d('B50') - 21, cx: 1150, cy: 700, s: 1.1 }],
    opt: { v0: { cy: -6, s: -L(4) }, v1: { cx: -2, cy: -0.6, s: -L(1.2) } },
    over: ({ abs }) => <Glow x={100} y={1351} rx={55} color="rgba(90,255,190,0.95)" op={0.6 * visorK(abs)} /> },
]);
// B51 (5217-5320) FLOW, K4 (his verse: the camera on HIM, not a door knob): rl7_p2's 11C lobby plates (same camera as the door plate, 1.5x
// copy for the close framing): him behind the glass, the HOURS AWAKE gauge beside him; after "Close the" (5232) the lobby lights come down on
// him (lit -> dim cross-fade over 12 f; his visor + chest light stay lit and pulse with his voice), the camera easing down toward the mail
// slot -> push-through at 5269 into cut 6's 11D (his hands, the glass on the brass tray). Without P2's plates: cut 6's knob + door.
const P11C = { lit: 'c7/11C/p2/D1_lit_6480.jpg', dim: 'c7/11C/p2/D1_dim_6480.jpg' };
const HAS11C = has(P11C.lit) && has(P11C.dim);
const DIM = [5230, 5242];
const Lobby11C: ShotDef = { stage: ({ shot }: any) => { const f = useCurrentFrame(); const g = shot.from + f;
  const k = Math.min(1, Math.max(0, (g - DIM[0]) / (DIM[1] - DIM[0]))); const e = k * k * (3 - 2 * k);
  const full = { position: 'absolute' as const, left: 0, top: 0, width: 2560, height: 1440 };
  const kk = visorK(g);
  return <AbsoluteFill>
    <Img src={staticFile(P11C.lit)} style={full} />
    {e > 0.002 ? <Img src={staticFile(P11C.dim)} style={{ ...full, opacity: e }} /> : null}
    <Glow x={1312} y={1024} rx={30} color="rgba(90,255,190,0.95)" op={0.55 * kk} />
    <Glow x={1296} y={762} rx={120} ry={46} color="rgba(150,235,255,0.9)" op={0.16 * kk} />
  </AbsoluteFill>; } };
const B51: ShotDef = HAS11C ? rigs([
  { at: 0, inner: Lobby11C, keys: [{ f: 0, cx: 1325, cy: 730, s: 1.56 }, { f: 30, cx: 1318, cy: 770, s: 1.64 }, { f: 51, cx: 1335, cy: 880, s: 1.76 }],
    opt: { v1: { cy: 4, s: L(4) } }, grain: true },
  { at: 52, keys: [{ f: 0, cx: 1280, cy: 650, s: 1.04 }, { f: d('B51') - 53, cx: 1290, cy: 740, s: 1.15 }], opt: { v0: { cy: 2, s: L(5) }, v1: { s: L(3) } } },
]) : rigs([
  { at: 0, keys: [{ f: 0, cx: 1240, cy: 700, s: 1.04 }, { f: 51, cx: 1280, cy: 790, s: 1.16 }], opt: { v1: { cy: 2.4, s: L(5) } } },
  { at: 52, keys: [{ f: 0, cx: 1280, cy: 650, s: 1.04 }, { f: d('B51') - 53, cx: 1290, cy: 740, s: 1.15 }], opt: { v0: { cy: 2, s: L(5) }, v1: { s: L(3) } } },
]);
// B52 (5320-5390) FLOW: his hand flat on the glass, slow push from her side (cut 6's 11E side-on palms); the camera keeps moving to the cut
const B52: ShotDef = rig({ keys: pushKeys(d('B52'), { cx: 1270, cy: 715, s0: 1.03, pct: 3, dx: -30, dy: -12 }) });

export const B10: Record<string, ShotDef> = { B48, B49, B50, B51, B52 };
