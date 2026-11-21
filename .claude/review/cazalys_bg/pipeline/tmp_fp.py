# TEMP footprint until the ground GLB exists: OSM Cazalys sports_centre outline -> radius per 1 degree (probe_outline format)
import json,math,numpy as np
s=json.load(open('spec/cazalys.json'));KX=111320*math.cos(math.radians(s['lat']));KY=110540
e=[e for e in json.load(open('data/cazalys/osm.json',encoding='utf-8'))['elements'] if e.get('id')==614183153][0]
P=np.array([((g['lon']-s['lon'])*KX,(g['lat']-s['lat'])*KY) for g in e['geometry']])
Q=np.concatenate([P[i]+(P[i+1]-P[i])*np.linspace(0,1,200)[:,None] for i in range(len(P)-1)])
b=(np.degrees(np.arctan2(Q[:,1],Q[:,0]))%360).astype(int)%360;R=np.zeros(360)
np.maximum.at(R,b,np.hypot(Q[:,0],Q[:,1]))
json.dump([round(float(x),2) for x in R],open('data/cazalys/prep/footprint.json','w'));print(R.min(),R.max())
