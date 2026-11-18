import numpy as np,json
exec(open('cam.py').read())
c=json.load(open('cam7.json'));p=c['p']
def P2(X):return proj(p,np.array(X,float).reshape(-1,3))
def back(u,v,z):
    from scipy.optimize import least_squares
    s=least_squares(lambda a:P2([[a[0],a[1],z]])[0]-[u,v],[-120,40]);return s.x
