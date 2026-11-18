# Re-fit the 2019 aerial camera on ground points matched between mu.png and the 2026 satellite (ground is lean-free).
import sys,os,json;sys.path.insert(0,os.getcwd())
from frame import *
import cv2
from scipy.optimize import least_squares
ph=cv2.imread('mu.png');G=cv2.cvtColor(ph,cv2.COLOR_BGR2GRAY);Hh,Ww=G.shape
sat=cv2.imread('../sat/lplan_all_clean.png')
def rays(p,u,v):
    M=R(*p[3:6]);d=np.stack([(u-p[7])/p[6],-(v-p[8])/p[6],np.ones_like(u)],-1);return d@M
def warp(p,z):
    us,vs=np.meshgrid(np.arange(Ww,dtype=float),np.arange(Hh,dtype=float));w=rays(p,us,vs);C=np.array(p[:3])
    k=(z-C[2])/w[...,2];X=C+k[...,None]*w;X[k<0]=1e5
    st_=np.stack([(X[...,:2]-c)@D,(X[...,:2]-c)@N],-1)
    mx=((200-st_[...,1])/0.25).astype(np.float32);my=((st_[...,0]+200)/0.25).astype(np.float32)
    return cv2.remap(sat,mx,my,cv2.INTER_LINEAR,borderValue=(0,0,0)),st_
p0=list(P)
W0,ST=warp(p0,0.0);Wg=cv2.cvtColor(W0,cv2.COLOR_BGR2GRAY)
cv2.imwrite('../sat/w0_fast.jpg',cv2.addWeighted(ph,0.5,W0,0.5,0))
# ground-only mask: drawn polygon excluding the stadium building and tall towers (aerial pixels)
mask=np.zeros_like(G);cv2.fillPoly(mask,[np.array([[0,620],[300,560],[430,800],[1340,800],[1500,560],[1920,560],[1920,1080],[0,1080]])],255)
pairs=[];T=24;S=40
for v in range(80,Hh-80,30):
    for u in range(80,Ww-80,30):
        if mask[v,u]==0:continue
        a=G[v-T:v+T,u-T:u+T];b=Wg[v-T-S:v+T+S,u-T-S:u+T+S]
        if a.std()<12 or b.min()==0 and (b==0).mean()>0.05:continue
        r=cv2.matchTemplate(b,a,cv2.TM_CCOEFF_NORMED);_,mxv,_,loc_=cv2.minMaxLoc(r)
        if mxv<0.6:continue
        du,dv=loc_[0]-S,loc_[1]-S
        uu,vv=u+du,v+dv
        pairs.append((u,v,*ST[int(vv),int(uu)],mxv))
pairs=np.array(pairs);print('matches',len(pairs))
def res(q,pp):
    p=list(q[:7])+[960.,540.];X=np.array([wld(s,t,0) for s,t in pp[:,2:4]]);return (proj(p,X)-pp[:,:2]).ravel()
q0=np.array(p0[:7]);r0=res(q0,pairs).reshape(-1,2);print('before rms',np.sqrt((r0**2).sum(1).mean()))
fit=least_squares(res,q0,args=(pairs,),loss='huber',f_scale=4)
rr=fit.fun.reshape(-1,2);e=np.sqrt((rr**2).sum(1));keep=e<3*np.median(e)
fit=least_squares(res,fit.x,args=(pairs[keep],),loss='huber',f_scale=3)
rr=fit.fun.reshape(-1,2);print('after rms',np.sqrt((rr**2).sum(1).mean()),'n',keep.sum());print(list(fit.x))
np.save('recal_pairs.npy',pairs[keep]);json.dump(dict(p=list(fit.x)+[960.,540.]),open('c4.json','w'))
vis=ph.copy()
for (u,v,s,t,m) in pairs[keep]:
    q=proj(list(fit.x)+[960,540],[wld(s,t,0)])[0];cv2.circle(vis,(int(u),int(v)),3,(0,255,0),-1);cv2.line(vis,(int(u),int(v)),(int(q[0]),int(q[1])),(0,0,255),1)
cv2.imwrite('../sat/recal_vis.jpg',vis)
