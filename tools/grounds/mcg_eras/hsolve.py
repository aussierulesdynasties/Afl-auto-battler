# Height of the roof front above the turf, from where its shadow falls on the turf.
import numpy as np
def load(fn):
    a=np.loadtxt(fn); a=a[~np.isnan(a[:,1])]; return a
def solve(F,S,az,e,bear):
    """F,S: arrays (bearing,r). Returns h for the roof-front point at each bearing in bear."""
    d=np.array([np.sin(np.radians(az+180)),np.cos(np.radians(az+180))]); t=1/np.tan(np.radians(e))
    Sb=np.unwrap(np.radians(S[:,0])); Sr=S[:,1]
    out=[]
    for b in bear:
        r=np.interp(b,F[:,0],F[:,1]); P=r*np.array([np.sin(np.radians(b)),np.cos(np.radians(b))])
        best=None
        for h in np.arange(0,70,0.05):
            Q=P+h*t*d; bq=np.arctan2(Q[0],Q[1]); bq=Sb[0]+((bq-Sb[0])%(2*np.pi))
            if bq>Sb[-1]: continue
            rs=np.interp(bq,Sb,Sr); rq=np.hypot(*Q)
            if rq<=rs: best=h; break
        out.append((b,r,best,np.degrees(bq)%360))
    return out
