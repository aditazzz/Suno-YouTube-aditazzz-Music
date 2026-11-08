// ROUND 5 (k16_gym_selfie, CD, Nov 7 2026 ~20:45 PT). Her K16 note (round 4): "This should be a gym mirror selfie".
// K16 is now a LinkedIn VIDEO post in light mode: a timelapse mirror selfie. In the mirror, the Founder holds the selfie pose (phone up
// in his left hand, the approved tiny pink dumbbell curled in his right, F17M = F17A's phone arm + F17B's dumbbell arm, same rig).
// The gym's red LED wall timer above the mirror races 00:00 -> 40:00 on "gym" (local f18-38, the approved timing), while the other
// gym-goers streak past as timelapse blurs and he never moves: his 40 minutes were one mirror selfie. Approved gag kept: the caption
// "40 min. No days off. 💪", the pink dumbbells, the stopwatch (now the gym's interval timer, which IS a stopwatch), 40:00.
// Geometry: the reflection is the front still mirrored (his left hand shows on the image-left, as in a real mirror), the phone's BACK
// faces the mirror (lenses, no logo) and sits near the photo's optical centre; the timer is on the mirror wall, so it reads the right
// way round; the post's UI is never mirrored. Set dressing: CC0 Poly Haven rubber_tiles (floor), painted_concrete_02 (wall above the
// mirror), concrete_wall_006 (the far wall in the reflection); logged in assets/polyhaven/SOURCES.md.
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { lin } from './theme';
import { Canvas, Avatar } from './ui';
import { LiNight, LI, LT, Ico, LiAuthor, LiActions, LiCounts } from './li';

// deterministic hash for timelapse jitter
const hsh = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
// ---------------------------------------------------------------- the clock (local frames; unchanged from the approved gag)
// minutes from the approved roll (0 -> 40 over f18-38); the seconds spin while it races (a timelapse of a clock), landing on :00
const clock = (f: number) => { const s = lin(f, 18, 38, 0, 2400); const racing = f > 18 && f < 38; return { mm: Math.floor(s / 60), ss: racing ? Math.floor(hsh(f * 13) * 60) : Math.floor(s % 60) }; };
const LAPSE = (f: number) => f >= 18 && f < 38; // the timelapse stretch of the clip

