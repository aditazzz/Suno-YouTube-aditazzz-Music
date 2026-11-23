// A photo app's stories, the layout everyone knows by heart (FIX4_PLAN §2e: real layout, NO app logo or wordmark):
//  StoryTray  = the feed's top: "Following" header, the row of story rings (gradient ring = unseen), names under them.
//  StoryView  = full-screen story: segmented progress bars, avatar + handle + time, the photo, "Send message" bar.
//  DMView     = a direct-message thread: header (avatar, handle, "Active now" + green dot), her outgoing bubbles, "Seen".
// All in iOS points (393 x 852). Images are public/ paths.
import React from 'react';
import { Img, staticFile } from 'remotion';
import { F } from './tokens';
import { IcCamera, IcChevDown, IcChevLeft, IcHeart, IcImage, IcMic, IcPhone, IcSend, IcVideo, IcX, IcDots } from './Icons';

// rl7_rb (PLAN7 W13, brand rule: no real-brand marks): an unseen story is a plain solid ring, not the app's gradient
const RING = '#F2643A';
export const Avatar: React.FC<{ src: string; d: number; ring?: boolean; seen?: boolean; press?: number; dot?: boolean; bg?: string }> = ({ src, d, ring, seen, press = 0, dot, bg = '#fff' }) => (
  <div style={{ position: 'relative', width: d, height: d, transform: `scale(${1 - 0.07 * press})` }}>
    {ring ? <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: seen ? '#C7C7CC' : RING }} /> : null}
    <div style={{ position: 'absolute', inset: ring ? d * 0.045 : 0, borderRadius: '50%', background: bg }} />
    <Img src={staticFile(src)} style={{ position: 'absolute', inset: ring ? d * 0.09 : 0, width: ring ? d * 0.82 : d, height: ring ? d * 0.82 : d, borderRadius: '50%', objectFit: 'cover' }} />
    {dot ? <div style={{ position: 'absolute', right: d * 0.02, bottom: d * 0.02, width: d * 0.28, height: d * 0.28, borderRadius: '50%', background: '#2BD15A', border: `${d * 0.05}px solid ${bg}` }} /> : null}
  </div>
);

export type Ring = { name: string; src: string; seen?: boolean; you?: boolean };
export const StoryTray: React.FC<{ rings: Ring[]; press?: { i: number; k: number }; feed?: string }> = ({ rings, press, feed }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: '#fff', fontFamily: F.ios, color: '#000', overflow: 'hidden' }}>
    <div style={{ position: 'absolute', left: 16, right: 16, top: 56, height: 44, display: 'flex', alignItems: 'center', gap: 4 }}>
      <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.02em' }}>Following</div><IcChevDown s={18} w={2} />
      <div style={{ flex: 1 }} /><IcHeart s={26} w={1.8} /><div style={{ width: 18 }} /><IcSend s={25} w={1.8} />
    </div>
    <div style={{ position: 'absolute', left: 10, top: 108, display: 'flex', gap: 14 }}>
      {rings.map((r, i) => (
        <div key={i} style={{ width: 76, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
          <Avatar src={r.src} d={76} ring={!r.you} seen={r.seen} press={press && press.i === i ? press.k : 0} />
          <div style={{ fontSize: 12, color: r.seen ? '#8E8E93' : '#000', width: 76, textAlign: 'center', whiteSpace: 'nowrap' }}>{r.you ? 'Your story' : r.name.length > 11 ? `${r.name.slice(0, 10)}…` : r.name}</div>
        </div>
      ))}
    </div>
    <div style={{ position: 'absolute', left: 0, right: 0, top: 226, height: 0.5, background: '#DBDBDB' }} />
    {feed ? (
      <div style={{ position: 'absolute', left: 0, right: 0, top: 238 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 12px 10px' }}>
          <Avatar src="l3/av/jo.jpg" d={34} ring /><div style={{ fontSize: 14, fontWeight: 600 }}>jo.builds</div><div style={{ flex: 1 }} /><IcDots s={20} />
        </div>
        <Img src={staticFile(feed)} style={{ width: 393, height: 393, objectFit: 'cover' }} />
      </div>
    ) : null}
  </div>
);

/** a story, full screen: n bars with `at` (index + fraction) progress; open 0..1 grows it out of the tray avatar */
export const StoryView: React.FC<{ src: string; handle: string; avatar: string; when: string; bars: number; at: number; caption?: React.ReactNode }> = ({ src, handle, avatar, when, bars, at, caption }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: '#000', fontFamily: F.ios, color: '#fff', overflow: 'hidden' }}>
    <div style={{ position: 'absolute', left: 0, right: 0, top: 50, bottom: 86, borderRadius: 10, overflow: 'hidden' }}>
      <Img src={staticFile(src)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 120, background: 'linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0))' }} />
      {caption}
    </div>
    <div style={{ position: 'absolute', left: 8, right: 8, top: 58, display: 'flex', gap: 4 }}>
      {Array.from({ length: bars }, (_, i) => (
        <div key={i} style={{ flex: 1, height: 2.5, borderRadius: 2, background: 'rgba(255,255,255,0.38)', overflow: 'hidden' }}>
          <div style={{ width: `${Math.max(0, Math.min(1, at - i)) * 100}%`, height: '100%', background: '#fff' }} />
        </div>
      ))}
    </div>
    <div style={{ position: 'absolute', left: 12, right: 12, top: 70, display: 'flex', alignItems: 'center', gap: 9 }}>
      <Avatar src={avatar} d={32} />
      <div style={{ fontSize: 14, fontWeight: 600, textShadow: '0 1px 2px rgba(0,0,0,0.3)' }}>{handle}</div>
      <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.75)' }}>{when}</div>
      <div style={{ flex: 1 }} /><IcDots s={22} c="#fff" /><div style={{ width: 8 }} /><IcX s={24} c="#fff" w={2} />
    </div>
    <div style={{ position: 'absolute', left: 12, right: 12, bottom: 30, display: 'flex', alignItems: 'center', gap: 14 }}>
      <div style={{ flex: 1, height: 44, borderRadius: 22, border: '1px solid rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', padding: '0 18px', fontSize: 15, color: 'rgba(255,255,255,0.9)' }}>Send message</div>
      <IcHeart s={27} c="#fff" w={1.8} /><IcSend s={26} c="#fff" w={1.8} />
    </div>
  </div>
);

