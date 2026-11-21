import json,math,numpy as np
W=[q[:2] for q in json.load(open('wallbase.json'))]+[(-120.0,y) for y in np.arange(-45,21,0.5)]
W=np.array(W)
def ll(ds,dn,es):
  lat=-(38+9/60+ds/3600);lon=144+21/60+es/3600
  return np.array([(lon-144.354577)*87547,(lat+38.158219)*111320])  # lat0 frame
P={ # name:(lat s,lon s,side,gap m)
 'E2':(29.13,20.15,'E',0.3),'E3':(27.27,20.97,'E',0.3),
 'N_faceW':(24.735,16.95,'N',0.31),'N_x300':(24.83,18.25,'N',0.3),'N_x900':(25.16,15.15,'N',0.1),
 'S_pillar':(33.35,17.32,'S',0.3),'S_pillar2':(33.29,14.23,'S',0.1),'S_wall3':(32.63,13.72,'S',0.1),
 'W_mid':(29.72,11.90,'W',0.3),'W_S':(30.44,12.00,'W',0.3),'W_N':(28.99,11.89,'W',0.3)}
HOLD={'N_x900','W_mid','S_wall3'}
G={k:ll(a,0,b) for k,(a,b,_,_) in P.items()}
def tf(p,th,t):c,s=math.cos(th),math.sin(th);return np.array([c*p[0]-s*p[1],s*p[0]+c*p[1]])-t
def nearest(m):
  d=np.hypot(*(W-m).T);i=np.argsort(d)[:6];pts=W[i]
  c=pts.mean(0);u,s,vt=np.linalg.svd(pts-c);n=vt[1];return c,n
def resid(names,th,t):
  out={}
  for k in names:
    m=tf(G[k],th,t);c,n=nearest(m);out[k]=float(n@(m-c))*(1 if n@(m-np.array([-6,-11]))>=0 else -1)
  return out
th,t=0.0,np.array([9.0,22.0])
fitn=[k for k in P if k not in HOLD]
for it in range(30):
  rows=[];b=[]
  for k in fitn:
    m=tf(G[k],th,t);c,n=nearest(m);r=n@(m-c)
    dm=np.array([-math.sin(th)*G[k][0]-math.cos(th)*G[k][1],math.cos(th)*G[k][0]-math.sin(th)*G[k][1]])
    rows.append([n@dm,-n[0],-n[1]]);b.append(-r)
  x=np.linalg.lstsq(np.array(rows),np.array(b),rcond=None)[0];th+=x[0];t=t+x[1:]
r0=resid(P,0.0,np.array([9.0,22.0]));r=resid(P,th,t)
print(f'fit: rot {math.degrees(th):.3f} deg  shift (model = lat0 frame - ({t[0]:.2f},{t[1]:.2f}))')
fr=[r[k] for k in fitn];print('rms fit pts',round(math.sqrt(np.mean(np.square(fr))),3))
print('pt,side,GE-only,gap_m,resid_before(+9,+22),resid_after,(+out/-in)')
for k,(a,b,s,g) in P.items():print(k,s,'GE',g,round(r0[k],2),round(r[k],2),'HOLD' if k in HOLD else '')
json.dump({'th':th,'t':list(t),'r0':r0,'r':r,'hold':list(HOLD)},open('fit3.json','w'))
