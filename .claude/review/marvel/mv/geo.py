from cam import *
G=json.load(open('osm/geo.json'))
FP=np.array(G['ways']['22971441'])
PITCH=np.array(G['ways']['10583685'])
SC=PITCH[:-1].mean(0)
def polar(poly,c=SC):
    a=np.arctan2(poly[:,1]-c[1],poly[:,0]-c[0]);r=np.hypot(poly[:,0]-c[0],poly[:,1]-c[1]);o=np.argsort(a);return a[o],r[o]
P=json.load(open('c1.json'))['p']
