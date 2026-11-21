# North stand (street side faces the 1992 camera). exec'd by build.py after the parts.
# Frame: O on the street face, a along it (west->east), n into the ground (toward the field).
# Every number below was back-projected from p92.png onto the measured planes (see bands.py / cam.py).
NO=(-52.5,117.2);NA=(0.997,0.079);NN=(0.079,-0.997)
def NP(s,d,z):return (NO[0]+NA[0]*s+NN[0]*d,NO[1]+NA[1]*s+NN[1]*d,z)
def nq(m,pts):quad(m,[NP(*p) for p in pts])
def fence_d(s):
    d=20.0
    while d<90:
        x,y,_=NP(s,d,0)
        if math.hypot(x-EC[0],y-EC[1])<=frad(tof(x,y))+0.5:return d
        d+=0.25
    return d
S_E=59.0;ROOF=24.2;BACK=30.0
EU=(0.465,0.884)          # west end line direction in (s,d): from O to (16.1,30.6)
def end_sd(e):return (EU[0]*e,EU[1]*e)
# ---- street facade: bays of horizontal bands [z0,z1,material,setback]
MAIN=[[0,1.8,'glass',2.5],[1.8,3.1,'white',2.5],[3.1,8.1,'white',1.5],[8.1,10.1,'glass',1.5],[10.1,11.5,'white',0],
      [11.5,13.1,'glass',1.0],[13.1,16.3,'white',0],[16.3,17.9,'glass',1.0],[17.9,20.2,'white',1.5],[20.2,21.5,'white',0],
      [21.5,23.0,'glass',1.0],[23.0,ROOF,'white',0]]
UPPER=[b for b in MAIN if b[0]>=16.3]
def stair(rails):
    out=[[0,17.4,'glass',1.2]]+[[z,z+0.4,'yellow',0.1] for z in rails]+[[17.4,17.9,'white',0]]
    return out+UPPER
WING=[[0,16.7,'white',-0.5],[16.7,18.3,'glass',1.0],[18.3,20.5,'white',1.5],[20.5,21.9,'white',0],[21.9,23.0,'glass',1.0],[23.0,ROOF,'white',0]]
WIN=[[0,2.9,'white',0],[2.9,3.5,'yellow',0],[3.5,4.8,'white',0],[4.8,6.7,'glass',0.6],[6.7,8.3,'white',0],[8.3,10.4,'glass',0.6],
     [10.4,12.5,'white',0],[12.5,14.9,'glass',0.6],[14.9,16.7,'white',0],[16.7,18.3,'glass',0.6],[18.3,20.7,'white',1.5],
     [20.7,22.0,'white',0],[22.0,23.0,'glass',1.0],[23.0,ROOF,'white',0]]
BAYS=[(0.0,12.3,WIN),(12.3,15.2,stair([3.0,6.6,10.2,13.8])),(15.2,22.6,WING),(22.6,27.0,stair([1.4,5.1,8.7,12.2,15.8])),
      (27.0,34.5,UPPER),(34.5,46.8,MAIN),(51.7,S_E,MAIN)]
for s0,s1,bands in BAYS:
    for z0,z1,m,sb in bands:
        nq(m,[(s0,sb,z0),(s1,sb,z0),(s1,sb,z1),(s0,sb,z1)])
        if sb:
            nq('white',[(s0,0,z0),(s0,sb,z0),(s0,sb,z1),(s0,0,z1)]);nq('white',[(s1,0,z0),(s1,sb,z0),(s1,sb,z1),(s1,0,z1)])
            nq('white',[(s0,0,z1),(s1,0,z1),(s1,sb,z1),(s0,sb,z1)]);nq('white',[(s0,0,z0),(s1,0,z0),(s1,sb,z0),(s0,sb,z0)])
# lower facade behind the protruding towers (T2 sits in front of it up to 20.4 m)
for z0,z1,m,sb in MAIN:
    if z1<=16.3:nq(m,[(27.0,sb,z0),(34.5,sb,z0),(34.5,sb,z1),(27.0,sb,z1)])
# bay A: white panel above the yellow awning (s 36.1-45.2)
nq('white',[(36.1,0,3.1),(45.2,0,3.1),(45.2,0,6.6),(36.1,0,6.6)])
nq('yellow',[(36.1,0,3.1),(45.2,0,3.1),(45.2,-1.2,1.8),(36.1,-1.2,1.8)])
# stair towers: T1 (s 46.8-51.7, out 5.5 m, 29 m), T2 (s 27.0-34.5, out 1.5 m, 20.4 m)
def ntower(s0,s1,out,z1):
    c=[(s0,-out),(s1,-out),(s1,0.3),(s0,0.3)]
    for i in range(4):
        (a0,b0),(a1,b1)=c[i],c[(i+1)%4];nq('white',[(a0,b0,0),(a1,b1,0),(a1,b1,z1),(a0,b0,z1)])
    nq('white',[(a,b,z1) for a,b in c])
