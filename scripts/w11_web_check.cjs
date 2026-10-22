const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const shared = path.resolve(root, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(shared, '.tmp/w01-browsers');
const { chromium } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const output = path.dirname(process.env.W11_RUNTIME);
const password = 'W11 browser acceptance passphrase!';
const scrub = s => String(s).replace(/\/join\/[^\s?"'<>]+/g, '/join/[REDACTED]')
  .replace(/[A-Za-z0-9_-]{43}/g, '[REDACTED]');
const audit = { screens: [], accessibility: [], http: [], errors: [], expectedConsole: [], pageErrors: [], failedRequests: [], assertions: [] };
let stage = 'bootstrap';

async function main() {
  const runtime = JSON.parse(await fs.readFile(process.env.W11_RUNTIME, 'utf8'));
  const base = runtime.base, cid = runtime.courseId;
  const browser = await chromium.launch();
  const contexts = [];
  const pending = [];
  async function makePage(name) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 },
      permissions: ['clipboard-read', 'clipboard-write'],
      recordVideo: { dir: path.join(root, '.tmp/w11-video'), size: { width: 1280, height: 900 } } });
    const page = await context.newPage(); contexts.push({ context, page, name });
    page.on('console', m => {
      if (m.type() !== 'error') return;
      const text = scrub(m.text());
      const expected = (stage.startsWith('axe:') && text.includes('Content Security Policy')
        && (text.startsWith("Connecting to 'https://fonts.googleapis.com/") || text.startsWith('Applying inline style')))
        || (text === 'Failed to load resource: the server responded with a status of 401 (Unauthorized)')
        || (stage === 'invalid' && text === 'Failed to load resource: the server responded with a status of 410 (Gone)');
      (expected ? audit.expectedConsole : audit.errors).push({ stage, text });
    });
    page.on('pageerror', e => audit.pageErrors.push(scrub(e.message)));
    page.on('requestfailed', req => {
      const u = new URL(req.url());
      if (stage.startsWith('axe:') && u.origin === 'https://fonts.googleapis.com'
        && ['csp', 'net::ERR_BLOCKED_BY_CSP'].includes(req.failure()?.errorText)) return;
      audit.failedRequests.push({ stage, path: scrub(u.pathname), error: scrub(req.failure()?.errorText) });
    });
    page.on('response', response => {
      const u = new URL(response.url());
      if (!u.pathname.startsWith('/api/v1/') || u.pathname.includes('/auth/') || u.pathname === '/api/v1/me') return;
      pending.push((async () => {
        let body;
        try { body = await response.json(); } catch { return; }
        if (body.link?.token) body.link.token = '[REDACTED]';
        if (body.link?.url) body.link.url = `${base}/join/[REDACTED]`;
        audit.http.push({ stage, method: response.request().method(), path: scrub(u.pathname), status: response.status(), body });
      })());
    });
    return page;
  }
  async function api(page, method, route, data) {
    const me = await page.request.get(`${base}/api/v1/me`);
    const identity = me.ok() ? await me.json() : null;
    const response = await page.request.fetch(`${base}/api/v1${route}`, {
      method, ...(data === undefined ? {} : { data }),
      headers: { Origin: base, ...(identity ? { 'X-CSRF-Token': identity.csrf_token } : {}) },
    });
    const body = await response.json();
    const safe = structuredClone(body);
    if (safe.link?.token) safe.link.token = '[REDACTED]';
    if (safe.link?.url) safe.link.url = `${base}/join/[REDACTED]`;
    audit.http.push({ stage, method, path: scrub(route), status: response.status(), body: safe });
    return { status: response.status(), body };
  }
  async function theme(page, value, modal = false) {
    if (await page.locator('html').getAttribute('data-theme') !== value) {
      const toggle = page.getByRole('button', { name: value === 'dark' ? 'Bật chế độ tối' : 'Bật chế độ sáng', includeHidden: modal });
      // The modal makes the shell inert. Dispatch its real React toggle for the
      // appearance matrix, so tokens AND the logo stay in the same theme.
      if (modal) await toggle.dispatchEvent('click'); else await toggle.click();
    }
    await page.waitForTimeout(250);
    assert.equal(await page.locator('html').getAttribute('data-theme'),value);
  }
  async function matrix(page, state) {
    for (const width of [390, 768, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      for (const mode of ['light', 'dark']) {
        await theme(page, mode, state === 'share');
        await page.waitForTimeout(250);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, state);
        if (state === 'owner-members' && width >= 768) {
          const columns = await page.locator('.members-list > li').evaluateAll(rows => rows.map(row =>
            [...row.querySelectorAll('.members-list__date')].map(cell => Math.round(cell.getBoundingClientRect().x))));
          assert.deepEqual(columns[0],columns[1],'owner and learner date columns must align');
        }
        const targets = await page.locator('button,a.button,select,input:not([type=hidden])').evaluateAll(nodes => nodes
          .filter(n => n.getClientRects().length && !n.closest('[inert]') && (!document.querySelector('dialog[open]') || n.closest('dialog[open]')))
          .map(n => ({ name: n.getAttribute('aria-label') || n.textContent.trim(), w: n.getBoundingClientRect().width, h: n.getBoundingClientRect().height })));
        assert.deepEqual(targets.filter(n => n.w < 44 || n.h < 44), [], `${state}/${width}/${mode} targets`);
        const file = `${state}-${width}-${mode}.png`;
        await page.screenshot({ path: path.join(output, file), fullPage: state !== 'share' });
        audit.screens.push({ file, state, width, theme: mode });
      }
    }
    for (const mode of ['light', 'dark']) {
      await theme(page, mode, state === 'share');
      stage = `axe:${state}:${mode}`;
      await page.waitForTimeout(250);
      const result = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
      audit.accessibility.push({ state, theme: mode, width: 1280, violations: result.violations, incomplete: result.incomplete });
      assert.deepEqual(result.violations.map(v => v.id), [], stage);
      assert.deepEqual(result.incomplete.map(v => v.id), [], stage);
    }
    stage = state;
  }
  const owner = await makePage('owner');
  const learner = await makePage('learner');
  let state = {};
  try {
    await owner.goto(`${base}/dang-nhap`, { waitUntil: 'networkidle' });
    await owner.getByLabel('Email', { exact: true }).fill('owner-w11@example.invalid');
    await owner.getByLabel('Mật khẩu', { exact: true }).fill(password);
    await owner.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await owner.getByRole('heading', { name: 'Khoá học của tôi', exact: true }).waitFor();
    await owner.goto(`${base}/khoa-hoc/${cid}`, { waitUntil: 'networkidle' });
    // Mask only the one-time bearer string in recorded pixels; clipboard and HTTP stay real.
    await owner.addStyleTag({ url: `${base}/__test__/redact.css` });
    await owner.getByRole('button', { name: 'Chia sẻ', exact: true }).click();
    await owner.getByRole('combobox', { name: /Thời hạn/ }).selectOption('never');
    await owner.getByLabel(/Số lượt tối đa/).fill('1');
    const response = owner.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/share-links'));
    await owner.getByRole('button', { name: 'Tạo link chia sẻ', exact: true }).click();
    const primary = (await (await response).json()).link;
    state.primaryLinkId = primary.id;
    await owner.getByRole('button', { name: 'Sao chép link', exact: true }).click();
    assert.equal(await owner.evaluate(() => navigator.clipboard.readText()), primary.url);
    await matrix(owner, 'share');
    await owner.keyboard.press('Tab');
    assert.equal(await owner.evaluate(() => Boolean(document.activeElement.closest('dialog[open]'))),true);
    await owner.keyboard.press('Escape');
    assert.equal(await owner.locator('dialog[open]').count(), 0);
    assert.equal(await owner.getByRole('button',{name:'Chia sẻ',exact:true}).evaluate(el=>el===document.activeElement),true);
    const refreshedLinks = owner.waitForResponse(r => r.request().method() === 'GET' && r.url().endsWith('/share-links'));
    await owner.getByRole('button', { name: 'Chia sẻ', exact: true }).click();
    await (await refreshedLinks).finished();
    await owner.getByText('Đang tải link…', { exact: true }).waitFor({ state: 'hidden' });
    assert.equal(await owner.locator('.sharing-once').count(), 0);
    await owner.keyboard.press('Escape');
    audit.assertions.push('owner creates/copies a one-time token; close clears it; list contains only tail');
    await learner.goto(primary.url, { waitUntil: 'networkidle' });
    await learner.getByRole('heading', { name: 'Đại số tuyến tính', exact: true }).waitFor();
    await matrix(learner, 'guest');
    assert.equal(new URL(await learner.locator('.join-auth-actions').getByRole('link', { name: 'Đăng ký', exact: true }).getAttribute('href'),base).searchParams.get('next'),`/join/${primary.token}`);
    await learner.locator('.join-auth-actions').getByRole('link', { name: 'Đăng nhập', exact: true }).click();
    assert.equal(new URL(learner.url()).searchParams.get('next'), `/join/${primary.token}`);
    // Create learner through real HTTP, then test actual login return route.
    const signup = await learner.request.post(`${base}/api/v1/auth/register`, { headers: { Origin: base },
      data: { email: 'learner-w11@example.invalid', password, display_name: 'Nguyễn An' } });
    assert.equal(signup.status(), 200);
    const me = await learner.request.get(`${base}/api/v1/me`); const identity = await me.json();
    state.learnerId = identity.account.id;
    await api(learner, 'POST', '/auth/logout');
    await learner.reload({ waitUntil: 'networkidle' });
    await learner.getByLabel('Email', { exact: true }).fill('learner-w11@example.invalid');
    await learner.getByLabel('Mật khẩu', { exact: true }).fill(password);
    await learner.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await learner.waitForURL(primary.url);
    await learner.getByRole('heading', { name: 'Thông tin khi tham gia' }).waitFor();
    await matrix(learner, 'authenticated');
    await learner.getByRole('button', { name: 'Tham gia', exact: true }).click();
    await learner.waitForURL(`${base}/khoa-hoc/${cid}`);
    audit.assertions.push('guest login returns to exact link; unverified learner joins with disclosure');
    const repeat = await api(learner, 'POST', `/join/${primary.token}`);
    assert.equal(repeat.body.already_member, true);
    assert.equal((await api(owner,'GET',`/courses/${cid}/share-links`)).body.items.find(x => x.id === primary.id).use_count,1);
    const progress = await api(learner,'PUT',`/courses/${cid}/progress/${encodeURIComponent(runtime.nodeId)}`,{learned:true});
    assert.equal(progress.status,200);
    await learner.goto(`${base}/khoa-hoc/${cid}/thanh-vien`,{waitUntil:'networkidle'});
    await learner.getByRole('heading',{name:'Thành viên',exact:true}).waitFor();
    await matrix(learner,'learner-members');
    await owner.goto(`${base}/khoa-hoc/${cid}/thanh-vien`,{waitUntil:'networkidle'});
    await owner.getByText('Nguyễn An',{exact:true}).waitFor();
    await matrix(owner,'owner-members');
    // Design-only snapshot of an authenticated real page; no token-bearing join URLs.
    let snapshot = (await owner.content()).replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
    for (const match of [...snapshot.matchAll(/<link\b[^>]*rel=["']stylesheet["'][^>]*href=["']([^"']+)["'][^>]*>/gi)]) {
      const css = await fs.readFile(path.join(root,'src/web/frontend/dist/assets',path.basename(new URL(match[1],base).pathname)),'utf8');
      snapshot = snapshot.replace(match[0],`<style>${css}</style>`);
    }
    const snapshotPath = path.join(root,'.tmp/w11-members-inspect.html');
    await fs.mkdir(path.dirname(snapshotPath),{recursive:true});
    await fs.writeFile(snapshotPath,snapshot.replace(/<head([^>]*)>/i,`<head$1><base href="${base}/">`));
    await fs.mkdir(path.join(root,'.tmp/w11-taste-profiles'),{recursive:true});
    const inspected = spawnSync(process.execPath,[path.join(shared,'.agents/skills/design-taste-frontend/scripts/inspect.mjs'),
      snapshotPath,'--out',path.join(output,'taste-inspect'),'--widths','1280,768,390','--app','--json'],
      {cwd:root,encoding:'utf8',timeout:180000,env:{...process.env,TASTE_SKILL_TMP:path.join(root,'.tmp/w11-taste-profiles')}});
    await fs.writeFile(path.join(output,'taste-inspector.log'),scrub(`${inspected.stdout||''}${inspected.stderr||''}`));
    assert.ok([0,1].includes(inspected.status),'taste inspector must finish its review');
    const designReport = JSON.parse(await fs.readFile(path.join(output,'taste-inspect/report.json'),'utf8'));
    assert.equal(designReport.viewports.length,3,'taste inspector must measure all three widths');
    audit.designInspection={exitCode:inspected.status,scope:'design-only real members DOM/CSS; does not replace HTTP acceptance'};
    await api(owner,'DELETE',`/courses/${cid}/share-links/${primary.id}`);
    assert.equal((await api(learner,'GET',`/courses/${cid}`)).status,200);
    await owner.getByRole('button',{name:'Xoá thành viên',exact:true}).click();
    await owner.getByRole('button',{name:'Xác nhận xoá',exact:true}).click();
    await owner.getByText('Nguyễn An',{exact:true}).waitFor({state:'hidden'});
    assert.equal((await api(learner,'GET',`/courses/${cid}/progress`)).status,404);
    audit.assertions.push('repeat does not consume uses; revoke retains members; removal denies next progress request');
    const replacement=(await api(owner,'POST',`/courses/${cid}/share-links`,{expires_in_days:null})).body.link;
    assert.equal((await api(learner,'POST',`/join/${replacement.token}`)).status,200);
    const restored=(await api(learner,'GET',`/courses/${cid}/progress`)).body;
    assert.equal(restored.nodes[runtime.nodeId].state,'learned');
    await learner.goto(replacement.url,{waitUntil:'networkidle'});
    await learner.getByRole('button',{name:'Tham gia',exact:true}).click();
    await learner.waitForURL(`${base}/khoa-hoc/${cid}`);
    await learner.getByText('Bạn đã tham gia khoá học này.',{exact:true}).waitFor();
    assert.equal((await api(owner,'GET',`/courses/${cid}/share-links`)).body.items.find(x=>x.id===replacement.id).use_count,1);
    await learner.goto(`${base}/khoa-hoc/${cid}/thanh-vien`,{waitUntil:'networkidle'});
    await learner.getByRole('button',{name:'Rời khoá học',exact:true}).click();
    await learner.getByRole('button',{name:'Xác nhận rời khoá',exact:true}).click();
    await learner.waitForURL(`${base}/khoa-hoc`);
    assert.equal((await api(learner,'GET',`/courses/${cid}`)).status,404);
    assert.equal((await api(owner,'POST',`/courses/${cid}/leave`)).status,403);
    audit.assertions.push('rejoin restores private progress; leave removes access; owner cannot leave');
    // All invalid-link causes share a dedicated join screen and the same HTTP envelope.
    const exhausted=(await api(owner,'POST',`/courses/${cid}/share-links`,{max_uses:1})).body.link;
    await api(learner,'POST',`/join/${exhausted.token}`);
    await api(learner,'POST',`/courses/${cid}/leave`);
    stage='invalid';
    let invalidBody;
    for (const token of ['broken',primary.token,exhausted.token,process.env.W11_EXPIRED_TOKEN]) {
      const invalid=await api(learner,'GET',`/join/${token}`);
      assert.equal(invalid.status,410);
      if (invalidBody) assert.deepEqual(invalid.body,invalidBody); else invalidBody=invalid.body;
      await learner.goto(`${base}/join/${token}`,{waitUntil:'networkidle'});
      await learner.getByRole('heading',{name:'Link chia sẻ',exact:true}).waitFor();
      assert.equal(await learner.getByText('Đặt mật khẩu mới',{exact:true}).count(),0);
    }
    await matrix(learner,'invalid');
    await learner.emulateMedia({reducedMotion:'reduce'});
    assert.equal(await learner.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),true);
    await learner.waitForTimeout(250);
    assert.equal(await learner.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').length),0);
    await learner.keyboard.press('Tab');
    const focus=await learner.evaluate(()=>({visible:!!document.activeElement.getClientRects().length,outline:getComputedStyle(document.activeElement).outlineStyle}));
    assert.equal(focus.visible,true);assert.notEqual(focus.outline,'none');
    audit.assertions.push('broken/revoked/expired/exhausted links have identical errors and dedicated join UI; keyboard/reduced motion checked');
    assert.deepEqual(audit.errors,[]);assert.deepEqual(audit.pageErrors,[]);assert.deepEqual(audit.failedRequests,[]);
    await fs.writeFile(path.join(output,'state.json'),JSON.stringify(state,null,2)+'\n');
  } finally {
    await Promise.allSettled(pending);
    for (const {context,page,name} of contexts) {
      const video=page.video();await context.close();
      if(video)await video.saveAs(path.join(output,`${name}.webm`));
    }
    await browser.close();
    await fs.writeFile(path.join(output,'audit.json'),scrub(JSON.stringify(audit,null,2))+'\n');
  }
  console.log(JSON.stringify({screens:audit.screens.length,axe:audit.accessibility.length,assertions:audit.assertions.length,http:audit.http.length}));
}
main().catch(error=>{console.error(scrub(error.stack));process.exitCode=1;});
