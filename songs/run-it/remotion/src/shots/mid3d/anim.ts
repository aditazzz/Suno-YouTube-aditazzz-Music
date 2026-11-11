// Copied from ../hook/anim.ts (rc_hook) so this folder never breaks when the hook changes.
// Pure easing / spring helpers (animation-principles: every frame a pure function of time).
export const clamp = (x: number, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export const prog = (t: number, a: number, b: number) => clamp((t - a) / (b - a));
export const easeOut3 = (k: number) => 1 - Math.pow(1 - clamp(k), 3);
export const easeIn2 = (k: number) => clamp(k) * clamp(k);
export const easeInOut3 = (k: number) => { k = clamp(k); return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
export const smooth = (k: number) => { k = clamp(k); return k * k * (3 - 2 * k); };
/** Damped spring step 0 -> 1 (overshoot when damp < 1). dt in seconds; f = natural frequency (Hz). */
export function spring(dt: number, f = 2, damp = 0.6) {
  if (dt <= 0) return 0;
  const w = 2 * Math.PI * f;
  if (damp >= 1) return 1 - Math.exp(-w * dt) * (1 + w * dt);
  const wd = w * Math.sqrt(1 - damp * damp);
  return 1 - Math.exp(-damp * w * dt) * (Math.cos(wd * dt) + ((damp * w) / wd) * Math.sin(wd * dt));
}
/** Impact wobble: 1 at the hit, decaying oscillation (for squash/settle). */
export const impact = (dt: number, f = 3.2, decay = 8) => (dt < 0 ? 0 : Math.exp(-dt * decay) * Math.cos(dt * 2 * Math.PI * f));
const hx = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
export const mixHex = (a: string, b: string, k: number) => { const A = hx(a), B = hx(b); k = clamp(k);
  return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * k).toString(16).padStart(2, '0')).join(''); };
export const rgbOf = hx;
