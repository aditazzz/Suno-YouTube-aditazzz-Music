// 7A / 7B / 7C (cut 5; plan §3: 3136-3205 / 3205-3275 / 3275-3344; N31-N34): her phone, a photo app's stories in the layout
// everyone knows (no app logo or wordmark), one screen per shot, each held still so the jokes read (N32/N34 "stay here so we can
// see the joke"). Names per her N31/N33: him `Claude ShipIt!` / `claude.shipit`, Cooper `coop.the.dood.le`.
//   7A  the stories row only (full handles, not truncated), framed close; his ring pulses on the beats; her tap on the last beat (3188).
//   7B  his story, held, its progress bar running: him with other tenants' parcels (story still: B's when it lands, else
//       cut 4e's l3/stories/story3.jpg, the parcel-with-a-bow one).
//   7C  "Opened a new chat": a new DM to him, header `Claude ShipIt!` / Active now; her three messages land on 3275 / 3286 / 3297,
//       `Seen just now` on 3305 and holds 1.3 s into the cut (plan: >= 1.2 s).
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { F } from '../../blocks/real/tokens';
import { Avatar, StoryView } from '../../blocks/real/Stories';
import { IcCamera, IcChevDown, IcChevLeft, IcHeart, IcImage, IcMic, IcPhone, IcSend, IcVideo } from '../../blocks/real/Icons';
import { SOCIAL } from '../../blocks/real/script';
import { PhoneStage, clamp, loc, pop } from './kit';

export const S7 = { PULSE: [3136, 3153, 3170], TAP: 3188, DM: [3275, 3286, 3297], SEEN: 3305 };
export const STORY_SRC = 'l3/stories/story3.jpg';      // swap for B's story still (public/c5/7B/...) when it lands
export const AV = { her: 'l3/av/her.jpg', him: 'l3/av/robot.jpg', cooper: 'l3/av/cooper.jpg', jo: 'l3/av/jo.jpg' };

/** the stories row, full handles (the tray scrolled to show four) */
export const StoryRow5: React.FC<{ pulse: number; press: number }> = ({ pulse, press }) => {
  const rings = [{ name: 'Your story', src: AV.her, you: true }, { name: SOCIAL.him, src: AV.him }, { name: SOCIAL.cooper, src: AV.cooper }, { name: SOCIAL.jo, src: AV.jo, seen: true }];
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: '#fff', fontFamily: F.ios, color: '#000', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', left: 16, right: 16, top: 56, height: 44, display: 'flex', alignItems: 'center', gap: 4 }}>
        <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.02em' }}>Following</div><IcChevDown s={18} w={2} />
        <div style={{ flex: 1 }} /><IcHeart s={26} w={1.8} /><div style={{ width: 18 }} /><IcSend s={25} w={1.8} />
      </div>
      <div style={{ position: 'absolute', left: 2, top: 108, display: 'flex' }}>
        {rings.map((r, i) => (
          <div key={i} style={{ width: 97, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
            <div style={{ transform: `scale(${i === 1 ? 1 + 0.05 * pulse : 1})` }}>
              <Avatar src={r.src} d={74} ring={!r.you} seen={r.seen} press={i === 1 ? press : 0} />
            </div>
            <div style={{ fontSize: 11.5, letterSpacing: '-0.02em', color: r.seen ? '#8E8E93' : '#000', width: 97, textAlign: 'center', whiteSpace: 'nowrap' }}>{r.name}</div>
          </div>
        ))}
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 226, height: 0.5, background: '#DBDBDB' }} />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 238 }}>
        <Img src={staticFile('l3/stories/story1.jpg')} style={{ width: 393, height: 393, objectFit: 'cover', filter: 'blur(1px)' }} />
      </div>
    </div>
  );
};

const S7A: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const pulse = S7.PULSE.map((F) => loc(shot, F)).reduce((m, b) => Math.max(m, f >= b && f < b + 10 ? Math.sin(((f - b) / 10) * Math.PI) : 0), 0);
  const tap = loc(shot, S7.TAP); const press = f >= tap && f < tap + 6 ? Math.sin(((f - tap) / 6) * Math.PI) : 0;
  return (
    <PhoneStage f={f} dur={shot.dur} k0={5.6} k1={5.75} focus0={168} focus1={168} time="4:24" seed={41} rot={-0.4}>
      <StoryRow5 pulse={pulse} press={press} />
    </PhoneStage>
  );
};
const S7B: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  return (
    <PhoneStage f={f} dur={shot.dur} k0={2.62} k1={2.7} focus0={330} focus1={330} time="4:24" seed={43} rot={-0.6} dark>
      <StoryView src={STORY_SRC} handle={SOCIAL.him} avatar={AV.him} when="2h" bars={3} at={2 + clamp(f / (shot.dur - 1)) * 0.9} />
    </PhoneStage>
  );
};
/** a NEW conversation (the app's DM look, as Stories.DMView): the header (name, Active now), the profile intro the app shows at the
 *  top of a new chat (big photo, name, handle), and her messages right under it (top-anchored: a new chat), Seen under the last */
