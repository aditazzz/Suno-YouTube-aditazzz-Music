// Cut 7 section 9 (the bridge), blocks B42-B47 (PLAN7 §1; rl7_rb). Lane H's plates (rl7_hero PATCH.md): 9A layer pack (robe + collagen mask,
// bigger TV, decor back, the plate's display pod), 9E1 re-animated (69 rendered frames, her approved a_9E1), 9E2 + 9G in the robe.
// APARTMENT PLATES: the finals lane re-renders these in the re-dressed room with the new sign; every path is one line in APT9 below.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../../types';
import { rig, rigs, pushKeys } from '../kit/rig';
import { Glow, blinkAmt } from '../kit/life';
import { VisorSweep } from '../kit/sets';
import { block } from '../kit/blocks';
import { Grain2 } from '../../../blocks/real/Scene';
import { VacuumNotif } from '../../c5/Notif';
import { VACUUM } from '../../../blocks/real/script';
import { F } from '../../../blocks/real/tokens';
import { pop } from '../../c5/kit';
import LA from '../../../../public/c7/9A/layout.json';

const L = (pct: number) => Math.log(1 + pct / 100) / 30;
const d = (id: string) => block(id).dur;
export const APT9 = {
  a: 'c7/9A/9A.jpg', fg: 'c7/9A/9A_fg.png', coop: 'c7/9A/9A_coop.png', hair: 'c7/9A/9A_hair.png', blink: 'c7/9A/9A_blink.png', blinkHalf: 'c7/9A/9A_blink_half.png',
  e1: (r: number) => `c7/9E1/f_${String(Math.max(0, Math.min(68, r))).padStart(4, '0')}.jpg`,
  e2: 'c7/9E2/9E2.jpg',
  g: (f: number) => (f < 17 ? 'c7/9G/9G_sign_Not_Mad.jpg' : f < 26 ? 'c7/9G/9G_sign_Cool.jpg' : f < 34 ? 'c7/9G/9G_sign_Cool_Cool.jpg' : 'c7/9G/9G.jpg'),
};
const full: React.CSSProperties = { position: 'absolute', left: 0, top: 0, width: 2560, height: 1440 };

// --- B42 (4246-4385) FLOW: 9A, wide -> push to medium-wide. The vibration plate visibly GOES: her + the plate buzz (2.6-3.8 px, up a notch on
// each "I'm not mad" 4288 / 4329), Cooper on his own phase (worried, a smaller lagged buzz), her curls + pom-pom on a lag; she blinks (the
// eyes-closed patch rides the buzzing her-layer); the plate's display pod meter flickers in the red. No NewsTV overlay (the plate's TV is big
// and lit: rl7_hero's call, W12/H7.29 answered by the 1.3x TV).
const jig = (g: number, amp: number, lag = 0, hz = 13.5) => { const ph = 2 * Math.PI * hz * (g / 30) - lag; return [amp * 0.35 * Math.sin(ph * 0.5 + 1.1), amp * Math.sin(ph)]; };
const Buzz: React.FC<{ g: number; amp: number; lag?: number; hz?: number; children: React.ReactNode }> = ({ g, amp, lag = 0, hz, children }) => (
  <>{[0, 1, 2].map((i) => { const [dx, dy] = jig(g + (i / 2 - 0.5) * 0.45, amp, lag, hz);
    return <div key={i} style={{ ...full, opacity: [1, 0.5, 0.33][i], transform: `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)` }}>{children}</div>; })}</>
);
const [bx0, by0, bx1, by1] = LA.blink_box as number[];
const Blink9: React.FC<{ g: number }> = ({ g }) => { const a = blinkAmt(g, 9, [4288, 4329]); if (a < 0.05) return null;
  return <Img src={staticFile(a > 0.7 ? APT9.blink : APT9.blinkHalf)} style={{ position: 'absolute', left: bx0, top: by0, width: bx1 - bx0, height: by1 - by0 }} />; };
