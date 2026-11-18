exec(open('fitx.py').read())
import io,contextlib,time
pitch=dens(G['4000006'],3);pitch=np.c_[pitch,np.zeros(len(pitch))]
HEAD={'F':(197,334),'A':(337,97),'B':(1205,74),'C':(1372,139),'D':(1263,553),'E':(550,561)}
SHAFT={'F':[(212.5,437),(222,531)],'A':[(347,187),(355,269)],'B':[(1195,156),(1189,237)],'C':[(1361,219),(1349,312)],
'D':[(1256,687),(1242,825)],'E':[(556,687),(564,812)]}
GR=np.load('grass16.npy');GR=GR[GR[:,1]<570][::3]
PCc=np.array([0.94,-11.82,0]);t0=time.time();res=[]
for az in range(140,261,5):
  for el in range(12,50,3):
    for d in np.geomspace(300,2500,12):
      a=math.radians(az);e=math.radians(el)
      C=PCc+d*np.array([math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)])
      v=(PCc-C)/d;yaw=math.atan2(v[1],v[0]);pit=math.asin(v[2])
      for f in np.geomspace(600,8000,14):
        p=[*C,yaw,pit,0,f,800,533,H]
        res.append((cost(HEAD,SHAFT,p,GR,0.5),p))
res.sort(key=lambda x:x[0]);print('grid',round(time.time()-t0),'s',[round(r[0]) for r in res[:5]])
best=None
for c,p in res[:8]:
    with contextlib.redirect_stdout(io.StringIO()):q=fit(HEAD,SHAFT,1600,1067,p[:9],GR)
    cc=cost(HEAD,SHAFT,q,GR,0.5)
    if best is None or cc<best[0]:best=(cc,q)
q=best[1];fit(HEAD,SHAFT,1600,1067,q[:9],GR);print([round(v,3) for v in q])
json.dump({'p':q,'W':1600,'H':1067,'img':'refs4/016.jpg'},open('cam16.json','w'))
