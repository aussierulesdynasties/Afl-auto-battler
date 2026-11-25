# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, math, cv2
import os; ENGIE_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'engie.json')
from scipy.optimize import least_squares
S=0.3640   # m/px, from the 60 m shifted shots
IM={'c':(cv2.imread('ge/top3000.png'),0.0),'N':(cv2.imread('ge/topN.png'),60.0),'S':(cv2.imread('ge/topS.png'),-60.0)}
D=json.load(open(ENGIE_JSON))
def per(t,q):
    t=np.array(sorted(t),float); return np.interp(np.asarray(q)%360,np.r_[t[:,0]-360,t[:,0],t[:,0]+360],np.r_[t[:,1],t[:,1],t[:,1]])
# translation: fit field grass edge (sunlit E/S) to the OSM fence shape scaled by k (k free: OSM size is under test)
f=np.load('field.npy').astype(np.uint8)
cs,_=cv2.findContours(f,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=len)[:,0,:].astype(float)
bear=np.degrees(np.arctan2(c[:,0]-640,-(c[:,1]-360)))%360; sel=c[(bear>25)&(bear<190)]
bb=np.linspace(0,360,3600,endpoint=False); fr=per(D['fence'],bb)
def res(p):
    k,dx,dy=p; e=(sel[:,0]-640)*S+dx; n=-(sel[:,1]-360)*S+dy
    Px=k*fr*np.sin(np.radians(bb)); Py=k*fr*np.cos(np.radians(bb))
    return np.sqrt(((e[:,None]-Px)**2+(n[:,None]-Py)**2).min(1))
r=least_squares(res,[1,0,0]); k,DX,DY=r.x
print('OSM fence scale vs GE grass edge k=%.4f dx=%.2f dy=%.2f rms %.2f m'%(k,DX,DY,np.sqrt((r.fun**2).mean())))
json.dump({'s':S,'dx':DX,'dy':DY,'osm_k':k},open('cal.json','w'))
