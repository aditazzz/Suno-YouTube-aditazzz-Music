// The Claude iOS app as on her own phone (rl_l3_phone; refs/claude_app_home_phone.png, her screenshot Nov 17 10:25: "My chat
// screen. Change what it says accordingly"). Measured off the screenshot and scaled to our 393 x 852 pt screen (ref 440 pt wide;
// every number below = ref pt x 0.893), colours sampled from it (tokens APP):
//   the round white menu button top-left and the ghost (incognito) button top-right, the clay spark centred, the serif greeting,
//   the composer card ("Chat with Claude" / "Reply to Claude"; +, the "Opus 5.5 Medium" chip, mic, the black Talk pill, which
//   becomes the clay send arrow once there is text), and the light iOS keyboard.
// The spark is the app's own mark as it appears on her screen (the brief: no logos beyond what the real app shows).
import React from 'react';
import { APP, EFFORT, F, LIMIT, MODEL, MOBILE, Theme, greetingAt } from './tokens';
import { IcArrowUp, IcCompose, IcPlus } from './Icons';
import { LimitBanner, PastedChip } from './Parts';

const SW = 1.75;   // the app's icon stroke (pt)
const Ico: React.FC<{ s: number; c?: string; w?: number; children: React.ReactNode; fill?: string }> = ({ s, c = APP.icon, w = SW, children, fill = 'none' }) => (
  <svg width={s} height={s} viewBox="0 0 20 20" fill={fill} stroke={c} strokeWidth={(w * 20) / s} strokeLinecap="round" strokeLinejoin="round" style={{ display: 'block', flexShrink: 0 }}>{children}</svg>
);
export const IcAppMenu: React.FC<{ s?: number; c?: string }> = ({ s = 20, c }) => <Ico s={s} c={c}><path d="M2.6 4.6h14.8M2.6 10h12.6M2.6 15.4h6.4" /></Ico>;
export const IcGhost: React.FC<{ s?: number; c?: string }> = ({ s = 20, c = APP.icon }) => (
  <Ico s={s} c={c}>
    <path d="M3.6 16.6V9.2a6.4 6.4 0 0 1 12.8 0v7.4l-2.15-1.5-2.1 1.5-2.15-1.5-2.15 1.5-2.1-1.5z" />
    <circle cx="7.7" cy="9.6" r="0.55" fill={c} /><circle cx="12.3" cy="9.6" r="0.55" fill={c} />
  </Ico>
);
export const IcAppMic: React.FC<{ s?: number; c?: string }> = ({ s = 20, c = APP.icon }) => (
  <Ico s={s} c={c}><rect x="7.2" y="2.6" width="5.6" height="9.4" rx="2.8" /><path d="M4.6 9.6a5.4 5.4 0 0 0 10.8 0M10 15v2.6" /></Ico>
);
export const IcTalk: React.FC<{ s?: number; c?: string }> = ({ s = 20, c = '#fff' }) => (
  <Ico s={s} c={c} w={1.9}><path d="M2.6 10v0.01M6.3 7v6M10 3.4v13.2M13.7 7v6M17.4 10v0.01" /></Ico>
);
export const IcChevL: React.FC<{ s?: number; c?: string }> = ({ s = 20, c }) => <Ico s={s} c={c} w={2}><path d="M12.4 4.4L6.8 10l5.6 5.6" /></Ico>;
export const IcChevD: React.FC<{ s?: number; c?: string }> = ({ s = 14, c = APP.gray }) => <Ico s={s} c={c} w={1.6}><path d="M5.5 8l4.5 4.5L14.5 8" /></Ico>;

