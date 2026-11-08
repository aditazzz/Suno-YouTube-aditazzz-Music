import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { C, D, F, W, H, fsForCap, pop } from './theme';
import { HAVE } from './stillsManifest';
import { useFonts } from './fonts';

// motion pass: set per item by Root. key = first approved key frame (entrances finish before it).
export const MotionCtx = React.createContext<{ key: number; on: boolean }>({ key: 0, on: false });
/** staggered entrance for each direct child (index 0 = background stays put): rise 20 px + fade from a 35% ghost, overshoot, 12 f */
export const Stagger: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const f = useCurrentFrame(); const m = React.useContext(MotionCtx);
  const kids = React.Children.toArray(children);
  if (!m.on) return <>{kids}</>;
  const n = Math.max(1, kids.length - 1); const step = Math.min(2, Math.max(0, (m.key - 14) / n));
  return <>{kids.map((k, i) => {
    if (i === 0 || !React.isValidElement(k)) return k;
    const t = pop(f, Math.round((i - 1) * step), 12); const o = Math.min(1, 0.35 + 0.65 * Math.min(1, t * 1.15));
    return <div key={i} style={{ position: 'absolute', inset: 0, opacity: o, transform: `translateY(${(1 - t) * 20}px)` }}>{k}</div>;
  })}</>;
};

// width / height of each founder still (matches render_founder_stills.py), and what the placeholder silhouette draws
export const STILL: Record<string, { a: number; k: 'head' | 'waist' | 'full' | 'lie' }> = {
  F01: { a: 0.75, k: 'head' }, F05: { a: 0.75, k: 'waist' }, F06: { a: 0.75, k: 'waist' }, F07: { a: 1, k: 'head' }, F08: { a: 0.75, k: 'waist' },
  F09: { a: 0.75, k: 'waist' }, F10: { a: 0.667, k: 'full' }, F11: { a: 0.75, k: 'lie' }, F12: { a: 0.667, k: 'full' }, F13: { a: 0.75, k: 'waist' },
  F14: { a: 0.75, k: 'waist' }, F15: { a: 0.75, k: 'waist' }, F16: { a: 0.75, k: 'waist' }, F17: { a: 0.75, k: 'waist' }, F17A: { a: 0.75, k: 'waist' }, F17B: { a: 0.75, k: 'waist' }, F18: { a: 0.75, k: 'waist' },
  F19: { a: 0.667, k: 'full' }, F20: { a: 0.667, k: 'full' }, F21: { a: 0.75, k: 'waist' }, F22: { a: 0.75, k: 'waist' }, F23: { a: 0.75, k: 'waist' },
  F24: { a: 0.75, k: 'waist' }, F25: { a: 0.75, k: 'waist' }, F26: { a: 0.75, k: 'waist' }, F27: { a: 0.667, k: 'full' }, F28: { a: 0.75, k: 'waist' },
  F29: { a: 0.75, k: 'head' }, F30: { a: 0.75, k: 'waist' },
};
export const hasStill = (id: string) => HAVE.includes(id);

const Sil: React.FC<{ id: string; w: number; h: number }> = ({ id, w, h }) => {
  const k = STILL[id].k;
  const g = '#9A94B0';
  return (
    <svg width={w} height={h} viewBox="0 0 300 400">
      {k === 'head' && (<g fill={g}><ellipse cx="150" cy="150" rx="62" ry="78" /><path d="M20 400 Q30 270 150 262 Q270 270 280 400Z" /><path d="M95 90 Q150 20 215 78 Q170 55 95 90Z" /></g>)}
      {k === 'waist' && (<g fill={g}><ellipse cx="150" cy="105" rx="42" ry="52" /><path d="M110 70 Q150 20 195 62 Q160 48 110 70Z" /><path d="M40 400 Q48 175 150 160 Q252 175 260 400Z" /></g>)}
      {k === 'full' && (<g fill={g}><ellipse cx="150" cy="58" rx="24" ry="30" /><path d="M105 90 Q150 80 195 90 L215 250 L190 250 L185 380 L155 380 L150 260 L145 380 L115 380 L110 250 L85 250Z" /></g>)}
      {k === 'lie' && (<g fill={g}><ellipse cx="150" cy="70" rx="46" ry="54" /><path d="M70 130 Q150 110 230 130 L245 400 L55 400Z" /></g>)}
      <text x="150" y="395" textAnchor="middle" fontFamily="Inter" fontWeight="600" fontSize="22" fill="#6B6580">{id} placeholder</text>
    </svg>
  );
};

