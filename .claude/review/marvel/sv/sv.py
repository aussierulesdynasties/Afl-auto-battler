# Street View helpers: local frame <-> lat/lon, panorama stitching, candidate points around the outline.
import sys,json,math,io,os,urllib.request
import numpy as np
MV=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','mv');sys.path.insert(0,MV)
cwd=os.getcwd();os.chdir(MV)
from frame import *
os.chdir(cwd)
LA0,LO0=-37.816495302702705,144.9475565216216;K=111320.0;KC=K*math.cos(math.radians(LA0));KL=110574.0
def ll(s,t):x,y=wld(s,t)[:2];return LA0+y/KL,LO0+x/KC
def st(la,lo):return loc(np.array([[(lo-LO0)*KC,(la-LA0)*KL,0]]))[0]
def fetch(pid,zoom=4,out=None):
    from PIL import Image
    nx,ny=2**zoom,2**(zoom-1);im=Image.new('RGB',(512*nx,512*ny))
    for y in range(ny):
        for x in range(nx):
            u='https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv.tactile&panoid=%s&x=%d&y=%d&zoom=%d&nbt=1&fover=2'%(pid,x,y,zoom)
            import subprocess,time
            for k in range(5):
                r=subprocess.run(['curl','-s','-f','-A','stadium-ref/1.0',u],capture_output=True).stdout
                if r:break
                time.sleep(1+k)
            im.paste(Image.open(io.BytesIO(r)),(512*x,512*y))
    im.save(out or pid+'.jpg',quality=93);return im
if __name__=='__main__':
    if sys.argv[1]=='cands':
        G=json.load(open(os.path.join(MV,'osm/geo.json'),encoding='utf-8'));a=np.array(G['ways']['22971441'])
        q=loc(np.c_[a,np.zeros(len(a))])[:-1];ctr=q.mean(0);out=[]
        for i in range(len(q)):
            p,n=q[i],q[(i+1)%len(q)];m=(p+n)/2;d=n-p;nm=np.array([d[1],-d[0]])/np.linalg.norm(d)
            if nm@(m-ctr)<0:nm=-nm
            if m[1]<40 or m[0]<-90:   # north end and east side
                la,lo=ll(*(m+nm*float(sys.argv[2])));out.append((i,round(la,6),round(lo,6)))
        print(json.dumps(out))
    elif sys.argv[1]=='fetch':fetch(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 4)
