// Shared pieces of the Claude chat UI (split out of ClaudeChat.tsx by rl_l3_phone so the mobile app module can use them too).
import React from 'react';
import { APP, F, LIGHT, LIMIT, Theme } from './tokens';
import { IcInfo } from './Icons';

/** a Pasted-text attachment card (the excerpt of what was pasted, the PASTED tag) */
export const PastedChip: React.FC<{ t?: Theme; excerpt: string; w?: number; style?: React.CSSProperties }> = ({ t = LIGHT, excerpt, w = 112, style }) => (
  <div style={{ position: 'relative', width: w, height: w, flexShrink: 0, borderRadius: 10, background: t.card, border: `0.5px solid ${t.borderStrong}`,
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)', overflow: 'hidden', boxSizing: 'border-box', padding: '9px 9px 0 9px', ...style }}>
    <div style={{ fontFamily: F.sans, fontSize: 8.5, lineHeight: '11px', color: t.text3, whiteSpace: 'pre-wrap', wordBreak: 'break-word', height: w - 38, overflow: 'hidden' }}>{excerpt}</div>
    <div style={{ position: 'absolute', left: 8, bottom: 8, padding: '9px 11px', borderRadius: 6, border: `0.5px solid ${t.borderStrong}`, background: t.bg,
      fontFamily: F.sans, fontSize: 9.5, fontWeight: 600, letterSpacing: '0.04em', color: t.text2 }}>PASTED</div>
  </div>
);

/** the usage-limit banner that sits on top of the composer (mobile: the iOS app's look, tucked behind the composer's top edge) */
export const LimitBanner: React.FC<{ t?: Theme; text?: string; mobile?: boolean; link?: string; style?: React.CSSProperties }> = ({ t = LIGHT, text = LIMIT.app, mobile, link = 'Upgrade', style }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: mobile ? '0 12px' : '0 14px', padding: mobile ? '10px 14px 30px' : '9px 16px 20px',
    borderRadius: mobile ? '18px 18px 0 0' : '14px 14px 0 0', background: mobile ? APP.fill : t.bg3, border: `0.5px solid ${mobile ? 'rgba(0,0,0,0.05)' : t.border}`, borderBottom: 'none',
    fontFamily: mobile ? F.ios : F.sans, fontSize: 14, letterSpacing: mobile ? '-0.01em' : undefined, color: mobile ? APP.greet : t.text2, marginBottom: mobile ? -20 : -12, ...style }}>
    <IcInfo s={16} c={mobile ? APP.gray : t.text3} />
    <span style={{ flex: 1, whiteSpace: 'nowrap' }}>{text}</span>
    {link ? <span style={{ color: mobile ? APP.ink : t.text, fontWeight: mobile ? 500 : undefined, textDecoration: 'underline', textUnderlineOffset: 3, whiteSpace: 'nowrap' }}>{link}</span> : null}
  </div>
);
