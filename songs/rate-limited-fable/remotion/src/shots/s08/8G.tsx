// 8G "Don't leave me on read like this": the neon over her sofa (Live Laugh / Lie Down) flickers to its third wording
// (Live Laugh / Last Warning) on beat 2: the old word stutters and dies letter by letter, a dark beat, the new word
// sputters on; a slow push on the sign. Leads into "Okay."
// rl_cut1 B (Nov 15): the sofa wall is now a crop of S13 T6 (the two-room set's own sign, ~1100 px wide in the 5760 still:
// 1.42x to the stage instead of the old 864 px region renders stretched 3x and to 16:9). The plate's lower line (Log Off)
// is removed (tubes + their blue cast inpainted: b_work/prep_b.py) and the lower word is code neon in the sign's own
// font (Caveat Medium, outline tubes like blroom.neon_sign: fill none, tube ~8 px, bright core), sized and placed on the
// measured Log Off line (cut1b.json 8G.lower); "Live Laugh" stays the rendered pink. Dead letters = unlit grey tube.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, Grain, PlateImg, gridF } from '../s07/_lib';
import { V8 } from '../../v8';

const STUT = [0.3, 0.9, 0.1, 0.6, 0];                    // a dying letter
const SPUT = [0.7, 0.15, 0.9, 0.4, 1];                   // a letter catching
// rl_cut4_prep (Nov 17, rl_l1_room PATCH A.3, her note #19 "too light to see the sign"): the real rendered neon on the approved
// Anthro sofa wall (l1room/s8g_*.jpg, 2880x1620 -> stage x 2560/2880). The four plates differ only in the lower line's tubes and
// their light, so each letter is a full-height vertical strip (feathered) cross-faded between the lit and the unlit plate.
// Lower-line x extents from textfit_sign_s8g_*.json bboxes (2880 px): Lie Down 993.7-1794.7, Last Warning 860.4-1929.8.
const KS = 2560 / 2880;
// rl5_d5 (cut 5): one factory, two configs. Cut 4e = Lie Down -> Last Warning on l1room; cut 5 = Click Click Ship It -> Ban 429 on
// rl5_a1's c5/8G plates (same camera; lower-line x extents measured by diffing each lit plate against its dead plate, 2880 px).
type Cfg8G = { oldW: string; newW: string; oldLit: string; oldDead: string; newLit: string; newDead: string; old: [number, number]; neu: [number, number]; step: number; cx?: number; oldEdges?: number[]; newEdges?: number[];
  oldRows?: { split: number; glyphs: { i: number; row: 0 | 1; a: number; b: number }[] } };   // rl8_sign2: two-row old line (plate px)
const CFG4E: Cfg8G = { oldW: 'Lie Down', newW: 'Last Warning', oldLit: 'l1room/s8g_liedown.jpg', oldDead: 'l1room/s8g_liedown_dead.jpg',
  newLit: 'l1room/s8g_lastwarn.jpg', newDead: 'l1room/s8g_lastwarn_dead.jpg', old: [993.7, 1794.7], neu: [860.4, 1929.8], step: 1.5 };
// rl7_fixb (her H7.5/H7.24, rl7_logo's tube family): the plates are the same four with the script neon painted out and the block-letter tube sign printed
// on (workers/rl7_fixb/neon/job_8g.py -> public/c7/fix713/c8G/): click = LIVE LOVE / CLICK CLICK / SHIP IT! (3 lines, as 6A), ban = LIVE LOVE / BAN 429.
// The letters die / light across the lettering's x range (the lines are justified, so a column crosses both lower rows at once).
export const CFG8G_C5: Cfg8G = { oldW: 'Click Click Ship It', newW: 'Ban 429', oldLit: 'c7/apt/8G_click.jpg', oldDead: 'c7/apt/8G_click_dead.jpg',
  newLit: 'c7/apt/8G_ban.jpg', newDead: 'c7/apt/8G_ban_dead.jpg', old: [960, 2100], neu: [960, 2100], step: 1.0 };   // rl7_master: rl7_apt_fin's re-aimed 8G (line-2 x 974-2096 by diff)
const SIGN_CY = 690;          // the sign + the sofa back under it
const FEATHER = 14;
/** plate `src` shown only inside letter i's strip (of n across [x0, x1]); the end strips run to the frame edges */
const Strip: React.FC<{ src: string; i: number; n: number; x0: number; x1: number; op: number; e?: number[] }> = ({ src, i, n, x0, x1, op, e }) => {
  if (op <= 0.001) return null;
  const w = (x1 - x0) / n; const a = i === 0 ? -FEATHER * 2 : e ? e[i] : x0 + i * w, b = i === n - 1 ? 2560 + FEATHER * 2 : e ? e[i + 1] : x0 + (i + 1) * w;
  const m = `linear-gradient(90deg, transparent ${a - FEATHER / 2}px, #000 ${a + FEATHER / 2}px, #000 ${b - FEATHER / 2}px, transparent ${b + FEATHER / 2}px)`;
  return <PlateImg src={src} opacity={clamp(op)} style={{ WebkitMaskImage: m, maskImage: m, WebkitMaskSize: '2560px 1440px', maskSize: '2560px 1440px' }} />;
};
/** rl8_sign2: letter i of a two-row line = its own x strip [a, b] (stage px) inside its row (row 0 above `split`, row 1 below; the rows' end strips
 *  run to the frame edges, so lit + dead strips still cover the whole plate) */
