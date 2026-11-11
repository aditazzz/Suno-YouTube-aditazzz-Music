// The 9:16 composer's balanced wrap (LAYOUT_916.md; reference: build/cd_916/mock.html wrap()). Computed once from the
// FULL lyric line, so the words type into fixed breaks: nothing reflows mid-line and no line ends on a lone word.
// 16:9 is one line (cols 99), so every helper returns today's single-line values there. rc_916.
import type { Layout } from '../theme';

export const CH = 0.6; // JetBrains Mono advance / em
const cache = new Map<string, string[]>();
/** fewest lines that fit `cols`, then the split whose longest line is shortest */
export function wrapBalanced(text: string, cols: number): string[] {
  const key = cols + '|' + text; const hit = cache.get(key); if (hit) return hit;
  const w = text.split(' ').filter((x, i, a) => x !== '' || a.length === 1);
  const best = (words: string[], n: number): string[] | null => {
    if (n === 1) { const s = words.join(' '); return s.length <= cols ? [s] : null; }
    let out: string[] | null = null, score = 1e9;
    for (let i = 1; i < words.length; i++) {
      const a = words.slice(0, i).join(' '); if (a.length > cols) break;
      const r = best(words.slice(i), n - 1); if (!r) continue;
      const sc = Math.max(a.length, ...r.map((x) => x.length));
      if (sc < score) { score = sc; out = [a, ...r]; }
    }
    return out;
  };
  let res: string[] = [text];
  for (let n = 1; n <= 5; n++) { const r = best(w, n); if (r) { res = r; break; } }
  cache.set(key, res); return res;
}
const PAD16: [number, number, number, number] = [0, 60, 0, 40];
export const barPad = (L: Layout) => L.bar.pad ?? PAD16;
export const barLh = (L: Layout) => L.bar.lh ?? L.bar.h;
/** box height (border included) for n lines; 16:9 is the fixed h */
export const barHeight = (L: Layout, n: number) => L.fmt === '16x9' ? L.bar.h : 4 + barPad(L)[0] + barPad(L)[2] + barLh(L) * Math.max(1, n);
/** rows of a line in this layout */
export const barRows = (L: Layout, full: string) => L.fmt === '16x9' ? [full] : wrapBalanced(full, L.bar.cols ?? 99);
/** split the typed prefix of `full` into the rows of its wrap (each row's typed part) */
export function typedRows(rows: string[], typed: string): string[] {
  const out: string[] = []; let pos = 0;
  for (let i = 0; i < rows.length; i++) {
    const seg = typed.slice(pos, pos + rows[i].length);
    if (i > 0 && pos > typed.length) break;
    out.push(seg); pos += rows[i].length + 1; // + the space the break consumed
    if (pos > typed.length) break;
  }
  return out.length ? out : [''];
}
/** the docked bar's offset for an overlay lift (16:9: lift px straight up; 9:16: the centred position's mapping) */
export const barLiftXY = (L: Layout, lift: number) => L.fmt === '16x9' ? { dx: 0, dy: lift }
  : { dx: ((L.bar.centreDx ?? 0) * lift) / 440, dy: ((L.bar.centreLift ?? 440) * lift) / 440 };
/**
 * Screen position of character idx of `lineText` in the bar (after the balanced wrap), its row centre.
 * 16:9: exactly the old hand copies `L.bar.x + 2 + 40 + 46 + idx * ch`, `L.bar.y + L.bar.h / 2`.
 * `lift` = the overlay barLift at that moment (0 = docked).
 */
export function barCharPos(L: Layout, lineText: string, idx: number, lift = 0): { x: number; y: number; ch: number; row: number } {
  const font = L.bar.font, ch = font * CH;
  if (L.fmt === '16x9') return { x: L.bar.x + 2 + 40 + 46 + idx * ch, y: L.bar.y + L.bar.h / 2 - lift, ch, row: 0 };
  const rows = barRows(L, lineText), pad = barPad(L), lh = barLh(L), o = barLiftXY(L, lift);
  let r = 0, c = idx;
  while (r < rows.length - 1 && c > rows[r].length) { c -= rows[r].length + 1; r++; }
  const top = (L.bar.bottom ?? L.bar.y + L.bar.h) - o.dy - barHeight(L, rows.length);
  return { x: L.bar.x + o.dx + 2 + pad[3] + (L.bar.chev ?? 46) + c * ch, y: top + 2 + pad[0] + r * lh + lh / 2, ch, row: r };
}
