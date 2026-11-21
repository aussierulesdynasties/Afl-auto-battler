# satellite white-roof outer radius per angle from oc, compared with r2/roofr_model.json
import json,math,numpy as np
from PIL import Image
S=np.asarray(Image.open('sat/sat_025.png').convert('RGB')).astype(int);X0,Y1,RES=-260,230,0.25
oc=json.load(open('geom.json'))['oc'];M=json.load(open('r2/roofr_model.json'))
def px(x,y):
  u,v=int(round((x-X0)/RES)),int(round((Y1-y)/RES))
  return S[v,u] if 0<=v<S.shape[0] and 0<=u<S.shape[1] else np.array([0,0,0])
out={};rows=[]
for a in range(0,360,2):
  c,s=math.cos(math.radians(a)),math.sin(math.radians(a));last=None;gap=0;r=95.0;started=False
  while r<200:
    p=px(oc[0]+c*r,oc[1]+s*r);w=p.min()>185 and p.max()-p.min()<40
    if w:started=True;last=r;gap=0
    elif started:
      gap+=0.25
      if gap>4.0:break
    r+=0.25
  m=M[str(a)][0];out[a]=(last,m);rows.append((a,last,m,None if last is None or m is None else m-last))
d=np.array([x[3] for x in rows if x[3] is not None])
print('n',len(d),'median diff (model-sat) %.2f  mean |d| %.2f  p90 |d| %.2f  max |d| %.2f'%(np.median(d),np.abs(d).mean(),np.percentile(np.abs(d),90),np.abs(d).max()))
for a,l,m,dd in rows:print(a,l,m,None if dd is None else round(dd,2))
json.dump(rows,open('r2/roofsat.json','w'))
