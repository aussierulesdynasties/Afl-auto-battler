# back-project pixels onto a stand-frame plane: python bpp.py cam.json t=0.6|s=-1.0 u,v u,v ...  -> s,t,z
import sys,json,numpy as np,cv2
import stand
c=json.load(open(sys.argv[1]));R=cv2.Rodrigues(np.array(c['r']))[0];t=np.array(c['t']);C=-R.T@t
K=np.array([[c['f'],0,c['w']/2],[0,c['f'],c['h']/2],[0,0,1]])
O=np.r_[stand.O,0];a=np.r_[stand.a,0];b=np.r_[stand.b,0];zz=np.array([0,0,1.])
ax,val=sys.argv[2].split('=');val=float(val)
for uv in sys.argv[3:]:
    u,v=map(float,uv.split(','));d=R.T@np.linalg.inv(K)@[u,v,1]
    n=a if ax=='s' else (b if ax=='t' else zz);p0=O+(a if ax=='s' else b if ax=='t' else zz)*val
    lam=((p0-C)@n)/(d@n);X=C+lam*d;rel=X-O
    print(uv,'s=%.2f t=%.2f z=%.2f'%(rel@a,rel@b,X[2]))
