# ENGIE Stadium exterior, world metres (x east, y north, z up).
# Usage: blender -b --python build.py -- OUT.glb RENDER.png
import bpy,bmesh,sys,math,json
from mathutils import Vector,Matrix
out,ren=[__import__('os').path.abspath(a) for a in sys.argv[sys.argv.index('--')+1:]]
bpy.ops.wm.read_factory_settings(use_empty=True)
PL=json.load(open('plan.json'));CAM=json.load(open('cam8.json'));c0=(18.4,43.3)
N=len(PL)
me=bpy.data.meshes.new('engie');ob=bpy.data.objects.new('engie',me);bpy.context.scene.collection.objects.link(ob)
def mat(name,rgb,rough=0.8):
    m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*[c**2.2 for c in rgb],1);b.inputs['Roughness'].default_value=rough
    me.materials.append(m);return len(me.materials)-1
GR=mat('grass',(0.36,0.50,0.22));TK=mat('track',(0.47,0.36,0.25));SE=mat('seats',(0.72,0.20,0.20));SD=mat('seats_dark',(0.30,0.16,0.17))
RF=mat('roof',(0.93,0.93,0.92),0.5);FC=mat('facade',(0.45,0.46,0.48));DK=mat('deck',(0.55,0.54,0.52));BL=mat('blue',(0.42,0.50,0.62))
CU=mat('copper',(0.62,0.40,0.24),0.5);LP=mat('lamps',(0.70,0.70,0.68),0.3);RD=mat('red_lattice',(0.75,0.16,0.12),0.5);WH=mat('white',(0.95,0.95,0.95),0.4)
CL=mat('roof_clear',(0.80,0.82,0.84),0.3);TN=mat('tower_tan',(0.74,0.58,0.43),0.6);MD=mat('mesh_dark',(0.40,0.31,0.25),0.7);LB=mat('lamp_backs',(0.35,0.36,0.38),0.5);MP=mat('mesh_panel',(0.74,0.76,0.76),0.6)
_m=me.materials[CL];_m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=0.35
try:_m.surface_render_method='BLENDED'
except Exception:_m.blend_method='BLEND'
DR=mat('dark_roof',(0.24,0.25,0.27),0.6);NR=mat('ne_roof',(0.27,0.28,0.30),0.6)
LV=mat('louvre',(0.62,0.63,0.64),0.6)
CS=mat('clear_strip',(0.87,0.89,0.83),0.4);TC=mat('cladding_tan',(0.69,0.61,0.50),0.6);RR_=mat('red_render',(0.59,0.23,0.20));RU=mat('rust_lattice',(0.52,0.24,0.17),0.6)
BG=mat('building',(0.70,0.69,0.66));SC=mat('screen',(0.08,0.08,0.10),0.2)
DG=mat('dark_glass',(0.20,0.22,0.25),0.15);WR=mat('white_render',(0.91,0.91,0.89));BK=mat('brick',(0.58,0.31,0.23))
OR=mat('panel_orange',(0.89,0.52,0.14),0.5);GN=mat('panel_green',(0.52,0.73,0.20),0.5);DC=mat('dark_clad',(0.31,0.31,0.33),0.6)
MM=mat('membrane',(0.95,0.95,0.94),0.6)
DT=mat('dirt',(0.59,0.46,0.33));BD=mat('boards',(0.78,0.12,0.14));SM=mat('metal_deck',(0.69,0.71,0.73))
BNM=mat('sponsor_band',(0.30,0.36,0.16),0.5)
ML=mat('metal_light',(0.87,0.89,0.87),0.5)
AW=mat('awning',(0.42,0.47,0.55),0.85)   # awnings: blue-grey sheet (photo 62-81, 83-99, 112-129 in their own shade)
BC=mat('blue_clad',(0.44,0.54,0.66),0.6);TM=mat('timber',(0.50,0.32,0.24));MB=mat('members_sign',(0.13,0.16,0.31),0.5)
bm=bmesh.new()
def V(x,y,z):return bm.verts.new((x,y,z))
def quad(a,b,c,d,mi):
    f=bm.faces.new([a,b,c,d]);f.material_index=mi;return f
def P(t,r,z):a=math.radians(t);return (c0[0]+r*math.cos(a),c0[1]+r*math.sin(a),z)
# facade feet (t, r) read off photo.jpg at z 0: north-west block, near stand, south-west corner
FT=[(95.0,105.6),(97.7,105.4),(104.7,104.2),(112.8,102.9),(123.9,106.1),(128.7,106.1),(133.2,105.8),(140.5,107.9),(148.7,112.7),
    (153.7,114.6),(158.6,117.6),(165.4,120.2),(172.1,120.2),(178.6,121.9),(184.6,124.5),(190.2,127.7),(197.7,125.5),(204.2,126.9),
    (212.7,126.3),(220.3,125.4),(222.0,125.6)]
# upper concourse wall set back behind the deck edge (photo: 158.6 -> 6.6 m, 180.6 -> 2.0 m, 148.7 -> ~1.5 m)
SB=[(140,1.5),(148.7,1.5),(158.6,6.6),(166,5.0),(174,3.0),(180.6,2.0),(222,2.0)]
def sback(t):return float(__import__('numpy').interp(t,*zip(*SB)))
def rback(i):
    r=PL[i]
    if r['roof']:
        t=r['t']
        if 95<=t<=222:return float(__import__('numpy').interp(t,*zip(*FT)))  # facade feet, measured off photo.jpg at z 0
        return max(r['roof'][1],r['rg'] or r['roof'][1])
    return ne_out(r['t'])  # NE: concourse behind the seats, outer edge read off the photo at z 8
# NE concourse: paved walkway behind the top row; from t 30 a dark roof band with skylight strips, inner and outer edges
# read off photo columns 150-430 (rows 478-630) at z 8
NRI=[(30,119.3),(34.7,119.1),(41.6,118.6),(49.9,116.9),(58.0,115.4),(86,115.4)]
NRO=[(14,123.0),(28,123.0),(31.7,126.0),(37.5,126.3),(44.9,124.1),(52.8,120.9),(58,120.0),(86,120.0)]
def ne_out(t):return float(__import__('numpy').interp(t,*zip(*NRO)))
def ne_in(t):return float(__import__('numpy').interp(t,*zip(*NRI))) if t>=30 else None
def zback(i):
    r=PL[i]
    return r['roof'][3] if r['roof'] else ne_top(r['t'])[1]
# field: grass to the OSM pitch edge, 4 m surround
# fence offset past the pitch line, measured off photo.jpg at z 0 (fence foot): far stand 12.2-13.3 m, wings 6.7-10.8 m;
# the near side is under the roofs (not visible), kept at 4 m
FOT=[(-110,4.0),(50.6,7.1),(90,4.0),(240,4.0),(252.1,6.7),(262.1,10.8),(336.1,12.6),(345.7,12.2),(354.8,13.3),(385.5,11.7),(392.8,11.2),(399.8,10.2),(410.6,7.1)]
def FO(t):
    import numpy as _n;t=t%360
    return float(_n.interp(t if t>=50.6 else t+360,*zip(*FOT)))
cen=V(c0[0]-8,c0[1]-6,0.0)
for i in range(N):
    # no field surface inside the fence: the game draws the turf (secretary 2026-11-18, ruling b)
    j=(i+1)%N;ti,tj=PL[i]['t'],PL[j]['t'];ri_,rj_=PL[i]['rp'],PL[j]['rp'];fi,fj=ri_+FO(ti),rj_+FO(tj)
    # no fence boards: director's pick C "no boards" (secretary 2026-11-18); the bowl's front wall is the bare fence
# seating bowl: fence wall, then the rake up to the back
# north-east open stand (photo grid, aisles at photo columns 490-725 sectioned on their radial planes): a 2.0 m front wall,
# the rake rising ~40 deg to the top row at rp+15-18 m, z 6.8-8.2; a walkway at the top-row level behind it.
# The players' race splits the stand at t 43.4-50.7: concrete apron at the wall top, a dark tunnel under a walkway bridge at rp+15.7
NEO=[(14,17.5),(25.5,17.8),(32.8,16.8),(39.8,16.9),(51.2,14.8),(86,14.8)]
NEZ=[(14,8.2),(25.5,8.2),(32.8,6.8),(39.8,7.2),(51.2,7.3),(86,7.3)]
def ne_top(t):
    import numpy as _n;return float(_n.interp(t,*zip(*NEO))),float(_n.interp(t,*zip(*NEZ)))
