import numpy as np,json,math,sys
from scipy.optimize import least_squares
from camlib import *
W,H=1024,629;cx,cy=W/2,H/2
E=json.load(open('edgeC.json'))
GR=np.array([(x,y) for x,y,t in E if t=='t' and x<600],float)
GB=np.array([(x,y) for x,y,t in E if t=='b' and 300<x<690],float)
a0=math.radians(172);U0=np.array([math.cos(a0),math.sin(a0)]);V0=np.array([-math.sin(a0),math.cos(a0)])
P0=PITCH-PITCH.mean(0);PN=np.c_[P0@U0/92.65,P0@V0/64.15];ext=PN[:,0].max()
JA=json.load(open('camA_final.json'));th,dx,dy,L,B=JA['ground']
a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)]);c=np.array([dx,dy])
MG=2.355
def fence(mg):
    A=(L+mg)/ext;ov=np.outer(PN[:,0]*A,U)+np.outer(PN[:,1]*(B+mg),V)+c;return np.vstack([ov,ov[:1]])
FE=fence(MG);FE3=np.c_[FE,np.zeros(len(FE))]
RR=np.vstack([way(1430111014),way(951696127),way(1374562961),way(951696126)])
RRI=np.array([(497,553),(576,525),(655,497),(734,459),(813,421),(892,396),(971,371)],float)
POSTI=np.array([(755,246),(771.7,251),(788,253),(805,250)],float)
TWI=[((554.1,300),(563.1,465)),((914.3,180),(916.0,343)),((201.2,130),(213.0,252.5)),((510.2,40),(517.3,160))]
TOW=np.array(json.load(open('layoutB.json'))['TOW'])[:,:2]
def posts(s):
    g=c+s*L*U;return np.array([g+k*V for k in(-9.6,-3.2,3.2,9.6)])
def pld(q0,q1,p):
    d=q1-q0;d=d/np.linalg.norm(d);v=p-q0;return d[0]*v[1]-d[1]*v[0]
def res(p,full=False):
    cam=list(p[:7])
    po=proj(cam,FE3,cx,cy)
    r1=curve_d(GR,po)
    r3=curve_d(RRI,proj(cam,np.c_[RR,np.zeros(len(RR))],cx,cy))
    rb=[]
    for u,v in GB[::4]:
        m=np.abs(po[:,0]-u)<6
        rb.append(min(0.0,po[m,1].max()-v) if m.any() else 0.0)
    rb=np.array(rb)
    best=None
    for s in(1,-1):
        q=proj(cam,np.c_[posts(s),np.zeros(4)],cx,cy);q=q[np.argsort(q[:,0])];d=(q-POSTI).ravel()
        if best is None or (d**2).sum()<(best**2).sum():best=d
    r4=[]
    lines=[proj(cam,np.array([[*t,0],[*t,60]]),cx,cy) for t in TOW]
    for tp,lo in TWI:
        tp=np.array(tp);lo=np.array(lo)
        k=int(np.argmin([abs(pld(l[0],l[1],tp))+abs(pld(l[0],l[1],lo)) for l in lines]))
        l=lines[k];r4+=[pld(l[0],l[1],tp),pld(l[0],l[1],lo)]
    r4=np.array(r4)
    if full:return r1,r3,rb,best,r4
    return np.concatenate([r1,r3*2,rb,best*2,r4*2])
out=[]
for F in [float(x) for x in sys.argv[1:]]:
  bst=None
  for yaw0 in range(0,360,30):
    for pit in (-25,-35,-45):
      D=F*300/800;pr=math.radians(pit);yw=math.radians(yaw0)
      C=[c[0]-D*math.cos(pr)*math.cos(yw),c[1]-D*math.cos(pr)*math.sin(yw),-D*math.sin(pr)]
      p0=np.array(C+[yw,pr,0.0])
      f=lambda q:res(np.r_[q,F])
      try:
        sol=least_squares(f,p0,loss='soft_l1',f_scale=3,max_nfev=500)
      except Exception as e:continue
      cst=(sol.fun**2).mean()
      if bst is None or cst<bst[0]:bst=(cst,np.r_[sol.x,F])
  r1,r3,rb,r2,r4=res(bst[1],True);rm=lambda r:round(float(np.sqrt(np.median(np.square(r)))),2)
  p=bst[1];print(F,'cost',round(bst[0],1),'fence',rm(r1),'rr',rm(r3),'hinge',round(float(np.abs(rb).max()),1),'posts',np.round(r2,1),'tow',np.round(r4,1),'C',np.round(p[:3]),'ypr',np.round(np.degrees(p[3:6]),1),flush=True)
  out.append((bst[0],F,list(p)))
out.sort();c0,F,p=out[0]
json.dump({'p':p[:7]+[1.0],'W':W,'H':H,'mg':MG,'oval':FE.tolist(),'note':'fitC10: A ground, B towers xy, posts E end, RR, far fence'},open('camC10.json','w'))
print('best',F)
