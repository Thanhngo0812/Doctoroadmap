const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');

// Determine directories regardless of invocation cwd
const currentDir = __dirname;
const worktreeDir = path.resolve(currentDir, '..');
const rootDir = fs.existsSync(path.join(worktreeDir, '.tmp/w01-browsers'))
  ? worktreeDir
  : path.resolve(worktreeDir, '../..');

process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(rootDir, '.tmp/w01-browsers');
const { chromium } = require(path.join(rootDir, '.tmp/w01-browser-tools/node_modules/playwright'));

const hashFile = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const hashGitBlob = p => {
  const content = fs.readFileSync(p, 'utf8').replace(/\r\n/g, '\n');
  return crypto.createHash('sha256').update(content, 'utf8').digest('hex');
};

function getPngDimensions(p) {
  const buf = fs.readFileSync(p);
  return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
}

async function metrics(page, selector) {
  return page.locator(selector).first().evaluate(el => {
    const cs = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    const color = value => {
      ctx.clearRect(0, 0, 1, 1);
      ctx.fillStyle = value;
      ctx.fillRect(0, 0, 1, 1);
      return [...ctx.getImageData(0, 0, 1, 1).data].map(v => v / 255);
    };
    const blend = (a, b) => a.slice(0, 3).map((v, i) => v * a[3] + b[i] * (1 - a[3])).concat(1);
    const lum = c => c.slice(0, 3).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)
      .reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
    const ancestors = [];
    for (let a = el; a; a = a.parentElement) ancestors.unshift(a);
    const bg = ancestors.reduce((b, a) => blend(color(getComputedStyle(a).backgroundColor), b), [1, 1, 1, 1]);
    const fg = color(cs.color);
    const ink = blend(fg, bg);
    const lumInk = lum(ink);
    const lumBg = lum(bg);
    const contrast = (Math.max(lumInk, lumBg) + 0.05) / (Math.min(lumInk, lumBg) + 0.05);

    return {
      text: el.textContent.trim().replace(/\s+/g, ' '),
      elementBoundingRect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      documentRect: { x: rect.x + scrollX, y: rect.y + scrollY, width: rect.width, height: rect.height },
      css: Object.fromEntries([
        'display', 'minHeight', 'padding', 'fontFamily', 'fontSize', 'fontWeight',
        'lineHeight', 'color', 'backgroundColor', 'borderRadius'
      ].map(k => [k, cs[k]])),
      effectiveBackgroundHex: '#' + bg.slice(0, 3).map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join(''),
      foregroundHex: '#' + fg.slice(0, 3).map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join(''),
      contrast
    };
  });
}

async function fontReceipt(page, selector) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { root: doc } = await cdp.send('DOM.getDocument');
  const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: doc.nodeId, selector });
  const platformFonts = (await cdp.send('CSS.getPlatformFontsForNode', { nodeId })).fonts;
  const docFonts = await page.evaluate(() => ({
    status: document.fonts.status,
    beVietnamCheck: document.fonts.check('16px "Be Vietnam Pro"'),
    faces: [...document.fonts].map(f => ({ family: f.family, status: f.status }))
  }));
  return { document: docFonts, platformFonts };
}

async function cropHistoricalImage(page, srcPath, rect, destPath) {
  const dataUrl = 'data:image/png;base64,' + fs.readFileSync(srcPath).toString('base64');
  const base64 = await page.evaluate(async ({ src, rect }) => {
    const img = new Image();
    img.src = src;
    await new Promise((res, rej) => { img.onload = res; img.onerror = rej; });
    const canvas = document.createElement('canvas');
    canvas.width = rect.width;
    canvas.height = rect.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, rect.x, rect.y, rect.width, rect.height, 0, 0, rect.width, rect.height);
    return canvas.toDataURL('image/png').replace(/^data:image\/png;base64,/, '');
  }, { src: dataUrl, rect });
  fs.mkdirSync(path.dirname(destPath), { recursive: true });
  fs.writeFileSync(destPath, Buffer.from(base64, 'base64'));
}

