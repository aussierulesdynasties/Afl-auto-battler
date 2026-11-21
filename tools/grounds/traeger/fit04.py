# w04 camera with free box ends. obs: box corners (s0/s1 free), roof N tip, fascia low-edge points on the front plane line
import json,numpy as np,cv2
from scipy.optimize import least_squares
import stand
P=stand.P;L=stand.L;W=stand.W;w,h=1280,720
def K(f):return np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
def pr(q,X):return cv2.projectPoints(np.array(X,np.float64),q[1:4],q[4:7],K(q[0]),None)[0][:,0]
box=[(0,1,(312,108)),(1,1,(986,171)),(1,0,(986,301)),(0,0,(312,259))]
tip=(1235,136)
def res(q):
    s0,s1=q[7],q[8];r=[]
    for e,top,uv in box:
        X=W(s1 if e else s0,P['box_t0'],P['box_z1'] if top else P['box_z0']);r+=list(pr(q,[X])[0]-uv)
    r+=list(pr(q,[W(L,0,stand.roof_z(L,0))])[0]-tip)
    sp=q[9]
    r+=list(pr(q,[W(sp,P['pl_t'],P['pl_z'])])[0]-(1165,490));r+=list(pr(q,[W(sp,P['pl_t'],0)])[0]-(1165,585))
    R=cv2.Rodrigues(q[1:4])[0];C=-R.T@q[4:7];r+=[(C[2]-1.6)*20]
    return np.array(r)
c=json.load(open('cam_w04.json'));q0=np.r_[c['f'],c['r'],c['t'],2.8,26.9,28.3]
q=least_squares(res,q0).x;rr=res(q)[:-1].reshape(-1,2)
print('f %.0f s0 %.2f s1 %.2f spl %.2f'%(q[0],q[7],q[8],q[9]),'rms',np.sqrt((rr**2).sum(1).mean()).round(2));print(rr.round(1))
R=cv2.Rodrigues(q[1:4])[0];C=-R.T@q[4:7];print('cam pos',C.round(1),'dist to box mid',np.linalg.norm(C-np.array(W(15,4.8,8))).round(1))
json.dump(dict(f=q[0],r=q[1:4].tolist(),t=q[4:7].tolist(),w=w,h=h,box_s0=q[7],box_s1=q[8]),open('cam_w04.json','w'))
