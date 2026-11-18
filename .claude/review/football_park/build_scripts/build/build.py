# Football Park exterior builder. Blender: blender -b --python build.py -- SPEC.py OUT.glb [CAM.json RENDER.png W H]
# World frame: x = west, y = south, z = up, metres, origin = oval centre. Ring(t,d,z): fence ellipse 72.5 x 88.5 offset by d.
# Every face carries UVs: explicit (seat bays, roof bays, facade bays, lamp heads) or planar in metres / tile size.
# Textures: hand-made PNGs from tex.py in env TEXDIR (no photo pixels).
import bpy,bmesh,sys,math,json,os,importlib.util
from mathutils import Vector,Matrix
argv=sys.argv[sys.argv.index('--')+1:]
spec_path,out=argv[0],argv[1]
sp=importlib.util.spec_from_file_location('spec',spec_path);S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
bpy.ops.wm.read_factory_settings(use_empty=True)
TEXDIR=os.environ.get('TEXDIR','')
A0,B0=72.5,88.5
# planar tile sizes in metres (u,v) for materials without explicit UVs
TILE={'turf':(20,20),'apron':(8,8),'pink':(5,5),'deck':(6,6),'west_back':(4,8),'embank':(9,9),'glass':(3,6.5),'col':(2,2),
      'tower':(3,12),'admin':(14,12),'admin_roof':(12,12),'box':(10,10),'box_roof':(10,10),'screen':(20,10),'facade':(32,14),'tan':(8,8),'white':(8,8),
      'west_roof':(8,8),'tan_under':(6,6),'seat_lb':(11,0.8),'seat_navy':(11,0.8),'riser':(11,0.4),'riser_navy':(11,0.4),'lamps':(7,18),'signs':(40,1.1),'kerb':(1,1),'grass_n':(12,12),'grass_s':(12,12),'road':(8,8),'footpath':(4,4),'carpark':(5,5),'conc':(4,4),'golf':(12,12),'road_top':(8,8),'road_diag':(8,8),'nw_roof':(1,1)}
# ---- seat aisles: 47 equal-arc bays (fitted to the white aisle lines in photo B), phase 0.77
_N=36000;_ts=[360*i/_N for i in range(_N+1)];_s=[0.0]
for i in range(1,_N+1):
    a,b=math.radians(_ts[i-1]),math.radians(_ts[i]);_s.append(_s[-1]+math.hypot(A0*(math.cos(b)-math.cos(a)),B0*(math.sin(b)-math.sin(a))))
_L=_s[-1]
def bay(t):
    t=t%360;i=min(_N-1,int(t/360*_N));f=t/360*_N-i;return (_s[i]+(_s[i+1]-_s[i])*f)/_L*getattr(S,'AISLES',47)-getattr(S,'AISLE_PH',0.77)
def ring(t,d,z):
    r=math.radians(t);return Vector(((A0+d)*math.cos(r),(B0+d)*math.sin(r),z))
def tang(t):
    r=math.radians(t);v=Vector((-(A0)*math.sin(r),B0*math.cos(r),0));return v.normalized()
MATS={}
def mat(name):
    if name in MATS:return MATS[name]
    c=S.COL.get(name,(200,200,200));m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree;b=nt.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(*[(x/255)**2.2 for x in c],1)
    b.inputs['Roughness'].default_value={'glass':0.15,'screen':0.3,'col':0.5,'white':0.55}.get(name,0.85)
    png=os.path.join(TEXDIR,name+'.png') if TEXDIR else ''
    if png and os.path.exists(png):
        tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(png);tx.interpolation='Cubic'
        nt.links.new(tx.outputs['Color'],b.inputs['Base Color'])
        px=list(tx.image.pixels[:4*4096:4*97]);m.diffuse_color=(0.6,0.6,0.6,1)
    else:m.diffuse_color=(*[(x/255)**2.2 for x in c],1)
    MATS[name]=m;return m
objs={}
def bm_for(name):
    if name not in objs:
        bm=bmesh.new();bm.loops.layers.uv.verify();objs[name]=bm
    return objs[name]
