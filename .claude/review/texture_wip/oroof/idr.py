import bpy,math,mathutils,sys,colorsys
O=sys.argv[-2];G=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+G+'.glb')
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='FLAT';sc.display.shading.color_type='MATERIAL'
sc.view_settings.view_transform='Standard'
sc.render.resolution_x=1600;sc.render.resolution_y=900
ms=sorted(bpy.data.materials,key=lambda m:m.name)
for k,m in enumerate(ms):
    r,g,b=colorsys.hsv_to_rgb(k/len(ms),1,1 if k%2 else 0.6);m.diffuse_color=(r,g,b,1);print('ID',m.name)
for i,(a,r,h,tr,lens) in enumerate(((-60,250,90,120,50),(30,330,140,0,40))):
    c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));c.data.lens=lens;sc.collection.objects.link(c)
    A=math.radians(a);c.location=(r*math.cos(A)-30,r*math.sin(A)-9,h)
    t=mathutils.Vector((tr*math.cos(A)-30,tr*math.sin(A)-9,30));c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler();sc.camera=c
    sc.render.filepath=O+'id%d.png'%i;bpy.ops.render.render(write_still=True)
