// The WebGL side: one ortho scene in screen units (y -1..1), drawn in order
//   dust (0) -> cast stars, back pass (1) -> her (2, premultiplied) -> mist (3) -> flows (4) -> sparks (5) -> cast stars, front pass (6) -> motes (7)
// then bloom + vignette/grain + ACES/sRGB output (EffectComposer, rendered from useFrame so Remotion's advance() drives it).
import * as THREE from 'three';
import React, { useEffect, useMemo, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { continueRender, delayRender, staticFile } from 'remotion';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { Fmt, Frame } from './types';
import { ASPECT, N_CAST, N_DUST, StarState, rng, starAttr } from './stars';
import { pathAt, projOrbit } from './camera';
import { makeExtras } from './Extra';
import { FINAL_FRAG, FINAL_VERT, MIST_FRAG, PLANET_FRAG, POINTS_FRAG, POINTS_VERT, QUAD_VERT, SPARK_FRAG, SPARK_VERT } from './shaders';

const D2R = Math.PI / 180;
// ---- textures: NASA maps already in public/textures (SOURCES.md); the frame waits until they are on the GPU ----
type Tex = { day: THREE.Texture; night: THREE.Texture; rivers: THREE.Texture; data: THREE.Texture; clouds: THREE.Texture };
let TEX: Promise<Tex> | null = null;
const load = (f: string, srgb: boolean) => new Promise<THREE.Texture>((res, rej) => new THREE.TextureLoader().load(staticFile(`textures/${f}`), (t) => {
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.ClampToEdgeWrapping;
  t.anisotropy = 8; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter; res(t);
}, undefined, rej));
export function useTextures() {
  const [tex, setTex] = useState<Tex | null>(null);
  const [h] = useState(() => delayRender('le textures', { timeoutInMilliseconds: 120000 }));
  useEffect(() => {
    TEX = TEX ?? Promise.all([load('earth_day_8k.jpg', true), load('earth_night_4k.jpg', true), load('earth_rivers_4k.png', false), load('earth_data_4k.png', false), load('earth_clouds_8k.jpg', false)])
      .then(([day, night, rivers, data, clouds]) => ({ day, night, rivers, data, clouds }));
    TEX.then(setTex).catch((e) => console.error('le textures failed', String(e)));
  }, []);
  return { tex, handle: h };
}

const MAX_FLOW = 9000, MAX_SPARK = 24, N_MOTES = 260;
function pointsGeo(n: number) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  g.setAttribute('aSize', new THREE.BufferAttribute(new Float32Array(n), 1));
  g.setAttribute('aColor', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  g.setAttribute('aOcc', new THREE.BufferAttribute(new Float32Array(n), 1));
  g.setAttribute('aDepth', new THREE.BufferAttribute(new Float32Array(n), 1));
  g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6);
  return g;
}
const ADD = { blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor, blendSrcAlpha: THREE.ZeroFactor, blendDstAlpha: THREE.OneFactor, depthTest: false, depthWrite: false, transparent: true } as const;
function pointsMat() { return new THREE.ShaderMaterial({ vertexShader: POINTS_VERT, fragmentShader: POINTS_FRAG, uniforms: { uPar: { value: new THREE.Vector2() }, uPxScale: { value: 1 }, uC: { value: new THREE.Vector2() }, uR: { value: 1 }, uGain: { value: 1 } }, ...ADD }); }

