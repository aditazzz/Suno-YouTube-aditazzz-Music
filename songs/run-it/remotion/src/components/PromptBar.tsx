import React from 'react';
import { C, FONT, MED, PAPER, mixC, useLayout, useT } from '../theme';
import { beatPos, lines, promptAt } from '../timing';
import { overlayAt } from '../overlay';
import { barHeight, barLiftXY, barPad, barRows, typedRows } from './barWrap';

export type BarTone = { accent?: string; border?: string; bg?: string; textColor?: string; cursor?: boolean };
/** Tones from the approved frames: default (white), crash ("Out of memory."). */
export const TONE_ERROR: BarTone = { accent: '#ff3b52', border: 'rgba(255,59,82,.85)', textColor: '#ff8a96', cursor: false };
const DRUMS_IN = 15.9085; // first drum-MIDI note: the cursor blinks in half notes before it, quarter notes after

/**
 * The prompt bar that lives inside the scene (not a caption line). Types each lyric word at its sung onset
 * (timeline.json), cursor blinking on the beat grid, submit flash when the line is sent (the payoff lift).
 * `text` overrides the lyric (e.g. "Out of memory."). `theme` 0 = paper (white intro page) .. 1 = dark (approved look).
 * `lift` moves the bar up (px); `dx` sideways.
 */
export const PromptBar: React.FC<BarTone & { text?: string; opacity?: number; lift?: number; theme?: number; scale?: number; hint?: string; hintOpacity?: number }> = ({
  accent, border, bg, textColor, cursor = true, text, opacity = 1, lift = 0, theme = 1, scale = 1, hint, hintOpacity = 1,
}) => {
  const t = useT();
  const L = useLayout();
  const p = promptAt(t);
  const shown = text ?? p.text;
  const bp = beatPos(t);
  const blinkOn = p.typing || (t < DRUMS_IN ? Math.floor(bp / 2) % 2 === 0 : Math.floor(bp) % 2 === 0);
  const f = text ? 0 : p.flash;
  const k = Math.max(0, Math.min(1, theme));
  const acc = accent ?? mixC(PAPER.ink, '#ffffff', k);
  const bgc = bg ?? mixC('rgba(249,248,245,.98)', C.barBg, k); // paper bar: luma ~248, raised above the page (243), never clipped
  const brd = border ?? mixC('rgba(23,23,28,.14)', C.barBorder, k);
  const txt = textColor ?? mixC(PAPER.ink, C.text, k);
  const shadow = mixC('rgba(23,23,28,.10)', 'rgba(0,0,0,.6)', k);
  const { x, y, w, h, font } = L.bar;
  if (L.fmt !== '16x9') return <Bar916 {...{ t, p, shown, text, f, k, acc, bgc, brd, txt, shadow, blinkOn, cursor, opacity, lift, scale, hint, hintOpacity }} />;
  return (
    <div style={{
      position: 'absolute', left: x, top: y - lift, width: w, minHeight: h, boxSizing: 'border-box', borderRadius: 22, opacity,
      transform: scale !== 1 ? `scale(${scale})` : undefined, transformOrigin: '50% 50%',
      background: f > 0 && k > 0 ? mixC(bgc, `rgba(${14 + 90 * f},${14 + 90 * f},${20 + 90 * f},.82)`, k) : bgc,
      border: `2px solid ${f > 0 ? mixC(brd, acc, 0.8 * f) : brd}`,
      boxShadow: `0 ${Math.round(12 * (1 - k))}px 40px ${shadow}` + (f > 0 ? `, 0 0 ${40 * f}px ${mixC('rgba(23,23,28,0)', acc, 0.45 * f)}` : ''),
      display: 'flex', alignItems: 'center', padding: L.fmt === '16x9' ? '0 60px 0 40px' : '24px 36px 24px 32px',
      color: txt, fontSize: font, lineHeight: 1.25, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
    }}>
      <span style={{ ...MED, color: acc, width: 46, flex: 'none', alignSelf: L.fmt === '16x9' ? 'center' : 'flex-start' }}>›</span>
      <span style={{ ...MED, flex: 1, fontFamily: FONT, minWidth: 0 }}>
        {shown}
        {cursor && <span style={{ display: 'inline-block', width: 22, height: Math.round(font * 1.1), marginLeft: 10, background: acc, verticalAlign: 'text-bottom', opacity: blinkOn ? 1 : 0 }} />}
        {/* rc_final: grey autocomplete suggestion after the cursor, only while the bar is empty (s77) */}
        {hint && !shown && hintOpacity > 0 && <span style={{ ...MED, marginLeft: 14, color: '#8a8794', opacity: hintOpacity }}>{hint}</span>}
      </span>
    </div>
  );
};