def is_race(t):return 43.4<=t<=50.7
def bowl(i):
    r=PL[i];t=r['t'];rf=r['rp']+FO(t)+0.3;rb=rback(i)-3
    if r['roof']:
        ri,ro,zi,zo=r['roof'];zb=min(zi,zo)-3.0
        if t>=290 or t<20:   # east two-tier stand: red lower tier, dark upper tier
            rm=rf+0.45*(rb-rf);return [(rf,0,FC),(rf,1.5,SE),(rm,8.0,FC),(rm,9.5,SE),(rb,max(zb,17.0),None)]
        return [(rf,0,FC),(rf,1.5,SE),(rb,max(zb,6.0),None)]
    o,zt=ne_top(t)
    if is_race(t):return [(rf,0,FC),(rf,2.0,TK),(r['rp']+15.7,2.0,DC),(r['rp']+15.7,zt,None)]
    return [(rf,0,FC),(rf,2.0,SE),(r['rp']+o,zt,None)]
# upper-tier vomitories on the east stand: six openings every ~10.8 deg (photo columns 927-1612, rows 420-472), 2.0 m wide,
# from 30% to 70% of the rake; a level tunnel floor runs 3 m in under the rows behind
VOM=[5.4,355.5,344.7,333.5,322.4,311.8];VS0,VS1,VW=0.3,0.7,1.0
def vom_cut(ti,tj,A,B,C,D,mi):
    dt=(tj-ti+180)%360-180;cuts=[]
    for tv in VOM:
        fc=((tv-ti+180)%360-180)/dt;hw=math.degrees(VW/(A-Vector((c0[0],c0[1],A.z))).length)/abs(dt)
        if fc+hw>0 and fc-hw<1:cuts.append((max(0.0,fc-hw),min(1.0,fc+hw)))
    def pt(f,s_):return (1-s_)*((1-f)*A+f*B)+s_*((1-f)*D+f*C)
    def cell(f0,f1,s0,s1):quad(V(*pt(f0,s0)),V(*pt(f1,s0)),V(*pt(f1,s1)),V(*pt(f0,s1)),mi)
    f=0.0
    for a_,b_ in sorted(cuts):
        if a_>f:cell(f,a_,0,1)
        cell(a_,b_,0,VS0);cell(a_,b_,VS1,1);f=b_
    if f<1:cell(f,1,0,1)
for i in range(N):
    j=(i+1)%N;pa=bowl(i);pb=bowl(j)
    if bool(PL[i]['roof'])!=bool(PL[j]['roof']):   # stand ends: the open-seat slope on both sides, the stand closed by an end wall
        pa=pb=bowl(j) if PL[i]['roof'] else bowl(i)
        k=i if PL[i]['roof'] else j;t=PL[k]['t'];prof=bowl(k)
        pts=[(x,z) for x,z,_ in prof]+[(rback(k),zback(k)),(rback(k),0.0)]
        f=bm.faces.new([V(*P(t,x,z)) for x,z in pts]);f.material_index=FC
    elif not PL[i]['roof'] and not PL[j]['roof'] and is_race(PL[i]['t'])!=is_race(PL[j]['t']):   # race side walls in concrete
        k=j if is_race(PL[i]['t']) else i;t=PL[k]['t'];pa=pb=bowl(k)
        pts=[(x,z) for x,z,_ in pa]+[(pa[-1][0],0.0)]
        f=bm.faces.new([V(*P(PL[j if k==i else i]['t'],x,z)) for x,z in pts]);f.material_index=TK
    n=max(len(pa),len(pb))
    while len(pa)<n:pa=[pa[0]]+pa
    while len(pb)<n:pb=[pb[0]]+pb
    two=n==5 and bool(PL[i]['roof']) and bool(PL[j]['roof'])   # east two-tier stand
    for k in range(n-1):
        mi=pa[k][2] if pa[k][2] is not None else SE
        # no sponsor band on the upper tier's front: director's pick C "no boards" (secretary 2026-11-18)
        A,B,C,D=[Vector(P(PL[a_]['t'],*pp[kk][:2])) for a_,pp,kk in ((i,pa,k),(j,pb,k),(j,pb,k+1),(i,pa,k+1))]
        if two and k==3:vom_cut(PL[i]['t'],PL[j]['t'],A,B,C,D,mi);continue
        quad(V(*A),V(*B),V(*C),V(*D),mi)
RIM=[(206,107),(210,108),(219,107),(224,106),(230,101),(238,96),(245,92),(254,86),(264,81),(276,80)]
def rim(t):
    if t<RIM[0][0] or t>RIM[-1][0]:return None
    for (a,ra),(b,rb) in zip(RIM,RIM[1:]):
        if a<=t<=b:return ra+(rb-ra)*(t-a)/(b-a)
# near stand outer edge, read off the photo (roof fascia bottom at z 15 and the facade feet, photo.jpg columns 1050-2350)
RR=[(141,110.0),(143.2,110.2),(146.9,110.9),(150,112.0),(151.2,113.3),(158.4,113.6),(165.6,116.5),(172.4,119.5),(178.8,122.3),(187,124.2),(195,127.4),(198,129.7),(202,130.6),(207,130.1),(213,129.0),(215,128.5),(217.7,128.9),(222.6,126.7)]   # past 215: eave read at z 16 (photo 2420,950 and the roof's end corner 2455,902)
def rroof(t):
    if t<RR[0][0] or t>RR[-1][0]:return None
    for (a,ra),(b,rb) in zip(RR,RR[1:]):
        if a<=t<=b:return ra+(rb-ra)*(t-a)/(b-a)
def tube(p0,p1,r0,r1,mi,n=8):
    p0=Vector(p0);p1=Vector(p1);ax=(p1-p0).normalized();up=Vector((0,0,1)) if abs(ax.z)<0.9 else Vector((1,0,0))
    u=ax.cross(up).normalized();w=ax.cross(u)
    A=[V(*(p0+r0*(math.cos(2*math.pi*k/n)*u+math.sin(2*math.pi*k/n)*w))) for k in range(n)]
    B=[V(*(p1+r1*(math.cos(2*math.pi*k/n)*u+math.sin(2*math.pi*k/n)*w))) for k in range(n)]
    for k in range(n):quad(A[k],A[(k+1)%n],B[(k+1)%n],B[k],mi)
def band(ta,tb,ra,rb,z0,z1,mi):quad(V(*P(ta,ra,z0)),V(*P(tb,rb,z0)),V(*P(tb,rb,z1)),V(*P(ta,ra,z1)),mi)
def near_facade(ta,tb,ra,rb):
    # photo.jpg columns 650-2400: dark glazed shopfronts 0-2.8; grey cladding (louvre screen at t 154-165) 2.8-7.3;
    # concourse deck at 7.3 with a concrete upstand to 8.4; upper wall set back sback(t): dark glazing to 12,
    # coloured panel band 12-13.5 (orange t 150-168, green t 174-205), cladding to the roof at 15; louvred awnings 11.7 -> 9.6
    tc=(ta+tb)/2;sa,sb=ra-sback(ta),rb-sback(tb)
    band(ta,tb,ra,rb,0,2.8,BK if 157.3<=tc<165 else DG);band(ta,tb,ra,rb,2.8,7.3,LV if 154<=tc<=165 else RR_ if 198.8<=tc<199.9 else TC if 199.9<=tc<206 else FC)
    quad(V(*P(ta,ra,7.3)),V(*P(tb,rb,7.3)),V(*P(tb,sb,7.3)),V(*P(ta,sa,7.3)),BG)
    band(ta,tb,ra,rb,7.0,7.6,BG);quad(V(*P(ta,ra-0.25,7.6)),V(*P(tb,rb-0.25,7.6)),V(*P(tb,rb,7.6)),V(*P(ta,ra,7.6)),BG)
    band(ta,tb,sa,sb,7.3,12.0,DG)
    band(ta,tb,sa,sb,12.0,13.5,DG if 141<=tc<165 or 174<=tc<200 else FC)
    band(ta,tb,sa,sb,13.5,15.0,FC)
def rw(t):return float(__import__('numpy').interp(t,[90,112,121.6],[102.4,102.2,102.8]))
def nw_bands(t,top):
    # north-west block (photo.jpg columns 200-700): measured band heights
    if t<112:return [(0,4.8,WR),(4.8,12.2,BC),(12.2,top,DC)]
    if t<121:return [(0,11.2,WR),(11.2,top,DC)]
    if t<131:return [(0,3.5,BK),(3.5,10.3,BC),(10.3,12.2,WR),(12.2,top,DC)]
    if t<138.3:return [(0,3.0,DG),(3.0,top,WR)]
    return [(0,top,DC)]   # photo u 728-790: dark recess under the roof between the white block and the stair
