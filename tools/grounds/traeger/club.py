# TIO clubrooms north of the grandstand. Club frame: u along the front (0 = blue building's north end, increasing south),
# w back (west), z up. Front line from the aerial wall base (350,548)->(305,585) at z 0.
# Read off: aerial (plan, blue wall 2.6 m via vertical lines), satellite (blue strip ~7 m deep, white strip ~4.5 m,
# green hip roof behind), w09 (heights in door units), w04 (green eave ~6.6 m at its south-east corner).
import json,numpy as np
# front line moved onto the satellite with the stand (same rigid shift)
P0=np.array([-61.69,69.88]);EU=np.array([-67.92,49.92])-P0;EU/=np.linalg.norm(EU);EW=np.array([EU[1],-EU[0]])
if EW[0]>0:EW=-EW
C=dict(blue_u1=24.0,blue_d=15.6,blue_zf=2.6,blue_ridge_w=8.0,blue_zr=4.9,ovh=0.6,
       bal_u0=20.9,bal_u1=29.5,bal_d=4.5,bal_floor=3.2,bal_z=6.3,
       g_s0=31.6,g_s1=45.0,g_t0=7.3,g_t1=21.6,g_eave=6.0,g_pitch=18.0,g_ridge_t=16.5,g_rot=14.0,ac=[(38.6,18.5),(41.2,18.5)])
