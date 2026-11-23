// Cut 7 sections 1-3, blocks B01-B14 (PLAN7 §1; rl7_ra). Each block is ONE camera over the whole block (kit/rig), drawn over the cut 6
// picture of its frames, so every block moves from its first frame to its last; push-throughs keep their velocity across the
// inner cut; wall dollies replace the CSS door slab. Frames below are block-local unless named abs.
import { ShotDef } from '../../types';
import { V8 } from '../../../v8';   // rl8_fix2: v8 flag
import { rig, rigs, pushKeys, has } from '../kit';
import { block } from '../kit/blocks';
import React from 'react';
import { B11 } from './b11';
import { Room1DLife, VisorSweep, ROOM1D_NOSIGN } from '../kit/sets';
import { SignFace } from '../kit/logo';
import { visorSrc, visorDigits, VTrack, Glass2G, NEWK, KPACK, VisorRegion } from '../../c5d/K';
import { C5_2C_WIDE } from '../../c5d/2C';

const L = (pct: number) => Math.log(1 + pct / 100) / 30;           // log-scale velocity per frame of a pct %/s push
const d = (id: string) => block(id).dur;

// B01 (0-76) PUNCH, the teaser: her at the chained door (0-23) opens TIGHTER on her (FRAMES 1A: his spikes were 35% of the frame,
// her eyes down): s 1.42 on her face, his spikes a soft edge at the right; push 3 %/s. 24-41 his visor close (push 4 %/s + a slight
// arc), 42-58 her deadpan (push 3 %/s), 59-75 the street wide starting the descent (push, leaves moving into B02).
const B01 = rigs([
  // 0-23 on the 2C plate's own rig (P2, P1's depth pack: her / him / room slices): parallax between her and his spikes, the spikes a soft
  // foreground (defocused), her breathing; the camera = cut 6's 2C framing x this block's tighter push, composed
  { at: 0, keys: [{ f: 0, cx: 905, cy: 470, s: 1.56 }, { f: 23, cx: 924, cy: 466, s: 1.605 }], grain: true,
    plate: { src: C5_2C_WIDE, pack: 'c7/apt/2C_P2', focus: 'her', mods: () => ({ him: { blur: 5 } }) } },
  { at: 24, keys: pushKeys(18, { cx: 1280, cy: 700, s0: 1.04, pct: 4, dx: -18, r0: -0.25, r1: 0.15 }) },
  // 42-58 her deadpan, tight (cut 6's K1_dp framing x the push), on its own rig: P1's K1 depth re-sliced on the deadpan plate
  { at: 42, keys: [{ f: 0, cx: 1180, cy: 360, s: 2.04 }, { f: 16, cx: 1191, cy: 358, s: 2.13 }], grain: true,
    plate: { src: 'c7/apt/2C_K1_dp_slop.jpg', pack: 'c7/apt/2C_K1_dp', focus: 'her' } },
  // 59-75: the street, uncropped at the top (the cat peeks down from the frame top 60-96: her face must stay in, PLAN7 row 2)
  { at: 59, keys: [{ f: 0, cx: 1280, cy: 720, s: 1.0 }, { f: 16, cx: 1280, cy: 722, s: 1.008 }] },
]);

