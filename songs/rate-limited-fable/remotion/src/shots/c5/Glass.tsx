// rl5_c: her messages on the door glass (2G, 5H, 8E; CUT5_PLAN §5 C: "Bubbles on the door glass in our Claude-style bubble, not
// blue"). The glass is a screen between them: her sent turns in the Claude app's user-bubble look (the warm cream bubble, dark ink,
// the app's rounded rect, no tail), right-aligned, landing with a small spring; under the last one the receipt pill (Delivered ->
// Read h:mm AM, >= 44 px, never both at once: out, one empty frame, in); for 8E his typing dots on his side (left), then gone.
// Drawn in whatever px space the caller is in (the 16:9 stage, or inside a ScreenInsert on the glass): size = the message type px.
//   <GlassChat f={f} msgs={[{text, at}]} delivered={at} read={{text, at}} typing={[from, to]} right={1700} top={300} size={92} />
// Ready-made cue sets for the three shots (plan frames): GLASS_2G / GLASS_5H / GLASS_8E (absolute; pass shot.from).
import React from 'react';
import { F } from '../../blocks/real/tokens';
import { GLASS } from '../../blocks/real/script';
import { clamp, pop } from './kit';

const CREAM = 'rgba(240,238,230,0.95)', INK = '#141413';
export type GMsg = { text: string; at: number };

export const GlassChat: React.FC<{
  f: number; msgs: GMsg[]; delivered?: number; read?: { text: string; at: number }; typing?: [number, number]; right: number; top: number; size: number;
  left?: number; dotsTop?: number; blur?: number; opacity?: number;
}> = ({ f, msgs, delivered, read, typing, right, top, size, left, dotsTop, blur = 0, opacity = 1 }) => {
  const padY = size * 0.42, padX = size * 0.62, lh = size * 1.25, gap = size * 0.3;
  const bh = lh + 2 * padY; const shown = msgs.filter((m) => f >= m.at);
  const rTop = top + shown.length * (bh + gap) + size * 0.05;
  const rs = Math.max(44, size * 0.56);
  const delOp = delivered !== undefined && f >= delivered ? clamp((f - delivered) / 3) * (read && f >= read.at - 3 ? 1 - clamp((f - (read.at - 3)) / 2) : 1) : 0;
  const readOp = read && f >= read.at ? clamp((f - read.at) / 3) : 0;
  const dotsOn = typing && f >= typing[0] && f < typing[1];
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', filter: blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : undefined, opacity, pointerEvents: 'none' }}>
      {shown.map((m, i) => {
        const k = clamp(pop(f, m.at, 9), 0, 1.15);
        return (
          <div key={i} style={{ position: 'absolute', right: `calc(100% - ${right}px)`, top: top + i * (bh + gap), height: bh, transformOrigin: '100% 100%',
            transform: `scale(${(0.6 + 0.4 * k).toFixed(4)})`, opacity: clamp(k * 2.5) }}>
            <div style={{ height: bh, boxSizing: 'border-box', padding: `${padY}px ${padX}px`, borderRadius: size * 0.82, background: CREAM,
              fontFamily: F.sans, fontWeight: 450, fontSize: size, lineHeight: `${lh}px`, color: INK, whiteSpace: 'nowrap',
              boxShadow: `0 0 ${size * 0.45}px rgba(255,236,200,0.28), 0 ${size * 0.08}px ${size * 0.3}px rgba(0,0,0,0.35)` }}>{m.text}</div>
          </div>
        );
      })}
      {shown.length && (delOp > 0 || readOp > 0) ? (
        <div style={{ position: 'absolute', right: `calc(100% - ${right}px)`, top: rTop, height: rs * 1.6, padding: `0 ${rs * 0.6}px`, borderRadius: rs, background: 'rgba(18,14,10,0.55)',
          display: 'flex', alignItems: 'center', fontFamily: F.sans, fontWeight: 600, fontSize: rs, color: 'rgba(240,238,230,0.96)', whiteSpace: 'nowrap', opacity: Math.max(delOp, readOp) }}>
          <span style={{ opacity: readOp > 0 ? readOp : delOp }}>{readOp > 0 ? read!.text : 'Delivered'}</span>
        </div>
      ) : null}
      {dotsOn ? (
        <div style={{ position: 'absolute', left: left ?? right - size * 9, top: dotsTop ?? rTop + rs * 2.2, height: bh, width: size * 2.6, borderRadius: size * 0.82, background: 'rgba(48,48,46,0.82)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: size * 0.22, opacity: clamp((f - typing![0]) / 3) }}>
          {[0, 1, 2].map((i) => {
            const ph = ((f - typing![0]) / 18 + i / 3) % 1; const up = Math.max(0, Math.sin(ph * Math.PI * 2));
            return <div key={i} style={{ width: size * 0.26, height: size * 0.26, borderRadius: size, background: 'rgba(240,238,230,0.9)', opacity: 0.45 + 0.55 * up, transform: `translateY(${-size * 0.08 * up}px)` }} />;
          })}
        </div>
      ) : null}
    </div>
  );
};

/** the three shots' cues (absolute film frames, CUT5_PLAN §3) -> GlassChat props for shot-local f */
export const glassCues = (id: '2G' | '5H' | '8E', from: number) => {
  const L = (F: number) => F - from;
  if (id === '2G') return { msgs: [{ text: GLASS.g2.msgs[0], at: L(1123) }], delivered: L(1132), read: { text: GLASS.g2.read, at: L(1142) } };          // Read holds 48 f
  if (id === '5H') return { msgs: GLASS.h5.msgs.map((t, i) => ({ text: t, at: L([2719, 2737, 2754][i]) })), delivered: L(2762), read: { text: GLASS.h5.read, at: L(2789) } };   // Read holds 2.3 s
  return { msgs: [{ text: GLASS.e8.msgs[0], at: L(3969) - 3 }], delivered: undefined, read: { text: GLASS.e8.read, at: L(3982) }, typing: [L(4004), L(4039)] as [number, number] };
};
