// W-02: real HTTP + PostgreSQL acceptance, isolated Chromium profiles.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const output = path.join(root, 'report/w02-evidence');
const url = process.env.W02_BASE_URL || 'http://127.0.0.1:8002';
const password = 'Riêng tư cho nghiệm thu W02!';

async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch();
  const audit = { baseUrl: url, screens: [], consoleErrors: [], expectedHttpDiagnostics: [], toolDiagnostics: [], requests: [], assertions: [] };
  let runningAxe = false;
  const observe = page => {
    page.on('pageerror', error => audit.consoleErrors.push(error.message));
    page.on('console', message => {
      if (message.type() !== 'error') return;
      const location = message.location().url;
      if (runningAxe) audit.toolDiagnostics.push(message.text());
      else if (/Failed to load resource: the server responded with a status of (401|422|429)/.test(message.text())
        && /\/api\/v1\/(me|auth\/login|auth\/register)$/.test(location)) {
        audit.expectedHttpDiagnostics.push({ text: message.text(), path: new URL(location).pathname });
      } else audit.consoleErrors.push(message.text());
    });
    page.on('response', response => {
      const parsed = new URL(response.url());
      if (parsed.pathname.startsWith('/api/')) audit.requests.push({ method: response.request().method(), path: parsed.pathname, status: response.status() });
    });
  };
  try {
    for (const width of [390, 768, 1280]) {
      for (const theme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: theme });
        const page = await context.newPage(); observe(page);
        for (const screen of ['dang-nhap', 'dang-ky']) {
          await page.goto(url + '/' + screen, { waitUntil: 'networkidle' });
          await page.locator('button[type="submit"]').waitFor({ state: 'visible' });
          await page.evaluate(() => document.fonts.ready);
          assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
          assert.equal(await page.evaluate(() => document.fonts.check('16px "Be Vietnam Pro"')
            && [...document.fonts].some(font => font.family === 'Be Vietnam Pro' && font.status === 'loaded')), true);
          const brokenImages = await page.locator("img").evaluateAll(images => images.filter(img => !img.complete || img.naturalWidth === 0).map(img => img.getAttribute("src")));
          assert.deepEqual(brokenImages, [], screen + " broken images");
          const undersized = await page.locator('button, input, .auth-switch, .auth-alternate a, .auth-demo-note a').evaluateAll(elements => elements.map(el => {
            const rect = el.getBoundingClientRect();
            return { name: el.getAttribute('aria-label') || el.textContent || el.getAttribute('name'), width: rect.width, height: rect.height };
          }).filter(rect => rect.width > 0 && rect.height > 0 && (rect.width < 44 || rect.height < 44)));
          assert.deepEqual(undersized, [], screen + ' touch targets');
          const screenshot = screen + '-' + width + '-' + theme + '.png';
          await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
          runningAxe = true;
          const a11y = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
          runningAxe = false;
          audit.screens.push({ screen, width, theme, screenshot, overflow: false, accessibilityViolations: a11y.violations });
          assert.deepEqual(a11y.violations, [], screen + ' accessibility');
        }
        await context.close();
      }
    }
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, colorScheme: 'light' });
    const page = await context.newPage(); observe(page);
    const email = 'w02-browser-' + Date.now() + '@example.vn';
    await page.goto(url + '/dang-ky', { waitUntil: 'networkidle' });
    await page.getByLabel('Tên hiển thị').fill('Người học nghiệm thu');
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
    await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill('Chưa giống mật khẩu');
    await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    await page.getByRole('alert').filter({ hasText: 'chưa khớp' }).waitFor();
    assert.equal(await page.getByLabel('Nhập lại mật khẩu', { exact: true }).getAttribute('aria-invalid'), 'true');
    await page.screenshot({ path: path.join(output, 'register-validation-390.png'), fullPage: true });
    await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill(password);
    const registerResponse = page.waitForResponse(response => response.url().endsWith('/api/v1/auth/register') && response.request().method() === 'POST');
    const meResponse = page.waitForResponse(response => response.url().endsWith('/api/v1/me') && response.status() === 200);
    await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    const registration = await (await registerResponse).json();
    const me = await (await meResponse).json();
    await page.getByRole('heading', { name: 'Tài khoản của bạn' }).waitFor();
    assert.ok(page.url().endsWith('/tai-khoan'));
    await page.screenshot({ path: path.join(output, 'account-390.png'), fullPage: true });
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Tài khoản của bạn' }).waitFor();
    const logoutResponse = page.waitForResponse(response => response.url().endsWith('/api/v1/auth/logout'));
    await page.locator('.account-menu summary').click();
    await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
    const logoutResult = await logoutResponse;
    const logout = await logoutResult.json();
    assert.equal(logoutResult.status(), 200);
    await page.waitForURL(current => current.pathname === '/dang-nhap').catch(async error => {
      console.error(JSON.stringify({ stage: "logout_redirect", url: page.url(), response: logout, alerts: await page.getByRole("alert").allTextContents() }));
      throw error;
    });
    await page.goto(url + '/tai-khoan', { waitUntil: 'networkidle' });
    assert.ok(page.url().includes('/dang-nhap'));
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Mật khẩu', { exact: true }).fill('Mật khẩu nhập sai');
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await page.getByRole('alert').filter({ hasText: 'chưa đúng' }).waitFor();
    await page.screenshot({ path: path.join(output, 'login-invalid-390.png'), fullPage: true });
    await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
    const loginResponse = page.waitForResponse(response => response.url().endsWith('/api/v1/auth/login') && response.status() === 200);
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    const login = await (await loginResponse).json();
    await page.getByRole('heading', { name: 'Tài khoản của bạn' }).waitFor();
    const examples = {
      note: 'Actual responses from disposable PostgreSQL acceptance runtime; session CSRF values redacted. No passwords or cookies saved.',
      register: { status: 200, body: registration },
      login: { status: 200, body: { ...login, csrf_token: '[REDACTED: session-specific CSRF]' } },
      me: { status: 200, body: { ...me, csrf_token: '[REDACTED: session-specific CSRF]' } },
      logout: { status: 200, body: logout },
    };
    await fs.writeFile(path.join(output, 'api-examples.json'), JSON.stringify(examples, null, 2));
    await page.locator('.account-menu summary').click();
    await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
    await page.waitForURL(current => current.pathname === '/dang-nhap');
    await page.goto(url + '/dang-ky', { waitUntil: 'networkidle' });
    await page.getByLabel('Tên hiển thị').fill('Không thay thế tài khoản');
    await page.getByLabel('Email', { exact: true }).fill(email.toUpperCase());
    await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
    await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'Yêu cầu đăng ký đã được tiếp nhận' }).waitFor();
    assert.ok(page.url().endsWith('/dang-ky'));
    await page.screenshot({ path: path.join(output, 'register-generic-390.png'), fullPage: true });
    await page.goto(url + '/dang-nhap', { waitUntil: 'networkidle' });
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Mật khẩu', { exact: true }).fill('Sai mật khẩu nhiều lần');
    for (let attempt = 0; attempt < 4; attempt++) {
      const failed = page.waitForResponse(response => response.url().endsWith('/api/v1/auth/login') && response.status() === 401);
      await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
      await failed;
      await page.getByRole('button', { name: 'Đăng nhập', exact: true }).waitFor({ state: 'visible' });
    }
    const throttled = page.waitForResponse(response => response.url().endsWith('/api/v1/auth/login') && response.status() === 429);
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    assert.equal((await throttled).status(), 429);
    await page.getByRole('alert').filter({ hasText: /Thử lại sau .*phút/ }).waitFor();
    await page.screenshot({ path: path.join(output, 'login-rate-limited-390.png'), fullPage: true });
    audit.assertions.push('registration_auto_login', 'confirmation_inline_validation', 'cookie_survives_reload', 'csrf_logout_to_login_stable', 'protected_route_redirect', 'generic_duplicate_no_session', 'login_invalid_credentials', 'rate_limited_with_minutes');
    await context.close();
    const reduced = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });
    const motionPage = await reduced.newPage(); observe(motionPage);
    await motionPage.goto(url + '/dang-nhap', { waitUntil: 'networkidle' });
    assert.equal(await motionPage.evaluate(() => document.getAnimations().filter(a => a.playState === 'running').length), 0);
    audit.assertions.push('auth_reduced_motion_no_running_animation');
    await reduced.close();
    assert.deepEqual(audit.consoleErrors, []);
    await fs.writeFile(path.join(output, 'browser-audit.json'), JSON.stringify(audit, null, 2));
    console.log(JSON.stringify({ screens: audit.screens.length, assertions: audit.assertions.length, consoleErrors: audit.consoleErrors.length }));
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