// ---------------------------------------------------------------- 7-segment LED digits (a real gym interval timer)
const SEG: Record<string, string> = { '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg' };
const Digit: React.FC<{ ch: string; h: number; on: string; off: string }> = ({ ch, h, on, off }) => {
  // viewBox 56 x 100, slanted 0 (gym timers are upright); segment thickness 12
  const t = 12, w = 56, H2 = 50;
  const P: Record<string, string> = {
    a: `${t / 2 + 2},${t / 2} ${t + 2},0 ${w - t - 2},0 ${w - t / 2 - 2},${t / 2} ${w - t - 2},${t} ${t + 2},${t}`,
    g: `${t / 2 + 2},${H2} ${t + 2},${H2 - t / 2} ${w - t - 2},${H2 - t / 2} ${w - t / 2 - 2},${H2} ${w - t - 2},${H2 + t / 2} ${t + 2},${H2 + t / 2}`,
    d: `${t / 2 + 2},${100 - t / 2} ${t + 2},${100 - t} ${w - t - 2},${100 - t} ${w - t / 2 - 2},${100 - t / 2} ${w - t - 2},100 ${t + 2},100`,
    f: `${t / 2},${t / 2 + 2} ${t},${t + 2} ${t},${H2 - t / 2 - 2} ${t / 2},${H2 - 2} 0,${H2 - t / 2 - 2} 0,${t + 2}`,
    b: `${w - t / 2},${t / 2 + 2} ${w},${t + 2} ${w},${H2 - t / 2 - 2} ${w - t / 2},${H2 - 2} ${w - t},${H2 - t / 2 - 2} ${w - t},${t + 2}`,
    e: `${t / 2},${H2 + 2} ${t},${H2 + t / 2 + 2} ${t},${100 - t - 2} ${t / 2},${100 - t / 2 - 2} 0,${100 - t - 2} 0,${H2 + t / 2 + 2}`,
    c: `${w - t / 2},${H2 + 2} ${w},${H2 + t / 2 + 2} ${w},${100 - t - 2} ${w - t / 2},${100 - t / 2 - 2} ${w - t},${100 - t - 2} ${w - t},${H2 + t / 2 + 2}`,
  };
  const lit = SEG[ch] ?? '';
  return (
    <svg width={h * 0.56} height={h} viewBox="0 0 56 100" style={{ display: 'block', overflow: 'visible' }}>
      {Object.entries(P).map(([k, p]) => <polygon key={k} points={p} fill={lit.includes(k) ? on : off} />)}
    </svg>
  );
};
/** the wall-mounted LED timer: black box, red digits MM:SS, unlit segments faintly visible. Box size = f(dh). */
export const LedTimer: React.FC<{ f: number; dh: number; x: number; y: number }> = ({ f, dh, x, y }) => {
  const { mm, ss } = clock(f);
  // "done" flash after it lands on 40:00 (f38): a dip at 41-42, full on from 43 (the approved key frame 44 is full on)
  const lvl = f >= 41 && f < 43 ? 0.42 : 1;
  const on = `rgba(255,${Math.round(46 + 10 * lvl)},${Math.round(34 + 8 * lvl)},${lvl})`, off = 'rgba(120,22,16,0.22)';
  const gap = dh * 0.16, pad = dh * 0.2, colW = dh * 0.26;
  const txt = String(mm).padStart(2, '0') + String(ss).padStart(2, '0');
  const bw = 4 * dh * 0.56 + 4 * gap + colW + 2 * pad, bh = dh + 2 * pad * 0.85;
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: bw, height: bh, borderRadius: dh * 0.07, background: 'linear-gradient(180deg,#151515,#070707)',
      boxShadow: `0 ${dh * 0.06}px ${dh * 0.12}px rgba(0,0,0,.55), inset 0 0 0 ${Math.max(3, dh * 0.025)}px #262626`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap }}>
      <Digit ch={txt[0]} h={dh} on={on} off={off} /><Digit ch={txt[1]} h={dh} on={on} off={off} />
      <svg width={colW} height={dh} viewBox="0 0 26 100" style={{ display: 'block' }}><rect x="6" y="27" width="14" height="14" fill={on} /><rect x="6" y="61" width="14" height="14" fill={on} /></svg>
      <Digit ch={txt[2]} h={dh} on={on} off={off} /><Digit ch={txt[3]} h={dh} on={on} off={off} />
      {/* the LED face's soft light on its own bezel only (it is a light; no bloom on the frame) */}
      <div style={{ position: 'absolute', inset: 0, borderRadius: dh * 0.07, boxShadow: `inset 0 0 ${dh * 0.25}px rgba(255,40,20,${0.10 * lvl})`, pointerEvents: 'none' }} />
    </div>
  );
};
export const ledBox = (dh: number) => ({ w: 4 * dh * 0.56 + 4 * dh * 0.16 + dh * 0.26 + 2 * dh * 0.2, h: dh + 2 * dh * 0.2 * 0.85 });

// ---------------------------------------------------------------- timelapse ghosts: other gym-goers as horizontal streaks
const Ghost: React.FC<{ x: number; y: number; h: number; tone: string; o: number; blur: number; id: string }> = ({ x, y, h, tone, o, blur, id }) => (
  <svg style={{ position: 'absolute', left: x - h * 0.6, top: y, width: h * 1.2, height: h, overflow: 'visible', opacity: o }} viewBox="0 0 120 100" preserveAspectRatio="none">
    <defs><filter id={id} x="-60%" y="-20%" width="220%" height="140%"><feGaussianBlur stdDeviation={`${blur} ${blur * 0.18}`} /></filter></defs>
    <g filter={`url(#${id})`} fill={tone}>
      <ellipse cx="60" cy="10" rx="7" ry="8.5" /><path d="M44 22 Q60 16 76 22 L80 58 L70 58 L69 100 L52 100 L50 58 L40 58Z" />
    </g>
  </svg>
);

