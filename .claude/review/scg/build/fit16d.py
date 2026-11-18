import io,contextlib
with contextlib.redirect_stdout(io.StringIO()):exec(open('geo.py').read())
exec(open('fitx.py').read())
CW=1500
pitch=dens(G['4000006'],3);pitch=np.c_[pitch,np.zeros(len(pitch))]
PCc=np.array([0.94,-11.82])
def edge(k):
    o=[];i=[]
    for d,(lo,hi,zf,zo,s) in OUT.items():
        if s in('bottom','trumper'):
            a=math.radians(d);u=np.array([math.cos(a),math.sin(a)])
            o.append([*(PCc+hi*u),zo]);i.append([*(PCc+lo*u),zf])
    return np.array(o),np.array(i)
EO,EI=edge(0);print(len(EO))
IO=np.array([(619.5,781),(811.6,786),(948,776),(1053.7,762.6),(1261,717),(1335,675),(1408,617),(1448,533)])
II=np.array([(653.7,691.6),(811.6,715),(948,694),(1053.7,668),(1145,627),(1192.6,601)])
HEAD={'D':(1263,553),'E':(550,561)};SHAFT={'D':[(1256,687),(1242,825)],'E':[(556,687),(564,812)]}
GR=np.load('grass16.npy');GR=GR[GR[:,1]<480][::2]
def cm(P,X,p):pp=proj(p,X);return np.sqrt(((P[:,None,:]-pp[None])**2).sum(-1)).min(1)
def res(q):
    p=list(q)+[H];r=[]
    for k,v in HEAD.items():r+=list(proj(p,[(*T[order.index(k)],H)])[0]-np.array(v))
    for k,L in SHAFT.items():
        i=order.index(k);a,b=proj(p,[(*T[i],0),(*T[i],H)]);t=(b-a)/np.linalg.norm(b-a);n=np.array([-t[1],t[0]])
        for v in L:r.append(float((np.array(v)-a)@n))
    return np.r_[r,cm(IO,EO,p),cm(II,EI,p),cm(GR,pitch,p)*0.5]
lo=[-4e3,-4e3,30,-7,-1.5,-0.5,300,-700,-1000];hi=[4e3,4e3,4e3,7,-0.05,0.5,20000,2300,2000]
best=None
for az in range(150,260,10):
  for el in (20,30,40):
    for d in (600,1000,1600):
      a=math.radians(az);e=math.radians(el);C=np.r_[PCc,0]+d*np.array([math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)])
      v=(np.r_[PCc,0]-C)/d;q=[*C,math.atan2(v[1],v[0]),math.asin(v[2]),0,d*1.6,800,533]
      try:s=least_squares(res,np.clip(q,np.array(lo)+1e-3,np.array(hi)-1e-3),bounds=(lo,hi),max_nfev=200)
      except Exception as ex:continue
      if best is None or s.cost<best.cost:best=s
s=least_squares(res,best.x,bounds=(lo,hi));r=s.fun
print('towers',np.round(r[:8],1));print('outer',np.round(r[8:8+len(IO)],1));print('inner',np.round(r[8+len(IO):8+len(IO)+len(II)],1))
print('grass rms',round(math.sqrt((r[8+len(IO)+len(II):]**2).mean())/0.5,1))
p=list(s.x)+[H];print([round(v,3) for v in p])
json.dump({'p':p,'W':1600,'H':1067,'img':'refs4/016.jpg'},open('cam16.json','w'))
