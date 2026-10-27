const assert = require('node:assert/strict');
const { hasTerminalFrame, intentionalDisconnect } = require('./w10_sse_audit.cjs');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..'), shared = path.resolve(root, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(shared, '.tmp/w01-browsers');
const { chromium } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const out = path.dirname(process.env.W16_RUNTIME);
const audit = { configurations: [], screens: [], accessibility: [], http: [], pageErrors: [], console: [], requests: [], assertions: [], streams: [], privacyFailures: [] };
let stage = 'bootstrap';
async function main() {
  const runtime = JSON.parse(await fs.readFile(process.env.W16_RUNTIME, 'utf8'));
  const { base, courseId: cid, moduleA: ma, moduleB: mb } = runtime;
  const api = base + '/api/v1/courses/' + cid, modulePage = base + '/khoa-hoc/' + cid + '/module/' + ma;
  function inspectPayload(url, body) {
    if (!/\/(quizzes|documents|library|sessions)/.test(url)) return;
    for (const value of ['"validation"', '"public_id"', '"_private"', 'res.cloudinary.com', 'PRIVATE_SOLVER_REASON', '"result_summary"', '"tool_calls"'])
      assert.ok(!body.includes(value), value);
    if (/\/quizzes(?:\/[^/]+)?$/.test(new URL(url).pathname) && !/\/submit|\/result/.test(url)) {
      for (const value of ['"correct_index"', '"is_correct"', '"explanation"', '"why_wrong"', '"answers"'])
        assert.ok(!body.includes(value), 'public quiz leaked ' + value);
    }
  }
  const browser = await chromium.launch(), contexts = [], pending = [], releaseRoutes = [], submitHolds = new Map();
  async function userPage(name) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 },
      recordVideo: { dir: path.join(root, 'tmp/w16-video'), size: { width: 1280, height: 900 } } });
    await context.exposeBinding('__w16HoldSubmit', (_, url) => {
      const hold = submitHolds.get(url);
      if (hold) { hold.ready = true; return hold.gate; }
    });
    await context.exposeBinding('__w16RecordJson', (_, row) => {
      const receipt = { ...row, stage, path: new URL(row.url).pathname, via: 'fetch-json-clone' };
      audit.http.push(receipt);
      try {
        if (row.readErrorName) {
          assert.equal(row.readErrorName, 'AbortError');
          assert.equal(row.signalAborted, true);
        } else { JSON.parse(row.body); inspectPayload(row.url, row.body); }
      } catch (error) { audit.privacyFailures.push({ path: receipt.path, message: error.message }); throw error; }
    });
    const streams = new Map();
    await context.exposeBinding('__w16RecordStream', (_, row) => {
      if (row.event === 'start') {
        const receipt = { id: row.id, stage, path: new URL(row.url).pathname, url: row.url, method: row.method,
          status: row.status, type: row.type, body: '', via: 'fetch-body-tee', complete: false, terminalSeen: false };
        streams.set(row.id, receipt); audit.streams.push(receipt); audit.http.push(receipt);
        return;
      }
      const receipt = streams.get(row.id); assert.ok(receipt, 'stream identity');
      if (row.event === 'chunk') {
        receipt.body += row.text;
        receipt.terminalSeen = hasTerminalFrame(receipt.body);
        try { inspectPayload(receipt.url, receipt.body); }
        catch (error) { audit.privacyFailures.push({ id: row.id, message: error.message }); throw error; }
      } else if (row.event === 'done') receipt.complete = true;
      else if (row.event === 'cancel') receipt.cancelled = true;
      else { receipt.readError = row.message; receipt.readErrorName = row.name; if (row.name === 'AbortError') receipt.cancelled = true; }
    });
    await context.addInitScript(({ prefix }) => {
      const original = window.fetch.bind(window);
      window.fetch = async (...args) => {
        const response = await original(...args);
        if (response.url.endsWith('/submit')) await window.__w16HoldSubmit(response.url);
        if (!response.url.startsWith(prefix) || !response.body) return response;
        const type = response.headers.get('content-type') ?? '';
        if (type.includes('json')) {
          const row = { url: response.url, method: args[1]?.method ?? 'GET', status: response.status, type };
          try {
            const body = await response.clone().text();
            await window.__w16RecordJson({ ...row, body, complete: true });
          } catch (error) {
            await window.__w16RecordJson({ ...row, body: null, complete: false, readErrorName: error.name,
              signalAborted: args[1]?.signal?.aborted === true });
            throw error;
          }
          return response;
        }
        if (!type.startsWith('text/event-stream')) return response;
        const id = crypto.randomUUID(), [application, recording] = response.body.tee();
        const appReader = application.getReader(), recorder = recording.getReader(), decoder = new TextDecoder();
        const record = event => window.__w16RecordStream({ id, ...event });
        await record({ event: 'start', url: response.url, method: args[1]?.method ?? 'GET', status: response.status, type: response.headers.get('content-type') });
        const body = new ReadableStream({
          async pull(controller) {
            try {
              const [part, copy] = await Promise.all([appReader.read(), recorder.read()]);
              if (part.done) { await record({ event: 'done' }); controller.close(); return; }
              await record({ event: 'chunk', text: decoder.decode(copy.value, { stream: true }) });
              controller.enqueue(part.value);
            } catch (error) {
              await record({ event: 'error', name: error.name, message: error.message }).catch(() => {});
              controller.error(error);
            }
          },
          async cancel(reason) {
            await record({ event: 'cancel' }).catch(() => {});
            await Promise.all([appReader.cancel(reason), recorder.cancel(reason)]);
          },
        });
        return new Response(body, { status: response.status, statusText: response.statusText, headers: response.headers });
      };
    }, { prefix: base + '/api/v1/' });
    const page = await context.newPage(); contexts.push({ context, page, name });
    page.on('pageerror', error => audit.pageErrors.push({ stage, message: error.message }));
    page.on('console', message => { if (message.type() === 'error') audit.console.push({ stage, message: message.text() }); });
    page.on('request', request => {
      if (request.url().startsWith(api) && request.method() === 'POST')
        audit.requests.push({ stage, path: new URL(request.url()).pathname, body: request.postDataJSON() });
    });
    page.on('response', response => {
      if (!response.url().startsWith(base + '/api/v1/')) return;
      const when = stage;
      const job = (async () => {
        const type = response.headers()['content-type'] ?? '';
        if (type.startsWith('text/event-stream') || (type.includes('json') && response.request().resourceType() === 'fetch')) return; // Fetch bodies are recorded before the app sees them.
        const body = /json|markdown/.test(type) ? await response.text() : null;
        if (body) inspectPayload(response.url(), body);
        audit.http.push({ stage: when, path: new URL(response.url()).pathname, method: response.request().method(), status: response.status(), type, body });
      })();
      pending.push(job); void job.catch(() => {}); // Keep the original rejection for the final audited assertion.
    });
    return page;
  }
  const owner = await userPage('owner'), learner = await userPage('learner');
  async function login(page, name) {
    await page.goto(base + '/dang-nhap');
    await page.getByLabel('Email', { exact: true }).fill(name + '-w16@example.invalid');
    await page.getByLabel('Mật khẩu', { exact: true }).fill('W16 isolated browser passphrase!');
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await page.waitForURL(base + '/khoa-hoc');
  }
  try {
    await login(owner, 'owner'); await login(learner, 'learner');
    const identity = await (await owner.request.get(base + '/api/v1/me')).json();
    const headers = { Origin: base, 'X-CSRF-Token': identity.csrf_token };
    const learnerIdentity = await (await learner.request.get(base + '/api/v1/me')).json();
    const learnerHeaders = { Origin: base, 'X-CSRF-Token': learnerIdentity.csrf_token };
    const control = async data => { const r = await owner.request.post(base + runtime.controlPath, { headers, data }); assert.equal(r.status(), 200, await r.text()); return r.json(); };
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
        const region = document.querySelector('dialog[open]') || document.querySelector('.usage-page') || document.querySelector('.content-page') || document.querySelector('.content-library');
        const targets = [...region.querySelectorAll('button:not(:disabled),a[href],select,textarea,label:has(input)')]
          .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
          .map(e => ({ label: e.getAttribute('aria-label') || e.textContent.trim().slice(0, 70), w: e.getBoundingClientRect().width, h: e.getBoundingClientRect().height }))
          .filter(row => row.w < 43.5 || row.h < 43.5);
        return { overflow: document.documentElement.scrollWidth > innerWidth + 1, targets };
      });
      assert.equal(layout.overflow, false, name + ' horizontal overflow');
      assert.deepEqual(layout.targets, [], name + ' 44px targets');
      if (width < 1280 && name.startsWith('library-')) await learner.locator('.content-library').evaluate(e => scrollTo({ top: scrollY + e.getBoundingClientRect().top - document.querySelector('.courses-header').getBoundingClientRect().height - 16, behavior: 'instant' }));
      else await learner.evaluate(() => scrollTo({ top: 0, behavior: 'instant' }));
      await learner.screenshot({ path: path.join(out, file), fullPage: width >= 1280 }); audit.screens.push({ file, width, theme, reduced, layout });
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
          if (!element?.closest('.katex,.usage-page,.content-library,.content-page,.content-dialog,.learning-chat-panel')) return { selector, eligible: false };
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


    const smoke = process.env.W16_BROWSER_SMOKE === '1';
    for (const width of (smoke ? [1280] : [390,768,1280])) for (const theme of (smoke ? ['light'] : ['light','dark'])) for (const reduced of (smoke ? [false] : [false,true])) {
      audit.configurations.push({width,theme,reduced});
      await learner.setViewportSize({width,height:900});
      await learner.emulateMedia({colorScheme:theme,reducedMotion:reduced?'reduce':'no-preference'});
      for (const [ratio,label] of [[.35,'Còn nhiều'],[.85,'Gần hết'],[1,'Đã hết']]) {
        stage = 'usage:'+width+':'+theme+':'+reduced+':'+ratio;
        await control({action:'state',ratio,unlimited:ratio!==.85});
        await learner.goto(base+'/muc-dung');
        if (await learner.locator('html').getAttribute('data-theme')!==theme) await learner.getByRole('button',{name:theme==='dark'?'Bật chế độ tối':'Bật chế độ sáng'}).click();
        await learner.getByRole('heading',{name:'Hôm nay đã dùng '+Math.round(ratio*100)+'%',exact:true}).waitFor();
        const response=await learner.request.get(base+'/api/v1/me/usage');assert.equal(response.status(),200);const usage=await response.json();
        assert.equal(response.headers()['cache-control'],'no-store');
        const keys=JSON.stringify(usage);assert.ok(!/"[^"]*(?:usd|cost)[^"]*"\s*:/i.test(keys));
        assert.equal(usage.learner_today.used_ratio,ratio);assert.equal(await learner.getByRole('progressbar',{name:'Hạn mức học hôm nay'}).getAttribute('value'),String(ratio));
        assert.equal(await learner.getByText(label,{exact:true}).count(),1);
        if(ratio!==.85) await learner.getByText('Không giới hạn',{exact:true}).waitFor();else await learner.getByText('Còn 3 lượt dựng',{exact:true}).waitFor();
        const formatted=new Date(usage.learner_today.resets_at).toLocaleString('vi-VN',{hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit',year:'numeric',timeZone:'Asia/Ho_Chi_Minh'});
        assert.equal(await learner.locator('.usage-today time').innerText(),formatted);
        assert.ok(!/USD|cost|\$|Còn 0 lượt/.test(await learner.locator('main').innerText()));
        await learner.getByRole('heading',{name:'Mức dùng',exact:true}).focus();await learner.keyboard.press('Tab');assert.equal(await learner.evaluate(()=>document.activeElement.textContent.trim()),'Về khoá học');
        if(reduced) assert.ok(await learner.locator('.usage-ring-value').evaluate(e=>parseFloat(getComputedStyle(e).transitionDuration)<=.001));
        await capture('usage-'+Math.round(ratio*100),true);
      }
      await learner.goto(modulePage);
      const library=learner.getByRole('region',{name:'Tài liệu & Quiz của module'});await library.locator('.usage-limit').waitFor();
      assert.ok(await library.getByRole('link',{name:/Ghi chú ôn tập/}).count()>0);
      assert.equal(await library.getByRole('link',{name:'Làm quiz',exact:true}).getAttribute('aria-disabled'),null);
      await library.getByRole('button',{name:'Tạo tài liệu',exact:true}).click();await learner.getByRole('dialog',{name:'Tạo tài liệu học tập'}).locator('.usage-limit').waitFor();
      await capture('document-limit',true);await learner.getByRole('button',{name:'Đóng tạo tài liệu'}).click();
      await learner.getByRole('button',{name:'Mở khung trợ lý'}).click();await learner.locator('.learning-chat-usage .usage-limit').waitFor();
      assert.equal(await learner.getByRole('textbox',{name:'Câu hỏi'}).isEnabled(),true);
      await learner.getByRole('textbox',{name:'Câu hỏi'}).fill('Mở nội dung đã có');
      assert.equal(await learner.getByRole('button',{name:'Gửi câu hỏi'}).isEnabled(),true);
      await capture('chat-limit',true);await learner.getByRole('button',{name:'Đóng trợ lý'}).click();
    }
    stage='shared-limit';await control({action:'state',ratio:1,shared:true,unlimited:true});
    await learner.goto(base+'/muc-dung');await learner.getByText('Nội dung mới tạm dừng tới ngày mai.',{exact:true}).waitFor();await capture('shared-limit',true);
    const before=await control({action:'probe'});
    const sessionResponse=await learner.request.post(api+'/sessions',{headers:learnerHeaders,data:{scope:{kind:'module',module_id:ma}}});assert.equal(sessionResponse.status(),201);
    const sessionId=(await sessionResponse.json()).session_id;
    const intent={question:'Mở nội dung đã có',client_turn_id:'w16-limited-intent'};
    for(let i=0;i<2;i++) {
      const reply=await learner.request.post(api+'/sessions/'+sessionId+'/turns',{headers:{...learnerHeaders,Accept:'text/event-stream'},data:intent});assert.equal(reply.status(),200);
      const body=await reply.text();inspectPayload(reply.url(),body);audit.http.push({stage:'limited-chat-http',path:new URL(reply.url()).pathname,status:reply.status(),body});
      const events=body.split('\n').filter(line=>line.startsWith('data: ')).map(line=>JSON.parse(line.slice(6)));
      assert.ok(events.some(row=>row.answer?.status==='daily_limit'));
    }
    const limitedProbe=await control({action:'probe'});assert.equal(limitedProbe.assistantCalls,before.assistantCalls);
    audit.limitedChat={reachedCore:true,status:'daily_limit',replayedSameIntent:true,modelCallsUnchanged:true};
    await learner.goto(modulePage+'/khai-niem/'+encodeURIComponent(runtime.cachedNode));await learner.locator('.lecture-body').waitFor();
    const cached=await learner.request.get(api+'/concepts/'+encodeURIComponent(runtime.cachedNode)+'/lecture');assert.equal(cached.status(),200);assert.equal((await cached.json()).status,'ready');
    await capture('cached-lecture',true);
    await learner.goto(modulePage+'/khai-niem/'+encodeURIComponent(runtime.coldNode));await learner.locator('.lecture-failure').waitFor();
    await learner.getByRole('button',{name:/Thử lại/}).waitFor();await capture('shared-lecture-failure',true);
    const coldStream=audit.streams.find(row=>row.path.includes('/concepts/'+encodeURIComponent(runtime.coldNode)+'/lecture/stream'));
    const frames=coldStream.body.split('\n').filter(line=>line.startsWith('data: ')).map(line=>JSON.parse(line.slice(6)));
    const cold=frames.find(row=>row.lecture?.failure?.reason_code==='tran_he_thong').lecture;
    assert.equal(cold.failure.reason_code,'tran_he_thong');
    await learner.goto(base+'/khoa-hoc/'+cid+'/quiz/'+runtime.quizId);await learner.locator('.content-question input').first().waitFor();await capture('saved-quiz',true);
    await learner.goto(base+'/khoa-hoc/'+cid+'/quiz/tao?module='+encodeURIComponent(ma));await learner.locator('.content-question input').first().waitFor();
    const after=await control({action:'probe'});assert.equal(after.lectureCalls,before.lectureCalls);assert.equal(after.generatorCalls,before.generatorCalls);
    audit.cacheGuard={cachedLectureReady:true,coldFailure:cold.failure.reason_code,bankQuizUsable:true,before,after};
    stage='loading-error-retry';await learner.route('**/me/usage',route=>route.abort('failed'),{times:1});await learner.goto(base+'/muc-dung');await learner.getByRole('alert').waitFor();await capture('usage-error',true);
    await learner.getByRole('button',{name:'Thử lại',exact:true}).click();await learner.getByRole('progressbar',{name:'Hạn mức học hôm nay'}).waitFor({state:'attached'});await capture('usage-retry',true);
    // Taste inspection uses a design-only copy of this real authenticated DOM.
    let snapshot = (await learner.evaluate(() => {
      const clone = document.documentElement.cloneNode(true);
      const source = [...document.querySelectorAll('input[type=checkbox]')];
      [...clone.querySelectorAll('input[type=checkbox]')].forEach((input, index) => input.toggleAttribute('checked', source[index].checked));
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
    const snapshotPath = path.join(root, 'tmp/w16-inspect.html');
    await fs.writeFile(snapshotPath, snapshot.replace(/<head([^>]*)>/i, `<head$1><base href="${base}/">`));
    await fs.mkdir(path.join(root, 'tmp/w16-taste-profiles'), { recursive: true });
    const inspected=spawnSync(process.execPath,[path.join(shared,'.agents/skills/design-taste-frontend/scripts/inspect.mjs'),snapshotPath,'--out',path.join(out,'taste-inspect'),'--widths','1280,768,390','--app','--json'],{cwd:root,encoding:'utf8',timeout:180000,env:{...process.env,TASTE_SKILL_TMP:path.join(root,'tmp/w16-taste-profiles')}});
    await fs.writeFile(path.join(out,'taste-inspector.log'),String(inspected.stdout??'')+String(inspected.stderr??''));
    audit.designInspection=JSON.parse(await fs.readFile(path.join(out,'taste-inspect/report.json'),'utf8'));assert.equal(audit.designInspection.findings.filter(x=>x.level==='FAIL').length,0);
    stage='logout';await learner.getByLabel('Tài khoản của Nguyễn An').click();await learner.getByRole('button',{name:'Đăng xuất',exact:true}).click();await learner.waitForURL(/dang-nhap/);assert.equal(await learner.locator('.usage-page').count(),0);
    audit.assertions.push('API used_ratio and VN reset; three states, null/finite build maximum; no money DTO/UI','PG ledger fake costs with real projection; cache hits and bank quiz remain usable under personal/shared caps','Chat/document banners remain in layout; keyboard, 44px, reduced motion, real logout');
    assert.deepEqual(audit.pageErrors,[]);
  } catch(error) { audit.failure={stage,message:error.message,stack:error.stack};throw error;
  } finally {
    for(const {context,page,name} of contexts){await page.waitForLoadState('networkidle');const video=page.video();await context.close();if(video)await video.saveAs(path.join(out,name+'.webm'));}
    const results=await Promise.allSettled(pending);audit.pendingRejections=results.filter(r=>r.status==='rejected').map(r=>String(r.reason));
    await fs.writeFile(path.join(out,'audit.json'),JSON.stringify(audit,null,2)+'\n');await browser.close();
    assert.deepEqual(audit.pendingRejections,[]);assert.deepEqual(audit.privacyFailures,[]);
  }
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
