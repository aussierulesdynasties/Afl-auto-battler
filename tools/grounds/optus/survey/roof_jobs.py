import json,math,numpy as np,sys
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/optus');import shape as S
F=360/math.tan(math.radians(25.58/2))
URL={x['name']:x['url'] for x in json.load(open('hover_jobs.json'))}
V={}
for a in open('args_g.txt').read().split():
    nm,v=a.split(':');v=[float(x) for x in v.split(',')];V[nm]=(v[3],v[4],v[2])
out={};meta=[]
for b in range(0,50,4):
    for half in (0,0.5):
        s=(float(S.truss_s(b))+half*S.PERIMETER/50)%S.PERIMETER;th=float(S.th_at_s(s))
        E=S.edge_xy(th);N=S.edge_normal(th)
        for d in [-1,-4,-8,-12,-16,-20,-24,-28,-32,-36]:
            X=E+N*d;best=None
            for nm,(e,n,H) in V.items():
                u=640+F*(X[0]-e)/(H-41);v=360-F*(X[1]-n)/(H-41);c=abs(u-640)+abs(v-360)
                if 10<u<1270 and 40<v<710 and (best is None or c<best[0]):best=(c,nm,u,v)
            if best:
                _,nm,u,v=best;out.setdefault(nm,[]).append([int(round(u)),int(round(v))]);meta.append([nm,len(out[nm])-1,b,half,d,float(th)])
json.dump([dict(name='r'+k[1:],url=URL[k],pts=p) for k,p in out.items()],open('roof_jobs.json','w'));json.dump(meta,open('roof_meta.json','w'))
print({k:len(p) for k,p in out.items()})
