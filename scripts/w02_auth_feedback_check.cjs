// Scoped UI acceptance. Account API responses are mocked; no local accounts created.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs/promises');
const root = path.resolve(__dirname, '..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const base = process.env.W02_BASE_URL || 'http://127.0.0.1:8000';
const output = path.join(root, 'report/w02-auth-feedback');
const anonymous = { error: { code: 'unauthenticated' } };
async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch();
  const audit = { mockedAccountApi: true, cases: [], errors: [], toolDiagnostics: [] };
  let runningAxe = false;
  const observe = page => {
    page.on('pageerror', error => audit.errors.push(error.message));
    page.on('console', message => {
      if (message.type() !== 'error') return;
      if (runningAxe) audit.toolDiagnostics.push(message.text());
      else if (!message.text().includes('Failed to load resource: the server responded with a status of 401')) audit.errors.push(message.text());
    });
  };
  try {
    for (const width of [390, 1280]) for (const theme of ['light', 'dark']) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: theme });
      const page = await context.newPage(); observe(page);
      await page.addInitScript(() => {
        window.authProbe = { transitions: 0, finished: 0, feedbackTweenSeen: false, durations: [] };
        const original = document.startViewTransition?.bind(document);
        if (original) document.startViewTransition = update => {
          window.authProbe.transitions++;
          const transition = original(update);
          transition.ready.then(() => {
            window.authProbe.durations.push(...document.getAnimations().map(animation => animation.effect.getTiming().duration));
          });
          transition.finished.then(() => window.authProbe.finished++);
          return transition;
        };
        const sample = () => {
          const slot = document.querySelector('.auth-feedback-slot');
          if (slot) {
            const opacity = Number(getComputedStyle(slot).opacity);
            if (opacity > 0 && opacity < 1) window.authProbe.feedbackTweenSeen = true;
          }
          requestAnimationFrame(sample);
        };
        requestAnimationFrame(sample);
      });
      await page.route('**/api/v1/me', route => route.fulfill({ status: 401, json: anonymous }));
      await page.route('**/api/v1/auth/login', route => route.fulfill({ status: 401, json: { error: { code: 'invalid_credentials' } } }));
      await page.goto(base + '/dang-nhap', { waitUntil: 'networkidle' });
      await page.getByLabel('Email', { exact: true }).fill('linh@example.vn');
      await page.getByLabel('Mật khẩu', { exact: true }).fill('wrong-password');
      await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
      await page.getByRole('alert').waitFor();
      await page.waitForTimeout(230);
      const errorStyles = await page.evaluate(() => ({
        alertOutline: getComputedStyle(document.querySelector('[role=alert]')).outlineStyle,
        email: getComputedStyle(document.querySelector('#email')).borderColor,
        password: getComputedStyle(document.querySelector('.password-control')).borderColor,
        danger: getComputedStyle(document.querySelector('.field-error')).color,
        focusedAlert: document.activeElement === document.querySelector('[role=alert]'),
      }));
      assert.equal(errorStyles.alertOutline, 'none');
      assert.equal(errorStyles.focusedAlert, true);
      assert.equal(errorStyles.email, errorStyles.danger);
      assert.equal(errorStyles.password, errorStyles.danger);
      assert.equal(await page.locator('.field-error').count(), 2);
      await page.screenshot({ path: path.join(output, 'login-error-' + width + '-' + theme + '.png'), fullPage: true });
      await page.getByRole('link', { name: 'Tạo tài khoản', exact: true }).first().click();
      await page.getByRole('heading', { name: 'Tạo tài khoản WayFinder' }).waitFor();
      await page.waitForFunction(() => window.authProbe.transitions === window.authProbe.finished);
      assert.equal(await page.getByRole('alert').count(), 0);
      assert.equal(await page.getByLabel('Mật khẩu', { exact: true }).inputValue(), '');
      assert.equal(await page.getByLabel('Email', { exact: true }).inputValue(), '');
      await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
      await page.getByRole('alert').waitFor();
      await page.waitForTimeout(230);
      assert.equal(await page.locator('input[aria-invalid=true]').count(), 4);
      assert.equal(await page.locator('.field-error').count(), 4);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.getByLabel('Email', { exact: true }).focus();
      const invalidFocus = await page.getByLabel('Email', { exact: true }).evaluate(element => getComputedStyle(element).outlineColor);
      assert.equal(invalidFocus, errorStyles.danger);
      await page.screenshot({ path: path.join(output, 'register-error-' + width + '-' + theme + '.png'), fullPage: true });
      runningAxe = true;
      const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      runningAxe = false;
      assert.deepEqual(accessibility.violations, []);
      await page.getByRole('link', { name: 'Đăng nhập', exact: true }).first().click();
      await page.getByRole('heading', { name: 'Đăng nhập WayFinder' }).waitFor();
      await page.waitForFunction(() => window.authProbe.transitions === window.authProbe.finished);
      assert.equal(await page.getByRole('alert').count(), 0);
      const motion = await page.evaluate(() => window.authProbe);
      assert.equal(motion.transitions, 2);
      assert.equal(motion.feedbackTweenSeen, true);
      audit.cases.push({ width, theme, errorStyles, invalidFocus, motion, accessibilityViolations: 0 });
      await context.close();
    }
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage(); observe(page);
    await page.route('**/api/v1/me', route => route.fulfill({ status: 401, json: anonymous }));
    await page.route('**/api/v1/auth/login', route => route.fulfill({ status: 200, json: {
      account: { id: 'ui-probe', email: 'linh@example.vn', display_name: 'Linh', role: 'user', email_verified: false }, csrf_token: 'ui-probe' } }));
    await page.goto(base + '/dang-nhap', { waitUntil: 'networkidle' });
    await page.getByLabel('Email', { exact: true }).fill('linh@example.vn');
    await page.getByLabel('Mật khẩu', { exact: true }).fill('test-password');
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await page.getByRole('heading', { name: 'Tài khoản của bạn' }).waitFor();
    await page.getByRole('status').filter({ hasText: 'Đăng nhập thành công.' }).waitFor();
    await page.waitForTimeout(200);
    await page.screenshot({ path: path.join(output, 'login-success-390.png'), fullPage: true });
    await page.locator('.auth-notice').waitFor({ state: 'detached', timeout: 6000 });
    audit.cases.push({ successSurvivesNavigation: true, autoDismiss: true });
    await context.close();
    const reduced = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
    const reducedPage = await reduced.newPage(); observe(reducedPage);
    await reducedPage.route('**/api/v1/me', route => route.fulfill({ status: 401, json: anonymous }));
    await reducedPage.goto(base + '/dang-nhap', { waitUntil: 'networkidle' });
    await reducedPage.getByRole('link', { name: 'Tạo tài khoản', exact: true }).first().click();
    await reducedPage.getByRole('heading', { name: 'Tạo tài khoản WayFinder' }).waitFor();
    await reducedPage.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    await reducedPage.getByRole('alert').waitFor();
    const animations = await reducedPage.evaluate(() => document.getAnimations().filter(a => a.playState === 'running').length);
    assert.equal(animations, 0);
    audit.cases.push({ reducedMotion: true, runningAnimations: animations });
    await reduced.close();
    assert.deepEqual(audit.errors, []);
    await fs.writeFile(path.join(output, 'browser-audit.json'), JSON.stringify(audit, null, 2));
    console.log(JSON.stringify({ cases: audit.cases.length, errors: audit.errors.length }));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
