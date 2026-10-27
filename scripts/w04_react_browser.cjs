const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),shared=path.resolve(root,'../..');
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(shared,'.tmp/w01-browsers');
const {chromium}=require(path.join(shared,'.tmp/w01-browser-tools/node_modules/playwright'));
const {AxeBuilder}=require(path.join(shared,'.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const runtimePath=process.env.W04_REACT_RUNTIME,out=path.dirname(runtimePath);
const P0='W04 synthetic original passphrase!',P1='W04 synthetic replacement passphrase!';
const audit={configurations:[],screens:[],accessibility:[],http:[],pageErrors:[],console:[],assertions:[],sql:[]};
let stage='bootstrap';
const scrub=value=>Array.isArray(value)?value.map(scrub):value&&typeof value==='object'?Object.fromEntries(Object.entries(value).map(([k,v])=>[k,/password|csrf|token|cookie/i.test(k)?'[REDACTED]':scrub(v)])):value;
const safeText=text=>[P0,P1,'Wrong W04 private passphrase!'].reduce((s,v)=>s.split(v).join('[REDACTED]'),text);
async function main(){
 const runtime=JSON.parse(await fs.readFile(runtimePath,'utf8')),base=runtime.base,api=base+'/api/v1';
 const browser=await chromium.launch(),contexts=[],pending=[];let holdGet=null,holdPatch=null;
 async function userPage(name){
  const context=await browser.newContext({viewport:{width:1280,height:900},recordVideo:{dir:path.join(root,'tmp/w04-react-video'),size:{width:1280,height:900}}});
  await context.exposeBinding('__w04Hold',(_,method)=>{const held=method==='GET'?holdGet:holdPatch;if(held){held.ready=true;return held.promise;}});
  await context.addInitScript(()=>{const original=window.fetch.bind(window);window.fetch=async(...args)=>{const response=await original(...args);if(response.url.endsWith('/api/v1/me'))await window.__w04Hold(args[1]?.method??'GET');return response;};});
  const page=await context.newPage();contexts.push({context,page,name});
  page.on('pageerror',e=>audit.pageErrors.push({stage,message:safeText(e.message)}));
  page.on('console',m=>{if(m.type()==='error')audit.console.push({stage,message:safeText(m.text())});});
  page.on('response',response=>{if(!response.url().startsWith(api))return;const when=stage;const job=(async()=>{const type=response.headers()['content-type']??'';if(!type.includes('json'))return;const body=scrub(await response.json());audit.http.push({stage:when,path:new URL(response.url()).pathname,status:response.status(),method:response.request().method(),body});})();pending.push(job);void job.catch(()=>{});});
  return page;
 }
 const a=await userPage('a'),b=await userPage('b'),learner=a;
 const observer=await browser.newContext();
 async function login(page,email='a-w04@example.invalid',password=P0){await page.goto(base+'/dang-nhap');await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Mật khẩu',{exact:true}).fill(password);await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await page.waitForURL(base+'/khoa-hoc');}
 const responseJson=async(response,label)=>{const body=await response.json();audit.http.push({stage:label,path:new URL(response.url()).pathname,status:response.status(),body:scrub(body)});return body;};
 let releaseGet,releasePatch;
 try{
  const observerLogin=await observer.request.post(api+'/auth/login',{headers:{Origin:base},data:{email:'other-w04@example.invalid',password:P0}});assert.equal(observerLogin.status(),200);
  const probe=async label=>{const response=await observer.request.get(base+runtime.controlPath);assert.equal(response.status(),200);const value=await response.json();audit.sql.push({stage:label,...value});return value;};
  const count=(row,id)=>row.sessions.find(s=>s.account_id===id)?.count??0;
  await login(a);await login(b);await a.goto(base+'/tai-khoan');await a.getByLabel('Tên hiển thị').waitFor();
    async function settled() {
      await learner.evaluate(() => Promise.all(document.getAnimations().filter(a => a.effect?.getTiming().iterations !== Infinity).map(a => a.finished.catch(() => {}))));
      await learner.evaluate(() => document.fonts.ready);
    }
    async function capture(name, axe = false) {
      await settled();
      const width = learner.viewportSize().width;
      const theme = await learner.locator('html').getAttribute('data-theme');
      const reduced = await learner.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
      const file = name + '-' + width + '-' + theme + (reduced ? '-reduced' : '') + '.png';
      const layout = await learner.evaluate(() => {
        const region = document.querySelector('dialog[open]') || document.querySelector('.profile-page') || document.querySelector('.content-page') || document.querySelector('.content-library');
        const targets = [...region.querySelectorAll('button:not(:disabled),a[href],select,textarea,input:not(:disabled),label:has(input)')]
          .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
          .map(e => ({ label: e.getAttribute('aria-label') || e.textContent.trim().slice(0, 70), w: e.getBoundingClientRect().width, h: e.getBoundingClientRect().height }))
          .filter(row => row.w < 43.5 || row.h < 43.5);
        return { overflow: document.documentElement.scrollWidth > innerWidth + 1, targets };
      });
      assert.equal(layout.overflow, false, name + ' horizontal overflow');
      assert.deepEqual(layout.targets, [], name + ' 44px targets');
      if (width < 1280 && name.startsWith('library-')) await learner.locator('.content-library').evaluate(e => scrollTo({ top: scrollY + e.getBoundingClientRect().top - document.querySelector('.courses-header').getBoundingClientRect().height - 16, behavior: 'instant' }));
      else await learner.evaluate(() => scrollTo({ top: 0, behavior: 'instant' }));
      await learner.screenshot({ path: path.join(out, file), fullPage: !name.startsWith('logout-confirm') }); audit.screens.push({ file, width, theme, reduced, layout });
      if (axe) {
        const result = await new AxeBuilder({ page: learner }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
        const row = { file, scope: 'document', violations: result.violations, incomplete: result.incomplete, passes: result.passes.length };
        audit.accessibility.push(row); assert.deepEqual(result.violations, [], name + ' Axe');
        const manual = [];
        for (const finding of result.incomplete) {
          assert.equal(finding.id, 'color-contrast');
          const measured = await mathContrast(learner, finding.nodes);
          assertMathContrast(measured); manual.push(...measured);
        }
        row.manualContrast = manual;
        if (manual.length && !audit.contrastGuard) {
          assert.throws(() => assertMathContrast(manual.map(x => ({ ...x, contrast: 1 }))));
          assert.throws(() => assertMathContrast(manual.map(x => ({ ...x, unobscured: false }))));
          audit.contrastGuard = { lowContrastRejected: true, obscuredRejected: true };
        }
      }
    }
    async function mathContrast(page, nodes) {
      return page.evaluate(targets => {
        const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1;
        const context = canvas.getContext('2d', { willReadFrequently: true });
        const color = value => {
          context.clearRect(0, 0, 1, 1); context.fillStyle = value; context.fillRect(0, 0, 1, 1);
          return [...context.getImageData(0, 0, 1, 1).data].map(value => value / 255);
        };
        const blend = (front, back) => front.slice(0, 3).map((value, index) => value * front[3] + back[index] * (1 - front[3])).concat(1);
        const luminance = rgb => rgb.slice(0, 3).map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
          .reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0);
        return targets.map(selector => {
          const element = document.querySelector(selector);
          if (!element?.closest('.katex,.profile-page,.content-library,.content-page,.profile-dialog,.learning-chat-panel')) return { selector, eligible: false };
          element.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
          let box = element.getBoundingClientRect();
          let left = Math.max(box.left, 0), right = Math.min(box.right, innerWidth);
          let top = Math.max(box.top, 0), bottom = Math.min(box.bottom, innerHeight);
          const scroller = element.closest('.learning-chat-messages');
          if (scroller) { const r = scroller.getBoundingClientRect(); top = Math.max(top, r.top); bottom = Math.min(bottom, r.bottom); }
          const hit = right > left && bottom > top ? document.elementFromPoint((left + right) / 2, (top + bottom) / 2) : null;
          // KaTeX's positioned fraction wrappers overlap inside one mathematical expression.
          const math = element.closest('.katex');
          const unobscured = Boolean(hit && (element.contains(hit) || hit.contains(element) || (math && hit.closest('.katex') === math)));
          const ancestors = [];
          for (let current = element; current; current = current.parentElement) ancestors.push(current);
          let background = [1, 1, 1, 1];
          for (const ancestor of ancestors.reverse()) background = blend(color(getComputedStyle(ancestor).backgroundColor), background);
          const foreground = color(getComputedStyle(element).color);
          foreground[3] *= ancestors.reduce((opacity, ancestor) => opacity * Number(getComputedStyle(ancestor).opacity), 1);
          const ink = blend(foreground, background), light = luminance(ink), ground = luminance(background);
          return { selector, eligible: true, unobscured, hitTag: hit?.tagName, hitClass: hit?.getAttribute('class'), foreground, background, contrast: (Math.max(light, ground) + .05) / (Math.min(light, ground) + .05) };
        });
      }, nodes.map(node => node.target.length === 1 ? node.target[0] : '__unsupported_shadow_target__'));
    }
    function assertMathContrast(rows) {
      for (const row of rows) assert.ok(row.eligible && row.unobscured && row.contrast >= 4.5, `Visible text contrast must reach 4.5:1: ${JSON.stringify(row)}`);
    }



 const smoke=process.env.W04_REACT_SMOKE==='1';let first=true;
 for(const width of(smoke?[1280]:[390,768,1280]))for(const theme of(smoke?['light']:['light','dark']))for(const reduced of(smoke?[false]:[false,true])){
  stage='profile:'+width+':'+theme+':'+reduced;audit.configurations.push({width,theme,reduced});await a.setViewportSize({width,height:900});await a.emulateMedia({colorScheme:theme,reducedMotion:reduced?'reduce':'no-preference'});
  await a.goto(base+'/tai-khoan');await a.getByLabel('Tên hiển thị').waitFor();if(await a.locator('html').getAttribute('data-theme')!==theme)await a.getByRole('button',{name:theme==='dark'?'Bật chế độ tối':'Bật chế độ sáng'}).click();
  await capture('profile',true);
  const newName='Nguyễn An '+width+' '+theme;await a.getByLabel('Tên hiển thị').fill('  '+newName+'  ');
  if(first){holdPatch={ready:false,promise:new Promise(r=>{releasePatch=r;})};}
  await a.getByRole('button',{name:'Lưu thay đổi',exact:true}).click();
  if(first){await a.getByRole('button',{name:'Đang lưu…'}).waitFor();await capture('profile-saving',true);assert.equal(await a.getByLabel('Tên hiển thị').isDisabled(),true);releasePatch();holdPatch=null;}
  await a.getByText('Đã lưu thông tin tài khoản.',{exact:true}).waitFor();const saved=await probe('saved-name');assert.equal(saved.displayName,newName);
  if(reduced)assert.equal(await a.locator('.profile-feedback.success').evaluate(e=>getComputedStyle(e).animationName),'none');
  await a.getByLabel('Mật khẩu hiện tại',{exact:true}).fill('Wrong W04 private passphrase!');await a.getByLabel('Mật khẩu mới',{exact:true}).fill(P1);await a.getByLabel('Xác nhận mật khẩu mới',{exact:true}).fill(P1);await a.getByRole('button',{name:'Đổi mật khẩu',exact:true}).click();
  await a.getByText('Mật khẩu hiện tại chưa đúng.',{exact:true}).waitFor();assert.equal(await a.getByLabel('Mật khẩu hiện tại',{exact:true}).getAttribute('aria-invalid'),'true');
  await a.getByLabel('Mật khẩu hiện tại',{exact:true}).focus();assert.equal(await a.getByLabel('Mật khẩu hiện tại',{exact:true}).evaluate(e=>getComputedStyle(e).outlineColor),await a.getByLabel('Mật khẩu hiện tại',{exact:true}).evaluate(e=>getComputedStyle(e).borderColor));
  await capture('password-invalid',true);const wrong=await probe('wrong-current');assert.equal(wrong.originalPasswordValid,true);assert.equal(wrong.replacementPasswordValid,false);assert.equal(count(wrong,runtime.accountId),2);
  await a.getByRole('button',{name:'Đăng xuất khỏi mọi thiết bị',exact:true}).click();await a.getByRole('dialog',{name:'Đăng xuất khỏi mọi thiết bị?'}).waitFor();await capture('logout-confirm',true);
  assert.equal(await a.getByRole('button',{name:'Giữ đăng nhập'}).evaluate(e=>e===document.activeElement),true);await a.keyboard.press('Escape');assert.equal(await a.getByRole('dialog').count(),0);
  assert.equal(await a.getByRole('button',{name:'Đăng xuất khỏi mọi thiết bị',exact:true}).evaluate(e=>e===document.activeElement),true);first=false;
 }
 stage='server-rejections';const identity=await(await a.request.get(api+'/me')).json(),headers={Origin:base,'X-CSRF-Token':identity.csrf_token};const before=await probe('before-invalid');
 let rejected=await a.request.patch(api+'/me',{headers,data:{display_name:'x'.repeat(61)}});assert.equal(rejected.status(),422);await responseJson(rejected,'invalid-name-http');
 rejected=await a.request.patch(api+'/me',{headers:{Origin:base},data:{display_name:'Should not save'}});assert.equal(rejected.status(),403);await responseJson(rejected,'csrf-http');
 const after=await probe('after-invalid');assert.equal(after.displayName,before.displayName);assert.equal(after.originalPasswordValid,true);assert.equal(count(after,runtime.accountId),2);
 stage='password-change';await a.getByLabel('Mật khẩu hiện tại',{exact:true}).fill(P0);await a.getByRole('button',{name:'Đổi mật khẩu',exact:true}).click();await a.getByText('Đã đổi mật khẩu. Các phiên đăng nhập khác đã được đăng xuất.',{exact:true}).waitFor();
 for(const name of ['Mật khẩu hiện tại','Mật khẩu mới','Xác nhận mật khẩu mới'])assert.equal(await a.getByLabel(name,{exact:true}).inputValue(),'');
 await capture('password-success',true);const changed=await probe('password-changed');assert.equal(changed.originalPasswordValid,false);assert.equal(changed.replacementPasswordValid,true);assert.equal(count(changed,runtime.accountId),1);assert.equal(count(changed,runtime.otherId),1);
 assert.equal((await a.request.get(api+'/me')).status(),200);assert.equal((await b.request.get(api+'/me')).status(),401);
 const oldLogin=await b.request.post(api+'/auth/login',{headers:{Origin:base},data:{email:'a-w04@example.invalid',password:P0}});assert.equal(oldLogin.status(),401);await responseJson(oldLogin,'old-password-denied');
 await login(b,'a-w04@example.invalid',P1);assert.equal(count(await probe('new-password-login'),runtime.accountId),2);
// Taste inspection uses a design-only copy of this real authenticated DOM.
    let snapshot = (await learner.evaluate(() => {
      const clone = document.documentElement.cloneNode(true);
      const source = [...document.querySelectorAll('input[type=checkbox]')];
      [...clone.querySelectorAll('input[type=checkbox]')].forEach((input, index) => input.toggleAttribute('checked', source[index].checked));
      clone.querySelectorAll('.profile-password input').forEach(input => { input.setAttribute('value',''); input.value=''; });
      return '<!doctype html>' + clone.outerHTML;
    })).replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
    for (const match of [...snapshot.matchAll(/<link\b[^>]*rel=["']stylesheet["'][^>]*href=["']([^"']+)["'][^>]*>/gi)]) {
      const cssUrl = new URL(match[1], base).href;
      let css = (await (await learner.request.get(cssUrl)).text()).replace(/url\((['"]?)([^)'"\s]+)\1\)/g,
        (full, delimiter, value) => value.startsWith('data:') ? full : `url("${new URL(value, cssUrl).href}")`);
      // A file:// design snapshot has a different origin. Embed its fonts, not a CORS-blocked localhost URL.
      for (const font of [...new Set([...css.matchAll(/url\("([^"()]+\.(?:woff2?|ttf))"\)/g)].map(match => match[1]))]) {
        const response = await learner.request.get(font);
        assert.equal(response.status(), 200);
        const type = font.endsWith('.woff2') ? 'font/woff2' : font.endsWith('.woff') ? 'font/woff' : 'font/ttf';
        css = css.split(font).join(`data:${type};base64,${Buffer.from(await response.body()).toString('base64')}`);
      }
      snapshot = snapshot.replace(match[0], `<style>${css}</style>`);
    }
    for (const match of [...snapshot.matchAll(/<img\b[^>]*src=["']([^"']*\/api\/v1\/[^"']+)["'][^>]*>/gi)]) {
      const response = await learner.request.get(new URL(match[1], base).href);
      const data = Buffer.from(await response.body()).toString('base64');
      snapshot = snapshot.replace(match[1], `data:image/webp;base64,${data}`);
    }
    const snapshotPath = path.join(root, 'tmp/w04-react-inspect.html');
    await fs.writeFile(snapshotPath, snapshot.replace(/<head([^>]*)>/i, `<head$1><base href="${base}/">`));
    await fs.mkdir(path.join(root, 'tmp/w04-react-taste-profiles'), { recursive: true });
    const inspected=spawnSync(process.execPath,[path.join(shared,'.agents/skills/design-taste-frontend/scripts/inspect.mjs'),snapshotPath,'--out',path.join(out,'taste-inspect'),'--widths','1280,768,390','--app','--json'],{cwd:root,encoding:'utf8',timeout:180000,env:{...process.env,TASTE_SKILL_TMP:path.join(root,'tmp/w04-react-taste-profiles')}});
    await fs.writeFile(path.join(out,'taste-inspector.log'),String(inspected.stdout??'')+String(inspected.stderr??''));
    audit.designInspection=JSON.parse(await fs.readFile(path.join(out,'taste-inspect/report.json'),'utf8'));assert.equal(audit.designInspection.findings.filter(x=>x.level==='FAIL').length,0);

 stage='stale-identity-and-logout-all';await a.goto(base+'/muc-dung');await a.getByRole('progressbar').waitFor({state:'attached'});
 holdGet={ready:false,promise:new Promise(r=>{releaseGet=r;})};await a.getByLabel(/Tài khoản của/).click();await a.getByRole('link',{name:'Tài khoản',exact:true}).click();await a.getByLabel('Tên hiển thị').waitFor();
 await a.getByRole('button',{name:'Đăng xuất khỏi mọi thiết bị',exact:true}).click();await a.getByRole('button',{name:'Xác nhận đăng xuất',exact:true}).click();await a.waitForURL(base+'/dang-nhap');assert.equal(await a.locator('.profile-page').count(),0);
 assert.equal((await a.request.get(api+'/me')).status(),401);assert.equal((await b.request.get(api+'/me')).status(),401);const all=await probe('logout-all');assert.equal(count(all,runtime.accountId),0);assert.equal(count(all,runtime.otherId),1);
 const currentGet=holdGet;holdGet=null;await login(a,'other-w04@example.invalid',P0);assert.equal(currentGet.ready,true);releaseGet();await a.getByLabel('Tài khoản của Bình').waitFor();assert.equal(await a.getByLabel(/Tài khoản của Nguyễn An/).count(),0);
 audit.sessionProof={passwordKeepsARevokesB:true,oldDeniedNewAccepted:true,logoutAllRevokesBoth:true,oldRefreshDoesNotResurrectA:true};
 const storage=await a.evaluate(()=>JSON.stringify({local:localStorage,session:sessionStorage,history:history.state,url:location.href}));assert.ok(![P0,P1].some(s=>storage.includes(s)));audit.secretStorageClean=true;
 assert.deepEqual(audit.pageErrors,[]);
 }catch(error){audit.failure={stage,message:safeText(error.message),stack:safeText(error.stack??'')};throw error;
 }finally{
  if(releaseGet)releaseGet();if(releasePatch)releasePatch();
  for(const {page}of contexts){await page.waitForLoadState('networkidle');page.removeAllListeners('response');}
  const results=await Promise.allSettled(pending);audit.pendingRejections=results.filter(r=>r.status==='rejected').map(r=>safeText(String(r.reason)));
  for(const {context,page,name}of contexts){const video=page.video();await context.close();if(video)await video.saveAs(path.join(out,name+'.webm'));}
  await observer.close();
  await fs.writeFile(path.join(out,'audit.json'),JSON.stringify(audit,null,2)+'\n');await browser.close();assert.deepEqual(audit.pendingRejections,[]);
 }
}
main().catch(e=>{console.error(safeText(e.stack??String(e)));process.exitCode=1;});
