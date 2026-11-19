# top-down check: along lines straight out from the fence, where does the bright roof band start/end in the satellite vs the
# straight-down render. Satellite and render share a frame (north.json fit), 0.25 m/px, image centre = (0,0).
import json,numpy as np,sys
from PIL import Image
exec(open('fence.py',encoding='utf-8').read().split("#MAIN")[0])
NJ=json.load(open('north.json'));th=NJ['th'];c,s_=np.cos(th),np.sin(th)
S=np.asarray(Image.open(sys.argv[1]).convert('L'),float);T=np.asarray(Image.open('out/top.png').convert('LA'),float)
def px(p):q=p-PC;x=c*q[:,0]-s_*q[:,1]+NJ['tx'];y=s_*q[:,0]+c*q[:,1]+NJ['ty'];return np.c_[1000+x/0.25,1000-y/0.25]
D=np.arange(0,70,0.25);thr=float(sys.argv[2]) if len(sys.argv)>2 else 170
def band(v):
    from scipy.ndimage import median_filter
    b=median_filter(v>thr,9);i=np.nonzero(b)[0]
    return (D[i[0]],D[i[-1]]) if len(i) else None
for s in np.arange(float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5])):
    P_=np.array([P([s],d,0)[0,:2] for d in D]);q=px(P_).round().astype(int)
    ok=(q[:,0]>=0)&(q[:,0]<2000)&(q[:,1]>=0)&(q[:,1]<2000);q=np.clip(q,0,1999)
    vs=S[q[:,1],q[:,0]];vt=T[q[:,1],q[:,0],0]*(T[q[:,1],q[:,0],1]>128)
    print('s%5.1f sat %s  model %s'%(s,band(vs),band(vt)))
