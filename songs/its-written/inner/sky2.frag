#version 300 es
precision highp float;
precision highp int;
precision highp sampler2D;
// It's Written, inside the grain: the Amazon at night, seen as light. One flight: down along a river of gold light,
// through the canopy, forward between the leaves over dark water, then lifted up and out on the wind.
// World: x across, y up, z = the way we fly. Ground / water y = 0, canopy top y = HC.
uniform vec2 uRes, uJit; uniform float uWeight, uSeed;
uniform vec3 uCam, uFw, uRt, uUp, uSun; uniform float uZoom, uT;
uniform sampler2D uRiv, uRivL; uniform vec4 uRivMap, uRivMapL;      // field: r = distance to the river's centre line, g = length along it, b = distance to the oxbow lakes
uniform float uLianaK, uNear, uFlyUp, uStream; uniform vec2 uAxis; uniform float uS, uCorr, uCorrB, uCone, uDense, uWaterK, uAbove, uTrunkK, uVeinK, uFocus, uLoose, uRoll;
uniform vec2 uCP, uRot;
uniform float uDream, uRoadS, uRoadK, uSky, uFly, uLift, uFlut, uGlowK, uGlowAz, uRivK;
uniform vec3 uWave;                                // wind over the canopy: front position, strength, unused
uniform vec4 uRings[8];                            // x, z, age, strength
uniform vec4 uRed; uniform float uRedK, uRedStep, uRedFront;
uniform vec4 uRib[32];                             // sky2: her red thread on the wind, a polyline in 1080p pixels from the middle of the picture (x, y, half-width, strength)
uniform float uBgAz, uFlyDY, uWind, uMist, uCanOff;
uniform vec4 uHero, uHeroA;                        // the vine's leaf we pass close: plane x, y, s, angle; visible, light head, vein light, -
uniform vec4 uDrops[4];                            // x, height, z, brightness
uniform float uCross;                              // how fast the world crosses the lens, units a second
uniform vec4 uBk, uBkP[9]; uniform vec3 uBkS, uBkD, uBkU, uBkN;   // her prints on the wet bank: (shown, print length, trail length, -); each print (along, across, foot, light); the bank's start, the way she went, up the bank, its normal
uniform vec4 uTree;                                // the great tree on the bank: axis x, axis z, the ground it stands on, shown
uniform vec4 uVine;                                // her gold in the vine: how high it has climbed (above the tree's ground), its strength, the glow at the root, -
uniform float uVth[32];                            // the vine's place round the trunk, every 0.6 of height
uniform vec3 uTdP[6], uTdC[6]; uniform vec4 uTdE[6], uTdR[6];   // its young tendrils: where each leaves the vine; the middle of the space it takes; the two upright planes it lies in; (sweep radius, coil radius, thickness, how far the light has run along it: 0..2)
uniform vec3 uFwM, uRtM, uUpM;                     // the way we look at the middle of the frame (the stars keep most of their place through the shutter: points, not rain)
uniform float uSprig, uStarK, uCeil, uMoonK;
uniform vec2 uCPA, uRotA; uniform float uXf, uXfF, uXfN;  // the other set of the same slabs of leaves (the old flight's own), how far we have changed over to the set used from 99.0 s on, and its fireflies' own height        // the turn the camera has still to make round the tree (slab shift); share of leaves that are the vine's own; stars; the roof of leaves seen from below
uniform sampler2D uHand;                           // the three answers, each a pen line: r = distance to the line (cell heights / 0.25), g = how far along the line (0..1)
uniform vec3 uHC[3], uHR[3], uHU[3];               // each answer's plane: the middle of its cell, its width and its height as vectors
uniform vec4 uHA[3], uHB[3];                       // (written up to, let go up to, brightness, curl) and (half-width of the line, fireflies 0..1, depth along the way we look, the cell is cut off right of this x)
uniform vec4 uFf[48];                              // the fireflies that gather into the first answer: place in its cell, size, brightness
uniform float uSkyOpen, uRedFig;                   // the roof of leaves has opened over us; she is a tiny figure (1) or a point (0)
out vec4 fragColor;

const float FOC = 1.05, HC = 16.0, DZ = 1.2, ZB = 15.5; const int NL = 9;
const vec3 GOLD = vec3(1.0, 0.60, 0.19), GOLDW = vec3(1.0, 0.79, 0.46);

uint hu(uint x){ x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16; return x; }
float h1(uint n){ return float(hu(n) >> 8) * (1.0/16777216.0); }
uint hc(ivec2 c, uint s){ return hu(uint(c.x)*0x9E3779B1U ^ hu(uint(c.y)*0x85EBCA77U ^ (s*0xC2B2AE3DU + 0x27d4eb2fU))); }
float vn(vec2 p){
  vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f); ivec2 c = ivec2(i);
  float a = h1(hc(c,7u)), b = h1(hc(c+ivec2(1,0),7u)), cc = h1(hc(c+ivec2(0,1),7u)), d = h1(hc(c+ivec2(1,1),7u));
  return mix(mix(a,b,f.x), mix(cc,d,f.x), f.y);
}
vec2 ppath(float s){ return vec2(0.50*sin(0.42*s) + 0.22*sin(0.97*s + 1.3), 0.10*sin(0.33*s + 0.7)); }
vec4 riv(vec2 p){ vec2 ul = (p - uRivMapL.xy)*uRivMapL.z; vec2 e = min(ul, 1.0 - ul); float w = smoothstep(0.01, 0.06, min(e.x, e.y));
  vec2 ug = (p - uRivMap.xy)*uRivMap.z; vec2 eg = min(ug, 1.0 - ug); float wg = smoothstep(0.0, 0.04, min(eg.x, eg.y));
  vec4 g = mix(vec4(99.0, 0.0, 0.0, 99.0), texture(uRiv, ug), wg); if(w <= 0.0) return g; vec4 l = texture(uRivL, ul); l.ba = g.ba; return mix(g, l, w); }

