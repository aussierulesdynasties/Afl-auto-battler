import numpy as np,json,math
from scipy.optimize import least_squares
G=json.load(open('osm/geo.json'))
MA=np.array(G['masts'])  # order: A NE, B E, C SSE, D SW, E W, F NNW (as in OSM)
# photo mast -> OSM index: M4=A M5=B M6=C M2=D M1=E M3=F
OBS={0:((1775,357),(1798,585)),1:((1619.5,628),(1640.5,933)),2:((825,802),(830.5,996)),3:((105,505),(103,714)),4:((424,257),(422,415)),5:((1071.7,188.3),(1075,340))}
GR=np.array([(348,756),(367,706),(401,650),(470,600),(570,562),(695,537),(725,498),(850,471),(1050,452),(1433,471),(1540,493),(1570,667),(1517,740),(1430,807),(1363,847),(1200,907),(1000,930),(800,940),(700,933)],float)
pitch=np.array([(x,y,0) for x,y in G['pitch']],float)
pd=[]
for i in range(len(pitch)-1):
    for t in np.linspace(0,1,6,endpoint=False):pd.append(pitch[i]*(1-t)+pitch[i+1]*t)
pitch=np.array(pd)
W,H=1920,1280
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    C=p[:3];M=R(*p[3:6]);fo=p[6];d=(np.atleast_2d(X)-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def res(p,detail=False):
    r=[]
    for k,(nk,lo) in OBS.items():
        x,y=MA[k];a=proj(p,[(x,y,p[9])])[0];b=proj(p,[(x,y,0)])[0]
        r+=list(a-nk)
        d=b-a;n=np.array([-d[1],d[0]])/np.linalg.norm(d);r.append(float((np.array(lo)-a)@n))
    pp=proj(p,pitch);dd=np.sqrt(((GR[:,None,:]-pp[None])**2).sum(-1)).min(1)
    return np.concatenate([r,dd])
if __name__=='__main__':
    best=None
    for yaw in np.radians(np.arange(60,180,15)):
        for dist in(350,500,700):
            for el in(0.4,0.6):
                C=[-math.cos(yaw)*dist*math.cos(el),-math.sin(yaw)*dist*math.cos(el),dist*math.sin(el)]
                p0=C+[yaw,-el,0,1800,960,640,40]
                try:s=least_squares(res,p0,bounds=([-3e3]*2+[20,-10,-1.5,-0.5,300,600,300,15],[3e3]*2+[3e3,10,0.2,0.5,9000,1300,1000,90]))
                except Exception:continue
                if best is None or s.cost<best.cost:best=s
    r=best.fun;p=best.x
    print('mast rms',round(math.sqrt((r[:18]**2).mean()),2),'grass rms',round(math.sqrt((r[18:]**2).mean()),2))
    print([round(v,3) for v in p]);print(np.round(r[:18].reshape(6,3),1));print(np.round(r[18:],1))
    json.dump({'p':list(p)},open('cam.json','w'))
