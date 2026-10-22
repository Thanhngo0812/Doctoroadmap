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

  // Full 12-configuration matrix for W-07 and W-14 (390, 768, 1280 x light, dark)
  // Plus core screens at 1280 & 390
  const viewports = {
    desktop: { width: 1280, height: 900 },
    tablet: { width: 768, height: 1024 },
    mobile: { width: 390, height: 844 }
  };

  const tasks = [];

  // W-07 Matrix (6 captures)
  for (const [vpName, vp] of Object.entries(viewports)) {
    for (const theme of ['light', 'dark']) {
      tasks.push({
        name: `w07_roadmap_${vp.width}_${theme}.png`,
        url: 'file:///' + path.join(root, 'design/preview/w07_roadmap_screens.html').replace(/\\/g, '/'),
        viewport: vp,
        theme,
        fullPage: true,
        setup: async (page) => {
          if (theme === 'dark') {
            await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'));
          }
        }
      });
    }
  }

  // W-14 Matrix (6 captures)
  for (const [vpName, vp] of Object.entries(viewports)) {
    for (const theme of ['light', 'dark']) {
      tasks.push({
        name: `w14_upload_${vp.width}_${theme}.png`,
        url: 'file:///' + path.join(root, 'design/preview/w14_upload_screens.html').replace(/\\/g, '/'),
        viewport: vp,
        theme,
        fullPage: true,
        setup: async (page) => {
          if (theme === 'dark') {
            await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'));
          }
        }
      });
    }
  }

  // Key Baseline Pages (Desktop 1280, Mobile 390)
  tasks.push(
    // Auth screens
    {
      name: 'auth_screens_1280_light.png',
      url: 'file:///' + path.join(root, 'design/preview/w03_auth_screens.html').replace(/\\/g, '/'),
      viewport: viewports.desktop,
      theme: 'light',
      fullPage: true
    },
    {
      name: 'auth_screens_390_mobile.png',
      url: 'file:///' + path.join(root, 'design/preview/w03_auth_screens.html').replace(/\\/g, '/'),
      viewport: viewports.mobile,
      theme: 'light',
      fullPage: true
    },
    // Courses list W-06
    {
      name: 'course_screens_1280_light.png',
      url: 'file:///' + path.join(root, 'design/preview/w06_course_screens.html').replace(/\\/g, '/'),
      viewport: viewports.desktop,
      theme: 'light',
      fullPage: true
    },
    {
      name: 'course_screens_390_mobile.png',
      url: 'file:///' + path.join(root, 'design/preview/w06_course_screens.html').replace(/\\/g, '/'),
      viewport: viewports.mobile,
      theme: 'light',
      fullPage: true
    },
    // Profile screens W-04
    {
      name: 'profile_screens_1280_light.png',
      url: 'file:///' + path.join(root, 'design/preview/w04_profile_screens.html').replace(/\\/g, '/'),
      viewport: viewports.desktop,
      theme: 'light',
      fullPage: true
    },
    {
      name: 'profile_screens_390_mobile.png',
      url: 'file:///' + path.join(root, 'design/preview/w04_profile_screens.html').replace(/\\/g, '/'),
      viewport: viewports.mobile,
      theme: 'light',
      fullPage: true
    },
    // Prototype flows workbench
    {
      name: 'prototype_flows_workbench.png',
      url: 'file:///' + path.join(root, 'design/preview/prototype_flows.html').replace(/\\/g, '/'),
      viewport: viewports.desktop,
      theme: 'light',
      fullPage: false
    }
  );

  console.log(`Starting capture of ${tasks.length} targeted screenshots across spec viewports & themes...`);

  for (const t of tasks) {
    const context = await browser.newContext({
      viewport: t.viewport,
      colorScheme: t.theme,
      permissions: ['clipboard-read', 'clipboard-write']
    });
    const page = await context.newPage();
    await page.goto(t.url, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    if (t.setup) {
      await t.setup(page);
    }
    await page.waitForTimeout(100);

    const persistentPath = path.join(persistentEvidenceDir, t.name);
    const artifactPath = path.join(artifactsDir, t.name);

    await page.screenshot({ path: persistentPath, fullPage: t.fullPage });
    await fs.copyFile(persistentPath, artifactPath);
    console.log(`  ✓ Captured: ${t.name} (${t.viewport.width}px, ${t.theme})`);
    await context.close();
  }

  await browser.close();
  console.log(`\nAll ${tasks.length} screenshots saved to report/w24-evidence/ and artifacts/ successfully.`);
}

capture().catch(err => {
  console.error('Fatal capture error:', err);
  process.exit(1);
});