// ---------------------------------------------------------------- the river of light, on the water
// field: r = signed distance to the main channel's centre line, g = length along it, b = half-width of the nearest small stream, a = distance to its centre line
float braidK(float s){ return (1.0 - exp(-s*s/2500.0))*smoothstep(0.16, 0.48, vn(vec2(s*0.021 + 3.0, 7.5))); }   // where the river runs wide and braids
float rivW(float s){ return (1.25 + 0.55*sin(s*0.083 + 1.0) + 0.30*sin(s*0.231 + 2.0))*(1.0 + 2.0*braidK(s)); }   // the river widens and narrows
vec3 riverLight(vec2 p, float px, out float d, out float w, float air){
  vec4 r = riv(p); float sd = r.r, s = r.g; d = abs(sd); w = rivW(s); float dn = sd/w;
  float body = smoothstep(w + 0.22 + 2.0*px, w - 0.22 - 2.0*px, d);
  float bar = air*braidK(s)*smoothstep(0.42, 0.49, vn(vec2(s*0.042 + 11.0, dn*2.7 + 4.0)))*smoothstep(0.95, 0.72, abs(dn));   // sandbars: the channel braids around them
  float fine = 1.0/(1.0 + 80.0*px), mid = 1.0/(1.0 + 3.0*px);
  float fl = vn(vec2(s*0.9 - uT*1.0, d*5.0))*vn(vec2(s*2.3 - uT*1.7, d*11.0 + 3.0));        // the current, one way
  float thal = exp(-pow(d/(0.34*w + 2.0*px), 2.0));                                         // brightest where it runs deepest
  float under = mix(0.30, 0.010 + 0.95*fl*fl, fine) + 0.42*thal*(1.0 - 0.80*fine);          // under the trees: as it was
  // from the air: light ON the water. Broken glints that travel with the current, dark under the banks, bright in the open reaches
  float gl = vn(vec2(s*0.16 - uT*0.55, dn*2.6 + 1.0))*vn(vec2(s*0.47 - uT*1.1, dn*5.0 + 7.0));
  float reach = 0.40 + 0.60*smoothstep(0.30, 0.65, vn(vec2(s*0.05 + 2.0, 1.5)));
  float far = (0.03 + mix(0.30, 1.05*smoothstep(0.10, 0.36, gl), mid))*reach*smoothstep(1.02, 0.45, abs(dn));
  far = mix(far, far*(0.4 + 2.4*fl), fine) + 0.06*thal;
  float sheen = mix(under, far, air);
  float road = 1.0 + 0.75*uRoadK*smoothstep(uRoadS, uRoadS - 26.0, s);
  float head = uRoadK*exp(-pow((s - uRoadS)/(7.0 + 5.0*air), 2.0));
  vec3 c = GOLD*body*(1.0 - bar)*sheen*road*uRivK;
  c += vec3(0.020, 0.024, 0.027)*body*bar;                                                  // moonlit sand
  c += GOLD*(exp(-max(d - w, 0.0)/1.1)*0.045 + exp(-d/6.0)*0.010)*road*uRivK*(1.0 - 0.6*air);   // its light on the mist and the banks
  c += GOLD*head*body*(1.0 - bar)*0.45*uRivK;
  float tw = smoothstep(r.b + 0.10 + 1.2*px, r.b - 0.10 - 1.2*px, r.a)*clamp(r.b/max(px, 1e-4), 0.0, 1.0)*(1.0 - body);   // the streams that feed it, finer with distance
  float tn = clamp(r.a/max(r.b, 0.05), 0.0, 1.0);                                            // close up they are water too: glints, dark under their banks
  c += GOLD*0.55*tw*mix(1.0, (1.0 - 0.8*tn*tn)*(0.15 + 0.85*smoothstep(0.12, 0.40, vn(p*0.7 + vec2(uT*0.3, uT*0.5))*vn(p*1.9 - vec2(uT*0.4, 0.0)))), mid)*(0.6 + 0.4*road)*uRivK;
  return c;
}
vec3 farBG(vec3 rd){
  float az = atan(rd.x, rd.z) + uBgAz, el = max(rd.y, 0.0), da = az - uGlowAz;
  float pool = exp(-da*da/0.055)*exp(-el*8.5);                                               // the river's light, low between the trunks
  float wide = exp(-da*da/0.9)*exp(-el*3.2);
  vec3 c = vec3(0.0030, 0.0040, 0.0036);
  vec3 g = GOLD*(0.008*exp(-el*4.0) + 0.040*wide + 0.50*pool) + GOLDW*0.45*pool*pool;
  float dark = 0.0;                                                                         // far trunks, two ranks, dark against the light
  for(int k = 0; k < 2; k++){
    float n = (k == 0) ? 46.0 : 27.0; float a = az*n/6.28318 + float(k)*0.37; float ci = floor(a), f = fract(a) - 0.5;
    uint h = hu(uint(int(ci) + 512)*31u + uint(k)*977u);
    if(h1(h) < 0.62){ float hw = (0.05 + 0.10*h1(h+1u))*(1.0 + 2.2*exp(-el*(k == 0 ? 30.0 : 16.0)));
      float m = smoothstep(hw + 0.035, hw - 0.035, abs(f - 0.5*(h1(h+2u) - 0.5)));
      dark = max(dark, m*(k == 0 ? 0.60 : 0.90)); } }
  return c + g*(1.0 - dark);
}
vec3 groundView(vec3 ro, vec3 rd, float sh){
  float t = ro.y/max(-rd.y, 1e-4); vec2 p = ro.xz + rd.xz*t;
  float px = t/(uRes.x*FOC)/max(-rd.y, 0.04);
  float d, w; vec3 c = vec3(0.0022, 0.0030, 0.0028) + riverLight(p, px, d, w, 0.0);
  // the forest stands in the water, and the water carries what is behind the trees
  vec3 rr = normalize(vec3(rd.x + 0.035*(vn(p*2.2 + vec2(0.0, uT*0.35)) - 0.5), -rd.y - sh, rd.z));
  c += farBG(rr)*0.62*pow(1.0 - clamp(-rd.y, 0.0, 1.0), 4.0);
  // rings of light: a drop, a step
  for(int i = 0; i < 8; i++){ vec4 q = uRings[i]; if(q.z < 0.0) continue; vec2 dv = p - q.xy; float rl = length(dv);
    if(q.w > 1.1){                                                                          // her step: a ripple that crosses the water toward us. Only the side that comes our way, never a circle
      float R = 0.25 + 3.3*pow(q.z, 0.85), wd = 0.05 + 0.06*q.z + 1.5*px;
      float a = q.w*exp(-q.z/1.3)*smoothstep(0.0, 0.12, q.z);
      float fr = smoothstep(0.10, 0.80, dot(dv/max(rl, 1e-3), normalize(ro.xz - q.xy)));
      c += GOLDW*a*fr*(0.85*exp(-pow((rl - R)/wd, 2.0)) + 0.35*exp(-pow((rl - R + 0.45)/wd, 2.0)));
    } else {
      float R = 0.20 + 1.75*pow(q.z, 0.72), wd = 0.030 + 0.045*q.z + 1.5*px;
      float a = q.w*exp(-q.z/0.75)*smoothstep(0.0, 0.12, q.z);
      c += GOLDW*a*(0.8*exp(-pow((rl - R)/wd, 2.0)) + 0.2*exp(-rl*rl/0.02)*exp(-q.z/0.25)); } }
  return mix(c, farBG(normalize(vec3(rd.x, 0.0, rd.z))), (1.0 - exp(-t/110.0))*smoothstep(0.42, 0.12, -rd.y));
}
// ---------------------------------------------------------------- the canopy from the air: crowns of many sizes, a few standing above the rest, mist lying between them
const vec3 MOON = vec3(-0.44, 0.50, 0.745);
vec3 gSD; float gGap;
vec3 moonGlow(vec3 rd){ float a = acos(clamp(dot(rd, normalize(vec3(-0.25, 0.52, 0.82))), -1.0, 1.0)); return vec3(0.55, 0.70, 1.0)*uMoonK*(0.050*exp(-pow(a/0.20, 2.0)) + 0.014*exp(-a/0.55)); }   // the moon behind thin mist, where the vine's last tendril reaches
float stars(vec3 rd){
  if(rd.y < 0.03) return 0.0;
  vec2 uv = vec2(atan(rd.x, rd.z), asin(clamp(rd.y, -1.0, 1.0)))*52.0; ivec2 c = ivec2(floor(uv)); uint h = hc(c, 401u); if(h1(h) > 0.22) return 0.0;
  vec2 f = fract(uv) - 0.5 - 0.6*(vec2(h1(h+1u), h1(h+2u)) - 0.5); float r = max(0.042, 1.5*52.0/(uRes.x*FOC));
  return (0.30 + 3.2*pow(h1(h+3u), 4.0))*exp(-dot(f, f)/(r*r))*smoothstep(0.03, 0.14, rd.y);
}
vec3 sky(vec3 rd){
  float el = max(rd.y, 0.0), sun = max(dot(rd, uSun), 0.0);
  return mix(vec3(0.020, 0.027, 0.038), vec3(0.0045, 0.0055, 0.0095), smoothstep(0.0, 0.30, el)) + GOLD*uSky*(0.10*exp(-el*3.0) + 0.9*pow(sun, 3.0)) + GOLDW*uSky*0.9*pow(sun, 14.0);
}
vec3 ceilView(vec3 ro, vec3 rd){                                                             // looking up from under the canopy: its dark roof, and the night in the gaps between the crowns
  float k = smoothstep(0.10, 0.36, rd.y)*uCeil; if(k <= 0.0) return vec3(0.0);
  float t = (HC + 2.5 - min(ro.y, HC))/rd.y; vec2 p = ro.xz + rd.xz*t; float px = t/(uRes.x*FOC);
  float big = 0.62*vn(p*0.13 + 2.0) + 0.38*vn(p*0.31 + 9.0);                                 // where two crowns leave a gap
  float fine = vn(p*1.1 + 4.0)*vn(p*2.7 + 1.0);                                              // leaves break each gap into small lights
  float gap = smoothstep(0.47, 0.62, big)*smoothstep(0.13, 0.27 + 2.0*px, fine);
  gGap = gap*k;
  return (vec3(0.026, 0.037, 0.054) + vec3(0.62, 0.72, 1.0)*stars(gSD))*gap*k*exp(-t/70.0);
}
// height of the treetops over the HC plane: main crowns, small ones between, a few emergents; gaps; cut down to the water where a river runs
float canH(vec2 p, out float id, out vec2 o1, out float F1){
  float h = -4.0; id = 0.5; o1 = vec2(1.0, 0.0); F1 = 1.0;
  vec2 pw = p + 1.8*(vec2(vn(p*0.21), vn(p*0.21 + 31.7)) - 0.5);
  for(int s = 0; s < 3; s++){
    float cs = (s == 0) ? 5.8 : ((s == 1) ? 3.4 : 21.0);
    vec2 q = pw/cs + float(s)*17.3; vec2 ic = floor(q - 0.5), fc = q - ic;
    for(int j = 0; j <= 1; j++) for(int i = 0; i <= 1; i++){
      ivec2 cc = ivec2(ic) + ivec2(i, j); uint hq = hc(cc, 3u + uint(s)); float e = h1(hq+5u);
      if(s == 2){ if(e > 0.34) continue; } else if(e < 0.09) continue;
      vec2 jc = 0.5 + (vec2(h1(hq), h1(hq+1u)) - 0.5)*0.6;
      if(s == 2 && length((vec2(cc) + jc - 34.6)*cs) < 24.0) continue;                      // no emergent where we fly through the canopy
      vec2 o = vec2(float(i), float(j)) + jc - fc;
      float rr = (s == 2) ? 0.20 + 0.10*h1(hq+2u) : 0.40 + 0.28*h1(hq+2u);
      float dd = dot(o, o)/(rr*rr); if(dd >= 1.0) continue;
      float top = (s == 2) ? 3.8 + 3.0*h1(hq+4u) : ((s == 0) ? 2.6*h1(hq+4u) : -1.0 + 2.4*h1(hq+4u));
      float hd = (s == 2) ? -0.8 + (top + 0.8)*pow(1.0 - dd, 0.8) : top - rr*cs*0.70*(1.0 - sqrt(1.0 - dd));   // emergents slope down to the canopy: no cliff
      if(hd > h){ h = hd; id = h1(hq+3u); o1 = o/rr; F1 = dd; } } }
  if(h > -3.5) h += 0.9*(vn(p*0.8 + id*13.0) - 0.5) + 0.45*(vn(p*2.1 + 5.0) - 0.5);
  vec4 r = riv(p); float w = rivW(r.g);
  float open = max(smoothstep(w + 2.4, w + 0.4, abs(r.r)), 0.8*smoothstep(r.b + 1.1, r.b + 0.2, r.a)*step(0.2, r.b));
  return mix(h, -1.4, open);
}
vec3 canopyView(vec3 ro, vec3 rd){
  float iy = 1.0/max(-rd.y, 1e-4), t0 = (ro.y - HC)*iy;
  float kr = 1.0/(1.0 + t0*t0/12000.0);                                             // far away the relief sinks into the haze
  float tA = max((ro.y - HC - 7.4*kr)*iy, 0.0), tB = (ro.y - HC + 1.6*kr)*iy;
  float id, F1; vec2 o1; float tp = tA, dp = 1.0, th = tB, tq = tB, dq = -1.0; bool hit = false;
  float jit = h1(hu(uint(gl_FragCoord.x) + 8191u*uint(gl_FragCoord.y) + 131071u*uint(uSeed)));      // each sample starts its search somewhere else: steps average into a smooth slope
  for(int i = 0; i <= 26; i++){ float tt = mix(tA, tB, (i == 0) ? 0.0 : min((float(i) + jit - 0.5)/26.0, 1.0));
    float h = canH(ro.xz + rd.xz*tt, id, o1, F1), dy = ro.y + rd.y*tt - HC - h*kr;
    if(dy <= 0.0){ tq = tt; dq = dy; hit = (i > 0); if(i == 0) th = tt; break; } tp = tt; dp = dy; }
  if(hit){ for(int k = 0; k < 4; k++){ float tm = 0.5*(tp + tq); float h = canH(ro.xz + rd.xz*tm, id, o1, F1), dy = ro.y + rd.y*tm - HC - h*kr;
      if(dy > 0.0){ tp = tm; dp = dy; } else { tq = tm; dq = dy; } }
    th = mix(tp, tq, dp/(dp - dq)); }
  vec2 p = ro.xz + rd.xz*th; float hS = canH(p, id, o1, F1);
  float t = th, px = t/(uRes.x*FOC);
  float d, w; vec3 rl = riverLight(p, px, d, w, 1.0);
  float e = 0.30 + 2.0*px, i2, f2; vec2 o2; float hx = canH(p + vec2(e, 0.0), i2, o2, f2), hz = canH(p + vec2(0.0, e), i2, o2, f2);
  vec3 N = normalize(vec3(-(hx - hS)*kr, e*1.3, -(hz - hS)*kr));                    // the lumps of each crown catch the moon
  float bump = 0.40*vn(p*0.9 + id*17.0) + 0.32*vn(p*2.6 + 7.0) + 0.28*vn(p*6.5)/(1.0 + 40.0*px);
  float moon = clamp(dot(N, MOON), 0.0, 1.0);
  float ao = smoothstep(-3.2, 0.8, hS)*(0.40 + 0.60*smoothstep(1.0, 0.25, F1));
  vec3 c = vec3(0.0035, 0.0075, 0.0055)*(0.5 + 0.9*bump)*ao*(0.7 + 0.6*id);                                   // night on the leaves: near-black green
  c += vec3(0.070, 0.110, 0.126)*moon*(0.15 + 1.5*bump)*ao*(1.0 + 0.6*smoothstep(2.5, 6.0, hS));             // cool moonlight on the side that faces it
  c += mix(GOLD, vec3(0.42, 0.62, 0.14), 0.5)*0.035*exp(-max(d - w, 0.0)/3.0)*(0.3 + bump)*ao*uRivK*(1.0 + 0.8*uRoadK);   // only the crowns at the bank catch the river
  // "a wind": a wave crosses the canopy; leaves turn their pale undersides and the mist lifts with it
  vec2 wd = normalize(vec2(0.55, 0.83)); float u = dot(p, wd), v = dot(p, vec2(wd.y, -wd.x));
  float wv = uWave.y*(exp(-pow((u - uWave.x)/14.0, 2.0)) + 0.35*exp(-pow((u - uWave.x + 26.0)/9.0, 2.0)));
  float streak = vn(vec2(v*0.30, u*0.9 - uT*2.2))*vn(vec2(v*0.9 + 5.0, u*2.2 - uT*3.1));
  c += vec3(0.50, 0.66, 0.62)*wv*ao*(0.04 + 0.30*streak)*(0.4 + bump)/(1.0 + 8.0*px);
  float open = smoothstep(w + 2.4, w + 0.4, d);                                     // the river parts the trees
  c = mix(c, vec3(0.0022, 0.0030, 0.0028), open);
  // low mist between the crowns, drifting
  float mt = 0.6 + 3.8*(0.65*vn(p*0.028 + vec2(uT*0.05, uT*0.02)) + 0.35*vn(p*0.083 - vec2(uT*0.08, 0.0)) - 0.45) + 2.0*wv;
  float fog = (1.0 - exp(-0.26*max(mt - hS, 0.0)*min(iy, 8.0)))*(1.0 - 0.55*open);
  vec3 fc = vec3(0.050, 0.066, 0.084)*(1.0 + 1.3*wv) + GOLD*0.05*exp(-max(d - w, 0.0)/2.5)*uRivK;
  c = mix(c, fc, fog);
  // "a dream": the canopy lights from within, thousands of small points
  { vec2 g = p/1.05; float acc = 0.0;
    for(int j = 0; j <= 1; j++) for(int i = 0; i <= 1; i++){
      ivec2 cc = ivec2(floor(g - 0.5)) + ivec2(i, j); uint hq = hc(cc, 19u); float b = h1(hq); if(b > 0.72) continue;
      vec2 ctr = (vec2(cc) + 0.5 + (vec2(h1(hq+1u), h1(hq+2u)) - 0.5)*0.9)*1.05;
      float on = smoothstep(0.0, 0.22, uDream*1.25 - h1(hq+3u));
      float tw = 0.55 + 0.45*sin(uT*(0.5 + 1.2*h1(hq+4u)) + 6.28*h1(hq+5u));
      float r = 0.075 + 1.1*px, dd = length(p - ctr);
      acc += on*tw*(0.20 + 2.6*b*b*b)*exp(-dd*dd/(r*r))*min(1.0, 0.0056/(r*r))*3.2; }
    c += mix(GOLD, GOLDW, 0.5)*acc*mix(0.40, 1.0, smoothstep(0.10, 0.30, -rd.y))*(0.5 + 0.5*F1)*(1.0 + 2.0*wv)*(1.0 - 0.5*fog)*(1.0 - open)*exp(-t/200.0); }
  return mix(c, sky(normalize(vec3(rd.x, 0.0, rd.z))), 1.0 - exp(-t/190.0)) + rl*(1.0 - 0.45*fog)*exp(-t/330.0);
}
// ---------------------------------------------------------------- plants. Local leaf space: x along the midrib 0..1, y across.
float heliconia(vec2 q, uint h, out float vein){
  q.y += 0.45*(h1(h+11u) - 0.5)*q.x*q.x;
  float x = clamp(q.x, 0.0, 1.0), ay = abs(q.y);
  float w = 0.150*pow(max(sin(3.14159*pow(x, 0.8)), 0.0), 0.6);
  float vc = (q.x + 0.30*ay)*24.0, vf = abs(fract(vc) - 0.5);
  float torn = step(0.84, h1(h + uint(int(floor(vc)) + 64)*13u + (q.y > 0.0 ? 5u : 9u)));
  w *= 1.0 - 0.45*torn*smoothstep(0.30, 0.48, vf)*smoothstep(0.35, 1.0, ay/max(w, 1e-3));    // the blade tears along its veins
  vein = max(smoothstep(0.010, 0.003, ay), 0.45*smoothstep(0.44, 0.49, vf));
  return max(ay - w, max(-q.x, q.x - 1.0));
}
float aroid(vec2 q, out float vein){
  float xn = (q.x + 0.20)/1.20, ay = abs(q.y);
  float w = 0.62*pow(clamp(xn, 0.0, 1.0), 0.48)*pow(clamp(1.0 - xn, 0.0, 1.0), 0.72);
  float d = max(ay - w, (0.035 - 0.75*q.x) - ay);                                           // the sinus between the two lobes
  d = max(d, max(-0.2 - q.x, q.x - 1.0));
  float xb = q.x - 0.55*ay - 0.9*ay*ay; float vf = abs(fract(xb*7.0) - 0.5);
  vein = max(smoothstep(0.012, 0.004, ay), 0.5*smoothstep(0.455, 0.49, vf)*step(-0.1, xb));
  return d;
}
float frond(vec2 q, uint h, out float vein){
  q.y += 0.30*q.x*q.x*(h1(h+3u) - 0.2);                                                     // the rachis arches
  float ay = abs(q.y), x0 = q.x - 0.55*ay; const float N = 12.0;
  float f = fract(x0*N) - 0.5, xb = (floor(x0*N) + 0.5)/N;
  float L = 0.34*pow(max(sin(3.14159*clamp(xb*0.92 + 0.06, 0.0, 1.0)), 0.0), 0.7);
  float l = ay/max(L, 1e-3);
  float wl = 0.40*(1.0 - l*l)*step(0.0, xb)*step(xb, 1.0);
  float dl = max(max((abs(f) - wl)/N, ay - L), max(-xb, xb - 1.0));
  float dr = max(ay - 0.008, max(-q.x, q.x - 1.0));
  vein = smoothstep(0.008, 0.003, ay);
  return min(dl, dr);
}
float sprig(vec2 q, uint h, out float vein){                                                  // a shoot of the vine: leaves in opposite pairs, oval, drawn out to a point
  q.y += 0.22*q.x*q.x*(h1(h+3u) - 0.5);
  float d = max(abs(q.y) - 0.007, max(-q.x, q.x - 0.84)); vein = 0.0;
  for(int i = 0; i < 4; i++){ bool tip = (i == 3); float x0 = tip ? 0.82 : 0.12 + 0.25*float(i), sz = tip ? 0.30 : 0.37 - 0.035*float(i);
    vec2 p = vec2(q.x - x0, tip ? q.y : abs(q.y)); float ca = tip ? 1.0 : 0.53, sa = tip ? 0.0 : 0.848;   // each pair stands out at 58 degrees
    vec2 l = vec2(ca*p.x + sa*p.y, -sa*p.x + ca*p.y)/sz; float xc = clamp(l.x, 0.0, 1.0);
    float w = 0.54*pow(xc, 0.5)*pow(1.0 - xc, 0.9), dl = max(abs(l.y) - w, max(-l.x, l.x - 1.0))*sz;
    if(dl < d){ d = dl; vein = max(smoothstep(0.035, 0.012, abs(l.y)), 0.4*smoothstep(0.43, 0.49, abs(fract((l.x - 0.8*abs(l.y))*6.0) - 0.5)))*step(dl, 0.0); } }
  return d;
}
float leafCell(vec2 L, ivec2 c, uint seed, float soft, vec2 corr, float crad, float Yt, out float vein, out float rim){
  vein = 0.0; rim = 0.0; const float C = 1.7;
  uint h = hc(c, seed); float r0 = h1(h);
  float ex = smoothstep(0.0, 0.12, uDense - r0); if(ex <= 0.0) return 0.0;
  vec2 ctr = (vec2(c) + 0.5 + (vec2(h1(h+1u), h1(h+2u)) - 0.5)*0.7)*C;
  ex *= smoothstep(crad, crad + 0.55, length(ctr - corr));
  float Yc = Yt + (ctr.y - L.y)*uUp.y + (ctr.x - L.x)*uRt.y;                               // leaves live under the canopy top;
  ex *= max(sqrt(smoothstep(HC + 4.0, HC - 3.0, Yc)), uLoose*step(h1(h+8u), 0.45));               // the roof of the canopy is ragged, not a sheet: we sink into it over a third of a second; a few ride the wind above it
  if(ex <= 0.01) return 0.0;
  float len = C*(0.68 + 0.39*h1(h+3u))*ex;                                               // the longest leaf stays inside the cells that are searched: no cut tips
  float ang = 1.5708 + (h1(h+4u) - 0.5)*2.9 + uFlut*0.24*sin(uT*(2.0 + 2.0*h1(h+6u)) + 40.0*r0);
  vec2 q = L - ctr; float ca = cos(ang), sa = sin(ang); q = vec2(ca*q.x + sa*q.y, -sa*q.x + ca*q.y)/len + vec2(0.40, 0.0);
  float ty = h1(h+5u), v, d;
  if(h1(h+12u) < uSprig) d = sprig(q, h, v); else if(ty < 0.44) d = heliconia(q, h, v); else if(ty < 0.84) d = aroid(q, v); else d = frond(q, h, v);
  d = min(d, max(abs(q.y) - 0.009, max(q.x, -0.18 - q.x)))*len;                             // the petiole
  float al = smoothstep(soft, -soft, d);
  vein = v*al; rim = smoothstep(-0.03 - 2.0*soft, 0.0, d)*al*mix(0.55, 1.35, smoothstep(-0.03, 0.03, q.y*sign(h1(h+9u) - 0.5)));
  return al;
}
float plantLayer(vec2 L, float kf, float soft, float Yw, float Yt, vec2 corr, float crad, out float vein, out float rim){
  uint seed = uint(int(kf) + 4096)*7u + 1u;
  ivec2 ic = ivec2(floor(L/1.7 - 0.5));
  float a = 0.0; vein = 0.0; rim = 0.0;
  for(int j = 0; j < 2; j++) for(int i = 0; i < 2; i++){
    float v, r; float al = leafCell(L, ic + ivec2(i, j), seed, soft, corr, crad, Yt, v, r);
    if(al > a){ a = al; vein = v; rim = r; } }
  float under = smoothstep(HC + 0.5, HC - 2.0, Yt);
  { float gi = floor(L.x/2.6); uint hl = hc(ivec2(int(gi), int(kf)), 77u);                  // lianas
    if(h1(hl) < 0.62){ float x0 = (gi + 0.2 + 0.6*h1(hl+1u))*2.6;
      float keep = smoothstep(crad*0.8, crad*0.8 + 0.4, abs(x0 - corr.x));
      float xx = x0 + 0.16*sin(L.y*1.1 + 6.28*h1(hl+2u)) + 0.05*sin(L.y*3.3 + 6.28*h1(hl+3u));
      float d = abs(L.x - xx) - (0.012 + 0.022*h1(hl+4u))*keep; float al = smoothstep(soft, -soft, d)*under*step(0.001, keep)*uLianaK;
      if(al > a){ a = al; vein = 0.0; rim = 0.6*al; } } }
  if(uTrunkK > 0.0){ float gi = floor(L.x/6.4); uint ht = hc(ivec2(int(gi), int(kf)), 91u);  // a kapok and its buttress roots, standing in the water
    if(h1(ht) < 0.42){ float x0 = (gi + 0.25 + 0.5*h1(ht+1u))*6.4;
      if(abs(x0 - corr.x) > crad + 1.0){ float hw = 0.20 + 0.20*h1(ht+2u), y = max(Yw, 0.0);
        float side = (L.x < x0) ? (0.6 + 0.7*h1(ht+3u)) : (0.6 + 0.7*h1(ht+4u));
        float fl = min(hw*side*(1.7*exp(-y/0.45) + 0.9*exp(-y/1.7)), 1.45 - hw);
        float d = abs(L.x - x0 - 0.07*sin(Yw*0.9 + 6.28*h1(ht+5u)) - 0.025*sin(Yw*3.1 + 6.28*h1(ht+6u))) - (hw*(1.0 - 0.035*min(y, 6.0)) + fl); float al = smoothstep(soft, -soft, d)*uTrunkK;
        if(al > a){ a = al; vein = 0.0; rim = smoothstep(-0.05 - 2.0*soft, 0.0, d)*al; } } } }
  return a;
}
vec3 flyLayer(vec2 L, float kf, float rb){
  uint seed = uint(int(kf) + 4096)*13u + 5u; const float C = 1.05;
  ivec2 ic = ivec2(floor(L/C - 0.5)); float acc = 0.0;
  for(int j = 0; j < 2; j++) for(int i = 0; i < 2; i++){
    ivec2 c = ic + ivec2(i, j); uint h = hc(c, seed); if(h1(h) > uFly) continue;
    float ph = 6.283*h1(h+1u), om = 0.5 + 0.9*h1(h+2u);
    vec2 ctr = (vec2(c) + 0.5 + (vec2(h1(h+3u), h1(h+4u)) - 0.5)*0.8)*C;
    ctr += 0.13*vec2(sin(uT*om*1.0 + ph), cos(uT*om*1.25 + ph*1.7));                         // hanging in the air
    ctr.y += uLift*(0.04 + 0.16*h1(h+5u));                                                  // every drum hit lifts them; they settle
    float d = length(L - ctr), r = 0.010 + rb;
    float pulse = 0.2 + 0.8*pow(0.5 + 0.5*sin(uT*om*1.4 + ph*3.0), 2.0);
    acc += pulse*(2.6*exp(-d*d/(r*r))*min(1.0, 0.00035/(r*r)) + 0.05*exp(-d/(0.05 + 3.0*r))); }
  return GOLDW*acc;
}
float backGlow(vec3 rd){                                                                    // the light behind the leaf without the trunks: a blade passes light on as a soft glow, never as a picture
  float az = atan(rd.x, rd.z) + uBgAz, el = abs(rd.y), da = az - uGlowAz;
  float pool = exp(-da*da/0.055)*exp(-el*8.5), wide = exp(-da*da/0.9)*exp(-el*3.2);
  return (0.68*(0.008*exp(-el*4.0) + 0.040*wide + 0.50*pool) + 0.37*pool*pool)*(rd.y < 0.0 ? 0.55 : 0.80); }
