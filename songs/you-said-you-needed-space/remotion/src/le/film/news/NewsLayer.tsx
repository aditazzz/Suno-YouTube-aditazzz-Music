// Real headlines made of stars (earth_news, Nov 9 2026). Her words: "current events and actual news is always welcome. but exactly as they appear".
// Its OWN layer over the film: nothing in the engine or the section files knows about it. Each headline of headlines.gen.ts (strings from
// build/le_news/VERIFIED.md, never typed by hand) is ~10-16,000 stars that leave the sky around it, write it in reading order, hold, and go home.
// Wire-in (Film.tsx): import { NewsLayer } from './news/NewsLayer';  and  <NewsLayer f={f} fmt={fmt} />  after <HimLayer/>.  Film prop to turn it off: none
// needed (remove the line). Every frame is a pure function of f: the canvas is drawn synchronously in a layout effect, so any frame renders on its own.
import React, { useLayoutEffect, useRef } from 'react';
import { useVideoConfig } from 'remotion';
import * as THREE from 'three';
import { at, FPS } from '../anchor';
import { Fmt } from '../types';
import { NEWS, NewsItem } from './headlines.gen';
import { NEWS_STARS } from './stars.gen';

export const NEWS_GAIN = 1.0;      // overall brightness of the lettering
export const NEWS_SCRIM = 0.6; /* earth_cut2 / fresh eyes: 0.42 before; the small outlet and date lines were hard to read over bright stars */    // how much the sky right behind a headline is dimmed (0 = off): the stars "make room", so it reads on a phone

// when a headline is on: t0 fly-in starts, tA fully formed (the anchor), tB starts to leave, t1 gone
export function newsTimes(n: NewsItem) { const tA = at(n.at); return { t0: tA - n.tin, tA, tB: tA + n.hold, t1: tA + n.hold + n.tout }; }
export function newsAt(t: number): NewsItem[] { return NEWS.filter((n) => { const k = newsTimes(n); return t >= k.t0 - 0.2 && t <= k.t1 + 0.2; }); }

const VERT = /* glsl */ `
attribute vec2 aTarget; attribute vec4 aRnd; // delay 0..1, curl, size (px at 1440 high), part
uniform float uU; uniform float uGain; uniform float uPxScale; uniform float uT;
varying vec3 vCol;
void main(){
  float uin = min(uU, 1.0), uout = max(uU - 1.0, 0.0);
  float a = clamp((uin - aRnd.x * 0.62) / 0.38, 0.0, 1.0); a = a * a * a * (a * (a * 6.0 - 15.0) + 10.0);
  float r1 = fract(aRnd.x * 91.7 + aRnd.y * 37.1), r2 = fract(aRnd.x * 53.3 + aRnd.y * 71.9);
  float b = clamp((uout - r1 * 0.5) / 0.5, 0.0, 1.0); b = b * b * (3.0 - 2.0 * b);
  vec2 h = position.xy; vec2 d = aTarget - h;
  vec2 p = uout > 0.0 ? h + d * (1.0 - b) + vec2(d.y, -d.x) * (aRnd.y - 0.1) * sin(3.14159265 * b)
                      : h + d * a + vec2(-d.y, d.x) * aRnd.y * sin(3.14159265 * a);
  p += 0.0012 * vec2(sin(uT * 0.9 + r1 * 40.0), cos(uT * 0.7 + r2 * 40.0));        // it breathes a little while it holds: stars, not print
  float w = a * (1.0 - b);                                                           // how much of the headline this star is right now
  float part = aRnd.w;
  vec3 IVORY = vec3(0.949, 0.925, 0.882), AURORA = vec3(0.557, 0.388, 0.961);    // PALETTE.md: type is Star Ivory (#F2ECE1), her feed's rule is Aurora (#8E63F5); no warm, no pure white
  vec3 pc = part < 0.5 ? AURORA * 0.62 : part < 1.5 ? IVORY * 0.66 : part < 2.5 ? IVORY * 0.88 : IVORY * 0.62;   // rule, outlet, headline, date (the sum of many stars; rolled off below)
  pc *= (0.82 + 0.36 * r2) * (r1 > 0.988 ? 1.9 : 1.0);                               // a few sparkles ride on the letters
  float tw = 0.86 + 0.14 * sin(uT * (1.5 + 2.5 * r2) + r1 * 40.0);
  vec3 sky = vec3(0.80, 0.88, 1.0) * (0.07 + 0.18 * r2 * r2);
  float fly = sin(3.14159265 * (uout > 0.0 ? b : a));                                // brighter while it travels
  float edge = uout > 0.0 ? 1.0 - b : smoothstep(0.0, 0.12, uin - aRnd.x * 0.62 + 0.12);   // a star lights up as it leaves home and dims as it gets back
  vCol = mix(sky, pc, w) * uGain * tw * (1.0 + 0.8 * fly) * mix(edge, 1.0, w);
  gl_PointSize = mix(2.6 + 2.0 * r2 * r2, aRnd.z, w) * uPxScale * (1.0 + 0.35 * fly);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 0.0, 1.0);
}`;
const FRAG = /* glsl */ `
varying vec3 vCol;
void main(){ vec2 q = gl_PointCoord - 0.5; float r2 = dot(q, q) * 4.0; float a = exp(-r2 * 9.0) + 0.14 * exp(-r2 * 2.5); if (a < 0.004 || r2 > 1.0) discard; gl_FragColor = vec4(vCol * a, 1.0); }`;

