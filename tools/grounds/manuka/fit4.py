import numpy as np,math,json
exec(open('fitcam.py').read().split("def res(")[0])
from scipy.optimize import least_squares
keep=[i for i in range(len(GR)) if i not in(5,10)];GR=GR[keep]
MA0=MA.copy();PC=np.array([4.7,-5.0])
def neck(b,Hn,al):
    inw=(PC-b)/np.linalg.norm(PC-b);return np.array([b[0]+inw[0]*Hn*math.sin(al),b[1]+inw[1]*Hn*math.sin(al),Hn*math.cos(al)])
def res4(q,PP=True):
    p=q[:10];Hn,al=q[10],q[11];off=q[12:].reshape(6,2);MA=MA0+off;r=[]
    for k,(nk,lo) in OBS.items():
        b=MA[k];a=proj(p,[neck(b,Hn,al)])[0];bb=proj(p,[(b[0],b[1],0)])[0]
        r+=list(a-nk);d=bb-a;n=np.array([-d[1],d[0]])/np.linalg.norm(d);r.append(float((np.array(lo)-a)@n))
    pp=proj(p,pitch);dd=np.sqrt(((GR[:,None,:]-pp[None])**2).sum(-1)).min(1)
    pri=[(p[7]-960)/100,(p[8]-640)/100] if PP else []
    return np.concatenate([r,dd,off.ravel()*2.0,pri])
p0=np.array(json.load(open('cam2.json'))['p'])
best=None
for al in(0,0.05,0.1,0.15):
  for f in(2500,4600):
    q0=np.concatenate([p0[:6],[f,960,640,35,al],np.zeros(12)])
    q0=np.concatenate([q0[:9],q0[9:]])
    q0=np.concatenate([p0[:6],[f,960,640],[0],[35,al],np.zeros(12)])  # p[9] unused
    s=least_squares(res4,q0)
    if best is None or s.cost<best.cost:best=s
q=best.x;r=res4(q)
print('mast rms',round(math.sqrt((r[:18]**2).mean()),2),'grass rms',round(math.sqrt((r[18:33]**2).mean()),2))
print('cam',[round(v,3) for v in q[:9]],'neck H',round(q[10],1),'lean deg',round(math.degrees(q[11]),1))
print('off',np.round(q[12:].reshape(6,2),1));print(np.round(r[:18].reshape(6,3),1));print(np.round(r[18:33],1))
json.dump({'q':list(q)},open('cam4.json','w'))
