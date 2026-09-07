#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const sharp = createRequire(path.join(process.cwd(), 'package.json'))('sharp');
export const SIZE = { width: 1200, height: 675 };
const digest = bytes => createHash('sha256').update(bytes).digest('hex');

export function placement(width, height, mode = 'auto') {
  if (!(width > 0 && height > 0)) throw new Error('Invalid source dimensions');
  if (!['auto', 'banner', 'screenshot', 'icon', 'poster'].includes(mode)) throw new Error('Unknown mode');
  const ratio = width / height;
  const resolvedMode = mode === 'auto' ? (ratio >= 1.65 && ratio <= 1.9 ? 'banner' : ratio >= .8 && ratio <= 1.2 ? 'icon' : ratio < .8 ? 'poster' : 'screenshot') : mode;
  const box = resolvedMode === 'icon' ? [540, 540] : resolvedMode === 'poster' ? [1080, 595] : [1200, 675];
  // Composition is defined at thumbnail resolution, not an artificial 2400px master.
  const scale = Math.min(1, box[0] / width, box[1] / height);
  const w = Math.max(1, Math.round(width * scale)), h = Math.max(1, Math.round(height * scale));
  return { mode: resolvedMode, width: w, height: h, left: Math.round((SIZE.width - w) / 2), top: Math.round((SIZE.height - h) / 2), scale };
}

async function transparentBounds(bytes) {
  const { data, info } = await sharp(bytes).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  let left = info.width, top = info.height, right = -1, bottom = -1;
  for (let y = 0; y < info.height; y++) for (let x = 0; x < info.width; x++) {
    if (data[(y * info.width + x) * 4 + 3] !== 0) {
      left = Math.min(left, x); right = Math.max(right, x); top = Math.min(top, y); bottom = Math.max(bottom, y);
    }
  }
  if (right < 0) throw new Error('Source image is fully transparent');
  return { left, top, width: right - left + 1, height: bottom - top + 1 };
}

