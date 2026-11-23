// Easing and motion helpers (animation-principles: every deliberate move eases in and out, overshoots and settles;
// nothing pops in). All pure functions.
export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
/** 0..1 progress of frame f through [a, b] */
export const prog = (f: number, a: number, b: number) => clamp((f - a) / Math.max(1e-6, b - a));
export const inOutCubic = (k: number) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
export const inOutSine = (k: number) => -(Math.cos(Math.PI * k) - 1) / 2;
export const outCubic = (k: number) => 1 - Math.pow(1 - k, 3);
export const inCubic = (k: number) => k * k * k;
export const outQuint = (k: number) => 1 - Math.pow(1 - k, 5);
/** overshoot then settle (s = overshoot amount, ~1.7 is classic) */
export const outBack = (k: number, s = 1.70158) => 1 + (s + 1) * Math.pow(k - 1, 3) + s * Math.pow(k - 1, 2);
/** damped spring 0 -> 1 (k in 0..1 of the settle window): overshoots ~8% and settles */
export const springy = (k: number, wobbles = 1.5, damp = 5) => (k >= 1 ? 1 : 1 - Math.exp(-damp * k) * Math.cos(wobbles * 2 * Math.PI * k));
/** gravity fall 0 -> 1 with one small bounce on landing */
export const fallBounce = (k: number) => { if (k < 0.8) return Math.pow(k / 0.8, 2); const u = (k - 0.8) / 0.2; return 1 - 0.06 * Math.sin(Math.PI * u); };
/** deterministic noise in -1..1 (for hand-held drift, flicker), smooth in t */
export const noise1 = (t: number, seed = 0) => {
  const h = (n: number) => { const x = Math.sin(n * 127.1 + seed * 311.7) * 43758.5453; return (x - Math.floor(x)) * 2 - 1; };
  const i = Math.floor(t), f = t - i, u = f * f * (3 - 2 * f); return lerp(h(i), h(i + 1), u);
};
