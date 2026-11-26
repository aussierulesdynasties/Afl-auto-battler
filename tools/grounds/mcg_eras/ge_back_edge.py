import json,math,numpy as np
D=json.load(open('/home/user/Afl-auto-battler/tools/grounds/mcg/model/mcg.json'))
t=np.array(D['roof_outer'],float); bb=np.r_[t[:,0]-360,t[:,0],t[:,0]+360]; vv=np.r_[t[:,1],t[:,1],t[:,1]]
bs=list(range(60,241,5))+list(range(250,360,10))
A=json.load(open('fa.json')); B=json.load(open('fb.json'))
def idx(f): return int(f[-8:-4])
pts={}
for off,L in [(0,A),(504,B)]:
    for f,v,s in L:
        if 'full' in f or v is None: continue
        pts[off+idx(f)]=v
res=[]
for k,b in enumerate(bs):
    P=[pts.get(k*21+j) for j in range(21)]; P=[p for p in P if p]
    P=sorted([(math.hypot(p[0],p[1]),p[2]-8) for p in P])
    zr=max(z for r,z in P); top=[(r,z) for r,z in P if z>=zr-3]
    last=max(r for r,z in top); nxt=[r for r,z in P if r>last]
    edge=(last+min(nxt))/2 if nxt else float('nan'); err=(min(nxt)-last)/2 if nxt else float('nan')
    m=float(np.interp(b,bb,vv)); res.append((b,round(edge,1),round(err,1),m,zr))
    print('%3d roof %2d m  back edge GE %5.1f +-%.1f  model %5.1f  diff %+5.1f   %s'%(b,zr,edge,err,m,edge-m,' '.join('%.0f:%d'%x for x in P)))
json.dump(res,open('fine_edges.json','w'))
