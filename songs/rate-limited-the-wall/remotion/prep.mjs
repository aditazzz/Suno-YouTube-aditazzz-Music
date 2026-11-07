// Writes everything the film reads at bundle time into public/ (all of it is generated and gitignored):
//   public/data/song.json  lines, word times, beats, downbeats, sections  (from ../build/*.json)
//   public/data/spec.json  48-band spectrum, 30 fps, quantised to bytes  (../build/spec.npy, else the
//                          original cut's songs/rate-limited/build/spec.npy, else computed from the audio)
//   public/fonts/*         the engine's fonts (assets/fonts, see assets/fonts/README.md)
//   public/audio.wav       a link to the song, only for previewing with sound in Remotion Studio
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SONG = path.resolve(HERE, '..');
const REPO = path.resolve(SONG, '..', '..');
const PUB = path.join(HERE, 'public');
fs.mkdirSync(path.join(PUB, 'data'), {recursive: true});
fs.mkdirSync(path.join(PUB, 'fonts'), {recursive: true});

const readJson = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));
const timed = readJson(path.join(SONG, 'build', 'timed.json'));
const beats = readJson(path.join(SONG, 'build', 'beats.json'));
const sections = readJson(path.join(SONG, 'build', 'sections.json'));
const song = {
  duration: beats.duration,
  tempo: beats.tempo,
  beats: beats.beats,
  downbeats: beats.downbeats,
  sections: sections.map(({name, s, e}) => ({name, s, e})),
  lines: timed.map(({sec, text, words, wt, s, e}) => ({sec, text, words, wt, s, e})),
};
fs.writeFileSync(path.join(PUB, 'data', 'song.json'), JSON.stringify(song));

function readNpy(file) {
  const buf = fs.readFileSync(file);
  const headerLen = buf.readUInt16LE(8);
  const header = buf.subarray(10, 10 + headerLen).toString('latin1');
  if (!header.includes("'descr': '<f4'")) throw new Error(`${file}: expected float32, got ${header}`);
  const shape = header.match(/'shape': \((\d+), (\d+)\)/).slice(1).map(Number);
  const start = 10 + headerLen;
  const data = new Float32Array(buf.buffer.slice(buf.byteOffset + start, buf.byteOffset + start + shape[0] * shape[1] * 4));
  return {frames: shape[0], bands: shape[1], data};
}

const specCandidates = [path.join(SONG, 'build', 'spec.npy'), path.join(REPO, 'songs', 'rate-limited', 'build', 'spec.npy')];
let specFile = specCandidates.find((p) => fs.existsSync(p));
if (!specFile) {
  execFileSync('python3', [path.join(SONG, 'scene.py'), 'spec'], {cwd: REPO, stdio: 'inherit'});
  specFile = specCandidates[0];
}
const spec = readNpy(specFile);
const bytes = Buffer.alloc(spec.frames * spec.bands);
for (let i = 0; i < bytes.length; i++) bytes[i] = Math.max(0, Math.min(255, Math.round(spec.data[i] * 255)));
fs.writeFileSync(path.join(PUB, 'data', 'spec.json'),
  JSON.stringify({fps: 30, frames: spec.frames, bands: spec.bands, b64: bytes.toString('base64')}));

const FONTS = ['InterDisplay-Black.otf', 'InterDisplay-Bold.otf', 'Inter-SemiBold.otf', 'JBMono-400.ttf', 'JBMono-700.ttf'];
for (const f of FONTS) {
  const src = path.join(REPO, 'assets', 'fonts', f);
  if (!fs.existsSync(src)) throw new Error(`missing font ${src} (see assets/fonts/README.md)`);
  fs.copyFileSync(src, path.join(PUB, 'fonts', f));
}

let audio = '';
try {
  audio = execFileSync('python3', ['-c', 'import sys; from studio import config; print(config.load_song(sys.argv[1])["audio"])', SONG],
    {cwd: REPO, encoding: 'utf8'}).trim();
} catch {}
if (audio && !fs.existsSync(audio)) audio = '';
const link = path.join(PUB, 'audio.wav');
fs.rmSync(link, {force: true});
if (audio) fs.symlinkSync(audio, link);

console.log(`prep: ${song.lines.length} lines, ${song.beats.length} beats, spectrum ${spec.frames}x${spec.bands} from ` +
  `${path.relative(REPO, specFile)}, audio ${audio ? 'linked' : 'not found (silent preview)'}`);