# roof sheet + front fascia, deck behind the roof, outer facade
for i in range(N):
    j=(i+1)%N;a=PL[i];b=PL[j];ta,tb=a['t'],b['t'];ra,rb=rback(i),rback(j);za,zb=zback(i),zback(j)
    if a['roof'] and b['roof']:
        ri,ro,zi,zo=a['roof'];Ri,Ro,Zi,Zo=b['roof']
        ka=rim(ta);kb=rim(tb)
        if ka is not None and kb is not None:
            ma=min(max(ka,ri),ro);mb=min(max(kb,Ri),Ro);za_=zi+(zo-zi)*(ma-ri)/(ro-ri);zb_=Zi+(Zo-Zi)*(mb-Ri)/(Ro-Ri)
            quad(V(*P(ta,ri,zi)),V(*P(tb,Ri,Zi)),V(*P(tb,mb,zb_)),V(*P(ta,ma,za_)),CS)
            quad(V(*P(ta,ma,za_)),V(*P(tb,mb,zb_)),V(*P(tb,Ro,Zo)),V(*P(ta,ro,zo)),RF)
            quad(V(*P(ta,ma,za_-1.0)),V(*P(tb,mb,zb_-1.0)),V(*P(tb,mb,zb_)),V(*P(ta,ma,za_)),WH)
        elif 86<=ta<=140 and 86<=tb<=140:
            # west roof: the fabric ends at the measured back edge (photo grid, r 102.2-102.8); behind it a dark plant deck 1.2 m lower
            wa,wb=rw(ta),rw(tb);ya=zi+(zo-zi)*(wa-ri)/(ro-ri);yb=Zi+(Zo-Zi)*(wb-Ri)/(Ro-Ri)
            quad(V(*P(ta,ri,zi)),V(*P(tb,Ri,Zi)),V(*P(tb,wb,yb)),V(*P(ta,wa,ya)),RF)
            quad(V(*P(ta,wa,ya-1.2)),V(*P(tb,wb,yb-1.2)),V(*P(tb,Ro,Zo-1.2)),V(*P(ta,ro,zo-1.2)),DK)
            quad(V(*P(ta,wa,ya-1.2)),V(*P(tb,wb,yb-1.2)),V(*P(tb,wb,yb)),V(*P(ta,wa,ya)),WH)
        else:quad(V(*P(ta,ri,zi)),V(*P(tb,Ri,Zi)),V(*P(tb,Ro,Zo)),V(*P(ta,ro,zo)),RF)
        quad(V(*P(ta,ri,zi-1.2)),V(*P(tb,Ri,Zi-1.2)),V(*P(tb,Ri,Zi)),V(*P(ta,ri,zi)),WH)
        ea=rroof(ta);eb=rroof(tb)
        if ea and eb:   # near stand: the roof runs on at its own slope out past the facade (photo fascia, z 15-16)
            quad(V(*P(ta,ro,zo)),V(*P(tb,Ro,Zo)),V(*P(tb,eb,16.0)),V(*P(ta,ea,16.0)),RF)
            quad(V(*P(ta,ea,15.0)),V(*P(tb,eb,15.0)),V(*P(tb,eb,16.0)),V(*P(ta,ea,16.0)),WH)
            quad(V(*P(ta,ea,15.0)),V(*P(tb,eb,15.0)),V(*P(tb,rb-sback(tb),15.0)),V(*P(ta,ra-sback(ta),15.0)),RF)
            near_facade(ta,tb,ra,rb);continue
        if ra>ro+0.5 or rb>Ro+0.5:quad(V(*P(ta,ro,zo)),V(*P(tb,Ro,Zo)),V(*P(tb,rb,Zo)),V(*P(ta,ra,zo)),RF if ta>=222 else DK)   # east: the ribbed roof runs on to the outer wall (photo 2080-2460 x 400-900, posts at r 112-122)
    elif not a['roof'] and not b['roof']:   # walkway at the top-row level, out to the concourse edge
        qa=bowl(i)[-1];qb=bowl(j)[-1]
        ia,ib=ne_in(ta),ne_in(tb)
        if ia and ib:
            quad(V(*P(ta,qa[0],qa[1])),V(*P(tb,qb[0],qb[1])),V(*P(tb,ib,zb)),V(*P(ta,ia,za)),DR)
            quad(V(*P(ta,ia,za)),V(*P(tb,ib,zb)),V(*P(tb,rb,zb)),V(*P(ta,ra,za)),NR)
        else:quad(V(*P(ta,qa[0],qa[1])),V(*P(tb,qb[0],qb[1])),V(*P(tb,rb,zb)),V(*P(ta,ra,za)),DR)
    if bool(a['roof'])!=bool(b['roof']):continue
    if 95<=ta<141:
        dr=3.0 if (ta+tb)/2>=138.3 else 0.0
        for z0,z1,mi in nw_bands((ta+tb)/2,min(za,zb)):band(ta,tb,ra-dr,rb-dr,z0,z1,mi)
        if abs(za-zb)>0.05:quad(V(*P(ta,ra,min(za,zb))),V(*P(tb,rb,min(za,zb))),V(*P(tb,rb,zb)),V(*P(ta,ra,za)),DC)
        continue
    # the near stand's layered facade runs on under the east roof (photo 2400-2500 x 950-1150); the outer walls the photo
    # does not show (one photo search 2026-11-18 found none) carry the same bands (secretary ruling a)
    zt_=min(za,zb)
    for z0,z1,mi in ((0,2.8,DG),(2.8,min(7.3,zt_),FC),(7.3,zt_,DG)):
        if z1>z0+0.05:band(ta,tb,ra,rb,z0,z1,mi)
    if abs(za-zb)>0.05:quad(V(*P(ta,ra,zt_)),V(*P(tb,rb,zt_)),V(*P(tb,rb,zb)),V(*P(ta,ra,za)),DG)
# north-west block: tall slot window (t 117.4-118.9, z 0.5-9.7), just proud of the white wall
def rft(t):return float(__import__('numpy').interp(t,*zip(*FT)))
band(117.4,118.9,rft(117.4)+0.05,rft(118.9)+0.05,0.5,9.7,DG)
# plaza at field level from the facade feet out to the podium edge, which drops to the car park at -5.2 (photo, z 0 edge reads)
PE=[(141,134.0),(144.6,134.3),(151.9,133.7),(159.5,133.9),(167.1,135.3),(174.5,136.6),(181.5,139.3),(186.2,142.2),(190,143.0),(195,140.0),(200.4,138.8),(205.2,138.4),(211.6,138.6),(214.8,137.2),(222,136.0)]
ts=[141+k*0.5 for k in range(163)]
for a_,b_ in zip(ts,ts[1:]):
    ea_=float(__import__('numpy').interp(a_,*zip(*PE)));eb_=float(__import__('numpy').interp(b_,*zip(*PE)))
    quad(V(*P(a_,rft(a_),0.02)),V(*P(b_,rft(b_),0.02)),V(*P(b_,eb_,0.02)),V(*P(a_,ea_,0.02)),TK)
    if b_<=190:band(a_,b_,ea_,eb_,-5.2,0.02,DC);band(a_,b_,ea_,eb_,0.02,1.1,CL)   # past t 190 the plaza stays at grade (photo 2100-2490 x 1180-1300)
# canopy over the plaza walk (photo columns 660-1355): back edge at z 4, front edge at z 3, white fascia, posts on the front
CB=[(141.5,120.7),(156.1,124.6),(169.4,132.1)];CF=[(141.6,128.4),(155.5,131.4),(169.0,139.6)]
ts=[141.5+k*0.7 for k in range(40)]
for a_,b_ in zip(ts,ts[1:]):
    ba,bb=[float(__import__('numpy').interp(x,*zip(*CB))) for x in (a_,b_)];fa,fb=[float(__import__('numpy').interp(x,*zip(*CF))) for x in (a_,b_)]
    quad(V(*P(a_,ba,4.0)),V(*P(b_,bb,4.0)),V(*P(b_,fb,3.0)),V(*P(a_,fa,3.0)),RF)
    band(a_,b_,fa,fb,2.6,3.0,WH)
for tp in (142,148,154,160,166):
    fr=float(__import__('numpy').interp(tp,*zip(*CF)))-0.3;tube(Vector(P(tp,fr,0)),Vector(P(tp,fr,2.6)),0.12,0.12,WH,6)
# service tower (photo columns 1240-1350): dark cladding to 9.3, white above to 14, two flue pipes to 21
def blk(t0,t1,r0,r1,z0,z1,mi,mt=None):
    band(t0,t1,r1,r1,z0,z1,mi);band(t1,t0,r0,r0,z0,z1,mi);band(t0,t0,r0,r1,z0,z1,mi);band(t1,t1,r1,r0,z0,z1,mi)
    quad(V(*P(t0,r0,z1)),V(*P(t1,r0,z1)),V(*P(t1,r1,z1)),V(*P(t0,r1,z1)),mt or mi)
blk(165.0,169.8,113.0,120.6,0,9.3,DC);blk(165.0,169.8,113.0,120.6,9.3,14.0,WR)
for tp in (165.5,166.3):tube(Vector(P(tp,119.0,14.0)),Vector(P(tp,119.0,21.0)),0.45,0.45,FC,10)
# Members entrance: navy sign panel (t 173.9-176.1, z 1-5.4) and a timber pergola (t 169.5-173.8) at z 2.6 on posts
band(173.9,176.1,rft(173.9)+0.15,rft(176.1)+0.15,1.0,5.4,MB)
for a_,b_ in ((169.5,171.65),(171.65,173.8)):
    quad(V(*P(a_,rft(a_),2.6)),V(*P(b_,rft(b_),2.6)),V(*P(b_,rft(b_)+2.5,2.6)),V(*P(a_,rft(a_)+2.5,2.6)),TM)
