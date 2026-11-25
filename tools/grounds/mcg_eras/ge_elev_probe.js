// Hover points in Google Earth web (3D, straight down) and save the status-bar readout for each.
const {chromium}=require('playwright'); const fs=require('fs');
const W=2000,H=2000; const pts=JSON.parse(fs.readFileSync(process.argv[2]));
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:W,height:H}});
await p.goto(`https://earth.google.com/web/@-37.81990,144.98330,20a,950d,35y,0h,0t,0r`,{timeout:120000});
await p.waitForTimeout(40000);
await p.mouse.click(W/2+204,H/2-240); await p.waitForTimeout(800); await p.mouse.click(45,148); await p.waitForTimeout(800);
await p.screenshot({path:'full.png',timeout:90000});
for(const [i,[x,y]] of pts.entries()){ await p.mouse.move(x,y); await p.waitForTimeout(1500);
  await p.screenshot({path:`s_${String(i).padStart(3,'0')}.png`,clip:{x:1350,y:1970,width:650,height:30},timeout:90000}); }
await b.close();})();
