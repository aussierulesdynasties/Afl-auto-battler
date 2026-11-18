# map the photo's pale radial lines on the near roof (x read off zB_nr2.png at the band middle) to fence angles through camB
import json,math,numpy as np
from camlib import proj
J=json.load(open('layoutA.json'));C0=J['C0'];co=J['fence']['co'];K=J['fence']['K'];JB=json.load(open('layoutB.json'))
cam=json.load(open('camB.json'))['p'][:7]
def rf(a):t=math.radians(a);return sum(co[k]*math.cos(k*t) for k in range(K+1))+sum(co[K+k]*math.sin(k*t) for k in range(1,K+1))
def P(a,d,z):r=rf(a)+d;t=math.radians(a);return [C0[0]+r*math.cos(t),C0[1]+r*math.sin(t),z]
def fP(S,col,ref=-70,deg=3):
    A=np.array([s[0] for s in S]);V=np.array([s[col] for s in S]);c=np.polyfit(A,V,deg);return lambda a:float(np.polyval(c,min(max(a,A.min()),A.max())))
SF=[[a,max(d,0.5),z] for a,d,z in JB['SF']];SB=JB['SB'];sfd,sfz,sbd,sbz=fP(SF,1),fP(SF,2),fP(SB,1),fP(SB,2)
A=np.arange(-141,-4,0.25);X=np.array([P(a,(sfd(a)+sbd(a))/2,(sfz(a)+sbz(a))/2) for a in A]);Q=proj(cam,X,500,300)
xs=[238,275,315,355,400,440,470,495,525,560,600,640,680]
out=[]
for x in xs:
    i=np.argmin(abs(Q[:,0]-x));out.append(round(float(A[i]),1))
print(out);print(np.diff(out))
# north stand aisles: lower-left (front) ends read off zB_ns2.png
pts=[(598,228),(632,242),(666,257),(695,272),(720,288),(742,302),(758,318),(774,334),(790,350)]
A=np.arange(30,140,0.2);X=np.array([P(a,2.0,1.5) for a in A]);Q=proj(cam,X,500,300)
print('aisles',[round(float(A[np.argmin(((Q-np.array(p))**2).sum(1))]),1) for p in pts])
print('front proj err',[round(float(np.sqrt(((Q-np.array(p))**2).sum(1)).min()),1) for p in pts])
BF=JB['BF'];bfd,bfz=fP(BF,1,100,3),fP(BF,2,100,3)
L=[((598,228),(635,190)),((632,242),(665,205)),((666,257),(700,225)),((695,272),(722,247)),((720,288),(742,272)),((742,302),(765,286)),((758,318),(790,302)),((774,334),(805,322)),((790,350),(820,340))]
def segd(p,a,b):
    p,a,b=map(np.array,(p,a,b));t=np.clip(((p-a)@(b-a))/((b-a)@(b-a)),0,1);return np.linalg.norm(p-(a+t*(b-a)))
res=[]
for f,b in L:
    best=min(((segd(f,*proj(cam,np.array([P(a,0,1.2),P(a,bfd(a),bfz(a))]),500,300))+segd(b,*proj(cam,np.array([P(a,0,1.2),P(a,bfd(a),bfz(a))]),500,300)),a) for a in np.arange(30,140,0.2)))
    res.append((round(float(best[1]),1),round(float(best[0]),1)))
print('aisles2',res)
