const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('BROWSER_ERROR:', msg.text());
    } else {
      console.log('BROWSER_LOG:', msg.text());
    }
  });
  
  page.on('pageerror', err => console.log('PAGE_EXCEPTION:', err.message));
  
  try {
    await page.goto('http://localhost:5173/finance', { waitUntil: 'networkidle' });
    console.log("Loaded page.");
    await page.waitForTimeout(2000); // wait for any async renders
  } catch (e) {
    console.log("Nav failed:", e.message);
  }
  
  await browser.close();
})();
