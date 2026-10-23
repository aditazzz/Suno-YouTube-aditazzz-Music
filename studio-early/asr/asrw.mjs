import { pipeline, env } from '@huggingface/transformers';
import fs from 'fs';
env.allowRemoteModels = false;
env.localModelPath = './node_modules/sts-whisper-small/models/';
const wav = fs.readFileSync(process.argv[2]);
// raw float32 mono 16k
const audio = new Float32Array(wav.buffer, wav.byteOffset, wav.byteLength/4);
const asr = await pipeline('automatic-speech-recognition', 'Xenova/whisper-small', { dtype: 'q8' });
const out = await asr(audio, { language: 'english', task: 'transcribe', return_timestamps: "word", chunk_length_s: 30, stride_length_s: 5 });
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
for (const c of out.chunks) console.log(c.timestamp[0]?.toFixed(2), c.timestamp[1]?.toFixed(2), c.text);
