# Norwood Oval exterior geometry in metres (x east, y north, z up). Pure python: parts[name] = list of (pts3d, mat).
import numpy as np
LEAN=0.207
def UL(pts,z): return [(x,y-LEAN*z) for x,y in pts]
V=lambda *a: np.array(a,float)
parts={}
def add(name,pts,mat,uv=None): parts.setdefault(name,[]).append(([tuple(map(float,p)) for p in pts],mat,uv))   # uv: per-vertex (u,v) in metres ('wall' textures) or 0..1 ('fit')
def prism(name,poly,z0,z1,wall,top=None):
    n=len(poly)
    for i in range(n):
        (x0,y0),(x1,y1)=poly[i],poly[(i+1)%n]
        add(name,[(x0,y0,z0),(x1,y1,z0),(x1,y1,z1),(x0,y0,z1)],wall)
    if top: add(name,[(x,y,z1) for x,y in poly],top)
def box(name,x0,x1,y0,y1,z0,z1,wall,top=None): prism(name,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z0,z1,wall,top)
def hip(name,poly4,ze,zr,mat,inset=None):
    a,b,c,d=[V(*p,ze) for p in poly4]
    L=np.linalg.norm(b-a);w=np.linalg.norm(d-a);ins=w/2 if inset is None else inset
    ax=(b-a)/L;m0=(a+d)/2;m1=(b+c)/2
    r0=m0+ax*ins;r1=m1-ax*ins;r0[2]=r1[2]=zr
    add(name,[a,b,r1,r0],mat);add(name,[c,d,r0,r1],mat);add(name,[d,a,r0],mat);add(name,[b,c,r1],mat)
def gable_roof(name,poly4,ze,zr,mat,end=None):
    a,b,c,d=[V(*p,ze) for p in poly4]
    r0=(a+d)/2;r1=(b+c)/2;r0[2]=r1[2]=zr
    add(name,[a,b,r1,r0],mat);add(name,[c,d,r0,r1],mat)
    if end: add(name,[d,a,r0],end);add(name,[b,c,r1],end)
def cyl(name,x,y,z0,z1,r0,r1,mat,n=12,cap=None):
    for i in range(n):
        t0=2*np.pi*i/n;t1=2*np.pi*(i+1)/n
        add(name,[(x+r0*np.cos(t0),y+r0*np.sin(t0),z0),(x+r0*np.cos(t1),y+r0*np.sin(t1),z0),(x+r1*np.cos(t1),y+r1*np.sin(t1),z1),(x+r1*np.cos(t0),y+r1*np.sin(t0),z1)],mat)
    if cap: add(name,[(x+r1*np.cos(2*np.pi*i/n),y+r1*np.sin(2*np.pi*i/n),z1) for i in range(n)],cap)

# ---------------- Sir Edwin Smith Stand (heritage grandstand, south) ----------------
ZE=9.5; ZR=14.3; ZG=12.6   # eave, ridge, gablet foot
F=[V(*p,ZE) for p in UL([(12.0,-94.7),(-11.2,-94.0),(-31.9,-85.3),(-49.3,-69.0)],ZE)]   # front eave E->W
B=[V(*p,ZE) for p in UL([(12.2,-111.6),(-14.0,-110.9),(-40.5,-100.1),(-59.5,-81.9)],ZE)]
R=[(f+b)/2 for f,b in zip(F,B)]
for r in R: r[2]=ZR
def along(p,q,d): return p+(q-p)/np.linalg.norm((q-p)[:2])*d
HIP=4.2
E0=along(R[0],R[1],HIP);E3=along(R[3],R[2],HIP)
def slope_pt(eave,ridge_pt,z):
    t=(z-ZE)/(ZR-ZE);return eave+(ridge_pt-eave)*t
def eave_at(e0,e1,ref):
    d=(e1-e0)[:2];t=np.dot((ref-e0)[:2],d)/np.dot(d,d);return e0+(e1-e0)*t
for (E,i,j) in ((E0,0,1),(E3,3,2)):
    fe=eave_at(F[i],F[j],E);be=eave_at(B[i],B[j],E)
    gf=slope_pt(fe,E,ZG);gb=slope_pt(be,E,ZG)
    add('ses_roof',[F[i],B[i],gb,gf],'ses_roof')
    add('ses_roof',[gf,gb,E],'ses_gablet')
    if i==0: add('ses_roof',[F[0],F[1],R[1],E0,gf],'ses_roof');add('ses_roof',[B[1],B[0],gb,E0,R[1]],'ses_roof')
    else:    add('ses_roof',[F[2],F[3],gf,E3,R[2]],'ses_roof');add('ses_roof',[B[3],B[2],R[2],E3,gb],'ses_roof')
add('ses_roof',[F[1],F[2],R[2],R[1]],'ses_roof');add('ses_roof',[B[2],B[1],R[1],R[2]],'ses_roof')
GW=6.0;GH=1.5   # pediment: 6 m base, 1.5 m tall (main photo 6 px apex-to-base; c32 H/W 0.23)
GC=[((0.92,-96.33),0,1),((-21.24,-91.75),1,2),((-39.64,-80.01),2,3)]   # three pediments (c32); the west end triangle is the hip gablet
for (gx,gy),i,j in GC:
    c=eave_at(F[i],F[j],V(gx,gy,ZE));ax=(F[j]-F[i]);ax=ax/np.linalg.norm(ax)
    l=c-ax*GW/2;r=c+ax*GW/2;ap=c.copy();ap[2]=ZE+GH
    mid=(R[i]+R[j])/2;foot=eave_at(F[i],F[j],mid);inn=mid-foot;inn[2]=0;run=np.linalg.norm(inn[:2]);inn/=run
    back=ap+inn*(GH/(ZR-ZE)*run)
    add('ses_gables',[l,r,ap],'ses_pediment')
    add('ses_gables',[l,ap,back],'ses_roof');add('ses_gables',[ap,r,back],'ses_roof')