// pass 2: the summed stars roll off to a ceiling just under Star Ivory, so dense letters never clip and never turn pure white (QA gate 3, PALETTE.md)
const QUAD_VERT = /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
const QUAD_FRAG = /* glsl */ `
varying vec2 vUv; uniform sampler2D uTex;
void main(){
  vec3 x = texture2D(uTex, vUv).rgb; float m = max(x.r, max(x.g, x.b));
  float ceilv = 0.949 * 0.93, knee = 0.60;                                  // brightest channel never passes 0.883 (225/255): under the film's 0.955 ceiling and the gate's 240
  float mk = m < knee ? m : knee + (ceilv - knee) * (1.0 - exp(-(m - knee) / (ceilv - knee)));   // straight up to the knee, then a soft shoulder
  gl_FragColor = vec4(m > 1e-5 ? x * (mk / m) : vec3(0.0), 1.0);           // scaled as one colour, so ivory stays ivory and her violet stays violet
}`;
type GL = { renderer: THREE.WebGLRenderer; scene: THREE.Scene; cam: THREE.OrthographicCamera; mat: THREE.ShaderMaterial; geo: THREE.BufferGeometry; rt: THREE.WebGLRenderTarget; post: THREE.Scene; quad: THREE.Mesh };
function makeGL(canvas: HTMLCanvasElement, id: string, fmt: Fmt, width: number, height: number): GL {
  const sd = NEWS_STARS[id][fmt], raw = Uint8Array.from(atob(sd.b64), (ch) => ch.charCodeAt(0)), bi = new Int16Array(raw.buffer);
  const geo = new THREE.BufferGeometry(), P = new Float32Array(sd.n * 3), T = new Float32Array(sd.n * 2), R = new Float32Array(sd.n * 4);
  for (let i = 0; i < sd.n; i++) { const o = i * 8; P[i * 3] = bi[o] / 1e4; P[i * 3 + 1] = bi[o + 1] / 1e4; T[i * 2] = bi[o + 2] / 1e4; T[i * 2 + 1] = bi[o + 3] / 1e4; R[i * 4] = bi[o + 4] / 1e4; R[i * 4 + 1] = bi[o + 5] / 1e4; R[i * 4 + 2] = bi[o + 6] / 1e3; R[i * 4 + 3] = bi[o + 7] / 1e3; }
  geo.setAttribute('position', new THREE.BufferAttribute(P, 3)); geo.setAttribute('aTarget', new THREE.BufferAttribute(T, 2)); geo.setAttribute('aRnd', new THREE.BufferAttribute(R, 4));
  geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6);
  const mat = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uU: { value: 0 }, uGain: { value: 0 }, uPxScale: { value: 1 }, uT: { value: 0 } } });
  const pts = new THREE.Points(geo, mat); pts.frustumCulled = false;
  const scene = new THREE.Scene(); scene.add(pts);
  const A = width / height, cam = new THREE.OrthographicCamera(-A, A, 1, -1, -10, 10); cam.position.set(0, 0, 5);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1); renderer.setSize(width, height, false); renderer.setClearColor(0x000000, 1);
  const rt = new THREE.WebGLRenderTarget(width, height, { type: THREE.HalfFloatType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, depthBuffer: false });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({ vertexShader: QUAD_VERT, fragmentShader: QUAD_FRAG, depthTest: false, depthWrite: false, uniforms: { uTex: { value: rt.texture } } }));
  quad.frustumCulled = false; const post = new THREE.Scene(); post.add(quad);
  return { renderer, scene, cam, mat, geo, rt, post, quad };
}

