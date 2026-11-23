// PandaClock: THE clock of Rate Limited (FIX4_PLAN §2a, her note: "Rolex panda ... consistent ... time easy to see").
// One face everywhere: her watch, the lobby wall clock, the street post clock, the BACK AT 6:00 sign, the 12I countdown.
//   warm white dial; black sub-dials at 3, 6, 9 (fine white rings, white hands, a small red heart on the 6 o'clock one);
//   black bezel with white numerals only (a tachymeter scale, no wordmark); polished steel case; applied black baton
//   indices with lume dots; thick black stick hour/minute hands with white lume inlay (hour 0.5 R, minute 0.8 R, each
//   >= 3% of the dial wide); a thin central chronograph hand with a red tip. No crown, no logo, no text on the dial.
//
//   <PandaClock cx={1800} cy={300} r={160} time={pt(2, 24)} variant="wall" />            // centre + outer radius, stage px
//   <PandaPin corners={quad} time={pt(4, 37)} variant="wall" light={0.9} blur={1.5} />  // 4-corner pinned onto a plate
//   <PandaFace size={800} time={pt(5, 59, 57)} chrono={57} />                          // the bare face in a size x size box
//   <BackAt6Sign x={..} y={..} w={420} swing={deg} />                                   // the hanging shop sign (hands at 6:00)
//
// time = minutes since midnight (pt(h, m, s) builds it; AM hours as on the timeline). chrono = the red hand in seconds (0-60);
// default follows the time's seconds. Everything is a pure function of its props.
import React from 'react';
import { staticFile } from 'remotion';
import { ScreenInsert, Quad } from './ScreenInsert';

export const pt = (h: number, m: number, s = 0) => h * 60 + m + s / 60;
/** film minutes (timing.ts: minutes after 6 PM) -> minutes since midnight */
export const fromFilm = (filmMinutes: number) => (filmMinutes + 18 * 60) % (24 * 60);

export type PandaVariant = 'face' | 'wall' | 'watch' | 'post' | 'sign';
type FaceProps = { time: number; chrono?: number; running?: number; uid?: string; glare?: number; lume?: number };

const STEEL = ['#f4f5f6', '#9ea3a8', '#e6e8ea', '#6f757b', '#d9dcdf', '#8b9096', '#f4f5f6'];
const DIAL_R = 0.74;          // dial radius as a fraction of the face radius (the bezel ring sits outside it)
const BEZ_R = 0.92;           // bezel outer radius (the steel case ring runs to 1.0)
const TACHY = [400, 300, 240, 200, 180, 160, 140, 120, 110, 100, 90, 80, 70, 60];

const polar = (deg: number, r: number) => [Math.sin((deg * Math.PI) / 180) * r, -Math.cos((deg * Math.PI) / 180) * r];

/** a stick hand: black body with a white lume inlay, pointed tip. len, width in face units */
const StickHand: React.FC<{ deg: number; len: number; w: number; tail?: number }> = ({ deg, len, w, tail = 0.12 }) => {
  const t = tail, hw = w / 2, tip = len + w * 0.6;
  const body = `M ${-hw} ${t} L ${-hw} ${-len} L 0 ${-tip} L ${hw} ${-len} L ${hw} ${t} Z`;
  const lw = hw * 0.48, l0 = -len * 0.28, l1 = -len * 0.96;
  return (
    <g transform={`rotate(${deg.toFixed(3)})`}>
      <path d={body} fill="#000" opacity={0.28} transform="translate(0.012 0.02)" />
      <path d={body} fill="#121214" stroke="#3c3f44" strokeWidth={w * 0.06} />
      <rect x={-lw} y={l1} width={2 * lw} height={l0 - l1} rx={lw * 0.6} fill="#f6f3ea" />
    </g>
  );
};

