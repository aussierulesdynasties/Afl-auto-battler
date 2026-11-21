# Traeger Park exterior, field frame metres (x east, y north, z up; pitch centre origin).
import numpy as np,json,math
from cam import load,at_z,at_vline
P=load()
prims=[]
def add(kind,name,mat,**kw):prims.append(dict(kind=kind,name=name,mat=mat,**kw))
def bp(u,v,z=0.0):return [float(a) for a in at_z(P,u,v,z)[:2]]
def lerp(a,b,t):return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]
# ---------- grandstand roof: photo corners at front 11.5 m, back 6.0 m ----------
hF,hB=11.5,6.0
RB_S,RF_S,RB_N,RF_N=bp(49,706,hB),bp(233,657,hF),bp(107,626,hB),bp(269,579,hF)
add('slab','gs_roof','roof_white',pts=[RB_S+[hB],RF_S+[hF],RF_N+[hF],RB_N+[hB]],th=0.35)
yS,yN=-14.7,19.5
add('prism','gs_base','base_dark',fp=[[-73.5,yS],[-73.5,yN],[-78.5,yN],[-78.5,yS]],z0=0,ztop=[2.1,2.1,4.0,4.0])
add('prism','gs_upper','glass',fp=[[-77.5,yS],[-77.5,yN],[-88,yN],[-88,yS]],z0=5.6,ztop=[10.3,10.3,7.9,7.9])
add('prism','gs_back','wall_cream',fp=[[-78.5,yS],[-78.5,yN],[-95,yN],[-95,yS]],z0=0,ztop=5.6)
add('prism','gs_stair','wall_white',fp=[[-88,yS-4],[-88,yS],[-96,yS],[-96,yS-4]],z0=0,ztop=7.0)
# ---------- north block between stand and clubrooms ----------
add('prism','nb','wall_cream',fp=[[-74.0,yN],[-74.0,37],[-90,37],[-90,yN]],z0=0,ztop=6.5)
# ---------- TIO clubrooms: blue skillion roof, photo corners at front 4.0 m, back 5.75 m ----------
cF,cB=4.0,5.75
BS,BN,FN,FS=bp(234.5,562.3,cB),bp(314.5,524.1,cB),bp(354.5,536.8,cF),bp(274.5,575,cF)
add('slab','cr_roof','roof_blue',pts=[BS+[cB],FS+[cF],FN+[cF],BN+[cB]],th=0.3)
fi=[lerp(FS,BS,2.5/math.dist(FS,BS)),lerp(FN,BN,2.5/math.dist(FN,BN))]
add('prism','cr_body','brick',fp=[BS,fi[0],fi[1],BN],z0=0,ztop=[cB-0.1,cF+0.6,cF+0.6,cB-0.1])
for t in np.linspace(0.04,0.96,6):
    q=lerp(lerp(FS,FN,t),lerp(BS,BN,t),0.4/math.dist(FS,BS))
    add('pole','cr_post','post',base=q,z1=cF,r0=0.08,r1=0.08)
# ---------- boundary fence: photo picks + west side from the boundary line pushed out 5.5 m ----------
# boundary fence: traced on the Google satellite all round (ringfit.py: 51 fence points read off z19/z20, the OSM pitch
# outline fitted to them fills the stretches hidden in shadow); 1-degree steps round the centre (5, 10)
ring=json.load(open('ring_sat.json'))
add('ground_ref','fence_ring','none',pts=ring)
def fmat(a,b):
    x=(a[0]+b[0])/2;y=(a[1]+b[1])/2
    if y>0 and -25<x<22:return 'hoard_blue'
    if x>=35 or (x>=22 and y>0):return 'hoard'
    if y<0 and -8<x<35:return 'hoard_white'
    # west side: open chain-link in front of the stand and clubrooms; the white backing sheet only on the south-west arc (c05)
    if y<-22:return 'rail'
    return 'rail_open'
# no boundary fence along the stand and clubroom front (c05, w04: the turf runs to the bench feet). The ring stops at
# index 124 north of the clubrooms (satellite g19: the fence line with its shadow starts there) and at index 197 south
# of the stand, where a low open chain-link turns in to the arch's north edge (w04 fence zoom, c05)
import stand as _st0
path=ring[197:]+ring[:125]
runs=[]
for i in range(len(path)-1):
    a,b=path[i],path[i+1];m=fmat(a,b)
    if runs and runs[-1][0]==m:runs[-1][1].append(b)
    else:runs.append([m,[a,b]])