export const NewDM: React.FC<{ n: number; seen: boolean; pop?: number }> = ({ n, seen, pop = 1 }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: '#fff', fontFamily: F.ios, color: '#000', overflow: 'hidden' }}>
    <div style={{ position: 'absolute', left: 0, right: 0, top: 54, height: 58, display: 'flex', alignItems: 'center', gap: 10, padding: '0 12px', borderBottom: '0.5px solid #EFEFEF' }}>
      <IcChevLeft s={28} w={2} /><Avatar src={AV.him} d={40} dot />
      <div style={{ lineHeight: 1.2 }}><div style={{ fontSize: 16, fontWeight: 600 }}>{SOCIAL.himName}</div><div style={{ fontSize: 13, color: '#8E8E93' }}>Active now</div></div>
      <div style={{ flex: 1 }} /><IcPhone s={24} w={1.8} /><div style={{ width: 14 }} /><IcVideo s={27} w={1.8} />
    </div>
    <div style={{ position: 'absolute', left: 0, right: 0, top: 132, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <Avatar src={AV.him} d={88} />
      <div style={{ fontSize: 20, fontWeight: 700, marginTop: 8 }}>{SOCIAL.himName}</div>
      <div style={{ fontSize: 14, color: '#8E8E93' }}>{SOCIAL.him}</div>
      <div style={{ marginTop: 8, padding: '7px 16px', borderRadius: 9, background: '#EFEFEF', fontSize: 14, fontWeight: 600 }}>View profile</div>
    </div>
    <div style={{ position: 'absolute', left: 14, right: 14, top: 352, display: 'flex', flexDirection: 'column', gap: 5 }}>
      {SOCIAL.dm.slice(0, n).map((m, i) => (
        <div key={i} style={{ alignSelf: 'flex-end', maxWidth: '84%', borderRadius: 26, padding: '12px 18px', fontSize: 20.8, color: '#fff',   // rl7_rb W14: 1.3x
          background: 'linear-gradient(135deg,#5B51F7,#8B3FE6 60%,#A93BD8)', borderBottomRightRadius: i === n - 1 ? 8 : 26,
          transformOrigin: '100% 100%', transform: i === n - 1 ? `scale(${0.6 + 0.4 * pop})` : undefined }}>{m}</div>
      ))}
      {seen ? <div style={{ alignSelf: 'flex-end', fontSize: 13.5, color: '#8E8E93', marginTop: 2 }}>{SOCIAL.seen}</div> : null}
    </div>
    <div style={{ position: 'absolute', left: 12, right: 12, bottom: 34, height: 44, borderRadius: 22, background: '#EFEFEF', display: 'flex', alignItems: 'center', gap: 10, padding: '0 6px' }}>
      <div style={{ width: 34, height: 34, borderRadius: 17, background: '#3797F0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><IcCamera s={20} c="#fff" /></div>
      <div style={{ flex: 1, fontSize: 15, color: '#8E8E93' }}>Message…</div><IcMic s={22} /><IcImage s={22} /><div style={{ width: 6 }} />
    </div>
  </div>
);

const S7C: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame();
  const n = S7.DM.filter((F) => f >= loc(shot, F)).length;
  return (
    <PhoneStage f={f} dur={shot.dur} k0={2.6} k1={2.68} focus0={306} focus1={310} time="4:25" seed={45} rot={-0.6}>
      <NewDM n={Math.max(1, n)} seen={f >= loc(shot, S7.SEEN)} pop={clamp(pop(f, Math.max(...S7.DM.map((F) => loc(shot, F)).filter((x) => f >= x), 0), 8))} />
    </PhoneStage>
  );
};
export const C5_7A: ShotDef = { stage: S7A, cx916: () => 0.5 };
export const C5_7B: ShotDef = { stage: S7B, cx916: () => 0.5 };
export const C5_7C: ShotDef = { stage: S7C, cx916: () => 0.5 };
