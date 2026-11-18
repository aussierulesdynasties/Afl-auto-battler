import bpy,math,json,sys,os
import numpy as np
from mathutils import Vector,Matrix
WD=os.path.dirname(os.path.abspath(__file__));A=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=A[0] if A else WD+'/out';MODE=A[1] if len(A)>1 else 'all'
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
Z=np.load(WD+'/mesh.npz');MATN=json.load(open(WD+'/mats.json'))
ROUGH={'roof':0.55,'white':0.5,'steel':0.45,'glass':0.15,'lamps':0.3,'turf':0.95}
def mat(name):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(WD+'/tex2/'+name+'.png');nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    b.inputs['Roughness'].default_value=ROUGH.get(name,0.85)
    if name=='glass':b.inputs['Metallic'].default_value=0.3
    if name=='turf':b.inputs['Specular IOR Level'].default_value=0.15  # photo: grass shows no sky sheen
    m.use_backface_culling=False
    return m
QV,QU,QM,TV,TU,TM=Z['QV'],Z['QU'],Z['QM'],Z['TV'],Z['TU'],Z['TM']
nq,nt_=len(QV),len(TV)
verts=np.r_[QV.reshape(-1,3),TV.reshape(-1,3)]
faces=[list(range(4*i,4*i+4)) for i in range(nq)]+[list(range(4*nq+3*i,4*nq+3*i+3)) for i in range(nt_)]
me=bpy.data.meshes.new('waverley');me.from_pydata(verts.tolist(),[],faces);me.update()
for n in MATN:me.materials.append(mat(n))
me.polygons.foreach_set('material_index',np.r_[QM,TM].astype(np.int32))
uv=me.uv_layers.new(name='UV');uvs=np.r_[QU.reshape(-1,2),TU.reshape(-1,2)].astype(np.float32)
uv.data.foreach_set('uv',uvs.ravel())
me.update()
ob=bpy.data.objects.new('WaverleyPark',me);bpy.context.scene.collection.objects.link(ob)
# merge coincident verts for a cleaner export
import bmesh
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.002);bm.to_mesh(me);bm.free()
cam=json.load(open(WD+'/camr6.json'))['q'];C=Vector(cam[:3]);yaw,pit,rol=cam[3:6];fo=cam[6];W,H=1023,576
cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pit),math.sin(pit);cr,sr=math.cos(rol),math.sin(rol)
f=Vector((cy*cp,sy*cp,sp));r=Vector((sy,-cy,0));u=r.cross(f);xr=cr*r+sr*u;yu=-sr*r+cr*u
cd=bpy.data.cameras.new('cam');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=fo*36/W;cd.clip_end=20000;cd.clip_start=1
cd.shift_x=-cam[7]/W;cd.shift_y=cam[8]/W
co=bpy.data.objects.new('cam',cd);bpy.context.scene.collection.objects.link(co)
co.matrix_world=Matrix(((xr.x,yu.x,-f.x,C.x),(xr.y,yu.y,-f.y,C.y),(xr.z,yu.z,-f.z,C.z),(0,0,0,1)))
sc=bpy.context.scene;sc.camera=co
sun=bpy.data.lights.new('sun','SUN');sun.energy=0.9;sun.angle=math.radians(1.0);so=bpy.data.objects.new('sun',sun);sc.collection.objects.link(so)
left=Vector((-sy,cy,0));fw=Vector((cy,sy,0));hz=(fw*0.94-left*0.34).normalized();el=math.radians(45)
tos=Vector((hz.x*math.cos(el),hz.y*math.cos(el),math.sin(el)))
so.rotation_euler=(-tos).to_track_quat('-Z','Y').to_euler()
wd=bpy.data.worlds.new('w');sc.world=wd;wd.use_nodes=True;bg=wd.node_tree.nodes['Background'];bg.inputs[0].default_value=(0.80,0.82,0.86,1);bg.inputs[1].default_value=1.2
if os.environ.get('WAV_CYCLES'):
    sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=True
    pr=bpy.context.preferences.addons['cycles'].preferences
    for dt in('OPTIX','CUDA'):
        try:
            pr.compute_device_type=dt;pr.get_devices();[setattr(d_,'use',True) for d_ in pr.devices];sc.cycles.device='GPU';break
        except Exception:pass
elif True:
  for e in('BLENDER_EEVEE','BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine=e;break
    except Exception:pass
try:sc.eevee.use_shadows=True
except Exception:pass
sc.view_settings.view_transform='Standard'
sc.render.resolution_x=2046;sc.render.resolution_y=1152;sc.render.film_transparent=True
if MODE=='close':
    for k,spec in enumerate(os.environ['CLOSE'].split(';')):
        v=[float(x) for x in spec.split(',')];e_=Vector(v[:3]);tg=Vector(v[3:6])
        cd2=bpy.data.cameras.new('c%d'%k);cd2.lens=v[6];cd2.clip_start=0.1;cd2.clip_end=5000
        c2=bpy.data.objects.new('c%d'%k,cd2);sc.collection.objects.link(c2);c2.location=e_
        c2.rotation_euler=(tg-e_).to_track_quat('-Z','Y').to_euler();sc.camera=c2
        sc.render.film_transparent=False;sc.render.resolution_x=1600;sc.render.resolution_y=1000
        sc.render.filepath=OUT+'/close_%d.png'%k;bpy.ops.render.render(write_still=True)
if MODE in('all','render'):
    sc.render.filepath=OUT+'/render.png';bpy.ops.render.render(write_still=True)
if MODE in('all','export'):
    bpy.ops.wm.save_as_mainfile(filepath=OUT+'/waverley2.blend')
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=OUT+'/waverley_park.glb',export_format='GLB',use_selection=True)
print('TRIS',sum(len(p_.vertices)-2 for p_ in me.polygons))
