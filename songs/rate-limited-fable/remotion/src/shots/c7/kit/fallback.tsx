// Cut 6 inside a cut 7 block. `Cut6` plays the cut 6 shots that cover [from, from+len) of the film (block-local: at the block's
// own frames), each against its own cut 6 shot object, exactly as cut 6 drew them. Every block without a new def plays this,
// and new defs use it as a layer (e.g. a screen built for cut 6, wrapped in a new camera).
import React from 'react';
import { Sequence } from 'remotion';
import { shotDef, OLD_DEFS } from '../../index';
import { C5_SHOTS } from '../../c5';
import { C5_4F_BASE } from '../../c5d/4F';
import { SHOTS, Shot } from '../../../timing';
import { ShotDef, ShotProps } from '../../types';

// cut 6 shots WITHOUT their cut 6 transition wrappers (the CSS door slab on 3A/3B, 4F's last-16-frame push into 4G): cut 7 does
// those moves itself (WallDolly). Every other shot plays exactly as cut 6.
export const RAW: Record<string, ShotDef> = { '3A': OLD_DEFS['3A'], '3B': C5_SHOTS['3B'], '4F': C5_4F_BASE };
const def6 = (id: string) => RAW[id] ?? shotDef(id);
type Opt = { only?: string[]; layer?: 'stage' | 'screen' };
const spans = (b: Shot, only?: string[]) => SHOTS.filter((s) => s.from < b.from + b.dur && s.to > b.from && (!only || only.includes(s.id)));
export const Cut6: React.FC<ShotProps & Opt> = ({ shot, fmt, slate, only, layer = 'stage' }) => (
  <>
    {spans(shot, only).map((s) => {
      const d = def6(s.id); const C = layer === 'stage' ? d.stage : d.screen;
      if (!C) return null;
      const at = Math.max(s.from, shot.from) - shot.from;   // where it starts in the block
      const len = Math.min(s.to, shot.from + shot.dur) - Math.max(s.from, shot.from);
      const skip = Math.max(s.from, shot.from) - s.from;     // frames of the old shot already gone (4T split over 3 blocks)
      return (
        <Sequence key={s.id} from={at} durationInFrames={len} layout="none">
          <Sequence from={-skip} layout="none"><C shot={s} fmt={fmt} slate={slate} /></Sequence>
        </Sequence>
      );
    })}
  </>
);
/** one cut 6 shot `id` played in a block at its natural film frames (stage layer); for use inside new cameras */
export const Old: React.FC<ShotProps & { id: string; layer?: 'stage' | 'screen' }> = ({ id, ...p }) => <Cut6 {...p} only={[id]} />;
/** the cut 6 picture of a block, untouched (the default for blocks without a def) */
export const fallback = (b: Shot): ShotDef => {
  const hasScreen = spans(b).some((s) => def6(s.id).screen);
  return {
    stage: (p) => <Cut6 {...p} />,
    screen: hasScreen ? (p) => <Cut6 {...p} layer="screen" /> : undefined,
    cx916: (f, shot) => { const abs = shot.from + f; const s = SHOTS.find((x) => abs >= x.from && abs < x.to)!; const d = def6(s.id); return d.cx916 ? d.cx916(abs - s.from, s) : s.cx916; },
  };
};