// ---------------------------------------------------------------- the photo/video: a gym mirror wall
type GymP = { f: number; w: number; h: number; band: number; dh: number; ledX: number; ledY: number; fh: number; phoneX: number; headY: number };
const STW = 1800, STH = 2400, PHX = 1690, HEADY = 247; // F17M still size; phone centre x and head top in still px (unflipped)
export const GymMirror: React.FC<GymP> = ({ f, w, h, band, dh, ledX, ledY, fh, phoneX, headY }) => {
  const sc = fh / STH, fw = STW * sc;
  // flipped still: still x -> left + (STW - x) * sc ; put the phone at phoneX
  const left = phoneX - (STW - PHX) * sc, top = headY - HEADY * sc;
  const lapse = LAPSE(f); const step = Math.floor(f / 2);
  const jx = lapse ? (hsh(step) - 0.5) * 6 : 0, jy = lapse ? (hsh(step + 9) - 0.5) * 4 : 0, jb = lapse ? 1 + (hsh(step + 3) - 0.5) * 0.07 : 1;
  const mh = h - band; // mirror height
  // ghosts: 3 people crossing at timelapse speed, re-seeded every 2 frames
  const ghosts = lapse ? [0, 1, 2].map((i) => ({ x: w * (0.08 + 0.84 * hsh(step * 3 + i * 17)), s: 0.78 + 0.3 * hsh(step + i * 5), tone: ['#C9CDD2', '#5E8CA6', '#B9A68E'][i], o: 0.38 + 0.2 * hsh(step * 7 + i) })) : [];
  const rackY = band + mh * 0.50, rackH = mh * 0.30;
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', background: '#2A2C30' }}>
      {/* the real wall above the mirror (painted concrete, lit from the ceiling) */}
      <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: band, backgroundImage: `url(${staticFile('gym/wall.jpg')})`, backgroundSize: '520px 520px', filter: 'grayscale(.6) brightness(.62) contrast(1.05)' }} />
      <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: band, background: 'linear-gradient(180deg,rgba(255,236,210,.10),rgba(0,0,0,.18))' }} />
      <LedTimer f={f} dh={dh} x={ledX} y={ledY} />
      {/* ---- the mirror: the room behind the camera, reflected ---- */}
      <div style={{ position: 'absolute', left: 0, top: band, width: w, height: mh, overflow: 'hidden' }}>
        {/* far wall */}
        <div style={{ position: 'absolute', inset: 0, backgroundImage: `url(${staticFile('gym/block.jpg')})`, backgroundSize: '460px 460px', filter: 'grayscale(.7) brightness(.50)' }} />
        {/* ceiling strip + linear pendant lights (real sources) */}
        <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: mh * 0.16, background: 'linear-gradient(180deg,#141518,#202226)' }} />
        {[0.12, 0.42, 0.72].map((p, i) => <div key={i} style={{ position: 'absolute', left: w * p, top: mh * 0.06, width: w * 0.2, height: Math.max(8, mh * 0.022), borderRadius: 6, background: '#FFF4E2', boxShadow: '0 0 18px rgba(255,236,205,.55)' }} />)}
        {/* warm light pooling on the far wall under the pendants */}
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 60% 55% at 45% 20%, rgba(255,232,200,.16), rgba(0,0,0,0) 70%)' }} />
        {/* rubber floor */}
        <div style={{ position: 'absolute', left: 0, top: mh * 0.80, width: w, height: mh * 0.2, backgroundImage: `url(${staticFile('gym/rubber.jpg')})`, backgroundSize: '300px 300px', filter: 'brightness(.62)' }} />
        <div style={{ position: 'absolute', left: 0, top: mh * 0.80, width: w, height: mh * 0.2, background: 'linear-gradient(180deg,rgba(0,0,0,.35),rgba(0,0,0,0) 40%)' }} />
        {/* the dumbbell rack behind him: real, heavy, black */}
        <svg style={{ position: 'absolute', left: 0, top: rackY - band, width: w, height: rackH }} viewBox={`0 0 ${w} 100`} preserveAspectRatio="none">
          <rect x={w * 0.02} y="30" width={w * 0.96} height="6" fill="#3B3E43" /><rect x={w * 0.02} y="78" width={w * 0.96} height="6" fill="#3B3E43" />
          {Array.from({ length: Math.floor(w / 92) }).map((_, i) => { const cx = w * 0.04 + i * 92; return (
            <g key={i}><rect x={cx - 30} y="8" width="18" height="24" rx="3" fill="#111214" /><rect x={cx + 12} y="8" width="18" height="24" rx="3" fill="#111214" /><rect x={cx - 12} y="17" width="24" height="5" fill="#9A9EA4" />
              <rect x={cx - 32} y="54" width="20" height="26" rx="3" fill="#0E0F11" /><rect x={cx + 12} y="54" width="20" height="26" rx="3" fill="#0E0F11" /><rect x={cx - 12} y="64" width="24" height="5" fill="#9A9EA4" /></g>); })}
        </svg>
        {/* timelapse ghosts (behind him) */}
        {ghosts.map((g, i) => <Ghost key={i} id={`gh${i}`} x={g.x} y={mh * (0.98 - 0.84 * g.s)} h={mh * 0.84 * g.s} tone={g.tone} o={g.o} blur={5} />)}
        {/* him: the front still mirrored = his reflection; the phone's back (lenses) faces the mirror */}
        <div style={{ position: 'absolute', left: left + jx, top: top - band + jy, width: fw, height: fh, transform: 'scaleX(-1)', filter: `drop-shadow(0 ${fh * 0.02}px ${fh * 0.03}px rgba(0,0,0,.35)) brightness(${jb})` }}>
          <Img src={staticFile('stills/F17M.png')} style={{ width: fw, height: fh, display: 'block' }} />
          <svg style={{ position: 'absolute', left: 0, top: 0, width: fw, height: fh }} viewBox={`0 0 ${STW} ${STH}`}>
            {/* phone back: graphite case tone over the slab's free column + a lens module (no logo) */}
            <rect x="1699" y="890" width="46" height="96" rx="12" fill="#1E2024" />
            <circle cx="1722" cy="914" r="13" fill="#0A0B0D" stroke="#5B6068" strokeWidth="3.5" /><circle cx="1722" cy="956" r="13" fill="#0A0B0D" stroke="#5B6068" strokeWidth="3.5" />
            <circle cx="1722" cy="935" r="4" fill="#E9E2CF" />
          </svg>
        </div>
        {/* the phone's torch in the glass: the mirror-selfie tell (a real light, so it may flare); sits on the lens */}
        <div style={{ position: 'absolute', left: phoneX - 32 * sc + jx - fh * 0.16, top: top - band + jy + 935 * sc - fh * 0.16, width: fh * 0.32, height: fh * 0.32, borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,255,250,.95) 0%, rgba(255,255,245,.75) 5%, rgba(255,250,235,.22) 16%, rgba(255,245,225,.06) 38%, rgba(255,245,225,0) 70%)', mixBlendMode: 'screen' }} />
        {/* mirror panel seams (gym mirrors are panels): a dark joint with a bright bevel edge */}
        {[0.31, 0.97].map((p, i) => <div key={i} style={{ position: 'absolute', left: w * p, top: 0, width: 5, height: mh, background: 'linear-gradient(90deg,rgba(0,0,0,.55),rgba(0,0,0,.55) 60%,rgba(255,255,255,.22))' }} />)}
        {/* mirror glass: a faint cool cast, a diagonal sheen and two smudges (it's a gym mirror) */}
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(115deg, rgba(220,240,240,0) 30%, rgba(220,240,240,.07) 42%, rgba(220,240,240,0) 52%), rgba(200,225,225,.04)' }} />
        <div style={{ position: 'absolute', left: w * 0.12, top: mh * 0.30, width: w * 0.07, height: mh * 0.12, borderRadius: '50%', background: 'radial-gradient(rgba(255,255,255,.06),rgba(255,255,255,0) 70%)' }} />
      </div>
      {/* mirror frame: black aluminium top rail */}
      <div style={{ position: 'absolute', left: 0, top: band - 10, width: w, height: 14, background: 'linear-gradient(180deg,#2D2F33,#0D0E10)' }} />
      {/* LinkedIn's inline video chrome: progress bar + the muted-speaker button */}
      <div data-fit="off" style={{ position: 'absolute', left: 0, bottom: 0, width: w, height: 10, background: 'rgba(255,255,255,.28)' }}><div style={{ width: `${Math.min(100, (f / 50) * 100)}%`, height: '100%', background: '#FFFFFF' }} /></div>
      <div data-fit="off" style={{ position: 'absolute', right: 36, bottom: 40, width: 96, height: 96, borderRadius: 48, background: 'rgba(0,0,0,.6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width="54" height="54" viewBox="0 0 24 24"><path d="M4 9h4l5-4v14l-5-4H4z" fill="#fff" /><path d="M16 9l5 6M21 9l-5 6" stroke="#fff" strokeWidth="2" strokeLinecap="round" /></svg>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- 16:9: the feed post (desktop, light mode), K07's card geometry, wider media
export const K16: React.FC = () => {
  const f = useCurrentFrame();
  const PX = 530, PW = 1500, MH = 740; const dh = 172; const lb = ledBox(dh);
  return (
    <Canvas bg={LI.canvas}>
      <div style={{ position: 'absolute', left: PX, top: 40, width: PW, height: 1360, borderRadius: 24, background: LI.card, overflow: 'hidden', boxShadow: LI.cardShadow }}>
        <div style={{ position: 'absolute', left: 56, top: 40 }}><LiAuthor avatar={<Avatar id="F01" size={150} bg={LI.card2} />} name="The Founder" headline="Founder · Visionary · Thought leader" when="3h" /></div>
        <div style={{ position: 'absolute', right: 56, top: 56 }}>{Ico.dots({ s: 70 })}</div>
        <div style={{ position: 'absolute', left: 56, top: 312 }}><LT cap={56}>40 min. No days off. 💪</LT></div>
        <div style={{ position: 'absolute', left: 0, top: 410, width: PW, height: MH, overflow: 'hidden' }}>
          <GymMirror f={f} w={PW} h={MH} band={250} dh={dh} ledX={96} ledY={(250 - lb.h) / 2 - 2} fh={1150} phoneX={660} headY={262} />
        </div>
        <div style={{ position: 'absolute', left: 56, top: 1172 }}><LiCounts w={PW - 112} n="12,431" comments="418 comments · 37 reposts" /></div>
        <div style={{ position: 'absolute', left: 56, right: 56, top: 1246, height: 2, background: LI.line }} />
        <div style={{ position: 'absolute', left: 0, top: 1256, width: PW, height: 96, display: 'flex', alignItems: 'center' }}><LiActions w={PW} /></div>
      </div>
      <LiNight />
    </Canvas>
  );
};

// ---------------------------------------------------------------- 9:16: the same post in the phone app (1080 x 1920); actions run below the frame
export const K16V: React.FC = () => {
  const f = useCurrentFrame();
  const MT = 560, MW = 1080, MHV = 1350; const dh = 190; const lb = ledBox(dh);
  return (
    <Canvas bg={LI.canvas}>
      <div style={{ position: 'absolute', left: 0, top: 236, width: 1080, height: 1800, background: LI.card }}>
        <div style={{ position: 'absolute', left: 100, top: 40, display: 'flex', gap: 26, alignItems: 'center' }}>
          <div style={{ width: 118, height: 118, borderRadius: '50%', overflow: 'hidden', flex: 'none' }}><Avatar id="F01" size={118} bg={LI.card2} /></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <LT cap={36} w={600}>The Founder</LT>
            <LT cap={28} c={LI.sub}>Founder · Visionary · Thought leader</LT>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><LT cap={28} c={LI.sub}>3h ·</LT>{Ico.globe({ s: 36 })}</div>
          </div>
        </div>
        <div style={{ position: 'absolute', left: 100, top: 214 }}><LT cap={40}>40 min. No days off. 💪</LT></div>
        <div style={{ position: 'absolute', left: 0, top: MT - 236, width: MW, height: MHV, overflow: 'hidden' }}>
          <GymMirror f={f} w={MW} h={MHV} band={300} dh={dh} ledX={(MW - lb.w) / 2} ledY={(300 - lb.h) / 2 + 6} fh={1200} phoneX={260} headY={360} />
        </div>
      </div>
      <LiNight />
    </Canvas>
  );
};
