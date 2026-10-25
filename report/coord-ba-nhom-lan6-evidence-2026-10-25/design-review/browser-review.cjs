const fs=require('node:fs/promises'),path=require('node:path'),{pathToFileURL}=require('node:url');
const root='C:/Users/ngoco/Desktop/Doctoroadmap',out=__dirname;
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(root,'.tmp/w01-browsers');
const {chromium}=require(path.join(root,'.tmp/w01-browser-tools/node_modules/playwright'));
(async()=>{const browser=await chromium.launch(),rows=[];try{
for(const width of [390,768,1280])for(const theme of ['light','dark'])for(const reducedMotion of ['no-preference','reduce']){
const ctx=await browser.newContext({viewport:{width,height:900},reducedMotion});
await ctx.route(/^https?:\/\//,route=>route.abort());
const page=await ctx.newPage(),errors=[],consoleMsgs=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(['error','warning'].includes(m.type()))consoleMsgs.push(m.text())});
await page.goto(pathToFileURL(path.join(out,'design/preview/w10_quiz_screens.html')).href);if(theme==='dark')await page.locator('#theme-toggle-btn').click();
await page.evaluate(()=>document.fonts.ready);
const result=await page.evaluate(()=>{const bounds=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,font:getComputedStyle(e).fontSize}};return{width:innerWidth,scrollWidth:document.documentElement.scrollWidth,sections:[...document.querySelectorAll('main>section')].map(e=>({id:e.id,...bounds(e),scrollWidth:e.scrollWidth})),overflows:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1}).map(e=>({tag:e.tagName,id:e.id,cls:e.className,...bounds(e)})).slice(0,20),math:[...document.querySelectorAll('.katex')].map(e=>({aria:e.getAttribute('aria-label'),nested:e.querySelectorAll('.katex').length,subscripts:[...e.querySelectorAll('.msub')].map(bounds),bases:[...e.querySelectorAll('.mathnormal')].map(bounds)})),spin:getComputedStyle(document.querySelector('[style*="animation: spin"]')).animationName,skeleton:getComputedStyle(document.querySelector('.skeleton-line')).animationName};});
result.mathSnapshots=[];for(const f of await page.locator('.katex').all())result.mathSnapshots.push(await f.ariaSnapshot());
const counts=[];for(const tab of ['here','elsewhere','all']){await page.locator('#tab-lib-'+tab).click();counts.push({tab,visibleCards:await page.locator('.doc-card:visible').count(),labels:await page.locator('.doc-card:visible .badge').allTextContents()});}
for(const c of await page.locator('.module-chips input').all())await c.check();
result.scopeSix={warningVisible:await page.locator('#scope-warning-box').isVisible(),counter:await page.locator('#scope-count-indicator').innerText(),createDisabled:await page.locator('#btn-create-document').isDisabled()};
result.libraryTabs=counts;result.errors=errors;result.console=consoleMsgs;rows.push({theme,reducedMotion,...result});
if(theme==='light'&&reducedMotion==='no-preference'&&[390,1280].includes(width)){for(const [name,id] of [['create','section-document-create'],['library','section-document-library'],['taking','section-quiz-taking']])await page.locator('#'+id).screenshot({path:path.join(out,'w10-'+name+'-'+width+'.png')});}
await ctx.close();}
await fs.writeFile(path.join(out,'browser-observations.json'),JSON.stringify({pin:'0b5993e47a01b45bc2f645741aa38af42f99c5f4',browser:browser.version(),externalNetwork:'blocked; typography measured with available fallback font, not Be Vietnam Pro acceptance',rows},null,2));console.log(JSON.stringify(rows.map(r=>({width:r.width,theme:r.theme,motion:r.reducedMotion,scrollWidth:r.scrollWidth,errors:r.errors,math:r.math.length,scope:r.scopeSix,tabs:r.libraryTabs.map(x=>[x.tab,x.visibleCards])}))));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
