# ptsolve.py : camera from known ground points (AFL goal posts, goal square) with free position
import numpy as np, itertools
from scipy.optimize import least_squares
W_,H_=1920,1440
def px2m(px,py): return np.array([(px-941)*0.2945,-(py-1021)*0.2945])
GW=px2m(644,1031.25); GE=px2m(1236,1014.5); u=(GE-GW)/np.linalg.norm(GE-GW); n=np.array([-u[1],u[0]])
def goal(end,flip):
    G=GW if end=='W' else GE; uin=u if end=='W' else -u; s=-1 if flip else 1
    P={'bA':G-9.6*n*s,'gA':G-3.2*n*s,'gB':G+3.2*n*s,'bB':G+9.6*n*s,'sqA':G+9*uin-3.2*n*s,'sqB':G+9*uin+3.2*n*s}
    return {k:np.array([v[0],v[1],0.0]) for k,v in P.items()}
def Rm(yaw,pitch,roll):
    y,p,r=np.radians([yaw,pitch,roll]); f=np.array([np.cos(p)*np.cos(y),np.cos(p)*np.sin(y),np.sin(p)])
    right=np.array([np.sin(y),-np.cos(y),0.0]); up=np.cross(right,f)
    return f,np.cos(r)*right+np.sin(r)*up,-np.sin(r)*right+np.cos(r)*up
def proj(q,P,W=W_,H=H_):
    c=q[:3]; f,rr,uu=Rm(*q[3:6]); F=q[6]; k1=q[7]
    v=np.atleast_2d(P)-c; z=v@f; x=(v@rr)/z; y=(v@uu)/z; s=1+k1*(x*x+y*y)*(F/1200.0)**2
    return np.stack([W/2+F*x*s,H/2-F*y*s],-1),z
def solve(obs,P3,extra=None,W=W_,H=H_):
    keys=list(obs); A=np.array([obs[k] for k in keys],float); B=np.array([P3[k] for k in keys])
    def r(q):
        uv,z=proj(q,B,W,H); out=[(uv-A).ravel()*1.0]
        if extra: out.append(extra(q))
        return np.concatenate(out)
    best=None
    cen=B.mean(0)
    for ang in range(0,360,30):
      for dist in (60,120):
        for hz in (15,30):
          c0=cen+np.array([dist*np.cos(np.radians(ang)),dist*np.sin(np.radians(ang)),hz])
          d=cen-c0; yaw=np.degrees(np.arctan2(d[1],d[0])); pit=np.degrees(np.arctan2(d[2],np.hypot(d[0],d[1])))
          for F0 in (1500,2500):
            try: s=least_squares(r,[*c0,yaw,pit,0,F0,0],bounds=([-300,-300,0.5,-1e3,-80,-20,500,-0.4],[300,300,80,1e3,40,20,8000,0.4]))
            except Exception: continue
            if best is None or s.cost<best.cost: best=s
    return best
if __name__=='__main__':
    obs={'bA':(1286.5,1092.5),'gA':(1495,1010),'gB':(1665,942.5),'bB':(1810,885),'sqA':(1170,917.5),'sqB':(1345,864)}
    for end in 'WE':
      for flip in (0,1):
        s=solve(obs,goal(end,flip)); res=s.fun.reshape(-1,2)
        print(end,flip,'rms %.2f px'%np.sqrt((res**2).sum(1).mean()),np.round(s.x,2))
