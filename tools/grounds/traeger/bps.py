# back-project w04 pixels to a plane s=const (stand frame): python bps.py cam.json s "u,v ..." -> t,z
import sys,json,numpy as np,cv2,stand
c=json.load(open(sys.argv[1]));s=float(sys.argv[2])
K=np.array([[c['f'],0,c['w']/2],[0,c['f'],c['h']/2],[0,0,1.]]);R=cv2.Rodrigues(np.array(c['r']))[0];T=np.array(c['t']);C=-R.T@T
O=np.r_[stand.O,0];a=np.r_[stand.a,0];b=np.r_[stand.b,0]
p0=O+s*a
for tok in sys.argv[3].split():
    u,v=map(float,tok.split(','));d=R.T@np.linalg.inv(K)@np.array([u,v,1.])
    lam=((p0-C)@a)/(d@a);X=C+lam*d
    print(tok,'t %.2f z %.2f'%((X-O)@b,X[2]))
