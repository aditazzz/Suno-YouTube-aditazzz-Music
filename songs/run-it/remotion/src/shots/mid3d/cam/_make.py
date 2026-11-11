#!/usr/bin/env python3
"""Writes the camera paths of the 3D middle (s46-s63), one JSON per shot. The JSONs are the data the Remotion stand-in
reads (../camera.ts) and the real Blender build reuses. Edit here and re-run (python3 _make.py), or edit the JSONs.

Conventions (same for the Blender build):
  units = metres, Y up, the camera starts looking down -Z at the near city. Blender: x_b = x, y_b = -z, z_b = y.
  t = film seconds (30 fps, frame = round(t*30)). fov = VERTICAL degrees for the 16:9 frame (9:16 widens it, camera.ts).
  roll = degrees, + turns the picture counter-clockwise (s58: world +X becomes screen-up).
  Between keys: monotone cubic (Catmull-Rom tangents, clamped; no overshoot). still = zero velocity at that key.
  cut = no interpolation from the previous key (a hard cut lands on this key's t).
World anchors: near city facade z=0, hero window (4,18,0); bay z -16..-270; far skyline facade z=-270;
sun final (0,220,-900); the car set is a separate location at x=3000 (the "bass tower" lies along X there).
"""
import json, os
X0 = 3000
def K(t, pos, tgt, fov, roll=0, **kw): return dict(t=t, pos=pos, target=tgt, fov=fov, roll=roll, **kw)
P = {
 's46': ("Run it (run it): the match-cut to 3D, same slow push toward one lit window, real shadows switch on", [
   K(116.21, [0, 10, 110], [0, 15, 0], 22, cut=True),
   K(122.08, [2, 14.5, 58], [3, 16.5, 0], 24)]),
 's47': ("Ooh, look what we can do: the push continues to the window (reflections, then full light on 'do')", [
   K(124.04, [3.4, 16.8, 26], [4, 17.6, 0], 27),
   K(125.70, [4, 18, 5], [4, 18, -10], 32)]),
 's48': ("push through the window on the bar-65 downbeat and out over the bay; then a slow crane up", [
   K(126.00, [4, 18, 0.2], [4, 18, -20], 40),
   K(126.50, [4, 19.5, -24], [4, 24, -300], 46),
   K(127.96, [2, 26, -46], [0, 60, -700], 44)]),
 's49': ("slow crane while the moons rise", [K(129.91, [-4, 31, -58], [0, 80, -800], 44)]),
 's50': ("slow orbit as the moons start orbiting each other", [K(131.87, [-14, 32, -64], [-2, 90, -800], 44)]),
 's51': ("(tasteful, beat 3) the orbit eases", []),
 's52': ("(weird) drift down", []),
 's53': ("(ocean disappears, beat 3) still descending", [K(133.82, [-12, 20, -70], [0, 70, -800], 43)]),
 's54': ("low over the water: every wave rises from the centre out", [K(135.78, [-2, 5, -80], [0, 40, -700], 42)]),
 's55': ("sixty frames: a slow glide forward (stepped before 'wait', buttery after)", [K(136.76, [0, 5.2, -84], [0, 42, -700], 42)]),
 's56': ("delete Mondays: glide continues under the calendar", [K(137.74, [1, 5.6, -88], [0, 46, -700], 42)]),
 's57': ("wide: pull back and tilt up; the gizmo drags the sun to (960,470), where the dot was", [
   K(139.69, [0, 16, -64], [0, 115, -600], 46),
   K(141.64, [1.5, 16.4, -66], [0, 115, -600], 46)]),
 's58': ("CUT to the car set: pillarbox 9:16 + roll 90, the car drives straight up the 'tower'; unroll into the cut back", [
   K(141.64, [X0 - 4, 5, 34], [X0 - 4, 5, 0], 34, 0, cut=True),
   K(141.94, [X0 - 2, 5, 34], [X0 - 2, 5, 0], 34, 90),
   K(143.35, [X0 + 10, 5, 34], [X0 + 10, 5, 0], 34, 90),
   K(143.59, [X0 + 12, 5, 34], [X0 + 12, 5, 0], 34, 0)]),
 's59': ("CUT back to the bay: slow lateral truck while the city claps on the snare", [
   K(143.60, [-26, 6, -70], [-4, 42, -600], 40, cut=True),
   K(145.55, [0, 4, -70], [0, 30, -600], 40)]),
 's60': ("barrel roll part 1, 0 -> 180 by bar 75 beat 3", [K(146.53, [0, 4.3, -72], [0, 30, -600], 40, 180)]),
 's61': ("barrel roll part 2, 180 -> 360, lands upright on totality (147.51); then hold, a slow 2% push", [
   K(147.51, [0, 4.5, -74], [0, 30, -600], 40, 360, still=True),
   K(149.47, [0, 4.6, -77], [0, 30, -600], 40, 360)]),
 's62': ("still (slow push) then the stutter: the camera itself is fine, the world time steps 24/8/2 fps", [
   K(151.40, [0, 4.7, -80], [0, 30, -600], 40, 360, still=True)]),
 's63': ("CRASH: frozen on the last good camera (+ a 1 px screen jitter in Crash.tsx)", [
   K(151.42, [0, 4.7, -80], [0, 30, -600], 40, 360, cut=True, still=True),
   K(155.34, [0, 4.7, -80], [0, 30, -600], 40, 360, still=True)]),
}
here = os.path.dirname(os.path.abspath(__file__))
for sid, (what, keys) in P.items():
    json.dump(dict(shot=sid, what=what, keys=keys), open(os.path.join(here, f'{sid}.json'), 'w'), indent=1)
print('wrote', len(P), 'camera paths')
