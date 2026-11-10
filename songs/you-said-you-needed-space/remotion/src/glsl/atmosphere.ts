// Single-scattering atmosphere (Rayleigh + Mie), integrated along the view ray through a shell around her.
// Used by Atmosphere (the sky shell seen from space, and from inside on the dive). Units: Earth radius = 1.
// Scale height is exaggerated (real ~8 km = 0.00125) so the glow reads as breath at film distances.
export const ATMOS = /* glsl */ `
uniform vec3 uSun; uniform float uPreGain; uniform float uSeq; uniform float uRunScale;
uniform float uAtmR;
uniform float uBreath;     // 0..1 her breath
uniform float uAtmGain;    // overall intensity (dawn fade, emotion)
const vec3 BETA_R = vec3(5.8, 13.5, 33.1);   // Rayleigh (relative), atmospheric blue
const float BETA_M = 18.0;
vec2 raySphere(vec3 ro, vec3 rd, float r){
  float b = dot(ro, rd); float c = dot(ro, ro) - r*r; float h = b*b - c;
  if (h < 0.0) return vec2(1e9, -1e9);
  h = sqrt(h); return vec2(-b - h, -b + h);
}
// optical depth toward the sun from point p (cheap: analytic-ish via 4 samples)
float sunDepth(vec3 p, float H){
  vec2 s = raySphere(p, uSun, uAtmR);
  float L = max(s.y, 0.0); float od = 0.0;
  for (int i=0;i<4;i++){ vec3 q = p + uSun * (L * (float(i)+0.5)/4.0); od += exp(-(length(q)-1.0)/H); }
  // shadowed by her own body: soft so the terminator glows warm instead of clipping
  // her shadow, soft: how deep the sun ray dips below her surface (closest approach), smooth so no banding
  float along = dot(p, uSun);
  float closest = along > 0.0 ? length(p) : length(p - uSun * along);
  float shadow = smoothstep(1.0 + 0.8 * H, 1.0 - 0.8 * H, closest);
  return od * L / 4.0 + shadow * 40.0;
}
// angle around her disc, as the lens at ro sees it, between the rim point nc and the sun (both projected on the plane
// facing the lens from her centre): 0 at the part of her rim the sun sits behind or beside
float limbAngle(vec3 nc, vec3 ro){
  vec3 c = normalize(-ro);
  vec3 sp = uSun - c * dot(uSun, c), np = nc - c * dot(nc, c);
  return acos(clamp(dot(np, sp) / max(length(np) * length(sp), 1e-6), -1.0, 1.0));
}
vec3 scatter(vec3 ro, vec3 rd, out vec3 transmit){
  float H = 0.0055 * (1.0 + 0.06 * uBreath);  // she breathes: the shell swells a little in height
  float Hm = 0.0018;
  vec2 a = raySphere(ro, rd, uAtmR);
  transmit = vec3(1.0);
  if (a.y < 0.0) return vec3(0.0);
  float t0 = max(a.x, 0.0), t1 = a.y;
  vec2 g = raySphere(ro, rd, 1.0);
  bool hit = g.x > 0.0 && g.y > g.x;
  if (hit) t1 = min(t1, g.x);
  float L = t1 - t0; if (L <= 0.0) return vec3(0.0);
  const int N = 32;
  float ds = L / float(N);
  float atmJit = fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715))));
  vec3 sumR = vec3(0.0), sumM = vec3(0.0); float odR = 0.0, odM = 0.0;
  for (int i=0;i<N;i++){
    vec3 p = ro + rd * (t0 + ds * (float(i) + atmJit)); // jittered per pixel: no contour bands along the limb
    float hgt = length(p) - 1.0;
    float dR = exp(-hgt / H) * ds, dM = exp(-hgt / Hm) * ds;
    odR += dR; odM += dM;
    float sd = sunDepth(p, H);
    vec3 tau = BETA_R * (odR + sd) * 8.0 + BETA_M * 1.1 * (odM + sd * 0.4) * 8.0;
    vec3 att = exp(-tau * 0.012);
    sumR += dR * att; sumM += dM * att;
  }
  float mu = dot(rd, uSun);
  float phR = 3.0 / (16.0*PI) * (1.0 + mu*mu);
  float gg = 0.76; float phM = 3.0/(8.0*PI) * ((1.0-gg*gg)*(1.0+mu*mu)) / ((2.0+gg*gg)*pow(1.0+gg*gg-2.0*gg*mu, 1.5));
  transmit = exp(-(BETA_R * odR + BETA_M * odM) * 8.0 * 0.012);
  // her outer air: a soft, wide blue falloff beyond the dense limb (thin high air, lit where the sun reaches it)
  float hc = length(ro + rd * max(-dot(ro, rd), 0.0)) - 1.0;   // closest approach height
  float lit = smoothstep(-0.3, 0.4, dot(normalize(ro + rd * max(-dot(ro, rd), 0.0)), uSun)) ;
  vec3 outer = hit ? vec3(0.0) : vec3(0.10, 0.28, 0.85) * exp(-max(hc, 0.0) / 0.022) * 0.08 * (0.25 + 0.75 * lit);
  // sunrise from orbit (creative direction 13 S1): where the sun grazes her limb, the low air burns gold-orange.
  // Only near the terminator, only looking toward the sun, fading along the rim away from it.
  vec3 pc = ro + rd * max(-dot(ro, rd), 0.0); vec3 nc = normalize(pc);
  float term = exp(-pow(dot(nc, uSun), 2.0) / 0.012);
  float toward = smoothstep(0.75, 0.995, dot(rd, uSun));
  float lowAir = exp(-abs(hc) / 0.006);
  // a sunrise is a sequence (creative direction 18 M3): while the sun is still behind her limb the band there warms
  // from deep red (never pink) to gold as it nears the edge (about a bar of approach), then the sun breaks
  vec3 sc = ro + uSun * max(-dot(ro, uSun), 0.0);
  float sunDepth = length(sc) - 1.0;                 // < 0: the sun is behind her, by this much (in her radii)
  float near = smoothstep(-0.06, 0.0, sunDepth);
  vec3 dawnC = mix(vec3(0.75, 0.10, 0.03), vec3(1.0, 0.62, 0.22), smoothstep(-0.03, 0.005, sunDepth));
  // (21.5) a sunrise is a sequence, keyed off the sun's elevation above her limb as THIS lens sees it (eps, mrad): a pure
  // function of the pose, so both ends of the C01 loop get the same light, and on the slide eps IS seam time (~0.15
  // mrad/frame). uSeq 0 (the POC, the long-lens holds) = the old constant look. Before the break a dim deep-red band
  // that thickens as the sun nears; at the break the gold starts at the sun and runs along her limb both ways (runA, a
  // visible front, wider per mrad on a wider view: uRunScale); beyond the front the limb stays blue.
  float eps = (acos(clamp(dot(normalize(-ro), uSun), -1.0, 1.0)) - asin(min(1.0, 1.0 / length(ro)))) * 1000.0;
  float warmOn = smoothstep(-0.3, 0.3, eps);
  float la = limbAngle(nc, ro);
  float runA = uRunScale * clamp(0.018 + 0.038 * max(eps, 0.0), 0.018, 0.34);
  float alongNew = warmOn * exp(-pow(la / runA, 4.0));
  // the sequence only lives within ~a bar and a half of a break (|eps| < 25-45 mrad) and only on the wide lenses (uSeq)
  float win = uSeq * (1.0 - smoothstep(25.0, 45.0, abs(eps)));
  float alongL = mix(exp(-pow(la / 0.28, 2.0)), alongNew, win);
  float preNear = win * (1.0 - warmOn) * exp(-pow(la / (0.22 * uRunScale), 2.0)); // near the sun, before the break
  float preBand = preNear * smoothstep(-14.0, -0.5, eps);                           // ... and how far into the approach
  if (!hit) outer += dawnC * term * toward * lowAir * (0.35 + 0.9 * near) * alongL;
  // art direction: her limb (rays that miss her) carries the breath and reads strong; the haze laid over her face
  // (rays that hit her) is held back so the day side keeps its colour and contrast
  float limbGain = hit ? 0.45 : 0.70;
  // the limb's dense core stays blue, not clipped white: Rayleigh carries it, the warm Mie only near the sun
  vec3 mie = sumM * BETA_M * phM * 3.0 * vec3(1.0, 0.72, 0.42) * mix(0.35, 1.0, smoothstep(0.6, 0.98, mu));
  if (!hit) mie *= mix(vec3(0.2), vec3(1.0, 0.68, 0.40), alongL); // (19.3) the warm forward glow sits on the rim near the sun (reddened by the long path); the rest stays blue
  vec3 col = (sumR * BETA_R * phR * vec3(0.75, 0.92, 1.2) + mie) * 8.0 * 1.25 * limbGain + outer;
  // the terminator seen from above (creative direction 15, S3): her air over the day/night line is lit at grazing
  // incidence and burns as a narrow gold line turning violet into the night, readable from a few thousand km
  // backlit (creative direction 18 B4): looking at her limb with the sun just behind it, her air is a thin layered
  // ring, deep red-orange at the surface, gold, pale yellow-white, then blue into black, never a clipped white band
  if (!hit) {
    float back = smoothstep(0.55, 0.97, mu);
    float h = max(hc, 0.0);
    float sunSide = smoothstep(-0.35, 0.05, dot(nc, uSun)); // the ring burns where the sun is behind it
    // (19.3/20.5) the warm layers burn only along the limb near the sun (angle along the rim from the point under the
    // sun, as seen from the lens); away from it her ring cools to blue
    float along = alongL;
    vec3 ring = (vec3(1.0, 0.30, 0.07) * exp(-pow(h / 0.0012, 2.0))
              + vec3(1.0, 0.64, 0.22) * exp(-pow((h - 0.0026) / 0.0014, 2.0))
              + vec3(1.0, 0.90, 0.70) * exp(-pow((h - 0.005) / 0.0018, 2.0)) * 0.45) * along
              + vec3(0.22, 0.42, 1.0) * exp(-h / 0.011) * 0.30 * (1.0 - 0.6 * along);
    col = mix(col, ring * 0.5 * sunSide * uAtmGain + col * 0.2, back);
  }
  // (19.1) the air over her dusk zone, seen from above, is lit by reddened grazing sunlight: warm, not blue haze, so
  // the band reads warm over clear ocean too
  if (hit) {
    float m = dot(normalize(ro + rd * g.x), uSun);
    col *= mix(vec3(1.0), vec3(1.45, 0.90, 0.40), exp(-pow((m - 0.06) / 0.14, 2.0)));
  }
  // (creative direction 18 B1: the day/night line is light lying on her surface, in LivingEarth/CloudLayer, not a
  // line drawn in her air. Her air only carries the real orange arc where the terminator meets her limb.)
  if (!hit) {
    // (19.1) the short orange-to-gold arc where the terminator crosses her limb, ~10-15 deg of limb either side
    float x = dot(nc, uSun);
    // (when the sun sits at or behind her limb the whole limb is her terminator; then the backlit ring carries it, not this)
    float arc = exp(-pow(x / 0.22, 2.0)) * exp(-abs(hc) / 0.010) * smoothstep(0.02, 0.15, sunDepth);
    col = mix(col, col * 0.4 + mix(vec3(1.0, 0.40, 0.10), vec3(1.0, 0.66, 0.26), smoothstep(-0.1, 0.15, x)) * 0.35 * uAtmGain, arc * 0.8);
    // (19.3) a sunrise's light runs along her limb both ways: near the sun the rim turns gold to orange-white, thinning
    // and cooling to her blue with distance (about 15-20% of the visible limb each way)
    float nearSun = smoothstep(0.80, 0.995, mu) * alongL; // close to the sun, along her rim
    col = mix(col, col * vec3(1.1, 0.74, 0.36) + vec3(0.22, 0.11, 0.025) * exp(-abs(hc) / 0.006) * uAtmGain, nearSun);
  }
  // (21.5) the sequence's own light (win 1 only)
  if (win > 0.001) {
    float grow = smoothstep(0.0, 5.0, eps);                 // 0 at the break .. 1 at ~C01 frame 30
    if (!hit) {
      float h = max(hc, 0.0);
      // the limb past the run: her blue, never lavender; a very faint thin high air out to the shell (her air, not a glow)
      vec3 blue = dot(col, vec3(0.30, 0.59, 0.11)) * vec3(0.50, 0.80, 1.30) * 0.80 + vec3(0.012, 0.030, 0.085) * exp(-h / 0.030) * smoothstep(0.090, 0.050, h) + vec3(0.0009, 0.0018, 0.0048) * smoothstep(0.090, 0.060, h);
      col = mix(col, blue, win * (1.0 - alongL));
      // before the break: near the sun the blue is gone from the lowest air (red plus blue would read pink): deep red,
      // dim, thin, thickening as the sun nears
      float prof = exp(-pow(h / (0.0022 + 0.0016 * smoothstep(-14.0, -0.5, eps)), 2.0));
      float kill = exp(-pow(h / 0.0060, 2.0));
      col = mix(col, col * (1.0 - kill) * 0.6, preNear);
      col += vec3(0.30, 0.050, 0.010) * prof * uPreGain * preBand;
      // the gold band itself, thickening as it runs; held to gold (a clipped band is white, and white isn't a sunrise)
      col += win * alongL * vec3(1.0, 0.58, 0.20) * exp(-h / mix(0.005, 0.021, grow)) * mix(0.55, 0.42, grow);
      float y = dot(col, vec3(0.30, 0.59, 0.11));
      vec3 gold = vec3(1.0, 0.60, 0.20) * min(y, 0.36) / 0.68;
      col = mix(col, gold, win * alongL * smoothstep(0.02, 0.08, y));
    } else {
      // low sun through her air over the near-limb night: the air lit gold along the run (depth = how far inside her limb)
      float depth = max(1.0 - length(pc), 0.0);
      // before the break the same deep-red band continues just inside her limb, with no blue in it (red + blue = pink)
      float pk = exp(-pow(depth / 0.0035, 2.0)) * preNear;
      col = mix(col, col * vec3(0.55, 0.35, 0.20), pk);
      col += vec3(0.26, 0.042, 0.008) * exp(-pow(depth / 0.0022, 2.0)) * uPreGain * preBand;
      // (22.4) only her low air right at the limb, as the lens sees it through it; the gold on her is LivingEarth/CloudLayer
      col += win * alongL * vec3(1.0, 0.50, 0.15) * exp(-depth / 0.004) * mix(0.30, 0.34, grow);
      col += win * vec3(0.0030, 0.0055, 0.0130); // her air's own faint blue over the night, so the night is a surface, not black
    }
  }
  return col;
}
`;