const N9A: ShotDef = { stage: ({ shot }: ShotProps) => {
  const f = useCurrentFrame(); const g = shot.from + f; const amp = g >= 4329 ? 3.8 : g >= 4288 ? 3.2 : 2.6;
  const [px, py] = LA.pod_px as number[];
  return (
    <AbsoluteFill>
      <Img src={staticFile(APT9.a)} style={full} />
      <Buzz g={g} amp={amp * 0.55} lag={0.9} hz={11}><Img src={staticFile(APT9.coop)} style={full} /></Buzz>
      <Buzz g={g} amp={amp}><Img src={staticFile(APT9.fg)} style={full} /><Blink9 g={g} />
        <Glow x={px} y={py} rx={60} ry={26} color="rgba(255,70,60,0.9)" op={0.25 + 0.2 * Math.abs(Math.sin(g * 1.7))} /></Buzz>
      <Buzz g={g} amp={amp * 1.45} lag={1.3}><Img src={staticFile(APT9.hair)} style={full} /></Buzz>
    </AbsoluteFill>); } };
// the LIVE LOVE / NOT MAD neon sits on the plate's left edge (the gag while she sings "I'm not mad"): the push keeps the left edge pinned
// (cx = 1280 / s) so the sign stays whole; the TV's right edge goes a little at the end
const B42: ShotDef = rig({ inner: N9A, keys: [{ f: 0, cx: 1280 / 1.005, cy: 730, s: 1.005 }, { f: 70, cx: 1280 / 1.04, cy: 750, s: 1.04 }, { f: d('B42') - 1, cx: 1280 / 1.075, cy: 768, s: 1.075 }],
  bumps: { at: [4288 - 4246, 4329 - 4246], amt: 0.008, len: 10 }, grain: true, screen: null });

// B43 (4385-4455) PUNCH: the stamped slip, push 5 %/s (the stamp lands on the beat in cut 6's own animation)
const B43: ShotDef = rig({ keys: pushKeys(d('B43'), { cx: 1280, cy: 720, s0: 1.03, pct: 5, dy: 10 }) });
// B44 (4455-4593) FLOW: low, following the roll, then a push into the PASTED grid so it reads big and holds >= 2 s (from ~4520)
const B44: ShotDef = rig({ keys: [{ f: 0, cx: 1280, cy: 720, s: 1.03 }, { f: 60, cx: 1290, cy: 760, s: 1.18 }, { f: d('B44') - 1, cx: 1300, cy: 790, s: 1.3 }] });

