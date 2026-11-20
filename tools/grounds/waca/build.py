# WACA 1992 exterior, world metres (x east, y north, z up).
# blender -b --python build.py -- OUT.glb [render.png]
import bpy,bmesh,math,json,sys,os
from mathutils import Vector,Matrix
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
HERE=os.path.dirname(os.path.abspath(__file__))
cam=json.load(open(os.path.join(HERE,'cam92f.json')))
P=json.load(open(os.path.join(HERE,'parts.json')))
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
MATS={}
def mat(name,rgb):
    if name in MATS:return MATS[name]
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*rgb,1);b.inputs['Roughness'].default_value=0.85
    MATS[name]=m;return m
C={'grass':(0.16,0.36,0.08),'red':(0.42,0.12,0.07),'green':(0.02,0.30,0.12),'dark':(0.05,0.06,0.08),'white':(0.80,0.80,0.80),
   'roof':(0.62,0.62,0.62),'brick':(0.45,0.20,0.10),'tent':(0.70,0.68,0.66),'concrete':(0.55,0.53,0.50),'blue':(0.20,0.35,0.60),
   'board':(0.03,0.03,0.04),'yellow':(0.85,0.55,0.05),'path':(0.60,0.57,0.52),'aisle':(0.85,0.85,0.85),'glass':(0.10,0.12,0.15),'road':(0.10,0.10,0.11),'land':(0.18,0.16,0.11),'terrace':(0.42,0.12,0.07),'loft':(0.30,0.30,0.32),'greenseat':(0.02,0.26,0.09),'navyseat':(0.03,0.06,0.10),'emuroof':(0.16,0.15,0.16),'emufascia':(0.41,0.30,0.27),'emuband':(0.49,0.46,0.44),'emubrick':(0.67,0.30,0.14),'ledge':(0.49,0.30,0.16),'gf':(0.21,0.18,0.20),'chair':(0.51,0.30,0.06),'emutruss':(0.30,0.22,0.19),'emusign':(0.8,0.8,0.8),'crownred':(0.65,0.03,0.02),'bbframe':(0.35,0.25,0.12),'sbface':(0.03,0.03,0.04),'sbcrown':(0.65,0.03,0.02),'bb1':(0.85,0.85,0.85),'bb2':(0.85,0.85,0.85)}
OBJ={}
def bm_for(name):
    if name not in OBJ:OBJ[name]=bmesh.new()
    return OBJ[name]
def quad(name,pts):
    bm=bm_for(name);vs=[bm.verts.new(p) for p in pts]
    try:bm.faces.new(vs)
    except ValueError:pass
def boxpts(name,c,z0,z1,top=None):
    top=top or name
    for i in range(len(c)):
        a,b=c[i],c[(i+1)%len(c)];quad(name,[(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)])
    quad(top,[(p[0],p[1],z1) for p in c])
def box(name,cx,cy,w,d,z0,z1,ang=0,top=None):
    ca,sa=math.cos(ang),math.sin(ang)
    boxpts(name,[(cx+ca*x-sa*y,cy+sa*x+ca*y) for x,y in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]],z0,z1,top)
EC=(9.0,1.0)
FP=[(108,0),(107,25),(101,48),(80,62),(50,67),(0,72),(-50,61.7),(-70,52),(-82,40),(-89,25),(-90.5,0),(-86,-25),(-75,-38),(-50,-59.5),(0,-69.2),(50,-62),(75,-49),(90,-33),(104,-15)]
def _dense(n=24):
    out=[];N=len(FP)
    for i in range(N):
        p0,p1,p2,p3=FP[i-1],FP[i],FP[(i+1)%N],FP[(i+2)%N]
        for k in range(n):
            t=k/n
            out.append(tuple(0.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t*t+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t**3) for j in (0,1)))
    return out
