import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { C, D, F, W, H, fsForCap, ease, pop, lin, fmt } from './theme';
import { NightBg, Canvas, Founder, Avatar, T, Abs, Card, Heart } from './ui';
import { Skyline, Sky } from './scenes';

const Dots: React.FC<{ n: number; i: number }> = ({ n, i }) => (<div style={{ display: 'flex', gap: 22 }}>{Array.from({ length: n }).map((_, k) => <div key={k} style={{ width: k === i ? 34 : 22, height: 22, borderRadius: 11, background: k === i ? C.uvSoft : '#4A3A88' }} />)}</div>);
// ---------------------------------------------------------------- K14 carousel (6 slides, swipe on beats)
export const k14Slide = (i: number) => {
    const bg = ['#15181D', '#1E3A5F', '#2E2620', '#1E3A5F', '#123A2E', '#15181D'][i]; // round 4: his carousel template, charcoal/navy + yellow, no ultraviolet
    return (
      <div style={{ position: 'absolute', inset: 0, background: bg }}>
        {i === 0 && (<><Abs x={90} y={80}><T cap={56} c="#FFE56B">MY 5AM ROUTINE 🧠</T></Abs><Abs x={90} y={260}><T cap={400} fam="anton" c="#fff" style={{ lineHeight: 1 }}>5:00</T></Abs><Abs x={100} y={780}><T cap={80} c="#C9D2DC">AM. rise. grind.</T></Abs>
          <svg style={{ position: 'absolute', left: 560, top: 760, width: 400, height: 300 }} viewBox="0 0 400 300"><circle cx="200" cy="170" r="110" fill="#fff" stroke="#EDEFF2" strokeWidth="16" /><path d="M200 170V100M200 170l50 30" stroke="#15181D" strokeWidth="14" strokeLinecap="round" /><circle cx="110" cy="50" r="46" fill="#FFE56B" /><circle cx="290" cy="50" r="46" fill="#FFE56B" /></svg></>)}
        {i === 1 && (<><Founder id="F14" h={1100} x={620} y={260} /><Abs x={70} y={70}><T cap={96} fam="anton" c="#fff">STRETCH.</T></Abs></>)}
        {i === 2 && (<><Abs x={80} y={70}><T cap={96} fam="anton" c="#fff">COLD BREW</T></Abs>
          <svg style={{ position: 'absolute', left: 190, top: 330, width: 700, height: 900 }} viewBox="0 0 700 900"><rect x="150" y="80" width="400" height="720" rx="60" fill="#3B2A1A" stroke="#EDEFF2" strokeWidth="14" /><rect x="190" y="140" width="320" height="200" rx="30" fill="#6B4A2A" /><rect x="230" y="520" width="240" height="160" rx="24" fill="#FFF3C4" /><path d="M260 80 L240 20 H460 L440 80" fill="#B0804A" stroke="#EDEFF2" strokeWidth="14" /></svg></>)}
        {i === 3 && (<><Abs x={80} y={70}><T cap={96} fam="anton" c="#fff">GRATITUDE</T></Abs>
          <div style={{ position: 'absolute', left: 150, top: 330, width: 780, height: 940, background: '#fff', borderRadius: 24, boxShadow: '0 20px 50px #00000030', transform: 'rotate(-3deg)' }}>{[0, 1, 2, 3, 4, 5].map((k) => <div key={k} style={{ position: 'absolute', left: 60, right: 60, top: 140 + k * 120, height: 5, background: '#D6DCE4' }} />)}<Abs x={60} y={50}><T cap={56} c="#1B3FA8" style={{ fontFamily: F.marker, fontWeight: 400 }}>1. Me</T></Abs><Abs x={60} y={170}><T cap={56} c="#1B3FA8">2. Myself</T></Abs><Abs x={60} y={290}><T cap={56} c="#1B3FA8">3. The grind</T></Abs></div></>)}
        {i === 4 && (<><Abs x={80} y={70}><T cap={96} fam="anton" c="#fff">SUPPLEMENTS</T></Abs>{[0, 1, 2].map((k) => <div key={k} style={{ position: 'absolute', left: 120 + k * 290, top: 380 + (k % 2) * 80, width: 240, height: 520, borderRadius: 40, background: ['#3A7BD5', '#FFE56B', '#fff'][k], border: `12px solid #EDEFF2` }}><div style={{ position: 'absolute', left: 20, right: 20, top: 190, height: 150, background: '#fff', borderRadius: 14 }} /></div>)}</>)}
        {i === 5 && (<><Founder id="F15" h={1240} x={690} y={200} /><Abs x={70} y={90} w={900}><T cap={110} fam="anton" c="#fff" style={{ lineHeight: 1.05 }}>"Discipline</T><T cap={110} fam="anton" c="#FFE56B" style={{ lineHeight: 1.05 }}>isn't a choice."</T></Abs></>)}
      </div>);
  };
export const K14: React.FC = () => {
  const f = useCurrentFrame(); const idx = Math.min(5, Math.floor(f / 16)); const sw = ease(f - idx * 16, 0, 8); const prev = Math.max(0, idx - 1);
  const slide = k14Slide;
  return (
    <Canvas><NightBg />
      <Card x={(W - 1080) / 2} y={30} w={1080} h={1380} r={44}>
        <Abs x={34} y={24} style={{ display: 'flex', gap: 22, alignItems: 'center', zIndex: 3 }}><Avatar id="F01" size={86} ring={C.uv} /><T cap={36} c={D.text}>thefounder</T></Abs>
        <div style={{ position: 'absolute', left: 0, top: 140, width: 1080, height: 1080, overflow: 'hidden', background: D.card }}>
          <div style={{ position: 'absolute', inset: 0, transform: `translateX(${-1080 * sw}px)` }}>{slide(prev === idx ? idx : prev)}</div>
          <div style={{ position: 'absolute', inset: 0, transform: `translateX(${1080 * (1 - sw)}px)` }}>{slide(idx)}</div>
          <Abs x={940} y={26}><div style={{ background: '#000A', padding: '8px 24px', borderRadius: 30 }}><T cap={34} c="#fff">{idx + 1}/6</T></div></Abs>
        </div>
        <Abs x={0} y={1250} w={1080} style={{ display: 'flex', justifyContent: 'center' }}><Dots n={6} i={idx} /></Abs>
        <Abs x={40} y={1300}><T cap={36} c={D.mute} w={500}>♡ 8,204   💬 641   ➤</T></Abs>
      </Card>
    </Canvas>
  );
};

// ---------------------------------------------------------------- K15 clip title, K16 gym, K17 quote
export const K15: React.FC = () => {
  const f = useCurrentFrame(); const words = ['MY', 'SECRET?', 'DISCIPLINE.']; const t = [8, 16, 28];
  return (
    <Canvas bg="#15171B"><div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(120deg,#3A3530,#101215)' }} />
      {[0, 1, 2].map((i) => <div key={i} style={{ position: 'absolute', left: 1500 + i * 260, top: 0, width: 130, height: H, background: '#FFE9B012', transform: 'skewX(-12deg)' }} />)}
      <Founder id="F16" h={1440} x={1750} y={40} />
      <Abs x={120} y={150} w={1500}>{words.map((w, i) => (<div key={i} style={{ opacity: pop(f, t[i], 8), transform: `translateY(${(1 - pop(f, t[i], 8)) * 50}px)` }}><T cap={i === 2 ? 230 : 170} fam="anton" c={i === 2 ? '#FFE56B' : '#fff'} style={{ lineHeight: 1.12, textShadow: '0 8px 0 #000' }}>{w}</T></div>))}</Abs>
      <Abs x={120} y={1250} style={{ display: 'flex', gap: 30, alignItems: 'center' }}><Avatar id="F01" size={110} ring="#fff" /><T cap={46} c="#fff">Ep. 47 · The Grind</T></Abs>
    </Canvas>
  );
};
const K16v: React.FC<{ still: string; rec?: boolean }> = ({ still, rec }) => {
  // round 2 (her f3460 note: "Dumb bell he's holding looks weird this could be funnier"): night palette, reframed still (fist no longer
  // cut by the still edge), and the prop is the joke. rec = the timer is a recording timer: his 40 minutes are 40 minutes of filming.
  const f = useCurrentFrame(); const s = lin(f, 18, 38, 0, 2400); const mm = Math.floor(s / 60), ss = Math.floor(s % 60);
  const blink = Math.floor(f / 8) % 2 === 0;
  return (
    <Canvas><NightBg at="70% 40%" />
      <div style={{ position: 'absolute', left: (W - 1080) / 2 - 560, top: 40, width: 1080, height: 1360, borderRadius: 44, overflow: 'hidden', background: D.card, boxShadow: '0 40px 80px rgba(6,2,20,.55), inset 0 0 0 2px rgba(255,255,255,.08)' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, right: 0, height: 960, background: 'linear-gradient(180deg,#5A2CE0,#2B0F73)' }} />
        <Founder id={still} h={1000} x={540} y={-20} />
        <Abs x={40} y={990}><T cap={60} c={D.text} w={600}>40 min. No days off. 💪</T></Abs>
        <Abs x={40} y={1130} style={{ display: 'flex', gap: 28, alignItems: 'center' }}><Heart s={70} /><T cap={38} c={D.mute}>12.4K</T></Abs>
      </div>
      {rec && <Abs x={1300} y={150} w={1100} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 34 }}><div style={{ width: 72, height: 72, borderRadius: 36, background: C.red, opacity: blink ? 1 : 0.35 }} /><T cap={90} fam="anton" c={C.red} style={{ letterSpacing: 10 }}>REC</T></Abs>}
      <Abs x={1300} y={rec ? 330 : 250} w={1100} style={{ textAlign: 'center' }}><T cap={400} fam="anton" c="#fff" style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>{String(mm).padStart(2, '0')}:{String(ss).padStart(2, '0')}</T></Abs>
      <Abs x={1300} y={rec ? 900 : 820} w={1100} style={{ textAlign: 'center' }}><T cap={80} fam="anton" c="#FFE56B" style={{ textAlign: 'center', letterSpacing: 8 }}>{rec ? 'WORKOUT VIDEO' : 'STOPWATCH'}</T></Abs>
    </Canvas>
  );
};
export const K16: React.FC = () => <K16v still="F17B" />;
export const K16A: React.FC = () => <K16v still="F17A" rec />;
export const K17: React.FC = () => {
  const f = useCurrentFrame(); const z = 1 + 0.06 * (f / 27); const likes = Math.round(lin(f, 0, 27, 9120, 12847));
  return (
    <Canvas bg="#111"><div style={{ position: 'absolute', inset: 0, transform: `scale(${z})`, transformOrigin: '30% 50%' }}>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 25% 50%,#666,#111 75%)' }} />
      <Founder id="F15" h={1300} x={640} y={60} bw rim={false} />
      <Abs x={1200} y={300} w={1300}><T cap={190} fam="anton" c="#fff" style={{ lineHeight: 1.05 }}>FOUNDER</T><T cap={190} fam="anton" c="#fff" style={{ lineHeight: 1.05 }}>MINDSET.</T></Abs>
      <Abs x={1200} y={900}><T cap={64} c="#fff" w={500}>Built different. <span style={{ color: '#70B5F9' }}>#founder</span></T></Abs>
      <Abs x={1200} y={1100} style={{ display: 'flex', gap: 28, alignItems: 'center' }}><Heart s={90} /><T cap={60} c="#fff">{fmt(likes)}</T></Abs>
    </div></Canvas>
  );
};

// ---------------------------------------------------------------- K18 the book
const GOLD = '#E3C26A';
const Cover: React.FC<{ w: number; h: number; hero?: boolean }> = ({ w, h, hero }) => (
  <div style={{ position: 'relative', width: w, height: h, background: 'linear-gradient(100deg,#0E1A44,#142560 60%,#1B2F7A)', borderRadius: '10px 22px 22px 10px', boxShadow: '34px 40px 70px #0007, inset 22px 0 0 #070F2A', overflow: 'hidden' }}>
    {/* gold frame: even 40 px from top/bottom/right, 40 px clear of the spine; everything on the cover is laid out INSIDE it (flex column), so nothing can touch the frame */}
    <div data-fit="frame" style={{ position: 'absolute', left: 62, right: 36, top: 40, bottom: 40, border: `5px solid ${GOLD}`, boxSizing: 'border-box', ...(hero ? { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px 44px 44px' } : {}) }}>
      {hero && <>
        <T cap={36} c={GOLD} w={700} style={{ textAlign: 'center', letterSpacing: 3 }}>THE #1 BESTSELLER*</T>
        <div style={{ marginTop: 16, textAlign: 'center' }}><T cap={104} fam="anton" c="#F3D685" style={{ textAlign: 'center', lineHeight: 1.0, letterSpacing: 2 }}>I BUILT THIS</T><T cap={104} fam="anton" c="#fff" style={{ textAlign: 'center', lineHeight: 1.0, letterSpacing: 2 }}>MYSELF</T></div>
        <div style={{ position: 'relative', marginTop: 28, width: '100%', flex: 1, minHeight: 0, overflow: 'hidden', border: `3px solid ${GOLD}`, boxSizing: 'border-box', background: 'radial-gradient(circle at 50% 30%,#9B72FF,#3A1A9A 70%,#170A3D)' }}>
          {[0, 1, 2, 3, 4, 5, 6].map((i) => <div key={i} style={{ position: 'absolute', left: '50%', top: '34%', width: 6, height: 900, background: '#ffffff18', transformOrigin: 'top', transform: `rotate(${-90 + i * 30}deg)` }} />)}
          <Founder id="F30" h={880} x={(w - 62 - 36 - 88) / 2} y={24} rim={false} />
          {/* round 4 (her K18 note): the cover's pull-quote is the punch, in his own voice */}
          <div data-fit="quote" style={{ position: 'absolute', left: 20, right: 20, bottom: 20, boxSizing: 'border-box', padding: '18px 24px 20px', background: GOLD, borderRadius: 8, boxShadow: '0 10px 24px #000a', transform: 'rotate(-2deg)', textAlign: 'center' }}>
            <T cap={38} c="#2B1A06" w={800} style={{ textAlign: 'center', lineHeight: 1.15 }}>“I was living on</T>
            <T cap={84} fam="anton" c="#9E1B14" style={{ textAlign: 'center', lineHeight: 1.1, letterSpacing: 4, margin: '6px 0 4px' }}>RAMEN</T>
            <T cap={38} c="#2B1A06" w={800} style={{ textAlign: 'center', lineHeight: 1.15 }}>when I made this.”</T>
          </div>
        </div>
        <div style={{ marginTop: 28, textAlign: 'center' }}><T cap={40} fam="corm" c={GOLD} style={{ textAlign: 'center', letterSpacing: 1, whiteSpace: 'nowrap' }}>a memoir by The Founder</T><T cap={34} c="#B9A98A" w={500} style={{ textAlign: 'center', marginTop: 10 }}>Foreword by The Founder</T></div>
      </>}
    </div>
  </div>
);
export const K18: React.FC = () => {
  const f = useCurrentFrame(); const drop = f < 16 ? -900 + 900 * (f / 16) ** 2 : (f < 22 ? 14 * Math.sin((f - 16) / 6 * Math.PI) : 0);
  const sq = f >= 16 && f < 24 ? 1 + 0.03 * Math.sin((f - 16) / 8 * Math.PI) : 1;
  return (
    <Canvas bg="#2A1A12"><div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 40% 25%,#7A5A3E 0%,#3A2417 55%,#1A0F09 100%)' }} />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 1240, bottom: 0, background: 'linear-gradient(180deg,#8A5A32,#5A3820)', boxShadow: '0 -10px 40px #0008' }} />
      {[0, 1, 2].map((i) => <div key={i} style={{ position: 'absolute', left: 1420 + i * 110, top: 760 - i * 10, transform: `rotate(${6 + i * 5}deg)`, transformOrigin: 'bottom left' }}><Cover w={560} h={780} /></div>)}
      <div style={{ position: 'absolute', left: 560, top: 60 + drop, transform: `scale(${1 / sq}, ${sq})`, transformOrigin: 'bottom' }}><Cover w={900} h={1260} hero /></div>
      <div style={{ position: 'absolute', left: 1640, top: 150, width: 640, background: '#FFFDF8', borderRadius: 12, padding: '36px 44px', boxShadow: '0 20px 40px #0008', transform: 'rotate(2deg)' }}>
        <T cap={38} fam="anton" c="#B3261E" style={{ letterSpacing: 2 }}>STAFF PICK</T>
        <T cap={40} c="#14131A" w={500} style={{ marginTop: 14 }}>“Couldn’t put it down. I wrote it.”</T>
        <T cap={34} c="#6B6580" w={500} style={{ marginTop: 14 }}>- the staff (the author)</T>
      </div>
      <div style={{ position: 'absolute', left: 60, top: 1100, width: 440, boxSizing: 'border-box', padding: '28px 32px', background: '#1A0F09', border: '4px solid #E3C26A', borderRadius: 10, transform: 'rotate(-2deg)' }}><T cap={40} fam="anton" c="#F3D685" style={{ letterSpacing: 2 }}>*SELF-REPORTED</T><T cap={34} c="#E3C26A" w={500} style={{ marginTop: 10 }}>Signed copies: 1 (his)</T></div>
    </Canvas>
  );
};

// ---------------------------------------------------------------- K19 keynote (3 beats: 51 / 43 / 52)
export const K19: React.FC = () => {
  const f = useCurrentFrame(); const beat = f < 51 ? 0 : f < 94 ? 1 : 2; const lf = beat === 0 ? f : beat === 1 ? f - 51 : f - 94;
  return (
    <Canvas bg="#05070A"><div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 20%,#1E2838,#05070A 70%)' }} />
      {beat < 2 ? (<>
        <div style={{ position: 'absolute', left: 280, top: 70, width: 2000, height: 920, background: beat === 0 ? 'linear-gradient(135deg,#1B2130,#0A0C10)' : 'radial-gradient(ellipse at 50% 30%,#1C2230,#08090C 80%)', boxShadow: '0 0 160px #9FB8D844', border: '10px solid #111317' }}>
          {beat === 0 ? <Abs x={100} y={66} w={1800} style={{ textAlign: 'center', opacity: pop(lf, 22, 8), transform: `scale(${0.9 + 0.1 * pop(lf, 22, 8)})` }}><T cap={280} fam="anton" c="#fff" style={{ textAlign: 'center', lineHeight: 1 }}>FOUNDER</T><T cap={280} fam="anton" c="#FFE56B" style={{ textAlign: 'center', lineHeight: 1 }}>MODE</T></Abs>
            : <Abs x={100} y={65} w={1800} style={{ textAlign: 'center' }}><T cap={170} fam="anton" c="#fff" style={{ textAlign: 'center', lineHeight: 1.1, opacity: pop(lf, 8, 8) }}>NOBODY KNOWS</T><T cap={170} fam="anton" c="#fff" style={{ textAlign: 'center', lineHeight: 1.1, opacity: pop(lf, 14, 8) }}>WHO OWNS</T><T cap={170} fam="anton" c="#FFE56B" style={{ textAlign: 'center', lineHeight: 1.1, opacity: pop(lf, 20, 8) }}>THE CODE?</T></Abs>}
        </div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 1080, bottom: 0, background: '#0A0B0E' }} />
        {beat === 0 ? <Founder id="F19" h={430} x={1280} y={1010} anchor="top" style={{ top: 1010 }} /> : <Founder id="F20" h={560} x={2200} y={900} />}
        {beat === 1 && <div />}
      </>) : (<>
        {[0, 1, 2].map((i) => <div key={i} style={{ position: 'absolute', left: 740 + i * 280 + Math.sin(lf / 10) * 120, top: 0, width: 260, height: 1100, background: 'linear-gradient(180deg,#DDE8FF66,#DDE8FF00)', transform: 'skewX(' + (i - 1) * 8 + 'deg)' }} />)}
        <Founder id="F12" h={1340} x={1280} y={70} />
      </>)}
      <Abs x={60} y={1330}><T cap={40} c="#8A93A6" style={{ letterSpacing: 6 }}>● LIVE · FOUNDER KEYNOTE</T></Abs>
    </Canvas>
  );
};

// ---------------------------------------------------------------- K20 guest tiles, K20b multiply
const EPS = ['Ep. 212: Delegation is a mindset', 'Ep. 98: Sleep is a skill issue', 'Ep. 301: Pivot, then pivot again', 'Ep. 77: No days off', 'Ep. 150: Being early is a lifestyle', 'Ep. 64: Ask me anything (no)', 'Ep. 233: Stealth is a feeling', 'Ep. 19: Why I left, again'];
const GT = ['F06', 'F21', 'F22', 'F23']; const GBG = ['#3A6EA5', '#FF8FB8', '#6BD6FF', '#FFD84A'];
// Round 4 (her K20 note "Backgrounds too basic. We have a Porsche couldn't we use that"): the two car tiles sit inside
// OUR GT3 RS (finish/car blend, yellow calipers, no badges): Blender plates public/k20/car_{P,D}.png (2380x1200, cabin glass
// ~80% holdout) laid over the founder, so he is seen through the window / windscreen. The studio and hotel rooms got the same
// depth: lit by their practicals, background softened like a real webcam's, a foreground element. Plates/rooms are laid out in
// a 2380:1200 box that covers the tile, so K20b's other tile sizes crop the same picture.
const PA = 2380 / 1200;
const CAR: Record<number, { img: string; id: string; fx: number; fy: number; fh: number; flip?: boolean }> = {
  2: { img: 'k20/car_P.png', id: 'F16', fx: 0.64, fy: 0.11, fh: 1.2 },
  3: { img: 'k20/car_D.png', id: 'F23', fx: 0.67, fy: 0.17, fh: 1.1 },
};
const Room4: React.FC<{ k: number; w: number; h: number }> = ({ k, w, h }) => {
  const s = h / 600;
  if (k === 0) return (<>{/* studio at night: foam wedges, warm key, shelf, neon ON AIR, boom arm in the foreground */}
    <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 30% 40%,#3E434C 0%,#22252B 45%,#0E1013 100%)' }} />
    <div style={{ position: 'absolute', inset: 0, filter: `blur(${2.2 * s}px)` }}>
      {Array.from({ length: 24 }).map((_, i) => <div key={i} style={{ position: 'absolute', left: (i % 6) * 112 * s + 10 * s, top: Math.floor(i / 6) * 112 * s + 6 * s, width: 104 * s, height: 104 * s, borderRadius: 6 * s, background: (i + Math.floor(i / 6)) % 2 ? 'repeating-linear-gradient(90deg,#33363D 0 13px,#1E2024 13px 26px)' : 'repeating-linear-gradient(0deg,#33363D 0 13px,#1E2024 13px 26px)', boxShadow: 'inset 0 0 26px #0009' }} />)}
      <div style={{ position: 'absolute', right: 20 * s, top: 150 * s, width: 400 * s, height: 460 * s, background: 'linear-gradient(180deg,#3A2018,#24130D)', boxShadow: 'inset 0 0 40px #000a' }}>
        {[0, 1, 2].map((r) => <div key={r} style={{ position: 'absolute', left: 0, right: 0, top: (r * 150 + 132) * s, height: 12 * s, background: '#5A3424' }} />)}
        {[0, 1, 2].map((r) => <div key={'b' + r} style={{ display: 'flex', gap: 5 * s, position: 'absolute', left: 18 * s, top: (r * 150 + 28) * s, alignItems: 'flex-end' }}>{['#C8553D', '#E6B24C', '#2E6F8E', '#EFE3C8', '#7A3A5A', '#3E8E6A', '#D9D2C2', '#5A7FA8'].slice(r, r + 6 + (r % 2)).map((c, i) => <div key={i} style={{ width: (26 + (i * 7) % 18) * s, height: (84 + (i * 13) % 22) * s, background: c, opacity: .9, borderRadius: 2 * s }} />)}</div>)}
      </div>
      {[[120, 470, 70, '#FFC58A'], [300, 520, 46, '#FF8FB8'], [520, 560, 60, '#FFC58A'], [900, 90, 40, '#9FD8FF']].map(([x, y, r, c], i) => <div key={i} style={{ position: 'absolute', left: (x as number) * s, top: (y as number) * s, width: (r as number) * s, height: (r as number) * s, borderRadius: '50%', background: c as string, opacity: .35, boxShadow: `0 0 ${30 * s}px ${c}` }} />)}
    </div>
    <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 52% 48%,#FFC58A33 0%,#FFC58A00 45%), linear-gradient(90deg,#0006,#0000 30%,#0000 70%,#0007)' }} />
    <div style={{ position: 'absolute', left: -40 * s, top: 70 * s, width: 520 * s, height: 26 * s, background: '#0C0A12', transform: 'rotate(-14deg)', transformOrigin: 'left', borderRadius: 13 * s, boxShadow: '0 6px 14px #0008' }} />
  </>);
  return (<>{/* hotel at night: tufted headboard, warm lamp, city window, crisp sheets */}
    <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg,#1E1A18,#2E2420 60%,#3A2C24)' }} />
    <div style={{ position: 'absolute', inset: 0, filter: `blur(${2.2 * s}px)` }}>
      <div style={{ position: 'absolute', left: 60 * s, top: 30 * s, width: 440 * s, height: 300 * s, background: 'linear-gradient(180deg,#0B1030,#1B1F4A)', border: `${10 * s}px solid #120C1C` }}>
        {Array.from({ length: 30 }).map((_, i) => <div key={i} style={{ position: 'absolute', left: ((i * 67) % 400) * s, top: (120 + ((i * 41) % 150)) * s, width: (8 + (i % 4) * 4) * s, height: (8 + (i % 4) * 4) * s, borderRadius: '50%', background: ['#FFD27A', '#FF9FC2', '#9FD8FF'][i % 3], opacity: .8, boxShadow: `0 0 ${12 * s}px currentColor` }} />)}
      </div>
      <div style={{ position: 'absolute', left: 300 * s, top: 250 * s, width: 820 * s, height: 260 * s, borderRadius: `${30 * s}px ${30 * s}px 0 0`, background: 'radial-gradient(circle,#7A6A58 0 8px,#5E4F40 9px) 0 0/' + 70 * s + 'px ' + 70 * s + 'px', boxShadow: 'inset 0 0 60px #000a' }} />
      <div style={{ position: 'absolute', left: 980 * s, top: 170 * s, width: 120 * s, height: 110 * s, borderRadius: `${50 * s}px ${50 * s}px ${10 * s}px ${10 * s}px`, background: 'linear-gradient(180deg,#FFF1C8,#FFC97A)', boxShadow: `0 0 ${140 * s}px ${60 * s}px #FFB65A66` }} />
      <div style={{ position: 'absolute', left: 1032 * s, top: 280 * s, width: 16 * s, height: 150 * s, background: '#8A5A20' }} />
    </div>
    <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 85% 30%,#FFB65A40,#FFB65A00 50%), linear-gradient(90deg,#0005,#0000 35%)' }} />
    <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 170 * s, background: 'linear-gradient(180deg,#F3F0EA,#D6D0C6)', borderTop: `${3 * s}px solid #FFFFFF`, boxShadow: `0 -${10 * s}px ${30 * s}px #0005` }} />
  </>);
};
const Tile: React.FC<{ id: string; x: number; y: number; w: number; h: number; bg: string; k?: number; label?: string; fs?: number; live?: boolean }> = ({ id, x, y, w, h, bg, k = 0, label, fs = 46, live = true }) => {
  const kk = k % 4; const car = CAR[kk];
  // the 2380:1200 picture box covering the tile
  const bw = Math.max(w, h * PA), bh = bw / PA, bx = (w - bw) / 2, by = (h - bh) / 2;
  return (
  <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, overflow: 'hidden', borderRadius: 24, background: `linear-gradient(160deg,${bg},#1C1C1C)`, boxShadow: '0 10px 30px #0008' }}>
    <div style={{ position: 'absolute', left: bx, top: by, width: bw, height: bh }}>
      {car ? (<>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg,#24262B,#101114)' }} />
        <Founder id={car.id} h={bh * car.fh} x={bw * car.fx} y={bh * car.fy} rim={false} shadow={false} flip={car.flip} />
        <Img src={staticFile(car.img)} style={{ position: 'absolute', inset: 0, width: bw, height: bh }} />
      </>) : (<>
        <Room4 k={kk} w={bw} h={bh} />
        <Founder id={id} h={bh * 1.05} x={bw / 2} y={bh * 0.08} rim={false} shadow={false} />
        {kk === 0 && bh > 480 && <div style={{ position: 'absolute', right: 40 * bh / 600, top: 40 * bh / 600, padding: `${8 * bh / 600}px ${22 * bh / 600}px`, borderRadius: 14 * bh / 600, background: '#7A0A1A', border: `${4 * bh / 600}px solid #FF5B6E`, boxShadow: '0 0 40px #FF5B6E' }}><T cap={34 * bh / 600} fam="anton" c="#FFD2D8" style={{ letterSpacing: 3 }}>ON AIR</T></div>}
        {kk === 1 && bh > 480 && <div style={{ position: 'absolute', right: 40 * bh / 600, bottom: 190 * bh / 600, width: 300 * bh / 600, height: 140 * bh / 600, background: '#fff', borderRadius: 16 * bh / 600, boxShadow: '0 6px 0 #0003', transform: 'rotate(-3deg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><T cap={34} fam="anton" c="#5E4F40" style={{ textAlign: 'center', lineHeight: 1.15, letterSpacing: 2 }}>DO NOT<br />DISTURB</T></div>}
      </>)}
    </div>
    {live && <div style={{ position: 'absolute', left: 16, top: 14, display: 'flex', alignItems: 'center', gap: 10, background: '#000A', padding: '6px 18px', borderRadius: 12 }}><div style={{ width: 16, height: 16, borderRadius: 8, background: '#FF3B55' }} /><T cap={fs * 0.7} c="#fff">REC</T></div>}
    {label && <div style={{ position: 'absolute', left: 16, bottom: 14, right: 16, background: '#000A', padding: '12px 24px 18px', borderRadius: 12 }}><T cap={fs} c="#fff">{label}</T></div>}
  </div>);
};
export const K20: React.FC = () => {
  const f = useCurrentFrame(); const n = Math.min(4, 1 + Math.floor(f / 14));
  return (
    <Canvas bg="#1A1A1A"><Abs x={60} y={36}><T cap={52} c="#BDBDBD">PODCAST · LIVE FROM EVERYWHERE</T></Abs>
      {GT.slice(0, n).map((id, i) => <Tile key={id} id={id} x={60 + (i % 2) * 1250} y={140 + Math.floor(i / 2) * 640} w={1190} h={600} bg={GBG[i]} k={i} label={['The studio', 'Hotel bed', 'Passenger seat', 'Driving (hands-free)'][i]} />)}
    </Canvas>
  );
};
export const K20b: React.FC = () => {
  const f = useCurrentFrame(); const g = f < 30 ? 1 : f < 62 ? 2 : 4; const ids = ['F06', 'F21', 'F22', 'F23', 'F12', 'F13', 'F16', 'F24', 'F25', 'F20', 'F17', 'F18', 'F28', 'F30', 'F15', 'F08'];
  const tw = (W - 60 - g * 20) / g, th = (H - 60 - g * 20) / g;
  return (
    <Canvas bg="#1A1A1A">{Array.from({ length: g * g }).map((_, i) => <Tile key={i} id={ids[i % 16]} x={30 + (i % g) * (tw + 20) + 0} y={30 + Math.floor(i / g) * (th + 20)} w={tw} h={th} bg={GBG[i % 4]} k={i} live={g < 4} label={g === 4 ? EPS[i % 8] : g === 2 ? EPS[i % 8] : undefined} fs={g === 4 ? 46 : 60} />)}</Canvas>
  );
};
