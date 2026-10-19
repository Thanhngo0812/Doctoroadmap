// Run after stopping only the W-01 dev DB. Restart it immediately afterwards.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));

(async () => {
  const response = await fetch('http://127.0.0.1:8000/api/v1/health');
  const health = await response.json();
  assert.equal(response.status, 503);
  assert.equal(health.db, 'down');
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 900 } });
    await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
    await page.locator('.health-error').waitFor();
    const retryResponse = page.waitForResponse(response =>
      new URL(response.url()).pathname === '/api/v1/health' && response.request().method() === 'GET');
    await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
    assert.equal((await retryResponse).status(), 503);
    await page.locator('.health-error').waitFor();
    assert.match(await page.locator('.health-copy').innerText(), /không kết nối/);
    const output = path.join(root, 'report/w01-evidence');
    await fs.mkdir(output, { recursive: true });
    await page.locator('.health-card').screenshot({ path: path.join(output, 'database-down-390.png') });
    await fs.writeFile(path.join(output, 'database-down.json'), JSON.stringify({
      http_status: response.status, retry_http_status: 503, health, assertion: 'database_failure_is_visible_and_retryable',
    }, null, 2) + '\n');
    console.log('database_failure_is_visible_and_retryable: passed');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
