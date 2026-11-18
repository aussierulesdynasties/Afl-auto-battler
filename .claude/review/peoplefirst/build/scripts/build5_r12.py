# People First Stadium exterior. blender -b -P build.py -- OUT.glb RENDER.png
import bpy,bmesh,sys,math,json,os
from mathutils import Vector,Matrix
sys.path.insert(0,os.getcwd())
out,rpng=sys.argv[sys.argv.index('--')+1:][:2]
D=json.load(open('geo_build.json'));CAM=json.load(open('cam.json'))['p']
RG,RIN,ROUT=D['RG'],D['rin'],D['rout']
def lerp_arr(A,a):
    f=(a%360)*4;i=int(f)%1440;t=f-int(f);return A[i]*(1-t)+A[(i+1)%1440]*t
rg=lambda a:lerp_arr(RG,a);rin=lambda a:lerp_arr(RIN,a);rout=lambda a:lerp_arr(ROUT,a)
def cf(c,a):r=math.radians(a);return c[0]+c[1]*math.cos(r)+c[2]*math.sin(r)
hin=lambda a:cf(D['hin'],a);hout=lambda a:cf(D['hout'],a)+(lerp_arr(D['hout_dz'],a) if 'hout_dz' in D else 0.0)
A0,A1=D['a0'],D['a1']
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('pf');ob=bpy.data.objects.new('PeopleFirstStadium',me);bpy.context.scene.collection.objects.link(ob)
bm=bmesh.new();uv=bm.loops.layers.uv.new()
TEX=json.load(open('htex/tex.json'))
MT={}
def mat(name,col,tex=None,rough=0.85,metal=0.0):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*[(c/255)**2.2 for c in col],1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if tex:
        t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.abspath('htex/'+tex+'.png'));t.interpolation='Linear'
        nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    me.materials.append(m);i=len(me.materials)-1;MT[i]=TEX[tex] if tex else [4.0,4.0];return i
GROUND=mat('ground',(150,150,140),None,0.95);APRON=mat('apron',(165,165,160),'apron');FENCE=mat('fence',(40,48,80),'led',0.5)
SEAT=mat('seats',(214,74,62),'seat_low');SEATU=mat('seats_up',(214,74,62),'seat_up');AIS=mat('aisle',(200,200,196),'aisle_low');AISU=mat('aisle_up',(200,200,196),'aisle_up')
WALK=mat('walk',(170,170,165),'walk');NAVY=mat('navy',(52,60,88),'navy',0.5)
GLASS=mat('glass',(45,52,70),'glass',0.25);CONC=mat('concrete',(190,188,182),'concrete');ROOF=mat('roof',(246,246,244),'roof',0.6)
UNDER=mat('roofunder',(215,215,212),'roofunder',0.7);YEL=mat('yellow',(238,190,40),'yellow',0.5,0.2);TW=mat('tower',(244,244,244),'tower',0.5)
LAMP=mat('lamps',(235,235,235),'lamps',0.4);SCR=mat('screen',(25,30,45),'screen',0.3);STR=mat('stripes',(200,120,80),'stripes',0.6)
SBF=mat('scorefront',(28,32,42),'scorefront',0.35);SBP=mat('scorepost',(250,249,248),'scorepost');RSG=mat('redsign',(243,56,59),'redsign',0.5)
POD=mat('podroof',(232,230,226),'podroof');DARK=mat('darkblock',(62,68,82),'dark',0.5);RED=mat('red',(205,40,40),'red',0.5);WHITE=mat('white',(236,236,236),'white')
UVSET=set()
def face(vs,mi,uvs=None):
    try:f=bm.faces.new(vs)
    except ValueError:return None
    f.material_index=mi
    if uvs:
        tw,th=MT[mi]
        for l,u in zip(f.loops,uvs):l[uv].uv=(u[0]/tw,u[1]/th)
        UVSET.add(f)
    return f
def P(a,d,z,base=None):
    r=(rg(a) if base is None else base(a))+d;t=math.radians(a);return Vector((r*math.cos(t),r*math.sin(t),z))
