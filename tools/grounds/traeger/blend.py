# blender -b --python blend.py -- prims.json cam.json OUTDIR
import bpy,bmesh,json,math,sys,os,random
from mathutils import Vector,Matrix
A=sys.argv[sys.argv.index('--')+1:];PR,CJ,OUT=A[0],A[1],A[2]
TEX=os.path.join(os.path.dirname(os.path.abspath(PR)),'tex')
OUT=os.path.abspath(OUT);os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
COL={'roof_white':(0.86,0.85,0.82),'base_dark':(0.09,0.10,0.12),'glass':(0.10,0.14,0.18),'wall_cream':(0.72,0.66,0.55),
'wall_white':(0.85,0.85,0.83),'brick':(0.45,0.22,0.13),'post':(0.85,0.85,0.85),'steel':(0.62,0.64,0.65),'frame':(0.18,0.19,0.2),
'roof_green':(0.04,0.13,0.10),'lamp_face':(0.78,0.80,0.80),'tree':(0.20,0.22,0.07),'trunk':(0.55,0.50,0.42),'dirt':(0.36,0.17,0.10),'grass':(0.08,0.22,0.04)}
TEXM={'lamps':'lamps.png','hoard':'hoard.png','sign_tio':'sign_tio.png','sign_white':'sign_white.png','roof_blue':'roof_blue.png','screen':'screen.png','hoard_blue':'hoard_blue.png','hoard_white':'hoard_white.png','rail':'rail.png'}
EMIT={'screen':0.6}   # daytime reference: lamps are off
TJ=json.load(open(os.path.join(os.path.dirname(os.path.abspath(PR)),'tex3','tex.json')));TILE=TJ['TILE']
M={}
def mat(n):
    if n in M:return M[n]
    m=bpy.data.materials.new(n);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF'];b.inputs['Roughness'].default_value=0.8
    T3=os.path.join(os.path.dirname(TEX),'tex3',n+'.png')
    if os.path.exists(T3) or n in TEXM:
        t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(T3 if os.path.exists(T3) else os.path.join(TEX,TEXM[n]));nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
        if n.startswith('rail'):
            nt.links.new(t.outputs['Alpha'],b.inputs['Alpha'])
            # smooth alpha: dithered alpha turned the sub-pixel chain-link into grain over dark walls (w04 arch)
            if hasattr(m,'surface_render_method'):m.surface_render_method='BLENDED'
        if n in EMIT:
            nt.links.new(t.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=EMIT[n]
    else:b.inputs['Base Color'].default_value=(*COL.get(n,(0.5,0.5,0.5)),1)
    if n in('glass','glass_sb'):b.inputs['Roughness'].default_value=0.3
    if n=='roof_green':b.inputs['Specular IOR Level'].default_value=0.1  # w04: matte painted steel; default specular washed it to grey at the low camera
    if n=='steel':b.inputs['Metallic'].default_value=0.5;b.inputs['Roughness'].default_value=0.45
    M[n]=m;return m
cols={}
def coll(n):
    if n not in cols:
        c=bpy.data.collections.new(n);sc.collection.children.link(c);cols[n]=c
    return cols[n]
def world_uv(bm,m):
    tu,tv=TILE.get(m,[2,2]);ul=bm.loops.layers.uv.new('UV')
    for fa in bm.faces:
        n=fa.normal;ax=(0,1) if abs(n.z)>=max(abs(n.x),abs(n.y)) else ((0,2) if abs(n.y)>=abs(n.x) else (1,2))
        for l in fa.loops:co=l.vert.co;l[ul].uv=(co[ax[0]]/tu,co[ax[1]]/tv)
def mk(name,V,F,m,UV=None,c='model'):
    me=bpy.data.meshes.new(name);bm=bmesh.new();vs=[bm.verts.new(v) for v in V]
    uvl=bm.loops.layers.uv.new('UV') if UV else None
    for i,f in enumerate(F):
        try:fa=bm.faces.new([vs[j] for j in f])
        except ValueError:continue
        if UV:
            for l,uv in zip(fa.loops,UV[i]):l[uvl].uv=uv
    bm.normal_update()
    if not UV:world_uv(bm,m)
    bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);coll(c).objects.link(o);me.materials.append(mat(m));return o
