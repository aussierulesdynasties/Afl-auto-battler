# camsolve.py : solve the camera of a ground-level photo from the far fence line (traced), a tower head and shaft
import json,sys,numpy as np
from scipy.optimize import least_squares
C=json.load(open('/home/user/Afl-auto-battler/tools/grounds/legacy/subiaco/measure/fence_fit.json'))['c']
def fr(a):
    t=np.radians(a);v=C[0]+0*t
    for k in range(1,11): v=v+C[2*k-1]*np.cos(k*t)+C[2*k]*np.sin(k*t)
    return v
def fpt(a,z=0.0):
    r=fr(a);t=np.radians(a);return np.stack([r*np.cos(t),r*np.sin(t),np.full_like(t,z)],-1)
def px2m(px,py): return np.array([(px-941)*0.2945,-(py-1021)*0.2945])
TW={'NW':px2m(751.3,725.7),'NE':px2m(1136.2,733.0),'SW':px2m(780,1330),'SE':px2m(1150,1335)}
def Rm(yaw,pitch,roll):
    # camera: forward along yaw (deg from east ccw), pitch up +, roll
    y,p,r=np.radians([yaw,pitch,roll])
    f=np.array([np.cos(p)*np.cos(y),np.cos(p)*np.sin(y),np.sin(p)])
    right=np.array([np.sin(y),-np.cos(y),0.0]); up=np.cross(right,f)
    rr=np.cos(r)*right+np.sin(r)*up; uu=-np.sin(r)*right+np.cos(r)*up
    return f,rr,uu
def campos(q):
    th,d,hc=q[:3]; p=fpt(np.array([th]))[0]; rad=p[:2]/np.linalg.norm(p[:2])
    return np.array([p[0]+d*rad[0],p[1]+d*rad[1],hc])
W,H=1920,1440
def proj(q,P):
    c=campos(q); f,rr,uu=Rm(*q[3:6]); F=q[6]
    v=P-c; z=v@f; x=(v@rr)/z; y=(v@uu)/z
    k1=q[8] if len(q)>8 else 0.0
    if k1: s=1+k1*(x*x+y*y)*(F/1200.0)**2; x=x*s; y=y*s
    return np.stack([W/2+F*x, H/2-F*y],-1), z
far=np.load('/home/user/work/subi/z/so_farfence.npy')
def resid(q,tw,head,shaft,wf=1.0):
    c=campos(q)
    a=np.linspace(0,360,3601)[:-1]; P=fpt(a); uv,z=proj(q,P)
    # far side branch: points farther than 60 m from camera and in front
    dist=np.linalg.norm(P[:,:2]-c[:2],axis=1); m=(z>0)&(dist>60)
    u=uv[m,0];v=uv[m,1];o=np.argsort(u);u,v=u[o],v[o]
    if len(u)<10 or u.min()>far[:,0].min() or u.max()<far[:,0].max(): return np.full(len(far)+3,500.0)
    r1=(far[:,1]-np.interp(far[:,0],u,v))*wf/ np.sqrt(len(far)/20)
    b=TW[tw]; ht=proj(q,np.array([[b[0],b[1],65.0]]))[0][0]
    l0=proj(q,np.array([[b[0],b[1],0.0],[b[0],b[1],60.0]]))[0]
    d=l0[1]-l0[0]; n=np.array([-d[1],d[0]])/np.linalg.norm(d); r3=(np.array(shaft)-l0[0])@n
    return np.concatenate([r1,ht-np.array(head),[r3]])
if __name__=='__main__':
    head=(1057,86); shaft=(1060,560)
    best=None
    for tw in TW:
      for th0 in range(0,360,15):
        for F0 in (1200,1600,2200):
          b=TW[tw]; p=fpt(np.array([th0]))[0]; yaw0=np.degrees(np.arctan2(b[1]-p[1],b[0]-p[0]))
          q0=[th0,3,3,yaw0,0,0,F0]
          try: s=least_squares(resid,q0,args=(tw,head,shaft),bounds=([-720,0.5,0.8,-720,-30,-10,600],[720,25,25,720,30,10,6000]))
          except Exception: continue
          if best is None or s.cost<best[0]: best=(s.cost,tw,s.x)
          
    print(best); c,tw,q=best; r=resid(q,tw,head,shaft); print('far rms px',np.sqrt((r[:-3]**2).mean()*len(far)/20/len(far)*1), 'head',r[-3:-1],'shaft',r[-1])
    np.save('cam_so.npy',np.concatenate([[list(TW).index(tw)],q]))
