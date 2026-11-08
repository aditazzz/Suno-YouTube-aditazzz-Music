// ROUND 4 (fix_realapp, CD, Nov 7 20:00): LIGHT mode, see LI below; the round-3 dark-mode notes that follow are history.
// ROUND 3 (fix_platforms, CD, Nov 7): "for things like LinkedIn it should actually look like LinkedIn" (her round-2 overall note).
// The professional network as it really looks in DARK MODE (LinkedIn has one; the film is night, and the feed was approved dark):
// grey #1B1F23 cards on a near-black canvas, light-blue #71B7FB primary actions with dark text (the dark-mode version of #0A66C2),
// system-UI type (SF on the Mac, like the real site), the top nav with labelled icons, the profile header (banner, overlapping round
// avatar, name + connection degree, headline, location · Contact info, followers · connections, Follow / Message / More), the post card
// (author row, body, media, reaction cluster, Like / Comment / Repost / Send) and the "Create a post" composer.
// YouTube-safe: no logo, no wordmark, no "in" square anywhere; layout, colour, type and the lyric carry it. The founder's own colour
// lives where the real site lets a user put colour: his ultraviolet banner and his portrait.
// Self-contained (React only) so the kit and the screens project share it: avatars come in as nodes, the scale comes from LiScale.
import React from 'react';

export const LI = {
  // ROUND 4 (her "Real-app colors", Nov 7 19:38): LIGHT mode like the real app. Off-white #F4F2EE canvas, white cards, #0A66C2 blue
  // filled primary pills with white text, near-black text, #666 secondary. No ultraviolet anywhere (his banner is a muted default-style one).
  canvas: '#F4F2EE', card: '#FFFFFF', card2: '#E9E5DF', line: '#E0DFDC', input: '#EDF3F8',
  text: '#191919', sub: '#666666', mute: '#8C8C8C', blue: '#0A66C2', blueDeep: '#004182', btnText: '#FFFFFF',
  like: '#378FE9', celebrate: '#6DAE4F', love: '#DF704D', green: '#057642', red: '#CC1016',
  banner: 'linear-gradient(100deg,#8FA6B8 0%,#A9BCCB 50%,#C9D5DE 100%)',
  pressed: '#D0E8FF', cardShadow: '0 0 0 2px #E0DFDC, 0 6px 18px rgba(0,0,0,.08)',
};
export const SYS = "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, 'Helvetica Neue', 'Inter', sans-serif";
const CAP_SYS = 0.705; // SF Pro cap height / em
/** layout scale divisor (1 in the kit's full-frame feeds; the Monitor's S in the screens project, where the layout is scaled into a room) */
export const LiScale = React.createContext(1);

/** text by FINAL cap height in px on the 2560x1440 frame */
export const LT: React.FC<{ cap: number; c?: string; w?: number; style?: React.CSSProperties; children?: React.ReactNode; fit?: string }> = ({ cap, c = LI.text, w = 400, style, children, fit }) => {
  const s = React.useContext(LiScale);
  return <div data-fit={fit} style={{ fontFamily: SYS, fontSize: Math.round(cap / s / CAP_SYS), fontWeight: w, color: c, lineHeight: 1.18, letterSpacing: -0.2, whiteSpace: 'nowrap', ...style }}>{children}</div>;
};
const px = (n: number) => n; // layout px (already in the 2560 layout space)

