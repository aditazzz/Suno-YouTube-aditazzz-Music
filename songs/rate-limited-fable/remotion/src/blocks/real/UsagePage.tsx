// Settings > Usage in the Claude app (mobile layout, iOS points 393 x 852): "Plan usage limits", the current session bar with
// its reset countdown, the weekly limits, "Last updated", and iOS pull-to-refresh (pull = 0..1 drag, spin = the spinner phase).
import React from 'react';
import { APP, F, MODEL, MOBILE, Theme } from './tokens';
import { IcRefresh } from './Icons';
import { RoundBtn, IcChevL } from './MobileApp';

const Bar: React.FC<{ t: Theme; v: number; full?: boolean }> = ({ t, v, full }) => (
  <div style={{ height: 8, borderRadius: 4, background: t.barTrack, overflow: 'hidden' }}>
    <div style={{ width: `${Math.min(100, v * 100)}%`, height: '100%', borderRadius: 4, background: full ? t.accent : t.bar }} />
  </div>
);
const Row: React.FC<{ t: Theme; title: string; sub: React.ReactNode; v: number; full?: boolean; subColor?: string }> = ({ t, title, sub, v, full, subColor }) => (
  <div style={{ padding: '14px 0' }}>
    <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 }}>
      <div>
        <div style={{ fontSize: 16, fontWeight: 600, color: t.text }}>{title}</div>
        <div style={{ fontSize: 14, color: subColor ?? t.text3, marginTop: 3 }}>{sub}</div>
      </div>
      <div style={{ fontSize: 14, color: t.text3, whiteSpace: 'nowrap' }}>{Math.round(v * 100)}% used</div>
    </div>
    <Bar t={t} v={v} full={full} />
  </div>
);

/** iOS activity spinner (8 spokes) */
export const Spinner: React.FC<{ phase: number; size?: number; color?: string; opacity?: number }> = ({ phase, size = 28, color = '#8E8E93', opacity = 1 }) => (
  <svg width={size} height={size} viewBox="-14 -14 28 28" style={{ opacity }}>
    {Array.from({ length: 8 }, (_, i) => {
      const k = ((i - Math.floor(phase * 8)) % 8 + 8) % 8;
      return <line key={i} x1={0} y1={-6} x2={0} y2={-11} stroke={color} strokeWidth={2.6} strokeLinecap="round" opacity={0.25 + 0.75 * (1 - k / 8)} transform={`rotate(${i * 45})`} />;
    })}
  </svg>
);

export const UsagePage: React.FC<{
  t?: Theme; resetsIn: React.ReactNode; session?: number; reachedAt?: string; weekly?: number; weeklyModel?: number; weeklyReset?: string;
  pull?: number; spin?: number; updated?: string;
}> = ({ t = MOBILE, resetsIn, session = 1, reachedAt = '2:01 AM', weekly = 0.64, weeklyModel = 0.81, weeklyReset = 'Mon 9:00 AM', pull = 0, spin = 0, updated = 'less than a minute ago' }) => {
  const drop = 70 * pull;
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 393, height: 852, background: t.bg, overflow: 'hidden', fontFamily: F.ios, letterSpacing: '-0.01em', color: t.text }}>
      {/* nav: the app's round white back button (as the menu/ghost buttons on her home screen) and the page title */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 54, height: 46, display: 'flex', alignItems: 'center', padding: '0 18px', background: t.bg, zIndex: 3 }}>
        <RoundBtn><IcChevL s={21} c={APP.icon} /></RoundBtn>
        <div style={{ flex: 1, textAlign: 'center', fontFamily: F.ios, fontSize: 17, fontWeight: 600, letterSpacing: '-0.01em', color: APP.ink, marginRight: 39.5 }}>Settings</div>
      </div>
      {/* pull-to-refresh spinner */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 104, height: drop, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1 }}>
        {pull > 0.05 ? <Spinner phase={spin} opacity={Math.min(1, pull * 1.6)} /> : null}
      </div>
      <div style={{ position: 'absolute', left: 20, right: 20, top: 104 + drop, zIndex: 2 }}>
        <div style={{ fontFamily: F.appSerif, fontSize: 32, fontWeight: 600, letterSpacing: '-0.03em', lineHeight: 1.15, color: APP.greet, margin: '6px 0 22px' }}>Usage</div>
        <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 2 }}>Plan usage limits</div>
        <Row t={t} title="Current session" sub={resetsIn} v={session} full={session >= 1} />
        <div style={{ fontSize: 14, color: t.text3, marginTop: -2, marginBottom: 8 }}>Limit reached at {reachedAt}</div>
        <div style={{ height: 0.5, background: t.border, margin: '8px 0 16px' }} />
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
          <div style={{ fontSize: 18, fontWeight: 600 }}>Weekly limits</div>
        </div>
        <div style={{ fontSize: 14, color: t.text3, marginTop: 4 }}>Learn more about <span style={{ textDecoration: 'underline', textUnderlineOffset: 3 }}>usage limits</span></div>
        <Row t={t} title="All models" sub={`Resets ${weeklyReset}`} v={weekly} />
        <Row t={t} title={`${MODEL.split(' ')[0]} only`} sub={`Resets ${weeklyReset}`} v={weeklyModel} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: t.text3, marginTop: 10 }}>
          Last updated: {updated}<IcRefresh s={15} c={t.text3} />
        </div>
      </div>
    </div>
  );
};