def auto_uv(name,pts):
    if name=='turf':return [((p.x+A0)/(2*A0),1-(p.y+B0)/(2*B0)) for p in pts]
    tu,tv=TILE.get(name,(4,4));n=(pts[1]-pts[0]).cross(pts[-1]-pts[0])
    if n.length<1e-9 and len(pts)>3:n=(pts[2]-pts[1]).cross(pts[0]-pts[1])
    if n.length<1e-9:return [(0,0)]*len(pts)
    n.normalize()
    if abs(n.z)>0.7:return [(p.x/tu,p.y/tv) for p in pts]
    h=n.cross(Vector((0,0,1))).normalized();return [(p.dot(h)/tu,p.z/tv) for p in pts]
def face(name,pts,uv=None):
    pts=[Vector(p) for p in pts]
    # drop degenerate faces
    if len(pts)>=3 and all((pts[i]-pts[(i+1)%len(pts)]).length<1e-4 for i in range(len(pts))):return
    bm=bm_for(name);vs=[bm.verts.new(p) for p in pts]
    try:f=bm.faces.new(vs)
    except ValueError:return
    uvl=bm.loops.layers.uv.active;uv=uv or auto_uv(name,pts)
    for lp,(u,v) in zip(f.loops,uv):lp[uvl].uv=(u,v)
def quad(name,a,b,c,d,uv=None):
    if ((b-a).cross(d-a)).length<1e-7 and ((c-b).cross(d-b)).length<1e-7:return
    face(name,[a,b,c,d],uv)
def tri(name,a,b,c,uv=None):face(name,[a,b,c],uv)
def interp(keys,t):
    ks=sorted(keys,key=lambda k:k[0]);t=t%360
    for i in range(len(ks)):
        t0,v0=ks[i];t1,v1=ks[(i+1)%len(ks)]
        span=(t1-t0)%360 or 360;dt=(t-t0)%360
        if dt<=span:
            w=dt/span;return [a+(b-a)*w for a,b in zip(v0,v1)]
    return ks[0][1]
def tsteps(t0,t1,step=1.0):
    span=(t1-t0)%360 or 360;n=max(1,int(math.ceil(span/step)));return [t0+span*i/n for i in range(n+1)]
# ---- seat tier as real steps: rows every ROW m of run (shared edges identical, so no cracks)
ROW=getattr(S,'ROW',0.8)
def rows(d0,z0,d1,z1):
    run=d1-d0;n=max(1,int(run/ROW));ds=[d0+ROW*i for i in range(n+1)]
    if d1-ds[-1]>0.05:ds.append(d1)
    else:ds[-1]=d1
    return [(d,z0+(z1-z0)*(d-d0)/run) for d in ds]
def seats(mname,ta,tb,pa0,pa1,pb0,pb1):
    # both ends get the same row count, spread evenly, so every riser and tread runs unbroken from one end to the other
    n=max(len(rows(*pa0,*pa1)),len(rows(*pb0,*pb1)))
    def even(p0,p1):return [(p0[0]+(p1[0]-p0[0])*i/(n-1),p0[1]+(p1[1]-p0[1])*i/(n-1)) for i in range(n)]
    ra=even(pa0,pa1);rb=even(pb0,pb1)
    ua,ub=bay(ta),bay(tb)
    if ub<ua:ub+=getattr(S,'AISLES',47)
    for i in range(n-1):
        (da,za),(da2,za2)=ra[i],ra[i+1];(db,zb),(db2,zb2)=rb[i],rb[i+1]
        # riser (vertical, at row front) then tread
        quad('riser' if mname=='seat_lb' else 'riser_navy',ring(ta,da,za),ring(ta,da,za2),ring(tb,db,zb2),ring(tb,db,zb),uv=[(ua,0),(ua,1),(ub,1),(ub,0)])
        quad(mname,ring(ta,da,za2),ring(ta,da2,za2),ring(tb,db2,zb2),ring(tb,db,zb2),uv=[(ua,0),(ua,1),(ub,1),(ub,0)])
