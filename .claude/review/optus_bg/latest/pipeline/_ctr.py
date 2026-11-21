import json, sys, numpy as np
from PIL import Image
from scipy import ndimage
from skimage import color
P='D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto/'
lab=color.rgb2lab(np.asarray(Image.open(P+'data/optus/sat_hi_south.png').convert('RGB')))
lab=np.stack([ndimage.uniform_filter(lab[...,c],9) for c in range(3)],-1)
H,W=lab.shape[:2]; S=json.load(open(P+(sys.argv[1] if len(sys.argv)>1 else 'spec/optus_fc_hand.json')))['south']
def at(q):
    c,r=(q[0]-90)/0.125,(-15-q[1])/0.125
    return lab[int(r),int(c)] if 0<=c<W-1 and 0<=r<H-1 else None
offs=np.arange(-3,3.01,0.25); allv=[]; snap=('--snap' in sys.argv); J=None
for i,p in enumerate(S):
    pts=np.array(p['pts'],float); d=[]
    for a,b in zip(pts,np.roll(pts,-1,0)):
        L=np.hypot(*(b-a)); n=np.array([-(b-a)[1],(b-a)[0]])/max(L,1e-6)
        for t in np.arange(0.25,L,1.0):
            q=a+(b-a)*t/max(L,1e-6); best=(0,None)
            for o in offs:
                A=[at(q+n*(o+s)) for s in (0.5,1.0,1.5)]; B=[at(q-n*(-o+s)) if False else at(q+n*(o-s)) for s in (0.5,1.0,1.5)]
                if any(x is None for x in A+B): continue
                cd=np.linalg.norm(np.mean(A,0)-np.mean(B,0))
                if cd>best[0]: best=(cd,o)
            if best[1] is not None and best[0]>12: d.append(abs(best[1]))
    if d: allv+=d; print(i,p['kind'],len(d),round(float(np.percentile(d,90)),2),round(float(np.median(d)),2))
print('ALL p90',round(float(np.percentile(allv,90)),2),'median',round(float(np.median(allv)),2),'n',len(allv))
