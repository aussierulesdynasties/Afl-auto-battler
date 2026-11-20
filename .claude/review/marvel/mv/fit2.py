import sys
exec(open('fit1.py',encoding='utf-8').read().split('import math\np0=')[0])
import math
# roof symmetry: nearB arch feet (L,R) at zr; far arch feet = 2c - (R,L); apex heights equal
NB=[(315,395),(1470,380)];NBA=(870,295);FA=[(540,215),(1300,210)];FAA=(900,120)
NF=[(210,485),(1560,470)];NFA=(870,365)
def unpack2(q):
    p=list(q[:9]);e=q[9:]
    return p,dict(hA=e[0],hT=e[1],hD=e[2],zr=e[3],ha=e[4],c=e[5:7],L=e[7:9],R=e[9:11],hf=e[11],FL=e[12:14],FR=e[14:16])
def res2(q):
    p,h=unpack2(q);r=[]
    for (uv,(x,y,z)) in FIX:
        z=h[z] if isinstance(z,str) else z;r+=list(proj(p,[(x,y,z)])[0]-np.array(uv))
    pt=proj(p,np.c_[TR,np.full(len(TR),h['hT'])]);dd=np.sqrt(((TIPS[:,None]-pt[None])**2).sum(-1)).min(1);r+=list(dd)
    pd=proj(p,np.c_[DRUM,np.full(len(DRUM),h['hD'])]);dd=np.sqrt(((ARC[:,None]-pd[None])**2).sum(-1)).min(1);r+=list(dd*0.5)
    zr=h['zr'];c=np.array(h['c']);L=np.array(h['L']);R_=np.array(h['R'])
    pts=[(L,zr,NB[0]),(R_,zr,NB[1]),(2*c-R_,zr,FA[0]),(2*c-L,zr,FA[1]),((L+R_)/2,h['ha'],NBA),(2*c-(L+R_)/2,h['ha'],FAA),
         (np.array(h['FL']),zr,NF[0]),(np.array(h['FR']),zr,NF[1]),((np.array(h['FL'])+np.array(h['FR']))/2,h['hf'],NFA)]
    for xy,z,uv in pts: r+=list(proj(p,[(xy[0],xy[1],z)])[0]-np.array(uv))
    # panels parallel & same length: near front arch parallel to near back, same length
    d1=R_-L;d2=np.array(h['FR'])-np.array(h['FL']);r+=[ (np.linalg.norm(d1)-np.linalg.norm(d2))*0.5, (d1[0]*d2[1]-d1[1]*d2[0])/np.linalg.norm(d1)*0.5]
    r+=list((c-np.array([0.27,-9.5]))*0.2)  # weak prior: roof centred on stadium footprint
    return np.array(r)
c1=json.load(open('c1.json'));p1=c1['p'];h1=c1['h']
best=None
for zr in (34,40,46):
  A=at_z(p1,*NB[0],zr);B=at_z(p1,*NB[1],zr);F1=at_z(p1,*NF[0],zr);F2=at_z(p1,*NF[1],zr)
  q0=list(p1)+[h1['hA'],h1['hT'],h1['hD'],zr,zr+12,0.27,-9.5,A[0],A[1],B[0],B[1],zr+12,F1[0],F1[1],F2[0],F2[1]]
  lo=[-1e4]*3+[-3,-1.3,-0.3,500,700,500]+[0,2,2,20,20,-40,-40]+[-1e3]*4+[20]+[-1e3]*4
  hi=[1e4]*3+[3,0,0.3,4000,1220,900]+[20,20,40,70,90,40,40]+[1e3]*4+[90]+[1e3]*4
  s=least_squares(res2,q0,bounds=(lo,hi))
  print(zr,'cost',round(s.cost,1))
  if best is None or s.cost<best.cost:best=s
s=best;p,h=unpack2(s.x);r=s.fun
print('rms',round(math.sqrt((r**2).mean()),1));print(np.round(r,1))
print('p',[round(v,3) for v in p]);print({k:np.round(v,2).tolist() for k,v in h.items()})
print('nearB len',np.linalg.norm(np.array(h['R'])-np.array(h['L'])))
json.dump({'p':[float(v) for v in p],'h':{k:np.asarray(v).tolist() for k,v in h.items()}},open('c2.json','w'))
