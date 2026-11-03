import sherpa_onnx, wave, numpy as np, json
d="models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx",
    tokens=f"{d}/tokens.txt", num_threads=2, model_type="nemo_transducer", debug=False)
with wave.open("song16k.wav") as f:
    sr=f.getframerate(); n=f.getnframes(); data=np.frombuffer(f.readframes(n),dtype=np.int16).astype(np.float32)/32768
# chunk into ~30s windows with 2s overlap handled simply by chunking at fixed boundaries
out=[]
step=30.0
t=0.0
while t < len(data)/sr:
    seg=data[int(t*sr):int(min(t+step,len(data)/sr)*sr)]
    s=rec.create_stream(); s.accept_waveform(sr, seg); rec.decode_stream(s)
    r=s.result
    toks=r.tokens; ts=r.timestamps
    for tok,tt in zip(toks,ts):
        out.append((tok, round(tt+t,2)))
    t+=step
# merge sentencepiece tokens into words
words=[]
for tok,tt in out:
    if tok.startswith(" ") or tok.startswith("▁") or not words:
        words.append({"w":tok.replace("▁","").strip(),"s":tt})
    else:
        words[-1]["w"]+=tok
for i,w in enumerate(words):
    w["e"]=words[i+1]["s"] if i+1<len(words) else w["s"]+0.4
json.dump(words,open("words.json","w"))
for w in words: print(f'{w["s"]:6.2f} {w["w"]}')
