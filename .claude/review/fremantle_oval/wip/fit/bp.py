import numpy as np, json, sys
sys.path.insert(0,'fit'); from cam import *
from scipy.optimize import least_squares
C={k: json.load(open(f'fit/{f}')) for k,f in (('a02','cam_a02s0.json'),('g34','cam_g34h.json'))}
def pr(k,X): c=C[k]; return proj(c['p'],np.array([X],float),c['W']/2,c['H']/2)[0]
def back(k,u,v,z,x0=(-25,-95)):
    r=least_squares(lambda xy: pr(k,[xy[0],xy[1],z])-[u,v],x0); return np.array([*r.x,z])
