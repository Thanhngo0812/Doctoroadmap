const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),shared=path.resolve(root,'../..');
process.env.PLAYWRIGHT_BROWSERS_PATH=path.join(shared,'.tmp/w01-browsers');
const {chromium}=require(path.join(shared,'.tmp/w01-browser-tools/node_modules/playwright'));
const {AxeBuilder}=require(path.join(shared,'.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const runtimePath=process.env.W12_REACT_RUNTIME,out=path.dirname(runtimePath),PASSWORD='W12 synthetic browser passphrase!';
const audit={configurations:[],screens:[],accessibility:[],http:[],requests:[],pageErrors:[],console:[],sql:[],tokenLeaks:[]};
const secrets=new Set([PASSWORD]);let stage='bootstrap';
const safeText=text=>[...secrets].reduce((s,v)=>s.split(v).join('[REDACTED]'),String(text)).replace(/((?:token|invitation)=)[A-Za-z0-9_-]+/g,'$1[REDACTED]');
const scrub=value=>Array.isArray(value)?value.map(scrub):value&&typeof value==='object'?Object.fromEntries(Object.entries(value).map(([k,v])=>[k,/password|csrf|token|cookie/i.test(k)?'[REDACTED]':scrub(v)])):typeof value==='string'?safeText(value):value;
async function main(){
 const runtime=JSON.parse(await fs.readFile(runtimePath,'utf8')),base=runtime.base,api=base+'/api/v1',ids=runtime.courseIds;
 const browser=await chromium.launch(),contexts=[];let learner;
 async function userPage(name){
  const context=await browser.newContext({viewport:{width:1280,height:900},recordVideo:{dir:path.join(root,'tmp/w12-react-video'),size:{width:1280,height:900}}});
  await context.exposeBinding('__w12Record',(_,row)=>{
   const serialized=JSON.stringify(row);for(const secret of secrets)if(secret!==PASSWORD&&serialized.includes(secret))audit.tokenLeaks.push({stage,via:'fetch',path:row.path});
   if(row.path.endsWith('/invitations')&&row.body.items)for(const item of row.body.items)assert.deepEqual(Object.keys(item).sort(),['id','course_id','course_title','email','status','expires_at','created_at','responded_at'].sort());
   audit.http.push({stage,...scrub(row),via:'fetch-clone-before-application'});
  });
  await context.addInitScript(()=>{const original=window.fetch.bind(window);window.fetch=async(...args)=>{const response=await original(...args);if(response.url.includes('/api/v1/')&&response.headers.get('content-type')?.includes('json'))await window.__w12Record({path:new URL(response.url).pathname,status:response.status,method:args[1]?.method??'GET',body:await response.clone().json()});return response;};});
  const page=await context.newPage();contexts.push({context,page,name});
  page.on('pageerror',e=>audit.pageErrors.push({stage,message:safeText(e.message)}));
  page.on('console',m=>{if(m.type()==='error')audit.console.push({stage,message:safeText(m.text())});});
  page.on('request',request=>{const url=new URL(request.url());for(const secret of secrets)if(secret!==PASSWORD&&(request.url().includes(secret)||(request.postData()??'').includes(secret)))audit.tokenLeaks.push({stage,via:'request',path:url.pathname});audit.requests.push({stage,path:url.pathname,queryKeys:[...url.searchParams.keys()],method:request.method(),origin:url.origin});});
  return page;
 }
 const owner=await userPage('owner'),receiver=await userPage('receiver');learner=owner;
 const observer=await browser.newContext();
 async function login(page,label){await page.goto(base+'/dang-nhap');await page.getByLabel('Email',{exact:true}).fill(label+'-w12@example.invalid');await page.getByLabel('Mật khẩu',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await page.waitForURL(base+'/khoa-hoc');}
 async function theme(page,value,reduced=false){await page.emulateMedia({colorScheme:value,reducedMotion:reduced?'reduce':'no-preference'});if(await page.locator('html').getAttribute('data-theme')!==value)await page.getByRole('button',{name:value==='dark'?'Bật chế độ tối':'Bật chế độ sáng'}).click();}
 async function share(page,cid){await page.goto(base+'/khoa-hoc/'+cid);await page.getByRole('button',{name:'Chia sẻ',exact:true}).click();await page.getByRole('tab',{name:'Mời qua email'}).click();await page.getByLabel('Email người nhận').waitFor();await page.getByText('Đang tải lời mời…',{exact:true}).waitFor({state:'hidden'});}
 async function result(response,label){const body=await response.json();audit.http.push({stage:label,path:new URL(response.url()).pathname,status:response.status(),body:scrub(body),via:'direct-http'});return body;}
 try{
  const observerLogin=await observer.request.post(api+'/auth/login',{headers:{Origin:base},data:{email:'other-w12@example.invalid',password:PASSWORD}});assert.equal(observerLogin.status(),200);
  const probe=async label=>{const response=await observer.request.get(api+'/__test/w12/probe');assert.equal(response.status(),200);const row=await response.json();audit.sql.push({stage:label,...row});return row;};
  const mail=async email=>{const response=await observer.request.get(api+'/__test/w12/mail',{params:{email}});assert.equal(response.status(),200);return(await response.json()).body;};
  const headers=async page=>({Origin:base,'X-CSRF-Token':(await(await page.request.get(api+'/me')).json()).csrf_token});
  await login(owner,'owner');await login(receiver,'receiver');
      async function settled() {
      await learner.evaluate(() => Promise.all(document.getAnimations().filter(a => a.effect?.getTiming().iterations !== Infinity).map(a => a.finished.catch(() => {}))));
      await learner.evaluate(() => document.fonts.ready);
    }
    async function capture(name, axe = false) {
      await settled();
      const images=await learner.locator('img').evaluateAll(nodes=>Promise.all(nodes.map(async image=>{await image.decode();return {src:new URL(image.src).pathname,width:image.naturalWidth,height:image.naturalHeight};})));
      for(const image of images)assert.ok(image.width>0&&image.height>0,'Visible page image must decode: '+image.src);
      const width = learner.viewportSize().width;
      const theme = await learner.locator('html').getAttribute('data-theme');
      const reduced = await learner.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
      const file = name + '-' + width + '-' + theme + (reduced ? '-reduced' : '') + '.png';
      const layout = await learner.evaluate(() => {
        const region = document.querySelector('dialog[open]') || document.querySelector('.invitations-inbox') || document.querySelector('.auth-card') || document.querySelector('.content-page') || document.querySelector('.content-library');
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
      await learner.screenshot({ path: path.join(out, file), fullPage: !(await learner.locator('dialog[open]').count()) }); audit.screens.push({ file, width, theme, reduced, layout, images });
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
          if (!element?.closest('.katex,.sharing-dialog,.invitations-inbox,.email-invitations,.auth-card,.content-library,.content-page,.profile-dialog,.learning-chat-panel')) return { selector, eligible: false };
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




  const smoke=process.env.W12_REACT_SMOKE==='1';
  for(const width of(smoke?[1280]:[390,768,1280]))for(const color of(smoke?['light']:['light','dark']))for(const reduced of(smoke?[false]:[false,true])){
   stage='matrix:'+width+':'+color+':'+reduced;audit.configurations.push({width,theme:color,reduced});
   await owner.setViewportSize({width,height:900});await owner.goto(base+'/khoa-hoc/'+ids.primary);await theme(owner,color,reduced);await owner.getByRole('button',{name:'Chia sẻ',exact:true}).click();
   await owner.getByRole('tab',{name:'Bằng link'}).focus();await owner.keyboard.press('ArrowRight');assert.equal(await owner.getByRole('tab',{name:'Mời qua email'}).getAttribute('aria-selected'),'true');assert.equal(await owner.getByRole('tab',{name:'Mời qua email'}).evaluate(e=>e===document.activeElement),true);
   await owner.getByText('receiver-w12@example.invalid',{exact:true}).waitFor();learner=owner;await capture('email-pending',true);
   await owner.getByLabel('Email người nhận').fill('email-khong-hop-le');await owner.getByRole('button',{name:'Gửi lời mời',exact:true}).click();assert.equal(await owner.getByLabel('Email người nhận').getAttribute('aria-invalid'),'true');await capture('email-invalid',true);
   await receiver.setViewportSize({width,height:900});await receiver.goto(base+'/khoa-hoc');await theme(receiver,color,reduced);await receiver.getByRole('button',{name:'Chấp nhận lời mời vào Đại số tuyến tính'}).waitFor();learner=receiver;await capture('inbox-pending',true);
  }
  stage='owner-create-deduplicate';await owner.getByLabel('Email người nhận').fill(' NEW-W12@example.invalid, new-w12@example.invalid\nsecond-new-w12@example.invalid');await owner.getByRole('button',{name:'Gửi lời mời',exact:true}).click();await owner.getByText(/Đã tạo 2 lời mời/).waitFor();
  if(!smoke)assert.equal(await owner.locator('.invitation-notice').evaluate(e=>getComputedStyle(e).animationName),'none');learner=owner;await capture('email-created',true);
  let state=await probe('after-dedup');assert.equal(state.invitations.filter(i=>i.email_normalized==='new-w12@example.invalid'&&i.course_id===ids.primary).length,1);
  const newInvite=state.invitations.find(i=>i.email_normalized==='new-w12@example.invalid'&&i.course_id===ids.primary);assert.equal(new Date(newInvite.expires_at)-new Date(newInvite.created_at),7*86400000);assert.equal(newInvite.hash_bytes,32);assert.equal(newInvite.invitee_account_id,null);
  const invitationUrl=(await mail('new-w12@example.invalid')).match(/http[^\s]+\/dang-ky#invitation=[A-Za-z0-9_-]+/)[0];const rawInvitation=new URL(invitationUrl).hash.split('=')[1];secrets.add(rawInvitation);
  stage='cancel';await share(owner,ids.cancel);await owner.getByRole('button',{name:'Huỷ lời mời cho receiver-w12@example.invalid'}).click();await owner.getByText('Đã huỷ lời mời.',{exact:true}).waitFor();
  let response=await receiver.request.post(api+'/invitations/'+runtime.invitationIds.cancel+'/accept',{headers:await headers(receiver)});assert.equal(response.status(),410);await result(response,'cancelled-denied');
  stage='expired';response=await receiver.request.post(api+'/invitations/'+runtime.invitationIds.expired+'/accept',{headers:await headers(receiver)});assert.equal(response.status(),410);await result(response,'expired-denied');await share(owner,ids.expired);await owner.getByText('Đã hết hạn',{exact:true}).waitFor();learner=owner;await capture('email-expired',true);
  stage='full';await receiver.goto(base+'/khoa-hoc');await receiver.getByRole('button',{name:'Chấp nhận lời mời vào Nhóm đã đủ 200 thành viên'}).click();await receiver.getByRole('alert').filter({hasText:'Khoá học đã đủ người.'}).waitFor();learner=receiver;await capture('inbox-course-full',true);assert.equal((await probe('full-course-denied')).courseCounts.find(c=>c.course_id===ids.full).members,200);
  stage='receiver-actions';await receiver.getByRole('button',{name:'Chấp nhận lời mời vào Đại số tuyến tính'}).click();await receiver.getByText('Đã tham gia Đại số tuyến tính.',{exact:false}).waitFor();await receiver.getByRole('article',{name:'Đại số tuyến tính',exact:true}).waitFor();
  await receiver.getByRole('button',{name:'Từ chối lời mời vào Ôn tập Đại số'}).click();await receiver.getByText('Đã từ chối lời mời.',{exact:true}).waitFor();state=await probe('receiver-accepted-declined');assert.ok(state.membership.some(m=>m.course_id===ids.primary&&m.account_id===runtime.accountIds.receiver&&m.via==='email'));assert.ok(!state.membership.some(m=>m.course_id===ids.secondary&&m.account_id===runtime.accountIds.receiver));
  stage='wrong-email-fragment';const other=await userPage('other');await login(other,'other');await other.goto(invitationUrl);await other.waitForURL(base+'/khoa-hoc');assert.equal(await other.getByRole('button',{name:/Chấp nhận lời mời/}).count(),0);response=await other.request.post(api+'/invitations/'+newInvite.id+'/accept',{headers:await headers(other)});assert.equal(response.status(),404);await result(response,'wrong-email-denied');
  stage='registration-fragment';const newcomer=await userPage('newcomer');await newcomer.goto(invitationUrl);await newcomer.waitForURL(base+'/dang-ky');await newcomer.getByText(/Xác minh đúng email nhận lời mời/).waitFor();
  await newcomer.getByRole('banner').getByRole('link',{name:'Đăng nhập',exact:true}).click();await newcomer.getByText(/Xác minh đúng email nhận lời mời/).waitFor();await newcomer.locator('.auth-alternate').getByRole('link',{name:'Tạo tài khoản',exact:true}).click();assert.equal(new URL(newcomer.url()).hash,'');
  await newcomer.getByLabel('Tên hiển thị',{exact:true}).fill('Minh Anh');await newcomer.getByLabel('Email',{exact:true}).fill('new-w12@example.invalid');await newcomer.getByLabel('Mật khẩu',{exact:true}).fill(PASSWORD);await newcomer.getByLabel('Nhập lại mật khẩu',{exact:true}).fill(PASSWORD);await newcomer.getByRole('button',{name:'Tạo tài khoản',exact:true}).click();await newcomer.waitForURL(base+'/khoa-hoc');assert.equal(await newcomer.getByRole('button',{name:/Chấp nhận lời mời/}).count(),0);
  response=await newcomer.request.post(api+'/invitations/'+newInvite.id+'/accept',{headers:await headers(newcomer)});assert.equal(response.status(),403);await result(response,'unverified-recipient-denied');state=await probe('registered-not-verified');assert.equal(state.invitations.find(i=>i.id===newInvite.id).invitee_account_id,null);
  const verifyUrl=(await mail('new-w12@example.invalid')).match(/http[^\s]+#token=[A-Za-z0-9_-]+/)[0];await newcomer.goto(verifyUrl);await newcomer.getByRole('button',{name:'Xác minh email',exact:true}).click();await newcomer.getByText('Địa chỉ email của bạn đã được xác minh.',{exact:true}).waitFor();
  state=await probe('verified-without-membership');const newAccount=state.invitations.find(i=>i.id===newInvite.id).invitee_account_id;assert.ok(newAccount);assert.ok(!state.membership.some(m=>m.course_id===ids.primary&&m.account_id===newAccount));
  await newcomer.goto(base+'/khoa-hoc');await newcomer.getByRole('button',{name:'Chấp nhận lời mời vào Đại số tuyến tính'}).click();await newcomer.getByRole('article',{name:'Đại số tuyến tính',exact:true}).waitFor();state=await probe('verified-explicit-accept');assert.ok(state.membership.some(m=>m.course_id===ids.primary&&m.account_id===newAccount&&m.via==='email'));
  const storage=await newcomer.evaluate(()=>JSON.stringify({history:history.state,local:localStorage,session:sessionStorage,url:location.href}));assert.ok(!storage.includes(rawInvitation));assert.ok(!storage.includes(PASSWORD));
  stage='unverified-owner';const unverified=await userPage('unverified');await login(unverified,'unverified');await share(unverified,ids.unverified);await unverified.getByLabel('Email người nhận').fill('ban@example.invalid');await unverified.getByRole('button',{name:'Gửi lời mời',exact:true}).click();await unverified.getByRole('alert').filter({hasText:'Bạn cần xác minh email trước.'}).waitFor();learner=unverified;await capture('email-unverified-owner',true);
  stage='daily-mail-cap';response=await observer.request.post(api+'/__test/w12/fill-rate',{headers:await headers(observer)});assert.equal(response.status(),200);await share(owner,ids.primary);await owner.getByLabel('Email người nhận').fill('over-limit@example.invalid');await owner.getByRole('button',{name:'Gửi lời mời',exact:true}).click();await owner.getByRole('alert').filter({hasText:'Thử lại sau'}).waitFor();learner=owner;await capture('email-rate-limited',true);state=await probe('rate-cap');assert.equal(state.audit.filter(e=>e.actor_id===runtime.accountIds.owner&&e.action==='invitation_sent').length,200);assert.equal(state.invitations.filter(i=>i.email_normalized==='over-limit@example.invalid').length,0);
  stage='design-inspection';learner=receiver;await receiver.setViewportSize({width:1280,height:900});await receiver.goto(base+'/khoa-hoc');await theme(receiver,'light');await settled();
const client=await receiver.context().newCDPSession(receiver);await client.send('DOM.enable');await client.send('CSS.enable');const {root:dom}=await client.send('DOM.getDocument');const {nodeId}=await client.send('DOM.querySelector',{nodeId:dom.nodeId,selector:'.courses-heading h1'});audit.liveFonts=await client.send('CSS.getPlatformFontsForNode',{nodeId});assert.ok(audit.liveFonts.fonts.some(f=>f.familyName==='Be Vietnam Pro'&&f.isCustomFont));
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
    const snapshotPath = path.join(root, 'tmp/w12-react-inspect.html');
    await fs.writeFile(snapshotPath, snapshot.replace(/<head([^>]*)>/i, `<head$1><base href="${base}/">`));
    await fs.mkdir(path.join(root, 'tmp/w12-react-taste-profiles'), { recursive: true });
    const inspected=spawnSync(process.execPath,[path.join(shared,'.agents/skills/design-taste-frontend/scripts/inspect.mjs'),snapshotPath,'--out',path.join(out,'taste-inspect'),'--widths','1280,768,390','--app','--json'],{cwd:root,encoding:'utf8',timeout:180000,env:{...process.env,TASTE_SKILL_TMP:path.join(root,'tmp/w12-react-taste-profiles')}});
    await fs.writeFile(path.join(out,'taste-inspector.log'),String(inspected.stdout??'')+String(inspected.stderr??''));
    audit.designInspection=JSON.parse(await fs.readFile(path.join(out,'taste-inspect/report.json'),'utf8'));assert.equal(audit.designInspection.findings.filter(x=>x.level==='FAIL').length,0);


  audit.proof={deduplicated:true,ttlDays:7,hashBytes:32,fullMemberCount:200,verifiedEmailBeforeMembership:true,explicitAccept:true,wrongEmailDenied:true,cancelledExpiredDenied:true,dailyCap:200,tokenStayedOutOfRequestsAndStorage:true};assert.deepEqual(audit.tokenLeaks,[]);assert.deepEqual(audit.pageErrors,[]);
 }catch(error){audit.failure={stage,message:safeText(error.message),stack:safeText(error.stack??'')};throw error;
 }finally{
  for(const {context,page,name}of contexts){await page.waitForLoadState('networkidle');const video=page.video();await context.close();if(video)await video.saveAs(path.join(out,name+'.webm'));}
  await observer.close();await fs.writeFile(path.join(out,'audit.json'),JSON.stringify(audit,null,2)+'\n');await browser.close();
 }
}
main().catch(e=>{console.error(safeText(e.stack??String(e)));process.exitCode=1;});
