// B49 (4975-5148) FLOW, PLAN7 row 49 = her P09 "Highlight/enhance maybe exclamation can you retire me I'm exhausted" (C1) + K4/K6/W19.
// Two rooms wide on P1's tube-neon plates (c7/10B/tube, same camera as cut 6's 10B, 2.5D by its seat_* packs):
//   LIVE LOVE / RETIRE ME hums -> two buzzes -> dark 3 f -> RETIRE ME! relights on the downbeat 5009 (pink, stutter-on) -> I'M EXHAUSTED on
//   the next beat 5027 (warm white) -> held whole in frame on her, her face lit by it, to 5066 (1.9 s from the relight) -> the camera trucks
//   LEFT through the wall (WallDolly, the rendered cross-section) and lands close on HIS profile for "I don't get tired" (5069-5088), the
//   RETIRE ME! glow still on the glass behind him; his visor + chest light pulse with HIS voice (robot WAV envelope); he rises on the
//   heartbeat kick 5113 (stepped: seat -> mid 2 f -> ear) and the camera starts craning up into B50.
// Plates swappable (one line each, APT list in workers/rl7_rb/STATUS.md): her room is the old dressing until the finals lane re-renders it.
import React from 'react';
import { Img, staticFile } from 'remotion';
import { ShotDef } from '../../types';
import { rigs } from '../kit/rig';
import { Whip, has } from '../kit/trans';
import { Glow, visorK, neonBuzz } from '../kit/life';
import { block } from '../kit/blocks';

const L = (pct: number) => Math.log(1 + pct / 100) / 30;
// rl7_p2's re-lettered plates (pile label headers + the 11A plaque in the double-click logo, her H7.1) when present, else P1's tube plates
const P2 = has('c7/10B/p2/plate_a2.jpg') && has('c7/10B/p2_seat_a2/pack.json');
const P2E = has('c7/11A/p2/H2a_ear.jpg');
// rl7_final: rl7_room's locked-room B49 (cream sofa, charcoal wall, the big sign A; workers/rl7_room/ROOM_READY): 4 sign states + per-line glows
const ROOM = true;
const PK0 = (st: 'old' | 'dark' | 'a2') => (P2 ? `c7/10B/p2_seat_${st}` : `c7/10B/seat_${st}`);
const RPK = { old: 'c7/room/B49_retire', dark: 'c7/room/B49_off', rmoff: 'c7/room/B49_rm_off', a2: 'c7/room/B49_rm_l23' };
export const PK = (st: 'old' | 'dark' | 'a2' | 'rmoff') => (ROOM ? RPK[st] : PK0(st === 'rmoff' ? 'dark' : st));
export const P10B = {
  old: P2 ? 'c7/10B/p2/plate_old.jpg' : 'c7/10B/tube/plate_old.jpg', dark: P2 ? 'c7/10B/p2/plate_dark.jpg' : 'c7/10B/tube/plate_dark.jpg', a2: P2 ? 'c7/10B/p2/plate_a2.jpg' : 'c7/10B/tube/plate_a2.jpg',
  glowOld: 'c7/10B/tube/glow_old.png', glowA2: 'c7/10B/tube/glow_a2.png',
  // his states (11A): P2's stepped robot states replace these when they land (workers/rl7_p2/PATCH.md)
  seat: P2 ? 'c7/10B/p2/plate_a2.jpg' : 'c7/10B/tube/plate_a2.jpg', mid: P2E ? 'c7/11A/p2/H2a_mid.jpg' : 'c7/11A/tube/H2a_mid.jpg', ear: P2E ? 'c7/11A/p2/H2a_ear.jpg' : 'c7/11A/tube/H2a_ear.jpg',
};
if (ROOM) Object.assign(P10B, { old: 'c7/room/10B/plate_retire.jpg', dark: 'c7/room/10B/plate_off.jpg', a2: 'c7/room/10B/plate_rm_l23.jpg', glowOld: 'c7/room/10B/glow_retire.png',
  seat: 'c7/room/10B/plate_rm_l23.jpg', ear: 'c7/room/11A/t10.jpg' });
const RM_OFF = 'c7/room/10B/plate_rm_off.jpg', GLOW_L2 = 'c7/room/10B/glow_l2.png', GLOW_L3 = 'c7/room/10B/glow_l3.png';
const B = block('B49'); const A = (abs: number) => abs - B.from;   // block-local
const T = { buzz1: 4994, buzz2: 5000, dark: 5006, line1: 5009, line2: 5027, cut: 5076, stand: 5113 };
const DOLLY = 10;
// the two lines' split on the stage (neon at stage y ~ 432-480 / 528-576 in the a2 state)
const SPLIT = 505;
/** neon light level 0..1 of a line at film frame g: stutter-on (tube strike) over 6 frames, then the hum */
const strike = (g: number, at: number) => { const d = g - at; if (d < 0) return 0; if (d >= 6) return neonBuzz(g, 41, [T.line1, T.line2]); return [0.55, 0.15, 0.9, 0.4, 1, 0.85][d]; };
const oldLevel = (g: number) => {
  if (g >= T.dark) return 0;
  if (g >= T.buzz1 && g < T.buzz1 + 3) return [0.25, 0.7, 0.35][g - T.buzz1];
  if (g >= T.buzz2 && g < T.buzz2 + 4) return [0.1, 0.5, 0.05, 0.6][g - T.buzz2];
  return neonBuzz(g, 17, [4975]);
};
const full: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };
/** the glow of a state laid on the back-wall slice (plus-lighter over the dark plate = that state), clipped to rows [y0, y1) */
const GlowL: React.FC<{ src: string; op: number; y0?: number; y1?: number }> = ({ src, op, y0 = 0, y1 = 1440 }) => (op > 0.01 ? (
  <Img src={staticFile(src)} style={{ ...full, opacity: Math.min(1, op), mixBlendMode: 'plus-lighter', clipPath: `inset(${y0}px 0 ${1440 - y1}px 0)` }} />) : null);