def sweep(angles,prof,base=None,uscale=None,mfun=None):
    angles=sorted(set(round(a,4) for a in angles))
    rows=[[bm.verts.new(P(a,d,z,base)) for a in angles] for d,z,_,_ in prof]
    vacc=0.0
    for k in range(1,len(prof)):
        mi=prof[k][2];L=math.hypot(prof[k][0]-prof[k-1][0],prof[k][1]-prof[k-1][1])
        cum=[0.0]
        for i in range(1,len(angles)):cum.append(cum[-1]+(rows[k][i].co-rows[k][i-1].co).length)
        for i in range(len(angles)-1):
            m2=mfun(k,(angles[i]+angles[i+1])/2,mi) if mfun else mi
            if m2 is None:continue
            face([rows[k-1][i],rows[k-1][i+1],rows[k][i+1],rows[k][i]],m2,[(cum[i],vacc),(cum[i+1],vacc),(cum[i+1],vacc+L),(cum[i],vacc+L)])
        vacc+=L
    return rows
def arange(a,b,s):
    n=max(2,int(round((b-a)/s))+1);return [a+(b-a)*i/(n-1) for i in range(n)]
MK=json.load(open('marks_final.json'))
VOMS=list(MK['voms'])
while VOMS[0]-6.65>A0+3:VOMS.insert(0,VOMS[0]-6.65)
def inint(a,c,hw):
    d=(a-c+180)%360-180;return abs(d)<=hw
def low_m(k,a,mi):
    if mi is not SEAT:return mi
    for o0,o1 in MK['low_openings']:
        if o0<=a%360<=o1:return CONC
    for c in MK['low_aisles']:
        if inint(a,c,math.degrees(0.55/(rg(a)+4))):return AIS
    return SEAT
def up_m(k,a,mi):
    if mi is not SEAT:return mi
    if k==4:return SEATU
    for c in VOMS:
        if inint(a,c,math.degrees(0.55/(rg(a)+13))):return AISU
    return SEATU
def edges(lst,dr,hwm):
    out=[]
    for c in lst:
        hw=math.degrees(hwm/(rg(c)+dr));out+=[c-hw,c+hw]
    return out
LOWE=edges(MK['low_aisles'],4,0.55)+[x for o in MK['low_openings'] for x in o]
UPE=edges(VOMS,13,0.55)
# no ground beyond the stadium (director 2026-11-18: background scene is a later pass)
# lower bowl all round
sweep(arange(0,360,0.5)+[e%360 for e in LOWE],[(0,0.02,None,0),(1.5,0.02,APRON,1),(1.5,1.0,FENCE,1),(6.5,4.0,SEAT,1.0),(8.5,4.0,WALK,1)],mfun=low_m)
span=arange(A0,A1,0.5)
SPROF=[(6.5,4.0),(6.5,6.0),(9.0,6.0),(9.0,6.4),(10.226,7.265),(24.0,16.98),(24.0,21.0),(25.0,21.0),(25.0,8.0),(26.0,8.0),(26.0,7.0),(16.0,7.0),(16.0,0.0)];SMAT=[None,FENCE,WALK,CONC,SEAT,SEAT,NAVY,CONC,NAVY,WALK,WALK,UNDER,DARK]
sweep(span+[e for e in UPE if A0<e<A1],[(d,z,SMAT[i],1) for i,(d,z) in enumerate(SPROF)],mfun=up_m)
sweep(span,[(26.0,8.0,None,0),(26.0,9.1,YEL,1)])
sweep(arange(A1-360,A0,0.5),[(8.5,4.0,None,0),(14.0,4.0,WALK,1),(14.0,0.0,CONC,1)])
for a,flip in((A0,False),(A1,True)):
    for poly in ([(6.5,0),(6.5,4.0),(6.5,6.0),(9.0,6.0),(9.0,6.4),(24,16.98),(24,21),(25,21),(25,8),(16,7),(16,0)],[(25,8),(26,8),(26,7),(16,7)]):
        vs=[bm.verts.new(P(a,d,z)) for d,z in poly];face(vs[::-1] if flip else vs,CONC)
