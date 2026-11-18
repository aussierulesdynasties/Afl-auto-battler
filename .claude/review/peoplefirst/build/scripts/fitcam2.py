import numpy as np,json,math
from scipy.optimize import least_squares
from fitcam import X,Y,GW,GP,R,proj,W,Hh
TW=[((654,488),(648,200)),((330,783),(312,450)),((1340,1043),(1333,693))]
nt=len(TW)
def unpack(q):return q[:7],q[7:7+3*nt].reshape(nt,3)
def res(q):
    p,T=unpack(q)
    r1=(proj(p,X)-Y).ravel()
    pp=proj(p,GW);dd=np.sqrt(((GP[:,None,:]-pp[None])**2).sum(-1)).min(1)
    rt=[]
    for (b,t),(x,y,h) in zip(TW,T):
        rt+=list(proj(p,np.array([[x,y,0.0]]))[0]-b)+list(proj(p,np.array([[x,y,h]]))[0]-t)
    return np.concatenate([r1,dd*0.7,np.array(rt)*1.5])
if __name__=='__main__':
    best=None
    for p0 in ([-998,-77,650,0.068,-0.562,0.013,6243],[-500,-100,300,0.2,-0.5,0,3000],[-700,-80,450,0.1,-0.55,0,4500],[-1500,-60,1000,0.05,-0.56,0,9000]):
        T0=[(92,68,66),(-22,116,73),(-89,-77,74)]
        s=least_squares(res,np.concatenate([p0,np.array(T0,float).ravel()]))
        print(round(s.cost,1),round(s.x[6]))
        if best is None or s.cost<best.cost:best=s
    s=best;r=s.fun;n=2*len(X);ng=len(GP)
    print('pt rms',round(math.sqrt((r[:n]**2).mean()),1),'grass rms',round(math.sqrt(((r[n:n+ng]/0.7)**2).mean()),1),'tower rms',round(math.sqrt(((r[n+ng:]/1.5)**2).mean()),1))
    p,T=unpack(s.x);print(np.round(p,3));print(np.round(T,1));print(np.round(r[n+ng:]/1.5,1))
    json.dump({'p':list(p)},open('cam.json','w'))