// the neon state of the room part: which pack/plate is the base, and what glow rides the back wall
const roomState = (g: number): { pack: string; src: string; d0?: React.ReactNode } => {
  if (g < T.dark) {   // LIVE LOVE / RETIRE ME: dark base + the old glow at its hum/buzz level (the light on her face is in the full plate only:
    const lv = oldLevel(g);   // keep the full old plate while steady, the dark base + glow only while it buzzes)
    if (lv > 0.93) return { pack: PK('old'), src: P10B.old };
    return { pack: PK('dark'), src: P10B.dark, d0: <GlowL src={P10B.glowOld} op={lv} /> };
  }
  if (ROOM) {   // the whole sign dark 5006-5008 (rm_off), then each line's own glow strikes whole: no matte seam (the judge's B49 nit)
    if (g < T.line1) return { pack: PK('rmoff'), src: RM_OFF };
    if (g < T.line2 + 6) return { pack: PK('rmoff'), src: RM_OFF, d0: <><GlowL src={GLOW_L2} op={strike(g, T.line1)} /><GlowL src={GLOW_L3} op={strike(g, T.line2)} /></> };
    return { pack: PK('a2'), src: P10B.a2 };
  }
  if (g < T.line1) return { pack: PK('dark'), src: P10B.dark };
  if (g < T.line2 + 6) {
    const l1 = strike(g, T.line1), l2 = strike(g, T.line2);
    return { pack: PK('dark'), src: P10B.dark, d0: <><GlowL src={P10B.glowA2} op={l1} y1={SPLIT} /><GlowL src={P10B.glowA2} op={l2} y0={SPLIT} /></> };
  }
  return { pack: PK('a2'), src: P10B.a2 };
};
// light falling on her face from the relit sign (the full a2 plate has it baked; this carries it during the strike frames)
const FaceLight: React.FC<{ g: number }> = ({ g }) => {
  if (g < T.line1 || g >= T.line2 + 6) return null;
  const k = 0.6 * strike(g, T.line1) + 0.4 * strike(g, T.line2);
  return <Glow x={1060} y={860} rx={300} ry={260} color={ROOM ? 'rgba(255,190,140,0.55)' : 'rgba(255,120,170,0.55)'} op={0.35 * k} />;
};
// his visor glass + chest light (side view; stage px of the seated / ear plates), driven by his voice from 5071, idle pulse before
const HisLights: React.FC<{ g: number; ear: boolean }> = ({ g, ear }) => {
  const turn = ROOM ? (g < 5110 ? 1 : g < 5113 ? (5113 - g) / 3 : g < 5128 ? 0 : g < 5131 ? (g - 5128) / 3 : 1) : 1;
  const k = visorK(g) * turn; if (k <= 0.001) return null;
  const v = ear ? { x: 700, y: 760 } : { x: 735, y: 820 };
  const c = ear ? { x: 640, y: 1010 } : { x: 578, y: 1118 };
  return <><Glow x={v.x} y={v.y} rx={70} ry={42} color="rgba(150,235,255,0.9)" op={0.32 * k} />
    <Glow x={c.x} y={c.y} rx={26} color="rgba(90,255,190,0.95)" op={0.65 * k} /></>;
};
// her H7.1 logo: cut 6's 11A lobby regions still carry the old script ShipIt! plaque; P1's 10B plate (same camera, same plaque) has the
// double-click logo, so its plaque region is laid over the ear/mid plates (box measured on both plates: identical frame and lighting)
export const PLAQUE = [398, 138, 697, 292];
export const PlaquePatch: React.FC = () => P2E ? null : <Img src={staticFile(P10B.a2)} style={{ ...full, clipPath: `inset(${PLAQUE[1]}px ${2560 - PLAQUE[2]}px ${1440 - PLAQUE[3]}px ${PLAQUE[0]}px)` }} />;
// the rise: no T-pose "mid" frame (PLAN7 K4); until P2's stepped states land it is seat -> ear in a 2-frame upward snap (smeared)
// rl7_p2's 4 stepped states (c7/11A/p2/st1..st4: rise / stand / turn / bent to her ear, same camera + plate) when landed: a robot rises in
// clean steps on the heartbeat (3 / 3 / 4 frames, a small settle on each), no smear needed
const P2ST = has('c7/11A/p2/st4.jpg');
const STEPS = [3, 6, 10];   // frames after T.stand at which st2 / st3 / st4 come in (st1 at 0)
const stepOf = (g: number) => { const d = g - T.stand; if (d < 0) return -1; return d < STEPS[0] ? 1 : d < STEPS[1] ? 2 : d < STEPS[2] ? 3 : 4; };
// rl7_room's real head turn: st1 (5113-5115) -> t00 standing left profile (5116-5118) -> t01..t10 one per frame (5119-5128) -> t10 hold
const roomHis = (g: number) => { const d = g - T.stand; if (d < 0) return P10B.seat; if (d < 3) return 'c7/room/11A/st1.jpg'; if (d < 6) return 'c7/room/11A/t00.jpg';
  return `c7/room/11A/t${String(Math.min(10, d - 5)).padStart(2, '0')}.jpg`; };
