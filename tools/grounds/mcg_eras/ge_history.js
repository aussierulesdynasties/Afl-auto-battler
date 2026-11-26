// Google Earth web, historical imagery: step back to the oldest date, then forward one date at a time,
// saving a straight-down capture of the MCG at each. Reference only: captures never go in the repo.
const {chromium}=require('playwright');
const W=+process.env.W||2000,H=+process.env.H||2000,R=process.env.R||'520',N=+process.argv[2]||25, BACK=+process.argv[3]||130;
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const shot=async(o)=>{for(let i=0;i<4;i++){try{return await p.screenshot({...o,timeout:90000});}catch(e){console.log('shot retry');}}};
const p=await b.newPage({viewport:{width:W,height:H}});
await p.goto(`https://earth.google.com/web/@-37.81990,144.98330,20a,${R}d,35y,0h,0t,0r`,{timeout:120000});
await p.waitForTimeout(30000);
await p.mouse.click(W/2+204,H/2-240); await p.waitForTimeout(800);
await p.mouse.click(45,148); await p.waitForTimeout(500);
await p.mouse.click(712,163); await p.waitForTimeout(500);
await p.mouse.click(543,57); await p.waitForTimeout(8000);
await p.mouse.click(712,163); await p.waitForTimeout(500); await p.mouse.click(45,148); await p.waitForTimeout(500);
await p.waitForTimeout(3000); await p.mouse.click(712,163); await p.waitForTimeout(400); await p.mouse.click(W-315,245); await p.waitForTimeout(400); await p.mouse.click(1177,1955); await p.waitForTimeout(400);
await shot({path:'hist_setup.png'}); if(process.env.SETUP_ONLY){await b.close();return;}
await p.mouse.click(45,148); await p.waitForTimeout(800); await p.mouse.click(45,148); await p.waitForTimeout(800); await shot({path:'hist_setup2.png'});
for(let i=0;i<BACK;i++){if(i%25==0){await p.mouse.click(45,148);await p.waitForTimeout(300);} await p.mouse.click(300,120); await p.waitForTimeout(600);}
await p.waitForTimeout(4000);
for(let k=0;k<N;k++){ await p.mouse.click(429,120); await p.waitForTimeout(25000);
  await shot({path:'hist_'+String(k).padStart(2,'0')+'.png'}); console.log('fwd',k);}
await b.close();})();
