import React from 'react';
import { Composition, useCurrentFrame } from 'remotion';
import { K01, K02, K04, K05, K06, K09, K10, K11, K12, K13 } from './items_a';
import { K15, K16A, K17, K18, K19, K20, K20b } from './items_b';
import { K21, K22, K23 } from './items_c';
import { K08, K25, K26 } from './li_items';
import { K07, K14 } from './li_feed';
import { K16, K16V } from './k16_gym'; // round 5: K16 = the gym mirror selfie (9:16 twin K16V)
import { KS1, KS2, KS3, KS4, KS5, KS6, KS7, KS8, KS9 } from './screens';
import { ITEMS } from './items';
import { MotionCtx } from './ui';
import { ease, lin } from './theme';
import { FitProbe } from './FitProbe';
import { FitSelfTest } from './FitSelfTest';

const COMP: Record<string, React.FC> = { K01, K02, K04, K05, K06, K07, K08, K09, K10, K11, K12, K13, K14, K15, K16, K16V, K16A, K17, K18, K19, K20, K20b, K21, K22, K23, K25, K26, KS1, KS2, KS3, KS4, KS5, KS6, KS7, KS8, KS9 };

// Motion pass wrapper (Nov 6): whole-frame settle-out (4% -> 1.0, landing exactly on the first approved key frame), then a
// slow 2% push after the last key frame (3% for the hard-cut items K09/KS6, push only). Entrances (Stagger in ui.tsx)
// finish before the first key frame, so every approved key frame is pixel-identical to its still.
const Motion: React.FC<{ id: string }> = ({ id }) => {
  const f = useCurrentFrame(); const it = ITEMS.find((i) => i.id === id)!; const Comp = COMP[id];
  const k0 = it.keys[0], kN = it.keys[it.keys.length - 1];
  const hard = id === 'K09' || id === 'KS6';
  const on = !hard && k0 >= 18 && it.dur > 1;
  let sc = 1;
  if (it.dur > 1) {
    if (!hard && k0 >= 14) sc = 1 + 0.04 * (1 - ease(f, 0, k0));
    const ps = hard ? k0 : kN; if (it.dur - 1 > ps) sc += (hard ? 0.03 : 0.02) * lin(f, ps, it.dur - 1);
  }
  return <MotionCtx.Provider value={{ key: k0, on }}><div style={{ position: 'absolute', inset: 0, transform: `scale(${sc})`, transformOrigin: '50% 50%' }}><FitProbe id={id}><Comp /></FitProbe></div></MotionCtx.Provider>;
};
const MO = (globalThis as any).process?.env?.REMOTION_MOTION !== '0';
export const Root: React.FC = () => (
  <>
    {ITEMS.map((it) => (
      <Composition key={it.id} id={it.id} component={MO ? () => <Motion id={it.id} /> : COMP[it.id]} durationInFrames={it.dur} fps={24} width={it.w ?? 2560} height={it.h ?? 1440} />
    ))}
    <Composition id="FITTEST" component={() => <FitProbe id="FITTEST"><FitSelfTest /></FitProbe>} durationInFrames={2} fps={24} width={2560} height={1440} />
    {ITEMS.map((it) => (
      <Composition key={it.id + '-base'} id={it.id + '-base'} component={() => { const C0 = COMP[it.id]; return <FitProbe id={it.id}><C0 /></FitProbe>; }} durationInFrames={it.dur} fps={24} width={it.w ?? 2560} height={it.h ?? 1440} />
    ))}
  </>
);
