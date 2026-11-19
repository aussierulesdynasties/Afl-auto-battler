import numpy as np,sys,os,json
from PIL import Image
from scipy import ndimage as nd
W=sys.argv[1];os.chdir(W);exec(open('fence.py',encoding='utf-8').read().split("#MAIN")[0])
os.chdir(sys.argv[2])
a=np.asarray(Image.open('sat.jpg').convert('RGB'),float);r,g,b=a[...,0],a[...,1],a[...,2]
m=(g>r+12)&(g>b+12)&(g>60)
m=nd.binary_opening(m,iterations=3);lab,n=nd.label(m);c=lab[1000,1000];m=nd.binary_fill_holes(lab==c)
Image.fromarray((m*255).astype(np.uint8)).save('grass.png')
e=m^nd.binary_erosion(m);py,px=np.nonzero(e);S=np.c_[(px-1000)*0.25,-(py-1000)*0.25]
print('grass area m2',m.sum()*0.0625,'edge pts',len(S),'extent x',S[:,0].min(),S[:,0].max(),'y',S[:,1].min(),S[:,1].max())
M=F(np.arange(0,PER,1.0));print('model fence extent',M[:,0].min(),M[:,0].max(),M[:,1].min(),M[:,1].max(),'PER',PER)
from scipy.spatial import cKDTree
T=cKDTree(S)
def tf(p,th,tx,ty,sc=1):c,s_=np.cos(th),np.sin(th);q=(p-PC)*sc;return np.c_[c*q[:,0]-s_*q[:,1],s_*q[:,0]+c*q[:,1]]+[tx,ty]
best=None
for th0 in np.radians(np.arange(0,360,5)):
    th,tx,ty=th0,S[:,0].mean(),S[:,1].mean()
    for it in range(40):
        Q=tf(M,th,tx,ty);d,i=T.query(Q);P_=S[i]
        A=Q-Q.mean(0);B=P_-P_.mean(0);U,_,Vt=np.linalg.svd(A.T@B);Rm=(U@Vt).T
        if np.linalg.det(Rm)<0:continue
        dth=np.arctan2(Rm[1,0],Rm[0,0]);th+=dth;Q2=tf(M,th,tx,ty);sh=(P_.mean(0)-Q2.mean(0));tx+=sh[0];ty+=sh[1]
    d,_=T.query(tf(M,th,tx,ty))
    if best is None or d.mean()<best[0]:best=(d.mean(),th,tx,ty,np.percentile(d,95),d.max())
print('best rigid: mean %.2f m  p95 %.2f  max %.2f  rot %.1f deg  t %.1f %.1f'%(best[0],best[4],best[5],np.degrees(best[1]),best[2],best[3]))
json.dump(dict(th=best[1],tx=best[2],ty=best[3],PC=list(map(float,PC))),open('fit.json','w'))
# per-s offset (signed: + = sat grass edge outside model fence)
Q=tf(M,best[1],best[2],best[3]);ctr=np.array([best[2],best[3]])
for s0 in range(0,int(PER),20):
    q=Q[s0];d,i=T.query(q);sg=np.sign(np.dot(S[i]-q,q-ctr));print('s%3d  %+.1f'%(s0,sg*d),end='  ')
print()
