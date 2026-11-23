import json,math,numpy as np,re
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rr
F=360/math.tan(math.radians(25.58/2))
LAT0,LON0=-31.95115518870997,115.88899235343283;X0,Y0=-30.38,-8.78
def ll2m(lat,lon):return X0+(lon-LON0)*111320*math.cos(math.radians(LAT0)),Y0+(lat-LAT0)*110574
import sys
JF,PF,OF=(sys.argv[1:4] if len(sys.argv)>3 else ('fjobs.json','fac_pts.json','obl/cams.json'))
P=json.load(open(PF));jobs=json.load(open(JF))
def proj(p,X):
    c=p[:3];R=Rr.from_rotvec(p[3:6]).as_matrix()   # R: world->cam (x right, y down, z fwd)
    q=(X-c)@R.T;return np.stack([640+F*q[:,0]/q[:,2],360+F*q[:,1]/q[:,2]],1)
out={}
for j in jobs:
    nm=j['name'];m=re.search(r'@([-\d.]+),([-\d.]+),([\d.]+)a,([\d.]+)d,35y,([\d.]+)h,([\d.]+)t',j['url'])
    lat,lon,a,d,h,t=map(float,m.groups());lx,ly=ll2m(lat,lon);lz=a-5
    hd=math.radians(h);tl=math.radians(t);fw=np.array([math.sin(hd)*math.sin(tl),math.cos(hd)*math.sin(tl),-math.cos(tl)])
    c0=np.array([lx,ly,lz])-fw*d
    z=fw;x=np.cross(z,[0,0,1.0]);x/=np.linalg.norm(x);y=np.cross(z,x);R0=np.stack([x,y,z])
    uv=[];XX=[]
    if not any(k.startswith(nm+'_') and v for k,v in P.items()):continue
    for k,v in P.items():
        if v and k.startswith(nm+'_'):uv.append(v[:2]);XX.append(v[2:5])
    uv=np.array(uv,float);XX=np.array(XX,float)
    p0=np.r_[c0,Rr.from_matrix(R0).as_rotvec()]
    f=lambda p:(proj(p,XX)-uv).ravel()
    r=least_squares(f,p0,loss='soft_l1',f_scale=3)
    res=np.hypot(*(proj(r.x,XX)-uv).T);Rm=Rr.from_rotvec(r.x[3:]).as_matrix()
    fwd=Rm[2];right=Rm[0];roll=math.degrees(math.asin(-right[2]))
    tgt=r.x[:3]+fwd*100
    out[nm]=dict(cam=r.x[:3].tolist(),tgt=tgt.tolist(),roll=roll,n=len(uv),med=float(np.median(res)),p90=float(np.percentile(res,90)),dc=float(np.linalg.norm(r.x[:3]-c0)))
    print(nm,len(uv),'med px %.1f p90 %.1f roll %.2f cam %s moved %.1f'%(out[nm]['med'],out[nm]['p90'],roll,np.round(r.x[:3],1),out[nm]['dc']))
json.dump(out,open(OF,'w'),indent=1)
