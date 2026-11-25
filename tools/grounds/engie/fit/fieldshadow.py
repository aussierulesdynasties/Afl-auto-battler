# The field edge where Google Earth has it in shadow (west and north): along each bearing, the step from the
# shaded turf to the brighter shaded apron, the first one going outward, searched 1 to 11 m inside the stand front. Writes field_shadow.json.
import cv2,numpy as np,json,math
from scipy.ndimage import gaussian_filter1d
C=json.load(open('cal.json')); S,DX,DY=C['s'],C['dx'],C['dy']
im=cv2.imread('ge/top3000.png').astype(np.float32)
import os
sfj=[p for p in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','model','engie.json')))['stand_front']
     if not 5<=p[0]<=75]   # the stand front (comp_rings.py; it does not depend on the field), the open end left out
sb,sr=np.array(sfj).T
def sfr(b): return float(np.interp(b%360,np.r_[sb-360,sb,sb+360],np.r_[sr,sr,sr]))
def px(e,n): return 640+(e-DX)/S, 360-(n-DY)/S
out=[]
for b in np.arange(195,385,0.5):
    s0=sfr(b); rs=np.arange(s0-12,s0+0.01,0.1); L=[]
    for r in rs:
        e,n=r*math.sin(math.radians(b)),r*math.cos(math.radians(b)); x,y=px(e,n)
        B,G,R=cv2.getRectSubPix(im,(3,3),(x,y)).mean((0,1)); L.append((B+G+R)/3)
    L=gaussian_filter1d(np.array(L),3)
    # the first step outward from the turf: the mean over the next 1.5 m beats the 2 m before it by 4 or more
    best=None
    for i in range(20,len(rs)-15):
        if not (s0-11<=rs[i]<=s0-1): continue
        if L[i-20:i].mean()<85 and L[i:i+15].mean()-L[i-20:i].mean()>=4.0:
            j=i-5+int(np.argmax(np.gradient(L)[i-5:i+6])); best=(rs[j],L[j:j+15].mean()-L[j-20:j].mean()); break
    if best: out.append([float(b%360),float(best[0]),float(best[1])])
json.dump(out,open('field_shadow.json','w')); print(len(out),'points of',len(np.arange(195,385,0.5)))