// ---------------------------------------------------------------- icons: generic line icons (no brand marks)
type IP = { s: number; c?: string; fill?: string };
export const Ico = {
  search: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke={c} strokeWidth="2.2" /><path d="M15.5 15.5L21 21" stroke={c} strokeWidth="2.4" strokeLinecap="round" /></svg>,
  home: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M3 11.2L12 4l9 7.2V21h-6v-6H9v6H3z" fill={c} /></svg>,
  network: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill={c}><circle cx="8.5" cy="7.5" r="3.6" /><path d="M1.5 20c0-4 3.1-7 7-7s7 3 7 7z" /><circle cx="17" cy="8.5" r="3" /><path d="M16.5 13.2c3.4 0 6 2.6 6 6.3h-5.3c0-2.4-.4-4.6-.7-6.3z" /></svg>,
  jobs: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill={c}><path d="M9 3h6a2 2 0 0 1 2 2v2h3.5A1.5 1.5 0 0 1 22 8.5V19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.5A1.5 1.5 0 0 1 3.5 7H7V5a2 2 0 0 1 2-2zm0 2v2h6V5z" /></svg>,
  msg: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" fill={c} /><path d="M7 9h10M7 13h7" stroke={LI.card} strokeWidth="1.8" strokeLinecap="round" /></svg>,
  bell: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill={c}><path d="M12 2.5a6.5 6.5 0 0 1 6.5 6.5v4.6l2 3.4v1H3.5v-1l2-3.4V9A6.5 6.5 0 0 1 12 2.5z" /><path d="M9.5 19.5h5a2.5 2.5 0 0 1-5 0z" /></svg>,
  thumb: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M7 10.5V21H3.5V10.5zM7 10.5l4.2-7.2c1.4 0 2.3 1.1 2.1 2.5L12.7 9h6.1a2 2 0 0 1 2 2.4l-1.5 7.6a2.5 2.5 0 0 1-2.4 2H7" fill="none" stroke={c} strokeWidth="1.9" strokeLinejoin="round" /></svg>,
  comment: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M5 4h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-7l-5 4v-4H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" fill="none" stroke={c} strokeWidth="1.9" strokeLinejoin="round" /></svg>,
  repost: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><path d="M4 11V8a2 2 0 0 1 2-2h12l-3-3M20 13v3a2 2 0 0 1-2 2H6l3 3" /></svg>,
  send: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M21.5 2.5L2.5 10l7.5 3 3 7.5z" fill="none" stroke={c} strokeWidth="1.9" strokeLinejoin="round" /><path d="M10 13l5-5" stroke={c} strokeWidth="1.9" strokeLinecap="round" /></svg>,
  globe: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.8"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3.2 3 14.8 0 18M12 3c-3 3.2-3 14.8 0 18" /></svg>,
  plus: ({ s, c = LI.btnText }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M12 4v16M4 12h16" stroke={c} strokeWidth="2.8" strokeLinecap="round" /></svg>,
  check: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M4.5 12.5l5 5 10-11" fill="none" stroke={c} strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" /></svg>,
  dots: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill={c}><circle cx="5" cy="12" r="2.2" /><circle cx="12" cy="12" r="2.2" /><circle cx="19" cy="12" r="2.2" /></svg>,
  close: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M5 5l14 14M19 5L5 19" stroke={c} strokeWidth="2.4" strokeLinecap="round" /></svg>,
  chart: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill={c}><rect x="3" y="13" width="4" height="8" rx="1" /><rect x="10" y="8" width="4" height="13" rx="1" /><rect x="17" y="3" width="4" height="18" rx="1" /></svg>,
  image: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.9"><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9.5" r="1.8" /><path d="M21 16l-5-5-9 9" /></svg>,
  smile: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.9"><circle cx="12" cy="12" r="9" /><path d="M8 14.5c1 1.5 2.3 2.2 4 2.2s3-.7 4-2.2" strokeLinecap="round" /><circle cx="9" cy="9.5" r="1" fill={c} /><circle cx="15" cy="9.5" r="1" fill={c} /></svg>,
  clock: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.9"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3.5 2" strokeLinecap="round" /></svg>,
  cap: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24" fill={c}><path d="M12 4L1.5 9 12 14l8.5-4v6h2V9z" /><path d="M6 12.5V16c0 1.5 2.7 3 6 3s6-1.5 6-3v-3.5l-6 2.9z" /></svg>,
  caret: ({ s, c = LI.sub }: IP) => <svg width={s} height={s} viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" fill="none" stroke={c} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg>,
};
/** the three-reaction cluster (like / celebrate / love), overlapping circles */
export const ReactCluster: React.FC<{ d: number }> = ({ d }) => {
  const one = (bg: string, glyph: React.ReactNode, i: number) => (
    <div key={i} style={{ width: d, height: d, borderRadius: '50%', background: bg, border: `${Math.round(d * 0.07)}px solid ${LI.card}`, marginLeft: i ? -d * 0.28 : 0, display: 'flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box', zIndex: 3 - i }}>{glyph}</div>
  );
  return <div data-fit="off" style={{ display: 'flex' }}>
    {one(LI.like, <svg width={d * 0.56} height={d * 0.56} viewBox="0 0 24 24"><path d="M7 10.5V21H3.5V10.5zM8.5 10.5l3.7-7c1.4 0 2.3 1.1 2.1 2.5L13.7 9h5.1a2 2 0 0 1 2 2.4l-1.5 7.6a2.5 2.5 0 0 1-2.4 2H8.5z" fill="#fff" /></svg>, 0)}
    {one(LI.celebrate, <svg width={d * 0.56} height={d * 0.56} viewBox="0 0 24 24" fill="#fff"><path d="M8 21l-5-5 7.5-10.5 8 8z" /><circle cx="18" cy="5" r="1.6" /><circle cx="20.5" cy="9.5" r="1.2" /><circle cx="14.5" cy="3" r="1.2" /></svg>, 1)}
    {one(LI.love, <svg width={d * 0.56} height={d * 0.56} viewBox="0 0 24 24"><path fill="#fff" d="M12 21s-8-5.2-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 5.8-8 11-8 11z" /></svg>, 2)}
  </div>;
};

// ---------------------------------------------------------------- the top nav: search + labelled icons (labels at the 46 px cap floor)
const NAV: [string, keyof typeof Ico][] = [['Home', 'home'], ['My Network', 'network'], ['Messaging', 'msg'], ['Notifications', 'bell']];
export const LiNav: React.FC<{ h?: number; active?: string; me?: React.ReactNode; badge?: string; x0?: number; x1?: number; drop?: string[] }> = ({ h = 196, active = 'Home', me, badge = '9+', x0 = 160, x1 = 2400, drop = [] }) => {
  const items = NAV.filter(([l]) => !drop.includes(l));
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: h, background: LI.card, borderBottom: `2px solid ${LI.line}` }}>
      <div data-fit="search" style={{ position: 'absolute', left: x0, top: (h - 100) / 2, width: 520, height: 100, borderRadius: 10, background: LI.input, display: 'flex', alignItems: 'center', gap: 26, padding: '0 34px', boxSizing: 'border-box' }}>
        {Ico.search({ s: 54, c: LI.sub })}<LT cap={46} c={LI.sub}>Search</LT>
      </div>
      <div style={{ position: 'absolute', right: 2560 - x1, top: 0, height: h, display: 'flex', alignItems: 'flex-end', gap: 70 }}>
        {items.map(([lab, ic]) => {
          const on = lab === active; const c = on ? LI.text : LI.sub;
          return <div key={lab} style={{ height: h, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10, position: 'relative', boxShadow: on ? `inset 0 -6px 0 ${LI.text}` : undefined, padding: '0 6px' }}>
            {Ico[ic]({ s: 66, c })}<LT cap={46} c={c} w={on ? 600 : 400}>{lab}</LT>
            {lab === 'Notifications' && badge && <div data-fit="off" style={{ position: 'absolute', left: '56%', top: 22, minWidth: 54, height: 54, borderRadius: 27, background: '#CB112D', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 10px', boxSizing: 'border-box' }}><LT cap={28} c="#fff" w={700}>{badge}</LT></div>}
          </div>;
        })}
        <div style={{ height: h, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
          <div style={{ width: 66, height: 66, borderRadius: '50%', overflow: 'hidden', background: LI.input }}>{me}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}><LT cap={46} c={LI.sub}>Me</LT>{Ico.caret({ s: 40 })}</div>
        </div>
      </div>
    </div>
  );
};

/** a pill button: primary (filled blue, dark text), outline (blue ring), ghost (grey ring) */
export const LiBtn: React.FC<{ kind?: 'primary' | 'outline' | 'ghost' | 'pressed'; cap?: number; icon?: React.ReactNode; children?: React.ReactNode; style?: React.CSSProperties }> = ({ kind = 'primary', cap = 46, icon, children, style }) => {
  const s = React.useContext(LiScale); const h = Math.round(cap / s * 2.5); const bw = Math.max(3, Math.round(cap / s * 0.085));
  const bg = kind === 'primary' ? LI.blue : kind === 'pressed' ? LI.pressed : 'transparent';
  const bc = kind === 'ghost' ? LI.sub : LI.blue; const tc = kind === 'primary' ? LI.btnText : kind === 'ghost' ? LI.sub : LI.blue;
  return <div data-fit="btn" style={{ height: h, borderRadius: h / 2, background: bg, border: `${bw}px solid ${bc}`, display: 'inline-flex', alignItems: 'center', gap: Math.round(h * 0.16), padding: `0 ${Math.round(h * 0.52)}px`, boxSizing: 'border-box', ...style }}>
    {icon}<LT cap={cap} c={tc} w={600}>{children}</LT>
  </div>;
};

// ---------------------------------------------------------------- profile header
export type ProfileP = {
  x: number; y: number; w: number; h: number; bannerH: number; avD: number; avatar: React.ReactNode;
  name: string; nameCap: number; degree?: string; headline: React.ReactNode; headCap: number; headC?: string;
  stats?: React.ReactNode; loc?: boolean; buttons?: React.ReactNode; right?: React.ReactNode; gap?: number;
};
export const LiProfile: React.FC<ProfileP> = ({ x, y, w, h, bannerH, avD, avatar, name, nameCap, degree = '3rd+', headline, headCap, headC = LI.text, stats, loc = true, buttons, right, gap = 0 }) => {
  const ax = 90, ay = bannerH - avD * 0.55;
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: 24, background: LI.card, overflow: 'hidden', boxShadow: LI.cardShadow }}>
      <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: bannerH, background: LI.banner }}>
        <svg style={{ position: 'absolute', left: 0, top: 0 }} width={w} height={bannerH} viewBox={`0 0 ${w} ${bannerH}`}>{Array.from({ length: 9 }).map((_, i) => <circle key={i} cx={w * 0.66} cy={bannerH * 1.3} r={140 + i * 120} fill="none" stroke="#fff" strokeOpacity={0.07} strokeWidth="3" />)}</svg>
      </div>
      <div style={{ position: 'absolute', left: ax, top: ay, width: avD, height: avD, borderRadius: '50%', border: `${Math.round(avD * 0.03)}px solid ${LI.card}`, overflow: 'hidden', background: LI.card2, boxSizing: 'border-box' }}>{avatar}</div>
      {right && <div style={{ position: 'absolute', right: 110, top: ay + avD + 30 }}>{right}</div>}
      <div style={{ position: 'absolute', left: ax, top: ay + avD + 24, display: 'flex', flexDirection: 'column', gap }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 22 }}><LT cap={nameCap} w={600}>{name}</LT>{degree && <LT cap={46} c={LI.sub}>· {degree}</LT>}</div>
        <div style={{ marginTop: Math.round(headCap * 0.35) }}><LT cap={headCap} c={headC}>{headline}</LT></div>
        {loc && <div style={{ display: 'flex', gap: 18, marginTop: 34 }}><LT cap={46} c={LI.sub}>Austin, Texas ·</LT><LT cap={46} c={LI.blue} w={600}>Contact info</LT></div>}
        {stats && <div style={{ marginTop: 22 }}>{stats}</div>}
        {buttons && <div style={{ display: 'flex', gap: 28, marginTop: 44 }}>{buttons}</div>}
      </div>
    </div>
  );
};
/** the right column of a profile: current company (redacted on purpose: "building in stealth") and school */
export const LiRightCol: React.FC = () => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 26 }}><div style={{ width: 76, height: 76, borderRadius: 10, background: '#191919', boxShadow: `inset 0 0 0 2px ${LI.line}` }} /><div style={{ width: 330, height: 50, borderRadius: 6, background: '#191919', boxShadow: `inset 0 0 0 2px ${LI.line}` }} /></div>
    <div style={{ display: 'flex', alignItems: 'center', gap: 26 }}><div style={{ width: 76, height: 76, borderRadius: 10, background: LI.input, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{Ico.cap({ s: 52, c: LI.sub })}</div><LT cap={46} c={LI.text} w={600}>Dropped out</LT></div>
  </div>
);

// ---------------------------------------------------------------- post parts
export const LiAuthor: React.FC<{ avatar: React.ReactNode; avD?: number; name: string; you?: boolean; headline: string; when: string; dots?: boolean }> = ({ avatar, avD = 150, name, you, headline, when, dots = true }) => (
  <div style={{ display: 'flex', gap: 34, alignItems: 'center', position: 'relative' }}>
    <div style={{ width: avD, height: avD, borderRadius: '50%', overflow: 'hidden', background: LI.card2, flex: 'none' }}>{avatar}</div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16 }}><LT cap={50} w={600}>{name}</LT>{you && <LT cap={46} c={LI.sub}>· You</LT>}</div>
      <LT cap={46} c={LI.sub}>{headline}</LT>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}><LT cap={46} c={LI.sub}>{when} ·</LT>{Ico.globe({ s: 50 })}</div>
    </div>
  </div>
);
export const LiActions: React.FC<{ w: number; liked?: boolean; compact?: boolean }> = ({ w, liked, compact }) => {
  const a: [keyof typeof Ico, string][] = [['thumb', 'Like'], ['comment', 'Comment'], ['repost', 'Repost'], ['send', 'Send']];
  return <div style={{ width: w, display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
    {a.map(([ic, lab]) => <div key={lab} style={{ display: 'flex', flexDirection: compact ? 'column' : 'row', alignItems: 'center', gap: compact ? 6 : 20 }}>{Ico[ic]({ s: 64, c: liked && lab === 'Like' ? LI.blue : LI.sub })}<LT cap={46} c={liked && lab === 'Like' ? LI.blue : LI.sub} w={600}>{lab}</LT></div>)}
  </div>;
};

/** reaction cluster + count, and "N comments · N reposts" on the right */
export const LiCounts: React.FC<{ w: number; n: string; comments?: string }> = ({ w, n, comments }) => (
  <div style={{ width: w, display: 'flex', alignItems: 'center', gap: 16 }}><ReactCluster d={58} /><LT cap={46} c={LI.sub}>{n}</LT><div style={{ flex: 1 }} />{comments && <LT cap={46} c={LI.sub}>{comments}</LT>}</div>
);

/** ROUND 4: light LinkedIn in the film's night. The page is his phone/laptop screen at 2 AM: display at night brightness (~16% down)
 *  with a soft falloff to the edges, the way a bright screen reads in a dark room. Then the grade's shoulder (white -> 0.935) and
 *  vignette on top. Put it LAST inside a full-frame LinkedIn item. Off for the in-building monitors (the room does that job). */
export const LiNight: React.FC = () => (
  <div data-fit="off" style={{ position: 'absolute', inset: 0, pointerEvents: 'none', background: 'radial-gradient(ellipse 75% 70% at 50% 46%, rgba(10,12,18,.12) 0%, rgba(10,12,18,.18) 62%, rgba(10,12,18,.36) 100%)' }} />
);
