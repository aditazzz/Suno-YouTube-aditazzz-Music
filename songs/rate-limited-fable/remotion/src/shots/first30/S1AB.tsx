// 1A + 1B = one move, no cut (first30.md "Shot 1AB"). Both ids render the same scene from the global frame, so the
// cut between them in shots.json is invisible. Plate: NS1 (tall night street) when it lands; placeholder = graded dawn.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { inCubic, inOutCubic, inOutSine, lerp, outBack, outCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, HeroClip, MBlur, ez, heroReady, hit, keys, PlateImg } from './kit';
import { NightStreet, STREET, tailSway, waveLit } from './street';
import { parseClock } from '../../timing';
import { FgBranch } from './glow';
import { HAVE_NS1, NS1Scene, NS1_FG, NS1_PH } from './ns';
import assets from './assets.json';
import { withTeaser } from './teaser';
import l5 from './l5.json';
import { Img, staticFile } from 'remotion';

const M = [7, 24, 42];          // the three "Mm" onsets (rl_shots cues, global frames)
const TWO_AM = 92, GREEN = 145, ZONE = 195;
const DROP0 = 190, DROP_D = 440, DROP_V = 3 * DROP_D / (216 - DROP0);   // rl6_edit: 1B's drop (starts on 190, still falling at the cut)

/** the tail's swing angle at global frame g (deg): mid-swing at frame 0, one swing across per "Mm", then a slow sway */
export const tailTheta = (g: number) => {
  const sides = [-16, 18, -17, 15];
  if (g < M[0]) return lerp(-5, sides[0], outCubic(Math.min(1, (g + 6) / (M[0] + 6))));
  for (let k = 0; k < 3; k++) {
    const a = M[k], b = k < 2 ? M[k + 1] : 1e9;
    if (g < b) {
      const swing = lerp(sides[k], sides[k + 1], outBack(Math.min(1, (g - a) / 10), 1.2));
      if (k < 2) return swing;
      // after the third swing: ease toward the slow sway
      const r = ez(g, a + 10, a + 40, inOutSine);
      return lerp(swing, 6 + tailSway(g, 0), r);
    }
  }
  return 0;
};

const clockMin = (g: number) => {
  const a = parseClock('11:58 PM'), b = parseClock('2:00 AM');
  const k = Math.min(1, Math.max(0, g / TWO_AM));
  return lerp(a, b, 1 - Math.pow(1 - k, 3.2));
};

// v3: the camera on the real tall plate NS1 (stage 2560 x 2400; frame 0 = its approved 16:9 hook framing, y 960..2400).
// Same beats as v1/v2: a slow rise, the crane to the roof on 'green' (the sign low in frame against the night sky the tall
// plate was rendered for), then the drop to the lobby glass on 'zone'. The lobby sits 118 px above the plate's bottom, so
// the landing is held at the bottom edge (the glass in the lower part of the frame, the pavement under it).
const camNS1 = (g: number) => {
  // the real plate is wider than the stand-in (three buildings at frame 0), so 'green' pushes harder: s 2.3 with BUILD
  // PASSING at ~60% of the frame height and the night sky above it (stand-in: 1.45). A small linear drift under the eased
  // keys keeps the first frames from freezing in 9:16.
  // rl6_edit (FRAMES blocker 12: 1B came to rest on the lobby, then 1C cut back up and dropped a second time): 1B no longer lands. It holds
  // on the sign after 'green', then the drop STARTS here (DROP0 -> the cut at 216, in-cubic, still accelerating at the cut, a third of the way
  // down the facade) and 1C carries the same fall on and eases it into the door (S1C.tsx camC2). One move down, one landing.
  const sk: [number, number][] = [[0, 1.0], [76, 1.08], [140, 2.3], [GREEN, 2.34], [DROP0, 2.3], [216, 2.2]];
  const s = keys(g, sk, inOutCubic) * (1 + hit(g, GREEN, 0.015, 12)) * (1 + 0.0001 * Math.min(g, 76));
  const bottom = (sc: number) => NS1_PH - 720 / sc;
  void bottom;
  const cy = (g <= DROP0 ? keys(g, [[0, 1680], [76, 1610], [140, 1292], [GREEN + 2, 1284], [DROP0, 1290]], inOutCubic)
    : 1290 + DROP_D * Math.pow(Math.min(1, (g - DROP0) / (216 - DROP0)), 3) + DROP_V * Math.max(0, g - 216)) - 0.25 * Math.min(g, 76);
  const cx = keys(g, [[0, 1280], [140, 1282], [ZONE, 1282]], inOutSine);
  return { s, cx, cy };
};
const camStand = (g: number) => {
  const s = keys(g, [[0, 1.0], [76, 1.06], [140, 1.45], [GREEN, 1.45], [ZONE, 2.1], [216, 2.13]], inOutCubic) * (1 + hit(g, GREEN, 0.015, 12));
  const cy = keys(g, [[0, 760], [76, 700], [140, 440], [GREEN + 2, 440], [ZONE, 1097], [216, 1100]], inOutCubic);
  const cx = keys(g, [[0, 1280], [140, 1270], [ZONE, 1293]], inOutSine);
  return { s, cx, cy };
};
export const camAB = HAVE_NS1 ? camNS1 : camStand;