export const DMView: React.FC<{ handle: string; name: string; avatar: string; active: boolean; mine: string[]; seen?: string; theirs?: string[]; typing?: boolean }> = ({ handle, name, avatar, active, mine, seen, theirs = [] }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: '#fff', fontFamily: F.ios, color: '#000', overflow: 'hidden' }}>
    <div style={{ position: 'absolute', left: 0, right: 0, top: 54, height: 58, display: 'flex', alignItems: 'center', gap: 10, padding: '0 12px', borderBottom: '0.5px solid #EFEFEF' }}>
      <IcChevLeft s={28} w={2} />
      <Avatar src={avatar} d={40} dot={active} />
      <div style={{ lineHeight: 1.2 }}>
        <div style={{ fontSize: 16, fontWeight: 600 }}>{name}</div>
        <div style={{ fontSize: 13, color: '#8E8E93' }}>{active ? 'Active now' : handle}</div>
      </div>
      <div style={{ flex: 1 }} /><IcPhone s={24} w={1.8} /><div style={{ width: 14 }} /><IcVideo s={27} w={1.8} />
    </div>
    <div style={{ position: 'absolute', left: 14, right: 14, bottom: 96, display: 'flex', flexDirection: 'column', gap: 4 }}>
      {theirs.map((m, i) => <div key={`t${i}`} style={{ alignSelf: 'flex-start', maxWidth: '72%', background: '#EFEFEF', borderRadius: 20, padding: '9px 14px', fontSize: 16 }}>{m}</div>)}
      {mine.map((m, i) => (
        <div key={i} style={{ alignSelf: 'flex-end', maxWidth: '72%', borderRadius: 20, padding: '9px 14px', fontSize: 16, color: '#fff',
          background: 'linear-gradient(135deg,#5B51F7,#8B3FE6 60%,#A93BD8)', borderBottomRightRadius: i === mine.length - 1 ? 6 : 20 }}>{m}</div>
      ))}
      {seen ? <div style={{ alignSelf: 'flex-end', fontSize: 12, color: '#8E8E93', marginTop: 2 }}>{seen}</div> : null}
    </div>
    <div style={{ position: 'absolute', left: 12, right: 12, bottom: 34, height: 44, borderRadius: 22, background: '#EFEFEF', display: 'flex', alignItems: 'center', gap: 10, padding: '0 6px' }}>
      <div style={{ width: 34, height: 34, borderRadius: 17, background: '#3797F0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><IcCamera s={20} c="#fff" /></div>
      <div style={{ flex: 1, fontSize: 15, color: '#8E8E93' }}>Message…</div>
      <IcMic s={22} /><IcImage s={22} /><div style={{ width: 6 }} />
    </div>
  </div>
);
