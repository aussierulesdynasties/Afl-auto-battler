# per imagery vintage: fit the model fence to the ground-level oval edge, then read the Members roof band (s 432-478)
import numpy as np,sys,os,json
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial import cKDTree
W=sys.argv[1];here=os.getcwd();os.chdir(W);exec(open('fence.py',encoding='utf-8').read().split("#MAIN")[0]);os.chdir(here)
M=F(np.arange(0,PER,1.0))
def tf(p,th,tx,ty):c,s_=np.cos(th),np.sin(th);q=p-PC;return np.c_[c*q[:,0]-s_*q[:,1],s_*q[:,0]+c*q[:,1]]+[tx,ty]
for f in sys.argv[2:]:
    a=np.asarray(Image.open(f).convert('RGB'),float);r,g,b=a[...,0],a[...,1],a[...,2]
    m=(g>r+12)&(g>b+12)&(g>60);m=nd.binary_opening(m,iterations=3);lab,n=nd.label(m);m=nd.binary_fill_holes(lab==lab[1000,1000])
    e=m^nd.binary_erosion(m);py,px=np.nonzero(e);S=np.c_[(px-1000)*0.25,-(py-1000)*0.25];T=cKDTree(S)
    best=None
    for th0 in np.radians(np.arange(-20,30,5)):
        th,tx,ty=th0,S[:,0].mean(),S[:,1].mean()
        for it in range(40):
            QQ=tf(M,th,tx,ty);_,i=T.query(QQ);P_=S[i];A=QQ-QQ.mean(0);B=P_-P_.mean(0);U,_,Vt=np.linalg.svd(A.T@B);Rm=(U@Vt).T
            th+=np.arctan2(Rm[1,0],Rm[0,0]);Q2=tf(M,th,tx,ty);sh=P_.mean(0)-Q2.mean(0);tx+=sh[0];ty+=sh[1]
        d,_=T.query(tf(M,th,tx,ty))
        if best is None or d.mean()<best[0]:best=(d.mean(),th,tx,ty)
    _,th,tx,ty=best;L=np.asarray(Image.open(f).convert('L'),float);D=np.arange(25,72,0.25);ins=[];outs=[]
    for s in np.arange(432,479,3.0):
        P_=np.array([P([s],d,0)[0,:2] for d in D]);q=tf(P_,th,tx,ty);q=np.clip(np.round(np.c_[1000+q[:,0]/0.25,1000-q[:,1]/0.25]).astype(int),0,1999)
        v=nd.median_filter(L[q[:,1],q[:,0]],5);hi=np.percentile(v,90);lo=np.percentile(v[D<34],50);t=(hi+lo)/2;i=np.nonzero(v>t)[0]
        if len(i):ins.append(D[i[0]])
        j=np.nonzero((v>t)&(D<60))[0]
        if len(j):outs.append(D[j[-1]])
    print('%s fit mean %.2f m rot %.2f deg | Members roof inner d %.1f (sd %.1f) outer d %.1f (sd %.1f)'%(f,best[0],np.degrees(th),np.median(ins),np.std(ins),np.median(outs),np.std(outs)))