/** the bare face (dial + bezel + steel case ring) drawn in a 2 x 2 viewBox centred on 0 (face radius 1) */
export const PandaFaceSvg: React.FC<FaceProps & { size: number; style?: React.CSSProperties }> = ({ size, time, chrono, running, uid = 'pc', glare = 1, lume = 0, style }) => {
  const mins = time; const secs = (mins * 60) % 60;
  const hA = ((mins / 60) % 12) * 30, mA = (mins % 60) * 6;
  const cs = chrono ?? secs; const cA = (cs % 60) * 6;
  const run = running ?? secs; const rA = (run % 60) * 6;
  const D = DIAL_R;
  const sub = (cx: number, cy: number, r: number, hand: number, heart?: boolean, key = '') => (
    <g transform={`translate(${cx} ${cy})`} key={key}>
      <circle r={r} fill={`url(#${uid}sub)`} />
      <circle r={r * 0.96} fill="none" stroke="#e9e6de" strokeWidth={r * 0.06} />
      {Array.from({ length: 12 }, (_, i) => {
        const [x0, y0] = polar(i * 30, r * 0.86), [x1, y1] = polar(i * 30, r * (i % 3 ? 0.74 : 0.64));
        return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} stroke="#f1eee6" strokeWidth={r * (i % 3 ? 0.035 : 0.06)} />;
      })}
      {heart ? <path d="M 0 0.30 C -0.36 0.02 -0.34 -0.30 -0.14 -0.32 C -0.05 -0.33 0 -0.26 0 -0.2 C 0 -0.26 0.05 -0.33 0.14 -0.32 C 0.34 -0.30 0.36 0.02 0 0.30 Z"
        transform={`translate(0 ${r * 0.38}) scale(${r * 0.62})`} fill="#d23a2e" /> : null}
      <g transform={`rotate(${hand.toFixed(2)})`}>
        <line x1={0} y1={r * 0.18} x2={0} y2={-r * 0.82} stroke="#f6f3ea" strokeWidth={r * 0.07} strokeLinecap="round" />
      </g>
      <circle r={r * 0.1} fill="#f6f3ea" />
    </g>
  );
  return (
    <svg data-fit="off" width={size} height={size} viewBox="-1 -1 2 2" style={{ display: 'block', overflow: 'visible', ...style }}>
      <defs>
        <radialGradient id={`${uid}dial`} cx="0.42" cy="0.36" r="0.75">
          <stop offset="0" stopColor="#fbf8f1" /><stop offset="0.7" stopColor="#f1ece1" /><stop offset="1" stopColor="#e3dccd" />
        </radialGradient>
        <radialGradient id={`${uid}sub`} cx="0.4" cy="0.35" r="0.8">
          <stop offset="0" stopColor="#2a2b2f" /><stop offset="1" stopColor="#0c0c0e" />
        </radialGradient>
        <radialGradient id={`${uid}bez`} cx="0.5" cy="0.5" r="0.5">
          <stop offset={`${(D / BEZ_R) * 100}%`} stopColor="#1b1c1f" /><stop offset="0.93" stopColor="#0d0d0f" /><stop offset="1" stopColor="#25262a" />
        </radialGradient>
        <linearGradient id={`${uid}steel`} x1="0" y1="0" x2="1" y2="1">
          {STEEL.map((c, i) => <stop key={i} offset={i / (STEEL.length - 1)} stopColor={c} />)}
        </linearGradient>
        <linearGradient id={`${uid}glare`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0.2" stopColor="#fff" stopOpacity={0} /><stop offset="0.42" stopColor="#fff" stopOpacity={0.22 * glare} />
          <stop offset="0.5" stopColor="#fff" stopOpacity={0.05 * glare} /><stop offset="0.75" stopColor="#fff" stopOpacity={0} />
        </linearGradient>
        <clipPath id={`${uid}clip`}><circle r={D} /></clipPath>
      </defs>
      {/* steel case ring */}
      <circle r={1} fill={`url(#${uid}steel)`} />
      <circle r={0.985} fill="none" stroke="#5c6166" strokeWidth={0.012} />
      {/* black bezel with the white tachymeter scale (numerals only) */}
      <circle r={BEZ_R} fill={`url(#${uid}bez)`} />
      {Array.from({ length: 60 }, (_, i) => {
        const [x0, y0] = polar(i * 6, BEZ_R - 0.018), [x1, y1] = polar(i * 6, BEZ_R - (i % 5 ? 0.04 : 0.06));
        return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} stroke="#e9e6de" strokeWidth={i % 5 ? 0.006 : 0.01} />;
      })}
      {TACHY.map((v) => {
        const deg = ((3600 / v) / 60) * 360 % 360; const [x, y] = polar(deg, (BEZ_R + D) / 2 - 0.012);
        return <text key={v} x={x} y={y} transform={`rotate(${deg.toFixed(2)} ${x} ${y})`} textAnchor="middle" dominantBaseline="central"
          fontFamily="RLInter, Inter, Helvetica, sans-serif" fontWeight={600} fontSize={0.066} fill="#f1eee6">{v}</text>;
      })}
      <circle r={D + 0.006} fill="none" stroke="#9aa0a6" strokeWidth={0.012} />
      {/* the dial */}
      <circle r={D} fill={`url(#${uid}dial)`} />
      {/* minute track: fifths of a second around the edge */}
      {Array.from({ length: 240 }, (_, i) => {
        const big = i % 4 === 0; const [x0, y0] = polar(i * 1.5, D - 0.012), [x1, y1] = polar(i * 1.5, D - (big ? 0.05 : 0.032));
        return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} stroke="#2b2b2e" strokeWidth={big ? 0.007 : 0.0035} />;
      })}
      {/* applied baton indices (steel edge, black body, lume dot at the outer end); the 3, 6, 9 batons are short (the sub-dials) */}
      {Array.from({ length: 12 }, (_, i) => {
        if (i === 3 || i === 6 || i === 9) return null;
        const outer = D - 0.075, inner = i === 0 ? D - 0.27 : D - 0.235, w = i === 0 ? 0.05 : 0.04;
        const body = (dx: number) => (
          <g key={dx} transform={`rotate(${i * 30}) translate(${dx} 0)`}>
            <rect x={-w / 2 - 0.006} y={-outer - 0.006} width={w + 0.012} height={outer - inner + 0.012} rx={0.008} fill="#c9ccd0" />
            <rect x={-w / 2} y={-outer} width={w} height={outer - inner} rx={0.006} fill="#141416" />
            <circle cx={0} cy={-outer + 0.03} r={w * 0.32} fill="#f3efe2" />
          </g>
        );
        return i === 0 ? <g key={i}>{body(-0.034)}{body(0.034)}</g> : <g key={i}>{body(0)}</g>;
      })}
      {/* sub-dials: 3 = chrono minutes, 6 = hours (with the heart), 9 = running seconds */}
      {sub(0.36, 0, 0.19, ((cs / 60) % 30) * 12, false, 's3')}
      {sub(0, 0.36, 0.19, ((mins / 60) % 12) * 30, true, 's6')}
      {sub(-0.36, 0, 0.19, rA, false, 's9')}
      {/* hands: hour 0.5 R, minute 0.8 R (R = the dial), thick sticks with lume, then the chrono hand */}
      <StickHand deg={hA} len={D * 0.5} w={0.075} />
      <StickHand deg={mA} len={D * 0.8} w={0.062} />
      <g transform={`rotate(${cA.toFixed(3)})`}>
        <line x1={0} y1={D * 0.22} x2={0} y2={-D * 0.93} stroke="#18181a" strokeWidth={0.012} strokeLinecap="round" />
        <line x1={0} y1={-D * 0.78} x2={0} y2={-D * 0.95} stroke="#d0342a" strokeWidth={0.014} strokeLinecap="round" />
        <circle cy={D * 0.2} r={0.028} fill="#18181a" />
      </g>
      <circle r={0.04} fill="#1a1a1c" stroke="#a9adb2" strokeWidth={0.01} />
      {lume > 0 ? <circle r={D} fill="#9fe8c0" opacity={0} /> : null}
      {/* crystal: a soft diagonal glare and an edge ring */}
      <g clipPath={`url(#${uid}clip)`}>
        <rect x={-1} y={-1} width={2} height={2} fill={`url(#${uid}glare)`} />
        <circle r={D} fill="none" stroke="#000" strokeOpacity={0.12} strokeWidth={0.05} />
      </g>
    </svg>
  );
};