ntower(46.8,51.7,5.5,29.0);ntower(27.0,34.5,1.5,20.4)
# ---- body: roof slab, end walls, two tiers facing the field
w_back=end_sd(BACK/EU[1])[0]                     # s where the west end line reaches the back
RIDGE=(5.0,28.0)   # front slope rises from the eave to a ridge 5 m back (photo ridge v 504)
def rs(d):return end_sd(d/EU[1])[0]
dr,zr=RIDGE
# front slope: white sheet east of x -21 (u 970), blue sheet west of it, as in the photo
SB=-21.0+52.5
nq('roof',[(SB,0,ROOF),(S_E,0,ROOF),(S_E,dr,zr),(SB,dr,zr)])
nq('blue',[(0,0,ROOF),(SB,0,ROOF),(SB,dr,zr),(rs(dr),dr,zr)])
nq('roof',[(rs(dr),dr,zr),(S_E,dr,zr),(S_E,BACK,ROOF),(w_back,BACK,ROOF)])
nq('white',[(S_E,0,ROOF),(S_E,dr,zr),(S_E,BACK,ROOF)])
nq('white',[(0,0,ROOF),(rs(dr),dr,zr),(w_back,BACK,ROOF)])
# A-frame posts on the front slope with a strut up to the ridge (photo u 812/866/926/990)
for x in (-6.6,-16.6,-25.3,-32.7):
    s0=x+52.5;dz=ROOF+(zr-ROOF)*2.0/dr
    for a,b in ((-0.25,0.25),):
        nq('white',[(s0+a,2.0,dz),(s0+b,2.0,dz),(s0+b,2.0,dz+2.2),(s0+a,2.0,dz+2.2)])
        nq('white',[(s0+a,2.0,dz+2.2),(s0+b,2.0,dz+2.2),(s0+b,dr,zr+0.2),(s0+a,dr,zr+0.2)])
nq('loft',[(0,0,ROOF-1),(S_E,0,ROOF-1),(S_E,BACK,ROOF-1),(w_back,BACK,ROOF-1)])   # roof underside
# west end profile in (e along the end line, z): measured on the angled end plane
def ee(e,z):s,d=end_sd(e);return (s,d,z)
nq('white',[ee(0,0),ee(52,0),ee(52,0.8),ee(39.3,5.7),ee(24.6,10.3),ee(0,13.3)])
nq('glass',[ee(0,13.3),ee(24.6,10.3),ee(24.8,13.5),ee(0,15.5)])
nq('white',[ee(0,15.5),ee(24.8,13.5),ee(27.9,13.1),ee(27.9,14.1),ee(0,22.9)])
# upper tier deck (seat rows) from the back wall down to its front lip, and its front fascia
UT=[(1.0,22.9),(BACK*0.82,14.1)]
def tier_s(d):return end_sd(d/EU[1])[0]
(d0,z0),(d1,z1)=UT
nq('terrace',[(tier_s(d0),d0,z0),(S_E,d0,z0),(S_E,d1,z1),(tier_s(d1),d1,z1)])
nq('white',[(tier_s(d1),d1,z1),(S_E,d1,z1),(S_E,d1,z1-1.0),(tier_s(d1),d1,z1-1.0)])
nq('glass',[(tier_s(d0),d0,z0),(S_E,d0,z0),(S_E,d0,ROOF-1),(tier_s(d0),d0,ROOF-1)])  # rear wall of the upper tier in shadow
# lower tier: under the upper lip down to the fence, row by row along s
LT=[(24.6,10.3),(34.7,5.7)]
steps=24
for i in range(steps):
    sa=tier_s(24.6)+(S_E-tier_s(24.6))*i/steps;sb=tier_s(24.6)+(S_E-tier_s(24.6))*(i+1)/steps
    fa,fb=fence_d(sa),fence_d(sb)
    for (da,za),(db,zb) in ((LT[0],LT[1]),((34.7,5.7),(None,0.8))):
        dba=fa if db is None else db;dbb=fb if db is None else db
        sa0=max(sa,tier_s(da));sb0=max(sb,tier_s(da))
        if sb0<=sa0:continue
        nq('terrace',[(sa0,da,za),(sb0,da,za),(sb0,dbb,zb),(sa0,dba,zb)])
    nq('white',[(sa,fa,0),(sb,fb,0),(sb,fb,0.8),(sa,fa,0.8)])
