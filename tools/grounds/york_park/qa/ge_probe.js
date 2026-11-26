// Google Earth heights under the mouse: node ge_probe.js <workdir> (reads <workdir>/probe.json, written by probe.py).
// Each job is a straight-down view centred on a building; the mouse visits screen spots worked out from metres
// (the URL's 35y is the vertical field of view of the 1000-row window, ge_compare.py) and each status-bar
// readout (lat/lon and the height of what is under the mouse, m above sea level) is saved as one strip:
// <workdir>/probe/<name>_<k>.png, read back by probe.py with tesseract.
const { chromium } = require('playwright');
const fs = require('fs');
async function settle(p, url) {
  await p.goto(url, {timeout: 90000});
  await p.waitForTimeout(12000);
  for (const sel of ['[aria-label="Close"]', 'text=Dismiss']) { try { await p.click(sel, {timeout: 1500}); } catch (e) {} }
  await p.keyboard.press('Escape');
  await p.waitForTimeout(16000);
}
(async () => {
  const W = process.argv[2]; const jobs = JSON.parse(fs.readFileSync(W + '/probe.json'));
  fs.mkdirSync(W + '/probe', {recursive: true});
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  for (const j of jobs) {
    if (fs.existsSync(`${W}/probe/${j.name}_${j.px.length - 1}.png`)) continue;   // done; a part-done job resumes
    const p = await b.newPage({viewport: {width: 1280, height: 1000}});
    try {
      await settle(p, j.url);
      await p.screenshot({path: `${W}/probe/${j.name}_view.png`});
      for (let k = 0; k < j.px.length; k++) {
        if (fs.existsSync(`${W}/probe/${j.name}_${k}.png`)) continue;
        await p.mouse.move(j.px[k][0], j.px[k][1]); await p.waitForTimeout(1200);
        await p.screenshot({path: `${W}/probe/${j.name}_${k}.png`, clip: {x: 900, y: 972, width: 380, height: 26}});
      }
      console.log('ok', j.name);
    } catch (e) { console.log('fail', j.name, e.message); }
    await p.close();
  }
  await b.close();
})();
