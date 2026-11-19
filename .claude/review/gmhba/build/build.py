# GMHBA Stadium exterior, built in world metres (x east, y north, z up) from OSM footprints and the
# measurements read off reference photo p1 through the fitted camera. Usage:
#   blender -b --python build.py -- SPDIR OUT.glb RENDER.png
import bpy,bmesh,sys,math,json
import numpy as np
from mathutils import Vector,Matrix
SP,OUT,REN=sys.argv[sys.argv.index('--')+1:]
G=json.load(open(SP+'/geo2.json'));GEO=json.load(open(SP+'/osm/geo.json'));LAY=json.load(open(SP+'/layout.json'))
PCx,PCy=G['PC'];PA=np.array(G['PA']);PR=np.array(G['PR']);OA=np.array(G['OA']);OR=np.array(G['OR'])
def rp(a):return float(np.interp(math.radians(a),PA,PR,period=2*math.pi))
def ro(a):return float(np.interp(math.radians(a),OA,OR,period=2*math.pi))
def dO(a):return ro(a)-rp(a)
def dOs(a):return sum(dO(a+k) for k in range(-6,7))/13.0   # outline smoothed over 12 deg (photo: balconies curve smoothly)
def P(a,d,z):
    r=rp(a)+d;t=math.radians(a);return Vector((PCx+r*math.cos(t),PCy+r*math.sin(t),z))
# Reg Hickey plan from the straight-down satellite (Esri z19, td/edges_e2.py -> east_plan.json, 2026-11-19): roof front
# eF and back eB per 0.5 deg; heights re-solved on p1 so each edge keeps its photo row (td/resolve.py)
EP=json.load(open(SP+'/east_plan.json'))
def _ei(k,a):return float(np.interp(a,EP['a'],EP[k]))
def eF(a):return _ei('f',a)
def eB(a):return _ei('b',a)
def RZa(a,d):f,b=eF(a),eB(a);zf,zb=_ei('zf',a),_ei('zb',a);return zf+(zb-zf)*(d-f)/(b-f)
AS,AN=-57.0,23.0   # satellite: roof's south end at -56.5..-57, north end (upper tier and roof) at 23 (p1 agrees)
CAM1=json.load(open(SP+'/cam.json'))['p']
def _b1():
    p=CAM1;cy,sy,cp,sp,cr,sr=math.cos(p[3]),math.sin(p[3]),math.cos(p[4]),math.sin(p[4]),math.cos(p[5]),math.sin(p[5])
    F=Vector((cy*cp,sy*cp,sp));rr=Vector((sy,-cy,0));u=rr.cross(F);return Vector(p[:3]),F,rr*cr+u*sr,-rr*sr+u*cr
_C1,_F1,_R0,_R1=_b1()
def v1(X):d=X-_C1;return CAM1[8]-CAM1[6]*d.dot(_R1)/d.dot(_F1)
def zkeep(X,Y):
    # height for plan point Y that keeps X's image row on p1 (oblique photo gives heights only)
    v=v1(X);lo,hi=-20.0,80.0
    for _ in range(50):
        m=(lo+hi)/2
        if v1(Vector((Y.x,Y.y,m)))>v:lo=m
        else:hi=m
    return (lo+hi)/2
from functools import lru_cache
def _ray(a,A,B):
    # distance past the pitch line where the ray at angle a meets the line A-B (None if parallel)
    t=math.radians(a);ux,uy=math.cos(t),math.sin(t);dx,dy=B[0]-A[0],B[1]-A[1];den=ux*dy-uy*dx
    if abs(den)<1e-9:return None
    s_=((A[0]-PCx)*dy-(A[1]-PCy)*dx)/den;w=((A[0]-PCx)*uy-(A[1]-PCy)*ux)/den   # w: where on the segment (0..1)
    if not -0.02<=w<=1.02:return None
    return s_-rp(a)
# west stand plan from the straight-down satellite (2026-11-19, td/trace_all.py and unwraps sW1-3, xyW): roof front
# ~10 m past the pitch line all along; back edge (fold tips) 42.7 at 100-157, 40 from 160; low SW canopy outer edge a
# straight line x -123.6 (y 27) to -123.2 (y 82.5), north edge from there through (-108, 73) on to the main roof
def WLE(a):return float(np.interp(a,[100,110,120,130,160,170,215,235,265,275],[11,10.6,10,9.7,9.7,10.1,10.1,9.8,9.6,10.1]))
def WBk(a):return float(np.interp(a,[100,157,160,209],[42.7,42.7,40,40]))
def CEn(a):
    if not 115.0<a<155.5:return 0.0
    q=[_ray(a,(-123.6,27.0),(-123.2,82.5)),_ray(a,(-123.2,82.5),(-80.0,55.7))];q=[v for v in q if v is not None and v>0]
    return min(q) if q else 0.0
