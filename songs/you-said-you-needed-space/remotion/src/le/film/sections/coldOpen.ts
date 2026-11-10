// Cold open + intro: co_dot, co_count, co_space, intro (frames 0-527). earth_proof30 (creative director), Nov 8:
// one continuous shot. Deep blue space full of stars and Milky Way mist, one small blue marble; his rocket a warm spark
// leaving her; on "space" every star backs away from her (nearest first, one straggler), a step more on each echo;
// then the approach: the dot becomes a living, glowing world and we come down over her night limb.
// The camera is ONE path for 0-35.6 s (proof30.ts CAM30), returned by every builder here and in verse1.ts.
import { PAL, Section, Out, env, smooth, spark, flow, C, lerp } from './api';
import { ROCKET_DEG, SPACE, T, cam30, roomK, roomSoft, roomR } from './proof30';
import { Fmt, Pulse } from '../types';
import { starAttr } from '../stars';
export const LOOK = { lux: 1, galaxy: 1, deep: 1, dust: 0, mist: 0, motes: 0, roomX: SPACE.cx, roomY: SPACE.cy, daySide: 1, seam: 0.10, glow: 0.8, haloWide: 0.55, atmos: 1.2, stars: 1.0,
  bloom: 0.52, bloomThreshold: 0.36, vignette: 0.5, clouds: 0.3, hisWarm: 0, herCyan: 0.5, capil: 1 };
// his rocket (rel = her radii from her centre, screen axes): it lifts off her limb on frame 0 and never stops accelerating
// away; the camera falls back from her faster than he climbs, so he stays in frame all the way to "space"
function his(t: number, r: number): Pick<Out, 'sparks' | 'flows'> {
  const at = (tt: number): [number, number] => { const q = Math.max(0, tt), rho = 1.004 + 0.35 * q * q, th = ((ROCKET_DEG + 6 * smooth(0, 12, q)) * Math.PI) / 180; return [Math.cos(th) * rho, Math.sin(th) * rho]; };
  const a = 1 - smooth(12.9, 15.1, t), close = smooth(0.05, 2.0, r), ign = 1 - smooth(0.2, 1.8, t);
  const trail = Math.min(t, 2.2), pts = Array.from({ length: 26 }, (_, i) => at(t - trail * (1 - i / 25)));
  return { sparks: [spark(0, 0, { rel: at(t), size: 15 * (1 + 2.6 * close), color: PAL.filament, intensity: 3.0 * a }), spark(0, 0, { rel: at(t), size: 64 * (1 + 2.0 * close), color: PAL.ember, intensity: 0.55 * a }), // (earth_cut2, gate 7: the film's first warm: Filament core, Ember halo + trail)
      spark(0, 0, { rel: at(0), size: 150, intensity: 0.9 * ign * close })],                                   // the lift-off lights her air for a moment
    flows: [flow({ space: 'rel', pts }, 1, { tail: 1, size: 4.6 * (1 + 1.2 * close), color: PAL.ember, intensity: 1.9 * a, count: 520 })] };
}
const WAKE: Pulse[] = [{ lat: -6, lon: -60, t0: 15.3, speed: 20, strength: 0.8 }, { lat: -6, lon: -60, t0: 16.4, speed: 20, strength: 0.9 }];   // the same two rings verse1.ts carries on (its PULSES)
const space = (t: number, fmt: Fmt): Out => {
  const gone = Math.max(0, Math.min(1.4, roomR(t) / SPACE.R0)), cam = cam30(t, fmt), k = smooth(0.06, 1.2, cam.r), far = 1 - smooth(0.04, 0.5, cam.r);   // k: 1 while we are close to her (the launch)
  return { cam, grade: { ...LOOK, room: roomK(fmt), roomKeep: 0.04, roomSpin: 0.05 * Math.max(0, t - 9.0) * (1 - smooth(T.intro, T.intro + 3.1, t)), haloWide: (0.55 + 0.75 * gone) * far, glow: lerp(0.8 + 0.25 * gone, 1.15, k), seam: lerp(0.10, 0.30, k), hisWarm: 0.35 * k, herCyan: lerp(0.5, 0.7, k), riverPulse: 0.8 }, ...his(t, cam.r) };
};
export const coldOpen: Section = {
  name: 'coldOpen',
  camera: [{ at: 0, cam: cam30(0), ease: 'hold' }],
  stars: [
    // the cast (the 2,600 bright stars) backs away with the 42,000 behind them: the same function of time (proof30.ts)
    { at: 0, dur: 0.01, set: { kind: 'fn', front: false, fn: (i, t, h, _n, fmt) => { const A = starAttr(); const g = roomK(fmt) * (1 - smooth(T.intro, T.intro + 3.1, t)); return g <= 0 ? h : roomSoft(h[0], h[1], t, g, SPACE.cx, SPACE.cy, A.r2[i], A.r1[i] * 0.1); } } },
  ],
  builders: {
    co_dot: (c) => space(c.t, c.fmt),
    co_count: (c) => space(c.t, c.fmt),
    co_space: (c) => space(c.t, c.fmt),
    intro: (c) => {
      const s = space(c.t, c.fmt), g = s.grade!, k = smooth(0.15, 0.8, c.u), k2 = smooth(0.45, 1, c.u);
      return { ...s, grade: { ...g, room: roomK(c.fmt) * (1 - smooth(0, 3.1, c.lt)), haloWide: lerp(g.haloWide!, 0, smooth(0.1, 0.55, c.u)), glow: lerp(g.glow!, 1.15, k), seam: lerp(0.10, 0.30, k2), hisWarm: lerp(0, 0.35, k2), herCyan: lerp(0.5, 0.7, k),
        motes: lerp(0, 0.35, k2), mist: lerp(0, 0.15, k2), clouds: lerp(0.3, 0.22, k), riverPulse: 0.8, atmos: lerp(1.2, 1.0, k), kick: 0.9 * env(c.t, 15.3, 0.25, 0.9) + 0.9 * env(c.t, 16.4, 0.25, 0.9) },
        pulses: WAKE.filter((p) => c.t >= p.t0 - 0.05) };   // she wakes as we come to her: her light spreads from the heart of the Amazon, twice
    },
  },
};