for tp in (169.6,171.65,173.7):tube(Vector(P(tp,rft(tp)+2.4,0)),Vector(P(tp,rft(tp)+2.4,2.6)),0.1,0.1,TM,6)
# near stand bays (photo grids 640-2300 x 1080-1240, nf.py on the wall planes): white roof columns from the deck edge up to
# the roof fascia; coloured panels on the upper wall (z 12-13.5) with dark glass between; an awning per bay (11.7 -> 9.6)
# with a white front lip; the deck upstand is light concrete with a railing on top
NCOL=[142.6,148.5,154.2,159.6,164.75,175.2,179.9,184.4,188.5,193.1,198.3,202.5,208.3]
NPAN=[(145.2,147.2,OR),(149.1,150.8,OR),(152.5,153.7,OR),(154.2,156.0,OR),(157.8,159.1,OR),(159.6,161.5,OR),(163.4,164.7,OR),
      (176.99,178.71,GN),(180.45,181.66,GN),(183.26,184.57,GN),(185.08,186.05,GN),(187.55,188.8,GN),(188.99,190.11,GN),(191.92,193.65,GN),(195.43,197.11,GN)]
def ruw(t):return rft(t)-sback(t)
for a_,b_,m_ in NPAN:band(a_,b_,ruw(a_)+0.05,ruw(b_)+0.05,12.0,13.5,m_)
for c_ in NCOL:
    e_=rroof(c_) or rft(c_)+3;tube(Vector(P(c_,rft(c_)-0.3,7.3)),Vector(P(c_,e_-0.5,15.0)),0.16,0.16,WH,6)
for a_,b_ in zip(NCOL,NCOL[1:]):
    if b_-a_>8:continue   # the service tower bay has no awning
    if a_>=202.5:continue   # SE bays: awnings read off the photo below
    a2,b2=a_+0.25,b_-0.25
    quad(V(*P(a2,ruw(a2),11.7)),V(*P(b2,ruw(b2),11.7)),V(*P(b2,ruw(b2)+1.8,10.6)),V(*P(a2,ruw(a2)+1.8,10.6)),AW)
    band(a2,b2,ruw(a2)+1.8,ruw(b2)+1.8,10.4,10.6,WH)
# SE awnings, corners read off photo rays (grid 1940-2500 x 940-1200): A 2122-2252 x 1087-1122, B 2265-2357 x 1030-1087,
# C 2380-2450 x 945-1002, D (low canopy) 2400-2470 x 1060-1120
for Q in (((203.63,125.61,10),(208.05,128.21,10),(208.23,128.88,9.2),(203.26,127.03,9.2)),
          ((211.2,125.58,9.4),(215.34,126.04,9.4),(215.0,127.68,8.6),(209.93,127.91,8.6)),
          ((220.68,123.45,11.65),(222.81,126.42,11.65),(220.11,128.12,9.6),(218.86,126.92,9.6)),
          ((216.79,128.79,4.0),(220.12,129.92,4.0),(217.64,132.64,4.0),(214.28,132.33,4.0))):
    q_=[V(*P(*c)) for c in Q];quad(q_[0],q_[1],q_[2],q_[3],AW)
    (t3,r3,z3),(t2,r2,z2)=Q[3],Q[2];band(t3,t2,r3,r2,z3-0.15,z3,WH)
for k_ in range(106):
    t_=141+k_*0.7;tube(Vector(P(t_,rft(t_)-0.15,7.6)),Vector(P(t_,rft(t_)-0.15,8.6)),0.03,0.03,WH,4)
ts_=[141+k*0.5 for k in range(149)]
# white rafters over the metal roof at each column (photo 1000-1023 / 1113-1123 / 1233-1247 at the top edge), ~0.8 m wide
for c_ in NCOL:
    if c_>=175:continue
    k_=min(range(N),key=lambda i:abs((PL[i]['t']-c_+180)%360-180));ri,ro,zi,zo=PL[k_]['roof'];e_=rroof(c_) or ro
    tube(Vector(P(c_,ri,zi+0.4)),Vector(P(c_,ro,zo+0.4)),0.4,0.4,WH,4);tube(Vector(P(c_,ro,zo+0.4)),Vector(P(c_,e_,16.4)),0.4,0.4,WH,4)
for a_,b_ in zip(ts_,ts_[1:]):band(a_,b_,rft(a_)-0.15,rft(b_)-0.15,8.55,8.65,WH)
def tube(p0,p1,r0,r1,mi,n=8):
    p0=Vector(p0);p1=Vector(p1);ax=(p1-p0).normalized();up=Vector((0,0,1)) if abs(ax.z)<0.9 else Vector((1,0,0))
    u=ax.cross(up).normalized();w=ax.cross(u)
    A=[V(*(p0+r0*(math.cos(2*math.pi*k/n)*u+math.sin(2*math.pi*k/n)*w))) for k in range(n)]
    B=[V(*(p1+r1*(math.cos(2*math.pi*k/n)*u+math.sin(2*math.pi*k/n)*w))) for k in range(n)]
    for k in range(n):quad(A[k],A[(k+1)%n],B[(k+1)%n],B[k],mi)
def plate(c,u,w,hu,hw,mi):
    c=Vector(c);quad(V(*(c-hu*u-hw*w)),V(*(c+hu*u-hw*w)),V(*(c+hu*u+hw*w)),V(*(c-hu*u+hw*w)),mi)
def nearest(t):return min(range(N),key=lambda k:abs((PL[k]['t']-t+180)%360-180))
def roofz_at(x,y):
    t=math.degrees(math.atan2(y-c0[1],x-c0[0]))%360;r=math.hypot(x-c0[0],y-c0[1]);R=PL[nearest(t)]['roof']
    if not R:return 0.0
    ri,ro,zi,zo=R;s=max(0,min(1,(r-ri)/(ro-ri)));return zi+s*(zo-zi)
