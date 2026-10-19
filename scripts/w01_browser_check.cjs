// W-01 browser acceptance. Install the temporary tools as documented in src/web/README.md.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(root, '.tmp/w01-browsers');
const { chromium } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/playwright'));
const { AxeBuilder } = require(path.join(root, '.tmp/w01-browser-tools/node_modules/@axe-core/playwright'));
const output = path.join(root, 'report/w01-evidence');

function contrastRatio({ foreground, background }) {
  const luminance = color => {
    const channels = color.match(/[\d.]+/g).slice(0, 3).map(Number).map(value => {
      const channel = value / 255;
      return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4;
    });
    return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
  };
  const first = luminance(foreground);
  const second = luminance(background);
  return (Math.max(first, second) + .05) / (Math.min(first, second) + .05);
}

function assertReadableButton(colors) {
  assert.ok(contrastRatio(colors) >= 4.5, 'Primary button text needs WCAG AA contrast');
}

async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch();
  const audit = { screens: [], consoleErrors: [], toolDiagnostics: [], accessibility: [], assertions: [] };
  const failed = [];
  try {
    for (const width of [390, 768, 1280]) {
      for (const theme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: theme });
        const page = await context.newPage();
        let runningAxe = false;
        page.on('pageerror', error => audit.consoleErrors.push(error.message));
        page.on('console', message => {
          if (message.type() === 'error') {
            (runningAxe ? audit.toolDiagnostics : audit.consoleErrors).push(message.text());
          }
        });
        await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
        await page.locator('.health-copy').filter({ hasText: 'Cơ sở dữ liệu: tốt' }).waitFor();
        await page.evaluate(() => document.fonts.ready);
        assert.equal(await page.evaluate(() => document.fonts.check('16px "Be Vietnam Pro"')
          && [...document.fonts].some(font => font.family === 'Be Vietnam Pro' && font.status === 'loaded')), true);
        assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
        if (overflow) failed.push(`Horizontal overflow at ${width}/${theme}`);
        const screenshot = `home-${width}-${theme}.png`;
        await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
        audit.screens.push({ width, theme, renderedTheme: theme, overflow, screenshot });
        // Axe fetches cross-origin stylesheets and injects a style element.
        // Record its CSP diagnostics separately from the application's console.
        runningAxe = true;
        const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
        runningAxe = false;
        audit.accessibility.push({ width, theme, violations: accessibility.violations });
        if (accessibility.violations.length) failed.push(`Accessibility violations at ${width}/${theme}`);
        if (width === 1280) {
          const button = page.locator('.button-primary').first();
          const colors = () => button.evaluate(element => ({
            foreground: getComputedStyle(element).color, background: getComputedStyle(element).backgroundColor,
          }));
          const original = await colors();
          assertReadableButton(original);
          audit.assertions.push('primary_button_contrast_' + theme);
          if (theme === 'light') {
            // Mutate only this disposable page, after its screenshot/axe check.
            await button.evaluate(element => { element.style.transition = 'none'; });
            await page.evaluate(() => document.documentElement.style.setProperty('--color-primary',
              getComputedStyle(document.documentElement).getPropertyValue('--color-brand')));
            const mutant = await colors();
            assert.throws(() => assertReadableButton(mutant), assert.AssertionError);
            audit.buttonContrast = { original: contrastRatio(original), mutant: contrastRatio(mutant) };
            audit.assertions.push('primary_contrast_guard_rejects_brand_blue_for_white_text');
          }
        }
        await context.close();
      }
    }

    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light',
      recordVideo: { dir: path.join(output, 'video'), size: { width: 1280, height: 900 } } });
    const page = await context.newPage();
    page.on('pageerror', error => audit.consoleErrors.push(error.message));
    page.on('console', message => {
      if (message.type() === 'error') audit.consoleErrors.push(message.text());
    });
    await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: /Khám phá lộ trình mẫu/ }).click();
    await page.getByRole('heading', { name: /Thử một hành trình học/ }).waitFor();
    const start = page.getByRole('button', { name: /Dựng lộ trình mẫu/ });
    assert.equal(await start.isDisabled(), true);
    await page.getByRole('checkbox').check();
    await start.click();
    await page.getByRole('button', { name: /Xem lộ trình mẫu/ }).click();
    await page.getByRole('button', { name: /Mở bài đầu tiên/ }).click();
    await page.getByRole('heading', { name: /Biến cố và xác suất/ }).waitFor();
    await page.getByRole('textbox', { name: /Câu hỏi cho trợ lý mẫu/ }).fill('Vì sao xác suất bằng một nửa?');
    await page.getByRole('button', { name: 'Gửi câu hỏi', exact: true }).click();
    await page.getByText(/Câu hỏi của bạn:/).waitFor();
    await page.getByRole('button', { name: /Đánh dấu đã học/ }).click();
    await page.getByRole('button', { name: 'B 1/2', exact: false }).click();
    await page.getByText('Chính xác.', { exact: true }).waitFor();
    await page.getByRole('button', { name: /Xem tiến độ mẫu/ }).click();
    await page.getByText('1 bài đã học', { exact: true }).waitFor();
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.screenshot({ path: path.join(output, 'demo-progress.png'), fullPage: true });
    audit.assertions.push('interactive_sample_upload_to_progress');
    await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
    for (let index = 0; index < 20; index++) {
      await page.keyboard.press('Tab');
      if (await page.getByRole('button', { name: /Bật chế độ tối/ }).evaluate(element => element === document.activeElement)) break;
    }
    const keyboardFocus = await page.getByRole('button', { name: /Bật chế độ tối/ }).evaluate(element => ({
      focused: element === document.activeElement, outline: getComputedStyle(element).outlineStyle,
    }));
    assert.equal(keyboardFocus.focused, true);
    assert.equal(keyboardFocus.outline, 'solid');
    await page.keyboard.press('Enter');
    await page.locator('html[data-theme="dark"]').waitFor();
    audit.assertions.push('theme_is_keyboard_reachable_with_visible_focus');
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
    await page.reload();
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
    audit.assertions.push('theme_persists_after_reload');
    await page.goto('http://127.0.0.1:8000/does-not-exist');
    await page.getByRole('heading', { name: 'Không tìm thấy trang.' }).waitFor();
    audit.assertions.push('spa_deep_link_and_not_found');
    const demoVideo = page.video();
    await context.close();
    audit.video = path.relative(output, await demoVideo.path()).replaceAll('\\', '/');

    const mobile = await browser.newContext({ viewport: { width: 390, height: 900 }, colorScheme: 'dark' });
    const mobilePage = await mobile.newPage();
    let checkingMobileAxe = false;
    mobilePage.on('pageerror', error => audit.consoleErrors.push(error.message));
    mobilePage.on('console', message => {
      if (message.type() === 'error') (checkingMobileAxe ? audit.toolDiagnostics : audit.consoleErrors).push(message.text());
    });
    await mobilePage.goto('http://127.0.0.1:8000/demo', { waitUntil: 'networkidle' });
    audit.demoStages = [];
    const mobileActions = [
      ['upload', async () => { await mobilePage.getByRole('checkbox').check(); await mobilePage.getByRole('button', { name: /Dựng lộ trình mẫu/ }).click(); }],
      ['processing', async () => mobilePage.getByRole('button', { name: /Xem lộ trình mẫu/ }).click()],
      ['roadmap', async () => mobilePage.getByRole('button', { name: /Mở bài đầu tiên/ }).click()],
      ['lecture', async () => { await mobilePage.getByRole('textbox', { name: /Câu hỏi cho trợ lý mẫu/ }).fill('Vì sao có hai khả năng?'); await mobilePage.getByRole('button', { name: 'Gửi câu hỏi', exact: true }).click(); await mobilePage.getByText(/Câu hỏi của bạn:/).waitFor(); await mobilePage.getByRole('button', { name: /Đánh dấu đã học/ }).click(); }],
      ['practice', async () => { await mobilePage.getByRole('button', { name: 'B 1/2', exact: false }).click(); await mobilePage.getByRole('button', { name: /Xem tiến độ mẫu/ }).click(); }],
      ['progress', async () => {}],
    ];
    for (const [stage, advance] of mobileActions) {
      const overflow = await mobilePage.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (overflow) failed.push('Mobile demo overflow: ' + stage);
      const smallTargets = await mobilePage.locator('button:not(:disabled), a').evaluateAll(elements => elements.filter(element => {
        const bounds = element.getBoundingClientRect();
        return bounds.width > 0 && bounds.height > 0 && (bounds.width < 44 || bounds.height < 44);
      }).map(element => ({ text: element.textContent.trim(), width: element.getBoundingClientRect().width, height: element.getBoundingClientRect().height })));
      if (smallTargets.length) failed.push('Mobile demo targets below 44px: ' + stage);
      checkingMobileAxe = true;
      const accessibility = await new AxeBuilder({ page: mobilePage }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      checkingMobileAxe = false;
      if (accessibility.violations.length) failed.push('Mobile demo accessibility: ' + stage);
      audit.demoStages.push({ stage, width: 390, theme: 'dark', overflow, smallTargets, violations: accessibility.violations });
      await mobilePage.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await mobilePage.screenshot({ path: path.join(output, 'demo-390-dark-' + stage + '.png'), fullPage: true });
      await advance();
    }
    audit.assertions.push('mobile_dark_sample_all_six_stages');
    await mobile.close();

    const reduced = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
    const reducedPage = await reduced.newPage();
    await reducedPage.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
    const motion = () => reducedPage.locator('.button-primary').first().evaluate(element => ({
      duration: getComputedStyle(element).transitionDuration,
      scroll: getComputedStyle(document.documentElement).scrollBehavior,
    }));
    const state = await motion();
    assert.equal(state.duration, '0s');
    assert.equal(state.scroll, 'auto');
    audit.assertions.push('reduced_motion_disables_transitions_and_smooth_scroll');
    // Deliberately remove the CSS protection in this isolated test page.
    // The same observable assertion must now fail; no source file is changed.
    await reducedPage.evaluate(() => {
      for (const sheet of document.styleSheets) {
        let rules;
        try { rules = sheet.cssRules; } catch { continue; }
        for (let index = rules.length - 1; index >= 0; index--) {
          if (rules[index] instanceof CSSMediaRule && rules[index].conditionText.includes('prefers-reduced-motion')) {
            sheet.deleteRule(index);
          }
        }
      }
    });
    const unprotected = await motion();
    assert.throws(() => assert.equal(unprotected.duration, '0s'), assert.AssertionError);
    audit.assertions.push('reduced_motion_guard_detects_removed_css_protection');
    audit.motion = { protected: state, unprotected };
    await reduced.close();
    if (audit.consoleErrors.length) failed.push('Browser console errors');
    assert.deepEqual(failed, [], failed.join('\n'));
    console.log(JSON.stringify({ screens: audit.screens.length, assertions: audit.assertions, consoleErrors: 0 }));
  } finally {
    await fs.writeFile(path.join(output, 'browser-audit.json'), JSON.stringify(audit, null, 2) + '\n');
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
