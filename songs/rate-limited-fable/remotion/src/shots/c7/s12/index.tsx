// Cut 7 sections 12-13 (the last chorus, P10 "Polish this make it smoother not glitchy flowy", and 6:00), blocks B53-B61 (PLAN7 §1; rl7_rb).
// Section 12 has no hard punch-ins: every block is one move, inner cuts are matched-velocity push-throughs or wall dollies.
import React from 'react';
import { AbsoluteFill, Img, Sequence, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../../types';
import { OLD } from '../kit/blocks';
import { shotDef } from '../../index';
import { FONT } from '../../../theme';
import { T13 } from '../../c5d/13E';
import { rig, rigs, pushKeys } from '../kit/rig';
import { Steam, Glow } from '../kit/life';
import { Whip, has } from '../kit/trans';
import { Candle } from '../kit/sets';
import { block } from '../kit/blocks';

const L = (pct: number) => Math.log(1 + pct / 100) / 30;
const d = (id: string) => block(id).dur;

// --- section 12
// B53 (5390-5597) FLOW: one 3-bar move: tight on the door (12A, cut 6: 90% still) -> push-through at 5458 into the two-shot (12B), drifting
const B53: ShotDef = rigs([
  // left edge pinned (cx = 1280 / s): the LIVE LOVE / RETIRE ME neon at the frame's top left stays whole while it pushes on her face
  { at: 0, keys: [{ f: 0, cx: 1280 / 1.04, cy: 715, s: 1.04 }, { f: 67, cx: 1280 / 1.17, cy: 690, s: 1.17 }], opt: { v1: { s: L(5), cx: -0.6 } } },
  { at: 68, keys: [{ f: 0, cx: 1330, cy: 730, s: 1.03 }, { f: d('B53') - 69, cx: 1220, cy: 715, s: 1.14 }], opt: { v0: { s: L(4), cx: -0.8 } } },
]);
// B54 (5597-5805) FLOW: her swoon (12D) -> push-through at 5666 into the slowest slide of the film on the coffee table (12E): she blows the
// candles out on 5753 (C7 / W10). Until P2's 6 in-betweens land the blow is built in 2D so nothing pops: the flames gutter (a 5-frame
// cross-fade of the candle region only, flames shrinking), her pursed lips + Cooper's ears change ON the beat, and three smoke wisps rise
// from the wicks for ~1.7 s. The camera: one slide left with a slow push, the top edge pinned so LIVE LOVE / BAN 429 stays whole.
export const P12E = { stare: 'c7/apt/12E_stare_ban.jpg', blow: 'c7/apt/12E_blow_ban.jpg' };   // rl7_master: locked room   // P2's dressing-bible re-renders: same names or swap here
const BLOW = 5753, WICKS = [[1192, 1049], [1223, 1076], [1296, 1108]];   // rl7_master: rl7_apt_fin's wick tips (2880 px / 1.125)
const CANDLE_BOX = [1130, 975, 1360, 1150];   // stage px: the three candles + flames
const N12E: ShotDef = { stage: ({ shot }: ShotProps) => {
  const f = useCurrentFrame(); const g = shot.from + f; const full = { position: 'absolute' as const, left: 0, top: 0, width: 2560, height: 1440 };
  const gut = Math.min(1, Math.max(0, (g - (BLOW - 3)) / 5));         // 0 lit .. 1 out, centred on the beat
  const [x0, y0, x1, y1] = CANDLE_BOX;
  return (
    <AbsoluteFill>
      <Img src={staticFile(g < BLOW ? P12E.stare : P12E.blow)} style={full} />
      {g >= BLOW - 3 && g < BLOW + 3 ? <Img src={staticFile(g < BLOW ? P12E.blow : P12E.stare)} style={{ ...full, opacity: g < BLOW ? gut : 1 - gut, clipPath: `inset(${y0}px ${2560 - x1}px ${1440 - y1}px ${x0}px)` }} /> : null}
      {g < BLOW - 3 ? WICKS.map(([x, y], i) => <Candle key={i} abs={g} x={x} y={y - 16} seed={i + 3} size={0.7} />) : null}
      {g >= BLOW - 1 && g < BLOW + 52 ? WICKS.map(([x, y], i) => <Steam key={i} abs={g - BLOW + 40} x={x} y={y - 6} h={260} w={34} n={4} op={0.55 * Math.max(0, 1 - (g - BLOW) / 52)} seed={i + 11} color="214,210,204" />) : null}
      {g < BLOW ? <Glow x={1250} y={1060} rx={260} ry={200} color="rgba(255,190,120,0.6)" op={0.1 * (1 - gut)} /> : null}
    </AbsoluteFill>); } };
// 12D: the swoon (sway plate) -> on the beat 5632 she lands flat out on the sofa and Cooper flops beside her (flop plate). Cut 6 swapped the
// plates in one frame (a pop in the gate, "glitchy" in her P10 note): now the drop is a 3-frame downward smear (the fall), then the thump.
export const P12D = { sway: 'c7/apt/12D_sway_ban.jpg', flop: 'c7/apt/12D_flop_ban.jpg' };   // rl7_master: locked room
const LAND = 5632;
const N12D: ShotDef = { stage: ({ shot }: ShotProps) => {
  const f = useCurrentFrame(); const g = shot.from + f; const full = { position: 'absolute' as const, left: 0, top: 0, width: 2560, height: 1440 };
  const pl = (src: string) => () => <Img src={staticFile(src)} style={full} />;
  if (g === LAND - 1) return <AbsoluteFill><Whip vx={0} vy={70} n={7} render={pl(P12D.sway)} /><AbsoluteFill style={{ opacity: 0.45 }}><Whip vx={0} vy={90} n={7} render={pl(P12D.flop)} /></AbsoluteFill></AbsoluteFill>;
  if (g === LAND) return <AbsoluteFill><Whip vx={0} vy={48} n={7} render={pl(P12D.flop)} /></AbsoluteFill>;
  if (g === LAND + 1) return <AbsoluteFill><Whip vx={0} vy={18} n={5} render={pl(P12D.flop)} /></AbsoluteFill>;
  return <AbsoluteFill>{pl(g < LAND ? P12D.sway : P12D.flop)()}</AbsoluteFill>; } };
const B54: ShotDef = rigs([
  { at: 0, inner: N12D, keys: [{ f: 0, cx: 1260, cy: 720, s: 1.03 }, { f: 68, cx: 1300, cy: 735, s: 1.13 }], opt: { v1: { s: L(4), cx: 0.6 } },
    bumps: { at: [LAND - 5597], amt: 0.018, len: 9 }, grain: true },
  { at: 69, inner: N12E, keys: [{ f: 0, cx: 1340, cy: 720 / 1.03, s: 1.03 }, { f: d('B54') - 70, cx: 1190, cy: 720 / 1.19, s: 1.19 }], opt: { v0: { s: L(4), cx: 0.2 } }, grain: true },
]);
// B55 (5805-5874) PUNCH: her watch (panda 5:59), one push (kept), leaves centred on the dial
const B55: ShotDef = rig({ keys: pushKeys(d('B55'), { cx: 1280, cy: 720, s0: 1.03, pct: 4.5 }) });
// B56 (5874-5943) FLOW: her laptop at the limit ("5-hour limit reached · resets 6:00 AM", her "see you at 6?" in the composer, send greyed):
// the screen is up from frame 0 (cut 6 showed it for 28 f after a room beat), all of it readable for the whole 2.3 s; a slow push.
// (cut 6's 12G stage played 41 frames later: its room-then-screen cut at local 41 is gone, and its one-frame pop with it)
const SCR12G = 41;
const Screen12G: ShotDef = { stage: (p: ShotProps) => { const S = shotDef('12G').stage; const sh = OLD('12G');
  return <Sequence from={-SCR12G} layout="none"><S {...p} shot={sh} /></Sequence>; } };
const B56: ShotDef = rig({ inner: Screen12G, keys: pushKeys(d('B56'), { cx: 1280, cy: 760, s0: 1.02, pct: 2.6, dy: 10 }) });
// B57 (5943-6116) FLOW: street wide (12H's animation) -> push-through at 6012 into the lobby clock (12I), second hand sweeping to 6:00
const B57: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1280, cy: 720, s: 1.02 }, { f: 68, cx: 1300, cy: 715, s: 1.14 }], opt: { v1: { s: L(5) } } },
  { at: 69, keys: [{ f: 0, cx: 1280, cy: 720, s: 1.02 }, { f: d('B57') - 70, cx: 1280, cy: 720, s: 1.16 }], opt: { v0: { s: L(4) } } },
]);
// --- section 13
// B58 (6116-6185) PUNCH: the door fills the frame, silence, slow push
const B58: ShotDef = rig({ keys: pushKeys(d('B58'), { cx: 1280, cy: 720, s0: 1.03, pct: 3, dy: -10 }) });
// B59 (6185-6254) FLOW (K7: cut 6's black-and-white floor flash read as a glitch): SUNRISE AS A MOVE. One tilt down the ShipIt! facade from
// the lit roof sign to the open door (P1's 13B sunrise plate, the sign lit at 6:00), while the colour floods top-down through the frame
// behind a soft travelling matte (~48 f, leading the tilt) over the same plate drained grey (1H's end look); no floor flicker, no tail blob.
// Then on 51 a push-through (same downward speed) into her pushing the boxes out through the door (cut 6's 13B_push).
export const STREET13B = { whole: has('c7/street/p2/13B_whole.jpg') ? 'c7/street/p2/13B_whole.jpg' : 'c7/street/13B_whole.jpg', push: 'c5/13B/13B_push.jpg' };   // rl7_p2's toned-down roof sign
const GREY = 'grayscale(0.94) brightness(0.74) contrast(0.92)';
const ez = (t: number) => (t <= 0 ? 0 : t >= 1 ? 1 : 0.5 - 0.5 * Math.cos(Math.PI * t));
const SIGN13 = { x: 1280, y: 54, rx: 330, ry: 120 };   // stage px: the roof sign (letters 1064-1495 x 18-90) + its glow, a feathered ellipse
const Sunrise: ShotDef = { stage: () => {
  const f = useCurrentFrame(); const full = { position: 'absolute' as const, left: 0, top: 0, width: 2560, height: 1440 };
  const front = -160 + 1800 * ez(f / 48), soft = 170;
  const m = `linear-gradient(180deg, #000 0px, #000 ${(front - soft).toFixed(0)}px, transparent ${(front + soft).toFixed(0)}px, transparent 1440px)`;
  const sign = f < 2 ? 0 : f < 6 ? [0.35, 0.1, 0.85, 0.5][f - 2] : 1;
  return (
    <AbsoluteFill>
      <Img src={staticFile(STREET13B.whole)} style={{ ...full, filter: GREY }} />
      <Img src={staticFile(STREET13B.whole)} style={{ ...full, WebkitMaskImage: m, maskImage: m, WebkitMaskSize: '2560px 1440px', maskSize: '2560px 1440px' }} />
      {sign > 0.01 ? (() => { const sm = `radial-gradient(ellipse ${SIGN13.rx}px ${SIGN13.ry}px at ${SIGN13.x}px ${SIGN13.y}px, #000 55%, transparent 100%)`;
        return <Img src={staticFile(STREET13B.whole)} style={{ ...full, opacity: sign, WebkitMaskImage: sm, maskImage: sm, WebkitMaskSize: '2560px 1440px', maskSize: '2560px 1440px', WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat' }} />; })() : null}
    </AbsoluteFill>); } };
const B59: ShotDef = rigs([
  { at: 0, inner: Sunrise, keys: [{ f: 0, cx: 1280, cy: 720 / 2.1, s: 2.1 }, { f: 14, cx: 1280, cy: 720 / 2.02 + 20, s: 2.02 }, { f: 50, cx: 1280, cy: 1440 - 720 / 1.66, s: 1.66 }], opt: { v1: { cy: 9, s: L(3) } } },   // ~0.5 s close on the lit roof sign, then tilt down + pull out to the door
  { at: 51, keys: [{ f: 0, cx: 1280, cy: 660, s: 1.06 }, { f: d('B59') - 52, cx: 1280, cy: 740, s: 1.12 }], opt: { v0: { cy: 5, s: L(4) } }, plate: { src: STREET13B.push }, grain: true },
]);
// B60 (6254-6358) FLOW: she's inside, coffee; he tips his head at the glass -> push-through at 6323 down to the brass plate GLASSES OF WATER 1
const B60: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1280, cy: 720, s: 1.03 }, { f: 68, cx: 1280, cy: 780, s: 1.14 }], opt: { v1: { s: L(5), cy: 1.4 } } },
  { at: 69, keys: [{ f: 0, cx: 1280, cy: 690, s: 1.03 }, { f: d('B60') - 70, cx: 1280, cy: 730, s: 1.12 }], opt: { v0: { s: L(5), cy: 1.2 } } },
]);
// B61 (6358-6598) FLOW: the tag (cut 6 13E: he stamps RETIREMENT -> her laptop, her first prompt "make me MORE famous" (the MAKE ME FAMOUS
// ticket of H7.10 paid off on her screen) -> the pull-back, the cat flops, the lid -> top-down on the shut lid with the RATE LIMITED card).
// W11: the stamp beat framed RIGHT (no blank-door third). C10: after the lid shuts, "Subscribe for the next song" fades in above the laptop
// (her brand type, 52 px, a plain dark pill, no logos) and stays to the end; the last 5 s are calm for YouTube's end-screen elements.
const SUB_AT = T13.top + 10;   // shot frames (13E starts at the block start)
const Subscribe: React.FC<{ f: number }> = ({ f }) => {
  const k = Math.min(1, Math.max(0, (f - SUB_AT) / 14)); if (k <= 0) return null; const e = 1 - Math.pow(1 - k, 3);
  return <><div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 560, opacity: e, background: 'linear-gradient(180deg, rgba(8,8,10,0.72) 0%, rgba(8,8,10,0.45) 45%, rgba(8,8,10,0) 100%)' }} />
    <div style={{ position: 'absolute', left: 0, right: 0, top: 170, display: 'flex', justifyContent: 'center', opacity: e, transform: `translateY(${(1 - e) * 16}px)` }}>
    <div data-fit="box" style={{ padding: '22px 54px', borderRadius: 999, background: 'rgba(14,14,16,0.82)', boxShadow: '0 10px 40px rgba(0,0,0,0.45)', border: '2px solid rgba(236,230,216,0.18)' }}>
      <span style={{ fontFamily: FONT.brand, fontSize: 64, letterSpacing: '0.02em', color: 'rgb(236,230,216)', whiteSpace: 'nowrap' }}>SUBSCRIBE FOR THE <span style={{ color: 'rgb(116,227,106)' }}>NEXT SONG</span></span>
    </div></div></>;
};
void Subscribe;
const B61: ShotDef = rigs([
  { at: 0, keys: [{ f: 0, cx: 1420, cy: 760, s: 1.1 }, { f: 65, cx: 1440, cy: 790, s: 1.16 }], opt: { v1: { s: L(2) } } },   // rl7_master: no in-film subscribe pill (her call Thu 23:12: films clean)
  // the laptop (66-120: cut 6 crept 1.5 %/s: 33% still) pushes 2.5 %/s, then gives it back as cut 6's own pull-back runs (120-138)
  { at: 66, keys: [{ f: 0, cx: 1280, cy: 720, s: 1.0 }, { f: 54, cx: 1310, cy: 735, s: 1.11 }, { f: 72, cx: 1280, cy: 720, s: 1.01 }, { f: d('B61') - 67, cx: 1280, cy: 720, s: 1.04 }], },
]);

export const B12: Record<string, ShotDef> = { B53, B54, B55, B56, B57, B58, B59, B60, B61 };