# north stand: back edge of the solar sawtooth from the satellite (td/sN.png)
def nB(a):return float(np.interp(a,[36,50,52,60,62,80,82,100],[50.5,50.5,49.75,49.75,49,49,49.75,49.75]))
# SE pocket: the stadium stops at the footpath along Moorabool St (satellite kerb line)
def _xy(a,d):r=rp(a)+d;t=math.radians(a);return (PCx+r*math.cos(t),PCy+r*math.sin(t))
_PK0=_xy(279.0,45.0);_PK1=None
def pK(a):
    # 279..293.5 from the satellite: the block's outer edge (d 45) to its corner at 285.3, then straight to where the kerb line starts (no OSM zig-zag)
    global _PK1
    if _PK1 is None:_PK1=_xy(293.5,_ray(293.5,(34.0,-125.0),(42.0,-100.0),) or 41.27)
    if a<=285.3:return _ray(a,_PK0,_xy(285.3,45.0))
    if a<=293.5:return _ray(a,_xy(285.3,45.0),_PK1)
    v=_ray(a,(34.0,-125.0),(42.0,-100.0));return min(dO(a)-2,v) if v is not None and v>0 else dO(a)-2
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('gmhba');ob=bpy.data.objects.new('gmhba',me);bpy.context.scene.collection.objects.link(ob)
MI={}
def mat(name,img,rough=0.85,clamp=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(SP+'/tex/'+img+'.png')
    if clamp:t.extension='EXTEND'
    nt.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough
    m.use_backface_culling=False;import colorsys;m.diffuse_color=(*colorsys.hsv_to_rgb((len(MI)*0.618)%1,0.6,0.9),1);me.materials.append(m);MI[name]=len(me.materials)-1
for n,i,r,c in(('turf','turf',.95,0),('seats','seats',.8,0),('seatsd','seats_dark',.8,0),('crowds','crowd_shade',.9,0),('seatse','seats_empty',.8,0),('roof','roof',.5,0),
               ('under','under',.8,0),('roofd','roofdark',.6,0),('roofg','roofgrey',.5,0),('wall','wall',.8,0),('fascia','fascia',.5,0),
               ('tower','tower',.4,0),('solar','solar',.3,0),('glass','glass',.2,0),('lamp','lamp',.3,0),('beige','beige',.8,1),
               ('wedge','wedge',.7,1),('wedgef','wedgef',.6,1),('rhend','rhend',.7,1),('slats','slats',.7,1),('players','players',.7,0),('screen','screen',.3,1),('teal','teal',.4,0),('sign','sign',.4,1),('photo','photo',.8,1),('cream','cream',.8,0),('deck','deck',.9,0),('plant','plant',.6,0),('fins','fins',.6,0),('blueband','blueband',.5,0),('aglass','aglass',.15,0),('pave','pave',.9,0),('line','line',.6,0),('pad','pad',.5,0),('logo','logo',.8,1),('navy','navy',.5,0),('deckg','deckg',.85,0),('soffit','soffit',.8,0),('banners','banners',.7,0),('recess','recess',.8,0),('seatback','seatback',.45,0),('seatpan','seatpan',.45,0),('tread','tread',.9,0),('aisle','aisle',.9,0),('seatback_d','seatback_d',.45,0),('seatpan_d','seatpan_d',.45,0),('tread_d','tread_d',.9,0),('aisle_d','aisle_d',.9,0)):mat(n,i,r,c)
for _n in('seatback','seatpan','seatback_d','seatpan_d'):   # seat shells cut out by alpha (glTF alphaMode MASK)
    _m=bpy.data.materials[_n];_nt=_m.node_tree;_ti=[n for n in _nt.nodes if n.type=='TEX_IMAGE'][0];_rd=_nt.nodes.new('ShaderNodeMath');_rd.operation='ROUND'
    _nt.links.new(_ti.outputs['Alpha'],_rd.inputs[0]);_nt.links.new(_rd.outputs[0],_nt.nodes['Principled BSDF'].inputs['Alpha'])
_lm=bpy.data.materials['logo'];_nt=_lm.node_tree;_nt.links.new([n for n in _nt.nodes if n.type=='TEX_IMAGE'][0].outputs['Alpha'],_nt.nodes['Principled BSDF'].inputs['Alpha'])
bm=bmesh.new();uv=bm.loops.layers.uv.new()
def face(vs,m,uvs):
    f=bm.faces.new([bm.verts.new(v) for v in vs]);f.material_index=MI[m]
    for l,q in zip(f.loops,uvs):l[uv].uv=q
    return f
def angles(a0,a1,step=1.0):
    n=max(1,int(round((a1-a0)/step)));return [a0+(a1-a0)*i/n for i in range(n+1)]
TILEM={'wall':8.0,'fascia':8.0,'cream':8.0,'recess':8.0,'teal':8.0,'navy':8.0,'soffit':8.0,'deck':8.0,'deckg':8.0,'pave':8.0,'seats':12.0,'seats_dark':12.0,'seatsd':12.0,'crowds':12.0,'seatse':12.0}   # metres per texture tile
def sweep(a0,a1,prof,mats,tile=8.0,step=1.0):
    # prof(a) -> list of (d,z); quads between neighbouring angles; uv: u by arc, v by run along the profile
    A=angles(a0,a1,step);cols=[[P(a,d,z) for d,z in prof(a)] for a in A]
    for i in range(len(A)-1):
        c0,c1=cols[i],cols[i+1]
        for k in range(len(c0)-1):
            if mats[k] is None or mats[k] in SEATM:continue
            tl=TILEM.get(mats[k],tile)   # hand-painted textures are drawn to a fixed size in metres
            u0=i*step*math.radians(1)*(rp(A[i])+20)/tl;u1=u0+step*math.radians(1)*(rp(A[i])+20)/tl
            l=(c0[k+1]-c0[k]).length/tl
            v0,v1=(l,0) if c0[k+1].z<c0[k].z-1e-6 else (0,l)   # image top stays up on walls that run downward
            face([c0[k],c1[k],c1[k+1],c0[k+1]],mats[k],[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
    for k,m in enumerate(mats):
        if m in SEATM:seat_rows(A,[prof(a) for a in A],k,m,step)
SEATM=('seats','seatsd','crowds','seatse')
def seat_rows(A,profs,k,m,step):
    # p12: real seat rows instead of a flat rake. Each row is a concrete tread and riser, a seat pan 0.42 m up and a
    # back tilted up to 0.88 m; the shells are cut out of hand-drawn textures by alpha. Aisles: every 8th degree step.
    sfx='_d' if m in('seatsd','crowds') else ''
    runs=[p[k+1][0]-p[k][0] for p in profs]
    if min(runs)<=0.5:
        print('seat_rows flat fallback',k,m);return
    n=max(1,int(round(float(np.median(runs))/0.8)));ul=[0.0]*n
    def pt(i,j,f,dz):
        (d0,z0),(d1,z1)=profs[i][k],profs[i][k+1];dd=(d1-d0)/n
        return P(A[i],d0+dd*(j+f),z0+(z1-z0)*j/n+dz)
    def zr(i,j):(d0,z0),(d1,z1)=profs[i][k],profs[i][k+1];return z0+(z1-z0)*j/n
    for i in range(len(A)-1):
        ais=(i%8)==4
        for j in range(n):
            L=(pt(i+1,j,0.15,0)-pt(i,j,0.15,0)).length/2.0;u0,u1=ul[j],ul[j]+L;ul[j]=u1
            rise=zr(i,j+1)-zr(i,j);r=j%4
            a,b=lambda f,dz:pt(i,j,f,dz),lambda f,dz:pt(i+1,j,f,dz)
            tm=('aisle' if ais else 'tread')+sfx
            face([a(0,0),b(0,0),b(1,0),a(1,0)],tm,[(u0,1),(u1,1),(u1,0.02),(u0,0.02)])                       # tread, nosing at the front
            (d0,z0),(d1,z1)=profs[i][k],profs[i][k+1]
            ra=P(A[i],d0+(d1-d0)*(j+1)/n,zr(i,j));rb=P(A[i+1],profs[i+1][k][0]+(profs[i+1][k+1][0]-profs[i+1][k][0])*(j+1)/n,zr(i+1,j))
            face([ra,rb,rb+Vector((0,0,zr(i+1,j+1)-zr(i+1,j))),ra+Vector((0,0,rise))],tm,[(u0,0.05),(u1,0.05),(u1,0.15),(u0,0.15)])   # riser
            if ais:continue
            vt,vb=1-r/4-0.001,1-(r+1)/4+0.001
            face([a(0.15,0.42),b(0.15,0.42),b(0.62,0.42),a(0.62,0.42)],'seatpan'+sfx,[(u0,vt),(u1,vt),(u1,vb),(u0,vb)])   # pan, front lip first
            face([a(0.62,0.40),b(0.62,0.40),b(0.75,0.88),a(0.75,0.88)],'seatback'+sfx,[(u0,vb),(u1,vb),(u1,vt),(u0,vt)])   # back, top lip up
def arc(a0,a1):
    s=0;a=a0
    while a<a1-1e-9:s+=ro(math.degrees(math.radians(a)) if False else a)*math.radians(0.5);a+=0.5
    return s
def facade(a0,a1,z0,z1,m,tex=None,tilew=None,dfn=None,step=0.5):
    # vertical wall on the outline (or at offset dfn(a)); tex=(ta0,ta1,H) maps a cropped photo strip
    A=angles(a0,a1,step)
    for i in range(len(A)-1):
        a,b=A[i],A[i+1];da=dfn(a) if dfn else dO(a);db=dfn(b) if dfn else dO(b)
        if tex:
            L=arc(tex[0],tex[1]);ua=arc(tex[0],a)/L;ub=arc(tex[0],b)/L;va=z0/tex[2];vb=z1/tex[2]
        else:
            ua=arc(a0,a)/tilew;ub=arc(a0,b)/tilew;vh=tilew*(440/512 if m=='players' else 1.0);va=z0/vh;vb=z1/vh
        face([P(a,da,z0),P(b,db,z0),P(b,db,z1),P(a,da,z1)],m,[(ua,va),(ub,va),(ub,vb),(ua,vb)])
# ---- turf and the ground plane inside the outline
tc=Vector((PCx,PCy,0.0))
MK=json.load(open(SP+'/marks.json'));MF=json.load(open(SP+'/mfit.json'))   # pitch frame fitted to p1's marks (1.25 px)
MC=Vector((MF['cc'][0],MF['cc'][1],0));MX=Vector((MF['ax'][0],MF['ax'][1],0));MN=Vector((-MF['ax'][1],MF['ax'][0],0))
def tuv(q):d=q-MC;return (d.dot(MX)/40.0,(d.dot(MN)-1.5)/40.0)   # mowing bands: 40 m tile, along-ground bands offset 1.5 m
FIELD=False   # director 2026-11-18: "Leave field out" - the game draws its own grass inside the boundary fence
A=angles(-180,180,2)
for i in range(len(A)-1 if FIELD else 0):
    a,b=A[i],A[i+1];pa,pb=P(a,1.5,0.02),P(b,1.5,0.02)
    face([tc,pa,pb],'turf',[tuv(q) for q in(tc,pa,pb)])
# ---- ground markings (marks.py, AFL dimensions, fitted to p1): 0.12 m white lines just above the turf
def strip(a,b,w=0.12,z=0.05):
    a=Vector((a[0],a[1],z));b=Vector((b[0],b[1],z));t=(b-a);t.z=0
    if t.length<1e-6:return
    n=Vector((-t.y,t.x,0)).normalized()*w/2;face([a-n,b-n,b+n,a+n],'line',[(0,0),(1,0),(1,1),(0,1)])
for l in (MK['lines'] if FIELD else []):
    pts=l['pts']+([l['pts'][0]] if l['closed'] else [])
    for a_,b_ in zip(pts,pts[1:]):strip(a_,b_)
# centre-ground painting on p1 (maroon field, white mark): 12 x 4.5 m, long side along the photo's across-frame line
_lc=MC+MX*(-1.0)+MN*(-27.0);_lu=(MX*(-11.7)+MN*(-6.9)).normalized();_lv=Vector((-_lu.y,_lu.x,0))
if FIELD:face([_lc-_lu*6-_lv*2.25+Vector((0,0,0.04)),_lc+_lu*6-_lv*2.25+Vector((0,0,0.04)),_lc+_lu*6+_lv*2.25+Vector((0,0,0.04)),_lc-_lu*6+_lv*2.25+Vector((0,0,0.04))],'logo',[(0,0),(1,0),(1,1),(0,1)])
# ---- seating bowls (d,z) profiles per sector, pitch line d=0
def bowl_w(a):
    e=(min(dO(a)-2,44.0,WBd(a)-1.0) if a<156 else min(dO(a)-2,44.0)) if not 209<=a<=279 else DBf(a)-3.5;pts=[(1.5,0.02),(1.5,1.2),(14,7),(14.5,7.4),(14.5,9.0),(30,18),(e,18.5),(e,15.0)]
    def rz(d):  # lowest roof height over d (leading edge 23 m to the folded back edge), keep seats 1.5 m under it
        le=WLE(a);bd=WBd(a);t=0.0 if bd<=le else max(0.0,min(1.0,(d-le)/(bd-le)));amp=1.5*(1-0.6*CW(a));zf=ZF(a)
        return zf+(WBz(a)-amp-zf)*t
    return [(d,min(z,rz(d)-1.5)) if i>1 else (d,z) for i,(d,z) in enumerate(pts)]
def bowl_n(a):   return [(1.5,0.02),(1.5,1.2),(20,10),(20.5,10.4),(20.5,13),(40,21),(nB(a)-2.5,21.5),(nB(a)-2.5,25)]
def RZ(d):return 17.6-4.4*(d-8.2)/38.5   # Reg Hickey roof top: front edge read off p1 zoom (v 288 at u 628), back (46.7,13.2)
def bowl_e(a):
    ds=min(20.0,eB(a)-1.5);w=eB(a)-0.3
    return [(1.5,0.02),(1.5,1.2),(10,5.1-0.054*a),(10.3,5.3-0.054*a),(10.5,6.6-0.07*a),(ds,min(11.3-0.096*a,13.4)),(ds+0.5,min(11.5-0.096*a,13.6)),(ds+0.5,RZa(a,ds+0.5)-0.7),(w,RZa(a,w)-0.7),(w,0.02)]
M8=['wall','wall','seats','wall','glass','seats','wall','wall']
def rh_le(a):return 19.25-0.08*a          # Reg Hickey roof leading edge height (photo: rises to the south)
def rh_top(a):return rh_le(a)+2.0
# SE pocket (p1: the scoreboard's legs reach grass at ground level, so the seat bank in front stays under ~4 m)
sweep(279,360+AS,lambda a:[(1.5,0.02),(1.5,1.2),(10,4.0),(10.5,4.0),(10.5,0.3),(pK(a),0.3),(pK(a),0.02)],['wall','seatse','wall','wall','turf','wall'],tile=6)
for c in(280,287.5,295):sweep(c-0.25,c+0.25,lambda a:[(1.5,1.25),(10,4.05)],['wall'],tile=6,step=0.5)   # p1 zoom: three pale aisles in the pocket bank
sweep(36,100,bowl_n,['wall','seatsd','wall','glass','crowds','wall','wall'],tile=6)
sweep(AS,AN,bowl_e,['wall','seats','wall','teal','seats','wall','glass','under','wall'],tile=6)
# NE corner a 23..36 (satellite: open seat rows to d 14, low flat concourse roof behind to the red-roofed strip; p1: seat top
# z 6.2, concourse roof z 9.5, white glazed end block of the Reg Hickey at 23..27.5 up to 15 m)
def DNE(a):return float(np.interp(a,[23,25,28,31,36],[30.0,35.0,41.0,46.0,46.0]))   # satellite: inside the red footpath band
sweep(AN,36,lambda a:[(1.5,0.02),(1.5,1.2),(14,6.2),(14,9.5),(DNE(a),9.5),(DNE(a),0.02)],['wall','seats','wall','roofg','wall'],tile=6)
_xb=lambda a,d,z:P(a,d,z)
sweep(AN,27.5,lambda a:[(9.0,0.02),(9.0,15.0),(eB(AN),15.0),(eB(AN),0.02)],['fascia','roofg','fascia'],tile=6)
face([P(27.5,9.0,0),P(27.5,eB(AN),0),P(27.5,eB(AN),15.0),P(27.5,9.0,15.0)],'glass',[(0,0),(2,0),(2,2),(0,2)])
# south end of the Reg Hickey Stand closed by its end wall (p1: glass stair bay, white block, banded floors)
_w=eB(AS)-0.3;_ec=[(3.1,0),(_w,0),(_w,RZa(AS,_w)-0.7),(3.1,RZa(AS,3.1)-0.7)]
face([P(AS,d_,z_) for d_,z_ in _ec],'rhend',[(d_/47,z_/17) for d_,z_ in _ec])
# annex on the street side of the stand's south end (satellite plan; p1: white banded block, top 12.5 m between the
# z 12 and z 16 outlines). Walls carry the end texture's banded floors (u 0.42-1.0)
_AX=[(37,-84),(52,-84),(52,-90),(46,-101.5),(37,-101.5)];_AH=12.5
_L=[math.hypot(_AX[(i+1)%5][0]-_AX[i][0],_AX[(i+1)%5][1]-_AX[i][1]) for i in range(5)]
for i in range(5):
    x0,y0=_AX[i];x1,y1=_AX[(i+1)%5];uw=0.58*_L[i]/28
    face([Vector((x0,y0,0)),Vector((x1,y1,0)),Vector((x1,y1,_AH)),Vector((x0,y0,_AH))],'rhend',[(0.42,0),(0.42+uw,0),(0.42+uw,_AH/17),(0.42,_AH/17)])
face([Vector((x,y,_AH)) for x,y in _AX],'roofg',[((x-37)/8,(y+101.5)/8) for x,y in _AX])
def ez(a,d):z0=6.6-0.07*a;z1=min(11.3-0.096*a,13.4);return z0+(z1-z0)*(d-10.5)/9.5+0.06
# Reg Hickey upper-tier aisle mouths (dark slots in p1 every ~9 deg, read at 18.5, 11, 1.5, -7.5, -16, -36, -46)
for c in(18.5,11,1.5,-7.5,-16,-26,-36,-46):
    sweep(c-0.6,c+0.6,lambda a:[(13,ez(a,13)),(min(19.6,eB(a)-1.9),ez(a,min(19.6,eB(a)-1.9)))],['glass'],tile=6,step=0.6)
# ---- facades on the outline
facade(169.2,192.6,0,LAY['beige'][2],'beige',tex=LAY['beige'])
facade(154.0,169.2,0,16.5,'wedge',tex=LAY['wedge'])
# grey box on top of the wedge (p1 x 263-381, top y 452): 156.9..165.5 deg, 16.5..22.0 m, 14 m deep, flat roof
facade(156.9,165.5,16.5,22.0,'wedge',tex=LAY['wedge'])
# NW corner stair tower: satellite (Esri z19) roof 99.5..105.5 deg, d 43.3..48.5; p1 top at about 16.5 m (grey box behind the NW tower)
sweep(99.5,105.5,lambda a:[(43.3,0.0),(43.3,16.5),(48.5,16.5),(48.5,0.0)],['wedge','roofg','wedge'],tile=6,step=0.5)
for a_ in(99.5,105.5):face([P(a_,43.3,0),P(a_,48.5,0),P(a_,48.5,16.5),P(a_,43.3,16.5)],'wedge',[(0,0),(1,0),(1,1),(0,1)])
sweep(156.9,165.5,lambda a:[(dO(a),22.0),(dO(a)-3,22.0)],['roofd'],tile=6)
sweep(156.9,165.5,lambda a:[(dO(a)-3,21.98),(WBk(a)-0.5,21.98)],['roofg'],tile=6)   # satellite: box roof reaches back to the stand's roof
a_=156.9;face([P(a_,dO(a_),16.5),P(a_,dO(a_)-3,16.5),P(a_,dO(a_)-3,22.0),P(a_,dO(a_),22.0)],'wall',[(0,0),(1,0),(1,1),(0,1)])
# p1 x 381-417: the box's east side recedes from the front corner (165.5) back toward the Premiership block (169.2)
_r0=P(165.5,dO(165.5),16.5);_r1=Vector(json.load(open(SP+'/wedge.json'))['Bk'])  # p1 back corner x 417 y 470
face([_r0,_r1,_r1+Vector((0,0,5.5)),_r0+Vector((0,0,5.5))],'wedge',[(0,0),(1,0),(1,.25),(0,.25)])
face([P(165.5,dO(165.5),22.0),P(165.5,dO(165.5)-3,22.0),_r1+Vector((0,0,5.5))],'roofd',[(0,0),(1,0),(1,1)])
# GMHBA wedge (p1 x 231-417, y 470-560): top edge A-B at 16.5 m sticks out of the block, front plane vertical to the
# bottom tip, lower facet leans back to the bottom-left corner, side face back to the block, flat dark top
WJ=json.load(open(SP+'/wedge.json'));WA,WB,WK,WT,WBL,WSB=[Vector(WJ[k]) for k in('A','B','Bk','tip','botL','sb')];WL=WJ['L']
_ex=(WB-WA).normalized()
def wuv(X):return ((X-WA).dot(_ex)/WL,X.z/16.5)
def on_outline(X):
    a=math.degrees(math.atan2(X.y-PCy,X.x-PCx));return P(a,dO(a),X.z)
WK=WB+(WK-WB)*0.52;WK=on_outline(WK);WA0=on_outline(WA)
face([WA,WT,WB],'wedgef',[wuv(q) for q in(WA,WT,WB)])
face([WA,WBL,WT],'wedgef',[wuv(q) for q in(WA,WBL,WT)])
WSB2=on_outline(Vector((WK.x,WK.y,WSB.z)))
face([WB,WT,WSB,WSB2,WK],'wedgef',[(0,1),(0,.27),(.03,.27),(.1,.27),(.1,1)])  # p1: side is the same dark cladding
face([WA,WB,WK,WA0],'roofd',[(0,0),(1,0),(1,1),(0,1)])
WBL0=on_outline(WBL);WT0=on_outline(WT)
face([WBL,WBL0,WT0,WT],'roofd',[(0,0),(0,1),(1,1),(1,0)])
face([WT,WT0,WSB2,WSB],'roofd',[(0,0),(0,1),(1,1),(1,0)])
face([WA,WA0,WBL0,WBL],'wedgef',[wuv(q) for q in(WA,WA0,WBL0,WBL)])
facade(193.9,209.0,0,LAY['slats'][2],'slats',tex=LAY['slats'])
facade(192.6,193.9,0,23.4,'wall',tilew=8)
# Players Stand, measured on p1 2026-11-18 (rhm/rhe/rhz.py): ground contacts of the navy ground-floor columns put them at
# d 34 (the OSM outline, d~40, is the roof edge here, as at the annex). Band front on the column line: white 5.3-8.4,
# navy stripe 8.4-8.9, white 8.9-11.4; open ground floor behind (dark back wall d 28.3-31.5, soffit at 5.3); grey deck at
# 10.0 back to d 24, white back wall to 12.0, dark above; white deck columns on the roof's back ridge points; fence banners.
# band line from its stripe (8.65), top (11.4) and bottom (5.3) edges on p1, all three agree within 0.3 m (2026-11-18):
_BA=[209,217.3,220.6,225.5,231.1,234.4,238.1,243.2,246.6];_BD=[33.6,33.8,34.1,34.6,35.5,35.75,36.6,37.7,38.8]
def DBf(a):return float(np.interp(a,_BA,_BD)) if a<=246.6 else dO(a)-0.5   # beyond 246.6 the stand turns behind the roof
def GB(a):return float(np.interp(a,[221.6,229.8],[28.3,31.5])) if a<=229.8 else DBf(a)-4.0
def DK(a):return DBf(a)-10.0   # deck back wall (p1: d 24 where the band is at 34)
facade(209,279,0,5.3,'aglass',tilew=8,dfn=GB)
sweep(209,279,lambda a:[(GB(a),5.3),(DBf(a),5.3)],['soffit'],tile=8)
sweep(209,279,lambda a:[(GB(a),0.03),(37.1,0.03)],['pave'],tile=8)
facade(209,279,5.3,8.4,'fascia',tilew=8,dfn=DBf)
facade(209,279,8.4,8.9,'navy',tilew=8,dfn=DBf)
facade(209,279,8.9,11.4,'fascia',tilew=8,dfn=DBf)
sweep(209,279,lambda a:[(DBf(a),11.4),(DBf(a)-0.3,11.4),(DBf(a)-0.3,10.0)],['fascia','fascia'],tile=8)
sweep(209,279,lambda a:[(DBf(a)-0.3,10.0),(DK(a),10.0)],['deckg'],tile=8)
facade(209,279,10.0,12.0,'fascia',tilew=8,dfn=DK)
facade(209,279,12.0,14.4,'roofd',tilew=8,dfn=DK)
sweep(209,279,lambda a:[(DK(a),14.3),(DBf(a)-3.5,18.2)],['recess'],tile=8)   # underside of the seat rake above the deck
for a in(209,279):face([P(a,DBf(a),0),P(a,GB(a),0),P(a,GB(a),5.3),P(a,DK(a),10),P(a,DK(a),14.4),P(a,DBf(a),11.4)],'fascia',[(0,0),(1,0),(1,.4),(1,.7),(1,1),(0,.8)])
facade(211,230,0,1.2,'wall',tilew=20,dfn=lambda a:37.1)   # bare fence: director 2026-11-18 sponsor boards 'C: no boards'
facade(279,360+AS,0,7.5,'wall',tilew=8,dfn=pK)
face([P(279,dO(279)-2,0),P(279,pK(279),0),P(279,pK(279),7.5),P(279,dO(279)-2,7.5)],'wall',[(0,0),(1,0),(1,1),(0,1)])   # end of the block that stands out past the Players Stand back
facade(36,100,0,25,'wall',tilew=8,dfn=lambda a:nB(a)-0.5)
facade(100,125,0,14.5,'aglass',tilew=8,dfn=lambda a:WBk(a)-1.0)
# Brownlow annex (photo): 14.5 m glass atrium on the outline bulge under the long canopy of the pleated roof
facade(151.9,154,0,14.5,'aglass',tilew=8)   # p1: annex glass reads dark (39) with dark frames; top 15.6 m from p1 profiles x 70/123/180 (y 469-478)
# p1 zoom: grey fin screen 151.9-156.9, 5.4-11.8 m, in front of the glass; blue concourse band 3.2-5.1 m
facade(151.9,156.9,5.4,11.8,'fins',tilew=8,dfn=lambda a:dO(a)+0.3)
facade(147,156.9,3.2,5.1,'blueband',tilew=8,dfn=lambda a:dO(a)+0.35)
# plant rooms on top of the GMHBA wedge (photo x 265-415, y 405-445)
def blockpolar(a0,a1,d0,d1,z0,z1,m):
    sweep(a0,a1,lambda a:[(d0,z0),(d0,z1),(d1,z1),(d1,z0)],[m,m,m],tile=6)
    for a in(a0,a1):face([P(a,d0,z0),P(a,d1,z0),P(a,d1,z1),P(a,d0,z1)],m,[(0,0),(1,0),(1,1),(0,1)])
# p1 zoom: cream precast block flush with the box front 156.9-162.3 (x 262-335) to 24.2 m, beige deck on top,
# dark 1.5 m parapet on its west half (x 262-307), dark east end (x 337-350); plant enclosure 162.3-165.5 (x 350-385)
blockpolar(156.9,162.3,dO(159.6)-8,dO(159.6),22.0,24.2,'cream')
sweep(156.9,162.3,lambda a:[(dO(159.6),24.21),(dO(159.6)-8,24.21)],['deck'],tile=6)
blockpolar(156.9,160.3,dO(158.6)-0.5,dO(158.6),24.2,25.7,'roofd')
face([P(162.31,dO(159.6),22.0),P(162.31,dO(159.6)-8,22.0),P(162.31,dO(159.6)-8,24.2),P(162.31,dO(159.6),24.2)],'roofd',[(0,0),(1,0),(1,1),(0,1)])
facade(162.3,165.5,22.0,25.0,'plant',tilew=8,dfn=lambda a:dO(a)-1.0)
def tube(p0,p1,r,m,n=6):
    ax=(p1-p0).normalized();t=ax.orthogonal().normalized();s=ax.cross(t)
    for i in range(n):
        u0=2*math.pi*i/n;u1=2*math.pi*(i+1)/n
        o0=(t*math.cos(u0)+s*math.sin(u0))*r;o1=(t*math.cos(u1)+s*math.sin(u1))*r
        face([p0+o0,p0+o1,p1+o1,p1+o0],m,[(0,0),(1,0),(1,1),(0,1)])
# ---- pleated roof, west and north (folded plates: straight leading edge, back edge zigzags up and down)
def pleat(a0,a1,le_d,le_z,bk_d,bk_z,amp,nb,faces=('roof','roof'),ampf=lambda a:1.0,ph=0):
    n=nb*2;A=angles(a0,a1,(a1-a0)/n)
    for i in range(n):
        a,b=A[i],A[i+1];am=(a+b)/2
        F0,F1=P(a,le_d(a),le_z(a)),P(b,le_d(b),le_z(b))
        hi=(i%2==ph)
        B0=P(a,bk_d(a),bk_z(a)+(amp if hi else -amp)*ampf(a));B1=P(b,bk_d(b),bk_z(b)+(-amp if hi else amp)*ampf(b))
        Bm=P(am,bk_d(am),bk_z(am))
        face([F0,F1,Bm],faces[i%2],[(0,0),(1,0),(.5,1)])
        face([F0,Bm,B0],faces[(i+1)%2],[(0,0),(.5,1),(0,1)])
        face([F1,B1,Bm],faces[(i+1)%2],[(1,0),(1,1),(.5,1)])
        # photo: white flashing on every ridge and along the zigzag back edge, dark gutter in every valley
        tube(B0,B1,0.22,'fascia',4)
        tube(F0,B0,0.12,'fascia' if hi else 'roofd',4)
    for i in range(n):  # white fascia band under the leading edge
        a,b=A[i],A[i+1]
        face([P(a,le_d(a),le_z(a)-0.9),P(b,le_d(b),le_z(b)-0.9),P(b,le_d(b),le_z(b)),P(a,le_d(a),le_z(a))],'fascia',[(0,0),(1,0),(1,1),(0,1)])
def ramp(a,a0,a1,b0,b1):
    if a<=a0 or a>=b1:return 0.0
    if a<a1:return (a-a0)/(a1-a0)
    if a<=b0:return 1.0
    return (b1-a)/(b1-b0)
def CW(a):return ramp(a,118,132,149,156)   # low SW canopy, outer edge measured on p1: straight line x=-113 from y 38.2 to 88.9
def CE(a):
    t=math.radians(min(149.0,max(132.0,a)));return (-113.0-PCx)/math.cos(t)-rp(a)
def WBdo(a):
    w=CW(a);v=(1-w)*min(dO(a),47.0)+w*CE(a)
    if a>222:t=min(1.0,(a-222)/6.3);v=(1-t)*v+t*float(np.interp(a,BA[1:],BD[1:]))
    return v
def WBd(a):
    v=max(WBk(a),CEn(a))
    if a>222:t=min(1.0,(a-222)/6.3);v=(1-t)*v+t*float(np.interp(a,BA[1:],BD[1:]))
    return v
def WBzo(a):
    w=CW(a);base=25.0 if a<154 else (24.0 if a<209 else 24.0-1.5*min(1,(a-209)/8))
    return (1-w)*base+w*12.4
@lru_cache(None)
def WBz(a):return zkeep(P(a,WBdo(a),WBzo(a)),P(a,WBd(a),0))   # back edge on the satellite, p1 row kept
EA=[209,229.8,235.9,242.5,248.8,253.6,263.4,271.8,274.6];ED=[15,15.8,13.9,13.8,13.4,12.9,13.4,13.3,13.3]   # roof leading edge read on p1 at z 23
def WLEo(a):return float(np.interp(a,EA,ED))
@lru_cache(None)
def ZF(a):return zkeep(P(a,WLEo(a),23.0),P(a,WLE(a),0))   # leading edge on the satellite, p1 row kept
BA=[222,228.3,234.6,241.6,249.1,252.0,256.0,260.9,266.8,273.2,274.6];BD=[None,40,40,38.8,41.8,41.6,40.3,39.6,39.8,40.4,40.4]  # SE roof outer edge, p1 at z 22.5
sweep(100,209,bowl_w,['wall','seats','wall','glass','seats','wall','wall'],tile=6)
sweep(209,279,bowl_w,['wall','seats','wall','glass','seats','recess','recess'],tile=6)   # p1: rake back over the deck is a dark recess  # one material per profile segment
EE=167.9-2*6.04   # main canopy: front fold vertices on p1 every 6.04 deg from 167.9 (z 23); old pleat keeps 100..EE (low SW canopy)
pleat(100,EE,WLE,ZF,WBd,WBz,1.5,9,faces=('roofg','roofg'),ampf=lambda a:(1-0.9*CW(a)))   # p1: low SW canopy is grey metal (median 160), not white; outer edge straight (2 px steps), fold 0.15 m there
# second fold row fitted on p1 (6 points, 2 px rms): 1.6 deg past each front vertex, 9.3 m behind the leading edge, z 20.4.
# back ends on p1 (outline d, 2 bays): each ridge runs from a front vertex back to 1.55 deg before it, each valley from the
# second-row point back to 2.14 deg past the front vertex; back edge z 23.3 (p1 reads 23.0-23.5).
# satellite (Esri z19, 2026-11-19): front vertices = gutter gaps between the white triangles at d 11.5-13
FK=[EE,160.7,167.05,173.45,179.9,186.2,192.5,198.55,204.5,210.1,215.1,220.3,225.4,230.5,235.55,240.6,245.7,250.65,255.7,260.8,265.75,270.9,274.6]
# satellite back edge, per bay: notch (ridge back) then tip (valley back), (angle, d); box zone 155.8-167 stays smooth
BKN=[None,None,(168.88,39.2),(175.11,36.16),(181.04,35.36),(186.63,35.79),(191.95,37.61),(200.25,38.88),(207.75,38.75),
 (210.5,37.25),(215.25,36.75),(221.0,36.67),(226.5,36.5),(231.75,36.75),(237.25,36.5),(242.75,36.5),(248.25,36.67),
 (253.25,36.75),(258.75,37.0),(263.75,37.58),(270.5,38.5)]
BKT=[None,None,(172.96,42.06),(178.3,40.6),(183.96,39.99),(189.23,40.78),(193.49,42.67),(204.0,39.5),(209.25,39.25),
 (212.5,39.96),(218.25,39.67),(223.75,39.58),(229.25,39.58),(234.75,39.33),(240.25,39.31),(245.5,39.5),(250.75,39.46),
 (255.75,38.93),(261.75,40.17),(267.0,40.58),(272.75,40.72)]
# entry k = bay k (FK[k]..FK[k+1]); the ridges are not radial, so notches drift from +0.4 deg past the vertex (210) to -2 (265); last part-bay smooth
def BZ(a):return min(23.3,WBz(a))
def FP(a):return P(a,WLE(a),ZF(a))
def AP(a):aa=min(a,274.6);return P(aa,WLE(aa)+9.3,zkeep(P(aa,WLEo(aa)+9.3,20.4),P(aa,WLE(aa)+9.3,0)))
# p1 roof lip over the Players Stand (lip.json, 56 points, traced 2026-11-18): a sawtooth, low 21.0 at the ridge backs, high
# 22.1 at the valley backs, for a 209-241 (beyond, the lip turns away behind the roof)
def _bk(ad,zr):a,d=ad;return P(a,d,zr if 209<=a<=241 else BZ(a))
def HK(k):
    if k>=len(FK)-1:return _bk((274.6,WBd(274.6)),21.0)
    n=BKN[k] if k<len(BKN) else None
    return _bk(n if n else (FK[k],WBd(FK[k])),21.0)
def LK(k):
    t=BKT[k] if k<len(BKT) else None;m=0.5*(FK[k]+FK[k+1])
    return _bk(t if t else (m,WBd(m)),22.1)
for k in range(len(FK)-1):
    a0,a1=FK[k],FK[k+1];F0,F1,A0,H0,H1,L0=FP(a0),FP(a1),AP(0.5*(a0+a1)),HK(k),HK(k+1),LK(k)
    face([F0,F1,A0],'roof',[(0,0),(1,0),(.2,1)])                                  # white face off the leading edge
    face([A0,F1,H1],'roofg',[(0,0),(1,0),(1,1)]);face([A0,H1,L0],'roofg',[(0,0),(1,1),(0,1)])
    face([F0,A0,L0],'roofg',[(0,0),(1,0),(1,1)]);face([F0,L0,H0],'roofg',[(0,0),(1,1),(0,1)])
    tube(F1,H1,0.14,'fascia',4);tube(A0,L0,0.14,'roofd',4);tube(F0,A0,0.08,'roofd',4)
    tube(H0,L0,0.22,'fascia',4);tube(L0,H1,0.22,'fascia',4)
    face([P(a0,WLE(a0),ZF(a0)-0.9),P(a1,WLE(a1),ZF(a1)-0.9),F1,F0],'fascia',[(0,0),(1,0),(1,1),(0,1)])
e=274.6;face([P(e,WLE(e),ZF(e)-0.9),FP(e),HK(len(FK)-1),P(e,WBd(e),BZ(e)-0.9)],'fascia',[(0,0),(1,0),(1,1),(0,1)])
for a in angles(118,156,0.5):  # canopy outer fascia, 12.4 down to 11.0 (p1)
    b=a+0.5;w0,w1=CW(a),CW(b)
    if w0+w1==0:continue
    face([P(a,WBd(a),WBz(a)-1.4*w0),P(b,WBd(b),WBz(b)-1.4*w1),P(b,WBd(b),WBz(b)),P(a,WBd(a),WBz(a))],'roofd',[(0,0),(1,0),(1,1),(0,1)])   # p1: dark fascia band (79,81,91)
def _czd(a,d):  # low canopy underside height at distance d (lowest fold point)
    le=WLE(a);bd=WBd(a);t=0.0 if bd<=le else max(0.0,min(1.0,(d-le)/(bd-le)))
    zf=ZF(a);return zf+(WBz(a)-zf)*t-1.5*(1-0.9*CW(a))-0.05
# Brownlow annex glass box: open plaza under the low canopy, glass set back. Base line back-projected from p1 (z 0):
# x74 y507 -> (133.1,65.7) ... x192 y518 -> (142.0,51.8); beyond 142 straight on in plan to the fin block at 151.9.
_GA=[133.1,134.8,136.6,138.1,139.9,142.0];_GD=[65.7,62.2,58.2,55.9,54.1,51.8]
_q0=P(138.1,55.9,0);_q1=P(142.0,51.8,0)
def GL(a):
    if a<=133.1:return dO(a)
    if a<=142.0:return float(np.interp(a,_GA,_GD))
    t=math.radians(a);dx,dy=_q1[0]-_q0[0],_q1[1]-_q0[1];ux,uy=math.cos(t),math.sin(t)
    s_=((_q0[0]-PCx)*dy-(_q0[1]-PCy)*dx)/(ux*dy-uy*dx);return s_-rp(a)
A_=angles(125,151.9,0.5)
for k in range(len(A_)-1):
    a,b=A_[k],A_[k+1];da,db=GL(a),GL(b);za,zb=_czd(a,da),_czd(b,db);ua,ub=arc(125,a)/8,arc(125,b)/8
    face([P(a,da,0),P(b,db,0),P(b,db,zb),P(a,da,za)],'aglass',[(ua,0),(ub,0),(ub,zb/6.875),(ua,za/6.875)])
sweep(118,156.9,lambda a:[(min(GL(a),dO(a))-0.2,0.03),(max(dO(a)+0.6,WBd(a)+0.8 if CW(a)>0 else 0),0.03)],['pave'],tile=8,step=0.5)   # plaza floor under the low canopy, inside the OSM footprint
_e=151.9;face([P(_e,GL(_e),0),P(_e,dO(_e),0),P(_e,dO(_e),_czd(_e,dO(_e))),P(_e,GL(_e),_czd(_e,GL(_e)))],'aglass',[(0,0),(1,0),(1,1),(0,1)])
for (cx_,cy_) in((-116.0,74.8),(-113.2,62.7)):  # canopy columns read off p1, moved with the canopy edge (x -113 -> -123.4)
    cx_-=10.4;aa=math.degrees(math.atan2(cy_-PCy,cx_-PCx));dd=math.hypot(cx_-PCx,cy_-PCy)-rp(aa)
    tube(Vector((cx_,cy_,0)),Vector((cx_,cy_,_czd(aa,dd))),0.3,'roofd',8)   # p1: dark steel columns, up to the underside
# north solar sawtooth: 10 peak tips on p1 fitted (0.96 px rms) to tips every 3.78 deg from a=36.94, d=dOs+8.3, z 27.36-0.044(a-80)
@lru_cache(None)
def NZ(a):return zkeep(P(a,dOs(a)+8.3,25.56-0.044*(a-80)),P(a,nB(a),0))   # back edge moved to the satellite, p1 row kept
pleat(35.05,99.31,lambda a:20,lambda a:24,nB,NZ,1.8,17,faces=('roof','roof'),ph=1)   # director 2026-11-19 gate: p1 shows pale grey folded sheeting, no navy stripes
face([P(99.31,20,24),P(99.31,nB(99.31),NZ(99.31)-1.8),P(100,nB(100),NZ(100)-1.8),P(100,20,24)],'roof',[(0,0),(1,0),(1,1),(0,1)])
# ---- Reg Hickey roof (photos p1,p2,p3): thin flat light-grey cantilever sloping down to the back, dark underside and
# front fascia; nine curved white masts in radial planes rise from the back of the roof and land on its front half
sweep(AS,AN,lambda a:[(eF(a),RZa(a,eF(a))),(eB(a),RZa(a,eB(a)))],['roof'],tile=8,step=0.5)
sweep(AS,AN,lambda a:[(eF(a),RZa(a,eF(a))-0.7),(eB(a),RZa(a,eB(a))-0.7)],['under'],tile=8,step=0.5)
sweep(AS,AN,lambda a:[(eF(a),RZa(a,eF(a))-1.0),(eF(a),RZa(a,eF(a)))],['roofd'],tile=8,step=0.5)
for a in(AS,AN):face([P(a,eF(a),RZa(a,eF(a))-1.0),P(a,eB(a),RZa(a,eB(a))-0.7),P(a,eB(a),RZa(a,eB(a))),P(a,eF(a),RZa(a,eF(a)))],'roofd',[(0,0),(1,0),(1,1),(0,1)])
def tube2(p0,p1,r0,r1,m,n=8):
    ax=(p1-p0).normalized();t=ax.orthogonal().normalized();s=ax.cross(t)
    for i in range(n):
        u0=2*math.pi*i/n;u1=2*math.pi*(i+1)/n
        c0=t*math.cos(u0)+s*math.sin(u0);c1=t*math.cos(u1)+s*math.sin(u1)
        q=[(0,0),(1,0),(1,1),(0,1)]
        if m=='navy':   # a column is one painted member: keep it inside one 2 m panel of the 8 m steel tile (no panel tones)
            a0,a1=0.01+0.23*i/n,0.01+0.23*(i+1)/n;q=[(a0,0.01),(a1,0.01),(a1,0.24),(a0,0.24)]
        face([p0+c0*r0,p0+c1*r0,p1+c1*r1,p1+c0*r1],m,q)
# Masts (p1 zooms g1/g2): each is a thick white blade, wide at the foot and thin at the top, bowed outward, from the
# back foot up to the apex, and a thin straight tie from the front foot to the apex. One shape for all nine, fitted to
# the apex and both feet of the seven visible masts at once (0.9 px rms): plane at world angle -24.6+0.43a deg,
# back foot (d 28.5, z 16.6), front foot (d 19.9, z 18.3), apex (d 24, z 25.3); short posts take the feet to the roof.
# goal and behind posts (marks.json, 6.4 m apart on the goal line); heights read off p1: goal 15 m, behind 10 m; red pads 3.6 m
POSTS=False   # director 2026-11-18: "Posts out" - the game draws its own goal and behind posts
for gp in (MK['posts'] if POSTS else []):
    x_,y_=gp['xy'];h_=15.0 if gp['goal'] else 10.0;r_=0.22 if gp['goal'] else 0.18
    tube2(Vector((x_,y_,3.6)),Vector((x_,y_,h_)),r_,r_*0.8,'line',8);tube2(Vector((x_,y_,0)),Vector((x_,y_,3.6)),r_+0.12,r_+0.12,'pad',8)
for a in[213.4+4.97*k for k in range(14) if 209.5<213.4+4.97*k<278.5]:   # navy ground-floor columns (p1: 213.4, 219.1, 224.4, 228.3)
    tube2(P(a,DBf(a),0),P(a,DBf(a),5.3),0.28,0.28,'navy',6)
for a in[214.0,219.7,225.7,232.1,239.0]+[n[0] for n in BKN[2:] if n and 245<n[0]<274]:   # white deck columns up to the roof (p1, on its back ridges)
    tube2(P(a,DBf(a)-0.6,11.4),P(a,DBf(a)-0.6,21.6),0.3,0.3,'fascia',8)
_ap=P(217.0,DBf(217.0)-0.6,21.0)
for a in(215.7,218.2):tube2(P(a,DBf(a)-0.6,11.4),_ap,0.2,0.2,'fascia',6)   # p1: inverted V brace at the stand's west end
MJ=json.load(open(SP+'/mastsJ.json'))
def mast(a):
    b=math.radians(MJ['b0']+a*MJ['K']);o=Vector((math.cos(b),math.sin(b),0))
    A=P(a,24,MJ['za']);B=P(a,24,MJ['zb'])+o*(MJ['db']-24);F=P(a,24,MJ['zf'])+o*(MJ['df']-24)
    # satellite: each blade's back end sits on the roof's back edge; move the mast radially so it does, and re-solve
    # every point's height on p1 (the photo fixes rows, the satellite fixes the plan)
    t=math.radians(a);rad=Vector((math.cos(t),math.sin(t),0));dB=(B.xy-Vector((PCx,PCy))).length-rp(a);sh=rad*(eB(a)+0.3-dB)
    def mv(X):Y=X+sh;Y.z=zkeep(X,Y);return Y
    A,B,F=mv(A),mv(B),mv(F)
    bow=o*(1.0 if MJ['db']>24 else -1.0)*1.1;C=(A+B)/2+bow;n=10;pts=[]
    for i in range(n+1):
        t=i/n;pts.append((1-t)**2*B+2*t*(1-t)*C+t*t*A)
    for i in range(n):tube2(pts[i],pts[i+1],0.75-0.45*i/n,0.75-0.45*(i+1)/n,'fascia')
    tube2(F,A,0.18,0.18,'fascia',6)
    def rzat(p):aa=math.degrees(math.atan2(p.y-PCy,p.x-PCx));return RZa(aa,(p.xy-Vector((PCx,PCy))).length-rp(aa))
    for p in(B,F):tube2(Vector((p.x,p.y,rzat(p)-0.2)),p,0.45 if p is B else 0.25,0.45 if p is B else 0.25,'fascia',6)
MA=MJ['a'];MA=MA[:5]+[MA[4]+(MA[5]-MA[4])/3,MA[4]+2*(MA[5]-MA[4])/3]+MA[5:]
for a in MA:mast(a)
# GMHBA STADIUM sign standing on the roof front (p1 u 666-718, v 282-292): blank cyan and grey panel, no lettering
SA=angles(-18.6,-3.0,0.5)
for a0,a1 in zip(SA,SA[1:]):
    u0=(-3.0-a0)/15.6;u1=(-3.0-a1)/15.6
    q=[]   # sign kept 0.8 m behind the satellite roof front, its p1 rows kept
    for a_ in(a0,a1):
        d_=eF(a_)+0.8;q.append((P(a_,d_,zkeep(P(a_,9.0,RZ(9.0)-0.2),P(a_,d_,0))),P(a_,d_,zkeep(P(a_,9.0,RZ(9.0)+3.1),P(a_,d_,0)))))
    face([q[0][0],q[1][0],q[1][1],q[0][1]],'sign',[(u0,0),(u1,0),(u1,1),(u0,1)])
# ---- towers (photo p1, all four towers measured row by row, towerfit2.py -> towerJ.json, 1.7 px rms):
# straight shaft leaning out 3.1 m to a knee at 55 m, then the V head leans back toward the pitch (-0.5 m at 75 m).
# Shaft section (across x along): 3.1x1.6 to 19 m, waist 1.9x1.7 at 36-39 m, flaring to 5.0 m wide at 52 m.
# Head: two 1.5 m legs whose outer edge runs from half-width 2.9 m (52 m) to 6.3 m (74.7 m); between them, top
# down: top rail, white panel, then blue lamp band / white panel x3 with thin open slits, solid white below 57.2 m.
TJ=json.load(open(SP+'/towerJ.json'));TT=TJ['T']
# satellite (Esri z19, 2026-11-19): heads 1 (SE) and 2 (NE) sat 2-4 m off the satellite heads; heads 3, 4 match within 2 m
_TO=[(-2.0,2.2),(-3.1,-2.2),(0,0),(0,0)];TT=[(x+dx,y+dy) for (x,y),(dx,dy) in zip(TT,_TO)]
def box(c,ax,ay,az,m):
    # box centred on c with half-axis vectors ax, ay, az
    V=[c+ax*i+ay*j+az*k for i in(-1,1) for j in(-1,1) for k in(-1,1)]
    for q in((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)):
        face([V[t] for t in q],m,[(0,0),(1,0),(1,1),(0,1)])
def tower(x,y):
    a=math.atan2(y-PCy,x-PCx);out=Vector((math.cos(a),math.sin(a),0));sd=Vector((-out.y,out.x,0));Z=Vector((0,0,1))
    base=Vector((x,y,0))
    def cl(z):return base+out*(float(np.interp(z,[0,TJ['zk'],75.1],[0,TJ['ok'],TJ['ot']]))-2.0*max(0.0,z-52.0)/22.7)+Z*z   # head edges (headfit.py): head tips a further 2 m toward the pitch
    def loft(secs,m,cap=True,off=0.0):
        for (z0,w0,d0),(z1,w1,d1) in zip(secs,secs[1:]):
            for k in range(4):
                c=[(1,1),(-1,1),(-1,-1),(1,-1)];i,j=c[k],c[(k+1)%4]
                q=lambda z,w,d,e:cl(z)+sd*(off+e[0]*w/2)+out*(e[1]*d/2)
                face([q(z0,w0,d0,i),q(z0,w0,d0,j),q(z1,w1,d1,j),q(z1,w1,d1,i)],m,[(0,0),(1,0),(1,1),(0,1)])
        if cap:
            for z,w,d in(secs[0],secs[-1]):
                face([cl(z)+sd*(off+e[0]*w/2)+out*(e[1]*d/2) for e in((1,1),(-1,1),(-1,-1),(1,-1))],m,[(0,0),(1,0),(1,1),(0,1)])
    loft([(0,3.1,1.6),(19,3.07,1.57),(24,2.6,1.6),(36,1.9,1.67),(39,1.9,1.67),(45,2.57,1.6),(52.5,5.2,1.1)],'tower')
    def hw(z):return 2.9+(z-52.0)*(6.3-2.9)/(74.7-52.0)
    LW=1.5
    for s_ in(-1,1):   # legs: section stepped every metre so the leg follows the leaning centreline
        Zs=[52.0+i*(74.7-52.0)/12 for i in range(13)]
        V=[(cl(z)+sd*s_*(hw(z)-LW/2)) for z in Zs]
        for k in range(12):
            for e0,e1 in(((1,1),(-1,1)),((-1,1),(-1,-1)),((-1,-1),(1,-1)),((1,-1),(1,1))):
                pa=lambda P,e:P+sd*(e[0]*LW/2)+out*(e[1]*0.55)
                face([pa(V[k],e0),pa(V[k],e1),pa(V[k+1],e1),pa(V[k+1],e0)],'tower',[(0,0),(1,0),(1,1),(0,1)])
        face([V[-1]+sd*(e[0]*LW/2)+out*(e[1]*0.55) for e in((1,1),(-1,1),(-1,-1),(1,-1))],'tower',[(0,0),(1,0),(1,1),(0,1)])
    def plate(z0,z1,m,dep=0.8):
        zc=(z0+z1)/2;w=hw(zc)-LW*0.9
        box(cl(zc),sd*w,Z*(z1-z0)/2,out*dep/2,m)
    plate(52.5,57.2,'tower');plate(57.2,59.4,'lamp');plate(59.8,61.8,'tower');plate(62.5,64.6,'lamp')
    plate(65.1,67.1,'tower');plate(67.7,70.0,'lamp');plate(70.3,72.5,'tower')
    zc=74.45;box(cl(zc),sd*hw(zc),Z*0.25,out*0.55,'tower')            # top rail
    for f_ in(-0.55,-0.2,0.2,0.55):                                     # rail posts
        zc=73.35;box(cl(zc)+sd*(f_*hw(zc)),sd*0.12,Z*0.85,out*0.12,'tower')
    zc=73.4;box(cl(zc),sd*hw(zc),Z*0.08,out*0.08,'tower')              # mid rail
for x,y in TT:tower(x,y)
# ---- scoreboard (fitted to the photo's four frame corners): SE corner pocket, a=-67.5, d=25, frame 15.3 x 9.4 m
# from 4.4 m, facing 131 deg (toward the ground), on two legs, dark box behind
# refit 2026-11-18 to the four red frame corners on p1 (scrfit.py, 1.2 px): 18.1 x 9.6 m from 4.1 m, facing 124.3 deg, top leans back 8 deg
SA,SD,SZ,STH,STL,SW,SH=json.load(open(SP+'/scr.json'))
sc=P(SA,SD,0);th=math.radians(STH);nrm=Vector((math.cos(th),math.sin(th),0));sd=Vector((-nrm.y,nrm.x,0));Z=Vector((0,0,1))
UP=Z*math.cos(math.radians(STL))-nrm*math.sin(math.radians(STL))
for s_ in(-1,1):tube(sc+sd*s_*5.5,sc+sd*s_*5.5+Z*SZ,0.45,'wall')
c0=sc+Z*SZ;sw=SW/2
face([c0+sd*sw,c0-sd*sw,c0-sd*sw+UP*SH,c0+sd*sw+UP*SH],'screen',[(0,0),(1,0),(1,1),(0,1)])
box(c0+UP*(SH/2)-nrm*0.9,sd*(sw-0.05),UP*(SH/2-0.05),nrm*0.85,'roofd')
# ---- matched camera renders (p1 and p2)
def render(cf,W,H,out,geo=False):
    cam=json.load(open(SP+'/'+cf))['p']
    cy_,sy_=math.cos(cam[3]),math.sin(cam[3]);cp,sp=math.cos(cam[4]),math.sin(cam[4]);cr,sr=math.cos(cam[5]),math.sin(cam[5])
    f=Vector((cy_*cp,sy_*cp,sp));r=Vector((sy_,-cy_,0));u=r.cross(f);R0=r*cr+u*sr;R1=-r*sr+u*cr
    cd=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cd);bpy.context.scene.collection.objects.link(co)
    co.matrix_world=Matrix(((R0.x,R1.x,-f.x,cam[0]),(R0.y,R1.y,-f.y,cam[1]),(R0.z,R1.z,-f.z,cam[2]),(0,0,0,1)))
    cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=cam[6]/W*36;cd.shift_x=(W/2-cam[7])/W;cd.shift_y=(cam[8]-H/2)/W
    cd.clip_end=5000;sc_=bpy.context.scene;sc_.camera=co
    if geo:
        sc_.render.engine='BLENDER_WORKBENCH';sc_.display.shading.color_type='MATERIAL';sc_.display.shading.light='FLAT'
    else:   # sun-lit check render: sun from behind the camera's left, as the photo's lit west facades show
        sc_.render.engine='BLENDER_EEVEE'
        if 'sun' not in bpy.data.objects:
            ld=bpy.data.lights.new('sun','SUN');ld.energy=4.4;ld.angle=0.02;lo=bpy.data.objects.new('sun',ld);sc_.collection.objects.link(lo)
            lo.rotation_euler=(Vector((-0.574,0.819,0.700)).normalized()).to_track_quat('Z','Y').to_euler()
            w=bpy.data.worlds.new('w');sc_.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.62,0.66,0.72,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.35
        sc_.view_settings.view_transform='Standard'
        try:sc_.eevee.use_raytracing=True;sc_.eevee.use_shadows=True;sc_.eevee.fast_gi_method='GLOBAL_ILLUMINATION'   # roofs shade the seats under them, as in p1
        except Exception as e:print('eevee opt',e)
    sc_.render.resolution_x=W;sc_.render.resolution_y=H;sc_.render.film_transparent=True;sc_.render.filepath=out
    bpy.ops.render.render(write_still=True)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-4);bm.normal_update()
# geometry-only render first: the edge check uses this one, because a projected render matches the photo trivially
bm.to_mesh(me);render('cam.json',1200,675,REN.replace('.png','_geo.png'),True)
# photo projection removed: director 2026-11-18, no photo pixels on any model (hand-made textures only)
bm.to_mesh(me);bm.free()
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',use_selection=False)
render('cam.json',1200,675,REN)
render('cam2.json',1000,596,REN.replace('.png','_2.png'))
