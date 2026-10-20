// Scoped account UI checks; all account API requests are mocked.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs/promises');
const root = path.resolve(__dirname, '..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const output = path.join(root, 'report/w02-account-menu');
const base = process.env.W02_BASE_URL || 'http://127.0.0.1:8000';

async function noticeGeometry(page, text) {
  await page.getByRole('status').filter({ hasText: text }).waitFor();
  await page.waitForTimeout(220);
  const geometry = await page.locator('.auth-notice-message').evaluate(element => {
    const box = element.getBoundingClientRect();
    const range = document.createRange(); range.selectNodeContents(element);
    const text = range.getBoundingClientRect();
    return { textCenterOffset: Math.abs(box.x + box.width / 2 - text.x - text.width / 2), rightGap: innerWidth - box.right, expectedRightGap: innerWidth < 768 ? 16 : 24, extraWidth: box.width - text.width, width: box.width };
  });
  assert.ok(geometry.textCenterOffset < 1, 'text must be centered inside notice: ' + JSON.stringify(geometry));
  assert.equal(geometry.rightGap, geometry.expectedRightGap, 'notice must stay on the right');
  assert.ok(geometry.extraWidth >= 24 && geometry.extraWidth <= 40, 'notice must fit its text: ' + JSON.stringify(geometry));
  return geometry;
}

async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch();
  const audit = { mockedAccountApi: true, cases: [], errors: [] };
  try {
    for (const width of [336, 390, 1280]) for (const theme of ['light', 'dark']) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: theme });
      const page = await context.newPage();
      page.on('pageerror', error => audit.errors.push(error.message));
      let logoutCsrf;
      await page.addInitScript(() => {
        window.logoutProbe = { calls: 0, finished: 0, durations: [] };
        const original = document.startViewTransition.bind(document);
        document.startViewTransition = update => {
          window.logoutProbe.calls++;
          const transition = original(update);
          transition.ready.then(() => window.logoutProbe.durations.push(...document.getAnimations().map(a => a.effect.getTiming().duration)));
          transition.finished.then(() => window.logoutProbe.finished++);
          return transition;
        };
      });
      await page.route('**/api/v1/me', route => route.fulfill({ status: 401, json: { error: { code: 'unauthenticated' } } }));
      await page.route('**/api/v1/auth/login', route => route.fulfill({ json: {
        account: { id: 'ui-account', email: 'linh.nguyen0812@example.com', display_name: 'Linh Nguyễn', role: 'user', email_verified: false }, csrf_token: 'ui-csrf',
      } }));
      await page.route('**/api/v1/auth/logout', route => {
        logoutCsrf = route.request().headers()['x-csrf-token'];
        return route.fulfill({ json: { message: 'Đã đăng xuất.' } });
      });
      await page.goto(base + '/dang-nhap', { waitUntil: 'networkidle' });
      await page.getByLabel('Email', { exact: true }).fill('linh.nguyen0812@example.com');
      await page.getByLabel('Mật khẩu', { exact: true }).fill('ui-password');
      await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
      await page.getByRole('heading', { name: 'Tài khoản của bạn' }).waitFor();
      const loginNotice = await noticeGeometry(page, 'Đăng nhập thành công.');
      await page.locator('.account-menu summary').click();
      const menu = await page.locator('.account-menu-panel').evaluate(element => {
        const box = element.getBoundingClientRect();
        const email = element.querySelector('.account-menu-email') || element.querySelector('span');
        const emailBox = email.getBoundingClientRect();
        const button = element.querySelector('button').getBoundingClientRect();
        return { left: box.left, right: box.right, emailHeight: emailBox.height, lineHeight: parseFloat(getComputedStyle(email).lineHeight), buttonHeight: button.height, viewport: innerWidth };
      });
      assert.ok(menu.left >= 0 && menu.right <= menu.viewport);
      assert.ok(menu.emailHeight <= menu.lineHeight + 1, 'email must stay on one line');
      assert.ok(menu.buttonHeight >= 44);
      const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      assert.deepEqual(accessibility.violations.map(v => v.id), []);
      await page.screenshot({ path: path.join(output, 'menu-' + width + '-' + theme + '.png') });
      await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
      await page.getByRole('heading', { name: 'Đăng nhập WayFinder' }).waitFor();
      await page.waitForFunction(() => window.logoutProbe.calls === window.logoutProbe.finished);
      const logoutNotice = await noticeGeometry(page, 'Đã đăng xuất.');
      const motion = await page.evaluate(() => window.logoutProbe);
      assert.equal(motion.calls, 1);
      assert.ok(motion.durations.some(duration => duration > 0 && duration <= 250));
      assert.equal(logoutCsrf, 'ui-csrf');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      assert.equal(new URL(page.url()).pathname, '/dang-nhap');
      await page.screenshot({ path: path.join(output, 'logout-' + width + '-' + theme + '.png') });
      audit.cases.push({ width, theme, menu, loginNotice, logoutNotice, motion, accessibilityViolations: 0 });
      await context.close();
    }
    for (const scenario of [{ width: 390, long: true }, { width: 1280, long: true }, { width: 390, reduced: true }]) {
      const context = await browser.newContext({ viewport: { width: scenario.width, height: 900 }, reducedMotion: scenario.reduced ? 'reduce' : 'no-preference' });
      const page = await context.newPage();
      page.on('pageerror', error => audit.errors.push(error.message));
      const email = scenario.long ? 'a'.repeat(64) + '@' + 'b'.repeat(63) + '.' + 'c'.repeat(63) + '.' + 'd'.repeat(58) + '.vn' : 'linh@example.vn';
      await page.addInitScript(() => {
        window.transitionCalls = 0;
        const original = document.startViewTransition.bind(document);
        document.startViewTransition = update => { window.transitionCalls++; return original(update); };
      });
      await page.route('**/api/v1/me', route => route.fulfill({ json: { account: {
        id: 'ui-account', email, display_name: scenario.long ? 'Đ'.repeat(60) : 'Linh', role: 'user', email_verified: false,
      }, csrf_token: 'ui-csrf' } }));
      await page.route('**/api/v1/auth/logout', route => route.fulfill({ json: { message: 'Đã đăng xuất.' } }));
      await page.goto(base + '/tai-khoan', { waitUntil: 'networkidle' });
      await page.locator('.account-menu summary').click();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      if (scenario.long) {
        const clipped = await page.locator('.account-menu-email').evaluate(element => ({
          clipped: element.scrollWidth > element.clientWidth, ellipsis: getComputedStyle(element).textOverflow,
          title: element.title, lineHeight: parseFloat(getComputedStyle(element).lineHeight), height: element.getBoundingClientRect().height,
        }));
        assert.equal(clipped.clipped, true);
        assert.equal(clipped.ellipsis, 'ellipsis');
        assert.equal(clipped.title, email);
        assert.ok(clipped.height <= clipped.lineHeight + 1);
        await page.screenshot({ path: path.join(output, 'menu-long-' + scenario.width + '.png') });
        audit.cases.push({ ...scenario, clipped });
      } else {
        await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
        await page.getByRole('heading', { name: 'Đăng nhập WayFinder' }).waitFor();
        const notice = await noticeGeometry(page, 'Đã đăng xuất.');
        const motion = await page.evaluate(() => ({ transitions: window.transitionCalls, animations: document.getAnimations().filter(a => a.playState === 'running').length }));
        assert.deepEqual(motion, { transitions: 0, animations: 0 });
        audit.cases.push({ ...scenario, notice, motion });
      }
      await context.close();
    }
    assert.deepEqual(audit.errors, []);
    await fs.writeFile(path.join(output, 'browser-audit.json'), JSON.stringify(audit, null, 2));
    console.log(JSON.stringify({ cases: audit.cases.length, errors: audit.errors.length }));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
