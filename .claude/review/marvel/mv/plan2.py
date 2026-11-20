from frame import *
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
G=json.load(open('osm/geo.json'))
def L(id):a=np.array(G['ways'][id]);return loc(np.c_[a,np.zeros(len(a))])
fig,ax=plt.subplots(figsize=(12,12))
for id,c in [('22971441','g'),('23272382','y'),('57019580','r'),('10583685','c')]:
    q=L(id);ax.plot(q[:,0],q[:,1],c+'-',lw=1);
    if id=='22971441':
        for i,(s,t) in enumerate(q[:-1]):ax.text(s,t,str(i),fontsize=7,color='g')
pts={'roofN':[(-93.5,-0.2),(-97.3,7.5),(-96.7,30.5),(-94.0,48.7),(-88.7,64.6),(-82.8,77.4),(-73.7,92.8),(-67.7,98.8)],
'roofS':[(90.5,89.7),(95.6,80.3),(100.0,69.2),(104.0,56.4),(106.0,46.1),(106.1,34.9),(106.8,30.7),(104.5,2.0),(94.4,-19.6)],
'wall':[(-79.9,80.5),(-64.3,93.8),(-49.1,102.5),(66.4,101.1),(83.8,100.3)],
'panel':[(-66.9,110.8),(87.4,105.7),(-69.5,69.3),(84.4,62.4),(-78.1,-56.3),(73.5,-59.4)],
'T1':[(-54.9,94.4),(-50.7,83.8),(-41.4,90.5),(-45.8,100.5)],'T2':[(57.1,88.8),(64.6,83.5),(70.9,91.3),(63.5,97.3)],
'NW':[(-119,48.1),(-113.6,39.8),(-99,48.6),(-104.6,59.1)],'SW':[(109.6,30.6),(122.8,16),(130.3,23),(117.5,36.9)]}
for k,v in pts.items():
    v=np.array(v);ax.plot(v[:,0],v[:,1],'o-' if k in('T1','T2','NW','SW') else 'o',ms=3,label=k)
ax.plot([11.7,11.7,11.7,11.7],[123.5,112,108.4,106],'kx')
ax.set_aspect('equal');ax.grid(True);ax.legend();ax.set_xticks(range(-160,170,20));ax.set_yticks(range(-160,170,20))
plt.savefig('plan2.png',dpi=80)
