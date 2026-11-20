# Subiaco Oval 1997 (version B), built in world metres (x east, y north, z up) from photo refs/c/17.jpg through
# the fitted camera camB.json; all positions from measureA.py -> layoutA.json. Hand-made textures in tex/.
#   blender -b --python buildA.py -- SPDIR OUT.glb RENDER.png
import bpy,bmesh,sys,math,json
import numpy as np
from mathutils import Vector,Matrix
SP,OUT,REN=sys.argv[sys.argv.index('--')+1:]
J=json.load(open(SP+'/layoutA.json'));C0=J['C0'];FJ=J['fence'];co=FJ['co'];K=FJ['K'];RK=J['RAKE']
def rf(a):
    t=math.radians(a);return sum(co[k]*math.cos(k*t) for k in range(K+1))+sum(co[K+k]*math.sin(k*t) for k in range(1,K+1))
def P(a,d,z):
    r=rf(a)+d;t=math.radians(a);return Vector((C0[0]+r*math.cos(t),C0[1]+r*math.sin(t),z))
def unwrap(a,ref):
    while a<ref-180:a+=360
    while a>ref+180:a-=360
    return a
def fn(samples,col,ref):
    S=sorted((unwrap(s[0],ref),s[col]) for s in samples);A=[s[0] for s in S];D=[s[1] for s in S]
    return lambda a:float(np.interp(unwrap(a,ref),A,D))
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('subiacoB');ob=bpy.data.objects.new('subiacoB',me);bpy.context.scene.collection.objects.link(ob)
MI={}
def mat(name,rough=0.85):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(SP+'/tex/'+name+'.png')
    nt.links.new(t.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough
    import colorsys;m.diffuse_color=(*colorsys.hsv_to_rgb((len(MI)*0.618)%1,0.6,0.9),1);me.materials.append(m);MI[name]=len(me.materials)-1
for n in('turf','paint','terrace','seats','roof','roofd','wall','brick','under','fascia','asphalt','paving','picket','steel','can','glass','seatsb','facade','pad','bank','ads','lamps','facaded'):mat(n)
bm=bmesh.new();uv=bm.loops.layers.uv.new()
def face(vs,m,uvs=None):
    if uvs is None:uvs=[(0,0),(1,0),(1,1),(0,1)]+[(0,0)]*max(0,len(vs)-4)
    f=bm.faces.new([bm.verts.new(v) for v in vs]);f.material_index=MI[m]
    for l,q in zip(f.loops,uvs):l[uv].uv=q
    return f
def angles(a0,a1,step=1.0):
    n=max(1,int(round(abs(a1-a0)/step)));return [a0+(a1-a0)*i/n for i in range(n+1)]
def sweep(a0,a1,prof,mats,tile=4.0,step=1.0):
    A=angles(a0,a1,step);cols=[[P(a,d,z) for d,z in prof(a)] for a in A];u=0.0
    for i in range(len(A)-1):
        c0,c1=cols[i],cols[i+1];du=(c1[0]-c0[0]).length/tile
        for k in range(len(c0)-1):
            if mats[k] is None:continue
            l=(c0[k+1]-c0[k]).length/tile
            face([c0[k],c1[k],c1[k+1],c0[k+1]],mats[k],[(u,0),(u+du,0),(u+du,l),(u,l)])
        u+=du
def endcap(a,prof,m):
    pts=[P(a,d,z) for d,z in prof(a)]
    if len(pts)>=3:
        try:face(pts,m,[(i/len(pts),0) for i in range(len(pts))])
        except ValueError:pass
# ---------------- field
A=angles(-180,180,1.5);tc=Vector((C0[0],C0[1],0.0))
for i in range(len(A)-1):
    continue  # director 2026-11-18 'Leave field out': no turf, the game draws its own grass
    pa,pb=P(A[i],0,0),P(A[i+1],0,0);face([tc,pa,pb],'turf',[((q.x-C0[0])/32,(q.y-C0[1])/32) for q in(tc,pa,pb)])
Uv=Vector((J['U'][0],J['U'][1],0));Vv=Vector((-Uv.y,Uv.x,0));Cc=Vector((C0[0],C0[1],0));Lg=J['L']
def line(p0,p1,w=0.12,z=0.04):
    d=(p1-p0);n=Vector((-d.y,d.x,0)).normalized()*w;Z=Vector((0,0,z))
    return  # field markings belong to the field, left out with it
def poly(pts,closed=False,w=0.12):
    for i in range(len(pts)-(0 if closed else 1)):line(pts[i],pts[(i+1)%len(pts)],w)
au=math.degrees(math.atan2(Uv.y,Uv.x))
def gap(a):c=abs(math.cos(math.radians(a-au)));return 4.5+3.3*c**6
def angof(p):q=p-Cc;return math.degrees(math.atan2(q.y,q.x))
poly([P(a,-gap(a),0) for a in angles(-180,180,2)],True,0.1)                  # boundary line through both goal lines
sq=[Cc+Uv*sx*22.5+Vv*sy*22.5 for sx,sy in((1,1),(1,-1),(-1,-1),(-1,1))];poly(sq,True)   # 45 m centre square (pre-2004)
for r in(1.5,5.0):poly([Cc+Uv*r*math.cos(t)+Vv*r*math.sin(t) for t in np.linspace(0,2*math.pi,40)],True)
line(Cc+Uv*-2.0,Cc+Uv*2.0)
for s in(1,-1):
    g=Cc+Uv*s*Lg
    pts=[g+(Uv*math.cos(t)+Vv*math.sin(t))*50 for t in np.linspace(0,2*math.pi,360)]
    ins=[p for p in pts if (p-Cc).length<rf(angof(p))-gap(angof(p))-0.3 and (p-Cc).dot(Uv)*s<Lg]
    ins.sort(key=lambda p:math.atan2((p-g).dot(Vv),-(p-g).dot(Uv)*s));poly(ins)
    poly([g+Vv*3.2,g+Vv*3.2-Uv*s*9,g-Vv*3.2-Uv*s*9,g-Vv*3.2])                        # goal square 6.4 x 9
    for k,h in((-9.6,10.0),(-3.2,15.0),(3.2,15.0),(9.6,10.0)):                          # goal and behind posts
        continue  # director 2026-11-18 'Posts out': the game draws its own posts
        b=g+Vv*k;n=8
        for j in range(n):
            t0=2*math.pi*j/n;t1=2*math.pi*(j+1)/n;o0=Vector((math.cos(t0),math.sin(t0),0))*0.15;o1=Vector((math.cos(t1),math.sin(t1),0))*0.15
            face([b+o0,b+o1,b+o1+Vector((0,0,h)),b+o0+Vector((0,0,h))],'fascia')
# picket fence on the fence line
sweep(-180,180,lambda a:[(0,0),(0,1.1)],['picket'],tile=2.0)
# ================= 1997 (version B) parts, all from layoutB.json (measured on refs/c/17.jpg through camB.json)
JB=json.load(open(SP+'/layoutB.json'))
def fD(S,ref):return fn(S,1,ref)
def fZ(S,ref):return fn(S,2,ref)
def fP(S,col,ref,deg=3):
    A_=np.array([unwrap(s[0],ref) for s in S]);V_=np.array([s[col] for s in S]);c=np.polyfit(A_,V_,min(deg,len(S)-1));lo,hi=A_.min(),A_.max()
    return lambda a:float(np.polyval(c,min(max(unwrap(a,ref),lo),hi)))
def block(pts,z1,wallm='wall',roofm='roof',z0=0.0):
    V=[P(a,d,z0) for a,d,*_ in pts];T=[P(a,d,z1) for a,d,*_ in pts];n=len(V)
    for i in range(n):face([V[i],V[(i+1)%n],T[(i+1)%n],T[i]],wallm,[(0,0),(1,0),(1,z1/4),(0,z1/4)])
    try:face(T,roofm,[((q.x)/8,(q.y)/8) for q in T])
    except ValueError:pass
def tube(b,h,r0,r1,m='steel',n=10):
    for j in range(n):
        t0=2*math.pi*j/n;t1=2*math.pi*(j+1)/n;c0=Vector((math.cos(t0),math.sin(t0),0));c1=Vector((math.cos(t1),math.sin(t1),0))
        face([b+c0*r0,b+c1*r0,b+c1*r1+Vector((0,0,h)),b+c0*r1+Vector((0,0,h))],m)
# ---- near bowl (south and near side, under one long roof): front rows from the fence, roof measured on both edges
SF=[[a,max(d,0.5),z] for a,d,z in JB['SF']];SB=JB['SB']
sfd,sfz,sbd,sbz=fP(SF,1,-70),fP(SF,2,-70),fP(SB,1,-70),fP(SB,2,-70)
def nb_prof(a):
    dF,zF,dB,zB=sfd(a),sfz(a),sbd(a),sbz(a)
    return [(0,0),(0,1.2),(0.8,1.2),(dB-1.0,zB-4.0),(dB,zB),(dF,zF),(dF,zF-1.0)]
NBM=['wall','fascia','seatsb','wall',None,'fascia']
sweep(-141.4,-4.3,nb_prof,NBM,tile=4)
sweep(-141.4,-95,lambda a:nb_prof(a)[4:6],['roof'],tile=4);sweep(-95,-4.3,lambda a:nb_prof(a)[4:6],['roofd'],tile=4)
sweep(-141.4,-4.3,lambda a:[(sbd(a),0),(sbd(a),sbz(a))],['facaded'],tile=16)
endcap(-141.4,lambda a:[(0,0),(sbd(a),0),(sbd(a),sbz(a)),(sfd(a),sfz(a)),(0,1.2)],'wall')
# ---- near-right stand: concrete multi-storey block with a dark flat roof
NRF,NRB=JB['NRF'],JB['NRB'];nfd,nfz,nbd=fD(NRF,10),fZ(NRF,10),fD(NRB,10)
def nr_prof(a):dF,z=nfd(a),nfz(a);dB=max(nbd(a),dF+8);return [(0,0),(0,1.2),(0.8,1.2),(dB-1,z-4),(dB,z),(dF,z),(dF,z-1.0)]
sweep(-4.3,33.2,nr_prof,['wall','fascia','seatsb','wall','roofd','fascia'],tile=4)
sweep(-4.3,33.2,lambda a:[(nr_prof(a)[4][0],0),nr_prof(a)[4]],['facade'],tile=16)
endcap(-4.3,lambda a:[(0,0),(nr_prof(a)[4][0],0),nr_prof(a)[4],nr_prof(a)[5],(0,1.2)],'wall')
endcap(-4.3,lambda a:[(0,0),(sbd(a),0),(sbd(a),sbz(a)),(sfd(a),sfz(a)),(0,1.2)],'wall')
endcap(33.2,lambda a:[(0,0),(nr_prof(a)[4][0],0),nr_prof(a)[4],nr_prof(a)[5],(0,1.2)],'wall')
# ---- north stand: blue seats raked from the fence up under a white roof (east end under the grey corner roof)
BF=JB['BF'];BB=JB['BB'];bfd,bfz,bbd,bbz=fP(BF,1,100),fP(BF,2,100),fP(BB,1,100),fP(BB,2,100)
def bs_prof(a):dF,zF,dB,zB=bfd(a),bfz(a),bbd(a),bbz(a);return [(0,0),(0,1.2),(0.8,1.2),(dF,zF-1.2),(dB-0.5,zF-1.2),(dB,zB),(dF,zF),(dF,zF-1.0)]
sweep(33.2,136.0,bs_prof,['wall','fascia','seatsb','under','wall',None,'fascia'],tile=4)
sweep(62.3,136.0,lambda a:bs_prof(a)[5:7],['roof'],tile=4)
sweep(33.2,136.0,lambda a:[(bbd(a),0),(bbd(a),bbz(a))],['wall'],tile=4)
endcap(136.0,lambda a:[(0,0),(bbd(a),0),(bbd(a),bbz(a)),(bfd(a),bfz(a)),(0,1.2)],'wall')
block([p for p in JB['CR']],18.0,'wall','steel')                                              # grey corner roof block
# ---- west end under construction: bare lit pad, grass bank, perimeter boards
W1,W2=JB['W1'],JB['W2'];w1d,w2d=fD(W1,170),fD(W2,170)
sweep(136.0,196.0,lambda a:[(0.1,0.05),(w1d(a),0.3)],['pad'],tile=12)
sweep(136.0,196.0,lambda a:[(w1d(a),0.3),(w2d(a),3.0)],['bank'],tile=8)
sweep(142.0,192.0,lambda a:[(w2d(a),3.0),(w2d(a),5.4)],['wall'],tile=24)
sweep(196.0,218.6,lambda a:[(0.1,0.05),(w1d(a)*0.9,0.3)],['pad'],tile=12)                 # SW corner pad to the near roof
block(JB['LW'],8.0,'wall','roof');block(JB['FL1'],8.0,'brick','roofd');block(JB['FL2'],5.0,'wall','roofd')
block(JB['GB'],10.0,'wall','steel')
# ---- four light towers: tapered (thicker at the base), lamp head facing the centre
for x,y,h in JB['TOW']:
    b=Vector((x,y,0));tube(b,h-3.0,0.9,0.45,'steel',12)
    c=Vector((x,y,h-3.0));t=(Cc-c);t.z=0;t.normalize();s=Vector((-t.y,t.x,0))*3.2;up=Vector((0,0,3.0))+t*0.6
    face([c-s,c+s,c+s+up*2,c-s+up*2],'lamps',[(0,0),(1,0),(1,1),(0,1)]);face([c-s-t*0.4,c-s-t*0.4+up*2,c+s-t*0.4+up*2,c+s-t*0.4],'steel')

# ---------------- matched-camera render
def render(cf,W,H,out,geo=False):
    Jc=json.load(open(SP+'/'+cf));cam=Jc['p']
    cy_,sy_=math.cos(cam[3]),math.sin(cam[3]);cp,sp=math.cos(cam[4]),math.sin(cam[4]);cr,sr=math.cos(cam[5]),math.sin(cam[5])
    f=Vector((cy_*cp,sy_*cp,sp));r=Vector((sy_,-cy_,0));u=r.cross(f);R0=r*cr+u*sr;R1=-r*sr+u*cr
    cd=bpy.data.cameras.new('c');co_=bpy.data.objects.new('c',cd);bpy.context.scene.collection.objects.link(co_)
    co_.matrix_world=Matrix(((R0.x,R1.x,-f.x,cam[0]),(R0.y,R1.y,-f.y,cam[1]),(R0.z,R1.z,-f.z,cam[2]),(0,0,0,1)))
    cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=cam[6]/W*36;cd.shift_x=0;cd.shift_y=0
    cd.clip_end=20000;sc_=bpy.context.scene;sc_.camera=co_
    sc_.render.engine='BLENDER_WORKBENCH';sc_.display.shading.color_type='MATERIAL' if geo else 'TEXTURE';sc_.display.shading.light='STUDIO'
    sc_.render.resolution_x=W;sc_.render.resolution_y=H;sc_.render.film_transparent=True;sc_.render.filepath=out
    bpy.ops.render.render(write_still=True)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-4);bm.normal_update();bm.to_mesh(me);bm.free()
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',use_selection=False)
render('camB.json',1000,600,REN.replace('.png','_geo.png'),True)
render('camB.json',1000,600,REN)