/** the clay spark, as on her home screen: 12 tapered rays of uneven length with blunt ends (our own trace of it) */
const RAYS: [number, number][] = [[-4, 1], [27, 0.92], [62, 0.8], [93, 1], [124, 0.82], [147, 0.94], [183, 1], [212, 0.84], [236, 0.9], [266, 0.98], [298, 0.8], [327, 0.95]];
export const Spark: React.FC<{ size: number; color?: string; turn?: number }> = ({ size, color = APP.spark, turn = 0 }) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100" style={{ display: 'block', overflow: 'visible' }}>
    <g transform={`rotate(${turn})`} fill={color}>
      <circle r={7} />
      {RAYS.map(([a, l], i) => {
        const L = 48 * l, b = 2.6, tw = 5 + (i % 3) * 0.5;
        // a thin wedge from the centre widening to a blunt, slightly slanted tip
        return <path key={i} transform={`rotate(${a})`} d={`M ${-b} -4 L ${-tw} ${-L + 1.5} Q ${-tw + 0.4} ${-L - 0.4} ${-tw + 1.6} ${-L - 0.6} L ${tw - 1.2} ${-L + 0.6} Q ${tw} ${-L + 0.9} ${tw} ${-L + 2.2} L ${b} -4 Z`} />;
      })}
    </g>
  </svg>
);

/** a round white header button (menu, ghost, back, new chat) */
export const RoundBtn: React.FC<{ children: React.ReactNode; d?: number; style?: React.CSSProperties }> = ({ children, d = 39.5, style }) => (
  <div style={{ width: d, height: d, borderRadius: d / 2, background: APP.btn, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    boxShadow: '0 3px 14px rgba(0,0,0,0.055), 0 0 0 0.5px rgba(0,0,0,0.035)', ...style }}>{children}</div>
);

/** the header row under the status bar: buttons centred at y 74.7 pt, 18 pt in from each side; title between them (in a chat) */
export const AppHeader: React.FC<{ left?: 'menu' | 'back'; right?: 'ghost' | 'compose' | 'none'; title?: string; bg?: string }> = ({ left = 'menu', right = 'ghost', title, bg }) => (
  <div style={{ position: 'absolute', left: 0, right: 0, top: 54, height: 42, display: 'flex', alignItems: 'center', padding: '0 18px', zIndex: 5, background: bg }}>
    <RoundBtn>{left === 'menu' ? <IcAppMenu s={20} /> : <IcChevL s={21} c={APP.icon} />}</RoundBtn>
    <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3, padding: '0 10px', fontFamily: F.ios, fontSize: 16, fontWeight: 600,
      letterSpacing: '-0.01em', color: APP.ink, whiteSpace: 'nowrap', overflow: 'hidden' }}>
      {title ? <><span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{title}</span><IcChevD s={14} /></> : null}
    </div>
    {right === 'none' ? <div style={{ width: 39.5 }} /> : <RoundBtn>{right === 'ghost' ? <IcGhost s={20} /> : <IcCompose s={19} c={APP.icon} w={1.6} />}</RoundBtn>}
  </div>
);

const Fill: React.FC<{ children: React.ReactNode; w?: number; style?: React.CSSProperties }> = ({ children, w, style }) => (
  <div style={{ height: 31.6, minWidth: 31.6, width: w, borderRadius: 15.8, background: APP.fill, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, ...style }}>{children}</div>
);

/** a paragraph word-wrapped to the field's width, measured in the field's own font and tracking (deterministic per font) */
let _ctx: CanvasRenderingContext2D | null = null;
export const wrapLines = (line: string, fs: number, width: number): string[] => {
  if (typeof document === 'undefined') return [line];
  if (!_ctx) _ctx = document.createElement('canvas').getContext('2d');
  const c = _ctx!; c.font = `400 ${fs}px -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif`;
  const ls = 0.022 * fs; const w = (t: string) => c.measureText(t).width + ls * t.length;
  const out: string[] = []; let cur = '';
  for (const word of line.split(' ')) {
    const next = cur ? `${cur} ${word}` : word;
    if (cur && w(next) > width) { out.push(cur); cur = word; } else cur = next;
  }
  out.push(cur);
  return out;
};

