// The Claude chat interface (claude.ai / desktop app / mobile app), built to the real layout: the cream page, Claude's replies
// in the serif, the user's turns in a soft bubble, the composer card (+, tools, model picker, the clay send button), the
// usage-limit banner above the composer, Pasted-text attachment cards. No logo marks.
// Sizes are the app's own CSS px / iOS points; the shot scales the whole screen (ScreenInsert / Phone).
import React from 'react';
import { F, LIGHT, LIMIT, MODEL, MOBILE, Theme } from './tokens';
import { AppComposer, AppHeader, IOSKeyboard, KB_H } from './MobileApp';
import { IcArrowUp, IcChat, IcChevDown, IcClock, IcCode, IcCompose, IcCopy, IcFolder, IcImage, IcMenu, IcPlus, IcRetry, IcSliders, IcThumbDown, IcThumbUp, IcWave, IcInfo } from './Icons';

export type Msg = { who: 'user' | 'claude'; text: string; chars?: number; chips?: string[]; hl?: { s: string; k: number } };

export { PastedChip, LimitBanner } from './Parts';
import { PastedChip, LimitBanner } from './Parts';

const SqBtn: React.FC<{ t: Theme; children: React.ReactNode; size?: number }> = ({ t, children, size = 32 }) => (
  <div style={{ width: size, height: size, borderRadius: 8, border: `0.5px solid ${t.borderStrong}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: t.text3 }}>{children}</div>
);

/** the composer card. text = what is typed (caret after it when caret), chips = Pasted cards above the text. */
export const Composer: React.FC<{
  t?: Theme; text?: string; placeholder?: string; caret?: boolean; chips?: string[]; chipW?: number; banner?: boolean | string; disabled?: boolean;
  model?: string; mobile?: boolean; style?: React.CSSProperties; sendPressed?: number; maxTextLines?: number;
}> = ({ t = LIGHT, text = '', placeholder = 'Reply to Claude…', caret = false, chips = [], chipW, banner, disabled, model = MODEL, mobile, style, sendPressed = 0 }) => {
  const has = text.length > 0 || chips.length > 0;
  const fs = mobile ? 17 : 16;
  return (
    <div style={{ position: 'relative', ...style }}>
      {banner ? <LimitBanner t={t} mobile={mobile} text={typeof banner === 'string' ? banner : undefined} /> : null}
      <div style={{ position: 'relative', background: t.card, borderRadius: mobile ? 24 : 20, border: `0.5px solid ${t.borderStrong}`,
        boxShadow: '0 4px 20px rgba(0,0,0,0.045), 0 1px 3px rgba(0,0,0,0.04)', padding: mobile ? '12px 12px 10px' : '14px 14px 12px', boxSizing: 'border-box' }}>
        {chips.length ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
            {chips.map((c, i) => <PastedChip key={i} t={t} excerpt={c} w={chipW ?? (mobile ? 96 : 112)} />)}
          </div>
        ) : null}
        <div style={{ fontFamily: F.sans, fontSize: fs, lineHeight: 1.45, color: text ? t.text : t.text3, minHeight: fs * 1.45, padding: mobile ? '2px 6px 12px' : '2px 4px 14px', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {text || (chips.length ? '' : placeholder)}
          {caret ? <span style={{ display: 'inline-block', width: 2, height: fs * 1.15, marginLeft: 1, verticalAlign: 'text-bottom', background: t.accent }} /> : null}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <SqBtn t={t}><IcPlus s={18} /></SqBtn>
          <SqBtn t={t}><IcSliders s={18} /></SqBtn>
          {mobile ? null : <SqBtn t={t}><IcClock s={18} /></SqBtn>}
          <div style={{ flex: 1 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 3, fontFamily: F.sans, fontSize: mobile ? 14 : 14, color: t.text2, whiteSpace: 'nowrap', marginRight: 6 }}>
            {model}<IcChevDown s={14} c={t.text3} />
          </div>
          <div style={{ width: 32, height: 32, borderRadius: mobile ? 16 : 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: has ? t.accent : mobile ? t.text : t.accent, opacity: disabled ? 0.45 : has || mobile ? 1 : 0.5, transform: `scale(${1 - 0.08 * sendPressed})` }}>
            {has || !mobile ? <IcArrowUp s={18} c={t.accentText} w={2} /> : <IcWave s={18} c={t.bg} w={2} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export const UserMsg: React.FC<{ t?: Theme; text: string; chips?: string[]; mobile?: boolean; time?: string }> = ({ t = LIGHT, text, chips, mobile }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
    {chips?.length ? <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>{chips.map((c, i) => <PastedChip key={i} t={t} excerpt={c} w={84} />)}</div> : null}
    <div style={{ maxWidth: mobile ? '82%' : '75%', background: t.userBubble, color: t.text, borderRadius: mobile ? 20 : 14, padding: mobile ? '9px 15px' : '10px 16px',
      fontFamily: mobile ? F.ios : F.sans, fontSize: mobile ? 17 : 16, letterSpacing: mobile ? '-0.01em' : undefined, lineHeight: 1.42, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{text}</div>
  </div>
);

/** Claude's reply in the serif; chars < text.length = still streaming (a soft trailing block) */
/** hl = the iOS text selection over a substring (k 0..1 sweeps it on, left to right, with the two blue handles) */
const Selected: React.FC<{ s: string; k: number }> = ({ s, k }) => {
  const n = Math.round(s.length * Math.max(0, Math.min(1, k)));
  const Handle: React.FC<{ end?: boolean }> = ({ end }) => (
    <span style={{ position: 'relative', display: 'inline-block', width: 0, height: '1em' }}>
      <span style={{ position: 'absolute', left: -1, top: end ? '-0.05em' : '-0.35em', width: 2.5, height: '1.35em', background: '#0A84FF', borderRadius: 1 }} />
      <span style={{ position: 'absolute', left: -4.5, top: end ? '1.2em' : '-0.62em', width: 9, height: 9, borderRadius: 5, background: '#0A84FF' }} />
    </span>
  );
  return n <= 0 ? <>{s}</> : (
    <>
      <Handle />
      <span data-fit="off" style={{ background: 'rgba(10,132,255,0.24)', borderRadius: 2 }}>{s.slice(0, n)}</span>
      <Handle end />
      {s.slice(n)}
    </>
  );
};
export const ClaudeMsg: React.FC<{ t?: Theme; text: string; chars?: number; mobile?: boolean; actions?: boolean; hl?: { s: string; k: number } }> = ({ t = LIGHT, text, chars, mobile, actions = true, hl }) => {
  const n = chars === undefined ? text.length : Math.max(0, Math.min(text.length, Math.floor(chars)));
  const streaming = n < text.length;
  const shown = text.slice(0, n); const at = hl ? shown.indexOf(hl.s) : -1;
  return (
    <div>
      <div style={{ fontFamily: mobile ? F.appSerif : F.serif, fontSize: mobile ? 17.5 : 16.5, lineHeight: 1.6, color: t.text, whiteSpace: 'pre-wrap', wordBreak: 'break-word', paddingRight: 4 }}>
        {at >= 0 && hl ? <>{shown.slice(0, at)}<Selected s={hl.s} k={hl.k} />{shown.slice(at + hl.s.length)}</> : shown}
        {streaming ? <span style={{ display: 'inline-block', width: 9, height: 9, borderRadius: 5, marginLeft: 4, background: t.accent, verticalAlign: 'middle' }} /> : null}
      </div>
      {actions && !streaming ? (
        <div style={{ display: 'flex', gap: mobile ? 14 : 10, marginTop: 10, color: t.text3 }}>
          <IcCopy s={mobile ? 18 : 16} /><IcThumbUp s={mobile ? 18 : 16} /><IcThumbDown s={mobile ? 18 : 16} /><IcRetry s={mobile ? 18 : 16} />
        </div>
      ) : null}
    </div>
  );
};

/** a column of messages laid out from the bottom (newest just above the composer); scroll lifts it */
export const Thread: React.FC<{ t?: Theme; msgs: Msg[]; mobile?: boolean; gap?: number; scroll?: number; blur?: number }> = ({ t = LIGHT, msgs, mobile, gap = 22, scroll = 0, blur = 0 }) => (
  <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', gap, transform: `translateY(${scroll}px)`, filter: blur ? `blur(${blur}px)` : undefined }}>
    {msgs.map((m, i) => m.who === 'user'
      ? <UserMsg key={i} t={t} text={m.text} chips={m.chips} mobile={mobile} />
      : <ClaudeMsg key={i} t={t} text={m.text} chars={m.chars} mobile={mobile} actions={i === msgs.length - 1} hl={m.hl} />)}
  </div>
);

/** the iOS app inside a conversation, in the look of her own app (rl_l3_phone, refs/claude_app_home_phone.png): the round menu button,
 *  the chat title, the round new-chat button, the thread (newest at the bottom), her app's composer ("Reply to Claude", the
 *  "Opus 5.5 Medium" chip, mic, Talk / send) and, when typing, the light keyboard. 393 x 852 pt; the top 54 pt are the status bar. */
export const MobileChat: React.FC<{
  t?: Theme; title?: string; msgs: Msg[]; composer?: React.ComponentProps<typeof AppComposer>; scroll?: number; threadBlur?: number;
  w?: number; h?: number; keyboard?: number | boolean; header?: React.ReactNode; empty?: React.ReactNode; composerLift?: number; hideComposer?: boolean;
}> = ({ t = MOBILE, title = 'New chat', msgs, composer = {}, scroll = 0, threadBlur = 0, w = 393, h = 852, keyboard = 0, header, empty, composerLift = 0, hideComposer }) => {
  const kb = keyboard ? KB_H - 8 : 34;
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: h, background: t.bg, overflow: 'hidden', fontFamily: F.ios, display: 'flex', flexDirection: 'column' }}>
      <div style={{ height: 106, flexShrink: 0 }} />
      <AppHeader left="menu" right="compose" title={title} bg={t.bg} />
      {header}
      <div style={{ position: 'relative', flex: 1, margin: '0 18px 14px', overflow: 'hidden' }}>
        {msgs.length ? <Thread t={t} msgs={msgs} mobile scroll={scroll} blur={threadBlur} /> : empty}
      </div>
      <div style={{ flexShrink: 0, padding: `0 7.7px ${kb + composerLift}px`, zIndex: 6, visibility: hideComposer ? 'hidden' : undefined }}>
        <AppComposer placeholder="Reply to Claude" {...composer} />
      </div>
      {keyboard ? <IOSKeyboard upper={!composer.text} /> : null}
    </div>
  );
};

/** the desktop app / claude.ai: sidebar, header, the centred thread, the composer. w x h CSS px (MacBook: 1512 x 945). */
export const DesktopChat: React.FC<{
  t?: Theme; title?: string; msgs: Msg[]; composer?: React.ComponentProps<typeof Composer>; scroll?: number; w?: number; h?: number;
  sidebar?: boolean; recents?: string[]; col?: number; topBar?: React.ReactNode;
}> = ({ t = LIGHT, title = 'Make the font bigger', msgs, composer = {}, scroll = 0, w = 1512, h = 945, sidebar = true, recents = [], col = 720, topBar }) => {
  const sw = sidebar ? 288 : 0;
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: h, background: t.bg, overflow: 'hidden', fontFamily: F.sans }}>
      {topBar}
      {sidebar ? (
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: sw, background: t.side, borderRight: `0.5px solid ${t.border}`, padding: '52px 10px 0', boxSizing: 'border-box' }}>
          {[['New chat', true], ['Chats'], ['Projects'], ['Artifacts'], ['Code']].map(([l, n]) => (
            <div key={l as string} style={{ display: 'flex', alignItems: 'center', gap: 10, height: 36, padding: '0 8px', borderRadius: 8, fontSize: 14, color: t.text, fontWeight: n ? 600 : 400 }}>
              {n ? <div style={{ width: 24, height: 24, borderRadius: 12, background: t.accent, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><IcPlus s={16} c="#fff" w={2.2} /></div>
                : <div style={{ width: 24, display: 'flex', justifyContent: 'center', color: t.text2 }}>{l === 'Chats' ? <IcChat s={18} /> : l === 'Projects' ? <IcFolder s={18} /> : l === 'Artifacts' ? <IcImage s={18} /> : <IcCode s={18} />}</div>}
              {l}
            </div>
          ))}
          <div style={{ fontSize: 12, color: t.text3, padding: '18px 8px 6px' }}>Recents</div>
          {recents.map((r, i) => (
            <div key={i} style={{ height: 32, display: 'flex', alignItems: 'center', padding: '0 8px', borderRadius: 8, fontSize: 14, color: t.text2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              background: i === 0 ? t.bg3 : undefined }}>{r}</div>
          ))}
          <div style={{ position: 'absolute', left: 10, right: 10, bottom: 12, display: 'flex', alignItems: 'center', gap: 10, padding: 8 }}>
            <div style={{ width: 32, height: 32, borderRadius: 16, background: '#3D3D3A', color: '#fff', fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>A</div>
            <div style={{ lineHeight: 1.25 }}><div style={{ fontSize: 14, color: t.text, fontWeight: 600 }}>Adita</div><div style={{ fontSize: 12, color: t.text3 }}>Max plan</div></div>
          </div>
        </div>
      ) : null}
      <div style={{ position: 'absolute', left: sw, right: 0, top: 0, height: 52, display: 'flex', alignItems: 'center', padding: '0 18px', fontSize: 14, color: t.text, gap: 6 }}>
        {title}<IcChevDown s={14} c={t.text3} />
        <div style={{ flex: 1 }} />
        <div style={{ padding: '8px 13px', borderRadius: 8, border: `0.5px solid ${t.borderStrong}`, fontSize: 13 }}>Share</div>
      </div>
      <div style={{ position: 'absolute', left: sw + (w - sw - col) / 2, width: col, top: 60, bottom: 150, overflow: 'hidden' }}>
        <Thread t={t} msgs={msgs} scroll={scroll} gap={26} />
      </div>
      <div style={{ position: 'absolute', left: sw + (w - sw - col - 40) / 2, width: col + 40, bottom: 22 }}>
        <Composer t={t} {...composer} />
      </div>
    </div>
  );
};
