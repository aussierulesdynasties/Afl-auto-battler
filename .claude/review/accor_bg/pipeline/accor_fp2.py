import json,math,numpy as np
lat0,lon0=-33.84722,151.06333;KX=111320*math.cos(math.radians(lat0));KY=110540
E=json.load(open('data/accor/osm.json',encoding='utf-8'))['elements']
w=[e for e in E if e['id']==4385777 and e['type']=='way'][0]
P=np.array([((g['lon']-lon0)*KX,(g['lat']-lat0)*KY) for g in w['geometry']])
# densify, then max radius per 2-degree bucket
D=[]
for a,b in zip(P[:-1],P[1:]):
    for t in np.linspace(0,1,40,endpoint=False): D.append(a+(b-a)*t)
D=np.array(D); ang=(np.degrees(np.arctan2(D[:,1],D[:,0]))%360)//2; r=np.hypot(D[:,0],D[:,1])
R=[float(r[ang==k].max()) if (ang==k).any() else 0 for k in range(180)]
for k in range(180):
    if R[k]==0: R[k]=max(R[k-1],R[(k+1)%180])
import os; os.makedirs('data/accor/prep',exist_ok=True)
json.dump([round(x,2) for x in R],open('data/accor/prep/footprint.json','w')); print('FP',min(R),max(R))