/** the face in a size x size box (top-left at 0,0) */
export const PandaFace: React.FC<FaceProps & { size: number }> = (p) => <PandaFaceSvg {...p} />;

/** a positioned clock: centre (cx, cy), outer radius r (stage px). Variants add their housing. */
export const PandaClock: React.FC<FaceProps & { cx: number; cy: number; r: number; variant?: PandaVariant; blur?: number; light?: number;
  tilt?: [number, number]; rot?: number; shadow?: number; style?: React.CSSProperties }> = ({ cx, cy, r, variant = 'wall', blur = 0, light = 1, tilt, rot = 0, shadow = 1, style, ...face }) => {
  const filt = [light !== 1 ? `brightness(${light})` : '', blur ? `blur(${blur}px)` : ''].join(' ').trim() || undefined;
  const t3d = tilt ? `perspective(${r * 12}px) rotateY(${tilt[0]}deg) rotateX(${tilt[1]}deg)` : '';
  const uid = face.uid ?? `pc${Math.round(cx)}_${Math.round(cy)}`;
  return (
    <div data-fit="off" style={{ position: 'absolute', left: cx - r, top: cy - r, width: 2 * r, height: 2 * r, transform: `${t3d} rotate(${rot}deg)`, filter: filt, ...style }}>
      {variant === 'watch' ? <WatchBody r={r} uid={uid} /> : null}
      {variant === 'post' ? <PostHousing r={r} /> : null}
      <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', boxShadow: shadow ? `0 ${r * 0.06}px ${r * 0.12}px rgba(0,0,0,${0.45 * shadow}), 0 ${r * 0.015}px ${r * 0.03}px rgba(0,0,0,${0.4 * shadow})` : undefined }} />
      <PandaFaceSvg size={2 * r} {...face} uid={uid} style={{ position: 'absolute', left: 0, top: 0 }} />
      {variant === 'watch' ? <WatchCrown r={r} /> : null}
    </div>
  );
};

