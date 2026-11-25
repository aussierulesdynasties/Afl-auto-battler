# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, math, cv2
C=json.load(open('cal.json')); S,DX,DY=C['s'],C['dx'],C['dy']
IMS=[(cv2.GaussianBlur(cv2.imread('ge/'+n+'.png').min(2).astype(float),(0,0),1.2),sh) for n,sh in (('top3000',0.0),('topN',60.0),('topS',-60.0))]
def sample(e,n):
    vals=[]
    for g,sh in IMS:
        x=640+(e-DX)/S; y=360-(n-DY-sh)/S
        if 2<=x<1277 and 60<=y<717 and not (x>660 and y<55):
            vals.append(cv2.getRectSubPix(g.astype(np.float32),(1,1),(float(x),float(y)))[0,0])
    return np.mean(vals) if vals else np.nan
STEP=0.25
out={}
for b in np.arange(0,360,0.5):
    sb,cb=math.sin(math.radians(b)),math.cos(math.radians(b))
    rs=np.arange(55,175,STEP); L=np.array([sample(r*sb,r*cb) for r in rs])
    out[str(b)]=L.tolist()
json.dump({'rs':[55,175,STEP],'L':out},open('profiles.json','w'))
