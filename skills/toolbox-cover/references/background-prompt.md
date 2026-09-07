# Shared background plate

Use the native image_gen tool. Do not simulate generation with SVG/CSS and do not redraw source screenshots.

Prompt:

> Create a reusable 16:9 background plate for a personal developer's toolbox website. A quiet flat midnight-navy field, approximately #080f20 to #111d32, with a very faint engineering-grid suggestion near the perimeter only. The central 90% width / 80% height is visually quiet and nearly uniform: it will receive a real product screenshot later. All four corners must remain plain background: no corner accent, folded corner, page curl, ribbon, badge, sticker, triangular tag, or decorative marker. Flat vector-like graphic design, restrained, clear, no 3D, bevel, tray rim, drop shadow, light beam, neon glow, gradient spotlight, lettering, labels, logo, icon, UI, screenshot, texture noise, watermark, or busy polygon scatter. Keep the background subordinate. Wide composition, high resolution. All covers in the batch will reuse this exact plate.

If the image tool returns a different aspect ratio, cover-crop only this expendable background when composing. Never crop the source product image by this rule.

Save native generated files and a `generation.json` with provider/tool name, exact prompt, output path and any tool-reported dimensions. Do not invent tool IDs, seeds, or model metadata.
