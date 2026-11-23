// A modern phone (our own body: titanium band, black border, the pill cut-out; no marks) holding a real app screen.
// The screen is laid out in iOS points (393 x 852) and the whole device is scaled so the screen is `w` stage px wide.
//   <Phone cx={1280} cy={900} w={1300} rot={-3} time="2:08" dark={false}><UsagePage .../></Phone>
// Framing closer = a bigger w (the phone runs off the frame); never redraw the UI bigger.
import React from 'react';
import { F } from './tokens';

export const PW = 393, PH = 852;
const BZ = 6.5, BAND = 3.5;     // black border, metal band (pt)

export const StatusBar: React.FC<{ time: string; dark?: boolean; battery?: number; bg?: string; silent?: boolean }> = ({ time, dark = false, battery = 0.31, bg, silent }) => {
  const c = dark ? '#fff' : '#000';
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 54, zIndex: 20, background: bg, fontFamily: F.ios, color: c }}>
      <div style={{ position: 'absolute', left: 0, width: 150, top: 17.8, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3, fontSize: 17.8, fontWeight: 650, letterSpacing: '-0.01em' }}>
        {time}
        {/* silent mode (the bell with the slash), as on her phone's status bar in her screenshot */}
        {silent ? <svg width={15} height={15} viewBox="0 0 20 20" style={{ marginTop: 1 }}><path d="M10 2.5a5 5 0 0 0-5 5v3.6L3.4 13.6c-.4.6 0 1.4.7 1.4h11.8c.7 0 1.1-.8.7-1.4L15 11.1V7.5a5 5 0 0 0-5-5zM8 16.4a2 2 0 0 0 4 0z" fill={c} /><path d="M3 2.5l14.5 15" stroke={dark ? '#000' : '#fff'} strokeWidth={3.2} strokeLinecap="round" /><path d="M3 2.5l14.5 15" stroke={c} strokeWidth={1.7} strokeLinecap="round" /></svg> : null}
      </div>
      <div style={{ position: 'absolute', right: 26, top: 21, display: 'flex', alignItems: 'center', gap: 6 }}>
        <svg width={18} height={12} viewBox="0 0 18 12">{[0, 1, 2, 3].map((i) => <rect key={i} x={i * 4.8} y={9 - i * 3} width={3.2} height={3 + i * 3} rx={0.8} fill={c} opacity={i < 3 ? 1 : 0.35} />)}</svg>
        <svg width={16} height={12} viewBox="0 0 16 12"><path d="M8 11.5l2.2-2.6a3.3 3.3 0 0 0-4.4 0zM3.4 6.6a6.8 6.8 0 0 1 9.2 0l1.5-1.7a9 9 0 0 0-12.2 0zM.4 3.4a11 11 0 0 1 15.2 0L16 3 15.6 3.4" fill={c} stroke={c} strokeWidth={0.6} /></svg>
        <div style={{ position: 'relative', width: 26, height: 12.5, borderRadius: 4, border: `1.2px solid ${c}`, opacity: 0.9, boxSizing: 'border-box' }}>
          <div style={{ position: 'absolute', left: 1.5, top: 1.5, bottom: 1.5, width: `${Math.max(0.08, battery) * 19.5}px`, borderRadius: 2, background: battery < 0.2 ? '#FF3B30' : c }} />
          <div style={{ position: 'absolute', right: -4, top: 3.2, width: 2, height: 4, borderRadius: 1, background: c, opacity: 0.6 }} />
        </div>
      </div>
    </div>
  );
};

export const Phone: React.FC<{
  cx: number; cy: number; w: number; rot?: number; time?: string; dark?: boolean; children?: React.ReactNode; light?: number;
  glare?: number; shadow?: number; tilt?: [number, number]; statusBg?: string; battery?: number; island?: boolean; style?: React.CSSProperties; fit?: boolean; silent?: boolean;
}> = ({ cx, cy, w, rot = 0, time = '2:08', dark = false, children, light = 0.9, glare = 0.1, shadow = 1, tilt, statusBg, battery, island = true, style, fit = false, silent }) => {
  const k = w / PW;
  const ow = PW + 2 * (BZ + BAND), oh = PH + 2 * (BZ + BAND);
  const t3d = tilt ? ` perspective(${ow * 4}px) rotateY(${tilt[0]}deg) rotateX(${tilt[1]}deg)` : '';
  return (
    // data-fit off in the film: the phone is framed closer than the frame on purpose (its UI runs off the edges like any camera
    // crop); the interfaces are text-fit checked whole in the fit lab (blocks/real/_lab, fit = true)
    <div data-fit={fit ? undefined : 'off'} style={{ position: 'absolute', left: cx - (ow * k) / 2, top: cy - (oh * k) / 2, width: ow * k, height: oh * k, transform: `rotate(${rot}deg)${t3d}`, ...style }}>
      <div style={{ position: 'absolute', left: 0, top: 0, width: ow, height: oh, transformOrigin: '0 0', transform: `scale(${k})` }}>
        {/* body: metal band, black border */}
        <div style={{ position: 'absolute', inset: 0, borderRadius: 62, background: 'linear-gradient(135deg,#8d8a85,#cfcbc4 18%,#6c6964 40%,#bdb9b2 62%,#5e5b57 84%,#a9a59e)',
          boxShadow: shadow ? `0 ${30}px ${60}px rgba(0,0,0,${0.45 * shadow}), 0 ${8}px ${16}px rgba(0,0,0,${0.35 * shadow})` : undefined }} />
        {/* side buttons */}
        <div style={{ position: 'absolute', left: -2.2, top: 172, width: 3, height: 32, borderRadius: 2, background: '#8a8781' }} />
        <div style={{ position: 'absolute', left: -2.2, top: 222, width: 3, height: 58, borderRadius: 2, background: '#8a8781' }} />
        <div style={{ position: 'absolute', left: -2.2, top: 292, width: 3, height: 58, borderRadius: 2, background: '#8a8781' }} />
        <div style={{ position: 'absolute', right: -2.2, top: 250, width: 3, height: 92, borderRadius: 2, background: '#8a8781' }} />
        <div style={{ position: 'absolute', left: BAND, top: BAND, right: BAND, bottom: BAND, borderRadius: 58.5, background: '#050505' }} />
        {/* the screen */}
        <div style={{ position: 'absolute', left: BAND + BZ, top: BAND + BZ, width: PW, height: PH, borderRadius: 55, overflow: 'hidden', background: dark ? '#000' : '#fff',
          filter: light !== 1 ? `brightness(${light})` : undefined }}>
          {children}
          <StatusBar time={time} dark={dark} bg={statusBg} battery={battery} silent={silent} />
          {island ? <div style={{ position: 'absolute', left: (PW - 125) / 2, top: 11, width: 125, height: 37, borderRadius: 19, background: '#000', zIndex: 30 }} /> : null}
          <div style={{ position: 'absolute', left: (PW - 140) / 2, bottom: 8, width: 140, height: 5, borderRadius: 3, background: dark ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.85)', zIndex: 30 }} />
          {glare > 0 ? <div style={{ position: 'absolute', inset: 0, zIndex: 40, background: `linear-gradient(118deg, rgba(255,255,255,0) 28%, rgba(255,255,255,${glare}) 44%, rgba(255,255,255,0) 58%)` }} /> : null}
        </div>
      </div>
    </div>
  );
};
