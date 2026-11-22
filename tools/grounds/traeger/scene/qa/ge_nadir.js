// Google Earth straight-down views for mosaic.py (measuring only: the shots stay out of the repo).
//   node ge_nadir.js nadir.json OUTDIR FROM TO      (two processes on halves of the list go twice as fast)
// A fresh page per view; Google Earth's popups are found and closed by find_popup.py, and a shot under
// 1.8 MB (the globe, or tiles still loading) is taken again.
const { chromium } = require('playwright');
const path = require('path');
const fs=require('fs'); const cp=require('child_process');
(async () => {
  const [,, vf, outd, from, to] = process.argv;
  let views = JSON.parse(fs.readFileSync(vf)).slice(parseInt(from), parseInt(to));
  const b = await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  for (const v of views) {
    if (fs.existsSync(`${outd}/${v.name}.png`)) continue;
    for (let attempt=0; attempt<3; attempt++) {
      const p = await b.newPage({viewport:{width:1280,height:1000}});
      const url = `https://earth.google.com/web/@${v.lat},${v.lon},${v.alt}a,${v.d}d,${v.fov||35}y,${v.h||0}h,${v.t||0}t,0r`;
      let ok=false;
      try {
        await p.goto(url, {timeout:90000});
        await p.waitForTimeout(40000);
        await p.keyboard.press('Escape');
        for (let k=0;k<3;k++) {
          const tmp=`${outd}/_tmp_${from}.png`;
          await p.screenshot({path: tmp});
          const r=cp.execSync(`python3 ${path.join(__dirname, 'find_popup.py')} ${tmp}`).toString().trim();
          if (!r) break;
          for (const xy of r.split(' ')) { const [x,y]=xy.split(',').map(Number); await p.mouse.click(x,y); await p.waitForTimeout(700); }
        }
        await p.waitForTimeout(2500);
        const buf = await p.screenshot({path: `${outd}/${v.name}.png`});
        ok = buf.length > 1800000;
        console.log('shot', v.name, buf.length, ok);
      } catch(e){ console.log('fail',v.name,e.message); }
      await p.close();
      if (ok) break;
      if (fs.existsSync(`${outd}/${v.name}.png`)) fs.renameSync(`${outd}/${v.name}.png`, `${outd}/${v.name}.bad${attempt}.png`);
    }
  }
  await b.close();
})();