def ridge_y(x):   # cupolas sit on the ridge (c32, woods1_ses): take y on the ridge line R at the cupola's x
    for i in range(3):
        a,b=R[i],R[i+1]
        if min(a[0],b[0])<=x<=max(a[0],b[0]): return float(a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
for (cx,cy) in [(-12.54,-104.42),(-36.2,-94.67)]:
    cy=ridge_y(cx)
    box('ses_cupola',cx-0.9,cx+0.9,cy-0.9,cy+0.9,ZR-1.2,ZR+1.6,'ses_cupola_wall')
    hip('ses_cupola',[(cx-1.1,cy-1.1),(cx+1.1,cy-1.1),(cx+1.1,cy+1.1),(cx-1.1,cy+1.1)],ZR+1.6,ZR+2.6,'ses_cupola_roof')
    cyl('ses_cupola',cx,cy,ZR+2.6,ZR+3.6,0.08,0.02,'ses_cupola_roof',n=6)
nS=[]
for k in range(4):
    a=F[max(k-1,0)];b=F[min(k+1,3)];t=b-a;n=np.array([t[1],-t[0],0.0]);n/=np.linalg.norm(n)
    if n[1]>0: n=-n
    nS.append(n)
def line(d,z): return [np.array([F[k][0],F[k][1],z])+nS[k]*d for k in range(4)]
DB=13.5
PROF=[(-9.5,0.0,'concrete'),(-2.6,0.0,'concrete'),(-2.6,2.2,'ses_brick'),(-2.2,2.2,'ses_cap'),(DB,7.0,'ses_seats'),(DB,ZE,'ses_backwall')]
prev=None
for d,z,m in PROF:
    cur=line(d,z)
    if prev is not None and m!='ses_seats':
        for k in range(3): add('ses_body',[prev[k+1],prev[k],cur[k],cur[k+1]],m)
    prev=cur
# cream eave fascia along the front, and the name board under the eave (c32)
for k in range(3):
    add('ses_trim',[F[k+1]-V(0,0,0.4),F[k]-V(0,0,0.4),F[k],F[k+1]],'ses_fascia')
# seating rake as real steps with benches (c32, 2021+): 14 rows, six colour sections split by five aisles
NR=14;D0,Z0,D1,Z1=-2.2,2.2,DB,7.0;TRD=(D1-D0)/NR;RIS=(Z1-Z0)/NR
SEGL=[float(np.linalg.norm((F[k+1]-F[k])[:2])) for k in range(3)];SL=sum(SEGL)
def SP(s,d,z):   # point at s metres from the east end along the stand, d metres back from the eave line, height z
    k=0
    while k<2 and s>SEGL[k]: s-=SEGL[k];k+=1
    a=line(d,z);return a[k]+(a[k+1]-a[k])*(s/SEGL[k])
AISLE=[12.4,23.5,36.2,47.0,59.5];AW=1.2;SEAT0,SEAT1=3.0,67.4
cuts=sorted(set([0,SEGL[0],SEGL[0]+SEGL[1],SL,SEAT0,SEAT1]+[a-AW/2 for a in AISLE]+[a+AW/2 for a in AISLE]))
def zone(s):
    if s<SEAT0 or s>SEAT1: return 'end',None
    for a in AISLE:
        if abs(s-a)<AW/2: return 'aisle',None
    return 'seat',sum(s>a for a in AISLE)
def tread_z(d): i=min(max(int((d-D0)/TRD),0),NR-1);return Z0+(i+1)*RIS
for r in range(NR):
    da,db=D0+r*TRD,D0+(r+1)*TRD;za,zb=Z0+r*RIS,Z0+(r+1)*RIS
    for i in range(len(cuts)-1):
        s0,s1=cuts[i],cuts[i+1];kind,sec=zone((s0+s1)/2)
        add('ses_rake',[SP(s1,da,za),SP(s0,da,za),SP(s0,da,zb),SP(s1,da,zb)],'ses_riser')
        add('ses_rake',[SP(s1,da,zb),SP(s0,da,zb),SP(s0,db,zb),SP(s1,db,zb)],'ses_aisle' if kind=='aisle' else 'ses_tread')
        if kind!='seat': continue
        band=r*4//NR
        m=f'bench_{sec}_{band}'
        if r<2 and sec in (2,3): m='box_red'
        if r<2 and sec==4: m='box_green'
        e0,e1=s0+0.05,s1-0.05
        b0,b1=da+0.30,da+0.72;h0,h1=zb+0.38,zb+0.45
        add('ses_bench',[SP(e1,b0,h1),SP(e0,b0,h1),SP(e0,b1,h1),SP(e1,b1,h1)],m)          # seat
        add('ses_bench',[SP(e1,b0,h0),SP(e0,b0,h0),SP(e0,b0,h1),SP(e1,b0,h1)],m)          # seat edge
        add('ses_bench',[SP(e1,b1+0.05,zb+0.55),SP(e0,b1+0.05,zb+0.55),SP(e0,b1+0.05,zb+0.85),SP(e1,b1+0.05,zb+0.85)],m)   # backrest
        for sl in np.arange(e0+0.9,e1-0.4,1.8):                                           # steel legs
            add('ses_bench',[SP(sl+0.04,b0+0.1,zb),SP(sl-0.04,b0+0.1,zb),SP(sl-0.04,b0+0.1,h0),SP(sl+0.04,b0+0.1,h0)],'steel')
BB=[np.array([b[0],b[1],0.0]) for b in B]
for k in range(3):
    add('ses_back',[BB[k],BB[k+1],B[k+1],B[k]],'ses_rear')
    add('ses_back',[line(DB,ZE)[k],line(DB,ZE)[k+1],B[k+1],B[k]],'ses_soffit')
for k in (0,3):
    add('ses_back',[line(-2.6,0)[k],line(-2.6,2.2)[k],line(DB,7.0)[k],line(DB,ZE)[k],B[k],BB[k]],'ses_endwall')
for k in range(3):
    n=3   # 3 bays per segment: posts read off the main photo (u 593..836) and c32
    for s in range(n+1):
        if k>0 and s==0: continue
        P=F[k]+(F[k+1]-F[k])*s/n+nS[k]*0.6
        zb=tread_z(0.6)
        cyl('ses_columns',P[0],P[1],zb,ZE,0.16,0.16,'ses_column',n=8)
# ---------------- Wolf Blass Community Centre (SW corner) ----------------
WB_Z=9.0
wb=UL([(-62,-44.4),(-55.4,-44.6),(-47.5,-68),(-49.5,-72.5),(-62,-72.5)],WB_Z)
for i in range(len(wb)):   # walls in two bands: ground storey (mural / brick) and the glass or rendered upper storey
    (x0,y0),(x1,y1)=wb[i],wb[(i+1)%len(wb)]
    lo,hi={1:('wbcc_mural','wbcc_upper'),0:('brick_red','render_cream'),3:('wbcc_south_lo','wbcc_south_up')}.get(i,('wbcc_west_lo','wbcc_mesh'))   # sides: Street View woods1 (south), woods2 (west)
    L_=float(np.hypot(x1-x0,y1-y0))
    if i in (2,3,4):   # sides from the street: recessed ground floor under a 0.9 m soffit, mesh-clad upper storey (woods2_ws)
        add('wbcc',[(x0,y0,0),(x1,y1,0),(x1,y1,3.3),(x0,y0,3.3)],lo,uv=[(L_,0),(0,0),(0,3.3),(L_,3.3)] if i!=3 else [(1,0),(0,0),(0,1),(1,1)])   # footprint runs clockwise: u falls along the edge so it reads left-to-right from the street
        add('wbcc',[(x0,y0,3.3),(x1,y1,3.3),(x1,y1,WB_Z),(x0,y0,WB_Z)],hi,uv=[(L_,0),(0,0),(0,WB_Z-3.3),(L_,WB_Z-3.3)] if i!=3 else [(1,0),(0,0),(0,1),(1,1)])
    else:
        add('wbcc',[(x0,y0,0),(x1,y1,0),(x1,y1,3.0),(x0,y0,3.0)],lo);add('wbcc',[(x0,y0,3.0),(x1,y1,3.0),(x1,y1,WB_Z),(x0,y0,WB_Z)],hi)
add('wbcc',[(x,y,WB_Z) for x,y in wb],'wbcc_roof')
prism('wbcc_box',UL([(-62,-44.4),(-55.4,-44.6),(-55.4,-53.2),(-62,-53.2)],11.0),WB_Z,11.0,'wbcc_box','wbcc_boxroof')
# ---------------- Western Stand (measured: gsat plan, front-edge height back-projected from main photo) ----------------
WS_FY=[-46,-40,-30,-20,-10,0,20,30,50.6];WS_FX=[-53.6,-54.0,-54.9,-55.6,-56.0,-57.1,-57.6,-57.9,-57.9]   # roof front edge
WS_LY=[-46,-40,-30,-10,0,26,50.6];WS_LX=[-59.6,-59.8,-60.3,-61.3,-62.1,-63.7,-65.0]                    # main-roof back (shadow line)
WS_KY=[-46,-40,0,10,26,50.6];WS_KX=[-61.6,-62.2,-65.1,-65.9,-66.7,-68.0]                                # rear edge
WS_ZY=[-46,-34,-10,16,40,50.6];WS_ZF=[8.2,8.2,8.4,8.6,9.3,9.6]                                          # fascia bottom
WSY=list(np.linspace(-46,50.6,25))
def wsx(y,X,Y): return float(np.interp(y,Y,X))
def wsec(y):
    xf=wsx(y,WS_FX,WS_FY);xl=wsx(y,WS_LX,WS_LY);xk=wsx(y,WS_KX,WS_KY);zf=wsx(y,WS_ZF,WS_ZY)
    return dict(xf=xf,xl=xl,xk=xk,zf=zf)
def wstrip(name,fa,fb,mat):
    for i in range(len(WSY)-1):
        y0,y1=WSY[i],WSY[i+1];A=fa(y0,wsec(y0));Bq=fb(y0,wsec(y0));C=fb(y1,wsec(y1));D=fa(y1,wsec(y1))
        add(name,[A,D,C,Bq],mat)
ZROOFB=lambda s:s['zf']+0.2
ZBACK=7.4
wstrip('ws_roof',lambda y,s:(s['xf'],y,s['zf']+0.6),lambda y,s:(s['xl'],y,ZROOFB(s)),'ws_roof')          # main roof top
wstrip('ws_roof',lambda y,s:(s['xf'],y,s['zf']),lambda y,s:(s['xf'],y,s['zf']+0.6),'ws_fascia')           # fascia
wstrip('ws_roof',lambda y,s:(s['xl'],y,s['zf']-0.2),lambda y,s:(s['xf'],y,s['zf']),'ws_under')            # underside
wstrip('ws_roof',lambda y,s:(s['xl'],y,ZBACK),lambda y,s:(s['xl'],y,ZROOFB(s)),'ws_step')                 # step above rear roof
wstrip('ws_rear',lambda y,s:(s['xl'],y,ZBACK),lambda y,s:(s['xk'],y,ZBACK-0.4),'ws_rearroof')
wstrip('ws_rear',lambda y,s:(s['xk'],y,ZBACK-0.4),lambda y,s:(s['xk'],y,0),'ws_rear')
PF=0.3
wstrip('ws_body',lambda y,s:(s['xf']+PF,y,0),lambda y,s:(s['xf']+PF,y,2.3),'ws_brick')
wstrip('ws_body',lambda y,s:(s['xf']+PF,y,2.3),lambda y,s:(s['xf']-1.2,y,2.4),'ws_cap')
wstrip('ws_body',lambda y,s:(s['xf']-1.2,y,2.4),lambda y,s:(s['xl']+0.3,y,6.2),'ws_seats')
wstrip('ws_body',lambda y,s:(s['xl']+0.3,y,6.2),lambda y,s:(s['xl']+0.3,y,s['zf']-0.2),'ws_backwall')
for y in (WSY[0],WSY[-1]):
    s=wsec(y);add('ws_body',[(s['xf']+PF,y,0),(s['xf']+PF,y,2.3),(s['xf']-1.2,y,2.4),(s['xl']+0.3,y,6.2),(s['xl']+0.3,y,s['zf']-0.2),(s['xl'],y,ZBACK),(s['xk'],y,ZBACK-0.4),(s['xk'],y,0)],'ws_end')
for i in range(13):
    y=WSY[0]+(WSY[-1]-WSY[0])*i/12;s=wsec(y);x=s['xf']-1.0
    cyl('ws_posts',x,y,2.4+0.2,s['zf']-0.1,0.12,0.12,'ws_post',n=6)
# ---------------- Light towers ----------------
HT=30.9
for nm,(x,y) in {'NE':(54.2,58.7),'NW':(-58.8,56.8),'SE':(58.0,-55.2),'SW':(-48.2,-70.2)}.items():
    cyl('tower_'+nm,x,y,0,HT-1.0,0.45,0.28,'tower_pole',n=12)
    d=V(-x,-y,0);d/=np.linalg.norm(d);s=V(-d[1],d[0],0)
    c=V(x,y,HT)+d*0.6;up=V(0,0,1)*0.8+(-d)*0.6;up/=np.linalg.norm(up)
    hw,hh=2.2,1.7
    add('tower_'+nm,[c-s*hw-up*hh,c+s*hw-up*hh,c+s*hw+up*hh,c-s*hw+up*hh],'lamp_face')
    b=-d*0.5
    add('tower_'+nm,[c+b-s*hw-up*hh,c+b-s*hw+up*hh,c+b+s*hw+up*hh,c+b+s*hw-up*hh],'lamp_back')
# ---------------- Boundary fence (line back-projected from the main photo's grass edge, smoothed) ----------------
import json as _json,os as _os
_FC=np.array(_json.load(open(_os.path.join(_os.path.dirname(__file__),'bound_fourier.json'))))
def rfence(t):
    t=np.atleast_1d(t);K=(len(_FC)-1)//2
    Mm=np.stack([np.ones_like(t)]+[f(k*t) for k in range(1,K+1) for f in (np.cos,np.sin)],1);return Mm@_FC
NT=180
TH=np.radians(np.arange(NT)*360/NT)
RF=rfence(TH)+0.2
FENCE=[(r*np.sin(t),r*np.cos(t)) for t,r in zip(TH,RF)]
for i in range(NT):
    (x0,y0),(x1,y1)=FENCE[i],FENCE[(i+1)%NT]
    add('fence',[(x0,y0,0),(x1,y1,0),(x1,y1,1.0),(x0,y0,1.0)],'fence_picket' if 193<=i*360/NT<230 else 'fence_hoarding')   # c32: white picket in front of the WBCC and west SES
# ---------------- Spectator terraces (concrete steps between fence and the outer walk; widths read off gsat) ----------------
WT=[(0,10),(25,9),(40,7),(55,6),(75,4.5),(100,4.5),(115,5),(130,12),(145,15),(160,9),(168,0),(315,0),(318,4),(330,7),(345,10),(360,10)]
def wterr(d): return float(np.interp(d%360,[a for a,_ in WT],[b for _,b in WT]))
TREAD=0.9;RISE=0.28
P=lambda r,t,z:(r*np.sin(t),r*np.cos(t),z)
def rail(name,a,b,mat,w=0.06):   # square steel tube from a to b
    a=V(*a);b=V(*b);d=b-a;d/=np.linalg.norm(d);sv=np.cross(d,[0,0,1.0])
    if np.linalg.norm(sv)<1e-6: sv=np.array([1.0,0,0])
    sv/=np.linalg.norm(sv);uv_=np.cross(sv,d);h=w/2;c=[(-1,-1),(1,-1),(1,1),(-1,1)]
    for k in range(4):
        e0=sv*c[k][0]*h+uv_*c[k][1]*h;e1=sv*c[(k+1)%4][0]*h+uv_*c[(k+1)%4][1]*h
        add(name,[a+e0,b+e0,b+e1,a+e1],mat)
# Open terrace ring (director 2026-11-18: "Add the detail"; concrete stays grey, no people: the game's crowd fills it).
# Grey concrete steps, hand-made joints (u = 80 m x angle so the joints line up radially from step to step),
# white crush barriers every 4th step, stair aisles every 20 degrees: half-steps, yellow nosings, a centre handrail.
UREF=80.0;AISLE=10;AW=1.2          # aisle every 10th 2-degree bay (about 26 m apart), 1.2 m wide
def pblock(name,ra,rb,ta,tb,z0,z1,top,side):   # a small block in polar coordinates: top, front, back and both ends
    A,B,C,D=P(ra,ta,0),P(ra,tb,0),P(rb,tb,0),P(rb,ta,0)
    up=lambda p,z:(p[0],p[1],z)
    add(name,[up(A,z1),up(B,z1),up(C,z1),up(D,z1)],top)
    for p,q in ((A,B),(B,C),(C,D),(D,A)): add(name,[up(p,z0),up(q,z0),up(q,z1),up(p,z1)],side)
for i in range(NT):
    t0=TH[i];t1=t0+np.radians(360/NT);d0=np.degrees(t0)
    w0,w1=wterr(d0),wterr(d0+360/NT)
    n=int(max(w0,w1)/TREAD)
    if n==0: continue
    r0,r1=RF[i]+0.3,RF[(i+1)%NT]+0.3;aisle=(i%AISLE==0) and min(w0,w1)>=TREAD*2
    u0,u1=UREF*t0,UREF*t1
    for s_ in range(n):
        a0=r0+min(s_*TREAD,w0);b0=r0+min((s_+1)*TREAD,w0);a1=r1+min(s_*TREAD,w1);b1=r1+min((s_+1)*TREAD,w1)
        z=0.3+RISE*s_
        if b0>a0 or b1>a1:
            add('terrace',[P(a0,t0,z),P(a1,t1,z),P(b1,t1,z),P(b0,t0,z)],'terrace_tread',uv=[(u0,0),(u1,0),(u1,b1-a1),(u0,b0-a0)])
            zl=z-RISE if s_ else 0
            add('terrace',[P(a0,t0,zl),P(a1,t1,zl),P(a1,t1,z),P(a0,t0,z)],'terrace_riser',uv=[(u0,0),(u1,0),(u1,z-zl),(u0,z-zl)])
            if aisle and b0-a0>0.5 and s_<n-1:   # aisle: a half-step on the tread, yellow nosings on the step and the half-step
                rm=(a0+a1)/2;tc=(t0+t1)/2;da=(AW/2)/rm
                pblock('terrace_aisle',a0+0.45,b0,tc-da,tc+da,z,z+RISE/2,'terrace_tread','terrace_riser')
                for (ra_,zz) in ((a0,z),(a0+0.45,z+RISE/2)):
                    add('terrace_aisle',[P(ra_+0.002,tc-da,zz+0.004),P(ra_+0.002,tc+da,zz+0.004),P(ra_+0.06,tc+da,zz+0.004),P(ra_+0.06,tc-da,zz+0.004)],'paint_yellow')
        if s_%4==3 and i%3!=2 and not aisle and b0>a0 and b1>a1:   # crush barrier 1.0 m up at the front of the step; posts at the bay ends; open at aisles
            A_=P(a0+0.15,t0,z+1.0);B_=P(a1+0.15,t1,z+1.0)
            rail('terrace_rails',A_,B_,'barrier');rail('terrace_rails',P(a0+0.15,t0,z),A_,'barrier',0.05)
            if i%3==1: rail('terrace_rails',P(a1+0.15,t1,z),B_,'barrier',0.05)
    zt=0.3+RISE*(n-1)
    if aisle:   # centre handrail up the aisle, 0.9 m above the nosings, posts every 3rd step
        tc=(t0+t1)/2;rr=lambda s_:r0+s_*TREAD+0.45
        rail('terrace_rails',P(rr(0),tc,0.3+0.9),P(rr(n-2),tc,0.3+RISE*(n-2)+0.9),'barrier',0.05)
        for s_ in range(0,n-1,3): rail('terrace_rails',P(rr(s_),tc,0.3+RISE*s_+RISE/2),P(rr(s_),tc,0.3+RISE*s_+0.9),'barrier',0.04)
    add('terrace',[P(r0+w0,t0,zt),P(r1+w1,t1,zt),P(r1+w1,t1,0),P(r0+w0,t0,0)],'terrace_back')
    rail('terrace_rails',P(r0+w0-0.1,t0,zt+1.0),P(r1+w1-0.1,t1,zt+1.0),'barrier')                        # rail along the back of the bank
    rail('terrace_rails',P(r0+w0-0.1,t0,zt),P(r0+w0-0.1,t0,zt+1.0),'barrier',0.05)
# ---------------- The playing field (render only: the game builds its own ground; not in the exterior GLB) ----------------
FX=[q[0] for q in FENCE];FY=[q[1] for q in FENCE];FIELD_BB=(min(FX)-1,max(FX)+1,min(FY)-1,max(FY)+1)
add('field',[(x,y,0.01) for x,y in FENCE],'turf',uv=[((x-FIELD_BB[0])/(FIELD_BB[1]-FIELD_BB[0]),(y-FIELD_BB[2])/(FIELD_BB[3]-FIELD_BB[2])) for x,y in FENCE])
AX=np.array([-np.sin(np.radians(4)),np.cos(np.radians(4))])   # long axis, 4 degrees west of north (main photo)
PX=np.array([AX[1],-AX[0]])                                  # across the ground, pointing east
CEN=np.array([-0.4,2.6]);GN=np.array([-2.65,85.45]);GS=np.array([1.8,-80.3])   # centre and goal-line centres (back-projected posts)
for G in (GN,GS):   # goal posts 14.5 m, behind posts 8 m, 6.4 m apart; blue padding at the foot
    for off,h,pad,r in ((-3.2,14.5,3.0,0.25),(3.2,14.5,3.0,0.25),(-9.6,8.0,2.5,0.2),(9.6,8.0,2.5,0.2)):
        x,y=G+PX*off
        cyl('goals',x,y,0,pad,r+0.07,r+0.07,'goal_pad',n=12,cap='goal_pad');cyl('goals',x,y,pad,h,r,r,'goal_post',n=12,cap='goal_post')
# ---------------- North-west buildings (gsat roofs + OSM footprint 915665057; heights back-projected from main photo) ----------------
# hall: hipped roof
hip('nw_hall',UL([(-70.0,78.3),(-51.6,78.3),(-51.6,91.7),(-70.0,91.7)],5.5),5.5,8.6,'nw_hall_roof',inset=3.5)
prism('nw_hall',UL([(-69.7,78.6),(-51.9,78.6),(-51.9,91.4),(-69.7,91.4)],5.5),0,5.5,'nw_hall_wall')
# bluestone clubrooms: two gabled wings in an L (satellite: ridges meet at J, hip at the outer corner A, valley inside)
# (s,t) frame: s along n1 (to the SW), t along u1 (to the NW); eave 4.2, ridge 6.4, both wings 7.5 m wide
_A=np.array([-35.0,90.8]);_u1=np.array([-0.5827,0.8127]);_n1=np.array([-0.8127,-0.5827])
def _L(s,t,z): q=_A+s*_n1+t*_u1; return (q[0],q[1],z)
_T1,_S2,_W,_ZE,_ZR=14.76,15.4,7.5,4.2,6.4;_h=_W/2
_Lpoly=[(0,0),(_S2,0),(_S2,_W),(_W,_W),(_W,_T1),(0,_T1)]
for _k in range(6):
    (sa,ta),(sb,tb)=_Lpoly[_k],_Lpoly[(_k+1)%6]
    if _k==5: add('nw_wing',[_L(sa,ta,0),_L(sb,tb,0),_L(sb,tb,_ZE),_L(sa,ta,_ZE)],'nw_wing_front',uv=[(1,0),(0,0),(0,1),(1,1)])   # main photo: bluestone then brick, plaque, window
    else: add('nw_wing',[_L(sa,ta,0),_L(sb,tb,0),_L(sb,tb,_ZE),_L(sa,ta,_ZE)],'nw_wing_wall')
_E,_R=_ZE,_ZR
add('nw_wing',[_L(0,0,_E),_L(0,_T1,_E),_L(_h,_T1,_R),_L(_h,_h,_R)],'nw_wing_roof')          # W1 NE slope (hip edge A-J)
add('nw_wing',[_L(_W,_T1,_E),_L(_W,_W,_E),_L(_h,_h,_R),_L(_h,_T1,_R)],'nw_wing_roof')       # W1 SW slope (valley)
add('nw_wing',[_L(_S2,0,_E),_L(0,0,_E),_L(_h,_h,_R),_L(_S2,_h,_R)],'nw_wing_roof')          # W2 SE slope
add('nw_wing',[_L(_W,_W,_E),_L(_S2,_W,_E),_L(_S2,_h,_R),_L(_h,_h,_R)],'nw_wing_roof')       # W2 NW slope (valley)
add('nw_wing',[_L(0,_T1,_E),_L(_W,_T1,_E),_L(_h,_T1,_R)],'nw_wing_wall')                    # gable at the NW end
add('nw_wing',[_L(_S2,_W,_E),_L(_S2,0,_E),_L(_S2,_h,_R)],'nw_wing_wall')                    # gable at the SW end (against the hall)
# low flat link between the SW gable and the hall
prism('nw_link',[_L(_S2,0,0)[:2],(-51.9,79.6),(-51.9,87.9)],0,3.6,'nw_link_wall','nw_link_roof')
# flat-roofed block north of the hall (two shallow pitches meeting at x=-63.5)
gable_roof('nw_north',UL([(-71.9,89.6+1.0),(-71.9,103.4),(-58.6,103.4),(-58.6,89.6+1.0)],5.0),5.0,5.6,'nw_north_roof',end='nw_north_wall')
prism('nw_north',[(-71.7,90.0),(-58.8,90.0),(-59.1,103.2),(-71.7,102.9)],0,5.0,'nw_north_wall')
# red-roof kiosk building between the Western Stand and the hall (skillion falling to the field), white annex
add('nw_red',[(-63.9,61.5,5.0),(-63.9,73.0,5.0),(-57.9,73.0,3.8),(-57.9,61.5,3.8)],'red_roof')
prism('nw_red',[(-63.6,61.8),(-58.2,61.8),(-58.2,72.7),(-63.6,72.7)],0,3.8,'red_wall')
add('nw_red',[(-63.6,61.8,3.8),(-63.6,72.7,3.8),(-63.6,72.7,5.0),(-63.6,61.8,5.0)],'red_wall')
prism('nw_annex',[(-69.0,62.0),(-63.9,62.0),(-63.9,73.0),(-69.0,73.0)],0,4.0,'annex_wall','annex_roof')
# ---------------- North end ----------------
# red hut: single roof plane rising from the north eave (2.8 m) to the south edge (3.8 m), small gable on the south edge
_HW,_HE,_HS,_HN=-10.27,-3.07,100.7,108.9
add('n_hut',[(_HW,_HN,2.8),(_HE,_HN,2.8),(_HE,_HS,3.8),(_HW,_HS,3.8)],'red_roof')
prism('n_hut',[(_HW+0.3,_HS+0.3),(_HE-0.3,_HS+0.3),(_HE-0.3,_HN-0.3),(_HW+0.3,_HN-0.3)],0,2.8,'hut_wall')
add('n_hut',[(_HW+0.3,_HS+0.3,2.8),(_HE-0.3,_HS+0.3,2.8),(_HE-0.3,_HS+0.3,3.65),(_HW+0.3,_HS+0.3,3.65)],'hut_wall')
for _x in (_HW+0.3,_HE-0.3): add('n_hut',[(_x,_HN-0.3,2.8),(_x,_HS+0.3,2.8),(_x,_HS+0.3,3.65)],'hut_wall')
add('n_hut',[(-8.0,_HS,3.8),(-5.07,_HS,3.8),(-6.53,_HS,4.6)],'red_roof')
add('n_hut',[(-8.0,_HS,3.8),(-6.53,_HS,4.6),(-6.53,_HS+1.9,4.0)],'red_roof')
add('n_hut',[(-5.07,_HS,3.8),(-6.53,_HS+1.9,4.0),(-6.53,_HS,4.6)],'red_roof')
# scoreboard (back seen in the main photo; satellite places it at y~105): 11 m wide, 4.5..6.8 m, on legs
_S0=np.array([0.6,104.6]);_S1=np.array([11.6,105.9])
add('n_board',[(*_S0,4.5),(*_S1,4.5),(*_S1,6.8),(*_S0,6.8)],'board_back')
add('n_board',[(*_S1,4.5),(*_S0,4.5),(*_S0,6.8),(*_S1,6.8)],'board_front')
for s_ in (_S0,_S1,(_S0+_S1)/2): box('n_board_legs',s_[0]-0.15,s_[0]+0.15,s_[1]-0.15,s_[1]+0.15,0,4.5,'steel')
# ---------------- South-east ----------------
prism('se_hut',UL([(60.5,-67.5),(64.5,-67.5),(64.5,-71.2),(60.5,-71.2)],3.8),0,3.8,'se_hut_wall','se_hut_roof')
hip('se_red',UL([(49.5,-91.6),(56.5,-88.6),(57.5,-90.8),(50.5,-93.8)],2.8),2.8,3.8,'red_roof')

# name board under the eave of the middle bay (c32: cream board, dark letters)
_c=SP(31.5,0.25,0);_e=SP(34.0,0.25,0)-SP(29.0,0.25,0);_e=_e/np.linalg.norm(_e)
add('ses_signboard',[_c-_e*2.5+V(0,0,ZE-1.05),_c+_e*2.5+V(0,0,ZE-1.05),_c+_e*2.5+V(0,0,ZE-0.55),_c-_e*2.5+V(0,0,ZE-0.55)],'ses_sign')

# ---------------- Wolf Blass Community Centre street sides: 0.9 m soffit over the ground floor, dark steel columns (woods2_ws) ----------------
for i in (2,3,4):
    (x0,y0),(x1,y1)=wb[i],wb[(i+1)%len(wb)];e=V(x1-x0,y1-y0,0);L_=np.linalg.norm(e);e/=L_
    o=-np.cross(e,[0,0,1.0]);o=o if np.dot(o[:2],np.array([x0,y0])-np.array([-56,-58]))>0 else -o
    A_=V(x0,y0,0);B_=V(x1,y1,0)
    add('wbcc_soffit',[A_+V(0,0,3.3),B_+V(0,0,3.3),B_+o*0.9+V(0,0,3.3),A_+o*0.9+V(0,0,3.3)],'wbcc_soffit')
    add('wbcc_soffit',[A_+o*0.9+V(0,0,3.0),B_+o*0.9+V(0,0,3.0),B_+o*0.9+V(0,0,3.3),A_+o*0.9+V(0,0,3.0+0.3)],'wbcc_soffit')
    add('wbcc_soffit',[A_+V(0,0,3.0),B_+V(0,0,3.0),B_+o*0.9+V(0,0,3.0),A_+o*0.9+V(0,0,3.0)],'wbcc_soffit')
    for d in np.arange(2.0,L_-0.5,4.0):
        c=A_+e*d+o*0.75;box('wbcc_cols',c[0]-0.1,c[0]+0.1,c[1]-0.1,c[1]+0.1,0,3.0,'steel_dark')
# ---------------- Signage along the west side (main photo) ----------------
# red boards standing 0.4 m inside the fence, 214-230 degrees, 0.9 m tall, facing the field
_us=0.0
for i in range(NT):
    d0=i*360/NT
    if not 214<=d0<230: continue
    t0=TH[i];t1=t0+np.radians(360/NT);ra,rb=RF[i]-0.4,RF[(i+1)%NT]-0.4
    u0=_us;_us+=float(np.linalg.norm(np.array(P(rb,t1,0))-np.array(P(ra,t0,0))));u1=_us
    add('signs',[P(ra,t0,0),P(rb,t1,0),P(rb,t1,0.9),P(ra,t0,0.9)],'sign_red',uv=[(u0,0),(u1,0),(u1,0.9),(u0,0.9)])
    add('signs',[P(ra+0.05,t0,0),P(rb+0.05,t1,0),P(rb+0.05,t1,0.9),P(ra+0.05,t0,0.9)],'steel_back')
# blue and white boards on the Western Stand's front brick wall, y -42..+7, 1.0-2.1 m up; dark LED board y +10..+15 above it
_WX=[wsx(_y,WS_FX,WS_FY)+PF for _y in WSY]
def _wallx(y): return float(np.interp(y,WSY,_WX))
_yb=list(np.arange(-42,7.01,7.0))
for k in range(len(_yb)-1):
    ya,yb_=_yb[k],_yb[k+1];xa=wsx(ya,WS_FX,WS_FY)+PF+0.03;xb=wsx(yb_,WS_FX,WS_FY)+PF+0.03
    _n=7;_ys=np.linspace(ya,yb_,_n+1)
    for q in range(_n):
        y0_,y1_=_ys[q],_ys[q+1];x0_=_wallx(y0_)+0.03;x1_=_wallx(y1_)+0.03   # on the brick wall's own chords, so no piece sinks behind it
        add('signs',[(x0_,y0_,1.0),(x1_,y1_,1.0),(x1_,y1_,2.1),(x0_,y0_,2.1)],'sign_blue' if k%2==0 else 'sign_white',uv=[(q/_n,0),((q+1)/_n,0),((q+1)/_n,1),(q/_n,1)])
xa=wsx(10,WS_FX,WS_FY)+PF+0.05;xb=wsx(15,WS_FX,WS_FY)+PF+0.05
add('signs',[(xa,10,2.4),(xb,15,2.4),(xb,15,3.4),(xa,10,3.4)],'led_board',uv=[(0,0),(1,0),(1,1),(0,1)])
for yy in (10.3,14.7): box('signs',xa-0.05,xa+0.05,yy-0.05,yy+0.05,2.1,2.4,'steel_dark')
# blue name board on the red-roofed kiosk's field side (main photo)
add('signs',[(-57.85,62.5,3.0),(-57.85,69.5,3.0),(-57.85,69.5,3.7),(-57.85,62.5,3.7)],'sign_kiosk',uv=[(0,0),(1,0),(1,1),(0,1)])
# ---------------- North-west: green hut beside the clubrooms (main photo: dark green walls, flat beige roof, cream edge) ----------------
_GH=[(-30.3,95.35),(-33.6,94.2),(-34.6,96.85),(-31.1,98.4)]
prism('nw_greenhut',_GH,0,2.8,'hut_green');prism('nw_greenhut',_GH,2.8,3.0,'paint_cream','roof_beige')
# boards on steel frames behind the north-east bank (main photo u 126-250): heights back-projected from their top and bottom edges
def hoard(d0,d1,z0,z1,mat,wall=False):
    segs=np.arange(d0,d1,2.0);n=len(segs);us=0.0
    for j,dg in enumerate(segs):
        i=int(dg/2)%NT;t0=np.radians(dg);t1=np.radians(dg+2);w0,w1=wterr(dg),wterr(dg+2)
        ra,rb=RF[i]+0.3+w0+0.3,RF[(i+1)%NT]+0.3+w1+0.3
        ua=us;us+=float(np.linalg.norm(np.array(P(rb,t1,0))-np.array(P(ra,t0,0))));ub=us
        uv=[(ua,0),(ub,0),(ub,0.9),(ua,0.9)] if wall else [(j/n,0),((j+1)/n,0),((j+1)/n,1),(j/n,1)]
        add('signs',[P(ra,t0,z0),P(rb,t1,z0),P(rb,t1,z1),P(ra,t0,z1)],mat,uv=uv)
        add('signs',[P(ra+0.08,t0,z0),P(rb+0.08,t1,z0),P(rb+0.08,t1,z1),P(ra+0.08,t0,z1)],'steel_back')
        rail('signs',P(ra+0.2,t0,0),P(ra+0.2,t0,z1),'steel_dark',0.12)
hoard(54,62,3.7,7.4,'hoard_red');hoard(62,70,3.4,8.0,'hoard_blue');hoard(70,76,5.3,7.4,'hoard_teal');hoard(76,92,4.3,6.3,'sign_red',wall=True)
# Director 2026-11-18: "just get the stadium model done not extra stuff": the near-side buildings below the north end are left out
for _k in ('nw_hall','nw_wing','nw_link','nw_north','nw_greenhut','n_hut','se_red','signs','field','goals'): parts.pop(_k,None)   # se_red: temporary marquee behind the SE terrace (stadium-only ruling); signs: director 2026-11-18 "C: no boards", bare fence at every ground; field: director 2026-11-18 "Leave field out" (the game draws its own grass); goals: director 2026-11-18 "Posts out" (the game draws its own goal and behind posts)
