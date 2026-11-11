import React from 'react';
import { Sequence } from 'remotion';
import { FromCtx } from './theme';
import { FPS, frameOf, sections } from './timing';
import { shots } from './shots';
import { registry } from './shots/index';
import { SectionStandIn, ShotStandIn } from './Placeholder';

/**
 * The picture layer. If shots.yaml has shots: each shot's component (src/shots/index.ts registry) in a Sequence over
 * [at, next at); shots without a component get a labelled stand-in. No shots yet: one stand-in per section.
 * Overlays (PromptBar, MemoryMeter) are drawn by RunIt.tsx on top, not here.
 */
export const Timeline: React.FC = () => {
  if (shots.length === 0) {
    return (
      <>
        {sections.map((s, i) => {
          const from = frameOf(s.s), to = i + 1 < sections.length ? frameOf(sections[i + 1].s) : frameOf(s.e);
          if (to <= from) return null;
          return (
            <Sequence key={i} from={from} durationInFrames={to - from} layout="none" name={`${s.name} (stand-in)`}>
              <FromCtx.Provider value={from}><SectionStandIn section={s} /></FromCtx.Provider>
            </Sequence>
          );
        })}
      </>
    );
  }
  return (
    <>
      {shots.map((sh) => {
        const C = registry[sh.id];
        return (
          <Sequence key={sh.id} from={sh.from} durationInFrames={sh.durationInFrames} layout="none" name={`${sh.id} ${sh.title ?? ''}`}>
            <FromCtx.Provider value={sh.from}>{C ? <C shot={sh} /> : <ShotStandIn shot={sh} />}</FromCtx.Provider>
          </Sequence>
        );
      })}
    </>
  );
};
export { FPS };