float heroBlade(vec2 q, out float vein, out float stalk){                                   // one broad understory leaf: round at the base, widest below the middle, drawn out to a drip tip; and its stalk
  float xt = (q.x + 0.20)/1.34, xc = clamp(xt, 0.0, 1.0), ay = abs(q.y);
  float w = 0.60*pow(xc, 0.5)*pow(1.0 - xc, 0.6)*(1.0 - 0.78*smoothstep(0.76, 1.0, xc));
  w *= 1.0 + 0.035*sin(xt*21.0 + 1.0)*smoothstep(0.05, 0.30, xc);
  float d = max(ay - w, max(-xt, xt - 1.0)*1.34);
  float xb = q.x - 0.55*ay - 0.9*ay*ay, vf = abs(fract(xb*7.0) - 0.5);
  vein = max(smoothstep(0.012, 0.004, ay)*step(-0.2, q.x)*smoothstep(1.14, 0.92, q.x), 0.5*smoothstep(0.455, 0.49, vf)*step(-0.1, xb)*smoothstep(0.0, 0.035, w - ay));
  float sx = -0.20 - q.x;
  stalk = max(abs(q.y + 0.20*sx*sx) - mix(0.010, 0.015, clamp(sx/0.42, 0.0, 1.0)), max(-sx - 0.03, sx - 0.42));
  return d;
}
vec3 heroLeaf(vec3 col, vec2 scl, float zh, vec3 rd){                                        // one leaf of the vine, passed close: her light runs up its midrib and out along every vein. Nothing is written on it
  const float HL = 0.52;
  float coc = 0.022*abs(1.0/zh - 1.0/uFocus) + 1.0/uRes.x, soft = coc*zh/FOC;
  vec2 L = uCP + (scl + uRot)*zh/FOC - uHero.xy;
  float ca = cos(uHero.w), sa = sin(uHero.w);
  vec2 q = vec2(ca*L.x + sa*L.y, -sa*L.x + ca*L.y)/HL + vec2(0.42, 0.0);
  q.y += 0.035*sin(q.x*3.4 + 0.6) + 0.004*sin(q.x*37.0)*smoothstep(0.08, 0.2, abs(q.y));
  float v, st; float db = heroBlade(q, v, st)*HL;
  float d = min(db, st*HL);
  float al = smoothstep(soft, -soft, d)*uHeroA.x, blade = smoothstep(soft, -soft, db);
  float lumP = min(dot(col, vec3(0.3, 0.6, 0.1)), 0.7), lum = mix(lumP, min(backGlow(rd), 0.7), 0.4);
  float ay = abs(q.y), xb = q.x - 0.55*ay - 0.9*ay*ay, vf = abs(fract(xb*7.0) - 0.5);
  float quilt = 0.70 + 0.30*smoothstep(0.50, 0.16, vf), fold = 1.0 - 0.18*sign(q.y)*smoothstep(0.0, 0.03, ay);   // the blade swells between its side veins and folds a little along the midrib
  vec3 lc = vec3(0.0030, 0.0062, 0.0040) + vec3(0.035, 0.15, 0.03)*lum*0.30*quilt*fold*blade;
  lc += vec3(0.014, 0.036, 0.022)*quilt*blade*smoothstep(-0.10, 0.55, q.x)*(0.45 + 0.55*fold);                    // glossy: a little of the moon lies on it
  lc += GOLD*smoothstep(-0.04 - 2.0*soft, 0.0, d)*(0.012 + 0.75*lum);
  float pl = max(xb, -0.2) + 1.25*ay;
  float lit = smoothstep(uHeroA.y, uHeroA.y - 0.10, pl), tip = exp(-pow((pl - uHeroA.y)/0.05, 2.0));
  lc += (GOLD*v*(0.03 + uHeroA.z*1.1*lit) + GOLDW*v*tip*2.0*uHeroA.z*smoothstep(0.0, 0.05, uHeroA.y))*blade;
  { float sx = -0.20 - q.x; lc += GOLD*0.30*(0.03 + uHeroA.z*1.1)*smoothstep(0.005, 0.0015, abs(q.y + 0.20*sx*sx))*step(0.0, sx)*smoothstep(0.42, 0.36, sx); }   // the light comes in along the stalk as a thread
  return mix(col, lc, al);
}
// ---------------------------------------------------------------- her prints: a short reach of wet bank on our side, and five prints of a worn flat sole, each holding a little of her light
float soleD(vec2 p, float foot){                                                             // p.x heel (-0.5) to toe (+0.5), p.y across; foot +1: her left. Our own plain sole: no maker's pattern
  float y = p.x, x = p.y*foot;                                                               // x > 0: the outside of the foot
  float cx = 0.028*sin((y + 0.5)*3.1416) - 0.012;
  float wf = mix(0.112, 0.158, smoothstep(-0.22, 0.16, y))*(1.0 - ((x - cx) < 0.0 ? 0.30 : 0.14)*exp(-pow((y + 0.09)/0.13, 2.0)));   // narrow heel, broad ball; the arch cuts in on the inside only, the outside runs almost straight: a shoe, not a peanut
  float capT = sqrt(max(1.0 - pow(max(y - 0.22, 0.0)/0.28, 2.0), 0.0)), capH = sqrt(max(1.0 - pow(max(-0.37 - y, 0.0)/0.13, 2.0), 0.0));
  return max(abs(x - cx) - wf*capT*capH, abs(y) - 0.5);
}
vec4 bank(vec3 ro, vec3 rd, out vec3 add, out float zb){
  add = vec3(0.0); zb = 1e3;
  float dn = dot(rd, uBkN); if(dn > -1e-3) return vec4(0.0);
  float tb = dot(uBkS - ro, uBkN)/dn; if(tb < 0.30 || tb > 11.0) return vec4(0.0);
  vec3 qq = ro + rd*tb - uBkS; float a = dot(qq, uBkD), b = dot(qq, uBkU);
  float wob = 0.07*(vn(vec2(a, b)*1.7 + 3.0) - 0.5);
  float A = smoothstep(-0.85, -0.45, a + wob)*smoothstep(uBk.z + 0.85, uBk.z + 0.45, a - wob)*smoothstep(0.52, 0.26, abs(b) + wob);
  float kd = smoothstep(10.5, 5.0, tb)*smoothstep(0.30, 0.90, tb)*uBk.x; A *= kd; if(A <= 0.001) return vec4(0.0);   // the wet ground comes out of the dark as we near it
  zb = tb*dot(rd, uFw);
  float pxs = tb/(uRes.x*FOC)/max(-dn, 0.2), Lp = uBk.y;
  float tex = 0.55*vn(vec2(a, b)*7.0) + 0.45*vn(vec2(a, b)*19.0 + 5.0);
  vec3 mud = vec3(0.0030, 0.0034, 0.0030)*(0.5 + tex) + vec3(0.020, 0.022, 0.021)*pow(vn(vec2(a, b)*31.0 + 9.0), 5.0)/(1.0 + 60.0*pxs);   // wet ground: dark, with small glints
  float light = 0.0, halo = 0.0;
  for(int i = 0; i < 9; i++){ vec4 pr = uBkP[i]; vec2 p = vec2(a - pr.x, b - pr.y)/Lp; if(abs(p.x) > 0.95 || abs(p.y) > 0.65) continue;
    float d = soleD(p, pr.z), e = max(0.006, 1.3*pxs/Lp), ins = smoothstep(e, -e, d), x = p.y*pr.z;
    float rim = smoothstep(-0.040, -0.012, d)*ins;                                           // the pressed edge holds the most
    float rib = 0.5 + 0.5*cos(6.2832*19.0*p.x), ribK = clamp(1.0 - 45.0*pxs/Lp, 0.0, 1.0);   // fine plain ribbing across the sole
    float arch = 1.0 - 0.45*exp(-pow((p.x + 0.07)/0.12, 2.0))*smoothstep(-0.03, 0.08, -x);   // the arch presses less
    float heel = 1.0 - 0.30*smoothstep(-0.30, -0.47, p.x)*smoothstep(0.0, 0.10, x);          // ten years: worn down at the outside of the heel
    float waist = 1.0 - 0.42*exp(-pow((p.x + 0.09)/0.10, 2.0));                              // a shoe: the heel and the forefoot press, the waist between them hardly
    light += pr.w*((0.17 + 0.14*mix(0.5, rib, ribK))*ins*arch*heel*waist + 0.34*rim*heel);      // a little light, held: the pressed edge and the ribs carry it. Plain tread, nothing written in it
    halo += pr.w*exp(-max(d, 0.0)/0.10)*(1.0 - ins); }
  add = GOLD*(light + 0.045*halo*(0.5 + tex))*A;
  return vec4(mud, 0.72*A);
}
// ---------------------------------------------------------------- the great tree on the bank, and the vine that climbs it (built from photographs of the living plant: stems fluted and twisted like rope, braided loosely, standing off the trunk)
const float VTOP = 14.3;
float vth(float h){ float x = clamp(h/0.6, 0.0, 30.99); int i = int(floor(x)); float f = x - float(i);
  float p0 = uVth[max(i - 1, 0)], p1 = uVth[i], p2 = uVth[min(i + 1, 31)], p3 = uVth[min(i + 2, 31)];
  return p1 + 0.5*f*(p2 - p0 + f*(2.0*p0 - 5.0*p1 + 4.0*p2 - p3 + f*(3.0*(p1 - p2) + p3 - p0))); }
