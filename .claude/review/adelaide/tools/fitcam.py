import numpy as np,json,math,itertools,sys
from scipy.optimize import least_squares
G=json.load(open('osm/geo.json'))
TW={t[0]:np.array(t[1:3]) for t in G['towers']}
OT=[9961520695,9961520696,9961520697,9961520698]
pitch=np.array(G['ways']['4681536']);pd=[]
for i in range(len(pitch)-1):
    for t in np.linspace(0,1,6,endpoint=False):pd.append(pitch[i]*(1-t)+pitch[i+1]*t)
PIT=np.c_[np.array(pd),np.zeros(len(pd))]
W,H=1811,1257
# photo towers: base px (or None), shaft px list
PT={'A':((97,968),[(97,700),(97,850)]),'B':(None,[(751,520),(751,610)]),'C':((1462,838),[(1463,600),(1463,750)]),'D':((690,1030),[(689,800),(688,900)])}
GR=np.array([(410,955),(480,907),(550,875),(630,855),(675,845),(760,822),(850,812),(950,806),(1050,806),(1110,810)],float)
def R(yaw,pt,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pt),math.sin(pt);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    X=np.atleast_2d(X);C=p[:3];M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def linedist(a,b,q):
    d=b-a;n=np.array([-d[1],d[0]])/np.linalg.norm(d);return (q-a)@n
def res(p,lab):
    out=[]
    for k,(base,sh) in PT.items():
        t=TW[lab[k]];a,b=proj(p,np.array([[t[0],t[1],0],[t[0],t[1],60]]))
        if base:out+=list(proj(p,np.array([t[0],t[1],0]))[0]-base)
        for q in sh:out.append(linedist(a,b,np.array(q,float)))
    pp=proj(p,PIT);dd=np.sqrt(((GR[:,None,:]-pp[None])**2).sum(-1)).min(1)
    return np.array(out+list(dd))
if __name__=='__main__':
    best=[]
    for perm in itertools.permutations(OT):
        lab=dict(zip('ABCD',perm))
        for yaw0 in np.radians(np.arange(0,360,30)):
            fwd=np.array([math.cos(yaw0),math.sin(yaw0)])
            C0=-fwd*600
            p0=[C0[0],C0[1],350,yaw0,-0.5,0,1800,W/2,H/2]
            try:s=least_squares(res,p0,args=(lab,),bounds=([-5e3,-5e3,30,-20,-1.5,-0.3,300,0,-800],[5e3,5e3,3000,20,0.2,0.3,20000,W,H+800]))
            except Exception as e:continue
            rms=math.sqrt((s.fun**2).mean());best.append((rms,perm,list(s.x)))
    best.sort(key=lambda z:z[0])
    for b in best[:6]:print(round(b[0],2),[str(x)[-2:] for x in b[1]],[round(v,2) for v in b[2]])
    b=best[0];json.dump({'p':b[2],'lab':dict(zip('ABCD',b[1]))},open('cam.json','w'))
    print(np.round(res(np.array(b[2]),dict(zip('ABCD',b[1]))),1))
