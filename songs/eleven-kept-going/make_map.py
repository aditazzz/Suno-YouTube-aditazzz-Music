"""Build the Cape Canaveral night-map assets from GSHHS full-resolution coastlines (basemap-data-hires, LGPL/GPL data).
usage: python3 make_map.py /path/to/basemap_data   -> assets/cape_land.png (land mask) + assets/cape_meta.json
"""
import sys, os, json, numpy as np, cv2
D = sys.argv[1]
LON0, LON1, LAT0, LAT1 = -81.55, -79.85, 27.85, 29.15
W = 8192
kx = np.cos(np.radians((LAT0 + LAT1) / 2))
H = int(round(W * (LAT1 - LAT0) / ((LON1 - LON0) * kx)))
meta = [l.split() for l in open(os.path.join(D, "gshhsmeta_f.dat"))]
raw = open(os.path.join(D, "gshhs_f.dat"), "rb")
land = np.zeros((H, W), np.uint8); water_in = np.zeros((H, W), np.uint8)
def to_px(lonlat):
    x = (lonlat[:, 0] - LON0) / (LON1 - LON0) * W
    y = (LAT1 - lonlat[:, 1]) / (LAT1 - LAT0) * H
    return np.stack([x, y], 1)
n_used = 0
for m in meta:
    level = int(m[0]); npts = int(m[2]); south = float(m[3]); north = float(m[4]); off = int(m[5]); nb = int(m[6])
    if south > LAT1 or north < LAT0: continue
    raw.seek(off); pts = np.frombuffer(raw.read(nb), dtype=np.float32).reshape(-1, 2).astype(np.float64)
    if pts[:, 0].max() > 180: pts[:, 0] = np.where(pts[:, 0] > 180, pts[:, 0] - 360, pts[:, 0])
    if pts[:, 0].min() > LON1 or pts[:, 0].max() < LON0: continue
    px = to_px(pts)
    # clip absurd coordinates (far-away parts of continent polygons) to a generous frame so int32 is safe
    px = np.clip(px, -4 * W, 5 * W)
    poly = np.round(px * 16).astype(np.int32)
    if level in (1, 3): cv2.fillPoly(land, [poly], 255, cv2.LINE_8, shift=4)
    else: cv2.fillPoly(land, [poly], 0, cv2.LINE_8, shift=4)
    n_used += 1
cv2.imwrite("assets/cape_land.png", land)
json.dump(dict(lon0=LON0, lon1=LON1, lat0=LAT0, lat1=LAT1, W=W, H=H), open("assets/cape_meta.json", "w"))
print("polygons", n_used, "size", W, H, "land frac", (land > 0).mean())

