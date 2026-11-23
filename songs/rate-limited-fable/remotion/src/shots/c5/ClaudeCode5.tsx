// rl5_c COPY for 5E (cut 5): + state.model (the header's model), + state.bash (her own `! cat do_it_myself.py` in Claude Code's bash
// mode: runs without the model, so it works at the limit: the file has one line), + state.stray (the cat's paw on the keys).
// The shared blocks/real/ClaudeCode.tsx is untouched. Original header:
// Claude Code in macOS Terminal, rebuilt by rl_l3_term (Nov 17) from her screenshot of the real thing
// (songs/rate-limited/refs/claude_code_terminal.png; her words via the chat: "the exact reference for every Claude Code terminal
// in the film"). Light Terminal window (white title bar, traffic lights, folder icon, "~ — ✳ Claude Code — claude — 57×18"),
// SF Mono, the orange pixel mascot measured off the ref, "Claude Code v2.1.318", the model line (her plan as a subscription:
// "Fable 5.2 · Claude Max", never "API Usage Billing"), cwd "~", the Fable notice, the two rules around the "❯" prompt, and the
// "⏵⏵ auto mode on (shift+tab to cycle)" status line. After Enter: her request in the transcript and the same limit message and
// reset time the phone app shows (LIMIT.app, one wording everywhere). No login line, no user/host, no logo marks.
// Colours are sampled from the ref; the mascot is in character cells (cw x lh) so it scales with the font.
// Lays out like a terminal: a grid of whole rows; when the content is taller than the window, the oldest rows scroll off the top.
import React from 'react';
import { LIMIT, MODEL } from '../../blocks/real/tokens';

// sampled from refs/claude_code_terminal.png
const C = {
  bg: '#FFFFFF', title: '#595959', titleRule: '#E6E6E6', edge: '#AEAEAE',
  fg: '#000000', dim: '#999999', link: '#B1BAF7', rule: '#BDBDBD', ph: '#A9A9A9', caret: '#929292',
  mascot: '#D5775B', eye: '#000000', amber: '#FEC02F', green: '#53B968', err: '#AB2B3F', userBg: '#F0F0F0',
  red: '#FF5F57', yellow: '#F9C72D', greenL: '#3DC55E', folder: '#B7E4F7',
};
const MONO = 'ui-monospace, "SF Mono", SFMono-Regular, Menlo, monospace';
const SANS = '-apple-system, "SF Pro Text", "Helvetica Neue", sans-serif';
export const CC_VERSION = 'v2.1.318';
export const CC_PLAN = 'Claude Max';
const NOTICE = 'Fable 5.2 is here for your longest and toughest coding tasks. It draws down usage faster than Opus 5.5. Switch with /model.';

export type CodeState = {
  typed: string;            // what she has typed into the prompt so far ('' = the placeholder)
  sent?: boolean;           // Enter pressed: the request moves into the transcript, the prompt clears
  limit?: number;           // 0..1: the limit lines appear
  caret?: boolean;          // caret visible (blink phase)
  thinking?: string;        // unused (kept for old callers)
  model?: string;           // rl5_c: the header model (default tokens.MODEL)
  bash?: { cmd: string; n: number; sent: boolean; out: number; file: string };   // rl5_c: bash mode: typed chars n, Enter, output 0..1
  stray?: string;           // rl5_c: what the cat typed into the prompt
};

/** word wrap to n columns (Ink wraps by word) */
const wrap = (s: string, n: number) => {
  const out: string[] = []; let cur = '';
  for (const w of s.split(' ')) {
    if (!cur) cur = w; else if ((cur + ' ' + w).length <= n) cur += ' ' + w; else { out.push(cur); cur = w; }
  }
  if (cur) out.push(cur);
  return out;
};

/** the mascot, measured off the ref in character cells (cw x lh), its box starting at column 0 of its first row; drawn one
 *  row at a time (row 0..2) so a scrolled-off row takes its slice of the mascot with it, as in a real terminal */
const Mascot: React.FC<{ cw: number; lh: number; row: number }> = ({ cw, lh, row }) => {
  const R = (x0: number, x1: number, y0: number, y1: number, c: string, k: string) =>
    <rect key={k} x={x0 * cw} y={y0 * lh} width={(x1 - x0) * cw} height={(y1 - y0) * lh} fill={c} shapeRendering="crispEdges" />;
  return (
    <svg width={9 * cw} height={lh} viewBox={`0 ${row * lh} ${9 * cw} ${lh}`} style={{ position: 'absolute', left: 0, top: 0 }}>
      {R(1.1, 8.1, 0, 2, C.mascot, 'body')}
      {R(0.46, 1.1, 0.57, 0.96, C.mascot, 'armL')}{R(8.1, 8.74, 0.57, 0.96, C.mascot, 'armR')}
      {R(2.56, 3.13, 0.57, 0.96, C.eye, 'eyeL')}{R(6.07, 6.64, 0.57, 0.96, C.eye, 'eyeR')}
      {R(1.1, 1.67, 2.14, 2.57, C.mascot, 'l1')}{R(2.1, 2.67, 2.14, 2.57, C.mascot, 'l2')}
      {R(6.53, 7.1, 2.14, 2.57, C.mascot, 'l3')}{R(7.53, 8.1, 2.14, 2.57, C.mascot, 'l4')}
    </svg>
  );
};

