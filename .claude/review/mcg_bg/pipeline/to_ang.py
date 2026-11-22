import json,numpy as np
from scipy.spatial import cKDTree
T=[np.array(t) for t in json.load(open('out/mcg/rails/plan_tracks.json'))]
toes=np.array(json.load(open('out/mcg/rails/toes.json')))
rows=[]
for i,p in enumerate(toes):
  div=[k for k,t in enumerate(T) if min(np.hypot(*(t[0]-p)),np.hypot(*(t[-1]-p)))<0.05]
  r=dict(i=i,at=p.round(1).tolist())
  if not div: rows.append(r);continue
  k=div[0];t=T[k];s=t if np.hypot(*(t[0]-p))<0.05 else t[::-1]
  best=None
  for m,u in enumerate(T):
    if m==k: continue
    d,j=cKDTree(u).query(p)
    if d<1.0 and (best is None or d<best[1]): best=(m,d,j)
  if not best: rows.append(r);continue
  m,_,j=best;u=T[m];tr=cKDTree(u)
  L=np.concatenate([[0],np.cumsum(np.hypot(*np.diff(s,axis=0).T))])
  dd=tr.query(s)[0]
  # angle: separation growth between 1.6 m (frog) and 4 m, or fit over first 25 m
  sel=(dd>0.8)&(dd<3.5)&(L<60)
  a=np.degrees(np.arctan(np.polyfit(L[sel],dd[sel],1)[0])) if sel.sum()>3 else None
  fi=int(np.argmax(dd>1.6)) if (dd>1.6).any() else None
  r.update(div=k,thr=m,ang=round(a,2) if a else None,N=round(1/np.tan(np.radians(a)),1) if a else None,frog_from_toe=round(float(L[fi]),1) if fi is not None else None,frog=s[fi].round(1).tolist() if fi is not None else None,maxsep=round(float(dd[L<60].max()),1))
  rows.append(r)
json.dump(rows,open('out/mcg/rails/turnout_angles.json','w'),indent=0)
import collections
for r in rows: print(r.get('i'),r.get('at'),r.get('div'),r.get('thr'),r.get('ang'),r.get('N'),r.get('frog_from_toe'),r.get('maxsep'))