# light towers as they are now (2026 photos): two red ladder chords from the ground up through the roof,
# widening at the top into an open red lattice inverted triangle, a small LED panel on its top edge
def box(p0,p1,s,mi,up=None):
    p0=Vector(p0);p1=Vector(p1);ax=(p1-p0).normalized();up=up or (Vector((0,0,1)) if abs(ax.z)<0.9 else Vector((1,0,0)))
    u=ax.cross(up).normalized()*s;w=ax.cross(u).normalized()*s
    A=[V(*(p0+a*u+b*w)) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))];B=[V(*(p1+a*u+b*w)) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
    for k in range(4):quad(A[k],A[(k+1)%4],B[(k+1)%4],B[k],mi)
def tower(base,tip,top,side,to,half_top,rung=3.0,FM=None,rows=3,lf=0.33,sh=0.9,spine=False):
    FM=RD if FM is None else FM
    """base: ground point under the shaft; tip: bottom of the triangle head; top: centre of its top edge."""
    # sh: half width of the head at its tip. Shaft (photo tower 25 grid 640-1000 x 720-1060, tower 26 top-down): one rust lattice
    # column ~1 m square straight up to the tip on the +side, and a raking prop from the roof on the -side up to the head's
    # -side chord a third of the way up (25: column 785,845-1030, prop 820,775 -> 805,1020); a small deck at the tip
    if spine:
        box(base+side*1.0,tip,0.5,RU)
        pj=tip-side*sh+((top-side*half_top)-(tip-side*sh))*0.3;box(base-side*1.0,pj,0.18,RU)
        dk=tip-to*0.4;quad(V(*(dk-side*2.2-to*1.0)),V(*(dk+side*2.2-to*1.0)),V(*(dk+side*2.2+to*1.0)),V(*(dk-side*2.2+to*1.0)),TN)
    else:
        for s in (-1,1):box(base+side*sh*s,tip+side*sh*s,0.22,FM)
        n=max(2,int((tip-base).length/rung))
        for k in range(1,n):
            q=base+(tip-base)*(k/n);box(q-side*sh,q+side*sh,0.09,FM)
    # head: two outer chords from the tip to the top corners, a top chord, ladder rungs and diagonals
    L=tip-side*sh;Rr=tip+side*sh;TL=top-side*half_top;TR=top+side*half_top
    box(L,TL,0.2,FM);box(Rr,TR,0.2,FM);box(TL,TR,0.2,FM)
    m=6
    for k in range(1,m):
        f=k/m;a=L+(TL-L)*f;b=Rr+(TR-Rr)*f;box(a,b,0.08,FM)
        if k<m:
            a2=L+(TL-L)*((k+1)/m);b2=Rr+(TR-Rr)*((k+1)/m);box(a,b2 if k%2 else a2,0.06,FM)
    # head infill (photo crops of towers 24, 25, 28, 30 and the 2026 top-down): the top third is the lamp array (lamp faces
    # toward the field, lamp backs with white catwalk rails behind), the next quarter a pale grey mesh panel, then open lattice;
    # a ladder runs up the middle of the head
    def edge(f):
        c=top+(tip-top)*f;hw=half_top+(sh-half_top)*f;return c-side*hw,c+side*hw
    for k_ in range(rows):           # lamp rows: each quad one row of the texture
        f0=lf*k_/rows;f1=lf*(k_+1)/rows;a0,b0=edge(f0);a1,b1=edge(f1)
        for off,mi in ((0.12,LP),(-0.12,LB)):
            o=to*off;quad(V(*(a0+o)),V(*(b0+o)),V(*(b1+o)),V(*(a1+o)),mi)
    a0,b0=edge(lf);a1,b1=edge(0.58)
    for off,mi in ((0.12,MD),(-0.12,MP)):   # field side dark brown, back pale grey (photo)
        o=to*off;quad(V(*(a0+o)),V(*(b0+o)),V(*(b1+o)),V(*(a1+o)),mi)
    # the ladder up the middle of the head: a 0.9 m strip in the frame paint, standing proud of both faces
    for off in (0.2,-0.2):
        o=to*off;c0_=top+o;c1_=tip+(top-tip)*0.0+o
        quad(V(*(c0_-side*0.45)),V(*(c0_+side*0.45)),V(*(c1_+side*0.45)),V(*(c1_-side*0.45)),FM)
HW=CAM['p'][9]
TB={'25':(-52.2,107.2,14.4),'26':(-85.5,53.7,13.9),'27':(-86.1,-4.3,11.8),'28':(-51.9,-44.6,14.2),'29':(-4.5,-50.2,20.6),'30':(69.4,-41.1,20.4)}
TP=json.load(open('towpts.json'))
def tower2(q,rows,lf):
    """Head and shaft of towers 25, 27, 30 read off the photo (towpts.py): a lopsided triangle head (one chord near
    vertical over the column), a rust column from the roof to the tip, a raking prop to the far chord, cable pods."""
    A,B,T=Vector(q['cl']),Vector(q['cr']),Vector(q['tip']);n=(B-A).cross(T-A).normalized()
    if n.dot(Vector(q['to']))<0:n=-n
    box(Vector(q['cf']),T,0.35,RU);box(Vector(q['pf']),Vector(q['pt']),0.18,RU)
    box(A,T,0.2,TN);box(B,T,0.2,TN);box(A,B,0.2,TN)
    for k_ in range(1,6):
        f=k_/6;a=A+(T-A)*f;b=B+(T-B)*f;box(a,b,0.08,TN)
    def edge(f):return A+(T-A)*f,B+(T-B)*f
    for k_ in range(rows):
        f0=lf*k_/rows;f1=lf*(k_+1)/rows;a0,b0=edge(f0);a1,b1=edge(f1)
        for off,mi in ((0.12,LP),(-0.12,LB)):
            o=n*off;quad(V(*(a0+o)),V(*(b0+o)),V(*(b1+o)),V(*(a1+o)),mi)
    # see-through mesh from the lamps down to the tip (photo: the grass shows through it)
    a0,b0=edge(lf);a1,b1=edge(0.96)
    for off,mi in ((0.12,MD),(-0.12,MP)):
        o=n*off;quad(V(*(a0+o)),V(*(b0+o)),V(*(b1+o)),V(*(a1+o)),mi)
    m_=(A+B)/2   # white ladder strip from the top chord down to the tip (photo 25: 805,650 -> 790,840)
    w_=(B-A).normalized()*0.25   # one strip ~0.5 m wide, behind the field-side mesh (photo: ~3 px, pale grey)
    o=-n*0.05;quad(V(*(m_-w_+o)),V(*(m_+w_+o)),V(*(T+w_+o)),V(*(T-w_+o)),MP)
    up=Vector((0,0,1));dx=(B-A).normalized()*2.2;dy=n*1.0   # deck at the tip (photo 25: 775-810 x 860)
    quad(V(*(T-dx-dy)),V(*(T+dx-dy)),V(*(T+dx+dy)),V(*(T-dx+dy)),TN)
    for pd in q['pods']:box(Vector(pd)-n*0.4,Vector(pd)+n*0.4,0.35,RD)
for k in ('25','27','30'):
    tower2(TP[k],{'25':5,'27':4,'30':4}[k],0.25)
for k in ('26','28','29'):
    x,y=CAM['towers'][k];bx,by,zb=TB[k]
    to=Vector((c0[0]-x,c0[1]-y,0)).normalized();side=Vector((-to.y,to.x,0))
    top=Vector((x,y,HW));d=(Vector((x,y,HW))-Vector((bx,by,zb))).normalized()
    tip=top-d*{'25':18.0,'27':21.2,'30':13.4}.get(k,20.0)/d.z   # head drop to the tip read off the photo (25: 785,845; 27: 2035,885; 30: 1752,278)
    base=Vector((bx,by,zb))   # chords start where they come through the roof (hidden below it)
    if k=='26':   # two red equipment boxes on the back of the head's lower edges (photo 1370-1385 / 1440-1455 x 765-800)
        ha=(top-tip).normalized();cb=top+(tip-top)*0.32
        for sg in (-1,1):q=cb+side*sg*4.0-to*0.6;box(q-ha*1.5,q+ha*1.5,0.6,RD)
    # head top edge measured on the photo (25: 783,635-868,652; 26: 1373,700-1458,712; 27: 1965,650-2045,655; 30: 1690,123-1760,140)
    # 28 and 29 are seen end-on, so they take the mean; chords 3.4 m apart (tower 26 top-down: 35 px at 10 px/m)
    if k=='26':
        # a red pipe up the outside of the column (+side, image left) into the head (photo 1372-1385 x 770-990)
        box(base+side*1.6,tip+side*0.6,0.15,RD);box(tip+side*0.6,top+side*4.17+(tip-top)*0.1,0.15,RD)
    tower(base,tip,top,side,to,{'25':4.54,'26':4.3,'27':4.25,'28':4.43,'29':4.43,'30':4.62}[k],sh=0.5,spine=True,FM=TN,rows={'25':5,'26':3,'27':4,'28':4,'29':5,'30':4}[k],lf=0.25)  # lamp band to 25% of the head, rows counted on the photo
# tower 24 (photo rays met on its lean plane, photo shaft centre 190,770 / 207,560 / 250,450 / 287,350): a box lattice
# cranked at z 28.6 - near-vertical below (chords 1.5 m deep toward the field, 20 px), leaning more above (2.1 m deep,
# 25-30 px); the head from z 48.4 to 54 (photo 277-323 x 310-367)
T24=[Vector((44.28,143.9,0)),Vector((43.0,138.9,28.6)),Vector((40.5,129.3,48.4))];T24top=Vector((40.15,127.9,54.0))
to=Vector((c0[0]-T24top.x,c0[1]-T24top.y,0)).normalized();side=Vector((-to.y,to.x,0))
def shaft(a,b,side,to,hw,dep):
    cs=[side*hw*i+to*dep*j for i in (-1,1) for j in (-1,1)]
    for c in cs:box(a+c,b+c,0.2,RD)
    n=max(2,int((b-a).length/2.5))
    for k in range(n+1):
        q=a+(b-a)*(k/n)
        for c1,c2 in ((cs[0],cs[1]),(cs[2],cs[3]),(cs[0],cs[2]),(cs[1],cs[3])):box(q+c1,q+c2,0.07,RD)
        if k<n:
            q2=a+(b-a)*((k+1)/n)
            for c1,c2 in ((cs[0],cs[1]),(cs[2],cs[3])):box(q+c1,q2+c2,0.06,RD)
for (a,b),dep in zip(((T24[0],T24[1]),(T24[1],T24[2])),(0.75,1.05)):shaft(a,b,side,to,0.9,dep)
# head (photo 3x crop 200-380 x 280-420): no box - the lattice runs on to the tip; lamp clusters hang off the field-ward
# side (photo 330-360 x 320-385, 0.8-3.4 m out along the shaft's depth), stepped red platforms on the other side
shaft(T24[2],T24top,side,to,0.9,1.05)
ax24=(T24top-T24[2]).normalized()
for k_ in range(3):
    c=T24top-ax24*(2.0+k_*2.2);c1=c+ax24*2.0;o0,o1=to*0.8,to*2.6   # hanging down from the tip (photo y 320-385)
    for off,mi in ((0.95,LP),(0.85,LB)):
        sd=side*off;quad(V(*(c+o0+sd)),V(*(c+o1+sd)),V(*(c1+o1+sd)),V(*(c1+o0+sd)),mi)
    box(c+o0+side*0.9,c+o1+side*0.9,0.08,RD);box(c1+o0+side*0.9,c1+o1+side*0.9,0.08,RD)
for k_ in range(3):
    pc=T24[2]+ax24*(k_*2.6-3.6)-to*1.3   # photo 255-295 x 340-400
    quad(V(*(pc-side*1.0-to*0.8)),V(*(pc+side*1.0-to*0.8)),V(*(pc+side*1.0+to*0.8)),V(*(pc-side*1.0+to*0.8)),RD)
    box(pc-to*0.8+side*1.0+Vector((0,0,1.0)),pc-to*0.8-side*1.0+Vector((0,0,1.0)),0.05,RD)
# tower 23 (photo grid 720-900 x 70-640): feet on the NE concourse (photo 785,470 at z 7.5), shaft photo x 772-800 leaning
# 12 m toward the field to the head (photo bottom 775-820 at y 140, top 770-848 at y 78): a trapezoid of lamps sitting
# off to the right of the shaft, its left edge on the shaft's, a strut from its lower right corner back to the shaft
b23=Vector((126.4,70.1,7.5));hb23=Vector((114.8,67.2,49.5));ax23=(hb23-b23)/(hb23.z-b23.z);ht23=b23+ax23*(56.5-b23.z)
to=Vector((c0[0]-hb23.x,c0[1]-hb23.y,0)).normalized();side=Vector((-to.y,to.x,0))
shaft(b23,hb23,side,to,1.2,0.75)
H3a,H3b,H3c,H3d=hb23-side*1.45,hb23+side*4.05,ht23-side*1.95,ht23+side*7.55
for p0,p1 in ((H3a,H3b),(H3b,H3d),(H3d,H3c),(H3c,H3a)):box(p0,p1,0.2,RD)
box(H3b,b23+ax23*(36-b23.z)+side*1.2,0.15,RD)
rows=6
for k_ in range(rows):
    f0=0.15+0.85*k_/rows;f1=0.15+0.85*(k_+1)/rows
    a0,b0=H3c+(H3a-H3c)*f0,H3d+(H3b-H3d)*f0;a1,b1=H3c+(H3a-H3c)*f1,H3d+(H3b-H3d)*f1
    for off,mi in ((0.12,LP),(-0.12,LB)):
        o=to*off;quad(V(*(a0+o)),V(*(b0+o)),V(*(b1+o)),V(*(a1+o)),mi)
# east tent roof (photo grid, columns 840-1730): 12 white masts every 5.27 deg from t 308.9 to 6.9, standing at 92% of the
# roof depth, 4.2 m tall; an A-frame of two legs to 97% depth at +-1.3 deg; a white ladder girder raking from the mast top
# down to 25% depth, its two chords landing at t+0.4 and t-3.0
def tpt(t,s,dz):
    ri,ro,zi,zo=PL[nearest(t)]['roof'];return Vector(P(t,ri+s*(ro-ri),zi+s*(zo-zi)+dz))
for k in range(12):
    t=(308.9+5.27*k)%360;top=tpt(t,0.92,4.2)
    tube(tpt(t,0.92,0),top,0.22,0.16,WH,6)
    for dt in (-1.3,1.3):tube(top,tpt(t+dt,0.97,0),0.12,0.12,WH,6)
    A=[tpt(t-0.3,0.92,3.9),tpt(t+0.3,0.92,3.9)];B=[tpt(t-3.0,0.25,0),tpt(t+0.4,0.25,0)]
    for k_ in range(2):tube(A[k_],B[k_],0.09,0.09,WH,4)
    for m_ in range(1,8):tube(A[0]+(B[0]-A[0])*(m_/8),A[1]+(B[1]-A[1])*(m_/8),0.05,0.05,WH,4)
# near roof masts with a tie to the front edge
for t in range(110,188,12):
    ri,ro,zi,zo=PL[nearest(t)]['roof'];base=Vector(P(t,ri+6,zi+(zo-zi)*6/(ro-ri)));top=base+Vector((0,0,6.0))
    tube(base,top,0.2,0.12,WH,6);tube(top,Vector(P(t,ri,zi)),0.05,0.05,WH,4)
# south-east roof posts (photo 3x grid 1700-1960 x 900-1110, roofhit on the roof and its run-out): (t, r, z of the roof, height);
# a raking strut from the tall post's top down to the roof at t 206.3
for t_,r_,z_,h_ in ((200.47,89.33,9.92,3.49),(204.30,94.72,10.24,6.11),(199.94,105.32,12.11,5.61),(196.04,100.95,11.82,3.06),(192.47,112.96,13.92,3.26),(196.37,116.59,14.16,5.73),(194.67,86.4,10.07,3.54),(185.92,102.44,13.04,5.48),(190.82,98.09,12.02,2.67),(216.28,105.58,12.13,5.58),(212.54,114.27,13.38,5.67),(225.44,105.98,12.92,2.26),(218.38,114.1,13.65,3.15),(221.86,113.83,13.88,3.14),(219.12,121.4,14.92,3.51),(215.77,121.73,14.84,2.99),(209.93,122.3,14.7,5.47),(228.99,106.04,13.25,4.88),(227.06,112.52,13.2,5.67),(226.35,118.24,13.2,7.79)):
    b_=Vector(P(t_,r_,z_));tube(b_,b_+Vector((0,0,h_)),0.18,0.12,WH,6)
tube(Vector(P(204.30,94.72,16.35)),Vector(P(206.27,95.94,10.26)),0.12,0.12,WH,6)
# SE tan cladding box on two pilotis (photo 2230-2350 x 1100-1215, 3x grid): r FT -> 131, z 2.6-7.4, t 205.9-211.9
_ta,_tb=205.9,211.9;_ts=[_ta+k*(_tb-_ta)/8 for k in range(9)]
for a_,b_ in zip(_ts,_ts[1:]):
    band(a_,b_,131,131,2.6,7.4,TC)
    quad(V(*P(a_,rft(a_),2.6)),V(*P(b_,rft(b_),2.6)),V(*P(b_,131,2.6)),V(*P(a_,131,2.6)),TC)
    quad(V(*P(a_,131,7.4)),V(*P(b_,131,7.4)),V(*P(b_,rft(b_),7.4)),V(*P(a_,rft(a_),7.4)),BG)
for t_ in (_ta,_tb):band(t_,t_,rft(t_),131,2.6,7.4,TC)
# second tan panel past a dark window (photo 2345-2400 x 1075-1165) and the white rail on the box top (2240-2400)
band(211.9,212.9,131,131,1.5,7.4,DG);band(212.9,214.8,130.7,130.7,1.5,7.4,TC)
for k_ in range(20):
    t_=205.9+k_*0.47;tube(Vector(P(t_,131.1,7.4)),Vector(P(t_,131.1,8.4)),0.03,0.03,WH,4)
_rs=[205.9+k*0.5 for k in range(19)]
for a_,b_ in zip(_rs,_rs[1:]):
    for z_ in (7.9,8.4):band(a_,b_,131.1,131.1,z_-0.04,z_+0.04,WH)
for t_,r_ in ((206.5,130.5),(210.6,130.6)):tube(Vector(P(t_,r_,0)),Vector(P(t_,r_,2.6)),0.22,0.22,BG,8)
# OSM building and video wall
G=json.load(open('osm/geo.json'))
def prism(poly,h,mi):
    pts=[tuple(p) for p in poly];pts=pts[:-1] if pts[0]==pts[-1] else pts
    lo=[V(x,y,0) for x,y in pts];hi=[V(x,y,h) for x,y in pts]
    for k in range(len(pts)):quad(lo[k],lo[(k+1)%len(pts)],hi[(k+1)%len(pts)],hi[k],mi)
    f=bm.faces.new(hi);f.material_index=mi
prism(G['395183264'],4.5,BG)
# video screen: on the OSM line, ends at 53% and -12% of it, face z 12.5 to 23 (photo corners (225,428) (225,522) (355,380)
# (375,470) solved on the OSM plane); a white box truss 4 m deep behind it from the concourse roof (z 8) to the top (photo
# columns 190-225 and the lattice under the screen, rows 500-560)
a,b=G['1098416479'];a=Vector((a[0],a[1],0));b=Vector((b[0],b[1],0));A=a+(b-a)*0.53;Bv=a+(b-a)*(-0.12)
e_=(b-a).normalized();nf=Vector((-e_.y,e_.x,0))          # nf: toward the field
if nf.dot(Vector((c0[0],c0[1],0))-A)<0:nf=-nf
lo=Vector((0,0,12.5));hi=Vector((0,0,23.0));ft=Vector((0,0,8.0))
quad(V(*(A+lo)),V(*(Bv+lo)),V(*(Bv+hi)),V(*(A+hi)),SC)
bk=-nf*0.5
quad(V(*(A+hi+bk)),V(*(Bv+hi+bk)),V(*(Bv+lo+bk)),V(*(A+lo+bk)),FC)          # screen casing back
for P0,P1 in ((A,A+bk),(Bv,Bv+bk)):quad(V(*(P0+lo)),V(*(P1+lo)),V(*(P1+hi)),V(*(P0+hi)),DC)   # casing ends
quad(V(*(A+hi)),V(*(Bv+hi)),V(*(Bv+hi+bk)),V(*(A+hi+bk)),DC);quad(V(*(A+lo)),V(*(Bv+lo)),V(*(Bv+lo+bk)),V(*(A+lo+bk)),DC)
D0,D1=-nf*0.7,-nf*4.0;L=(Bv-A).length;ns=max(2,round(L/3.0));nz=6
def fp(s_,d_,z_):return A+(Bv-A)*s_+d_+Vector((0,0,z_))
for s_ in (0.0,1.0):
    for d_ in (D0,D1):tube(fp(s_,d_,8.0),fp(s_,d_,23.0),0.16,0.16,WH,6)        # corner chords
    for k in range(nz+1):
        z_=8.0+15.0*k/nz;tube(fp(s_,D0,z_),fp(s_,D1,z_),0.08,0.08,WH,4)       # end-face ties
        if k<nz:tube(fp(s_,D0,z_),fp(s_,D1,z_+15.0/nz),0.06,0.06,WH,4)       # end-face diagonals
for d_ in (D0,D1):
    for z_ in (8.0,12.5,23.0):tube(fp(0,d_,z_),fp(1,d_,z_),0.12,0.12,WH,6)   # long chords
for k in range(ns+1):
    s_=k/ns
    tube(fp(s_,D1,8.0),fp(s_,D1,23.0),0.08,0.08,WH,4);tube(fp(s_,D0,23.0),fp(s_,D1,23.0),0.07,0.07,WH,4)
    tube(fp(s_,D0,8.0),fp(s_,D0,12.5),0.08,0.08,WH,4)
    if k<ns:
        s2=(k+1)/ns;tube(fp(s_,D1,8.0),fp(s2,D1,23.0),0.06,0.06,WH,4);tube(fp(s_,D0,8.0),fp(s2,D0,12.5),0.06,0.06,WH,4)
        tube(fp(s_,D0,23.0),fp(s2,D1,23.0),0.05,0.05,WH,4)
# aisle stairs on the far stand's lower tier, at the bays measured off the photo (row 520, z 4)
AI=mat('aisle',(0.58,0.57,0.55))
def nearest(t):return min(range(N),key=lambda i:abs((PL[i]['t']-t+180)%360-180))
for ta in (324.2,334.9,345.7,356.3,5.95,16.9,24.7,32.2,39.8):   # NE aisles: feet at the wall top (z 2) off photo columns 545-822
    prof=bowl(nearest(ta));(r0,z0,_),(r1,z1,_)=prof[1],prof[2]
    for rr,zz in ((r0,z0),(r1,z1)):pass
    w=math.degrees(0.6/((r0+r1)/2))
    quad(V(*P(ta-w,r0,z0+0.05)),V(*P(ta+w,r0,z0+0.05)),V(*P(ta+w,r1,z1+0.05)),V(*P(ta-w,r1,z1+0.05)),AI)

# vomitory tunnels (see VOM)
for tv in VOM:
    prof=bowl(nearest(tv));(rm,zm,_),(rb_,zb_,_)=prof[3],prof[4]
    r0,z0=rm+VS0*(rb_-rm),zm+VS0*(zb_-zm);r1,z1=rm+VS1*(rb_-rm),zm+VS1*(zb_-zm);re=r1+3.0
    w=math.degrees(VW/rm)
    quad(V(*P(tv-w,r0,z0)),V(*P(tv+w,r0,z0)),V(*P(tv+w,re,z0)),V(*P(tv-w,re,z0)),DC)          # tunnel floor
    quad(V(*P(tv-w,re,z1)),V(*P(tv+w,re,z1)),V(*P(tv+w,r1,z1)),V(*P(tv-w,r1,z1)),DC)          # soffit under the rows behind
    band(tv-w,tv+w,re,re,z0,z1,FC)                                                              # back wall
    for e_ in (-w,w):
        f_=bm.faces.new([V(*P(tv+e_,r0,z0)),V(*P(tv+e_,re,z0)),V(*P(tv+e_,re,z1)),V(*P(tv+e_,r1,z1))]);f_.material_index=TK
# north-west stair (photo columns 790-860): concourse deck at 7.3 down to the plaza, running along the facade
def ramp(t0,t1,ra,rb,z0,z1,w,mi):
    quad(V(*P(t0,ra-w/2,z0)),V(*P(t0,ra+w/2,z0)),V(*P(t1,rb+w/2,z1)),V(*P(t1,rb-w/2,z1)),mi)
ramp(144.1,145.6,110.8,111.6,7.3,0.0,1.8,AI)
for s_ in (-0.9,0.9):quad(V(*P(144.1,110.8+s_,7.3)),V(*P(145.6,111.6+s_,0.0)),V(*P(145.6,111.6+s_,1.0)),V(*P(144.1,110.8+s_,8.3)),CL)
# west membrane roof (t 88-140): white fabric on a triangulated white tube space frame, 1.5 m above the fabric,
# three chords round the roof (at 15/45/75% of its depth), radial members every 6 deg, diagonals between them (photo columns 150-800)
def rpt(t,s,dz=1.5):
    ri,ro,zi,zo=PL[nearest(t)]['roof'];return Vector(P(t,ri+s*(ro-ri),zi+s*(zo-zi)+dz))
# photo grid read (roofhit.py): a back row of tall white posts (3.8 m) at r 100.3-102.8, every ~4.3 deg from t 90.4;
# a front row of joints on short posts (1.8 m) at r 92.3 between them; top chords along both rows, zig-zag
# diagonals between the rows, ties from the front joints to the field edge and from the posts to the back edge
def fpt(t,r,dz):
    ri,ro,zi,zo=PL[nearest(t)]['roof'];s=(r-ri)/(ro-ri);return Vector(P(t,r,zi+s*(zo-zi)+dz))
def redge(t,s,dz=0.1):return rpt(t,s,dz)
TWB=[90.4,94.5,99.05,103.0,107.1,112.4,116.9,121.6]
while TWB[-1]+4.4<139:TWB.append(TWB[-1]+4.4)
def rb_(t):return float(__import__('numpy').interp(t,[107,121.6],[100.3,102.8]))
for k,t in enumerate(TWB):
    tube(fpt(t,rb_(t),0.0),fpt(t,rb_(t),3.8),0.13,0.13,WH,6)
    for d_ in (-1.2,1.2):tube(fpt(t,rb_(t),3.8),fpt(t+d_,rw(t+d_)-0.1,0.1),0.09,0.09,WH,4)
    if k+1<len(TWB):
        tn=TWB[k+1];tm=(t+tn)/2
        tube(fpt(t,rb_(t),3.8),fpt(tn,rb_(tn),3.8),0.12,0.12,WH,6)
        tube(fpt(tm,92.3,0.0),fpt(tm,92.3,1.8),0.1,0.1,WH,4)
        tube(fpt(t,rb_(t),3.8),fpt(tm,92.3,1.8),0.1,0.1,WH,4);tube(fpt(tn,rb_(tn),3.8),fpt(tm,92.3,1.8),0.1,0.1,WH,4)
        for d_ in (-1.2,1.2):tube(fpt(tm,92.3,1.8),redge(tm+d_,0.02,0.2),0.09,0.09,WH,4)
        if k+2<len(TWB):tm2=(tn+TWB[k+2])/2;tube(fpt(tm,92.3,1.8),fpt(tm2,92.3,1.8),0.1,0.1,WH,4)
# south roof frame (photo grid, columns 1950-2300, roofhit.py): white radial frames every 8 deg (t 246.4, 254.4 measured),
# posts 2.3 m tall at 50%, 74% and 96% of the roof depth, a radial top tube from the front edge over the post tops,
# and circumferential tubes joining the post tops of each row
SR=[230.4+8*k for k in range(9)];SP=(0.5,0.74,0.96)
for k,t in enumerate(SR):
    for s_ in SP:tube(rpt(t,s_,0.0),rpt(t,s_,2.3),0.1,0.1,WH,4)
    pts=[rpt(t,0.02,0.2)]+[rpt(t,s_,2.3) for s_ in SP]
    for a_,b_ in zip(pts,pts[1:]):tube(a_,b_,0.12,0.12,WH,6)
    if k+1<len(SR):
        for s_ in SP:tube(rpt(t,s_,2.3),rpt(SR[k+1],s_,2.3),0.1,0.1,WH,4)
        tube(rpt(t,0.02,0.2),rpt(SR[k+1],0.02,0.2),0.14,0.14,WH,6)
# south-west stair tower (photo columns 1960-2020): two flights between the deck at 7.3 and the plaza, landings, rails
ramp(195.8,197.4,129.0,129.0,7.3,3.65,1.6,AI);ramp(197.4,195.8,127.2,127.2,3.65,0.0,1.6,AI)
for t_,z_ in ((195.6,7.3),(197.6,3.65)):quad(V(*P(t_-0.25,126.4,z_)),V(*P(t_+0.25,126.4,z_)),V(*P(t_+0.25,129.8,z_)),V(*P(t_-0.25,129.8,z_)),DK)
band(195.55,197.65,129.85,129.85,0,8.3,CL);band(197.65,197.65,129.85,126.3,0,8.3,CL)
import os
TEX=os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex')
TS={}
def texture(mi,fname,tw,th):
    """Give material mi a hand-made image (tex/fname) repeating every tw x th metres."""
    m=me.materials[mi];nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.join(TEX,fname));t.extension='REPEAT'
    nt.links.new(t.outputs['Color'],b.inputs['Base Color']);TS[mi]=(tw,th,fname)
    if fname.startswith('mesh_'):nt.links.new(t.outputs['Alpha'],b.inputs['Alpha'])   # perforated: the ground shows through
