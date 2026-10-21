const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const toolsRoot = require('node:fs').existsSync(path.join(root, '.tmp/w01-browser-tools'))
  ? root : path.resolve(root, '../..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(toolsRoot, '.tmp/w01-browsers');
const { chromium } = require(path.join(toolsRoot, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(toolsRoot, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));

const base = process.env.W06_BASE_URL || 'http://127.0.0.1:8006';
const runtimeFile = process.env.W06_RUNTIME_JSON || path.join(root, 'report/w06-web-evidence/runtime.json');
const output = path.join(root, 'report/w06-web-evidence');
const password = 'W06 browser-only test password 2026!';
const expectedDocs = ['doc-1', 'nhap-mon-ml', 'naive-bayes', 'doc-6', 'xstk-ch3-1', 'doc-4'];

async function main() {
  await fs.mkdir(output, { recursive: true });
  const runtime = JSON.parse(await fs.readFile(runtimeFile, 'utf8'));
  assert.equal(runtime.database, 'disposable-postgresql');
  assert.equal(runtime.phaseBStore, 'postgresql');
  assert.equal(runtime.media, 'memory-only');
  assert.equal(runtime.mailer, 'fake');
  assert.equal(runtime.modelCalls, 0);
  assert.equal(runtime.modelCostUsd, 0);
  assert.equal(runtime.fixtureState.samples.length, 6);

  const browser = await chromium.launch();
  const audit = {
    realHttp: true,
    realPostgres: true,
    realArgon2: runtime.realArgon2,
    media: runtime.media,
    mailer: runtime.mailer,
    modelCalls: runtime.modelCalls,
    modelCostUsd: runtime.modelCostUsd,
    screens: [],
    apiResponses: [],
    assertions: [],
    pageErrors: [],
    rawConsoleErrors: [],
    consoleErrors: [],
    expectedConsoleErrors: [],
    failedRequests: [],
    externalRequests: [],
    fontRequests: [],
    rawFontFailures: [],
    expectedProbeRequests: [],
    fontFailures: [],
    accessibility: [],
    video: 'w06-join-resume.webm',
  };
  let stage = 'auth.register';
  const observe = page => {
    page.on('pageerror', error => audit.pageErrors.push(error.message));
    page.on('console', message => {
      if (message.type() !== 'error') return;
      const text = message.text();
      const event = { stage, text, expected: null };
      const expectedInitial401 = stage === 'auth.register'
        && text === 'Failed to load resource: the server responded with a status of 401 (Unauthorized)'
        && audit.apiResponses.some(response => response.stage === stage && response.method === 'GET'
          && response.path === '/api/v1/me' && response.status === 401);
      const expectedMock500 = stage === 'visual.mock.error'
        && text === 'Failed to load resource: the server responded with a status of 500 (Internal Server Error)'
        && audit.apiResponses.some(response => response.stage === stage && response.method === 'GET'
          && response.path === '/api/v1/courses' && response.status === 500);
      const axeProbeCsp = stage.startsWith('axe:') && (
        (text.startsWith("Connecting to 'https://fonts.googleapis.com/")
          && text.includes('violates the following Content Security Policy directive: "default-src \'self\'"')
          && text.endsWith('The action has been blocked.'))
        || (text.startsWith("Applying inline style violates the following Content Security Policy directive 'style-src-elem \'self\' https://fonts.googleapis.com'")
          && text.includes("Either the 'unsafe-inline' keyword") && text.endsWith('The action has been blocked.'))
      );
      if (expectedInitial401) event.expected = 'unauthenticated GET /api/v1/me during registration bootstrap';
      else if (expectedMock500) event.expected = 'deliberate mocked GET /api/v1/courses error state';
      else if (axeProbeCsp) event.expected = 'Axe injected probe blocked by the production CSP';
      audit.rawConsoleErrors.push(event);
      if (event.expected) audit.expectedConsoleErrors.push(event);
      else audit.consoleErrors.push(event);
    });
    page.on('requestfailed', request => {
      const url = new URL(request.url());
      const failure = { stage, method: request.method(), url: url.pathname, resourceType: request.resourceType(), error: request.failure()?.errorText };
      if (['https://fonts.googleapis.com', 'https://fonts.gstatic.com'].includes(url.origin)) {
        audit.rawFontFailures.push(failure);
        const axeFetchProbe = stage.startsWith('axe:')
          && url.origin === 'https://fonts.googleapis.com'
          && url.pathname === '/css2'
          && ['fetch', 'xhr'].includes(request.resourceType())
          && request.failure()?.errorText === 'csp';
        if (axeFetchProbe) audit.expectedProbeRequests.push(failure);
        else audit.fontFailures.push(failure);
      }
      else audit.failedRequests.push(failure);
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
        audit.fontFailures.push({ method: response.request().method(), url: url.pathname, status: response.status() });
      }
      if (url.pathname.startsWith('/api/')) audit.apiResponses.push({
        method: response.request().method(), path: url.pathname, status: response.status(), stage,
      });
    });
  };

  let context;
  let page;
  let video;
  try {
    context = await browser.newContext({ viewport: { width: 1280, height: 900 },
      recordVideo: { dir: path.join(root, 'tmp/w06-browser-video'), size: { width: 1280, height: 900 } } });
    page = await context.newPage();
    video = page.video();
    observe(page);
    await page.goto(`${base}/dang-ky`, { waitUntil: 'networkidle' });
    await page.getByLabel('Tên hiển thị').fill('Người học W06');
    await page.getByLabel('Email', { exact: true }).fill(`w06-${crypto.randomUUID()}@example.invalid`);
    await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
    const confirmation = page.getByLabel('Nhập lại mật khẩu', { exact: true });
    if (await confirmation.count()) await confirmation.fill(password);
    await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    await page.getByRole('heading', { name: 'Khoá học của tôi' }).waitFor();
    const identity = await (await page.request.get(`${base}/api/v1/me`)).json();
    assert.ok(identity.account?.id);
    assert.ok(identity.csrf_token);
    audit.assertions.push('real UI registration created an authenticated PostgreSQL account');
    stage = 'real.core-flow';

    await page.goto(`${base}/khoa-hoc`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Khoá học của tôi' }).waitFor();
    const fontStatus = await page.evaluate(async () => {
      await document.fonts.ready;
      const family = getComputedStyle(document.body).fontFamily;
      const loaded = [...document.fonts].some(font => font.family === 'Be Vietnam Pro' && font.status === 'loaded');
      return { family, loaded, matched: document.fonts.check('16px "Be Vietnam Pro"') };
    });
    assert.match(fontStatus.family, /Be Vietnam Pro/);
    assert.equal(fontStatus.loaded && fontStatus.matched, true, 'Be Vietnam Pro must load from the documented Google Fonts origins');
    audit.assertions.push('Be Vietnam Pro loaded successfully from the documented font origins');
    const coursesResponse = await page.request.get(`${base}/api/v1/courses`);
    assert.equal(coursesResponse.status(), 200);
    const initialCourses = await coursesResponse.json();
    assert.deepEqual(initialCourses.owned, []);
    assert.deepEqual(initialCourses.joined, []);
    assert.equal(initialCourses.samples.length, 6);
    assert.deepEqual(initialCourses.samples.map(course => course.doc_id).sort(), [...expectedDocs].sort());
    assert.deepEqual(initialCourses.samples.map(course => course.course_id).sort(),
      runtime.fixtureState.samples.map(course => course.courseId).sort());
    await fs.writeFile(path.join(output, 'courses-before-join.json'), JSON.stringify(initialCourses, null, 2));
    await page.getByRole('heading', { name: 'Khoá học mẫu' }).waitFor();

    const doc1 = initialCourses.samples.find(course => course.doc_id === 'doc-1');
    assert.ok(doc1);
    const doc1Card = page.locator('.course-card').filter({ hasText: doc1.title }).first();
    const joinDoc1 = page.waitForResponse(response => response.url().endsWith(`/api/v1/courses/${doc1.course_id}/join-sample`));
    await doc1Card.getByRole('button', { name: 'Tham gia', exact: true }).click();
    assert.equal((await joinDoc1).status(), 200);

    const secondSample = initialCourses.samples.find(course => course.doc_id === 'doc-6');
    const secondCard = page.locator('.course-card').filter({ hasText: secondSample.title }).first();
    const keyboardJoin = page.waitForResponse(response => response.url().endsWith(`/api/v1/courses/${secondSample.course_id}/join-sample`));
    await secondCard.getByRole('button', { name: 'Tham gia', exact: true }).focus();
    await page.keyboard.press('Enter');
    assert.equal((await keyboardJoin).status(), 200, 'Enter must activate a sample join button');

    const duplicateJoin = await page.request.post(`${base}/api/v1/courses/${doc1.course_id}/join-sample`, {
      headers: { Origin: base, 'X-CSRF-Token': identity.csrf_token },
      data: { owner: runtime.fixtureState.seedOwnerId, owner_id: runtime.fixtureState.seedOwnerId,
        doc_id: 'not-the-course', graph_version: 999 },
    });
    assert.equal(duplicateJoin.status(), 200, 'joining the same sample twice must be idempotent');
    const duplicateBody = await duplicateJoin.json();
    assert.equal(duplicateBody.course_id, doc1.course_id);
    assert.equal(duplicateBody.doc_id, 'doc-1');
    assert.equal(duplicateBody.published_graph_version, 8);
    assert.equal(duplicateBody.role, 'learner');

    const afterJoinResponse = await page.request.get(`${base}/api/v1/courses`);
    assert.equal(afterJoinResponse.status(), 200);
    const afterJoin = await afterJoinResponse.json();
    assert.equal(afterJoin.joined.filter(course => course.course_id === doc1.course_id).length, 1);
    assert.equal(afterJoin.joined.filter(course => course.course_id === secondSample.course_id).length, 1);
    await fs.writeFile(path.join(output, 'learner-state.json'), JSON.stringify({
      accountId: identity.account.id,
      joinedCourseIds: [doc1.course_id, secondSample.course_id],
      privateCourseId: runtime.fixtureState.privateCourseId,
      duplicateJoinStatus: duplicateJoin.status(),
    }, null, 2));
    await fs.writeFile(path.join(output, 'courses-after-join.json'), JSON.stringify(afterJoin, null, 2));
    await page.reload({ waitUntil: 'networkidle' });
    const joinedCard = page.locator('.course-card').filter({ hasText: doc1.title }).first();
    await joinedCard.getByRole('link', { name: 'Học tiếp' }).waitFor();
    const detailResponse = await page.request.get(`${base}/api/v1/courses/${doc1.course_id}`);
    assert.equal(detailResponse.status(), 200);
    const detail = await detailResponse.json();
    assert.equal(detail.course_id, doc1.course_id);
    assert.equal(detail.doc_id, 'doc-1');
    const roadmapResponse = await page.request.get(`${base}/api/v1/courses/${doc1.course_id}/roadmap`);
    assert.equal(roadmapResponse.status(), 200);
    const roadmap = await roadmapResponse.json();
    assert.equal(roadmap.course_id, doc1.course_id);
    assert.equal(roadmap.doc_id, 'doc-1');
    assert.equal(roadmap.graph_version, doc1.published_graph_version);
    assert.ok(roadmap.modules.length > 0);
    assert.ok(roadmap.modules.every(module => module.module_id && module.title));
    await fs.writeFile(path.join(output, 'doc-1-detail.json'), JSON.stringify(detail, null, 2));
    await fs.writeFile(path.join(output, 'doc-1-roadmap.json'), JSON.stringify(roadmap, null, 2));
    audit.assertions.push('real GET /courses returned six seeded samples; both joins and duplicate join persisted idempotently');
    audit.assertions.push('real doc-1 detail and roadmap returned the published graph version and modules');

    await joinedCard.getByRole('link', { name: 'Học tiếp' }).click();
    await page.waitForURL(url => url.pathname === `/khoa-hoc/${doc1.course_id}/module/${detail.resume.module_id}`);
    assert.equal(new URL(page.url()).pathname, `/khoa-hoc/${doc1.course_id}/module/${detail.resume.module_id}`);
    const resumeModule = roadmap.modules.find(module => module.module_id === detail.resume.module_id);
    assert.ok(resumeModule, 'resume module must exist in the real doc-1 roadmap');
    await page.getByRole('heading', { level: 1, name: detail.title }).waitFor();
    await page.getByRole('heading', { level: 2, name: resumeModule.title }).waitFor();
    audit.assertions.push('Học tiếp navigated to the joined course and its real resume module');
    await page.goto(`${base}/khoa-hoc`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Khoá học của tôi' }).waitFor();

    const privateId = runtime.fixtureState.privateCourseId;
    for (const [method, route, body] of [
      ['GET', `/api/v1/courses/${privateId}?owner=${encodeURIComponent(runtime.fixtureState.seedOwnerId)}`, undefined],
      ['GET', `/api/v1/courses/${privateId}/roadmap?owner=${encodeURIComponent(runtime.fixtureState.seedOwnerId)}&doc_id=doc-1&graph_version=8`, undefined],
      ['POST', `/api/v1/courses/${privateId}/join-sample`, { owner: runtime.fixtureState.seedOwnerId, doc_id: 'doc-1', graph_version: 8 }],
    ]) {
      const response = method === 'GET'
        ? await page.request.get(base + route)
        : await page.request.post(base + route, { headers: { Origin: base, 'X-CSRF-Token': identity.csrf_token }, data: body });
      assert.equal(response.status(), 404, `${method} ${new URL(base + route).pathname} must hide the private course`);
    }
    audit.assertions.push('an authenticated non-member got not_found for private detail, roadmap, and injected-owner join');

    for (const width of [390, 768, 1280]) {
      await page.setViewportSize({ width, height: 950 });
      for (const theme of ['light', 'dark']) {
        const current = await page.locator('html').getAttribute('data-theme');
        if (current !== theme) {
          await page.getByRole('button', { name: current === 'dark' ? 'Bật chế độ sáng' : 'Bật chế độ tối' }).click();
        }
        assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
        await page.getByRole('heading', { name: 'Khoá học của tôi' }).waitFor();
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false,
          `${width}px ${theme} layout must not overflow horizontally`);
        stage = `axe:${width}:${theme}`;
        let axe;
        try { axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze(); }
        finally { stage = 'real.core-flow'; }
        assert.deepEqual(axe.violations.map(violation => violation.id), [], `${width}px ${theme} axe violations`);
        assert.deepEqual(axe.incomplete, [], `${width}px ${theme} axe incomplete checks`);
        const iconContrast = await inspectIconContrast(page);
        assert.ok(iconContrast.length > 0, `${width}px ${theme} must expose visible header/course SVG icons for contrast checks`);
        for (const icon of iconContrast) {
          assert.ok(icon.ratio >= 3, `${width}px ${theme} icon ${icon.target} contrast must be at least 3:1`);
        }
        audit.accessibility.push({
          width, theme,
          violationCount: axe.violations.length,
          violations: axe.violations.map(violation => ({ id: violation.id, impact: violation.impact, nodes: violation.nodes.length })),
          incompleteCount: axe.incomplete.length,
          incomplete: axe.incomplete.map(result => ({
            id: result.id,
            impact: result.impact,
            nodes: result.nodes.map(node => ({
              target: node.target,
              html: node.html,
              failureSummary: node.failureSummary,
              any: node.any,
              all: node.all,
              none: node.none,
            })),
          })),
          nonTextIconContrast: iconContrast,
        });
        if (width === 390) {
          const smallTargets = await page.locator('.courses-page button, .courses-page a').evaluateAll(elements => elements
            .filter(element => element.getClientRects().length)
            .map(element => ({ name: element.textContent.trim(), width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height }))
            .filter(element => element.width < 44 || element.height < 44));
          assert.deepEqual(smallTargets, [], `${theme} course controls must be at least 44x44`);
          const smallHeaderTargets = await page.locator('.courses-header a, .courses-header button, .courses-header summary').evaluateAll(elements => elements
            .filter(element => element.getClientRects().length)
            .map(element => ({ name: element.textContent.trim() || element.getAttribute('aria-label'), width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height }))
            .filter(element => element.width < 44 || element.height < 44));
          assert.deepEqual(smallHeaderTargets, [], `${theme} visible header controls must be at least 44x44`);
        }
        const screenshot = `courses-${width}-${theme}.png`;
        await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
        audit.screens.push({ width, theme, screenshot, overflow: false });
      }
    }
    audit.assertions.push('real course page passed axe, responsive overflow, and 44x44 target checks at required viewports/themes');

    await page.emulateMedia({ reducedMotion: 'reduce' });
    assert.equal(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true);
    await page.goto(`${base}/khoa-hoc`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Khoá học của tôi' }).waitFor();
    await page.waitForTimeout(300);
    const runningAnimations = await page.evaluate(() => document.getAnimations().filter(animation => animation.playState === 'running').length);
    assert.equal(runningAnimations, 0);
    audit.assertions.push('reduced-motion browser preference leaves no running course-page animations');

    await page.keyboard.press('Tab');
    const tabState = await page.evaluate(() => ({
      interactive: document.activeElement?.matches('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])'),
      visible: Boolean(document.activeElement?.getClientRects().length),
      outlineStyle: getComputedStyle(document.activeElement).outlineStyle,
      outlineWidth: parseFloat(getComputedStyle(document.activeElement).outlineWidth),
    }));
    assert.equal(tabState.interactive && tabState.visible, true, 'Tab must focus a visible interactive element');
    assert.notEqual(tabState.outlineStyle, 'none', 'keyboard focus must have a visible outline');
    assert.ok(tabState.outlineWidth >= 2, 'keyboard focus outline must be at least 2px');
    audit.assertions.push('keyboard activation joined another real sample and Tab focused a visible control');
    audit.axeProbeCaveat = 'Axe injects CSS probes; exact CSP console messages during axe:* stages are preserved and counted as expected tool diagnostics. CSP remains unchanged; application-stage CSP errors still fail.';

    const visualPage = await context.newPage();
    observe(visualPage);
    const visualOnlyStates = [];
    for (const state of ['empty', 'loading', 'error']) {
      for (const width of [390, 1280]) {
        for (const theme of ['light', 'dark']) {
          stage = `visual.mock.${state}`;
          await visualPage.setViewportSize({ width, height: 950 });
          let releaseLoading;
          await visualPage.route('**/api/v1/courses', async route => {
            if (state === 'loading') return new Promise(resolve => { releaseLoading = () => {
              void route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ owned: [], joined: [], samples: [] }) }).then(resolve);
            }; });
            const body = state === 'error'
              ? { error: { code: 'internal_error' } }
              : { owned: [], joined: [], samples: [] };
            return route.fulfill({ status: state === 'error' ? 500 : 200, contentType: 'application/json', body: JSON.stringify(body) });
          });
          await visualPage.goto(`${base}/khoa-hoc`, { waitUntil: state === 'loading' ? 'domcontentloaded' : 'networkidle' });
          if (state === 'loading') await visualPage.getByRole('status', { name: 'Đang tải khoá học' }).waitFor();
          if (state === 'empty') await visualPage.getByText('Chưa có khoá học.', { exact: false }).waitFor();
          if (state === 'error') await visualPage.getByRole('alert').waitFor();
          await applyTheme(visualPage, theme);
          assert.equal(await visualPage.getByRole('heading', { name: 'Khoá học mẫu' }).count(), 0,
            `${state} mock state must not claim sample courses are available`);
          const screenshot = `mock-only-${state}-${width}-${theme}.png`;
          await visualPage.screenshot({ path: path.join(output, screenshot), fullPage: true });
          visualOnlyStates.push({ state, width, theme, screenshot, source: 'intercepted GET /api/v1/courses', acceptance: false });
          if (state === 'loading') {
            assert.equal(typeof releaseLoading, 'function');
            releaseLoading();
            await visualPage.getByRole('heading', { name: 'Khoá học của tôi' }).waitFor();
          }
          await visualPage.unroute('**/api/v1/courses');
        }
      }
    }
    stage = 'real.core-flow';
    audit.visualOnlyStates = visualOnlyStates;

    await page.goto(`${base}/khoa-hoc`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Khoá học của tôi' }).waitFor();
    await runDesignInspection(page, audit);

    assert.deepEqual(audit.pageErrors, []);
    assert.deepEqual(audit.consoleErrors, []);
    assert.equal(audit.expectedConsoleErrors.filter(event => event.expected === 'unauthenticated GET /api/v1/me during registration bootstrap').length, 1);
    const deliberateMockFailures = audit.apiResponses.filter(response => response.stage === 'visual.mock.error'
      && response.method === 'GET' && response.path === '/api/v1/courses' && response.status === 500).length;
    assert.equal(deliberateMockFailures, 4, 'the four intercepted error-state screenshots must each return the deliberate 500');
    assert.equal(audit.expectedConsoleErrors.filter(event => event.expected === 'deliberate mocked GET /api/v1/courses error state').length, deliberateMockFailures);
    assert.ok(audit.expectedConsoleErrors.filter(event => event.expected === 'Axe injected probe blocked by the production CSP')
      .every(event => event.stage.startsWith('axe:')));
    const axeFontConnectWarnings = audit.expectedConsoleErrors.filter(event => event.expected === 'Axe injected probe blocked by the production CSP'
      && event.text.startsWith("Connecting to 'https://fonts.googleapis.com/")).length;
    assert.equal(audit.expectedProbeRequests.length, axeFontConnectWarnings,
      'each Axe CSP font-fetch warning must have a matching blocked fetch/XHR request');
    assert.deepEqual(audit.failedRequests, []);
    assert.deepEqual(audit.externalRequests, []);
    assert.deepEqual(audit.fontFailures, []);
    console.log(JSON.stringify({ screens: audit.screens.length, assertions: audit.assertions.length,
      apiResponses: audit.apiResponses.length, rawConsoleErrors: audit.rawConsoleErrors.length,
      expectedConsoleErrors: audit.expectedConsoleErrors.length, genuineConsoleErrors: audit.consoleErrors.length,
      pageErrors: audit.pageErrors.length, failedRequests: audit.failedRequests.length,
      externalRequests: audit.externalRequests.length }));
  } finally {
    if (context) {
      try { await context.close(); } catch {}
      if (video) {
        try { await video.saveAs(path.join(output, audit.video)); }
        catch (error) { audit.videoSaveError = error.message; }
      }
    }
    try { await fs.writeFile(path.join(output, 'browser-audit.json'), JSON.stringify(audit, null, 2)); } catch {}
    await browser.close();
  }
}

