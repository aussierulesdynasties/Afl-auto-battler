import numpy as np,json,math
from scipy.optimize import least_squares
from camlib import *
W,H=1000,600;cx,cy=W/2,H/2
m=np.load('grassB.npy')
ED=[]
for x in range(285,786,4):
    ys=np.nonzero(m[:,x])[0]
    if len(ys):ED.append((x,ys.min()))
ED=np.array(ED,float)
a0=math.radians(172);U0=np.array([math.cos(a0),math.sin(a0)]);V0=np.array([-math.sin(a0),math.cos(a0)])
P0=PITCH-PITCH.mean(0);PN=np.c_[P0@U0/92.65,P0@V0/64.15];ext=PN[:,0].max()
JA=json.load(open('camA_final.json'));th,dx,dy,L,B=JA['ground']
a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)]);c=np.array([dx,dy])
def fence(mg):
    A=(L+mg)/ext;ov=np.outer(PN[:,0]*A,U)+np.outer(PN[:,1]*(B+mg),V)+c;return np.vstack([ov,ov[:1]])
POSTI=np.array([(352.5,220),(373.7,219),(392.5,218),(412.5,217)],float)
TW=[((133.3,130),(132.3,270)),((685,60),(678.8,170)),((883.3,180),(873.3,315)),((271,300),(267,500))]
def posts(s):
    g=c+s*L*U;return np.array([g+k*V for k in(-9.6,-3.2,3.2,9.6)])
def res(p,full=False):
    cam=p[:7];mg=p[7]
    r1=curve_d(ED,proj(cam,np.c_[fence(mg),np.zeros(len(fence(mg)))],cx,cy))
    best=None
    for s in(1,-1):
        q=proj(cam,np.c_[posts(s),np.zeros(4)],cx,cy);q=q[np.argsort(q[:,0])];d=(q-POSTI).ravel()
        if best is None or (d**2).sum()<(best**2).sum():best=d
    r4=[]
    for (t,l) in TW:
        X=at_z(cam,*l,cx,cy,0.0);q=proj(cam,np.array([X,X+[0,0,60]]),cx,cy);d=q[1]-q[0];d/=np.linalg.norm(d)
        v=np.array(t)-np.array(l);r4.append(d[0]*v[1]-d[1]*v[0])
    r4=np.array(r4)
    return (r1,best,r4) if full else np.concatenate([r1,best*3,r4*2,[(mg-6)*0.1]])
out=[]
for F in (6000,):
  best=None
  for yaw0 in (150,170,190,210):
    for pit in (-25,-35,-45):
      D=F*200/600;pr=math.radians(pit);yw=math.radians(yaw0)
      C=[-D*math.cos(pr)*math.cos(yw),-D*math.cos(pr)*math.sin(yw),-D*math.sin(pr)]
      p0=np.array(C+[yw,pr,0.0,F,6.0])
      try:sol=least_squares(lambda q:res(np.r_[q[:6],F,q[6]]),np.r_[p0[:6],p0[7]],loss='soft_l1',f_scale=2,max_nfev=600)
      except Exception as e:continue
      cst=(sol.fun**2).mean()
      if best is None or cst<best[0]:best=(cst,np.r_[sol.x[:6],F,sol.x[6]])
  r1,r2,r4=res(best[1],True);rm=lambda r:round(float(np.sqrt(np.median(np.square(r)))),2)
  p=best[1];print(F,'cost',round(best[0],2),'edge',rm(r1),'posts',rm(r2),'lean',np.round(r4,1),'C',np.round(p[:3]),'ypr',np.round(np.degrees(p[3:6]),1),'mg',round(p[7],1),flush=True)
  out.append((best[0],F,list(p)))
out.sort();c0,F,p=out[0]
json.dump({'p':p[:7]+[1.0],'W':W,'H':H,'mg':p[7],'note':'fitB: A ground, posts W end, fence = boundary+mg, tower leans'},open('camB.json','w'))
