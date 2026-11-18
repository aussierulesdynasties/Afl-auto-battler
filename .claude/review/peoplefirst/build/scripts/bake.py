# blender -b model.blend -P bake.py -- RES : atlas UVs, then bake world position, normal and lit close-up colour
import bpy,sys,os,math
RES=int(sys.argv[sys.argv.index('--')+1])
ob=bpy.data.objects['PeopleFirstStadium'];me=ob.data
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
if 'atlas' not in me.uv_layers:
    me.uv_layers.new(name='atlas')
me.uv_layers.active=me.uv_layers['atlas']
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=0.0015,area_weight=0.0,scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='GPU'
try:
    pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
    for d in pr.devices:d.use=True
except Exception as e:print('gpu',e)
def target(name,float_=True):
    im=bpy.data.images.new(name,RES,RES,float_buffer=float_,alpha=False)
    for m in me.materials:
        nt=m.node_tree;n=nt.nodes.get('BAKE') or nt.nodes.new('ShaderNodeTexImage');n.name='BAKE';n.image=im
        u=nt.nodes.get('BAKEUV') or nt.nodes.new('ShaderNodeUVMap');u.name='BAKEUV';u.uv_map='atlas';nt.links.new(u.outputs[0],n.inputs[0])
        nt.nodes.active=n
    return im
def save(im,path,fmt):
    im.filepath_raw=os.path.abspath(path);im.file_format=fmt;im.save()
sc.cycles.samples=1;sc.render.bake.margin=4
im=target('pos');bpy.ops.object.bake(type='POSITION',uv_layer='atlas');save(im,'bake_pos.exr','OPEN_EXR')
im=target('nrm');sc.render.bake.normal_space='OBJECT';bpy.ops.object.bake(type='NORMAL',uv_layer='atlas');save(im,'bake_nrm.exr','OPEN_EXR')
# lit close-up colour: sun as in the photo plus sky
sd=bpy.data.lights.new('sun','SUN');sd.energy=3.3;so=bpy.data.objects.new('sun',sd);sc.collection.objects.link(so);so.rotation_euler=(math.radians(40),0,math.radians(-141))
w=bpy.data.worlds.new('w');w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(0.55,0.6,0.68,1);bg.inputs['Strength'].default_value=0.8;sc.world=w
sc.view_settings.view_transform='Standard'
sc.cycles.samples=64
im=target('lit',False);bpy.ops.object.bake(type='COMBINED',uv_layer='atlas');save(im,'bake_lit.png','PNG')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('baked.blend'))
print('BAKED')
