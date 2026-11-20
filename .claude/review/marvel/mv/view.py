# Blender: render stage2.blend from a given eye. Usage: blender -b stage2.blend --python view.py -- MV OUT.png ex ey ez tx ty tz [own]
import bpy,sys,os
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];MV,OUT=a[0],a[1];E=Vector(map(float,a[2:5]));T=Vector(map(float,a[5:8]));own=len(a)>8
sc=bpy.context.scene;cam=sc.camera
cam.location=E;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(T-E).to_track_quat('-Z','Y');cam.data.lens=30
if own:
    for g in ('front','sym','roof'):
        for n in bpy.data.materials['m_'+g].node_tree.nodes:
            if n.type=='TEX_IMAGE':n.image=bpy.data.images.load(os.path.join(MV,'tex_%s_own.png'%g))
sc.render.resolution_x=1600;sc.render.resolution_y=900;sc.render.film_transparent=False
sc.world=sc.world or bpy.data.worlds.new('w');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.62,0.7,1)
sc.render.filepath=OUT;bpy.ops.render.render(write_still=True)
