# python model/cmp.py name x0 y0 x1 y1 ztop out : for the 4 close views where box is biggest, photo crop | render crop | edges
import sys,cv2,numpy as np,os
sys.path.insert(0,'work');import earthcam as E
n=sys.argv[1];x0,y0,x1,y1,zt=map(float,sys.argv[2:7]);out=sys.argv[7]
G={'nw':(-62,58),'n':(-15,80),'ne':(62,60),'e':(79,-8),'e2':(76,-46),'se':(60,-90),'s':(51,-120),'w':(-80,-20)}
P=[(x,y,z) for x in(x0,x1) for y in(y0,y1) for z in(0,zt)]
cands=[]
for g,(tx,ty) in G.items():
  for h in(0,90,180,270):
    c=E.cam(h,60,140,tz=1,tx=tx,ty=ty);q=np.array([E.proj(c,p) for p in P])
    u0,v0=q.min(0);u1,v1=q.max(0)
    if u0<0 or v0<50 or u1>1920 or v1>1040:continue
    cands.append(((u1-u0)*(v1-v0),f'g_{g}_{h:03d}',int(u0),int(v0),int(u1),int(v1)))
cands.sort(reverse=True);rows=[]
for A,nm,u0,v0,u1,v1 in cands[:4]:
  pad=40;u0,v0=max(u0-pad,0),max(v0-pad,0);u1,v1=min(u1+pad,1920),min(v1+pad,1080)
  p=cv2.imread(f'ge/{nm}.png')[v0:v1,u0:u1];r=cv2.imread(f'rr/{nm}.png',cv2.IMREAD_UNCHANGED)[v0:v1,u0:u1]
  a=r[:,:,3:4]/255.;ren=(r[:,:,:3]*a+np.array([235,215,190])*(1-a)).astype(np.uint8)
  e=cv2.Canny(cv2.cvtColor(r[:,:,:3],cv2.COLOR_BGR2GRAY),60,150)|cv2.Canny(r[:,:,3],50,150);ov=p.copy();ov[e>0]=(0,0,255)
  s=600/max(p.shape[0],1)
  row=np.hstack([cv2.resize(x,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC) for x in(p,ren,ov)])
  cv2.putText(row,nm,(8,28),0,0.9,(0,255,255),2);rows.append(row)
W=max(r.shape[1] for r in rows);rows=[np.pad(r,((0,4),(0,W-r.shape[1]),(0,0))) for r in rows]
cv2.imwrite(out,np.vstack(rows));print(out,[c[1] for c in cands[:4]])
