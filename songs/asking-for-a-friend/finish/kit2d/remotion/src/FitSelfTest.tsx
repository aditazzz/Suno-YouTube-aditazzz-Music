// Planted failures for the text-fit check ("every check must be able to fail"): `text_fit_check.py --selftest` renders this and
// must catch: a title spilling out of its card (outside), a button label clipped by overflow:hidden (clipped), text touching its
// card edge (tight), and two text blocks drawn over each other (overlap). Register it in Root as <Composition id="FITTEST" .../>.
import React from 'react';
import { AbsoluteFill } from 'remotion';
export const FitSelfTest: React.FC = () => (
  <AbsoluteFill style={{ background: '#EDE5FF', fontFamily: 'Arial, sans-serif' }}>
    <div id="card-out" style={{ position: 'absolute', left: 100, top: 100, width: 600, height: 200, background: '#fff', borderRadius: 24, boxShadow: '0 0 0 3px #7B3CFF' }}>
      <div style={{ position: 'absolute', left: 40, top: 60, whiteSpace: 'nowrap', fontSize: 80, fontWeight: 700, color: '#120A24' }}>THIS TITLE SPILLS OVER ITS CARD</div>
    </div>
    <div style={{ position: 'absolute', left: 100, top: 400, width: 420, height: 90, background: '#7B3CFF', borderRadius: 20, overflow: 'hidden' }}>
      <div style={{ position: 'absolute', left: 30, top: 14, whiteSpace: 'nowrap', fontSize: 56, fontWeight: 700, color: '#fff' }}>A BUTTON LABEL THAT IS CUT OFF</div>
    </div>
    <div style={{ position: 'absolute', left: 100, top: 600, width: 500, height: 120, background: '#fff', borderRadius: 20 }}>
      <div style={{ position: 'absolute', left: 3, top: 28, fontSize: 56, fontWeight: 700, color: '#120A24' }}>Touching the edge</div>
    </div>
    <div style={{ position: 'absolute', left: 900, top: 300, width: 800, height: 400, background: '#fff', borderRadius: 20 }}>
      <div style={{ position: 'absolute', left: 40, top: 80, fontSize: 90, fontWeight: 700, color: '#120A24' }}>Overlapping</div>
      <div style={{ position: 'absolute', left: 70, top: 120, fontSize: 90, fontWeight: 700, color: '#E5304A' }}>text blocks</div>
    </div>
  </AbsoluteFill>
);
