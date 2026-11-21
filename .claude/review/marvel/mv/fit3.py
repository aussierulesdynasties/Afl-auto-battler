import sys
exec(open('fit1.py',encoding='utf-8').read().split('import math\np0=')[0])
import math
MODE=sys.argv[1]  # 'pp' free principal point, 'k1' centre pp + radial k1
NB=[(315,395),(1470,380)];NBA=(870,298)
NF=[(205,488),(1557,478)];NFA=(870,379)
FI=[(540,215),(1300,210)];FIA=(880,136);FOA=(880,120)
def projk(p,X,k1):
    uv=proj(p,X);
    if k1==0:return uv
    c=np.array([960,540.]);d=(uv-c)/1000;r2=(d**2).sum(1,keepdims=True);return c+d*1000*(1+k1*r2)
def unpack(q):
    if MODE=='pp':p=list(q[:9]);k1=0;e=q[9:]
    else:p=list(q[:7])+[960,540];k1=q[7];e=q[8:]
    return p,k1,dict(hA=e[0],hT=e[1],hD=e[2],zr=e[3],hi=e[4],ho=e[5],c=e[6:8],L=e[8:10],R=e[10:12],FL=e[12:14],FR=e[14:16])
def res(q):
    p,k1,h=unpack(q);r=[];P=lambda X:projk(p,X,k1)
    for (uv,(x,y,z)) in FIX:
        z=h[z] if isinstance(z,str) else z;r+=list(P([(x,y,z)])[0]-np.array(uv))
    pt=P(np.c_[TR,np.full(len(TR),h['hT'])]);dd=np.sqrt(((TIPS[:,None]-pt[None])**2).sum(-1)).min(1);r+=list(dd)
    pd=P(np.c_[DRUM,np.full(len(DRUM),h['hD'])]);dd=np.sqrt(((ARC[:,None]-pd[None])**2).sum(-1)).min(1);r+=list(dd*0.5)
    zr=h['zr'];c=np.array(h['c']);L=np.array(h['L']);R_=np.array(h['R']);FL=np.array(h['FL']);FR=np.array(h['FR'])
    pts=[(L,zr,NB[0]),(R_,zr,NB[1]),(2*c-R_,zr,FI[0]),(2*c-L,zr,FI[1]),((L+R_)/2,h['hi'],NBA),(2*c-(L+R_)/2,h['hi'],FIA),
         (FL,zr,NF[0]),(FR,zr,NF[1]),((FL+FR)/2,h['ho'],NFA),(2*c-(FL+FR)/2,h['ho'],FOA)]
    for xy,z,uv in pts: r+=list(P([(xy[0],xy[1],z)])[0]-np.array(uv))
    d1=R_-L;d2=FR-FL;r+=[(np.linalg.norm(d1)-np.linalg.norm(d2))*0.5,(d1[0]*d2[1]-d1[1]*d2[0])/np.linalg.norm(d1)*0.5]
    r+=list((c-np.array([0.27,-9.5]))*0.2)
    return np.array(r)
c2=json.load(open('c2.json'));p2=c2['p'];h2=c2['h']
best=None
for zr in (36,42,48):
  A=at_z(p2,*NB[0],zr);B=at_z(p2,*NB[1],zr);F1=at_z(p2,*NF[0],zr);F2=at_z(p2,*NF[1],zr)
  ex=[h2['hA'],h2['hT'],h2['hD'],zr,zr+14,zr+12,0.27,-9.5,A[0],A[1],B[0],B[1],F1[0],F1[1],F2[0],F2[1]]
  elo=[0,2,2,20,20,20,-40,-40]+[-1e3]*8;ehi=[20,20,40,70,90,90,40,40]+[1e3]*8
  if MODE=='pp':q0=list(p2)+ex;lo=[-1e4]*3+[-3,-1.3,-0.3,500,700,400]+elo;hi=[1e4]*3+[3,0,0.3,4000,1220,900]+ehi
  else:q0=list(p2[:7])+[0.0]+ex;lo=[-1e4]*3+[-3,-1.3,-0.3,500,-0.5]+elo;hi=[1e4]*3+[3,0,0.3,4000,0.5]+ehi
  s=least_squares(res,q0,bounds=(lo,hi),x_scale='jac')
  print(zr,'cost',round(s.cost,1),flush=True)
  if best is None or s.cost<best.cost:best=s
s=best;p,k1,h=unpack(s.x);r=s.fun
print('rms',round(math.sqrt((r**2).mean()),1),'k1',k1);print(np.round(r,1))
print('p',[round(float(v),3) for v in p]);print({k:np.round(v,2).tolist() for k,v in h.items()})
json.dump({'p':[float(v) for v in p],'k1':float(k1),'h':{k:np.asarray(v).tolist() for k,v in h.items()}},open('c3_%s.json'%MODE,'w'))
