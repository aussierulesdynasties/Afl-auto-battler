// Plays the Web probe (tools/perf/web_memory.sh) in headless Chromium and reads the page's memory.
//   node web_memory.js <site dir> <grounds, comma separated> <out dir>
// Memory read two ways at each step: the page's own measure (performance.measureUserAgentSpecificMemory:
// JavaScript and the game's WebAssembly memory), and the resident memory of Chromium's page and GPU
// processes from /proc (what a phone would have to hold). Writes <out>/web_memory.json.
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { chromium } = require('playwright');

const [site, grounds, out] = process.argv.slice(2);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm', '.pck': 'application/octet-stream',
  '.png': 'image/png', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(site) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream',
    'Cross-Origin-Opener-Policy': 'same-origin', 'Cross-Origin-Embedder-Policy': 'require-corp',
    'Content-Length': fs.statSync(p).size });
  fs.createReadStream(p).pipe(res);
});

function rssMB(kind) {
  // Chromium's processes of this run, by --type=; RSS in MB.
  let total = 0;
  for (const line of execSync('ps -eo pid=,rss=,args=').toString().split('\n')) {
    if (line.includes('--type=' + kind) && line.includes('pw-browsers')) total += parseInt(line.trim().split(/\s+/)[1], 10) / 1024;
  }
  return Math.round(total);
}

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  // The probe's arguments, as a command line would give them.
  const html = path.join(site, 'index.html');
  let page_html = fs.readFileSync(html, 'utf8');
  const args = ['--', 'grounds=' + grounds, 'levels=high', 'measure=4', 'size=1012x1242'];
  page_html = page_html.replace(/"args":\[[^\]]*\]/, '"args":' + JSON.stringify(args));
  fs.writeFileSync(html, page_html);
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1012, height: 1242 } });
  const steps = [];
  const log = [];
  async function sample(label) {
    // Godot's own count of what it holds (the probe prints it in each row) comes from the console;
    // the browser's own figure where it gives one.
    const m = await page.evaluate(async () => {
      if (!(globalThis.performance && performance.measureUserAgentSpecificMemory)) return {};
      try { return { page_mb: Math.round((await performance.measureUserAgentSpecificMemory()).bytes / 1048576) }; }
      catch (e) { return {}; }
    }).catch(() => ({}));
    const row = { step: label, ...m, renderer_rss_mb: rssMB('renderer'), gpu_rss_mb: rssMB('gpu-process') };
    steps.push(row);
    console.log(JSON.stringify(row));
  }
  let waiters = [];
  page.on('console', msg => {
    const t = msg.text();
    log.push(t);
    if (/fetched|high|Playing|ERROR|error/i.test(t)) console.log('  page:', t.slice(0, 160));
    waiters = waiters.filter(w => !(w.re.test(t) && (w.done(t), true)));
  });
  const wait = (re, ms) => new Promise((res, rej) => {
    waiters.push({ re, done: res });
    setTimeout(() => rej(new Error('timed out waiting for ' + re)), ms);
  });
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  await wait(/GameDB: \d+ players/, 600000);
  await sample('game started (no ground)');
  // The probe plays the grounds in its own order; each measured row is a step.
  const want = grounds.split(',');
  for (let i = 0; i < want.length; i++) {
    const row = await wait(new RegExp('^(' + want.join('|') + ')\\s+hig'), 1800000);
    // The probe's own row: Godot's memory and video memory in use (the last two numbers before load).
    const cols = row.trim().split(/\s+/);
    await sample(cols[0] + ' played (pack fetched and loaded, stadium built); probe row: ' + row.trim());
  }
  fs.writeFileSync(path.join(out, 'web_memory.json'), JSON.stringify({ grounds, steps }, null, 2));
  fs.writeFileSync(path.join(out, 'web_console.txt'), log.join('\n'));
  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