// --- B45 (4593-4732) FLOW, her P08 "Streamers coming out scene needs polishing": lane H's 9E1 (every frame rendered: the bursts at 4610 / 4626,
// Cooper launched and landing on the sofa, the ta-da), one slow push centred between her and Cooper (both stay whole), and at 4662 a
// matched-speed cut into 9E2 (same robe + mask, the party's paper lying in the room) carrying on toward the door. The VACUUM notification
// slides in on the cut and holds the whole of 9E2 (2.3 s), 1.15x bigger.
const E1: ShotDef = { stage: () => { const f = useCurrentFrame(); return <Img src={staticFile(APT9.e1(f))} style={full} />; } };
// rl7_final (judge nit B45: the centred banner landed on her head and hid NOT, so the neon read "MAD"): a compact two-line banner in the
// top-left corner (over the clock + poster), clear of her head (x >= 700), the neon (x >= 1490) and the QUIET HOURS lettering (y >= 214)
const NW = 640, NX = 40, NY = 14;
const NotifCompact: React.FC<{ f: number; at: number }> = ({ f, at }) => {
  if (f < at) return null;
  const k = Math.min(1.08, Math.max(0, pop(f, at, 10)));
  const words = VACUUM.body.split(' '); const l1 = words.slice(0, 3).join(' '), l2 = words.slice(3).join(' ');
  return (
    <div data-fit="notif45" style={{ position: 'absolute', left: NX, top: NY, width: NW, transform: `translateY(${((k - 1) * 240).toFixed(1)}px)`, opacity: Math.min(1, k * 3),
      borderRadius: 44, background: 'rgba(246,244,240,0.88)', backdropFilter: 'blur(30px)', boxShadow: '0 16px 44px rgba(0,0,0,0.35)', padding: '18px 26px',
      display: 'flex', alignItems: 'center', gap: 20, fontFamily: F.ios, boxSizing: 'border-box' }}>
      <div style={{ width: 78, height: 78, borderRadius: 19, background: 'linear-gradient(160deg,#5b6370,#2d323a)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width={56} height={56} viewBox="0 0 80 80"><circle cx={40} cy={40} r={32} fill="#E9ECF0" /><circle cx={40} cy={40} r={22} fill="none" stroke="#9aa3ad" strokeWidth={4} />
          <circle cx={40} cy={22} r={6} fill="#2d323a" /><path d="M14 52 Q40 66 66 52" fill="none" stroke="#9aa3ad" strokeWidth={4} /></svg>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 16 }}>
          <span style={{ fontSize: 36, fontWeight: 700, letterSpacing: 1, color: '#1c1c1e' }}>{VACUUM.app}</span>
          <span style={{ fontSize: 36, color: '#6c6c70' }}>{VACUUM.when}</span>
        </div>
        <div style={{ fontSize: 48, lineHeight: '55px', fontWeight: 500, color: '#1c1c1e', marginTop: 2, whiteSpace: 'nowrap' }}>{l1}<br />{l2}</div>
      </div>
    </div>
  );
};
const NotifBig: React.FC<ShotProps> = ({ shot }) => { const f = useCurrentFrame(); return <div style={full}><NotifCompact f={f} at={4664 - shot.from} /></div>; };
void VacuumNotif;
const B45: ShotDef = rigs([
  { at: 0, inner: E1, keys: [{ f: 0, cx: 1120, cy: 750, s: 1.0 }, { f: 68, cx: 1100, cy: 770, s: 1.065 }], opt: { v1: { s: L(3), cx: -0.4 } }, grain: true, screen: NotifBig },
  { at: 69, keys: [{ f: 0, cx: 1240, cy: 740, s: 1.02 }, { f: d('B45') - 70, cx: 1150, cy: 760, s: 1.085 }], opt: { v0: { s: L(3), cx: -1 } },
    plate: { src: APT9.e2 }, grain: true, screen: NotifBig },
]);
// B46 (4732-4784) PUNCH: silence, flat-on, centred. Designed near-stop: a 1.8 %/s creep; the real Claude limit banner on the glass (cut 6),
// his visor glass alive (slow sweep)
const B46: ShotDef = rig({ keys: pushKeys(d('B46'), { cx: 1280, cy: 720, s0: 1.01, pct: 1.8, dy: -6 }),
  top: ({ abs }) => <VisorSweep abs={abs} x={1300} y={600} w={1300} h={520} seed={9} k={0.6} /> });   // his visor glass at 9F's s 2.9 framing (output px)
// B47 (4784-4836) PUNCH: reverse wide, drift; the neon goes Not Mad -> Cool (4801) -> Cool Cool (4810) -> Cool Cool Cool (4818): whole-frame
// state plates (lane H), a small push bump on each "cool"; she is still in the robe, mask peeled in her hand
// rl10_fix (her v3 note "~2:40 (B47): give the sign/top element proper top margin"): the plate has no headroom, so the drift also rises
// (cy 705 -> 668, the view's top edge stays inside the plate) and her neon is baked 45 px lower (9G plates _rl10); v3 keys: cy 720, dy 0
const B47: ShotDef = rig({ keys: pushKeys(d('B47'), { cx: 1300, cy: 705, s0: 1.03, pct: 3, dx: -40, dy: -37 }),
  bumps: { at: [17, 26, 34], amt: 0.007, len: 8 }, plate: { src: (f) => APT9.g(f) }, grain: true });

export const B9: Record<string, ShotDef> = { B42, B43, B44, B45, B46, B47 };
void Grain2;
