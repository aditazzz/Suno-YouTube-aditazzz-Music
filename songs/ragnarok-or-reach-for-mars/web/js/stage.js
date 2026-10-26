// renderer + post chain for the film (the chain from the "I have a blocker." 3D film: bloom, then a finish pass with
// vignette, grain, a touch of chromatic aberration, a flash and a fade; plus a warm/cool split-tone for firelight).
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

export function makeStage(W, H, { exposure = 1.0, bloom = [0.55, 0.55, 0.78] } = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1); renderer.setSize(W, H);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = exposure;
  document.body.appendChild(renderer.domElement);
  const composer = new EffectComposer(renderer);
  const rp = new RenderPass(new THREE.Scene(), new THREE.PerspectiveCamera()); composer.addPass(rp);
  const bl = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), bloom[0], bloom[1], bloom[2]); composer.addPass(bl);
  const finish = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uVig: { value: 0.38 }, uGrain: { value: 0.028 }, uCA: { value: 0.0011 }, uFlash: { value: 0 }, uFade: { value: 1 },
      uFlashCol: { value: new THREE.Color(1, 1, 1) }, uSplit: { value: 0.06 } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime, uVig, uGrain, uCA, uFlash, uFade, uSplit; uniform vec3 uFlashCol; varying vec2 vUv;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + uTime * 17.0) * 43758.5453); }
      void main(){ vec2 d = vUv - 0.5; vec3 c;
        c.r = texture2D(tDiffuse, vUv + d * uCA).r; c.g = texture2D(tDiffuse, vUv).g; c.b = texture2D(tDiffuse, vUv - d * uCA).b;
        float l = dot(c, vec3(0.299, 0.587, 0.114));
        c += uSplit * mix(vec3(-0.25, 0.0, 0.35), vec3(0.3, 0.08, -0.25), smoothstep(0.05, 0.6, l)) * (1.0 - l);   // cool shadows, warm lights
        c *= 1.0 - uVig * pow(length(d * vec2(1.0, 0.9)) * 1.45, 2.4);
        c += (h(vUv * 1000.0) - 0.5) * uGrain; c = mix(c, uFlashCol, uFlash); gl_FragColor = vec4(max(c, 0.0) * uFade, 1.0); }` });
  composer.addPass(finish); composer.addPass(new OutputPass());
  return {
    renderer, composer, bloom: bl, finish, W, H,
    render(scene, cam, t = 0) { rp.scene = scene; rp.camera = cam; finish.uniforms.uTime.value = t; composer.render(); },
    jpeg(q = 0.93) { return renderer.domElement.toDataURL('image/jpeg', q); },
  };
}
