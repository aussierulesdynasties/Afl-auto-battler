# blender -b baked.blend -P posrender.py -- CAMJSON OUT.npy : per-pixel world position (nan = empty) from a pinhole camera
import bpy,sys,os,math,json,numpy as np
from mathutils import Vector,Matrix
a=sys.argv[sys.argv.index('--')+1:];CAM=json.load(open(a[0]))['p'];W=int(a[2]) if len(a)>2 else 2000;H=int(a[3]) if len(a)>3 else 1333
ob=bpy.data.objects['PeopleFirstStadium'];me=ob.data
m=bpy.data.materials.new('posm');m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
g=nt.nodes.new('ShaderNodeNewGeometry');e=nt.nodes.new('ShaderNodeEmission');o=nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(g.outputs['Position'],e.inputs[0]);nt.links.new(e.outputs[0],o.inputs[0])
me.materials.clear();me.materials.append(m)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=1;sc.cycles.use_denoising=False;sc.cycles.filter_width=0.01
sc.cycles.device='GPU'
sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.film_transparent=True
sc.view_settings.view_transform='Raw' if 'Raw' in [x.identifier for x in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Standard'
sc.render.image_settings.file_format='OPEN_EXR';sc.render.image_settings.color_depth='32'
cd=bpy.data.cameras.new('cam');cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=CAM[6]*36/W;cd.clip_end=5000;cd.clip_start=20
co=bpy.data.objects.new('cam',cd);sc.collection.objects.link(co);sc.camera=co
def RR(yaw,p_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(p_),math.sin(p_);cr,sr=math.cos(roll),math.sin(roll)
    f=Vector((cy*cp,sy*cp,sp));r=Vector((sy,-cy,0.0));u=r.cross(f)
    return [cr*r+sr*u,-sr*r+cr*u,f]
M=RR(*CAM[3:6])
Mb=Matrix(((M[0][0],M[1][0],-M[2][0]),(M[0][1],M[1][1],-M[2][1]),(M[0][2],M[1][2],-M[2][2])))
co.matrix_world=Matrix.Translation(Vector(CAM[:3]))@Mb.to_4x4()
sc.world=None
tmp=os.path.abspath(a[1]+'.exr');sc.render.filepath=tmp;bpy.ops.render.render(write_still=True)
im=bpy.data.images.load(tmp);im.colorspace_settings.name='Non-Color'
px=np.empty(W*H*4,np.float32);im.pixels.foreach_get(px);px=px.reshape(H,W,4)[::-1]
P=px[...,:3].copy();P[px[...,3]<0.5]=np.nan;np.save(os.path.abspath(a[1]),P);print('POS',np.nanmin(P),np.nanmax(P))
