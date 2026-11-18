# blender -b baked.blend -P apply.py -- ATLAS.png OUT.glb [CAMJSON RENDER.png] : one unlit atlas material, export, optional matched render
import bpy,sys,os,math,json
from mathutils import Vector,Matrix
a=sys.argv[sys.argv.index('--')+1:];atlas,out=a[0],a[1]
ob=bpy.data.objects['PeopleFirstStadium'];me=ob.data
img=bpy.data.images.load(os.path.abspath(atlas));img.colorspace_settings.name='sRGB'
m=bpy.data.materials.new('pf_atlas');m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
t=nt.nodes.new('ShaderNodeTexImage');t.image=img;t.interpolation='Linear'
uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map='atlas';nt.links.new(uv.outputs[0],t.inputs[0])
bg=nt.nodes.new('ShaderNodeBackground');o=nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(t.outputs[0],bg.inputs[0]);nt.links.new(bg.outputs[0],o.inputs[0])
me.materials.clear();me.materials.append(m)
for p in me.polygons:p.material_index=0
for l in list(me.uv_layers):
    if l.name!='atlas':me.uv_layers.remove(l)
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out),export_format='GLB',export_image_format='WEBP' if os.environ.get('WEBP') else 'AUTO')
if len(a)>2:
    CAM=json.load(open(a[2]))['p'];rpng=a[3]
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
    sc.view_settings.view_transform='Standard';sc.world=None
    sc.render.filepath=os.path.abspath(rpng);bpy.ops.render.render(write_still=True)
print('APPLIED')