# ---------------------------------------------------------------- night lights (procedural, placed on the real coastline)
M = json.load(open("assets/cape_meta.json")); LON0, LON1, LAT0, LAT1, W, H = M["lon0"], M["lon1"], M["lat0"], M["lat1"], M["W"], M["H"]
land = cv2.imread("assets/cape_land.png", 0) > 127
r = np.random.default_rng(42)
lights = np.zeros((H, W), np.float32)
kmx = (LON1 - LON0) * 111.32 * np.cos(np.radians((LAT0 + LAT1) / 2)) / W     # km per px (x)
kmy = (LAT1 - LAT0) * 110.57 / H
def px(lon, lat): return (lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H
def cluster(lon, lat, rx_km, ry_km, n, b=1.0, warm=0.0):
    cx, cy = px(lon, lat)
    xs = cx + r.normal(0, rx_km / kmx, n); ys = cy + r.normal(0, ry_km / kmy, n)
    xi = np.clip(xs.astype(int), 0, W - 1); yi = np.clip(ys.astype(int), 0, H - 1)
    ok = land[yi, xi]
    np.add.at(lights, (yi[ok], xi[ok]), (r.power(0.4, ok.sum()) * b).astype(np.float32))
def road(pts, spacing_km=0.12, b=0.6, jitter=0.0):
    for (lo0, la0), (lo1, la1) in zip(pts[:-1], pts[1:]):
        x0, y0 = px(lo0, la0); x1, y1 = px(lo1, la1)
        L = np.hypot((x1 - x0) * kmx, (y1 - y0) * kmy); n = max(2, int(L / spacing_km))
        for k in range(n):
            u = k / n; x = int(x0 + (x1 - x0) * u + r.normal(0, jitter)); y = int(y0 + (y1 - y0) * u + r.normal(0, jitter))
            if 0 <= x < W and 0 <= y < H: lights[y, x] += b * r.uniform(0.6, 1.0)
towns = [(-80.607, 28.320, 1.0, 3.6, 9000, 1.0), (-80.605, 28.392, 0.9, 1.4, 3500, 1.0), (-80.625, 28.410, 1.0, 0.6, 2500, 1.6),
         (-80.700, 28.360, 2.6, 3.0, 9000, 0.9), (-80.742, 28.386, 1.4, 1.8, 6000, 1.0), (-80.727, 28.316, 1.5, 2.0, 6000, 0.9),
         (-80.808, 28.600, 2.2, 5.0, 12000, 0.9), (-80.630, 28.090, 4.0, 4.5, 16000, 1.0), (-80.590, 28.180, 1.0, 4.0, 7000, 0.9),
         (-80.735, 28.240, 3.0, 2.6, 7000, 0.8), (-80.790, 28.480, 1.6, 1.8, 4000, 0.7), (-81.380, 28.540, 9.0, 9.0, 70000, 1.1),
         (-81.200, 28.660, 3.5, 3.0, 12000, 0.9), (-81.270, 28.800, 3.0, 3.0, 9000, 0.9), (-81.220, 28.900, 4.0, 4.0, 12000, 0.8),
         (-80.930, 29.030, 1.6, 2.4, 6000, 0.9), (-80.900, 28.985, 1.4, 1.8, 3500, 0.8), (-81.030, 29.140, 3.0, 2.0, 9000, 1.0),
         (-80.650, 28.522, 1.2, 1.0, 1200, 0.5), (-80.651, 28.586, 0.4, 0.4, 400, 1.0), (-81.10, 28.40, 4.0, 4.0, 5000, 0.6),
         (-80.95, 28.32, 3.0, 3.0, 3000, 0.5), (-81.30, 28.20, 5.0, 5.0, 9000, 0.7)]
for lo, la, rx, ry, n, b in towns: cluster(lo, la, rx, ry, n, b)
road([(-80.62, 27.86), (-80.70, 28.20), (-80.78, 28.45), (-80.84, 28.62), (-80.95, 28.90), (-81.05, 29.14)], 0.25, 0.35, 1.0)   # I-95
road([(-80.58, 27.86), (-80.66, 28.15), (-80.72, 28.30), (-80.76, 28.42), (-80.80, 28.55), (-80.83, 28.65), (-80.90, 28.95)], 0.12, 0.6, 0.6)  # US-1
road([(-81.30, 28.45), (-81.00, 28.42), (-80.80, 28.40), (-80.64, 28.405)], 0.2, 0.45, 0.6)                                       # 528
road([(-80.76, 28.36), (-80.68, 28.36), (-80.61, 28.36)], 0.10, 0.6, 0.5)                                                       # 520
road([(-80.57, 27.86), (-80.60, 28.10), (-80.61, 28.32), (-80.606, 28.405)], 0.08, 0.7, 0.4)                                    # A1A
road([(-80.62, 28.42), (-80.60, 28.47), (-80.575, 28.53), (-80.58, 28.60)], 0.6, 0.25, 0.3)                                     # the Cape's road (dim)
# launch complexes and the landing zone: bright work lights
for lo, la, b, n in [(-80.5772, 28.5618, 9.0, 60), (-80.6041, 28.6082, 5.0, 50), (-80.5442, 28.4858, 7.0, 40), (-80.5680, 28.5310, 1.5, 15),
                     (-80.5830, 28.5830, 2.5, 25)]:
    cx, cy = px(lo, la)
    for k in range(n):
        x = int(cx + r.normal(0, 0.12 / kmx)); y = int(cy + r.normal(0, 0.12 / kmy))
        if 0 <= x < W and 0 <= y < H: lights[y, x] += b / n * 6
lights = cv2.GaussianBlur(lights, (0, 0), 0.8) * 3.0
out = np.clip(np.sqrt(np.clip(lights, 0, 4) / 4) * 255, 0, 255).astype(np.uint8)
cv2.imwrite("assets/cape_lights.png", out)
print("lights written", out.mean(), (out > 0).mean())