/** the composer card, measured off her screenshot: 377.6 x 92 pt with one line, radius 18, 7 pt inner padding round the button row.
 *  text = what she has typed (grows up to maxLines, then shows its last lines like the real field), chips = Pasted cards. */
export const AppComposer: React.FC<{
  text?: string; placeholder?: string; caret?: boolean; caretOn?: boolean; chips?: string[]; chipW?: number; banner?: boolean | string; disabled?: boolean;
  model?: string; effort?: string; sendPressed?: number; maxLines?: number; style?: React.CSSProperties;
}> = ({ text = '', placeholder = 'Chat with Claude', caret = false, caretOn = true, chips = [], chipW = 96, banner, disabled, model = MODEL, effort = EFFORT, sendPressed = 0, maxLines = 6, style }) => {
  const has = text.length > 0 || chips.length > 0;
  const fs = 20, lh = 24;
  // the field grows to maxLines, then shows its latest lines, clipped at a line boundary like the real field scrolled to the caret.
  // Lines are counted by measuring the words in the field's own font (word wrap at the field's width), so the height is exact.
  // wrapped here (not by the browser), so only the visible lines exist: the field shows its last maxLines visual lines
  const vis = text ? text.split('\n').flatMap((l) => wrapLines(l, fs, 354)) : [];
  const nLines = Math.max(1, Math.min(maxLines, vis.length));
  const shownText = vis.slice(-maxLines).join('\n');
  return (
    <div style={{ position: 'relative', ...style }}>
      {banner ? <LimitBanner t={MOBILE} mobile text={typeof banner === 'string' ? banner : LIMIT.app} /> : null}
      <div style={{ position: 'relative', background: APP.bg, borderRadius: 18, boxSizing: 'border-box', padding: '15.3px 6.8px 6.8px',
        boxShadow: 'inset 0 0.6px 0 #fff, 0 0 0 0.5px rgba(0,0,0,0.055), 0 -3px 12px rgba(0,0,0,0.035), 0 4px 16px rgba(0,0,0,0.05)' }}>
        {chips.length ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, margin: '-4px 0 10px 4px' }}>
            {chips.map((c, i) => <PastedChip key={i} t={MOBILE} excerpt={c} w={chipW} />)}
          </div>
        ) : null}
        <div style={{ height: lh * Math.max(1, Math.min(maxLines, nLines)), overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', padding: '0 5px' }}>
          <div style={{ fontFamily: F.ios, fontSize: fs, lineHeight: `${lh}px`, letterSpacing: '0.022em', fontWeight: text ? 400 : 480, color: text ? APP.ink : APP.gray, whiteSpace: 'pre', }}>
            {shownText || (chips.length ? '' : placeholder)}
            {caret ? <span style={{ display: 'inline-block', width: 2, height: 21, marginLeft: 1, marginRight: -3, verticalAlign: '-4px', background: '#C6613F', opacity: caretOn ? 1 : 0, borderRadius: 1 }} /> : null}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginTop: 14.5 }}>
          <Fill><IcPlus s={19} c={APP.ink} w={1.5} /></Fill>
          <Fill style={{ marginLeft: 7.7, height: 41, borderRadius: 20.5, padding: '0 18px', fontFamily: F.ios, fontSize: 15.7, fontWeight: 450, letterSpacing: '-0.01em', whiteSpace: 'nowrap' }}>
            <span style={{ color: APP.ink }}>{model}</span><span style={{ color: APP.gray }}>&nbsp;{effort}</span>
          </Fill>
          <div style={{ flex: 1 }} />
          <Fill><IcAppMic s={18} /></Fill>
          {has ? (
            <div style={{ marginLeft: 8, width: 31.6, height: 31.6, borderRadius: 15.8, background: '#C6613F', display: 'flex', alignItems: 'center', justifyContent: 'center',
              opacity: disabled ? 0.38 : 1, transform: `scale(${1 - 0.1 * sendPressed})` }}><IcArrowUp s={18} c="#fff" w={2.1} /></div>
          ) : (
            <div style={{ marginLeft: 8, height: 31.6, width: 82.8, borderRadius: 15.8, background: APP.ink, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
              fontFamily: F.ios, fontSize: 15.6, fontWeight: 700, letterSpacing: '-0.01em', color: '#fff' }}><IcTalk s={17} />Talk</div>
          )}
        </div>
      </div>
    </div>
  );
};