_D=_dense();_A=sorted((math.atan2(y-EC[1],x-EC[0]),math.hypot(x-EC[0],y-EC[1])) for x,y in _D)
_A=[(a-2*math.pi,r) for a,r in _A[-3:]]+_A+[(a+2*math.pi,r) for a,r in _A[:3]]
def frad(t):
    t=math.atan2(math.sin(t),math.cos(t))
    for i in range(len(_A)-1):
        if _A[i][0]<=t<=_A[i+1][0]:
            s=(t-_A[i][0])/((_A[i+1][0]-_A[i][0]) or 1);return _A[i][1]+(_A[i+1][1]-_A[i][1])*s
    return _A[0][1]
def ell(t,d=0):r=frad(t)+d;return (EC[0]+r*math.cos(t),EC[1]+r*math.sin(t))
def tof(x,y):return math.atan2(y-EC[1],x-EC[0])
def lerp(a,b,s):return (a[0]+(b[0]-a[0])*s,a[1]+(b[1]-a[1])*s)
def unwrap(ts):
    for i in range(1,len(ts)):
        while ts[i]-ts[i-1]>math.pi:ts[i]-=2*math.pi
        while ts[i]-ts[i-1]<-math.pi:ts[i]+=2*math.pi
    return ts
def backpt(poly,ts,t):
    for i in range(len(ts)-1):
        a,b=ts[i],ts[i+1]
        if (a-t)*(b-t)<=0 and a!=b:return lerp(poly[i],poly[i+1],(t-a)/(b-a))
    return poly[0] if abs(t-ts[0])<abs(t-ts[-1]) else poly[-1]
def sector(poly,n=24,fd=1.5):
    ts=unwrap([tof(*p) for p in poly])
    T=[ts[0]+(ts[-1]-ts[0])*k/n for k in range(n+1)]
    return T,[ell(t,fd) for t in T],[backpt(poly,ts,t) for t in T]
def loft(name,S,s0,s1,z0,z1):
    T,F,B=S
    for k in range(len(T)-1):
        a0,a1=lerp(F[k],B[k],s0),lerp(F[k],B[k],s1);b0,b1=lerp(F[k+1],B[k+1],s0),lerp(F[k+1],B[k+1],s1)
        quad(name,[(a0[0],a0[1],z0),(b0[0],b0[1],z0),(b1[0],b1[1],z1),(a1[0],a1[1],z1)])
def endwalls(name,S,prof):
    T,F,B=S
    for k in (0,len(T)-1):
        pts=[(*lerp(F[k],B[k],prof[0][0]),0)]+[(*lerp(F[k],B[k],s),z) for s,z in prof]+[(*lerp(F[k],B[k],prof[-1][0]),0)]
        quad(name,pts)
def terrace(name,S,s0,s1,z0,z1,steps,aisle_every=0):
    T,F,B=S
    for i in range(steps):
        sa,sb=s0+(s1-s0)*i/steps,s0+(s1-s0)*(i+1)/steps;za,zb=z0+(z1-z0)*i/steps,z0+(z1-z0)*(i+1)/steps
        loft(name,S,sa,sa,za,zb);loft(name,S,sa,sb,zb,zb)
    if aisle_every:
        for k in range(aisle_every,len(T)-1,aisle_every):
            for i in range(steps):
                sa,sb=s0+(s1-s0)*i/steps,s0+(s1-s0)*(i+1)/steps;zb=z0+(z1-z0)*(i+1)/steps+0.03
                a0,a1=lerp(F[k],B[k],sa),lerp(F[k],B[k],sb)
                d=(F[k+1][0]-F[k][0],F[k+1][1]-F[k][1]);L=math.hypot(*d) or 1;e=(d[0]/L*0.6,d[1]/L*0.6)
                quad('aisle',[(a0[0],a0[1],zb),(a0[0]+e[0],a0[1]+e[1],zb),(a1[0]+e[0],a1[1]+e[1],zb),(a1[0],a1[1],zb)])
