# Straight-down orthographic renders, north up (build frame x east, y north). Usage:
# blender -b moorabbin3.blend --python topdown.py -- out.png cx cy metres px [transparent 0/1]
import bpy,sys,math
a=sys.argv[sys.argv.index('--')+1:];out=a[0];cx,cy,m=float(a[1]),float(a[2]),float(a[3]);px=int(a[4]);tr=len(a)>5 and a[5]=='1'
sc=bpy.context.scene
cam=bpy.data.cameras.new('td');cam.type='ORTHO';cam.ortho_scale=m;cam.clip_end=2000
co=bpy.data.objects.new('td',cam);sc.collection.objects.link(co);co.location=(cx,cy,400);co.rotation_euler=(0,0,0)
sc.camera=co;sc.render.resolution_x=sc.render.resolution_y=px;sc.render.resolution_percentage=100
sc.render.engine='BLENDER_EEVEE';sc.render.film_transparent=tr;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.view_settings.view_transform='Standard'
for o in sc.objects:
    if o.type=='LIGHT':o.data.energy=3.0;o.rotation_euler=(math.radians(25),0,math.radians(150))
sc.render.filepath=out;bpy.ops.render.render(write_still=True);print('TD',out)
