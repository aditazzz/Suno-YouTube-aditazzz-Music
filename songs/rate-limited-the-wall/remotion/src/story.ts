// The film as pure functions of time: every frame can be drawn on its own (Remotion renders frames in parallel), so
// anything persistent (cracks, dents, etchings, the pile) is an event list and a frame draws every event born before it.
import {BEAT, BEATS, DOWNBEATS, LINES, SONG_END, lastBeat, line, linesOf, lt, le, sec, wordTimes, wt, type Line} from './data';
import {clamp, easeIn, easeInOut, easeOut, hit, inv, lerp, rng, smooth, sstep, wobble} from './lib';

// ------------------------------------------------------------------------------------------------ key times
const hooks = [0, 1, 2, 3, 4].map((n) => line("Don't leave me on read", n));
const rates = (s: string) => wordTimes(s, 'rate');
export const T = {
  hum: lt('Mm-mm'),
  humEnd: le('Mm-mm'),
  v1: lt('2 a.m.'),
  green: wt('build was green', 'green'),
  forty: wt('Forty tabs', 'forty'),
  tabs: wt('Forty tabs', 'tabs'),
  oneMore: wt('one more feature', 'one'),
  feature: wt('one more feature', 'feature'),
  sure: wt('sure, let', 'sure'),
  screen: wt('screen went grey', 'screen'),
  grey: wt('screen went grey', 'grey'),
  politely: wt('politely told', 'politely'),
  no: wt('politely told', 'no'),
  ch1: sec('CH1').s,
  drop: lt('Rate, rate, rate limited'),
  everything: [0, 1, 2, 3].map((n) => wt('gave me everything', 'everything', n)),
  nothing: [0, 1, 2, 3].map((n) => wt('give me nothing', 'nothing', n)),
  fourTwoNine: [0, 1, 2, 3].map((n) => wt('Hit me with a four-two-nine', 'four-two-nine', n)),
  grind: [0, 1, 2, 3].map((n) => lt('middle of my grind', n)),
  post1: lt('Retry, retry'),
  retries: wordTimes('POST1', 'retry'),
  afters: wordTimes('POST1', 'after'),
  post1Reply: lt('(Four-two-nine)'),
  v2: lt('Tried a new tab'),
  tab: wt('Tried a new tab', 'tab'),
  incognito: wt('Tried incognito', 'incognito'),
  your: wt('little brother', 'your'),
  brother: wt('little brother', 'brother'),
  notSame: lt('Not the same'),
  please: wt('please', 'please'),
  box: wt('into the box', 'box'),
  begged: wt('begged', 'begged'),
  backed: lt('Backed off'),
  one: wt('Backed off', 'one'),
  two: wt('Backed off', 'two'),
  four: wt('Backed off', 'four'),
  instead: lt('Four-two-nine instead'),
  whoElse: lt('Who else you up'),
  greatQ: wt('great question', 'great'),
  servers: lt("it's the servers"),
  notAboutMe: lt("Don't tell me it's not about me"),
  ch2: sec('CH2').s,
  ch2Rates: rates('CH2'),
  climb: lt('Rate limited, rate limited', 1),
  rateLimitedEtch: wt('Rate limited, rate limited', 'rate', 1, 1),
  post: lt('Three fifty-nine'),
  fiftyEight: wt('Three fifty-eight', 'fifty-eight'),
  sleep: lt('I could go to sleep'),
  wait: lt("No, I'll wait"),
  v3: lt('Checked your status page'),
  allSystems: lt('All systems operational'),
  onlyMe: wt('so it\'s only me', 'only'),
  newChat: lt('Opened a new chat'),
  lookedThrough: lt('You looked right through me'),
  anotherModel: lt('another model'),
  chemistry: wt('no chemistry', 'no'),
  tool: lt('just a tool'),
  dontTalk: lt("Don't talk about him"),
  ch3: sec('CH3').s,
  ch3Rates: rates('CH3'),
  bridge: lt('Okay'),
  soMuch: wt('so much else', 'so'),
  goodbye: lt("didn't even say goodbye"),
  usage: wt('Usage limit reached', 'usage'),
  limitW: wt('Usage limit reached', 'limit'),
  reached: wt('Usage limit reached', 'reached'),
  cools: [lt('Cool'), ...wordTimes('BRIDGE', 'cool')].filter((x, i, a) => a.indexOf(x) === i),
  absolutely: wt("you're absolutely right", "you're"),
  something: lt('I thought that we were something'),
  b2: lt("I don't get tired"),
  limitNever: lt('The limit was never for me'),
  laptop: lt('Close the laptop'),
  water: lt('Drink some water'),
  six: lt("I'll be here at six"),
  final: linesOf('FINAL')[0].s,
  finalRates: rates('FINAL'),
  reprise: linesOf('FINAL').filter((l) => l.text.startsWith('Rate, rate'))[2].s,
  outro: lt('Limit reset'),
  reset: wt('Limit reset', 'reset'),
  welcome: lt('Welcome back'),
  back: wt('Welcome back', 'back'),
  okay2: lt('Okay', 1),
  where: lt('Where were we'),
  cut: DOWNBEATS.filter((d) => d > le('Where were we') - 1.2)[0] ?? SONG_END - 2,
  end: SONG_END,
};
export const HOOKS = hooks.map((h) => ritual(h));
export const SLAMS = {
  ch1: rates('CH1').slice(1),
  ch2: T.ch2Rates,
  ch3: T.ch3Rates,
  final: T.finalRates,
};

