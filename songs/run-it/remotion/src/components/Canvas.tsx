import React from 'react';
import { AbsoluteFill } from 'remotion';
import { C, useLayout } from '../theme';

/** The design canvas: near-black blue-night ground with a faint dot grid (48 px step, 2 px dots). */
export const Canvas: React.FC<{ bg?: string; grid?: number; step?: number; children?: React.ReactNode }> = ({ bg = C.bg, grid = 0.08, step = 48, children }) => {
  const { W, H } = useLayout();
  return (
    <AbsoluteFill style={{ background: bg }}>
      {grid > 0 && (
        <svg width={W} height={H} style={{ position: 'absolute', left: 0, top: 0 }}>
          <defs>
            <pattern id="dotgrid" width={step} height={step} patternUnits="userSpaceOnUse">
              <rect x={step / 2 - 1} y={step / 2 - 1} width={2} height={2} fill={`rgba(255,255,255,${grid})`} />
            </pattern>
          </defs>
          <rect width={W} height={H} fill="url(#dotgrid)" />
        </svg>
      )}
      {children}
    </AbsoluteFill>
  );
};
