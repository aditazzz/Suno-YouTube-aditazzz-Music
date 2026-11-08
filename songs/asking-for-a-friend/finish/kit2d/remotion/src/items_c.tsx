import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C, D, F, W, H, fsForCap, ease, pop, lin, fmt } from './theme';
import { NightBg, Canvas, Founder, Avatar, T, Abs, Card, Heart, Caret, Mark } from './ui';
import { Skyline, Sky } from './scenes';

// ---------------------------------------------------------------- K21 funding announcement
export const K21: React.FC = () => {
  const f = useCurrentFrame(); const n = Math.round(lin(f, 4, 40, 0, 20000000)); const sw = Math.sin(Math.min(1, Math.max(0, (f - 30) / 20)) * Math.PI * 3) * 14 * (1 - ease(f, 30, 52));
  return (
    <Canvas bg="#0E1014"><div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg,#232833,#0B0C10)' }} />
      {Array.from({ length: 26 }).map((_, i) => <div key={i} style={{ position: 'absolute', left: (i * 397) % W, top: ((i * 211) % 600) + lin(f, 30, 52, -300, 700) * (0.5 + (i % 5) * 0.2), width: 24, height: 44, background: ['#FFE56B', '#FF8FB8', '#6BD6FF', '#fff'][i % 4], transform: `rotate(${i * 40 + f * 6}deg)`, opacity: ease(f, 30, 36) }} />)}
      <Founder id="F24" h={1230} x={2160} y={190} />
      <Abs x={110} y={110}><div style={{ background: '#fff', padding: '12px 36px', borderRadius: 14 }}><T cap={48} c="#111">ANNOUNCEMENT</T></div></Abs>
      <Abs x={110} y={300}><T cap={250} fam="anton" c="#fff" style={{ lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>${fmt(n)}</T></Abs>
      <Abs x={110} y={620}><T cap={230} fam="anton" c="#FFE56B" style={{ lineHeight: 1 }}>RAISED</T></Abs>
      <Abs x={110} y={1000} w={1600}><T cap={64} c="#fff" w={500}>Series B. We're just getting started.</T></Abs>
      <Abs x={110} y={1200} style={{ display: 'flex', gap: 26, alignItems: 'center' }}><Heart s={72} /><T cap={52} c="#fff">21,309</T><Mark s={72} c="#fff" /></Abs>
    </Canvas>
  );
};
// ---------------------------------------------------------------- K22 whiteboard
export const K22: React.FC = () => {
  const f = useCurrentFrame(); const z = 1 + 0.06 * ease(f, 0, 51);
  return (
    <Canvas bg="#0B0A09"><div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 28% 18%,#5A3A26 0%,#24160F 38%,#0B0A09 80%)' }} />
      <div style={{ position: 'absolute', inset: 0, transform: `scale(${z})`, transformOrigin: '30% 55%' }}>
        <div style={{ position: 'absolute', left: 120, top: 100, width: 1760, height: 1100, background: '#E4DED0', borderRadius: 14, boxShadow: '0 30px 70px #000A, inset 0 0 0 16px #6E6A62' }}>
          <svg style={{ position: 'absolute', inset: 0 }} width="1760" height="1100" viewBox="0 0 1760 1100">
            {[[300, 380], [620, 280], [940, 420], [1260, 300]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r={96} fill="none" stroke="#1B3FA8" strokeWidth="12" />)}
            {[[400, 340, 520, 300], [720, 300, 840, 380], [1040, 390, 1160, 330]].map(([a, b, c, d], i) => <path key={i} d={`M${a} ${b} L${c} ${d}`} stroke="#1B3FA8" strokeWidth="12" markerEnd="url(#ar)" />)}
            <defs><marker id="ar" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="#1B3FA8" /></marker></defs>
            <path d="M1360 300 L1440 330" stroke="#1B3FA8" strokeWidth="12" markerEnd="url(#ar)" />
          </svg>
          <Abs x={780} y={640}><T cap={190} fam="marker" c="#C62C3E" style={{ fontFamily: F.marker, fontWeight: 400 }}>AI?</T></Abs>
          <Abs x={1180} y={730}><T cap={200} c="#1B3FA8" style={{ fontFamily: F.marker, fontWeight: 400 }}>$$$</T></Abs>
          <Abs x={160} y={700}><T cap={60} c="#1B3FA8" style={{ fontFamily: F.marker, fontWeight: 400 }}>step 1 → ??? → profit</T></Abs>
          <div style={{ position: 'absolute', inset: 0, borderRadius: 14, background: 'radial-gradient(ellipse at 18% 10%, rgba(255,214,160,.10) 0%, rgba(20,16,12,0) 40%, rgba(10,9,8,.42) 100%)', pointerEvents: 'none' }} />
        </div>
      </div>
      <Founder id="F25" h={1380} x={2100} y={60} />
    </Canvas>
  );
};
// ---------------------------------------------------------------- K23 cold plunge reel
export const K23: React.FC = () => {
  const f = useCurrentFrame(); const br = 1 + 0.02 * Math.sin(f / 54 * Math.PI * 2 * 1.5);
  const cubes = [[120, 0], [260, 2], [560, 1], [660, 3], [190, 4], [610, 5]];
  return (
    <Canvas><NightBg />
      <div style={{ position: 'absolute', left: (W - 810) / 2, top: 0, width: 810, height: H, overflow: 'hidden', background: 'linear-gradient(180deg,#22305E,#4A6FB0 62%,#7FA6D8)', boxShadow: '0 40px 80px rgba(6,2,20,.55)' }}>
        <svg style={{ position: 'absolute', left: 0, top: 380, width: 810, height: 560 }} viewBox="0 0 810 560">
          <path d="M0 300 L150 90 L240 200 L380 20 L520 210 L640 110 L810 300 V560 H0Z" fill="#2C4A84" /><path d="M380 20 L330 90 L360 80 L380 110 L410 76 L440 92Z M150 90 L118 140 L150 126 L176 144Z M640 110 L606 160 L640 148 L668 166Z" fill="#C9D8F0" />
          {[60, 130, 700, 760, 650].map((x, i) => <g key={i} transform={`translate(${x} ${330 + (i % 2) * 40})`}><path d="M0 -150 L44 -60 L18 -64 L56 10 L0 0 L-56 10 L-18 -64 L-44 -60Z" fill="#2F7A6A" /><rect x="-7" y="0" width="14" height="40" fill="#5C3A1E" /><path d="M0 -150 L22 -110 L0 -118 L-22 -110Z" fill="#fff" /></g>)}
        </svg>
        <div style={{ position: 'absolute', inset: 0, transform: `scale(${br})`, transformOrigin: '50% 80%' }}><Founder id="F26" h={900} x={405} y={330} /></div>
        {cubes.map(([x, k], i) => <div key={i} style={{ position: 'absolute', left: x + Math.sin(f / 9 + i) * 8, top: 905 + Math.sin(f / 7 + k) * 10, width: 84, height: 84, borderRadius: 16, transform: `rotate(${-14 + i * 9}deg)`, background: 'linear-gradient(135deg,#FFFFFFE0,#BDE9FF99)', border: '3px solid #fff', boxShadow: '0 6px 16px #0A3A5A55' }} />)}
        {[0, 1, 2, 3, 4].map((i) => <div key={i} style={{ position: 'absolute', left: 230 + i * 80 + Math.sin(f / 7 + i) * 24, top: 900 - ((f * 5 + i * 64) % 330), width: 120, height: 50, borderRadius: 30, background: '#ffffff', opacity: 0.3 * (1 - ((f * 5 + i * 64) % 330) / 400) }} />)}
        {Array.from({ length: 26 }).map((_, i) => <div key={i} style={{ position: 'absolute', left: (i * 97) % 790 + Math.sin(f / 10 + i) * 14, top: ((i * 173 + f * (4 + (i % 3))) % 1440), width: 8 + (i % 3) * 4, height: 8 + (i % 3) * 4, borderRadius: '50%', background: '#fff', opacity: 0.85 }} />)}
        <Abs x={50} y={190} style={{ display: 'flex', alignItems: 'center', gap: 22 }}>
          <div style={{ width: 40, height: 150, borderRadius: 20, background: '#fff', border: '5px solid #0E3A5A', position: 'relative' }}><div style={{ position: 'absolute', left: 10, right: 10, bottom: 10, height: 36, borderRadius: 14, background: '#E5304A' }} /></div>
          <div><T cap={104} fam="anton" c="#fff" style={{ lineHeight: 1.0 }}>3°C</T></div>
        </Abs>
        <Abs x={40} y={1060} w={660} style={{ background: '#0E3A5ACC', borderRadius: 24, padding: '22px 36px', boxSizing: 'border-box' }}><T cap={52} c="#fff">Day 400 · breathe</T><T cap={34} c="#BDE9FF" w={500} style={{ marginTop: 8 }}>#coldplunge · 6:00 AM · again</T></Abs>
        <div style={{ position: 'absolute', right: 26, top: 700, display: 'flex', flexDirection: 'column', gap: 40, alignItems: 'center' }}><Heart s={80} c="#fff" /><T cap={34} c="#fff">48K</T><div style={{ width: 70, height: 70, borderRadius: 35, background: '#ffffffEE' }} /><T cap={34} c="#fff">2,019</T></div>
        <Abs x={50} y={80} style={{ display: 'flex', gap: 22, alignItems: 'center' }}><Avatar id="F01" size={84} ring="#fff" /><T cap={34} c="#fff">thefounder</T></Abs>
      </div>
    </Canvas>
  );
};

// ---------------------------------------------------------------- K25 the LinkedIn-style post that nobody sees (233 f)
export const K25: React.FC = () => {
  const f = useCurrentFrame(); const msg = "Couldn't have done it without my incredible team 🙏"; const n = Math.round(lin(f, 10, 80, 0, msg.length));
  const phase = f < 85 ? 0 : f < 142 ? 1 : 2; const lf = phase === 2 ? f - 142 : f - 85;
  const spin = f * 14;
  return (
    <Canvas><NightBg />
      <Card x={420} y={120} w={1720} h={1200} r={44}>
        <Abs x={70} y={60} style={{ display: 'flex', gap: 36, alignItems: 'center' }}><Avatar id="F28" size={150} zoom={2.1} cy={0.3} ring={C.uv} /><div><T cap={50} c={D.text}>The Founder</T><T cap={46} c={D.mute} w={500}>Founder · Visionary · Thought leader</T></div><div style={{ marginLeft: 'auto', marginRight: 70 }}><Mark s={100} /></div></Abs>
        {phase === 0 && <><div style={{ position: 'absolute', left: 70, top: 280, width: 1580, height: 600, border: `5px solid ${C.uv}`, borderRadius: 28, boxSizing: 'border-box', padding: 50 }}><T cap={72} c={D.text} w={400} style={{ lineHeight: 1.25 }}>{msg.slice(0, n)}<Caret f={f} h={74} c={C.uv} /></T></div>
          <Abs x={70} y={1000}><div style={{ display: 'inline-block', padding: '28px 96px', borderRadius: 70, background: C.uv }}><T cap={52} c="#fff">Post</T></div></Abs></>}
        {phase >= 1 && <><Abs x={70} y={260} w={1580}><T cap={72} c={D.text} w={400} style={{ lineHeight: 1.25 }}>{msg}</T></Abs>
          <div style={{ position: 'absolute', left: 0, top: 480, width: 1720, height: 560, background: 'linear-gradient(160deg,#3B1B94,#B4529E)' }}><Founder id="F27" h={800} x={860} y={-10} /></div>
          <Abs x={70} y={1090} style={{ display: 'flex', gap: 80 }}>
            <T cap={50} c={D.text}>👍 {phase === 2 ? '0' : '…'}</T><T cap={50} c={D.text}>💬 {phase === 2 ? '0' : '…'}</T>
            <T cap={50} c={D.mute} w={500}>{phase === 2 ? 'Seen by 0' : 'Posting…'}</T></Abs></>}
        {phase >= 1 && <div style={{ position: 'absolute', right: 70, top: 1075, width: 90, height: 90, borderRadius: '50%', border: `12px solid #3A2A78`, borderTopColor: C.uv, transform: `rotate(${spin}deg)` }} />}
      </Card>
    </Canvas>
  );
};
// ---------------------------------------------------------------- K26 unfollowed profile
export const K26: React.FC = () => {
  const f = useCurrentFrame(); const n = Math.round(12551 * (1 - ease(f, 4, 22))); const swap = f >= 20;
  return (
    <Canvas><NightBg />
      <Card x={430} y={130} w={1700} h={1180} r={44}>
        <div style={{ position: 'absolute', left: 0, top: 0, right: 0, height: 320, background: 'linear-gradient(100deg,#5A2CE0,#7B3CFF 60%,#A07BFF)' }} />
        <Abs x={80} y={160}><div style={{ width: 340, height: 340, borderRadius: '50%', border: `14px solid ${D.card}`, overflow: 'hidden' }}><Avatar id={swap ? 'F29' : 'F01'} size={312} zoom={2.0} cy={swap ? 0.45 : 0.3} cx={0.5} /></div></Abs>
        <Abs x={480} y={360}><T cap={96} fam="anton" c={D.text}>THE FOUNDER</T></Abs>
        <Abs x={90} y={560} style={{ display: 'flex', gap: 160 }}>
          <div><T cap={190} fam="anton" c={swap ? C.red : D.text} style={{ fontVariantNumeric: 'tabular-nums', filter: f > 4 && f < 22 ? 'blur(6px)' : 'none' }}>{fmt(n)}</T><T cap={52} c={D.mute}>followers</T></div>
          <div><T cap={190} fam="anton" c={D.text}>1</T><T cap={52} c={D.mute}>following</T></div>
        </Abs>
        <Abs x={90} y={930} style={{ display: 'flex', gap: 40 }}><div style={{ padding: '30px 100px', borderRadius: 70, background: swap ? 'transparent' : C.uv, border: `5px solid ${C.uv}` }}><T cap={52} c={swap ? C.uvSoft : '#fff'}>{swap ? 'Follow' : 'Following'}</T></div><div style={{ padding: '30px 100px', borderRadius: 70, border: `5px solid ${C.uv}` }}><T cap={52} c={C.uvSoft}>Message</T></div></Abs>
      </Card>
    </Canvas>
  );
};
