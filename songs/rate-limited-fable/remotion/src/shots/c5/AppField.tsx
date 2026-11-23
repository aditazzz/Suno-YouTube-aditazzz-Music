// rl5_c: the iOS app's composer (blocks/real/MobileApp AppComposer, same measurements off her screenshot) with two cut 5 additions,
// kept here so the shared block stays untouched: marks (logical lines tinted on their beat: 8D) and chipRing (a highlight ring on
// a Pasted card as it lands: 9C). Plus MobileHome5 / MobileChat5 wrappers that take it.
import React from 'react';
import { APP, EFFORT, F, LIMIT, MODEL, MOBILE } from '../../blocks/real/tokens';
import { LimitBanner, PastedChip } from '../../blocks/real/Parts';
import { AppHeader, IcAppMic, IcTalk, IOSKeyboard, KB_H, Spark, wrapLines } from '../../blocks/real/MobileApp';
import { IcArrowUp, IcPlus } from '../../blocks/real/Icons';
import { greetingAt } from '../../blocks/real/tokens';
import { Msg, Thread } from '../../blocks/real/ClaudeChat';

const Fill: React.FC<{ children: React.ReactNode; w?: number; style?: React.CSSProperties }> = ({ children, w, style }) => (
  <div style={{ height: 31.6, minWidth: 31.6, width: w, borderRadius: 15.8, background: APP.fill, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, ...style }}>{children}</div>
);

/** a Pasted-text card (Parts.PastedChip's look: the card, the excerpt, the PASTED tag) with the excerpt set larger and darker so the
 *  pasted ask reads at phone size when framed close (her N43 "highlight each so we can read them"), and a clay ring as it lands */
export const PastedCard: React.FC<{ excerpt: string; w: number; ring?: number }> = ({ excerpt, w, ring = 0 }) => (
  <div style={{ position: 'relative', width: w, height: w, flexShrink: 0, borderRadius: 10, background: MOBILE.card, border: `0.5px solid ${MOBILE.borderStrong}`, overflow: 'hidden',
    boxSizing: 'border-box', padding: '10px 9px 0 9px',
    boxShadow: ring > 0 ? `0 0 0 ${(2.5 * ring).toFixed(2)}px rgba(198,97,63,${(0.9 * ring).toFixed(3)}), 0 1px 2px rgba(0,0,0,0.05)` : '0 1px 2px rgba(0,0,0,0.05)' }}>
    <div style={{ fontFamily: F.ios, fontSize: 12, lineHeight: '15px', color: MOBILE.text2, whiteSpace: 'pre-wrap', wordBreak: 'break-word', height: w - 44, overflow: 'hidden' }}>{excerpt}</div>
    <div style={{ position: 'absolute', left: 8, bottom: 8, padding: '7px 10px', borderRadius: 6, border: `0.5px solid ${MOBILE.borderStrong}`, background: MOBILE.bg,
      fontFamily: F.sans, fontSize: 9.5, fontWeight: 600, letterSpacing: '0.04em', color: MOBILE.text2 }}>PASTED</div>
  </div>
);

