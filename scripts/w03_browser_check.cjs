// Real HTTP, auth and PostgreSQL; only mail delivery/clock are fake in the isolated runner.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const base = process.env.W03_BASE_URL || 'http://127.0.0.1:8003';
const output = path.join(root, 'report/w03-evidence');
const originalPassword = 'Riêng tư cho nghiệm thu W03!';
const newPassword = 'Mật khẩu khôi phục riêng W03!';
const genericReset = 'Nếu email có tài khoản, bạn sẽ nhận được thư đặt lại mật khẩu.';

async function mailLink(page, email, kind) {
  const messages = await (await page.request.get(base + '/__test__/mail?email=' + encodeURIComponent(email))).json();
  const mail = messages.filter(message => message.subject.includes(kind)).at(-1);
  assert.ok(mail, 'expected mail message');
  const link = mail.body.match(/https?:\/\/[^\s<>]+[#?]token=[A-Za-z0-9_-]+/)[0];
  assert.equal(new URL(link).search, '', 'new mail tokens must not go into request query strings');
  assert.ok(new URL(link).hash.startsWith('#token='));
  return link;
}

async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch();
  const audit = { realHttp: true, realPostgres: true, fakeMailer: true, screens: [], assertions: [], pageErrors: [], requests: [] };
  const observe = page => {
    page.on('pageerror', error => audit.pageErrors.push(error.message));
    page.on('response', response => {
      const url = new URL(response.url());
      if (url.pathname.startsWith('/api/')) audit.requests.push({ method: response.request().method(), path: url.pathname, status: response.status() });
    });
  };
  try {
    const requestContext = await browser.newContext();
    const fixtures = await (await requestContext.request.get(base + '/__test__/fixtures')).json();
    await requestContext.close();
    for (const width of [390, 768, 1280]) for (const theme of ['light', 'dark']) {
      const context = await browser.newContext({ viewport: { width, height: 950 }, colorScheme: theme });
      const page = await context.newPage(); observe(page);
      for (const [name, route] of [
        ['verify', '/xac-minh#token=' + fixtures.previewVerify],
        ['forgot', '/quen-mat-khau'],
        ['reset', '/dat-lai-mat-khau#token=' + fixtures.previewReset],
      ]) {
        await page.goto(base + route, { waitUntil: 'networkidle' });
        await page.locator('.auth-card h1').waitFor();
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
        const undersized = await page.locator('.auth-card button, .auth-card input, .auth-alternate a').evaluateAll(elements => elements.map(element => {
          const box = element.getBoundingClientRect();
          return { name: element.getAttribute('name') || element.textContent, width: box.width, height: box.height };
        }).filter(box => box.width > 0 && box.height > 0 && (box.width < 44 || box.height < 44)));
        assert.deepEqual(undersized, []);
        const a11y = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
        assert.deepEqual(a11y.violations.map(v => v.id), []);
        const screenshot = name + '-' + width + '-' + theme + '.png';
        await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
        audit.screens.push({ name, width, theme, screenshot, overflow: false, accessibilityViolations: 0 });
      }
      await context.close();
    }

    const context = await browser.newContext({ viewport: { width: 390, height: 950 }, recordVideo: { dir: path.join(root, '.tmp/w03-video'), size: { width: 390, height: 950 } } });
    const page = await context.newPage(); observe(page);
    const email = 'w03-browser@example.vn';
    await page.goto(base + '/dang-ky', { waitUntil: 'networkidle' });
    await page.getByLabel('Tên hiển thị').fill('Người học W03');
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Mật khẩu', { exact: true }).fill(originalPassword);
    await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill(originalPassword);
    await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    await page.getByRole('heading', { name: 'Tài khoản của bạn' }).waitFor();
    await page.getByText('Xác minh email để mời bạn qua email', { exact: true }).waitFor();
    await page.screenshot({ path: path.join(output, 'verification-banner-390.png'), fullPage: true });
    const verifyLink = await mailLink(page, email, 'Xác minh');
    await page.goto(verifyLink, { waitUntil: 'networkidle' });
    assert.equal(audit.requests.filter(r => r.path.endsWith('/verify-email')).length, 0, 'GET must not consume verification');
    await page.getByRole('button', { name: 'Xác minh email', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'Email đã được xác minh.' }).waitFor();
    assert.equal((await (await page.request.get(base + '/api/v1/me')).json()).account.email_verified, true);
    await page.screenshot({ path: path.join(output, 'verification-success-390.png'), fullPage: true });
    audit.assertions.push('register -> fake mail -> real verify updates account; GET does not consume token');

    for (const [fixture, route, word] of [
      ['expiredVerify', '/xac-minh', 'hết hạn'], ['usedVerify', '/xac-minh', 'được sử dụng'],
      ['expiredReset', '/dat-lai-mat-khau', 'hết hạn'], ['usedReset', '/dat-lai-mat-khau', 'được sử dụng'],
    ]) {
      await page.goto(base + route + '#token=' + fixtures[fixture], { waitUntil: 'networkidle' });
      if (route.includes('mat-khau')) {
        await page.getByLabel('Mật khẩu mới', { exact: true }).fill(newPassword);
        await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill(newPassword);
      }
      await page.locator('.auth-card button[type=submit], .auth-card button').filter({ hasText: route.includes('mat-khau') ? 'Đặt mật khẩu mới' : 'Xác minh email' }).first().click();
      await page.getByRole('alert').filter({ hasText: word }).waitFor();
      await page.screenshot({ path: path.join(output, fixture + '-390.png'), fullPage: true });
      assert.equal(await page.getByRole('alert').evaluate(el => getComputedStyle(el).outlineStyle), 'none');
      audit.assertions.push(fixture + ' is rejected by real API and shown correctly');
    }

    const secondContext = await browser.newContext();
    const oldLogin = await secondContext.request.post(base + '/api/v1/auth/login', {
      headers: { Origin: base }, data: { email, password: originalPassword },
    });
    assert.equal(oldLogin.status(), 200);
    assert.equal((await secondContext.request.get(base + '/api/v1/me')).status(), 200);

    await page.goto(base + '/quen-mat-khau', { waitUntil: 'networkidle' });
    await page.getByLabel('Email tài khoản', { exact: true }).fill('unknown-w03@example.vn');
    const unknownResponse = page.waitForResponse(r => r.url().endsWith('/password-reset/request'));
    await page.getByRole('button', { name: 'Gửi hướng dẫn đặt lại', exact: true }).click();
    const unknown = await (await unknownResponse).json();
    await page.getByRole('status').filter({ hasText: genericReset }).waitFor();
    assert.deepEqual(await (await page.request.get(base + '/__test__/mail?email=unknown-w03@example.vn')).json(), []);
    await page.goto(base + '/quen-mat-khau', { waitUntil: 'networkidle' });
    await page.getByLabel('Email tài khoản', { exact: true }).fill(email);
    const knownResponse = page.waitForResponse(r => r.url().endsWith('/password-reset/request'));
    await page.getByRole('button', { name: 'Gửi hướng dẫn đặt lại', exact: true }).click();
    const known = await (await knownResponse).json();
    assert.deepEqual(known, unknown);
    const resetLink = await mailLink(page, email, 'Đặt lại');
    await page.goto(resetLink, { waitUntil: 'networkidle' });
    await page.getByLabel('Mật khẩu mới', { exact: true }).fill(newPassword);
    await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill('Mật khẩu không trùng!');
    await page.getByRole('button', { name: 'Đặt mật khẩu mới', exact: true }).click();
    assert.equal(await page.getByLabel('Nhập lại mật khẩu', { exact: true }).getAttribute('aria-invalid'), 'true');
    await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill(newPassword);
    await page.getByRole('button', { name: 'Đặt mật khẩu mới', exact: true }).click();
    await page.getByRole('heading', { name: 'Đăng nhập WayFinder' }).waitFor();
    await page.getByRole('status').filter({ hasText: 'Đã đặt lại mật khẩu.' }).waitFor();
    assert.equal((await page.request.get(base + '/api/v1/me')).status(), 401);
    assert.equal((await secondContext.request.get(base + '/api/v1/me')).status(), 401);
    assert.equal((await page.request.post(base + '/api/v1/auth/login', { headers: { Origin: base }, data: { email, password: originalPassword } })).status(), 401);
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Mật khẩu', { exact: true }).fill(newPassword);
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await page.getByRole('heading', { name: 'Tài khoản của bạn' }).waitFor();
    audit.assertions.push('known/unknown reset response matches and unknown email receives no mail');
    audit.assertions.push('reset rejects mismatched confirmation locally, revokes both real sessions, old password fails and new password works');
    await secondContext.close();
    const flowVideo = page.video();
    await context.close();
    await flowVideo.saveAs(path.join(output, 'w03-auth-flow.webm'));

    const reduced = await browser.newContext({ viewport: { width: 390, height: 950 }, reducedMotion: 'reduce' });
    const reducedPage = await reduced.newPage(); observe(reducedPage);
    await reducedPage.goto(base + '/quen-mat-khau', { waitUntil: 'networkidle' });
    await reducedPage.getByRole('button', { name: 'Gửi hướng dẫn đặt lại', exact: true }).click();
    await reducedPage.getByRole('alert').waitFor();
    assert.equal(await reducedPage.evaluate(() => document.getAnimations().filter(a => a.playState === 'running').length), 0);
    audit.assertions.push('reduced motion has no running feedback animation');
    await reduced.close();
    assert.deepEqual(audit.pageErrors, []);
    await fs.writeFile(path.join(output, 'browser-audit.json'), JSON.stringify(audit, null, 2));
    console.log(JSON.stringify({ screens: audit.screens.length, assertions: audit.assertions.length, errors: audit.pageErrors.length }));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
