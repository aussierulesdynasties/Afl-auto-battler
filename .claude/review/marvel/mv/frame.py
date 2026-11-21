from cam2 import *
c=np.array(HH['c']);L=np.array(HH['L']);Rr=np.array(HH['R']);ZR=HH['zr']
D=(Rr-L)/np.linalg.norm(Rr-L);N=np.array([-D[1],D[0]])
if (np.array(P[:2])-c)@N<0:N=-N
def loc(X):X=np.atleast_2d(X);return np.stack([(X[:,:2]-c)@D,(X[:,:2]-c)@N],1)
def wld(s,t,z=0):return np.array([*(c+s*D+t*N),z])
def bp(u,v,z):return loc(at_z(P,u,v,z))[0]   # mu.png pixel -> local (s,t) at height z
