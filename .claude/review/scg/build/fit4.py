import numpy as np,json,math
from scipy.optimize import least_squares
exec(open('cam.py').read())
HEAD={'A':(396,45),'B':(869,30),'C':(982,88),'D':(892,478),'E':(410,483)}
BASE={'D':(872,638)}
SHAFT={'A':[(405,100),(418,190)],'B':[(865,60),(858,130)],'C':[(975,130),(966,200)],'D':[(885,530),(875,620)],'E':[(420,530),(430,610)],'F':[(170,360),(200,460)]}
order=['F','A','B','C','D','E'];lab={order[i]:TN[i] for i in range(6)}
GR=np.load('grass.npy').astype(float)
pitch=dens(G['4000006']);pitch=np.c_[pitch,np.zeros(len(pitch))]
T0=np.array([TOW[lab[k]] for k in order])
obs=[(order.index(k),1,v) for k,v in HEAD.items()]+[(order.index(k),0,v) for k,v in BASE.items()]
def unpack(q):return q[:10],T0+q[10:].reshape(6,2)
def res(q,wprior=1.0):
    p,T=unpack(q);r=[]
    for i,hd,v in obs:r+=list(proj(p,[(*T[i],p[9]*hd)])[0]-np.array(v))
    for k,L in SHAFT.items():
        i=order.index(k);a,b=proj(p,[(*T[i],0),(*T[i],p[9])]);t=(b-a)/np.linalg.norm(b-a);nrm=np.array([-t[1],t[0]])
        for v in L:r.append(float((np.array(v)-a)@nrm))
    pp=proj(p,pitch);dd=np.sqrt(((GR[:,None,:]-pp[None])**2).sum(-1)).min(1)
    return np.concatenate([r,dd*0.7,(q[10:])*wprior])
p0=json.load(open('cam2.json'))['p']
q0=np.r_[p0,np.zeros(12)]
lo=[-3e3,-3e3,50,-10,-1.5,-0.4,300,200,0,30]+[-15]*12;hi=[3e3,3e3,2e3,10,-0.05,0.4,4000,1000,700,95]+[15]*12
s=least_squares(res,q0,bounds=(lo,hi))
r=s.fun;n=2*len(obs)+12;print('tower rms',round(math.sqrt((r[:n]**2).mean()),1),'grass rms',round(math.sqrt((r[n:n+len(GR)]**2).mean()/0.49),1))
print(np.round(r[:n]));p,T=unpack(s.x);print('tower shifts m',np.round(s.x[10:].reshape(6,2),1))
print([round(v,3) for v in p])
json.dump({'p':list(p),'T':T.tolist(),'order':order},open('cam.json','w'))
