import json, sys, numpy as np
from PIL import Image
from scipy import ndimage
from skimage import feature, color
P='D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto/'
rgb=np.asarray(Image.open(P+'data/optus/sat_hi_south.png').convert('RGB'))
lab=color.rgb2lab(rgb); E=np.zeros(lab.shape[:2],bool)
for c in range(3): E|=feature.canny(ndimage.median_filter(lab[...,c],9),sigma=3,low_threshold=None)
dt=ndimage.distance_transform_edt(~E)*0.125
H,W=E.shape; S=json.load(open(P+(sys.argv[1] if len(sys.argv)>1 else 'spec/optus_fc_hand.json')))['south']
allv=[]
for i,p in enumerate(S):
    pts=np.array(p['pts'],float); d=[]
    for a,b in zip(pts,np.roll(pts,-1,0)):
        L=np.hypot(*(b-a))
        for t in np.arange(0,L,0.5):
            q=a+(b-a)*t/max(L,1e-6); c,r=(q[0]-90)/0.125,(-15-q[1])/0.125
            if 2<c<W-2 and 2<r<H-2: d.append(dt[int(r),int(c)])
    allv+=d; print(i,p['kind'],len(d),round(float(np.percentile(d,90)),2))
print('ALL p90',round(float(np.percentile(allv,90)),2))
Image.fromarray((E*255).astype(np.uint8)).save(P+'_canny.png')
