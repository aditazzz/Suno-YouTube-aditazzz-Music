// @ts-nocheck
// THE WORLD (Fable, Nov 10): one real 3D world for verse 2 through the crash ("Bigger, with the car"). Plain three.js.
// createWorld() builds it once; render(S) draws any moment from a state object S (./film.ts makes S from film time).
// Nothing here reads a clock or Math.random: every frame is a pure function of S.
// Geography: the city is an island at the origin with the pink dot as its central roundabout; an avenue runs south (+z) from
// the dot to the shore (z 545); the causeway continues to the pier end (z 1722), where the car parks facing back at the city.
// Colour rules: night blue vs amber; pink only the dot; purple only the car; magenta only in the crash. Bloom on real lights only.
import * as THREE from 'three';
import { Water } from 'three/examples/jsm/objects/Water.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';

export function rng(seed: number) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
export const SUN_EL = 14, PIER_Z = 1700, SHORE_Z = 545, AVE_X = -3.4, GROUND_Y = 0.36, DECK_Y = 1.4;
export const QUAD = 16500, QDIST = 40000;       // the sky quad the sun and moons live on (its centre is the eclipse spot)

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
const WATER_NOISE = `vec4 getNoise( vec2 uv ) {
  vec4 n = texture2D( normalSampler, uv / 5.0 + vec2( time * .050, time * .031 ) ) * .55
         + texture2D( normalSampler, uv / 19.0 + vec2( -time * .017, time * .024 ) ) * .85
         + texture2D( normalSampler, uv / 83.0 + vec2( time * .006, -time * .004 ) )
         + texture2D( normalSampler, uv / 410.0 + vec2( -time * .0016, time * .0011 ) ) * .9
         + texture2D( normalSampler, uv / 2300.0 + vec2( time * .0004, time * .0003 ) ) * .7;
  return n * 0.5 - 1.0; }`;