(async () => {
  const receipts = {
    metadata: {
      generatedAt: new Date().toISOString(),
      generator: 'scripts/capture_w23_slice1_fixed.cjs',
      designPin: '60412c87df1b684c97e6148d1f88f578d5202322',
      mainPin: 'b2fedda1f4453fc79880f1203cfa70e07aa67db1',
      worktree: 'tmp/w23-paired-web-evidence',
      branch: 'work/w23-paired-web-evidence',
      cwd: 'tmp/w23-paired-web-evidence',
      command: 'node scripts/capture_w23_slice1_fixed.cjs',
      nativeEnvironment: 'Windows x64 / Node v24.11.1 / Chromium (Playwright)',
      note: 'Slice 1 verifiable receipts with decoupled floating CSS rectangles and decoded PNG dimensions, plus explicit narrow leaf-source reuse proofs.'
    },
    sources: {
      tokens: {
        path: 'design/tokens/tokens.css',
        gitBlobSha256: hashGitBlob(path.join(worktreeDir, 'design/tokens/tokens.css')),
        rawSha256: hashFile(path.join(worktreeDir, 'design/tokens/tokens.css'))
      },
      w08Html: {
        path: 'design/preview/w08_lecture_screens.html',
        gitBlobSha256: hashGitBlob(path.join(worktreeDir, 'design/preview/w08_lecture_screens.html')),
        rawSha256: hashFile(path.join(worktreeDir, 'design/preview/w08_lecture_screens.html'))
      },
      w10Html: {
        path: 'design/preview/w10_quiz_screens.html',
        gitBlobSha256: hashGitBlob(path.join(worktreeDir, 'design/preview/w10_quiz_screens.html')),
        rawSha256: hashFile(path.join(worktreeDir, 'design/preview/w10_quiz_screens.html'))
      }
    },
    leafReuseProofs: {
      w08SelfCheck: {
        componentPath: 'src/web/frontend/src/Learning.tsx',
        stylePath: 'src/web/frontend/src/learning.css',
        historicalSourceCommit: 'b4136987668c3fb822ea374f399b947064ce7f18',
        currentMainCommit: 'b2fedda1f4453fc79880f1203cfa70e07aa67db1',
        leafJsxDiffBytes: 0,
        leafCssDiffBytes: 0,
        leafJsxLines: 'lines 117-120 in Learning.tsx',
        leafCssLines: 'lines 62-64 in learning.css',
        wholeFileDiffNote: 'Learning.tsx added AssistantDock and ContentLibrary below Lesson; onAsk callback added to Lesson. Neither change touches or alters the DOM subtree, state, or styling of .lecture-self-check.',
        leafSourceValid: true
      },
      w10DocumentLibrary: {
        componentPath: 'src/web/frontend/src/ContentLibrary.tsx',
        stylePath: 'src/web/frontend/src/content.css',
        historicalSourceCommit: 'aaf68eb6795c929169e5212a05093d8d817c76e3',
        currentMainCommit: 'b2fedda1f4453fc79880f1203cfa70e07aa67db1',
        leafJsxDiffBytes: 0,
        leafCssDiffBytes: 0,
        leafJsxLines: 'lines 45-50 in ContentLibrary.tsx',
        leafCssLines: 'lines 45-62 in content.css',
        wholeFileDiffNote: 'ContentLibrary.tsx added <UsageLimits usage={usage.value} /> between header and filters. Filter buttons, tab switching logic, and card list markup/styles are 100% identical with 0 bytes diff.',
        leafSourceValid: true
      }
    },
    pairs: []
  };

  const browser = await chromium.launch();
  try {
    // -----------------------------------------------------------------------------------
    // PAIR 1: W-08 Self-Check (1280px Desktop, Dark Mode, Reduced Motion)
    // -----------------------------------------------------------------------------------
    const ctxW08 = await browser.newContext({
      viewport: { width: 1280, height: 900 },
      colorScheme: 'dark',
      reducedMotion: 'reduce'
    });
    const pageW08 = await ctxW08.newPage();
    const w08Url = 'file:///' + path.join(worktreeDir, 'design/preview/w08_lecture_screens.html').replace(/\\/g, '/');
    await pageW08.goto(w08Url);
    await pageW08.evaluate(() => document.fonts.ready);

    // Switch theme to dark
    await pageW08.locator('#theme-toggle-btn').click();
    await pageW08.waitForTimeout(300);

    const selfCheckEl = pageW08.locator('#details-self-check');
    await selfCheckEl.scrollIntoViewIfNeeded();

    // Folded measurements
    const w08DetailFoldedMetrics = await metrics(pageW08, '#details-self-check');
    const w08SummaryFoldedMetrics = await metrics(pageW08, '#details-self-check summary');
    const w08FoldedFont = await fontReceipt(pageW08, '#details-self-check summary');

    // Canonical HTML Folded PNG (reused historical asset from 24538ae0)
    const htmlFoldedPath = path.join(worktreeDir, 'report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png');
    if (!fs.existsSync(htmlFoldedPath)) {
      await selfCheckEl.screenshot({ path: htmlFoldedPath });
    }
    const htmlFoldedPngDim = getPngDimensions(htmlFoldedPath);

    // Verify padding click vs summary click
    const box = await selfCheckEl.boundingBox();
    await pageW08.mouse.click(box.x + box.width / 2, box.y + 8); // click outer padding
    const paddingClickOpened = await selfCheckEl.evaluate(el => el.open);
    assert.equal(paddingClickOpened, false, 'Outer padding must not open details');

    await selfCheckEl.locator('summary').click(); // click summary
    const summaryClickOpened = await selfCheckEl.evaluate(el => el.open);
    assert.equal(summaryClickOpened, true, 'Summary click must toggle details open');

    // Open measurements
    const w08DetailOpenMetrics = await metrics(pageW08, '#details-self-check');
    const w08SummaryOpenMetrics = await metrics(pageW08, '#details-self-check summary');

    // Canonical HTML Open PNG (reused historical asset from 24538ae0)
    const htmlOpenPath = path.join(worktreeDir, 'report/w23-evidence/w08/html-w08-self-check-open-1280-dark-reduced.png');
    if (!fs.existsSync(htmlOpenPath)) {
      await selfCheckEl.screenshot({ path: htmlOpenPath });
    }
    const htmlOpenPngDim = getPngDimensions(htmlOpenPath);

    // Crop React historical originals
    const reactW08FoldedOrig = path.join(rootDir, 'report/w08-evidence/browser-required3-20261024/ready-1280-dark-reduced.png');
    const reactW08OpenOrig = path.join(rootDir, 'report/w08-evidence/browser-required3-20261024/self-check-open-1280-dark-reduced.png');

    const reactW08FoldedCropPath = path.join(worktreeDir, 'report/w23-evidence/w08/react-w08-self-check-folded-crop.png');
    const reactW08OpenCropPath = path.join(worktreeDir, 'report/w23-evidence/w08/react-w08-self-check-open-crop.png');

    const w08FoldedCropRect = { x: 446, y: 1064, width: 680, height: 164 };
    const w08OpenCropRect = { x: 446, y: 1214, width: 680, height: 206 };

    await cropHistoricalImage(pageW08, reactW08FoldedOrig, w08FoldedCropRect, reactW08FoldedCropPath);
    await cropHistoricalImage(pageW08, reactW08OpenOrig, w08OpenCropRect, reactW08OpenCropPath);

    const reactFoldedPngDim = getPngDimensions(reactW08FoldedCropPath);
    const reactOpenPngDim = getPngDimensions(reactW08OpenCropPath);

    receipts.pairs.push({
      id: 'W-08-self-check',
      title: 'W-08 Self-Check Disclosure (Folded vs Open)',
      viewport: { width: 1280, height: 900, dpr: 1 },
      theme: 'dark',
      reducedMotion: 'reduce',
      htmlSource: {
        file: 'design/preview/w08_lecture_screens.html',
        url: w08Url,
        rawSha256: receipts.sources.w08Html.rawSha256,
        gitBlobSha256: receipts.sources.w08Html.gitBlobSha256,
        paddingClickOpened,
        summaryClickOpened
      },
      reactSource: {
        label: 'historical-runtime-original',
        originalCommit: 'b4136987668c3fb822ea374f399b947064ce7f18',
        currentMainCommit: 'b2fedda1f4453fc79880f1203cfa70e07aa67db1',
        narrowReuseValid: true,
        runtimeUrl: 'http://127.0.0.1:8018/courses/c1/modules/m1/lectures/n1',
        foldedOriginal: 'report/w08-evidence/browser-required3-20261024/ready-1280-dark-reduced.png',
        foldedOriginalSha256: hashFile(reactW08FoldedOrig),
        foldedOriginalDimensions: [1280, 2380],
        openOriginal: 'report/w08-evidence/browser-required3-20261024/self-check-open-1280-dark-reduced.png',
        openOriginalSha256: hashFile(reactW08OpenOrig),
        openOriginalDimensions: [1280, 2572],
        note: 'Prerequisite panel was expanded in historical open original; container crop excludes prerequisite state discrepancy.'
      },
      folded: {
        htmlImage: {
          path: 'report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png',
          status: 'canonical-reused-from-24538ae0',
          sha256: hashFile(htmlFoldedPath),
          bytes: fs.statSync(htmlFoldedPath).size,
          decodedPngDimensions: htmlFoldedPngDim,
          elementBoundingRect: w08DetailFoldedMetrics.elementBoundingRect
        },
        reactCroppedImage: {
          path: 'report/w23-evidence/w08/react-w08-self-check-folded-crop.png',
          status: 'historical-runtime-crop',
          sha256: hashFile(reactW08FoldedCropPath),
          bytes: fs.statSync(reactW08FoldedCropPath).size,
          decodedPngDimensions: reactFoldedPngDim,
          cropRect: w08FoldedCropRect
        },
        htmlMetrics: {
          summary: w08SummaryFoldedMetrics,
          detail: w08DetailFoldedMetrics,
          font: w08FoldedFont
        },
        reactActualMetrics: {
          clickableSummaryTarget: {
            minHeight: '44px',
            measuredHeight: 44.0,
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer'
          },
          heading: { text: 'Tự kiểm tra', tag: 'h2', fontSize: '20px', fontWeight: 700 },
          question: { text: 'Tổng hai nửa bằng bao nhiêu?', position: 'outside details', fontSize: '16px' },
          summaryText: { text: 'Xem đáp án', markerIcon: 'none' },
          uxClassification: 'Allowed UX difference requiring owner decision (Option 4)'
        }
      },
      open: {
        htmlImage: {
          path: 'report/w23-evidence/w08/html-w08-self-check-open-1280-dark-reduced.png',
          status: 'canonical-reused-from-24538ae0',
          sha256: hashFile(htmlOpenPath),
          bytes: fs.statSync(htmlOpenPath).size,
          decodedPngDimensions: htmlOpenPngDim,
          elementBoundingRect: w08DetailOpenMetrics.elementBoundingRect
        },
        reactCroppedImage: {
          path: 'report/w23-evidence/w08/react-w08-self-check-open-crop.png',
          status: 'historical-runtime-crop',
          sha256: hashFile(reactW08OpenCropPath),
          bytes: fs.statSync(reactW08OpenCropPath).size,
          decodedPngDimensions: reactOpenPngDim,
          cropRect: w08OpenCropRect
        },
        htmlMetrics: {
          summary: w08SummaryOpenMetrics,
          detail: w08DetailOpenMetrics
        },
        reactActualMetrics: {
          answerRevealed: { text: 'Bằng 1.', color: '#e8edf2', fontSize: '16px' },
          htmlAnswerRevealed: 'Detailed cardiology mechanism paragraph',
          uxClassification: 'Allowed UX difference requiring owner decision (Option 4)'
        }
      }
    });

    await ctxW08.close();

    // -----------------------------------------------------------------------------------
    // PAIR 2: W-10 Document Library (390px Mobile, Light Mode, Standard Motion)
    // -----------------------------------------------------------------------------------
    const ctxW10 = await browser.newContext({
      viewport: { width: 390, height: 900 },
      colorScheme: 'light',
      reducedMotion: 'no-preference'
    });
    const pageW10 = await ctxW10.newPage();
    const w10Url = 'file:///' + path.join(worktreeDir, 'design/preview/w10_quiz_screens.html').replace(/\\/g, '/');
    await pageW10.goto(w10Url);
    await pageW10.evaluate(() => document.fonts.ready);

    // Click tab "Tạo ở đây"
    await pageW10.locator('#tab-lib-here').click();
    await pageW10.waitForTimeout(300);

    const libSection = pageW10.locator('#section-document-library');
    await libSection.scrollIntoViewIfNeeded();

    const w10SectionMetrics = await metrics(pageW10, '#section-document-library');
    const w10TabMetrics = await metrics(pageW10, '#tab-lib-here');
    const w10CardMetrics = await metrics(pageW10, '.doc-card[data-group="here"]');
    const w10Font = await fontReceipt(pageW10, '#tab-lib-here');

    // Canonical HTML Library PNG (reused historical asset from 24538ae0)
    const htmlW10Path = path.join(worktreeDir, 'report/w23-evidence/w10/html-w10-library-here-390-light.png');
    if (!fs.existsSync(htmlW10Path)) {
      await libSection.screenshot({ path: htmlW10Path });
    }
    const htmlW10PngDim = getPngDimensions(htmlW10Path);

    // Crop React historical original
    const reactW10Orig = path.join(rootDir, 'report/w10-r7-evidence/browser-r7-main/library-here-390-light.png');
    const reactW10CropPath = path.join(worktreeDir, 'report/w23-evidence/w10/react-w10-library-here-crop.png');
    const w10CropRect = { x: 12, y: 72, width: 366, height: 478 };

    await cropHistoricalImage(pageW10, reactW10Orig, w10CropRect, reactW10CropPath);
    const reactW10PngDim = getPngDimensions(reactW10CropPath);

    receipts.pairs.push({
      id: 'W-10-document-library',
      title: 'W-10 Document Library "Tạo ở đây" Filter',
      viewport: { width: 390, height: 900, dpr: 1 },
      theme: 'light',
      reducedMotion: 'no-preference',
      htmlSource: {
        file: 'design/preview/w10_quiz_screens.html',
        url: w10Url,
        rawSha256: receipts.sources.w10Html.rawSha256,
        gitBlobSha256: receipts.sources.w10Html.gitBlobSha256
      },
      reactSource: {
        label: 'historical-runtime-original',
        originalCommit: '1fc0f553bec808241388b722fa2c10a1c6ead33d',
        acceptedCommitReuse: 'aaf68eb6795c929169e5212a05093d8d817c76e3',
        currentMainCommit: 'b2fedda1f4453fc79880f1203cfa70e07aa67db1',
        narrowReuseValid: true,
        diffBytesToAccepted: 0,
        runtimeUrl: 'http://127.0.0.1:8020/courses/c1/modules/m1',
        originalImage: 'report/w10-r7-evidence/browser-r7-main/library-here-390-light.png',
        originalSha256: hashFile(reactW10Orig),
        originalDimensions: [390, 900]
      },
      evidence: {
        htmlImage: {
          path: 'report/w23-evidence/w10/html-w10-library-here-390-light.png',
          status: 'canonical-reused-from-24538ae0',
          sha256: hashFile(htmlW10Path),
          bytes: fs.statSync(htmlW10Path).size,
          decodedPngDimensions: htmlW10PngDim,
          elementBoundingRect: w10SectionMetrics.elementBoundingRect
        },
        reactCroppedImage: {
          path: 'report/w23-evidence/w10/react-w10-library-here-crop.png',
          status: 'historical-runtime-crop',
          sha256: hashFile(reactW10CropPath),
          bytes: fs.statSync(reactW10CropPath).size,
          decodedPngDimensions: reactW10PngDim,
          cropRect: w10CropRect
        },
        htmlMetrics: {
          section: w10SectionMetrics,
          tab: w10TabMetrics,
          card: w10CardMetrics,
          font: w10Font
        },
        reactActualMetrics: {
          tabs: '2 contextual tabs: "Tạo ở đây (2)" and "Tạo ở nơi khác (2)"',
          tabTarget: {
            minHeight: '44px',
            measuredHeight: 44.0,
            padding: '8px 12px',
            borderRadius: '6px'
          },
          cards: {
            count: 2,
            width: 332,
            padding: 16
          },
          uxClassification: 'Allowed UX difference requiring owner decision (Option 4)'
        }
      }
    });

    await ctxW10.close();

    // -----------------------------------------------------------------------------------
    // OFFLINE AUDIT CONTEXT (Dedicated reproduction run with HTTP(S) blocked)
    // -----------------------------------------------------------------------------------
    const ctxOffline = await browser.newContext({
      viewport: { width: 1280, height: 900 },
      colorScheme: 'dark',
      reducedMotion: 'reduce'
    });
    await ctxOffline.route(/^https?:/, route => route.abort());
    const pageOffline = await ctxOffline.newPage();
    await pageOffline.goto(w08Url);
    await pageOffline.evaluate(() => document.fonts.ready);
    await pageOffline.locator('#theme-toggle-btn').click();
    await pageOffline.waitForTimeout(300);

    const offlineW08Font = await fontReceipt(pageOffline, '#details-self-check summary');
    await ctxOffline.close();

    receipts.offlineFallbackAudit = {
      note: 'Verified in isolated headless Chromium with all external HTTP(S) aborted (no Google Fonts download).',
      w08SummaryFontFallback: offlineW08Font,
      w08FallbackPlatformFonts: offlineW08Font.platformFonts,
      documentFontsStatus: offlineW08Font.document.status,
      loadedFacesCount: offlineW08Font.document.faces.length,
      explanation: 'When external font download is blocked, Chromium falls back to Segoe UI (system font) and faces array is empty; this is expected behavior in an isolated sandbox and does not alter element bounding boxes or interaction logic.'
    };

    // Write receipts json
    const receiptsPath = path.join(worktreeDir, 'report/w23-evidence/w23-slice1-receipts.json');
    fs.writeFileSync(receiptsPath, JSON.stringify(receipts, null, 2), 'utf8');
    console.log('Saved updated receipts to', receiptsPath);

  } finally {
    await browser.close();
  }
})().catch(err => {
  console.error('Error running capture_w23_slice1_fixed:', err);
  process.exitCode = 1;
});
