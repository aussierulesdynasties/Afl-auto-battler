import functools,builtins
print=functools.partial(builtins.print,flush=True)
import subprocess,time,json,urllib.request,base64,sys,websocket,os
SP=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W,H=int(os.environ.get('W',1920)),int(os.environ.get('H',1080))
args=[CH,'--headless=new','--enable-gpu','--ignore-gpu-blocklist','--use-angle=d3d11','--remote-debugging-port=9333',
 '--user-data-dir='+SP+r'\ge\prof2',f'--window-size={W},{H}','--hide-scrollbars','--no-first-run','about:blank']
p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
  for i in range(120):
    try: tabs=json.load(urllib.request.urlopen('http://127.0.0.1:9333/json'));break
    except Exception: time.sleep(0.5)
  ws=websocket.create_connection([t for t in tabs if t['type']=='page'][0]['webSocketDebuggerUrl'],timeout=120)
  n=[0]
  def cmd(m,**pa):
    n[0]+=1;ws.send(json.dumps({'id':n[0],'method':m,'params':pa}))
    while True:
      r=json.loads(ws.recv())
      if r.get('id')==n[0]: return r
  cmd('Page.enable')
  cmd('Emulation.setDeviceMetricsOverride',width=W,height=H,deviceScaleFactor=1,mobile=False)
  print(cmd('Runtime.evaluate',expression="(()=>{const c=document.createElement('canvas');const g=c.getContext('webgl2');if(!g)return 'no webgl2';const e=g.getExtension('WEBGL_debug_renderer_info');return g.getParameter(e.UNMASKED_RENDERER_WEBGL)})()")['result']['result'].get('value'))
  jobs=json.loads(sys.argv[1])  # list of [url,wait,out]
  def click(x,y):
    for t in ('mousePressed','mouseReleased'): cmd('Input.dispatchMouseEvent',type=t,x=x,y=y,button='left',clickCount=1)
  for job in jobs:
    url,wait,out=job[:3]
    cmd('Page.navigate',url=url); time.sleep(wait)
    for c in (job[3] if len(job)>3 else []):
      if isinstance(c,list) and c and c[0]=='js': print('js:',cmd('Runtime.evaluate',expression=c[1],awaitPromise=True)['result'].get('result',{}).get('value'))
      elif isinstance(c,list) and c and c[0]=='key':
        k=c[1];m=c[2] if len(c)>2 else 0;vk=ord(k.upper()) if len(k)==1 else 27
        for t in ('rawKeyDown','keyUp'): cmd('Input.dispatchKeyEvent',type=t,key=k,code='Key'+k.upper() if len(k)==1 else k,windowsVirtualKeyCode=vk,modifiers=m)
      elif c=='esc': cmd('Input.dispatchKeyEvent',type='keyDown',key='Escape',code='Escape',windowsVirtualKeyCode=27); cmd('Input.dispatchKeyEvent',type='keyUp',key='Escape',code='Escape',windowsVirtualKeyCode=27)
      else: click(*c)
      time.sleep(1.5)
    if out=='-':
      r=cmd('Page.captureScreenshot',format='png');open('ge/_last.png','wb').write(base64.b64decode(r['result']['data']));continue
    for xy in ((1163,300),(1867,781),(752,163),(45,148)): click(*xy); time.sleep(0.7)
    time.sleep(2)
    time.sleep(1)
    r=cmd('Page.captureScreenshot',format='png')
    open(out,'wb').write(base64.b64decode(r['result']['data'])); print('saved',out)
finally:
  p.kill()
