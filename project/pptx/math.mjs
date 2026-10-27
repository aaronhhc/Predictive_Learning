// LaTeX -> standalone vector SVG (MathJax, bundled locally; no network) + PNG fallback via headless Chrome.
import { mathjax } from 'mathjax-full/js/mathjax.js';
import { TeX } from 'mathjax-full/js/input/tex.js';
import { SVG } from 'mathjax-full/js/output/svg.js';
import { liteAdaptor } from 'mathjax-full/js/adaptors/liteAdaptor.js';
import { RegisterHTMLHandler } from 'mathjax-full/js/handlers/html.js';
import { AllPackages } from 'mathjax-full/js/input/tex/AllPackages.js';
import puppeteer from 'puppeteer-core';

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const doc = mathjax.document('', { InputJax: new TeX({ packages: AllPackages }), OutputJax: new SVG({ fontCache: 'none' }) });

// Returns { svg, wEm, hEm } for a color; 1 em = 1000 viewBox units.
export function texToSvg(latex, color) {
  const node = doc.convert(latex, { display: true });
  let s = adaptor.innerHTML(node);
  s = s.match(/<svg[\s\S]*<\/svg>/)[0];
  const vb = s.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
  const pad = 80; // keep glyph overhang (italic, parentheses) inside the frame
  vb[0] -= pad; vb[1] -= pad; vb[2] += 2 * pad; vb[3] += 2 * pad;
  s = s.replace(/viewBox="[^"]+"/, `viewBox="${vb.join(' ')}"`);
  const wEm = vb[2] / 1000, hEm = vb[3] / 1000;
  const px = 100; // arbitrary absolute size; PowerPoint scales to the picture frame
  s = s.replace(/<svg[^>]*>/, m => m
    .replace(/width="[^"]*"/, `width="${(wEm * px).toFixed(2)}px"`)
    .replace(/height="[^"]*"/, `height="${(hEm * px).toFixed(2)}px"`)
    .replace(/style="[^"]*"/, '')
    .replace('<svg', '<svg xmlns:xlink="http://www.w3.org/1999/xlink"')) ;
  if (!/xmlns="http:\/\/www.w3.org\/2000\/svg"/.test(s)) s = s.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
  s = s.replace(/currentColor/g, '#' + color);
  return { svg: s, wEm, hEm };
}

export async function svgsToPng(items) { // items: [{svg,wEm,hEm}] -> Buffer[] (transparent, high-res)
  const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new' });
  const p = await b.newPage();
  const out = [];
  for (const it of items) {
    const scale = Math.min(8, 8000 / (it.wEm * 100)); // ~800 px per em, capped below the 16k texture limit
    const w = Math.ceil(it.wEm * 100 * scale), h = Math.ceil(it.hEm * 100 * scale);
    await p.setViewport({ width: w, height: h });
    const svg = it.svg.replace(/width="[^"]*"/, `width="${w}"`).replace(/height="[^"]*"/, `height="${h}"`);
    await p.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
    out.push(await p.screenshot({ omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } }));
  }
  await b.close();
  return out;
}
