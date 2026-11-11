// HERO SHOTS (Fable, Nov 10): the pier at "Make it Sunday, make it night", the pull-back to the whole island, and the crash
// breaking that widest frame. A stand-alone composition for the hero-shot review; the film's timeline takes these over after approval.
// Hero time: 0-5 s pier, 5-11 s pull-back, 11-12.5 s hold, 12.5-15.5 s the crash in steps (the world freezes, the UI keeps running).
import React from 'react';
import { AbsoluteFill, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { createWorld } from './world';

export const HERO_FPS = 30, HERO_FRAMES = 465;
const CRASH_T = 12.5;
/** crash amount at hero time t: hard steps on a half-second grid, never a fade */
export const crashAt = (t: number) => (t < CRASH_T ? 0 : [0.22, 0.4, 0.58, 0.72, 0.85, 0.85][Math.min(5, Math.floor((t - CRASH_T) / 0.5))]);
const promptAt = (t: number) => (t < 5.6 ? 'Make it Sunday, make it night' : t < CRASH_T + 1 ? "Make me feel like I'm on time" : 'Out of memory.');
const memAt = (t: number) => (t < 5 ? 94 : t < CRASH_T ? Math.min(99, 94 + Math.floor((t - 5) * 0.7)) : 100);

export const Hero: React.FC<{ ui?: boolean }> = ({ ui = true }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H } = useVideoConfig();
  const ref = React.useRef<HTMLCanvasElement>(null);
  const world = React.useRef<any>(null);
  const cur = React.useRef(frame); cur.current = frame;
  const [handle] = React.useState(() => delayRender('hero world', { timeoutInMilliseconds: 240000 }));
  const draw = () => { const t = cur.current / HERO_FPS; world.current?.render(Math.min(t, CRASH_T - 1 / 30), crashAt(t)); };
  React.useEffect(() => {
    createWorld(ref.current!, W, H, { car: staticFile('car/gt3rs.glb'), plate: staticFile('car/plate_texas_DKWHEEL.png') }, 2)
      .then((w) => { world.current = w; draw(); continueRender(handle); })
      .catch((e) => cancelRender(e));
  }, []);
  React.useLayoutEffect(draw, [frame]);
  const t = frame / HERO_FPS, mem = memAt(t), oom = t >= CRASH_T + 1, k = W / 1920;
  const warn = mem >= 100 ? '#ff3b52' : mem >= 90 ? '#ffb347' : '#ececf2';
  const c = crashAt(t);
  const labels: [number, number, string, number][] = [[1056, 150, 'sun.mat — not found', 0.3], [1290, 800, 'ocean.tex — missing', 0.5], [300, 430, 'city_lod3 — failed', 0.7]];
  return (
    <AbsoluteFill style={{ background: '#04080e', fontFamily: 'JBM, monospace' }}>
      <canvas ref={ref} width={W * 2} height={H * 2} style={{ position: 'absolute', left: 0, top: 0, width: W, height: H }} />
      {ui && <>
        {labels.filter((l) => c >= l[3]).map((l) => (
          <div key={l[2]} style={{ position: 'absolute', left: l[0] * k, top: l[1] * k, font: `500 ${34 * k}px JBM`, color: '#f4f1f6', background: 'rgba(8,8,12,.88)', padding: `${6 * k}px ${14 * k}px`, borderRadius: 6 * k, whiteSpace: 'nowrap' }}>{l[2]}</div>))}
        <div style={{ position: 'absolute', right: 64 * k, top: 48 * k, width: 330 * k, font: `500 ${34 * k}px JBM`, letterSpacing: '.04em' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#b9b6c2' }}><span>MEMORY</span><span style={{ color: warn }}>{mem}%</span></div>
          <div style={{ height: 6 * k, borderRadius: 3 * k, background: 'rgba(255,255,255,.12)', marginTop: 10 * k }}><div style={{ height: 6 * k, borderRadius: 3 * k, width: `${mem}%`, background: warn }} /></div>
        </div>
        <div style={{ position: 'absolute', left: 370 * k, top: 930 * k, width: 1180 * k, height: 100 * k, borderRadius: 22 * k, background: 'rgba(14,14,20,.72)', boxSizing: 'border-box',
          border: `${2 * k}px solid ${oom ? 'rgba(255,59,82,.85)' : 'rgba(255,255,255,.16)'}`, boxShadow: '0 0 40px rgba(0,0,0,.6)', display: 'flex', alignItems: 'center', paddingLeft: 40 * k,
          font: `500 ${42 * k}px JBM`, color: oom ? '#ff8a96' : '#f4f1f6', whiteSpace: 'nowrap' }}>
          <span style={{ marginRight: 22 * k }}>›</span>{promptAt(t)}{!oom && <span style={{ display: 'inline-block', width: 22 * k, height: 46 * k, background: '#fff', marginLeft: 10 * k }} />}
        </div>
      </>}
    </AbsoluteFill>
  );
};