# ---- bowl: closed loop of profiles (list of (d,z) flattened), materials per segment by sector
def bowl():
    ts=tsteps(0,360,0.5)
    fb=getattr(S,'FACADE_BAY',3.0)
    for i in range(len(ts)-1):
        ta,tb=ts[i],ts[i+1];pa=interp(S.BOWL,ta);pb=interp(S.BOWL,tb);tm=(ta+tb)/2
        mats=S.bowl_mats(tm%360)
        # fence / advertising band: vertical at d 0 from the turf up to the walkway
        quad('signs',ring(ta,0,0),ring(tb,0,0),ring(tb,0,pb[1]),ring(ta,0,pa[1]),uv=[(ta/360*40,0),(tb/360*40,0),(tb/360*40,1),(ta/360*40,1)])
        for k in range(len(pa)//2-1):
            a=ring(ta,pa[2*k],pa[2*k+1]);b=ring(ta,pa[2*k+2],pa[2*k+3]);c=ring(tb,pb[2*k+2],pb[2*k+3]);d=ring(tb,pb[2*k],pb[2*k+1])
            if (a-b).length<1e-3 and (c-d).length<1e-3:continue
            m=mats[k]
            if m.startswith('seat'):
                seats(m,ta,tb,(pa[2*k],pa[2*k+1]),(pa[2*k+2],pa[2*k+3]),(pb[2*k],pb[2*k+1]),(pb[2*k+2],pb[2*k+3]));continue
            if m=='facade':
                # v = height / the wall top at that vertex's own bearing: a shared edge gets the same UVs from both sides, so the bands meet
                za=max(a.z,b.z) or 1;zb=max(c.z,d.z) or 1;q=fb*4;quad(m,a,b,c,d,uv=[(ta/q,a.z/za),(ta/q,b.z/za),(tb/q,c.z/zb),(tb/q,d.z/zb)]);continue
            quad(m,a,b,c,d)
# ---- lofted strips (roofs): u = bays along t (S strip 'bay' degrees), v = 0 inner .. 1 outer
def strip(st):
    ts=tsteps(st['t0'],st['t1'],st.get('step',0.5));th=st.get('thick',0.0);m=st['mat'];mu=st.get('mat_under',m)
    keys=st['keys'];bd=st.get('bay',4.0);t0=st['t0']
    def P(t):return interp(keys,t) if len(keys)>1 else keys[0][1]
    for i in range(len(ts)-1):
        ta,tb=ts[i],ts[i+1];pa=P(ta);pb=P(tb);ua=((ta-t0)%360)/bd;ub=((tb-t0)%360)/bd
        if ub<ua:ub+=360/bd
        a=ring(ta,pa[0],pa[1]);b=ring(ta,pa[2],pa[3]);c=ring(tb,pb[2],pb[3]);d=ring(tb,pb[0],pb[1])
        quad(m,a,b,c,d,uv=[(ua,0),(ua,1),(ub,1),(ub,0)])
        if th>0:
            dz=Vector((0,0,th));quad(mu,a-dz,d-dz,c-dz,b-dz,uv=[(ua,0),(ub,0),(ub,1),(ua,1)])
            quad(st.get('mat_edge',m),a,d,d-dz,a-dz);quad(st.get('mat_edge',m),b-dz,c-dz,c,b)
    if th>0:
        for t in (ts[0],ts[-1]):
            p=P(t);a=ring(t,p[0],p[1]);b=ring(t,p[2],p[3]);dz=Vector((0,0,th));quad(st.get('mat_edge',m),a,b,b-dz,a-dz)
# ---- walls: vertical band at keyed d between z0..z1 (keys (t,[d,z0,z1]))
def wall(st):
    ts=tsteps(st['t0'],st['t1'],st.get('step',0.5));keys=st['keys']
    def P(t):return interp(keys,t) if len(keys)>1 else keys[0][1]
    for i in range(len(ts)-1):
        ta,tb=ts[i],ts[i+1];pa=P(ta);pb=P(tb)
        quad(st['mat'],ring(ta,pa[0],pa[1]),ring(tb,pb[0],pb[1]),ring(tb,pb[0],pb[2]),ring(ta,pa[0],pa[2]))
def endwall(e):face(e['mat'],[ring(e['t'],d,z) for d,z in e['poly']])
def cyl(name,base,top,r0,r1,n=8,tile=None):
    ax=(top-base);up=ax.normalized();side=up.orthogonal().normalized();s2=up.cross(side)
    tu,tv=tile or TILE.get(name,(2,2));L=ax.length;lo=[];hi=[]
    for i in range(n):
        a=2*math.pi*i/n;o=side*math.cos(a)+s2*math.sin(a);lo.append(base+o*r0);hi.append(top+o*r1)
    circ=2*math.pi*r0
    for i in range(n):
        j=(i+1)%n;u0=circ*i/n/tu;u1=circ*(i+1)/n/tu
        quad(name,lo[i],lo[j],hi[j],hi[i],uv=[(u0,0),(u1,0),(u1,L/tv),(u0,L/tv)])
    face(name,list(reversed(lo)));face(name,hi)
def columns(c):
    span=(c['t1']-c['t0'])%360;n=int(span/c['step'])
    for i in range(n+1):
        tt=c['t0']+span*i/max(n,1);cyl(c['mat'],ring(tt,c['d'],c['z0']),ring(tt,c['d'],c['z1']),c['r'],c['r'])
def box(b):
    t=b['t'];c=ring(t,b['d'],0);tg=tang(t);rd=Vector((tg.y,-tg.x,0))
    if rd.dot(c)<0:rd=-rd
    w,dp=b['w']/2,b['dep']/2;z0,z1=b['z0'],b['z1']
    if 'yaw' in b:
        a=math.radians(b['yaw']);tg=Vector((math.cos(a),math.sin(a),0));rd=Vector((-tg.y,tg.x,0))
    P=lambda s,r,z:c+tg*(s*w)+rd*(r*dp)+Vector((0,0,z))
    m=b['mat'];mt=b.get('mat_top',m);mf=b.get('mat_front',m)
    quad(mt,P(-1,-1,z1),P(1,-1,z1),P(1,1,z1),P(-1,1,z1))
    if mf=='screen':quad(mf,P(-1,-1,z0),P(1,-1,z0),P(1,-1,z1),P(-1,-1,z1),uv=[(0,0),(1,0),(1,1),(0,1)])
    else:quad(mf,P(-1,-1,z0),P(1,-1,z0),P(1,-1,z1),P(-1,-1,z1))
    quad(m,P(1,1,z0),P(-1,1,z0),P(-1,1,z1),P(1,1,z1))
    quad(m,P(1,-1,z0),P(1,1,z0),P(1,1,z1),P(1,-1,z1))
    quad(m,P(-1,1,z0),P(-1,-1,z0),P(-1,-1,z1),P(-1,1,z1))
# ---- light towers: tapered shaft + lamp head (lamp grid on the face towards the centre)
def tower(x,y):
    T=S.TOWER;H=T['H'];hh=T['head_h']/2;hw=T['head_w']/2
    cyl('tower',Vector((x,y,0)),Vector((x,y,H-T['head_h'])),T['r0'],T['r1'],16)
    to=Vector((-x,-y,0)).normalized();sd=Vector((-to.y,to.x,0));c=Vector((x,y,H-hh))
    up=Vector((0,0,1))*math.cos(math.radians(T['tilt']))+to*math.sin(math.radians(T['tilt']));dp=to*T.get('head_d',1.0)
    P=lambda s,u,f:c+sd*(s*hw)+up*(u*hh)+dp*f
    quad('lamps',P(-1,-1,1),P(1,-1,1),P(1,1,1),P(-1,1,1),uv=[(0,0),(1,0),(1,1),(0,1)])
    quad('tower',P(1,-1,0),P(-1,-1,0),P(-1,1,0),P(1,1,0))
    quad('tower',P(-1,1,0),P(-1,1,1),P(1,1,1),P(1,1,0));quad('tower',P(-1,-1,0),P(1,-1,0),P(1,-1,1),P(-1,-1,1))
    quad('tower',P(-1,-1,0),P(-1,-1,1),P(-1,1,1),P(-1,1,0));quad('tower',P(1,-1,0),P(1,1,0),P(1,1,1),P(1,-1,1))
def goals():
    gp=S.GOALS if hasattr(S,'GOALS') else dict(inset=3.0,gh=12.0,bh=6.5,r=0.25)
    for sg in(-1,1):
        y=sg*(B0-gp['inset'])
        for x,h in((-9.6,gp['bh']),(-3.2,gp['gh']),(3.2,gp['gh']),(9.6,gp['bh'])):
            cyl('posts',Vector((x,y,0)),Vector((x,y,h)),gp['r'],gp['r']*0.7,10,tile=(1,1))
            cyl('padding',Vector((x,y,0)),Vector((x,y,2.0)),gp['r']+0.12,gp['r']+0.12,10,tile=(1,2))
def lin_k(ks,t):
    ks=sorted(ks)
    if t<=ks[0][0]:return ks[0][1]
    if t>=ks[-1][0]:return ks[-1][1]
    for (a,da),(b,db) in zip(ks,ks[1:]):
        if a<=t<=b:return da+(db-da)*(t-a)/(b-a)
def kerbline(pts,h=0.15,w=0.3,m='kerb',closed=False):
    pts=[Vector(p) for p in pts];n=len(pts);up=Vector((0,0,h))
    for i in range(n if closed else n-1):
        a=pts[i];b=pts[(i+1)%n];tg=(b-a);tg.z=0
        if tg.length<1e-6:continue
        nr=Vector((-tg.y,tg.x,0)).normalized()*w
        quad(m,a,b,b+up,a+up);quad(m,b+nr,a+nr,a+nr+up,b+nr+up);quad(m,a+up,b+up,b+nr+up,a+nr+up)
def road(m,pts,w,z=-0.06,kerb=True):
    pts=[Vector((p[0],p[1],z)) for p in pts];L=[];R=[]
    for i,p in enumerate(pts):
        a=pts[max(i-1,0)];b=pts[min(i+1,len(pts)-1)];tg=(b-a);tg.z=0;tg.normalize();nr=Vector((-tg.y,tg.x,0))
        L.append(p+nr*w/2);R.append(p-nr*w/2)
    for i in range(len(pts)-1):quad(m,R[i],R[i+1],L[i+1],L[i])
    if kerb:kerbline(list(reversed(L)));kerbline(R)
def ground():
    for t0,t1,m,kin,kout in getattr(S,'APRONK',[]):
        span=(t1-t0)%360 or 360;n=int(span);tt=[t0+span*i/n for i in range(n+1)];out=[]
        def uw(t):return t if t>=t0 else t+360
        for ta,tb in zip(tt,tt[1:]):
            ia,ib=lin_k(kin,ta%360),lin_k(kin,tb%360);oa,ob=lin_k(kout,ta%360),lin_k(kout,tb%360)
            quad(m,ring(ta,ia,-0.05),ring(ta,oa,-0.05),ring(tb,ob,-0.05),ring(tb,ib,-0.05))
        out=[ring(t,lin_k(kout,t%360),-0.05) for t in tt]
        if getattr(S,'KERB',True):kerbline(list(reversed(out)) if False else out)
    for m,pts,w in getattr(S,'ROADS',[]):road(m,pts,w)
    for t0,t1,d0,d1,m in S.APRON:
        for ta in tsteps(t0,t1,1.0)[:-1]:
            tb=ta+1.0;quad(m,ring(ta,d0,-0.05),ring(ta,d1,-0.05),ring(tb,d1,-0.05),ring(tb,d0,-0.05))
def prism(pr):
    top=[Vector(p) for p in pr['top']];bot=[Vector(p) for p in pr['bot']];n=len(top)
    if pr.get('uv_box'):
        xs=[p.x for p in top];ys=[p.y for p in top];x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
        face(pr.get('mat_top',pr['mat']),top,uv=[((p.x-x0)/(x1-x0),(p.y-y0)/(y1-y0)) for p in top])
    else:face(pr.get('mat_top',pr['mat']),top)
    for i in range(n):
        j=(i+1)%n;quad(pr['mat'],bot[i],bot[j],top[j],top[i])
def polys():
    for name,pts,z in getattr(S,'GROUNDPOLY',[]):face(name,[(x,y,z) for x,y in pts])
ground();bowl();polys()
for s in S.STRIPS:strip(s)
for w in S.WALLS:wall(w)
for e in getattr(S,'ENDS',[]):endwall(e)
for c in S.COLUMNS:columns(c)
for b in S.BOXES:box(b)
for pr in getattr(S,'PRISMS',[]):prism(pr)
for k,(x,y) in S.TOWERS.items():tower(x,y)
for name,bm in objs.items():
    me=bpy.data.meshes.new(name);bm.to_mesh(me);ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);me.materials.append(mat(name))
    for pl in me.polygons:pl.use_smooth=False
