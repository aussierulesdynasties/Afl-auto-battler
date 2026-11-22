import json, numpy as np
from PIL import Image
from scipy import ndimage
P='D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto/'
im=np.asarray(Image.open(P+'data/optus/sat_hi_south.png').convert('L'),float)
g=ndimage.gaussian_filter(ndimage.median_filter(im,15),3); gm=np.hypot(ndimage.sobel(g,1),ndimage.sobel(g,0))
H,W=im.shape; S=json.load(open(P+'spec/optus_fc_hand.json'))['south']
def px(x,y): return (x-90)/0.125, (-15-y)/0.125
res={}
for i,p in enumerate(S):
    pts=np.array(p['pts'],float); d=[]
    for a,b in zip(pts,np.roll(pts,-1,0)):
        L=np.hypot(*(b-a)); n=np.array([-(b-a)[1],(b-a)[0]])/max(L,1e-6)
        for t in np.arange(0.5,L,1.0):
            q=a+(b-a)*t/L; off=np.arange(-2,2.01,0.125); best=None
            vals=[]
            for o in off:
                c,r=px(*(q+n*o))
                if 0<=c<W-1 and 0<=r<H-1: vals.append(gm[int(r),int(c)])
                else: vals.append(-1)
            vals=np.array(vals)
            if vals.max()>40: d.append(abs(off[vals.argmax()]))
    if d: res[f"{i}:{p.get('kind')}"]=(len(d),round(float(np.percentile(d,90)),2))
for k,v in res.items(): print(k,v)