def box_faces(n):
    F=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    for i in range(n):
        j=(i+1)%n;F.append((i,j,n+j,n+i))
    return F
def face_dir(b):
    a=math.atan2(-b[1],-b[0]);return Vector((math.cos(a),math.sin(a),0)),Vector((-math.sin(a),math.cos(a),0))
def cone(name,b,z0,z1,r0,r1,m,seg=16,c='model'):
    V=[(b[0]+r0*math.cos(2*math.pi*i/seg),b[1]+r0*math.sin(2*math.pi*i/seg),z0) for i in range(seg)]
    V+=[(b[0]+r1*math.cos(2*math.pi*i/seg),b[1]+r1*math.sin(2*math.pi*i/seg),z1) for i in range(seg)]
    return mk(name,V,box_faces(seg),m,c=c)
def rod(name,p,q,r,m):
    p=Vector(p);q=Vector(q);d=q-p;L=d.length;rot=d.to_track_quat('Z','Y').to_matrix();V=[];seg=6
    for z in(0,L):
        for i in range(seg):V.append(tuple(p+rot@Vector((r*math.cos(2*math.pi*i/seg),r*math.sin(2*math.pi*i/seg),z))))
    return mk(name,V,box_faces(seg),m)
def quad(n,a,b,z0,z1,m,two=True):
    V=[(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)]
    F=[(0,1,2,3)]+([(3,2,1,0)] if two else []);UV=[[(0,0),(1,0),(1,1),(0,1)],[(0,1),(1,1),(1,0),(0,0)]][:len(F)]
    return mk(n,V,F,m,UV)
P=json.load(open(PR))
SJ=os.path.join(os.path.dirname(os.path.abspath(PR)),'stand_uv.json')
if os.path.exists(SJ):   # the measured grandstand replaces the old block prims
    P=[p for p in P if not p['name'].startswith('gs_')]
    for g in json.load(open(SJ))['G']:mk(g['name'],[tuple(v) for v in g['V']],[tuple(f) for f in g['F']],g['mat'],g.get('UV'))
CLJ=os.path.join(os.path.dirname(os.path.abspath(PR)),'club_uv.json')
if os.path.exists(CLJ):   # the measured clubrooms replace the old block prims
    P=[p for p in P if not (p['name'].startswith('cr_') or p['name']=='nb' or p['kind']=='tree')]   # trees: surroundings, not the stadium (director 2026-11-18)   # hoardings: match-day only, absent in the 2025 photos
    for g in json.load(open(CLJ))['G']:mk(g['name'],[tuple(v) for v in g['V']],[tuple(f) for f in g['F']],g['mat'],g.get('UV'))
