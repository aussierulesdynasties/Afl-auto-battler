# Football Park 1991-2000 (photo A, Getty 1997 aerial). Same builder; keys from photo A. No Northern Grandstand, no screen. t: 0 west, 90 south, 180 east, 270 north. Profiles: (d,z) x6.
import json,os
K=json.load(open(os.path.join(os.path.dirname(__file__),'keysA.json')))
def lin(ks,t):
    ks=sorted(ks)
    if t<=ks[0][0]:return ks[0][1]
    if t>=ks[-1][0]:return ks[-1][1]
    for (a,da),(b,db) in zip(ks,ks[1:]):
        if a<=t<=b:return da+(db-da)*(t-a)/(b-a)
def unwrap(ks,ref):return [[(t-ref+180)%360-180+ref,d] for t,d in ks]
def skeys(kin,kout,zin,zout,t0,t1,step=4):
    mid=(t0+((t1-t0)%360)/2);a=unwrap(K[kin],mid);b=unwrap(K[kout],mid);out=[];span=(t1-t0)%360;n=int(span/step)
    for i in range(n+1):
        t=t0+span*i/n;tt=(t-mid+180)%360-180+mid;out.append((t%360,[lin(a,tt),zin,lin(b,tt),zout]))
    return out
COL={'turf':(98,124,58),'apron':(150,150,140),'seat_lb':(95,160,195),'seat_navy':(25,45,70),'deck':(175,175,168),'facade':(225,215,200),
 'embank':(185,190,180),'pink':(196,148,120),'tan':(214,196,152),'tan_under':(120,110,90),'white':(232,232,234),'glass':(40,50,60),
 'col':(225,225,225),'tower':(205,205,205),'lamps':(250,250,240),'box':(230,230,232),'admin':(205,192,185),'screen':(30,35,40),'west_roof':(220,208,192),'west_back':(200,195,185)}
WEST=[0,1, 1.5,1.2, 36,15, 39,15, 39.5,24, 40,0]
SOUTH=[0,1, 1.5,1.2, 26,7, 34,7, 35,7, 46,0]
EAST=[0,1, 1.5,1.2, 24,4.5, 33,4.5, 33.5,4.5, 48,0]
NG=[0,1, 1.5,1.2, 42,19, 46,19, 48.5,20, 48.6,0]
def eastp(t):
    o=lin(K['e_roof_out'],t);g=o+0.6   # photo A: the concourse starts at the roof's column line (traced grass line 6-15 m beyond)
    return [0,1, 1.5,1.2, lin(K['e_roof_in'],t)-0.5,4.5, o-0.5,4.5, o,4.5, g,0]
def ngp(t):
    b=lin(K['ng_base'],t);return [0,1, 1.5,1.2, b-7,19, b-3,19, b-0.1,20, b,0]
BOWL=[(322,WEST),(35,WEST),(45,SOUTH),(135,SOUTH)]+[(t,eastp(t)) for t in range(150,317,6)]
def bowl_mats(t):
    seat='seat_navy' if (t>=318 or t<=38) else 'seat_lb'
    back='west_back' if (t>=318 or t<=38) else 'deck'
    face='embank' if (138<=t<=317 or 40<=t<=135) else 'west_back'
    return ['apron',seat,'deck',back,face]
