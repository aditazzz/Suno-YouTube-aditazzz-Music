// renderer, post (bloom + a film finish: motion blur, chromatic aberration, grade, grain, vignette, flashes)
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export function makeLook(W, H) {
  const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1); renderer.setSize(W, H);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
  document.body.appendChild(renderer.domElement);
  const pm = new THREE.PMREMGenerator(renderer);
  const envTex = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 0 });
  const composer = new EffectComposer(renderer, rt);
  const renderPass = new RenderPass(null, null); composer.addPass(renderPass);
  const bloom = new UnrealBloomPass(new THREE.Vector2(Math.round(W / 2), Math.round(H / 2)), 0.65, 0.55, 0.78); composer.addPass(bloom);
  const finish = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uVig: { value: 0.32 }, uGrain: { value: 0.045 }, uCA: { value: 0.0016 },
      uVel: { value: new THREE.Vector2(0, 0) }, uFlash: { value: 0 }, uFlashCol: { value: new THREE.Color(1, 1, 1) }, uFade: { value: 0 },
      uLift: { value: new THREE.Color(0.012, 0.010, 0.022) }, uGain: { value: new THREE.Color(1.03, 1.0, 0.96) }, uSat: { value: 1.06 }, uAspect: { value: W / H } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uTime, uVig, uGrain, uCA, uFlash, uFade, uSat, uAspect; uniform vec2 uVel; uniform vec3 uFlashCol, uLift, uGain; varying vec2 vUv;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      vec3 tap(vec2 uv){ vec2 d = uv - 0.5; vec2 o = d * uCA;
        return vec3(texture2D(tDiffuse, uv + o).r, texture2D(tDiffuse, uv).g, texture2D(tDiffuse, uv - o).b); }
      void main(){
        vec3 c = vec3(0.0);
        if (length(uVel) > 0.0005) { for (int i = 0; i < 9; i++) { float k = float(i) / 8.0 - 0.5; c += tap(vUv + uVel * k); } c /= 9.0; }
        else c = tap(vUv);
        float l = dot(c, vec3(0.2126, 0.7152, 0.0722)); c = mix(vec3(l), c, uSat);
        c = c * uGain + uLift * (1.0 - clamp(l * 3.0, 0.0, 1.0));
        vec2 d = (vUv - 0.5) * vec2(uAspect, 1.0) / uAspect * 1.9;
        c *= 1.0 - uVig * pow(clamp(length(d), 0.0, 1.4), 2.6);
        c += (h(vUv * 1000.0 + fract(uTime * 7.13)) - 0.5) * uGrain;
        c = mix(c, uFlashCol, uFlash); c *= 1.0 - uFade;
        gl_FragColor = vec4(c, 1.0); }` });
  composer.addPass(finish); composer.addPass(new OutputPass());
  return { renderer, composer, renderPass, bloom, finish, envTex };
}
