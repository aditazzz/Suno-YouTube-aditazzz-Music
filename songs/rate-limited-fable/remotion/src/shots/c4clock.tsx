// rl_cut4 (one clock, FIX4 §2a): lane L2's yoga stills (9E_w2, 9G, 12B_w2, 12B_tree) still show the OLD gold lobby wall clock through the
// glass (L2's lobby_clock() swap hides 'TR_CLOCK*' but the gold clock is 'TR_clock_*'). THE panda wall clock covers it here, as in 1D / 2E:
// centre + radius measured by projecting TR_clock_face / its ticks with each still's own camera (blrl4_c4sign C4_DEBUG_CLOCK), x 2560/2880.
import React from 'react';
import { PandaClock, pt } from '../blocks/PandaClock';

const K = 2560 / 2880;
const C1 = { cx: 0.076 * 2560, cy: 0.071 * 1440, r: 70 };                  // 9E_w2 / 9G / 12B_w2 (one camera)
export const LOBBY_CLOCK: Record<string, { cx: number; cy: number; r: number }> = {
  '9E_w2': C1, '9G': C1, '12B_w2': C1,
  '12B_tree': { cx: 0.106 * 2560, cy: 0.131 * 1440, r: 66 },
};
void K;
/** the panda over the old clock in plate `id` at time (h, m) */
export const LobbyPanda: React.FC<{ id: string; h: number; m: number }> = ({ id, h, m }) => {
  const c = LOBBY_CLOCK[id]; if (!c) return null;
  return <PandaClock cx={c.cx} cy={c.cy} r={c.r} time={pt(h, m)} variant="wall" light={0.82} blur={0.7} uid={`lp${id}`} />;
};
