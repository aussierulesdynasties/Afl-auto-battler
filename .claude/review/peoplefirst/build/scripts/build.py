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
hin=lambda a:cf(D['hin'],a);hout=lambda a:cf(D['hout'],a)
A0,A1=D['a0'],D['a1']
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('pf');ob=bpy.data.objects.new('PeopleFirstStadium',me);bpy.context.scene.collection.objects.link(ob)
bm=bmesh.new();uv=bm.loops.layers.uv.new()
def mat(name,col,tex=None,rough=0.85,metal=0.0):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*[(c/255)**2.2 for c in col],1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if tex:
        t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.abspath('tex/'+tex))
        nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    me.materials.append(m);return len(me.materials)-1
GROUND=mat('ground',(150,150,140),'ground.png',0.95);APRON=mat('apron',(165,165,160));FENCE=mat('fence',(40,48,80),'led.png',0.5)
SEAT=mat('seats',(214,74,62),'seats.png');WALK=mat('walk',(170,170,165));NAVY=mat('navy',(52,60,88),None,0.5)
GLASS=mat('glass',(45,52,70),None,0.25);CONC=mat('concrete',(190,188,182));ROOF=mat('roof',(246,246,244),None,0.6)
UNDER=mat('roofunder',(215,215,212),None,0.7);YEL=mat('yellow',(238,190,40),None,0.5,0.2);TW=mat('tower',(244,244,244),None,0.5)
LAMP=mat('lamps',(235,235,235),'lamps.png',0.4);SCR=mat('screen',(25,30,45),'screen.png',0.3);STR=mat('stripes',(200,120,80),'stripes.png',0.6)
POD=mat('podroof',(232,230,226));DARK=mat('darkblock',(62,68,82),None,0.5);RED=mat('red',(205,40,40),None,0.5);WHITE=mat('white',(236,236,236))
def face(vs,mi,uvs=None):
    try:f=bm.faces.new(vs)
    except ValueError:return None
    f.material_index=mi
    if uvs:
        for l,u in zip(f.loops,uvs):l[uv].uv=u
    return f
def P(a,d,z,base=None):
    r=(rg(a) if base is None else base(a))+d;t=math.radians(a);return Vector((r*math.cos(t),r*math.sin(t),z))
def sweep(angles,prof,base=None,uscale=4.0):
    cum=[0.0]
    for i in range(1,len(angles)):cum.append(cum[-1]+(P(angles[i],0,0,base)-P(angles[i-1],0,0,base)).length)
    rows=[[bm.verts.new(P(a,d,z,base)) for a in angles] for d,z,_,_ in prof]
    for k in range(1,len(prof)):
        mi,vr=prof[k][2],prof[k][3]
        for i in range(len(angles)-1):
            u0,u1=cum[i]/uscale,cum[i+1]/uscale
            face([rows[k-1][i],rows[k-1][i+1],rows[k][i+1],rows[k][i]],mi,[(u0,0),(u1,0),(u1,vr),(u0,vr)])
    return rows
def arange(a,b,s):
    n=max(2,int(round((b-a)/s))+1);return [a+(b-a)*i/(n-1) for i in range(n)]
# ground (satellite photo, roof painted out)
g=[bm.verts.new((x,y,-0.05)) for x,y in((-200,-200),(200,-200),(200,200),(-200,200))]
if not os.environ.get('NOGROUND'):face(g,GROUND,[(0,0),(1,0),(1,1),(0,1)])
# lower bowl all round
sweep(arange(0,360,0.5),[(0,0.02,None,0),(1.5,0.02,APRON,1),(1.5,1.0,FENCE,1),(6.5,4.0,SEAT,1.0),(8.5,4.0,WALK,1)])
span=arange(A0,A1,0.5)
SPROF=[(8.5,4.0),(8.5,6.0),(18.0,12.7),(18.0,15.2),(18.0,18.2),(21.0,18.2),(21.0,8.0),(26.0,8.0),(26.0,7.0),(16.0,7.0),(16.0,0.0)];SMAT=[None,FENCE,SEAT,NAVY,GLASS,CONC,NAVY,WALK,WALK,UNDER,DARK]
sweep(span,[(d,z,SMAT[i],1.5 if SMAT[i] is SEAT else 1) for i,(d,z) in enumerate(SPROF)])
sweep(span,[(26.0,8.0,None,0),(26.0,9.1,YEL,1)])
sweep(arange(A1-360,A0,0.5),[(8.5,4.0,None,0),(14.0,4.0,WALK,1),(14.0,0.0,CONC,1)])
for a,flip in((A0,False),(A1,True)):
    for poly in ([(8.5,0),(8.5,4.0),(8.5,6.0),(18,12.7),(18,15.2),(18,18.2),(21,18.2),(21,8),(16,7),(16,0)],[(21,8),(26,8),(26,7),(16,7)]):
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
for k in range(len(SR)-1):
    for i in range(len(ra)-1):
        sc=(SR[k]+SR[k+1])/2;ph=phase((ra[i]+ra[i+1])/2)
        face([top[k][i],top[k][i+1],top[k+1][i+1],top[k+1][i]],NAVY if sc<0.13 else ROOF)
        face([bot[k][i+1],bot[k][i],bot[k+1][i],bot[k+1][i+1]],UNDER)
