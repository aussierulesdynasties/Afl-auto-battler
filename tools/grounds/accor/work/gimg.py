# Google Images: save the first N result thumbnails + source links per query (reference only, never textures).
import subprocess,time,json,urllib.request,urllib.parse,base64,sys,os,websocket
CH=r"C:\Program Files\Google\Chrome\Application\chrome.exe"; SP=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=sys.argv[1]; Q=json.load(open(sys.argv[2])); N=12
JS=r"""JSON.stringify([...document.images].filter(i=>i.naturalWidth>=60&&i.src.startsWith('data:image/jpeg')).slice(0,%d).map(i=>{let l='',k=i;for(let j=0;j<10&&k;j++){let a=k.querySelector&&k.querySelector('a[href^="http"]:not([href*="google."])');if(a){l=a.href;break}k=k.parentElement}return [i.src,l]}))"""%N
print("launch",flush=True);p=subprocess.Popen([CH,'--headless=new','--remote-debugging-port=9433','--user-data-dir='+SP+r'\ge\prof_accor','--no-first-run','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
  for i in range(100):
    try: tabs=json.load(urllib.request.urlopen('http://127.0.0.1:9433/json'));break
    except Exception: time.sleep(0.5)
  print("tabs",len(tabs),flush=True);ws=websocket.create_connection([t for t in tabs if t['type']=='page'][0]['webSocketDebuggerUrl'],timeout=60); n=[0]
  def cmd(m,**pa):
    n[0]+=1;ws.send(json.dumps({'id':n[0],'method':m,'params':pa}))
    while True:
      r=json.loads(ws.recv())
      if r.get('id')==n[0]: return r
  for tag,q in Q.items():
    cmd('Page.navigate',url='https://www.google.com/search?udm=2&q='+urllib.parse.quote(q)); time.sleep(8)
    print(cmd("Runtime.evaluate",expression="location.href+'|'+document.title+'|'+document.images.length")["result"],flush=True);rr=cmd("Runtime.evaluate",expression=JS)["result"]
    if 'exceptionDetails' in rr: print(tag,'ERR',str(rr['exceptionDetails'])[:300]); continue
    items=json.loads(rr['result'].get('value','[]')); src=[]
    for k,(d,l) in enumerate(items):
      fn='%s_%02d.jpg'%(tag,k); open(os.path.join(OUT,fn),'wb').write(base64.b64decode(d.split(',',1)[1])); src.append('%s  %s  (Google Images: %s)'%(fn,l,q))
    open(os.path.join(OUT,'SOURCES.txt'),'a',encoding='utf-8').write('\n'.join(src)+'\n'); print(tag,len(items),flush=True)
finally: p.kill()
