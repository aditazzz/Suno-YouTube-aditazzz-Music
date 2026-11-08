// ROUND 4 (fix_realapp): LIGHT mode like the real app (her "Real-app colors"); same layout, copy and timing as round 3.
// ROUND 3 (fix_platforms): the three founder screens the lyric says are LinkedIn, rebuilt to look like LinkedIn (dark mode).
// K08 "His LinkedIn says 'building in stealth'" (S055) · K25 "He has just posted on LinkedIn:" (S142) · K26 "The team has unfollowed him" (S148)
// Timing, jokes and key frames are the approved round-2 ones; only the platform look changed.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ease, pop, lin, fmt } from './theme';
import { Canvas, Founder, Avatar } from './ui';
import { LiNight, LI, LT, Ico, LiNav, LiBtn, LiProfile, LiRightCol, LiAuthor, LiActions } from './li';

const Page: React.FC<{ children?: React.ReactNode; dim?: number }> = ({ children }) => <div style={{ position: 'absolute', inset: 0, background: LI.canvas }}>{children}</div>;

// ---------------------------------------------------------------- K08 · the profile header, "Building in stealth." types on the sung words
export const K08: React.FC = () => {
  const f = useCurrentFrame(); const s = 0.95 + 0.05 * pop(f, 0, 10);
  const words = ['Building', 'in', 'stealth.']; const on = [9, 12, 15];
  return (
    <Canvas bg={LI.canvas}><Page />
      <div style={{ position: 'absolute', inset: 0, transform: `scale(${s})` }}>
        <LiNav active="" me={<Avatar id="F08" size={66} zoom={1.25} cy={0.36} />} />
        <LiProfile x={160} y={236} w={2240} h={1260} bannerH={300} avD={360} gap={0}
          avatar={<Avatar id="F08" size={340} zoom={1.25} cy={0.36} bg={LI.card2} />}
          name="The Founder" nameCap={76}
          headline={<span>{words.map((wd, i) => <span key={i} style={{ opacity: ease(f, on[i], on[i] + 2) }}>{wd}{i < 2 ? ' ' : ''}</span>)}</span>} headCap={96}
          stats={<div style={{ display: 'flex', gap: 18 }}><LT cap={46} c={LI.sub}>12,551 followers ·</LT><LT cap={46} c={LI.blue} w={600}>500+ connections</LT></div>}
          right={<LiRightCol />}
          buttons={<><LiBtn kind="primary" icon={Ico.plus({ s: 50 })}>Follow</LiBtn><LiBtn kind="outline">Message</LiBtn><LiBtn kind="ghost">More</LiBtn></>}
        />
      </div>
      <LiNight />
    </Canvas>
  );
};