/** ⏵⏵ as two small filled triangles (glyph-independent, the ref's size) */
const Play2: React.FC<{ cw: number; lh: number }> = ({ cw, lh }) => (
  <svg width={2 * cw} height={lh} style={{ verticalAlign: 'top' }} viewBox="0 0 20 20" preserveAspectRatio="none">
    <path d="M1.5 6.3 L7.5 10 L1.5 13.7 Z M10.5 6.3 L16.5 10 L10.5 13.7 Z" fill={C.amber} />
  </svg>
);

type Row = { node: React.ReactNode; h?: number; key: string; bg?: string };
const PINK = '#C2306E';                         // Claude Code's bash-mode colour

export const ClaudeCode5: React.FC<{
  w?: number; h?: number; fs?: number; ui?: number; state: CodeState; chrome?: boolean; hint?: boolean;
  cols?: number; cwd?: string; title?: string; user?: string; anchor?: 'top' | 'bottom';   // cols/user/anchor: old callers, ignored
}> = ({ w = 1512, h = 945, fs = 17, ui = 1, state, chrome = true, cwd = '~', title, hint = false }) => {
  const cw = fs * 0.6, lh = fs * 1.2;                 // SF Mono advance 0.6 em; Terminal's line = 2 cells (ref: 7 x 14 px)
  const padX = Math.round(cw * 1.6), padY = Math.round(lh * 0.15);
  const bar = chrome ? 28 * ui : 0;
  const cols = Math.floor((w - 2 * padX) / cw);
  const rowsN = Math.floor((h - bar - 2 * padY) / lh);
  const rows: Row[] = [];
  const add = (node: React.ReactNode, extra?: Partial<Row>) => rows.push({ node, key: String(rows.length), ...extra });
  const dim = (s: React.ReactNode) => <span style={{ color: C.dim }}>{s}</span>;

  add(<span>{`${cwd} % claude`}</span>);
  // header: the mascot over three rows, the text at column 11
  const head = (s: React.ReactNode, row: number) => (
    <span style={{ position: 'relative', display: 'block' }}>
      <Mascot cw={cw} lh={lh} row={row} />
      <span style={{ marginLeft: 11 * cw }}>{s}</span>
    </span>
  );
  add(head(<><b style={{ fontWeight: 700 }}>Claude Code</b> {dim(CC_VERSION)}</>, 0));
  add(head(dim(`${state.model ?? MODEL} · ${CC_PLAN}`), 1));
  add(head(dim(cwd), 2));
  add(' ');
  const nl = wrap(NOTICE, cols - 2);
  nl.forEach((l, i) => {
    const k = l.indexOf('/model');
    add(<span>{'  '}{k >= 0 ? <>{l.slice(0, k)}<span style={{ color: C.link }}>/model</span>{l.slice(k + 6)}</> : l}</span>, { key: 'n' + i });
  });
  add(dim('  1 more notice hidden'));
  add(' ');
  if (state.sent) {
    // her message in the transcript: CC's grey user-message band, a little taller than a row
    const ul = wrap(state.typed, cols - 2);
    add(<>{ul.map((l, i) => <div key={i}>{i ? '  ' : '> '}{l}</div>)}</>, { bg: C.userBg, h: ul.length * lh + Math.round(lh * 0.3) });
    const lim = state.limit ?? 0;
    if (lim > 0) {
      add(<span style={{ opacity: Math.min(1, lim * 2) }}>{dim('  ⎿  ')}<span style={{ color: C.err }}>{LIMIT.app}</span></span>);
      // the "/upgrade" hint is off by default: the terminal says exactly what the app's banner says (her ask via the chat)
      if (hint) add(<span style={{ opacity: Math.min(1, Math.max(0, lim * 2 - 1)) }}>{dim('     ' + LIMIT.codeHint)}</span>);
    }
    add(' ');
  }
  const B = state.bash;
  if (B && B.sent) {
    add(<span><span style={{ color: PINK, fontWeight: 700 }}>{'! '}</span>{B.cmd}</span>, { bg: C.userBg, h: lh + Math.round(lh * 0.3) });
    if (B.out > 0) add(<span style={{ opacity: Math.min(1, B.out * 2) }}>{dim('  ⎿  ')}{B.file}</span>);
    add(' ');
  }
  // the prompt between two rules
  const bashMode = !!(B && !B.sent && !state.stray);
  const rule = <span style={{ color: bashMode ? PINK : C.rule }}>{'─'.repeat(cols)}</span>;
  add(rule);
  const typed = B && !B.sent ? B.cmd.slice(0, B.n) : state.stray ? state.stray : state.sent ? '' : state.typed;
  const caretOn = state.caret !== false;
  // the cursor cell: a block behind the character (inverse video), drawn as its own layer so the glyph sits on it like Terminal's
  const blk = (ch: string, color: string) => (
    <span style={{ position: 'relative', color: caretOn ? '#FFFFFF' : color }}>
      {caretOn ? <span data-fit="off" style={{ position: 'absolute', left: 0, top: 0, width: cw, height: lh, background: C.caret, zIndex: 0 }} /> : null}
      <span style={{ position: 'relative', zIndex: 1 }}>{ch}</span>
    </span>
  );
  const ph = 'Try "fix typecheck errors"';
  add(
    <span>
      {bashMode ? <b style={{ fontWeight: 700, color: PINK }}>{'!'}</b> : <b style={{ fontWeight: 700 }}>{'❯'}</b>}{' '}
      {typed ? <>{typed}{blk(' ', C.fg)}</> : <>{blk(ph[0], C.ph)}<span style={{ color: C.ph }}>{ph.slice(1)}</span></>}
    </span>,
  );
  add(rule);
  add(<span>{'  '}<Play2 cw={cw} lh={lh} /><span style={{ color: C.amber }}>{' auto mode on'}</span>{dim(' (shift+tab to cycle)')}</span>);
  // whole rows only; the oldest scroll off the top when the window is full
  const avail = h - bar - 2 * padY; let used = 0, first = rows.length;
  while (first > 0 && used + (rows[first - 1].h ?? lh) <= avail + 0.5) { used += rows[first - 1].h ?? lh; first--; }
  const shown = rows.slice(first);
  const ttl = title ?? `${cwd} — ✳ Claude Code — claude — ${cols}×${rowsN}`;
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: h, background: C.bg, borderRadius: chrome ? 10 * ui : 0, overflow: 'hidden',
      boxShadow: chrome ? `inset 0 0 0 ${Math.max(1, ui * 0.6)}px ${C.edge}` : undefined }}>
      {chrome ? (
        <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: bar, background: C.bg, borderBottom: `${Math.max(1, ui * 0.6)}px solid ${C.titleRule}` }}>
          {[C.red, C.yellow, C.greenL].map((c, i) => (
            <div key={c} style={{ position: 'absolute', left: (9 + i * 20) * ui, top: 8 * ui, width: 12 * ui, height: 12 * ui, borderRadius: 6 * ui, background: c,
              boxShadow: `inset 0 0 0 ${0.5 * ui}px rgba(0,0,0,0.12)` }} />
          ))}
          <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: bar, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5 * ui,
            fontFamily: SANS, fontSize: 13 * ui, fontWeight: 600, color: C.title, whiteSpace: 'nowrap' }}>
            <svg width={16 * ui} height={13 * ui} viewBox="0 0 16 13"><path d="M0.5 2 Q0.5 0.8 1.7 0.8 L5.6 0.8 L7 2.4 L14.3 2.4 Q15.5 2.4 15.5 3.6 L15.5 11.4 Q15.5 12.4 14.3 12.4 L1.7 12.4 Q0.5 12.4 0.5 11.4 Z" fill={C.folder} /></svg>
            <span>{ttl}</span>
          </div>
        </div>
      ) : null}
      <div style={{ position: 'absolute', left: 0, right: 0, top: bar + padY, fontFamily: MONO, fontSize: fs, lineHeight: `${lh}px`, color: C.fg, whiteSpace: 'pre',
        fontVariantLigatures: 'none' }}>
        {shown.map((r) => (
          <div key={r.key} style={{ height: r.h ?? lh, padding: `${((r.h ?? lh) - lh * Math.max(1, Math.floor((r.h ?? lh) / lh))) / 2}px ${padX}px`, boxSizing: 'border-box', background: r.bg }}>{r.node}</div>
        ))}
      </div>
    </div>
  );
};
export const CODE_COLORS5 = { CLAY: C.mascot, DIM: C.dim, FG: C.fg, BG: C.bg, ERR: C.err, OK: C.green };
