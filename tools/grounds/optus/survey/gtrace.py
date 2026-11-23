import numpy as np,json,math,re,subprocess,os
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter
W=os.environ.get('OPTUS_WORK','/tmp/claude-0/gw')   # working folder of the Google Earth shots (never committed)
F=360/math.tan(math.radians(25.58/2))
OC=np.array([-30.382794076748684,-8.777071878585646])
TURF=5.0
def cam_h(name):
    im=Image.open(f'{W}/ge/{name}_cam.png');big=f'{W}/_x.png';im.resize((im.width*4,im.height*4),Image.LANCZOS).save(big)
    t=subprocess.run(['tesseract',big,'-','--psm','6'],capture_output=True,text=True).stdout
    return float(re.search(r'Camera:\s*([\d.,]+)\s*m',t).group(1).replace(',',''))-TURF
def shots():
    S=[]
    for v in json.load(open(f'{W}/views.json')):
        im=np.asarray(Image.open(f'{W}/ge/{v["name"]}.png').convert('RGB'),float)
        bad=np.zeros(im.shape[:2],bool);bad[:30,330:570]=True  # Dismiss box
        S.append(dict(v,H=cam_h(v['name']),im=im,bad=bad,L=gaussian_filter(im.min(2),0.7)))
    return S
def proj(s,x,y,z):
    return 640+F*(x-s['e'])/(s['H']-z),360-F*(y-s['n'])/(s['H']-z)
def ray_profile(s,th,rs,z):
    u,v=proj(s,OC[0]+rs*math.cos(th),OC[1]+rs*math.sin(th),z)
    ok=(u>3)&(u<1276)&(v>3)&(v<716)
    L=map_coordinates(s['L'],[v,u],order=1,mode='nearest')
    b=map_coordinates(s['bad'].astype(float),[v,u],order=0,mode='nearest')>0
    return L,ok&~b
def outer_edge(s,th,r0,z,step=0.05,thr=175,run=2.0):
    rs=np.arange(r0,r0+60,step);L,ok=ray_profile(s,th,rs,z)
    if not ok[0]:return None
    nrun=int(run/step);below=L<thr
    j=None
    for i in range(len(rs)-nrun):
        if not ok[i+nrun]:return None
        if below[i:i+nrun].all():j=i;break
    if j is None or j<int(3/step):return None
    hi=np.median(L[j-int(3/step):j]);lo=np.median(L[j+int(1/step):j+int(4/step)])
    if hi-lo<25:return None
    t=(hi+lo)/2;k=j-int(1.5/step)
    while L[k]>t:k+=1
    return rs[k-1]+(L[k-1]-t)/max(L[k-1]-L[k],1e-6)*step
def inner_edge(s,th,r0,z,step=0.05,thr=170,run=2.0):
    rs=np.arange(r0,r0-50,-step);L,ok=ray_profile(s,th,rs,z)
    if not ok[0]:return None
    nrun=int(run/step);below=L<thr;j=None
    for i in range(len(rs)-nrun):
        if not ok[i+nrun]:return None
        if below[i:i+nrun].all():j=i;break
    if j is None or j<int(3/step):return None
    hi=np.median(L[j-int(3/step):j]);lo=np.median(L[j+int(1/step):j+int(4/step)])
    if hi-lo<25:return None
    t=(hi+lo)/2;k=j-int(1.5/step)
    while L[k]>t:k+=1
    return rs[k-1]-(L[k-1]-t)/max(L[k-1]-L[k],1e-6)*step
