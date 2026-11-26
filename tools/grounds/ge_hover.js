// Google Earth's own 3D position of chosen points: node tools/grounds/ge_hover.js <points.json> <out_dir>
// <points.json> is [[url, [[x, y], ...]], ...]: a Google Earth view (ge_compare.py's urls) and points in its
// 1280 x 720 shot. For each point this puts the mouse there and saves the status bar's readout, which gives the
// latitude, longitude and height above sea level of the surface under the mouse (Google Earth's 3D mesh, to
// 0.01" and the metre) as <out_dir>/<view>_<n>.png; ge_compare.readouts / scg/hover.py read them (tesseract).
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const list = JSON.parse(fs.readFileSync(process.argv[2]));
  // HOVER_SCALE=0.5 draws Google Earth in a 640 x 500 window instead of 1280 x 1000 (same field of view, a
  // quarter of the pixels to draw on a software renderer); the points are scaled to it, and the status bar,
  // a fixed size at the window's bottom right, is read where it then sits.
  const k = Number(process.env.HOVER_SCALE || 1);
  const W = Math.round(1280 * k), H = Math.round(1000 * k);
  fs.mkdirSync(process.argv[3], {recursive: true});
  for (const [name, url, pts] of list) {
    if (pts.every((_, i) => fs.existsSync(process.argv[3] + '/' + name + '_' + i + '.png'))) continue;
    const p = await b.newPage({viewport: {width: W, height: H}});
    try {
      await p.goto(url, {timeout: 90000});
      await p.waitForTimeout(12000);
      for (const sel of ['[aria-label="Close"]', 'text=Dismiss']) { try { await p.click(sel, {timeout: 1500}); } catch (e) {} }
      await p.keyboard.press('Escape');
      await p.waitForTimeout(20000);
      for (let i = 0; i < pts.length; i++) {
        const f = process.argv[3] + '/' + name + '_' + i + '.png';
        if (fs.existsSync(f)) continue;
        await p.mouse.move(pts[i][0] * k, (pts[i][1] + 140) * k); await p.waitForTimeout(Number(process.env.HOVER_WAIT || 400));
        await p.screenshot({path: f, clip: {x: W - 380, y: H - 28, width: 380, height: 26}});
      }
      console.log('ok', name, pts.length);
    } catch (e) { console.log('fail', name, e.message); }
    await p.close();
  }
  await b.close();
})();
