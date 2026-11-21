import bpy,sys,math,json
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];src,out=a[0],a[1];lx,ly,lz,rng,hd,tl,fov=map(float,a[2:9])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE'
W,H=1280,585;sc.render.resolution_x,sc.render.resolution_y=W,H
h,t=math.radians(hd),math.radians(tl);L=Vector((lx,ly,lz))
d=Vector((math.sin(h)*math.sin(t),math.cos(h)*math.sin(t),-math.cos(t)))
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c'));sc.collection.objects.link(cam);sc.camera=cam
cam.location=L-d*rng;cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam.data.sensor_fit='VERTICAL';cam.data.angle=math.radians(fov);cam.data.clip_end=5000
sc.world=bpy.data.worlds.new('w');sc.world.color=(0.6,0.7,0.8)
bpy.context.view_layer.update()
f=(W/2)/math.tan(cam.data.angle/2);Mr=cam.matrix_world.to_3x3()
json.dump({'C':list(cam.location),'R':[list(r) for r in Mr],'f':f},open(out+'.json','w'))
if len(a)>9:
  dg=bpy.context.evaluated_depsgraph_get()
  for s in a[9].split(';'):
    n,u,v=s.split(',');u,v=float(u),float(v)
    dirc=Mr@Vector(((u-W/2)/f,-(v-H/2)/f,-1)).normalized()
    hit=sc.ray_cast(dg,cam.location,dirc.normalized())
    print('HIT',n,'%.2f %.2f %.2f'%tuple(hit[1]) if hit[0] else 'none')
else:
  sc.render.filepath=out;bpy.ops.render.render(write_still=True)
