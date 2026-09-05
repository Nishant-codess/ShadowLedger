const { chromium } = require('playwright');
const path = require('path');

const SCREENSHOT_DIR = '/Users/nishant/.gemini/antigravity-ide/brain/a3cc6efd-c551-448a-8774-043c7c4c6571/screenshots';

async function run() {
  console.log('Starting Playwright site crawl & comprehensive audit...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
  });
  const page = await context.newPage();

  async function snap(name) {
    const filePath = path.join(SCREENSHOT_DIR, `${name}.png`);
    await page.screenshot({ path: filePath, fullPage: true });
    console.log(`Saved screenshot: ${name}.png`);
  }

  try {
    // 1. Home / Command Center
    console.log('\n--- 1. Visiting Home Page ---');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('01_command_center');

    // 2. Click "Explore Kirana Story" or Hero A card
    console.log('\n--- 2. Clicking Hero A (Kirana) ---');
    const heroACard = page.locator('text=Hero A • Kirana').first();
    await heroACard.click();
    await page.waitForURL(/\/cases\//, { timeout: 10000 });
    await page.waitForTimeout(1500);
    await snap('02_hero_a_explain');

    // 3. Click "Generate AI Investigation Narrative" on Hero A
    console.log('\n--- 3. Clicking Generate AI Investigation Narrative on Hero A ---');
    const explainButton = page.locator('button:has-text("Generate AI Investigation Narrative")').first();
    if (await explainButton.isVisible()) {
      await explainButton.click();
      await page.waitForTimeout(2000);
      await snap('03_hero_a_ai_narrative');
    }

    // 4. Click a node in the Value Flow Graph (inspect node)
    console.log('\n--- 4. Clicking a node in Value Flow Graph ---');
    const chocolateNode = page.locator('text=Dairy Milk Chocolate Change').first();
    if (await chocolateNode.isVisible()) {
      await chocolateNode.click();
      await page.waitForTimeout(500);
    }

    // 5. Toggle INVESTIGATE Mode on Hero A
    console.log('\n--- 5. Toggling INVESTIGATE Mode on Hero A ---');
    const investigateToggle = page.locator('button:has-text("INVESTIGATE")').first();
    if (await investigateToggle.isVisible()) {
      await investigateToggle.click();
      await page.waitForTimeout(1000);
      await snap('04_hero_a_investigate');
    }

    // 6. Navigate back to Home and click Hero B
    console.log('\n--- 6. Triggering Hero B (Mobility) ---');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    const heroBCard = page.locator('text=Hero B • Mobility').first();
    await heroBCard.click();
    await page.waitForURL(/\/cases\//, { timeout: 10000 });
    await page.waitForTimeout(1500);

    // Switch back to EXPLAIN if not in Explain
    const explainToggle = page.locator('button:has-text("EXPLAIN")').first();
    if (await explainToggle.isVisible()) {
      await explainToggle.click();
      await page.waitForTimeout(500);
    }
    await snap('05_hero_b_explain');

    // 7. Click Local AI on Hero B
    console.log('\n--- 7. Clicking Generate AI Investigation Narrative on Hero B ---');
    const explainBtnB = page.locator('button:has-text("Generate AI Investigation Narrative")').first();
    if (await explainBtnB.isVisible()) {
      await explainBtnB.click();
      await page.waitForTimeout(2000);
      await snap('06_hero_b_ai_narrative');
    }

    // 8. Toggle INVESTIGATE on Hero B
    console.log('\n--- 8. Toggling INVESTIGATE Mode on Hero B ---');
    const investigateToggleB = page.locator('button:has-text("INVESTIGATE")').first();
    if (await investigateToggleB.isVisible()) {
      await investigateToggleB.click();
      await page.waitForTimeout(1000);
      await snap('07_hero_b_investigate');
    }

    // 9. Exceptions Workbench
    console.log('\n--- 9. Visiting Exceptions Workbench ---');
    await page.goto('http://localhost:3000/exceptions', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('08_exceptions_all');

    // Filter by Human Review
    console.log('\n--- 10. Filtering Exceptions by Human Review ---');
    const humanReviewTab = page.locator('button:has-text("Human Review")').first();
    if (await humanReviewTab.isVisible()) {
      await humanReviewTab.click();
      await page.waitForTimeout(500);
      await snap('09_exceptions_human_review');
    }

    // Filter by Auto-Resolved
    console.log('\n--- 11. Filtering Exceptions by Auto-Resolved ---');
    const autoResolvedTab = page.locator('button:has-text("Auto-Resolved")').first();
    if (await autoResolvedTab.isVisible()) {
      await autoResolvedTab.click();
      await page.waitForTimeout(500);
      await snap('10_exceptions_autoresolved');
    }

    // 10. Fleet Patterns
    console.log('\n--- 12. Visiting Fleet Patterns ---');
    await page.goto('http://localhost:3000/patterns', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('11_patterns');

    // 11. Benchmark
    console.log('\n--- 13. Visiting Benchmark ---');
    await page.goto('http://localhost:3000/benchmark', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('12_benchmark');

    console.log('\nComprehensive Crawl & Screenshot capture successfully completed!');
  } catch (err) {
    console.error('Error during crawl:', err);
  } finally {
    await browser.close();
  }
}

run();
