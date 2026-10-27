// Writes the same LaTeX->SVG equations used in the PPTX to ../eq/*.svg for the Quarto deck.
import { mkdirSync, writeFileSync } from 'node:fs';
import { EQ } from './equations.mjs';
import { texToSvg } from './math.mjs';
mkdirSync('../eq', { recursive: true });
const colors = { default:'1F2328', white:'FFFFFF', warn:'DC2626', muted:'6B7280', head:'111827' };
const want = { t168:'head', t24:'head', t1:'head', wPrev:'white', wTarget:'warn', yTarget:'muted', ridge:'default', gain:'default', gap:'default', ablate:'default', mae:'default', rmse:'default' };
const meta = {};
for (const [k,c] of Object.entries(want)) { const r = texToSvg(EQ[k], colors[c]); writeFileSync(`../eq/${k}.svg`, r.svg); meta[k] = { wEm:+r.wEm.toFixed(3), hEm:+r.hEm.toFixed(3) }; }
console.log(JSON.stringify(meta));
