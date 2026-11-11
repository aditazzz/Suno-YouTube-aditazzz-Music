// s58 "Make it vertical for everyone", 9:16 only (LAYOUT_916.md, rc_916): the joke is a CROP GUIDE. 0.30 s before the land
// (with the payoff lift) a white 16:9 guide (960 x 540 centred at (540, 700), 3 px at 80%, 18 px corner handles, the hook
// artboard's style) appears with its pill "1920 × 1080" at (480, 290) (moved left of (540, 290) so it clears the MEMORY meter); on the land it rotates 90 deg (spring 0.45 s, ~6 deg
// overshoot, settle) while scaling to the full frame, the pill flips to "1080 × 1920", and the guide fades out over 0.4 s.
// The 16:9 pillarbox (Mid3D viewportAt) stays as approved; this file only draws in 9:16.
import React from 'react';
import { MED } from '../../theme';
import { tshot } from '../../timing';
import { clamp, easeOut3, lerp, prog, smooth } from './anim';

const SEL = '#16233a';
/** a damped spring 0 -> 1 that reaches its first peak at `peak` s with ~6.7% overshoot (6 deg on 90), then settles */
const rotSpring = (dt: number, peak = 0.45) => {
  if (dt <= 0) return 0;
  const zeta = 0.65, wd = Math.PI / peak, wn = wd / Math.sqrt(1 - zeta * zeta);
  return 1 - Math.exp(-zeta * wn * dt) * (Math.cos(wd * dt) + ((zeta * wn) / wd) * Math.sin(wd * dt));
};
export const CropGuide: React.FC<{ t: number }> = ({ t }) => {
  const s = tshot('s58'); if (!s) return null;
  const land = s.land, t0 = land - 0.3;
  if (t < t0 || t > land + 1.0) return null;
  const inK = easeOut3(clamp((t - t0) / 0.18));
  const r = rotSpring(t - land), sc = lerp(1, 2, clamp(r, 0, 1.2)); // 960 x 540 turned 90 deg = 540 x 960; x2 = the full frame
  const cy = lerp(700, 960, clamp(r, 0, 1));
  const fade = 1 - smooth(prog(t, land + 0.35, land + 0.75));
  const a = inK * fade;
  if (a <= 0.005) return null;
  const W = 960, H = 540, hs = 18;
  // the pill: 1920 x 1080 until the land, a quick vertical flip (scaleY 1 -> 0 -> 1 over 0.16 s) to 1080 x 1920
  const fl = (t - land) / 0.16, flipS = fl < 0 ? 1 : fl < 0.5 ? 1 - 2 * fl : fl < 1 ? 2 * fl - 1 : 1;
  const label = t < land + 0.08 ? '1920 × 1080' : '1080 × 1920';
  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
      <div data-fit="off" style={{ position: 'absolute', left: 540 - W / 2, top: cy - H / 2, width: W, height: H, boxSizing: 'border-box', opacity: a,
        border: '3px solid rgba(255,255,255,.8)', transform: `rotate(${90 * r}deg) scale(${sc})`, transformOrigin: '50% 50%',
        boxShadow: '0 0 0 1px rgba(0,0,0,.25)' }}>
        {[[0, 0], [1, 0], [0, 1], [1, 1]].map(([x, y], i) => (
          <div key={i} style={{ position: 'absolute', left: x * W - hs / 2 - 1.5, top: y * H - hs / 2 - 1.5, width: hs, height: hs, boxSizing: 'border-box',
            background: '#ffffff', border: `2.5px solid ${SEL}`, transform: `scale(${1 / sc})` }} />
        ))}
      </div>
      <div style={{ ...MED, position: 'absolute', left: 480, top: 290, height: 56, padding: '0 22px', boxSizing: 'border-box', display: 'flex', alignItems: 'center',
        background: 'rgba(244,243,240,.94)', color: SEL, borderRadius: 12, fontSize: 34, lineHeight: '40px', whiteSpace: 'nowrap', opacity: a,
        transform: `translate(-50%, -50%) scaleY(${flipS})` }}>{label}</div>
    </div>
  );
};