for pr in P:   # the hoardings were traced over the permanent fence: the runs stay, as open chain-link (c03, c07; no boards: the director picked C, bare fence, 2026-11-18)
    if pr['name'].startswith('fence_hoard'):pr['mat']='rail_open';pr['h']=1.0
    if pr['name']=='east_wall':pr['mat']='block_tan';pr['h']=1.0   # c07: beige blockwork about 1 m high (read against the 1.2 m bench), not red brick
    k=pr['kind'];n=pr['name'];m=pr['mat']
    if k=='slab':
        pts=pr['pts'];t=pr['th'];V=[(x,y,z-t) for x,y,z in pts]+[tuple(q) for q in pts];UV=None
        if m=='roof_blue':UV=[[(0,1),(1,1),(1,0),(0,0)],[(0,1),(0,0),(1,0),(1,1)]]+[[(0,0)]*4]*4
        mk(n,V,box_faces(4),m,UV)
    elif k=='prism':
        fp=pr['fp'];zt=pr['ztop'] if isinstance(pr['ztop'],list) else [pr['ztop']]*len(fp)
        V=[(x,y,pr['z0']) for x,y in fp]+[(x,y,z) for (x,y),z in zip(fp,zt)];mk(n,V,box_faces(len(fp)),m)
    elif k=='pole':cone(n,pr['base'],0,pr['z1'],pr['r0'],pr['r1'],m)
    elif k=='lattice':
        b=pr['base'];z1=pr['z1'];L=[]
        for sx,sy in((1,1),(-1,1),(-1,-1),(1,-1)):L.append(((b[0]+sx*pr['r0'],b[1]+sy*pr['r0'],0),(b[0]+sx*pr['r1'],b[1]+sy*pr['r1'],z1)))
        for i,(p,q) in enumerate(L):rod(n+'_leg%d'%i,p,q,0.09,m)
        steps=int(z1/2.5)
        def at(i,t):
            p,q=L[i];return tuple(p[j]+(q[j]-p[j])*t for j in range(3))
        for s in range(steps):
            for i in range(4):rod(n+'_br',at(i,s/steps),at((i+1)%4,(s+1)/steps),0.04,m)
    elif k=='head':   # 3D lamp heads facing the field (c05, w04): poles carry a tilted rack of round lamps on a railed
        # platform with the pole running on to a crossbar; lattice towers carry a square panel of square lamps
        b=pr['base'];f,sd=face_dir(b);z0,z1=pr['z0'],pr['z1'];B=Vector((b[0],b[1],0));lat=pr.get('lat',False)
        nc,nr,W_,H_=(5,5,4.6,z1-z0-0.6) if lat else (8,7,7.0,min(6.6,z1-z0-0.4))
        # rack top leans 12 degrees toward the field so the lamps aim down at the ground; the rack hangs 1 m in front of the pole
        tilt=math.radians(12);up=Vector((0,0,1))*math.cos(tilt)+f*math.sin(tilt);nrm=f*math.cos(tilt)-Vector((0,0,1))*math.sin(tilt)
        base_z=z0+0.5;C0=B+f*1.0+Vector((0,0,base_z))
        V=[];F=[]
        def cyl(p,q,r,seg):
            d=(q-p).normalized();u=d.cross(Vector((0,0,1)));u=u.normalized() if u.length>1e-6 else Vector((1,0,0));v=d.cross(u);o=len(V)
            for e in(p,q):
                for i in range(seg):an=2*math.pi*i/seg;V.append(tuple(e+r*(u*math.cos(an)+v*math.sin(an))))
            F.append(tuple(range(o+seg-1,o-1,-1)));F.append(tuple(range(o+seg,o+2*seg)))
            for i in range(seg):j=(i+1)%seg;F.append((o+i,o+j,o+seg+j,o+seg+i))
        Vl=[];Fl=[]
        for i in range(nc):
            for j in range(nr):
                c=C0+sd*((i+0.5)/nc-0.5)*W_+up*((j+0.5)/nr)*H_
                if lat:   # square lamp box 0.7 x 0.7, 0.3 deep
                    hw=0.33;o=len(Vl)
                    for dz in(0,0.3):
                        for (a_,b_) in((-1,-1),(1,-1),(1,1),(-1,1)):Vl.append(tuple(c-nrm*dz+sd*a_*hw+up*b_*hw))
                    Fl+=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)];Fl[-6:]=[tuple(o+x for x in t) for t in Fl[-6:]]
                else:
                    o=len(V);cyl(c-nrm*0.35,c,0.29,10)
                    # the lamp's front cap goes to the glass mesh
                    Vl+=V[o:];Fl.append(tuple(range(len(Vl)-10,len(Vl))));del V[o:];F[:]=[t for t in F if max(t)<o]
                    o2=len(V);p_,q_=c-nrm*0.35,c-nrm*0.02;cyl(p_,q_,0.30,10)
        # rack frame: outline and two crossbars behind the lamps
        for t_ in(0.0,0.5,1.0):cyl(C0-nrm*0.4-sd*W_/2+up*H_*t_,C0-nrm*0.4+sd*W_/2+up*H_*t_,0.06,6)
        for e in(-0.5,0.5):cyl(C0-nrm*0.4+sd*W_*e,C0-nrm*0.4+sd*W_*e+up*H_,0.06,6)
        # platform under the rack with a rail on its open sides
        pw=W_/2+0.3;pd=1.4;o=len(V);zp=z0+0.2
        for dz in(0,0.12):
            for (a_,b_) in((-1,-0.4),(1,-0.4),(1,1),(-1,1)):V.append(tuple(B+sd*a_*pw+f*(b_*pd)+Vector((0,0,zp+dz))))
        F+=[tuple(o+x for x in t) for t in((3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))]
        for (pa,pb) in((B-sd*pw+f*pd,B+sd*pw+f*pd),(B-sd*pw-f*pd*0.4,B-sd*pw+f*pd),(B+sd*pw-f*pd*0.4,B+sd*pw+f*pd)):
            za=Vector((0,0,zp+1.1));cyl(pa+za,pb+za,0.03,5)
            for t_ in(0,0.5,1):q=pa+(pb-pa)*t_;cyl(q+Vector((0,0,zp)),q+za,0.025,5)
        if not lat:   # the pole runs on behind the rack to a crossbar at the top
            cyl(B+Vector((0,0,z0)),B+Vector((0,0,z1)),0.4,10);cyl(B-sd*W_/2+Vector((0,0,z1)),B+sd*W_/2+Vector((0,0,z1)),0.12,8)
        else:     # lattice: the four legs carry on to the panel top
            for (a_,b_) in((-1,-1),(1,-1),(1,1),(-1,1)):cyl(B+Vector((a_*0.35,b_*0.35,z0)),B+Vector((a_*0.35,b_*0.35,z1-0.3)),0.08,6)
        mk(n+'_frame',V,F,'steel');mk(n+'_lamps',Vl,Fl,'lamp_face')
    elif k=='sign':
        b=pr['base'];f,s=face_dir(b);B=Vector((b[0],b[1],0))+f*pr['off'];w=pr['w']/2
        quad(n,B-s*w,B+s*w,pr['z0'],pr['z1'],m)
    elif k=='fence':
        pts=pr['pts']+([] if pr.get('open') else [pr['pts'][0]]);h=pr['h'];V=[];F=[];UV=[];s=0
        for i in range(len(pts)-1):
            a,b2=pts[i],pts[i+1];L=math.dist(a,b2);o=len(V)
            V+=[(a[0],a[1],0),(b2[0],b2[1],0),(b2[0],b2[1],h),(a[0],a[1],h)]
            tu,tv=TILE.get(m,(16,1));u0,u1=s/tu,(s+L)/tu;t=h/tv   # each material's own tile size, so nothing stretches
            F+=[(o,o+1,o+2,o+3),(o+3,o+2,o+1,o)];UV+=[[(u0,0),(u1,0),(u1,t),(u0,t)],[(u0,t),(u1,t),(u1,0),(u0,0)]];s+=L
        mk(n,V,F,m,UV)
    elif k=='board':
        a,b2=pr['a'],pr['b'];quad(n,a,b2,pr['z0'],pr['z1'],m)   # reads left-to-right from the field
    elif k=='gable':
        fp=pr['fp'];e=pr['eave'];r=pr['ridge'];x0,x1=fp[0][0],fp[1][0];yN,yS=fp[0][1],fp[2][1];ym=(yN+yS)/2
        mk(n+'_walls',[(x0,yN,0),(x1,yN,0),(x1,yS,0),(x0,yS,0),(x0,yN,e),(x1,yN,e),(x1,yS,e),(x0,yS,e)],box_faces(4),'shed_wall')
        mk(n+'_gables',[(x0,yN,e),(x0,ym,r),(x0,yS,e),(x1,yN,e),(x1,ym,r),(x1,yS,e)],[(0,1,2),(2,1,0),(3,4,5),(5,4,3)],'shed_wall')
        mk(n,[(x0-0.4,yN-0.4,e-0.1),(x1+0.4,yN-0.4,e-0.1),(x1+0.4,ym,r),(x0-0.4,ym,r),(x1+0.4,yS+0.4,e-0.1),(x0-0.4,yS+0.4,e-0.1)],[(0,1,2,3),(3,2,1,0),(3,2,4,5),(5,4,2,3)],m)
    elif k=='tree':
        cx,cy=pr['xy'];r=pr['r'];h=pr['h'];cd=pr['cd']
        cone(n+'_trunk',(cx,cy),0,h-cd*0.6,0.35,0.2,'trunk',8)
        random.seed(int(abs(cx*7+cy*13)))
        for i in range(6):
            a=random.random()*2*math.pi;d=random.random()*r*0.55;rr=r*(0.45+0.2*random.random())
            me=bpy.data.meshes.new(n+'_canopy');bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1.0)
            bmesh.ops.transform(bm,matrix=Matrix.Translation((cx+d*math.cos(a),cy+d*math.sin(a),h-cd/2+random.uniform(-0.2,0.25)*cd))@Matrix.Diagonal((rr,rr,rr*0.75,1)),verts=bm.verts)
            bm.normal_update();world_uv(bm,'tree');bm.to_mesh(me);bm.free();o=bpy.data.objects.new(n+'_canopy',me);coll('model').objects.link(o);me.materials.append(mat('tree'))