for mi,f,tw,th in ((SE,'seats.png',8,3.2),(SD,'seats.png',8,3.2),(RF,'roof.png',4,4),(GR,'grass.png',22.0,23.2),(TK,'concrete.png',4,4),
                   (FC,'cladding.png',4,4),(DK,'deck.png',4,4),(BL,'glazing.png',4,2.4),(RD,'red_steel.png',1,1),(LV,'louvre.png',2,1),
                   (BG,'concrete.png',4,4),(DR,'deck.png',4,4),(WH,'roof.png',4,4),(LP,'lamps.png',2,1),(SC,'screen.png',1,1),(CL,'clear_roof.png',4,4),(CU,'copper.png',4,4),(AI,'aisle.png',1.2,3.2),
                   (DG,'dark_glass.png',4,3),(WR,'white_render.png',4,4),(BK,'brick.png',1,1),(OR,'panel_orange.png',2,1.5),(GN,'panel_green.png',2,1.5),
                   (DC,'dark_clad.png',4,4),(BC,'blue_clad.png',4,4),(TM,'timber.png',2,2),(MB,'members.png',1,1),(MM,'membrane.png',6,6),(DT,'dirt.png',4,4),(BD,'boards.png',8,1),(SM,'metal_deck.png',4,4),(LB,'lamp_backs.png',2,1.6),(MP,'mesh_panel.png',1,1),(MD,'mesh_dark.png',1,1),(TN,'tan_steel.png',1,1),(BNM,'band.png',7,1.5),(NR,'ne_roof.png',7,1),(ML,'metal_light.png',4,4),(AW,'awning.png',2,1),(TC,'cladding_tan.png',4,4),(CS,'clear_strip.png',4,4),(RR_,'red_render.png',4,4),(RU,'rust_lattice.png',1,1)):
    texture(mi,f,tw,th)