# roof panels between ridges (inward points of the outer scallop line), gaps filled at the median spacing
V=sorted(D['valleys']);med=sorted(V[i+1]-V[i] for i in range(len(V)-1))[len(V)//2]
R=[A0]
for v in V+[A1]:
    while v-R[-1]>1.5*med:R.append(R[-1]+med)
    if v-R[-1]>0.4*med:R.append(v)
R[-1]=A1
def phase(a):
    for i in range(len(R)-1):
        if R[i]<=a<=R[i+1]:return (a-R[i])/(R[i+1]-R[i])
    return 0.0
SR=[0,0.04,0.08,0.13,0.18,0.24,0.32,0.45,0.6,0.72,0.82,0.88,0.92,0.95,0.975,0.99,1.0]
LOBE_IN=float(os.environ.get('LOBE_IN',1.2));LOBE_OUT=float(os.environ.get('LOBE_OUT',3.5));CAP0=float(os.environ.get('CAP0',0.86))
ra=arange(A0,A1,0.125)
def rp(a,s,dz=0.0):
    ph=phase(a);ri=rin(a)+0.8-1.6*math.sin(math.pi*ph);ro=rout(a);r=ri+(ro-ri)*s;z=hin(a)+(hout(a)-hin(a))*s
    # inflated tube lobe: round cross-section (sqrt of sine), height grows outward, domed cap at the outer end
    A=LOBE_IN+(LOBE_OUT-LOBE_IN)*s
    cap=math.sqrt(max(0.0,1-((s-CAP0)/(1-CAP0))**2)) if s>CAP0 else 1.0
    z+=A*math.sqrt(max(0.0,math.sin(math.pi*ph)))*cap+dz
    t=math.radians(a);return Vector((r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],z))
SH=D.get('roofshift',[0,0])
top=[[bm.verts.new(rp(a,s)) for a in ra] for s in SR];bot=[[bm.verts.new(rp(a,s,-0.6)) for a in ra] for s in SR]
def gridcum(G):
    U=[[0.0]+[0.0]*(len(ra)-1) for _ in SR];Vv=[[0.0]*len(ra) for _ in SR]
    for k in range(len(SR)):
        for i in range(1,len(ra)):U[k][i]=U[k][i-1]+(G[k][i].co-G[k][i-1].co).length
    for k in range(1,len(SR)):
        for i in range(len(ra)):Vv[k][i]=Vv[k-1][i]+(G[k][i].co-G[k-1][i].co).length
    return U,Vv
TU,TV=gridcum(top);BU,BV=gridcum(bot)
for k in range(len(SR)-1):
    for i in range(len(ra)-1):
        sc=(SR[k]+SR[k+1])/2;ph=phase((ra[i]+ra[i+1])/2)
        q=[(k,i),(k,i+1),(k+1,i+1),(k+1,i)]
        face([top[a][b] for a,b in q],NAVY if sc<0.13 else ROOF,[(TU[a][b],TV[a][b]) for a,b in q])
        q=[(k,i+1),(k,i),(k+1,i),(k+1,i+1)]
        face([bot[a][b] for a,b in q],UNDER,[(BU[a][b],BV[a][b]) for a,b in q])
for i in range(len(ra)-1):
    face([top[0][i],bot[0][i],bot[0][i+1],top[0][i+1]],YEL)
    n=len(SR)-1;face([top[n][i+1],bot[n][i+1],bot[n][i],top[n][i]],YEL)
for i in (0,len(ra)-1):
    for k in range(len(SR)-1):face([top[k][i],top[k+1][i],bot[k+1][i],bot[k][i]] if i==0 else [top[k+1][i],top[k][i],bot[k][i],bot[k+1][i]],YEL)
def prism(poly,z0,z1,mside,mtop,uscale=4.0):
    b=[bm.verts.new((x,y,z0)) for x,y in poly];t=[bm.verts.new((x,y,z1)) for x,y in poly];n=len(poly);acc=0
    for i in range(n):
        j=(i+1)%n;L=(Vector(poly[j])-Vector(poly[i])).length
        face([b[i],b[j],t[j],t[i]],mside,[(acc,0),(acc+L,0),(acc+L,z1-z0),(acc,z1-z0)]);acc+=L
    face(t,mtop);face(b[::-1],mtop)