// ---------------- 9:16: the composer (LAYOUT_916.md) ----------------
const HEIGHT_EASE = 0.15; // s: the bar's height eases between prompts (ease-out); the bar bottom never moves
/** the full line the bar is showing at t (its wrap is fixed for the whole line) */
const fullOf = (p: ReturnType<typeof promptAt>, shown: string, text?: string) => {
  if (text !== undefined) return text;
  const l = p.lineIndex >= 0 ? lines[p.lineIndex] : undefined;
  const full = l ? l.words.join(' ') : '';
  return full.startsWith(shown) ? full : shown;
};
/** number of rows the bar is sized for at t: the full wrap of the line on show (an empty bar = 1) */
const rowsAt = (L: ReturnType<typeof useLayout>, t: number) => {
  const text = overlayAt(t).barText; const p = promptAt(t); const shown = text ?? p.text;
  return shown ? barRows(L, fullOf(p, shown, text)).length : 1;
};
const Bar916: React.FC<{ t: number; p: ReturnType<typeof promptAt>; shown: string; text?: string; f: number; k: number; acc: string; bgc: string; brd: string;
  txt: string; shadow: string; blinkOn: boolean; cursor: boolean; opacity: number; lift: number; scale: number; hint?: string; hintOpacity: number }> = (q) => {
  const L = useLayout();
  const { t, p, shown, f, k, acc, bgc, brd, txt, shadow } = q;
  const font = L.bar.font, lh = L.bar.lh ?? 70, pad = barPad(L), chev = L.bar.chev ?? 42;
  const full = fullOf(p, shown, q.text);
  const rows = shown ? barRows(L, full) : [''];
  const typed = shown ? typedRows(rows, shown) : [''];
  // height: the current wrap's rows; eased from the previous value over HEIGHT_EASE after the last change (pure in t)
  const n = rows.length;
  let hNow = barHeight(L, n);
  for (let d = 1; d <= Math.ceil(HEIGHT_EASE * 30) + 1; d++) {
    const tc = t - d / 30; const nPrev = rowsAt(L, tc);
    if (nPrev !== n) { const since = (d - 0.5) / 30; const e = 1 - Math.pow(1 - Math.min(1, since / HEIGHT_EASE), 3);
      hNow = barHeight(L, nPrev) + (barHeight(L, n) - barHeight(L, nPrev)) * e; break; }
  }
  const o = barLiftXY(L, q.lift);
  const bottom = (L.bar.bottom ?? L.bar.y + L.bar.h) - o.dy;
  const innerW = L.bar.w - 4 - pad[3] - chev - pad[1];
  const last = typed.length - 1;
  return (
    <div style={{
      position: 'absolute', left: L.bar.x + o.dx, top: bottom - hNow, width: L.bar.w, height: hNow, boxSizing: 'border-box', borderRadius: 26, opacity: q.opacity, overflow: 'hidden',
      transform: q.scale !== 1 ? `scale(${q.scale})` : undefined, transformOrigin: '50% 50%',
      background: f > 0 && k > 0 ? mixC(bgc, `rgba(${14 + 90 * f},${14 + 90 * f},${20 + 90 * f},.82)`, k) : bgc,
      border: `2px solid ${f > 0 ? mixC(brd, acc, 0.8 * f) : brd}`,
      boxShadow: `0 ${Math.round(12 * (1 - k))}px 40px ${shadow}` + (f > 0 ? `, 0 0 ${40 * f}px ${mixC('rgba(23,23,28,0)', acc, 0.45 * f)}` : ''),
      color: txt, fontSize: font,
    }}>
      <div style={{ ...MED, position: 'absolute', left: pad[3], top: pad[0], width: chev, height: lh, lineHeight: `${lh}px`, color: acc }}>›</div>
      {typed.map((row, i) => (
        <div key={i} style={{ ...MED, position: 'absolute', left: pad[3] + chev, top: pad[0] + i * lh, width: innerW, height: lh, lineHeight: `${lh}px`, whiteSpace: 'pre' }}>
          {row}
          {i === last && q.cursor && <span style={{ display: 'inline-block', width: 22, height: 64, marginLeft: 8, background: acc, verticalAlign: -12, opacity: q.blinkOn ? 1 : 0 }} />}
          {i === last && q.hint && !shown && q.hintOpacity > 0 && <span style={{ ...MED, marginLeft: 14, color: '#8a8794', opacity: q.hintOpacity }}>{q.hint}</span>}
        </div>
      ))}
    </div>
  );
};
