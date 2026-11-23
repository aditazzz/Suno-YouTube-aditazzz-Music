// 11A "I don't get tired" (CODEPLAN keep*): no cut from 10B: the door edge (a dark vertical layer) wipes across as the camera keeps
// travelling left. rl_fix2_robot (WATCH: the certificates read as colour-square filler, EMPLOYEE OF THE MONTH unreadable - its header
// sits behind the QUIET HOURS note in T24 - and he never visibly stands): the wipe now lands CLOSE on his certificate wall, a code
// insert on the lobby wall: framed EMPLOYEE OF THE MONTH certificates, every one his face (the approved D5 render, 429 paddle and all),
// MAY .. OCTOBER on brass plaques, sliding past (the claim). On beat 2 cut close to him seated against the door (the
// master camera, his new seat; T24's camera sat behind his head and never showed him stand); on the heartbeat (2:50.4, measured) he
// stands: seat -> rise (2 frames, hands on knees) -> standing tall, eyes wide open, the frame tilting up hard with him (the proof).
// Renders: blrl_fix2_robot mode 3 RLF_POSE=rise|stand (region renders on the S12 H2a scene), composite2.py.
// Text: title 84/50 px Anton, plaques 48 px on the 2560 stage (63/37/36 px at 1920); 9:16 keeps the centre card inside the safe zone.
import { PandaWallClockCompat } from '../../blocks/PandaClock';
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { cueFrame } from '../../timing';
import { Cam, hit, swap } from '../first30/kit';
import { MASTER_CLOCK, PL, Pl, WallClock, clamp, gl, lerp, pulse } from '../s10/_lib';
import { Breath } from '../s10/10B';
import { FONT } from '../../theme';
import { inCubic, inOutCubic, outBack, outCubic } from '../../ease';
import { FX } from './_fix2';
import { outX } from './_meter';