async function matte(bytes, forceContrast = false) {
  const { data, info } = await sharp(bytes).resize(64, 64, { fit: 'inside' }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const corners = [0, info.width - 1, (info.height - 1) * info.width, info.height * info.width - 1];
  if (!forceContrast && corners.every(i => data[i * 4 + 3] === 255)) {
    const rgb = [0, 1, 2].map(channel => Math.round(corners.reduce((sum, i) => sum + data[i * 4 + channel], 0) / 4));
    return { color: { r: rgb[0], g: rgb[1], b: rgb[2] }, method: 'opaque-corner-average' };
  }
  let light = 0, weight = 0;
  for (let i = 0; i < data.length; i += 4) {
    const alpha = data[i + 3] / 255;
    light += (.2126 * data[i] + .7152 * data[i + 1] + .0722 * data[i + 2]) * alpha;
    weight += alpha;
  }
  return { color: weight && light / weight < 128 ? '#e6edf5' : '#0c1628', method: 'alpha-weighted-contrast' };
}

export async function compose({ source, output, background, mode = 'auto', provenance = 'user-provided', crop }) {
  if (!source || !output) throw new Error('--source and --output are required');
  const sourcePath = path.resolve(source), out = path.resolve(output);
  const sourceBytes = await fs.readFile(sourcePath);
  const sourceMeta = await sharp(sourceBytes).metadata();
  if ((sourceMeta.pages ?? 1) > 1) throw new Error('Animated/multipage source: choose a representative still explicitly');
  const original = await sharp(sourceBytes, { limitInputPixels: 40000000 }).rotate().webp({ lossless: true }).toBuffer();
  const metadata = await sharp(original).metadata();
  let content = original, cropRecord = null;
  if (crop) {
    const values = String(crop).split(',').map(Number);
    if (values.length !== 4 || values.some(v => !Number.isInteger(v) || v < 0)) throw new Error('--crop must be left,top,width,height');
    const [left, top, width, height] = values;
    if (!width || !height || left + width > metadata.width || top + height > metadata.height) throw new Error('Crop exceeds source bounds');
    cropRecord = { left, top, width, height, reason: 'explicit-approved-crop' };
    content = await sharp(content).extract({ left, top, width, height }).png().toBuffer();
  } else if (metadata.hasAlpha && ['icon', 'auto'].includes(mode)) {
    const bounds = await transparentBounds(content);
    if (bounds.width !== metadata.width || bounds.height !== metadata.height) {
      cropRecord = { ...bounds, reason: 'fully-transparent-padding-only' };
      content = await sharp(content).extract(bounds).png().toBuffer();
    }
  }
  const contentMeta = await sharp(content).metadata();
  const fit = placement(contentMeta.width, contentMeta.height, mode);
  const sourceLayer = await sharp(content).resize(fit.width, fit.height).png().toBuffer();
  const matchingMatte = await matte(content, fit.mode === 'icon' && metadata.hasAlpha);
  let canvas, backgroundRecord;
  if (background) {
    const bytes = await fs.readFile(background);
    canvas = await sharp(bytes).resize(SIZE.width, SIZE.height, { fit: 'cover' }).flatten({ background: '#080f20' }).png().toBuffer();
    backgroundRecord = { path: path.resolve(background), sha256: digest(bytes), provenance };
  } else {
    canvas = await sharp({ create: { ...SIZE, channels: 3, background: matchingMatte.color } }).png().toBuffer();
    backgroundRecord = { provenance: 'deterministic-source-adaptive', ...matchingMatte };
  }
  await fs.mkdir(out, { recursive: true });
  for (const name of ['original.webp', 'cover.webp', 'manifest.json']) {
    try { await fs.access(path.join(out, name)); throw new Error(`Refusing to overwrite ${path.join(out, name)}`); }
    catch (e) { if (e.code !== 'ENOENT') throw e; }
  }
  const thumbnail = await sharp(canvas).composite([{ input: sourceLayer, left: fit.left, top: fit.top }]).webp({ quality: 92 }).toBuffer();
  const warnings = [];
  if (fit.scale === 1 && fit.width < (fit.mode === 'icon' ? 540 : 1200)) warnings.push('Source is below the preferred thumbnail size; no upscaling or detail synthesis was applied.');
  if (contentMeta.width / contentMeta.height > 3.2 || contentMeta.width / contentMeta.height < .6) warnings.push('Extreme aspect ratio: review at card size and ask whether to select a representative crop. Original preview remains intact.');
  const manifest = {
    source: { path: sourcePath, sha256: digest(sourceBytes), width: metadata.width, height: metadata.height },
    crop: cropRecord, background: backgroundRecord, placement: fit,
    preview: { file: 'original.webp', width: metadata.width, height: metadata.height, lossless: true, bytes: original.length },
    thumbnail: { file: 'cover.webp', ...SIZE, quality: 92, bytes: thumbnail.length }, warnings,
  };
  await fs.writeFile(path.join(out, 'original.webp'), original, { flag: 'wx' });
  await fs.writeFile(path.join(out, 'cover.webp'), thumbnail, { flag: 'wx' });
  await fs.writeFile(path.join(out, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx' });
  return manifest;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const args = process.argv.slice(2);
  if (args.includes('--help')) {
    console.log('Run from repo root (sharp required):\nnode <skill>/scripts/compose.mjs --source FILE --output NEW_DIR [--mode auto|banner|screenshot|icon|poster] [--crop left,top,width,height] [--background FILE] [--provenance image_gen|user-provided]\nOutput: 1200x675 cover.webp + original.webp (native-size lossless preview) + manifest.json. Crop applies only to the thumbnail and requires user approval. Existing files are never overwritten.');
  } else {
    try {
      const options = {};
      for (let i = 0; i < args.length; i += 2) {
        if (!['--source', '--output', '--background', '--mode', '--provenance', '--crop'].includes(args[i]) || !args[i + 1]) throw new Error('Unknown or incomplete option; use --help');
        options[args[i].slice(2)] = args[i + 1];
      }
      console.log(JSON.stringify(await compose(options), null, 2));
    } catch (e) { console.error(e.message); process.exitCode = 1; }
  }
}
