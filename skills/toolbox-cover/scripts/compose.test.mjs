import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { compose, placement } from './compose.mjs';
const sharp = createRequire(path.join(process.cwd(), 'package.json'))('sharp');
async function fixture(t, width, height, background = '#e4eaf2') {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'toolbox-cover-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const source = path.join(root, 'source.png');
  await sharp({ create: { width, height, channels: 4, background } }).png().toFile(source);
  return { source, output: path.join(root, 'output') };
}

test('1440 and 2880px banners both fill thumbnail: no master-size occupancy regression', () => {
  for (const [w, h] of [[1440, 810], [2880, 1620]]) {
    const p = placement(w, h, 'banner');
    assert.deepEqual([p.width, p.height, p.left, p.top], [1200, 675, 0, 0]);
  }
});
test('wide, square, tall and tiny inputs stay in bounds without upscaling', () => {
  for (const [w, h] of [[2742, 1182], [800, 800], [400, 5000], [5000, 200], [24, 24]]) {
    const p = placement(w, h);
    assert.ok(p.scale <= 1);
    assert.ok(p.left >= 0 && p.top >= 0 && p.left + p.width <= 1200 && p.top + p.height <= 675);
  }
  assert.equal(placement(800, 800).width, 540);
  assert.equal(placement(400, 5000).mode, 'poster');
});
test('exact thumbnail size, native lossless preview, unchanged source, overwrite rejection', async t => {
  const options = await fixture(t, 1440, 810);
  const before = await fs.readFile(options.source);
  const m = await compose({ ...options, mode: 'banner' });
  const thumb = await sharp(path.join(options.output, 'cover.webp')).metadata();
  assert.deepEqual([thumb.width, thumb.height], [1200, 675]);
  assert.deepEqual([m.preview.width, m.preview.height], [1440, 810]);
  assert.deepEqual(await sharp(before).ensureAlpha().raw().toBuffer(), await sharp(path.join(options.output, 'original.webp')).ensureAlpha().raw().toBuffer());
  assert.deepEqual(await fs.readFile(options.source), before);
  await assert.rejects(compose(options), /Refusing to overwrite/);
});
test('transparent icon padding removed only from thumbnail; black icon gets light matte', async t => {
  const options = await fixture(t, 1000, 1000, { r: 0, g: 0, b: 0, alpha: 0 });
  const icon = await sharp({ create: { width: 400, height: 400, channels: 4, background: '#101010' } }).png().toBuffer();
  const bytes = await sharp(options.source).composite([{ input: icon, left: 300, top: 300 }]).png().toBuffer();
  await fs.writeFile(options.source, bytes);
  const m = await compose({ ...options, mode: 'icon' });
  assert.equal(m.crop.reason, 'fully-transparent-padding-only');
  assert.deepEqual([m.crop.left, m.crop.top, m.crop.width, m.crop.height], [300, 300, 400, 400]);
  assert.deepEqual([m.preview.width, m.preview.height], [1000, 1000]);
  assert.equal(m.placement.width, 400);
  // Preserve contrast even when transparent-padding removal reveals opaque edges.
  assert.equal(m.background.color, '#e6edf5');
});
test('approved crop never crops original preview; extreme input emits warning', async t => {
  const options = await fixture(t, 400, 2000);
  const m = await compose({ ...options, mode: 'poster', crop: '0,200,400,400' });
  assert.deepEqual([m.preview.width, m.preview.height], [400, 2000]);
  assert.equal(m.crop.reason, 'explicit-approved-crop');
  const other = await compose({ ...options, output: options.output + '-uncropped', mode: 'poster' });
  assert.ok(other.warnings.some(w => w.includes('Extreme aspect ratio')));
});
