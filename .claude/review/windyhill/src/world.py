import json,numpy as np,math
from cam import R
p=json.load(open('cam84.json'))['p']
C=np.array(p[:3]);M=R(*p[3:6]);fo=p[6];u0,v0=p[7],p[8]
def at_z(u,v,z=0.0):
    d=M.T@np.array([(u-u0)/fo,-(v-v0)/fo,1.0])
    t=(z-C[2])/d[2];X=C+t*d;return [round(float(X[0]),2),round(float(X[1]),2)]
import parts
# heights (m) read from shadows: h = shadow_px/2.75*0.8 (sun ~39 deg from car shadows)
H={'reyn_roof':12.0,'reyn_back':12.0,'hird':7.0,'cook_roof':9.0,'cook_seats':5.0,'n_stand':5.0,
   'nb1':3.5,'nb2':3.5,'croq_hut':3.0,'scoreboard':13.0,'sb_hut':3.0,'crichton':5.0,'sb1':3.0,'sb2':3.0,'sb3':3.0,
   'showers_roof':12.0,'club':4.0,'nw_bldg':4.0,'bowl1':0.0,'bowl2':0.0,'ne_terr_in':0.0}
W={}
for k,pts in parts.P.items():
    h=H.get(k,0.0);W[k]={'h':h,'pts':[at_z(u,v,h) for u,v in pts]}
EXTRA={
 'hill_outer':[(520,110),(560,135),(630,175),(655,195),(653,300),(652,420),(645,480),(625,545),(600,558),(442,562)],
 'east_wall':[(655,192),(653,300),(652,420),(645,480),(625,545),(600,558)],
 'south_wall':[(282,585),(640,628)],
}
for k,pts in EXTRA.items():W[k]={'h':0,'pts':[at_z(u,v,0) for u,v in pts]}
json.dump(W,open('world.json','w'),indent=0)
for k,v in W.items():print(k,v['h'],v['pts'][:2])
