// Cut 7 sections 4-6, blocks B15-B30 (PLAN7 §1; rl7_ra). Same approach as ../s01: one camera per block over the cut 6 picture.
import React from 'react';
import { ShotDef } from '../../types';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ROOM6 } from '../../c5d/6x';
import { PL, Pl } from '../../s10/_lib';
import { M1Needle, PlateDigit } from '../../s11/_meter';
import { outBack } from '../../../ease';
import { Room6Life, VisorSweep, ROOM6_NOSIGN } from '../kit/sets';
import { SignFace } from '../kit/logo';
import { B21 } from './b21';
import { visorSrc, Glass5H, NEWK, KPACK } from '../../c5d/K';
import { rig, rigs, pushKeys } from '../kit';
import { block, beatsIn } from '../kit/blocks';

const L = (pct: number) => Math.log(1 + pct / 100) / 30;
const d = (id: string) => block(id).dur;

// --- section 4, verse 2
// B15 (1451-1590) FLOW: the laptop (4T a): arrives from B14's phone on the screen rectangle, then slides right along the page
// toward the tab/incognito read, slow push. Moving at both ends.
const B15: ShotDef = rig({ keys: pushKeys(d('B15'), { cx: 1240, cy: 720, s0: 1.02, pct: 2.5, dx: 70, dy: -10 }) });
// B16 (1590-1650) PUNCH: push HARD into the model picker as it flips (W4: the chip was ~8 px on a phone; at the landing it is
// ~2.1x: >= 40 px tall at phone size). Lands on the chip.
const B16: ShotDef = rig({
  keys: [{ f: 0, cx: 1500, cy: 800, s: 1.08 }, { f: 40, cx: 1930, cy: 890, s: 2.05 }, { f: d('B16') - 1, cx: 1950, cy: 892, s: 2.15 }],
  opt: { v0: { s: L(8), cx: 6, cy: 1.5 } },
});
// B17 (1650-1712) PUNCH: cut on the beat to the picker re-opening (Opus -> Sonnet, "little brother": cut 6 plays that flip here), tight
// on the dropdown, then a pull back as Sonnet lands to the page ("Up late, Totally Not Adita?"). PLAN7 wanted her face here: that
// needs a P1 face render at the laptop (not in P1's list) -> noted for the director; the flip stays readable instead.
const B17: ShotDef = rig({
  keys: [{ f: 0, cx: 1785, cy: 630, s: 1.75 }, { f: 30, cx: 1700, cy: 660, s: 1.55 }, { f: d('B17') - 1, cx: 1380, cy: 720, s: 1.12 }],
  opt: { v1: { s: -L(4) } },
});
// B18 (1712-1851) FLOW: pull back and RISE from the foot of the door, moving from frame 0 (cut 6: 72% still)
const B18: ShotDef = rig({
  keys: [{ f: 0, cx: 1280, cy: 860, s: 1.2 }, { f: d('B18') - 1, cx: 1280, cy: 690, s: 1.03 }],
  opt: { v1: { s: -L(1.5), cy: -0.4 } },
});
// B19 (1851-1920) FLOW: 4F's backoff slide (cut 6's stops), under a slow push; the WALL DOLLY to him leaves from its last 12 frames
const B19: ShotDef = rig({ keys: pushKeys(d('B19'), { s0: 1.02, pct: 2.5, dx: -20 }), dollyOut: { n: 12, dir: -1 } });
// B20 (1920-1990) PUNCH: arrives through the wall (replaces the 90-degree hard cut, W18), lands on the 429 visor at 35 (1955)
const B20: ShotDef = rig({
  keys: [{ f: 0, cx: 1280, cy: 720, s: 1.0 }, { f: 35, cx: 1280, cy: 690, s: 1.1 }, { f: d('B20') - 1, cx: 1280, cy: 684, s: 1.13 }],
  opt: { v0: { s: L(3) } }, dollyIn: { n: 12, dir: -1 },
});
// B21 (1990-2129) FLOW: ./b21.tsx (parcel to parcel, slowing on each label)
// B22 (2129-2302) FLOW: one 2.5-bar push, him + the notice board -> the dial; the drums stop at 104 (2233) and the push eases from 4 to
// 4.5 %/s + a drift and a slight roll toward the dial (the meter's plain wall reads as still under a slower move: prev2 25.6%)
const B22: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1280, cy: 720, s: 1.02 }, { f: 103, cx: 1300, cy: 700, s: 1.2 }], opt: { v1: { s: L(5.5) } } },
  { at: 104, keys: [{ f: 0, cx: 1320, cy: 735, s: 1.03, r: -0.3 }, { f: d('B22') - 105, cx: 1240, cy: 700, s: 1.14, r: 0.3 }], opt: { v0: { s: L(4) }, v1: { s: L(3.5) } } },
]);
// --- section 5, chorus 2
// B23 (2302-2372) PUNCH x3: one framing per "Rate" (beats 1/18/35), each with its own drift, alternating direction
// Every framing keeps the top edge (the 418 visor sits at the plate's top: cy = 720/s keeps it whole, cut 6's "top edge kept").
const top = (s0: number) => 720 / s0;
const B23: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1240, cy: top(1.02), s: 1.02 }, { f: 17, cx: 1272, cy: top(1.05), s: 1.05 }] },
  { at: 18, keys: [{ f: 0, cx: 1300, cy: top(1.14), s: 1.14 }, { f: 16, cx: 1262, cy: top(1.172), s: 1.172 }] },
  { at: 35, keys: [{ f: 0, cx: 1250, cy: top(1.08), s: 1.08 }, { f: d('B23') - 36, cx: 1300, cy: top(1.13), s: 1.13 }] },
]);
// B24 (2372-2511) FLOW: him and THE cat, push + arc (the 2441 plate swap stays)
const B24: ShotDef = rig({ keys: pushKeys(d('B24'), { cx: 1320, s0: 1.02, pct: 3, dx: -80, r0: -0.3, r1: 0.3 }) });
// B25 (2511-2719) FLOW: her wall by the door -> push down to the laptop (5D) -> push-through into the 5E screen at 69 (2580)
const B25: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1280, cy: 680, s: 1.02 }, { f: 68, cx: 1280, cy: 780, s: 1.14 }], opt: { v1: { cy: 2, s: L(6) } } },
  { at: 69, keys: [{ f: 0, cx: 1280, cy: 700, s: 1.03 }, { f: d('B25') - 70, cx: 1260, cy: 730, s: 1.13 }], opt: { v0: { cy: 1, s: L(6) } } },
]);
// B26 (2719-2858) FLOW: ONE push with beat accents (speed bumps on the off-beats, no punch-ins), on the K plate's own rig: her three
// messages land on the glass (cut 6's GlassChat, riding the move), his visor glass alive
const B26: ShotDef = rig({
  keys: pushKeys(d('B26'), { cx: 1290, cy: 720, s0: 1.02, pct: 2.5, dx: -40 }),
  bumps: { at: beatsIn(block('B26')).filter((_, i) => i % 2 === 1), amt: 0.012, len: 10 },
  plate: { src: visorSrc('K', [[0, 'eyes']]), pack: KPACK('K') }, grain: true,
  over: ({ f, abs, shot }) => <>{NEWK('K') ? null : <SignFace dir="K" />}<VisorSweep abs={abs} x={1316} y={669} w={430} h={200} seed={5} /><Glass5H f={f} shot={shot} /></>,
});
// --- section 6, the countdown
// B27 (2858-2927) PUNCH: two-room wide (cut 6: 100% still): slow truck toward the door + push
// (own plate through SliceCam: c5/6A/room_rain.jpg, 2.5D when P1's pack lands) + rain on her window, neon hum/flicker, candles
// It ends just wider than B28's first frame (6B starts on this plate at s 1.012 and punches in to her phone on the beat), so the cut
// reads as a punch-in, not a jump back out.
const B27: ShotDef = rig({ keys: [{ f: 0, cx: 1345, cy: 728, s: 1.075 }, { f: d('B27') - 1, cx: 1272, cy: 720, s: 1.0 }], opt: { v1: { cx: -0.6, s: -L(1) } },
  plate: { src: ROOM6_NOSIGN, pack: 'c7/apt/6A_room_rain' }, over: ({ abs }) => <Room6Life abs={abs} avoid={[2858, 2927]} /> });
