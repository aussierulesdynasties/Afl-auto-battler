// A Google Earth shot plus the status bar under chosen pixels, for oblique.py.
//   node ge_probe.js <dir> <name> <url>     (reads <dir>/pts.json: [[u, v], ...] in the 1280 x 720 crop)
// Saves <dir>/<name>.png (the crop, rows 140-860 of a 1280 x 1000 window) and <dir>/<name>_<i>.png (the status bar
// with the mouse on point i: tesseract reads the camera's altitude and the point's latitude, longitude and height).
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [dir, name, url] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport: {width: 1280, height: 1000}});
  await p.goto(url, {timeout: 90000});
  await p.waitForTimeout(12000);
  for (const sel of ['[aria-label="Close"]', 'text=Dismiss']) { try { await p.click(sel, {timeout: 1500}); } catch (e) {} }
  await p.keyboard.press('Escape');
  await p.waitForTimeout(20000);
  await p.mouse.move(1279, 999);
  await p.screenshot({path: `${dir}/${name}.png`, clip: {x: 0, y: 140, width: 1280, height: 720}});
  const pts = JSON.parse(fs.readFileSync(`${dir}/pts.json`));
  for (let i = 0; i < pts.length; i++) {
    await p.mouse.move(pts[i][0], pts[i][1] + 140);
    await p.waitForTimeout(1500);
    await p.screenshot({path: `${dir}/${name}_${i}.png`, clip: {x: 900, y: 972, width: 380, height: 26}});
  }
  await b.close();
})();
