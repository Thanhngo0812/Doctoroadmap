const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..'), shared = path.resolve(root, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(shared, '.tmp/w01-browsers');
const { chromium } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const out = path.dirname(process.env.W08_RUNTIME);
const scrub = value => String(value).replace(/(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{43}(?![A-Za-z0-9_-])/g, '[REDACTED]');
const audit = { screens: [], accessibility: [], http: [], errors: [], expectedConsole: [], failedRequests: [], pageErrors: [], assertions: [], configurations: [] };
const smoke = process.env.W08_BROWSER_SMOKE === '1';
audit.scope = smoke ? 'development smoke; not the final matrix' : 'full 12-configuration matrix';
let stage = 'bootstrap';

async function main() {
  const runtime = JSON.parse(await fs.readFile(process.env.W08_RUNTIME, 'utf8'));
  const { base, courseId: cid, moduleId: mid, nodeId: nid } = runtime;
  const moduleUrl = `${base}/khoa-hoc/${cid}/module/${encodeURIComponent(mid)}`;
  const lessonUrl = `${moduleUrl}/khai-niem/${encodeURIComponent(nid)}`;
  const api = `${base}/api/v1/courses/${cid}`;
  const browser = await chromium.launch();
  audit.browserVersion = browser.version();
  const contexts = [], pending = [];
  async function makePage(name) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 },
      recordVideo: { dir: path.join(root, 'tmp/w08-video'), size: { width: 1280, height: 900 } } });
    // DevTools may discard SSE bodies. Tee the actual fetch response without changing requests or responses.
    await context.addInitScript(() => {
      const originalFetch = window.fetch;
      window.__w08WireStreams = [];
      window.fetch = async function (...args) {
        const response = await originalFetch.apply(this, args);
        if (response.headers.get('content-type')?.startsWith('text/event-stream')) {
          const record = { url: response.url, body: null, completed: false, error: null };
          window.__w08WireStreams.push(record);
          response.clone().text().then(body => { record.body = body; record.completed = true; },
            error => { record.error = String(error); record.completed = true; });
        }
        return response;
      };
    });
    const page = await context.newPage(); contexts.push({ context, page, name });
    page.on('pageerror', error => audit.pageErrors.push({ stage, message: scrub(error.message) }));
    page.on('console', message => {
      if (message.type() !== 'error') return;
      const text = scrub(message.text());
      const location = message.location().url;
      const pathname = location?.startsWith(base) ? new URL(location).pathname : location;
      const expected = (stage === 'bootstrap' && pathname === '/api/v1/me' && text.includes('401'))
        || (stage === 'rollback' && pathname === `/api/v1/courses/${cid}/progress/${nid}` && text.includes('500'))
        || (stage === 'related-rollback' && pathname?.startsWith(`/api/v1/courses/${cid}/progress/`) && text.includes('500'))
        || (stage === 'removed' && [`/api/v1/courses/${cid}`, `/api/v1/courses/${cid}/roadmap`, `/api/v1/courses/${cid}/progress`].includes(pathname) && text.includes('404'))
        || (stage.startsWith('axe:') && text.includes('Content Security Policy') && text.includes('fonts.googleapis.com'));
      (expected ? audit.expectedConsole : audit.errors).push({ stage, path: pathname, text });
    });
    page.on('requestfailed', request => {
      const url = new URL(request.url());
      const reason = request.failure()?.errorText;
      if (url.origin === base && /\/lecture\/stream$/.test(url.pathname) && reason === 'net::ERR_ABORTED') {
        audit.expectedConsole.push({ stage, path: url.pathname, text: 'SSE cancelled by route change; separate HTTP/PG disconnect assertion covers completion' });
        return;
      }
      if (stage.startsWith('axe:') && url.hostname === 'fonts.googleapis.com' && /CSP|csp/.test(reason ?? '')) return;
      audit.failedRequests.push({ stage, path: url.pathname, error: reason });
    });
    page.on('response', response => {
      const url = new URL(response.url());
      if (url.origin !== base || !url.pathname.startsWith(`/api/v1/courses/${cid}`)) return;
      const at = stage;
      pending.push((async () => {
        const type = response.headers()['content-type'] ?? '';
        const body = /json|event-stream/.test(type) ? scrub(await response.text()) : null;
        if (body) {
          assert.ok(!body.includes('"validation"') && !body.includes('"public_id"'));
          assert.ok(!body.includes('res.cloudinary.com') && !body.includes('"sections"') && !body.includes('"bridge"'));
        }
        const rawHeaders = response.headers();
        const headers = Object.fromEntries(['cache-control', 'x-page-count', 'x-content-type-options', 'referrer-policy']
          .filter(key => rawHeaders[key]).map(key => [key, rawHeaders[key]]));
        audit.http.push({ stage: at, path: url.pathname, method: response.request().method(), status: response.status(), contentType: type, headers, body });
      })().catch(error => {
        if (error.code === 'ERR_ASSERTION') audit.errors.push({ stage: at, path: url.pathname, text: scrub(error.message) });
        else audit.http.push({ stage: at, path: url.pathname, status: response.status(), unavailableBody: scrub(error.message) });
      }));
    });
    await page.route('https://evil.example/**', route => { audit.errors.push({ stage, text: 'Untrusted Markdown attempted an external request' }); return route.abort(); });
    return page;
  }
  async function login(page, identity) {
    await page.goto(`${base}/dang-nhap`);
    await page.getByLabel('Email', { exact: true }).fill(`${identity}-w08@example.invalid`);
    await page.getByLabel('Mật khẩu', { exact: true }).fill('W08 isolated browser passphrase!');
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await page.waitForURL(`${base}/khoa-hoc`);
  }
  const owner = await makePage('owner'), learner = await makePage('learner');
  try {
    await login(owner, 'owner'); await login(learner, 'learner');
    const me = await (await owner.request.get(`${base}/api/v1/me`)).json();
    const headers = { Origin: base, 'X-CSRF-Token': me.csrf_token };
    async function control(data) {
      const result = await owner.request.post(base + runtime.controlPath, { headers, data });
      assert.equal(result.status(), 200, `fixture control ${data.action}: ${await result.text()}`);
      return result.json();
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
          if (!element?.closest('.katex')) return { selector, eligible: false };
          const ancestors = [];
          for (let current = element; current; current = current.parentElement) ancestors.push(current);
          let background = [1, 1, 1, 1];
          for (const ancestor of ancestors.reverse()) background = blend(color(getComputedStyle(ancestor).backgroundColor), background);
          const foreground = color(getComputedStyle(element).color);
          foreground[3] *= ancestors.reduce((opacity, ancestor) => opacity * Number(getComputedStyle(ancestor).opacity), 1);
          const ink = blend(foreground, background), light = luminance(ink), ground = luminance(background);
          return { selector, eligible: true, foreground, background, contrast: (Math.max(light, ground) + .05) / (Math.min(light, ground) + .05) };
        });
      }, nodes.map(node => node.target.length === 1 ? node.target[0] : '__unsupported_shadow_target__'));
    }
    function assertMathContrast(rows) {
      for (const row of rows) assert.ok(row.eligible && row.contrast >= 4.5, `KaTeX contrast must reach 4.5:1: ${JSON.stringify(row)}`);
    }
    async function capture(page, name, width, theme, axe = false) {
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      assert.equal(await page.locator('html').getAttribute('data-theme'), theme, 'screenshot theme must match the real document');
      await page.evaluate(() => document.fonts.ready);
      const layout = await page.evaluate(() => {
        const visible = element => element.getClientRects().length && getComputedStyle(element).visibility !== 'hidden';
        const badTargets = [...document.querySelectorAll('button:not(:disabled),a[href],summary,label.learning-check,.lecture-progress label')]
          .filter(visible).filter(element => !element.closest('details:not([open])') || element.tagName === 'SUMMARY')
          .filter(element => !element.classList.contains('skip-link'))
          .map(element => ({ label: element.getAttribute('aria-label') ?? element.textContent.trim().slice(0, 65), width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height }))
          .filter(box => box.width < 43.5 || box.height < 43.5);
        return { overflow: document.documentElement.scrollWidth > innerWidth + 1, badTargets };
      });
      assert.equal(layout.overflow, false, `${name} ${width} must not overflow`);
      assert.deepEqual(layout.badTargets, [], `${name} ${width} must provide 44px targets`);
      const reduced = await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
      const file = `${name}-${width}-${theme}${reduced ? '-reduced' : ''}.png`;
      await page.screenshot({ path: path.join(out, file), fullPage: true });
      audit.screens.push({ state: name, width, theme, reducedMotion: reduced, file, layout });
      if (axe) {
        stage = `axe:${name}:${theme}`;
        const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
        const manualMath = [], unreviewed = [];
        for (const finding of result.incomplete) {
          const supported = finding.id === 'color-contrast' && finding.nodes.every(node => node.any.every(check =>
            check.id === 'color-contrast' && check.message === 'Element content is too short to determine if it is actual text content'));
          const measured = supported ? await mathContrast(page, finding.nodes) : [];
          if (!supported || !measured.every(row => row.eligible)) unreviewed.push(finding);
          else {
            assertMathContrast(measured);
            manualMath.push(...measured);
          }
        }
        audit.accessibility.push({ state: name, width, theme, violations: result.violations, incomplete: result.incomplete,
          manualMathContrast: manualMath, unreviewedIncomplete: unreviewed });
        assert.deepEqual(result.violations, [], `Axe ${name} ${theme}`);
        assert.deepEqual(unreviewed, [], `Axe incomplete requires review ${name} ${theme}`);
        if (manualMath.length && !audit.mathContrastCounterexample) {
          const saved = await page.locator('.katex').evaluateAll(elements => elements.map(element => element.getAttribute('style')));
          try {
            const background = `rgb(${manualMath[0].background.slice(0, 3).map(channel => Math.round(channel * 255)).join(',')})`;
            await page.locator('.katex').evaluateAll((elements, color) => elements.forEach(element => element.style.setProperty('color', color, 'important')), background);
            const bad = await mathContrast(page, result.incomplete.flatMap(finding => finding.nodes));
            assert.throws(() => assertMathContrast(bad), { code: 'ERR_ASSERTION' }, 'same guard must reject invisible math');
            audit.mathContrastCounterexample = { mutatedOnlyDOM: true, badRatios: bad.map(row => row.contrast), rejectedBySameThreshold: true };
          } finally {
            await page.locator('.katex').evaluateAll((elements, styles) => elements.forEach((element, index) => styles[index] === null ? element.removeAttribute('style') : element.setAttribute('style', styles[index])), saved);
          }
          const restored = await mathContrast(page, result.incomplete.flatMap(finding => finding.nodes));
          assertMathContrast(restored);
        }
      }
    }
    for (const width of (smoke ? [1280] : [390, 768, 1280])) for (const theme of (smoke ? ['light'] : ['light', 'dark'])) for (const reduced of (smoke ? [false] : [false, true])) {
      await learner.setViewportSize({ width, height: 900 });
      await learner.emulateMedia({ colorScheme: theme, reducedMotion: reduced ? 'reduce' : 'no-preference' });
      await control({ action: 'scenario', name: 'normal' });
      stage = `module:${width}:${theme}`;
      await learner.goto(moduleUrl);
      await learner.locator('.learning-module-intro h1').waitFor();
      if (await learner.locator('html').getAttribute('data-theme') !== theme) {
        await learner.getByRole('button', { name: theme === 'dark' ? 'Bật chế độ tối' : 'Bật chế độ sáng' }).click();
      }
      await capture(learner, 'module', width, theme, width === 1280);
      stage = `waiting:${width}:${theme}`;
      await learner.goto(lessonUrl);
      await learner.getByText('Đang soạn bài…', { exact: true }).waitFor();
      if (reduced) assert.ok((await learner.locator('.task-wait img').getAttribute('src')).endsWith('.png'));
      else assert.ok((await learner.locator('.task-wait source').getAttribute('srcset')).endsWith('.webp'));
      await capture(learner, 'waiting', width, theme, false);
      stage = `streaming:${width}:${theme}`;
      await learner.getByText(/Bài học được viết từng phần/).waitFor();
      assert.equal((await control({ action: 'probe' })).finished, false, 'text must be visible before the fake model finishes');
      await capture(learner, 'streaming', width, theme);
      await control({ action: 'release' });
      await learner.getByText('Xem đáp án', { exact: true }).waitFor();
      stage = `ready:${width}:${theme}`;
      assert.equal(await learner.locator('.lecture-self-check details').getAttribute('open'), null);
      assert.ok(await learner.locator('.katex').count() >= 2);
      assert.equal(await learner.locator('.lecture-body a').filter({ hasText: '[S999]' }).count(), 0);
      await capture(learner, 'ready', width, theme, width === 1280);
      const prerequisite = learner.locator('.lecture-prerequisites details').first();
      assert.equal(await prerequisite.getAttribute('open'), null);
      await prerequisite.locator('summary').click();
      stage = `prerequisite:${width}:${theme}`;
      await capture(learner, 'prerequisite-open', width, theme);
      await learner.getByText('Xem đáp án', { exact: true }).click();
      stage = `self-check:${width}:${theme}`;
      await capture(learner, 'self-check-open', width, theme);
      const source = learner.locator('.lecture-body button.lecture-citation').first();
      const label = await source.getAttribute('aria-label');
      const sourcePage = Number(label.match(/trang (\d+)/)[1]);
      await source.click();
      const dialog = learner.getByRole('dialog');
      await dialog.locator('img').waitFor();
      await dialog.locator('img').evaluate(image => image.decode());
      assert.ok((await dialog.locator('img').getAttribute('alt')).includes(String(sourcePage)));
      stage = `source:${width}:${theme}`;
      await capture(learner, 'source', width, theme, width === 1280);
      if (width === 1280) {
        const region = dialog.getByRole('region', { name: `Ảnh trang ${sourcePage}` });
        await region.focus();
        assert.equal(await region.evaluate(element => element === document.activeElement), true);
        await learner.keyboard.press('ArrowDown');
        await learner.waitForFunction(() => document.querySelector('.source-viewer__image').scrollTop > 0);
      }
      if (sourcePage < runtime.sourcePageCount) {
        await dialog.getByRole('button', { name: 'Trang sau' }).click();
        await dialog.getByRole('img', { name: `Trang ${sourcePage + 1} của tài liệu` }).waitFor();
        await dialog.locator('img').evaluate(image => image.decode());
        await dialog.getByRole('button', { name: 'Trang trước' }).click();
        await dialog.getByRole('img', { name: `Trang ${sourcePage} của tài liệu` }).waitFor();
        await dialog.locator('img').evaluate(image => image.decode());
      }
      await learner.keyboard.press('Escape');
      await dialog.waitFor({ state: 'hidden' });
      await learner.waitForFunction(value => document.activeElement?.getAttribute('aria-label') === value, label);
      assert.equal(await source.evaluate(element => element === document.activeElement), true, 'dialog returns keyboard focus');
      const cached = await learner.request.get(`${api}/concepts/${encodeURIComponent(nid)}/lecture`);
      const lesson = await cached.json();
      assert.equal(lesson.sources.find(row => row.label === label.match(/Nguồn (S\d+)/)[1]).page, sourcePage);
      const calls = (await control({ action: 'probe' })).calls;
      await learner.reload(); await learner.getByText('Xem đáp án', { exact: true }).waitFor();
      assert.equal((await control({ action: 'probe' })).calls, calls, 'reload must use the shared cache');
      await control({ action: 'scenario', name: 'empty' });
      stage = `failure:${width}:${theme}`;
      await learner.reload(); await learner.getByRole('heading', { name: 'Chưa có bài giảng' }).waitFor();
      assert.ok((await learner.locator('.lecture-failure [role=alert]').textContent()).trim());
      await capture(learner, 'failure', width, theme, width === 1280);
      const beforeRetry = (await control({ action: 'probe' })).calls;
      await learner.getByRole('button', { name: 'Thử lại', exact: true }).click();
      await learner.getByRole('heading', { name: 'Chưa có bài giảng' }).waitFor();
      assert.equal((await control({ action: 'probe' })).calls, beforeRetry, 'failure within the core negative-cache window must not trigger another call');
      const mediaObserved = await learner.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
      assert.equal(mediaObserved, reduced);
      audit.configurations.push({ width, theme, reducedMotion: reduced, mediaObserved, firstDeltaBeforeFinish: true, sourcePage, sourcePaging: true, cacheReuse: true });
    }
    assert.equal(audit.configurations.length, smoke ? 1 : 12);
    await learner.setViewportSize({ width: 1280, height: 900 });
    if (await learner.locator('html').getAttribute('data-theme') !== 'dark') await learner.getByRole('button', { name: 'Bật chế độ tối' }).click();
    for (const name of ['tail', 'no-self-check', 'unsafe']) {
      await control({ action: 'scenario', name }); stage = name;
      await learner.goto(lessonUrl);
      if (name === 'tail') {
        await learner.getByText('Bài được rút gọn', { exact: true }).waitFor();
        assert.ok((await learner.locator('.lecture-body').textContent()).includes('Phần đã gửi được giữ lại.'));
      } else if (name === 'no-self-check') {
        await learner.getByText(/Bài này không có câu hỏi/).waitFor();
        assert.equal(await learner.locator('.lecture-self-check').count(), 0);
      } else {
        await learner.getByText(/Nội dung an toàn/).waitFor();
        await learner.locator('.lecture-body .lecture-markdown').waitFor();
        assert.equal(await learner.evaluate(() => window.__w08pwned), undefined);
        assert.equal(await learner.locator('.lecture-body img,.lecture-body .w08-injected,.lecture-body script').count(), 0);
        assert.equal(await learner.locator('.lecture-body a[href^="javascript:"]').count(), 0);
      }
      await capture(learner, name, 1280, 'dark');
    }
    await control({ action: 'scenario', name: 'no-self-check' });
    await learner.goto(lessonUrl); await learner.getByText(/Bài này không có câu hỏi/).waitFor();
    await control({ action: 'progress-fail' }); stage = 'rollback';
    const mark = learner.getByRole('checkbox', { name: 'Đánh dấu bài học đã học' });
    assert.equal(await mark.isChecked(), false);
    await mark.check();
    await learner.getByText(/Chưa lưu được tiến độ/).first().waitFor();
    assert.equal(await mark.isChecked(), false, 'failed PostgreSQL write must roll back the mark');
    await capture(learner, 'progress-rollback', 1280, 'dark', true);
    await control({ action: 'progress-ok' });
    await mark.check(); await learner.getByText('Đang lưu…', { exact: true }).waitFor({ state: 'hidden' });
    assert.equal(await mark.isChecked(), true);
    await control({ action: 'scenario', name: 'normal' }); await control({ action: 'release' });
    await learner.reload(); await learner.getByText('Xem đáp án', { exact: true }).waitFor();
    stage = 'ready-after-save'; await capture(learner, 'saved', 1280, 'dark');
    // R-W08-1: while A remains open, sidebar B updates every visible related badge without another lecture request.
    const lecture = await (await learner.request.get(`${api}/concepts/${encodeURIComponent(nid)}/lecture`)).json();
    const related = lecture.prerequisites.find(row => row.recall.module_id === mid);
    assert.ok(related, 'fixture must expose a prerequisite in the current sidebar');
    const bid = related.recall.node_id;
    const relatedMark = learner.getByRole('checkbox', { name: `Đã học: ${related.recall.name}`, exact: true });
    const badge = learner.locator('.lecture-prerequisites details').filter({ has: learner.locator('summary', { hasText: related.recall.name }) }).locator('summary > span:last-child');
    const badgeState = async value => assert.equal((await badge.textContent()).trim(), value);
    const beforeCalls = (await control({ action: 'probe' })).calls;
    await Promise.allSettled(pending);
    const beforeLectureRequests = audit.http.filter(row => row.path?.includes('/lecture')).length;
    stage = 'related-save';
    await relatedMark.check(); await relatedMark.waitFor({ state: 'visible' });
    await learner.waitForFunction(label => !document.querySelector(`input[aria-label="${label}"]`).disabled, `Đã học: ${related.recall.name}`);
    await badgeState('Đã học');
    const savedRelated = await control({ action: 'progress-probe', node_id: bid });
    assert.equal(savedRelated.record?.state, 'learned');
    await capture(learner, 'related-saved', 1280, 'dark');
    await control({ action: 'progress-fail' }); stage = 'related-rollback';
    await relatedMark.uncheck();
    await learner.getByText(/Chưa lưu được tiến độ/).first().waitFor();
    assert.equal(await relatedMark.isChecked(), true); await badgeState('Đã học');
    const rolledBack = await control({ action: 'progress-probe', node_id: bid });
    assert.equal(rolledBack.record?.state, 'learned');
    await capture(learner, 'related-rollback', 1280, 'dark');
    await control({ action: 'progress-ok' }); stage = 'related-unmark';
    await relatedMark.uncheck();
    await learner.waitForFunction(label => !document.querySelector(`input[aria-label="${label}"]`).disabled, `Đã học: ${related.recall.name}`);
    await badgeState('Chưa học');
    const unmarked = await control({ action: 'progress-probe', node_id: bid });
    assert.equal(unmarked.record?.state, 'not_learned');
    assert.equal((await control({ action: 'probe' })).calls, beforeCalls);
    await Promise.allSettled(pending);
    assert.equal(audit.http.filter(row => row.path?.includes('/lecture')).length, beforeLectureRequests, 'badge changes must not fetch/regenerate a lecture');
    audit.relatedProgress = { nodeId: bid, saved: savedRelated, rollback: rolledBack, unmarked, noLectureRefetch: true };
    // R-W08-2: HTTP uses the actual core splitter; React also protects against older/full text deltas.
    audit.selfCheckHeadings = [];
    for (const name of ['heading-two', 'heading-four', 'heading-indent', 'heading-colon', 'heading-tab']) {
      stage = name; await control({ action: 'scenario', name }); await learner.goto(lessonUrl);
      await learner.getByText('Phần chính hiện ngay.', { exact: true }).waitFor();
      assert.equal((await control({ action: 'probe' })).finished, false);
      assert.equal(await learner.getByText('Đáp án riêng phải gập.', { exact: true }).count(), 0);
      await control({ action: 'release' });
      const answer = learner.getByText('Đáp án riêng phải gập.', { exact: true });
      await answer.waitFor({ state: 'attached' }); assert.equal(await answer.isVisible(), false);
      await learner.getByText('Xem đáp án', { exact: true }).click(); assert.equal(await answer.isVisible(), true);
      await learner.waitForFunction(() => window.__w08WireStreams.findLast(row => row.url.endsWith('/lecture/stream'))?.completed);
      const stream = await learner.evaluate(() => window.__w08WireStreams.findLast(row => row.url.endsWith('/lecture/stream')));
      assert.equal(stream.error, null);
      assert.equal(typeof stream.body, 'string', 'inspect actual HTTP/SSE, independently from the React filter');
      assert.ok(!/"validation"|"public_id"|res\.cloudinary\.com/.test(stream.body));
      (audit.sseWire ??= []).push({ scenario: name, url: new URL(stream.url).pathname, body: scrub(stream.body),
        collectedBy: 'Response.clone().text() of the actual browser fetch response; no response mocking' });
      const deltaText = stream.body.split(/\r?\n\r?\n/).filter(frame => /^event: delta\r?\n/.test(frame))
        .map(frame => JSON.parse(frame.split(/\r?\n/).find(line => line.startsWith('data:')).slice(5)).text).join('');
      assert.equal(deltaText.trim(), 'Phần chính hiện ngay.', 'SA70 must keep the whole self-check out of HTTP deltas');
      audit.selfCheckHeadings.push({ scenario: name, hiddenBeforeFinal: true, foldedFinal: true, opensOnRequest: true, httpDeltasExcludeSelfCheck: true });
      await capture(learner, name, 1280, 'dark');
    }
    stage = 'unsplit'; await control({ action: 'scenario', name: 'unsplit' }); await learner.goto(lessonUrl);
    await learner.getByText('Đoạn cuối thiếu khuôn hỏi đáp vẫn phải được giữ ở final.', { exact: true }).waitFor();
    assert.equal(await learner.locator('.lecture-self-check').count(), 0);
    await capture(learner, 'unsplit-final', 1280, 'dark');
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
    const snapshotPath = path.join(root, 'tmp/w08-inspect.html');
    await fs.writeFile(snapshotPath, snapshot.replace(/<head([^>]*)>/i, `<head$1><base href="${base}/">`));
    await fs.mkdir(path.join(root, 'tmp/w08-taste-profiles'), { recursive: true });
    const inspected = spawnSync(process.execPath, [path.join(shared, '.agents/skills/design-taste-frontend/scripts/inspect.mjs'), snapshotPath,
      '--out', path.join(out, 'taste-inspect'), '--widths', '1280,768,390', '--app', '--json'],
      { cwd: root, encoding: 'utf8', timeout: 180000, env: { ...process.env, TASTE_SKILL_TMP: path.join(root, 'tmp/w08-taste-profiles') } });
    await fs.writeFile(path.join(out, 'taste-inspector.log'), scrub(`${inspected.stdout ?? ''}${inspected.stderr ?? ''}`));
    assert.ok([0, 1].includes(inspected.status));
    audit.designInspection = JSON.parse(await fs.readFile(path.join(out, 'taste-inspect/report.json'), 'utf8'));
    assert.equal(audit.designInspection.findings.filter(finding => finding.level === 'FAIL').length, 0, 'taste inspector failures must be fixed');
    // The next HTTP request after removal must fail, including source and media.
    stage = 'removed';
    const removed = await owner.request.delete(`${api}/members/${runtime.learnerId}`, { headers });
    assert.equal(removed.status(), 200);
    for (const endpoint of [`/concepts/${encodeURIComponent(nid)}/lecture`, `/concepts/${encodeURIComponent(nid)}/lecture/stream`, '/source/pages/1', '/source']) {
      const response = await learner.request.get(api + endpoint, { maxRedirects: 0 });
      assert.equal(response.status(), 404); assert.equal((await response.json()).error.code, 'not_found');
      audit.http.push({ stage, path: new URL(api + endpoint).pathname, status: 404, body: scrub(await response.text()) });
    }
    await learner.reload(); await learner.getByRole('heading', { name: 'Chưa thể mở trang học' }).waitFor();
    audit.assertions.push('real SA64 + HTTP + PostgreSQL, fake model/media/mail only', 'first delta visible before completion, reload reuses cache',
      'Markdown/LaTeX and source page mapping safe; unknown labels preserved; self-check collapsed/null',
      'real PostgreSQL write failure rolls back progress; subsequent write succeeds', 'member removal denies the next lecture/source request',
      '390/768/1280 in both themes; browser reduced motion, keyboard, 44px targets and scoped Axe');
    await Promise.allSettled(pending);
    assert.deepEqual(audit.errors, []); assert.deepEqual(audit.pageErrors, []); assert.deepEqual(audit.failedRequests, []);
    console.log(JSON.stringify({ screens: audit.screens.length, axe: audit.accessibility.length, http: audit.http.length }));
  } finally {
    await Promise.allSettled(pending);
    for (const { context, page, name } of contexts) {
      const video = page.video(); await context.close(); if (video) await video.saveAs(path.join(out, `${name}.webm`));
    }
    await fs.writeFile(path.join(out, 'audit.json'), JSON.stringify(audit, null, 2) + '\n');
    await browser.close();
  }
}
main().catch(error => { console.error(scrub(error.stack)); process.exitCode = 1; });