def membrane_pass():
    for f in bm.faces:
        if f.material_index!=RF:continue
        c=f.calc_center_median();t=math.degrees(math.atan2(c.y-c0[1],c.x-c0[0]))%360
        if (86<=t<=140 or t>=305 or t<10) and c.z>10:f.material_index=MM
        elif 222<=t<305 and c.z>10:f.material_index=SM   # south roof: grey ribbed metal deck (photo)
        elif 141<=t<175 and c.z>10:f.material_index=ML   # near roof west of the Members bay: light ribbed metal (photo 640-1460)
        elif 175<=t<222 and c.z>10:f.material_index=MM   # near roof east of it: white fabric with posts (photo 1460-2100)
membrane_pass()
def uvpass():
    uv=bm.loops.layers.uv.verify()
    for f in bm.faces:
        if f.material_index not in TS:continue
        tw,th,_=TS[f.material_index];c=f.calc_center_median();n=f.normal
        tc=math.degrees(math.atan2(c.y-c0[1],c.x-c0[0]));rc=math.hypot(c.x-c0[0],c.y-c0[1])
        er=Vector((math.cos(math.radians(tc)),math.sin(math.radians(tc)),0))
        for l in f.loops:
            X=l.vert.co;t=math.degrees(math.atan2(X.y-c0[1],X.x-c0[0]));dt=(t-tc+180)%360-180
            if f.material_index in (SE,SD,AI):          # seats: rows run round the bowl, v climbs the rake
                r=math.hypot(X.x-c0[0],X.y-c0[1]);u=math.radians(tc+dt)*rc
                al=math.atan2(abs(n.dot(er)),max(1e-3,abs(n.z)));v=r*math.cos(al)+X.z*math.sin(al)
            elif f.material_index in (SM,ML,CS):u=math.radians(tc+dt)*rc;v=math.hypot(X.x-c0[0],X.y-c0[1])   # ribs run down the slope
            elif f.material_index==NR:u=math.radians(tc+dt)*rc;v=math.hypot(X.x-c0[0],X.y-c0[1])   # skylights run round the roof
            elif abs(n.z)>0.7:u,v=X.x,X.y          # flat: plan coordinates
            elif rc>40 and abs(n.dot(er))>0.5:      # bowl walls: arc length round the ground, height
                u=math.radians(tc+dt)*rc;v=X.z
            else:                                    # anything else: along its own face
                tg=Vector((-n.y,n.x,0)).normalized() if Vector((n.x,n.y,0)).length>1e-4 else Vector((1,0,0));u=X.dot(tg);v=X.z if abs(n.z)<0.7 else X.dot(n.cross(tg))
            l[uv].uv=(u/tw,v/th)
        if f.material_index in (LP,LB,BNM,NR):   # lamp rows: one texture row per quad, u at real scale
            vs=[l[uv].uv.y for l in f.loops];v0,v1=min(vs),max(vs)
            for l in f.loops:l[uv].uv=(l[uv].uv.x,(l[uv].uv.y-v0)/max(1e-6,v1-v0))
        if f.material_index==MB:   # the sign is one picture stretched over its panel
            us=[l[uv].uv for l in f.loops];u0=min(q.x for q in us);u1=max(q.x for q in us);v0=min(q.y for q in us);v1=max(q.y for q in us)
            for l in f.loops:q=l[uv].uv;l[uv].uv=((q.x-u0)/max(1e-6,u1-u0),(q.y-v0)/max(1e-6,v1-v0))
