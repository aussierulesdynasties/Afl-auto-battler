// Google Earth shots for ge_compare.py: node tools/grounds/ge_shoot.js <workdir> (reads <workdir>/urls.json).
// Headless Chromium on swiftshader; a fresh page per view (Google Earth sometimes shows the globe otherwise).
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const list = JSON.parse(fs.readFileSync(process.argv[2] + '/urls.json'));
  const only = process.argv.slice(3);
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  for (const [out, url] of list) {
    if (only.length && !only.some(n => out.endsWith('/' + n + '.png'))) continue;
    const p = await b.newPage({viewport: {width: 1280, height: 1000}});
    try {
      await p.goto(url, {timeout: 90000});
      await p.waitForTimeout(12000);
      await p.keyboard.press('Escape');
      await p.waitForTimeout(16000);
      // The "Dismiss" card arrives late; clear it just before the shot.
      for (const sel of ['text=Dismiss', '[aria-label="Close"]']) { try { await p.click(sel, {timeout: 1500}); } catch (e) {} }
      await p.waitForTimeout(1500);
      await p.screenshot({path: out, clip: {x: 0, y: 140, width: 1280, height: 720}});
      console.log('ok', out);
    } catch (e) { console.log('fail', out, e.message); }
    await p.close();
  }
  await b.close();
})();
