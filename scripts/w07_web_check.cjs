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

const base = process.env.W07_BASE_URL || 'http://127.0.0.1:8007';
const runtimeFile = process.env.W07_RUNTIME_JSON || path.join(root, 'report/w07-evidence/runtime.json');
const output = path.join(root, 'report/w07-evidence');
const password = 'W07 browser-only test password 2026!';

async function main() {
  await fs.mkdir(output, { recursive: true });
  const runtime = JSON.parse(await fs.readFile(runtimeFile, 'utf8'));
  assert.equal(runtime.database, 'disposable-postgresql');
  assert.equal(runtime.realArgon2, true);
  assert.equal(runtime.phaseBStore, 'postgresql');
  assert.equal(runtime.media, 'memory-only');
  assert.equal(runtime.mailer, 'fake');
  assert.equal(runtime.modelCalls, 0);
  assert.equal(runtime.modelCostUsd, 0);
  assert.equal(runtime.fixture.docId, 'doc-1');
  assert.equal(runtime.fixture.expectedGraphVersion, 8);
  assert.equal(runtime.fixture.sourceSha256Verified, true);
  const courseId = runtime.fixtureState.courseId;
  assert.ok(courseId);

  const browser = await chromium.launch();
  const audit = {
    realHttp: true,
    realPostgres: true,
    realArgon2: runtime.realArgon2,
    graph: { docId: runtime.fixtureState.docId, version: runtime.fixtureState.graphVersion },
    media: runtime.media,
    mailer: runtime.mailer,
    modelCalls: runtime.modelCalls,
    modelCostUsd: runtime.modelCostUsd,
    screens: [],
    apiResponses: [],
    assertions: [],
    rawConsoleErrors: [],
    consoleErrors: [],
    expectedConsoleErrors: [],
    pageErrors: [],
    failedRequests: [],
    externalRequests: [],
    fontRequests: [],
    rawFontFailures: [],
    expectedProbeRequests: [],
    fontFailures: [],
    accessibility: [],
    iconContrast: [],
    visualOnlyStates: [],
    video: 'w07-roadmap-progress.webm',
  };
  let stage = 'learner-a.register';
  let rollbackPutPath = null;
  const observe = page => {
    page.on('pageerror', error => audit.pageErrors.push({ stage, message: error.message }));
    page.on('console', message => {
      if (message.type() !== 'error') return;
      const text = message.text();
      const event = { stage, text, expected: null };
      const expectedInitial401 = /^learner-[ab]\.register$/.test(stage)
        && text === 'Failed to load resource: the server responded with a status of 401 (Unauthorized)'
        && audit.apiResponses.some(response => response.stage === stage && response.method === 'GET'
          && response.path === '/api/v1/me' && response.status === 401);
      const expectedMock500 = stage === 'visual.mock.error'
        && text === 'Failed to load resource: the server responded with a status of 500 (Internal Server Error)'
        && audit.apiResponses.some(response => response.stage === stage && response.method === 'GET'
          && response.path.endsWith('/progress') && response.status === 500);
      const expectedRollback500 = stage === 'rollback.injected-put' && rollbackPutPath !== null
        && text === 'Failed to load resource: the server responded with a status of 500 (Internal Server Error)'
        && audit.apiResponses.some(response => response.stage === stage && response.method === 'PUT'
          && response.path === rollbackPutPath && response.status === 500);
      const axeProbeCsp = stage.startsWith('axe:') && (
        (text.startsWith("Connecting to 'https://fonts.googleapis.com/")
          && text.includes('violates the following Content Security Policy directive: "default-src \'self\'"')
          && text.endsWith('The action has been blocked.'))
        || (text.startsWith("Applying inline style violates the following Content Security Policy directive 'style-src-elem \'self\' https://fonts.googleapis.com'")
          && text.includes("Either the 'unsafe-inline' keyword") && text.endsWith('The action has been blocked.'))
      );
      if (expectedInitial401) event.expected = 'unauthenticated GET /api/v1/me during registration bootstrap';
      else if (expectedMock500) event.expected = 'deliberate intercepted GET progress error state';
      else if (expectedRollback500) event.expected = 'deliberate intercepted PUT rollback fault';
      else if (axeProbeCsp) event.expected = 'Axe injected probe blocked by production CSP';
      audit.rawConsoleErrors.push(event);
      if (event.expected) audit.expectedConsoleErrors.push(event);
      else audit.consoleErrors.push(event);
    });
    page.on('requestfailed', request => {
      const url = new URL(request.url());
      const failure = { stage, method: request.method(), path: url.pathname,
        resourceType: request.resourceType(), error: request.failure()?.errorText };
      if (['https://fonts.googleapis.com', 'https://fonts.gstatic.com'].includes(url.origin)) {
        audit.rawFontFailures.push(failure);
        const axeFetchProbe = stage.startsWith('axe:')
          && url.origin === 'https://fonts.googleapis.com'
          && url.pathname === '/css2'
          && ['fetch', 'xhr'].includes(request.resourceType())
          && request.failure()?.errorText === 'csp';
        if (axeFetchProbe) audit.expectedProbeRequests.push(failure);
        else audit.fontFailures.push(failure);
      } else audit.failedRequests.push(failure);
    });
    page.on('request', request => {
      const url = new URL(request.url());
      if (url.origin === 'https://fonts.googleapis.com' || url.origin === 'https://fonts.gstatic.com') {
        audit.fontRequests.push(url.origin);
      } else if (url.origin !== new URL(base).origin) audit.externalRequests.push(url.origin);
    });
    page.on('response', response => {
      const url = new URL(response.url());
      if ((url.origin === 'https://fonts.googleapis.com' || url.origin === 'https://fonts.gstatic.com') && response.status() >= 400) {
        audit.fontFailures.push({ stage, method: response.request().method(), path: url.pathname, status: response.status() });
      }
      if (url.pathname.startsWith('/api/')) audit.apiResponses.push({
        method: response.request().method(), path: url.pathname, status: response.status(), stage,
      });
    });
  };

  let contextA;
  let contextB;
  let page;
  let video;
  try {
    const rawVideoDir = path.join(root, '.tmp/w07-browser-video');
    await fs.mkdir(rawVideoDir, { recursive: true });
    contextA = await browser.newContext({ viewport: { width: 1280, height: 900 },
      recordVideo: { dir: rawVideoDir, size: { width: 1280, height: 900 } } });
    page = await contextA.newPage();
    video = page.video();
    observe(page);
    const learnerA = await registerAndJoin(page, 'learner-a', courseId);
    audit.assertions.push('learner A registered through the UI and joined the real doc-1 sample course');

    stage = 'learner-a.roadmap';
    await page.goto(`${base}/khoa-hoc/${courseId}`, { waitUntil: 'networkidle' });
    const courseHeading = page.getByRole('heading', { level: 1, name: 'Đại số tuyến tính' });
    await courseHeading.waitFor();
    const fontStatus = await page.evaluate(async () => {
      await document.fonts.ready;
      const family = getComputedStyle(document.body).fontFamily;
      const loaded = [...document.fonts].some(font => font.family === 'Be Vietnam Pro' && font.status === 'loaded');
      return { family, loaded, matched: document.fonts.check('16px "Be Vietnam Pro"') };
    });
    assert.match(fontStatus.family, /Be Vietnam Pro/);
    assert.equal(fontStatus.loaded && fontStatus.matched, true, 'Be Vietnam Pro must load from its documented font origins');
    audit.assertions.push('Be Vietnam Pro loaded from its documented font origins');
    const roadmapResponse = await page.request.get(`${base}/api/v1/courses/${courseId}/roadmap`);
    assert.equal(roadmapResponse.status(), 200);
    const roadmap = await roadmapResponse.json();
    const progressResponse = await page.request.get(`${base}/api/v1/courses/${courseId}/progress`);
    assert.equal(progressResponse.status(), 200);
    const initialProgress = await progressResponse.json();
    assertRoadmap(roadmap, initialProgress, runtime.fixtureState);
    await writeJson('roadmap-doc-1.json', roadmap);
    await writeJson('progress-before.json', initialProgress);
    audit.assertions.push('real GET roadmap/progress returned doc-1 v8 with ordered nodes and matching module summaries');

    const firstModule = roadmap.modules[0];
    assert.ok(firstModule.concepts.length >= 3, 'doc-1 first module must provide nodes for learn/unlearn/rollback checks');
    const moduleButton = page.locator('button[aria-expanded]').filter({ hasText: firstModule.title }).first();
    await moduleButton.waitFor();
    assert.equal(await moduleButton.getAttribute('aria-expanded'), 'true', 'the first module starts expanded');
    await moduleButton.click();
    assert.equal(await moduleButton.getAttribute('aria-expanded'), 'false', 'the learner can collapse a module');
    await moduleButton.click();
    assert.equal(await moduleButton.getAttribute('aria-expanded'), 'true', 'the learner can expand a module');

    const learnedConcept = firstModule.concepts[0];
    const unmarkedConcept = firstModule.concepts[1];
    const rollbackConcept = firstModule.concepts[2];
    const learnedCheckbox = page.getByRole('checkbox', { name: `Đã học: ${learnedConcept.name}`, exact: true });
    const unmarkedCheckbox = page.getByRole('checkbox', { name: `Đã học: ${unmarkedConcept.name}`, exact: true });
    const rollbackCheckbox = page.getByRole('checkbox', { name: `Đã học: ${rollbackConcept.name}`, exact: true });
    await learnedCheckbox.waitFor();
    assert.equal(await learnedCheckbox.isChecked(), false);
    assert.equal(await unmarkedCheckbox.isChecked(), false);

    const markResponse = page.waitForResponse(response => response.request().method() === 'PUT'
      && response.url().endsWith(`/progress/${encodeURIComponent(learnedConcept.node_id)}`));
    await learnedCheckbox.click();
    assert.equal((await markResponse).status(), 200, 'successful learner mark must reach the real HTTP endpoint');
    assert.equal(await learnedCheckbox.isChecked(), true);

    const keyboardResponse = page.waitForResponse(response => response.request().method() === 'PUT'
      && response.url().endsWith(`/progress/${encodeURIComponent(unmarkedConcept.node_id)}`));
    await unmarkedCheckbox.focus();
    await page.keyboard.press('Space');
    assert.equal((await keyboardResponse).status(), 200, 'Space activates the native learned checkbox');
    assert.equal(await unmarkedCheckbox.isChecked(), true);
    const unmarkResponse = page.waitForResponse(response => response.request().method() === 'PUT'
      && response.url().endsWith(`/progress/${encodeURIComponent(unmarkedConcept.node_id)}`));
    await unmarkedCheckbox.click();
    assert.equal((await unmarkResponse).status(), 200, 'learner can unmark a concept through the real HTTP endpoint');
    assert.equal(await unmarkedCheckbox.isChecked(), false);
    assert.equal(await learnedCheckbox.isChecked(), true, 'unmarking another concept leaves the learned marker intact');
    const afterSuccessfulWritesResponse = await page.request.get(`${base}/api/v1/courses/${courseId}/progress`);
    assert.equal(afterSuccessfulWritesResponse.status(), 200);
    const afterSuccessfulWrites = await afterSuccessfulWritesResponse.json();
    await assertUiProgressMatches(page, afterSuccessfulWrites, 'after successful mark/unmark writes');
    audit.assertions.push('real UI marked and unmarked concepts; keyboard Space activated the native checkbox');

    const failedPutPath = `/api/v1/courses/${courseId}/progress/${encodeURIComponent(rollbackConcept.node_id)}`;
    rollbackPutPath = failedPutPath;
    let releaseFailure;
    let interceptedFailure;
    const failureSeen = new Promise(resolve => { interceptedFailure = resolve; });
    const failureGate = new Promise(resolve => { releaseFailure = resolve; });
    let injectedFailures = 0;
    await page.route(`${base}${failedPutPath}`, async route => {
      if (route.request().method() !== 'PUT' || injectedFailures > 0) return route.continue();
      injectedFailures += 1;
      interceptedFailure();
      await failureGate;
      await route.fulfill({ status: 500, contentType: 'application/json',
        body: JSON.stringify({ error: { code: 'internal_error', message: 'Injected browser-only rollback fault' } }) });
    });
    stage = 'rollback.injected-put';
    const rollbackClick = rollbackCheckbox.click();
    try {
      await Promise.race([failureSeen, page.waitForTimeout(5000).then(() => { throw new Error('rollback PUT was not intercepted'); })]);
      assert.equal(await rollbackCheckbox.isChecked(), true,
        'optimistic checkbox must show checked while the injected PUT response is held');
      audit.assertions.push('rollback fault is explicitly an intercepted browser-only PUT, with optimistic state observed before rejection');
    } finally { releaseFailure(); }
    await rollbackClick;
    await page.getByRole('alert').waitFor();
    assert.equal(injectedFailures, 1);
    assert.equal(audit.apiResponses.filter(response => response.stage === 'rollback.injected-put'
      && response.method === 'PUT' && response.path === failedPutPath && response.status === 500).length, 1,
    'the only expected rollback 500 must be the exact intercepted PUT');
    assert.equal(audit.expectedConsoleErrors.filter(event => event.expected === 'deliberate intercepted PUT rollback fault').length, 1,
      'the exact intercepted rollback PUT response must account for one console error');
    stage = 'learner-a.roadmap';
    assert.equal(await rollbackCheckbox.isChecked(), false, '500 response must restore the prior unchecked value');
    await page.unroute(`${base}${failedPutPath}`);
    const afterRollbackResponse = await page.request.get(`${base}/api/v1/courses/${courseId}/progress`);
    assert.equal(afterRollbackResponse.status(), 200);
    const afterRollback = await afterRollbackResponse.json();
    assert.equal(afterRollback.nodes[rollbackConcept.node_id].state, 'not_learned',
      'the intercepted browser-only failure must not appear in the real server state');
    assert.equal(afterRollback.nodes[learnedConcept.node_id].state, 'learned');
    assert.equal(afterRollback.nodes[unmarkedConcept.node_id].state, 'not_learned');
    await assertUiProgressMatches(page, afterRollback, 'after the intercepted rollback');
    await writeJson('progress-after-rollback.json', afterRollback);
    audit.assertions.push('rollback restored UI and real GET progress confirmed the injected failure made no server write');

    const invalidNode = await page.request.put(`${base}/api/v1/courses/${courseId}/progress/not-a-published-node`, {
      headers: { Origin: base, 'X-CSRF-Token': learnerA.csrfToken }, data: { learned: true },
    });
    assert.equal(invalidNode.status(), 404, 'node outside the published graph must return not_found');
    assert.equal((await invalidNode.json()).error.code, 'not_found');
    const invalidShape = await page.request.put(`${base}/api/v1/courses/${courseId}/progress/${learnedConcept.node_id}`, {
      headers: { Origin: base, 'X-CSRF-Token': learnerA.csrfToken }, data: { learned: 'true' },
    });
    assert.equal(invalidShape.status(), 422, 'learned must be a JSON boolean');
    audit.assertions.push('real HTTP rejected an unpublished node and a non-boolean learned value');

    const moduleLink = page.getByRole('link', { name: `Mở module: ${firstModule.title}`, exact: true });
    await moduleLink.click();
    await page.waitForURL(url => url.pathname === `/khoa-hoc/${courseId}/module/${firstModule.module_id}`);
    await courseHeading.waitFor();
    await page.getByRole('heading', { level: 2, name: firstModule.title, exact: true }).waitFor();
    assert.equal(await page.getByRole('checkbox', { name: `Đã học: ${learnedConcept.name}`, exact: true }).isChecked(), true,
      'module route must read the same learner progress');
    await page.getByRole('link', { name: 'Quay lại lộ trình', exact: true }).click();
    await page.waitForURL(url => url.pathname === `/khoa-hoc/${courseId}`);
    await courseHeading.waitFor();
    audit.assertions.push('module route shows the real selected module and returns to the roadmap');

    stage = 'learner-b.register';
    contextB = await browser.newContext();
    const pageB = await contextB.newPage();
    observe(pageB);
    const learnerB = await registerAndJoin(pageB, 'learner-b', courseId);
    stage = 'learner-b.isolation';
    await pageB.goto(`${base}/khoa-hoc/${courseId}`, { waitUntil: 'networkidle' });
    await pageB.getByRole('heading', { level: 1, name: 'Đại số tuyến tính' }).waitFor();
    const progressBResponse = await pageB.request.get(`${base}/api/v1/courses/${courseId}/progress`);
    assert.equal(progressBResponse.status(), 200);
    const progressB = await progressBResponse.json();
    assert.equal(progressB.nodes[learnedConcept.node_id].state, 'not_learned',
      'learner B must not inherit learner A’s mark from the same course');
    assert.equal(progressB.nodes[unmarkedConcept.node_id].state, 'not_learned');
    const otherCourseGet = await pageB.request.get(`${base}/api/v1/courses/${runtime.fixtureState.privateCourseId}/progress`);
    assert.equal(otherCourseGet.status(), 404, 'a member of the sample course cannot read a private course progress');
    const otherCoursePut = await pageB.request.put(
      `${base}/api/v1/courses/${runtime.fixtureState.privateCourseId}/progress/${learnedConcept.node_id}`,
      { headers: { Origin: base, 'X-CSRF-Token': learnerB.csrfToken }, data: { learned: true } });
    assert.equal(otherCoursePut.status(), 404, 'a member of the sample course cannot write a private course progress');
    await writeJson('progress-learner-b.json', progressB);
    await fs.writeFile(path.join(output, 'learner-state.json'), JSON.stringify({
      courseId,
      learnerAId: learnerA.accountId,
      learnerBId: learnerB.accountId,
      learnedNodeId: learnedConcept.node_id,
      unmarkedNodeId: unmarkedConcept.node_id,
      rollbackNodeId: rollbackConcept.node_id,
      keyboardNodeId: unmarkedConcept.node_id,
    }, null, 2) + '\n', 'utf8');
    audit.assertions.push('a second UI-registered member joined the same real course but saw independent progress; private course progress stayed hidden');

    stage = 'real.visual';
    await page.goto(`${base}/khoa-hoc/${courseId}`, { waitUntil: 'networkidle' });
    await courseHeading.waitFor();
    for (const width of [390, 768, 1280]) {
      await page.setViewportSize({ width, height: 950 });
      for (const theme of ['light', 'dark']) {
        await setTheme(page, theme);
        const moduleToggle = page.locator('button[aria-expanded]').filter({ hasText: firstModule.title }).first();
        if (await moduleToggle.getAttribute('aria-expanded') !== 'true') await moduleToggle.click();
        assert.equal(await moduleToggle.getAttribute('aria-expanded'), 'true');
        assert.equal(await page.getByRole('checkbox', { name: `Đã học: ${learnedConcept.name}`, exact: true }).isChecked(), true);
        assert.equal(await page.getByRole('checkbox', { name: `Đã học: ${unmarkedConcept.name}`, exact: true }).isChecked(), false);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false,
          `${width}px ${theme} roadmap must not overflow horizontally`);
        stage = `axe:${width}:${theme}`;
        let axe;
        try { axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze(); }
        finally { stage = 'real.visual'; }
        assert.deepEqual(axe.violations.map(violation => violation.id), [], `${width}px ${theme} axe violations`);
        assert.deepEqual(axe.incomplete, [], `${width}px ${theme} axe incomplete checks`);
        const iconContrast = await inspectIconContrast(page);
        assert.ok(iconContrast.length > 0, `${width}px ${theme} must expose SVG controls for contrast inspection`);
        assert.ok(iconContrast.every(icon => icon.ratio >= 3), `${width}px ${theme} SVG icons must meet 3:1 contrast`);
        audit.iconContrast.push({ width, theme, checks: iconContrast });
        if (width === 390) {
          const undersized = await page.locator('.courses-page button, .courses-page a, .courses-page label:has(input[type="checkbox"])')
            .evaluateAll(elements => elements.filter(element => element.getClientRects().length)
              .map(element => ({ name: element.getAttribute('aria-label') || element.textContent.trim(),
                width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height }))
              .filter(element => element.width < 44 || element.height < 44));
          assert.deepEqual(undersized, [], `${theme} roadmap interactive targets must be at least 44x44`);
        }
        const screenshot = `roadmap-${width}-${theme}.png`;
        await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
        audit.screens.push({ width, theme, screenshot, moduleOpen: firstModule.module_id });
        audit.accessibility.push({ width, theme, violations: axe.violations.length, incomplete: axe.incomplete.length });
      }
    }
    audit.assertions.push('real roadmap passed Axe, responsive overflow, and 44x44 target checks at 390/768/1280 in both themes');
    await runDesignInspection(page, audit);

    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.reload({ waitUntil: 'networkidle' });
    await courseHeading.waitFor();
    assert.equal(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true);
    assert.equal(await page.evaluate(() => document.getAnimations().filter(animation => animation.playState === 'running').length), 0);
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
    audit.assertions.push('reduced-motion leaves no running animations and Tab shows a visible focus outline');

    await captureMockStates(contextA, courseId, initialProgress, roadmap, audit, observe, () => stage, value => { stage = value; });
    assert.equal(audit.expectedConsoleErrors.filter(event => event.expected === 'unauthenticated GET /api/v1/me during registration bootstrap').length, 2);
    const mock500s = audit.apiResponses.filter(response => response.stage === 'visual.mock.error'
      && response.method === 'GET' && response.path.endsWith('/progress') && response.status === 500).length;
    assert.equal(mock500s, 4, 'each mock error-state screenshot must use the intercepted progress 500');
    assert.equal(audit.expectedConsoleErrors.filter(event => event.expected === 'deliberate intercepted GET progress error state').length, mock500s);
    const fontWarnings = audit.expectedConsoleErrors.filter(event => event.expected === 'Axe injected probe blocked by production CSP'
      && event.text.startsWith("Connecting to 'https://fonts.googleapis.com/")).length;
    assert.equal(audit.expectedProbeRequests.length, fontWarnings,
      'every Axe CSP font warning must match the exact blocked fetch/XHR request');
    assert.deepEqual(audit.consoleErrors, []);
    assert.deepEqual(audit.pageErrors, []);
    assert.deepEqual(audit.failedRequests, []);
    assert.deepEqual(audit.externalRequests, []);
    assert.deepEqual(audit.fontFailures, []);
    console.log(JSON.stringify({ realScreens: audit.screens.length, mockScreens: audit.visualOnlyStates.length,
      assertions: audit.assertions.length, apiResponses: audit.apiResponses.length,
      rawConsoleErrors: audit.rawConsoleErrors.length, expectedConsoleErrors: audit.expectedConsoleErrors.length,
      genuineConsoleErrors: audit.consoleErrors.length, pageErrors: audit.pageErrors.length,
      failedRequests: audit.failedRequests.length, unexpectedExternalRequests: audit.externalRequests.length }));
  } finally {
    for (const context of [contextA, contextB]) {
      if (!context) continue;
      try { await context.close(); } catch {}
    }
    if (video) {
      try { await video.saveAs(path.join(output, audit.video)); }
      catch (error) { audit.videoSaveError = error.message; }
    }
    await fs.writeFile(path.join(output, 'browser-audit.json'), JSON.stringify(audit, null, 2) + '\n').catch(() => {});
    await browser.close();
  }
}