// rl_l3_ui (cut 4, S20 "DECEMBER plaque": it's a night in November, so no future months): MAY .. OCTOBER; the hold reads
// AUGUST / SEPTEMBER / OCTOBER (SEPTEMBER lands centre).
const MONTHS = ['MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER'];
const CW = 620, CH = 760, PITCH = 740, TOP = 250;
const Card: React.FC<{ month: string; x: number }> = ({ month, x }) => (
  <div style={{ position: 'absolute', left: x - CW / 2, top: TOP, width: CW, height: CH, borderRadius: 6,
    background: 'linear-gradient(135deg, #6b4a33 0%, #4a3122 45%, #3a2619 100%)', boxShadow: '0 30px 50px rgba(30,18,8,0.45), 0 6px 12px rgba(30,18,8,0.35)' }}>
    {/* gold lip + cream mat */}
    <div data-fit="on" style={{ position: 'absolute', left: 26, top: 26, right: 26, bottom: 26, border: '4px solid #b8955a', background: 'linear-gradient(180deg, #f3ecda 0%, #ebe1c9 100%)',
      boxShadow: 'inset 0 3px 8px rgba(60,40,20,0.25)' }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 18, textAlign: 'center', fontFamily: FONT.brand, color: '#3a3024', lineHeight: 1 }}>
        <div style={{ fontSize: 84, letterSpacing: 2 }}>EMPLOYEE</div>
        <div style={{ fontSize: 50, letterSpacing: 5, marginTop: 6 }}>OF THE MONTH</div>
      </div>
      <div style={{ position: 'absolute', left: (CW - 52 - 392) / 2, top: 186, width: 392, height: 392, border: '6px solid #c7a465', boxShadow: '0 4px 10px rgba(40,25,10,0.35)', overflow: 'hidden' }}>
        <Img src={staticFile(FX.PORTRAIT)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </div>
      <div style={{ position: 'absolute', left: (CW - 52 - 420) / 2, top: 606, width: 420, height: 70, borderRadius: 4,
        background: 'linear-gradient(180deg, #e1c47e 0%, #c49a4c 55%, #a97f36 100%)', boxShadow: 'inset 0 1px 0 rgba(255,245,210,0.7), 0 2px 4px rgba(40,25,10,0.35)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT.head, fontWeight: 700, fontSize: 48, letterSpacing: 4, color: '#3b2d16' }}>{month}</div>
    </div>
    {/* the glass: one soft diagonal reflection */}
    <div style={{ position: 'absolute', inset: 26, background: 'linear-gradient(118deg, rgba(255,255,255,0) 30%, rgba(255,250,235,0.10) 42%, rgba(255,255,255,0) 54%)', pointerEvents: 'none' }} />
  </div>
);
/** the certificate wall, flat-on, sliding left -> right as the camera lands (slide 0..1) */
export const CertWall: React.FC<{ slide: number; g: number; dx0?: number }> = ({ slide, g, dx0 = 300 }) => {   // rl6_edit: dx0 (cut 6 slides right)
  const dx = lerp(dx0, -60, slide);
  return (
    <AbsoluteFill style={{ overflow: 'hidden', background: '#a88660' }}>
      <Img src={staticFile(FX.CERT_BG)} style={{ position: 'absolute', left: -120 + dx * 0.4, top: -80, width: 2800, height: 1600, objectFit: 'cover', filter: 'blur(22px) brightness(0.9) saturate(0.9)' }} />
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 70% 80% at 35% 30%, rgba(255,226,170,0.20), rgba(40,25,12,0.30) 100%)' }} />
      <div style={{ position: 'absolute', left: 0, top: 0, width: 2560, height: 1440, transform: `translateX(${dx.toFixed(2)}px) scale(${(1 + 0.004 * Math.sin(g / 40)).toFixed(5)})`, transformOrigin: '1280px 720px' }}>
        {MONTHS.map((m, i) => <Card key={m} month={m} x={1280 + (i - 4) * PITCH} />)}
      </div>
    </AbsoluteFill>
  );
};

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const cut = gl(shot, 2, 35);                                            // beat 2: the cut to his profile
  const stand = (cueFrame(shot, 'stands') ?? shot.from + 52) - shot.from;  // the heartbeat
  const edge = lerp(-500, 3100, inOutCubic(clamp(f / 16)));              // the door edge crossing left -> right
  if (f < cut) {
    return (
      <>
        <CertWall slide={outCubic(clamp(f / (cut - 2)))} g={g} />
        {f < 16 ? (
          <>
            <div style={{ position: 'absolute', left: 0, top: 0, width: Math.max(0, edge), height: 1440, overflow: 'hidden' }}>
              <Cam cx={lerp(700, 660, inCubic(clamp(f / 16)))} cy={935} s={1.56}><Pl src={FX.H2a} /><Breath src={FX.H2a} a={0.5 - 0.5 * Math.cos((2 * Math.PI * g) / 96)} />
                <PandaWallClockCompat cx={MASTER_CLOCK.cx} cy={MASTER_CLOCK.cy} r={MASTER_CLOCK.r} hr={5} min={31} blur={0.5} /></Cam>
            </div>
            <div style={{ position: 'absolute', left: edge - 140, top: 0, width: 280, height: 1440, background: 'linear-gradient(90deg, rgba(10,8,8,0) 0%, #120d0b 30%, #1d1612 55%, #0c0908 75%, rgba(10,8,8,0) 100%)', filter: 'blur(6px)' }} />
          </>
        ) : null}
      </>
    );
  }
  // his side, close (H2 master camera at 5760): seated (eyes low) -> rise (2 frames) -> standing tall, eyes wide; the frame tilts up with him
  const st = swap(f, stand, 2);
  const c = camUp(f, cut, stand);
  return (
    <Cam cx={c.cx} cy={c.cy} s={c.s * (1 + hit(f, stand, 0.015, 12)) * pulse(g)}>
      <Pl src={st === 'A' ? FX.H2a5k : st === 'S' ? FX.H2aRise : FX.H2aStand} />
    </Cam>
  );
};
/** on him (1.8x; the frame's left edge is the plate's): seated, his whole figure on the floor (head ~ (710, 900) stage, feet ~1300); on
 *  the heartbeat the camera tilts up with him as he stands (standing head ~ (580, 670)), the QUIET HOURS wall sliding down behind him.
 *  (p3 preview had 2.0x: seated read as head + torso only, so the stand didn't show; framing checked by plate crops, check_11A.py) */
export const camUp = (f: number, cut: number, stand: number) => {
  const rise = outBack(clamp((f - stand) / 9), 1.2); const pre = clamp((f - cut) / Math.max(1, stand - cut));
  return { cx: 711, cy: lerp(lerp(905, 895, pre), 705, rise), s: lerp(1.8, 1.84, clamp((f - cut) / 50)) };
};
const headX = (f: number, stand: number) => lerp(710, 580, outBack(clamp((f - stand) / 9), 1.2));
export const S11_11A: ShotDef = {
  stage: Stage,
  // 9:16: the centre (SEPTEMBER) card while on the wall, then his head (stage x ~640) after the cut
  cx916: (f, shot) => {
    const cut = gl(shot, 2, 35); const stand = (cueFrame(shot, 'stands') ?? shot.from + 52) - shot.from;
    if (f < cut) { const dx = lerp(300, -60, outCubic(clamp(f / (cut - 2)))); return clamp((1280 + dx) / 2560, 0, 1); }
    const c = camUp(f, cut, stand); return clamp(outX(headX(f, stand), c.cx, c.s) / 2560, 0, 1);
  },
};
