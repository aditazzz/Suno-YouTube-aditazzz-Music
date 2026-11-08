import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { C, D, F, W, H, fsForCap, ease, pop, lin, fmt } from './theme';
import { NightBg, Canvas, T, Abs, Bezel, Caret, Avatar } from './ui';

// K-S1 chat on the boardroom screen. Round 4 (her note: the post-it didn't make sense): Claude asks the question in
// #leadership; the founder starts typing ... and leaves the channel. The members panel fills the right third and drops 2 -> 1.
// Timing (local frames, sung: Asking -4, for 4, a 16, friend 22, How 39): typed f1-16, typing dots f18-24, LEFT at f25, held.
export const KS1: React.FC = () => {
  const f = useCurrentFrame(); const l1 = 'asking for a friend:'; const l2 = 'how does this thing end?'; const all = l1.length + l2.length;
  const n = Math.round(lin(f, 1, 16, 0, all)); const t1 = l1.slice(0, n), t2 = l2.slice(0, Math.max(0, n - l1.length)); const typing = n < all;
  const dots = f >= 18 && f < 25; const left = f >= 25; const lp = pop(f, 25, 7); const gone = ease(f, 26, 34);
  return (
    <Canvas bg="#000"><Bezel>
      <div style={{ position: 'absolute', inset: 0, background: '#F4F2EE' }} />
      <div style={{ position: 'absolute', left: 0, top: 0, right: 0, height: 190, background: '#E6E2DA' }}><Abs x={0} y={96} w={W}><T cap={54} c="#2A2833" style={{ textAlign: 'center' }}>Boardroom · #leadership</T></Abs></div>
      {/* chat column */}
      <Abs x={170} y={250} w={1530} style={{ display: 'flex', gap: 40, alignItems: 'flex-start' }}>
        <div style={{ width: 190, height: 190, borderRadius: 36, overflow: 'hidden', flex: 'none', border: `6px solid ${C.claude}`, background: '#14131A' }}><Img src={staticFile('stills/CLAUDE_face.png')} style={{ width: 190, height: 190, objectFit: 'cover', objectPosition: '50% 20%' }} /></div>
        <div data-fit="bubble" style={{ background: '#fff', borderRadius: 40, padding: '40px 56px 44px', boxShadow: '0 3px 0 #D8D3C8', width: 1300, boxSizing: 'border-box' }}><T cap={34} c="#9A958A" w={600} style={{ marginBottom: 16 }}>Claude</T><T cap={58} c="#2A2833" w={500} style={{ lineHeight: 1.3, whiteSpace: 'nowrap' }}>{t1}{n <= l1.length && typing && <Caret f={f} h={74} c={C.claude} />}<br />{t2}{n > l1.length && typing && <Caret f={f} h={74} c={C.claude} />}{'\u00a0'}</T></div>
      </Abs>
      {/* the founder's reply that never comes */}
      <Abs x={400} y={690} w={1340} h={130} style={{ display: 'flex', alignItems: 'center', gap: 30, opacity: Math.min(ease(f, 17, 21), left ? 0 : 1) }}>
        <Avatar id="F01" size={110} ring={C.uv} /><T cap={46} c="#6B6580" w={600}>The Founder is typing</T><T cap={46} c={C.uv} w={800} style={{ letterSpacing: 6 }}>{'.'.repeat(1 + (Math.floor(f / 3) % 3))}</T>
      </Abs>
      {left && <Abs x={400} y={690} w={1340} h={130} style={{ display: 'flex', alignItems: 'center', gap: 30, opacity: lp, transform: `translateY(${(1 - lp) * 20}px)` }}>
        <div style={{ width: 110, height: 110, borderRadius: 55, background: C.uvPale, border: `5px solid ${C.uv}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none' }}><T cap={52} c={C.uv} w={800}>←</T></div>
        <T cap={58} c={C.uv} w={800}>The Founder left #leadership</T>
      </Abs>}
      {/* members panel: the right third */}
      <div data-fit="members" style={{ position: 'absolute', left: 1770, top: 250, width: 620, height: 720, boxSizing: 'border-box', padding: '40px 44px', background: '#ECE8E0', borderRadius: 36 }}>
        <T cap={38} c="#6B6580" w={700} style={{ letterSpacing: 4 }}>MEMBERS · {left && gone > 0.5 ? 1 : 2}</T>
        <div style={{ display: 'flex', alignItems: 'center', gap: 26, marginTop: 44 }}>
          <div style={{ width: 110, height: 110, borderRadius: 26, overflow: 'hidden', flex: 'none', border: `5px solid ${C.claude}`, background: '#14131A' }}><Img src={staticFile('stills/CLAUDE_face.png')} style={{ width: 110, height: 110, objectFit: 'cover', objectPosition: '50% 20%' }} /></div>
          <div><T cap={44} c="#2A2833" w={700}>Claude</T><T cap={34} c="#1E8F5C" w={600} style={{ marginTop: 10 }}>● online</T></div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 26, marginTop: 40, opacity: 1 - gone, transform: `translateX(${gone * 24}px)`, visibility: gone >= 1 ? 'hidden' : 'visible' }}>
          <Avatar id="F01" size={110} ring={C.uv} />
          <div><T cap={44} c="#2A2833" w={700}>The Founder</T><T cap={34} c="#6B6580" w={600} style={{ marginTop: 10 }}>on a podcast</T></div>
        </div>
        <div style={{ position: 'absolute', left: 44, right: 44, top: 470, borderTop: '3px solid #D8D3C8' }} />
        <Abs x={44} y={510}><T cap={34} c="#6B6580" w={700} style={{ letterSpacing: 4 }}>CHANNEL OWNER</T></Abs>
        {f < 30 && <Abs x={44} y={580} style={{ opacity: 1 - ease(f, 26, 30) }}><T cap={50} c="#2A2833" w={700}>The Founder</T></Abs>}
        {f >= 30 && <Abs x={44} y={580} style={{ opacity: pop(f, 30, 6), transform: `scale(${0.9 + 0.1 * pop(f, 30, 6)})`, transformOrigin: 'left center' }}><T cap={50} c={C.red} w={800}>nobody</T></Abs>}
      </div>
      <Abs x={170} y={1020} w={2220} h={150} style={{ background: '#fff', borderRadius: 40, border: '4px solid #D8D3C8', display: 'flex', alignItems: 'center', padding: '0 56px', boxSizing: 'border-box' }}><T cap={46} c="#9A958A" w={500}>Message #leadership</T></Abs>
    </Bezel></Canvas>
  );
};
// K-S2 paper form + DENIED stamp
export const KS2: React.FC = () => {
  const f = useCurrentFrame(); const hit = f >= 34; const st = pop(f, 34, 6);
  return (
    <Canvas bg="#2A2420"><div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 40%,#4A3F36,#1C1814)' }} />
      <div style={{ position: 'absolute', left: 560, top: 70, width: 1440, height: 1300, background: '#F4EEDD', boxShadow: '0 30px 80px #000A', transform: 'rotate(-1.2deg)', backgroundImage: 'repeating-linear-gradient(0deg,transparent 0 58px,#E4DCC6 58px 60px)' }}>
        <Abs x={90} y={80}><T cap={48} c="#2A2833" style={{ fontFamily: F.stencil, letterSpacing: 4, fontWeight: 400 }}>PRODUCTION ACCESS REQUEST</T></Abs>
        <Abs x={90} y={260}><T cap={52} c="#2A2833">Requester: <span style={{ fontFamily: F.caveat, fontSize: 96, fontWeight: 500, color: '#1B3FA8' }}>Claude (contractor)</span></T></Abs>
        <Abs x={90} y={440}><T cap={52} c="#2A2833">Reason: keep it running</T></Abs>
        <Abs x={90} y={620}><T cap={52} c="#2A2833">Status: <span style={{ color: hit ? '#9A958A' : C.red }}>UNKNOWN</span></T></Abs>
        {hit && <div style={{ position: 'absolute', left: 110, top: 760, width: 1220, height: 400, border: `22px solid ${C.red}`, borderRadius: 24, transform: `rotate(-9deg) scale(${1.25 - 0.25 * st})`, opacity: st * 0.92, display: 'flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box' }}><T cap={250} fam="anton" c={C.red} style={{ letterSpacing: 10 }}>DENIED</T></div>}
      </div>
    </Canvas>
  );
};
// K-S3 deploy pipeline (machine voice)
export const KS3: React.FC = () => {
  const f = useCurrentFrame(); const steps = [['BUILD', 'OK', '#E6B24C'], ['TESTS (0)', 'OK', '#E6B24C'], ['DEPLOY', 'OK', '#E6B24C'], ['???', '', C.red]];
  return (
    <Canvas bg="#000"><Bezel glow="#FFB13B">
      <div style={{ position: 'absolute', inset: 0, background: '#0A0804' }} />
      <Abs x={170} y={130}><T cap={60} fam="vt" c={C.amber} style={{ letterSpacing: 6 }}>PIPELINE · prod-main</T></Abs>
      {steps.map(([a, b, c], i) => { const on = pop(f, 6 + i * 9, 8); return (
        <div key={i}>
          <Abs x={170 + i * 560} y={420} w={480} h={480} style={{ border: `8px solid ${c}`, borderRadius: 22, opacity: on, transform: `translateY(${(1 - on) * 30}px)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><T cap={72} fam="mono" c={c} style={{ textAlign: 'center' }}>{a}</T></Abs>
          {i < 3 && <Abs x={170 + i * 560 + 490} y={640} style={{ opacity: on }}><T cap={72} fam="vt" c={C.amber}>→</T></Abs>}
        </div>); })}
      <Abs x={170} y={1010}><T cap={56} fam="vt" c={C.amber}>deploying to prod<Caret f={f} h={60} /></T></Abs>
    </Bezel></Canvas>
  );
};
// K-S4 memoir chat from @founder
export const KS4: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <Canvas bg="#000"><Bezel>
      <div style={{ position: 'absolute', inset: 0, background: '#14161C' }} />
      <Abs x={170} y={130} style={{ display: 'flex', gap: 34, alignItems: 'center' }}><Avatar id="F01" size={130} ring="#2A2F3A" /><T cap={56} c="#E6EDF3">@founder</T><T cap={46} c="#7A8594" w={500}>typing…</T></Abs>
      <Abs x={170} y={430} w={1800}><div style={{ background: '#2B3040', borderRadius: 40, padding: '56px 80px', display: 'inline-block', opacity: pop(f, 3, 8) }}><T cap={110} c="#fff" w={500}>can u write my memoir?</T></div></Abs>
      <Abs x={170} y={1000} w={1800} h={160} style={{ border: '4px solid #2A2F3A', borderRadius: 40, display: 'flex', alignItems: 'center', padding: '0 56px', boxSizing: 'border-box' }}><T cap={52} c={C.claude} style={{ fontFamily: F.caveat, fontSize: 84, fontWeight: 500 }}><Caret f={f} h={70} c={C.claude} /></T></Abs>
    </Bezel></Canvas>
  );
};
// K-S5 net profit dashboard
export const KS5: React.FC = () => {
  const f = useCurrentFrame(); const t = ease(f, 14, 30); const v = Math.round(-12004 + t * (12004 + 1204)); const pos = v >= 0;
  return (
    <Canvas bg="#000"><Bezel>
      <div style={{ position: 'absolute', inset: 0, background: '#0F1218' }} />
      <Abs x={170} y={130}><T cap={52} c="#8B96A5" style={{ letterSpacing: 8 }}>NET PROFIT · THIS QUARTER</T></Abs>
      <Abs x={170} y={330}><T cap={300} fam="anton" c={pos ? C.green : C.red} style={{ fontVariantNumeric: 'tabular-nums' }}>{pos ? '+' : '-'}${fmt(Math.abs(v))}</T></Abs>
      <svg style={{ position: 'absolute', left: 170, top: 800, width: 2200, height: 400 }} viewBox="0 0 2200 400"><path d="M0 330 C300 360 500 380 800 300 S1300 180 1600 140 S2000 60 2200 30" stroke={pos ? C.green : C.red} strokeWidth="14" fill="none" strokeDasharray={`${t * 2400} 2400`} /></svg>
      <Abs x={1500} y={1230}><T cap={48} c="#8B96A5" w={500}>somehow</T></Abs>
    </Bezel></Canvas>
  );
};
// K-S6 all systems green (hard cut to black at the end)
export const KS6: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <Canvas bg="#000"><Bezel glow="#9BFFD0">
      <div style={{ position: 'absolute', inset: 0, background: '#07140E' }} />
      <Abs x={0} y={320} w={W} style={{ textAlign: 'center' }}><T cap={230} fam="anton" c={C.green} style={{ textAlign: 'center', letterSpacing: 6 }}>ALL SYSTEMS</T><T cap={230} fam="anton" c={C.green} style={{ textAlign: 'center', letterSpacing: 6 }}>GREEN</T></Abs>
      <Abs x={170} y={130}><T cap={52} fam="mono" c="#4AA880">status.prod · uptime 100%</T></Abs>
      {[0, 1, 2, 3, 4, 5].map((i) => <div key={i} style={{ position: 'absolute', left: 340 + i * 330, top: 1120, width: 24, height: 24, borderRadius: 12, background: C.green, boxShadow: `0 0 ${12 + 8 * Math.sin(f / 5 + i)}px ${C.green}` }} />)}
    </Bezel></Canvas>
  );
};
// K-S7 valuation board
export const KS7: React.FC = () => {
  const f = useCurrentFrame(); const v = Math.round(lin(f, 20, 80, 12000000, 400000000));
  return (
    <Canvas bg="#000"><Bezel>
      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(160deg,#2B0F73,#12082F)' }} />
      <Abs x={170} y={150}><T cap={56} c="#B9A0FF" style={{ letterSpacing: 10 }}>VALUATION</T></Abs>
      <Abs x={170} y={360}><T cap={290} fam="anton" c="#fff" style={{ fontVariantNumeric: 'tabular-nums' }}>${fmt(v)}</T></Abs>
      <Abs x={170} y={820}><T cap={96} fam="anton" c="#FFE56B">+3,233% SINCE JANUARY</T></Abs>
      <Abs x={170} y={1060}><T cap={50} c="#8A98E0" w={500}>company voice · board deck · confidential</T></Abs>
    </Bezel></Canvas>
  );
};
// K-S8 Claude's phone keypad: 9-1-1, the orange finger hovers over CALL and does not press
export const KS8: React.FC = () => {
  const f = useCurrentFrame(); const digits = f < 22 ? 0 : f < 44 ? 1 : f < 66 ? 2 : 3; const hover = ease(f, 70, 92);
  const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];
  return (
    <Canvas bg="#000"><Bezel>
      <div style={{ position: 'absolute', inset: 0, background: '#101218' }} />
      <Abs x={780} y={110} w={1000} style={{ textAlign: 'center' }}><T cap={150} fam="inter" c="#fff" w={500} style={{ textAlign: 'center', letterSpacing: 18, paddingLeft: 18, height: 160 }}>{'911'.slice(0, digits).split('').join('')}</T></Abs>
      <Abs x={1000} y={330} w={560} h={640} style={{ display: 'flex', flexWrap: 'wrap', gap: 24 }}>{keys.map((k) => <div key={k} style={{ width: 166, height: 140, borderRadius: 70, background: k === '9' || k === '1' ? '#3A4050' : '#232733', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><T cap={56} c="#fff">{k}</T></div>)}</Abs>
      <Abs x={1090} y={1030} w={380} h={170} style={{ background: '#F2EBDD', borderRadius: 90, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><T cap={56} c="#2A2833">CALL</T></Abs>
      <div style={{ position: 'absolute', left: 1460 + (1 - hover) * 700, top: 1180 - hover * 60 - 120, width: 150, height: 330, borderRadius: 75, background: 'linear-gradient(90deg,#F2EBDD,#D6CDB8)', transform: 'rotate(-28deg)', boxShadow: '0 20px 40px #0008' }}><div style={{ position: 'absolute', left: 0, top: 0, width: 150, height: 120, borderRadius: 75, background: C.claude }} /></div>
      <Abs x={1760} y={420} w={640}><T cap={110} fam="caveat" c={C.claude} style={{ lineHeight: 1 }}>…not yet.</T></Abs>
    </Bezel></Canvas>
  );
};
// K-S9 the team's screen: Unfollow pressed
export const KS9: React.FC = () => {
  const f = useCurrentFrame(); const press = ease(f, 3, 9); const toast = pop(f, 8, 6);
  return (
    <Canvas bg="#000"><Bezel>
      <div style={{ position: 'absolute', inset: 0, background: '#F4F2EE' }} />
      <Abs x={170} y={160} style={{ display: 'flex', gap: 50, alignItems: 'center' }}><Avatar id="F01" size={260} ring="#D8D3C8" /><div><T cap={96} fam="anton" c="#2A2833">THE FOUNDER</T><T cap={50} c="#6B6580" w={500}>12,551 followers</T></div></Abs>
      <Abs x={1600} y={190}><div style={{ padding: '36px 110px', borderRadius: 80, background: f < 7 ? '#fff' : '#E6E2DA', border: '5px solid #2A2833', transform: `scale(${1 - 0.05 * press})` }}><T cap={60} c="#2A2833">{f < 7 ? 'Following' : 'Unfollow'}</T></div></Abs>
      <Abs x={560} y={1060} w={1400} h={140} style={{ background: '#2A2833', borderRadius: 70, opacity: toast, transform: `translateY(${(1 - toast) * 40}px)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><T cap={52} c="#fff">You unfollowed The Founder</T></Abs>
      <div style={{ position: 'absolute', left: 1860 - press * 0, top: 400 - 0, width: 130, height: 300, borderRadius: 65, background: 'linear-gradient(90deg,#F2EBDD,#D6CDB8)', transform: `rotate(-12deg) translateY(${-110 * (1 - press) }px)`, boxShadow: '0 20px 40px #0006' }}><div style={{ position: 'absolute', left: 0, top: 0, width: 130, height: 90, borderRadius: 65, background: C.claude }} /></div>
    </Bezel></Canvas>
  );
};