async function registerAndJoin(page, stage, courseId) {
  await page.goto(`${base}/dang-ky`, { waitUntil: 'networkidle' });
  await page.getByLabel('Tên hiển thị').fill(`Người học W07 ${stage.slice(-1).toUpperCase()}`);
  await page.getByLabel('Email', { exact: true }).fill(`w07-${stage}-${crypto.randomUUID()}@example.invalid`);
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
  const confirmation = page.getByLabel('Nhập lại mật khẩu', { exact: true });
  if (await confirmation.count()) await confirmation.fill(password);
  await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
  await page.getByRole('heading', { name: 'Khoá học của tôi' }).waitFor();
  const identityResponse = await page.request.get(`${base}/api/v1/me`);
  assert.equal(identityResponse.status(), 200);
  const identity = await identityResponse.json();
  assert.ok(identity.account?.id);
  assert.ok(identity.csrf_token);
  await page.goto(`${base}/khoa-hoc`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Khoá học mẫu' }).waitFor();
  const sampleCard = page.locator('.course-card').filter({ hasText: 'Đại số tuyến tính' }).first();
  const joined = page.waitForResponse(response => response.request().method() === 'POST'
    && response.url().endsWith(`/api/v1/courses/${courseId}/join-sample`));
  await sampleCard.getByRole('button', { name: 'Tham gia', exact: true }).click();
  assert.equal((await joined).status(), 200);
  const listResponse = await page.request.get(`${base}/api/v1/courses`);
  assert.equal(listResponse.status(), 200);
  const list = await listResponse.json();
  assert.ok(list.joined.some(course => course.course_id === courseId));
  return { accountId: identity.account.id, csrfToken: identity.csrf_token };
}

function assertRoadmap(roadmap, progress, fixture) {
  assert.equal(roadmap.course_id, fixture.courseId);
  assert.equal(roadmap.doc_id, 'doc-1');
  assert.equal(roadmap.graph_version, 8);
  assert.equal(roadmap.modules.length, fixture.moduleCount);
  assert.equal(roadmap.progress.learned, 0);
  assert.ok(roadmap.progress.total > 0);
  assert.equal(roadmap.progress.total, fixture.learnableNodeCount);
  assert.equal(progress.course_id, fixture.courseId);
  assert.equal(progress.contract_version, 'progress-1');
  assert.equal(progress.doc_id, 'doc-1');
  assert.equal(Object.keys(progress.nodes).length, fixture.learnableNodeCount);
  assert.ok(roadmap.modules.length > 0);
  const conceptIds = roadmap.modules.flatMap(module => module.concepts.map(concept => concept.node_id));
  assert.deepEqual(new Set(conceptIds), new Set(Object.keys(progress.nodes)));
  assert.equal(progress.modules.length, roadmap.modules.length);
  assert.deepEqual(roadmap.modules.map(module => module.index), [...roadmap.modules].map(module => module.index).sort((a, b) => a - b));
  for (const module of roadmap.modules) {
    const summary = progress.modules.find(row => row.module_id === module.module_id);
    assert.ok(summary);
    assert.deepEqual(module.progress, { learned: summary.learned, total: summary.total });
    assert.equal(summary.total, module.concepts.length);
  }
}

async function setTheme(page, theme) {
  const current = await page.locator('html').getAttribute('data-theme');
  if (current !== theme) {
    await page.getByRole('button', { name: current === 'dark' ? 'Bật chế độ sáng' : 'Bật chế độ tối' }).click();
  }
  assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
}

async function captureMockStates(context, courseId, progress, roadmap, audit, observe, getStage, setStage) {
  const page = await context.newPage();
  observe(page);
  const states = [];
  for (const state of ['empty', 'loading', 'error']) {
    for (const width of [390, 1280]) {
      for (const theme of ['light', 'dark']) {
        setStage(`visual.mock.${state}`);
        await page.setViewportSize({ width, height: 950 });
        let releaseLoading;
        let requestSeen;
        const seen = new Promise(resolve => { requestSeen = resolve; });
        const progressRoute = `**/api/v1/courses/${courseId}/progress`;
        const roadmapRoute = `**/api/v1/courses/${courseId}/roadmap`;
        if (state === 'empty') {
          const emptyRoadmap = { ...roadmap, modules: [], progress: { learned: 0, total: 0 } };
          await page.route(roadmapRoute, async route => {
            if (route.request().method() !== 'GET') return route.continue();
            return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(emptyRoadmap) });
          });
        }
        await page.route(progressRoute, async route => {
          if (route.request().method() !== 'GET') return route.continue();
          requestSeen();
          if (state === 'loading') return new Promise(resolve => { releaseLoading = () => {
            void route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(progress) }).then(resolve);
          }; });
          if (state === 'error') return route.fulfill({ status: 500, contentType: 'application/json',
            body: JSON.stringify({ error: { code: 'internal_error', message: 'mock-only progress failure' } }) });
          const empty = { ...progress, nodes: {}, modules: [] };
          return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(empty) });
        });
        const navigation = page.goto(`${base}/khoa-hoc/${courseId}`, { waitUntil: state === 'loading' ? 'domcontentloaded' : 'networkidle' });
        if (state === 'loading') {
          await seen;
          await page.getByRole('status', { name: 'Đang tải lộ trình' }).waitFor();
        } else if (state === 'error') await page.getByRole('alert').waitFor();
        else {
          await page.getByText('Chưa có bài học trong lộ trình này.', { exact: true }).waitFor();
          assert.equal(await page.getByRole('checkbox').count(), 0, 'empty roadmap has no progress checkboxes');
          assert.equal(await page.locator('button[aria-expanded]').count(), 0, 'empty roadmap has no module accordions');
        }
        await setTheme(page, theme);
        const screenshot = `mock-only-${state}-${width}-${theme}.png`;
        await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
        states.push({ state, width, theme, screenshot,
          source: state === 'empty' ? 'intercepted GET course roadmap and progress' : 'intercepted GET course progress',
          acceptance: false });
        if (state === 'loading') {
          assert.equal(typeof releaseLoading, 'function');
          releaseLoading();
          await navigation;
        }
        await page.unroute(progressRoute);
        if (state === 'empty') await page.unroute(roadmapRoute);
      }
    }
  }
  setStage('real.visual');
  audit.visualOnlyStates = states;
  await page.close();
}

