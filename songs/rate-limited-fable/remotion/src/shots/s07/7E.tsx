// 7E "Went out with another model just to make you see": the date (approved DATE). A slow push to the table; the
// candle breathes as a light pass (warm pool on the cloth and faces, flicker from noise), the banner rides with the plate.
// rl_cutfix (Nov 15): plate = the approved Rain date frame (build/rain_r2/date_rain.png, same camera as the old DATE, measured:
// scale 1.000, shift 0 px), which has no banner: the banner is a code layer now and slides in on the first beat.
// 16:9: in the stage (rides the push, where the old baked one was). 9:16: a two-line card in the screen layer, inside the safe zone.
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp, noise1 } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, Grain, breath } from './_lib';
import { FONT } from '../../theme';
import { outBack } from '../../ease';

export const DATE_PLATE = 'cutfix/date_rain.jpg';
const CYAN = '#74e4f2';   // cf5: was #7ff0ff (B 255 tripped the highlight check)
/** the restaurant's hold banner (measured on the old baked one: pill 478..2480 x 61..168 stage px) */
export const DateBanner: React.FC<{ k: number; two?: boolean; x?: number; y?: number; w?: number; size?: number }> = ({ k, two, x = 478, y = 61, w = 2002, size = 55 }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: w, transform: `translateY(${(1 - k) * -(y + 200)}px)`, opacity: clamp(k * 3) }}>
    <div data-fit="box" style={{ display: 'flex', alignItems: two ? 'flex-start' : 'center', gap: size * 0.45, padding: two ? `${size * 0.55}px ${size * 0.8}px` : `${size * 0.4}px ${size * 0.9}px`,
      boxSizing: 'border-box', width: '100%', borderRadius: two ? size * 0.7 : 200, background: 'rgba(14,20,24,0.94)', boxShadow: '0 0 0 3px #5fb3b8, 0 10px 26px rgba(0,0,0,0.45)' }}>
      <div style={{ flex: 'none', width: size * 0.9, height: size * 0.9, marginTop: two ? size * 0.2 : 0, borderRadius: '50%', boxSizing: 'border-box', border: `${size * 0.26}px solid ${CYAN}` }} />
      <div style={{ fontFamily: FONT.ui, fontWeight: 600, fontSize: size, lineHeight: 1.2, color: '#e8edf0', whiteSpace: two ? 'normal' : 'nowrap' }}>
        Your date is important to us.{two ? <br /> : ' '}<span style={{ color: CYAN }}>Estimated wait: 47 minutes.</span>
      </div>
    </div>
  </div>
);
export const bannerIn = (f: number) => outBack(clamp((f - 2) / 10), 1.1);

export const CANDLE: [number, number] = [1282, 668];
export const CandleLight: React.FC<{ g: number; k?: number }> = ({ g, k = 1 }) => {
  const fl = 0.75 + 0.18 * noise1(g / 3.2, 7) + 0.07 * noise1(g / 1.3, 9);
  return (
    <AbsoluteFill style={{ mixBlendMode: 'screen', opacity: k * fl * 0.55,
      background: `radial-gradient(ellipse 520px 380px at ${CANDLE[0]}px ${CANDLE[1] + 30}px, rgba(255,170,90,0.55) 0%, rgba(255,140,70,0.18) 45%, rgba(0,0,0,0) 100%)` }} />
  );
};

const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const v = fmt === '9x16';
  // 9:16 (rl_fix2_read): no push (it would crowd her out of the 810 px crop); the crop pans her -> Cooper instead (cx916)
  const s = v ? breath(g, 0.004) : lerp(1.0, 1.07, inOutSine(clamp(f / (shot.dur - 1)))) * breath(g, 0.004);
  return (
    <Cam cx={v ? 1280 : lerp(1280, 1290, f / shot.dur)} cy={v ? 720 : lerp(720, 690, f / shot.dur)} s={s}>
      <PlateImg src={DATE_PLATE} />
      <CandleLight g={g} />
      {fmt !== '9x16' ? <DateBanner k={bannerIn(f)} /> : null}
      <Grain g={g} />
    </Cam>
  );
};
// 9:16 (1080x1920): the card sits under the top 13% and inside 9% sides
const Screen: React.FC<ShotProps> = ({ fmt }) => {
  const f = useCurrentFrame();
  if (fmt !== '9x16') return null;
  return <DateBanner k={bannerIn(f)} two x={124} y={266} w={832} size={44} />;
};
// 9:16 (rl_fix2_read, WATCH 7E: she was out of frame, one leg at the edge): the crop holds her (head x ~560-700) and Cooper
// (x ~1050-1357 stage): it starts on her and drifts right to take in Cooper by "make you see"
export const S7_7E: ShotDef = { stage: Stage, screen: Screen, cx916: (f, shot) => lerp(0.334, 0.364, inOutSine(clamp(f / (shot.dur - 1)))) };