const Scene: React.FC<{ g: number }> = ({ g }) => {
  const parcels = [180, 197, 214].map((st) => (g - st) / 18);
  if (HAVE_NS1) {
    const c = camAB(g); const fgOff = -(c.cy - 1680) * 0.12;     // the foreground lags the tilt a little (near the lens)
    return <NS1Scene g={g} win={waveLit(g, M)} sign={g < GREEN ? 0 : Math.min(1, (g - GREEN) < 1 ? 0.6 : (g - GREEN) < 2 ? 0.1 : 1)}
      clockMin={(dt) => clockMin(g + dt)} tailAngle={(u) => tailTheta(g - 3 * u)} parcels={parcels}
      // rl6_edit: the tail is the cat's: it goes up with her when she pulls back (86-96) instead of hanging over the skyline to the drop
      tail={!(heroReady('H3') && g <= 78) && g <= CAT_OUT + 10} tailLift={1500 * catGone(g) / c.s} fgOff={fgOff} />;
  }
  return (
    <NightStreet g={g} win={waveLit(g, M)} sign={g < GREEN ? 0 : Math.min(1, (g - GREEN) < 1 ? 0.6 : (g - GREEN) < 2 ? 0.1 : 1)}
      signLight={ez(g, GREEN + 1, GREEN + 5, outCubic)} clockMin={(dt) => clockMin(g + dt)}
      tailAngle={(u) => tailTheta(g - 3 * u)} parcels={parcels} tail={!(heroReady('H3') && g <= 78)} />
  );
};

