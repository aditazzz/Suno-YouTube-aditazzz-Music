import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { C, D, F, W, H, fsForCap, ease, pop, lin, fmt } from './theme';
import { NightBg, Canvas, Founder, Avatar, T, Abs, Bezel, Card, Caret, Mark, Heart } from './ui';
import { Skyline, Sky, Sun } from './scenes';

// ---------------------------------------------------------------- K01 commit review screen (in-world family, with the founder avatar)
export const K01: React.FC = () => {
  const f = useCurrentFrame(); const msg = 'trust me'; const n = Math.round(lin(f, 12, 38, 0, msg.length));
  return (
    <Canvas bg="#000"><Bezel>
      <div style={{ position: 'absolute', inset: 0, background: '#0D1117' }} />
      <Abs x={160} y={150} style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
        <T cap={48} c="#9AA4B2" style={{ fontFamily: F.mono }}>review / main</T>
        <T cap={48} c="#5C6672">›</T><T cap={48} c="#E6EDF3" style={{ fontFamily: F.mono }}>commit 5eeyah1</T>
      </Abs>
      <Abs x={160} y={300} w={2160} h={250} style={{ display: 'flex', alignItems: 'center', gap: 56, background: '#161B22', borderRadius: 28, padding: '0 64px', border: '3px solid #2A313B', boxSizing: 'border-box' }}>
        <Avatar id="F01" size={170} ring="#2A313B" />
        <T cap={56} c="#E6EDF3">@founder</T>
        <T cap={48} c="#8B96A5" w={500}>committed 3 years ago</T>
      </Abs>
      <Abs x={160} y={620} w={2240} h={400} style={{ background: '#0B0E13', border: `4px solid ${C.amber}`, borderRadius: 28, boxSizing: 'border-box', padding: '0 80px', display: 'flex', alignItems: 'center' }}>
        <div style={{ fontFamily: F.mono, fontWeight: 700, fontSize: fsForCap(98, 'mono'), color: '#F2EBDD', letterSpacing: 2 }}>{msg.slice(0, n)}<Caret f={f} h={fsForCap(98, 'mono') * 0.95} /></div>
      </Abs>
      <Abs x={160} y={1100} style={{ fontFamily: F.mono, fontWeight: 700, fontSize: fsForCap(50, 'mono'), color: '#C9D1D9' }}>
        <span style={{ color: C.amber }}>+1,204</span> <span style={{ color: '#8B96A5' }}>-0</span>   ·   312 files changed
      </Abs>
    </Bezel></Canvas>
  );
};

// ---------------------------------------------------------------- K02 lobby portrait (3:4 print, 2400x3200)
// K02 print bg: ultraviolet -> charcoal (founder_print, director call Sat Nov 7 20:55; recolor_stills transform hue 218, S x0.32, V x0.50 = the 3D post fix finish/qa/founder_clothes/fix_founder.py; was #6B3FD8/#2B0F73/#9B72FF/#5A2CC0)
export const K02: React.FC = () => (
  <Canvas bg="#2A2420">
    <div style={{ position: 'absolute', inset: 90, background: 'linear-gradient(160deg,#545C6C,#2A2F3A)', boxShadow: 'inset 0 0 0 26px #C9A24A, inset 0 0 0 36px #6B4F14, 0 40px 120px rgba(0,0,0,.6)' }} />
    <div style={{ position: 'absolute', left: 210, top: 210, right: 210, bottom: 520, overflow: 'hidden', background: 'radial-gradient(circle at 50% 38%, #697180 0%, #485160 55%, #2A2F3A 100%)' }}>
      <Founder id="F30" h={2300} x={990} y={170} />
    </div>
    <div style={{ position: 'absolute', left: 640, bottom: 150, width: 1120, height: 190, background: 'linear-gradient(180deg,#E3C26A,#A8812C)', borderRadius: 10, boxShadow: '0 6px 0 #6B4F14', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ fontFamily: F.corm, fontWeight: 700, fontSize: 84, letterSpacing: 8, color: '#3A2A08', whiteSpace: 'nowrap' }}>THE VISIONARY</div>
    </div>
  </Canvas>
);

