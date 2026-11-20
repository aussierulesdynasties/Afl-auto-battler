# blender -b -P render_top.py -- in.glb out.png [half_extent_m=200] [m_per_px=0.25]
# Straight-down orthographic render of a GLB, centred on the world origin. Image x = Blender +X (glTF +X),
# image up = Blender +Y (= glTF -Z). Transparent background. Prints the model's bounds.
import bpy,sys,math
a=sys.argv[sys.argv.index('--')+1:]
import os;src,out=os.path.abspath(a[0]),os.path.abspath(a[1]); H=float(a[2]) if len(a)>2 else 200.0; mpp=float(a[3]) if len(a)>3 else 0.25
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
import mathutils
mn=[1e9]*3;mx=[-1e9]*3
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        for c in o.bound_box:
            w=o.matrix_world@mathutils.Vector(c)
            for i in range(3):mn[i]=min(mn[i],w[i]);mx[i]=max(mx[i],w[i])
print('BOUNDS',[round(v,1) for v in mn],[round(v,1) for v in mx])
cam=bpy.data.cameras.new('c');cam.type='ORTHO';cam.ortho_scale=2*H;cam.clip_end=5000
co=bpy.data.objects.new('c',cam);bpy.context.scene.collection.objects.link(co)
co.location=(0,0,mx[2]+100);co.rotation_euler=(0,0,0)
sc=bpy.context.scene;sc.camera=co
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='FLAT';sc.display.shading.color_type='TEXTURE'
sc.render.film_transparent=True;sc.render.resolution_x=sc.render.resolution_y=int(round(2*H/mpp));sc.render.resolution_percentage=100
sc.view_settings.view_transform='Standard'
sc.render.filepath=out;bpy.ops.render.render(write_still=True);print('WROTE',out)