for m in MATS.values():m.use_backface_culling=False
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_yup=True)
print('FACES',sum(len(b.faces) for b in objs.values()))
def setcam(sc,p,W,H):
    cd=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cd);sc.collection.objects.link(co);sc.camera=co
    yaw,pit,rol=p[3:6];cy_,sy_=math.cos(yaw),math.sin(yaw);cp,spn=math.cos(pit),math.sin(pit)
    f=Vector((cy_*cp,sy_*cp,spn));r=Vector((sy_,-cy_,0));u=r.cross(f);cr,sr=math.cos(rol),math.sin(rol)
    r2=r*cr+u*sr;u2=-r*sr+u*cr
    M=Matrix(((r2.x,u2.x,-f.x),(r2.y,u2.y,-f.y),(r2.z,u2.z,-f.z)))
    co.matrix_world=Matrix.Translation(Vector(p[:3]))@M.to_4x4()
    cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=p[6]*36/W;mx=max(W,H)
    cd.shift_x=(W/2-p[7])/mx;cd.shift_y=(p[8]-H/2)/mx;cd.clip_end=5000;cd.clip_start=0.5
    return co,cd
if len(argv)>2:
    cam=json.load(open(argv[2]));W,H=int(argv[4]),int(argv[5])
    sc=bpy.context.scene;sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=int(os.environ.get('PCT','100'))
    sc.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    sun=bpy.data.lights.new('sun','SUN');sun.energy=S.SUN.get('energy',4.0);sun.angle=math.radians(1.0);so=bpy.data.objects.new('sun',sun);sc.collection.objects.link(so)
    so.rotation_euler=Vector(S.SUN['dir']).to_track_quat('-Z','Y').to_euler()
    w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.45,0.5,0.55,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.9
    sc.render.film_transparent=True;sc.view_settings.view_transform='Standard'
    if os.environ.get('FAST','0') not in ('','0'):
        sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE'
    shots=[]
    if 'p' in cam:shots.append((cam['p'],W,H,argv[3]))
    for s in cam.get('shots',[]):shots.append((s['p'],s['W'],s['H'],s['out']))
    for p,w_,h_,o in shots:
        sc.render.resolution_x=w_;sc.render.resolution_y=h_;co,cd=setcam(sc,p,w_,h_)
        bd=os.environ.get('BORDER','')
        if bd:
            x0,y0,x1,y1=[float(v) for v in bd.split(',')];sc.render.use_border=True;sc.render.use_crop_to_border=True
            sc.render.border_min_x=x0;sc.render.border_max_x=x1;sc.render.border_min_y=1-y1;sc.render.border_max_y=1-y0
        sc.render.filepath=os.path.abspath(o);bpy.ops.render.render(write_still=True)