/** pinned with 4 corners (TL, TR, BR, BL) of the face's bounding square: sits in any plate's perspective */
export const PandaPin: React.FC<FaceProps & { corners: Quad; light?: number; blur?: number; opacity?: number }> = ({ corners, light = 1, blur = 0, opacity = 1, ...face }) => (
  <ScreenInsert corners={corners} w={1000} h={1000} light={light} opacity={opacity}>
    <div style={{ position: 'absolute', inset: 0, filter: blur ? `blur(${blur}px)` : undefined }}>
      <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', boxShadow: '0 30px 50px rgba(0,0,0,0.45)' }} />
      <PandaFaceSvg size={1000} {...face} uid={face.uid ?? 'pin'} />
    </div>
  </ScreenInsert>
);

/** a quad for a round wall clock seen square-on at (cx, cy) with radius r, squashed by sx/sy (foreshortening) and rotated */
export const clockQuad = (cx: number, cy: number, r: number, sx = 1, sy = 1, rot = 0): Quad => {
  const a = (rot * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a);
  return ([[-1, -1], [1, -1], [1, 1], [-1, 1]] as [number, number][]).map(([x, y]) => {
    const X = x * r * sx, Y = y * r * sy; return [cx + X * c - Y * s, cy + X * s + Y * c];
  }) as Quad;
};

