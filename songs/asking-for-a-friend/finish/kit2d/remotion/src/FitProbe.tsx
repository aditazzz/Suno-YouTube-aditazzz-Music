// Text-fit probe for Remotion/HTML films (studio rule: no text spilling over its box). Copy this file into the project's src/ and
// wrap every composition in <FitProbe id=...>. It does NOTHING in normal renders: it only runs when tools/text_fit_check.py
// renders with inputProps {__fit: pad}. Then, for the rendered frame, it measures every text node (Range rects = real glyph
// line extents) against its container and logs one 'FITJSON{...}' browser line that tools/textfit/remotion_fit.mjs collects.
// Container = nearest ancestor-or-self with a background / border / data-fit attribute. Opt a subtree out with data-fit="off"
// (decorative, intentionally bleeding or tiny in-world text) or out of the overlap test with data-fit="overlap-ok".
import React from 'react';
import { continueRender, delayRender, getInputProps, useCurrentFrame, useVideoConfig } from 'remotion';

type R = { l: number; t: number; r: number; b: number };
const alpha = (c: string) => { const m = c.match(/\(([^)]+)\)/); if (!m) return c === 'transparent' ? 0 : 1; const p = m[1].split(/[ ,/]+/).filter(Boolean); return p.length >= 4 ? parseFloat(p[3]) : 1; };
const isBox = (el: Element) => {
  const d = el.getAttribute('data-fit'); if (d && d !== 'off' && d !== 'overlap-ok') return true;
  const cs = getComputedStyle(el);
  return alpha(cs.backgroundColor) > 0.08 || (cs.backgroundImage !== 'none' && cs.backgroundImage !== '') || (parseFloat(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none' && alpha(cs.borderTopColor) > 0.05);
};
const clips = (el: Element) => { const cs = getComputedStyle(el); return ['hidden', 'clip', 'auto', 'scroll'].includes(cs.overflowX) || ['hidden', 'clip', 'auto', 'scroll'].includes(cs.overflowY); };
const rect = (r: DOMRect | R): R => ('left' in r ? { l: r.left, t: r.top, r: r.right, b: r.bottom } : r);
const textRect = (n: Text): R | null => {
  const rg = document.createRange(); rg.selectNodeContents(n);
  const rs = [...rg.getClientRects()].filter((x) => x.width > 0.5 && x.height > 0.5); if (!rs.length) return null;
  const l = Math.min(...rs.map((x) => x.left)), r = Math.max(...rs.map((x) => x.right));
  let t = Math.min(...rs.map((x) => x.top)), b = Math.max(...rs.map((x) => x.bottom));
  // tighten top/bottom from the line box to the real glyph extents (canvas measureText of the actual string in the actual font)
  try {
    const el = n.parentElement!; const cs = getComputedStyle(el);
    const ctx = (textRect as any).ctx || ((textRect as any).ctx = document.createElement('canvas').getContext('2d')!);
    ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    const tm = ctx.measureText(n.textContent!.trim());
    if (tm.fontBoundingBoxAscent !== undefined) {
      const fh = tm.fontBoundingBoxAscent + tm.fontBoundingBoxDescent; const top = Math.min(...rs.map((x) => x.top)), bot = Math.max(...rs.map((x) => x.bottom));
      const first = rs.filter((x) => Math.abs(x.top - top) < 2)[0], last = rs.filter((x) => Math.abs(x.bottom - bot) < 2).slice(-1)[0];
      t = first.top + (first.height - fh) / 2 + (tm.fontBoundingBoxAscent - tm.actualBoundingBoxAscent);
      b = last.bottom - (last.height - fh) / 2 - (tm.fontBoundingBoxDescent - tm.actualBoundingBoxDescent);
    }
  } catch (_) { /* keep line-box extents */ }
  return { l, t, r, b };
};
const padBox = (el: Element): R => { const b = el.getBoundingClientRect(); const cl = (el as HTMLElement).clientLeft || 0, ct = (el as HTMLElement).clientTop || 0, cw = (el as HTMLElement).clientWidth, ch = (el as HTMLElement).clientHeight; return cw && ch ? { l: b.left + cl, t: b.top + ct, r: b.left + cl + cw, b: b.top + ct + ch } : rect(b); };
const rounded = (r: R) => ({ l: Math.round(r.l), t: Math.round(r.t), r: Math.round(r.r), b: Math.round(r.b) });

/** with chain[0..upto] stripped of rotate/scale (translation kept) run fn, then restore: compares text and box in the box's own axes */
function local<T>(chain: Element[], upto: number, fn: () => T): T {
  const saved: [HTMLElement, string][] = [];
  for (let i = 0; i <= upto; i++) {
    const el = chain[i] as HTMLElement; if (!el.style) continue;
    const tr = getComputedStyle(el).transform; if (tr === 'none') continue;
    const m = new DOMMatrix(tr); saved.push([el, el.style.transform]);
    el.style.transform = m.is2D && m.a === 1 && m.b === 0 && m.c === 0 && m.d === 1 ? tr : `translate(${m.e}px, ${m.f}px)`;
  }
  try { return fn(); } finally { for (const [el, v] of saved) el.style.transform = v; }
}

export function measureFit(root: HTMLElement, pad: number, W: number, H: number) {
  const out: any[] = []; const nodes: { n: Text; el: Element; sr: R }[] = []; let checked = 0;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode() as Text | null; n; n = walker.nextNode() as Text | null) {
    if (!n.textContent || !n.textContent.trim()) continue;
    const el = n.parentElement; if (!el) continue;
    const chain: Element[] = []; let op = 1, off = false;
    for (let e: Element | null = el; e && e !== root.parentElement; e = e.parentElement) {
      chain.push(e); const cs = getComputedStyle(e); op *= parseFloat(cs.opacity); if (cs.visibility === 'hidden' || cs.display === 'none') off = true;
      if (e.getAttribute('data-fit') === 'off') off = true;
    }
    if (off || op < 0.05) continue;
    const sr = textRect(n); if (!sr) continue;
    if (sr.r < 0 || sr.l > W || sr.b < 0 || sr.t > H) continue; // wholly off-frame = not on screen (waiting to slide in)
    checked++; nodes.push({ n, el, sr });
    const fail: string[] = []; const info: any = {};
    const cs = getComputedStyle(el);
    // (1) nearest container: padding
    const ci = chain.findIndex(isBox);
    if (ci >= 0) {
      const c = chain[ci];
      const { tr, cr } = local(chain, chain.length - 1, () => ({ tr: textRect(n)!, cr: rect(c.getBoundingClientRect()) }));
      const m = { left: tr.l - cr.l, right: cr.r - tr.r, top: tr.t - cr.t, bottom: cr.b - tr.b };
      const vpad = pad;
      const worst = Math.min(m.left, m.right);
      info.container = { tag: c.tagName.toLowerCase(), cls: (c.getAttribute('class') || '').slice(0, 30), screen: rounded(rect(c.getBoundingClientRect())), margins: Object.fromEntries(Object.entries(m).map(([k, v]) => [k, Math.round(v)])) };
      const tol = 2; // glyph measuring tolerance, px at 1440p
      if (m.left < -1 || m.right < -1 || m.top < -1 || m.bottom < -1) fail.push('outside');
      else if (worst < pad - tol || m.top < vpad - tol || m.bottom < vpad - tol) fail.push('tight');
    }
    // (2) any clipping ancestor cutting the text
    let hidden = false;
    for (let i = 0; i < chain.length; i++) {
      if (!clips(chain[i])) continue;
      const { tr, kr } = local(chain, chain.length - 1, () => ({ tr: textRect(n)!, kr: padBox(chain[i]) }));
      if (tr.r < kr.l || tr.l > kr.r || tr.b < kr.t || tr.t > kr.b) { hidden = true; break; } // wholly outside its clipper: hidden, not cut
      if (tr.l < kr.l - 1 || tr.r > kr.r + 1 || tr.t < kr.t - 1 || tr.b > kr.b + 1) { fail.push('clipped'); info.clipper = { tag: chain[i].tagName.toLowerCase(), screen: rounded(rect(chain[i].getBoundingClientRect())) }; break; }
    }
    if (hidden) { checked--; nodes.pop(); continue; }
    // (3) text element itself overflowing (scroll size), e.g. ellipsis or hidden overflow
    const h = el as HTMLElement;
    if (h.scrollWidth && h.clientWidth && (cs.overflowX !== 'visible' || cs.textOverflow === 'ellipsis') && h.scrollWidth > h.clientWidth + 1) fail.push('overflow');
    // (4) frame edge
    if (sr.l < pad - 1 || sr.t < 2 || sr.r > W - pad + 1 || sr.b > H - 2) fail.push(sr.l < 0 || sr.t < 0 || sr.r > W || sr.b > H ? 'offframe' : 'frame-edge');
    if (fail.length) out.push({ text: n.textContent.trim().slice(0, 48), kind: fail, text_rect: rounded(sr), fontSize: parseFloat(cs.fontSize), ...info });
  }
  // (5) two different text blocks drawn over each other (mid-move collisions)
  const skip = (e: Element) => !!e.closest('[data-fit="overlap-ok"]');
  for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
    const a = nodes[i], b = nodes[j]; if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el) || a.el.parentElement === b.el.parentElement || skip(a.el) || skip(b.el)) continue;
    const sh = (r: R): R => { const dh = (r.b - r.t) * 0.18, dw = (r.r - r.l) * 0.04; return { l: r.l + dw, r: r.r - dw, t: r.t + dh, b: r.b - dh }; };
    const A = sh(a.sr), B = sh(b.sr); const w = Math.min(A.r, B.r) - Math.max(A.l, B.l), hh = Math.min(A.b, B.b) - Math.max(A.t, B.t);
    if (w > 4 && hh > 4) out.push({ text: `${a.n.textContent!.trim().slice(0, 24)}  x  ${b.n.textContent!.trim().slice(0, 24)}`, kind: ['overlap'], text_rect: rounded({ l: Math.max(a.sr.l, b.sr.l), t: Math.max(a.sr.t, b.sr.t), r: Math.min(a.sr.r, b.sr.r), b: Math.min(a.sr.b, b.sr.b) }), fontSize: 0 });
  }
  return { checked, fails: out };
}

