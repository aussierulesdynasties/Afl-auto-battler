# python work/hgt.py view ubase vbase vtop [vtop2 ...] : base on z=0 (or env Z0), heights of points straight above
import sys,os,numpy as np;sys.path.insert(0,'work');import tri,earthcam as E
v=sys.argv[1];u,vb=float(sys.argv[2]),float(sys.argv[3]);z0=float(os.environ.get('Z0',0))
B=tri.onz(v,u,vb,z0);c=tri.camv(v);print('base',B.round(1))
for vt in sys.argv[4:]:
    vt=float(vt);zs=np.arange(z0,90,0.05);vv=[E.proj(c,[B[0],B[1],z])[1] for z in zs]
    print('v',vt,'z',round(float(zs[np.argmin(np.abs(np.array(vv)-vt))]),1))
