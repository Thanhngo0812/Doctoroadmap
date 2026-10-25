const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const root='C:/Users/ngoco/Desktop/Doctoroadmap',wt=path.join(root,'tmp/coord-r5-acceptance-20261025');
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(root,'.tmp/w01-browsers');
const {chromium}=require(path.join(root,'.tmp/w01-browser-tools/node_modules/playwright'));
const out=path.join(__dirname,'design-browser');
(async()=>{
 await fs.mkdir(out,{recursive:true});const browser=await chromium.launch();const rows=[];
 try{
  for(const width of [390,768,1280])for(const theme of ['light','dark'])for(const reducedMotion of ['no-preference','reduce']){
   const context=await browser.newContext({viewport:{width,height:900},reducedMotion});const page=await context.newPage();
   for(const ticket of ['w08','w09']){
    const name=ticket==='w08'?'w08_lecture_screens.html':'w09_chat_screens.html';
    await page.goto(pathToFileURL(path.join(wt,'design/preview',name)).href);
    if(theme==='dark')await page.locator('.theme-toggle-btn').click();
    await page.evaluate(()=>document.fonts.ready);
    const row=await page.evaluate(()=>{
     const bounds=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,width:r.width,height:r.height,font:s.font,fontSize:s.fontSize,position:s.position,verticalAlign:s.verticalAlign,display:s.display};};
     const img=document.getElementById('waiting-character-96px');
     return {overflow:document.documentElement.scrollWidth>innerWidth,
      math:[...document.querySelectorAll('.katex')].map(e=>({text:e.textContent,ariaLabel:e.getAttribute('aria-label'),mathml:e.querySelectorAll('math').length,
       nested:e.querySelectorAll('.katex').length,hiddenHtml:[...e.querySelectorAll('.katex-html')].map(n=>n.getAttribute('aria-hidden')),
       outer:bounds(e),bases:[...e.querySelectorAll('.mathnormal')].map(bounds),subscripts:[...e.querySelectorAll('.msub')].map(bounds)})),
      waiting:img?{...bounds(img),src:img.currentSrc,naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight}:null,
      fatalRetry:!!document.getElementById('btn-retry-lecture-fatal'),earlyRetry:!!document.getElementById('btn-retry-lecture-early'),
      tailPromise:document.querySelector('#section-lecture-tail-error')?.innerText.includes('Tải lại bản đủ')??null};
    });
    const snapshots=[];
    for(const formula of await page.locator('.katex').all()) snapshots.push(await formula.ariaSnapshot());
    assert.ok(row.math.length>0);assert.equal(row.overflow,false);
    assert.ok(row.math.every(m=>m.nested===0 && m.mathml===1 && m.ariaLabel?.trim()),'accessible balanced math');
    assert.ok(snapshots.every(s=>s.includes('math') && s.trim()),'real accessibility tree exposes math');
    if(ticket==='w09') {
      assert.ok(row.math[0].subscripts.length>0);
      const base=row.math[0].bases[0], sub=row.math[0].subscripts[0];
      assert.ok(parseFloat(sub.fontSize)<parseFloat(base.fontSize));
      assert.ok(sub.y>base.y,'subscript physically below base');
    }
    if(ticket==='w08'){assert.equal(row.fatalRetry,true);assert.equal(row.earlyRetry,true);assert.equal(row.waiting.naturalWidth>0,true);}
    rows.push({ticket,width,theme,reducedMotion,...row,mathAccessibilitySnapshots:snapshots});
    if([390,1280].includes(width)&&theme==='light'&&reducedMotion==='no-preference'){
     if(ticket==='w08'){
      await page.locator('#section-lecture-ready').screenshot({path:path.join(out,`w08-ready-${width}.png`)});
      await page.locator('#section-lecture-waiting-first-chunk').screenshot({path:path.join(out,`w08-waiting-${width}.png`)});
     }else await page.locator('#section-chat-active').screenshot({path:path.join(out,`w09-active-${width}.png`)});
    }
   }
   await context.close();
  }
  await fs.writeFile(path.join(out,'observations.json'),JSON.stringify({diagnosticOnly:false,workerCommit:'aa387f3',browserVersion:browser.version(),rows},null,2)+'\n');
  console.log(JSON.stringify({configurations:12,pages:rows.length,emptyMathSnapshots:rows.every(r=>r.mathAccessibilitySnapshots.every(s=>!s.trim())),
    w08NestedMath:rows.filter(r=>r.ticket==='w08').map(r=>r.math[0].nested),w09SubscriptSizes:rows.filter(r=>r.ticket==='w09').map(r=>[r.math[0].bases[0].fontSize,r.math[0].subscripts[0].fontSize])}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
