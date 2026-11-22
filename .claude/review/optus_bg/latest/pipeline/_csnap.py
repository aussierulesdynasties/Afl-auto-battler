import json, numpy as np
from PIL import Image
from scipy import ndimage
from skimage import color
P='D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto/'
lab=color.rgb2lab(np.asarray(Image.open(P+'data/optus/sat_hi_south.png').convert('RGB')))
lab=np.stack([ndimage.uniform_filter(lab[...,c],9) for c in range(3)],-1); H,W=lab.shape[:2]
def at(q):
    c,r=(q[0]-90)/0.125,(-15-q[1])/0.125
    return lab[int(r),int(c)] if 0<=c<W-1 and 0<=r<H-1 else None
offs=np.arange(-3,3.01,0.25)
J=json.load(open(P+'spec/optus_fc_hand.json'))
for it in range(3):
  for p in J['south']:
    D=np.array(p['pts'],float); N=len(D)
    tg=np.roll(D,-1,0)-np.roll(D,1,0); nn=np.stack([-tg[:,1],tg[:,0]],1); nn/=np.linalg.norm(nn,axis=1,keepdims=True)+1e-9
    o=np.full(N,np.nan)
    for i in range(N):
        best=(12,None)
        for of in offs:
            A=[at(D[i]+nn[i]*(of+s)) for s in (0.5,1,1.5)]; B=[at(D[i]+nn[i]*(of-s)) for s in (0.5,1,1.5)]
            if any(x is None for x in A+B): continue
            cd=np.linalg.norm(np.mean(A,0)-np.mean(B,0))
            if cd>best[0]: best=(cd,of)
        if best[1] is not None: o[i]=best[1]
    sm=np.array([np.nanmedian(w) if np.isfinite(w).any() else 0 for w in (np.take(o,range(i-4,i+5),mode='wrap') for i in range(N))])
    p['pts']=np.round(D+nn*sm[:,None]*0.7,2).tolist()
json.dump(J,open(P+'spec/optus_fc_hand.json','w'),indent=1); print('ok')
