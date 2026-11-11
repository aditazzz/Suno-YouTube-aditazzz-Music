// @ts-nocheck
// HERO WORLD (Fable, Nov 10): the real 3D world for the bridge, the eclipse and the crash. Plain three.js, no react-three:
// one function builds the world once, render(t, shot) draws any moment of it deterministically (no clocks, no Math.random).
// Geography ("Bigger, with the car"): the city is an island at the origin; a causeway runs from its near shore (z 540) out to a
// pier end at z 1722; the GT3 RS parks there facing back at the island; the two moons eclipse the sun above the island.
// The wide shot is the same world from far up the same axis, so the pier shot pulls back into it without a cut.
// Colour rules: night blue vs amber; purple only the car; magenta only in the crash. Bloom only on real lights.
import * as THREE from 'three';
import { Water } from 'three/examples/jsm/objects/Water.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';

function rng(seed: number) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (x: number) => { x = clamp(x); return x * x * (3 - 2 * x); };
const ease = (x: number) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

export const SUN_EL = 14;                       // degrees above the horizon, straight up the causeway axis (-z)
export const PIER_Z = 1700;                     // where the car parks
export const CAR = { x: -0.7, y: 1.4, z: PIER_Z, yaw: Math.PI - 0.34 };

/** camera at hero time t (s): 0-5 the pier, 5-11 the pull-back, then the wide frame holds (the crash breaks that frame) */
export function heroCam(t: number) {
  const pier = { p: [3.5 - 0.1 * t / 5, 2.05, PIER_Z + 9.3 - 0.5 * t / 5], l: [-3.3, 3.9, PIER_Z - 27.5], fov: 38 };
  const wide = { p: [34, 20, 1840], l: [0, 62, 0], fov: 38 };
  const k = ease((t - 5) / 6);
  // rise first, then travel back: height leads so the car stays in frame while the island grows
  const kh = smooth(clamp(k * 1.25)), kz = k * k * (3 - 2 * k);
  const pp = pier.p; const P = [lerp(pp[0], wide.p[0], kz), lerp(pp[1], wide.p[1], kh), lerp(pp[2], wide.p[2], kz)];
  const Lk = [lerp(pier.l[0], wide.l[0], kz), lerp(pier.l[1], wide.l[1], kh), lerp(pier.l[2], wide.l[2], kz)];
  return { p: P, l: Lk, fov: lerp(pier.fov, wide.fov, k), k };
}

function makeNormals(N = 512) {
  const r = rng(11), h = new Float32Array(N * N), waves: number[][] = [];
  for (let i = 0; i < 46; i++) { let kx = Math.round((r() * 2 - 1) * 26), ky = Math.round((r() * 2 - 1) * 26); if (Math.abs(kx) + Math.abs(ky) < 3) { kx += 4; ky -= 3; }
    const k = Math.hypot(kx, ky); waves.push([kx, ky, r() * 6.283, 1 / Math.pow(k, 1.25)]); }
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { let s = 0; const u = x / N * 6.2832, v = y / N * 6.2832; for (const w of waves) s += w[3] * Math.sin(w[0] * u + w[1] * v + w[2]); h[y * N + x] = s; }
  const d = new Uint8Array(N * N * 4), S = 9;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const hx = h[y * N + (x + 1) % N] - h[y * N + (x + N - 1) % N], hy = h[((y + 1) % N) * N + x] - h[((y + N - 1) % N) * N + x];
    const nx = -hx * S, ny = -hy * S, nz = 1; const l = Math.hypot(nx, ny, nz); const i = (y * N + x) * 4; d[i] = (nx / l * .5 + .5) * 255; d[i + 1] = (ny / l * .5 + .5) * 255; d[i + 2] = (nz / l * .5 + .5) * 255; d[i + 3] = 255; }
  const t = new THREE.DataTexture(d, N, N, THREE.RGBAFormat); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter; t.generateMipmaps = true; t.anisotropy = 8; t.needsUpdate = true; return t;
}

const HASH = `float hash(vec2 p){vec3 p3=fract(vec3(p.xyx)*.1031);p3+=dot(p3,p3.yzx+33.33);return fract((p3.x+p3.y)*p3.z);}`;
const MAGENTA = `vec3 checker(vec2 p){float c=mod(floor(p.x)+floor(p.y),2.);return mix(vec3(.02,.0,.03),vec3(1.,0.,1.),c);}`;

