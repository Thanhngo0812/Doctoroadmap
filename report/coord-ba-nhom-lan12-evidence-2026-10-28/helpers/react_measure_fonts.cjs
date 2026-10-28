const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root="C:/Users/ngoco/Desktop/Doctoroadmap",td="C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-tools-20261028";process.env.PLAYWRIGHT_BROWSERS_PATH=root+'/.tmp/w01-browsers';const {chromium}=require(root+'/.tmp/w01-browser-tools/node_modules/playwright');
async function metrics(page, selector) {
  return page.locator(selector).first().evaluate(el => {
    const cs = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    const color = value => {
      ctx.clearRect(0, 0, 1, 1);
      ctx.fillStyle = value;
      ctx.fillRect(0, 0, 1, 1);
      return [...ctx.getImageData(0, 0, 1, 1).data].map(v => v / 255);
    };
    const blend = (a, b) => a.slice(0, 3).map((v, i) => v * a[3] + b[i] * (1 - a[3])).concat(1);
    const lum = c => c.slice(0, 3).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)
      .reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
    const ancestors = [];
    for (let a = el; a; a = a.parentElement) ancestors.unshift(a);
    const bg = ancestors.reduce((b, a) => blend(color(getComputedStyle(a).backgroundColor), b), [1, 1, 1, 1]);
    const fg = color(cs.color);
    const ink = blend(fg, bg);
    const lumInk = lum(ink);
    const lumBg = lum(bg);
    const contrast = (Math.max(lumInk, lumBg) + 0.05) / (Math.min(lumInk, lumBg) + 0.05);

    return {
      text: el.textContent.trim().replace(/\s+/g, ' '),
      elementBoundingRect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      documentRect: { x: rect.x + scrollX, y: rect.y + scrollY, width: rect.width, height: rect.height },
      css: Object.fromEntries([
        'display', 'minHeight', 'padding', 'fontFamily', 'fontSize', 'fontWeight',
        'lineHeight', 'color', 'backgroundColor', 'borderRadius'
      ].map(k => [k, cs[k]])),
      effectiveBackgroundHex: '#' + bg.slice(0, 3).map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join(''),
      foregroundHex: '#' + fg.slice(0, 3).map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join(''),
      contrast
    };
  });
}

async function fontReceipt(page, selector) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { root: doc } = await cdp.send('DOM.getDocument');
  const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: doc.nodeId, selector });
  const platformFonts = (await cdp.send('CSS.getPlatformFontsForNode', { nodeId })).fonts;
  const docFonts = await page.evaluate(() => ({
    status: document.fonts.status,
    beVietnamCheck: document.fonts.check('16px "Be Vietnam Pro"'),
    faces: [...document.fonts].map(f => ({ family: f.family, status: f.status }))
  }));
  return { document: docFonts, platformFonts };
}


async function main(){const runtime=JSON.parse(fs.readFileSync(process.env.W10_RUNTIME,'utf8')),out=path.dirname(process.env.W10_RUNTIME),base=runtime.base;const browser=await chromium.launch();const context=await browser.newContext({viewport:{width:390,height:900},colorScheme:'light'});const page=await context.newPage();const report={source:runtime.sourceCommit,base,syntheticFixtures:true,externalProviderUsd:0,networkPolicy:'Local application plus Google font assets only',screens:[],http:[],pageErrors:[]};page.on('pageerror',e=>report.pageErrors.push(e.message));page.on('response',r=>{if(r.url().includes('/api/v1/'))report.http.push({url:new URL(r.url()).pathname,status:r.status()});});await context.route(/^https?:/,route=>(route.request().url().startsWith(base+'/')||['fonts.googleapis.com','fonts.gstatic.com'].includes(new URL(route.request().url()).hostname))?route.continue():route.abort());
async function snap(name,selector){const loc=page.locator(selector).first();await loc.scrollIntoViewIfNeeded();await page.evaluate(()=>document.fonts.ready);const m=await metrics(page,selector);const file=path.join(out,name+'.png');await loc.screenshot({path:file});const b=fs.readFileSync(file);return {path:path.basename(file),sha256:require('node:crypto').createHash('sha256').update(b).digest('hex'),decodedPngDimensions:[b.readUInt32BE(16),b.readUInt32BE(20)],metrics:m,url:page.url(),viewport:page.viewportSize(),theme:await page.locator('html').getAttribute('data-theme'),font:await fontReceipt(page,selector)};}
try{await page.goto(base+'/dang-nhap');await page.getByLabel('Email',{exact:true}).fill('learner-w10@example.invalid');await page.getByLabel('Mật khẩu',{exact:true}).fill('W10 isolated browser passphrase!');await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await page.waitForURL(base+'/khoa-hoc');const moduleUrl=base+'/khoa-hoc/'+runtime.courseId+'/module/'+runtime.moduleA;await page.goto(moduleUrl);await page.locator('.content-library-list > li').nth(1).waitFor();assert.equal(await page.locator('.content-library-list > li').count(),2);report.library={...(await snap('current-w10-library-here-390-light','.content-library')),tab:await metrics(page,'.content-tabs button'),card:await metrics(page,'.content-library-list a'),usageBlocks:await page.locator('.content-library .usage-limits').count()};report.library.tabFont=await fontReceipt(page,'.content-tabs button');report.library.cardFont=await fontReceipt(page,'.content-library-list a strong');report.screens.push(report.library.path);
await page.setViewportSize({width:1280,height:900});await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});if(await page.locator('html').getAttribute('data-theme')!=='dark')await page.getByRole('button',{name:'Bật chế độ tối'}).click();await page.goto(moduleUrl+'/khai-niem/'+encodeURIComponent(runtime.nodeId));await page.locator('.lecture-self-check').waitFor({timeout:60000});await page.locator('.lecture-self-check details:not([open])').waitFor();report.selfCheckFolded={...(await snap('current-w08-self-check-folded-1280-dark-reduced','.lecture-self-check')),summary:await metrics(page,'.lecture-self-check summary'),heading:await metrics(page,'.lecture-self-check h2')};report.selfCheckFolded.summaryFont=await fontReceipt(page,'.lecture-self-check summary');report.selfCheckFolded.headingFont=await fontReceipt(page,'.lecture-self-check h2');report.screens.push(report.selfCheckFolded.path);await page.locator('.lecture-self-check summary').click();report.selfCheckOpen={...(await snap('current-w08-self-check-open-1280-dark-reduced','.lecture-self-check')),summary:await metrics(page,'.lecture-self-check summary')};report.screens.push(report.selfCheckOpen.path);assert.equal(report.pageErrors.length,0);fs.writeFileSync(path.join(out,'current-react-metrics.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({screens:report.screens,libraryCard:report.library.card.elementBoundingRect,cardPadding:report.library.card.css.padding,selfSummary:report.selfCheckFolded.summary.elementBoundingRect}));}finally{fs.writeFileSync(path.join(out,'current-react-metrics-partial.json'),JSON.stringify(report,null,2));await context.close();await browser.close();}}main().catch(e=>{console.error(e);process.exitCode=1;});