async function writeJson(filename, value) {
  await fs.writeFile(path.join(output, filename), JSON.stringify(value, null, 2) + '\n', 'utf8');
}

async function assertUiProgressMatches(page, progress, moment) {
  const learned = Object.values(progress.nodes).filter(node => node.state === 'learned').length;
  const expected = `${learned}/${Object.keys(progress.nodes).length} bài học`;
  await page.waitForFunction(value =>
    document.querySelector('[aria-label="Tiến độ cả kho"] strong')?.textContent?.trim() === value, expected);
  const actual = (await page.locator('[aria-label="Tiến độ cả kho"] strong').textContent()).trim();
  assert.equal(actual, expected, `UI course summary must match latest GET progress ${moment}`);
}

async function inspectIconContrast(page) {
  return page.evaluate(() => {
    const parse = value => {
      const match = value.match(/rgba?\(([^)]+)\)/);
      if (!match) return null;
      const parts = match[1].split(',').map(part => Number.parseFloat(part.trim()));
      return { r: parts[0], g: parts[1], b: parts[2], a: parts.length > 3 ? parts[3] : 1 };
    };
    const luminance = ({ r, g, b }) => {
      const linear = channel => {
        const value = channel / 255;
        return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
    };
    const contrast = (first, second) => {
      const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
      return Number(((values[0] + 0.05) / (values[1] + 0.05)).toFixed(3));
    };
    return [...document.querySelectorAll('.courses-header svg, .roadmap-module__toggle svg, .roadmap-module__open svg, .roadmap-module__complete svg')]
      .filter(icon => icon.getClientRects().length)
      .map(icon => {
        const foreground = parse(getComputedStyle(icon).color);
        if (!foreground || foreground.a !== 1) throw new Error('Visible SVG icon foreground must be opaque');
        let ancestor = icon;
        let background = null;
        while (ancestor && !background) {
          const color = parse(getComputedStyle(ancestor).backgroundColor);
          if (color && color.a === 1) background = color;
          else if (color && color.a !== 0) throw new Error('SVG icon background must be opaque or transparent');
          ancestor = ancestor.parentElement;
        }
        if (!background) throw new Error('SVG icon has no opaque ancestor background');
        return {
          foreground: `rgb(${foreground.r}, ${foreground.g}, ${foreground.b})`,
          background: `rgb(${background.r}, ${background.g}, ${background.b})`,
          ratio: contrast(foreground, background),
        };
      });
  });
}