// ---------- housings ----------
const WatchBody: React.FC<{ r: number; uid: string }> = ({ r }) => {
  // lugs + an Oyster-style three-link steel bracelet, top and bottom (no crown guard logo, no marks)
  const link = (y: number, h: number, k: number) => (
    <div key={`${y}`} style={{ position: 'absolute', left: r * 0.36, top: y, width: r * 1.28, height: h, display: 'flex', gap: r * 0.02 }}>
      <div style={{ flex: 1, borderRadius: r * 0.05, background: `linear-gradient(90deg,#8e9399,#dfe2e5 ${40 + k}%,#9a9fa4)` }} />
      <div style={{ flex: 1.15, borderRadius: r * 0.05, background: `linear-gradient(90deg,#c8ccd0,#f6f7f8 ${45 + k}%,#b9bdc2)` }} />
      <div style={{ flex: 1, borderRadius: r * 0.05, background: `linear-gradient(90deg,#9a9fa4,#dfe2e5 ${55 - k}%,#8e9399)` }} />
    </div>
  );
  return (
    <>
      <div style={{ position: 'absolute', left: r * 0.3, top: -r * 0.95, width: r * 1.4, height: r * 1.2, borderRadius: r * 0.12, background: 'linear-gradient(90deg,#7d8288,#e8eaec 45%,#8a8f95)' }} />
      <div style={{ position: 'absolute', left: r * 0.3, top: r * 1.75, width: r * 1.4, height: r * 1.2, borderRadius: r * 0.12, background: 'linear-gradient(90deg,#7d8288,#e8eaec 45%,#8a8f95)' }} />
      {[-1.6, -1.25, -0.9].map((y, i) => link(r * y, r * 0.32, i * 4))}
      {[2.0, 2.35, 2.7].map((y, i) => link(r * y, r * 0.32, i * 4))}
    </>
  );
};
const WatchCrown: React.FC<{ r: number }> = ({ r }) => (
  <>
    {[[-0.62, 0.16], [0, 0.22], [0.62, 0.16]].map(([dy, h], i) => (
      <div key={i} style={{ position: 'absolute', left: 2 * r - r * 0.04, top: r + r * dy - r * h / 2, width: r * (i === 1 ? 0.16 : 0.12), height: r * h,
        borderRadius: r * 0.03, background: 'linear-gradient(180deg,#e8eaec,#8a8f95 60%,#c9ccd0)', zIndex: -1 }} />
    ))}
  </>
);
const PostHousing: React.FC<{ r: number }> = ({ r }) => (
  <div style={{ position: 'absolute', left: -r * 0.1, top: -r * 0.1, width: r * 2.2, height: r * 2.2, borderRadius: '50%',
    background: 'radial-gradient(circle at 40% 35%, #3a3d40, #141516 70%)', boxShadow: `0 ${r * 0.05}px ${r * 0.15}px rgba(0,0,0,0.5)` }} />
);

/**
 * BACK AT 6:00: the one hanging shop sign (FIX4_PLAN §2a, R7, S10). A real "back at" shop sign: a landscape black enamel board with
 * a gilt edge, BACK / AT in gilt caps on the left, and the panda dial on the right with its hands set to 6:00, hung from a brass
 * hook on two chains. (x, y) = the hook point; w = board width (stage px); swing = degrees about the hook.
 */
export const BackAt6Sign: React.FC<{ x: number; y: number; w: number; swing?: number; light?: number; blur?: number; uid?: string; chain?: number }> = ({ x, y, w, swing = 0, light = 1, blur = 0, uid = 'ba6', chain = 0.16 }) => {
  const h = w * 0.56, ch = w * chain;
  const filt = [light !== 1 ? `brightness(${light})` : '', blur ? `blur(${blur}px)` : ''].join(' ').trim() || undefined;
  const fs = h * 0.25, d = h * 0.8;
  return (
    <div data-fit="off" style={{ position: 'absolute', left: x - w / 2, top: y, width: w, height: h + ch, transformOrigin: `${w / 2}px 0px`, transform: `rotate(${swing.toFixed(3)}deg)`, filter: filt }}>
      <svg width={w} height={ch + 4} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
        {[0.16, 0.84].map((k, i) => {
          const x1 = w * k, n = 8;
          return Array.from({ length: n }, (_, j) => {
            const t = (j + 0.5) / n; const px = w / 2 + (x1 - w / 2) * t, py = ch * t;
            return <ellipse key={`${i}${j}`} cx={px} cy={py} rx={w * 0.008} ry={(ch / n) * 0.62} transform={`rotate(${(Math.atan2(x1 - w / 2, ch) * -180) / Math.PI} ${px} ${py})`}
              fill="none" stroke="#b08a45" strokeWidth={w * 0.006} />;
          });
        })}
        <circle cx={w / 2} cy={0} r={w * 0.018} fill="#c9a35a" stroke="#6e5427" strokeWidth={w * 0.004} />
      </svg>
      <div style={{ position: 'absolute', left: 0, top: ch, width: w, height: h }}><SignBoard w={w} h={h} side="back" uid={uid} /></div>
    </div>
  );
};

