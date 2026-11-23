// node ge_hover.js jobs.json outdir : jobs = [{name,url,pts:[[u,v],...]}] (u,v in the 1280x720 crop)
const { chromium } = require('playwright');const fs=require('fs');
(async()=>{
 const jobs=JSON.parse(fs.readFileSync(process.argv[2]));const out=process.argv[3];fs.mkdirSync(out,{recursive:true});
 const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 for(const j of jobs){
  const p=await b.newPage({viewport:{width:1280,height:1000}});
  try{await p.goto(j.url,{timeout:90000});}catch(e){}
  await p.waitForTimeout(12000);
  for(const sel of ['[aria-label="Close"]','text=Dismiss']){try{await p.click(sel,{timeout:1500});}catch(e){}}
  await p.keyboard.press('Escape');await p.waitForTimeout(16000);
  await p.mouse.move(1279,999);try{await p.screenshot({path:`${out}/${j.name}.png`,clip:{x:0,y:140,width:1280,height:720},timeout:120000});}catch(e){console.log('shotfail',j.name)}
  let i=0;
  for(const [u,v] of j.pts){await p.mouse.move(u,v+140);await p.waitForTimeout(900);
    try{await p.screenshot({path:`${out}/${j.name}_${String(i).padStart(4,'0')}.png`,clip:{x:900,y:972,width:380,height:26},timeout:60000});}catch(e){console.log('rofail',i)}i++;}
  console.log('done',j.name,i);await p.close();}
 await b.close();})();