FR=[P0,EU,EW]
def X(u,w,z):p=FR[0]+u*FR[1]+w*FR[2];return [float(p[0]),float(p[1]),float(z)]
G=[]
def mesh(name,mat,V,F,uvmode='tile'):G.append(dict(name=name,mat=mat,V=V,F=F,uvm=uvmode))
def box(name,mat,u0,u1,w0,w1,z0,z1,top=True,bottom=False):
    V=[X(u,w,z) for z in (z0,z1) for (u,w) in ((u0,w0),(u1,w0),(u1,w1),(u0,w1))]
    F=[[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]+([[4,5,6,7]] if top else [])+([[3,2,1,0]] if bottom else [])
    mesh(name,mat,V,F)
def quad(name,mat,pts,mode='tile'):mesh(name,mat,[X(*p) for p in pts],[[0,1,2,3]],mode)
c=C
# ---- blue building: single storey gable; front slope blue (sponsor), back slope green with the yellow band ----
U1,Dp,zf,wr,zr,o=c['blue_u1'],c['blue_d'],c['blue_zf'],c['blue_ridge_w'],c['blue_zr'],c['ovh']
box('blue_body','club_render',0,U1,0,Dp,0,zf,top=False)
quad('blue_front','blue_front',[(U1,-0.01,0),(0,-0.01,0),(0,-0.01,zf),(U1,-0.01,zf)],'panel')
def rz(w):return zf+0.1+(zr-zf-0.1)*(1-abs(w-wr)/wr) if w<=wr else zf+0.1+(zr-zf-0.1)*(1-(w-wr)/(Dp-wr))
for uu in (0.0,U1):mesh('blue_gable','club_render',[X(uu,0,zf),X(uu,wr,rz(wr)),X(uu,Dp,zf)],[[0,1,2]])
quad('blue_roof','roof_blue_club',[(U1,-o,rz(0)-(zr-zf)*o/wr),(-o,-o,rz(0)-(zr-zf)*o/wr),(-o,wr,zr),(U1,wr,zr)],'panel')
quad('blue_roof_back','roof_back_club',[(-o,wr,zr),(-o,Dp+o,zf+0.1-(zr-zf)*o/(Dp-wr)),(U1,Dp+o,zf+0.1-(zr-zf)*o/(Dp-wr)),(U1,wr,zr)],'panel')
quad('blue_fascia','fascia',[(U1,-o,zf-0.15),(-o,-o,zf-0.15),(-o,-o,zf+0.05),(U1,-o,zf+0.05)])
quad('blue_soffit','roof_soffit',[(-o,-o,zf),(U1,-o,zf),(U1,0,zf+0.02),(-o,0,zf+0.02)])
# ---- glass balcony block between the blue building and the green building (white flat roof) ----
u0,u1,d=c['bal_u0'],c['bal_u1'],c['bal_d']
box('bal_ground','club_render',u0,u1,0.0,d,0,c['bal_floor'],top=False)
quad('bal_front_lo','bal_front_lo',[(u1,-0.01,0),(u0,-0.01,0),(u0,-0.01,c['bal_floor']),(u1,-0.01,c['bal_floor'])],'panel')
box('bal_slab','cream',u0,u1,-0.2,d,c['bal_floor']-0.25,c['bal_floor'],bottom=True)
quad('bal_back_blue','bal_back_blue',[(u1,d,c['bal_floor']),(u0,d,c['bal_floor']),(u0,d,c['bal_z']),(u1,d,c['bal_z'])])
box('bal_roof','steel_white',u0,u1,-0.3,d,c['bal_z']-0.3,c['bal_z'],bottom=True)
box('bal_end','club_render',u0-0.25,u0,0,d,c['bal_floor'],c['bal_z']-0.3)
for uu in np.linspace(u0+0.15,u1-0.15,5):box('bal_post','rear_dark',uu-0.07,uu+0.07,-0.15,0.0,c['bal_floor'],c['bal_z']-0.3)
quad('bal_glass','glass_bal',[(u1,-0.08,c['bal_floor']),(u0,-0.08,c['bal_floor']),(u0,-0.08,c['bal_floor']+1.1),(u1,-0.08,c['bal_floor']+1.1)],'panel')
# ---- green building: two storeys, gable roof, ALIGNED WITH THE STAND (w04 gable end fits plane s=32:
#      eave t 7.8 z 6.0, apex t 15.0 z 8.55); recessed upper balcony with dark rails along the front ----
ST=json.load(open('stand.json'));Oa,Aa,Bb=np.array(ST['O']),np.array(ST['a']),np.array(ST['b'])
# w04: eave and ridge both climb northward on a stand-parallel plane, so the block turns g_rot deg toward the club line
dl=np.radians(c['g_rot']);A2=Aa*np.cos(dl)-Bb*np.sin(dl);B2=Bb*np.cos(dl)+Aa*np.sin(dl);PV=Oa+c['g_s0']*Aa+c['g_t0']*Bb
FR[:]=[PV-c['g_s0']*A2-c['g_t0']*B2,-A2,B2]   # u=-s, w=t about the s0/t0 corner, rotated
g0,g1,w0,w1=-c['g_s1'],-c['g_s0'],c['g_t0'],c['g_t1'];fl=c['bal_floor'];bd=1.6
wm=c['g_ridge_t'];e=0.6;vo=0.4   # w04 ridge back-projects to t 16-17, z ~9.2
# w04 fit (fg2.py): eave EDGE z 6.0 at s 31.2 t 6.7, pitch 18 deg, gable parallel to the stand
k=float(np.tan(np.radians(c['g_pitch'])));ze=c['g_eave']+k*e;zr2=c['g_eave']+k*(wm-(w0-e))
box('green_body','club_brick',g0,g1,w0+bd,w1,0,ze,top=False)
box('green_lower','club_brick',g0,g1,w0,w0+bd,0,fl,top=False)
quad('green_front_lo','green_front_lo',[(g1,w0-0.01,0),(g0,w0-0.01,0),(g0,w0-0.01,fl),(g1,w0-0.01,fl)],'panel')
for uu in (g0,g1):
    mesh('green_gable','club_weather',[X(uu,w0,ze),X(uu,wm,zr2),X(uu,w1,ze)],[[0,1,2]])
    quad('green_end_upper','club_weather',[(uu,w0,fl),(uu,w0+bd,fl),(uu,w0+bd,ze),(uu,w0,ze)])
box('green_balc_floor','cream',g0,g1,w0-0.1,w0+bd,fl-0.25,fl)
for z in (fl+1.05,fl+0.1):box('green_rail','rear_dark',g0,g1,w0+0.02,w0+0.1,z-0.06,z)
for uu in np.arange(g0+0.05,g1,0.14):box('green_bal','rear_dark',uu,uu+0.025,w0+0.04,w0+0.08,fl+0.1,fl+1.0,top=False)
for uu in np.linspace(g0+0.1,g1-0.1,7):box('green_post','rear_dark',uu-0.07,uu+0.07,w0,w0+0.14,fl,ze)
for uu,ww in c['ac']:pass
for nm,ws,we in (('green_roof_f',w0-e,wm),('green_roof_b',w1+e,wm)):
    zs=zr2-k*abs(wm-ws) if ws<wm else ze-k*e
    pts=[(g1+vo,ws,zs),(g0-vo,ws,zs),(g0-vo,wm,zr2),(g1+vo,wm,zr2)]
    pts=pts[::-1]  # both slopes face up (the front slope was wound down, so its pale soffit showed on top)
    quad(nm,'roof_green',pts)
    quad(nm+'_u','roof_soffit',pts[::-1])
    quad('green_fascia','fascia',[(g0-vo,ws,zs-0.22),(g1+vo,ws,zs-0.22),(g1+vo,ws,zs),(g0-vo,ws,zs)])
for uu,sg in ((g0-vo,-1),(g1+vo,1)):
    for ws in (w0-e,w1+e):
        zs=zr2-k*abs(wm-ws) if ws<wm else ze-k*e;quad('green_barge','fascia',[(uu,ws,zs-0.2),(uu,wm,zr2-0.2),(uu,wm,zr2),(uu,ws,zs)])
for s0_,t0_ in c['ac']:   # measured in the stand frame (bp.py, plane t 18.5); convert into the turned frame
    Wp=Oa+s0_*Aa+t0_*Bb-PV;s_=c['g_s0']+Wp@A2;t_=c['g_t0']+Wp@B2
    uu=-s_;zr_=zr2-(zr2-ze+k*e)*(t_-wm)/(w1+e-wm);box('ac_unit','ac_unit',uu-0.85,uu+0.85,t_-0.6,t_+0.6,zr_-0.3,10.5)   # w04: 1.7 m wide, tops z 10.5
FR[:]=[P0,EU,EW]
# ---- UVs in metres (tiled) or 0..1 (panel), club frame ----
T=json.load(open('tex3/tex.json'));TILE=T['TILE']
def cf(V):V=np.array(V,float);d=V[:,:2]-P0;return np.c_[d@EU,d@EW,V[:,2]]
for m in G:
    Q=cf(m['V']);UV=[]
    for f in m['F']:
        Pq=Q[f];n=np.abs(np.cross(Pq[1]-Pq[0],Pq[2]-Pq[0]))
        ax=(0,1) if n[2]>=n[0] and n[2]>=n[1] else ((0,2) if n[1]>=n[0] else (1,2))
        if m['uvm']=='panel':
            lo=Pq.min(0);sp=np.maximum(Pq.max(0)-lo,1e-6)
            UV.append([[float(1-(Pq[k,ax[0]]-lo[ax[0]])/sp[ax[0]]),float((Pq[k,ax[1]]-lo[ax[1]])/sp[ax[1]])] for k in range(len(f))])
        else:
            tu,tv=TILE.get(m['mat'],[2,2])
            UV.append([[float(Pq[k,ax[0]]/tu),float(Pq[k,ax[1]]/tv)] for k in range(len(f))])
    m['UV']=UV
json.dump(dict(G=G,C=C,P0=P0.tolist(),EU=EU.tolist(),EW=EW.tolist()),open('club_uv.json','w'))
print(len(G),'club meshes; EU',EU.round(3),'EW',EW.round(3))