// ---------------------------------------------------------------- K04 call grid (boardroom screen texture)
const TILES = [['CV', 'Chief Vision Officer'], ['VS', 'VP, Synergy'], ['HV', 'Head of Vibes'], ['BO', 'Board Observer'], ['F', 'Founder (away)']];
export const K04: React.FC = () => {
  const f = useCurrentFrame(); const t0 = 1448 - 1381;
  const gone = (i: number) => f >= t0 + i * 8 + 4;
  const nGone = TILES.filter((_, i) => gone(i)).length;
  const toastI = Math.min(4, Math.max(0, Math.floor((f - t0) / 8)));
  const toast = f >= t0 && f < t0 + 5 * 8 + 6;
  const solo = ease(f, t0 + 40, 112 - 0);
  return (
    <Canvas bg="#0F1014">
      <Abs x={90} y={44} style={{ display: 'flex', alignItems: 'baseline', gap: 36 }}><T cap={52} c="#E9E7EF">Q3 STRATEGY</T><T cap={46} c="#8B8798" w={500}>· 6 participants</T></Abs>
      {TILES.concat([['C', 'Claude']]).map(([ini, name], i) => {
        const isC = i === 5; const col = i % 3, row = Math.floor(i / 3);
        const tw = 800, th = 560;
        const idx = TILES.filter((_, k) => !gone(k));
        const posIdx = isC ? idx.length : idx.findIndex((_, k) => TILES.indexOf(idx[k]) === i);
        if (!isC && gone(i)) return null;
        const p = isC ? idx.length : posIdx;
        const x = 90 + (p % 3) * (tw + 40), y = 170 + Math.floor(p / 3) * (th + 40);
        const full = isC ? solo : 0;
        const X = x + (0 - x) * full, Y = y + (0 - Y0(full, y)) * 0;
        return (
          <div key={i} style={{ position: 'absolute', left: X, top: y + (0 - y) * full, width: tw + (W - tw) * full, height: th + (H - th) * full, borderRadius: 34 * (1 - full), overflow: 'hidden', background: isC ? 'radial-gradient(circle at 50% 40%,#FFD9A0,#C77A3A 70%,#6B3A1A)' : '#23242C', border: isC ? `6px solid ${C.claude}` : '0' }}>
            {isC ? <Img src={staticFile('stills/CLAUDE_face_b.png')} style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 6%' }} /> : (<>
              <div style={{ position: 'absolute', left: '50%', top: '42%', transform: 'translate(-50%,-50%)', width: 220, height: 220, borderRadius: '50%', background: '#3A3B47', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {i === 4 ? <Avatar id="F01" size={90} ring="#3A3B47" style={{ position: 'absolute', right: -6, bottom: -6 }} /> : null}
                <T cap={84} c="#C9C6D6" fam="inter">{ini}</T></div></>)}
            <div style={{ position: 'absolute', left: 36 * (1 - full) + 60 * full, bottom: 32 + 40 * full, background: 'rgba(0,0,0,.55)', padding: '8px 26px', borderRadius: 16 }}><T cap={isC ? 46 + 10 * full : 46} c="#fff">{name}</T></div>
            {!isC && <div style={{ position: 'absolute', right: 30, top: 28, width: 70, height: 70, borderRadius: 35, background: '#5A1620', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><svg width="40" height="40" viewBox="0 0 24 24"><path d="M3 3l18 18M7 6v5a5 5 0 0 0 8 4M12 17v4" stroke="#FF8A9B" strokeWidth="2.4" fill="none" strokeLinecap="round" /></svg></div>}
          </div>
        );
      })}
      {toast && <Abs x={560} y={1290} w={1440} h={100} style={{ whiteSpace: 'nowrap', background: '#E9E7EF', borderRadius: 50, opacity: pop(f, t0 + toastI * 8, 6), transform: `translateY(${(1 - pop(f, t0 + toastI * 8, 6)) * 30}px)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><T cap={46} c="#14131A">{TILES[toastI][1]} left the meeting</T></Abs>}
    </Canvas>
  );
};
const Y0 = (_: number, y: number) => y;

// ---------------------------------------------------------------- K05 his story (2 segments)
const StoryShell: React.FC<{ seg: number; p: number; bgA: string; bgB: string; children: React.ReactNode; nm?: string }> = ({ seg, p, bgA, bgB, children }) => (
  <Canvas bg={bgA}>
    <NightBg />
    <div style={{ position: 'absolute', left: 3000 - 2300 + 0, top: 0 }} />
    <div style={{ position: 'absolute', left: (W - 810) / 2, top: 0, width: 810, height: H, background: '#000', borderRadius: 0, overflow: 'hidden', boxShadow: '0 0 120px rgba(0,0,0,.5)' }}>
      {children}
      <div style={{ position: 'absolute', left: 36, right: 36, top: 36, display: 'flex', gap: 12 }}>
        {[0, 1].map((s) => (<div key={s} style={{ flex: 1, height: 10, borderRadius: 5, background: 'rgba(255,255,255,.35)' }}><div style={{ width: `${(s < seg ? 1 : s === seg ? p : 0) * 100}%`, height: '100%', borderRadius: 5, background: '#fff' }} /></div>))}
      </div>
      <Abs x={36} y={70} style={{ display: 'flex', alignItems: 'center', gap: 20 }}><Avatar id="F01" size={84} ring="#fff" /><T cap={34} c="#fff" style={{ textShadow: '0 2px 10px rgba(0,0,0,.5)' }}>thefounder</T><T cap={34} c="#ffffffAA" w={500}>2h</T></Abs>
    </div>
  </Canvas>
);
export const K05: React.FC = () => {
  const f = useCurrentFrame(); const seg = f < 27 ? 0 : 1; const p = seg === 0 ? ease(f, 0, 27) : ease(f, 27, 54);
  const line = ease(f, 3, 18);
  return (
    <StoryShell seg={seg} p={p} bgA="#14171C" bgB={seg ? '#FFB3C7' : '#FFD27A'}>
      {seg === 0 ? (
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg,#22262C,#16191E)' }}>
          <svg style={{ position: 'absolute', left: 0, top: 240, width: 810, height: 800 }} viewBox="0 0 810 800">
            <rect x="0" y="0" width="810" height="800" fill="#1F2328" />
            {[0, 1, 2, 3].map((i) => <path key={i} d={`M0 ${120 + i * 190} H810`} stroke="#30353C" strokeWidth="6" />)}
            {[0, 1, 2].map((i) => <path key={i} d={`M${130 + i * 270} 0 V800`} stroke="#30353C" strokeWidth="6" />)}
            <path d="M0 620 C300 700 420 300 810 240" stroke="#4A5059" strokeWidth="46" fill="none" />
            <path d="M150 640 C300 560 400 360 640 280" stroke="#0A84FF" strokeWidth="14" fill="none" strokeDasharray="1 30" strokeLinecap="round" pathLength={1} style={{ strokeDasharray: `${line} 1` }} />
            <rect x="110" y="610" width="90" height="56" rx="14" fill="#3A3F47" /><text x="155" y="650" textAnchor="middle" fontFamily="Anton" fontSize="40" fill="#fff">HQ</text>
            <g transform={`translate(640 ${250 - (1 - pop(f, 14, 8)) * 60})`}><path d="M0 0 C-60 -70 -60 -150 0 -150 C60 -150 60 -70 0 0Z" fill={C.red} /><circle cx="0" cy="-100" r="22" fill="#fff" /></g>
            <rect x="500" y="300" width="270" height="76" rx="38" fill="#0A84FF" /><text x="635" y="353" textAnchor="middle" fontFamily="Anton" fontSize="52" fill="#fff" letterSpacing="3">AUSTIN</text>
          </svg>
          <Abs x={50} y={1100} w={710}><T cap={52} c="#fff" fam="inter" style={{ fontWeight: 600 }}>New chapter.</T><T cap={52} c="#fff" style={{ fontWeight: 600 }}>Austin, here I come.</T></Abs>
        </div>
      ) : (
        <div style={{ position: 'absolute', inset: 0 }}>
          <Sky a="#2E4A7A" b="#D98B6A" c="#FFC58A" /><Sun x={560} y={760} r={140} />
          <div style={{ position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, transform: `translateX(-810px)` }} />
          <Skyline y={1000} c1="#3A4A66" c2="#2B3850" />
          <div style={{ position: 'absolute', left: 0, right: 0, top: 1060, height: 20, background: '#222' }} />
          <Founder id="F05" h={900} x={330} y={1120} anchor="bottom" />
          <div style={{ position: 'absolute', left: 0, right: 0, top: 1070, height: 24, background: '#121419' }} /><div style={{ position: 'absolute', left: 0, right: 0, top: 1094, bottom: 0, background: '#1A1D24' }} />
        </div>
      )}
    </StoryShell>
  );
};

// ---------------------------------------------------------------- K06 balcony story, then podcast launch tile
export const K06: React.FC = () => {
  const f = useCurrentFrame(); const sw = f >= 80;
  const s = 0.9 + 0.1 * pop(f, 80, 10);
  if (!sw) return <K05Seg2 f={f} />;
  return (
    <Canvas bg="#2A1E1A">
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 40%,#D9A066,#4A2E2A 72%)' }} />
      <Card x={(W - 1100) / 2} y={170} w={1100} h={1100} r={44} bg="#FFE56B" style={{ transform: `scale(${s})`, transformOrigin: 'center' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(160deg,#FFE56B,#FF8FB8)' }} />
        <Founder id="F06" h={900} x={760} y={230} />
        <Abs x={60} y={70}><T cap={46} c="#1A1410" style={{ letterSpacing: 4 }}>NEW PODCAST</T></Abs>
        <Abs x={60} y={150} w={620}><T cap={118} fam="anton" c="#1A1410" style={{ lineHeight: 1.0 }}>EP. 1:</T><T cap={118} fam="anton" c="#fff" style={{ lineHeight: 1.0, WebkitTextStroke: '0px' }}>WHY I</T><T cap={118} fam="anton" c="#fff" style={{ lineHeight: 1.0 }}>LEFT</T></Abs>
      </Card>
      <Abs x={0} y={1296} w={W} style={{ textAlign: 'center' }}><T cap={52} c="#fff" style={{ textAlign: 'center' }}>Out now · wherever you listen</T></Abs>
    </Canvas>
  );
};
const K05Seg2: React.FC<{ f: number }> = ({ f }) => (
  <StoryShell seg={1} p={ease(f, 0, 80)} bgA="#14171C" bgB="#FFB3C7">
    <div style={{ position: 'absolute', inset: 0 }}><Sky a="#2E4A7A" b="#D98B6A" c="#FFC58A" /><Sun x={560} y={760} r={140} /><Skyline y={1000} c1="#3A4A66" c2="#2B3850" />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 1070, bottom: 0, background: '#1A1D24' }} />
      <Founder id="F05" h={900} x={330} y={1120} anchor="bottom" /></div>
  </StoryShell>
);

// ---------------------------------------------------------------- K07 selfie post

/** K07 background life: a far-off desert festival where a giant wooden man burns, tiny people dance, an art car rolls, sparks rise, flags flutter */
export const Burn: React.FC<{ f: number }> = ({ f }) => {
  const fl = (k: number) => 1 + 0.12 * Math.sin(f / 3 + k);
  return (
    <>
      <svg style={{ position: 'absolute', left: 0, top: 380, width: 1080, height: 420 }} viewBox="0 0 1080 420">
        <path d="M0 250 Q200 190 420 245 T800 230 T1080 250 V420 H0Z" fill="#B9763F" opacity=".55" />
        {[[60, 40, 2], [150, 70, 1], [900, 60, 2], [990, 90, 1], [800, 120, 1]].map(([x, y, k], i) => <g key={i} transform={`translate(${x} ${y + 190})`}><path d="M0 40 L34 0 L68 40Z" fill={['#3A8FB7', '#FF6FA8', '#FFB13B'][i % 3]} opacity=".85" /><rect x="26" y="26" width="16" height="14" fill="#2A1E14" /></g>)}
        <g transform="translate(300 100)">
          <rect x="62" y="150" width="36" height="140" fill="#5C3A1E" /><rect x="30" y="60" width="100" height="100" fill="#6B4424" />
          <rect x="52" y="0" width="56" height="60" fill="#6B4424" /><rect x="0" y="80" width="26" height="14" fill="#5C3A1E" /><rect x="134" y="80" width="26" height="14" fill="#5C3A1E" />
          <g transform={`translate(80 120) scale(${fl(0)} ${fl(1)}) translate(-80 -120)`}>
            <path d="M80 -40 Q130 40 120 120 Q100 90 80 130 Q60 90 40 120 Q30 40 80 -40Z" fill="#FF7A1A" opacity=".92" />
            <path d="M80 10 Q108 60 100 120 Q80 100 80 126 Q60 100 60 120 Q54 60 80 10Z" fill="#FFD84A" />
          </g>
        </g>
        {Array.from({ length: 14 }).map((_, i) => { const t = ((f * 3 + i * 31) % 220) / 220; return <circle key={i} cx={380 + Math.sin(i * 2 + f / 9) * 60 + (i % 3) * 22} cy={230 - t * 210} r={3 + (i % 3)} fill="#FFD84A" opacity={1 - t} />; })}
        {Array.from({ length: 9 }).map((_, i) => { const x = 40 + i * 118 + (i % 2) * 20; const hop = Math.abs(Math.sin(f / 4 + i)) * 12; const armUp = Math.sin(f / 3 + i) > 0; return <g key={i} transform={`translate(${x} ${330 - hop})`} fill="#2A1E14"><circle cx="0" cy="-34" r="9" /><rect x="-7" y="-24" width="14" height="30" rx="6" /><path d={armUp ? 'M-6 -20 L-22 -42 M6 -20 L22 -42' : 'M-6 -20 L-24 -6 M6 -20 L24 -6'} stroke="#3A1A6B" strokeWidth="6" strokeLinecap="round" fill="none" /><rect x="-6" y="6" width="5" height="22" /><rect x="1" y="6" width="5" height="22" /></g>; })}
        <g transform={`translate(${700 + ((f * 2) % 520) * 0.0} 300)`}>
          <rect x="0" y="-30" width="170" height="48" rx="18" fill="#FF6FA8" /><rect x="30" y="-62" width="90" height="36" rx="14" fill="#FFB13B" /><circle cx="34" cy="20" r="18" fill="#2A1E14" /><circle cx="140" cy="20" r="18" fill="#2A1E14" />
          {[0, 1, 2, 3, 4].map((i) => <circle key={i} cx={20 + i * 32} cy="-6" r="6" fill={Math.floor(f / 4 + i) % 2 ? '#fff' : '#7BFFD8'} />)}
        </g>
      </svg>
      <svg style={{ position: 'absolute', left: 0, top: 130, width: 1080, height: 120 }} viewBox="0 0 1080 120"><path d={`M0 20 Q270 ${70 + Math.sin(f / 5) * 8} 540 24 T1080 20`} stroke="#2A1E14" strokeWidth="4" fill="none" />
        {Array.from({ length: 11 }).map((_, i) => <path key={i} d={`M${i * 100 + 20} ${34 + Math.sin(i) * 10} l36 0 l-18 ${40 + Math.sin(f / 4 + i) * 6}Z`} fill={['#FF6FA8', '#FFD84A', '#6BD6FF', '#FFFFFF'][i % 4]} />)}</svg>
    </>
  );
};
/** K07 third eye: a huge glowing eye-in-triangle banner with a slowly turning mandala halo, behind the founder, above his head */
export const ThirdEye: React.FC<{ f: number }> = ({ f }) => {
  const blink = (f % 48) >= 44 ? 0.15 : 1; const glow = 0.75 + 0.25 * Math.sin(f / 6);
  return (
    <svg style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 980 }} viewBox="0 0 1080 980">
      <defs>
        <linearGradient id="teTri" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#FFE9A8" stopOpacity=".55" /><stop offset="1" stopColor="#FF6FA8" stopOpacity=".12" /></linearGradient>
        <radialGradient id="teHalo"><stop offset="0" stopColor="#FFF3C4" stopOpacity=".85" /><stop offset="1" stopColor="#FFF3C4" stopOpacity="0" /></radialGradient>
        <filter id="teGlow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6" /></filter>
      </defs>
      <circle cx="620" cy="340" r="420" fill="url(#teHalo)" opacity={0.5 * glow} />
      <g transform={`rotate(${f * 0.35} 620 340)`}>{Array.from({ length: 24 }).map((_, i) => <rect key={i} x="614" y="-380" width={i % 2 ? 8 : 14} height="720" fill="#FFE9A8" opacity={i % 2 ? 0.16 : 0.24} transform={`rotate(${i * 15} 620 340)`} />)}</g>
      <circle cx="620" cy="340" r="250" fill="none" stroke="#FFD84A" strokeWidth="4" opacity=".6" />
      <circle cx="620" cy="340" r="300" fill="none" stroke="#FF6FA8" strokeWidth="5" strokeDasharray="22 14" opacity=".6" transform={`rotate(${-f * 0.6} 620 340)`} />
      <circle cx="620" cy="340" r="360" fill="none" stroke="#FFF3C4" strokeWidth="4" strokeDasharray="3 16" strokeLinecap="round" opacity=".7" transform={`rotate(${f * 0.4} 620 340)`} />
      <polygon points="620,-70 1030,640 210,640" fill="url(#teTri)" stroke="#FFD84A" strokeWidth="8" strokeLinejoin="round" opacity={0.9} />
      <polygon points="620,-70 1030,640 210,640" fill="none" stroke="#FFE9A8" strokeWidth="14" strokeLinejoin="round" filter="url(#teGlow)" opacity={0.7 * glow} />
      <g transform="translate(620 150)">
        {Array.from({ length: 9 }).map((_, i) => { const a = (-80 + i * 20) * Math.PI / 180; return <line key={i} x1={Math.sin(a) * 118} y1={-Math.cos(a) * 80 - 14} x2={Math.sin(a) * 150} y2={-Math.cos(a) * 104 - 20} stroke="#FFD84A" strokeWidth="6" strokeLinecap="round" opacity={0.9} />; })}
        <g transform={`scale(1 ${blink})`}>
          <path d="M-92 0 Q0 -72 92 0 Q0 72 -92 0Z" fill="#FFFDF8" stroke="#2A1E14" strokeWidth="7" strokeLinejoin="round" />
          <circle cx="0" cy="0" r="38" fill="#2F7FB8" /><circle cx="0" cy="0" r="17" fill="#0E0E10" /><circle cx="-12" cy="-12" r="8" fill="#fff" />
        </g>
      </g>
    </svg>
  );
};
export const K07: React.FC = () => {
  const f = useCurrentFrame(); const z = 1 + 0.05 * (f / 74); const burst = ease(f, 61, 72);
  return (
    <Canvas><NightBg />
      <div style={{ position: 'absolute', left: (W - 1080) / 2, top: 40, width: 1080, height: 1360, borderRadius: 44, overflow: 'hidden', background: D.card, boxShadow: '0 40px 80px rgba(6,2,20,.55), inset 0 0 0 2px rgba(255,255,255,.08)' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 980, overflow: 'hidden' }}>
          <div style={{ position: 'absolute', inset: 0, transform: `scale(${z})`, transformOrigin: '50% 60%' }}>
            <Sky a="#4B2A9E" b="#D46AA0" c="#FFB38A" />
            <div style={{ position: 'absolute', left: 0, right: 0, top: 620, bottom: 0, background: 'linear-gradient(180deg,#C08458,#7A4A36)' }} />
            <svg style={{ position: 'absolute', left: 250, top: 400, width: 140, height: 240 }} viewBox="0 0 140 240"><path d="M70 10 L90 70 L130 90 L100 110 L108 170 L70 130 L32 170 L40 110 L10 90 L50 70Z" fill="#6B3FA0" opacity=".9" /><rect x="64" y="130" width="12" height="100" fill="#6B3FA0" /></svg>
            <Burn f={f} />
            <ThirdEye f={f} />
            <Founder id="F07" h={900} x={620} y={160} />
          </div>
        </div>
        <Abs x={46} y={1000} style={{ display: 'flex', alignItems: 'center', gap: 22 }}><Avatar id="F01" size={78} /><T cap={36} c={D.text}>thefounder</T></Abs>
        <Abs x={46} y={1100} w={990}><T cap={48} c={D.text} w={400}>Found myself. 🙏 Back to building.</T></Abs>
        <Abs x={46} y={1262} style={{ display: 'flex', gap: 30 }}><Heart s={72} c={burst > 0 ? C.red : '#6E64A0'} /><T cap={38} c={D.mute}>4,812 likes</T></Abs>
        {burst > 0 && [0, 1, 2, 3, 4, 5].map((i) => { const a = i * 60 * Math.PI / 180; return <div key={i} style={{ position: 'absolute', left: 540 + Math.cos(a) * 430 * burst - 50, top: 480 + Math.sin(a) * 330 * burst - 50, opacity: 1 - burst * 0.4 }}><Heart s={100 * (0.6 + burst)} /></div>; })}
        
      </div>
    </Canvas>
  );
};

// ---------------------------------------------------------------- K08 profile header / K09 billboard
export const K08: React.FC = () => {
  // round 2: dark mode (bible §4) + the missing joke line (lookdev S055 spec). "His LinkedIn says," = master 2155-2167 (local -4..8);
  // the headline types word by word from local 9 and is complete by 17, so the billboard (K09, f2186) lands it big on the sung word.
  const f = useCurrentFrame(); const s = 0.95 + 0.05 * pop(f, 0, 10);
  const words = ['Building', 'in', 'stealth.']; const on = [9, 12, 15]; const shown = words.filter((_, i) => f >= on[i]).join(' ');
  const cx = 1980 / 2;
  return (
    <Canvas><NightBg /><div style={{ position: 'absolute', inset: 0, transform: `scale(${s})` }}>
      <Card x={290} y={130} w={1980} h={1180} r={44}>
        <div style={{ position: 'absolute', left: 0, top: 0, right: 0, height: 330, background: 'linear-gradient(100deg,#3A16A8,#7B3CFF 62%,#9A70FF)' }} />
        <svg style={{ position: 'absolute', left: 0, top: 0 }} width="1980" height="330" viewBox="0 0 1980 330">{Array.from({ length: 9 }).map((_, i) => <circle key={i} cx={1980 * 0.62} cy={420} r={160 + i * 120} fill="none" stroke="#ffffff" strokeOpacity={0.07} strokeWidth="3" />)}</svg>
        <Abs x={1840} y={60}><Mark s={92} c="#ffffff22" /></Abs>
        <Abs x={cx - 190} y={130}><div style={{ width: 380, height: 380, borderRadius: '50%', border: `14px solid ${D.card}`, overflow: 'hidden', background: D.card2, boxShadow: '0 20px 40px rgba(6,2,20,.55)', boxSizing: 'border-box' }}><Avatar id="F08" size={352} zoom={1.25} cy={0.36} /></div></Abs>
        <Abs x={0} y={545} w={1980} style={{ textAlign: 'center' }}><T cap={96} fam="anton" c={D.text} style={{ textAlign: 'center', letterSpacing: 2 }}>THE FOUNDER</T></Abs>
        <Abs x={140} y={700} w={1700} h={150} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}><T cap={100} c="#FFFFFF" w={600} style={{ textAlign: 'center', letterSpacing: -1, whiteSpace: 'nowrap' }}>{shown}<Caret f={f} h={128} c={C.uvSoft} /></T></Abs>
        <Abs x={140} y={880} w={1700} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 20, whiteSpace: 'nowrap' }}><T cap={46} c={D.mute} w={500} style={{ whiteSpace: 'nowrap' }}>Founder & CEO at</T><div style={{ width: 260, height: 50, background: '#05030C', borderRadius: 6, boxShadow: 'inset 0 0 0 2px #ffffff14' }} /><T cap={46} c={D.mute} w={500} style={{ whiteSpace: 'nowrap' }}>· 12,551 followers</T></Abs>
        <Abs x={0} y={1010} w={1980} style={{ display: 'flex', gap: 30, justifyContent: 'center' }}>
          <div style={{ padding: '26px 70px', borderRadius: 60, background: C.uv }}><T cap={46} c="#fff">Follow</T></div>
          <div style={{ padding: '21px 65px', borderRadius: 60, border: `5px solid ${C.uvSoft}` }}><T cap={46} c={C.uvSoft}>Message</T></div>
        </Abs>
      </Card>
    </div></Canvas>
  );
};
export const K09: React.FC = () => {
  const f = useCurrentFrame(); const z = 1 + 0.03 * (f / 24);
  return (
    <Canvas bg="#1E2E4F"><div style={{ position: 'absolute', inset: 0, transform: `scale(${z})`, transformOrigin: '50% 40%' }}>
      <Sky a="#1B2A48" b="#4F6F98" c="#E9A982" />
      <Skyline y={1120} c1="#1F2836" c2="#161D28" />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 1120, bottom: 0, background: 'linear-gradient(180deg,#161A22,#0C0E12)' }} />
      {[0, 1, 2, 3, 4, 5, 6].map((i) => <div key={i} style={{ position: 'absolute', left: 1280 + (i - 3) * (60 + i * 0), top: 1120, width: 6, height: 320, background: '#ffffff22', transform: `skewX(${(i - 3) * 14}deg)` }} />)}
      <div style={{ position: 'absolute', left: 120, top: 120, width: 2320, height: 860, background: 'linear-gradient(0deg,#2A2824 0%,#17181B 38%,#0E0F12 100%)', borderRadius: 30, boxShadow: '0 0 120px #FFE9B033, inset 0 0 0 14px #2A2C30' }} />
      <div style={{ position: 'absolute', left: 1180, top: 980, width: 200, height: 260, background: '#111317' }} /><div style={{ position: 'absolute', left: 1100, top: 1190, width: 360, height: 50, background: '#111317' }} />
      <div style={{ position: 'absolute', left: 120, top: 980, width: 2320, height: 28, background: '#FFE9B0', opacity: 0.35, filter: 'blur(14px)' }} />
      <Founder id="F08" h={760} x={540} y={150} />
      <Abs x={940} y={260} w={1440}><T cap={190} fam="anton" c="#fff" style={{ lineHeight: 1.05, textShadow: '0 8px 0 #000' }}>BUILDING IN</T><T cap={190} fam="anton" c="#FFE56B" style={{ lineHeight: 1.05, textShadow: '0 8px 0 #000' }}>STEALTH.</T></Abs>
    </div></Canvas>
  );
};

// ---------------------------------------------------------------- K10 podcast player
export const K10: React.FC = () => {
  const f = useCurrentFrame(); const land = pop(f, 15, 10); const bar = lin(f, 0, 40, 0.31, 0.34);
  return (
    <Canvas bg="#121212"><div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 25% 45%,#4A4130 0%,#121212 65%)' }} />
      <Card x={150} y={150} w={1140} h={1140} r={56} bg="#141414" style={{ transform: `scale(${0.88 + 0.12 * land})`, boxShadow: '0 40px 120px #000A, 0 0 0 4px #2A2A2A' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 62% 38%,#3A3A3A,#141414 62%,#0A0A0A)' }} />
        <Founder id="F09" h={900} x={760} y={290} />
        <Abs x={60} y={50}><T cap={170} fam="anton" c="#fff" style={{ lineHeight: 1 }}>THE</T><T cap={170} fam="anton" c="#FFE56B" style={{ lineHeight: 1 }}>GRIND</T></Abs>
      </Card>
      <Abs x={1420} y={200}><T cap={48} c="#B3B3B3">NOW PLAYING</T></Abs>
      <Abs x={1420} y={300} w={1000}><T cap={100} fam="anton" c="#fff" style={{ lineHeight: 1.05 }}>Ep. 47:</T><T cap={100} fam="anton" c="#fff" style={{ lineHeight: 1.05 }}>Sleep is a</T><T cap={100} fam="anton" c="#FFE56B" style={{ lineHeight: 1.05 }}>skill issue</T></Abs>
      <Abs x={1420} y={870} w={1000} h={18} style={{ background: '#ffffff33', borderRadius: 9 }}><div style={{ width: `${bar * 100}%`, height: '100%', background: '#fff', borderRadius: 9 }} /><div style={{ position: 'absolute', left: `${bar * 100}%`, top: -17, width: 52, height: 52, borderRadius: 26, background: '#fff', marginLeft: -26 }} /></Abs>
      <Abs x={1420} y={950} w={1000} style={{ display: 'flex', justifyContent: 'space-between' }}><T cap={46} c="#B3B3B3" w={500}>14:02</T><T cap={46} c="#B3B3B3" w={500}>-1:32:10</T></Abs>
      <Abs x={1420} y={1100} style={{ display: 'flex', gap: 56, alignItems: 'center' }}>
        <svg width="110" height="110" viewBox="0 0 24 24"><path d="M6 6h3v12H6zM15 6h3v12h-3z" fill="#fff" /></svg>
        <div style={{ padding: '14px 44px', borderRadius: 60, background: '#fff' }}><T cap={52} c="#121212">2x</T></div>
      </Abs>
    </Canvas>
  );
};

// ---------------------------------------------------------------- K11 sales page
export const K11: React.FC = () => {
  const f = useCurrentFrame(); const strike = ease(f, 22, 30); const pulse = 1 + 0.06 * Math.sin(Math.PI * Math.min(1, Math.max(0, (f - 33) / 8)));
  return (
    <Canvas bg="#0B0B0C"><div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 22% 45%, #2E2A24 0%, #141413 48%, #0A0A0A 100%)' }} />
      <Founder id="F10" h={1260} x={560} y={110} />
      <Abs x={1040} y={100}><T cap={50} c="#D4B26A" style={{ letterSpacing: 6 }}>A 6-WEEK COURSE</T></Abs>
      <Abs x={1040} y={190}><T cap={230} fam="anton" c="#fff" style={{ lineHeight: 1 }}>LETTING GO<span style={{ fontSize: '0.35em', verticalAlign: 'super' }}>™</span></T></Abs>
      <Abs x={1040} y={650} style={{ display: 'flex', alignItems: 'baseline', gap: 50 }}>
        <div style={{ position: 'relative' }}><T cap={110} fam="anton" c="#8C8C8C">$1,999</T><div style={{ position: 'absolute', left: -10, top: '50%', width: `${strike * 112}%`, height: 14, background: C.red, transform: 'rotate(-4deg)' }} /></div>
        <T cap={150} fam="anton" c="#FFE56B">$1,499</T>
      </Abs>
      <Abs x={1040} y={910}><T cap={50} c="#A8A8A8">today only · 3 spots left</T></Abs>
      <Abs x={1040} y={1050}><div style={{ padding: '36px 110px', borderRadius: 80, background: '#E3B341', transform: `scale(${pulse})`, transformOrigin: 'left', boxShadow: '0 20px 50px #E3B34144' }}><T cap={66} c="#111">Enroll now</T></div></Abs>
    </Canvas>
  );
};

// ---------------------------------------------------------------- K12 sleep score + morning story
export const K12: React.FC = () => {
  const f = useCurrentFrame(); const sc = lin(f, 0, 23, 0, 98) ; const photo = ease(f, 28, 38);
  const R = 360, circ = 2 * Math.PI * R;
  return (
    <Canvas bg="#0B1230"><div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 30% 40%,#2A3A8F,#0B1230 70%)' }} />
      <svg style={{ position: 'absolute', left: 230, top: 180, width: 860, height: 860 }} viewBox="-430 -430 860 860"><circle r={R} stroke="#ffffff22" strokeWidth="54" fill="none" /><circle r={R} stroke="#7FB2FF" strokeWidth="54" fill="none" strokeLinecap="round" strokeDasharray={`${circ * sc / 100} ${circ}`} transform="rotate(-90)" /></svg>
      <Abs x={230} y={450} w={860} style={{ textAlign: 'center' }}><T cap={230} fam="anton" c="#fff" style={{ textAlign: 'center' }}>{Math.round(sc)}</T></Abs>
      <Abs x={230} y={1080} w={860} style={{ textAlign: 'center' }}><T cap={50} c="#B9C4FF" style={{ textAlign: 'center' }}>SLEEP SCORE</T></Abs>
      <Abs x={1230} y={240}><T cap={170} fam="anton" c="#fff">11 h 42 min</T></Abs>
      <Abs x={1230} y={470}><T cap={96} c="#B9C4FF">Excellent recovery</T></Abs>
      <Abs x={1230} y={720} style={{ display: 'flex', gap: 24 }}>{[0.6, 0.9, 1, 0.95, 0.8, 1, 0.85].map((h, i) => <div key={i} style={{ width: 70, height: 260 * h, alignSelf: 'flex-end', background: '#7FB2FF', borderRadius: 14, opacity: 0.9 }} />)}</Abs>
      <Abs x={1230} y={1100}><T cap={46} c="#8A98E0" w={500}>Deep 3 h 10 · REM 2 h 48</T></Abs>
      <Card x={1760} y={1440 - 840 * photo} w={720} h={800} r={36} bg="#fff" style={{ transform: 'none' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg,#FFE9C9,#FFD2E4)' }} />
        <Founder id="F11" h={560} x={360} y={60} />
        <Abs x={30} y={650}><T cap={46} c="#1A1410">Rise and grind ☀️</T></Abs>
      </Card>
    </Canvas>
  );
};

// ---------------------------------------------------------------- K13 livestream
const Chat = ['legend', 'who wrote the code tho', '🔥🔥', 'first', 'GOAT', 'ok but who is paying', '👏👏👏'];
export const K13: React.FC = () => {
  const f = useCurrentFrame(); const b2 = f >= 48; const lf = b2 ? f - 48 : f; const v = Math.round(lin(f, 0, 83, 41200, 58900));
  const off = lin(f, 0, 84, 0, 130);
  return (
    <Canvas bg="#0F0F0F"><div style={{ position: 'absolute', left: 0, top: 0, width: 1780, height: H, background: b2 ? 'linear-gradient(180deg,#141A24,#34506F 60%,#C98A6A)' : 'radial-gradient(circle at 50% 30%,#4A6283,#0E1118 75%)' }} />
      {[0, 1, 2, 3].map((i) => <div key={i} style={{ position: 'absolute', left: 200 + i * 400, top: 0, width: 140, height: 1200, background: 'linear-gradient(180deg,#FFFFFF55,#FFFFFF00)', transform: 'skewX(-14deg)' }} />)}
      <div style={{ position: 'absolute', left: 0, top: 1130, width: 1780, height: 310, background: '#0B0C10' }} />
      {!b2 ? <Founder id="F12" h={1260} x={890} y={90} /> : <Founder id="F13" h={1220} x={890} y={110} />}
      <Abs x={50} y={40} style={{ display: 'flex', gap: 26, alignItems: 'center' }}>
        <div style={{ background: C.red, padding: '10px 34px', borderRadius: 14 }}><T cap={46} c="#fff">● LIVE</T></div><T cap={52} c="#fff">THE GRIND TOUR</T></Abs>
      <Abs x={1380} y={32}><div style={{ background: '#00000088', padding: '18px 34px', borderRadius: 14 }}><T cap={46} c="#fff">👁 {fmt(v)}</T></div></Abs>
      {b2 && <Abs x={120} y={1160} style={{ opacity: pop(lf, 4, 10), transform: `translateY(${(1 - pop(lf, 4, 10)) * 40}px)` }}><div style={{ background: '#FFE56B', padding: '14px 70px', borderRadius: 20 }}><T cap={110} fam="anton" c="#111">THE GRIND</T></div></Abs>}
      <div style={{ position: 'absolute', left: 1780, top: 0, width: 780, height: H, background: '#0F0F0F', borderLeft: '4px solid #272727', overflow: 'hidden' }}>
        <Abs x={40} y={36}><T cap={46} c="#F1F1F1">LIVE CHAT</T></Abs>
        <div data-fit="off" style={{ position: 'absolute', left: 40, top: 230 - off % 130, width: 700 }}>
          {Array.from({ length: 11 }).map((_, i) => { const k = (i + Math.floor(off / 130)) % Chat.length; return (
            <div key={i} style={{ height: 130, display: 'flex', alignItems: 'center', gap: 24 }}><div style={{ width: 70, height: 70, borderRadius: 35, background: ['#3EA6FF', '#F28B82', '#81C995', '#FDD663'][k % 4], flex: 'none' }} /><T cap={46} c="#fff" w={500}>{Chat[k]}</T></div>); })}
        </div>
      </div>
    </Canvas>
  );
};