float trunkR0(float h){ return (0.60 - 0.010*h + 0.045*sin(0.9*h + 1.0))*(1.0 - 0.93*smoothstep(11.5, 14.9, h)); }
float vineR(float h){ return trunkR0(h) + 0.17 + 0.15*pow(max(sin(0.50*h + 0.4), 0.0), 2.0) + 0.85*exp(-max(h, 0.0)/0.45); }
// a young tendril: a stalk that sweeps out and up along a quarter circle (radius R, in the upright plane of e1), then a coil (first radius C, in the upright plane of e2). x: distance to its line; y: 0..1 along the stalk, 1..2 round the coil
vec2 tendril(vec3 p, vec3 P0, vec2 e1, float R, vec2 e2, float C){
  vec3 v = p - P0; float a = dot(v.xz, e1), c = dot(v.xz, vec2(-e1.y, e1.x));
  vec2 w = vec2(a, v.y - R); float s = clamp(atan(w.x, -w.y), 0.0, 1.5708);
  float d1 = length(vec3(w - R*vec2(sin(s), -cos(s)), c));
  vec3 u = v - vec3(e1.x*R, R, e1.y*R); float a2 = dot(u.xz, e2), c2 = dot(u.xz, vec2(-e2.y, e2.x)); vec2 q = vec2(a2 - C, u.y);
  float rr = length(q), be = mod(3.14159 - atan(q.y, q.x), 6.28318), d2 = 1e3, s2 = 0.0; const float BM = 10.9;
  for(int k = 0; k < 3; k++){ float bk = be + 6.28318*float(k); if(bk > BM) break; float d = abs(rr - C*(1.0 - 0.80*bk/BM)); if(d < d2){ d2 = d; s2 = bk/BM; } }
  d2 = length(vec2(d2, c2));
  return (d1 < d2) ? vec2(d1, s/1.5708) : vec2(d2, 1.0 + s2);
}
float barkR(float th, float h, vec2 cs, float N, float sd){                                    // one size of ridge: N ridges round the trunk, wandering, breaking off and starting again, cracked across into plates
  float wr = 1.7*vn(cs*1.6 + vec2(h*0.21 + sd, -h*0.17)) + 0.6*vn(cs*4.5 + vec2(3.0 - h*0.4, h*0.5 + sd)) + 0.42*vn(cs*9.0 + vec2(h*1.9, sd - h*1.4));
  float a = th*N/6.28318 + wr*2.4*sqrt(N/22.0), r = abs(fract(a) - 0.5)*2.0, ri = mod(floor(a), N);
  float pl = abs(fract(h*(0.9 + N*0.02) + 5.0*h1(uint(int(ri))*7u + 3u)) - 0.5)*2.0;
  float brk = smoothstep(0.22, 0.42, vn(vec2(ri*3.7 + 1.0 + sd, h*1.6)));
  return (1.0 - pow(r, 3.0))*(1.0 - 0.75*pow(pl, 6.0))*(0.30 + 0.70*brk);
}
float barkH(float th, float h){                                                               // furrowed bark: broad plates and, on them, finer ridges a few fingers wide. About 1 on a ridge, 0 in a furrow
  vec2 cs = vec2(cos(th), sin(th));
  return 0.40*barkR(th, h, cs, 22.0, 0.0) + 0.62*barkR(th, h, cs, 64.0, 5.3) + 0.20*vn(vec2(th*90.0, h*9.0));
}
// m: x what (0 trunk, 1 the vine, 2 a tendril, 3 the thin liana, 4 a leaf of the vine), y how deep in a furrow / how far along a tendril, z the light on a tendril, w height above the tree's ground
float treeD(vec3 p, out vec4 m){
  vec2 q = p.xz - uTree.xy; float r = length(q), th = atan(q.x, -q.y), h = p.y - uTree.z;
  float R0 = trunkR0(h), fl = exp(-max(h, 0.0)/0.50);
  float R = R0 + fl*(0.30 + 0.80*pow(0.5 + 0.5*cos(5.0*th + 1.3 + 0.9*sin(th + 0.5)), 2.0)) + (0.012*sin(3.0*th + 0.7*h) + 0.007*cos(22.0*th + 3.0*sin(0.7*h + th)))*(1.0 - 0.8*smoothstep(11.0, 15.0, h));
  float d = max((r - R)*mix(0.45, 0.72, smoothstep(0.5, 2.0, h)), h - 14.9); m = vec4(0.0, 0.0, 0.0, h);
  if(h < VTOP + 0.5){
    float rv = vineR(h), sc = (1.0 - 0.40*smoothstep(8.0, 13.0, h))*(1.0 - 0.55*smoothstep(13.2, VTOP, h));
    float dth = th - vth(h); dth -= 6.28318*floor(dth/6.28318 + 0.5);
    vec2 uv = vec2(r - rv, rv*dth*0.92); float lc = length(uv);
    if(lc < 0.95){ float dA = 1e3, dB = 1e3;
      for(int i = 0; i < 3; i++){ float fi = float(i), ph = 2.6*h + 2.0944*fi + 0.8*sin(0.7*h + 2.0*fi);
        float a = sc*0.064*(1.0 + 0.26*sin(1.3*h + 2.0*fi)) + (i == 2 ? 0.08*pow(max(sin(0.42*h + 1.0), 0.0), 6.0) : 0.0);     // three stems wound round each other; now and then one stands off and comes back
        float nd = exp(-pow((fract(h*1.6 + 0.37*fi) - 0.5)/0.10, 2.0));                                                            // a node: the stem swells where leaves leave it
        float rs = sc*0.058*(1.0 + 0.16*sin(2.1*h + 1.7*fi + 0.5) + 0.22*nd);
        vec2 e = uv - a*vec2(cos(ph), sin(ph));
        float ds = length(e) - rs - 0.0030*sc*cos(5.0*atan(e.y, e.x) + 9.0*h); if(ds < dA){ dB = dA; dA = ds; } else if(ds < dB) dB = ds; }
      float dv = max(dA*0.70, h - VTOP);
      if(dv < d){ d = dv; m = vec4(1.0, (dB - dA)/sc, sc, h); }
      float k2 = (1.0 - smoothstep(10.5, 12.5, h))*smoothstep(0.1, 1.2, h);                                                    // a second, thin liana crosses over the vine and back, the way they tangle
      if(k2 > 0.01){ float v2 = 0.52*sin(0.62*h + 0.8); vec2 e = uv - vec2(mix(-0.10, 0.20, exp(-v2*v2/0.03)), v2);
        float d2 = (length(e) - k2*(0.034 + 0.009*cos(2.0*atan(e.y, e.x) + 7.0*h)))*0.62;
        if(d2 < d){ d = d2; m = vec4(3.0, 0.0, 0.0, h); } }
      if(h > 1.5 && h < VTOP - 0.3){                                                                                           // its leaves: opposite pairs at the nodes, oval, drawn out to a point
        float nk = floor(h/0.44), hl = h - (nk + 0.5)*0.44; uint hn = hu(uint(int(nk) + 40)*2654435761u);
        if(h1(hn) < 0.88){ float L = sc*(0.25 + 0.09*h1(hn + 1u)), an = 0.20 + 0.55*h1(hn + 2u);
          vec2 lp = vec2(abs(uv.y) - 0.07*sc, hl + 0.06), ax = vec2(cos(an), sin(an));
          float xl = dot(lp, ax)/L, yl = (lp.y*ax.x - lp.x*ax.y)/L, xc = clamp(xl, 0.0, 1.0), wl = 0.50*pow(xc, 0.5)*pow(1.0 - xc, 0.85);
          float dl = max(max((abs(yl) - wl)*L, max(-xl, xl - 1.0)*L), abs(uv.x - 0.03 - 0.25*xc*L) - 0.006)*0.6;
          if(dl < d){ d = dl; m = vec4(4.0, xl, yl/max(wl, 0.02), h); } } }
    } else d = min(d, (lc - 0.78)*0.7);
  }
  for(int i = 0; i < 6; i++){ vec4 R4 = uTdR[i]; if(R4.x <= 0.0) continue; float bd = length(p - uTdC[i]) - (0.75*R4.x + 2.0*R4.y + 0.1);
    if(bd > 0.3){ d = min(d, bd); continue; }
    vec2 t2 = tendril(p, uTdP[i], uTdE[i].xy, R4.x, uTdE[i].zw, R4.y); float dt = (t2.x - R4.z*(1.0 - 0.32*t2.y))*0.9;
    if(dt < d){ d = dt; m = vec4(2.0, t2.y, R4.w, R4.z); } }
  return max(d, -h - 0.04);
}
vec4 treeView(vec3 ro, vec3 rd, out float zt){                                                // colour (already times its cover) and cover; zt: its depth along the way we look
  zt = 1e3;
  vec2 oc = ro.xz - uTree.xy; float A = dot(rd.xz, rd.xz), B = dot(oc, rd.xz), Cq = dot(oc, oc) - 10.9, D = B*B - A*Cq; if(D <= 0.0 || A < 1e-7) return vec4(0.0);
  float sq = sqrt(D), t0 = max((-B - sq)/A, 0.02), t1 = (-B + sq)/A, ya = uTree.z - 0.03, yb = uTree.z + 18.4;
  if(rd.y > 1e-4){ t0 = max(t0, (ya - ro.y)/rd.y); t1 = min(t1, (yb - ro.y)/rd.y); } else if(rd.y < -1e-4){ t0 = max(t0, (yb - ro.y)/rd.y); t1 = min(t1, (ya - ro.y)/rd.y); } else if(ro.y < ya || ro.y > yb) return vec4(0.0);
  t1 = min(t1, 34.0); if(t1 <= t0) return vec4(0.0);
  float t = t0, px = 1.0/(uRes.x*FOC); vec4 m = vec4(0.0); bool hit = false;
  for(int i = 0; i < 84; i++){ float d = treeD(ro + rd*t, m); if(d < 0.7*px*t){ hit = true; break; } t += d; if(t > t1) break; }
  vec3 c = vec3(0.0); float al = 0.0;
  if(hit){ vec3 p = ro + rd*t; float e = max(0.0012, 0.9*px*t); vec4 mm; vec2 k = vec2(1.0, -1.0);
    vec3 n = normalize(k.xyy*treeD(p + k.xyy*e, mm) + k.yyx*treeD(p + k.yyx*e, mm) + k.yxy*treeD(p + k.yxy*e, mm) + k.xxx*treeD(p + k.xxx*e, mm));
    vec2 q = p.xz - uTree.xy; float r = length(q), th = atan(q.x, -q.y), h = m.w;
    float lit = uVine.y*smoothstep(uVine.x + 0.25, uVine.x - 0.9, h), head = uVine.y*exp(-pow((h - uVine.x)/0.42, 2.0));
    float flow = 0.45 + 0.55*smoothstep(0.25, 0.70, vn(vec2(h*1.5 - uT*2.6, 3.0)));                                             // something always travels up through the gold
    float moon = max(dot(n, MOON), 0.0)*(0.30 + 0.70*smoothstep(0.30, 0.62, vn(vec2(th*1.4 + 2.0, h*0.5 + th))));               // moonlight comes down through the leaves in patches
    vec3 amb = vec3(0.0075, 0.0100, 0.0120)*(0.6 + 0.4*n.y) + GOLD*0.012*max(dot(n, normalize(vec3(-0.85, -0.10, -0.50))), 0.0)*uRivK;   // night, and a little of the river from below
    vec3 key = vec3(0.070, 0.105, 0.122)*1.15*moon;
    if(m.x < 0.5){                                                                                                              // the trunk: furrowed bark, lichen
      float rv = vineR(h), dth = th - vth(h); dth -= 6.28318*floor(dth/6.28318 + 0.5); float lv = length(vec2(r - rv, rv*dth));
      float eb = 0.006, b0 = barkH(th, h), dbt = (barkH(th + eb, h) - b0)/(eb*max(r, 0.2)), dbh = (barkH(th, h + 0.008) - b0)/0.008;
      vec3 nb = normalize(n - 0.016*(dbt*vec3(cos(th), 0.0, sin(th)) + dbh*vec3(0.0, 1.0, 0.0)));                                 // the relief of the bark: ridges catch the light, furrows keep the dark
      float occ = 0.20 + 0.80*smoothstep(0.08, 0.75, b0);
      float moonB = max(dot(nb, MOON), 0.0)*(0.30 + 0.70*smoothstep(0.30, 0.62, vn(vec2(th*1.4 + 2.0, h*0.5 + th))));
      vec3 alb = mix(vec3(0.33, 0.265, 0.205), vec3(0.37, 0.36, 0.31), smoothstep(0.62, 0.80, vn(vec2(cos(th), sin(th))*2.4 + h*0.6)))*(0.50 + 0.80*b0)*(0.8 + 0.4*vn(vec2(th*40.0, h*11.0)));   // grey-brown, a little pale lichen
      vec3 ambB = vec3(0.0075, 0.0100, 0.0120)*(0.6 + 0.4*nb.y) + GOLD*0.012*max(dot(nb, normalize(vec3(-0.85, -0.10, -0.50))), 0.0)*uRivK + vec3(0.016, 0.022, 0.027)*pow(max(dot(nb, -rd), 0.0), 1.5);
      c = alb*occ*(ambB + vec3(0.070, 0.105, 0.122)*1.25*moonB) + alb*occ*GOLD*0.22*lit*(0.55 + 0.45*flow)*exp(-max(lv - 0.13, 0.0)/0.20)*smoothstep(VTOP + 0.3, VTOP - 1.0, h) + alb*GOLDW*0.20*head*exp(-max(lv - 0.13, 0.0)/0.35);
      c += alb*GOLD*0.10*uVine.z*exp(-max(h, 0.0)/0.7);
    } else if(m.x < 1.5){                                                                                                       // the vine: smooth brown bark; her gold glows from inside the furrows of the twist
      float g = max(m.y, 0.0), seam = exp(-pow(g/0.010, 2.0)), near = exp(-g/0.022);
      float pulse = pow(smoothstep(0.42, 0.82, vn(vec2(h*1.1 - uT*3.2, 3.0))), 1.5);                                             // her light goes up through the furrows in pulses                                          // g: how far this point of one stem is from the next stem: 0 in the furrow where two stems meet
      vec3 alb = vec3(0.58, 0.38, 0.25)*(0.40 + 0.55*vn(vec2(th*46.0 + h*2.0, h*2.4)) + 0.28*vn(vec2(h*9.0, th*20.0)))*(0.80 + 0.35*vn(vec2(th*130.0, h*38.0)));   // smooth brown bark: long fine grain, small marks
      float ndk = exp(-pow((fract(h*1.6) - 0.5)/0.10, 2.0));
      c = alb*(1.0 - 0.25*ndk)*(amb*1.3 + key)*(0.20 + 0.80*smoothstep(0.0, 0.036, g)) + alb*GOLD*0.07*lit*near*(0.2 + 0.8*pulse);
      float into = 0.25 + 0.75*pow(max(dot(n, -rd), 0.0), 2.0);                                                                  // the light is inside the furrow: we see it where we look into one
      c += lit*seam*into*(GOLD*0.46*(0.07 + 1.0*pulse) + GOLDW*0.13*pulse) + head*(GOLDW*0.9*seam + alb*GOLDW*0.16*near);
      c += GOLD*0.7*uVine.z*seam*exp(-max(h, 0.0)/0.6);
    } else if(m.x < 2.5){                                                                                                       // a young tendril: the light runs out along it like a pen line
      float tipK = smoothstep(2.14, 1.95, m.z)*smoothstep(0.0, 0.06, m.z), tip = exp(-pow((m.y - m.z)/0.05, 2.0))*tipK, trail = step(m.y, m.z)*(0.10 + 0.90*exp(-(m.z - m.y)/0.32)*tipK);
      float gn = 0.40 + 0.60*smoothstep(0.007, 0.016, m.w);                                                                    // the small ones on the way up pass close to the lens: quieter
      c = vec3(0.050, 0.062, 0.036)*(amb*14.0 + key*5.0) + (GOLD*0.50*trail + GOLDW*1.9*tip)*gn;
    } else if(m.x < 3.5){ vec3 alb = vec3(0.40, 0.31, 0.24)*(0.7 + 0.4*vn(vec2(h*6.0, th*15.0))); c = alb*(amb + key);         // the thin liana: no light in it
    } else {                                                                                                                    // a leaf of the vine: dark glossy green, a pale midrib and side veins; a thread of her light in the midrib once the gold has passed
      float mid = smoothstep(0.16, 0.04, abs(m.z)), side = 0.5*smoothstep(0.40, 0.49, abs(fract((m.y - 0.25*abs(m.z))*6.0) - 0.5));
      vec3 alb = vec3(0.105, 0.250, 0.090)*(0.80 + 0.20*m.z) + vec3(0.07, 0.12, 0.05)*max(mid, side);
      c = alb*(amb*2.6 + key*1.5 + vec3(0.020, 0.028, 0.034)*abs(dot(n, rd))) + GOLD*0.15*lit*mid*(0.3 + 0.7*flow)*smoothstep(0.0, 0.15, m.y); }
    c *= mix(1.0, exp(-t/16.0), 0.85); al = 1.0; zt = t*dot(rd, uFw);
  }
  float tg = (rd.y < -1e-4) ? (uTree.z - ro.y)/rd.y : 1e4;                                                                      // the wet ground it stands on
  if(tg < (hit ? t : 1e4)){ vec3 gp = ro + rd*tg; vec2 gq = gp.xz - uTree.xy; float rg = length(gq);
    float ga = smoothstep(3.0, 2.0, rg + 0.5*(vn(gp.xz*1.1 + 3.0) - 0.5))*smoothstep(0.02, 0.6, tg);
    if(ga > 0.0){ float pxs = tg*px/max(-rd.y, 0.15), tex = 0.55*vn(gp.xz*7.0) + 0.45*vn(gp.xz*19.0 + 5.0);
      vec3 mud = vec3(0.0030, 0.0034, 0.0030)*(0.5 + tex) + vec3(0.020, 0.022, 0.021)*pow(vn(gp.xz*31.0 + 9.0), 5.0)/(1.0 + 60.0*pxs);
      float th0 = uVth[0]; vec2 root = vineR(0.0)*vec2(sin(th0), -cos(th0)); float dr = length(gq - root);
      mud += GOLD*(0.050*uVine.z + 0.020*uVine.y)*exp(-dr/0.55)*(0.5 + tex) + GOLD*0.22*uVine.z*exp(-dr*dr/0.03);
      mud *= mix(1.0, exp(-tg/16.0), 0.85);
      c = c*al*(1.0 - ga) + mud*ga; al = ga + al*(1.0 - ga); zt = min(zt, tg*dot(rd, uFw)); c /= max(al, 1e-4); } }
  return vec4(c*al, al)*uTree.w;
}
vec3 point3(vec3 ro, vec3 rd, vec3 P, float rad, out float disc, out float glow, out float px){
  vec3 v = P - ro; float t = dot(v, rd); float d = sqrt(max(dot(v, v) - t*t, 0.0));
  px = max(t, 0.01)*uZoom/(uRes.x*FOC); float rr = rad + 0.6*px;
  disc = (t > 0.0) ? smoothstep(rr, rr - 1.6*px, d) : 0.0; glow = (t > 0.0) ? exp(-d/(2.2*rr)) : 0.0;
  return v;
}
vec3 redPoint(vec3 col, vec3 ro, vec3 rd){
  if(uRedFig > 0.0){                                                                         // on the bank and at the root: a tiny figure seen from behind, looking up at the tree. Red hat, cream pom-pom, blonde curls, a dark coat. No face
    const float HF = 0.224; vec3 fp = uRed.xyz - vec3(0.0, 0.064, 0.0); float t = dot(fp - ro, uFw)/max(dot(rd, uFw), 1e-3);
    vec3 hp = ro + rd*t - fp; vec2 f = vec2(dot(hp, uRt), dot(hp, uUp))/HF; float px = 1.2*t/(uRes.x*FOC)/HF, k = uRedK*uRedFig;
    if(t > 0.0 && abs(f.x) < 0.45 && f.y > -0.08 && f.y < 1.12){
      float legs = max(abs(abs(f.x) - 0.045) - 0.032, abs(f.y - 0.10) - 0.11);
      float hwc = mix(0.150, 0.105, clamp((f.y - 0.17)/0.50, 0.0, 1.0)), coat = max(abs(f.x) - hwc, abs(f.y - 0.42) - 0.25) - 0.012;
      float hair = min(min(length(f - vec2(0.0, 0.735)) - 0.094, length(f - vec2(-0.064, 0.655)) - 0.060), min(length(f - vec2(0.064, 0.655)) - 0.060, length(f - vec2(0.0, 0.620)) - 0.068)) - 0.010*sin(f.x*70.0)*sin(f.y*64.0 + 1.0);
      float hat = max(length((f - vec2(0.0, 0.772))/vec2(0.106, 0.092)) - 1.0, (0.724 - f.y)/0.09)*0.09;                // tipped back on her head: she is looking up
      float pom = length(f - vec2(0.004, 0.888)) - 0.047, rim = smoothstep(-0.055, 0.0, coat);
      col = mix(col, vec3(0.012, 0.012, 0.016), (1.0 - smoothstep(-px, px, legs))*k);
      col = mix(col, vec3(0.020, 0.024, 0.036) + vec3(0.085, 0.115, 0.140)*rim*(0.45 + 0.55*step(f.x, 0.0)) + GOLD*0.14*uVine.z*rim, (1.0 - smoothstep(-px, px, coat))*k);
      col = mix(col, vec3(0.78, 0.57, 0.25)*(0.62 + 0.18*sin(f.x*85.0 + 3.0*sin(f.y*60.0))), (1.0 - smoothstep(-px, px, hair))*k);
      col = mix(col, vec3(1.75, 0.105, 0.060)*(0.66 + 0.34*smoothstep(-0.10, 0.08, 0.5*f.x + f.y - 0.80)), (1.0 - smoothstep(-px, px, hat))*k);
      col = mix(col, vec3(1.50, 1.36, 1.10), (1.0 - smoothstep(-px, px, pom))*k); }
  }
  float pk = uRedK*(1.0 - uRedFig); if(pk <= 0.0) return col;
  float dd = dot(rd, uFw); if(dd <= 0.0) return col;                                       // after the root: the red thread of fate on the wind. Thin, soft-edged, one red; no core, no glow, no disc
  vec2 P1 = FOC*vec2(dot(rd, uRt), dot(rd, uUp))/dd/uZoom*1920.0; float aa = 0.75*max(1.0, 1920.0/uRes.x), cov = 0.0;
  for(int i = 0; i < 31; i++){ vec4 A = uRib[i], B = uRib[i + 1]; if(A.w <= 0.0 && B.w <= 0.0) continue;
    vec2 ab = B.xy - A.xy; float h = clamp(dot(P1 - A.xy, ab)/max(dot(ab, ab), 1e-6), 0.0, 1.0);
    float d = length(P1 - A.xy - ab*h), hw = mix(A.z, B.z, h);
    cov = max(cov, mix(A.w, B.w, h)*(1.0 - smoothstep(hw - aa, hw + aa, d))); }
  return mix(col, vec3(0.86, 0.060, 0.042)*(0.85 + 0.35*uRedStep), cov*pk);
}
// ---------------------------------------------------------------- the three answers, written in her gold. Each is one pen line (a joined hand) on its own plane; it is drawn on in the order a pen would take, then let go
vec3 answer(int k, vec3 ro, vec3 rd, out float zw){
  vec4 A = uHA[k], B = uHB[k]; zw = B.z; if(A.z <= 0.0) return vec3(0.0);
  vec3 R = uHR[k], U = uHU[k], N = cross(R, U); float dn = dot(rd, N); if(abs(dn) < 1e-9) return vec3(0.0);
  float t = dot(uHC[k] - ro, N)/dn; if(t <= 0.02) return vec3(0.0);
  vec3 p = ro + rd*t - uHC[k]; vec2 q = vec2(dot(p, R)/dot(R, R), dot(p, U)/dot(U, U)) + 0.5; vec3 c = vec3(0.0);
  if(k == 0 && abs(q.x - 0.5) < 1.7 && abs(q.y - 0.5) < 4.2){                                // the fireflies that gather into the first answer, and scatter from it
    for(int i = 0; i < 48; i++){ vec4 f = uFf[i]; if(f.w <= 0.0) continue; vec2 e = (q - f.xy)*vec2(4.0, 1.0); float d2 = dot(e, e), r = f.z;
      c += GOLDW*f.w*(2.6*exp(-d2/(r*r)) + 0.05*exp(-sqrt(d2)/(3.5*r))); } }
  if(A.w > 0.0){ vec2 e = (q - vec2(0.44, 0.5))*vec2(4.0, 1.0); float a = A.w*exp(-dot(e, e)/1.3), ca = cos(a), sa = sin(a); q = vec2(ca*e.x - sa*e.y, sa*e.x + ca*e.y)/vec2(4.0, 1.0) + vec2(0.44, 0.5); }   // letting go, it curls
  if(q.x < 0.004 || q.x > 0.996 || q.y < 0.02 || q.y > 0.98) return c*A.z;
  vec2 sm = texture(uHand, vec2(q.x, (float(k) + q.y)/3.0)).rg; float d = sm.r*0.25, T = sm.g, w = B.x;
  float on = (1.0 - smoothstep(A.x - 0.012, A.x, T))*smoothstep(A.y - 0.012, A.y, T)*smoothstep(0.02, 0.07, q.y)*(1.0 - smoothstep(0.93, 0.98, q.y))*(1.0 - smoothstep(B.w - 0.014, B.w + 0.004, q.x));
  float core = exp(-pow(d/w, 2.0)), halo = exp(-d/(3.2*w)), bead = 1.0;
  if(B.y > 0.0){ float bi = T*210.0; bead = mix(1.0, (0.34 + 1.0*pow(0.5 + 0.5*cos(6.2832*bi), 2.0))*(0.74 + 0.26*sin(uT*5.0 + 6.2832*h1(uint(int(floor(bi))) + 77u))), B.y); }   // the first answer is made of fireflies: beads of light along the line
  float tip = exp(-pow((T - A.x + 0.006)/0.016, 2.0))*step(0.002, A.x)*(1.0 - step(1.0, A.x))*exp(-pow(d/(2.4*w), 2.0));          // the point of the pen
  float cur = 0.88 + 0.12*sin(42.0*T - uT*3.0);                                                                                   // light runs along the line like a current
  c += (mix(GOLD, GOLDW, 0.55)*1.75*core*cur + GOLD*0.34*halo)*on*bead + GOLDW*2.4*tip*(1.0 - smoothstep(B.w - 0.014, B.w + 0.004, q.x));
  return c*A.z;
}

