// Cut 7 sections 7-8, blocks B31-B41 (PLAN7 §1; rl7_rb). One camera per block over the cut 6 picture (rl7_fixb's fixes are in it:
// 8D's request list, 8E's typing dots under her message, 7E1's LED visor words, 8G's tube neon), plus the block's own life.
import React from 'react';
import { V8 } from '../../../v8';   // rl8_fix2: v8 flag
import { ShotDef, ShotProps } from '../../types';
import { rig, rigs, pushKeys } from '../kit/rig';
import { block } from '../kit/blocks';
import { make7E1, beatF } from '../../c5d/7E1';
import { Visor7Led } from '../fix713/Visor7Led';
import type { Quad } from '../../../blocks/ScreenInsert';
import { visorSrc, VisorRegion, KPACK, NEWK, visorState } from '../../c5d/K';
import { VisorSeg, VISOR_ROWS } from '../kit/seg';
import { VisorSweep } from '../kit/sets';
import { Glow, visorK } from '../kit/life';
import { SignFace } from '../kit/logo';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { shotDef } from '../../index';
import { OLD } from '../kit/blocks';
import { has } from '../kit/trans';
import { Grain2 } from '../../../blocks/real/Scene';

const L = (pct: number) => Math.log(1 + pct / 100) / 30;
const d = (id: string) => block(id).dur;

// --- section 7
// B31 (3136-3275) FLOW: her stories row (7A), push in toward his ring, then on 3205 a push-through down into the status page (7B), tilting
// down the board to "all systems operational" (cut 6 7B: 67% still)
const B31: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1280, cy: 700, s: 1.03 }, { f: 68, cx: 1180, cy: 640, s: 1.16 }], opt: { v1: { s: L(5), cy: 1.5 } } },
  { at: 69, keys: [{ f: 0, cx: 1280, cy: 600, s: 1.1 }, { f: d('B31') - 70, cx: 1280, cy: 820, s: 1.16 }], opt: { v0: { cy: 3.2, s: L(2) } } },
]);
// B32 (3275-3344) PUNCH: the new chat on her phone, push 5 %/s toward his reply bubbles (W14: the DM bubbles read bigger as it lands)
const B32: ShotDef = rig({ keys: [{ f: 0, cx: 1280, cy: 720, s: 1.04 }, { f: d('B32') - 1, cx: 1330, cy: 820, s: 1.3 }], opt: { v0: { s: L(5) } } });
// B33 (3344-3414) PUNCH: close on her ("you looked right through me", cut 6: 99% still): drift across + a slow push, hand-held breath
const B33: ShotDef = rig({ keys: pushKeys(d('B33'), { cx: 1200, cy: 690, s0: 1.06, pct: 6, dx: 150, dy: 16, r0: -0.5, r1: 0.4 }), hand: { amp: 9, roll: 0.35, seed: 33 } });   // prev1: 64% still at 3 %/s (soft close-up): a real move
// B34 (3414-3553) FLOW: the date (P06: the LED visor words, one dot pitch, rl7_fixb). The push starts tight on him + the visor (WOW! / TRUE!
// read) and travels LEFT along the table to end on HER face + side-eye (W3: she slid out of frame in cut 6), Cooper drooping between them.
const GLASS7: Quad = [[1864, 374], [1968, 372], [1968, 410], [1864, 414]];
const Visor7: React.FC<{ f: number; shot: ShotProps['shot'] }> = ({ f, shot }) => (
  <Visor7Led f={f} beats={[0, 1.5, 3, 4.5, 6].map((b) => (b === 0 ? 0 : beatF(shot, b)))} quad={GLASS7} />);
const DATE = make7E1({ from: { cx: 1280, cy: 720 }, to: { cx: 1280, cy: 720 }, s1: 1.0, Visor: Visor7 });
const B34: ShotDef = rig({ inner: DATE,
  keys: [{ f: 0, cx: 1760, cy: 560, s: 1.95 }, { f: 50, cx: 1560, cy: 600, s: 1.72 }, { f: 100, cx: 1050, cy: 660, s: 1.5 }, { f: d('B34') - 1, cx: 860, cy: 680, s: 1.46 }],
  opt: { v1: { cx: -2 } } });
// B35 (3553-3622) PUNCH: the group chat, hand-held drift + push
const B35: ShotDef = rig({ keys: pushKeys(d('B35'), { cx: 1280, cy: 720, s0: 1.04, pct: 4, dy: 30 }), hand: { amp: 7, roll: 0.35, seed: 35 } });
// B36 (3622-3691) FLOW, K10 (the glass is the setup for 11D / 13C-13D): her phone -> she sends it, then on the beat (3657) her view through the
// door glass: HIS HAND sets THE glass down on his desk in real steps (rl7_p2's c7/7H/p2/T28_g0..g4: comes down in his hand, its shadow lands,
// held, lets go, hand up out of frame) instead of cut 6's dissolve, then the glass alone (T28_a) holds, full and clear, under the push.
const CUT7H = 3657;
const P7H = has('c7/7H/p2/T28_a.jpg');
const glassSrc = (g: number) => { const d = g - CUT7H; const k = d < 2 ? 'g0' : d < 4 ? 'g1' : d < 8 ? 'g2' : d < 10 ? 'g3' : d < 12 ? 'g4' : 'a'; return `c7/7H/p2/T28_${k}.jpg`; };
const Inner7H: ShotDef = { stage: (p: ShotProps) => {
  const f = useCurrentFrame(); const g = p.shot.from + f; const S = shotDef('7H').stage;
  if (!P7H || g < CUT7H) return <S {...p} shot={OLD('7H')} />;
  const k = Math.min(1, Math.max(0, (g - CUT7H) / (3690 - CUT7H))); const e = 0.5 - 0.5 * Math.cos(Math.PI * k); const sc = 1 + 0.045 * e;
  return <AbsoluteFill style={{ overflow: 'hidden' }}><AbsoluteFill style={{ transformOrigin: '1290px 760px', transform: `scale(${sc.toFixed(5)})` }}>
    <Img src={staticFile(glassSrc(g))} style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 }} /></AbsoluteFill><Grain2 f={f} /></AbsoluteFill>; },
  screen: shotDef('7H').screen };