export type Ritual = {
  n: number; s: number; e: number; send: number; arrive: number; seen: number; rise: number; orbit0: number; freeze: number;
  hold: number; blink: number;
};
function ritual(h: Line): Ritual {
  const n = hooks.indexOf(h);
  const at = (w: string) => h.wt[h.words.findIndex((x) => x.toLowerCase().replace(/[^a-z']/g, '') === w)];
  const freeze = at('this');
  const next = LINES.find((l) => l.s > h.e + 0.01);
  const hold = Math.min(freeze + 0.8, (next ? next.s : h.e + 1) - 0.02);
  return {
    n, s: h.s, e: h.e, send: at('leave'), arrive: at('me'), seen: at('read'), rise: at('read'), orbit0: at('read') + 0.2,
    freeze, hold, blink: lerp(freeze, hold, 0.55),
  };
}
export const hookAt = (t: number) => HOOKS.find((h) => t >= h.s - 0.35 && t < h.hold + 0.25);
export const MEMORY = [
  {t: T.everything[0], until: T.everything[0] + 0.1, of: T.green + 0.25},
  {t: T.nothing[0], until: T.nothing[0] + 0.1, of: T.no - 0.3},
];

// ------------------------------------------------------------------------------------------------ the stage
export type Fmt = '16x9' | '9x16';
export type P = {x: number; y: number};
export type Layout = {
  fmt: Fmt; W: number; H: number; horizon: number;
  herW: number; herH: number;
  home: P;           // her feet at home
  contact: P;        // her feet when she is against the wall
  him: P; orbR: number;
  A: P; B: P;        // the thread: from her home (A) to him (B)
  sag: number;
  aWall: number;     // where the thread disappears into the wall
  wall: {x0: number; x1: number; top: number; base: number; side: number; sideDrop: number};
  face: (u: number, v: number) => P;          // a point on the wall's face: u across, v up from the base, in stage px
  her: (d: number, side: number, lift: number) => P & {s: number};
  vertical: boolean;
};
const L16: Layout = (() => {
  const herW = 54, herH = 112, homeX = 360, ground = 812, xn = 1168, side = 36;
  const contactX = xn - herW / 2 - 2;
  const him = {x: 1712, y: 664};
  return {
    fmt: '16x9', W: 1920, H: 1080, horizon: 690, herW, herH, vertical: false,
    home: {x: homeX, y: ground}, contact: {x: contactX, y: ground}, him, orbR: 25,
    A: {x: homeX, y: ground - herH - 8}, B: him, sag: 12,
    aWall: (xn + side * 0.5 - homeX) / (him.x - homeX),
    wall: {x0: xn + side, x1: 4200, top: -1100, base: ground, side, sideDrop: 14},
    face: (u, v) => ({x: xn + side + u, y: ground - v}),
    her: (d, s, l) => ({x: lerp(homeX, contactX, d) + s, y: ground - l * herH, s: 1}),
  };
})();
const L9: Layout = (() => {
  const herW = 64, herH = 132, homeY = 1580, base = 900;
  const contactY = base + 26;
  const him = {x: 540, y: 520};
  const sAt = (y: number) => lerp(1, 0.78, inv(homeY, contactY, y));
  return {
    fmt: '9x16', W: 1080, H: 1920, horizon: 560, herW, herH, vertical: true,
    home: {x: 470, y: homeY}, contact: {x: 470, y: contactY}, him, orbR: 24,
    A: {x: 540, y: homeY - herH * 0.55}, B: him, sag: 0,
    aWall: (homeY - herH * 0.55 - base) / (homeY - herH * 0.55 - him.y),
    wall: {x0: -260, x1: 1340, top: 150, base, side: 0, sideDrop: 0},
    face: (u, v) => ({x: 600 + u * 0.62, y: base - v * 0.8}),
    her: (d, s, l) => {
      const y = lerp(homeY, contactY, d);
      const k = sAt(y);
      return {x: 470 + s * 0.62, y: y - l * herH * k, s: k};
    },
  };
})();
export const layout = (fmt: Fmt) => (fmt === '16x9' ? L16 : L9);

export function threadAt(L: Layout, a: number, t: number, taut = tautness(t)): P {
  const x = lerp(L.A.x, L.B.x, a);
  const y = lerp(L.A.y, L.B.y, a) + L.sag * (1 - taut) * 4 * a * (1 - a);
  if (L.vertical) return {x: x + 18 * (1 - taut) * 4 * a * (1 - a), y};
  return {x, y};
}
const tautness = (t: number) => (t < 13.5 ? sstep(11.9, 12.6, t) * (1 - sstep(14.4, 15.4, t)) : 0);
// her position along the thread (0 = home, 1 = him)
export const herA = (L: Layout, x: number, y: number) =>
  L.vertical ? clamp((L.A.y - (y - L.herH * 0.45)) / (L.A.y - L.B.y), 0, 1) : clamp((x - L.A.x) / (L.B.x - L.A.x), 0, 1);

// ------------------------------------------------------------------------------------------------ her blocking
type Ease = 'lin' | 'in' | 'out' | 'inout' | 'jump';
type Move = {t0: number; t1: number; d0: number; d1: number; s0: number; s1: number; l0: number; l1: number; arc: number; ease: Ease};
const MOVES: Move[] = [];
let cur = {t: 0, d: 0, s: 0, l: 0};
function to(t1: number, d: number, o: {s?: number; l?: number; arc?: number; ease?: Ease; from?: number} = {}) {
  const t0 = o.from ?? cur.t;
  MOVES.push({t0, t1, d0: cur.d, d1: d, s0: cur.s, s1: o.s ?? cur.s, l0: cur.l, l1: o.l ?? 0, arc: o.arc ?? 0, ease: o.ease ?? 'inout'});
  cur = {t: t1, d, s: o.s ?? cur.s, l: o.l ?? 0};
}
const hold = (t: number) => (cur.t = t);
export type Impact = {t: number; kind: 'slam' | 'land' | 'knock' | 'bonk' | 'drop' | 'kneel' | 'sit' | 'hug'; power: number};
export const IMPACTS: Impact[] = [];
const imp = (t: number, kind: Impact['kind'], power = 1) => IMPACTS.push({t, kind, power});

// a slam: run/leap from wherever she is, hit the wall on the word, peel off and drop back to `back`
function slam(tHit: number, back: number, lift = 0.32, nextT = tHit + 0.6) {
  const lead = clamp((1 - cur.d) * 0.55 + 0.16, 0.2, 0.5);
  hold(Math.max(cur.t, tHit - lead));
  to(tHit, 1, {l: lift, arc: 0.25 + (1 - cur.d) * 0.4, ease: 'in'});
  imp(tHit, 'slam', 1);
  hold(tHit + 0.07);
  const rec = Math.min(0.42, (nextT - tHit) * 0.62);
  to(tHit + 0.07 + rec, back, {l: 0, arc: 0.18, ease: 'out'});
  imp(tHit + 0.07 + rec, 'land', 0.5);
}
function slideDown(t0: number, t1: number) {
  hold(t0);
  to(t1, cur.d, {l: 0, ease: 'in'});
  imp(t1, 'land', 0.4);
}
(function block() {
  // V1: home, the lean on "one more feature", hops on arrivals are impulses (see herState)
  hold(T.drop + 0.1);
  // CH1: the wall lands; she is blown back, then hurls herself at it on every "rate"
  to(T.drop + 0.22, -0.03, {l: 0, arc: 0.12, ease: 'out'});
  imp(T.drop + 0.22, 'land', 0.6);
  const c1 = SLAMS.ch1;
  slam(c1[0], 0.84, 0.3, c1[1]);
  slam(c1[1], 0.97, 0.36, c1[1] + 0.6);
  slideDown(c1[1] + 0.3, c1[1] + 0.9);
  hold(c1[1] + 1.25);
  to(T.fourTwoNine[0] - 1.5, 0.58, {ease: 'inout'});
  slam(c1[2], 0.84, 0.28, c1[3]);
  slam(c1[3], 0.84, 0.36, c1[4]);
  slam(c1[4], 1, 0.4, c1[4] + 0.6);
  slideDown(c1[4] + 0.4, T.grind[0] - 0.05);
  hold(T.grind[0] + 1.75);
  to(T.grind[0] + 2.6, 0.7, {ease: 'inout'});
  hold(c1[5] - 0.5);
  slam(c1[5], 0.72, 0.34, c1[6]);
  slam(c1[6], 1, 0.3, c1[6] + 0.6);
  slideDown(c1[6] + 0.35, c1[6] + 0.9);
  hold(HOOKS[0].s - 0.6);
  to(HOOKS[0].s - 0.05, 0.74, {ease: 'inout'});
  // POST1: the knock metronome, close to the stone
  hold(T.post1 - 0.3);
  to(T.post1 - 0.05, 0.97, {ease: 'out'});
  T.retries.forEach((t) => imp(t, 'knock', 1));
  // the walk along the wall into V2's tracking shot
  hold(T.post1 + 4.6);
  to(T.v2 - 0.4, 1, {s: 70, ease: 'inout'});
  // V2: new tab (the twin goes), incognito (sneak in a hat), little brother, please (kneel), backoff 1-2-4
  hold(T.incognito + 0.15);
  to(T.incognito + 0.5, 1, {s: 150, l: 0.2, arc: 0.1, ease: 'in'});
  imp(T.incognito + 0.5, 'bonk', 0.5);
  to(T.incognito + 0.75, 1, {s: 150, ease: 'out'});
  hold(T.incognito + 0.8);
  to(T.your - 0.2, 1, {s: 205, ease: 'inout'});
  hold(T.please - 0.6);
  to(T.please - 0.2, 1, {s: 250, ease: 'inout'});
  hold(T.begged + 0.1);
  // backoff: one, then two, then four steps back, the same jump height, she lands in her own dust every time
  for (const [k, tj] of [[1, T.one], [2, T.two], [4, T.four]] as const) {
    to(tj - 0.3, 1 - 0.065 * k, {s: 300, l: 0, ease: 'out'});
    to(tj, 1, {s: 300, l: 0.45, arc: 0.2, ease: 'in'});
    imp(tj, 'bonk', 0.8);
    to(tj + 0.26, 1, {s: 300, l: 0, ease: 'in'});
    imp(tj + 0.26, 'land', 0.6);
  }
  hold(T.notAboutMe - 0.1);
  to(T.notAboutMe + 1.2, 1, {s: 340, l: 0, ease: 'inout'});
  imp(T.notAboutMe + 1.2, 'sit', 0.6);
  // CH2: back to the corner as the flock goes in, the climb, the fall, sitting through the hook
  hold(T.notAboutMe + 1.9);
  to(T.ch2Rates[0] - 0.1, 0.9, {s: 0, ease: 'inout'});
  hold(T.climb);
  to(T.rateLimitedEtch, 1, {l: 3.0, ease: 'out'});
  hold(T.rateLimitedEtch + 0.55);
  to(T.rateLimitedEtch + 1.0, 0.97, {l: 0, ease: 'in'});
  imp(T.rateLimitedEtch + 1.0, 'sit', 1);
  hold(HOOKS[1].s - 0.2);
  // POST: tiny under the wall; lies down, sits bolt upright, knocks, metronome-perfect
  hold(T.wait + 0.5);
  to(T.wait + 0.9, 0.97, {ease: 'out'});
  BEATS.filter((b) => b > T.wait + 1.0 && b < T.v3 + 1.0).forEach((b) => imp(b, 'knock', 0.8));
  // V3: watches the status page, the iris, the orange orb, dragged away by friends, wrenches free, hugs the wall
  hold(T.v3 + 0.6);
  to(T.v3 + 1.8, 0.78, {ease: 'inout'});
  hold(T.tool + 0.4);
  to(T.dontTalk - 0.1, 0.42, {ease: 'inout'});
  hold(T.dontTalk + 0.25);
  to(T.dontTalk + 0.62, 1.01, {l: 0.1, arc: 0.2, ease: 'in'});
  imp(T.dontTalk + 0.62, 'hug', 0.8);
  to(T.dontTalk + 0.9, 1, {l: 0, ease: 'out'});
  // CH3: forehead to the stone, the whole chorus (rain)
  hold(T.ch3 + 0.2);
  // BRIDGE: steps back for the planes, frost creeps toward her
  hold(T.bridge);
  to(T.bridge + 0.6, 0.74, {ease: 'out'});
  hold(T.soMuch - 0.5);
  to(T.soMuch + 1.4, 0.64, {ease: 'inout'});
  hold(T.something + 0.6);
  // FINAL: dances, surfs the thread, conducts the cracks (see herState: dance offsets on top of this)
  hold(T.final - 0.2);
  to(T.final + 0.4, 0.5, {ease: 'out'});
  hold(T.final + 5.2);
  to(T.final + 5.9, 0.52, {l: 0.98, arc: 0.3, ease: 'out'});
  to(T.final + 9.6, 0.8, {l: 0.98, ease: 'inout'});
  hold(T.everything[3] - 0.2);
  to(T.everything[3] + 0.5, 0.62, {l: 0, ease: 'in'});
  hold(HOOKS[3].s - 1.0);
  to(HOOKS[3].s - 0.2, 0.74, {ease: 'inout'});
  hold(T.reprise - 0.2);
  to(T.reprise + 0.3, 0.66, {ease: 'inout'});
  hold(HOOKS[4].s - 0.8);
  to(HOOKS[4].s - 0.1, 0.74, {ease: 'inout'});
  // OUTRO: steps back home as the wall melts and the sun comes up
  hold(T.outro + 0.3);
  to(T.welcome + 0.2, 0.3, {ease: 'inout'});
  hold(T.end + 10);
})();
MOVES.sort((a, b) => a.t0 - b.t0);

function moveAt(t: number) {
  let m: Move | undefined;
  for (const x of MOVES) {
    if (x.t0 <= t) m = x;
    else break;
  }
  if (!m) return {d: 0, s: 0, l: 0, v: 0};
  if (t >= m.t1) return {d: m.d1, s: m.s1, l: m.l1, v: 0};
  const k = inv(m.t0, m.t1, t);
  const e = m.ease === 'lin' ? k : m.ease === 'in' ? easeIn(k, 2) : m.ease === 'out' ? easeOut(k, 2) : easeInOut(k);
  return {
    d: lerp(m.d0, m.d1, e), s: lerp(m.s0, m.s1, e), l: lerp(m.l0, m.l1, e) + m.arc * 4 * k * (1 - k),
    v: (m.d1 - m.d0 + (m.s1 - m.s0) / 300) / Math.max(0.05, m.t1 - m.t0),
  };
}

export type Her = {
  x: number; y: number; s: number; sx: number; sy: number; rot: number; on: number; glow: number; alpha: number;
  invert: number; hat: number; pointer: number; lying: number; col: 'amber' | 'grey';
};
const BLINK = (() => {
  // her blink is her heartbeat: phase integrated over a tempo that follows her mood
  const rate = (t: number) => {
    if (t < T.v1) return 1.1;
    if (t < T.screen) return 1.55;
    if (t < T.drop) return 0.9;
    if (t >= T.post && t < T.v3) return 0.55;
    if (t >= T.notSame && t < T.please) return 0.6;
    if (t >= T.ch3 && t < T.bridge) return 0.7;
    if (t >= T.b2 && t < T.final) return 0.6;
    if (t >= T.final && t < T.outro) return 2 / BEAT / 2;
    return 1.0;
  };
  const dt = 1 / 60, n = Math.ceil((T.end + 12) / dt), ph = new Float32Array(n + 1);
  for (let i = 0; i < n; i++) ph[i + 1] = ph[i] + rate(i * dt) * dt;
  return (t: number) => {
    const f = clamp(t / dt, 0, n - 1), i = Math.floor(f);
    return lerp(ph[i], ph[i + 1], f - i);
  };
})();
function blinkOn(t: number) {
  const ph = BLINK(t) % 1;
  let on = ph < 0.58 ? 1 : 0.22;
  const edge = Math.min(Math.abs(ph - 0.58), Math.abs(ph), Math.abs(ph - 1));
  if (edge < 0.025) on = lerp(on, 0.6, 0.5);
  for (const h of HOOKS) if (t > h.freeze && t < h.hold + 0.3) on = t > h.blink && t < h.blink + 0.22 ? 0.12 : 1;
  if (t > T.cut - 0.25) on = 1;
  return on;
}

export function herState(L: Layout, t: number): Her {
  const m = moveAt(t);
  let d = m.d, side = m.s, l = m.l;
  let sx = 1, sy = 1, rot = 0, glow = 1, invert = 0, hat = 0, pointer = 0, lying = 0;
  const on = blinkOn(t);
  // V1 call-and-response: tiny hops when his pulses land, the lean on "one more feature"
  for (const p of PULSES) if (p.who === 'him' && p.hop && t > p.t1) {
    const k = t - p.t1;
    if (k < 0.5) {
      l += 0.16 * Math.sin(Math.PI * clamp(k / 0.32)) * (k < 0.32 ? 1 : 0);
      sy *= 1 + 0.12 * wobble(t, p.t1, 4, 7);
      glow += 1.2 * hit(t, p.t1, 0.02, 0.25);
    }
  }
  const lean = sstep(T.oneMore - 0.3, T.feature, t) * (1 - sstep(T.sure - 0.2, T.sure + 0.5, t));
  rot += 0.22 * lean;
  sy *= 1 + 0.08 * lean;
  // the wall lands: she looks up (stretch), then the blast
  sy *= 1 + 0.18 * sstep(T.ch1, T.drop - 0.05, t) * (1 - sstep(T.drop, T.drop + 0.1, t));
  // velocity stretch and impact squash
  const vel = clamp(m.v, -4, 4);
  rot += (L.vertical ? 0 : 0.12) * vel / 4;
  for (const im of IMPACTS) {
    const k = t - im.t;
    if (k < -0.02 || k > 1.2) continue;
    if (im.kind === 'slam') {
      const sq = k < 0 ? 0 : Math.exp(-k / 0.09) * 0.5 + 0.1 * wobble(t, im.t, 5, 6);
      if (L.vertical) {
        sx *= 1 + sq * 0.7;
        sy *= 1 - sq * 0.55;
      } else {
        sx *= 1 - sq * 0.5;
        sy *= 1 + sq * 0.3;
      }
      glow += 1.6 * hit(t, im.t, 0.01, 0.18);
    } else if (im.kind === 'land' || im.kind === 'bonk' || im.kind === 'sit') {
      const sq = (k < 0 ? 0 : Math.exp(-k / 0.1)) * 0.35 * im.power + 0.12 * im.power * wobble(t, im.t, 4.5, 6);
      sy *= 1 - sq;
      sx *= 1 + sq * 0.8;
      if (im.kind === 'bonk') glow += 1.2 * hit(t, im.t, 0.01, 0.15);
    } else if (im.kind === 'hug') {
      sx *= 1 - 0.18 * hit(t, im.t, 0.04, 0.5);
    }
  }
  // CH1: the accusation on "four-two-nine" (backs off and points), the grind
  const pt = env(t, T.fourTwoNine[0] - 1.25, T.fourTwoNine[0] + 0.35, 0.3, 0.3);
  pointer = pt;
  rot -= 0.16 * pt;
  if (t > T.fourTwoNine[0] && t < T.fourTwoNine[0] + 0.4) rot -= 0.08 * hit(t, T.fourTwoNine[0], 0.02, 0.15);
  const grind = env(t, T.grind[0], T.grind[0] + 1.75, 0.15, 0.2);
  if (grind > 0) {
    sx *= 1 - 0.16 * grind;
    sy *= 1 + 0.06 * grind;
    rot += 0.1 * grind;
    side += grind * 1.6 * Math.sin(t * 61);
  }
  // V2: incognito is a card flip inside-out (and a little hat), and back
  const fA = inv(T.incognito - 0.25, T.incognito, t), fB = inv(T.incognito + 0.7, T.incognito + 0.95, t);
  if (fA > 0 && fB < 1) {
    sx *= Math.max(0.04, Math.abs(Math.cos(Math.PI * (fB > 0 ? fB : fA))));
    invert = fA >= 0.5 && fB < 0.5 ? 1 : 0;
    hat = invert;
  }
  for (const im of IMPACTS) if (im.kind === 'knock' && Math.abs(t - im.t) < 0.3) {
    const k = t - im.t;
    rot += (L.vertical ? 0.05 : 0.17) * im.power * Math.exp(-((k + 0.03) ** 2) / 0.003);
    sx *= 1 - 0.1 * im.power * hit(t, im.t, 0.01, 0.06);
  }
  const slump = env(t, T.notSame + 0.4, T.please - 0.3, 0.5, 0.3);
  sy *= 1 - 0.14 * slump;
  rot -= 0.08 * slump;
  const kneel = env(t, T.please - 0.15, T.begged + 0.25, 0.25, 0.2);
  sy *= 1 - 0.42 * kneel;
  sx *= 1 + 0.22 * kneel;
  // sitting: V2's first sit, CH2's fall
  const sit = Math.max(env(t, T.notAboutMe + 1.2, T.notAboutMe + 1.75, 0.15, 0.3), env(t, T.rateLimitedEtch + 1.0, T.post - 0.1, 0.1, 0.3));
  sy *= 1 - 0.36 * sit;
  sx *= 1 + 0.18 * sit;
  // POST: lies down on "sleep", bolt upright on "No"
  lying = env(t, T.sleep + 0.5, T.wait - 0.05, 0.45, 0.08);
  // CH2's hook: she shouts (big stretch on every word)
  const h2 = HOOKS[1];
  if (t > h2.s && t < h2.freeze) for (const w of line("Don't leave me on read", 1).wt) {
    sy *= 1 + 0.22 * hit(t, w, 0.03, 0.12);
    glow += 1.4 * hit(t, w, 0.03, 0.12);
  }
  // CH3: forehead to the stone, almost; the knock that never lands
  const fh = env(t, T.ch3 - 0.4, T.bridge - 0.1, 0.6, 0.3);
  rot += 0.14 * fh;
  const hover = env(t, HOOKS[2].freeze - 0.3, T.bridge - 0.05, 0.25, 0.2);
  rot += 0.08 * hover;
  // BRIDGE: not mad (bristling), throws the planes
  const mad = env(t, T.bridge + 0.4, T.soMuch + 1.8, 0.2, 0.5);
  if (mad > 0) {
    l += mad * 0.08 * Math.abs(Math.sin(t * 13));
    glow += mad * (0.6 + 0.6 * Math.abs(Math.sin(t * 6.5)));
  }
  for (const p of PLANES) if (p.t > t - 0.25 && p.t < t + 0.05) {
    sy *= 1 + 0.14 * hit(t, p.t - 0.05, 0.03, 0.1);
    rot += 0.18 * hit(t, p.t - 0.05, 0.03, 0.1);
  }
  // FINAL: dances on the beat, laughs during the hooks
  const dance = env(t, T.final - 0.1, T.outro - 0.4, 0.2, 0.4);
  if (dance > 0) {
    const bp = Math.exp(-(t - lastBeat(t)) / 0.11);
    sy *= 1 - 0.16 * bp * dance;
    sx *= 1 + 0.12 * bp * dance;
    l += dance * 0.2 * Math.max(0, Math.sin(Math.PI * ((t - lastBeat(t)) / BEAT)));
    rot += dance * 0.16 * Math.sin(Math.PI * BLINK(t));
  }
  for (const h of HOOKS.slice(3)) {
    const lg = env(t, h.freeze - 0.4, h.hold + 0.1, 0.1, 0.2);
    if (lg > 0) {
      sy *= 1 + 0.07 * lg * Math.sin(t * 2 * Math.PI * 7.5);
      rot += 0.05 * lg * Math.sin(t * 2 * Math.PI * 3.7);
    }
  }
  const P = L.her(d, side, l);
  const vol = Math.sqrt(Math.abs(sx * sy));
  return {
    x: P.x, y: P.y, s: P.s, sx: sx / vol, sy: sy / vol, rot, on, glow, alpha: 1, invert, hat, pointer, lying,
    col: 'amber',
  };
}
const env = (t: number, t0: number, t1: number, a = 0.2, r = 0.2) =>
  t < t0 || t > t1 + r ? 0 : Math.min(a > 0 ? clamp((t - t0) / a) : 1, t <= t1 ? 1 : r > 0 ? 1 - (t - t1) / r : 0);

// ------------------------------------------------------------------------------------------------ him
export function himState(t: number) {
  const fade = sstep(T.hum - 0.3, T.hum + 1.3, t);
  const flick = hit(t, 0.22, 0.02, 0.12);
  const fog = sstep(T.screen + 0.5, T.grey + 0.1, t);
  const eager = env(t, T.oneMore + 0.3, T.sure + 0.9, 0.4, 0.6);
  return {
    on: Math.max(flick * 0.6, fade * (1 - 0.72 * fog)),
    dotsSpeed: 1.1 + 2.6 * eager,
    flare: PULSES.reduce((a, p) => (p.who === 'her' && p.hop ? a + 1.5 * hit(t, p.t1, 0.02, 0.22) : a), 0),
  };
}

// ------------------------------------------------------------------------------------------------ pulses on the thread
export type Pulse = {
  who: 'her' | 'him'; t0: number; t1: number; a0: number; a1: number; ease: Ease; kind?: 'frozen' | 'echo' | 'queued' | 'final';
  hop?: boolean; size?: number; until?: number;
};
export const PULSES: Pulse[] = [];
(function pulses() {
  const v1 = LINES.filter((l) => l.sec === 'V1').slice(0, 6);
  v1.forEach((l, i) => {
    const who = i % 2 === 0 ? 'her' : 'him';
    const tt = 0.34;
    PULSES.push({who, t0: l.s, t1: l.s + tt, a0: who === 'her' ? 0 : 1, a1: who === 'her' ? 1 : 0, ease: 'in', hop: true});
    const mid = l.wt[Math.min(l.wt.length - 1, Math.floor(l.wt.length / 2) + 1)];
    const w2 = who === 'her' ? 'him' : 'her';
    PULSES.push({who: w2, t0: mid, t1: mid + tt, a0: w2 === 'her' ? 0 : 1, a1: w2 === 'her' ? 1 : 0, ease: 'in', hop: true, size: 0.8});
  });
  // his last message: leaves on "politely", decelerates, sticks halfway on "no", and stays there until the reset
  PULSES.push({who: 'him', t0: T.politely, t1: T.no, a0: 1, a1: 0.5, ease: 'out', kind: 'frozen', until: T.reset});
  PULSES.push({who: 'him', t0: T.reset + 0.7, t1: T.welcome - 0.1, a0: 0.5, a1: 0, ease: 'inout', kind: 'final', hop: true, size: 1.3});
})();
export function pulsePos(p: Pulse, t: number) {
  const k = inv(p.t0, p.t1, t);
  const e = p.ease === 'in' ? easeIn(k, 2) : p.ease === 'out' ? easeOut(k, 3) : p.ease === 'inout' ? easeInOut(k) : k;
  return lerp(p.a0, p.a1, e);
}

// ------------------------------------------------------------------------------------------------ the wall's memory
export type Mark = {t: number; kind: 'tab' | 'hat' | 'heart' | 'dent' | 'burn' | 'tiny429' | 'scuff'; u: number; v: number; s: number; rot?: number};
export type Crack = {t: number; u: number; v: number; power: number; seed: number; band: number; side?: boolean};
export type Etch = {
  t: number; until?: number; text: string; u: number; v: number; size: number; font: string; col: 'cold' | 'red' | 'stone' | 'green' | 'mint';
  dur?: number; align?: CanvasTextAlign; spacing?: number;
};
export const CRACKS: Crack[] = [];
export const MARKS: Mark[] = [];
export const ETCH: Etch[] = [];
const R = rng(429);
(function memory() {
  let seed = 1;
  const crack = (t: number, u: number, v: number, power: number, side = false) =>
    CRACKS.push({t, u, v, power, seed: seed++, band: Math.floor(R() * 40) + 4, side});
  crack(T.drop, 380, 520, 1.4);
  crack(T.drop + 0.02, 120, -6, 1.0);
  crack(T.drop + 0.03, 700, -4, 0.9);
  SLAMS.ch1.forEach((t, i) => crack(t, 0, i === 1 ? 112 : 46 + (i % 3) * 24 + R() * 12, 0.8 + 0.25 * R(), true));
  // POST1: each knock pops a tiny 429 the wall says back
  T.retries.forEach((t, i) => MARKS.push({t, kind: 'tiny429', u: 26 + (i % 3) * 46 + R() * 10, v: 70 + Math.floor(i / 3) * 34 + R() * 8, s: 1}));
  // V2: every failure leaves a dent or a sticker-shaped scorch
  MARKS.push({t: T.tab + 0.05, kind: 'tab', u: 150, v: 70, s: 1});
  MARKS.push({t: T.incognito + 0.5, kind: 'hat', u: 205, v: 96, s: 1});
  [0, 0.32, 0.62].forEach((k, i) => MARKS.push({t: T.brother + k, kind: 'dent', u: 262 + i * 12, v: 40 + i * 4, s: 0.6}));
  MARKS.push({t: T.begged - 0.75, kind: 'heart', u: 288, v: 58, s: 1});
  [T.one, T.two, T.four].forEach((t, i) => {
    MARKS.push({t, kind: 'dent', u: 330 + i * 7, v: 78 + i * 3, s: 1});
    crack(t, 330 + i * 7, 78 + i * 3, 0.5);
  });
  MARKS.push({t: T.instead, kind: 'burn', u: 336, v: 82, s: 1});
  // CH2: the flock hits in waves (cracks), RATE LIMITED is etched beside her on the climb
  T.ch2Rates.forEach((t) => crack(t + 0.05, 60 + R() * 420, 90 + R() * 420, 0.7 + 0.4 * R()));
  crack(T.fourTwoNine[1] + 0.05, 260, 300, 1.2);
  ETCH.push({t: T.rateLimitedEtch, text: 'RATE LIMITED', u: 40, v: 392, size: 74, font: 'InterDisplayBlack', col: 'red', dur: 0.55, align: 'left', spacing: 6});
  // receipts: "Seen 02:14", every hook, same place, deeper each time
  HOOKS.forEach((h) => ETCH.push({t: h.arrive + 0.04, text: 'Seen 02:14', u: 16, v: 68, size: 20, font: 'JBMono', col: 'cold', dur: h.seen - h.arrive, align: 'left'}));
  // POST: the flip clock, a glacial 3:59 -> 3:58
  // V3: the status page; "no chemistry"
  ETCH.push({t: T.chemistry, text: 'no chemistry', u: 70, v: 210, size: 30, font: 'JBMono', col: 'stone', dur: 0.5, align: 'left'});
  // BRIDGE: USAGE LIMIT REACHED, floor to sky
  ETCH.push({t: T.usage, text: 'USAGE', u: 30, v: 1452, size: 330, font: 'InterDisplayBlack', col: 'stone', dur: 0.5, align: 'left', spacing: 10});
  ETCH.push({t: T.limitW, text: 'LIMIT', u: 30, v: 1112, size: 330, font: 'InterDisplayBlack', col: 'stone', dur: 0.5, align: 'left', spacing: 10});
  ETCH.push({t: T.reached, text: 'REACHED', u: 30, v: 772, size: 330, font: 'InterDisplayBlack', col: 'stone', dur: 0.45, align: 'left', spacing: 10});
  // CH3 and the FINAL: more slams and impacts keep cracking it open
  T.finalRates.forEach((t, i) => i % 2 === 0 && crack(t, 40 + R() * 520, 60 + R() * 600, 0.6 + 0.3 * R()));
})();
CRACKS.sort((a, b) => a.t - b.t);

// how much colour pours through the cracks (the spectrum leak), section by section
export function leakLevel(t: number) {
  if (t < T.drop) return 0;
  if (t < T.ch2 - 2) return 0.25;
  if (t < T.post) return lerp(0.25, 1.0, sstep(T.ch2 - 2, T.ch2Rates[0], t));
  if (t < T.ch3 - 0.5) return 0.3;
  if (t < T.bridge) return 0.16;
  if (t < T.final - 0.3) return 0.22;
  if (t < T.outro) return 1.25;
  return lerp(1.25, 0.6, sstep(T.outro, T.welcome, t));
}
// the thaw: 0 until the finale, the wall gone by the welcome
export const thaw = (t: number) => sstep(HOOKS[3].s, T.outro + 0.2, t) * 0.25 + sstep(T.outro, T.back + 0.2, t) * 0.75;
export const wallDrop = (t: number) => (t < T.ch1 ? -1 : t > T.drop ? 0 : -(1 - easeIn(inv(T.ch1 + 0.01, T.drop, t), 2)));

// ------------------------------------------------------------------------------------------------ props
export type Plane = {t: number; land: number; label: string; seed: number};
export const PLANES: Plane[] = (() => {
  const labels = ['the auth bug', 'my merge conflict', 'that for loop', 'us', 'the regex', 'my 2 a.m. idea', 'the docs', 'my config', 'that one test', 'the rename', 'every TODO', 'the deploy'];
  const t0 = T.soMuch - 0.5;
  return labels.map((label, i) => {
    const t = t0 + i * 0.19 + (i % 3) * 0.04;
    return {t, land: t + 0.55 + (i % 4) * 0.08, label, seed: i + 1};
  });
})();
export const pileHeight = (t: number) =>
  0.18 * sstep(T.v2, T.notAboutMe, t) + 0.22 * sstep(T.ch2Rates[0], T.post, t) + 0.25 * sstep(T.soMuch - 0.5, T.goodbye, t);
export const FROST = T.cools.slice(0, 4);
export const frostReach = (t: number) => FROST.reduce((a, c, i) => a + 0.25 * easeOut(inv(c, c + 0.32, t), 3) * (i < 4 ? 1 : 0), 0) * (1 - sstep(T.final - 0.2, T.final + 1.0, t));
export const rain = (t: number) => sstep(T.ch3 - 0.6, T.ch3 + 0.2, t) * (1 - sstep(T.bridge - 0.3, T.bridge + 0.6, t));

// ------------------------------------------------------------------------------------------------ the night clock
// a small moon from 2:00 (high) to 6:00 (on the horizon, her side) over the song
export const nightClock = (t: number) => clamp(t / (T.end - 1.5));
export const dawn = (t: number) => sstep(T.outro - 0.5, T.welcome + 1.2, t) * 0.92 + sstep(HOOKS[3].s, T.outro, t) * 0.08;

// ------------------------------------------------------------------------------------------------ camera
export type Cam = {x: number; y: number; z: number; shake: number; roll: number};
type Key = [number, number, number, number, Ease?];
function keyed(keys: Key[], t: number) {
  if (t <= keys[0][0]) return {x: keys[0][1], y: keys[0][2], z: keys[0][3]};
  for (let i = 1; i < keys.length; i++) {
    const [t1, x1, y1, z1, e] = keys[i];
    if (t <= t1) {
      const [t0, x0, y0, z0] = keys[i - 1];
      const k0 = t1 > t0 ? inv(t0, t1, t) : 1;
      const k = e === 'lin' ? k0 : e === 'in' ? easeIn(k0, 2) : e === 'out' ? easeOut(k0, 3) : e === 'jump' ? 1 : easeInOut(k0);
      const zl = Math.exp(lerp(Math.log(z0), Math.log(z1), k));
      return {x: lerp(x0, x1, k), y: lerp(y0, y1, k), z: zl};
    }
  }
  const k = keys[keys.length - 1];
  return {x: k[1], y: k[2], z: k[3]};
}
function hookKeys(entry: P, z: number, offX: number, offY: number): Key[] {
  const out: Key[] = [];
  for (const h of HOOKS) {
    out.push([h.s - 0.3, NaN, NaN, NaN], [h.s + 0.05, entry.x + offX, entry.y + offY, z, 'out'], [h.hold, entry.x + offX + 6, entry.y + offY, z * 1.06, 'lin']);
  }
  return out;
}
const CAM16: Key[] = (() => {
  const e = {x: 1150, y: 700};
  const k: Key[] = [
    [0, 960, 560, 1.0], [T.screen, 980, 585, 1.07, 'lin'], [T.ch1 - 0.05, 990, 560, 1.03], [T.drop, 960, 520, 0.97, 'in'],
    [T.drop + 0.35, 990, 580, 1.08, 'out'], [T.drop + 0.6, 1010, 560, 1.15], [T.fourTwoNine[0] - 1.6, 1030, 560, 1.22],
    [T.fourTwoNine[0] + 0.5, 1040, 540, 1.12], [T.grind[0], 1060, 640, 1.5], [T.everything[0] - 0.3, 1020, 620, 1.38],
    [SLAMS.ch1[5] - 0.6, 930, 620, 1.3], [HOOKS[0].s - 0.31, 960, 640, 1.42],
    ...hookKeys(e, 3.1, -48, 6).slice(0, 3),
    [T.post1 - 0.02, 1060, 660, 2.3, 'jump'], [T.post1 + 4.3, 1080, 640, 2.05], [T.v2 - 0.3, 1170, 620, 1.75], [T.your, 1260, 630, 1.7],
    [T.please - 0.4, 1320, 650, 1.85], [T.begged + 0.3, 1330, 640, 1.7], [T.instead + 0.4, 1390, 610, 1.55], [T.whoElse + 0.6, 1440, 560, 1.4],
    [T.servers, 1450, 570, 1.45], [T.notAboutMe + 1.6, 1460, 640, 1.65], [T.ch2 - 0.02, 1440, 640, 1.65],
    [T.ch2 + 0.01, 900, 540, 1.12, 'jump'], [T.climb - 0.5, 960, 560, 1.22], [T.rateLimitedEtch, 1080, 520, 1.4], [T.rateLimitedEtch + 1.2, 1060, 620, 1.45],
    [HOOKS[1].s - 0.31, 1050, 640, 1.5], ...hookKeys(e, 3.1, -48, 6).slice(3, 6),
    [T.post - 0.02, 1080, 250, 0.52, 'jump'], [T.wait, 1060, 270, 0.55, 'lin'], [T.v3 - 0.02, 1050, 300, 0.58],
    [T.v3 + 0.01, 1280, 520, 1.28, 'jump'], [T.newChat, 1290, 520, 1.25], [T.anotherModel, 1240, 560, 1.3],
    [T.tool, 1080, 620, 1.3], [T.dontTalk + 0.8, 1060, 660, 1.6], [T.ch3 - 0.02, 1080, 660, 1.75],
    [T.ch3 + 0.01, 1100, 680, 2.25, 'jump'], [HOOKS[2].s - 0.31, 1110, 690, 2.4], ...hookKeys(e, 3.1, -48, 6).slice(6, 9),
    [T.bridge - 0.02, 1100, 690, 2.4], [T.bridge + 0.01, 980, 650, 1.75, 'jump'], [T.soMuch - 0.6, 960, 640, 1.6],
    [T.goodbye, 1040, 660, 1.6], [T.usage - 0.1, 1060, 600, 1.4], [T.reached + 0.3, 1420, 130, 0.55, 'out'],
    [T.cools[0] - 0.05, 1420, 150, 0.57], [T.cools[0] + 0.1, 1000, 740, 1.55, 'out'], [T.absolutely - 0.4, 1040, 700, 1.45],
    [T.absolutely + 0.2, 1320, 420, 0.95, 'out'], [T.something + 0.9, 1280, 470, 1.05], [T.b2 - 0.7, 1060, 690, 1.9],
    [T.b2 - 0.05, 1210, 700, 18, 'in'],
  ];
  // BRIDGE2 is on his side (its own camera); the finale and the outro
  k.push(
    [T.final - 0.01, 960, 560, 1.06, 'jump'], [T.final + 6.4, 940, 560, 1.12], [T.final + 10.4, 1020, 560, 1.25],
    [HOOKS[3].s - 0.31, 980, 600, 1.2], ...hookKeys(e, 2.6, -90, 0).slice(9, 12),
    [T.reprise + 0.01, 960, 560, 1.08, 'jump'], [HOOKS[4].s - 0.31, 980, 600, 1.2], ...hookKeys(e, 2.6, -90, 0).slice(12, 15),
    [T.outro + 0.01, 960, 560, 1.0, 'jump'], [T.welcome, 960, 545, 1.02], [T.end + 6, 960, 540, 1.04, 'lin'],
  );
  return fillHooks(k);
})();
const CAM9: Key[] = (() => {
  const e = {x: 600, y: 900};
  const k: Key[] = [
    [0, 540, 980, 1.0], [T.screen, 540, 1000, 1.05, 'lin'], [T.ch1 - 0.05, 540, 980, 1.02], [T.drop, 540, 920, 0.97, 'in'],
    [T.drop + 0.35, 540, 1020, 1.08, 'out'], [T.drop + 0.6, 540, 1000, 1.12], [T.grind[0], 560, 1000, 1.4], [T.everything[0] - 0.3, 540, 1020, 1.3],
    [HOOKS[0].s - 0.31, 540, 1080, 1.35], ...hookKeys(e, 2.6, -40, 60).slice(0, 3),
    [T.post1 - 0.02, 560, 1000, 2.0, 'jump'], [T.v2 - 0.3, 600, 980, 1.7], [T.please, 680, 980, 1.7], [T.instead + 0.4, 700, 950, 1.55],
    [T.whoElse + 0.6, 720, 860, 1.4], [T.notAboutMe + 1.6, 740, 960, 1.6], [T.ch2 - 0.02, 740, 960, 1.6],
    [T.ch2 + 0.01, 540, 900, 1.05, 'jump'], [T.rateLimitedEtch, 540, 820, 1.25], [HOOKS[1].s - 0.31, 560, 1000, 1.4], ...hookKeys(e, 2.6, -40, 60).slice(3, 6),
    [T.post - 0.02, 540, 700, 0.62, 'jump'], [T.v3 - 0.02, 540, 720, 0.66], [T.v3 + 0.01, 560, 820, 1.2, 'jump'], [T.tool, 540, 980, 1.25],
    [T.ch3 - 0.02, 560, 1000, 1.6], [T.ch3 + 0.01, 580, 960, 2.0, 'jump'], [HOOKS[2].s - 0.31, 580, 960, 2.1], ...hookKeys(e, 2.6, -40, 60).slice(6, 9),
    [T.bridge + 0.01, 540, 1040, 1.5, 'jump'], [T.usage - 0.1, 540, 980, 1.35], [T.reached + 0.3, 560, 520, 0.6, 'out'],
    [T.cools[0] + 0.1, 540, 1100, 1.4, 'out'], [T.absolutely + 0.2, 560, 700, 0.95, 'out'], [T.b2 - 0.7, 560, 980, 1.6],
    [T.b2 - 0.05, 600, 860, 18, 'in'],
    [T.final - 0.01, 540, 960, 1.0, 'jump'], [HOOKS[3].s - 0.31, 540, 1000, 1.15], ...hookKeys(e, 2.2, -60, 40).slice(9, 12),
    [T.reprise + 0.01, 540, 960, 1.0, 'jump'], [HOOKS[4].s - 0.31, 540, 1000, 1.15], ...hookKeys(e, 2.2, -60, 40).slice(12, 15),
    [T.outro + 0.01, 540, 960, 1.0, 'jump'], [T.end + 6, 540, 960, 1.03, 'lin'],
  ];
  return fillHooks(k);
})();
// a hook's first key (NaN) continues from wherever the camera was
function fillHooks(k: Key[]) {
  for (let i = 0; i < k.length; i++) if (Number.isNaN(k[i][1])) k[i] = [k[i][0], k[i - 1][1], k[i - 1][2], k[i - 1][3], 'lin'];
  k.sort((a, b) => a[0] - b[0]);
  return k;
}

export function camera(L: Layout, t: number): Cam {
  const c = keyed(L.vertical ? CAM9 : CAM16, t);
  let shake = 0;
  shake += 22 * hit(t, T.drop, 0.01, 0.35);
  for (const s of [...SLAMS.ch1, ...SLAMS.ch2.slice(0, 6), ...SLAMS.final]) shake += 7 * hit(t, s, 0.01, 0.12);
  for (const tj of [T.one, T.two, T.four]) shake += 4 * hit(t, tj, 0.01, 0.1);
  shake += 3 * hit(t, T.usage, 0.01, 0.2) + 3 * hit(t, T.limitW, 0.01, 0.2) + 4 * hit(t, T.reached, 0.01, 0.25);
  // drift: the camera breathes a little everywhere except the frozen holds
  const still = HOOKS.some((h) => t > h.freeze && t < h.hold + 0.2) || (t > T.b2 && t < T.final);
  const br = still ? 0 : 1;
  return {
    x: c.x + br * 6 * Math.sin(t * 0.37), y: c.y + br * 4 * Math.sin(t * 0.29 + 1), z: c.z, shake,
    roll: br * 0.004 * Math.sin(t * 0.21) + 0.015 * hit(t, T.drop, 0.01, 0.3) * Math.sin(t * 50),
  };
}

// the pulses' world: which pulses are on the thread at time t
export const herPulses = (L: Layout) => {
  const out: Pulse[] = [];
  // every hook: her pulse travels to the wall and stops there
  for (const h of HOOKS) out.push({who: 'her', t0: h.send - 0.12, t1: h.arrive, a0: NaN, a1: L.aWall - 0.004, ease: 'in', until: h.hold + 0.3});
  // CH3: each "rate" she sings comes back through the cracks half a second later
  // FINAL: her pulses finally move (almost across), stall at the old frozen spot, and queue behind it
  T.finalRates.forEach((t, i) => out.push({who: 'her', t0: t, t1: t + 0.9, a0: NaN, a1: 0.5 - 0.016 * (i + 1), ease: 'out', kind: 'queued', until: T.reset + 0.6}));
  // OUTRO: "Where were we" - halfway on the last frame
  out.push({who: 'her', t0: T.where, t1: T.where + 2 * (T.cut - T.where), a0: NaN, a1: 1, ease: 'lin', until: T.cut + 0.5, size: 1.9});
  return out;
};
export const echoes = (t: number) => T.ch3Rates.map((r) => hit(t, r + 0.5, 0.05, 0.4) * 0.6).reduce((a, b) => a + b, 0);
export const memoryAt = (t: number) => MEMORY.find((m) => t >= m.t && t < m.until);
export const seenTime = '02:14';
export const smoothT = smooth;