/** the sign's board alone (w x h, fills from its top-left): side 'back' = BACK / AT + the panda dial at 6:00; 'open' = OPEN.
 *  2A and 13A flip it (scale through zero); see PandaSignFace for their drop-in. */
export const SignBoard: React.FC<{ w: number; h: number; side: 'open' | 'back'; uid?: string }> = ({ w, h, side, uid = 'sb' }) => {
  const fs = h * 0.25, d = h * 0.8, u = Math.min(w, h / 0.56);
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: w, height: h, borderRadius: u * 0.045,
      background: 'linear-gradient(160deg,#2b2a2c 0%,#141315 55%,#0d0c0e 100%)',
      boxShadow: `0 ${u * 0.035}px ${u * 0.06}px rgba(0,0,0,0.5), inset 0 0 0 ${u * 0.012}px #b8934e, inset 0 0 0 ${u * 0.02}px #2a2420, inset 0 ${u * 0.006}px ${u * 0.014}px rgba(255,255,255,0.12)` }}>
      {[0.16, 0.84].map((k) => <div key={k} style={{ position: 'absolute', left: w * k - u * 0.016, top: h * 0.05, width: u * 0.032, height: u * 0.032, borderRadius: '50%',
        background: 'radial-gradient(circle at 35% 35%,#f1d68e,#9b7535)' }} />)}
      {side === 'back' ? (
        <>
          <div style={{ position: 'absolute', left: w * 0.05, width: w * 0.97 - d - w * 0.05, top: 0, bottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
            fontFamily: 'RLInterDisplay, Inter, sans-serif', fontWeight: 900, fontSize: fs, letterSpacing: '0.04em', lineHeight: 1.04, color: '#e4c27a',
            textShadow: `0 ${u * 0.003}px 0 #6e5427, 0 0 ${u * 0.014}px rgba(228,194,122,0.25)` }}><div>BACK</div><div>AT</div></div>
          <div style={{ position: 'absolute', left: w * 0.97 - d, top: (h - d) / 2, width: d, height: d }}>
            <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', boxShadow: `0 ${u * 0.012}px ${u * 0.025}px rgba(0,0,0,0.6)` }} />
            <PandaFaceSvg size={d} time={pt(6, 0)} chrono={0} running={0} uid={uid} />
          </div>
        </>
      ) : (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'RLInterDisplay, Inter, sans-serif', fontWeight: 900,
          fontSize: h * 0.46, letterSpacing: '0.08em', color: '#e4c27a', textShadow: `0 ${u * 0.003}px 0 #6e5427, 0 0 ${u * 0.014}px rgba(228,194,122,0.25)` }}>OPEN</div>
      )}
    </div>
  );
};
/** drop-in for first30/S2A SignFace (fills a SIGN.w x SIGN.h box, default 700 x 330): the same board in the new design */
export const PandaSignFace: React.FC<{ side: 'open' | 'back'; w?: number; h?: number }> = ({ side, w = 700, h = 330 }) => <SignBoard w={w} h={h} side={side} uid={`psf${side}`} />;

