# PPTX revision notes
- Build: `cd pptx && npm i && node make_pptx.mjs` -> ../presentation.pptx. Check: `./export_check.sh` (PowerPoint export -> ../presentation.pdf).
- Equations: LaTeX sources in `equations.mjs` (also dumped to `equations.tex`). MathJax (local, no network) -> vector SVG, embedded as PowerPoint `svgBlip` with PNG fallback; LaTeX kept in each picture's alt text. Not OMML.
- Slide 9: tau/W/y symbols as LaTeX; lane labels/timeline shifted so E3 text no longer touches lag_168.
- Slide 10: table widened (no wrap), legend and cards spaced, Ridge objective in its own full-width strip.
- Slide 11: Gain, Gap, ablation as separate display equations; claim moved below.
- Slide 12: MAE/RMSE side by side; boxes/timeline/cards re-spaced.
- Slides 1, 5, 6: cover band text clipped at right edge, table/caption and table/text collisions fixed. Slide 3, 13: removed Unicode math wording.
