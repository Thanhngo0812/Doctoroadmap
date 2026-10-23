const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const shared='C:/Users/ngoco/Desktop/Doctoroadmap';
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(shared,'.tmp/w01-browsers');
const {chromium}=require(path.join(shared,'.tmp/w01-browser-tools/node_modules/playwright'));
const wt=path.join(shared,'tmp/w24-figma-evidence');
const out=path.join(__dirname,'design-browser');
(async()=>{
 await fs.mkdir(out,{recursive:true});
 const browser=await chromium.launch();
 const observations=[];
 try{
  for(const width of [390,768,1280]) for(const theme of ['light','dark']) for(const reducedMotion of ['no-preference','reduce']){
   const context=await browser.newContext({viewport:{width,height:900},reducedMotion});
   const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.goto(pathToFileURL(path.join(wt,'design/preview/w08_lecture_screens.html')).href);
   if(theme==='dark') await page.locator('.theme-toggle-btn').click();
   await page.evaluate(()=>document.fonts.ready);
   const row=await page.evaluate(()=>{
    const ready=document.querySelector('#section-lecture-ready');
    const waiting=document.querySelector('#section-lecture-waiting-first-chunk');
    const fatal=document.querySelector('#section-lecture-fatal-error');
    const spinner=waiting.querySelector('[style*="animation: spin"]');
    const sr=spinner.getBoundingClientRect(), style=getComputedStyle(spinner);
    return {theme:document.documentElement.dataset.theme,overflow:document.documentElement.scrollWidth>innerWidth,
      katexNodes:ready.querySelectorAll('.katex').length,rawMath:ready.innerText.match(/\$[^$]+\$/g),
      fatalActions:[...fatal.querySelectorAll('button,a')].map(e=>e.innerText),
      fatalHasRetry:[...fatal.querySelectorAll('button,a')].some(e=>/thử lại/i.test(e.innerText)),
      earlyHasRetry:!!document.querySelector('#btn-retry-lecture-early'),
      spinner:{width:sr.width,height:sr.height,animationName:style.animationName,animationDuration:style.animationDuration},
      selfCheckFolded:!document.querySelector('#details-self-check')?.open,
      images:[...waiting.querySelectorAll('img')].map(e=>({src:e.getAttribute('src'),width:e.width,height:e.height}))};
   });
   assert.equal(row.theme,theme);assert.equal(row.katexNodes,0);assert.ok(row.rawMath.length>0);
   assert.equal(row.fatalHasRetry,false);assert.equal(row.earlyHasRetry,true);
   if(width!==768 && reducedMotion==='no-preference'){
    for(const [name,id] of [['ready','section-lecture-ready'],['fatal','section-lecture-fatal-error'],['waiting','section-lecture-waiting-first-chunk']]){
     await page.locator('#'+id).screenshot({path:path.join(out,`${name}-${width}-${theme}.png`)});
    }
   }
   observations.push({width,reducedMotion,...row,pageErrors:errors});
   await context.close();
  }
  const page=await browser.newPage();
  await page.goto(pathToFileURL(path.join(wt,'design/preview/w09_chat_screens.html')).href);
  const chat=await page.evaluate(()=>({usage:document.querySelector('#badge-chat-usage')?.textContent,
    empty:!!document.querySelector('#section-chat-empty'),toolAnchor:!!document.querySelector('#text-tool-action'),
    rawTools:/vector_search_harrison|30 lượt\/ngày/.test(document.body.innerText)}));
  await page.goto(pathToFileURL(path.join(wt,'design/preview/w11_course_management_screens.html')).href);
  const management=await page.evaluate(()=>Object.fromEntries(['section-invite-email','section-pending-invitations','section-danger-zone','btn-delete-course','btn-delete-course-permanent'].map(id=>[id,!!document.getElementById(id)])));
  const result={diagnosticOnly:true,productAccepted:false,workerCommit:'f292f18',browserVersion:browser.version(),observations,chat,management};
  await fs.writeFile(path.join(out,'observations.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({diagnosticOnly:true,configurations:observations.length,katexNodes:0,fatalHasRetry:false,chat,management}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
