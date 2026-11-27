# p3.py : camera of AUSvIRE3 (International Rules, 2013/14) from the west goal posts, the SW tower shaft and the far fence
import sys,numpy as np
sys.path.insert(0,'/home/user/work/subi/photo')
from scipy.optimize import least_squares
from ptsolve import goal,Rm
from camsolve import fpt,TW
W,H=1920,1434
USE_TW=False
def cpos(q):
    p=fpt(np.array([q[0]]))[0];rad=p[:2]/np.linalg.norm(p[:2]);return np.array([p[0]+q[1]*rad[0],p[1]+q[1]*rad[1],q[2]])
def proj(q,P):
    c=cpos(q); f,rr,uu=Rm(*q[3:6]); F=q[6]; k1=q[7]
    v=np.atleast_2d(P)-c; z=v@f; x=(v@rr)/z; y=(v@uu)/z; s=1+k1*(x*x+y*y)*(F/1200.0)**2
    return np.stack([W/2+F*x*s,H/2-F*y*s],-1),z
def linedist(q,base,pts,h=8.0):
    l=proj(q,np.array([[base[0],base[1],0.0],[base[0],base[1],h]]))[0];d=l[1]-l[0];n=np.array([-d[1],d[0]])/np.linalg.norm(d)
    return (np.array(pts)-l[0])@n
FT=[(x,y) for x,y in [(710,568),(720,568),(730,568),(740,569),(750,565),(760,564),(770,564),(780,563),(790,564),(800,564),(810,564),(820,563),(860,557),(870,557),(880,557),(890,557),(910,556),(920,555),(940,555),(950,555),(980,555),(990,555),(1000,554),(1010,554),(1020,555),(1030,554),(1040,554),(1050,554),(1060,553),(1070,552),(1080,553),(1090,552),(1120,552),(1130,552),(1140,551),(1150,552),(1160,552),(1170,552),(1190,551),(1200,551),(1210,552),(1220,551),(1230,551),(1240,551)]]
FT=np.array(FT,float)
def resid(q,G,use_fence=True):
    out=[]
    uv,_=proj(q,np.array([G['bA'],G['gA']]));out.append((uv-np.array([[1282,554.5],[1356,554.5]])).ravel())
    out.append(linedist(q,G['bA'][:2],[(1282,500)]));out.append(linedist(q,G['gA'][:2],[(1356,500)]))
    out.append(linedist(q,G['gB'][:2],[(1434,500),(1434,530)]));out.append(linedist(q,G['bB'][:2],[(1514,500),(1514,530)]))
    if USE_TW: out.append(linedist(q,TW['SW'],[(602.5,40),(620.8,400)],60.0))
    if use_fence:
        a=np.linspace(0,360,7201)[:-1];P=fpt(a);uv,z=proj(q,P);c=cpos(q)
        dist=np.linalg.norm(P[:,:2]-c[:2],axis=1);m=(z>0)&(dist>80)
        u=uv[m,0];v=uv[m,1];o=np.argsort(u);u,v=u[o],v[o]
        if len(u)<10 or u.min()>FT[0,0] or u.max()<FT[-1,0]: out.append(np.full(len(FT),300.0))
        else: out.append((FT[:,1]-np.interp(FT[:,0],u,v))/np.sqrt(len(FT)/10))
    return np.concatenate(out)
if __name__=='__main__':
    best=None
    for flip in (0,1):
        G=goal('W',flip)
        for th in range(0,360,20):
            for d in (3,10,20):
                c0=cpos([th,d,3+d*0.4]);tgt=G['gA'];yaw=np.degrees(np.arctan2(tgt[1]-c0[1],tgt[0]-c0[0]))
                for F0 in (1500,2000):
                    try: s=least_squares(resid,[th,d,3+d*0.4,yaw,0,0,F0,0],args=(G,),bounds=([-720,0.3,0.8,-1e3,-30,-15,800,-0.3],[720,40,40,1e3,30,15,6000,0.3]))
                    except Exception as e: continue
                    if best is None or s.cost<best[0]: best=(s.cost,flip,s.x)
    c,flip,q=best;G=goal('W',flip);r=resid(q,G)
    print('flip',flip,'cost %.1f'%c,np.round(q,3));print('posts',np.round(r[:4],1),'lines',np.round(r[4:11],1),'fence rms %.2f px'%np.sqrt(((r[11:]*np.sqrt(len(FT)/10))**2).mean()))
    np.save('cam3.npy',np.concatenate([[flip],q]))
NEAR=np.array([(880,970),(980,959),(1080,944),(1180,932.5),(1280,918),(1380,906),(1480,892),(1580,881),(1742,851),(1780,846),(1820,836),(1920,820)],float)
def resid_n(q9,G):
    q=q9[:8];hr=q9[8];r=resid(q,G)
    a=np.linspace(0,360,7201)[:-1];P=fpt(a,hr);uv,z=proj(q,P);c=cpos(q)
    dist=np.linalg.norm(P[:,:2]-c[:2],axis=1);m=(z>0)&(dist<70)
    u=uv[m,0];v=uv[m,1];o=np.argsort(u);u,v=u[o],v[o]
    if len(u)<5 or u.min()>NEAR[0,0] or u.max()<NEAR[-1,0]: rn=np.full(len(NEAR),300.0)
    else: rn=NEAR[:,1]-np.interp(NEAR[:,0],u,v)
    return np.concatenate([r,rn/np.sqrt(len(NEAR)/6)])
