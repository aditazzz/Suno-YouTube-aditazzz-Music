from pathlib import Path
ROOT = str(Path(__file__).resolve().parents[4]) + "/"
"""Sky plate: a perspective view out of a Poly Haven night HDRI's 8k preview (CC0), camera-matched to the Blender foreground."""
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
LIB = ROOT + 'assets/earth_library/polyhaven/hdris/'
_c = {}
def pano(name):
    if name not in _c:
        _c[name] = np.asarray(Image.open(f'{LIB}{name}/{name}_preview.jpg').convert('RGB'))
    return _c[name]
def view(name, W, H, yaw_deg, pitch_deg, lens_mm=24.0, sensor=36.0):
    a = pano(name); PH, PW = a.shape[:2]
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float64)
    px = (xs + 0.5 - W / 2) / W * sensor / lens_mm
    py = -(ys + 0.5 - H / 2) / W * sensor / lens_mm
    # camera looks along +Y, up +Z; pitch up, then yaw about Z
    p = np.radians(pitch_deg); yw = np.radians(yaw_deg)
    dx, dy, dz = px, np.ones_like(px), py
    dy, dz = dy * np.cos(p) - dz * np.sin(p), dy * np.sin(p) + dz * np.cos(p)
    dx, dy = dx * np.cos(yw) + dy * np.sin(yw), -dx * np.sin(yw) + dy * np.cos(yw)
    n = np.sqrt(dx * dx + dy * dy + dz * dz)
    az = np.arctan2(dx, dy); el = np.arcsin(dz / n)
    u = (az / (2 * np.pi) + 0.5) % 1.0 * PW - 0.5
    v = np.clip((0.5 - el / np.pi) * PH - 0.5, 0, PH - 1.001)
    x0 = np.floor(u).astype(int); y0 = np.floor(v).astype(int)
    fx = (u - x0)[..., None]; fy = (v - y0)[..., None]
    x1 = (x0 + 1) % PW; x0 %= PW; y1 = np.minimum(y0 + 1, PH - 1)
    r = (a[y0, x0] * (1 - fx) + a[y0, x1] * fx) * (1 - fy) + (a[y1, x0] * (1 - fx) + a[y1, x1] * fx) * fy
    return (r / 255.0).astype(np.float32), el
if __name__ == '__main__':
    tiles = []
    for name, yaw, pitch, lens in (('rogland_clear_night', 10, 16, 20), ('rogland_clear_night', 75, 16, 20), ('rogland_clear_night', 43, 22, 18),
                                   ('dikhololo_night', -30, 14, 20), ('dikhololo_night', -70, 14, 20), ('qwantani_night_puresky', 0, 16, 20)):
        im, _ = view(name, 520, 292, yaw, pitch, lens)
        tiles.append(Image.fromarray((np.clip(im * 1.6, 0, 1) * 255).astype(np.uint8)))
    s = Image.new('RGB', (1560, 584))
    for i, t in enumerate(tiles): s.paste(t, ((i % 3) * 520, (i // 3) * 292))
    s.save('sky_look.jpg', quality=88)
