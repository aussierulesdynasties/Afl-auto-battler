# back-project pixels to a stand plane t=const: python bp.py cam.json t "u,v u,v ..."  -> s,z
import sys,json,numpy as np,cv2,stand
c=json.load(open(sys.argv[1]));t=float(sys.argv[2])
K=np.array([[c['f'],0,c['w']/2],[0,c['f'],c['h']/2],[0,0,1.]]);R=cv2.Rodrigues(np.array(c['r']))[0];T=np.array(c['t']);C=-R.T@T
O=np.r_[stand.O,0];a=np.r_[stand.a,0];b=np.r_[stand.b,0]
n=b;p0=O+t*b
for tok in sys.argv[3].split():
    u,v=map(float,tok.split(','));d=R.T@np.linalg.inv(K)@np.array([u,v,1.])
    lam=((p0-C)@n)/(d@n);X=C+lam*d;s=(X-O)@a
    print(tok,'s %.2f z %.2f'%(s,X[2]))