for i in range(len(ra)-1):
    face([top[0][i],bot[0][i],bot[0][i+1],top[0][i+1]],NAVY)
    n=len(SR)-1;face([top[n][i+1],bot[n][i+1],bot[n][i],top[n][i]],YEL)
for i in (0,len(ra)-1):
    for k in range(len(SR)-1):face([top[k][i],top[k+1][i],bot[k+1][i],bot[k][i]] if i==0 else [top[k+1][i],top[k][i],bot[k][i],bot[k+1][i]],YEL)
def prism(poly,z0,z1,mside,mtop,uscale=4.0):
    b=[bm.verts.new((x,y,z0)) for x,y in poly];t=[bm.verts.new((x,y,z1)) for x,y in poly];n=len(poly);acc=0
    for i in range(n):
        j=(i+1)%n;L=(Vector(poly[j])-Vector(poly[i])).length
        face([b[i],b[j],t[j],t[i]],mside,[(acc/uscale,0),((acc+L)/uscale,0),((acc+L)/uscale,1),(acc/uscale,1)]);acc+=L
    face(t,mtop);face(b[::-1],mtop)
def cyl(p0,p1,r0,r1,mi,n=12):
    p0,p1=Vector(p0),Vector(p1);ax=(p1-p0).normalized();q=ax.orthogonal().normalized();w=ax.cross(q)
    a=[bm.verts.new(p0+(q*math.cos(2*math.pi*i/n)+w*math.sin(2*math.pi*i/n))*r0) for i in range(n)]
    b=[bm.verts.new(p1+(q*math.cos(2*math.pi*i/n)+w*math.sin(2*math.pi*i/n))*r1) for i in range(n)]
    for i in range(n):face([a[i],a[(i+1)%n],b[(i+1)%n],b[i]],mi)
    face(b,mi);face(a[::-1],mi)
def obox(c,ex,ey,ez,ang,mi,tilt=0.0,front=None):
    ca,sa=math.cos(ang),math.sin(ang);ux=Vector((ca,sa,0));uy=Vector((-sa,ca,0));uz=Vector((0,0,1))
    rot=Matrix.Rotation(tilt,3,ux);uy2=rot@uy;uz2=rot@uz;C=Vector(c);vs=[]
    for sx,sy,sz in((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)):
        vs.append(bm.verts.new(C+ux*sx*ex+uy2*sy*ey+uz2*sz*ez))
    for fi,m_ in [((0,3,2,1),mi),((4,5,6,7),mi),((0,1,5,4),front if front is not None else mi),((1,2,6,5),mi),((2,3,7,6),mi),((3,0,4,7),mi)]:
        face([vs[i] for i in fi],m_,[(0,0),(1,0),(1,1),(0,1)])

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
obox((mid.x,mid.y,(zb+zt)/2),half,0.7,(zt-zb)/2,ang,NAVY,front=SCR)
for e in (L,Rr):
    d=(e-mid).normalized()*1.3;obox((e.x-d.x,e.y-d.y,zt/2),1.3,0.9,zt/2,ang,WHITE)
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
bm.normal_update();bm.to_mesh(me);bm.free()
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
sd=bpy.data.lights.new('sun','SUN');sd.energy=3.3;so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so)
so.rotation_euler=(math.radians(40),0,math.radians(-141))
w=bpy.data.worlds.new('w');w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(0.55,0.6,0.68,1);bg.inputs['Strength'].default_value=0.8;sc.world=w
sc.view_settings.view_transform='Standard'
sc.render.filepath=os.path.abspath(rpng);bpy.ops.render.render(write_still=True)
