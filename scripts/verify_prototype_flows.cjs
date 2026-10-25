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

async function runPrototypes() {
  const artifactsDir = path.join(root, 'artifacts');
  const persistentEvidenceDir = path.join(root, 'report/w24-evidence');
  await fs.mkdir(artifactsDir, { recursive: true });
  await fs.mkdir(persistentEvidenceDir, { recursive: true });

  const browser = await chromium.launch();
  const results = [];
  let allPassed = true;

  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 900 },
      permissions: ['clipboard-read', 'clipboard-write']
    });
    const page = await context.newPage();
    const targetUrl = 'file:///' + path.join(root, 'design/preview/prototype_flows.html').replace(/\\/g, '/');
    await page.goto(targetUrl);
    await page.evaluate(() => document.fonts.ready);

    // ==========================================
    // FLOW 1: Đăng ký -> Khoá học mẫu -> Bài giảng lecture-2
    // ==========================================
    console.log('Testing Flow 1: Onboarding (Register -> Courses -> Lecture)...');
    try {
      // Step 1: Ensure Register screen is visible
      const isRegVisible = await page.isVisible('#flow1-screen-register');
      if (!isRegVisible) throw new Error('Flow 1 - Step 1: Register form is not visible initially');

      // Click register button
      await page.click('#flow1-btn-register');

      // Step 2: Assert Register form is now HIDDEN and Course list is VISIBLE
      const isRegHidden = !(await page.isVisible('#flow1-screen-register'));
      const isCoursesVisible = await page.isVisible('#flow1-screen-courses');
      if (!isRegHidden || !isCoursesVisible) {
        throw new Error(`Flow 1 - Step 2: Transition failed (regHidden: ${isRegHidden}, coursesVisible: ${isCoursesVisible})`);
      }

      // Click to open sample course
      await page.click('#flow1-btn-open-course');

      // Step 3: Assert Course list is HIDDEN and Lecture is VISIBLE
      const isCoursesHidden = !(await page.isVisible('#flow1-screen-courses'));
      const isLectureVisible = await page.isVisible('#flow1-screen-lecture');
      const lectureTitle = await page.textContent('#flow1-lecture-title');
      if (!isCoursesHidden || !isLectureVisible || !lectureTitle.includes('lecture-2')) {
        throw new Error('Flow 1 - Step 3: Transition to lecture-2 failed');
      }

      // Step 4: Strict Accordion Falsifiable Two-Way Assertion
      const accordionBodyBefore = await page.isVisible('#flow1-accordion-body');
      if (accordionBodyBefore) throw new Error('Flow 1 - Step 4: Accordion should be closed initially');

      // 4a. Click to open
      await page.click('#flow1-accordion-toggle');
      await page.waitForTimeout(100);
      const accordionBodyOpen = await page.isVisible('#flow1-accordion-body');
      if (!accordionBodyOpen) {
        throw new Error('Flow 1 - Step 4: Accordion failed to open on first click');
      }

      // 4b. Click to close (Two-way assertion)
      await page.click('#flow1-accordion-toggle');
      await page.waitForTimeout(100);
      const accordionBodyClosed = await page.isVisible('#flow1-accordion-body');
      if (accordionBodyClosed) {
        throw new Error('Flow 1 - Step 4: Accordion failed to close on second click');
      }

      // Re-open for visual screenshot
      await page.click('#flow1-accordion-toggle');
      await page.waitForTimeout(100);

      const shotPath = path.join(persistentEvidenceDir, 'prototype_flow1_auth.png');
      await page.screenshot({ path: shotPath, fullPage: false });
      await fs.copyFile(shotPath, path.join(artifactsDir, 'prototype_flow1_auth.png'));

      results.push({
        flow: 'Flow 1: Register -> Courses -> Lecture',
        stepsChecked: 5,
        passed: true,
        evidence: 'report/w24-evidence/prototype_flow1_auth.png',
        notes: 'Strict two-way open/close accordion toggle verified.'
      });
      console.log('  -> Flow 1 PASSED (All transitions and two-way accordion verified)');
    } catch (err) {
      console.error('  -> Flow 1 FAILED:', err.message);
      results.push({ flow: 'Flow 1: Register -> Courses -> Lecture', passed: false, error: err.message });
      allPassed = false;
    }

    // ==========================================
    // FLOW 2: Chia sẻ -> Tham gia khoá học
    // ==========================================
    console.log('Testing Flow 2: Share & Join Course (with Clipboard content proof)...');
    try {
      // Switch to Flow 2 tab
      await page.click('#tab-flow2');
      await page.waitForTimeout(100);

      // Verify share screen active
      const isShareVisible = await page.isVisible('#flow2-screen-share');
      if (!isShareVisible) throw new Error('Flow 2 - Step 1: Share screen not visible');

      // Click copy button and assert feedback appears + clipboard content verified
      await page.click('#flow2-btn-copy');
      const isFeedbackVisible = await page.isVisible('#flow2-copy-feedback');
      if (!isFeedbackVisible) throw new Error('Flow 2 - Step 2: Copy feedback not displayed');

      // Assert actual clipboard content read from browser strictly contains WF-PHARM-2026
      const copiedText = await page.evaluate(async () => {
        return await navigator.clipboard.readText();
      });
      if (!copiedText || !copiedText.includes('WF-PHARM-2026')) {
        throw new Error(`Flow 2 - Step 2: Actual clipboard read failed! (got: "${copiedText}")`);
      }

      // Click simulate join
      await page.click('#flow2-btn-simulate-join');

      // Assert join screen visible and share screen hidden
      const isShareHidden = !(await page.isVisible('#flow2-screen-share'));
      const isJoinVisible = await page.isVisible('#flow2-screen-join');
      if (!isShareHidden || !isJoinVisible) {
        throw new Error('Flow 2 - Step 3: Transition to join screen failed');
      }

      // Click confirm join
      await page.click('#flow2-btn-confirm-join');
      const isJoinSuccess = await page.isVisible('#flow2-join-success');
      const isBtnDisabled = await page.getAttribute('#flow2-btn-confirm-join', 'disabled');
      if (!isJoinSuccess || isBtnDisabled === null) {
        throw new Error('Flow 2 - Step 4: Confirm join state assertion failed');
      }

      const shotPath = path.join(persistentEvidenceDir, 'prototype_flow2_learning.png');
      await page.screenshot({ path: shotPath, fullPage: false });
      await fs.copyFile(shotPath, path.join(artifactsDir, 'prototype_flow2_learning.png'));

      results.push({
        flow: 'Flow 2: Share -> Join Course',
        stepsChecked: 4,
        passed: true,
        evidence: 'report/w24-evidence/prototype_flow2_learning.png',
        notes: `Clipboard content strictly verified: "${copiedText}"`
      });
      console.log('  -> Flow 2 PASSED (Share & Join confirmed with strict clipboard verification)');
    } catch (err) {
      console.error('  -> Flow 2 FAILED:', err.message);
      results.push({ flow: 'Flow 2: Share -> Join Course', passed: false, error: err.message });
      allPassed = false;
    }

    // ==========================================
    // FLOW 3: Tải sách -> Cấu hình -> Dựng lộ trình 4 bước
    // ==========================================
    console.log('Testing Flow 3: Upload Book -> Config -> 4-Step Build (with OS & Manual Reduced Motion proof)...');
    try {
      // Switch to Flow 3 tab
      await page.click('#tab-flow3');
      await page.waitForTimeout(100);

      // Verify upload dropzone active
      const isUploadVisible = await page.isVisible('#flow3-screen-upload');
      if (!isUploadVisible) throw new Error('Flow 3 - Step 1: Upload screen not visible');

      // Click select file
      await page.click('#flow3-btn-select-file');

      // Assert confirm screen visible
      const isUploadHidden = !(await page.isVisible('#flow3-screen-upload'));
      const isConfirmVisible = await page.isVisible('#flow3-screen-confirm');
      if (!isUploadHidden || !isConfirmVisible) {
        throw new Error('Flow 3 - Step 2: Transition to confirm screen failed');
      }

      // Click start build
      await page.click('#flow3-btn-start-build');

      // Assert progress screen active
      const isProgressVisible = await page.isVisible('#flow3-screen-progress');
      if (!isProgressVisible) throw new Error('Flow 3 - Step 3: Progress screen not visible');

      // Wait for progression completion
      await page.waitForSelector('#flow3-build-complete-banner', { state: 'visible', timeout: 3000 });
      const isBannerVisible = await page.isVisible('#flow3-build-complete-banner');
      const isFinishBtnVisible = await page.isVisible('#flow3-btn-finish-progress');
      if (!isBannerVisible || !isFinishBtnVisible) {
        throw new Error('Flow 3 - Step 4: 4-Step build progress completion assertion failed');
      }

      // Verify animated GIF is successfully loaded and decoded with naturalWidth > 0
      const initialImgStatus = await page.$eval('#flow3-spinner-img', async (img) => {
        if ('decode' in img) {
          try { await img.decode(); } catch (e) {}
        }
        return {
          complete: img.complete,
          naturalWidth: img.naturalWidth,
          naturalHeight: img.naturalHeight,
          src: img.currentSrc || img.src
        };
      });
      if (!initialImgStatus.complete || initialImgStatus.naturalWidth <= 0) {
        throw new Error(`Flow 3 - Step 5: Spinner animated GIF failed to load or has 0 dimensions! complete=${initialImgStatus.complete}, naturalWidth=${initialImgStatus.naturalWidth}`);
      }

      // --- 5A: Manual toggle reduced-motion test ---
      await page.click('#btn-toggle-reduced-motion');
      const spinnerSrc = await page.getAttribute('#flow3-spinner-img', 'src');
      if (!spinnerSrc.includes('Untitled_Artwork_static.png')) {
        throw new Error(`Flow 3 - Step 5a: Manual reduced motion static fallback not engaged (got: ${spinnerSrc})`);
      }

      // Verify static replacement image is loaded, rendered, and decoded
      const staticImgStatus = await page.$eval('#flow3-spinner-img', async (img) => {
        if ('decode' in img) {
          try { await img.decode(); } catch (e) {}
        }
        const rect = img.getBoundingClientRect();
        return {
          complete: img.complete,
          naturalWidth: img.naturalWidth,
          naturalHeight: img.naturalHeight,
          renderedWidth: rect.width,
          renderedHeight: rect.height
        };
      });
      if (!staticImgStatus.complete || staticImgStatus.naturalWidth <= 0 || staticImgStatus.renderedWidth <= 0) {
        throw new Error(`Flow 3 - Step 5a: Static replacement image failed to render! (renderedWidth: ${staticImgStatus.renderedWidth})`);
      }

      // Capture spinner buffer at t=0
      const spinnerElem = await page.$('#flow3-spinner-img');
      const bufferT0 = await spinnerElem.screenshot();

      // Wait 350ms
      await page.waitForTimeout(350);

      // Capture spinner buffer at t=350ms
      const bufferT350 = await spinnerElem.screenshot();

      // Assert byte equality (frame is frozen and unchanged over time)
      const isFrozen = bufferT0.equals(bufferT350);
      if (!isFrozen) {
        throw new Error('Flow 3 - Step 5a: Spinner frame changed over time while manual reduced-motion is active! Must remain frozen.');
      }

      // --- 5B: OS-level prefers-reduced-motion: reduce test via separate context ---
      const osContext = await browser.newContext({
        viewport: { width: 1280, height: 900 },
        reducedMotion: 'reduce'
      });
      const failedRequests = [];
      const osPage = await osContext.newPage();
      osPage.on('requestfailed', req => failedRequests.push(req.url()));
      osPage.on('response', resp => {
        if (resp.status() >= 400) failedRequests.push(resp.url());
      });

      await osPage.goto(targetUrl);
      await osPage.evaluate(() => document.fonts.ready);
      await osPage.click('#tab-flow3');
      await osPage.waitForTimeout(100);

      // Advance to Step 3 in osPage so progress screen and spinner are visible
      await osPage.click('#flow3-btn-select-file');
      await osPage.click('#flow3-btn-start-build');
      await osPage.waitForSelector('#flow3-screen-progress.active');

      // Verify no broken asset requests occurred under OS reduced-motion
      if (failedRequests.length > 0) {
        throw new Error(`Flow 3 - Step 5b: OS reduced-motion triggered failed asset requests: ${failedRequests.join(', ')}`);
      }

      // Verify rendered dimension and frozen frame under OS reduced-motion media query
      const osSpinner = await osPage.$('#flow3-spinner-img');
      const osRect = await osPage.$eval('#flow3-spinner-img', el => {
        const r = el.getBoundingClientRect();
        return { width: r.width, height: r.height };
      });
      if (osRect.width <= 0 || osRect.height <= 0) {
        throw new Error(`Flow 3 - Step 5b: Spinner image is not rendered under OS reduced-motion (width: ${osRect.width})`);
      }

      const osBufferT0 = await osSpinner.screenshot();
      await osPage.waitForTimeout(350);
      const osBufferT350 = await osSpinner.screenshot();
      if (!osBufferT0.equals(osBufferT350)) {
        throw new Error('Flow 3 - Step 5b: OS reduced-motion CSS rule failed to freeze animation over time!');
      }
      await osContext.close();

      const shotPath = path.join(persistentEvidenceDir, 'prototype_flow3_upload.png');
      await page.screenshot({ path: shotPath, fullPage: false });
      await fs.copyFile(shotPath, path.join(artifactsDir, 'prototype_flow3_upload.png'));

      results.push({
        flow: 'Flow 3: Upload -> Config -> 4-Step Build',
        stepsChecked: 6,
        passed: true,
        evidence: 'report/w24-evidence/prototype_flow3_upload.png',
        notes: 'Both OS prefers-reduced-motion and manual toggle verified: zero failed requests, rendered width > 0, buffer frozen over time.'
      });
      console.log('  -> Flow 3 PASSED (OS & Manual reduced-motion + zero asset failures strictly proven)');
    } catch (err) {
      console.error('  -> Flow 3 FAILED:', err.message);
      results.push({ flow: 'Flow 3: Upload -> Config -> 4-Step Build', passed: false, error: err.message });
      allPassed = false;
    }

    // ==========================================
    // FLOW 4: Quiz -> Nộp bài -> Phản hồi kết quả & Trích dẫn
    // ==========================================
    console.log('Testing Flow 4: Quiz -> Submit -> Result & Citation (with Content & Scroll proof)...');
    try {
      // Switch to Flow 4 tab
      await page.click('#tab-flow4');
      await page.waitForTimeout(100);

      // Verify submit button disabled initially
      const submitDisabledBefore = await page.getAttribute('#flow4-btn-submit', 'disabled');
      if (submitDisabledBefore === null) {
        throw new Error('Flow 4 - Step 1: Submit button must be disabled before option selection');
      }

      // Click Option B
      await page.click('.quiz-opt[data-opt="B"]');

      // Assert Option B is selected and aria-checked=true
      const optBClass = await page.getAttribute('.quiz-opt[data-opt="B"]', 'class');
      const optBChecked = await page.getAttribute('.quiz-opt[data-opt="B"]', 'aria-checked');
      if (!optBClass.includes('selected') || optBChecked !== 'true') {
        throw new Error('Flow 4 - Step 2: Option B selection state assertion failed');
      }

      // Assert submit button is now enabled
      const submitDisabledAfter = await page.getAttribute('#flow4-btn-submit', 'disabled');
      if (submitDisabledAfter !== null) {
        throw new Error('Flow 4 - Step 3: Submit button should be enabled after selection');
      }

      // Submit Quiz
      await page.click('#flow4-btn-submit');
      await page.waitForTimeout(100);

      // Assert result panel is visible with score 10/10
      const isResultVisible = await page.isVisible('#flow4-result-panel');
      const resultText = await page.textContent('#flow4-result-status');
      if (!isResultVisible || !resultText.includes('10/10')) {
        throw new Error('Flow 4 - Step 4: Result panel display assertion failed');
      }

      // Assert Citation Box starts offscreen (below initial viewport fold)
      const viewportHeight = 900;
      const rectBefore = await page.$eval('#flow4-citation-box', el => {
        const r = el.getBoundingClientRect();
        return { top: r.top, bottom: r.bottom };
      });
      if (rectBefore.top < viewportHeight) {
        throw new Error(`Flow 4 - Step 5: Citation box must start offscreen below fold before scrolling! (top: ${rectBefore.top}, viewportHeight: ${viewportHeight})`);
      }

      // Click View Citation button and wait for scroll animation
      await page.click('#flow4-btn-view-citation');
      await page.waitForTimeout(400);

      // Assert Citation Box is now scrolled into viewport (intersecting bounding box)
      const rectAfter = await page.$eval('#flow4-citation-box', el => {
        const r = el.getBoundingClientRect();
        return { top: r.top, bottom: r.bottom };
      });
      const isInViewport = rectAfter.top < viewportHeight && rectAfter.bottom > 0;
      if (!isInViewport) {
        throw new Error(`Flow 4 - Step 6: Citation box failed to scroll into viewport! (top: ${rectAfter.top}, bottom: ${rectAfter.bottom}, viewportHeight: ${viewportHeight})`);
      }

      // Assert Citation Content strictly matches Harrison's Internal Medicine 21st, Trang 1892
      const citationText = await page.textContent('#flow4-citation-box');
      if (!citationText.includes("Harrison's Internal Medicine, 21st Edition") || !citationText.includes("Trang 1892")) {
        throw new Error(`Flow 4 - Step 7: Citation content mismatch! (got: "${citationText}")`);
      }

      const shotPath = path.join(persistentEvidenceDir, 'prototype_flow4_quiz.png');
      await page.screenshot({ path: shotPath, fullPage: false });
      await fs.copyFile(shotPath, path.join(artifactsDir, 'prototype_flow4_quiz.png'));

      results.push({
        flow: 'Flow 4: Quiz -> Submit -> Result & Citation',
        stepsChecked: 6,
        passed: true,
        evidence: 'report/w24-evidence/prototype_flow4_quiz.png',
        notes: 'Citation content proven: Harrison 21st Ed, Trang 1892, with verified view interaction.'
      });
      console.log('  -> Flow 4 PASSED (Quiz evaluation & citation content/scroll strictly proven)');
    } catch (err) {
      console.error('  -> Flow 4 FAILED:', err.message);
      results.push({ flow: 'Flow 4: Quiz -> Submit -> Result & Citation', passed: false, error: err.message });
      allPassed = false;
    }

    await context.close();
  } finally {
    await browser.close();
  }

  const auditData = {
    timestamp: new Date().toISOString(),
    totalFlows: results.length,
    passedCount: results.filter(r => r.passed).length,
    allPassed,
    flows: results
  };

  await fs.writeFile(path.join(persistentEvidenceDir, 'prototype_flows_audit.json'), JSON.stringify(auditData, null, 2), 'utf-8');
  await fs.writeFile(path.join(artifactsDir, 'prototype_flows_audit.json'), JSON.stringify(auditData, null, 2), 'utf-8');

  console.log(`\nPrototype Verification Summary: ${results.filter(r => r.passed).length}/${results.length} flows passed.`);
  if (!allPassed) {
    console.error('❌ Prototype Verification Failed with strict assertions.');
    process.exit(1);
  } else {
    console.log('✅ All 4 Prototype flows passed with strict, falsifiable DOM & visual assertions.');
  }
}

runPrototypes().catch(err => {
  console.error('Fatal test error:', err);
  process.exit(1);
});
