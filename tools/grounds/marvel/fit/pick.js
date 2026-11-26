// usage: node pick.js NAME HEADING TILT RANGE X0 X1 Y0 Y1 STEP WAITMS
const { chromium } = require('playwright');
const fs=require('fs');
const [name,h,t,r,x0,x1,y0,y1,st,wm,sx]=process.argv.slice(2);
const out='/tmp/claude-0/obl/'+name; fs.mkdirSync(out,{recursive:true});
(async () => {
  const browser = await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const ctx = await browser.newContext({viewport:{width:1280,height:1000}});
  const page = await ctx.newPage();
  const url = `https://earth.google.com/web/@-37.8164953,144.9475565,8a,${r}d,35y,${h}h,${t}t,0r`;
  try { await page.goto(url, {timeout:90000}); } catch(e) { console.log('goto', e.message); }
  await page.waitForTimeout(15000);
  try { const d=page.getByText('Dismiss').first(); if (await d.isVisible({timeout:800})) await d.click({timeout:1500}); } catch(e) {}
  try { if (await page.getByText('New from Google Earth').first().isVisible({timeout:1000})) { await page.mouse.click(844,259);} } catch(e) {}
  await page.waitForTimeout(20000);
  await page.mouse.click(844,259); await page.waitForTimeout(3000);
  try { const d=page.getByText('Dismiss').first(); if (await d.isVisible({timeout:800})) await d.click({timeout:1500}); } catch(e) {}
  await page.waitForTimeout(25000);
  await page.mouse.move(5,500);await page.waitForTimeout(1500);
  await page.screenshot({path:out+'/view.png'});
  const pts=[];
  for (let y=+y0;y<=+y1;y+=+st) for (let x=+x0;x<=+x1;x+=+(sx||st)) pts.push([x,y]);
  let i=0;
  for (const [x,y] of pts) {
    await page.mouse.move(x-2,y-2);await page.mouse.move(x,y);await page.waitForTimeout(+wm);
    await page.screenshot({path:`${out}/p_${x}_${y}.png`,clip:{x:940,y:975,width:340,height:22}});
    if(++i%100==0)console.log(i,pts.length);
  }
  await page.screenshot({path:out+'/view_end.png'});
  await browser.close();
})();