// ---------- the lobby wall clock on the S7 door plates (D1, D7, T25 ... every 4320 px S7-camera still, on the 2560 stage) ----------
// It covers the old digital box's spot (layout S7.digital_clock, S7 px (2529..2808) x (948..1055)): "a panda wall clock covers its
// spot" (FIX4_PLAN §2a). r covers the box's half-diagonal; the meter sits just below it. Put it INSIDE the shot's Cam.
export const S7_CLOCK = { cx: 1581.4, cy: 593.6, r: 92 };
// rl5_d (cut 5, CUT5_PLAN §2e "no comp'd clocks anywhere", her N03/N06): on the S7 door plates the panda is gone; the old blank
// digital box under it is covered by a patch of the D1 plate's own wall (public/c5d/s7_wallpatch.png, cut from D1_nobox.jpg).
export const C5_NO_COMP_CLOCKS = true;
const S7Patch: React.FC = () => (
  <img src={staticFile('c5d/s7_wallpatch.png')} style={{ position: 'absolute', left: 2490 * 2560 / 4320, top: 922 * 2560 / 4320, width: 342 * 2560 / 4320, height: 220 * 2560 / 4320 }} />
);
export const LobbyPanda: React.FC<{ time: number; blur?: number; light?: number; dim?: number; chrono?: number; uid?: string }> = ({ time, blur = 0.9, light = 0.95, dim = 0, chrono, uid = 'lp' }) => {
  if (C5_NO_COMP_CLOCKS) return <S7Patch />;
  const { cx, cy, r } = S7_CLOCK;
  return (
    <>
      {/* contact shadow on the lobby wall (key light from upper left) */}
      <div style={{ position: 'absolute', left: cx - r * 0.98 + r * 0.06, top: cy - r * 0.98 + r * 0.1, width: r * 1.96, height: r * 1.96, borderRadius: '50%',
        background: 'rgba(60,40,20,0.42)', filter: `blur(${r * 0.07}px)` }} />
      <PandaClock cx={cx} cy={cy} r={r} time={time} chrono={chrono} variant="wall" blur={blur} light={light * (1 - dim)} shadow={0} uid={uid} />
    </>
  );
};

// the same clock on the other lobby cameras (stage px, measured on the plates by Hough circle, r covers the old gold rim)
export const T6_CLOCK = { cx: 484.8, cy: 329.9, r: 58 };      // T6 camera wide (S11 h1_t4*, 4G): above the QUIET HOURS board
export const E8_CLOCK = { cx: 284.5, cy: 231.6, r: 70 };      // fix2/end/h1_8e_liedown (8E)
export const B2B_CLOCK = { cx: 300, cy: 215, r: 80 };         // the B2B left strip (6A, 6D): the wall above the board (the plate has no clock)
export const WallPanda: React.FC<{ at: { cx: number; cy: number; r: number }; time: number; blur?: number; light?: number; chrono?: number; running?: number; uid?: string }> = ({ at, time, blur = 0.8, light = 0.95, chrono, running, uid = 'wp' }) => (
  <>
    <div style={{ position: 'absolute', left: at.cx - at.r * 0.98 + at.r * 0.07, top: at.cy - at.r * 0.98 + at.r * 0.1, width: at.r * 1.96, height: at.r * 1.96, borderRadius: '50%',
      background: 'rgba(60,40,20,0.4)', filter: `blur(${at.r * 0.08}px)` }} />
    <PandaClock cx={at.cx} cy={at.cy} r={at.r} time={time} chrono={chrono} running={running} variant="wall" blur={blur} light={light} shadow={0} uid={uid} />
  </>
);

// ---------- drop-in replacements for the film's old clock helpers (same props), so one re-export per shared file turns every
// lane's clock into the panda (workers/rl_l3_ui/PATCH.md lists the one-line patches). ----------
const tparse = (text: string) => { const [h, m] = text.split(':').map(Number); return pt(h, m); };

