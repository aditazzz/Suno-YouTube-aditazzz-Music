"""The grade, as its own step (CD 13.4): scene-linear EXR (Rec.709 linear, from the renders) -> exposure -> Filmic view
with a softer look -> a lifted toe -> a tight halation from real highlights only -> 16-bit display PNG (then
finish_still.py / post_encode.py add the grain and encode, as before). Also writes the object-index masks for measuring.

Runs with Blender's bundled Python (numpy, OpenImageIO, PyOpenColorIO):
  BPY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
  $BPY grade.py <in.exr | dir> <out dir> [--shot S1|S2|S3 | --exposure EV] [--look "Medium Contrast"] [--toe 0.10]

The defaults live in GRADE below, so a later exposure note is a one-line change and a re-grade, never a re-render."""
import os, sys, re, glob, json, argparse
import numpy as np
import OpenImageIO as oiio
import PyOpenColorIO as OCIO

HERE = os.path.dirname(os.path.abspath(__file__))
GRADE_FILE = os.path.join(HERE, "..", "data", "grade.json")
GRADE = {   # per shot: exposure (EV), Filmic look, toe lift, halation strength
    "S1": {"ev": 0.35, "look": "Medium Contrast", "toe": 0.10, "hal": 0.05},
    "S2": {"ev": 0.30, "look": "Medium Contrast", "toe": 0.12, "hal": 0.05},
    "S3": {"ev": 0.00, "look": "Medium Contrast", "toe": 0.12, "hal": 0.05},
}
if os.path.exists(GRADE_FILE):
    for k, v in json.load(open(GRADE_FILE)).items():
        if k == "ranges":
            GRADE["ranges"] = v
        else:
            GRADE.setdefault(k, {}).update(v)


def shot_of(f):
    return "S1" if f <= 572 else ("S2" if f <= 768 else "S3")


def read_exr(p):
    inp = oiio.ImageInput.open(p)
    spec = inp.spec()
    names = list(spec.channelnames)
    px = inp.read_image(0, 0, 0, len(names), oiio.FLOAT)
    inp.close()
    px = np.asarray(px).reshape(spec.height, spec.width, len(names))

    def ch(suffixes):
        for s in suffixes:
            for i, n in enumerate(names):
                if n.endswith(s):
                    return px[..., i]
        return None
    # prefer the composited result if the file has one, else the render layer's Combined
    rgb = None
    for pre in ("Composite.Combined.", "Composite.", ""):
        idx = [next((i for i, n in enumerate(names) if n == pre + "Combined." + c or n == pre + c or n.endswith("Combined." + c)), None) for c in "RGB"] if pre == "" else \
              [next((i for i, n in enumerate(names) if n.startswith(pre) and n.endswith("." + c) or n == pre + c), None) for c in "RGB"]
        if all(i is not None for i in idx):
            rgb = np.stack([px[..., i] for i in idx], -1)
            break
    io_ = ch(["IndexOB.X", "IndexOB.V", "IndexOB"])
    return rgb.astype(np.float32), (None if io_ is None else io_.astype(np.float32)), names


_cfg = OCIO.Config.CreateFromFile(os.environ.get("OCIO") or "/Applications/Blender.app/Contents/Resources/5.2/datafiles/colormanagement/config.ocio")


def blur(a, frac):
    """A cheap wide gaussian: down-res with a good filter, back up (OIIO only; no cv2 in Blender's Python)."""
    h, w, c = a.shape
    sw, sh = max(4, int(w * frac)), max(4, int(h * frac))
    buf = oiio.ImageBuf(np.ascontiguousarray(a))
    small = oiio.ImageBufAlgo.resize(buf, roi=oiio.ROI(0, sw, 0, sh, 0, 1, 0, c), filtername="gaussian")
    big = oiio.ImageBufAlgo.resize(small, roi=oiio.ROI(0, w, 0, h, 0, 1, 0, c), filtername="gaussian")
    return np.asarray(big.get_pixels(oiio.FLOAT)).reshape(h, w, c)