def cyl(p0,p1,r0,r1,mi,n=12):
    p0,p1=Vector(p0),Vector(p1);ax=(p1-p0).normalized();q=ax.orthogonal().normalized();w=ax.cross(q);Ln=(p1-p0).length
    a=[bm.verts.new(p0+(q*math.cos(2*math.pi*i/n)+w*math.sin(2*math.pi*i/n))*r0) for i in range(n)]
    b=[bm.verts.new(p1+(q*math.cos(2*math.pi*i/n)+w*math.sin(2*math.pi*i/n))*r1) for i in range(n)]
    C=2*math.pi*(r0+r1)/2;tw,th=MT[mi]
    for i in range(n):face([a[i],a[(i+1)%n],b[(i+1)%n],b[i]],mi,[(C*i/n,0),(C*(i+1)/n,0),(C*(i+1)/n,Ln),(C*i/n,Ln)])
    def cap(vs,c):return [((v.co-c).dot(q)+0.5*tw,(v.co-c).dot(w)+0.5*th) for v in vs]
    face(b,mi,cap(b,p1));face(a[::-1],mi,cap(a[::-1],p0))
def obox(c,ex,ey,ez,ang,mi,tilt=0.0,front=None,fullfront=False,allsides=False):
    ca,sa=math.cos(ang),math.sin(ang);ux=Vector((ca,sa,0));uy=Vector((-sa,ca,0));uz=Vector((0,0,1))
    rot=Matrix.Rotation(tilt,3,ux);uy2=rot@uy;uz2=rot@uz;C=Vector(c);vs=[]
    for sx,sy,sz in((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)):
        vs.append(bm.verts.new(C+ux*sx*ex+uy2*sy*ey+uz2*sz*ez))
    for fi,m_ in [((0,3,2,1),mi),((4,5,6,7),mi),((0,1,5,4),front if front is not None else mi),((1,2,6,5),mi),((2,3,7,6),mi),((3,0,4,7),mi)]:
        sc_=MT[m_] if ((fullfront and fi==(0,1,5,4)) or (allsides and fi not in((0,3,2,1),(4,5,6,7)))) else (1,1)
        face([vs[i] for i in fi],m_,[(0,0),(sc_[0],0),(sc_[0],sc_[1]),(0,sc_[1])])

def lamphead(x,y,h,ang):
    # trapezoid lattice head measured from the photo: 13.2 m wide at top, 11.2 m at bottom, 9.9 m tall (measured on two main-photo heads), 6 lamp shelves, back spine
    fwd=Vector((math.cos(ang),math.sin(ang),0));side=Vector((-math.sin(ang),math.cos(ang),0));up=Vector((0,0,1))
    tl=math.radians(20);fz=fwd*math.cos(tl)-up*math.sin(tl);uz=up*math.cos(tl)+fwd*math.sin(tl)
    C=Vector((x,y,h-5.5))+fwd*0.9
    def pt(sx,sz,sd=0.0):return C+side*sx+uz*sz+fz*sd
    def bar(a,b,r=0.14,m=TW):cyl(a,b,r,r,m,6)
    H2=4.95;wt,wb=6.6,5.6
    hw=lambda z:wb+(wt-wb)*(z+H2)/(2*H2)
    for sd in (0.0,-1.2):
        bar(pt(-wb,-H2,sd),pt(-wt,H2,sd));bar(pt(wb,-H2,sd),pt(wt,H2,sd));bar(pt(-wt,H2,sd),pt(wt,H2,sd));bar(pt(-wb,-H2,sd),pt(wb,-H2,sd))
    for zz in (-H2,H2):
        for sx in (-1,1):bar(pt(sx*hw(zz),zz,0),pt(sx*hw(zz),zz,-1.2))
    bar(pt(0,-H2-1.0,-1.2),pt(0,H2,-1.2),0.3)
    for i in range(6):
        z=-H2+0.75+i*(2*H2-1.5)/5;w=hw(z)-0.3
        obox(pt(0,z-0.55,-0.6),w,0.6,0.08,ang+math.pi/2,TW,tilt=-tl)
        n=8 if i<2 else 10
        for j in range(n):
            sx=-w+0.45+j*(2*w-0.9)/(n-1);p0=pt(sx,z,-0.4);p1=pt(sx,z,0.25)
            cyl(p0,p1,0.36,0.42,LAMP,10)
# towers: white shafts thicker at the base, thinner at the top; lamp heads face the centre, tilted down
for x,y,h in D['towers']:
    hb=h-11.0;cyl((x,y,0),(x,y,hb),1.35,0.55,TW,16);cyl((x,y,0),(x,y,2.0),2.0,1.9,CONC,16)
    ang=math.atan2(-y,-x);lamphead(x,y,h,ang)
    cyl((x,y,hb-0.5),(x,y,hb+0.5),1.6,1.6,TW,12)
