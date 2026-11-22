// Google Earth shots for ge_compare.py: node tools/grounds/ge_shoot.js <workdir> (reads <workdir>/urls.json).
// Headless Chromium on swiftshader; a fresh page per view (Google Earth sometimes shows the globe otherwise).
// node tools/grounds/ge_shoot.js <workdir> --level: Google Earth's own height for the turf (ge_compare.py's ge_alt).
// It opens <workdir>/level_url.json (straight down on the field centre), puts the mouse on five spots of grass round
// the middle and saves their status-bar readouts (lat/lon and height under the mouse) as <workdir>/ge/_level.png.
// `python3 tools/grounds/ge_compare.py level <ground> <views.json> <workdir>` reads them (tesseract); set the ground's
// ge_alt to the turf's height (a spot on a stand reads higher).
const { chromium } = require('playwright');
const fs = require('fs');
async function settle(p, url) {   // load a view and let Google Earth stream it in, with its pop-ups closed
  await p.goto(url, {timeout: 90000});
  await p.waitForTimeout(12000);
  for (const sel of ['[aria-label="Close"]', 'text=Dismiss']) { try { await p.click(sel, {timeout: 1500}); } catch (e) {} }
  await p.keyboard.press('Escape');
  await p.waitForTimeout(16000);
}
// The status bar's readout with the mouse on the picture's centre: where Google Earth really put the camera
// ("Camera: N m" above sea level) and the lat/lon and height of what the centre shows. Google Earth lifts a
// camera it thinks too low (15-30 m at Adelaide, measured 2026-11-22) and keeps its spot and tilt, so
// ge_compare.py plan reads this back and puts ours where Google Earth's really was.
async function readout(p, path) {
  await p.mouse.move(640, 500); await p.waitForTimeout(1500);
  await p.screenshot({path, clip: {x: 900, y: 972, width: 380, height: 26}});
}
(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  if (process.argv[3] === '--level') {
    const p = await b.newPage({viewport: {width: 1280, height: 1000}});
    await settle(p, JSON.parse(fs.readFileSync(process.argv[2] + '/level_url.json')));
    fs.mkdirSync(process.argv[2] + '/ge', {recursive: true});
    const strips = [];
    for (const [x, y] of [[640, 500], [600, 470], [680, 470], [600, 530], [680, 530]]) {
      await p.mouse.move(x, y); await p.waitForTimeout(1500);
      strips.push(await p.screenshot({clip: {x: 900, y: 972, width: 380, height: 26}}));
    }
    // stack the five readouts into one picture in the page itself (no image library needed here)
    const urls = strips.map(s => 'data:image/png;base64,' + s.toString('base64'));
    const q = await b.newPage({viewport: {width: 380, height: 26 * urls.length}});
    await q.setContent('<body style="margin:0">' + urls.map(u => '<img style="display:block" src="' + u + '">').join('') + '</body>');
    await q.screenshot({path: process.argv[2] + '/ge/_level.png'});
    console.log('level readouts', process.argv[2] + '/ge/_level.png');
    await b.close(); return;
  }
  const list = JSON.parse(fs.readFileSync(process.argv[2] + '/urls.json'));
  const only = process.argv.slice(3);
  for (const [out, url] of list) {
    if (only.length && !only.some(n => out.endsWith('/' + n + '.png'))) continue;
    const p = await b.newPage({viewport: {width: 1280, height: 1000}});
    try {
      await settle(p, url);
      await p.mouse.move(1279, 999);   // keep the pointer's hover marks out of the picture
      await p.screenshot({path: out, clip: {x: 0, y: 140, width: 1280, height: 720}});
      await readout(p, out.replace(/\.png$/, '_cam.png'));
      console.log('ok', out);
    } catch (e) { console.log('fail', out, e.message); }
    await p.close();
  }
  await b.close();
})();