async function runDesignInspection(page, audit) {
  const inspectScript = path.join(toolsRoot, '.agents/skills/design-taste-frontend/scripts/inspect.mjs');
  const snapshotPath = path.join(root, 'tmp/w06-course-inspect.html');
  const inspectionOutput = path.join(output, 'taste-inspect');
  await fs.mkdir(path.dirname(snapshotPath), { recursive: true });
  const content = await staticSnapshot(page);
  audit.designInspectionReadiness = await page.evaluate(async () => {
    await document.fonts.ready;
    const style = getComputedStyle(document.querySelector('.courses-page'));
    return {
      stylesheetCount: [...document.styleSheets].filter(sheet => {
        try { return Boolean(sheet.cssRules.length); } catch { return false; }
      }).length,
      fontLoaded: [...document.fonts].some(font => font.family === 'Be Vietnam Pro' && font.status === 'loaded'),
      pageWidth: document.querySelector('.courses-page')?.getBoundingClientRect().width ?? null,
      pageMaxWidth: style.maxWidth,
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: innerWidth,
    };
  });
  await fs.writeFile(snapshotPath, content, 'utf8');
  const tasteTmp = path.join(root, 'tmp/w06-taste-profiles');
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
    source: 'static snapshot of real authenticated course list; scripts removed; design review only',
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
    return [...document.querySelectorAll('.courses-header svg, .course-card__actions svg')]
      .filter(icon => icon.getClientRects().length)
      .map(icon => {
        const foreground = parse(getComputedStyle(icon).color);
        if (!foreground || foreground.a !== 1) throw new Error('Visible SVG icon foreground must resolve to an opaque computed color');
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
          target: icon.outerHTML.slice(0, 180),
          foreground: `rgb(${foreground.r}, ${foreground.g}, ${foreground.b})`,
          background: `rgb(${background.r}, ${background.g}, ${background.b})`,
          ratio: contrast(foreground, background),
        };
      });
  });
}

async function applyTheme(page, theme) {
  const current = await page.locator('html').getAttribute('data-theme');
  if (current !== theme) {
    await page.getByRole('button', { name: current === 'dark' ? 'Bật chế độ sáng' : 'Bật chế độ tối' }).click();
  }
  assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
}

main().catch(error => { console.error(error); process.exitCode = 1; });
