import json,math,numpy as np
from PIL import Image
S=np.asarray(Image.open('../obuild/sat/sat_025.png').convert('L')).astype(float)
J=json.load(open('../obuild/geom.json'));oc=np.array(J['oc'][:2]);X0,Y1,RS=-260,230,0.25
M=np.load('mask.npy')
def at(A,x,y):
    u,v=int(round((x-X0)/RS)),int(round((Y1-y)/RS));return A[v,u]
ds=np.arange(0,360,1.0)
E=json.load(open('model_edges.json'));mi,mo=np.array(E['mi']),np.array(E['mo'])
for d in []:
    a=math.radians(d);rs=np.arange(60,200,0.1);w=np.array([at(M,oc[0]+math.cos(a)*r,oc[1]+math.sin(a)*r) for r in rs]);i=np.where(w)[0];mi.append(rs[i[0]]);mo.append(rs[i[-1]])

def val(x,y,z):
    u=(x-X0)/RS-5/44.7*z;v=(Y1-y)/RS+56/44.7*z;return S[int(round(v)),int(round(u))]
RF=np.array([p[:2] for p in J['roof']]);IN=np.array([p[:2] for p in J['inner']]);K=J['K']
out={}
for T in(0.3,0.5,0.7):
  dd=np.arange(0,360,0.1);p=[]
  for d in dd:
    a=math.radians(d);r=np.interp(d,ds,mo,period=360)*(1-T)+np.interp(d,ds,mi,period=360)*T;z=46.55-3.75*T
    p.append(np.mean([val(oc[0]+math.cos(a)*(r+o),oc[1]+math.sin(a)*(r+o),z) for o in(-2,-1,0,1,2)]))
  p=np.array(p);bg=np.convolve(np.r_[p[-30:],p,p[:30]],np.ones(61)/61,'same')[30:-30];dip=bg-p
  pk=np.array([dd[i] for i in range(len(p)) if dip[i]>8 and dip[i]==max(dip[max(0,i-25):i+26])])
  mr=[]
  for i in range(0,len(RF),K):
    q=RF[i]+(IN[i]-RF[i])*T-oc;a=math.degrees(math.atan2(q[1],q[0]))%360
    r=np.interp(a,ds,mo,period=360)*(1-T)+np.interp(a,ds,mi,period=360)*T
    mr.append(a)
  mr=np.array(mr);off=np.full(len(mr),np.nan)
  for k,a in enumerate(mr):
    d_=(pk-a+180)%360-180
    if len(d_) and abs(d_).min()<2.6:off[k]=d_[abs(d_).argmin()]
  ok=~np.isnan(off);print('T=%.1f photo ribs %d, model ribs matched %d/52, offset median %+.2f, mean|.| %.2f, |off|<0.5: %d'%(T,len(pk),ok.sum(),np.nanmedian(off),np.nanmean(abs(off)),(abs(off[ok])<0.5).sum()))
  out[T]={'model':mr.tolist(),'off':[None if np.isnan(o) else float(o) for o in off],'peaks':pk.tolist()}
json.dump(out,open('ribs.json','w'))
