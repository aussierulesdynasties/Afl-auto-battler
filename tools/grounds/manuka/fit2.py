import numpy as np,math,json
exec(open('fitcam.py').read().split("if __name__")[0])
from scipy.optimize import least_squares
keep=[i for i in range(len(GR)) if i not in(5,10)];GR=GR[keep]
MA0=MA.copy()
def unpack(q):
    p=np.concatenate([q[:7],[960,640],q[7:8]]);off=q[8:].reshape(6,2);return p,off
def res3(q):
    global MA
    p,off=unpack(q);MA=MA0+off;r=res(p)
    return np.concatenate([r,(off.ravel())*2.0])
p0=np.array(json.load(open('cam_c.json'))['p'])
q0=np.concatenate([p0[:7],[p0[9]],np.zeros(12)])
s=least_squares(res3,q0)
p,off=unpack(s.x);MA=MA0+off;r=res(p)
print('mast rms',round(math.sqrt((r[:18]**2).mean()),2),'grass rms',round(math.sqrt((r[18:]**2).mean()),2))
print([round(v,3) for v in p]);print('offsets m',np.round(off,1));print(np.round(r[18:],1))
json.dump({'p':list(p),'masts':MA.tolist()},open('cam2.json','w'))