/** the light iOS keyboard as in her screenshot (suggestion bar, white keys on #E1E1E4, rounded top), 306 pt tall */
export const KB_H = 306;
const ROWS = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm'];
export const IOSKeyboard: React.FC<{ upper?: boolean; sugg?: [string, string, string]; press?: string }> = ({ upper = true, sugg = ['I', 'The', 'I’m'], press }) => {
  const kw = 33, kh = 39.3, gx = 5.6;
  const Key: React.FC<{ x: number; y: number; w?: number; children?: React.ReactNode; on?: boolean; fs?: number }> = ({ x, y, w = kw, children, on, fs = 23.5 }) => (
    <div style={{ position: 'absolute', left: x, top: y, width: w, height: kh, borderRadius: 8.5, background: on ? '#C9CACE' : APP.key, boxShadow: '0 1px 0 rgba(0,0,0,0.28)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: F.ios, fontSize: fs, color: APP.keyInk }}>{children}</div>
  );
  const rowY = [45.6, 95.4, 145.2, 195];
  const cs = (ch: string) => (upper ? ch.toUpperCase() : ch);
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: KB_H, background: APP.kb, borderRadius: '24px 24px 0 0', zIndex: 8, overflow: 'hidden',
      boxShadow: '0 -0.5px 0 rgba(0,0,0,0.06)' }}>
      {/* suggestions */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 9, height: 26, display: 'flex', alignItems: 'center', fontFamily: F.ios, fontSize: 19.5, color: APP.sugg }}>
        {sugg.map((s, i) => (
          <div key={i} style={{ flex: 1, textAlign: 'center', borderLeft: i ? '1px solid rgba(60,60,67,0.18)' : undefined, whiteSpace: 'nowrap' }}>{s}</div>
        ))}
      </div>
      {ROWS[0].split('').map((c, i) => <Key key={c} x={6 + i * (kw + gx) + 0.4} y={rowY[0]} on={press === c}>{cs(c)}</Key>)}
      {ROWS[1].split('').map((c, i) => <Key key={c} x={25.4 + i * (kw + gx)} y={rowY[1]} on={press === c}>{cs(c)}</Key>)}
      <Key x={6} y={rowY[2]} w={44.4}>
        <svg width={20} height={20} viewBox="0 0 20 20"><path d="M10 2.6L2.8 10.4h4v6.6h6.4v-6.6h4z" fill={upper ? '#000' : 'none'} stroke="#000" strokeWidth={1.6} strokeLinejoin="round" /></svg>
      </Key>
      {ROWS[2].split('').map((c, i) => <Key key={c} x={64 + i * (kw + gx)} y={rowY[2]} on={press === c}>{cs(c)}</Key>)}
      <Key x={342.4} y={rowY[2]} w={44.4}>
        <svg width={24} height={18} viewBox="0 0 24 18"><path d="M8 1.5h13a1.5 1.5 0 0 1 1.5 1.5v12a1.5 1.5 0 0 1-1.5 1.5H8L1.5 9z" fill="none" stroke="#000" strokeWidth={1.5} strokeLinejoin="round" /><path d="M11 5.5l7 7M18 5.5l-7 7" stroke="#000" strokeWidth={1.5} strokeLinecap="round" /></svg>
      </Key>
      <Key x={6} y={rowY[3]} w={42.4} fs={17}>123</Key>
      <Key x={54.2} y={rowY[3]} w={42.4}>
        <svg width={22} height={22} viewBox="0 0 22 22" fill="none" stroke="#000" strokeWidth={1.5}><circle cx="11" cy="11" r="9" /><circle cx="8" cy="9" r="0.9" fill="#000" /><circle cx="14" cy="9" r="0.9" fill="#000" /><path d="M6.6 12.6a4.8 4.8 0 0 0 8.8 0z" fill="#000" /></svg>
      </Key>
      <Key x={102.4} y={rowY[3]} w={187.8} on={press === ' '}><span style={{ position: 'absolute', right: 7, bottom: 4, fontSize: 9.5, color: '#8A8A8E', letterSpacing: '0.02em' }}>EN</span></Key>
      <Key x={296.2} y={rowY[3]} w={90.8}>
        <svg width={24} height={18} viewBox="0 0 24 18" fill="none" stroke="#000" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round"><path d="M20 2v6.5a1.5 1.5 0 0 1-1.5 1.5H4M8.5 5.5L4 10l4.5 4.5" /></svg>
      </Key>
      {/* globe + dictation */}
      <svg style={{ position: 'absolute', left: 26, top: 255 }} width={25} height={25} viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth={1.4}><circle cx="12" cy="12" r="10" /><ellipse cx="12" cy="12" rx="4.4" ry="10" /><path d="M2 12h20M4 6.5h16M4 17.5h16" /></svg>
      <svg style={{ position: 'absolute', left: 343, top: 253 }} width={22} height={28} viewBox="0 0 22 28" fill="none" stroke="#000" strokeWidth={1.7} strokeLinecap="round"><rect x="6.5" y="1.5" width="9" height="15" rx="4.5" /><path d="M2.5 12.5a8.5 8.5 0 0 0 17 0M11 21v5" /></svg>
    </div>
  );
};

