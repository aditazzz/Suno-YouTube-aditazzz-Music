// GLSL for the Living Earth film layers. The planet is ONE full-screen pass: per pixel, an orthographic ray-sphere hit,
// lat/lon -> NASA maps, regraded into the bioluminescent look (every grade.ts knob is a uniform). Projection = camera.ts.
import { NOISE } from '../../glsl/noise';
export const QUAD_VERT = /* glsl */ `
varying vec2 vP; varying vec2 vUv;
void main(){ vUv = uv; vP = position.xy; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
export const PLANET_FRAG = /* glsl */ `
precision highp float;
varying vec2 vP;
uniform sampler2D uDay; uniform sampler2D uNight; uniform sampler2D uRivers; uniform sampler2D uData; uniform sampler2D uClouds;
uniform vec2 uC; uniform float uR; uniform float uLat; uniform float uLon; uniform float uRoll; uniform float uPx; uniform float uT;
uniform vec3 uSun;
uniform float uGlow; uniform float uViolet; uniform float uDaySide; uniform float uHisWarm; uniform float uHerCyan; uniform float uRiv;
uniform float uRivPulse; uniform float uCoast; uniform float uForest; uniform float uOcean; uniform float uCloudsK; uniform float uAtmos;
uniform float uFlare; uniform float uKick; uniform float uHisOff; uniform float uAurora;
uniform float uSunWarm; uniform float uLux; uniform float uCapil; uniform float uSeam; uniform float uHaloWide; uniform vec4 uGold;
uniform vec3 uHer; uniform vec3 uVio; uniform vec3 uHis;
uniform vec4 uPulse[8]; uniform float uPulseS[8];
${NOISE}
const float PI = 3.14159265;
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec3 geoDir(float la, float lo){ return vec3(cos(la) * sin(lo), sin(la), cos(la) * cos(lo)); }
void main(){
  vec2 q = (vP - uC) / uR;
  float cr = cos(uRoll), sr = sin(-uRoll);
  vec2 p = vec2(cr * q.x - sr * q.y, sr * q.x + cr * q.y);
  float d = length(p);
  float px = uPx / uR;
  vec3 atmC = mix(uHer, uVio, 0.45 * uViolet);
  vec3 L = normalize(uSun);
  vec3 col = vec3(0.0); float alpha = 0.0;
  if (d < 1.0 + 2.0 * px) {
    float z = sqrt(max(0.0, 1.0 - d * d));
    vec3 n = vec3(p, z);
    float cl = uLat;
    vec3 v = vec3(n.x, n.y * cos(cl) + n.z * sin(cl), -n.y * sin(cl) + n.z * cos(cl));
    float lat = asin(clamp(v.y, -1.0, 1.0));
    float lon = uLon + atan(v.x, v.z);
    vec3 w = geoDir(lat, lon); // fixed to her body: noise uses this so patterns turn with her
    vec2 uv = vec2(fract(lon / (2.0 * PI) + 0.5), lat / PI + 0.5);
    vec2 gx = dFdx(uv), gy = dFdy(uv); gx.x -= floor(gx.x + 0.5); gy.x -= floor(gy.x + 0.5);
    vec3 alb = textureGrad(uDay, uv, gx, gy).rgb;
    vec4 dat = textureGrad(uData, uv, gx, gy);
    float wideWater = textureGrad(uData, uv, gx * 10.0 + vec2(0.004, 0.0), gy * 10.0 + vec2(0.0, 0.004)).g;
    vec4 rv = textureGrad(uRivers, uv, gx, gy);
    vec4 rvw = textureGrad(uRivers, uv, gx * 6.0 + vec2(0.0015, 0.0), gy * 6.0 + vec2(0.0, 0.0015));
    vec3 nl = textureGrad(uNight, uv, gx, gy).rgb;
    float cloud = textureGrad(uClouds, uv + vec2(uT * 0.0004, 0.0), gx, gy).r;
    float near = smoothstep(2.5, 7.0, uR);
    float mu = dot(n, L);
    float day = smoothstep(-0.06, 0.22, mu) * uDaySide;
    float water = smoothstep(0.35, 0.65, dat.g);
    float lum = dot(alb, vec3(0.3, 0.55, 0.15));
    // night base: a dark world, not a void: continents faintly readable in deep teal, oceans deep blue (violet-leaning)
    vec3 landN = mix(vec3(0.004, 0.010, 0.016), vec3(0.016, 0.045, 0.055), smoothstep(0.02, 0.3, lum));
    vec3 seaN = mix(vec3(0.002, 0.008, 0.03), vec3(0.008, 0.005, 0.034), uViolet * 0.6);
    vec3 base = mix(landN, seaN, water);
    if (near > 0.0) base *= 1.0 + 0.5 * near * fbm3(w * 900.0);
    vec3 sunC = mix(vec3(1.0, 0.45, 0.2), vec3(1.0, 0.96, 0.9), smoothstep(0.0, 0.35, mu));
    vec3 dayCol = alb * sunC * max(mu, 0.0) * 1.4;
    vec3 Hh = normalize(L + vec3(0.0, 0.0, 1.0));
    dayCol += sunC * pow(max(dot(n, Hh), 0.0), 60.0) * water * 0.6 * step(0.0, mu);
    vec3 surf = mix(base, dayCol, day);
    // ---- her bioluminescence ----
    float acc = rv.r, wet = rv.b;
    float core = pow(smoothstep(0.18, 1.0, acc), 2.0) * 1.6 * (1.0 + 1.2 * smoothstep(0.75, 0.95, acc));
    float body = smoothstep(0.22, 0.6, rvw.r) * 0.12 + smoothstep(0.45, 0.8, rvw.r) * 0.35;
    float riv = (core + body) * (0.25 + 0.75 * smoothstep(0.05, 0.5, wet)) * (1.0 - water);
    float ph = acc * 9.0 + snoise(w * 6.0) * 2.0;
    float trav = 0.5 + 0.5 * sin(ph * 3.0 - uT * 4.0);
    float rivE = riv * (0.7 + uRivPulse * 0.8 * trav) * (1.0 + 2.2 * uKick) * uRiv;
    float coast = smoothstep(0.35, 0.95, 1.0 - abs(dat.g * 2.0 - 1.0));
    float green = smoothstep(0.01, 0.07, alb.g - max(alb.r, alb.b) * 0.92) * (1.0 - water);
    float shim = 0.55 + 0.45 * snoise(w * 30.0 + vec3(0.0, uT * 0.15, 0.0));
    float plank = pow(clamp(0.5 + 0.5 * fbm3(w * 14.0 + vec3(uT * 0.02)), 0.0, 1.0), 3.0);
    float shelf = water * (1.0 - smoothstep(0.55, 0.98, wideWater));
    float clum = dot(nl, vec3(0.3, 0.5, 0.2));
    float on = uHisOff > 0.001 ? step(uHisOff, hash12(floor(uv * vec2(900.0, 450.0)))) : 1.0;
    vec3 his = uHis * clum * 2.2 * uHisWarm * on;
    vec3 hers = uHer * clum * 1.6 * uHerCyan * (1.0 + 0.8 * uHisOff);
    vec3 E = uHer * rivE
      + mix(uHer, uVio, 0.6 * uViolet) * coast * 0.16 * uCoast
      + vec3(0.1, 1.0, 0.7) * green * shim * 0.2 * uForest
      + mix(uHer, uVio, 0.75 * uViolet) * plank * (0.12 + shelf) * 0.4 * uOcean
      + hers;
    float ringAcc = 0.0;
    for (int i = 0; i < 8; i++) {
      if (uPulseS[i] <= 0.0) continue;
      float age = uT - uPulse[i].z; if (age < 0.0) continue;
      float ang = acos(clamp(dot(w, geoDir(uPulse[i].x, uPulse[i].y)), -1.0, 1.0));
      float ring = exp(-pow((ang - age * uPulse[i].w) / 0.035, 2.0)) * exp(-age * 0.7) * uPulseS[i];
      E += mix(uHer, vec3(0.1, 1.0, 0.7), 0.5) * ring * (0.3 + 1.6 * (riv + green)); ringAcc += ring;
    }
    if (near > 0.0) E += uHer * pow(max(snoise(w * 2600.0), 0.0), 6.0) * near * 2.5 * (1.0 - water); // grains of sand catch her light
    E *= uGlow * (1.0 - 0.75 * day);
    E += uHer * uFlare * (0.25 + riv + coast * 0.5);
    vec3 Lc = his * (1.0 - day);
    float cv = smoothstep(0.25, 0.85, cloud) * uCloudsK;
    vec3 cloudCol = mix(vec3(0.008, 0.016, 0.03) + 0.08 * E, sunC * max(mu, 0.0) * 1.2, day);
    col = surf + E + Lc;
    col = mix(col, cloudCol + 0.5 * E, cv * 0.5);
        col += atmC * pow(1.0 - z, 4.0) * 0.28 * uAtmos * (0.5 + 0.5 * uGlow);
    col += sunC * pow(1.0 - z, 4.0) * smoothstep(-0.1, 0.4, mu) * 0.45 * uAtmos;

    if (uLux > 0.001) { // ---- the PROOF look (grade.lux; a GLSL port of the approved mockup recipe, pitch_mockups/le_lib.py shade) ----
      const vec3 BIOG = vec3(0.25, 1.0, 0.55); const vec3 TEAL = vec3(0.02, 0.50, 0.55); const vec3 GOLD = vec3(1.0, 0.60, 0.22);
      const vec3 ROSE = vec3(1.0, 0.32, 0.38); const vec3 INDIGO = vec3(0.14, 0.20, 1.0); const vec3 MAG = vec3(1.0, 0.22, 0.62);
      float ds = uDaySide, sd = mu * 1.5;
      float nightK = mix(1.0, smoothstep(0.10, -0.12, sd), ds);
      float dayw = smoothstep(-0.08, 0.30, sd) * ds;
      float twi = exp(-pow(sd / 0.11, 2.0)) * ds;
      float wake = mix(1.0, smoothstep(-0.03, -0.30, sd), ds);
      float foot = px / max(z, 0.10);                      // one pixel's footprint on her surface (her radii)
      vec2 tx = vec2(1.0 / 4096.0, 1.0 / 2048.0);
      float eR = textureGrad(uData, uv + vec2(tx.x, 0.0), gx, gy).r, eL = textureGrad(uData, uv - vec2(tx.x, 0.0), gx, gy).r;
      float eU = textureGrad(uData, uv + vec2(0.0, tx.y), gx, gy).r, eD = textureGrad(uData, uv - vec2(0.0, tx.y), gx, gy).r;
      float relief = clamp(0.5 + ((eL - eR) + (eU - eD)) * 22.0, 0.0, 1.0);
      float nMot = 0.5 + 0.5 * fbm3(w * 9.0 + 2.0);
      float nBig = 0.5 + 0.5 * fbm3(w * 2.2 + 7.0);
      float nFine = 0.5 + 0.5 * snoise(w * 240.0) * (1.0 - smoothstep(0.0015, 0.006, foot));
      float nCl = 0.5 + 0.5 * fbm3(w * 22.0 + vec3(uT * 0.012, 0.0, uT * 0.008));
      vec3 wp = w + 0.012 * vec3(snoise(w * 14.0), snoise(w * 14.0 + 5.0), snoise(w * 14.0 + 9.0));
      // rivers: the flow map with a small organic wiggle, crisp thresholds; big rivers get a white-hot trunk
      vec2 wig = vec2(snoise(w * 85.0), snoise(w * 85.0 + vec3(4.0))) * 0.00045 * smoothstep(0.7, 1.8, uR);
      vec4 rv2 = textureGrad(uRivers, uv + wig, gx, gy);
      float flow = rv2.r, nearR = rv2.g, wet2 = rv2.b;
      // the flow map IS a dendritic network (every stream a thin line, brighter = more water): keep the lines only (flow
      // against its own local average), faint for small streams, bright for the great rivers
      float avg = rvw.r;
      float lineF = smoothstep(0.015, 0.11, flow - avg * 0.86);
      float hier = pow(smoothstep(0.28, 0.64, flow), 2.0);
      float core2 = lineF * (0.07 + 0.93 * hier) * (0.35 + 0.65 * wet2);
      float trunk = smoothstep(0.50, 0.72, flow) * lineF;
      float shal = clamp((dat.b - 0.863) / 0.12, 0.0, 1.0) * water;
      // capillaries: thin ridged lines at five scales, each fading out before it would go below a pixel
      float c1 = pow(1.0 - abs(snoise(wp * 34.0)), 16.0) * (1.0 - smoothstep(0.0020, 0.0060, foot));
      float c2 = pow(1.0 - abs(snoise(wp * 95.0 + 3.0)), 14.0) * (1.0 - smoothstep(0.0008, 0.0024, foot));
      float c3 = pow(1.0 - abs(snoise(wp * 260.0 + 11.0)), 12.0) * (1.0 - smoothstep(0.0003, 0.0009, foot));
      float c4 = pow(1.0 - abs(snoise(wp * 720.0 + 23.0)), 12.0) * (1.0 - smoothstep(0.00011, 0.00033, foot));
      float c5 = pow(1.0 - abs(snoise(wp * 2000.0 + 31.0)), 10.0) * (1.0 - smoothstep(0.00004, 0.00012, foot));
      float capMask = (1.0 - water) * (0.10 + 0.55 * smoothstep(0.08, 0.34, avg) + 0.14 * green);
      float capv = (c1 * 0.16 + c2 * 0.30 + c3 * 0.44 + c4 * 0.40 + c5 * 0.34) * capMask * uCapil;
      float vhue = smoothstep(0.42, 0.70, nMot * 0.5 + nBig * 0.5);
      vec3 vcol = mix(uHer, BIOG * 0.55 + uHer * 0.45, vhue);
      float ph2 = flow * 9.0 + snoise(w * 6.0) * 2.0;
      float trav2 = 0.5 + 0.5 * sin(ph2 * 3.0 - uT * 4.0);
      float pk = (0.72 + uRivPulse * 0.7 * trav2) * (1.0 + 1.8 * uKick);
      vec3 veins = (vcol * (core2 * 0.80 + trunk * 0.95) + vec3(0.9, 1.0, 1.0) * trunk * trunk * 0.06) * pk * uRiv * 0.80
                 + TEAL * avg * 0.018 * (0.3 + wet2) + vcol * capv * (0.55 + 0.9 * uKick + 0.5 * uRivPulse * trav2);
      veins *= 1.0 - water;
      if (uGold.w > 0.001) { // his gold running up her rivers from one place: only where the map has a river; she relights behind it
        float ga = acos(clamp(dot(w, geoDir(uGold.x, uGold.y)), -1.0, 1.0));
        float passed = smoothstep(uGold.z + 0.03, uGold.z - 0.12, ga);
        veins *= mix(1.0, mix(0.22, 1.0, passed), min(uGold.w, 1.0));
        float fr = exp(-pow((ga - uGold.z) / 0.028, 2.0)) + 0.55 * exp(-pow((ga - uGold.z + 0.11) / 0.03, 2.0)) + 0.3 * exp(-pow((ga - uGold.z + 0.22) / 0.035, 2.0));
        vec3 gc = mix(vec3(1.0, 0.62, 0.22), uHer, smoothstep(0.22, 0.62, uGold.z));
        veins += gc * fr * uGold.w * (lineF * (0.25 + 2.6 * hier) + trunk * 2.4) * (1.0 - water);
      }
      vec3 fcol = uVio * 1.5 * smoothstep(0.38, 0.62, nMot) + INDIGO * 1.1 * smoothstep(0.62, 0.36, nMot) + MAG * 1.3 * smoothstep(0.60, 0.80, nMot * 0.5 + nBig * 0.5);
      fcol = mix(vec3(0.03, 0.55, 0.60), fcol, min(1.0, 0.25 + uViolet));
      vec3 forest = fcol * green * (0.10 + 0.42 * nFine) * (0.5 + nBig) * 0.22 * uForest;
      float plk = smoothstep(0.58, 0.95, 0.5 + 0.5 * fbm3(wp * 13.0 + vec3(uT * 0.01))) * smoothstep(0.40, 0.70, nBig) * water * (0.10 + 0.6 * shal);
      vec3 sea = ((TEAL * 0.75 + uHer * 0.14) * pow(shal, 1.4) * (0.45 + 1.1 * nMot) + mix(uHer * 0.5 + TEAL * 0.5, uVio, 0.45 * uViolet) * plk * 1.5) * 0.9 * uOcean;
      float mf = smoothstep(0.42, 0.78, nCl) * smoothstep(0.10, 0.34, avg) * (1.0 - water);
      vec3 mistL = (TEAL * 0.40 + uVio * 0.45) * mf * 0.07;
      vec3 life = (veins + forest + sea + mistL) * wake * uGlow;
      life += mix(uHer, BIOG, 0.5) * ringAcc * (2.2 * (core2 + trunk + capv) + 0.25 * lineF) * wake;
      life += (uHer * 1.2 + 0.25) * exp(-pow((sd + 0.105) / 0.045, 2.0)) * ds * (core2 * 1.2 + trunk * 1.6 + 0.03 * avg) * uGlow;
      life += uHer * uFlare * (0.06 + core2 + trunk + capv + 0.08 * green + 0.15 * shal);
      vec3 nls = pow(nl, vec3(1.0 / 2.2));
      float nlw = clamp(((nls.r - 0.5 * nls.b) * 255.0 - 6.0) / 150.0, 0.0, 1.0);
      vec3 cities = (uHis * pow(nlw, 1.25) * 2.6 + vec3(1.0, 0.86, 0.66) * smoothstep(0.55, 1.0, nlw) * 2.2) * uHisWarm * on * nightK
                  + uHer * nlw * 1.2 * uHerCyan * (1.0 + 0.8 * uHisOff) * wake * uGlow;
      float lum2 = pow(dot(alb, vec3(0.3333)), 0.6);
      vec3 bLand = 0.62 * (vec3(0.016, 0.026, 0.050) + uVio * 0.012 * uViolet * smoothstep(0.4, 0.7, nMot)) * (0.55 + 1.5 * lum2) * (0.45 + 1.1 * relief) * (0.8 + 0.4 * nFine);
      vec3 bSea = mix(vec3(0.004, 0.017, 0.030), vec3(0.010, 0.010, 0.036), 0.5 * uViolet) * (0.8 + 0.6 * nBig) + vec3(0.0, 0.012, 0.016) * shal;
      vec3 base2 = mix(bLand, bSea, water);
      float sdc = clamp(sd, 0.0, 1.0);
      vec3 sunlit = alb * mix(vec3(0.80, 0.95, 1.12), vec3(1.22, 0.92, 0.60), uSunWarm) * (0.10 + 1.25 * pow(sdc, 0.75)) * 1.25;   // her day side leans cool: warm is his
      vec3 warm = mix(vec3(1.0), GOLD, twi * 0.6);
      float spec2 = pow(max(dot(n, Hh), 0.0), 90.0) * water * clamp(sd * 6.0, 0.0, 1.0);
      vec3 dayc = sunlit * warm * dayw + GOLD * spec2 * 2.2 * ds;
      vec3 dusk = (ROSE * 0.035 + uVio * 0.02) * exp(-pow((sd + 0.10) / 0.10, 2.0)) * (0.6 + lum2) * ds;
      vec3 s2 = base2 * (1.0 - dayw) + dayc + dusk + life + cities;
      // clouds: a dark blue veil at night, lit from below by whatever glows under it; pink-gold on the line; white by day
      float cm = clamp(smoothstep(0.30, 0.82, cloud + (nCl - 0.5) * 0.55 * smoothstep(0.08, 0.5, cloud)) * uCloudsK * 2.4, 0.0, 1.0);
      vec3 under = vcol * smoothstep(0.10, 0.45, avg) * 0.09 * (0.8 + uKick) * wake * uGlow;
      vec3 cN = vec3(0.026, 0.040, 0.075) + uVio * 0.012 * uViolet + under;
      vec3 cD = mix(vec3(1.0, 0.98, 0.95), vec3(1.0, 0.80, 0.56), uSunWarm) * (0.12 + 0.98 * pow(sdc, 0.6));
      vec3 cL = (GOLD * 0.9 + ROSE * 0.35) * twi * 0.75 * smoothstep(-0.16, 0.02, sd);
      vec3 ccol = cN * (1.0 - dayw) + cD * dayw * warm + cL;
      s2 = s2 * (1.0 - cm * (0.78 - 0.25 * nightK)) + ccol * cm;
      s2 += (GOLD * exp(-pow((sd - 0.04) / 0.060, 2.0)) + ROSE * 0.55 * exp(-pow((sd + 0.03) / 0.055, 2.0)) + uVio * 0.45 * exp(-pow((sd + 0.10) / 0.075, 2.0))) * uSeam * ds;
      float rim2 = pow(1.0 - z, 3.2);
      vec3 acol = mix(vec3(0.20, 0.50, 1.0), vec3(1.0, 0.56, 0.24), uSunWarm) * dayw * 1.1 + (GOLD * 0.9 + ROSE * 0.3) * twi * 0.24
                + mix(vec3(0.012, 0.065, 0.09), uVio * 0.07, 0.3 * uViolet) * nightK * (1.0 + 2.0 * uGlow);
      s2 += (acol * rim2 * 1.15 + acol * 0.03 * (1.0 - nightK)) * uAtmos;
      col = mix(col, s2, uLux);
    }
    alpha = 1.0 - smoothstep(1.0 - px, 1.0 + px, d);
    col *= alpha;
  }
  // her air outside the disk (premultiplied, additive): a tight bright rim, a wide soft halo, brighter toward the sun
  float h = max(d - 1.0, 0.0);
  vec2 sd = normalize(L.xy + vec2(1e-4)); vec2 pd = normalize(p + vec2(1e-5));
  float side = 0.5 + 0.5 * dot(pd, sd);
  float halo = (exp(-h / 0.010) * 0.42 + exp(-h / 0.05) * 0.09) * uAtmos * smoothstep(1.0 - 2.0 * px, 1.0, d);
  vec3 haloC = atmC * (0.35 + 0.65 * uGlow) + uFlare * uHer * 0.6 + vec3(1.0, 0.7, 0.45) * side * side * smoothstep(-0.6, 0.2, -L.z) * 0.8;
  float ang = atan(p.y, p.x);
  float ray = 0.5 + 0.5 * snoise(vec3(ang * 46.0, uT * 0.25, 1.7)); float band = 0.5 + 0.5 * snoise(vec3(ang * 4.0, uT * 0.12, 4.2));
  float aur = uAurora * exp(-h / (0.035 + 0.04 * band)) * smoothstep(0.0, 0.012, h) * pow(ray, 2.5) * band * 0.9;
  vec3 haloOut = halo * haloC;
  if (uLux > 0.001) { // the PROOF limb: thin, coloured by the sun where the ray grazes her (blue day, gold/rose line, deep teal night) + a detached airglow line
    float sq = dot(vec3(pd, 0.0), L) * 1.5, dsq = uDaySide;
    float dq = smoothstep(-0.10, 0.30, sq) * dsq, tq = exp(-pow(sq / 0.13, 2.0)) * dsq, nq = mix(1.0, smoothstep(0.10, -0.12, sq), dsq);
    vec3 lcol = mix(vec3(0.22, 0.52, 1.0), vec3(1.0, 0.58, 0.24), uSunWarm) * dq * 1.4 + (vec3(1.0, 0.60, 0.22) * 1.3 + vec3(1.0, 0.32, 0.38) * 0.5) * tq * 0.20
              + mix(vec3(0.02, 0.11, 0.14), uVio * 0.10, 0.35 * uViolet) * nq * (0.5 + 1.0 * uGlow);
    float limb = exp(-h / (0.0034 + 1.1 * px)) * 0.72 + exp(-h / (0.030 + 2.0 * px)) * 0.16;
    float air = exp(-pow((h - 0.016) / 0.0028, 2.0)) * nq * 0.10 * (0.4 + uGlow) * (1.0 - smoothstep(0.001, 0.003, px));
    vec3 halo2 = (lcol * limb + vec3(0.25, 1.0, 0.55) * 0.8 * air) * uAtmos * smoothstep(1.0 - 2.0 * px, 1.0, d);
    float hS = h * uR;                                    // screen units: her own wide soft light (the far dot in its room)
    halo2 += uHer * uHaloWide * (0.016 / pow(1.0 + hS * hS / 0.30, 1.6) + 0.10 / pow(1.0 + hS * hS / 0.0115, 2.2)) * (1.0 - alpha);
    halo2 += uHer * uFlare * (exp(-h / 0.06) * 0.22 + exp(-h / 0.35) * 0.05) * (1.0 - alpha);
    haloOut = mix(haloOut, halo2, uLux);
  }
  col += haloOut + max(aur, 0.0) * mix(vec3(0.2, 1.0, 0.55), uVio, 0.5 + 0.5 * sin(ang * 3.0 + uT * 0.2));
  gl_FragColor = vec4(col, alpha);
}`;
export const POINTS_VERT = /* glsl */ `
attribute float aSize; attribute vec3 aColor; attribute float aOcc; attribute float aDepth;
uniform vec2 uPar; uniform float uPxScale; uniform vec2 uC; uniform float uR; uniform float uGain;
varying vec3 vCol;
void main(){
  vec3 p = position; p.xy += uPar * aDepth;
  float occ = 1.0;
  if (aOcc > 0.5) { float dd = length(p.xy - uC) / max(uR, 1e-4); occ = smoothstep(0.995, 1.05, dd); }
  vCol = aColor * occ * uGain;
  gl_PointSize = aSize * uPxScale;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(p.xy, 0.0, 1.0);
}`;
export const POINTS_FRAG = /* glsl */ `
varying vec3 vCol;
void main(){ vec2 q = gl_PointCoord - 0.5; float r2 = dot(q, q) * 4.0; float a = exp(-r2 * 9.0) + 0.12 * exp(-r2 * 2.5); if (a < 0.004 || r2 > 1.0) discard; gl_FragColor = vec4(vCol * a, 1.0); }`;
export const SPARK_FRAG = /* glsl */ `
varying vec2 vUv; uniform vec3 uCol; uniform float uOcc; uniform vec2 uC; uniform float uR; varying vec2 vP;
void main(){ vec2 q = vUv - 0.5; float r = length(q) * 2.0; float a = exp(-r * r * 60.0) * 1.6 + exp(-r * r * 9.0) * 0.35 + exp(-r * 3.2) * 0.12;
  a *= 1.0 - smoothstep(0.85, 1.0, r);
  // a soft 4-point glint on the core
  a += (exp(-abs(q.x) * 90.0) * exp(-abs(q.y) * 7.0) + exp(-abs(q.y) * 90.0) * exp(-abs(q.x) * 7.0)) * 0.25;
  gl_FragColor = vec4(uCol * a, 1.0); }`;
export const SPARK_VERT = /* glsl */ `
varying vec2 vUv; varying vec2 vP;
void main(){ vUv = uv; vec4 w = modelMatrix * vec4(position, 1.0); vP = w.xy; gl_Position = projectionMatrix * viewMatrix * w; }`;
export const MIST_FRAG = /* glsl */ `
precision highp float;
varying vec2 vP; uniform float uT; uniform float uMist; uniform vec3 uCol; uniform vec2 uPar;
${NOISE}
void main(){ float n = fbm3(vec3(vP * 0.8 + uPar * 0.6 + vec2(uT * 0.02, 0.0), uT * 0.03)); float m = smoothstep(-0.1, 0.75, n) * uMist;
  gl_FragColor = vec4(uCol * m * 0.10, 1.0); }`;
export const FINAL_FRAG = /* glsl */ `
uniform sampler2D tDiffuse; uniform float uVig; uniform float uGrain; uniform float uT; uniform float uAspect; varying vec2 vUv;
void main(){ vec4 c = texture2D(tDiffuse, vUv); vec2 q = (vUv - 0.5) * vec2(uAspect, 1.0);
  c.rgb *= 1.0 - uVig * smoothstep(0.35, 1.25, length(q) * 1.15);
  float g = fract(sin(dot(vUv * 1000.0 + vec2(uT * 37.0, uT * 11.0), vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
  c.rgb += g * uGrain * (0.15 + c.rgb); gl_FragColor = vec4(max(c.rgb, 0.0), 1.0); }`;
export const FINAL_VERT = /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
