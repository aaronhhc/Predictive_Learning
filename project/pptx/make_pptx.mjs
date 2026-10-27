// Builds ../presentation.pptx with native, editable PowerPoint objects.
// Design tokens mirror theme.scss (T1 42px=31.5pt, T2 31px=23pt, T3 26px=19.5pt, T4 22px=16.5pt, T5 18px=13.5pt).
import pptxgen from 'pptxgenjs';
import JSZip from 'jszip';
import { writeFileSync } from 'node:fs';
import { EQ } from './equations.mjs';
import { texToSvg, svgsToPng } from './math.mjs';

const eqs = [];   // every distinct (equation, colour) pair that is placed on a slide
function build(png) {
const pptx = new pptxgen();
pptx.defineLayout({ name: 'W', width: 13.333, height: 8.333 });
pptx.layout = 'W';
pptx.title = 'Impact of Weather Information Availability on One-Hour-Ahead Bike-Sharing Demand Forecasting: A Cross-Model Study';
const F = 'Arial';
const C = { text:'1F2328', head:'111827', blue:'0B5CAD', model:'B45309', warn:'DC2626', ok:'15803D', muted:'6B7280', line:'E5E7EB', th:'F6F8FA', claimBg:'F8FAFC', grey:'F3F4F6', navy:'0B2545' };
const T1=31.5, T2=23, T3=19.5, T4=16.5, T5=13.5;
const X=0.4, W=12.53;

function base(title, n) {
  const s = pptx.addSlide(); s.background = { color:'FFFFFF' };
  s.addText(title, { x:X, y:0.25, w:W, h:0.7, fontFace:F, fontSize:T1, bold:true, color:C.head, valign:'middle', margin:0 });
  s.addShape(pptx.ShapeType.line, { x:X, y:1.0, w:W, h:0, line:{ color:C.line, width:1.5 } });
  s.addText(`${n} / 14`, { x:11.9, y:7.95, w:1.03, h:0.3, fontFace:F, fontSize:11, color:C.muted, align:'right', margin:0 });
  return s;
}
const t = (s, runs, o) => s.addText(runs, Object.assign({ fontFace:F, fontSize:T3, color:C.text, valign:'top', margin:0 }, o));
const b = (text, o={}) => ({ text, options:Object.assign({ bold:true }, o) });
const r = (text, o={}) => ({ text, options:o });
const bl = (runs, o={}) => runs.map((x,i)=>{ const q = typeof x==='string'?{text:x,options:{}}:x; if(i===0) q.options=Object.assign({bullet:{indent:16}},q.options); return q; });
function bullets(s, items, o) { // items: array of strings or run arrays
  const arr=[]; items.forEach(it=>{ const runs = typeof it==='string'?[r(it)]:it; runs.forEach((q,i)=>{ const opt=Object.assign({}, q.options); if(i===0) opt.bullet={indent:16}; if(i===runs.length-1) opt.breakLine=true; arr.push({text:q.text, options:opt}); }); });
  t(s, arr, Object.assign({ fontSize:T4, paraSpaceAfter:5 }, o));
}
function claim(s, runs, x, y, w, h, color=C.blue, bg=C.claimBg) {
  s.addShape(pptx.ShapeType.rect, { x, y, w, h, fill:{color:bg}, line:{color:bg, width:0} });
  s.addShape(pptx.ShapeType.rect, { x, y, w:0.07, h, fill:{color}, line:{color, width:0} });
  t(s, runs, { x:x+0.25, y, w:w-0.4, h, fontSize:T2, valign:'middle' });
}
const noB = { type:'none' };
const rule = { type:'solid', pt:0.75, color:'D1D5DB' };
function table(s, rows, colW, o={}) {
  const fs = o.fontSize || T4;
  const data = rows.map((row,ri)=>row.map((cell,ci)=>{
    const c = typeof cell==='object' && !Array.isArray(cell) && cell.text!==undefined && !cell.options ? cell : { text:cell };
    const opts = Object.assign({ fontFace:F, fontSize:fs, color:C.text, valign:'middle', margin:[0.04,0.1,0.04,0.1],
      border:[noB,noB,ri===0?{type:'solid',pt:1.5,color:'D1D5DB'}:rule,noB], bold:ri===0,
      fill: ri===0?{color:C.th}:undefined, align:(o.center&&o.center.includes(ci))?'center':'left' }, c.options||{});
    return { text:c.text, options:opts };
  }));
  s.addTable(data, { x:o.x??X, y:o.y, w:colW.reduce((a,v)=>a+v,0), colW, rowH:o.rowH, autoPage:false });
}
function box(s, x,y,w,h, o={}) { s.addShape(pptx.ShapeType.roundRect, { x,y,w,h, rectRadius:0.06, fill:{color:o.fill||'FFFFFF'}, line:{color:o.line||C.line, width:o.lw||1.25, dashType:o.dash} }); }
function chip(s, x,y,w, label, color, o={}) {
  s.addShape(pptx.ShapeType.roundRect, { x,y,w,h:0.34, rectRadius:0.05, fill:{color:o.hollow?'FFFFFF':color}, line:{color, width:o.hollow?2:0, dashType:o.hollow?'dash':undefined} });
  t(s, label, { x,y,w,h:0.34, fontSize:T5, bold:true, color:o.hollow?color:'FFFFFF', align:'center', valign:'middle' });
}

function eq(s, key, o) { // o: x,y,w,h box; pt font size; color; align
  const pt=o.pt||18, color=o.color||C.text;
  const id=`${key}_${color}`; let e=eqs.find(q=>q.id===id);
  if(!e){ e={id, key, color, ...texToSvg(EQ[key], color)}; eqs.push(e); }
  const iw=e.wEm*pt/72, ih=e.hEm*pt/72, w=o.w??iw, h=o.h??ih;
  if(iw>w+0.01||ih>h+0.01) console.warn('EQ too large for box', key, iw.toFixed(2), ih.toFixed(2), 'box', w, h);
  const x=o.align==='center'?o.x+(w-iw)/2:o.align==='right'?o.x+w-iw:o.x;
  s.addImage({ data: 'data:image/png;base64,'+(png?Buffer.from(png[id]).toString('base64'):'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='), x, y:o.y+(h-ih)/2, w:iw, h:ih, altText:`eq:${id} | ${EQ[key].replace(/\s+/g,' ')}` });
}

// ---------------- 1 Cover (left 60% text; right 40% intentionally empty for a photo added in PowerPoint) ----------------
{
  const s = pptx.addSlide(); s.background = { color:'FFFFFF' };
  const CX=0.9, CW=7.0, NAVY=C.navy;
  const ct = (txt,o)=>t(s, txt, Object.assign({ align:'left' }, o));
  s.addShape(pptx.ShapeType.rect, { x:0, y:0, w:0.28, h:8.333, fill:{color:C.blue}, line:{color:C.blue,width:0} });
  ct('MIDTERM RESEARCH PROPOSAL', { x:CX, y:1.73, w:CW, h:0.4, fontSize:T4, bold:true, color:C.blue, charSpacing:3 });
  ct('Impact of Weather Information Availability on One-Hour-Ahead Bike-Sharing Demand Forecasting: A Cross-Model Study', { x:CX, y:2.47, w:8.41, h:2.54, fontSize:36, bold:true, color:NAVY, lineSpacingMultiple:1.05 });
  ct('Predictive Learning', { x:CX, y:5.65, w:CW, h:0.4, fontSize:T3, bold:true, color:NAVY });
  ct('Department of Computer Science and Information Engineering', { x:CX, y:6.1, w:CW, h:0.35, fontSize:T4 });
  ct('National Taiwan Normal University', { x:CX, y:6.45, w:CW, h:0.35, fontSize:T4 });
  ct('October 27, 2026', { x:CX, y:6.8, w:CW, h:0.35, fontSize:T4 });
  ct('Group Members:  [Member A]  ·  [Member B]  ·  [Member C]  ·  [Member D]', { x:CX, y:7.3, w:CW, h:0.35, fontSize:15, color:C.muted });
}

// ---------------- 2 Background ----------------
{
  const s = base('Research Background and Motivation', 2);
  claim(s, [r('Weather is a recognized driver of bike-sharing use, but a '), b('forecast', {color:C.blue}), r(' can only use weather that is already known.')], X, 1.2, W, 1.15);
  const cw=4.05, gap=0.19, y=2.65, h=3.55;
  const cards = [
    ['Demand depends on weather', 'Cold, rain and high humidity are associated with fewer and shorter bikeshare trips (Gebhart & Noland, 2014). Weather and temporal factors recur across the bike-sharing literature (Eren & Uz, 2020).'],
    ['Seoul hourly data is public', 'The Seoul Bike Sharing Demand data pairs hourly rental counts with weather and calendar fields, and has been used for weather-based demand prediction (Sathishkumar & Cho, 2020).'],
    ['Evaluation must match use', 'Hourly forecasts are made at a forecast origin and applied to later months. Which weather is available, and how flexible the model is, should be judged out of time.'],
  ];
  cards.forEach((c,i)=>{ const x=X+i*(cw+gap); box(s,x,y,cw,h);
    t(s, c[0], { x:x+0.2, y:y+0.18, w:cw-0.4, h:0.7, fontSize:T4, bold:true, color:C.blue });
    t(s, c[1], { x:x+0.2, y:y+0.9, w:cw-0.4, h:2.5, fontSize:T4 }); });
  t(s, 'Scope: system-wide hourly rental counts only; no station, return-flow or inventory data, so no rebalancing claims.', { x:X, y:6.55, w:W, h:0.4, fontSize:T4, color:C.muted });
}

// ---------------- 3 Problem ----------------
{
  const s = base('Research Problem and Forecasting Scenario', 3);
  claim(s, [r('Which information is available at the '), b('forecast origin', {color:C.blue}), r(', and how complex should the model be?')], X, 1.2, W, 1.0);
  // scenario strip
  box(s, X, 2.45, W, 1.55, { fill:C.claimBg });
  t(s, 'Forecasting scenario', { x:X+0.25, y:2.55, w:4, h:0.35, fontSize:T4, bold:true, color:C.blue });
  bullets(s, [
    [b('Target: '), r('system-wide Rented Bike Count in the target hour (rentals per hour)')],
    [b('Forecast origin: '), r('end of the previous hour; only earlier observations may be used')],
    [b('Protocol: '), r('rolling one-step forecasts; model parameters stay frozen during testing')],
  ], { x:X+0.25, y:2.95, w:W-0.5, h:1.0 });
  const cw=4.05, gap=0.19, y=4.25, h=2.9;
  const P = [
    ['P1  Information availability', 'Is previous-hour observed weather useful? How much does target-hour actual weather change the picture?'],
    ['P2  Model complexity', 'How do regularization and flexibility affect generalization from winter–spring training to later months?'],
    ['P3  Attribution and errors', 'What do demand history, time, calendar and weather each add, and when do forecasts fail?'],
  ];
  P.forEach((c,i)=>{ const x=X+i*(cw+gap); box(s,x,y,cw,h);
    t(s, c[0], { x:x+0.2, y:y+0.18, w:cw-0.4, h:0.4, fontSize:T4, bold:true, color:C.blue });
    t(s, c[1], { x:x+0.2, y:y+0.7, w:cw-0.4, h:2.0, fontSize:T4 }); });
}

// ---------------- 4 Related work I ----------------
{
  const s = base('Related Work: Bike-Sharing Demand Forecasting', 4);
  table(s, [
    ['Study', 'Setting', 'What it contributes'],
    [{text:'Eren & Uz (2020)'}, 'Review of station-based bike-sharing research', 'Organizes factors behind demand: weather, built environment, public transport, socio-demographics, temporal and safety factors.'],
    [{text:'Sathishkumar & Cho (2020)'}, 'Seoul hourly rentals with weather data', 'Weather-based, rule-based model for Seoul bike demand prediction; this line of work uses the Seoul Bike dataset adopted here.'],
    [{text:'Xin (2026)'}, 'Seoul and Washington, DC; one-hour-ahead', 'Probabilistic forecasting with Transformer-based and other models; reports point error and 80% interval coverage.'],
  ], [2.7, 3.5, 6.33], { y:1.3, rowH:[0.45,1.2,1.2,1.2] });
  claim(s, [r('Prior work links weather to demand and forecasts Seoul hourly demand with learned models.')], X, 5.75, W, 1.05);
  t(s, 'Sources: see References (slide 14). Descriptions summarize each work\'s stated scope.', { x:X, y:7.05, w:W, h:0.3, fontSize:T5, color:C.muted });
}

// ---------------- 5 Related work II ----------------
{
  const s = base('Related Work: Weather Information and Predictive Models', 5);
  t(s, 'Weather evidence', { x:X, y:1.2, w:5.8, h:0.4, fontSize:T4, bold:true, color:C.blue });
  bullets(s, [
    'Gebhart & Noland (2014), Washington, DC: cold temperature, rain and high humidity reduce both the likelihood and duration of bikeshare trips.',
    'Eren & Uz (2020): weather is one of several factor groups studied for demand.',
    'Sathishkumar & Cho (2020): weather variables used for Seoul demand prediction.',
  ], { x:X, y:1.65, w:5.8, h:3.6 });
  t(s, 'Predictive models: Xin (2026), Seoul, one hour ahead', { x:6.5, y:1.2, w:6.4, h:0.4, fontSize:T4, bold:true, color:C.blue });
  table(s, [
    ['Model', 'MAE (rentals/h)', '80% coverage'],
    ['N-BEATS', '115.07', '75.42%'],
    ['Random Forest', '115.86', '89.26%'],
    ['TFT', '306.98', '81.11%'],
    ['Transformer', '317.72', '74.01%'],
  ], [2.2, 2.1, 2.1], { x:6.5, y:1.7, rowH:0.42, center:[1,2] });
  t(s, 'Reported by Xin (2026), Table 2 (p. 6). Not our results and not directly comparable to ours.', { x:6.5, y:4.1, w:6.4, h:0.55, fontSize:T5, color:C.muted });
  claim(s, [r('Lowest point error does not imply the best interval coverage.')], 6.5, 4.9, 6.43, 1.15, C.blue);
  t(s, 'Open point: the literature does not specify, field by field, which weather values exist at the forecast origin of a one-hour-ahead forecast.', { x:X, y:6.3, w:W, h:0.8, fontSize:T4 });
}

// ---------------- 6 Gap ----------------
{
  const s = base('Research Gap and Proposed Contribution', 6);
  table(s, [
    ['Insufficiently clarified question', 'What prior work leaves open', 'Our contribution'],
    ['Information timing', 'Xin (2026) describes target-time covariates; availability of each field at the forecast origin is not fully specified (not an allegation of leakage).', 'Explicit E1 / E2 / E3 information settings under one protocol'],
    ['Complexity control', 'Models from different families are compared; controlled complexity curves are not the focus.', 'Ridge α, KNN k and tree-depth curves with train vs. validation error (X2, X3)'],
    ['Information value', 'Which input group matters, and where errors concentrate, is not isolated.', 'Group ablation and temporal error slices (X4, X5)'],
  ], [2.5, 5.5, 4.53], { y:1.25, rowH:[0.45,1.25,1.05,0.95] });
  t(s, [b('Shared with Xin (2026): '), r('date boundaries of the chronological split. '), b('Different: '), r('five weather variables and three demand lags, a 168-hour warm-up, and the definition of eligible samples.')], { x:X, y:5.45, w:W, h:0.8, fontSize:T4 });
  claim(s, [b('Not claimed: ', {color:C.warn}), r('the first weather study, any leakage in prior work, or superiority over probabilistic methods.')], X, 6.4, W, 1.1, C.warn, 'FEF2F2');
}

// ---------------- 7 Aim & RQ ----------------
{
  const s = base('Research Aim and Research Questions', 7);
  claim(s, [b('Aim: ', {color:C.blue}), r('separate the value of '), b('available', {color:C.blue}), r(' weather information from retrospective information, and study model complexity under out-of-time evaluation.')], X, 1.2, W, 1.45);
  table(s, [
    ['', 'Research question', 'Objective', 'Falsifiable hypothesis', 'Analyses'],
    ['RQ1', 'Does previous-hour observed weather improve next-hour forecasts, and how does target-hour actual weather differ?', 'Quantify E1 vs. E2 vs. E3', 'E2 may beat E1; E3 may help precipitation hours but is not guaranteed to beat E2.', 'X1, X4, X5'],
    ['RQ2', 'How do model complexity and regularization affect out-of-time generalization?', 'Map train vs. validation error', 'Moderate regularization may help; complex models need not win.', 'X1, X2, X3'],
    ['RQ3', 'What do demand, time, calendar and weather contribute, and where do models fail?', 'Attribute value and locate errors', 'Demand history may add most; peak hours may have larger absolute error.', 'X4, X5'],
  ], [0.75, 4.15, 2.4, 3.9, 1.33], { y:2.85, rowH:[0.45,1.25,1.1,1.1] });
}

// ---------------- 8 Dataset ----------------
{
  const s = base('Dataset, Preprocessing and Chronological Split', 8);
  const m = [['8,760','hourly observations, 14 columns',C.head],['8,297','eligible samples',C.head],['4,152','training',C.blue],['720','validation',C.model],['3,425','test',C.ok]];
  const mw=2.35, mg=(W-5*mw)/4;
  m.forEach((q,i)=>{ const x=X+i*(mw+mg); box(s,x,1.2,mw,1.05);
    t(s, q[0], { x:x+0.15, y:1.25, w:mw-0.3, h:0.55, fontSize:T1, bold:true, color:q[2] });
    t(s, q[1], { x:x+0.15, y:1.78, w:mw-0.3, h:0.4, fontSize:T5, color:C.muted }); });
  // split bar: 365 days over W
  const d=W/365, ww=7*d, tr=175*d, va=30*d, te=153*d; let x=X; const y=2.75, h=0.55;
  s.addShape(pptx.ShapeType.rect,{x,y,w:ww,h,fill:{color:'9CA3AF'},line:{color:'9CA3AF',width:0}}); x+=ww;
  s.addShape(pptx.ShapeType.rect,{x,y,w:tr,h,fill:{color:C.blue},line:{color:C.blue,width:0}}); t(s,'Train',{x,y,w:tr,h,fontSize:T4,bold:true,color:'FFFFFF',align:'center',valign:'middle'}); x+=tr;
  s.addShape(pptx.ShapeType.rect,{x,y,w:va,h,fill:{color:C.model},line:{color:C.model,width:0}}); t(s,'Val',{x,y,w:va,h,fontSize:T4,bold:true,color:'FFFFFF',align:'center',valign:'middle'}); x+=va;
  s.addShape(pptx.ShapeType.rect,{x,y,w:te,h,fill:{color:C.ok},line:{color:C.ok,width:0}}); t(s,'Test',{x,y,w:te,h,fontSize:T4,bold:true,color:'FFFFFF',align:'center',valign:'middle'});
  t(s,'Dec 1–7, 2017: 168-h warm-up',{x:X,y:2.4,w:4,h:0.3,fontSize:T5,color:C.muted});
  t(s,'Dec 8, 2017',{x:X+ww,y:3.35,w:2,h:0.3,fontSize:T5,color:C.muted});
  t(s,'Jun 1, 2018',{x:X+ww+tr-0.9,y:3.35,w:1.8,h:0.3,fontSize:T5,color:C.muted,align:'center'});
  t(s,'Jul 1',{x:X+ww+tr+va-0.5,y:3.35,w:1.0,h:0.3,fontSize:T5,color:C.muted,align:'center'});
  t(s,'Nov 30, 2018',{x:X+W-2.5,y:3.35,w:2.5,h:0.3,fontSize:T5,color:C.muted,align:'right'});
  // steps
  const steps = [
    ['1  Align timestamps', 'Date + Hour become a unique hourly timestamp (Seoul local time); no gaps, no missing cells.'],
    ['2  Build lags first', 'lag_1, lag_24 and lag_168 are shifted on the full hourly axis; non-functioning hours stay as observed history.'],
    ['3  Select eligible rows', 'Score only Functioning Day = Yes targets with all lags available: 8,465 operating hours, 8,297 after warm-up.'],
    ['4  Fit on train only', 'StandardScaler and encoders are fitted on training rows, then applied to validation and test.'],
  ];
  const sw=2.95, sg=(W-4*sw)/3, sy=3.85, sh=2.35;
  steps.forEach((q,i)=>{ const x0=X+i*(sw+sg); box(s,x0,sy,sw,sh,{fill:i===3?'F0FDF4':'FFFFFF', line:i===3?C.ok:C.line});
    t(s,q[0],{x:x0+0.15,y:sy+0.12,w:sw-0.3,h:0.4,fontSize:T4,bold:true,color:C.blue});
    t(s,q[1],{x:x0+0.15,y:sy+0.58,w:sw-0.3,h:1.7,fontSize:T4});
    if(i<3) t(s,'›',{x:x0+sw,y:sy+0.8,w:sg,h:0.6,fontSize:T1,color:C.muted,align:'center'}); });
  claim(s, [b('Leakage control: ', {color:C.blue}), r('chronological split, past-only lags, no target-hour demand input.')], X, 6.4, W, 0.85);
  t(s,'Source: Kaggle, Seoul Bike Sharing Demand Prediction (SeoulBikeData.csv); file checksum identical to the UCI release. Bar length proportional to calendar days.',{x:X,y:7.4,w:11.4,h:0.5,fontSize:T5,color:C.muted});
}

// ---------------- 9 Features & E1-E3 ----------------
{
  const s = base('Feature Engineering and Information Settings (E1–E3)', 9);
  const sh = 3.35, ty=1.2;
  s.addShape(pptx.ShapeType.rect,{x:9.85,y:ty,w:3.08,h:sh,fill:{color:C.grey},line:{color:C.grey,width:0}});
  s.addShape(pptx.ShapeType.line,{x:9.85,y:ty,w:0,h:sh,line:{color:C.head,width:2.25,dashType:'dash'}});
  const cx=[4.9,6.55,8.75];
  [['t168','last week'],['t24','yesterday'],['t1','last completed hour']].forEach((q,i)=>{
    eq(s,q[0],{x:cx[i]-1.1,y:ty+0.02,w:2.2,h:0.3,pt:15,align:'center',color:C.head});
    t(s,q[1],{x:cx[i]-1.1,y:ty+0.36,w:2.2,h:0.3,fontSize:T5,align:'center',color:C.muted}); });
  t(s,'Target hour',{x:10.2,y:ty+0.02,w:2.5,h:0.3,fontSize:T4,bold:true,align:'center',color:C.ok});
  t(s,'predict',{x:10.2,y:ty+0.36,w:1.2,h:0.3,fontSize:T5,align:'right',color:C.muted});
  eq(s,'yTarget',{x:11.5,y:ty+0.34,w:0.8,h:0.3,pt:15,color:C.muted});
  const lanes=[['E1 · 13 features','No explicit weather'],['E2 · 18 features','Previous-hour observed weather'],['E3 · 18 features','Target-hour weather (oracle)']];
  const ly=[ty+0.95, ty+1.75, ty+2.55];
  lanes.forEach((q,i)=>{
    t(s,q[0],{x:X,y:ly[i]-0.28,w:3.2,h:0.3,fontSize:T4,bold:true,color:i===2?C.warn:C.head});
    t(s,q[1],{x:X,y:ly[i]+0.02,w:3.2,h:0.3,fontSize:T5,color:C.muted});
    if(i<2) s.addShape(pptx.ShapeType.line,{x:X,y:ly[i]+0.5,w:W,h:0,line:{color:C.line,width:0.75}});
    const cy=ly[i]-0.1;
    chip(s,cx[0]-0.7,cy,1.4,'lag_168',C.blue);
    chip(s,cx[1]-0.7,cy,1.4,'lag_24',C.blue);
    if(i===1){ chip(s,7.55,cy,0.95,'lag_1',C.blue); chip(s,8.6,cy,1.0,'',C.model); eq(s,'wPrev',{x:8.6,y:cy,w:1.0,h:0.34,pt:15,align:'center',color:'FFFFFF'});}
    else chip(s,cx[2]-0.5,cy,1.0,'lag_1',C.blue);
    if(i<2) chip(s,10.9,cy,1.7,'time + calendar','6B7280');
    else { chip(s,10.15,cy,1.55,'time + calendar','6B7280'); chip(s,11.8,cy,1.0,'',C.warn,{hollow:true}); eq(s,'wTarget',{x:11.8,y:cy,w:1.0,h:0.34,pt:15,align:'center',color:C.warn}); }
  });
  t(s,'Forecast origin',{x:8.9,y:ty+sh+0.02,w:1.9,h:0.3,fontSize:T5,bold:true,color:C.head,align:'right'});
  t(s,'not yet observed',{x:10.9,y:ty+sh+0.02,w:2.0,h:0.3,fontSize:T5,color:C.muted,align:'center'});
  table(s, [
    ['Group', 'Columns', 'Encoding', 'Dim.'],
    ['H  Historical demand', 'lag_1, lag_24, lag_168', 'StandardScaler', '3'],
    ['T  Time', 'Hour and Weekday of the target hour', 'sin / cos pairs', '4'],
    ['C  Calendar', 'Season (4 levels), Holiday (2 levels)', 'One-hot', '6'],
    ['W  Weather', 'Temperature, Humidity, Wind speed, Rainfall, Snowfall', 'StandardScaler', '5'],
  ], [2.7, 6.0, 2.6, 1.23], { y:4.95, rowH:0.4, center:[3] });
  t(s,'E1 = H + T + C. E2 adds the previous-hour weather; E3 replaces it with target-hour weather. E3 is a retrospective oracle, is not deployable, and need not beat E2. Target-hour demand is never an input.',{x:X,y:7.1,w:W-1.4,h:0.7,fontSize:T5,color:C.muted});
}

// ---------------- 10 X1-X3 ----------------
{
  const s = base('Experimental Design: X1–X3', 10);
  t(s,'X1–X5 are analyses; E1–E3 are information settings. They are crossed, not eight separate experiments.',{x:X,y:1.15,w:W,h:0.35,fontSize:T5,color:C.muted});
  table(s, [
    ['Analysis', 'Models', 'E1', 'E2', 'E3', 'Varied or controlled'],
    ['X1  Model comparison', 'Ridge, KNN, Random Forest, 3 naive', '●', '●', '●', 'Model × information setting'],
    ['X2  Ridge regularization', 'Ridge', '○', '●', '○', 'Penalty α'],
    ['X3  Complexity control', 'KNN, Decision Tree', '–', '●', '–', 'k; max_depth'],
    ['X4  Weather and ablation', 'Ridge, Random Forest', '●', '●', '●', 'Setting; removed group (E2)'],
    ['X5  Temporal error analysis', 'Best E2 model by validation', '○', '●', '○', 'Hour, month, day type, rain'],
  ], [3.1, 4.0, 0.7, 0.7, 0.7, 3.33], { y:1.55, rowH:0.4, center:[2,3,4] });
  t(s,'● main analysis   ○ supplementary comparison   – not used',{x:X,y:4.1,w:W,h:0.3,fontSize:T5,color:C.muted});
  const cw=4.05, gap=0.19, y=4.55, h=2.2;
  const C3 = [
    ['X1 · Model comparison', [
      'Does the model ranking change with the information setting?',
      'Ridge, KNN, Random Forest × E1, E2, E3, plus 3 naive baselines' ]],
    ['X2 · Ridge regularization', [
      'How does L2 strength change out-of-time error?',
      'E2 fixed; 10 log-spaced α; train vs. validation RMSE' ]],
    ['X3 · Complexity control', [
      'Does added flexibility only lower training error?',
      'E2 fixed; KNN k = 1–97; tree max_depth = 2–16, None' ]],
  ];
  C3.forEach((c,i)=>{ const x=X+i*(cw+gap); box(s,x,y,cw,h);
    t(s,c[0],{x:x+0.2,y:y+0.12,w:cw-0.4,h:0.4,fontSize:T4,bold:true,color:C.blue});
    bullets(s,c[1],{x:x+0.2,y:y+0.6,w:cw-0.4,h:1.55}); });
  box(s,X,6.9,W,0.95,{fill:C.claimBg});
  t(s,'X2 Ridge objective',{x:X+0.25,y:6.9,w:3.0,h:0.95,fontSize:T4,bold:true,color:C.blue,valign:'middle'});
  eq(s,'ridge',{x:3.6,y:6.92,w:9.0,h:0.9,pt:19,align:'center'});
}

// ---------------- 11 X4-X5 ----------------
{
  const s = base('Experimental Design: X4–X5', 11);
  t(s,'X4 · Weather information and feature ablation',{x:X,y:1.15,w:6.1,h:0.4,fontSize:T4,bold:true,color:C.blue});
  t(s,[b('4a  E1 vs. E2 vs. E3. '),r('Ridge and Random Forest on identical samples.')],{x:X,y:1.6,w:6.1,h:0.6,fontSize:T4});
  eq(s,'gain',{x:X+0.2,y:2.22,w:5.9,h:0.5,pt:18});
  eq(s,'gap',{x:X+0.2,y:2.8,w:5.9,h:0.5,pt:18});
  t(s,[b('4b  Group ablation on E2. '),r('Hyperparameters fixed from Full E2; same samples.')],{x:X,y:3.45,w:6.1,h:0.6,fontSize:T4});
  table(s, [
    ['Variant','Removed columns'],
    ['Full E2','none (reference)'],
    ['− H','lag_1, lag_24, lag_168'],
    ['− T','hour and weekday sin / cos'],
    ['− C','season and holiday'],
    ['− W','5 weather columns (= E1)'],
  ], [1.6,4.5], { y:4.1, rowH:0.36 });
  eq(s,'ablate',{x:X+0.2,y:6.35,w:5.9,h:0.55,pt:18});
  t(s,'X5 · Temporal error analysis',{x:6.9,y:1.15,w:6.0,h:0.4,fontSize:T4,bold:true,color:C.blue});
  t(s,'Pre-specified slices of the test period, for the best E2 model by validation MAE:',{x:6.9,y:1.6,w:6.0,h:0.6,fontSize:T4});
  table(s, [
    ['Slice','Definition'],
    ['Hour','MAE for each target hour 0–23; night 00–05, peaks 07–09 and 17–19'],
    ['Month','July to November 2018'],
    ['Day type','Weekday vs. weekend; holiday flag'],
    ['Precipitation','Rainfall > 0 or Snowfall > 0 vs. none (scoring label only)'],
    ['Curve','Actual vs. predicted, 2018-07-01 to 2018-07-07 (fixed in advance)'],
  ], [1.7,4.33], { x:6.9, y:2.3, rowH:[0.37,0.8,0.4,0.4,0.8,0.8] });
  t(s,'Each slice reports n, mean rentals, MAE, RMSE and signed error.',{x:6.9,y:6.0,w:6.0,h:0.6,fontSize:T4});
  claim(s,[r('Ablation is not a causal intervention.')],X,7.05,W,0.7);
}

// ---------------- 12 Evaluation, resources, timeline ----------------
{
  const s = base('Evaluation Protocol, Resources and Project Timeline', 12);
  box(s,X,1.2,7.45,2.25);
  t(s,'Evaluation metrics',{x:X+0.2,y:1.28,w:5.8,h:0.35,fontSize:T4,bold:true,color:C.blue});
  eq(s,'mae',{x:X+0.2,y:1.7,w:2.8,h:0.85,pt:19});
  eq(s,'rmse',{x:X+3.35,y:1.65,w:3.9,h:1.0,pt:19});
  bullets(s,['Unit: rentals per hour; predictions clipped at 0','No MAPE (zero counts); rolling one-step forecasts'],{x:X+0.2,y:2.65,w:7.0,h:0.75});
  box(s,8.05,1.2,4.88,2.25);
  t(s,'Model selection and leakage control',{x:8.25,y:1.28,w:4.5,h:0.35,fontSize:T4,bold:true,color:C.blue});
  bullets(s,['Validation MAE selects hyperparameters','Test evaluated once on a pre-registered list','Scalers fitted on training rows only; no shuffled K-fold'],{x:8.25,y:1.7,w:4.5,h:1.7});
  // timeline
  t(s,'Project timeline',{x:X,y:3.65,w:4,h:0.35,fontSize:T4,bold:true,color:C.blue});
  s.addShape(pptx.ShapeType.line,{x:X,y:4.55,w:W,h:0,line:{color:C.blue,width:2.5}});
  const tl=[['Oct 26','Moodle upload by 23:59'],['Oct 27','Presentation (backup Nov 3)'],['Week 1','Shared pipeline, baselines, Ridge'],['Week 2','X1–X3 on train / validation; freeze settings'],['Week 3','X4 setup; LSTM extension'],['Week 4','Freeze list; run test and X5 once'],['Week 5','Reproducibility check, final report']];
  const nw=W/7;
  tl.forEach((q,i)=>{ const x=X+i*nw; s.addShape(pptx.ShapeType.ellipse,{x:x+0.05,y:4.45,w:0.2,h:0.2,fill:{color:i<2?C.model:C.blue},line:{color:'FFFFFF',width:1.5}});
    t(s,q[0],{x:x+0.02,y:4.15,w:nw-0.05,h:0.27,fontSize:T5,bold:true,color:C.head});
    t(s,q[1],{x:x+0.02,y:4.75,w:nw-0.1,h:0.95,fontSize:T5}); });
  const cw=4.05, gap=0.19, y=6.0, h=1.6;
  [['Resources and budget','Python, pandas, scikit-learn (Pedregosa et al., 2011), matplotlib on laptop CPUs. No additional budget.'],
   ['Collaboration','A: data and pipeline. B: Ridge, KNN (X2, X3). C: Random Forest (X1, X4). D: X5, integration, LSTM extension.'],
   ['Ethics and confidentiality','Public aggregated hourly data; no human subjects, personal data or animal experiments. No ethics review is claimed.']].forEach((c,i)=>{
    const x=X+i*(cw+gap); box(s,x,y,cw,h);
    t(s,c[0],{x:x+0.15,y:y+0.1,w:cw-0.3,h:0.35,fontSize:T4,bold:true,color:C.blue});
    t(s,c[1],{x:x+0.15,y:y+0.5,w:cw-0.3,h:1.3,fontSize:T5+1}); });
}

// ---------------- 13 Outcomes ----------------
{
  const s = base('Proposed Outcomes and Research Limitations', 13);
  t(s,'Planned analyses and deliverables',{x:X,y:1.15,w:6.1,h:0.4,fontSize:T4,bold:true,color:C.ok});
  bullets(s,[
    'Model × information-setting table of MAE and RMSE, with naive baselines',
    'Quantified Gain and Gap between E1, E2 and E3',
    'Ridge α curve; KNN k and tree-depth curves',
    'Group-ablation chart of MAE change (H, T, C, W)',
    'Hourly, monthly, weekday and precipitation error analysis',
    'Reproducible, time-ordered, leakage-checked pipeline',
  ],{x:X,y:1.6,w:6.1,h:3.9});
  t(s,'Research limitations',{x:6.9,y:1.15,w:6.0,h:0.4,fontSize:T4,bold:true,color:C.warn});
  bullets(s,[
    'One city and one year; no multi-year or cross-city claim',
    'Season and time are confounded in the split',
    'Aggregate rentals are not station demand or unmet demand',
    'E2 assumes the previous hour is already published',
    'E3 is oracle information, not a weather forecast',
    'Point forecasts only; no interval calibration',
  ],{x:6.9,y:1.6,w:6.0,h:3.9});
  t(s,'Figures shown in the final report will come from executed experiments; none are claimed here.',{x:X,y:5.5,w:W,h:0.35,fontSize:T5,color:C.muted});
  claim(s,[b('Contribution: ',{color:C.blue}),r('a reproducible protocol separating available from retrospective weather information, with complexity and error analysis.')],X,6.0,W,1.5);
}

// ---------------- 14 References ----------------
{
  const s = base('References', 14);
  const refs = [
    'Eren, E., & Uz, V. E. (2020). A review on bike-sharing: The factors affecting bike-sharing demand. Sustainable Cities and Society, 54, 101882. https://doi.org/10.1016/j.scs.2019.101882',
    'Gebhart, K., & Noland, R. B. (2014). The impact of weather conditions on bikeshare trips in Washington, DC. Transportation, 41(6), 1205–1225. https://doi.org/10.1007/s11116-014-9540-7',
    'Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.',
    'Sathishkumar, V. E., & Cho, Y. (2020). A rule-based model for Seoul Bike sharing demand prediction using weather data. European Journal of Remote Sensing, 53(sup1), 166–183. https://doi.org/10.1080/22797254.2020.1725789',
    'Xin, Q. (2026). Probabilistic bike-sharing demand forecasting under changing weather and seasonal regimes with Transformer-based models. Findings. https://doi.org/10.32866/001c.157499',
    'Seoul Bike Sharing Demand [Data set]. UCI Machine Learning Repository. https://doi.org/10.24432/C5F62R',
    'Seoul Bike Sharing Demand Prediction [Data set]. Kaggle. https://www.kaggle.com/datasets/saurabhshahane/seoul-bike-sharing-demand-prediction',
  ];
  const arr=[]; refs.forEach(q=>arr.push({text:q,options:{breakLine:true,bullet:{type:'number'}}}));
  t(s,arr,{x:X,y:1.25,w:W,h:6.3,fontSize:T4,paraSpaceAfter:9});
}

return pptx;
}