export type FieldProps = {
  text?: string; placeholder?: string; caret?: boolean; caretOn?: boolean; chips?: string[]; chipW?: number; banner?: boolean | string; disabled?: boolean;
  model?: string; effort?: string; sendPressed?: number; maxLines?: number; marks?: { line: number; k: number }[]; chipRing?: (i: number) => number; chipCols?: number;
};
export const AppField: React.FC<FieldProps> = ({ text = '', placeholder = 'Chat with Claude', caret = false, caretOn = true, chips = [], chipW = 96, banner, disabled,
  model = MODEL, effort = EFFORT, sendPressed = 0, maxLines = 6, marks = [], chipRing }) => {
  const has = text.length > 0 || chips.length > 0;
  const fs = 20, lh = 24;
  const tagged = text ? text.split('\n').flatMap((l, li) => wrapLines(l, fs, 354).map((v) => ({ v, li }))).slice(-maxLines) : [];
  const caretEl = <span style={{ display: 'inline-block', width: 2, height: 21, marginLeft: 1, marginRight: -3, verticalAlign: '-4px', background: '#C6613F', opacity: caretOn ? 1 : 0, borderRadius: 1 }} />;
  return (
    <div style={{ position: 'relative' }}>
      {banner ? <LimitBanner t={MOBILE} mobile text={typeof banner === 'string' ? banner : LIMIT.app} /> : null}
      <div style={{ position: 'relative', background: APP.bg, borderRadius: 18, boxSizing: 'border-box', padding: '15.3px 6.8px 6.8px',
        boxShadow: 'inset 0 0.6px 0 #fff, 0 0 0 0.5px rgba(0,0,0,0.055), 0 -3px 12px rgba(0,0,0,0.035), 0 4px 16px rgba(0,0,0,0.05)' }}>
        {chips.length ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, margin: '-4px 0 10px 4px' }}>
            {chips.map((c, i) => {
              const r = chipRing ? chipRing(i) : 0;
              return <PastedCard key={i} excerpt={c} w={chipW} ring={r} />;
            })}
          </div>
        ) : null}
        {text || !chips.length ? (
          <div style={{ minHeight: lh, padding: '0 5px', fontFamily: F.ios, fontSize: fs, lineHeight: `${lh}px`, letterSpacing: '0.022em', fontWeight: text ? 400 : 480, color: text ? APP.ink : APP.gray, whiteSpace: 'pre' }}>
            {text ? tagged.map((t, i) => {
              const m = marks.find((x) => x.line === t.li); const k = m ? Math.max(0, Math.min(1, m.k)) : 0;
              return (
                <div key={i} style={{ height: lh, margin: '0 -4px', padding: '0 4px', borderRadius: 5, background: k > 0 ? `rgba(198,97,63,${(0.22 * k).toFixed(3)})` : undefined }}>
                  {t.v || ' '}{caret && i === tagged.length - 1 ? caretEl : null}
                </div>
              );
            }) : <>{placeholder}{caret ? caretEl : null}</>}
          </div>
        ) : null}
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

/** her app's new-chat screen (MobileHome's layout) with AppField */
export const MobileHome5: React.FC<{ hour?: number; field?: FieldProps; keyboard?: boolean; kbUpper?: boolean; kbPress?: string; sugg?: [string, string, string] }> = ({
  hour = 4, field = {}, keyboard = true, kbUpper, kbPress, sugg }) => {
  const cBottom = keyboard ? 852 - 537.6 : 34 + 8;
  const cTop1 = 852 - cBottom - 92;
  const mid = (100 + cTop1) / 2;
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: APP.bg, overflow: 'hidden' }}>
      <AppHeader left="menu" right="ghost" />
      <div style={{ position: 'absolute', left: (393 - 42.7) / 2, top: mid - 25.6 - 21.3 }}><Spark size={42.7} /></div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: mid + 9, textAlign: 'center', fontFamily: F.appSerif, fontSize: 27.6, fontWeight: 700, letterSpacing: '-0.03em', wordSpacing: '-0.06em',
        lineHeight: '36px', color: APP.greet, whiteSpace: 'nowrap' }}>{greetingAt(hour)}</div>
      <div style={{ position: 'absolute', left: 7.7, right: 7.7, bottom: cBottom, zIndex: 6 }}><AppField {...field} /></div>
      {keyboard ? <IOSKeyboard upper={kbUpper ?? !field.text} press={kbPress} sugg={sugg} /> : null}
    </div>
  );
};

/** the app inside a conversation (MobileChat's layout) with AppField; thread = messages newest at the bottom, scroll px */
export const MobileChat5: React.FC<{ title: string; msgs: Msg[]; field?: FieldProps; scroll?: number; hideThread?: boolean }> = ({ title, msgs, field = {}, scroll = 0, hideThread }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: MOBILE.bg, overflow: 'hidden', fontFamily: F.ios, display: 'flex', flexDirection: 'column' }}>
    <div style={{ height: 106, flexShrink: 0 }} />
    <AppHeader left="menu" right="compose" title={title} bg={MOBILE.bg} />
    <div style={{ position: 'relative', flex: 1, margin: '0 18px 14px', overflow: 'hidden', visibility: hideThread ? 'hidden' : undefined }}>
      <Thread t={MOBILE} msgs={msgs} mobile scroll={scroll} />
    </div>
    <div style={{ flexShrink: 0, padding: '0 7.7px 34px', zIndex: 6 }}><AppField placeholder="Reply to Claude" {...field} /></div>
  </div>
);
export { KB_H };
