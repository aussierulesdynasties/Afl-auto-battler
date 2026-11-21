# height from aerial pixel + satellite reading taken at z=38: python tri.py u38 v38 px py
import sys;from sf import *
from scipy.optimize import brentq
K=np.array([-6.94,-2.2])/38.0
p=P('c5.json')
def at(u38,v38,z):
    s,t=st(u38,v38)+K*(38-z);return proj(p,[wld(s,t,z)])[0]
def solve(u,v,px,py):
    zs=np.arange(0,80,0.25);e=[np.hypot(*(at(u,v,z)-[px,py])) for z in zs];i=int(np.argmin(e));return zs[i],e[i],at(u,v,zs[i])
if __name__=='__main__':
    a=list(map(float,sys.argv[1:]))
    for j in range(0,len(a),4):
        z,e,q=solve(*a[j:j+4]);print(a[j:j+4],'z=%.2f err=%.1fpx'%(z,e),q.round(1))
