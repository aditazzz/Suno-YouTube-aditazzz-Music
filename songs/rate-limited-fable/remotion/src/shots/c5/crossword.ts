// 3B: the crossword grid built from script.CROSSWORD, with every crossing validated in code (N09: "if sleep is supposed to be
// the word there, then it should fit"). validateGrid() throws on any clash, on a word running off the grid, and on any
// accidental run of 2+ letters that isn't one of the listed words (a real crossword has no unclued words).
import { CROSSWORD } from '../../blocks/real/script';

export type Cell = { r: number; c: number; ch: string; num?: number };
type W = { w: string; dir: 'across' | 'down'; r: number; c: number };
export type Word = W & { num: number; cells: [number, number][] };

const cellsOf = (w: W) => w.w.split('').map((_, i) => (w.dir === 'across' ? [w.r, w.c + i] : [w.r + i, w.c]) as [number, number]);

export const buildGrid = () => {
  const n = CROSSWORD.size;
  const g: (string | null)[][] = Array.from({ length: n + 1 }, () => Array(n + 1).fill(null));
  for (const w of CROSSWORD.words as W[]) {
    cellsOf(w).forEach(([r, c], i) => {
      if (r < 1 || c < 1 || r > n || c > n) throw new Error(`crossword: ${w.w} runs off the grid at r${r}c${c}`);
      const ch = w.w[i];
      if (g[r][c] !== null && g[r][c] !== ch) throw new Error(`crossword: ${w.w} clashes at r${r}c${c}: ${g[r][c]} vs ${ch}`);
      g[r][c] = ch;
    });
  }
  // numbering: row-major, a cell gets a number when it starts a listed word
  let k = 0; const num: Record<string, number> = {};
  for (let r = 1; r <= n; r++) for (let c = 1; c <= n; c++) {
    if ((CROSSWORD.words as W[]).some((w) => w.r === r && w.c === c)) num[`${r},${c}`] = ++k;
  }
  const words: Word[] = (CROSSWORD.words as W[]).map((w) => ({ ...w, num: num[`${w.r},${w.c}`], cells: cellsOf(w) }));
  const cells: Cell[] = [];
  for (let r = 1; r <= n; r++) for (let c = 1; c <= n; c++) if (g[r][c]) cells.push({ r, c, ch: g[r][c]!, num: num[`${r},${c}`] });
  return { n, g, words, cells };
};

/** every run of 2+ filled cells across and down must be exactly one listed word, and every highlight word must be listed */
export const validateGrid = () => {
  const { n, g, words } = buildGrid();
  const listed = new Set(words.map((w) => `${w.dir}:${w.r},${w.c}:${w.w}`));
  const found: string[] = [];
  for (const dir of ['across', 'down'] as const) {
    for (let a = 1; a <= n; a++) {
      let run = '', r0 = 0, c0 = 0;
      for (let b = 1; b <= n + 1; b++) {
        const [r, c] = dir === 'across' ? [a, b] : [b, a];
        const ch = b <= n ? g[r][c] : null;
        if (ch) { if (!run) { r0 = r; c0 = c; } run += ch; }
        else { if (run.length >= 2) found.push(`${dir}:${r0},${c0}:${run}`); run = ''; }
      }
    }
  }
  const extra = found.filter((x) => !listed.has(x)); const missing = [...listed].filter((x) => !found.includes(x));
  const badHl = CROSSWORD.highlight.filter((h) => !words.some((w) => w.w === h));
  if (extra.length || missing.length || badHl.length) throw new Error(`crossword invalid: unlisted runs ${extra.join(' ')} | missing ${missing.join(' ')} | highlight not in grid ${badHl.join(' ')}`);
  return { ok: true, runs: found };
};
