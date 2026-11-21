import json,math
import numpy as np
s=json.load(open('spec/riverway.json'));lat0,lon0=s['lat'],s['lon'];KX=111320*math.cos(math.radians(lat0));KY=110540
d=json.load(open('data/riverway/osm.json'))
nodes={e['id']:(e['lon'],e['lat']) for e in d['elements'] if e['type']=='node'}
w=[e for e in d['elements'] if e['id']==175599089][0]
P=np.array([((g['lon']-lon0)*KX,(g['lat']-lat0)*KY) for g in w['geometry']])
R=np.zeros(180)
for i in range(len(P)-1):
  for t in np.linspace(0,1,40):
    x,y=P[i]*(1-t)+P[i+1]*t;b=int(math.degrees(math.atan2(y,x))%360//2)%180;R[b]=max(R[b],math.hypot(x,y))
json.dump([round(float(x),2) for x in R],open('data/riverway/prep/footprint.json','w'));print('FP',R.min(),R.max(),P.mean(0))
