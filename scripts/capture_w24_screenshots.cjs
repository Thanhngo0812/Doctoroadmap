const fs = require('node:fs/promises');
const path = require('node:path');
const fsSync = require('node:fs');

const root = path.resolve(__dirname, '..');
let browserToolsDir = path.join(root, '.tmp/w01-browser-tools');
let browsersPath = path.join(root, '.tmp/w01-browsers');
if (!fsSync.existsSync(browserToolsDir)) {
  const mainRepo = path.resolve(root, '..', '..');
  if (fsSync.existsSync(path.join(mainRepo, '.tmp/w01-browser-tools'))) {
    browserToolsDir = path.join(mainRepo, '.tmp/w01-browser-tools');
    browsersPath = path.join(mainRepo, '.tmp/w01-browsers');
  }
}
process.env.PLAYWRIGHT_BROWSERS_PATH = browsersPath;
const { chromium } = require(path.join(browserToolsDir, 'node_modules/playwright'));

async function capture() {
  const artifactsDir = path.join(root, 'artifacts');
  const persistentEvidenceDir = path.join(root, 'report/w24-evidence');
  await fs.mkdir(artifactsDir, { recursive: true });
  await fs.mkdir(persistentEvidenceDir, { recursive: true });

  const browser = await chromium.launch();

  const captures = [
    {
      url: 'file:///' + path.join(root, 'design/preview/components.html').replace(/\\/g, '/'),
      filename: 'preview_components.png',
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/screens.html').replace(/\\/g, '/'),
      filename: 'preview_screens.png',
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/screens_dark.html').replace(/\\/g, '/'),
      filename: 'preview_screens_dark.png',
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'dark'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/screens.html').replace(/\\/g, '/'),
      filename: 'preview_screens_768.png',
      viewport: { width: 768, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/mobile_screens.html').replace(/\\/g, '/'),
      filename: 'preview_mobile_screens.png',
      viewport: { width: 900, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/auth_screens.html').replace(/\\/g, '/'),
      filename: 'preview_auth_light.png',
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/auth_screens.html').replace(/\\/g, '/') + '?theme=dark',
      filename: 'preview_auth_dark.png',
      viewport: { width: 1400, height: 900 },
      fullPage: true,
      theme: 'dark'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/auth_screens.html').replace(/\\/g, '/'),
      filename: 'preview_auth_mobile.png',
      viewport: { width: 500, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w03_auth_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w03_screens.png',
      viewport: { width: 1280, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w03_auth_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w03_mobile.png',
      viewport: { width: 390, height: 844 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/prototype_flows.html').replace(/\\/g, '/'),
      filename: 'preview_prototype_flows_workbench.png',
      viewport: { width: 1280, height: 1000 },
      fullPage: false,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w06_course_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w06_courses.png',
      viewport: { width: 1280, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w06_course_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w06_mobile.png',
      viewport: { width: 390, height: 844 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w04_profile_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w04_profile.png',
      viewport: { width: 1280, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w04_profile_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w04_mobile.png',
      viewport: { width: 390, height: 844 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w07_roadmap_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w07_roadmap.png',
      viewport: { width: 1280, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w07_roadmap_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w07_mobile.png',
      viewport: { width: 390, height: 844 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w14_upload_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w14_upload.png',
      viewport: { width: 1280, height: 900 },
      fullPage: true,
      theme: 'light'
    },
    {
      url: 'file:///' + path.join(root, 'design/preview/w14_upload_screens.html').replace(/\\/g, '/'),
      filename: 'preview_w14_mobile.png',
      viewport: { width: 390, height: 844 },
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
    
    const persistentPath = path.join(persistentEvidenceDir, item.filename);
    const artifactPath = path.join(artifactsDir, item.filename);
    
    await page.screenshot({ path: persistentPath, fullPage: item.fullPage });
    await fs.copyFile(persistentPath, artifactPath);
    console.log(`Saved screenshot: ${item.filename} (both persistent & artifact)`);
    await context.close();
  }

  await browser.close();
  console.log('All 19 screenshots captured successfully into persistent and artifact dirs.');
}

capture().catch(err => {
  console.error(err);
  process.exit(1);
});
