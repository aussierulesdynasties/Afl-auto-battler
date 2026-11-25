import json,math,numpy as np,sys
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/optus');import shape as S
from scipy.spatial.transform import Rotation as Rr
F=360/math.tan(math.radians(25.58/2))
cams=json.load(open('obl/cams.json'));jobs={j['name']:j for j in json.load(open('fjobs.json'))}
def proj(c,t,X):
    c=np.array(c);z=np.array(t)-c;z/=np.linalg.norm(z);x=np.cross(z,[0,0,1.0]);x/=np.linalg.norm(x);y=np.cross(z,x)
    q=X-c;return 640+F*(q@x)/(q@z),360+F*(q@y)/(q@z)
out={};meta=[]
for comp in range(214,304,3):
    a=(90-comp)%360;vn='f%03d'%(int(round(a/30.0))*30%360)
    th=math.radians(a);E=S.edge_xy(th);N=S.edge_normal(th)
    for HH in (12.0,20.0):
     for d in np.arange(2,26,2.0):
        X=np.array([E[0]+N[0]*d,E[1]+N[1]*d,HH]);u,v=proj(cams[vn]['cam'],cams[vn]['tgt'],X)
        if 5<u<1275 and 40<v<715:
            out.setdefault(vn,[]).append([int(round(u)),int(round(v))]);meta.append([vn,len(out[vn])-1,comp,float(d),HH])
J=[dict(name='w'+k[1:],url=jobs[k]['url'],pts=v) for k,v in out.items()]
json.dump(J,open('west_jobs.json','w'));json.dump(meta,open('west_meta.json','w'))
print({j['name']:len(j['pts']) for j in J},sum(len(j['pts']) for j in J))