runs.append(['rail_open',[ring[197],_st0.W(10.9,_st0.P['pl_t'],0)[:2]]])
for m,pts in runs:add('fence','fence_'+m,m,pts=pts,h=1.0 if m.startswith('rail') else 1.1,open=True)
# south forecourt: black bow-top fence round the grassed yard south of the stand (satellite z20 trace; c05)
add('fence','fence_bow','rail_bow',pts=[[-82.6,-18.0],[-82.5,-24.7],[-65.9,-20.7]],h=1.2,open=True)
# grey vertical-bar palisade round the stair tower and the south door (c08, c09), stand frame s -5.8, t 1.5..23.5
import stand as _st
add('fence','fence_pal','rail_pal',pts=[_st.W(-1.0,1.5,0)[:2],_st.W(-5.8,1.5,0)[:2],_st.W(-5.8,23.5,0)[:2],_st.W(-1.0,23.5,0)[:2]],h=1.8,open=True)
# ---------- outer east wall ----------
# east_wall removed (director 2026-11-19 "Remove wall": it ran through the tennis courts on the satellite)
# ---------- scoreboard: legs at photo (787,485)/(825,485), board 479..449 ----------
L=bp(787,485);Rr=bp(825,485);M=lerp(L,Rr,.5)
zb=float(at_vline(P,806,479,M)[2]);zt=float(at_vline(P,806,449,M)[2])
add('board','scoreboard','screen',a=L,b=Rr,z0=zb,z1=zt)
for q in(L,Rr):add('pole','sb_leg','post',base=q,z1=zb,r0=0.15,r1=0.15)
# ---------- east shelter: white roof at 3 m ----------
# east_shelter dropped (lead ruling via the secretary 2026-11-18: no photo shows it)
# add('slab','east_shelter','roof_white',pts=[bp(u,v,3.0)+[3.0] for u,v in[(1091,500),(1106,500),(1127,515),(1112,517)]],th=0.2)
# ---------- green shed (satellite footprint, gable) ----------
add('gable','shed','roof_green',fp=[[17,-105],[85,-105],[85,-119],[17,-119]],eave=4.0,ridge=6.0)
add('gable','shed_annex','roof_green',fp=[[2,-106],[17,-106],[17,-119],[2,-119]],eave=3.0,ridge=4.5)
# ---------- trees: canopy centre pixel at 7 m ----------
TR=[(300,900,120),(115,770,40),(215,770,30),(380,470,22),
    (1020,490,30),(1328,826,80)]
for u,v,rp in TR:
    c=at_z(P,u,v,7.0);d=float(np.linalg.norm(c-P[:3]));r=rp*d/P[6]
    add('tree','tree','tree',xy=[float(c[0]),float(c[1])],r=r,h=7+r*0.6,cd=r*1.2)
# ---------- towers ----------
T=json.load(open('towers.json'))
SATB={'FL_pole':[-52.0,97.5],'FL_2':[-61.0,75.0],'NL_pole':[-58.5,-72.5]}   # satellite: head seen from above / shadow foot
T0={k:dict(v) for k,v in T.items()}
for k in SATB:T[k]['base']=SATB[k]
for k,v in T.items():
    b=v['base'];lat=k.endswith('lat') or k.endswith('_2')   # c05: FL_2 is a lattice mast with a square head; FR_2 the same (era tower, unphotographed close)
    r0,r1={'NL_pole':(1.1,0.5),'R_pole':(1.1,0.5),'FL_pole':(0.9,0.45),'FR_pole':(0.9,0.45),'FL_2':(0.7,0.35),'FR_2':(0.7,0.35)}.get(k,(1.1,0.7))
    add('lattice' if lat else 'pole',k,'steel',base=b,z1=float(v['hbot']),r0=r0,r1=r1)
    add('head',k+'_head','lamps',base=b,z0=float(v['hbot']),z1=float(v['top']),w=6.5,lat=lat)
json.dump(prims,open('prims.json','w'),indent=0)
if __name__=='__main__':
    print('cr',BS,BN,FN,FS,'sb',L,Rr,zb,zt)
    print('trees',[(round(p['xy'][0]),round(p['xy'][1]),round(p['r'],1)) for p in prims if p['kind']=='tree'])
# ---------- pole signs (photo boxes on the pole) ----------
SG=[('FL_pole',(396,415,409,430),'sign_tio',0.9),('FR_pole',(886,904,395,415),'sign_tio',0.9),('NL_pole',(165,202,830,875),'sign_white',1.1)]
for k,(u0,u1,v0,v1),m,rr in SG:
    b0=T0[k]['base'];b=T[k]['base'];z0=float(at_vline(P,(u0+u1)/2,v1,b0)[2]);z1=float(at_vline(P,(u0+u1)/2,v0,b0)[2])
    d=float(np.linalg.norm(np.array(b0+[(z0+z1)/2])-P[:3]));w=(u1-u0)*d/P[6]
    add('sign',k+'_sign',m,base=b,z0=z0,z1=z1,w=w,off=rr+0.1)
json.dump(prims,open('prims.json','w'),indent=0)
if __name__=='__main__':print([(p['name'],round(p['z0'],1),round(p['z1'],1),round(p['w'],1)) for p in prims if p['kind']=='sign'])