const B36: ShotDef = rig({ inner: Inner7H, keys: pushKeys(d('B36'), { cx: 1280, cy: 700, s0: 1.03, pct: 3.5, dy: 40 }), hand: { amp: 5, roll: 0.3, seed: 36 } });

// --- section 8, chorus 3
// B37 (3691-3830) FLOW: low behind the car, push; the street plate + meter digits (cut 6 8A)
const B37: ShotDef = rig({ keys: pushKeys(d('B37'), { cx: 1300, cy: 740, s0: 1.03, pct: 3, dx: -50, dy: -10 }) });
// B38 (3830-3969) FLOW: the request list (her H7.25 / H7.26 via rl7_fixb: "PR REVIEW before standup at 9!!!!!!", no dog genius): a slow
// crane down the list with a beat accent per "Rate", landing on the last line held >= 2 s
const B38: ShotDef = rig({ keys: [{ f: 0, cx: 1280, cy: 620, s: 1.08 }, { f: 70, cx: 1290, cy: 720, s: 1.16 }, { f: d('B38') - 1, cx: 1300, cy: 800, s: 1.24 }],
  bumps: { at: [0, 18, 35], amt: 0.008, len: 10 } });
// B39 (3969-4108) FLOW: two-room wide, push to the glass at 3 %/s (cut 6: 84% still) + "You up?" bubble, typing dots below it (H7.27)
const B39: ShotDef = rig({ keys: pushKeys(d('B39'), { cx: 1280, cy: 700, s0: 1.02, pct: 3, dx: 20, dy: -20 }) });
// B40 (4108-4177) PUNCH, W17 (the 5th 429 face gets a new beat): ONE push on the K plate (cut 6 8F's framing, the latched chain in frame, H7.28)
// and his 429 DROOPS INTO A YAWN: from beat 2 the seven-segment digits sag (squash, slide down, skew, dim) like heavy eyelids, hang a
// moment, and SNAP back lit on beat 3 (4142) with a strike flicker, then the visor blinks to his eyes on 40 as cut 6.
const TR8F: [number, string][] = [[0, '429'], [40, 'eyes']];
const droop = (f: number) => { if (f < 17) return 0; if (f < 29) { const t = (f - 17) / 12; return t * t * (3 - 2 * t); } if (f < 34) return 1; return 0; };
const Droop429: React.FC<{ f: number }> = ({ f }) => {
  const st = visorState(f, TR8F); const row = VISOR_ROWS.K; if (!/^\d+$/.test(st)) return null;
  const k = droop(f); const ys = row.quad.map((p) => p[1]); const by = Math.max(...ys); const cx = (row.quad[0][0] + row.quad[1][0]) / 2;
  const on = f >= 34 && f < 37 ? [0.35, 1, 0.6][f - 34] : 1 - 0.55 * k;
  return <div style={{ position: 'absolute', inset: 0, transformOrigin: `${cx}px ${by}px`, transform: `translateY(${(14 * k).toFixed(2)}px) scaleY(${(1 - 0.32 * k).toFixed(4)}) skewX(${(-5 * k).toFixed(2)}deg)` }}>
    <VisorSeg text={st} quad={row.quad} color={row.color} on={on} /></div>;
};
const B40: ShotDef = rig({
  keys: V8 ? [{ f: 0, cx: 1250, cy: 660, s: 1.10 }, { f: d('B40') - 1, cx: 1222, cy: 640, s: 1.19 }]   // rl8_fix2: V8 reframe, whole SHIP IT! wall in frame, chain still in
    : [{ f: 0, cx: 1296, cy: 664, s: 1.17 }, { f: d('B40') - 1, cx: 1290, cy: 648, s: 1.29 }], opt: { v0: { s: L(4.5) } },
  plate: { src: visorSrc('K', TR8F), pack: KPACK('K') }, grain: true,
  over: ({ f, abs }) => <><VisorRegion dir="K" tr={TR8F} f={f} />{NEWK('K') ? null : <SignFace dir="K" />}<Droop429 f={f} />
    <VisorSweep abs={abs} x={1316} y={669} w={430} h={200} /><Glow x={1377} y={1098} rx={60} color="rgba(120,255,220,0.9)" op={0.25 * visorK(abs)} /></>,
});
// B41 (4177-4246) PUNCH: the empty room, drift; the neon Click Click Ship It -> Ban 429 (rl7_fixb's tube states)
const B41: ShotDef = rig({ keys: pushKeys(d('B41'), { cx: 1250, cy: 720, s0: 1.03, pct: 3, dx: 60 }) });

export const B7: Record<string, ShotDef> = { B31, B32, B33, B34, B35, B36, B37, B38, B39, B40, B41 };
