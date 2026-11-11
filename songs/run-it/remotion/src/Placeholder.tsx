import React from 'react';
import { AbsoluteFill } from 'remotion';
import { Canvas } from './components/Canvas';
import { Dot } from './components/Dot';
import { C, FONT, MED, useLayout, useT } from './theme';
import { Section, sections } from './timing';
import type { Shot } from './shots';

const tc = (t: number) => `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`;

const WHAT: Record<string, string> = {
  INTRO: 'blank design canvas, dot grid, unlabeled red button',
  V1: 'flat vector: the dot, the red button',
  PRE1: 'zoom in/out, upside down',
  CH1: 'Bigger, brighter',
  POST1: 'Run it (run it)',
  V2: 'the city: rain on the left half only, tiny guys, pigeons, the GT3 RS',
  PRE2: 'turn off gravity',
  CH2: 'Bigger, brighter (city)',
  POST2: 'Run it (run it)',
  BRIDGE: 'push through into 3D: ocean, two moons, the eclipse',
  BREAK: 'Out of memory. wireframe, missing textures, DEAD SILENCE',
  FINAL: 'undo history rewinds the world into the dot',
  OUTRO: 'one white light; the click starts New session; loop',
};

/** One labelled stand-in layer. Real shots replace it. Greys/blues only: no loud colour in a stand-in. */
export const StandIn: React.FC<{ title: string; range: string; what?: string; dot?: 'pink' | 'white' | false; nameTag?: string }> = ({ title, range, what, dot = 'pink', nameTag }) => {
  const L = useLayout();
  const t = useT();
  const wide = L.fmt === '16x9';
  return (
    <Canvas>
      {dot && <Dot variant={dot} />}
      <div style={{ position: 'absolute', left: wide ? 96 : 97, top: wide ? 64 : 262, width: wide ? 1100 : 500, fontFamily: FONT, color: 'rgba(255,255,255,.62)' }}>
        <div style={{ ...MED, fontSize: 34, letterSpacing: 2, color: '#9fb0cc' }}>STAND-IN · {nameTag ?? 'section'}</div>
        <div style={{ ...MED, fontSize: wide ? 64 : 56, color: '#f4f1f6', marginTop: 8, lineHeight: 1.1 }}>{title}</div>
        <div style={{ fontSize: 34, marginTop: 10 }}>{range}</div>
        {what && <div style={{ fontSize: 34, marginTop: 10, lineHeight: 1.3 }}>{what}</div>}
      </div>
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <div style={{ position: 'absolute', left: wide ? 96 : 97, bottom: wide ? 176 + 10 : 360, fontFamily: FONT, fontSize: 34, color: 'rgba(255,255,255,.45)' }}>{tc(t)}</div>
      </AbsoluteFill>
    </Canvas>
  );
};

export const SectionStandIn: React.FC<{ section: Section }> = ({ section }) => {
  const dot = section.name === 'BREAK' ? false : section.name === 'OUTRO' ? 'white' : 'pink';
  return <StandIn title={section.name} range={`${tc(section.s)} – ${tc(section.e)}`} what={WHAT[section.name]} dot={dot} />;
};
export const ShotStandIn: React.FC<{ shot: Shot }> = ({ shot }) => (
  <StandIn nameTag={shot.id} title={shot.title ?? shot.id} range={`${tc(shot.from / 30)} – ${tc(shot.to / 30)}`} what={shot.lyric} dot="pink" />
);
export const SECTIONS = sections;