# ground: outer grass apron; inside the fence plain grass stands in for the game's own scene
fence=[p for p in P if p['name']=='fence_ring'][0]['pts']
mk('ground_dirt',[(-140,-135,-0.05),(140,-135,-0.05),(140,135,-0.05),(-140,135,-0.05)],[(0,1,2,3)],'grass_out',c='ground')
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ring.py')).read());print('apron ring m2',round(ring_mesh(bpy.data.objects['ground_dirt'].data,[(-140,-135),(140,-135),(140,135),(-140,135)],fence,-0.05,TILE.get('grass_out',(6,6)))))   # grass outside the fence too (aerial, w04, c07)
# playing field left out: the game draws its own grass inside the boundary fence (director 2026-11-18: "Leave field out")
# mk('ground_grass',[(x,y,0.0) for x,y in fence],[tuple(range(len(fence)))],'grass',c='ground')
for o in coll('model').objects:
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(o.data);bm.free()
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'pairfix.py')).read());print('pair_fix flipped',pair_fix(list(coll('model').objects)))
# camera from cam.json
p=json.load(open(CJ))['p'];W,H=1500,1074
def Rm(yaw,pitch,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch);cr,sr=math.cos(roll),math.sin(roll)
    f=Vector((cy*cp,sy*cp,sp));r=Vector((sy,-cy,0));u=r.cross(f)
    return cr*r+sr*u,-sr*r+cr*u,f
