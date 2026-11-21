import numpy as np,math,json
from scipy.optimize import least_squares
G=json.load(open('osm/geo.json'))['geo'];poly=np.array(G['242194673'])
P=np.array(json.load(open('bnd_m.json')))
# densify OSM polygon
d=[]
for i in range(len(poly)-1):
    for t in np.linspace(0,1,20,endpoint=False):d.append(poly[i]*(1-t)+poly[i+1]*t)
D=np.array(d)
def tf(s,X):
    c,sn=math.cos(s[0]),math.sin(s[0]);return X@np.array([[c,sn],[-sn,c]])+s[1:3]
def res(s):
    Q=tf(s,P);return np.sqrt(((Q[:,None]-D[None])**2).sum(-1)).min(1)
best=None
for a in np.radians(range(-180,180,15)):
    r=least_squares(res,[a,0,0],loss='soft_l1',f_scale=3)
    m=np.median(r.fun)
    if best is None or m<best[0]:best=(m,r)
m,r=best;print('rot deg',math.degrees(r.x[0]),'t',r.x[1:],'median',m);print(np.round(r.fun,1))
json.dump({'s':list(r.x)},open('align.json','w'))
