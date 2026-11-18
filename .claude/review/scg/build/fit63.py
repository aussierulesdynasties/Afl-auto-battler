import io,contextlib,itertools
with contextlib.redirect_stdout(io.StringIO()):exec(open('geo.py').read())
exec(open('fitx.py').read())
PCc=np.array([0.94,-11.82])
o=[];ii=[];ends=[]
ks=sorted(d for d,v in OUT.items() if v[4]=='messenger')
for d in ks:
    lo_,hi_,zf,zo,s=OUT[d];a=math.radians(d);u=np.array([math.cos(a),math.sin(a)])
    o.append([*(PCc+hi_*u),zo]);ii.append([*(PCc+lo_*u),zf])
for d in (ks[0],ks[-1]):
    lo_,hi_,zf,zo,s=OUT[d];a=math.radians(d);u=np.array([math.cos(a),math.sin(a)])
    for t in np.linspace(0,1,15):ends.append([*(PCc+(lo_+(hi_-lo_)*t)*u),zf+(zo-zf)*t])
EDGE=np.array(o+ii+ends)
RC=np.load('roof63.npy').astype(float);RC=RC[~((RC[:,1]<125)&(RC[:,0]>470)&(RC[:,0]<900))][::2]
print('roof pts',len(RC),'edge pts',len(EDGE),'deg',ks[0],ks[-1])
def cm(P,X,p):pp=proj(p,X);return np.sqrt(((P[:,None,:]-pp[None])**2).sum(-1)).min(1)
W_,H_=1296,800
def run(t1,t2):
    HEAD={t1:(677,222)};SHAFT={t1:[(683,350),(685,600)],t2:[(490,60),(492,200)]}
    def res(q):
        p=list(q)+[H];r=[]
        for k,v in HEAD.items():r+=list(proj(p,[(*T[order.index(k)],H)])[0]-np.array(v))
        for k,L in SHAFT.items():
            i=order.index(k);a,b=proj(p,[(*T[i],0),(*T[i],H)]);tt=(b-a)/np.linalg.norm(b-a);n=np.array([-tt[1],tt[0]])
            for v in L:r.append(float((np.array(v)-a)@n))
        return np.r_[r,cm(RC,EDGE,p)*0.5]
    lo=[-4e3,-4e3,30,-7,-1.5,-0.5,300,-700,-1000];hi=[4e3,4e3,4e3,7,-0.05,0.5,20000,2300,2000];best=None
    for az in range(0,360,20):
      for el in (25,40,55):
        for dd in (400,700,1100):
          a=math.radians(az);e=math.radians(el);C=np.r_[PCc,0]+dd*np.array([math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)])
          tgt=np.r_[PCc+np.array([10,90]),10];v=(tgt-C)/np.linalg.norm(tgt-C);q=[*C,math.atan2(v[1],v[0]),math.asin(v[2]),0,dd*1.6,W_/2,H_/2]
          try:s=least_squares(res,np.clip(q,np.array(lo)+1e-3,np.array(hi)-1e-3),bounds=(lo,hi),max_nfev=150)
          except Exception:continue
          if best is None or s.cost<best.cost:best=s
    s=least_squares(res,best.x,bounds=(lo,hi));return s
res_=[]
for t1,t2 in [('F','E'),('A','F'),('F','A'),('A','E')]:
    s=run(t1,t2);r=s.fun;print(t1,t2,'tower',np.round(r[:6],1),'roof rms',round(math.sqrt((r[6:]**2).mean())/0.5,1),flush=True);res_.append((s.cost,t1,t2,s))
c,t1,t2,s=min(res_,key=lambda x:x[0]);p=list(s.x)+[H];print('BEST',t1,t2,[round(v,3) for v in p])
json.dump({'p':p,'W':W_,'H':H_,'img':'refs3/063.jpg','towers':[t1,t2]},open('cam63.json','w'))
