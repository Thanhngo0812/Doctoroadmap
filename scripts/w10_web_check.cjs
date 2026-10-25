const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..'), shared = path.resolve(root, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(shared, '.tmp/w01-browsers');
const { chromium } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const out = path.dirname(process.env.W10_RUNTIME);
const audit = { configurations: [], screens: [], accessibility: [], http: [], pageErrors: [], console: [], requests: [], assertions: [] };
let stage = 'bootstrap';
async function main() {
  const runtime = JSON.parse(await fs.readFile(process.env.W10_RUNTIME, 'utf8'));
  const { base, courseId: cid, moduleA: ma, moduleB: mb } = runtime;
  const api = base + '/api/v1/courses/' + cid, modulePage = base + '/khoa-hoc/' + cid + '/module/' + ma;
  const browser = await chromium.launch(), contexts = [], pending = [];
  async function userPage(name) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 },
      recordVideo: { dir: path.join(root, 'tmp/w10-video'), size: { width: 1280, height: 900 } } });
    const page = await context.newPage(); contexts.push({ context, page, name });
    page.on('pageerror', error => audit.pageErrors.push({ stage, message: error.message }));
    page.on('console', message => { if (message.type() === 'error') audit.console.push({ stage, message: message.text() }); });
    page.on('request', request => {
      if (request.url().startsWith(api) && request.method() === 'POST')
        audit.requests.push({ stage, path: new URL(request.url()).pathname, body: request.postDataJSON() });
    });
    page.on('response', response => {
      if (!response.url().startsWith(api)) return;
      const when = stage;
      pending.push((async () => {
        const type = response.headers()['content-type'] ?? '';
        const body = /json|event-stream|markdown/.test(type) ? await response.text() : null;
        if (/\/(quizzes|documents|library)/.test(response.url()) && body) {
          for (const value of ['"validation"', '"public_id"', '"_private"', 'res.cloudinary.com', 'PRIVATE_SOLVER_REASON'])
            assert.ok(!body.includes(value), value);
          if (/\/quizzes(?:\/[^/]+)?$/.test(new URL(response.url()).pathname) && !/\/submit|\/result/.test(response.url())) {
            for (const value of ['"correct_index"', '"is_correct"', '"explanation"', '"why_wrong"', '"answers"'])
              assert.ok(!body.includes(value), 'public quiz leaked ' + value);
          }
        }
        audit.http.push({ stage: when, path: new URL(response.url()).pathname, method: response.request().method(), status: response.status(), type, body });
      })().catch(error => { if (error.code === 'ERR_ASSERTION') throw error; audit.http.push({ stage: when, path: new URL(response.url()).pathname, status: response.status(), unavailableBody: error.message }); }));
    });
    return page;
  }
  const owner = await userPage('owner'), learner = await userPage('learner');
  async function login(page, name) {
    await page.goto(base + '/dang-nhap');
    await page.getByLabel('Email', { exact: true }).fill(name + '-w10@example.invalid');
    await page.getByLabel('Mật khẩu', { exact: true }).fill('W10 isolated browser passphrase!');
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
        const region = document.querySelector('dialog[open]') || document.querySelector('.content-page') || document.querySelector('.content-library');
        const targets = [...region.querySelectorAll('button:not(:disabled),a[href],select,textarea,label:has(input)')]
          .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
          .map(e => ({ label: e.getAttribute('aria-label') || e.textContent.trim().slice(0, 70), w: e.getBoundingClientRect().width, h: e.getBoundingClientRect().height }))
          .filter(row => row.w < 43.5 || row.h < 43.5);
        return { overflow: document.documentElement.scrollWidth > innerWidth + 1, targets };
      });
      assert.equal(layout.overflow, false, name + ' horizontal overflow');
      assert.deepEqual(layout.targets, [], name + ' 44px targets');
      await learner.evaluate(() => scrollTo({ top: 0, behavior: 'instant' }));
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
          if (!element?.closest('.katex,.content-page,.content-dialog')) return { selector, eligible: false };
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

    const smoke = process.env.W10_BROWSER_SMOKE === '1';
    let first = true, lastDid = '', lastAid = '';
    for (const width of (smoke ? [1280] : [390, 768, 1280])) for (const theme of (smoke ? ['light'] : ['light', 'dark'])) for (const reduced of (smoke ? [false] : [false, true])) {
      stage = 'matrix:' + width + ':' + theme + ':' + reduced; audit.configurations.push({ width, theme, reduced });
      await control({ action: 'advance' });
      await learner.setViewportSize({ width, height: 900 }); await learner.emulateMedia({ colorScheme: theme, reducedMotion: reduced ? 'reduce' : 'no-preference' });
      await learner.goto(modulePage);
      if (await learner.locator('html').getAttribute('data-theme') !== theme)
        await learner.getByRole('button', { name: theme === 'dark' ? 'Bật chế độ tối' : 'Bật chế độ sáng' }).click();
      const library = learner.getByRole('region', { name: 'Tài liệu & Quiz của module' });
      await library.getByRole('link', { name: /Ghi chú ôn tập/ }).first().waitFor();
      await capture('library-here', width === 390 || width === 1280);
      await library.getByRole('button', { name: /Tạo ở nơi khác/ }).click();
      assert.ok(await library.getByRole('link', { name: /Ghi chú ôn tập/ }).count() >= 2);
      await capture('library-elsewhere', width === 768);
      await library.getByRole('link', { name: 'Làm quiz', exact: true }).click();
      await learner.locator('.content-question input').first().waitFor();
      const early = learner.locator('.content-question input').first();
      const earlyChoice = { item: await early.getAttribute('name'), option: await early.getAttribute('value') };
      await early.check();
      if (first) {
        const probe = await control({ action: 'probe' });
        assert.equal(probe.quizWaiting, true);
        assert.equal(Object.keys(probe.answers).length, 0, 'no completed attempt before held concept finishes');
        await capture('quiz-streaming');
        await control({ action: 'release-quiz' });
      }
      await learner.waitForURL(url => /\/quiz\/qa_/.test(url.pathname));
      const aid = new URL(learner.url()).pathname.split('/').at(-1); lastAid = aid;
      assert.equal(await learner.locator('input[name="' + earlyChoice.item + '"][value="' + earlyChoice.option + '"]').isChecked(), true, 'early selection survives final');
      assert.equal(await learner.getByRole('button', { name: 'Mở khung trợ lý' }).count(), 0);
      const q = await (await learner.request.get(api + '/quizzes/' + aid)).json();
      const answerMap = (await control({ action: 'probe' })).answers[aid];
      for (const [index, item] of q.items.entries()) {
        const option = index ? answerMap[item.item_id] : item.options.find(o => o.option_id !== answerMap[item.item_id]).option_id;
        await learner.locator('input[name="' + item.item_id + '"][value="' + option + '"]').check();
      }
      await capture('quiz-ready', width === 390 || width === 1280);
      if (first) {
        await learner.route('**/quizzes/' + aid + '/submit', async route => {
          const response = await route.fetch();
          audit.lostSubmit = { response: await response.json(), request: route.request().postDataJSON() };
          await route.abort('failed');
        }, { times: 1 });
      }
      await learner.getByRole('button', { name: 'Nộp bài', exact: true }).click();
      if (first) {
        await learner.getByRole('button', { name: 'Thử nộp lại' }).waitFor();
        await capture('submit-network-error');
        await learner.getByRole('button', { name: 'Thử nộp lại' }).click();
      }
      await learner.getByRole('heading', { name: 'Kết quả quiz', exact: true }).waitFor();
      const grade = await (await learner.request.get(api + '/quizzes/' + aid + '/result')).json();
      assert.equal(grade.correct_count, grade.question_count - 1);
      assert.ok(grade.results[0].why_wrong); assert.ok(grade.results[0].evidence.length);
      if (first) assert.deepEqual(grade, audit.lostSubmit.response, 'retry after lost HTTP response reuses exact saved grade');
      await capture('quiz-result', true);
      const beforeReload = audit.requests.filter(row => row.path.endsWith('/submit')).length;
      await learner.reload(); await learner.getByRole('heading', { name: 'Kết quả quiz', exact: true }).waitFor();
      assert.equal(audit.requests.filter(row => row.path.endsWith('/submit')).length, beforeReload);
      await learner.goto(modulePage); await library.getByRole('button', { name: 'Tạo tài liệu', exact: true }).click();
      const dialog = learner.getByRole('dialog', { name: 'Tạo tài liệu học tập' });
      await dialog.waitFor();
      await settled();
      if (reduced) assert.equal(await dialog.evaluate(e => getComputedStyle(e).animationName), 'none');
      if (first) {
        const boxes = dialog.getByRole('checkbox');
        const beforePosts = audit.requests.filter(row => row.path.endsWith('/documents')).length;
        for (let i = 1; i < 6; i++) await boxes.nth(i).check();
        await dialog.getByText('Chọn tối đa 5 module. Bỏ bớt một module để tiếp tục.').waitFor();
        assert.equal(await dialog.getByRole('button', { name: 'Tạo tài liệu', exact: true }).isDisabled(), true);
        assert.equal(audit.requests.filter(row => row.path.endsWith('/documents')).length, beforePosts);
        await capture('document-scope-error', true);
        for (let i = 0; i < 6; i++) await boxes.nth(i).uncheck();
      } else await dialog.getByRole('checkbox').nth(0).uncheck();
      await dialog.getByRole('checkbox').nth(1).check();
      await dialog.getByRole('textbox').fill('Tạo bảng công thức và một ví dụ từng bước.');
      await capture('document-create', true);
      if (first) await control({ action: 'document-mode', mode: 'pause' });
      await dialog.getByRole('button', { name: 'Tạo tài liệu', exact: true }).click();
      if (first) {
        await learner.locator('.content-draft').waitFor();
        await capture('document-streaming');
        await control({ action: 'release-document' });
      }
      await learner.waitForURL(url => /\/tai-lieu\/[^/]+$/.test(url.pathname));
      lastDid = new URL(learner.url()).pathname.split('/').at(-1);
      await learner.getByRole('link', { name: 'Tải Markdown' }).waitFor();
      assert.equal(await learner.locator('.content-document-body img').count(), 0);
      await capture('document-view', true);
      const source = learner.locator('.content-document-body .lecture-citation').first();
      if (await source.count()) {
        await source.click(); await learner.locator('.source-viewer img').waitFor();
        await learner.locator('.source-viewer img').evaluate(image => image.complete ? Promise.resolve() : new Promise(resolve => image.addEventListener('load', resolve, { once: true })));
        await capture('document-source'); await learner.locator('.source-viewer').getByRole('button', { name: 'Đóng', exact: true }).click();
      }
      if (first) {
        const downloadPromise = learner.waitForEvent('download');
        await learner.getByRole('link', { name: 'Tải Markdown' }).click();
        const download = await downloadPromise; await download.saveAs(path.join(out, 'document-export.md'));
        assert.match(await fs.readFile(path.join(out, 'document-export.md'), 'utf8'), /\[\^S1\]: tr\./);
        audit.export = { file: 'document-export.md', via: 'real authenticated HTTP download' };
      }
      const grouping = await (await learner.request.get(api + '/library?scope=module%3A' + mb)).json();
      assert.equal(grouping.items.find(row => row.id === lastDid).group, 'elsewhere');
      first = false;
    }
    stage = 'failure';
    await control({ action: 'advance' }); await control({ action: 'document-mode', mode: 'failure' });
    await learner.goto(modulePage); await learner.getByRole('button', { name: 'Tạo tài liệu', exact: true }).click();
    await learner.getByRole('dialog').getByRole('button', { name: 'Tạo tài liệu', exact: true }).click();
    await learner.getByRole('dialog').getByRole('alert').waitFor(); await capture('document-failure', true);
    assert.equal(await learner.getByRole('dialog').getByRole('button', { name: 'Thử lại' }).isEnabled(), true);
    await learner.getByRole('button', { name: 'Đóng tạo tài liệu' }).click();
    stage = 'privacy';
    const outsider = await userPage('outsider'); await login(outsider, 'outsider');
    assert.equal((await outsider.request.get(api + '/quizzes/' + lastAid)).status(), 404);
    assert.equal((await outsider.request.get(api + '/documents/' + lastDid)).status(), 404);
    const removed = await owner.request.delete(api + '/members/' + runtime.learnerId, { headers }); assert.equal(removed.status(), 200);
    assert.equal((await learner.request.get(api + '/documents/' + lastDid)).status(), 404);
    await learner.goto(base + '/khoa-hoc/' + cid + '/tai-lieu/' + lastDid);
    await learner.getByRole('heading', { name: 'Chưa mở được tài liệu' }).waitFor();
    audit.assertions.push('HTTP/PG/core Quiz3 and Document3; streamed items before completion', 'Actual shuffled option IDs and atomic/idempotent retry after lost HTTP response',
      'No assistant while taking quiz; reload restores saved result', 'Core group independent from origin; direct document home A/content B is elsewhere in B',
      'Six-module UI prevents POST; real Markdown export/source PDF; errors have retry', 'Outsider and removed member denied next HTTP request; 0 external provider calls');
    assert.deepEqual(audit.pageErrors, []);
    console.log(JSON.stringify({ screens: audit.screens.length, axe: audit.accessibility.length, http: audit.http.length }));
  } finally {
    for (const { context, page, name } of contexts) { const video = page.video(); await context.close(); if (video) await video.saveAs(path.join(out, name + '.webm')); }
    await Promise.allSettled(pending);
    await fs.writeFile(path.join(out, 'audit.json'), JSON.stringify(audit, null, 2) + '\n'); await browser.close();
  }
}
main().catch(error => { console.error(error.stack); process.exitCode = 1; });
