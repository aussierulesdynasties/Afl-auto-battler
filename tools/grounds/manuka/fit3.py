import numpy as np,math,json
exec(open('fitcam.py').read().split("if __name__")[0])
from scipy.optimize import least_squares
keep=[i for i in range(len(GR)) if i not in(5,10)];GR=GR[keep]
MA0=MA.copy()
def unpack(q):return q[:10],q[10:].reshape(6,2)
def res3(q):
    global MA
    p,off=unpack(q);MA=MA0+off;return np.concatenate([res(p),off.ravel()*2.0])
best=None
p0=np.array(json.load(open('cam2.json'))['p'])
for cy in(200,400,640,900):
  for f in(2000,3000,4600):
    q0=np.concatenate([p0[:6],[f,960,cy,p0[9]],np.zeros(12)])
    s=least_squares(res3,q0,bounds=([-3e3,-3e3,20,-10,-1.5,-.5,500,0,-1500,15]+[-20]*12,[3e3,3e3,3e3,10,.2,.5,9000,1920,2800,90]+[20]*12))
    if best is None or s.cost<best.cost:best=s
p,off=unpack(best.x);MA=MA0+off;r=res(p)
print('mast rms',round(math.sqrt((r[:18]**2).mean()),2),'grass rms',round(math.sqrt((r[18:]**2).mean()),2))
print([round(v,3) for v in p]);print('offsets m',np.round(off,1));print(np.round(r[:18].reshape(6,3),1));print(np.round(r[18:],1))
json.dump({'p':list(p),'masts':MA.tolist()},open('cam3.json','w'))
