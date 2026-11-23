import sys,json,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from ocr import read
from multiprocessing import Pool
LAT0,LON0=-31.95115518870997,115.88899235343283;X0,Y0=-30.38,-8.78
jobs,d,out=sys.argv[1:4]
J=json.load(open(jobs));old=json.load(open(out)) if os.path.exists(out) else {}
tasks=[]
for j in J:
    for i,(u,v) in enumerate(j['pts']):
        k='%s_%04d'%(j['name'],i);f=f'{d}/{k}.png'
        if k not in old and os.path.exists(f):tasks.append((k,f,u,v))
def go(t):
    k,f,u,v=t;r,_=read(f)
    if not r:return k,None
    lat,lon,h=r;return k,[u,v,X0+(lon-LON0)*111320*math.cos(math.radians(LAT0)),Y0+(lat-LAT0)*110574,h-5.0]
with Pool(3) as p:
    for k,v in p.imap_unordered(go,tasks):old[k]=v
json.dump(old,open(out,'w'));print(len(old),sum(v is None for v in old.values()))