const sm = (x: number) => { const c = Math.min(1, Math.max(0, x)); return c * c * (3 - 2 * c); };
const Headline: React.FC<{ n: NewsItem; f: number; fmt: Fmt }> = ({ n, f, fmt }) => {
  const { width, height } = useVideoConfig(), ref = useRef<HTMLCanvasElement>(null), gl = useRef<GL | null>(null);
  const t = f / FPS, k = newsTimes(n);
  const u = t < k.tA ? (t - k.t0) / n.tin : t < k.tB ? 1 : 1 + (t - k.tB) / n.tout;                  // 0..1 in, 1 hold, 1..2 out
  const gain = sm((t - k.t0) / 0.3) * sm((k.t1 - t) / 0.3);                                           // nothing pops on or off
  const room = sm((t - k.t0) / (n.tin * 0.8)) * sm((k.t1 - t) / (n.tout * 0.9));
  useLayoutEffect(() => {
    if (!ref.current) return;
    if (!gl.current) gl.current = makeGL(ref.current, n.id, fmt, width, height);
    const g = gl.current, un = g.mat.uniforms;
    un.uU.value = Math.max(0, Math.min(2, u)); un.uGain.value = gain * NEWS_GAIN; un.uPxScale.value = height / 1440; un.uT.value = t;
    g.renderer.setRenderTarget(g.rt); g.renderer.clear(); g.renderer.render(g.scene, g.cam); g.renderer.setRenderTarget(null); g.renderer.render(g.post, g.cam);
  }, [f, fmt, width, height, n.id, u, gain, t]);
  useLayoutEffect(() => () => { const g = gl.current; if (g) { g.geo.dispose(); g.mat.dispose(); g.rt.dispose(); g.quad.geometry.dispose(); (g.quad.material as THREE.Material).dispose(); g.renderer.dispose(); g.renderer.forceContextLoss(); gl.current = null; } }, []);
  const A = width / height, [l, b, r, tp] = n.box[fmt];
  const cx = ((l + r) / 2 / A + 1) * 50, cy = (1 - (b + tp) / 2) * 50, rx = ((r - l) / 2 / A) * 50 * 1.5 + 4, ry = ((tp - b) / 2) * 50 * 1.7 + 4;
  return (
    <>
      {NEWS_SCRIM > 0 && <div style={{ position: 'absolute', inset: 0, opacity: room * NEWS_SCRIM, background: `radial-gradient(ellipse ${rx}% ${ry}% at ${cx}% ${cy}%, #000 0%, rgba(0,0,0,0.85) 55%, rgba(0,0,0,0) 100%)` }} />}
      <canvas ref={ref} width={width} height={height} style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: '100%', mixBlendMode: 'screen' }} />
    </>
  );
};

export const NewsLayer: React.FC<{ f: number; fmt: Fmt }> = ({ f, fmt }) => {
  const t = f / FPS, live = NEWS.filter((n) => { const k = newsTimes(n); return !!NEWS_STARS[n.id]?.[fmt] && t >= k.t0 && t <= k.t1; });   // a headline with no clean sky in a format has no stars there
  if (!live.length) return null;
  return <>{live.map((n) => <Headline key={n.id} n={n} f={f} fmt={fmt} />)}</>;
};