// helper used inside build(): place a LaTeX equation as a picture (vector SVG + PNG fallback is added after writing)
// ---------------------------------------------------------------------------------------------------------------
build(null);                                   // pass 1: collect equations
const pngs = await svgsToPng(eqs);
const pngMap = Object.fromEntries(eqs.map((e,i)=>[e.id, pngs[i]]));
const out = build(pngMap);                     // pass 2: real images
const buf = await out.write({ outputType:'nodebuffer' });

// Post-process: add the SVG as svgBlip (PowerPoint 2016+/365) behind the PNG fallback.
const zip = await JSZip.loadAsync(buf);
let ct = await zip.file('[Content_Types].xml').async('string');
if (!/Extension="svg"/.test(ct)) ct = ct.replace('<Default ', '<Default Extension="svg" ContentType="image/svg+xml"/><Default ');
zip.file('[Content_Types].xml', ct);
let n = 0;
for (const f of Object.keys(zip.files).filter(f=>/^ppt\/slides\/slide\d+\.xml$/.test(f))) {
  let xml = await zip.file(f).async('string');
  const relF = f.replace('slides/','slides/_rels/') + '.rels';
  let rels = await zip.file(relF).async('string');
  xml = xml.replace(/<p:pic>[\s\S]*?<\/p:pic>/g, pic => {
    const m = pic.match(/descr="eq:([^"|]+)/); if (!m) return pic;
    const e = eqs.find(q=>q.id===m[1].trim());
    const name = `eq${++n}.svg`; zip.file(`ppt/media/${name}`, e.svg);
    const rid = `rIdSvg${n}`;
    rels = rels.replace('</Relationships>', `<Relationship Id="${rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/${name}"/></Relationships>`);
    return pic.replace(/<a:blip ([^>]*?)\/>/, `<a:blip $1><a:extLst><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}"><asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" r:embed="${rid}"/></a:ext></a:extLst></a:blip>`);
  });
  zip.file(f, xml); zip.file(relF, rels);
}
writeFileSync('../presentation.pptx', await zip.generateAsync({ type:'nodebuffer', compression:'DEFLATE' }));
writeFileSync('equations.tex', Object.entries(EQ).map(([k,v])=>`% ${k}\n\\[ ${v.replace(/\n/g,' ')} \\]\n`).join('\n'));
console.log('written, svg equations embedded:', n);