def write_png(path, arr, bits):
    arr = np.ascontiguousarray(arr)
    ch = 1 if arr.ndim == 2 else arr.shape[2]
    out = oiio.ImageOutput.create(path)
    out.open(path, oiio.ImageSpec(arr.shape[1], arr.shape[0], ch, oiio.UINT16 if bits == 16 else oiio.UINT8))
    out.write_image(arr)
    out.close()


_procs = {}


def display(lin, look):
    """Blender's own path: the config's Filmic view on the sRGB display, with the look applied as Blender applies it."""
    if look not in _procs:
        lv = OCIO.LegacyViewingPipeline()
        lv.setDisplayViewTransform(OCIO.DisplayViewTransform(src="Linear Rec.709", display="sRGB", view="Filmic"))
        if look and look != "None":
            lv.setLooksOverrideEnabled(True)
            lv.setLooksOverride(look)
        _procs[look] = lv.getProcessor(_cfg, _cfg.getCurrentContext()).getDefaultCPUProcessor()
    img = np.ascontiguousarray(lin.astype(np.float32))
    _procs[look].applyRGB(img)
    return img


def toe(x, t):
    """Lift the toe without lifting black: a smooth boost of the low end that fades out by the midtones."""
    if t <= 0:
        return x
    return np.clip(x + t * x * np.exp(-x / 0.12) * 2.2, 0, 1)


def halation(lin, s):
    if s <= 0:
        return lin
    hi = np.clip(lin - 1.0, 0, 8)
    h, w = hi.shape[:2]
    k = max(3, int(w * 0.006)) | 1
    b = blur(hi, 1 / 60) * 0.6 + blur(hi, 1 / 200) * 0.4
    b[..., 1] *= 0.55; b[..., 2] *= 0.35            # halation is warm (red layer of the film)
    return lin + s * b


def grade_one(src, dst_dir, f=None, ev=None, look=None, t=None, hal=None, shot=None):
    rgb, idx, names = read_exr(src)
    if f is None:
        m = re.search(r"f(\d{4})", os.path.basename(src)); f = int(m.group(1)) if m else 0
    g = dict(GRADE[shot or shot_of(f)])
    fmt = "9x16" if rgb.shape[0] > rgb.shape[1] else "16x9"
    for rg in GRADE.get("ranges", []):    # per-shot overrides inside a set, e.g. the OTS on the CRT; optional 4th: format
        a_, b_, over = rg[:3]
        if a_ <= f <= b_ and (len(rg) < 4 or rg[3] == fmt):
            over = dict(over)
            if "ease" in over:    # LOCK 12 A6: a ramp {"ev_from": x (default: the shot's base), "ev_to": y, "ease": [a, b]}, smoothstep over a..b
                ea, eb = over.pop("ease"); u = min(1.0, max(0.0, (f - ea) / float(eb - ea))); u = u * u * (3 - 2 * u)
                e0 = over.pop("ev_from", GRADE[shot or shot_of(f)]["ev"]); e1 = over.pop("ev_to")
                over["ev"] = e0 + (e1 - e0) * u
            g.update(over)
    ev = g["ev"] if ev is None else ev
    look = g["look"] if look is None else look
    t = g["toe"] if t is None else t
    hal = g["hal"] if hal is None else hal
    lin = np.maximum(rgb, 0) * (2.0 ** ev)
    lin = halation(lin, hal)
    d = toe(display(lin, look), t)
    os.makedirs(dst_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    out = os.path.join(dst_dir, base + ".png")
    write_png(out, (np.clip(d, 0, 1) * 65535 + 0.5).astype(np.uint16), 16)
    if idx is not None:
        write_png(os.path.join(dst_dir, base + "_idx.png"), np.clip(idx, 0, 255).astype(np.uint8), 8)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--shot"); ap.add_argument("--exposure", type=float); ap.add_argument("--look")
    ap.add_argument("--toe", type=float); ap.add_argument("--hal", type=float); ap.add_argument("--names", action="store_true")
    a = ap.parse_args()
    srcs = sorted(glob.glob(os.path.join(a.src, "*.exr"))) if os.path.isdir(a.src) else [a.src]
    if a.names:
        print(read_exr(srcs[0])[2]); sys.exit()
    for s in srcs:
        print(grade_one(s, a.dst, ev=a.exposure, look=a.look, t=a.toe, hal=a.hal, shot=a.shot))
