import { Easing, interpolate } from 'remotion';
export const W = 2560, H = 1440, FPS = 24;
// colours: ultraviolet = the founder only; orange = Claude only; green = the system holding; red = failure
export const C = {
  uv: '#7B3CFF', uvDeep: '#2B0F73', uvInk: '#170A3D', uvSoft: '#B9A0FF', uvPale: '#EDE5FF',
  white: '#FFFFFF', ink: '#120A24', paper: '#FFFDF8',
  grey: '#8E8AA0', greyDark: '#2A2833', screen: '#0E0F14', amber: '#FFB13B', amberDim: '#B77A14',
  red: '#E5304A', green: '#2FD08A', claude: '#FF7A1A', ivory: '#F2EBDD',
  skyTop: '#FFB3C7', skyMid: '#FFC9D9', skyLow: '#FFF1E6',
};
// round 2 (look bible §4): founder feeds in dark mode on ultraviolet ink
// round 4 (her "Real-app colors"): neutral real-app dark greys; ultraviolet is the car's paint only
export const D = { bg0: '#0B0C0E', bg1: '#121417', bg2: '#1A1D22', card: '#1E2126', card2: '#2A2E35', line: 'rgba(255,255,255,0.08)', text: '#F2F2F2', sub: '#B8BEC6', mute: '#8E949C', night: 'radial-gradient(ellipse at 50% 35%, #2A3240 0%, #1C2230 48%, #0D0F14 100%)' };
export const F = {
  anton: "'Anton', 'Impact', sans-serif",
  inter: "'Inter', 'Helvetica Neue', Arial, sans-serif",
  mono: "'JBMono', 'Menlo', monospace",
  vt: "'VT323', monospace",
  caveat: "'Caveat', cursive",
  corm: "'Cormorant', 'Georgia', serif",
  stencil: "'SairaStencil', sans-serif",
  marker: "'PermanentMarker', cursive",
};
// cap heights (fraction of font-size) so sizes are specified as the cap height the rules talk about
export const CAP = { anton: 0.73, inter: 0.727, mono: 0.73, vt: 0.6, caveat: 0.62, corm: 0.63 };
export const fsForCap = (cap: number, fam: keyof typeof CAP = 'inter') => Math.round(cap / CAP[fam]);
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const ease = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.45, 0, 0.2, 1) });
// settle-in with a small overshoot, never pops (>= 6 f)
export const pop = (f: number, a: number, dur = 8) =>
  interpolate(f, [a, a + dur], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.back(1.5)) });
export const lin = (f: number, a: number, b: number, from = 0, to = 1) =>
  interpolate(f, [a, b], [from, to], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
export const fmt = (n: number) => Math.round(n).toLocaleString('en-US');
