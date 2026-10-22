"""Download the speech-recognition and vocal-separation models (~700 MB) into models/."""
import os, subprocess, tarfile, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); M = os.path.join(ROOT, "models"); os.makedirs(M, exist_ok=True)
BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
for rel, name in [("asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2", "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"),
                  ("source-separation-models/sherpa-onnx-spleeter-2stems-fp16.tar.bz2", "sherpa-onnx-spleeter-2stems-fp16")]:
    if os.path.isdir(os.path.join(M, name)): print("have", name); continue
    tgz = os.path.join(M, os.path.basename(rel)); print("downloading", name)
    urllib.request.urlretrieve(BASE + rel, tgz)
    with tarfile.open(tgz) as t: t.extractall(M)
    os.remove(tgz)
print("models ready")
