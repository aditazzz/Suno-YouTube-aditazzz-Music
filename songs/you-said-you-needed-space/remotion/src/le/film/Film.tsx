// LivingEarthFilm: the whole song, every slot of beats.ts at its sung time. Props: fmt ('169' | '916'), labels (the
// rough cut's beat label), inserts (public/ paths of finished clips that exist; a section's `inserts` entry shows only if
// its src is listed here, so a render never fails on a clip that isn't there yet).
import React, { useCallback, useEffect, useState } from 'react';
import { AbsoluteFill, OffthreadVideo, Sequence, continueRender, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import { frameAt, INSERTS, insertAt, insertSrc } from './engine';
import { starsAt } from './stars';
import { Scene, useTextures } from './Layers';
import { FPS } from './anchor';
import { Fmt } from './types';
import { HimLayer, himFrame } from './him/Him';
import { NewsLayer } from './news/NewsLayer';

export type FilmProps = { fmt: Fmt; labels: boolean; inserts: string[]; him?: boolean }; // him: the 3D him layer (him/Him.tsx); on unless false
export const LivingEarthFilm: React.FC<FilmProps> = ({ fmt, labels, inserts, him }) => {
  const f = useCurrentFrame(), { width, height } = useVideoConfig();
  const t = f / FPS;
  const himOn = him !== false, frame = himOn ? himFrame(frameAt(t, fmt), f, t, fmt) : frameAt(t, fmt), stars = starsAt(fmt, t);
  const { tex, handle } = useTextures();
  const [done, setDone] = useState(false);
  const onDrawn = useCallback(() => { if (!done) { setDone(true); continueRender(handle); } }, [done, handle]);
  const ins = insertAt(t, inserts, fmt);
  const label = labels ? (ins ? `${frame.label} · [MOCKUP INSERT ${ins.label ?? ins.src}]` : frame.label) : null;
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {tex && (
        <ThreeCanvas width={width} height={height} gl={{ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' }} dpr={1} linear={false} flat>
          <Scene frame={frame} stars={stars} fmt={fmt} width={width} height={height} tex={tex} onDrawn={onDrawn} />
        </ThreeCanvas>
      )}
      {himOn && <HimLayer f={f} fmt={fmt} />}
      <NewsLayer f={f} fmt={fmt} />
      {INSERTS.filter((x) => inserts.includes(insertSrc(x, fmt))).map((x) => {
        const from = Math.round(x.t0 * FPS), dur = Math.max(1, Math.round((x.t1 - x.t0) * FPS)), start = Math.max(0, Math.round((x.t0 - x.from) * FPS));
        return (
          <Sequence key={x.slot} from={from} durationInFrames={dur}>
            <OffthreadVideo src={staticFile(insertSrc(x, fmt))} startFrom={start} muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </Sequence>
        );
      })}
      {label && (
        <div style={{ position: 'absolute', left: height * 0.025, top: height * 0.025, maxWidth: width * 0.9, fontFamily: 'Helvetica, Arial, sans-serif', fontSize: Math.round(height * 0.024),
          color: frame.built ? 'rgba(160,255,240,0.85)' : 'rgba(255,210,150,0.85)', textShadow: '0 0 6px #000, 0 0 2px #000', lineHeight: 1.25 }}>{label}</div>
      )}
    </AbsoluteFill>
  );
};