const VFEATHER = 12;
const RowStrip: React.FC<{ src: string; a: number; b: number; row: 0 | 1; split: number; op: number; first: boolean; last: boolean }> = ({ src, a: a0, b: b0, row, split, op, first, last }) => {
  if (op <= 0.001) return null;
  const a = first ? -FEATHER * 2 : a0, b = last ? 2560 + FEATHER * 2 : b0;
  const m = `linear-gradient(90deg, transparent ${a - FEATHER / 2}px, #000 ${a + FEATHER / 2}px, #000 ${b - FEATHER / 2}px, transparent ${b + FEATHER / 2}px)`;
  const v = row === 0 ? `linear-gradient(180deg, #000 ${split - VFEATHER / 2}px, transparent ${split + VFEATHER / 2}px)`
    : `linear-gradient(180deg, transparent ${split - VFEATHER / 2}px, #000 ${split + VFEATHER / 2}px)`;
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, WebkitMaskImage: v, maskImage: v, WebkitMaskSize: '2560px 1440px', maskSize: '2560px 1440px' }}>
      <PlateImg src={src} opacity={clamp(op)} style={{ WebkitMaskImage: m, maskImage: m, WebkitMaskSize: '2560px 1440px', maskSize: '2560px 1440px' }} />
    </div>
  );
};
const mk = (C: Cfg8G): React.FC<ShotProps> => ({ shot, fmt }) => {
  const LINE = { old: [C.old[0] * KS, C.old[1] * KS], neu: [C.neu[0] * KS, C.neu[1] * KS] };
  const EO = C.oldEdges?.map((x) => x * KS), EN = C.newEdges?.map((x) => x * KS);   // per-glyph strip edges (v8), else equal strips
  const SIGN_CX = (C.cx ?? (Math.min(C.old[0], C.neu[0]) + Math.max(C.old[1], C.neu[1])) / 2) * KS;
  const f = useCurrentFrame(); const g = shot.from + f;
  const at = gridF(shot)[1] ?? 17; const d = f - at;
  const OLD = C.oldW, NEW = C.newW;
  const oldLit = (i: number) => { const e = d - i * C.step; return e < 0 ? 1 : e < STUT.length ? STUT[Math.floor(e)] : 0; };
  const D_NEW = Math.round((OLD.length - 1) * C.step) + STUT.length + 3;          // after the last letter dies + a dark beat of 3
  const off = (i: number) => (i * 7) % 3;                                      // letters catch a frame or two apart
  const newLit = (i: number) => { const e = d - D_NEW - off(i); return e < 0 ? 0 : e < SPUT.length ? SPUT[e] : 1; };
  const s = lerp(1.0, 1.08, inOutSine(clamp(f / (shot.dur - 1))));
  const k9 = fmt === '9x16' ? 0.37 : 1;                 // 9:16: the whole sign inside the 810 px column (Last Warning + tube + push)
  const fade = 'linear-gradient(180deg, transparent 0%, #000 12%, #000 88%, transparent 100%)';
  const oldN = Array.from(OLD).length, newN = Array.from(NEW).length;
  return (
    <AbsoluteFill>
      {k9 < 1 ? <PlateImg src={C.oldLit} filter="blur(40px) brightness(0.92)" style={{ transform: 'scale(1.3)' }} /> : null}
      <AbsoluteFill style={{ transform: `scale(${k9})`, transformOrigin: '1280px 800px', ...(k9 < 1 ? { WebkitMaskImage: fade, maskImage: fade } : {}) }}>
        <Cam cx={SIGN_CX} cy={SIGN_CY} s={s}>
          {d < D_NEW ? (
            <>
              <PlateImg src={C.oldLit} />
              {C.oldRows ? C.oldRows.glyphs.map((g, j, G) => <RowStrip key={g.i} src={C.oldDead} a={g.a * KS} b={g.b * KS} row={g.row} split={C.oldRows!.split * KS}
                op={1 - oldLit(g.i)} first={j === 0 || G[j - 1].row !== g.row} last={j === G.length - 1 || G[j + 1].row !== g.row} />)
                : Array.from(OLD).map((_, i) => <Strip key={i} src={C.oldDead} i={i} n={oldN} x0={LINE.old[0]} x1={LINE.old[1]} op={1 - oldLit(i)} e={EO} />)}
              {/* the dark beat: the unlit tubes morph from Lie Down to Last Warning over 2 frames (as the code neon did) */}
              {d >= D_NEW - 2 ? <PlateImg src={C.newDead} opacity={clamp((d - (D_NEW - 3)) / 3)} /> : null}
            </>
          ) : (
            <>
              <PlateImg src={C.newDead} />
              {Array.from(NEW).map((_, i) => <Strip key={i} src={C.newLit} i={i} n={newN} x0={LINE.neu[0]} x1={LINE.neu[1]} op={newLit(i)} e={EN} />)}
            </>
          )}
        </Cam>
      </AbsoluteFill>
      <Grain g={g} />
    </AbsoluteFill>
  );
};
export const S8_8G: ShotDef = { stage: mk(CFG4E), cx916: () => 0.5 };
// rl8_sign v8 (her approved mockup, Nov 20): line 2 = "click, click, ship it" (21 letters, ONE row) dies letter by letter -> BAN 429, both blue.
// Same plate names (the v8 overlay public dir carries the new pixels). Option A: step 0.9 so the die ends on the SAME beat as the delivered
// 19 letters at 1.0 (D_NEW = round(20 * 0.9) + 5 + 3 = 26 = round(18 * 1.0) + 8). Line x from diffing each v8 lit plate against its dead plate
// (2880 px, |d| > 25): ccsi 964-2116, BAN 429 1060-2015. cx pinned to the delivered camera centre ((960 + 2100) / 2), so the push is unchanged.
// Strip edges per glyph (Inter Display Black advances at the baked size, mid-height, 2880 px; workers/rl8_sign 8G_edges.json): narrow lowercase
// glyphs (i, l, commas) get narrow strips, so each strip is one letter instead of slicing through two.
export const CFG8G_V8: Cfg8G = { ...CFG8G_C5, oldW: 'click, click, ship it', old: [964, 2116], neu: [1060, 2015], step: 0.9, cx: 1530,
  oldEdges: [964, 1048.8, 1087.6, 1126.4, 1204.3, 1282.8, 1319.8, 1339, 1416.9, 1455.7, 1494.6, 1572.5, 1650.9, 1688, 1707.2, 1781.9, 1864.4, 1903.2, 1986.6, 2013, 2051.9, 2116],
  newEdges: [1060, 1212.6, 1377.2, 1536.3, 1578, 1727.1, 1863.3, 2015],
  // rl8_sign2 (her 09:12 "every sign big"): the line is now TWO rows at RETIRE ME's size, "click, click," / "ship it". Same 21-letter sequence and
  // step (reading order: row 1 left to right, then "ship it", so the wish dies last; D_NEW stays 26, BAN 429 strikes on the same beat, f4219 hold
  // unchanged). Each glyph's strip is its own x range inside its own row (exact: sign_v8 layout -> canvas -> 8G quad, mid x-height gaps;
  // build/rl8/rl8_sign2/edges8g.py -> 8G_edges2.json); row split y 638.1 (row 1 comma tails end 624.2, row 2 ascenders start 652.0).
  oldRows: { split: 638.1, glyphs: [
    { i: 0, row: 0, a: 975.9, b: 1097.5 }, { i: 1, row: 0, a: 1097.5, b: 1157.8 }, { i: 2, row: 0, a: 1157.8, b: 1218.1 }, { i: 3, row: 0, a: 1218.1, b: 1341.1 },
    { i: 4, row: 0, a: 1341.1, b: 1465.9 }, { i: 5, row: 0, a: 1465.9, b: 1536.9 }, { i: 7, row: 0, a: 1536.9, b: 1674.3 }, { i: 8, row: 0, a: 1674.3, b: 1734.6 },
    { i: 9, row: 0, a: 1734.6, b: 1795.0 }, { i: 10, row: 0, a: 1795.0, b: 1918.0 }, { i: 11, row: 0, a: 1918.0, b: 2042.8 }, { i: 12, row: 0, a: 2042.8, b: 2098.0 },
    { i: 14, row: 1, a: 1216.3, b: 1335.4 }, { i: 15, row: 1, a: 1335.4, b: 1468.3 }, { i: 16, row: 1, a: 1468.3, b: 1530.0 }, { i: 17, row: 1, a: 1530.0, b: 1685.2 },
    { i: 19, row: 1, a: 1685.2, b: 1767.6 }, { i: 20, row: 1, a: 1767.6, b: 1857.1 }] } };
export const C5_8G: ShotDef = { stage: mk(V8 ? CFG8G_V8 : CFG8G_C5), cx916: () => 0.5 };
