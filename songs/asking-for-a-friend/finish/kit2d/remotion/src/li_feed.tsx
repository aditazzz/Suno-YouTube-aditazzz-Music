// ROUND 4 (fix_realapp): LIGHT mode like the real app; post photos in real colours (dusk, gym), no ultraviolet.
// ROUND 3 (fix_platforms): the rest of his feed posts, from a generic photo app ("thefounder", hearts) to LinkedIn posts in dark mode,
// so his whole feed is ONE real-looking platform (the lyric names LinkedIn twice; carousels and photo posts are LinkedIn's native
// founder genre). The approved media, timing and jokes are kept inside the post: K07 burn selfie, K14 5AM carousel (now LinkedIn's
// document carousel, "6 / 6"), K16 gym post (B, two tiny pink dumbbells) with its stopwatch.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C, W, ease, lin } from './theme';
import { Canvas, Founder, Avatar, Heart, T, Abs } from './ui';
import { Sky } from './scenes';
import { Burn, ThirdEye } from './items_a';
import { k14Slide } from './items_b';
import { LiNight, LI, LT, Ico, LiAuthor, LiActions, LiCounts } from './li';

const Post: React.FC<{ x: number; w: number; children?: React.ReactNode }> = ({ x, w, children }) => (
  <div style={{ position: 'absolute', left: x, top: 40, width: w, height: 1360, borderRadius: 24, background: LI.card, overflow: 'hidden', boxShadow: LI.cardShadow }}>{children}</div>
);

// ---------------------------------------------------------------- K07 · the burn selfie
export const K07: React.FC = () => {
  const f = useCurrentFrame(); const z = 1 + 0.05 * (f / 74); const burst = ease(f, 61, 72);
  const sc = 0.75, bx = (1400 - 1080 * sc) / 2, by = 3;
  return (
    <Canvas bg={LI.canvas}>
      <Post x={580} w={1400}>
        <div style={{ position: 'absolute', left: 56, top: 40 }}><LiAuthor avatar={<Avatar id="F01" size={150} bg={LI.card2} />} name="The Founder" headline="Founder · Visionary · Thought leader" when="2h" /></div>
        <div style={{ position: 'absolute', right: 56, top: 56 }}>{Ico.dots({ s: 70 })}</div>
        <div style={{ position: 'absolute', left: 56, top: 312 }}><LT cap={56}>Found myself. 🙏 Back to building.</LT></div>
        <div style={{ position: 'absolute', left: 0, top: 410, width: 1400, height: 740, overflow: 'hidden' }}>
          <div style={{ position: 'absolute', inset: 0, transform: `scale(${z})`, transformOrigin: '50% 60%' }}>
            <Sky a="#2F4A78" b="#C98A7A" c="#FFC08A" />
            <div style={{ position: 'absolute', left: 0, right: 0, top: by + 620 * sc, bottom: 0, background: 'linear-gradient(180deg,#C08458,#7A4A36)' }} />
            <div style={{ position: 'absolute', left: bx, top: by, width: 1080, height: 980, transform: `scale(${sc})`, transformOrigin: '0 0' }}>
              <svg style={{ position: 'absolute', left: 250, top: 400, width: 140, height: 240 }} viewBox="0 0 140 240"><path d="M70 10 L90 70 L130 90 L100 110 L108 170 L70 130 L32 170 L40 110 L10 90 L50 70Z" fill="#5A3A24" opacity=".9" /><rect x="64" y="130" width="12" height="100" fill="#5A3A24" /></svg>
              <Burn f={f} />
              <ThirdEye f={f} />
              <Founder id="F07" h={900} x={620} y={160} />
            </div>
          </div>
          {burst > 0 && [0, 1, 2, 3, 4, 5].map((i) => { const a = i * 60 * Math.PI / 180; return <div key={i} style={{ position: 'absolute', left: 700 + Math.cos(a) * 520 * burst - 50, top: 370 + Math.sin(a) * 290 * burst - 50, opacity: 1 - burst * 0.4 }}><Heart s={100 * (0.6 + burst)} c={LI.love} /></div>; })}
        </div>
        <div style={{ position: 'absolute', left: 56, top: 1172 }}><LiCounts w={1288} n={burst > 0 ? '4,812' : '4,811'} comments="312 comments · 48 reposts" /></div>
        <div style={{ position: 'absolute', left: 56, right: 56, top: 1246, height: 2, background: LI.line }} />
        <div style={{ position: 'absolute', left: 0, top: 1256, width: 1400, height: 96, display: 'flex', alignItems: 'center' }}><LiActions w={1400} liked={burst > 0} /></div>
      </Post>
      <LiNight />
    </Canvas>
  );
};

