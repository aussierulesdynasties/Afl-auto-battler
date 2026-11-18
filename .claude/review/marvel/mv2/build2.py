# Blender 5.2: Marvel Stadium exterior from parts2.json with hand-made tiling textures (tex/*.png, tiles.json).
# Usage: blender -b --python build2.py -- MODE [args]
#   ov            : render from the aerial camera c5 -> r_ov.png (1920x1080)
#   views         : render named views from views.json -> r_<name>.png
#   glb           : export marvel2.glb (origin at the pitch centre, +Y = north)
import bpy,json,sys,math,os
import numpy as np
from mathutils import Matrix,Vector
HERE=os.path.dirname(os.path.abspath(__file__));argv=sys.argv[sys.argv.index('--')+1:];MODE=argv[0]
J=json.load(open(os.path.join(HERE,'parts2.json')));P=J['cam'];TILE=json.load(open(os.path.join(HERE,'tex','tiles.json')))
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
C0=np.array(J.get('C',[2.32,0.64,0.0]))
# ---------- materials: one image texture each, UVs already in metres; scaled here by the tile size
MATS={}
ALIAS={'deck2':'deck'}
def mat(name):
    if name in MATS:return MATS[name]
    src=ALIAS.get(name,name);m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=False
    nt=m.node_tree;b=nt.nodes['Principled BSDF'];tx=nt.nodes.new('ShaderNodeTexImage')
    tx.image=bpy.data.images.load(os.path.join(HERE,'tex',src+'.png'));tx.interpolation='Cubic'
    nt.links.new(tx.outputs['Color'],b.inputs['Base Color'])
    rough={'glass':0.15,'curtain':0.12,'silver':0.35,'teal':0.45,'tank':0.3}.get(src,0.8)
    b.inputs['Roughness'].default_value=rough
    if src in('glass','curtain','silver','tank'):b.inputs['Metallic'].default_value=0.35 if src!='silver' else 0.5
    if name=='deck2':
        hs=nt.nodes.new('ShaderNodeHueSaturation');hs.inputs['Value'].default_value=0.93
        nt.links.new(tx.outputs['Color'],hs.inputs['Color']);nt.links.new(hs.outputs['Color'],b.inputs['Base Color'])
    MATS[name]=m;return m
def tile(n):return TILE.get(ALIAS.get(n,n),[4,4])
# ---------- meshes (one object per group so crops and the GLB stay tidy)
def group(n):
    for g in('slab','end_','truss','arch','bowl','col','bracket','plinth','tier','podium','canopy','tank','tower','sign'):
        if n.startswith(g):return g.rstrip('_')
    return 'misc'
G={}
for q in J['parts']:G.setdefault(group(q['name']),[]).append(q)
OBJ=[]
for g,qs in G.items():
    V=[];F=[];M=[];UV=[]
    for q in qs:
        o=len(V);V+=[tuple(np.array(v)-C0) for v in q['V']];F+=[[o+i for i in f] for f in q['F']];M+=q['M'];UV+=q['UV']
    me=bpy.data.meshes.new(g);me.from_pydata(V,[],F);me.update()
    names=sorted(set(M))
    for n in names:me.materials.append(mat(n))
    idx={n:i for i,n in enumerate(names)}
    for poly,m in zip(me.polygons,M):poly.material_index=idx[m];poly.use_smooth=False
    uvl=me.uv_layers.new(name='UVMap');k=0
    for poly,uv,m in zip(me.polygons,UV,M):
        tu,tv=tile(m)
        for j,li in enumerate(poly.loop_indices):uvl.data[li].uv=(uv[j][0]/tu,uv[j][1]/tv)
    ob=bpy.data.objects.new(g,me);sc.collection.objects.link(ob);OBJ.append(ob)
# ---------- light: summer midday sun from the north, sky fill
wd=bpy.data.worlds.new('w');sc.world=wd;wd.use_nodes=True;bg=wd.node_tree.nodes['Background']
bg.inputs['Color'].default_value=(0.62,0.72,0.86,1);bg.inputs['Strength'].default_value=0.9
sd=bpy.data.lights.new('sun','SUN');sd.energy=3.2;sd.angle=math.radians(1.0)
sun=bpy.data.objects.new('sun',sd);sc.collection.objects.link(sun)
sun.rotation_euler=(math.radians(28),0,math.radians(float(os.environ.get('SUNAZ','160'))))
sc.view_settings.view_transform='AgX';sc.view_settings.look='None'
for e in('BLENDER_EEVEE','BLENDER_EEVEE_NEXT'):
    try:sc.render.engine=e;break
    except Exception:pass
try:sc.eevee.taa_render_samples=32
except Exception:pass
sc.render.film_transparent=True
def Rm(yaw,pitch,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
cd=bpy.data.cameras.new('cam');cam=bpy.data.objects.new('cam',cd);sc.collection.objects.link(cam);sc.camera=cam
cd.sensor_fit='HORIZONTAL';cd.sensor_width=36.0;cd.clip_start=0.5;cd.clip_end=5000
def set_pinhole(p,W=1920,H=1080):
    M=Rm(*p[3:6]);cd.lens=p[6]*36.0/W;R=np.stack([M[0],M[1],-M[2]],1);mw=Matrix.Identity(4)
    for i in range(3):
        for j in range(3):mw[i][j]=R[i,j]
        mw[i][3]=p[i]-C0[i]
    cam.matrix_world=mw;sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100
def look(eye,tgt,lens,W,H):
    eye=Vector(eye);d=(Vector(tgt)-eye);cam.location=eye;cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    cd.lens=lens;sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.resolution_percentage=100
def render(path):sc.render.filepath=path;bpy.ops.render.render(write_still=True)
if MODE=='ov':
    set_pinhole(P);render(os.path.join(HERE,'r_ov.png'))
elif MODE=='views':
    VW=json.load(open(os.path.join(HERE,argv[1] if len(argv)>1 else 'views.json')))
    for n,v in VW.items():
        sc.render.film_transparent=v.get('transparent',True)
        look(v['eye'],v['tgt'],v.get('lens',35),v.get('W',1600),v.get('H',1000));render(os.path.join(HERE,'r_%s.png'%n))
elif MODE=='glb':
    # GLB: origin at the pitch centre, north = +Y. World x,y here are the local frame axes; rotate so u (south) = -Y.
    U=np.array([0.336,-0.942]);ang=math.atan2(-U[0],-U[1])  # rotate u-direction onto -Y
    for ob in OBJ:ob.matrix_world=Matrix.Rotation(ang,4,'Z')@ob.matrix_world
    for ob in OBJ:ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE,'marvel2.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
print('DONE',MODE)
