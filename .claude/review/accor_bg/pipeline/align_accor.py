"""Align to builder GLB (md5 0137e8e3...): origin -33.847086,151.063400; footprint = max(OSM way, roof_outer, arch feet)+4 m."""
import json,math,os,shutil,numpy as np
SRC='C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/dazzling-margulis-e47fa0/tools/grounds/accor'
os.makedirs('ground',exist_ok=True); shutil.copy(SRC+'/model/accor.glb','ground/accor.glb')
s=open('spec/mk_accor.py').read()
s=s.replace("lat=-33.84722,lon=151.06333","lat=-33.847086,lon=151.063400").replace("ground/accor_placeholder.glb","ground/accor.glb")
open('spec/mk_accor.py','w').write(s)
lat0,lon0=-33.847086,151.063400;KX=111320*math.cos(math.radians(lat0));KY=110540
E=json.load(open('data/accor/osm.json',encoding='utf-8'))['elements']
w=[e for e in E if e['id']==4385777 and e['type']=='way'][0]
P=np.array([((g['lon']-lon0)*KX,(g['lat']-lat0)*KY) for g in w['geometry']])
D=np.vstack([a+(b-a)*t for a,b in zip(P[:-1],P[1:]) for t in np.linspace(0,1,40,endpoint=False)])
ang=(np.degrees(np.arctan2(D[:,1],D[:,0]))%360)//2; r=np.hypot(*D.T)
R=np.array([r[ang==k].max() if (ang==k).any() else 0 for k in range(180)])
ro=np.array(json.load(open(SRC+'/work/plan.json'))['roof_outer']); ro=np.vstack([ro,[ro[0,0]+360,ro[0,1]]])
R=np.maximum(R,np.interp(np.arange(180)*2+1,ro[:,0],ro[:,1]))
for a0,rr in ((10,157),(190,167)):          # arch feet
    for k in range(180):
        if abs(((k*2+1-a0)+180)%360-180)<6: R[k]=max(R[k],rr)
R=R+4
json.dump([round(float(x),2) for x in R],open('data/accor/prep/footprint.json','w')); print('FP',R.min().round(1),R.max().round(1))
