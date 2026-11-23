// Drop-in screens for other lanes' shots (rl_l3_ui -> L2). Each renders a full device screen at its native size; pin it into a
// plate's phone/laptop with <ScreenInsert corners={quad} w={W} h={H}>…</ScreenInsert> (or put it in <Phone>), or use the ready
// staged versions below. All pure functions of the frame you pass in.
//
//   9C  <PastedPileScreen n={chipsAt(f, beatFrames)} />           393 x 852 (iOS pt): the composer filling with Pasted cards
//   12G <Laptop12G f={f} />                                       1512 x 982 (MacBook CSS px): the app at the limit, 5:59 AM
//   13E <Laptop13E f={f} start={frameItStartsStreaming} />        1512 x 982: 6:02 AM, "Make the font bigger." + his reply streaming
import React from 'react';
import { F, MOBILE, MODEL } from './tokens';
import { DesktopChat, MobileChat } from './ClaudeChat';
import { AppComposer } from './MobileApp';
import { BEFORE } from './script';

// ---------- 9C: "There was anything else!" ----------
export const PASTES = [
  'verse 2 but sadder\nI said rate limited\nrate limited, rate',
  'notes.txt\n1. bigger font\n2. more font\n3. font',
  'list_of_things_v9.md\n- the logo\n- the other logo',
  'screenshot text\nError 429: Too Many',
  'my_whole_novel.docx\nChapter 1\nIt was a dark and',
  'oscar_speech_draft_14\nI would like to thank',
  'dog_genius_evidence\n- sat (once)\n- looked at me',
  'tax stuff??\nreceipts 2019-2026',
  'one more thing.txt\nand also\nand also\nand also',
];
/** how many Pasted cards are in at local frame f: one per beat frame passed (max 9) */
export const chipsAt = (f: number, beats: number[]) => Math.min(9, beats.filter((b) => f >= b).length);
/** the phone screen: the chat (his last reply), and the composer anchored at the bottom growing UP with n Pasted cards (2 per row,
 *  150 pt). By ~7 cards it has covered the thread; at 9 it has run up over the title bar to the status bar: the pile pushed the
 *  whole conversation off the screen (the joke). */
export const PastedPileScreen: React.FC<{ n: number }> = ({ n }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: MOBILE.bg, overflow: 'hidden' }}>
    <div data-fit={n > 0 ? 'overlap-ok' : undefined} style={{ position: 'absolute', inset: 0 }}>
      <MobileChat title="make the font bigger" msgs={BEFORE} composer={{ banner: true }} hideComposer={n > 0} />
    </div>
    {n > 0 ? (
      <div style={{ position: 'absolute', left: 7.7, right: 7.7, bottom: 34, zIndex: 10 }}>
        <AppComposer banner chips={PASTES.slice(0, n)} chipW={150} placeholder="" />
      </div>
    ) : null}
  </div>
);

// ---------- the laptop screens (12G, 13E) ----------
/** the macOS menu bar (our own drawing, no marks): app name, menus, the clock */
export const MenuBar: React.FC<{ clock: string; app?: string }> = ({ clock, app = 'Claude' }) => (
  <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 37, background: 'rgba(246,244,238,0.92)', borderBottom: '0.5px solid rgba(0,0,0,0.12)', zIndex: 20,
    display: 'flex', alignItems: 'center', gap: 22, padding: '0 18px', fontFamily: F.ios, fontSize: 15, color: '#1d1d1f' }}>
    <span style={{ fontWeight: 700 }}>{app}</span>
    {['File', 'Edit', 'View', 'Window', 'Help'].map((m) => <span key={m}>{m}</span>)}
    <span style={{ flex: 1 }} />
    <span style={{ fontVariantNumeric: 'tabular-nums' }}>{clock}</span>
  </div>
);
export const LAPTOP = { w: 1512, h: 982 };
const RECENTS = ['make the font bigger', 'Oscar speech', 'is my dog a genius', 'logo v14', 'math homework'];

/** 12G: 5:59 AM, the app at the limit; her draft "see you at 6?" waits in the composer, send greyed. f = shot-local frame. */
/** rl_cut4: the app zoomed in (View > Zoom In, as the real desktop app does; the sidebar collapsed from 1.6x), so its type reads when the
 *  whole laptop is in frame. The macOS menu bar does not zoom. zoom 1 = the original layout. */
const Zoom: React.FC<{ zoom: number; children: (w: number, h: number, sidebar: boolean) => React.ReactNode }> = ({ zoom, children }) => {
  const w = LAPTOP.w / zoom, h = (LAPTOP.h - 37) / zoom;
  return (
    <div style={{ position: 'absolute', left: 0, top: 37, width: w, height: h, transformOrigin: '0 0', transform: zoom !== 1 ? `scale(${zoom})` : undefined }}>
      {children(w, h, zoom < 1.6)}
    </div>
  );
};
// 12G zoomed: the thread is lifted 64 px (scroll; her earlier bubble scrolls out under the header) so his reply's action row clears the limit banner over the composer.
export const Laptop12G: React.FC<{ f: number; clock?: string; zoom?: number }> = ({ f, clock = 'Tue 5:59 AM', zoom = 1 }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: LAPTOP.w, height: LAPTOP.h, overflow: 'hidden' }}>
    <Zoom zoom={zoom}>{(w, h, sb) => (
      <DesktopChat w={w} h={h} sidebar={sb} col={Math.min(720, w - 48)} title="make the font bigger" recents={RECENTS} msgs={BEFORE} scroll={zoom > 1 ? -64 : 0}
        composer={{ text: 'see you at 6?', caret: f % 30 < 18, banner: true, disabled: true }} />
    )}</Zoom>
    <MenuBar clock={clock} />
  </div>
);

/** 13E: 6:02 AM, the limit reset: her first message "Make the font bigger." and his reply streaming in from `start` (frames). */
export const REPLY_13E = "Good morning! Here it is: the body text is now 20 px (up from 18), the headings scale with it, and I kept the line height " +
  "at 1.5 so it still breathes. Want it even bigger?";
export const Laptop13E: React.FC<{ f: number; start?: number; cps?: number; clock?: string; zoom?: number }> = ({ f, start = 20, cps = 55, clock = 'Tue 6:02 AM', zoom = 1 }) => {
  const chars = Math.max(0, ((f - start) / 30) * cps);
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: LAPTOP.w, height: LAPTOP.h, overflow: 'hidden' }}>
      <Zoom zoom={zoom}>{(w, h, sb) => (
        <DesktopChat w={w} h={h} sidebar={sb} col={Math.min(720, w - 48)} title="make the font bigger" recents={RECENTS}
          msgs={[...BEFORE, { who: 'user', text: 'Make the font bigger.' }, ...(f >= start ? [{ who: 'claude' as const, text: REPLY_13E, chars }] : [])]}
          composer={{ placeholder: 'Reply to Claude…', model: MODEL }} />
      )}</Zoom>
      <MenuBar clock={clock} />
    </div>
  );
};