from mathutils.bvhtree import BVHTree
bm.normal_update();_bv=BVHTree.FromBMesh(bm)
for k in ('25','27'):
    q=TP[k]
    for i,d in q['rays']:
        hit=_bv.ray_cast(Vector(q['C']),Vector(d))[0]
        if hit is not None:tube(Vector(q['pods'][i]),hit,0.05,0.05,WH,4)
if os.environ.get('MASK')=='1':   # towers only, for the photo clean-up mask
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index not in (CU,LP,RD)],context='FACES')
    for m in me.materials:
        b=m.node_tree.nodes['Principled BSDF'];b.inputs['Emission Color'].default_value=(1,1,1,1);b.inputs['Emission Strength'].default_value=50
else:
    bm.normal_update();uvpass()   # face normals must be current before mapping
bm.normal_update();bm.to_mesh(me);bm.free()
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB')
# camera matched to the photo (undistorted; k1 applied afterwards in Python)
p=CAM['p'];cy_,sy_=math.cos(p[3]),math.sin(p[3]);cp,sp=math.cos(p[4]),math.sin(p[4])
f=Vector((cy_*cp,sy_*cp,sp));r=Vector((sy_,-cy_,0));u=r.cross(f);cr,sr=math.cos(p[5]),math.sin(p[5])
rr=cr*r+sr*u;uu=-sr*r+cr*u
cd=bpy.data.cameras.new('cam');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=p[6]*36/2500;cd.clip_end=5000
cam=bpy.data.objects.new('cam',cd);bpy.context.scene.collection.objects.link(cam)
M=Matrix(((rr.x,uu.x,-f.x),(rr.y,uu.y,-f.y),(rr.z,uu.z,-f.z)));cam.matrix_world=Matrix.Translation(Vector(p[:3]))@M.to_4x4()
sc=bpy.context.scene;sc.camera=cam;sc.render.resolution_x=2500;sc.render.resolution_y=1667;sc.render.film_transparent=True
sun=bpy.data.lights.new('sun','SUN');sun.energy=4.0;so=bpy.data.objects.new('sun',sun);sc.collection.objects.link(so)
# sun fitted to the photo: the NW light tower's head (top 34.7,126.9,54.5 - it leans over the field) casts its shadow tip to
# photo (770,828) = world (27.9,93.7,0); head top re-read 2026-11-18 at (40.15,127.9,54.0)
so.rotation_euler=(Vector((27.9,93.7,0))-Vector((40.15,127.9,54.0))).normalized().to_track_quat('-Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(0.50,0.62,0.85,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.25   # sky light into the shade (photo shade ~58,67,87)
try:sc.render.engine='BLENDER_EEVEE_NEXT'
except Exception:sc.render.engine='BLENDER_EEVEE'
sc.view_settings.view_transform='Standard'
sc.render.filepath=ren;bpy.ops.render.render(write_still=True)
