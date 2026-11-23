// 5F "Now you give me nothing": his half only. He tips a glass into the bigger plant on his desk and the water goes INTO the pot:
// the stream runs from the glass's lip down onto the soil inside the rim, the soil darkens where it lands, and on
// "nothing" (beat 3) the glass runs dry: the stream's top lets go and falls in. The camera pushes in on the pour.
// rl_fix3_a (Nov 16; her note on P05 f2699: "Water isn't going in the pot"): the old plate (S21k T17) hid the glass behind the
// leaves and the code stream ended on the pot's outside wall. New plate F3_T17 (blrl_fix3_a.py): the same camera, his same grip,
// the glass at the rim from his side, the plant turned and the few leaf pieces in the pour's way pruned, and the water a REAL
// mesh (ballistic, landing on the soil inside the rim; the leaves and the rim hide it where they are in front). Here: T17_dry is
// the plate, stream.png (T17_pour's pixels where the stream is seen) is revealed from the lip down as it pours; it lands
// behind a front leaf, on the soil inside the rim. No code shapes over the plant (they would sit in front of that leaf). The old leaf
// bounce is gone (water landing in soil doesn't bounce the leaves; the plant layer was from the old plate).
import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';
import { clamp, lerp, inOutCubic } from '../../ease';
import { ShotDef, ShotProps } from '../types';
import { Cam, PlateImg, gb, pulse, c916 } from '../s03/_lib';
import { F3 } from './_fix3a_data';

const K = 2560 / F3.size[0];                                         // still px -> stage px
const SP = F3.stream_px.map(([x, y]) => [x * K, y * K]);              // the stream's centre line, lip -> soil (stage px)
const [BX0, BY0, BX1, BY1] = F3.stream_box.map((v) => v * K);
const YTOP = SP[0][1], YBOT = SP[SP.length - 1][1];
const [LDX, LDY] = [F3.land[0] * K, F3.land[1] * K];
const WET = [1690.8, 901.8, 1840.8, 941.8];                           // wet.png's box, still px (make_wet.py)
const MIDX = (SP[0][0] + LDX) / 2, MIDY = (YTOP + LDY) / 2;
const camAt = (f: number, dur: number) => { const k = inOutCubic(clamp(f / (dur - 6))); return { cx: lerp(1440, MIDX, k), cy: lerp(760, MIDY, k), s: lerp(1.06, 1.5, k) }; };
const Stage: React.FC<ShotProps> = ({ shot }) => {
  const f = useCurrentFrame(); const g = shot.from + f;
  const t1 = gb(shot, 3);                                              // "nothing": the glass runs dry
  const head = clamp((f - 1) / 4);                                    // the stream's front falls to the soil (4 frames)
  const tail = clamp((f - t1) / 5) ** 1.6;                            // the last of it lets go and falls in (accelerating)
  const yTop = lerp(YTOP, YBOT + 2, tail), yHead = lerp(YTOP, YBOT + 2, head ** 1.5);
  const landed = f >= 5;
  const wet = clamp((f - 5) / (t1 + 6 - 5));                          // the wet patch spreads while it pours, then holds
  const c = camAt(f, shot.dur);
  return (
    <Cam cx={c.cx} cy={c.cy} s={c.s * (1 + pulse(g))}>
      <PlateImg src="fix3/a/T17_dry.jpg" />
      {/* the wet soil spreading where it lands: soil pixels only (workers/rl_fix3_a/make_wet.py masks out the leaves and the rim,
          so it sits behind the front leaf like the stream does) */}
      {landed ? <Img src={staticFile('fix3/a/wet.png')} style={{ position: 'absolute', left: WET[0] * K, top: WET[1] * K, width: (WET[2] - WET[0]) * K, height: (WET[3] - WET[1]) * K, opacity: Math.min(1, wet * 1.25) }} /> : null}
      {yHead > yTop + 1 ? (
        <div style={{ position: 'absolute', left: BX0, top: BY0, width: BX1 - BX0, height: BY1 - BY0, overflow: 'hidden',
          clipPath: `inset(${Math.max(0, yTop - BY0).toFixed(1)}px 0px ${Math.max(0, BY1 - yHead).toFixed(1)}px 0px)` }}>
          <Img src={staticFile('fix3/a/stream.png')} style={{ position: 'absolute', left: 0, top: 0, width: BX1 - BX0, height: BY1 - BY0 }} />
        </div>
      ) : null}
    </Cam>
  );
};
export const S5_5F: ShotDef = { stage: Stage, cx916: (f, shot) => { const c = camAt(f, shot.dur); return c916(MIDX, c.cx, c.s); } };
