# w04 camera: brackets at bay joints (s=kL/7), plinth base line (t=pl_t,z=0) with free s, column verticals
import json,numpy as np,cv2,stand
from scipy.optimize import least_squares
W=stand.W;L=stand.L;w,h=1280,720
br=[(3,585,57),(4,755,77),(5,920,92),(6,1075,107),(7,1225,135)]
gnd=[(500,585),(1100,585),(700,585)]
cols=[(632,330,400),(795,330,470)]  # x, y_top, y_bot of a vertical edge
zb=float(stand.P['zF'])
def K(f):return np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
def res(q):
    f=q[0];rv=q[1:4];tv=q[4:7];ss=q[7:10];cs=q[10:12]
    r=[]
    X=np.array([W(k*L/7,0.0,zb) for k,_,_ in br]);U=np.array([[u,v] for _,u,v in br])
    r+=list((cv2.projectPoints(X,rv,tv,K(f),None)[0][:,0]-U).ravel())
    X=np.array([W(s,0.6,0) for s in ss]);U=np.array(gnd,float)
    r+=list((cv2.projectPoints(X,rv,tv,K(f),None)[0][:,0]-U).ravel())
    for (x,y0,y1),s in zip(cols,cs):
        X=np.array([W(s,5.0,3.0),W(s,5.0,6.0)]);P=cv2.projectPoints(X,rv,tv,K(f),None)[0][:,0]
        # vertical line through P0,P1 must pass x at y0,y1
        for y in (y0,y1):
            tt=(y-P[0,1])/(P[1,1]-P[0,1]+1e-9);r.append(P[0,0]+tt*(P[1,0]-P[0,0])-x)
    return np.array(r)
best=None
for f in np.geomspace(700,8000,30):
    X=np.array([W(k*L/7,0.0,zb) for k,_,_ in br]+[W(12,0.6,0),W(27,0.6,0),W(18,0.6,0)]);U=np.array([[u,v] for _,u,v in br]+gnd,float)
    ok,rv,tv=cv2.solvePnP(X,U,K(f),None,flags=cv2.SOLVEPNP_SQPNP)
    q0=np.r_[f,rv.ravel(),tv.ravel(),12,27,18,14,18]
    q=least_squares(res,q0).x;e=np.sqrt((res(q)**2).mean())
    if best is None or e<best[0]:best=(e,q)
e,q=best;R=cv2.Rodrigues(q[1:4])[0];C=-R.T@q[4:7]
print('f %.0f rms %.2f cam %s ground s %s col s %s'%(q[0],e,C.round(2),q[7:10].round(2),q[10:12].round(2)));print(res(q).round(1))
json.dump(dict(f=q[0],r=q[1:4].tolist(),t=q[4:7].tolist(),w=w,h=h),open('cam_w04b.json','w'))
