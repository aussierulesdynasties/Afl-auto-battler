import numpy as np,json
import roofbp as RB
P=np.load('polar.npy');deg=RB.deg
H=np.arange(14,40,1.0);E={0:[],1:[]}
for w in (0,1):
    for h in H:E[w].append(RB.edges(h,w))
    E[w]=np.array(E[w])
G=json.load(open('geo_build.json'));rin=np.array(G['rin']);rout=np.array(G['rout'])
out={}
for w,ref in ((0,rin),(1,rout)):
    hs=[]
    for a in range(0,1440,8):
        e=E[w][:,a]
        if np.isnan(e).all() or np.isnan(ref[a]):hs.append(np.nan);continue
        err=np.abs(e-ref[a]);err[np.isnan(err)]=99;k=np.argmin(err);hs.append(H[k] if err[k]<3 else np.nan)
    out[w]=hs
for i,a in enumerate(range(0,1440,8)):
    d=a/4
    if (d>=104 or d<=37):print(d,out[0][i],out[1][i])
