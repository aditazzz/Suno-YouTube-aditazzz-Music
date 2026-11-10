// (CREATIVE.md 21.5 / 22.4) the sunrise run as each lens sees it, shared by LivingEarth and CloudLayer so the gold lies ON
// her surface and clouds (light, not a filter). The same constants as Atmosphere's run (glsl/atmosphere.ts): eps is the
// sun's elevation above her limb (mrad), a pure function of the pose; along = how far along her limb the gold has run;
// depth = how far inside her limb this point sits as the lens sees it (0 at the limb).
export const SUNRISE = /* glsl */ `
uniform float uSeq; uniform float uRunScale;
vec3 sunriseAt(vec3 Pw, vec3 ro, vec3 S){
  float eps = (acos(clamp(dot(normalize(-ro), S), -1.0, 1.0)) - asin(min(1.0, 1.0 / length(ro)))) * 1000.0;
  float win = uSeq * (1.0 - smoothstep(25.0, 45.0, abs(eps)));
  if (win < 0.001) return vec3(0.0);
  vec3 rd = normalize(Pw - ro); vec3 pc = ro + rd * max(-dot(ro, rd), 0.0); vec3 nc = normalize(pc);
  vec3 c = normalize(-ro); vec3 sp = S - c * dot(S, c), np = nc - c * dot(nc, c);
  float la = acos(clamp(dot(np, sp) / max(length(np) * length(sp), 1e-6), -1.0, 1.0));
  float runA = uRunScale * clamp(0.018 + 0.038 * max(eps, 0.0), 0.018, 0.34);
  float along = smoothstep(-0.3, 0.3, eps) * exp(-pow(la / runA, 4.0)) * win;
  return vec3(along, smoothstep(0.0, 5.0, eps), max(1.0 - length(pc), 0.0));
}`;
