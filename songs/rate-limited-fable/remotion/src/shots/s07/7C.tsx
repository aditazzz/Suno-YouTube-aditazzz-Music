// 7C "Opened a new chat, thought we'd start again": her side of the door (S7 D1). A HELLO MY NAME IS: NEW USER sticker
// is slapped onto the glass over his chest on beat 2 (comes in from her side, squash on contact, settles, one corner
// lifts and lies down), a small camera hit; the buzzer lamp beside the door blinks once on beat 3.
// rl_fix3_qa1 (QA3): (1) the fly-in was 5 stacked shutter copies (read as overlapping text); now ONE sticker with a directional
// motion blur (SVG Gaussian along the flight direction, strength from its speed over a 0.6 shutter, sharp by the landing).
// (2) NEW USER was clipped by its card (9:16 text fit f3309): 62 px (46 px at 1920) with 18 px side padding.
// (3) 9:16 only: the sticker lands 150 px higher (just under his chin) at 0.92 so NEW USER sits at ~58-68% height, above the
// Shorts UI (it was at 69-80%); 16:9 unchanged. In flight (motion-blurred, crossing the frame edge) the sticker is data-fit
// off; the text check measures it from the landing on.
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { clamp, inOutSine, lerp, outBack, outCubic } from '../../ease';
import { FONT } from '../../theme';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, gridF, hit, flick, flickOut, Grain, breath, D1Clocks, amMin } from './_lib';

export const NewUserSticker: React.FC<{ k?: number }> = () => (
  <div style={{ width: 380, height: 280, background: '#f6f3ec', borderRadius: 16, boxShadow: '0 6px 14px rgba(0,0,0,0.35)' }}>
    <div style={{ height: 124, borderRadius: '16px 16px 0 0', padding: '0 24px', background: '#c8352b', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
      <div style={{ fontFamily: FONT.head, fontWeight: 900, fontSize: 46, lineHeight: 1, letterSpacing: '0.06em' }}>HELLO</div>
      <div style={{ fontFamily: FONT.ui, fontWeight: 600, fontSize: 34, lineHeight: 1.1 }}>my name is</div>
    </div>
    <div data-fit="box" style={{ height: 156, padding: '0 18px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT.brand, fontSize: 62, color: '#1d2a5a', transform: 'rotate(-3deg)' }}>NEW USER</div>
  </div>
);

const Stage: React.FC<ShotProps> = ({ shot, fmt }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const nine = fmt === '9x16'; const LY = nine ? 860 : 1010, LS = nine ? 0.92 : 1;   // landing y and size (9:16: above the Shorts UI)
  const bt = gridF(shot); const slap = bt[1] ?? 17, buzz = bt[2] ?? 35;
  // sticker: travels in from lower right over 6 frames, lands at `slap`, squash 1 frame, settle
  const fly = (dt: number) => {
    const t = f + dt; const k = clamp((t - (slap - 6)) / 6);
    const x = lerp(2150, 1295, outCubic(k)), y = lerp(1500, LY, outCubic(k)), rot = lerp(28, -4, outCubic(k));
    const sq = t >= slap ? 1 + 0.12 * Math.exp(-(t - slap) / 2.2) * Math.cos((t - slap) * 1.3) : 1;
    const sc = LS * (t < slap ? lerp(1.35, 1.0, outCubic(k)) : 1);
    return { x, y, rot, sx: sc * sq, sy: sc / sq, vis: t >= slap - 6 };
  };
  const s = (1.02 + 0.03 * inOutSine(clamp(f / shot.dur))) * (1 + hit(f, slap, 0.012, 12)) * breath(g, 0.004);
  const lamp = f < buzz ? 0 : f < buzz + 8 ? flick(f, buzz) : flickOut(f, buzz + 8);
  return (
    <Cam cx={1290} cy={760} s={s}>
      <PlateImg src="secb/D1.jpg" />
      <D1Clocks minutes={amMin(4, 5)} />
      {/* buzzer lamp (the red box right of the door): one blink */}
      <div style={{ position: 'absolute', left: 1932 - 26, top: 650 - 26, width: 52, height: 52, borderRadius: '50%', opacity: lamp,
        background: 'radial-gradient(circle, rgba(255,120,90,0.95) 0%, rgba(255,60,40,0.55) 40%, rgba(255,40,30,0) 72%)' }} />
      {(() => {
        const p = fly(0); if (!p.vis) return null;
        // motion over the 0.6 shutter: direction and length -> one blurred copy (blur along the wrapper's x = the flight)
        const a = fly(-0.3), b = fly(0.3); const mx = b.x - a.x, my = b.y - a.y; const len = Math.hypot(mx, my);
        const sd = f < slap ? Math.min(40, len / 3) : 0; const ang = (Math.atan2(my, mx) * 180) / Math.PI;
        return (<>
          {sd > 0.5 ? (
            <svg width={0} height={0} style={{ position: 'absolute' }}>
              <defs><filter id="rl7c_mb" x="-30%" y="-30%" width="160%" height="160%" colorInterpolationFilters="sRGB"><feGaussianBlur stdDeviation={`${sd.toFixed(2)} 0`} /></filter></defs>
            </svg>
          ) : null}
          <div data-fit={f < slap ? 'off' : undefined} style={{ position: 'absolute', left: p.x - 380, top: p.y - 380, width: 760, height: 760, transform: `rotate(${ang.toFixed(2)}deg)`, transformOrigin: '50% 50%', filter: sd > 0.5 ? 'url(#rl7c_mb)' : undefined }}>
            <div style={{ position: 'absolute', left: 380 - 190, top: 380 - 140, transform: `rotate(${(p.rot - ang).toFixed(3)}deg) scale(${p.sx}, ${p.sy})`, transformOrigin: '50% 50%', filter: 'brightness(0.92)' }}>
              <NewUserSticker />
            </div>
          </div>
        </>);
      })()}
      <Grain g={g} />
    </Cam>
  );
};
export const S7_7C: ShotDef = { stage: Stage, cx916: () => 0.505 };
