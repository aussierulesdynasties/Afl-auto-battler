// node ge_hover.js <plan.json> <outdir>: plan = [[url, [[name, px, py], ...]], ...] (px, py in the 1280x1000 window).
// One Google Earth page per view; the mouse visits each point and the status bar (lat/lon and the surface height under
// the mouse, whole metres) is saved as <outdir>/<name>.png.
const { chromium } = require('playwright');
const fs = require('fs');
const plan = JSON.parse(fs.readFileSync(process.argv[2]));
const OUT = process.argv[3]; fs.mkdirSync(OUT, {recursive: true});
(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  for (const [url, pts] of plan) {
    const p = await b.newPage({viewport: {width: 1280, height: 1000}});
    try {
      await p.goto(url, {timeout: 90000}); await p.waitForTimeout(12000);
      for (const sel of ['[aria-label="Close"]', 'text=Dismiss']) { try { await p.click(sel, {timeout: 1500}); } catch (e) {} }
      await p.keyboard.press('Escape'); await p.waitForTimeout(16000);
      for (const [name, x, y] of pts) {
        await p.mouse.move(x, y); await p.waitForTimeout(900);
        await p.screenshot({path: `${OUT}/${name}.png`, clip: {x: 900, y: 972, width: 380, height: 26}});
      }
      console.log('ok', url, pts.length);
    } catch (err) { console.log('fail', url, err.message); }
    await p.close();
  }
  await b.close();
})();