# scoreboard (north end)
L,Rr,zb,zt=D['scoreboard'];L=Vector((*L,0));Rr=Vector((*Rr,0));mid=(L+Rr)/2;ang=math.atan2(Rr.y-L.y,Rr.x-L.x);half=(Rr-L).length/2
obox((mid.x,mid.y,(zb+zt)/2),half+2.0,0.7,(zt-zb)/2,ang,NAVY,front=SBF,fullfront=True)  # board runs over the end posts (photo grid: corners ~6 px past L/R)
for e in (L,Rr):
    # end posts measured on the photo grid: outer face flush with the board end, 1.2 m thick, 3.4 m deep
    # (end face spans x425-440 at 4.5 px/m: from 0.5 m behind the board line to 2.9 m in front), top 12.2 m
    d=(e-mid).normalized();uyp=Vector((-math.sin(ang),math.cos(ang),0));o=e+d*2.0-d*0.6-uyp*1.2;obox((o.x,o.y,6.1),0.6,1.7,6.1,ang,SBP,allsides=True)
# legs and the red sign under the board (positions along the board measured on the photo grid: legs 0.37/0.71, sign 0.40-0.68)
ux_=(Rr-L).normalized();uy_=Vector((-ux_.y,ux_.x,0))
for f_ in (0.37,0.71):
    p_=L+ux_*(2*half*f_);cyl((p_.x,p_.y,0),(p_.x,p_.y,zb),0.35,0.35,WHITE,10)
p_=L+ux_*(2*half*0.54)-uy_*1.5;obox((p_.x,p_.y,1.3),4.15,0.25,1.3,ang,WHITE,front=RSG,fullfront=True)
# west podium (striped facade, flat roof) from the satellite footprint, plus the dark entrance block
POLY=[(-103,45),(-128,20.5),(-132.5,15.5),(-135,11),(-134.5,7),(-131,2),(-97,-39),(-90,-39),(-90,45)]
prism(POLY,0,10.6,STR,POD,uscale=12.0)
prism([(-105.2,46.1),(-99.7,60.1),(-86,56),(-92,40)],0,21.5,DARK,DARK)
prism([(-63,86.5),(-86,63.5),(-84,61.5),(-61.5,84.5)],0,10.3,STR,DARK,uscale=12.0)

# buildings under the near roof, measured from the photo (white, flat roofs), the tank and the red drum on the podium
prism([(-98.9,-48.0),(-89.3,-69.5),(-96.2,-77.8),(-104.9,-74.0),(-115.0,-49.4)],0,5.8,WHITE,WHITE)
prism([(-73.0,-93.5),(-64.0,-104.3),(-66.9,-109.1),(-83.1,-108.7),(-85.7,-96.4)],0,6.0,WHITE,WHITE)
cyl((-71.5,-111.8,0),(-71.5,-111.8,9.8),3.4,3.4,DARK,20)
dr=[];cx,cy_,rr=-97.5,-14.4,5.6
for i in range(13):
    t=math.radians(90+180*i/12);dr.append((cx+rr*math.cos(t),cy_+rr*math.sin(t)))
prism(dr,10.6,21.0,RED,DARK,uscale=40.0)
# yellow raking columns under the west and south-west roof edge, one per ridge
for i in range(1,len(R)-1):
    a=R[i];t=math.radians(a);ro=rout(a)-9;g0=Vector((ro*math.cos(t)+SH[0],ro*math.sin(t)+SH[1],0));fk=Vector((g0.x,g0.y,9.0))
    cyl(g0,fk,0.45,0.4,YEL,8)
    for da in (-0.32,0.32):
        a2=a+da*(R[i+1]-R[i] if da>0 else R[i]-R[i-1]);cyl(fk,rp(a2,0.93,-0.6),0.35,0.3,YEL,8)
# vomitories: opening in the upper tier at each measured angle, 2.4 m wide, front 1.5 m up the slope, hood over 3 m
def T(a,sl,dz=0.0):
    t=sl/11.62;d=9.0+9.5*t;z=6.4+6.7*t+dz;r=rg(a)+d;th=math.radians(a);return Vector((r*math.cos(th),r*math.sin(th),z))