export const FitProbe: React.FC<{ id: string; children: React.ReactNode }> = ({ id, children }) => {
  const ref = React.useRef<HTMLDivElement>(null);
  const frame = useCurrentFrame(); const { width, height } = useVideoConfig();
  const ip: any = getInputProps(); const on = ip && ip.__fit !== undefined && ip.__fit !== null;
  const [h0] = React.useState(() => (on ? delayRender('fitprobe') : 0));
  React.useEffect(() => {
    if (!on) return;
    let live = true; const h1 = delayRender('fitprobe2');
    (async () => {
      try {
        await (document as any).fonts.ready;
        await Promise.all([...document.images].map((i) => (i.decode ? i.decode().catch(() => undefined) : undefined)));
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
        if (live && ref.current) {
          const pad = Math.max(2, Math.round(Number(ip.__fit || 12) * width / 2560));
          const res = measureFit(ref.current, pad, width, height);
          console.log('FITJSON' + JSON.stringify({ id, frame, pad, w: width, h: height, ...res }));
        }
      } catch (e) { console.log('FITJSON' + JSON.stringify({ id, frame, error: String(e) })); }
      if (h0) { try { continueRender(h0); } catch (_) { /* already released */ } }
      continueRender(h1);
    })();
    return () => { live = false; };
  }, [frame]);
  return <div ref={ref} style={{ position: 'absolute', inset: 0 }}>{children}</div>;
};