const hisSrc = (g: number) => (ROOM ? roomHis(g) : g < T.stand ? P10B.seat : P2ST ? `c7/11A/p2/st${stepOf(g)}.jpg` : P10B.ear);
const RiseSmear: React.FC<{ g: number }> = ({ g }) => {
  const d = g - T.stand; if (P2ST || d < 0 || d > 1) return null;
  return <Whip vx={0} vy={d === 0 ? -80 : -30} n={7} render={() => <Img src={staticFile(P10B.ear)} style={full} />} />;
};

// framings (stage px of the 2560x1440 plate box): A0 the wide two rooms; A1 her + the whole sign (neon x ~1424-1888, y ~352-592; her face ~1060, 860);
// H0 his seated profile (head ~ 704, 800); H1 the risen ear pose (head ~ 656, 752) drifting up toward the HOURS AWAKE gauge (272, 208) for B50
export const B49: ShotDef = rigs([
  { at: 0,
    keys: ROOM ? [{ f: 0, cx: 1330, cy: 735, s: 1.06 }, { f: A(T.line1), cx: 1400, cy: 690, s: 1.22 }, { f: A(5066), cx: 1440, cy: 690, s: 1.25 }, { f: A(T.cut) - 1, cx: 1360, cy: 690, s: 1.3 }]
      : [{ f: 0, cx: 1330, cy: 735, s: 1.06 }, { f: A(T.line1), cx: 1380, cy: 690, s: 1.22 }, { f: A(T.cut) - 1, cx: 1250, cy: 690, s: 1.34 }],
    opt: { v1: { cx: -9, s: L(2) } },
    plate: { src: (f) => roomState(B.from + f).src, pack: (f) => roomState(B.from + f).pack, depth: 0.8,
      on: (f, abs) => { const st = roomState(abs); return st.d0 ? { d0: st.d0 } : {}; } },
    over: ({ abs }) => <><FaceLight g={abs} /><HisLights g={abs} ear={false} /></>,
    dollies: [{ at: A(T.cut), n: DOLLY, dir: -1, travel: 360 }], grain: true,
  },
  { at: A(T.cut),
    // lands close on his profile with the RETIRE ME! sign just out of frame right (no cropped letters), lead room toward her
    keys: [{ f: 0, cx: 860, cy: 790, s: 1.7 }, { f: 22, cx: 735, cy: 800, s: 1.8 }, { f: A(T.stand) - A(T.cut) - 1, cx: 725, cy: 790, s: 1.84 },
      // the camera tilts up WITH his steps (rise 5113, stand 5116, turn 5119), then settles on the bent-to-her-ear pose
      { f: A(T.stand) - A(T.cut) + 5, cx: 715, cy: 600, s: 1.8 }, { f: A(T.stand) - A(T.cut) + 11, cx: 712, cy: 610, s: 1.8 },
      { f: B.dur - 1 - A(T.cut), cx: 712, cy: 600, s: 1.82 }],   // s >= 1.8 keeps the RETIRE ME! sign (x >= 1424) just out of frame
    opt: { v0: { cx: -9 }, v1: { cy: -3, s: L(1) } },
    plate: { src: (f) => hisSrc(B.from + f) },
    dollies: [{ at: A(T.cut), n: DOLLY, dir: -1, travel: 360 }],
    over: ({ abs }) => <>{ROOM ? null : <><RiseSmear g={abs} />{abs >= T.stand ? <PlaquePatch /> : null}</>}<HisLights g={abs} ear={abs >= T.stand} /></>,
    mod: (f) => { const g = B.from + f, d = g - T.stand; if (d < 0) return {};
      if (ROOM) return d < 3 ? { ds: 0.006 * [1, 0.5, 0.2][d] } : {};   // a small settle on the rise only; none during the turn
      if (P2ST) { const at = [0, ...STEPS].filter((x) => x <= d).pop() ?? 0; const e = d - at; return e < 3 ? { ds: 0.006 * [1, 0.5, 0.2][e] } : {}; }
      return d < 10 ? { ds: 0.012 * Math.sin((d / 10) * Math.PI) } : {}; },
    grain: true,
  },
]);