for a in VOMS:
    if not (A0<a<A1):continue
    th=math.radians(a);tv=Vector((-math.sin(th),math.cos(th),0))
    F=T(a,0.15);zt=F.z+2.4;B=T(a,0.15+2.4/(6.7/11.62))
    # across the opening: white jamb 0.6 m | dark opening 1.8 m | white jamb 0.6 m
    xs=[-1.5,-0.9,0.9,1.5];MS=[WHITE,DARK,WHITE];HD=[WHITE,RED,WHITE]
    fb=[bm.verts.new(F+tv*x) for x in xs];ft=[bm.verts.new(Vector((F.x,F.y,zt))+tv*x) for x in xs];bt=[bm.verts.new(Vector((B.x,B.y,zt))+tv*x) for x in xs]
    Hf=zt-F.z;D_=(B-F).length
    for k in range(3):
        w0,w1=xs[k]+1.5,xs[k+1]+1.5
        if k==1:
            fm=[bm.verts.new(Vector((F.x,F.y,zt-0.5))+tv*x) for x in xs[1:3]]
            face([fb[1],fb[2],fm[1],fm[0]][::-1],DARK,[(w0,0),(w1,0),(w1,Hf-0.5),(w0,Hf-0.5)][::-1])
            face([fm[0],fm[1],ft[2],ft[1]][::-1],RED,[(w0,Hf-0.5),(w1,Hf-0.5),(w1,Hf),(w0,Hf)][::-1])
        else:face([fb[k],fb[k+1],ft[k+1],ft[k]][::-1],MS[k],[(w0,0),(w1,0),(w1,Hf),(w0,Hf)][::-1])
        face([ft[k],ft[k+1],bt[k+1],bt[k]],SEATU if k==1 else WHITE,[(w0,0),(w1,0),(w1,D_),(w0,D_)])
    face([fb[0],ft[0],bt[0]],WHITE,[(0,0),(0,Hf),(D_,Hf)])
    face([bt[3],ft[3],fb[3]],WHITE,[(D_,Hf),(0,Hf),(0,0)])
bm.normal_update()
for f in bm.faces:
    if f in UVSET:continue
    n=f.normal;tw,th=MT[f.material_index]
    if abs(n.z)>0.7:co=[(l.vert.co.x,l.vert.co.y) for l in f.loops]
    else:
        t=Vector((-n.y,n.x,0));t=t.normalized() if t.length>1e-6 else Vector((1,0,0));co=[(l.vert.co.dot(t),l.vert.co.z) for l in f.loops]
    for l,c in zip(f.loops,co):l[uv].uv=(c[0]/tw,c[1]/th)
bm.to_mesh(me);bm.free()
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out),export_format='GLB')
if os.environ.get('SAVEBLEND'):bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.environ['SAVEBLEND']))
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=2000;sc.render.resolution_y=1333;sc.render.film_transparent=True
cd=bpy.data.cameras.new('cam');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=CAM[6]*36/2000;cd.clip_end=5000;cd.clip_start=50
co=bpy.data.objects.new('cam',cd);sc.collection.objects.link(co);sc.camera=co
def RR(yaw,p_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(p_),math.sin(p_);cr,sr=math.cos(roll),math.sin(roll)
    f=Vector((cy*cp,sy*cp,sp));r=Vector((sy,-cy,0.0));u=r.cross(f)
    return [cr*r+sr*u,-sr*r+cr*u,f]
M=RR(*CAM[3:6])
Mb=Matrix(((M[0][0],M[1][0],-M[2][0]),(M[0][1],M[1][1],-M[2][1]),(M[0][2],M[1][2],-M[2][2])))
co.matrix_world=Matrix.Translation(Vector(CAM[:3]))@Mb.to_4x4()
sd=bpy.data.lights.new('sun','SUN');sd.energy=2.7;so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so)
so.rotation_euler=(math.radians(40),0,math.radians(-141))
w=bpy.data.worlds.new('w');w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(0.55,0.6,0.68,1);bg.inputs['Strength'].default_value=0.55;sc.world=w
sc.view_settings.view_transform='Standard'
sc.render.filepath=os.path.abspath(rpng);bpy.ops.render.render(write_still=True)
