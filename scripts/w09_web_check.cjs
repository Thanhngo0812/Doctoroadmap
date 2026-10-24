const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..'), shared = path.resolve(root, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(shared, '.tmp/w01-browsers');
const { chromium } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(shared, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const out = path.dirname(process.env.W09_RUNTIME);
const audit = { configurations: [], screens: [], accessibility: [], http: [], pageErrors: [], console: [], requests: [], assertions: [] };
let stage = 'bootstrap';
async function main() {
  const runtime = JSON.parse(await fs.readFile(process.env.W09_RUNTIME, 'utf8'));
  const { base, courseId: cid, moduleId: mid, nodeId: nid } = runtime;
  const api = `${base}/api/v1/courses/${cid}`, roadmap = `${base}/khoa-hoc/${cid}`;
  const lesson = `${roadmap}/module/${encodeURIComponent(mid)}/khai-niem/${encodeURIComponent(nid)}`;
  const browser = await chromium.launch(); audit.browserVersion = browser.version();
  const contexts = [], pending = [];
  async function pageFor(name) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 },
      recordVideo: { dir: path.join(root, 'tmp/w09-video'), size: { width: 1280, height: 900 } } });
    await context.addInitScript(() => {
      const original = window.fetch; window.__w09Streams = [];
      window.fetch = async function (...args) {
        const response = await original.apply(this, args);
        if (response.headers.get('content-type')?.startsWith('text/event-stream')) {
          const row = { url: response.url, body: null, completed: false };
          window.__w09Streams.push(row);
          response.clone().text().then(body => { row.body = body; row.completed = true; }, error => { row.error = String(error); row.completed = true; });
        }
        return response;
      };
    });
    const page = await context.newPage(); contexts.push({ context, page, name });
    page.on('pageerror', error => audit.pageErrors.push({ stage, message: error.message }));
    page.on('console', message => { if (message.type() === 'error') audit.console.push({ stage, message: message.text(), url: message.location().url }); });
    page.on('request', request => {
      if (request.url().startsWith(api) && request.method() === 'POST' && request.url().endsWith('/turns'))
        audit.requests.push({ stage, path: new URL(request.url()).pathname, body: request.postDataJSON() });
    });
    page.on('response', response => {
      if (!response.url().startsWith(api)) return;
      const when = stage;
      pending.push((async () => {
        const type = response.headers()['content-type'] ?? '';
        const body = /json|event-stream/.test(type) ? await response.text() : null;
        if (body && !response.url().includes('/share-links')) {
          for (const key of ['"validation"', '"args"', '"public_id"', '"tool_calls"', 'res.cloudinary.com']) assert.ok(!body.includes(key), `private ${key}`);
        }
        audit.http.push({ stage: when, path: new URL(response.url()).pathname, method: response.request().method(), status: response.status(), type, body });
      })().catch(error => { if (error.code === 'ERR_ASSERTION') throw error; audit.http.push({ stage: when, path: new URL(response.url()).pathname, status: response.status(), unavailableBody: error.message }); }));
    });
    return page;
  }
  const owner = await pageFor('owner'), learner = await pageFor('learner');
  async function login(page, identity) {
    await page.goto(`${base}/dang-nhap`);
    await page.getByLabel('Email', { exact: true }).fill(`${identity}-w09@example.invalid`);
    await page.getByLabel('Mật khẩu', { exact: true }).fill('W09 isolated browser passphrase!');
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click(); await page.waitForURL(`${base}/khoa-hoc`);
  }
  try {
    await login(owner, 'owner'); await login(learner, 'learner');
    const me = await (await owner.request.get(`${base}/api/v1/me`)).json();
    const headers = { Origin: base, 'X-CSRF-Token': me.csrf_token };
    const control = async data => { const r = await owner.request.post(base + runtime.controlPath, { headers, data }); assert.equal(r.status(), 200, await r.text()); return r.json(); };
    async function probeUntil(check) {
      const deadline = Date.now() + 5000;
      while (Date.now() < deadline) {
        const value = await control({ action: 'probe' });
        if (check(value)) return value;
        await new Promise(resolve => setTimeout(resolve, 30));
      }
      assert.fail('Independent SQL/provider probe did not reach the required state');
    }
    async function open() {
      await learner.getByRole('button', { name: 'Mở khung trợ lý' }).click();
      await learner.getByRole('textbox', { name: 'Câu hỏi' }).waitFor();
      await learner.getByText('Đang mở cuộc trò chuyện…', { exact: true }).waitFor({ state: 'hidden' });
      const target = await learner.getByRole('textbox', { name: 'Câu hỏi' }).isDisabled()
        ? learner.getByRole('button', { name: 'Đóng trợ lý' }) : learner.getByRole('textbox', { name: 'Câu hỏi' });
      assert.equal(await target.evaluate(e => e === document.activeElement), true, 'opening focuses the composer or close when limited');
      if (await learner.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches))
        assert.equal(await learner.locator('.learning-chat-panel').evaluate(e => getComputedStyle(e).animationName), 'none');
    }
    async function ask(question) {
      await learner.getByRole('textbox', { name: 'Câu hỏi' }).fill(question);
      await Promise.all([learner.waitForResponse(r => r.url().endsWith('/turns') && r.request().method() === 'POST'),
        learner.getByRole('button', { name: 'Gửi câu hỏi' }).click()]);
    }
    async function ready() {
      await learner.getByRole('button', { name: 'Dừng nhận chữ' }).waitFor({ state: 'hidden' });
      await learner.waitForFunction(() => window.__w09Streams.at(-1)?.completed);
      const stream = await learner.evaluate(() => window.__w09Streams.at(-1));
      audit.http.push({ stage, path: new URL(stream.url).pathname, method: 'POST', status: 200, type: 'text/event-stream', body: stream.body, capture: 'tee of actual fetch response' });
      for (const key of ['"validation"', '"args"', '"public_id"', '"tool_calls"']) assert.ok(!stream.body.includes(key));
    }
    async function newSession() {
      const [response] = await Promise.all([learner.waitForResponse(r => r.url().endsWith('/sessions') && r.request().method() === 'POST'),
        learner.getByRole('button', { name: 'Trò chuyện mới', exact: true }).click()]);
      const value = await response.json();
      await learner.waitForFunction(sid => document.querySelector('.learning-chat-session-controls select')?.value === sid, value.session_id);
      await learner.getByRole('button', { name: 'Trò chuyện mới', exact: true }).waitFor();
    }
    async function dragChat(target) {
      const handle = learner.getByRole('separator', { name: 'Điều chỉnh độ rộng trợ lý' });
      const from = Number(await handle.getAttribute('aria-valuenow')), box = await handle.boundingBox();
      assert.ok(box.width >= 44 && box.height >= 44);
      await learner.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await learner.mouse.down(); await learner.mouse.move(box.x + box.width / 2 + from - target, box.y + box.height / 2, { steps: 10 }); await learner.mouse.up();
      const expected = Math.max(Number(await handle.getAttribute('aria-valuemin')), Math.min(target, Number(await handle.getAttribute('aria-valuemax'))));
      await learner.waitForFunction(width => Math.abs(document.querySelector('.learning-chat-panel').getBoundingClientRect().width - width) < 1, expected);
      const actual = await learner.evaluate(() => ({ chat: document.querySelector('.learning-chat-panel').getBoundingClientRect().toJSON(),
        main: document.querySelector('.courses-page').getBoundingClientRect().toJSON(), reading: document.querySelector('.learning-reading')?.getBoundingClientRect().toJSON(),
        saved: localStorage.getItem('wf-assistant-width') }));
      assert.equal(Number(actual.saved), expected); assert.ok(actual.main.right + 44 <= actual.chat.left + 1);
      if (actual.reading) assert.ok(actual.reading.width >= 379, 'dragging must retain a readable lesson column');
      (audit.resizes ??= []).push({ stage, requested: target, expected, actual });
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
          if (!element?.closest('.katex,.learning-chat-panel')) return { selector, eligible: false };
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
    async function capture(name, axe = false) {
      await learner.evaluate(() => document.fonts.ready);
      await learner.evaluate(() => Promise.all(document.getAnimations().filter(animation =>
        animation.effect?.getTiming().iterations !== Infinity).map(animation => animation.finished.catch(() => {}))));
      const width = learner.viewportSize().width;
      const theme = await learner.locator('html').getAttribute('data-theme');
      const reduced = await learner.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
      const layout = await learner.evaluate(() => {
        const panel = document.querySelector('.learning-chat-panel');
        const targets = [...panel.querySelectorAll('button:not(:disabled),a[href],summary,select,textarea,label.learning-chat-filter')]
          .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
          .filter(e => !e.closest('details:not([open])') || e.tagName === 'SUMMARY')
          .map(e => ({ label: e.getAttribute('aria-label') ?? e.textContent.trim().slice(0, 60), w: e.getBoundingClientRect().width, h: e.getBoundingClientRect().height }))
          .filter(b => b.w < 43.5 || b.h < 43.5);
        return { overflow: document.documentElement.scrollWidth > innerWidth + 1, targets };
      });
      assert.equal(layout.overflow, false, `${name}: overflow`); assert.deepEqual(layout.targets, [], `${name}: 44px targets`);
      const file = `${name}-${width}-${theme}${reduced ? '-reduced' : ''}.png`;
      await learner.screenshot({ path: path.join(out, file), fullPage: width >= 1280 }); audit.screens.push({ file, name, width, theme, reduced, layout });
      if (axe) {
        const focused = await learner.evaluateHandle(() => document.activeElement);
        // The opened options intentionally cover text below. Audit that floating group separately;
        // the underlying conversation is audited in the immediately preceding answered capture.
        const scope = name === 'conversation-options' ? '.learning-chat-options-panel' : null;
        const builder = new AxeBuilder({ page: learner }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']);
        const result = await (scope ? builder.include(scope) : builder).analyze();
        audit.accessibility.push({ file, scope: scope ?? 'document', violations: result.violations, incomplete: result.incomplete, passes: result.passes.length });
        assert.deepEqual(result.violations, [], `${name}: Axe violations`);
        const manual = [], unresolved = [];
        for (const finding of result.incomplete) {
          const supported = finding.id === 'color-contrast' && finding.nodes.every(node => node.any.every(check =>
            check.id === 'color-contrast' && ['Element content is too short to determine if it is actual text content',
              "Element's background color could not be determined because it partially overlaps other elements"].includes(check.message)));
          const measured = supported ? await mathContrast(learner, finding.nodes) : [];
          if (!supported || !measured.every(row => row.eligible)) unresolved.push(finding);
          else { assertMathContrast(measured); manual.push(...measured); }
        }
        audit.accessibility.at(-1).manualMath = manual;
        assert.deepEqual(unresolved, [], `${name}: unresolved accessibility checks`);
        if (manual.length && !audit.contrastCounterexample) {
          assert.throws(() => assertMathContrast(manual.map(row => ({ ...row, contrast: 1 }))), { code: 'ERR_ASSERTION' });
          assert.throws(() => assertMathContrast(manual.map(row => ({ ...row, unobscured: false }))), { code: 'ERR_ASSERTION' });
          audit.contrastCounterexample = { invisibleInkRejected: true, obscuredTextRejected: true, threshold: 4.5 };
        }
        const focus = await focused.evaluate(element => {
          const changed = element !== document.activeElement;
          const before = element?.getAttribute('aria-label') ?? element?.textContent?.trim().slice(0, 60);
          const after = document.activeElement?.getAttribute('aria-label') ?? document.activeElement?.tagName;
          if (changed && element instanceof HTMLElement && element.isConnected) element.focus({ preventScroll: true });
          return { changedByInspection: changed, before, after };
        });
        audit.accessibility.at(-1).focus = focus;
        await focused.dispose();
      }
    }
    const smoke = process.env.W09_BROWSER_SMOKE === '1';
    for (const width of (smoke ? [1280] : [390, 768, 1280])) for (const theme of (smoke ? ['light'] : ['light', 'dark'])) for (const reduced of (smoke ? [false] : [false, true])) {
      stage = `matrix:${width}:${theme}:${reduced}`; audit.configurations.push({ width, theme, reduced });
      await control({ action: 'advance' }); await control({ action: 'scenario', name: 'normal', pause: true });
      await learner.setViewportSize({ width, height: 900 }); await learner.emulateMedia({ colorScheme: theme, reducedMotion: reduced ? 'reduce' : 'no-preference' });
      await learner.goto(roadmap); await learner.getByRole('button', { name: 'Mở khung trợ lý' }).waitFor();
      if (await learner.locator('html').getAttribute('data-theme') !== theme) await learner.getByRole('button', { name: theme === 'dark' ? 'Bật chế độ tối' : 'Bật chế độ sáng' }).click();
      await open(); await capture('roadmap', width === 1280);
      await newSession();
      await ask(`Giải thích ý chính ${width} ${theme} ${reduced}.`);
      await learner.getByText('Theo sách, một tập hợp gồm các phần tử.', { exact: false }).last().waitFor();
      const before = await control({ action: 'probe' }); assert.equal(before.finished, false, 'first delta before provider finishes');
      assert.ok(!Object.hasOwn(audit.requests.at(-1).body, 'focus_node_id'));
      await capture('streaming'); await control({ action: 'release' }); await ready();
      await learner.locator('.learning-chat-answer .katex').first().waitFor();
      assert.equal(await learner.getByRole('link', { name: 'Quiz tự bịa' }).count(), 0);
      assert.equal(await learner.getByRole('link', { name: 'URL tự bịa' }).count(), 0);
      assert.match(await learner.locator('.learning-chat-messages').innerText(), /\[S999\]/);
      await capture('answered', true);
      await learner.getByRole('button', { name: 'Tuỳ chọn cuộc trò chuyện' }).click();
      assert.equal(await learner.getByRole('button', { name: 'Đổi tên', exact: true }).evaluate(element => element === document.activeElement), true);
      await capture('conversation-options', width === 390 || width === 1280);
      await learner.keyboard.press('Escape');
      assert.equal(await learner.getByRole('button', { name: 'Tuỳ chọn cuộc trò chuyện' }).evaluate(element => element === document.activeElement), true);
      await learner.getByRole('button', { name: 'Đóng trợ lý' }).click();
      if (width < 1280) await learner.getByRole('button', { name: 'Mở khung trợ lý' }).waitFor({ state: 'visible' });
      await learner.goto(lesson); await learner.getByRole('button', { name: 'Mở khung trợ lý' }).waitFor(); await open();
      await newSession();
      await ask(`Bài này khác gì ${width} ${theme} ${reduced}?`); await ready();
      assert.equal(audit.requests.at(-1).body.focus_node_id, nid);
      await capture('lesson', width === 390);
      if (width === 1280) {
        await dragChat(480); await capture('chat-wide', true);
        await dragChat(700); assert.equal(await learner.getByRole('separator').getAttribute('aria-valuenow'), '512');
        await dragChat(200); await capture('chat-narrow');
        await dragChat(480); await learner.reload(); await open();
        assert.equal(await learner.getByRole('separator').getAttribute('aria-valuenow'), '480');
        await capture('chat-restored'); await dragChat(380); await capture('lesson-current', true);
      } else assert.equal(await learner.getByRole('separator').count(), 0);
      const citation = learner.locator('.learning-chat-answer .lecture-citation').first();
      if (await citation.count()) {
        const sourcePage = Number((await citation.getAttribute('aria-label')).match(/trang (\d+)/)[1]);
        await citation.click(); await learner.locator('.source-viewer').waitFor();
        await learner.getByRole('heading', { name: `Trang ${sourcePage} trong tài liệu` }).waitFor();
        await learner.locator('.source-viewer img').evaluate(image => image.complete ? Promise.resolve() : new Promise(resolve => image.addEventListener('load', resolve, { once: true })));
        await capture('source'); await learner.locator('.source-viewer').getByRole('button', { name: 'Đóng', exact: true }).click();
      }
      if (width < 1280) {
        await learner.keyboard.press('Escape');
        assert.equal(await learner.getByRole('button', { name: 'Mở khung trợ lý' }).evaluate(e => e === document.activeElement), true, 'Escape restores opener focus');
        await open();
      }
      await learner.getByRole('button', { name: 'Đóng trợ lý' }).click();
    }
    stage = 'changing-focus';
    await control({ action: 'advance' });
    await learner.goto(lesson); await open(); await ask('Bài X đang mở.'); await ready();
    assert.equal(audit.requests.at(-1).body.focus_node_id, nid);
    await learner.getByRole('button', { name: 'Đóng trợ lý' }).click();
    await learner.locator(`.learning-sidebar a[href$="/khai-niem/${runtime.otherNodeId}"]`).click();
    await learner.waitForURL(url => decodeURIComponent(url.pathname).endsWith('/' + runtime.otherNodeId));
    await open(); await ask('Tôi đã chuyển sang bài Y.'); await ready();
    assert.equal(audit.requests.at(-1).body.focus_node_id, runtime.otherNodeId);
    await learner.goto(lesson);
    await learner.locator('.lecture-prerequisites summary').first().click();
    const prerequisite = learner.getByRole('link', { name: 'Mở bài học tiên quyết' }).first();
    const prerequisitePath = await prerequisite.getAttribute('href');
    await prerequisite.click(); await learner.waitForURL(url => url.pathname === prerequisitePath);
    await open(); await ask('Giải thích bài tiên quyết đang mở.'); await ready();
    assert.equal(audit.requests.at(-1).body.focus_node_id, decodeURIComponent(prerequisitePath.split('/').at(-1)));
    await capture('prerequisite-focus');
    stage = 'session-actions';
    await learner.goto(lesson); await open();
    await learner.getByRole('button', { name: 'Tuỳ chọn cuộc trò chuyện' }).click();
    await learner.getByRole('button', { name: 'Đổi tên', exact: true }).click();
    await learner.getByRole('textbox', { name: 'Tên cuộc trò chuyện' }).fill('Ôn tập trước kiểm tra');
    await learner.getByRole('button', { name: 'Lưu tên' }).click();
    await learner.getByRole('option', { name: /^Ôn tập trước kiểm tra/ }).waitFor({ state: 'attached' });
    await control({ action: 'old-scope' }); await learner.reload(); await open();
    await learner.getByRole('checkbox', { name: 'Tất cả cuộc trò chuyện' }).check();
    await learner.getByRole('combobox', { name: 'Cuộc trò chuyện đang mở' }).selectOption(await learner.getByRole('option', { name: /^Ôn tập trước kiểm tra/ }).getAttribute('value'));
    await control({ action: 'advance' }); await ask('Ôn lại phạm vi đã đổi.'); await ready();
    await learner.getByText('Module này đã đổi. Bạn có thể mở phiên mới cho module hiện tại.').last().waitFor();
    await capture('old-scope', true);
    await newSession();
    stage = 'disconnect-reload';
    await control({ action: 'scenario', name: 'normal', pause: true });
    await ask('Lưu kết quả khi tôi đóng trang.');
    await learner.locator('.learning-chat-turn').filter({ has: learner.getByText('Lưu kết quả khi tôi đóng trang.', { exact: true }) })
      .getByText('Theo sách, một tập hợp gồm các phần tử.', { exact: false }).waitFor();
    const intent = audit.requests.at(-1).body; const before = await probeUntil(value => value.calls === 1 && !value.finished);
    assert.equal(before.finished, false); await learner.reload(); await open();
    await learner.getByRole('button', { name: 'Thử lại câu hỏi' }).waitFor();
    await capture('reload-pending'); await control({ action: 'release' });
    await probeUntil(value => value.finished && value.turns === before.turns + 1);
    await learner.getByRole('button', { name: 'Cập nhật trò chuyện', exact: true }).last().click();
    await learner.getByRole('button', { name: 'Thử lại câu hỏi' }).waitFor({ state: 'hidden' });
    assert.equal((await control({ action: 'probe' })).calls, 1);
    assert.equal(audit.requests.filter(row => row.body.client_turn_id === intent.client_turn_id).length, 1);
    await capture('reload-saved', true);
    stage = 'tools'; await control({ action: 'scenario', name: 'tools' }); await ask('Tạo quiz và tài liệu ôn tập.');
    await learner.getByRole('status').filter({ hasText: 'Đang tạo tài liệu' }).waitFor();
    assert.equal(await learner.getByRole('button', { name: /Tài liệu đã tạo/ }).count(), 0);
    await capture('creating-artifact'); await control({ action: 'release-tools' }); await ready();
    await learner.getByRole('button', { name: /Tài liệu đã tạo/ }).last().waitFor();
    await capture('artifacts', true);
    await learner.getByRole('button', { name: /Tài liệu đã tạo/ }).last().click();
    await learner.getByText('Tài liệu ôn tập đã lưu.', { exact: false }).last().waitFor();
    await learner.locator('.learning-chat-preview').scrollIntoViewIfNeeded(); await capture('artifact-preview', true);
    await learner.locator('.learning-chat-preview').getByRole('button', { name: 'Đóng nội dung' }).click();
    await learner.getByRole('button', { name: /Quiz đã tạo/ }).last().click();
    await learner.locator('.learning-chat-preview h4').first().waitFor();
    await learner.locator('.learning-chat-preview').scrollIntoViewIfNeeded(); await capture('quiz-preview', true);
    await learner.locator('.learning-chat-preview').getByRole('button', { name: 'Đóng nội dung' }).click();
    const counts = await control({ action: 'probe' }); assert.ok(counts.documents > 0);
    stage = 'delete'; await learner.getByRole('button', { name: 'Tuỳ chọn cuộc trò chuyện' }).click();
    await learner.getByRole('button', { name: 'Xoá cuộc trò chuyện', exact: true }).click();
    await capture('delete-confirmation'); await learner.getByRole('button', { name: 'Xác nhận xoá' }).click();
    await learner.getByRole('group', { name: 'Xác nhận xoá cuộc trò chuyện' }).waitFor({ state: 'hidden' });
    assert.equal((await control({ action: 'probe' })).documents, counts.documents);
    const retained = await learner.request.get(`${api}/library?scope=all`);
    assert.equal(retained.status(), 200);
    assert.ok((await retained.json()).items.some(item => item.kind === 'document' && item.session_deleted));
    await newSession();
    stage = 'failure'; await control({ action: 'scenario', name: 'failure' }); await ask('Thử kết nối lỗi.'); await ready();
    await learner.getByRole('button', { name: 'Thử lại câu hỏi' }).waitFor(); await capture('failure', true);
    await control({ action: 'scenario', name: 'normal' }); await learner.getByRole('button', { name: 'Thử lại câu hỏi' }).click(); await ready();
    stage = 'daily-limit'; await control({ action: 'limit' }); await learner.reload(); await open();
    await learner.getByText(/Đã dùng hết hạn mức hôm nay/).waitFor();
    assert.equal(await learner.getByRole('textbox', { name: 'Câu hỏi' }).isDisabled(), true);
    await capture('daily-limit', true);
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
    const snapshotPath = path.join(root, 'tmp/w09-inspect.html');
    await fs.writeFile(snapshotPath, snapshot.replace(/<head([^>]*)>/i, `<head$1><base href="${base}/">`));
    await fs.mkdir(path.join(root, 'tmp/w09-taste-profiles'), { recursive: true });
    const inspected = spawnSync(process.execPath, [path.join(shared, '.agents/skills/design-taste-frontend/scripts/inspect.mjs'), snapshotPath,
      '--out', path.join(out, 'taste-inspect'), '--widths', '1280,768,390', '--app', '--json'],
      { cwd: root, encoding: 'utf8', timeout: 180000, env: { ...process.env, TASTE_SKILL_TMP: path.join(root, 'tmp/w09-taste-profiles') } });
    await fs.writeFile(path.join(out, 'taste-inspector.log'), String(`${inspected.stdout ?? ''}${inspected.stderr ?? ''}`));
    assert.ok([0, 1].includes(inspected.status));
    audit.designInspection = JSON.parse(await fs.readFile(path.join(out, 'taste-inspect/report.json'), 'utf8'));
    assert.equal(audit.designInspection.findings.filter(finding => finding.level === 'FAIL').length, 0, 'taste inspector failures must be fixed');
    stage = 'revoked';
    const removal = await owner.request.delete(`${api}/members/${runtime.learnerId}`, { headers }); assert.equal(removal.status(), 200);
    const denied = await learner.request.get(`${api}/sessions?filter=all`); assert.equal(denied.status(), 404);
    await learner.reload(); await learner.getByRole('heading', { name: 'Chưa thể mở trang học' }).waitFor();
    audit.assertions.push('Real HTTP/PG/Core Assistant3; first delta before finish', 'Roadmap no focus; lesson sends current focus',
      'Reload keeps pending identity; saved history returns with one fake call', 'Verified document artifact preview; fabricated prose links inert',
      'Rename, old scope, delete keeps generated document', 'Failure has retry; day limit ratio and disabled input; removal denied next request',
      '390/768/1280 both themes and real reduced-motion media; per-screen layout/44px and scoped Axe');
    assert.deepEqual(audit.pageErrors, []);
    console.log(JSON.stringify({ screens: audit.screens.length, axe: audit.accessibility.length, http: audit.http.length }));
  } finally {
    for (const { context, page, name } of contexts) { const video = page.video(); await context.close(); if (video) await video.saveAs(path.join(out, `${name}.webm`)); }
    await Promise.allSettled(pending); await fs.writeFile(path.join(out, 'audit.json'), JSON.stringify(audit, null, 2) + '\n'); await browser.close();
  }
}
main().catch(error => { console.error(error.stack); process.exitCode = 1; });