async function runDesignInspection(page, audit) {
  const inspectScript = path.join(toolsRoot, '.agents/skills/design-taste-frontend/scripts/inspect.mjs');
  const snapshotPath = path.join(root, '.tmp/w07-course-inspect.html');
  const inspectionOutput = path.join(output, 'taste-inspect');
  await fs.mkdir(path.dirname(snapshotPath), { recursive: true });
  const content = await staticSnapshot(page);
  audit.designInspectionReadiness = await page.evaluate(async () => {
    await document.fonts.ready;
    const pageElement = document.querySelector('.roadmap-content');
    return {
      stylesheetCount: [...document.styleSheets].filter(sheet => {
        try { return Boolean(sheet.cssRules.length); } catch { return false; }
      }).length,
      fontLoaded: [...document.fonts].some(font => font.family === 'Be Vietnam Pro' && font.status === 'loaded'),
      pageWidth: pageElement?.getBoundingClientRect().width ?? null,
      pageMaxWidth: pageElement ? getComputedStyle(pageElement).maxWidth : null,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: innerWidth,
    };
  });
  await fs.writeFile(snapshotPath, content, 'utf8');
  const tasteTmp = path.join(root, '.tmp/w07-taste-profiles');
  await fs.mkdir(tasteTmp, { recursive: true });
  const result = spawnSync(process.execPath, [inspectScript, snapshotPath, '--out', inspectionOutput,
    '--widths', '1280,768,390', '--app', '--json'], {
    cwd: root,
    encoding: 'utf8',
    timeout: 180000,
    env: { ...process.env, TASTE_SKILL_TMP: tasteTmp },
  });
  const logPath = path.join(output, 'taste-inspector.log');
  await fs.writeFile(logPath, `${result.stdout || ''}${result.stderr || ''}`, 'utf8');
  audit.designInspection = {
    source: 'static snapshot of real authenticated doc-1 roadmap; scripts removed and built CSS inlined; design review only',
    acceptance: false,
    snapshot: path.relative(root, snapshotPath),
    output: path.relative(root, inspectionOutput),
    exitCode: result.status,
    signal: result.signal,
    log: path.relative(root, logPath),
  };
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

main().catch(error => { console.error(error); process.exitCode = 1; });
