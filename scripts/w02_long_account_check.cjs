// Rendering probe: API response is mocked with valid maximum-length account text.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));
const url = process.env.W02_BASE_URL || 'http://127.0.0.1:8000';
const output = path.join(root, 'report/w02-evidence');
async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch();
  const screens = [];
  try {
    for (const width of [390, 1280]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      const page = await context.newPage();
      await page.route('**/api/v1/me', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        account: { id: 'layout-probe-only', email: 'a'.repeat(64) + '@' + 'b'.repeat(63) + '.' + 'c'.repeat(63) + '.' + 'd'.repeat(58) + '.vn',
          display_name: 'Đ'.repeat(60), role: 'user', email_verified: false }, csrf_token: 'layout-probe-only' }) }));
      await page.goto(url + '/tai-khoan', { waitUntil: 'networkidle' });
      await page.getByRole('heading', { name: 'Tài khoản của bạn' }).waitFor();
      assert.equal(await page.locator('.account-menu-name').evaluate(el => el.scrollWidth > el.clientWidth && getComputedStyle(el).textOverflow === 'ellipsis'), true);
      await page.locator('.account-menu summary').click();
      await page.getByRole('button', { name: 'Đăng xuất', exact: true }).waitFor();
      await page.locator('.account-menu summary').click();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      const screenshot = 'account-long-text-' + width + '.png';
      await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
      screens.push({ width, overflow, screenshot, data: 'Mocked account response; 60-character unbroken display name and 254-character valid email.' });
      assert.equal(overflow, false, 'Long account text overflows at ' + width);
      await context.close();
    }
    await fs.writeFile(path.join(output, 'long-account-audit.json'), JSON.stringify({ screens }, null, 2));
    console.log(JSON.stringify({ screens: screens.length, overflow: false }));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
