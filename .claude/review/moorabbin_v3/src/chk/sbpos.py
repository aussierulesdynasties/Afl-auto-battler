import json,math,numpy as np
exec(open('chk/ringover.py').read().split("cam=np.array")[0])
print(list(O.keys()))
S=O['score']
for q in S['ends']+[S['base']]:
    a,d=polar([q]);print('sb',np.degrees(a).round(2),d.round(2),'do',round(d_out(a[0]),2))
for b in O['club']:
    a,d=polar(b['pts']);print(b['n'],np.degrees(a).round(0).min(),np.degrees(a).round(0).max(),d.min().round(1),d.max().round(1),[round(d_out(x),1) for x in a][:3])
for k in ('huggins','pav','pavilion','hug'):
    if k in O:print(k,str(O[k])[:300])