export async function createWorld(canvas: HTMLCanvasElement, W: number, H: number, urls: { car: string; plate: string }, SS = 2) {
  const R = rng(7);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
  renderer.setPixelRatio(SS); renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, W / H, 0.3, 90000);
  const el = SUN_EL * Math.PI / 180;
  const sunDir0 = new THREE.Vector3(0, Math.sin(el), -Math.cos(el)).normalize();
  const sunPos = sunDir0.clone().multiplyScalar(QDIST);
  const U = { crash: { value: 0 }, uT: { value: 0 }, grow: { value: 1 }, bounce: { value: 0 }, env: { value: 0 }, tower: { value: 1 }, guys: { value: 0 }, wired: { value: 0 },
    lit: { value: 1 }, clap: { value: 0 }, sunDir: { value: sunDir0.clone() }, dusk: { value: 0 }, tot: { value: 1 },
    hk: { value: 1 }, fuse: { value: 9 }, gwave: { value: 0 }, clapX: { value: 0 }, love: { value: 0 }, flash: { value: 0 }, sq: { value: 0 }, lift: { value: 0 }, flip: { value: 0 }, eq: { value: 0 }, kr: { value: new THREE.Vector4(9, 9, 9, 9) }, kamp: { value: 0 }, look: { value: 0 }, drain: { value: 0 },
    sun: { value: new THREE.Vector3(0, 0, 1) }, m1: { value: new THREE.Vector4(-.034, 0, .118, 1) }, m2: { value: new THREE.Vector4(.040, .012, .104, 1) }, weird: { value: 0 } };

  // ---- sky
  let STARS: any = null;
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60000, 48, 24), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, uniforms: { sun: U.sunDir, dusk: U.dusk, tot: U.tot, flash: U.flash },
    vertexShader: `varying vec3 d;void main(){d=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader: `varying vec3 d;uniform vec3 sun;uniform float dusk;uniform float tot;uniform float flash;
    void main(){vec3 n=normalize(d);float h=max(n.y,0.);
      vec3 zen=vec3(.005,.010,.026),hor=vec3(.026,.047,.092);
      vec3 c=mix(hor,zen,pow(h,.42));
      float s=max(dot(n,normalize(sun)),0.);
      c+=tot*(vec3(.30,.27,.24)*pow(s,10.)*.03+vec3(.9,.7,.42)*pow(s,140.)*.08);
      // dusk: while the sun is uncovered the sky around it warms (never daylight: the film stays a blue night)
      c+=dusk*(vec3(.30,.19,.09)*pow(s,9.)*.42*exp(-h*6.)+vec3(.012,.030,.075)*.6+vec3(.5,.32,.15)*pow(s,70.)*.3);
      c+=vec3(.02,.03,.05)*exp(-h*14.);
      c+=flash*vec3(.55,.68,1.)*smoothstep(.15,-.5,n.x)*(.35+.65*exp(-h*2.5));   // the storm lives on the left only
      if(n.y<0.)c=mix(hor,vec3(.01,.015,.03),min(-n.y*6.,1.));
      gl_FragColor=vec4(c,1.);}` }));
  sky.renderOrder = -10; scene.add(sky);
  { const N = 2600, pos = new Float32Array(N * 3), col = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) { const u = R(), v = R() * .96 + .04; const th = u * 6.2832, y = v, r = Math.sqrt(1 - y * y);
      pos.set([Math.cos(th) * r * 50000, y * 50000, Math.sin(th) * r * 50000], i * 3); const b = Math.pow(R(), 3) * 1.3 + .12; col.set([b, b, b * 1.08], i * 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const st = new THREE.Points(g, new THREE.PointsMaterial({ size: 1.15 * SS, sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false, fog: false, blending: THREE.AdditiveBlending }));
    st.renderOrder = -9; st.layers.set(1); camera.layers.enable(1); scene.add(st); STARS = st; }

  // (STARS is assigned where the star field is built)
  // ---- the sun and the two moons, on one sky quad. tot 0: a small warm sun and two lit moons; tot 1: the eclipse ring.
  const corona = new THREE.Mesh(new THREE.PlaneGeometry(QUAD, QUAD), new THREE.ShaderMaterial({ transparent: true, depthWrite: false,
    uniforms: { crash: U.crash, sunP: U.sun, m1: U.m1, m2: U.m2, tot: U.tot, weird: U.weird, love: U.love, sq: U.sq, uT: U.uT },
    vertexShader: `varying vec2 u;void main(){u=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader: `varying vec2 u;uniform float crash;uniform vec3 sunP;uniform vec4 m1;uniform vec4 m2;uniform float tot;uniform float weird;uniform float love;uniform float sq;uniform float uT;
    float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
    float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
    float fbm(vec2 p){float a=.5,s=0.;for(int i=0;i<5;i++){s+=a*noise(p);p*=2.03;a*=.5;}return s;}
    float moonD(vec2 p,vec4 m){vec2 q=p-m.xy;q.x/=(1.+weird*.55);q.y*=(1.+weird*.55);float r=mix(length(q),max(abs(q.x),abs(q.y))*1.08,sq);return m.w>.5?r-m.z:9.;}
    vec3 moonCol(vec2 p,vec4 m,float id,float d){vec2 q=(p-m.xy)/m.z;float z=sqrt(max(1.-dot(q,q),0.));vec3 n=vec3(q,z);
      float cr=fbm(q*5.+id);
      vec2 ls=sunP.xy-m.xy;vec3 L=normalize(vec3(ls*6.,.55));            // lit from wherever the sun is on the quad
      float lam=max(dot(n,L),0.);
      vec3 tone=id<3.?vec3(.62,.70,.86):vec3(.90,.80,.66);             // one cool moon, one warm moon
      tone=mix(tone,vec3(1.25,.92,.42),love*(.55+.45*smoothstep(.2,-.5,q.y)));   // in love they blush gold, cheeks first
      vec3 day=tone*(.10+.95*lam)*(.55+.6*cr)*sunP.z;
      vec3 night=((id<3.)?vec3(.013,.016,.024):vec3(.020,.019,.022))*(.55+.9*cr)*(.35+.65*z)+vec3(1.,.86,.62)*smoothstep(-.012,0.,d)*.10;
      return mix(day+night*.6,night,tot);}
    void main(){vec2 p=(u-.5)*2.;
      float d1=moonD(p,m1),d2=moonD(p,m2);float d=min(d1,d2);
      float ang=atan(p.y-sunP.y,p.x-sunP.x);
      bool broken=crash>.25&&p.x>.012;
      if(broken&&length(p)<.21){
        float rr=length(p-vec2(.012,0.));float sp=abs(fract(ang*12./6.2832+.5)-.5)*rr*6.2832/12.;
        float line=max(smoothstep(.0022,.0008,sp),smoothstep(.0022,.0008,abs(rr-.15)));
        line=max(line,smoothstep(.0022,.0008,abs(p.x-.012)));
        if(rr>.152)discard;gl_FragColor=vec4(mix(vec3(.02,.022,.035),vec3(.95),line),1.);return;}
      if(d<0.){vec3 col=(d2<0.)?moonCol(p,m2,7.,d2):moonCol(p,m1,1.,d1);
        if(d2<0.&&d1<0.){float e=smoothstep(.006,0.,abs(d2));col+=vec3(.9,.8,.62)*e*.045;}
        gl_FragColor=vec4(col,1.);return;}
      float live=broken?0.:1.;
      // the uncovered sun: a small warm disc with a soft halo
      float ds=length(p-sunP.xy)-.060;
      float disc=smoothstep(.004,-.004,ds);float halo=exp(-max(ds,0.)/.05)*.55+exp(-max(ds,0.)/.22)*.16;
      vec3 sunCol=(vec3(1.,.90,.70)*disc*5.+vec3(1.,.70,.40)*halo)*sunP.z;float sunA=clamp(disc+halo,0.,1.)*sunP.z;
      // totality: the ring hugs the two moons
      float ring=exp(-pow(d/.0075,2.));
      float st=.72+.28*(fbm(vec2(ang*2.2,1.7))*1.6-.3)+.18*sin(ang*2.-.6);
      float glow=exp(-d/.030)*.95+.05/(1.+pow(d/.06,2.));
      float wide=exp(-d/.20)*.22;
      vec3 totCol=vec3(1.,.93,.80)*ring*4.2+vec3(1.,.82,.55)*glow*st*.85+vec3(.95,.72,.45)*wide*st*.16;float totA=clamp(ring+glow*st+wide*.4,0.,1.);
      float fade=smoothstep(1.,.45,length(p));
      vec3 col=mix(sunCol,totCol*fade,tot);float a=mix(sunA,totA*fade,tot)*live;
      if(love>.001){vec3 hs=vec3(0.);vec2 hc=vec2(-.005,-.03),prev=vec2(0.);                       // a constellation: 28 stars and the lines between them
        for(int i=0;i<=28;i++){float tt=float(i)/28.*6.28318;float sx=sin(tt);
          vec2 h=vec2(16.*sx*sx*sx,13.*cos(tt)-5.*cos(2.*tt)-2.*cos(3.*tt)-cos(4.*tt))/17.;vec2 pt=hc+h*.31;float on=smoothstep(float(i),float(i)+1.5,love*31.);
          if(i>0){vec2 pa=p-prev,ba=pt-prev;float hh=clamp(dot(pa,ba)/dot(ba,ba),0.,1.);hs+=vec3(1.,.88,.62)*smoothstep(.0030,.0008,length(pa-ba*hh))*.20*on;}
          float tw=.62+.38*sin(uT*7.+float(i)*2.4);float dd=length(p-pt);
          hs+=vec3(1.,.94,.80)*(smoothstep(.010,.003,dd)*1.7+exp(-dd/.016)*.30)*tw*on;prev=pt;}
        float ha=clamp(max(hs.r,max(hs.g,hs.b)),0.,1.);float a2=a+ha*(1.-a);col=(col*a+hs*(1.-a))/max(a2,.001);a=a2;}
      gl_FragColor=vec4(col,a);}` }));
  corona.position.copy(sunPos); corona.renderOrder = -5; scene.add(corona);

  // ---- ocean (three's Water, shading rewritten) + the dry seabed for "Make the ocean disappear"
  const NT = makeNormals();
  const patchWater = (w: any, rf0: number, spec: number, crashable: boolean) => {
    w.material.uniforms.crash = U.crash; w.material.uniforms.love = U.love; w.material.uniforms.drain = U.drain; w.material.uniforms.kr = U.kr; w.material.uniforms.kamp = U.kamp; w.material.uniforms.uT = U.uT;
    w.material.fragmentShader = w.material.fragmentShader.replace('uniform float time;', 'uniform float time;uniform float crash;uniform float love;uniform float uT;uniform float drain;uniform vec4 kr;uniform float kamp;\n' + MAGENTA)
      .replace(/vec4 getNoise\( vec2 uv \) \{[\s\S]*?return noise \* 0\.5 - 1\.0;\s*\}/, WATER_NOISE)
      .replace('float rf0 = 0.3;', 'float rf0 = ' + rf0.toFixed(3) + ';').replace('100.0, 2.0, 0.5', '160.0, 2.0, 0.5')
      .replace(/vec3 albedo = mix\([^;]*;/, 'vec3 albedo = mix( scatter*.5, reflectionSample*1.05, reflectance ) + specularLight*' + spec.toFixed(2) + '*reflectance;')
      .replace('gl_FragColor = vec4( outgoingLight, alpha );', (crashable ? `float edge = mix( 9000., -1900., crash );
        if ( crash > .01 && worldPosition.x > edge + floor( worldPosition.z / 260. ) * 55. ) { vec2 cp = worldPosition.xz / 120.; float fwc = max( fwidth( cp.x ), fwidth( cp.y ) ); outgoingLight = mix( checker( cp ) * 1.15, vec3( .5, 0., .5 ), smoothstep( .25, .7, fwc ) ); }` : '') + `
 if ( kamp > .001 ) { float rr = length( worldPosition.xz ); float ring = 0.;                                   // louder: every kick sends a ring out across the sea
   for ( int i = 0; i < 4; i ++ ) { float age = kr[ i ]; float R = 640. + age * 1500.; ring += smoothstep( 34. + age * 30., 0., abs( rr - R ) ) * exp( - age * 1.5 ) * step( 0., age ) * step( age, 3. ); }
   outgoingLight += vec3( .70, .84, 1. ) * ring * kamp * 1.1; }
 if ( drain > .001 ) { vec2 dp = worldPosition.xz - vec2( -150., 1060. ); float dr = length( dp ); float da = atan( dp.y, dp.x );
   float arm = sin( da * 3. + log( dr + 1. ) * 7. - uT * 4.2 ); float fall = smoothstep( 900., 60., dr );
   outgoingLight = mix( outgoingLight, outgoingLight * .25 + vec3( .75, .86, 1. ) * smoothstep( .35, .95, arm ) * .55, drain * fall * .85 );
   outgoingLight *= 1. - drain * smoothstep( 110., 20., dr ); }
 if ( love > .001 ) { vec2 hp = ( mirrorCoord.xy / mirrorCoord.w - vec2( .5, .25 ) ) / vec2( .0844, .15 ); float hx = abs( hp.x );   // drawn in screen space so it is a true heart from this camera
   float hd = pow( hx * hx + hp.y * hp.y - 1., 3. ) - hx * hx * hp.y * hp.y * hp.y;                                   // the heart curve
   float hm = smoothstep( .03, -.08, hd ); float sp = .55 + .45 * sin( worldPosition.x * .9 + uT * 9. ) * sin( worldPosition.z * .7 - uT * 7. );
   float rim = smoothstep( .16, 0., abs( hd ) );
   outgoingLight += love * ( vec3( 1., .58, .15 ) * hm * ( .30 + .45 * sp ) + 0. * rim ); }
 gl_FragColor = vec4( outgoingLight, alpha );`);
    w.rotation.x = -Math.PI / 2; w.material.uniforms.size.value = 1; };
  const water = new Water(new THREE.PlaneGeometry(160000, 160000), { textureWidth: 2048, textureHeight: 2048, waterNormals: NT, sunDirection: sunDir0.clone(), sunColor: 0xffe0a8, waterColor: 0x030812, distortionScale: 3.0, fog: false });
  patchWater(water, .05, 2.4, true); scene.add(water);
  const seabed = new THREE.Mesh(new THREE.PlaneGeometry(40000, 40000), new THREE.ShaderMaterial({ vertexShader: `varying vec3 w;void main(){vec4 p=modelMatrix*vec4(position,1.);w=p.xyz;gl_Position=projectionMatrix*viewMatrix*p;}`,
    fragmentShader: `varying vec3 w;void main(){vec2 g=w.xz/60.;vec2 f=abs(fract(g)-.5);vec2 fw=fwidth(g);float l=max(smoothstep(fw.x*1.5,0.,f.x),smoothstep(fw.y*1.5,0.,f.y));
      float fd=exp(-length(w.xz-cameraPosition.xz)/2600.);float a=1.-smoothstep(.2,.6,max(fw.x,fw.y));
      vec3 c=vec3(.012,.018,.034)+vec3(.10,.16,.28)*l*a*fd*.8;gl_FragColor=vec4(c,1.);}` }));
  seabed.rotation.x = -Math.PI / 2; seabed.position.y = -46; seabed.visible = false; scene.add(seabed);
  // the wet left lane of the avenue: a second small mirror, only while the street is in view
  const wet = new Water(new THREE.PlaneGeometry(13, 500), { textureWidth: 1024, textureHeight: 1024, waterNormals: NT, sunDirection: new THREE.Vector3(0, 1, 0), sunColor: 0x000000, waterColor: 0x04070d, distortionScale: .05, fog: false });
  patchWater(wet, .12, 0, false); wet.position.set(-6.5, GROUND_Y + .03, 295); wet.visible = false; scene.add(wet);

  // ---- the city
  const bList: any[] = [];
  const B = (x, z, w, d, h, y = 0, lit = .2, tw = 0) => bList.push({ x, z, w, d, h, y, lit, tw, seed: Math.floor(R() * 100) });
  const tower = (x, z, w, d, h, lit) => { B(x, z, w, d, h, 0, lit); const r = R();
    if (r < .55 && h > 40) { B(x, z, w * .72, d * .72, h * .16, h, lit); if (r < .2) B(x, z, w * .12, d * .12, h * .22, h * 1.16, 0); }
    else if (r < .75) B(x + w * .2, z, w * .3, d * .4, 5, h, 0); };
  for (let i = 0; i < 640; i++) { const a = R() * 6.2832, r = Math.sqrt(R()) * 640; const x = Math.cos(a) * r * 1.45, z = Math.sin(a) * r * .8;
    const w = 26 + R() * 30, dd = 22 + R() * 30;
    if (Math.abs(x) < 60 + w / 2 && z > -70 - dd / 2) continue;                       // keep the avenue and the roundabout clear
    if (Math.hypot(x, z) < 70 + w / 2) continue;
    const cen = Math.exp(-(r * r) / (2 * 250 * 250)); const h = (12 + Math.pow(R(), 1.5) * 150 * cen + cen * 38) * (.75 + R() * .5); tower(x, z, w, dd, h, .07 + R() * .2); }
  for (const sx of [-1, 1]) for (let row = 0; row < 2; row++) { let z = 34; while (z < SHORE_Z - 22) { const d = 18 + R() * 18, w = 20 + R() * 12; const h = row === 0 ? 26 + R() * 64 : 50 + R() * 90;
    tower(sx * (13.5 + w / 2 + row * 38), z + d / 2, w, d, h * (1 - .45 * Math.max(0, (z - 330) / 215)), .10 + R() * .2); z += d + (R() < .16 ? 14 : 3); } }
  B(-64, -52, 54, 54, 345, 0, .3, 1);                                                // THE tower (it grows with the bass)
  tower(74, -40, 46, 46, 255, .26); tower(-190, 40, 40, 40, 205, .24); tower(215, -10, 42, 42, 180, .24);
  const cityMat = new THREE.ShaderMaterial({ uniforms: { fogC: { value: new THREE.Color(0x0d1627) }, fogK: { value: .00007 }, sun: U.sunDir, crash: U.crash, uT: U.uT, grow: U.grow, bounce: U.bounce, env: U.env, tower: U.tower, guys: U.guys, wired: U.wired, lit: U.lit, clap: U.clap, hk: U.hk, fuse: U.fuse, gwave: U.gwave, clapX: U.clapX, flash: U.flash, lift: U.lift, flip: U.flip, look: U.look, eq: U.eq },
    vertexShader: `attribute vec3 aS;attribute vec3 aD;varying vec3 L;varying vec3 N;varying vec3 D;varying vec3 Wp;varying vec3 S;varying float G;
      uniform float grow;uniform float bounce;uniform float env;uniform float tower;uniform float hk;uniform float clapX;uniform float lift;uniform float flip;uniform float eq;uniform float uT;
      ${HASH}
      void main(){vec3 c=vec3(instanceMatrix[3]);float r=length(c.xz);
        float g=clamp((grow*1.7-r/900.)*4.,0.,1.);g=1.-pow(1.-g,3.);g*=1.+.12*sin(g*3.1416);       // rises with a little overshoot
        float hb=hash(floor(c.xz/46.));float k=g*(1.+bounce*env*(.25+.75*hb))*mix(hk,tower,aD.z);
        float band=floor((c.x+1200.)/82.);float lev=.12+.88*abs(sin(uT*6.4+hash(vec2(band,3.))*6.2832))*(.35+.65*env);k*=mix(1.,.30+1.45*lev,eq*(1.-aD.z));
        vec3 pp=position;pp.y*=k;vec3 sc=aS;sc.y*=k;
        L=pp*aS;N=normal;D=aD;S=sc;G=g;
        vec4 w=modelMatrix*instanceMatrix*vec4(pp,1.);w.y=mix(w.y,c.y*k+pp.y*aS.y,step(.5,c.y)); // pieces that sit on a roof ride it up
        w.x+=clapX*(step(.5,fract(floor(c.x/46.)*.5))*2.-1.)*min(6.+.30*max(w.y,0.),44.)*smoothstep(0.,6.,w.y+8.);
        w.y+=lift*(1.5+26.*hb*hb)*(1.-aD.z);w.x+=lift*(hb-.5)*5.;                                   // gravity off: every block leaves the ground
        w.y=mix(w.y,600.-w.y,flip);                                                                        // weird: the city hangs from the sky                    // neighbours slam together: the city claps
        Wp=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;}`,
    fragmentShader: `varying vec3 L;varying vec3 N;varying vec3 D;varying vec3 Wp;varying vec3 S;varying float G;uniform vec3 fogC;uniform float fogK;uniform vec3 sun;uniform float crash;
      uniform float uT;uniform float guys;uniform float wired;uniform float lit;uniform float clap;uniform float fuse;uniform float gwave;uniform float flash;uniform float look;
      ${HASH}${MAGENTA}
      void main(){vec3 col;float dist=length(Wp-cameraPosition);float sd=floor(D.x+.5);
        float face=abs(N.x)>.5?1.:abs(N.z)>.5?2.:0.;
        float fail=hash(vec2(sd,7.)+floor(Wp.xz/900.));
        if(crash>fail*.9+.05){
          vec2 f2=face<.5?L.xz:(face<1.5?vec2(L.z,L.y):vec2(L.x,L.y));
          if(fract(sd/3.)<.4){vec2 cq=f2/14.;float fq=max(fwidth(cq.x),fwidth(cq.y));gl_FragColor=vec4(mix(checker(cq)*1.1,vec3(.5,0.,.5),smoothstep(.25,.7,fq)),1.);return;}
          vec2 sz=face<.5?S.xz:(face<1.5?S.zy:S.xy);vec2 q=f2/sz+(face<.5?vec2(.5):vec2(.5,0.));
          float px=max(fwidth(q.x),fwidth(q.y))*1.4;
          float e=min(min(q.x,1.-q.x),min(q.y,1.-q.y));float dg=min(abs(q.x-q.y),abs(q.x+q.y-1.))*.7;
          float line=max(smoothstep(px,0.,e),smoothstep(px,0.,dg))*(1.-smoothstep(.10,.30,px)*.75);
          gl_FragColor=vec4(mix(vec3(.02,.024,.04),vec3(.92),line),1.);return;}
        float pb=hash(vec2(sd,23.));                                                                   // every building is painted: teal, terracotta, mustard, slate blue, green, stone
        vec3 fac=pb<.20?vec3(.010,.066,.072):pb<.38?vec3(.105,.034,.016):pb<.54?vec3(.088,.062,.012):pb<.72?vec3(.022,.038,.098):pb<.86?vec3(.014,.058,.032):vec3(.060,.058,.054);
        float pw=hash(vec2(sd,41.));                                                                   // and has its own light: amber, warm white, mint, sky, coral
        vec3 tint=pw<.40?vec3(1.,.66,.27):pw<.58?vec3(1.,.90,.72):pw<.73?vec3(.30,1.,.78):pw<.88?vec3(.42,.78,1.):vec3(1.,.40,.20);
        vec3 base=mix(vec3(.012,.020,.040),fac,.82)*(1.+.25*(hash(vec2(sd,3.))-.5));
        float ndl=max(dot(N,normalize(vec3(-.35,.5,.8))),0.);
        base*=.75+.55*ndl;base+=vec3(.10,.075,.045)*max(dot(N,sun),0.)*.6;base+=flash*vec3(.16,.2,.32)*step(Wp.x,2.)*(.4+.6*max(-N.x,0.)+.5*step(.5,abs(N.z)));
        if(face<.5){col=base*1.25+vec3(.012,.016,.026);}
        else{
          vec2 f=face<1.5?vec2(L.z+S.z*.5,L.y):vec2(L.x+S.x*.5,L.y);
          vec2 cell=vec2(3.4,3.7);vec2 g=f/cell;vec2 id=floor(g);vec2 q=fract(g);
          float topm=step(L.y,S.y-1.2)*step(1.6,L.y);
          float edge=step(.6,f.x)*step(f.x,(face<1.5?S.z:S.x)-.6);
          vec2 fw=fwidth(g);float aa=clamp(max(fw.x,fw.y)*1.2,0.,.2);
          float win=smoothstep(.20-aa,.20+aa,q.x)*smoothstep(.80+aa,.80-aa,q.x)*smoothstep(.26-aa,.26+aa,q.y)*smoothstep(.76+aa,.76-aa,q.y)*topm*edge;
          float hh=hash(id+sd*vec2(17.,3.)+face*31.);
          float h2=hash(id+vec2(sd*7.+face*5.,91.));float h3=hash(id+vec2(13.,sd*3.+face));
          float on=step(1.-min(D.y*lit,1.),hh)*step(.92,G);
          on=max(on,step(L.y,fuse)*step(fuse,9000.)*step(.42,hh));                                  // the fuse: the skyline lights floor by floor
          // a little guy in every window: every window lights, and a head and shoulders sit in it; "wired" = he types, his screen flickers
          float near=1.-smoothstep(.03,.09,max(fw.x,fw.y));
          float guyOn=step(1.-guys,h3)*step(.001,guys)*step(dist,gwave);                               // they fill the windows in a wave, outward from the camera
          on=max(on,guyOn*step(.92,G));
          vec3 wc=mix(tint,vec3(1.,.66,.27),step(.72,h2));
          float bright=mix(.45,1.7,h3*h3)*(1.+clap*1.6);
          float bob=wired*sin(uT*(14.+h3*9.)+h2*40.)*.012;
          float cx=.5+(h2-.5)*.12;vec2 hq=(q-vec2(cx,.585+bob))/1.5;float tl=wired*.16*sin(uT*(7.+h3*5.)+h2*30.);hq=mat2(cos(tl),-sin(tl),sin(tl),cos(tl))*hq;                                   // a little Claude in every window: orange head, visor, half-lidded eyes, ivory spikes
          float hdd=length(max(abs(hq)-vec2(.050,.040),0.))-.022;float head=smoothstep(.004,-.004,hdd);
          float hairY=.056+.050*(1.-abs(fract((hq.x+.07)/.035)-.5)*2.);float hair=step(abs(hq.x),.066)*step(.048,hq.y)*step(hq.y,hairY);
          float visor=step(abs(hq.x),.057)*step(abs(hq.y-.002),.023)*head;
          vec2 ep=vec2(abs(hq.x)-.027,hq.y+.003);float blink=step(.95,fract(uT*.37+h3*7.));
          float eye=visor*smoothstep(.016,.012,length(ep))*step(ep.y,mix(.002,.016,look))*(1.-blink);
          float ear=smoothstep(.017,.013,length(vec2(abs(hq.x)-.078,hq.y)));
          vec2 tq=hq-vec2(0.,-.115);float torso=step(abs(tq.x),.050)*step(abs(tq.y),.058);
          float sh=torso;float guy=max(max(head,hair),max(torso,ear))*guyOn*near;
          vec3 rc=vec3(.74,.155,.006);rc=mix(rc,vec3(.80,.76,.66),hair*(1.-head));rc=mix(rc,vec3(.006),visor);rc=mix(rc,vec3(1.3,1.25,1.1),eye);
          float scr=step(.5,wired)*smoothstep(.0,.02,.5)*step(abs(q.x-(.5+(h2-.5)*.16)-.0),.11)*step(abs(q.y-.40),.05)*(.55+.45*step(.5,hash(id+floor(uT*(9.+h3*8.)))));
          col=mix(base,base*1.35+.004*h3,win);
          vec3 glow=wc*bright*mix(1.,mix(.72,1.12,clamp((q.y-.26)/.5,0.,1.)),near);
          float mull=max(smoothstep(.014,.008,abs(q.x-.5)),smoothstep(.016,.009,abs(q.y-.52)))*near*(1.-guyOn);glow*=1.-.7*mull;
          glow=mix(glow,vec3(.10,.17,.30)*(.8+.5*h3),guyOn*near);glow=mix(glow,rc,guy);glow=mix(glow,vec3(.75,.9,1.2),scr*guyOn*near);
          col+=win*on*glow;
          float lit2=step(.92,G)*(1.-step(.5,crash));
          float trim=step(S.y-1.0,L.y)*step(.55,hash(vec2(sd,57.)));col+=tint*trim*1.25*lit2;                    // a neon line round the roof
          float sid=floor(f.x/8.);float sh2=hash(vec2(sd*1.7+face,sid));vec3 shc=sh2<.25?vec3(.30,1.,.78):sh2<.5?vec3(1.,.66,.27):sh2<.75?vec3(.42,.78,1.):vec3(1.,.40,.20);
          float shop=step(L.y,1.45)*step(.25,L.y)*step(.42,hash(vec2(sid,sd+9.)))*smoothstep(.0,.5,fract(f.x/8.))*smoothstep(1.,.5,fract(f.x/8.));col+=shc*shop*.9*lit2;   // shopfronts at street level
        }
        float fg=1.-exp(-dist*fogK);col=mix(col,fogC,fg*.92);
        gl_FragColor=vec4(col,1.);}` });
  { const n = bList.length, geo = new THREE.BoxGeometry(1, 1, 1); geo.translate(0, .5, 0);
    const aS = new Float32Array(n * 3), aD = new Float32Array(n * 3); const m = new THREE.InstancedMesh(geo, cityMat, n), o = new THREE.Object3D();
    bList.forEach((b, i) => { o.position.set(b.x, b.y, b.z); o.scale.set(b.w, b.h, b.d); o.updateMatrix(); m.setMatrixAt(i, o.matrix); aS.set([b.w, b.h, b.d], i * 3); aD.set([b.seed, b.lit, b.tw], i * 3); });
    geo.setAttribute('aS', new THREE.InstancedBufferAttribute(aS, 3)); geo.setAttribute('aD', new THREE.InstancedBufferAttribute(aD, 3)); m.frustumCulled = false; scene.add(m); }
  const dark = new THREE.MeshBasicMaterial({ color: 0x070b14 });
  const land = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 96), dark); land.scale.set(960, 47, 560); land.position.y = -23.15; scene.add(land);
  const dots = (pts: number[][], color: number, size: number, k: number) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pts.flat()), 3));
    const p = new THREE.Points(g, new THREE.PointsMaterial({ size: size * SS, sizeAttenuation: false, color: new THREE.Color(color).multiplyScalar(k), depthWrite: false })); scene.add(p); return p; };
  { const pts: number[][] = []; for (let i = 0; i < 300; i++) { const a = i / 300 * 6.2832; const j = 1 + .012 * Math.sin(a * 9.) + .01 * Math.sin(a * 23.); pts.push([Math.cos(a) * 948 * j, 3, Math.sin(a) * 552 * j]); } dots(pts, 0xffd9a0, 1.5, 2.4); }

  // ---- the dot (it never left: it is the roundabout at the heart of the city), the avenue, its lamps
  const dot = new THREE.Mesh(new THREE.CircleGeometry(19, 96), new THREE.MeshBasicMaterial({ color: new THREE.Color(1, .20, .46).multiplyScalar(.85) })); dot.rotation.x = -Math.PI / 2; dot.position.y = GROUND_Y + 1.2; scene.add(dot);
  const dotBase = new THREE.Mesh(new THREE.CylinderGeometry(21, 21, 1.1, 96), new THREE.MeshStandardMaterial({ color: 0x151c2a, roughness: .8 })); dotBase.position.y = GROUND_Y + .5; scene.add(dotBase);
  const dotL = new THREE.PointLight(0xff6fae, 2600, 120, 1.7); dotL.position.set(0, 14, 0); scene.add(dotL);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(26, SHORE_Z - 20), new THREE.MeshStandardMaterial({ color: 0x0b101b, roughness: .95 })); road.rotation.x = -Math.PI / 2; road.position.set(0, GROUND_Y, (SHORE_Z + 20) / 2); scene.add(road);
  { const paint = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xd9dde8).multiplyScalar(.26) }); const n = Math.floor((SHORE_Z - 40) / 9);
    const dash = new THREE.InstancedMesh(new THREE.BoxGeometry(.16, .02, 4.2), paint, n); const o = new THREE.Object3D(); for (let i = 0; i < n; i++) { o.position.set(.12, GROUND_Y + .03, 36 + i * 9); o.updateMatrix(); dash.setMatrixAt(i, o.matrix); } scene.add(dash);
    const curbM = new THREE.MeshStandardMaterial({ color: 0x151c2a, roughness: .8 });
    for (const sx of [-1, 1]) { const c = new THREE.Mesh(new THREE.BoxGeometry(2.6, .18, SHORE_Z - 40), curbM); c.position.set(sx * 12.2, GROUND_Y + .09, (SHORE_Z + 30) / 2); scene.add(c); }
    const postM = new THREE.MeshStandardMaterial({ color: 0x0b0f18, roughness: .7 }); const zs: [number, number][] = [];
    for (let z = 50; z < SHORE_Z - 10; z += 34) for (const sx of [-1, 1]) zs.push([sx, z + (sx > 0 ? 17 : 0)]);
    const poles = new THREE.InstancedMesh(new THREE.CylinderGeometry(.08, .11, 7.2, 8), postM, zs.length), arms = new THREE.InstancedMesh(new THREE.BoxGeometry(1.7, .09, .09), postM, zs.length),
      bulbs = new THREE.InstancedMesh(new THREE.BoxGeometry(.6, .1, .26), new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffd29a).multiplyScalar(6) }), zs.length);
    zs.forEach(([sx, z], i) => { o.position.set(sx * 10.4, GROUND_Y + 3.6, z); o.updateMatrix(); poles.setMatrixAt(i, o.matrix); o.position.set(sx * 9.6, GROUND_Y + 7.15, z); o.updateMatrix(); arms.setMatrixAt(i, o.matrix); o.position.set(sx * 8.9, GROUND_Y + 7.08, z); o.updateMatrix(); bulbs.setMatrixAt(i, o.matrix); });
    scene.add(poles, arms, bulbs);
    for (const [sx, z] of zs) if (z > 230 && z < 400) { const L = new THREE.PointLight(0xffc98a, 90, 40, 1.8); L.position.set(sx * 8.9, GROUND_Y + 6.9, z); scene.add(L); } }

  // ---- rain (left of the centre line only). Falls with S.rainT; when gravity is off rainT stops and the drops hang.
  const rainMat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, uniforms: { rt: { value: 0 }, amt: { value: 0 } },
    vertexShader: `attribute float tail;uniform float rt;uniform float amt;varying float a;void main(){vec3 p=position;float sp=38.+fract(position.x*7.3)*12.;
      p.y=mod(position.y-rt*sp,64.)+tail*2.6;p.x-=tail*.16;a=amt*step(fract(position.z*3.7),amt);gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.);}`,
    fragmentShader: `varying float a;void main(){if(a<.01)discard;gl_FragColor=vec4(.70,.78,.95,.5*a);}` });
  { const N = 42000, p = new Float32Array(N * 6), tl = new Float32Array(N * 2); const rr = rng(3);
    for (let i = 0; i < N; i++) { const x = -rr() * 70 - .05, y = rr() * 64, z = 150 + rr() * 400; p.set([x, y, z, x, y, z], i * 6); tl.set([0, 1], i * 2); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setAttribute('tail', new THREE.BufferAttribute(tl, 1));
    const rain = new THREE.LineSegments(g, rainMat); rain.frustumCulled = false; scene.add(rain); }

  // ---- two traffic lights that collide; pigeons; fireworks
  const mkTL = () => { const g = new THREE.Group(); const m = new THREE.MeshStandardMaterial({ color: 0x0b0f18, roughness: .6 });
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(.09, .11, 4.2, 10), m); pole.position.y = 2.1; g.add(pole);
    const box = new THREE.Mesh(new THREE.BoxGeometry(.5, 1.4, .42), m); box.position.y = 4.7; g.add(box); const lamps: any[] = [];
    [[0xff3b30, .42], [0xffb020, 0], [0x30e070, -.42]].forEach(([c, y]: any) => { const l = new THREE.Mesh(new THREE.SphereGeometry(.15, 16, 12), new THREE.MeshBasicMaterial({ color: 0x111111 })); l.position.set(0, 4.7 + y, .2); l.userData.c = new THREE.Color(c); g.add(l); lamps.push(l); });
    g.userData.lamps = lamps; scene.add(g); return g; };
  const tlA = mkTL(), tlB = mkTL(); const tlL = new THREE.PointLight(0xfff0c0, 0, 90, 1.6); scene.add(tlL);
  const NB = 70; const birdG = new THREE.BufferGeometry(); birdG.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-.55, .12, -.1, 0, 0, .12, 0, 0, -.2, .55, .12, -.1, 0, 0, -.2, 0, 0, .12]), 3));
  const birds = new THREE.InstancedMesh(birdG, new THREE.MeshBasicMaterial({ color: 0xaab6d6, side: THREE.DoubleSide }), NB); birds.frustumCulled = false; scene.add(birds);
  const NF = 9 * 110, fwPos = new Float32Array(NF * 3), fwCol = new Float32Array(NF * 3); const fwG = new THREE.BufferGeometry(); fwG.setAttribute('position', new THREE.BufferAttribute(fwPos, 3)); fwG.setAttribute('color', new THREE.BufferAttribute(fwCol, 3));
  const fw = new THREE.Points(fwG, new THREE.PointsMaterial({ size: 4.2 * SS, sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); fw.frustumCulled = false; scene.add(fw);
  const fwDirs = (() => { const r = rng(21), a: number[][] = []; for (let i = 0; i < NF; i++) { const u = r() * 2 - 1, th = r() * 6.2832, s = Math.sqrt(1 - u * u); a.push([s * Math.cos(th), u, s * Math.sin(th), .6 + .4 * r()]); } return a; })();
  const fwC = (() => { const r = rng(22), a: number[][] = []; for (let b = 0; b < 9; b++) a.push([(r() * 2 - 1) * 420, 230 + r() * 150, (r() * 2 - 1) * 200 - 40, 70 + r() * 50]); return a; })();

  // ---- the causeway and pier (it can be built outward: S.cause 0..1)
  const Z0 = SHORE_Z, Z1 = PIER_Z + 22, LEN = Z1 - Z0;
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 512; { const x = cv.getContext('2d')!; x.fillStyle = '#232a36'; x.fillRect(0, 0, 512, 512);
    const pr = rng(5); for (let i = 0; i < 16; i++) { const v = 28 + pr() * 16 | 0; x.fillStyle = `rgb(${v + 4},${v + 8},${v + 18})`; x.fillRect(0, i * 32, 512, 30); x.fillStyle = 'rgba(0,0,0,.55)'; x.fillRect(0, i * 32 + 30, 512, 2); } }
  const deckT = new THREE.CanvasTexture(cv); deckT.wrapS = deckT.wrapT = THREE.RepeatWrapping; deckT.colorSpace = THREE.SRGBColorSpace; deckT.anisotropy = 16;
  const deck = new THREE.Mesh(new THREE.BoxGeometry(8.4, .3, 1), new THREE.MeshStandardMaterial({ map: deckT, roughness: .5, metalness: 0, envMapIntensity: 1 })); scene.add(deck);
  const ramp = new THREE.Mesh(new THREE.BoxGeometry(8.4, .3, 26), deck.material); ramp.position.set(0, (GROUND_Y + DECK_Y) / 2 - .15, SHORE_Z - 11); ramp.rotation.x = -Math.atan2(DECK_Y - GROUND_Y, 26); scene.add(ramp);
  const postM2 = new THREE.MeshStandardMaterial({ color: 0x0b0f18, roughness: .7 }); const czs: number[] = []; for (let z = Z0 + 4; z <= PIER_Z - 12; z += 8.5) czs.push(z);
  const cPosts = new THREE.InstancedMesh(new THREE.CylinderGeometry(.16, .2, 3.4, 10), postM2, czs.length * 2), cBulbs = new THREE.InstancedMesh(new THREE.CylinderGeometry(.19, .19, .12, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffd29a).multiplyScalar(2.2) }), czs.length * 2);
  const pylons = new THREE.InstancedMesh(new THREE.BoxGeometry(1.1, 47, 1.1), postM2, Math.ceil(LEN / 42) * 2);
  const farPts: number[][] = []; { const o = new THREE.Object3D(); let i = 0; for (const z of czs) for (const sx of [-1, 1]) { o.position.set(sx * 4.05, .4, z); o.updateMatrix(); cPosts.setMatrixAt(i, o.matrix); o.position.set(sx * 4.05, 2.16, z); o.updateMatrix(); cBulbs.setMatrixAt(i, o.matrix); i++; farPts.push([sx * 4.05, 2.3, z]); }
    let j = 0; for (let z = Z0 + 20; z < Z1; z += 42) for (const sx of [-1, 1]) { o.position.set(sx * 3.4, -22.4, z); o.updateMatrix(); pylons.setMatrixAt(j++, o.matrix); } pylons.count = j; }
  scene.add(cPosts, cBulbs, pylons); const cFar = dots(farPts, 0xffd29a, 1.1, 1.6);
  for (const z of [PIER_Z - 14, PIER_Z - 22.5, PIER_Z - 31]) for (const sx of [-1, 1]) { const L = new THREE.PointLight(0xffc98a, .5, 7, 1.8); L.position.set(sx * 3.7, 2.3, z); scene.add(L); }

  // ---- image-based light for the paint
  { const s = new THREE.Scene(); s.add(sky.clone()); const c = corona.clone(); c.lookAt(0, 2, PIER_Z); s.add(c);
    for (const e of [{ p: [-9, 7, PIER_Z + 22], r: 3.2, c: 0xffd0a0, k: 5 }, { p: [10, 6, PIER_Z + 26], r: 3, c: 0x9fc0ff, k: 2.2 }, { p: [4, 5, PIER_Z - 18], r: 1, c: 0xffd29a, k: 6 }, { p: [-4, 5, PIER_Z - 18], r: 1, c: 0xffd29a, k: 6 }]) {
      const m = new THREE.Mesh(new THREE.SphereGeometry(e.r, 16, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(e.c).multiplyScalar(e.k) })); m.position.set(e.p[0], e.p[1], e.p[2]); s.add(m); }
    const pm = new THREE.PMREMGenerator(renderer); const cc = new THREE.CubeCamera(1, 90000, new THREE.WebGLCubeRenderTarget(512, { type: THREE.HalfFloatType }));
    cc.position.set(0, 2, PIER_Z); cc.update(renderer, s); scene.environment = pm.fromCubemap(cc.renderTarget.texture).texture; }

  // ---- the GT3 RS (Ultraviolet, YELLOW calipers, DKWHEEL plate). Its lights ride with it.
  const gltf = await new GLTFLoader().loadAsync(urls.car); const carM = gltf.scene; const wheels: any[] = [];
  carM.traverse((o: any) => { if (/^wheel_/.test(o.name)) wheels.push(o); if (!o.isMesh) return; const ms = Array.isArray(o.material) ? o.material : [o.material];
    ms.forEach((m: any) => { const n = (m.name || '').toLowerCase();
      if (n.includes('caliper')) { m.color.set(0xffd21f); m.emissive = new THREE.Color(0xffd21f); m.emissiveIntensity = .35; m.roughness = .4; m.metalness = .1; }
      if (n === 'paint' || n.includes('body_paint')) { m.color.set(0x8431c4); m.metalness = .5; m.roughness = .34; m.clearcoat = 1; m.clearcoatRoughness = .06; m.envMapIntensity = 1.5; }
      if (n === 'rim') { m.color.set(0xc9ccd2); m.metalness = .9; m.roughness = .3; }
      if (n.includes('window_glass')) { m.opacity = .13; m.transparent = true; m.depthWrite = false; }
      if (m.userData && m.userData.lamp_color && n.includes('taillight') && n.includes('lens')) { const lc = m.userData.lamp_color; m.emissive.setRGB(lc[0], lc[1], lc[2]); m.emissiveIntensity = 2.2; }
      if (m.userData && m.userData.lamp_color && (n.includes('headlight') || n.includes('frontlamp'))) { m.emissive.setRGB(1, .95, .86); m.emissiveIntensity = n.includes('glass') ? 1.2 : 4; } }); });
  { const tex = await new THREE.TextureLoader().loadAsync(urls.plate); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 16;
    const pw = .305, ph = pw * 340 / 1160 * 1.72; const g = new THREE.Group();
    g.add(new THREE.Mesh(new THREE.PlaneGeometry(pw, ph), new THREE.MeshStandardMaterial({ map: tex, roughness: .55, metalness: 0, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: .10 })));
    const fm = new THREE.MeshStandardMaterial({ color: 0x050506, roughness: .35, metalness: .6 }); const bw = .012, bb = .022, d = .012;
    const bar = (w, h, x, y) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), fm); m.position.set(x, y, 0); g.add(m); };
    bar(pw + 2 * bw, bw, 0, ph / 2 + bw / 2); bar(pw + 2 * bw, bb, 0, -ph / 2 - bb / 2); bar(bw, ph, -pw / 2 - bw / 2, 0); bar(bw, ph, pw / 2 + bw / 2, 0);
    g.position.set(0, .45, -2.275); g.rotation.y = Math.PI; carM.add(g); }
  const bot = new THREE.Group(), botHead = new THREE.Group(); {
    const OR = new THREE.MeshStandardMaterial({ color: 0xf0600c, roughness: .45, metalness: .0, envMapIntensity: .5, emissive: 0xf04a00, emissiveIntensity: .14 }), IV = new THREE.MeshStandardMaterial({ color: 0xf2ecdd, roughness: .5, emissive: 0xf2ecdd, emissiveIntensity: .16 }),
      CH = new THREE.MeshStandardMaterial({ color: 0x23242a, roughness: .6 }), BK = new THREE.MeshStandardMaterial({ color: 0x0b0b0e, roughness: .25, metalness: .2 }), WH = new THREE.MeshBasicMaterial({ color: 0xfff6e6 });
    const add = (g: any, geo: any, m: any, x: number, y: number, z: number, rx = 0, rz = 0) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.rotation.set(rx, 0, rz); g.add(o); return o; };
    add(botHead, new RoundedBoxGeometry(.56, .50, .50, 5, .12), OR, 0, 0, 0);
    add(botHead, new RoundedBoxGeometry(.44, .17, .06, 3, .03), BK, 0, .03, .245);                                   // the visor
    for (const sx of [-1, 1]) { add(botHead, new THREE.CircleGeometry(.052, 24, Math.PI, Math.PI), WH, sx * .105, .022, .279);   // eyes: lower halves only (half-lidded)
      add(botHead, new THREE.BoxGeometry(.13, .018, .01), OR, sx * .105, .052, .28, 0, sx * -.16);                    // the lids, tilted: deadpan
      add(botHead, new THREE.CylinderGeometry(.085, .085, .05, 20), OR, sx * .30, 0, 0, 0, Math.PI / 2); add(botHead, new THREE.CylinderGeometry(.045, .045, .06, 16), CH, sx * .305, 0, 0, 0, Math.PI / 2); }
    const sr = rng(41); for (let i = 0; i < 15; i++) { const a = sr() * 6.2832, r = sr() * .17, h = .16 + sr() * .15; const sp = add(botHead, new THREE.ConeGeometry(.045, h, 8), IV, Math.cos(a) * r, .25 + h / 2 - .02, Math.sin(a) * r * .8 - .02); sp.rotation.set(Math.sin(a) * r * 2.2 - .1, 0, -Math.cos(a) * r * 2.6); }
    botHead.position.set(0, 1.25, 0); bot.add(botHead);
    add(bot, new RoundedBoxGeometry(.44, .46, .32, 4, .09), OR, 0, .74, 0); add(bot, new THREE.CylinderGeometry(.07, .07, .08, 12), CH, 0, .99, 0);
    for (const sx of [-1, 1]) { add(bot, new THREE.CylinderGeometry(.055, .055, .34, 10), IV, sx * .30, .74, 0, 0, sx * .12); add(bot, new THREE.SphereGeometry(.07, 12, 10), CH, sx * .26, .92, 0);
      add(bot, new THREE.SphereGeometry(.085, 12, 10), OR, sx * .33, .53, 0); add(bot, new THREE.CylinderGeometry(.06, .06, .32, 10), IV, sx * .12, .34, 0); add(bot, new THREE.SphereGeometry(.07, 12, 10), CH, sx * .12, .50, 0);
      add(bot, new RoundedBoxGeometry(.17, .11, .26, 3, .04), OR, sx * .12, .055, .04); }
    scene.add(bot); }
  const car = new THREE.Group(); car.add(carM); scene.add(car);
  const key = new THREE.SpotLight(0xffd9c8, 240, 60, .5, .8, 1.6), fill = new THREE.SpotLight(0xc9b8ff, 46, 60, .6, .9, 1.6), hl = new THREE.SpotLight(0xfff0d8, 150, 70, .40, 1, 1.5);
  const kT = new THREE.Object3D(), hT = new THREE.Object3D(); scene.add(key, fill, hl, kT, hT); key.target = kT; fill.target = kT; hl.target = hT;
  const carDot = dots([[0, 0, 0]], 0x9a4dff, 2.2, 2.6);
  const back = new THREE.DirectionalLight(0xffe2b0, .13); scene.add(back);
  scene.add(new THREE.HemisphereLight(0x25365c, 0x05070c, .9));


  // ---- "Make it spin": the island is the label of a record. A ring of vinyl on the sea, grooves and two sheen wedges.
  const vinyl = new THREE.Mesh(new THREE.RingGeometry(770, 1750, 160, 1), new THREE.ShaderMaterial({ transparent: true, depthWrite: false, depthTest: false, uniforms: { uT: U.uT, op: { value: 0 }, sa: { value: 0 } },
    vertexShader: `varying vec2 p;void main(){p=position.xy;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader: `varying vec2 p;uniform float uT;uniform float op;uniform float sa;
      void main(){float r=length(p),a=atan(p.y,p.x);float fw=fwidth(r);float gr=.5+.5*sin(r*1.6);gr=mix(.5,gr,clamp(1.-fw*.9,0.,1.));
        float band=smoothstep(.0,6.,abs(mod(r,230.)-115.)-104.);                                   // the gaps between tracks
        float sh=pow(abs(cos(a-sa-1.15)),46.)+.5*pow(abs(cos(a-sa+.55)),80.);
        vec3 c=vec3(.010,.010,.014)+vec3(.045,.045,.055)*gr*(1.-band)+vec3(.62,.66,.78)*sh*(.25+.75*gr)*(1.-.6*band);
        float gl=pow(abs(cos((a+uT*3.6)*1.)),260.)+pow(abs(cos((a+uT*3.6)*1.+1.9)),420.);c+=vec3(.5,.52,.6)*gl*(.4+.6*gr)*(1.-band);
        float ed=smoothstep(770.,780.,r)*smoothstep(1750.,1740.,r);gl_FragColor=vec4(c,op*ed);}` }));
  vinyl.rotation.x = -Math.PI / 2; vinyl.position.y = 1; vinyl.renderOrder = 2; vinyl.visible = false; scene.add(vinyl);

  // ---- GIANT CLAUDE: he does the prompts by hand. Built in robot units (about 1.9 tall) and scaled by GS; each arm is two-bone IK to a
  // world target. Props: a watering can (and its water), tweezers for the car, a bath plug on a chain.
  const GS = 450, GL1 = .36, GL2 = .34;
  const giant = new THREE.Group(), gUpper = new THREE.Group(), gHead = new THREE.Group(); giant.visible = false; scene.add(giant);
  const GM: any = { or: new THREE.MeshStandardMaterial({ color: 0xf47a1a, roughness: .5, metalness: 0, emissive: 0xe8700e, emissiveIntensity: .30 }),
    iv: new THREE.MeshStandardMaterial({ color: 0xf2ecdd, roughness: .55, emissive: 0xf2ecdd, emissiveIntensity: .24 }),
    ch: new THREE.MeshStandardMaterial({ color: 0x23242a, roughness: .6, emissive: 0x23242a, emissiveIntensity: .3 }), bk: new THREE.MeshStandardMaterial({ color: 0x0b0b0e, roughness: .25, metalness: .2 }),
    wh: new THREE.MeshBasicMaterial({ color: 0xfff6e6 }), st: new THREE.MeshStandardMaterial({ color: 0xaab0bb, roughness: .32, metalness: .6, emissive: 0x6a7080, emissiveIntensity: .28 }),
    tin: new THREE.MeshStandardMaterial({ color: 0xa9c0d4, roughness: .42, metalness: .5, emissive: 0x4a6076, emissiveIntensity: .55 }) };
  const gAdd = (g: any, geo: any, m: any, x: number, y: number, z: number, rx = 0, rz = 0) => { const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.rotation.set(rx, 0, rz); g.add(o); return o; };
  for (const sx of [-1, 1]) { gAdd(giant, new THREE.CylinderGeometry(.06, .06, .50, 12), GM.iv, sx * .12, .27, 0); gAdd(giant, new THREE.SphereGeometry(.07, 12, 10), GM.ch, sx * .12, .50, 0);
    gAdd(giant, new RoundedBoxGeometry(.17, .11, .26, 3, .04), GM.or, sx * .12, .055, .04); }
  gUpper.position.set(0, .52, 0); giant.add(gUpper);
  gAdd(gUpper, new RoundedBoxGeometry(.44, .46, .32, 4, .09), GM.or, 0, .22, 0); gAdd(gUpper, new THREE.CylinderGeometry(.07, .07, .08, 12), GM.ch, 0, .47, 0);
  gHead.position.set(0, .73, 0); gUpper.add(gHead);
  gAdd(gHead, new RoundedBoxGeometry(.56, .50, .50, 5, .12), GM.or, 0, 0, 0); gAdd(gHead, new RoundedBoxGeometry(.44, .17, .06, 3, .03), GM.bk, 0, .03, .245);
  for (const sx of [-1, 1]) { gAdd(gHead, new THREE.CircleGeometry(.052, 24, Math.PI, Math.PI), GM.wh, sx * .105, .022, .279); gAdd(gHead, new THREE.BoxGeometry(.13, .018, .01), GM.or, sx * .105, .052, .28, 0, sx * -.16);
    gAdd(gHead, new THREE.CylinderGeometry(.085, .085, .05, 20), GM.or, sx * .30, 0, 0, 0, Math.PI / 2); gAdd(gHead, new THREE.CylinderGeometry(.045, .045, .06, 16), GM.ch, sx * .305, 0, 0, 0, Math.PI / 2); }
  { const sr = rng(41); for (let i = 0; i < 15; i++) { const a = sr() * 6.2832, r = sr() * .17, h = .16 + sr() * .15; const sp = gAdd(gHead, new THREE.ConeGeometry(.045, h, 8), GM.iv, Math.cos(a) * r, .25 + h / 2 - .02, Math.sin(a) * r * .8 - .02);
      sp.rotation.set(Math.sin(a) * r * 2.2 - .1, 0, -Math.cos(a) * r * 2.6); } }
  const mkArm = (sx: number) => { const a: any = { sx, S: new THREE.Vector3(sx * .30, .40, 0), hand: new THREE.Group() };
    a.up = gAdd(gUpper, new THREE.CylinderGeometry(.055, .055, 1, 12), GM.iv, 0, 0, 0); a.fo = gAdd(gUpper, new THREE.CylinderGeometry(.05, .05, 1, 12), GM.iv, 0, 0, 0);
    gAdd(gUpper, new THREE.SphereGeometry(.078, 14, 12), GM.ch, sx * .30, .40, 0); a.el = gAdd(gUpper, new THREE.SphereGeometry(.066, 14, 12), GM.ch, 0, 0, 0);
    gAdd(a.hand, new RoundedBoxGeometry(.15, .15, .11, 3, .04), GM.or, 0, .05, 0); a.f1 = gAdd(a.hand, new RoundedBoxGeometry(.05, .12, .06, 2, .02), GM.or, -.045, .17, 0); a.f2 = gAdd(a.hand, new RoundedBoxGeometry(.05, .12, .06, 2, .02), GM.or, .045, .17, 0);
    gUpper.add(a.hand); return a; };
  const gArms = [mkArm(-1), mkArm(1)];
  const _gT = new THREE.Vector3(), _gu = new THREE.Vector3(), _gw = new THREE.Vector3(), _gE = new THREE.Vector3(), _gY = new THREE.Vector3(0, 1, 0), _gd = new THREE.Vector3(), _gp = new THREE.Vector3();
  const gSeg = (m: any, A: any, B: any) => { _gd.subVectors(B, A); const len = Math.max(1e-4, _gd.length()); m.position.copy(A).addScaledVector(_gd, .5); m.scale.set(1, len, 1); m.quaternion.setFromUnitVectors(_gY, _gd.normalize()); };
  const ikArm = (a: any, Tw: number[] | null, pinch = 0) => {
    if (Tw) { _gT.set(Tw[0], Tw[1], Tw[2]); gUpper.worldToLocal(_gT); } else _gT.set(a.sx * .37, -.18, .07);
    _gu.subVectors(_gT, a.S); let d = _gu.length(); const mx = (GL1 + GL2) * .998; if (d > mx) { _gu.multiplyScalar(mx / d); d = mx; _gT.copy(a.S).add(_gu); } _gu.normalize();
    const an = Math.acos(Math.max(-1, Math.min(1, (GL1 * GL1 + d * d - GL2 * GL2) / (2 * GL1 * d))));
    _gp.set(a.sx * .9, -.55, -.6); _gw.copy(_gp).addScaledVector(_gu, -_gp.dot(_gu)).normalize();
    _gE.copy(a.S).addScaledVector(_gu, GL1 * Math.cos(an)).addScaledVector(_gw, GL1 * Math.sin(an));
    gSeg(a.up, a.S, _gE); gSeg(a.fo, _gE, _gT); a.el.position.copy(_gE);
    _gd.subVectors(_gT, _gE).normalize(); a.hand.position.copy(_gT); a.hand.quaternion.setFromUnitVectors(_gY, _gd);
    const g = .048 - .03 * pinch; a.f1.position.x = -g; a.f2.position.x = g; };
  // the watering can (robot units; spout along +x) and its water
  const can = new THREE.Group(); can.visible = false; can.scale.setScalar(GS); scene.add(can);
  gAdd(can, new THREE.CylinderGeometry(.17, .17, .30, 28), GM.tin, 0, 0, 0); gAdd(can, new THREE.CylinderGeometry(.176, .176, .03, 28), GM.st, 0, .15, 0);
  gAdd(can, new THREE.CylinderGeometry(.03, .05, .37, 14), GM.tin, .30, .14, 0, 0, -.944); gAdd(can, new THREE.CylinderGeometry(.08, .035, .06, 18), GM.st, .47, .265, 0, 0, -.944);
  gAdd(can, new THREE.TorusGeometry(.105, .02, 10, 24), GM.tin, -.19, .0, 0);
  const NW = 900, wPos = new Float32Array(NW * 6), wGeo = new THREE.BufferGeometry(); wGeo.setAttribute('position', new THREE.BufferAttribute(wPos, 3));
  const water2 = new THREE.LineSegments(wGeo, new THREE.LineBasicMaterial({ color: 0xcfe8ff, transparent: true, opacity: .85, blending: THREE.AdditiveBlending, depthWrite: false })); water2.frustumCulled = false; water2.visible = false; scene.add(water2);
  const wR = rng(77), wH = Array.from({ length: NW }, () => [wR(), wR(), wR(), wR()]);
  const _c0 = new THREE.Vector3(), _cx = new THREE.Vector3(), _cz = new THREE.Vector3();
  // tweezers (world units): tips at the origin, opening along x
  const tw = new THREE.Group(); tw.visible = false; scene.add(tw);
  const twB = [-1, 1].map((sx) => { const g = new THREE.CylinderGeometry(.95, .2, 80, 4); g.rotateY(Math.PI / 4); g.translate(0, 40, 0); const m = new THREE.Mesh(g, GM.st); tw.add(m); return m; });
  { const top = new THREE.Mesh(new THREE.BoxGeometry(1.6, 6, 1.9), GM.st); top.position.y = 80; tw.add(top); }
  // the bath plug and its chain (world units)
  const plug = new THREE.Group(); plug.visible = false; scene.add(plug);
  gAdd(plug, new THREE.CylinderGeometry(58, 44, 24, 32), GM.bk, 0, 0, 0); gAdd(plug, new THREE.TorusGeometry(14, 3.2, 8, 20), GM.st, 0, 22, 0);
  const chain = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 1, 8), GM.st); chain.visible = false; scene.add(chain);
  const rt = new THREE.WebGLRenderTarget(W * SS, H * SS, { type: THREE.HalfFloatType, samples: 4 });
  const comp = new EffectComposer(renderer, rt); comp.setPixelRatio(1); comp.setSize(W * SS, H * SS);
  comp.addPass(new RenderPass(scene, camera)); const bloom = new UnrealBloomPass(new THREE.Vector2(W * SS, H * SS), .2, .55, 1.0); comp.addPass(bloom); comp.addPass(new OutputPass());
  // ---- STYLE FLIPS: one prompt can re-render the whole picture in another style.
  // 1 blueprint, 2 daylight, 3 pencil model, 4 terminal text, 5 pixel art, 6 thermal, 7 two-ink print, 8 neon wire.
  // tiles 2 / 4: the same shot rendered 4 / 16 ways at once (chorus 1's variant wall, in 3D).
  const stylePass = new ShaderPass({ uniforms: { tDiffuse: { value: null }, res: { value: new THREE.Vector2(W * SS, H * SS) }, mode: { value: 0 }, modeB: { value: 0 }, xf: { value: 1 }, k: { value: 1 }, split: { value: 0 }, tiles: { value: 1 }, tick: { value: 0 } },
    vertexShader: `varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader: `varying vec2 vUv;uniform sampler2D tDiffuse;uniform vec2 res;uniform float mode;uniform float modeB;uniform float xf;uniform float k;uniform float split;uniform float tiles;uniform float tick;
      float L(vec3 c){return dot(c,vec3(.299,.587,.114));}
      vec3 T(vec2 uv){return texture2D(tDiffuse,uv).rgb;}
      float edge(vec2 uv,float px){vec2 d=vec2(px)/res;float a=L(T(uv+vec2(-d.x,-d.y))),b=L(T(uv+vec2(0.,-d.y))),c=L(T(uv+vec2(d.x,-d.y))),e=L(T(uv+vec2(-d.x,0.))),f=L(T(uv+vec2(d.x,0.))),g=L(T(uv+vec2(-d.x,d.y))),h=L(T(uv+vec2(0.,d.y))),i=L(T(uv+d));
        float gx=-a-2.*e-g+c+2.*f+i,gy=-a-2.*b-c+g+2.*h+i;return sqrt(gx*gx+gy*gy);}
      float keepHue(vec3 c,float l){float mx=max(c.r,max(c.g,c.b)),mn=min(c.r,min(c.g,c.b));return smoothstep(.5,.75,(mx-mn)/max(mx,.01))*smoothstep(.10,.22,l);}
      vec3 styled(vec2 uv,float m,float sc){vec3 c=T(uv),o=c;float l=L(c);float asp=res.x/res.y;
        if(m<.5){o=c;}
        else if(m<1.5){float e=smoothstep(.05,.22,edge(uv,3.*sc));vec2 g=uv*vec2(asp,1.)*18./sc;vec2 gf=abs(fract(g)-.5);float grid=smoothstep(.478,.5,max(gf.x,gf.y));
          vec2 g5=abs(fract(g*5.)-.5);float fine=smoothstep(.46,.5,max(g5.x,g5.y));
          vec3 bp=vec3(.035,.17,.47)+grid*.10+fine*.03;o=mix(bp,vec3(.90,.95,1.),e);}
        else if(m<2.5){float l2=.94-.68*pow(l,.5);vec3 hue=c/max(max(c.r,max(c.g,c.b)),.02);o=l2*mix(vec3(1.),hue,.34)*vec3(1.03,1.,.95);o*=1.-.30*smoothstep(.03,.16,edge(uv,2.*sc));o=mix(o,c*1.05,keepHue(c,l)*step(c.b*.9,c.r)*step(c.g*1.15,max(c.r,c.b)));}
        else if(m<3.5){float l2=.94-.68*pow(l,.5);o=vec3(.972,.958,.93)*mix(.78,1.,l2);float e=smoothstep(.04,.18,edge(uv,2.*sc));o=mix(o,vec3(.30,.29,.28),e*.55);o=mix(o,c*1.05,keepHue(c,l)*step(c.b*1.25,c.r));}
        else if(m<4.5){float rows=40./sc;vec2 cz=vec2(.6/(rows*asp),1./rows);vec2 cell=floor(uv/cz);vec2 f=fract(uv/cz);float lc=smoothstep(.04,.80,pow(L(T((cell+.5)*cz)),.62));float lv=floor(lc*6.99);
          vec2 p=f-.5;float g=0.;
          if(lv<.5)g=0.;else if(lv<1.5)g=step(length(p-vec2(0.,-.25)),.10);else if(lv<2.5)g=max(step(length(p-vec2(0.,.2)),.10),step(length(p-vec2(0.,-.2)),.10));
          else if(lv<3.5)g=max(step(abs(p.x),.08)*step(abs(p.y),.32),step(abs(p.y),.07)*step(abs(p.x),.34));
          else if(lv<4.5)g=max(max(step(abs(p.x-.16),.07),step(abs(p.x+.16),.07))*step(abs(p.y),.36),max(step(abs(p.y-.14),.06),step(abs(p.y+.14),.06))*step(abs(p.x),.40));
          else if(lv<5.5)g=step(abs(p.x),.40)*step(abs(p.y),.40)*step(.5,fract((f.x+f.y)*3.));else g=step(abs(p.x),.42)*step(abs(p.y),.44);
          vec3 cc=T((cell+.5)*cz);vec3 gh=mix(vec3(.30,1.,.50),cc/max(max(cc.r,max(cc.g,cc.b)),.03),.55*keepHue(cc,L(cc)));o=vec3(.012,.035,.02)+gh*g*(.40+.80*lc);o*=.88+.12*sin(uv.y*res.y/sc*1.5708);}
        else if(m<5.5){vec2 n=vec2(320.,180.)/sc;vec2 pc=floor(uv*n);vec3 p=T((pc+.5)/n);p=pow(p,vec3(.80));float by=mod(pc.x,2.)*.5+mod(pc.x+pc.y,2.)*.25-.375;o=clamp(floor(p*7.+.5+by*.9)/7.,0.,1.);}
        else if(m<6.5){float x=pow(l,.48);o=mix(vec3(.02,.03,.20),vec3(.0,.55,.75),smoothstep(.0,.30,x));o=mix(o,vec3(.95,.85,.10),smoothstep(.28,.55,x));o=mix(o,vec3(.95,.25,.05),smoothstep(.52,.78,x));o=mix(o,vec3(1.,.97,.9),smoothstep(.78,1.,x));}
        else if(m<7.5){float cs=74./sc;vec2 q=mat2(.7071,-.7071,.7071,.7071)*(uv*vec2(asp,1.))*cs;vec2 f=fract(q)-.5;vec2 cuv=uv;float d=clamp(pow(l,.50)*1.25,0.,1.);
          float dot1=smoothstep(.05,-.05,length(f)-.60*sqrt(d));vec3 paper=vec3(.955,.93,.87);vec3 ink=vec3(.06,.10,.36);o=mix(paper,ink,dot1);o=mix(o,ink,smoothstep(.04,.16,edge(uv,2.2*sc))*.85);
          float warm=keepHue(c,l)*step(c.b*1.1,c.r);vec2 f2=fract(q+.5)-.5;o=mix(o,vec3(.96,.36,.10),warm*smoothstep(.04,-.04,length(f2)-.40));}
        else{float e=smoothstep(.04,.20,edge(uv,2.5*sc));float e2=smoothstep(.02,.30,edge(uv,7.*sc));o=vec3(.008,.012,.03)+vec3(.10,.95,1.)*e+vec3(.05,.30,.55)*e2*.5;o=mix(o,c*1.4,keepHue(c,l)*.85);}
        return o;}
      void main(){vec3 c=T(vUv),o;
        if(tiles>1.5){vec2 tv=vUv*tiles;vec2 id=floor(tv);vec2 uv=fract(tv);float idx=id.x+(tiles-1.-id.y)*tiles;
          float tab[9];tab[0]=0.;tab[1]=1.;tab[2]=5.;tab[3]=2.;tab[4]=8.;tab[5]=7.;tab[6]=6.;tab[7]=3.;tab[8]=4.;
          float sel=mod(idx*(tiles>2.5?5.:1.)+tick,9.);float m=0.;for(int i=0;i<9;i++)if(abs(float(i)-sel)<.5)m=tab[i];
          o=styled(uv,m,tiles);vec2 bw=vec2(2.5)*tiles/res;float gut=step(uv.x,bw.x)+step(1.-bw.x,uv.x)+step(uv.y,bw.y)+step(1.-bw.y,uv.y);o=mix(o,vec3(.015,.02,.035),clamp(gut,0.,1.));}
        else{vec3 sA=styled(vUv,mode,1.);if(xf<.999)sA=mix(styled(vUv,modeB,1.),sA,xf);o=mix(c,sA,k);
          if(split>.001){float mm=smoothstep(split-1.5/res.x,split+1.5/res.x,vUv.x);o=mix(c,o,mm);o=mix(o,vec3(1.),smoothstep(3.5/res.x,1./res.x,abs(vUv.x-split))*.9*step(split,.995));}}
        gl_FragColor=vec4(o,1.);}` });
  comp.addPass(stylePass);


  const V = new THREE.Vector3(), O = new THREE.Object3D(), Q = new THREE.Quaternion(), E = new THREE.Euler();
  const SPD = new THREE.Vector3(), SPR = new THREE.Vector3(), SPU = new THREE.Vector3();
  const project = (x: number, y: number, z: number) => { V.set(x, y, z).project(camera); return [(V.x * .5 + .5) * W, (-V.y * .5 + .5) * H, V.z]; };
  const right = new THREE.Vector3(1, 0, 0), upQ = new THREE.Vector3(0, Math.cos(el), Math.sin(el));   // the sky quad's own axes

  return {
    project,
    render(S: any) {
      // camera (roll turns the horizon: "Turn the ceiling into the floor")
      camera.position.set(S.cam.p[0], S.cam.p[1], S.cam.p[2]); camera.fov = S.cam.fov; camera.updateProjectionMatrix();
      camera.up.set(0, 1, 0); camera.lookAt(S.cam.l[0], S.cam.l[1], S.cam.l[2]); if (S.cam.roll) camera.rotateZ(S.cam.roll); vinyl.material.uniforms.sa.value = Math.atan2(-camera.position.z, camera.position.x);
      { const g = S.giant; giant.visible = !!(g && g.on); can.visible = !!(g && g.on && g.can); water2.visible = can.visible && g.can.pour > .02; plug.visible = chain.visible = !!(g && g.on && g.plug);
        if (g && g.on) { giant.position.set(g.x, g.y, g.z); giant.rotation.set(0, g.yaw, 0); giant.scale.setScalar(GS); gUpper.rotation.set(g.lean || 0, 0, 0); gHead.rotation.set(g.headPitch || 0, g.headYaw || 0, 0); giant.updateMatrixWorld(true);
          let L = g.L || null, R = g.R || null;
          if (g.can) { can.position.set(g.can.p[0], g.can.p[1], g.can.p[2]); can.rotation.set(0, g.can.yaw || 0, -(g.can.tilt || 0)); can.updateMatrixWorld(true);
            _gT.set(-.245, .02, 0); can.localToWorld(_gT); L = [_gT.x, _gT.y, _gT.z]; if (!g.can.oneHand) { _gT.set(.10, -.17, .05); can.localToWorld(_gT); R = [_gT.x, _gT.y, _gT.z]; }
            _c0.set(.49, .285, 0); can.localToWorld(_c0); _cx.setFromMatrixColumn(can.matrixWorld, 0).normalize(); _cz.setFromMatrixColumn(can.matrixWorld, 2).normalize();
            const life = 1.55, G2 = 560; for (let i = 0; i < NW; i++) { const h = wH[i]; const on = h[3] < g.can.pour; let tau = (((S.t / life + h[0]) % 1) + 1) % 1 * life; const sp = 300 + 150 * h[1], sd = (h[2] - .5) * 330, upv = 60 * (h[0] - .3);
                for (let e = 0; e < 2; e++) { const tt = Math.max(0, tau - e * .04); const o = i * 6 + e * 3;
                  wPos[o] = _c0.x + (_cx.x * sp + _cz.x * sd) * tt; wPos[o + 1] = on ? _c0.y + (_cx.y * sp + upv) * tt - .5 * G2 * tt * tt : -500; wPos[o + 2] = _c0.z + (_cx.z * sp + _cz.z * sd) * tt; }
                if (wPos[i * 6 + 1] < 2) { wPos[i * 6 + 1] = wPos[i * 6 + 4] = -500; } }
            wGeo.attributes.position.needsUpdate = true; }
          ikArm(gArms[0], g.armSwap ? R : L, g.pinch || 0); ikArm(gArms[1], g.armSwap ? L : R, g.pinch || 0);
          if (g.plug) { plug.position.set(g.plug.x, g.plug.y, g.plug.z); _gT.set(g.plug.x, g.plug.y + 26, g.plug.z); _gE.set(g.plug.hx, g.plug.hy, g.plug.hz); gSeg(chain, _gT, _gE); } }
        const q = S.tw; tw.visible = !!(q && q.on); if (tw.visible) { tw.position.set(q.x, q.y, q.z); const gp = 1.08 + 1.7 * q.open; twB.forEach((m: any, i: number) => { const sx = i ? 1 : -1; m.position.set(sx * gp, 0, 0); m.rotation.z = sx * Math.atan((gp - .7) / 80); }); } }

      // shared uniforms
      U.crash.value = S.crash; U.uT.value = S.t; U.grow.value = S.grow; U.bounce.value = S.bounce; U.env.value = S.env; U.tower.value = S.tower; U.guys.value = S.guys; U.wired.value = S.wired;
      U.lit.value = S.lit; U.clap.value = S.clap; U.hk.value = S.hk; U.fuse.value = S.fuse; U.gwave.value = S.gwave; U.clapX.value = S.clapX; U.love.value = S.love; U.flash.value = S.flash; U.sq.value = S.sq; U.eq.value = S.eq || 0; U.kamp.value = S.kamp || 0; if (S.kr) U.kr.value.set(S.kr[0], S.kr[1], S.kr[2], S.kr[3]); vinyl.visible = (S.vinyl || 0) > .01; vinyl.material.uniforms.op.value = S.vinyl || 0; stylePass.enabled = (S.style || 0) > 0 || (S.tiles || 1) > 1; stylePass.uniforms.tiles.value = S.tiles || 1; stylePass.uniforms.tick.value = S.tick || 0; if (STARS) STARS.visible = !((S.style === 2 || S.style === 3) && !(S.tiles > 1)); stylePass.uniforms.mode.value = S.style || 0; stylePass.uniforms.modeB.value = S.styleB || 0; stylePass.uniforms.xf.value = S.styleX ?? 1; stylePass.uniforms.k.value = S.styleK ?? 1; stylePass.uniforms.split.value = S.split || 0; U.lift.value = S.float || 0; U.flip.value = S.flip || 0; U.look.value = S.look || 0; U.drain.value = S.drain || 0; U.dusk.value = S.dusk; U.tot.value = S.tot; U.weird.value = S.weird;
      U.sun.value.set(S.sun[0], S.sun[1], S.sun[2]); U.m1.value.set(S.m1[0], S.m1[1], .118 * S.m1[3], S.m1[2]); U.m2.value.set(S.m2[0], S.m2[1], .104 * S.m2[3], S.m2[2]);
      const sx = mix(S.sun[0], 0, S.tot), sy = mix(S.sun[1], 0, S.tot);
      V.copy(sunPos).addScaledVector(right, sx * QUAD / 2).addScaledVector(upQ, sy * QUAD / 2).normalize(); U.sunDir.value.copy(V);
      water.material.uniforms.sunDirection.value.copy(V); back.position.copy(V).multiplyScalar(100); back.intensity = .13 * Math.max(S.tot, S.sun[2]);
      water.material.uniforms.sunColor.value.setHex(0xffe0a8).multiplyScalar(Math.max(S.tot, S.sun[2] * .8));
      corona.lookAt(camera.position);
      // ocean
      water.visible = S.level > -45.5; water.position.y = S.level; seabed.visible = S.level < -.5; water.material.uniforms.time.value = S.waterT; water.material.uniforms.distortionScale.value = 3.0 * S.wave;
      wet.visible = S.wet > .5 && camera.position.y < 90 && camera.position.z < 700; wet.material.uniforms.time.value = S.t * .2;
      // the dot, rain
      dot.visible = dotBase.visible = S.dot > .5; dot.scale.setScalar(1 + .10 * (S.kick || 0)); dotL.intensity = 2600 * S.dot * S.grow; rainMat.uniforms.rt.value = S.rainT; rainMat.uniforms.amt.value = S.rain;
      // traffic lights: slide in from the kerbs, bonk in the middle, then all three lamps flash
      { const k = S.tl, z = 318, lean = S.tlHit * .16; tlA.visible = tlB.visible = S.tlOn > .5; const fl = S.tlFlash || 0; tlA.scale.setScalar(1.5); tlB.scale.setScalar(1.5);
        const fy = (S.float || 0); tlA.position.set(-9.6 + 9.0 * k, GROUND_Y + fy * 2.2, z); tlB.position.set(9.6 - 9.0 * k, GROUND_Y + fy * 3.1, z); tlA.rotation.set(fy * .5, 0, -lean - fy * .4); tlB.rotation.set(-fy * .3, 0, lean + fy * .6);
        [tlA, tlB].forEach((g, gi) => g.userData.lamps.forEach((l: any, i: number) => { const on = S.tlHit > 0 ? (Math.floor(S.t * 2.4) + i + gi) % 2 === 0 : (i === (gi === 0 ? 2 : 0)); l.material.color.copy(l.userData.c).multiplyScalar((on ? 3.2 : .06) + fl * 10); })); tlL.intensity = 1600 * fl; tlL.position.set(0, GROUND_Y + 6, z); }
      // pigeons: a ring over the avenue; with gravity off they stop flapping and drift up, tumbling
      birds.visible = S.birds > .5; if (birds.visible) for (let i = 0; i < NB; i++) { const ph = i / NB * 6.2832, r = 20 + 9 * Math.sin(i * 2.4), sp = .9 + .25 * Math.sin(i * 1.7);
        const sk = S.spinner || 0; const a = sk > .5 ? ph - S.t * 2.2 : ph + S.birdT * sp; const fl = S.birdFloat; const rr = sk > .5 ? 21 : r;
        O.position.set(Math.cos(a) * rr, sk > .5 ? 36 : 34 + 5 * Math.sin(i * 3.1) + 3 * Math.sin(a * 2 + i) + fl * (10 + 6 * Math.sin(i * 1.3)), 318 + Math.sin(a) * rr * (sk > .5 ? 1 : .8));
        O.rotation.set(fl * Math.sin(i * 5.1 + S.t * .7) * 1.4, -a, .35 + fl * (S.t * .5 + i)); const flap = fl > .5 ? 1 : .55 + .45 * Math.sin(S.birdT * 16 + i * 2); const tail = sk > .5 ? .35 + 1.5 * Math.pow(((i / NB - S.t * 1.25) % 1 + 1) % 1, 2.2) : 1; O.scale.set(2.6 * tail, 2.6 * flap * tail, 2.6 * tail); if (sk > .5) { camera.getWorldDirection(SPD); SPR.crossVectors(SPD, camera.up).normalize(); SPU.crossVectors(SPR, SPD);
          O.position.copy(camera.position).addScaledVector(SPD, 62).addScaledVector(SPU, 5.5).addScaledVector(SPR, Math.cos(a) * 10.5).addScaledVector(SPU, Math.sin(a) * 10.5);
          O.quaternion.copy(camera.quaternion); O.rotateX(Math.PI / 2); O.rotateY(-a + Math.PI / 2); const tl2 = .30 + 1.25 * Math.pow(((i / NB + S.t * 1.25) % 1 + 1) % 1, 2.4); O.scale.set(1.5 * tl2, 1.5 * tl2, 1.5 * tl2); }
        O.updateMatrix(); birds.setMatrixAt(i, O.matrix); }
      birds.instanceMatrix.needsUpdate = true;
      // fireworks: nine white-gold bursts, one per half beat
      { fw.visible = S.fire >= 0 && S.fire < 5.2; if (fw.visible) { for (let b = 0; b < 9; b++) { const age = S.fire - b * .245, c = fwC[b];
          for (let i = 0; i < 110; i++) { const j = b * 110 + i, d = fwDirs[j]; if (age < 0 || age > 2.4) { fwPos[j * 3 + 1] = -9999; continue; }
            const e = 1 - Math.exp(-2.6 * age), rad = c[3] * d[3] * e; fwPos[j * 3] = c[0] + d[0] * rad; fwPos[j * 3 + 1] = c[1] + d[1] * rad - 14 * age * age; fwPos[j * 3 + 2] = c[2] + d[2] * rad;
            const br = Math.max(0, 1 - age / 2.2) * (2.4 + 1.2 * Math.sin(j * 7.7 + age * 30)) * (age < .12 ? 2 : 1); fwCol[j * 3] = br; fwCol[j * 3 + 1] = br * (b % 2 ? .84 : .93); fwCol[j * 3 + 2] = br * (b % 2 ? .55 : .80); } }
          fwG.attributes.position.needsUpdate = true; fwG.attributes.color.needsUpdate = true; } }
      // causeway
      { const c = Math.max(.0005, S.cause), L = LEN * c; deck.visible = S.cause > 0; ramp.visible = S.cause > 0; deck.scale.z = L; deck.position.set(0, 1.25, Z0 + L / 2); deckT.repeat.set(1, L / 5);
        const n = Math.floor(czs.length * Math.min(1, c * LEN / (PIER_Z - 12 - Z0))) * 2; cPosts.count = cBulbs.count = Math.min(czs.length * 2, n); cFar.geometry.setDrawRange(0, Math.min(czs.length * 2, n)); pylons.visible = S.cause > .98; }
      // the car
      { const c = S.car; car.visible = c.vis > .5; car.position.set(c.x, c.y, c.z); E.set(c.pitch || 0, c.yaw, c.roll || 0, 'YXZ'); car.quaternion.setFromEuler(E); car.scale.setScalar(c.s ?? 1);
        wheels.forEach((w) => { w.rotation.x = c.spin || 0; });
        const fwd = V.set(Math.sin(c.yaw), 0, Math.cos(c.yaw)); kT.position.set(c.x, c.y + .2, c.z); key.position.set(c.x - 9.3, c.y + 7.6, c.z + 5.5); fill.position.set(c.x + 8.7, c.y + 2.6, c.z + 9.5);
        hl.position.set(c.x + fwd.x * 2.2, c.y + .65, c.z + fwd.z * 2.2); hT.position.set(c.x + fwd.x * 26, c.y - .2, c.z + fwd.z * 26); hl.visible = key.visible = fill.visible = car.visible;
        carDot.visible = car.visible; carDot.position.set(c.x, c.y + 1.0, c.z);
        // Claude: at the wheel (left seat), or standing by the car
        const b = S.bot || { mode: 'drive' }; bot.visible = car.visible && b.mode !== 'none';
        if (b.mode === 'stand') { bot.position.set(b.x, b.y, b.z); bot.rotation.set(0, b.yaw, 0); bot.scale.setScalar(1.12); }
        else { V.set(.37, -.02, -.12).applyQuaternion(car.quaternion); bot.position.set(c.x + V.x, c.y + V.y, c.z + V.z); bot.quaternion.copy(car.quaternion); bot.scale.setScalar(.72 * (c.s ?? 1)); }
        botHead.rotation.set(b.nod || 0, b.head || 0, 0); }
      bloom.strength = S.crash > .5 ? .08 : .2 + .1 * S.clap;
      comp.render();
      return { sun: project(sunPos.x + right.x * sx * QUAD / 2, sunPos.y + upQ.y * sy * QUAD / 2, sunPos.z + upQ.z * sy * QUAD / 2), car: project(S.car.x, S.car.y + .6, S.car.z) };
    },
  };
}
const mix = (a: number, b: number, k: number) => a + (b - a) * k;
