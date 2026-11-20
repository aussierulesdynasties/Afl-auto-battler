# prattfix.py IN OUT EXTEND XEAST  -> Pratt plan corrected to the 2022 Wayback roof edges at lean (0.10,0.28)
# Each front/back vertex moves along its outward normal by the median-smoothed satellite edge offset (heights kept).
# EXTEND: extra vertices continuing the west curve (same step and turn as the last 8). XEAST: drop vertices east of it (B only).
import cv2,json,sys,numpy as np
G=json.load(open(sys.argv[1]));ext=int(sys.argv[3]);xe=float(sys.argv[4])
s=cv2.GaussianBlur(cv2.imread('sat/wb42663.png',0).astype(np.float32),(0,0),1.5)
KX,KY=0.10,0.28;C=np.array(G['centre'][:2],float)
def val(x,y):return cv2.getRectSubPix(s,(1,1),(float((x+150)/0.25),float((230-y)/0.25)))[0,0]
def normals(P):
  N=[]
  for i in range(len(P)):
    a=P[max(i-1,0)][:2];b=P[min(i+1,len(P)-1)][:2];t=b-a;n=np.array([t[1],-t[0]]);n/=np.linalg.norm(n)
    if np.dot(n,P[i][:2]-C)<0:n=-n
    N.append(n)
  return np.array(N)
def fit(P,sg,W=6):
  N=normals(P);T=np.arange(-W,W+.01,0.25);o=[];g=[]
  for (x,y,z),n in zip(P,N):
    q=np.array([x+KX*z,y+KY*z]);pr=np.array([val(*(q+t*n)) for t in T]);d=np.gradient(pr)*-sg;j=int(np.argmax(d));o.append(T[j]);g.append(d[j])
  return np.array(o),np.array(g),N
def extend(P,k):
  P=[np.array(p,float) for p in P]
  if k<=0:return np.array(P)
  d=P[-1][:2]-P[-9][:2];step=np.linalg.norm(d)/8
  a0=np.arctan2(*(P[-9][:2]-P[-10][:2])[::-1]);a1=np.arctan2(*(P[-1][:2]-P[-2][:2])[::-1]);turn=(a1-a0)/8
  a=a1;cur=P[-1].copy()
  for _ in range(k):
    a+=turn;cur=cur+np.array([np.cos(a)*step,np.sin(a)*step,0]);P.append(cur.copy())
  return np.array(P)
pr=G['pratt'];F=extend(pr['front'],ext);B=extend(pr['back'],ext)
keep=[i for i in range(len(B)) if B[i][0]<=xe and F[i][0]<=xe+6]
for it in range(2):
  for key,P,sg in (('front',F,-1),('back',B,1)):
    o,g,N=fit(P,sg);med=np.array([np.median(o[max(0,i-3):i+4]) for i in range(len(o))])
    P[:,:2]+=med[:,None]*N
    print(it,key,'raw',' '.join(f'{v:+.1f}' for v in o))
F=F[keep];B=B[keep]
for P in (F,B):
  Q=P.copy()
  for i in range(2,len(P)-2):P[i,:2]=Q[i-2:i+3,:2].mean(0)
  P[-1,:2]=2*P[-2,:2]-P[-3,:2];P[0,:2]=2*P[1,:2]-P[2,:2]
for key,P,sg in (('front',F,-1),('back',B,1)):
  o,g,N=fit(P,sg);print('AFTER',key,'n',len(o),'|o|<=2:',f'{np.mean(abs(o)<=2):.2f}','max',abs(o).max(),'\n ',' '.join(f'{v:+.1f}' for v in o),'\n  str',' '.join(f'{v:.0f}' for v in g))
pr['front']=F.round(2).tolist();pr['back']=B.round(2).tolist()
mi=[i for i in pr['mastidx'] if i<len(F)]
mi=[i for i in mi if i<len(F)-4]+[len(F)-1]
pr['mastidx']=mi
json.dump(G,open(sys.argv[2],'w',encoding='utf-8',newline=''))
print('verts',len(F),'west end back',B[-1].round(1),'front',F[-1].round(1),'east back',B[0].round(1))
