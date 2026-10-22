"""Build the Florida-wide night map (outer level around the Cape): land mask from GSHHS full-resolution coastlines and
point lights distributed from NASA's Black Marble city-lights density (three-globe example earth-night.jpg, public domain
NASA imagery).  usage: python3 make_florida.py /path/to/basemap_data  -> assets/fl_land.png, assets/fl_lights.png, assets/fl_meta.json
"""
import sys, os, json, numpy as np, cv2
D = sys.argv[1]
LON0, LON1, LAT0, LAT1 = -86.0, -75.5, 23.5, 33.5
W = 7000
kx = np.cos(np.radians((LAT0 + LAT1) / 2))
H = int(round(W * (LAT1 - LAT0) / ((LON1 - LON0) * kx)))
meta = [l.split() for l in open(os.path.join(D, "gshhsmeta_f.dat"))]
raw = open(os.path.join(D, "gshhs_f.dat"), "rb")
land = np.zeros((H, W), np.uint8)
def to_px(lonlat):
    x = (lonlat[:, 0] - LON0) / (LON1 - LON0) * W
    y = (LAT1 - lonlat[:, 1]) / (LAT1 - LAT0) * H
    return np.stack([x, y], 1)
n_used = 0
for m in meta:
    level = int(m[0]); south = float(m[3]); north = float(m[4]); off = int(m[5]); nb = int(m[6])
    if south > LAT1 or north < LAT0: continue
    raw.seek(off); pts = np.frombuffer(raw.read(nb), dtype=np.float32).reshape(-1, 2).astype(np.float64)
    if pts[:, 0].max() > 180: pts[:, 0] = np.where(pts[:, 0] > 180, pts[:, 0] - 360, pts[:, 0])
    if pts[:, 0].min() > LON1 or pts[:, 0].max() < LON0: continue
    px = np.clip(to_px(pts), -4 * W, 5 * W)
    poly = np.round(px * 16).astype(np.int32)
    cv2.fillPoly(land, [poly], 255 if level in (1, 3) else 0, cv2.LINE_8, shift=4)
    n_used += 1
cv2.imwrite("assets/fl_land.png", land)
# light density from Black Marble (4096 x 2048 equirectangular)
night = cv2.imread("assets/earth_night_4k.jpg").astype(np.float32) / 255
lum = (0.3 * night[..., 2] + 0.55 * night[..., 1] + 0.15 * night[..., 0])
nh, nw = lum.shape
x0 = (LON0 + 180) / 360 * nw; x1 = (LON1 + 180) / 360 * nw; y0 = (90 - LAT1) / 180 * nh; y1 = (90 - LAT0) / 180 * nh
xs = np.linspace(x0, x1, W, dtype=np.float32); ys = np.linspace(y0, y1, H, dtype=np.float32)
mx, my = np.meshgrid(xs, ys)
dens = cv2.remap(lum, mx, my, cv2.INTER_CUBIC)
dens = np.clip(dens - 0.03, 0, None) ** 1.3
landf = cv2.GaussianBlur((land > 0).astype(np.float32), (0, 0), 2.0)
dens *= landf
r = np.random.default_rng(11)
p = np.clip(dens * 2.2, 0, 0.9)                        # probability of a light in each 150 m cell
lit = r.random((H, W)).astype(np.float32) < p
inten = (r.power(0.35, (H, W)).astype(np.float32) * 0.8 + 0.2) * lit
lights = inten * (0.6 + 0.8 * np.clip(dens * 3, 0, 1))
out = np.clip(np.sqrt(np.clip(lights, 0, 4) / 4) * 255, 0, 255).astype(np.uint8)
cv2.imwrite("assets/fl_lights.png", out)
json.dump(dict(lon0=LON0, lon1=LON1, lat0=LAT0, lat1=LAT1, W=W, H=H), open("assets/fl_meta.json", "w"))
print("polygons", n_used, "size", W, H, "land", (land > 0).mean(), "lit", lit.mean())
# check
cv2.imwrite(sys.argv[2] if len(sys.argv) > 2 else "/tmp/fl_check.jpg", np.hstack([cv2.resize(land, (900, int(900 * H / W))), cv2.resize(out, (900, int(900 * H / W)), interpolation=cv2.INTER_AREA)]))
