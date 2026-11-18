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
sweep(span,[(8.5,4.0,None,0),(8.5,6.0,FENCE,1),(18.0,12.7,SEAT,1.5),(18.0,15.2,NAVY,1),(18.0,18.2,GLASS,1),(30.0,18.2,CONC,1),(30.0,0.0,CONC,1)])
sweep(arange(A1-360,A0,0.5),[(8.5,4.0,None,0),(14.0,4.0,WALK,1),(14.0,0.0,CONC,1)])
for a,flip in((A0,False),(A1,True)):
    vs=[bm.verts.new(P(a,d,z)) for d,z in [(8.5,4.0),(8.5,6.0),(18,12.7),(18,15.2),(18,18.2),(30,18.2),(30,0),(8.5,0)]]
    face(vs[::-1] if flip else vs,CONC)
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
SR=[0,0.03,0.06,0.09,0.12,0.16,0.22,0.32,0.45,0.6,0.75,0.88,1.0]
ra=arange(A0,A1,0.25)
def rp(a,s,dz=0.0):
    ri,ro=rin(a),rout(a);r=ri+(ro-ri)*s;z=hin(a)+(hout(a)-hin(a))*s
    z+=0.9*math.sin(math.pi*phase(a))*math.sin(math.pi*s)+dz
    t=math.radians(a);return Vector((r*math.cos(t)+SH[0],r*math.sin(t)+SH[1],z))
SH=D.get('roofshift',[0,0])
top=[[bm.verts.new(rp(a,s)) for a in ra] for s in SR];bot=[[bm.verts.new(rp(a,s,-0.6)) for a in ra] for s in SR]
for k in range(len(SR)-1):
    for i in range(len(ra)-1):
        sc=(SR[k]+SR[k+1])/2;ph=phase((ra[i]+ra[i+1])/2)
        face([top[k][i],top[k][i+1],top[k+1][i+1],top[k+1][i]],NAVY if sc<0.05+0.10*math.sin(math.pi*ph) else ROOF)
        face([bot[k][i+1],bot[k][i],bot[k+1][i],bot[k+1][i+1]],UNDER)
for i in range(len(ra)-1):
    face([top[0][i],bot[0][i],bot[0][i+1],top[0][i+1]],NAVY)
    n=len(SR)-1;face([top[n][i+1],bot[n][i+1],bot[n][i],top[n][i]],ROOF)
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
# towers: white shafts thicker at the base, thinner at the top; lamp heads face the centre, tilted down
for x,y,h in D['towers']:
    hb=h-9.0;cyl((x,y,0),(x,y,hb),1.35,0.55,TW,16);cyl((x,y,0),(x,y,2.0),2.0,1.9,CONC,16)
    ang=math.atan2(-y,-x);c=(x+0.6*math.cos(ang),y+0.6*math.sin(ang),h-4.3)
    obox(c,6.0,0.6,4.3,ang+math.pi/2,TW,tilt=math.radians(-20),front=LAMP)
    cyl((x,y,hb-0.5),(x,y,hb+0.5),1.6,1.6,TW,12)
# scoreboard (north end)
L,Rr,zb,zt=D['scoreboard'];L=Vector((*L,0));Rr=Vector((*Rr,0));mid=(L+Rr)/2;ang=math.atan2(Rr.y-L.y,Rr.x-L.x);half=(Rr-L).length/2
obox((mid.x,mid.y,(zb+zt)/2),half,0.7,(zt-zb)/2,ang,NAVY,front=SCR)
for e in (L,Rr):
    d=(e-mid).normalized()*1.3;obox((e.x-d.x,e.y-d.y,zt/2),1.3,0.9,zt/2,ang,WHITE)
# west podium (striped facade, flat roof) from the satellite footprint, plus the dark entrance block
POLY=[(-103,45),(-128,20.5),(-132.5,15.5),(-135,11),(-134.5,7),(-131,2),(-97,-39),(-90,-39),(-90,45)]
prism(POLY,0,10.6,STR,POD,uscale=12.0)
prism([(-104,46),(-95,56),(-87,48),(-96,38)],0,14.5,DARK,DARK)
prism([(-99,51),(-94,57),(-87,51),(-92,45)],0,21.5,DARK,DARK)
prism([(-63,86.5),(-86,63.5),(-84,61.5),(-61.5,84.5)],0,10.3,STR,DARK,uscale=12.0)
# yellow raking columns under the west and south-west roof edge, one per ridge
for a in R:
    if 118<=a<=250:
        t=math.radians(a);ro=rout(a);g0=Vector(((ro-10)*math.cos(t),(ro-10)*math.sin(t),0))
        cyl(g0,rp(a,0.92,-0.6),0.45,0.35,YEL,8)
bm.normal_update();bm.to_mesh(me);bm.free()
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out),export_format='GLB')
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
sd=bpy.data.lights.new('sun','SUN');sd.energy=4.0;so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so)
so.rotation_euler=(math.radians(35),0,math.radians(160))
w=bpy.data.worlds.new('w');w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(0.55,0.6,0.68,1);bg.inputs['Strength'].default_value=0.8;sc.world=w
sc.view_settings.view_transform='Standard'
sc.render.filepath=os.path.abspath(rpng);bpy.ops.render.render(write_still=True)
