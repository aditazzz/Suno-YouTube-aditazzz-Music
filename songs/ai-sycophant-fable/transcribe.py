import json, sys
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8")
segs, info = m.transcribe("mono16k.wav", word_timestamps=True, language="en", vad_filter=False, beam_size=5,
  initial_prompt="AI Sycophant RLHF. R-L-H-F. Tell me which one you like best. Thumbs up, keep her. Thumbs down, kill her.")
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
    print(f"{s.start:7.2f} {s.end:7.2f} {s.text}", flush=True)
json.dump(out, open(f"trans_{sys.argv[1]}.json","w"), indent=1)