type FP = { id: string; h: number; x: number; y: number; flip?: boolean; rim?: boolean; shadow?: boolean; bw?: boolean; opacity?: number; rot?: number; anchor?: 'top' | 'bottom'; style?: React.CSSProperties; tint?: string };
/** founder cutout: centred on x, top at y (or bottom at y), soft drop shadow + 2-4 px ultraviolet rim */
export const Founder: React.FC<FP> = ({ id, h, x, y, flip, rim = true, shadow = true, bw, opacity = 1, rot = 0, anchor = 'top', style }) => {
  const a = STILL[id]?.a ?? 0.75; const w = h * a;
  const filt = [
    rim ? `drop-shadow(0 0 1.2px rgba(255,255,255,.55)) drop-shadow(0 0 2.2px rgba(255,255,255,.25))` : '', // round 4: neutral rim, no ultraviolet
    shadow ? `drop-shadow(0 ${Math.round(h * 0.03)}px ${Math.round(h * 0.045)}px rgba(6,8,12,0.38))` : '',
    bw ? 'grayscale(1) contrast(1.15)' : '',
  ].filter(Boolean).join(' ');
  return (
    <div style={{ position: 'absolute', left: x - w / 2, top: anchor === 'top' ? y : y - h, width: w, height: h, opacity, transform: `${flip ? 'scaleX(-1)' : ''} rotate(${rot}deg)`, filter: filt, ...style }}>
      {hasStill(id) ? <Img src={staticFile(`stills/${id}.png`)} style={{ width: w, height: h, display: 'block' }} /> : <Sil id={id} w={w} h={h} />}
    </div>
  );
};
/** a round avatar cropped to the head of a still */
export const Avatar: React.FC<{ id: string; size: number; zoom?: number; cx?: number; cy?: number; bg?: string; ring?: string; style?: React.CSSProperties }> = ({ id, size, zoom = 2.2, cx = 0.5, cy = 0.33, bg = D.card2, ring, style }) => {
  const a = STILL[id]?.a ?? 0.75; const iw = size * zoom, ih = iw / a;
  return (
    <div style={{ width: size, height: size, borderRadius: '50%', overflow: 'hidden', position: 'relative', background: bg, boxShadow: ring ? `0 0 0 ${Math.max(3, size * 0.04)}px ${ring}` : undefined, flex: 'none', ...style }}>
      <div style={{ position: 'absolute', left: size / 2 - cx * iw, top: size / 2 - cy * ih, width: iw, height: ih }}>
        {hasStill(id) ? <Img src={staticFile(`stills/${id}.png`)} style={{ width: iw, height: ih }} /> : <Sil id={id} w={iw} h={ih} />}
      </div>
    </div>
  );
};
/** base canvas: loads fonts, 2560x1440 */
export const Canvas: React.FC<{ bg?: string; children?: React.ReactNode; style?: React.CSSProperties }> = ({ bg = D.bg1, children, style }) => {
  useFonts();
  return <AbsoluteFill style={{ background: bg, fontFamily: F.inter, overflow: 'hidden', ...style }}><Stagger>{children}</Stagger></AbsoluteFill>;
};
export const T: React.FC<{ cap?: number; fam?: 'inter' | 'anton' | 'mono' | 'vt' | 'caveat' | 'corm'; w?: number; c?: string; style?: React.CSSProperties; children?: React.ReactNode }> = ({ cap = 48, fam = 'inter', w, c = C.ink, style, children }) => (
  <div style={{ fontFamily: { inter: F.inter, anton: F.anton, mono: F.mono, vt: F.vt, caveat: F.caveat, corm: F.corm }[fam], fontSize: fsForCap(cap, fam), fontWeight: w ?? (fam === 'inter' ? 600 : fam === 'mono' ? 700 : fam === 'corm' ? 700 : 400), color: c, lineHeight: 1.08, ...style }}>{children}</div>
);
export const Abs: React.FC<{ x: number; y: number; w?: number; h?: number; style?: React.CSSProperties; children?: React.ReactNode }> = ({ x, y, w, h, style, children }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, ...style }}>{children}</div>
);
/** the in-world screen: dark bezel 3-5% visible at the edge, faint warm glass reflection, content fully inside */
export const Bezel: React.FC<{ children: React.ReactNode; inset?: number; glow?: string }> = ({ children, inset = 84, glow = '#FFC58A' }) => (
  <AbsoluteFill style={{ background: '#0A0A0D' }}>
    <div style={{ position: 'absolute', inset: 22, borderRadius: 26, background: '#15161B', boxShadow: 'inset 0 0 0 3px #23242C, inset 0 0 60px rgba(0,0,0,.8)' }} />
    <div style={{ position: 'absolute', left: inset, top: inset * 0.8, right: inset, bottom: inset * 0.8, borderRadius: 14, overflow: 'hidden', background: C.screen }}>
      <div style={{ position: 'absolute', left: -inset, top: -inset * 0.8, width: W, height: H }}><Stagger>{children}</Stagger></div>
      <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(115deg, ${glow}1F 0%, ${glow}00 28%, transparent 70%, ${glow}0D 100%)`, pointerEvents: 'none' }} />
    </div>
  </AbsoluteFill>
);
/** soft shadow card */
export const Card: React.FC<{ x: number; y: number; w: number; h: number; r?: number; bg?: string; shadow?: boolean; style?: React.CSSProperties; children?: React.ReactNode }> = ({ x, y, w, h, r = 36, bg = D.card, shadow = true, style, children }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: r, background: bg, boxShadow: shadow ? '0 40px 80px rgba(6,2,20,.55), inset 0 0 0 2px rgba(255,255,255,.08)' : undefined, overflow: 'hidden', ...style }}>{children}</div>
);
export const Caret: React.FC<{ f: number; h: number; c?: string; w?: number }> = ({ f, h, c = C.amber, w = 14 }) => (
  <span style={{ display: 'inline-block', width: w, height: h, background: c, marginLeft: 8, verticalAlign: 'text-bottom', opacity: Math.floor(f / 6) % 2 === 0 ? 1 : 0.1 }} />
);
/** generic invented 'professional network' mark: a rounded square with a pennant, not any real logo */
export const Mark: React.FC<{ s: number; c?: string }> = ({ s, c = '#0A66C2' }) => (
  <svg width={s} height={s} viewBox="0 0 100 100"><rect x="4" y="4" width="92" height="92" rx="24" fill={c} /><path d="M30 74V26l44 14-44 14" fill="none" stroke="#fff" strokeWidth="10" strokeLinejoin="round" strokeLinecap="round" /></svg>
);
export const Heart: React.FC<{ s: number; c?: string }> = ({ s, c = C.red }) => (
  <svg width={s} height={s} viewBox="0 0 24 24"><path fill={c} d="M12 21s-8-5.2-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 5.8-8 11-8 11z" /></svg>
);
/** the night behind every founder feed (bible §4): ultraviolet ink, a soft pool of light behind the card, never lavender */
export const NightBg: React.FC<{ at?: string }> = ({ at = '50% 38%' }) => (
  <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse at ${at}, #2C3442 0%, #1C2230 45%, #0D0F14 100%)` /* round 4: slate night, not ultraviolet */ }} />
);