// ---------------------------------------------------------------- K25 · "Create a post" -> posting -> the post: 0 impressions
export const K25: React.FC = () => {
  const f = useCurrentFrame(); const msg = "Couldn't have done it without my incredible team 🙏"; const n = Math.round(lin(f, 10, 80, 0, msg.length));
  const phase = f < 85 ? 0 : f < 142 ? 1 : 2;
  const me = <Avatar id="F28" size={66} zoom={2.1} cy={0.3} />;
  if (phase === 0) return (
    <Canvas bg={LI.canvas}><Page />
      <LiNav me={me} />
      <div style={{ position: 'absolute', left: 420, top: 236, width: 1720, height: 1300, borderRadius: 24, background: LI.card }} />
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,.62)' }} />
      <div style={{ position: 'absolute', left: 400, top: 150, width: 1760, height: 1140, borderRadius: 24, background: LI.card, boxShadow: '0 24px 60px rgba(0,0,0,.28)' }}>
        <div style={{ position: 'absolute', left: 64, top: 56, display: 'flex', gap: 34, alignItems: 'center' }}>
          <div style={{ width: 150, height: 150, borderRadius: '50%', overflow: 'hidden', background: LI.card2 }}><Avatar id="F28" size={150} zoom={2.1} cy={0.3} /></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}><div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><LT cap={56} w={600}>The Founder</LT>{Ico.caret({ s: 56, c: LI.text })}</div><LT cap={46} c={LI.sub}>Post to Anyone</LT></div>
        </div>
        <div style={{ position: 'absolute', right: 64, top: 70 }}>{Ico.close({ s: 70 })}</div>
        <div style={{ position: 'absolute', left: 64, top: 300, width: 1630 }}><LT cap={72} style={{ whiteSpace: 'normal', lineHeight: 1.32 }}>{msg.slice(0, n)}<span style={{ display: 'inline-block', width: 8, height: 104, background: LI.blue, marginLeft: 6, verticalAlign: 'text-bottom', opacity: Math.floor(f / 6) % 2 === 0 ? 1 : 0.1 }} /></LT></div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 930, height: 2, background: LI.line }} />
        <div style={{ position: 'absolute', left: 64, top: 990, display: 'flex', gap: 56 }}>{Ico.smile({ s: 70 })}{Ico.image({ s: 70 })}{Ico.chart({ s: 70 })}</div>
        <div style={{ position: 'absolute', right: 64, top: 965, display: 'flex', gap: 44, alignItems: 'center' }}>{Ico.clock({ s: 70 })}<LiBtn kind="primary" cap={52}>Post</LiBtn></div>
      </div>
      <LiNight />
    </Canvas>
  );
  const prog = lin(f, 85, 140);
  return (
    <Canvas bg={LI.canvas}><Page />
      <LiNav me={me} />
      <div style={{ position: 'absolute', left: 420, top: 236, width: 1720, height: 1180, borderRadius: 24, background: LI.card, overflow: 'hidden', boxShadow: LI.cardShadow }}>
        {phase === 1 && <div style={{ position: 'absolute', left: 0, top: 0, height: 10, width: 1720 * prog, background: LI.blue }} />}
        <div style={{ position: 'absolute', left: 60, top: 50 }}><LiAuthor avatar={<Avatar id="F28" size={150} zoom={2.1} cy={0.3} />} name="The Founder" you headline="Founder · Visionary · Thought leader" when="Now" /></div>
        <div style={{ position: 'absolute', right: 60, top: 64 }}>{Ico.dots({ s: 70 })}</div>
        <div style={{ position: 'absolute', left: 60, top: 322, width: 1600 }}><LT cap={64} style={{ whiteSpace: 'normal', lineHeight: 1.3 }}>{msg}</LT></div>
        <div style={{ position: 'absolute', left: 0, top: 560, width: 1720, height: 384, background: 'linear-gradient(160deg,#4E6A80,#9FB3C2 55%,#E3C7A4)', overflow: 'hidden' }}><Founder id="F27" h={640} x={860} y={-14} /></div>
        <div style={{ position: 'absolute', left: 0, top: 960, width: 1720, height: 96, display: 'flex', alignItems: 'center' }}><LiActions w={1720} /></div>
        <div style={{ position: 'absolute', left: 60, right: 60, top: 1066, height: 2, background: LI.line }} />
        <div style={{ position: 'absolute', left: 60, right: 60, top: 1080, height: 90, display: 'flex', alignItems: 'center', gap: 24 }}>
          {phase === 2 ? <>{Ico.chart({ s: 60, c: LI.sub })}<LT cap={56} w={600}>0 impressions</LT><div style={{ flex: 1 }} /><LT cap={46} c={LI.blue} w={600}>View analytics</LT></>
            : <LT cap={46} c={LI.sub}>Posting…</LT>}
        </div>
      </div>
      <LiNight />
    </Canvas>
  );
};

// ---------------------------------------------------------------- K26 · 12,551 followers -> 0, Following -> Follow
export const K26: React.FC = () => {
  const f = useCurrentFrame(); const n = Math.round(12551 * (1 - ease(f, 4, 22))); const swap = f >= 20;
  const av = swap ? 'F29' : 'F01';
  return (
    <Canvas bg={LI.canvas}><Page />
      <LiNav active="" me={<Avatar id="F01" size={66} zoom={2.0} cy={0.3} />} badge="" />
      <LiProfile x={160} y={236} w={2240} h={1260} bannerH={300} avD={340}
        avatar={<Avatar id={av} size={320} zoom={2.0} cy={swap ? 0.45 : 0.3} bg={LI.card2} />}
        name="The Founder" nameCap={76} headline="Founder · Visionary · Thought leader" headCap={50} loc={false}
        stats={<div style={{ display: 'flex', alignItems: 'baseline', gap: 30 }}>
          <LT cap={150} w={700} c={swap ? LI.red : LI.text} style={{ fontVariantNumeric: 'tabular-nums', filter: f > 4 && f < 22 ? 'blur(6px)' : 'none' }}>{fmt(n)}</LT>
          <LT cap={64} c={LI.sub}>followers</LT></div>}
        right={<LiRightCol />}
        buttons={swap ? <><LiBtn kind="primary" icon={Ico.plus({ s: 50 })}>Follow</LiBtn><LiBtn kind="outline">Message</LiBtn></>
          : <><LiBtn kind="outline" icon={Ico.check({ s: 50, c: LI.blue })}>Following</LiBtn><LiBtn kind="outline">Message</LiBtn></>}
      />
      <LiNight />
    </Canvas>
  );
};
