// 9A / 9E1 TV screen (cut 5; plan §3: 9A f4246-4385, 9E1 f4593-4662; N42, N44): a live news broadcast at 4:41 AM with the real
// headline verbatim and its source (memory "real headlines welcome"): `LIVE 4:41 AM` · `Microsoft Outlook outage stretches on` ·
// `Source: ABC7 Los Angeles, Nov 13, 2026`. A generic news look (no channel logo, no brand mark: the bug is our own plain "LIVE").
// On 9E1's first beat (4593) the headline FLASHES (the lower third wipes in again, a white flash), the beat the streamers burst on (4610).
//   <ScreenInsert corners={A2's tv quad} w={TVW} h={TVH} light={0.9}><NewsTV f={f} from={shot.from} /></ScreenInsert>
import React from 'react';
import { F } from '../../blocks/real/tokens';
import { TV } from '../../blocks/real/script';
import { clamp, ez } from './kit';

export const TVW = 1600, TVH = 900;
export const TV9 = { FLASH: 4593, BURST: 4610 };   // absolute

export const NewsTV: React.FC<{ f: number; from: number }> = ({ f, from }) => {
  const g = f + from;                                   // film frame
  const flash = g >= TV9.FLASH ? 1 - clamp((g - TV9.FLASH) / 6) : 0;
  const wipe = g >= TV9.FLASH && g < TV9.FLASH + 8 ? ez(g, TV9.FLASH, TV9.FLASH + 7) : 1;
  const pulse = 0.55 + 0.45 * Math.abs(Math.sin((g / 30) * Math.PI));
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: TVW, height: TVH, overflow: 'hidden', background: 'linear-gradient(160deg, #0d1b33 0%, #13284a 55%, #0a1426 100%)', fontFamily: F.ios }}>
      {/* the studio backdrop: a soft grid of lit panels (abstract, no marks) */}
      {Array.from({ length: 24 }, (_, i) => (
        <div key={i} style={{ position: 'absolute', left: 80 + (i % 8) * 185, top: 70 + Math.floor(i / 8) * 150, width: 160, height: 120, borderRadius: 8,
          background: `rgba(${90 + (i * 37) % 60},${140 + (i * 23) % 60},220,${0.1 + ((i * 7) % 5) * 0.03})` }} />
      ))}
      {/* an inbox-shaped icon wall graphic: an envelope with a red error badge (generic) */}
      <svg style={{ position: 'absolute', left: 980, top: 120, width: 420, height: 300 }} viewBox="0 0 420 300">
        <rect x={20} y={40} width={330} height={220} rx={18} fill="#E9EEF6" />
        <path d="M24 52 L185 170 L346 52" fill="none" stroke="#9AA9C0" strokeWidth={14} strokeLinejoin="round" />
        <circle cx={350} cy={50} r={46} fill="#D93A30" /><path d="M350 24 V58 M350 72 V76" stroke="#fff" strokeWidth={13} strokeLinecap="round" />
      </svg>
      {/* LIVE bug + time */}
      <div style={{ position: 'absolute', left: 54, top: 46, display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 22px', borderRadius: 8, background: '#D3222A', color: '#fff', fontWeight: 800, fontSize: 46, letterSpacing: 2 }}>
          <div style={{ width: 18, height: 18, borderRadius: 9, background: '#fff', opacity: pulse }} />{TV.live}
        </div>
        <div style={{ padding: '10px 20px', borderRadius: 8, background: 'rgba(0,0,0,0.55)', color: '#fff', fontWeight: 700, fontSize: 46, fontVariantNumeric: 'tabular-nums' }}>{TV.time}</div>
      </div>
      {/* the lower third: the headline, the source under it */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 70, height: 250, clipPath: `inset(0 ${((1 - wipe) * 100).toFixed(2)}% 0 0)` }}>
        <div style={{ position: 'absolute', left: 40, right: 40, top: 0, height: 158, borderRadius: 10, background: '#F4F6FA', display: 'flex', alignItems: 'center', padding: '0 40px',
          boxShadow: '0 8px 30px rgba(0,0,0,0.4)' }}>
          <div style={{ width: 14, alignSelf: 'stretch', margin: '22px 30px 22px 0', borderRadius: 4, background: '#D3222A' }} />
          <div style={{ fontWeight: 800, fontSize: 70, lineHeight: 1.05, color: '#0B1426', letterSpacing: '-0.01em', whiteSpace: 'nowrap' }}>{TV.head}</div>
        </div>
        <div style={{ position: 'absolute', left: 40, top: 172, padding: '10px 26px', borderRadius: 8, background: 'rgba(8,14,28,0.85)', color: '#E8EDF5', fontSize: 40, fontWeight: 600, whiteSpace: 'nowrap' }}>{TV.src}</div>
      </div>
      {flash > 0 ? <div style={{ position: 'absolute', inset: 0, background: '#fff', opacity: 0.7 * flash }} /> : null}
    </div>
  );
};
