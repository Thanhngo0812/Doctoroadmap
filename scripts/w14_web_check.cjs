const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const toolsRoot = require('node:fs').existsSync(path.join(root, '.tmp/w01-browser-tools'))
  ? root : path.resolve(root, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(toolsRoot, '.tmp/w01-browsers');
const { chromium } = require(path.join(toolsRoot, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(toolsRoot, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));

const base = process.env.W14_BASE_URL || 'http://127.0.0.1:8014';
const runtimeFile = process.env.W14_RUNTIME_JSON || path.join(root, 'report/w14-react-evidence/runtime.json');
const output = path.join(root, 'report/w14-react-evidence');
const password = 'W14 browser-only test passphrase 2026!';
const timeoutMs = 30000;

async function main() {
  await fs.mkdir(output, { recursive: true });
  const runtime = JSON.parse(await fs.readFile(runtimeFile, 'utf8'));
  assert.equal(runtime.database, 'uuid-disposable-postgresql');
  assert.equal(runtime.media, 'MemoryMediaStore');
  assert.equal(runtime.mailer, 'FakeMailer');
  assert.equal(runtime.modelCalls, 0);
  assert.equal(runtime.modelCostUsd, 0);
  assert.equal(runtime.fixture.sourceDoc, 'doc-1');
  assert.equal(runtime.fixture.manifestSha256Verified, true);

  const audit = {
    source: 'real browser against FastAPI and disposable PostgreSQL; worker pipeline is deterministic fake',
    localIntegrationEvidence: false,
    media: runtime.media,
    mailer: runtime.mailer,
    modelCalls: runtime.modelCalls,
    modelCostUsd: runtime.modelCostUsd,
    assertions: [], screens: [], accessibility: [], apiResponses: [],
    consoleErrors: [], rawConsoleErrors: [], expectedConsoleErrors: [], pageErrors: [],
    failedRequests: [], fontFailures: [], fontRequests: [], unexpectedExternalRequests: [],
    expectedProbeRequests: [], builds: [], video: 'w14-upload-build.webm',
  };
  const state = { accountId: null, courseIds: [], buildIds: [], statuses: [], reuseSameBuild: false };
  await fs.mkdir(path.join(root, '.tmp/w14-browser-video'), { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    recordVideo: { dir: path.join(root, '.tmp/w14-browser-video'), size: { width: 1280, height: 900 } },
  });
  const page = await context.newPage();
  let stage = 'register';
  let csrfToken = '';

  page.on('pageerror', error => {
    const entry = { stage, message: error.message };
    audit.pageErrors.push(entry);
  });
  page.on('console', message => {
    if (message.type() === 'error') {
      const entry = { stage, text: message.text() };
      const initialMe401 = stage === 'register'
        && entry.text === 'Failed to load resource: the server responded with a status of 401 (Unauthorized)'
        && audit.apiResponses.some(response => response.stage === stage && response.method === 'GET'
          && response.path === '/api/v1/me' && response.status === 401);
      const axeProbeCsp = stage.startsWith('axe:') && (
        (entry.text.startsWith("Connecting to 'https://fonts.googleapis.com/")
          && entry.text.includes('violates the following Content Security Policy directive: "default-src \'self\'"')
          && entry.text.endsWith('The action has been blocked.'))
        || (entry.text.startsWith("Applying inline style violates the following Content Security Policy directive 'style-src-elem \'self\' https://fonts.googleapis.com'")
          && entry.text.includes("Either the 'unsafe-inline' keyword") && entry.text.endsWith('The action has been blocked.'))
      );
      if (initialMe401) entry.expected = 'unauthenticated GET /api/v1/me during registration bootstrap';
      else if (axeProbeCsp) entry.expected = 'Axe injected probe blocked by application CSP';
      audit.rawConsoleErrors.push(entry);
      if (entry.expected) audit.expectedConsoleErrors.push(entry);
      else audit.consoleErrors.push(entry);
    }
  });
  page.on('requestfailed', request => {
    const url = new URL(request.url());
    const entry = { stage, method: request.method(), path: url.pathname,
      resourceType: request.resourceType(), error: request.failure()?.errorText ?? 'failed' };
    const axeFontProbe = stage.startsWith('axe:') && url.origin === 'https://fonts.googleapis.com'
      && url.pathname === '/css2' && ['fetch', 'xhr'].includes(request.resourceType())
      && entry.error === 'net::ERR_BLOCKED_BY_CSP';
    if (axeFontProbe) {
      audit.expectedProbeRequests.push(entry);
    } else if (['https://fonts.googleapis.com', 'https://fonts.gstatic.com'].includes(url.origin)) {
      audit.fontFailures.push(entry);
    } else {
      audit.failedRequests.push(entry);
    }
  });
  page.on('request', request => {
    const url = new URL(request.url());
    if (['https://fonts.googleapis.com', 'https://fonts.gstatic.com'].includes(url.origin)) {
      audit.fontRequests.push({ stage, method: request.method(), origin: url.origin, path: url.pathname });
    } else if (url.origin !== new URL(base).origin) {
      audit.unexpectedExternalRequests.push({ stage, origin: url.origin, path: url.pathname });
    }
  });
  page.on('response', async response => {
    const url = new URL(response.url());
    if (url.origin !== new URL(base).origin || !url.pathname.startsWith('/api/v1/')) return;
    audit.apiResponses.push({ stage, method: response.request().method(), path: url.pathname,
      status: response.status() });
    if (response.status() < 200 || response.status() >= 300) return;
    if (!['/api/v1/uploads', '/api/v1/builds/', '/api/v1/courses/'].some(prefix => url.pathname.startsWith(prefix))) return;
    try { assertPrivateBuildDto(await response.json(), `${response.request().method()} ${url.pathname}`); }
    catch (error) {
      const entry = { stage, path: url.pathname, message: error.message };
      audit.pageErrors.push(entry);
    }
  });
  page.on('response', response => {
    const url = new URL(response.url());
    if (['https://fonts.googleapis.com', 'https://fonts.gstatic.com'].includes(url.origin)) {
      audit.fontRequests.push({ stage, method: response.request().method(), origin: url.origin,
        path: url.pathname, status: response.status() });
      if (response.status() >= 400) {
        audit.fontFailures.push({ stage, method: response.request().method(), origin: url.origin,
          path: url.pathname, status: response.status() });
      }
    }
  });

  const workerHeaders = () => ({
    Origin: base,
    'X-CSRF-Token': csrfToken,
    'X-W14-Control': process.env.W14_CONTROL_TOKEN,
    'Content-Type': 'application/json',
  });
  const control = async (route, data = undefined) => {
    const response = await page.request.post(`${base}/__test__/worker/${route}`, {
      headers: workerHeaders(), ...(data === undefined ? {} : { data }),
    });
    assert.equal(response.status(), 200, `test-only worker control ${route}`);
    return response.json();
  };
  const workerState = async () => {
    const response = await page.request.get(`${base}/__test__/worker/state`, {
      headers: { 'X-W14-Control': process.env.W14_CONTROL_TOKEN },
    });
    assert.equal(response.status(), 200, 'test-only worker state');
    return response.json();
  };
  const apiJson = async route => {
    const response = await page.request.get(`${base}${route}`);
    assert.equal(response.status(), 200, `GET ${route}`);
    return response.json();
  };

  let video;
  try {
    await page.goto(`${base}/dang-ky`, { waitUntil: 'networkidle' });
    await page.getByLabel('Tên hiển thị').fill('Người học W14');
    await page.getByLabel('Email', { exact: true }).fill(`w14-${crypto.randomUUID()}@example.invalid`);
    await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
    const confirmation = page.getByLabel('Nhập lại mật khẩu', { exact: true });
    if (await confirmation.count()) await confirmation.fill(password);
    await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    await page.getByRole('heading', { exact: true, name: 'Khoá học của tôi' }).waitFor();
    const meResponse = await page.request.get(`${base}/api/v1/me`);
    assert.equal(meResponse.status(), 200);
    const me = await meResponse.json();
    assert.ok(me.account?.id);
    assert.ok(me.csrf_token);
    state.accountId = me.account.id;
    csrfToken = me.csrf_token;
    audit.assertions.push('registered a real account and received an authenticated session');

    const fixtures = path.join(output, 'fixtures');
    const successDigest = crypto.createHash('sha256').update(await fs.readFile(path.join(fixtures, runtime.fixtureNames.success))).digest('hex');
    const reuseDigest = crypto.createHash('sha256').update(await fs.readFile(path.join(fixtures, runtime.fixtureNames.reuse))).digest('hex');
    assert.equal(successDigest, reuseDigest, 'reuse fixtures must be byte-identical');
    stage = 'upload.page';
    await page.goto(`${base}/tai-len`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Tải tài liệu lên' }).waitFor();
    const fontLoaded = await page.evaluate(async () => {
      await document.fonts.ready;
      return [...document.fonts].some(font => font.family === 'Be Vietnam Pro' && font.status === 'loaded');
    });
    assert.equal(fontLoaded, true, 'the interface must load its declared Be Vietnam Pro font');
    audit.fontLoaded = fontLoaded;
    await assertFilePickerKeyboardFocus(page, audit);
    await setViewportThemeScreens(page, audit, 'upload', [390, 768, 1280]);
    await page.setViewportSize({ width: 1280, height: 900 });
    await setTheme(page, 'light');

    const success = await uploadThroughUi(page, path.join(fixtures, runtime.fixtureNames.success), 'W14 - xác suất học tập');
    state.courseIds.push(success.courseId);
    state.buildIds.push(success.buildId);
    const awaiting = await apiJson(`/api/v1/builds/${success.buildId}?course_id=${success.courseId}`);
    assert.equal(awaiting.status, 'awaiting_confirmation');
    assert.equal((await workerState()).runs, 0, 'worker must not run before explicit confirmation');
    const persistedBeforeConfirm = await apiJson(`/api/v1/courses/${success.courseId}`);
    assert.equal(persistedBeforeConfirm.title, 'w14-success',
      'custom course title is not persisted until the explicit confirmation action');
    const quotaResponse = await page.request.get(`${base}/api/v1/me/usage`);
    assert.equal(quotaResponse.status(), 200);
    const quotaPayload = await quotaResponse.json();
    assertPrivateBuildDto(quotaPayload, 'build quota response');
    assert.doesNotMatch(await page.locator('body').innerText(), /dự toán|chi phí|\bUSD\b|ước tính/i);
    await page.getByLabel('Tên khoá học').fill('Đại số tuyến tính — tên do tôi chọn');
    audit.screens.push(await screenshot(page, 'awaiting-confirmation-1280-light.png'));
    const confirmResponsePromise = page.waitForResponse(response => response.request().method() === 'POST'
      && new URL(response.url()).pathname === `/api/v1/uploads/${success.uploadId}/build`);
    await page.getByRole('button', { name: 'Dựng lộ trình', exact: true }).click();
    const confirmResponse = await confirmResponsePromise;
    assert.equal(confirmResponse.status(), 200);
    const queued = await confirmResponse.json();
    assert.equal(queued.status, 'queued');
    const persistedAfterConfirm = await apiJson(`/api/v1/courses/${success.courseId}`);
    assert.match(JSON.stringify(persistedAfterConfirm), /Đại số tuyến tính — tên do tôi chọn/);
    audit.assertions.push('upload stayed awaiting_confirmation without worker activity; confirmation persisted the user-edited title and queued work');

    await control('start', { mode: 'success', pause_stages: ['doc_reading', 'concepts'] });
    await waitFor(async () => {
      const worker = await workerState();
      assert.equal(worker.lastException, null, `fake worker stopped with ${JSON.stringify(worker)}`);
      return worker.pausedStage === 'doc_reading';
    }, 'worker pause at reading', 240000);
    await waitForBuild(page, success.buildId, success.courseId, 'reading');
    stage = 'build.reading';
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Đang đọc và kiểm tra tài liệu' }).waitFor();
    audit.screens.push(await screenshot(page, 'reading-reloaded-390-dark.png', { width: 390, theme: 'dark' }));
    await control('advance');
    await waitFor(async () => (await workerState()).pausedStage === 'concepts', 'worker pause at concepts', 240000);
    const running = await waitForBuild(page, success.buildId, success.courseId, 'running');
    assert.equal(running.step, 'concepts');
    stage = 'build.running';
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Đang xác định bài học' }).waitFor();
    audit.screens.push(await screenshot(page, 'running-768-light.png', { width: 768, theme: 'light' }));
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Đang xác định bài học' }).waitFor();
    await page.locator('.task-wait img[src$="wayfinder-wait.png"]').waitFor();
    assert.equal(await page.locator('.task-wait picture').count(), 0,
      'reduced motion must select the static waiting illustration');
    assert.equal(await page.evaluate(() => document.getAnimations().filter(item => item.playState === 'running').length), 0);
    audit.assertions.push('reduced-motion replaced the animated waiting asset with its static image during a live build');
    await runDesignInspection(page, audit);
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    await control('advance');
    await waitFor(async () => !(await workerState()).running, 'success worker completion');
    const succeeded = await waitForBuild(page, success.buildId, success.courseId, 'succeeded');
    assert.equal(succeeded.course_id, success.courseId);
    stage = 'build.succeeded';
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Lộ trình đã sẵn sàng' }).waitFor();
    assert.equal(await page.getByRole('link', { name: 'Mở khoá học', exact: true }).count(), 1);
    audit.screens.push(await screenshot(page, 'success-1280-dark.png', { width: 1280, theme: 'dark' }));
    audit.assertions.push('real BuildWorker persisted reading and running checkpoints across reload, then completed the manifest-backed build');
    audit.builds.push({ buildId: success.buildId, courseId: success.courseId, status: 'succeeded', title: 'Đại số tuyến tính — tên do tôi chọn' });

    stage = 'upload.reuse';
    const reuse = await uploadThroughUi(page, path.join(fixtures, runtime.fixtureNames.reuse), 'Khoá học dùng lại, tiêu đề đã xác nhận');
    assert.equal(reuse.buildId, success.buildId, 'same source bytes and pipeline reuse the succeeded build');
    assert.notEqual(reuse.courseId, success.courseId, 'reuse still creates a separate course');
    assert.equal((await workerState()).runs, 1, 'reuse upload must not start a duplicate worker before confirming its course title');
    await page.getByRole('heading', { exact: true, name: 'Xác nhận dựng lộ trình' }).waitFor();
    await page.getByLabel('Tên khoá học').fill('Khoá học dùng lại, tiêu đề đã xác nhận');
    await page.setViewportSize({ width: 390, height: 900 });
    await setTheme(page, 'light');
    await page.screenshot({ path: path.join(output, 'reuse-awaiting-confirmation-390-light.png'), fullPage: true });
    audit.screens.push({ filename: 'reuse-awaiting-confirmation-390-light.png', width: 390, theme: 'light' });
    const reuseConfirmPromise = page.waitForResponse(response => response.request().method() === 'POST'
      && new URL(response.url()).pathname === `/api/v1/uploads/${reuse.uploadId}/build`);
    await page.getByRole('button', { name: 'Dựng lộ trình', exact: true }).click();
    const reuseConfirm = await reuseConfirmPromise;
    assert.equal(reuseConfirm.status(), 200);
    assert.equal((await reuseConfirm.json()).status, 'succeeded');
    const reusedCourse = await apiJson(`/api/v1/courses/${reuse.courseId}`);
    assert.equal(reuse.status, 'succeeded');
    assert.match(JSON.stringify(reusedCourse), /Khoá học dùng lại, tiêu đề đã xác nhận/);
    assert.equal((await apiJson(`/api/v1/builds/${success.buildId}?course_id=${reuse.courseId}`)).course_id, reuse.courseId);
    assert.equal((await workerState()).runs, 1, 'confirming a reused succeeded build must not start a duplicate runner');
    state.courseIds.push(reuse.courseId);
    state.reuseSameBuild = true;
    state.reuse = {
      sameBuild: true,
      originalCourseId: success.courseId,
      reusedCourseId: reuse.courseId,
      buildId: success.buildId,
      originalTitle: 'Đại số tuyến tính — tên do tôi chọn',
      reusedTitle: 'Khoá học dùng lại, tiêu đề đã xác nhận',
    };
    audit.assertions.push('a second upload of identical bytes reused the succeeded build while keeping a distinct course and title context');
    audit.builds.push({ buildId: reuse.buildId, courseId: reuse.courseId, status: 'succeeded', reused: true });
    await page.goto(`${base}/khoa-hoc`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Khoá học của tôi' }).waitFor();
    const firstCard = page.locator('.course-card[aria-label="Đại số tuyến tính — tên do tôi chọn"]');
    const secondCard = page.locator('.course-card[aria-label="Khoá học dùng lại, tiêu đề đã xác nhận"]');
    assert.equal(await firstCard.count(), 1);
    assert.equal(await secondCard.count(), 1);
    assert.ok((await secondCard.getByRole('link', { name: 'Học tiếp' }).getAttribute('href')).includes(reuse.courseId));
    audit.assertions.push('course list displayed both titles and resumed the second course through its own course ID');

    stage = 'build.cancel';
    const cancel = await uploadThroughUi(page, path.join(fixtures, runtime.fixtureNames.cancel), 'W14 - bản có thể huỷ');
    state.courseIds.push(cancel.courseId);
    state.buildIds.push(cancel.buildId);
    await confirmThroughUi(page, cancel, 'Bản DOCX cần dừng');
    await control('start', { mode: 'success', pause_stages: ['doc_reading'] });
    await waitFor(async () => (await workerState()).pausedStage === 'doc_reading', 'cancel worker pause');
    await waitForBuild(page, cancel.buildId, cancel.courseId, 'reading');
    const cancelledActionPromise = page.waitForResponse(response => response.request().method() === 'POST'
      && new URL(response.url()).pathname === `/api/v1/builds/${cancel.buildId}/cancel`);
    await page.getByRole('button', { name: 'Huỷ dựng', exact: true }).click();
    const cancelledAction = await cancelledActionPromise;
    assert.equal(cancelledAction.status(), 200);
    await control('advance');
    await waitFor(async () => !(await workerState()).running, 'cancel worker completion');
    await waitForBuild(page, cancel.buildId, cancel.courseId, 'cancelled');
    stage = 'build.cancelled';
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Đã huỷ' }).waitFor();
    audit.assertions.push('cancellation during a paused reading step stopped the real worker at its next boundary and persisted cancelled');
    audit.builds.push({ buildId: cancel.buildId, courseId: cancel.courseId, status: 'cancelled' });

    stage = 'build.retry';
    const retry = await uploadThroughUi(page, path.join(fixtures, runtime.fixtureNames.retry), 'W14 - có thể thử lại');
    state.courseIds.push(retry.courseId);
    state.buildIds.push(retry.buildId);
    await confirmThroughUi(page, retry, 'Bản PDF có thể thử lại');
    await control('start', { mode: 'retryable', pause_stages: [] });
    await waitFor(async () => !(await workerState()).running, 'retryable fake worker result');
    const failed = await waitForBuild(page, retry.buildId, retry.courseId, 'failed');
    assert.equal(failed.error?.retryable, true);
    stage = 'build.retryable';
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Thử lại', exact: true }).waitFor();
    const retriedPromise = page.waitForResponse(response => response.request().method() === 'POST'
      && new URL(response.url()).pathname === `/api/v1/builds/${retry.buildId}/retry`);
    await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
    const retried = await retriedPromise;
    assert.equal(retried.status(), 200);
    assert.equal((await retried.json()).status, 'queued');
    await control('start', { mode: 'success', pause_stages: [] });
    await waitFor(async () => !(await workerState()).running, 'retry success worker completion');
    await waitForBuild(page, retry.buildId, retry.courseId, 'succeeded');
    stage = 'build.retried';
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Lộ trình đã sẵn sàng' }).waitFor();
    audit.assertions.push('retryable synthetic failure exposed Retry, queued a new attempt, and succeeded through the real worker');
    audit.builds.push({ buildId: retry.buildId, courseId: retry.courseId, status: 'succeeded-after-retry' });

    stage = 'build.rejected';
    const reject = await uploadThroughUi(page, path.join(fixtures, runtime.fixtureNames.reject), 'W14 - tài liệu quét');
    state.courseIds.push(reject.courseId);
    state.buildIds.push(reject.buildId);
    await confirmThroughUi(page, reject, 'Bản PDF không đọc được');
    await control('start', { mode: 'rejected', pause_stages: [] });
    await waitFor(async () => !(await workerState()).running, 'rejected worker completion');
    const rejected = await waitForBuild(page, reject.buildId, reject.courseId, 'rejected');
    assert.equal(rejected.error?.code, 'ban_quet');
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('heading', { exact: true, name: 'Không thể đọc tài liệu' }).waitFor();
    await setViewportThemeScreens(page, audit, 'rejected', [390, 768, 1280]);
    audit.assertions.push('the non-retryable synthetic scan result was shown as rejected with a safe user-facing error');
    audit.builds.push({ buildId: reject.buildId, courseId: reject.courseId, status: 'rejected', errorCode: 'ban_quet' });

    state.buildIds = [...new Set(state.buildIds)];
    state.statuses = audit.builds.map(item => ({ buildId: item.buildId, status: item.status }));
    assert.equal(state.courseIds.length, 5);
    assert.equal(state.buildIds.length, 4);
    assert.equal(state.reuseSameBuild, true);
    await writeJson('browser-state.json', state);

    stage = 'axe:build-rejected';
    const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    audit.accessibility.push({ route: '/ban-dung/:id', violations: axe.violations.map(item => item.id), incomplete: axe.incomplete.map(item => item.id) });
    assert.deepEqual(axe.violations.map(item => item.id), []);
    assert.deepEqual(axe.incomplete.map(item => item.id), []);
    const probeWarnings = audit.expectedConsoleErrors.filter(item => item.stage.startsWith('axe:')
      && item.expected === 'Axe injected probe blocked by application CSP'
      && item.text.startsWith("Connecting to 'https://fonts.googleapis.com/")).length;
    assert.equal(audit.expectedProbeRequests.length, probeWarnings,
      'each Axe font CSP warning must match its exact blocked fetch request');
    stage = 'accessibility';

    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto(`${base}/tai-len`, { waitUntil: 'networkidle' });
    assert.equal(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true);
    assert.equal(await page.evaluate(() => document.getAnimations().filter(item => item.playState === 'running').length), 0);
    await page.keyboard.press('Tab');
    const focus = await page.evaluate(() => ({
      interactive: document.activeElement?.matches('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])'),
      visible: Boolean(document.activeElement?.getClientRects().length),
      outlineStyle: getComputedStyle(document.activeElement).outlineStyle,
      outlineWidth: Number.parseFloat(getComputedStyle(document.activeElement).outlineWidth),
    }));
    assert.equal(focus.interactive && focus.visible, true);
    assert.notEqual(focus.outlineStyle, 'none');
    assert.ok(focus.outlineWidth >= 2);
    audit.assertions.push('Axe found no violation or incomplete check; reduced-motion and keyboard focus assertions passed');
    assert.deepEqual(audit.pageErrors, []);
    assert.deepEqual(audit.consoleErrors, []);
    assert.deepEqual(audit.failedRequests, []);
    assert.deepEqual(audit.fontFailures, []);
    assert.deepEqual(audit.unexpectedExternalRequests, []);
    assert.equal(audit.designInspection.exitCode, 0,
      `taste inspection must finish without findings; see ${audit.designInspection.log}`);
    audit.rawConsoleErrorCount = audit.rawConsoleErrors.length;
    audit.localIntegrationEvidence = true;
    audit.assertions.push('browser made no unexpected external requests; all API calls used same-origin FastAPI');
  } finally {
    video = page.video();
    await context.close();
    if (video) {
      try { await video.saveAs(path.join(output, audit.video)); }
      catch (error) { audit.videoSaveError = error.message; }
    }
    await fs.writeFile(path.join(output, 'browser-audit.json'), JSON.stringify(audit, null, 2) + '\n', 'utf8').catch(() => {});
    await browser.close();
  }
  console.log(JSON.stringify({ assertions: audit.assertions.length, screenshots: audit.screens.length,
    apiResponses: audit.apiResponses.length, builds: audit.builds.length,
    axeViolations: audit.accessibility.reduce((n, item) => n + item.violations.length, 0),
    consoleErrors: audit.consoleErrors.length, pageErrors: audit.pageErrors.length }));
}

async function uploadThroughUi(page, file, title = null) {
  await page.goto(`${base}/tai-len`, { waitUntil: 'networkidle' });
  await page.getByLabel('Tệp PDF hoặc DOCX').setInputFiles(file);
  await page.getByLabel('Tôi có quyền sử dụng và chia sẻ tài liệu này.').check();
  await page.getByRole('button', { name: 'Tải tài liệu lên', exact: true }).click();
  await page.waitForURL(url => url.pathname.startsWith('/ban-dung/'), { timeout: timeoutMs });
  const route = new URL(page.url());
  const buildId = decodeURIComponent(route.pathname.split('/').pop());
  const courseId = route.searchParams.get('course_id');
  const uploadId = route.searchParams.get('upload_id');
  assert.ok(buildId && courseId && uploadId, 'upload navigation must carry build, course, and upload identifiers');
  const response = await page.request.get(`${base}/api/v1/uploads/${uploadId}`);
  assert.equal(response.status(), 200);
  const uploaded = await response.json();
  assert.equal(uploaded.upload_id, uploadId);
  assert.equal(uploaded.build.build_id, buildId);
  assert.equal(uploaded.build.course_id, courseId);
  assertPrivateBuildDto(uploaded, 'upload response');
  if (uploaded.build.status === 'awaiting_confirmation') {
    await page.getByRole('heading', { exact: true, name: 'Xác nhận dựng lộ trình' }).waitFor();
    if (title !== null) await page.getByLabel('Tên khoá học').fill(title);
  } else if (uploaded.confirmed_at == null) {
    await page.getByRole('heading', { exact: true, name: 'Xác nhận dựng lộ trình' }).waitFor();
    if (title !== null) await page.getByLabel('Tên khoá học').fill(title);
  } else {
    await page.getByRole('heading', { exact: true, name: 'Lộ trình đã sẵn sàng' }).waitFor();
  }
  return { uploadId, buildId, courseId, status: uploaded.build.status };
}

async function confirmThroughUi(page, item, title) {
  if (!page.url().includes(`/ban-dung/${item.buildId}`)) {
    await page.goto(`${base}/ban-dung/${item.buildId}?course_id=${item.courseId}&upload_id=${item.uploadId}`, { waitUntil: 'networkidle' });
  }
  await page.getByRole('heading', { exact: true, name: 'Xác nhận dựng lộ trình' }).waitFor();
  await page.getByLabel('Tên khoá học').fill(title);
  const responsePromise = page.waitForResponse(candidate => candidate.request().method() === 'POST'
    && new URL(candidate.url()).pathname === `/api/v1/uploads/${item.uploadId}/build`);
  await page.getByRole('button', { name: 'Dựng lộ trình', exact: true }).click();
  const response = await responsePromise;
  assert.equal(response.status(), 200);
  assert.equal((await response.json()).status, 'queued');
}

async function waitForBuild(page, buildId, courseId, status) {
  let last = null;
  await waitFor(async () => {
    const response = await page.request.get(`${base}/api/v1/builds/${buildId}?course_id=${courseId}`);
    if (response.status() !== 200) return false;
    last = await response.json();
    assertPrivateBuildDto(last, 'build response');
    return last.status === status;
  }, `build ${status}`);
  return last;
}

async function waitFor(predicate, label, waitMs = timeoutMs) {
  const deadline = Date.now() + waitMs;
  while (Date.now() < deadline) {
    if (await predicate()) return;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function setTheme(page, theme) {
  const current = await page.locator('html').getAttribute('data-theme');
  if (current !== theme) {
    await page.getByRole('button', { name: current === 'dark' ? 'Bật chế độ sáng' : 'Bật chế độ tối' }).click();
  }
  assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
}

async function setViewportThemeScreens(page, audit, prefix, widths) {
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    for (const theme of ['light', 'dark']) {
      await setTheme(page, theme);
      const overflow = await page.evaluate(() => ({
        viewport: innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        elements: [...document.querySelectorAll('body *')].map(element => {
          const rect = element.getBoundingClientRect();
          return { tag: element.tagName, id: element.id,
            className: typeof element.className === 'string' ? element.className : '',
            text: element.textContent.trim().slice(0, 80), left: Math.round(rect.left), right: Math.round(rect.right),
            width: Math.round(rect.width), scrollWidth: element.scrollWidth, clientWidth: element.clientWidth };
        }).filter(element => element.right > innerWidth + 1 || element.left < -1
          || element.scrollWidth > element.clientWidth + 1)
          .sort((a, b) => b.right - a.right).slice(0, 12),
      }));
      assert.equal(overflow.documentWidth > overflow.viewport, false,
        `${prefix} ${width}px ${theme} horizontal overflow: ${JSON.stringify(overflow)}`);
      const targets = await inspectTargetSizes(page);
      assert.deepEqual(targets.filter(item => item.width < 44 || item.height < 44), [],
        `${prefix} ${width}px ${theme} visible controls must be at least 44x44`);
      const filename = `${prefix}-${width}-${theme}.png`;
      audit.screens.push(await screenshot(page, filename));
    }
  }
}

async function screenshot(page, filename, options = {}) {
  if (options.width) await page.setViewportSize({ width: options.width, height: 900 });
  if (options.theme) await setTheme(page, options.theme);
  await page.screenshot({ path: path.join(output, filename), fullPage: true });
  return { filename, width: (await page.evaluate(() => innerWidth)), theme: await page.locator('html').getAttribute('data-theme') };
}

async function runDesignInspection(page, audit) {
  const inspectScript = path.join(toolsRoot, '.agents/skills/design-taste-frontend/scripts/inspect.mjs');
  const snapshotPath = path.join(root, '.tmp/w14-progress-inspect.html');
  const inspectionOutput = path.join(output, 'taste-inspect');
  const inspectionReportPath = path.join(inspectionOutput, 'report.json');
  const logPath = path.join(output, 'taste-inspector.log');
  await fs.mkdir(path.dirname(snapshotPath), { recursive: true });
  await fs.mkdir(path.join(root, '.tmp/w14-taste-profiles'), { recursive: true });
  await fs.writeFile(snapshotPath, await staticSnapshot(page), 'utf8');
  audit.designInspectionReadiness = await page.evaluate(async () => {
    await document.fonts.ready;
    const element = document.querySelector('.builds-page');
    return {
      stylesheetCount: [...document.styleSheets].filter(sheet => {
        try { return Boolean(sheet.cssRules.length); } catch { return false; }
      }).length,
      fontLoaded: [...document.fonts].some(font => font.family === 'Be Vietnam Pro' && font.status === 'loaded'),
      pageWidth: element?.getBoundingClientRect().width ?? null,
      pageMaxWidth: element ? getComputedStyle(element).maxWidth : null,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: innerWidth,
    };
  });
  const result = spawnSync(process.execPath, [inspectScript, snapshotPath, '--out', inspectionOutput,
    '--widths', '1280,768,390', '--app', '--json'], {
    cwd: root,
    encoding: 'utf8',
    timeout: 180000,
    env: { ...process.env, TASTE_SKILL_TMP: path.join(root, '.tmp/w14-taste-profiles') },
  });
  await fs.writeFile(logPath, `${result.stdout || ''}${result.stderr || ''}${result.error ? `\n${result.error.name}: ${result.error.message}` : ''}`, 'utf8');
  const inspectionReport = JSON.parse(await fs.readFile(inspectionReportPath, 'utf8'));
  audit.designInspection = {
    source: 'static DOM and built CSS snapshot from the live authenticated RUNNING page; design-only, not HTTP acceptance evidence',
    acceptance: false,
    snapshot: path.relative(root, snapshotPath),
    output: path.relative(root, inspectionOutput),
    exitCode: result.status,
    signal: result.signal,
    findings: (inspectionReport.findings || []).map(({ level, id, width, message }) => ({ level, id, width, message })),
    log: path.relative(root, logPath),
  };
  assert.ok(result.status === 0 || result.status === 1,
    `design inspector did not produce a review report; see ${path.relative(root, logPath)}`);
  audit.assertions.push('taste inspector reviewed an authenticated live RUNNING page snapshot at 1280, 768, and 390px (design-only)');
}

async function staticSnapshot(page) {
  let content = (await page.content()).replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
  const stylesheetLinks = [...content.matchAll(/<link\b[^>]*rel=["']stylesheet["'][^>]*href=["']([^"']+)["'][^>]*>/gi)];
  for (const match of stylesheetLinks) {
    const assetName = path.basename(new URL(match[1], base).pathname);
    const cssPath = path.join(root, 'src/web/frontend/dist/assets', assetName);
    const css = await fs.readFile(cssPath, 'utf8');
    content = content.replace(match[0], `<style>${css}</style>`);
  }
  return content.replace(/<head([^>]*)>/i, `<head$1><base href="${base}/">`);
}

function assertPrivateBuildDto(value, label) {
  const forbidden = /(public_?id|internal_?path|artifact_?path|temporary_?path|source_?path|estimated_?cost|cost_?estimate)/i;
  const internalPath = /(?:[A-Z]:[\\/]|\/(?:tmp|internal|home|users)\/)/i;
  const visit = (item, current) => {
    if (typeof item === 'string') {
      assert.equal(internalPath.test(item), false, `${label} must not expose a local or internal path`);
      return;
    }
    if (!item || typeof item !== 'object') return;
    for (const [key, nested] of Object.entries(item)) {
      assert.equal(forbidden.test(key), false, `${label} must not expose private field ${current}${key}`);
      visit(nested, `${current}${key}.`);
    }
  };
  visit(value, '');
}

async function inspectTargetSizes(page) {
  return page.locator('.courses-header a, .courses-header button, .account-menu summary, '
    + '.builds-page a, .builds-page button, .builds-file-choice, .builds-rights')
    .evaluateAll(elements => elements.filter(element => element.getClientRects().length)
      .map(element => ({ name: element.getAttribute('aria-label') || element.textContent.trim(),
        width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height })));
}

async function assertFilePickerKeyboardFocus(page, audit) {
  const input = page.locator('#build-file');
  await page.evaluate(() => document.activeElement?.blur());
  let focused = false;
  for (let attempt = 0; attempt < 24; attempt += 1) {
    await page.keyboard.press('Tab');
    if (await input.evaluate(element => document.activeElement === element)) {
      focused = true;
      break;
    }
  }
  assert.equal(focused, true, 'the visually hidden native file input remains keyboard reachable');
  const outlineWidth = await page.locator('.builds-file-button').evaluate(element =>
    Number.parseFloat(getComputedStyle(element).outlineWidth));
  assert.ok(outlineWidth >= 2, 'the custom file-picker target shows a visible focus indicator');
  audit.assertions.push('file selection uses a visible 44px+ label target and the native input has a keyboard-visible focus indicator');
}

async function writeJson(filename, value) {
  await fs.writeFile(path.join(output, filename), JSON.stringify(value, null, 2) + '\n', 'utf8');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
