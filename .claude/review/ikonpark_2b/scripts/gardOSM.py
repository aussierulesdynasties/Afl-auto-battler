import json,numpy as np,sys
g=json.load(open('osm/geo.json',encoding='utf-8'));P=np.array(g['390148641'])
inner=P[0:7][::-1]  # (34.4,112.8)->(-31.2,108.3)  wait order fixed below
inner=P[1:7]; inner=np.r_[P[0:1],inner]          # -31.2,108.3 .. 34.4,112.8
outer=P[7:13][::-1]                              # -31.2,108.3 .. 34.3,127.2 reversed -> from west
outer=P[7:13]                                    # 34.3,127.2 .. -31.2,108.3
def resample(L,n):
    d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(L,axis=0),axis=1))];t=np.linspace(0,d[-1],n)
    return np.c_[np.interp(t,d,L[:,0]),np.interp(t,d,L[:,1])]
for src,dst in sys.argv[1:]and [tuple(a.split(':')) for a in sys.argv[1:]]:
    G=json.load(open(src));s=G['gardiner'];n=len(s['front']);z=s['front'][0][2]
    fr=np.array(s['front']);east_first=fr[0,0]>fr[-1,0]
    I=resample(inner[::-1] if east_first else inner,n);O=resample(outer if east_first else outer[::-1],n)
    print(src,'front move m',np.round(np.linalg.norm(fr[:,:2]-I,axis=1).max(),1),'back move m',np.round(np.linalg.norm(np.array(s['back'])[:,:2]-O,axis=1).max(),1))
    s['front']=[[a,b,z] for a,b in I];s['back']=[[a,b,z] for a,b in O]
    json.dump(G,open(dst,'w'),indent=1)
