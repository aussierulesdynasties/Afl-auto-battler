import numpy as np,json,math
from scipy.optimize import least_squares
G=json.load(open('osm/geo.json'))
T={'E':G['towers'][0],'S':G['towers'][1],'W':G['towers'][2],'N':G['towers'][3]}
# photo (head centre, base)
P={'S':((1211,155),(1203,314)),'E':((561,320),(580,483)),'W':((1630,543),(1593,727)),'N':((757,810),(777,1000))}
W,H=1936,1290
def R(yaw,pt,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pt),math.sin(pt);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X,cx=W/2,cy=H/2):
    C=p[:3];M=R(*p[3:6]);fo=p[6];d=(np.atleast_2d(X)-C)@M.T
    return np.stack([cx+fo*d[:,0]/d[:,2],cy-fo*d[:,1]/d[:,2]],1)
def res(p):
    r=[]
    for k,(hd,bs) in P.items():
        x,y=T[k];q=proj(p,np.array([[x,y,p[7]],[x,y,0]]))
        r+=list(q[0]-hd)+list(q[1]-bs)
    return np.array(r)
if __name__=='__main__':
    best=None
    for yaw0 in np.radians(np.arange(0,360,30)):
        for pit in(-0.6,-0.9,-1.2):
            d=np.array([math.cos(yaw0),math.sin(yaw0)])
            p0=[20-d[0]*600,30-d[1]*600,700,yaw0,pit,0,2500,50]
            try:s=least_squares(res,p0,bounds=([-5e3,-5e3,50,-20,-1.57,-0.5,300,10],[5e3,5e3,5e3,20,0,0.5,2e4,120]))
            except Exception as e:continue
            if best is None or s.cost<best.cost:best=s
    s=best;p=s.x
    print('rms',round(math.sqrt((s.fun**2).mean()),2),[round(v,3) for v in p]);print(np.round(s.fun.reshape(-1,2),1))
    print('cam bearing deg from north',round((90-math.degrees(p[3]))%360,1),'pitch',round(math.degrees(p[4]),1),'tower h',round(p[7],1))
    json.dump({'p':list(p)},open('cam.json','w'))