/** s10/_lib WallClock (cx, cy, r = the plate's face radius; hr/min/sec): the panda covers the gold face and rim (rim = 1.12 r) */
export const PandaWallClockCompat: React.FC<{ cx: number; cy: number; r: number; hr: number; min: number; sec?: number | null; face?: boolean; blur?: number }> = ({ cx, cy, r, hr, min, sec = null, blur = 0 }) => (
  <>
    <div style={{ position: 'absolute', left: cx - r * 1.16 + r * 0.07, top: cy - r * 1.16 + r * 0.1, width: r * 2.32, height: r * 2.32, borderRadius: '50%',
      background: 'rgba(60,40,20,0.4)', filter: `blur(${r * 0.08 + blur}px)` }} />
    <PandaClock cx={cx} cy={cy} r={r * 1.16} time={pt(hr, min, sec ?? 0)} chrono={sec ?? 0} running={sec ?? 0} variant="wall" blur={blur} light={0.95} shadow={0} uid={`wc${Math.round(cx)}`} />
  </>
);
/** s03/_lib WallClock (cx, cy, r, minutes since midnight, secs) */
export const PandaWallClockMinutes: React.FC<{ cx: number; cy: number; r: number; minutes: number; secs?: number; blur?: number }> = ({ cx, cy, r, minutes, secs, blur = 0 }) => (
  <WallPanda at={{ cx, cy, r: r * 1.1 }} time={minutes + (secs ?? 0) / 60} chrono={secs ?? 0} blur={blur + 0.6} uid={`wm${Math.round(cx)}`} />
);
/** 13A DigitalTime(text) and s07/_lib D1Clocks(minutes after 6 PM): the S7 lobby panda where the digital box was */
export const PandaDigitalTime: React.FC<{ text: string }> = ({ text }) => <LobbyPanda time={tparse(text)} uid="dt" />;
export const PandaD1Clocks: React.FC<{ minutes: number; digital?: boolean }> = ({ minutes }) => <LobbyPanda time={fromFilm(minutes)} uid="d1c" />;
/** s06/_clock ClockOnWall (minutes since midnight, secs): the B2B wall */
export const PandaClockOnWall: React.FC<{ minutes: number; secs?: number }> = ({ minutes, secs }) => (
  <WallPanda at={B2B_CLOCK} time={minutes + (secs ?? 0) / 60} chrono={secs ?? 0} running={secs ?? 0} uid="cow" />
);
/** S8 close plates (C0/C1/C2): the panda covers the lobby display behind his head, out of focus; `paddle` masks it behind the
 *  raised 429 paddle (C1/C2). Replaces LobbyClock(text) from s03/_lib and first30/S2B. */
export const S8_CLOCK = { cx: 2125.4, cy: 139.0, r: 212 };
export const S8_PADDLE = { cx: 2291.4, cy: 476.7, r: 282 };
export const PandaLobbyClockS8: React.FC<{ text: string; blur?: number; paddle?: boolean }> = ({ text, blur = 4, paddle = true }) => {
  const { cx, cy, r } = S8_CLOCK; const P = S8_PADDLE;
  const mask = paddle ? `radial-gradient(circle ${P.r}px at ${P.cx - (cx - r * 1.2)}px ${P.cy - (cy - r * 1.2)}px, transparent 98%, #000 100%)` : undefined;
  return (
    <div style={{ position: 'absolute', left: cx - r * 1.2, top: cy - r * 1.2, width: r * 2.4, height: r * 2.4, WebkitMaskImage: mask, maskImage: mask }}>
      <div style={{ position: 'absolute', left: r * 0.2 + r * 0.06, top: r * 0.2 + r * 0.09, width: r * 2, height: r * 2, borderRadius: '50%', background: 'rgba(60,40,20,0.38)', filter: `blur(${r * 0.08 + blur}px)` }} />
      <PandaClock cx={r * 1.2} cy={r * 1.2} r={r} time={tparse(text)} variant="wall" blur={blur} light={0.93} shadow={0} uid="s8c" />
    </div>
  );
};
