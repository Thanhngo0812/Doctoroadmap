const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));
const worker = path.join(root, 'tmp/w23-paired-web-evidence');
const output = { network: 'All HTTP(S) requests aborted; only local file inputs; no product runtime', cases: [] };
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

async function metrics(page, selector) {
  return page.locator(selector).first().evaluate(el => {
    const cs = getComputedStyle(el), rect = el.getBoundingClientRect();
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    const color = value => { ctx.clearRect(0,0,1,1); ctx.fillStyle = value; ctx.fillRect(0,0,1,1); return [...ctx.getImageData(0,0,1,1).data].map(v=>v/255); };
    const blend = (a,b) => a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3])).concat(1);
    const lum = c => c.slice(0,3).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
    const ancestors = []; for(let a=el;a;a=a.parentElement) ancestors.unshift(a);
    const bg = ancestors.reduce((b,a)=>blend(color(getComputedStyle(a).backgroundColor),b),[1,1,1,1]);
    const fg = color(cs.color), ink = blend(fg,bg);
    return { text: el.textContent.trim(), rect: {x:rect.x,y:rect.y,width:rect.width,height:rect.height}, documentRect: {x:rect.x+scrollX,y:rect.y+scrollY,width:rect.width,height:rect.height},
      css: Object.fromEntries(['display','minHeight','padding','fontFamily','fontSize','fontWeight','lineHeight','color','backgroundColor','borderRadius'].map(k=>[k,cs[k]])),
      effectiveBackground: bg, foreground:fg, contrast: (Math.max(lum(ink),lum(bg))+.05)/(Math.min(lum(ink),lum(bg))+.05) };
  });
}
async function fontReceipt(page, selector) {
  const cdp=await page.context().newCDPSession(page); await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
  const {root:doc}=await cdp.send('DOM.getDocument');
  const {nodeId}=await cdp.send('DOM.querySelector',{nodeId:doc.nodeId,selector});
  return { document: await page.evaluate(()=>({ status:document.fonts.status, beVietnamCheck:document.fonts.check('16px "Be Vietnam Pro"'), faces:[...document.fonts].map(f=>({family:f.family,status:f.status})) })), platformFonts: (await cdp.send('CSS.getPlatformFontsForNode',{nodeId})).fonts };
}
async function capture(page, locator, name) {
  const file=path.join(__dirname,name); await locator.screenshot({path:file});
  return {file:name,sha256:hash(file)};
}
(async()=>{
  const browser=await chromium.launch(); output.browser=browser.version();
  try {
    for (const w of ['w08','w10']) {
      const context=await browser.newContext({viewport:{width:w==='w08'?1280:390,height:900},reducedMotion:w==='w08'?'reduce':'no-preference',colorScheme:w==='w08'?'dark':'light'});
      const blocked=[];
      await context.route(/^https?:/,route=>{blocked.push(route.request().url());return route.abort();});
      const page=await context.newPage();
      const source=path.join(worker,'design/preview',w==='w08'?'w08_lecture_screens.html':'w10_quiz_screens.html');
      await page.goto('file:///'+source.replaceAll('\\','/')); await page.evaluate(()=>document.fonts.ready);
      if(w==='w08') await page.locator('#theme-toggle-btn').click();
      else await page.locator('#tab-lib-here').click();
      await page.waitForTimeout(350);
      const row={case:w,url:page.url(),sourceRawSha256:hash(source),viewport:page.viewportSize(),theme:await page.locator('html').getAttribute('data-theme'),motion:await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),deviceScaleFactor:await page.evaluate(()=>devicePixelRatio),blocked};
      if(w==='w08') {
        const detail=page.locator('#details-self-check'); await detail.scrollIntoViewIfNeeded();
        row.folded={detail:await metrics(page,'#details-self-check'),summary:await metrics(page,'#details-self-check summary'),font:await fontReceipt(page,'#details-self-check summary')};
        row.folded.image=await capture(page,detail,'offline-html-w08-folded.png');
        await detail.scrollIntoViewIfNeeded();
        const box=await detail.boundingBox();
        await page.mouse.click(box.x+box.width/2,box.y+8);
        row.paddingClickOpened=await detail.evaluate(e=>e.open);
        await detail.locator('summary').click();
        row.summaryClickOpened=await detail.evaluate(e=>e.open);
        row.open={detail:await metrics(page,'#details-self-check'),summary:await metrics(page,'#details-self-check summary')};
        row.open.image=await capture(page,detail,'offline-html-w08-open.png');
        assert.equal(row.paddingClickOpened,false,'outer padding is not the disclosure target');
        assert.equal(row.summaryClickOpened,true,'summary itself toggles');
        assert.ok(row.folded.summary.rect.height<44,'HTML summary target is below claimed 44px');
      } else {
        const section=page.locator('#section-document-library'); await section.scrollIntoViewIfNeeded();
        row.section=await metrics(page,'#section-document-library'); row.tab=await metrics(page,'#tab-lib-here'); row.card=await metrics(page,'.doc-card[data-group="here"]');
        row.font=await fontReceipt(page,'#tab-lib-here');
        row.image=await capture(page,section,'offline-html-w10-here.png');
        row.tabs=await page.locator('#section-document-library .filter-tab').allTextContents();
        row.visibleGroups=await page.locator('#section-document-library .doc-card:visible').evaluateAll(es=>es.map(e=>({origin:e.dataset.origin,group:e.dataset.group,title:e.querySelector('.doc-title')?.textContent})));
      }
      output.cases.push(row); await context.close();
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(__dirname,'html-probe.json'),JSON.stringify(output,null,2));
  console.log(JSON.stringify({browser:output.browser,cases:output.cases.map(r=>({case:r.case,font:r.font||r.folded.font,target:r.tab||r.folded.summary,paddingClickOpened:r.paddingClickOpened,summaryClickOpened:r.summaryClickOpened}))},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
