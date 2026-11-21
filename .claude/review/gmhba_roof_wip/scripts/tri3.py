import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R
exec(open('tri.py').read().split('def tri')[0])
q=np.load('cam_tlj.npy');FT={'30':(30,15)}
def PT(fr,X):
    h,pt=FT[fr];M=R.from_rotvec(q[2:5]).as_matrix()@R.from_euler('ZYX',np.radians([-h,-pt,0])).as_matrix()
    c=M.T@(X-np.array([q[0],q[1],2.6]));return np.array([400-q[5]*c[1]/c[0],300-q[5]*c[2]/c[0]])
obs=[('B',(815,254)),('C',(673.3,262.7)),('T30',(291,323))]
def r(X):return np.concatenate([(PT('30',X) if k=='T30' else P90(k,X))-np.array(uv) for k,uv in obs])
s=least_squares(r,np.array([-124,17,18.]));X=s.x
print('signTL',X.round(2),'res',np.abs(r(X)).reshape(-1,2).round(1).tolist())
C1=p[:3];C3=np.array([q[0],q[1],2.6])
a,b=X-C1,X-C3;print('angle p90 vs tlj',round(np.degrees(np.arccos(a@b/np.linalg.norm(a)/np.linalg.norm(b))),1))