// B02 (76-286) FLOW: the one descent (1B crane down the facade, whip at 216, 1C elevator drop onto the door) under one outer move:
// a constant 2 %/s push over 1B, then 1C pushes toward the door and LEAVES at 6 %/s (B03 arrives at the same rate: push-through).
const B02: ShotDef = rig({
  keys: [{ f: 0, cx: 1280, cy: 722, s: 1.008 }, { f: 30, cx: 1280, cy: 724, s: 1.02 }, { f: 139, cx: 1280, cy: 726, s: 1.05 }, { f: d('B02') - 1, cx: 1280, cy: 690, s: 1.08 }],
  opt: { v1: { s: L(6) } },
});
// B03 (286-356) FLOW: the master wide. Arrives on the push-through (6 %/s, slowing), then a slow truck right + push toward the
// threshold; leaves moving into B04.
// Own plate through SliceCam (c6/1D/T1s.jpg; 2.5D when P1's pack lands, P1's W7 re-render swaps in by path) + idle life.
const B03: ShotDef = rig({
  keys: [{ f: 0, cx: 1200, cy: 750, s: 1.04 }, { f: d('B03') - 1, cx: 1300, cy: 735, s: 1.12 }],
  opt: { v0: { s: L(6), cx: 2.0 }, v1: { s: L(3), cx: 1.0 } },
    // always the painted-out plate (made from P1's 1D re-render once it lands: workers/rl7_ra/reland_1d4f.sh), + its re-slice when P1's depth lands
  plate: { src: ROOM1D_NOSIGN, pack: 'c7/apt/1D_T1s' }, grain: true,
  over: ({ abs }) => <Room1DLife abs={abs} avoid={[286, 356]} />,
});
// B04 (356-426) FLOW: arrives moving, settles on the ticket pull (41) by the tally click (beat 4), then the wall dolly (her side ->
// lobby: the camera travels left) out of its last 12 frames into B05.
const B04: ShotDef = rig({
  keys: [{ f: 0, cx: 1240, cy: 700, s: 1.0 }, { f: 46, cx: 1280, cy: 730, s: 1.08 }, { f: d('B04') - 1, cx: 1300, cy: 735, s: 1.1 }],
  opt: { v0: { s: L(5) } },
  dollyOut: { n: 12, dir: -1 },
});
// B05 (426-530) FLOW: one tilt-push, him at the desk (1F) -> down to the screen (1G "the screen went grey"); push-through at 52 (478).
const B05: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1280, cy: 720, s: 1.0 }, { f: 51, cx: 1280, cy: 770, s: 1.08 }], opt: { v0: { cy: 0.6, s: L(2) }, v1: { cy: 2.0, s: L(6) } },
    dollyIn: { n: 12, dir: -1 } },
  { at: 52, keys: [{ f: 0, cx: 1280, cy: 620, s: 1.03 }, { f: d('B05') - 53, cx: 1280, cy: 700, s: 1.12 }], opt: { v0: { cy: 2.5, s: L(6) }, v1: { cy: 0.6, s: L(2.5) } } },
]);
// B06 (530-565) PUNCH: the facade goes grey floor by floor (1H) under a fast drift down
const B06: ShotDef = rig({ keys: [{ f: 0, cx: 1280, cy: 640, s: 1.1 }, { f: d('B06') - 1, cx: 1280, cy: 800, s: 1.12 }] });
// B07 (565-635) PUNCH: tight on the door, push 3 %/s accelerating into the chorus (leaves at 7 %/s)
const B07: ShotDef = rig({
  keys: [{ f: 0, cx: 1280, cy: 720, s: 1.0 }, { f: d('B07') - 1, cx: 1280, cy: 700, s: 1.12 }],
  opt: { v0: { s: L(2) }, v1: { s: L(7) } },
});
// --- section 2, chorus 1
// B08 (635-704) PUNCH: the door fills the frame, push (the BACK AT sign swings in cut 6's own animation)
const B08: ShotDef = rig({ keys: pushKeys(d('B08'), { s0: 1.02, pct: 3.5, dy: -10 }) });
// B09 (704-774) PUNCH: close on him through the glass (the K plate, 4 / 42 / 429 on the sung digits, then sorry eyes: cut 6's track), on
// its own plate rig so the visor's live glass rides the move: push + a slight arc (truck left + roll). 2.5D when the K pack lands.
const K2B: VTrack = [[0, 'eyes'], [16, '4'], [26, '42'], [36, '429'], [58, 'sorry']];
const B09: ShotDef = rig({
  keys: V8 ? pushKeys(d('B09'), { cx: 1230, cy: 680, s0: 1.16, pct: 3.5, dx: -56, dy: -38, r0: 0.35, r1: -0.35 })   // rl8_fix2: V8 reframe, whole SHIP IT! wall in frame
    : pushKeys(d('B09'), { cx: 1316, cy: 700, s0: 1.3, pct: 3.5, dx: -36, r0: 0.35, r1: -0.35 }),
  // the visor (P1's state region, the seven-segment digits, the live glass) rides HIS slice, so it never slides off his face in 2.5D
  plate: { src: visorSrc('K', K2B), pack: KPACK('K'),
    on: (f, abs) => { const D = visorDigits('K', K2B); return { him: <><VisorRegion dir="K" tr={K2B} f={f} /><D f={f} shot={block('B09')} /><VisorSweep abs={abs} x={1316} y={669} w={430} h={200} /></> }; } },
  grain: true, over: () => (NEWK('K') ? null : <SignFace dir="K" />),
});
// B10 (774-913) FLOW: over his shoulder through the glass (2C) -> pan down onto his desk insert (2D); push-through at 69 (843)
const B10: ShotDef = rigs([
  // 0-68 (2C) on the P2 plate's own rig (P1's pack): over his shoulder, real parallax between his spikes, her and the room as it tilts down;
  // cut 6's framing (s 1.10, frame bottom <= 1309 so his paddle rim stays out) x the block's push
  { at: 0, keys: [{ f: 0, cx: 1220, cy: 600, s: 1.122 }, { f: 68, cx: 1300, cy: 708, s: 1.21 }], opt: { v1: { cy: 2.3, s: L(4) } }, grain: true,
    plate: { src: C5_2C_WIDE, pack: 'c7/apt/2C_P2', focus: 'her' } },
  { at: 69, keys: [{ f: 0, cx: 1280, cy: 640, s: 1.03 }, { f: d('B10') - 70, cx: 1280, cy: 730, s: 1.12 }], opt: { v0: { cy: 2.5, s: L(4) } } },
]);
// B12 (1121-1190) PUNCH: close on him behind the glass + her message on the glass (cut 6's GlassChat, riding the move), push
const B12: ShotDef = rig({
  keys: pushKeys(d('B12'), { cx: 1280, cy: 720, s0: 1.02, pct: 3.5, dx: 30, dy: -8 }),
  plate: { src: visorSrc('K', [[0, 'eyes']]), pack: KPACK('K') }, grain: true,
  over: ({ f, abs, shot }) => <>{NEWK('K') ? null : <SignFace dir="K" />}<VisorSweep abs={abs} x={1316} y={669} w={430} h={200} seed={2} /><Glass2G f={f} shot={shot} /></>,
});
// --- section 3
// B13 (1190-1330) FLOW: low at the threshold tipping down (3A) -> WALL DOLLY (her side -> lobby, at 70 = 1260) -> waist-up him with
// the crossword (3B). One outer push under both.
const B13: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1280, cy: 680, s: 1.02 }, { f: 69, cx: 1280, cy: 760, s: 1.09 }], dollies: [{ at: 70, n: 12, dir: -1 }] },
  { at: 70, keys: [{ f: 0, cx: 1290, cy: 720, s: 1.02 }, { f: d('B13') - 71, cx: 1260, cy: 700, s: 1.1 }], dollies: [{ at: 70, n: 12, dir: -1 }] },
]);
// B14 (1330-1451) FLOW: her phone, in her hand: hand-held drift (+-6 px, 0.4 deg, low-pass) + a slow push; leaves into B15's match
// The last 22 frames push into the phone's screen until it is the size and place of B15's laptop screen (the rectangle match).
const B14: ShotDef = rig({
  keys: [{ f: 0, cx: 1270, cy: 724, s: 1.03 }, { f: 98, cx: 1260, cy: 718, s: 1.09 }, { f: d('B14') - 1, cx: 1250, cy: 720, s: 1.3 }],
  opt: { v1: { s: L(25) } }, hand: { amp: 6, roll: 0.4, seed: 14 },
});

export const A1: Record<string, ShotDef> = { B01, B02, B03, B04, B05, B06, B07, B08, B09, B10, B11, B12, B13, B14 };