rr,uu,ff=Rm(*p[3:6])
cd=bpy.data.cameras.new('cam');cam=bpy.data.objects.new('cam',cd);sc.collection.objects.link(cam);sc.camera=cam
cam.matrix_world=Matrix(((rr.x,uu.x,-ff.x,p[0]),(rr.y,uu.y,-ff.y,p[1]),(rr.z,uu.z,-ff.z,p[2]),(0,0,0,1)))
cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=p[6]*36/W;cd.shift_x=(W/2-p[7])/W;cd.shift_y=(p[8]-H/2)/W;cd.clip_end=3000
sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100
# sun low in the west: the photo is late afternoon, shadows fall east
sd=bpy.data.lights.new('sun','SUN');sd.energy=4.0;sd.color=(1.0,0.82,0.62);sun=bpy.data.objects.new('sun',sd);sc.collection.objects.link(sun)
sun.rotation_euler=Vector((1.0,0.25,-0.28)).normalized().to_track_quat('-Z','Y').to_euler()
w=bpy.data.worlds.new('w');sc.world=w;w.use_nodes=True
w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.62,0.75,1);w.node_tree.nodes['Background'].inputs[1].default_value=0.8
for e in('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
    try:
        sc.render.engine=e;break
    except TypeError:pass
sc.view_settings.view_transform='Standard'
sc.render.film_transparent=True
sc.render.filepath=os.path.join(OUT,'render_ground.png');bpy.ops.render.render(write_still=True)
for o in coll('ground').objects:o.hide_render=True
sc.render.filepath=os.path.join(OUT,'render_model.png');bpy.ops.render.render(write_still=True)
for o in coll('ground').objects:o.hide_render=False
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'traeger.glb'),export_format='GLB',export_cameras=False,export_lights=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'traeger.blend'))
print('DONE',len(bpy.data.objects))