export const Scene: React.FC<{ frame: Frame; stars: StarState; fmt: Fmt; width: number; height: number; tex: Tex; onDrawn: () => void }> = ({ frame, stars, fmt, width, height, tex, onDrawn }) => {
  const { gl, scene } = useThree();
  const A = ASPECT[fmt], pxs = height / 1440, g = frame.grade, cam = frame.cam;
  const ortho = useMemo(() => { const c = new THREE.OrthographicCamera(-A, A, 1, -1, -10, 10); c.position.set(0, 0, 5); return c; }, [A]);
  // ---- objects (built once) ----
  const objs = useMemo(() => {
    const quad = new THREE.PlaneGeometry(2 * A, 2);
    const planetMat = new THREE.ShaderMaterial({
      vertexShader: QUAD_VERT, fragmentShader: PLANET_FRAG, transparent: true, depthTest: false, depthWrite: false,
      blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor, blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor,
      uniforms: {
        uDay: { value: tex.day }, uNight: { value: tex.night }, uRivers: { value: tex.rivers }, uData: { value: tex.data }, uClouds: { value: tex.clouds },
        uC: { value: new THREE.Vector2() }, uR: { value: 1 }, uLat: { value: 0 }, uLon: { value: 0 }, uRoll: { value: 0 }, uPx: { value: 2 / height }, uT: { value: 0 }, uSun: { value: new THREE.Vector3() },
        uGlow: { value: 1 }, uViolet: { value: 0 }, uDaySide: { value: 0 }, uHisWarm: { value: 0 }, uHerCyan: { value: 0 }, uRiv: { value: 0 }, uRivPulse: { value: 0 }, uCoast: { value: 0 },
        uForest: { value: 0 }, uOcean: { value: 0 }, uCloudsK: { value: 0 }, uAtmos: { value: 0 }, uFlare: { value: 0 }, uKick: { value: 0 }, uHisOff: { value: 0 }, uAurora: { value: 0 },
        uSunWarm: { value: 0 }, uLux: { value: 0 }, uCapil: { value: 1 }, uSeam: { value: 0 }, uHaloWide: { value: 0 }, uGold: { value: new THREE.Vector4() },
        uHer: { value: new THREE.Vector3() }, uVio: { value: new THREE.Vector3() }, uHis: { value: new THREE.Vector3() },
        uPulse: { value: Array.from({ length: 8 }, () => new THREE.Vector4()) }, uPulseS: { value: new Array(8).fill(0) },
      },
    });
    const planet = new THREE.Mesh(quad, planetMat); planet.renderOrder = 2; planet.frustumCulled = false;
    const mistMat = new THREE.ShaderMaterial({ vertexShader: QUAD_VERT, fragmentShader: MIST_FRAG, uniforms: { uT: { value: 0 }, uMist: { value: 0 }, uCol: { value: new THREE.Vector3(0.1, 0.5, 0.6) }, uPar: { value: new THREE.Vector2() } }, ...ADD });
    const mist = new THREE.Mesh(quad, mistMat); mist.renderOrder = 3; mist.frustumCulled = false;
    // dust: static faint stars
    const dustG = pointsGeo(N_DUST), R = rng(fmt === '169' ? 99 : 98);
    const dp = dustG.getAttribute('position').array as Float32Array, ds = dustG.getAttribute('aSize').array as Float32Array, dc = dustG.getAttribute('aColor').array as Float32Array, dd = dustG.getAttribute('aDepth').array as Float32Array, doc = dustG.getAttribute('aOcc').array as Float32Array;
    for (let i = 0; i < N_DUST; i++) { dp[i * 3] = (R() * 2 - 1) * A * 1.1; dp[i * 3 + 1] = (R() * 2 - 1) * 1.1; const m = Math.pow(R(), 2.5); ds[i] = 1.6 + 2.4 * m; const b = 0.05 + 0.3 * m; dc.set([b * 0.85, b * 0.92, b], i * 3); dd[i] = 0.08 + 0.2 * R(); doc[i] = 1; }
    const dustMat = pointsMat(); const dust = new THREE.Points(dustG, dustMat); dust.renderOrder = 0; dust.frustumCulled = false;
    const backG = pointsGeo(N_CAST), frontG = pointsGeo(N_CAST);
    const backMat = pointsMat(), frontMat = pointsMat();
    const back = new THREE.Points(backG, backMat); back.renderOrder = 1; back.frustumCulled = false;
    const front = new THREE.Points(frontG, frontMat); front.renderOrder = 6; front.frustumCulled = false;
    const flowG = pointsGeo(MAX_FLOW), flowMat = pointsMat(); const flows = new THREE.Points(flowG, flowMat); flows.renderOrder = 4; flows.frustumCulled = false;
    const moteG = pointsGeo(N_MOTES), moteMat = pointsMat(); const motes = new THREE.Points(moteG, moteMat); motes.renderOrder = 7; motes.frustumCulled = false;
    const sparkQuad = new THREE.PlaneGeometry(1, 1);
    const sparks = Array.from({ length: MAX_SPARK }, () => { const m = new THREE.Mesh(sparkQuad, new THREE.ShaderMaterial({ vertexShader: SPARK_VERT, fragmentShader: SPARK_FRAG, uniforms: { uCol: { value: new THREE.Vector3() }, uOcc: { value: 0 }, uC: { value: new THREE.Vector2() }, uR: { value: 1 } }, ...ADD })); m.renderOrder = 5; m.frustumCulled = false; m.visible = false; return m; });
    const extras = makeExtras({ A, fmt, height }); // proof-30 layers (galaxy, deep stars, ...): off unless their grade knobs are set
    return { planet, planetMat, mist, mistMat, dust, dustMat, back, backMat, front, frontMat, flows, flowMat, motes, moteMat, sparks, extras };
  }, [tex, A, fmt, height]);
  // attached synchronously (an effect can run after the first advance() and leave the first frame empty)
  for (const o of [...objs.extras.objects, objs.dust, objs.back, objs.planet, objs.mist, objs.flows, ...objs.sparks, objs.front, objs.motes]) if (o.parent !== scene) scene.add(o);
  // ---- post ----
  const post = useMemo(() => {
    gl.toneMapping = THREE.ACESFilmicToneMapping; gl.outputColorSpace = THREE.SRGBColorSpace; gl.setPixelRatio(1);
    const rt = new THREE.WebGLRenderTarget(width, height, { type: THREE.HalfFloatType });
    const composer = new EffectComposer(gl, rt); composer.setPixelRatio(1); composer.setSize(width, height);
    const rp = new RenderPass(scene, ortho); rp.clearColor = new THREE.Color(0, 0, 0); rp.clearAlpha = 1;
    const bloom = new UnrealBloomPass(new THREE.Vector2(width, height), 0.9, 0.5, 0.12);
    const fin = new ShaderPass(new THREE.ShaderMaterial({ vertexShader: FINAL_VERT, fragmentShader: FINAL_FRAG, uniforms: { tDiffuse: { value: null }, uVig: { value: 0.5 }, uGrain: { value: 0.03 }, uT: { value: 0 }, uAspect: { value: A } } }));
    composer.addPass(rp); composer.addPass(bloom); composer.addPass(fin); composer.addPass(new OutputPass());
    return { composer, bloom, fin };
  }, [gl, scene, ortho, width, height, A]);
  useFrame(() => { post.composer.render(); if (scene.children.length > 0) onDrawn(); }, 1);

  // ---- per-frame state -> uniforms/buffers (everything below is a function of `frame` and `stars`) ----
  const t = frame.t;
  const pu = objs.planetMat.uniforms;
  pu.uC.value.set(cam.x, cam.y); pu.uR.value = cam.r; pu.uLat.value = cam.lat * D2R; pu.uLon.value = cam.lon * D2R; pu.uRoll.value = cam.roll * D2R; pu.uT.value = t;
  pu.uSun.value.set(cam.sun[0], cam.sun[1], cam.sun[2]);
  pu.uGlow.value = g.glow; pu.uViolet.value = g.violet; pu.uDaySide.value = g.daySide; pu.uHisWarm.value = g.hisWarm; pu.uHerCyan.value = g.herCyan;
  pu.uRiv.value = g.rivers; pu.uRivPulse.value = g.riverPulse; pu.uCoast.value = g.coast; pu.uForest.value = g.forest; pu.uOcean.value = g.ocean;
  pu.uCloudsK.value = g.clouds; pu.uAtmos.value = g.atmos; pu.uFlare.value = g.flare; pu.uKick.value = g.kick; pu.uHisOff.value = g.hisOff; pu.uAurora.value = g.aurora;
  pu.uGold.value.set(g.goldLat * D2R, g.goldLon * D2R, g.goldR * D2R, g.goldK); pu.uLux.value = g.lux; pu.uSunWarm.value = g.sunWarm; pu.uCapil.value = g.capil; pu.uSeam.value = g.seam; pu.uHaloWide.value = g.haloWide;
  objs.extras.update(frame, pxs);
  pu.uHer.value.set(...g.herColor); pu.uVio.value.set(...g.violetColor); pu.uHis.value.set(...g.hisColor);
  const ps = frame.pulses.slice(-8);
  for (let i = 0; i < 8; i++) { const p = ps[i]; pu.uPulse.value[i].set(p ? p.lat * D2R : 0, p ? p.lon * D2R : 0, p ? p.t0 : 0, p ? p.speed * D2R : 0); pu.uPulseS.value[i] = p ? p.strength : 0; }
  const mu = objs.mistMat.uniforms; mu.uT.value = t; mu.uMist.value = g.mist; mu.uPar.value.set(cam.par[0], cam.par[1]); mu.uCol.value.set(g.herColor[0] * 0.4 + g.violetColor[0] * 0.3 * g.violet, g.herColor[1] * 0.45, g.herColor[2] * 0.5 + g.violetColor[2] * 0.2 * g.violet);
  for (const m of [objs.dustMat, objs.backMat, objs.frontMat, objs.flowMat, objs.moteMat]) { m.uniforms.uPxScale.value = pxs; m.uniforms.uC.value.set(cam.x, cam.y); m.uniforms.uR.value = cam.r; m.uniforms.uPar.value.set(cam.par[0], cam.par[1]); }
  objs.dustMat.uniforms.uGain.value = g.dust * g.stars; objs.dust.visible = g.dust > 0.001;
  // cast stars
  {
    const SA = starAttr();
    const fill = (geo: THREE.BufferGeometry, pass: 0 | 1) => {
      const P = geo.getAttribute('position').array as Float32Array, S = geo.getAttribute('aSize').array as Float32Array, Cc = geo.getAttribute('aColor').array as Float32Array, O = geo.getAttribute('aOcc').array as Float32Array, Dp = geo.getAttribute('aDepth').array as Float32Array;
      for (let i = 0; i < N_CAST; i++) {
        const wgt = pass === 0 ? 1 - stars.front[i] : stars.front[i];
        const tw = 0.82 + 0.18 * Math.sin(t * (1.3 + 2.1 * SA.r2[i]) + SA.r1[i] * 40);
        const b = SA.bright[i] * tw * wgt * g.stars * (1 + 1.5 * stars.motion[i]);
        P[i * 3] = stars.pos[i * 2]; P[i * 3 + 1] = stars.pos[i * 2 + 1];
        S[i] = SA.size[i] * (1 + 0.6 * stars.motion[i]) * (pass === 1 ? 1.15 : 1);
        { const cw = g.castWarm, em = SA.r1[i] < 0.3, lum = 1.25 * (SA.color[i * 3] + SA.color[i * 3 + 1] + SA.color[i * 3 + 2]) / 3; // castWarm: his gold (Filament, 30% Ember)
          Cc[i * 3] = (SA.color[i * 3] * (1 - cw) + lum * cw) * b; Cc[i * 3 + 1] = (SA.color[i * 3 + 1] * (1 - cw) + (em ? 0.34 : 0.64) * lum * cw) * b; Cc[i * 3 + 2] = (SA.color[i * 3 + 2] * (1 - cw) + (em ? 0.08 : 0.28) * lum * cw) * b; }
        O[i] = pass === 0 ? 1 : 0; Dp[i] = SA.depth[i] * (1 - stars.front[i]);
      }
      for (const k of ['position', 'aSize', 'aColor', 'aOcc', 'aDepth']) geo.getAttribute(k).needsUpdate = true;
    };
    fill(objs.back.geometry, 0); fill(objs.front.geometry, 1);
  }
  // flows
  {
    const geo = objs.flows.geometry, P = geo.getAttribute('position').array as Float32Array, S = geo.getAttribute('aSize').array as Float32Array, Cc = geo.getAttribute('aColor').array as Float32Array, O = geo.getAttribute('aOcc').array as Float32Array;
    let k = 0;
    for (const f of frame.flows) {
      const n = f.count ?? 160;
      for (let j = 0; j < n && k < MAX_FLOW; j++) {
        const fr = j / Math.max(1, n - 1); let s = f.head - f.tail * fr;
        let a = Math.pow(1 - fr, 1.4) * f.intensity;
        if (f.dash && f.dash > 0) { const seg = (fr * f.dash) % 1; a *= seg < 0.45 ? 1 : 0; }
        if (s < 0 || s > 1) { a = 0; s = Math.max(0, Math.min(1, s)); }
        const pr = pathAt(cam, f.path, s); if (!pr.visible) a = 0;
        P[k * 3] = pr.x; P[k * 3 + 1] = pr.y; S[k] = f.size * (j === 0 ? 2.2 : 1) * (0.7 + 0.3 * (1 - fr));
        Cc[k * 3] = f.color[0] * a; Cc[k * 3 + 1] = f.color[1] * a; Cc[k * 3 + 2] = f.color[2] * a; O[k] = 0; k++;
      }
    }
    for (; k < MAX_FLOW; k++) { S[k] = 0; Cc[k * 3] = Cc[k * 3 + 1] = Cc[k * 3 + 2] = 0; }
    for (const a of ['position', 'aSize', 'aColor', 'aOcc']) geo.getAttribute(a).needsUpdate = true;
  }
  // sparks
  objs.sparks.forEach((m, i) => {
    const s = frame.sparks[i]; if (!s || s.intensity <= 0.001) { m.visible = false; return; }
    let x = s.x, y = s.y, vis = true;
    if (s.orbit) { const p = projOrbit(cam, s.orbit[0], s.orbit[1], s.orbit[2], s.orbit[3]); x = p.x; y = p.y; vis = p.visible; }
    else if (s.rel) { x = cam.x + cam.r * s.rel[0]; y = cam.y + cam.r * s.rel[1]; }
    m.visible = vis; const sz = (s.size * 2 / 1440) * 3; m.scale.set(sz, sz, 1); m.position.set(x, y, 0);
    (m.material as THREE.ShaderMaterial).uniforms.uCol.value.set(s.color[0] * s.intensity, s.color[1] * s.intensity, s.color[2] * s.intensity);
  });
  // motes: soft out-of-focus lights in front, drifting / falling (rain) / rising
  {
    const geo = objs.motes.geometry, P = geo.getAttribute('position').array as Float32Array, S = geo.getAttribute('aSize').array as Float32Array, Cc = geo.getAttribute('aColor').array as Float32Array, Dp = geo.getAttribute('aDepth').array as Float32Array;
    const R = rng(4242), mode = frame.motes ?? 'drift';
    for (let i = 0; i < N_MOTES; i++) {
      const x0 = (R() * 2 - 1) * A * 1.1, y0 = R() * 2.4, dep = R(), ph = R() * 6.28, sp = 0.02 + 0.05 * R(), sz = 3 + 22 * Math.pow(R(), 2.2), hue = R();
      const vy = mode === 'rain' ? -(0.35 + 0.5 * dep) : mode === 'rise' ? 0.12 + 0.2 * dep : 0.015 * Math.sin(ph);
      let y = ((y0 + vy * t) % 2.4 + 2.4) % 2.4 - 1.2;
      const x = x0 + Math.sin(t * sp * 6 + ph) * 0.05 + (mode === 'rain' ? 0.08 * y : 0);
      P[i * 3] = x; P[i * 3 + 1] = y; S[i] = sz * (mode === 'rain' ? 0.7 : 1); Dp[i] = 0.6 + 1.6 * dep;
      const b = g.motes * (0.06 + 0.22 * (1 - Math.min(1, sz / 25))) * (0.6 + 0.4 * Math.sin(t * 0.8 + ph));
      const c = hue < 0.7 ? g.herColor : hue < 0.9 ? [0.4, 1, 0.8] : g.violetColor;
      Cc[i * 3] = c[0] * b; Cc[i * 3 + 1] = c[1] * b; Cc[i * 3 + 2] = c[2] * b;
    }
    for (const a of ['position', 'aSize', 'aColor', 'aDepth']) geo.getAttribute(a).needsUpdate = true;
  }
  post.bloom.strength = g.bloom; post.bloom.radius = g.bloomRadius; post.bloom.threshold = g.bloomThreshold;
  const fu = (post.fin.material as THREE.ShaderMaterial).uniforms; fu.uVig.value = g.vignette; fu.uGrain.value = g.grain; fu.uT.value = t;
  gl.toneMappingExposure = g.exposure;
  return null;
};
