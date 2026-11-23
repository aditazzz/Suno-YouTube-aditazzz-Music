// rl_first30_v3: easings the v3 moves use that ease.ts does not have
/** lands past the target and settles back (overshoot ~ s * 10%) */
export const outBack = (k: number, s = 1.4) => { const c = s + 1; const x = k - 1; return 1 + c * x * x * x + s * x * x; };