// ---------------------------------------------------------------- K14 · the 5AM carousel as a LinkedIn document post (slide 6 shown)
const Dots: React.FC<{ n: number; i: number }> = ({ n, i }) => (<div style={{ display: 'flex', gap: 18 }}>{Array.from({ length: n }).map((_, k) => <div key={k} style={{ width: k === i ? 30 : 18, height: 18, borderRadius: 9, background: k === i ? LI.text : '#B0B0B0' }} />)}</div>);
export const K14: React.FC = () => {
  const slide = k14Slide;
  const f = useCurrentFrame(); const idx = Math.min(5, Math.floor(f / 16)); const sw = ease(f - idx * 16, 0, 8); const prev = Math.max(0, idx - 1);
  const ss = 650 / 1080, sx = (1400 - 650) / 2;
  return (
    <Canvas bg={LI.canvas}>
      <Post x={580} w={1400}>
        <div style={{ position: 'absolute', left: 56, top: 40 }}><LiAuthor avatar={<Avatar id="F01" size={150} bg={LI.card2} />} name="The Founder" headline="Founder · Visionary · Thought leader" when="1d" /></div>
        <div style={{ position: 'absolute', right: 56, top: 56 }}>{Ico.dots({ s: 70 })}</div>
        <div style={{ position: 'absolute', left: 56, top: 312 }}><LT cap={56}>My 5AM routine 🧠 Save this.</LT></div>
        <div style={{ position: 'absolute', left: 0, top: 410, width: 1400, height: 740, background: '#E9E5DF', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', left: 0, top: 0, width: 1400, height: 104, background: 'rgba(255,255,255,.94)', borderBottom: `2px solid ${LI.line}`, display: 'flex', alignItems: 'center', padding: '0 40px', boxSizing: 'border-box' }}><LT cap={46} c={LI.text} w={600}>My 5AM routine · 6 pages</LT></div>
          <div style={{ position: 'absolute', left: sx, top: 100, width: 1080, height: 1080, transform: `scale(${ss})`, transformOrigin: '0 0', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', inset: 0, transform: `translateX(${-1080 * sw}px)` }}>{slide(prev === idx ? idx : prev)}</div>
            <div style={{ position: 'absolute', inset: 0, transform: `translateX(${1080 * (1 - sw)}px)` }}>{slide(idx)}</div>
          </div>
          {[0, 1].map((k) => <div key={k} style={{ position: 'absolute', left: k ? 1400 - 60 - 110 : 60, top: 85 + 325 - 55, width: 110, height: 110, borderRadius: 55, background: 'rgba(0,0,0,.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: k ? 'rotate(-90deg)' : 'rotate(90deg)' }}>{Ico.caret({ s: 64, c: '#fff' })}</div>)}
          <div data-fit="pager" style={{ position: 'absolute', right: 40, top: 740 - 116, height: 100, padding: '0 34px', borderRadius: 50, background: 'rgba(0,0,0,.7)', display: 'flex', alignItems: 'center' }}><LT cap={46} c="#fff" w={600}>{idx + 1} / 6</LT></div>
          <div style={{ position: 'absolute', left: 40, top: 740 - 70 }}><Dots n={6} i={idx} /></div>
        </div>
        <div style={{ position: 'absolute', left: 56, top: 1172 }}><LiCounts w={1288} n="8,204" comments="641 comments · 97 reposts" /></div>
        <div style={{ position: 'absolute', left: 56, right: 56, top: 1246, height: 2, background: LI.line }} />
        <div style={{ position: 'absolute', left: 0, top: 1256, width: 1400, height: 96, display: 'flex', alignItems: 'center' }}><LiActions w={1400} /></div>
      </Post>
      <LiNight />
    </Canvas>
  );
};

// ---------------------------------------------------------------- K16 · the gym post (B) beside its stopwatch
export const K16: React.FC = () => {
  const f = useCurrentFrame(); const s = lin(f, 18, 38, 0, 2400); const mm = Math.floor(s / 60), ss = Math.floor(s % 60);
  return (
    <Canvas bg={LI.canvas}>
      <Post x={(W - 1080) / 2 - 560} w={1080}>
        <div style={{ position: 'absolute', left: 48, top: 40 }}><LiAuthor avatar={<Avatar id="F01" size={150} bg={LI.card2} />} name="The Founder" headline="Founder · Visionary · Thoug…" when="3h" /></div>
        <div style={{ position: 'absolute', left: 48, top: 304 }}><LT cap={56}>40 min. No days off. 💪</LT></div>
        <div style={{ position: 'absolute', left: 0, top: 394, width: 1080, height: 710, overflow: 'hidden', background: 'linear-gradient(180deg,#7C838B,#4A4F56 70%,#33363B)' }}><Founder id="F17B" h={750} x={540} y={-14} /></div>
        <div style={{ position: 'absolute', left: 48, top: 1122 }}><LiCounts w={984} n="12,431" comments="418 comments" /></div>
        <div style={{ position: 'absolute', left: 48, right: 48, top: 1196, height: 2, background: LI.line }} />
        <div style={{ position: 'absolute', left: 0, top: 1208, width: 1080, height: 140, display: 'flex', alignItems: 'center' }}><LiActions w={1080} compact /></div>
      </Post>
      {/* round 4: the stopwatch is his phone's stopwatch app (black, white digits), so it reads on LinkedIn's light canvas */}
      <div style={{ position: 'absolute', left: 1300, top: 190, width: 1180, height: 860, borderRadius: 64, background: '#000', boxShadow: '0 30px 70px rgba(0,0,0,.30)' }} />
      <Abs x={1300} y={290} w={1180} style={{ textAlign: 'center' }}><T cap={360} fam="anton" c="#fff" style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>{String(mm).padStart(2, '0')}:{String(ss).padStart(2, '0')}</T></Abs>
      <Abs x={1300} y={820} w={1180} style={{ textAlign: 'center' }}><T cap={80} fam="anton" c="#FFE56B" style={{ textAlign: 'center', letterSpacing: 8 }}>STOPWATCH</T></Abs>
      <LiNight />
    </Canvas>
  );
};
