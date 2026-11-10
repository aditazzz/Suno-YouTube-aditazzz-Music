// Outro countdown + Houston tag: cd_10 .. ho_line (earth_sec_fc, Sun Nov 8; polish earth_pol_fc, Nov 9: lux look, numbers hold).
// Outro: ONE continuous camera move after the cut-heavy
// chorus (finalChorus.ts endCam): from the wide with her at the left, down to a low horizon, into the sunrise. Her countdown:
// each number forms from the stars on its word (in the sky the move leaves free), then they wander off. His satellite hangs
// in the sky on a thin data link the whole count; on "disconnected" the link dies and the satellite goes dark; she exhales one
// last glow, and the sun comes up over her. The last frames are the sunrise (never black).
// GROUND INSERT (placeholder): none needed here; the sunrise is the engine's.
import { PAL, Section, Builder, Out, smooth, spark, flow, C, env, lerp, hits } from './api';
import { Fmt, StarKey } from '../types';
import { words, at } from '../anchor';
import { camFor } from '../camera';
import { endCam, FC, starDip, NUM_LEAD, NUM_DUR, NUM_DEEP, LUXB, satPos } from './finalChorus';
const { CD0, HOU, END, F, mix } = FC;
const cw = (li: number) => words('countdown', li).map((w) => w[0]);
const DISC = cw(3)[2] ?? at('countdown/L3') + 1.2;   // "disconnected"
const HOME = 0.9;                                    // s after "disconnected" until the last of the link is back in her
// each number forms on its word in the part of the sky the camera move leaves free, then wanders off after the line's last number
const NUMS: [number, string[], { cx: number; cy: number; w: number; h: number }][] = [
  [0, ['10', '9', '8'], { cx: 0.85, cy: 0.12, w: 0.85, h: 0.95 }],
  [1, ['7', '6'], { cx: 0.9, cy: 0.2, w: 0.8, h: 0.9 }],
  [2, ['5', '4', '3'], { cx: 0.5, cy: 0.5, w: 0.8, h: 0.58 }],
  [3, ['2', '1'], { cx: 0.12, cy: 0.48, w: 0.8, h: 0.58 }],
];
// A line's last number HOLDS through the rest of its line ("... I'm doing great") and turns straight into the next line's first
// number, so every line leaves one number up for 1.2-1.6 s (phone-size reading); the "1" falls apart with the link on "disconnected".
const numKeys: StarKey[] = [
  ...NUMS.flatMap(([li, ns, box]) => ns.map((n, wi) => ({ at: cw(li)[wi] - NUM_LEAD, set: { kind: 'text' as const, text: n, box, keep: 0.3 }, dur: NUM_DUR, straggle: 0.2, curve: 0.2 }))),
  { at: DISC + 0.08, set: { kind: 'sky' as const }, dur: 1.3, straggle: 0.6, curve: 0.3 },
];
// his satellite: a fixed point in the sky (screen space), linked to the nearest point of her limb
function link(t: number, fmt: Fmt): Out {
  const cam = camFor(fmt, endCam(t)), s = satPos(fmt, t), dx = s[0] - cam.x, dy = s[1] - cam.y, d = Math.hypot(dx, dy) || 1;
  const limb: [number, number] = [cam.x + (dx / d) * cam.r * 1.0, cam.y + (dy / d) * cam.r * 1.0];
  // The link: packets of light climb from her to him the whole count. On "disconnected" it flickers and lets go at HIS end, and
  // what is left of it comes home: the line reels back down into her limb, turning from his warm to her cyan (cut 2: it used to
  // just fade). He goes red and dark; her limb flashes where her light lands, and she breathes out (cd_disc).
  const on = smooth(CD0 - 0.5, CD0 + 0.4, t), fl = t >= DISC && t < DISC + 0.3 ? (Math.sin((t - DISC) * 70) > 0 ? 1 : 0.2) : 1;
  const home = smooth(DISC + 0.22, DISC + HOME, t), N = 9, tail = 1.25, run = t < DISC ? t : DISC;   // packets travel up the link until it dies, then freeze
  const col = mix(PAL.ember, C.her, smooth(DISC + 0.1, DISC + 0.6, t)), // (earth_cut2, gate 7: the link is Ember; the last warm in the film leaves with him)
    land = env(t, DISC + HOME - 0.12, 0.1, 0.6);
  return {
    flows: on > 0.01 && home < 0.995 ? [
      // (drawn from him DOWN to her, so "home" can shorten it from his end: tail = the share of the line still out)
      flow({ space: 'screen', pts: [s, limb] }, 1, { tail: Math.max(0.001, 1 - home), size: 6.5, color: col, intensity: (t < DISC ? 0 : 1.9) * on * fl, count: 420 }),
      ...(t < DISC ? [flow({ space: 'screen', pts: [limb, s] }, 1 + ((run * 0.22) % (tail / N)), { tail, dash: N, size: 6.5, color: col, intensity: 2.1 * on, count: 420 })] : [])] : [],
    sparks: [spark(s[0], s[1], { size: 20 + 6 * hits(t, [DISC], 0.2), color: mix(C.his, C.red, Math.max(0.55 - 0.3 * on, smooth(DISC, DISC + 0.3, t))), intensity: 2.0 * (1 - smooth(DISC + 0.3, DISC + 0.7, t)) * fl }),
      spark(limb[0], limb[1], { size: 9 + 26 * land, color: C.her, intensity: 1.1 * on * (1 - smooth(DISC + HOME + 0.3, DISC + HOME + 0.9, t)) + 1.6 * land })],
  };
}
const count = (li: number): Builder => (c) => {
  const k = link(c.t, c.fmt), view = li === 2 ? smooth(cw(2)[3] - 0.2, cw(2)[5] + 0.4, c.t) : li > 2 ? 1 : 0;
  return { cam: endCam(c.t), ...k, motes: 'drift',
    grade: { ...LUXB, deep: lerp(NUM_DEEP, 1, smooth(DISC + 0.2, DISC + 1.4, c.t)), galaxy: lerp(0.5, 1, smooth(DISC + 0.2, DISC + 1.4, c.t)), glow: 1.35 + 0.15 * view, stars: 1.6 * starDip(c.t), rivers: 1.4, riverPulse: 1.0, forest: 1.2, ocean: 1.1, kick: 0.3 * hits(c.t, cw(li), 0.3), atmos: 1.0, mist: lerp(0.6, 1.8, view), violet: 0.9, aurora: 0.2 + 0.25 * view, motes: 0.7, bloom: 0.7, herCyan: 0.9, hisWarm: 0.35 } };
};
// the sunrise (ho_sunrise + ho_line are one move; ho_line just keeps going)
const LIFT916 = 0.5;
function sunrise(t: number, fmt: Fmt): Out {
  const s = smooth(HOU - 0.2, END - 0.2, t), up = smooth(HOU + 0.2, END - 0.6, t), say = env(t, at('houston/L0'), 0.25, 1.2), k = link(t, fmt);   // say: her light swells once on the last line
  // (earth_cut2, gate 5 / fresh eyes) 9:16: the dawn sat wholly under the bottom-30% line (the app's caption block). After he has gone (HOU + 0.6) she rises up the tall frame.
  const ec = endCam(t), cam = fmt === '916' ? { ...ec, y: ec.y + LIFT916 * smooth(HOU + 0.6, END - 0.5, t) } : ec;
  return { cam, motes: 'rise',
    grade: { ...LUXB, glow: lerp(1.35, 1.05, s) + 0.5 * env(t, DISC + HOME - 0.15, 0.35, 1.3) + 0.22 * say, kick: 0.5 * say, daySide: lerp(0.12, 0.5, s), sunWarm: s, seam: lerp(0.14, 0.6, s), atmos: lerp(1.0, 1.2, s), // (earth_cut2, gate 3 + 7: the dawn was a white flood; now a warm sun on her limb with her cyan still alight below)
      stars: lerp(1.4, 0.35, s), mist: lerp(1.8, 0.8, s), violet: 0.9, aurora: 0.4 * (1 - s), rivers: 1.3, riverPulse: 0.9, motes: lerp(0.8, 1.3, s), bloom: lerp(0.7, 0.6, s), exposure: lerp(1.0, 0.9, s) },
    flows: k.flows,                                      // the last of the link still coming home across the slot change
    sparks: [...(t < DISC + HOME + 1.0 ? k.sparks ?? [] : []), spark(0, 0, { rel: [0.085, lerp(0.972, 1.022, up)], behind: true, size: lerp(30, F({ fmt }, 200, 155), up), color: PAL.filament, intensity: lerp(0.0, 1.15, smooth(0.02, 0.8, up)) }), spark(0, 0, { rel: [0.085, lerp(0.972, 1.022, up)], behind: true, size: lerp(60, F({ fmt }, 560, 420), up), color: PAL.rose, intensity: 0.16 * smooth(0.02, 0.8, up) }), // (earth_cut2: a warm dawn: Filament core, Dusk Rose rim)
      spark(0, 0, { rel: [0.085, lerp(0.972, 1.022, up)], behind: true, size: lerp(8, 34, up), color: [1, 0.86, 0.6], intensity: 1.8 * smooth(0.25, 0.9, up) })] };
}
export const outro: Section = {
  name: 'outro',
  camera: [],                                            // the camera is endCam(t), set by every builder below (one continuous path)
  stars: numKeys,
  builders: {
    cd_10: count(0),                                    // (fc_atmos's scarf fades out under the engine's slot blend)
    cd_7: count(1),
    cd_5: count(2),                                     // "enjoy the view": the horizon arrives under the numbers
    cd_disc: (c) => {                                    // the link dies on "disconnected"; she exhales one last glow
      const o = count(3)(c), ex = env(c.t, DISC + HOME - 0.15, 0.35, 1.3);   // she breathes out as her light lands
      return { ...o, grade: { ...o.grade, glow: 1.5 + 0.5 * ex, atmos: 1.0 + 0.6 * ex, motes: 0.7 + 0.8 * ex }, motes: ex > 0.05 ? 'rise' : 'drift' };
    },
    ho_sunrise: (c) => sunrise(c.t, c.fmt),
    ho_line: (c) => sunrise(c.t, c.fmt),
  },
};