# lower tier west edge beyond the end wall (e 39.3 -> fence)
# east end wall, full section
fE=fence_d(S_E)
nq('white',[(S_E,0,0),(S_E,fE,0),(S_E,fE,0.8),(S_E,34.7,5.7),(S_E,BACK,ROOF),(S_E,0,ROOF)])
# ---- annexe at the west end (photo u 1095-1335, v 700-872), set along the stand's angled end wall
# lower block: street level (-4.7) to 1.6 m; upper box on it to 7.3 m with three windows 3.9-5.3 m
LOW=[(-51.6,121.2),(-66.1,103.8),(-53.0,92.5),(-40.5,107.5)]
boxpts('white',LOW,-4.7,1.6,top='concrete')
UP=[(-50.3,113.0),(-57.0,101.2),(-44.5,88.2),(-35.9,96.0)]
boxpts('white',UP,1.6,7.3,top='concrete')
for p0,p1 in (((-50.56,112.54),(-51.79,110.38)),((-52.13,109.77),(-53.37,107.59)),((-53.72,106.98),(-54.96,104.8))):
    ox,oy=-0.052,0.029
    quad('glass',[(p0[0]+ox,p0[1]+oy,3.95),(p1[0]+ox,p1[1]+oy,3.95),(p1[0]+ox,p1[1]+oy,5.3),(p0[0]+ox,p0[1]+oy,5.3)])
box('white',-47.3,100.7,4.0,4.0,7.3,9.3,ang=math.radians(-60),top='concrete')
# ---- podium: forecourt at field level held by a 4.7 m brick wall; Hay St side below at -4.7
WL=[(30,141.5),(8,140.4),(-8.6,134.5),(-40,123.2),(-51.6,121.2),(-66.1,103.8),(-100,95)]
ZS=-4.7
for (x0,y0),(x1,y1) in zip(WL,WL[1:]):
    if (x0,y0)==(-51.6,121.2):continue          # the annexe's lower block is the wall here
    quad('brick',[(x0,y0,ZS),(x1,y1,ZS),(x1,y1,0),(x0,y0,0)])
quad('path',[NP(-0.5,0,0.02),NP(S_E+3,0,0.02),(8,140.4,0.02),(-8.6,134.5,0.02),(-40,123.2,0.02),(-51.6,121.2,0.02)])
quad('road',[(-260,95,ZS)]+[(x,y,ZS) for x,y in reversed(WL)]+[(260,135,ZS),(260,260,ZS),(-260,260,ZS)])
# land: same outline as before, with the oval cut out to the grass ring at the apron (field left out, director 2026-11-18)
LO=[(-260,-260),(260,-260),(260,135)]+[tuple(p) for p in WL]+[(-260,95)]
def _hit(t):
    dx,dy=math.cos(t),math.sin(t);best=None
    for i in range(len(LO)):
        (x1,y1),(x2,y2)=LO[i],LO[(i+1)%len(LO)];ex,ey=x2-x1,y2-y1;den=dx*ey-dy*ex
        if abs(den)<1e-12:continue
        u=((x1-EC[0])*ey-(y1-EC[1])*ex)/den;v=((x1-EC[0])*dy-(y1-EC[1])*dx)/den
        if u>0 and -1e-9<=v<=1+1e-9 and (best is None or u<best):best=u
    return (EC[0]+dx*best,EC[1]+dy*best)
_ts=sorted(set([round((2*math.pi*k/120)%(2*math.pi),9) for k in range(120)]+[round(math.atan2(y-EC[1],x-EC[0])%(2*math.pi),9) for x,y in LO]))
_ap=P.get('apron',3)
for i in range(len(_ts)):
    t1,t2=_ts[i],_ts[(i+1)%len(_ts)]
    a,b=ell(t1,_ap),ell(t2,_ap);c,d=_hit(t1),_hit(t2)
    quad('land',[(a[0],a[1],-0.05),(c[0],c[1],-0.05),(d[0],d[1],-0.05),(b[0],b[1],-0.05)])
# street-level drop beyond the podium ends (keeps the street cut closed in every view)
quad('brick',[(-260,95,ZS),(-100,95,ZS),(-100,95,0),(-260,95,0)]);quad('brick',[(30,141.5,ZS),(260,135,ZS),(260,135,0),(30,141.5,0)])
