// 12G "Don't leave me on read like this" (cut 4, lane L2; her #35 note): one minute away. A wide of her room: she is perched bolt upright on
// the sofa's edge, laptop open on her knees, one finger hovering over Enter, eyes huge; Cooper sprawled belly-up asleep across the rest of the
// sofa, legs in the air; the cat asleep draped over the laptop's lid (l2/12G). On "read" we cut to her screen: the real Claude app at the
// limit, "5-hour limit reached · resets 6:00 AM", her "see you at 6?" waiting in the composer, send greyed, Tue 5:59 AM (L3's Laptop12G).
import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { ShotDef, ShotProps } from '../types';
import { Cam, hit } from '../first30/kit';
import { LAPTOP, Laptop12G } from '../../blocks/real/Dropins';
import { L2Img, beat } from '../l2kit';
import { FixPlate } from '../c7/fix713/FixPlate';   // rl7_fixb: neon in the tube family baked into the plate
import { clamp, inOutSine, lerp } from '../../ease';

const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const b2 = beat(shot, 2, 35) + 6;
  if (f < b2) { const k = inOutSine(clamp(f / (b2 - 1))); return <Cam cx={1280} cy={720} s={lerp(1.0, 1.06, k)}><FixPlate src="c7/apt/12G_ban.jpg" /></Cam>; }
  const k = inOutSine(clamp((f - b2) / (shot.dur - 1 - b2)));
  // rl_cut4 (director: "dim the screen to the room light, frame the laptop with bezel + room; type readable at phone size"): her POV on the
  // whole laptop, its screen tipped back a little, in front of her own room (the 12G plate, out of focus, the lamp and the neon as bokeh);
  // the screen at ~87% brightness (the room's light, no blown white); the app zoomed in (2.4x, the real app's zoom) so the limit banner
  // and her draft read at phone size with the whole screen in frame.
  const s = lerp(1, 1.035, k) * (1 + hit(f, b2, 0.01, 8));
  const SW_ = 1960, KS = SW_ / LAPTOP.w, SH_ = LAPTOP.h * KS, BZ = 44, BZB = 58;           // screen on the stage, bezels
  const x0 = 1280 - SW_ / 2, y0 = 1440 - BZB - 8 - SH_;                                   // the lid's bottom edge just inside the frame
  return (
    <AbsoluteFill style={{ background: '#0b0b0d' }}>
      <Cam cx={1280} cy={720} s={1.18 * s}><FixPlate src="c7/apt/12G_ban.jpg" style={{ filter: 'blur(26px) brightness(0.62) saturate(1.05)' }} /></Cam>
      <AbsoluteFill style={{ transformOrigin: '1280px 1440px', transform: `scale(${s.toFixed(5)})`, perspective: 3200, perspectiveOrigin: '1280px 300px' }}>
        <div style={{ position: 'absolute', left: x0 - BZ - 6, top: y0 - BZ - 6, width: SW_ + 2 * BZ + 12, height: SH_ + BZ + BZB + 12, transformOrigin: '50% 100%', transform: 'rotateX(7deg)',
          borderRadius: '30px 30px 14px 14px', background: 'linear-gradient(180deg,#b9bcc2,#8d9096 60%,#6f7277)', boxShadow: '0 30px 80px rgba(0,0,0,0.55)' }}>
          <div style={{ position: 'absolute', left: 6, top: 6, right: 6, bottom: 6, borderRadius: '25px 25px 10px 10px', background: 'linear-gradient(180deg,#0d0d10,#060607)' }}>
            <div style={{ position: 'absolute', left: BZ, top: BZ, width: SW_, height: SH_, overflow: 'hidden', borderRadius: 6 }}>
              <div style={{ position: 'absolute', left: 0, top: 0, width: LAPTOP.w, height: LAPTOP.h, transformOrigin: '0 0', transform: `scale(${KS.toFixed(5)})`, filter: 'brightness(0.87)' }}>
                <Laptop12G f={f} zoom={2.4} />
              </div>
              {/* the room's lamp caught faintly in the glass */}
              <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(115deg, rgba(255,214,170,0.07) 0%, rgba(255,214,170,0) 38%, rgba(255,255,255,0) 70%, rgba(255,255,255,0.04) 100%)' }} />
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
export const S12_12G: ShotDef = { stage: Stage, cx916: () => 0.5 };