def build_part(pt):
    S=sector(pt['back'],pt.get('n',24),pt.get('fd',1.5))
    for op in pt['ops']:
        k=op[0]
        if k=='terrace':terrace(op[1],S,*op[2:])
        elif k=='loft':loft(op[1],S,*op[2:])
        elif k=='wall':loft(op[1],S,op[2],op[2],op[3],op[4])
        elif k=='ends':endwalls(op[1],S,op[2])
        elif k=='tents':
            _,nm,s0,s1,ze,zr,step=op;T,F,B=S
            for j in range(0,len(T)-step,step):
                a0,a1=lerp(F[j],B[j],s0),lerp(F[j],B[j],s1);b0,b1=lerp(F[j+step],B[j+step],s0),lerp(F[j+step],B[j+step],s1)
                m0,m1=lerp(a0,b0,0.5),lerp(a1,b1,0.5)
                quad(nm,[(a0[0],a0[1],ze),(m0[0],m0[1],zr),(m1[0],m1[1],zr),(a1[0],a1[1],ze)])
                quad(nm,[(m0[0],m0[1],zr),(b0[0],b0[1],ze),(b1[0],b1[1],ze),(m1[0],m1[1],zr)])
                quad(nm,[(a0[0],a0[1],ze),(b0[0],b0[1],ze),(m0[0],m0[1],zr)])
        elif k=='gable':
            # ["gable",mat,s0,s1,xa,za,xb,zb,zbase]: block whose roof height runs linearly in x
            _,nm,s0,s1,xa,za,xb,zb,zb0=op;T,F,B=S
            ks=[i for i,t in enumerate(T) if min(xa,xb)<=ell(t)[0]<=max(xa,xb)]
            hz=lambda x:za+(zb-za)*(x-xa)/(xb-xa)
            for i in range(min(ks),max(ks)):
                a0,a1=lerp(F[i],B[i],s0),lerp(F[i],B[i],s1);b0,b1=lerp(F[i+1],B[i+1],s0),lerp(F[i+1],B[i+1],s1)
                ha,hb=hz(ell(T[i])[0]),hz(ell(T[i+1])[0])
                quad(nm,[(a0[0],a0[1],ha),(b0[0],b0[1],hb),(b1[0],b1[1],hb),(a1[0],a1[1],ha)])
                quad(nm,[(a0[0],a0[1],zb0),(b0[0],b0[1],zb0),(b0[0],b0[1],hb),(a0[0],a0[1],ha)])
                quad(nm,[(a1[0],a1[1],zb0),(b1[0],b1[1],zb0),(b1[0],b1[1],hb),(a1[0],a1[1],ha)])
            for i in (min(ks),max(ks)):
                a0,a1=lerp(F[i],B[i],s0),lerp(F[i],B[i],s1);h=hz(ell(T[i])[0])
                quad(nm,[(a0[0],a0[1],zb0),(a1[0],a1[1],zb0),(a1[0],a1[1],h),(a0[0],a0[1],h)])
        elif k=='sub':
            _,lo,hi,ops=op;T,F,B=S;ks=[i for i,t in enumerate(T) if lo<=ell(t)[0]<=hi]
            if ks:
                a,b=min(ks),max(ks);S2=(T[a:b+1],F[a:b+1],B[a:b+1])
                for o in ops:
                    if o[0]=='loft':loft(o[1],S2,*o[2:])
                    elif o[0]=='wall':loft(o[1],S2,o[2],o[2],o[3],o[4])
                    elif o[0]=='ends':endwalls(o[1],S2,o[2])
# ground and boundary fence
G=[ell(2*math.pi*k/120,P.get('apron',3)) for k in range(120)]
G2=[ell(2*math.pi*k/120,0) for k in range(120)]
F1=[ell(2*math.pi*k/120,1.5) for k in range(120)]   # field left out (director 2026-11-18): grass only from the fence out to the apron
for k in range(120):
    j=(k+1)%120;quad('grass',[(F1[k][0],F1[k][1],0.0),(G[k][0],G[k][1],0.0),(G[j][0],G[j][1],0.0),(F1[j][0],F1[j][1],0.0)])
for k in range(120):
    a,b=ell(2*math.pi*k/120,1.5),ell(2*math.pi*(k+1)/120,1.5);quad('white',[(a[0],a[1],0),(b[0],b[1],0),(b[0],b[1],1.0),(a[0],a[1],1.0)])
