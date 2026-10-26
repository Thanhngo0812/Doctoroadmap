const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const root = 'C:/Users/ngoco/Desktop/Doctoroadmap';
const out = __dirname;
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));
const currentSource = process.argv[2] || path.join(out, 'design/preview/w10_quiz_screens.html');
const expected = {
 here: ['Đề cương ôn tập các nhánh xiên vách động mạch liên thất trước', 'Bảng tra cứu phân bố giải phẫu nút xoang và nút nhĩ thất'],
 elsewhere: ['Tóm tắt công thức huyết động & Bảng so sánh nhánh mạch vành', 'Tổng quan các nhánh xiên vách và cơ chế tưới máu tâm trương']
};
async function inspectFilters(page) {
 const rows = [];
 for (const group of ['here', 'elsewhere', 'all']) {
   await page.locator('#tab-lib-' + group).focus();
   await page.keyboard.press('Enter');
   const actual = await page.locator('.doc-card:visible h3').allTextContents();
   const trimmed = actual.map(x => x.trim());
   const wanted = group === 'all' ? [expected.here[0], expected.elsewhere[0], expected.here[1], expected.elsewhere[1]] : expected[group];
   let assertionFailure = null;
   try { assert.deepEqual(trimmed, wanted, 'Visible library records must follow canonical group independently of origin'); }
   catch(e) { assertionFailure = { name: e.name, message: e.message }; }
   rows.push({group, actual:trimmed, expected:wanted, assertionFailure});
 }
 return rows;
}
(async () => {
 const browser = await chromium.launch();
 const report = {source:currentSource, browserVersion: browser.version(), externalRequestsAllowed:false, configurations:[], controls:[]};
 try {
  for(const width of [390,768,1280]) for(const theme of ['light','dark']) for(const reducedMotion of ['no-preference','reduce']) {
   const context = await browser.newContext({ viewport:{width,height:900}, reducedMotion });
   await context.route(/^https?:\/\//,r=>r.abort());
   const page=await context.newPage(); const pageErrors=[],consoleErrors=[];
   page.on('pageerror',e=>pageErrors.push(String(e)));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
   await page.goto(pathToFileURL(currentSource).href);
   if(theme==='dark') await page.locator('#theme-toggle-btn').click();
   await page.evaluate(()=>document.fonts.ready);
   const filters=await inspectFilters(page); assert.ok(filters.every(r=>!r.assertionFailure),'Current filter must select expected records');
   // Check the observable boundary at 5 -> 6 -> 5 using actual checkbox change handlers.
   const checkboxes=page.locator('.module-chips input');
   for(let i=0;i<5;i++) await checkboxes.nth(i).check();
   assert.equal(await page.locator('#btn-create-document').isEnabled(),true);
   assert.equal(await page.locator('#scope-warning-box').isVisible(),false);
   await checkboxes.nth(5).check();
   assert.equal(await page.locator('#btn-create-document').isDisabled(),true);
   assert.equal(await page.locator('#scope-warning-box').isVisible(),true);
   await checkboxes.nth(5).uncheck();
   assert.equal(await page.locator('#btn-create-document').isEnabled(),true);
   assert.equal(await page.locator('#scope-warning-box').isVisible(),false);
   const layout=await page.evaluate(()=>{
     const bounds=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,width:r.width,height:r.height,fontSize:s.fontSize,fontFamily:s.fontFamily};};
     const badTargets=[...document.querySelectorAll('button,.quiz-option,.module-chip,a')].filter(e=>e.getClientRects().length).map(e=>({text:e.textContent.trim(),...bounds(e)})).filter(b=>b.width<43.9||b.height<43.9);
     const math=[...document.querySelectorAll('.katex')].map(e=>({text:e.textContent,mathml:e.querySelectorAll('math').length,nested:e.querySelectorAll('.katex').length,bases:[...e.querySelectorAll('.mathnormal')].map(bounds),subscripts:[...e.querySelectorAll('.msub')].map(bounds)}));
     return {overflow:document.documentElement.scrollWidth>innerWidth,badTargets,math,fontFamily:getComputedStyle(document.body).fontFamily,fontLoaded:document.fonts.check('16px "Be Vietnam Pro"'),animations:[...document.querySelectorAll('.skeleton-line')].map(e=>getComputedStyle(e).animationName)};
   });
   assert.equal(layout.overflow,false,'No horizontal overflow');assert.deepEqual(layout.badTargets,[],'Touch targets >=44');
   assert.ok(layout.math.length>0);assert.ok(layout.math.every(m=>m.mathml===1&&m.nested===0),'Accessible balanced math');
   for(const math of layout.math.filter(m=>m.subscripts.length)) {
     for(const sub of math.subscripts) {assert.ok(parseFloat(sub.fontSize)<parseFloat(math.bases[0].fontSize));assert.ok(sub.y>math.bases[0].y);}
   }
   const accessibility=[];for(const f of await page.locator('.katex').all()) accessibility.push(await f.ariaSnapshot());
   assert.ok(accessibility.every(s=>s.includes('math')));
   if(reducedMotion==='reduce')assert.ok(layout.animations.every(x=>x==='none'));
   if(width===390&&theme==='light'&&reducedMotion==='reduce') {
     await page.locator('#tab-lib-here').click();await page.locator('#section-document-library').screenshot({path:path.join(out,'library-here-390-light.png')});
     await page.locator('#tab-lib-elsewhere').click();await page.locator('#section-document-library').screenshot({path:path.join(out,'library-elsewhere-390-light.png')});
     await page.locator('#section-quiz-taking').screenshot({path:path.join(out,'quiz-taking-390-light.png')});
   }
   report.configurations.push({width,theme,reducedMotion,filters,scopeBoundary:{enabledAt5:true,disabledAt6:true,recoveredAt5:true},layout,accessibility,pageErrors,consoleErrors});
   assert.deepEqual(pageErrors,[]);await context.close();
  }
  for(const name of ['old-filter-on-current-fixtures.html','mutant-filter.html']) {
   const context=await browser.newContext({viewport:{width:1280,height:900}});await context.route(/^https?:\/\//,r=>r.abort());
   const page=await context.newPage();await page.goto(pathToFileURL(path.join(out,'design/preview',name)).href);
   const filters=await inspectFilters(page);assert.ok(filters.filter(r=>r.group!=='all').every(r=>r.assertionFailure),'Both invalid filters must be caught by observable record assertions');
   report.controls.push({variant:name,filters});await context.close();
  }
  await fs.writeFile(path.join(out,'browser-probe.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({configurations:report.configurations.length,controls:report.controls.map(x=>({variant:x.variant,failures:x.filters.filter(r=>r.assertionFailure).length})),passed:true}));
 } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
