// node probe.js URL points.json outdir : Google Earth status-bar readout (lat/lon/height under the mouse) at each screen point
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [url, pf, out] = process.argv.slice(2); const pts = JSON.parse(fs.readFileSync(pf)); fs.mkdirSync(out, {recursive: true});
  const b = await chromium.launch({args: ['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport: {width: 1280, height: 1000}});
  await p.goto(url, {timeout: 90000}); await p.waitForTimeout(12000);
  for (const sel of ['[aria-label="Close"]', 'text=Dismiss']) { try { await p.click(sel, {timeout: 1500}); } catch (e) {} }
  await p.keyboard.press('Escape'); await p.waitForTimeout(25000);
  await p.mouse.move(1279, 999); await p.screenshot({path: out + '/view.png'});
  for (let i = 0; i < pts.length; i++) {
    const [x, y] = pts[i]; await p.mouse.move(x, y); await p.waitForTimeout(700);
    await p.screenshot({path: `${out}/r${String(i).padStart(5,'0')}.png`, clip: {x: 880, y: 972, width: 400, height: 26}});
  }
  await b.close(); console.log('done', pts.length);
})();