for pt in P['parts']:build_part(pt)
exec(open(os.path.join(HERE,'north.py')).read());exec(open(os.path.join(HERE,'south.py')).read());SIGNS={};exec(open(os.path.join(HERE,'emu.py')).read());exec(open(os.path.join(HERE,'sb.py')).read())
for b in P.get('boxes',[]):
    if 'pts' in b:boxpts(b['m'],b['pts'],b['z0'],b['z1'],b.get('top'))
    else:box(b['m'],b['x'],b['y'],b['w'],b['d'],b['z0'],b['z1'],math.radians(b.get('ang',0)),b.get('top'))
for py in P.get('pyramids',[]):
    cx,cy=py['peak'];a=py['along'];nn=py['norm'];hw=py['hw']
    def pt(sa,sn,z):return (cx+a[0]*sa+nn[0]*sn,cy+a[1]*sa+nn[1]*sn,z)
    c=[pt(-hw,py['df'],py['ze']),pt(hw,py['df'],py['ze']),pt(hw,-py['db'],py['ze']),pt(-hw,-py['db'],py['ze'])]
    top=pt(0,0,py['zp'])
    for i in range(4):quad('tent',[c[i],c[(i+1)%4],top])
    f0,f1=c[0],c[1];quad('white',[(f0[0],f0[1],py['zf']),(f1[0],f1[1],py['zf']),(f1[0],f1[1],py['ze']),(f0[0],f0[1],py['ze'])])
def tower(x,y,H):
    n=16;r0,r1=P['tower_r']
    for i in range(n):
        a,b=2*math.pi*i/n,2*math.pi*(i+1)/n
        quad('white',[(x+r0*math.cos(a),y+r0*math.sin(a),0),(x+r0*math.cos(b),y+r0*math.sin(b),0),(x+r1*math.cos(b),y+r1*math.sin(b),H),(x+r1*math.cos(a),y+r1*math.sin(a),H)])
    ang=math.atan2(EC[1]-y,EC[0]-x);ux,uy=math.cos(ang),math.sin(ang);px,py=-uy,ux
    w,h,tilt,off0=P['head']
    tilt=math.radians(tilt)
    D=1.8;TI=len(SIGNS)
    def hp(a,v,o):return (x+px*a+ux*(off0+v*math.sin(tilt)+o),y+py*a+uy*(off0+v*math.sin(tilt)+o),H+v*math.cos(tilt))
    k='%d'%TI;bn,fn='headb_'+k,'headf_'+k
    quad(bn,[hp(-w/2,h,0),hp(w/2,h,0),hp(w/2,0,0),hp(-w/2,0,0)]);SIGNS[bn]=(hp(-w/2,0,0),(px,py),w,H,h*math.cos(tilt))   # wound to face out, away from the field
    quad(fn,[hp(-w/2,0,D),hp(w/2,0,D),hp(w/2,h,D),hp(-w/2,h,D)]);SIGNS[fn]=(hp(-w/2,0,D),(px,py),w,H,h*math.cos(tilt))
    for A,B in (((-w/2,0),(-w/2,h)),((w/2,0),(w/2,h)),((-w/2,h),(w/2,h)),((-w/2,0),(w/2,0))):
        q=[hp(A[0],A[1],0),hp(B[0],B[1],0),hp(B[0],B[1],D),hp(A[0],A[1],D)];cc=hp(0,h/2,D/2)
        e1=[q[1][i]-q[0][i] for i in range(3)];e2=[q[3][i]-q[0][i] for i in range(3)]
        nn=(e1[1]*e2[2]-e1[2]*e2[1],e1[2]*e2[0]-e1[0]*e2[2],e1[0]*e2[1]-e1[1]*e2[0])
        if sum(nn[i]*(q[0][i]-cc[i]) for i in range(3))<0:q=q[::-1]   # every side faces out
        quad('headside',q)
