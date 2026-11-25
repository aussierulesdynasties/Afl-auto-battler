# Compare Google Earth 3D readouts along each 10-degree ray with today's MCG model roof.
import json,math,numpy as np,sys
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/mcg/model')
D=json.load(open('/home/user/Afl-auto-battler/tools/grounds/mcg/model/mcg.json'))
def per(tab):
    t=np.array(tab,float); b=np.r_[t[:,0]-360,t[:,0],t[:,0]+360]; v=np.r_[t[:,1],t[:,1],t[:,1]]
    return lambda q: np.interp(q%360,b,v)
ri,ro,rh=per(D['roof_inner']),per(D['roof_outer']),per(D['roof_h'])
R=json.load(open('sweep_all.json')); TURF=8
rays={}
for f,v,s in R:
    i=int(f[-8:-4])
    if i==0 or v is None: continue
    ray=(i-1)//29; rays.setdefault(ray*10,[]).append(v)
out={}
for b in sorted(rays):
    P=rays[b]; P.sort(key=lambda p: math.hypot(p[0],p[1]))
    rr=[math.hypot(p[0],p[1]) for p in P]; zz=[p[2]-TURF for p in P]
    roof=[(r,z) for r,z in zip(rr,zz) if z>=zz[0]+15 and z>18]
    if not roof: print(b,'no roof'); continue
    # roof points: those within 6 m of the max height band
    zmax=max(z for r,z in roof); band=[(r,z) for r,z in roof if z>=zmax-7]
    rf=min(r for r,z in band); rb=max(r for r,z in band)
    zf=np.mean([z for r,z in band if r<rf+8]); zb=np.mean([z for r,z in band if r>rb-8])
    m_rf,m_rb,m_h=float(ri(b)),float(ro(b)),float(rh(b))+4.2
    out[b]=dict(ge_front_r=rf,ge_back_r=rb,ge_front_z=zf,ge_back_z=zb,model_front_r=m_rf,model_back_r=m_rb,model_z=m_h)
    print('%3d  front r GE %5.1f model %5.1f | back r GE %5.1f model %5.1f | z GE %4.1f..%4.1f model %4.1f'%(b,rf,m_rf,rb,m_rb,zf,zb,m_h))
json.dump(out,open('cmp.json','w'),indent=1)