STRIPS=[
 dict(t0=318,t1=35,keys=skeys('w_roof_in','w_roof_out',26.4,25,318,35),mat='west_roof',thick=1.0,mat_under='tan_under'),
 dict(t0=148,t1=317,keys=skeys('e_roof_in','e_roof_out',11.4,11.5,148,317),mat='tan',thick=0.5,mat_under='tan_under'),
 dict(t0=45,t1=135,keys=[(0,[26,12,34,12])],mat='box_roof',thick=1.2,mat_edge='signs',mat_under='tan_under'),
]
WALLS=[dict(t0=45,t1=135,keys=[(0,[26,7,11.6])],mat='glass')]
COLUMNS=[dict(t0=t,t1=t,step=1,d=lin(K['e_roof_out'],t)-0.8,z0=4.5,z1=11.2,r=0.3,mat='col') for t in range(150,317,4)]
BOXES=[dict(t=163,d=64,w=34,dep=24,z0=0,z1=12,mat='admin')]
APRON=[(0,360,30,75,'pink')]
T=json.load(open(os.path.join(os.path.dirname(__file__),'../b/towers.json')))
TOWERS=T['T'];TOWER=dict(H=61,r0=1.2,r1=0.6,head_w=7,head_h=18,tilt=0)
SUN=dict(dir=(-0.45,0.55,-0.7),energy=4.0)
import sys as _s;_s.path.insert(0,os.path.join(os.path.dirname(__file__),'../b'))
from camlib import at_z as _az
_p=json.load(open(os.path.join(os.path.dirname(__file__),'../b/camB.json')))['p']  # buildings traced in B (sharper), checked in A
def _rz(uv,z):X=_az(_p,uv[0],uv[1],z);return (float(X[0]),float(X[1]),z)
# SE admin building: roof outline at 18 m; back walls vertical; front face stepped down to its traced ground line
_adm=[(58.6,535),(98.6,530.7),(101.4,562),(78,566),(55.7,570.7)];_admT=[_rz(q,18) for q in _adm]
_admB=[(_admT[0][0],_admT[0][1],0),(_admT[1][0],_admT[1][1],0),_rz((101.4,598),0),_rz((78,606),0),_rz((57,604),0)]
# NW members building: roof outline at 12 m, vertical walls
_nw=[(410,460.6),(441,455.6),(469,467.8),(452,480),(430,478)];_nwT=[_rz(q,12) for q in _nw]
_admF=[(_admT[2][0],_admT[2][1],14),(_admT[3][0],_admT[3][1],14),(_admT[4][0],_admT[4][1],14),(_admB[4][0],_admB[4][1],14),(_admB[3][0],_admB[3][1],14),(_admB[2][0],_admB[2][1],14)]
PRISMS=[dict(top=_admT,bot=[(x,y,0) for x,y,z in _admT],mat='admin',mat_top='admin_roof'),dict(top=_admF,bot=[(x,y,0) for x,y,z in _admF],mat='admin',mat_top='white'),dict(top=_nwT,bot=[(x,y,0) for x,y,z in _nwT],mat='west_back',mat_top='white')]
BOXES=[b for b in BOXES if b['mat']!='admin']
COL['admin_roof']=(190,200,190)
APRON=[(0,360,38,50,'deck')]
# --- photo A (1997) specifics ---
# Colours sampled from photo A (median 5x5): south roof, tan concourse roof, grey members roof, dark concourse.
COL.update({'embank':(78,76,88),'box':(152,171,194),'tan':(186,175,142),'west_roof':(150,154,170),'deck':(80,78,90)})
# Blocks behind the south roof, traced in A at z 12 (same roof colour)
BOXES=BOXES+[dict(t=94.5,d=42,w=25,dep=14,z0=0,z1=12,mat='box'),dict(t=110,d=47.5,w=5,dep=11,z0=0,z1=12,mat='box'),dict(t=64.5,d=40,w=6,dep=10,z0=0,z1=12,mat='box')]
# South towers re-fitted to photo A (head top read at 61 m); north towers from B (out of A's frame)
TOWERS=dict(TOWERS);TOWERS['SW']=[81.44,83.0];TOWERS['SE']=[-83.68,80.23]

# --- ground round the ground, traced in photo A (pixels of the 407x612 photo) and projected to z 0 with camA ---
import math as _m
_pa=json.load(open(os.path.join(os.path.dirname(__file__),'../a/camA.json')))['p']
from camlib import proj as _proj
def _w(u,v,z=0.0):X=_az(_pa,u,v,z);return (float(X[0]),float(X[1]))
def _td(x,y):
    f=lambda dd:(x/(72.5+dd))**2+(y/(88.5+dd))**2-1;lo,hi=-70.0,900.0
    for _ in range(60):
        m=(lo+hi)/2
        if f(m)>0:lo=m
        else:hi=m
    d=(lo+hi)/2;return _m.degrees(_m.atan2(y/(88.5+d),x/(72.5+d)))%360,d
# concourse outer edge (grass line): north side (photo bottom) and south side (photo top, pink pavers)
_north=[(20,478),(45,495),(80,505),(120,512),(160,516),(200,518),(240,515),(280,507),(300,500)]
_south=[(77,200),(100,187),(127,178),(167,172),(200,170),(250,173),(283,177),(317,187)]
_kn=sorted(_td(*_w(u,v)) for u,v in _north);_ks=sorted(_td(*_w(u,v)) for u,v in _south)
_kout=sorted(_kn+_ks+[(t,50.0) for t in range(0,360,10) if not any(abs((t-a+180)%360-180)<12 for a,_ in _kn+_ks)])
_s0,_s1=_ks[0][0],_ks[-1][0]
APRON=[]
# director 2026-11-18 via the secretary: stadium only; the paved ground stops 3 m past the stand's outer foot (kerbed)
_kedge=[(t%360,prof[-2]+3.0) for t,prof in BOWL]
APRONK=[(_s0,_s1,'pink',[(0,20)],_kedge),(_s1,_s0,'conc',[(0,20)],_kedge)]
# every stadium structure stands on paving: the edge also runs 3 m past buildings and light-tower bases (apronfit.py)
import importlib.util as _ilu,os as _os
_af=_ilu.spec_from_file_location('apronfit',_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'apronfit.py'));_AF=_ilu.module_from_spec(_af);_af.loader.exec_module(_AF)
_kedge=_AF.fit(_kedge,PRISMS,BOXES,TOWERS)
APRONK=[(a,b,m,ki,_kedge) for a,b,m,ki,ko in APRONK]
