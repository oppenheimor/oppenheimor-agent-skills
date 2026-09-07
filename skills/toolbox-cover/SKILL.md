---
name: toolbox-cover
description: Normalize Oppenheimor toolbox cover images into source-faithful 16:9 thumbnails with untouched full-image previews. Use for 工具封面、统一封面比例、方形图标转封面、截图美化、批量封面处理, or website-coordinated covers from screenshots, logos, icons, banners, and product artwork. Uses content-aware layout choices and optional image_gen backgrounds, not mandatory blue frames. Not a tool-record publisher.
---

# Toolbox covers

Thumbnail for recognition; original for inspection. Never regenerate product text, logos, or UI. Do not solve low resolution by synthesizing detail or shrinking an image inside an unnecessarily large output canvas.

## Contract

- Read `DESIGN.md` and `PRODUCT.md`. Respect the navy/cobalt site without repainting every brand navy. The website already supplies a grid: do not repeat it inside every cover.
- Export `cover.webp`: exactly 1200×675, quality 92, and `original.webp`: native-dimension, lossless, orientation-correct preview. No artificial 2400×1350 preview canvas.
- Set `cover` to the thumbnail; set `coverFull` to the original high-resolution asset, never a decorated composition. Reuse an existing lossless original when available.
- Preserve aspect ratio and source files. No upscaling. Low resolution warnings are explicit; do not claim the thumbnail is retina-sharp if the source is not.
- No folds, page curls, badges, ribbons, corner tags, extra labels, numbering, fake logos, or placeholder artwork. Keep the site's `/` for missing images.
- Never overwrite earlier candidates. Applying covers requires user approval; publishing, committing, and pushing are separate permissions.

## Inspect and classify before composing

The agent makes the semantic choice after viewing the image. `auto` is only an aspect-ratio heuristic; a square screenshot is not necessarily an icon.

| Source | Mode and treatment |
| --- | --- |
| Landscape promotional artwork | `banner`: preserve composition, fill as much of the canvas as contain permits; no mandatory inner frame. |
| UI / terminal screenshot | `screenshot`: preserve complete interface; source-matched flat margins when needed. |
| Square icon / transparent logo | `icon`: centered, maximum 540×540; trim only fully transparent outer padding automatically, never opaque content. |
| Portrait / long screenshot | `poster`: contain by default; ask about a representative crop if the result is unreadable at card size. |
| Extreme wide strip | Contain and warn; propose a user-approved crop or a better source. |
| Excess opaque whitespace | Inspect and propose specific crop bounds; do not blindly trim white UI areas. |
| Tiny / blurry source | Warn and request a better source; no generated text restoration. |
| Animated / multipage image | Select an explicit representative still first; the script rejects implicit frame loss. |

Uniformity means equal outer dimensions, intentional visual weight, and consistent edges—not identical inset rectangles. Inspect dark and light products together. The original's identity wins over palette matching.

## Background policy

Use the existing image first. The default script samples opaque corners for a matching flat matte, or picks a light/dark matte from alpha-weighted foreground brightness for transparency. These are heuristics: visually inspect multicolored edges and multicolor logos; override with a suitable provided background if necessary.

Use `image_gen` only when an added background genuinely helps and generation is requested/authorized. Read `references/background-prompt.md`. Keep exact prompts, native output, and truthful provenance. Do not regenerate brand content. If the tool is unavailable, say so; deterministic output is not AI generation. Shared backgrounds are optional, not a batch requirement.

## Run

From the repo root with its existing `sharp` dependency:

```sh
node <installed-skill-dir>/scripts/compose.mjs \
  --source path/to/original.png --output path/to/new-candidate --mode banner
```

Options: `--mode auto|banner|screenshot|icon|poster`, `--background FILE`, `--provenance LABEL`, `--crop left,top,width,height`. Crop coordinates refer to the orientation-correct original. **Only pass `--crop` after approval**; the full preview is always uncropped. Fully transparent padding removal needs no manual crop approval because it removes no visible content.

Review candidates at real desktop/mobile card sizes and inspect original preview text. Check output dimensions, logo integrity, source hash, crop record, contrast, warnings, and batch visual weight. Return a contact sheet and distinguish deterministic processing from actual image generation.

Resolve `<installed-skill-dir>` to the directory containing this SKILL.md, not the current working directory. Run `node --test <installed-skill-dir>/scripts/compose.test.mjs` from the target project root. Tests cover banner occupancy independent of master resolution, square icons, panoramas, portraits, tiny images, transparent padding, full-preview fidelity, approved crops, and overwrite rejection. Site lightbox must retain its DPR-aware no-upscale behavior.

## Optional image_gen delegation

When explicitly asked to use Herdr/Codex, follow the installed Herdr skill. Check `HERDR_ENV=1`, discover CLI syntax and the `codexy` alias, preserve cwd and user focus. Limit the worker to candidate assets and truthful provenance. Do not permit website edits or publication by the image worker. Report missing image tools rather than faking generation.
