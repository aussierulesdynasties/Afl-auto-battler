import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.optimize import least_squares
p=np.load('cam_p90.npy');hp=np.load('cam_svw.npy');f95=1280/2/np.tan(np.radians(37.5))
HP={'A':(90,8),'B':(125,8),'C':(145,8)}
def P90(fr,X):
    h,pt=HP[fr];M=(R.from_rotvec(p[3:6])*R.from_euler('ZYX',[np.radians(-h),np.radians(-pt),0])).as_matrix()
    c=M.T@(X-p[:3]);return np.array([640-p[6]*c[1]/c[0],292.5-p[6]*c[2]/c[0]])
M95=R.from_euler('ZYX',hp[3:]).as_matrix()
def P95(X):c=M95.T@(X-hp[:3]);return np.array([640-f95*c[1]/c[0],292.5-f95*c[2]/c[0]])
def tri(obs,X0):
    def r(X):return np.concatenate([(P95(X) if fr=='h95' else P90(fr,X))-uv for fr,uv in obs])
    s=least_squares(r,X0);return s.x,r(s.x).reshape(-1,2)
import sys