export async function createWorld(canvas: HTMLCanvasElement, W: number, H: number, urls: { car: string; plate: string }, SS = 2) {
  const R = rng(7);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
  renderer.setPixelRatio(SS); renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, W / H, 0.3, 90000);
  const el = SUN_EL * Math.PI / 180;
  const sunDir = new THREE.Vector3(0, Math.sin(el), -Math.cos(el)).normalize();
  const sunPos = sunDir.clone().multiplyScalar(40000);
  const U = { crash: { value: 0 } };            // shared: 0 = the finished world, 1 = fully failed

  // ---- sky
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60000, 48, 24), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, uniforms: { sun: { value: sunDir } },
    vertexShader: `varying vec3 d;void main(){d=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader: `varying vec3 d;uniform vec3 sun;
    void main(){vec3 n=normalize(d);float h=max(n.y,0.);
      vec3 zen=vec3(.005,.010,.026),hor=vec3(.026,.047,.092);
      vec3 c=mix(hor,zen,pow(h,.42));
      float s=max(dot(n,normalize(sun)),0.);
      c+=vec3(.30,.27,.24)*pow(s,10.)*.03+vec3(.9,.7,.42)*pow(s,140.)*.08;
      c+=vec3(.02,.03,.05)*exp(-h*14.);
      if(n.y<0.)c=mix(hor,vec3(.01,.015,.03),min(-n.y*6.,1.));
      gl_FragColor=vec4(c,1.);}` }));
  sky.renderOrder = -10; scene.add(sky);
  { const N = 2600, pos = new Float32Array(N * 3), col = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) { const u = R(), v = R() * .96 + .04; const th = u * 6.2832, y = v, r = Math.sqrt(1 - y * y);
      pos.set([Math.cos(th) * r * 50000, y * 50000, Math.sin(th) * r * 50000], i * 3); const b = Math.pow(R(), 3) * 1.3 + .12; col.set([b, b, b * 1.08], i * 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const st = new THREE.Points(g, new THREE.PointsMaterial({ size: 1.15 * SS, sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false, fog: false, blending: THREE.AdditiveBlending }));
    st.renderOrder = -9; st.layers.set(1); camera.layers.enable(1); scene.add(st); }   // layer 1: the water mirror never sees the stars

  // ---- the eclipse: two moons in love, a white-gold ring. In the crash the right half is a wireframe fan ("sun.mat - not found")
  const corona = new THREE.Mesh(new THREE.PlaneGeometry(16500, 16500), new THREE.ShaderMaterial({ transparent: true, depthWrite: false, uniforms: { crash: U.crash },
    vertexShader: `varying vec2 u;void main(){u=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader: `varying vec2 u;uniform float crash;
    float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
    float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
    float fbm(vec2 p){float a=.5,s=0.;for(int i=0;i<5;i++){s+=a*noise(p);p*=2.03;a*=.5;}return s;}
    void main(){vec2 p=(u-.5)*2.;
      vec2 c1=vec2(-.034,.0),c2=vec2(.040,.012);float r1=.118,r2=.104;
      float d1=length(p-c1)-r1,d2=length(p-c2)-r2;float d=min(d1,d2);
      float ang=atan(p.y,p.x);
      bool broken=crash>.25&&p.x>.012;
      if(broken&&length(p)<.21){ // the missing material: a flat fan of spokes on near-black, hard edges
        float rr=length(p-vec2(.012,0.));float sp=abs(fract(ang*12./6.2832+.5)-.5)*rr*6.2832/12.;
        float line=max(smoothstep(.0022,.0008,sp),smoothstep(.0022,.0008,abs(rr-.15)));
        line=max(line,smoothstep(.0022,.0008,abs(p.x-.012)));
        gl_FragColor=vec4(mix(vec3(.02,.022,.035),vec3(.95),line*step(rr,.152)),step(rr,.152)+0.*d);if(rr>.152)discard;return;}
      if(d<0.){
        vec2 q=(d2<0.)?(p-c2)/r2:(p-c1)/r1;
        float z=sqrt(max(1.-dot(q,q),0.));
        float cr=fbm(q*5.+((d2<0.)?7.:1.));
        vec3 base=(d2<0.)?vec3(.020,.019,.022):vec3(.013,.016,.024);
        vec3 col=base*(.55+.9*cr)*(.35+.65*z);
        float rim=smoothstep(-.012,0.,d);col+=vec3(1.,.86,.62)*rim*.10;
        if(d2<0.&&d1<0.){float e=smoothstep(.006,0.,abs(d2));col+=vec3(.9,.8,.62)*e*.045;}
        gl_FragColor=vec4(col,1.);return;}
      float ring=exp(-pow(d/.0075,2.));
      float st=.72+.28*(fbm(vec2(ang*2.2,1.7))*1.6-.3)+.18*sin(ang*2.-.6);
      float glow=exp(-d/.030)*.95+.05/(1.+pow(d/.06,2.));
      float wide=exp(-d/.20)*.22;
      float fade=smoothstep(1.,.45,length(p));
      float live=broken?0.:1.;
      vec3 col=vec3(1.,.93,.80)*ring*4.2+vec3(1.,.82,.55)*glow*st*.85+vec3(.95,.72,.45)*wide*st*.16;
      float a=clamp(ring+glow*st+wide*.4,0.,1.)*fade*live;
      gl_FragColor=vec4(col*fade,a);}` }));
  corona.position.copy(sunPos); corona.renderOrder = -5; scene.add(corona);

  // ---- ocean: three's Water (true mirror) with its shading rewritten: no grey floor, a gold glitter path, waves at every scale
  const NT = makeNormals();
  const water = new Water(new THREE.PlaneGeometry(160000, 160000), { textureWidth: 2048, textureHeight: 2048, waterNormals: NT, sunDirection: sunDir.clone(), sunColor: 0xffe0a8, waterColor: 0x030812, distortionScale: 3.0, fog: false });
  water.material.uniforms.crash = U.crash;
  water.material.fragmentShader = water.material.fragmentShader
    .replace('uniform float time;', 'uniform float time;uniform float crash;\n' + MAGENTA)
    .replace(/vec4 getNoise\( vec2 uv \) \{[\s\S]*?return noise \* 0\.5 - 1\.0;\s*\}/,
      `vec4 getNoise( vec2 uv ) {
        vec4 n = texture2D( normalSampler, uv / 5.0 + vec2( time * .050, time * .031 ) ) * .55
               + texture2D( normalSampler, uv / 19.0 + vec2( -time * .017, time * .024 ) ) * .85
               + texture2D( normalSampler, uv / 83.0 + vec2( time * .006, -time * .004 ) )
               + texture2D( normalSampler, uv / 410.0 + vec2( -time * .0016, time * .0011 ) ) * .9
               + texture2D( normalSampler, uv / 2300.0 + vec2( time * .0004, time * .0003 ) ) * .7;
        return n * 0.5 - 1.0;
      }`)
    .replace('float rf0 = 0.3;', 'float rf0 = 0.05;')
    .replace('100.0, 2.0, 0.5', '160.0, 2.0, 0.5')
    .replace(/vec3 albedo = mix\([^;]*;/, 'vec3 albedo = mix( scatter*.5, reflectionSample*1.05, reflectance ) + specularLight*2.4*reflectance;')
    .replace('gl_FragColor = vec4( outgoingLight, alpha );',
      `// the crash: the ocean's texture goes missing from the right, in hard steps
       float edge = mix( 9000., -1900., crash );
       if ( crash > .01 && worldPosition.x > edge + floor( worldPosition.z / 260. ) * 55. ) { vec2 cp = worldPosition.xz / 120.; float fwc = max( fwidth( cp.x ), fwidth( cp.y ) ); outgoingLight = mix( checker( cp ) * 1.15, vec3( .5, 0., .5 ), smoothstep( .25, .7, fwc ) ); }
       gl_FragColor = vec4( outgoingLight, alpha );`);
  water.rotation.x = -Math.PI / 2; water.material.uniforms.size.value = 1; scene.add(water);

  // ---- the city (instanced boxes, the windows are drawn in the shader; integer seeds, or the hash dithers per pixel)
  const bList: any[] = [];
  const B = (x, z, w, d, h, y = 0, lit = .2) => bList.push({ x, z, w, d, h, y, lit, seed: Math.floor(R() * 100) });
  const tower = (x, z, w, d, h, lit) => { B(x, z, w, d, h, 0, lit); const r = R();
    if (r < .55 && h > 40) { B(x, z, w * .72, d * .72, h * .16, h, lit); if (r < .2) B(x, z, w * .12, d * .12, h * .22, h * 1.16, 0); }
    else if (r < .75) B(x + w * .2, z, w * .3, d * .4, 5, h, 0); };
  for (let i = 0; i < 640; i++) { const a = R() * 6.2832, r = Math.sqrt(R()) * 640; const x = Math.cos(a) * r * 1.45, z = Math.sin(a) * r * .8;
    if (Math.abs(x) < 9 && z > 300) continue;                                   // the avenue the causeway lands on stays open
    const cen = Math.exp(-(r * r) / (2 * 250 * 250)); const w = 26 + R() * 30; const h = (12 + Math.pow(R(), 1.5) * 150 * cen + cen * 38) * (.75 + R() * .5); tower(x, z, w, 22 + R() * 30, h, .07 + R() * .2); }
  tower(-60, -20, 54, 54, 345, .3); tower(70, 30, 46, 46, 255, .26); tower(-190, 40, 40, 40, 205, .24); tower(215, -10, 42, 42, 180, .24);
  const cityMat = new THREE.ShaderMaterial({ uniforms: { fogC: { value: new THREE.Color(0x0d1627) }, fogK: { value: .00007 }, sun: { value: sunDir }, crash: U.crash },
    vertexShader: `attribute vec3 aS;attribute vec2 aD;varying vec3 L;varying vec3 N;varying vec2 D;varying vec3 Wp;varying vec3 S;
      void main(){L=position*aS;N=normal;D=aD;S=aS;vec4 w=modelMatrix*instanceMatrix*vec4(position,1.);Wp=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;}`,
    fragmentShader: `varying vec3 L;varying vec3 N;varying vec2 D;varying vec3 Wp;varying vec3 S;uniform vec3 fogC;uniform float fogK;uniform vec3 sun;uniform float crash;
      ${HASH}${MAGENTA}
      void main(){vec3 col;float dist=length(Wp-cameraPosition);float sd=floor(D.x+.5);
        float face=abs(N.x)>.5?1.:abs(N.z)>.5?2.:0.;
        // the crash, building by building: a third lose their texture (magenta checker), a third fall back to wireframe
        float fail=hash(vec2(sd,7.)+floor(Wp.xz/900.));
        if(crash>fail*.9+.05){
          vec2 f2=face<.5?L.xz:(face<1.5?vec2(L.z,L.y):vec2(L.x,L.y));
          if(fract(sd/3.)<.4){vec2 cq=f2/14.;float fq=max(fwidth(cq.x),fwidth(cq.y));gl_FragColor=vec4(mix(checker(cq)*1.1,vec3(.5,0.,.5),smoothstep(.25,.7,fq)),1.);return;}
          vec2 sz=face<.5?S.xz:(face<1.5?S.zy:S.xy);vec2 q=f2/sz+(face<.5?vec2(.5):vec2(.5,0.));
          float px=max(fwidth(q.x),fwidth(q.y))*1.4;
          float e=min(min(q.x,1.-q.x),min(q.y,1.-q.y));float dg=min(abs(q.x-q.y),abs(q.x+q.y-1.))*.7;
          float line=max(smoothstep(px,0.,e),smoothstep(px,0.,dg))*(1.-smoothstep(.10,.30,px)*.75);
          gl_FragColor=vec4(mix(vec3(.02,.024,.04),vec3(.92),line),1.);return;}
        vec3 base=vec3(.012,.020,.040)*(1.+.25*(hash(vec2(sd,3.))-.5));
        float ndl=max(dot(N,normalize(vec3(-.35,.5,.8))),0.);
        base*=.75+.55*ndl;base+=vec3(.10,.075,.045)*max(dot(N,sun),0.)*.6;
        if(face<.5){col=base*1.25+vec3(.012,.016,.026);}
        else{
          vec2 f=face<1.5?vec2(L.z+S.z*.5,L.y):vec2(L.x+S.x*.5,L.y);
          vec2 cell=vec2(3.4,3.7);vec2 g=f/cell;vec2 id=floor(g);vec2 q=fract(g);
          float topm=step(L.y,S.y-1.2)*step(1.6,L.y);
          float edge=step(.6,f.x)*step(f.x,(face<1.5?S.z:S.x)-.6);
          vec2 fw=fwidth(g);float aa=clamp(max(fw.x,fw.y)*1.2,0.,.2);
          float win=smoothstep(.20-aa,.20+aa,q.x)*smoothstep(.80+aa,.80-aa,q.x)*smoothstep(.26-aa,.26+aa,q.y)*smoothstep(.76+aa,.76-aa,q.y)*topm*edge;
          float hh=hash(id+sd*vec2(17.,3.)+face*31.);float on=step(1.-D.y,hh);
          float h2=hash(id+vec2(sd*7.+face*5.,91.));float h3=hash(id+vec2(13.,sd*3.+face));
          vec3 wc=mix(vec3(1.,.66,.27),vec3(.80,.90,1.)*.5,step(.95,h2));wc=mix(wc,vec3(1.,.58,.22),step(h2,.25));
          col=mix(base,base*1.35+.004*h3,win);col+=win*on*wc*mix(.45,1.7,h3*h3);
        }
        float fg=1.-exp(-dist*fogK);col=mix(col,fogC,fg*.92);
        gl_FragColor=vec4(col,1.);}` });
  { const n = bList.length, geo = new THREE.BoxGeometry(1, 1, 1); geo.translate(0, .5, 0);
    const aS = new Float32Array(n * 3), aD = new Float32Array(n * 2); const m = new THREE.InstancedMesh(geo, cityMat, n), o = new THREE.Object3D();
    bList.forEach((b, i) => { o.position.set(b.x, b.y, b.z); o.scale.set(b.w, b.h, b.d); o.updateMatrix(); m.setMatrixAt(i, o.matrix); aS.set([b.w, b.h, b.d], i * 3); aD.set([b.seed, b.lit], i * 2); });
    geo.setAttribute('aS', new THREE.InstancedBufferAttribute(aS, 3)); geo.setAttribute('aD', new THREE.InstancedBufferAttribute(aD, 2)); m.frustumCulled = false; scene.add(m); }
  const dark = new THREE.MeshBasicMaterial({ color: 0x070b14 });
  const land = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 96), dark); land.scale.set(960, .3, 560); land.position.y = .2; scene.add(land);
  const dots = (pts: number[][], color: number, size: number, k: number) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pts.flat()), 3));
    const p = new THREE.Points(g, new THREE.PointsMaterial({ size: size * SS, sizeAttenuation: false, color: new THREE.Color(color).multiplyScalar(k), depthWrite: false })); scene.add(p); return p; };
  { const pts: number[][] = []; for (let i = 0; i < 300; i++) { const a = i / 300 * 6.2832; const j = 1 + .012 * Math.sin(a * 9.) + .01 * Math.sin(a * 23.); pts.push([Math.cos(a) * 948 * j, 3, Math.sin(a) * 552 * j]); } dots(pts, 0xffd9a0, 1.5, 2.4); }

  // ---- the causeway and the pier: one deck, 8.4 m wide, low warm lights down both edges (a line of light to the island)
  const Z0 = 545, Z1 = PIER_Z + 22, LEN = Z1 - Z0;
  { const cv = document.createElement('canvas'); cv.width = 512; cv.height = 512; const x = cv.getContext('2d')!; x.fillStyle = '#232a36'; x.fillRect(0, 0, 512, 512);
    const pr = rng(5); for (let i = 0; i < 16; i++) { const v = 28 + pr() * 16 | 0; x.fillStyle = `rgb(${v + 4},${v + 8},${v + 18})`; x.fillRect(0, i * 32, 512, 30); x.fillStyle = 'rgba(0,0,0,.55)'; x.fillRect(0, i * 32 + 30, 512, 2); }
    const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(1, LEN / 5); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 16;
    const deck = new THREE.Mesh(new THREE.BoxGeometry(8.4, .3, LEN), new THREE.MeshStandardMaterial({ map: t, roughness: .5, metalness: 0, envMapIntensity: 1 })); deck.position.set(0, 1.25, (Z0 + Z1) / 2); scene.add(deck);
    const postM = new THREE.MeshStandardMaterial({ color: 0x0b0f18, roughness: .7 });
    const zs: number[] = []; for (let z = Z0 + 4; z <= PIER_Z - 12; z += 8.5) zs.push(z);
    const posts = new THREE.InstancedMesh(new THREE.CylinderGeometry(.16, .2, 3.4, 10), postM, zs.length * 2);
    const bulbs = new THREE.InstancedMesh(new THREE.CylinderGeometry(.19, .19, .12, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffd29a).multiplyScalar(2.2) }), zs.length * 2);
    const o = new THREE.Object3D(); let i = 0; const far: number[][] = [];
    for (const z of zs) for (const sx of [-1, 1]) { o.position.set(sx * 4.05, .4, z); o.updateMatrix(); posts.setMatrixAt(i, o.matrix); o.position.set(sx * 4.05, 2.16, z); o.updateMatrix(); bulbs.setMatrixAt(i, o.matrix); i++; far.push([sx * 4.05, 2.3, z]); }
    scene.add(posts, bulbs); dots(far, 0xffd29a, 1.1, 1.6);                         // the same lamps as points, so the line still reads from far away
    for (const z of [PIER_Z - 14, PIER_Z - 22.5, PIER_Z - 31]) for (const sx of [-1, 1]) { const L = new THREE.PointLight(0xffc98a, .5, 7, 1.8); L.position.set(sx * 3.7, 2.3, z); scene.add(L); } }

  // ---- image-based light for the paint: the night sky, the eclipse and two soft sources near the car
  { const s = new THREE.Scene(); s.add(sky.clone()); const c = corona.clone(); c.lookAt(0, 2, PIER_Z); s.add(c);
    for (const e of [{ p: [-9, 7, PIER_Z + 22], r: 3.2, c: 0xffd0a0, k: 5 }, { p: [10, 6, PIER_Z + 26], r: 3, c: 0x9fc0ff, k: 2.2 }, { p: [4, 5, PIER_Z - 18], r: 1, c: 0xffd29a, k: 6 }, { p: [-4, 5, PIER_Z - 18], r: 1, c: 0xffd29a, k: 6 }]) {
      const m = new THREE.Mesh(new THREE.SphereGeometry(e.r, 16, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(e.c).multiplyScalar(e.k) })); m.position.set(e.p[0], e.p[1], e.p[2]); s.add(m); }
    const pm = new THREE.PMREMGenerator(renderer); const cc = new THREE.CubeCamera(1, 90000, new THREE.WebGLCubeRenderTarget(512, { type: THREE.HalfFloatType }));
    cc.position.set(0, 2, PIER_Z); cc.update(renderer, s); scene.environment = pm.fromCubemap(cc.renderTarget.texture).texture; }

  // ---- the GT3 RS: Ultraviolet, YELLOW calipers, tail lights on, the DKWHEEL plate in a plain satin frame (rear only, as in Asking for a Friend)
  const gltf = await new GLTFLoader().loadAsync(urls.car); const car = gltf.scene;
  car.traverse((o: any) => { if (!o.isMesh) return; const ms = Array.isArray(o.material) ? o.material : [o.material];
    ms.forEach((m: any) => { const n = (m.name || '').toLowerCase();
      if (n.includes('caliper')) { m.color.set(0xffd21f); m.emissive = new THREE.Color(0xffd21f); m.emissiveIntensity = .35; m.roughness = .4; m.metalness = .1; }
      if (n === 'paint' || n.includes('body_paint')) { m.color.set(0x7a2fb8); m.metalness = .5; m.roughness = .34; m.clearcoat = 1; m.clearcoatRoughness = .06; m.envMapIntensity = 1.5; }
      if (n === 'rim') { m.color.set(0xc9ccd2); m.metalness = .9; m.roughness = .3; }
      if (m.userData && m.userData.lamp_color && n.includes('taillight') && n.includes('lens')) { const lc = m.userData.lamp_color; m.emissive.setRGB(lc[0], lc[1], lc[2]); m.emissiveIntensity = 2.2; }
      if (m.userData && m.userData.lamp_color && (n.includes('headlight') || n.includes('frontlamp'))) { m.emissive.setRGB(1, .95, .86); m.emissiveIntensity = n.includes('glass') ? 1.2 : 4; } }); });
  { const tex = await new THREE.TextureLoader().loadAsync(urls.plate); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 16;
    const pw = .305, ph = pw * 340 / 1160 * 1.72;     // a US plate is 12 x 6 in; the artwork is drawn wider, so it is fitted to plate height
    const g = new THREE.Group(); const plate = new THREE.Mesh(new THREE.PlaneGeometry(pw, ph), new THREE.MeshStandardMaterial({ map: tex, roughness: .55, metalness: 0, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: .10 }));
    g.add(plate); const fm = new THREE.MeshStandardMaterial({ color: 0x050506, roughness: .35, metalness: .6 }); const bw = .012, bb = .022, d = .012;
    const bar = (w, h, x, y) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), fm); m.position.set(x, y, 0); g.add(m); };
    bar(pw + 2 * bw, bw, 0, ph / 2 + bw / 2); bar(pw + 2 * bw, bb, 0, -ph / 2 - bb / 2); bar(bw, ph, -pw / 2 - bw / 2, 0); bar(bw, ph, pw / 2 + bw / 2, 0);
    g.position.set(0, .45, -2.275); g.rotation.y = Math.PI; g.name = 'plate'; car.add(g); }   // glTF: the car faces +Z, so its tail is at -Z
  car.position.set(CAR.x, CAR.y, CAR.z); car.rotation.y = CAR.yaw; scene.add(car);
  const tgt = new THREE.Vector3(CAR.x, CAR.y + .2, CAR.z);
  const key = new THREE.SpotLight(0xffd9c8, 240, 60, .5, .8, 1.6); key.position.set(-10, 9, PIER_Z + 5.5); key.target.position.copy(tgt); scene.add(key, key.target);
  const fill = new THREE.SpotLight(0xc9b8ff, 46, 60, .6, .9, 1.6); fill.position.set(8, 4, PIER_Z + 9.5); fill.target.position.copy(tgt); scene.add(fill, fill.target);
  const back = new THREE.DirectionalLight(0xffe2b0, .13); back.position.copy(sunDir).multiplyScalar(100); scene.add(back);
  scene.add(new THREE.HemisphereLight(0x25365c, 0x05070c, .9));
  // headlights on: a warm pool on the deck ahead of the car, pointing down the causeway at the city (and it marks the car from far away)
  { const fw = new THREE.Vector3(Math.sin(CAR.yaw), 0, Math.cos(CAR.yaw)); const hl = new THREE.SpotLight(0xfff0d8, 420, 70, .36, .75, 1.5);
    hl.position.set(CAR.x, CAR.y + .65, CAR.z).addScaledVector(fw, 2.2); hl.target.position.set(CAR.x, CAR.y - .2, CAR.z).addScaledVector(fw, 26); scene.add(hl, hl.target);
    dots([[CAR.x, CAR.y + 1.0, CAR.z]], 0x9a4dff, 2.2, 2.6); }

  // ---- post: restrained bloom on real lights only
  const rt = new THREE.WebGLRenderTarget(W * SS, H * SS, { type: THREE.HalfFloatType, samples: 4 });
  const comp = new EffectComposer(renderer, rt); comp.setPixelRatio(1); comp.setSize(W * SS, H * SS);
  comp.addPass(new RenderPass(scene, camera)); const bloom = new UnrealBloomPass(new THREE.Vector2(W * SS, H * SS), .2, .55, 1.0); comp.addPass(bloom); comp.addPass(new OutputPass());

  const V = new THREE.Vector3();
  const project = (x: number, y: number, z: number) => { V.set(x, y, z).project(camera); return [(V.x * .5 + .5) * W, (-V.y * .5 + .5) * H, V.z]; };
  return {
    /** draw the world at hero time t; crash 0..1 */
    render(t: number, crash = 0) {
      const c = heroCam(t); camera.position.set(c.p[0], c.p[1], c.p[2]); camera.fov = c.fov; camera.updateProjectionMatrix(); camera.lookAt(c.l[0], c.l[1], c.l[2]);
      U.crash.value = crash; water.material.uniforms.time.value = 4.2 + (crash > 0 ? 11.0 : t) * 1.0;      // the crash freezes the water
      corona.lookAt(camera.position); bloom.strength = crash > .5 ? .08 : .2;
      comp.render();
      return { sun: project(sunPos.x, sunPos.y, sunPos.z), car: project(CAR.x, CAR.y + .6, CAR.z) };
    },
    project,
  };
}