// B28 (2927-2997) PUNCH: the phone on the yoga block, push 4 %/s
// (0-17: the room through SliceCam with the new neon, 6B's own punch toward her phone (cut 6: s 1.012 -> 1.12 out-cubic to beat 1);
// 18-: cut 6's sleep-story phone screen under a 4 %/s push)
const B28: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1280, cy: 720, s: 1.012 }, { f: 6, cx: 1323, cy: 976, s: 1.077 }, { f: 17, cx: 1360, cy: 1080, s: 1.12 }], opt: { v1: { cx: 0.5, cy: 1.5, s: L(3) } },
    plate: { src: ROOM6_NOSIGN, pack: 'c7/apt/6A_room_rain' }, over: ({ abs }) => <Room6Life abs={abs} avoid={[2927, 2945]} /> },
  { at: 18, keys: pushKeys(d('B28') - 18, { s0: 1.012, pct: 4, dy: 10 }) },
]);
// B29 (2997-3066) FLOW: very close on her watch; the push accelerates in the last second until the watch face is the size and place
// of the HOURS AWAKE dial at B30's first frame (the match cut). Watch face in cut 6's 6C: centre (1537, 720), r ~144 at s 1.
const MATCH = { s: 2.0, cx: 1166, cy: 847 };       // watch (6C (1476, 695)) -> screen (1900, 416), the dial at B30 f0 (measured on stills)
const B29: ShotDef = rig({
  keys: [{ f: 0, cx: 1500, cy: 730, s: 1.04 }, { f: 38, cx: 1450, cy: 760, s: 1.16 }, { f: d('B29') - 1, ...MATCH }],
  opt: { v1: { s: L(40) } },
});
// B30 (3066-3136) FLOW: the MATCH CUT: her round watch face -> the round HOURS AWAKE dial, same size and place (M1 plate at s 1.1:
// dial (1967, 422) r ~250 plate -> screen (1908, 464) r ~275); the needle climbs a notch; the camera pulls back off the dial, then on
// the beat (35 = 3101) the pull-back carries on in the two-room wide (room_rain) out to the wide on "No, I'll wait", idle life on.
const Dial: ShotDef = { stage: ({ shot }) => { const f = useCurrentFrame(); const v = 19 + 0.85 * outBack(Math.min(1, Math.max(0, (f - 6) / 14)), 2.2) + 0.05 * Math.sin(f * 1.3);
  return <AbsoluteFill><Pl src={PL.M1} /><M1Needle v={v} /><PlateDigit f={f} at={1e9} from="0" to="0" /></AbsoluteFill>; void shot; } };
const B30: ShotDef = rigs([
  { at: 0, inner: Dial, keys: [{ f: 0, cx: 1396, cy: 655, s: 1.1 }, { f: 34, cx: 1300, cy: 715, s: 1.0 }], opt: { v0: { s: -L(6) } } },
  { at: 35, keys: [{ f: 0, cx: 1330, cy: 700, s: 1.22 }, { f: d('B30') - 36, cx: 1280, cy: 720, s: 1.03 }], opt: { v0: { s: -L(12) }, v1: { s: -L(3) } },
    plate: { src: ROOM6_NOSIGN, pack: 'c7/apt/6A_room_rain' }, over: ({ abs }) => <Room6Life abs={abs} avoid={[3101, 3136]} /> },
]);

export const A4: Record<string, ShotDef> = { B15, B16, B17, B18, B19, B20, B21, B22, B23, B24, B25, B26, B27, B28, B29, B30 };
