// rl_l5_street: a preview entry = the film's own compositions + the 13B exterior beat alone (13B_ext is not in the shared registry: L2's
// 13B.tsx / rl_cut4 place it). One bundle for both (each bundle copies public/ to $TMPDIR: 1.8 GB).
import React from 'react';
import { AbsoluteFill, Composition, registerRoot, useCurrentFrame } from 'remotion';
import { Root } from '../../Root';
import { Ext13B } from './13B_ext';
const C: React.FC = () => { const f = useCurrentFrame(); return <AbsoluteFill style={{ background: '#000', overflow: 'hidden' }}><Ext13B f={f} dur={45} /></AbsoluteFill>; };
const Both: React.FC = () => (<><Root /><Composition id="L5Ext13B" component={C} width={2560} height={1440} fps={30} durationInFrames={45} /></>);
registerRoot(Both);