/** foreground branch (a CC0 branch/lamp layer replaces it with the real plate): moves 1.3x the camera for depth */
const Branch: React.FC<{ g: number }> = ({ g }) => {
  const c = camAB(g); const off = -(c.cy - 700) * c.s * 1.3;
  return (
    <svg width={900} height={900} style={{ position: 'absolute', left: 1860, top: 60 + off, overflow: 'visible', filter: 'blur(5px)' }}>
      <path d="M 900 120 C 700 160, 520 240, 300 420 M 620 210 C 560 120, 470 80, 380 70 M 470 300 C 430 380, 360 430, 250 450" stroke="#07080c" strokeWidth={26} fill="none" strokeLinecap="round" />
      {[[300, 420], [380, 70], [250, 450], [520, 200], [430, 120], [360, 360], [600, 180]].map(([x, y], i) => (
        <ellipse key={i} cx={x} cy={y} rx={70} ry={34} transform={`rotate(${(i * 47) % 180} ${x} ${y})`} fill="#06070a" />
      ))}
    </svg>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  // fast stretch of the pedestal gets shutter blur
  const v = Math.abs(camAB(g + 0.5).cy - camAB(g - 0.5).cy) * camAB(g).s;
  return (
    <MBlur n={v > 10 ? 5 : 1} shutter={0.5} render={(dt) => {
      const c = camAB(g + dt);
      return (
        <Cam cx={c.cx} cy={c.cy} s={c.s} ph={HAVE_NS1 ? NS1_PH : undefined}>
          <HeroClip id="H3" g={g} fallback={<Scene g={g} />} />
        </Cam>
      );
    }} />
  );
};
// rl_l5_street (round 4, FIX4_PLAN R8, the watch: "the tail as an orange blob in the sky with no cat"): the cat itself, once. It lies on top
// of the screen (the frame's top edge is the ledge it lies on), so what we see is what hangs over the edge: her face peeking down at the
// street as the teaser returns to it, a fore paw, and her bushy sky tail (kept) hanging from her rump at the left. L4's one cat (rl4_kit, the ledge
// pose with the head over the edge), rendered from the street looking up (build/stills/L5_1A). Pinned to the frame (it's on the screen,
// not in the world); her rump rides the tail's entry point every frame so the tail always hangs from her. Gone before the crane.
// (A whole cat on an invisible ledge in the sky was the other way to read the note; it floats, so it doesn't make sense.)
const CAT = (l5 as any).A1 as undefined | { file: string; size: number[]; tail_root_x: number; head: number[] };
const PIV = (assets as any).NS?.NS1?.tail;
// frames: the teaser (on by default since cut 3) cuts away 6-58 and returns to the street on the beat at 59, so she peeks down just after
// the return (60), holds a beat, and pulls back up 86-96 while the crane is still slow (it only picks up speed after "2 a.m." at 92)
const CAT_IN = 60, CAT_OUT = 86;
const catPeek = (g: number) => {
  if (g < CAT_IN || g > CAT_OUT + 10) return 0;
  if (g < CAT_IN + 9) return outBack(clamp01((g - CAT_IN) / 9), 1.6);
  if (g > CAT_OUT) return 1 - inCubic(clamp01((g - CAT_OUT) / 10));
  return 1;
};
const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const catGone = (g: number) => (g > CAT_OUT ? inCubic(clamp01((g - CAT_OUT) / 10)) : 0);   // rl6_edit: the cat's pull-back 0..1
/** screen x where the sky tail crosses the frame's top edge at film frame g (NS1 tail layer about its pivot, as NS1Scene draws it) */
const tailEntryX = (g: number) => {
  if (!PIV) return 770;
  const k1 = 2560 / 5760; const c = camAB(g);
  const P = [PIV.pivot[0] * k1, PIV.pivot[1] * k1], L0 = [PIV.low_point[0] * k1, PIV.low_point[1] * k1];
  const a = ((-tailTheta(g - 1.5) - (PIV.rendered_swing_deg ?? 0)) * Math.PI) / 180;
  const dx = L0[0] - P[0], dy = L0[1] - P[1]; const x2 = dx * Math.cos(a) - dy * Math.sin(a), y2 = dx * Math.sin(a) + dy * Math.cos(a);
  const top = c.cy - 720 / c.s; const t = (top - P[1]) / y2; return (P[0] + t * x2 - c.cx) * c.s + 1280;
};
const CatPeek: React.FC<{ g: number }> = ({ g }) => {
  if (!CAT || !HAVE_NS1) return null;
  const k = catPeek(g); if (k <= 0.001) return null;
  const sc = 1.0; const w = CAT.size[0] * sc, h = CAT.size[1] * sc;
  const x = tailEntryX(g) - CAT.tail_root_x * sc;
  return <Img src={staticFile(CAT.file)} style={{ position: 'absolute', left: x, top: -(1 - k) * (h + 12), width: w, height: h }} />;
};
// v3: the CC0 branch (FgBranch, glow.tsx) replaces the drawn one; same parallax (1.3x the camera's vertical move)
const StageWithFg: React.FC<ShotProps> = (p) => {
  const f = useCurrentFrame(); const g = p.shot.from + f; const c = camAB(g);
  if (HAVE_NS1 && NS1_FG) return <><Stage {...p} /><CatPeek g={g} /></>;     // NS1 carries its own rendered foreground (lamp + branch)
  return <><Stage {...p} /><FgBranch off={-(c.cy - 760) * c.s * 1.3} fmt={p.fmt} cx916={c.cx / 2560} /></>;
};
void Branch;
const cx916 = (f: number, shot: ShotProps['shot']) => camAB(shot.from + f).cx / 2560;
// rl_teaser: the opening teaser on the three hums, OFF unless the input prop `teaser` is true (first30/teaser.tsx)
export const S1_1A_BASE: ShotDef = { stage: StageWithFg, cx916 };   // rl5_d3: cut 5 wraps it with its own teaser beats
export const S1_1A: ShotDef = withTeaser(S1_1A_BASE);
export const S1_1B: ShotDef = { stage: StageWithFg, cx916 };
void PlateImg; void inCubic; void STREET;
