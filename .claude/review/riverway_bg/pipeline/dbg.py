import numpy as np, math, json
poly=np.array([p for k,p in json.load(open('spec/peoplefirst.json'))['paint_poly'] if k=='paved'][0],float)
def _dens(P, step):
    Q = [P[0]]
    for p2 in P[1:]:
        k = max(1, int(math.ceil(np.hypot(*(p2 - Q[-1])) / step))); a = Q[-1]
        for j in range(1, k + 1): Q.append(a + (p2 - a) * (j / k))
    return np.array(Q)
x0,y0=np.floor(poly.min(0))
E=_dens(np.vstack([poly,poly[:1]]),0.25)
edge=set(zip((np.floor(E[:,0])-x0).astype(int),(np.floor(E[:,1])-y0).astype(int)))
for cx in (83,87): print(cx, (cx-x0, -47-y0) in edge, (cx-x0,-46-y0) in edge, [ (int(i+x0),int(j+y0)) for i,j in edge if i+x0==cx])
