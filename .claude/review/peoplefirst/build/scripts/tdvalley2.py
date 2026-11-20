# Nearest distance from each model outer-edge valley point (top-down render) to the satellite's roof edge contour.
import sys,json,numpy as np,cv2
S=json.load(open('sat.json'));m=S['mpp'];W=1000
sat=cv2.imread('sat.png',0);x0,y0=int(round(S['px']-W/2)),int(round(S['py']-W/2));c=sat[y0:y0+W,x0:x0+W]
al=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED)[...,3]
def contour(mask):
    e=cv2.morphologyEx(mask.astype(np.uint8),cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0;return np.argwhere(e)
sm=cv2.morphologyEx((c>200).astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))>0
SE=contour(sm);ME=contour(al>128)
def pt(a,rlo,rhi):   # outermost model edge pixel along the ray, within the roof band
    t=np.radians(a);best=None
    for r in np.arange(rlo,rhi,0.05):
        u=int(round(W/2+r*np.cos(t)/m));v=int(round(W/2-r*np.sin(t)/m))
        if al[v,u]>128:best=(v,u)
    return best
for nm,angs in (('photo valleys (model V points)',[358.3,365.7,373.1,380.2,387.4,394.7]),):
    print(nm)
    for a in angs:
        p=pt(a,100,124);d=np.sqrt(((SE-np.array(p))**2).sum(1)).min()*m
        print(f'  {a:6.1f} deg  nearest satellite edge {d:4.2f} m')
