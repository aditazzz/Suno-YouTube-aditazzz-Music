// Renders the film headless (run prep.mjs first; the npm scripts do):
//   node render.mjs stills <16x9|9x16> <out_dir> name=seconds [name=seconds ...]   PNG stills of single moments
//   node render.mjs master <16x9|9x16> [--width W --height H] [--from S --to S]    the silent master,
//        ../build/master_<fmt>.mp4 (scene.py reads it and adds the studio's 2D layer: captions, pill, end card)
//   node render.mjs clip <16x9|9x16> <from_s> <to_s> <out.mp4>                      a silent excerpt
import path from 'node:path';
import os from 'node:os';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FPS = 30;
const [cmd, fmt, ...rest] = process.argv.slice(2);
if (!['stills', 'master', 'clip'].includes(cmd) || !['16x9', '9x16'].includes(fmt)) {
  console.error('usage: node render.mjs stills|master|clip 16x9|9x16 ...');
  process.exit(2);
}
const opt = (name, dflt) => {
  const i = rest.indexOf(`--${name}`);
  return i >= 0 ? rest[i + 1] : dflt;
};
const id = fmt === '16x9' ? 'Wall16x9' : 'Wall9x16';
const size = fmt === '16x9' ? [1920, 1080] : [1080, 1920];
const inputProps = {preview: false, width: Number(opt('width', size[0])), height: Number(opt('height', size[1]))};

const t0 = Date.now();
const serveUrl = await bundle({entryPoint: path.join(HERE, 'src', 'index.ts'), publicDir: path.join(HERE, 'public')});
const composition = await selectComposition({serveUrl, id, inputProps});
console.log(`bundled ${id} ${composition.width}x${composition.height}, ${composition.durationInFrames} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s`);

if (cmd === 'stills') {
  const [outDir, ...shots] = rest.filter((x, i, a) => !x.startsWith('--') && !(a[i - 1] || '').startsWith('--'));
  fs.mkdirSync(outDir, {recursive: true});
  for (const shot of shots) {
    const [name, sec] = shot.includes('=') ? shot.split('=') : [`t${shot}`, shot];
    const frame = Math.round(Number(sec) * FPS);
    const output = path.resolve(outDir, `${name}.png`);
    const s0 = Date.now();
    await renderStill({composition, serveUrl, output, frame, imageFormat: 'png', inputProps});
    console.log(`${output}  (t=${sec}s, frame ${frame}, ${((Date.now() - s0) / 1000).toFixed(1)}s)`);
  }
} else {
  const from = cmd === 'clip' ? Number(rest[0]) : Number(opt('from', 0));
  const to = cmd === 'clip' ? Number(rest[1]) : Number(opt('to', composition.durationInFrames / FPS));
  const out = cmd === 'clip' ? path.resolve(rest[2]) : path.join(HERE, '..', 'build', `master_${fmt}.mp4`);
  fs.mkdirSync(path.dirname(out), {recursive: true});
  const frameRange = [Math.round(from * FPS), Math.min(composition.durationInFrames - 1, Math.round(to * FPS) - 1)];
  let last = 0;
  await renderMedia({
    composition, serveUrl, codec: 'h264', outputLocation: out, inputProps, frameRange, muted: true,
    crf: 14, pixelFormat: 'yuv420p', imageFormat: 'jpeg', jpegQuality: 94,
    concurrency: Number(opt('concurrency', Math.max(1, os.cpus().length - 1))),
    onProgress: ({progress}) => {
      if (progress - last >= 0.02 || progress === 1) {
        last = progress;
        console.log(`${(progress * 100).toFixed(0)}%  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
      }
    },
  });
  console.log(`wrote ${out} (frames ${frameRange[0]}..${frameRange[1]})`);
}