/** a new chat (her home screen): spark + greeting centred in the space above the composer. greeting defaults by `hour`.
 *  keyboard = the field is focused (as in her screenshot). The composer grows upward from its one-line spot. */
export const MobileHome: React.FC<{
  hour?: number; greeting?: string; composer?: React.ComponentProps<typeof AppComposer>; keyboard?: boolean; kbUpper?: boolean; kbPress?: string; sugg?: [string, string, string];
  sparkTurn?: number; children?: React.ReactNode;
}> = ({ hour = 10, greeting, composer = {}, keyboard = true, kbUpper, kbPress, sugg, sparkTurn = 0, children }) => {
  const cBottom = keyboard ? 852 - 537.6 : 34 + 8;     // composer bottom edge (pt from the screen's bottom)
  const cTop1 = 852 - cBottom - 92;                     // its one-line top
  const mid = (100 + cTop1) / 2;                        // spark + greeting block centre (ref: 273 pt with the keyboard up)
  const text = greeting ?? greetingAt(hour);
  const upper = kbUpper ?? !(composer.text && !composer.text.endsWith('\n'));
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: APP.bg, overflow: 'hidden' }}>
      <AppHeader left="menu" right="ghost" />
      <div style={{ position: 'absolute', left: (393 - 42.7) / 2, top: mid - 25.6 - 21.3 }}><Spark size={42.7} turn={sparkTurn} /></div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: mid + 9, textAlign: 'center', fontFamily: F.appSerif, fontSize: 27.6, fontWeight: 700, letterSpacing: '-0.03em', wordSpacing: '-0.06em',
        lineHeight: '36px', color: APP.greet, whiteSpace: 'nowrap' }}>{text}</div>
      {children}
      <div style={{ position: 'absolute', left: 7.7, right: 7.7, bottom: cBottom, zIndex: 6 }}>
        <AppComposer {...composer} />
      </div>
      {keyboard ? <IOSKeyboard upper={upper} press={kbPress} sugg={sugg} /> : null}
    </div>
  );
};