for k,x,y,Ht in P['towers']:tower(x,y,Ht)
for name,bm in OBJ.items():
    me=bpy.data.meshes.new(name);bm.to_mesh(me);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);
    if name.startswith('head'):ob.display.show_shadows=False   # open lattice: its own box must not shade its face
    me.materials.append(mat(name,C.get(name,(0.5,0.5,0.5))))
p=cam['p'];Cc=Vector(p[:3]);yaw,pitch,roll=p[3:6]
cy,sy,cp,sp,cr,sr=math.cos(yaw),math.sin(yaw),math.cos(pitch),math.sin(pitch),math.cos(roll),math.sin(roll)
f=Vector((cy*cp,sy*cp,sp));r=Vector((sy,-cy,0));u=r.cross(f)
ri=cr*r+sr*u;ui=-sr*r+cr*u
M=Matrix(((ri.x,ui.x,-f.x),(ri.y,ui.y,-f.y),(ri.z,ui.z,-f.z)))
cd=bpy.data.cameras.new('cam');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=p[6]*36/cam['W']
cd.shift_x=-(cam['cx']-cam['W']/2)/cam['W'];cd.shift_y=(cam['cy']-cam['Hh']/2)/cam['W'];cd.clip_end=5000
co=bpy.data.objects.new('cam',cd);co.matrix_world=Matrix.Translation(Cc)@M.to_4x4();bpy.context.collection.objects.link(co)
sc=bpy.context.scene;sc.camera=co;sc.render.resolution_x=cam['W'];sc.render.resolution_y=cam['Hh']
# ---- hand-made textures (tex.py), mapped in world metres; no photo pixels
def apply_tex():
    TD=os.path.join(HERE,'tex');SZ=json.load(open(os.path.join(TD,'size.json')))
    for ob in [o for o in bpy.context.collection.objects if o.type=='MESH']:
        nm=ob.name.split('.')[0]
        base=nm.split('_')[0]
        if base not in SZ:print('NO TEX',nm);continue
        m=ob.data.materials[0];nt=m.node_tree
        tn=nt.nodes.new('ShaderNodeTexImage');tn.image=bpy.data.images.load(os.path.join(TD,base+'.png'));tn.interpolation='Cubic';tn.extension='REPEAT'
        nt.links.new(tn.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);nt.nodes.active=tn
        S=SZ[base];bm=bmesh.new();bm.from_mesh(ob.data);uvl=bm.loops.layers.uv.new('UVMap');bm.normal_update()
        Z=Vector((0,0,1))
        if nm in SIGNS:
            o,dv,w,z0,h=SIGNS[nm]
            for fc in bm.faces:
                for lp in fc.loops:
                    p=lp.vert.co;lp[uvl].uv=(((p.x-o[0])*dv[0]+(p.y-o[1])*dv[1])/w,(p.z-z0)/h)
            bm.to_mesh(ob.data);bm.free();tn.extension='CLIP';continue
        for fc in bm.faces:
            n=fc.normal;t=Z.cross(n)
            t=Vector((1,0,0)) if t.length<1e-3 else t.normalized();bb=n.cross(t).normalized()
            if bb.z<0:bb=-bb
            for lp in fc.loops:
                p=lp.vert.co;lp[uvl].uv=(p.dot(t)/S,p.dot(bb)/S)
        bm.to_mesh(ob.data);bm.free()
if os.environ.get('WACA_TEX'):apply_tex()
if argv and argv[0]!='-':
    bpy.ops.export_scene.gltf(filepath=argv[0],export_format='GLB',export_cameras=False,export_lights=False)
if len(argv)>1:
    sc.render.engine='BLENDER_WORKBENCH';sc.view_settings.view_transform='Standard';sh=sc.display.shading;sh.light='FLAT';sh.color_type='TEXTURE' if os.environ.get('WACA_TEX') else 'MATERIAL';sh.show_shadows=True;sh.shadow_intensity=0.55;sc.display.light_direction=(0.35,0.45,0.82);sh.show_cavity=True
    sc.render.film_transparent=True;sc.render.filepath=argv[1];bpy.ops.render.render(write_still=True)
