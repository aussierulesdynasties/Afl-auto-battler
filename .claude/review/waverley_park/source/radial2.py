import json,numpy as np,sys
from PIL import Image
exec(open('fence.py',encoding='utf-8').read().split("#MAIN")[0])
NJ=json.load(open('north.json'));th=NJ['th'];c,s_=np.cos(th),np.sin(th)
S=np.asarray(Image.open(sys.argv[1]).convert('L'),float);T=np.asarray(Image.open('out/top.png').convert('LA'),float)
def px(p):q=p-PC;x=c*q[:,0]-s_*q[:,1]+NJ['tx'];y=s_*q[:,0]+c*q[:,1]+NJ['ty'];return np.c_[1000+x/0.25,1000-y/0.25]
D=np.arange(0,80,2.0)
print('d     '+' '.join('%3d'%d for d in D))
for s in np.arange(float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])):
    P_=np.array([P([s],d,0)[0,:2] for d in D]);q=np.clip(px(P_).round().astype(int),0,1999)
    vs=S[q[:,1],q[:,0]];vt=np.where(T[q[:,1],q[:,0],1]>128,T[q[:,1],q[:,0],0],-1)
    print('s%3d S '%s+' '.join('%3d'%v for v in vs));print('     M '+' '.join(('%3d'%v if v>=0 else '  .') for v in vt))
