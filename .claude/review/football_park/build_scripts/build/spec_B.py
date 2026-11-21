# Football Park 2001-2013 (photo B, Alamy A1K6CR). t: 0 west, 90 south, 180 east, 270 north. Profiles: (d,z) x6.
import json,os
K=json.load(open(os.path.join(os.path.dirname(__file__),'keysB.json')))
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
    o=lin(K['e_roof_out'],t);g=48.0
    return [0,1, 1.5,1.2, lin(K['e_roof_in'],t)-0.5,4.5, o-0.5,4.5, o,4.5, g,0]
def ngp(t):
    b=lin(K['ng_base'],t);return [0,1, 1.5,1.2, b-7,19, b-3,19, b-0.1,20, b,0]
BOWL=[(322,WEST),(35,WEST),(45,SOUTH),(135,SOUTH)]+[(t,eastp(t)) for t in range(150,236,6)]+[(t,ngp(t)) for t in (258,266,273,282,292,300,306)]
def bowl_mats(t):
    seat='seat_navy' if (t>=318 or t<=38) else 'seat_lb'
    back='west_back' if (t>=318 or t<=38) else ('deck' if not (250<=t<=315) else 'facade')
    face='embank' if (138<=t<=240 or 40<=t<=135) else ('facade' if 240<t<318 else 'west_back')
    return ['apron',seat,'deck',back,face]
STRIPS=[
 dict(t0=322,t1=35,keys=skeys('w_roof_in','w_roof_out',26.5,25,322,35),mat='west_roof',thick=1.0,mat_under='tan_under'),
 dict(t0=148,t1=236,keys=skeys('e_roof_in','e_roof_out',11.4,11.5,148,236),mat='tan',thick=0.5,mat_under='tan_under'),
 dict(t0=257,t1=322,keys=[(t,([skeys('w_roof_in','w_roof_out',26.5,25,322,35)[0][1][0],p[1],p[2],p[3]] if t==322 else p)) for t,p in skeys('ng_roof_in','ng_eave',26.5,26.5,257,322)],mat='white',thick=1.0,mat_under='tan_under'),
 dict(t0=45,t1=135,keys=[(0,[26,12,34,12])],mat='box_roof',thick=1.2,mat_edge='signs',mat_under='tan_under'),
]
WALLS=[dict(t0=257,t1=306,keys=[(t,[lin(K['ng_base'],t)-0.1,20,26.5]) for t in range(257,307,3)],mat='glass'),dict(t0=45,t1=135,keys=[(0,[26,7,11.6])],mat='glass')]
COLUMNS=[dict(t0=t,t1=t,step=1,d=lin(K['e_roof_out'],t)-0.8,z0=4.5,z1=11.2,r=0.3,mat='col') for t in range(150,236,4)]
BOXES=[dict(t=244,d=28,w=20,dep=4,z0=6,z1=16,mat='box',mat_front='screen'),dict(t=163,d=64,w=34,dep=24,z0=0,z1=12,mat='admin')]
APRON=[(0,360,30,75,'pink')]
T=json.load(open(os.path.join(os.path.dirname(__file__),'../b/towers.json')))
TOWERS=T['T'];TOWER=dict(H=61,r0=1.2,r1=0.6,head_w=7,head_h=18,tilt=0)
SUN=dict(dir=(-0.45,0.55,-0.7),energy=4.0)
import sys as _s;_s.path.insert(0,os.path.join(os.path.dirname(__file__),'../b'))
from camlib import at_z as _az
_p=json.load(open(os.path.join(os.path.dirname(__file__),'../b/camB.json')))['p']
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
APRON=[(140,330,40,58,'pink'),(330,140,38,46,'deck')]

# apron: pink pavers' outer edge traced in photo B (pixels projected to z 0 with camB); far side unchanged
APRON=[]
_kedge=[(t%360,prof[-2]+3.0) for t,prof in BOWL]   # stadium only (director 2026-11-18): paving stops 3 m past the stand foot
APRONK=[(140,330,'pink',[(0,30)],_kedge),(330,140,'deck',[(0,30)],_kedge)]
PRISMS[2]=dict(PRISMS[2],mat_top='nw_roof',uv_box=True)
# every stadium structure stands on paving: the edge also runs 3 m past buildings and light-tower bases (apronfit.py)
import importlib.util as _ilu,os as _os
_af=_ilu.spec_from_file_location('apronfit',_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'apronfit.py'));_AF=_ilu.module_from_spec(_af);_af.loader.exec_module(_AF)
_kedge=_AF.fit(_kedge,PRISMS,BOXES,TOWERS)
APRONK=[(a,b,m,ki,_kedge) for a,b,m,ki,ko in APRONK]
# join fix: the north grandstand's glass back wall runs on from 306 to 322 along the bowl's back top, up to the roof, so roof, wall and west stand meet with no slot
_p306=dict(BOWL)[306];_p322=dict(BOWL)[322]
def _bk(t):w=(t-306)/16;return [_p306[i]+(_p322[i]-_p306[i])*w for i in (8,9)]
WALLS[0]=dict(WALLS[0],t1=322,keys=WALLS[0]['keys']+[(t,[_bk(t)[0],_bk(t)[1],26.5]) for t in range(308,323,2)])
