const fs = require('node:fs/promises');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));

async function capture() {
  const artifactsDir = path.join(root, 'artifacts');
  await fs.mkdir(artifactsDir, { recursive: true });

  const browser = await chromium.launch();

  const captures = [
    {
      url: 'file:///' + path.join(root, 'design/preview/components.html').replace(/\\/g, '/'),
      output: path.join(artifactsDir, 'preview_components.png'),
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/screens.html').replace(/\\/g, '/'),
      output: path.join(artifactsDir, 'preview_screens.png'),
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/screens_dark.html').replace(/\\/g, '/'),
      output: path.join(artifactsDir, 'preview_screens_dark.png'),
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'dark'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/screens.html').replace(/\\/g, '/'),
      output: path.join(artifactsDir, 'preview_screens_768.png'),
      viewport: { width: 768, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/mobile_screens.html').replace(/\\/g, '/'),
      output: path.join(artifactsDir, 'preview_mobile_screens.png'),
      viewport: { width: 900, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/auth_screens.html').replace(/\\/g, '/'),
      output: path.join(artifactsDir, 'preview_auth_light.png'),
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/auth_screens.html').replace(/\\/g, '/') + '?theme=dark',
      output: path.join(artifactsDir, 'preview_auth_dark.png'),
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'dark'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/auth_screens.html').replace(/\\/g, '/'),
      output: path.join(artifactsDir, 'preview_auth_mobile.png'),
      viewport: { width: 500, height: 900 },
      fullPage: true,
      theme: 'light'
    }
  ];

  for (const item of captures) {
    const context = await browser.newContext({
      viewport: item.viewport,
      colorScheme: item.theme
    });
    const page = await context.newPage();
    await page.goto(item.url, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: item.output, fullPage: item.fullPage });
    console.log(`Saved screenshot: ${path.basename(item.output)}`);
    await context.close();
  }

  await browser.close();
  console.log('All screenshots captured successfully.');
}

capture().catch(err => {
  console.error(err);
  process.exit(1);
});
