# Height of each roof corner: walk up the vertical through its plan position (from the nadir views) in a solved oblique,
# and take the strongest brightness step (roof edge against fascia shadow or the car park behind).
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0,'of'); import zline as Z, solve as S
def run(view,corners,zr=(7,16)):
    p=np.array(Z.SOL[view]['p']); g=np.asarray(Image.open(f'of/ge/{view}.png').convert('L'),float); g=nd.gaussian_filter(g,1.0)
    out={}
    for c in corners:
        zs=np.arange(zr[0],zr[1],0.05); r=[]
        for dx in (-0.4,0,0.4):   # three parallel verticals around the corner (inward along nothing: plan jitter)
            P=np.array([[*Z.xy_at(c,z),z] for z in zs]); P[:,0]+=dx
            uv,_=S.proj(p,P); r.append(nd.map_coordinates(g,[uv[:,1],uv[:,0]],order=1))
        L=np.mean(r,0); dL=np.gradient(L,zs); k=np.argmax(np.abs(dL)); pxm=np.linalg.norm(uv[-1]-uv[0])/(zs[-1]-zs[0])
        out[c]=(round(float(zs[k]),2),round(float(dL[k]),1),round(float(pxm),1))
    return out
for v in sys.argv[1:]:
    print(v,run(v,['FL','FK','FR','RR','RK','B2','B1']))
