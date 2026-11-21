import json, numpy as np
from PIL import Image
from scipy import ndimage
P='D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto/'
im=np.asarray(Image.open(P+'data/optus/sat_hi_south.png').convert('L'),float)
g=ndimage.gaussian_filter(ndimage.median_filter(im,15),3); gm=np.hypot(ndimage.sobel(g,1),ndimage.sobel(g,0))
H,W=im.shape; J=json.load(open(P+'spec/optus_fc_hand.json'))
def gv(x,y):
    c,r=(x-90)/0.125,(-15-y)/0.125
    return gm[int(r),int(c)] if 0<=c<W-1 and 0<=r<H-1 else -1
off=np.arange(-3,3.01,0.125)
def prof(q,n): return np.array([gv(*(q+n*o)) for o in off])
for p in J['south']:
    pts=np.array(p['pts'],float); D=[]
    for a,b in zip(pts,np.roll(pts,-1,0)):
        L=np.hypot(*(b-a)); k=max(2,int(L)); 
        for t in np.linspace(0,1,k,endpoint=False): D.append(a+(b-a)*t)
    D=np.array(D); N=len(D)
    tg=np.roll(D,-1,0)-np.roll(D,1,0); nn=np.stack([-tg[:,1],tg[:,0]],1); nn/=np.linalg.norm(nn,axis=1,keepdims=True)+1e-9
    o=np.zeros(N); ok=np.zeros(N,bool)
    for i in range(N):
        v=prof(D[i],nn[i]); w=v*np.exp(-(off/2.5)**2)
        if v.max()>40: o[i]=off[w.argmax()]; ok[i]=True
    o=np.where(ok,o,np.nan)
    sm=np.array([np.nanmedian(np.take(o,range(i-3,i+4),mode='wrap')) if np.isfinite(np.take(o,range(i-3,i+4),mode='wrap')).any() else 0 for i in range(N)])
    p['pts']=np.round(D+nn*sm[:,None],2).tolist()
json.dump(J,open(P+'spec/optus_fc_hand.json','w'),indent=1)
print('snapped')
