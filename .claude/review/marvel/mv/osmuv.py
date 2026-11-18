import json,numpy as np,math,sys
from sf import *
G=json.load(open('osm/geo.json'))
def touv(a):
    a=np.array(a);q=loc(np.c_[a,np.zeros(len(a))]);d=q-O;return np.stack([d@U,d@V],1)
out=[]
for k,w in G['ways'].items():
    tg=G['tags'].get(k,{})
    if not any(x in tg for x in('building','building:part','man_made','leisure','amenity')):continue
    q=touv(w)
    if np.abs(q).max()>190 or np.abs(q).min()>150:pass
    if (np.abs(q[:,0])<200).all() and (np.abs(q[:,1])<200).all():
        out.append((k,{x:tg[x] for x in tg if x in('building','building:part','name','height','building:levels','min_height','leisure','man_made','amenity')},q.round(1).tolist()))
for k,t,q in out:print(k,t,len(q),np.array(q).min(0),np.array(q).max(0))
json.dump(out,open('osmuv.json','w'))
