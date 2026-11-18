import numpy as np,json,math
exec(open('cam.py').read())
_c=json.load(open('cam.json'));p=np.array(_c['p']);TW=np.array(_c['T']);C=p[:3];M=R(*p[3:6]);fo=p[6];cx0,cy0=p[7],p[8]
def ray(u,v):
    d=np.array([(u-cx0)/fo,-(v-cy0)/fo,1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(u,v,z=0.0):
    w=ray(u,v);t=(z-C[2])/w[2];return C+t*w
def height(base,top):
    b=at_z(*base,0.0);w=ray(*top)
    A=np.array([[w[0]],[w[1]]]);rhs=np.array([b[0]-C[0],b[1]-C[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0]
    return b,(C+t*w)[2]
def pr(X):return proj(p,X)
PIT=np.array(G['4000006']);PC=PIT[:-1].mean(0)
def polar(poly,n=720):
    P=np.array(poly,float)-PC;out=np.full((n,2),np.nan)
    for i in range(n):
        a=2*math.pi*i/n;d=np.array([math.cos(a),math.sin(a)]);hits=[]
        for j in range(len(P)-1):
            A=P[j];B=P[j+1];Mx=np.array([d,A-B]).T
            if abs(np.linalg.det(Mx))<1e-9:continue
            t,s=np.linalg.solve(Mx,A)
            if t>0 and 0<=s<=1:hits.append(t)
        if hits:out[i]=(min(hits),max(hits))
    return out
def theta(xy):return math.atan2(xy[1]-PC[1],xy[0]-PC[0])
def rr(xy):return math.hypot(xy[0]-PC[0],xy[1]-PC[1])