void main(){
  vec2 frag = gl_FragCoord.xy + uJit; gGap = 0.0;
  vec2 sc = (frag - 0.5*uRes)/uRes.x*uZoom;
  vec3 rd = normalize(uFw*FOC + uRt*sc.x + uUp*sc.y), ro = uCam;
  // the world behind the leaves: under the canopy (water, river, far trunks) or over it (crowns, river, sky)
  vec3 below = vec3(0.0), above = vec3(0.0);
  if(uAbove < 1.0){ float sh = min(ro.y, 3.0)/max((ZB - ro.z)/max(rd.z, 0.25), 2.0);                 // the far bank: the forest stands at the water's edge, a little below the horizon
    below = (rd.y < -sh - 1e-3) ? groundView(ro, rd, sh) : farBG(vec3(rd.x, rd.y + sh, rd.z)) + ceilView(ro, rd); }
  gSD = normalize(mix(rd, normalize(uFwM*FOC + uRtM*sc.x + uUpM*sc.y), 0.6));
  if(uAbove > 0.0) above = (rd.y < -1e-3) ? canopyView(vec3(ro.x - uCanOff, max(ro.y, HC + 3.4), ro.z), rd) : sky(rd) + vec3(0.62, 0.72, 1.0)*stars(gSD)*uStarK + moonGlow(rd);
  vec3 col = mix(below, above, uAbove);
  // the plants: nine slabs across the way we look, each with its leaves, lianas, trunks and fireflies
  float cr = cos(uRoll), sr = sin(uRoll); vec2 scl = vec2(cr*sc.x - sr*sc.y, sr*sc.x + cr*sc.y);
  float k0 = floor(uS/DZ), zh = uHero.z - uS; bool heroDone = (uHeroA.x <= 0.0 || zh < 0.05);
  vec3 ry = vec3(uFw.y*FOC + uRt.y*sc.x + uUp.y*sc.y);
  vec3 bkAdd = vec3(0.0); float zbk = 1e3; vec4 bk = vec4(0.0); bool bankDone = true;
  if(uBk.x > 0.0){ bk = bank(ro, rd, bkAdd, zbk); bankDone = (bk.a <= 0.0); }
  float ztr = 1e3; vec4 tr = vec4(0.0); if(uTree.w > 0.0) tr = treeView(ro, rd, ztr);
  float zred = dot(uRed.xyz - ro, uFw);
  // the bank, the tree, her red point and the leaf each stand at their own depth: drawn between the slabs of leaves, farthest first
  vec3 aw0, aw1, aw2; float zw0, zw1, zw2; aw0 = answer(0, ro, rd, zw0); aw1 = answer(1, ro, rd, zw1); aw2 = answer(2, ro, rd, zw2); vec3 aw2n = aw2*uSkyOpen; aw2 *= (1.0 - uSkyOpen)*(0.25 + 0.75*gGap);   // the third begins in the gaps of the roof of leaves and is whole in the open sky
  float zI[7]; bool dI[7]; zI[0] = zbk; dI[0] = bankDone; zI[1] = ztr; dI[1] = (tr.a <= 0.0); zI[2] = zred; dI[2] = !(uRedK > 0.0 && uRedFront < 0.5); zI[3] = zh; dI[3] = heroDone;
  zI[4] = zw0; dI[4] = (uHA[0].z <= 0.0); zI[5] = zw1; dI[5] = (uHA[1].z <= 0.0); zI[6] = zw2; dI[6] = (uHA[2].z <= 0.0);
#define ITEMS(ZK) for(int qi = 0; qi < 7; qi++){ int wh = -1; float zm = ZK; for(int e = 0; e < 7; e++) if(!dI[e] && zI[e] > zm){ zm = zI[e]; wh = e; } if(wh < 0) break; dI[wh] = true; if(wh == 0) col = mix(col, bk.rgb, bk.a) + bkAdd; else if(wh == 1) col = col*(1.0 - tr.a) + tr.rgb; else if(wh == 2) col = redPoint(col, ro, rd); else if(wh == 3) col = heroLeaf(col, scl, zh, rd); else if(wh == 4) col += aw0; else if(wh == 5) col += aw1; else col += aw2; }
  for(int j = NL - 1; j >= 0; j--){
    float kf = k0 + 1.0 + float(j), zk = kf*DZ - uS;
    ITEMS(zk)
    float fade = smoothstep(float(NL)*DZ, (float(NL) - 1.6)*DZ, zk)*smoothstep(0.10, uNear, zk)*smoothstep(0.28*uCross, 0.66*uCross, zk);   // a leaf that would cross the lens faster than the eye can follow thins out before it gets there: it slides past, it never blinks
    if(fade <= 0.0) continue;
    float coc = 0.022*abs(1.0/zk - 1.0/uFocus) + 1.0/uRes.x, soft = coc*zk/FOC;
    float Yt = ro.y + ry.x*zk/FOC, Yw0 = mix(10.0, Yt, uWaterK), crad = uCorr + uCone*zk, haze = 1.0 - exp(-zk/6.0), fk = max(smoothstep(HC + 2.0, HC - 1.0, Yt), uFlyUp);
    for(int br = 0; br < 2; br++){                                                           // two sets of the same slabs (see the page script): A, the old flight's own, until 98.2 s; B from 99.0 s; a slow dissolve between
      float wb = (br == 0) ? 1.0 - uXf : uXf; if(wb <= 0.0) continue;
      vec2 cp = (br == 0) ? uCPA : uCP, rot = (br == 0) ? uRotA : uRot; float fdy = uFlyDY - ((br == 0) ? uXfF : 0.0), kb = (br == 0) ? kf - uXfN : kf;   // kb: which slab this is in its own set's count
      vec2 L = cp + (scl + rot)*zk/FOC; float Yw = Yw0, refl = 1.0, sf = soft;
      if(Yw < 0.0){ L.y -= 2.0*Yw; L.x += 0.02*sin(Yw*31.0 + uT*1.7 + L.x*3.0)*min(1.0, -Yw*4.0); refl = 0.62*exp(Yw/1.1); sf *= 1.0 + 3.0*min(-Yw, 1.0); Yw = -Yw; }
      vec2 corr = mix(cp + rot*zk/FOC, uAxis, uCorrB);
      float vein, rim; float a = plantLayer(L, kb, sf, Yw, Yt, corr, crad, vein, rim);
      float lum = min(dot(col, vec3(0.3, 0.6, 0.1)), 0.7);
      vec3 lc = vec3(0.0016, 0.0026, 0.0020) + vec3(0.0055, 0.0050, 0.0036)*haze;
      lc += vec3(0.035, 0.15, 0.03)*lum*0.30;                                                // green only where light passes through a leaf
      lc += GOLD*vein*uVeinK*(0.018 + 0.30*lum)*(0.8 + 0.2*sin(uT*0.9 + kb));
      lc += GOLD*rim*(0.010 + 0.75*lum);
      col = mix(col, lc, a*fade*refl*wb);
      vec2 Lf = L; float stw = 1.0;
      Lf.y += -fdy + uWind*0.24*sin(0.5*L.x + 1.9*kb + 0.8*uT);                              // the wind carries them level with us, bending along the flow: never falling
      if(uStream > 1.0){ Lf.x = cp.x + (L.x - cp.x)/uStream; stw = uStream; }
      col += flyLayer(Lf + vec2(0.37, 0.61), kb, sf*1.2/sqrt(stw))*fade*refl*fk*wb*mix(1.0, 1.25, clamp((stw - 1.0)/3.0, 0.0, 1.0)); }
  }
  ITEMS(-1.0)
  col += aw2n*(1.0 - tr.a);
  if(uMist > 0.0){ float mx = scl.x*9.0 + uCP.x, my = scl.y*9.0 + 0.30*sin(0.33*mx + 0.6*uT);   // mist torn along with the wind
    float n = 0.65*vn(vec2(mx*0.11, my*1.9 + 3.0)) + 0.35*vn(vec2(mx*0.31 + 9.0, my*4.3));
    col += vec3(0.030, 0.036, 0.042)*uMist*smoothstep(0.42, 0.85, n); }
  for(int i = 0; i < 4; i++){ vec4 q = uDrops[i]; if(q.w <= 0.0) continue;
    vec3 vv = q.xyz - ro; float tt = dot(vv, rd); if(tt <= 0.0) continue; vec3 dl = ro + rd*tt - q.xyz;
    float dh = length(dl.xz), r = 0.008 + 1.2*tt/(uRes.x*FOC);
    col += GOLDW*q.w*1.6*exp(-dh*dh/(r*r))*smoothstep(-0.02, 0.03, dl.y)*smoothstep(0.34, 0.0, dl.y); }
  if(uRedK > 0.0 && uRedFront >= 0.5 && !(tr.a > 0.5 && zred > ztr)) col = redPoint(col, ro, rd);
  col += mix(vec3(1.0, 0.56, 0.17), vec3(1.0, 0.80, 0.47), 0.3)*uGlowK;                    // the gold of the seam, in the air itself
  fragColor = vec4(max(col, 0.0)*uWeight, uWeight);
}
