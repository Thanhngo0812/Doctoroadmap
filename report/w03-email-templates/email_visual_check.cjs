const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "../..");
const toolsRoot = fs.existsSync(path.join(root, ".tmp/w01-browser-tools")) ? root : path.resolve(root, "../..");
process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(toolsRoot, ".tmp/w01-browsers");
const { chromium } = require(path.join(toolsRoot, ".tmp/w01-browser-tools/node_modules/playwright"));
const sampleDir = path.join(root, "report/w03-email-templates");
const outputDir = path.join(sampleDir, "screenshots");
const logoPath = path.join(root, "src/web/frontend/public/assets/Artboard 24.png");
const samples = [
  ["verify", "Xác minh email.html", "/xac-minh", "#token=demo-verify-token"],
  ["reset", "Đặt lại mật khẩu.html", "/dat-lai-mat-khau", "#token=demo-reset-token"],
  ["existing", "Tài khoản đã tồn tại.html", "/dang-nhap", ""],
];

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const [name, filename, expectedPath, expectedHash] of samples) {
      for (const [width, device] of [[1280, "desktop"], [390, "mobile"]]) {
        const page = await browser.newPage({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
        const errors = [];
        let logoLoaded = false;
        page.on("pageerror", (error) => errors.push(error.message));
        await page.route("**/*", async (route) => {
          const url = new URL(route.request().url());
          if (url.hostname === "wayfinder.example.vn" && url.pathname === "/assets/Artboard%2024.png") {
            logoLoaded = true;
            await route.fulfill({
              status: 200,
              contentType: "image/png",
              body: fs.readFileSync(logoPath),
            });
          } else {
            await route.abort("blockedbyclient");
          }
        });
        await page.setContent(fs.readFileSync(path.join(sampleDir, filename), "utf8"), { waitUntil: "load" });
        await page.locator("img[alt='WayFinder']").waitFor();
        await page.screenshot({
          path: path.join(outputDir, `${name}-${device}.png`),
          fullPage: true,
        });
        const facts = await page.evaluate(() => ({
          title: document.querySelector("h1")?.innerText ?? "(no heading)",
          bodyWidth: document.body.scrollWidth,
          viewportWidth: window.innerWidth,
          documentHeight: document.documentElement.scrollHeight,
          logoWidth: document.querySelector("img[alt='WayFinder']")?.naturalWidth ?? 0,
          buttonText: document.querySelector("a[style*='inline-block']")?.innerText ?? "(no action)",
          actionUrl: (() => {
            const url = new URL(document.querySelector("a[style*='inline-block']").href);
            return { pathname: url.pathname, hash: url.hash, search: url.search };
          })(),
        }));
        if (facts.actionUrl.pathname !== expectedPath || facts.actionUrl.hash !== expectedHash || facts.actionUrl.search !== "") {
          throw new Error(`${name}/${device}: unexpected primary link ${JSON.stringify(facts.actionUrl)}`);
        }
        assert.ok(facts.bodyWidth <= width, `${name}/${device}: horizontal overflow`);
        assert.ok(logoLoaded && facts.logoWidth > 0, `${name}/${device}: logo did not load`);
        assert.deepEqual(errors, [], `${name}/${device}: browser errors`);
        results.push({ sample: name, device, ...facts, logoLoaded, errors });
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(sampleDir, "visual-metadata.json"), JSON.stringify(results, null, 2), "utf8");
  process.stdout.write(JSON.stringify(results, null, 2) + "\n");
}

main().catch((error) => {
  process.stderr.write(`${error.name}: ${error.message}\n`);
  process.exitCode = 1;
});
